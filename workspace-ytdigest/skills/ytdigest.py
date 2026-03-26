import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

data = open('/tmp/rss.xml').read()
root = ET.fromstring(data)
ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
cutoff = (datetime.now() - timedelta(days=int(sys.argv[1]))).strftime('%Y-%m-%d')
for entry in root.findall('atom:entry', ns):
    pub = entry.find('atom:published', ns).text[:10]
    if pub >= cutoff:
        vid = entry.find('yt:videoId', ns).text
        title = entry.find('atom:title', ns).text
        channel = root.find('atom:title', ns).text
        print(f'{vid}|{title}|{channel}|{pub}')