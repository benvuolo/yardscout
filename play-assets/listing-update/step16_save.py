"""Pick 'Don't label assets' (real screenshots, not AI-generated), save the
listing, and capture the result."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    # AI declaration: real captured screenshots -> 'Don't label assets'.
    radio = page.get_by_text("Don't label assets", exact=True)
    radio.first.click()
    page.wait_for_timeout(1000)
    shot(page, "16-review-ai-declaration")

    # Scroll through the review assets for the record.
    page.evaluate("""() => {
        const el = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Phone screenshots$/.test(e.textContent.trim()));
        if (el) el.scrollIntoView({block: 'center'});
    }""")
    page.wait_for_timeout(1500)
    shot(page, "16-review-screenshots")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_timeout(6000)
    shot(page, "16-after-save")
    print("URL:", page.url)
    body = page.evaluate("() => document.body.innerText.slice(0, 1500)")
    print("PAGE TEXT:\n", body)
