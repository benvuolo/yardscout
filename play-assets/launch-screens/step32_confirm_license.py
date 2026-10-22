import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    btn = page.query_selector(".acx-overlay-container .modal button:has-text('Save')")
    print("MODAL SAVE:", bool(btn))
    if btn:
        btn.click()
        page.wait_for_timeout(6000)
    shot(page, "32-license-confirmed")
    # verify checkbox state now
    boxes = page.query_selector_all("input[type=checkbox], [role=checkbox]")
    for b in boxes:
        lbl = b.get_attribute("aria-label") or ""
        try: checked = b.is_checked()
        except Exception: checked = b.get_attribute("aria-checked")
        print("CB:", repr(lbl), "checked:", checked)
    print("TAIL:", page.inner_text("body")[-300:])
