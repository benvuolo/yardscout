"""vc10 step 4: fill release notes, click Next, show preview."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc13-screens"
NOTES = ("<en-US>\n"
         "Cleaner look: tidier Parts search controls, a simpler stats row, and "
         "collapsible info sections. Plus new Detroit-area yards.\n"
         "</en-US>")


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        tareas = await page.query_selector_all("textarea")
        filled = False
        for t in tareas:
            ph = ((await t.get_attribute("aria-label") or "") + (await t.get_attribute("placeholder") or "")).lower()
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
        i = body.find("Release notes")
        print("BODY (from Release notes):\n", body[i:i+600] if i >= 0 else body[:1500])

asyncio.run(main())
