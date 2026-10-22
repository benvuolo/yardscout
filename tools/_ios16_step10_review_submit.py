"""ios step 10: open App Review page and click Submit for Review."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.click("text=App Review", timeout=15000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "10a_app_review_page")
        body = await page.inner_text("body")
        print("REVIEW PAGE HEAD:\n", body[:1500])
        btn = page.locator("button:has-text('Submit for Review')").first
        if not await btn.count():
            print("ABORT: Submit for Review not found")
            return
        await btn.click()
        await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "10b_after_submit_click")
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1500])
        body = await page.inner_text("body")
        print("BODY HEAD:\n", body[:800])

asyncio.run(main())
