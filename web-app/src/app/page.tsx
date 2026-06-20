"use client";

import { useState } from "react";
import { reviewGitHubProfile, ReviewResult } from "./actions";

export default function Home() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ReviewResult[] | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Clean up inputs like full URLs
      const cleanUsername = username.replace(/^https?:\/\/github\.com\//, "").replace(/\/$/, "");
      
      const data = await reviewGitHubProfile(cleanUsername);
      setResults(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 sm:p-20 font-sans max-w-4xl mx-auto bg-zinc-50 dark:bg-black text-black dark:text-zinc-50">
      <header className="mb-12 text-center">
        <h1 className="text-3xl font-bold mb-4">GitHub Profile Reviewer (AI-Native)</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Enter a GitHub username to automatically analyze their recent public repositories using AI.
        </p>
      </header>

      <main className="flex flex-col gap-8">
        <form onSubmit={handleSubmit} className="flex gap-4 flex-col sm:flex-row w-full max-w-lg mx-auto">
          <input
            type="text"
            className="flex-1 px-4 py-3 rounded-md border border-zinc-300 dark:border-zinc-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. torvalds or https://github.com/torvalds"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !username}
            className="px-6 py-3 rounded-md bg-zinc-900 text-white dark:bg-zinc-100 dark:text-black font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Review Profile"}
          </button>
        </form>

        {error && (
          <div className="p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md text-center max-w-lg mx-auto w-full">
            {error}
          </div>
        )}

        {results && (
          <div className="flex flex-col gap-6 mt-8">
            <h2 className="text-xl font-semibold mb-2 text-center">
              Analysis Results for <span className="text-blue-500">@{username.split("/").pop()}</span>
            </h2>
            <div className="grid gap-6">
              {results.map((repo, i) => (
                <div key={i} className="border border-zinc-200 dark:border-zinc-800 rounded-lg p-6 shadow-sm bg-white dark:bg-zinc-900">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-bold">
                      <a href={repo.repoUrl} target="_blank" rel="noreferrer" className="hover:underline text-blue-600 dark:text-blue-400">
                        {repo.repoName}
                      </a>
                    </h3>
                    <span className={
                      "px-3 py-1 text-xs font-semibold rounded-full " +
                      (repo.level.toLowerCase().includes("advanced") ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300" :
                        repo.level.toLowerCase().includes("intermediate") ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300" :
                        repo.level.toLowerCase().includes("error") || repo.level.includes("Unknown") ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" :
                          "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300")
                    }>
                      {repo.level}
                    </span>
                  </div>
                  <p className="text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">
                    <span className="font-semibold block mb-1">Assessment:</span>
                    {repo.assessment}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
