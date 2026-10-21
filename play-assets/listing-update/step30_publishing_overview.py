"""Open the publishing overview directly and dump its text + screenshot,
to see whether this morning's slide-5 submission is still in review."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        await page.goto(APP + "/publishing", wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await shot(page, "30-publishing-overview")
        body = await page.inner_text("body")
        # print the interesting middle (skip global nav noise)
        print(body[:4000])

asyncio.run(main())
