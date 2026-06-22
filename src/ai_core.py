import os
import json
import time
import base64
import logging
import requests
import warnings
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Suppress the deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning)

# Try to load either the CLI or Web App env files based on what's available
cli_env = os.path.join(os.path.dirname(__file__), '..', 'python-cli', '.env')
web_env = os.path.join(os.path.dirname(__file__), '..', 'web-app', '.env.local')
if os.path.exists(cli_env):
    load_dotenv(cli_env)
elif os.path.exists(web_env):
    load_dotenv(web_env)
else:
    load_dotenv()

# Setup Logger
logger = logging.getLogger("AI_Reviewer")
logger.setLevel(logging.INFO)
log_file = os.path.join(os.path.dirname(__file__), 'app.log')
file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".profile_cache.json")
CACHE_EXPIRATION_SECONDS = 3600  # 1 hour

def get_cached_result(username):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            entry = cache.get(username)
            if entry:
                # Check timestamp
                cached_time = entry.get("timestamp", 0)
                if time.time() - cached_time < CACHE_EXPIRATION_SECONDS:
                    logger.info(f"Cache hit for user: {username}")
                    return entry.get("data")
                else:
                    logger.info(f"Cache expired for user: {username}")
    except Exception as e:
        logger.error(f"Cache read error: {e}")
    return None

def set_cached_result(username, data):
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
    cache[username] = {
        "timestamp": time.time(),
        "data": data
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def _generate_with_retry(model, prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = 15
                    import re
                    match = re.search(r"retry in ([\d\.]+)s", str(e))
                    if match:
                        wait_time = float(match.group(1)) + 2.0
                    logger.warning(f"[429 Rate Limit Hit] Waiting {wait_time:.1f}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
            raise e

def evaluate_profile(username: str):
    logger.info(f"Starting review for '{username}'")
    
    # 1. Check Cache
    cached = get_cached_result(username)
    if cached:
        cached["cached"] = True
        return cached

    # 2. Setup APIs
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is missing from environment")
        raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}

    # 3. Fetch Repos
    logger.info("Fetching GitHub public repositories...")
    url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=5"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        raise ValueError(f"GitHub user '{username}' not found.")
    resp.raise_for_status()
    repos = resp.json()

    if not repos:
        raise ValueError("No public repositories found.")

    # 4. Fetch READMEs
    repo_text = ""
    original_repos = []
    
    for repo in repos:
        repo_name = repo["name"]
        repo_url = repo["html_url"]
        original_repos.append({"name": repo_name, "url": repo_url})
        
        readme_url = f"https://api.github.com/repos/{repo['full_name']}/readme"
        rm_resp = requests.get(readme_url, headers=headers)
        if rm_resp.status_code == 200:
            content_b64 = rm_resp.json().get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            repo_text += f"\n\n--- REPOSITORY: {repo_name} ---\n{content[:2500]}"
            logger.info(f"Fetched README for {repo_name}")
        else:
            logger.warning(f"No README found for {repo_name}")

    if not repo_text:
        raise ValueError("No READMEs found in any repository to analyze.")

    # 5. Execute AI Batch Prompt
    logger.info("Building batched prompt and sending to Gemini API...")
    prompt = f"""
        You are an expert technical recruiter assessing a candidate's GitHub profile.
        Below are the README contents of up to 5 repositories from this developer.
        
        Analyze the projects and provide a JSON object with:
        1. "results": An array of objects for each repository, each containing:
           - "repoName": The exact name of the repository.
           - "level": A string (Basic, Intermediate, or Advanced).
           - "assessment": A 1-2 line summary.
        2. "summary": A 1-paragraph summary of the developer's overall strengths and experience based on all provided projects.

        Respond ONLY with the raw JSON object, no markdown formatting.

        REPOSITORIES TO EVALUATE:
        {repo_text}
    """
    
    try:
        ai_response = _generate_with_retry(model, prompt)
        clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_response)
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        raise ValueError(f"AI evaluation failed: {e}")

    # 6. Map results
    final_results = []
    ai_results = parsed_json.get("results", [])
    
    for obj in original_repos:
        match = next((r for r in ai_results if r.get("repoName") == obj["name"]), None)
        final_results.append({
            "repoName": obj["name"],
            "repoUrl": obj["url"],
            "level": str(match.get("level", "Unknown")) if match else "Unknown",
            "assessment": str(match.get("assessment", "No README analysis via AI.")) if match else "No README analysis via AI."
        })

    payload = {
        "results": final_results,
        "holisticSummary": parsed_json.get("summary", "No summary generated."),
        "cached": False
    }

    # 7. Cache & Return
    logger.info("Successfully generated AI review payload.")
    set_cached_result(username, payload)
    
    return payload

if __name__ == "__main__":
    import sys
    import argparse
    
    # Silence standard logging output if we want clean JSON
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--json", action="store_true", help="Output raw JSON via stdout")
    args = parser.parse_args()

    if args.json:
        # turn off stream handler so it doesn't pollute json output
        logger.removeHandler(stream_handler)

    try:
        data = evaluate_profile(args.username)
        if args.json:
            print(json.dumps(data))
        else:
            if data.get("cached"):
                print(f"⚡ [CACHE HIT] Loaded results for {args.username}\n")
            # Standard print block
            for r in data["results"]:
                print(f"--- {r['repoName']} ---")
                print(f"Level: {r['level']}")
                print(f"Assessment: {r['assessment']}\n")
            print("🌟 HOLISTIC SUMMARY 🌟")
            print(data["holisticSummary"])
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}")