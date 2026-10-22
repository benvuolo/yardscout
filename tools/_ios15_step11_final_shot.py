"""iOS step 11: dismiss dialog, screenshot final Waiting for Review state."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(2000)
        await page.goto("https://appstoreconnect.apple.com/apps/6817126581/distribution/ios/version/inflight",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "11_final_waiting_for_review")
        body = await page.inner_text("body")
        print(body[:500])

asyncio.run(main())
