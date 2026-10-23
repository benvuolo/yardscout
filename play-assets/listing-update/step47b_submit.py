"""Click 'Submit 1 change for review' for the phone-screenshots listing
change (the only item in the unsent bucket — verified in step47 output)."""
import re
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    # Several /publishing tabs exist (incl. the release worker's) — use a
    # fresh tab of our own so we never act on a stale or foreign one.
    page = ctx.new_page()
    page.goto("https://play.google.com/console/u/0/developers/9052149026359320771"
              "/app/4975171430765358175/publishing",
              wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(8000)
    print("URL:", page.url)

    body = page.evaluate("() => document.body.innerText")
    assert "Change Phone screenshots" in body, "listing change not in bucket"
    # Guard: the unsent bucket area must not list a Production change.
    unsent_zone = body.split("Changes not yet submitted for review", 1)[-1]
    assert "Production" not in unsent_zone.split("Product updates")[0], \
        "ABORT: Production row in unsent bucket"

    sub = page.get_by_role("button",
                           name=re.compile(r"Submit \d+ change(s)? for review"))
    assert sub.count(), "submit button not found"
    print("clicking:", sub.first.inner_text())
    sub.first.click()
    page.wait_for_timeout(2500)
    dlg = page.locator("[role='dialog']")
    if dlg.count() and dlg.first.is_visible():
        dtext = dlg.first.inner_text()
        print("DIALOG:", dtext[:600])
        assert "Production" not in dtext, \
            "ABORT: submit dialog mentions Production — not confirming"
        shot(page, "47b-submit-dialog")
        for name in ("Submit changes for review", "Send changes for review",
                     "Submit", "Confirm"):
            b = dlg.get_by_role("button", name=name)
            if b.count():
                b.first.click()
                print("confirmed via:", name)
                break
    page.wait_for_timeout(7000)
    body = page.evaluate("() => document.body.innerText")
    print("AFTER SUBMIT:\n", body[:2500])
    shot(page, "47b-after-submit")
