#!/usr/bin/env python3
"""Browser-level e2e: the real PWA (docs/) talking to the real backend, both
local — verifies the api.js scaffold end-to-end in a browser:

  static-fallback OFF-state → API inventory load (shard assembly, vpic re-key)
  → magic-link sign-in via the account UI → free tier (values hidden) →
  admin grant → Pro (values visible, pill active) → sign out.

Prereqs (already true in this repo's .venv): playwright + chromium.
Run from backend/:  ../.venv/bin/python test/browser_e2e.py
The script starts and tears down its own wrangler dev + static file server.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
API_PORT, WEB_PORT = 8791, 8792
API = f"http://127.0.0.1:{API_PORT}"
WEB = f"http://127.0.0.1:{WEB_PORT}"
UPLOAD_TOKEN, ADMIN_SECRET = "bt-upload", "bt-admin"
OUT = BACKEND / "test" / ".out"
OUT.mkdir(parents=True, exist_ok=True)

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"  [{detail}]" if detail and not cond else ""))


def wait_http(url, tries=60):
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    env_file = BACKEND / ".dev.vars.browser"
    env_file.write_text(
        f"DEV_MODE=1\nUPLOAD_TOKEN={UPLOAD_TOKEN}\nADMIN_SECRET={ADMIN_SECRET}\n"
        f"APP_URL={WEB}/index.html\n"
        f"APP_ORIGINS=https://benvuolo.github.io,{WEB},http://localhost:{WEB_PORT}\n"
    )
    state = OUT / "wrangler-state-browser"
    import shutil
    shutil.rmtree(state, ignore_errors=True)  # fresh D1 every run
    subprocess.run(
        ["npx", "wrangler", "d1", "migrations", "apply", "yardscout-db", "--local",
         "--persist-to", str(state)],
        cwd=BACKEND, check=True, capture_output=True,
    )
    api_proc = subprocess.Popen(
        ["npx", "wrangler", "dev", "--port", str(API_PORT), "--env-file", str(env_file),
         "--persist-to", str(state)],
        cwd=BACKEND, stdout=(OUT / "browser-api.log").open("w"), stderr=subprocess.STDOUT,
    )
    web_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", "127.0.0.1"],
        cwd=ROOT / "docs", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        assert wait_http(f"{API}/v1/health"), "wrangler dev never came up"
        assert wait_http(f"{WEB}/index.html"), "static server never came up"

        subprocess.run(
            [sys.executable, str(ROOT / "scraper" / "push_inventory.py"),
             "--file", str(ROOT / "docs" / "data" / "inventory_live.json"),
             "--api", API, "--token", UPLOAD_TOKEN, "--max-yards", "6"],
            check=True, capture_output=True,
        )
        run_browser()
    finally:
        api_proc.terminate()
        web_proc.terminate()
        env_file.unlink(missing_ok=True)

    print(f"\n════ BROWSER RESULT: {len(passed)} passed, {len(failed)} failed ════")
    return 1 if failed else 0


def run_browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ── 1. default state: API OFF, static file loads as before ──────────
        page.goto(f"{WEB}/index.html", wait_until="domcontentloaded")
        page.wait_for_function("typeof liveLoaded !== 'undefined' && liveLoaded === true", timeout=30000)
        check("flag OFF: static inventory path still works",
              page.evaluate("liveInventory.length") > 100000)
        check("flag OFF: account UI stays hidden",
              page.evaluate("document.getElementById('account-wrap').style.display") == "none")

        # ── 2. API mode, anonymous → free variant ───────────────────────────
        page.goto(f"{WEB}/index.html?api=1&apibase={API}", wait_until="domcontentloaded")
        page.wait_for_function("typeof liveLoaded !== 'undefined' && liveLoaded === true", timeout=30000)
        n = page.evaluate("liveInventory.length")
        check("API mode: inventory loaded via backend (6 test yards)", 1000 < n < 20000, f"n={n}")
        check("API mode: vpic trims survived the shard round-trip",
              page.evaluate("liveInventory.filter(v => v.vpicTrim).length") > 0)
        check("anonymous: all maxValue stripped server-side",
              page.evaluate("liveInventory.reduce((m, v) => Math.max(m, v.maxValue || 0), 0)") == 0)
        check("anonymous: part names still present",
              page.evaluate("liveInventory.filter(v => v.topParts.length).length") > 0)
        check("account UI visible in API mode",
              page.evaluate("document.getElementById('account-wrap').style.display") != "none")

        # ── 3. magic-link sign-in through the real account UI ───────────────
        page.evaluate("openUpgradeSheet('browser-test')")
        page.fill("#account-email", "browser-tester@example.com")
        page.click("#account-send-link")
        # DEV_MODE: api.js auto-navigates to the dev_link → callback →
        # redirect back here with #session= → consumed on load.
        page.wait_for_url(re.compile(r".*index\.html.*"), timeout=15000)
        page.wait_for_function(
            "window.YSApi && !!YSApi.getToken() && !location.hash.includes('session=')",
            timeout=15000,
        )
        check("magic link round-trip: session stored, fragment stripped", True)
        page.wait_for_function("typeof liveLoaded !== 'undefined' && liveLoaded === true", timeout=30000)
        page.evaluate("openUpgradeSheet('browser-test')")
        page.wait_for_selector(".account-signedin", state="visible", timeout=10000)
        check("signed in as the tester",
              page.evaluate("document.getElementById('account-user').textContent")
              == "browser-tester@example.com")
        check("fresh account shows Free plan",
              "Free" in page.evaluate("document.getElementById('account-tier').textContent"))
        check("free session: values still stripped",
              page.evaluate("liveInventory.reduce((m, v) => Math.max(m, v.maxValue || 0), 0)") == 0)

        # ── 4. admin grant → Pro data + gates ────────────────────────────────
        req = urllib.request.Request(
            f"{API}/v1/admin/grant",
            data=json.dumps({"email": "browser-tester@example.com", "tier": "pro"}).encode(),
            headers={"x-admin-secret": ADMIN_SECRET, "content-type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("typeof liveLoaded !== 'undefined' && liveLoaded === true", timeout=30000)
        page.wait_for_function("localStorage.getItem('jh_pro') === '1'", timeout=15000)
        check("pro grant flows into the app's Pro gate (jh_pro set by account)", True)
        check("pro session: real dollar values delivered",
              page.evaluate("liveInventory.reduce((m, v) => Math.max(m, v.maxValue || 0), 0)") > 0)
        check("Pro pill lit",
              page.evaluate("document.getElementById('pro-pill').classList.contains('active')"))

        # ── 5. sign out clears account-sourced Pro ───────────────────────────
        page.evaluate("openUpgradeSheet('browser-test')")
        page.click("#account-logout")
        page.wait_for_function("!YSApi.getToken()", timeout=10000)
        check("logout: session cleared", True)
        check("logout: account-granted Pro revoked",
              page.evaluate("localStorage.getItem('jh_pro')") is None)

        check("no JS errors during the whole run", not errors, "; ".join(errors[:3]))
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
