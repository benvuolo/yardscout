import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    boxes = page.query_selector_all("input[type=checkbox], [role=checkbox]")
    print("CHECKBOXES:", len(boxes))
    sel_all = None
    for b in boxes:
        lbl = (b.get_attribute("aria-label") or "")
        if "all" in lbl.lower():
            sel_all = b
            print("SELECT ALL CB:", repr(lbl))
            break
    if sel_all:
        sel_all.click()
        page.wait_for_timeout(2500)
    shot(page, "39a-all-selected")
    btn = [b for b in page.query_selector_all("button:has-text('Set price')") if b.is_visible()]
    print("SET PRICE BTNS:", len(btn))
    btn[-1].click()
    page.wait_for_timeout(4000)
    shot(page, "39b-price-dialog")
    print("TAIL:\n", page.inner_text("body")[-1800:])
    for f in page.query_selector_all("input"):
        if f.is_visible():
            print("FIELD:", repr(f.get_attribute("aria-label")), repr(f.input_value()))
