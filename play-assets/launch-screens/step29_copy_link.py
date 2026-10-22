import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.click("text=Copy link", timeout=10000)
    page.wait_for_timeout(2000)
    try:
        clip = page.evaluate("navigator.clipboard.readText()")
        print("OPTIN LINK:", clip)
    except Exception as e:
        print("clipboard read failed:", e)
    shot(page, "29-copy-link")
