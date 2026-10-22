"""Step 9: click Production in the promote menu; land in prod release editor."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "tracks/")
        items = [e for e in await page.query_selector_all("[role=menuitem]") if await e.is_visible()]
        target = None
        for e in items:
            if (await e.inner_text()).strip() == "Production":
                target = e
        if not target:
            print("ABORT: Production menu item not visible"); return
        await target.click()
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "09_prod_release_editor")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3500])

asyncio.run(main())
