import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    btn = page.query_selector(".acx-overlay-container .modal button:has-text('Create')")
    print("MODAL CREATE BTN:", bool(btn))
    if btn:
        btn.click()
        page.wait_for_timeout(6000)
    shot(page, "27a-after-create")
    txt = page.inner_text("body")
    print("HAS LIST NAME:", "YardScout internal testers" in txt)
    boxes = page.query_selector_all("input[type=checkbox]")
    for b in boxes:
        lbl = b.get_attribute("aria-label") or ""
        print("CB:", repr(lbl), "checked:", b.is_checked())
        if "internal testers" in lbl.lower() and not b.is_checked():
            b.check(); print(" -> CHECKED")
    page.wait_for_timeout(1500)
    sv = [b for b in page.query_selector_all("button:has-text('Save')") if b.is_visible()]
    print("SAVE BTNS:", len(sv))
    if sv:
        sv[-1].click(); print("CLICKED SAVE")
    page.wait_for_timeout(5000)
    shot(page, "27b-track-saved")
    print("BODY:\n", page.inner_text("body")[-2000:])
