"""Retry: wait for the store-listings page to actually render, then enter
the main listing editor and dump description fields."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

APP = ("https://play.google.com/console/u/0/developers/9052149026359320771/"
       "app/4975171430765358175")


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        if "store-listings" not in page.url:
            await page.goto(APP + "/store-listings",
                            wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector("text=Main store listing", timeout=60000)
        await page.wait_for_timeout(3000)
        await shot(page, "33-store-listings")
        await page.click("text=Main store listing")
        await page.wait_for_timeout(4000)
        try:
            await page.wait_for_selector("textarea", timeout=60000)
        except Exception:
            pass
        await page.wait_for_timeout(4000)
        print("editor URL:", page.url)
        await shot(page, "33-editor-top")
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        print("text boxes:", n)
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v:
                print(f"--- box {i} ---")
                print(v[:2500])

asyncio.run(main())
