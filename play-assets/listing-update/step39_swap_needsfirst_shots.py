"""Swap all 5 phone screenshots for the needs-first recaptures, preserving
the owner's approved order: live, yards, pro, search, alerts (step20 order).

Same flow as step08: delete every tile, then upload the new files one at a
time via the Add-assets file chooser so order is guaranteed."""
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

THUMBS_JS = """() =>
    [...document.querySelector("[data-ys-shots='1']")
        .querySelectorAll("button[debug-id='delete-button']")]
    .map(b => b.getAttribute('aria-label'))"""


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        assert "store-listings/default/edit" in page.url, page.url

        async def thumbs():
            assert await page.evaluate(TAG_JS), "screenshots section not found"
            return await page.evaluate(THUMBS_JS)

        sec = page.locator("[data-ys-shots='1']")
        print("before:", await thumbs())
        await sec.scroll_into_view_if_needed()
        await page.wait_for_timeout(800)

        # ---- delete all current tiles ----
        for _ in range(10):
            btns = sec.locator("button[debug-id='delete-button']")
            if await btns.count() == 0:
                break
            name = await btns.first.get_attribute("aria-label")
            await btns.first.click()
            await page.wait_for_timeout(1200)
            for txt in ("Delete", "Remove", "Confirm"):
                dlg = page.locator(f"[role='dialog'] button:has-text('{txt}')")
                if await dlg.count():
                    await dlg.first.click()
                    await page.wait_for_timeout(1000)
                    break
            print("deleted:", name, flush=True)
        print("after-delete:", await thumbs())
        await shot(page, "39-after-delete")

        # ---- upload new shots one at a time, in approved order ----
        for i, name in enumerate(ORDER):
            await page.evaluate(TAG_JS)
            sec = page.locator("[data-ys-shots='1']")
            add = sec.locator("button:has-text('Add assets')")
            if await add.count() == 0:
                add = sec.get_by_text("Add assets")
            async with page.expect_file_chooser() as fc:
                await add.first.click()
            chooser = await fc.value
            await chooser.set_files(f"{NEW}/{name}")
            for _ in range(60):
                await page.wait_for_timeout(1000)
                if len(await thumbs()) >= i + 1:
                    break
            print("uploaded:", name, "->", await thumbs(), flush=True)
            await page.wait_for_timeout(1500)

        labels = await thumbs()
        print("ORDER OK:", labels == [f"Remove {n}" for n in ORDER])
        await shot(page, "39-after-upload")
        errs = await page.evaluate("""() => {
            const sec = document.querySelector("[data-ys-shots='1']");
            return [...sec.querySelectorAll("[role='alert'], .error, [debug-id*='error']")]
                .map(e => e.textContent.trim()).filter(Boolean);
        }""")
        print("errors:", errs)

asyncio.run(main())
