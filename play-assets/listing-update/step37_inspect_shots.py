"""Scroll to the phone screenshots section and inspect its current state."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        assert "store-listings/default/edit" in page.url, page.url
        hdr = page.locator("text=Phone screenshots").first
        await hdr.scroll_into_view_if_needed()
        await page.wait_for_timeout(1500)
        await shot(page, "37-shots-panel")
        # Thumbnails usually render as img tags inside the uploader; count them
        info = await page.evaluate("""() => {
            const imgs = [...document.querySelectorAll('img')]
                .filter(i => i.offsetParent && i.naturalWidth > 0
                             && /googleusercontent|play-lh/.test(i.src))
                .map(i => ({src: i.src.slice(0, 90), w: i.width, h: i.height}));
            return imgs;
        }""")
        for x in info:
            print(x)

asyncio.run(main())
