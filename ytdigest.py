#!/usr/bin/env python3
import sys
import re
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

CHANNELS_FILE = '/root/.openclaw/workspace-ytdigest/channels.txt'
PROCESSED_FILE = '/media/ytsummary/processed.txt'

BOT_TOKEN = '8449030330:AAH5XqTv69P2usSg4E7TG8FGKF7LCPQuqrQ'
CHAT_ID = '-1003823823665'
TOPIC_ID = 22

days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

processed = set()
try:
    with open(PROCESSED_FILE) as f:
        processed = set(line.strip() for line in f if line.strip())
except FileNotFoundError:
    pass

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

if not results:
    print('✅ Новых видео нет')
    sys.exit(0)

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

# Summary message
tg_post('sendMessage', {
    'chat_id': CHAT_ID,
    'message_thread_id': TOPIC_ID,
    'text': f'📋 <b>Найдено новых видео: {len(results)}</b> (за {days} дн.)',
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
})

# Each video as sendPhoto with caption
for pub, vid, title, channel, lang in results:
    thumb = f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
    caption = f'🎬 <b>{title}</b>\n📺 {channel}  📅 {pub}  🌐 {lang}\n🔗 https://youtu.be/{vid}'
    tg_post('sendPhoto', {
        'chat_id': CHAT_ID,
        'message_thread_id': TOPIC_ID,
        'photo': thumb,
        'caption': caption,
        'parse_mode': 'HTML'
    })

print(f'✅ Отправлено {len(results)} видео в Telegram')
