#!/usr/bin/env python3
"""One-shot Playwright check: the 'Show' filter renders on WEB, carries the
honest confirmed-only manual option, reveals the inline hint when selected,
and actually narrows the grid to confirmed-manual cars.

Run:  ../.venv/bin/python scraper/_verify_show_filter.py   (from repo root ok)
Serves docs/ itself on :8793; writes screenshots next to this file.
"""

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8793
URL = f"http://127.0.0.1:{PORT}/"
OUT = Path(__file__).resolve().parent / ".out-show-filter"
OUT.mkdir(exist_ok=True)

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


server = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
    cwd=ROOT / "docs", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(URL, wait_until="domcontentloaded")
        # Wait for inventory to load (stat cards replace the skeleton chips).
        page.wait_for_selector("#live-stats-bar .stat-card", timeout=120000)

        # Open the Filters drawer (collapsed by default on every platform).
        page.click("#live-filter-toggle")
        check("filters drawer opens", page.is_visible("#live-controls"))

        sel = page.locator("#live-filter-match")
        check("'Show' select renders on web", sel.is_visible())
        opts = sel.locator("option").all_text_contents()
        check("valuable-parts option intact", "Only cars with valuable parts" in opts, str(opts))
        check("manual option says confirmed-only",
              "Manual transmission (confirmed only)" in opts, str(opts))
        check("old overclaiming label gone",
              not any("VIN-confirmed" in o for o in opts), str(opts))

        # Hint hidden until the manual option is chosen.
        check("hint hidden by default", not page.is_visible("#manual-filter-hint"))

        # Unlock filters with a zip, then choose the manual filter.
        page.fill("#live-zip", "84101")
        page.wait_for_function("!document.getElementById('live-filter-match').disabled", timeout=15000)
        sel.select_option("manual")
        check("hint appears when manual selected", page.is_visible("#manual-filter-hint"))
        hint = page.text_content("#manual-filter-hint") or ""
        check("hint names both provenance sources",
              "VIN decode" in hint and "listing" in hint, hint)
        check("hint admits the under-count", "won\u2019t appear" in hint or "won't appear" in hint, hint)

        # The grid should narrow to confirmed-manual cars (Manual badge on each).
        page.wait_for_timeout(1500)
        cards = page.locator("#live-grid .car-card")
        n = cards.count()
        badges = page.locator("#live-grid .badge-manual").count()
        check("manual filter yields cards", n > 0, f"{n} cards")
        check("every shown card carries the Manual badge", n == badges, f"{n} cards vs {badges} badges")

        page.screenshot(path=str(OUT / "web_manual_filter.png"))
        # Close-up of the control group with the hint.
        page.locator("#live-filter-match").scroll_into_view_if_needed()
        page.locator("div.ctl", has=page.locator("#live-filter-match")).screenshot(
            path=str(OUT / "web_show_control.png"))
        browser.close()
finally:
    server.terminate()

print()
if failed:
    print(f"{len(failed)} FAILURE(S): {failed}")
    sys.exit(1)
print(f"all {len(passed)} web filter checks passed — screenshots in {OUT}")
