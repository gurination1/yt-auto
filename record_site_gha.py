import asyncio
import os
import sys
import glob
import subprocess
from playwright.async_api import async_playwright

async def record():
    display = os.environ.get('DISPLAY', ':99')
    url = os.environ.get('TARGET_URL', 'https://dreamheights-source.vercel.app/')
    raw_mp4 = '/tmp/raw_x11grab.mp4'
    output_mp4 = '/tmp/dreamheights_cloud_60fps.mp4'

    print("==================================================")
    print("🎬 Starting 60FPS Cloud Screen Recording")
    print(f"   Target URL: {url}")
    print(f"   X11 Display: {display}")
    print("==================================================")

    # 1. Start FFmpeg x11grab at true 60 FPS
    print("1. Launching FFmpeg x11grab (60fps lossless capture from X11 buffer)...")
    ffmpeg_cmd = [
        'ffmpeg',
        '-video_size', '1920x1080',
        '-framerate', '60',
        '-f', 'x11grab',
        '-draw_mouse', '0',
        '-i', f'{display}.0',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '15',
        '-pix_fmt', 'yuv420p',
        raw_mp4,
        '-y'
    ]
    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )

    # Allow FFmpeg to initialize the framebuffer grabber
    await asyncio.sleep(0.5)

    # 2. Launch Chromium in Headful Kiosk mode on X11
    print("2. Launching Headful Chromium on X11 (1920x1080 Kiosk)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--window-size=1920,1080',
                '--window-position=0,0',
                '--start-fullscreen',
                '--kiosk',
                '--disable-infobars',
                '--disable-session-crashed-bubble',
                '--hide-scrollbars',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--enable-gpu-rasterization',
                '--ignore-gpu-blocklist',
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1
        )

        # Pre-set cookie preference to prevent popup overlay
        await context.add_init_script("""
        (() => {
            try {
                localStorage.setItem('cookies', 'accepted');
            } catch(e) {}
        })()
        """)

        page = await context.new_page()

        # Set dark background to prevent any white flash
        await page.goto("data:text/html,<body style='background:#050505;margin:0;'></body>")
        await asyncio.sleep(0.3)

        print(f"3. Navigating to {url} to capture preloader...")
        await page.goto(url, wait_until='domcontentloaded')

        print("4. Preloader running! Waiting for preloader animation to complete naturally...")
        try:
            # Wait for data-preloader to finish its GSAP arch animation and hide
            await page.wait_for_function('''() => {
                const p = document.querySelector("[data-preloader]");
                if (!p) return true;
                const style = window.getComputedStyle(p);
                return style.display === "none" || style.opacity === "0" || style.visibility === "hidden";
            }''', timeout=30000)
            print("   ✅ Preloader animation finished! Hero section revealed.")
        except Exception as e:
            print("   ⚠️ Preloader wait warning:", e)

        print("5. Holding on Hero view (2.0s)...")
        await asyncio.sleep(2.0)

        print("6. Scrolling down smoothly via native Lenis (0 -> 5500px in 6.0s)...")
        await page.evaluate('''() => {
            return new Promise((resolve) => {
                if (window.lenis) {
                    window.lenis.scrollTo(5500, {
                        duration: 6.0,
                        easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
                    });
                    setTimeout(resolve, 6200);
                } else {
                    window.scrollTo({ top: 5500, behavior: 'smooth' });
                    setTimeout(resolve, 6200);
                }
            });
        }''')

        print("7. Pausing on architectural showcase section (2.0s)...")
        await asyncio.sleep(2.0)

        print("8. Scrolling back to Hero via native Lenis (5500px -> 0 in 4.5s)...")
        await page.evaluate('''() => {
            return new Promise((resolve) => {
                if (window.lenis) {
                    window.lenis.scrollTo(0, {
                        duration: 4.5,
                        easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
                    });
                    setTimeout(resolve, 4800);
                } else {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    setTimeout(resolve, 4800);
                }
            });
        }''')

        print("9. Settle on Hero view (1.5s)...")
        await asyncio.sleep(1.5)

        print("10. Closing browser...")
        await context.close()
        await browser.close()

    print("11. Stopping FFmpeg capture...")
    try:
        ffmpeg_proc.stdin.write(b'q')
        ffmpeg_proc.stdin.flush()
        ffmpeg_proc.wait(timeout=10)
    except Exception as e:
        print("   Terminating FFmpeg:", e)
        ffmpeg_proc.terminate()
        ffmpeg_proc.wait(timeout=5)

    if not os.path.exists(raw_mp4):
        raise RuntimeError("Raw capture video was not generated!")

    print(f"12. Transcoding to ultra-high-bitrate 60fps MP4: {output_mp4} ...")
    subprocess.run([
        'ffmpeg', '-i', raw_mp4,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '16',
        '-r', '60',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_mp4, '-y'
    ], check=True)

    print("=== Uploading to catbox.moe ===")
    try:
        res = subprocess.run([
            'curl', '-s', '-A', 'Mozilla/5.0',
            '-F', 'reqtype=fileupload',
            '-F', f'fileToUpload=@{output_mp4}',
            'https://catbox.moe/user/api.php'
        ], capture_output=True, text=True, check=True)
        print("CATBOX_URL:", res.stdout.strip())
    except Exception as e:
        print("Catbox upload failed:", e)

    print("=== Uploading to tmpfiles.org ===")
    try:
        res = subprocess.run([
            'curl', '-s', '-F', f'file=@{output_mp4}',
            'https://tmpfiles.org/api/v1/upload'
        ], capture_output=True, text=True, check=True)
        print("TMPFILES_RES:", res.stdout.strip())
    except Exception as e:
        print("Tmpfiles upload failed:", e)

if __name__ == '__main__':
    asyncio.run(record())
