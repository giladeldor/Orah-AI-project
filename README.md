# 🚀 AI-Native GitHub Profile Reviewer

An intelligent, dual-interface diagnostic tool (Next.js Web App & Python CLI) that automatically evaluates a developer's GitHub portfolio. It ingests public repositories, reads their codebases (READMEs), and leverages the **Google Gemini 2.5 Flash** model to provide a holistic assessment of the candidate's skill level.

Designed natively for high performance, featuring **Batched LLM Prompting**, **In-Memory/Local Caching**, and **Smart API Rate-Limit Handling**.

---

## 🌟 Key Architectural Features

1. **Batched "One-Shot" AI Processing**: 
   Instead of looping API requests (which quickly exhausts free-tier AI quotas and throttles networks), the app dynamically aggregates ALL public repositories (with smart batching to avoid token limits), processes them in parallel groups, and generates a holistic developer summary. This approach is fast, scalable, and completely eliminates redundant API calls.
2. **Resilient Rate-Limiting & Retries**: 
   Intercepts HTTP 429 Quota Exhaustion codes directly from the Google API, autonomously parsing the `Retry-After` metrics, pausing execution gracefully, and resuming without crashing.
3. **Multi-layer Caching Strategy with Expiration**: 
   - *Web App*: Employs an in-memory cache in the Python backend that auto-expires after 1 hour.
   - *Python CLI*: Persists successful generation payloads to a local `.profile_cache.json` with timestamp validation, ensuring cache freshness while eliminating redundant AI calls.
4. **Adaptive UI Fallbacks**:
   Safely handles AI hallucinations. If the LLM omits a JSON property, the responsive Next.js Glassmorphism UI elegantly falls back without crashing the React virtual DOM.

---

## 💻 Web Application (`/web-app`)

A premium, interactive React 19 / Next.js application styled with Tailwind CSS v4. 
Includes gorgeous slide-in animations, dynamic SVGs, and real-time scanning loaders.

### 🛠️ Setup & Run
1. Navigate to the directory: `cd web-app`
2. Install Node dependencies: `npm install`
3. Configure your Environment Variables in `web-app/.env.local`:
   ```env
   GEMINI_API_KEY="your_gemini_api_key_here"
   GITHUB_TOKEN="your_github_token_here"
   ```
4. Start the frontend: `npm run dev`
5. Open `http://localhost:3000`

---

## ⚙️ Python CLI (`/python-cli`)

A modular, lightweight Python application structured for direct terminal injection.
Both the Web App and CLI share the same core logic in `src/ai_core.py`.

### 🛠️ Setup & Run (with Poetry)
1. Install Poetry if you haven't already:
   ```bash
   pip install poetry
   ```
2. Install project dependencies:
   ```bash
   poetry install
   ```
3. Configure your Environment Variables in `python-cli/.env`:
   ```env
   GEMINI_API_KEY="your_gemini_api_key_here"
   GITHUB_TOKEN="your_github_token_here"
   ```
4. Run the script against any username:
   ```bash
   poetry run python python-cli/main.py torvalds
   ```
   Or activate the Poetry shell:
   ```bash
   poetry shell
   python python-cli/main.py torvalds
   ```

---

## 🤝 Decision-Making & AI Workflow
This architecture was designed in collaboration with an AI pairing agent. 
Early sequential processing strategies were scrapped in favor of payload aggregation to bypass strict 20-Request/Day limits. 
State-caching paradigms and rigorous string-matching error boundaries were introduced post-scaffolding to achieve enterprise-level robustness.
