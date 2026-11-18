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
import signal
import socket
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


def port_busy(port):
    """True when something accepts connections on 127.0.0.1:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def need_ports(*ports):
    """Refuse to start (exit 2) when a port this suite uses is taken: never
    test against someone else's server (2026-11-17: e2e.sh failed 3 of 39 on
    a server an earlier run had left behind)."""
    busy = [p for p in ports if port_busy(p)]
    if busy:
        print(f"REFUSING TO START: port {', '.join(map(str, busy))}, needed by browser_e2e.py, "
              "is already in use. Another test is running, or an earlier run left a server "
              "behind. Stop it and run again.", file=sys.stderr)
        sys.exit(2)


def start_group(cmd, **kw):
    """Start cmd in a process group of its own, so stop_group() reaches every
    process under it (npx -> wrangler -> workerd; terminating the npx process
    alone left workerd on the port)."""
    return subprocess.Popen(cmd, start_new_session=True, **kw)


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def stop_group(proc, port=None):
    """TERM the whole group, KILL it after 5 s; with port, wait for it to close."""
    if proc is None:
        return
    pgid = proc.pid   # start_new_session: the child leads its own group
    for sig, wait_s in ((signal.SIGTERM, 5.0), (signal.SIGKILL, 2.0)):
        if not group_alive(pgid):
            break
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            break
        deadline = time.time() + wait_s
        while time.time() < deadline and group_alive(pgid):
            time.sleep(0.1)
    try:
        proc.wait(timeout=2)
    except Exception:
        pass
    if port is not None:
        for _ in range(50):
            if not port_busy(port):
                return
            time.sleep(0.1)
        print(f"WARNING: port {port} still in use after stopping its server", file=sys.stderr)


def wait_http(url, tries=60):
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    need_ports(API_PORT, WEB_PORT)
    # A runner's SIGTERM (or Ctrl-C) still runs the finally below.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
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
    api_proc = web_proc = None
    try:
        api_proc = start_group(
            ["npx", "wrangler", "dev", "--port", str(API_PORT), "--env-file", str(env_file),
             "--persist-to", str(state)],
            cwd=BACKEND, stdout=(OUT / "browser-api.log").open("w"), stderr=subprocess.STDOUT,
        )
        web_proc = start_group(
            [sys.executable, "-m", "http.server", str(WEB_PORT), "--bind", "127.0.0.1"],
            cwd=ROOT / "docs", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
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
        stop_group(api_proc, API_PORT)
        stop_group(web_proc, WEB_PORT)
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
        # A saved zip: a free visitor with no zip/watch/link loads nothing in
        # the background (2026-10-30), so give this one a view first.
        page.evaluate("localStorage.setItem('jh_zip', '84101')")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("typeof liveLoaded !== 'undefined' && liveLoaded === true", timeout=30000)
        # Radius-first shards: liveLoaded fires once the nearby shards are in;
        # the national total arrives when the background load completes.
        page.wait_for_function("typeof liveComplete !== 'undefined' && liveComplete === true", timeout=120000)
        check("flag OFF: static inventory path still works",
              page.evaluate("liveInventory.length") > 100000)
        page.evaluate("localStorage.removeItem('jh_zip')")   # later phases run zip-less as before
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
