"""vc9 step 5: expand warnings on the review page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc9-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        sm = page.locator("text=Show more").first
        if await sm.count():
            await sm.click()
            await page.wait_for_timeout(2500)
        await ys_cdp.shot(page, "05_warnings_expanded")
        body = await page.inner_text("body")
        i = body.find("Errors, warnings")
        print(body[i:i+2500] if i >= 0 else body[:2500])

asyncio.run(main())
