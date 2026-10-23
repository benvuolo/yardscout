"""Capture the two interchange-release Play screenshots from yardscout.io.

Android sibling of appstore-assets/ios/_capture_ios_interchange.py — same
scenes, same house rules as _capture_android.py (1080x2160 via viewport
432x864 @ dsf 2.5, Android Chrome UA, free-tier state, real production data).

  * Shot 6 (screen_6_compare.png) — Yards tab, cross-yard part price compare:
    zip 84047 (Midvale, Salt Lake valley), query "alternator", compare sheet
    open with the default cheapest-first sort. Asserts >= 2 priced yards and
    ascending prices (the cheapest-first promise must be visibly true).
  * Shot 7 (screen_7_fitment.png) — Parts tab fitment results: 2005 Toyota
    Camry + alternator. Asserts donor rows render with the honesty-tier tags
    ("Verified fit" / "Likely fit — verify part #") — the tags are the point
    of the shot, so at least one of each tier must be visible in-frame.

Both shots: free-tier state (only jh_honesty_ack / ys_install_hint pre-set) —
both features are free; no Pro staging, no DOM edits beyond the house-rule
#head-spec fade pin.

Usage: python _capture_android_interchange.py [--compare-only | --fitment-only]
"""
import sys
from playwright.sync_api import sync_playwright

OUT = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/screenshots"
URL = "https://yardscout.io/"
ZIP = "84047"
COMPARE_ONLY = "--compare-only" in sys.argv
FITMENT_ONLY = "--fitment-only" in sys.argv

# 432 x 864 CSS px @ 2.5 => 1080 x 2160 physical (exactly 2:1, Play's limit).
VIEWPORT = {"width": 432, "height": 864}
DSF = 2.5
TARGET = (1080, 2160)
UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Mobile Safari/537.36")

def log(*a):
    print(*a, flush=True)

def shoot(page, name, scroll_top=True):
    if scroll_top:
        page.evaluate("window.scrollTo(0, 0)")
    # Pin the rotating header tagline fully opaque (house rule).
    page.evaluate("""() => {
        const s = document.getElementById('head-spec');
        if (s) { s.style.transition = 'none'; s.style.opacity = '1'; }
    }""")
    page.wait_for_timeout(600)
    path = f"{OUT}/{name}"
    page.screenshot(path=path)
    log(f"saved {path}")

def new_mobile_context(browser):
    ctx = browser.new_context(
        viewport=VIEWPORT, device_scale_factor=DSF,
        is_mobile=True, has_touch=True, user_agent=UA,
    )
    # ys_app_promo suppresses the web-only "YardScout is now a native app"
    # banner — it never renders inside the native builds (IS_NATIVE guard),
    # so it must not appear in a store screenshot.
    ctx.add_init_script(
        "try { localStorage.setItem('jh_honesty_ack','1');"
        " localStorage.setItem('ys_install_hint','1');"
        " localStorage.setItem('ys_app_promo','1'); } catch(e) {}")
    return ctx

def load_with_zip(page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#zip-banner-input", state="visible", timeout=30000)
    page.fill("#zip-banner-input", ZIP)
    page.click("#zip-banner-go")
    page.wait_for_selector("#live-grid .car-card", timeout=60000)
    page.wait_for_timeout(4000)  # stats chips, fonts, price lists settle

def compare_shot(page):
    # ---------- Shot 6: Yards tab, alternator compared across yards ----------
    page.click('.tab[data-tab="yards"]')
    page.wait_for_selector("#yards-grid .yard-card", timeout=30000)
    page.wait_for_timeout(1500)
    page.click("#compare-input")
    page.type("#compare-input", "alternator", delay=40)
    page.wait_for_selector("#compare-suggest .compare-suggest-item", timeout=8000)
    page.locator("#compare-suggest .compare-suggest-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(1500)
    state = page.evaluate("""() => {
        const sheet = document.getElementById('prices-sheet');
        const rows = [...document.querySelectorAll('#prices-body .compare-row')]
            .map(r => ({
                yard: r.querySelector('strong')?.textContent.trim() || '',
                text: r.textContent.replace(/\\s+/g, ' ').trim(),
                price: parseFloat((r.textContent.match(/\\$([\\d.]+)/) || [,''])[1]),
            }));
        return {
            open: sheet.classList.contains('open'),
            title: document.getElementById('prices-title').textContent,
            sub: document.getElementById('prices-sub').textContent,
            cheapFirstActive: document.getElementById('prices-sort-price')
                .classList.contains('active'),
            rows,
        };
    }""")
    log(f"shot6 title: {state['title']}")
    log(f"shot6 sub: {state['sub']}")
    for r in state["rows"]:
        log(f"  row: {r['text']}")
    prices = [r["price"] for r in state["rows"]]
    assert state["open"], "compare sheet did not open"
    assert "alternator" in state["title"].lower(), f"wrong title: {state['title']}"
    assert len(prices) >= 2, f"want >=2 priced yards, got {len(prices)}"
    assert state["cheapFirstActive"], "cheapest-first sort not active"
    assert prices == sorted(prices), f"prices not ascending: {prices}"
    shoot(page, "screen_6_compare.png")

def fitment_shot(page):
    # ---------- Shot 7: Parts tab, 2005 Camry alternator fitment ----------
    page.click('.tab[data-tab="parts"]')
    page.wait_for_timeout(800)
    page.fill("#pf-part", "alternator")
    page.wait_for_selector("#pf-part-suggest .compare-suggest-item", timeout=8000)
    page.locator("#pf-part-suggest .compare-suggest-item").first.dispatch_event("mousedown")
    page.wait_for_timeout(900)
    page.select_option("#pf-year", "2005")
    page.select_option("#pf-make", "Toyota")
    page.wait_for_timeout(500)
    page.select_option("#pf-model", "Camry")
    page.click("#pf-go")
    page.wait_for_timeout(1500)

    def tier_counts():
        return page.evaluate("""() => ({
            rows: document.querySelectorAll('#pf-results .pf-row-card').length,
            verified: document.querySelectorAll('#pf-results .pf-tier-verified').length,
            likely: document.querySelectorAll('#pf-results .pf-tier-likely').length,
            head: document.querySelector('#pf-results')?.innerText.slice(0, 160) || '',
        })""")

    # The 05 Camry shipped with two engines, so the honesty UI asks which one
    # is in YOUR car before answering. Both are real answers; for the store
    # shot pick the chip whose results show BOTH tiers (a Verified fit tag
    # next to Likely fit tags is the differentiator), preferring the most
    # verified donors.
    chips = page.locator("#pf-engine .pf-chip")
    n_chips = chips.count()
    best = None  # (verified>0 and likely>0, verified, chip_index)
    if n_chips:
        for i in range(n_chips):
            label = chips.nth(i).inner_text()
            if "isn't listed" in label or "isn\u2019t listed" in label:
                continue
            chips.nth(i).click()
            page.wait_for_timeout(1400)
            t = tier_counts()
            log(f"chip {i} '{label}': {t['rows']} rows"
                f" | {t['verified']} verified | {t['likely']} likely")
            score = (t["verified"] > 0 and t["likely"] > 0, t["verified"], -i)
            if t["rows"] and (best is None or score > best[0]):
                best = (score, i, label)
        assert best, "no engine chip produced donor rows"
        if best[1] != n_chips - 1:  # re-select the winner if not current
            chips.nth(best[1]).click()
            page.wait_for_timeout(1400)
        log(f"chosen engine chip: {best[2]}")
    t = tier_counts()
    log(f"shot7 rows: {t['rows']} | verified: {t['verified']} | likely: {t['likely']}")
    log(f"shot7 head: {t['head']!r}")
    assert t["rows"] > 0, "no fitment donor rows rendered"
    assert t["verified"] and t["likely"], \
        f"need both tiers visible (verified={t['verified']}, likely={t['likely']})"

    # Frame: engine chips + results header at the top (under the sticky
    # header), donor rows with their tier tags filling the rest.
    page.evaluate("""() => {
        const anchor = document.querySelector('#pf-engine')
            || document.querySelector('#pf-results');
        const y = anchor.getBoundingClientRect().top + window.scrollY - 70;
        window.scrollTo(0, Math.max(0, y));
    }""")
    page.wait_for_timeout(600)
    in_frame = page.evaluate("""() => ({
        tags: [...document.querySelectorAll('#pf-results .pf-tier')].filter(e => {
            const b = e.getBoundingClientRect();
            return b.top >= 0 && b.bottom <= window.innerHeight;
        }).map(e => e.textContent.trim()),
        promo: (() => {
            const p = document.getElementById('app-promo');
            return !!p && p.style.display !== 'none'
                && p.getBoundingClientRect().height > 0;
        })(),
    })""")
    log(f"shot7 tier tags in frame: {in_frame['tags']}")
    assert any("Verified" in x for x in in_frame["tags"]), \
        "no Verified fit tag in the captured frame"
    assert any("Likely" in x for x in in_frame["tags"]), \
        "no Likely fit tag in the captured frame"
    assert not in_frame["promo"], "native-app promo banner visible in frame"
    shoot(page, "screen_7_fitment.png", scroll_top=False)

import os
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = new_mobile_context(browser)
    page = ctx.new_page()
    load_with_zip(page)
    if not FITMENT_ONLY:
        compare_shot(page)
    if not COMPARE_ONLY:
        # Close the compare sheet if it's open from shot 6.
        page.evaluate("""() => {
            document.getElementById('prices-sheet')?.classList.remove('open');
            document.getElementById('prices-backdrop')?.classList.remove('open');
        }""")
        page.wait_for_timeout(400)
        fitment_shot(page)
    browser.close()

# Verify geometry (Play: each side 320-3840px, portrait <= 2:1).
from PIL import Image
names = (["screen_6_compare.png"] if COMPARE_ONLY
         else ["screen_7_fitment.png"] if FITMENT_ONLY
         else ["screen_6_compare.png", "screen_7_fitment.png"])
ok = True
for n in names:
    im = Image.open(f"{OUT}/{n}")
    log(f"{n}: {im.size}")
    if im.size != TARGET:
        ok = False
        log(f"ERROR: {n} wrong size (want {TARGET})")
sys.exit(0 if ok else 1)
