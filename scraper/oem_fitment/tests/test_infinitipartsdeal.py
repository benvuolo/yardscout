#!/usr/bin/env python3
"""Offline test for sites/infinitipartsdeal.py (rules shared with Nissan).
Pure checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_infinitipartsdeal.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import infinitipartsdeal as I  # noqa: E402
from sites import nissanpartsdeal as N  # noqa: E402

B = "https://www.infinitipartsdeal.com"
G35 = f"{B}/infiniti-g35-parts.html"
COUPE05 = f"{B}/2005-infiniti-g35-coupe-parts.html"
THR = f"{B}/parts-list/2004-infiniti-g35-coupe/fuel_engine_control/throttle_chamber.html"
P_THR = f"{B}/parts/infiniti-service-file-ch~16119-8j103.html"     # engine-only cells, MultiSupersession
P_ALT = f"{B}/parts/infiniti-alternator-asmy~23100-jk01a.html"     # 15 rows across EX/FX/G/M/QX

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


ok(I.CFG.parts is N.PARTS and I.CFG.subcats is N.SUBCATS, "rules shared with Nissan")
ok(I.MODELS[("Infiniti", "G37X")].inc == r"^sedan$", "G37X -> sedan catalogs")
import re  # noqa: E402
ok(re.search(N.PARTS["gauge-cluster"][0], "Meter Assy-Analog | Meter Assy-Analog |  | ")
   and not re.search(N.PARTS["gauge-cluster"][0], "Meter Assy-Temperature | Meter Assy-Temperature |  | F/COMPASS"),
   "2004 G35 coupe cluster 24820-AC700 'Meter Assy-Analog' (audit 2026-11-05)")
pure = n

if not _pg_cacheonly.have([G35, COUPE05, THR, P_THR, P_ALT]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

ok(I.T.year_catalogs(I.CFG, "Infiniti", "G35", 2005) == [("coupe", COUPE05)], "2005 G35: coupe catalog only on this site")
ok("16119-8J103" in [p["pn"] for p in I.parts_on_page(THR, "throttle-body")], "throttle list")
t = I.product(P_THR)
ok(t["replaced_by"] == "(MultiSupersession)" and t["replaces"] == ["16119-8J100", "16119-8J101", "16119-8J10B"], "supersession raw")
ok([(f["model"], f["trims"], f["engines"]) for f in t["fitment"][:3]] ==
   [("FX35", [], ["6 Cyl 3.5L"]), ("FX45", [], ["6 Cyl 3.5L"]), ("G35", ["Basic", "Sport", "Track"], ["6 Cyl 3.5L"])], "engine-only cells")
ok(t["fitment"][1]["raw"] == "2003-2007 Infiniti FX45 | 6 Cyl 3.5L | VQ35DE", "raw as printed")
a = I.product(P_ALT)
ok(len(a["fitment"]) == 15 and a["replaced_by"] == "2310M-JK01ARW", "alternator rows")
ok((a["fitment"][0]["years"], a["fitment"][0]["model"]) == ([2008, 2010], "EX35"), "first row")
print(f"OK {n} checks ({pure} pure)")
