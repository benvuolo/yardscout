"""Open the Main store listing in our own tab, dump current field values,
and take 'before' screenshots (top + description + screenshots section)."""
from playwright.sync_api import sync_playwright
from _cdp import get_page, goto_listing, shot

with sync_playwright() as p:
    browser, page = get_page(p)
    goto_listing(page)
    print("URL:", page.url)
    shot(page, "01-before-top")

    # Dump every textbox/textarea the form renders (label + value + count).
    fields = page.evaluate("""() =>
        [...document.querySelectorAll('textarea, input[type=text]')].map(el => ({
            label: el.getAttribute('aria-label') || el.closest('[debug-id]')?.getAttribute('debug-id') || '?',
            value: (el.value || '').slice(0, 400),
            len: (el.value || '').length,
        }))""")
    for f in fields:
        print(f"FIELD [{f['label']}] len={f['len']}: {f['value']!r}")

    # Find the phone screenshots section and count current thumbnails.
    heads = page.evaluate("""() =>
        [...document.querySelectorAll('h2,h3,h4')].map(h => h.textContent.trim()).filter(Boolean)""")
    print("HEADINGS:", heads)
