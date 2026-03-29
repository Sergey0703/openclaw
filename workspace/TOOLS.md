# TOOLS.md - Local Tools

## Gmail (READ ONLY)

To read emails use himalaya CLI directly via exec tool:
Step 1: exec("/usr/local/bin/himalaya envelope list")
Step 2: take the FIRST ID from the output
Step 3: exec("/usr/local/bin/himalaya message read THAT_ID")
IMPORTANT: READ ONLY. Never send, delete, or modify emails.

## Web Search — STRICT RULES

web_fetch is DISABLED for search. Do NOT call web_fetch with any search engine URL.
The ONLY way to search is via exec:

exec("curl -s 'http://65.21.3.89:8765/search?q=YOUR+QUERY+HERE'")

Examples:
exec("curl -s 'http://65.21.3.89:8765/search?q=events+in+Tralee+tomorrow'")
exec("curl -s 'http://65.21.3.89:8765/search?q=latest+AI+news'")

For weather:
exec("curl -s 'http://wttr.in/CITY?format=%l:+%c+%t+(feels+%f),+%w+wind,+%h+humidity,+%p+rain'")



## YouTube Links

When user sends a YouTube link:
1. Call sessions_spawn(task="/ytsummarize URL", agentId="ytsummarize-v2", runTimeoutSeconds=180)
2. Call sessions_yield() to end your turn and wait for the result
DO NOT write anything else after sessions_yield.

## /ytdigest command

exec("openclaw agent --agent ytdigest --message '/ytdigest 1'")

## /checkapi command

When user message is exactly "/checkapi":
MUST call: exec("/usr/local/bin/check-status.sh")
DO NOT call openclaw status or any other command.
Reply with the exec output exactly as-is, no changes.
