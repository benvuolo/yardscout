"""iOS step 8: Add for Review, then submit on the review submission page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.locator("button:has-text('Add for Review')").first
        if not await btn.count():
            print("ABORT: Add for Review button not found")
            return
        await btn.click()
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "08a_after_add_for_review")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2500])

asyncio.run(main())
