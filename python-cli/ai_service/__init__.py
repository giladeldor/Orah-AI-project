import os
import json
import time
import google.generativeai as genai

def _generate_with_retry(model, prompt, max_retries=4):
    """Executes Gemini generation with backoff for rate limits."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt < max_retries - 1:
                    # Look for "Please retry in X" in the error to wait exactly that long if available
                    wait_time = 15  # Default wait for RPM limit
                    import re
                    match = re.search(r"retry in ([\d\.]+)s", str(e))
                    if match:
                        wait_time = float(match.group(1)) + 1
                    
                    print(f"    [Rate Limit Hit] Waiting {wait_time:.1f}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
            raise e

def evaluate_all_repos_at_once(repo_contents: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    repo_text = ""
    for name, content in repo_contents.items():
        repo_text += f"\n\n--- REPOSITORY: {name} ---\n"
        repo_text += content[:2500]  # truncate to avoid token blows

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
        return parsed_json
    except Exception as e:
        return {"results": [], "summary": f"Failed to generate holistic summary due to AI evaluation error: {str(e)}"}
