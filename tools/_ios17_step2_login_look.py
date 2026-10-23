"""ios17 step 2: inspect the plain ASC login tab state, then probe a fresh /apps load."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        for pg in ctx.pages:
            if pg.url.rstrip("/").endswith("appstoreconnect.apple.com/login"):
                await ys_cdp.shot(pg, "02_login_tab")
                body = await pg.inner_text("body")
                print("LOGIN TAB BODY:\n", body[:600])
                break
        # fresh probe
        page = await ctx.new_page()
        await page.goto("https://appstoreconnect.apple.com/apps", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        print("PROBE URL:", page.url)
        await ys_cdp.shot(page, "02b_fresh_probe")
        body = await page.inner_text("body")
        print("PROBE BODY:\n", body[:500])
        await page.close()

asyncio.run(main())
