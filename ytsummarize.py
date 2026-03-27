#!/usr/bin/env python3
"""
ytsummarize.py - fetch transcript of a YouTube video and print it to stdout
Usage: python3 ytsummarize.py <youtube_url> [lang]
"""
import sys
import re
import json
import urllib.request
import urllib.parse
import subprocess
import os
from datetime import datetime

YT_API = 'http://65.21.3.89:8765'
VAULT_DIR = '/root/obsidian-vault'
VAULT_SUBDIR = 'YouTube'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

def extract_video_id(url):
    m = re.search(r'(?:youtu\.be/|v=|/v/|embed/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None

def get_transcript(vid_id, lang='ru'):
    url = f'https://www.youtube.com/watch?v={vid_id}'
    enc = urllib.parse.quote(url, safe='')
    api_url = f'{YT_API}/transcript?url={enc}&lang={lang}'
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
            return data.get('text', ''), data.get('error', '')
    except Exception as e:
        return '', str(e)

def save_to_vault(vid_id, title, transcript, summary=None):
    date = datetime.now().strftime('%Y-%m-%d')
    safe_title = re.sub(r'[\/*?:"<>|]', '', title)[:60].strip()
    filename = f'{date} - {safe_title}.md'
    filepath = os.path.join(VAULT_DIR, VAULT_SUBDIR, filename)
    os.makedirs(os.path.join(VAULT_DIR, VAULT_SUBDIR), exist_ok=True)

    content = f"""---
date: {date}
url: https://youtu.be/{vid_id}
channel: {channel}
tags: [youtube]
---

# {title}

📺 {channel}  📅 {date}
🔗 https://youtu.be/{vid_id}

## Транскрипт

{transcript}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # git push
    env = os.environ.copy()
    subprocess.run(['git', '-C', VAULT_DIR, 'pull', '--rebase'], capture_output=True, env=env)
    subprocess.run(['git', '-C', VAULT_DIR, 'add', filepath], capture_output=True, env=env)
    subprocess.run(['git', '-C', VAULT_DIR, 'commit', '-m', f'Add: {safe_title}'], capture_output=True, env=env)
    result = subprocess.run(['git', '-C', VAULT_DIR, 'push'], capture_output=True, text=True, env=env)
    return filename, result.returncode == 0

if len(sys.argv) < 2:
    print('Usage: ytsummarize.py <youtube_url> [lang]')
    sys.exit(1)

video_url = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else 'ru'

vid_id = extract_video_id(video_url)
if not vid_id:
    print('ERROR: Не удалось распознать YouTube ссылку')
    sys.exit(1)

transcript, error = get_transcript(vid_id, lang)
if not transcript:
    transcript, error = get_transcript(vid_id, 'en')
if not transcript:
    print(f'ERROR: Транскрипт недоступен ({error})')
    sys.exit(1)

# Get title via oEmbed
try:
    oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json'
    req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        meta = json.loads(r.read())
        title = meta.get('title', f'YouTube {vid_id}')
        channel = meta.get('author_name', '')
except Exception:
    title = f'YouTube {vid_id}'
    channel = ''

filename, pushed = save_to_vault(vid_id, title, transcript)

print(f'VIDEO_ID:{vid_id}')
print(f'VIDEO_URL:https://youtu.be/{vid_id}')
print(f'TRANSCRIPT_LEN:{len(transcript)}')
print(f'VAULT_FILE:{filename}')
print(f'VAULT_PUSHED:{"yes" if pushed else "no"}')
print('---TRANSCRIPT---')
print(transcript)
