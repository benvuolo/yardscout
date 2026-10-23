"""ios17 step 8: Remove All screenshots on 1.6 draft, upload the 7-slide set in order."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"
D = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/ios/dynamic-island-1206x2622"
ORDER = ["screen_1_live", "screen_2_search", "screen_7_fitment", "screen_6_compare",
         "screen_3_yards", "screen_5_pro", "screen_4_alerts"]
FILES = [f"{D}/{n}.png" for n in ORDER]


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        # Remove existing 5
        ra = page.locator("button:has-text('Remove All')").first
        if await ra.count() and await ra.is_visible():
            await ra.click()
            await page.wait_for_timeout(2500)
            dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
            for b in dlg:
                t = (await b.inner_text()).strip()
                print("DIALOG BTN:", t)
            for b in dlg:
                t = (await b.inner_text()).strip().lower()
                if "remove" in t or "delete" in t or t == "confirm":
                    await b.click(); print("CONFIRMED:", t); break
            await page.wait_for_timeout(4000)
        await ys_cdp.shot(page, "08a_after_remove_all")
        body = await page.inner_text("body")
        i = body.find("App Screenshots")
        print("COUNT NOW:", body[max(0, i-30):i+20])
        # Upload 7 in order via the section's file input
        up = page.locator("button:has-text('Upload')").first
        if await up.count():
            # Upload button opens a chooser; prefer direct input if present
            inputs = await page.query_selector_all("input[type=file]")
            print("FILE INPUTS:", len(inputs))
            done = False
            for inp in inputs:
                acc = (await inp.get_attribute("accept")) or ""
                if "png" in acc:
                    await inp.set_input_files(FILES)
                    done = True
                    print("SET FILES on input accept=", acc)
                    break
            if not done:
                async with page.expect_file_chooser() as fc:
                    await up.click()
                chooser = await fc.value
                await chooser.set_files(FILES)
                print("SET FILES via chooser")
        # wait for upload processing
        for i in range(30):
            await page.wait_for_timeout(5000)
            body = await page.inner_text("body")
            j = body.find("App Screenshots")
            frag = body[max(0, j-30):j+20]
            if "7 of 10" in frag:
                break
        print("FINAL COUNT:", frag)
        await ys_cdp.shot(page, "08b_after_upload")

asyncio.run(main())
