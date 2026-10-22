import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    ids = [i for i in page.query_selector_all("input") if i.is_visible() and (i.get_attribute("aria-label") or "")]
    for i in ids:
        print("INPUT:", repr(i.get_attribute("aria-label")))
    bp = page.query_selector("input[aria-label*='Base plan ID'], input[aria-label*='base plan']")
    if not bp:
        bp = ids[0] if ids else None
    bp.fill("monthly")
    print("BASE PLAN ID:", repr(bp.input_value()))
    # select Auto-renewing radio
    radios = page.query_selector_all("[role=radio], input[type=radio]")
    for r in radios:
        lbl = r.get_attribute("aria-label") or ""
        print("RADIO:", repr(lbl), "checked:", r.get_attribute("aria-checked") or r.is_checked())
    auto = page.query_selector("[role=radio][aria-label*='Auto'], label:has-text('Auto-renewing')")
    if auto:
        auto.click()
        print("CLICKED AUTO-RENEWING")
    page.wait_for_timeout(4000)
    shot(page, "37-baseplan-id-type")
    print("BODY (top):\n", page.inner_text("body")[:2500])
