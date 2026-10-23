"""vc9 step 6: Save and publish the internal testing release."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc9-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        await page.click("button:has-text('Save and publish')", timeout=15000)
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "06a_publish_dialog")
        for sel in ["button:has-text('Save and publish')", "button:has-text('Publish')", "button:has-text('Confirm')"]:
            bs = [b for b in await page.query_selector_all(sel) if await b.is_visible()]
            if bs:
                await bs[-1].click(); print("CONFIRM:", sel); break
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "06b_after_publish")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3000])

asyncio.run(main())
