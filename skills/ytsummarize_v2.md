---
name: ytsummarize_v2
description: Summarize YouTube video using only agent tools (no Python scripts)
user_invocable: true
---
# ytsummarize_v2 skill

When user sends /ytsummarize2 <url>:

1. Extract video ID from URL (part after v= or youtu.be/)

2. Fetch transcript:
   web_fetch("http://65.21.3.89:8765/transcript?url=https://www.youtube.com/watch?v=VIDEO_ID&lang=ru")
   If text is empty — try lang=en.

3. Get video title and channel:
   web_fetch("https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json")
   Extract "title" and "author_name" from JSON.

4. Write summary in Russian:

📌 Главная идея: (1-2 sentences)

🔑 Ключевые моменты:
• ...
• ...
• ...

💡 Вывод: (1 sentence)
🔗 https://youtu.be/VIDEO_ID

5. Reply to user with the summary above.
