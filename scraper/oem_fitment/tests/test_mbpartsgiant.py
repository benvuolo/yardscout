#!/usr/bin/env python3
"""Offline test for sites/mbpartsgiant.py (SimplePart "giant" variant; feed
class names expanded to the catalog's badges).
Pure checks always run; page checks read the fetch.py cache only and are
skipped when it is absent.
Run: python3 scraper/oem_fitment/tests/test_mbpartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sp_cacheonly as _cacheonly  # noqa: E402

_cacheonly.install()
from sites import mbpartsgiant as MB  # noqa: E402

B = "https://www.mbpartsgiant.com"
L = f"{B}/parts-list/2008-mercedes_benz-c300"
FDOOR = f"{L}/body-hardware/front-door"
P_REG = f"{B}/genuine/mercedes-benz~regulator-module~2127201579"
P_SW = f"{B}/genuine/mercedes-benz~switch-block~2049053905659107"
ALT55 = f"{B}/parts-list/2005-mercedes_benz-c55_amg/charging-starting/alternator"
PAGES = [ALT55, f"{B}/", f"{B}/2008-mercedes_benz-c300-parts", FDOOR, P_REG, P_SW] + \
        [f"{B}/mercedes_benz-{b}-parts" for b in ("c230", "c300", "c350", "c63_amg")]

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        raise AssertionError(msg)


ok(MB._slug("Sprinter 2500") == "sprinter_2500" and MB._slug("C300") == "c300", "badge slugs")
ok(MB._T.year_url("Mercedes-Benz", "c300", 2008) == f"{B}/2008-mercedes_benz-c300-parts", "year url")
import re  # noqa: E402
ok(all(re.search(MB.CLASSES["GL-Class"], s) for s in ("gl320", "gl450", "gl63_amg")), "GL badges")
ok(not any(re.search(MB.CLASSES["GL-Class"], s) for s in ("gla250", "glk350", "gle350", "gls450")), "GL excludes GLA/GLK/GLE/GLS")
ok(not any(re.search(MB.CLASSES["C-Class"], s) for s in ("cl500", "cla250", "clk320", "cls550")), "C excludes CL/CLA/CLK/CLS")
for cat in ("door-front", "door-rear", "fuel-pump-module", "side-mirrors", "climate-control"):
    ok(cat not in MB.CAT_PAGES, f"{cat} not crawled (page does not print what it needs)")
pure = checks

if not _cacheonly.have(PAGES):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

ok(MB.badges(MB.CLASSES["C-Class"], 2008) == ["c300", "c350", "c63_amg"], MB.badges(MB.CLASSES["C-Class"], 2008))
cats = MB.categories_for("Mercedes-Benz", "C300", 2008, ["window-switch", "door-front"])
ok(cats == {"window-switch": [FDOOR]}, cats)

reg = {p["pn"]: p for p in MB.parts_on_page(FDOOR, "window-regulator")}
ok(sorted(reg) == ["212-720-15-79", "212-720-16-79", "212-906-67-02", "212-906-68-02"], sorted(reg))
ok(reg["212-906-67-02"]["product_check"].startswith("'Window' in 'Window Motor |"), reg["212-906-67-02"]["product_check"])
sw = [p["pn"] for p in MB.parts_on_page(FDOOR, "window-switch")]
ok(sw == ["204-905-39-05-65-9107", "204-905-40-05-65-9107"], sw)  # both print Position: Driver Side

alt = [p["pn"] for p in MB.parts_on_page(ALT55, "alternator")]
ok(alt == [], alt)  # its only "Alternator" row is 271-155-01-15, whose product page says "Pulley"

p = MB.product(P_REG)  # W204 + W212 under one number
ok(p["pn"] == "212-720-15-79" and p["position"] == "Driver Side" and p["replaces"] == ["204-720-24-79", "204-720-05-79"], p)
rows = [(f["years"], f["make"], f["model"]) for f in p["fitment"]]
ok(rows[:4] == [([2012, 2014], "Mercedes-Benz", "C250"), ([2008, 2014], "Mercedes-Benz", "C300"),
                ([2008, 2014], "Mercedes-Benz", "C350"), ([2008, 2014], "Mercedes-Benz", "C63 AMG")], rows)
ok(([2010, 2016], "Mercedes-Benz", "E350") in rows and "flags" not in p, p.get("flags"))
p = MB.product(P_SW)  # "2014, 2012 C250" -> two spans
ok([f["years"] for f in p["fitment"][:2]] == [[2014, 2014], [2012, 2012]] and p["description"] == "SWITCH BLOCK", p["fitment"][:2])

print(f"OK {checks} checks ({pure} pure, {checks - pure} on cached pages)")
