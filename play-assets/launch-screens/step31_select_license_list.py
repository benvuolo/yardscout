import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    boxes = page.query_selector_all("input[type=checkbox], [role=checkbox]")
    print("CHECKBOXES:", len(boxes))
    for b in boxes:
        lbl = b.get_attribute("aria-label") or ""
        try: checked = b.is_checked()
        except Exception: checked = b.get_attribute("aria-checked")
        print(" -", repr(lbl), "checked:", checked)
    # click the row checkbox for our list
    row = page.query_selector("tr:has-text('YardScout internal testers'), [role=row]:has-text('YardScout internal testers')")
    print("ROW:", bool(row))
    if row:
        cb = row.query_selector("input[type=checkbox], [role=checkbox], material-checkbox")
        print("ROW CB:", bool(cb))
        if cb:
            cb.click()
            page.wait_for_timeout(2000)
    shot(page, "31a-list-checked")
    sv = [b for b in page.query_selector_all("button:has-text('Save changes')") if b.is_visible()]
    if sv:
        sv[-1].click(); print("SAVED")
    page.wait_for_timeout(5000)
    shot(page, "31b-license-saved")
    print("BODY TAIL:\n", page.inner_text("body")[-1200:])
