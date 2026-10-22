import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="base-plans/create")
    print("PAGE:", page.url)
    # sanity: check form state
    bp = page.query_selector("input[aria-label='Base plan ID field']")
    print("BASE PLAN ID:", repr(bp.input_value()) if bp else None)
    txt = page.inner_text("body")
    print("US PRICED:", "USD 8.99" in txt or "$8.99" in txt)
    # close the leftover invite page to avoid future confusion
    for pg in browser.contexts[0].pages:
        if "users-and-permissions/invite" in pg.url:
            pg.close(); print("closed stray invite tab")
    sv = [b for b in page.query_selector_all("button") if b.is_visible() and (b.inner_text() or "").strip() == "Save"]
    print("SAVE BTNS:", len(sv))
    if sv:
        sv[-1].click()
        page.wait_for_timeout(8000)
    print("URL AFTER:", page.url)
    shot(page, "42-baseplan-saved")
    print("BODY:\n", page.inner_text("body")[:3500])
