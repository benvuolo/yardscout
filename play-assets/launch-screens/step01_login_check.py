import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.goto("https://play.google.com/console", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    print("URL:", page.url)
    print("TITLE:", page.title())
    shot(page, "01-console-landing")
    # Dump visible text snippet to judge state
    body = page.inner_text("body")[:2000]
    print("BODY_SNIPPET:\n", body)
