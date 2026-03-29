from fastapi import FastAPI
import subprocess, tempfile, os, re, urllib.request

app = FastAPI()

@app.get("/transcript")
def get_transcript(url: str, lang: str = "ru"):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "sub")

        def run_yt(lang_str):
            cmd = [
                "yt-dlp",
                "--cookies", "/root/.openclaw/youtube_cookies.txt",
                "--js-runtimes", "node",
                "--write-auto-sub",
                "--sub-lang", lang_str,
                "--skip-download", "--no-playlist", "--quiet",
                url, "-o", output_path,
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        run_yt(f"{lang},ru,en")
        vtt_files = [f for f in os.listdir(tmpdir) if f.endswith(".vtt")]
        if not vtt_files:
            run_yt("en,ru")
            vtt_files = [f for f in os.listdir(tmpdir) if f.endswith(".vtt")]

        if not vtt_files:
            return {"error": "No transcript found", "text": ""}

        content = open(os.path.join(tmpdir, vtt_files[0]), encoding="utf-8").read()
        lines = content.split("\n")
        out = []
        for line in lines:
            line = line.strip()
            if not line or "-->" in line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or re.match(r"^\d+$", line):
                continue
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and (not out or out[-1] != line):
                out.append(line)
        return {"text": " ".join(out)}


@app.get("/search")
def search_news(q: str, gl: str = "IE"):
    lang = "en-IE"
    encoded_q = q.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={gl}&ceid={gl}:en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            xml = r.read().decode("utf-8")
        items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
        results = []
        for item in items[:10]:
            title = re.search(r"<title>(.*?)</title>", item)
            link = re.search(r"<link>(.*?)</link>", item)
            pubdate = re.search(r"<pubDate>(.*?)</pubDate>", item)
            results.append({
                "title": title.group(1) if title else "",
                "link": link.group(1) if link else "",
                "date": pubdate.group(1) if pubdate else ""
            })
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}
