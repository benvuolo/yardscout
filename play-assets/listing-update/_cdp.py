"""Shared CDP helper for the store-listing update (own tab, never touches
the other agent's publishing tab)."""
import sys, time
from playwright.sync_api import sync_playwright

SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/listing-update"
LISTING_URL = ("https://play.google.com/console/u/0/developers/"
               "9052149026359320771/app/4975171430765358175/main-store-listing")

def get_page(p):
    """Connect over CDP and return (browser, page) — reusing OUR listing tab
    if a previous step opened it, else a brand-new tab."""
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    for pg in ctx.pages:
        if "main-store-listing" in pg.url:
            return browser, pg
    return browser, ctx.new_page()

def goto_listing(page):
    if "main-store-listing" not in page.url:
        page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)  # console SPA settle

def shot(page, name):
    path = f"{SHOTS}/{name}.png"
    page.screenshot(path=path, full_page=False)
    print(f"SCREENSHOT {path}", flush=True)
