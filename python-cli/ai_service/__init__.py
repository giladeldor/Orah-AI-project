import os
import json
import google.generativeai as genai

def get_ai_assessment(readme_content: str, repo_name: str):
    """Sends README content to Gemini for assessment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
        You are an expert technical recruiter assessing a candidate's GitHub project.
        Below is the content of the README.md file for the repository "{repo_name}".
        
        Analyze the project and provide a JSON object with three keys:
        1. "level": (A string that must be one of: "Basic", "Intermediate", or "Advanced")
        2. "assessment": (A string containing a 1-3 line summary of the project, its complexity, clarity, and the experience it reflects based ONLY on the README.)
        3. "repoName": (A string with the repository name: "{repo_name}")

        Your entire response must be ONLY the raw JSON object, with no extra text, explanations, or markdown formatting.

        README CONTENT:
        ----------------
        {readme_content[:4000]}
    """

    try:
        response = model.generate_content(prompt)
        ai_response = response.text
        
        # Clean the response to ensure it's a valid JSON string
        clean_response = ai_response.strip().replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_response)

        return parsed_json.get("level", "Unknown"), parsed_json.get("assessment", "Failed to parse AI response.")

    except (json.JSONDecodeError, AttributeError) as e:
        return "Error", f"AI response parsing failed: {str(e)}. Raw response: {ai_response}"
    except Exception as e:
        return "Error", f"AI evaluation failed: {str(e)}"
