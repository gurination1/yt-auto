import asyncio
import os
import subprocess
from playwright.async_api import async_playwright

REC_DIR = "/tmp/site_recordings"
os.makedirs(REC_DIR, exist_ok=True)

async def record_site(url: str, output_name: str, duration_sec: float = 6.0, scroll_max: int = 1600):
    print(f"[*] Starting recording for {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--disable-notifications"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 480, "height": 960},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            record_video_dir=REC_DIR,
            record_video_size={"width": 480, "height": 960}
        )
        page = await context.new_page()
        print(f"[*] Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"[!] Navigation error: {e}, waiting for domcontentloaded...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Allow initial animations/3D canvas to warm up
        await asyncio.sleep(1.5)

        # Smooth easing scroll
        fps = 30
        total_frames = int(duration_sec * fps)
        for f in range(total_frames):
            progress = f / total_frames
            # smooth sinusoidal easeInOut
            import math
            ease = 0.5 * (1 - math.cos(progress * math.pi))
            curr_y = int(ease * scroll_max)
            await page.evaluate(f"window.scrollTo(0, {curr_y})")
            await asyncio.sleep(1 / fps)

        await asyncio.sleep(0.5)
        await page.close()
        video_path = await page.video.path()
        await context.close()
        await browser.close()

        final_mp4 = os.path.join(REC_DIR, output_name)
        # Convert webm to h264 mp4 30fps
        cmd = [
            "/data/data/com.termux/files/usr/bin/ffmpeg", "-y",
            "-i", video_path,
            "-vf", "fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            final_mp4
        ]
        subprocess.run(cmd, check=True)
        print(f"[✓] Saved recording: {final_mp4} ({os.path.getsize(final_mp4)} bytes)")
        return final_mp4

async def main():
    dream_mp4 = await record_site("https://dreamheights-source.vercel.app", "rec_dreamheights.mp4", duration_sec=5.0, scroll_max=1800)
    bioprac_mp4 = await record_site("https://myhealthprac.vercel.app", "rec_bioprac.mp4", duration_sec=5.0, scroll_max=1500)
    print("\nAll site recordings complete!")

if __name__ == "__main__":
    asyncio.run(main())
