"""Confirm production release state: is 6 (1.2) Published/live?
Read-only — screenshots of publishing overview + production track."""
from playwright.sync_api import sync_playwright
from _cdp import shot

APP = ("https://play.google.com/console/u/0/developers/9052149026359320771"
       "/app/4975171430765358175")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = next((pg for pg in ctx.pages
                 if "play.google.com/console" in pg.url
                 and "submission-activity" not in pg.url), None)

    page.goto(APP + "/publishing", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    body = page.evaluate("() => document.body.innerText")
    print("=== PUBLISHING OVERVIEW ===")
    print(body[:2200])
    shot(page, "24-publishing-overview")

    page.goto(APP + "/tracks/production", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(8000)
    body = page.evaluate("() => document.body.innerText")
    print("=== PRODUCTION TRACK ===")
    print(body[:2800])
    shot(page, "24-production-track")
