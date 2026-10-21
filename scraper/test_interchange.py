#!/usr/bin/env python3
"""Interchange (platform-family) test suite — standalone, no network.

Covers the PLATFORM_FAMILIES engine, sharedWith provenance scoping, the
word-boundary gate fix, and output_json passthrough.  Run:

    python3 scraper/test_interchange.py
"""
import sys

import junkyard_scraper as js

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    tag = "ok  " if cond else "FAIL"
    print(f"{tag} {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def parts_for(year, make, model, vin_decode=None):
    out = {}
    for m in js.match_vehicle(year, make, model, vin_decode):
        for p in m["top_parts"]:
            out[p["name"]] = p
    return out


# --- import-time lints already passed or we wouldn't be here -------------
check("import + gate lint + family lint pass", True)
check("at least 20 platform families", len(js.PLATFORM_FAMILIES) >= 20,
      str(len(js.PLATFORM_FAMILIES)))

# --- provenance lands on the right generation row ------------------------
p = parts_for(2009, "GMC", "Yukon").get("3rd Row Seat (complete)", {})
check("2009 Yukon 3rd row cites GMT900 group",
      "Tahoe 2007\u201314" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2017, "GMC", "Yukon").get("3rd Row Seat (complete)", {})
check("2017 Yukon 3rd row cites K2XX group",
      "Tahoe 2015\u201320" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2004, "Cadillac", "Escalade").get("3rd Row Seat", {})
check("2004 Escalade cites GMT800 SWB caveat",
      "Suburban/Yukon XL differ" in p.get("sharedWith", ""),
      p.get("sharedWith", ""))

# --- copied rows: member had no row of its own ---------------------------
p = parts_for(2005, "Porsche", "Cayenne").get("Air Suspension Compressor", {})
check("Cayenne gains Touareg air compressor row",
      "Touareg 2004\u201310" in p.get("sharedWith", ""), str(p))
# Raw DB row (pre-calibration) must carry the donor's pricing verbatim.
_cay = next(pp for pp in js.UNOBTANIUM_DB["cayenne"]["top_parts"]
            if pp["name"] == "Air Suspension Compressor")
check("copied row keeps donor pricing", _cay["low"] == 120 and _cay["high"] == 280,
      f"{_cay['low']}-{_cay['high']}")
p = parts_for(2010, "GMC", "Sierra").get("Tailgate (straight)", {})
check("2010 Sierra gains Silverado tailgate row",
      "Silverado 2007\u201313" in p.get("sharedWith", ""), str(p))
p = parts_for(2000, "Toyota", "Tacoma").get("Rear E-Locker Actuator Motor", {})
check("1st-gen Tacoma gains e-locker row (option-gated → unconfirmed)",
      p.get("trim_status") == "unconfirmed"
      and "4Runner" in p.get("sharedWith", ""), str(p))

# --- sharedYears scoping: claim dropped outside the group window ---------
p = parts_for(2012, "Dodge", "Charger").get('Uconnect 8.4" Touchscreen', {})
check("2012 Charger keeps LX 11\u201314 Uconnect claim",
      "RE2/RB5" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2016, "Dodge", "Charger").get('Uconnect 8.4" Touchscreen', {})
check("2016 Charger drops the 11\u201314 claim", "sharedWith" not in p, str(p))
check("sharedYears is internal only — never shipped",
      all("sharedYears" not in pp for pp in
          parts_for(2012, "Dodge", "Charger").values()))

# --- trim-gated family rows attach but are never copied ------------------
p = parts_for(2008, "Subaru", "Forester XT").get("XT Turbo Intercooler + Piping", {})
check("Forester XT TMIC listing-confirmed w/ WRX provenance",
      p.get("trim_status") == "listing" and "WRX" in p.get("sharedWith", ""),
      str({k: p.get(k) for k in ("trim_status", "sharedWith")}))

# --- word-boundary gate fix regression (commit 1) ------------------------
p = parts_for(2015, "Ford", "Fiesta ST").get("ST Steering Wheel", {})
check("'Fiesta ST' listing confirms trim ST", p.get("trim_status") == "listing",
      p.get("trim_status", "?"))
p = parts_for(2015, "Ford", "Fiesta").get("ST Steering Wheel", {})
check("plain 'Fiesta' stays unconfirmed", p.get("trim_status") == "unconfirmed",
      p.get("trim_status", "?"))

# --- output_json passthrough ---------------------------------------------
fake = {"id": "t1", "vin": "", "year": 2009, "make": "GMC", "model": "Yukon",
        "_matches": js.match_vehicle(2009, "GMC", "Yukon", None)}
fake["_top_parts"] = fake["_matches"][0]["top_parts"]
fake["_max_value"] = 1
row = js.output_json([fake])[0]
shared = [tp for tp in row["topParts"] if tp.get("sharedWith")]
check("output_json ships sharedWith", bool(shared))
check("output_json never ships sharedYears",
      all("sharedYears" not in tp for tp in row["topParts"]))

# --- family engine data hygiene ------------------------------------------
seen, gated_copies = set(), []
for key, info in js.UNOBTANIUM_DB.items():
    if id(info) in seen:
        continue
    seen.add(id(info))
    for pp in info["top_parts"]:
        if pp.get("sharedWith") and "\n" in pp["sharedWith"]:
            gated_copies.append(f"{key}: newline in sharedWith")
check("sharedWith strings are single-line", not gated_copies, str(gated_copies[:3]))

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print("all interchange tests passed")
