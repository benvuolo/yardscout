"""Open the default-listing editor and dump every populated text field."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

EDIT = ("https://play.google.com/console/u/0/developers/9052149026359320771/"
        "app/4975171430765358175/store-listings/default/edit")


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings")
        await page.goto(EDIT, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector("textarea", timeout=90000)
        await page.wait_for_timeout(4000)
        print("URL:", page.url)
        await shot(page, "35-editor")
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        print("text boxes:", n)
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v:
                print(f"--- box {i} ({len(v)} chars) ---")
                print(v)
                print()

asyncio.run(main())
