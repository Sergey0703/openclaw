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

## YouTube Links

When user sends a YouTube link — delegate to ytsummarize subagent:
exec("openclaw agent --agent ytsummarize-v2 --message '/ytsummarize YOUTUBE_URL'")
Do NOT process YouTube links yourself.

## /ytdigest command

When user asks for YouTube digest — delegate to ytdigest subagent:
exec("openclaw agent --agent ytdigest --message '/ytdigest 1'")
