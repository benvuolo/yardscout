"""Open Store listings -> default listing editor (same path as step04),
then dump the current short/full description values."""
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
        await page.goto(APP + "/store-listings", wait_until="domcontentloaded",
                        timeout=90000)
        await page.wait_for_timeout(7000)
        print("URL:", page.url)
        await shot(page, "32-store-listings")
        links = await page.evaluate("""() =>
            [...document.querySelectorAll('a[href]')]
              .map(a => a.href)
              .filter(h => /store-listings\\/.+/.test(h))""")
        print("listing links:", links)
        edit = next((h for h in links if "edit" in h), links[0] if links else None)
        assert edit, "no listing edit link found"
        await page.goto(edit, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(9000)
        print("editor URL:", page.url)
        await shot(page, "32-editor-top")
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        print("text boxes:", n)
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v:
                print(f"--- box {i} ---")
                print(v[:2500])

asyncio.run(main())
