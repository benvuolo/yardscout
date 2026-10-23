#!/usr/bin/env python3
"""One-off QA for the official store badges (header pair + footer pair).

Serves docs/ locally (or prod via YS_BASE) and checks, per context:
  Desktop 1280       -> header badges visible + correct links, footer badges visible
  Tablet 834 (iPad)  -> promo banner showing: header badges SUPPRESSED;
                        after dismissal + reload: header badges visible
  Phone 390 (iPhone) -> header badges hidden (CSS width gate), footer badges
                        visible, promo banner stays the primary mobile promo
  Capacitor native   -> NO badges anywhere (window.Capacitor set before load)
  standalone PWA     -> footer badges visible, NO header badges

Async API on purpose: the sync API's greenlet crashes on free-threaded 3.14t.
"""
import asyncio, http.server, threading, functools, os, sys
from playwright.async_api import async_playwright

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
PORT = 8478
# YS_BASE=https://yardscout.io/index.html runs the same suite against prod.
BASE = os.environ.get("YS_BASE") or f"http://127.0.0.1:{PORT}/index.html"
LOCAL = "127.0.0.1" in BASE
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "_store_badge_shots" if LOCAL else "_store_badge_shots_prod")
os.makedirs(SHOTS, exist_ok=True)

IPHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")
IPAD_UA = ("Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
           "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")

APP_STORE = "https://apps.apple.com/app/id6817126581"
PLAY = "https://play.google.com/store/apps/details?id=io.yardscout.app"

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

        # ---- 1. Desktop 1280 ----
        ctx, page = await new_page(viewport={"width": 1280, "height": 800})
        await page.goto(BASE, wait_until="networkidle")
        check("desktop: header badges visible", await page.is_visible("#header-badges"))
        hrefs = await page.eval_on_selector_all("#header-badges a", "els => els.map(e => e.href)")
        check("desktop: header App Store link", APP_STORE in hrefs, str(hrefs))
        check("desktop: header Play link", PLAY in hrefs, str(hrefs))
        # badge art actually loaded (not broken images)
        ok = await page.evaluate("[...document.querySelectorAll('.store-badges img')].every(i => i.complete && i.naturalWidth > 0)")
        check("desktop: badge art loaded", ok)
        # visible heights roughly match (Apple 40px vs Play visible 168/250*59.5 ~= 40px)
        ih = await page.evaluate("document.querySelector('#header-badges .badge-ios').getBoundingClientRect().height")
        check("desktop: Apple badge >= 40px (guideline min)", ih >= 39.5, f"{ih:.1f}px")
        check("desktop: footer badges visible", await page.is_visible(".footer-badges"))
        legal = await page.inner_text(".badge-legal")
        check("desktop: trademark attribution present", "Google LLC" in legal and "Apple Inc" in legal)
        check("desktop: promo banner NOT visible", not await page.is_visible("#app-promo"))
        await page.screenshot(path=os.path.join(SHOTS, "desktop_header.png"))
        await page.locator(".app-footer").scroll_into_view_if_needed()
        await page.screenshot(path=os.path.join(SHOTS, "desktop_footer.png"))
        await ctx.close()

        # ---- 2. Tablet 834 (iPad UA — mobile banner exists at this width) ----
        ctx, page = await new_page(ua=IPAD_UA, viewport={"width": 834, "height": 1194})
        await page.goto(BASE, wait_until="networkidle")
        check("tablet: promo banner visible (primary promo)", await page.is_visible("#app-promo"))
        check("tablet: header badges suppressed while banner shows", not await page.is_visible("#header-badges"))
        check("tablet: footer badges visible anyway", await page.is_visible(".footer-badges"))
        await page.screenshot(path=os.path.join(SHOTS, "tablet_banner.png"))
        await page.click("#app-promo-close")
        await page.reload(wait_until="networkidle")
        check("tablet: header badges appear after banner dismissed", await page.is_visible("#header-badges"))
        await page.screenshot(path=os.path.join(SHOTS, "tablet_after_dismiss.png"))
        await ctx.close()

        # ---- 3. Phone 390 (iPhone UA) ----
        ctx, page = await new_page(ua=IPHONE_UA)
        await page.goto(BASE, wait_until="networkidle")
        check("phone: promo banner visible (primary promo)", await page.is_visible("#app-promo"))
        check("phone: header badges hidden", not await page.is_visible("#header-badges"))
        check("phone: footer badges visible", await page.is_visible(".footer-badges"))
        await page.screenshot(path=os.path.join(SHOTS, "phone.png"))
        await page.click("#app-promo-close")
        await page.reload(wait_until="networkidle")
        check("phone: header badges still hidden after dismissal (width gate)",
              not await page.is_visible("#header-badges"))
        await page.locator(".app-footer").scroll_into_view_if_needed()
        await page.screenshot(path=os.path.join(SHOTS, "phone_footer.png"))
        await ctx.close()

        # ---- 4. Capacitor-simulated native ----
        ctx, page = await new_page(ua=IPHONE_UA, viewport={"width": 1280, "height": 800}, init_script="""
            window.Capacitor = {
              isNativePlatform: () => true,
              getPlatform: () => 'ios',
              Plugins: {}
            };
        """)
        await page.goto(BASE, wait_until="networkidle")
        check("capacitor: header badges NOT visible", not await page.is_visible("#header-badges"))
        check("capacitor: footer badges NOT visible", not await page.is_visible(".footer-badges"))
        check("capacitor: footer get-app block NOT visible", not await page.is_visible("#footer-get-app .store-badges"))
        await page.screenshot(path=os.path.join(SHOTS, "capacitor.png"))
        await ctx.close()

        # ---- 5. Standalone display-mode (installed PWA) ----
        ctx, page = await new_page(ua=IPHONE_UA, viewport={"width": 1024, "height": 768}, init_script="""
            const origMatchMedia = window.matchMedia.bind(window);
            window.matchMedia = (q) => q === '(display-mode: standalone)'
              ? { matches: true, media: q, addEventListener(){}, removeEventListener(){}, addListener(){}, removeListener(){} }
              : origMatchMedia(q);
            Object.defineProperty(navigator, 'standalone', { get: () => true });
        """)
        await page.goto(BASE, wait_until="networkidle")
        check("standalone: header badges NOT visible (no header push)", not await page.is_visible("#header-badges"))
        check("standalone: footer badges visible", await page.is_visible(".footer-badges"))
        await page.locator(".app-footer").scroll_into_view_if_needed()
        await page.screenshot(path=os.path.join(SHOTS, "standalone_footer.png"))
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
