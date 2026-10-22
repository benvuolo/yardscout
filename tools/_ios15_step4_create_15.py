"""iOS step 4: fill 1.5 in the New Version dialog, Create."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        dlg = page.locator("[role=dialog]").first
        inp = dlg.locator("input").first
        await inp.fill("1.5")
        await page.wait_for_timeout(800)
        await ys_cdp.shot(page, "04a_version_filled")
        await dlg.locator("button:has-text('Create')").first.click()
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "04b_version_15_page")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2200])

asyncio.run(main())
