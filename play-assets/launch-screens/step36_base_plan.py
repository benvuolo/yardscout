import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("button:has-text('Add base plan')", timeout=15000)
    page.wait_for_timeout(7000)
    print("URL:", page.url)
    shot(page, "36-base-plan-form")
    print("BODY:\n", page.inner_text("body")[:5000])
