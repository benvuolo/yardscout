#!/usr/bin/env python3
"""Browser e2e for part-first interchange search v2.

Flows the task demands: an alternator search for a 2005 Toyota Camry, a
1999 Ford F-150, and a 2016 Subaru WRX — each must return donor rows with
honest two-tier confidence chips. Starts its own static server over docs/
and drives Chromium at an iPhone viewport.

    ~/projects/sigma-mcp/.venv/bin/python backend/test/part_finder_e2e.py

Screenshots land in /tmp/yardscout_shots/.
"""
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SHOTS = pathlib.Path("/tmp/yardscout_shots")
SHOTS.mkdir(exist_ok=True)
PORT = 8619
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    print(("ok   " if cond else "FAIL ") + name
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    def log_message(self, *a):
        pass


threading.Thread(
    target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    .serve_forever, daemon=True).start()

IPHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3,
          "is_mobile": True, "has_touch": True}
PRO_BOOT = """
  localStorage.setItem('jh_pro', '1');
  localStorage.setItem('jh_pro_source', 'account');
  localStorage.setItem('jh_honesty_ack', '1');
"""

CARS = [
    # (slug, year, make, model-option candidates, engine-chip substring,
    #  expect_verified)
    ("camry05", "2005", "Toyota", ["Camry"], "2AZ", True),
    ("f150_99", "1999", "Ford", ["F-150", "F150 Pickup", "F150"], "5.4", True),
    ("wrx16", "2016", "Subaru", ["WRX"], None, True),
]


def pf_search(page, year, make, model_candidates, engine_chip):
    page.fill("#pf-part", "alternator")
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item",
                           timeout=5000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event(
        "mousedown")
    page.select_option("#pf-year", year)
    page.select_option("#pf-make", make)
    page.wait_for_timeout(200)
    opts = page.eval_on_selector_all(
        "#pf-model option", "os => os.map(o => o.value)")
    model = next((m for m in model_candidates if m in opts), None)
    if model is None:
        model = next((o for o in opts
                      for m in model_candidates if m.lower() in o.lower()), None)
    if model is None:
        return None
    page.select_option("#pf-model", model)
    page.click("#pf-go")
    page.wait_for_timeout(600)
    # Multi-engine models ask "which engine is in YOUR car?" — answer it.
    if engine_chip and page.locator("#pf-engine .pf-chip").count():
        chips = page.locator("#pf-engine .pf-chip")
        for i in range(chips.count()):
            if engine_chip.lower() in chips.nth(i).inner_text().lower():
                chips.nth(i).click()
                break
        page.wait_for_timeout(600)
    return model


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(**IPHONE)
    page = ctx.new_page()
    page.add_init_script(PRO_BOOT)
    page.goto(f"http://127.0.0.1:{PORT}/index.html",
              wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "85003")   # Phoenix — Pull-N-Save holds
    # verified-span WRX donors (2016/2018 at Phoenix South, 2015 Gilbert)
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=30000)
    page.click("#live-filter-toggle")

    page.click("#pf-toggle")
    page.wait_for_selector("#pf-body", state="visible")

    for slug, year, make, models, engine_chip, expect_verified in CARS:
        model = pf_search(page, year, make, models, engine_chip)
        check(f"{slug}: model option found", model is not None, str(models))
        if model is None:
            continue
        rows = page.locator("#pf-results .pf-row-card")
        check(f"{slug}: donor rows render", rows.count() > 0,
              page.locator("#pf-results").inner_text()[:120])
        if not rows.count():
            continue
        head = page.locator("#pf-results .pf-results-head").inner_text()
        check(f"{slug}: head reports verified/likely split",
              "verified" in head and "likely" in head, head[:120])
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        n_lik = page.locator("#pf-results .pf-row-card.pf-likely").count()
        if expect_verified:
            check(f"{slug}: at least one Verified-fit donor", n_ver > 0,
                  f"ver={n_ver} lik={n_lik}")
        chips = page.locator("#pf-results .pf-tier").count()
        check(f"{slug}: every row carries a tier chip",
              chips == rows.count(), f"{chips} chips / {rows.count()} rows")
        # Sorted by distance then confidence — distances must be
        # non-decreasing down the list.
        dists = page.eval_on_selector_all(
            "#pf-results .pf-row-card .dist",
            "els => els.map(e => parseInt(e.textContent))")
        check(f"{slug}: rows sorted by distance",
              all(a <= b for a, b in zip(dists, dists[1:])), str(dists[:8]))
        page.evaluate("document.getElementById('pf-results')"
                      ".scrollIntoView({block:'start'})")
        page.wait_for_timeout(250)
        page.screenshot(path=str(SHOTS / f"pf_{slug}_alternator.png"))
        print(f"     ver={n_ver} lik={n_lik} — "
              f"shot pf_{slug}_alternator.png")

    ctx.close()
    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print(f"all part-finder e2e tests passed — screenshots in {SHOTS}/")
