#!/usr/bin/env python3
"""Offline test for sites/hyundaipartsdeal.py (PartsGiant ".html" template).
Pure rule checks always run; page checks read the fetch.py cache only and are
skipped when it is absent. Run: python3 scraper/oem_fitment/tests/test_hyundaipartsdeal.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pg_cacheonly  # noqa: E402

_pg_cacheonly.install()
from sites import hyundaipartsdeal as H  # noqa: E402

B = "https://www.hyundaipartsdeal.com"
MODEL = f"{B}/hyundai-sonata-parts.html"
Y2011 = f"{B}/2011-hyundai-sonata-parts.html"
L = f"{B}/parts-list/2011-hyundai-sonata"
ALT = f"{L}/engine/alternator.html"
AC = f"{L}/electrical/air_conditioning_system_cooler_line.html"
FREG = f"{L}/trim/front_door_window_regulator_glass.html"
DTRIM = f"{L}/trim/front_door_trim.html"
P_ALT = f"{B}/genuine/hyundai-alternator-assy~37300-2g600.html"         # Santa Fe + Sonata
P_NEW = f"{B}/genuine/hyundai-motor-assy-fr-p-wdw~82450-3q011.html"     # Replaces, side
P_OLD = f"{B}/genuine/hyundai-motor-assy-fr-p-wdw~82450-3q010.html"     # Replaced By
P_RM = f"{B}/genuine/hyundai-compressor-assy~97701-3v110-rm.html"       # reman

n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


def match(cat, name, info=""):
    inc, exc_head, exc_full = (tuple(H.PARTS[cat]) + (None, None))[:3]
    text = f"{name} | {name} |  | {info}"
    return bool(re.search(inc, text, re.I) and not (exc_head and re.search(exc_head, f"{name} | {name} | ", re.I))
                and not (exc_full and re.search(exc_full, text, re.I))
                and not H.T.COMMON_EXCLUDE.search(f"{name} | {name}"))


ok(match("alternator", "Alternator Assy") and match("alternator", "Generator Assy"), "alternator")
ok(not match("alternator", "Regulator Assy-Generator") and not match("alternator", "Rotor Assy-Generator"), "alt pieces")
ok(match("ac-compressor", "Compressor Assy") and not match("ac-compressor", "Disc & Hub Assy-A/C Compressor"), "compressor")
ok(not match("ac-compressor", "Bolt-Compressor MTG"), "compressor bolt")
ok(match("headlights", "Lamp Assy-Head, LH") and not match("headlights", "Bulb"), "headlamp")
ok(match("tail-lights", "Lamp Assy-Rear Comb Outside, LH") and match("tail-lights", "Lamp Assy-Rear Combination, RH"), "tail")
ok(not match("tail-lights", "Holder & Wiring-Rear Combination, Inside"), "tail holder")
ok(match("side-mirrors", "Mirror Assy-Outside Rear View, LH") and not match("side-mirrors", "Mirror Assy-Rear View Inside"), "mirror")
ok(not match("side-mirrors", "Actuator Assy-O/S Mirror, LH") and not match("side-mirrors", "Lamp Assy-Outside Mirror, LH"), "mirror parts")
ok(match("window-regulator", "Motor Assy-Front Power Wdw, LH") and match("window-regulator", "Panel Assy-Front DR Module, LH"), "module")
ok(match("window-regulator", "Regulator Assy-Front Door Power Window LH") and match("window-regulator", "Module Panel & Reg Assy-Front Door, LH"), "old names")
ok(not match("window-regulator", "Regulator Assy-Generator") and not match("window-regulator", "Glass-Front Door Window, LH"), "not regulators")
ok(match("window-switch", "Switch Assy-Power Window Main") and not match("window-switch", "Switch Assy-P/Wdw Assist"), "master")
ok(match("climate-control", "Control Assy-Heater") and not match("climate-control", "Panel-Heater Control"), "hvac head")
ok(match("fuel-pump-module", "Fuel Pump & Sender Module Assy") and match("fuel-pump-module", "Complete-Fuel Pump"), "pump")
ok(not match("fuel-pump-module", "Sender Assy-Fuel Pump") and not match("fuel-pump-module", "Pump-High Pressure"), "sender, GDI pump")
ok(match("throttle-body", "Body Assy-Throttle") and not match("throttle-body", "Gasket-Throttle Body"), "throttle")
ok(match("power-steering-pump", "Pump Assembly-Power Steering") and match("power-steering-pump", "Pump Assy-Power Steering Oil"), "ps pump")
ok(not match("power-steering-pump", "Pulley-Power Steering Pump"), "ps pulley")
ok(match("bumper-rear", "Cover-RR Bumper") and not match("bumper-rear", "Cover-RR Bumper Under"), "rear cover, not under")
ok(re.search(H.REMAN_PN, "97701-3V110-RM") and re.search(H.REMAN_PN, "373002G500RU"), "reman pn")
ok(not re.search(H.REMAN_PN, "93570-3Q000-RAS") and not re.search(H.REMAN_PN, "93570-3Q000-RY"), "color codes are not reman")
pure = n

if not _pg_cacheonly.have([MODEL, Y2011, ALT, AC, FREG, DTRIM, P_ALT, P_NEW, P_OLD, P_RM]):
    print(f"OK {pure} pure checks; cached-page checks skipped")
    sys.exit(0)

ok([v for v, _ in H.T.year_catalogs(H.CFG, "Hyundai", "Sonata", 2011)] == [""], "plain 2011 catalog")
cats = H.categories_for("Hyundai", "Sonata", 2011, ["alternator", "window-switch", "power-steering-pump"])
ok(cats["alternator"] == [ALT] and DTRIM in cats["window-switch"], f"nav {cats}")
ok("power-steering-pump" not in cats, "electric steering: no pump page")
alt = [p["pn"] for p in H.parts_on_page(ALT, "alternator")]
ok(alt == ["37300-2G600", "37300-2G150", "37300-2G800", "37300-2G855", "37300-2G900", "37300-2G950"], f"alternators {alt}")
ac = [p["pn"] for p in H.parts_on_page(AC, "ac-compressor")]
ok(ac == ["97701-3R000", "97701-3V110"], f"reman -RM dropped when new numbers exist: {ac}")
sw = [p["pn"] for p in H.parts_on_page(DTRIM, "window-switch")]
ok(len(sw) == 6 and all(p.startswith("93570-") for p in sw), f"master switches {sw}")
reg = {p["pn"]: p for p in H.parts_on_page(FREG, "window-regulator")}
ok(sorted(reg) == ["82450-3Q010", "82450-3Q011", "82460-3Q000", "82460-3Q001", "82471-3Q000", "82471-3Q001",
                   "82471-3Q002", "82481-3Q000", "82481-3Q001", "82481-3Q002"], sorted(reg))
ok("Location: Driver Side" in reg["82450-3Q011"]["list_info"], reg["82450-3Q011"]["list_info"])

a = H.product(P_ALT)  # multi-model block
ok(a["pn"] == "37300-2G600" and a["description"] == "Alternator Assembly" and a["position"] is None, a)
ok([(f["years"], f["make"], f["model"], f["trims"], f["engines"], f["options"]) for f in a["fitment"]] ==
   [([2009, 2012], "Hyundai", "Santa Fe", [], ["DOHC - MPI"], ["Wagon - 5Door 5P"]),
    ([2009, 2014], "Hyundai", "Sonata", [], ["DOHC - TCI/GDI"], ["Sedan - 4Door 5P"])], a["fitment"])
ok(a["evidence_lines"] == ["Part Number: 37300-2G600", "Part Description: Alternator Assembly",
                           "Year Make Model | Trim & Engine | Important vehicle option details",
                           "2009-2012 Hyundai Santa Fe | DOHC - MPI | Wagon - 5Door 5P",
                           "2009-2014 Hyundai Sonata | DOHC - TCI/GDI | Sedan - 4Door 5P"], a["evidence_lines"])
ok(a["flags"] == [], a["flags"])
m = H.product(P_NEW)
ok(m["replaces"] == ["82450-3Q010"] and m["replaced_by"] is None and m["position"] == "Location: Driver Side", m)
ok(m["fitment"][0]["engines"] == ["DOHC - GDI", "DOHC - TCI/GDI"] and m["fitment"][0]["years"] == [2009, 2014], m["fitment"])
o = H.product(P_OLD)
ok(o["replaced_by"] == "82450-3Q011" and o["replaces"] == [], o)
r = H.product(P_RM)
ok(r["description"] == "Reman Compressor" and r["pn"] == "97701-3V110-RM", r)
print(f"OK {n} checks ({pure} pure)")
