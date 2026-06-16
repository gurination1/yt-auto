import os
import subprocess

def clean_thumbnail_text(text: str) -> str:
    # Remove chars that frequently break FFmpeg filter parsing (e.g. colons, commas, semicolons, backslashes)
    cleaned = "".join(c for c in text if c.isalnum() or c in " -!?")
    # Escape single quotes for shell/ffmpeg drawtext argument
    return cleaned.replace("'", "'\\\\''")

def generate_thumbnail(final_video_path: str, thumbnail_text: str) -> str:
    print(f"Generating thumbnail for {final_video_path} with text: '{thumbnail_text}'...")
    os.makedirs("output", exist_ok=True)
    
    hook_frame_path = "output/hook_frame.jpg"
    thumbnail_path = "output/thumbnail.jpg"
    
    # 1. Extract best frame of video
    print("Extracting best frame from video...")
    # Use FFmpeg thumbnail filter to find most visually rich frame (not frame 0)
    cmd_frame = [
        "ffmpeg", "-y", "-i", final_video_path,
        "-vf", "thumbnail=n=300",    # analyze first 300 frames (~10s), pick best
        "-frames:v", "1", "-q:v", "2", hook_frame_path
    ]
    subprocess.run(cmd_frame, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Scale and draw text
    cleaned_text = clean_thumbnail_text(thumbnail_text).upper()   # ALL CAPS for impact
    
    # We will try with Bebas Neue first, and fallback to DejaVu Sans Bold / sans if it fails.
    drawtext_filter = (
        f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        f"drawbox=x=0:y=200:w=iw:h=320:color=black@0.65:t=fill,"
        f"drawtext=text='{cleaned_text}':"
        f"font='Bebas Neue':fontsize=110:"
        f"fontcolor=yellow:borderw=8:bordercolor=black:"
        f"x=(w-text_w)/2:y=(h-text_h)/2"
    )
    
    cmd_thumb = [
        "ffmpeg", "-y", "-i", hook_frame_path,
        "-vf", drawtext_filter,
        "-q:v", "2", thumbnail_path
    ]
    
    try:
        print("Drawing thumbnail text with Bebas Neue...")
        subprocess.run(cmd_thumb, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Font Bebas Neue failed, retrying with DejaVu Sans Bold...")
        drawtext_filter_fallback = (
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"drawbox=x=0:y=200:w=iw:h=320:color=black@0.65:t=fill,"
            f"drawtext=text='{cleaned_text}':font='DejaVu Sans Bold':fontsize=95:"
            f"fontcolor=yellow:borderw=8:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2"
        )
        cmd_thumb_fallback = [
            "ffmpeg", "-y", "-i", hook_frame_path,
            "-vf", drawtext_filter_fallback,
            "-q:v", "2", thumbnail_path
        ]
        subprocess.run(cmd_thumb_fallback, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    print(f"Thumbnail generated successfully: {thumbnail_path}")
    return thumbnail_path
