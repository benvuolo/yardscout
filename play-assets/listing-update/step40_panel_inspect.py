"""Open the Add-assets panel and inspect its upload affordances."""
import asyncio
import sys

sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/tools")
from playwright.async_api import async_playwright
from ys_cdp import get_page, shot

TAG_JS = """() => {
    document.querySelectorAll('[data-ys-shots]').forEach(e =>
        e.removeAttribute('data-ys-shots'));
    const head = [...document.querySelectorAll('*')].find(e =>
        e.children.length === 0 && /^Phone screenshots/.test(e.textContent.trim()));
    let s = head;
    for (let i = 0; i < 14 && s; i++) {
        if (s.textContent.includes('Add assets')) break;
        s = s.parentElement;
    }
    s.setAttribute('data-ys-shots', '1');
    return true;
}"""


async def main():
    async with async_playwright() as p:
        browser, page = await get_page(p, "store-listings/default/edit")
        if await page.locator(".asset-library-container").count() == 0:
            await page.evaluate(TAG_JS)
            await page.locator("[data-ys-shots='1']").get_by_text("Add assets").first.click()
            await page.wait_for_timeout(3000)
        await shot(page, "40-panel")
        info = await page.evaluate("""() => {
            const c = document.querySelector('.asset-library-container');
            if (!c) return {panel: false};
            return {
                panel: true,
                buttons: [...c.querySelectorAll('button')]
                    .filter(b => b.offsetParent)
                    .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
                    .filter(Boolean).slice(0, 30),
                inputs: [...c.querySelectorAll('input[type=file]')].length,
                anyFileInputs: [...document.querySelectorAll('input[type=file]')].length,
                tiles: [...c.querySelectorAll("[debug-id='tile-container']")]
                    .map(t => t.getAttribute('aria-label')).slice(0, 30),
            };
        }""")
        import json
        print(json.dumps(info, indent=1))

asyncio.run(main())
