import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    for el in page.query_selector_all("text=Show more"):
        try:
            el.click(); page.wait_for_timeout(1500)
        except Exception as e:
            print("click err", e)
    page.wait_for_timeout(3000)
    shot(page, "15-errors-expanded")
    print("BODY:\n", page.inner_text("body")[:7000])
