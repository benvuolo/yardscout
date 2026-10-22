"""ios step 7: remove attached build 1, attach build 2 on the 1.5 page."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v16-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        # scroll to Build section
        bl = page.locator("h2:has-text('Build'), h3:has-text('Build')").first
        if await bl.count():
            await bl.scroll_into_view_if_needed()
        await page.wait_for_timeout(1500)
        await ys_cdp.shot(page, "07a_build_section")
        # look for a remove/delete control near the build row
        row = page.locator("tr", has=page.locator("text=1.5")).first
        print("BUILD ROW FOUND:", await row.count())
        if await row.count():
            await row.hover()
            await page.wait_for_timeout(1000)
        candidates = await page.query_selector_all(
            "button[aria-label*=elete], button[aria-label*=emove], a[aria-label*=elete], "
            ".delete-button, button:has-text('Remove Build')")
        print("DELETE CANDIDATES:", len(candidates))
        for c in candidates:
            if await c.is_visible():
                print("CLICK:", await c.get_attribute("aria-label"))
                await c.click()
                break
        await page.wait_for_timeout(2500)
        await ys_cdp.shot(page, "07b_after_delete_click")
        # confirm dialog if any
        dlg = [b for b in await page.query_selector_all("[role=dialog] button") if await b.is_visible()]
        for b in dlg:
            print("DIALOG BTN:", (await b.inner_text()).strip())
        for b in dlg:
            t = (await b.inner_text()).strip().lower()
            if "delete" in t or "remove" in t or t == "ok":
                await b.click(); print("CONFIRMED:", t); break
        await page.wait_for_timeout(3000)
        await ys_cdp.shot(page, "07c_build_removed")
        body = await page.inner_text("body")
        i = body.find("Build")
        print("BUILD SECTION NOW:\n", body[i:i+500] if i >= 0 else body[:500])

asyncio.run(main())
