"""Step 1: open Play Console internal testing page for YardScout."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
URL = "https://play.google.com/console/u/0/developers/9052149026359320771/app-list"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(URL)
        await page.wait_for_load_state("networkidle", timeout=45000)
        await ys_cdp.shot(page, "01_app_list")
        print("URL:", page.url)
        print("TITLE:", await page.title())

asyncio.run(main())
