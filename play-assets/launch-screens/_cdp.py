"""Shared CDP helper for Play Console launch-day automation."""
import sys, time
from playwright.sync_api import sync_playwright

SHOTS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens"

def get_page(p, prefer=None):
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    if prefer:
        for pg in ctx.pages:
            if prefer in pg.url:
                return browser, pg
    # Reuse an existing play console page if present, else new
    for pg in ctx.pages:
        if "play.google.com/console" in pg.url:
            return browser, pg
    return browser, ctx.new_page()

def shot(page, name):
    path = f"{SHOTS}/{name}.png"
    page.screenshot(path=path, full_page=False)
    print(f"SCREENSHOT {path}")
