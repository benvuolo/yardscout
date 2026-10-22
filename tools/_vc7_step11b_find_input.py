"""Step 11b: enumerate inputs to find the rollout percentage field."""
import asyncio, sys, json
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
import ys_cdp
from playwright.async_api import async_playwright

ys_cdp.SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/vc7-screens"


async def main():
    async with async_playwright() as p:
        browser, page = await ys_cdp.get_page(p, "/releases/")
        meta = await page.eval_on_selector_all(
            "input:not([type=radio]):not([type=checkbox]), textarea",
            """els => els.map(e => ({
                tag: e.tagName, type: e.type, id: e.id,
                aria: e.getAttribute('aria-label'), ph: e.placeholder,
                visible: !!(e.offsetWidth || e.offsetHeight), value: e.value
            }))""")
        print(json.dumps(meta, indent=1))

asyncio.run(main())
