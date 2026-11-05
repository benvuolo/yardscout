#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 2: Toyota, Lexus, Scion,
Nissan, Infiniti.

What the manufacturers' own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say, read filing by filing:

  * Toyota / Lexus / Scion: NO transmission character in any filing read
    (MY1991 Toyota+Lexus, MY2000 Corolla/Solara, MY2003 Corolla/Matrix,
    MY2004 Toyota/Lexus/Scion, MY2005 Corolla/Matrix/Tacoma/Sienna/Sequoia/
    Tundra). Passenger cars: 4 engine, 5 line, 6 model, 7 series (grade),
    8 body + restraint (pre-2000 layout); 4 body/cab + drive, 5 engine,
    6 series, 7 restraint or grade, 8 line (2000 on). Trucks: engine,
    line, drive, cab, series/brake/GVWR.
    The engine character (or, before 2000, the grade digit) does pick out a
    few engines that were sold in the US with a manual gearbox only:
    MR2 Turbo 3S-GTE (MY1991-95), Corolla XRS 2ZZ-GE (MY2005-06), Matrix
    XRS 2ZZ-GE (MY2004-06; MY2003 also had an automatic), Celica All-Trac
    Turbo 3S-GTE (candidate), Tacoma 2TR-FE 4x4 MY2005-10 and T100 3RZ-FE
    4x2 MY1994 (candidates: EPA only, sources conflict or are silent).
  * Nissan / Infiniti: NO transmission character in any filing read
    (MY1985, 1990, 1998, 2002, 2013, 2025). Position 4 is the engine,
    position 8 the restraint system or GVWR/brake/drive (S = 2WD, Y = 4WD
    on trucks). Manual-only engine + drive cells: Xterra 2.4L KA24DE
    (MY2000-04, 2WD only), Frontier 2.4L 4WD (MY1998 only after the
    2026-11-05 verification: MY1999-2000 have a published automatic); the 1984-97
    Nissan pickup 2.4L 4WD is a candidate (EPA only).

Scion FR-S / Toyota 86 / GR86 (WMI JF1, Subaru-built) follow Subaru's
scheme and are ruled in vin_rules_1 (character 11), not here. Scion iA
(3MY, Mazda-built) follows Mazda's scheme (no transmission character).

Every rule is validated against ground_truth.jsonl (uniformCell lines are
treated as unlabelled), cross-checked against the EPA cell it relies on,
cross-checked against a live vPIC decode of each in-scope VIN (engine model
and drive; saved in vin_rules_2_vpic.json so the run is offline), and counted
for the lot cars WITHOUT transmission info it would newly confirm. Cars at
Canadian yards are counted but NOT newly confirmed: every manual-only claim
here rests on what was sold in the US market (EPA), and Canadian-market
offerings can differ.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (EPA cross-check),
        scraper/manual_detect/vin_rules_2_vpic.json (live vPIC decodes, 2026-11-05).
Output: scraper/manual_detect/vin_rules_2.json

Run:  python3 -I scraper/manual_detect/vin_rules_2.py
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

OUT = HERE / "vin_rules_2.json"
VPIC_FILE = HERE / "vin_rules_2_vpic.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
CANADA = {"AB", "BC", "MB", "NB", "NL", "NS", "ON", "PE", "QC", "SK"}

# ---------------------------------------------------------------------------
# VIN helpers (same as vin_rules_1)
# ---------------------------------------------------------------------------
_TRANSLIT = {**{str(i): i for i in range(10)},
             **dict(zip("ABCDEFGH", range(1, 9))), **dict(zip("JKLMN", range(1, 6))),
             "P": 7, "R": 9, **dict(zip("STUVWXYZ", range(2, 10)))}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"   # 1980..2009, then repeats


def check_digit_ok(vin: str) -> bool:
    if len(vin) != 17 or any(ch not in _TRANSLIT for ch in vin):
        return False
    s = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS))
    r = s % 11
    return vin[8] == ("X" if r == 10 else str(r))


def vin_year(vin: str, hint) -> int | None:
    """Model year from character 10; the listing year only picks the 30-year
    cycle and must be within 2 years, else None (VIN and listing disagree)."""
    i = _YEAR_CODES.find(vin[9])
    if i < 0:
        return None
    cands = [1980 + i] + ([2010 + i] if i < 21 else [])
    if not hint:
        return cands[0] if len(cands) == 1 else None
    best = min(cands, key=lambda y: abs(y - hint))
    return best if abs(best - hint) <= 2 else None


def year_chars(lo: int, hi: int) -> str:
    out = []
    for y in range(lo, hi + 1):
        c = _YEAR_CODES[(y - 1980) % 30]
        if c not in out:
            out.append(c)
    return "".join(out)


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


def epa_tclass(trany: str) -> str:
    t = (trany or "").lower()
    if t.startswith("manual"):
        return "manual"
    if "(av" in t or "variable" in t:
        return "cvt"
    if "(am" in t:
        return "amt"
    if t.startswith("auto"):
        return "automatic"
    return "other"


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------
def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


def web(url: str, doc: str, says: str) -> dict:
    return {"url": url, "doc": doc, "says": says}


C = {
    # --- Toyota / Lexus / Scion filings ------------------------------------
    "toy_1991": mid("f666efc7-e181-41ad-badf-f9468b8718c6",
                    "NHTSA 01-22-N11B-3801, Toyota Motor Corporate Services of North America letter 1990-07-27, 'Toyota and Lexus VIN Coding System applicable to 1991 models' (19 pp.)",
                    "Passenger-car VDS: 1st digit (VIN 4) engine type, 2nd (VIN 5) line, 3rd (VIN 6) model designation, 4th (VIN 7) series (grade), 5th (VIN 8) body type & restraint system. MR2: engine S (3S-GTE / 5S-FE), line W, model 2 (SW20L, SW21L), body M/N; Note #4: 'As for MR2, engine types are identified as follows: 3S-GTE = VDS 1st digit S, 4th digit 2; 5S-FE = S, 1'. Celica: line T, model 8 (AT180L, ST184L, ST185L), grade 5 GT-S / 6 ST / 7 GT / 8 'turbo All-Trac', body F 2DR CP 2WD, N 3DR LB 2WD, P 3DR LB 4WD; Note #3: '3S-GTE = S, 8; 5S-FE = S, 5 or 7'. Truck VDS: engine (R 22R-E, V 3VZ-E), line N, drive train type (8/9 = 4x2, 0/1 = 4x4), cab type & chassis, series & brake systems / GVWR. MPV (4Runner, Land Cruiser, Previa) and Lexus LS400/ES250: same layout. No position carries the transmission."),
    "toy_2000": mid("fa97a11b-6ac2-4784-a6ff-81b51c6169a7",
                    "NHTSA 01-22-N11B-7440, Toyota Technical Center USA letter 1999-10-26, VIN coding system for 2000 Toyota Corolla & Camry Solara (TMMC)",
                    "4th digit body type (B 4-door sedan 2WD; C 2-door coupe, F convertible), 5th engine type (R 1ZZ-FE; G 5S-FE, F 1MZ-FE), 6th series (ZZE110L, SXV20L, MCV20L), 7th restraint system type, 8th line (E Corolla, P Camry Solara). No transmission character."),
    "toy_2003": mid("0fb58d67-2158-4d38-81ea-aa8412e42f7f",
                    "NHTSA 01-022-N11B-8516, Toyota Motor North America letter 2001-11-28, VIN coding system for 2003 Toyota Corolla (NUMMI, TMMC) and Corolla Matrix (TMMC)",
                    "Corolla Matrix VDS: 4th digit body type K = 5 door small station wagon 2WD, L = 4WD; 5th digit engine type R = 1ZZ-FE, Y = 2ZZ-GE; 6th series 3 (ZZE132L/133L/134L); 7th restraint system; 8th line E = Corolla Matrix. No transmission character."),
    "toy_2004": mid("09aff477-0478-4482-b0f5-43de01fd5794",
                    "NHTSA 01-022-N11B-9265, Toyota Motor North America letter 2002-11-25, VIN coding system for 2004 Toyota, Lexus and Scion vehicles (incl. TMMC Corolla, Corolla Matrix, Lexus RX330; Scion xA/xB)",
                    "2004 Corolla Matrix VDS: 4th body K = 5 door hatchback 2WD, L = 4WD; 5th engine R = 1ZZ-FE, Y = 2ZZ-GE; 6th series 3; 7th restraint 2/8; 8th line E. 2004 Corolla (TMMC): 4th B, 5th R = 1ZZ-FE only. No transmission character for any Toyota, Lexus or Scion line in the filing."),
    "toy_2005": mid("9ffcb615-f3c4-42a8-9a39-399f04795814",
                    "NHTSA 01-022-N11B-9892, Toyota Motor North America letter 2004-05-13, VIN coding system for 2005 Toyota and Lexus vehicles (TMMC Corolla, Corolla Matrix, RX330; TMMCA Tacoma; TMMI Sienna, Sequoia, Tundra) (11 pp.)",
                    "2005 Corolla (TMMC, WMI 2T1): 4th digit body B = 4 door sedan 2WD; 5th digit engine type R = 1ZZ-FE, Y = 2ZZ-GE; 6th series 3 (ZZE130L, ZZE131L); 7th restraint 2/0; 8th line E. 2005 Corolla Matrix: K/L body, R/Y engine. 2005 Tacoma (5TE): 4th 'Cab, Chassis, Drive Train & Brake System Type' N Regular Cab short WB 2WD, T Xtra Cab long WB 2WD, J Double Cab long WB 2WD, K Double Cab super long WB 2WD, P Regular Cab short WB 4WD, U Xtra Cab long WB 4WD, L Double Cab long WB 4WD, M Double Cab super long WB 4WD; 5th engine X = 2TR-FE, U = 1GR-FE; 6th series; 7th grade; 8th line N Tacoma. No transmission character."),
    # --- Nissan / Infiniti filings ------------------------------------------
    "nis_1985": mid("05513c5e-b97d-47a0-a708-a799a23929b9",
                    "NHTSA 01-22-N11B-1690, Nissan Research & Development letter 1984-08-28, 'Information for Nissan VIN coding system, 1985 year models' (10 pp.)",
                    "Section 2 (digits 4-8) Vehicle Description: 'Engine Type, Line, Model Change, Body Type, Restraint System, GVWR, Brake System, etc.' Digit 4 engine type (e.g. Sentra P 1.6L gasoline, S 1.7L diesel; 300ZX H 3.0L, C 3.0L turbo), digit 5 vehicle line. No transmission character."),
    "nis_1990": mid("cf757d20-f93c-4e38-9e67-9b1e31741e5c",
                    "NHTSA 01-22-N11B-3587, Nissan Motor Co. 1989-11-22, Nissan VIN coding system (passenger car), MY1990",
                    "Position 4 engine type, 5 vehicle line, 6 model change, 7 body type, 8 restraint system (S standard 2WD, Y standard 4WD, C air cushion, A 3-point automatic belt, P/J motorized 2-point belt, B 2-point automatic belt). Covers Sentra, Pulsar NX, 240SX, Maxima, Stanza, 300ZX, Axxess, Infiniti Q45/M30. No transmission character."),
    "nis_1998": mid("8a102da6-82f2-49d5-84d3-c1434fc90747",
                    "NHTSA 01-22-N11B-6349, Nissan North America letter 1997-04-28, VIN deciphering information for MY1998 Nissan and Infiniti",
                    "Letter: 'Truck VIN Coding Chart Revisions: (1) Revision of Engine Type code from \"S\" to \"D\" (position #4), revision of Line/Series designation from \"Nissan Truck\" to \"Nissan Frontier Truck\" ... addition of Chassis Brake System designation \"4-Wheel ABS (2WD)\" and Code \"T\" (position #8)'. Truck chart: position 4 2.4L gasoline = D; position 5 Nissan Frontier Truck = D; position 7 Regular Cab 1, King Cab 6; position 8 GVWR / chassis-brake: Class C Rear ABS (2WD) S, 4-Wheel ABS (2WD) T, Class D Standard (4WD) Y. No transmission character."),
    "nis_2001": mid("1d224522-3841-405e-919c-06ad20757cd7",
                    "NHTSA 01-022-N11B-7821, Nissan North America letter 2000-07-07, MY2001 Nissan VIN coding system (light-duty trucks, revised)",
                    "MPV/truck chart for MY2001 (Pathfinder, QX4, Xterra, Frontier): position 4 engine type, 5 line/series, 7 body type, 8 GVWR / chassis-brake system. No transmission character."),
    "nis_2002": mid("00371e3b-454c-49da-ba8c-aa85eda874cf",
                    "NHTSA 01-022-N11B-8061, Nissan North America letter 2000-11-28, MY2002 Nissan VIN coding system (passenger car; MPV and truck)",
                    "MPV/truck chart: Xterra position 4 engine 2.4L gasoline = D, 3.3L gasoline = E; position 5 Xterra = D; position 7 4-door wagon = 8; position 8 Class C 4-wheel ABS (2WD) S, Class D Standard (4WD) Y. Frontier: 2.4L D, 3.3L E, 3.3L supercharged M; line D; Regular Cab 1, King Cab 6, Crew Cab 7; position 8 Class C rear ABS (2WD) S / 4-wheel ABS (2WD) T, Class D Standard (4WD) Y. Passenger-car chart: position 8 = restraint system. No transmission character."),
    "nis_2013": mid("14dd2f5b-10a2-45d0-8107-0e5b51ead1fa",
                    "MID ORG7767, Nissan North America filing 2012-05-14, 'MY13 Nissan VIN Coding System [Passenger Car]'",
                    "Position 4 engine type, 5 line/series (GT-R, Infiniti M, G37, 370Z, Altima ...), 6 model change, 7 body type, 8 restraint system + 2WD/4WD, 10 model year, 11 plant. No transmission character."),
    "nis_2025": mid("78f9a1e7-b33f-4550-b06c-a0b00b19a85f",
                    "MID ORG23829, Nissan North America filing 2024-12-04 (MY2025 Nissan/Infiniti)",
                    "Column headings: 4th digit Engine Type, 5th Line/Series, 6th/7th Body Type, 8th Restraint System (cars) or GVWR / Brake System / Chassis / Restraint System (MPV, trucks), 9th check digit, 10th model year, 11th plant. The word 'transmission' does not occur in the filing."),
    # --- vPIC (NHTSA, built from these filings) -----------------------------
    "vpic_live": web("https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/",
                     "NHTSA vPIC live decodes, 2026-11-05 (saved in scraper/manual_detect/vin_rules_2_vpic.json: every in-scope lot VIN plus partial-VIN pattern decodes per code and model year)",
                     "Engine model / displacement / drive per code and year: see each rule's vpic_check."),
    # --- EPA -------------------------------------------------------------
    "epa": web(EPA_URL, "EPA fueleconomy.gov vehicles.csv (downloaded 2026-11-05, Last-Modified 2026-09-29)",
               "Every certified US configuration; rule-specific rows listed in epa_ids and re-checked by this script (epa_cell)."),
    # --- Independent references (search-result excerpts; the pages themselves
    #     could not be fetched from this session: wikipedia.org, edmunds.com,
    #     consumerguide.com and media.toyota.ca are outside its network allowlist)
    "ref_corolla_xrs": web("https://www.theautochannel.com/news/2004/10/28/266529.html",
                           "The Auto Channel, '2005 Car Review: Toyota Corolla XRS' (also auto123.com 2004 Corolla XRS preview); search-result excerpts, 2026-11-05",
                           "The 130-hp Corollas come with a five-speed manual or four-speed automatic; the XRS (2ZZ-GE, 170 hp) is available only with a six-speed manual gearbox."),
    "ref_matrix_xrs": web("https://en.wikipedia.org/wiki/Toyota_Matrix",
                          "Wikipedia 'Toyota Matrix' (and curbsideclassic.com 'COAL: 2003 Toyota Matrix XRS'); search-result excerpts, 2026-11-05",
                          "'With the exception of an available automatic in 2003, a six-speed manual transmission was the only gearbox offered in the XRS'; the XRS automatic was seldom ordered and dropped after 2003."),
    "ref_mr2_turbo": web("https://www.slashgear.com/1697726/toyota-sw20-mr2-what-engine-current-price",
                         "SlashGear on the SW20 MR2; CarGurus 1995 MR2; classic.com listing of a 1995 MR2 Turbo VIN JT2SW22N2S0102679; search-result excerpts, 2026-11-05",
                         "MR2 Turbo models were equipped exclusively with a five-speed manual (E153); naturally aspirated versions could be had with a four-speed automatic or five-speed manual. US market MY1991-1995. A 1995 MR2 Turbo carries JT2SW22N."),
    "ref_xterra": web("https://www2020.theautochannel.com/news/press/date/19990104/press002061.html",
                      "Nissan's 1999 Xterra announcement (Auto Channel reprint), Consumer Guide 2000-04 Xterra, Edmunds 2000 Xterra review, Cars.com 2000 'what's new'; search-result excerpts, 2026-11-05",
                      "The base XE's 2.4-liter 143-hp four-cylinder is paired only with a 5-speed manual and is offered only with two-wheel drive; the V6 is available in 2WD or 4WD with manual or automatic."),
    "ref_frontier": web("https://consumerguide.com/used/1998-04-nissan-frontier/",
                        "Consumer Guide, used 1998-2004 Nissan Frontier; search-result excerpt, 2026-11-05",
                        "All Frontiers offered either a manual or automatic transmission, except for 4-cylinder 4x4s, which were manual-shift only."),
    "ref_tacoma_conflict": web("https://www.cars.com/articles/2005-toyota-tacoma-whats-new-1420685445813",
                               "Cars.com 2005 Tacoma 'what's new', Edmunds 2005 Tacoma review, auto123 2005 Tacoma test, autotrader.ca 2008/2009 Tacoma research; search-result excerpts, 2026-11-05",
                               "The four-cylinder came with a five-speed manual or four-speed automatic (not split by 2WD/4WD). Canadian sources: 4x4 Tacomas were V6-only until a four-cylinder 4x4 Access Cab arrived for 2009 with a five-speed manual and no automatic. Conflicting and not US-specific, so the 2005-10 4x4 2.7 rule stays a candidate."),
    "ref_hardbody_none": web("https://www.cargurus.com/research/1997-Nissan-Pickup-c3044",
                             "Search for an independent statement on 1985-97 Nissan pickup 4-cylinder 4x4 transmissions, 2026-11-05",
                             "No manufacturer or review source found. One owner comment (CarGurus) says the 1997 4-cylinder 4x4 came only with a 5-speed; content-farm buying guides say the automatic was offered 'with both engines'. EPA alone supports manual-only, so the rule stays a candidate."),
    "ref_celica_alltrac": web("https://en.wikipedia.org/wiki/Toyota_Celica_GT-Four",
                              "Wikipedia 'Toyota Celica GT-Four'; search-result excerpt, 2026-11-05",
                              "The GT-Four was sold in the US as the All-Trac Turbo; the E150F manual transaxle was installed in the Japanese market and All-Trac cars. No source found that states the US All-Trac Turbo had no automatic; EPA lists only a 5-speed manual for every year."),
    # --- Added by the adversarial verification pass, 2026-11-05 (pages read directly) ---
    "tca_matrix": web("https://media.toyota.ca/content/dam/media-toyota/general/specifications/04matrix_specsfeat_e.pdf",
                      "Toyota Canada 2004, 2005 and 2006 Matrix specification sheets (04matrix_specsfeat_e.pdf, 05matrix_specs_e.pdf, 06matrix_specs_e.pdf; reached from media.toyota.ca/en/specifications/<year>/<year>-matrix-specifications.html), read 2026-11-05",
                      "Columns BASE FWD, XR FWD, XRS FWD, BASE 4WD, XR 4WD. Transmission row: XRS FWD is marked only for '6-Speed, Manual, Close Ratio, Overdrive'; '4-Speed, Automatic, Overdrive, Lock-Up Torque Converter, ECT' is marked for Base/XR FWD and both 4WD columns. Curb-weight and fuel-consumption tables list XRS under Manual only. The XRS engine is the VVTL-i 1.8 (180 hp in 2004)."),
    "wiki_matrix_direct": web("https://en.wikipedia.org/wiki/Toyota_Matrix",
                              "Wikipedia 'Toyota Matrix', page read directly 2026-11-05",
                              "Infobox: '4-speed U240E automatic transmission (FWD XRS available in the 2003 only)'. Text: 'With the exception of an available automatic in 2003, a six-speed manual transmission was the only gearbox offered in the XRS.'"),
    "wiki_corolla_e120": web("https://en.wikipedia.org/wiki/Toyota_Corolla_(E120)",
                             "Wikipedia 'Toyota Corolla (E120)', page read directly 2026-11-05",
                             "'a sporty XRS model (ZZE131), introduced in 2004 between the 2005 and 2006 model years only, featured the high-revving ... 2ZZ-GE engine and 6-speed manual'; 'The close ratio C60 6-speed manual transmission (also found in the Toyota Matrix XRS) was the only transmission available.'; 'The Corolla XRS was on sale in the United States, Canada, and Puerto Rico.'"),
    "wiki_mr2": web("https://en.wikipedia.org/wiki/Toyota_MR2",
                    "Wikipedia 'Toyota MR2', page read directly 2026-11-05",
                    "'US market trim levels: MR2 with a NA 2.2L 5S-FE engine ... offered with a four-speed A/T or five-speed M/T. MR2 Turbo with a turbocharged 2.0L 3S-GTE engine ... offered only with a 5-speed M/T'."),
    "cg_xterra_direct": web("https://consumerguide.com/used/2000-04-nissan-xterra/",
                            "Consumer Guide, used 2000-04 Nissan Xterra, page read directly 2026-11-05",
                            "'The Xterra lineup began with a base XE model, with a 4-cylinder engine, manual transmission, and 2-wheel drive.' 'Base XE editions held a 2.4-liter 4-cylinder engine that developed 143 horsepower, teamed only with a 5-speed manual transmission. ... Only 2-wheel drive was available with the base XE'. Every yearly price list gives XE standard equipment as '2.4-liter dohc 4-cylinder engine, 5-speed manual transmission'; the options table marks the automatic 'NA XE 4-cylinder'."),
    "cg_frontier_direct": web("https://consumerguide.com/used/1998-04-nissan-frontier/",
                              "Consumer Guide, used 1998-04 Nissan Frontier, page read directly 2026-11-05",
                              "1998: 'Two-wheel-drive Frontiers came with a 5-speed manual or optional 4-speed automatic transmission, but initial 4x4s were manual-shift only.' 1999: 'All Frontiers offered either a manual or automatic transmission, except for 4-cylinder 4x4s, which were manual-shift only.' 2000 price list: the only 4-cylinder 4WD line is 'XE 4WD King Cab extended cab, 5-Speed'; '4WD adds: ... 5-speed manual transmission'."),
}

# ---------------------------------------------------------------------------
# Rules. `fixed` = VIN characters that must match (scope); `pos` = the coded
# character; `codes` = {value: (claim, meaning, (first MY, last MY))}.
# `epa_cell` = the EPA rows the manual-only claim rests on (make, model regex,
# displ, drive 2/4, eng_dscr regex or None), checked per model year.
# `vpic_expect` = what a live vPIC decode of an in-scope VIN must show.
# ---------------------------------------------------------------------------
M, A = "manual", "automatic"

RULES = [
    # ---------------- Toyota ----------------------------------------------
    dict(id="toyota_mr2_turbo_3sgte_1991_1995", make="Toyota", wmi=["JT2"], years=(1991, 1995),
         fixed={4: "S", 5: "W", 6: "2"}, pos=7,
         codes={"2": (M, "3S-GTE 2.0L turbo (MR2 Turbo): US 5-speed manual only", (1991, 1995))},
         not_ruled_codes={"1": "5S-FE 2.2L (MR2 base): 5-speed manual or 4-speed automatic"},
         models="Toyota MR2 (SW20/SW21), MY1991-1995 (VIN JT2SW22*)",
         cites=["toy_1991", "vpic_live", "ref_mr2_turbo", "wiki_mr2", "epa"],
         epa_cell=dict(make="Toyota", model=r"^MR2$", displ="2.0", drive="2", dscr=r"TRBO"),
         epa_ids=["7494 (1991)", "8591 (1992)", "9665 (1993)", "10650 (1994)", "11612 (1995): MR2 2.0 turbo, Manual 5-spd, the only turbo rows; the 2.2 (5S-FE) rows list Automatic 4-spd and Manual 5-spd"],
         vpic_expect=dict(engine=r"3S", displ="2.0"),
         evidence_gaps="Code read in the MY1991 filing; MY1992-1995 rest on vPIC (JT2SW22N decodes to 3S 2.0L turbo for every year 1991-1995) and a 1995 MR2 Turbo VIN (JT2SW22N2S0102679)."),
    dict(id="toyota_corolla_xrs_2zzge_2005_2006", make="Toyota", wmi=["2T1"], years=(2005, 2006),
         fixed={4: "B", 6: "3", 8: "E"}, pos=5,
         codes={"Y": (M, "2ZZ-GE 1.8L (Corolla XRS): 6-speed manual only", (2005, 2006))},
         not_ruled_codes={"R": "1ZZ-FE 1.8L: 5-speed manual or 4-speed automatic"},
         models="Toyota Corolla XRS sedan built by TMMC (WMI 2T1, VIN 2T1BY3*E), MY2005-2006",
         cites=["toy_2005", "vpic_live", "ref_corolla_xrs", "wiki_corolla_e120", "epa"],
         epa_cell=dict(make="Toyota", model=r"^Corolla$", displ="1.8", drive="2", dscr=r"SPORTS"),
         epa_ids=["20798 (2005 Corolla 1.8 'SPORTS' Manual 6-spd)", "21883 (2006 Corolla 1.8 'SPORTS' Manual 6-spd): the only 2ZZ-GE Corolla rows; 1ZZ-FE rows 20796/20797, 21881/21882 list Automatic 4-spd and Manual 5-spd"],
         vpic_expect=dict(engine=r"2ZZ", displ="1.8"),
         evidence_gaps="MY2005 code read in the TMMC filing; MY2006 rests on vPIC (2T1BY32E decodes to 2ZZ-GE for 2005 and 2006)."),
    dict(id="toyota_matrix_xrs_2zzge_2004_2006", make="Toyota", wmi=["2T1"], years=(2004, 2006),
         fixed={4: "K", 6: "3", 8: "E"}, pos=5,
         codes={"Y": (M, "2ZZ-GE 1.8L (Matrix XRS, 2WD): 6-speed manual only from MY2004", (2004, 2006))},
         not_ruled_codes={"R": "1ZZ-FE 1.8L: 5-speed manual or 4-speed automatic",
                          "Y (MY2003)": "2ZZ-GE 1.8L in MY2003: 6-speed manual OR 4-speed automatic (EPA 18789, 18791), so MY2003 is out of scope"},
         models="Toyota (Corolla) Matrix XRS, TMMC (WMI 2T1, VIN 2T1KY3*E), MY2004-2006",
         cites=["toy_2004", "toy_2005", "toy_2003", "vpic_live", "ref_matrix_xrs", "wiki_matrix_direct", "tca_matrix", "epa"],
         epa_cell=dict(make="Toyota", model=r"^Matrix$", displ="1.8", drive="2", dscr=r"SPORTS"),
         epa_ids=["19900 (2004)", "21032 (2005)", "22126 (2006): Matrix 1.8 'SPORTS' Manual 6-spd only", "2003 for contrast: 18789 Automatic 4-spd and 18791 Manual 6-spd"],
         vpic_expect=dict(engine=r"2ZZ", displ="1.8"),
         evidence_gaps="MY2004 and MY2005 codes read in the TMMC filings; MY2006 rests on vPIC (2T1KY32E decodes to 2ZZ-GE for 2005 and 2006)."),
    dict(id="toyota_celica_alltrac_turbo_1990_1993", make="Toyota", wmi=["JT2"], years=(1990, 1993),
         fixed={4: "S", 5: "T", 6: "8"}, pos=7, candidate=True,
         codes={"8": (M, "Grade 8 = 'turbo All-Trac' (3S-GTE, ST185): 5-speed manual per EPA", (1990, 1993))},
         not_ruled_codes={"5": "GT-S (5S-FE)", "6": "ST", "7": "GT (5S-FE)"},
         models="Toyota Celica All-Trac Turbo (JT2ST88P*), MY1990-1993",
         candidate_reason="Manual-only rests on EPA alone (one row per year, Manual 5-spd); no manufacturer or review statement that the US All-Trac Turbo had no automatic was found. No lot car is in scope.",
         cites=["toy_1991", "vpic_live", "ref_celica_alltrac", "epa"],
         epa_cell=dict(make="Toyota", model=r"^Celica$", displ="2.0", drive="4", dscr=r"TRBO"),
         epa_ids=["6614 (1990)", "7720 (1991)", "8810 (1992)", "9868 (1993): Celica 2.0 turbo 4WD Manual 5-spd only"],
         vpic_expect=dict(engine=r"3S", displ="2.0"),
         evidence_gaps="MY1988-1989 ST165 All-Trac is not ruled: the MY1988/1989 filings were not read."),
    dict(id="toyota_tacoma_2trfe_4wd_2005_2010", make="Toyota", wmi=["5TE", "3TM"], years=(2005, 2010),
         fixed={4: "PU", 5: "X"}, pos=4, candidate=True,
         codes={"P": (M, "Regular Cab 4WD with 2TR-FE 2.7L: EPA lists Manual 5-spd only for MY2005-2010", (2005, 2010)),
                "U": (M, "Xtra (Access) Cab 4WD with 2TR-FE 2.7L: EPA lists Manual 5-spd only for MY2005-2010", (2005, 2010))},
         not_ruled_codes={"N/T (2WD) + X": "2.7L 2WD: Manual 5-spd or Automatic 4-spd", "any + U": "1GR-FE 4.0L V6: 6MT or 5AT"},
         models="Toyota Tacoma 2.7L 4x4 Regular/Access Cab (5TEPX4*, 5TEUX4*), MY2005-2010",
         candidate_reason="EPA lists only 'Tacoma 4WD 2.7 Manual 5-spd' for 2005-2010 (both from 2011), but reviews say the four-cylinder came with either gearbox (not split by drive) and Canadian sources say no 4-cylinder 4x4 existed before 2009. Not certain enough for a badge.",
         cites=["toy_2005", "vpic_live", "ref_tacoma_conflict", "epa"],
         epa_cell=dict(make="Toyota", model=r"^Tacoma 4WD$", displ="2.7", drive="4", dscr=None),
         epa_ids=["21184 (2005)", "22293 (2006)", "23692 (2007)", "24940 (2008)", "25572 (2009)", "29526 (2010): Tacoma 4WD 2.7 Manual 5-spd only", "2011 for contrast: 30449 Automatic 4-spd, 30450 Manual 5-spd"],
         vpic_expect=dict(engine=r"2TR", displ="2.7"),
         evidence_gaps="MY2005 code table read; MY2006-2010 rest on vPIC."),
    dict(id="toyota_t100_3rzfe_2wd_1994", make="Toyota", wmi=["JT4"], years=(1994, 1994),
         fixed={4: "U", 5: "D"}, pos=6, candidate=True,
         codes={"1": (M, "T100 3RZ-FE 2.7L 4x2: EPA lists Manual 5-spd only for MY1994", (1994, 1994))},
         not_ruled_codes={},
         models="Toyota T100 2.7L 4x2 (JT4UD1*), MY1994",
         candidate_reason="Code meanings come from vPIC only (the MY1994 Toyota truck filing was not read) and the manual-only claim from EPA only; MY1995 added an automatic.",
         cites=["vpic_live", "epa"],
         epa_cell=dict(make="Toyota", model=r"^T100 2WD$", displ="2.7", drive="2", dscr=None),
         epa_ids=["1994 T100 2WD 2.7 Manual 5-spd is the only 2.7 row for 1994; 1995-1998 add Automatic 4-spd"],
         vpic_expect=dict(engine=r"3RZ", displ="2.7"),
         evidence_gaps="No Toyota filing read for MY1994 trucks."),
    # ---------------- Nissan ----------------------------------------------
    dict(id="nissan_xterra_ka24de_2000_2004", make="Nissan", wmi=["5N1"], years=(2000, 2004),
         fixed={5: "D", 7: "8", 8: "ST"}, pos=4,
         codes={"D": (M, "2.4L KA24DE (Xterra XE four-cylinder, 2WD only): 5-speed manual only", (2000, 2004))},
         not_ruled_codes={"E": "3.3L VG33E V6: 5MT or 4AT", "M": "3.3L supercharged V6: 6MT or 4AT"},
         models="Nissan Xterra 2WD (5N1DD28[S/T]*), MY2000-2004",
         cites=["nis_2002", "nis_2001", "vpic_live", "ref_xterra", "cg_xterra_direct", "epa"],
         epa_cell=dict(make="Nissan", model=r"^Xterra (2WD|4WD)$", displ="2.4", drive=None, dscr=None),
         epa_ids=["16295 (2000)", "17171 (2001)", "18114 (2002)", "19092 (2003)", "20220 (2004): Xterra 2WD 2.4 Manual 5-spd, the only 2.4 Xterra rows (no 4WD 2.4, no automatic 2.4)"],
         vpic_expect=dict(engine=r"KA24|^$", displ="2.4"),
         evidence_gaps="Engine code read in the MY2002 chart (and the MY2001 chart lists Xterra in the same layout); MY2000, 2001, 2003, 2004 rest on vPIC (5N1DD28T decodes to 2.4L 4x2 for each year; KA24DE named for 2002-2004)."),
    dict(id="nissan_frontier_ka24de_4wd_1998", make="Nissan", wmi=["1N6"], years=(1998, 1998),
         fixed={4: "D", 5: "D", 7: "16"}, pos=8,
         codes={"Y": (M, "Position 8 Y = Class D Standard (4WD) with position 4 D = 2.4L: 4-cylinder 4x4, 5-speed manual only", (1998, 1998))},
         not_ruled_codes={"S/T (2WD)": "2.4L 2WD: 5MT or 4AT", "E + Y": "3.3L V6 4WD: 5MT or 4AT",
                          "D + Y in MY1999-2000": "2.4L 4x4: US sources and EPA say manual only, but auto123.com's (Canadian) spec page for the 1999 Frontier XE 4x4 Regular Cab lists an optional 4-speed automatic; not certain, so not ruled"},
         models="Nissan Frontier 2.4L 4x4 Regular/King Cab (1N6DD2[1/6]Y), MY1998",
         cites=["nis_1998", "nis_2002", "vpic_live", "ref_frontier", "cg_frontier_direct", "epa"],
         epa_cell=dict(make="Nissan", model=r"^Frontier 4WD$", displ="2.4", drive="4", dscr=None),
         epa_ids=["14577 (1998): Frontier 4WD 2.4 Manual 5-spd only (also 15365 1999 and 16166 2000, years no longer in scope; no 4WD 2.4 rows after 2000)"],
         vpic_expect=dict(engine=r"KA24|^$", displ="2.4", drive=r"4WD|4x4"),
         evidence_gaps="Codes read in the MY1998 chart (and the MY2002 chart). Narrowed from MY1998-2000 to MY1998 on 2026-11-05 (see verified)."),
    dict(id="nissan_pickup_4cyl_4wd_1984_1997", make="Nissan", wmi=["1N6", "JN6"], years=(1984, 1997),
         fixed={4: "NS", 5: "D"}, pos=8, candidate=True,
         codes={"Y": (M, "Position 8 Y = standard 4WD with a 2.4L four-cylinder (N = Z24/Z24i, S = KA24E): EPA lists Manual 5-spd only", (1984, 1997))},
         not_ruled_codes={"S (2WD)": "2.4L 2WD: 5MT or 4AT", "H + Y": "3.0L V6 4WD: 5MT or 4AT"},
         models="Nissan 720 / D21 'Hardbody' pickup, 2.4L four-cylinder 4x4 (1N6ND??Y, 1N6SD??Y), MY1984-1997",
         candidate_reason="Manual-only rests on EPA alone (every year 1984-1997 lists only Manual 5-spd for the 2.4 4WD truck, while the V6 4WD lists an automatic). No manufacturer or review statement found; weak web sources say an automatic was offered 'with both engines'. The truck charts for MY1984-1997 were not read (MY1998 letter confirms the 2.4L code was S before 1998).",
         cites=["nis_1998", "nis_1990", "vpic_live", "ref_hardbody_none", "epa"],
         epa_cell=dict(make="Nissan", model=r"^(Pickup|Truck|Hardbody) 4WD", displ="2.4", drive="4", dscr=None),
         epa_ids=["27273/28272 (1984 Pickup 4WD)", "868/1550 (1985)", "2537-2539 (1986)", "3782 (1987)", "4948 (1988)", "6080 (1989)", "7147 (1990 Hardbody 4WD)", "8275 (1991)", "9342 (1992)", "10344 (1993)", "11306 (1994)", "12267 (1995)", "13041 (1996)", "13770 (1997): all Manual 5-spd"],
         vpic_expect=dict(engine=r"Z24|KA24|^$", displ="2.4", drive=r"4WD|4x4"),
         evidence_gaps="Truck charts for MY1984-1997 not read; code meanings from vPIC and the MY1998 revision letter."),
]

# ---------------------------------------------------------------------------
# Adversarial verification, 2026-11-05 (a second session tried to refute each
# rule). Every surviving rule carries what was checked. Counterexample scans
# that can be recomputed (ground truth, vPIC decode cache, published labels)
# are recomputed on every run and merged into the block as "rescan".
# ---------------------------------------------------------------------------
VERIFIED_ON = "2026-11-05"
VERIFIED = {
    "toyota_mr2_turbo_3sgte_1991_1995": {
        "result": "kept (low_sample, 0 lot cars)",
        "citations_reopened": [
            "MID f666efc7 (MY1991 Toyota/Lexus) re-downloaded and read as page images: Attachment II p.3 lists MR2 engine S (3S-GTE, 5S-FE), line W, model 2 (SW20L, SW21L), grade 1/2, body M/N; Note #4 (p.5): 3S-GTE = VDS 1st digit S, 4th digit 2; 5S-FE = S, 1. Matches the rule (VIN 4 S, 5 W, 6 2, 7 2).",
            "Wikipedia 'Toyota MR2' read directly: US MR2 Turbo 'offered only with a 5-speed M/T'; NA 5S-FE had A/T or M/T.",
            "EPA rows 7494, 8591, 9665, 10650, 11612 re-read: the only turbo MR2 rows 1991-1995, all Manual 5-spd; the 2.2 rows have Automatic 4-spd.",
        ],
        "counterexample_search": "No ground-truth line, decode-cache VIN or lot car matches JT2SW22 in 1991-1995, so nothing can contradict it today.",
        "scope_edges": "Japanese-market SW20 Turbos (also manual only) carry JDM chassis numbers, not 17-character VINs, so they cannot match. 1996+ excluded (US sales ended after MY1995).",
        "changes": "none",
    },
    "toyota_corolla_xrs_2zzge_2005_2006": {
        "result": "kept (low_sample); narrowed: VIN 6 must be 3 (series ZZE130L/ZZE131L in the filing); no lot car lost",
        "citations_reopened": [
            "MID 9ffcb615 (MY2005 TMMC Corolla/Corolla Matrix/RX330) re-downloaded, chart page read: Corolla 4th B = 4 door sedan 2WD, 5th R = 1ZZ-FE, Y = 2ZZ-GE, 6th 3 = ZZE130L/ZZE131L, 7th 2/0 restraint, 8th E Corolla. No transmission character.",
            "Wikipedia 'Toyota Corolla (E120)' read directly: XRS (ZZE131) MY2005-2006 only, 2ZZ-GE; 'The close ratio C60 6-speed manual transmission ... was the only transmission available'; sold in the US, Canada and Puerto Rico (so a Canadian-market XRS at a US yard is covered too).",
            "EPA: every Corolla row 2004-2007 re-read. 2005: 20796 Automatic 4-spd, 20797 Manual 5-spd, 20798 Manual 6-spd 'SPORTS'; 2006: 21881/21882/21883 the same. No other 1.8 Corolla row, so no 2ZZ-GE automatic.",
            "Live vPIC batch re-decode of the 3 lot VINs (2026-11-05) identical to vin_rules_2_vpic.json: EngineModel 2ZZ-GE, 1.8 L, 4x2, TransmissionStyle blank.",
            "MY2006 NUMMI Corolla filing (01-022-N11B-10382) lists only engine R = 1ZZ-FE, so 2006 XRS VINs are TMMC (2T1) only, as the rule assumes.",
        ],
        "scope_edges": "MY2009-10 Corolla XRS (2AZ-FE, 5MT or 5AT) has a different engine code and years, outside the regex. NUMMI (1NX) and Japan-built (JTD) Corollas are not matched (coverage, not precision).",
        "changes": "fixed VIN 6 = 3",
    },
    "toyota_matrix_xrs_2zzge_2004_2006": {
        "result": "kept (low_sample); narrowed: VIN 6 must be 3; no lot car lost",
        "citations_reopened": [
            "MID 09aff477 (MY2004) re-downloaded, 'Toyota Corolla, Corolla Matrix & Lexus RX330 (2004 Models)' page read: Matrix 4th K = 5 door hatchback 2WD, L = 4WD; 5th R = 1ZZ-FE, Y = 2ZZ-GE; 6th 3; 7th 2/8 restraint; 8th E. MY2005 filing 9ffcb615: same codes (7th 2/0).",
            "Wikipedia 'Toyota Matrix' read directly: U240E automatic 'FWD XRS available in the 2003 only'; 'With the exception of an available automatic in 2003, a six-speed manual transmission was the only gearbox offered in the XRS.'",
            "Toyota Canada 2004, 2005 and 2006 Matrix spec sheets (manufacturer, media.toyota.ca) read: the XRS FWD column is marked only for the 6-speed manual; the 4-speed automatic is marked for Base/XR FWD and 4WD only. TMMC built both markets, so Canadian-market XRS cars are manual too.",
            "EPA: every Matrix row 2003-2007 re-read. 2003 has 18789 Automatic 4-spd 'SPORTS' (that year stays excluded); 2004/2005/2006 the only 'SPORTS' row is Manual 6-spd (19900, 21032, 22126).",
            "Live vPIC batch re-decode of the 4 lot VINs identical to the saved decodes (2ZZ-GE, 1.8 L, 4x2).",
        ],
        "conflicts_found": "auto123.com's 2004 Matrix XRS spec page says 'Transmission 6 speed automatic'. No 6-speed automatic Matrix existed (Wikipedia lists only 4-speed A246E/U240E/U341F automatics; Toyota Canada marks the XRS 6-speed as manual), so this is a data error, not counterevidence. It is recorded because the same site is the only source contradicting the Frontier rule.",
        "scope_edges": "MY2003 XRS (automatic offered) stays out by VIN year 3. AWD Matrix (L body) is 1ZZ-FE only and outside the fixed K. The Kelowna BC car stays uncounted (US-yard rule), although the Canadian spec sheet shows it would also be manual.",
        "changes": "fixed VIN 6 = 3",
    },
    "nissan_xterra_ka24de_2000_2004": {
        "result": "kept (low_sample); narrowed: VIN 8 must be a 2WD code (S or T); no lot car lost",
        "citations_reopened": [
            "MID 00371e3b (MY2002) p.4 and 1d224522 (MY2001) p.2 re-downloaded and read: Xterra (5N1) line D, position 4 2.4L = D, 3.3L = E, position 7 4-door wagon = 8, position 8 Class C 4-wheel ABS (2WD) S, Class D standard (4WD) Y. The chart prints S for the 2WD Xterra, but real 2WD Xterra VINs carry T (all 538 2WD Xterra VINs MY2000-04 in the decode cache; vPIC decodes T as 4x2). The rule now accepts S or T.",
            "Consumer Guide used 2000-04 Xterra read directly: base XE 2.4 'teamed only with a 5-speed manual transmission', 'Only 2-wheel drive was available with the base XE'; options table marks the automatic 'NA XE 4-cylinder'.",
            "EPA: every Xterra row 2000-2005 re-read. The only 2.4 rows are 'Xterra 2WD Manual 5-spd' (16295, 17171, 18114, 19092, 20220); every V6 cell lists both.",
            "Live vPIC batch re-decode of all lot VINs identical to the saved decodes; the new lot car 5N1DD28T91C594227 (Pick Your Part Fontana, listed after the first build) decodes 2001 Xterra 2.4 L 4x2 and was added to vin_rules_2_vpic.json.",
        ],
        "scope_edges": "Xterra was built only in Smyrna (5N1). 2005+ Xterra (VQ40, engine code A) is outside the years. A 2.4 code with Y (4WD) would contradict every source, so it is not labelled.",
        "changes": "fixed VIN 8 in [ST]",
    },
    "nissan_frontier_ka24de_4wd_1998": {
        "previous_id": "nissan_frontier_ka24de_4wd_1998_2000",
        "result": "kept (low_sample) but NARROWED from MY1998-2000 to MY1998; VIN 7 must be 1 or 6 (Regular or King Cab). All 3 lot cars are MY1998, so the count is unchanged.",
        "citations_reopened": [
            "MID 8a102da6 (MY1998) re-downloaded and read: letter p.1 (engine code revised S to D) and truck chart p.4: 2.4L = D, Nissan Frontier Truck = D, Regular Cab 1, King Cab 6, position 8 Class D Standard (4WD) = Y. MY2002 chart (00371e3b p.4) the same.",
            "Consumer Guide used 1998-04 Frontier read directly: 1998 'initial 4x4s were manual-shift only'; 1999 '... except for 4-cylinder 4x4s, which were manual-shift only'; 2000 price list has only a 5-speed 4-cylinder 4WD line.",
            "EPA: every Nissan 2.4 truck row 1997-2001 re-read. Frontier 4WD 2.4 is Manual 5-spd only in 1998 (14577), 1999 (15365) and 2000 (16166); the 2WD 2.4 rows list both.",
            "Live vPIC batch re-decode of the 3 lot VINs identical to the saved decodes (2.4 L, 4WD, TransmissionStyle blank).",
        ],
        "conflicts_found": "auto123.com (Canadian market) spec page for the 1999 Nissan Frontier 4x4 Regular Cab XE (2.4L 16V 4cyl dohc) lists 'Transmission 5 speed manual' and 'Transmission (Option) 4 speed automatic'. ARFC / New Car Test Drive 1999 review text (search excerpts) says the 2.4 'powers all two-wheel-drive Frontiers and XE 4x4 models' and that a four-speed automatic is optional, without splitting by drive. auto123's data are error-prone (it lists a 6-speed automatic for the 2004 Matrix XRS), and every US source agrees on manual only, but a published source names an automatic for exactly this configuration in MY1999, and a Canadian-market truck has the same VIN pattern and can reach a US yard. MY1999-2000 are therefore not certain and were removed. No source naming a 1998 4-cylinder 4x4 automatic was found (auto123 has no 1998 page).",
        "scope_edges": "Crew Cab (VIN 7 = 7) was V6-only, now excluded by the fixed VIN 7. 2001+ 4WD Frontiers were V6-only (no EPA 4WD 2.4 row). Desert Runner is 2WD (S/T) and outside the Y code.",
        "changes": "years 1998-2000 -> 1998; id renamed; fixed VIN 7 in [16]",
    },
    "toyota_celica_alltrac_turbo_1990_1993": {
        "result": "still candidate (not counted, 0 lot cars); not re-researched beyond the checks below",
        "checked": "MY1991 filing note #3 re-read (3S-GTE = S, 8). EPA rows 6614, 7720, 8810, 9868 re-read: the only 2.0 turbo 4WD Celica rows, Manual 5-spd. No ground-truth or decode-cache VIN matches.",
    },
    "toyota_tacoma_2trfe_4wd_2005_2010": {
        "result": "still candidate (not counted)",
        "checked": "MID MY2006 TMMCA Tacoma chart (01-022-N11B-10382) shows the same 4th/5th-digit codes as MY2005 (P/U 4WD Regular/Xtra Cab, X = 2TR-FE). EPA rows re-read (Manual 5-spd only 2005-2010). The source conflict that keeps it a candidate stands. One lot car, decoded 2TR-FE 4WD by live vPIC.",
    },
    "toyota_t100_3rzfe_2wd_1994": {
        "result": "still candidate (not counted)",
        "checked": "EPA 1994 T100 2WD 2.7 row re-read (Manual 5-spd only). Live vPIC re-decode of the 2 lot VINs: 3RZ-FE 2.7 4x2. No filing for MY1994 trucks read.",
    },
    "nissan_pickup_4cyl_4wd_1984_1997": {
        "result": "still candidate (not counted)",
        "checked": "EPA rows re-read (2.4 4WD truck Manual 5-spd only every year). Wikipedia 'Nissan Hardbody Truck' read directly says only that 'an automatic transmission was an available option' (not split by engine or drive), so manual-only still rests on EPA alone. Live vPIC re-decode of all 20 lot VINs unchanged (Z24/KA24, 2.4 L, 4WD). One lot car carries the feed model name 'Ford F150 Pickup' (make Nissan); the rule keys on the VIN, which decodes to a Nissan Pickup, so the name does not affect it.",
    },
}

ANSWER = {
    "toyota": "The VIN does NOT encode the transmission in any model year read (MY1991, 2000, 2003, 2004, 2005 filings; same layout for Toyota-built Lexus and Scion). Positions 4-8 carry engine, line, model/series, grade or restraint, body/cab and drive. Manual-only cells reachable by the engine character or pre-2000 grade digit: MR2 Turbo (JT2SW22, MY1991-95), Corolla XRS (2T1BY..E, MY2005-06), Matrix XRS (2T1KY..E, MY2004-06). Candidates only: Celica All-Trac Turbo (JT2ST88, MY1990-93), Tacoma 2.7 4x4 (P/U + X, MY2005-10), T100 2.7 4x2 (MY1994).",
    "lexus": "The VIN does NOT encode the transmission (Lexus shares Toyota's filings: MY1991 LS400/ES250, MY2004 RX330, MY2005 RX330). No Lexus engine was sold manual-only, so no rule.",
    "scion": "The VIN does NOT encode the transmission for Toyota-built Scions (xA, xB, tC, xD, iQ, iM; MY2004 filing). Scion FR-S (WMI JF1) is Subaru-built and IS ruled by Subaru's character 11 in vin_rules_1; Scion iA (WMI 3MY) is Mazda-built (no transmission character). No manual-only Scion engine, so no rule here.",
    "nissan": "The VIN does NOT encode the transmission in any model year read (MY1985, 1990, 1998, 2001, 2002, 2013, 2025). Position 4 is the engine and position 8 the restraint system (cars) or GVWR/brake/drive (trucks: S/T/X 2WD, Y 4WD). Manual-only cells reachable by engine + drive: Xterra 2.4L (5N1DD28, MY2000-04), Frontier 2.4L 4WD (1N6DD..Y, MY1998 only; MY1999-2000 not ruled, a Canadian spec source lists an automatic). Candidate only: 720/D21 pickup 2.4L 4WD (MY1984-97).",
    "infiniti": "The VIN does NOT encode the transmission (Infiniti is in Nissan's charts: MY1990, 2002, 2013, 2025). No Infiniti engine was sold manual-only (EPA lists an automatic for every Infiniti engine/drive cell), so no rule.",
    "vpic_already_decodes_it": "vPIC leaves TransmissionStyle blank for these VIN patterns, so every in-scope car without a listing transmission is a newly confirmed car. The flip side: ground truth for these makes is almost entirely automatics from listings or vPIC defaults, and no in-scope car has a checkable label, so every kept rule is low_sample and rests on the manufacturer's code table + EPA + an independent reference.",
}

VIN_SCHEME = {
    "toyota_pre_2000_passenger_car": "VDS (VIN 4-8): 4 engine type, 5 line, 6 model designation, 7 series (grade), 8 body type + restraint (MY1991 filing). MR2: VIN 7 = 2 means 3S-GTE turbo, 1 = 5S-FE. Celica: VIN 7 = 8 'turbo All-Trac', 5 GT-S, 6 ST, 7 GT.",
    "toyota_pre_2000_truck": "VIN 4 engine (R 22R-E, V 3VZ-E), 5 line (N truck), 6 drive train (8/9 4x2, 0/1 4x4), 7 cab/chassis, 8 series + brake / GVWR (MY1991 filing).",
    "toyota_2000_on_passenger_car": "VIN 4 body type (+2WD/4WD), 5 engine type, 6 series (chassis code), 7 restraint system, 8 line (MY2000-2005 filings). Corolla/Matrix 5th digit: R = 1ZZ-FE, Y = 2ZZ-GE.",
    "toyota_2005_tacoma": "VIN 4 cab + drive + brake (N/T/J/K 2WD, P/U/L/M 4WD), 5 engine (X 2TR-FE 2.7L, U 1GR-FE 4.0L), 6 series, 7 grade, 8 line N.",
    "nissan_cars": "VIN 4 engine, 5 line, 6 model change, 7 body type, 8 restraint system (+ 2WD/4WD from the 2010s) (MY1985, 1990, 2002, 2013, 2025 filings).",
    "nissan_trucks_mpv": "VIN 4 engine, 5 line, 6 model change, 7 body/cab, 8 GVWR class + chassis/brake system + drive: S/T/X = 2WD, Y = standard 4WD (MY1998, 2001, 2002 charts).",
    "transmission_character": "none, in any filing read for these five makes",
}

NOT_RULED = [
    "Toyota/Lexus/Scion and Nissan/Infiniti VINs carry no transmission character, so for the large majority of these cars (Camry, Corolla 1ZZ/2ZR, Tacoma 2WD and V6, Sentra, Altima, Versa, Frontier/Xterra V6, 350Z/370Z, G35/G37, IS/SC ...) the VIN cannot say manual vs automatic. Those cars need listing text, a build-sheet source, or the owner.",
    "Nissan Sentra SE-R Spec V (MY2002-06 and MY2007-12, 6-speed manual only) shares its engine code with the SE-R (manual/automatic MY2002-06, CVT MY2007-12); position 8 is the restraint system (A/D), so the Spec V is not identifiable from the VIN. Not ruled.",
    "Nissan 370Z MY2021 (EPA lists only Manual 6-spd) and 370Z NISMO: engine code shared with automatic cars in other years; not ruled.",
    "Toyota MR2 Spyder (MY2000-05): EPA lists only manuals, but the SMT sequential gearbox (an automated manual, which the app does not call manual) was sold from MY2002 and the VIN does not tell it apart. Not ruled.",
    "Toyota Celica All-Trac Turbo ST165 (MY1988-89), Camry All-Trac 2.0 4WD (MY1988 manual-only per EPA), 4Runner 2.4 4WD (MY1984, 1994-95), 22R-TE turbo pickups (MY1985-88), FJ60 Land Cruiser (MY1984-87), GR Corolla (MY2023+), Nissan Pathfinder 2.4 4WD (MY1987-89), 200SX turbo (MY1986), Sentra 4WD wagon (MY1987-88), Stanza 4WD wagon (MY1987), Sentra 1.7 diesel (MY1985-86): EPA lists only manuals, but the filings for those years were not read; no lot car with a matching VIN was found for most of them. Not ruled.",
    "Matrix XRS MY2003 (2T1KY..E): EPA lists both a 4-speed automatic and a 6-speed manual for the 2ZZ-GE that year (Wikipedia agrees), so MY2003 is excluded from the Matrix rule.",
    "Lexus and Infiniti: no engine/drive cell is manual-only in EPA for any year; no rule.",
    "Nissan Frontier 2.4L 4x4 MY1999-2000 (1N6DD..Y, VIN year X/Y): removed from the Frontier rule by the 2026-11-05 verification. EPA and Consumer Guide say manual only, but auto123.com's spec page for the 1999 Frontier 4x4 Regular Cab XE (2.4L 4cyl, Canadian market) lists 'Transmission (Option) 4 speed automatic', and the 1999 ARFC/New Car Test Drive review text does not split the optional automatic by drive. A Canadian-market truck has the same VIN pattern and can reach a US yard, so the claim is not certain for those years. No lot car is affected today (all in-scope trucks are MY1998).",
    "Cars without a 17-character VIN (summary.five_make_coverage.<make>.no_vin) cannot be reached by VIN rules.",
    "Cars at Canadian yards (AB, BC) are scanned but not newly confirmed: the manual-only facts are US-market facts (EPA).",
]

VALIDATION_METHOD = (
    "For each rule, every lot car is matched by WMI, valid check digit, VIN model year (character 10, listing year picks the 30-year cycle) and the fixed + coded characters. "
    "'checkable' = its ground_truth.jsonl line has class manual/automatic/cvt/amt/dct and uniformCell is empty (uniform-cell lines are vPIC model-level defaults, counted separately). "
    "Agreement = same manual-vs-not-manual answer. epa_cell = the EPA rows the claim rests on, re-read per model year: 'manual_only_years' must cover the rule's years. "
    "vpic_check = live vPIC decode of each in-scope VIN (vin_rules_2_vpic.json): engine model / displacement / drive must match the code's meaning. "
    "Status: candidate when flagged (evidence short of certain); drop when >= 20 checkable and agreement < 99.5%; low_sample when < 20 checkable (kept: the code table is the manufacturer's own Part 565 filing or vPIC built from it, and the manual-only fact has EPA plus an independent reference); keep otherwise. "
    "'newly_confirmed_manual' = in-scope cars at US yards whose published extras transmission is empty today."
)


# ---------------------------------------------------------------------------
def rule_regex(r: dict) -> str:
    chars = ["."] * 17
    for p, allowed in r["fixed"].items():
        chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
    man = "".join(c for c, v in r["codes"].items() if v[0] == M)
    if not man:
        return ""
    chars[r["pos"] - 1] = "[" + man + "]" if len(man) > 1 else man
    ys = year_chars(*r["years"])
    chars[9] = "[" + ys + "]" if len(ys) > 1 else ys
    return "^(" + "|".join(r["wmi"]) + ")" + "".join(chars[3:])


def classify(vin: str, year: int):
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        hit = r["codes"].get(vin[r["pos"] - 1])
        if hit and hit[2][0] <= year <= hit[2][1]:
            return r, hit[0], vin[r["pos"] - 1], hit[1]
    return None


class Epa:
    def __init__(self, path: Path):
        self.ok = path.exists()
        self.rows = []
        if self.ok:
            with open(path, newline="", encoding="utf-8") as f:
                self.rows = [r for r in csv.DictReader(f) if r["make"] in ("Toyota", "Nissan")]

    def cell(self, spec: dict, years) -> dict:
        """Per model year: EPA transmission classes and row ids for the cell."""
        out = {}
        for y in range(years[0], years[1] + 1):
            cls, ids = set(), []
            for r in self.rows:
                if int(r["year"]) != y or r["make"] != spec["make"] or not re.search(spec["model"], r["model"]):
                    continue
                if r["displ"] != spec["displ"]:
                    continue
                four = ("4-Wheel" in r["drive"] or "All-Wheel" in r["drive"] or "4WD" in r["model"])
                if spec.get("drive") == "4" and not four:
                    continue
                if spec.get("drive") == "2" and four:
                    continue
                if spec.get("dscr") and not re.search(spec["dscr"], r["eng_dscr"] + ("TRBO" if r["tCharger"] == "T" else "")):
                    continue
                cls.add(epa_tclass(r["trany"]))
                ids.append(f"{r['id']} {r['model']} {r['trany']}")
            out[y] = {"classes": sorted(cls), "rows": ids}
        return out


def main() -> int:
    inv = json.loads((DATA / "inventory_live.json").read_text())
    extras = json.loads((DATA / "vehicle_extras.json").read_text())["extras"]
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache.pop("_exportedAt", None)
    gt = {}
    with open(HERE / "ground_truth.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            gt[d["id"]] = d
    epa = Epa(HERE / "epa" / "vehicles.csv")
    vp = json.loads(VPIC_FILE.read_text()) if VPIC_FILE.exists() else {"vins": {}, "partial": []}
    vlive = vp.get("vins", {})

    fi = {f: i for i, f in enumerate(inv["fields"])}
    yards = inv["yards"]
    FIVE = ("Toyota", "Lexus", "Scion", "Nissan", "Infiniti")
    all_wmi = {w for r in RULES for w in r["wmi"]}

    st = {r["id"]: defaultdict(Counter) for r in RULES}
    ex_dis = {r["id"]: [] for r in RULES}
    vchk = {r["id"]: Counter() for r in RULES}
    vbad = {r["id"]: [] for r in RULES}
    codes_seen = {r["id"]: Counter() for r in RULES}
    years_seen = {r["id"]: Counter() for r in RULES}
    models_seen = {r["id"]: Counter() for r in RULES}
    make_cov = {m: Counter() for m in FIVE}
    scan = Counter()
    newly, canada_cars, in_scope_vins, conflicts = [], [], [], []

    for row in inv["vehicles"]:
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        fyear = row[fi["year"]]
        make = row[fi["make"]] or ""
        model = row[fi["model"]] or ""
        yd = yards[row[fi["yard"]]] if isinstance(row[fi["yard"]], int) else ["", "", ""]
        ex = list(extras.get(vid) or []) + [""] * 5
        pub = ex[3] or ""
        if make in FIVE:
            make_cov[make]["cars"] += 1
            make_cov[make]["no_trans_info"] += 0 if pub else 1
            make_cov[make]["vin17"] += 1 if len(vin) == 17 else 0
            make_cov[make]["no_vin"] += 0 if len(vin) == 17 else 1
        if len(vin) != 17 or vin[:3] not in all_wmi:
            continue
        scan["rule_wmi_vins"] += 1
        if not check_digit_ok(vin):
            scan["bad_check_digit"] += 1
            continue
        y = vin_year(vin, fyear)
        if y is None:
            scan["vin_year_vs_listing_mismatch"] += 1
            continue
        res = classify(vin, y)
        if res is None:
            continue
        r, claim, code, meaning = res
        rid = r["id"]
        scan["covered"] += 1
        s = st[rid][claim]
        s["in_scope"] += 1
        codes_seen[rid][f"char{r['pos']}={code}"] += 1
        years_seen[rid][y] += 1
        models_seen[rid][f"{make} {model}"] += 1
        in_scope_vins.append(vin)
        if make in FIVE:
            make_cov[make]["covered_by_rule"] += 1
        g = gt.get(vid)
        if g is not None:
            gcls = g.get("transClass", "")
            if g.get("uniformCell"):
                s["uniform_cell_excluded"] += 1
            elif gcls in KNOWN:
                s["checkable"] += 1
                ok = (gcls == "manual") == (claim == M)
                s["agree" if ok else "disagree"] += 1
                if gcls == "manual":
                    s["checkable_gt_manual"] += 1
                if not ok:
                    ex_dis[rid].append({"id": vid, "vin": vin, "year": y, "model": model, "ground_truth": g.get("trans"), "source": g.get("source")})
            else:
                s["speeds_only_excluded"] += 1
        # live vPIC cross-check
        lv = vlive.get(vin)
        if lv is None:
            vchk[rid]["not_decoded"] += 1
        else:
            exp = r["vpic_expect"]
            okv = bool(re.search(exp["engine"], lv.get("EngineModel", ""))) and \
                (lv.get("DisplacementL", "")[:3].rstrip("0").rstrip(".") == exp["displ"].rstrip("0").rstrip(".")
                 or str(round(float(lv.get("DisplacementL") or 0), 1)) == exp["displ"]) and \
                (not exp.get("drive") or bool(re.search(exp["drive"], lv.get("DriveType", ""))))
            vchk[rid]["consistent" if okv else "inconsistent"] += 1
            if lv.get("TransmissionStyle"):
                vchk[rid]["vpic_has_transmission"] += 1
            if not okv and len(vbad[rid]) < 10:
                vbad[rid].append({"vin": vin, "year": y, "EngineModel": lv.get("EngineModel"), "DisplacementL": lv.get("DisplacementL"), "DriveType": lv.get("DriveType")})
        # published label that contradicts the rule
        pcls = tclass(pub)
        if pub and pcls in KNOWN and (pcls == "manual") != (claim == M):
            conflicts.append({"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid, "published_trans": pub, "transSrc": ex[4] or "vin"})
        if not pub:
            raw = cache.get(vin)
            dec = raw if isinstance(raw, dict) else None
            why = "not_in_cache_backup" if dec is None else "vpic_trans_blank"
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"char{r['pos']}={code}: {meaning}", "why_no_trans": why, "yard": yd[0], "state": yd[2]}
            if yd[2] in CANADA:
                s["no_trans_info_canadian_yard"] += 1
                canada_cars.append(rec)
                continue
            s["no_trans_info"] += 1
            s[f"no_trans_info_{why}"] += 1
            if claim == M:
                newly.append(rec)

    # Counterexample rescan (verification): every ground-truth line and every
    # cached vPIC decode whose raw VIN matches a rule's regex, regardless of
    # check digit or listing year, and what transmission (if any) it carries.
    rescan = {}
    for r in RULES:
        rx = re.compile(rule_regex(r))
        g_hits = [g for g in gt.values() if rx.match((g.get("vin") or "").upper())]
        c_hits = {v: d for v, d in cache.items() if rx.match(v)}
        c_tr = {v: d.get("transmission") for v, d in c_hits.items() if isinstance(d, dict) and d.get("transmission")}
        rescan[r["id"]] = {
            "regex": rx.pattern,
            "ground_truth_lines_matching": len(g_hits),
            "ground_truth_by_class": dict(Counter(g.get("transClass") or "none" for g in g_hits)),
            "ground_truth_non_manual_examples": [{"id": g["id"], "vin": g["vin"], "trans": g.get("trans"), "source": g.get("source")}
                                                 for g in g_hits if g.get("transClass") != "manual"][:10],
            "vpic_cache_vins_matching": len(c_hits),
            "vpic_cache_with_transmission": dict(Counter(c_tr.values())),
            "published_label_conflicts": sum(1 for c in conflicts if c["rule"] == r["id"]),
        }

    out_rules = []
    for r in RULES:
        rid = r["id"]
        tot = Counter()
        for cl in (M, A):
            tot.update(st[rid][cl])
        chk, agr = tot["checkable"], tot["agree"]
        agreement = round(agr / chk, 4) if chk else None
        if r.get("candidate"):
            status = "candidate"
        elif chk >= MIN_SAMPLE and agreement is not None and agreement < MIN_AGREEMENT:
            status = "drop"
        elif chk < MIN_SAMPLE:
            status = "low_sample"
        else:
            status = "keep"
        cell = epa.cell(r["epa_cell"], r["years"]) if epa.ok else {}
        man_only_years = [y for y, v in cell.items() if v["classes"] == ["manual"]]
        other_years = {y: v["classes"] for y, v in cell.items() if v["classes"] != ["manual"]}
        sm = st[rid][M]
        out_rules.append({
            "id": rid,
            "make": r["make"],
            "status": status,
            "claim": "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + ", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())),
                                     "car is at a US yard (Canadian-market offerings are not covered by the EPA evidence)"]},
            "vin_condition": {"position": r["pos"], "manual_codes": {c: v[1] + f" (MY{v[2][0]}-{v[2][1]})" for c, v in r["codes"].items()},
                              "codes_not_ruled": r["not_ruled_codes"]},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"] if k != "epa"] + [{"url": C["epa"]["url"], "doc": C["epa"]["doc"], "says": "; ".join(r["epa_ids"])}],
            "candidate_reason": r.get("candidate_reason", ""),
            "evidence_gaps": r.get("evidence_gaps", ""),
            "validation": {
                "in_scope_lot_cars": sm["in_scope"],
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": tot["checkable_gt_manual"],
                "uniform_cell_lines_excluded": tot["uniform_cell_excluded"],
                "ground_truth_speeds_only_excluded": tot["speeds_only_excluded"],
                "disagree_examples": ex_dis[rid][:10],
                "epa_cell": {"filter": r["epa_cell"], "manual_only_years": man_only_years, "years_with_other_classes": other_years,
                             "all_rule_years_manual_only": len(man_only_years) == r["years"][1] - r["years"][0] + 1,
                             "rows": {y: v["rows"] for y, v in cell.items()}},
                "vpic_check": {**dict(vchk[rid]), "expect": r["vpic_expect"], "inconsistent_examples": vbad[rid]},
                "codes_seen_on_lots": dict(codes_seen[rid]),
                "years_seen_on_lots": dict(sorted(years_seen[rid].items())),
                "models_seen_on_lots": dict(models_seen[rid].most_common()),
                "cars_without_trans_info_us_yards": sm["no_trans_info"],
                "cars_without_trans_info_by_reason": {k[len("no_trans_info_"):]: v for k, v in sm.items() if k.startswith("no_trans_info_") and k != "no_trans_info_canadian_yard"},
                "cars_without_trans_info_canadian_yards_not_counted": sm["no_trans_info_canadian_yard"],
            },
            "newly_confirmed_manual": sm["no_trans_info"],
            "verified": {"on": VERIFIED_ON, **VERIFIED.get(rid, {"result": "NOT VERIFIED"}), "rescan": rescan[rid]},
        })

    kept = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    nm_conf = [c for c in newly if c["rule"] in kept]
    nm_cand = [c for c in newly if c["rule"] not in kept]
    man_chk = sum(x["validation"]["checkable_ground_truth"] for x in out_rules if x["id"] in kept)
    man_agr = sum(x["validation"]["agree"] for x in out_rules if x["id"] in kept)
    doc = {
        "worklist": "vin_rules_2",
        "makes": list(FIVE),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "generator": "scraper/manual_detect/vin_rules_2.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json", "vehicle_extras": "docs/data/vehicle_extras.json",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (uniformCell lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA cross-check skipped)"),
                   "vpic_live": "scraper/manual_detect/vin_rules_2_vpic.json" + ("" if vlive else " (MISSING)"),
                   "mid_filings_read": "NHTSA MID Part 565 files: Toyota 159 filings MY1984-2011 downloaded (text-searched where OCR text exists; MY1991, 2000, 2003, 2004, 2005 tables read), Nissan 104 filings MY1985-2013 downloaded (scans; MY1985, 1990, 1998, 2001, 2002, 2013 charts read), plus MY2025 Nissan (ORG23829). Downloaded 2026-11-05 from vpic.nhtsa.dot.gov/mid (search API + displayfile)."},
        "answer": ANSWER,
        "vin_scheme": VIN_SCHEME,
        "not_encoded_or_not_ruled": NOT_RULED,
        "summary": {
            "rules": len(out_rules),
            "rules_by_status": dict(Counter(x["status"] for x in out_rules)),
            "newly_confirmed_manual_keep_and_low_sample_rules": len(nm_conf),
            "newly_confirmed_manual_candidate_rules_only": len(nm_cand),
            "newly_confirmed_manual_by_rule": {x["id"]: x["newly_confirmed_manual"] for x in out_rules},
            "newly_confirmed_manual_by_feed_make": dict(Counter(c["make"] for c in nm_conf)),
            "canadian_yard_cars_not_counted": len(canada_cars),
            "ground_truth_precision_manual_claims_kept_rules": {"checkable": man_chk, "agree": man_agr,
                                                                "precision": round(man_agr / man_chk, 4) if man_chk else None,
                                                                "note": "no in-scope car has a checkable ground-truth label" if not man_chk else ""},
            "published_labels_contradicting_a_rule": len(conflicts),
            "scan": dict(scan),
            "five_make_coverage": {m: dict(v) for m, v in make_cov.items()},
        },
        "validation_method": VALIDATION_METHOD,
        "adversarial_verification": {
            "on": VERIFIED_ON,
            "method": "A second session tried to refute every rule: re-downloaded and read each cited MID filing page; re-read every EPA row of each model/year (not only the rule's filter); read Wikipedia, Consumer Guide and Toyota Canada pages directly where the first pass had only search excerpts; searched for any published statement of the other transmission; re-decoded all in-scope VINs live with vPIC; scanned ground_truth.jsonl and the vPIC decode cache for every VIN matching each rule regex (per-rule 'rescan', recomputed each run); checked scope edges (year boundaries, drive and cab codes, Canada/Mexico-built variants, feed model names).",
            "outcome": "No rule refuted outright. Frontier narrowed to MY1998 (a Canadian spec source lists an optional automatic for the 1999 4-cylinder 4x4). Fixed characters tightened on Corolla XRS and Matrix XRS (VIN 6 = 3), Xterra (VIN 8 = S/T, 2WD) and Frontier (VIN 7 = 1/6). Candidates unchanged. Ground truth still has no labelled in-scope car, so precision on ground truth remains unmeasurable (0 of 0).",
            "not_done": "Wikipedia 'Nissan Xterra' returned HTTP 429 and was not read; edmunds.com, cars.com, kbb.com and thecarconnection.com refuse the session (403) and were not worked around (CLAUDE.md rule 2). The MY2006 TMMC Corolla/Matrix filing was not located; MY2006 rests on vPIC, Wikipedia and the Toyota Canada 2006 spec sheet.",
        },
        "rules": out_rules,
        "newly_confirmed_manual_cars": nm_conf,
        "candidate_rule_manual_cars": nm_cand,
        "canadian_yard_cars": canada_cars,
        "published_label_conflicts": conflicts,
        "vpic_partial_pattern_decodes": vp.get("partial", []),
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    if "--list-vins" in sys.argv:
        print("\n".join(sorted(set(in_scope_vins))))
        return 0
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}  canadian not counted: {s['canadian_yard_cars_not_counted']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("manual-claim precision (kept):", s["ground_truth_precision_manual_claims_kept_rules"])
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"])
    for x in out_rules:
        v = x["validation"]
        print(f"  {x['id']}: {x['status']} in_scope={v['in_scope_lot_cars']} chk={v['checkable_ground_truth']} epa_manual_only_all_years={v['epa_cell']['all_rule_years_manual_only']} other={v['epa_cell']['years_with_other_classes']} vpic={ {k: v['vpic_check'][k] for k in v['vpic_check'] if k not in ('expect', 'inconsistent_examples')} }")
    print("scan:", s["scan"])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
