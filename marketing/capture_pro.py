#!/usr/bin/env python
"""Capture the YardScout web app in PRO state (server + Playwright in one process)."""
import subprocess, sys, time

DOCS = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/docs"
OUT = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter/marketing/pro_capture.png"
PORT = 8777

server = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
    cwd=DOCS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 393, "height": 852},
                                  device_scale_factor=3)
        ctx.add_init_script("""
            localStorage.setItem('jh_pro', '1');
            localStorage.setItem('jh_pro_source', 'iap');
            localStorage.setItem('jh_honesty_ack', '1');
        """)
        page = ctx.new_page()
        page.goto(f"http://localhost:{PORT}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Seed zip via the banner if it's showing
        banner = page.locator("#zip-banner-input")
        if banner.is_visible():
            banner.fill("84101")
            page.click("#zip-banner-go")
            print("zip banner filled")
        else:
            print("zip banner not visible; state:", page.evaluate("localStorage.getItem('jh_zip')"))

        page.wait_for_timeout(10000)  # inventory load + render

        # Diagnostics: pro flag took? any lock chips in DOM?
        diag = page.evaluate("""() => ({
            pro: localStorage.getItem('jh_pro'),
            src: localStorage.getItem('jh_pro_source'),
            lockChips: document.querySelectorAll('.lock-chip').length,
            cards: document.querySelectorAll('#live-grid details.parts-details').length,
        })""")
        print("diag:", diag)

        # Expand the first car card's parts dropdown so unlocked names+values show
        first = page.locator("#live-grid details.parts-details summary").first
        first.scroll_into_view_if_needed()
        first.click()
        page.wait_for_timeout(800)

        # Scroll so the expanded parts list fills the frame nicely:
        # put the top of the first card near the top of the viewport.
        page.evaluate("""() => {
            const d = document.querySelector('#live-grid details.parts-details[open]');
            const card = d ? d.closest('.car-card') || d.parentElement : null;
            const el = card || d;
            if (el) {
                const y = el.getBoundingClientRect().top + window.scrollY - 70;
                window.scrollTo(0, Math.max(0, y));
            }
        }""")
        page.wait_for_timeout(600)

        page.screenshot(path=OUT)
        print("saved", OUT)
        browser.close()
finally:
    server.terminate()
    server.wait()
