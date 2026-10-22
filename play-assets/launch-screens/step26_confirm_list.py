import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Create') >> visible=true", timeout=10000)
    page.wait_for_timeout(6000)
    shot(page, "26a-list-created")
    txt = page.inner_text("body")
    print("HAS LIST:", "YardScout internal testers" in txt)
    # select checkbox for the list if not already
    boxes = page.query_selector_all("input[type=checkbox]")
    print("CHECKBOXES:", len(boxes))
    for b in boxes:
        lbl = b.get_attribute("aria-label") or ""
        checked = b.is_checked()
        print(" -", repr(lbl), "checked:", checked)
        if "YardScout internal testers" in lbl or "internal testers" in lbl.lower():
            if not checked:
                b.check()
                print("   -> CHECKED")
    page.wait_for_timeout(2000)
    # save track settings
    sv = [b for b in page.query_selector_all("button:has-text('Save')") if b.is_visible()]
    if sv:
        sv[-1].click(); print("SAVED TRACK")
    page.wait_for_timeout(5000)
    shot(page, "26b-testers-saved")
    print("BODY:\n", page.inner_text("body")[-2500:])
