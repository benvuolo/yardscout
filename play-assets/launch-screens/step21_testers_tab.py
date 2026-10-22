import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("text=Testers >> visible=true", timeout=10000)
    page.wait_for_timeout(5000)
    shot(page, "21-testers-tab")
    print("BODY:\n", page.inner_text("body")[:4000])
