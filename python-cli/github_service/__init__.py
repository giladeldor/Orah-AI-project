import os
import requests
import base64

def get_user_repos(username: str):
    """Fetches public repositories for a given GitHub username."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=5"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
    return response.json()

def get_readme_content(repo_full_name: str):
    """Fetches and decodes the README content for a given repository."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return None # README not found is not a critical error
        
    response.raise_for_status()
    
    readme_data = response.json()
    content_base64 = readme_data.get("content", "")
    return base64.b64decode(content_base64).decode("utf-8")
