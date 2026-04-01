---
name: ytdigest
description: Search YouTube channels for new videos and send to Telegram
user_invocable: true
---
# ytdigest skill

When user sends /ytdigest or /ytdigest N:

1. Extract N from command (default: 1)
2. Run: exec("python3 /root/.openclaw/workspace-ytdigest/ytdigest.py N")
3. The script runs for several minutes. Keep polling until it finishes:
   - exec(process poll sessionId=<id> timeout=60000) — repeat until process exits
   - If still running after poll, poll again. Do NOT give up after one poll.
   - Maximum wait: 60 minutes total. If not done by then, kill the process and report timeout.
4. Once finished, reply with the final stdout line (like "Отправлено X видео в Telegram")

The script sends messages to Telegram itself. Your reply is just the status line from stdout.
