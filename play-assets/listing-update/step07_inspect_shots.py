"""Inspect the phone-screenshots uploader: thumbnails, delete buttons, file
inputs."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    info = page.evaluate("""() => {
        // Find the section containing the 'Phone screenshots' heading.
        const head = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Phone screenshots$/.test(e.textContent.trim()));
        if (!head) return {err: 'no heading'};
        let sec = head;
        for (let i = 0; i < 12 && sec; i++) {
            if (sec.querySelector('input[type=file]')) break;
            sec = sec.parentElement;
        }
        if (!sec) return {err: 'no section with file input'};
        sec.setAttribute('data-ys-shots', '1');
        const inputs = [...sec.querySelectorAll('input[type=file]')].map(i => ({
            accept: i.accept, multiple: i.multiple,
            debug: i.closest('[debug-id]')?.getAttribute('debug-id') || '',
        }));
        const btns = [...sec.querySelectorAll('button')].map(b => ({
            label: b.getAttribute('aria-label') || b.textContent.replace(/\\s+/g,' ').trim(),
            debug: b.getAttribute('debug-id') || '',
        }));
        const thumbs = [...sec.querySelectorAll('img')].map(i => i.src.slice(0, 70));
        return {inputs, btns: btns.slice(0, 40), thumbs,
                html: sec.outerHTML.slice(0, 1500)};
    }""")
    import json
    print(json.dumps(info, indent=1)[:4000])
