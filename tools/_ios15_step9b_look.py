"""Look at current ASC page state."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        print("URL:", page.url)
        await ys_cdp.shot(page, "09b_current_state")
        dlg = page.locator("[role=dialog]")
        for i in range(await dlg.count()):
            d = dlg.nth(i)
            if await d.is_visible():
                print(f"DIALOG {i}:\n", (await d.inner_text())[:1200])

asyncio.run(main())
