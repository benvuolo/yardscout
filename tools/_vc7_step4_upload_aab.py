"""Step 4: upload the signed 1.3 AAB and wait for processing."""
import asyncio, sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"
AAB = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/android/app/build/outputs/bundle/release/app-release.aab"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        print("URL:", page.url)
        await page.set_input_files("input[type=file]", AAB, timeout=15000)
        print("UPLOAD STARTED")
        for i in range(36):  # up to 6 min
            await page.wait_for_timeout(10000)
            body = await page.inner_text("body")
            if "Uploading" in body or "Processing" in body:
                continue
            if "1.3" in body or "Error" in body:
                break
        await ys_cdp.shot(page, "04_after_upload")
        idx = body.find("App bundles")
        print("BODY AFTER (from App bundles):\n", body[idx:idx+1800] if idx >= 0 else body[:2500])

asyncio.run(main())
