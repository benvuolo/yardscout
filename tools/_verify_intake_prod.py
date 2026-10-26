#!/usr/bin/env python3
"""Production check for the intake-system catalog release (jh-v69).

Owner acceptance: Parts tab search 'intake' -> pick 1998 Toyota 4Runner ->
donor cars with honest tiers (3rd-gen = 3RZ/5VZ families, all Likely — no
published manifold application lists exist). Verifies at 390px (phone):

 1. 'intake' surfaces BOTH categories (Intake manifold + Air intake / airbox)
 2. synonyms resolve: air cleaner / air box / airbox / intake manifold
 3. manifold fitment: 98 4Runner -> engine chips -> 5VZ -> Likely-tier donors,
    zero Verified, casting verify note + California/throttle caveat visible
 4. airbox fitment: same car -> same-gen (96-02) donor rows, never empty

Zip 95670 (Rancho Cordova, CA) — densest 96-02 Toyota-truck donor pool at
scan time. Run:  ~/projects/sigma-mcp/.venv/bin/python tools/_verify_intake_prod.py
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "https://yardscout.io/")
ZIP = os.environ.get("YS_ZIP", "95670")
SHOTS = "/tmp/yardscout-prod-intake"
os.makedirs(SHOTS, exist_ok=True)
FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def fresh_page(browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              device_scale_factor=2, is_mobile=True,
                              has_touch=True)
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('jh_honesty_ack', '1');")
    page.goto(BASE, wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", ZIP)
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=45000)
    page.click(".tab[data-tab='parts']")
    page.wait_for_timeout(500)
    return ctx, page


def suggest_labels(page, query):
    page.fill("#pf-part", "")
    page.wait_for_timeout(150)
    page.fill("#pf-part", query)
    page.wait_for_timeout(400)
    items = page.locator("#pf-part-suggest .compare-suggest-item")
    return [items.nth(i).inner_text() for i in range(items.count())]


def pick_category(page, query, label):
    page.fill("#pf-part", "")
    page.wait_for_timeout(150)
    page.fill("#pf-part", query)
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item",
                           timeout=8000)
    items = page.locator("#pf-part-suggest .compare-suggest-item")
    for i in range(items.count()):
        if label in items.nth(i).inner_text():
            items.nth(i).dispatch_event("mousedown")
            page.wait_for_timeout(600)
            return True
    return False


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx, page = fresh_page(browser)

    # 1. 'intake' surfaces both categories
    labels = suggest_labels(page, "intake")
    check("'intake' surfaces Intake manifold",
          any("Intake manifold" in x for x in labels), str(labels))
    check("'intake' surfaces Air intake / airbox",
          any("Air intake / airbox" in x for x in labels), str(labels))
    page.screenshot(path=f"{SHOTS}/1_intake_suggest_390.png")

    # 2. synonyms
    for q, want in [("air cleaner", "Air intake / airbox"),
                    ("air box", "Air intake / airbox"),
                    ("airbox", "Air intake / airbox"),
                    ("intake manifold", "Intake manifold")]:
        ls = suggest_labels(page, q)
        check(f"synonym '{q}' resolves to {want}",
              any(want in x for x in ls), str(ls))

    # 3. manifold fitment: 1998 Toyota 4Runner
    check("picked Intake manifold", pick_category(page, "intake", "Intake manifold"))
    page.select_option("#pf-year", "1998")
    page.select_option("#pf-make", "Toyota")
    page.wait_for_timeout(400)
    page.select_option("#pf-model", "4Runner")
    page.click("#pf-go")
    page.wait_for_timeout(1200)
    chips = page.locator("#pf-engine .pf-chip")
    chip_txt = " | ".join(chips.nth(i).inner_text() for i in range(chips.count()))
    check("98 4Runner -> engine chips offered (multi-engine model)",
          chips.count() >= 3, chip_txt)   # 3RZ + 5VZ + "not listed"
    check("chips include 3RZ and 5VZ families",
          "3RZ" in chip_txt and "5VZ" in chip_txt, chip_txt)
    page.screenshot(path=f"{SHOTS}/2_manifold_chips_390.png")
    for i in range(chips.count()):
        if "5VZ" in chips.nth(i).inner_text():
            chips.nth(i).click()
            break
    page.wait_for_timeout(1200)
    rows = page.locator("#pf-results .pf-row-card")
    likely = page.locator("#pf-results .pf-tier-likely")
    verified = page.locator("#pf-results .pf-tier-verified")
    check("manifold: donor rows returned", rows.count() > 0,
          page.locator("#pf-results").inner_text()[:160])
    check("manifold: every donor is Likely tier (no vg evidence shipped)",
          likely.count() == rows.count() and verified.count() == 0,
          f"{rows.count()} rows / {likely.count()} likely / {verified.count()} verified")
    body = page.locator("#pf-results").inner_text()
    check("manifold: casting verify warning on rows", "casting" in body)
    check("manifold: California-emissions / throttle caveat visible",
          "California" in body and "throttle" in body)
    page.screenshot(path=f"{SHOTS}/3_manifold_donors_390.png", full_page=False)
    page.locator("#pf-results .pf-row-card").first.scroll_into_view_if_needed()
    page.screenshot(path=f"{SHOTS}/4_manifold_rows_390.png")

    # 4. airbox fitment: same car — fresh context so no sticky engine state
    ctx.close()
    ctx, page = fresh_page(browser)
    check("picked Air intake / airbox",
          pick_category(page, "airbox", "Air intake / airbox"))
    page.select_option("#pf-year", "1998")
    page.select_option("#pf-make", "Toyota")
    page.wait_for_timeout(400)
    page.select_option("#pf-model", "4Runner")
    page.click("#pf-go")
    page.wait_for_timeout(1200)
    rows = page.locator("#pf-results .pf-row-card")
    likely = page.locator("#pf-results .pf-tier-likely")
    body = page.locator("#pf-results").inner_text()
    check("airbox: donor rows returned (not empty)", rows.count() > 0,
          body[:160])
    check("airbox: all Likely tier (generation window, class B)",
          likely.count() == rows.count(),
          f"{rows.count()} rows / {likely.count()} likely")
    check("airbox: same-generation provenance on rows",
          "generation" in body)
    check("airbox: engine-size/MAF honesty note visible",
          "MAF" in body or "engine size" in body)
    page.screenshot(path=f"{SHOTS}/5_airbox_donors_390.png")

    ctx.close()
    browser.close()

print("FAILS:", FAILS if FAILS else "none")
print("shots:", SHOTS)
raise SystemExit(1 if FAILS else 0)
