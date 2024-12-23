from flask import Flask, render_template, request, send_file
import os
import re
from datetime import datetime
import io

app = Flask(__name__)

class LocalRepoScraper:
    def __init__(self, files, output_filename):
        self.files = files
        self.output_filename = output_filename

    def fetch_all_files(self):
        files_data = []
        for file_obj in self.files:
            relative_path = file_obj.filename
            file_content = f"\n'''--- {relative_path} ---\n"
            try:
                content_decoded = file_obj.read().decode('utf-8', errors='replace')
                file_content += content_decoded
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
                continue
            file_content += "\n'''"
            files_data.append(file_content)
            print(f"Processed file {relative_path}: size {len(file_obj.read())} bytes")
        return files_data

    def write_to_memory(self, files_data):
        output_buffer = io.StringIO()
        output_buffer.write(f"*Uploaded Files*\n")
        for file_data in files_data:
            output_buffer.write(file_data)
        output_buffer.seek(0)
        return output_buffer

    def clean_up_text(self, text_buffer):
        text = text_buffer.getvalue()
        cleaned_text = re.sub('\n{3,}', '\n\n', text)
        return cleaned_text.encode('utf-8')

    def run(self):
        print("Fetching all files...")
        files_data = self.fetch_all_files()

        print("Writing to memory...")
        output_buffer = self.write_to_memory(files_data)

        print("Cleaning up text...")
        cleaned_bytes = self.clean_up_text(output_buffer)

        return cleaned_bytes

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'repo_files' not in request.files:
            return "No files part"
        files = request.files.getlist('repo_files')
        output_filename = request.form.get('output_filename', 'combined_output')

        if not files or all(file.filename == '' for file in files):
            return "No selected file"

        scraper = LocalRepoScraper(files, output_filename)
        output_bytes = scraper.run()

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
