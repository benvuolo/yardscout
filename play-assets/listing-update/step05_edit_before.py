"""Open the default-listing editor; dump current field values and take
'before' screenshots of the description + graphics sections."""
from playwright.sync_api import sync_playwright
from _cdp import shot

EDIT = ("https://play.google.com/console/u/0/developers/9052149026359320771"
        "/app/4975171430765358175/store-listings/default/edit")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    page.goto(EDIT, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    shot(page, "05-before-edit-top")

    fields = page.evaluate("""() =>
        [...document.querySelectorAll('textarea, input[type=text]')].map(el => ({
            label: el.getAttribute('aria-label')
                   || el.closest('console-form-row')?.querySelector('label')?.textContent.trim()
                   || '?',
            value: el.value || '',
        }))""")
    for f in fields:
        print(f"FIELD [{f['label']}] len={len(f['value'])}:")
        print(f["value"])
        print("---")

    # Scroll to the phone screenshots area and shoot it.
    found = page.evaluate("""() => {
        const els = [...document.querySelectorAll('h2,h3,h4,div')]
            .filter(e => /^Phone screenshots$/i.test(e.textContent.trim()));
        if (!els.length) return false;
        els[0].scrollIntoView({block:'start'});
        return true;
    }""")
    page.wait_for_timeout(1500)
    print("phone screenshots heading found:", found)
    shot(page, "05-before-phone-screenshots")
    # Count current phone screenshot thumbnails (images inside the section).
    info = page.evaluate("""() => {
        const all = [...document.querySelectorAll('img')]
            .map(i => i.src).filter(s => /googleusercontent|play-lh/.test(s));
        return {imgCount: all.length, srcs: all.map(s => s.slice(0, 90))};
    }""")
    print("console-hosted images:", info["imgCount"])
    for s in info["srcs"]:
        print("  ", s)
