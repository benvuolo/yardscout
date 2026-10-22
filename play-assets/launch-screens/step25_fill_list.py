import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    page.fill("input[aria-label='List name']", "YardScout internal testers")
    em = page.query_selector("input[aria-label='Add email addresses']")
    em.fill("yardscout.io@gmail.com")
    em.press("Enter")
    page.wait_for_timeout(2000)
    shot(page, "25a-list-filled")
    print("DIALOG TEXT:\n", page.inner_text("body")[-1500:])
    page.click("button:has-text('Save changes')", timeout=10000)
    page.wait_for_timeout(5000)
    shot(page, "25b-list-saved")
    print("AFTER SAVE:\n", page.inner_text("body")[-2500:])
