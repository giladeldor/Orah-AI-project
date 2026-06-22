"use client";

import { useState } from "react";
import { reviewGitHubProfile, ProfileAnalysis } from "./actions";

export default function Home() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ProfileAnalysis | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const cleanUsername = username.replace(/^https?:\/\/github\.com\//, "").replace(/\/$/, "");
      const data = await reviewGitHubProfile(cleanUsername);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen font-sans bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 selection:bg-blue-500/30">
      <div className="max-w-5xl mx-auto px-6 py-12 sm:py-24">
        {/* Header */}
        <header className="mb-16 text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 bg-zinc-900 dark:bg-zinc-100 rounded-2xl shadow-sm mb-6">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-white dark:text-black">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.545 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.285 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
            AI Profile Reviewer
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
            Analyze any developer's GitHub portfolio in seconds. We read the repos, understand the code, and give you an expert rundown.
          </p>
        </header>

        {/* Search Form */}
        <main className="flex flex-col items-center w-full max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative w-full group mb-10">
            <div className="absolute inset-y-0 left-0 flex items-center pl-5 pointer-events-none">
              <span className="text-zinc-400 dark:text-zinc-500 font-medium text-lg">github.com/</span>
            </div>
            <input
              type="text"
              className="w-full pl-[110px] sm:pl-[120px] pr-32 py-5 text-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-zinc-400"
              placeholder="torvalds"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="off"
              spellCheck="false"
            />
            <button
              type="submit"
              disabled={loading || !username}
              className="absolute right-2 top-2 bottom-2 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:hover:bg-blue-600 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Scanning...
                </>
              ) : (
                "Analyze"
              )}
            </button>
          </form>

          {error && (
            <div className="w-full p-4 mb-8 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400 rounded-xl text-sm font-medium flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              {error}
            </div>
          )}

          {analysis && (
            <div className="w-full flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pb-4">
                 <h2 className="text-2xl font-bold tracking-tight">
                   @{username.split("/").pop()}
                 </h2>
                 {analysis.cached && (
                   <span className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] uppercase tracking-wide font-bold bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400 rounded-md border border-green-200 dark:border-green-500/20">
                     <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                     Cache Hit
                   </span>
                 )}
              </div>

              {/* HOLISTIC SUMMARY SECTION */}
              {analysis.holisticSummary && (
                <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-500/5 to-purple-500/5 border border-blue-100 dark:border-blue-900/30 p-8">
                  <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-blue-500 to-purple-500"></div>
                  <h3 className="text-sm uppercase tracking-widest font-bold text-blue-700 dark:text-blue-400 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                    AI Developer Assessment
                  </h3>
                  <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed text-lg">
                    {analysis.holisticSummary}
                  </p>
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                {analysis.results.map((repo, i) => {
                  const isAdvanced = (repo.level || "").toLowerCase().includes("advanced");
                  const isIntermediate = (repo.level || "").toLowerCase().includes("intermediate");
                  const isError = (repo.level || "").toLowerCase().includes("error") || (repo.level || "").toLowerCase().includes("unknown");
                  
                  return (
                    <div 
                      key={i} 
                      className="group relative flex flex-col justify-between border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 bg-white dark:bg-zinc-900 hover:shadow-lg hover:border-zinc-300 dark:hover:border-zinc-700 transition-all duration-300"
                    >
                      <div>
                        <div className="flex items-start justify-between mb-4">
                          <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 truncate pr-4">
                            <a href={repo.repoUrl} target="_blank" rel="noreferrer" className="hover:text-blue-600 dark:hover:text-blue-400 hover:underline inline-flex items-center gap-1.5 focus:outline-none focus:underline">
                              <svg className="w-5 h-5 text-zinc-400 group-hover:text-blue-500 transition-colors" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                              {repo.repoName}
                            </a>
                          </h3>
                        </div>
                        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6 line-clamp-3 leading-relaxed">
                          {repo.assessment}
                        </p>

                        <div className="hidden group-hover:block absolute left-4 right-4 top-16 z-20 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white/95 dark:bg-zinc-900/95 p-4 shadow-xl backdrop-blur-sm">
                          <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {repo.assessment}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center">
                         <span className={
                          "px-2.5 py-1 text-xs font-semibold rounded-md border " +
                          (isAdvanced ? "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/10 dark:text-purple-300 dark:border-purple-500/20" :
                           isIntermediate ? "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-500/10 dark:text-sky-300 dark:border-sky-500/20" :
                           isError ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-500/10 dark:text-red-300 dark:border-red-500/20" :
                            "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/20")
                        }>
                          {repo.level || "Unknown"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
