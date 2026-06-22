"use server";

import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

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

// Caching and expiration is now strictly handled inside the Python Core (src/ai_core.py)!
export async function reviewGitHubProfile(username: string): Promise<ProfileAnalysis> {
  if (!username) throw new Error("Username is required");
  const normalizedUser = username.toLowerCase();

  try {
    // We execute the single shared Python logic engine (ai_core.py) using the local .venv
    const venvPythonPath = path.join(process.cwd(), "..", ".venv", "Scripts", "python.exe");
    const aiCorePath = path.join(process.cwd(), "..", "src", "ai_core.py");
    
    // Pass the --json flag so we only get pure JSON through stdout
    const { stdout, stderr } = await execAsync(`"${venvPythonPath}" "${aiCorePath}" ${normalizedUser} --json`);
    
    const parsedData = JSON.parse(stdout.trim());
    
    // If the python script returned an error inside JSON, throw it to the UI
    if (parsedData.error) {
       throw new Error(parsedData.error);
    }
    
    return parsedData as ProfileAnalysis;

  } catch (err: any) {
     console.error("Exec error:", err);
     if (err.message.includes("not found")) throw new Error(`GitHub user '${username}' not found.`);
     throw new Error(err.message || "Failed to fetch data from GitHub / AI Core.");
  }
}
