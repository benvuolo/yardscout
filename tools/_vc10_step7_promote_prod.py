"""vc10 step 7: Promote release -> Production, land in prod release editor."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc10-screens"
APP = "https://play.google.com/console/u/0/developers/9052149026359320771/app/4975171430765358175"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "tracks/")
        await page.goto(APP + "/tracks/internal-testing", wait_until="domcontentloaded", timeout=60000)
        btn = page.locator("button:has-text('Promote release')").first
        for i in range(15):
            await page.wait_for_timeout(5000)
            if await btn.count() and await btn.is_visible():
                break
        await ys_cdp.shot(page, "07a_internal_track")
        if not await btn.count():
            print("ABORT: no Promote release button"); return
        await btn.click()
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "07b_promote_menu")
        items = [e for e in await page.query_selector_all("[role=menuitem]") if await e.is_visible()]
        target = None
        for e in items:
            t = (await e.inner_text()).strip()
            print("MENU ITEM:", t)
            if t == "Production":
                target = e
        if not target:
            print("ABORT: Production menu item not visible"); return
        await target.click()
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "07c_prod_release_editor")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3000])

asyncio.run(main())
