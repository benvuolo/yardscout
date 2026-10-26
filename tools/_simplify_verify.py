#!/usr/bin/env python3
"""Owner-approved simplification batch verification (2026-10-26).

Usage: python3 tools/_simplify_verify.py [BASE] [TAG]
  BASE defaults to https://yardscout.io ; TAG names the output dir.

Per engine (chromium, webkit) x width (390, 360):
  1. Fresh profile: tab-bar labels, filter badge hidden.
  2. Enter zip (default radius): badge still hidden (post-fix) / shown (pre-fix).
  3. Change radius 100 -> 50: badge shows 1.
  4. Stats chips: capture the 3-chip row text (Worth a look vs New this week).
  5. Yards + Parts tabs: badge states + every placeholder, truncation check.
Shots land in tools/_simplify_shots_{TAG}/ ; findings print as JSON.
"""
import sys, json, os
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://yardscout.io"
TAG = sys.argv[2] if len(sys.argv) > 2 else "before"
OUT = f"tools/_simplify_shots_{TAG}"
os.makedirs(OUT, exist_ok=True)
ZIP = "30301"  # Atlanta — dense coverage

report = {}

def badge_state(page, el_id):
    return page.evaluate(f"""() => {{
      const el = document.getElementById('{el_id}');
      return {{shown: el && el.style.display !== 'none', text: el ? el.textContent : null}};
    }}""")

with sync_playwright() as p:
    for engine in ("chromium", "webkit"):
        browser = getattr(p, engine).launch()
        for w, h in ((390, 844), (360, 800)):
            key = f"{engine}_{w}"
            ctx = browser.new_context(viewport={"width": w, "height": h},
                                      device_scale_factor=2, is_mobile=(engine == "chromium"),
                                      has_touch=True)
            page = ctx.new_page()
            page.goto(BASE, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)
            r = {}
            r["tabs"] = page.eval_on_selector_all(
                ".tabs .tab .tab-label", "els => els.map(e => e.textContent)")
            r["badge_fresh_no_zip"] = badge_state(page, "live-filter-count")
            # Dismiss first-run note if present, then enter zip via the banner.
            if page.locator("#first-run-dismiss").is_visible():
                page.click("#first-run-dismiss")
            if page.locator("#zip-banner-input").is_visible():
                page.fill("#zip-banner-input", ZIP)
                page.click("#zip-banner-go")
            else:
                page.click("#live-filter-toggle")
                page.fill("#live-zip", ZIP)
            page.wait_for_timeout(2500)
            page.screenshot(path=f"{OUT}/{key}_1_cars_fresh_zip.png")
            r["badge_default_radius"] = badge_state(page, "live-filter-count")
            r["stats_chips"] = page.eval_on_selector_all(
                "#live-stats-bar .stat-card",
                "els => els.map(e => e.innerText.replace(/\\n/g,' | '))")
            # Change radius from the 100 mi default -> badge should appear.
            if not page.locator("#live-controls.open").count():
                page.click("#live-filter-toggle")
            page.wait_for_timeout(400)
            page.select_option("#live-radius", "50")
            page.wait_for_timeout(1200)
            r["badge_after_radius_change"] = badge_state(page, "live-filter-count")
            page.screenshot(path=f"{OUT}/{key}_2_cars_radius_changed.png")
            # Back to default -> badge should clear again (post-fix).
            page.select_option("#live-radius", "100")
            page.wait_for_timeout(800)
            r["badge_back_to_default"] = badge_state(page, "live-filter-count")

            # Yards tab
            page.click(".tab[data-tab='yards']")
            page.wait_for_timeout(1200)
            r["yards_badge_default"] = badge_state(page, "yards-filter-count")
            page.screenshot(path=f"{OUT}/{key}_3_yards.png")

            # Parts tab + placeholder audit (all tabs' inputs, truncation check)
            page.click(".tab[data-tab='parts']")
            page.wait_for_timeout(800)
            page.screenshot(path=f"{OUT}/{key}_4_parts.png")
            r["placeholders"] = page.evaluate("""() =>
              [...document.querySelectorAll('input[placeholder]')].map(i => {
                let clipped = null;
                if (i.offsetWidth) {
                  const s = getComputedStyle(i);
                  const c = document.createElement('canvas').getContext('2d');
                  c.font = `${s.fontSize} ${s.fontFamily}`;
                  const tw = c.measureText(i.placeholder).width;
                  const inner = i.clientWidth - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight);
                  clipped = tw > inner + 1;
                }
                return {id: i.id, ph: i.placeholder, visible: !!i.offsetWidth, clipped};
              })""")
            r["sw_version"] = page.evaluate(
                "() => fetch('sw.js').then(r => r.text()).then(t => (t.match(/jh-v\\d+/)||[null])[0])")
            report[key] = r
            ctx.close()
        browser.close()

print(json.dumps(report, indent=2))
with open(f"{OUT}/report.json", "w") as f:
    json.dump(report, f, indent=2)
