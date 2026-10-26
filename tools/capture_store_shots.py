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
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ZIP = "84047"
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
            "localStorage.setItem('ys_app_promo','1')", "localStorage.setItem('jh_visits','5')"]
    if pro:
        keys += ["localStorage.setItem('jh_pro','1')", "localStorage.setItem('jh_pro_source','iap')"]
    ctx.add_init_script("try { " + "; ".join(keys) + "; } catch(e) {}")
    return ctx


def load_with_zip(page, base):
    page.goto(base, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#zip-banner-input", state="visible", timeout=60000)
    page.fill("#zip-banner-input", ZIP)
    page.click("#zip-banner-go")
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

    # 2: filtered to a popular make/model
    try:
        page.click("#live-filter-toggle"); page.wait_for_timeout(500)
        makes = page.eval_on_selector_all("#live-filter-make option", "els => els.map(e => e.value)")
        best = None
        for make, model in [("Toyota", "Tacoma"), ("Toyota", "4Runner"), ("Honda", "Civic"), ("Toyota", "Camry"), ("Ford", "F-150"), ("Subaru", "Outback")]:
            if make not in makes:
                continue
            page.select_option("#live-filter-make", make); page.wait_for_timeout(700)
            page.click("#live-filter-model-btn"); page.wait_for_timeout(400)
            models = page.eval_on_selector_all("#live-filter-model-list input[data-model]", "els => els.map(e => e.dataset.model)")
            target = next((m for m in models if model.lower() in m.lower()), None)
            for el in page.locator("#live-filter-model-list input:checked").all():
                el.click()
            if target:
                page.click(f'#live-filter-model-list input[data-model="{target}"]')
            page.click("#live-filter-model-done"); page.wait_for_timeout(1000)
            n = page.locator("#live-grid .car-card").count()
            log(f"  {make} {target}: {n} cars")
            if target and (best is None or n > best[0]):
                best = (n, make, target)
            if target and n >= 6:
                break
        if best and (best[1], best[2]) != (make, target):
            page.select_option("#live-filter-make", best[1]); page.wait_for_timeout(700)
            page.click("#live-filter-model-btn"); page.wait_for_timeout(400)
            for el in page.locator("#live-filter-model-list input:checked").all():
                el.click()
            page.click(f'#live-filter-model-list input[data-model="{best[2]}"]')
            page.click("#live-filter-model-done"); page.wait_for_timeout(1000)
        page.click("#live-filter-toggle"); page.wait_for_timeout(1200)
        page.evaluate("window.scrollTo(0, 0)")
        shoot(page, out, "2_search")
    except Exception as e:
        log("shot 2 failed:", str(e)[:120])

    # 7: fitment — Parts tab
    try:
        page.click('.tab[data-tab="parts"]'); page.wait_for_timeout(1000)
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
        btn = page.locator('button:has-text("Find donor cars"):visible').first
        if btn.count():
            btn.click(); page.wait_for_timeout(4000)
        res = page.locator('#pf-results, .pf-results').first
        if res.count():
            res.scroll_into_view_if_needed(); page.wait_for_timeout(400)
            page.evaluate("window.scrollBy(0, -120)")
        shoot(page, out, "7_fitment")
    except Exception as e:
        log("shot 7 failed:", str(e)[:120])

    # 6: compare — Yards tab
    try:
        page.click('.tab[data-tab="yards"]'); page.wait_for_selector("#yards-grid .yard-card", timeout=30000); page.wait_for_timeout(1500)
        cmp_in = page.locator('input[placeholder*="Compare" i]:visible').first
        if cmp_in.count():
            cmp_in.fill("Alternator"); page.wait_for_timeout(800)
            opt = page.locator('[role="option"]:visible, .combo-item:visible').first
            if opt.count():
                opt.click(); page.wait_for_timeout(300)
            page.locator('button:has-text("Compare"):visible').first.click(); page.wait_for_timeout(2500)
            cmp_in.scroll_into_view_if_needed(); page.evaluate("window.scrollBy(0, -140)"); page.wait_for_timeout(400)
        shoot(page, out, "6_compare")
        # 3: plain yards list
        page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(1500)
        page.click('.tab[data-tab="yards"]'); page.wait_for_selector("#yards-grid .yard-card", timeout=60000); page.wait_for_timeout(2000)
        first = page.locator("#yards-grid .yard-card").first
        first.scroll_into_view_if_needed(); page.evaluate("window.scrollBy(0, -170)"); page.wait_for_timeout(400)
        shoot(page, out, "3_yards")
    except Exception as e:
        log("shot 6/3 failed:", str(e)[:120])

    # 4: alerts
    try:
        page.click('.tab[data-tab="alerts"]'); page.wait_for_timeout(2500)
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
    card.scroll_into_view_if_needed(); page.evaluate("window.scrollBy(0, -130)"); page.wait_for_timeout(500)
    shoot(page, out, "5_pro")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8765/")
    ap.add_argument("--out", type=Path, default=Path("fastlane/screenshots/en-US"))
    ap.add_argument("--android-out", type=Path, default=Path("fastlane/metadata/android/en-US/images/phoneScreenshots"))
    args = ap.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch()
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
