"""Pick the YardScout LLC developer account, open the app, then the
publishing overview — screenshot each hop so review state is visible."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        await page.click("text=YardScout LLC")
        await page.wait_for_timeout(6000)
        print("after account pick:", page.url)
        await shot(page, "29-after-account")
        # App row (single-app account): click the YardScout app entry.
        app = page.locator("text=YardScout").first
        if await app.count():
            await app.click()
            await page.wait_for_timeout(6000)
        print("after app pick:", page.url)
        await shot(page, "29-app-dashboard")

asyncio.run(main())
