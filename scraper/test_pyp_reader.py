#!/usr/bin/env python3
"""LKQ Pick Your Part reader: a failed page gets one retry, and a read that
stops early says why (2026-11-18: 17 yards stopped after 25 or 50 cars in one
scan, silently).

Run:  python3 scraper/test_pyp_reader.py   (offline; a fake session answers)"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests  # noqa: E402
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


STORE = {"code": "1134", "name": "Pick Your Part - Test", "city": "Testville", "state": "CA",
         "lat": 34.0, "lng": -118.0}


def page_html(start, n):
    rows = []
    for i in range(start, start + n):
        rows.append(
            f'<div class="pypvi_resultRow" id="1134-{i}">'
            f'<div class="pypvi_ymm">2004 Toyota Tacoma</div>'
            f'<div class="pypvi_detailItem">Silver · 1134-{i}</div>'
            f'<div class="pypvi_detailItem">VIN 5TENL42N24Z{i:06d}</div>'
            f'<div class="pypvi_available"><time datetime="2026-11-17T00:00:00">Nov 17</time></div>'
            f'<table class="locate"><tr><td><span>Row</span><b>{i % 40}</b></td></tr></table>'
            f'</div>')
    return "<div>" + "".join(rows) + "</div>"


class Resp:
    def __init__(self, status, text="", headers=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}


class FakeSession:
    """Answers page N from a script: a list of answers per page, used in order."""
    def __init__(self, script):
        self.script = {p: list(a) for p, a in script.items()}
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        p = params["page"]
        self.calls.append(p)
        ans = self.script[p].pop(0)
        if isinstance(ans, Exception):
            raise ans
        return ans


sleeps = []
js.time.sleep = lambda s: sleeps.append(s)


def run(script):
    sleeps.clear()
    s = FakeSession(script)
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        cars = js._fetch_pyp_store_inventory(STORE, s)
    return cars, s.calls, err.getvalue()


# 1. A 503 on page 2, then it works: all cars, one pause of the default length.
cars, calls, log = run({0: [Resp(200, page_html(0, 20))],
                        1: [Resp(503), Resp(200, page_html(20, 5))]})
check("503 then 200: every car read", len(cars) == 25, f"{len(cars)} cars")
check("...page 2 asked twice", calls == [0, 1, 1], str(calls))
check("...one pause before the retry", js.PYP_RETRY_WAIT in sleeps, str(sleeps))
check("...nothing logged as failed", "failed" not in log, log)

# 2. A 403 is not retried, and the stop is logged with the reason.
cars, calls, log = run({0: [Resp(200, page_html(0, 20))], 1: [Resp(403)]})
check("403: stops after the first page", len(cars) == 20, f"{len(cars)} cars")
check("...403 not retried", calls == [0, 1], str(calls))
check("...log names the yard, page and status",
      "Pick Your Part - Test: page 2 failed (HTTP 403)" in log and "stops at 20 cars" in log, log)

# 3. Two timeouts: one retry, then stop, and the log says it retried.
cars, calls, log = run({0: [Resp(200, page_html(0, 20))],
                        1: [requests.Timeout("t1"), requests.Timeout("t2")]})
check("timeout twice: stops at 20", len(cars) == 20, f"{len(cars)} cars")
check("...retried once", calls == [0, 1, 1], str(calls))
check("...log says Timeout after one retry", "Timeout (after one retry)" in log, log)

# 4. A 429 with Retry-After waits that long (capped at 30 s).
cars, calls, log = run({0: [Resp(429, headers={"Retry-After": "7"}), Resp(200, page_html(0, 3))]})
check("429 Retry-After 7: waits 7 s, then reads", sleeps == [7.0] and len(cars) == 3, f"{sleeps} {len(cars)}")
cars, calls, log = run({0: [Resp(429, headers={"Retry-After": "600"}), Resp(200, page_html(0, 3))]})
check("429 Retry-After 600: wait capped at 30 s", sleeps == [30.0], str(sleeps))

# 5. A normal read: no retries, no pauses beyond the page pacing, no log.
cars, calls, log = run({0: [Resp(200, page_html(0, 20))], 1: [Resp(200, page_html(20, 20))],
                        2: [Resp(200, page_html(40, 4))]})
check("normal read: 44 cars over 3 pages", len(cars) == 44 and calls == [0, 1, 2], f"{len(cars)} {calls}")
check("...no retry pause", js.PYP_RETRY_WAIT not in sleeps, str(sleeps))
check("...quiet log", log == "", log)

print(f"\n{len(fails)} FAILURE(S)" if fails else "\nall passed")
sys.exit(1 if fails else 0)
