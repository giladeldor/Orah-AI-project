import os
import argparse
from dotenv import load_dotenv
from github_service import get_user_repos, get_readme_content
from ai_service import get_ai_assessment

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="GitHub Profile Reviewer CLI")
    parser.add_argument("username", help="GitHub username to review")
    args = parser.parse_args()
    
    username = args.username
    print(f"🔍 Starting review for GitHub user: {username}\n")
    
    try:
        # 1. Fetch GitHub repos
        repos = get_user_repos(username)
        print(f"Found {len(repos)} public repositories. Analyzing...\n")

        # 2. Process each repo
        for repo in repos:
            repo_name = repo["name"]
            repo_url = repo["html_url"]
            print(f"--- Processing Repo: {repo_name} ---")
            
            # 3. Get README
            readme_content = get_readme_content(repo["full_name"])
            
            if not readme_content:
                print("  Level: Unknown")
                print("  Assessment: No README file found in this repository.\n")
                continue

            # 4. Get AI Assessment
            level, assessment = get_ai_assessment(readme_content, repo_name)
            
            print(f"  Level: {level}")
            print(f"  Assessment: {assessment}\n")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
