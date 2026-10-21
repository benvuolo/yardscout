"""Click 'Submit 4 changes for review', confirm, and capture the post-submit
status."""
from playwright.sync_api import sync_playwright
from _cdp import shot

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages if "/publishing" in pg.url
                 and "submission-activity" not in pg.url), None)
    assert page, "publishing tab not found"

    page.get_by_role("button", name="Submit 4 changes for review").first.click()
    page.wait_for_timeout(2500)
    # Confirmation dialog, if any.
    dlg = page.locator("[role='dialog']")
    if dlg.count():
        print("DIALOG:", dlg.first.inner_text()[:600])
        shot(page, "18-submit-dialog")
        for label in ("Submit", "Send", "Confirm", "OK"):
            b = dlg.get_by_role("button", name=label)
            if b.count():
                b.first.click()
                print(f"clicked dialog button: {label}")
                break
    page.wait_for_timeout(6000)
    shot(page, "18-after-submit")
    body = page.evaluate("() => document.body.innerText")
    print("PAGE TEXT:\n", body[:2200])
