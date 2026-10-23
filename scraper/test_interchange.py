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

# =========================================================================
# Phase B explicit fixtures — mirror the hand-verified spot-checks
# =========================================================================
def _tier(fid, cat, a, b):
    return js.interchange_tier(EF[fid], cat, a, b)

check("IS 250 <-> IS 350 06-09 alternator verified",
      _tier("lexus-is2", "alternator",
            (2009, "Lexus", "IS 250"), (2007, "Lexus", "IS 350")) == "verified")
check("IS 250 2012 alternator NOT verified (Base-qualified rows)",
      _tier("lexus-is2", "alternator",
            (2012, "Lexus", "IS 250"), (2009, "Lexus", "IS 250")) != "verified")
check("RDX 2.3T 08<->11 alternator verified",
      _tier("acura-rdx", "alternator",
            (2008, "Acura", "RDX"), (2011, "Acura", "RDX")) == "verified")
check("RDX 3.5 13<->15 starter verified",
      _tier("acura-rdx35", "starter",
            (2013, "Acura", "RDX"), (2015, "Acura", "RDX")) == "verified")
check("Transit Connect 2010<->2013 alternator verified",
      _tier("ford-tc", "alternator",
            (2010, "Ford", "Transit Connect"),
            (2013, "Ford", "Transit Connect")) == "verified")
check("Transit Connect 2011 alternator NOT verified (vendor-qualified)",
      _tier("ford-tc", "alternator",
            (2011, "Ford", "Transit Connect"),
            (2010, "Ford", "Transit Connect")) != "verified")
check("Passat 2.0T 08 <-> GTI 07 starter verified",
      _tier("vw-20t", "starter",
            (2008, "Volkswagen", "Passat"),
            (2007, "Volkswagen", "GTI")) == "verified")
check("Passat 2.0T 2010 starter NOT verified (Bosch-qualified row)",
      _tier("vw-20t", "starter",
            (2010, "Volkswagen", "Passat"),
            (2008, "Volkswagen", "Passat")) != "verified")
check("Sonata 2012 GDI alternator NOT verified (2011-13 rows unpublished)",
      _tier("hk-theta2gdi", "alternator",
            (2012, "Hyundai", "Sonata"), (2012, "Kia", "Optima")) != "verified")
check("Intrepid 2.7 99<->01 alternator verified",
      _tier("mopar-lh27", "alternator",
            (1999, "Dodge", "Intrepid"), (2001, "Dodge", "Intrepid")) == "verified")
check("feed alias: Chrysler-make 'Dodge 1500 Pickup' 1998 reaches mopar-magnum",
      "mopar-magnum" in [f["id"] if isinstance(f, dict) and "id" in f else fid
                         for fid, f in EF.items()
                         if any(js._app_matches(a, 1998, "Chrysler", "Dodge 1500 Pickup")
                                for a in f["apps"])])
check("feed alias: raw 'Town &amp; Country' entity 2012 reaches mopar-pentastar",
      any(js._app_matches(a, 2012, "Chrysler", "Town &amp; Country")
          for a in EF["mopar-pentastar"]["apps"]))

# =========================================================================
# Performance-trim platform groups (2026-10) — body parts follow the
# platform even when the engine is trim-unique.
# =========================================================================
_payload2 = js.build_interchange_payload()
_trim_ids = set(js.TRIM_PLATFORM_GROUPS)
_trim_groups = [g for g in _payload2["platformGroups"]
                if g["id"].split("#")[0] in _trim_ids]
check("payload ships a group per trim family x category",
      len(_trim_groups) == sum(len(t["cats"])
                               for t in js.TRIM_PLATFORM_GROUPS.values()),
      str(len(_trim_groups)))
check("every trim platform group ships tier=likely (reasoned, not published)",
      all(g["tier"] == "likely" for g in _trim_groups))
check("every trim platform group carries a caveat note",
      all(len(g["note"]) >= 15 for g in _trim_groups))
check("legacy platform groups still ship tier=verified",
      all(g["tier"] == "verified" for g in _payload2["platformGroups"]
          if g["id"].split("#")[0] not in _trim_ids))
_ten = _payload2["trimEngineNotes"]
check("trimEngineNotes shipped for unique-engine trims", len(_ten) >= 10)
check("E46 M3 2002 hits a trim engine note (S54 honesty)",
      any(any(js._app_matches(tuple(a), 2002, "BMW", "M3") for a in t["apps"])
          for t in _ten))
check("E46 M3 2002 reaches the window-regulator platform group",
      any(g["cat"] == "window-regulator"
          and any(js._app_matches(tuple(a), 2002, "BMW", "M3")
                  for a in g["apps"])
          and any(js._app_matches(tuple(a), 2003, "BMW", "325ci")
                  for a in g["apps"])
          for g in _trim_groups))
check("Mercedes prefixed feed spelling reaches the AMG groups",
      any(g["id"].startswith("mb-w211-e55")
          and any(js._app_matches(tuple(a), 2005, "Mercedes-Benz",
                                  "Mercedes E-Class") for a in g["apps"])
          for g in _trim_groups))
check("no trim group claims an engine category",
      all(g["cat"] not in ("alternator", "starter") for g in _trim_groups))
check("gauge clusters never cross a trim boundary (unique faces)",
      all(g["cat"] != "gauge-cluster" for g in _trim_groups))

# Trim engine families with published rows get real tiers.
check("Neon SRT-4 04<->05 alternator verified",
      _tier("mopar-srt4", "alternator",
            (2004, "Dodge", "Neon Srt-4"),
            (2005, "Dodge", "Neon Srt-4")) == "verified")
check("Marauder 03<->04 starter verified (dual case styles noted)",
      _tier("mercury-marauder", "starter",
            (2003, "Mercury", "Marauder"),
            (2004, "Mercury", "Marauder")) == "verified")
check("R32 2008 starter verified",
      _tier("vw-r32-32", "starter",
            (2008, "Volkswagen", "R32"),
            (2008, "Volkswagen", "R32")) == "verified")
check("SRT-4 never matches the 2.0 Neon family (engine split)",
      not any(js._app_matches(a, 2004, "Dodge", "Neon Srt-4")
              for a in EF["mopar-neon"]["apps"]))

# =========================================================================
# P0 part catalog (PART_CATALOG_SPEC, 2026-10) — rule classes, honesty
# notes, taxonomy fixes, generation windows.
# =========================================================================
_p0 = js.build_interchange_payload()
CATS = {c["id"]: c for c in _p0["categories"]}
PC = js.INTERCHANGE_PART_CATEGORIES

check("payload ships schemaVersion 2", _p0["schemaVersion"] == 2)
check("25 P0 categories ship", len(CATS) == 25, str(len(CATS)))
_P0_NEW = ["engine-assembly", "ignition-coils", "transmission-auto", "ecm",
           "radio", "front-seats", "door-front", "fender", "hood",
           "bumper-front", "grille", "trunk-lid", "liftgate"]
check("all 13 new categories present", all(c in CATS for c in _P0_NEW))

# Rule classes (spec §3): A=engine, B=body, C=combo, D=exact.
check("engine assembly + coils are class A (engine kind)",
      CATS["engine-assembly"]["kind"] == "engine"
      and CATS["ignition-coils"]["kind"] == "engine")
check("transmission + ECM are class C (combo kind)",
      CATS["transmission-auto"]["kind"] == "combo"
      and CATS["ecm"]["kind"] == "combo")
check("radio is class D (exact kind) — electronics never cross models",
      CATS["radio"]["kind"] == "exact")
check("panels are class B (body kind)",
      all(CATS[c]["kind"] == "body" for c in
          ("door-front", "fender", "hood", "bumper-front", "grille",
           "trunk-lid", "liftgate", "front-seats")))

# Mandatory honesty notes (spec §4) — computed into the payload, not UI-only.
_ea_notes = " ".join(CATS["engine-assembly"]["notes"]).lower()
check("engine assembly ships all three §4 honesty notes",
      "long block" in _ea_notes and "mileage" in _ea_notes
      and "hours" in _ea_notes and "call ahead" in _ea_notes)
check("engine assembly + transmission ship no resale band (noValue)",
      CATS["engine-assembly"].get("noValue") is True
      and CATS["transmission-auto"].get("noValue") is True
      and not any(CATS[c].get("noValue")
                  for c in CATS if c not in
                  ("engine-assembly", "transmission-auto")))
check("transmission rowWarn demands the case-tag code check",
      "code" in CATS["transmission-auto"]["rowWarn"]
      and "code" in " ".join(CATS["transmission-auto"]["notes"]).lower())
check("radio note covers VIN-lock/anti-theft",
      "vin-lock" in " ".join(CATS["radio"]["notes"]).lower()
      or "anti-theft" in " ".join(CATS["radio"]["notes"]).lower())
check("front seats warn about seat-mounted airbags",
      "airbag" in " ".join(CATS["front-seats"]["notes"]).lower())
check("every combo/exact category carries notes (never a bare fit claim)",
      all(CATS[c].get("notes") for c in CATS
          if CATS[c]["kind"] in ("combo", "exact")))
check("headlights + tail lights carry the facelift note",
      "facelift" in " ".join(CATS["headlights"]["notes"]).lower()
      and "facelift" in " ".join(CATS["tail-lights"]["notes"]).lower())

# Class A synthesis: every family answers assembly + coils with no vg
# (Verified for assemblies comes only from a donor VIN decode, app-side).
check("every engine family ships engine-assembly + ignition-coils parts",
      all("engine-assembly" in f["parts"] and "ignition-coils" in f["parts"]
          for f in _p0["engineFamilies"]))
check("no family claims a verified group for the assembly (decode-only tier)",
      all("vg" not in f["parts"]["engine-assembly"]
          for f in _p0["engineFamilies"]))

# Honest refusal: exact/combo categories never ride platform groups —
# a chassis-mate's radio or transmission is not a claim we can make.
check("no platform group ships an exact/combo category",
      all(g["cat"] not in ("radio", "transmission-auto", "ecm")
          for g in _p0["platformGroups"]))
check("no platform group ships an engine category",
      all(CATS.get(g["cat"], {}).get("kind") != "engine"
          for g in _p0["platformGroups"]))

# Taxonomy fixes (spec §6): ordered priceTokens, specific-first.
check("starter quotes exact row first (STARTER SOLENOID hazard)",
      PC["starter"]["priceTokens"][0] == "=starter")
check("tow mirrors quote tow rows before any plain mirror",
      PC["tow-mirrors"]["priceTokens"][0].startswith("tow")
      and PC["tow-mirrors"]["priceTokens"][-1] == "mirror")
check("3rd row seat never substring-matches a brake light",
      all("row" in t or "seat" in t
          for t in PC["third-row-seat"]["priceTokens"])
      and "3rd" not in PC["third-row-seat"]["priceTokens"]
      and "third" not in PC["third-row-seat"]["priceTokens"])

# Generation windows (spec §5.1).
GENS = {(mk, md): wins for mk, md, wins in js.MODEL_GENERATIONS}


def _gen_win(mk, md, yr):
    for lo, hi in GENS.get((mk, md), ()):
        if lo <= yr <= hi:
            return (lo, hi)
    return None


check("payload ships the generation table",
      len(_p0["modelGenerations"]) == len(js.MODEL_GENERATIONS)
      and len(_p0["modelGenerations"]) >= 190)
check("Altima 2015<->2013 share a window; 2012 does not",
      _gen_win("Nissan", "Altima", 2015) == _gen_win("Nissan", "Altima", 2013)
      and _gen_win("Nissan", "Altima", 2012)
      != _gen_win("Nissan", "Altima", 2013))
check("Tahoe 2008<->2014 share the GMT900 window",
      _gen_win("Chevrolet", "Tahoe", 2008)
      == _gen_win("Chevrolet", "Tahoe", 2014) == (2007, 2014))
check("feed aliases carry identical windows (Ram Pickup = Ram 1500)",
      all(w in GENS[("Dodge", "Ram 1500")]
          for w in GENS[("Dodge", "Ram Pickup")]))
check("Ram-make 1500 row exists for post-split feed spellings",
      _gen_win("Ram", "1500", 2015) == (2009, 2018))
check("Town & Country ships all three feed spellings",
      GENS[("Chrysler", "Town & Country")]
      == GENS[("Chrysler", "Town And Country")]
      == GENS[("Chrysler", "Town &amp; Country")])
check("civic 1995<->1997 do NOT share a window (EG/EK split)",
      _gen_win("Honda", "Civic", 1995) != _gen_win("Honda", "Civic", 1997))
check("no window predates 1960 or runs past 2035",
      all(1960 < lo <= hi < 2036
          for wins in GENS.values() for lo, hi in wins))
# The 2026-10 model-normalization worker rewrites feed spellings before they
# reach the payload. Generation rows key on squashed forms, which must absorb
# every canon rewrite — a canon change that squashes a row out of the table
# would silently kill its class-B coverage.
_gen_keys = {(mk.lower(), js._squash_model(md, mk))
             for mk, md, _ in js.MODEL_GENERATIONS}
check("every generation row survives model normalization (squash-stable)",
      all((mk.lower(), js._squash_model(js.normalize_model(md, mk), mk))
          in _gen_keys for mk, md, _ in js.MODEL_GENERATIONS))

# Browse mode (2026-10-23): engine-class categories browse by FAMILY data
# (select a family, donors by application list + decode) — they must not
# carry spotted-part tokens that would silently keyword-match instead.
# Body-class categories browse by spotted-part tokens — they must have some.
check("browse: engine assembly ships no spotted tokens (family browse only)",
      PC["engine-assembly"]["tokens"] == [])
check("browse: every body category ships spotted-part tokens",
      all(PC[c]["tokens"] for c in PC if PC[c]["kind"] == "body"),
      str([c for c in PC if PC[c]["kind"] == "body" and not PC[c]["tokens"]]))

# Yaris/Echo/Scion 1NZ coverage (2026-10-23, owner-reported miss): the
# Canadian-market MY2006 XP90 Yaris and the 2016-18 XP130 facelift are both
# 1NZ-FE and belong to the family; the 2019-20 US Yaris is the Mazda2-based
# P5 1.5 and must stay OUT. Toyota-prefixed feed spellings of the Scion
# models must land in the same families as their Scion-make rows.
_1nz = js.ENGINE_FAMILIES["toyota-1nz"]["apps"]


def _fam_hit(fid, year, make, model):
    return any(js._app_matches(a, year, make, model)
               for a in js.ENGINE_FAMILIES[fid]["apps"])


check("1nz: 2006 Yaris (Canadian MY2006 XP90) is in the family",
      _fam_hit("toyota-1nz", 2006, "Toyota", "Yaris"))
check("1nz: 2016-18 XP130 facelift Yaris is in the family",
      _fam_hit("toyota-1nz", 2016, "Toyota", "Yaris")
      and _fam_hit("toyota-1nz", 2018, "Toyota", "Yaris"))
check("1nz: 2019 Mazda2-based Yaris is honestly excluded",
      not any(any(js._app_matches(a, 2019, "Toyota", "Yaris")
                  for a in f["apps"])
              for f in js.ENGINE_FAMILIES.values()))
check("1nz: 'Toyota / Scion xA' and 'Toyota / Scion xB' aliases match",
      _fam_hit("toyota-1nz", 2005, "Toyota", "Scion xA")
      and _fam_hit("toyota-1nz", 2005, "Toyota", "Scion xB"))
check("2az/2ar: 'Toyota / Scion tC' alias lands in the right gen's family",
      _fam_hit("toyota-2az", 2008, "Toyota", "Scion tC")
      and _fam_hit("toyota-2ar", 2013, "Toyota", "Scion tC"))
check("2zr: 'Toyota / Scion xD' alias matches",
      _fam_hit("toyota-2zr", 2010, "Toyota", "Scion xD"))
check("1nz: starter has NO verified groups (dual-published 0336/0401)",
      "verified" not in js.ENGINE_FAMILIES["toyota-1nz"]["parts"]["starter"])
check("1nz: alternator verified covers 16-18 but NOT the 2015 date-split",
      any(any(r[:2] == ("Toyota", "Yaris") and r[2] == 2016 and r[3] == 2018
              for r in g)
          for g in js.ENGINE_FAMILIES["toyota-1nz"]["parts"]["alternator"]
          ["verified"]["groups"])
      and not any(any(r[2] <= 2015 <= r[3] and r[:2] == ("Toyota", "Yaris")
                      for r in g)
                  for g in js.ENGINE_FAMILIES["toyota-1nz"]["parts"]
                  ["alternator"]["verified"]["groups"]))
check("gens: Yaris window opens 2006 and the Mazda-based 19-20 is its own",
      _gen_win("Toyota", "Yaris", 2006) == (2006, 2011)
      and _gen_win("Toyota", "Yaris", 2019) == (2019, 2020)
      and _gen_win("Toyota", "Yaris", 2018) == (2012, 2018))
# Next-tier coverage (2026-10-23): Sentra B17, Juke, R52 Pathfinder.
check("mra8: Sentra 2013-19 covered; 2020+ (B18, different engine) is not",
      _fam_hit("nissan-mra8", 2013, "Nissan", "Sentra")
      and _fam_hit("nissan-mra8", 2019, "Nissan", "Sentra")
      and not _fam_hit("nissan-mra8", 2020, "Nissan", "Sentra"))
check("mr16t: Juke 2011-17 covered, alternator verified spans all years",
      _fam_hit("nissan-mr16t", 2011, "Nissan", "Juke")
      and _fam_hit("nissan-mr16t", 2017, "Nissan", "Juke")
      and js.ENGINE_FAMILIES["nissan-mr16t"]["parts"]["alternator"]
      ["verified"]["groups"] == [[("Nissan", "Juke", 2011, 2017)]])
check("vq35de: R52 Pathfinder 13-16 in; VQ35DD-era 2017 honestly out",
      _fam_hit("nissan-vq35de", 2013, "Nissan", "Pathfinder")
      and _fam_hit("nissan-vq35de", 2016, "Nissan", "Pathfinder")
      and not _fam_hit("nissan-vq35de", 2017, "Nissan", "Pathfinder"))

check("gens: Echo/xA/xD rows exist; Toyota-alias Scion rows mirror Scion's",
      _gen_win("Toyota", "Echo", 2003) == (2000, 2005)
      and _gen_win("Scion", "xA", 2005) == (2004, 2006)
      and _gen_win("Scion", "xD", 2010) == (2008, 2014)
      and GENS[("Toyota", "Scion tC")] == GENS[("Scion", "tC")]
      and GENS[("Toyota", "Scion xB")] == GENS[("Scion", "xB")]
      and GENS[("Toyota", "Scion xA")] == GENS[("Scion", "xA")]
      and GENS[("Toyota", "Scion xD")] == GENS[("Scion", "xD")])

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):", *FAILS, sep="\n  - ")
    sys.exit(1)
print("all interchange tests passed")
