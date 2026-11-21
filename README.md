# ClipCutter

Paste a YouTube link, choose a start and end time, and download that part as an MP4.

- Works with long videos (5 to 6 hours or more)
- Drag the timeline or type exact times
- Only the section you pick is downloaded, so short clips from long videos are fast
- Runs on Windows, macOS and Linux

> **Use responsibly.** Downloading from YouTube can violate its Terms of Service. Only clip videos you own, that are Creative Commons licensed, or that you have permission to use.

## What you need

- Python 3.10 or newer
- ffmpeg
- About 4 GB RAM and 5 GB free disk space
- An internet connection

## Install

First, download the project:

```
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
```

No git? Click **Code → Download ZIP** on this page, unzip it, and open a terminal in that folder.

### Windows

1. Install Python from https://www.python.org/downloads (tick **Add python.exe to PATH**).
2. Install ffmpeg: `winget install Gyan.FFmpeg`, then close and reopen the terminal.
3. Run:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS

```
brew install python ffmpeg
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Linux (Ubuntu / Debian)

```
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Docker (any system)

If you have Docker, you don't need to install Python or ffmpeg:

```
docker build -t clipcutter .
docker run -p 8000:8000 clipcutter
```

Then open http://localhost:8000

## Use it

1. Open http://localhost:5000 in your browser.
2. Paste a YouTube link and click **Load video**.
3. Drag the yellow range, or type exact start and end times (`h:mm:ss`).
4. Click **Cut and download clip**.

Next time, you only need to activate the environment and start the app:

```
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
python app.py
```

## Use it from a phone or tablet

The app runs on a computer, and your phone opens it in the browser.

1. In `app.py`, change the last line to `app.run(host="0.0.0.0", port=5000)`.
2. Find your computer's IP address (`ipconfig` on Windows, `ip a` on Linux, `ifconfig` on macOS).
3. On your phone, connected to the same Wi-Fi, open `http://YOUR-IP:5000`.

To use it from anywhere, deploy it with Docker on a server (Render, Railway, Fly.io or a VPS). It needs a real server, so static hosting like GitHub Pages will not work.

## Settings

Change these at the top of `app.py`:

| Setting | Default | Meaning |
|---|---|---|
| `MAX_CLIP_SECONDS` | 60 minutes | Longest clip allowed |
| `MAX_VIDEO_SECONDS` | 24 hours | Longest source video allowed |

If you change the clip limit, also update the `600` check in `static/index.html`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found | Windows: reinstall Python with PATH ticked, or use `py`. Linux / macOS: use `python3`. |
| ffmpeg not found, or clip fails | Reopen the terminal after installing, then run `ffmpeg -version`. |
| Page shows "Not Found" | Make sure `index.html` is inside the `static` folder. |
| Downloads suddenly fail | Update yt-dlp: `pip install -U yt-dlp` |
| "Sign in to confirm you're not a bot" | Update yt-dlp, or try another video or network. |
| Port already in use | Change `port=5000` in `app.py`. |

## Project structure

```
app.py              Flask server (uses yt-dlp and ffmpeg)
requirements.txt    Python dependencies
Dockerfile          Container setup
static/index.html   Web page
```

## Built with

[Flask](https://flask.palletsprojects.com), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [ffmpeg](https://ffmpeg.org)

## Disclaimer

This project is for personal and educational use. You are responsible for following copyright law and the terms of any website you use it with. The author is not responsible for misuse.
