import os
import sys
import json
import time
import subprocess
import requests
import urllib.parse
import re

def search_wikimedia_commons_video(query: str) -> str | None:
    try:
        # Extract core 2-3 words
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', query).split() if len(w) > 2]
        clean_q = " ".join(words[:2]) if words else query
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srnamespace": "6",
                "srsearch": f"{clean_q} filetype:video",
                "format": "json",
                "srlimit": "3",
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=10,
        )
        if r.status_code == 200:
            results = r.json().get("query", {}).get("search", [])
            for res in results:
                title = res["title"]
                r_info = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url|mime",
                        "format": "json",
                    },
                    headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
                    timeout=10,
                )
                if r_info.status_code == 200:
                    pages = r_info.json().get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        info = pdata.get("imageinfo", [])
                        if info and "video" in info[0].get("mime", ""):
                            return info[0].get("url")
    except Exception as e:
        print(f"   [Wikimedia] Error: {e}")
    return None

def search_nasa_video(query: str) -> str | None:
    try:
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', query).split() if len(w) > 2]
        clean_q = " ".join(words[:2]) if words else query
        r = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": clean_q, "media_type": "video"},
            timeout=10
        )
        if r.status_code == 200:
            items = r.json().get("collection", {}).get("items", [])
            for item in items[:2]:
                href = item.get("href")
                if href:
                    r_col = requests.get(href, timeout=10)
                    if r_col.status_code == 200:
                        urls = r_col.json()
                        for u in urls:
                            if u.endswith("~orig.mp4") or u.endswith("~medium.mp4") or u.endswith(".mp4"):
                                return u
    except Exception as e:
        print(f"   [NASA] Error: {e}")
    return None

def search_dvids_video(query: str) -> str | None:
    try:
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', query).split() if len(w) > 2]
        clean_q = " ".join(words[:2]) if words else query
        r = requests.get(
            "https://www.dvidshub.net/rss/search",
            params={"q": clean_q, "filter[type]": "video"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=10,
        )
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items[:3]:
                link = item.findtext("link") or ""
                m = re.search(r'video/(\d+)', link)
                if m:
                    vid_id = m.group(1)
                    page_url = f"https://www.dvidshub.net/video/{vid_id}"
                    r_p = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                    if r_p.status_code == 200:
                        mp4s = re.findall(r'https?://[^\"]+\.mp4[^\"]*', r_p.text)
                        if mp4s:
                            return mp4s[0]
    except Exception as e:
        print(f"   [DVIDS] Error: {e}")
    return None

def search_archive_documentary_video(query: str) -> str | None:
    try:
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', query).split() if len(w) > 3]
        clean_q = " ".join(words[:2]) if words else query
        r = requests.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": f"({clean_q}) AND mediatype:movies AND (collection:prelinger OR collection:educationalfilms OR collection:nasa OR collection:usgs)",
                "fl[]": ["identifier", "title"],
                "sort[]": "downloads desc",
                "rows": 3,
                "output": "json"
            },
            headers={"User-Agent": "yt-auto/1.0"},
            timeout=10
        )
        if r.status_code == 200:
            docs = r.json().get("response", {}).get("docs", [])
            for doc in docs:
                ident = doc.get("identifier")
                if ident:
                    r_meta = requests.get(f"https://archive.org/metadata/{ident}", headers={"User-Agent": "yt-auto/1.0"}, timeout=8)
                    if r_meta.status_code == 200:
                        files = r_meta.json().get("files", [])
                        for f in files:
                            name = f.get("name", "")
                            if (name.endswith(".mp4") or name.endswith(".ogv")) and int(f.get("size") or 0) > 10_000:
                                return f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
    except Exception as e:
        print(f"   [Archive] Error: {e}")
    return None

def run_harvest_test():
    print("=" * 60)
    print("🚀 RUNNING OPEN MULTI-PLATFORM VIDEO DOWNLOAD TEST ON GHA")
    print("=" * 60)

    test_cases = [
        {"topic": "Tunnel construction Switzerland", "niche": "engineering"},
        {"topic": "Deep sea ocean fish", "niche": "nature"},
        {"topic": "Apollo spacecraft launch", "niche": "space"},
        {"topic": "Military warfare tactics", "niche": "military"}
    ]

    os.makedirs("test_output", exist_ok=True)
    results = []

    for tc in test_cases:
        topic = tc["topic"]
        niche = tc["niche"]
        print(f"\n▶ Testing Topic: '{topic}' ({niche})")
        downloaded = False
        winner_data = {}

        # Try sources in order of open reliability
        sources = [
            ("Wikimedia Commons Video", search_wikimedia_commons_video),
            ("NASA Video Archive", search_nasa_video),
            ("DVIDS Real Footage", search_dvids_video),
            ("Internet Archive Documentary", search_archive_documentary_video)
        ]

        for s_name, s_fn in sources:
            v_url = s_fn(topic)
            if v_url:
                print(f"   Found candidate from {s_name}: {v_url}")
                out_file = f"test_output/{niche}_{s_name.split()[0].lower()}.mp4"
                
                # Download and slice 5 seconds directly with FFmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n",
                    "-i", v_url,
                    "-t", "5",
                    "-c:v", "libx264", "-preset", "ultrafast",
                    "-an",
                    out_file
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 50_000:
                    size_kb = os.path.getsize(out_file) // 1024
                    frame_path = f"test_output/{niche}_frame.jpg"
                    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:02", "-i", out_file, "-vframes", "1", frame_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"   ✅ [SUCCESS] Downloaded & sliced 5s authentic video from {s_name}: {out_file} ({size_kb} KB)")
                    downloaded = True
                    winner_data = {"platform": s_name, "url": v_url, "file": out_file, "size_kb": size_kb, "frame": frame_path}
                    break
                else:
                    print(f"   ❌ Failed downloading stream from {s_name}")

        results.append({
            "topic": topic,
            "niche": niche,
            "success": downloaded,
            "details": winner_data
        })

    print("\n" + "=" * 60)
    print("📊 OPEN MULTI-PLATFORM VIDEO DOWNLOAD REPORT")
    print("=" * 60)
    print(json.dumps(results, indent=2))

    with open("test_output/results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_harvest_test()
