# SKILL.md — /jobs

Search for IT jobs in Killarney/Kerry area across LinkedIn, IrishJobs, and Indeed.

## Trigger
User sends `/jobs` or `/jobs <keyword>` (e.g. `/jobs devops`, `/jobs support`)

## Instructions

When triggered, perform these searches using exec("curl -s '...'") — run all 4 searches:

### 1. IrishJobs — Developers & Programmers
exec("curl -s 'http://65.21.3.89:8765/search?q=software+developer+programmer+engineer+Kerry+site:irishjobs.ie'")

### 2. IrishJobs — Support, DevOps, Network
exec("curl -s 'http://65.21.3.89:8765/search?q=IT+support+devops+network+engineer+sysadmin+Kerry+site:irishjobs.ie'")

### 3. Indeed — All IT Kerry
exec("curl -s 'http://65.21.3.89:8765/search?q=IT+developer+programmer+engineer+devops+support+Killarney+Kerry+site:ie.indeed.com'")

### 4. LinkedIn — IT Kerry
exec("curl -s 'http://65.21.3.89:8765/search?q=software+developer+engineer+devops+IT+support+Killarney+Kerry+site:linkedin.com/jobs'")

If user provided a keyword (e.g. `/jobs devops`), add it to all queries.

## Output format

Format results as:

🔍 **IT Jobs in Kerry** — <date>

**📋 IrishJobs**
• [Job Title](url) — snippet
• ...

**📋 Indeed**
• [Job Title](url) — snippet
• ...

**💼 LinkedIn**
• [Job Title](url) — snippet
• ...

Remove duplicate jobs (same title + company appearing on multiple sites).
Show max 5 results per source.
Keep it concise — title, company if visible, link. No long descriptions.
