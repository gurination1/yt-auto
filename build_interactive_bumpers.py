import os
import sys
import math
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 132  # Exactly 4.40 seconds
OUT_BUMPERS_DIR = "/root/yt-auto/assets/bumpers"
os.makedirs(OUT_BUMPERS_DIR, exist_ok=True)

TMP_FRAMES_DIR = "/tmp/bumper_render"
os.makedirs(TMP_FRAMES_DIR, exist_ok=True)

# Fonts
FONT_TITLE_X = "/root/.local/share/fonts/BarlowCondensed-ExtraBold.ttf"
FONT_TITLE_B = "/root/.local/share/fonts/BarlowCondensed-Bold.ttf"
FONT_HEAD = "/root/.local/share/fonts/Rajdhani-Bold.ttf"
FONT_BODY = "/root/.local/share/fonts/Montserrat-Variable.ttf"

font_title_lg = ImageFont.truetype(FONT_TITLE_X, 62)
font_title_md = ImageFont.truetype(FONT_TITLE_X, 52)
font_head_md = ImageFont.truetype(FONT_HEAD, 38)
font_head_sm = ImageFont.truetype(FONT_HEAD, 30)
font_badge = ImageFont.truetype(FONT_HEAD, 24)
font_url = ImageFont.truetype(FONT_BODY, 24)
font_browser_url = ImageFont.truetype(FONT_HEAD, 20)
font_cta_btn = ImageFont.truetype(FONT_TITLE_X, 46)
font_cta_sub = ImageFont.truetype(FONT_HEAD, 28)
font_stat_num = ImageFont.truetype(FONT_TITLE_X, 44)
font_stat_lbl = ImageFont.truetype(FONT_HEAD, 22)

SFX_WHOOSH = "/root/yt-auto/cache_sfx/sfx_19284.wav"

def make_rounded_mask(w, h, radius):
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    return mask

def draw_cyber_background(draw, t, accent_rgb=(0, 229, 255)):
    # Dark modern obsidian gradient
    for y in range(0, HEIGHT, 16):
        ratio = y / HEIGHT
        r = int(6 + ratio * 8)
        g = int(8 + ratio * 10)
        b = int(14 + ratio * 18)
        draw.rectangle([0, y, WIDTH, y + 16], fill=(r, g, b))

    # Tech grid
    grid_alpha = 15
    for gx in range(60, WIDTH, 120):
        draw.line([gx, 0, gx, HEIGHT], fill=(35, 50, 75, grid_alpha), width=1)
    for gy in range(80, HEIGHT, 120):
        draw.line([0, gy, WIDTH, gy], fill=(35, 50, 75, grid_alpha), width=1)

def draw_pill_badge(draw, text, x, y, bg_color=(12, 18, 30, 230), border_color=(0, 229, 255, 200), text_color=(0, 229, 255), show_dot=False, dot_color=(0, 255, 157)):
    bbox = font_badge.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x = 18 if not show_dot else 28
    pad_y = 6
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw.rounded_rectangle([x - w // 2, y - h // 2, x + w // 2, y + h // 2], radius=h // 2, fill=bg_color, outline=border_color, width=2)
    
    if show_dot:
        dot_r = 5
        draw.ellipse([x - w // 2 + 14, y - dot_r, x - w // 2 + 14 + dot_r * 2, y + dot_r], fill=dot_color)
        draw.text((x - tw // 2 + 10, y - th // 2 - 2), text, font=font_badge, fill=text_color)
    else:
        draw.text((x - tw // 2, y - th // 2 - 2), text, font=font_badge, fill=text_color)

def draw_cta_button(draw, t, text, x, y, w=840, h=96, cta_color1=(0, 229, 255), cta_color2=(0, 119, 255)):
    pulse = math.sin(t * 7)
    glow_alpha = int(140 + 70 * pulse)
    
    x0 = x - w // 2
    y0 = y - h // 2
    x1 = x + w // 2
    y1 = y + h // 2
    
    # Outer animated glow border
    draw.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], radius=(h + 8) // 2, outline=(cta_color1[0], cta_color1[1], cta_color1[2], glow_alpha), width=3)
    
    btn_fill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(btn_fill)
    for bx in range(w):
        r = bx / w
        cr = int(cta_color1[0] * (1 - r) + cta_color2[0] * r)
        cg = int(cta_color1[1] * (1 - r) + cta_color2[1] * r)
        cb = int(cta_color1[2] * (1 - r) + cta_color2[2] * r)
        bdraw.line([bx, 0, bx, h], fill=(cr, cg, cb, 255))
        
    mask = make_rounded_mask(w, h, h // 2)
    draw._image.paste(btn_fill, (x0, y0), mask)
    
    bbox = font_cta_btn.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw // 2, y - th // 2 - 4), text, font=font_cta_btn, fill=(5, 8, 14, 255))

def draw_phone_frame(base_img, screen_frame_img, center_x, center_y, phone_w, phone_h, border_color=(0, 229, 255), angle=0.0, browser_url=""):
    phone = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(phone)
    
    bezel = 10
    radius = 32
    
    # Phone body & border
    pdraw.rounded_rectangle([0, 0, phone_w, phone_h], radius=radius, fill=(16, 22, 34, 255), outline=border_color, width=3)
    
    # Inner screen
    sw = phone_w - bezel * 2
    sh = phone_h - bezel * 2
    screen_resized = screen_frame_img.resize((sw, sh), Image.Resampling.LANCZOS)
    screen_mask = make_rounded_mask(sw, sh, radius - 8)
    
    phone.paste(screen_resized, (bezel, bezel), screen_mask)
    
    # Redraw frame outline
    pdraw = ImageDraw.Draw(phone)
    pdraw.rounded_rectangle([bezel, bezel, phone_w - bezel, phone_h - bezel], radius=radius - 8, outline=(40, 54, 80, 160), width=1)
    
    # Dynamic Island
    notch_w = int(phone_w * 0.28)
    notch_h = 20
    nx0 = (phone_w - notch_w) // 2
    ny0 = bezel + 6
    pdraw.rounded_rectangle([nx0, ny0, nx0 + notch_w, ny0 + notch_h], radius=10, fill=(6, 8, 12, 255))
    pdraw.ellipse([nx0 + notch_w - 18, ny0 + 5, nx0 + notch_w - 10, ny0 + 13], fill=(20, 30, 48, 255))
    
    # Browser URL Pill Bar under Dynamic Island
    if browser_url:
        bar_w = int(phone_w * 0.72)
        bar_h = 26
        bx0 = (phone_w - bar_w) // 2
        by0 = ny0 + notch_h + 8
        pdraw.rounded_rectangle([bx0, by0, bx0 + bar_w, by0 + bar_h], radius=13, fill=(10, 14, 22, 220), outline=(0, 229, 255, 120), width=1)
        # Lock dot
        pdraw.ellipse([bx0 + 10, by0 + 9, bx0 + 18, by0 + 17], fill=(0, 255, 157, 240))
        pdraw.text((bx0 + 24, by0 + 4), browser_url, font=font_browser_url, fill=(210, 230, 255, 230))
        
    # Glass sheen
    sheen = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(sheen)
    sdraw.polygon([(0, 0), (phone_w // 2, 0), (phone_w // 4, phone_h), (0, phone_h)], fill=(255, 255, 255, 10))
    phone.alpha_composite(sheen)
    
    if angle != 0.0:
        phone = phone.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        
    pw, ph = phone.size
    px = center_x - pw // 2
    py = center_y - ph // 2
    base_img.alpha_composite(phone, (px, py))

def mux_video_and_audio(frames_pattern, audio_path, output_mp4):
    """Encodes 1080x1920 @ 30fps H.264 video with AAC 48kHz stereo and loudnorm."""
    temp_mp4 = output_mp4 + ".temp.mp4"
    cmd = [
        "/data/data/com.termux/files/usr/bin/ffmpeg", "-y",
        "-framerate", "30",
        "-i", frames_pattern,
        "-i", audio_path,
        "-i", SFX_WHOOSH,
        "-filter_complex",
        "[1:a]volume=1.4[vo];[2:a]volume=0.30[sfx];[vo][sfx]amix=inputs=2:duration=first:normalize=0[amix];[amix]loudnorm=I=-14:TP=-1.5:LRA=11,aformat=channel_layouts=stereo:sample_rates=48000[afinal]",
        "-map", "0:v:0",
        "-map", "[afinal]",
        "-c:v", "libx264", "-preset", "faster", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest",
        temp_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.move(temp_mp4, output_mp4)
    print(f"[✓] Created bumper: {output_mp4} ({os.path.getsize(output_mp4)} bytes)")

# ─────────────────────────────────────────────────────────────
# 1. BUMPER 1: Dream Heights Luxury 3D Web & Architecture
# ─────────────────────────────────────────────────────────────
def render_bumper_1():
    print("[1/5] Rendering Ad 1: Dream Heights 3D Web...")
    fdir = os.path.join(TMP_FRAMES_DIR, "b1")
    os.makedirs(fdir, exist_ok=True)
    
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (6, 8, 14, 255))
        draw = ImageDraw.Draw(frame)
        draw_cyber_background(draw, t, accent_rgb=(0, 229, 255))
        
        # Header
        draw_pill_badge(draw, "LIVE CLIENT BUILD", WIDTH // 2, 130, bg_color=(10, 20, 36, 240), border_color=(0, 229, 255, 230), text_color=(0, 229, 255), show_dot=True, dot_color=(0, 255, 157))
        
        # Headline
        draw.text((WIDTH // 2, 210), "NEED A 3D WEB EXPERIENCE?", font=font_title_lg, fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 275), "BESPOKE ARCHITECTURAL PORTALS", font=font_head_md, fill=(0, 229, 255), anchor="mm")
        
        # Phone Mockup with Dream Heights 3D Render
        frame_idx = min(140, i + 1)
        screen_path = f"/tmp/frames_dream/frame_{frame_idx:04d}.jpg"
        if not os.path.exists(screen_path):
            screen_path = "/tmp/frames_dream/frame_0001.jpg"
        screen_img = Image.open(screen_path).convert("RGBA")
        
        draw_phone_frame(frame, screen_img, WIDTH // 2, 860, 520, 1020, border_color=(0, 229, 255, 220), browser_url="dreamheights-source.vercel.app")
        
        # Under Phone: Live URL pill
        draw_pill_badge(draw, "dreamheights-source.vercel.app", WIDTH // 2, 1420, bg_color=(8, 14, 24, 240), border_color=(0, 229, 255, 180), text_color=(200, 230, 255), show_dot=True, dot_color=(0, 229, 255))
        
        # Tags row
        draw_pill_badge(draw, "3D WEBGL", 270, 1480, border_color=(0, 229, 255, 140), text_color=(0, 229, 255))
        draw_pill_badge(draw, "CUSTOM REACT", 540, 1480, border_color=(0, 229, 255, 140), text_color=(0, 229, 255))
        draw_pill_badge(draw, "HIGH CONVERSION", 810, 1480, border_color=(0, 229, 255, 140), text_color=(0, 229, 255))
        
        # CTA Button & Subtext
        draw_cta_button(draw, t, "TAP BIO TO SCALE • DM '3D'", WIDTH // 2, 1630, w=860, h=100, cta_color1=(0, 229, 255), cta_color2=(0, 119, 255))
        draw.text((WIDTH // 2, 1720), "WORLDWIDE HIGH-TICKET CLIENT ACQUISITION", font=font_cta_sub, fill=(140, 165, 195), anchor="mm")
        
        frame.convert("RGB").save(f"{fdir}/f_{i:04d}.jpg", quality=92)
        
    out_mp4 = os.path.join(OUT_BUMPERS_DIR, "ad_1_dreamheights.mp4")
    mux_video_and_audio(f"{fdir}/f_%04d.jpg", "/tmp/bumper_audio/ad_1_dreamheights.mp3", out_mp4)

# ─────────────────────────────────────────────────────────────
# 2. BUMPER 2: BioPrac Clinical HealthTech SaaS
# ─────────────────────────────────────────────────────────────
def render_bumper_2():
    print("[2/5] Rendering Ad 2: BioPrac Clinical SaaS...")
    fdir = os.path.join(TMP_FRAMES_DIR, "b2")
    os.makedirs(fdir, exist_ok=True)
    
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (6, 12, 10, 255))
        draw = ImageDraw.Draw(frame)
        draw_cyber_background(draw, t, accent_rgb=(0, 255, 157))
        
        # Header
        draw_pill_badge(draw, "ENTERPRISE HEALTHTECH SAAS", WIDTH // 2, 130, bg_color=(8, 24, 18, 240), border_color=(0, 255, 157, 230), text_color=(0, 255, 157), show_dot=True, dot_color=(0, 255, 157))
        
        # Headline
        draw.text((WIDTH // 2, 210), "SCALING A HEALTHCARE APP?", font=font_title_lg, fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 275), "CLINICAL-GRADE SAAS & WEB PLATFORMS", font=font_head_md, fill=(0, 255, 157), anchor="mm")
        
        # Phone Mockup with BioPrac scrolling
        frame_idx = min(140, i + 1)
        screen_path = f"/tmp/frames_bioprac/frame_{frame_idx:04d}.jpg"
        if not os.path.exists(screen_path):
            screen_path = "/tmp/frames_bioprac/frame_0001.jpg"
        screen_img = Image.open(screen_path).convert("RGBA")
        
        draw_phone_frame(frame, screen_img, WIDTH // 2, 860, 520, 1020, border_color=(0, 255, 157, 220), browser_url="myhealthprac.vercel.app")
        
        # Under Phone: Live URL pill
        draw_pill_badge(draw, "myhealthprac.vercel.app", WIDTH // 2, 1420, bg_color=(8, 18, 14, 240), border_color=(0, 255, 157, 180), text_color=(200, 245, 220), show_dot=True, dot_color=(0, 255, 157))
        
        # Tags row
        draw_pill_badge(draw, "CLINICAL UI/UX", 270, 1480, border_color=(0, 255, 157, 140), text_color=(0, 255, 157))
        draw_pill_badge(draw, "HIPAA READY", 540, 1480, border_color=(0, 255, 157, 140), text_color=(0, 255, 157))
        draw_pill_badge(draw, "BESPOKE CODE", 810, 1480, border_color=(0, 255, 157, 140), text_color=(0, 255, 157))
        
        # CTA Button & Subtext
        draw_cta_button(draw, t, "TAP BIO TO SCALE • DM 'APP'", WIDTH // 2, 1630, w=860, h=100, cta_color1=(0, 255, 157), cta_color2=(0, 184, 217))
        draw.text((WIDTH // 2, 1720), "ENTERPRISE SOFTWARE & WEB APP ENGINEERING", font=font_cta_sub, fill=(140, 195, 170), anchor="mm")
        
        frame.convert("RGB").save(f"{fdir}/f_{i:04d}.jpg", quality=92)
        
    out_mp4 = os.path.join(OUT_BUMPERS_DIR, "ad_2_bioprac.mp4")
    mux_video_and_audio(f"{fdir}/f_%04d.jpg", "/tmp/bumper_audio/ad_2_bioprac.mp3", out_mp4)

# ─────────────────────────────────────────────────────────────
# 3. BUMPER 3: Autonomous Content Engine (SM Automation)
# ─────────────────────────────────────────────────────────────
def render_bumper_3():
    print("[3/5] Rendering Ad 3: Autonomous Content Engine...")
    fdir = os.path.join(TMP_FRAMES_DIR, "b3")
    os.makedirs(fdir, exist_ok=True)
    
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (12, 10, 6, 255))
        draw = ImageDraw.Draw(frame)
        draw_cyber_background(draw, t, accent_rgb=(255, 229, 0))
        
        # Header
        draw_pill_badge(draw, "AUTONOMOUS MEDIA FLEET", WIDTH // 2, 130, bg_color=(28, 24, 8, 240), border_color=(255, 229, 0, 230), text_color=(255, 229, 0), show_dot=True, dot_color=(255, 229, 0))
        
        # Headline
        draw.text((WIDTH // 2, 210), "THIS VIDEO RAN AUTONOMOUSLY", font=font_title_lg, fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 275), "24/7 CLOUD CONTENT ENGINES FOR BRANDS", font=font_head_md, fill=(255, 229, 0), anchor="mm")
        
        # Tech Dashboard Mockup (HUD Cards)
        card_w, card_h = 880, 800
        cx0 = (WIDTH - card_w) // 2
        cy0 = 400
        cx1 = cx0 + card_w
        cy1 = cy0 + card_h
        
        draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=24, fill=(16, 18, 26, 240), outline=(255, 229, 0, 160), width=2)
        
        # HUD Top Bar
        draw.rounded_rectangle([cx0 + 20, cy0 + 20, cx1 - 20, cy0 + 90], radius=14, fill=(22, 26, 38, 255))
        draw.text((cx0 + 40, cy0 + 55), "AUTONOMOUS SYSTEM STATUS:", font=font_head_sm, fill=(180, 195, 215), anchor="lm")
        # Green Dot
        draw.ellipse([cx1 - 250, cy0 + 49, cx1 - 238, cy0 + 61], fill=(0, 255, 157))
        draw.text((cx1 - 225, cy0 + 55), "100% OPERATIONAL", font=font_head_sm, fill=(0, 255, 157), anchor="lm")
        
        # 4 Stat Boxes
        stats = [
            ("5 CHANNELS", "FLEET SCALE"),
            ("16 SLOTS/DAY", "24/7 CADENCE"),
            ("100% CLOUD", "ZERO LOCAL CRONS"),
            ("HIGH RETENTION", "JUDGE AI GATED")
        ]
        box_w = (card_w - 60) // 2
        box_h = 130
        
        for s_idx, (num, lbl) in enumerate(stats):
            bx0 = cx0 + 20 + (s_idx % 2) * (box_w + 20)
            by0 = cy0 + 110 + (s_idx // 2) * (box_h + 16)
            bx1 = bx0 + box_w
            by1 = by0 + box_h
            
            draw.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=(22, 26, 38, 255), outline=(50, 65, 90, 160), width=1)
            draw.text((bx0 + box_w // 2, by0 + 45), num, font=font_stat_num, fill=(255, 229, 0), anchor="mm")
            draw.text((bx0 + box_w // 2, by0 + 92), lbl, font=font_stat_lbl, fill=(160, 175, 195), anchor="mm")
            
        # Live Pipeline Retention Wave
        py0 = cy0 + 420
        draw.rounded_rectangle([cx0 + 20, py0, cx1 - 20, py0 + 350], radius=16, fill=(12, 14, 22, 255), outline=(40, 50, 75, 140), width=1)
        draw.text((cx0 + 45, py0 + 40), "FLEET VIRAL RETENTION CURVE", font=font_head_sm, fill=(255, 255, 255), anchor="lm")
        draw.text((cx1 - 45, py0 + 40), "AVERAGE 92.4%", font=font_head_sm, fill=(0, 229, 255), anchor="rm")
        
        points = []
        for px_i in range(cx0 + 40, cx1 - 40, 12):
            wave_progress = (px_i - (cx0 + 40)) / (card_w - 80)
            wy = py0 + 260 - int(140 * math.sqrt(wave_progress)) + int(12 * math.sin(wave_progress * 12 + t * 6))
            points.append((px_i, wy))
        if len(points) > 1:
            draw.line(points, fill=(0, 229, 255, 255), width=4)
            
        # Tags row
        draw_pill_badge(draw, "ZERO EDITORS", 270, 1360, border_color=(255, 229, 0, 140), text_color=(255, 229, 0))
        draw_pill_badge(draw, "CLOUD GHA FLEET", 540, 1360, border_color=(255, 229, 0, 140), text_color=(255, 229, 0))
        draw_pill_badge(draw, "AI RESEARCH & SCRIPT", 810, 1360, border_color=(255, 229, 0, 140), text_color=(255, 229, 0))
        
        # CTA Button & Subtext
        draw_cta_button(draw, t, "DM 'FLEET' TO DEPLOY • LINK IN BIO", WIDTH // 2, 1560, w=860, h=100, cta_color1=(255, 229, 0), cta_color2=(255, 85, 0))
        draw.text((WIDTH // 2, 1650), "WE ARCHITECT AUTONOMOUS MEDIA ENGINES", font=font_cta_sub, fill=(200, 190, 140), anchor="mm")
        
        frame.convert("RGB").save(f"{fdir}/f_{i:04d}.jpg", quality=92)
        
    out_mp4 = os.path.join(OUT_BUMPERS_DIR, "ad_3_sm_automation.mp4")
    mux_video_and_audio(f"{fdir}/f_%04d.jpg", "/tmp/bumper_audio/ad_3_sm_automation.mp3", out_mp4)

# ─────────────────────────────────────────────────────────────
# 4. BUMPER 4: Dual Live Portfolio (Dream Heights + BioPrac)
# ─────────────────────────────────────────────────────────────
def render_bumper_4():
    print("[4/5] Rendering Ad 4: Dual Live Portfolio...")
    fdir = os.path.join(TMP_FRAMES_DIR, "b4")
    os.makedirs(fdir, exist_ok=True)
    
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (6, 8, 14, 255))
        draw = ImageDraw.Draw(frame)
        draw_cyber_background(draw, t, accent_rgb=(0, 229, 255))
        
        # Header
        draw_pill_badge(draw, "DUAL CLIENT SHOWCASE", WIDTH // 2, 130, bg_color=(10, 20, 36, 240), border_color=(0, 229, 255, 230), text_color=(0, 229, 255), show_dot=True, dot_color=(0, 255, 157))
        
        # Headline
        draw.text((WIDTH // 2, 210), "TWO LIVE ENTERPRISE BUILDS", font=font_title_lg, fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 275), "REAL CODE • LIVE ON VERCEL • ZERO TEMPLATES", font=font_head_md, fill=(0, 229, 255), anchor="mm")
        
        frame_idx = min(140, i + 1)
        
        # Left: Dream Heights 3D
        sp_dream = f"/tmp/frames_dream/frame_{frame_idx:04d}.jpg"
        if not os.path.exists(sp_dream):
            sp_dream = "/tmp/frames_dream/frame_0001.jpg"
        img_dream = Image.open(sp_dream).convert("RGBA")
        
        # Right: BioPrac SaaS
        sp_bioprac = f"/tmp/frames_bioprac/frame_{frame_idx:04d}.jpg"
        if not os.path.exists(sp_bioprac):
            sp_bioprac = "/tmp/frames_bioprac/frame_0001.jpg"
        img_bioprac = Image.open(sp_bioprac).convert("RGBA")
        
        # Left Phone (angle -2.5°, center 280)
        draw_phone_frame(frame, img_dream, 280, 870, 440, 880, border_color=(0, 229, 255, 200), angle=-2.5, browser_url="dreamheights.app")
        # Right Phone (angle +2.5°, center 800)
        draw_phone_frame(frame, img_bioprac, 800, 870, 440, 880, border_color=(0, 255, 157, 200), angle=2.5, browser_url="myhealthprac.app")
        
        # URL Pills under phones
        draw_pill_badge(draw, "dreamheights-source.vercel.app", 280, 1390, bg_color=(10, 16, 28, 240), border_color=(0, 229, 255, 180), text_color=(190, 225, 255), show_dot=True, dot_color=(0, 229, 255))
        draw_pill_badge(draw, "myhealthprac.vercel.app", 800, 1390, bg_color=(8, 20, 16, 240), border_color=(0, 255, 157, 180), text_color=(190, 245, 220), show_dot=True, dot_color=(0, 255, 157))
        
        # Tags row
        draw_pill_badge(draw, "3D WEBGL ARCHITECTURE", 320, 1460, border_color=(0, 229, 255, 140), text_color=(0, 229, 255))
        draw_pill_badge(draw, "CLINICAL SAAS PLATFORM", 760, 1460, border_color=(0, 255, 157, 140), text_color=(0, 255, 157))
        
        # CTA Button & Subtext
        draw_cta_button(draw, t, "DM 'BUILD' TO WORK WITH US • LINK IN BIO", WIDTH // 2, 1610, w=880, h=100, cta_color1=(0, 229, 255), cta_color2=(121, 40, 202))
        draw.text((WIDTH // 2, 1700), "BESPOKE 3D WEBSITES & HIGH-CONVERSION SAAS", font=font_cta_sub, fill=(150, 175, 205), anchor="mm")
        
        frame.convert("RGB").save(f"{fdir}/f_{i:04d}.jpg", quality=92)
        
    out_mp4 = os.path.join(OUT_BUMPERS_DIR, "ad_4_dual_portfolio.mp4")
    mux_video_and_audio(f"{fdir}/f_%04d.jpg", "/tmp/bumper_audio/ad_4_dual_portfolio.mp3", out_mp4)

# ─────────────────────────────────────────────────────────────
# 5. BUMPER 5: Full-Suite Agency (Websites + AI Fleets)
# ─────────────────────────────────────────────────────────────
def render_bumper_5():
    print("[5/5] Rendering Ad 5: Full-Suite Agency...")
    fdir = os.path.join(TMP_FRAMES_DIR, "b5")
    os.makedirs(fdir, exist_ok=True)
    
    for i in range(TOTAL_FRAMES):
        t = i / FPS
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (8, 10, 16, 255))
        draw = ImageDraw.Draw(frame)
        draw_cyber_background(draw, t, accent_rgb=(0, 242, 254))
        
        # Header
        draw_pill_badge(draw, "ENTERPRISE WEB & CONTENT ENGINE", WIDTH // 2, 130, bg_color=(12, 18, 32, 240), border_color=(0, 242, 254, 230), text_color=(0, 242, 254), show_dot=True, dot_color=(0, 242, 254))
        
        # Headline
        draw.text((WIDTH // 2, 210), "BESPOKE WEBSITES x AI FLEETS", font=font_title_lg, fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 275), "END-TO-END DIGITAL ACQUISITION SUITE", font=font_head_md, fill=(0, 242, 254), anchor="mm")
        
        # Center phone showing Dream Heights 3D
        frame_idx = min(140, i + 1)
        sp_dream = f"/tmp/frames_dream/frame_{frame_idx:04d}.jpg"
        if not os.path.exists(sp_dream):
            sp_dream = "/tmp/frames_dream/frame_0001.jpg"
        screen_img = Image.open(sp_dream).convert("RGBA")
        
        draw_phone_frame(frame, screen_img, WIDTH // 2, 850, 520, 1000, border_color=(0, 242, 254, 220), browser_url="dreamheights-source.vercel.app")
        
        # Floating Feature Pill Left
        draw_pill_badge(draw, "SUB-SECOND SPEED", 220, 680, bg_color=(10, 16, 28, 240), border_color=(0, 242, 254, 200), text_color=(0, 242, 254), show_dot=True, dot_color=(0, 242, 254))
        # Floating Feature Pill Right
        draw_pill_badge(draw, "10X TRAFFIC SCALE", 860, 1020, bg_color=(10, 16, 28, 240), border_color=(255, 229, 0, 200), text_color=(255, 229, 0), show_dot=True, dot_color=(255, 229, 0))
        
        # Live sites indicator
        draw.text((WIDTH // 2, 1420), "FEATURED BUILDS: DREAM HEIGHTS (3D) • BIOPRAC (SAAS)", font=font_head_sm, fill=(180, 215, 245), anchor="mm")
        
        # Tags row
        draw_pill_badge(draw, "CUSTOM WEB PLATFORMS", 320, 1480, border_color=(0, 242, 254, 140), text_color=(0, 242, 254))
        draw_pill_badge(draw, "AUTONOMOUS AI MEDIA", 760, 1480, border_color=(0, 242, 254, 140), text_color=(0, 242, 254))
        
        # CTA Button & Subtext
        draw_cta_button(draw, t, "TAP BIO TO PARTNER • DM 'SCALE'", WIDTH // 2, 1630, w=860, h=100, cta_color1=(0, 242, 254), cta_color2=(79, 172, 254))
        draw.text((WIDTH // 2, 1720), "PARTNER DIRECTLY WITH OUR DEV STUDIO", font=font_cta_sub, fill=(140, 175, 210), anchor="mm")
        
        frame.convert("RGB").save(f"{fdir}/f_{i:04d}.jpg", quality=92)
        
    out_mp4 = os.path.join(OUT_BUMPERS_DIR, "ad_5_agency_fullstack.mp4")
    mux_video_and_audio(f"{fdir}/f_%04d.jpg", "/tmp/bumper_audio/ad_5_agency_fullstack.mp3", out_mp4)

def main():
    print("=== STARTING REFINED INTERACTIVE BUMPERS COMPOSITION ===")
    render_bumper_1()
    render_bumper_2()
    render_bumper_3()
    render_bumper_4()
    render_bumper_5()
    print("=== ALL 5 INTERACTIVE BUMPERS COMPOSITED AND SAVED TO ASSETS/BUMPERS ===")

if __name__ == "__main__":
    main()
