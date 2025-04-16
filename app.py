from flask import Flask, request, jsonify
from pytube import YouTube
import os
import tempfile
import api_video

app = Flask(__name__)
API_KEY = os.getenv("APIVIDEO_API_KEY")
client = api_video.AuthenticatedClient(api_key=API_KEY)

def download_youtube_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    stream.download(output_path=os.path.dirname(temp_file.name), filename=os.path.basename(temp_file.name))
    return temp_file.name

def upload_and_trim(video_path, start, end, title="Video"):
    video = client.videos.create(title=title)
    with open(video_path, "rb") as f:
        client.videos.upload(video_id=video.video_id, file=f)
    trimmed = client.video_clipping.create(video_id=video.video_id, trim_from=start, trim_to=end)
    return {
        "original": video.assets["player"],
        "trimmed": trimmed.assets["player"]
    }

@app.route("/clip", methods=["POST"])
def clip_video():
    try:
        data = request.get_json()
        main_url = data["mainUrl"]
        background_url = data.get("backgroundUrl")
        start = int(data["startSeconds"])
        end = int(data["endSeconds"])

        results = {}

        # Main video
        main_path = download_youtube_video(main_url)
        results["main"] = upload_and_trim(main_path, start, end, title="Main Video")
        os.remove(main_path)

        # Background video (if provided)
        if background_url:
            bg_path = download_youtube_video(background_url)
            results["background"] = upload_and_trim(bg_path, start, end, title="Background Video")
            os.remove(bg_path)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
