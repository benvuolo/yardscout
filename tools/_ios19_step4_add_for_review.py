"""ios step 9: Add for Review -> submission page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v19-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.locator("button:has-text('Add for Review')").first
        if not await btn.count():
            body = await page.inner_text("body")
            print("ABORT: Add for Review button not found. Visible buttons:")
            for b in await page.query_selector_all("button"):
                if await b.is_visible():
                    t = (await b.inner_text()).strip()
                    if t: print(" -", t[:60])
            return
        await btn.click()
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "09a_after_add_for_review")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2500])

asyncio.run(main())
