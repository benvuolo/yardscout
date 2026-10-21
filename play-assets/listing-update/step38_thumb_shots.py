"""Element-screenshot each phone-screenshot thumbnail to confirm slide order."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, SHOTS


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        assert "store-listings/default/edit" in page.url, page.url
        thumbs = page.locator("img[src*='googleusercontent']")
        n = await thumbs.count()
        idx = 0
        for i in range(n):
            el = thumbs.nth(i)
            box = await el.bounding_box()
            if not box or box["height"] < 100:   # skip avatar/icon images
                continue
            if abs(box["height"] / max(box["width"], 1) - 2.0) > 0.3:
                continue                          # keep only 1:2 slide thumbs
            idx += 1
            await el.scroll_into_view_if_needed()
            await el.screenshot(path=f"{SHOTS}/thumb_{idx}.png")
            print(f"thumb_{idx}: {box['width']}x{box['height']}")
        print("slides found:", idx)

asyncio.run(main())
