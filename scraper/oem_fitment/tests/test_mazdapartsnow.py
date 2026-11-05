#!/usr/bin/env python3
"""Offline test for sites/mazdapartsnow.py (SimplePart "giant" variant with
product-page checks for door side and switch position).
Pure checks always run; page checks read the fetch.py cache only and are
skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_mazdapartsnow.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import mazdapartsnow as M  # noqa: E402
from sites._simplepart import NavError  # noqa: E402

B = "https://www.mazdapartsnow.com"
L = f"{B}/parts-list/2008-mazda-3"
YEAR = f"{B}/2008-mazda-3-parts"
ALT, DOORS, FDOOR, FUEL = (f"{L}/charging-starting/alternator", f"{L}/body-hardware/door-components",
                           f"{L}/body-hardware/front-door", f"{L}/air-fuel-delivery/fuel-supply")
P_ALT = f"{B}/genuine/mazda~alternator~l3m618300r0a"
P_RDOOR = f"{B}/genuine/mazda~door-shell~bnyb7202xd"
P_SW = f"{B}/genuine/mazda~window-switch~bn8f66350a"

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


T = M._T
ok(T.year_url("Mazda", "Mazda3", 2008) == f"{B}/2008-mazda-3-parts", "Mazda3 slug")
ok(T.year_url("Mazda", "CX-9", 2010) == f"{B}/2010-mazda-cx_9-parts", "underscore slug")
ok(T.year_url("Mazda", "MX-5 Miata", 2003) == f"{B}/2003-mazda-miata-parts", "miata <= 2005")
ok(T.year_url("Mazda", "MX-5 Miata", 2007) == f"{B}/2007-mazda-mx_5_miata-parts", "mx_5_miata >= 2006")
for model in ("B-Series", "Truck"):
    try:
        T.year_url("Mazda", model, 2000)
        ok(False, f"{model} should not navigate")
    except NavError:
        ok(True, "")
ok(not T.match("fuel-pump-module", "Fuel Pump", "") and T.match("fuel-pump-module", "Fuel Pump Assembly", ""), "fuel")
ok(T.match("tail-lights", "Lens & Housing", "") and not T.match("tail-lights", "Lens & Housing Gasket", ""), "tail")
pure = checks

if not _cacheonly.have([YEAR, ALT, DOORS, FDOOR, FUEL, P_ALT, P_RDOOR, P_SW]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

cats = M.categories_for("Mazda", "Mazda3", 2008, ["alternator", "door-front", "door-rear", "tailgate"])
ok(cats == {"alternator": [ALT], "door-front": [DOORS], "door-rear": [DOORS]}, cats)

front = {p["pn"]: p for p in M.parts_on_page(DOORS, "door-front")}
rear = {p["pn"]: p for p in M.parts_on_page(DOORS, "door-rear")}
ok(sorted(front) == ["BNYV-58-02XJ", "BNYV-59-02XJ", "BPYK-58-02XJ", "BPYK-59-02XJ"], sorted(front))
ok(sorted(rear) == ["BNYB-72-02XD", "BNYB-73-02XD", "BNYF-72-02XE", "BNYF-73-02XE"], sorted(rear))
ok(not set(front) & set(rear), "a shell is front or rear, never both")
ok(rear["BNYB-72-02XD"]["product_check"] == "'Rear Door' in 'Door Shell | Body(Right), Rear Door | Position: Passenger Side'",
   rear["BNYB-72-02XD"]["product_check"])
sw = M.parts_on_page(FDOOR, "window-switch")
ok([p["pn"] for p in sw] == ["BN8F-66-350A"], [p["pn"] for p in sw])  # passenger B32H-66-370 dropped
fuel = [p["pn"] for p in M.parts_on_page(FUEL, "fuel-pump-module")]
ok("L3K9-13-35ZC" not in fuel and "LF66-13-35XG" in fuel, fuel)  # high-pressure pump out

alt = [p["pn"] for p in M.parts_on_page(ALT, "alternator")]
ok(alt == ["L3M6-18-300R-0A", "LF1F-18-300R-0A"], alt)

p = M.product(P_ALT)  # two-model block, catalog prints model "3" / "6"
ok([(f["years"], f["make"], f["model"]) for f in p["fitment"]] == [([2007, 2009], "Mazda", "3"), ([2006, 2007], "Mazda", "6")], p["fitment"])
ok("flags" not in p, p.get("flags"))
p = M.product(P_RDOOR)
ok(p["position"] == "Passenger Side" and len(p["replaces"]) == 6 and p["replaces"][0] == "BNYB-72-02X", p["replaces"])
ok(p["fitment"][0]["years"] == [2004, 2009] and "flags" not in p, p.get("flags"))
p = M.product(P_SW)
ok(p["position"] == "Driver Side" and p["replaces"] == ["BN8F-66-350"], p)

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
