"""ios step 12: open the draft submission row, click Submit for Review inside."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        row = page.locator("tr", has=page.locator("text=Ready for Review")).first
        if not await row.count():
            print("ABORT: draft row not found"); return
        await row.click()
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "12a_draft_open")
        btn = page.locator("button:has-text('Submit for Review')").first
        for i in range(6):
            if await btn.count() and await btn.is_visible():
                break
            await page.wait_for_timeout(3000)
        if not await btn.count() or not await btn.is_visible():
            print("ABORT: Submit button not visible after opening draft")
            dlgs = page.locator("[role=dialog]")
            for i in range(await dlgs.count()):
                d = dlgs.nth(i)
                if await d.is_visible():
                    print(f"DIALOG {i}:\n", (await d.inner_text())[:1200])
            return
        await btn.click()
        await page.wait_for_timeout(9000)
        await ys_cdp.shot(page, "12b_after_submit")
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1500])
        body = await page.inner_text("body")
        print("BODY:\n", body[:1600])

asyncio.run(main())
