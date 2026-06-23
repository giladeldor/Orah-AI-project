# 🚀 AI-Native GitHub Profile Reviewer

An intelligent, dual-interface diagnostic tool (Next.js Web App & Python CLI) that automatically evaluates a developer's GitHub portfolio. It ingests public repositories, reads their codebases (READMEs), and leverages the **Google Gemini 2.5 Flash** model to provide a holistic assessment of the candidate's skill level.

Designed natively for high performance, featuring **Batched LLM Prompting**, **In-Memory/Local Caching**, and **Smart API Rate-Limit Handling**.

---
# GitHub Profile Reviewer

Lightweight toolset to analyze a GitHub profile using a shared Python core, a
CLI, and a Next.js web UI. The core fetches public repositories and READMEs,
batches prompts to an LLM, and returns per-repo assessments and a holistic
summary. Caching and logging live under `src/cache` and `src/logs`.

This README covers the updated run paths, env vars, and how we handle AI
quota (429) responses.

---

## Quick setup (recommended: Poetry)

1. Install Poetry: https://python-poetry.org/
2. Create and activate an environment with Poetry, then install deps:

```bash
poetry install
poetry shell
```

If you prefer a traditional venv:

```powershell
# from project root (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt  # or pip install requests python-dotenv google-generativeai
```

Note: The repo currently uses the `google.generativeai` package (deprecated);
plan to migrate to `google.genai` when you provision an API key.

---

## Environment variables

- `GEMINI_API_KEY` — required for AI calls (Gemini). Place in a `.env` file or
  export in your shell.
- `GITHUB_TOKEN` — optional but recommended to avoid GitHub rate limits.

Create a `.env` with:

```ini
GEMINI_API_KEY=your_api_key_here
GITHUB_TOKEN=ghp_...
```

---

## Running the Python runner (used by the web action)

The runner wraps the core and can output JSON for the UI.

```powershell
# using project venv
.\.venv\Scripts\python.exe src\ai_runner.py <github_username> --json
```

Example:

```powershell
.\.venv\Scripts\python.exe src\ai_runner.py giladeldor --json
```

On AI quota errors the runner will return a structured JSON error with fields
`error`, `code` (429), `message` and optional `retry_after` (seconds). The web
UI surfaces a friendly message when this occurs.

---

## Running the CLI

```powershell
.\.venv\Scripts\python.exe src\python_cli\main.py <github_username>
```

Add `--json` when running `src\ai_runner.py` directly to get machine-readable
output.

---

## Running the Web App (Next.js)

From `web-app`:

```bash
cd web-app
pnpm install   # or npm/yarn
pnpm dev
```

Notes:
- The Server Action calls `src/ai_runner.py` via the detected `.venv` python.
- If you update `web-app/src/app/actions.ts` make sure to restart the dev
  server and clear the `.next` cache if you see stale paths:

```powershell
rm -r web-app\.next
# then restart dev server
```

---

## Logs and cache

- Logs: `src/logs/app.log` — application and AI-call logs.
- Cache: `src/cache/.profile_cache.json` — cached per-username results (1h TTL).

Tail logs (PowerShell):

```powershell
Get-Content src\logs\app.log -Tail 200 -Wait
```

---

## Handling AI quota (429)

The system implements exponential backoff for transient 429s, but when the
quota is exceeded the analyzer now returns a structured error JSON so the web
UI can show a clear message. Short-term options:

- Wait and retry after the `retry_after` seconds returned in the error.
- Reduce downstream AI calls by increasing batch sizes or capping repos.
- Provision a paid API key / higher quota and set `GEMINI_API_KEY`.

---

## Troubleshooting

- If the web UI reports `AI quota exceeded`, either wait or ask the project
  owner to add an API key.
- If the Server Action still references old paths like `src/src/ai_core.py`,
  delete `web-app/.next` and restart the dev server.
- If Python modules are missing, ensure you're using the correct `.venv` and
  run `pip install -r requirements.txt` or `poetry install`.

---

## Developer notes

- Core: `src/common/repos_analyzer.py`
- Runner: `src/ai_runner.py`
- CLI: `src/python_cli/main.py`
- Web action: `web-app/src/app/actions.ts` and `src/web-app/src/app/actions.ts` (dev copies).

If you'd like, I can also update the README to include sample outputs or add a
small troubleshooting script to reproduce 429s for testing.

---

Happy hacking!

