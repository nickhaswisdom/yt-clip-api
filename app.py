from flask import Flask, request, jsonify
from pytube import YouTube
import os
import tempfile
import api_video

app = Flask(__name__)
API_KEY = os.getenv("APIVIDEO_API_KEY")

client = api_video.AuthenticatedClient(api_key=API_KEY)

@app.route("/clip", methods=["POST"])
def clip_video():
    try:
        data = request.get_json()

        main_url = data["mainUrl"]
        start = int(data["startSeconds"])
        end = int(data["endSeconds"])

        # Download the main video from YouTube
        yt = YouTube(main_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            stream.download(output_path=os.path.dirname(tmp_file.name), filename=os.path.basename(tmp_file.name))
            video_path = tmp_file.name

        # Upload to api.video
        video = client.videos.create(title="Trimmed YouTube Clip")
        with open(video_path, "rb") as f:
            client.videos.upload(video_id=video.video_id, file=f)

        # Create a clip using the trimming feature
        trimmed = client.video_clipping.create(video_id=video.video_id, trim_from=start, trim_to=end)

        return jsonify({
            "original_video_url": video.assets["player"],
            "trimmed_video_url": trimmed.assets["player"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

