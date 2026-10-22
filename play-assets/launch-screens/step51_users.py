import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p, prefer="/publishing")
    page.goto("https://play.google.com/console/u/0/developers/9052149026359320771/users-and-permissions",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(9000)
    shot(page, "51-users-permissions")
    print("BODY:\n", page.inner_text("body")[:4000])
