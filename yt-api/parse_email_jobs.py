#!/usr/bin/env python3
"""
Parse job alert emails from Gmail via himalaya and save new jobs to jobs.db.
Sources: IrishJobs, Indeed, Glassdoor, LinkedIn
Run daily via cron.
"""
import subprocess, re, sqlite3, urllib.request, urllib.parse, sys
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

JOBS_DB = '/opt/yt-api/jobs.db'
HIMALAYA = '/usr/local/bin/himalaya'

def db():
    conn = sqlite3.connect(JOBS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def job_save(job_id, source, title, company, url):
    """Returns True if new, False if already known."""
    with db() as conn:
        if conn.execute('SELECT id FROM jobs WHERE id=?', (job_id,)).fetchone():
            return False
        conn.execute(
            'INSERT INTO jobs (id, source, title, company, url, date_found, status) VALUES (?,?,?,?,?,?,?)',
            (job_id, source, title, company, url, datetime.utcnow().strftime('%Y-%m-%d'), 'new')
        )
        return True

def follow_redirect(url, timeout=10):
    """Follow HTTP redirect and return final URL."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.url
    except Exception:
        return url

def get_email_ids(days_back=1):
    """Get list of email IDs from inbox for the last N days."""
    result = subprocess.run([HIMALAYA, 'envelope', 'list', '--page-size', '200'],
                            capture_output=True, text=True)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_back)
    ids = []
    for line in result.stdout.splitlines():
        m = re.match(r'\|\s*(\d+)\s*\|', line)
        if not m:
            continue
        email_id = m.group(1)
        # Parse date from line — format: 2026-03-29 22:15+00:00
        dm = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}[+-]\d{2}:\d{2})', line)
        if dm:
            try:
                email_dt = datetime.fromisoformat(dm.group(1).replace(' ', 'T'))
                if email_dt < cutoff:
                    continue
            except Exception:
                pass
        ids.append(email_id)
    return ids

def read_email(email_id):
    """Read email body without marking as read (--preview)."""
    result = subprocess.run([HIMALAYA, 'message', 'read', '--preview', email_id],
                            capture_output=True, text=True)
    return result.stdout

def parse_irishjobs(body):
    """Extract IrishJobs job links — follow click.irishjobs.ie redirects in parallel."""
    # Collect raw URLs first
    raw_urls = list(dict.fromkeys(
        u for u in re.findall(r'https://click\.irishjobs\.ie/f/a/[^\s\)>]+', body)
        if 'Report' not in u and 'Unsubscribe' not in u
    ))

    def resolve(raw_url):
        final_url = follow_redirect(raw_url)
        if '/job/' not in final_url:
            return None
        m = re.search(r'-job(\d+)', final_url)
        if not m:
            return None
        job_id = m.group(1)
        idx = body.find(raw_url)
        before = body[max(0, idx-300):idx].strip().splitlines()
        title = ''
        for line in reversed(before):
            line = line.strip()
            if line and len(line) > 5 and not line.startswith('http'):
                title = line
                break
        return {'id': job_id, 'source': 'irishjobs', 'title': title or 'IrishJobs job', 'company': '', 'url': final_url}

    jobs = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(resolve, u): u for u in raw_urls}
        for f in as_completed(futures):
            result = f.result()
            if result:
                jobs.append(result)
    return jobs

def parse_indeed(body):
    """Extract Indeed viewjob links — follow cts.indeed.com redirects."""
    jobs = []
    raw_urls = re.findall(r'https://cts\.indeed\.com/v3/[^\s\)>]+', body)
    seen = set()
    for raw_url in raw_urls:
        if 'Unsubscribe' in raw_url:
            continue
        if raw_url in seen:
            continue
        seen.add(raw_url)
        final_url = follow_redirect(raw_url)
        m = re.search(r'jk=([a-f0-9]+)', final_url)
        if not m:
            continue
        job_id = m.group(1)
        # Extract title from subject or body
        idx = body.find(raw_url)
        before = body[max(0, idx-400):idx].strip().splitlines()
        title = ''
        for line in reversed(before):
            line = line.strip()
            if line and len(line) > 5 and not line.startswith('http'):
                title = line
                break
        jobs.append({'id': job_id, 'source': 'indeed', 'title': title or 'Indeed job', 'company': '', 'url': 'https://ie.indeed.com/viewjob?jk=' + job_id})
    return jobs

def parse_glassdoor(body):
    """Extract Glassdoor jobs.
    Email structure per job:
      COMPANY X.X ★\n\nJOB TITLE\n\nLOCATION\n\n[SALARY]\n\n[easy apply]\n\nNd (URL...jobListingId=ID...)
    So title is 2 lines after ★ line, company is on the ★ line itself.
    """
    jobs = []
    # Find each jobListingId
    matches = list(re.finditer(r'jobListingId=(\d+)', body))
    seen = set()
    for m in matches:
        job_id = m.group(1)
        if job_id in seen:
            continue
        seen.add(job_id)
        idx = m.start()
        # Look back up to 1200 chars
        block = body[max(0, idx-1200):idx]
        lines = [l.strip() for l in block.splitlines()]
        # Find last ★ line — that's "company X.X ★"
        star_idx = None
        for i in range(len(lines)-1, -1, -1):
            if '★' in lines[i]:
                star_idx = i
                break
        if star_idx is not None:
            # Company is on the ★ line — format: "...URL) company X.X ★"
            star_line = lines[star_idx]
            # Extract just the company part before the rating
            company_m = re.search(r'\)\s+([a-zA-Z][^★\d]{2,40})\s+\d+\.\d+\s*★', star_line)
            if company_m:
                company = company_m.group(1).strip()
            else:
                # Fallback: strip rating and URL garbage
                company = re.sub(r'https?://\S+', '', star_line)
                company = re.sub(r'\s*\d+\.\d+\s*★.*', '', company).strip()
                company = re.sub(r'[^a-zA-Z\s\-\.]', ' ', company).strip()
                company = ' '.join(company.split())  # normalize spaces
            # Title: first non-empty, non-noise line after ★
            title = ''
            for line in lines[star_idx+1:]:
                line = line.strip()
                if not line:
                    continue
                # Skip location/salary/apply noise or URL garbage
                if re.search(r'€|\$|easy apply|apply now|employer est|^\d+[dh]|^http|kerry|killarney|tralee|ireland|remote|hybrid', line, re.IGNORECASE):
                    continue
                # Skip lines that look like URL fragments
                if re.search(r'utm_|rdforyou|jobListingId|glassdoor\.ie|[a-zA-Z0-9]{40,}', line):
                    continue
                if len(line) > 5 and len(line) < 120:
                    title = line
                    break
        else:
            # Fallback: last meaningful line before URL
            clean = [l.strip() for l in lines if l.strip() and not l.strip().startswith('http') and len(l.strip()) > 5]
            noise = re.compile(r'€|\$|easy apply|^\d+[dh]|kerry|killarney|tralee|ireland|★', re.IGNORECASE)
            clean = [l for l in clean if not noise.search(l)]
            title = clean[-1] if clean else 'Glassdoor job'
            company = clean[-2] if len(clean) >= 2 else ''
        url = 'https://www.glassdoor.ie/job-listing/job?jobListingId=' + job_id
        jobs.append({'id': job_id, 'source': 'glassdoor', 'title': title or 'Glassdoor job', 'company': company, 'url': url})
    return jobs

def parse_linkedin(body):
    """Extract LinkedIn job IDs from comm/jobs/view/ links."""
    jobs = []
    matches = list(re.finditer(r'linkedin\.com/comm/jobs/view/(\d+)', body))
    seen = set()
    # Also try to find subject for context
    subj_m = re.search(r'^Subject:\s*(.+)', body, re.MULTILINE)
    subject = subj_m.group(1).strip() if subj_m else ''
    for m in matches:
        job_id = m.group(1)
        if job_id in seen:
            continue
        seen.add(job_id)
        idx = m.start()
        before = body[max(0, idx-600):idx]
        lines = [l.strip() for l in before.splitlines() if l.strip()]
        # Filter location, generic phrases, and URL garbage
        noise = re.compile(
            r'^view job|^jobs similar|^http|^\d+$|^new jobs|^apply now|'
            r'^ireland$|^european union$|^united kingdom$|^remote$|^hybrid$|^subject:|'
            r'^apply with|^see all|^promoted$|^actively recruiting|^be an early|'
            r'^this company is|^high skills|^high experience|^be first|^early applicant|'
            r'^to:|^from:|^date:|^message-id:|'
            r'county kerry|killarney|tralee|dublin|cork|galway|county clare|county |'
            r'@gmail\.com|@yahoo|@hotmail|'
            r'^\d+ applicant|linkedin\.com|crossing hurdles|professional consultants',
            re.IGNORECASE
        )
        clean_lines = [l for l in lines if not noise.search(l) and 5 < len(l) < 100]
        title = clean_lines[-1] if clean_lines else 'LinkedIn job'
        url = 'https://ie.linkedin.com/jobs/view/' + job_id
        jobs.append({'id': job_id, 'source': 'linkedin', 'title': title, 'company': '', 'url': url})
    return jobs

def is_job_email(from_addr, subject):
    """Check if email is a job alert."""
    from_lower = from_addr.lower()
    subject_lower = subject.lower()
    if 'irishjobs' in from_lower:
        return 'irishjobs'
    if 'indeed' in from_lower and any(w in subject_lower for w in ['job', 'hiring', 'apply', 'position']):
        return 'indeed'
    if 'glassdoor' in from_lower:
        return 'glassdoor'
    if 'linkedin' in from_lower and any(w in subject_lower for w in ['job', 'hiring', 'similar', 'opportunity', 'new job']):
        return 'linkedin'
    return None

def main():
    # days_back: how far back to look. Default 1 (today only). Pass 7 for initial scan.
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    print(f'[{now_str} UTC] Parsing job emails (last {days_back} day(s))...')

    # Ensure email_id column exists
    with db() as conn:
        try:
            conn.execute('ALTER TABLE jobs ADD COLUMN email_id TEXT')
        except Exception:
            pass

    email_ids = get_email_ids(days_back=days_back)
    print(f'Found {len(email_ids)} emails in last {days_back} day(s)')

    total_new = 0
    processed_emails = 0

    for email_id in email_ids:
        body = read_email(email_id)
        # Extract From and Subject
        from_m = re.search(r'^From:\s*(.+)', body, re.MULTILINE)
        subj_m = re.search(r'^Subject:\s*(.+)', body, re.MULTILINE)
        from_addr = from_m.group(1).strip() if from_m else ''
        subject = subj_m.group(1).strip() if subj_m else ''

        source_type = is_job_email(from_addr, subject)
        if not source_type:
            continue

        processed_emails += 1
        jobs = []
        if source_type == 'irishjobs':
            jobs = parse_irishjobs(body)
        elif source_type == 'indeed':
            jobs = parse_indeed(body)
        elif source_type == 'glassdoor':
            jobs = parse_glassdoor(body)
        elif source_type == 'linkedin':
            jobs = parse_linkedin(body)

        new_count = 0
        for job in jobs:
            if job_save(job['id'], job['source'], job['title'], job['company'], job['url']):
                new_count += 1
                print(f'  [NEW] [{job["source"]}] {job["title"]} -> {job["url"]}')

        if jobs:
            print(f'  Email {email_id} ({source_type}): {len(jobs)} jobs found, {new_count} new')
        total_new += new_count

    print(f'Done. Processed {processed_emails} job emails, {total_new} new jobs saved.')

    # Show DB stats
    with db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        by_source = conn.execute('SELECT source, COUNT(*) as n FROM jobs GROUP BY source').fetchall()
        print(f'DB total: {total} jobs')
        for row in by_source:
            print(f'  {row["source"]}: {row["n"]}')

if __name__ == '__main__':
    main()
