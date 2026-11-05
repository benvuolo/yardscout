#!/usr/bin/env python3
"""Offline test for sites/vwpartsgiant.py (SimplePart "giant" variant:
/<year>-volkswagen-<model>-parts year pages, /genuine/ product pages).
Pure checks always run; page checks read the fetch.py cache only and are
skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_vwpartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import vwpartsgiant as V  # noqa: E402

B = "https://www.vwpartsgiant.com"
YEAR = f"{B}/2006-volkswagen-jetta-parts"
ALT = f"{B}/parts-list/2006-volkswagen-jetta/charging-starting/alternator"
FUEL = f"{B}/parts-list/2006-volkswagen-jetta/air-fuel-delivery/fuel-supply"
MIRR = f"{B}/parts-list/2006-volkswagen-jetta/body-hardware/outside-mirrors"
P_NEW = f"{B}/genuine/volkswagen~alternator~06f903023f"
P_X = f"{B}/genuine/volkswagen~alternator~06f903023fx"
P_WS = f"{B}/genuine/volkswagen~compressor~1k0820808f"

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


m = V._T.match
ok(m("alternator", "Alternator", ""), "alternator")
ok(not m("alternator", "Voltage Regulator", ""), "regulator")
ok(m("fuel-pump-module", "Fuel Pump Assembly", ""), "in-tank assembly")
ok(not m("fuel-pump-module", "Fuel Pump", ""), "plain Fuel Pump (may be the engine HP pump) excluded")
ok(m("side-mirrors", "Housing Assembly", "") and not m("side-mirrors", "Mirror Glass", ""), "mirror names")
ok(not m("bumper-front", "Bumper Cover Screw", ""), "screw")
ok(V._T.year_url("Volkswagen", "New Beetle", 2005) == f"{B}/2005-volkswagen-beetle-parts", "year url / slug")
ok("door-front" not in V.CAT_PAGES and "door-rear" not in V.CAT_PAGES, "doors not crawled (front/rear not printed)")
pure = checks

if not _cacheonly.have([YEAR, ALT, FUEL, MIRR, P_NEW, P_X, P_WS]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = V.categories_for("Volkswagen", "Jetta", 2006, ["alternator", "side-mirrors", "door-front", "liftgate"])
ok(cats == {"alternator": [ALT], "side-mirrors": [MIRR]}, cats)

alt = {p["pn"]: p for p in V.parts_on_page(ALT, "alternator")}
ok(sorted(alt) == ["06F-903-023-F", "06F-903-023-FX"], sorted(alt))
# FX is on a "New" row and a "Remanufactured" row: not reman, so not dropped
ok(alt["06F-903-023-FX"]["reman"] is False and len(alt["06F-903-023-FX"]["list_notes"]) == 2, alt["06F-903-023-FX"])
ok(alt["06F-903-023-F"]["product_url"] == P_NEW, alt["06F-903-023-F"]["product_url"])
fuel = [p["pn"] for p in V.parts_on_page(FUEL, "fuel-pump-module")]
ok(fuel == ["1K0-919-050-AB", "1K0-919-051-DB"] and "06F-127-025-M" not in fuel, fuel)
mir = V.parts_on_page(MIRR, "side-mirrors")
ok(len(mir) == 4 and all(p["category_note"].startswith("VW lists the outside mirror") for p in mir), mir[:1])

p = V.product(P_NEW)  # 7-row multi-model block
ok(p["pn"] == "06F-903-023-F" and p["replaces"] == [] and "flags" not in p, p.get("flags"))
rows = [(f["years"], f["model"]) for f in p["fitment"]]
ok(rows == [([2013, 2016], "Beetle"), ([2007, 2008], "Eos"), ([2010, 2014], "Golf"), ([2012, 2013], "Golf R"),
            ([2006, 2009], "GTI"), ([2005, 2015], "Jetta"), ([2006, 2008], "Passat")], rows)
ok(p["fitment"][5]["make"] == "Volkswagen" and p["fitment"][0]["trims"] == ["R-Line S", "R-Line SE", "R-Line SEL", "TDI"], p["fitment"][0])

p = V.product(P_X)  # reman exchange number, multi-span first row
ok(p["replaces"] == ["07K-903-023-AX"] and "flags" not in p, p.get("flags"))
ok([f["years"] for f in p["fitment"][:2]] == [[2013, 2015], [2006, 2006]], p["fitment"][:2])
ok(p["fitment"][0]["raw"].startswith("2013-2015, 2006 Volkswagen Beetle | 2.5, TDI | "), p["fitment"][0]["raw"])

p = V.product(P_WS)  # page HTML prints "2020-2022,  2012-2015, 2006-2010 ... Passat" (two spaces)
ok("flags" not in p and p["fitment_rows_total"] == 8, p.get("flags"))
ok([f["years"] for f in p["fitment"] if f["model"] == "Passat"] == [[2020, 2022], [2012, 2015], [2006, 2010]], p["fitment"])
ok(any("2020-2022,  2012-2015" in ln for ln in p["evidence_lines"]), "evidence keeps the page text")

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
