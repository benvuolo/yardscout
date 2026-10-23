#!/usr/bin/env python3
"""Post-merge production check for the interchange release (yardscout.io).

Covers the release checklist: Parts tab present, fitment flow (05 Camry
alternator), browse mode (engine hunt), Live drawer has no spotted-part
field but keeps the -> Parts pointer.

Run:  ~/projects/sigma-mcp/.venv/bin/python tools/_verify_prod_interchange.py
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "https://yardscout.io/")
SHOTS = "/tmp/yardscout-prod-interchange"
os.makedirs(SHOTS, exist_ok=True)
FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('jh_honesty_ack', '1');")
    page.goto(BASE, wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "30310")
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card", timeout=45000)

    # 1. Parts tab present
    tab = page.locator(".tab[data-tab='parts']")
    check("Parts tab present", tab.count() == 1)

    # 2. Fitment flow: 05 Camry alternator
    tab.click()
    page.wait_for_timeout(500)
    page.fill("#pf-part", "alternator")
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item", timeout=8000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(700)
    page.select_option("#pf-year", "2005")
    page.select_option("#pf-make", "Toyota")
    page.wait_for_timeout(400)
    page.select_option("#pf-model", "Camry")
    page.click("#pf-go")
    page.wait_for_timeout(1200)
    if (not page.locator("#pf-results .pf-row-card").count()
            and page.locator("#pf-engine .pf-chip").count()):
        page.locator("#pf-engine .pf-chip").first.click()
        page.wait_for_timeout(1000)
    rows = page.locator("#pf-results .pf-row-card")
    tiers = page.locator("#pf-results .pf-tier")
    check("fitment: 05 Camry alternator -> tiered donor rows",
          rows.count() > 0 and tiers.count() > 0,
          f"{rows.count()} rows / {tiers.count()} tiers; " +
          page.locator("#pf-results").inner_text()[:140])
    page.screenshot(path=f"{SHOTS}/1_camry_alternator.png")

    # 3. Browse mode: engine hunt (no car) — fresh context so no saved car
    ctx.close()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('jh_honesty_ack', '1');")
    page.goto(BASE, wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "30310")
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card", timeout=45000)
    page.click(".tab[data-tab='parts']")
    page.wait_for_timeout(500)
    page.fill("#pf-part", "engine assembly")
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item", timeout=8000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(900)
    check("engine browse: family picker renders", page.locator("#pf-browse-fam").count() == 1)
    fam_val = page.evaluate("""() => {
      const os = [...document.querySelectorAll('#pf-browse-fam option')];
      const o = os.find(o => o.textContent.includes('5.3'));
      return o ? o.value : '';
    }""")
    check("engine browse: 5.3 family present", bool(fam_val))
    if fam_val:
        page.select_option("#pf-browse-fam", fam_val)
        page.wait_for_timeout(1000)
        check("engine browse: 5.3 donors render",
              page.locator("#pf-results .pf-row-card.pf-browse").count() > 0,
              page.locator("#pf-results").inner_text()[:140])
    page.screenshot(path=f"{SHOTS}/2_engine_browse.png")

    # 4. Live drawer: no spotted-part field; -> Parts pointer present
    page.click(".tab[data-tab='live']")
    page.wait_for_timeout(400)
    if not page.locator("#live-controls.open").count():
        page.click("#live-filter-toggle")
        page.wait_for_timeout(400)
    check("drawer: spotted-part field removed", page.locator("#live-part-search").count() == 0)
    pointer = page.locator("#live-parts-pointer")
    check("drawer: -> Parts pointer present",
          pointer.count() == 1 and "Parts" in pointer.inner_text())
    page.screenshot(path=f"{SHOTS}/3_drawer.png")

    ctx.close()
    browser.close()

print("FAILS:", FAILS if FAILS else "none")
raise SystemExit(1 if FAILS else 0)
