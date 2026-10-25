"""ios17 step 5: Add Build -> pick 1.9 build 2 -> Done -> Save."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v21-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        await page.goto("https://appstoreconnect.apple.com/apps/6817126581/distribution/ios/version/inflight",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(9000)
        btn = page.get_by_text("Add Build", exact=False).first
        if not await btn.count():
            print("ABORT: Add Build not found"); return
        await btn.click()
        await page.wait_for_timeout(5000)
        await ys_cdp.shot(page, "05a_build_dialog")
        dlg = page.locator("[role=dialog]").first
        if not await dlg.count():
            print("NO DIALOG"); return
        print("DIALOG TEXT:\n", (await dlg.inner_text())[:600])
        rows = dlg.locator("tr")
        n = await rows.count()
        picked = False
        for i in range(n):
            r = rows.nth(i)
            t = (await r.inner_text()).replace("\n", " ")
            if "1.9" in t and __import__("re").search(r"(^| )1( |$)", t):
                radio = r.locator("input[type=radio], input[type=checkbox]").first
                if await radio.count():
                    await radio.check()
                else:
                    await r.click()
                picked = True
                print("PICKED ROW:", t[:80])
                break
        if not picked:
            print("ABORT: no 1.9 build row"); return
        await page.wait_for_timeout(1500)
        await dlg.locator("button:has-text('Done')").first.click()
        await page.wait_for_timeout(5000)
        save = page.locator("button:has-text('Save')").first
        if await save.count():
            await save.click()
            await page.wait_for_timeout(7000)
        await ys_cdp.shot(page, "05b_saved_with_build")
        body = await page.inner_text("body")
        i = body.find("BUILD")
        print("BUILD SECTION:\n", body[i:i+200] if i >= 0 else body[:400])

asyncio.run(main())
