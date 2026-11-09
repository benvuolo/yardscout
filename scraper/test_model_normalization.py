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
    ("Mr2", "Toyota", "MR2"),
    ("MR-2", "Toyota", "MR2"),
    ("Mr2 Spyder", "Toyota", "MR2 Spyder"),
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

# ---- 2026-10-29 audit: Hollander 9-char abbreviations + trailing make ----
print("hollander abbreviations:")
for raw, make, want in [
    ("Silvrdo15", "Chevrolet", "Silverado 1500"), ("SilvRDO15", "Chevrolet", "Silverado 1500"),
    ("Trailblaz", "Chevrolet", "Trailblazer"), ("Tchev1500", "Chevrolet", "C/K 1500"),
    ("Grandcher", "Jeep", "Grand Cherokee"), ("Chergrand", "Jeep", "Grand Cherokee"),
    ("Expediton", "Ford", "Expedition"), ("F150New", "Ford", "F-150"), ("Transcnct", "Ford", "Transit Connect"),
    ("Optimakia", "Kia", "Optima"), ("Pathfindr", "Nissan", "Pathfinder"), ("Highlandr", "Toyota", "Highlander"),
    ("Sierra150", "GMC", "Sierra 1500"), ("Yukonxl15", "GMC", "Yukon XL 1500"), ("Mountneer", "Mercury", "Mountaineer"),
    ("Rendezvou", "Buick", "Rendezvous"), ("Town Coun", "Chrysler", "Town & Country"),
    ("Lancermit", "Mitsubishi", "Lancer"), ("Outbakleg", "Subaru", "Outback"), ("Minicoope", "MINI", "Cooper"),
    ("Ttoytcoma", "Toyota", "Tacoma"), ("Xb Scion", "Scion", "xB"), ("Tc Scion", "Scion", "tC"),
    ("A4 Audi", "Audi", "A4"), ("428I Bmw", "BMW", "428i"), ("Cc Volks", "Volkswagen", "CC"),
    ("4Runner Sr5", "Toyota", "4Runner"), ("Tundra 4WD Truck", "Toyota", "Tundra"),
]:
    check(f"{make} {raw!r} -> {want!r}", N(raw, make) == want, N(raw, make))
check("trailing make strip never empties the model", N("Audi", "Audi") == "Audi")
check("unknown abbreviation left alone (never guessed)", N("Buick-Sw", "Buick") == "Buick-Sw")

# ---- 2026-11-04 data-quality audit: split spellings in the live inventory --
# Basis: collision audit of docs/data/inventory_live.json (2,198 distinct
# make|model pairs, 53 groups whose squashed key collided) plus the 64-day
# scan history rebuilt from git. Each pair below is a case / space / hyphen
# spelling of ONE model; no distinct trims or body styles are merged.
print("2026-11 collision audit:")
for raw, make, want in [
    ("Ram1500", "Dodge", "Ram 1500"), ("Ram2500", "Dodge", "Ram 2500"),
    ("Ram3500", "Dodge", "Ram 3500"), ("RAM Van", "Dodge", "Ram Van"),
    ("RAM Chassis Cab", "Dodge", "Ram Chassis Cab"), ("RAM", "Dodge", "Ram"),
    ("D-150", "Dodge", "D150"), ("D-250", "Dodge", "D250"), ("D-50", "Dodge", "D50"),
    ("COLT", "Dodge", "Colt"), ("Caravan/grand Caravan", "Dodge", "Caravan/Grand Caravan"),
    ("Trail Blazer", "Chevrolet", "Trailblazer"), ("TrailBlazer", "Chevrolet", "Trailblazer"),
    ("Blazers10", "Chevrolet", "Blazer S10"), ("C/k 10", "Chevrolet", "C/K 10"),
    ("1500 ext cab", "Chevrolet", "1500 Ext Cab"),
    ("X-terra", "Nissan", "Xterra"), ("325-I", "BMW", "325i"),
    ("Ats", "Cadillac", "ATS"), ("Allante'", "Cadillac", "Allante"),
    ("300c", "Chrysler", "300C"), ("Rsx", "Acura", "RSX"),
    ("Gs", "Lexus", "GS"), ("Es", "Lexus", "ES"), ("Rx", "Lexus", "RX"), ("Ls", "Lexus", "LS"),
    ("Sx4", "Suzuki", "SX4"), ("Fx", "Infiniti", "FX"), ("Xj8", "Jaguar", "XJ8"),
    ("Ls1", "Saturn", "LS1"), ("Spectra 5", "Kia", "Spectra5"), ("allroad", "Audi", "Allroad"),
    ("Jetta Sportwagen", "Volkswagen", "Jetta SportWagen"), ("Fr-S", "Scion", "FR-S"),
    ("Lancer SportBack", "Mitsubishi", "Lancer Sportback"),
    ("Legacy/ Outback", "Subaru", "Legacy Outback"), ("I-290", "Isuzu", "i-290"),
    ("Mgb", "MG", "MGB"), ("WAVE", "Pontiac", "Wave"), ("Le Mans", "Pontiac", "LeMans"),
    ("TR-7", "Triumph", "TR7"), ("Ml", "Mercedes-Benz", "ML"),
    ("Gti", "Volkswagen", "GTI"), ("Sc2", "Saturn", "SC2"), ("SKY", "Saturn", "Sky"),
    ("Nx", "Nissan", "NX"), ("635Csi", "BMW", "635CSi"), ("TR-6", "Triumph", "TR6"),
    ("coronet", "Dodge", "Coronet"), ("W-100", "Dodge", "W100"), ("W-250", "Dodge", "W250"),
    ("C/k 20", "Chevrolet", "C/K 20"), ("Cj Series", "Jeep", "CJ Series"), ("Xk", "Jaguar", "XK"),
    ("Towne & country", "Chrysler", "Town & Country"), ("New Yorker (Fwd)", "Chrysler", "New Yorker"),
    ("Jetta Tdi", "Volkswagen", "Jetta TDI"),
]:
    check(f"{make} {raw!r} -> {want!r}", N(raw, make) == want, N(raw, make))
check("body-style suffixes from one hand-typed yard are NOT merged into the base model (kept separate, 1-row each)",
      N("F-150 ext cab", "Ford") != "F-150")
# Historical DB spellings (frozen at first insert, pre-2026-10 tables) that the
# lifespan writer now runs through the same canon: must land on today's form.
for raw, make, want in [
    ("Es300", "Lexus", "ES 300"), ("Rx 330", "Lexus", "RX 330"), ("Is250", "Lexus", "IS 250"),
    ("TC", "Scion", "tC"), ("XB", "Scion", "xB"), ("Mazda 3", "Mazda", "Mazda3"),
    ("3-Series", "BMW", "3 Series"), ("328I", "BMW", "328i"), ("Yukon Xl", "GMC", "Yukon XL"),
    ("Silverado 2500 Hd", "Chevrolet", "Silverado 2500HD"), ("Pt Cruiser", "Chrysler", "PT Cruiser"),
    ("Lesabre", "Buick", "LeSabre"), ("S10", "Chevrolet", "S-10"), ("Rav4", "Toyota", "RAV4"),
]:
    check(f"history {make} {raw!r} -> {want!r}", N(raw, make) == want, N(raw, make))
# Different marques / different models stay apart (never merged).
check("Dodge 'Ram 1500' is not moved to make Ram (NHTSA decodes 2011+ trucks as both)",
      js.normalize_make("Dodge", model="Ram 1500", year=2014) == "Dodge")
check("'Ram' blob without a decode stays 'Ram' (never guessed to 1500)",
      R("Ram", "Dodge", None) == "Ram")
check("Ram 1500 vs Ram 2500 stay separate", N("Ram1500", "Dodge") != N("Ram2500", "Dodge"))

# ---- saved watches keep matching (CLAUDE.md rule 6: watches are never rewritten)
# A watch stored under an old spelling matches through two paths, neither of
# which touches the stored watch: (a) the scan's own alert matcher
# (check_watchlist_alerts) normalizes BOTH the watch terms and the car, then
# compares by substring; (b) the app (docs/app.js canonicalModel) and the
# Worker (backend/src/alerts.js canonModelLow) compare raw-substring OR
# canonical-equal, with a squashed-key mirror table. Every merge above whose
# old spelling is not a raw substring of the new one therefore needs a mirror
# entry in both JS files; this test reads those tables and proves it.
print("saved watches under old spellings:")
import json as _json
import re as _re

def _js_table(path, name):
    src = Path(path).read_text()
    start = src.index(f"const {name} = {{")
    end = src.index("\n};", start)
    body = src[start + len(f"const {name} = "):end + 2]
    body = _re.sub(r"//[^\n]*", "", body)              # comments
    body = _re.sub(r",(\s*[}\]])", r"\1", body)          # trailing commas
    return _json.loads(body)

APP = _js_table(Path(__file__).resolve().parent.parent / "docs" / "app.js", "MODEL_RENAMES_2026_10")
SRV = _js_table(Path(__file__).resolve().parent.parent / "backend" / "src" / "alerts.js", "MODEL_RENAMES")
_sq = lambda s: _re.sub(r"[^a-z0-9]", "", s.lower())

def _scan_alert_matches(watch_make, watch_model, car_make, car_model):
    # mirrors check_watchlist_alerts: normalize both sides, substring compare
    mk = js.normalize_make(watch_make).lower()
    md = js.normalize_model(watch_model, watch_make).lower()
    return (not mk or mk in car_make.lower()) and (not md or md in car_model.lower())

def _js_canon(table, make, model):
    t = table.get(_sq(make)) or {}
    return (t.get(_sq(model)) or model).lower()

def _js_matches(table, watch_model, car_make, car_model):
    raw = watch_model.lower() in car_model.lower()
    return raw or _js_canon(table, car_make, car_model) == _js_canon(table, car_make, watch_model)

OLD_WATCHES = [
    ("Dodge", "Ram1500"), ("Dodge", "Ram 1500"), ("Dodge", "RAM Van"), ("Dodge", "D-150"),
    ("Chevrolet", "Trail Blazer"), ("Chevrolet", "TrailBlazer"), ("Chevrolet", "Blazers10"),
    ("Chevrolet", "C/k 10"), ("Nissan", "X-terra"), ("BMW", "325-I"), ("Cadillac", "Ats"),
    ("Cadillac", "Allante'"), ("Chrysler", "300c"), ("Lexus", "Gs"), ("Kia", "Spectra 5"),
    ("Subaru", "Legacy/ Outback"), ("Isuzu", "I-290"), ("Scion", "Fr-S"), ("Pontiac", "Le Mans"),
    ("Triumph", "TR-7"), ("Volkswagen", "Jetta Sportwagen"), ("Lexus", "Es300"), ("Lexus", "Rx 330"),
    ("Scion", "TC"), ("Mazda", "Mazda 3"), ("Toyota", "Rav4"),
]
for wmake, wmodel in OLD_WATCHES:
    cmake = js.normalize_make(wmake, model=wmodel)
    cmodel = js.normalize_model(wmodel, cmake)      # what the car is called now
    check(f"scan alert: watch {wmake!r}/{wmodel!r} matches car {cmake!r}/{cmodel!r}",
          _scan_alert_matches(wmake, wmodel, cmake, cmodel))
    check(f"app canonicalModel: watch {wmodel!r} matches car {cmodel!r}",
          _js_matches(APP, wmodel, cmake, cmodel), f"app mirror lacks {_sq(wmodel)} -> {cmodel}")
    check(f"worker canonModelLow: watch {wmodel!r} matches car {cmodel!r}",
          _js_matches(SRV, wmodel, cmake, cmodel), f"server mirror lacks {_sq(wmodel)} -> {cmodel}")
    # and the new-spelling watch keeps matching a yard that still sends the old spelling
    check(f"app: watch {cmodel!r} matches a raw-feed car {wmodel!r}", _js_matches(APP, cmodel, cmake, wmodel))
# ---- cross-family make in the model (owner report 2026-11-06) ---------------
# Pull-N-Save / Nevada Pic-A-Part rows: VINs and decodes are the real cached
# NHTSA answers for these listed cars (docs/data/vin_decodes.json.gz).
print("cross-family make in the model:")
FM = js.resolve_foreign_make_model
def _dec(make, model, series="", drive=""):
    return {"make": make, "model": model, "series": series, "driveType": drive}
KNOWN = {"acura": {"rl": "RL", "tl": "TL"}, "bmw": {"550i": "550i", "328i": "328i"},
         "toyota": {"4runner": "4Runner"}, "chrysler": {"fifthavenue": "Fifth Avenue"}}
for make, model, dec, want in [
    # JTEBU5JR0D5116438 — the reported Toyota "Audi A3" is a 2013 4Runner
    ("Toyota", "Audi A3", _dec("TOYOTA", "4Runner"), ("Toyota", "4Runner", True, "vin")),
    # WBAVC535X7FZ81105 — Acura "Bmw Rl" decodes as a BMW 328i: the VIN wins
    ("Acura", "Bmw Rl", _dec("BMW", "328i", "3-Series"), ("BMW", "328i", True, "vin")),
    ("Acura", "Volvo El", _dec("VOLVO", "V70"), ("Volvo", "V70", True, "vin")),
    ("Audi", "Volvo S4", _dec("VOLVO", "S40"), ("Volvo", "S40", True, "vin")),
    ("Audi", "Ford Audi Allroad", _dec("FORD", "F-250"), ("Ford", "F-250", True, "vin")),
    ("Chrysler", "Audi 4000", _dec("CHRYSLER", "FIFTH AVENUE"), ("Chrysler", "Fifth Avenue", True, "vin")),
    ("Chrysler", "Mazda 1500 Pickup", _dec("MAZDA", "Mazda6"), ("Mazda", "Mazda6", True, "vin")),
    ("Dodge", "Audi Cabriolet", _dec("DODGE", "Ram", "DR (1500)"), ("Dodge", "Ram 1500", True, "vin")),
    # KMHEC4A40FA137265 — filed Alfa Romeo, VIN is a Hyundai Sonata
    ("Alfa Romeo", "Hyundai Alfa-Romeo 4c", _dec("HYUNDAI", "Sonata"), ("Hyundai", "Sonata", True, "vin")),
    ("BMW", "Hyundai 550i", _dec("HYUNDAI", "Elantra"), ("Hyundai", "Elantra", True, "vin")),
    ("Volvo", "Lexus Ls600Hl", _dec("VOLVO", "S60"), ("Volvo", "S60", True, "vin")),
    # GM twins: VIN confirms the row's make -> untouched; VIN names the twin -> follow it
    ("GMC", "Chevrolet 1500 Pickup", _dec("GMC", "Sierra", "1/2 Ton"), ("GMC", "Chevrolet 1500 Pickup", True, "twin")),
    ("Chevrolet", "Gmc Suburban 1500", _dec("GMC", "Suburban", "1/2 Ton Nominal"), ("GMC", "Suburban 1500", True, "vin")),
    ("GMC", "Chevrolet 1500 Pickup", None, ("GMC", "Chevrolet 1500 Pickup", True, "")),
    # decode contradicts both makes -> not a basis; no known model -> no pick
    ("Toyota", "Audi A3", _dec("HONDA", "Civic"), ("Toyota", "Audi A3", False, "nopick")),
    # multi-model decode ('750i, Alpina B7') is not confident
    ("BMW", "Alfa-Romeo 4C", _dec("BMW", "750i, Alpina B7"), ("BMW", "Alfa-Romeo 4C", False, "nopick")),
    # no decode: strip only onto a known model of the row's make
    ("Acura", "Bmw Rl", None, ("Acura", "RL", True, "strip")),
    ("BMW", "Hyundai 550i", None, ("BMW", "550i", True, "strip")),
    ("Toyota", "Audi A3", None, ("Toyota", "Audi A3", False, "nopick")),
    ("Acura", "Volvo El", None, ("Acura", "Volvo El", False, "nopick")),
    # real names, never touched
    ("Dodge", "Mini Ram", None, ("Dodge", "Mini Ram", True, "")),
    ("Dodge", "Mini Ram", _dec("DODGE", "Mini Ram"), ("Dodge", "Mini Ram", True, "")),
    ("Dodge", "Ram 1500", None, ("Dodge", "Ram 1500", True, "")),
    ("Alfa Romeo", "Alfa-Romeo 4c", None, ("Alfa Romeo", "Alfa-Romeo 4c", True, "")),
    ("Toyota", "4Runner", _dec("TOYOTA", "4Runner"), ("Toyota", "4Runner", True, "")),
]:
    got = FM(make, model, dec, KNOWN)
    check(f"{make} {model!r} dec={dec and dec['make']+' '+dec['model']} -> {want}", got == want, str(got))

# Toyota picker noise: canon folds (stated basis in _MODEL_CANON_BY_MAKE), VIN-only 'EL',
# Scion filed under Toyota moves by the VIN decode only when the model agrees.
for model, want in [("Rav-4 Sport", "RAV4"), ("Prius Awd-E", "Prius"), ("T100 Pickup", "T100"),
                    ("Celica Supra", "Celica Supra"), ("Corona", "Corona"), ("EL", "EL")]:
    check(f"Toyota {model!r} -> {want!r}", N(model, "Toyota") == want, N(model, "Toyota"))
check("Toyota 'EL' + VIN 4Runner -> 4Runner", R("EL", "Toyota", _dec("TOYOTA", "4Runner")) == "4Runner")
check("Toyota 'EL' no decode stays", R("EL", "Toyota", None) == "EL")
check("Toyota 'tC' + VIN 'Scion tC' -> Scion", js._scion_by_vin("Toyota", "tC", _dec("TOYOTA", "Scion tC")) == "Scion")
check("Toyota 'xD' + VIN 'Scion xD' -> Scion", js._scion_by_vin("Toyota", "xD", _dec("TOYOTA", "Scion xD")) == "Scion")
check("Toyota 'tC' + VIN 'Scion xB' stays Toyota", js._scion_by_vin("Toyota", "tC", _dec("TOYOTA", "Scion xB")) is None)
check("Toyota 'tC' no decode stays Toyota", js._scion_by_vin("Toyota", "tC", None) is None)
# saved watches under the folded spellings keep matching on the scan's alert path
for wmodel, cmodel in [("Rav-4 Sport", "RAV4"), ("Prius Awd-E", "Prius"), ("T100 Pickup", "T100")]:
    check(f"scan alert: watch Toyota/{wmodel!r} matches car {cmodel!r}",
          _scan_alert_matches("Toyota", wmodel, "Toyota", N(wmodel, "Toyota")))

# end to end through enrich_vehicles: flag reaches the payload, models.json split
cars = [{"id": i, "vin": "", "year": 2010, "make": "Acura", "model": "RL"} for i in range(3)] + [
    {"id": 10, "vin": "", "year": 2007, "make": "Acura", "model": "Bmw Rl"},
    {"id": 11, "vin": "", "year": 2013, "make": "Toyota", "model": "Audi A3"}]
js.enrich_vehicles(cars)
by = {c["id"]: c for c in cars}
check("enrich: Acura 'Bmw Rl' (no decode, RL known x3) -> RL", by[10]["model"] == "RL" and not by[10].get("_noPick"))
check("enrich: Toyota 'Audi A3' (no decode) keeps text, flagged", by[11]["model"] == "Audi A3" and by[11].get("_noPick"))
check("enrich: stats count by rule", js.FOREIGN_MAKE_STATS.get("strip") == 1 and js.FOREIGN_MAKE_STATS.get("nopick") == 1,
      str(js.FOREIGN_MAKE_STATS))
ents = js.output_json(cars, only_matches=False)
check("output_json: noPick only on the flagged row", [e["id"] for e in ents if e.get("noPick")] == [11])

import json as _json, tempfile as _tf
pl = js.compact_inventory_v2(ents)
check("compact payload: noPickModels lists the flagged pair", pl.get("noPickModels") == {"Toyota": ["Audi A3"]},
      str(pl.get("noPickModels")))
_old_dd = js.DATA_DIR
with _tf.TemporaryDirectory() as td:
    js.DATA_DIR = Path(td)
    try:
        js._write_models_json(pl)
        mj = _json.loads((Path(td) / "models.json").read_text())
    finally:
        js.DATA_DIR = _old_dd
check("models.json: 'Audi A3' not under makes.Toyota", "Audi A3" not in mj["makes"].get("Toyota", {}), str(mj["makes"]))
check("models.json: 'Audi A3' under noPick.Toyota", mj["noPick"].get("Toyota") == {"Audi A3": 1}, str(mj.get("noPick")))
check("models.json: Acura RL counted 4", mj["makes"]["Acura"].get("RL") == 4, str(mj["makes"]))

# ---- another make's model, no make word (hub follow-up 2026-11-07) ----------
print("another make's model without a make word:")
OM = js.resolve_other_make_model
CNT = {("acura", "mdx"): 900, ("acura", "tsx"): 400, ("acura", "csx"): 20, ("nissan", "sentra"): 2000,
       ("mitsubishi", "lancer"): 300, ("dodge", "lancer"): 1, ("bmw", "740"): 1, ("volvo", "740"): 50,
       ("dodge", "sprinter"): 40, ("mercedesbenz", "sprinter"): 1, ("dodge", "caravan"): 900}
OWN = {}
for (mk_, md_), n_ in CNT.items():
    if n_ >= js.OTHER_MAKE_OWNER_MIN:
        OWN.setdefault(md_, set()).add(mk_)
for make, model, dec, want in [
    ("Dodge", "MDX", _dec("DODGE", "Grand Caravan"), ("Dodge", "Grand Caravan", True, "other_vin")),
    ("BMW", "TSX", _dec("BMW", "335i"), ("BMW", "335i", True, "other_vin")),
    ("Oldsmobile", "Sentra", _dec("NISSAN", "Sentra"), ("Nissan", "Sentra", True, "other_vin")),
    ("Dodge", "CSX", None, ("Dodge", "CSX", False, "other_nopick")),
    # decode names a third make: no basis -> noPick, never guessed
    ("Dodge", "MDX", _dec("HONDA", "Odyssey"), ("Dodge", "MDX", False, "other_nopick")),
    # comma decode is not confident
    ("BMW", "TSX", _dec("BMW", "750i, Alpina B7"), ("BMW", "TSX", False, "other_nopick")),
    # real names: decode agrees with the row's model / numeric / twin / known
    ("Dodge", "Lancer", _dec("DODGE", "LANCER"), ("Dodge", "Lancer", True, "")),
    ("Dodge", "Lancer", None, ("Dodge", "Lancer", False, "other_nopick")),
    ("BMW", "740", None, ("BMW", "740", True, "")),
    ("Mercedes-Benz", "Sprinter", None, ("Mercedes-Benz", "Sprinter", True, "")),
    ("Dodge", "Caravan", None, ("Dodge", "Caravan", True, "")),
    ("AMC", "Sentra", None, ("AMC", "Sentra", True, "")),
]:
    got = OM(make, model, dec, CNT, OWN)
    check(f"{make} {model!r} dec={dec and dec['make']+' '+dec['model']} -> {want}", got == want, str(got))
# comma-joined decode names never become the model; the row keeps its own blob
for blob, dm in [("7 Series", "750i, Alpina B7"), ("7 Series", "750Li, Alpina B7"), ("7 Series", "750Lxi, Alpina B7")]:
    check(f"BMW {blob!r} + decode {dm!r} keeps {blob!r}", R(blob, "BMW", _dec("BMW", dm, "7-Series")) == blob,
          R(blob, "BMW", _dec("BMW", dm, "7-Series")))
cars2 = [{"id": 20, "vin": "", "year": 2012, "make": "BMW", "model": "750Lxi, Alpina B7"},
         {"id": 21, "vin": "", "year": 2012, "make": "BMW", "model": "750Li"}]
js.enrich_vehicles(cars2)
check("enrich: comma model kept as text, flagged noPick", cars2[0]["model"] == "750Lxi, Alpina B7" and cars2[0].get("_noPick"))
check("enrich: plain model not flagged", not cars2[1].get("_noPick"))
check("BMW '7 Series' + decode '750i' still resolves", R("7 Series", "BMW", _dec("BMW", "750i")) == "750i")

# ---- noPick is pair-level only when EVERY car of the pair is flagged --------
# 2026-11-08 regression: one unresolved Pull-N-Save "Tracker" (adapter flag)
# moved all 27 Geo Trackers out of models.json `makes`; the daily ops email
# then reported a saved "Geo Tracker" watch as matching no car.
print("noPick pairs need every car flagged:")
def _ent(i, make, model, flag):
    e = {"id": i, "vin": "", "year": 1995, "make": make, "model": model, "row": "", "dateAdded": "",
         "location": "Y", "city": "C", "state": "AZ", "lat": 1.0, "lng": 2.0, "maxValue": 0, "topParts": []}
    if flag:
        e["noPick"] = True
    return e
mixed = [_ent(1, "Geo", "Tracker", True), _ent(2, "Geo", "Tracker", False), _ent(3, "Geo", "Tracker", False),
         _ent(4, "Plymouth", "SW", True), _ent(5, "Ford", "F-150", True)] + [_ent(10 + i, "Ford", "F-150", False) for i in range(5)]
plm = js.compact_inventory_v2(mixed)
check("mixed pair Geo Tracker not listed", "Tracker" not in plm["noPickModels"].get("Geo", []), str(plm["noPickModels"]))
check("mixed pair Ford F-150 not listed", "F-150" not in plm["noPickModels"].get("Ford", []), str(plm["noPickModels"]))
check("all-flagged pair Plymouth SW listed", plm["noPickModels"] == {"Plymouth": ["SW"]}, str(plm["noPickModels"]))
with _tf.TemporaryDirectory() as td:
    js.DATA_DIR = Path(td)
    try:
        js._write_models_json(plm)
        mj2 = _json.loads((Path(td) / "models.json").read_text())
    finally:
        js.DATA_DIR = _old_dd
check("models.json: Geo Tracker stays in makes with all 3 cars", mj2["makes"].get("Geo", {}).get("Tracker") == 3, str(mj2["makes"]))
check("models.json: Ford F-150 stays in makes with all 6 cars", mj2["makes"].get("Ford", {}).get("F-150") == 6)
check("models.json: Plymouth SW under noPick", mj2["noPick"] == {"Plymouth": {"SW": 1}}, str(mj2["noPick"]))
# carry-forward: a carried clean car un-lists a pair; a carried flagged car
# keeps it listed only when no clean car of it exists
_y2 = lambda name: dict(location=name, city="C", state="AZ", lat=1.0, lng=2.0)
new_e = [dict(_ent(1, "Plymouth", "SW", True), **_y2("A")), dict(_ent(2, "Geo", "Storm", True), **_y2("A"))]
prev_e = [dict(_ent(7, "Geo", "Storm", False), **_y2("B")), dict(_ent(8, "Pontiac", "Optima", True), **_y2("B"))]
newp, prevp = js.compact_inventory_v2(new_e), js.compact_inventory_v2(prev_e)
js.merge_carryforward_yards(newp, prevp, ["B"])
check("carry-forward: clean carried Geo Storm un-lists it; flagged pairs stay",
      newp["noPickModels"] == {"Plymouth": ["SW"], "Pontiac": ["Optima"]}, str(newp["noPickModels"]))

# ---- junk model names (owner report 2026-11-08, Parts tab 2003 Chevrolet) ---
print("junk model names:")
JK, RJ = js.junk_model_kind, js.resolve_junk_model
for make, model, want in [
    ("Chevrolet", "chevy", "alias"), ("Smart", "Smart", "alias"), ("Dodge", "Dodge", "alias"),
    ("Chevrolet", "Caprice Classic Or Impala", "alternatives"), ("Isuzu", "Rodeo/Amigo", "alternatives"),
    ("Audi", "A3/S3", "alternatives"), ("Chevrolet", "Cargo Van", "body"), ("Ford", "Wagon", "body"),
    ("Chevrolet", "Van", "body"), ("Ford", "Truck", "body"), ("Packard", "Sedan", "body"),
    # real names stay
    ("Toyota", "Pickup", ""), ("Nissan", "Pickup", ""), ("Nissan", "Truck", ""), ("Mazda", "Truck", ""),
    ("Toyota", "Van", ""), ("Saturn", "SW", ""), ("MINI", "Convertible", ""), ("Volkswagen", "Bus", ""),
    ("Dodge", "Ram Van", ""), ("Dodge", "Ram", ""), ("Land Rover", "Range Rover", ""),
    ("Cadillac", "Fleetwood", ""), ("Chevrolet", "C/K 1500", ""), ("Chevrolet", "R/V 20", ""),
    ("Ram", "C/V", ""), ("Chevrolet", "Blazer S10/Jimmy S15", ""), ("Chevrolet", "S10/S15/Sonoma", ""),
    ("Dodge", "Caravan/Grand Caravan", ""), ("GMC", "Jimmy Or Envoy", ""), ("Lexus", "SC 300/400", ""),
    ("Other", "Other", ""), ("Trailer", "Trailer", ""), ("Chevrolet", "Impala", ""),
]:
    check(f"junk kind {make} {model!r} -> {want!r}", JK(make, model) == want, JK(make, model))
for make, model, dec, want in [
    ("Chevrolet", "Caprice Classic Or Impala", _dec("CHEVROLET", "Impala"), ("Impala", True, "junk_vin")),
    ("Chevrolet", "Cargo Van", _dec("CHEVROLET", "Express", "2500 (3/4 Ton)"), ("Express 2500", True, "junk_vin")),
    ("Chevrolet", "chevy", _dec("CHEVROLET", "Malibu"), ("Malibu", True, "junk_vin")),
    ("Chevrolet", "chevy", None, ("chevy", False, "junk_nopick")),
    ("Chevrolet", "Cargo Van", _dec("FORD", "E-250"), ("Cargo Van", False, "junk_nopick")),  # make disagrees
    ("Ford", "Wagon", _dec("FORD", "Wagon"), ("Wagon", False, "junk_nopick")),              # decode no better
    ("Toyota", "Pickup", _dec("TOYOTA", "Pickup"), ("Pickup", True, "")),
]:
    got = RJ(make, model, dec)
    check(f"{make} {model!r} dec={dec and dec['make']+' '+dec['model']} -> {want}", got == want, str(got))

for mk_ in ("Chevrolet", "GMC"):
    for raw_ in ("S10/s15/sonoma Truck", "S10/S15/Sonoma Pickup"):
        check(f"{mk_} {raw_!r} -> 'S10/S15/Sonoma'", N(raw_, mk_) == "S10/S15/Sonoma", N(raw_, mk_))
        check(f"scan alert: watch {mk_}/{raw_!r} matches car 'S10/S15/Sonoma'",
              _scan_alert_matches(mk_, raw_, mk_, N(raw_, mk_)))

# ---- modelYears: per make|model span for year-appropriate pickers -----------
print("modelYears:")
ye = [_ent(1, "Chevrolet", "Chevelle", False), _ent(2, "Chevrolet", "Chevelle", False),
      _ent(3, "Chevrolet", "Impala", False), _ent(4, "Chevrolet", "Impala", False), _ent(5, "Chevrolet", "Impala", False)]
ye[0]["year"], ye[1]["year"] = 1970, 1972
ye[2]["year"], ye[3]["year"], ye[4]["year"] = 2003, 2003, 1999
ye[4]["spanYear"] = 2008          # VIN model year wins over the listing year
ye.append(dict(_ent(6, "Chevrolet", "Impala", False), year=0))       # unknown year skipped
ye.append(dict(_ent(7, "Chevrolet", "Impala", False), year=2091))    # implausible skipped
ply = js.compact_inventory_v2(ye)
check("modelYears Chevelle [1970, 1972]", ply["modelYears"]["Chevrolet"]["Chevelle"] == [1970, 1972], str(ply["modelYears"]))
check("modelYears Impala [2003, 2008] (VIN year, junk years skipped)",
      ply["modelYears"]["Chevrolet"]["Impala"] == [2003, 2008], str(ply["modelYears"]))
with _tf.TemporaryDirectory() as td:
    js.DATA_DIR = Path(td)
    try:
        js._write_models_json(ply)
        mj3 = _json.loads((Path(td) / "models.json").read_text())
    finally:
        js.DATA_DIR = _old_dd
check("models.json carries modelYears", mj3["modelYears"] == ply["modelYears"])
cy = js.enrich_vehicles([{"id": 30, "vin": "", "year": 2003, "make": "Chevrolet", "model": "Impala"}])
check("enrich sets _spanYear from the listing year without a decode", cy[0].get("_spanYear") == 2003, str(cy[0].get("_spanYear")))

# ---- body style for photo-less silhouettes (vehicle_extras index 5) --------
print("body style from vPIC bodyClass:")
BS = js.body_style_from_vpic
for bc, want in [("Sedan/Saloon", "sedan"), ("Coupe", "coupe"), ("Hatchback/Liftback/Notchback", "hatchback"),
                 ("Wagon", "wagon"), ("Sport Utility Vehicle [SUV]/Multipurpose Vehicle [MPV]", "suv"),
                 ("Crossover Utility Vehicle [CUV]", "suv"), ("Pickup", "pickup"), ("Sport Utility Truck [SUT]", "pickup"),
                 ("Minivan", "van"), ("Van", "van"), ("Cargo Van", "van"), ("Convertible/Cabriolet", "convertible"),
                 ("Roadster", "convertible"), ("Incomplete - Cutaway", ""), ("Truck-Tractor", ""),
                 ("Motorcycle - Sport", ""), ("Limousine", ""), ("", "")]:
    check(f"bodyClass {bc!r} -> {want!r}", BS({"make": "FORD", "bodyClass": bc}, "Ford") == want)
check("no decode -> ''", BS(None, "Ford") == "")
check("same-family decode make keeps the style (Chrysler row, DODGE VIN)", BS({"make": "DODGE", "bodyClass": "Minivan"}, "Chrysler") == "van")
check("cross-family decode make -> '' (scrambled row)", BS({"make": "TOYOTA", "bodyClass": "Sport Utility Vehicle [SUV]/Multipurpose Vehicle [MPV]"}, "Audi") == "")
ob = js.output_json([{"id": 40, "vin": "X", "year": 2010, "make": "Ford", "model": "Escape",
                      "_vpic": {"make": "FORD", "model": "Escape", "bodyClass": "Sport Utility Vehicle [SUV]/Multipurpose Vehicle [MPV]"}}],
                    only_matches=False)
pb = js.compact_inventory_v2([dict(ob[0], location="Y", city="C", state="AZ", lat=1.0, lng=2.0)])
check("extras carry body at index 5", pb["_extras"].get("40", [None] * 6)[5:6] == ["suv"], str(pb["_extras"]))

check("app and worker mirror tables agree (same keys, same values modulo case)",
      all(set(APP.get(m, {})) == set(SRV.get(m, {})) and
          all(APP[m][k].lower() == SRV[m][k] for k in APP.get(m, {})) for m in set(APP) | set(SRV)),
      str([m for m in set(APP) | set(SRV) if set(APP.get(m, {})) != set(SRV.get(m, {}))]))

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("all model-normalization tests passed")
