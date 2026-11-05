#!/usr/bin/env python3
"""Offline test for sites/nissanpartsdeal.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_nissanpartsdeal.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import nissanpartsdeal as N  # noqa: E402

B = "https://www.nissanpartsdeal.com"
MODEL = f"{B}/nissan-altima-parts.html"
SEDAN = f"{B}/2012-nissan-altima-sedan-parts.html"
COUPE = f"{B}/2012-nissan-altima-coupe-parts.html"
L = f"{B}/parts-list/2012-nissan-altima-sedan"
ALT = f"{L}/engine_electrical/alternator.html"
MIRRORS = f"{L}/miscellaneous/rear_view_mirror.html"
SWITCH = f"{L}/body_electrical/switch.html"
REAR_REG = f"{B}/parts-list/2013-nissan-altima-sedan/body_side_rear/rear_door_window_regulator.html"
P_ALT = f"{B}/parts/nissan-alt-assy~23100-ja04d.html"            # Altima + Sentra, "Trim & Engine"
P_STARTER = f"{B}/parts/nissan-motor-assy-starter~23300-ja10c.html"  # 4 models, Replaced By
P_MOTOR = f"{B}/parts/nissan-motor-asmy-re~82731-3ta2a.html"     # side from list, Replaces

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, name, info=""):
    inc, exc_head, exc_full = (tuple(N.PARTS[cat]) + (None, None))[:3]
    text = f"{name} | {name} |  | {info}"
    return bool(re.search(inc, text, re.I) and not (exc_head and re.search(exc_head, f"{name} | {name} | ", re.I))
                and not (exc_full and re.search(exc_full, text, re.I)))


ok(match("side-mirrors", "Door Mirror Assy-LH") and match("side-mirrors", "Mirror Assy-Outside, RH"), "mirrors")
ok(not match("side-mirrors", "Glass-Mirror, LH") and not match("side-mirrors", "Mirror Assy-Inside"), "glass/inside")
ok(match("window-switch", "Switch Assy-Power Window, Main") and not match("window-switch", "Switch Assy-Power Window, Assist"), "master")
ok(match("climate-control", "Controller Assy-Air Conditiner"), "site's spelling 'Conditiner'")
ok(match("fuel-pump-module", "Fuel Pump-In Tank"), "in-tank pump")
ok(not match("ignition-coils", "", "") and not match("alternator", "", "Value Advantage Replacement Part"), "value advantage")
ok(match("trunk-lid", "Lid-Trunk", "W/ SPOILER,W/O CAM") and not match("trunk-lid", "Bar-Torsion, Trunk Lid LH"), "trunk")
pure = n

if not _pg_cacheonly.have([MODEL, SEDAN, COUPE, ALT, MIRRORS, SWITCH, REAR_REG, P_ALT, P_STARTER, P_MOTOR]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

ok([v for v, _ in N.T.year_catalogs(N.CFG, "Nissan", "Altima", 2012)] == ["sedan", "coupe"], "altima variants, hybrid excluded")
cats = N.categories_for("Nissan", "Altima", 2012, ["alternator", "side-mirrors"])
ok(ALT in cats["alternator"] and MIRRORS in cats["side-mirrors"] and len(cats["alternator"]) == 2, f"nav {cats}")
ok([p["pn"] for p in N.parts_on_page(ALT, "alternator")] == ["23100-JA11B", "23100-JA04D", "23100-JA04C"], "alternators")
mir = [p["pn"] for p in N.parts_on_page(MIRRORS, "side-mirrors")]
ok(len(mir) == 10 and "96302-JB17E" not in mir and "96321-CB01A" not in mir, f"mirrors {mir}")
sw = [p["pn"] for p in N.parts_on_page(SWITCH, "window-switch")]
ok(set(sw) >= {"25401-ZN40A", "25401-ZN50C"} and "25411-JA01A" not in sw and "25411-JA00A" not in sw, f"switches {sw}")

a = N.product(P_ALT)
ok(a["description"] == "Alternator; Generator" and a["replaces"] == ["23100-JA04A", "23100-JA04C"], "alt fields")
ok([(f["years"], f["model"], f["trims"], f["engines"], f["options"]) for f in a["fitment"]] ==
   [([2009, 2013], "Altima", ["Base", "S"], ["4 Cyl 2.5L"], ["QR25DE"]),
    ([2009, 2012], "Sentra", ["SE-R", "Spec V"], ["4 Cyl 2.5L"], ["QR25DE"])], "trim & engine split")
ok(a["evidence_lines"][-3:] == ["Year Make Model | Trim & Engine | Important vehicle option details",
                                "2009-2013 Nissan Altima | Base, S|4 Cyl 2.5L | QR25DE",
                                "2009-2012 Nissan Sentra | SE-R, Spec V|4 Cyl 2.5L | QR25DE"], "evidence")
s = N.product(P_STARTER)
ok(s["replaced_by"] == "2330M-JA12ARW" and [f["model"] for f in s["fitment"]] == ["Altima", "Maxima", "Murano", "Quest"], "starter")
N.parts_on_page(REAR_REG, "window-regulator")
m = N.product(P_MOTOR)
ok(m["position"] == "Location: Driver side" and m["replaces"] == ["82731-3TA1A"], f"motor {m['position']}")
ok([(f["years"], f["model"]) for f in m["fitment"]] == [([2013, 2018], "Altima"), ([2016, 2023], "Maxima"), ([2013, 2019], "Sentra")], "motor rows")
print(f"OK {n} checks ({pure} pure)")
