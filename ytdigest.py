#!/usr/bin/env python3
import sys
import os
import re
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

CHANNELS_FILE = '/root/.openclaw/workspace-ytdigest/channels.txt'
PROCESSED_FILE = '/media/ytsummary/processed.txt'

BOT_TOKEN = '8449030330:AAH5XqTv69P2usSg4E7TG8FGKF7LCPQuqrQ'
CHAT_ID = '-1003823823665'
TOPIC_ID = 22

TRANSCRIPT_API = 'http://65.21.3.89:8765/transcript'
NVIDIA_API_KEY = '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'
NVIDIA_API_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
NVIDIA_MODEL = 'meta/llama-3.3-70b-instruct'

days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

processed = set()
try:
    with open(PROCESSED_FILE) as f:
        processed = set(line.strip() for line in f if line.strip())
except FileNotFoundError:
    pass

import xml.etree.ElementTree as ET

results = []

with open(CHANNELS_FILE) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|', 1)
        if len(parts) != 2:
            continue
        lang, url = parts
        m = re.search(r'/channel/([A-Za-z0-9_-]+)', url)
        if not m:
            continue
        channel_id = m.group(1)

        rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        try:
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()
        except Exception:
            continue

        try:
            root = ET.fromstring(data)
        except Exception:
            continue

        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }
        channel_name_el = root.find('atom:title', ns)
        channel_name = channel_name_el.text if channel_name_el is not None else url

        for entry in root.findall('atom:entry', ns):
            vid_el = entry.find('yt:videoId', ns)
            title_el = entry.find('atom:title', ns)
            pub_el = entry.find('atom:published', ns)
            if vid_el is None or title_el is None or pub_el is None:
                continue
            vid = vid_el.text
            title = title_el.text
            pub = pub_el.text[:10]
            if pub < cutoff:
                continue
            if vid in processed:
                continue
            results.append((pub, vid, title, channel_name, lang))

results.sort(key=lambda x: x[0], reverse=True)


def tg_post(endpoint, payload):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}'
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'TG error: {e}')
        return None


def get_transcript(video_url, lang='ru'):
    try:
        params = urllib.parse.urlencode({'url': video_url, 'lang': lang})
        req = urllib.request.Request(f'{TRANSCRIPT_API}?{params}')
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
            return data.get('text', ''), data.get('source', 'none')
    except Exception as e:
        print(f'Transcript API error: {e}')
        return '', 'none'


def get_summary(title, transcript, lang='ru'):
    if not transcript:
        return None

    lang_instruction = 'на русском языке' if lang == 'ru' else f'in {lang}'
    prompt = f"""Сделай краткое саммари видео "{title}" {lang_instruction}.

Транскрипт:
{transcript[:4000]}

Саммари (3-5 предложений, главные идеи):"""

    payload = json.dumps({
        'model': NVIDIA_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 300,
        'temperature': 0.3
    }).encode()

    req = urllib.request.Request(
        NVIDIA_API_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {NVIDIA_API_KEY}',
            'Content-Type': 'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'NVIDIA API error: {e}')
        return None


if not results:
    print('✅ Новых видео нет')
    sys.exit(0)

# Summary header message
tg_post('sendMessage', {
    'chat_id': CHAT_ID,
    'message_thread_id': TOPIC_ID,
    'text': f'📋 <b>Найдено новых видео: {len(results)}</b> (за {days} дн.)',
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
})

# Each video: photo card + summary
all_summaries = []

for pub, vid, title, channel, lang in results:
    thumb = f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
    video_url = f'https://youtu.be/{vid}'

    # Get transcript and summary
    transcript, source = get_transcript(video_url, lang)
    summary = get_summary(title, transcript, lang) if transcript else None

    if summary:
        all_summaries.append(f'• {title} ({channel}): {summary}')

    # Build caption
    caption = f'🎬 <b>{title}</b>\n📺 {channel}  📅 {pub}  🌐 {lang}\n🔗 {video_url}'
    if summary:
        caption += f'\n\n💡 {summary}'
    elif source == 'none':
        caption += '\n\n⚠️ Субтитры недоступны'

    tg_post('sendPhoto', {
        'chat_id': CHAT_ID,
        'message_thread_id': TOPIC_ID,
        'photo': thumb,
        'caption': caption,
        'parse_mode': 'HTML'
    })

    # Mark as processed
    try:
        os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
        with open(PROCESSED_FILE, 'a') as f:
            f.write(vid + '\n')
        processed.add(vid)
    except Exception as e:
        print(f'Could not write processed: {e}')

# Final digest
if all_summaries:
    digest_input = '\n'.join(all_summaries)
    prompt = f"""На основе этих саммари YouTube видео составь краткий дайджест дня (5-7 предложений).
Выдели главные тренды и самые важные темы. Пиши на русском языке.

{digest_input[:6000]}

Дайджест дня:"""

    payload = json.dumps({
        'model': NVIDIA_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.4
    }).encode()

    req = urllib.request.Request(
        NVIDIA_API_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {NVIDIA_API_KEY}',
            'Content-Type': 'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            digest = data['choices'][0]['message']['content'].strip()
        tg_post('sendMessage', {
            'chat_id': CHAT_ID,
            'message_thread_id': TOPIC_ID,
            'text': f'📰 <b>Дайджест дня ({len(results)} видео)</b>\n\n{digest}',
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        })
    except Exception as e:
        print(f'Digest error: {e}')

print(f'✅ Отправлено {len(results)} видео в Telegram')

# Write log
log_path = f'/var/log/ytdigest-{datetime.now().strftime("%Y-%m-%d")}.log'
with open(log_path, 'a') as lf:
    lf.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M UTC")} Отправлено {len(results)} видео в Telegram\n')
