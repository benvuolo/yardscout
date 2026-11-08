#!/usr/bin/env python3
"""iis-pro-upull page fetch: one patient retry on a read timeout only
(2026-11-08, Midway Muncie dropped after a single 60 s timeout).
Run:  python3 scraper/test_iis_timeout_retry.py   (offline)"""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


class Resp:
    status_code = 200
    text = '<div class="car-details-uPull">ok</div>'

    def raise_for_status(self):
        pass


SITE = js.IIS_UPULL_SITES["midwayupull"]
js.IIS_UPULL_TIMEOUT_RETRY_PAUSE = 0
calls = []


def timeout_then_ok(url, headers=None, timeout=None):
    calls.append(timeout)
    if len(calls) == 1:
        raise js.requests.Timeout("Read timed out")
    return Resp()


with mock.patch.object(js.requests, "get", side_effect=timeout_then_ok):
    out = js._iis_upull_get(SITE, "https://midwayupull.com/x")
check("timeout -> one retry -> page", out == Resp.text and calls == [60, 120], calls)

calls.clear()
with mock.patch.object(js.requests, "get", side_effect=js.requests.Timeout("t")) as g:
    out = js._iis_upull_get(SITE, "https://midwayupull.com/x")
check("two timeouts -> give up (no third try)", out is None and g.call_count == 2, g.call_count)

with mock.patch.object(js.requests, "get", side_effect=js.requests.ConnectionError("refused")) as g:
    out = js._iis_upull_get(SITE, "https://midwayupull.com/x")
check("other errors are not retried", out is None and g.call_count == 1, g.call_count)

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
