import sys
import json
from common.repos_analyzer import evaluate_profile
from dotenv import load_dotenv

def main():
    load_dotenv()
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "username required"}))
        sys.exit(1)
    username = args[0]
    json_out = "--json" in args
    try:
        result = evaluate_profile(username)
        if json_out:
            print(json.dumps(result))
        else:
            # human readable
            if result.get("cached"):
                print(f"⚡ [CACHE HIT] Loaded results for {username}\n")
            for r in result["results"]:
                print(f"--- {r.get('repoName', 'Unknown')} ---")
                print(f"Level: {r.get('level', 'Unknown')}")
                print(f"Assessment: {r.get('assessment', 'N/A')}\n")
            print("🌟 HOLISTIC SUMMARY 🌟")
            print(result.get("holisticSummary", "No summary generated."))
    except Exception as e:
        if json_out:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
