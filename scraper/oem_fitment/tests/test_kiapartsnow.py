#!/usr/bin/env python3
"""Offline test for sites/kiapartsnow.py (PartsGiant ".html" template, rules
shared with hyundaipartsdeal.py). Pure checks always run; page checks read
the fetch.py cache only and are skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_kiapartsnow.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import kiapartsnow as K  # noqa: E402

B = "https://www.kiapartsnow.com"
MODEL = f"{B}/kia-optima-parts.html"
SOR = f"{B}/kia-sorento-parts.html"
KOR = f"{B}/2013-kia-optima-korean_made-parts.html"
GA = f"{B}/2013-kia-optima-us_georgia_made-parts.html"
L = f"{B}/parts-list/2013-kia-optima-us_georgia_made"
ALT = f"{L}/engine/alternator.html"
FREG = f"{L}/trim/front_door_window_regulator_glass.html"
DTRIM = f"{L}/trim/trim_front_door.html"
P_ALT = f"{B}/genuine/kia-alternator-assy~373002g600.html"   # Optima + Sorento, Replaced By a reman
P_MOD = f"{B}/genuine/kia-pnl-assy-fr-dr~824714c000.html"    # door module, side from list

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


ok(K.CFG.parts is K.PARTS and K.CFG.subcats is K.SUBCATS, "rules shared with Hyundai")
ok(K.T._mapping(K.CFG, "Kia", "Rio5", 2013).slugs == "rio" and K.T._mapping(K.CFG, "Kia", "Forte5", 2016).slugs == "forte", "hatch slugs")
pure = n

if not _pg_cacheonly.have([MODEL, SOR, KOR, GA, ALT, FREG, DTRIM, P_ALT, P_MOD]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

ok([v for v, _ in K.T.year_catalogs(K.CFG, "Kia", "Optima", 2013)] == ["korean_made", "us_georgia_made"], "optima plants")
ok([v for v, _ in K.T.year_catalogs(K.CFG, "Kia", "Sorento", 2006)][0] == "old_body_style", "sorento first gen preferred")
cats = K.categories_for("Kia", "Optima", 2013, ["alternator", "window-regulator", "window-switch"])
ok(ALT in cats["alternator"] and len(cats["alternator"]) == 2 and DTRIM in cats["window-switch"], f"nav {cats}")
ok([p["pn"] for p in K.parts_on_page(ALT, "alternator")] == ["373002G150", "373002G600"], "alternators")
ok([p["pn"] for p in K.parts_on_page(DTRIM, "window-switch")] == ["935702T000", "935702T030"], "master switch")
reg = [p["pn"] for p in K.parts_on_page(FREG, "window-regulator")]
ok(reg == ["824502T000", "824504C010", "824502T010", "824602T000", "824604C010", "824602T010", "824714C000", "824814C000"], reg)

a = K.product(P_ALT)  # multi-model block; pn printed without hyphen
ok(a["pn"] == "373002G600" and a["replaced_by"] == "373002G500RU" and a["replaces"] == [], a)
ok([(f["years"], f["make"], f["model"], f["engines"], f["options"]) for f in a["fitment"]] ==
   [([2011, 2013], "Kia", "Optima", ["2.0L - Theta 2"], ["Sedan - 4Door 5P"]),
    ([2009, 2012], "Kia", "Sorento", ["2.4L - Theta 2"], ["Wagon - 5Door 5P", "Wagon - 5Door 7P"])], a["fitment"])
ok(a["evidence_lines"][-2:] == ["2011-2013 Kia Optima | 2.0L - Theta 2 | Sedan - 4Door 5P",
                                "2009-2012 Kia Sorento | 2.4L - Theta 2 | Wagon - 5Door 5P, Wagon - 5Door 7P"], a["evidence_lines"])
m = K.product(P_MOD)
ok(m["description"] == "Panel Assembly-Front Door Module,LH" and m["position"] == "Location: Driver Side", m)
ok(m["fitment"][0]["raw"] == "2011-2013 Kia Optima | 2.0L - Theta 2, 2.4L - Theta 2 | Sedan - 4Door 5P", m["fitment"])
ok(m["flags"] == [], m["flags"])
print(f"OK {n} checks ({pure} pure)")
