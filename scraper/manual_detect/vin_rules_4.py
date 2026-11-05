#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 4: Ford, Lincoln, Mercury.

What Ford Motor Company's own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say:

  * NO Ford, Lincoln or Mercury VIN encodes the transmission. All 249 Ford
    Motor Company filings in MID were downloaded (MY1984-MY2028). The 125
    with a text layer (MY2000-2004 partly, MY2013-2028 fully) contain the
    word "transmission" once, in a cover letter about a GVWR coding error
    (01-022-N11B-8035). The scanned filings read as page images (MY1985,
    1987, 1993, 2001-2007, 2014) have the same layout: 1-3 WMI, 4 restraint
    (cars) or brake/GVWR (trucks), 5 make designator (cars: P Ford, M
    Lincoln/Mercury, T imported/non-Ford built) + 6-7 line/series/body
    (trucks: 5-7 line/series/chassis/body), 8 engine, 9 check digit,
    10 model year, 11 plant, 12-17 serial. No position or column names a
    transmission.
  * The only VIN-level evidence is indirect: an engine code (character 8)
    or a series code (characters 5-7) that Ford sold only with a manual.
    Each rule below names the filing that defines the code, the EPA rows
    that list only a manual for that engine/model (fueleconomy.gov
    vehicles.csv, independent of vPIC), and an independent text source.
    Where an independent source contradicts EPA (Ranger 2.0) the rule is a
    candidate and its cars are NOT counted.

Rule status: keep / low_sample rules are counted; candidate rules are
written but their cars are listed separately and not counted. "basis" is
engine_code or series_code (no Ford filing names a transmission).

Every rule is validated against ground_truth.jsonl (uniformCell lines are
treated as unlabelled), cross-checked against EPA, and counted for the lot
cars WITHOUT transmission info it would newly confirm as manual.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (optional, EPA cross-check).
Output: scraper/manual_detect/vin_rules_4.json

Run:  python3 -I scraper/manual_detect/vin_rules_4.py
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
import epa_profile as ep  # noqa: E402  (norm, epa_keys, feed_keys, trany_class)

OUT = HERE / "vin_rules_4.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
MAKES = ("Ford", "Lincoln", "Mercury")
M, A = "manual", "automatic"

# ---------------------------------------------------------------------------
# VIN helpers (same conventions as vin_rules_0/1/2)
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


def year_chars(years) -> str:
    out = []
    for y in sorted(years):
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


# ---------------------------------------------------------------------------
# Citations. MID files were downloaded 2026-11-05 (search API + displayfile);
# scanned ones were read as page images.
# ---------------------------------------------------------------------------
def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


def web(url: str, doc: str, says: str) -> dict:
    return {"url": url, "doc": doc, "says": says}


C = {
    # --- Ford Part 565 filings -------------------------------------------
    "f1985": mid("467ce8a2-d1db-4b76-b5fc-1675f6c32744",
                 "NHTSA 01-22-N11B-1724, Ford Motor Company 1984-05-30, '1985 Vehicle Identification Number Codes' (page image)",
                 "Attachment page 8, 'Engine Type (VIN Position 8)', LIGHT TRUCK/MPV: C = 2.0, 122 CID, I-4, Gasoline, Ford. No transmission position anywhere in the attachment."),
    "f1986": mid("19f76e38-6103-4cd2-845b-e3ca7ae41ed7",
                 "NHTSA 01-22-N11B-1942, Ford Motor Company 1985-06-07, 1986 VIN codes",
                 "Pages 2-18 failed to decode here (CCITT fax stream errors in the PDF); not read."),
    "f1987": mid("e1094195-4318-4205-9f3e-7b1a581e9755",
                 "NHTSA 01-22-N11B-2387, Ford Motor Company 1986-06-10, '1987 Vehicle Identification Number Codes' (page image)",
                 "Attachment page 8 'Engine Type (VIN Position 8)', LIGHT TRUCK/MPV: C = 2.0 IFM, 122 CID, I-4, Gasoline, Ford. Pages 3-7: line/series/body (positions 5-7). No transmission position."),
    "f1993": mid("0fa607e8-e5ab-49af-9b8c-ae9a827b656f",
                 "NHTSA 01-22-N11B-4649, Ford Motor Company 1992-11-11, '1993 Model Year VIN Codes - Amendments: Revision No. 2', attachment page 10 dated 1992-11-11 (page image)",
                 "Engine Type (VIN Position 8), PASSENGER CAR: Y = 3.0 EFI SHO, 182 CID, V-6, Gasoline, Yamaha, 220 hp; P = 3.2 EFI SHO, 195 CID, V-6, Yamaha, 220 hp; U = 3.0 EFI (Ford, 130-140 hp); 1 = 3.0 EFI-FFV; 6 = 1.6 EFI-TC I-4 (Turbo) Mazda 132 hp; Z = 1.6 EFI-DOHC Mazda 100 hp."),
    "f2001": mid("6e5e56bf-4fd5-46c7-87a4-4268ee76e089",
                 "NHTSA 01-022-N11B-8035, Ford Motor Company 2000-11-01, '2001 Model Year Vehicle Identification Number Codes - Revision No. 4' (19 pp, page image)",
                 "Section IV (Line, Series, Body Type, positions 6-7), MAKE-MERCURY: 60 = Cougar I4 3-Dr. Coupe, 61 = Cougar V6, 62 = Cougar High Output V6. Section VII Table 1 PASSENGER CAR: 3 = 2.0 EFI-ZETEC DOHC I-4 130 hp. Table 2 LIGHT TRUCK/MPV: B = 2.0 SEFI-ZETEC DOHC I-4; 1 = 3.0 SEFI-DOHC V-6. Cover letter item (2): 'Some 4X2 Ford Escapes and Mazda Tributes built with 2.0L engines and manual transmissions were coded in VIN position number 4 as 3001-4000 lb. GVWR class' (a GVWR coding note, not a transmission code)."),
    "f2002_rev2": mid("888d9009-afb5-4eb5-8ee0-f1c57396c0f9",
                      "NHTSA 01-022-N11B-8520, Ford Motor Company 2001-09-28, '2002 Model Year VIN Codes - Revision No. 2', cover letter (page image)",
                      "'\"B\", is the 2.0L SEFI-ZETEC, I-4, gasoline engine, used in the Escape and Tribute vehicles, \"1\" is the 3.0L SEFI-DOHC, V-6, gasoline engine, used in the Escape and Tribute vehicles'."),
    "f2002": mid("b0424777-deef-431a-9f44-e0c67183c777",
                 "NHTSA 01-022-N11B-8829, Ford Motor Company 2002-05-31, '2002 Model Year VIN Codes - Revision No. 4' (19 pp, page image)",
                 "Section III (position 5): P = Ford make, M = Lincoln or Mercury, T = imported / non-Ford-built passenger cars marketed by Ford. Section IV (positions 6-7): Focus 31 ZX3, 33 LX, 34 SE, 36 SE wagon, 37 ZX5, 38 ZTS, 39 ZX3 SVT; Mercury 60 = Cougar I4, 61 = Cougar V6, 62 = Cougar High Output V6. Section VII Table 1 PASSENGER CAR: 3 = 2.0 EFI-ZETEC DOHC I-4 125-130 hp; 5 = 2.0 EFI-ZETEC SVT I-4 170 hp; P = 2.0 EFI-SPI. Table 2 LIGHT TRUCK/MPV: B = 2.0 SEFI-ZETEC DOHC I-4 127 hp; 1 = 3.0 SEFI-DOHC V-6 201 hp."),
    "f2003": mid("a1f0a033-6e6a-45ac-8482-9c55ad6f8321",
                 "NHTSA 01-022-N11B-8756, Ford Motor Company 2002-03-08, '2003 Model Year Vehicle Identification Number Codes' (40 pp, page image)",
                 "2003 Ford Focus page: 3 = 2.0L DOHC ZETEC I-4 130 hp; 5 = 2.0L DOHC HP ZETEC I-4 170 hp; P = 2.0L SPI-EFI; P39 = Focus ZX3 SVT 3Dr-Coupe. 2003 Ford Escape page: 1 = 3.0L DOHC V-6 201 hp; the 2.0L Zetec I-4 127 hp row's code letter is clipped in the scan (B or E), so MY2003 code B is not ruled. U02/U03/U04 = XLS/XLT/Limited 4X2, U92/U93/U94 = 4X4."),
    "f2004": mid("0901de1c-afcc-4e58-9f40-5bd1830d5cac",
                 "NHTSA 01-022-N11B-9889, Ford Motor Company 2004-02-09, '2004 Model Year VIN Codes - Revision 4' (38 pp, page image)",
                 "2004 Ford Focus page: 3 = 2.0L DOHC ZETEC I-4 130 hp; 5 = 2.0L DOHC HP ZETEC I-4 170 hp; P = 2.0L SPI-EFI; Z = 2.3L DOHC PZEV I-4 144 hp; P30 = ZX5 SVT 5Dr, P39 = ZX3 SVT 3Dr. 2004 Ford Escape page: B = 2.0L Zetec I-4 127 hp; 1 = 3.0L DOHC V-6 201 hp; U02/U03/U04 XLS/XLT/Limited 4X2, U92/U93/U94 4X4."),
    "f2005": mid("f04d910d-9902-4e7a-bff1-009ae04fc9ce",
                 "NHTSA 01-022-N11B-9888, Ford Motor Company 2004-05-21, '2005 Model Year VIN codes - Revision #3' (37 pp, page image)",
                 "2005 Ford Focus page: N = 2.0L DOHC I-4 136 hp; N = 2.0L DOHC PZEV I-4 130 hp; Z = 2.3L DOHC PZEV I-4 151 hp; P31 ZX3, P34 ZX4, P36 ZXW, P37 ZX5, P38 = Focus ST 4-Dr. Sedan."),
    "f2006": mid("5cdbc314-0a3d-426e-9b99-ed56dcb3c39c",
                 "NHTSA ORG338, Ford Motor Company 2005-03-07, '2006 Model Year VIN Codes - Revision #2' (page image)",
                 "2006 Ford Focus page (attachment dated 2005-03-04): N = 2.0L DOHC PZEV I-4 130 hp; N = 2.0L DOHC ZETEC I-4 136 hp; Z = 2.3L DOHC I-4 151 hp; P31 ZX3, P34 ZX4, P36 ZXW, P37 ZX5, P38 = ST 4-Dr. Sedan."),
    "f2007": mid("fd65e666-0f41-462c-86d7-a7c1d161e534",
                 "NHTSA ORG2474, Ford Motor Company 2006-09-29, '2007 Model Year VIN Codes - Revision #5' (page image)",
                 "2007 Ford Focus page (attachment page 8 of 40): N = 2.0L DOHC I-4 130 hp; Z = 2.3L DOHC I-4 151 hp; P38 = Focus ST 4-Dr. Sedan."),
    "f2013": mid("f334b82e-64d4-4557-aa0b-fb8993293918",
                 "NHTSA ORG25021, Ford Motor Company 2025-11-24 refiling of the MY2013 VIN codes (pages dated 2012-07-20, text layer)",
                 "2013 Ford Focus: 2 = 2.0L GDI I4 159 hp, 4 = Electric, 9 = 2.0L GTDI I4 243 hp; P3L = FOCUS ST 5-Dr Hatch. 2013 Ford Mustang (WMI 1ZV): F = 5.0L 4V V8 420, M = 3.7L V6, Z = 5.8L SC DOHC 4V V8 650 hp, U = 5.0L DOHC 4V V8 444 hp; P8J = Shelby Coupe, P8K = Shelby Convertible. 2013 Fusion: R = 1.6L GTDI I4."),
    "f2014": mid("763285e4-3c0b-4879-8b5c-0be1f265fe66",
                 "NHTSA ORG8727, Ford Motor Company 2013-06-25, '2014 Model Year VIN Codes - Revision #2' (page image)",
                 "2014 Ford Fiesta: J = 1.6L TIVCT I4 120 hp, X = 1.6L GTDI I4, E = 1.0L GTDI I3; P4G = FIESTA ST 5-DR HATCH. 2014 Ford Focus: 2 = 2.0L GDI, 4 = Electric, 9 = 2.0L GTDI I-4 252 hp; P3L = FOCUS ST 5-DR HATCH. 2014 Ford Fusion: 7 = 2.5L, D = 1.5L, R = 1.6L GTDI I4 178 hp, U = 2.0L HEV, 9 = 2.0L GTDI. 2014 Ford Mustang (1ZV): F = 5.0L 4V V-8 420, M = 3.7L V-6, Z = 5.8L 4V V-8 662 hp; P8J = Shelby Coupe, P8K = Shelby Convertible."),
    "f2015": mid("1f714e28-25e3-4df9-86b8-419d9360ce8e",
                 "NHTSA ORG25018, Ford Motor Company 2025-11-24 refiling of the MY2015 VIN codes (text layer)",
                 "2015 Ford Fiesta: J = 1.6L TiVCT, X = 1.6L GTDI I4 197 hp, E = 1.0L GTDI I3; P4G = FIESTA ST. 2015 Ford Focus: 2 = 2.0L GDI, 9 = 2.0L GTDI 250 hp, E = 1.0L GTDI I-3; P3L = FOCUS ST. 2015 Mustang: Z = 5.2L TIVCT V-8 500 hp; P8J = Shelby Coupe."),
    "f2016": mid("c7e812c4-d5eb-4c22-b6ec-5f3231b7febb",
                 "NHTSA ORG25019, Ford Motor Company 2025-11-24 refiling of the MY2016 VIN codes (text layer)",
                 "2016 Ford Fiesta: X = 1.6L GTDI, E = 1.0L Fox GTDI; P4G = FIESTA ST (the hp column is transposed in this filing). 2016 Ford Focus: 9 = 2.0L GTDI 252 hp, E = 1.0L GTDI I-3 123 hp; P3L = FOCUS ST. 2016 Ford Focus RS (WMI WF0, Saarlouis): H = 2.3L GTDI I-4; P3T = FOCUS RS 5 DR HATCH. 2016 Mustang: Z = 5.2L TIVCT V-8; P8J = Shelby Coupe."),
    "f2017": mid("cbb561f5-810c-4157-8e6d-4f8242b384fa",
                 "NHTSA ORG25020, Ford Motor Company 2025-11-24 refiling of the MY2017 VIN codes (text layer)",
                 "2017 Fiesta: X = 1.6L GTDI 197 hp, E = 1.0L Fox GTDI 123 hp; P4G = ST. 2017 Focus: 9 = 2.0L GTDI 252 hp, E = 1.0L GTDI 123 hp; P3L = ST. 2017 Focus RS (WF0): H = 2.3L GTDI 350 hp; P3T = RS. 2017 Mustang: Z = 5.2L TIVCT V-8 526 hp; P8J = Shelby Coupe."),
    "f2018": mid("490f8b21-ba00-417f-9628-a2098fa5d209",
                 "NHTSA ORG25014, Ford Motor Company 2025-11-24 refiling of the MY2018 VIN codes (text layer)",
                 "2018 Fiesta: X = 1.6L GTDI 197 hp, E = 1.0L Fox GTDI; P4G = ST. 2018 Focus: 9 = 2.0L GTDI 252 hp, E = 1.0L GTDI; P3L = ST. 2018 Focus RS (WF0): H = 2.3L GTDI; P3T = RS. 2018 Mustang: Z = 5.2L TIVCT V-8 526 hp; P8J = Shelby Coupe."),
    "f2019": mid("21ccd043-81e4-4380-b1ee-4778dd3debb7",
                 "NHTSA ORG25017, Ford Motor Company 2025-11-24 refiling of the MY2019 VIN codes (text layer)",
                 "2019 Fiesta: J = 1.6L TiVCT, X = 1.6L GTDI, E = 1.0L Fox GTDI; P4D = FIESTA ST 5-DR HATCH and P4G = FIESTA ST 5-DR HATCH (on the lots P4D carries engine J, i.e. the 1.6 TiVCT 'ST-Line', so the ST rule keys on engine X). 2019 Mustang: 0 = 5.0L 4V V-8 480 hp, F = 5.0L TiVCT 460 hp, Z = 5.2L TIVCT 526 hp; P8K = Bullitt Coupe, P8J = Shelby Coupe."),
    "f2020": mid("87906d32-2802-421f-8c95-0fdb52067a5b",
                 "NHTSA ORG23802, Ford Motor Company 2024-11-26 refiling of the MY2020 VIN codes (text layer)",
                 "2020 Mustang: 0 = 5.0L 4V V-8, F = 5.0L TIVCT, J = 5.2L, Z = 5.2L TIVCT V-8 526 hp; P8K = Bullitt Coupe, P8J = Shelby Coupe, P8S = Shelby GT500 Coupe."),
    # --- independent text sources (read through web search result text, 2026-11-05) ----
    "edmunds_escape_2003": web("https://www.edmunds.com/ford/escape/2003/suv/review",
                               "Edmunds, 2003 Ford Escape review",
                               "'Standard on the Escape XLS 2WD is a 2.0-liter inline four-cylinder engine that makes 127 horsepower and 135 pound-feet of torque. It is matched to a five-speed manual transmission.'"),
    "edmunds_escape_2001": web("https://www.edmunds.com/ford/escape/2001/comparison-test.html",
                               "Edmunds, 2001 Ford Escape comparison test",
                               "The standard four-speed automatic came with the optional 3.0-liter Duratec V6."),
    "wiki_escape": web("https://en.wikipedia.org/wiki/Ford_Escape",
                       "Wikipedia, Ford Escape (first generation / Ford Maverick section)",
                       "'Only two versions were made, the 2.0 L Zetec inline-4 engine with manual transmission and 3.0 L Duratec V6 with automatic transmission'; North America: 2.0 L Zetec with a five-speed manual on the base XLS, V6 with a four-speed automatic."),
    "cg_cougar": web("https://consumerguide.com/used/1999-02-mercury-cougar/",
                     "Consumer Guide, 1999-02 Mercury Cougar used-car review",
                     "'Cougars came with two distinct engines: a 125-horsepower 4-cylinder (manual shift only), or a 170-horsepower 2.5-liter V6 that could be equipped either with a five-speed or with an optional 4-speed automatic transmission.'"),
    "svt_focus": web("https://www.ultimatecarpage.com/spec/1409/Ford-SVT-Focus.html",
                     "Ultimatecarpage SVT Focus spec page; Ward's Auto 'Ford's SVT changes Focus' (https://wardsauto.com/ford/ford-s-svt-changes-focus); MotorWeek 2002 SVT Focus road test",
                     "The SVT Focus's only gearbox is the Getrag 6-speed manual (MT-285); Ward's: the SVT Focus joins the SVT Mustang Cobra R as the only Ford product with a 6-speed gearbox. No source lists an automatic SVT Focus."),
    "cars_focus_2005": web("https://www.cars.com/research/ford-focus-2005",
                           "Cars.com, 2005 Ford Focus research page; The Auto Channel 'New Car Review: 2005 Ford Focus ZX4 ST' (https://theautochannel.com/news/2004/09/30/240175.html)",
                           "The ZX4 ST's 151 hp 2.3-liter 'is teamed only with a smooth shifting 5-speed manual'; the 2.3L Duratec was available only in ST models; the 2.0 (incl. the 2.0 PZEV Duratec 20E) took the 5-speed manual or 4-speed automatic."),
    "cg_focus_st": web("https://consumerguide.com/ford/2017-focus/",
                       "Consumer Guide, 2015 and 2017/2018 Ford Focus specifications",
                       "Turbocharged 2.0-liter 4-cylinder (ST), 252 hp: Std. Transmission 6-speed manual; Avail. Transmission NA."),
    "cars_focus_rs": web("https://www.cars.com/articles/articles-2015-02-ford-focus-rs-first-look/",
                         "Cars.com, Ford Focus RS first look (2015-02)",
                         "'more than 315-hp, turbocharged 2.3-liter EcoBoost four-cylinder, all-wheel drive, six-speed manual transmission only'."),
    "fiesta_st": web("https://www.guideautoweb.com/en/galleries/34838/2015-ford-fiesta-st-the-grass-is-greener-here/",
                     "Guide Auto Web, 2015 Ford Fiesta ST review",
                     "'The only transmission offered is a six-speed manual.'"),
    "cd_focus_10": web("https://www.edmunds.com/ford/focus/2016/review",
                       "Edmunds 2016 Ford Focus review; Car and Driver item 'previously manual-only Ford Focus 1.0L EcoBoost now available with automatic' (as quoted at https://foreverpontiac.com/forums/topic/8425-car-and-driver-previously-manual-only-ford-focus-10l-ecoboost-now-available-with-automatic/)",
                       "Edmunds: 'for 2016, the Ford Focus returns with ... a six-speed automatic transmission for the available 1.0-liter EcoBoost engine'. Car and Driver: the 1.0L Focus was 'previously available with only a six-speed manual transmission', and the smaller Fiesta 1.0L 'is still manual-only'."),
    "fusion_2014": web("https://www.cars.com/articles/2014-ford-fusion-whats-changed-1420663051662",
                       "Cars.com '2014 Ford Fusion: What's Changed'; Autobytel '2014 Ford Fusion gets a smaller engine' (https://www.autobytel.com/2014-ford-fusion-gets-a-smaller-engine)",
                       "SE models with the automatic swap the 1.6L EcoBoost for the new 1.5L EcoBoost; 'the 1.5 will be mated exclusively to automatic transmissions while the 1.6 will only be available with a manual gearbox'."),
    "gt500_2013": web("https://develop.motorbiscuit.com/5-best-manual-ford-mustang-models-recent-years-v8-fun-factories",
                      "MotorBiscuit, '5 best manual Ford Mustang models'",
                      "The S197 Shelby GT500 from 2013 or 2014 'offers just one transmission option: a TREMEC TR-6060 six-speed manual unit'."),
    "gt350": web("https://www.streetmusclemag.com/?p=1124648",
                 "Street Muscle, 'Lighter, Better Six-Speed Manual The Only Option For Shelby GT350'; InsideHook 'the last stick-shift Shelby Mustangs'",
                 "'only six-speed Tremec manual transmissions are available for the Mustang Shelby GT350 and GT350R'."),
    "sho": web("https://en.wikipedia.org/wiki/Ford_SHO_V6_engine",
               "Wikipedia, Ford SHO V6 engine / Ford Taurus SHO",
               "The 3.0 L SHO V6 continued with the MTX-IV 5-speed manual for 1993-1995; the 3.2 L version, introduced for 1993, was paired only with the AX4S 4-speed automatic."),
    "ranger_station": web("https://www.therangerstation.com/tech/ford-ranger-manual-transmissions/",
                          "The Ranger Station, Ford Ranger transmission guides",
                          "Conflicting evidence: '1985-1988 - Rangers with NON-overdrive automatic trans (essentially 2.0 carb engine ONLY) will be a C-3', i.e. some 2.0L Rangers had an automatic, which EPA does not list."),
    "epa": web(EPA_URL, "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29, sha256 33d32caa...b22f), row ids",
               "see each rule's epa_rows"),
}

# ---------------------------------------------------------------------------
# Rules. codes: {char: (claim, meaning, [model years])}; fixed: {position: allowed chars}
# epa: list of row filters for the independent sole-offering check
#      (years, model regex, displacement, charger "T"/"S"/"" or None = any)
# ---------------------------------------------------------------------------
def yrs(lo, hi):
    return list(range(lo, hi + 1))


RULES = [
    {"id": "ford_escape_2001_2004_char8_engine", "make": "Ford", "basis": "engine_code",
     "models": "Ford Escape (1st gen) MY2001-2004, every series (U0x 4x2 / U9x 4x4)",
     "wmi": ["1FM"], "years": (2001, 2004), "fixed": {5: "U", 6: "09"}, "pos": 8,
     "codes": {"B": (M, "2.0L SEFI-Zetec DOHC I-4, 127 hp: sold only with the 5-speed manual", [2001, 2002, 2004]),
               "1": (A, "3.0L SEFI-DOHC Duratec V-6, 201 hp: sold only with the 4-speed automatic", yrs(2001, 2004))},
     "cites": ["f2001", "f2002_rev2", "f2002", "f2003", "f2004", "edmunds_escape_2003", "edmunds_escape_2001", "wiki_escape"],
     "epa": [{"years": yrs(2001, 2004), "model": r"^Escape (2WD|4WD|FWD)$", "displ": 2.0, "claim": M},
             {"years": yrs(2001, 2004), "model": r"^Escape (2WD|4WD|FWD)$", "displ": 3.0, "claim": A}],
     "evidence_gaps": "MY2003 code B is not ruled: in the MY2003 filing (01-022-N11B-8756) the code letter of the 2.0L row is clipped (B or E). No 2003 Escape with code B is on the lots.",
     "notes": "The 2.0 Zetec code B is used only in the Escape and the Mazda Tribute (01-022-N11B-8520 cover letter); Mazda Tribute (WMI 4F2, Mazda make) belongs to worklist 1."},
    {"id": "ford_focus_svt_2002_2004_char8_engine", "make": "Ford", "basis": "engine_code",
     "models": "Ford SVT Focus (ZX3 SVT 2002-2004, ZX5 SVT 2003-2004)",
     "wmi": ["1FA", "3FA"], "years": (2002, 2004), "fixed": {5: "P", 6: "3"}, "pos": 8,
     "codes": {"5": (M, "2.0L DOHC HP (SVT) Zetec I-4, 170 hp: SVT Focus only, Getrag 6-speed manual only", yrs(2002, 2004))},
     "cites": ["f2002", "f2003", "f2004", "svt_focus"],
     "epa": [{"years": yrs(2002, 2004), "model": r"^Focus$", "displ": 2.0, "trany": r"6-spd", "claim": M}],
     "evidence_gaps": "EPA cannot separate the SVT engine from the other 2.0L Focus engines by displacement; its only 6-speed Focus rows (2002 id 17549 eng_dscr '2.0Z', 2003 18515, 2004 19578) are manuals, and no 6-speed automatic exists.",
     "notes": ""},
    {"id": "ford_focus_st_2005_2007_series_P38_char8_Z", "make": "Ford", "basis": "series_code",
     "models": "Ford Focus ZX4 ST / ST sedan MY2005-2007 (series P38 with the 2.3L engine)",
     "wmi": ["1FA", "3FA"], "years": (2005, 2007), "fixed": {5: "P", 6: "3", 7: "8"}, "pos": 8,
     "codes": {"Z": (M, "series P38 = Focus ST 4-Dr Sedan with the 2.3L DOHC I-4 151 hp: 5-speed manual only", yrs(2005, 2007))},
     "cites": ["f2005", "f2006", "f2007", "cars_focus_2005"],
     "epa": [{"years": yrs(2005, 2007), "model": r"^Focus", "displ": 2.3, "claim": M}],
     "evidence_gaps": "",
     "notes": "MY2003-2004 code Z is the 2.3L PZEV offered with both transmissions (EPA 18516/18517, 19579/19580); this rule starts at MY2005, when the PZEV engine became the 2.0L (code N) and the 2.3L went only into the ST. vPIC still calls 2005 P38 'ZTS'; the MY2005 filing says ST."},
    {"id": "ford_focus_st_2013_2018_series_P3L_char8_9", "make": "Ford", "basis": "series_code",
     "models": "Ford Focus ST MY2013-2018 (series P3L, 2.0L GTDI)",
     "wmi": ["1FA"], "years": (2013, 2018), "fixed": {5: "P", 6: "3", 7: "L"}, "pos": 8,
     "codes": {"9": (M, "series P3L = Focus ST 5-Dr Hatch with the 2.0L GTDI I-4 (243-252 hp): 6-speed manual only", yrs(2013, 2018))},
     "cites": ["f2013", "f2014", "f2015", "f2016", "f2017", "f2018", "cg_focus_st"],
     "epa": [{"years": yrs(2013, 2018), "model": r"^Focus", "displ": 2.0, "charger": "T", "claim": M}],
     "evidence_gaps": "", "notes": ""},
    {"id": "ford_focus_rs_2016_2018_series_P3T_char8_H", "make": "Ford", "basis": "series_code",
     "models": "Ford Focus RS MY2016-2018 (WMI WF0, Saarlouis)",
     "wmi": ["WF0"], "years": (2016, 2018), "fixed": {5: "P", 6: "3", 7: "T"}, "pos": 8,
     "codes": {"H": (M, "series P3T = Focus RS with the 2.3L GTDI I-4 (350 hp): 6-speed manual only", yrs(2016, 2018))},
     "cites": ["f2016", "f2017", "f2018", "cars_focus_rs"],
     "epa": [{"years": yrs(2016, 2018), "model": r"^Focus RS", "displ": 2.3, "claim": M}],
     "evidence_gaps": "", "notes": ""},
    {"id": "ford_focus_10_2015_char8_E", "make": "Ford", "basis": "engine_code",
     "models": "Ford Focus SE 1.0L EcoBoost, MY2015 only",
     "wmi": ["1FA"], "years": (2015, 2015), "fixed": {5: "P", 6: "3"}, "pos": 8,
     "codes": {"E": (M, "1.0L GTDI I-3 (EcoBoost): 6-speed manual only in MY2015 (automatic added for MY2016)", [2015])},
     "cites": ["f2015", "cd_focus_10"],
     "epa": [{"years": [2015], "model": r"^Focus", "displ": 1.0, "claim": M}],
     "evidence_gaps": "",
     "notes": "MY2016-2018 code E is NOT ruled: EPA lists Automatic (S6) for the 1.0L from 2016 (36988, 38469, 39607)."},
    {"id": "ford_fiesta_10_2014_2017_char8_E", "make": "Ford", "basis": "engine_code",
     "models": "Ford Fiesta SE 1.0L EcoBoost (SFE), MY2014-2017",
     "wmi": ["3FA"], "years": (2014, 2017), "fixed": {5: "P", 6: "4"}, "pos": 8,
     "codes": {"E": (M, "1.0L GTDI I-3 (Fox EcoBoost): 5-speed manual only in the US", yrs(2014, 2017))},
     "cites": ["f2014", "f2015", "f2016", "f2017", "cd_focus_10"],
     "epa": [{"years": yrs(2014, 2017), "model": r"^Fiesta", "displ": 1.0, "claim": M}],
     "evidence_gaps": "", "notes": "The MY2018-2019 filings still list code E, but EPA has no 1.0L Fiesta for 2018-2019; those years are outside the rule."},
    {"id": "ford_fiesta_st_2014_2019_char8_X", "make": "Ford", "basis": "engine_code",
     "models": "Ford Fiesta ST MY2014-2019 (1.6L GTDI)",
     "wmi": ["3FA"], "years": (2014, 2019), "fixed": {5: "P", 6: "4"}, "pos": 8,
     "codes": {"X": (M, "1.6L GTDI I-4 (197 hp), fitted only to the Fiesta ST: 6-speed manual only", yrs(2014, 2019))},
     "cites": ["f2014", "f2015", "f2016", "f2017", "f2018", "f2019", "fiesta_st"],
     "epa": [{"years": yrs(2014, 2019), "model": r"^Fiesta", "displ": 1.6, "charger": "T", "claim": M}],
     "evidence_gaps": "", "notes": "Keyed on the engine, not the series: the MY2019 filing also calls P4D 'ST', but P4D cars on the lots carry the 1.6 TiVCT (J) ST-Line."},
    {"id": "ford_fusion_16_2014_char8_R", "make": "Ford", "basis": "engine_code",
     "models": "Ford Fusion SE 1.6L EcoBoost, MY2014 only",
     "wmi": ["3FA", "1FA"], "years": (2014, 2014), "fixed": {5: "P", 6: "0"}, "pos": 8,
     "codes": {"R": (M, "1.6L GTDI I4, 178 hp: in MY2014 sold only with the 6-speed manual (automatic SEs got the new 1.5L, code D)", [2014])},
     "cites": ["f2014", "fusion_2014"],
     "epa": [{"years": [2014], "model": r"^Fusion", "displ": 1.6, "claim": M}],
     "evidence_gaps": "",
     "notes": "MY2013 code R is NOT ruled: EPA lists Manual 6-spd and Automatic (S6) for the 2013 1.6L (33084, 33085, 33280). 199 of the 200 lot Fusions with code R are MY2013."},
    {"id": "ford_mustang_gt500_2013_2014_char8_Z", "make": "Ford", "basis": "series_code",
     "models": "Ford Shelby GT500 MY2013-2014 (WMI 1ZV, series P8J/P8K)",
     "wmi": ["1ZV"], "years": (2013, 2014), "fixed": {5: "P", 6: "8", 7: "JK"}, "pos": 8,
     "codes": {"Z": (M, "Shelby Coupe/Convertible with the 5.8L supercharged V-8 (650-662 hp): TR-6060 6-speed manual only", yrs(2013, 2014))},
     "cites": ["f2013", "f2014", "gt500_2013"],
     "epa": [{"years": yrs(2013, 2014), "model": r"^Mustang", "displ": 5.8, "charger": "S", "claim": M}],
     "evidence_gaps": "", "notes": "Code Z means the 5.2L GT350 engine from MY2015; this rule is year-scoped."},
    {"id": "ford_mustang_gt350_2016_2020_char8_Z", "make": "Ford", "basis": "series_code",
     "models": "Ford Shelby GT350 / GT350R MY2016-2020 (WMI 1FA, series P8J)",
     "wmi": ["1FA"], "years": (2016, 2020), "fixed": {5: "P", 6: "8", 7: "J"}, "pos": 8,
     "codes": {"Z": (M, "Shelby Coupe with the 5.2L TiVCT flat-plane V-8 (526 hp): Tremec 6-speed manual only", yrs(2016, 2020))},
     "cites": ["f2016", "f2017", "f2018", "f2019", "f2020", "gt350"],
     "epa": [{"years": yrs(2016, 2020), "model": r"Shelby GT350", "displ": 5.2, "claim": M}],
     "evidence_gaps": "", "notes": "MY2015 (P8J + Z, 37 cars built) is outside the rule: EPA has no 2015 GT350 row. The MY2020 GT500 is P8S + J (dual-clutch, EPA AM7) and is not touched."},
    {"id": "ford_taurus_sho_1993_char8", "make": "Ford", "basis": "engine_code",
     "models": "Ford Taurus SHO MY1993",
     "wmi": ["1FA"], "years": (1993, 1993), "fixed": {5: "P"}, "pos": 8,
     "codes": {"Y": (M, "3.0 EFI SHO V-6 (Yamaha, 220 hp): 5-speed manual only", [1993]),
               "P": (A, "3.2 EFI SHO V-6 (Yamaha, 220 hp): 4-speed automatic only", [1993])},
     "cites": ["f1993", "sho"],
     "epa": [{"years": [1993], "model": r"Taurus SHO", "displ": 3.0, "claim": M},
             {"years": [1993], "model": r"Taurus SHO", "displ": 3.2, "claim": A}],
     "evidence_gaps": "", "notes": "MY1989-1992 and 1994-1995 SHOs carry the same engines, but no filing for those years was read; they are outside the rule. A listing-year-1997 Taurus with VIN year N (1992) and code Y is skipped by the year check."},
    {"id": "mercury_cougar_i4_2001_2002_series_60_char8_3", "make": "Mercury", "basis": "series_code",
     "models": "Mercury Cougar I4 coupe MY2001-2002 (WMI 1ZW, series T60)",
     "wmi": ["1ZW"], "years": (2001, 2002), "fixed": {5: "T", 6: "6", 7: "0"}, "pos": 8,
     "codes": {"3": (M, "series 60 = Cougar I4 3-Dr Coupe with the 2.0L Zetec DOHC I-4: 5-speed manual only", yrs(2001, 2002))},
     "cites": ["f2001", "f2002", "cg_cougar"],
     "epa": [{"years": yrs(2001, 2002), "model": r"^Cougar$", "displ": 2.0, "claim": M}],
     "evidence_gaps": "",
     "notes": "Engine code 3 alone is NOT enough: the same 2.0 Zetec code is used in the Focus and Escort ZX2, which had automatics. MY1999 is outside the rule (EPA 14999 lists a 2.0 Automatic 4-spd for the 1999 Cougar). MY2000: EPA manual only (15802), but no MY2000 filing was read and no MY2000 I4 Cougar is on the lots."},
    # --- candidates (written, NOT counted) ---------------------------------
    {"id": "ford_ranger_20_1985_1987_char8_C", "make": "Ford", "basis": "engine_code", "candidate": True,
     "models": "Ford Ranger 2.0L I-4 (light truck engine C), MY1985-1987",
     "wmi": ["1FT"], "years": (1985, 1987), "fixed": {5: "R"}, "pos": 8,
     "codes": {"C": (M, "2.0L I-4 (light truck table): EPA lists only manuals, but an independent source reports C3 automatics with the 2.0", yrs(1985, 1987))},
     "cites": ["f1985", "f1986", "f1987", "ranger_station"],
     "epa": [{"years": yrs(1985, 1987), "model": r"^Ranger", "displ": 2.0, "claim": M}],
     "evidence_gaps": "MY1986 filing (01-22-N11B-1942) did not decode; code C read from the MY1985 and MY1987 filings and vPIC's 2.0L decode.",
     "notes": "Candidate only: The Ranger Station says the 1985-1988 non-overdrive C-3 automatic was used 'essentially' behind the 2.0 carbureted engine. That contradicts EPA, so these cars are not counted."},
    {"id": "ford_mustang_bullitt_2019_2020_series_P8K", "make": "Ford", "basis": "series_code", "candidate": True,
     "models": "Ford Mustang Bullitt MY2019-2020 (series P8K, engine 0)",
     "wmi": ["1FA"], "years": (2019, 2020), "fixed": {5: "P", 6: "8", 7: "K"}, "pos": 8,
     "codes": {"0": (M, "P8K = Bullitt Coupe with the 5.0L 4V V-8 480 hp", yrs(2019, 2020))},
     "cites": ["f2019", "f2020"],
     "epa": [{"years": yrs(2019, 2020), "model": r"Mustang Bullitt", "displ": 5.0, "claim": M}],
     "evidence_gaps": "Only EPA (40327, 41995: 'Mustang Bullitt', Manual 6-spd only) was found; no independent text source was collected.",
     "notes": "Candidate: no lot car; kept for completeness."},
]

RULE_STATUS_NOTE = {
    "candidate": "not counted: the evidence does not meet the bar (see notes / evidence_gaps)",
    "low_sample": f"fewer than {MIN_SAMPLE} checkable ground-truth cars; kept because the code meaning comes from Ford's own Part 565 VIN filing and the manual-only fact from EPA plus an independent source",
    "keep": f">= {MIN_SAMPLE} checkable cars and agreement >= {MIN_AGREEMENT}",
    "drop": f"agreement below {MIN_AGREEMENT}",
}

ANSWER = {
    "Ford": ("NOT ENCODED. No Ford Motor Company Part 565 filing names a transmission: all 249 Ford filings in MID were downloaded "
             "(MY1984-2028); the 125 with a text layer mention 'transmission' once, in a cover-letter note about a GVWR code "
             "(01-022-N11B-8035), and the scanned filings read as page images (MY1985, 1987, 1993, 2001-2007, 2014) show no "
             "transmission position. Characters: 4 restraint (cars) / brake+GVWR (trucks), 5 make designator (cars) + 6-7 line/"
             "series/body, or 5-7 line/series/chassis/body (trucks), 8 engine, 10 year, 11 plant. Where an engine or series code "
             "belongs to a configuration Ford sold only with a manual, the code decides: Escape 2.0 Zetec (2001, 2002, 2004), SVT "
             "Focus (2002-2004), Focus ST sedan (2005-2007), Focus ST (2013-2018), Focus RS (2016-2018), Focus 1.0 EcoBoost (2015 "
             "only), Fiesta 1.0 EcoBoost (2014-2017), Fiesta ST (2014-2019), Fusion 1.6 EcoBoost (2014 only), Shelby GT500 "
             "(2013-2014), Shelby GT350 (2016-2020), Taurus SHO 3.0 (1993). Everything else (F-Series, Ranger, Explorer, Mustang "
             "GT/V6/EcoBoost, Focus/Fiesta base engines, Escape from 2005 ...) cannot be decided from the VIN."),
    "Lincoln": ("NOT ENCODED (Ford's scheme, same positions). No Lincoln engine or series code is manual-only: the only Lincoln with "
                "a manual in the period, the LS V6 (2000-2002, 5-speed), shares its 3.0L V6 engine code with the automatic LS, so "
                "the VIN cannot tell them apart. No Lincoln rule."),
    "Mercury": ("NOT ENCODED (Ford's scheme). One series+engine combination is manual-only: Cougar I4 coupe, series 60 + engine "
                "3, MY2001-2002. Capri XR2 turbo (1991-1994; MY1993 passenger-car engine code 6 = 1.6 EFI-TC) was manual-only per "
                "EPA, but no lot car carries it (lot Capris are code Z, the 1.6 DOHC base engine that had an automatic)."),
}

VIN_SCHEME = {
    "Ford/Lincoln/Mercury": {
        "positions": {"1-3": "WMI", "4": "restraint system (passenger cars) / brake system + GVWR class (trucks, MPVs)",
                      "5": "make designator for passenger cars (P = Ford, M = Lincoln or Mercury, T = imported / non-Ford-built marketed by Ford; MY2002 filing section III)",
                      "6-7": "line, series, body type (passenger cars); trucks/MPVs use 5-7 for line, series, chassis, cab/body",
                      "8": "engine type (displacement, cylinders, fuel, manufacturer, net hp); separate tables for passenger car, light truck/MPV, medium/heavy truck",
                      "9": "check digit", "10": "model year", "11": "assembly plant", "12-17": "sequential number"},
        "transmission": "none in any filing read (MY1985, 1987, 1993, 2001-2007, 2013-2020 read for the rules; text search of all 125 text-layer filings MY2000-2028)",
    }
}

NOT_RULED = [
    {"make": "Ford", "scope": "every Ford outside the rules (F-Series, Super Duty, Ranger, Explorer, Escape 2005+, Mustang GT/V6/EcoBoost/Mach 1, Focus/Fiesta base engines, Contour, Escort, Probe, Tempo, Taurus non-SHO, vans)", "why": "no transmission character, and the engine/series codes were sold with both transmissions or only with automatics"},
    {"make": "Ford", "scope": "Fusion 1.6L EcoBoost MY2013 (code R, 199 lot cars)", "why": "EPA lists Manual 6-spd and Automatic (S6) for 2013 (33084, 33085, 33280)"},
    {"make": "Ford", "scope": "Focus 1.0L EcoBoost MY2016-2018 (code E, 43 lot cars)", "why": "EPA lists Automatic (S6) from 2016 (36988, 38469, 39607). vPIC returns '6-spd Automatic' for every 2018 one (uniformCell auto), which is a model default, not this rule's business"},
    {"make": "Ford", "scope": "Escape 2.0 Zetec MY2003 (code B)", "why": "the code letter is clipped in the MY2003 filing scan; no 2003 Escape with code B is on the lots"},
    {"make": "Ford", "scope": "Ranger 2.0L MY1985-1987 (code C, 4 lot cars)", "why": "candidate only: EPA lists manuals only, but The Ranger Station reports C-3 automatics behind the 2.0"},
    {"make": "Ford", "scope": "Probe GT 2.2 turbo MY1989 (code L, 2 lot cars)", "why": "EPA lists only a manual for the 1989 turbo (5550), but its Mazda 626/MX-6 turbo twin had an automatic (EPA 5744) and the Probe got one for 1990 (6679); no independent statement and no MY1989 filing read"},
    {"make": "Ford", "scope": "Taurus SHO MY1989-1992, 1994-1995", "why": "same engines (3.0 manual, 3.2 automatic from 1993), but no filing for those years was read; 1994-1995 lot SHOs are code P (automatic) anyway"},
    {"make": "Ford", "scope": "Mustang SVT Cobra 1993-2004, Cobra R 1995/2000, Bullitt 2001 and 2008-2009, Boss 302 2012-2013 (code U), Shelby GT500 2007-2012 (5.4 SC), Ford GT 2005-2006", "why": "manual-only models, but no lot car carries their codes (the lots hold one 2014 GT500), so no rule was built; Bullitt 2001/2008-09 and Boss share codes with automatic GTs or lack an independent source"},
    {"make": "Ford", "scope": "Mustang Bullitt 2019-2020 (P8K + 0)", "why": "candidate only (EPA-only transmission evidence); no lot car"},
    {"make": "Ford", "scope": "Shelby GT500 2020+ (P8S + J)", "why": "dual-clutch (EPA AM7): not manual, no rule needed; no lot car"},
    {"make": "Ford", "scope": "Contour SVT 1998-2000, Escort ZX2 S/R, Thunderbird Turbo Coupe, Mustang SVO / Turbo GT 1984-1986, EXP/Escort Turbo 1984-1985, Escort/Tempo 2.0 diesel 1984-1986", "why": "manual-only or near, but no lot car without transmission info carries a distinct code"},
    {"make": "Lincoln", "scope": "every Lincoln", "why": "no manual-only engine or series code; the LS V6 manual (2000-2002) shares its engine code with the automatic"},
    {"make": "Mercury", "scope": "Cougar I4 MY1999 and MY2000", "why": "1999: EPA lists an automatic for the 2.0 (14999). 2000: EPA manual only (15802) but no MY2000 filing read; no MY2000 I4 Cougar on the lots"},
    {"make": "Mercury", "scope": "Capri XR2 1991-1994 (1.6 turbo)", "why": "EPA manual only, but no lot car carries the turbo code"},
    {"make": "Mazda (Ford-coded)", "scope": "Mazda Tribute 2001-2004 2.0 (WMI 4F2, engine B)", "why": "Mazda make, worklist 1. The same evidence applies: Ford filing 01-022-N11B-8520 ('B ... used in the Escape and Tribute'), EPA 17159, 17260, 18102, 18212, 19082, 19203, 20210, 20331 manual only"},
]

VALIDATION_METHOD = (
    "Every lot car with a rule WMI, a 17-character VIN and a valid check digit is classified. The model year comes from VIN "
    "character 10 (the listing year only picks the 30-year cycle and must be within 2 years). A rule fires only when the VIN "
    "matches its WMI, years and fixed characters and character 8 is in its table for that year; other codes get no claim. "
    "Ground truth = scraper/manual_detect/ground_truth.jsonl; uniformCell lines are unlabelled, speeds-only lines excluded, the "
    "rest checkable: agree means (truth is manual) == (rule says manual). Ford/Lincoln/Mercury ground truth is almost all vPIC "
    "decodes of MY2017+ cars (vPIC gives no Ford transmission before then) plus VIN-less listing lines, so no rule here has a "
    "checkable car. Independent checks: (1) epa_rows, the EPA rows for the rule's exact model/engine (row ids, all must be the "
    "claimed class); (2) a per-car EPA union check (year/make/model names + vPIC displacement) as in vin_rules_1. Status: "
    "candidate (not counted) when the transmission evidence is contradicted or EPA-only; drop when >= 20 checkable and agreement "
    "< 0.995; low_sample when < 20 checkable (kept: code meaning from Ford's own filing, manual-only fact from EPA plus an "
    "independent text source); keep otherwise. newly_confirmed_manual counts lot cars with no published transmission "
    "(vehicle_extras trans empty) that a keep or low_sample rule calls manual."
)


def rule_regex(r: dict) -> str:
    """Regex for the rule's MANUAL codes: WMI, fixed characters, code character and year codes."""
    man = {c: v for c, v in r["codes"].items() if v[0] == M}
    if not man:
        return ""
    chars = ["."] * 17
    for p, allowed in r["fixed"].items():
        chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
    codes = "".join(man)
    chars[r["pos"] - 1] = "[" + codes + "]" if len(codes) > 1 else codes
    ys = year_chars({y for v in man.values() for y in v[2]})
    chars[9] = "[" + ys + "]" if len(ys) > 1 else ys
    return "^(" + "|".join(r["wmi"]) + ")" + "".join(chars[3:])


def classify(vin: str, year: int):
    """-> (rule, claim, code, meaning); ('unknown_code', rule) when in scope but the code is not in the table."""
    scoped = None
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        scoped = scoped or r
        code = vin[r["pos"] - 1]
        hit = r["codes"].get(code)
        if hit and year in hit[2]:
            return (r, hit[0], code, hit[1])
    return ("unknown_code", scoped) if scoped else None


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
                if r["make"] not in MAKES:
                    continue
                try:
                    y = int(r["year"])
                except ValueError:
                    continue
                i = len(self.rows)
                self.rows.append(r)
                for _lv, k in ep.epa_keys(r):
                    self.idx[(y, r["make"], k)].add(i)

    def rule_rows(self, make: str, spec: dict) -> list[dict]:
        out = []
        for r in self.rows:
            if r["make"] != make or int(r["year"]) not in spec["years"] or not re.search(spec["model"], r["model"]):
                continue
            if not r["displ"] or abs(float(r["displ"]) - spec["displ"]) > 0.051:
                continue
            ch = spec.get("charger")
            if ch is not None and (r["tCharger"].strip() if ch == "T" else r["sCharger"].strip() if ch == "S" else "") != ch:
                continue
            if spec.get("trany") and not re.search(spec["trany"], r["trany"]):
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
    make_cov = {m: Counter() for m in MAKES}
    gt_cov = {m: Counter() for m in MAKES}
    newly_manual, newly_auto, conflicts = [], [], []

    for row in inv["vehicles"]:
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        fyear = row[fi["year"]]
        make = row[fi["make"]] or ""
        model = row[fi["model"]] or ""
        yard = yards[row[fi["yard"]]][0] if isinstance(row[fi["yard"]], int) else ""
        ex = list(extras.get(vid) or []) + [""] * 5
        pub = ex[3] or ""
        pcls = tclass(pub)
        g = gt.get(vid)
        if make in MAKES:
            mc = make_cov[make]
            mc["cars"] += 1
            mc["no_trans_info"] += 0 if pub else 1
            mc["vin17"] += 1 if len(vin) == 17 else 0
            if g is not None:
                gt_cov[make][f"{g.get('source')}:{g.get('transClass')}" + (":uniformCell" if g.get("uniformCell") else "")] += 1
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
            unknown_codes[r["id"]][f"{y}:{vin[r['pos'] - 1]}"] += 1
            scan["in_scope_code_not_in_table"] += 1
            continue
        r, claim, code, meaning = res
        rid = r["id"]
        scan["covered"] += 1
        st = per_rule[rid]
        st[claim]["in_scope"] += 1
        codes_seen[rid][f"{y} {vin[3:8]}"] += 1
        if make in MAKES:
            make_cov[make]["covered_by_rule"] += 1
        raw = cache.get(vin)
        dec = raw if isinstance(raw, dict) else None
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
            cls = epa.classes(y, make if make in MAKES else r["make"], [model, (dec or {}).get("model", "")], displ)
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
                              "code": f"char{r['pos']}={code}: {meaning}", "rule_claim": claim, "published_trans": pub,
                              "transSrc": ex[4] or "vin", "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        if not pub:
            why = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if "transmission" in dec else "cache_old_schema")
            st[claim]["no_trans_info"] += 1
            st[claim][f"no_trans_info_{why}"] += 1
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"char{r['pos']}={code} ({vin[4:7]}): {meaning}", "why_no_trans": why, "yard": yard}
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
        # independent EPA rows for the rule's exact model/engine
        epa_rows, epa_ok = [], True
        for spec in r["epa"]:
            rows = epa.rule_rows(r["make"], spec) if epa.ok else []
            classes = sorted({ep.trany_class(x["trany"]) for x in rows})
            years_found = sorted({int(x["year"]) for x in rows})
            sole = bool(rows) and (classes == ["manual"] if spec["claim"] == M else "manual" not in classes)
            missing = sorted(set(spec["years"]) - set(years_found))
            epa_ok = epa_ok and sole and not missing
            epa_rows.append({"claim": spec["claim"], "filter": {k: v for k, v in spec.items() if k != "claim"},
                             "rows": [f"{x['year']} id {x['id']} '{x['model']}' {x['displ']}L {x['trany']}"
                                      + (f" ({x['eng_dscr']})" if x["eng_dscr"] else "") for x in rows],
                             "classes": classes, "sole_offering_holds": sole, "years_without_epa_row": missing})
        if r.get("candidate"):
            status = "candidate"
        elif not epa_ok:
            status = "candidate"
        elif chk >= MIN_SAMPLE and agreement is not None and agreement < MIN_AGREEMENT:
            status = "drop"
        elif chk < MIN_SAMPLE:
            status = "low_sample"
        else:
            status = "keep"

        def side(cl):
            s = st[cl]
            return {"in_scope_lot_cars": s["in_scope"], "checkable_ground_truth": s["checkable"],
                    "agree": s["agree"], "disagree": s["disagree"],
                    "agreement": round(s["agree"] / s["checkable"], 4) if s["checkable"] else None,
                    "uniform_cell_lines_excluded": s["uniform_cell_excluded"],
                    "uniform_cell_lines_that_would_agree": s["uniform_cell_would_agree"],
                    "ground_truth_speeds_only_excluded": s["speeds_only_excluded"],
                    "epa_crosscheck_per_car": {"consistent": s["epa_consistent"], "conflict": s["epa_conflict"],
                                               "no_epa_match": s["epa_no_match"]},
                    "cars_without_trans_info": s["no_trans_info"],
                    "cars_without_trans_info_by_reason": {k[len("no_trans_info_"):]: v for k, v in s.items()
                                                          if k.startswith("no_trans_info_")}}

        def fmt(v):
            ys = v[2]
            return v[1] + (f" (MY{ys[0]})" if len(ys) == 1 else f" (MY{', '.join(map(str, ys))})" if ys != list(range(ys[0], ys[-1] + 1)) else f" (MY{ys[0]}-{ys[-1]})")
        man_codes = {c: fmt(v) for c, v in r["codes"].items() if v[0] == M}
        aut_codes = {c: fmt(v) for c, v in r["codes"].items() if v[0] == A}
        out_rules.append({
            "id": rid, "make": r["make"], "status": status, "basis": r["basis"],
            "status_reason": RULE_STATUS_NOTE[status] + ("" if epa_ok or r.get("candidate") else " (EPA rows do not show a sole offering)"),
            "notes": r["notes"],
            "claim": "manual for the manual codes; automatic (not manual) for the automatic codes" if aut_codes else "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + (", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())) or "none")]},
            "vin_condition": {"position": r["pos"], "manual_codes": man_codes, "automatic_codes": aut_codes},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"]] + [{"url": EPA_URL, "doc": C["epa"]["doc"],
                                                        "says": "; ".join(f"{e['claim']}: " + ", ".join(e["rows"]) for e in epa_rows)}],
            "evidence_gaps": r["evidence_gaps"],
            "validation": {
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": st[M]["checkable_gt_manual"] + st[A]["checkable_gt_manual"],
                "epa_rows": epa_rows, "epa_sole_offering_holds": epa_ok,
                "manual_codes": side(M), "automatic_codes": side(A),
                "disagree_examples": examples[rid]["disagree"],
                "epa_conflict_examples": examples[rid]["epa_conflict"],
                "codes_seen_on_lots": dict(codes_seen[rid].most_common()),
                "in_scope_codes_not_in_table": dict(unknown_codes[rid].most_common()),
            },
            "newly_confirmed_manual": st[M]["no_trans_info"],
            "newly_labelled_non_manual": st[A]["no_trans_info"],
        })

    keep_ids = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    nm_conf = [c for c in newly_manual if c["rule"] in keep_ids]
    nm_cand = [c for c in newly_manual if c["rule"] not in keep_ids]
    for mk in MAKES:
        make_cov[mk]["newly_confirmed_manual_counted"] = sum(1 for c in nm_conf if c["make"] == mk)
        make_cov[mk]["newly_confirmed_manual_candidate_rules_only"] = sum(1 for c in nm_cand if c["make"] == mk)
        make_cov[mk]["newly_labelled_non_manual_counted"] = sum(1 for c in newly_auto if c["make"] == mk and c["rule"] in keep_ids)
    man_chk = sum(x["validation"]["manual_codes"]["checkable_ground_truth"] for x in out_rules if x["id"] in keep_ids)
    man_agr = sum(x["validation"]["manual_codes"]["agree"] for x in out_rules if x["id"] in keep_ids)
    aut_chk = sum(x["validation"]["automatic_codes"]["checkable_ground_truth"] for x in out_rules if x["id"] in keep_ids)
    aut_agr = sum(x["validation"]["automatic_codes"]["agree"] for x in out_rules if x["id"] in keep_ids)

    doc = {
        "worklist": "vin_rules_4",
        "makes": list(MAKES),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/vin_rules_4.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json", "vehicle_extras": "docs/data/vehicle_extras.json",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (uniformCell lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA checks skipped, every rule falls to candidate)"),
                   "mid_filings": "all 249 Ford Motor Company Part 565 filings listed by the MID search (vpic.nhtsa.dot.gov/mid, manufacturer 'Ford'), downloaded 2026-11-05; the ones cited were read (text layer or page image). MID lists no Lincoln- or Mercury-named filer: Ford files for all three makes",
                   "web_sources": "independent text sources were read through web-search result text (WebFetch could not reach wikipedia.org / auto123.com from this session); quotes in each citation"},
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
            "newly_labelled_non_manual_keep_and_low_sample_rules": len([c for c in newly_auto if c["rule"] in keep_ids]),
            "ground_truth_precision_manual_claims": {"checkable": man_chk, "agree": man_agr,
                                                     "precision": round(man_agr / man_chk, 4) if man_chk else None},
            "ground_truth_agreement_automatic_claims": {"checkable": aut_chk, "agree": aut_agr,
                                                        "agreement": round(aut_agr / aut_chk, 4) if aut_chk else None},
            "published_labels_contradicting_a_rule": len(conflicts),
            "scan": dict(scan),
            "make_coverage": {m: dict(v) for m, v in make_cov.items()},
            "ground_truth_lines_by_make": {m: dict(v.most_common()) for m, v in gt_cov.items()},
        },
        "validation_method": VALIDATION_METHOD,
        "rules": out_rules,
        "newly_confirmed_manual_cars": nm_conf,
        "candidate_rule_manual_cars": nm_cand,
        "newly_labelled_non_manual_cars": [c for c in newly_auto if c["rule"] in keep_ids],
        "published_label_conflicts": conflicts,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("non-manual labels (keep+low_sample):", s["newly_labelled_non_manual_keep_and_low_sample_rules"])
    print("manual-claim precision:", s["ground_truth_precision_manual_claims"], " auto-claim agreement:", s["ground_truth_agreement_automatic_claims"])
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"])
    print("scan:", s["scan"])
    for x in out_rules:
        print(f"  {x['id']}: {x['status']} epa_ok={x['validation']['epa_sole_offering_holds']} chk={x['validation']['checkable_ground_truth']} new_manual={x['newly_confirmed_manual']} codes={x['validation']['codes_seen_on_lots']} unknown={x['validation']['in_scope_codes_not_in_table']}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
