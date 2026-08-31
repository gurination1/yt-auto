import os
import sys
import json
import time
import subprocess
import requests
import re

INVIDIOUS_INSTANCES = [
    "https://invidious.flokinet.to",
    "https://inv.nadeko.net",
    "https://yt.artemislena.eu",
    "https://invidious.privacyredirect.com"
]

def search_youtube_invidious(query: str, max_results: int = 3) -> list[dict]:
    candidates = []
    for inst in INVIDIOUS_INSTANCES:
        try:
            url = f"{inst}/api/v1/search"
            r = requests.get(url, params={"q": query, "type": "video"}, timeout=6)
            if r.status_code == 200:
                items = r.json()
                for item in items:
                    if len(candidates) >= max_results:
                        break
                    vid_id = item.get("videoId")
                    if vid_id:
                        candidates.append({
                            "title": item.get("title", query),
                            "url": f"https://www.youtube.com/watch?v={vid_id}",
                            "id": vid_id,
                            "duration": item.get("lengthSeconds", 0)
                        })
                if candidates:
                    print(f"   [Invidious] Found {len(candidates)} YouTube candidates via {inst}")
                    break
        except Exception:
            continue
    return candidates

def search_reddit_rss(query: str, max_results: int = 3) -> list[str]:
    v_ids = []
    try:
        # Extract core 2-3 words for broad matching
        words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', query).split() if len(w) > 2 and w.lower() not in [
            "footage", "real", "authentic", "documentary", "4k", "1080p", "construction"
        ]]
        clean_q = " ".join(words[:3]) if words else query
        url = "https://www.reddit.com/search.rss"
        r = requests.get(url, params={"q": clean_q, "sort": "relevance"}, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=8)
        if r.status_code == 200:
            found = re.findall(r'https?://v\.redd\.it/([a-zA-Z0-9]+)', r.text)
            for vid in found:
                if vid not in v_ids:
                    v_ids.append(f"https://v.redd.it/{vid}")
                if len(v_ids) >= max_results:
                    break
            print(f"   [Reddit RSS] Found {len(v_ids)} Reddit video URLs for '{clean_q}'")
    except Exception as e:
        print(f"   [Reddit RSS] Error: {e}")
    return v_ids

def run_harvest_test():
    print("=" * 60)
    print("🚀 RUNNING LIVE GHA VIDEO HARVESTING & DOWNLOAD TEST")
    print("=" * 60)

    test_cases = [
        {"topic": "Gotthard Base Tunnel Switzerland", "niche": "engineering"},
        {"topic": "deep sea anglerfish bioluminescence", "niche": "nature"},
        {"topic": "Roman legion warfare tactics", "niche": "history"}
    ]

    os.makedirs("test_output", exist_ok=True)
    results = []

    for tc in test_cases:
        topic = tc["topic"]
        niche = tc["niche"]
        print(f"\n▶ Testing Topic: '{topic}' ({niche})")
        downloaded = False
        winner_data = {}

        # 1. Search YouTube via Invidious
        yt_candidates = search_youtube_invidious(topic, max_results=3)
        for idx, yt in enumerate(yt_candidates):
            out_file = f"test_output/yt_{niche}_{idx}.mp4"
            print(f"   Downloading YouTube clip: {yt['title']} ({yt['url']})...")
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=android",
                "--user-agent", "com.google.android.youtube/19.05.36 (Linux; U; Android 14; US)",
                "--format", "18/22/best[ext=mp4]/best",
                "--socket-timeout", "15",
                "-o", out_file,
                yt["url"]
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000:
                size_mb = os.path.getsize(out_file) / (1024 * 1024)
                # Extract frame verification
                frame_path = f"test_output/yt_{niche}_{idx}_frame.jpg"
                subprocess.run(["ffmpeg", "-y", "-ss", "00:00:05", "-i", out_file, "-vframes", "1", frame_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"   ✅ [SUCCESS] YouTube video downloaded: {out_file} ({size_mb:.2f} MB)")
                downloaded = True
                winner_data = {"platform": "YouTube", "title": yt["title"], "file": out_file, "size_mb": round(size_mb, 2), "frame": frame_path}
                break

        # 2. If YouTube not downloaded, test Reddit
        if not downloaded:
            red_urls = search_reddit_rss(topic, max_results=2)
            for idx, r_url in enumerate(red_urls):
                out_file = f"test_output/reddit_{niche}_{idx}.mp4"
                print(f"   Downloading Reddit clip: {r_url}...")
                cmd = ["yt-dlp", "--socket-timeout", "15", "-o", out_file, r_url]
                subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000:
                    size_mb = os.path.getsize(out_file) / (1024 * 1024)
                    frame_path = f"test_output/reddit_{niche}_{idx}_frame.jpg"
                    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:02", "-i", out_file, "-vframes", "1", frame_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"   ✅ [SUCCESS] Reddit video downloaded: {out_file} ({size_mb:.2f} MB)")
                    downloaded = True
                    winner_data = {"platform": "Reddit", "url": r_url, "file": out_file, "size_mb": round(size_mb, 2), "frame": frame_path}
                    break

        results.append({
            "topic": topic,
            "niche": niche,
            "success": downloaded,
            "details": winner_data
        })

    print("\n" + "=" * 60)
    print("📊 GHA VIDEO HARVESTING & DOWNLOAD TEST REPORT")
    print("=" * 60)
    print(json.dumps(results, indent=2))

    with open("test_output/results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_harvest_test()
