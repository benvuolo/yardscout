"""Step 2: open the internal testing track directly."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(APP + "/tracks/internal-testing", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "02_internal_testing")
        body = await page.inner_text("body")
        print("BODY_SNIPPET:\n", body[:3000])

asyncio.run(main())
