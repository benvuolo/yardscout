"""ios17 step 10: Submit for Review — dialog if open, else via App Review draft."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v23-screens"
APP_REVIEW = "https://appstoreconnect.apple.com/apps/6817126581/distribution/reviewsubmissions"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.locator("[role=dialog] button:has-text('Submit for Review')").first
        if not await btn.count() or not await btn.is_visible():
            await page.goto(APP_REVIEW, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(8000)
            link = page.locator("a:has-text('Today at')").first
            if not await link.count():
                link = page.locator("button:has-text('Draft Submissions')").first
            if await link.count():
                await link.click()
                await page.wait_for_timeout(5000)
            btn = page.locator("button:has-text('Submit for Review')").first
            for i in range(8):
                if await btn.count() and await btn.is_visible():
                    break
                await page.wait_for_timeout(3000)
        if not await btn.count() or not await btn.is_visible():
            print("ABORT: Submit for Review not reachable")
            await ys_cdp.shot(page, "10x_stuck")
            body = await page.inner_text("body")
            print(body[:1200]); return
        await btn.click()
        await page.wait_for_timeout(9000)
        await ys_cdp.shot(page, "10a_after_submit")
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1200])
        body = await page.inner_text("body")
        i = body.find("Submissions")
        print("BODY:\n", body[i:i+1200] if i >= 0 else body[:1200])

asyncio.run(main())
