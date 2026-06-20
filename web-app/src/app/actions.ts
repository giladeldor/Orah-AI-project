"use server";

import { Octokit } from "octokit";
import { GoogleGenerativeAI } from "@google/generative-ai";

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");
const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

export type ReviewResult = {
  repoName: string;
  repoUrl: string;
  level: string;
  assessment: string;
  error?: string;
};

export type ProfileAnalysis = {
  results: ReviewResult[];
  holisticSummary: string | null;
  cached?: boolean;
};

// Extremely simple in-memory cache for demo purposes
const cache = new Map<string, ProfileAnalysis>();

// Delay helper to prevent sending out requests too fast and tripping the RPM limit
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function fetchWithRetry(prompt: string, maxRetries = 5): Promise<string> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await model.generateContent(prompt);
      return result.response.text();
    } catch (e: any) {
      if (e.message?.includes("429") && i < maxRetries - 1) {
        // Parse the exact wait time Gemini asks for (e.g. "Please retry in 13.7s")
        const match = e.message.match(/retry in ([\d\.]+)s/i);
        let waitTime = 15000; // Fallback to 15s
        if (match && match[1]) {
          waitTime = (parseFloat(match[1]) + 2) * 1000; // Add 2s safety buffer
        }
        console.warn(`[429 Rate Limit Hit] Pausing execution for ${waitTime / 1000}s before retry ${i + 1}/${maxRetries}...`);
        await delay(waitTime);
        continue;
      }
      throw e;
    }
  }
  throw new Error("Max retries reached. The free tier API quota is fully exhausted.");
}

export async function reviewGitHubProfile(username: string): Promise<ProfileAnalysis> {
  if (!username) throw new Error("Username is required");
  
  const normalizedUser = username.toLowerCase();
  if (cache.has(normalizedUser)) {
    return { ...cache.get(normalizedUser)!, cached: true };
  }

  if (!process.env.GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY is missing in your environment. Please add it to .env.local");
  }

  try {
    // 1. Fetch public repositories for the user
    const { data: repos } = await octokit.rest.repos.listForUser({
      username,
      type: "public",
      sort: "updated",
      per_page: 5,
    });

    if (!repos || repos.length === 0) {
      throw new Error(`No public repositories found for user: ${username}`);
    }

    const results: ReviewResult[] = [];

    // 2. Fetch README for each repo
    let repoContextString = "";
    for (const repo of repos) {
      try {
        const { data: readme } = await octokit.rest.repos.getReadme({
          owner: username,
          repo: repo.name,
        });
        const readmeContent = Buffer.from(readme.content, "base64").toString("utf-8");
        repoContextString += `\n\n--- REPOSITORY: ${repo.name} ---\n${readmeContent.slice(0, 2500)}`;
      } catch (err: any) {
        // Skip missing readmes
      }
    }

    if (!repoContextString) {
        throw new Error("No READMEs found in any public repository to analyze.");
    }

    // 3. Send ALL data in ONE AI request to bypass API rate limits and speed up generation massively
    const prompt = `
      You are an expert technical recruiter assessing a candidate's GitHub profile.
      Below are the README contents of up to 5 repositories from this developer.
      
      Analyze the projects and provide a JSON object with:
      1. "results": An array of objects for each repository, each containing:
         - "repoName": The exact name of the repository.
         - "level": A string (Basic, Intermediate, or Advanced).
         - "assessment": A 1-2 line summary based purely on the README.
      2. "holisticSummary": A 1-paragraph summary of the developer's overall strengths and experience based on all provided projects.

      Respond ONLY with the raw JSON object, no markdown formatting.
      
      REPOSITORIES TO EVALUATE:
      ${repoContextString}
    `;

    let aiData: any;
    try {
      let aiResponse = await fetchWithRetry(prompt);
      aiResponse = aiResponse.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();
      aiData = JSON.parse(aiResponse);
    } catch (aiError: any) {
      throw new Error(`AI Evaluation failed: ${aiError.message}`);
    }

    // Map AI results to our known structure, matching them back to the original repos to maintain GitHub URLs
    const finalResults: ReviewResult[] = repos.map(repo => {
       const aiMatch = (aiData.results || []).find((r: any) => r.repoName === repo.name);
       return {
          repoName: repo.name,
          repoUrl: repo.html_url,
          level: (aiMatch && typeof aiMatch.level === "string") ? aiMatch.level : "Unknown",
          assessment: (aiMatch && typeof aiMatch.assessment === "string") ? aiMatch.assessment : "No analysis could be performed or no README was found.",
       };
    });

    const payload: ProfileAnalysis = { 
        results: finalResults, 
        holisticSummary: aiData.holisticSummary || "No summary generated." 
    };
    cache.set(normalizedUser, payload);
    return payload;

  } catch (err: any) {
     if (err.status === 404) throw new Error(`GitHub user '${username}' not found.`);
     throw new Error(err.message || "Failed to fetch data from GitHub.");
  }
}
