#!/usr/bin/env python3
"""Visual uniformity audit: screenshot every tab + key sheets at phone/tablet/
desktop widths and flag horizontal overflow (elements poking past the viewport).

Usage: python3 tools/_qa_visual_audit.py [BASE] [TAG] [--native]
  BASE defaults to http://localhost:8742 (serve docs/ or native/www there).
  --native injects a Capacitor iOS mock (simulated webview spot-check).
Shots land in tools/_qa_shots_{TAG}/; an overflow report prints as JSON.
"""
import sys, time, json, os
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8742"
TAG = sys.argv[2] if len(sys.argv) > 2 else "local"
NATIVE = "--native" in sys.argv
OUT = f"tools/_qa_shots_{TAG}"
os.makedirs(OUT, exist_ok=True)
ZIP = "30301"  # Atlanta — dense coverage, published price lists

VIEWPORTS = [(360, 800), (390, 844), (430, 932), (768, 1024), (1280, 900)]

NATIVE_MOCK = """
window.Capacitor = {
  isNativePlatform: () => true,
  getPlatform: () => 'ios',
  Plugins: {
    Purchases: {
      isEntitled: async () => ({ entitled: false }),
      getProduct: async () => ({ ok: true, price: '$8.99' }),
    },
    PushNotifications: {
      checkPermissions: async () => ({ receive: 'prompt' }),
      addListener: () => ({ remove: () => {} }),
    },
  },
};
"""

OVERFLOW_JS = """() => {
  const vw = window.innerWidth;
  const bad = [];
  if (document.documentElement.scrollWidth > vw + 1)
    bad.push({ el: '<page>', right: document.documentElement.scrollWidth });
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    // allow intentionally scrollable strips
    if (el.closest('.stats-bar, .multi-select-panel, .compare-suggest')) continue;
    if (r.right > vw + 2 || r.left < -2) {
      const id = el.id ? '#' + el.id : '';
      const cls = el.className && typeof el.className === 'string'
        ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : '';
      bad.push({ el: el.tagName.toLowerCase() + id + cls,
                 left: Math.round(r.left), right: Math.round(r.right), vw });
      if (bad.length > 12) break;
    }
  }
  return bad;
}"""

report = {}

def shoot(pg, name, label):
    pg.screenshot(path=f"{OUT}/{name}-{label}.png", full_page=False)
    over = pg.evaluate(OVERFLOW_JS)
    if over:
        report.setdefault(f"{name}-{label}", []).extend(over)

def run(width, height):
    label = f"{width}w" + ("-native" if NATIVE else "")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": height})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        if NATIVE:
            pg.add_init_script(NATIVE_MOCK)
        pg.goto(BASE + "/index.html", wait_until="domcontentloaded")
        pg.evaluate("""() => {
            localStorage.setItem('jh_pro', '1');
            localStorage.setItem('jh_pro_source', 'iap');
            localStorage.setItem('jh_zip', '%s');
        }""" % ZIP)
        pg.reload(wait_until="domcontentloaded")
        try:
            zi = pg.locator("#zip-banner-input")
            if zi.is_visible(timeout=3000):
                zi.fill(ZIP)
                pg.locator("#zip-banner-go").click()
        except Exception:
            pass
        pg.wait_for_selector(".car-card", timeout=90000)
        time.sleep(1.2)

        # 1. Live tab with the first-run honesty note forced visible
        pg.evaluate("document.getElementById('first-run-note').style.display=''")
        shoot(pg, "live-note", label)
        pg.evaluate("document.getElementById('first-run-note').style.display='none'")

        # 2. Filters drawer
        pg.locator("#live-filter-toggle").click(); time.sleep(0.5)
        shoot(pg, "live-filters", label)
        pg.locator("#live-filter-toggle").click(); time.sleep(0.3)

        # 3. Expanded card (part rows with the buyer-lens chips)
        cards = pg.locator(".car-card .parts-details summary")
        n = min(cards.count(), 25)
        for i in range(n):
            cards.nth(i).click(); time.sleep(0.2)
            det = cards.nth(i).locator("xpath=ancestor::details")
            if det.locator(".part-save").count() > 0:
                break
        time.sleep(0.4)
        shoot(pg, "live-card", label)

        # 4. Yards tab + compare sheet
        pg.locator(".tab[data-tab='yards']").click(); time.sleep(1.0)
        shoot(pg, "yards", label)
        try:
            pg.locator("#compare-input").fill("headlight")
            pg.locator("#compare-go").click()
            pg.wait_for_selector("#prices-sheet.open", timeout=8000)
            time.sleep(0.6)
            shoot(pg, "compare-sheet", label)
            pg.locator("#prices-close").click(); time.sleep(0.3)
        except Exception as e:
            report.setdefault("errors", []).append(f"compare {label}: {e}")

        # 5. Parts tab: fit search results
        pg.locator(".tab[data-tab='parts']").click(); time.sleep(0.5)
        try:
            pg.locator("#pf-part").click()
            pg.locator("#pf-part").fill("alternator"); time.sleep(0.8)
            try:
                pg.locator("#pf-part-suggest [role='option']").first.click()
            except Exception:
                pg.keyboard.press("Enter")
            pg.select_option("#pf-year", "2008")
            pg.select_option("#pf-make", "Chevrolet")
            time.sleep(0.5)
            pg.select_option("#pf-model", index=1)
            pg.locator("#pf-go").click(); time.sleep(2.5)
            shoot(pg, "parts-results", label)
        except Exception as e:
            shoot(pg, "parts-results", label)
            report.setdefault("errors", []).append(f"parts {label}: {e}")

        # 6. Coverage-request form (ask-us-to-add-it)
        try:
            pg.evaluate("""() => {
                const out = document.getElementById('pf-results');
                out.innerHTML = '<div class="pf-empty">QA: coverage form.' + pfAskHtml('car') + '</div>';
            }""")
            pg.locator(".pfc-ask").click(); time.sleep(0.4)
            shoot(pg, "coverage-form", label)
        except Exception as e:
            report.setdefault("errors", []).append(f"coverage {label}: {e}")

        # 7. Alerts tab
        pg.locator(".tab[data-tab='alerts']").click(); time.sleep(0.6)
        shoot(pg, "alerts", label)

        # 8. Paywall — stage as free user state for the real pitch
        pg.evaluate("""() => {
            localStorage.removeItem('jh_pro');
            localStorage.removeItem('jh_pro_source');
        }""")
        pg.reload(wait_until="domcontentloaded")
        pg.wait_for_selector(".car-card", timeout=60000); time.sleep(0.8)
        pg.evaluate("openUpgradeSheet('qa-audit')"); time.sleep(0.6)
        shoot(pg, "paywall", label)

        if errors:
            report.setdefault("console-errors", []).append({label: errors[:5]})
        b.close()

for w, h in VIEWPORTS:
    run(w, h)
    print(f"done {w}w")

print(json.dumps(report, indent=2) if report else "NO OVERFLOW / NO CONSOLE ERRORS")
