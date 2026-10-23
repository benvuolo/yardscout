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

# --- phase-3 families: Toyota deep ----------------------------------------
p = parts_for(2002, "Toyota", "Camry").get("Alternator (spin-test at yard)", {})
check("2002 Camry alternator cites 1MZ family w/ V6 caveat",
      "ES300" in p.get("sharedWith", "") and "V6" in p.get("sharedWith", ""),
      p.get("sharedWith", ""))
p = parts_for(2005, "Toyota", "Camry").get("Alternator (spin-test at yard)", {})
check("2005 Camry (3MZ era) drops the claim", "sharedWith" not in p, str(p))
p = parts_for(2001, "Lexus", "RX 300").get("Alternator (spin-test at yard)", {})
check("RX300 gains copied 1MZ alternator row",
      "Camry V6" in p.get("sharedWith", ""), str(p))
p = parts_for(1990, "Toyota", "4Runner").get("22RE EFI Intake/Throttle Body", {})
check("4Runner gains copied 22RE intake row",
      "Toyota Pickup" in p.get("sharedWith", ""), str(p))
p = parts_for(1990, "Toyota", "4Runner").get(
    "Climate Control Panel (works, knobs intact)", {})
check("4Runner climate panel carries two-era caveat",
      "don't mix" in p.get("sharedWith", ""), p.get("sharedWith", ""))

# --- phase-3: donor notes ship verbatim (no member labels) ----------------
p = parts_for(2006, "Toyota", "Prius").get("Hybrid Battery Pack (complete)", {})
check("gen2 Prius pack carries NiMH module donor note",
      p.get("sharedWith", "").startswith("NiMH modules interchange"),
      p.get("sharedWith", ""))
p = parts_for(2018, "Toyota", "Prius").get("Hybrid Battery Cells (bulk)", {})
check("2018 Prius (Li-ion era) drops the module claim",
      "sharedWith" not in p, str(p.get("sharedWith")))
p = parts_for(1998, "Acura", "Integra").get(
    "Rear Disc Brake Conversion Parts (trailing arms)", {})
check("Integra rear-disc donor note warns about Type R 5-lug",
      "5-lug Type R" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2007, "Acura", "TL").get("Brembo Front Calipers (Type-S)", {})
check("TL-S Brembo donor note demands knuckles",
      "knuckles" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2000, "Pontiac", "Grand Prix").get(
    "GTP Supercharger Accessories (pulleys/brackets)", {})
check("L67 donor note scoped to Gen-3 era",
      "Regal GS" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2005, "Pontiac", "Grand Prix").get(
    "GTP Supercharger Accessories (pulleys/brackets)", {})
check("2005 GTP (Gen-5) drops the L67 claim", "sharedWith" not in p, str(p))

# --- phase-3: Subaru + classics -------------------------------------------
p = parts_for(2005, "Subaru", "Impreza").get("WRX Top-Mount Intercooler", {})
check("Impreza TMIC joins EJ-turbo family",
      "Forester XT" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(2003, "Subaru", "Baja").get("Headlights (clear, non-hazed)", {})
check("Baja gains Legacy GT headlight row w/ base-lamp caveat",
      "base Legacy lamp differs" in p.get("sharedWith", ""),
      p.get("sharedWith", ""))
p = parts_for(2006, "Subaru", "Outback").get("Headlights (clear, non-hazed)", {})
check("2006 Outback cites the 05–07 halogen group (not 00–04)",
      "2005\u201307" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(1999, "Jeep", "Wrangler").get("Half Doors (pair)", {})
check("TJ half doors cite YJ w/ striker caveat",
      "YJ pin vs TJ hoop" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(1985, "Chevrolet", "Blazer").get("K5 Removable Hardtop Parts", {})
check("K5 hardtop excludes 73–75 full tops",
      "73\u201375 full tops differ" in p.get("sharedWith", ""),
      p.get("sharedWith", ""))
p = parts_for(1995, "Chevrolet", "K1500").get("Tailgate (straight)", {})
check("OBS K1500 tailgate cites C/K 88–98",
      "C/K 1988\u201398" in p.get("sharedWith", ""), p.get("sharedWith", ""))
p = parts_for(1980, "Chevrolet", "Monte Carlo").get(
    "Dash Pad (uncracked, G-body)", {})
check("G-body dash pad cites Cutlass + Regal",
      "Cutlass" in p.get("sharedWith", "")
      and "Regal" in p.get("sharedWith", ""), p.get("sharedWith", ""))

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

# =========================================================================
# Part-first interchange v2: verified-groups quality bar
# =========================================================================
import itertools
import json
import os
import random

EF = js.ENGINE_FAMILIES

# --- every family carries at least one verified group (any category) ------
# Phase A (2026-10): some platforms publish clean starter spans while every
# alternator row is turbo-/vendor-/OEM-number-qualified (Z32, BMW M54, VW
# 2.0T, LT1 F-body) — those families are starter-verified and the alternator
# honestly stays at Likely. The gate is: verified evidence SOMEWHERE.
_no_group = [fid for fid, f in EF.items()
             if not any(p.get("verified") for p in f["parts"].values())]
check("every family has >=1 verified group (any category)", not _no_group,
      str(_no_group[:5]))

# --- evidence strings are real citations (length + retrieval date) --------
_bad_ev = []
for fid, f in EF.items():
    for cat, p in f["parts"].items():
        v = p.get("verified")
        if not v:
            continue
        ev = v.get("evidence", "")
        if len(ev) < 20 or "retrieved" not in ev:
            _bad_ev.append(f"{fid}/{cat}")
        if not v.get("groups"):
            _bad_ev.append(f"{fid}/{cat}: empty groups")
check("every verified block cites evidence w/ retrieval date", not _bad_ev,
      str(_bad_ev[:5]))

# --- group spans are well-formed and anchored to the family ----------------
_bad_span = []
for fid, f in EF.items():
    for cat, p in f["parts"].items():
        for g in p.get("verified", {}).get("groups", []):
            if len(g) < 1:
                _bad_span.append(f"{fid}/{cat}: empty group")
            for s in g:
                if len(s) != 4 or not (1900 < s[2] <= s[3] < 2035):
                    _bad_span.append(f"{fid}/{cat}: {s}")
        v = p.get("verified")
        if v and not any(
                a[0] == s[0] and s[2] <= a[3] and a[2] <= s[3]
                for g in v["groups"] for s in g for a in f["apps"]):
            _bad_span.append(f"{fid}/{cat}: no group span overlaps family apps")
check("verified group spans well-formed + overlap family apps", not _bad_span,
      str(_bad_span[:5]))

# --- research notes: every family id documented ----------------------------
_notes_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "interchange_research.md")
check("interchange_research.md exists", os.path.exists(_notes_path))
_notes = open(_notes_path).read() if os.path.exists(_notes_path) else ""
_undoc = [fid for fid in EF if f"### {fid} " not in _notes]
check("every family has a research-notes section", not _undoc, str(_undoc[:5]))

# --- symmetric consistency: tier(A,B) == tier(B,A) --------------------------
random.seed(20261022)
_asym = []
for fid, f in EF.items():
    cars = []
    for a in f["apps"]:
        make = a[0].split("|")[0]
        model = a[1].rstrip("*") + (" 1500" if a[1].endswith("*") else "")
        for yr in {a[2], a[3], (a[2] + a[3]) // 2}:
            cars.append((yr, make, model))
    for s, d in itertools.islice(itertools.combinations(cars, 2), 40):
        for cat in f["parts"]:
            t1 = js.interchange_tier(f, cat, s, d)
            t2 = js.interchange_tier(f, cat, d, s)
            if t1 != t2:
                _asym.append(f"{fid}/{cat}: {s}->{d} {t1} vs {t2}")
check("interchange_tier is symmetric", not _asym, str(_asym[:3]))

# --- verified tier actually reachable where groups are unambiguous ---------
def _famb(f, yr, mk, md):
    """True when (yr, mk, md) hits an ambig-flagged family app."""
    for a in f["apps"]:
        if js._app_matches(a, yr, mk, md) and len(a) > 4 and a[4].get("ambig"):
            return True
    return False

_unreach = []
for fid, f in EF.items():
    for cat, p in f["parts"].items():
        v = p.get("verified")
        if not v:
            continue
        hit = None
        for g in v["groups"]:
            cars = []
            for s in g:
                mk = s[0].split("|")[0]
                md = s[1].rstrip("*") + (" 1500" if s[1].endswith("*") else "")
                cars.append((s[2], mk, md))
                cars.append((s[3], mk, md))
            for a, b in itertools.combinations(cars, 2):
                if _famb(f, *a) or _famb(f, *b):
                    continue
                if js.interchange_tier(f, cat, a, b) == "verified":
                    hit = (a, b)
                    break
            if hit:
                break
        all_ambig = all(
            _famb(f, s[2], s[0].split("|")[0], s[1].rstrip("*"))
            for g in v["groups"] for s in g)
        if hit is None and not all_ambig:
            _unreach.append(f"{fid}/{cat}")
check("verified tier reachable in every non-ambig family", not _unreach,
      str(_unreach[:5]))

# --- payload: vg groups shipped for every family ----------------------------
_payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "docs", "data", "interchange.json")
_payload = json.load(open(_payload_path))
_pf = _payload["engineFamilies"]
check("payload family count matches module", len(_pf) == len(EF),
      f"{len(_pf)} vs {len(EF)}")
_no_vg = [pf["id"] for pf in _pf
          if not any(p.get("vg") for p in pf["parts"].values())]
check("payload ships vg for every family (some category)", not _no_vg,
      str(_no_vg[:5]))
_bad_vg = []
for pf in _pf:
    for cat, pp in pf["parts"].items():
        for g in pp.get("vg", []):
            for s in g:
                if len(s) != 4 or not isinstance(s[0], str) \
                        or not isinstance(s[2], int):
                    _bad_vg.append(f"{pf['id']}/{cat}")
check("payload vg spans are [make, model, lo, hi]", not _bad_vg,
      str(_bad_vg[:5]))
_tiers = [pf for pf in _pf
          for pp in pf["parts"].values() if "tier" in pp]
check("payload never ships a declared tier key", not _tiers)

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print("all interchange tests passed")
