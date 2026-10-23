#!/usr/bin/env python3
"""Tests for model-name normalization (owner-reported 2026-10-22: the BMW
model filter showed '328' and '328i' as separate entries, '330I' vs '330i'
case variants, and a 919-car '3 Series' blob; the full audit found 2,388
distinct (make, model) strings with the same disease across makes).

This file is also the REFERENCE for canonical model forms — if you maintain
model aliases elsewhere (e.g. feature/interchange's alias tables), rebase
against the expectations below.

Canonical-form conventions, per marque:
  BMW        328i / 328is / 328ci / 328xi / 323iC / 750Li / 740iL (input
             letter order preserved: is≠si, xi≠ix, iC≠ci); '320i xDrive',
             '535i GT'; 525iA/530iA merge INTO 525i/530i (automatic-
             transmission marker, not a model).
  Mercedes   C300/ML350 (letters first, caps); classic 300E/300SD/560SEC;
             'ML55 AMG'; classes stay 'C-Class', 'CLK-Class', 'M-Class'.
  Lexus      'ES 300', 'RX 450h', 'IS 200t', 'IS 250C' (space; h/t lower,
             C upper).
  Ford       F-150 / E-350 (hyphen, chain 'Pickup'/'Van'/'Econoline'/'Club
             Wagon' suffixes dropped); 'F-250 Super Duty' ('F-250 SD'
             merges into it; plain F-250 stays separate).
  Volvo/Infiniti  XC90 / QX56 / FX35 (letters upper).
  Chevy/GMC  'Silverado 1500', 'Express 2500', 'Sierra 1500' (chain body
             suffixes dropped); C/K 1500 (C1500/K1500 when drive known).
  Chrysler-family  trailing platform codes dropped ('Charger Lc',
             'Sebring Jr', 'Town And Country Rs' -> base); 'Town & Country'.
  Scion      tC / xA / xB / xD / iQ / iA / iM.

KEEP-SEPARATE (different cars for parts purposes — never merged):
  328i / 328is / 328ci / 328xi / 323iC; F-250 vs F-250 Super Duty;
  E-350 vs E-350 Super Duty; Malibu/Impala/Cruze/Acadia 'Limited'
  continuation models; A4 vs A4 Quattro; Armada vs Pathfinder Armada;
  Crosstour vs Accord Crosstour; B9 Tribeca vs Tribeca; XV Crosstrek vs
  Crosstrek; Silverado 1500 Classic; Sierra Classic 1500; '300 Lh'
  (ambiguous — Chrysler 300 didn't exist in the LH era).

Blob resolution (VIN decode cache, _apply_match time): '3 Series',
'5 Series', Ford 'E-Series'/'Econoline', GMC 'Sierra', Chevy 'Silverado'/
'Suburban'/'Express'/'Gmt-400'/'C/K', Dodge 'RAM'/'Ram Pickup', Saturn
'S-Series'/'L-Series', Volvo 'NN Series', Jaguar 'XJ-Series', Infiniti
'Fx Series', Hyundai 'Xg Series', Mazda 'B-Series', Lexus 'GS 300/400',
bare BMW '328', 'Unknown'. Ambiguous rows keep the blob. Mercedes
'*-Class' deliberately NOT resolved (NHTSA is class-grained for MB).

Run:  python3 scraper/test_model_normalization.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


N = js.normalize_model
R = js.resolve_model_blob

# ---- 1. case canonicalization per marque -------------------------------------
print("case canonicalization:")
for model, make, want in [
    ("330I", "BMW", "330i"),
    ("328I", "BMW", "328i"),
    ("320I Xdrive", "BMW", "320i xDrive"),
    ("328D Xdrive", "BMW", "328d xDrive"),
    ("535I Gt", "BMW", "535i GT"),
    ("550I Gt Xdrive", "BMW", "550i GT xDrive"),
    ("740Il", "BMW", "740iL"),
    ("750LI", "BMW", "750Li"),
    ("318Ti", "BMW", "318ti"),
    ("325Es", "BMW", "325es"),
    ("325Ix", "BMW", "325ix"),
    ("Activehybrid 5", "BMW", "ActiveHybrid 5"),
    ("I3", "BMW", "i3"),
    ("Lesabre", "Buick", "LeSabre"),
    ("Lacrosse", "Buick", "LaCrosse"),
    ("Encore Gx", "Buick", "Encore GX"),
    ("Deville", "Cadillac", "DeVille"),
    ("El Dorado", "Cadillac", "Eldorado"),
    ("Sts", "Cadillac", "STS"),
    ("Cts-V", "Cadillac", "CTS-V"),
    ("Ml350", "Mercedes-Benz", "ML350"),
    ("300e", "Mercedes-Benz", "300E"),
    ("300Sd", "Mercedes-Benz", "300SD"),
    ("560Sec", "Mercedes-Benz", "560SEC"),
    ("450Sl", "Mercedes-Benz", "450SL"),
    ("380Sel", "Mercedes-Benz", "380SEL"),
    ("Ml55 Amg", "Mercedes-Benz", "ML55 AMG"),
    ("E-class", "Mercedes-Benz", "E-Class"),
    ("Slk-class", "Mercedes-Benz", "SLK-Class"),
    ("Ml-Class", "Mercedes-Benz", "M-Class"),
    ("Cla-Class", "Mercedes-Benz", "CLA-Class"),
    ("Es300", "Lexus", "ES 300"),
    ("Rx450H", "Lexus", "RX 450h"),
    ("Is200T", "Lexus", "IS 200t"),
    ("Is 250C", "Lexus", "IS 250C"),
    ("Xc90", "Volvo", "XC90"),
    ("V70 Xc", "Volvo", "V70 XC"),
    ("Qx56", "Infiniti", "QX56"),
    ("Fx50", "Infiniti", "FX50"),
    ("KONA", "Hyundai", "Kona"),
    ("Santa Fe Xl", "Hyundai", "Santa Fe XL"),
    ("Grand AM", "Pontiac", "Grand Am"),
    ("Gto", "Pontiac", "GTO"),
    ("Cc", "Volkswagen", "CC"),
    ("TAOS", "Volkswagen", "Taos"),
    ("Cl", "Acura", "CL"),
    ("Rdx", "Acura", "RDX"),
    ("Ls", "Lincoln", "LS"),
    ("Mks", "Lincoln", "MKS"),
    ("Xf", "Jaguar", "XF"),
    ("Xj6", "Jaguar", "XJ6"),
    ("IQ", "Scion", "iQ"),
    ("IA", "Scion", "iA"),
    ("Scion Tc", "Toyota", "Scion tC"),
    ("SCION xB", "Toyota", "Scion xB"),
    ("Yaris Ia", "Toyota", "Yaris iA"),
    ("9-2x", "Saab", "9-2X"),
    ("NIRO", "Kia", "Niro"),
    ("Soul Ev", "Kia", "Soul EV"),
    ("Xv Crosstrek", "Subaru", "XV Crosstrek"),
    ("I-Miev", "Mitsubishi", "i-MiEV"),
    ("240Sx", "Nissan", "240SX"),
    ("350z", "Nissan", "350Z"),
    ("Nv 3500", "Nissan", "NV3500"),
    ("Lw300", "Saturn", "LW300"),
    ("SL-1", "Saturn", "SL1"),
    ("Trailblazer Ext", "Chevrolet", "Trailblazer EXT"),
    ("VEGA", "Chevrolet", "Vega"),
]:
    check(f"{make} {model!r} -> {want!r}", N(model, make) == want, N(model, make))

# ---- 2. merges: spelling variants, chain suffixes, platform codes -------------
print("merges:")
for model, make, want in [
    # HTML entities + punctuation
    ("TOWN &amp; COUNTRY", "Chrysler", "Town & Country"),
    ("Town And Country", "Chrysler", "Town & Country"),
    ("Town And Country Rs", "Chrysler", "Town & Country"),
    ("Grand Caravan.", "Dodge", "Grand Caravan"),
    ("300 M", "Chrysler", "300M"),
    # own-make prefixes (incl. doubled and two-word makes)
    ("BMW 328i", "BMW", "328i"),
    ("Bmw X5", "BMW", "X5"),
    ("Mercedes C-Class", "Mercedes-Benz", "C-Class"),
    ("Mini Mini Cooper", "MINI", "Cooper"),
    ("Land Rover Range Rover", "Land Rover", "Range Rover"),
    ("Volvo 740", "Volvo", "740"),
    ("Lexus Es300", "Lexus", "ES 300"),
    ("Infiniti G35", "Infiniti", "G35"),
    ("Gmc Yukon Xl 1500", "GMC", "Yukon XL 1500"),
    ("Toyota Scion Xa", "Scion", "xA"),
    # chain body suffixes
    ("F150 Pickup", "Ford", "F-150"),
    ("Ford F250Sd Pickup", "Ford", "F-250 Super Duty"),
    ("F-250 SD", "Ford", "F-250 Super Duty"),
    ("E250 Van", "Ford", "E-250"),
    ("E-150 Econoline", "Ford", "E-150"),
    ("E-350 Econoline Club Wagon", "Ford", "E-350"),
    ("S10 Pickup", "Chevrolet", "S-10"),
    ("Silverado 1500 Pickup", "Chevrolet", "Silverado 1500"),
    ("Silverado Classic 1500", "Chevrolet", "Silverado 1500 Classic"),
    ("Express 2500 Van", "Chevrolet", "Express 2500"),
    ("Astro Van", "Chevrolet", "Astro"),
    ("C/K 1500 Series", "Chevrolet", "C/K 1500"),
    ("Sierra 1500 Pickup", "GMC", "Sierra 1500"),
    ("Sierra C/K 1500", "GMC", "Sierra 1500"),
    ("Savana 2500 Van", "GMC", "Savana 2500"),
    ("Safari (Gmc)", "GMC", "Safari"),
    ("Pick-Up Std", "Toyota", "Pickup"),
    ("D150 Pickup", "Dodge", "D150"),
    ("Ram 1500 Van", "Dodge", "Ram Van 1500"),
    # Chrysler-family platform codes
    ("Charger Lc", "Dodge", "Charger"),
    ("Dakota Nd", "Dodge", "Dakota"),
    ("Caliber Pm", "Dodge", "Caliber"),
    ("Sebring Jr", "Chrysler", "Sebring"),
    ("300 Lx", "Chrysler", "300"),
    ("Pt Cruiser Pt", "Chrysler", "PT Cruiser"),
    ("Pacifica Cs", "Chrysler", "Pacifica"),
    ("Liberty Kj", "Jeep", "Liberty"),
    ("Grand Cherokee Wk", "Jeep", "Grand Cherokee"),
    ("Patriot Mk", "Jeep", "Patriot"),
    # trim junk / redundant qualifiers
    ("Escape Xlt", "Ford", "Escape"),
    ("Tribute Lx", "Mazda", "Tribute"),
    ("Aura Xe", "Saturn", "Aura"),
    ("Grand Am Se1", "Pontiac", "Grand Am"),
    ("Intrigue Gx", "Oldsmobile", "Intrigue"),
    ("Rendezvous Srv", "Buick", "Rendezvous"),
    ("Aztek Srv", "Pontiac", "Aztek"),
    # same-car wording variants
    ("Mazda 3", "Mazda", "Mazda3"),
    ("3", "Mazda", "Mazda3"),
    ("Miata", "Mazda", "MX-5 Miata"),
    ("Rx8", "Mazda", "RX-8"),
    ("Solara", "Toyota", "Camry Solara"),
    ("Corolla Matrix", "Toyota", "Matrix"),
    ("Golf Gti", "Volkswagen", "GTI"),
    ("Jetta Gli", "Volkswagen", "Jetta GLI"),
    ("Cooper Countryman", "MINI", "Countryman"),
    ("Cooper Clubman", "MINI", "Clubman"),
    ("Evoque", "Land Rover", "Range Rover Evoque"),
    ("Discovery Ii", "Land Rover", "Discovery Series II"),
    ("Grand Vitara XL-7", "Suzuki", "XL-7"),
    ("Sx4 Sedan", "Suzuki", "SX4 Sport"),
    ("Ciera", "Oldsmobile", "Cutlass Ciera"),
    ("Culass Ciera", "Oldsmobile", "Cutlass Ciera"),
    ("Eighty Eight (88)", "Oldsmobile", "Eighty-Eight"),
    ("Rio 5-Door", "Kia", "Rio5"),
    ("Civic Crx", "Honda", "CRX"),
    ("Promaster 1500 Van", "Ram", "ProMaster 1500"),
    ("Dodge 1500 Pickup", "Ram", "1500"),
    ("QX4 (1999)", "Infiniti", "QX4"),
    ("240 Series 240", "Volvo", "240"),
    ("525Ia", "BMW", "525i"),  # automatic marker, not a model
]:
    check(f"{make} {model!r} -> {want!r}", N(model, make) == want, N(model, make))

# ---- 3. KEEP-SEPARATE: genuinely distinct cars --------------------------------
print("keep-separate:")
for model, make in [
    ("328i", "BMW"), ("328is", "BMW"), ("328ci", "BMW"), ("328xi", "BMW"),
    ("323iC", "BMW"), ("328d", "BMW"), ("M3", "BMW"), ("X5", "BMW"),
    ("F-250", "Ford"), ("F-250 Super Duty", "Ford"),
    ("E-350", "Ford"), ("E-350 Super Duty", "Ford"),
    ("Malibu Limited", "Chevrolet"), ("Impala Limited", "Chevrolet"),
    ("Cruze Limited", "Chevrolet"), ("Malibu Classic", "Chevrolet"),
    ("Silverado 1500 Classic", "Chevrolet"), ("Caprice Classic", "Chevrolet"),
    ("Acadia Limited", "GMC"), ("Sierra Classic 1500", "GMC"),
    ("A4 Quattro", "Audi"), ("A4", "Audi"),
    ("Pathfinder Armada", "Nissan"), ("Armada", "Nissan"),
    ("Rogue Select", "Nissan"),
    ("Crosstour", "Honda"), ("Accord Crosstour", "Honda"),
    ("B9 Tribeca", "Subaru"), ("Tribeca", "Subaru"),
    ("XV Crosstrek", "Subaru"), ("Crosstrek", "Subaru"),
    ("New Beetle", "Volkswagen"), ("Beetle", "Volkswagen"),
    ("Touareg 2", "Volkswagen"),
    ("300 Lh", "Chrysler"),            # ambiguous platform code — kept
    ("Focus SVT", "Ford"),             # real performance model
    ("Montana SV6", "Pontiac"),        # real model, not a platform code
    ("Taurus Wagon", "Ford"),          # body style matters for parts
    ("K1500 Suburban", "GMC"),
    ("Hardtop 2 Door", "MINI"),
    ("C10 Suburban", "Chevrolet"),
    ("Celica GT", "Toyota"),           # engine differs from base
    ("Navigator L", "Lincoln"),
    ("S-Type R", "Jaguar"),
]:
    check(f"{make} {model!r} survives untouched", N(model, make) == model, N(model, make))
# sibling-make prefixes NEVER stripped (meaning would silently change)
check("Chrysler 'Dodge Durango' keeps its prefix",
      N("Dodge Durango", "Chrysler") == "Dodge Durango", N("Dodge Durango", "Chrysler"))
check("Buick 'Chevrolet Sonic' keeps its prefix",
      N("Chevrolet Sonic", "Buick") == "Chevrolet Sonic", N("Chevrolet Sonic", "Buick"))
check("model equal to the make is not stripped to nothing",
      N("Land Rover", "Land Rover") == "Land Rover", N("Land Rover", "Land Rover"))

# ---- 4. blob resolution via VIN decode ----------------------------------------
print("blob resolution:")
BMW328 = {"model": "328i", "series": "3-Series", "make": "BMW"}
check("3 Series + decode 328i -> 328i", R("3 Series", "BMW", BMW328) == "328i")
check("3 Series + decode 325Ci -> 325ci (house casing)",
      R("3 Series", "BMW", {"model": "325Ci", "series": "", "make": "BMW"}) == "325ci")
check("bare '328' + decode -> 328is",
      R("328", "BMW", {"model": "328is", "series": "", "make": "BMW"}) == "328is")
check("5 Series + decode 525iA -> 525i",
      R("5 Series", "BMW", {"model": "525iA", "series": "", "make": "BMW"}) == "525i")
check("no decode: blob kept", R("3 Series", "BMW", None) == "3 Series")
check("multi-model decode ('325/325e'): blob kept",
      R("3 Series", "BMW", {"model": "325/325e", "series": "", "make": "BMW"}) == "3 Series")
check("decode make mismatch: blob kept",
      R("3 Series", "BMW", {"model": "Accord", "series": "", "make": "HONDA"}) == "3 Series")
check("non-blob row never overwritten by decode",
      R("328i", "BMW", {"model": "325i", "series": "", "make": "BMW"}) == "328i")
check("Silverado + series tonnage -> Silverado 1500",
      R("Silverado", "Chevrolet",
        {"model": "Silverado", "series": "1500 (1/2 Ton)", "make": "CHEVROLET"}) == "Silverado 1500")
check("Sierra + '3/4 Ton Nominal' -> Sierra 2500",
      R("Sierra", "GMC", {"model": "Sierra", "series": "3/4 Ton Nominal", "make": "GMC"}) == "Sierra 2500")
check("Gmt-400 + 4WD -> K1500",
      R("Gmt-400", "Chevrolet",
        {"model": "GMT-400", "series": "1/2 Ton Nominal", "make": "CHEVROLET",
         "driveType": "4WD/4-Wheel Drive/4x4"}) == "K1500")
check("Gmt-400, drive unknown -> C/K 1500 (never guess C vs K)",
      R("Gmt-400", "Chevrolet",
        {"model": "GMT-400", "series": "1500 (1/2 Ton)", "make": "CHEVROLET",
         "driveType": ""}) == "C/K 1500")
check("Silverado, no tonnage in series: blob kept",
      R("Silverado", "Chevrolet", {"model": "Silverado", "series": "", "make": "CHEVROLET"}) == "Silverado")
check("RAM + 'DR (1500)' -> Ram 1500",
      R("RAM", "Dodge", {"model": "Ram", "series": "DR (1500)", "make": "DODGE"}) == "Ram 1500")
check("Econoline + decode E-250 -> E-250",
      R("Econoline", "Ford", {"model": "E-250", "series": "Econoline", "make": "FORD"}) == "E-250")
check("Saturn S-Series + decode SL2 -> SL2",
      R("S-Series", "Saturn", {"model": "SL2", "series": "", "make": "SATURN"}) == "SL2")
check("Volvo 70 Series + decode XC70 -> XC70",
      R("70 Series", "Volvo", {"model": "XC70", "series": "", "make": "VOLVO"}) == "XC70")
check("Jaguar XJ-Series + decode Vanden Plas -> Vanden Plas",
      R("XJ-Series", "Jaguar", {"model": "Vanden Plas", "series": "", "make": "JAGUAR"}) == "Vanden Plas")
check("Mazda B-Series + series B2200 -> B2200",
      R("B-Series", "Mazda", {"model": "B-Series", "series": "B2200", "make": "MAZDA"}) == "B2200")
check("Mazda B-Series + odd series kept",
      R("B-Series", "Mazda", {"model": "B-Series", "series": "2600i", "make": "MAZDA"}) == "B-Series")
check("Lexus GS 300/400 + JZS160 -> GS 300",
      R("GS 300/400", "Lexus", {"model": "GS", "series": "JZS160L", "make": "LEXUS"}) == "GS 300")
check("'Unknown' resolves for any make",
      R("Unknown", "Ford", {"model": "Focus", "series": "", "make": "FORD"}) == "Focus")
check("Mercedes C-Class NOT resolved (class-grained, by design)",
      R("C-Class", "Mercedes-Benz",
        {"model": "C-Class", "series": "C240", "make": "MERCEDES-BENZ"}) == "C-Class")

# ---- 5. idempotency ------------------------------------------------------------
print("idempotency:")
for model, make in [
    ("328I Xdrive", "BMW"), ("Ford F250Sd Pickup", "Ford"),
    ("TOWN &amp; COUNTRY", "Chrysler"), ("Lexus Es300", "Lexus"),
    ("Mini Mini Cooper", "MINI"), ("Xc90", "Volvo"), ("3", "Mazda"),
]:
    once = N(model, make)
    check(f"N(N({model!r})) stable ({once!r})", N(once, make) == once, N(once, make))
check("empty stays empty", N("", "Ford") == "")

# ---- 6. enrich_vehicles end-to-end ---------------------------------------------
print("enrich_vehicles:")
vehicles = [
    {"make": "BMW", "model": "330I", "vin": "", "year": 2006, "dateAdded": ""},
    {"make": "Bmw", "model": "BMW 328i", "vin": "", "year": 2008, "dateAdded": ""},
    {"make": "Chrysler", "model": "TOWN &amp; COUNTRY", "vin": "", "year": 2012, "dateAdded": ""},
    {"make": "Mazda", "model": "Mazda 3", "vin": "", "year": 2010, "dateAdded": ""},
    {"make": "Ford", "model": "F250Sd Pickup", "vin": "", "year": 2004, "dateAdded": ""},
]
out = js.enrich_vehicles(vehicles)
check("enrich: 330I -> 330i", out[0]["model"] == "330i", out[0]["model"])
check("enrich: make canon + prefix strip -> 328i", out[1]["model"] == "328i", out[1]["model"])
check("enrich: HTML entity -> Town & Country", out[2]["model"] == "Town & Country", out[2]["model"])
check("enrich: Mazda 3 -> Mazda3", out[3]["model"] == "Mazda3", out[3]["model"])
check("enrich: F250Sd Pickup -> F-250 Super Duty", out[4]["model"] == "F-250 Super Duty", out[4]["model"])

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all model-normalization tests passed")
