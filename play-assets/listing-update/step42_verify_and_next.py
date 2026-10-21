"""Re-verify the needs-first description is still in the draft, close the
asset panel, then click Next to reach the review/save step."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        # close the asset panel if still open
        x = page.locator(".asset-library-container ~ * button[aria-label*='lose'], "
                         "button[aria-label='Close']")
        if await page.locator(".asset-library-container").count():
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        full = None
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v.startswith("YardScout tracks the live inventory"):
                full = v
        assert full, "description box lost"
        ok_value = "Value ranges on nearly every car" in full
        ok_alert = "strips the part you need" in full
        gone = ("Resale" not in full and "demand speed" not in full
                and "coming soon" not in full)
        print("value bullet:", ok_value, "| alert bullet:", ok_alert,
              "| old strings gone:", gone)
        assert ok_value and ok_alert and gone
        nxt = page.get_by_role("button", name="Next", exact=True)
        assert await nxt.count(), "Next button missing"
        await nxt.first.click()
        await page.wait_for_timeout(5000)
        print("URL:", page.url)
        await shot(page, "42-after-next")
        body = await page.inner_text("body")
        for kw in ("review", "publish", "Save"):
            pass
        print(body[:2500])

asyncio.run(main())
