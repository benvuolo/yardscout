"""Replace the two flip-framed Pro bullets in the full description with the
needs-first copy (matches play-assets/LISTING.md after the reframe)."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

OLD_VALUE = "\u2022 Resale value ranges and demand speed on nearly every car"
NEW_VALUE = ("\u2022 Value ranges on nearly every car \u2014 know what a part "
             "is worth before you drive")
OLD_ALERT = ("\u2022 In-app arrival alerts within hours of a watched car "
             "hitting a yard in your radius \u2014 before the weekend crowd "
             "strips it (push notifications coming soon)")
NEW_ALERT = ("\u2022 Push alerts within hours of a watched car hitting a yard "
             "in your radius \u2014 before the weekend crowd strips the part "
             "you need")


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        assert "store-listings/default/edit" in page.url, page.url
        boxes = page.locator("textarea, input[type=text]")
        n = await boxes.count()
        full_i = None
        for i in range(n):
            v = await boxes.nth(i).input_value()
            if v.startswith("YardScout tracks the live inventory"):
                full_i = i
                cur = v
        assert full_i is not None, "full description box not found"
        assert OLD_VALUE in cur and OLD_ALERT in cur, "expected bullets missing"
        new = cur.replace(OLD_VALUE, NEW_VALUE).replace(OLD_ALERT, NEW_ALERT)
        box = boxes.nth(full_i)
        await box.scroll_into_view_if_needed()
        await box.fill(new)
        await page.wait_for_timeout(800)
        check = await box.input_value()
        assert NEW_VALUE in check and NEW_ALERT in check, "fill failed"
        assert "Resale" not in check and "coming soon" not in check
        print(f"full description updated ({len(check)} chars)")
        await shot(page, "36-after-text")

asyncio.run(main())
