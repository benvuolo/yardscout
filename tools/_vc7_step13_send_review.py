"""Step 13: Go to Publishing overview, send change for review."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        # click Go to overview if dialog still up, else navigate
        dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
        clicked = False
        for b in dlg:
            if "Go to overview" in (await b.inner_text()):
                await b.click(); clicked = True; break
        if not clicked:
            await page.goto(APP + "/publishing", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "13a_publishing_overview")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3500])

asyncio.run(main())
