from fastapi import FastAPI
import subprocess, tempfile, os, re, urllib.request, urllib.parse, json

app = FastAPI()

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
        run_yt(f'{lang},ru,en')
        vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]
        if not vtt_files:
            run_yt('en,ru')
            vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]
        if not vtt_files:
            return {'error': 'No transcript found', 'text': ''}
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
        return {'text': ' '.join(out)}

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
        body = e.read().decode('utf-8')
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
        out = re.sub(r"\[[0-9;]*m", "", r.stdout)
        # find first ID (first number in table)
        m = re.search(r"\|\s*(\d+)\s*\|", out)
        if not m:
            return {"text": "No emails found"}
        first_id = m.group(1)
        cmd = ["/usr/local/bin/himalaya", "message", "read", first_id]
    else:
        return {"text": "Error: use action=list, action=read&id=NUMBER, or action=latest"}

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    output = result.stdout or result.stderr
    output = re.sub(r"\[[0-9;]*m", "", output)
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
