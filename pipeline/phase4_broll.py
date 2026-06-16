import os
import random
import requests
import urllib.parse
import subprocess
from pipeline.config import PEXELS_API_KEY, PIXABAY_API_KEY, COVERR_API_KEY, NASA_API_KEY


# ── Source 1: Pexels Candidates ──────────────────────────────────────────────

def _pexels_candidates(query: str, orientation: str, n: int = 8) -> list[dict]:
    if not PEXELS_API_KEY:
        return []
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": n, "orientation": orientation},
            timeout=30,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        candidates = []
        for video in videos:
            image_url = video.get("image")
            video_files = [f for f in video.get("video_files", []) if f.get("quality") in ("hd", "sd")]
            if image_url and video_files:
                video_files.sort(key=lambda f: f.get("width", 0), reverse=True)
                candidates.append({
                    "video_url": video_files[0]["link"],
                    "thumb_url": image_url
                })
        return candidates
    except Exception as e:
        print(f"[B-roll] Pexels search failed for '{query}': {e}")
        return []


# ── Source 2: Pixabay ────────────────────────────────────────────────────────

def _pixabay_video(query: str) -> str | None:
    if not PIXABAY_API_KEY:
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_API_KEY, "q": query, "per_page": 3},
            timeout=30,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        videos_data = hits[0].get("videos", {})
        for size in ["large", "medium", "small", "tiny"]:
            url = videos_data.get(size, {}).get("url")
            if url:
                return url
        return None
    except Exception as e:
        print(f"[B-roll] Pixabay failed for '{query}': {e}")
        return None


# ── Source 3: Coverr (cinematic, high quality) ───────────────────────────────

def _coverr_video(query: str) -> str | None:
    if not COVERR_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.coverr.co/videos",
            params={"keywords": query, "token": COVERR_API_KEY, "page": 1, "size": 5},
            timeout=30,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        item = random.choice(hits[:3])
        urls = item.get("urls", {}).get("mp4", {})
        return urls.get("hd") or urls.get("sd")
    except Exception as e:
        print(f"[B-roll] Coverr failed for '{query}': {e}")
        return None


# ── Source 4: NASA Image & Video Library (no key — public domain) ─────────────

def _nasa_image(query: str) -> str | None:
    """Fetches a real NASA image for science/space topics. Completely free, no key."""
    try:
        r = requests.get(
            "https://images-api.nasa.gov/search",
            params={
                "q": query,
                "media_type": "image",
                "page_size": 5,
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=20,
        )
        r.raise_for_status()
        items = r.json().get("collection", {}).get("items", [])
        if not items:
            return None
        item = random.choice(items[:3])
        links = item.get("links", [])
        for link in links:
            href = link.get("href", "")
            if href and href.startswith("http"):
                return href
        return None
    except Exception as e:
        print(f"[B-roll] NASA failed for '{query}': {e}")
        return None


# ── Source 5: Wikipedia article thumbnail ────────────────────────────────────

def _wikipedia_image(query: str) -> str | None:
    """
    Fetches the Wikipedia article image for the query topic.
    No API key required. Perfect for named people and well-known concepts.
    """
    try:
        title = urllib.parse.quote(query.replace(" ", "_"))
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        # Prefer full-size original, fall back to thumbnail
        img = data.get("originalimage", {}).get("source") \
           or data.get("thumbnail", {}).get("source")
        return img
    except Exception as e:
        print(f"[B-roll] Wikipedia failed for '{query}': {e}")
        return None


def _wikimedia_video(query: str) -> str | None:
    """Search Wikimedia Commons for CC-licensed educational videos and fetch actual URL. No API key needed."""
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srnamespace": "6",  # File namespace
                "srsearch": f"{query} filetype:video",
                "format": "json",
                "srlimit": "5",
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return None

        # Pick the top result and use Wikipedia API to get the correct URL
        title = results[0]["title"]
        r_info = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=15,
        )
        r_info.raise_for_status()
        pages = r_info.json().get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            imageinfo = page_data.get("imageinfo", [])
            if imageinfo:
                return imageinfo[0].get("url")
        return None
    except Exception as e:
        print(f"[B-roll] Wikimedia Commons failed for '{query}': {e}")
        return None


def _nasa_video(query: str) -> str | None:
    """Fetches a real NASA video for science/space topics. Completely free, no key."""
    try:
        r = requests.get(
            "https://images-api.nasa.gov/search",
            params={
                "q": query,
                "media_type": "video",
                "page_size": 5,
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=20,
        )
        r.raise_for_status()
        items = r.json().get("collection", {}).get("items", [])
        if not items:
            return None

        # Pick one from top 3
        item = random.choice(items[:3])
        nasa_id = item.get("data", [{}])[0].get("nasa_id")
        if not nasa_id:
            return None

        r_asset = requests.get(
            f"https://images-api.nasa.gov/asset/{urllib.parse.quote(nasa_id)}",
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=15,
        )
        r_asset.raise_for_status()
        items_asset = r_asset.json().get("collection", {}).get("items", [])
        for a in items_asset:
            href = a.get("href", "")
            if href.endswith("~medium.mp4") or href.endswith("~mobile.mp4"):
                return href
        for a in items_asset:
            href = a.get("href", "")
            if href.endswith(".mp4"):
                return href
        return None
    except Exception as e:
        print(f"[B-roll] NASA video failed for '{query}': {e}")
        return None


def _archive_video(query: str) -> str | None:
    """Search Internet Archive for public domain movies. No API key needed."""
    try:
        r = requests.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": f"title:({query}) AND mediatype:(movies)",
                "fl[]": "identifier",
                "rows": "5",
                "output": "json",
            },
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=20,
        )
        r.raise_for_status()
        docs = r.json().get("response", {}).get("docs", [])
        if not docs:
            return None

        identifier = docs[0]["identifier"]
        r_files = requests.get(
            f"https://archive.org/metadata/{urllib.parse.quote(identifier)}",
            headers={"User-Agent": "yt-auto/1.0 (educational-pipeline)"},
            timeout=15,
        )
        r_files.raise_for_status()
        files = r_files.json().get("files", [])
        for f in files:
            name = f.get("name", "")
            if name.endswith(".mp4") and int(f.get("size", 0)) > 10_000:
                return f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"
        return None
    except Exception as e:
        print(f"[B-roll] Internet Archive failed for '{query}': {e}")
        return None


def _download_video_robust(url: str, out_path: str, segment_index: int) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=90, headers={"User-Agent": "yt-auto/1.0"})
        r.raise_for_status()

        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()
        is_webm = path.endswith(".webm") or path.endswith(".ogv")

        temp_file = f"output/temp_dl_{segment_index}" + (".webm" if is_webm else ".mp4")
        with open(temp_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 10_000:
            if is_webm:
                print(f"[B-roll] Converting webm/ogv from {url} to mp4...")
                cmd = [
                    "ffmpeg", "-y", "-i", temp_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-an", out_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 10_000
            else:
                if os.path.exists(out_path):
                    os.remove(out_path)
                os.rename(temp_file, out_path)
                return True
        return False
    except Exception as e:
        print(f"[B-roll] Robust download failed for {url}: {e}")
        return False


# ── Ken Burns zoom — applied to ALL image-to-video conversions ───────────────

def _image_to_ken_burns_video(img_path: str, out_path: str, w: int, h: int, duration: float = 6.0):
    """
    Converts a static image to a video with a slow cinematic zoom (Ken Burns effect).
    Uses FFmpeg zoompan filter — zero dependencies, no quality loss.
    Randomly picks zoom direction for variety across segments.
    """
    fps    = 30
    frames = int(duration * fps)  # zoompan needs total frame count, not seconds

    # Three zoom styles — randomly chosen per segment for variety
    styles = [
        # Slow zoom into center
        f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
        # Slow zoom starting top-left
        f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':d={frames}:x=0:y=0:s={w}x{h}:fps={fps}",
        # Slow zoom, panning slightly right
        f"scale=8000:-1,zoompan=z='min(zoom+0.001,1.3)':d={frames}:x='iw-iw/zoom':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
    ]
    vf = random.choice(styles)

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-vf", f"{vf},setsar=1",
        "-t", str(duration), "-r", str(fps),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an", out_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── Fallback: Pollinations.ai (AI-generated, multiple models) ────────────────

def _pollinations_image(query: str, w: int, h: int, img_path: str) -> bool:
    """Returns True if image was downloaded successfully."""
    encoded = urllib.parse.quote(query)
    for model in ["flux", "flux-realism", "turbo"]:
        try:
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width={w}&height={h}&model={model}&nologo=true"
            )
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(img_path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception as e:
            print(f"[B-roll] Pollinations {model} failed: {e}")
    return False


# ── Last resort: PIL gradient placeholder ────────────────────────────────────

def _pil_placeholder(query: str, w: int, h: int, img_path: str):
    """Better-looking placeholder: dark gradient with large centered text."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    # Dark gradient background (top dark blue → bottom near-black)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        ratio = y / h
        arr[y, :, 0] = int(10 + ratio * 5)   # R
        arr[y, :, 1] = int(10 + ratio * 20)   # G
        arr[y, :, 2] = int(40 + ratio * 20)   # B

    img  = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # Draw centered query text, large and readable
    words  = query.upper().split()
    lines  = []
    line   = ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) > 18:
            lines.append(line.strip())
            line = word
        else:
            line = test
    if line:
        lines.append(line.strip())

    font_size = max(60, min(100, w // (max(len(l) for l in lines) + 1) if lines else 80))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    total_text_h = len(lines) * (font_size + 10)
    y_start      = (h - total_text_h) // 2

    for i, line_text in enumerate(lines):
        bbox = draw.textbbox((0, 0), line_text, font=font)
        tw   = bbox[2] - bbox[0]
        x    = (w - tw) // 2
        y    = y_start + i * (font_size + 10)
        # Shadow
        draw.text((x + 3, y + 3), line_text, font=font, fill=(0, 0, 0))
        # Main text
        draw.text((x, y), line_text, font=font, fill=(255, 255, 255))

    img.save(img_path, "JPEG", quality=90)


# ── Master fetch function ────────────────────────────────────────────────────

def fetch_broll(query: str, format_type: str, segment_index: int, duration: float = 6.0, narration: str = "", alt_queries: list[str] | None = None) -> str:
    """
    6-tier B-roll waterfall with Gemini Vision matching:
      1. Pexels video (ranked and validated via Gemini Vision API on thumbnails)
      2. Pixabay video (validated via Gemini Vision API on extracted frame)
      3. Coverr video (validated via Gemini Vision API on extracted frame)
      4. NASA image → Ken Burns video (for science/space queries, free, no key)
      5. Wikipedia image → Ken Burns video (for named people/concepts, free, no key)
      6. Pollinations AI image → Ken Burns video (fallback)
      7. PIL gradient placeholder → Ken Burns video (last resort)

    Ken Burns zoom is applied to ALL image sources for cinematic motion.
    """
    orientation = "portrait" if format_type == "short" else "landscape"
    out_path    = f"output/broll_{segment_index}.mp4"
    img_path    = f"output/broll_{segment_index}.jpg"
    w, h        = (1080, 1920) if format_type == "short" else (1920, 1080)

    os.makedirs("output", exist_ok=True)

    # Return cached clip if already valid
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10_000:
        print(f"[B-roll] Segment {segment_index}: using cached clip.")
        return out_path

    # Build a simpler fallback query (first 2-3 nouns if first query fails)
    words         = query.split()
    fallback_query = " ".join(words[:2]) if len(words) > 2 else query

    # Build list of queries to try (primary + alternatives + fallback)
    queries_to_try = [query]
    if alt_queries:
        queries_to_try.extend([q for q in alt_queries if q != query])
    queries_to_try.append(fallback_query)

    # ── Try Pexels with vision ranking ───────────────────────────────────────
    candidates = []
    for q in queries_to_try:
        print(f"[B-roll] Segment {segment_index}: searching Pexels for '{q}'…")
        candidates = _pexels_candidates(q, orientation)
        if candidates:
            break

    if candidates:
        thumbs = []
        for idx, cand in enumerate(candidates):
            try:
                r_thumb = requests.get(cand["thumb_url"], timeout=15)
                r_thumb.raise_for_status()
                thumbs.append(r_thumb.content)
            except Exception as e:
                print(f"[B-roll] Failed to download thumbnail {idx} from Pexels: {e}")
                thumbs.append(b"")

        from pipeline.vision_match import vision_rank_broll
        best_idx, match_found = vision_rank_broll(thumbs, narration, query)

        if match_found and best_idx is not None and best_idx < len(candidates):
            chosen = candidates[best_idx]
            print(f"[B-roll] Pexels match found at index {best_idx}. Downloading video…")
            try:
                r_vid = requests.get(chosen["video_url"], stream=True, timeout=90)
                r_vid.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r_vid.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                if os.path.getsize(out_path) > 10_000:
                    print(f"[B-roll] Segment {segment_index}: Pexels video downloaded OK.")
                    return out_path
            except Exception as e:
                print(f"[B-roll] Pexels video download failed: {e}. Continuing waterfall…")
                if os.path.exists(out_path):
                    os.remove(out_path)
        else:
            print(f"[B-roll] No suitable Pexels candidate passed Vision Match. Trying next sources…")

    # ── Try other video sources with single frame validation ─────────────────
    other_videos = [
        ("Pixabay (main)", lambda: _pixabay_video(query)),
        ("Pixabay (fallback)", lambda: _pixabay_video(fallback_query)),
        ("Coverr (main)", lambda: _coverr_video(query)),
        ("Coverr (fallback)", lambda: _coverr_video(fallback_query)),
        ("NASA video (main)", lambda: _nasa_video(query)),
        ("NASA video (fallback)", lambda: _nasa_video(fallback_query)),
        ("Wikimedia video (main)", lambda: _wikimedia_video(query)),
        ("Wikimedia video (fallback)", lambda: _wikimedia_video(fallback_query)),
        ("Archive video (main)", lambda: _archive_video(query)),
        ("Archive video (fallback)", lambda: _archive_video(fallback_query)),
    ]

    from pipeline.vision_match import vision_rank_broll

    for label, fetch_url_fn in other_videos:
        video_url = fetch_url_fn()
        if video_url:
            print(f"[B-roll] Downloading video from {label}…")
            if _download_video_robust(video_url, out_path, segment_index):
                # Extract one frame via FFmpeg
                temp_frame_path = f"output/temp_frame_{segment_index}.jpg"
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)
                
                cmd = [
                    "ffmpeg", "-y", "-i", out_path,
                    "-vf", "thumbnail=n=30", "-frames:v", "1", temp_frame_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(temp_frame_path):
                    with open(temp_frame_path, "rb") as tf:
                        frame_data = tf.read()
                    os.remove(temp_frame_path)
                    
                    _, match_found = vision_rank_broll([frame_data], narration, query)
                    if match_found:
                        print(f"[B-roll] {label} video accepted by Vision Match.")
                        return out_path
                    else:
                        print(f"[B-roll] {label} video rejected by Vision Match. Continuing waterfall…")
                        os.remove(out_path)
                else:
                    print(f"[B-roll] Warning: Frame extraction failed for {label}. Accepting by default.")
                    return out_path

    # ── Try image sources (all converted with Ken Burns) ─────────────────────
    print(f"[B-roll] Segment {segment_index}: trying image sources…")

    img_url = (
        _nasa_image(query)
        or _nasa_image(fallback_query)
        or _wikipedia_image(query)
        or _wikipedia_image(fallback_query)
    )

    if img_url:
        try:
            r = requests.get(img_url, timeout=30, headers={"User-Agent": "yt-auto/1.0"})
            r.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(r.content)
            print(f"[B-roll] Segment {segment_index}: image downloaded. Applying Ken Burns…")
            _image_to_ken_burns_video(img_path, out_path, w, h, duration)
            return out_path
        except Exception as e:
            print(f"[B-roll] Image source failed: {e}. Trying Pollinations…")

    # ── Pollinations AI image ─────────────────────────────────────────────────
    if _pollinations_image(query, w, h, img_path):
        print(f"[B-roll] Segment {segment_index}: Pollinations OK. Applying Ken Burns…")
        _image_to_ken_burns_video(img_path, out_path, w, h, duration)
        return out_path

    # ── PIL gradient placeholder ──────────────────────────────────────────────
    print(f"[B-roll] Segment {segment_index}: all sources failed. Using gradient placeholder.")
    _pil_placeholder(query, w, h, img_path)
    _image_to_ken_burns_video(img_path, out_path, w, h, duration)
    return out_path
