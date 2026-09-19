import asyncio
import os
import sys
import glob
import json
import subprocess
from playwright.async_api import async_playwright

async def record_site(url, site_name, display=":99"):
    raw_mp4 = f"/tmp/raw_{site_name}.mp4"
    output_mp4 = f"/tmp/{site_name}_cloud_60fps.mp4"

    print("==================================================")
    print(f"🎬 Starting 60FPS Cloud Screen Recording: {site_name.upper()}")
    print(f"   Target URL: {url}")
    print(f"   Display: {display}")
    print("==================================================")

    # 1. Launch FFmpeg x11grab at true 60 FPS
    ffmpeg_cmd = [
        'ffmpeg',
        '-video_size', '1920x1080',
        '-framerate', '60',
        '-f', 'x11grab',
        '-draw_mouse', '0',
        '-i', f'{display}.0',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '14',
        '-pix_fmt', 'yuv420p',
        raw_mp4,
        '-y'
    ]
    print(f"1. Starting FFmpeg x11grab for {site_name}...")
    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    await asyncio.sleep(0.6)

    # 2. Launch Chromium in borderless App mode (--app=URL)
    print("2. Launching Chromium in borderless App mode (zero URL/tab bar)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                f'--app={url}',
                '--window-size=1920,1080',
                '--window-position=0,0',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--start-fullscreen',
                '--hide-scrollbars',
                '--enable-gpu-rasterization',
                '--ignore-gpu-blocklist',
                '--enable-features=VaapiVideoDecoder,CanvasOopRasterization,UseSkiaRenderer',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
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

        # Get existing page created by --app
        pages = context.pages
        page = pages[0] if pages else await context.new_page()

        print(f"3. Navigating to {url} ...")
        await page.goto(url, wait_until='domcontentloaded')

        # 4. Handle preloader if site has one (e.g. Dream Heights)
        has_preloader = await page.evaluate('() => document.querySelector("[data-preloader]") != null')
        if has_preloader:
            print("4. Preloader detected! Allowing full luxury preloader animation to play...")
            try:
                # Wait for preloader to animate progress bar and arch split, then hide
                await page.wait_for_function('''() => {
                    const p = document.querySelector("[data-preloader]");
                    if (!p) return true;
                    const style = window.getComputedStyle(p);
                    return style.display === "none" || style.visibility === "hidden";
                }''', timeout=25000)
                print("   ✅ Preloader completed and dissolved naturally!")
            except Exception as e:
                print("   ⚠️ Preloader wait exception:", e)
        else:
            print("4. No preloader on site. Proceeding to Hero hold...")
            await asyncio.sleep(1.0)

        print("5. Holding on Hero section (2.5s)...")
        await asyncio.sleep(2.5)

        # 6. Measure total scroll height and scroll smoothly to the footer
        print("6. Calculating full page height and scrolling through ALL sections to footer...")
        scroll_info = await page.evaluate('''() => {
            const total = document.documentElement.scrollHeight - window.innerHeight;
            return { total: Math.max(total, 1000) };
        }''')
        total_scroll = scroll_info['total']
        
        # Calculate duration based on total height: ~650 px/s for cinematic smooth pacing
        scroll_down_duration = max(20.0, min(38.0, total_scroll / 650.0))
        print(f"   Total scrollable height: {total_scroll}px. Downward scroll duration: {scroll_down_duration:.1f}s")

        await page.evaluate(f'''() => {{
            return new Promise((resolve) => {{
                const target = {total_scroll};
                const dur = {scroll_down_duration};
                if (window.lenis) {{
                    window.lenis.scrollTo(target, {{
                        duration: dur,
                        easing: (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
                    }});
                }} else {{
                    window.scrollTo({{ top: target, behavior: 'smooth' }});
                }}
                setTimeout(resolve, Math.round(dur * 1000 + 400));
            }});
        }}''')

        print("7. Pausing at bottom / Footer section (2.5s)...")
        await asyncio.sleep(2.5)

        # 8. Smooth return scroll back to Hero
        return_duration = max(8.0, min(14.0, total_scroll / 1800.0))
        print(f"8. Scrolling back up to Hero ({return_duration:.1f}s)...")
        await page.evaluate(f'''() => {{
            return new Promise((resolve) => {{
                const dur = {return_duration};
                if (window.lenis) {{
                    window.lenis.scrollTo(0, {{
                        duration: dur,
                        easing: (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
                    }});
                }} else {{
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }}
                setTimeout(resolve, Math.round(dur * 1000 + 400));
            }});
        }}''')

        print("9. Settling on Hero section (2.0s)...")
        await asyncio.sleep(2.0)

        print("10. Closing browser window...")
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
        raise RuntimeError(f"Raw video capture failed for {site_name}!")

    print(f"12. Transcoding to ultra-high-bitrate 60fps MP4: {output_mp4} ...")
    subprocess.run([
        'ffmpeg', '-i', raw_mp4,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '16',
        '-r', '60',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_mp4, '-y'
    ], check=True)

    # Upload to tmpfiles.org
    print(f"=== Uploading {site_name} to tmpfiles.org ===")
    tmpfiles_url = None
    try:
        res = subprocess.run([
            'curl', '-s', '-F', f'file=@{output_mp4}',
            'https://tmpfiles.org/api/v1/upload'
        ], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        raw_url = data.get("data", {}).get("url", "")
        if raw_url:
            # Convert https://tmpfiles.org/XXXX/name.mp4 -> https://tmpfiles.org/dl/XXXX/name.mp4
            tmpfiles_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            print(f"✅ {site_name.upper()} TMPFILES STREAM URL: {tmpfiles_url}")
    except Exception as e:
        print(f"Tmpfiles upload failed for {site_name}:", e)

    return output_mp4, tmpfiles_url


async def main():
    display = os.environ.get('DISPLAY', ':99')
    target = os.environ.get('TARGET_SITE', 'both')  # 'dreamheights', 'bioprac', or 'both'

    sites = []
    if target in ('dreamheights', 'both'):
        sites.append(('https://dreamheights-source.vercel.app/', 'dreamheights'))
    if target in ('bioprac', 'both'):
        sites.append(('https://gurination1.github.io/bioprac/', 'bioprac'))

    results = {}
    for url, name in sites:
        out_file, stream_url = await record_site(url, name, display=display)
        results[name] = {
            'file': out_file,
            'url': stream_url
        }

    print("\n==================================================")
    print("🎉 ALL SCREEN RECORDINGS COMPLETED SUCCESSFULLY!")
    print("==================================================")
    for name, data in results.items():
        print(f"• {name.upper()}: {data['url']}")
    print("==================================================")

if __name__ == '__main__':
    asyncio.run(main())
