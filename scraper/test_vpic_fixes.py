#!/usr/bin/env python3
"""VPIC_TRANS_FIXES: known NHTSA decode errors are corrected, nothing else moves.

Run:  python3 scraper/test_vpic_fixes.py
"""
import collections
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        failures.append(name)


lr3 = {"make": "LAND ROVER", "model": "LR3", "modelYear": "2005", "engine": "4.4L 8-cyl", "transmission": "5-spd Automatic"}
fixed = js._correct_vpic(lr3)
check("2005 LR3 becomes 6-spd", fixed["transmission"] == "6-spd Automatic" and fixed.get("transmissionFixed") is True)
check("input not mutated", lr3["transmission"] == "5-spd Automatic")
for dec, why in (
    ({**lr3, "modelYear": "2006", "transmission": "6-spd Automatic"}, "2006 LR3 already right"),
    ({**lr3, "model": "Range Rover"}, "2005 Range Rover really is a 5-speed"),
    ({**lr3, "make": "JAGUAR", "model": "XJ8", "modelYear": "1998", "transmission": "5-spd Automatic"}, "1998 XJ8 really is a 5-speed"),
    ({**lr3, "transmission": "5-spd Manual/Standard"}, "only the exact wrong text is replaced"),
    ({**lr3, "transmission": ""}, "empty transmission untouched"),
):
    check(f"unchanged: {why}", js._correct_vpic(dec) == dec, str(js._correct_vpic(dec)))
check("None passes through", js._correct_vpic(None) is None)

# Against the real cache: every 2005 LR3 decode is corrected, every decode in a
# vPIC default cell loses its transmission, and nothing else changes.
cache = json.load(gzip.open(Path(__file__).resolve().parent.parent / "docs" / "data" / "vin_decodes.json.gz"))
changed = {vin for vin, d in cache.items() if isinstance(d, dict) and js._correct_vpic(d) != d}
lr3_2005 = {vin for vin, d in cache.items() if isinstance(d, dict) and d.get("model") == "LR3" and d.get("modelYear") == "2005" and d.get("transmission")}


def _in_default_cell(d):
    try:
        yr = int(str(d.get("modelYear") or "0")[:4])
    except ValueError:
        return False
    mk, md = str(d.get("make") or "").upper(), str(d.get("model") or "").upper()
    return bool(d.get("transmission")) and any(mk == a and md == b and y0 <= yr <= y1 for a, b, y0, y1 in js.VPIC_TRANS_DEFAULT_CELLS)


defaults = {vin for vin, d in cache.items() if isinstance(d, dict) and _in_default_cell(d)}
check("real cache: exactly the 2005 LR3 decodes and the default cells change", changed == lr3_2005 | defaults and len(lr3_2005) > 0, f"{len(changed)} vs {len(lr3_2005)}+{len(defaults)}")
check("real cache: default cells only ever drop the transmission", all(js._correct_vpic(cache[v])["transmission"] == "" for v in defaults))
print(f"  default-cell decodes whose transmission is dropped: {len(defaults)}")
check("real cache: the reported car is among them", "SALAD25445A319797" in changed)

# VIN-pattern trims
rsx = {"make": "ACURA", "model": "RSX", "modelYear": "2002", "trim": "", "series": "", "trimQuality": "empty",
       "bodyClass": "Hatchback/Liftback/Notchback", "driveType": "", "transmission": "5-spd Automatic"}
ts = js._correct_vpic(rsx, "JH4DC53022C000001")
check("DC53 -> Type-S, usable", ts["trim"] == "Type-S" and ts["trimQuality"] == "usable" and ts.get("trimFromVin") is True, str(ts))
base = js._correct_vpic(rsx, "JH4DC54632C801476")
check("DC54 -> Base", base["trim"] == "Base" and base["trimQuality"] == "usable")
check("RSX 5-spd automatic left alone (it's real)", base["transmission"] == "5-spd Automatic")
check("a vPIC-supplied trim is never overwritten", js._correct_vpic({**rsx, "trim": "Type-S", "trimQuality": "usable"}, "JH4DC54632C801476")["trim"] == "Type-S")
check("no VIN -> unchanged", js._correct_vpic(rsx, "") == rsx)
check("wrong year -> unchanged", js._correct_vpic({**rsx, "modelYear": "2008"}, "JH4DC53022C000001").get("trim") == "")
def parts(year, make, model, dec):
    return {p["name"]: p for m in js.match_vehicle(year, make, model, vin_decode=dec) for p in m["top_parts"]}
seats = "Type-S Recaro-style Seats (pair)"
check("RSX Type-S VIN: seats VIN-confirmed", parts(2002, "Acura", "RSX", ts).get(seats, {}).get("trim_status") == "vin", str(parts(2002, "Acura", "RSX", ts).get(seats)))
check("RSX base VIN: Type-S seats excluded", seats not in parts(2002, "Acura", "RSX", base))
check("RSX no decode: seats 'if equipped'", parts(2002, "Acura", "RSX", None).get(seats, {}).get("trim_status") == "unconfirmed")
# Camry hybrid vs gas from the powertrain code
cam = {"make": "TOYOTA", "model": "Camry", "modelYear": "2009", "trim": "", "series": "", "trimQuality": "empty", "bodyClass": "Sedan/Saloon", "driveType": "", "transmission": "CVT"}
check("4T1BB46K 2009 -> Hybrid", js._correct_vpic(cam, "4T1BB46K59U000001")["trim"] == "Hybrid")
check("JTNBB46K 2008 -> Hybrid (Japan-built)", js._correct_vpic({**cam, "modelYear": "2008"}, "JTNBB46K883000001")["trim"] == "Hybrid")
check("4T1BE46K 2009 -> Gas", js._correct_vpic(cam, "4T1BE46K79U000001")["trim"] == "Gas")
check("4T1BF3EK 2011 -> Gas", js._correct_vpic({**cam, "modelYear": "2011"}, "4T1BF3EK5BU000001")["trim"] == "Gas")
check("4T1BD1FK 2014 -> Hybrid", js._correct_vpic({**cam, "modelYear": "2014"}, "4T1BD1FK2EU000001")["trim"] == "Hybrid")
check("4T1BK1FK 2013 -> Gas", js._correct_vpic({**cam, "modelYear": "2013"}, "4T1BK1FK6DU000001")["trim"] == "Gas")
battery = "Hybrid Battery Pack (test modules first)"
hy = js._correct_vpic(cam, "4T1BB46K59U000001"); gas = js._correct_vpic(cam, "4T1BE46K79U000001")
check("Camry hybrid VIN: battery pack VIN-confirmed", parts(2009, "Toyota", "Camry", hy).get(battery, {}).get("trim_status") == "vin", str(parts(2009, "Toyota", "Camry", hy).get(battery)))
check("Camry gas VIN: battery pack excluded", battery not in parts(2009, "Toyota", "Camry", gas))
check("Camry no decode: battery pack 'if equipped'", parts(2009, "Toyota", "Camry", None).get(battery, {}).get("trim_status") == "unconfirmed")
# real cache: every BD1FK vPIC labelled "Hybrid" must also be Hybrid by pattern (agreement check)
agree = disagree = 0
for vin, dd in cache.items():
    if isinstance(dd, dict) and dd.get("model") == "Camry" and vin[3:8] == "BD1FK":
        pat = js._correct_vpic({**dd, "trim": ""}, vin).get("trim")
        if "ybrid" in str(dd.get("trim") or ""): agree += (pat == "Hybrid"); disagree += (pat != "Hybrid")
check("real cache: pattern agrees with every vPIC 'Hybrid' label on BD1FK", agree > 50 and disagree == 0, f"{agree} agree, {disagree} disagree")

# Against the real cache: how many RSX / Camry decodes gain a trim, and none lose one.
gained = collections.Counter(); lost = 0
for vin, d in cache.items():
    if not isinstance(d, dict): continue
    o = js._correct_vpic(d, vin)
    if d.get("trim") and o.get("trim") != d.get("trim"): lost += 1
    if not d.get("trim") and o.get("trim"): gained[(d.get("model"), o["trim"])] += 1
check("real cache: no decode loses its vPIC trim", lost == 0)
check("real cache: RSX and Camry decodes gain trims, nothing else", gained[("RSX", "Base")] > 0 and gained[("RSX", "Type-S")] > 0 and gained[("Camry", "Hybrid")] > 300 and gained[("Camry", "Gas")] > 2000 and all(m in ("RSX", "Camry") for m, _ in gained), str(dict(gained)))
print("gained trims from VIN patterns:", dict(gained))


# vPIC model-level transmission defaults (BASELINE.md 2026-11-05): dropped
d = js._correct_vpic({"make": "HYUNDAI", "model": "Elantra", "modelYear": "2008", "transmission": "5-spd Manual/Standard", "trim": "GLS"}, "KMHDU46D08U000000")
check("2008 Elantra vPIC 'manual' default is dropped", d["transmission"] == "" and d.get("transmissionDistrusted") is True, str(d))
d = js._correct_vpic({"make": "HYUNDAI", "model": "Elantra", "modelYear": "2009", "transmission": "5-spd Manual/Standard"}, "")
check("2009 Elantra outside the cell keeps its decode", d["transmission"] == "5-spd Manual/Standard", str(d))
d = js._correct_vpic({"make": "HONDA", "model": "Fit", "modelYear": "2007", "transmission": "5-spd Manual/Standard"}, "")
check("2007 Fit default dropped", d["transmission"] == "", str(d))
d = js._correct_vpic({"make": "MERCEDES-BENZ", "model": "SLK-Class", "modelYear": "2000", "transmission": "5-spd Manual/Standard"}, "")
check("2000 SLK default dropped", d["transmission"] == "", str(d))
d = js._correct_vpic({"make": "HONDA", "model": "Civic", "modelYear": "2004", "transmission": "5-spd Manual/Standard"}, "")
check("other Civic years untouched", d["transmission"] == "5-spd Manual/Standard", str(d))
d = js._correct_vpic({"make": "LAND ROVER", "model": "LR3", "modelYear": "2005", "transmission": "5-spd Automatic"}, "")
check("LR3 fix still applies", d["transmission"] == "6-spd Automatic", str(d))

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
