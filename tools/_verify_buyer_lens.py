#!/usr/bin/env python3
"""Buyer-lens copy verification: load the app (local or prod), unlock Pro,
expand a Live card's parts, run a Parts-tab browse search, open the compare
sheet — screenshot each at phone + desktop widths and assert the new copy."""
import sys, time
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8742"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"
OUT = f"tools/_buyer_lens_shots_{TAG}"

import os
os.makedirs(OUT, exist_ok=True)

ZIP = "30301"  # Atlanta — dense Pull-A-Part coverage, published price lists

def run(width, height, label):
    results = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": height})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(BASE + "/index.html", wait_until="domcontentloaded")
        pg.evaluate("""() => {
            localStorage.setItem('jh_pro', '1');
            localStorage.setItem('jh_pro_source', 'iap');
            localStorage.setItem('jh_honesty_ack', '1');
            localStorage.setItem('jh_zip', '%s');
        }""" % ZIP)
        pg.reload(wait_until="domcontentloaded")
        # Enter zip if the banner is still up
        try:
            zi = pg.locator("#zip-banner-input")
            if zi.is_visible(timeout=3000):
                zi.fill(ZIP)
                pg.locator("#zip-banner-go").click()
        except Exception:
            pass
        pg.wait_for_selector(".car-card", timeout=90000)
        time.sleep(1.5)

        # --- 1. Live card expanded parts: find a card whose parts include a
        # priced row (Save ~ visible) ---
        cards = pg.locator(".car-card .parts-details summary")
        n = min(cards.count(), 25)
        best = None
        for i in range(n):
            cards.nth(i).click()
            time.sleep(0.25)
            card = cards.nth(i).locator("xpath=ancestor::details")
            if card.locator(".part-save").count() > 0:
                best = i
                break
        if best is None and n:
            best = 0
            cards.nth(0).click()
        time.sleep(0.5)
        card_el = cards.nth(best).locator("xpath=ancestor::div[contains(@class,'car-card')]")
        card_el.scroll_into_view_if_needed()
        card_el.screenshot(path=f"{OUT}/live-card-{label}.png")
        html = card_el.inner_html()
        results["live_used_online"] = "Used online:" in html
        results["live_save"] = "Save ~" in html
        results["live_no_spares_sell"] = "Spares sell on" not in html

        # --- 2. Parts tab browse result ---
        pg.locator(".tab[data-tab='parts']").click()
        time.sleep(0.5)
        pg.locator("#pf-part").click()
        pg.locator("#pf-part").fill("headlight")
        time.sleep(1.0)
        try:
            pg.locator("#pf-part-suggest .suggest-item, #pf-part-suggest [role='option']").first.click()
        except Exception:
            pg.keyboard.press("Enter")
        time.sleep(2.5)
        rows = pg.locator(".pf-row-card")
        if rows.count():
            rows.first.scroll_into_view_if_needed()
            pg.screenshot(path=f"{OUT}/parts-tab-{label}.png")
            body = pg.locator("#pf-results").inner_html()
            results["pf_used_online"] = "Used online:" in body
            results["pf_yard_prefix"] = "Yard: $" in body
            results["pf_save"] = "save ~" in body
        else:
            pg.screenshot(path=f"{OUT}/parts-tab-{label}.png")
            results["pf_rows"] = 0

        # --- 3. Compare sheet (Yards tab price compare) ---
        pg.locator(".tab[data-tab='yards']").click()
        time.sleep(1.0)
        try:
            pg.locator("#compare-input").fill("headlight")
            pg.locator("#compare-go").click()
            pg.wait_for_selector("#prices-sheet.open", timeout=8000)
            time.sleep(0.8)
            pg.screenshot(path=f"{OUT}/compare-sheet-{label}.png")
            sheet = pg.locator("#prices-sheet").inner_html()
            results["compare_ok"] = "published price list" in sheet
        except Exception as e:
            results["compare_err"] = str(e)[:120]
            pg.screenshot(path=f"{OUT}/compare-sheet-{label}.png")

        results["pageerrors"] = errors
        b.close()
    return results

for w, h, label in [(390, 844, "phone"), (1280, 900, "desktop")]:
    r = run(w, h, label)
    print(label, "->")
    for k, v in r.items():
        print("   ", k, "=", v)
