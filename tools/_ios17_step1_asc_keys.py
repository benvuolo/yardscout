"""ios17 step 1: open ASC Users and Access -> Integrations (API keys)."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v17-screens"
URL = "https://appstoreconnect.apple.com/access/integrations/api"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "appstoreconnect")
        if "appstoreconnect" not in page.url:
            ctx = browser.contexts[0]
            page = await ctx.new_page()
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(9000)
        print("URL:", page.url)
        await ys_cdp.shot(page, "01_integrations")
        body = await page.inner_text("body")
        print("BODY:\n", body[:2000])

asyncio.run(main())
