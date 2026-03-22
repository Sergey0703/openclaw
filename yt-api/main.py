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
        lines.append(f'- {title} ({url}): {snippet}')

    return {'text': '\n'.join(lines) if lines else 'No results found.'}
