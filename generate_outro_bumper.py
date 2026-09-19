import os
import sys
import math
import asyncio
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import edge_tts

OUT_DIR = "/root/yt-auto/output"
os.makedirs(OUT_DIR, exist_ok=True)
TMP_FRAMES_DIR = "/tmp/bumper_frames"
os.makedirs(TMP_FRAMES_DIR, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 120  # Exactly 4.0 seconds

# Font paths
FONT_TITLE = "/root/.local/share/fonts/BarlowCondensed-ExtraBold.ttf"
FONT_HEADING = "/root/.local/share/fonts/Rajdhani-Bold.ttf"
FONT_BODY = "/root/.local/share/fonts/Montserrat-Variable.ttf"

font_title_lg = ImageFont.truetype(FONT_TITLE, 76)
font_title_md = ImageFont.truetype(FONT_TITLE, 64)
font_badge = ImageFont.truetype(FONT_HEADING, 32)
font_body_bold = ImageFont.truetype(FONT_HEADING, 44)
font_body_sm = ImageFont.truetype(FONT_BODY, 30)
font_cta_btn = ImageFont.truetype(FONT_TITLE, 52)
font_cta_sub = ImageFont.truetype(FONT_HEADING, 34)

# Load Source Images
dream_img_path = "/root/dreamheights-source/images/dreamsquare_hero_1920x1728.jpg"
if not os.path.exists(dream_img_path):
    dream_img_path = "/tmp/test_dream_clean.png"

bioprac_img_path = "/tmp/live_myhealthprac.png"

img_dream = Image.open(dream_img_path).convert("RGB")
img_bioprac = Image.open(bioprac_img_path).convert("RGB")

async def generate_tts():
    wav_path = "/tmp/bumper_voice.mp3"
    text = "We engineer custom websites and autonomous content engines. Tap the bio to scale."
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+32%")
    await communicate.save(wav_path)
    return wav_path

def draw_glass_card(draw, x0, y0, x1, y1, radius=24, fill=(10, 15, 26, 210), border=(0, 229, 255, 120)):
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=border, width=2)

print("[1/4] Generating voiceover...")
voice_path = asyncio.run(generate_tts())

print("[2/4] Rendering 120 frames (4.0s @ 30fps)...")
for i in range(TOTAL_FRAMES):
    t = i / FPS # time in seconds
    frame = Image.new("RGBA", (WIDTH, HEIGHT), (8, 10, 16, 255))
    draw = ImageDraw.Draw(frame)

    # ── PHASE 1: DREAM HEIGHTS (0.0s - 1.33s / frames 0 - 39) ──
    if i < 40:
        prog = i / 40.0
        # Smooth scale
        scale = 1.0 + 0.08 * prog
        w_scaled = int(WIDTH * scale)
        h_scaled = int(HEIGHT * scale)
        bg = img_dream.resize((w_scaled, h_scaled), Image.Resampling.LANCZOS)
        # Center crop
        left = (w_scaled - WIDTH) // 2
        top = (h_scaled - HEIGHT) // 2
        frame.paste(bg.crop((left, top, left + WIDTH, top + HEIGHT)))

        # Dark gradient overlay
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        # Top gradient
        for y in range(400):
            alpha = int(210 * (1 - y / 400.0))
            ov_draw.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, alpha))
        # Bottom gradient
        for y in range(HEIGHT - 500, HEIGHT):
            alpha = int(230 * ((y - (HEIGHT - 500)) / 500.0))
            ov_draw.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, alpha))
        frame = Image.alpha_composite(frame, overlay)
        draw = ImageDraw.Draw(frame)

        # Top Badge
        badge_text = "ENTERPRISE PORTFOLIO  •  01"
        draw_glass_card(draw, 80, 100, WIDTH - 80, 170, radius=20, fill=(10, 15, 24, 230), border=(0, 240, 255, 180))
        draw.text((WIDTH // 2, 135), badge_text, font=font_badge, fill=(0, 240, 255, 255), anchor="mm")

        # Bottom Glass Card
        draw_glass_card(draw, 70, HEIGHT - 460, WIDTH - 70, HEIGHT - 120, radius=32, fill=(10, 15, 26, 230), border=(255, 255, 255, 50))
        draw.text((110, HEIGHT - 410), "DREAM HEIGHTS", font=font_title_lg, fill=(255, 255, 255, 255))
        draw.text((110, HEIGHT - 325), "3D Architecture & Luxury Web Platform", font=font_body_bold, fill=(0, 229, 255, 255))
        draw.text((110, HEIGHT - 260), "Next.js • Procedural Three.js • High-Conversion UI", font=font_body_sm, fill=(200, 215, 230, 255))
        draw.text((110, HEIGHT - 200), "Live Deployment: dreamheights-source.vercel.app", font=font_body_sm, fill=(140, 160, 185, 255))

    # ── PHASE 2: BIOPRAC (1.33s - 2.66s / frames 40 - 79) ──
    elif i < 80:
        prog = (i - 40) / 40.0
        # Smooth scroll
        pan_y = int(300 * prog)
        bg = img_bioprac.resize((WIDTH, int(img_bioprac.height * (WIDTH / img_bioprac.width))), Image.Resampling.LANCZOS)
        crop_top = max(0, min(pan_y, bg.height - HEIGHT))
        frame.paste(bg.crop((0, crop_top, WIDTH, crop_top + HEIGHT)))

        # Dark gradient overlay
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        for y in range(400):
            alpha = int(210 * (1 - y / 400.0))
            ov_draw.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, alpha))
        for y in range(HEIGHT - 500, HEIGHT):
            alpha = int(230 * ((y - (HEIGHT - 500)) / 500.0))
            ov_draw.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, alpha))
        frame = Image.alpha_composite(frame, overlay)
        draw = ImageDraw.Draw(frame)

        # Top Badge
        badge_text = "ENTERPRISE PORTFOLIO  •  02"
        draw_glass_card(draw, 80, 100, WIDTH - 80, 170, radius=20, fill=(10, 15, 24, 230), border=(50, 255, 180, 180))
        draw.text((WIDTH // 2, 135), badge_text, font=font_badge, fill=(50, 255, 180, 255), anchor="mm")

        # Bottom Glass Card
        draw_glass_card(draw, 70, HEIGHT - 460, WIDTH - 70, HEIGHT - 120, radius=32, fill=(10, 18, 24, 230), border=(255, 255, 255, 50))
        draw.text((110, HEIGHT - 410), "BIOPRAC HEALTH", font=font_title_lg, fill=(255, 255, 255, 255))
        draw.text((110, HEIGHT - 325), "Clinical Longevity & Healthcare Platform", font=font_body_bold, fill=(50, 255, 180, 255))
        draw.text((110, HEIGHT - 260), "Telemetry Dashboard • Cleanroom UX • Web Vitals 100", font=font_body_sm, fill=(200, 225, 220, 255))
        draw.text((110, HEIGHT - 200), "Live Deployment: myhealthprac.vercel.app", font=font_body_sm, fill=(140, 175, 170, 255))

    # ── PHASE 3: CALL TO ACTION (2.66s - 4.0s / frames 80 - 119) ──
    else:
        prog = (i - 80) / 40.0
        # Dark high-tech cybernetic background with clean vertical gradient
        base = Image.new("RGBA", (WIDTH, HEIGHT), (8, 10, 16, 255))
        b_draw = ImageDraw.Draw(base)
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(6 + 8 * ratio)
            g = int(8 + 12 * ratio)
            b = int(14 + 26 * ratio)
            b_draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

        frame = base
        draw = ImageDraw.Draw(frame)

        # Top Tag
        draw_glass_card(draw, 140, 220, WIDTH - 140, 285, radius=18, fill=(12, 18, 28, 240), border=(0, 229, 255, 160))
        draw.text((WIDTH // 2, 252), "AUTONOMOUS MEDIA & DIGITAL PLATFORMS", font=font_badge, fill=(0, 229, 255, 255), anchor="mm")

        # Main Headline
        draw.text((WIDTH // 2, 430), "NEED CLIENTS OR", font=font_title_lg, fill=(255, 255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 520), "VIRAL AUTOMATION?", font=font_title_lg, fill=(0, 240, 255, 255), anchor="mm")

        # Core Value Prop Cards
        draw_glass_card(draw, 90, 650, WIDTH - 90, 830, radius=24, fill=(14, 20, 32, 230), border=(0, 229, 255, 60))
        draw.text((130, 690), "• Custom High-Converting Websites", font=font_body_bold, fill=(255, 255, 255, 255))
        draw.text((130, 755), "3D Three.js, Next.js, Framer-grade polish like Dream Heights & BioPrac", font=font_body_sm, fill=(170, 190, 215, 255))

        draw_glass_card(draw, 90, 870, WIDTH - 90, 1050, radius=24, fill=(14, 20, 32, 230), border=(0, 229, 255, 60))
        draw.text((130, 910), "• 100% Autonomous Video Fleets", font=font_body_bold, fill=(255, 255, 255, 255))
        draw.text((130, 975), "Self-operating AI media pipelines running 24/7 in the cloud", font=font_body_sm, fill=(170, 190, 215, 255))

        # Bottom Magnetic CTA Button (Pulsing neon)
        pulse = math.sin(prog * math.pi * 2) * 4
        btn_y0 = int(1220 + pulse)
        btn_y1 = int(1360 + pulse)
        draw.rounded_rectangle([90, btn_y0, WIDTH - 90, btn_y1], radius=30, fill=(0, 235, 255, 255))
        draw.text((WIDTH // 2, (btn_y0 + btn_y1) // 2), "DM 'BUILD' TO WORK WITH US", font=font_cta_btn, fill=(6, 10, 18, 255), anchor="mm")

        draw.text((WIDTH // 2, 1420), "OR TAP THE LINK IN CHANNEL BIO", font=font_cta_sub, fill=(220, 235, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 1480), "Limited Client Intake • Enterprise Tier", font=font_body_sm, fill=(130, 155, 180, 255), anchor="mm")

    frame.save(f"{TMP_FRAMES_DIR}/frame_{i:04d}.png")

print("[3/4] Encoding bumper video with FFmpeg...")
out_video = f"{OUT_DIR}/ad_bumper_ch1.mp4"
cmd_ffmpeg = [
    "ffmpeg", "-y",
    "-r", str(FPS),
    "-i", f"{TMP_FRAMES_DIR}/frame_%04d.png",
    "-i", voice_path,
    "-filter_complex", "[1:a]atempo=1.05[a]",
    "-map", "0:v",
    "-map", "[a]",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-t", "4.0",
    out_video
]
subprocess.run(cmd_ffmpeg, check=True)
print(f"[4/4] Outro Bumper Generated Successfully: {out_video}")
