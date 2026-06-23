import os
import json
import time
import base64
import requests
import warnings
import google.generativeai as genai

# Suppress the deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning)


# Import shared logger configured in logger.py
from common.logger import logger

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'cache', '.profile_cache.json')
CACHE_EXPIRATION_SECONDS = 3600  # 1 hour


class reposAnalyzer:
    """Encapsulates repository fetching, batching and AI evaluation."""

    def __init__(self):
        # instance-level placeholders (if needed later)
        self.cache_file = CACHE_FILE
        self.cache_ttl = CACHE_EXPIRATION_SECONDS

    def _fetch_all_public_repos(self, username: str, headers: dict):
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

    def _build_batch_prompt(self, repo_batch):
        repo_text = ""
        for repo in repo_batch:
            repo_text += f"\n\n--- REPOSITORY: {repo['name']} ---\n{repo['readme'][:1500]}"

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

    def _analyze_repositories_in_batches(self, model, repo_readmes):
        all_results = []
        current_batch = []
        current_chars = 0
        max_batch_chars = 40000

        for repo in repo_readmes:
            item_chars = len(repo["readme"])
            if current_batch and (current_chars + item_chars > max_batch_chars):
                prompt = self._build_batch_prompt(current_batch)
                ai_response = self._generate_with_retry(model, prompt)
                clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
                try:
                    parsed = json.loads(clean_response)
                except Exception as je:
                    raise ValueError(f"Failed to parse AI response as JSON: {je}\nResponse was: {clean_response[:1000]}")

                # Support two common shapes: {"results": [...]} or a top-level list [...]
                if isinstance(parsed, dict):
                    results = parsed.get("results", [])
                elif isinstance(parsed, list):
                    results = parsed
                else:
                    results = []

                all_results.extend(results)
                current_batch = []
                current_chars = 0

            current_batch.append(repo)
            current_chars += item_chars

        if current_batch:
            prompt = self._build_batch_prompt(current_batch)
            ai_response = self._generate_with_retry(model, prompt)
            clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
            try:
                parsed = json.loads(clean_response)
            except Exception as je:
                raise ValueError(f"Failed to parse AI response as JSON: {je}\nResponse was: {clean_response[:1000]}")

            if isinstance(parsed, dict):
                results = parsed.get("results", [])
            elif isinstance(parsed, list):
                results = parsed
            else:
                results = []

            all_results.extend(results)

        return all_results

    def _generate_holistic_summary(self, model, repo_results):
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
        return self._generate_with_retry(model, prompt).strip()

    def get_cached_result(self, username):
        if not os.path.exists(self.cache_file):
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                entry = cache.get(username)
                if entry:
                    cached_time = entry.get("timestamp", 0)
                    if time.time() - cached_time < self.cache_ttl:
                        logger.info(f"Cache hit for user: {username}")
                        return entry.get("data")
                    else:
                        logger.info(f"Cache expired for user: {username}")
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None

    def set_cached_result(self, username, data):
        cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                pass
        cache[username] = {
            "timestamp": time.time(),
            "data": data
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

    def _generate_with_retry(self, model, prompt, max_retries=5):
        import re
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower():
                    if attempt < max_retries - 1:
                        match = re.search(r"retry[_\s]after[\":\s]+([\d\.]+)", err_str, re.IGNORECASE) or \
                                re.search(r"retry in ([\d\.]+)s", err_str, re.IGNORECASE)
                        if match:
                            wait_time = float(match.group(1)) + 3.0
                        else:
                            wait_time = min(15 * (2 ** attempt), 120)
                        logger.warning(f"[429 Rate Limit Hit] Waiting {wait_time:.1f}s before retry {attempt+1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                raise e

    def evaluate_profile(self, username: str):
        logger.info(f"Starting review for '{username}'")

        # 1. Check Cache
        cached = self.get_cached_result(username)
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
        repos = self._fetch_all_public_repos(username, headers)

        if not repos:
            raise ValueError("No public repositories found.")

        # Cap to top 12 most recently updated repos to minimize API calls
        repos = repos[:12]

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
            ai_results = self._analyze_repositories_in_batches(model, repo_readmes)
            holistic_summary = self._generate_holistic_summary(model, ai_results)
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
        self.set_cached_result(username, payload)

        return payload


def evaluate_profile(username: str):
    analyzer = reposAnalyzer()
    return analyzer.evaluate_profile(username)

# if __name__ == "__main__":
#     import sys
#     import argparse
    
#     # Silence standard logging output if we want clean JSON
#     parser = argparse.ArgumentParser()
#     parser.add_argument("username", help="GitHub username")
#     parser.add_argument("--json", action="store_true", help="Output raw JSON via stdout")
#     args = parser.parse_args()

#     if args.json:
#         # turn off stream handler so it doesn't pollute json output
#         logger.removeHandler(stream_handler)

#     try:
#         data = evaluate_profile(args.username)
#         if args.json:
#             print(json.dumps(data))
#         else:
#             if data.get("cached"):
#                 print(f"⚡ [CACHE HIT] Loaded results for {args.username}\n")
#             # Standard print block
#             for r in data["results"]:
#                 print(f"--- {r['repoName']} ---")
#                 print(f"Level: {r['level']}")
#                 print(f"Assessment: {r['assessment']}\n")
#             print("🌟 HOLISTIC SUMMARY 🌟")
#             print(data["holisticSummary"])
#     except Exception as e:
#         if args.json:
#             print(json.dumps({"error": str(e)}))
#         else:
#             print(f"Error: {e}")