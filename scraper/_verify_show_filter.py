#!/usr/bin/env python3
"""One-shot Playwright check of the 'Show' filter.

Verifies (against production by default, or a local docs/ server with
--local): the valuable-parts option is gone, the confirmed-only manual option
works as shipped, legacy state referencing the removed option degrades
gracefully (no stuck empty grid, no console errors), and every manual-filtered
card carries the Manual badge.

Run:  .venv/bin/python scraper/_verify_show_filter.py [--local]
Writes screenshots to scraper/.out-show-filter/.
"""

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LOCAL = "--local" in sys.argv
PORT = 8793
URL = f"http://127.0.0.1:{PORT}/" if LOCAL else "https://yardscout.io/"
OUT = Path(__file__).resolve().parent / ".out-show-filter"
OUT.mkdir(exist_ok=True)

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


server = None
if LOCAL:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT / "docs", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        # Legacy-state simulation: a stale client that still references the
        # removed 'valuable parts' option (hypothetical persisted key + the
        # filters drawer open, which is a real persisted key).
        page.add_init_script(
            "localStorage.setItem('jh_match', 'match');"
            "localStorage.setItem('jh_filters_open', '1');")

        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector("#live-stats-bar .stat-card", timeout=120000)

        sel = page.locator("#live-filter-match")
        check("'Show' select renders", sel.is_visible())
        values = sel.locator("option").evaluate_all("os => os.map(o => o.value)")
        texts = sel.locator("option").all_text_contents()
        check("exactly All cars + manual options", values == ["", "manual"], str(values))
        check("valuable-parts option removed", not any("valuable" in t.lower() for t in texts), str(texts))
        check("manual option says confirmed-only",
              "Manual transmission (confirmed only)" in texts, str(texts))
        check("select defaults to All cars", sel.evaluate("s => s.value") == "")

        # Unlock filters, confirm the default (All cars) shows results.
        page.fill("#live-zip", "84101")
        page.wait_for_function("!document.getElementById('live-filter-match').disabled", timeout=20000)
        page.wait_for_selector("#live-grid .car-card", timeout=20000)
        n_all = page.locator("#live-grid .car-card").count()
        check("default filter shows cars", n_all > 0, f"{n_all} cards")

        # Simulate a form-restore landing on the removed option: with no such
        # <option>, the select reads '' and the grid must NOT go empty.
        page.evaluate(
            "() => { const s = document.getElementById('live-filter-match');"
            " s.selectedIndex = -1; renderLive(); }")
        page.wait_for_timeout(800)
        check("invalid restored selection reads as All cars",
              page.evaluate("document.getElementById('live-filter-match').value") == "")
        n_after = page.locator("#live-grid .car-card").count()
        check("no stuck empty grid after invalid selection", n_after > 0, f"{n_after} cards")

        # Manual option still works exactly as shipped.
        sel.select_option("manual")
        check("hint appears when manual selected", page.is_visible("#manual-filter-hint"))
        hint = page.text_content("#manual-filter-hint") or ""
        check("hint names both provenance sources",
              "VIN decode" in hint and "listing" in hint, hint)
        page.wait_for_timeout(1200)
        n = page.locator("#live-grid .car-card").count()
        badges = page.locator("#live-grid .badge-manual").count()
        check("manual filter yields cards", n > 0, f"{n} cards")
        check("every shown card carries the Manual badge", n == badges, f"{n} vs {badges}")

        check("no console errors", not console_errors, "; ".join(console_errors[:3]))

        page.screenshot(path=str(OUT / (("local" if LOCAL else "prod") + "_show_filter.png")))
        browser.close()
finally:
    if server:
        server.terminate()

print()
if failed:
    print(f"{len(failed)} FAILURE(S): {failed}")
    sys.exit(1)
print(f"all {len(passed)} checks passed against {URL} — screenshots in {OUT}")
