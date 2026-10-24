"""Pre-submit webkit check for the vonly layout hotfix (vc12 / iOS 1.8).

Playwright webkit, 390x844, against https://yardscout.io:
Parts tab -> engine-browse (Hunt chip) -> toggle Verified/VIN-only ON ->
assert document scrollWidth == clientWidth (no page-wide zoom/overflow).
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "https://yardscout.io/"
SHOTS = Path("/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/v20-screens")


async def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        await page.goto(BASE + "index.html", wait_until="domcontentloaded")
        await page.click("#live-filter-toggle")
        await page.fill("#live-zip", "85003")
        await page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card", timeout=30000)
        await page.click("#live-filter-toggle")
        await page.click(".tab[data-tab='parts']")
        await page.wait_for_selector("#tab-parts.active #pf-body", state="visible")
        await page.wait_for_selector("#pf-results .pf-try-chip", timeout=10000)

        chips = page.locator("#pf-results .pf-try-chip")
        labels = [await chips.nth(i).inner_text() for i in range(await chips.count())]
        hunt_i = next((j for j, l in enumerate(labels) if l.startswith("Hunt")), None)
        print("chips:", labels, "| hunt index:", hunt_i)
        if hunt_i is None:
            print("FAIL: no engine-browse (Hunt) chip found")
            return
        await chips.nth(hunt_i).click()
        await page.wait_for_timeout(1200)
        await page.check("#pf-vonly-cb")
        await page.wait_for_timeout(600)

        sw = await page.evaluate("document.documentElement.scrollWidth")
        cw = await page.evaluate("document.documentElement.clientWidth")
        await page.screenshot(path=str(SHOTS / "webkit_vonly_check.png"))
        print(f"scrollWidth={sw} clientWidth={cw}")
        print("PASS" if sw == cw else "FAIL: horizontal overflow")
        await browser.close()


asyncio.run(main())
