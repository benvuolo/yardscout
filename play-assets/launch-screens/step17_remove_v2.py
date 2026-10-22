import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    # the bundle table row overflow menu
    mv = page.query_selector_all("button:has-text('more_vert')")
    print("MORE_VERT BUTTONS:", len(mv))
    clicked = False
    for b in mv:
        if b.is_visible():
            b.click(); clicked = True; break
    print("OPENED MENU:", clicked)
    page.wait_for_timeout(2500)
    shot(page, "17a-overflow-menu")
    # dump menu items
    items = page.eval_on_selector_all("[role=menuitem], [role=menu] *, .mat-menu-content *",
        "els => els.map(e => e.innerText && e.innerText.trim()).filter(Boolean).slice(0,30)")
    print("MENU ITEMS:", items)
