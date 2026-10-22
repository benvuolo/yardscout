"""iOS step 10: click Submit for Review in the Draft Submission panel."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.locator("[role=dialog] button:has-text('Submit for Review')").first
        if not await btn.count():
            btn = page.locator("button:has-text('Submit for Review')").first
        if not await btn.count():
            print("ABORT: Submit for Review not found")
            return
        await btn.click()
        await page.wait_for_timeout(6000)
        await ys_cdp.shot(page, "10a_after_submit_click")
        # possible confirmation dialog (export compliance etc.)
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1500])
        body = await page.inner_text("body")
        print("BODY HEAD:\n", body[:600])

asyncio.run(main())
