# YouTube Transcript API

FastAPI server that extracts YouTube subtitles via yt-dlp.

## Install

```bash
pip3 install fastapi uvicorn --break-system-packages
cp main.py /opt/yt-api/
cp yt-transcript /usr/local/bin/yt-transcript && chmod +x /usr/local/bin/yt-transcript
cp yt-api.service /etc/systemd/system/
systemctl enable yt-api && systemctl start yt-api
```

## Usage

```
GET http://SERVER_IP:8765/transcript?url=YOUTUBE_URL&lang=ru
```

Response: `{"text": "transcript text..."}`

## Requirements

- yt-dlp (with --js-runtimes node support)
- node.js
- YouTube cookies at `/root/.openclaw/youtube_cookies.txt`
