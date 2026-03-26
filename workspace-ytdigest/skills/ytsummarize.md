---
name: ytsummarize
description: Summarize a YouTube video and save to Obsidian
user_invocable: true
---
# ytsummarize skill

When user sends /ytsummarize <url> [lang]:

1. Extract URL (or from replied-to message). lang default: ru
2. Run: python3 /root/.openclaw/workspace-ytdigest/ytsummarize.py <url> [lang]
3. The script outputs metadata lines then "---TRANSCRIPT---" then transcript text
4. Summarize the transcript in Russian:

📌 **Главная идея**: (1-2 предложения)

🔑 **Ключевые моменты**:
• ...
• ...
• ...

💡 **Вывод**: (1 предложение)

5. Save summary to vault by running:
   python3 /root/.openclaw/workspace-ytdigest/vault_append.py <VAULT_FILE> "<summary text>"
   Where VAULT_FILE is the value from the script output line "VAULT_FILE:..."

6. Reply to user with the summary + "✅ Сохранено в Obsidian: <VAULT_FILE>"
