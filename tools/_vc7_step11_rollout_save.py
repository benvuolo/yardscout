"""Step 11: set rollout 100%, Save, handle confirm dialog."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        # rollout percentage input
        filled = False
        for inp in await page.query_selector_all("input"):
            label = ((await inp.get_attribute("aria-label")) or "").lower()
            if "roll" in label or "percent" in label:
                await inp.fill("100"); filled = True
                print("ROLLOUT INPUT label:", label); break
        if not filled:
            # fallback: numeric input near 'Roll-out percentage'
            inp = page.locator("input").last
            print("FALLBACK input; aria:", await inp.get_attribute("aria-label"))
            await inp.fill("100"); filled = True
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "11a_rollout_100")
        await page.click("button:has-text('Save')", timeout=15000)
        await page.wait_for_timeout(4000)
        await ys_cdp.shot(page, "11b_after_save")
        # possible confirm dialog
        for sel in ["button:has-text('Save')", "button:has-text('Confirm')", "button:has-text('OK')"]:
            bs = [b for b in await page.query_selector_all(sel) if await b.is_visible()]
            if bs:
                txt = await bs[-1].inner_text()
                await bs[-1].click(); print("CONFIRM clicked:", txt); break
        await page.wait_for_timeout(7000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "11c_saved")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3000])

asyncio.run(main())
