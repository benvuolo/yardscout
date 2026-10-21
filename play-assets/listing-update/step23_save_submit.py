"""Next -> Review -> Save -> Publishing overview -> submit (flexible button
match: 'Submit N change(s) for review')."""
import re
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    page.get_by_role("button", name="Next").click()
    page.wait_for_timeout(6000)
    radio = page.get_by_text("Don't label assets", exact=True)
    if radio.count():
        radio.first.click()
        page.wait_for_timeout(800)
    page.evaluate("""() => {
        const el = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Phone screenshots$/.test(e.textContent.trim()));
        if (el) el.scrollIntoView({block: 'center'});
    }""")
    page.wait_for_timeout(1500)
    shot(page, "23-review-honest-alerts")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_timeout(6000)
    btn = page.get_by_role("button", name="Go to overview")
    if btn.count():
        btn.first.click()
    else:
        page.goto("https://play.google.com/console/u/0/developers/9052149026359320771"
                  "/app/4975171430765358175/publishing",
                  wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    shot(page, "23-publishing-overview")

    # Submit: button text is 'Submit N change(s) for review'.
    sub = page.get_by_role("button", name=re.compile(r"Submit \d+ changes? for review"))
    assert sub.count(), "no submit button found"
    print("submit button:", sub.first.inner_text())
    sub.first.click()
    page.wait_for_timeout(2500)
    dlg = page.locator("[role='dialog']")
    if dlg.count() and dlg.first.is_visible():
        print("DIALOG:", dlg.first.inner_text()[:300])
        dlg.get_by_role("button", name="Send changes for review").first.click()
        print("sent for review")
    page.wait_for_timeout(6000)
    body = page.evaluate("() => document.body.innerText")
    print("AFTER SUBMIT:\n", body[:1800])
    shot(page, "23-after-submit")
