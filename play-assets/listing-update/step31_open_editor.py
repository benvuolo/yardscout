"""Open the main store listing editor and dump the current short/full
description values so the needs-first edit can be made surgically."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

EDIT = ("https://play.google.com/console/u/0/developers/9052149026359320771/"
        "app/4975171430765358175/main-store-listing")


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        await page.goto(EDIT, wait_until="domcontentloaded")
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await shot(page, "31-editor-top")
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        print("text boxes:", n)
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v:
                print(f"--- box {i} ---")
                print(v[:2500])

asyncio.run(main())
