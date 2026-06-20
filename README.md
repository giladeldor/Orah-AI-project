# GitHub Profile Reviewer

This project contains two tools to analyze a GitHub user's profile: a command-line interface (CLI) and a web application. Both tools fetch a user's public repositories, analyze their README files using an AI, and provide an assessment of each project.

This project was built with the assistance of an AI programming assistant to demonstrate effective human-AI collaboration.

## Features

- **Dual Interface**: Choose between a fast CLI or an interactive web app.
- **AI-Powered Analysis**: Uses Google's Gemini model to assess project complexity, README clarity, and developer experience.
- **Error Handling**: Gracefully handles common issues like missing user profiles or README files.
- **Clean, Modular Code**: Both projects are structured for readability and maintainability.

---

## Web Application (`web-app`)

A modern, responsive Next.js application for a more visual and interactive experience.

### How to Run

1.  **Navigate to the web-app directory**:
    ```bash
    cd web-app
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Set up environment variables**:
    -   Rename the `.env.local.example` file to `.env.local`.
    -   Add your Google Gemini API key to the file. You can get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    -   (Optional) Add a GitHub Personal Access Token to avoid rate limits.

    ```env
    # .env.local
    GEMINI_API_KEY=your_gemini_api_key_here
    GITHUB_TOKEN=your_github_token_here
    ```

4.  **Run the development server**:
    ```bash
    npm run dev
    ```

5.  Open your browser to `http://localhost:3000`.

---

## Python CLI (`python-cli`)

A lightweight and fast command-line tool for quick analyses directly in your terminal.

### How to Run

1.  **Navigate to the python-cli directory**:
    ```bash
    cd python-cli
    ```

2.  **Install dependencies** into the project's virtual environment:
    ```bash
    # Make sure you are using the provided virtual environment
    & "c:/Users/gilad/OneDrive/Desktop/Orah AI project/.venv/Scripts/python.exe" -m pip install -r requirements.txt
    ```

3.  **Set up environment variables**:
    -   Rename the `.env.example` file to `.env`.
    -   Add your Google Gemini API key and optional GitHub token.

4.  **Run the script**:
    Execute the `main.py` script with a GitHub username as an argument.

    ```bash
    & "c:/Users/gilad/OneDrive/Desktop/Orah AI project/.venv/Scripts/python.exe" main.py <github_username>
    ```
    Example:
    ```bash
    & "c:/Users/gilad/OneDrive/Desktop/Orah AI project/.venv/Scripts/python.exe" main.py torvalds
    ```

## How AI Was Used in Development

-   **Scaffolding**: The AI assistant generated the initial project structure for both the Next.js app and the Python CLI, including package setup and directory creation.
-   **Boilerplate Code**: It wrote the initial boilerplate for API calls (GitHub, Gemini), command-line parsing, and the React frontend component structure.
-   **Error Debugging & Refinement**: When the initial text-based AI parsing proved brittle, the AI assistant suggested and implemented a more robust JSON-based prompting strategy to ensure reliable output.
-   **Documentation**: The AI assistant generated this README file, summarizing the project features and providing clear setup instructions for both tools.
