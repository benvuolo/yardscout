"""iOS step 3: click + next to iOS App, create version 1.5."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v15-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        # The + button sits next to the "iOS App" sidebar header
        btn = page.locator("button[aria-label*='Add' i], [class*='addVersion'], button:near(:text('iOS App'))").first
        # safer: find small + button near iOS App text
        candidates = await page.query_selector_all("button")
        target = None
        for b in candidates:
            al = (await b.get_attribute("aria-label")) or ""
            if "add" in al.lower() and ("version" in al.lower() or "platform" in al.lower() or al.strip().lower() == "add"):
                target = b
                print("BTN aria-label:", al)
                break
        if not target:
            # click by position: the + icon next to iOS App
            el = page.locator("text=iOS App").first
            box = await el.bounding_box()
            print("iOS App box:", box)
            if box:
                await page.mouse.click(box["x"] + box["width"] + 14, box["y"] + box["height"] / 2)
        else:
            await target.click()
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "03a_new_version_dialog")
        body = await page.inner_text("body")
        i = body.find("New Version") if "New Version" in body else 0
        print("BODY:\n", body[i:i+800])

asyncio.run(main())
