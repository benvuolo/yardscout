"""Step 14: click 'Submit 1 change for review' and confirm."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/publishing")
        btn = page.locator("button:has-text('Submit 1 change for review')").first
        if not await btn.count():
            print("ABORT: submit button not found"); return
        await btn.click()
        await page.wait_for_timeout(3500)
        await ys_cdp.shot(page, "14a_submit_dialog")
        dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
        for b in dlg:
            print("DIALOG BTN:", (await b.inner_text()).strip())
        for b in dlg:
            t = (await b.inner_text()).strip()
            if "Send" in t or "Submit" in t or t == "Confirm":
                await b.click(); print("CONFIRMED with:", t); break
        await page.wait_for_timeout(8000)
        await ys_cdp.shot(page, "14b_after_submit")
        body = await page.inner_text("body")
        i = body.find("Publishing overview")
        print("BODY:\n", body[i:i+2200] if i >= 0 else body[:2500])

asyncio.run(main())
