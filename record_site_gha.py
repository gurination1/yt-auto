import asyncio
import os
import glob
import subprocess
from playwright.async_api import async_playwright

async def run():
    rec_dir = '/tmp/recordings'
    os.makedirs(rec_dir, exist_ok=True)

    print("Launching Chromium on GitHub Actions runner...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--enable-webgl',
                '--ignore-gpu-blocklist',
                '--use-gl=angle',
                '--use-angle=swiftshader',
                '--window-size=1920,1080'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=rec_dir,
            record_video_size={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        url = os.environ.get('TARGET_URL', 'https://dreamheights-source.vercel.app/')
        print(f"1. Navigating to {url} ...")
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await asyncio.sleep(2.5)

        print("2. Scrubbing overlays and initializing Lenis...")
        await page.evaluate('''() => {
            document.querySelectorAll('[data-cookie], .cookie, [class*="cookie"], [data-preloader], [data-master-preloader]').forEach(e => e.remove());
            document.documentElement.style.overflow = 'auto';
            document.body.style.overflow = 'auto';
            document.body.style.paddingRight = '';
            if (window.lenis) {
                window.lenis.start();
                window.lenis.scrollTo(0, { immediate: true });
            }
        }''')

        print("3. Capturing Hero view (2.5s)...")
        await asyncio.sleep(2.5)

        print("4. Executing smooth dynamic scroll down (0 -> 9500px in 7.0s)...")
        await page.evaluate('''() => {
            return new Promise((resolve) => {
                const targetY = 9500;
                const duration = 7000;
                const startY = window.scrollY;
                let start = null;

                function step(timestamp) {
                    if (!start) start = timestamp;
                    const elapsed = timestamp - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const ease = progress < 0.5 
                        ? 2 * progress * progress 
                        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                    
                    const current = startY + targetY * ease;
                    if (window.lenis) {
                        window.lenis.scrollTo(current, { immediate: true });
                    } else {
                        window.scrollTo(0, current);
                    }

                    if (progress < 1) {
                        requestAnimationFrame(step);
                    } else {
                        resolve();
                    }
                }
                requestAnimationFrame(step);
            });
        }''')

        print("5. Pausing on architectural amenities section (2.0s)...")
        await asyncio.sleep(2.0)

        print("6. Executing smooth dynamic return scroll (9500px -> 0 in 4.5s)...")
        await page.evaluate('''() => {
            return new Promise((resolve) => {
                const startY = window.scrollY;
                const duration = 4500;
                let start = null;

                function step(timestamp) {
                    if (!start) start = timestamp;
                    const elapsed = timestamp - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const ease = progress < 0.5 
                        ? 2 * progress * progress 
                        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                    
                    const current = startY * (1 - ease);
                    if (window.lenis) {
                        window.lenis.scrollTo(current, { immediate: true });
                    } else {
                        window.scrollTo(0, current);
                    }

                    if (progress < 1) {
                        requestAnimationFrame(step);
                    } else {
                        resolve();
                    }
                }
                requestAnimationFrame(step);
            });
        }''')

        print("7. Settle on Hero (2.0s)...")
        await asyncio.sleep(2.0)

        print("8. Closing context to flush video...")
        await context.close()
        await browser.close()

    webms = glob.glob(os.path.join(rec_dir, '*.webm'))
    if not webms:
        raise RuntimeError("No recorded video found!")
    
    input_webm = webms[0]
    output_mp4 = '/tmp/dreamheights_cloud_60fps.mp4'
    print(f"Encoding {input_webm} to high-bitrate 60fps MP4: {output_mp4} ...")
    subprocess.run([
        'ffmpeg', '-i', input_webm,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '17',
        '-r', '60',
        '-pix_fmt', 'yuv420p',
        output_mp4, '-y'
    ], check=True)

    print("=== Uploading to catbox.moe ===")
    try:
        res = subprocess.run([
            'curl', '-s', '-F', 'reqtype=fileupload',
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
    asyncio.run(run())
