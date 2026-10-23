"""ios17 step 9: wait for thumbnails, Save the 1.6 page, verify."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        # wait for thumbnails to render (img tags inside the media section)
        for i in range(24):
            await page.wait_for_timeout(5000)
            n = await page.eval_on_selector_all(
                "img", "els => els.filter(e => (e.src||'').includes('image')).length")
            body = await page.inner_text("body")
            if "7 of 10 App Screenshots" in body and n >= 5:
                break
        print("THUMB IMGS:", n)
        await ys_cdp.shot(page, "09a_thumbs")
        save = page.locator("button:has-text('Save')").first
        if await save.count() and await save.is_enabled():
            await save.click()
            await page.wait_for_timeout(8000)
            print("SAVED")
        else:
            print("Save button state:", await save.count(), "— may be auto-saved")
        await ys_cdp.shot(page, "09b_after_save")
        body = await page.inner_text("body")
        j = body.find("App Screenshots")
        print("COUNT:", body[max(0, j-30):j+20])
        print("STATUS LINE:", [l for l in body.split("\n") if "1.6" in l][:3])

asyncio.run(main())
