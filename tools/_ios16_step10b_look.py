"""ios step 10b: screenshot current ASC page to find the blocking overlay."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await ys_cdp.shot(page, "10c_overlay_look")
        print("URL:", page.url)
        dlgs = page.locator("[role=dialog]")
        for i in range(await dlgs.count()):
            d = dlgs.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1200])
        # try escape to dismiss
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(2000)
        await ys_cdp.shot(page, "10d_after_escape")

asyncio.run(main())
