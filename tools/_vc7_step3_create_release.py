"""Step 3: wait for internal track render, click Create new release."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "tracks/internal-testing")
        for i in range(12):
            body = await page.inner_text("body")
            if "Create new release" in body or "Releases" in body:
                break
            await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "03a_internal_loaded")
        print("BODY:\n", body[:2500])
        btn = page.locator("button:has-text('Create new release')").first
        if await btn.count() == 0 or not await btn.is_visible():
            print("ABORT: Create new release button not found/visible")
            return
        await btn.click()
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "03b_release_editor")
        body = await page.inner_text("body")
        print("EDITOR BODY:\n", body[:3000])
        n = await page.eval_on_selector_all("input[type=file]", "els => els.length")
        print("FILE_INPUTS:", n)

asyncio.run(main())
