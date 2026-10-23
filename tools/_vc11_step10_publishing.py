"""vc10 step 10: Publishing overview — inspect pending changes."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc11-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(APP + "/publishing", wait_until="domcontentloaded", timeout=60000)
        body = ""
        for i in range(15):
            await page.wait_for_timeout(5000)
            body = await page.inner_text("body")
            if "Publishing overview" in body:
                break
        await ys_cdp.shot(page, "10_publishing_overview")
        print("URL:", page.url)
        i = body.find("Publishing overview")
        print("BODY:\n", body[i:i+3000] if i >= 0 else body[:3000])

asyncio.run(main())
