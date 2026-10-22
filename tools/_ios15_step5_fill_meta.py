"""iOS step 5: fill Description + What's New on the 1.5 page, Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"
DESC = open("/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools/_ios15_description.txt").read().strip()
WHATS_NEW = "Tap an alert to jump straight to that car with the freshest data. Clearer filters and part values, plus bug fixes."


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        tareas = await page.query_selector_all("textarea")
        print("TEXTAREAS:", len(tareas))
        desc_t, wn_t = None, None
        for t in tareas:
            name = (await t.get_attribute("name")) or ""
            aria = (await t.get_attribute("aria-label")) or ""
            vis = await t.is_visible()
            val = (await t.input_value())[:60].replace("\n", " ")
            print(f" - name={name!r} aria={aria!r} vis={vis} val={val!r}")
            key = (name + " " + aria).lower()
            if "description" in key and desc_t is None:
                desc_t = t
            if ("whatsnew" in key.replace(" ", "")) or ("what's new" in key) or ("whats new" in key):
                wn_t = t
        if not desc_t or not wn_t:
            print("ABORT: couldn't identify fields (desc:", bool(desc_t), "wn:", bool(wn_t), ")")
            return
        await desc_t.fill(DESC)
        await wn_t.fill(WHATS_NEW)
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "05a_meta_filled")
        # Save
        save = page.locator("button:has-text('Save')").first
        await save.click()
        await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "05b_saved")
        body = await page.inner_text("body")
        print("AFTER SAVE snippet:", body[:400])

asyncio.run(main())
