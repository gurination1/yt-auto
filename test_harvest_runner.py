import os
import sys
import json
import time
import subprocess
import requests
import re

def test_harvest_and_download():
    print("=" * 60)
    print("STARTING FAST GHA VIDEO HARVESTING & DOWNLOAD TEST")
    print("=" * 60)

    test_cases = [
        {"topic": "Gotthard Base Tunnel construction", "niche": "engineering"},
        {"topic": "deep sea anglerfish MBARI", "niche": "nature"},
        {"topic": "Roman legion battle tactics", "niche": "history"}
    ]

    os.makedirs("test_output", exist_ok=True)
    results_summary = []

    for tc in test_cases:
        topic = tc["topic"]
        niche = tc["niche"]
        print(f"\n--- Testing Topic: '{topic}' ({niche}) ---")
        
        # 1. Test Reddit RSS Extraction
        print(f"[Reddit RSS] Searching community footage for '{topic}'...")
        reddit_candidates = []
        try:
            subreddits = {
                "engineering": ["engineeringporn", "InfrastructurePorn", "interestingasfuck"],
                "nature": ["NatureIsFuckingLit", "marinebiology", "thalassophobia"],
                "history": ["ArtefactPorn", "WarCollege", "CombatFootage"]
            }.get(niche, ["interestingasfuck", "videos"])

            for sub in subreddits[:2]:
                url = f"https://www.reddit.com/r/{sub}/search.rss?q={requests.utils.quote(topic)}&restrict_sr=1&sort=relevance"
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
                if r.status_code == 200:
                    v_ids = re.findall(r'https?://v\.redd\.it/([a-zA-Z0-9]+)', r.text)
                    for vid in v_ids:
                        hls_url = f"https://v.redd.it/{vid}/HLSPlaylist.m3u8"
                        if hls_url not in reddit_candidates:
                            reddit_candidates.append(hls_url)
            print(f"[Reddit RSS] Found {len(reddit_candidates)} video stream candidates.")
        except Exception as e:
            print(f"[Reddit RSS] Search error: {e}")

        # 2. Test YouTube Extraction via yt-dlp
        print(f"[YouTube yt-dlp] Searching and extracting format info for '{topic}'...")
        yt_candidates = []
        try:
            cmd_search = [
                "yt-dlp",
                "--default-search", "ytsearch3",
                "--dump-json",
                "--no-playlist",
                "--socket-timeout", "10",
                "--extractor-args", "youtube:player_client=android_creator,android",
                "--user-agent", "com.google.android.youtube/19.05.36 (Linux; U; Android 14; US)",
                f"ytsearch3:{topic} authentic footage"
            ]
            res = subprocess.run(cmd_search, capture_output=True, text=True, timeout=25)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    try:
                        data = json.loads(line)
                        yt_candidates.append({
                            "title": data.get("title"),
                            "url": data.get("webpage_url") or f"https://www.youtube.com/watch?v={data.get('id')}",
                            "id": data.get("id"),
                            "duration": data.get("duration")
                        })
                    except Exception:
                        pass
            print(f"[YouTube yt-dlp] Found {len(yt_candidates)} YouTube candidates.")
        except Exception as e:
            print(f"[YouTube yt-dlp] Search error: {e}")

        # 3. Test Download & Slicing of Candidates
        download_success = False
        winner_info = {}

        # Try Reddit stream download first
        for idx, r_url in enumerate(reddit_candidates[:2]):
            out_file = f"test_output/reddit_{niche}_{idx}.mp4"
            print(f"[Download Test] Trying Reddit stream: {r_url}")
            cmd = [
                "ffmpeg", "-y",
                "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n",
                "-i", r_url,
                "-t", "5",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac",
                out_file
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if os.path.exists(out_file) and os.path.getsize(out_file) > 50_000:
                size_kb = os.path.getsize(out_file) // 1024
                print(f"[SUCCESS] Downloaded Reddit clip: {out_file} ({size_kb} KB)")
                download_success = True
                winner_info = {"platform": "Reddit", "url": r_url, "file": out_file, "size_kb": size_kb}
                break

        # If Reddit didn't succeed, try YouTube yt-dlp download
        if not download_success:
            for idx, yt_item in enumerate(yt_candidates[:2]):
                v_url = yt_item["url"]
                out_file = f"test_output/youtube_{niche}_{idx}.mp4"
                print(f"[Download Test] Trying YouTube video: {yt_item['title']} ({v_url})")
                
                # Test multiple client extractor options
                clients = ["android_creator,android", "tv_embedded,ios,mweb", "mweb"]
                for cl in clients:
                    temp_full = f"test_output/temp_yt_{niche}_{idx}.mp4"
                    cmd_yt = [
                        "yt-dlp",
                        "--extractor-args", f"youtube:player_client={cl}",
                        "--user-agent", "com.google.android.youtube/19.05.36 (Linux; U; Android 14; US)",
                        "--format", "18/22/136/137/best[ext=mp4]/best",
                        "--no-playlist",
                        "--socket-timeout", "15",
                        "-o", temp_full,
                        v_url
                    ]
                    print(f"   Executing yt-dlp with player_client={cl}...")
                    subprocess.run(cmd_yt, capture_output=True, text=True, timeout=30)
                    
                    if os.path.exists(temp_full) and os.path.getsize(temp_full) > 50_000:
                        # Slice 5s with FFmpeg
                        cmd_slice = [
                            "ffmpeg", "-y", "-ss", "00:00:05", "-i", temp_full,
                            "-t", "5", "-c:v", "libx264", "-preset", "ultrafast", "-an", out_file
                        ]
                        subprocess.run(cmd_slice, capture_output=True, text=True, timeout=15)
                        try: os.remove(temp_full)
                        except Exception: pass
                        
                        if os.path.exists(out_file) and os.path.getsize(out_file) > 50_000:
                            size_kb = os.path.getsize(out_file) // 1024
                            print(f"[SUCCESS] Downloaded & sliced YouTube clip ({cl}): {out_file} ({size_kb} KB)")
                            download_success = True
                            winner_info = {"platform": "YouTube", "title": yt_item["title"], "url": v_url, "file": out_file, "size_kb": size_kb}
                            break
                if download_success:
                    break

        results_summary.append({
            "topic": topic,
            "niche": niche,
            "success": download_success,
            "details": winner_info
        })

    print("\n" + "=" * 60)
    print("FINAL HARVESTING TEST SUMMARY")
    print("=" * 60)
    print(json.dumps(results_summary, indent=2))

    with open("test_output/test_summary.json", "w") as f:
        json.dump(results_summary, f, indent=2)

if __name__ == "__main__":
    test_harvest_and_download()
