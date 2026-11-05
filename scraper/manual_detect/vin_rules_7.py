#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 7: Volkswagen, Audi, BMW,
MINI, Mercedes-Benz, Volvo, Saab, Porsche, Land Rover.

What the manufacturers' own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say. 945 filings were downloaded 2026-11-05 for the
filers Saab (4 names), Volvo Car USA / Volvo Car Corp., Porsche AG / Porsche
Cars NA, Volkswagen AG / VW Group of America / VW de Mexico (which also files
for Audi), Audi AG, BMW AG / BMW of North America / BMW Manufacturing / BMW M
(which also file for MINI), Mercedes-Benz AG / MB of North America / MB Cars /
MB USA (Sprinter) / DaimlerChrysler AG, Land Rover North America / Jaguar Land
Rover, filed up to 2021. Text layers were searched; scanned filings were OCR'd
(tesseract) and the key pages were read as page images.

  * Saab (YS3): ENCODED. Position 7 is "Gearbox" in every Saab filing in MID
    (MY1988-1990, 1992-1996, 1999, 2001, 2010-2012).
  * Land Rover (SAL): ENCODED MY1993-1998 at position 8 "Transmission Type"
    (4 = 4-speed automatic, 8 = 5-speed manual); MY1999 on the position lists
    automatics only.
  * BMW (WBA/WBS/4US): the type ("AG") code in positions 4-7 is a model
    identifier, and BMW gave the automatic its own code in the E21/E23/E24/
    E28/E30/E32/E34 era (BMW of North America "US Serial Number Ranges",
    model suffix "A = Automatic Transmission") and for the E39 5 Series
    (MY2003 DMV package: 525i DT3x / 525iA DT4x ...). E36 (MY1992-1999 codes
    come in pairs but no BMW document in MID names which is automatic), E46,
    E53 X5, E83 X3, E85 Z4, E60/E90 and later share one code for both
    transmissions: NOT ENCODED.
  * MINI (WMW): NOT ENCODED (Cooper RC33 and Cooper S RE33 each cover both
    transmissions in BMW's MY2003 table). Model-level manual-only codes:
    Cooper S RE33 MY2003-2004 (BMW lists no automatic serial range; EPA lists
    only the 6-speed manual), John Cooper Works MY2009-2012.
  * Volkswagen (WVW/3VW/1VW/WVG): position 4 carries the transmission for
    some lines from MY2006 (Rabbit, new GTI, Eos, Passat B6, CC, Golf); before
    MY2006 and for Jetta, New Beetle, Passat NMS, Routan, Touareg, Tiguan
    position 4 is a trim/package code: NOT ENCODED.
  * Audi (WAU/WA1/TRU): NOT ENCODED before MY2010; from the MY2010 VIN
    breakdown position 4 carries a "Trans" column for some series (A4/A5
    manual series letters). Not ruled here: every lot car in those scopes
    already has a vPIC transmission (see not_encoded_or_not_ruled).
  * Volvo (YV1/YV4): NOT ENCODED. MY1994-2003 filings annotate engine-version
    (positions 6-7) + emissions (position 8) combinations as "Man. Only",
    "Auto Only" or both; only the 850 B5254S with emissions code 0
    (MY1994-1995) and some Canada-only codes are manual-only.
  * Mercedes-Benz, Porsche: NOT ENCODED in any filing read.

Every rule is validated against ground_truth.jsonl (uniformCell lines are
unlabelled), cross-checked per car against EPA, and counted for the lot cars
WITHOUT transmission info it would newly confirm as manual.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (optional, EPA cross-check).
Output: scraper/manual_detect/vin_rules_7.json

Run:  python3 -I scraper/manual_detect/vin_rules_7.py
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
import epa_profile as ep  # noqa: E402  (epa_keys, feed_keys, trany_class)

OUT = HERE / "vin_rules_7.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
MAKES = ("Volkswagen", "Audi", "BMW", "MINI", "Mercedes-Benz", "Volvo", "Saab", "Porsche", "Land Rover")
EPA_MAKES = {"Volkswagen", "Audi", "BMW", "MINI", "Mini", "Mercedes-Benz", "Volvo", "Saab", "Porsche", "Land Rover"}
M, A = "manual", "automatic"
CANADA = {"ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "YT", "NT", "NU"}

# ---------------------------------------------------------------------------
# VIN helpers (same conventions as vin_rules_0..6)
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


def yrs(lo, hi):
    return list(range(lo, hi + 1))


def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


def web(url: str, doc: str, says: str) -> dict:
    return {"url": url, "doc": doc, "says": says}


# ---------------------------------------------------------------------------
# Citations (MID files downloaded 2026-11-05; "OCR" = scanned filing read via
# tesseract and checked against the page image for the quoted rows)
# ---------------------------------------------------------------------------
C = {
    # --- Saab ---------------------------------------------------------------
    "saab3046": mid("2839b830-8346-4492-9171-cda7753fa370",
                    "NHTSA 01-22-N11B-3046, Saab-Scania of America 1988-10-12, VIN format and coding for 1989 Saab cars, OCR",
                    "Positions: 4 Product Line (A = Saab 900, C = Saab 9000), 5 Model Series & Restraint, 6 Body Type, 7 - Gearbox: 5 = 5-speed Manual, 6 = 3-speed Automatic, 8 = 4-speed Automatic; 8 Engine Type."),
    "saab3986": mid("969940d5-9681-47f0-b32a-cb05e145ca0c",
                    "NHTSA 01-22-N11B-3986, Saab Cars North America 1990-07-06, 1988-1990 Saab VIN coding format, OCR",
                    "MY1990 and MY1988-1989 sheets: '7 - Gearbox: 5 = 5-Speed Manual, 6 = 3-Speed Automatic (900), 8 = 4-Speed Automatic (9000)'."),
    "saab4735": mid("9b8abf7b-e2bb-47f9-944a-250582b8d1ea",
                    "NHTSA 01-22-N11B-4735, Saab Cars USA 1991-06-20, VIN deciphering for MY1992, OCR",
                    "'7 . Gearbox: 5 = 5-Speed Manual, 6 = 3-Speed Automatic (900 only), 8 = 4-Speed Automatic (9000 only)'; model year N = 1992."),
    "saab5368": mid("2f075528-8fbc-42b7-bffc-e347344c4674",
                    "NHTSA 01-22-N11B-5368, Saab Cars USA 1993-11-23, MY1993 VIN coding, OCR",
                    "'7 Gearbox: 5 = 5-Speed Manual, 6 = 3-Speed Automatic (900 only), 8 = 4-Speed Automatic (9000 only)'; P = 1993."),
    "saab5385": mid("2add9339-bf48-48bc-a7b7-64c4b4f70983",
                    "NHTSA 01-22-N11B-5385, Saab Cars USA 1993-11-24, MY1994 VIN coding, OCR",
                    "Car line A = Saab 900 (Convertible only), C = 9000, D = 900 (New Generation); '7 Gearbox: 5 = 5-Speed Manual, 6 = 3-Speed Automatic (900 Convertible only), 8 = 4-Speed Automatic'."),
    "saab5627": mid("16dcefa9-31bc-4744-9824-0a3cbc8680c7",
                    "NHTSA 01-22-N11B-5627, Saab Cars USA 1994-03-08, MY1995 VIN coding, OCR",
                    "'7 Gearbox: 5 = 5-Speed Manual, 8 = 4-Speed Automatic' (C = 9000, D = 900)."),
    "saab5866": mid("dc176f2d-ba46-494b-bb2c-a0c0786fa7a9",
                    "NHTSA 01-22-N11B-5866, Saab Cars USA 1995-05-31, MY1996 VIN coding, OCR",
                    "'7 Gearbox: 5 = 5-Speed Manual, 8 = 4-Speed Automatic'; T = 1996."),
    "saab6702": mid("59685278-ddfe-4f0c-8b66-6c5313b1baf3",
                    "NHTSA 01-22-N11B-6702, Saab Cars USA 1998-02-09, 1999 Vehicle Identification Number (service information sheet), OCR",
                    "Car line D = Saab 9-3, E = Saab 9-5; '7 Gearbox: 5 = 5-Speed Manual' (the automatic code is cut off in the scan; the MY2001 sheet below gives 8 = 4-Speed Automatic)."),
    "saab8039": mid("f2d5eaaa-f1d9-4363-91a1-84ef8b89dbf1",
                    "NHTSA 01-022-N11B-8039, Saab Cars USA 2000-10-13, Saab Model Year 2001 VIN information, text layer",
                    "'Gearbox: 5 = 5-Speed Manual, 8 = 4-Speed Automatic'; car line D = 9-3, E = 9-5; model year 1 = 2001."),
    "saab5676": mid("7024b658-09b1-4e31-8585-78498998fff3",
                    "NHTSA ORG5676, Saab Cars North America 2010-03-04, '2010 Saab 9-3 and 9-5 Vehicle Identification Number', OCR",
                    "'Pos. 7 Gearbox: A 6-speed automatic/Front wheel drive, B 6-speed automatic/All wheel drive, C 5-speed automatic/Front wheel drive, M 6-speed manual/Front wheel drive, N 6-speed manual/All wheel drive'."),
    "saab5930": mid("0bea485d-6fec-4327-93f9-d7232bddabd1",
                    "NHTSA ORG5930, Saab Cars North America 2010-07-15, '2011 Saab 9-3 and 9-5 Vehicle Identification Number', OCR",
                    "'Pos. 7 Gearbox: A 6-speed automatic/Front wheel drive, B 6-speed automatic/All wheel drive, C 5-speed automatic/Front wheel drive, M 6-speed manual/Front wheel drive, N 6-speed manual/All wheel drive'; B = 2011."),
    "saab7108": mid("be63e5b8-5420-47f5-b4e5-8049e55e4a9b",
                    "NHTSA ORG7108, Saab Automobile AB 2011-09-14, '2012 Saab 9-3 and 9-5 Vehicle Identification Number (07-20-2011)', OCR",
                    "'Pos. 7 Gearbox: A 6-speed automatic/FWD, B 6-speed automatic/AWD, M 6-speed manual/FWD, N 6-speed manual/AWD'."),
    "fhi2006": mid("63662431-fe07-4d49-a90e-60db7c2b4db3",
                   "NHTSA ORG225, Fuji Heavy Industries USA 2005-02-23, 2006MY Subaru VIN breakdown, OCR",
                   "Lists WMI JF1/4S3/4S4 only (no JF4, no Saab). Digit 11 'Plant of manufacturer and transmission type': FHI G = AWD 5MT, H = AWD 4AT. No MID filing covers the Saab 9-2X (WMI JF4)."),
    # --- Land Rover ---------------------------------------------------------
    "lr5389": mid("08a8745a-1420-42ec-b4ab-e2c49090ab99",
                  "NHTSA 01-22-N11B-5389, Land Rover North America 1992-04-24, Range Rover VIN breakdown MY1993, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8* = 5 Speed Manual Trans'; model year P = 1993; plant A = Solihull."),
    "lr5284": mid("358abbc7-a12e-4e0c-9aee-404e711d7842",
                  "NHTSA 01-22-N11B-5284, Land Rover North America 1993-05-26, VIN breakdown MY1994, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8 = 5 Speed Manual Trans'; R = 1994."),
    "lr5839": mid("9afd275e-8d84-42c2-9009-8a50fc25859f",
                  "NHTSA 01-22-N11B-5839, Land Rover 1994-10-17, VIN breakdown MY1995, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8 = 5 Speed Manual Trans'; S = 1995."),
    "lr5983": mid("49667183-1c42-4f1b-b4e6-393d5bfd69a9",
                  "NHTSA 01-22-N11B-5983, Land Rover 1995-07-11, VIN breakdown MY1996, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8 = 5 Speed Manual Trans'; T = 1996."),
    "lr6164": mid("805d556c-109a-40dc-9ebb-de20b565bc5c",
                  "NHTSA 01-22-N11B-6164, Land Rover 1996-07-15, VIN breakdown MY1997, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8 = 5 Speed Manual Trans'; V = 1997."),
    "lr6343": mid("aeb0d20e-9d0e-4b19-8c8d-f697d70ddfb7",
                  "NHTSA 01-22-N11B-6343, Land Rover 1997-07-01, VIN breakdown MY1998, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans, 8 = 5 Speed Manual Trans'; W = 1998."),
    "lr6903": mid("e20c8300-1583-4301-afa3-52b081d7aa44",
                  "NHTSA 01-22-N11B-6903, Land Rover 1998-07-22, VIN breakdown MY1999, OCR",
                  "'8 Transmission Type: 4 = 4 Speed Automatic Trans' (no manual code from MY1999)."),
    "lr9576": mid("aae6a306-4384-4620-8d23-0d944e4231a2",
                  "NHTSA 01-022-N11B-9576, Land Rover North America 2003-05-30, VIN code MY2004, text layer",
                  "'8 Transmission Type - Discovery and Range Rover: 4 = Automatic Trans; Transmission Type - Freelander: 2 = 5 SP Automatic'."),
    # --- Volvo ----------------------------------------------------------------
    "volvo3486": mid("728f683f-71e9-4236-8e23-2fa51733ec9f",
                     "NHTSA 01-22-N11B-3486, Volvo Cars of North America 1989-06-29, VIN codes MY1990, OCR",
                     "Pos. 4 Vehicle Series, 5 Restraint System, 6-7 Engine Version (69 B280F, 87 B230FT, 88 B230F, 89 B234F), 8 Body Version (2/4/5-door). No transmission position."),
    "volvo5240": mid("0ad0a668-ee02-4a0f-924a-eef1c0ce81bf",
                     "NHTSA 01-22-N11B-5240, Volvo Cars of North America 1993-06-22, VIN codes 1994 model year, OCR",
                     "Pos. 4 L = 850 Series; Pos. 6-7 Engine Version with TRANS. column and Pos. 8 emissions: '55 = B5254S (Man.Only) 30/39 0'; '55 = B5254S (Auto 31/39) (Man.31) 1'. Pos. 8 0 = Federal (non Calif) w/o EGR Bosch."),
    "volvo5705": mid("4daf9234-6f86-46f1-a4d0-7cde6d3c7fbc",
                     "NHTSA 01-22-N11B-5705, Volvo Cars of North America 1994-07-22, VIN codes 1995 model year, OCR",
                     "Engine version / emissions (Pos. 8) / transmission: 55 B5254S 0 (Man. Only) 30/31*/39; 55 B5254S 1 (Auto Only); 55 B5254S 3 (Auto Only); 57 B5234T 0 (Man. Only-CDN); 57 B5234T 1 (Auto Only); 58 B5234T5 1 (Auto Only); 83 B230FD, 86 B230FT, 93 B6254S, 96 B6304S: 1 (Auto Only)."),
    "volvo6019": mid("66e65503-ec7a-45cd-a044-2a622b9adbdc",
                     "NHTSA 01-22-N11B-6019, Volvo Cars of North America 1995-11-27, VIN codes 1996 model year (revised), OCR",
                     "51 B5252S 0 (Man/Auto CDN); 55 B5254S 4 (Man. Only) 31,39; 55 B5254S 5 (Auto Only) 30,39; 55 B5254S 4 (Auto Only) 31; 57 B5234T 0 (Man. Only CDN); 57 B5234T 2 (Auto Only); 58 B5234T5 0 (Man. Only CDN); 58 B5234T5 2 (Auto Only); 96 B6304S2 0 (Auto Only). The earlier 7/95 sheet (01-22-N11B-5976) gives 55/1 Auto Only. 55/4 is listed both ways, so it is not ruled."),
    "volvo6353": mid("ce2aecbd-a016-4e6c-a473-75c7597dfb69",
                     "NHTSA 01-22-N11B-6353, Volvo 1997-05-15, VIN codes 1998 model year, OCR",
                     "52 B5234T6 4 (V70R-AWD Auto. Only); 53 B5234T3 4/7 (Auto. and Man.); 55 B5254S 4 (Auto. and Man.); 55 B5254S 7, 3, 8 (Auto. Only); 56 B5254T 4, 7 (Auto. Only); 56 B5254T 0 (V70AWDM Canada); 96 B6304S 0 (Auto. Only)."),
    "volvo6213": mid("ab2a9875-3fe5-47ef-8439-fac4e4ebfcb7",
                     "NHTSA 01-022-N11B-6213, Volvo 1996-12-20, VIN codes 1997 and 1998 model year, OCR",
                     "53 B5234T3 4 (Auto. and Man.); 55 B5254S 4 (Auto. and Man.); 55 B5254S 3 (Auto. Only); 56 B5254T 4 (Auto. Only); 56 B5254T 0 (V70AWDM Canada); 96 B6304S 0 (Auto. Only)."),
    "volvo6928": mid("f9fcfea8-ec1d-4ad7-af90-42df973152de",
                     "NHTSA 01-22-N11B-6928, Volvo 1998-07-28, VIN codes 1999 model year, OCR",
                     "53 B5234T3 D (Auto. and Man.); 55 B5254S A (Auto. and Man.); 56 B5254T D (Auto. Only, incl. AWD); 62 B5234T8 D (V70 R AWD Auto. Only); 90 B6284T6 D and 97 B6304S D (Auto. Only)."),
    "volvo9010": mid("55d4bcb5-f23e-433e-9682-4dc937810e18",
                     "NHTSA 01-022-N11B-9010, Volvo 2002-05-06, VIN code 2003 model year, text layer",
                     "Engine versions annotated per model: 27/29 S40/V40 Automatic Only; 53 S60/V70 Automatic/Manual; 58, 59, 63, 91, 92 Automatic Only; 61 Automatic/Manual; 62 C70 Automatic/Manual; 64 Automatic Only in CA, NY, MA, VT, ME. Pos. 8 is the emissions code."),
    "volvo4321": mid("5d683b5b-d22c-49b7-82e4-19da55edbc72",
                     "NHTSA ORG4321, Volvo Car USA 2008-07-22, VIN decoder MY2009, OCR",
                     "Pos 6-7 engine version with availability notes (38 B5244S4 automatic only all states except listed; 54, 59, 85, 98, 99 Automatic Only; 67 B5254T7 automatic plus manual); Pos 8 emissions. No transmission position."),
    # --- BMW / MINI -----------------------------------------------------------
    "bmw4023": mid("9a7499b9-89c1-446f-a03c-733d9b0458ef",
                   "NHTSA 01-22-N11B-4023, BMW of North America 1989-09-01, BMW Vehicle Identification Manual (September 1989 update), 'US Serial Number Ranges 1964 through present date', OCR (same pages in 01-22-N11B-3611 and -3811)",
                   "Heading descriptions: 'MODEL ... Suffixes explained as follows: A Automatic Transmission'; 'AG CODE Model identification code, appears in 4th through 7th digits of VIN'. Tables per model year, e.g. 1987: 325is/2 AA13, 325is A/2 AA23, 325i/4 AD13, 325i A/4 AD23, 325ic BB13, 325ic A BB23, 528e DK73, 528e A DK83, 535is/535i DC74, 535is A/535i A DC84; 1989-1990: 525i HC13, 525i A HC23, 535i HD13, 535i A HD23, 735i GB33, 735i A GB43, 735iL A GC43, 750iL A GC83, M3 AK03."),
    "bmw9505": mid("f23bd433-2a27-4e23-8242-b2d5f5e9063c",
                   "NHTSA 01-022-N11B-9505, BMW of North America 2003-01-27, 2003 Model Year Information to all State Motor Vehicle Departments (update 03-03): 'Model Codes and VIN Decipherment' and 'Serial Number Ranges (Std./Auto.)', page image",
                   "Positions 4-8: 525i 0356 D T 3 3 4; 525iA 0357 D T 4 3 4; 530i 0350 D T 5 3 4; 530iA 0355 D T 6 3 4; 540i 0353 D N 5 3 4; 540iA 0358 D N 6 3 4; M5 0351 (WBS) D E 9 3 4; 525iT 0354 D S 3 3 4; 525iAT 0359 D S 4 3 4; 540iAT 0369 D R 6 3 4. 3 Series (e.g. 325i E V 3 3 4), X5 3.0i (F A 5 3 5), Z4 2.5i (B T 3 3 4), MINI Cooper (R C 3 3 4) and Cooper S (R E 3 3 4) have one code each. Serial ranges: Cooper 0310 Std. TC38579- / Auto. TE13267-; Cooper S 0311 Std. TD57850- with no Auto. range ('*NO TRANSMISSION TYPE FOR MODEL'); M5 0351 Std. only; 525i/530i/540i Std. only, 525iA/530iA/540iA Auto. only."),
    "bmw8210": mid("e147be52-0647-4469-9a01-71b7389ec148",
                   "NHTSA 01-022-N11B-8210, BMW 2000-01-04 (filed by BMW M GmbH / BMW), VIN Decipherments for 2001 model year BMW models, text layer",
                   "Per-model tables list the same E39 code pairs: 525i 'DT33 or DT43', 525i Sport Wagon 'DS33 or DS43', 530i 'DT53 or DT63', 540i 'DN53 or DN63', 540i Sport Wagon 'DR63'. E46 323i 'AV33 or AN37' (no transmission split)."),
    "bmw7012": mid("8ab54247-29e8-4159-8591-420242598a7a",
                   "NHTSA 01-22-N11B-7012, Bayerische Motoren Werke AG 1998-10-26, Decipherment of BMW VINs for the 1999 model year, OCR",
                   "'Table for 540i Sedan - 1999 Model Year': 'DN53 or DN63', Series 540i, 4-Door Sedan, 282 BHP; 'Table for 528i Sedan - 1999': 'DM53 or DM63' (no transmission named)."),
    "bmw4769": mid("2c89d29d-ff17-470c-8775-4212d577d857",
                   "NHTSA 01-22-N11B-4769, BMW AG 1991-07-24, VIN decipherments for MY1992 (325iC, 535i, M5, 735i, 735iL, 750iL, 850i), OCR",
                   "Lists the code pairs without naming the transmission (e.g. 325iC 'BB13 or BB23', 850i 'EG13 or EG23')."),
    "bmw5023": mid("cedbdce3-d37e-46d2-88b4-3b8eef05f260",
                   "NHTSA 01-22-N11B-5023, BMW AG 1993-03-05, VIN decipherment for MY1994 530i, 530i Touring, 540i, 730i, OCR",
                   "'Table for 530i MY 1994: HE13 or HE23', 4-Door Sedan, 215 BHP (no transmission named)."),
    "mini8594": mid("1d9053bb-9297-47a0-87b5-b83206c9ebd8",
                    "NHTSA 01-022-N11B-8594, BMW of North America 2002-02-25, VIN Decipherments for 2002 Model Year MINI Models, text layer",
                    "'Table for MINI Cooper S - 2002 Model Year': WMW RE33, Series Cooper S, 2-Door Hatchback, 161 BHP 1.6 liter; model year 2 = 2002; plant Oxford. No transmission named."),
    "mini4565": mid("0d8e9a59-681b-4225-adc6-6b6e5a8d9535",
                    "NHTSA ORG4565, BMW of North America 2008-12-11, VIN Decipherments for 2009 Model Year MINI models, page image",
                    "MINI MODEL YEAR 2009 decipherment, positions 4-7: Cooper M F 3 3; Cooper S M F 7 3; JCW* Hardtop M F 9 3 (205 BHP); Cooper Clubman M L 3 3; Cooper S Clubman M M 3 3; JCW* Clubman M M 9 3; Cooper Convertible M R 3 3; Cooper S Convertible M S 3 3. '*JCW = John Cooper Works'. No transmission column."),
    "mini7370": mid("c3862d77-2eae-4f51-9f90-7a79ce5c5bf0",
                    "NHTSA ORG7370, BMW of North America 2011-12-01, VIN Decipherments for 2012 Model Year MINI models, page image",
                    "MINI MODEL YEAR 2012 decipherment, positions 4-7: Cooper Hardtop S U 3 C; Cooper S Hardtop S V 3 C; JCW* Hardtop S V 9 C (206 BHP); Clubman Z F 3 C / Z G 3 C / JCW Z G 9 C; Convertible Z N 3 C / Z P 3 C / JCW Z P 9 C; Countryman Z B 3 C / Z C 3 C / All4 Z C 5 C; Coupe S X 1 C / Cooper S Coupe S X 3 C / JCW* Coupe S X 5 C. No transmission column."),
    "mini9501": mid("9f5f301a-3e4b-41ae-bd9f-51159333049a",
                    "NHTSA 01-022-N11B-9501, BMW 2002-10-30, Complete packet of VIN decipherments for 2003 model year MINI Cooper and Cooper S, text layer",
                    "Cooper S tables keep type RE33 (no transmission split)."),
    # --- Volkswagen -------------------------------------------------------------
    "vw10541": mid("beedfa70-210b-4945-9347-7b8b29020530",
                   "NHTSA ORG10541, Volkswagen Group of America 2006-10-11, Volkswagen VIN Breakdown 2006 Model Year (Revision 13), text layer",
                   "Position 4 Series: new GTI 2-dr E = man. trans., F = auto. trans; Rabbit A (2 dr) / C (4 dr) man. trans., B / D auto. trans; Passat A = 2.0T / 3.6L auto. trans, G = 2.0T man. trans., E = 2.0T / 3.6L auto. trans w/Luxury Pkg. Jetta, Golf, New Beetle, Touareg codes are trim/package only. Positions 7-8: 1K Jetta / new GTI / Rabbit, 3C Passat."),
    "vw10543": mid("403644c5-8d21-4dc3-a90d-75efe146a3fd",
                   "NHTSA ORG10543, Volkswagen Group of America (dated 2006-06-23, Revision 7 of 23 Jan 2008), Volkswagen VIN Breakdown 2007 Model Year, text layer",
                   "Position 4: Rabbit A/C man., B/D auto.; GTI E (2 dr) / G (4 dr) man. trans., F / H auto. trans; Eos A man., B auto., C Sport man., D Sport auto., F Luxury auto.; Passat J auto., U manual, A auto., G man., E auto. w/Luxury, K man. w/Luxury, C auto. w/Sport, H man. w/Sport; Passat Wagon X auto., Y man., L auto., N man., T auto. w/Luxury, W man. w/Luxury, S man. w/Sport. Jetta and New Beetle codes are trim only."),
    "vw10545": mid("14e196ec-9877-4352-8986-97bfbf7dfb61",
                   "NHTSA ORG10545, Volkswagen Group of America 2008-01-12, Volkswagen VIN Breakdown 2008 Model Year (Revision 3), text layer",
                   "Position 4: Rabbit A/C man., B/D auto.; GTI E/G man., F/H auto.; Eos A Turbo/Komfort man., B Turbo/Komfort auto., F Lux auto.; Passat J Turbo auto., U Turbo man., A Komfort auto., E Lux auto.; Passat Wagon X Turbo auto., Y Turbo man., L Komfort auto., T Lux auto. Jetta (J/H/R), GLI and New Beetle codes are trim only."),
    "vw10547": mid("51bbc5e2-e426-45cb-956b-c21cd15d9bdc",
                   "NHTSA ORG10547, Volkswagen Group of America 2009-02-27, Volkswagen VIN Breakdown 2009 Model Year (Revision 3a), text layer",
                   "Position 4: Rabbit A/C man., B/D auto.; GTI E/G man., F/H auto.; Eos A man., B auto., F Lux auto.; CC M Sport auto., N Sport man., H Luxury auto.; Passat J/X Komfort (no transmission). Jetta, Jetta SportWagen, GLI, New Beetle codes are trim only."),
    "vw10549": mid("aa2dd01d-5420-4117-bc9e-777b8f26c016",
                   "NHTSA ORG10549, Volkswagen Group of America 2010-01-01, Volkswagen VIN Breakdown 2010 Model Year (Revision 2.5), text layer",
                   "Position 4: Golf A (2 dr) / C (4 dr) 5 Spd. man. trans., B / D auto. trans, M / N 6 Spd. man. trans.; GTI E / G man. trans., F / H auto. trans; CC M Sport auto., N Sport man., H Luxury auto.; Eos A Turbo/Komfort man., B auto., F Lux auto. Positions 7-8: AJ Golf/GTI/Jetta, AH Eos, AN CC/Passat. Jetta codes are trim only."),
    "vw10532": mid("2e8c2d8a-fd61-4c33-96a7-a47eeeb0f00e",
                   "NHTSA ORG10532, Volkswagen Group of America 2005-05-18, Volkswagen VIN Breakdown 2004 Model Year (Revision 12), text layer",
                   "Position 4 'Series' is a trim (Golf GL/GLS, Jetta GL/GLS/GLI, New Beetle GL/GLS/GLX/Turbo S, Passat GL/GLS/GLX/W8), 5 engine type, 6 restraint, 7-8 model. No transmission position."),
    "vw10553": mid("5729e845-5410-4af3-b7f6-b30d5025b840",
                   "NHTSA ORG10553, Volkswagen Group of America (dated 2005-03-12), Volkswagen VIN Breakdown 2012 Model Year, text layer",
                   "Passat (NMS) position 4: A = S, B = SE, C = SEL (trim, no transmission)."),
    "audi10538": mid("6b8c7264-1a20-425f-8c7d-24835a7d4b9c",
                     "NHTSA ORG10538, Volkswagen Group of America 2005-03-21, Audi VIN Breakdown 2005 Model Year, text layer",
                     "Position 4 series (e.g. TT S Coupe, T Roadster, W Coupe quattro, U Roadster quattro; A4 trims), 5 engine, 6 restraint, 7-8 model. No transmission column (the 2006-2009 Audi breakdowns are the same)."),
    "audi15449": mid("3bcf47eb-0242-4dc3-aad6-007fdcc4c669",
                     "NHTSA ORG15449, Volkswagen Group of America 2018-03-12, Audi VIN Breakdown 2018 Model Year, text layer",
                     "Position 4 Series table has a 'Trans' column ('A' = Automatic, 'M' = Manual), e.g. A4 quattro Premium D = A, N = M; A5 Coupe quattro Premium N = A, K = M."),
    # --- Mercedes / Porsche ---------------------------------------------------
    "mb12600": mid("06e13e64-bc34-4f2b-9401-3ce9602c042f",
                   "NHTSA ORG12600, Mercedes-Benz Cars 2016-03-18, VIN decoding table, text layer",
                   "Columns WMI, 'First 4 of second VIN section' (e.g. WF4J C300 4-Door Sedan), make, model, body, engine (displacement, cylinders, an automatic gear count such as 'L-7', fuel). Positions 4-7 identify the model; no manual/automatic code."),
    "porsche9555": mid("224328ec-0317-42c0-9810-6d0290bf5318",
                       "NHTSA 01-022-N11B-9555, Porsche Cars North America 2003-07-29, 2004 Model Year VIN decipherability information, text layer",
                       "VDS fields: Line, Body Type, Restraint System, Engine (and GVWR 'man.-auto.' for Cayenne). No transmission position."),
    "porsche4020": mid("8f7a6e1f-d900-4759-b9d5-6adacc952f08",
                       "NHTSA 01-22-N11B-4020, Porsche Cars North America 1989-09-21, VIN information, OCR",
                       "No transmission field in the VIN description."),
    # --- independent sources ----------------------------------------------------
    "epa": web(EPA_URL, "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29, sha256 33d32caa...b22f), downloaded 2026-11-05",
               "One row per certified model/engine/transmission configuration; 'trany' gives the transmission. Row ids are cited per rule."),
    "motorweek_r53": web("https://motorweek.org/road_tests/2002_mini_cooper_s_program_2204",
                         "MotorWeek road test 'Program #2204: 2002 Mini Cooper S' (found 2026-11-05 via web search; quoted from the search result, page not fetched)",
                         "'the S sports a sharp-shifting 6-speed manual transmission. No automatic is available or wanted.'"),
    "fastcar_r53": web("https://www.fastcar.co.uk/tuning-tech-guides/mini-cooper-s-r53-buyers-guide/",
                       "Fast Car, MINI Cooper S R53 buyer's guide (search result 2026-11-05)",
                       "The six-speed automatic arrived as a new option with the mid-life (LCI) facelift of September 2004 / April 2005."),
    "motoringfile_r53": web("https://reddit.birdcat.cafe/r/MINI/wiki/Buyers-Guide/R50-R53",
                            "r/MINI buyer's guide R50/R53 (Motoring File based; search result 2026-11-05)",
                            "'in 2005, a conventional 6-speed automatic transmission was available as an option' (for the Cooper S)."),
}

# ---------------------------------------------------------------------------
# Rules. Each rule: WMI list, model-year range, fixed characters, the decision
# characters ('pos' = 1-based start, 'len' = length), and the code table
# {code: (claim, meaning, [years])}. A rule fires only when the code is in its
# table for that model year; other codes get no claim.
# 'status_flag': "candidate" forces candidate (not counted) with the reason.
# ---------------------------------------------------------------------------
_SAAB_88_01 = yrs(1988, 2001)
_BMW_AG = {
    # code: (claim, model, years)  from BMW NA 'US Serial Number Ranges' (01-22-N11B-4023)
    "AG33": (M, "320i", yrs(1981, 1983)), "AG43": (A, "320i A", yrs(1981, 1983)),
    "EB35": (M, "633CSi", [1981]), "EB45": (A, "633CSi A", [1981]),
    "EB36": (M, "633CSi", [1982]), "EB46": (A, "633CSi A", [1982]),
    "EB74": (M, "633CSi", yrs(1983, 1984)), "EB84": (A, "633CSi A", yrs(1983, 1984)),
    "FF33": (M, "733i", [1981]), "FF43": (A, "733i A", [1981]),
    "FF34": (M, "733i", [1982]), "FF44": (A, "733i A", [1982]),
    "FF74": (M, "733i", yrs(1983, 1984)), "FF84": (A, "733i A", yrs(1983, 1984)),
    "DK73": (M, "528e", yrs(1982, 1988)), "DK83": (A, "528e A", yrs(1982, 1988)),
    "DB74": (M, "533i", yrs(1983, 1984)), "DB84": (A, "533i A", yrs(1983, 1984)),
    "AK74": (M, "318i (2-door)", yrs(1984, 1985)), "AK84": (A, "318i A (2-door)", yrs(1984, 1985)),
    "AC74": (M, "318i/4", [1985]), "AC84": (A, "318i A/4", [1985]),
    "AB54": (M, "325e / 325 / 325es 2-door", yrs(1984, 1988)), "AB64": (A, "325e A / 325 A / 325es A 2-door", yrs(1984, 1988)),
    "AE54": (M, "325e / 325 4-door", yrs(1985, 1988)), "AE64": (A, "325e A / 325 A 4-door", yrs(1985, 1988)),
    "DB24": (A, "524td A", yrs(1985, 1986)),
    "DC74": (M, "535i / 535is", yrs(1985, 1988)), "DC84": (A, "535i A / 535is A", yrs(1985, 1988)),
    "EC74": (M, "635CSi", yrs(1985, 1989)), "EC84": (A, "635CSi A", yrs(1985, 1989)),
    "FH74": (M, "735i", yrs(1985, 1986)), "FH84": (A, "735i A", yrs(1985, 1987)),
    "FG24": (A, "L7 A", yrs(1986, 1987)),
    "AA13": (M, "325is / 325i 2-door", yrs(1987, 1990)), "AA23": (A, "325is A / 325i A 2-door", yrs(1987, 1990)),
    "AD13": (M, "325i/4", yrs(1987, 1990)), "AD23": (A, "325i A/4", yrs(1987, 1990)),
    "BB13": (M, "325ic (Cabrio)", yrs(1987, 1990)), "BB23": (A, "325ic A (Cabrio)", yrs(1987, 1990)),
    "EE14": (M, "M6", yrs(1987, 1988)),
    "AB93": (M, "325iX/2", yrs(1988, 1990)), "AB03": (A, "325iX A/2", yrs(1988, 1990)),
    "AE93": (M, "325iX/4", yrs(1988, 1990)), "AE03": (A, "325iX A/4", yrs(1988, 1990)),
    "AK03": (M, "M3", yrs(1988, 1990)),
    "DC93": (M, "M5", [1988]),
    "GB33": (M, "735i", yrs(1988, 1990)), "GB43": (A, "735i A", yrs(1988, 1990)),
    "GC43": (A, "735iL A", yrs(1988, 1990)), "GC83": (A, "750iL A", yrs(1988, 1990)),
    "HC13": (M, "525i", yrs(1989, 1990)), "HC23": (A, "525i A", yrs(1989, 1990)),
    "HD13": (M, "535i", yrs(1989, 1990)), "HD23": (A, "535i A", yrs(1989, 1990)),
}
_E39 = {
    "DT33": (M, "525i (model code 0356)", yrs(2001, 2003)), "DT43": (A, "525iA (0357)", yrs(2001, 2003)),
    "DT53": (M, "530i (0350)", yrs(2001, 2003)), "DT63": (A, "530iA (0355)", yrs(2001, 2003)),
    "DS33": (M, "525iT (0354)", yrs(2001, 2003)), "DS43": (A, "525iAT (0359)", yrs(2001, 2003)),
    "DN53": (M, "540i (0353)", yrs(1999, 2003)), "DN63": (A, "540iA (0358)", yrs(1999, 2003)),
    "DR63": (A, "540iAT (0369)", yrs(2001, 2003)),
}


def _tab(d):
    return {k: (v[0], v[1], v[2]) for k, v in d.items()}


RULES = [
    {
        "id": "saab_ys3_char7_gearbox_1988_2001", "make": "Saab", "wmi": ["YS3"], "years": (1988, 2001),
        "fixed": {}, "pos": 7, "len": 1, "basis": "transmission_code",
        "models": "Saab 900 (classic and NG), 9000, 9-3 (1999-2001), 9-5 (1999-2001)",
        "codes": {"5": (M, "5-speed manual", _SAAB_88_01),
                  "6": (A, "3-speed automatic (900; listed MY1988-1994)", yrs(1988, 1994)),
                  "8": (A, "4-speed automatic", _SAAB_88_01)},
        "cites": ["saab3046", "saab3986", "saab4735", "saab5368", "saab5385", "saab5627", "saab5866", "saab6702", "saab8039"],
        "notes": "Filings in MID cover MY1988-1990, 1992-1996, 1999 and 2001; every one lists position 7 'Gearbox' with 5 = 5-speed manual. MY1991, 1997-1998 and 2000 have no filing in MID and are included because the filings on both sides are identical for codes 5 and 8.",
        "epa": [],
    },
    {
        "id": "saab_ys3_char7_gearbox_2010_2012", "make": "Saab", "wmi": ["YS3"], "years": (2010, 2012),
        "fixed": {}, "pos": 7, "len": 1, "basis": "transmission_code",
        "models": "Saab 9-3, 9-5 (YS3 builds)",
        "codes": {"M": (M, "6-speed manual FWD", yrs(2010, 2012)), "N": (M, "6-speed manual AWD", yrs(2010, 2012)),
                  "A": (A, "6-speed automatic FWD", yrs(2010, 2012)), "B": (A, "6-speed automatic AWD", yrs(2010, 2012)),
                  "C": (A, "5-speed automatic FWD", [2010, 2011])},
        "cites": ["saab5676", "saab5930", "saab7108"], "notes": "", "epa": [],
    },
    {
        "id": "saab_ys3_char7_gearbox_2002_2009_vpic_only", "make": "Saab", "wmi": ["YS3"], "years": (2002, 2009),
        "fixed": {}, "pos": 7, "len": 1, "basis": "transmission_code",
        "models": "Saab 9-3 (2003+ Epsilon and 2002 9-3), 9-5",
        "codes": {"5": (M, "manual (vPIC)", yrs(2002, 2009)), "6": (M, "6-speed manual (vPIC)", yrs(2002, 2009)),
                  "7": (M, "manual (vPIC)", yrs(2002, 2009)),
                  "1": (A, "automatic (vPIC)", yrs(2002, 2009)), "2": (A, "automatic (vPIC)", yrs(2002, 2009)),
                  "8": (A, "automatic (vPIC)", yrs(2002, 2009)), "9": (A, "automatic (vPIC)", yrs(2002, 2009))},
        "cites": ["saab8039", "saab5676"],
        "status_flag": "MID holds no Saab filing for MY2002-2009; the code meanings here are vPIC's (code 6 meant a 3-speed automatic in the MY1988-1994 filings), so the table is not the manufacturer's own for these years",
        "notes": "vPIC decodes every lot YS3 VIN of these years, so the rule adds nothing; it documents the codes.",
        "epa": [],
    },
    {
        "id": "saab_9_2x_jf4_char11_subaru_scheme", "make": "Saab", "wmi": ["JF4"], "years": (2005, 2006),
        "fixed": {4: "G", 5: "G"}, "pos": 11, "len": 1, "basis": "transmission_code",
        "models": "Saab 9-2X (Subaru-built Impreza GG wagon, Gunma)",
        "codes": {"G": (M, "Gunma AWD 5MT (Subaru scheme)", yrs(2005, 2006)), "H": (A, "Gunma AWD 4AT (Subaru scheme)", yrs(2005, 2006))},
        "cites": ["fhi2006"],
        "status_flag": "no MID filing covers WMI JF4; the meaning is borrowed from Subaru's JF1 scheme, not stated for this WMI",
        "notes": "Positions 4-8 of the 9-2X VINs (GG616 / GG226) follow Subaru's Impreza wagon layout. A Subaru/Saab filing for JF4 would make this a keep rule (3 lot cars, all without transmission info).",
        "epa": [{"model": r"^9-2X", "displ": None, "years": yrs(2005, 2006), "claim": M}],
    },
    {
        "id": "landrover_sal_char8_transmission_1993_1998", "make": "Land Rover", "wmi": ["SAL"], "years": (1993, 1998),
        "fixed": {}, "pos": 8, "len": 1, "basis": "transmission_code",
        "models": "Range Rover (classic and P38A), Discovery Series I, Defender 90/110 (US)",
        "codes": {"8": (M, "5-speed manual", yrs(1993, 1998)), "4": (A, "4-speed automatic", yrs(1993, 1998))},
        "cites": ["lr5389", "lr5284", "lr5839", "lr5983", "lr6164", "lr6343", "lr6903", "lr9576"],
        "notes": "MY1999 and later Land Rover filings list automatic codes only at this position (4; Freelander 2 = 5-speed automatic in MY2004); later layouts move the transmission to other positions and list automatics only.",
        "epa": [],
    },
    {
        "id": "volvo_engine_emission_combination_1994_1999", "make": "Volvo", "wmi": ["YV1"], "years": (1994, 1999),
        "fixed": {}, "pos": 4, "len": 5, "codes_by_slice": (4, [(4, 1), (6, 3)]), "basis": "engine_code_sole_offering",
        "models": "850 / S70 / V70 / C70 / 960 / S90 / V90 / S80 (YV1)",
        "codes": {
            "L550": (M, "850 B5254S, emissions 0: 'Man. Only'", [1994, 1995]),
            "L570": (M, "850 B5234T, emissions 0: 'Man. Only - CDN'", [1995, 1996]),
            "L580": (M, "850 B5234T5, emissions 0: 'Man. Only CDN'", [1996]),
            "L551": (A, "850 B5254S, emissions 1: 'Auto Only'", [1995]),
            "L553": (A, "850/S70/V70 B5254S, emissions 3: 'Auto Only'", [1995, 1997, 1998]),
            "L555": (A, "850 B5254S, emissions 5: 'Auto Only'", [1996]),
            "L571": (A, "850 B5234T, emissions 1: 'Auto Only'", [1995]),
            "L572": (A, "850 B5234T, emissions 2: 'Auto Only'", [1996]),
            "L581": (A, "850 B5234T5, emissions 1: 'Auto Only'", [1995]),
            "L582": (A, "850 B5234T5, emissions 2: 'Auto Only'", [1996]),
            "J831": (A, "940 B230FD: 'Auto Only'", [1995]), "J861": (A, "940 B230FT: 'Auto Only'", [1995]),
            "K931": (A, "960 B6254S: 'Auto Only'", [1995]), "K961": (A, "960 B6304S: 'Auto Only'", [1995]),
            "K960": (A, "960 B6304S2: 'Auto Only'", [1996, 1997, 1998]),
            "L564": (A, "S70/V70 B5254T emissions 4: 'Auto Only'", [1997, 1998]),
            "L567": (A, "S70/V70 B5254T emissions 7: 'Auto Only'", [1998]),
            "L557": (A, "S70/V70 B5254S emissions 7: 'Auto Only'", [1998]),
            "L558": (A, "S70/V70 B5254S emissions 8: 'Auto Only'", [1998]),
            "L524": (A, "V70R AWD B5234T6: 'Auto Only'", [1998]),
            "L56D": (A, "S70/V70 B5254T emissions D: 'Auto Only'", [1999]),
            "L62D": (A, "V70 R AWD B5234T8: 'Auto Only'", [1999]),
            "T90D": (A, "S80 B6284T6: 'Auto Only'", [1999]), "T97D": (A, "S80 B6304S: 'Auto Only'", [1999]),
        },
        "cites": ["volvo5240", "volvo5705", "volvo6019", "volvo6213", "volvo6353", "volvo6928", "volvo3486", "volvo9010"],
        "notes": "Not a transmission position: the filing annotates which engine-version (positions 6-7) + emissions (position 8) combinations were certified with which transmission. Decision characters = position 4 (series) + positions 6-8. Codes the filings mark 'Auto. and Man.' (e.g. 1994 55/1, 1997-1999 53/4, 55/4, 53/D, 55/A) and the 1996 55/4 (listed both 'Man. Only' and 'Auto Only') get no claim. 1997 code 3 (55/3) is also 'Auto Only'.",
        "epa": [{"model": r"^850", "displ": 2.4, "years": [1994, 1995], "claim": M, "mode": "offered"}],
    },
    {
        "id": "bmw_ag_code_1981_1990", "make": "BMW", "wmi": ["WBA", "WBS"], "years": (1981, 1990),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code",
        "models": "E21 320i, E23 733i/735i, E24 633CSi/635CSi/M6, E28 524td/528e/533i/535i/M5, E30 318i/325e/325/325i/325is/325ic/325iX/M3, E32 735i/735iL/750iL, E34 525i/535i",
        "codes": _tab(_BMW_AG),
        "cites": ["bmw4023"],
        "notes": "BMW gave the automatic its own AG (type) code; the manual defines the code as 'Model identification code, appears in 4th through 7th digits of VIN' and the 'A' model suffix as 'Automatic Transmission'. Only codes and model years printed in the manual are used. OCR misreads (e.g. 'AEG4', 'Dc84') were resolved against the page images and the code pattern of the same table.",
        "epa": [],
    },
    {
        "id": "bmw_e39_ag_code_1999_2003", "make": "BMW", "wmi": ["WBA"], "years": (1999, 2003),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code",
        "models": "E39 525i, 530i, 540i sedans; 525i and 540i Sport Wagons",
        "codes": _tab(_E39),
        "cites": ["bmw9505", "bmw8210", "bmw7012"],
        "notes": "The MY2003 DMV package names each code (525i DT3 / 525iA DT4 ...). The same code pairs are listed for the same models in BMW's MY2001 filing (DT33/DT43, DS33/DS43, DT53/DT63, DN53/DN63) and MY1999 filing (DN53/DN63), so the meaning is applied to those years. 528i (DD/DM, MY1997-2000) and 540i DE53/DE63 (MY1997-1998) are not named in any BMW document in MID: see bmw_e39_528i_540i_1997_2000_vpic_only.",
        "epa": [],
    },
    {
        "id": "bmw_e39_528i_540i_1997_2000_vpic_only", "make": "BMW", "wmi": ["WBA"], "years": (1997, 2000),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code",
        "models": "E39 528i (DD 1997-1998, DM 1999-2000), 540i (DE 1997-1998)",
        "codes": {"DD53": (M, "528i (pair partner of DD63)", [1997, 1998]), "DD63": (A, "528i automatic (vPIC)", [1997, 1998]),
                  "DE53": (M, "540i (pair partner of DE63)", [1997, 1998]), "DE63": (A, "540i automatic (vPIC)", [1997, 1998]),
                  "DM53": (M, "528i (pair 5/6 as DT/DN)", [1999, 2000]), "DM63": (A, "528i (pair 5/6 as DT/DN)", [1999, 2000])},
        "cites": ["bmw7012"],
        "status_flag": "BMW's own documents in MID list these pairs without naming the transmission; the meaning rests on vPIC (DD63/DE63 decode as Automatic) and on the 5/6 pattern of the MY2003 codes",
        "notes": "", "epa": [],
    },
    {
        "id": "bmw_m5_e39_manual_only", "make": "BMW", "wmi": ["WBS"], "years": (2000, 2003),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code_sole_offering",
        "models": "E39 M5",
        "codes": {"DE93": (M, "M5 (0351): Std. serial range only", yrs(2000, 2003))},
        "cites": ["bmw9505", "epa"],
        "notes": "BMW lists only a Std. (manual) serial range for M5 0351.",
        "epa": [{"model": r"^M5$", "displ": 4.9, "years": yrs(2000, 2003), "claim": M}],
    },
    {
        "id": "mini_cooper_s_r53_re33_2003_2004", "make": "MINI", "wmi": ["WMW"], "years": (2003, 2004),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code_sole_offering",
        "models": "MINI Cooper S hardtop (R53)",
        "codes": {"RE33": (M, "Cooper S (model code 0311)", [2003, 2004])},
        "cites": ["bmw9505", "mini9501", "epa", "fastcar_r53", "motoringfile_r53"],
        "notes": "Type RE33 covers both transmissions from MY2005 (EPA 21546 Automatic (S6)), so the rule stops at MY2004. EPA rows 19297 (2003) and 19408 (2004): Manual 6-spd only.",
        "epa": [{"model": r"^Cooper S$", "displ": 1.6, "years": [2003, 2004], "claim": M}],
    },
    {
        "id": "mini_cooper_s_r53_re33_2002", "make": "MINI", "wmi": ["WMW"], "years": (2002, 2002),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code_sole_offering",
        "models": "MINI Cooper S hardtop (R53), first model year",
        "codes": {"RE33": (M, "Cooper S", [2002])},
        "cites": ["mini8594", "motorweek_r53", "fastcar_r53", "bmw9505"],
        "status_flag": "EPA's file has no MY2002 Cooper S row, so the EPA sole-offering check cannot run for this year; the manual-only fact rests on a road test (MotorWeek: 'No automatic is available') and on the automatic's 2005 introduction",
        "notes": "Strong candidate: same type code and car as MY2003, for which BMW lists no automatic and EPA lists only the manual.",
        "epa": [{"model": r"^Cooper S$", "displ": 1.6, "years": [2002], "claim": M}],
    },
    {
        "id": "mini_john_cooper_works_2009_2012", "make": "MINI", "wmi": ["WMW"], "years": (2009, 2012),
        "fixed": {}, "pos": 4, "len": 4, "basis": "model_code_sole_offering",
        "models": "MINI John Cooper Works Hardtop, Clubman (2009, 2012), Convertible and Coupe (2012)",
        "codes": {"MF93": (M, "JCW Hardtop (205 BHP)", [2009]), "MM93": (M, "JCW Clubman (205 BHP)", [2009]),
                  "SV9C": (M, "JCW Hardtop (206 BHP)", [2012]), "ZG9C": (M, "JCW Clubman (206 BHP)", [2012]),
                  "ZP9C": (M, "JCW Convertible (206 BHP)", [2012]), "SX5C": (M, "JCW Coupe (206 BHP)", [2012])},
        "cites": ["mini4565", "mini7370", "epa"],
        "notes": "Type codes from BMW's MINI MY2009 and MY2012 decipherment tables (page images). MY2010-2011 JCW codes were not transcribed (no lot car carries one); MS93 (MY2009, not in BMW's MY2009 table) gets no claim. EPA: John Cooper Works 25401 (2009), 31645 (2012); JCW Clubman 25417, 31672; JCW Convertible 31646; JCW Coupe 31631, all Manual 6-spd; the first automatic JCW rows are MY2013.",
        "epa": [{"model": r"^John Cooper Works( Clubman| Convertible| Coupe)?$", "displ": 1.6, "years": [2009, 2012], "claim": M}],
    },
    {
        "id": "vw_wvw_char4_series_transmission_2006_2010", "make": "Volkswagen", "wmi": ["WVW"], "years": (2006, 2010),
        "fixed": {}, "pos": 4, "len": 1, "key_slice": [(4, 1), (7, 2)], "basis": "transmission_code",
        "models": "Rabbit, new GTI (Mk5/Mk6), Golf (2010), Eos, Passat B6 sedan and wagon (2006-2008), CC (2009-2010)",
        "codes": {
            # Rabbit / GTI (1K, 2006-2009; AJ 2010)
            "A1K": (M, "Rabbit 2 dr man. trans.", yrs(2006, 2009)), "C1K": (M, "Rabbit 4 dr man. trans.", yrs(2006, 2009)),
            "B1K": (A, "Rabbit 2 dr auto. trans", yrs(2006, 2009)), "D1K": (A, "Rabbit 4 dr auto. trans", yrs(2006, 2009)),
            "E1K": (M, "GTI 2 dr man. trans.", yrs(2006, 2009)), "F1K": (A, "GTI 2 dr auto. trans", yrs(2006, 2009)),
            "G1K": (M, "GTI 4 dr man. trans.", yrs(2007, 2009)), "H1K": (A, "GTI 4 dr auto. trans", yrs(2007, 2009)),
            "AAJ": (M, "Golf 2 dr 5 Spd. man. trans.", [2010]), "CAJ": (M, "Golf 4 dr 5 Spd. man. trans.", [2010]),
            "BAJ": (A, "Golf 2 dr auto. trans", [2010]), "DAJ": (A, "Golf 4 dr auto. trans", [2010]),
            "MAJ": (M, "Golf 2 dr 6 Spd. man. trans.", [2010]), "NAJ": (M, "Golf 4 dr 6 Spd. man. trans.", [2010]),
            "EAJ": (M, "GTI 2 dr man. trans.", [2010]), "GAJ": (M, "GTI 4 dr man. trans.", [2010]),
            "FAJ": (A, "GTI 2 dr auto. trans", [2010]), "HAJ": (A, "GTI 4 dr auto. trans", [2010]),
            # Eos (1F 2007-2009, AH 2010)
            "A1F": (M, "Eos man. trans.", yrs(2007, 2009)), "B1F": (A, "Eos auto. trans", yrs(2007, 2009)),
            "C1F": (M, "Eos Sport man. trans.", [2007]), "D1F": (A, "Eos Sport auto. trans", [2007]),
            "F1F": (A, "Eos Luxury auto. trans", yrs(2007, 2009)),
            "AAH": (M, "Eos man. trans.", [2010]), "BAH": (A, "Eos auto. trans", [2010]), "FAH": (A, "Eos Lux auto. trans", [2010]),
            # Passat B6 (3C 2006-2008)
            "A3C": (A, "Passat 2.0T/3.6L auto. trans (2006-07) / Komfort auto. (2008)", yrs(2006, 2008)),
            "E3C": (A, "Passat auto. trans w/Luxury (2006-07) / Lux auto. (2008)", yrs(2006, 2008)),
            "G3C": (M, "Passat 2.0T man. trans.", [2006, 2007]),
            "J3C": (A, "Passat auto. (2007) / Turbo auto. (2008)", [2007, 2008]),
            "U3C": (M, "Passat manual (2007) / Turbo man. (2008)", [2007, 2008]),
            "K3C": (M, "Passat 2.0T man. w/Luxury", [2007]), "C3C": (A, "Passat 2.0T/3.6L auto. w/Sport", [2007]),
            "H3C": (M, "Passat 2.0T man. w/Sport", [2007]),
            "X3C": (A, "Passat Wagon auto. (2007) / Turbo auto. (2008)", [2007, 2008]),
            "Y3C": (M, "Passat Wagon man. (2007) / Turbo man. (2008)", [2007, 2008]),
            "L3C": (A, "Passat Wagon 2.0T/3.6L auto. (2007) / Komfort auto. (2008)", [2007, 2008]),
            "N3C": (M, "Passat Wagon 2.0T man.", [2007]), "T3C": (A, "Passat Wagon auto. w/Luxury (2007) / Lux auto. (2008)", [2007, 2008]),
            "W3C": (M, "Passat Wagon 2.0T man. w/Luxury", [2007]), "S3C": (M, "Passat Wagon 2.0T man. w/Sport", [2007]),
            # CC (3C 2009, AN 2010)
            "M3C": (A, "CC Sport auto. trans", [2009]),
            "MAN": (A, "CC Sport auto. trans", [2010]), "NAN": (M, "CC Sport man. trans.", [2010]), "HAN": (A, "CC Luxury auto. trans", [2010]),
        },
        "cites": ["vw10541", "vw10543", "vw10545", "vw10547", "vw10549", "vw10532"],
        "notes": "Decision characters = position 4 + positions 7-8 (model). WMI WVW only (Jetta, Jetta SportWagen and GLI use 3VW and their position 4 is a trim code). Codes the filings describe without a transmission (Passat 3.6L 4Motion, VR6, R32, Komfort 2009) get no claim. CC 2009 N (man.) and H (auto.) share the 3C model code with Passat codes of other years and are handled per year below.",
        "extra_codes": {(2009, "N3C"): (M, "CC Sport man. trans."), (2009, "H3C"): (A, "CC Luxury auto. trans")},
        "epa": [],
    },
]

# John Cooper Works (R56/R55/R57 family) MY2009-2012: added only when the BMW filing
# naming the type codes is read (see vin_rules_7.json -> not_encoded_or_not_ruled).

ANSWER = {
    "Volkswagen": "PARTLY ENCODED. Position 4 ('Series') carries the transmission for some lines from MY2006: Rabbit (A/C manual, B/D automatic, 2006-2009), new GTI (E/G manual, F/H automatic, 2006-2010), Eos (A/C manual, B/D/F automatic, 2007-2010), Passat B6 (2006-2008 sedan and wagon, e.g. G/U/K/H/Y/N/W/S manual), CC (N manual, M/H automatic, 2009-2010), Golf (A/C 5MT, M/N 6MT, B/D automatic, 2010); VW keeps this for Golf/GTI in later breakdowns. NOT ENCODED before MY2006 (MY2004-2005 breakdowns: position 4 is a trim such as GL/GLS/GLX) and NOT ENCODED for Jetta, Jetta SportWagen, GLI, New Beetle, Passat NMS (A/B/C = S/SE/SEL), Routan, Touareg, Tiguan in any breakdown read.",
    "Audi": "NOT ENCODED for MY2005-2009 (Audi VIN breakdowns: position 4 series, 5 engine, 6 restraint, 7-8 model; no transmission column). From the MY2010 breakdown on, the position 4 series table carries a 'Trans' column (A/M) for some series (e.g. MY2018 A4 quattro Premium D = automatic, N = manual). Not ruled here: no lot car without transmission info falls in a manual code of those years.",
    "BMW": "ENCODED BY MODEL CODE in two eras. MY1981-1990 (E21/E23/E24/E28/E30/E32/E34): BMW of North America's serial-number manual gives the automatic its own AG code (VIN positions 4-7), e.g. 325i/4 AD13 vs 325i A/4 AD23, 525i HC13 vs HC23. E39 5 Series MY1999-2003: 525i DT3x / 525iA DT4x, 530i DT5x / DT6x, 540i DN5x / DN6x, 525iT DS3x / DS4x (BMW MY2003 DMV package). NOT ENCODED for E46 3 Series (1999-2006), E53 X5, E83 X3, Z3/Z4, E60/E90 and later (one code covers both transmissions). E36 (1992-1999), E34 1991-1995, E31, 528i 1997-2000 codes come in pairs, but no BMW document in MID names which is the automatic.",
    "MINI": "NOT ENCODED: BMW's MY2003 table gives Cooper (RC33) and Cooper S (RE33) one type code each for both transmissions, and later type codes (MF33/MF73, SU3C/SV3C, ZB3C/ZC3C ...) likewise. Manual-only by model: Cooper S RE33 MY2003-2004 (BMW lists no automatic serial range; EPA Manual 6-spd only; automatic from MY2005), MY2002 candidate (no EPA row). John Cooper Works MY2009 (MF93 Hardtop, MM93 Clubman) and MY2012 (SV9C, ZG9C, ZP9C, SX5C) per BMW's MINI decipherment tables, manual-only per EPA (first automatic JCW rows are MY2013).",
    "Mercedes-Benz": "NOT ENCODED in any filing read (MY1980s-2021). Positions 4-6/4-7 are the model (e.g. WDD WF4J = C300 sedan); the MY2016+ tables give an automatic gear count in the engine description. US manuals (190E 2.3/2.6, C230/C320 Sport, SLK, C300 Sport, SLK250) share their model code with automatics. vPIC's 'manual' for every 1999-2000 SLK230 is a vPIC default (uniformCell), not VIN evidence.",
    "Volvo": "NOT ENCODED. MY1984-1993: 4 series, 5 restraint, 6-7 engine, 8 body. MY1994-2003 filings annotate engine-version + emissions combinations as Man. Only / Auto Only / both; the only US manual-only combination is the 850 B5254S with emissions code 0 (MY1994-1995, plus Canada-only B5234T/B5234T5 code 0). MY2004 on: engine versions annotated 'Automatic Only' or 'Automatic/Manual', no manual-only version.",
    "Saab": "ENCODED. Position 7 'Gearbox' in every Saab filing in MID: MY1988-2001 5 = 5-speed manual, 6 = 3-speed automatic (900, to MY1994), 8 = 4-speed automatic; MY2010-2012 M/N = 6-speed manual, A/B = 6-speed automatic, C = 5-speed automatic (MY2010-2011). MID has no Saab filing for MY2002-2009 (vPIC decodes these, codes 5/6/7 manual). Not Saab VINs: 9-7X (GM, 5S3, automatic only) and 9-2X (Subaru, JF4; no filing for JF4).",
    "Porsche": "NOT ENCODED in any filing read (MY1985-2021: line, body type, restraint system, engine; Cayenne lists a GVWR per transmission but no VIN code).",
    "Land Rover": "ENCODED MY1993-1998: position 8 'Transmission Type' 4 = 4-speed automatic, 8 = 5-speed manual. MY1999 on: the position lists automatics only (4; Freelander 2 = 5-speed automatic), and every lot car with a VIN already has a vPIC transmission.",
}

NOT_RULED = [
    {"make": "Mercedes-Benz", "years": "all", "why": "VIN does not encode the transmission; no model code is manual-only on the lots in a way EPA confirms."},
    {"make": "Porsche", "years": "all", "why": "VIN does not encode the transmission. Manual-only US models (944 Turbo/S2, 911 GT3) are not separable from the model codes filed, or have no lot car."},
    {"make": "Audi", "years": "2010+", "why": "Position 4 'Trans' column exists from the MY2010 breakdown; vPIC already decodes these and no lot car without transmission info has a manual code, so no rule was written in this pass."},
    {"make": "Volkswagen", "years": "2011+", "why": "Golf/GTI/Golf R position 4 keeps a transmission split in later breakdowns; vPIC already decodes these. Jetta, Passat NMS, Beetle, Tiguan, Routan, Touareg: not encoded."},
    {"make": "MINI", "years": "2010-2011 John Cooper Works; 2009 JCW Convertible", "why": "JCW type codes for MY2010-2011 were not transcribed (no lot car carries one). The lot's one MY2009 MS93 (vPIC: no trim) is not in BMW's MY2009 table, so it gets no claim."},
    {"make": "BMW", "years": "1991-1998 (E36, E34 1991-1995, E31, E32 1991-1994)", "why": "BMW's Part 565 filings list both codes of each pair ('HE13 or HE23') without naming the transmission, and no BMW serial-range manual after 1990 is in MID. vPIC decodes some of them (e.g. CD43, BG23 automatic; BG13 manual)."},
    {"make": "Volvo", "years": "1996 850 B5254S code 4", "why": "Listed in the same filing both as 'Man. Only' (markets 31, 39) and 'Auto Only' (market 31)."},
]


def _code_of(r: dict, vin: str) -> str:
    if r["id"].startswith("volvo_"):
        return vin[3] + vin[5:8]
    if "key_slice" in r:
        return "".join(vin[p - 1:p - 1 + n] for p, n in r["key_slice"])
    return vin[r["pos"] - 1:r["pos"] - 1 + r["len"]]


def classify(vin: str, year: int):
    """-> (rule, claim, code, meaning) or ('unknown_code', rule) when in scope but the code is not in its table."""
    scoped = None
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        scoped = scoped or r
        code = _code_of(r, vin)
        ex = r.get("extra_codes", {}).get((year, code))
        if ex:
            return (r, ex[0], code, ex[1])
        hit = r["codes"].get(code)
        if hit and year in hit[2]:
            return (r, hit[0], code, hit[1])
    return ("unknown_code", scoped) if scoped else None


def rule_regex(r: dict) -> str:
    """Regex for the rule's MANUAL codes (WMI, decision characters, model-year character)."""
    alts = []
    for code, (cl, _m, ys) in r["codes"].items():
        if cl != M or not ys or "_" in code:
            continue
        chars = ["."] * 17
        if r["id"].startswith("volvo_"):
            chars[3] = code[0]
            chars[5:8] = list(code[1:])
        elif "key_slice" in r:
            i = 0
            for p, n in r["key_slice"]:
                for k in range(n):
                    chars[p - 1 + k] = code[i]
                    i += 1
        else:
            for k, ch in enumerate(code):
                chars[r["pos"] - 1 + k] = ch
        for p, allowed in r["fixed"].items():
            chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
        yc = "".join(sorted({_YEAR_CODES[(y - 1980) % 30] for y in ys}))
        chars[9] = "[" + yc + "]" if len(yc) > 1 else yc
        alts.append("(" + "|".join(r["wmi"]) + ")" + "".join(chars[3:]))
    for (y, code), (cl, _m) in r.get("extra_codes", {}).items():
        if cl == M and "key_slice" in r:
            chars = ["."] * 17
            i = 0
            for p, n in r["key_slice"]:
                for k in range(n):
                    chars[p - 1 + k] = code[i]
                    i += 1
            chars[9] = _YEAR_CODES[(y - 1980) % 30]
            alts.append("(" + "|".join(r["wmi"]) + ")" + "".join(chars[3:]))
    return "^(" + "|".join(alts) + ")$" if alts else ""


# ---------------------------------------------------------------------------
# EPA (independent of vPIC)
# ---------------------------------------------------------------------------
class Epa:
    def __init__(self, path: Path):
        self.ok = path.exists()
        self.rows: list[dict] = []
        self.idx: dict[tuple[int, str, str], set[int]] = defaultdict(set)
        if not self.ok:
            return
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["make"] not in EPA_MAKES:
                    continue
                try:
                    y = int(r["year"])
                except ValueError:
                    continue
                mk = "MINI" if r["make"] == "Mini" else r["make"]
                r["make"] = mk
                i = len(self.rows)
                self.rows.append(r)
                for _lv, k in ep.epa_keys(r):
                    self.idx[(y, mk, k)].add(i)

    def rule_rows(self, make: str, spec: dict) -> list[dict]:
        out = []
        for r in self.rows:
            if r["make"] != make or int(r["year"]) not in spec["years"] or not re.search(spec["model"], r["model"]):
                continue
            if spec.get("displ") and (not r["displ"] or abs(float(r["displ"]) - spec["displ"]) > 0.051):
                continue
            out.append(r)
        return out

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


def parse_displ(engine: str) -> float | None:
    m = re.match(r"\s*(\d+(?:\.\d+)?)L", engine or "")
    return float(m.group(1)) if m else None


def _title(s: str) -> str:
    return s.title() if s and s.isupper() else s


VALIDATION_METHOD = (
    "Every lot car with a rule WMI, a 17-character VIN and a valid check digit is classified. The model year comes from VIN "
    "character 10 (the listing year only picks the 30-year cycle and must be within 2 years). A rule fires only when the VIN "
    "matches its WMI, years and fixed characters and its decision characters are in its table for that year; other codes get "
    "no claim. Ground truth = scraper/manual_detect/ground_truth.jsonl; uniformCell lines are unlabelled (counted separately), "
    "speeds-only lines are excluded, the rest are checkable: agree means (truth is manual) == (rule says manual). All "
    "VIN-bearing truth comes from vPIC, which NHTSA builds from the same manufacturer data, so agreement is partly circular; "
    "the per-car EPA union check (year, make, feed/vPIC model names, vPIC displacement: a manual claim is consistent when EPA "
    "lists a manual, an automatic claim when EPA lists a non-manual) and, for sole-offering rules, the EPA rows of the exact "
    "model (row ids; every rule year must have rows and all must be the claimed class) are the independent checks. Status: "
    "candidate (not counted) when status_flag is set (the code meaning is not the manufacturer's own for those years, or the "
    "EPA check cannot run); drop when >= 20 checkable and agreement < 0.995 or an EPA sole-offering check fails; low_sample "
    "when < 20 checkable (kept: the code meaning comes from the manufacturer's own VIN document); keep otherwise. "
    "newly_confirmed_manual counts lot cars at US yards with no published transmission (vehicle_extras trans empty) that a "
    "keep or low_sample rule calls manual; Canadian-yard cars are listed but not counted."
)


# ---------------------------------------------------------------------------
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

    fi = {f: i for i, f in enumerate(inv["fields"])}
    yards = inv["yards"]
    all_wmi = sorted({w for r in RULES for w in r["wmi"]})

    per_rule = {r["id"]: defaultdict(Counter) for r in RULES}
    examples = {r["id"]: defaultdict(list) for r in RULES}
    codes_seen = {r["id"]: Counter() for r in RULES}
    unknown_codes = defaultdict(Counter)
    scan = Counter()
    newly_manual, newly_auto, conflicts, canadian = [], [], [], []
    jetta06 = []
    make_cov = {m: Counter() for m in MAKES}

    for row in inv["vehicles"]:
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        fyear = row[fi["year"]]
        make = row[fi["make"]] or ""
        model = row[fi["model"]] or ""
        yinfo = yards[row[fi["yard"]]] if isinstance(row[fi["yard"]], int) else None
        yard = yinfo[0] if yinfo else ""
        ex = list(extras.get(vid) or []) + [""] * 5
        pub = ex[3] or ""
        pcls = tclass(pub)
        g = gt.get(vid)
        raw = cache.get(vin) if len(vin) == 17 else None
        dec = raw if isinstance(raw, dict) else None
        if make in MAKES:
            make_cov[make]["cars"] += 1
            make_cov[make]["no_trans_info"] += 0 if pub else 1
        if (len(vin) == 17 and vin[:3] == "3VW" and vin[6:8] == "1K" and vin[9] == "6" and pub
                and (ex[4] or "vin") == "vin" and vin[3] in "ACD"):
            jetta06.append({"id": vid, "vin": vin, "year": fyear, "model": model, "char4": vin[3],
                            "vpic_trim": (dec or {}).get("trim", ""), "published_trans": pub, "yard": yard})
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
            scan["out_of_rule_scope"] += 1
            continue
        if res[0] == "unknown_code":
            r = res[1]
            unknown_codes[r["id"]][f"{y}:{_code_of(r, vin)}"] += 1
            scan["in_scope_code_not_in_table"] += 1
            continue
        r, claim, code, meaning = res
        rid = r["id"]
        scan["covered"] += 1
        st = per_rule[rid]
        st[claim]["in_scope"] += 1
        codes_seen[rid][f"{y} {code}"] += 1
        if make in MAKES:
            make_cov[make]["covered_by_rule"] += 1
        displ = parse_displ((dec or {}).get("engine", "") or ex[2])
        if g is not None:
            gcls = g.get("transClass", "")
            if g.get("uniformCell"):
                st[claim]["uniform_cell_excluded"] += 1
                if (gcls == "manual") == (claim == M):
                    st[claim]["uniform_cell_would_agree"] += 1
            elif gcls in KNOWN:
                st[claim]["checkable"] += 1
                ok = (gcls == "manual") == (claim == M)
                st[claim]["agree" if ok else "disagree"] += 1
                if gcls == "manual":
                    st[claim]["checkable_gt_manual"] += 1
                if not ok and len(examples[rid]["disagree"]) < 10:
                    examples[rid]["disagree"].append({"id": vid, "vin": vin, "year": y, "model": model, "code": code,
                                                      "claim": claim, "ground_truth": g.get("trans"), "source": g.get("source")})
            else:
                st[claim]["speeds_only_excluded"] += 1
        if epa.ok:
            emake = "MINI" if make == "MINI" else (r["make"] if r["make"] in EPA_MAKES else make)
            names = [model, _title((dec or {}).get("model", ""))] + (["CC"] if meaning.startswith("CC") else [])
            cls = epa.classes(y, emake, names, displ)
            if cls is None:
                st[claim]["epa_no_match"] += 1
            elif (claim == M and "manual" in cls) or (claim == A and (cls - {"manual", "unknown", "other"})):
                st[claim]["epa_consistent"] += 1
            else:
                st[claim]["epa_conflict"] += 1
                if len(examples[rid]["epa_conflict"]) < 10:
                    examples[rid]["epa_conflict"].append({"vin": vin, "year": y, "make": make, "model": model,
                                                          "claim": claim, "epa_classes": sorted(cls)})
        if pub and pcls in KNOWN and (pcls == "manual") != (claim == M):
            conflicts.append({"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                              "code": f"{code}: {meaning}", "rule_claim": claim, "published_trans": pub,
                              "transSrc": ex[4] or "vin", "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        if not pub:
            why = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if "transmission" in dec and not dec.get("transmission")
                                                              else "vpic_trans_dropped_by_scraper" if dec.get("transmission") else "cache_old_schema")
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"{code}: {meaning}", "why_no_trans": why, "yard": yard}
            state = str(yinfo[2]) if yinfo and len(yinfo) > 2 else ""
            if state.upper() in CANADA:
                canadian.append(rec)
                st[claim]["no_trans_info_canadian_yard"] += 1
                continue
            st[claim]["no_trans_info"] += 1
            st[claim][f"no_trans_info_{why}"] += 1
            (newly_manual if claim == M else newly_auto).append(rec)

    # ---- assemble rules ----
    out_rules = []
    for r in RULES:
        rid = r["id"]
        st = per_rule[rid]
        tot = Counter()
        for cl in (M, A):
            tot.update(st[cl])
        chk, agr = tot["checkable"], tot["agree"]
        agreement = round(agr / chk, 4) if chk else None
        epa_rows, epa_ok = [], True
        for spec in r["epa"]:
            rows = epa.rule_rows(r["make"], spec) if epa.ok else []
            classes = sorted({ep.trany_class(x["trany"]) for x in rows})
            years_found = sorted({int(x["year"]) for x in rows})
            if spec.get("mode") == "offered":
                sole = bool(rows) and "manual" in classes
            else:
                sole = bool(rows) and (classes == ["manual"] if spec["claim"] == M else "manual" not in classes)
            missing = sorted(set(spec["years"]) - set(years_found))
            epa_ok = epa_ok and sole and not missing
            epa_rows.append({"model_regex": spec["model"], "displ": spec.get("displ"), "years": spec["years"],
                             "claim": spec["claim"], "check": "manual offered" if spec.get("mode") == "offered" else "sole offering",
                             "rows": [{"id": x["id"], "year": x["year"], "model": x["model"], "displ": x["displ"],
                                       "trany": x["trany"], "drive": x["drive"]} for x in rows],
                             "classes": classes, "missing_years": missing, "passes": sole and not missing})
        flag = r.get("status_flag")
        if flag:
            status, reason = "candidate", flag
        elif r["epa"] and not epa_ok:
            status, reason = "drop", "EPA rows for the rule's model do not support the claim every rule year"
        elif chk >= MIN_SAMPLE and agreement is not None and agreement < MIN_AGREEMENT:
            status, reason = "drop", f">= {MIN_SAMPLE} checkable cars and agreement {agreement} < {MIN_AGREEMENT}"
        elif chk < MIN_SAMPLE:
            status, reason = "low_sample", f"{chk} checkable cars (< {MIN_SAMPLE}); kept because the code meaning comes from the manufacturer's own VIN document"
        else:
            status, reason = "keep", f">= {MIN_SAMPLE} checkable cars and agreement >= {MIN_AGREEMENT}"
        man_codes = {c: f"{v[1]} (MY{min(v[2])}-{max(v[2])})" for c, v in r["codes"].items() if v[0] == M and v[2]}
        aut_codes = {c: f"{v[1]} (MY{min(v[2])}-{max(v[2])})" for c, v in r["codes"].items() if v[0] == A and v[2]}
        for (yy, c), (cl, mm) in r.get("extra_codes", {}).items():
            (man_codes if cl == M else aut_codes)[f"{c}@{yy}"] = f"{mm} (MY{yy})"
        if r["id"].startswith("volvo_"):
            chars = "position 4 (series) + positions 6-7 (engine version) + position 8 (emissions); code written as p4+p6p7p8"
        elif "key_slice" in r:
            chars = "position 4 (series) + positions 7-8 (model); code written as p4+p7p8"
        else:
            chars = f"positions {r['pos']}-{r['pos'] + r['len'] - 1}" if r["len"] > 1 else f"position {r['pos']}"
        out_rules.append({
            "id": rid, "make": r["make"], "status": status, "status_reason": reason, "basis": r["basis"],
            "claim": "manual for the manual codes; automatic (not manual) for the automatic codes" if aut_codes and man_codes
            else ("manual" if man_codes else "automatic (not manual)"),
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + (", ".join(f"position {p} in [{a}]" for p, a in r["fixed"].items()) or "none")]},
            "vin_condition": {"characters": chars, "manual_codes": man_codes, "automatic_codes": aut_codes},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"]],
            "notes": r.get("notes", ""),
            "epa_rows": epa_rows,
            "validation": {
                "lot_cars_in_scope": tot["in_scope"],
                "checkable": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_ground_truth_manual": tot["checkable_gt_manual"],
                "manual_claims": {k: st[M][k] for k in ("in_scope", "checkable", "agree", "disagree")},
                "automatic_claims": {k: st[A][k] for k in ("in_scope", "checkable", "agree", "disagree")},
                "uniform_cell_lines_excluded": tot["uniform_cell_excluded"],
                "uniform_cell_lines_that_would_agree": tot["uniform_cell_would_agree"],
                "speeds_only_excluded": tot["speeds_only_excluded"],
                "epa_per_car": {"consistent": tot["epa_consistent"], "conflict": tot["epa_conflict"], "no_match": tot["epa_no_match"]},
                "disagreement_examples": examples[rid]["disagree"],
                "epa_conflict_examples": examples[rid]["epa_conflict"],
            },
            "codes_seen_on_lots": dict(codes_seen[rid].most_common(40)),
            "in_scope_codes_not_in_table": dict(unknown_codes[rid].most_common(25)),
            "newly_confirmed_manual": st[M]["no_trans_info"],
            "newly_labelled_automatic": st[A]["no_trans_info"],
            "no_trans_info_breakdown": {k: v for k, v in tot.items() if k.startswith("no_trans_info_")},
        })

    counted = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    by_rule = {x["id"]: x["newly_confirmed_manual"] for x in out_rules}
    nm_counted = [x for x in newly_manual if x["rule"] in counted]
    nm_cand = [x for x in newly_manual if x["rule"] not in counted]
    prec = Counter()
    for x in out_rules:
        if x["status"] in ("keep", "low_sample"):
            v = x["validation"]["manual_claims"]
            prec["checkable"] += v["checkable"]
            prec["agree"] += v["agree"]
    allc = Counter()
    for x in out_rules:
        if x["status"] in ("keep", "low_sample"):
            allc["checkable"] += x["validation"]["checkable"]
            allc["agree"] += x["validation"]["agree"]

    out = {
        "worklist": 7,
        "makes": list(MAKES),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "generator": "scraper/manual_detect/vin_rules_7.py",
        "inputs": {"inventory": "docs/data/inventory_live.json", "extras": "docs/data/vehicle_extras.json",
                   "vin_cache": "docs/data/vin_decodes.json.gz", "ground_truth": "scraper/manual_detect/ground_truth.jsonl",
                   "epa": "scraper/manual_detect/epa/vehicles.csv (present)" if epa.ok else "missing: EPA checks skipped",
                   "mid_filings_read": "945 Part 565 filings (VW Group incl. Audi 287+59, BMW/MINI 263, Mercedes/Daimler 162, Volvo Car 87, Porsche 84, Land Rover/JLR 268 (LR-relevant subset), Saab 16, FHI 3), filed up to 2021; scanned ones OCR'd"},
        "answer": ANSWER,
        "vin_scheme": {
            "Saab": "YS3: 4 car line, 5 model series/restraint, 6 body, 7 GEARBOX, 8 engine, 10 year, 11 assembly line.",
            "Land Rover": "SAL (1993-1998): 4-5 model/line, 6 body, 7 engine, 8 TRANSMISSION TYPE, 10 year, 11 plant.",
            "BMW": "WBA/WBS/4US/5UX/WBX: 4-7 AG (type) code = model identification code; 10 year; 11 plant. Transmission is part of the model code only where BMW split it (see answer).",
            "MINI": "WMW: 4-7 type code (RC33 Cooper, RE33 Cooper S, ...), one code per model for both transmissions.",
            "Volkswagen": "4 series (trim; transmission for some lines MY2006+), 5 engine, 6 restraint, 7-8 model, 10 year, 11 plant.",
            "Audi": "4 series (with a Trans column MY2010+), 5 engine, 6 restraint, 7-8 model, 10 year, 11 plant.",
            "Volvo": "4 series, 5 body/restraint, 6-7 engine version, 8 emissions (1994-2003) or body (to 1993), 10 year, 11 factory.",
            "Mercedes-Benz": "4-6/4-7 model (e.g. WF4J C300 sedan), 8 restraint, 10 year, 11 plant.",
            "Porsche": "4 line/market, 5 body, 6 restraint/engine, 7-8 model type, 10 year, 11 plant.",
        },
        "not_encoded_or_not_ruled": NOT_RULED,
        "summary": {
            "rules": len(out_rules),
            "rules_by_status": dict(Counter(x["status"] for x in out_rules)),
            "newly_confirmed_manual_keep_and_low_sample_rules": len(nm_counted),
            "newly_confirmed_manual_candidate_rules_only": len(nm_cand),
            "newly_confirmed_manual_by_rule": by_rule,
            "newly_confirmed_manual_by_feed_make": dict(Counter(x["make"] for x in nm_counted)),
            "newly_labelled_automatic_keep_and_low_sample_rules": sum(1 for x in newly_auto if x["rule"] in counted),
            "canadian_yard_cars_not_counted": len(canadian),
            "ground_truth_precision_manual_claims_kept_rules": {
                "checkable": prec["checkable"], "agree": prec["agree"],
                "precision": round(prec["agree"] / prec["checkable"], 4) if prec["checkable"] else None},
            "ground_truth_agreement_all_claims_kept_rules": {
                "checkable": allc["checkable"], "agree": allc["agree"],
                "agreement": round(allc["agree"] / allc["checkable"], 4) if allc["checkable"] else None},
            "scan": dict(scan),
            "lot_coverage_by_feed_make": {m: dict(v) for m, v in make_cov.items()},
        },
        "validation_method": VALIDATION_METHOD,
        "rules": out_rules,
        "newly_confirmed_manual_cars": nm_counted,
        "candidate_rule_manual_cars": nm_cand,
        "newly_labelled_non_manual_cars": [x for x in newly_auto if x["rule"] in counted],
        "canadian_yard_cars": canadian,
        "published_label_conflicts": conflicts,
        "hub_findings": [
            {"id": "vpic_jetta_2006_rabbit_pattern",
             "finding": "vPIC decodes MY2006 Jetta VINs (WMI 3VW, model 1K) with position 4 A or C as 'Manual/Standard' and D as 'Automatic', and leaves every other Jetta letter blank. That is the Rabbit's scheme (WVW 1K: A/C man. trans., B/D auto. trans). VW's own MY2006 breakdown (ORG10541, Revision 13) lists Jetta position 4 as trims only: A = 2.0T, C = Diesel Special Ed. w/sunroof, D = 2.5 / TDI w/Package 2, and the 2.0T and TDI were sold with both transmissions. The published Manual badges on these cars are therefore not supported by the manufacturer's VIN scheme.",
             "published_manual_badges": sum(1 for x in jetta06 if tclass(x["published_trans"]) == "manual"),
             "published_automatic_labels": sum(1 for x in jetta06 if tclass(x["published_trans"]) == "automatic"),
             "suggested_action": "hub decision: treat vPIC transmission for 2006 Jetta (3VW...1K, char 4 A/C/D, model year 6) as a model-level default like VPIC_TRANS_DEFAULT_CELLS (drop the badge) unless an independent source confirms each car",
             "citation": C["vw10541"],
             "cars": jetta06},
            {"id": "mercedes_vpic_manual_defaults",
             "finding": "No Mercedes-Benz filing read encodes the transmission, so any vPIC 'manual' on a Mercedes VIN (e.g. the 1999-2000 SLK230 uniform cell, already dropped by VPIC_TRANS_DEFAULT_CELLS) is a model-level default, not VIN evidence. No published Mercedes manual badge remains on the lots."},
        ],
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    s = out["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}; newly confirmed manual (counted) {s['newly_confirmed_manual_keep_and_low_sample_rules']}, "
          f"candidate-only {s['newly_confirmed_manual_candidate_rules_only']}; precision {s['ground_truth_precision_manual_claims_kept_rules']}")
    for x in out_rules:
        v = x["validation"]
        print(f"  {x['id']:48s} {x['status']:10s} chk {v['checkable']:4d} agr {v['agreement']} man(chk {v['manual_claims']['checkable']}) "
              f"new_manual {x['newly_confirmed_manual']} new_auto {x['newly_labelled_automatic']} epa {v['epa_per_car']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
