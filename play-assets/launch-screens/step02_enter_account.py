import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("text=YardScout LLC", timeout=15000)
    page.wait_for_timeout(6000)
    print("URL:", page.url)
    shot(page, "02-account-home")
    print("BODY_SNIPPET:\n", page.inner_text("body")[:3000])
