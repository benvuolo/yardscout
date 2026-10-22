"""ios step 8: Add Build -> pick build 2 -> Done -> Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        btn = page.get_by_text("Add Build", exact=False).first
        if not await btn.count():
            print("ABORT: Add Build not found"); return
        await btn.click()
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "08a_build_dialog")
        dlg = page.locator("[role=dialog]").first
        if not await dlg.count():
            print("NO DIALOG"); return
        print("DIALOG TEXT:\n", (await dlg.inner_text())[:1200])
        # pick the row containing 'Build 2' / '2'
        rows = dlg.locator("tr")
        n = await rows.count()
        picked = False
        for i in range(n):
            r = rows.nth(i)
            t = (await r.inner_text()).replace("\n", " ")
            if "2" in t and "1.5" in t:
                radio = r.locator("input[type=radio], input[type=checkbox]").first
                if await radio.count():
                    await radio.check()
                else:
                    await r.click()
                picked = True
                print("PICKED ROW:", t[:100])
                break
        if not picked:
            # single-build dialogs sometimes just list build 2
            radio = dlg.locator("input[type=radio]").first
            if await radio.count():
                await radio.check(); picked = True; print("PICKED only radio")
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "08b_build_selected")
        await dlg.locator("button:has-text('Done')").first.click()
        await page.wait_for_timeout(5000)
        save = page.locator("button:has-text('Save')").first
        if await save.count():
            await save.click()
            await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "08c_saved_with_build2")
        body = await page.inner_text("body")
        i = body.find("BUILD")
        print("BUILD SECTION:\n", body[i:i+300] if i >= 0 else body[:600])

asyncio.run(main())
