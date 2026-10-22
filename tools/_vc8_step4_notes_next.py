"""vc8 step 4: fill release notes, click Next, show preview."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc8-screens"
NOTES = ("<en-US>\n"
         "Tap any car to open it on the yard's own website. "
         "Compare part prices across yards side by side. "
         "Cleaner make list (no more duplicate makes). "
         "Search yards by zip. "
         "New 500-mile radius option for Pro. "
         "Fixed a bug that showed some cars as fresh arrivals.\n"
         "</en-US>")


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        tareas = await page.query_selector_all("textarea")
        print("TEXTAREAS:", len(tareas))
        filled = False
        for t in tareas:
            ph = ((await t.get_attribute("aria-label") or "") + (await t.get_attribute("placeholder") or "")).lower()
            print(" -", repr(ph[:80]))
            if "note" in ph:
                await t.fill(NOTES); filled = True; break
        if not filled and tareas:
            await tareas[-1].fill(NOTES); filled = True
        print("NOTES FILLED:", filled)
        await page.wait_for_timeout(2000)
        await ys_cdp.shot(page, "04a_notes_filled")
        await page.click("button:has-text('Next')", timeout=15000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "04b_preview_confirm")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3500])

asyncio.run(main())
