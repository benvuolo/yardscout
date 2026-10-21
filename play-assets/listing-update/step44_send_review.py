"""Open Publishing overview and send the saved listing change for review."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

PUB = ("https://play.google.com/console/u/0/developers/9052149026359320771/"
       "app/4975171430765358175/publishing")


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "play.google.com/console")
        await page.goto(PUB, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(7000)
        await shot(page, "44-overview-before")
        body = await page.inner_text("body")
        print("has 'Changes ready':", "ready to send" in body.lower()
              or "Changes ready" in body)
        btn = page.get_by_role("button", name="Send change for review")
        if await btn.count() == 0:
            btn = page.get_by_role("button", name="Send changes for review")
        if await btn.count() == 0:
            btn = page.locator("button", has_text="for review")
        assert await btn.count(), "send-for-review button not found"
        await btn.first.click()
        await page.wait_for_timeout(2500)
        await shot(page, "44-confirm-dialog")
        # confirm dialog (step18 pattern)
        dlg = page.locator("[role='dialog'] button", has_text="Send")
        if await dlg.count():
            await dlg.last.click()
            await page.wait_for_timeout(5000)
        await shot(page, "44-after-submit")
        body = await page.inner_text("body")
        snippet = [l for l in body.splitlines()
                   if any(k in l.lower() for k in
                          ("review", "sent", "publish", "error"))]
        print("\n".join(snippet[:20]))

asyncio.run(main())
