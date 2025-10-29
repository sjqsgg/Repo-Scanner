# LLM Git Secret Scanner

This is a Python tool that scans the last N commits of a local Git repository for secrets and other sensitive data. It works by analyzing the *added lines* in each commit's diff and using the Google Gemini API to determine if a line contains sensitive information.

## Features

* **Diff-based Scanning:** Analyzes `git diffs` to check only the lines of code that were recently added.
* **LLM-Powered Analysis:** Uses a powerful Language Model (Google's Gemini) to intelligently identify secrets, reducing false positives from simple regex or entropy checks.
* **Targeted Reporting:** Generates a clean JSON report detailing each finding, including the commit hash, file, code snippet, and the LLM's rationale.
* **Simple CLI:** Easy to run from the command line with configurable options.

## Setup

### 1. Prerequisites

* Python 3.10+
* Git installed on your system

### 2. Installation & Dependencies

1.  **Clone or Download:**
    Place the Python script (e.g., `scan.py`) in a directory.

2.  **Install Required Python Libraries:**
    This script relies on `GitPython`, `requests`, and `python-dotenv`. You can install them using pip:
    ```bash
    pip install GitPython requests python-dotenv
    ```

### 3. API Key Configuration

This tool requires a Google Gemini API key to function.

1.  **Get your API Key:**
    Generate an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

2.  **Create a `.env` file:**
    In the *same directory* as your Python script, create a file named `.env`. If you cloned Repo Scanner repository, then there is an .env you can modify in the folder.

3.  **Add your key to the file:**
    Open the `.env` file and add the following line, replacing `YOUR_API_KEY_HERE` with your actual key:
    ```
    api_key=YOUR_API_KEY_HERE
    ```

## 🖥️ How to run

Run the script from your terminal using the following command structure.

```bash
python <script_name.py> --repo <path_to_repo> --n <num_commits> --out <output_file.json>

