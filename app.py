from flask import Flask, render_template, request, send_file
import os
import re
from datetime import datetime
import io
from github import Github

app = Flask(__name__)

# Replace with your GitHub personal access token if needed for private repos or higher rate limits
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

class LocalRepoScraper:
    def __init__(self):
        pass

    def fetch_repo_files(self, repo_url):
        try:
            g = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()
            repo_path = repo_url.replace("https://github.com/", "")
            repo = g.get_repo(repo_path)
            contents = repo.get_contents("")  # Get the root directory contents
            all_files = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    all_files.append(file_content)
            return all_files
        except Exception as e:
            print(f"Error fetching repository: {e}")
            return None

    def get_file_content(self, github_file):
        try:
            return github_file.decoded_content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Error decoding file {github_file.path}: {e}")
            return None

    def write_to_memory(self, files_data, repo_name):
        output_buffer = io.StringIO()
        output_buffer.write(f"*GitHub Repository: {repo_name}*\n")
        for filename, content in files_data.items():
            output_buffer.write(f"\n'''--- {filename} ---\n")
            output_buffer.write(content)
            output_buffer.write("\n'''\n")
        output_buffer.seek(0)
        return output_buffer

    def clean_up_text(self, text_buffer):
        text = text_buffer.getvalue()
        cleaned_text = re.sub('\n{3,}', '\n\n', text)
        return cleaned_text.encode('utf-8')

    def run(self, repo_url):
        print(f"Fetching files from: {repo_url}")
        files = self.fetch_repo_files(repo_url)
        if not files:
            return None

        repo_name = repo_url.split('/')[-1]
        files_data = {}
        for file_info in files:
            content = self.get_file_content(file_info)
            if content:
                files_data[file_info.path] = content

        print("Writing to memory...")
        output_buffer = self.write_to_memory(files_data, repo_name)

        print("Cleaning up text...")
        cleaned_bytes = self.clean_up_text(output_buffer)

        return cleaned_bytes

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        repo_url = request.form.get('repo_url')
        output_filename = request.form.get('output_filename', 'repo_text')

        if not repo_url:
            return "Please enter a GitHub repository URL."

        scraper = LocalRepoScraper()
        output_bytes = scraper.run(repo_url)

        if not output_bytes:
            return "Error processing the repository or invalid URL."

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        actual_filename = f"{output_filename}_{timestamp}.txt"

        return send_file(
            io.BytesIO(output_bytes),
            download_name=actual_filename,
            as_attachment=True
        )
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
