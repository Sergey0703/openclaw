# yt-api

FastAPI service on port 8765.

## Endpoints
- GET /transcript?url=YOUTUBE_URL&lang=ru — YouTube transcript via yt-dlp
- GET /search?q=QUERY — Web search via Tavily API, returns text with URLs

## Deploy
- Server: 65.21.3.89
- Path: /opt/yt-api/
- Service: systemctl restart yt-api
- Env: /opt/yt-api/.env (TAVILY_API_KEY)
