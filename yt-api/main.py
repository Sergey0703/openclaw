from fastapi import FastAPI
import subprocess, tempfile, os, re, urllib.request, urllib.parse, json
import sqlite3
from datetime import datetime

JOBS_DB = '/opt/yt-api/jobs.db'

def jobs_db():
    conn = sqlite3.connect(JOBS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def job_save(job_id, source, title, company, url, date_posted=''):
    """Save job if not exists. Returns True if new, False if already known."""
    with jobs_db() as conn:
        existing = conn.execute('SELECT id FROM jobs WHERE id=?', (job_id,)).fetchone()
        if existing:
            return False
        conn.execute(
            'INSERT INTO jobs (id, source, title, company, url, date_posted, date_found, status) VALUES (?,?,?,?,?,?,?,?)',
            (job_id, source, title, company, url, date_posted, datetime.utcnow().strftime('%Y-%m-%d'), 'new')
        )
        return True

def job_is_known(job_id):
    with jobs_db() as conn:
        return conn.execute('SELECT id FROM jobs WHERE id=?', (job_id,)).fetchone() is not None

app = FastAPI()

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '')

@app.get('/transcript')
def get_transcript(url: str, lang: str = 'ru'):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'sub')

        def run_yt(lang_str):
            cmd = ['yt-dlp', '--cookies', '/root/.openclaw/youtube_cookies.txt',
                   '--js-runtimes', 'node', '--write-auto-sub', '--sub-lang', lang_str,
                   '--skip-download', '--no-playlist', '--quiet', url, '-o', output_path]
            subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Try subtitles first
        run_yt(f'{lang},ru,en')
        vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]
        if not vtt_files:
            run_yt('en,ru')
            vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]

        if vtt_files:
            content = open(os.path.join(tmpdir, vtt_files[0]), encoding='utf-8').read()
            lines = content.split('\n')
            out = []
            for line in lines:
                line = line.strip()
                if not line or '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or re.match(r'^\d+$', line):
                    continue
                line = re.sub(r'<[^>]+>', '', line).strip()
                if line and (not out or out[-1] != line):
                    out.append(line)
            if out:
                return {'text': ' '.join(out), 'source': 'subtitles'}

        # Fallback 1: video description
        desc_result = subprocess.run(
            ['yt-dlp', '--cookies', '/root/.openclaw/youtube_cookies.txt',
             '--skip-download', '--print', 'description', '--no-playlist', '--quiet', url],
            capture_output=True, text=True, timeout=30
        )
        description = desc_result.stdout.strip()
        if description and len(description) > 100:
            return {'text': description[:3000], 'source': 'description'}

        # Fallback 2: Whisper via Groq
        if not GROQ_API_KEY:
            return {'error': 'No transcript found', 'text': '', 'source': 'none'}

        audio_path = os.path.join(tmpdir, 'audio.mp3')
        subprocess.run(
            ['yt-dlp', '--cookies', '/root/.openclaw/youtube_cookies.txt',
             '--js-runtimes', 'node', '-x', '--audio-format', 'mp3',
             '--audio-quality', '5', '--no-playlist', '--quiet',
             '--postprocessor-args', 'ffmpeg:-t 600',
             url, '-o', audio_path],
            capture_output=True, text=True, timeout=120
        )
        if not os.path.exists(audio_path):
            return {'error': 'No transcript found', 'text': '', 'source': 'none'}

        boundary = 'FormBoundary7MA4YWxkTrZu0gW'
        with open(audio_path, 'rb') as af:
            audio_data = af.read()

        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="audio.mp3"\r\n'
            f'Content-Type: audio/mpeg\r\n\r\n'
        ).encode() + audio_data + (
            f'\r\n--{boundary}\r\n'
            f'Content-Disposition: form-data; name="model"\r\n\r\n'
            f'whisper-large-v3-turbo\r\n'
            f'--{boundary}--\r\n'
        ).encode()

        req = urllib.request.Request(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            data=body,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read())
                return {'text': result.get('text', ''), 'source': 'whisper'}
        except Exception as e:
            return {'error': str(e), 'text': '', 'source': 'none'}


@app.get('/search')
def search_news(q: str):
    api_key = TAVILY_API_KEY
    payload = json.dumps({'api_key': api_key, 'query': q, 'max_results': 5}).encode('utf-8')
    req = urllib.request.Request(
        'https://api.tavily.com/search',
        data=payload,
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'text': f'Search error: {e.code}'}
    except Exception as e:
        return {'text': f'Search error: {str(e)}'}

    lines = []
    for item in data.get('results', []):
        title = item.get('title', '')
        url = item.get('url', '')
        snippet = item.get('content', '')[:200].strip()
        lines.append(f'- {title}: {snippet} → {url}')

    if not lines:
        return {'text': 'No results found.'}
    result = '\n'.join(lines)
    return {'text': result, 'instruction': 'Show each result with its URL (after →). Do not remove URLs.'}


@app.get('/email')
def email_action(action: str = 'list', id: str = ''):
    if action == 'list':
        cmd = ['/usr/local/bin/himalaya', 'envelope', 'list']
    elif action == 'read' and id:
        cmd = ['/usr/local/bin/himalaya', 'message', 'read', id]
    elif action == 'latest':
        r = subprocess.run(['/usr/local/bin/himalaya', 'envelope', 'list'], capture_output=True, text=True, timeout=30)
        out = re.sub(r"\[[0-9;]*m", "", r.stdout)
        m = re.search(r"\|\s*(\d+)\s*\|", out)
        if not m:
            return {"text": "No emails found"}
        first_id = m.group(1)
        cmd = ["/usr/local/bin/himalaya", "message", "read", first_id]
    else:
        return {"text": "Error: use action=list, action=read&id=NUMBER, or action=latest"}

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    output = result.stdout or result.stderr
    output = re.sub(r"\[[0-9;]*m", "", output)
    return {"text": output.strip()}


@app.get('/weather')
def get_weather(city: str):
    city_enc = urllib.parse.quote(city)
    req = urllib.request.Request(
        f'http://wttr.in/{city_enc}?format=j1',
        headers={'User-Agent': 'curl/7.68.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

    cur = data['current_condition'][0]
    tomorrow = data['weather'][1] if len(data['weather']) > 1 else data['weather'][0]

    hours = {}
    for h in tomorrow['hourly']:
        t = int(h['time']) // 100
        if t in [6, 9, 12, 15, 18]:
            hours[f'{t:02d}:00'] = {
                'desc': h['weatherDesc'][0]['value'],
                'temp_c': h['tempC'],
                'wind_kmh': h['windspeedKmph'],
                'rain_mm': h['precipMM'],
                'humidity': h['humidity']
            }

    return {
        'city': city,
        'now': {
            'desc': cur['weatherDesc'][0]['value'],
            'temp_c': cur['temp_C'],
            'feels_c': cur['FeelsLikeC'],
            'wind_kmh': cur['windspeedKmph'],
            'humidity': cur['humidity']
        },
        'tomorrow': {
            'min_c': tomorrow['mintempC'],
            'max_c': tomorrow['maxtempC'],
            'hours': hours
        }
    }


@app.get('/jobs')
def search_jobs(keyword: str = ''):
    import re as _re

    def tavily_search(query, max_results=8):
        payload = json.dumps({'api_key': TAVILY_API_KEY, 'query': query, 'max_results': max_results}).encode('utf-8')
        req = urllib.request.Request(
            'https://api.tavily.com/search',
            data=payload,
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode('utf-8')).get('results', [])
        except Exception:
            return []

    CF_PROXY = 'https://fetch-proxy.sergey070373.workers.dev/'

    def irishjobs_get_date(url):
        import re as _re2
        from datetime import datetime, timezone
        for attempt in range(3):
            try:
                req = urllib.request.Request(CF_PROXY + '?url=' + urllib.parse.quote(url, safe=''), headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    html = r.read().decode('utf-8', errors='ignore')
                m = _re2.search(r'"datePosted":"([^"]+)"', html)
                if m:
                    dt = datetime.fromisoformat(m.group(1).replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    age_days = (now - dt).days
                    return age_days
                return None
            except Exception:
                if attempt == 2:
                    return None
        return None

    def linkedin_is_open(job_id):
        try:
            req = urllib.request.Request(
                f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}',
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read().decode('utf-8', errors='ignore')
            return 'No longer' not in html and html.count('closed') < 3
        except Exception:
            return True

    kw = keyword.strip()

    # Default search groups when no keyword given
    if kw:
        ij_queries = [
            kw + ' County Kerry site:irishjobs.ie/job/',
            kw + ' Kerry site:irishjobs.ie/job/',
        ]
        indeed_queries = [
            kw + ' Killarney County Kerry indeed.com',
            kw + ' Tralee County Kerry indeed.com',
            kw + ' Kerry Ireland indeed.com',
        ]
        linkedin_queries = [kw + ' Killarney Kerry linkedin jobs', kw + ' site:linkedin.com/jobs/view Killarney Kerry']
    else:
        ij_queries = [
            'software developer engineer devops IT support technical support systems administrator County Kerry site:irishjobs.ie/job/',
            'AI machine learning website SEO ecommerce webmaster digital marketing tutor assessor County Kerry site:irishjobs.ie/job/',
        ]
        indeed_queries = [
            'software engineer IT developer devops support Killarney County Kerry indeed.com',
            'AI website SEO ecommerce webmaster digital marketing systems administrator Killarney Kerry indeed.com',
            'technical support tutor assessor digital marketing stock control Kerry Ireland indeed.com',
        ]
        linkedin_queries = ['software engineer IT developer devops support AI website SEO digital marketing Killarney Kerry linkedin jobs', 'site:linkedin.com/jobs/view Killarney Kerry IT software developer engineer']

    kw_encoded = kw.replace(' ', '+') if kw else 'software+developer+engineer'

    # IrishJobs — direct scraping via CF proxy (no Tavily)
    # Reason: Tavily returns stale/old listings with no dates, and mixes in jobs from other counties.
    # CF proxy fetches IrishJobs search pages directly, we get datePosted from JSON-LD on each job page.
    def fetch_cf(url):
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    CF_PROXY + '?url=' + urllib.parse.quote(url, safe=''),
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    return r.read().decode('utf-8', errors='ignore')
            except Exception:
                if attempt == 2:
                    raise
        return ''  

    if kw:
        ij_search_urls = [
            'https://www.irishjobs.ie/jobs/in-kerry?q=' + urllib.parse.quote(kw),
            'https://www.irishjobs.ie/jobs/it-software/in-kerry?q=' + urllib.parse.quote(kw),
        ]
    else:
        ij_search_urls = [
            'https://www.irishjobs.ie/jobs/it-software/in-kerry',
            'https://www.irishjobs.ie/jobs/in-kerry?q=digital+marketing+SEO+ecommerce+webmaster',
            'https://www.irishjobs.ie/jobs/in-kerry?q=IT+support+systems+administrator',
        ]

    ij_seen = set()
    ij_candidates = []
    for search_url in ij_search_urls:
        try:
            html = fetch_cf(search_url)
            links = list(dict.fromkeys(_re.findall(r'href="(/job/[^"?]+)"', html)))
            for path in links:
                full_url = 'https://www.irishjobs.ie' + path
                if full_url not in ij_seen:
                    ij_seen.add(full_url)
                    ij_candidates.append(full_url)
        except Exception:
            pass

    kerry_locs = ['kerry', 'killarney', 'tralee', 'listowel', 'kenmare', 'killorglin',
                  'caherciveen', 'dingle', 'castleisland', 'abbeyfeale', 'ballybunion',
                  'waterville', 'sneem', 'rathmore']
    it_keywords = ['software', 'developer', 'devops', 'it ', 'it-', 'tech support', 'helpdesk',
                   'digital', 'seo', 'ecommerce', 'webmaster', 'ai ', 'machine learning',
                   'data ', 'network', 'systems admin', 'system admin', 'cloud',
                   'cybersecurity', 'cyber security', 'database', 'full stack', 'fullstack',
                   'front end', 'back end', 'frontend', 'backend', 'linux', 'desktop support',
                   'infrastructure', 'python', 'java', 'web developer', 'web design',
                   'computer technician', 'it manager', 'it officer', 'it support',
                   'tutor', 'assessor', 'marketing']

    from datetime import datetime, timezone
    import re as _re3
    import threading

    def process_ij_url(url):
        # Single fetch — get date + location + title all at once
        try:
            html = fetch_cf(url)
            # Date
            m = _re3.search(r'"datePosted":"([^"]+)"', html)
            age_days = None
            if m:
                dt = datetime.fromisoformat(m.group(1).replace('Z', '+00:00'))
                age_days = (datetime.now(timezone.utc) - dt).days
            if age_days is not None and age_days > 60:
                return None
            # Location
            loc_m = _re3.search(r'"addressLocality":"([^"]+)"', html)
            if loc_m:
                locality = loc_m.group(1).lower()
                if not any(k in locality for k in kerry_locs):
                    return None
            # Title
            t = _re3.search(r'<title>([^<]+)</title>', html)
            title = t.group(1).strip().replace(' - IrishJobs.ie', '').replace(' | IrishJobs', '') if t else url
            # IT filter
            if not any(kw in title.lower() for kw in it_keywords):
                return None
            age_str = (' (' + str(age_days) + 'd ago)') if age_days is not None else ''
            return {'title': title + age_str, 'url': url, 'snippet': ''}
        except Exception:
            return None

    # Process candidates in parallel (max 8 threads)
    ij_results = []
    lock = threading.Lock()
    threads = []
    thread_results = [None] * len(ij_candidates)

    def worker(i, url):
        thread_results[i] = process_ij_url(url)

    for i, url in enumerate(ij_candidates[:20]):
        t = threading.Thread(target=worker, args=(i, url))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=25)

    for r in thread_results:
        if r is not None:
            ij_results.append(r)
        if len(ij_results) >= 5:
            break

    ij_results = ij_results[:5]

    # Indeed — via Exa MCP (mcporter), better than Tavily for Indeed
    import subprocess as _sp
    indeed_results = []
    indeed_seen = set()
    indeed_exa_queries = []
    if kw:
        indeed_exa_queries = [kw + ' jobs Killarney Kerry Ireland']
    else:
        indeed_exa_queries = [
            'IT software developer engineer jobs Killarney Kerry Ireland',
            'digital marketing IT support jobs Kerry Ireland',
        ]
    good_locs = ['kerry', 'killarney', 'tralee', 'munster', 'killorglin', 'county kerry']
    bad_locs = ['dublin,', 'cork,', 'limerick,', 'galway,', 'waterford,', 'belfast', 'kildare,']
    for eq in indeed_exa_queries:
        if len(indeed_results) >= 5:
            break
        try:
            exa_cmd = 'exa.web_search_advanced_exa(query: "' + eq + '", includeDomains: ["ie.indeed.com"], numResults: 8)'
            res = _sp.run(['/usr/bin/mcporter', 'call', exa_cmd], capture_output=True, text=True, timeout=20)
            if res.returncode != 0:
                print(f'[indeed] mcporter error: {res.stderr[:200]}')
            raw = res.stdout
            # Extract viewjob URLs
            import re as _re4
            urls = list(dict.fromkeys(_re4.findall(r'https://ie\.indeed\.com/viewjob\?jk=[a-f0-9]+', raw)))
            for url in urls:
                if url in indeed_seen:
                    continue
                indeed_seen.add(url)
                # Get title from Exa JSON field before URL
                idx = raw.find(url)
                before = raw[max(0, idx-300):idx] if idx > 0 else ''
                context = raw[max(0, idx-300):idx+300] if idx > 0 else ''
                tm = _re4.findall(r'"title":\s*"([^"]+)"', before)
                title = tm[-1].strip() if tm else 'Indeed job in Kerry'
                # Clean up Indeed category page titles used as job titles
                if 'Jobs in' in title and '|' in title:
                    title = 'Job in Kerry'
                # Check location only in title (context may contain other job locations)
                loc_text = title.lower()
                if not any(g in loc_text for g in good_locs):
                    continue
                if any(b in loc_text for b in bad_locs):
                    continue
                # Crawl the actual job page to get real title
                try:
                    crawl_cmd = 'exa.crawling_exa(urls: ["' + url + '"], maxCharacters: 300)'
                    cr = _sp.run(['/usr/bin/mcporter', 'call', crawl_cmd], capture_output=True, text=True, timeout=15)
                    ct = cr.stdout
                    # First heading is the job title
                    real_title_m = _re4.search(r'# (.{5,80})', ct)
                    if real_title_m:
                        title = real_title_m.group(1).strip()
                except Exception:
                    pass
                # IT keyword filter on final title
                it_kws = ['software', 'developer', 'devops', 'it ', 'helpdesk', 'digital', 'seo',
                          'ecommerce', 'webmaster', 'ai ', 'machine learning', 'data ', 'network',
                          'systems admin', 'cloud', 'cybersecurity', 'database', 'full stack',
                          'linux', 'web developer', 'computer', 'it manager', 'it officer',
                          'it support', 'tutor', 'assessor', 'marketing', 'engineer', 'technical support',
                          'systems administrator', 'programmer', 'analyst']
                if not any(k in title.lower() for k in it_kws):
                    continue
                indeed_results.append({'title': title, 'url': url, 'snippet': ''})
                if len(indeed_results) >= 5:
                    break
        except Exception:
            pass
    # Fallback to Tavily if Exa found nothing
    if not indeed_results:
        for q in indeed_queries:
            for r in tavily_search(q, 8):
                url = r.get('url', '')
                if '/viewjob?jk=' not in url:
                    continue
                title = r.get('title', '')
                snippet = r.get('content', '')
                loc_text = (title + ' ' + snippet[:300]).lower()
                if not any(g in loc_text for g in good_locs):
                    continue
                if any(b in loc_text for b in bad_locs):
                    continue
                if url not in [x['url'] for x in indeed_results]:
                    indeed_results.append({'title': title, 'url': url, 'snippet': snippet[:150]})
            if len(indeed_results) >= 5:
                break
    indeed_results = indeed_results[:5]

    # LinkedIn
    linkedin_results = []
    seen_linkedin = set()
    for linkedin_query in linkedin_queries:
     for r in tavily_search(linkedin_query, 8):
        url = r.get('url', '')
        if '/jobs/view/' not in url:
            continue
        title = r.get('title', '')
        snippet = r.get('content', '')
        loc_text = (title + ' ' + snippet[:300]).lower()
        bad_locs = ['dublin,', 'cork,', 'limerick,', 'galway,', 'waterford,', 'belfast', 'kildare,', 'leinster', 'connacht']
        good_locs = ['kerry', 'killarney', 'tralee', 'munster', 'killorglin', 'county kerry']
        if not any(g in loc_text for g in good_locs):
            continue
        if any(b in loc_text for b in bad_locs):
            continue
        age_m = _re.search(r'([0-9]+) month', snippet)
        if age_m and int(age_m.group(1)) > 3:
            continue
        id_m = _re.search(r'-([0-9]{9,})$', url)
        if id_m and not linkedin_is_open(id_m.group(1)):
            continue
        age_days = irishjobs_get_date(url)
        if age_days is not None and age_days > 60:
            continue
        if url not in seen_linkedin:
            seen_linkedin.add(url)
            age_str = (' (' + str(age_days) + 'd ago)') if age_days is not None else ''
            linkedin_results.append({'title': title + age_str, 'url': url, 'snippet': snippet[:150]})
    linkedin_results = linkedin_results[:5]

    # Save to DB and mark new vs known
    def save_and_mark(results, source):
        for item in results:
            url = item['url']
            import re as _re5
            if source == 'indeed':
                mm = _re5.search(r'jk=([a-f0-9]+)', url)
                job_id = mm.group(1) if mm else url
            elif source == 'linkedin':
                mm = _re5.search(r'/view/[^/]+-([0-9]+)', url)
                job_id = mm.group(1) if mm else url
            else:
                mm = _re5.search(r'-job([0-9]+)$', url)
                job_id = mm.group(1) if mm else url
            item['is_new'] = job_save(job_id, source, item['title'], '', url)

    save_and_mark(ij_results, 'irishjobs')
    save_and_mark(indeed_results, 'indeed')
    save_and_mark(linkedin_results, 'linkedin')

    def fmt(items, source):
        nl = '\n'
        if not items:
            return '**' + source + '**' + nl + 'No specific listings found.' + nl
        out = ['**' + source + '**']
        for i, item in enumerate(items, 1):
            new_tag = ' [NEW]' if item.get('is_new') else ''
            out.append(str(i) + '. ' + item['title'] + new_tag + ' -> ' + item['url'])
        return nl.join(out) + nl

    result = fmt(ij_results, 'IrishJobs (Kerry)') + '\n' + fmt(indeed_results, 'Indeed (Kerry)') + '\n' + fmt(linkedin_results, 'LinkedIn (Kerry)')
    return {'text': result, 'irishjobs': ij_results, 'indeed': indeed_results, 'linkedin': linkedin_results}
