"""After-shots of each edited section, then proceed to the Review step."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    # Close asset panel.
    page.evaluate("""() => {
        const c = document.querySelector('.asset-library-container');
        if (!c) return;
        const x = [...c.parentElement.querySelectorAll('button')]
            .find(b => /close/i.test(b.getAttribute('aria-label') || ''));
        if (x) x.click();
    }""")
    page.wait_for_timeout(1500)

    def scroll_to(heading):
        found = page.evaluate("""(h) => {
            const el = [...document.querySelectorAll('*')].find(e =>
                e.children.length === 0 && e.textContent.trim().startsWith(h));
            if (!el) return false;
            el.scrollIntoView({block: 'start'});
            window.scrollBy(0, -80);
            return true;
        }""", heading)
        page.wait_for_timeout(1200)
        return found

    scroll_to("Short description")
    shot(page, "15-after-descriptions")
    scroll_to("Phone screenshots")
    shot(page, "15-after-phone-screenshots")

    # Any remaining form errors before moving on?
    errs = page.evaluate("""() =>
        [...document.querySelectorAll("[role='alert']")]
        .map(e => e.textContent.trim()).filter(Boolean)""")
    print("alerts:", errs)

    # Next -> Review step.
    page.get_by_role("button", name="Next").click()
    page.wait_for_timeout(6000)
    print("URL:", page.url)
    shot(page, "15-review-top")
    # Dump visible buttons so we know the save/publish control names.
    btns = page.evaluate("""() =>
        [...document.querySelectorAll('button')]
        .filter(b => b.offsetParent)
        .map(b => b.textContent.replace(/\\s+/g,' ').trim()).filter(Boolean)""")
    print("buttons:", btns)
    body = page.evaluate("() => document.body.innerText.slice(0, 3000)")
    print("PAGE TEXT:\n", body)
