"""Navigate (again) to Main store listing; fall back to clicking through the
app card + left nav if the deep link bounces to home."""
from playwright.sync_api import sync_playwright
from _cdp import get_page, shot, LISTING_URL

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)
    assert page, "our console tab not found"
    page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    print("URL after goto:", page.url)
    if "main-store-listing" not in page.url:
        # Click through: app row -> Grow users -> Store presence -> listing
        page.get_by_text("YardScout: Junkyard Inventory").first.click()
        page.wait_for_timeout(5000)
        print("URL after app click:", page.url)
        page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(7000)
        print("URL retry:", page.url)
    shot(page, "02-listing-page")
