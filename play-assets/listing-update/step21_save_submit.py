"""Next -> Review (AI declaration: Don't label) -> Save -> Publishing overview
-> submit the reorder."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "store-listings/default/edit" in pg.url), None)

    page.get_by_role("button", name="Next").click()
    page.wait_for_timeout(6000)

    # AI declaration — keep 'Don't label assets'.
    radio = page.get_by_text("Don't label assets", exact=True)
    if radio.count():
        radio.first.click()
        page.wait_for_timeout(800)

    # Scroll the review to Phone screenshots for the record.
    page.evaluate("""() => {
        const el = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0 && /^Phone screenshots$/.test(e.textContent.trim()));
        if (el) el.scrollIntoView({block: 'center'});
    }""")
    page.wait_for_timeout(1500)
    shot(page, "21-review-reordered")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_timeout(6000)
    shot(page, "21-after-save")

    # 'Go to Publishing overview?' dialog.
    btn = page.get_by_role("button", name="Go to overview")
    if btn.count():
        btn.first.click()
    else:
        page.goto("https://play.google.com/console/u/0/developers/9052149026359320771"
                  "/app/4975171430765358175/publishing",
                  wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    body = page.evaluate("() => document.body.innerText")
    print("PUBLISHING OVERVIEW:\n", body[:2500])
    shot(page, "21-publishing-overview")

    # Submit whatever unsubmitted bucket exists (should be just the reorder).
    sub = page.locator("button").filter(has_text="changes for review")
    if sub.count():
        label = sub.first.inner_text()
        print("submit button:", label)
        sub.first.click()
        page.wait_for_timeout(2500)
        dlg = page.locator("[role='dialog']")
        if dlg.count() and dlg.first.is_visible():
            print("DIALOG:", dlg.first.inner_text()[:400])
            b = dlg.get_by_role("button", name="Send changes for review")
            if b.count():
                b.first.click()
                print("sent for review")
        page.wait_for_timeout(6000)
        body = page.evaluate("() => document.body.innerText")
        print("AFTER SUBMIT:\n", body[:2200])
        shot(page, "21-after-submit")
    else:
        print("no submit button found — dumping buttons")
        print(page.evaluate("""() => [...document.querySelectorAll('button')]
            .filter(b => b.offsetParent)
            .map(b => b.textContent.replace(/\\s+/g,' ').trim()).filter(Boolean)"""))
