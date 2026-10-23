"""vc10 step 2: open internal testing track, click Create new release."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc11-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(APP + "/tracks/internal-testing", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        body = await page.inner_text("body")
        for i in range(10):
            if "Create new release" in body:
                break
            await page.wait_for_timeout(4000)
            body = await page.inner_text("body")
        await ys_cdp.shot(page, "02a_internal_track")
        btn = page.locator("button:has-text('Create new release')").first
        if await btn.count() == 0 or not await btn.is_visible():
            print("ABORT: Create new release button not found/visible")
            print("BODY:\n", body[:2500])
            return
        await btn.click()
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "02b_release_editor")
        body = await page.inner_text("body")
        print("EDITOR BODY:\n", body[:2500])
        n = await page.eval_on_selector_all("input[type=file]", "els => els.length")
        print("FILE_INPUTS:", n)

asyncio.run(main())
