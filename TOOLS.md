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

CRITICAL: ONE single-line command only. No pipes. No backslashes. No multiline.
NEVER write: exec("curl -")  — this is always wrong.
CORRECT: exec("curl -s 'http://65.21.3.89:8765/search?q=query+words+here'")

Examples:
exec("curl -s 'http://65.21.3.89:8765/search?q=events+in+Tralee+tomorrow'")
exec("curl -s 'http://65.21.3.89:8765/search?q=latest+AI+news'")
exec("curl -s 'http://65.21.3.89:8765/search?q=Killarney+news+this+week'")

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

## /jobs command

When user sends /jobs or /jobs <keyword>:
Run ALL 4 searches below (one exec per search), then format results.

IrishJobs developers:
exec("curl -s 'http://65.21.3.89:8765/search?q=software+developer+programmer+engineer+Kerry+site:irishjobs.ie/job/'")

IrishJobs support/devops/network:
exec("curl -s 'http://65.21.3.89:8765/search?q=IT+support+devops+network+engineer+sysadmin+Kerry+site:irishjobs.ie/job/'")

Indeed:
exec("curl -s 'http://65.21.3.89:8765/search?q=IT+developer+programmer+engineer+devops+support+Killarney+Kerry+site:ie.indeed.com'")

LinkedIn:
exec("curl -s 'http://65.21.3.89:8765/search?q=software+developer+engineer+devops+IT+support+Killarney+Kerry+site:linkedin.com/jobs'")

If keyword given (e.g. /jobs devops), add it to all queries.
FILTER: Only show IrishJobs URLs containing /job/ (not /jobs/ which are category pages).

Format output:
IT Jobs in Kerry - [date]

IrishJobs
- Title - Company -> URL

Indeed
- Title - snippet -> URL

LinkedIn
- Title - Company -> URL

Max 5 per source. No long descriptions. Remove obvious duplicates.

## /monitor command

When user sends /monitor:
Call: exec("openclaw agent --agent monitor --message '/monitor'")
Reply with the output as-is.
