"""Pick 'Don't label assets' (real app captures, no AI imagery) and Save.
Saving stages the change in Publishing overview, ready to send for review."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        radio = page.get_by_text("Don't label assets", exact=True)
        await radio.first.click()
        await page.wait_for_timeout(1000)
        await shot(page, "43-declared")
        save = page.get_by_role("button", name="Save", exact=True)
        assert await save.count(), "Save button missing"
        await save.first.click()
        await page.wait_for_timeout(6000)
        await shot(page, "43-after-save")
        body = await page.inner_text("body")
        snippet = [l for l in body.splitlines()
                   if any(k in l.lower() for k in
                          ("saved", "review", "publish", "error", "problem"))]
        print("\n".join(snippet[:25]))
        print("URL:", page.url)

asyncio.run(main())
