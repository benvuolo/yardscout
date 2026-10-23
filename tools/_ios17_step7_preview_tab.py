"""ios17 step 7: open the Preview tab in the media section, inspect screenshots."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        tab = page.locator("button:has-text('Preview'), [role=tab]:has-text('Preview')").first
        print("PREVIEW TAB FOUND:", await tab.count())
        if await tab.count():
            await tab.click()
            await page.wait_for_timeout(4000)
        await ys_cdp.shot(page, "07a_preview_tab")
        body = await page.inner_text("body")
        i = body.find("App Previews and Screenshots")
        print("SECTION:\n", body[i:i+1200])
        imgs = await page.query_selector_all("img")
        print("TOTAL IMGS on page:", len(imgs))
        # look for a media manager link
        mm = page.locator("text=/Media Manager|View All Sizes/i").first
        print("MEDIA MANAGER LINK:", await mm.count())

asyncio.run(main())
