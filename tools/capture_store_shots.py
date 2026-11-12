#!/usr/bin/env python3
"""Store screenshots for both stores: a benefit headline over a real capture
of the current app, on a plain brand background.

Two stages in one run:

1. Capture. The app in docs/ is served locally and driven with Playwright,
   with the real data in docs/data. The page runs as the native shell does
   (a stubbed window.Capacitor, so the Alerts tab shows the push UI the store
   apps show and no web-only banners); the shell's data fetches to
   https://yardscout.io/ are answered from the local docs/ copy, and every
   request to the YardScout API / analytics is aborted, so a capture never
   writes a counter, a device or a watch anywhere. Pro slides set the Pro
   flag the way the iOS IAP handoff does (jh_pro + jh_pro_source=iap).
   Raw captures: 430x830 CSS px @3x, light theme.

2. Compose. Each slide is an HTML page (Inter from Google Fonts, colours from
   docs/styles.css tokens, the mark from docs/brand/) with the headline, an
   optional sub-line and the capture inside a plain rounded phone outline,
   rendered at:
     iOS     440x956 CSS @3x   -> 1320x2868 (6.9" iPhone; the only set the
                                  iPhone-only app uploads)
     Android 432x864 CSS @2.5x -> 1080x2160 (Play phone, 2:1)
   PNGs are flattened to RGB (App Store rejects alpha).

    python3 tools/capture_store_shots.py            # serves docs/ itself
    python3 tools/capture_store_shots.py --only cars,parts --keep-raw /tmp/raw

Every number on a slide is whatever the app shows for the data on disk that
day; re-run after a scan and the slides change with it. Look at every slide
before committing (crowding, cut-off text, a bad photo on the first card).
"""
from __future__ import annotations

import argparse
import base64
import functools
import http.server
import io
import mimetypes
import os
import socketserver
import tempfile
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# San Antonio: Wrench-A-Part's own photos (no watermark), row numbers on
# every car, a dozen yards within 100 mi.
ZIP = "78219"
THEME = "light"
APP_VIEW = {"width": 430, "height": 830}
APP_SCALE = 3

# (file stem, headline, sub-line, capture step, pro?)
SLIDES = [
    ("01_cars", "Find the car before you drive", "Each car's row and the day it was set out", "cars", False),
    ("02_map", "Every yard near you on one map", "Tap a yard to see what landed this week", "map", False),
    ("03_parts", "See which cars carry a part that fits", "Camry alternator: verified or likely fit", "parts", False),
    ("04_rows", "Walk the rows with a list", "One yard's cars in row order, tick them off", "rows", False),
    ("05_alerts", "Get a push the day your car lands", "Watch a model; Pro alerts within hours", "alerts", True),
    ("06_value", "Know what a part is worth", "Pro: yard price vs what it sells for online", "value", True),
]

# Parts slide search: a common car and part with Verified and Likely donors.
PARTS_CAR = ("2009", "Toyota", "Camry")
PARTS_PART = "Alternator"
PARTS_ENGINE = "3.5 V6"
# Walk-the-rows slide: a yard with its own photos and numbered rows.
ROWS_YARD = "Wrench-A-Part - San Antonio"
# Alerts slide watch: make + model.
WATCH = ("Toyota", "Camry")
WATCH_RADIUS = "50"
# Value slide: VINs passed over after a look (e.g. an option part on top).
VALUE_SKIP: set[str] = set()

IOS_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Mobile/15E148")
ANDROID_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/130.0 Mobile Safari/537.36")
BLOCK_HOSTS = ("workers.dev", "goatcounter", "stripe.com")


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- serving --

def serve_docs() -> tuple[str, socketserver.TCPServer]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(DOCS))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/", srv


# ---------------------------------------------------------------- capture --

def native_stub(platform: str) -> str:
    # Just enough of the Capacitor bridge for the shell's code paths: no
    # Purchases plugin (Pro comes from the local flag), a PushNotifications
    # plugin that reports permission granted and hands back a dummy token.
    return """
    (() => {
      const listeners = {};
      const PN = {
        addListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); return { remove() {} }; },
        async checkPermissions() { return { receive: 'granted' }; },
        async requestPermissions() { return { receive: 'granted' }; },
        async register() { setTimeout(() => (listeners.registration || []).forEach(f => f({ value: 'store-shot' })), 50); },
        async removeAllListeners() {},
      };
      window.Capacitor = { isNativePlatform: () => true, getPlatform: () => '%s', Plugins: { PushNotifications: PN } };
    })();
    """ % platform


def new_ctx(browser, base: str, *, platform: str, pro: bool):
    ctx = browser.new_context(viewport=APP_VIEW, device_scale_factor=APP_SCALE, is_mobile=True,
                              has_touch=True, user_agent=IOS_UA if platform == "ios" else ANDROID_UA)
    keys = {"jh_honesty_ack": "1", "ys_install_hint": "1", "ys_app_promo": "1", "jh_visits": "5",
            "ys_theme": THEME, "ys_rows_tip_off": "1", "ys_review_asked": "1"}
    if pro:
        keys.update({"jh_pro": "1", "jh_pro_source": "iap", "ys_push_on": "1"})
    sets = "; ".join(f"localStorage.setItem('{k}','{v}')" for k, v in keys.items())
    # Only on the first load of a page: a later reload keeps what the app saved.
    ctx.add_init_script("try { if (!sessionStorage.getItem('shot_init')) { " + sets +
                        "; sessionStorage.setItem('shot_init','1'); } } catch(e) {}")
    ctx.add_init_script(native_stub(platform))

    def route(r):
        url = r.request.url
        if any(h in url for h in BLOCK_HOSTS):
            return r.abort()
        if url.startswith("https://yardscout.io/"):
            rel = url[len("https://yardscout.io/"):].split("?")[0].split("#")[0]
            f = (DOCS / rel).resolve()
            if DOCS in f.parents and f.is_file():
                ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                return r.fulfill(status=200, body=f.read_bytes(), content_type=ctype,
                                 headers={"access-control-allow-origin": "*"})
            return r.fulfill(status=404, body="")
        return r.continue_()
    ctx.route("**/*", route)
    return ctx


def tidy(page):
    page.evaluate("""() => {
        const s = document.getElementById('head-spec');
        if (s) { s.style.transition = 'none'; s.style.opacity = '1'; }
        for (const id of ['app-promo', 'appstore-alerts-panel', 'first-run-note']) {
            const el = document.getElementById(id); if (el) el.remove();
        }
        document.querySelectorAll('.toast, #toast').forEach(t => t.remove());
    }""")


def wait_images(page, timeout=15000):
    try:
        page.wait_for_function("""() => [...document.images].filter(i => {
              const r = i.getBoundingClientRect();
              return r.bottom > 0 && r.top < innerHeight && r.width > 0;
            }).every(i => i.complete)""", timeout=timeout)
    except Exception:
        log("  (some on-screen images still loading)")
    page.wait_for_timeout(400)


def load_app(page, base):
    page.goto(base, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector("#zip-banner-input", state="visible", timeout=8000)
        page.fill("#zip-banner-input", ZIP)
        page.click("#zip-banner-go")
    except Exception:
        pass
    page.wait_for_selector("#live-grid .car-card", timeout=90000)
    # Background regions: wait until the whole inventory is in.
    try:
        page.wait_for_function("!/Loading the rest of the inventory/.test(document.body.innerText)", timeout=120000)
    except Exception:
        log("  (inventory still loading)")
    page.wait_for_timeout(2000)
    tidy(page)


def tab(page, name):
    page.locator(f'.tab[data-tab="{name}"]').first.click(timeout=10000)
    page.wait_for_timeout(1200)


def scroll_to(page, selector, gap=12):
    page.locator(selector).first.evaluate(
        "(el, gap) => { el.scrollIntoView({block: 'start'}); "
        "window.scrollBy(0, -(document.querySelector('header')?.offsetHeight || 64) - gap); }", gap)
    page.wait_for_timeout(500)


def step_cars(page, base):
    load_app(page, base)
    page.evaluate("window.scrollTo(0, 0)")
    wait_images(page)


def step_map(page, base):
    load_app(page, base)
    tab(page, "yards")
    page.locator('.yv-btn[data-view="map"]').click()
    page.wait_for_selector("#yards-map .maplibregl-canvas, #yards-map .map-pin", timeout=30000)
    page.wait_for_timeout(6000)   # tiles


def step_parts(page, base):
    load_app(page, base)
    tab(page, "parts")
    y, mk, md = PARTS_CAR
    page.select_option("#pf-year", y); page.wait_for_timeout(500)
    page.select_option("#pf-make", mk); page.wait_for_timeout(500)
    page.select_option("#pf-model", md); page.wait_for_timeout(500)
    page.fill("#pf-part", PARTS_PART); page.wait_for_timeout(600)
    opt = page.locator("#pf-part-suggest [role=option]:visible").first
    if opt.count():
        opt.click(); page.wait_for_timeout(500)
    engs = page.locator("#pf-engine button:visible")
    if engs.count():
        log("  engines:", engs.all_inner_texts())
        pick = page.locator("#pf-engine button:visible", has_text=PARTS_ENGINE)
        (pick.first if pick.count() else engs.first).click(); page.wait_for_timeout(500)
    page.click("#pf-go"); page.wait_for_timeout(4000)
    scroll_to(page, "#pf-results .pf-tier-counts")
    wait_images(page)


def step_rows(page, base):
    load_app(page, base)
    page.evaluate("loc => openYardRows(loc)", ROWS_YARD)
    page.wait_for_timeout(1500)
    wait_images(page)


def step_alerts(page, base):
    load_app(page, base)
    tab(page, "alerts")
    page.select_option("#alert-make", WATCH[0]); page.wait_for_timeout(600)
    page.click("#alert-model-btn"); page.wait_for_timeout(400)
    page.fill("#alert-model-search", WATCH[1]); page.wait_for_timeout(400)
    page.locator("#alert-model-list label", has_text=WATCH[1]).first.click(); page.wait_for_timeout(300)
    page.click("#alert-model-done"); page.wait_for_timeout(300)
    page.select_option("#alert-radius", WATCH_RADIUS)
    page.click("#alert-add-btn"); page.wait_for_timeout(1500)
    btn = page.locator("#native-push-enable")
    if btn.is_visible():
        btn.click(); page.wait_for_timeout(1000)
    scroll_to(page, "#alert-watchlist", gap=8)
    wait_images(page)


def step_value(page, base):
    load_app(page, base)
    # Nearby new arrivals with a photo and several parts on the list. Their
    # yards' price lists load lazily: touch them, wait, then pick the first
    # car whose top two "Worth pulling" rows both show a yard price.
    keys = page.evaluate("""() => liveInventory.filter(v => {
            const d = vehicleDistanceMi(v);
            if (d == null || d > 30 || !isNew(v.dateAdded)) return false;
            const ex = extrasFor(v), ph = ex && ex[extraIdx.photo] ? photoInfo(ex[extraIdx.photo]) : null;
            if (!ph || !ph.onCards || !v.hasMatch || !v.topParts || v.topParts.length < 4) return false;
            v.topParts.forEach(p => lookupYardCost(p.name, v.location));
            return true;
        }).slice(0, 60).map(v => vehicleKey(v))""")
    page.wait_for_timeout(4000)
    key = None
    for k in keys:
        page.evaluate("k => openCarDetail(k)", k)
        page.wait_for_timeout(250)
        info = page.evaluate("""() => {
            const rows = [...document.querySelectorAll('#car-detail-body .worth-list li.worth-item')].slice(0, 3);
            return { priced: rows.slice(0, 2).filter(r => /Yard \\$\\d/.test(r.textContent)).length,
                     busy: rows.slice(0, 2).some(r => r.querySelector('.shared-note')),
                     title: document.getElementById('car-detail-title')?.textContent,
                     parts: rows.map(r => r.querySelector('.part-name')?.textContent) };
        }""")
        if info["priced"] >= 2 and not info["busy"]:
            log("  candidate:", k, info["title"], info["parts"])
            if not key and k not in VALUE_SKIP:
                key = k
    log("  value car:", key)
    key = key or (keys[0] if keys else None)
    if key:
        page.evaluate("k => openCarDetail(k)", key)
    page.wait_for_timeout(1500)
    # Car name at the top: yard, row and the priced parts below it.
    page.evaluate("""() => { const sc = document.getElementById('car-detail-scroll'),
        el = document.querySelector('#car-detail-body .eyebrow');
        sc.scrollTop += el.getBoundingClientRect().top - sc.getBoundingClientRect().top - 12; }""")
    page.wait_for_timeout(500)
    wait_images(page)


STEPS = {"cars": step_cars, "map": step_map, "parts": step_parts, "rows": step_rows,
         "alerts": step_alerts, "value": step_value}


def capture(browser, base, platform, slides, raw_dir: Path) -> dict[str, Path]:
    out = {}
    for stem, _h, _s, step, pro in slides:
        ctx = new_ctx(browser, base, platform=platform, pro=pro)
        page = ctx.new_page()
        try:
            STEPS[step](page, base)
            tidy(page)
            path = raw_dir / f"{platform}_{stem}.png"
            page.screenshot(path=str(path))
            out[stem] = path
            log(f"  captured {platform} {stem}")
        except Exception as e:
            log(f"  FAILED {platform} {stem}: {str(e)[:200]}")
        finally:
            ctx.close()
    return out


# ---------------------------------------------------------------- compose --

SLIDE_HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  :root { --bg:%(bg)s; --fg:%(fg)s; --dim:%(dim)s; --brand:#F26B1D; --rim:%(rim)s; }
  html,body { margin:0; height:100%%; background:var(--bg); }
  body { font-family:'Inter',system-ui,sans-serif; color:var(--fg); display:flex;
         flex-direction:column; align-items:center; overflow:hidden; }
  .stripe { position:absolute; left:0; right:0; top:0; height:%(stripe)spx;
            background:repeating-linear-gradient(-45deg,var(--brand) 0 %(sw)spx,transparent %(sw)spx %(sw2)spx); opacity:.9; }
  .head { padding:%(top)spx %(side)spx 0; text-align:center; }
  h1, p { text-wrap:balance; }
  h1 { margin:0; font-weight:800; font-size:%(h1)spx; line-height:1.08; letter-spacing:-0.02em; }
  p { margin:%(subgap)spx 0 0; font-weight:500; font-size:%(sub)spx; line-height:1.25; color:var(--dim); }
  .phone { margin-top:%(phgap)spx; width:%(pw)spx; height:%(ph)spx; border-radius:%(pr)spx;
           border:%(bw)spx solid var(--rim); background:#000; padding:%(pad)spx; box-sizing:border-box;
           flex:none; }
  .screen { width:100%%; height:100%%; border-radius:%(sr)spx; overflow:hidden; background:%(screen)s; }
  .screen img { display:block; width:100%%; }
</style></head><body>
<div class="stripe"></div>
<div class="head"><h1>%(headline)s</h1>%(subhtml)s</div>
<div class="phone"><div class="screen"><img src="data:image/png;base64,%(img)s"></div></div>
</body></html>"""

# Slide styles. Colours are docs/styles.css tokens (light: --bg, --text,
# --text-dim; dark: the same names under [data-theme="dark"]).
#   dark-out:  ink background, cream headline, the app in its light theme
#   light-out: paper background, ink headline, the app in its dark theme
STYLES = {
    "dark-out": dict(theme="light", bg="#1C1C1A", fg="#F4F2EC", dim="#B3B1AA", rim="#3F3F3B", screen="#F4F2EC"),
    "light-out": dict(theme="dark", bg="#F4F2EC", fg="#1C1C1A", dim="#5E5B54", rim="#1C1C1A", screen="#1C1C1A"),
}
STYLE = STYLES["dark-out"]

# CSS geometry per store (the page is rendered at the store's CSS size).
GEOM = {
    "ios": dict(css=(440, 956), scale=3, top=58, side=28, h1=40, sub=19, subgap=12, phgap=34,
                stripe=8, sw=10, sw2=20, bw=3, pad=6, pr=44),
    "android": dict(css=(432, 864), scale=2.5, top=46, side=26, h1=36, sub=17, subgap=10, phgap=26,
                    stripe=7, sw=9, sw2=18, bw=3, pad=5, pr=40),
}


def compose(browser, raw: Path, headline: str, sub: str, platform: str, out: Path):
    g = GEOM[platform]
    W, H = g["css"]
    # Phone height = what is left below the text; width follows the capture's aspect.
    with Image.open(raw) as im:
        aspect = im.width / im.height
    # Estimate the header height by rendering once and measuring.
    params = dict(g, **STYLE, headline=headline, subhtml=f"<p>{sub}</p>" if sub else "",
                  img=base64.b64encode(raw.read_bytes()).decode(), pw=100, ph=100, sr=g["pr"] - g["pad"])
    ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=g["scale"])
    page = ctx.new_page()
    page.set_content(SLIDE_HTML % params, wait_until="networkidle")
    head_bottom = page.evaluate("document.querySelector('.head').getBoundingClientRect().bottom")
    avail = H - head_bottom - g["phgap"] - 18
    inner_h = avail - 2 * (g["bw"] + g["pad"])
    inner_w = inner_h * aspect
    params.update(ph=round(avail), pw=round(inner_w + 2 * (g["bw"] + g["pad"])))
    page.set_content(SLIDE_HTML % params, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    png = page.screenshot(type="png")
    ctx.close()
    Image.open(io.BytesIO(png)).convert("RGB").save(out, optimize=True)
    log("  saved", out, Image.open(out).size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="serve URL of docs/ (default: serve docs/ on a free port)")
    ap.add_argument("--out", type=Path, default=ROOT / "fastlane/screenshots/en-US")
    ap.add_argument("--android-out", type=Path,
                    default=ROOT / "fastlane/metadata/android/en-US/images/phoneScreenshots")
    ap.add_argument("--only", help="comma list of steps (cars,map,parts,rows,alerts,value)")
    ap.add_argument("--platforms", default="ios,android")
    ap.add_argument("--keep-raw", type=Path, help="keep the raw app captures here")
    ap.add_argument("--style", choices=sorted(STYLES), default="dark-out",
                    help="dark-out: dark slide, light app (default); light-out: light slide, dark app")
    args = ap.parse_args()
    global THEME, STYLE
    STYLE = STYLES[args.style]
    THEME = STYLE["theme"]

    slides = [s for s in SLIDES if not args.only or s[3] in args.only.split(",")]
    base, srv = (args.base, None) if args.base else serve_docs()
    raw_dir = args.keep_raw or Path(tempfile.mkdtemp(prefix="store_raw_"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        exe = os.environ.get("PW_CHROMIUM")
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for platform in args.platforms.split(","):
            out = args.out if platform == "ios" else args.android_out
            out.mkdir(parents=True, exist_ok=True)
            log(f"== {platform} -> {out}")
            raws = capture(browser, base, platform, slides, raw_dir)
            for stem, headline, sub, _step, _pro in slides:
                if stem in raws:
                    compose(browser, raws[stem], headline, sub, platform, out / f"{stem}.png")
        browser.close()
    if srv:
        srv.shutdown()


if __name__ == "__main__":
    main()
