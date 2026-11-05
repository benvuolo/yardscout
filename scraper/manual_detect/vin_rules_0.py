#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 0: Honda and Acura.

Honda's own Part 565 VIN filings (NHTSA Manufacturer Information Database)
define a VIN character that carries the transmission type for every Honda
and Acura passenger car, MPV and truck:

  * MY1987-2009 Honda, MY1986-2009 Acura: character 7 is "body type and
    transmission": odd digit = manual, even digit = automatic
    (1/2 = 2-door, 3/4 = 2-door hatch or 3-door, 5/6 = 4-door sedan,
    7/8 = 5-door / wagon / SUV / van).
  * MY2010 on, both brands: character 7 is a letter with the same pairing:
    A/B = 2-door, C/D = 3-door, E/F = 4-door, G/H = 5-door; A, C, E, G =
    manual and B, D, F, H = automatic (CVT and DCT included).
  * MY1984-1986 Honda (before the 1987 recode): character 6 is the
    transmission (3 = 3-speed automatic, 4 = 4-speed manual, 5 = 5-speed
    manual, 6 = 5-speed manual + Super Low, 7 = 4-speed automatic) and
    character 7 is the body only.

This script turns that into rules, applies them to every lot car with a
Honda/Acura WMI and a valid check digit, validates each rule against
ground_truth.jsonl (uniformCell lines treated as unlabelled), cross-checks
every in-scope car against EPA (year/make/model union, vPIC displacement
when known), and counts the lot cars WITHOUT transmission info each manual
rule would newly confirm.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl
        (build_baseline.py), scraper/manual_detect/epa/vehicles.csv (optional,
        for the EPA cross-check).
Output: scraper/manual_detect/vin_rules_0.json

Run:  python3 -I scraper/manual_detect/vin_rules_0.py
"""

import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import epa_profile as ep  # noqa: E402  (norm, epa_keys, feed_keys, trany_class)

OUT = HERE / "vin_rules_0.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"

# WMIs from Honda's own filings (MY2003 TL, MY2007 Fit, MY2010 and MY2024
# filings list them). Motorcycle/ATV WMIs (JH2, JH3, 478, 1HF) are not here;
# neither are 4S6 (Isuzu-built Honda Passport) and JAE (Isuzu-built Acura
# SLX), whose VINs follow Isuzu's scheme, not Honda's.
HONDA_WMI = {"JHM", "JHL", "JH1", "1HG", "5J6", "5J7", "5KB", "5FN", "5FP",
             "19X", "7FA", "2HG", "2HK", "2HJ", "3HG", "3CZ", "SHH", "SHS"}
ACURA_WMI = {"JH4", "19U", "5J8", "5J0", "5KC", "5FR", "5FS", "19V", "2HH",
             "2HN", "2HU", "3HD"}

# ---------------------------------------------------------------------------
# Citations (all public PDFs in NHTSA's Manufacturer Information Database).
# ---------------------------------------------------------------------------
C = {
    "mid_1983_09_12": {
        "url": MID + "5ec1023d-ef91-47ab-a2e7-9b636dd7885d",
        "doc": "NHTSA 01-22-N11B-1384, American Honda letter 1983-09-12 (table issued 1983-06-08, rows added 1983-08-08), 1984 Honda Accord, Prelude, Civic Wagon",
        "says": "Construction of VIN: character 6 = transmission (5 = 5-speed manual, 7 = 4-speed automatic, 3 = 3-speed automatic); character 7 = body type (2 2-door sedan, 3 2-door hatchback, 4 4-door sedan, 5 4-door wagon). Example JHMAD532 = Accord hatchback 5M, JHMAD732 = 4A, JHMAN352 = Civic Wagon 3A.",
    },
    "mid_1984_06_20": {
        "url": MID + "99140621-6bb8-4988-9922-bf53e3f0bd32",
        "doc": "NHTSA 01-22-N11B-1717, American Honda letter 1984-06-20, 1985 Honda Accord, Prelude, Civic (all lines)",
        "says": "Character 6 = transmission: 3 = 3-speed automatic, 4 = 4-speed manual, 5 = 5-speed manual, 7 = 4-speed automatic; character 7 = body. Civic CRX/hatch/sedan: JHMAF531 CRX HF M5, JHMAF332 CRX L3, JHMAG431 1300 hatch M4, JHMAK343 sedan L3.",
    },
    "mid_1985_06_12": {
        "url": MID + "386ede85-a1c2-474d-bccf-88647bd49403",
        "doc": "NHTSA 01-22-N11B-1906, American Honda letter 1985-06-12, 1986 Honda Civic CRX/hatchback/4-door sedan",
        "says": "Character 6 = transmission representation: 4 = 4 speed manual, 5 = 5 speed manual, 7 = 4 speed automatic; character 7 = body type (3 = 2-door hatchback or coupe, 4 = 4-door sedan). JHMAK543 sedan M5, JHMAK743 sedan L4.",
    },
    "mid_1985_07_11": {
        "url": MID + "66a0a3d1-e263-40e0-9dc2-92f115a9a147",
        "doc": "NHTSA 01-22-N11B-1989, American Honda letter 1985-07-11, 1986 Honda Accord, Prelude, Civic Wagon, Civic Wagon 4WD",
        "says": "Character 6 = transmission: 5 = 5-speed manual, 6 = 5-speed manual + Super Low, 7 = 4-speed automatic. JHMBA532 Accord hatchback 5M, JHMBA742 Accord sedan 4A, JHMAR652 Civic Wagon 4WD 5M+SL.",
    },
    "mid_1985_11_19": {
        "url": MID + "594deacc-cedf-43c3-afc4-b371a3562bca",
        "doc": "NHTSA 01-22-N11B-2081, American Honda letter 1985-11-19, 1986 Acura Integra (and 1986 Civic Wagovan)",
        "says": "1986 Acura already uses character 7 = 'Body type and Transmission representation': 3 = 3-door hatchback 5-speed manual, 4 = 3-door hatchback 4-speed automatic, 7 = 5-door hatchback 5-speed manual, 8 = 5-door hatchback 4-speed automatic. Same letter re-issues the 1986 Honda table (character 6 = transmission; VN552 Civic Wagovan 5M).",
    },
    "mid_1986_06_27": {
        "url": MID + "1d1d246e-7f53-42d7-92d9-8296b5acb4e9",
        "doc": "NHTSA 01-22-N11B-2373, American Honda letter 1986-06-27, 1987 Honda Accord and Prelude",
        "says": "Character 7 = 'Body type and Transmission representation': 1 = 2-door sedan Manual, 2 = 2-door sedan Automatic, 3 = 2-door hatchback Manual, 4 = 2-door hatchback Automatic, 5 = 4-door sedan Manual, 6 = 4-door sedan Automatic. JHMCA552 = Accord sedan 5M, JHMCA562 = 4A, JHMBA314 = Prelude Si 5M, JHMBA324 = 4A.",
    },
    "mid_1986_07_18": {
        "url": MID + "ee50d2f2-0644-4c5b-b967-8df8837e14d6",
        "doc": "NHTSA 01-22-N11B-2350, American Honda letter 1986-07-18, 1987 Honda Civic (CRX, hatchback, sedan, Wagon, Wagovan)",
        "says": "Character 7 = body type and transmission: 3 = 2-door hatchback or coupe Manual, 4 = Automatic, 5 = 4-door sedan Manual, 6 = Automatic, 7 = 4-door wagon manual, 8 = 4-door wagon automatic. JHMEC572 Civic Wagon 5M, JHMEC582 4A, JHMEY172 Wagovan 5M.",
    },
    "mid_1986_08_26": {
        "url": MID + "b8c1ed83-b581-4aaf-b66e-989269918f50",
        "doc": "NHTSA 01-22-N11B-2440, American Honda letter 1986-08-26, revised 1987 Accord/Prelude adding Civic Wagon Real Time 4WD",
        "says": "Same character-7 table plus 7 = 4-door wagon Manual; JHMEC672 Civic Wagon Real Time 4WD = 5M+SL.",
    },
    "mid_1988_06_10": {
        "url": MID + "5ac16ebd-6ab7-49b1-ae7d-eee4f41ac222",
        "doc": "NHTSA 01-22-N11B-3143, American Honda letter 1988-06-10, 1989 Acura Integra",
        "says": "DA334 = Integra 3-door RS 5M, DA344 = 3-door RS 4A, DA335/DA345 = LS 5M/4A, DA174/DA184 = 5-door RS 5M/4A, DA175/DA185 = 5-door LS 5M/4A.",
    },
    "mid_1996_07_01": {
        "url": MID + "27ea75b4-8c79-4a9c-9b66-029270dbe9a5",
        "doc": "NHTSA 01-022-N11B-6178, American Honda letter 1996-07-01, 1997 Honda Civic and Accord, 1997 Acura 3.0CL",
        "says": "1997 Accord 2nd-section table: CD552/CD551/CD553/CD554/CD550/CD555/CD556 = 4-door sedan 5MT; CD562/CD561/CD563/CD564/CD560/CD565/CD566 = 4-door sedan 4AT; CE663/CE664/CE665/CE667 = V6 sedan 4AT (C27A4); CD71x = coupe 5MT, CD72x = coupe 4AT; CE172 = wagon 5MT, CE182/CE183/CE189 = wagon 4AT. 1997 Civic: EJ65x sedan 5MT, EJ66x sedan 4AT, EJ61x/EJ62x coupe 5MT/4AT, EJ71x/EJ72x HX coupe 5MT/CVT, EJ63x/EJ64x hatchback 5MT/4AT. 1997 3.0CL YA224/YA225 = 2/CPE 4AT.",
    },
    "mid_2002_01_02": {
        "url": MID + "836ed5a1-3594-439d-a5dd-cd214c21621b",
        "doc": "NHTSA 01-022-N11B-8561 (AHCERT-220003), American Honda letter 2002-01-02, 2003 Acura 3.2TL",
        "says": "UA566/UA567/UA568/UA569 = 3.2TL 4DR Sedan 5AT (character 7 = 6).",
    },
    "mid_2005_10_31": {
        "url": MID + "260e4159-7c32-4e16-8fc1-b50a6b3aa5ce",
        "doc": "NHTSA 01-022-N11B-10902, American Honda letter 2005-10-31, 2007 Honda Fit",
        "says": "2007 Honda Fit model codes: GD374 = 5MT 5DR hatchback, GD384 = 5AT, GD376 = 5MT, GD386 = 5AT (engine L15A1).",
    },
    "mid_2009_08_24": {
        "url": MID + "7bdb4344-93a5-4415-ab31-11864e261300",
        "doc": "MID ORG5294, American Honda filing dated 2009-08-24, 2010 Honda/Acura (MDX, TL, Civic, CR-V, Element, Odyssey, Pilot)",
        "says": "Positions 4-8 'model code' tables, first letter-coded year: FA1E2 Civic DX 5MT 4DR Sedan / FA1F2 5AT; FA5E5 Civic Si 6MT 4DR; FA3F2 Civic Hybrid CVT 4DR; FG1A2 Civic DX 5MT 2DR Coupe / FG1B2 5AT; FG2A5 Civic Si 6MT 2DR; YH2G7 Element 4WD EX 5MT 5DR SUV / YH1H3 5AT; UA9E5 TL SH-AWD 6MT 4DR / UA9F5 5AT; RE3H3 CR-V 5AT 5DR; RL3H2 Odyssey 5AT 5DR VAN; YF4H2 Pilot 5AT 5DR SUV; YD2H2 MDX 6AT 5DR SUV.",
    },
    "mid_2010_03_10": {
        "url": MID + "f293cffc-27b6-4ce0-9f20-412a4c955188",
        "doc": "MID ORG5705, American Honda letter 2010-03-10, 2011 Honda CR-Z",
        "says": "ZF1C4/ZF1C6 = CR-Z 6MT 3DR HatchBack; ZF1D4/ZF1D6 = CR-Z CVT 3DR HatchBack (character 7 C = 3-door manual, D = 3-door automatic/CVT).",
    },
    "mid_2023_07_21": {
        "url": MID + "51b13a22-cf03-40a9-84d5-3cda0375140f",
        "doc": "MID ORG21966, American Honda letter 2023-07-20, 2024 Honda Civic Type R",
        "says": "FL5G4 = CIVIC HATCHBACK Type R, 6MT, 5DR Hatchback (character 7 G = 5-door manual still in use for MY2024).",
    },
}

EPA_CIT = {
    "url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
    "doc": "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29, sha256 33d32caa...b22f)",
}

# ---------------------------------------------------------------------------
# VIN helpers
# ---------------------------------------------------------------------------
_TRANSLIT = {**{str(d): d for d in range(10)},
             "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
             "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
             "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"   # 1980..2009, then repeats


def check_digit_ok(vin: str) -> bool:
    if len(vin) != 17 or any(ch not in _TRANSLIT for ch in vin):
        return False
    s = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS))
    r = s % 11
    return vin[8] == ("X" if r == 10 else str(r))


def vin_year(vin: str, hint: int | None) -> int | None:
    """Model year from character 10, using the feed / vPIC year only to pick
    the 30-year cycle. None when the code is invalid or the hint is >2 years
    away from every candidate (VIN and listing disagree)."""
    code = vin[9]
    i = _YEAR_CODES.find(code)
    if i < 0:
        return None
    cands = [1980 + i] + ([2010 + i] if i < 21 else [])
    if not hint:
        return cands[0] if len(cands) == 1 else None
    best = min(cands, key=lambda y: abs(y - hint))
    return best if abs(best - hint) <= 2 else None


def brand_of(vin: str) -> str:
    w = vin[:3]
    return "Honda" if w in HONDA_WMI else ("Acura" if w in ACURA_WMI else "")


# Old (MY1984-1986 Honda) scheme: character 6 = transmission. Line codes
# (characters 4-5) are the ones the cited filings list for each year.
OLD_LINES = {
    1984: {"AD", "AB", "AN"},                                      # mid_1983_09_12
    1985: {"AD", "AB", "AN", "AF", "AG", "AH", "AK"},              # mid_1984_06_20
    1986: {"AF", "AG", "AH", "AK", "BA", "AB", "BB", "AN", "AR", "VN"},  # mid_1985_06_12/07_11/11_19
}
OLD_T6 = {"3": ("automatic", "3-speed automatic"), "4": ("manual", "4-speed manual"),
          "5": ("manual", "5-speed manual"), "6": ("manual", "5-speed manual + Super Low"),
          "7": ("automatic", "4-speed automatic")}
DIGIT_T7 = {"1": ("manual", "2-door, manual"), "2": ("automatic", "2-door, automatic"),
            "3": ("manual", "2-door hatchback / 3-door, manual"), "4": ("automatic", "2-door hatchback / 3-door, automatic"),
            "5": ("manual", "4-door sedan, manual"), "6": ("automatic", "4-door sedan, automatic (incl. CVT)"),
            "7": ("manual", "5-door / wagon / SUV / van, manual"), "8": ("automatic", "5-door / wagon / SUV / van, automatic")}
LETTER_T7 = {"A": ("manual", "2-door, manual"), "B": ("automatic", "2-door, automatic/CVT"),
             "C": ("manual", "3-door, manual"), "D": ("automatic", "3-door, automatic/CVT"),
             "E": ("manual", "4-door, manual"), "F": ("automatic", "4-door, automatic/CVT/DCT"),
             "G": ("manual", "5-door, manual"), "H": ("automatic", "5-door, automatic/CVT")}


def classify(vin: str, year: int) -> tuple[str, str, str] | None:
    """-> (rule_id, claim, code meaning) or None when no rule covers the VIN."""
    brand = brand_of(vin)
    p6, p7 = vin[5], vin[6]
    line = vin[3:5]
    if brand == "Honda" and 1984 <= year <= 1986:
        if line in OLD_LINES[year] and p6 in OLD_T6 and p7 in "2345":
            claim, meaning = OLD_T6[p6]
            return (f"honda_vin6_1984_1986_{claim}", claim, f"char6={p6}: {meaning}")
        return None
    lo = 1987 if brand == "Honda" else 1986
    if brand and lo <= year <= 2009:
        if p7 not in DIGIT_T7:
            return None
        claim, meaning = DIGIT_T7[p7]
        if brand == "Honda" and year == 1997 and line in ("CD", "CE"):
            return (f"honda_accord_1997_vin7_{claim}", claim, f"char7={p7}: {meaning}")
        return (f"{brand.lower()}_vin7_digit_{lo}_2009_{claim}", claim, f"char7={p7}: {meaning}")
    if brand and year >= 2010:
        if p7 not in LETTER_T7:
            return None
        claim, meaning = LETTER_T7[p7]
        return (f"{brand.lower()}_vin7_letter_2010_on_{claim}", claim, f"char7={p7}: {meaning}")
    return None


def tclass(t: str) -> str:
    """Same buckets as build_baseline.trans_class (manual = app isConfirmedManual)."""
    s = (t or "").strip()
    if not s:
        return ""
    if re.search(r"manual", s, re.I) and not re.search(r"automated", s, re.I):
        return "manual"
    if re.search(r"automated manual|\bAMT\b", s, re.I):
        return "amt"
    if re.search(r"dual.clutch|\bDCT\b", s, re.I):
        return "dct"
    if re.search(r"continuously variable|\bcvt\b", s, re.I):
        return "cvt"
    if re.search(r"automatic", s, re.I):
        return "automatic"
    return "other"


KNOWN = {"manual", "automatic", "cvt", "amt", "dct"}


# ---------------------------------------------------------------------------
# EPA cross-check (independent of vPIC)
# ---------------------------------------------------------------------------
class Epa:
    def __init__(self, path: Path):
        self.ok = path.exists()
        self.idx: dict[tuple[int, str, str], set[int]] = defaultdict(set)
        self.rows: list[dict] = []
        if not self.ok:
            return
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["make"] not in ("Honda", "Acura"):
                    continue
                try:
                    y = int(r["year"])
                except ValueError:
                    continue
                i = len(self.rows)
                self.rows.append(r)
                for _lv, k in ep.epa_keys(r):
                    self.idx[(y, r["make"], k)].add(i)

    def classes(self, year: int, make: str, models: list[str], displ: float | None) -> set[str] | None:
        hits: set[int] = set()
        for m in models:
            if not m:
                continue
            for _lv, k in ep.feed_keys(make, m):
                hits |= self.idx.get((year, make, k), set())
        if not hits:
            return None
        if displ:
            same = {i for i in hits if self.rows[i]["displ"] and abs(float(self.rows[i]["displ"]) - displ) < 0.051}
            if same:
                hits = same
        return {ep.trany_class(self.rows[i]["trany"]) for i in hits}


def main() -> int:
    inv = json.loads((DATA / "inventory_live.json").read_text())
    extras = json.loads((DATA / "vehicle_extras.json").read_text())["extras"]
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache.pop("_exportedAt", None)
    gt = {}
    with open(HERE / "ground_truth.jsonl") as f:
        for line in f:
            d = json.loads(line)
            gt[d["id"]] = d
    epa = Epa(HERE / "epa" / "vehicles.csv")
    fi = {f: i for i, f in enumerate(inv["fields"])}

    stats: dict[str, dict] = defaultdict(lambda: {
        "in_scope_cars": 0, "checkable": 0, "agree": 0, "disagree": 0,
        "uniform_cell_excluded": 0, "uniform_cell_agree": 0, "gt_other_speeds_only": 0,
        "no_trans_info": 0, "no_trans_info_reason": Counter(),
        "published_contradicts_rule": 0, "published_contradicts_examples": [],
        "disagree_examples": [], "codes": Counter(), "models": Counter(), "years": Counter(),
        "epa": Counter(), "epa_conflict_examples": [], "feed_make_mismatch": 0,
    })
    # (VIN model year, chars 4-7) that vPIC decodes to a model on some lot car:
    # the code is in the data NHTSA built from Honda's filings.
    documented: set[tuple[int, str]] = set()
    for row in inv["vehicles"]:
        vin = (row[fi["vin"]] or "").strip().upper()
        d = cache.get(vin) if len(vin) == 17 and brand_of(vin) else None
        if isinstance(d, dict) and d.get("model") and check_digit_ok(vin):
            try:
                y = vin_year(vin, int(str(d.get("modelYear") or 0)[:4]) or None)
            except ValueError:
                y = None
            if y:
                documented.add((y, vin[3:7]))

    scan = Counter()
    newly_cars: list[dict] = []
    for row in inv["vehicles"]:
        vin = (row[fi["vin"]] or "").strip().upper()
        if len(vin) != 17 or not brand_of(vin):
            continue
        scan["honda_acura_wmi"] += 1
        if not check_digit_ok(vin):
            scan["bad_check_digit"] += 1
            continue
        vid = str(row[fi["id"]])
        raw = cache.get(vin)
        dec = raw if isinstance(raw, dict) else None
        try:
            hint = int(str((dec or {}).get("modelYear") or row[fi["year"]] or 0)[:4]) or None
        except ValueError:
            hint = None
        year = vin_year(vin, hint)
        if year is None:
            scan["year_unresolved"] += 1
            continue
        hit = classify(vin, year)
        if not hit:
            scan["no_rule"] += 1
            scan[f"no_rule_{brand_of(vin)}_{'pre1984' if year < 1984 else ('digit' if year < 2010 else 'letter')}"] += 1
            continue
        rid, claim, meaning = hit
        # A character-7 code whose line/body/transmission prefix (chars 4-7)
        # NHTSA's vPIC has never decoded to a model for that year is a code
        # Honda did not file with NHTSA (Canada-market Acura EL / CSX ...).
        # Honda's construction rule still defines character 7, but no filing
        # lists that exact code, so those cars get their own low-sample rule.
        if "_vin7_" in rid and "accord_1997" not in rid:
            if not ((dec or {}).get("model") or (year, vin[3:7]) in documented):
                rid = f"honda_acura_vin7_code_not_in_vpic_{claim}"
                scan["code_not_in_vpic"] += 1
        scan["covered"] += 1
        s = stats[rid]
        s["in_scope_cars"] += 1
        s["codes"][meaning] += 1
        model = row[fi["model"]] or ""
        s["models"][model] += 1
        s["years"][year] += 1
        feed_make = row[fi["make"]] or ""
        if feed_make.lower() != brand_of(vin).lower():
            s["feed_make_mismatch"] += 1

        ex = list(extras.get(vid) or []) + [""] * 5
        pub = ex[3] or ""
        pc = tclass(pub)
        if not pub:
            s["no_trans_info"] += 1
            reason = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if not dec.get("transmission") else "other")
            s["no_trans_info_reason"][reason] += 1
            if claim == "manual":
                yd = row[fi["yard"]]
                newly_cars.append({"id": vid, "vin": vin, "year": year, "make": feed_make, "model": model,
                                   "rule": rid, "code": meaning, "why_no_trans": reason,
                                   "yard": inv["yards"][yd][0] if isinstance(yd, int) else ""})
        elif pc in KNOWN and ((pc == "manual") != (claim == "manual")):
            s["published_contradicts_rule"] += 1
            if len(s["published_contradicts_examples"]) < 8:
                s["published_contradicts_examples"].append(
                    {"vin": vin, "year": year, "model": model, "published": pub, "src": ex[4]})

        g = gt.get(vid)
        if g:
            gc = g.get("transClass", "")
            if g.get("uniformCell"):
                s["uniform_cell_excluded"] += 1
                if gc in KNOWN and ((gc == "manual") == (claim == "manual")):
                    s["uniform_cell_agree"] += 1
            elif gc in KNOWN:
                s["checkable"] += 1
                if (gc == "manual") == (claim == "manual"):
                    s["agree"] += 1
                else:
                    s["disagree"] += 1
                    if len(s["disagree_examples"]) < 12:
                        s["disagree_examples"].append(
                            {"vin": vin, "year": year, "model": model, "ground_truth": g.get("trans"),
                             "vpic_trim": g.get("trim"), "source": g.get("source")})
            elif gc == "other":
                s["gt_other_speeds_only"] += 1

        # EPA: does EPA list a transmission of the claimed kind for this
        # year/make/model (and vPIC displacement when known)?
        if epa.ok:
            displ = None
            m = re.match(r"(\d+(?:\.\d+)?)L", (dec or {}).get("engine") or "")
            if m:
                displ = float(m.group(1))
            cls = epa.classes(year, brand_of(vin), [model, (dec or {}).get("model", "")], displ)
            if cls is None:
                s["epa"]["no_epa_match"] += 1
            else:
                want = {"manual"} if claim == "manual" else {"automatic", "cvt", "amt"}
                if cls & want:
                    s["epa"]["consistent"] += 1
                else:
                    s["epa"]["conflict"] += 1
                    if len(s["epa_conflict_examples"]) < 8:
                        s["epa_conflict_examples"].append(
                            {"vin": vin, "year": year, "model": model, "displ": displ, "epa_classes": sorted(cls)})

    # -----------------------------------------------------------------------
    # Rule records
    # -----------------------------------------------------------------------
    def val(rid: str) -> dict:
        s = stats[rid]
        ck = s["checkable"]
        pos = s["agree"] if rid.endswith("_manual") else 0
        return {
            "in_scope_lot_cars": s["in_scope_cars"],
            "checkable_ground_truth": ck,
            "agree": s["agree"],
            "disagree": s["disagree"],
            "agreement": round(s["agree"] / ck, 5) if ck else None,
            "checkable_positives_manual": pos if rid.endswith("_manual") else None,
            "uniform_cell_lines_excluded": s["uniform_cell_excluded"],
            "uniform_cell_lines_that_would_agree": s["uniform_cell_agree"],
            "ground_truth_speeds_only_excluded": s["gt_other_speeds_only"],
            "disagree_examples": s["disagree_examples"],
            "epa_crosscheck": dict(s["epa"]),
            "epa_conflict_examples": s["epa_conflict_examples"],
            "published_label_contradicts_rule": s["published_contradicts_rule"],
            "published_label_contradicts_examples": s["published_contradicts_examples"],
            "cars_without_trans_info": s["no_trans_info"],
            "cars_without_trans_info_by_reason": dict(s["no_trans_info_reason"]),
            "codes_seen": dict(s["codes"].most_common()),
            "top_models": dict(s["models"].most_common(12)),
            "years_seen": [min(s["years"]), max(s["years"])] if s["years"] else None,
            "feed_make_differs_from_wmi_brand": s["feed_make_mismatch"],
        }

    def status(rid: str, cite_is_mfr: bool = True) -> str:
        s = stats[rid]
        ck = s["checkable"]
        rate = s["agree"] / ck if ck else None
        if rate is not None and rate < 0.995:
            return "drop_or_narrow"
        if ck < 20:
            return "keep_low_sample" if cite_is_mfr else "drop_low_sample"
        return "keep"

    common_cond = [
        "VIN is 17 characters and its check digit (character 9) is valid (49 CFR 565.15(c)); VINs that fail it are skipped, not guessed",
        "model year from VIN character 10 (Honda year table in every filing); the listing/vPIC year only picks the 30-year cycle and must be within 2 years",
        "WMI (characters 1-3) is a Honda car/MPV/truck WMI from Honda's filings; motorcycle/ATV WMIs and the Isuzu-built 4S6 Passport / JAE SLX are excluded",
        "character-7 rules: characters 4-7 for that model year are a code NHTSA's vPIC decodes to a model (the VIN's own decode has a Model, or another lot car of that year with the same characters 4-7 does); codes vPIC does not know go to honda_acura_vin7_code_not_in_vpic_*",
    ]

    rules = []

    def add(rid, make, claim, years, wmis, vin_condition, regex, scope_note, cites, extra=None):
        r = {
            "id": rid,
            "make": make,
            "claim": claim,
            "status": status(rid),
            "scope": {
                "make": make,
                "models": scope_note,
                "model_years": years,
                "wmi": sorted(wmis),
                "conditions": common_cond,
            },
            "vin_condition": vin_condition,
            "vin_regex": regex,
            "citations": [{k: C[c][k] for k in ("url", "doc", "says")} for c in cites],
            "validation": val(rid),
            "newly_confirmed_manual": stats[rid]["no_trans_info"] if claim == "manual" else 0,
            "newly_labelled_non_manual": stats[rid]["no_trans_info"] if claim != "manual" else 0,
        }
        if extra:
            r.update(extra)
        rules.append(r)

    hw = "|".join(sorted(HONDA_WMI))
    aw = "|".join(sorted(ACURA_WMI))
    digit_cites_h = ["mid_1986_06_27", "mid_1986_07_18", "mid_1986_08_26", "mid_1996_07_01", "mid_2005_10_31"]
    digit_cites_a = ["mid_1985_11_19", "mid_1988_06_10", "mid_1996_07_01", "mid_2002_01_02"]
    letter_cites = ["mid_2009_08_24", "mid_2010_03_10", "mid_2023_07_21"]

    # Honda digit era
    for claim, vals in (("manual", "1357"), ("automatic", "2468")):
        add(f"honda_vin7_digit_1987_2009_{claim}", "Honda", claim, [1987, 2009], HONDA_WMI,
            {"position": 7, "values": list(vals),
             "table": {k: v[1] for k, v in DIGIT_T7.items() if k in vals},
             "exclusion": "MY1997 Accord (characters 4-5 CD or CE) is carved out into honda_accord_1997_vin7_*: vPIC decodes those VINs inverted, so the ground truth cannot validate them"},
            rf"^({hw})[A-HJ-NPR-Z0-9]{{3}}[{vals}][A-HJ-NPR-Z0-9]{{2}}[HJKLMNPRSTVWXY1-9]",
            "every Honda-brand passenger car, MPV and truck with a Honda WMI (Accord, Civic, CRX, del Sol, Prelude, S2000, Insight, Fit, CR-V, Element, Odyssey, Pilot, Ridgeline ...)",
            digit_cites_h)
    # Honda letter era
    for claim, vals in (("manual", "ACEG"), ("automatic", "BDFH")):
        add(f"honda_vin7_letter_2010_on_{claim}", "Honda", claim, [2010, None], HONDA_WMI,
            {"position": 7, "values": list(vals),
             "table": {k: v[1] for k, v in LETTER_T7.items() if k in vals}},
            rf"^({hw})[A-HJ-NPR-Z0-9]{{3}}[{vals}][A-HJ-NPR-Z0-9]{{2}}[A-HJ-NPR-TV-Y]",
            "every Honda-brand vehicle with a Honda WMI, MY2010 on (character 7 is a letter from MY2010)",
            letter_cites)
    # Acura digit era
    for claim, vals in (("manual", "1357"), ("automatic", "2468")):
        add(f"acura_vin7_digit_1986_2009_{claim}", "Acura", claim, [1986, 2009], ACURA_WMI,
            {"position": 7, "values": list(vals),
             "table": {k: v[1] for k, v in DIGIT_T7.items() if k in vals}},
            rf"^({aw})[A-HJ-NPR-Z0-9]{{3}}[{vals}][A-HJ-NPR-Z0-9]{{2}}[GHJKLMNPRSTVWXY1-9]",
            "every Acura (Integra, Legend, Vigor, CL, TL, RL, RSX, TSX, NSX, MDX, RDX, ZDX ...) with an Acura WMI",
            digit_cites_a)
    # Acura letter era
    for claim, vals in (("manual", "ACEG"), ("automatic", "BDFH")):
        add(f"acura_vin7_letter_2010_on_{claim}", "Acura", claim, [2010, None], ACURA_WMI,
            {"position": 7, "values": list(vals),
             "table": {k: v[1] for k, v in LETTER_T7.items() if k in vals}},
            rf"^({aw})[A-HJ-NPR-Z0-9]{{3}}[{vals}][A-HJ-NPR-Z0-9]{{2}}[A-HJ-NPR-TV-Y]",
            "every Acura with an Acura WMI, MY2010 on",
            letter_cites)
    # Honda MY1984-1986 (character 6)
    for claim, vals in (("manual", "456"), ("automatic", "37")):
        add(f"honda_vin6_1984_1986_{claim}", "Honda", claim, [1984, 1986], HONDA_WMI,
            {"position": 6, "values": list(vals),
             "table": {k: v[1] for k, v in OLD_T6.items() if k in vals},
             "also_required": "characters 4-5 are a line code the filing for that year lists (1984: AD AB AN; 1985: AD AB AN AF AG AH AK; 1986: AF AG AH AK BA AB BB AN AR VN) and character 7 is a body code 2-5"},
            rf"^({hw})(AD|AB|AN|AF|AG|AH|AK|BA|BB|AR|VN)[{vals}][2-5][A-HJ-NPR-Z0-9]{{2}}[EFG]",
            "MY1984-1986 Honda Accord, Prelude, Civic (CRX, hatchback, sedan, Wagon, Wagon 4WD, Wagovan): the pre-1987 Honda layout where character 6 is the transmission",
            ["mid_1983_09_12", "mid_1984_06_20", "mid_1985_06_12", "mid_1985_07_11", "mid_1985_11_19"])
    # Character-7 codes NHTSA's data does not list (Canada-market lines).
    for claim in ("manual", "automatic"):
        dvals, lvals = ("1357", "ACEG") if claim == "manual" else ("2468", "BDFH")
        add(f"honda_acura_vin7_code_not_in_vpic_{claim}", "Honda+Acura", claim, [1986, None], HONDA_WMI | ACURA_WMI,
            {"position": 7, "values": list(dvals) + list(lvals),
             "table": {**{k: v[1] for k, v in DIGIT_T7.items() if k in dvals},
                       **{k: v[1] for k, v in LETTER_T7.items() if k in lvals}},
             "also_required": "the VIN's vPIC decode has no Model AND no lot car of that model year with the same characters 4-7 decodes to a model, i.e. Honda never filed this code with NHTSA (on the lots: Canada-market Acura EL/CSX and a few Canada-only Civic codes)"},
            rf"^({hw}|{aw})[A-HJ-NPR-Z0-9]{{3}}[{dvals}{lvals}][A-HJ-NPR-Z0-9]{{2}}[A-HJ-NPR-TV-Y1-9]",
            "Honda/Acura VINs (mostly Canada-market cars at Canadian yards) whose model code is not in NHTSA's vPIC data",
            ["mid_1986_06_27", "mid_1985_11_19", "mid_2009_08_24"],
            {"caveat": ("Honda's construction-of-VIN pages define character 7 as body type + transmission for every "
                        "model code, and Honda of Canada Mfg. (2HG/2HH/2HK/2HN) is one of the filers, but no US "
                        "filing lists these exact Canada-market codes and vPIC returns no decode for them, so no "
                        "ground truth can check them. Kept as low_sample on the strength of Honda's own scheme; "
                        "the hub may prefer to hold these.")})

    # 1997 Accord carve-out
    for claim, vals in (("manual", "1357"), ("automatic", "2468")):
        rid = f"honda_accord_1997_vin7_{claim}"
        add(rid, "Honda", claim, [1997, 1997], HONDA_WMI,
            {"position": 7, "values": list(vals),
             "table": {k: v[1] for k, v in DIGIT_T7.items() if k in vals},
             "also_required": "characters 4-5 = CD or CE (1997 Accord coupe, sedan, V6 sedan, wagon)"},
            rf"^(1HG|JHM)(CD|CE)[A-HJ-NPR-Z0-9][{vals}][A-HJ-NPR-Z0-9]{{2}}V",
            "MY1997 Honda Accord only",
            ["mid_1996_07_01"],
            {"status": "vpic_conflict_hub_decision",
             "vpic_conflict": (
                 "vPIC returns the transmission INVERTED for MY1997 Accord sedans: CD553/CD555/CD556 "
                 "(Honda: 5MT) decode as 'Automatic' and CD560/CD563/CD565/CD566/CD568 and V6 CE664/CE667 "
                 "(Honda: 4AT) decode as 'Manual/Standard'. The same codes decode correctly for 1994-1996 "
                 "in the same cache. Independent check: EPA lists only 'Automatic 4-spd' for the 1997 Accord "
                 "2.7 V6 (vehicles.csv id 13472), yet vPIC labels every CE664/CE667 V6 on the lots manual. "
                 "Agreement against ground truth is therefore expected to be near 0 for the sedans; it "
                 "measures vPIC's error, not the rule. Applying this rule changes existing published labels, "
                 "so it needs a hub decision."),
             "epa_citation": {**EPA_CIT, "says": "1997 Honda Accord 2.7L 6-cyl: Automatic 4-spd only (id 13472); 2.2L: Automatic 4-spd and Manual 5-spd (ids 13468-13471)"}})

    # Final status for the main rules (the carve-out keeps its own status).
    by_id = {r["id"]: r for r in rules}

    # -----------------------------------------------------------------------
    # vPIC conflicts this research surfaced (published labels that the
    # manufacturer's own VIN table contradicts).
    # -----------------------------------------------------------------------
    conflicts = [
        {
            "cell": "2007-2008 Honda Fit, VIN characters 4-7 GD38 (GD384, GD386)",
            "honda_says": "5AT (character 7 = 8, 5-door automatic)",
            "vpic_says": "5-spd Manual/Standard for every Fit VIN of these years (baseline uniformCell = manual)",
            "evidence": [C["mid_2005_10_31"]["url"] + " (2007 Fit model codes: GD374/GD376 5MT, GD384/GD386 5AT)",
                         "EPA ids 22860-22862, 24920-24922: Fit 1.5 Automatic 5-spd, Automatic (S5), Manual 5-spd"],
            "effect_if_rule_applied": "Manual badge removed from GD38x Fits; GD37x Fits stay Manual, now on VIN evidence",
            "rule": "honda_vin7_digit_1987_2009_automatic / _manual",
        },
        {
            "cell": "1997 Honda Accord sedans (CD55x, CD56x, CE66x)",
            "honda_says": "CD55x = 5MT, CD56x = 4AT, CE66x (V6) = 4AT",
            "vpic_says": "inverted: CD55x 'Automatic', CD56x and CE66x 'Manual/Standard'",
            "evidence": [C["mid_1996_07_01"]["url"], "EPA id 13472: 1997 Accord 2.7 V6 Automatic 4-spd only"],
            "effect_if_rule_applied": "Manual badge removed from 1997 Accord automatics and V6s; added to the true 5MT sedans",
            "rule": "honda_accord_1997_vin7_manual / _automatic (status vpic_conflict_hub_decision)",
        },
        {
            "cell": "1989 Acura Integra, VIN characters 4-7 DA34 (DA344 = 3-door RS)",
            "honda_says": "DA344 = 4A (4-speed automatic)",
            "vpic_says": "5-spd Manual/Standard (1 lot car, JH4DA3448KS017664)",
            "evidence": [C["mid_1988_06_10"]["url"]],
            "effect_if_rule_applied": "Manual badge removed from that car",
            "rule": "acura_vin7_digit_1986_2009_automatic",
        },
    ]
    # Count the lot cars in each conflict cell from the per-rule examples.
    fit = {"GD38_published_manual": 0, "GD37_published_manual": 0}
    acc97 = Counter()
    for row in inv["vehicles"]:
        vin = (row[fi["vin"]] or "").strip().upper()
        if len(vin) != 17 or not check_digit_ok(vin):
            continue
        ex = list(extras.get(str(row[fi["id"]])) or []) + [""] * 5
        pc = tclass(ex[3])
        if vin[:3] == "JHM" and vin[3:6] == "GD3" and vin[9] in "78":
            if vin[6] == "8" and pc == "manual":
                fit["GD38_published_manual"] += 1
            if vin[6] == "7" and pc == "manual":
                fit["GD37_published_manual"] += 1
        if vin[:3] in ("1HG", "JHM") and vin[3:5] in ("CD", "CE") and vin[9] == "V":
            honda = DIGIT_T7.get(vin[6], ("?",))[0]
            if pc in KNOWN:
                acc97[f"honda_{honda}__published_{'manual' if pc == 'manual' else 'non_manual'}"] += 1
    conflicts[0]["lot_cars"] = fit
    conflicts[1]["lot_cars"] = dict(acc97)

    # -----------------------------------------------------------------------
    # Where the VIN does NOT encode the transmission
    # -----------------------------------------------------------------------
    not_encoded = [
        "Honda MY1981-1983: not ruled. The earliest Honda filings in NHTSA's MID are from August 1983 (MY1984). vPIC's decodes for the 7 MY1981-83 Hondas on the lots are consistent with the MY1984 layout (character 6 = transmission), but no Honda document for those years was found, so no rule covers them.",
        "Honda MY1984 Civic hatchback/CRX/sedan (line codes AF, AG, AH, AK): not ruled for 1984. The MY1984 filing in MID covers only Accord, Prelude and Civic Wagon; the Civic hatchback/sedan table for 1984 was not found (1985 and 1986 tables were).",
        "Honda Passport (1994-2002, WMI 4S6) and Acura SLX (1996-99, WMI JAE) are Isuzu-built and use Isuzu's VIN layout; Honda's character-7 code does not apply and no rule here covers them.",
        "Honda/Acura VINs whose character 7 is outside the table for the era (e.g. a letter on a 2001-2009 VIN or a digit on a 2010+ VIN) are not ruled; on the lots they are listing-year errors or mis-typed VINs.",
        "The code says manual vs automatic, not the gear count or the gearbox model; speeds stay with vPIC/EPA. Automatic codes cover CVT and DCT as well (e.g. 2015+ TLX 'F' = 8-speed DCT or 9-speed automatic).",
        "Cars without a VIN (Honda 2,699, Acura 426 on the lots) cannot be reached by these rules.",
    ]

    honda_on_lots = sum(1 for row in inv["vehicles"] if (row[fi["make"]] or "") == "Honda")
    acura_on_lots = sum(1 for row in inv["vehicles"] if (row[fi["make"]] or "") == "Acura")
    newly = sum(r["newly_confirmed_manual"] for r in rules if r["claim"] == "manual" and r["status"] in ("keep", "keep_low_sample"))
    newly_all = sum(r["newly_confirmed_manual"] for r in rules if r["claim"] == "manual")

    agg = {}
    for claim in ("manual", "automatic"):
        rs = [r for r in rules if r["claim"] == claim and r["status"] in ("keep", "keep_low_sample")]
        ck = sum(r["validation"]["checkable_ground_truth"] for r in rs)
        ag = sum(r["validation"]["agree"] for r in rs)
        agg[claim] = {"rules": [r["id"] for r in rs], "checkable": ck, "agree": ag,
                      "disagree": ck - ag, "agreement": round(ag / ck, 5) if ck else None,
                      "uniform_cell_lines_excluded": sum(r["validation"]["uniform_cell_lines_excluded"] for r in rs),
                      "uniform_cell_lines_that_would_agree": sum(r["validation"]["uniform_cell_lines_that_would_agree"] for r in rs)}

    out = {
        "worklist": "vin_rules_0",
        "makes": ["Honda", "Acura"],
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "generator": "scraper/manual_detect/vin_rules_0.py",
        "inputs": {
            "inventory_live": "docs/data/inventory_live.json",
            "vehicle_extras": "docs/data/vehicle_extras.json",
            "vin_decodes": "docs/data/vin_decodes.json.gz",
            "ground_truth": "scraper/manual_detect/ground_truth.jsonl (uniformCell lines treated as unlabelled)",
            "epa": "scraper/manual_detect/epa/vehicles.csv" if epa.ok else "missing (EPA cross-check skipped)",
        },
        "answer": {
            "honda": "VIN encodes it for every model year from 1984 on: character 6 for MY1984-1986, character 7 (odd digit = manual) for MY1987-2009, character 7 (A/C/E/G = manual) for MY2010 on.",
            "acura": "VIN encodes it for every model year (1986 on): character 7, odd digit = manual for MY1986-2009, A/C/E/G = manual for MY2010 on.",
            "vpic_already_decodes_it": "vPIC already turns this code into TransmissionStyle for almost every Honda/Acura VIN (Honda 21,026 and Acura 3,534 lot cars have a vPIC transmission), so the rules newly reach only the few cars where vPIC is blank or the VIN is not in the decode cache. Their larger value is correcting vPIC where it contradicts Honda's own table (vpic_conflicts).",
        },
        "summary": {
            "lot_cars_feed_make_honda": honda_on_lots,
            "lot_cars_feed_make_acura": acura_on_lots,
            "scan": dict(scan),
            "rules": len(rules),
            "newly_confirmed_manual_keep_and_low_sample_rules": newly,
            "newly_confirmed_manual_keep_rules_only": sum(r["newly_confirmed_manual"] for r in rules if r["claim"] == "manual" and r["status"] == "keep"),
            "newly_confirmed_manual_low_sample_rules_only": sum(r["newly_confirmed_manual"] for r in rules if r["claim"] == "manual" and r["status"] == "keep_low_sample"),
            "newly_confirmed_manual_all_rules": newly_all,
            "newly_confirmed_manual_by_rule": {r["id"]: r["newly_confirmed_manual"] for r in rules if r["claim"] == "manual"},
            "ground_truth_agreement_keep_rules": agg,
            "published_manual_labels_contradicted_by_honda_table": {
                "2007_2008_fit_gd38": fit["GD38_published_manual"],
                "1997_accord_honda_automatic": acc97.get("honda_automatic__published_manual", 0),
                "1989_integra_da344": stats["acura_vin7_digit_1986_2009_automatic"]["published_contradicts_rule"],
            },
            "published_non_manual_labels_contradicted_by_honda_table": {
                "1997_accord_honda_manual": acc97.get("honda_manual__published_non_manual", 0),
            },
        },
        "vin_scheme": {
            "positions": "1-3 WMI; 4-8 Honda 'model code' (4-5 line, 6 line/engine, 7 body + transmission, 8 grade); 9 check digit; 10 model year; 11 plant; 12-17 serial",
            "char7_digit_MY1987_2009_Honda_MY1986_2009_Acura": {k: v[1] for k, v in DIGIT_T7.items()},
            "char7_letter_MY2010_on": {k: v[1] for k, v in LETTER_T7.items()},
            "char6_MY1984_1986_Honda": {k: v[1] for k, v in OLD_T6.items()},
            "char7_body_MY1984_1986_Honda": {"2": "2-door sedan", "3": "2-door hatchback or coupe", "4": "4-door sedan", "5": "4-door wagon"},
        },
        "vin_regex_note": ("Each rule's vin_regex checks the WMI, the transmission character and the character-10 year code. "
                           "Character 10 letters repeat every 30 years (A = 1980 or 2010), so the model year is resolved "
                           "with the listing/vPIC year (scope.model_years); the check digit is verified separately; the "
                           "'not in vPIC' split and the 1997 Accord carve-out need the extra conditions stated in the rule."),
        "not_encoded_or_not_ruled": not_encoded,
        "rules": rules,
        "newly_confirmed_manual_cars": newly_cars,
        "vpic_conflicts": conflicts,
        "validation_method": (
            "For each rule, every lot car in scope is matched by WMI, valid check digit, VIN model year and the "
            "character-6/7 value. 'checkable' = its ground_truth.jsonl line has class manual/automatic/cvt/amt/dct "
            "and uniformCell is empty (uniform-cell lines are vPIC model-level defaults and are counted separately "
            "as unlabelled). Agreement = same manual-vs-not-manual answer. All VIN-bearing ground truth comes from "
            "vPIC, which NHTSA builds from these same Honda filings, so agreement is partly circular; the EPA "
            "cross-check (does EPA list a transmission of the claimed kind for that year/make/model, narrowed to the "
            "vPIC displacement when known) is the independent check. 'newly_confirmed_manual' = in-scope cars whose "
            "published extras transmission is empty today."),
    }
    OUT.write_text(json.dumps(out, indent=1, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)) + "\n")
    print(json.dumps(out["summary"], indent=1))
    for r in rules:
        v = r["validation"]
        print(f'{r["id"]:45s} {r["status"]:28s} scope={v["in_scope_lot_cars"]:6d} chk={v["checkable_ground_truth"]:6d} '
              f'agree={v["agreement"]} dis={v["disagree"]} uni={v["uniform_cell_lines_excluded"]} '
              f'epa={v["epa_crosscheck"]} new={r["newly_confirmed_manual"]} newA={r["newly_labelled_non_manual"]} '
              f'contra={v["published_label_contradicts_rule"]}')
    _ = by_id
    return 0


if __name__ == "__main__":
    sys.exit(main())
