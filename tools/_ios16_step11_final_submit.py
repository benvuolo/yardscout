"""ios step 11: click Submit for Review in the Draft Submission panel (or App Review page)."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"
APP_REVIEW = "https://appstoreconnect.apple.com/apps/6817126581/distribution/reviewsubmissions"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.locator("[role=dialog] button:has-text('Submit for Review')").first
        if not await btn.count() or not await btn.is_visible():
            await page.goto(APP_REVIEW, wait_until="domcontentloaded", timeout=60000)
            btn = page.locator("button:has-text('Submit for Review')").first
            for i in range(18):
                await page.wait_for_timeout(5000)
                if await btn.count() and await btn.is_visible():
                    break
            await ys_cdp.shot(page, "11a_review_page")
        if not await btn.count():
            print("ABORT: Submit for Review not found")
            body = await page.inner_text("body")
            print("BODY:\n", body[:1500])
            return
        await btn.click()
        await page.wait_for_timeout(8000)
        await ys_cdp.shot(page, "11b_after_submit")
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1500])
        body = await page.inner_text("body")
        print("BODY HEAD:\n", body[:1200])

asyncio.run(main())
