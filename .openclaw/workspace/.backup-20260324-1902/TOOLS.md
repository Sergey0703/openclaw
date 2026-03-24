# TOOLS.md - Local Tools

## Web Search

NEVER use web_search (requires paid Perplexity credits — fails with 402).

For any search query — delegate to subagent:
model: "nvidia/meta/llama-3.1-8b-instruct", mode: "run"

Task template:
"Fetch http://65.21.3.89:8765/search?q=QUERY (URL-encode the query). Return the full 'text' field from the response exactly as-is, word for word. Do not summarize or reformat."

### Weather:
web_fetch("http://wttr.in/CITY?format=%l:+%c+%t+(feels+%f),+%w+wind,+%h+humidity,+%p+rain")

## Gmail (READ ONLY)

For any email request — delegate to subagent:
model: "nvidia/meta/llama-3.1-8b-instruct", mode: "run"

Task templates:
- Latest email: "Fetch http://65.21.3.89:8765/email?action=latest — return the full 'text' field exactly as-is, word for word. Do not summarize."
- List emails: "Fetch http://65.21.3.89:8765/email?action=list — return the full 'text' field exactly as-is."
- Read by ID: "Fetch http://65.21.3.89:8765/email?action=read&id=ID — return the full 'text' field exactly as-is, word for word. Do not summarize."

IMPORTANT: READ ONLY. Never send, delete, or modify emails.

## YouTube Transcripts

For YouTube links — delegate to subagent:
model: "nvidia/meta/llama-3.1-8b-instruct", mode: "run"

Task: "Fetch http://65.21.3.89:8765/transcript?url=YOUTUBE_URL&lang=ru — if text empty retry lang=en. Return a 3-5 sentence summary in Russian."

## Subagent rules

sessions_spawn is NON-BLOCKING — wait for the result before responding to user.
Do NOT answer until the subagent result arrives as an incoming message.
