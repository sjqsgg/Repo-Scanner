# Connect to git repository
import os
import git
import requests
import json
import argparse
import time
from dotenv import load_dotenv

# Get last N commits and filter locally to get a smaller range
def analyze_local(repo, count_to_check):
    try:
        commits_for_file_generator = repo.iter_commits('HEAD', max_count=count_to_check)
        commits = list(commits_for_file_generator)
    except Exception as e:
        print(f"Get commits failed: {e}\n")

    tocheck = []

    try:
        for commit in commits:
            # id, author, email
            id = commit.hexsha
            authorName = commit.author.name
            authorEmail = commit.author.email
            message = commit.message.strip()
            if commit.parents:
                diffLs = commit.diff(commit.parents[0],create_patch=True)
                for diff in diffLs:
                    if diff.diff:
                        try:
                            diffTextLs = diff.diff.decode('utf-8').splitlines()
                            for diffText in diffTextLs:
                                if diffText.startswith("+") and not diffText.startswith('+++'):
                                    tocheck.append((id,diff.b_path,diffText[1:]))
                        except UnicodeDecodeError:
                            continue
    except Exception as e:
        print(f"Analyze locally failed: {e}\n")

    return tocheck

# Connect and analyze with LLM
def analyze_by_LLM (id, path, content):
    load_dotenv()
    api_key = os.getenv("api_key")
    model_name = "gemini-2.5-flash-preview-09-2025"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    system_prompt = """
    You are a professional product security engineer. You check every line of a commit code to see if it contains any sensitive data, and report it back in JSON file.    
    If it is sensitive, the JSON format MUST be:
    {
      "is_secret": true,
      "reason": "A brief rationale for your decision.",
      "data_type": "The type of secret found (e.g., 'API Key', 'Password', 'Private Key')."
    }
    
    If it is NOT sensitive, respond with:
    {
      "is_secret": false,
      "reason": "This appears to be a non-sensitive value (e.g., config, public ID).",
      "data_type": "Not a secret"
    }
    """

    user_prompt = f"""
    Please analyze this code,and send me a JSON file about its information. Please find JSON file format in system_prompt, you need to figure out its data type and sensitive reason.
    file_path: {path}
    commit_id: {id}
    code: {content}
    """

    payload = {
        "contents": [
            {"parts": [{"text": user_prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
        }
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=20
        )

        response.raise_for_status()
        result_json = response.json()
        answer_text = result_json['candidates'][0]['content']['parts'][0]['text']
        final_answer_dict = json.loads(answer_text)
        return final_answer_dict

    except requests.exceptions.RequestException as e:
        print(f"  [LLM Error] API request failed: {e}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        print(f"  [LLM Error] LLM response failed: {e}")
        print(f"  The original error log: {result_json}")
        return None

def main():
    # scan --repo <path|url> --n <commits> --out report.json
    parser = argparse.ArgumentParser(description="Scan sensitive data in git repository by LLM 使用 LLM 扫描 Git 仓库的秘密")
    parser.add_argument('--repo', type=str, required=True, help="Local git repository path to check")
    parser.add_argument('--n', type=int, default=10, help="Last n commits to scan")
    parser.add_argument('--out', type=str, default='report.json', help="JSON file name to output")
    args = parser.parse_args()

    # Open git repository
    try:
        repo = git.Repo(args.repo)
        print(f"Repository opened: {args.repo}")
    except Exception as e:
        print(f"Repository open failed: {e}")
        return

    # Locally scan at first
    tocheck_list = analyze_local(repo, args.n)
    if tocheck_list:
        print(f"{len(tocheck_list)} candidates to check after local scan, LLM running...")
    else:
        print("No sensitive data found locally.")

    # LLM scan
    final_findings = []
    for candidate in tocheck_list:
        commit_id, file_path, line_text = candidate
        if not line_text.strip(): continue
        llm_result = analyze_by_LLM(commit_id, file_path, line_text)

        if llm_result and llm_result.get("is_secret"):
            print(f"Sensitive data: {llm_result.get('data_type')}")

            report_entry = {
                "commit_hash": commit_id,
                "file_path": file_path,
                "line_snippet": line_text,
                "finding_type": llm_result.get("data_type"),
                "rationale": llm_result.get("reason")
            }
            final_findings.append(report_entry)
        elif llm_result:
            print(f": {llm_result.get('reason')}")
        else:
            print(f"LLM analyze failed: {file_path}")

    try:
        output_dir = os.path.dirname(args.out)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(final_findings, f, indent=2, ensure_ascii=False)
        print(f"Scan finished！{len(final_findings)} sensitive data found in {args.out}")

    except Exception as e:
        print(f"JSON export failed: {e}\n")

if __name__ == "__main__":
    main()

