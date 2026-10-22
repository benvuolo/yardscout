"""ios step 4: reload the version page and check 1.5 status."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        await ys_cdp.shot(page, "04_status_after_reload")
        body = await page.inner_text("body")
        lines = [l.strip() for l in body.split("\n") if l.strip()]
        for l in lines[:40]:
            print(l)

asyncio.run(main())
