"""iOS step 6: click Add Build, list available builds."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.get_by_text("Add Build", exact=False).first
        if not await btn.count():
            print("ABORT: Add Build not found")
            return
        await btn.click()
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "06a_build_dialog")
        dlg = page.locator("[role=dialog]").first
        if await dlg.count():
            print("DIALOG TEXT:\n", await dlg.inner_text())
        else:
            body = await page.inner_text("body")
            print("NO DIALOG; BODY:\n", body[:1500])

asyncio.run(main())
