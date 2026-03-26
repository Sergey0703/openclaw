---
name: ytdigest
description: Search YouTube channels for new videos and send to Telegram
user_invocable: true
---
# ytdigest skill

When user sends /ytdigest or /ytdigest N:

1. Extract N from command (default: 1)
2. Run: python3 /root/.openclaw/workspace-ytdigest/ytdigest.py N
3. Reply with the script's stdout output (one line like "✅ Отправлено X видео в Telegram")

The script sends messages to Telegram itself. Your reply is just the status line from stdout.
