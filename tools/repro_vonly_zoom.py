"""Repro + verify for the VIN-confirmed-only zoom-out bug (iOS WebKit).

Drives the Parts tab in engine-browse mode (GM Gen III Vortec) and in fitment
mode, toggles the verified-only checkbox, and measures horizontal overflow
(document.scrollWidth vs documentElement.clientWidth) plus visualViewport.scale
at each step. Any scrollWidth > clientWidth is the overflow that makes iOS
zoom the page out.

Usage:
  python tools/repro_vonly_zoom.py <base_url> <width> [shot_prefix]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8777"
WIDTH = int(sys.argv[2]) if len(sys.argv) > 2 else 390
PREFIX = sys.argv[3] if len(sys.argv) > 3 else "/tmp/vonly"

MEASURE = """() => {
  const d = document, de = d.documentElement;
  const wide = [];
  for (const el of d.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width > de.clientWidth + 1 || r.right > de.clientWidth + 1) {
      wide.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0,60)} w=${Math.round(r.width)} right=${Math.round(r.right)}`);
    }
  }
  return {
    scrollWidth: de.scrollWidth,
    clientWidth: de.clientWidth,
    bodyScrollWidth: d.body.scrollWidth,
    vvScale: window.visualViewport ? window.visualViewport.scale : null,
    overflow: de.scrollWidth > de.clientWidth,
    widest: wide.slice(0, 8),
  };
}"""

def report(page, label):
    m = page.evaluate(MEASURE)
    flag = "OVERFLOW!" if m["overflow"] else "ok"
    print(f"[{label}] {flag} scrollWidth={m['scrollWidth']} clientWidth={m['clientWidth']} "
          f"bodyScrollWidth={m['bodyScrollWidth']} vvScale={m['vvScale']}")
    for w in m["widest"]:
        print(f"    wide: {w}")
    return m["overflow"]

def main():
    failures = []
    with sync_playwright() as p:
        browser = p.webkit.launch()
        ctx = browser.new_context(
            viewport={"width": WIDTH, "height": 844},
            device_scale_factor=3,
            is_mobile=True,
            user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 "
                        "Mobile/15E148 Safari/604.1"),
        )
        page = ctx.new_page()
        page.goto(BASE + "/index.html", wait_until="networkidle")
        page.wait_for_timeout(1200)

        # Set a zip (Orem UT, like the owner's screenshot) — browse mode
        # refuses to render without a location.
        try:
            if page.locator("#zip-banner-input").is_visible(timeout=1000):
                page.fill("#zip-banner-input", "84057")
                page.click("#zip-banner-go")
            else:
                page.fill("#live-zip", "84057")
                page.locator("#live-zip").press("Enter")
        except Exception as e:
            print("zip setup fallback:", e)
            page.evaluate("""() => {
              const z = document.getElementById('live-zip');
              z.value = '84057';
              z.dispatchEvent(new Event('input', {bubbles:true}));
              z.dispatchEvent(new Event('change', {bubbles:true}));
            }""")
        page.wait_for_timeout(1000)

        # ---- ENGINE BROWSE MODE -------------------------------------------
        page.click(".tab[data-tab='parts']")
        page.wait_for_timeout(300)
        page.click("#pf-part")
        page.wait_for_selector(".compare-suggest-item", timeout=15000)
        page.fill("#pf-part", "engine")
        page.wait_for_timeout(200)
        page.locator(".compare-suggest-item", has_text="Engine assembly").first.dispatch_event("mousedown")
        page.wait_for_selector("#pf-browse-fam", timeout=10000)
        page.select_option("#pf-browse-fam",
                           label="GM Gen III Vortec truck V8 (4.8/5.3/6.0)")
        page.wait_for_selector("#pf-vonly-cb", timeout=10000)
        page.wait_for_timeout(400)

        if report(page, f"browse pre-toggle {WIDTH}px"): failures.append("browse pre-toggle")
        page.screenshot(path=f"{PREFIX}_browse_pre_{WIDTH}.png")

        page.check("#pf-vonly-cb")
        page.wait_for_timeout(400)
        if report(page, f"browse toggle ON {WIDTH}px"): failures.append("browse toggle ON")
        page.screenshot(path=f"{PREFIX}_browse_on_{WIDTH}.png")

        page.uncheck("#pf-vonly-cb")
        page.wait_for_timeout(400)
        if report(page, f"browse toggle OFF {WIDTH}px"): failures.append("browse toggle OFF")

        # sanity: zip/distance controls row visible on this tab
        # ---- FITMENT MODE -------------------------------------------------
        page.evaluate("""() => {
          const y = document.getElementById('pf-year');
          const mk = document.getElementById('pf-make');
          const md = document.getElementById('pf-model');
          y.value = '2003'; y.dispatchEvent(new Event('input', {bubbles:true}));
          mk.value = 'Chevrolet'; mk.dispatchEvent(new Event('input', {bubbles:true}));
          md.value = 'Silverado 1500'; md.dispatchEvent(new Event('input', {bubbles:true}));
          y.dispatchEvent(new Event('change', {bubbles:true}));
          mk.dispatchEvent(new Event('change', {bubbles:true}));
          md.dispatchEvent(new Event('change', {bubbles:true}));
        }""")
        page.wait_for_timeout(600)
        has_cb = page.locator("#pf-vonly-cb").count() > 0
        if report(page, f"fitment pre-toggle {WIDTH}px"): failures.append("fitment pre-toggle")
        page.screenshot(path=f"{PREFIX}_fitment_pre_{WIDTH}.png")
        if has_cb:
            page.check("#pf-vonly-cb")
            page.wait_for_timeout(400)
            if report(page, f"fitment toggle ON {WIDTH}px"): failures.append("fitment toggle ON")
            page.screenshot(path=f"{PREFIX}_fitment_on_{WIDTH}.png")
            page.uncheck("#pf-vonly-cb")
            page.wait_for_timeout(400)
            if report(page, f"fitment toggle OFF {WIDTH}px"): failures.append("fitment toggle OFF")
        else:
            print("[fitment] no verified-only checkbox rendered (no results?) — check screenshot")

        browser.close()

    if failures:
        print("\nFAIL — horizontal overflow in:", ", ".join(failures))
        sys.exit(1)
    print("\nPASS — no horizontal overflow in any state")

main()
