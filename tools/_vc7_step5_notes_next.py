"""Step 5: fill release notes, click Next, show preview."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
NOTES = "<en-US>\nTap an alert to jump straight to that car with the freshest data. Clearer filters and part values. Bug fixes.\n</en-US>"


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
        await ys_cdp.shot(page, "05a_notes_filled")
        await page.click("button:has-text('Next')", timeout=15000)
        await page.wait_for_timeout(8000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "05b_preview_confirm")
        body = await page.inner_text("body")
        print("BODY:\n", body[:3500])

asyncio.run(main())
