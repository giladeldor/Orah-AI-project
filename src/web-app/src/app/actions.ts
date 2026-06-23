"use server";

import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";

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
    // Locate Python executable from a list of candidate locations
    const pythonCandidates = [
      path.join(process.cwd(), '..', '.venv', 'Scripts', 'python.exe'),
      path.join(process.cwd(), '.venv', 'Scripts', 'python.exe'),
      path.join(process.cwd(), '..', '..', '.venv', 'Scripts', 'python.exe'),
      path.join(process.cwd(), '..', '.venv', 'bin', 'python'),
      path.join(process.cwd(), '.venv', 'bin', 'python')
    ];

    const runnerCandidates = [
      path.join(process.cwd(), '..', 'src', 'ai_runner.py'),
      path.join(process.cwd(), '..', '..', 'src', 'ai_runner.py'),
      path.join(process.cwd(), 'src', 'ai_runner.py')
    ];

    const venvPythonPath = pythonCandidates.find(p => fs.existsSync(p));
    const runnerPath = runnerCandidates.find(p => fs.existsSync(p));

    if (!venvPythonPath) throw new Error('Python executable not found in expected .venv locations.');
    if (!runnerPath) throw new Error('AI runner script not found (src/ai_runner.py).');

    // Pass the --json flag so we only get pure JSON through stdout
    const { stdout, stderr } = await execAsync(`"${venvPythonPath}" "${runnerPath}" ${normalizedUser} --json`);
    
    const parsedData = JSON.parse(stdout.trim());
    
     // If the python script returned an error inside JSON, surface a friendly message
     if (parsedData.error) {
       // Handle AI quota specifically
       if (parsedData.code === 429 || /quota|429/i.test(parsedData.error)) {
        const retry = parsedData.retry_after ? `Retry after ${Math.round(parsedData.retry_after)}s.` : "";
        throw new Error(`AI quota exceeded. ${retry} Ask the project owner to provide an API key or try again later.`);
       }
       throw new Error(parsedData.error);
     }
    
    return parsedData as ProfileAnalysis;

  } catch (err: any) {
     console.error("Exec error:", err);
     if (err.message.includes("not found")) throw new Error(`GitHub user '${username}' not found.`);
     throw new Error(err.message || "Failed to fetch data from GitHub / AI Core.");
  }
}
