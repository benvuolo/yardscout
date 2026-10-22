"""vc8 step 9: inspect the production track state + rollout percentage."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc8-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "play.google.com/console")
        await page.goto(APP + "/tracks/production", wait_until="domcontentloaded", timeout=60000)
        for i in range(15):
            await page.wait_for_timeout(5000)
            body = await page.inner_text("body")
            if "Releases" in body and "Loading" not in body.split("\n")[0]:
                break
        await ys_cdp.shot(page, "09_prod_track")
        print("URL:", page.url)
        print("BODY:\n", body[:3500])

asyncio.run(main())
