"""Capture Google Play phone screenshots of YardScout from https://yardscout.io/.

Android sibling of appstore-assets/ios/_capture_ios.py — same scenes, same
house rules, Play-compliant geometry:

  * Play phone screenshots: PNG/JPG, each side 320-3840px, portrait aspect
    no taller than 2:1. The iOS 1320x2868 (2.17:1) is too tall, so this rig
    renders 1080x2160 (exactly 2:1) via viewport 432x864 @ dsf 2.5 — CSS
    width 432 vs the iOS comp's 440, so text sizes match the approved iOS
    set instead of squashing those renders.
  * Android Chrome user agent; the iOS-install-hint never fires off-iOS but
    ys_install_hint stays pre-set anyway (belt and braces).
  * Shot 4 (alerts) renders the REAL Android 1.2 state: FCM push shipped
    (vc6 published 2026-10-21), and app.js dropped its Android-only "coming
    soon" branches — iOS and Android now share the native alerts copy. The
    capture reproduces that unified IS_NATIVE state: native intro (weekly
    recap push free / instant push alerts Pro), #native-alerts-note shown
    with its live "Enable push notifications" button, web-only panels
    (#appstore-alerts-panel, email alerts, #alert-notif-btn) hidden. A
    zero-"coming soon" assertion still guards the shot.
  * Shot 5 (Pro) keeps the audited house rules: every part row must carry a
    concrete yard list price (UTPAP/wired-pricing yards — never the "check
    yard price list" fallback) and no option-dependent VIN-confirmed badges.
    Prefers the approved iOS set's 2019 Ford F-150 if it still passes, else
    the strongest passing full-size US truck, else the top passing card.

Shots 1-4: free-tier state (only jh_honesty_ack / ys_install_hint pre-set).
Shot 5: Pro state (jh_pro=1 + jh_pro_source=iap) showing unlocked part values.

Usage: python _capture_android.py [--pro-only | --alerts-only]
"""
import sys
from playwright.sync_api import sync_playwright

OUT = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/play-assets/screenshots"
URL = "https://yardscout.io/"
PRO_ONLY = "--pro-only" in sys.argv
ALERTS_ONLY = "--alerts-only" in sys.argv

# 432 x 864 CSS px @ 2.5 => 1080 x 2160 physical (exactly 2:1, Play's limit).
VIEWPORT = {"width": 432, "height": 864}
DSF = 2.5
TARGET = (1080, 2160)

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
    page.screenshot(path=path)  # viewport-only => 1080x2160 at dsf 2.5
    log(f"saved {path}")

def new_mobile_context(browser, pro=False):
    ctx = browser.new_context(
        viewport=VIEWPORT,
        device_scale_factor=DSF,
        is_mobile=True,
        has_touch=True,
        user_agent=("Mozilla/5.0 (Linux; Android 14; Pixel 8) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Mobile Safari/537.36"),
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
    # ---------- Shot 4: alerts tab, Android 1.2 state (FCM push is live) ----
    page.click('.tab[data-tab="alerts"]')
    page.wait_for_timeout(3000)
    # Reproduce app.js's unified IS_NATIVE alerts state — since 1.2 (vc6,
    # FCM shipped) Android renders the same push copy as iOS:
    #   - drop the web-only "Get the iOS app" panel (#appstore-alerts-panel)
    #   - hide the web Notification-API button (#alert-notif-btn)
    #   - swap #alerts-intro-copy to the native wording (IS_NATIVE branch,
    #     app.js ~3050 — push promises are now true on Android)
    #   - show #native-alerts-note with its real "Enable push notifications"
    #     button, as a fresh 1.2 install renders it (no status text)
    #   - hide the web-only Pro email-alerts panel (native never shows it)
    state = page.evaluate("""() => {
        document.getElementById('appstore-alerts-panel')?.remove();
        const email = document.getElementById('email-alerts-panel');
        if (email) email.style.display = 'none';
        const btn = document.getElementById('alert-notif-btn');
        if (btn) btn.style.display = 'none';
        const intro = document.getElementById('alerts-intro-copy');
        if (intro) intro.innerHTML =
            'Add vehicles you want to track &mdash; watching is free, '
            + 'no signup, no email. Free watches get a <strong>weekly recap '
            + 'push</strong>; <strong>instant push alerts</strong> within '
            + 'hours of a car hitting the yard are Pro.';
        const note = document.getElementById('native-alerts-note');
        if (note) note.style.display = '';
        const pushBtn = document.getElementById('native-push-enable');
        if (pushBtn) pushBtn.style.display = '';
        const status = document.getElementById('native-push-status');
        if (status) status.textContent = '';
        const tab = document.getElementById('tab-alerts');
        return {
            iosPanelGone: !document.getElementById('appstore-alerts-panel'),
            noteShown: !!note && note.style.display !== 'none',
            enableBtnShown: !!pushBtn && pushBtn.style.display !== 'none',
            emailPanelHidden: !email || email.style.display === 'none',
            comingSoon: /coming soon|coming to android/i.test(tab.innerText),
            iosMention: /ios app|iphone|app store/i.test(tab.innerText),
        };
    }""")
    page.wait_for_timeout(500)
    log(f"shot4 android alerts state: {state}")
    assert state["iosPanelGone"] and state["emailPanelHidden"] \
        and state["noteShown"] and state["enableBtnShown"], \
        f"wrong panel state: {state}"
    assert not state["comingSoon"] and not state["iosMention"], \
        f"stale/iOS copy rendered: {state}"
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

# The approved iOS Pro shot (screen_5_option_a) is a 2019 Ford F-150; mirror
# it if that card still passes, else fall back to another full-size US truck.
PREFERRED_CARD = re.compile(r"2019 Ford F-150", re.I)
FULLSIZE_TRUCK = re.compile(
    r"F-?[12]50|Silverado|Sierra|Tundra|\bRam\b(?! ?charger)|Titan", re.I)

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
    shot's point is the pull-cost-vs-part-value contrast)."""
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
        priced = sum(1 for r in c["rows"] if "worth $" in r["price"])
        bad = [r["name"] for r in c["rows"]
               if r["vin"] and RISKY_VIN_PART.search(r["name"])]
        nocost = [r["name"] for r in c["rows"] if "$" not in r["cost"]]
        if not bad and not nocost and priced >= 4:
            # top value high, e.g. 'worth $270–$700' -> 700
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
    # ---------- Shot 5: Pro state, expanded card with part values ----------
    setup_pro_live(page)
    passing = scan_candidates(page)
    if not passing:
        raise SystemExit("No candidate card passed all rules")
    # Mirror the approved iOS option-a card if it still passes; otherwise the
    # strongest passing full-size truck; otherwise the top card in scan order.
    c = next((c for c in passing if PREFERRED_CARD.search(c["title"])), None)
    if c:
        log(f"preferred iOS card still passing: {c['title']}")
    else:
        trucks = sorted((c for c in passing if FULLSIZE_TRUCK.search(c["title"])),
                        key=lambda c: -c["top_high"])
        c = trucks[0] if trucks else passing[0]
        log("preferred 2019 Ford F-150 not available/passing; "
            f"fallback: {c['title']}")
    log(f"chosen: {c['title']} @ {c['yard']}")
    for r in c["rows"]:
        log(f"  part: {r['name']} | vin-confirmed={r['vin']}"
            f" | cost: {r['cost']} | {r['price']}")
    capture_card(page, c["index"], "screen_5_pro.png")

import os
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    if not PRO_ONLY:
        ctx = new_mobile_context(browser)
        free_shots(ctx.new_page(), alerts_only=ALERTS_ONLY)
        ctx.close()
    if not ALERTS_ONLY:
        pro_ctx = new_mobile_context(browser, pro=True)
        pro_shot(pro_ctx.new_page())
    browser.close()

# Verify every output is exactly 1080x2160 (Play portrait limit is 2:1 and
# both sides must be 320-3840px — 1080x2160 satisfies all three).
from PIL import Image

if PRO_ONLY:
    names = ["screen_5_pro.png"]
elif ALERTS_ONLY:
    names = ["screen_4_alerts.png"]
else:
    names = ["screen_1_live.png", "screen_2_search.png", "screen_3_yards.png",
             "screen_4_alerts.png", "screen_5_pro.png"]
ok = True
for n in names:
    im = Image.open(f"{OUT}/{n}")
    log(f"{n}: {im.size}")
    if im.size != TARGET:
        ok = False
        log(f"ERROR: {n} wrong size (want {TARGET})")
sys.exit(0 if ok else 1)
