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
            
            # Test 3 different yt-dlp permutations to pinpoint exact working datacenter flags
            configs = [
                ["--extractor-args", "youtube:player_client=android", "--user-agent", "com.google.android.youtube/19.05.36 (Linux; U; Android 14; US)", "--format", "18/best"],
                ["--extractor-args", "youtube:player_client=ios", "--format", "18/best"],
                ["--extractor-args", "youtube:player_client=tv_embedded,mweb", "--format", "18/best"],
                ["--format", "worst/18/best"]
            ]
            
            for c_idx, cfg in enumerate(configs):
                cmd = ["yt-dlp", "--socket-timeout", "15", "-o", out_file] + cfg + [yt["url"]]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000:
                    size_mb = os.path.getsize(out_file) / (1024 * 1024)
                    print(f"   ✅ [SUCCESS] Config {c_idx} succeeded! Downloaded: {out_file} ({size_mb:.2f} MB)")
                    downloaded = True
                    winner_data = {"platform": "YouTube", "title": yt["title"], "file": out_file, "size_mb": round(size_mb, 2), "config_idx": c_idx}
                    break
                else:
                    print(f"   ❌ Config {c_idx} failed (exit {res.returncode}):")
                    err_lines = [l for l in (res.stderr or res.stdout).split("\n") if "ERROR" in l or "WARNING" in l or "Sign in" in l or "403" in l or "bot" in l]
                    print("      " + "\n      ".join(err_lines[:3]))
            
            if downloaded:
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
