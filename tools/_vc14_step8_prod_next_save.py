"""vc10 step 8: Next on prod editor -> review page; then Save (100% rollout)."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc14-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        await page.click("button:has-text('Next')", timeout=15000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "08a_prod_review")
        body = await page.inner_text("body")
        i = body.find("Errors, warnings")
        print("REVIEW:\n", body[i:i+1200] if i >= 0 else body[:2000])
        j = body.find("Rollout")
        print("ROLLOUT SECTION:\n", body[j:j+600] if j >= 0 else "(no Rollout text)")
        # Save
        btns = [b for b in await page.query_selector_all("button") if await b.is_visible()]
        save = None
        for b in btns:
            if (await b.inner_text()).strip() == "Save":
                save = b
        if not save:
            names = [(await b.inner_text()).strip() for b in btns]
            print("ABORT: no visible Save button. Buttons:", names[-12:]); return
        await save.click()
        await page.wait_for_timeout(4000)
        await ys_cdp.shot(page, "08b_save_dialog")
        dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
        for b in dlg:
            print("DIALOG BTN:", (await b.inner_text()).strip())
        for b in dlg:
            if (await b.inner_text()).strip() in ("Save", "Confirm", "OK"):
                await b.click(); print("CONFIRMED"); break
        await page.wait_for_timeout(7000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "08c_after_save")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2500])

asyncio.run(main())
