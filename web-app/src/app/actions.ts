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

export async function reviewGitHubProfile(username: string): Promise<ReviewResult[]> {
  if (!username) throw new Error("Username is required");
  
  if (!process.env.GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY is missing in your environment. Please add it to .env.local");
  }

  try {
    // 1. Fetch public repositories for the user
    const { data: repos } = await octokit.rest.repos.listForUser({
      username,
      type: "public",
      sort: "updated",
      per_page: 5, // Limiting to top 5 recently updated to avoid long waits & rate limits for now
    });

    if (!repos || repos.length === 0) {
      throw new Error(`No public repositories found for user: ${username}`);
    }

    const results: ReviewResult[] = [];

    // 2. Fetch README for each repo and analyze
    for (const repo of repos) {
      let readmeContent = "";
      try {
        const { data: readme } = await octokit.rest.repos.getReadme({
          owner: username,
          repo: repo.name,
        });
        
        // GitHub API returns BASE64 encoded content
        readmeContent = Buffer.from(readme.content, "base64").toString("utf-8");
      } catch (err: any) {
        // If README is missing (404), we can log/skip or review without it
        if (err.status === 404) {
          results.push({
            repoName: repo.name,
            repoUrl: repo.html_url,
            level: "Unknown",
            assessment: "No README file found in this repository.",
            error: "No README",
          });
          continue;
        } else {
             results.push({
                repoName: repo.name,
                repoUrl: repo.html_url,
                level: "Error",
                assessment: "Failed to fetch README.",
                error: err.message,
              });
              continue;
        }
      }

      // 3. Send to AI
      const prompt = `
        You are an expert technical recruiter assessing a candidate's GitHub project.
        Below is the content of the README.md file for the repository "${repo.name}".
        
        Analyze the project and provide a JSON object with three keys:
        1. "level": (A string that must be one of: "Basic", "Intermediate", or "Advanced")
        2. "assessment": (A string containing a 1-3 line summary of the project, its complexity, clarity, and the experience it reflects based ONLY on the README.)
        3. "repoName": (A string with the repository name: "${repo.name}")

        Your entire response must be ONLY the raw JSON object, with no extra text, explanations, or markdown formatting.

        README CONTENT:
        ----------------
        ${readmeContent.slice(0, 4000)}
      `;

      try {
        const result = await model.generateContent(prompt);
        let aiResponse = result.response.text();
        
        // Clean markdown backticks if AI returns them
        aiResponse = aiResponse.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();

        // Parse the JSON response
        const parsedJson = JSON.parse(aiResponse);

        results.push({
          repoName: parsedJson.repoName || repo.name,
          repoUrl: repo.html_url,
          level: parsedJson.level || "Unknown",
          assessment: parsedJson.assessment || "Failed to parse AI response.",
        });

      } catch (aiError: any) {
        results.push({
          repoName: repo.name,
          repoUrl: repo.html_url,
          level: "Error",
          assessment: "AI evaluation failed.",
          error: aiError.message,
        });
      }
    }

    return results;

  } catch (err: any) {
     if (err.status === 404) {
         throw new Error(`GitHub user '${username}' not found.`);
     }
     throw new Error(err.message || "Failed to fetch data from GitHub.");
  }
}
