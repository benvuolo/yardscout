"""iOS step 7: select the 1.5 build row, Done, Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        dlg = page.locator("[role=dialog]").first
        # click the radio in the row containing '1.5'
        row = dlg.locator("tr", has=page.locator("text=1.5")).first
        if await row.count():
            radio = row.locator("input[type=radio], input[type=checkbox]").first
            if await radio.count():
                await radio.check()
            else:
                await row.click()
        else:
            # fallback: click the text cell '1.5'
            await dlg.get_by_text("1.5", exact=True).first.click()
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "07a_build_selected")
        await dlg.locator("button:has-text('Done')").first.click()
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "07b_build_attached")
        # Save the page
        save = page.locator("button:has-text('Save')").first
        if await save.count():
            await save.click()
            await page.wait_for_timeout(6000)
        await ys_cdp.shot(page, "07c_saved_with_build")
        body = await page.inner_text("body")
        i = body.find("Build")
        print("BUILD SECTION:\n", body[i:i+400] if i >= 0 else body[:800])

asyncio.run(main())
