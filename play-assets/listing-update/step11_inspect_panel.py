"""Dump the asset-library panel's interactive elements."""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)
    info = page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return {err: 'panel closed'};
        const inter = [...c.querySelectorAll('button, [role=checkbox], [role=option], [aria-checked], input')]
            .map(e => ({
                tag: e.tagName, role: e.getAttribute('role'),
                label: (e.getAttribute('aria-label') || e.textContent.replace(/\\s+/g,' ').trim()).slice(0, 80),
                checked: e.getAttribute('aria-checked'),
                debug: e.getAttribute('debug-id') || '',
            }));
        return {count: inter.length, inter: inter.slice(0, 50)};
    }""")
    print(json.dumps(info, indent=1))
