#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 1: Subaru, Mazda,
Mitsubishi, Suzuki, Isuzu.

What the manufacturers' own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say, read filing by filing:

  * Subaru: VIN character 11 is "plant of manufacture AND transmission type"
    in every Subaru filing read, MY1985 through MY2025 (rules capped at MY2025, the latest filing read). The letter/digit
    pairs differ by plant (FHI Gunma: JF1/JF2; Subaru of Indiana: 4S3/4S4)
    and by era, so every code is scoped to the model years whose filing
    defines it. The Subaru-built Scion FR-S / Toyota 86 / GR86 (WMI JF1,
    line ZN) use the same character.
  * Mazda: NO transmission character in any filing read (MY1990, 1995,
    2003-2007, 2011, 2021 MX-5/Mazda3). Character 8 is the engine type, and
    for a handful of engines Mazda's own engine code is a manual-only engine
    in the US market: RX-8 13B "High Power" (MY2004, MY2009-2011),
    MAZDASPEED3 L3T turbo (MY2007-2013), MAZDASPEED6 L3T turbo
    (MY2006-2007) and the MY2003 MAZDASPEED Protege FSD 170 hp engine.
  * Mitsubishi: NO transmission character (MY1992, 1993, 1995, 1998, 2003,
    2018 filings). Character 8 is the engine; the 3000GT VR-4 / Dodge
    Stealth R/T Turbo twin-turbo engine code is manual-only.
  * Isuzu: NO transmission character (MY1992, 1995, 1997, 1998, 2002
    filings). Character 5 = line + 4x2/4x4, 7 = body, 8 = engine. Ruled:
    Rodeo 2.6 4x2 (1991-1997) and the 1998 Amigo, both sold only with a
    manual (EPA + Wikipedia / Edmunds / Consumer Guide). EPA-only candidates:
    Pickup/Amigo 2.3 4x2, Pickup/Amigo 2.6 4x4, Trooper 2.3.
  * Suzuki: NO transmission character (MY2003, MY2009 filings). Samurai is
    an EPA-only candidate model rule.

Rule status: keep / low_sample rules are counted; candidate rules are
written to the output but their cars are listed separately and NOT counted.
Each rule carries "basis": transmission_code (the filing names the
transmission) or engine_code / line_body_code (the filing names an engine or
model that independent sources say was sold only with a manual).

Every rule is validated against ground_truth.jsonl (uniformCell lines are
treated as unlabelled), cross-checked against EPA, and counted for the lot
cars WITHOUT transmission info it would newly confirm.

Adversarial verification (2026-11-05, second session): every rule carries a
"verified" block (filings re-read, counterexample searches, scope edges,
changes) and a whole-vPIC-cache counterexample scan; the top-level
"verification" block lists what was narrowed. No rule was refuted; the
Subaru rules were capped at MY2025, Mazdaspeed6 fixed to JM1GG12L, the Isuzu
Rodeo rule split by line code (G 1991-1995, K 1995-1997) and the Isuzu rules
limited to WMI 4S2.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (optional, EPA cross-check).
Output: scraper/manual_detect/vin_rules_1.json

Run:  python3 -I scraper/manual_detect/vin_rules_1.py
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

OUT = HERE / "vin_rules_1.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995

# ---------------------------------------------------------------------------
# VIN helpers
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
        i = (y - 1980) % 30
        if _YEAR_CODES[i] not in out:
            out.append(_YEAR_CODES[i])
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
# Citations (every URL is a public NHTSA MID file, EPA, or Wikipedia page)
# ---------------------------------------------------------------------------
def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


C = {
    # --- Subaru ---------------------------------------------------------
    "sub_1986": mid("446794e0-c365-45d3-bbc0-5bbb8faec9e8",
                    "NHTSA 01-22-N11B-2097, Subaru of America 1985-10-01/1985-11-06, booklet 'Subaru Vehicle Identification Numbers 1986 Edition' (SOAD-840004), covers MY1985 and MY1986",
                    "Character 11 'Plant of manufacture and transmission type', Gunma: A = 4 spd manual, B = 5 spd manual, C = automatic, D = 4 spd 4WD (81-84) / 5 spd 4WD (85-86), E = 4 spd 4x2 trans/4wd / 5 spd 4x2 trans/4wd (dual range), F = automatic/4wd. Starting-VIN table: e.g. GL Hatchback 5 Speed JF1AF23BX GB100001, Hatchback Automatic JF1AF43BX GC100001."),
    "sub_1989": mid("61a7bf0d-2808-48d2-8251-8d193607514d",
                    "NHTSA 01-22-N11B-3170, Subaru of America letter dated 1988-09-23 (MID lists 1998-09-23), '1989 Subaru Vehicle Identification Number' (read as page image 2026-11-05)",
                    "Character 11 'Transmission Type': B = 5MT, C = AT & ECVT, D = 4WD 5MT, E = 4WD, Dual-range, F = 4WD AT, G = Full time 4WD MT, H = Full time 4WD AT, 4 = 4WD 4MT Hatchback. Model year K = 1989. Example JF1AN43B4KC400001."),
    "sub_1996": mid("d1ff1a13-a4a8-46f1-9027-0523cd2fbe7d",
                    "NHTSA 01-22-N11B-5909, Subaru of America 1995-05-10, revised VIN schematic for 1996MY Legacy, Impreza, SVX (read as page images 2026-11-05)",
                    "Legacy (SIA, 4S3): 'Plant of manufacture and transmission type' 1 = 5MT, 6 = Fulltime AWD 5MT, 7 = Fulltime AWD 4AT, 9 = 4AT, 8 = Fulltime AWD for Postal; model year T = 1996, V = 1997. Impreza (FHI Gunma, JF1): B = 5MT, G = Fulltime AWD 5MT, H = Fulltime AWD 4AT, K = 4AT."),
    "sub_1997": mid("39b27c13-9a93-4fa7-9a4d-80330fbcd84f",
                    "NHTSA 01-22-N11B-6089, Subaru of America 1996-04-15, VIN schematic for 1997MY Legacy, Impreza, SVX (read as page images 2026-11-05)",
                    "Impreza (FHI Gunma): G = Fulltime AWD 5MT, H = Fulltime AWD 4AT; model year V = 1997, W = 1998, X = 1999."),
    "sub_1999": mid("4d7ecefc-4e64-4b1a-b999-563e5d347341",
                    "NHTSA 01-22-N11B-6751, Subaru of America 1998-03-20, VIN schemes for 1999MY Legacy, Impreza, Forester (read as page images 2026-11-05)",
                    "Forester (FHI Gunma, JF1SF): 'Plant of manufacture and transmission' G = Full-time AWD 5MT, H = Full-time AWD 4AT; model year X = 1999, Y = 2000, 1 = 2001."),
    "sub_2004_impreza": mid("a2db76f6-1da9-4c6b-9f40-df82b8b3d47a",
                            "NHTSA 01-022-N11B-9355, Subaru of America 2002-12-09, VIN scheme for 2004MY Impreza (read as page image 2026-11-05)",
                            "FHI Gunma: G = Full-time AWD 5MT, H = Full-time AWD 4AT; model year 4 = 2004, 5 = 2005, 6 = 2006; trims TS, RS, OUTBACK, WRX, STi."),
    "sub_2014_forester": mid("7d6c9023-c08a-4397-a0d4-a58fb77d04d2",
                             "NHTSA ORG8505, Fuji Heavy Industries 2013-02-11 (MID 2013-02-19), VIN scheme 2014MY Forester (read as page image 2026-11-05)",
                             "Plant of manufacture and transmission type: G = FHI (Yajima Plant, Ota, Gunma) Full-time AWD 6MT, H = FHI (Yajima) Full-time AWD CVT."),
    "sub_1990": mid("6c834268-78d8-405f-b7ac-c13348eea91f",
                    "NHTSA 01-22-N11B-3599, Subaru of America 1989-10-13, '1990 Model Year VIN Schematic'",
                    "Position 11 'Plant of manuf. & trans. type': FHI Gunma / SIA Lafayette / type: B / 1 = MT5; C / 2 = AT3; D / 3 = 4WD MT5; F / 5 = 4WD AT3/ECVT; G / 6 = F4WD MT5; H / 7 = F4WD 4EAT; K / 9 = 4EAT."),
    "sub_1991": mid("0dcae545-9204-464e-8db4-dcf2b0d8190e",
                    "NHTSA 01-22-N11B-3713, Subaru of America 1990-06-08, starting VINs for 1991 Justy, XT, Loyale, Legacy",
                    "Character 11 follows the model's transmission: Justy 3D DL MT5 JF1KA722X MB700001, Justy ECVT ...MC..., Justy OD 4WD MT5 ...MD..., OD 4WD ECVT ...MF...; Legacy sedan L MT5 ...MB..., L 4EAT ...MK..., L F4WD MT5 ...MG..., L F4WD 4EAT ...MH...; Loyale AT3 ...MC..., OD 4WD AT3 ...MF..."),
    "sub_1994": mid("4b3e22a1-120a-4936-b61b-8da14f61d6ee",
                    "NHTSA 01-22-N11B-5384, Subaru of America 1993-07-12, VIN schemes for 1994 Justy, Loyale, Impreza, Legacy, SVX",
                    "Character 11 'Plant of manufacture and transmission type'. Justy (FHI): B FWD 5MT, C FWD ECVT, D AWD 5MT, F AWD ECVT. Loyale: B FWD 5MT, C FWD 3AT, D AWD 5MT, F AWD 3AT. Impreza: B FWD 5MT, G full-time AWD 5MT single-range, H full-time AWD E4AT, K FWD E4AT. Legacy SIA/FHI: 1/B 5MT, 6/G full-time AWD 5MT, 7/H full-time AWD E4AT, 9/K E4AT, 8/P full-time AWD E4AT for Postal Service. SVX: H AWD E4AT, K FWD E4AT."),
    "sub_2001_forester": mid("100d2b73-b2e6-4824-81ed-5064ae016f4e",
                             "NHTSA 01-22-N11B-7472, Fuji Heavy Industries USA 1999-11-15, 2001 Forester VIN scheme",
                             "Character 11 'Plant of manufacture and transmission': G Full-time AWD 5MT, H Full-time AWD 4AT (text layer is OCR)."),
    "sub_2001_legacy": mid("0a4c5b9d-3768-474f-9052-e5ad9f00c1ff",
                           "NHTSA 01-022-N11B-7829, Subaru of America 2000-05-17, 2001 Legacy VIN scheme",
                           "Character 11 'Plant of manufacture, transmission and postal car': 6 Full-time AWD 5MT, 7 Full-time AWD 4AT (SIA)."),
    "sub_2002": mid("0daefd73-3aa2-44ad-9d6a-eaa204f58e38",
                    "NHTSA 01-022-N11B-8115, Subaru of America 2001-01-15, 2002 Legacy and Forester VIN schemes",
                    "Legacy (SIA): 6 Full-time AWD 5MT, 7 Full-time AWD 4AT. Forester (FHI): G Full-time AWD 5MT, H Full-time AWD 4AT."),
    "sub_2003": mid("456278b0-4f15-4488-b2ec-dea5be2f0e9f",
                    "NHTSA 01-022-N11B-9269, Subaru of America 2002-10-18, 2003 Subaru VIN update (Legacy, Baja, Impreza, Forester)",
                    "Position 11 'Plant of manufacturer and transmission type' (SIA 6/7, FHI G/H: AWD 5MT / AWD 4AT)."),
    "sub_2006": mid("63662431-fe07-4d49-a90e-60db7c2b4db3",
                    "NHTSA ORG225 (filed 2005-02-23), 'Subaru 2006MY VIN Breakdown'",
                    "Digit 11 'Plant of manufacturer and transmission type': SIA 4 = AWD 5AT, SIA 5 = AWD 4AT-SS, SIA 6 / FHI G = AWD 5MT, SIA 7 / FHI H = AWD 4AT, FHI L = AWD 6MT."),
    "sub_2009_forester": mid("21609d02-0d8c-40fe-916f-42eb1d3bdd46",
                             "NHTSA ORG3853, Fuji Heavy Industries USA 2008-01-17, VIN scheme for 2009MY Forester",
                             "Digit 11 'Plant of manufacture and transmission type' (FHI Gunma): G Full-time AWD 5MT S/R, H Full-time AWD 4AT."),
    "sub_2009_impreza": mid("37b703d5-77f6-4c0e-9201-feda1c4c9d50",
                            "NHTSA ORG7191, Fuji Heavy Industries USA (MID date 2011-10-03), 'VIN scheme for 2009MY Impreza (second submission)', GR11-055 (read as page image 2026-11-05)",
                            "Digit 11 (FHI Gunma): G Full-time AWD 5MT, H Full-time AWD 4AT, L Full-time AWD 6MT; model year 9 = 2009, A = 2010, B = 2011; trims include WRX and STI."),
    "sub_2012": mid("9c69db94-0fc4-4bea-816d-6a192305240b",
                    "NHTSA ORG7743, Fuji Heavy Industries USA 2012-05-02, 2012MY Legacy, Outback, Tribeca, Forester, Impreza, Impreza WRX/STI",
                    "Character 11 'Plant of manufacture and transmission type': SIA 1 Full-time AWD 6MT, 2 Full-time AWD 5AT, 3 Full-time AWD CVT, 4 (Tribeca) Full-time AWD 5AT; FHI Yajima G Full-time AWD 5MT, H Full-time AWD 4AT (Forester) / CVT (Impreza), L Full-time AWD 6MT (WRX/STI)."),
    "sub_2013_brz": mid("b1bc51b0-ab51-491e-8ba8-d73370380952",
                        "NHTSA ORG9621, Fuji Heavy Industries USA 2012-01-17, 2013MY Subaru BRZ (JF1ZC) and Toyota Scion FR-S (JF1ZN)",
                        "Character 11 'Plant of manufacture and transmission type': 1 = FHI 6MT, 2 = FHI 6AT (both BRZ and FR-S)."),
    "sub_2014": mid("f4bf0f92-4305-4bc3-8020-2a71dcb73c12",
                    "NHTSA ORG8624, Fuji Heavy Industries USA 2013-05-06, 2014MY Forester and Legacy/Outback",
                    "Forester: G FHI (Yajima) Full-time AWD 6MT, H Full-time AWD CVT. Legacy/Outback: 1 SIA Full-time AWD 6MT, 2 SIA 5AT, 3 SIA CVT."),
    "sub_2014_b": mid("8c6eeb84-dc82-4b4d-9ff5-0041b92800d5",
                      "NHTSA ORG9048, Fuji Heavy Industries USA 2013-10-28, 2014MY Tribeca, Impreza, XV Crosstrek, Impreza WRX/STI (+ others)",
                      "Impreza and XV Crosstrek: G FHI Yajima Full-time AWD 5MT, H Yajima CVT, 9 FHI Main Plant Full-time AWD 5MT, 8 Main Plant CVT. WRX/STI: G 5MT, L 6MT. Tribeca: 4 SIA Full-time AWD 5AT."),
    "sub_2017": mid("aeb340f8-3175-4e72-81af-51f52eab29a6",
                    "NHTSA ORG13185, Fuji Heavy Industries USA 2016-09-08, 2017 Subaru and Toyota models (ninth submission; text layer)",
                    "Plant of manufacture and transmission type: WRX/STI 9 Main Plant 6MT, 8 Main Plant CVT; Legacy/Outback 1 SIA 6MT, 3 SIA CVT; Forester G Yajima 6MT, H Yajima CVT; Crosstrek G/9 5MT, H/8 CVT; BRZ and Toyota 86 9 Main Plant 6MT, 8 Main Plant 6AT; Impreza 1 SIA 5MT, 3 SIA CVT."),
    "sub_2018": mid("0d16df95-607d-4140-a413-e0095416028d",
                    "NHTSA ORG15037, Fuji Heavy Industries USA 2017-10-30, 2018 Subaru models (fourth submission; text layer)",
                    "WRX/STI 8 CVT / 9 6MT (Main Plant); Forester and Crosstrek G 6MT / H CVT (Yajima), Crosstrek 8 CVT / 9 6MT (Main Plant); Impreza 1 SIA 5MT / 3 SIA CVT; BRZ and Toyota 86 8 6AT / 9 6MT."),
    "sub_2022": mid("d8020630-0a9a-47fb-a194-9888a072973b",
                    "NHTSA ORG19703, Subaru Corporation 2021-10-28, 2022MY Subaru and Toyota GR86 (seventh submission; text layer)",
                    "BRZ and Toyota GR86 8 Main Plant 6AT, 9 Main Plant 6MT; WRX 8 CVT, 9 6MT; Crosstrek G 6MT, H CVT, 8 CVT, 9 6MT; Impreza 1 SIA 5MT, 3 SIA CVT; Legacy/Outback/Ascent 3 SIA CVT."),
    "sub_2025": mid("72bb4585-2803-4a75-a8dd-47b21498cc21",
                    "NHTSA ORG23706, Subaru Corporation 2024-10-30, 2025MY Subaru and Toyota GR86 (seventh submission; text layer)",
                    "BRZ and GR86 8 6AT / 9 6MT; WRX 8 CVT / 9 6MT; Impreza 8 Main Plant CVT; Crosstrek H/8/3 CVT; Legacy/Outback/Ascent 3 SIA CVT."),
    # --- Mazda ----------------------------------------------------------
    "mz_1990": mid("08fa9f7c-f9b3-4849-9662-d2e11d5b3dd2",
                   "NHTSA 01-22-N11B-3504, Mazda Motor Corporation 1989-02-21, 1990MY VIN codes",
                   "Table II: characters 4-8 = Line, Series, Body Type, Engine Type (with horsepower), Restraint System Type; character 11 = plant (0 Hiroshima, 1 Hofu, 5 Flat Rock). No transmission field."),
    "mz_1995": mid("3d125d14-bd46-4bd0-a3b3-44c151705786",
                   "NHTSA 01-22-N11B-5638, Mazda Motor Corporation 1994-04-22, 1995MY VIN coding",
                   "Characters 4-8 = LINE / SERIES / BODY TYPE / ENGINE TYPE + HORSE POWER / RESTRAINT (brake/GVWR for MPV); character 11 = plant. Ford-built B-Series (4F4): brake/GVWR, carline, engine, plant. No transmission field."),
    "mz_2003_protege": mid("418ce1b8-2fb6-4209-a798-7ab4860e01be",
                           "NHTSA 01-022-N11B-9298, Mazda Motor Corporation 2002-06-19, 2003MY VIN coding (adds 'Mazda Protege high power version')",
                           "JM1 BJ225/BJ226 = Protege sedan, FSD 2.0L, 130 hp; BJ227/BJ228 = Protege sedan, FSD 2.0L, 170 hp (the MAZDASPEED Protege); BJ245/BJ246 = Protege5 hatchback 130 hp. No transmission field."),
    "mz_2004_rx8": mid("839b548e-3c15-467b-a743-a69c17480924",
                       "NHTSA 01-022-N11B-9546, Mazda Motor Corporation 2003-01-08, 2004MY Mazda RX-8 VIN coding",
                       "JM1 FE17N = RX-8 coupe, engine 13B STD (1.3L) 207 +/- 20.7 hp; JM1 FE173 = RX-8 coupe, engine 13B HP (1.3L) 247 +/- 24.7 hp. No transmission field."),
    "mz_2004": mid("1ea6879d-e490-48b2-acb9-2125676af6b8",
                   "NHTSA 01-022-N11B-9586, Mazda Motor Corporation 2003-07-16, 2004MY VIN coding (Mazda3, B-Series; Mazda6/MPV earlier)",
                   "Decipherable information columns: LINE, SERIES, BODY TYPE, ENGINE TYPE, HORSE POWER, BRAKE SYSTEM/GVWR, RESTRAINT. Tribute/B-Series (Ford-built 4F2/4F4): brake/GVWR, carline, engine, plant. No transmission field."),
    "mz_2006": mid("e24d0e67-d70f-4c46-afda-c715cbfb6237",
                   "NHTSA ORG322 (MID date 2004-05-14; the letter itself is dated 2005-03-14, ref NH05/03, same document as 01-022-N11B-10376), Mazda 2006MY VIN coding for MX-5, Mazda5, Mazda3, Mazda6 (base and turbo), MPV (read as page images 2026-11-05)",
                   "JM1 GG12L = Mazda 6 sedan, L3T (2.3L Turbo) 274+/-27 hp; every other 2006 Mazda6 is 1YV (AAI Flat Rock; character 8 C = 2.3L I-4, D = 3.0L V-6). Mazda3 JM1 BK: character 8 = 3 L3V (2.3L) General, 4 = L3V California. No transmission field. RX-8 not refiled for 2006."),
    "mz_2008": mid("af16f4a3-08b1-4ebd-9f3f-9b05f2c41269",
                   "NHTSA ORG2947, Mazda Motor Corporation 2007-04-03, 2008MY VIN coding (MX-5, RX-8, Mazda3, Mazda5, Mazda6, CX-7, CX-9) (read as page image 2026-11-05)",
                   "JM1 FE173 = RX-8 13B (1.3L) High Power, horse power '232HP (MT) / 212HP (AT)' (so FE173 covers both transmissions in 2006-2008). JM1 BK34L / BK14L = Mazda3 5-door hatchback L3T (2.3L) Turbo Fed., BK34M / BK14M = L3T Turbo Calif., 263HP. No transmission field."),
    "mz_2009": mid("97b6caf5-5451-42e7-b1bd-d947b6cd3a20",
                   "NHTSA ORG3973, Mazda Motor Corporation 2008-02-29, 2009MY VIN coding (read as page images 2026-11-05)",
                   "RX-8: JM1 FE17M = 13B California Standard Power, FE172 = California High Power, FE17P = Federal Standard Power, FE174 = Federal High Power. Mazda3: BK34L / BK14L = L3T (2.3L) Turbo Fed., BK34M / BK14M = L3T Turbo Calif. No transmission field."),
    "mz_2010_mazda3": mid("c8003b0a-3f47-4de7-a680-d19a82e74dc4",
                          "NHTSA ORG4472, Mazda Motor Corporation (MID 2009-10-17), 2010MY VIN coding for Mazda3 (read as page image 2026-11-05)",
                          "JM1 BL1H3 = Mazda3 5-door hatchback L3T (2.3L Turbo) Federal, BL1H4 = L3T California; BL1HF = LFX 2.0, BL1H5 / BL1H6 = L5X 2.5. No transmission field."),
    "mz_2007": mid("9833e4a8-e804-47ae-abd4-80d334a4124e",
                   "NHTSA ORG1842, Mazda Motor Corporation 2006-04-05, 2007MY VIN coding",
                   "JM1 BK14L / BK34L = Mazda3 5-door hatchback, L3T (2.3L) Turbo Fed.; BK14M / BK34M = L3T Turbo Calif.; JM1 GG12L = Mazda6 sedan L3T (2.3L) Turbo; JM1 FE173 = RX-8 13B (1.3L) High Power. No transmission field."),
    "mz_2011": mid("534fb246-aca9-475b-9b94-db135237831b",
                   "NHTSA ORG5728, Mazda Motor Corporation 2010-03-08, 2011MY VIN coding",
                   "RX-8 JM1 FE1CM = 13B California Standard Power, FE1C2 = California High Power, FE1CP = Federal Standard Power, FE1C4 = Federal High Power. Mazda3 JM1 BL1H3 = L3T (2.3L Turbo) Federal, BL1H4 = L3T California (others LFX 2.0 / L5X 2.5 Federal/California). Columns: LINE, SERIES, BODY TYPE, ENGINE TYPE, RESTRAINT. No transmission field."),
    "mz_2021": mid("a959bc72-6781-4277-bab7-cd2043cf4f6c",
                   "NHTSA ORG17864, Mazda Motor Corporation 2020-05-22, 2021MY MAZDA3 (text layer)",
                   "Generic format: 4 Line, 5 Series, 6 Body type, 7 restraint devices, 8 engine type, 10 model year, 11 plant. No transmission field."),
    "mz_2024_cx90": mid("174a9bdd-b18b-4acc-8af3-628f2597e743",
                        "NHTSA ORG21118, Mazda Motor Corporation 2022-11-21, 2024MY CX-90 (text layer)",
                        "Character 7 = 'Transmission type / Drive axle / Body style' (H = AT 4WD wagon). First Mazda filing read that names a transmission; CX-90 (and CX-70, 2026 CX-5) are automatic-only, so it never marks a manual."),
    "mz_vpic_rx8": {"url": "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/",
                    "doc": "NHTSA vPIC decodes 2026-11-05 of lot VINs and of VINs built from the filing pattern (check digit recomputed)",
                    "says": "MY2009 JM1FE17[2|4] and MY2010-2011 JM1FE1C[2|4] decode EngineModel '13B ... High Power'; [M|P] decode 'Standard Power'. MY2005-2008 JM1FE173 decodes '13B (1.3L) High Power', OtherEngineInfo 'Engine HP: 238 hp for MT; 212 hp for AT' (so FE173 is NOT manual-only after 2004)."},
    "mz_vpic_ms": {"url": "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/",
                   "doc": "NHTSA vPIC decodes 2026-11-05 (lot VINs and pattern VINs, check digit recomputed)",
                   "says": "JM1BK[1|3]4[L|M] MY2007-2009 = 'L3T (2.3L) Turbo Federal/California', Turbo=Yes; JM1BL1H[3|4] MY2010-2013 = 'L3T (Turbo) Federal/California', Turbo=Yes (BL1H5-9, F, G, P are non-turbo 2.0/2.5); JM1GG1[2|4]L MY2006-2007 = 'L3T (2.3L) Turbo'; JM1BJ227 MY2003 = FSD, EngineHP 153-187."},
    "wiki_rx8": {"url": "https://en.wikipedia.org/wiki/Mazda_RX-8",
                 "doc": "Wikipedia, Mazda RX-8 (wikitext read 2026-11-05)",
                 "says": "Port-option table: 2004-2005 automatic = 4-speed with the 4-port (standard) engine; 6-speed manual = 6-port; the 5-speed manual with the 4-port engine was 'Not sold in North America'. 6-speed automatic 'introduced in the U.S. for the 2006 model year, replacing the 4-speed automatic of 2004-2005', 212 hp; 6-speed manual 232 hp (North America). 'Automatic versions all had lower output/lower rpm engines.'"},
    "wiki_ms3": {"url": "https://en.wikipedia.org/wiki/Mazdaspeed3",
                 "doc": "Wikipedia, Mazdaspeed3", "says": "Infobox transmission: 6-speed manual (only transmission listed, both generations)."},
    "wiki_ms6": {"url": "https://en.wikipedia.org/wiki/Mazda6",
                 "doc": "Wikipedia, Mazda6 (Mazdaspeed6 section)",
                 "says": "Mazdaspeed6: turbocharged 2.3 L MZR; 'All markets received a revised front fascia with a raised hood, a 6-speed manual transmission, and all-wheel drive.'"},
    "wiki_msp": {"url": "https://en.wikipedia.org/wiki/Mazda_Familia",
                 "doc": "Wikipedia, Mazda Familia (Mazdaspeed Protege section)",
                 "says": "'In 2003, Mazdaspeed introduced the Mazdaspeed Protege ... 170 hp turbocharged engine'; 4,500 built. (Transmission not stated here; see EPA and Edmunds.)"},
    "edmunds_msp": {"url": "https://www.edmunds.com/mazda/mazdaspeed-protege/2003/st-100178606/features-specs",
                    "doc": "Edmunds 2003 Mazdaspeed Protege features & specs (seen via web search 2026-11-05; page not fetched); also Cars.com https://www.cars.com/research/mazda-mazdaspeed_protege-2003/specs/109435/",
                    "says": "Edmunds: 5-speed manual, front-wheel drive, limited-slip differential; no automatic listed for the MAZDASPEED Protege. Cars.com: 2.0L turbocharged I-4, 170 hp."},
    "lot_msp_serials": {"url": "docs/data/inventory_live.json",
                        "doc": "YardScout lot VINs, 2026-11-04 scan (supporting evidence, not a source of the claim)",
                        "says": "Every 2003 JM1BJ227 VIN on the lots has a serial in 641697-648720; every 2003 BJ225/BJ226/BJ245/BJ246 serial is 101133-221210. The 170 hp code sits in its own production block, as a 4,500-car special run would."},
    # --- Mitsubishi -----------------------------------------------------
    "mi_1992": mid("6bf5786d-ae22-4ecd-b944-c444c17fa858",
                   "NHTSA 01-22-N11B-4081, Mitsubishi Motors Corporation 1990-11-26, VIN for 1992 model vehicles",
                   "4th restraint/GVWR, 5th-6th car line + series (D 4-6 / E 7 = Mitsubishi 3000GT / Dodge Stealth), 7th body, 8th engine type: C = 3.0L DOHC MPI T/C I/C (twin turbo), B = 3.0L DOHC, S = 3.0L MPI, U = 2.0L DOHC MPI T/C I/C. No transmission field."),
    "mi_1992_dsm": mid("4a8efed6-ef2d-412d-b2c7-006be20bea87",
                       "NHTSA 01-22-N11B-4155, Mitsubishi Motors Corporation 1991-03-11, Diamond-Star Motors 1992MY VIN coding",
                       "4th restraint/GVWR, 5th-6th car line/series (Eclipse/Laser/Talon S, T; Mirage U), 7th body, 8th engine (U = 2.0L DOHC MPI T/C I/C). No transmission field."),
    "mi_1993": mid("9ae7b268-70af-461a-bbf0-57116a463629",
                   "NHTSA 01-22-N11B-4618, Mitsubishi Motors Corporation 1992-04-23, VIN for 1993 model vehicles (MMC and Diamond-Star)",
                   "5th car line M (series 4-6) / N (series 7) = Mitsubishi 3000GT / Dodge Stealth; 8th engine K = 3.0 DOHC MPI T/C I/C, J = 3.0 DOHC MPI, H = 3.0 MPI. No transmission field."),
    "mi_1995": mid("9f607dc2-5a9a-46e8-930f-91cff3e94876",
                   "NHTSA 01-22-N11B-5700, Mitsubishi Motors Corporation 1994-06-22, VIN for 1995 model vehicles (MMC and Diamond-Star)",
                   "5th-6th: M (4,5,8) / N (7) = 3000GT / Dodge Stealth, V (6) / W (7) = 3000GT Spyder; 8th engine K = 3.0 DOHC MPI 2 T/C 2 I/C, J = 3.0 DOHC MPI, H = 3.0 MPI. No transmission field."),
    "mi_1998": mid("8010978c-097c-4896-9dbc-76830515b7db",
                   "NHTSA 01-22-N11B-6347, Mitsubishi Motors Corporation 1997-06-11, 1998MY VIN codes (MMC and MMMA)",
                   "5th car line M/N = 3000GT, V/W = 3000GT Spyder; 8th engine K = 3.0 DOHC MPI 2T/C 2I/C. MMMA (4A3): 4th restraint, 5th line, 6th series, 7th body, 8th engine. No transmission field."),
    "mi_2003": mid("b3cd8644-68af-45cd-a4db-3cafea891ada",
                   "NHTSA 01-022-N11B-8726, Mitsubishi Motors Corporation 2002-06-04, 2003MY VIN coding (MMC and MMMA)",
                   "MMMA: 4th restraint, 5th car line (Galant, Eclipse, Eclipse Spyder, Stratus/Sebring), 6th series-price class, 7th body type, 8th engine (text layer is OCR). No transmission field."),
    "mi_2018": mid("f5286676-13c8-492f-8cac-79caa21e9d99",
                   "NHTSA ORG13914, Mitsubishi Motors Corporation 2017-03-29, 2018MY VIN coding (text layer)",
                   "4th restraint/GVWR, 5th car line, 6th make/series-price class, 7th body type, 8th engine type. No transmission field."),
    "mi_montero_sport": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                         "doc": "EPA vehicles.csv (only source for the claim) + vPIC decodes of the lot VINs (2.4L 4-cyl, 4x2)",
                         "says": "29580 (1997), 14677 (1998), 15482 (1999) Montero Sport 2WD 2.4: Manual 5-spd, the only 2.4 rows. No Mitsubishi filing for 1997-1999 was read for the JA4 LS..G code, and no text source confirms the 2.4 was manual-only."},
    "mi_vpic": {"url": "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/",
                "doc": "NHTSA vPIC decodes 2026-11-05 of pattern VINs (check digit recomputed)",
                "says": "MY1991-1992 JA3/JB3 XE74C (3000GT / Stealth R/T Turbo) Turbo=Yes; MY1993-1999 JA3/JB3 ..N74K Turbo / VR-4 / R/T TURBO, AWD."},
    # --- Suzuki / Isuzu (no rule; cited for the 'not encoded' finding) --
    "sz_2003": mid("272472b5-771c-4699-91c6-1f901abf99ac",
                   "NHTSA 01-022-N11B-9332, American Suzuki 2002-11-14, 2003MY Aerio, Vitara, Grand Vitara, XL-7 (OCR text)",
                   "Aerio: 4 line, 5 series/chassis/restraint, 6 engine type, 7 design sequence, 8 body type, 11 plant. Vitara/Grand Vitara: line, series (2WD/4WD body), engine, body. No transmission field."),
    "sz_2009": mid("e858cbea-a0c6-4a48-a996-7b5fc053b854",
                   "NHTSA ORG4192, American Suzuki 2008-06-10, 2009MY SX4, Grand Vitara, XL7, Equator",
                   "SX4: 4 line, 5 series/chassis/restraint, 6 engine, 7 design code, 8 grade. Grand Vitara: 5 series, 6 engine, 7 design code, 8 grade. XL7 (GM CAMI): 6-7 grade, 8 engine. Equator (Nissan-built 5Z6): 4 engine, 5 line, 7 body, 8 GVWR/brake. No transmission field."),
    "is_1992": mid("6fd83e64-2598-4305-9e04-d30d12e814ba",
                   "NHTSA 01-22-N11B-4240, Isuzu Motors 1991-04-11 (issued 1990-10, revised 1991-04), VIN for 1992 model year vehicles (read as page images 2026-11-05)",
                   "Section C (MPV / light-duty truck): position 4 GVWR/brake, 5 'Line and Chassis Type' (G = Utility 4x2, H = Utility 4x4, L = Conventional Cab 4x2, R = Conventional Cab 4x4, Y = Utility 4x4), 6 model-series, 7 body type (1 = 2-door cab SWB, 7 = utility 2-door SWB, 8 = utility 4-door), 8 'Engine Codes' (E = 4ZE1 2.6L L4, L = 4ZD1 2.3L L4, Z = 3.1L V6 GM, V = 6VD1 3.2L SOHC, W = 6VD1 3.2L DOHC). No transmission table."),
    "is_1995": mid("c8d1cf75-c8c6-44da-a98f-3ff54437a542",
                   "NHTSA 01-22-N11B-5634, Isuzu Motors 1994-03-15, VIN for 1995 model year (read as page images 2026-11-05)",
                   "Position 5 (JAA, JAC, 4S1, 4S2): L = Pickup 4x2, R = Pickup 4x4, H/J = Trooper 4x4, G = Rodeo 4x2, Y = Rodeo 4x4, K = Rodeo 4x2 with airbags, M = Rodeo 4x4 with airbags (4S6 Passport G/Y/K/M). Position 7: 8 = Utility 4-door, 7 = Utility 2-door SWB. Position 8: E = 4ZE1 2.6L, L = 4ZD1 2.3L, Z = 3.1L V6 GM, V/W = 6VD1 3.2L. No transmission table."),
    "is_1998": mid("89d04d52-a600-4ba0-982d-43aa688f1137",
                   "NHTSA 01-22-N11B-6340, Isuzu Motors 1997-04-01, VIN for MODEL YEAR 1998 (read as page images 2026-11-05)",
                   "Position 5 (JAC, 4S2): J = Trooper 4x4, K = Rodeo or Amigo 4x2, M = Rodeo or Amigo 4x4; (4S6) K/M = Passport; (JAE) J = SLX. Position 7: 5 = Utility 2-door LWB, 7 = Utility 2-door SWB, 8 = Utility 4-door. Position 8: D = X22SE 2.2L L4 (Holden), W = 6VD1 3.2L V6, X = 6VE1 3.5L V6. No transmission table."),
    "wiki_isuzu_mu": {"url": "https://en.wikipedia.org/wiki/Isuzu_MU",
                      "doc": "Wikipedia, Isuzu MU (raw wikitext fetched 2026-11-05)",
                      "says": "Amigo 1989: 'The transmission was initially manual only'; '1992: ... the added availability of a four-speed automatic transmission on the RWD version'. Rodeo 1991: 'available with either a 2.6-liter inline-four ... or a 3.1-liter V6 ... An automatic transmission was available for the V6.' Second generation: 'The Amigo made a comeback in the US for 1998 ... The Amigo was originally only available only as a soft top with a five-speed transmission'; '1999: The Amigo gains a hardtop version and an optional automatic transmission.'"},
    "amigo_1998_reviews": {"url": "https://www.cars.com/reviews/star-telegram-coms-view-1420689180647",
                           "doc": "Star-Telegram review reprinted on Cars.com, and Drive Chicago 1998 Isuzu Amigo review https://drivechicago.com/reviews/article/655/ (both seen via web search 2026-11-05 during verification; pages not fetched)",
                           "says": "Star-Telegram: the five-speed manual was the sole transmission on '98 models; a four-speed automatic was to be offered with the V-6 starting in 1999. Drive Chicago: Isuzu sells the Amigo only with a five-speed manual; an automatic will not be offered until the 1999 models."},
    "rx8_2004_launch": {"url": "https://www.cars.com/articles/2004-mazda-rx-8-whats-new-1420687138978",
                        "doc": "Cars.com '2004 Mazda RX-8: What's New' and Mazda's 2004 RX-8 pricing announcement (seen via web search 2026-11-05 during verification; pages not fetched)",
                        "says": "2004 RX-8: 238 hp with the six-speed manual; 197 hp with the four-speed automatic (Sport Shift). Automatic from $25,180, manual from $26,680."},
    "edmunds_rodeo_1996": {"url": "https://www.edmunds.com/isuzu/rodeo/1996/review",
                           "doc": "Edmunds 1996 Isuzu Rodeo review, and Consumer Guide used 1991-97 Isuzu Rodeo https://consumerguide.com/used/1991-97-isuzu-rodeo/ (seen via web search 2026-11-05; pages not fetched)",
                           "says": "Edmunds: the 2.6-liter four-cylinder 'powers the two-wheel-drive S edition, which comes only with manual shift'. Consumer Guide (1991-97): the price leader was the 2-wheel-drive S, with a 4-cylinder engine and 5-speed manual."},
    "is_epa_only": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                    "doc": "EPA vehicles.csv; web search 2026-11-05 found no manufacturer or editorial text saying these engines were manual-only",
                    "says": "Row ids quoted in the rule. EPA is the only source for the manual-only claim, so the rule stays a candidate."},
    "sz_samurai": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                   "doc": "EPA vehicles.csv (only source for the claim) + Wikipedia Suzuki Jimny (US Samurai 1986-1995, no transmission statement) + vPIC decodes of lot VINs (model Samurai)",
                   "says": "Every Samurai row 1986-1995 (19 rows, 2871 ... 12499) is Manual 5-spd. The JS4 JC line code is taken from the lot VINs and vPIC, not from a Suzuki filing."},
    "is_1997": mid("5cf7fd0f-5168-4a7e-b720-ea2b6f19b297",
                   "NHTSA 01-22-N11B-6088, Isuzu Motors 1996-04-26, VIN for 1997 model year",
                   "MPV/light truck: 4 GVWR/brake, 5 line/chassis/restraint (J Trooper 4x4, K Rodeo 4x2, M Rodeo 4x4; 4S6 Passport; JAE SLX), 6 series, 7 body, 8 engine, 11 plant. No transmission field."),
    "is_2002": mid("9d4ae26c-6c10-46ba-9f08-3cbb710e7a07",
                   "NHTSA 01-022-N11B-7861, Isuzu 2000-09-06, 2002MY VIN decoding information (text layer)",
                   "Section C (MPV/light truck): 4 GVWR/brake, 5 line/chassis/restraint (Axiom, Trooper, Rodeo, Rodeo Sport, VehiCROSS, Passport), 6 series, 7 body type, 8 engine (Y22SE 2.2, 6VD1 3.2, 6VE1 3.5). No transmission field."),
    # --- EPA ------------------------------------------------------------
    "epa": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
            "doc": "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29, sha256 33d32caa...b22f), local copy scraper/manual_detect/epa/vehicles.csv",
            "says": "Row ids quoted in each rule."},
}


# ---------------------------------------------------------------------------
# Rules. Each rule: WMIs, VIN model-year range, fixed characters (1-based
# position -> allowed characters), the code position and a code table
# {char: (claim, meaning, (first_year, last_year))}. A code only fires inside
# its own year range, which is the span the cited filings define it for.
# ---------------------------------------------------------------------------
FHI = ["JF1", "JF2"]          # Fuji Heavy Industries / Subaru Corp., Gunma (incl. Subaru-built Scion FR-S / Toyota 86, line ZN)
SIA = ["4S3", "4S4"]          # Subaru of Indiana Automotive (4S2/4S6 are Isuzu/Honda-badged SIA products: not Subaru's scheme)
M, A = "manual", "automatic"

RULES = [
    # ---------------- Subaru: character 11 = plant + transmission ----------
    dict(id="subaru_fhi_1985_1986_char11", make="Subaru", wmi=FHI, years=(1985, 1986), fixed={}, pos=11,
         codes={"A": (M, "Gunma 4-speed manual", (1985, 1986)),
                "B": (M, "Gunma 5-speed manual", (1985, 1986)),
                "D": (M, "Gunma 4WD 4/5-speed manual", (1985, 1986)),
                "E": (M, "Gunma 4x2 dual-range 4WD 4/5-speed manual", (1985, 1986)),
                "C": (A, "Gunma automatic", (1985, 1986)),
                "F": (A, "Gunma automatic 4WD", (1985, 1986))},
         models="every Gunma-built Subaru (GL/DL/RX/XT/Brat/Hatchback), MY1985-1986",
         cites=["sub_1986"], epa_ids=[]),
    dict(id="subaru_fhi_1989_char11", make="Subaru", wmi=FHI, years=(1989, 1989), fixed={}, pos=11,
         codes={"B": (M, "5MT", (1989, 1989)),
                "D": (M, "4WD 5MT", (1989, 1989)),
                "G": (M, "Full time 4WD MT", (1989, 1989)),
                "4": (M, "4WD 4MT Hatchback", (1989, 1989)),
                "C": (A, "AT & ECVT", (1989, 1989)),
                "F": (A, "4WD AT", (1989, 1989)),
                "H": (A, "Full time 4WD AT", (1989, 1989))},
         models="every Gunma-built Subaru (Justy, DL/GL/RX, XT/XT6, Loyale line), MY1989. Code E ('4WD, Dual-range') is left out: the 1989 table does not state its transmission",
         cites=["sub_1989"], epa_ids=[]),
    dict(id="subaru_fhi_1990_1994_char11", make="Subaru", wmi=FHI, years=(1990, 1994), fixed={}, pos=11,
         codes={"B": (M, "Gunma FWD 5-speed manual (MT5)", (1990, 1994)),
                "D": (M, "Gunma on-demand 4WD / AWD 5-speed manual", (1990, 1994)),
                "G": (M, "Gunma full-time AWD 5-speed manual", (1990, 1994)),
                "C": (A, "Gunma 3-speed automatic or ECVT (Justy)", (1990, 1994)),
                "F": (A, "Gunma 4WD 3-speed automatic or ECVT", (1990, 1994)),
                "H": (A, "Gunma full-time AWD 4-speed automatic (4EAT)", (1990, 1994)),
                "K": (A, "Gunma FWD 4-speed automatic (4EAT)", (1990, 1994)),
                "P": (A, "Gunma full-time AWD E4AT for Postal Service", (1994, 1994))},
         models="Justy, Loyale, XT/XT6, Legacy, Impreza, SVX built in Gunma (JF1/JF2), MY1990-1994",
         cites=["sub_1990", "sub_1991", "sub_1994"], epa_ids=[]),
    dict(id="subaru_fhi_G_H_1995_2025_char11", make="Subaru", wmi=FHI, years=(1995, 2025), fixed={}, pos=11,
         codes={"G": (M, "Gunma (Yajima) full-time AWD 5MT/6MT", (1995, 2025)),
                "B": (M, "Gunma FWD 5MT (Impreza / Legacy FWD)", (1995, 1996)),
                "H": (A, "Gunma (Yajima) full-time AWD automatic / CVT", (1995, 2025)),
                "K": (A, "Gunma FWD 4-speed automatic (SVX L, Legacy/Impreza FWD)", (1995, 1996))},
         models="Gunma-built Impreza, WRX/STI, Forester, Legacy/Outback (Gunma builds), Crosstrek, SVX, MY1995-2025 (MY2026 not ruled: no MY2026 filing read)",
         cites=["sub_1994", "sub_1996", "sub_1997", "sub_1999", "sub_2001_forester", "sub_2002", "sub_2003",
                "sub_2004_impreza", "sub_2006", "sub_2009_forester", "sub_2009_impreza",
                "sub_2012", "sub_2014_forester", "sub_2014", "sub_2014_b", "sub_2017", "sub_2018", "sub_2022"], epa_ids=[]),
    dict(id="subaru_fhi_L_6mt_2006_2014_char11", make="Subaru", wmi=FHI, years=(2006, 2014), fixed={}, pos=11,
         codes={"L": (M, "Gunma full-time AWD 6-speed manual (WRX STI)", (2006, 2014))},
         models="Impreza WRX STI (and other 6MT Gunma builds), MY2006-2014",
         cites=["sub_2006", "sub_2009_impreza", "sub_2012", "sub_2014_b"], epa_ids=[]),
    dict(id="subaru_fhi_main_plant_2014_2025_char11", make="Subaru", wmi=FHI, years=(2014, 2025), fixed={}, pos=11,
         codes={"9": (M, "Gunma Main Plant 5MT/6MT", (2014, 2025)),
                "8": (A, "Gunma Main Plant CVT / 6AT", (2014, 2025))},
         models="Main-Plant builds: Impreza/XV Crosstrek (2014+), WRX/STI, BRZ, Scion FR-S, Toyota 86 / GR86, MY2014-2025 (MY2026 not ruled: no MY2026 filing read)",
         cites=["sub_2014_b", "sub_2017", "sub_2018", "sub_2022", "sub_2025"], epa_ids=[]),
    dict(id="subaru_fhi_brz_frs_2013_char11", make="Subaru", wmi=["JF1"], years=(2013, 2013), fixed={4: "Z", 5: "CN"}, pos=11,
         codes={"1": (M, "FHI 6-speed manual (BRZ JF1ZC / Scion FR-S JF1ZN)", (2013, 2013)),
                "2": (A, "FHI 6-speed automatic (BRZ / FR-S)", (2013, 2013))},
         models="MY2013 Subaru BRZ (JF1ZC) and Scion FR-S (JF1ZN) only; MY2013 Impreza/XV also carry 1/2 but no filing for them was found, so they are not ruled",
         cites=["sub_2013_brz"], epa_ids=[]),
    dict(id="subaru_sia_1990_1996_char11", make="Subaru", wmi=SIA, years=(1990, 1996), fixed={}, pos=11,
         codes={"1": (M, "SIA FWD 5-speed manual", (1990, 1996)),
                "3": (M, "SIA 4WD 5-speed manual (1990 table)", (1990, 1990)),
                "6": (M, "SIA full-time AWD 5-speed manual", (1990, 1996)),
                "2": (A, "SIA 3-speed automatic (1990 table)", (1990, 1990)),
                "5": (A, "SIA 4WD 3-speed automatic (1990 table)", (1990, 1990)),
                "7": (A, "SIA full-time AWD 4-speed automatic", (1990, 1996)),
                "8": (A, "SIA full-time AWD E4AT for Postal Service", (1994, 1994)),
                "9": (A, "SIA FWD 4-speed automatic", (1990, 1996))},
         models="Lafayette-built Legacy (4S3/4S4), MY1990-1996",
         cites=["sub_1990", "sub_1994", "sub_1996"], epa_ids=[]),
    dict(id="subaru_sia_1997_2009_char11", make="Subaru", wmi=SIA, years=(1997, 2009), fixed={}, pos=11,
         codes={"6": (M, "SIA full-time AWD 5-speed manual", (1997, 2009)),
                "7": (A, "SIA full-time AWD 4-speed automatic", (1997, 2009)),
                "4": (A, "SIA full-time AWD 5-speed automatic", (2005, 2009)),
                "5": (A, "SIA full-time AWD 4AT sport-shift", (2006, 2006))},
         models="Lafayette-built Legacy, Outback, Baja, B9 Tribeca/Tribeca, MY1997-2009",
         cites=["sub_1996", "sub_2001_legacy", "sub_2002", "sub_2003", "sub_2006"], epa_ids=[]),
    dict(id="subaru_sia_2010_2025_char11", make="Subaru", wmi=SIA, years=(2010, 2025), fixed={}, pos=11,
         codes={"1": (M, "SIA full-time AWD 6MT (Legacy/Outback) / 5MT (Impreza)", (2010, 2025)),
                "2": (A, "SIA full-time AWD 5-speed automatic", (2010, 2014)),
                "3": (A, "SIA full-time AWD CVT", (2010, 2025)),
                "4": (A, "SIA full-time AWD 5-speed automatic (Tribeca)", (2010, 2014))},
         models="Lafayette-built Legacy, Outback, Tribeca, Impreza (2017+), Crosstrek (2024+), Ascent, MY2010-2025 (MY2026 not ruled: no MY2026 filing read)",
         cites=["sub_2012", "sub_2014", "sub_2014_b", "sub_2017", "sub_2018", "sub_2022", "sub_2025"], epa_ids=[]),

    # ---------------- Mazda: character 8 = engine type -------------------
    dict(id="mazda_rx8_2004_char8_engine_power", make="Mazda", wmi=["JM1"], years=(2004, 2004),
         fixed={4: "F", 5: "E", 6: "1", 7: "7"}, pos=8,
         codes={"3": (M, "13B HP (High Power, 6-port, 247 hp filed / 238 hp marketed): North-American RX-8 6-speed manual only", (2004, 2004)),
                "N": (A, "13B STD (Standard Power, 4-port, 207 hp filed / 197 hp marketed): North-American RX-8 4-speed automatic only", (2004, 2004))},
         models="MY2004 Mazda RX-8 (JM1FE17*)",
         cites=["mz_2004_rx8", "wiki_rx8", "rx8_2004_launch", "mz_vpic_rx8", "epa"], epa_ids=["19485 (2004 RX-8 Manual 6-spd)", "19486 (2004 RX-8 Automatic (S4))"]),
    dict(id="mazda_rx8_2005_char8_engine_power", make="Mazda", wmi=["JM1"], years=(2005, 2005),
         fixed={4: "F", 5: "E", 6: "1", 7: "7"}, pos=8, candidate=True,
         codes={"3": (M, "13B High Power (2004 code meaning carried to 2005)", (2005, 2005)),
                "N": (A, "13B Standard Power (2004 code meaning carried to 2005)", (2005, 2005))},
         models="MY2005 Mazda RX-8 (JM1FE17*). CANDIDATE ONLY: no MY2005 Mazda filing was found in MID, and vPIC's 2005-2008 pattern for FE173 says '238 hp for MT; 212 hp for AT'",
         cites=["mz_2004_rx8", "mz_2006", "mz_2008", "wiki_rx8", "mz_vpic_rx8", "epa"], epa_ids=["20621 (2005 RX-8 Manual 6-spd)", "20622 (2005 RX-8 Automatic (S4))"]),
    dict(id="mazda_rx8_2009_2011_char8_engine_power", make="Mazda", wmi=["JM1"], years=(2009, 2011),
         fixed={4: "F", 5: "E", 6: "1", 7: "7C"}, pos=8,
         codes={"2": (M, "13B High Power, California (232 hp): 6-speed manual only", (2009, 2011)),
                "4": (M, "13B High Power, Federal (232 hp): 6-speed manual only", (2009, 2011)),
                "M": (A, "13B Standard Power, California (212 hp): 6-speed automatic only", (2009, 2011)),
                "P": (A, "13B Standard Power, Federal (212 hp): 6-speed automatic only", (2009, 2011))},
         models="MY2009-2011 Mazda RX-8 (JM1FE17* MY2009, JM1FE1C* MY2009-2011). MY2005-2008 FE173 is NOT ruled: the 6AT also used the High Power code then",
         cites=["mz_2009", "mz_2011", "mz_2008", "mz_vpic_rx8", "wiki_rx8", "epa"], epa_ids=["25224/25225 (2009)", "28557/28558 (2010)", "30614/30615 (2011): Manual 6-spd and Automatic (S6) only"]),
    dict(id="mazda_mazdaspeed3_2007_2009_char8_L3T", make="Mazda", wmi=["JM1"], years=(2007, 2009),
         fixed={4: "B", 5: "K", 6: "13", 7: "4"}, pos=8,
         codes={"L": (M, "L3T 2.3L DISI Turbo, Federal: MAZDASPEED3, 6-speed manual only", (2007, 2009)),
                "M": (M, "L3T 2.3L DISI Turbo, California: MAZDASPEED3, 6-speed manual only", (2007, 2009))},
         models="MY2007-2009 MAZDASPEED3 (JM1BK[1|3]4[L|M]; feed may call it Mazda3)",
         cites=["mz_2007", "mz_2008", "mz_2009", "mz_vpic_ms", "wiki_ms3", "epa"], epa_ids=["23183 (2007 Mazda 3 2.3 'MAZDA3 T/C' Manual 6-spd; no turbo automatic)", "24387 (2008 Speed 3 Manual 6-spd)", "25503 (2009 Speed 3 Manual 6-spd)"]),
    dict(id="mazda_mazdaspeed3_2010_2013_char8_L3T", make="Mazda", wmi=["JM1"], years=(2010, 2013),
         fixed={4: "B", 5: "L", 6: "1", 7: "H"}, pos=8,
         codes={"3": (M, "L3T 2.3L Turbo, Federal: MAZDASPEED3, 6-speed manual only", (2010, 2013)),
                "4": (M, "L3T 2.3L Turbo, California: MAZDASPEED3, 6-speed manual only", (2010, 2013))},
         models="MY2010-2013 MAZDASPEED3 (JM1BL1H3 / BL1H4)",
         cites=["mz_2010_mazda3", "mz_2011", "mz_vpic_ms", "wiki_ms3", "epa"], epa_ids=["26420 (2010)", "30402 (2011)", "31584 (2012)", "32984 (2013): Speed 3 Manual 6-spd, the only Speed 3 rows"]),
    dict(id="mazda_mazdaspeed6_2006_2007_char8_L3T", make="Mazda", wmi=["JM1"], years=(2006, 2007),
         fixed={4: "G", 5: "G", 6: "1", 7: "2"}, pos=8,
         codes={"L": (M, "L3T 2.3L Turbo (274 hp): MAZDASPEED6, 6-speed manual + AWD only", (2006, 2007))},
         models="MY2006-2007 MAZDASPEED6 (JM1GG12L only, the one code both filings list; Japan-built Mazda6 with the L3T engine; every other Mazda6 is 1YV)",
         cites=["mz_2006", "mz_2007", "mz_vpic_ms", "wiki_ms6", "epa"], epa_ids=["21987 (2006 Mazda 6 2.3 turbo AWD Manual 6-spd)", "23261 (2007 'MAZDA6 T/C' AWD Manual 6-spd); no turbo or AWD automatic row"]),
    dict(id="mazda_mazdaspeed_protege_2003_char8_FSD170", make="Mazda", wmi=["JM1"], years=(2003, 2003),
         fixed={4: "B", 5: "J", 6: "2", 7: "2"}, pos=8,
         codes={"7": (M, "FSD 2.0L 170 hp (MAZDASPEED Protege), D&P frontal air bags: 5-speed manual only", (2003, 2003)),
                "8": (M, "FSD 2.0L 170 hp (MAZDASPEED Protege), D&P frontal + side air bags: 5-speed manual only", (2003, 2003))},
         models="MY2003 MAZDASPEED Protege (JM1BJ227 / BJ228). The 2001 BJ227 code meant something else and is out of scope",
         cites=["mz_2003_protege", "mz_vpic_ms", "wiki_msp", "edmunds_msp", "lot_msp_serials", "epa"],
         epa_ids=["18552 (2003 Protege/Protege 5 2.0 Manual 5-spd, Premium fuel): the ONLY premium-fuel 2003 Protege configuration; the automatics 18551/18554 are regular fuel"]),

    # ---------------- Mitsubishi / Dodge: character 8 = engine -----------
    dict(id="mitsubishi_3000gt_stealth_twin_turbo_1991_1992_char8", make="Mitsubishi", wmi=["JA3", "JB3"], years=(1991, 1992),
         fixed={5: "DE"}, pos=8,
         codes={"C": (M, "3.0L DOHC MPI twin turbo + intercooler (3000GT VR-4 / Stealth R/T Turbo): 5-speed manual AWD only", (1991, 1992))},
         models="Mitsubishi 3000GT (JA3) and Dodge Stealth (JB3), lines D/E, MY1991-1992",
         cites=["mi_1992", "mi_vpic", "epa"], epa_ids=["7667 (1991 3000 GT turbo AWD Manual 5-spd)", "8764 (1992)", "7590 (1991 Stealth turbo AWD Manual 5-spd)", "8680 (1992 Stealth)"]),
    dict(id="mitsubishi_3000gt_stealth_twin_turbo_1993_1999_char8", make="Mitsubishi", wmi=["JA3", "JB3"], years=(1993, 1999),
         fixed={5: "MNVW"}, pos=8,
         codes={"K": (M, "3.0L DOHC MPI 2 turbo + 2 intercooler (3000GT VR-4 / Spyder VR-4 / Stealth R/T Turbo): manual AWD only (5MT 1993, 6MT 1994-99)", (1993, 1999))},
         models="Mitsubishi 3000GT / 3000GT Spyder (JA3) and Dodge Stealth (JB3, to 1996), MY1993-1999",
         cites=["mi_1993", "mi_1995", "mi_1998", "mi_vpic", "epa"],
         epa_ids=["9823 (1993 3000 GT turbo Manual 5-spd)", "10789, 11742, 12641, 13382, 14107, 14890 (1994-1999 3000 GT turbo Manual 6-spd)", "11744, 12643, 13384, 14109 (Spyder turbo Manual 6-spd)", "9734, 10713, 11669, 12581 (Stealth turbo manual)"]),
    dict(id="mitsubishi_montero_sport_24_4x2_1997_1999_char8", make="Mitsubishi", wmi=["JA4"], years=(1997, 1999),
         fixed={5: "S"}, pos=8, candidate=True,
         codes={"G": (M, "2.4L 4-cyl (4G64) in the 4x2 Montero Sport line S: EPA lists only a 5-speed manual", (1997, 1999))},
         models="MY1997-1999 Mitsubishi Montero Sport ES 4x2 2.4 (JA4 LS21G on the lots). CANDIDATE ONLY: EPA is the only source for manual-only, and the code meaning is from vPIC decodes, not a filing read",
         cites=["mi_montero_sport", "epa"], epa_ids=["29580 (1997)", "14677 (1998)", "15482 (1999) Montero Sport 2WD 2.4 Manual 5-spd: the only 2.4 rows"]),

    # ---------------- Isuzu (and SIA-built 4S1/4S2): 5 line/chassis, 7 body, 8 engine --
    dict(id="isuzu_rodeo_26_4x2_lineG_1991_1995_char8", make="Isuzu", wmi=["4S2"], years=(1991, 1995),
         fixed={5: "G", 7: "8"}, pos=8,
         codes={"E": (M, "4ZE1 2.6L L4 in a Rodeo 4x2 (line G = utility 4x2 in the MY1992 table, Rodeo 4x2 in the MY1995 table; body 8 = utility 4-door): Rodeo S 2WD, 5-speed manual only", (1991, 1995))},
         models="MY1991-1995 Isuzu Rodeo S 4x2 with the 2.6L four-cylinder, line code G (4S2 G58E). Line G is defined in the MY1992 and MY1995 tables only (not in MY1997), so it is not ruled after 1995. The Honda Passport twin (4S6) is not ruled (Honda make)",
         cites=["is_1992", "is_1995", "wiki_isuzu_mu", "edmunds_rodeo_1996", "epa"],
         epa_ids=["8452 (1991)", "9522 (1992)", "10518 (1993)", "11469 (1994)", "12429 (1995): Rodeo 2WD 2.6 Manual 5-spd, the only 2.6 Rodeo rows each year"]),
    dict(id="isuzu_rodeo_26_4x2_lineK_1995_1997_char8", make="Isuzu", wmi=["4S2"], years=(1995, 1997),
         fixed={5: "K", 7: "8"}, pos=8,
         codes={"E": (M, "4ZE1 2.6L L4 in a Rodeo 4x2 with driver & passenger air bags (line K; body 8 = utility 4-door): Rodeo S 2WD, 5-speed manual only", (1995, 1997))},
         models="MY1995-1997 Isuzu Rodeo S 4x2 with the 2.6L four-cylinder, line code K (4S2 K58E). Line K is first defined in the MY1995 table (absent from MY1992), so it is not ruled before 1995. The Honda Passport twin (4S6) is not ruled (Honda make)",
         cites=["is_1995", "is_1997", "wiki_isuzu_mu", "edmunds_rodeo_1996", "epa"],
         epa_ids=["12429 (1995)", "13168 (1996)", "13895 (1997): Rodeo 2WD 2.6 Manual 5-spd, the only 2.6 Rodeo rows each year"]),
    dict(id="isuzu_amigo_1998_char7", make="Isuzu", wmi=["4S2"], years=(1998, 1998),
         fixed={5: "KM"}, pos=7,
         codes={"7": (M, "Amigo (line K/M Rodeo-or-Amigo, body 7 = utility 2-door short wheelbase): every 1998 Amigo was manual (automatic optional from 1999)", (1998, 1998))},
         models="MY1998 Isuzu Amigo, every engine (2.2 X22SE, 3.2 6VD1) and drive",
         cites=["is_1998", "wiki_isuzu_mu", "amigo_1998_reviews", "epa"],
         epa_ids=["14659 (1998 Amigo 2WD 2.2)", "14735 (1998 Amigo 4WD 2.2)", "14736 (1998 Amigo 4WD 3.2): all Manual 5-spd, no automatic row"]),
    dict(id="isuzu_4zd1_23_4x2_1988_1995_char8", make="Isuzu", wmi=["JAA", "JAC", "4S1"], years=(1988, 1995),
         fixed={5: "LG"}, pos=8, candidate=True,
         codes={"L": (M, "4ZD1 2.3L L4 in a 4x2 Pickup (line L) or Amigo (line G): EPA lists only a 5-speed manual", (1988, 1995))},
         models="MY1988-1995 Isuzu Pickup 4x2 2.3 and Amigo 4x2 2.3. CANDIDATE ONLY: EPA is the only source for manual-only (no Isuzu, editorial or encyclopedia text found)",
         cites=["is_1992", "is_1995", "is_epa_only", "epa"],
         epa_ids=["4797, 5934, 7002, 8131, 9218, 10231, 11185, 11186, 12149 (Pickup 2WD 2.3, 1988-1995)", "6276, 7335, 8450, 9519, 10515 (Amigo 2WD 2.3, 1989-1993): all Manual 5-spd"]),
    dict(id="isuzu_4ze1_26_4x4_pickup_amigo_1989_1995_char8", make="Isuzu", wmi=["JAA", "JAC", "4S1"], years=(1989, 1995),
         fixed={5: "R"}, pos=8, candidate=True,
         codes={"E": (M, "4ZE1 2.6L L4 in the 4x4 conventional-cab line R (Pickup 4x4; the 1989-1991 Amigo 4x4 also decodes here): EPA lists only a 5-speed manual", (1989, 1995))},
         models="MY1989-1995 Isuzu Pickup 4x4 2.6 and early Amigo 4x4 2.6. CANDIDATE ONLY: EPA is the only source; MY1988 is excluded because EPA lists a 4-speed automatic for the 1988 2.6 4WD",
         cites=["is_1992", "is_1995", "is_epa_only", "wiki_isuzu_mu", "epa"],
         epa_ids=["6144, 7215, 8338, 9399, 10400, 11354, 12318 (Pickup 4WD 2.6, 1989-1995)", "6349, 7408, 8511, 9584, 10571, 11536 (Amigo 4WD 2.6, 1989-1994): all Manual 5-spd"]),
    dict(id="isuzu_trooper_23_1986_1987_char8", make="Isuzu", wmi=["JAA", "JAC"], years=(1986, 1987),
         fixed={5: "H"}, pos=8, candidate=True,
         codes={"L": (M, "2.3L gasoline L4 in the Trooper (II) 4x4 line H: EPA lists only a 5-speed manual", (1986, 1987))},
         models="MY1986-1987 Isuzu Trooper / Trooper II 2.3. CANDIDATE ONLY: EPA is the only source and the code meaning is from vPIC decodes (no 1986-87 Isuzu filing read)",
         cites=["is_epa_only", "epa"], epa_ids=["Trooper 1986 2.3 4WD and 1987 2.3 4WD: Manual 5-spd only (the 2.2 turbo-diesel rows are manual too)"]),

    # ---------------- Suzuki: model code (no transmission field) -------------
    dict(id="suzuki_samurai_1986_1995_char4_5", make="Suzuki", wmi=["JS3", "JS4"], years=(1986, 1995),
         fixed={4: "J"}, pos=5, candidate=True,
         codes={"C": (M, "Samurai line (JS4 JC..): EPA lists only a 5-speed manual for every Samurai 1986-1995", (1986, 1995))},
         models="MY1986-1995 Suzuki Samurai. CANDIDATE ONLY: EPA is the only source for manual-only and the JC code comes from lot VINs + vPIC, not a Suzuki filing read",
         cites=["sz_samurai", "epa"], epa_ids=["2871, 2872, 4099, 4100, 5219, 5220, 6367, 6368, 7426, 7427, 8463, 8531, 8532, 9536, 9604, 10527, 10592, 11561, 12499: every Samurai row is Manual 5-spd"]),
]

# How the claim is supported. "transmission_code": the manufacturer's own VIN
# table names the transmission. "engine_code" / "line_body_code": the
# manufacturer's table names an engine or model, and independent sources
# (EPA + text) say that engine or model was sold only with a manual.
RULE_BASIS = {
    "mazda": "engine_code", "mitsubishi": "engine_code",
    "isuzu_rodeo": "engine_code", "isuzu_4z": "engine_code", "isuzu_trooper": "engine_code",
    "isuzu_amigo": "line_body_code", "suzuki": "line_body_code",
}

RULE_NOTES = {
    "mazda_rx8_2005_char8_engine_power": "Why only a candidate: no MY2005 Mazda filing is in MID (the next one, ORG322 / 10376, is MY2006 and does not refile the RX-8). vPIC decodes 2005 FE17N as '13B Std' (207 hp) and FE173 as '13B High Power' with OtherEngineInfo '238 hp for MT; 212 hp for AT', a note shared with 2006-2008, when the 6AT did use FE173 (MY2008 filing: '232HP (MT) / 212HP (AT)'). On the lots FE17N appears in 2004-2005 only, which fits the 4AT Standard-Power car being dropped for 2006. Promote it only with a MY2005 Mazda document.",
    "mazda_rx8_2009_2011_char8_engine_power": "Standard Power vs High Power is the engine output, not the transmission. The manual-only reading rests on Wikipedia ('Automatic versions all had lower output/lower rpm engines'; NA 6MT 232 hp, 6AT 212 hp) and EPA (only Manual 6-spd and Automatic (S6) each year). MY2005-2008 FE173 is NOT ruled: the MY2008 filing gives it '232HP (MT) / 212HP (AT)'.",
    "mazda_mazdaspeed_protege_2003_char8_FSD170": "The filing's 170 hp FSD (BJ227/BJ228) is the MAZDASPEED Protege (Wikipedia: 170 hp turbocharged, 4,500 built). Lot serials for BJ227 are a separate block (641697-648720) from all other 2003 Proteges (101133-221210). The 2001 BJ227 code (Protege MP3 era) is outside the rule's years.",
    "isuzu_rodeo_26_4x2_lineG_1991_1995_char8": "Split from isuzu_rodeo_26_4x2_1991_1997_char8 by the 2026-11-05 verification: line G is defined in the MY1992 table ('Utility 4x2') and the MY1995 table ('Rodeo 4x2') but not in the MY1997 table, so G is ruled 1991-1995 only. Body 8 and engine E mean the same in all three tables. On the lots and in the vPIC cache, 4S2 G..8 VINs carry model-year codes M-S (1991-1995) only. The 2.6 Rodeo was 4x2 only (EPA has no 2.6 4WD Rodeo row).",
    "isuzu_rodeo_26_4x2_lineK_1995_1997_char8": "Split from isuzu_rodeo_26_4x2_1991_1997_char8 by the 2026-11-05 verification: line K ('Rodeo 4x2 with driver & passenger inflatable restraint') appears in the MY1995 and MY1997 tables but not in the MY1992 table, so K is ruled 1995-1997 only. On the lots and in the vPIC cache, 4S2 K..8E VINs carry model-year codes S-V (1995-1997) only.",
    "isuzu_amigo_1998_char7": "Applies to every engine: EPA lists 1998 Amigo 2WD 2.2, 4WD 2.2 and 4WD 3.2, all Manual 5-spd; Wikipedia dates the Amigo's optional automatic to 1999.",
}

# ---------------------------------------------------------------------------
# Adversarial verification, 2026-11-05 (second session). For each rule: what was
# re-opened, which counterexample searches were run, scope edges checked, and
# what changed. "filing re-read" means the MID PDF was downloaded again from the
# cited displayfile URL and its VIN table read (as page images where scanned).
# The vPIC-cache counterexample counts are recomputed on every run
# (verified.vpic_cache_scan).
# ---------------------------------------------------------------------------
VERIFIED_ON = "2026-11-05"
_SUB_COMMON = ("vPIC cache scan: every cached VIN in scope (lots and history, ~470k VINs) whose decode carries a transmission was "
               "compared with the rule (see vpic_cache_scan); this agreement is partly circular because vPIC is built from the same "
               "filings. Independent sanity check on vPIC trims (VDS characters, not character 11): B9 Tribeca (automatic-only) "
               "carries only SIA 4; Impreza STI carries only L; Outback 3.0R / 3.0R L.L.Bean carry only automatic codes 4/7; "
               "Legacy/Outback 2.5GT split 6 (5MT) / 4 (5AT); Forester 2.5XT G/H; no automatic-only trim carries a manual code. "
               "No VIN-bearing lot car has a listing transmission, so there is no non-vPIC label to test against.")
VERIFIED = {
    "subaru_fhi_1985_1986_char11": {"verdict": "verified (filing not re-read)", "checks": [
        "Citation sub_1986 not re-read in this pass (scanned booklet); relies on the first session's reading. 0 lot cars newly confirmed.",
        "1989 and 1990 tables re-read use the same letter meanings for B/C/D/F, consistent with the 1985-86 reading.",
        _SUB_COMMON]},
    "subaru_fhi_1989_char11": {"verdict": "verified (filing not re-read)", "checks": [
        "Citation sub_1989 not re-read in this pass; code E (dual range) correctly left out. 0 lot cars newly confirmed.", _SUB_COMMON]},
    "subaru_fhi_1990_1994_char11": {"verdict": "verified", "checks": [
        "Re-read 01-22-N11B-3599 (MY1990) page 2: Gunma/Lafayette table B/1 MT5, C/2 AT3, D/3 4WD MT5, F/5 4WD AT3/ECVT, G/6 F4WD MT5, H/7 F4WD 4EAT, K/9 4EAT, as cited.",
        "Re-read 01-22-N11B-5384 (MY1994) Legacy page: SIA/FHI 1/B 5MT, 6/G full-time AWD 5MT single-range, 7/H full-time AWD E4AT, 9/K E4AT, 8/P full-time AWD E4AT for Postal Service, as cited.",
        "Scope edge: code P is claimed (automatic) only for MY1994; a 1993 P on the lots stays unclaimed.", _SUB_COMMON]},
    "subaru_fhi_G_H_1995_2025_char11": {"verdict": "narrowed (MY2026 removed)", "changes": [
        "Renamed from subaru_fhi_G_H_1995_2026_char11; upper year 2026 -> 2025. The latest Subaru filing read is MY2025 (ORG23706); no MY2026 filing was read, so MY2026 is no longer covered."],
        "checks": [
        "Re-read 01-22-N11B-5909 (MY1996, Impreza FHI B 5MT / G AWD 5MT / H AWD 4AT / K 4AT), 01-22-N11B-9269 (MY2003, FHI G AWD 5MT / H AWD 4AT), ORG225 (MY2006, FHI G AWD 5MT / H AWD 4AT / L AWD 6MT), ORG7191 (MY2009 Impreza, G 5MT / H 4AT / L 6MT), ORG13185 (MY2017), ORG15037 (MY2018), ORG19703 (MY2022), ORG23706 (MY2025): every Gunma table read gives G = full-time AWD 5MT/6MT and H = full-time AWD 4AT/CVT (MY1996 Impreza page also B = 5MT, K = 4AT; SVX H = AWD 4AT). The MY2002 text layer gives G/H = AWD 5MT/4AT; the MY2001 Forester and MY2004 Impreza text layers list the same two rows (letters lost in OCR).",
        "Scope edges: Subaru Solterra is JTM (Toyota Motomachi), not JF1/JF2, so it is outside the WMI scope; Saab 9-2X is JF4, outside; Scion FR-S / Toyota 86 / GR86 use 1/2 (2013) or 9/8 (2014+), never G/H.",
        _SUB_COMMON]},
    "subaru_fhi_L_6mt_2006_2014_char11": {"verdict": "verified", "checks": [
        "Re-read ORG225 (MY2006: FHI L = AWD 6MT) and ORG7191 (MY2009 Impreza: L = full-time AWD 6MT, trims include STI).",
        "vPIC trim check: Impreza STI / STI-S carry only L.", _SUB_COMMON]},
    "subaru_fhi_main_plant_2014_2025_char11": {"verdict": "narrowed (MY2026 removed)", "changes": [
        "Renamed from subaru_fhi_main_plant_2014_2026_char11; upper year 2026 -> 2025 (no MY2026 filing read)."], "checks": [
        "Re-read text layers of ORG13185 (2017), ORG15037 (2018), ORG19703 (2022), ORG23706 (2025): Main Plant 9 = 5MT/6MT and 8 = CVT/6AT for every model listed (WRX, Impreza, Crosstrek, BRZ, Toyota 86/GR86).",
        "MY2014-2016 BRZ / FR-S rest on the plant+transmission table being model-independent (MY2014 Impreza/XV filing ORG9048 cited, not re-read) plus vPIC agreement (FR-S/86 8 and 9 decode automatic/manual, 0 conflicts).",
        _SUB_COMMON]},
    "subaru_fhi_brz_frs_2013_char11": {"verdict": "verified", "checks": [
        "Re-read ORG9621 page images: 2013MY Subaru BRZ (JF1ZC) and Toyota Scion FR-S (JF1ZN) 'Plant of manufacture and transmission type' 1 = FHI 6MT, 2 = FHI 6AT, exactly as cited.",
        "Scope edge: fixed char4 Z / char5 C,N keeps 2013 Impreza/XV codes 1/2 out.", _SUB_COMMON]},
    "subaru_sia_1990_1996_char11": {"verdict": "verified", "checks": [
        "Re-read MY1990 (B/1 MT5 ... K/9 4EAT), MY1994 (1/B 5MT, 6/G AWD 5MT, 7/H AWD E4AT, 9/K E4AT, 8/P Postal E4AT) and 01-22-N11B-5909 MY1996 Legacy page (SIA 1 5MT, 6 Fulltime AWD 5MT, 7 Fulltime AWD 4AT, 9 4AT, 8 'Fulltime AWD for Postal' without a transmission).",
        "Scope edge: code 8 is claimed only for MY1994, where the table names E4AT; MY1996 8 (no transmission given) stays unclaimed.",
        "Counted lot car 4S3BK4258T6312409: body K = station wagon, char 6 = 4 (2.2 AWD), char 11 = 6 = Fulltime AWD 5MT per the MY1996 table.",
        _SUB_COMMON]},
    "subaru_sia_1997_2009_char11": {"verdict": "verified", "checks": [
        "Re-read MY2003 (01-22-N11B-9269: SIA 5 AWD 4AT-SS, 6 AWD 5MT, 7 AWD 4AT) and MY2006 (ORG225: SIA 4 AWD 5AT, 5 AWD 4AT-SS, 6 AWD 5MT, 7 AWD 4AT); text layers of MY2001 Legacy and MY2002 agree (6 = 5MT, 7 = 4AT).",
        "Scope edge: the MY2006 table has no SIA 6MT code, so a 6MT Legacy spec.B would carry 6 ('AWD 5MT'); the claim (manual) is still right. SIA 5 in 2003-2005 is an automatic left unclaimed (conservative).",
        _SUB_COMMON]},
    "subaru_sia_2010_2025_char11": {"verdict": "narrowed (MY2026 removed)", "changes": [
        "Renamed from subaru_sia_2010_2026_char11; upper year 2026 -> 2025 (no MY2026 filing read)."], "checks": [
        "Re-read text layers of 2017, 2018, 2022, 2025 filings: SIA 1 = 6MT/5MT, 3 = CVT in every table; MY2012 / MY2014 (scanned) cited for 2 = 5AT and 4 = Tribeca 5AT, not re-read.",
        "SIA-built Toyota Camry is 4T1 and Isuzu/Honda SIA builds are 4S2/4S6, all outside the WMI scope.", _SUB_COMMON]},
    "mazda_rx8_2004_char8_engine_power": {"verdict": "verified", "checks": [
        "Re-read 01-022-N11B-9546 page images: 2004MY RX-8 JM1 FE17N = 13B STD 207+/-20.7 hp, JM1 FE173 = 13B HP 247+/-24.7 hp; no transmission column, as cited.",
        "Manual-only claim for FE173 in MY2004: Wikipedia RX-8 option table (2004-2005: 4-speed automatic = 4-port; 6-speed manual = 6-port; 5-speed manual with the 4-port 'Not sold in North America'); launch coverage (238 hp six-speed manual vs 197 hp four-speed automatic); EPA 2004 RX-8 has exactly two rows, Manual 6-spd and Automatic (S4).",
        "vPIC decodes 2004 FE173 as '13B (1.3L) HP' (222 hp) and FE17N as 'STD'. vPIC's '238 hp for MT; 212 hp for AT' note appears only on 2005-2008 FE173, which this rule does not cover.",
        "Counterexample search: no FE173 VIN (lots or cache) has a published or vPIC transmission; no listing text names an automatic HP RX-8."]},
    "mazda_rx8_2005_char8_engine_power": {"verdict": "candidate kept uncounted", "checks": [
        "No MY2005 Mazda RX-8 filing; the vPIC 2005 FE173 note mentions an automatic. Not promoted."]},
    "mazda_rx8_2009_2011_char8_engine_power": {"verdict": "verified (inference rests on Wikipedia + EPA; 0 lot cars confirmed)", "checks": [
        "Re-read ORG3973 (MY2009: FE17M California Standard Power, FE172 California High Power, FE17P Federal Standard Power, FE174 Federal High Power) and ORG5728 (MY2011: same four codes as FE1Cx).",
        "Re-read ORG2947 (MY2008): FE173 High Power '232HP (MT) / 212HP (AT)', which is why 2005-2008 is not ruled.",
        "The High = manual / Standard = automatic mapping is inferred: the filings name power, not transmission; North America had only the 232 hp 6MT and 212 hp 6AT (Wikipedia), and EPA lists only Manual 6-spd and Automatic (S6). Residual risk is that Mazda coded an automatic as High Power, as it did in 2008; no lot car is affected today."]},
    "mazda_mazdaspeed3_2007_2009_char8_L3T": {"verdict": "verified", "checks": [
        "Re-read ORG1842 (MY2007), ORG2947 (MY2008, 263HP) and ORG3973 (MY2009): JM1 BK34L / BK14L = 5-door hatchback L3T Turbo Fed., BK34M / BK14M = L3T Turbo Calif.; the same tables give 3/4 = L3V/L3X 2.3 non-turbo and F/G = 2.0, so L/M are turbo-only within BK hatchbacks.",
        "Scope edge: in the MY2007 table 'L' at position 8 also means L3V California on the Mazda5 (JM1 CR29L) and L3T on the CX-7 (JM3 ER29L, automatic-only); the rule's fixed characters (B, K, 1/3, 4) exclude both.",
        "Manual-only: Wikipedia Mazdaspeed3 ('a six-speed manual transmission ... No automatic transmission option was offered'; infobox lists only the 6-speed manual for both generations); EPA turbo Mazda3 rows 2007-2009 are Manual 6-spd only. Canada-market cars (Edmonton yard) are the same 6MT-only model.",
        "Counterexample search: no in-scope VIN has a vPIC or listing transmission."]},
    "mazda_mazdaspeed3_2010_2013_char8_L3T": {"verdict": "verified", "checks": [
        "Re-read ORG4472 (MY2010 Mazda3): JM1 BL1H3 = L3T (2.3L Turbo) Federal, BL1H4 = L3T California, BL1HF = LFX 2.0, BL1H5/6 = L5X 2.5; ORG5728 (MY2011) cited.",
        "MY2012-2013: no filing read; vPIC decodes pattern VINs JM1BL1H3?C/D and JM1BL1H4?C/D as 'L3T Turbo Federal/Canada' / 'L3T Turbo California', Turbo=Yes. The 2012 SKYACTIV 2.0 hatch uses different characters (BL1L / BL1M, engine PE), so H3/H4 were not reassigned.",
        "Manual-only: Wikipedia Mazdaspeed3 (6-speed manual, no automatic); EPA Speed 3 rows 2010-2013 are Manual 6-spd only."]},
    "mazda_mazdaspeed6_2006_2007_char8_L3T": {"verdict": "narrowed (fixed characters 6-7 added)", "changes": [
        "Fixed characters tightened from char4 G, char5 G to char4 G, char5 G, char6 1, char7 2 (JM1GG12L), the only code the MY2006 and MY2007 filings list. vPIC also decodes an unfiled GG14L (hatchback); that is no longer claimed. No lot car changes."],
        "checks": [
        "Re-read ORG322 (MY2006, letter dated 2005-03-14): JM1 GG12L = Mazda 6 sedan L3T (2.3L Turbo) 274+/-27 hp; every other Mazda6 is 1YV. Re-read ORG1842 (MY2007) attachment 3: JM1 GG12L = Mazda6 sedan L3T Turbo; attachment 4: non-turbo Mazda6 = 1YV.",
        "Manual-only: Wikipedia Mazda6 ('All markets received ... a 6-speed manual transmission, and all-wheel drive'); EPA 2006/2007 turbo AWD rows are Manual 6-spd only."]},
    "mazda_mazdaspeed_protege_2003_char8_FSD170": {"verdict": "verified", "checks": [
        "Re-read 01-022-N11B-9298 page images: BJ225/BJ226 = Protege sedan FSD 2.0L 130+/-13 hp; BJ227/BJ228 = Protege sedan FSD 2.0L 170+/-17 hp; BJ245/BJ246 = 5-door hatchback 130 hp.",
        "Manual-only: Edmunds and Cars.com 2003 MAZDASPEED Protege specs (5-speed manual, FWD, LSD); EPA 2003 Protege has one premium-fuel row, 18552 Manual 5-spd, and both automatics are regular fuel. Wikipedia confirms the 170 hp turbo and 4,500 built but states no transmission.",
        "Scope edge: vPIC decodes 2001 BJ227 as FSD 126 hp (a different car), and the rule is limited to MY2003."]},
    "mitsubishi_3000gt_stealth_twin_turbo_1991_1992_char8": {"verdict": "verified (MY1991 code from vPIC)", "checks": [
        "Re-read 01-22-N11B-4081 (MY1992, issued 1990-11-26): 5th-6th D (4-6) / E (7) = Mitsubishi 3000GT / Dodge Stealth; 8th C = 3.0L DOHC MPI T/C I/C, B = 3.0L DOHC MPI, S = 3.0L MPI.",
        "vPIC: 1991 JB3XE74C = Dodge Stealth 'R/T Turbo', Turbo=Yes, intercooled; 1992 JA3XE74C Turbo=Yes; 1991 XD64B / XD54B (non-turbo) decode without turbo.",
        "EPA 1991-1992: the only turbo rows for 3000 GT and Stealth are Manual 5-spd AWD; every automatic row is FWD non-turbo."]},
    "mitsubishi_3000gt_stealth_twin_turbo_1993_1999_char8": {"verdict": "verified", "checks": [
        "Re-read MY1993 (01-22-N11B-4618: K = 3.0 DOHC MPI T/C I/C on the 3000GT / Dodge Stealth line; the M/N line letters were not legible in the OCR and rest on the first session's reading and vPIC), MY1995 (01-22-N11B-5700: K = 3.0 DOHC MPI 2 T/C 2 I/C; 3000GT, Stealth, 3000GT Spyder) and MY1998 (01-22-N11B-6347: K = 3.0 DOHC MPI 2 T/C 2 I/C; 3000GT, 3000GT Spyder) via OCR of the page images.",
        "EPA 1993-1999: every turbo row (3000 GT, Spyder, Stealth) is Manual 5-spd (1993) or Manual 6-spd (1994-1999) AWD; automatics exist only for FWD non-turbo J/H engines.",
        "vPIC: 1996 JA3AN74K = 3000GT VR-4, AWD, 'MPI 2 T/C 2 I/C'."]},
    "mitsubishi_montero_sport_24_4x2_1997_1999_char8": {"verdict": "candidate kept uncounted", "checks": [
        "EPA re-checked: 1997-1999 Montero Sport 2WD 2.4 rows are Manual 5-spd only. No filing or text source; stays a candidate."]},
    "isuzu_rodeo_26_4x2_lineG_1991_1995_char8": {"verdict": "narrowed (split from isuzu_rodeo_26_4x2_1991_1997_char8)", "changes": [
        "Old rule allowed line G and K in every year 1991-1997. Line G is now ruled only 1991-1995 (defined in the MY1992 and MY1995 tables, absent from MY1997). WMI narrowed from 4S2/JAC to 4S2 (the US Rodeo was built only by SIA; no JAC Rodeo VIN exists on the lots or in the cache)."],
        "checks": [
        "Re-read 01-22-N11B-4240 (MY1992) section C: G = Utility 4x2, body 8 = Utility 4-door, engine E = 4ZE1 2.6L L4; and 01-22-N11B-5634 (MY1995): G = Rodeo 4x2, K = Rodeo 4x2 with driver & passenger inflatable restraint, body 8 = Utility 4-door, E = 4ZE1 2.6L L4.",
        "Manual-only: EPA Rodeo 2WD 2.6 is Manual 5-spd only in every year 1991-1997 (automatic rows are V6 only); Wikipedia Isuzu MU ('An automatic transmission was available for the V6'); Edmunds 1996 review (2.6 S 4x2 'comes only with manual shift').",
        "Scope edge: the 2-door Amigo shares line G in 1992 and had an automatic on the RWD 2.6 from 1992 (Wikipedia, EPA), but it is body 7; the rule requires body 8.",
        "Counterexample search: lots + cache 4S2 G..8 VINs carry year codes M-S only; no in-scope VIN has a transmission label."]},
    "isuzu_rodeo_26_4x2_lineK_1995_1997_char8": {"verdict": "narrowed (split from isuzu_rodeo_26_4x2_1991_1997_char8)", "changes": [
        "Line K is now ruled only 1995-1997 (defined in the MY1995 and MY1997 tables, absent from MY1992). WMI narrowed to 4S2."],
        "checks": [
        "Re-read 01-22-N11B-5634 (MY1995) and 01-22-N11B-6088 (MY1997): K = Rodeo 4x2 with driver & passenger inflatable restraint, body 8 = Utility 4-door, E = 4ZE1 2.6L L4 (MY1997 lists only E and V engines).",
        "Manual-only: as the line-G rule (EPA 1995-1997 Rodeo 2WD 2.6 Manual 5-spd only; Edmunds 1996).",
        "Counterexample search: lots + cache 4S2 K..8E VINs carry year codes S-V only; no in-scope VIN has a transmission label."]},
    "isuzu_amigo_1998_char7": {"verdict": "verified (WMI narrowed to 4S2)", "changes": [
        "WMI narrowed from 4S2/JAC to 4S2: the 1998 Amigo was built by SIA; no JAC Amigo VIN exists on the lots or in the cache."],
        "checks": [
        "Re-read 01-22-N11B-6340 (MY1998): position 5 K = Rodeo or Amigo 4x2, M = Rodeo or Amigo 4x4 (JAC, 4S2); position 7: 5 = Utility 2-door LWB, 7 = Utility 2-door SWB, 8 = Utility 4-door; engines D = X22SE 2.2, W = 6VD1 3.2, X = 6VE1 3.5.",
        "Manual-only for every 1998 Amigo: EPA 1998 Amigo rows (2WD 2.2, 4WD 2.2, 4WD 3.2) are all Manual 5-spd; Wikipedia Isuzu MU ('originally only available ... with a five-speed transmission'; automatic optional from 1999); Star-Telegram/Cars.com and Drive Chicago 1998 reviews (five-speed the sole transmission, automatic from the 1999 models).",
        "Scope edge: 1998 Rodeo (body 8) is excluded; EPA 1999 Amigo gains automatics, and the rule stops at MY1998.",
        "Counterexample search: no in-scope VIN has a transmission label."]},
    "isuzu_4zd1_23_4x2_1988_1995_char8": {"verdict": "candidate kept uncounted", "checks": [
        "EPA re-checked: Pickup 2WD 2.3 is Manual 5-spd only 1988-1995 (1986-1987 had a 3-speed automatic, outside the years); Amigo 2WD 2.3 manual only 1989-1993."]},
    "isuzu_4ze1_26_4x4_pickup_amigo_1989_1995_char8": {"verdict": "candidate kept uncounted", "checks": [
        "EPA re-checked: Pickup 4WD 2.6 Manual 5-spd only 1989-1995 (1988 had an automatic, outside the years)."]},
    "isuzu_trooper_23_1986_1987_char8": {"verdict": "candidate kept uncounted", "checks": [
        "EPA re-checked: Trooper 2.3 1986-1987 Manual 5-spd only."]},
    "suzuki_samurai_1986_1995_char4_5": {"verdict": "candidate kept uncounted", "checks": [
        "EPA re-checked: every Samurai row 1986-1995 is Manual 5-spd."]},
}

VERIFICATION = {
    "on": VERIFIED_ON,
    "kind": "adversarial re-check by a second session (task: refute rules)",
    "method": [
        "Re-downloaded the cited MID filings from vpic.nhtsa.dot.gov/mid/home/displayfile/<guid> into a fresh directory and read the VIN tables (page images for scanned files, text layer otherwise). Each rule's verified.checks names the filings re-read; a few early Subaru scans (MY1986, 1989, 1991, 1997, 1999, 2009 Forester, 2012, 2014) were not re-read and rest on the first session's reading plus vPIC agreement.",
        "Re-read Wikipedia (raw wikitext: Mazda RX-8, Mazdaspeed3, Mazda6, Mazda Familia, Isuzu MU) for every quoted sentence; ran web searches for second text sources (RX-8 2004 launch, MAZDASPEED Protege, 1998 Amigo, Solterra WMI).",
        "Re-checked every EPA row id quoted against scraper/manual_detect/epa/vehicles.csv, and listed all EPA rows for each scope to look for an automatic in a manual-only cell.",
        "Counterexample search: (a) ground_truth.jsonl and published lot labels (built in, see validation); (b) the whole vPIC decode cache, lots and history (rule verified.vpic_cache_scan); (c) for Subaru, vPIC trims that are automatic-only or manual-only against character 11; (d) vPIC decodes of pattern VINs at scope edges (2012-2013 Mazdaspeed3, 2004/2005 RX-8, unfiled Mazdaspeed6 GG14L, 2001-2002 BJ227, 1991 Stealth, 1991-1998 Isuzu Rodeo/Amigo).",
        "Scope edges checked: model-year boundaries against the years each filing defines a code; WMI/plant (Solterra JTM, SIA-built Isuzu/Honda/Toyota, JAC vs 4S2); body/line codes shared with automatic models (Amigo vs Rodeo, Mazda5/CX-7 'L', 2001 BJ227); Canada-market cars (Mazdaspeed3, RX-8 are the same as US)."],
    "outcome": {
        "rules_refuted_and_removed": 0,
        "rules_narrowed": [
            "subaru_fhi_G_H_1995_2026_char11 -> subaru_fhi_G_H_1995_2025_char11 (MY2026 removed: no MY2026 filing read)",
            "subaru_fhi_main_plant_2014_2026_char11 -> subaru_fhi_main_plant_2014_2025_char11 (same)",
            "subaru_sia_2010_2026_char11 -> subaru_sia_2010_2025_char11 (same)",
            "mazda_mazdaspeed6_2006_2007_char8_L3T: fixed characters 6-7 = '12' (JM1GG12L, the only filed code)",
            "isuzu_rodeo_26_4x2_1991_1997_char8 split into isuzu_rodeo_26_4x2_lineG_1991_1995_char8 and isuzu_rodeo_26_4x2_lineK_1995_1997_char8 (each line code ruled only in the years its filings define it); WMI 4S2 only",
            "isuzu_amigo_1998_char7: WMI 4S2 only"],
        "lot_cars_affected_by_narrowing": "none on the 2026-11-05 lots (no MY2026 Subaru, no GG14L, no JAC Rodeo/Amigo, no off-year G/K Rodeo)",
        "counts_note": "newly_confirmed_manual is recomputed from the current docs/data inventory, which has changed since the first session's run (cars sold, cars added), so the totals differ from the first run for that reason, not because of the narrowing."},
    "not_reachable": "WebFetch could not resolve www2020.theautochannel.com or www.conceptcarz.com (outside this session's allowed network hosts); those pages were not read. Wikipedia was read as raw wikitext with curl through the proxy.",
    "residual_risks": [
        "Subaru agreement with ground truth is partly circular (vPIC is built from the same filings); no VIN-bearing lot car has a non-vPIC transmission label.",
        "Engine-code rules (Mazda, Mitsubishi, Isuzu) depend on EPA + text sources for 'sold only with a manual'; the filings name engines, not transmissions.",
        "mazda_rx8_2009_2011: the High Power = manual mapping is inferred (0 lot cars affected)."],
}

VPIC_ONLY_YEARS = {
    "mitsubishi_3000gt_stealth_twin_turbo_1991_1992_char8": "MY1991 code from vPIC only (the 1991 passenger-car filing was not found; 01-22-N11B-3997 is the 1991 Fuso truck filing)",
    "mazda_rx8_2009_2011_char8_engine_power": "MY2010 codes from vPIC (the MY2009 and MY2011 filings define the same four codes, FE17x in 2009 and FE1Cx in 2011)",
    "mazda_mazdaspeed3_2010_2013_char8_L3T": "MY2012-2013 codes from vPIC (MY2010 and MY2011 filings read)",
    "isuzu_rodeo_26_4x2_lineG_1991_1995_char8": "MY1991, 1993, 1994 codes interpolated between the MY1992 and MY1995 filings (vPIC decodes 1991 and 1993 4S2CG58E as Rodeo 4ZE1 2.6 4x2)",
    "isuzu_rodeo_26_4x2_lineK_1995_1997_char8": "MY1996 codes interpolated between the MY1995 and MY1997 filings (vPIC decodes 1996 4S2CK58E as Rodeo 4ZE1 2.6 4x2)",
    "subaru_fhi_G_H_1995_2025_char11": "Years between filings read (e.g. 1995, 2005, 2007-2008, 2010-2011, 2013, 2015-2016, 2019-2021, 2023-2024) are interpolated: G = manual / H = automatic in every Gunma table read from MY1990 to MY2025",
}

ANSWER = {
    "Subaru": "ENCODED. VIN character 11 is 'plant of manufacture and transmission type' in every Subaru filing read, MY1985-1986, 1989, 1990, 1991, 1994, 1996, 1997, 1999, 2001-2004, 2006, 2009, 2012-2014, 2017, 2018, 2022, 2025. Gunma (JF1/JF2): G = AWD manual, H = AWD automatic/CVT, L = AWD 6MT (2006-2014), 9 = Main Plant manual / 8 = Main Plant CVT or 6AT (2014+); SIA Lafayette (4S3/4S4): 6 = AWD 5MT and 7 = AWD 4AT (1990-2009), 4 = 5AT (2005-2014), 1 = 6MT/5MT, 3 = CVT (2010+). The same character covers the Subaru-built Scion FR-S / Toyota 86 / GR86 (JF1 ZN/ZD). Not ruled: MY1987-1988 (no filing found), MY2013 Gunma codes 1/2 on Impreza / XV Crosstrek (no filing read; vPIC applies the BRZ meanings 6MT/6AT to them).",
    "Mazda": "NOT ENCODED in any filing read (MY1990, 1995, 2003, 2004, 2006, 2007, 2008, 2009, 2010 Mazda3, 2011, 2021). Characters 4-8 are line, series, body, engine type, restraint; the filings give engine type and horsepower but no transmission column. The first Mazda filing read that names a transmission is the MY2024 CX-90 (character 7), an automatic-only model. Ford-built Mazdas (B-Series 4F4, Tribute 4F2) are coded by Ford, also without transmission. Where Mazda's engine code is an engine sold only with a manual in the US, the engine code decides: MAZDASPEED3 L3T (2007-2013), MAZDASPEED6 L3T (2006-2007), MAZDASPEED Protege FSD 170 hp (2003), RX-8 13B High Power (2004 and 2009-2011; 2005 is a candidate; 2006-2008 is not, because the 6AT also used the High Power code).",
    "Mitsubishi": "NOT ENCODED in any filing read (MY1992, 1993, 1995, 1998, 2003, 2018). Character 8 is the engine; the only manual-only engine code ruled is the 3.0 twin-turbo (MY1991-1992 C, MY1993-1999 K) of the 3000GT VR-4 / Spyder VR-4 / Dodge Stealth R/T Turbo. Montero Sport 2.4 4x2 (1997-1999) is an EPA-only candidate. Lancer Evolution VIII/IX (2003-2006) were manual-only but no lot car without transmission info carries an Evolution code, so no rule was built.",
    "Suzuki": "NOT ENCODED in any filing read (MY2003, MY2009). The Samurai (1986-1995) is an EPA-only candidate model rule; nothing else. GM-built Suzukis (Forenza / Reno / Verona KL5, XL7 2007-2009 2S3) and the Nissan-built Equator (5Z6) follow GM / Nissan schemes, also without transmission.",
    "Isuzu": "NOT ENCODED in any filing read (MY1992, 1995, 1997, 1998, 2002). Character 5 is line + chassis (4x2 / 4x4), 7 body, 8 engine. Ruled where engine + line identify a configuration sold only with a manual: Rodeo 2.6 4x2 (1991-1997) and the 1998 Amigo (every engine). EPA-only candidates: Pickup/Amigo 2.3 4x2 (1988-1995), Pickup/Amigo 2.6 4x4 (1989-1995), Trooper 2.3 (1986-1987). GM-built Isuzus (Hombre 1GG, i-Series 1GG, Ascender 4NU) follow GM's scheme without transmission.",
}

VIN_SCHEME = {
    "Subaru": {"position": 11, "name": "Plant of manufacture and transmission type",
               "tables": "see each subaru_* rule's vin_condition; per-filing quotes in citations"},
    "Mazda": {"positions": {"4": "line", "5": "series", "6": "body type", "7": "engine type (pre-2021 the 4-8 group is read as one VDS code)", "8": "restraint / engine (varies by era; filings list whole VDS codes)", "11": "plant"},
              "transmission": "none (MY2024 CX-90 first names one, automatic only)"},
    "Mitsubishi": {"positions": {"4": "restraint / GVWR", "5": "car line", "6": "series (price class)", "7": "body type", "8": "engine type", "11": "plant"},
                   "transmission": "none"},
    "Suzuki": {"positions": {"4": "line", "5": "series / chassis / restraint", "6": "engine type", "7": "design sequence", "8": "body type / grade", "11": "plant"},
               "transmission": "none"},
    "Isuzu": {"positions": {"4": "GVWR / brake", "5": "line, chassis (4x2/4x4) and restraint", "6": "series", "7": "body type", "8": "engine", "11": "plant"},
              "transmission": "none"},
}

NOT_RULED = [
    {"make": "Subaru", "scope": "MY1987-1988 Gunma", "why": "no filing found in MID for these years; the 1985-86 and 1989 tables agree, but the codes are not interpolated across a gap with no document"},
    {"make": "Subaru", "scope": "MY1989 code E ('4WD, Dual-range')", "why": "the 1989 table does not say whether E is manual"},
    {"make": "Subaru", "scope": "MY2013 Gunma Impreza / XV Crosstrek codes 1 and 2", "why": "no MY2013 Impreza filing read; vPIC decodes them with the BRZ meanings (1 = 6MT, 2 = 6AT) although the Impreza had a 5MT or CVT. Every lot car with these codes already has a vPIC transmission"},
    {"make": "Subaru", "scope": "SIA codes outside the tables (e.g. 2006 U), FHI L before 2006, SIA 1/9 after 1996", "why": "not defined by a filing read; the rules make no claim for codes outside their tables"},
    {"make": "Subaru", "scope": "4S1/4S2/4S6 (Isuzu- and Honda-badged SIA builds), 4T1 (SIA-built Toyota Camry)", "why": "those VINs follow Isuzu's or Toyota's scheme, not Subaru's"},
    {"make": "Subaru", "scope": "MY2026 (every plant)", "why": "the latest Subaru filing read is MY2025 (ORG23706); the 2026-11-05 verification capped the Gunma G/H, Main Plant 9/8 and SIA 2010+ rules at MY2025 instead of carrying the code tables into a year with no document"},
    {"make": "Subaru", "scope": "SIA code 5 ('AWD 4AT-SS') in MY2003-2005", "why": "the MY2003 table lists SIA 5 = AWD 4AT-SS, but the rule claims 5 only for MY2006 (the table it was read from). These are automatics, so leaving them out costs no manual claim"},
    {"make": "Mazda", "scope": "every Mazda except the engine codes ruled", "why": "Mazda's VIN has no transmission character; the engines are offered with both transmissions"},
    {"make": "Mazda", "scope": "RX-8 MY2006-2008 (JM1FE173)", "why": "the MY2008 filing lists FE173 13B High Power as '232HP (MT) / 212HP (AT)': both transmissions"},
    {"make": "Mazda", "scope": "Mazdaspeed MX-5 (2004-2005), 323 GTX (1988-89), RX-7 Turbo II (1987-88), 626 turbo", "why": "manual-only engines, but no lot car without transmission info carries them (MX-5 NB353 on the lots is the 142 hp base engine); not researched further"},
    {"make": "Mazda", "scope": "Tribute 2.0 (2001-2004, Ford Zetec, EPA manual only)", "why": "Ford-built (4F2) and no 2.0 Tribute on the lots lacks transmission info"},
    {"make": "Mitsubishi", "scope": "every Mitsubishi except the 3000GT/Stealth twin turbo", "why": "no transmission character; engines are offered with both"},
    {"make": "Mitsubishi", "scope": "Lancer Evolution VIII/IX 2003-2006, Galant VR-4 1991-92, 1990 Eclipse/Talon turbo", "why": "manual-only per EPA, but none of the lot cars without transmission info carries these codes (or only 1-2 cars), so no filing was read for them"},
    {"make": "Mitsubishi", "scope": "Lancer Evolution X (2008-2015)", "why": "GSR was 5MT, MR was the TC-SST dual clutch; the engine code is shared with the TC-SST-only Lancer Ralliart"},
    {"make": "Suzuki", "scope": "every Suzuki except the Samurai candidate", "why": "no transmission character; Sidekick 1.3 4WD (1989) and X-90 2WD (1996) are EPA manual-only cells with no matching lot cars"},
    {"make": "Isuzu", "scope": "Rodeo 2.6 line G after MY1995 and line K before MY1995; JAC-WMI Rodeo/Amigo codes", "why": "line G is not in the MY1997 table and line K is not in the MY1992 table, so each is ruled only in the years its tables define it; the US Rodeo and 1998 Amigo were built by SIA (4S2), so JAC is not ruled"},
    {"make": "Isuzu", "scope": "Hombre (1996-2000), i-Series, Ascender", "why": "GM-built (1GG / 4NU), GM scheme. EPA lists only a manual for the 1996-1997 Hombre 2.2 4x2, but GM's 2.2 engine code is shared with the S-10, which had an automatic"},
    {"make": "Isuzu", "scope": "Rodeo 2.2 4x2 (1998-2000), Amigo 2.2 4x2 (1999-2000)", "why": "EPA lists only a manual, but no lot car without transmission info falls there (the 2.2 Rodeos on the lots are 2001-2002, when EPA lists an automatic)"},
]

VALIDATION_METHOD = (
    "Every lot car with a WMI used by a rule, a 17-character VIN and a valid check digit is classified. The model year comes from "
    "VIN character 10 (the listing year only picks the 30-year cycle and must be within 2 years). A rule fires only when the VIN "
    "matches its WMI, years and fixed characters and the code is in its table for that year; other codes get no claim. "
    "Ground truth = scraper/manual_detect/ground_truth.jsonl. Lines with uniformCell set are treated as unlabelled (counted "
    "separately as uniform_cell_lines_excluded / _that_would_agree), speeds-only lines are excluded, and the rest are checkable: "
    "agree means (truth is manual) == (rule says manual). Note that every VIN-bearing truth line comes from vPIC, which NHTSA builds "
    "from the same Part 565 filings, so agreement is partly circular. The EPA cross-check (year/make/model union, vPIC displacement "
    "when known) is the independent check: a manual claim is consistent when EPA lists a manual for the car, an automatic claim when "
    "EPA lists a non-manual. Status: candidate (not counted) when the evidence is short of the bar; drop when >= 20 checkable and "
    "agreement < 0.995; low_sample when < 20 checkable (kept: the code meaning comes from the manufacturer's own VIN scheme); "
    "keep otherwise. newly_confirmed_manual counts lot cars with no published transmission (vehicle_extras trans empty) that a "
    "keep or low_sample rule calls manual."
)


def rule_regex(r: dict) -> str:
    """Regex for the rule's MANUAL codes: WMI, fixed characters, code character and year code."""
    chars = ["."] * 17
    for p, allowed in r["fixed"].items():
        chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
    man = "".join(c for c, v in r["codes"].items() if v[0] == M)
    if not man:
        return ""
    chars[r["pos"] - 1] = "[" + man + "]" if len(man) > 1 else man
    ys = year_chars(*r["years"])
    chars[9] = "[" + ys + "]" if len(ys) > 1 else ys
    body = "".join(chars[3:])
    return "^(" + "|".join(r["wmi"]) + ")" + body


def classify(vin: str, year: int) -> tuple[dict, str, str, str] | None | str:
    """-> (rule, claim, code, meaning); 'unknown_code' when a rule's scope
    matches but the code is outside its table/years; None when out of scope."""
    scoped = None
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        scoped = r
        code = vin[r["pos"] - 1]
        hit = r["codes"].get(code)
        if hit and hit[2][0] <= year <= hit[2][1]:
            return (r, hit[0], code, hit[1])
    return ("unknown_code", scoped) if scoped else None


# ---------------------------------------------------------------------------
# EPA cross-check (independent of vPIC)
# ---------------------------------------------------------------------------
EPA_MAKES = {"Subaru", "Mazda", "Mitsubishi", "Dodge", "Scion", "Toyota", "Suzuki", "Isuzu"}
EXTRA_ALIAS = {"mazdaspeed6": ["6"], "mazdaspeed3": ["speed3", "3"], "mazdaspeedprotege": ["protege"],
               "3000gtvr4": ["3000gt"], "frs": ["frs"], "imprezaoutback": ["impreza"]}


class Epa:
    def __init__(self, path: Path):
        self.ok = path.exists()
        self.idx: dict[tuple[int, str, str], set[int]] = defaultdict(set)
        self.rows: list[dict] = []
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
                i = len(self.rows)
                self.rows.append(r)
                for _lv, k in ep.epa_keys(r):
                    self.idx[(y, r["make"], k)].add(i)

    def classes(self, year: int, make: str, models: list[str], displ: float | None) -> set[str] | None:
        hits: set[int] = set()
        for m in models:
            if not m:
                continue
            keys = [k for _lv, k in ep.feed_keys(make, m)]
            keys += EXTRA_ALIAS.get(ep.norm(m), [])
            for k in keys:
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
    FIVE = ("Subaru", "Mazda", "Mitsubishi", "Suzuki", "Isuzu")

    per_rule = {r["id"]: defaultdict(Counter) for r in RULES}
    examples = {r["id"]: defaultdict(list) for r in RULES}
    codes_seen = {r["id"]: Counter() for r in RULES}
    unknown_codes = defaultdict(Counter)
    scan = Counter()
    make_cov = {m: Counter() for m in FIVE}
    newly_manual, newly_auto, vpic_conflicts = [], [], []

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
        if make in FIVE:
            mc = make_cov[make]
            mc["cars"] += 1
            mc["no_trans_info"] += 0 if pub else 1
            mc["vin17"] += 1 if len(vin) == 17 else 0
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
        codes_seen[rid][f"char{r['pos']}={code}"] += 1
        if make in FIVE:
            make_cov[make]["covered_by_rule"] += 1
        g = gt.get(vid)
        raw = cache.get(vin)
        dec = raw if isinstance(raw, dict) else None
        displ = parse_displ((dec or {}).get("engine", "") or ex[2])
        # ---- validation against ground truth ----
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
                    examples[rid]["disagree"].append({"id": vid, "vin": vin, "year": y, "model": model,
                                                      "code": code, "claim": claim, "ground_truth": g.get("trans"),
                                                      "source": g.get("source")})
            else:
                st[claim]["speeds_only_excluded"] += 1
        # ---- EPA cross-check ----
        if epa.ok:
            emake = make if make in EPA_MAKES else r["make"]
            cls = epa.classes(y, emake, [model, (dec or {}).get("model", "")], displ)
            if cls is None:
                st[claim]["epa_no_match"] += 1
            elif (claim == M and "manual" in cls) or (claim == A and (cls - {"manual", "unknown", "other"})):
                st[claim]["epa_consistent"] += 1
            else:
                st[claim]["epa_conflict"] += 1
                if len(examples[rid]["epa_conflict"]) < 10:
                    examples[rid]["epa_conflict"].append({"vin": vin, "year": y, "make": make, "model": model,
                                                          "claim": claim, "epa_classes": sorted(cls)})
        # ---- published label vs rule (vPIC conflicts) ----
        if pub and pcls in KNOWN and (pcls == "manual") != (claim == M):
            vpic_conflicts.append({"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                                   "code": f"char{r['pos']}={code}: {meaning}", "rule_claim": claim,
                                   "published_trans": pub, "transSrc": ex[4] or "vin",
                                   "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        # ---- cars without transmission info ----
        if not pub:
            why = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if "transmission" in dec else "cache_old_schema")
            st[claim]["no_trans_info"] += 1
            st[claim][f"no_trans_info_{why}"] += 1
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"char{r['pos']}={code}: {meaning}", "why_no_trans": why, "yard": yard}
            if claim == M:
                newly_manual.append(rec)
            else:
                newly_auto.append(rec)

    # ---- counterexample scan over the whole vPIC cache (lots + history) ----
    cache_scan: dict[str, dict] = {}
    cs_counts = defaultdict(Counter)
    cs_examples = defaultdict(list)
    for cvin, payload in cache.items():
        if not isinstance(payload, dict) or len(cvin) != 17 or cvin[:3] not in all_wmi or not check_digit_ok(cvin):
            continue
        try:
            hint = int(payload.get("modelYear") or 0) or None
        except ValueError:
            hint = None
        cy = vin_year(cvin, hint)
        if cy is None:
            continue
        cres = classify(cvin, cy)
        if cres is None or cres[0] == "unknown_code":
            continue
        cr, cclaim, ccode, _m = cres
        cc = cs_counts[cr["id"]]
        cc["in_scope_vins"] += 1
        ccls = tclass(payload.get("transmission", ""))
        if ccls not in KNOWN:
            cc["no_vpic_transmission"] += 1
            continue
        cc["with_vpic_transmission"] += 1
        if (ccls == "manual") == (cclaim == M):
            cc["agree"] += 1
        else:
            cc["disagree"] += 1
            if len(cs_examples[cr["id"]]) < 10:
                cs_examples[cr["id"]].append({"vin": cvin, "year": cy, "code": ccode, "claim": cclaim,
                                              "vpic_transmission": payload.get("transmission", "")})
    for r in RULES:
        cc = cs_counts[r["id"]]
        cache_scan[r["id"]] = {"in_scope_vins": cc["in_scope_vins"], "with_vpic_transmission": cc["with_vpic_transmission"],
                               "agree": cc["agree"], "disagree": cc["disagree"],
                               "no_vpic_transmission": cc["no_vpic_transmission"],
                               "disagree_examples": cs_examples[r["id"]]}

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
        if r.get("candidate"):
            status = "candidate"
        elif chk >= MIN_SAMPLE and agreement is not None and agreement < MIN_AGREEMENT:
            status = "drop"
        elif chk < MIN_SAMPLE:
            status = "low_sample"       # kept: the citation is the manufacturer's own VIN scheme
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
                    "epa_crosscheck": {"consistent": s["epa_consistent"], "conflict": s["epa_conflict"],
                                       "no_epa_match": s["epa_no_match"]},
                    "cars_without_trans_info": s["no_trans_info"],
                    "cars_without_trans_info_by_reason": {k[len("no_trans_info_"):]: v for k, v in s.items()
                                                          if k.startswith("no_trans_info_")}}
        man_codes = {c: v[1] + f" (MY{v[2][0]}-{v[2][1]})" for c, v in r["codes"].items() if v[0] == M}
        aut_codes = {c: v[1] + f" (MY{v[2][0]}-{v[2][1]})" for c, v in r["codes"].items() if v[0] == A}
        basis = "transmission_code"
        for pre, b in RULE_BASIS.items():
            if rid.startswith(pre):
                basis = b
        out_rules.append({
            "id": rid,
            "make": r["make"],
            "status": status,
            "basis": basis,
            "status_reason": ({"candidate": "not counted: the evidence does not meet the bar (see scope.models and notes)",
                               "low_sample": f"fewer than {MIN_SAMPLE} checkable ground-truth cars; kept because the VIN code meaning comes from the manufacturer's own Part 565 VIN scheme",
                               "keep": f">= {MIN_SAMPLE} checkable cars and agreement >= {MIN_AGREEMENT}",
                               "drop": f"agreement below {MIN_AGREEMENT}"}[status]),
            "notes": RULE_NOTES.get(rid, ""),
            "claim": "manual for the manual codes; automatic (not manual) for the automatic codes" if aut_codes else "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + (", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())) or "none")]},
            "vin_condition": {"position": r["pos"], "manual_codes": man_codes, "automatic_codes": aut_codes},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"]] + ([{"url": C["epa"]["url"], "doc": C["epa"]["doc"],
                                                          "says": "; ".join(r["epa_ids"])}] if r["epa_ids"] else []),
            "evidence_gaps": VPIC_ONLY_YEARS.get(rid, ""),
            "validation": {
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": st[M]["checkable_gt_manual"] + st[A]["checkable_gt_manual"],
                "manual_codes": side(M), "automatic_codes": side(A),
                "disagree_examples": examples[rid]["disagree"],
                "epa_conflict_examples": examples[rid]["epa_conflict"],
                "codes_seen_on_lots": dict(codes_seen[rid].most_common()),
                "in_scope_codes_not_in_table": dict(unknown_codes[rid].most_common()),
            },
            "newly_confirmed_manual": st[M]["no_trans_info"],
            "newly_labelled_non_manual": st[A]["no_trans_info"],
            "verified": {"on": VERIFIED_ON, **VERIFIED.get(rid, {"verdict": "not verified"}),
                         "vpic_cache_scan": cache_scan.get(rid, {})},
        })

    keep_ids = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    nm_conf = [c for c in newly_manual if c["rule"] in keep_ids]
    nm_cand = [c for c in newly_manual if c["rule"] not in keep_ids]
    for mk in FIVE:
        make_cov[mk]["newly_confirmed_manual_counted"] = sum(1 for c in nm_conf if c["make"] == mk)
        make_cov[mk]["newly_confirmed_manual_candidate_rules_only"] = sum(1 for c in nm_cand if c["make"] == mk)
        make_cov[mk]["newly_labelled_non_manual_counted"] = sum(1 for c in newly_auto if c["make"] == mk and c["rule"] in keep_ids)
    man_chk = sum(x["validation"]["manual_codes"]["checkable_ground_truth"] for x in out_rules if x["id"] in keep_ids)
    man_agr = sum(x["validation"]["manual_codes"]["agree"] for x in out_rules if x["id"] in keep_ids)
    aut_chk = sum(x["validation"]["automatic_codes"]["checkable_ground_truth"] for x in out_rules if x["id"] in keep_ids)
    aut_agr = sum(x["validation"]["automatic_codes"]["agree"] for x in out_rules if x["id"] in keep_ids)

    doc = {
        "worklist": "vin_rules_1",
        "makes": list(FIVE),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/vin_rules_1.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json", "vehicle_extras": "docs/data/vehicle_extras.json",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (uniformCell lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA cross-check skipped)"),
                   "mid_filings_read": "NHTSA MID Part 565 files listed in each rule's citations and in vin_scheme; downloaded 2026-11-05 from vpic.nhtsa.dot.gov/mid (search API + displayfile)"},
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
            "published_labels_contradicting_a_rule": len(vpic_conflicts),
            "scan": dict(scan),
            "five_make_coverage": {m: dict(v) for m, v in make_cov.items()},
        },
        "validation_method": VALIDATION_METHOD,
        "verification": VERIFICATION,
        "rules": out_rules,
        "newly_confirmed_manual_cars": nm_conf,
        "candidate_rule_manual_cars": nm_cand,
        "vpic_conflicts": vpic_conflicts,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("manual-claim precision:", s["ground_truth_precision_manual_claims"], " auto-claim agreement:", s["ground_truth_agreement_automatic_claims"])
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"])
    print("scan:", s["scan"])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
