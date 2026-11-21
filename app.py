import os, re, shutil, subprocess, tempfile, uuid
from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
from yt_dlp.utils import download_range_func

app = Flask(__name__, static_folder="static", static_url_path="")

MAX_CLIP_SECONDS = 60 * 60          # longest clip allowed (60 min)
MAX_VIDEO_SECONDS = 24 * 60 * 60    # longest source video allowed (24 hours)
MAX_CROP_EDGE = 0.45                # max share of one edge you can trim
YT_RE = re.compile(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", re.I)


def valid_url(url):
    return isinstance(url, str) and YT_RE.match(url.strip())


def read_crop(raw):
    """Return (top, bottom, left, right) as fractions 0..MAX_CROP_EDGE."""
    raw = raw or {}
    vals = []
    for k in ("top", "bottom", "left", "right"):
        try:
            v = float(raw.get(k, 0))
        except (TypeError, ValueError):
            v = 0.0
        vals.append(min(max(v, 0.0), MAX_CROP_EDGE))
    t, b, l, r = vals
    if t + b > 0.9 or l + r > 0.9:
        raise ValueError("Frame is too small. Trim less from the edges.")
    return t, b, l, r


def crop_video(src, dst, t, b, l, r):
    """Crop with ffmpeg. Sizes are rounded to even numbers (required by H.264)."""
    vf = (
        f"crop=w='trunc(iw*(1-{l}-{r})/2)*2':h='trunc(ih*(1-{t}-{b})/2)*2':"
        f"x='trunc(iw*{l}/2)*2':y='trunc(ih*{t}/2)*2'"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "copy", "-movflags", "+faststart", dst]
    subprocess.run(cmd, check=True, timeout=60 * 60)


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
                   thumbnail=d.get("thumbnail"),
                   width=d.get("width"), height=d.get("height"))


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
    try:
        t, b, l, r = read_crop(body.get("crop"))
    except ValueError as e:
        return jsonify(error=str(e)), 400

    workdir = tempfile.mkdtemp(prefix="clip_")
    out_tpl = os.path.join(workdir, f"{uuid.uuid4().hex}.%(ext)s")
    opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": out_tpl,
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        files = os.listdir(workdir)
        if not files:
            raise RuntimeError("no output")
        path = os.path.join(workdir, files[0])

        if t or b or l or r:
            cropped = os.path.join(workdir, "cropped.mp4")
            crop_video(path, cropped, t, b, l, r)
            path = cropped
    except Exception:
        shutil.rmtree(workdir, ignore_errors=True)
        return jsonify(error="Clipping failed. Try a shorter range, a smaller frame trim, or another video."), 500

    @after_this_request
    def cleanup(resp):
        shutil.rmtree(workdir, ignore_errors=True)
        return resp

    return send_file(path, as_attachment=True, download_name="clip.mp4", mimetype="video/mp4")


if __name__ == "__main__":
    app.run(debug=True, port=5000)