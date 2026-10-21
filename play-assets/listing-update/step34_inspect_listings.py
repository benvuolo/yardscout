"""Inspect the rendered store-listings page: screenshot + visible links."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings")
        print("URL:", page.url)
        await shot(page, "34-listings-state")
        rows = await page.evaluate("""() =>
            [...document.querySelectorAll('a[href]')]
              .filter(a => a.offsetParent)
              .map(a => ({t: a.innerText.trim().slice(0, 60), h: a.href}))
              .filter(x => x.t)""")
        for r in rows:
            print(r)

asyncio.run(main())
