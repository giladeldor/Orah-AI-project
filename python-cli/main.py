import os
import sys
import argparse

# Inject root into python path so we can import the shared src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.ai_core import evaluate_profile

def main():
    parser = argparse.ArgumentParser(description="GitHub Profile Reviewer CLI")
    parser.add_argument("username", help="GitHub username to review")
    args = parser.parse_args()
    
    try:
        data = evaluate_profile(args.username)
        if data.get("cached"):
            print(f"⚡ [CACHE HIT] Loaded results for {args.username}\n")
            
        for r in data["results"]:
            print(f"--- {r.get('repoName', 'Unknown')} ---")
            print(f"Level: {r.get('level', 'Unknown')}")
            print(f"Assessment: {r.get('assessment', 'N/A')}\n")
            
        print("🌟 HOLISTIC SUMMARY 🌟")
        print(data.get("holisticSummary", "No summary generated."))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
