import os
import argparse
from dotenv import load_dotenv
from github_service import get_user_repos, get_readme_content
from ai_service import evaluate_all_repos_at_once
from cache_service import get_cached_result, set_cached_result

load_dotenv()

def _print_results(repos, summary):
    for r in repos:
        print(f"--- Processing Repo: {r.get('repoName', 'Unknown')} ---")
        print(f"  Level: {r.get('level', 'Unknown')}")
        print(f"  Assessment: {r.get('assessment', 'N/A')}\n")
    print(f"======================================")
    print(f"🌟 HOLISTIC SUMMARY:\n{summary}")
    print(f"======================================\n")

def main():
    parser = argparse.ArgumentParser(description="GitHub Profile Reviewer CLI")
    parser.add_argument("username", help="GitHub username to review")
    args = parser.parse_args()
    username = args.username
    print(f"\n🔍 Starting review for GitHub user: {username}\n")
    
    cached_data = get_cached_result(username)
    if cached_data:
        print(f"⚡ [CACHE HIT] Loaded results for {username} from local cache:\n")
        _print_results(cached_data["repos"], cached_data["summary"])
        return

    try:
        repos = get_user_repos(username)
        print(f"Found {len(repos)} public repositories. Fetching READMEs (this is fast now)...\n")

        repo_contents = {}
        for repo in repos:
            repo_name = repo["name"]
            readme_content = get_readme_content(repo["full_name"])
            if readme_content:
                repo_contents[repo_name] = readme_content

        if not repo_contents:
            print("No READMEs found in any public repository.")
            return

        print("🧠 Sending batched request to Gemini (Bypasses rate limit and extreme delays)...")
        # One fast API call instead of 6 slow ones!
        ai_data = evaluate_all_repos_at_once(repo_contents)
        
        assessments_list = ai_data.get("results", [])
        summary = ai_data.get("summary", "No summary generated.")

        _print_results(assessments_list, summary)
        set_cached_result(username, {"repos": assessments_list, "summary": summary})

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
