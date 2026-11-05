#!/usr/bin/env python3
"""Pure checks for sites/_partsgiant.py (no pages needed).
Run: python3 scraper/oem_fitment/tests/test_partsgiant_template.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import _partsgiant as T  # noqa: E402

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


ok(T.slug("F-150") == "f_150" and T.slug("Town & Country") == "town_country", "slug")
ok(T.slug("E-350 / E-350 Super Duty") == "e_350_e_350_super_duty", "slug multi")
html = '<script id="initialState">\n window.__INITIAL_STORE__ = {"a":undefined,"b":"undefined","c":[undefined,1]};</script>'
ok(T.store(html) == {"a": None, "b": "undefined", "c": [None, 1]}, "store undefined")
m = T.YEARS_RE.match("2002, 1999-2000 Chevrolet Silverado")
ok(m and T.SPAN_RE.findall(m.group(1)) == [("2002", ""), ("1999", "2000")] and m.group(2) == "Chevrolet"
   and m.group(3) == "Silverado", "multi-span")
m = T.YEARS_RE.match("2012-2015 Chevrolet Captiva Sport")
ok(m and m.group(3) == "Captiva Sport", "model with space")
ok(T._list_position(["Location: Driver Side", "Fitting Vehicle Options: Z"]) == "Location: Driver Side", "location")
ok(T._list_position(["Right [GTS], [JP5]"]) == "Right", "mopar bare side")
ok(T._list_position(["RIGHT BANK", "Replaced By: 16119-JK20D"]) == "RIGHT BANK", "verbatim phrase")
ok(T._list_position(["CVT", "Fitting Vehicle Options: QR25DE"]) is None, "no side words")
ok(T._list_position(["Fitting Vehicle Options: Z(LY7)"]) is None, "no side")
ok(T._split("Base, S") == ["Base", "S"] and T._split("") == [], "split")
ok(T.COMMON_EXCLUDE.search("BULB, Capsule/Headlamp") and not T.COMMON_EXCLUDE.search("HEADLAMP, Capsule/Headlamp"), "common")
ok(not T.COMMON_EXCLUDE.search("Lamp Assy - Rear, Stop And Flasher | Housing - Throttle Plate"), "stop/plate kept")
ok(T.REMAN_RE.search("Remanufactured [BAE]") and T.REMAN_RE.search("New Part For Core Return"), "reman")
print(f"OK {n} checks")
