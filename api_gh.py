import requests
import base64
import os

GITHUB_TOKEN = "********************"
REPO_NAME = "baderddine725/trend_Analyser_AI"
BRANCH = "main"
FOLDER_PATH = "***************"

# GitHub API URL
GITHUB_API = f"https://api.github.com/repos/{REPO_NAME}/contents/"

# Headers
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Upload files
for root, _, files in os.walk(FOLDER_PATH):
    for file in files:
        file_path = os.path.join(root, file)
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        # File relative path
        relative_path = os.path.relpath(file_path, FOLDER_PATH).replace("\\", "/")

        # GitHub file upload URL
        file_url = GITHUB_API + relative_path

        # Payload
        data = {
            "message": f"Add {relative_path}",
            "content": content,
            "branch": BRANCH
        }

        # Upload the file
        response = requests.put(file_url, json=data, headers=headers)

        if response.status_code == 201:
            print(f"Uploaded {relative_path} successfully!")
        else:
            print(f"Failed to upload {relative_path}: {response.text}")
