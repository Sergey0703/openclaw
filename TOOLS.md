# TOOLS.md - Local Tools

## Gmail (READ ONLY)

Use himalaya CLI to read emails:
- List inbox: /usr/local/bin/himalaya envelope list
- Read email: /usr/local/bin/himalaya message read <ID>

IMPORTANT: READ ONLY. Never send, delete, or modify emails.

## Web Search

NEVER use web_search (requires paid Perplexity credits — fails with 402).
NEVER use web_fetch on google.com or news.google.com directly (returns 405).

### How to search:
web_fetch("http://65.21.3.89:8765/search?q=YOUR+QUERY")
Returns: {"results": [{"title": "...", "snippet": "...", "url": "..."}]}

For each result, present it as:
Title: snippet (source: url)

Example:
Events next week in Dublin: Swan Leisure Easter Camp, AS ONE FEST and more (source: https://eventbrite.com/...)

NEVER omit the source URL. It must appear after every item.

### Weather:
web_fetch("http://wttr.in/CITY?format=%l:+%c+%t+%f+%h+%w+%P+%p")

## YouTube Transcripts

When user sends YouTube link — ALWAYS fetch transcript first:
web_fetch("http://65.21.3.89:8765/transcript?url=YOUTUBE_URL&lang=ru")
Returns: {"text": "transcript..."}
Try ru first, then en if text is empty. Summarize — do not paste full text.

## Subagents

Use sessions_spawn tool for YouTube and email tasks (heavy text processing).
model: "nvidia/meta/llama-3.1-8b-instruct", mode: "run"

YouTube example task: "Fetch http://65.21.3.89:8765/transcript?url=URL&lang=ru — if text empty retry lang=en. Return a 3-5 sentence summary in Russian."

Email example task: "Run /usr/local/bin/himalaya envelope list and return 5 most recent subject + sender."
