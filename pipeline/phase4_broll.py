import os
import random
import requests
import urllib.parse
import subprocess
from pipeline.config import PEXELS_API_KEY, PIXABAY_API_KEY, COVERR_API_KEY, NASA_API_KEY


# ── Source 1: Pexels ─────────────────────────────────────────────────────────

def _pexels_video(query: str, orientation: str) -> str | None:
    if not PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 5, "orientation": orientation},
            timeout=30,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None
        video = random.choice(videos[:3])
        files = [f for f in video["video_files"] if f.get("quality") in ("hd", "sd")]
        files.sort(key=lambda f: f.get("width", 0), reverse=True)
        return files[0]["link"] if files else None
    except Exception as e:
        print(f"[B-roll] Pexels failed for '{query}': {e}")
        return None


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

def fetch_broll(query: str, format_type: str, segment_index: int, duration: float = 6.0) -> str:
    """
    6-tier B-roll waterfall:
      1. Pexels video
      2. Pixabay video
      3. Coverr video (cinematic, requires COVERR_API_KEY)
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

    # ── Try video sources ────────────────────────────────────────────────────
    print(f"[B-roll] Segment {segment_index}: searching for '{query}'…")

    # Build a simpler fallback query (first 2-3 nouns if first query fails)
    words         = query.split()
    fallback_query = " ".join(words[:2]) if len(words) > 2 else query

    video_url = (
        _pexels_video(query, orientation)
        or _pexels_video(fallback_query, orientation)
        or _pixabay_video(query)
        or _pixabay_video(fallback_query)
        or _coverr_video(query)
        or _coverr_video(fallback_query)
    )

    if video_url:
        try:
            r = requests.get(video_url, stream=True, timeout=90)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(out_path) > 10_000:
                print(f"[B-roll] Segment {segment_index}: video downloaded OK.")
                return out_path
        except Exception as e:
            print(f"[B-roll] Video download failed: {e}. Falling to image sources…")
            if os.path.exists(out_path):
                os.remove(out_path)

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
