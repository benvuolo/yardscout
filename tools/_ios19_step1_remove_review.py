"""ios step 3: find and click 'Remove from Review' on the 1.7 version page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v19-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        body = await page.inner_text("body")
        import re
        hits = [l.strip() for l in body.split("\n") if re.search(r"[Rr]emove.*[Rr]eview|[Cc]ancel.*[Ss]ubmission", l)]
        print("TEXT HITS:", hits)
        loc = page.locator("text=/Remove.*from Review/i").first
        if not await loc.count():
            # sometimes it's under the status or a button
            loc = page.locator("button:has-text('Remove'), a:has-text('Remove')").first
        if not await loc.count():
            print("NO REMOVE CONTROL FOUND — dumping candidate buttons")
            btns = [b for b in await page.query_selector_all("button, a") if await b.is_visible()]
            for b in btns[:60]:
                t = (await b.inner_text()).strip()
                if t: print("CTRL:", t[:70])
            return
        print("CLICKING:", (await loc.inner_text()).strip())
        await loc.click()
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "03a_remove_dialog")
        dlg = [b for b in await page.query_selector_all("[role=dialog] button, .modal button") if await b.is_visible()]
        for b in dlg:
            print("DIALOG BTN:", (await b.inner_text()).strip())
        for b in dlg:
            t = (await b.inner_text()).strip().lower()
            if "remove" in t or "confirm" in t or t == "yes":
                await b.click(); print("CONFIRMED:", t); break
        await page.wait_for_timeout(6000)
        await ys_cdp.shot(page, "03b_after_remove")
        body = await page.inner_text("body")
        print("STATUS LINE:", [l for l in body.split("\n") if "1.7" in l][:5])

asyncio.run(main())
