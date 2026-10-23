"""ios17 step 6: inspect the App Previews and Screenshots section on 1.6."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        sec = page.locator("text=App Previews and Screenshots").first
        await sec.scroll_into_view_if_needed()
        await page.wait_for_timeout(2000)
        await ys_cdp.shot(page, "06a_media_section")
        body = await page.inner_text("body")
        i = body.find("App Previews and Screenshots")
        print("SECTION TEXT:\n", body[i:i+900])
        # enumerate file inputs + visible size tabs
        inputs = await page.query_selector_all("input[type=file]")
        print("FILE INPUTS:", len(inputs))
        for inp in inputs[:6]:
            acc = await inp.get_attribute("accept")
            print("  accept=", acc)
        imgs = await page.query_selector_all("[class*=screenshot] img, [class*=Screenshot] img")
        print("SCREENSHOT IMGS:", len(imgs))

asyncio.run(main())
