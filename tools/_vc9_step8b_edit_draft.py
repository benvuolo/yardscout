"""vc9 step 8b: open the draft production release editor from the track page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc9-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(APP + "/tracks/production?tab=releases", wait_until="domcontentloaded", timeout=60000)
        btn = page.locator("button:has-text('Edit release')").first
        for i in range(15):
            await page.wait_for_timeout(5000)
            if await btn.count() and await btn.is_visible():
                break
        await ys_cdp.shot(page, "08b_prod_releases_tab")
        if not await btn.count():
            print("ABORT: no Edit release button")
            body = await page.inner_text("body")
            print(body[:1500]); return
        await btn.click()
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "08c_draft_editor")
        body = await page.inner_text("body")
        i = body.find("Release notes")
        print("EDITOR (from Release notes):\n", body[i:i+700] if i >= 0 else body[:1500])

asyncio.run(main())
