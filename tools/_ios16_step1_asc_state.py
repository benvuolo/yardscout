"""ios next release step 1: open ASC, check the app's current version states."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        if "appstoreconnect" not in page.url:
            ctx = browser.contexts[0]
            page = await ctx.new_page()
        await page.goto("https://appstoreconnect.apple.com/apps", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "01_asc_apps")
        body = await page.inner_text("body")
        print("BODY:\n", body[:1500])

asyncio.run(main())
