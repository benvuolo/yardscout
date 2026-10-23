"""Dump the DOM of the newest screen_3_yards.png library tile to find the
real selection click target."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "store-listings/default/edit" in pg.url)
    html = page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        const crops = [...c.querySelectorAll("button[debug-id='crop-button']")]
            .filter(b => b.getAttribute('aria-label') === 'Crop screen_3_yards.png');
        for (const b of crops) {
            let row = b;
            for (let i = 0; i < 10 && row; i++) {
                if (row.textContent.includes('1080x2160')
                    && row.textContent.includes('screen_3_yards.png')) break;
                row = row.parentElement;
            }
            if (!row || !row.textContent.includes('1080x2160')) continue;
            return row.outerHTML;
        }
        return null;
    }""")
    print((html or "NOT FOUND")[:4000])
    shot(page, "46d-panel")
