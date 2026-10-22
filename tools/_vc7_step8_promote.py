"""Step 8: Promote release -> Production."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "tracks/")
        await page.goto(APP + "/tracks/internal-testing", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(9000)
        await ys_cdp.shot(page, "08a_internal_track")
        btn = page.locator("button:has-text('Promote release')").first
        if not await btn.count():
            print("ABORT: no Promote release button"); return
        await btn.click()
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "08b_promote_menu")
        items = await page.eval_on_selector_all(
            "[role=menuitem], [role=menu] *",
            "els => els.map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20)")
        print("MENU:", items)

asyncio.run(main())
