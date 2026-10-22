"""Step 12: Save the production release (100% rollout) and handle dialog."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        await ys_cdp.shot(page, "12a_before_save")
        btns = [b for b in await page.query_selector_all("button") if await b.is_visible()]
        save = None
        for b in btns:
            if (await b.inner_text()).strip() == "Save":
                save = b
        if not save:
            print("ABORT: no visible Save button"); return
        await save.click()
        await page.wait_for_timeout(4000)
        await ys_cdp.shot(page, "12b_save_dialog")
        body = await page.inner_text("body")
        # dialog?
        dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
        for b in dlg:
            print("DIALOG BTN:", (await b.inner_text()).strip())
        for b in dlg:
            if (await b.inner_text()).strip() in ("Save", "Confirm", "OK"):
                await b.click(); print("CONFIRMED"); break
        await page.wait_for_timeout(7000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "12c_after_save")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2500])

asyncio.run(main())
