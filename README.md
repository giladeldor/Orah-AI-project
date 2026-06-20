# 🚀 AI-Native GitHub Profile Reviewer

An intelligent, dual-interface diagnostic tool (Next.js Web App & Python CLI) that automatically evaluates a developer's GitHub portfolio. It ingests public repositories, reads their codebases (READMEs), and leverages the **Google Gemini 2.5 Flash** model to provide a holistic assessment of the candidate's skill level.

Designed natively for high performance, featuring **Batched LLM Prompting**, **In-Memory/Local Caching**, and **Smart API Rate-Limit Handling**.

---

## 🌟 Key Architectural Features

1. **Batched "One-Shot" AI Processing**: 
   Instead of looping API requests (which quickly exhausts free-tier AI quotas and throttles networks), the app dynamically aggregates all repository data into a single, massive context window. This evaluates 5 repos + generates a holistic developer summary in <3 seconds.
2. **Resilient Rate-Limiting & Retries**: 
   Intercepts HTTP 429 Quota Exhaustion codes directly from the Google API, autonomously parsing the `Retry-After` metrics, pausing execution gracefully, and resuming without crashing.
3. **Multi-layer Caching Strategy**: 
   - *Web App*: Employs an ultra-fast Next.js Server-Side `Map()` Cache. Subsequent queries to the same username render instantaneously with a `Cache Hit` UI validation payload.
   - *Python CLI*: Persists successful generation payloads to a local `.profile_cache.json` system, bypassing web dependency entirely on repeated lookups.
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

A modular, lightweight python application structured for direct terminal injection.

### 🛠️ Setup & Run
1. Navigate to the directory: `cd python-cli`
2. Ensure you have your `venv` active and dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Environment Variables in `python-cli/.env`:
   ```env
   GEMINI_API_KEY="your_gemini_api_key_here"
   GITHUB_TOKEN="your_github_token_here"
   ```
4. Run the script against any username:
   ```bash
   python main.py torvalds
   ```

---

## 🤝 Decision-Making & AI Workflow
This architecture was designed in collaboration with an AI pairing agent. 
Early sequential processing strategies were scrapped in favor of payload aggregation to bypass strict 20-Request/Day limits. 
State-caching paradigms and rigorous string-matching error boundaries were introduced post-scaffolding to achieve enterprise-level robustness.
