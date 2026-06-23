import argparse
from common.repos_analyzer import evaluate_profile
from common.logger import logger
from dotenv import load_dotenv

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="GitHub Profile Reviewer CLI")
    parser.add_argument("username", help="GitHub username to review")
    args = parser.parse_args()
    
    try:
        logger.info(f"CLI: Starting review for '{args.username}'")
        data = evaluate_profile(args.username)
        if data.get("cached"):
            logger.info(f"CACHE HIT for {args.username}")
            logger.info(f"⚡ [CACHE HIT] Loaded results for {args.username}")

        for r in data["results"]:
            logger.info(f"--- {r.get('repoName', 'Unknown')} ---")
            logger.info(f"Level: {r.get('level', 'Unknown')}")
            logger.info(f"Assessment: {r.get('assessment', 'N/A')}")

        logger.info("🌟 HOLISTIC SUMMARY 🌟")
        logger.info(data.get("holisticSummary", "No summary generated."))
    except Exception as e:
        logger.exception(f"CLI error while reviewing '{args.username}': {e}")
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
