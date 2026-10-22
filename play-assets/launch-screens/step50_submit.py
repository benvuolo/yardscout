import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="/publishing")
    btns = [b for b in page.query_selector_all("button:has-text('Submit 1 change for review')") if b.is_visible()]
    print("SUBMIT BTNS:", len(btns), "disabled:", [b.is_disabled() for b in btns])
    if btns and not btns[0].is_disabled():
        btns[0].click()
        page.wait_for_timeout(4000)
        shot(page, "50a-submit-dialog")
        print("TAIL:\n", page.inner_text("body")[-1500:])
        # confirm if dialog
        conf = page.query_selector(".acx-overlay-container .modal button:has-text('Submit'), .acx-overlay-container .modal button:has-text('Send')")
        if conf:
            conf.click(); print("CONFIRMED")
            page.wait_for_timeout(7000)
    shot(page, "50b-after-submit")
    print("BODY:\n", page.inner_text("body")[:3500])
