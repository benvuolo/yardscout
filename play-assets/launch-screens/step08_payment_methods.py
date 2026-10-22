import sys
sys.path.insert(0, "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/launch-screens")
from _cdp import get_page, shot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page = get_page(p)
    target = None
    for f in page.frames:
        if "embedded_landing_page" in f.url:
            target = f
    if not target:
        print("No payments frame found"); sys.exit(1)
    target.click("text=Manage payment methods", timeout=15000)
    page.wait_for_timeout(7000)
    shot(page, "08-payment-methods")
    for f in page.frames:
        if "payments.google.com" in f.url and "auth_warmup" not in f.url:
            try:
                txt = f.inner_text("body")
                if txt.strip():
                    print("=== FRAME", f.url[:90], "===")
                    print(txt[:3000])
            except Exception as e:
                print("err", e)
