"""ios17 step 4: fill What's New on the 1.6 page, Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"
WHATS_NEW = (
    "New Parts tab: tell us the part and your car, and we list donor cars near "
    "you that fit, with how sure we are. Or browse any part near you \u2014 engine "
    "hunting included. "
    "Clearer filters on the Yards tab (fixed truncation on phones). "
    "Find cars by model with any spelling (mr2, f150). "
    "Yard-site links on every car. "
    "Cleaner make and model lists. "
    "More yards, including metro Detroit."
)


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        tareas = await page.query_selector_all("textarea")
        print("TEXTAREAS:", len(tareas))
        wn_t = None
        for t in tareas:
            name = (await t.get_attribute("name")) or ""
            aria = (await t.get_attribute("aria-label")) or ""
            key = (name + " " + aria).lower().replace(" ", "").replace("'", "")
            if "whatsnew" in key:
                wn_t = t
        if not wn_t:
            for t in tareas:
                print("  name=", await t.get_attribute("name"),
                      "aria=", await t.get_attribute("aria-label"))
            print("ABORT: What's New textarea not found"); return
        await wn_t.fill(WHATS_NEW)
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "04a_whatsnew_filled")
        save = page.locator("button:has-text('Save')").first
        await save.click()
        await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "04b_saved")
        body = await page.inner_text("body")
        i = body.find("What")
        print("SAVED; around What's New:", body[i:i+120] if i >= 0 else body[:200])

asyncio.run(main())
