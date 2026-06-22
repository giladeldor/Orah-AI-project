import os
import json
import time
import base64
import logging
import requests
import warnings
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

def _fetch_all_public_repos(username: str, headers: dict):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=100&page={page}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found.")
        resp.raise_for_status()
        page_items = resp.json()
        if not page_items:
            break
        repos.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
    return repos

def _build_batch_prompt(repo_batch):
    repo_text = ""
    for repo in repo_batch:
        repo_text += f"\n\n--- REPOSITORY: {repo['name']} ---\n{repo['readme'][:2500]}"

    return f"""
        You are an expert technical recruiter assessing a candidate's GitHub profile.
        Below are README contents for a subset of this developer's public repositories.

        Analyze the projects and provide a JSON object with ONLY one key:
        1. "results": An array of objects for each repository, each containing:
           - "repoName": The exact name of the repository.
           - "level": A string (Basic, Intermediate, or Advanced).
           - "assessment": A 1-2 line summary.

        Respond ONLY with the raw JSON object, no markdown formatting.

        REPOSITORIES TO EVALUATE:
        {repo_text}
    """

def _analyze_repositories_in_batches(model, repo_readmes):
    all_results = []
    current_batch = []
    current_chars = 0
    max_batch_chars = 22000

    for repo in repo_readmes:
        item_chars = len(repo["readme"])
        if current_batch and (current_chars + item_chars > max_batch_chars):
            prompt = _build_batch_prompt(current_batch)
            ai_response = _generate_with_retry(model, prompt)
            clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_response)
            all_results.extend(parsed.get("results", []))
            current_batch = []
            current_chars = 0

        current_batch.append(repo)
        current_chars += item_chars

    if current_batch:
        prompt = _build_batch_prompt(current_batch)
        ai_response = _generate_with_retry(model, prompt)
        clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_response)
        all_results.extend(parsed.get("results", []))

    return all_results

def _generate_holistic_summary(model, repo_results):
    compact = []
    for r in repo_results:
        compact.append({
            "repoName": r.get("repoName", "Unknown"),
            "level": r.get("level", "Unknown"),
            "assessment": r.get("assessment", "")
        })

    prompt = f"""
        Based on the following repository assessments for a developer:
        {json.dumps(compact, indent=2)[:50000]}

        Provide one concise paragraph summarizing overall strengths, experience level, and capabilities.
        Respond with plain text only.
    """
    return _generate_with_retry(model, prompt).strip()

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
    repos = _fetch_all_public_repos(username, headers)

    if not repos:
        raise ValueError("No public repositories found.")

    # 4. Fetch READMEs
    original_repos = []
    repo_readmes = []
    
    for repo in repos:
        repo_name = repo["name"]
        repo_url = repo["html_url"]
        original_repos.append({"name": repo_name, "url": repo_url})
        
        readme_url = f"https://api.github.com/repos/{repo['full_name']}/readme"
        rm_resp = requests.get(readme_url, headers=headers)
        if rm_resp.status_code == 200:
            content_b64 = rm_resp.json().get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            repo_readmes.append({"name": repo_name, "readme": content})
            logger.info(f"Fetched README for {repo_name}")
        else:
            logger.warning(f"No README found for {repo_name}")

    if not repo_readmes:
        raise ValueError("No READMEs found in any repository to analyze.")

    # 5. Execute AI analysis in batches so all repos can be included safely
    logger.info("Analyzing repository READMEs in batches...")
    try:
        ai_results = _analyze_repositories_in_batches(model, repo_readmes)
        holistic_summary = _generate_holistic_summary(model, ai_results)
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        raise ValueError(f"AI evaluation failed: {e}")

    # 6. Map results
    final_results = []
    
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
        "holisticSummary": holistic_summary or "No summary generated.",
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