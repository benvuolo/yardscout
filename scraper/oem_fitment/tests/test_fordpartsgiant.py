#!/usr/bin/env python3
"""Offline test for sites/fordpartsgiant.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_fordpartsgiant.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import fordpartsgiant as F  # noqa: E402

B = "https://www.fordpartsgiant.com"
F150 = f"{B}/ford-f_150-parts.html"
Y2001 = f"{B}/2001-ford-f_150-parts.html"
OPT_FIRST = f"{B}/2001-ford-f_150--6_cyl_4_2l-4at_4r100-parts.html"
OPT_LAST = f"{B}/2001-ford-f_150--8_cyl_5_4l-5mt-parts.html"
REAR = f"{B}/parts-list/2001-ford-f_150--6_cyl_4_2l-4at_4r100/lamps_wiring/rear_lamp_backup_lamp_license_plate_lamp.html"
ALT = f"{B}/parts-list/2010-ford-escape-gas/electrical/alternator_and_mountings.html"
REG = f"{B}/parts-list/2010-ford-escape-gas/body_and_paint/front_door_glass_window_controls.html"
P_TAIL = f"{B}/parts/ford-lamp-assy-rear-stop-and-flasher_f85z-13405-ca.html"   # 6 models, Replaces, side
P_COMP = f"{B}/parts/ford-compressor-assy_f7lz-19703-aa.html"                   # 19 rows, Replaced By
P_ALT = f"{B}/parts/ford-alternator-asy_9l8z-10346-a.html"                      # Escape/Fusion/MKZ/Mariner

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def rule(cat, pn, group, main="", info=()):
    r = {"pn": pn, "group": group, "main": main or group, "remark": "", "info": list(info)}
    return F.PARTS[cat](r, f"{r['group']} | {r['main']} |  | {'; '.join(r['info'])}")


# ---- pure rule checks (base numbers inside Ford part numbers)
ok(F._base("8L8Z-7823201-A") == "7823201" and F._base("-W520414-S437") == "", "base (hardware has none)")
ok(rule("window-regulator", "8L8Z-7823201-A", "Regulator Assy", "Regulator Assy", ["Includes Motor", "Location: Driver Side"]), "regulator 78+23201")
ok(not rule("window-regulator", "BL8Z-7821452-BA", "Weatherstrip - Door Glass"), "belt moulding")
ok(rule("alternator", "9L8Z-10346-A", "Alternator Assy"), "alternator")
ok(rule("alternator", "FU2Z-10V346-DRM", "Alternator Assy"), "reman matched (template drops it when a new number is listed)")
ok(not rule("side-mirrors", "8L8Z-17K707-C", "Glass", "Glass Assy - Rear View Outer Mirror"), "mirror glass (17K707)")
ok(rule("side-mirrors", "AL8Z-17682-AA", "Mirror Assy", "Mirror Assy - Rear View Outer"), "mirror 17682")
ok(rule("window-switch", "8L8Z-14529-AC", "Switch Assy", "Switch - Window Control - Double", ["BLACK", "Location: Driver Side"]), "master")
ok(not rule("window-switch", "8L8Z-14529-AB", "Switch Assy", "Switch - Window Control - Single", ["BLACK , Single Switch", "Location: Passenger Side"]), "single")
ok(rule("throttle-body", "9L8Z-9E926-A", "Housing - Throttle Plate"), "throttle housing")
ok(rule("liftgate", "AL8Z-7840010-A", "Door Assy - Rear") and not rule("trunk-lid", "AL8Z-7840010-A", "Door Assy - Rear"), "liftgate 40010")
pure = n

if not _pg_cacheonly.have([F150, Y2001, OPT_FIRST, OPT_LAST, REAR, ALT, REG, P_TAIL, P_COMP, P_ALT]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

# ---- navigation: 2001 F-150 is split into engine/transmission catalogs
cats = F.categories_for("Ford", "F-150", 2001, ["tail-lights"])
ok(REAR in cats["tail-lights"], f"option catalog list {cats}")
ok(any("/2001-ford-f_150--8_cyl_5_4l-5mt/" in u for u in cats["tail-lights"]), "last option catalog used")

# ---- list pages
alts = [p["pn"] for p in F.parts_on_page(ALT, "alternator")]
ok(alts == ["9L8Z-10346-A", "8S4Z-10346-A", "G2MZ-10346-CN"], f"alternators (reman dropped) {alts}")
regs = F.parts_on_page(REG, "window-regulator")
ok(sorted(p["pn"] for p in regs) == ["8L8Z-7823200-A", "8L8Z-7823201-A", "AL8Z-7823200-A", "AL8Z-7823201-A"], f"regs {regs}")
tails = {p["pn"]: p for p in F.parts_on_page(REAR, "tail-lights")}
ok("F85Z-13405-CA" in tails and "F85Z-13404-CA" in tails, f"tails {sorted(tails)}")

# ---- product pages
t = F.product(P_TAIL)
ok(t["description"] == "Lamp Assy - Rear, Stop And Flasher" and t["replaces"] == ["F65Z-13405-AF"] and t["replaced_by"] is None, "tail fields")
ok(t["position"] == "Location: Driver Side", f"tail side {t['position']}")
ok([(f["years"], f["model"]) for f in t["fitment"]][:3] == [([1997, 2004], "F-150"), ([1997, 1999], "F-250"), ([1999, 2007], "F-250 Super Duty")], "tail rows")
ok(len(t["fitment"]) == 6 and all(f["trims"] == [] for f in t["fitment"]), "ford options are not trims")
ok(t["fitment"][0]["options"][:2] == ["4AT", "4AT 4R100"], "options kept")
c = F.product(P_COMP)
ok(c["replaced_by"] == "4L3Z-19703-AC" and len(c["fitment"]) == 19, "compressor")
ok(c["fitment"][2]["model"] == "E-350/E-350 Super Duty" and c["fitment"][2]["years"] == [1997, 2001], "model name kept as printed")
ok(c["evidence_lines"][2:4] == ["Replaced By: 4L3Z-19703-AC", "Year Make Model | Engine | Important vehicle option details"], "evidence")
a = F.product(P_ALT)
ok([(f["years"], f["make"], f["model"]) for f in a["fitment"]][:4] == [([2009, 2012], "Ford", "Escape"), ([2010, 2012], "Ford", "Fusion"),
                                                                     ([2010, 2012], "Lincoln", "MKZ"), ([2009, 2011], "Mercury", "Mariner")], "alt rows")
ok(a["fitment"][0]["engines"] == ["6 Cyl 3.0L OHC Duratec"], "engine")
print(f"OK {n} checks ({pure} pure)")
