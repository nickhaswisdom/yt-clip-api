from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip, CompositeVideoClip
from pytube import YouTube
import os
import tempfile
import uuid
import subprocess
import requests

app = Flask(__name__)

FFMPEG_PATH = "./bin/ffmpeg"  # bundled ffmpeg binary (you'll add this later)

def download_youtube_clip(url, start, end, filename):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    stream.download(filename=filename + ".mp4")
    return trim_video(filename + ".mp4", start, end, filename + "_trimmed.mp4")

def trim_video(input_path, start, end, output_path):
    subprocess.run([
        FFMPEG_PATH,
        "-ss", str(start),
        "-to", str(end),
        "-i", input_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        output_path
    ])
    return output_path

def upload_to_tmpfiles(filepath):
    with open(filepath, "rb") as f:
        response = requests.post("https://file.io", files={"file": f})
        return response.json()["link"]

@app.route('/combine', methods=['POST'])
def combine():
    data = request.json
    main_url = data.get("mainUrl")
    bg_url = data.get("backgroundUrl")
    start = data.get("startSeconds")
    end = data.get("endSeconds")

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        uid = str(uuid.uuid4())[:8]

        main_clip_path = download_youtube_clip(main_url, start, end, f"main_{uid}")
        bg_clip_path = download_youtube_clip(bg_url, start, end, f"bg_{uid}")

        # Optional: overlay or do more editing here if needed
        # For now, just return the trimmed clip URLs

        main_link = upload_to_tmpfiles(main_clip_path)
        bg_link = upload_to_tmpfiles(bg_clip_path)

        return jsonify({
            "mainClip": main_link,
            "backgroundClip": bg_link
        })

@app.route('/', methods=['GET'])
def home():
    return "YT Clip API is alive!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
