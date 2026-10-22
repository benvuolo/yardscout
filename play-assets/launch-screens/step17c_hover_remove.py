import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    row = page.query_selector("tr:has-text('2 (1.1)'), [role=row]:has-text('2 (1.1)')")
    print("ROW FOUND:", bool(row))
    if row:
        row.hover()
        page.wait_for_timeout(1500)
    # re-enumerate buttons
    btns = page.query_selector_all("button")
    target = None
    for b in btns:
        t = (b.inner_text() or "").strip()
        al = b.get_attribute("aria-label") or ""
        if "more_vert" in t or "more" in al.lower() or "option" in al.lower():
            if b.is_visible():
                target = b
                print("MENU BTN:", repr(t), repr(al))
                break
    if target:
        target.click()
        page.wait_for_timeout(2000)
        shot(page, "17c-menu-open")
        items = page.eval_on_selector_all("[role=menuitem], [role=menu] button, [role=menu] a",
            "els => els.map(e => (e.innerText||'').trim()).filter(Boolean)")
        print("MENU ITEMS:", items)
    else:
        print("no menu button found")
        shot(page, "17c-no-menu")
