"""ios17 step 3: open the app page, click + by iOS App, create version 2.0."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v22-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.goto("https://appstoreconnect.apple.com/apps/6817126581/distribution",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(9000)
        await ys_cdp.shot(page, "03a_app_page")
        candidates = await page.query_selector_all("button")
        target = None
        for b in candidates:
            al = (await b.get_attribute("aria-label")) or ""
            if "add" in al.lower() and ("version" in al.lower() or "platform" in al.lower() or al.strip().lower() == "add"):
                target = b
                print("BTN aria-label:", al)
                break
        if not target:
            el = page.locator("text=iOS App").first
            box = await el.bounding_box()
            print("iOS App box:", box)
            if box:
                await page.mouse.click(box["x"] + box["width"] + 14, box["y"] + box["height"] / 2)
        else:
            await target.click()
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "03b_new_version_dialog")
        dlg = page.locator("[role=dialog]").first
        if not await dlg.count():
            print("NO DIALOG"); return
        print("DIALOG:", (await dlg.inner_text())[:400])
        inp = dlg.locator("input").first
        await inp.fill("2.0")
        await page.wait_for_timeout(800)
        await ys_cdp.shot(page, "03c_version_filled")
        await dlg.locator("button:has-text('Create')").first.click()
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "03d_version_16_page")
        body = await page.inner_text("body")
        print("BODY:\n", body[:1200])

asyncio.run(main())
