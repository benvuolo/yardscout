#!/usr/bin/env python3
"""The U-Pull-R reader stays switched off until their API or feed arrives
(2026-11-17). While `UPULLR_READER_ENABLED` is False nothing of ours may be
sent to upullrparts.com: not the inventory reader, not the price-list refresh.

This test FAILS if the switch is turned on. That is on purpose: turning it on
is a decision (their API arrived, or the owner said so), never an accident.
To turn it on, follow ops/yards.md "U-Pull-R reader is switched off" and
change this test in the same commit.

Run:  python3 scraper/test_upullr_switch.py   (offline; every network call
made while it runs is refused and counted)"""
import inspect
import re
import socket
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


# Refuse and count every outgoing request, at two levels: the one place all
# `requests` calls pass through, and the socket under everything else.
attempts: list[str] = []


def _refuse_send(self, request, **kwargs):
    attempts.append(f"{request.method} {request.url}")
    raise requests.exceptions.ConnectionError("test: network is off")


def _refuse_connect(self, address, *a, **k):
    attempts.append(f"socket {address}")
    raise OSError("test: network is off")


_real_send = requests.sessions.Session.send
_real_connect = socket.socket.connect
requests.sessions.Session.send = _refuse_send
socket.socket.connect = _refuse_connect
_real_sleep = js.time.sleep
js.time.sleep = lambda *_a, **_k: None

try:
    check("the switch exists and is OFF (see the docstring before changing this)",
          getattr(js, "UPULLR_READER_ENABLED", None) is False,
          repr(getattr(js, "UPULLR_READER_ENABLED", "missing")))

    # 1. The inventory reader sends nothing and returns no cars.
    attempts.clear()
    rows = js.fetch_upullr_inventory()
    check("inventory reader: no request sent", attempts == [], attempts)
    check("inventory reader: returns no cars", rows == [], rows[:2])

    # 2. The price-list refresh sends nothing and leaves the file alone.
    price_file = js.DATA_DIR / "upullr_pricing.json"
    before = price_file.read_bytes() if price_file.exists() else None
    attempts.clear()
    ret = js.refresh_upullr_pricing_file()
    after = price_file.read_bytes() if price_file.exists() else None
    check("price-list refresh: no request sent", attempts == [], attempts)
    check("price-list refresh: existing file untouched", before == after and ret == price_file)

    # 3. Off on purpose is not reported as a broken adapter on every scan.
    check("zero-vehicle alarm skips the switched-off source",
          js.independent_sources_switched_off() == {"upullr"},
          js.independent_sources_switched_off())
    check("the reader is still registered (so switching on needs no re-wiring)",
          any(fn is js.fetch_upullr_inventory for _l, fn in js.INDEPENDENT_FETCHERS)
          and "upullr" in js.INDEPENDENT_EXPECTED_SOURCES)

    # 4. No other code path may reach their site: every function that names
    #    their host or its URL constants checks the switch before it does
    #    anything on the network.
    names = re.compile(r"UPR_AJAX|UPR_PRICING_URL|UPR_HEADERS|upullrparts\.com")
    touching = []
    for fname, fn in inspect.getmembers(js, inspect.isfunction):
        if fn.__module__ != js.__name__:
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            continue
        # Comments do not count (the Ario config explains why U-Pull-R is
        # NOT read through Ario, and names the host while doing so).
        code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
        code = re.sub(r'""".*?"""', "", code, flags=re.S)
        if not names.search(code):
            continue
        touching.append(fname)
        guard = code.find("if not UPULLR_READER_ENABLED:")
        first_net = min([i for i in (code.find("requests."), code.find(".post("),
                                     code.find(".get(UPR"), code.find("urlopen"))
                         if i >= 0] or [len(code)])
        check(f"{fname}: checks the switch before any request",
              0 <= guard < first_net, f"guard at {guard}, first network use at {first_net}")
    check("exactly the two known functions name U-Pull-R's site",
          sorted(touching) == ["fetch_upullr_inventory", "refresh_upullr_pricing_file"], touching)

    # 5. Self-check of this test: with the switch forced on in memory the
    #    reader DOES try to call their site (and is refused here), which shows
    #    it is the switch, not luck, that keeps the scan quiet.
    js.UPULLR_READER_ENABLED = True
    try:
        attempts.clear()
        js.fetch_upullr_inventory()
        check("self-check: with the switch on, the reader would call their site",
              any("upullrparts.com" in a for a in attempts), attempts)
        check("self-check: on, the source is expected again",
              js.independent_sources_switched_off() == set())
    finally:
        js.UPULLR_READER_ENABLED = False
    attempts.clear()
    js.fetch_upullr_inventory()
    check("self-check: off again, silent again", attempts == [], attempts)
finally:
    requests.sessions.Session.send = _real_send
    socket.socket.connect = _real_connect
    js.time.sleep = _real_sleep

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall passed")
