import os, re, shutil, tempfile, uuid
from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
from yt_dlp.utils import download_range_func

app = Flask(__name__, static_folder="static", static_url_path="")

MAX_CLIP_SECONDS = 10 * 60          # longest clip allowed
MAX_VIDEO_SECONDS = 24 * 60 * 60     # longest source video allowed
YT_RE = re.compile(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", re.I)


def valid_url(url):
    return isinstance(url, str) and YT_RE.match(url.strip())


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/api/info")
def info():
    url = (request.json or {}).get("url", "").strip()
    if not valid_url(url):
        return jsonify(error="Paste a valid YouTube link."), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True, "skip_download": True}) as ydl:
            d = ydl.extract_info(url, download=False)
    except Exception:
        return jsonify(error="Couldn't read that video. Check the link and try again."), 400
    if d.get("is_live"):
        return jsonify(error="Live streams can't be clipped."), 400
    duration = int(d.get("duration") or 0)
    if duration <= 0 or duration > MAX_VIDEO_SECONDS:
        return jsonify(error="This video is too long to clip here."), 400
    return jsonify(id=d["id"], title=d.get("title"), duration=duration,
                   thumbnail=d.get("thumbnail"))


@app.post("/api/clip")
def clip():
    body = request.json or {}
    url = str(body.get("url", "")).strip()
    try:
        start, end = float(body["start"]), float(body["end"])
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Start and end times are required."), 400
    if not valid_url(url):
        return jsonify(error="Paste a valid YouTube link."), 400
    if start < 0 or end <= start:
        return jsonify(error="End time must be after start time."), 400
    if end - start > MAX_CLIP_SECONDS:
        return jsonify(error=f"Clips can be at most {MAX_CLIP_SECONDS // 60} minutes."), 400

    workdir = tempfile.mkdtemp(prefix="clip_")
    out_tpl = os.path.join(workdir, f"{uuid.uuid4().hex}.%(ext)s")
    opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": out_tpl,
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,   # frame-accurate cuts (re-encodes the clip)
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        files = os.listdir(workdir)
        if not files:
            raise RuntimeError("no output")
        path = os.path.join(workdir, files[0])
    except Exception:
        shutil.rmtree(workdir, ignore_errors=True)
        return jsonify(error="Clipping failed. Try a shorter range or another video."), 500

    @after_this_request
    def cleanup(resp):
        shutil.rmtree(workdir, ignore_errors=True)
        return resp

    return send_file(path, as_attachment=True, download_name="clip.mp4", mimetype="video/mp4")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
