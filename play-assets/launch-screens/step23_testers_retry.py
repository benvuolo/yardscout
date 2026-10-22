import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    for i in range(10):
        page.wait_for_timeout(4000)
        txt = page.inner_text("body")
        if "Testers" in txt or "tester" in txt.lower():
            break
    shot(page, "23-testers-loaded")
    print("BODY:\n", page.inner_text("body")[:4500])
    # list tab elements
    tabs = page.eval_on_selector_all("[role=tab]", "els => els.map(e => ({t: e.innerText.trim(), sel: e.getAttribute('aria-selected')}))")
    print("TABS:", tabs)
