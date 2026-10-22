#!/usr/bin/env python3
"""One-off QA for the native-app promo (replaces the old A2HS hint).

Serves docs/ locally and checks, per context:
  iPhone Safari UA  -> apple-itunes-app meta present, promo visible w/ App Store link, no old hint
  Android Chrome UA -> promo visible w/ Play link, manifest related_applications
  Capacitor native  -> NO promo (window.Capacitor set before load)
  standalone PWA    -> NO promo (display-mode emulated via CDP)
  Desktop           -> NO promo, no change

Async API on purpose: the sync API's greenlet crashes on free-threaded 3.14t.
"""
import asyncio, http.server, json, threading, functools, os, sys
from playwright.async_api import async_playwright

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
PORT = 8477
# YS_BASE=https://yardscout.io/index.html runs the same suite against prod.
BASE = os.environ.get("YS_BASE") or f"http://127.0.0.1:{PORT}/index.html"
LOCAL = "127.0.0.1" in BASE
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "_app_promo_shots" if LOCAL else "_app_promo_shots_prod")
os.makedirs(SHOTS, exist_ok=True)

IPHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")
ANDROID_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36")

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, detail)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        async def new_page(ua=None, viewport=None, init_script=None):
            ctx = await browser.new_context(
                user_agent=ua,
                viewport=viewport or {"width": 390, "height": 844},
                is_mobile=bool(ua and "Mobile" in ua),
            )
            page = await ctx.new_page()
            if init_script:
                await page.add_init_script(init_script)
            return ctx, page

        # ---- 1. iPhone Safari UA ----
        ctx, page = await new_page(ua=IPHONE_UA)
        await page.goto(BASE, wait_until="networkidle")
        meta = await page.get_attribute('meta[name="apple-itunes-app"]', "content")
        check("iphone: apple-itunes-app meta", meta == "app-id=6817126581", repr(meta))
        check("iphone: old #install-hint gone", await page.query_selector("#install-hint") is None)
        promo = await page.query_selector("#app-promo")
        check("iphone: promo visible", promo and await promo.is_visible())
        href = await page.get_attribute("#app-promo-link", "href")
        check("iphone: App Store link", href and "apps.apple.com" in href and "6817126581" in href, href)
        txt = (await promo.inner_text()).lower() if promo else ""
        check("iphone: no homescreen copy", "home screen" not in txt)
        await page.screenshot(path=os.path.join(SHOTS, "iphone.png"))
        await page.click("#app-promo-close")
        check("iphone: hidden after dismiss", not await page.is_visible("#app-promo"))
        await page.reload(wait_until="networkidle")
        check("iphone: stays dismissed after reload", not await page.is_visible("#app-promo"))
        await ctx.close()

        # ---- 2. Android Chrome UA ----
        ctx, page = await new_page(ua=ANDROID_UA)
        await page.goto(BASE, wait_until="networkidle")
        check("android: promo visible", await page.is_visible("#app-promo"))
        href = await page.get_attribute("#app-promo-link", "href")
        check("android: Play link", href == "https://play.google.com/store/apps/details?id=io.yardscout.app", href)
        label = await page.inner_text("#app-promo-link")
        check("android: label says Google Play", "Google Play" in label, label)
        manifest = json.loads(await page.evaluate("fetch('manifest.webmanifest').then(r=>r.text())"))
        ra = manifest.get("related_applications", [])
        play = [a for a in ra if a.get("platform") == "play"]
        check("android: manifest prefer_related_applications", manifest.get("prefer_related_applications") is True)
        check("android: manifest play id", bool(play) and play[0].get("id") == "io.yardscout.app", json.dumps(play))
        await page.screenshot(path=os.path.join(SHOTS, "android.png"))
        await ctx.close()

        # ---- 3. Capacitor-simulated native (iPhone UA + window.Capacitor before load) ----
        ctx, page = await new_page(ua=IPHONE_UA, init_script="""
            window.Capacitor = {
              isNativePlatform: () => true,
              getPlatform: () => 'ios',
              Plugins: {}
            };
        """)
        await page.goto(BASE, wait_until="networkidle")
        check("capacitor: promo NOT visible", not await page.is_visible("#app-promo"))
        await page.goto(BASE + "?appbanner=ios", wait_until="networkidle")
        check("capacitor: promo NOT visible even forced", not await page.is_visible("#app-promo"))
        await page.screenshot(path=os.path.join(SHOTS, "capacitor.png"))
        await ctx.close()

        # ---- 4. Standalone display-mode (installed PWA) ----
        # CDP media emulation proved flaky headless; stub the exact query the
        # app checks (plus navigator.standalone, the iOS Safari signal).
        ctx, page = await new_page(ua=IPHONE_UA, init_script="""
            const origMatchMedia = window.matchMedia.bind(window);
            window.matchMedia = (q) => q === '(display-mode: standalone)'
              ? { matches: true, media: q, addEventListener(){}, removeEventListener(){}, addListener(){}, removeListener(){} }
              : origMatchMedia(q);
            Object.defineProperty(navigator, 'standalone', { get: () => true });
        """)
        await page.goto(BASE, wait_until="networkidle")
        dm = await page.evaluate("window.matchMedia('(display-mode: standalone)').matches")
        check("standalone: display-mode emulated", dm)
        check("standalone: promo NOT visible", not await page.is_visible("#app-promo"))
        await page.screenshot(path=os.path.join(SHOTS, "standalone.png"))
        await ctx.close()

        # ---- 5. Desktop ----
        ctx, page = await new_page(viewport={"width": 1280, "height": 800})
        await page.goto(BASE, wait_until="networkidle")
        check("desktop: promo NOT visible", not await page.is_visible("#app-promo"))
        check("desktop: header renders", await page.is_visible("header"))
        await page.screenshot(path=os.path.join(SHOTS, "desktop.png"))
        await ctx.close()

        await browser.close()

httpd = None
if LOCAL:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
asyncio.run(main())
if httpd:
    httpd.shutdown()
fails = [r for r in results if not r[1]]
print(f"\n{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
