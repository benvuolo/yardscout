"""ios step 5: check TestFlight iOS builds list for the new build's state."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v23-screens"
URL = "https://appstoreconnect.apple.com/apps/6817126581/testflight/ios"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        await ys_cdp.shot(page, "05_testflight_builds")
        body = await page.inner_text("body")
        i = body.find("Builds")
        print(body[i:i+1800] if i >= 0 else body[:1800])

asyncio.run(main())
