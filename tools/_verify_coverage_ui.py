#!/usr/bin/env python3
"""Coverage-request UI flow check (Parts tab "ask us to add it").

Runs against the local docs/ served on :8765 (CORS-allowed origin) with the
PRODUCTION API — submissions land in the real coverage_requests table under
a throwaway e2e email and are deleted afterwards by exact request_key.

Covers all three uncovered states:
  car    — 2000 Daewoo Lanos alternator (make absent from interchange table)
  engine — 2005 Toyota Camry alternator + "My engine isn't listed" chip
  part   — "flux capacitor" typed into the part combobox

Run:  .venv/bin/python tools/_verify_coverage_ui.py
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("YS_BASE", "http://localhost:8765/index.html")
SHOTS = "/tmp/ys-coverage-ui"
os.makedirs(SHOTS, exist_ok=True)
TEST_EMAIL = "coverage-e2e@yardscout-test.example"
FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 860, "height": 900})
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('jh_honesty_ack', '1');")
    page.goto(BASE, wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "84101")
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card", timeout=45000)

    # ── 1. car not covered: 2000 Daewoo Lanos alternator ────────────────────
    page.click(".tab[data-tab='parts']")
    page.wait_for_timeout(600)
    page.fill("#pf-part", "alternator")
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item", timeout=8000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(500)
    page.select_option("#pf-year", "2000")
    page.select_option("#pf-make", "Daewoo")
    page.wait_for_timeout(400)
    page.select_option("#pf-model", "Lanos")
    page.click("#pf-go")
    page.wait_for_timeout(800)
    empty = page.locator("#pf-results .pf-empty")
    ask = page.locator("#pf-results .pfc-ask")
    check("car: honest empty state shows", empty.count() == 1, empty.inner_text() if empty.count() else "no empty state")
    check("car: quiet ask link present", ask.count() == 1)
    page.screenshot(path=f"{SHOTS}/1-car-empty-with-ask.png")

    ask.click()
    page.wait_for_selector("#pf-coverage-form", timeout=4000)
    what = page.locator(".pfc-what").inner_text()
    check("car: form prefilled with car + part", "2000 Daewoo Lanos" in what and "Alternator" in what, what)
    check("car: form prefilled with zip", "84101" in what, what)
    page.screenshot(path=f"{SHOTS}/2-car-form-prefilled.png")

    page.fill("#pfc-email", TEST_EMAIL)
    page.fill("#pfc-note", "ui e2e — delete me")
    page.click("#pfc-send")
    page.wait_for_selector(".pfc-thanks", timeout=10000)
    thanks = page.locator(".pfc-thanks").inner_text()
    check("car: thank-you in the muted voice", "Added to the list" in thanks, thanks)
    page.screenshot(path=f"{SHOTS}/3-car-thanks.png")

    # ── 2. engine not listed: 05 Camry + "My engine isn't listed" ──────────
    page.select_option("#pf-year", "2005")
    page.select_option("#pf-make", "Toyota")
    page.wait_for_timeout(400)
    page.select_option("#pf-model", "Camry")
    page.click("#pf-go")
    page.wait_for_timeout(1000)
    none_chip = page.locator("#pf-engine .pf-chip", has_text="isn’t listed")
    check("engine: escape-hatch chip offered", none_chip.count() == 1)
    if none_chip.count():
        none_chip.click()
        page.wait_for_timeout(600)
        ask2 = page.locator("#pf-results .pfc-ask")
        check("engine: ask link in the not-listed state", ask2.count() == 1)
        page.screenshot(path=f"{SHOTS}/4-engine-empty-with-ask.png")
        ask2.click()
        page.wait_for_selector("#pf-coverage-form", timeout=4000)
        ph = page.locator("#pfc-note").get_attribute("placeholder")
        check("engine: note asks which engine", "which engine" in (ph or ""), ph)
        page.screenshot(path=f"{SHOTS}/5-engine-form.png")

    # ── 3. part not in catalog: flux capacitor ──────────────────────────────
    page.fill("#pf-part", "flux capacitor")
    page.wait_for_timeout(400)
    sugg_ask = page.locator("#pf-part-suggest .pfc-ask")
    check("part: ask link inside the no-match dropdown", sugg_ask.count() == 1)
    page.screenshot(path=f"{SHOTS}/6-part-suggest-with-ask.png")
    sugg_ask.dispatch_event("mousedown")
    page.wait_for_selector("#pf-coverage-form", timeout=4000)
    what3 = page.locator(".pfc-what").inner_text()
    check("part: form prefilled with the typed part", "flux capacitor" in what3, what3)
    page.fill("#pfc-email", TEST_EMAIL)
    page.fill("#pfc-note", "ui e2e — delete me")
    page.click("#pfc-send")
    page.wait_for_selector(".pfc-thanks", timeout=10000)
    page.screenshot(path=f"{SHOTS}/7-part-thanks.png")
    check("part: submitted", page.locator(".pfc-thanks").count() == 1)

    browser.close()

print()
print("FAILS:", FAILS if FAILS else "none")
raise SystemExit(1 if FAILS else 0)
