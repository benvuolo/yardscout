"""Diagnose the Add-assets panel state after the step46 partial add."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "store-listings/default/edit" in pg.url)

    def tag_section():
        return page.evaluate("""() => {
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
        }""")

    tag_section()
    print("slot:", page.evaluate("""() =>
        [...document.querySelector("[data-ys-shots='1']")
            .querySelectorAll("button[debug-id='delete-button']")]
        .map(b => b.getAttribute('aria-label'))"""))

    panel_open = page.locator(".asset-library-container").count() > 0
    print("panel open:", panel_open)
    if not panel_open:
        page.locator("[data-ys-shots='1']").get_by_text("Add assets").first.click()
        page.wait_for_timeout(2500)

    info = page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return null;
        return {
            crops: [...c.querySelectorAll("button[debug-id='crop-button']")]
                .map(b => b.getAttribute('aria-label')),
            buttons: [...c.querySelectorAll('button')].filter(b => b.offsetParent)
                .map(b => b.textContent.replace(/\\s+/g, ' ').trim()).filter(Boolean),
            live: [...c.querySelectorAll('[aria-live]')]
                .map(e => e.textContent.trim()).filter(Boolean),
            text: c.innerText.slice(0, 1200),
        };
    }""")
    import json
    print(json.dumps(info, indent=1)[:3000])
    shot(page, "46b-panel-diag")
