"""ios step 6: open the 1.5 version page, fill What's New, Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"
URL = "https://appstoreconnect.apple.com/apps/6817126581/distribution/ios/version/inflight"
WHATS_NEW = (
    "Tap an alert to jump straight to that car with the freshest data. "
    "Tap any car to open it on the yard's own website. "
    "Compare part prices across yards side by side on the Yards tab. "
    "Search yards by zip. "
    "New 500-mile radius option for Pro. "
    "Cleaner make list (no more duplicate makes). "
    "Clearer filters, plus bug fixes - including one that showed some cars as fresh arrivals."
)


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(9000)
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
            # fallback: the textarea whose current value matches the old notes
            for t in tareas:
                v = await t.input_value()
                if v.startswith("Tap an alert"):
                    wn_t = t
        if not wn_t:
            print("ABORT: What's New textarea not found")
            for t in tareas:
                print("  name=", await t.get_attribute("name"), "aria=", await t.get_attribute("aria-label"),
                      "val=", (await t.input_value())[:50])
            return
        await wn_t.fill(WHATS_NEW)
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "06a_whatsnew_filled")
        save = page.locator("button:has-text('Save')").first
        await save.click()
        await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "06b_saved")
        body = await page.inner_text("body")
        print("SAVED. Page head:", body[:300])

asyncio.run(main())
