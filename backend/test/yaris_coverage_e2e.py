#!/usr/bin/env python3
"""Browser e2e for the 2026-10-23 coverage run's owner repro.

The owner's miss: a 2006 Toyota Yaris answered "no parts" on the Parts
tab. The toyota-1nz window now opens at 2006 (Canadian-market MY2006 XP90)
— an alternator search for it must return donor rows. Also spot-checks a
2016 Yaris (XP130, Verified-capable) and a 2015 Sentra (new nissan-mra8).

    ~/projects/sigma-mcp/.venv/bin/python backend/test/yaris_coverage_e2e.py

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
PORT = 8627
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


def pf_search(page, year, make, model_candidates, part="alternator"):
    page.fill("#pf-part", part)
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
                      for m in model_candidates if m.lower() in o.lower()),
                     None)
    if model is None:
        return None
    page.select_option("#pf-model", model)
    page.click("#pf-go")
    page.wait_for_timeout(800)
    return model


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(**IPHONE)
    page = ctx.new_page()
    page.add_init_script(PRO_BOOT)
    page.goto(f"http://127.0.0.1:{PORT}/index.html",
              wait_until="domcontentloaded")
    page.click("#live-filter-toggle")
    page.fill("#live-zip", "90670")  # Santa Fe Springs — Monrovia/LA yards
    # hold ~22 Yaris/Echo/xA/xB donors within Pro radius
    page.wait_for_selector("#live-grid .match-card, #live-grid .dim-card",
                           timeout=30000)
    page.click("#live-filter-toggle")
    page.click(".tab[data-tab='parts']")
    page.wait_for_selector("#tab-parts.active #pf-body", state="visible")

    # --- the owner's repro: 2006 Yaris alternator -------------------------
    model = pf_search(page, "2006", "Toyota", ["Yaris"])
    check("yaris06: model option found", model is not None)
    rows = page.locator("#pf-results .pf-row-card")
    check("yaris06: donor rows render (the owner's miss, fixed)",
          rows.count() > 0,
          page.locator("#pf-results").inner_text()[:150])
    if rows.count():
        head = page.locator("#pf-results .pf-tier-counts").inner_text()   # toggle row under the head
        check("yaris06: head reports the verified/likely split",
              "likely" in head.lower(), head[:120])
        # No published 2006 row exists — every donor must be Likely, none
        # Verified (honesty check on the Canadian-MY argument).
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("yaris06: donors are honestly Likely-only", n_ver == 0,
              f"ver={n_ver}")
        page.evaluate("document.getElementById('pf-results')"
                      ".scrollIntoView({block:'start'})")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "yaris06_alternator.png"),
                        full_page=False)
        print(f"  shot: {SHOTS}/yaris06_alternator.png")

    # --- 2016 Yaris: the XP130 extension, Verified-capable ---------------
    model = pf_search(page, "2016", "Toyota", ["Yaris"])
    check("yaris16: model option found", model is not None)
    rows = page.locator("#pf-results .pf-row-card")
    check("yaris16: donor rows render", rows.count() > 0)

    # --- 2015 Sentra: the new nissan-mra8 family, starter ----------------
    model = pf_search(page, "2015", "Nissan", ["Sentra"], part="starter")
    check("sentra15: model option found", model is not None)
    rows = page.locator("#pf-results .pf-row-card")
    check("sentra15: starter donors render (new mra8 family)",
          rows.count() > 0)
    if rows.count():
        n_ver = page.locator("#pf-results .pf-row-card.pf-verified").count()
        check("sentra15: at least one Verified starter donor (280-3139)",
              n_ver > 0, f"ver={n_ver}")
        page.screenshot(path=str(SHOTS / "sentra15_starter.png"))
        print(f"  shot: {SHOTS}/sentra15_starter.png")

    browser.close()

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print("yaris coverage e2e passed")
