"""Upload the 5 recaptured shots through the asset-library Upload control,
one at a time, verifying each lands on the listing in order."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

NEW = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/screenshots"
ORDER = ["screen_1_live.png", "screen_3_yards.png", "screen_5_pro.png",
         "screen_2_search.png", "screen_4_alerts.png"]

TAG_JS = """() => {
    document.querySelectorAll('[data-ys-shots]').forEach(e =>
        e.removeAttribute('data-ys-shots'));
    const head = [...document.querySelectorAll('*')].find(e =>
        e.children.length === 0 && /^Phone screenshots/.test(e.textContent.trim()));
    if (!head) return false;
    let s = head;
    for (let i = 0; i < 14 && s; i++) {
        if (s.querySelector("button[debug-id='delete-button']")
            || s.textContent.includes('Add assets')) break;
        s = s.parentElement;
    }
    if (!s) return false;
    s.setAttribute('data-ys-shots', '1');
    return true;
}"""

THUMBS_JS = """() => {
    const sec = document.querySelector("[data-ys-shots='1']");
    if (!sec) return null;
    return [...sec.querySelectorAll("button[debug-id='delete-button']")]
        .map(b => b.getAttribute('aria-label'));
}"""


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")

        async def thumbs():
            assert await page.evaluate(TAG_JS)
            return await page.evaluate(THUMBS_JS)

        async def open_panel():
            if await page.locator(".asset-library-container").count() == 0:
                await page.evaluate(TAG_JS)
                await page.locator("[data-ys-shots='1']").get_by_text(
                    "Add assets").first.click()
                await page.wait_for_timeout(2500)

        print("start:", await thumbs())
        for i, name in enumerate(ORDER):
            await open_panel()
            panel = page.locator(".asset-library-container")
            finput = panel.locator("input[type=file]")
            if await finput.count() == 0:
                finput = page.locator("input[type=file]")
            await finput.first.set_input_files(f"{NEW}/{name}")
            # wait for the upload to finish and the tile to attach
            attached = False
            for _ in range(60):
                await page.wait_for_timeout(1000)
                t = await thumbs()
                if t is not None and len(t) >= i + 1:
                    attached = True
                    break
            if not attached:
                # maybe it only selected in the library; press the exact Add
                add = panel.get_by_role("button", name="Add", exact=True)
                if await add.count():
                    await add.first.click()
                    for _ in range(20):
                        await page.wait_for_timeout(1000)
                        t = await thumbs()
                        if t is not None and len(t) >= i + 1:
                            attached = True
                            break
            t = await thumbs()
            print(f"after {name}: {t}", flush=True)
            assert attached, f"{name} did not attach"
            await page.wait_for_timeout(1000)

        labels = await thumbs()
        ok = labels == [f"Remove {n}" for n in ORDER]
        print("ORDER OK:", ok)
        # close the panel if open
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1200)
        await page.evaluate(TAG_JS)
        await page.locator("[data-ys-shots='1']").scroll_into_view_if_needed()
        await page.wait_for_timeout(800)
        await shot(page, "41-after-upload")

asyncio.run(main())
