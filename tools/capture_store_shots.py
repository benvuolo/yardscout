#!/usr/bin/env python3
"""Capture store screenshots of the web shell for both stores in one run.

iOS:     viewport 440x956 @3x   -> 1320x2868 (Apple 6.9" iPhone size)
Android: viewport 432x864 @2.5x -> 1080x2160 (Play phone, 2:1)

Seven slides per store, same order as the live listings:
  1 live results · 2 make/model search · 7 fitment (Parts tab) ·
  6 compare (Yards tab) · 3 yards · 5 Pro card with values · 4 alerts

Runs against a local copy of docs/ (python3 -m http.server in docs/) so the
shots match the shell that is about to ship, not whatever Pages last served.
Pro state is staged the way the iOS handoff documents (jh_pro + jh_pro_source).

    python3 tools/capture_store_shots.py --base http://127.0.0.1:8765/ \
        --out fastlane/screenshots/en-US --android-out fastlane/metadata/android/en-US/images/phoneScreenshots
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ZIP = "84047"
# Store shots are taken in dark mode (owner preference, 2026-10-27); pass
# --theme light for the old look.
THEME = "dark"
SHOTS = ["1_live", "2_search", "7_fitment", "6_compare", "3_yards", "5_pro", "4_alerts"]


def log(*a):
    print(*a, flush=True)


def pin_header(page):
    page.evaluate("""() => {
        const s = document.getElementById('head-spec');
        if (s) { s.style.transition = 'none'; s.style.opacity = '1'; }
        for (const id of ['app-promo', 'appstore-alerts-panel', 'first-run-note']) {
            const el = document.getElementById(id); if (el) el.remove();
        }
        document.body.classList.remove('has-header-badges');
    }""")


def new_ctx(browser, *, ios: bool, pro: bool):
    if ios:
        opts = dict(viewport={"width": 440, "height": 956}, device_scale_factor=3,
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    else:
        opts = dict(viewport={"width": 432, "height": 864}, device_scale_factor=2.5,
                    user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36")
    ctx = browser.new_context(is_mobile=True, has_touch=True, **opts)
    keys = ["localStorage.setItem('jh_honesty_ack','1')", "localStorage.setItem('ys_install_hint','1')",
            "localStorage.setItem('ys_app_promo','1')", "localStorage.setItem('jh_visits','5')",
            f"localStorage.setItem('ys_theme','{THEME}')"]
    if pro:
        keys += ["localStorage.setItem('jh_pro','1')", "localStorage.setItem('jh_pro_source','iap')"]
    ctx.add_init_script("try { " + "; ".join(keys) + "; } catch(e) {}")
    return ctx


def load_with_zip(page, base):
    page.goto(base, wait_until="domcontentloaded", timeout=60000)
    # A second page in the same context already has the zip stored, so the
    # zip banner never appears — go straight to the cards in that case.
    try:
        page.wait_for_selector("#zip-banner-input", state="visible", timeout=8000)
        page.fill("#zip-banner-input", ZIP)
        page.click("#zip-banner-go")
    except Exception:
        pass
    page.wait_for_selector("#live-grid .car-card", timeout=90000)
    page.wait_for_timeout(3000)
    pin_header(page)


def shoot(page, out: Path, name: str):
    pin_header(page)
    page.wait_for_timeout(600)
    path = out / f"{name}.png"
    page.screenshot(path=str(path))
    log("saved", path)


def free_shots(page, base, out):
    load_with_zip(page, base)
    page.evaluate("window.scrollTo(0, 0)")
    shoot(page, out, "1_live")

    # 2: filtered to a popular make (the model picker is a modal whose
    # controls vary; a make-only filter is robust and reads the same).
    try:
        page.click("#live-filter-toggle"); page.wait_for_timeout(500)
        makes = page.eval_on_selector_all("#live-filter-make option", "els => els.map(e => e.value)")
        for make in ("Toyota", "Honda", "Subaru", "Ford"):
            if make in makes:
                page.select_option("#live-filter-make", make); page.wait_for_timeout(1200)
                if page.locator("#live-grid .car-card").count() >= 4:
                    break
        page.click("#live-filter-toggle"); page.wait_for_timeout(1200)
        page.evaluate("window.scrollTo(0, 0)")
        shoot(page, out, "2_search")
    except Exception as e:
        log("shot 2 failed:", str(e)[:120])
    page.keyboard.press("Escape"); page.wait_for_timeout(300)

    # 7: fitment — Parts tab
    try:
        page.locator('.tab[data-tab="parts"]').first.click(timeout=10000); page.wait_for_timeout(1000)
        page.fill("#pf-part", "alternator"); page.wait_for_timeout(800)
        opt = page.locator('[role="option"]:visible, .combo-item:visible').first
        if opt.count():
            opt.click(); page.wait_for_timeout(400)
        for sel, val in (("#pf-year", "2005"), ("#pf-make", "Toyota")):
            try:
                page.select_option(sel, val); page.wait_for_timeout(600)
            except Exception:
                pass
        try:
            page.select_option("#pf-model", "Camry"); page.wait_for_timeout(600)
        except Exception:
            pass
        if page.locator("#pf-zip").count():
            page.fill("#pf-zip", ZIP)
        # Multi-engine models ask which engine is in YOUR car: pick the first.
        eng = page.locator('button:has-text(" I4"), button:has-text(" V6"), button:has-text(" V8")').first
        if eng.count():
            eng.click(); page.wait_for_timeout(600)
        btn = page.locator('button:has-text("Find donor cars"):visible').first
        if btn.count():
            btn.click(); page.wait_for_timeout(5000)
        res = page.locator('#pf-results .pf-results-head, #pf-results .car-card').first
        if res.count():
            res.evaluate("el => { el.scrollIntoView({block: 'start'}); window.scrollBy(0, -(document.querySelector('header')?.offsetHeight || 90) - 60); }")
            page.wait_for_timeout(500)
        shoot(page, out, "7_fitment")
    except Exception as e:
        log("shot 7 failed:", str(e)[:120])

    # 6 + 3: Yards tab in a fresh page (the Parts flow leaves state that
    # makes the tab bar unreachable for the driver). Each shot fails alone.
    try:
        page = page.context.new_page()
        load_with_zip(page, base)
        page.locator('.tab[data-tab="yards"]').first.click(timeout=10000)
        page.wait_for_selector("#yards-grid .yard-card", timeout=30000); page.wait_for_timeout(1500)
    except Exception as e:
        log("yards tab failed:", str(e)[:120])
    try:
        cmp_in = page.locator('input[placeholder*="Compare" i]').first
        cmp_in.fill("Alternator", timeout=5000); page.wait_for_timeout(800)
        opt = page.locator('[role="option"], .combo-item').first
        try:
            opt.click(timeout=3000); page.wait_for_timeout(300)
        except Exception:
            page.keyboard.press("Enter")
        page.get_by_role("button", name="Compare", exact=True).first.click(timeout=5000); page.wait_for_timeout(2500)
        cmp_in.evaluate("el => { el.scrollIntoView({block: 'start'}); window.scrollBy(0, -(document.querySelector('header')?.offsetHeight || 90) - 10); }")
        page.wait_for_timeout(400)
        shoot(page, out, "6_compare")
    except Exception as e:
        log("shot 6 failed:", str(e)[:120])
    try:
        page.reload(wait_until="domcontentloaded"); page.wait_for_selector("#live-grid .car-card", timeout=90000); page.wait_for_timeout(800)
        page.locator('.tab[data-tab="yards"]').first.click(timeout=10000)
        page.wait_for_selector("#yards-grid .yard-card", timeout=60000); page.wait_for_timeout(2000)
        first = page.locator("#yards-grid .yard-card").first
        first.evaluate("el => { el.scrollIntoView({block: 'start'}); window.scrollBy(0, -(document.querySelector('header')?.offsetHeight || 90) - 60); }")
        page.wait_for_timeout(400)
        shoot(page, out, "3_yards")
    except Exception as e:
        log("shot 3 failed:", str(e)[:120])

    # 4: alerts
    try:
        page.locator('.tab[data-tab="alerts"]').first.click(timeout=10000); page.wait_for_timeout(2500)
        page.evaluate("window.scrollTo(0, 0)")
        shoot(page, out, "4_alerts")
    except Exception as e:
        log("shot 4 failed:", str(e)[:120])


def pro_shot(page, base, out):
    load_with_zip(page, base)
    try:
        page.click("#live-filter-toggle"); page.wait_for_timeout(400)
        page.select_option("#live-sort", "gold-first"); page.wait_for_timeout(1500)
        page.click("#live-filter-toggle"); page.wait_for_timeout(800)
    except Exception as e:
        log("pro sort:", str(e)[:80])
    # first card with >= 4 priced rows and a real pull cost on each
    idx = page.evaluate("""() => {
        const cards = [...document.querySelectorAll('#live-grid .car-card')];
        return cards.findIndex(c => {
            const rows = [...c.querySelectorAll('li.part-item')];
            const priced = rows.filter(li => /\\$/.test(li.querySelector('.part-price')?.textContent || '')).length;
            const nocost = rows.some(li => !/\\$/.test(li.querySelector('.part-cost')?.textContent || ''));
            return priced >= 4 && !nocost;
        });
    }""")
    if idx is None or idx < 0:
        idx = 0
    card = page.locator("#live-grid .car-card").nth(idx)
    s = card.locator("details summary").first
    if s.count():
        s.click(); page.wait_for_timeout(500)
    # Frame the chosen card right under the sticky header (no sliver of the
    # card above it).
    card.evaluate("el => { el.scrollIntoView({block: 'start'}); window.scrollBy(0, -(document.querySelector('header')?.offsetHeight || 90) - 10); }")
    page.wait_for_timeout(500)
    shoot(page, out, "5_pro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8765/")
    ap.add_argument("--out", type=Path, default=Path("fastlane/screenshots/en-US"))
    ap.add_argument("--android-out", type=Path, default=Path("fastlane/metadata/android/en-US/images/phoneScreenshots"))
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    args = ap.parse_args()
    global THEME
    THEME = args.theme
    with sync_playwright() as p:
        # Pre-installed browser on the cloud runner (a pip-installed
        # playwright can't find its own); set PW_CHROMIUM elsewhere if needed.
        exe = os.environ.get("PW_CHROMIUM")
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for ios, out in ((True, args.out), (False, args.android_out)):
            out.mkdir(parents=True, exist_ok=True)
            label = "iOS" if ios else "Android"
            log(f"== {label} ->", out)
            ctx = new_ctx(browser, ios=ios, pro=False); page = ctx.new_page()
            free_shots(page, args.base, out); ctx.close()
            ctx = new_ctx(browser, ios=ios, pro=True); page = ctx.new_page()
            pro_shot(page, args.base, out); ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
