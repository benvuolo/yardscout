"""Interchange listing update, part 2: Next -> Review (AI declaration: Don't
label) -> Save -> Publishing overview -> send ONLY the listing change for
review.

Safety: the vc9 (1.5) production release is in review right now (submitted by
the release worker this morning). Before confirming 'Send changes for review'
we assert the unsent bucket mentions the store listing and does NOT contain a
Production/release row — if it does, abort without sending."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next(pg for pg in ctx.pages if "store-listings/default/edit" in pg.url)

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
    shot(page, "47-review-interchange")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_timeout(6000)
    shot(page, "47-after-save")

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
    shot(page, "47-publishing-overview")

    # Submit the unsent bucket — must be ONLY the listing change.
    sub = page.locator("button").filter(has_text="changes for review")
    if not sub.count():
        print("no submit button found — dumping buttons")
        print(page.evaluate("""() => [...document.querySelectorAll('button')]
            .filter(b => b.offsetParent)
            .map(b => b.textContent.replace(/\\s+/g,' ').trim()).filter(Boolean)"""))
        raise SystemExit(1)

    # The 'Changes not yet sent for review' section must not include a
    # Production release row (the in-review vc9 lives in its own section).
    unsent = page.evaluate("""() => {
        const h = [...document.querySelectorAll('*')].find(e =>
            e.children.length === 0
            && /not yet sent for review/i.test(e.textContent));
        if (!h) return null;
        let s = h;
        for (let i = 0; i < 12 && s; i++) {
            if (/Item changed/i.test(s.textContent)) break;
            s = s.parentElement;
        }
        return s ? s.innerText : null;
    }""")
    print("UNSENT BUCKET:\n", unsent)
    assert unsent and "store listing" in unsent.lower(), \
        f"unsent bucket missing the listing change: {unsent!r}"
    assert "Production" not in (unsent or ""), \
        "ABORT: unsent bucket contains a Production row — would touch the release"

    label = sub.first.inner_text()
    print("submit button:", label)
    sub.first.click()
    page.wait_for_timeout(2500)
    dlg = page.locator("[role='dialog']")
    if dlg.count() and dlg.first.is_visible():
        dtext = dlg.first.inner_text()
        print("DIALOG:", dtext[:500])
        assert "Production" not in dtext, \
            "ABORT: submit dialog mentions Production — not confirming"
        shot(page, "47-submit-dialog")
        b = dlg.get_by_role("button", name="Send changes for review")
        if b.count():
            b.first.click()
            print("sent for review")
    page.wait_for_timeout(6000)
    body = page.evaluate("() => document.body.innerText")
    print("AFTER SUBMIT:\n", body[:2200])
    shot(page, "47-after-submit")
