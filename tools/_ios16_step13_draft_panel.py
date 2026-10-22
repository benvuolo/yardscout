"""ios step 13: open draft via its date link / floating button, then Submit for Review."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        link = page.locator("a:has-text('Today at 12:06 AM')").first
        if not await link.count():
            link = page.locator("button:has-text('Draft Submissions')").first
        if not await link.count():
            print("ABORT: no draft link/button"); return
        await link.click()
        await page.wait_for_timeout(6000)
        await ys_cdp.shot(page, "13a_draft_panel")
        btn = page.locator("button:has-text('Submit for Review')").first
        for i in range(6):
            if await btn.count() and await btn.is_visible():
                break
            await page.wait_for_timeout(3000)
        if not await btn.count() or not await btn.is_visible():
            print("NO SUBMIT BTN. Page text around draft:")
            body = await page.inner_text("body")
            i = body.find("Draft")
            print(body[i:i+1500] if i >= 0 else body[:1500])
            return
        await btn.click()
        await page.wait_for_timeout(9000)
        await ys_cdp.shot(page, "13b_after_submit")
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1500])
        body = await page.inner_text("body")
        print("BODY:\n", body[:1600])

asyncio.run(main())
