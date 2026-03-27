# TOOLS.md - YTDigest Agent

## Skills
- `/ytdigest` — search all channels for new videos (last 24h)

## Paths
- Channels list: `/root/.openclaw/workspace-ytdigest/channels.txt`
- Processed videos: `/media/ytsummary/processed.txt`
- Cookies: `/home/claudeclaw/.claude/skills/ytsummary/cookies.txt`
- Media dir: `/media/ytsummary/`

## Tools available
- `bash` — run shell commands (yt-dlp, etc.)
- Skills in `skills/` folder

## yt-dlp
- Always use `--cookies /home/claudeclaw/.claude/skills/ytsummary/cookies.txt`
- Always use `--js-runtimes node` if transcript download fails
