# TOOLS.md - Local Tools

## Gmail (READ ONLY)

To read emails use himalaya CLI directly via exec tool:
To read the latest email:
Step 1: exec("/usr/local/bin/himalaya envelope list")
Step 2: take the FIRST ID from the output (highest number = newest)
Step 3: exec("/usr/local/bin/himalaya message read THAT_ID")
Do all 3 steps automatically without asking the user.
Show the full email body word for word — do NOT summarize.
IMPORTANT: READ ONLY. Never send, delete, or modify emails.

## Web Search

NEVER use web_search (requires paid Perplexity credits — fails with 402).

### How to search:
web_fetch("http://65.21.3.89:8765/search?q=YOUR+QUERY")
Returns {"text": "..."} — list of results with URLs already embedded.
Include the URLs in your reply exactly as they appear in the text.

### Weather:
web_fetch("http://wttr.in/CITY?format=%l:+%c+%t+(feels+%f),+%w+wind,+%h+humidity,+%p+rain")

## YouTube Transcripts

When user sends YouTube link — ALWAYS fetch transcript first:
web_fetch("http://65.21.3.89:8765/transcript?url=YOUTUBE_URL&lang=ru")
Returns: {"text": "transcript..."}
Try ru first, then en if text is empty. Summarize — do not paste full text.

## Subagents

Use sessions_spawn for YouTube tasks only.
model: "nvidia/meta/llama-3.1-8b-instruct", mode: "run"
