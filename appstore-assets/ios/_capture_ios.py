"""Capture iOS App Store screenshots of YardScout from https://yardscout.io/.

Viewport 440x956 @3x => 1320x2868 PNGs (Apple 6.9" requirement).
Shots 1-4: free-tier state (only jh_honesty_ack / ys_install_hint pre-set).
Shot 5: Pro state (jh_pro=1 + jh_pro_source=iap) showing unlocked part values.

Usage: python _capture_ios.py [--pro-only | --alerts-only]
"""
import sys
from playwright.sync_api import sync_playwright

OUT = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/appstore-assets/ios"
URL = "https://yardscout.io/"
PRO_ONLY = "--pro-only" in sys.argv
ALERTS_ONLY = "--alerts-only" in sys.argv
PRO_OPTIONS = "--pro-options" in sys.argv

def log(*a):
    print(*a, flush=True)

def shoot(page, name, scroll_top=True):
    if scroll_top:
        page.evaluate("window.scrollTo(0, 0)")
    # The header tagline (#head-spec) rotates with an opacity fade; pin it
    # fully opaque so captures never catch it mid-fade.
    page.evaluate("""() => {
        const s = document.getElementById('head-spec');
        if (s) { s.style.transition = 'none'; s.style.opacity = '1'; }
    }""")
    page.wait_for_timeout(600)
    path = f"{OUT}/{name}"
    page.screenshot(path=path)  # viewport-only => 1320x2868 at dsf 3
    log(f"saved {path}")

def new_mobile_context(browser, pro=False):
    ctx = browser.new_context(
        viewport={"width": 440, "height": 956},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"),
    )
    keys = ["localStorage.setItem('jh_honesty_ack','1')",
            "localStorage.setItem('ys_install_hint','1')"]
    if pro:
        # boot code revokes jh_pro unless jh_pro_source is iap/account
        keys += ["localStorage.setItem('jh_pro','1')",
                 "localStorage.setItem('jh_pro_source','iap')"]
    ctx.add_init_script("try { " + "; ".join(keys) + "; } catch(e) {}")
    return ctx

def load_with_zip(page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#zip-banner-input", state="visible", timeout=30000)
    page.fill("#zip-banner-input", "84101")
    page.click("#zip-banner-go")
    page.wait_for_selector("#live-grid .car-card", timeout=60000)
    page.wait_for_timeout(4000)  # stats chips, fonts, images settle

def alerts_shot(page):
    # ---------- Shot 4: alerts tab ----------
    page.click('.tab[data-tab="alerts"]')
    page.wait_for_timeout(3000)
    # The 'Get the iOS app' card (#appstore-alerts-panel) is web-only — the
    # native build hides it via its Capacitor IS_NATIVE check, so it must not
    # appear in an App Store screenshot. Remove it before capturing.
    page.evaluate(
        "document.getElementById('appstore-alerts-panel')?.remove()")
    page.wait_for_timeout(500)
    gone = page.locator("#appstore-alerts-panel").count() == 0
    log(f"shot4 install card removed: {gone}")
    shoot(page, "screen_4_alerts.png")

def free_shots(page, alerts_only=False):
    # ---------- Shot 1: live results for zip 84101 ----------
    load_with_zip(page)
    if alerts_only:
        alerts_shot(page)
        return
    stats = page.inner_text("#live-stats-bar").replace("\n", " | ")
    log(f"shot1 stats: {stats}")
    log(f"shot1 car cards rendered: {page.locator('#live-grid .car-card').count()}")
    shoot(page, "screen_1_live.png")

    # ---------- Shot 2: filtered to a popular make/model ----------
    page.click("#live-filter-toggle")  # open filters panel
    page.wait_for_timeout(500)
    make_opts = page.eval_on_selector_all(
        "#live-filter-make option", "els => els.map(e => e.value)")

    def apply_filter(make, model):
        """Select make + exactly one model; return rendered card count."""
        page.select_option("#live-filter-make", make)
        page.wait_for_timeout(800)
        page.click("#live-filter-model-btn")
        page.wait_for_timeout(400)
        models = page.eval_on_selector_all(
            "#live-filter-model-list input[data-model]",
            "els => els.map(e => e.dataset.model)")
        target = next((m for m in models if model.lower() in m.lower()), None)
        if not target:
            page.click("#live-filter-model-done")
            page.wait_for_timeout(300)
            return None, 0
        for el in page.locator("#live-filter-model-list input:checked").all():
            el.click()  # clear same-make leftovers
        page.click(f'#live-filter-model-list input[data-model="{target}"]')
        page.wait_for_timeout(300)
        page.click("#live-filter-model-done")
        page.wait_for_timeout(1200)
        return target, page.locator("#live-grid .car-card").count()

    candidates = [("Honda", "Civic"), ("Toyota", "Camry"),
                  ("Toyota", "Tacoma"), ("Ford", "F-150"),
                  ("Toyota", "Corolla"), ("Honda", "Accord")]
    best = None  # (count, make, model)
    for make, model in candidates:
        if make not in make_opts:
            continue
        target, n = apply_filter(make, model)
        log(f"candidate {make} {target or model}: {n} cars")
        if target and (best is None or n > best[0]):
            best = (n, make, target)
        if target and n >= 8:
            break
    if best is None:
        log("WARN: no candidate model found; leaving make-only filter")
    else:
        target, n = apply_filter(best[1], best[2])
        log(f"final filter: {best[1]} {best[2]} ({n} cars)")
    page.wait_for_timeout(1200)
    page.click("#live-filter-toggle")  # collapse panel so results show
    page.wait_for_timeout(1500)
    log(f"shot2 stats: {page.inner_text('#live-stats-bar')}".replace("\n", " | "))
    shoot(page, "screen_2_search.png")

    # ---------- Shot 3: yards tab ----------
    page.click('.tab[data-tab="yards"]')
    page.wait_for_selector("#yards-grid .yard-card", timeout=30000)
    page.wait_for_timeout(2500)
    log(f"shot3 yards stats: {page.inner_text('#yards-stats-bar')}".replace("\n", " | "))
    log(f"shot3 yard cards: {page.locator('#yards-grid .yard-card').count()}")
    shoot(page, "screen_3_yards.png")

    alerts_shot(page)

import re

# Part types where a 'VIN-confirmed' badge is an overclaim (option/package-
# dependent content that a VIN trim decode alone can't confirm). Cards showing
# VIN-confirmed on any of these are skipped. 'if equipped — unconfirmed'
# labels are honest by definition and always fine.
RISKY_VIN_PART = re.compile(
    r"headlight|headlamp|\bhid\b|xenon|matrix"               # lighting
    r"|b&o|bang\s*&\s*olufsen|bowers|wilkins|harman|kardon"  # premium audio
    r"|levinson|bose|jbl|rockford|fosgate|premium (audio|sound)"
    r"|sound system|amplifier|subwoofer|speaker"
    r"|recaro|seat"                                          # branded seats
    r"|spoiler|sunroof|moonroof|panoramic",                  # body options
    re.IGNORECASE)

def setup_pro_live(page):
    """Load the live tab in Pro state and apply the 'Most valuable first' sort."""
    load_with_zip(page)
    diag = page.evaluate("""() => ({
        pro: localStorage.getItem('jh_pro'),
        src: localStorage.getItem('jh_pro_source'),
        locked: document.querySelectorAll('.locked-blur').length,
    })""")
    log(f"pro diag: {diag}")
    page.click("#live-filter-toggle")
    page.wait_for_timeout(500)
    page.select_option("#live-sort", "gold-first")
    page.wait_for_timeout(1500)
    page.click("#live-filter-toggle")
    page.wait_for_timeout(1000)

def scan_candidates(page, limit=None, verbose=True):
    """Scan rendered cards' part rows straight from the DOM (details content
    exists even while collapsed). Returns cards that pass every rule:
    >= 4 priced parts, no risky VIN-confirmed badge, and a concrete yard list
    price on every row (never the 'check yard price list' fallback — the
    shot's point is the buy-low/sell-high contrast)."""
    slice_js = f".slice(0, {limit})" if limit else ""
    cards = page.evaluate("""() =>
        [...document.querySelectorAll('#live-grid .car-card')]""" + slice_js + """
        .map(card => ({
            title: card.querySelector('.car-name')?.textContent.trim() || '?',
            yard: card.querySelector('.loc-name')?.textContent.trim() || '?',
            rows: [...card.querySelectorAll('li.part-item')].map(li => ({
                name: li.querySelector('.part-name')?.textContent.trim() || '',
                vin: !!li.querySelector('.trim-badge.trim-vin'),
                price: li.querySelector('.part-price')?.textContent || '',
                cost: (li.querySelector('.part-cost')?.textContent || '')
                      .replace(/\\s+/g, ' ').trim(),
            })),
        }))""")
    passing = []
    for i, c in enumerate(cards):
        priced = sum(1 for r in c["rows"] if "sells $" in r["price"])
        bad = [r["name"] for r in c["rows"]
               if r["vin"] and RISKY_VIN_PART.search(r["name"])]
        nocost = [r["name"] for r in c["rows"] if "$" not in r["cost"]]
        if not bad and not nocost and priced >= 4:
            # top resale high, e.g. 'sells $270–$700' -> 700
            highs = [int(m.group(1).replace(",", ""))
                     for r in c["rows"]
                     for m in [re.search(r"\$[\d,]+\u2013\$([\d,]+)", r["price"])]
                     if m]
            c.update(index=i, priced=priced, top_high=max(highs, default=0))
            passing.append(c)
            if verbose:
                log(f"card {i}: {c['title']} @ {c['yard']} | {priced} priced"
                    f" | top ${c['top_high']} | PASS")
        elif verbose:
            why = ("risky VIN-confirmed " + str(bad)) if bad \
                else f"only {priced} priced parts" if priced < 4 \
                else "no yard list price on " + str(nocost)
            log(f"card {i}: {c['title']} @ {c['yard']} | reject: {why}")
    return passing

def capture_card(page, card_index, filename):
    """Expand a card's parts panel, frame it under the sticky header, shoot."""
    chosen = page.locator("#live-grid .car-card").nth(card_index)
    # Cosmetic: some inventory rows store the make inside the model string
    # ('Audi' + 'Audi A6' => '2016 Audi Audi A6'). Dedupe the repeated word.
    fixed = chosen.evaluate("""el => {
        const n = el.querySelector('.car-name');
        if (!n) return null;
        n.textContent = n.textContent.replace(/\\b(\\S+) \\1\\b/, '$1');
        return n.textContent.trim();
    }""")
    log(f"capturing '{fixed}' -> {filename}")
    summary = chosen.locator("details.parts-details summary").first
    summary.scroll_into_view_if_needed()
    summary.click()
    page.wait_for_timeout(800)
    # Put the top of this card just below the sticky header.
    chosen.evaluate("""el => {
        const y = el.getBoundingClientRect().top + window.scrollY - 70;
        window.scrollTo(0, Math.max(0, y));
    }""")
    page.wait_for_timeout(800)
    shoot(page, filename, scroll_top=False)
    summary.click()  # collapse again so later captures aren't shifted
    page.wait_for_timeout(400)

def pro_shot(page):
    # ---------- Shot 5: Pro state, expanded card with part resale values ----
    setup_pro_live(page)
    passing = scan_candidates(page, limit=40)
    if not passing:
        raise SystemExit("No candidate card passed all rules")
    c = passing[0]
    log(f"chosen: {c['title']} @ {c['yard']}")
    for r in c["rows"]:
        log(f"  part: {r['name']} | vin-confirmed={r['vin']}"
            f" | cost: {r['cost']} | {r['price']}")
    capture_card(page, c["index"], "screen_5_pro.png")

# Buckets for the three-option candidate spread (r/projectcar audience).
BUCKETS = [
    ("truck", re.compile(
        r"F-?[12]50|Silverado|Sierra|Tacoma|Tundra|\bRam\b|Ranger|Frontier"
        r"|Colorado|Dakota|Titan|Avalanche|C[/ ]?K ?15|S-?10", re.I)),
    ("tuner", re.compile(
        r"Subaru|WRX|Impreza|Civic|Integra|Prelude|Accord|Acura|RSX|GTI"
        r"|Golf|Jetta|Volkswagen|Miata|MX-5|RX-[78]|240SX|3[57]0Z|Eclipse"
        r"|Lancer|Celica|Supra|MR2|BRZ|Mustang|Camaro|tC\b", re.I)),
    ("german/luxury", re.compile(
        r"Audi|BMW|Mercedes|Porsche|\bMini\b|Jaguar|Land Rover|Lexus"
        r"|Infiniti|Cadillac|Lincoln|Genesis|Volvo", re.I)),
]
EXCLUDE_VEHICLE = re.compile(r"Corvette|Focus", re.I)

def pro_options(page):
    # ---- Three candidate Pro shots: truck / tuner / German-luxury spread ----
    setup_pro_live(page)
    passing = [c for c in scan_candidates(page, verbose=False)
               if not EXCLUDE_VEHICLE.search(c["title"])]
    log(f"{len(passing)} cards pass all rules (after vehicle exclusions)")
    for c in passing:
        log(f"  [{c['index']}] {c['title']} @ {c['yard']}"
            f" | {c['priced']} parts | top ${c['top_high']}")

    picks, used_models = [], set()
    def model_key(title):
        return " ".join(title.split()[1:]).lower()  # drop year
    for bucket, rx in BUCKETS:
        pool = [c for c in passing
                if rx.search(c["title"]) and model_key(c["title"]) not in used_models]
        # Favor impressive top resale (> $400), then scan order (gold-first).
        pool.sort(key=lambda c: (c["top_high"] <= 400, c["index"]))
        if pool:
            picks.append((bucket, pool[0]))
            used_models.add(model_key(pool[0]["title"]))
            log(f"bucket {bucket}: picked {pool[0]['title']}")
        else:
            log(f"bucket {bucket}: NO passing card")
    # Backfill empty buckets with the strongest unused candidates.
    for c in sorted(passing, key=lambda c: -c["top_high"]):
        if len(picks) >= 3:
            break
        if model_key(c["title"]) not in used_models:
            picks.append(("backfill", c))
            used_models.add(model_key(c["title"]))
            log(f"backfill: picked {c['title']}")
    if len(picks) < 3:
        raise SystemExit(f"Only {len(picks)} candidates available")

    for (bucket, c), letter in zip(picks, "abc"):
        log(f"--- option {letter} ({bucket}): {c['title']} @ {c['yard']} ---")
        for r in c["rows"]:
            log(f"  part: {r['name']} | vin-confirmed={r['vin']}"
                f" | cost: {r['cost']} | {r['price']}")
        capture_card(page, c["index"], f"screen_5_option_{letter}.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    if PRO_OPTIONS:
        pro_ctx = new_mobile_context(browser, pro=True)
        pro_options(pro_ctx.new_page())
    else:
        if not PRO_ONLY:
            ctx = new_mobile_context(browser)
            free_shots(ctx.new_page(), alerts_only=ALERTS_ONLY)
            ctx.close()
        if not ALERTS_ONLY:
            pro_ctx = new_mobile_context(browser, pro=True)
            pro_shot(pro_ctx.new_page())
    browser.close()

# verify dimensions, and produce 1206x2622 dynamic-island copies
# (cover-scale then center-crop, matching the existing files there).
from PIL import Image
import os
DI = f"{OUT}/dynamic-island-1206x2622"

def dynamic_island_copy(name):
    im = Image.open(f"{OUT}/{name}")
    scale = max(1206 / im.width, 2622 / im.height)
    w, h = round(im.width * scale), round(im.height * scale)
    im2 = im.resize((w, h), Image.LANCZOS)
    left, top = (w - 1206) // 2, (h - 2622) // 2
    im2 = im2.crop((left, top, left + 1206, top + 2622))
    os.makedirs(DI, exist_ok=True)
    im2.save(f"{DI}/{name}")
    log(f"{DI}/{name}: {im2.size}")

if PRO_ONLY:
    names = ["screen_5_pro.png"]
elif ALERTS_ONLY:
    names = ["screen_4_alerts.png"]
elif PRO_OPTIONS:
    names = [f"screen_5_option_{x}.png" for x in "abc"]
else:
    names = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
             "screen_4_alerts.png", "screen_5_pro.png"]
ok = True
for n in names:
    im = Image.open(f"{OUT}/{n}")
    log(f"{n}: {im.size}")
    if im.size != (1320, 2868):
        ok = False
        log(f"ERROR: {n} wrong size")
    if PRO_OPTIONS:
        dynamic_island_copy(n)
sys.exit(0 if ok else 1)
