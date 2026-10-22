"""vc8 step 1b: screenshot whatever the console page shows now."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc8-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "01b_look")
        print("URL:", page.url)
        print("TITLE:", await page.title())
        body = await page.inner_text("body")
        print("BODY HEAD:\n", body[:800])

asyncio.run(main())
