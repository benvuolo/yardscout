"""Check Play Console publishing state before the needs-first copy update.

Connects to the CDP Chrome, finds (or opens) the Play Console publishing
overview for io.yardscout.app, and screenshots it so we can see whether
changes are still in review (if so, the listing edit waits)."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        if "play.google.com/console" not in page.url:
            page = await browser.contexts[0].new_page()
        # Land on the app dashboard first; the left nav carries the developer
        # and app ids we need for the publishing-overview URL.
        await page.goto("https://play.google.com/console", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        print("URL:", page.url)
        await shot(page, "28-console-landing")

asyncio.run(main())
