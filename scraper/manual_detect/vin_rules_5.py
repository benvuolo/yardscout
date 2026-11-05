#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 5: Chevrolet, GMC, Pontiac,
Saturn, Buick, Cadillac, Oldsmobile, Hummer (General Motors), plus Geo/CAMI
Metro, which no other worklist covers.

What GM's own Part 565 VIN filings (NHTSA Manufacturer Information Database,
MID, filer "General Motors"; NUMMI for the Pontiac Vibe 2003-2004) say. The
filings were downloaded 2026-11-05 (MID search API + displayfile): 243 GM,
NUMMI, GM Daewoo, AM General and CAMI files, MY1984-MY2027. Text layers were
searched; scanned ones were OCR'd and the tables cited here were read as page
images.

  * GM has no dedicated transmission position. But for many car lines the
    LINE/SERIES code (positions 4-5 on cars, 5-6 on trucks/MPVs) is defined
    per transmission: the filing's description reads "Cobalt LS (Manual)",
    "HHR LS w/ manual trans", "SL1 AUTO", "Vue FWD Manual" ... Those codes
    are the rules here. Every rule is bound to the model years whose LATEST
    filing names the transmission, because GM reuses letters with different
    meanings from year to year (2008 Solstice MG = turbo AUTO, 2009 MG =
    turbo M/T; 2011 Cruze PF = 1LT automatic, the Dec-2009 draft said manual)
    and sometimes drops the split in a later revision (MY2008 Cobalt/G5).
  * Years and lines whose filings name no transmission are NOT encoded and get
    no series rule (see ANSWER / NOT_RULED).
  * For a few manual-only engines/sub-models in years without a coded series
    (CTS-V 2004-07, Cobalt SS supercharged 2005-07, Ion Red Line 2004-07,
    Vibe GT 2003-06, Metro 1.0 1999-2000) the code's meaning comes from the
    filing and the transmission fact from EPA (fueleconomy.gov vehicles.csv,
    independent of vPIC): EPA must list only a manual for every rule year.

Every rule is validated against ground_truth.jsonl (uniformCell lines are
unlabelled), cross-checked per car against EPA, and counted for the lot cars
WITHOUT transmission info it would newly confirm as manual. Published labels
that contradict a rule are listed (published_label_conflicts).

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (optional, EPA cross-check).
Output: scraper/manual_detect/vin_rules_5.json

Run:  python3 -I scraper/manual_detect/vin_rules_5.py
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

OUT = HERE / "vin_rules_5.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
MAKES = ("Chevrolet", "GMC", "Pontiac", "Saturn", "Buick", "Cadillac", "Oldsmobile", "Hummer", "Geo")
M, A = "manual", "automatic"
BY6 = "by_position_6"

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


def yrs(lo, hi):
    return list(range(lo, hi + 1))


# ---------------------------------------------------------------------------
# Citations (MID files downloaded 2026-11-05; "page image" = scanned table read
# as a rendered image)
# ---------------------------------------------------------------------------
def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


C = {
    # --- Saturn S/L (1G8, lines Z and J) -----------------------------------
    "s1991": mid("7bc7743c-c997-456d-bcef-10eeeadb9e0f", "NHTSA 01-22-N11B-3797, General Motors 1990-08-28, MY1991 VIN standard, Table B2g Saturn (page image / OCR)",
                 "Carline Z series: B = SC (2 door) / SL1 (4 door), D = SL2, F = SL1, G = SC / SL1, H = SC / SL1, J = SL2, K = SL2. No transmission is named."),
    "s1993": mid("c6c1667c-f57e-42df-a14d-4d4ce7e74190", "NHTSA 01-22-N11B-4795, General Motors 1992-07-10, MY1993 VIN standard, Table B2g Saturn (OCR)",
                 "Z F = SL, Z G = SC (2 door) / SL1 (4 door), Z H = SC (2 door) / SL1 (4 door), Z J = SL2, Z K = SL2. G and H (and J and K) carry identical descriptions: no transmission is named."),
    "s1996": mid("c2e7c850-1193-4b15-810f-30194636094a", "NHTSA 01-22-N11B-5967, General Motors 1995-08-03, MY1996 VIN standard, Table B2g Saturn (OCR)",
                 "Saturn series descriptions are SC1 coupe, SC2 coupe, SL or SL1 sedan, SW1/SW2 wagon, SL2 sedan; no transmission is named."),
    "s1999": mid("0671200a-c907-4a74-af74-960131a92f33", "NHTSA 01-22-N11B-6619, General Motors 1998-01-15, MY1999 VIN standard, Table B2g Saturn (OCR)",
                 "Z E = SC1 coupe, Z F = SC1 coupe, Z G = SC2 coupe / SW1 wagon / SL1 sedan, Z H = SC2 coupe / SW1 wagon / SL1 sedan, Z J = SW2 wagon / SL2 sedan, Z K = SW2 wagon / SL2 sedan; no transmission is named."),
    "s2000": mid("d4f44ce1-7f9e-4f82-9269-66875c1c0cda", "NHTSA 01-022-N11B-7868, General Motors 2000-07-28, 'Vehicle Identification Number decoding for 2000 Model Year', Table B2g Saturn (VIN positions 4 and 5), text layer",
                 "Z F SL MANUAL; Z G SL1 MANUAL; Z H SL1 AUTO; Z J SW2 MANUAL, SL2 MANUAL; Z K SL2 AUTO; Z M SW1 AUTO RHD; Z N SC1 MANUAL, SW2 AUTO; Z P SC1 AUTO; Z R SC2 MANUAL; Z Y SC2 AUTO; J R LS MANUAL; J S LS AUTO; J T LS1 MANUAL; J U LS1 AUTO, LW1; J W LS2, LW2."),
    "s2000a": mid("b1e3c9f9-70c4-417c-ba54-1fd3570b8b0d", "NHTSA 01-22-N11B-7504, General Motors 1999-12-02, MY2000 VIN standard update (cover letter + Table B2g), text layer",
                  "Cover letter: 'Section B, page B8 - Carline, Series \"ZK\" changed to SL2 Auto.' Table B2g: Z F SL MANUAL, Z G SL1 MANUAL, Z H SL1 AUTO, Z K SL2 AUTO, Z R SC2 MANUAL, J R LS MANUAL ..."),
    "s2001": mid("8bf5edfb-dcc0-403a-9c8c-9c2c0211bdd3", "NHTSA 01-22-N11B-7505, General Motors 1999-12-02, MY2001 VIN standard (November 1999), Table B2g Saturn, page B8 (page image)",
                 "Z F SL; Z G SL1 MANUAL; Z H SL1 AUTO; Z J SW2 MANUAL, SL2 MANUAL; Z K SL2 AUTO; Z M SW1; Z N SC1 MANUAL, SW2 AUTO; Z P SC1 AUTO; Z R SC2 MANUAL; Z Y SC2 AUTO; J R LS MANUAL; J S LS AUTO; J T LS1 MANUAL; J U LS1 AUTO, LW1; J W LS2, LW2. (ZF 'SL' names no transmission in MY2001.)"),
    "s2002rev": mid("d8eee998-eac0-4a20-8d40-7c30fd46de36", "NHTSA 01-022-N11B-8753, General Motors 2001-07-18, MY2002 VIN standard revision, cover letter (text layer)",
                    "'Section B, page B8 ZJ revised to remove \"SW2 MANUAL,\" ZM deleted, ZN revised to remove \"SW2 AUTO\" reference'."),
    "s2002": mid("d4702437-5037-472d-aabf-9c013fb80fce", "NHTSA 01-022-N11B-9012, General Motors 2002-05-17, MY2002 VIN standard (latest MY2002 revision in MID), Table B2g Saturn, text layer",
                 "Z F SL Manual; Z G SL1 MANUAL; Z H SL1 AUTO; Z J SL2 MANUAL; Z K SL2 AUTO; Z N SC1 MANUAL; Z P SC1 AUTO; Z R SC2 MANUAL; Z Y SC2 AUTO; Z S SL MANUAL SPRING SPECIAL; J R LS MANUAL; J S LS AUTO; J T LS1/LW1 MANUAL; J U LS1/LW1 AUTO; J W LS2, LW2."),
    "s2002b": mid("2a903abd-2be2-4d94-9b48-b6a173a22c80", "NHTSA 01-022-N11B-8755, General Motors 2001-10-23, MY2002 VIN standard (October 2001), Table B2g page B7 and Table C3g page C7 (page images)",
                  "B2g: Z F SL; Z G SL1 MANUAL; Z H SL1 AUTO; Z J SL2 MANUAL; Z K SL2 AUTO; Z N SC1 MANUAL; Z P SC1 AUTO; Z R SC2 MANUAL; Z Y SC2 AUTO. C3g Saturn (VIN positions 5 and 6, WMI 5GZ): Z 2 FWD Manual; Z 3 FWD Auto; Z 4 AWD 4 Cyl; Z 6 AWD 6Cyl."),
    "s2003": mid("10ed3002-d0f7-4e86-b6b7-a3930e96bce5", "NHTSA 01-022-N11B-8695, General Motors 2002-07-29, MY2003 VIN standard, Table B2g Saturn and Table C3g, text layer",
                 "B2g: A F Level I Sedan Manual; A G Level I Sedan Auto; A J Level 2 Sedan Auto; A K Level 3 Sedan Manual; A L Level 3 Sedan Auto; A M Level 2 Coupe Manual; A N Level 2 Coupe Auto; A V Level 3 Coupe Manual; A W Level 3 Coupe Auto; A Z Level 2 Sedan Manual; J T L200/LW200 MANUAL; J U L200/LW200 AUTO; J W L300, LW300."),
    "s2003v": mid("a0b13a49-d7d0-4bd1-b876-b07508d561e4", "NHTSA 01-022-N11B-9063, General Motors 2002-06-17, MY2003 VIN standard, Table C3g Saturn, text layer",
                  "Z 2 FWD Manual; Z 3 FWD Auto; Z 4 AWD 4 Cyl."),
    "s2004": mid("3f316431-e3fb-4096-b2a9-656cb9f9a3b1", "NHTSA 01-022-N11B-9604, General Motors 2003-07-23, MY2004 VIN standard (June 2003), Table B2g Saturn page B8 (page image), Table B2f Cadillac page B7, engine table, Table C3g",
                 "B2g: A F ION Level I Sedan Manual; A G Level I Sedan Auto; A J Level 2 Sedan Auto; A K Level 3 Sedan Manual; A L Level 3 Sedan Auto; A M Level 2 Coupe Manual; A N Level 2 Coupe Auto; A V Level 3 Coupe Manual; A W Level 3 Coupe Auto; A Y ION Red Line Coupe; A Z ION Level 2 Sedan Manual. B2f: D M CTS; D N CTS-V; D R CTS Right Hand Drive. Engine: 'P 2.0L, L4 MFI, DOHC, SC, Alum, Lotus, LSJ, Saturn' (cover letter: 'Engines added: ... LSJ code P'). C3g: Z 2 FWD Manual; Z 3 FWD Auto; Z 4 AWD 4 Cyl."),
    "s2005": mid("3901d674-62de-4ace-9139-41dcda680ad1", "NHTSA 01-022-N11B-9926, General Motors 2004-03-10, MY2005 VIN standard (January 2004), Table B2g Saturn page B7 (page image), Table C3g (OCR)",
                 "A F ION - Sedan Level 1 - Man (RE9); A G ION - Sedan Level 1 - Auto (RF1); A H Level I - Base; A J Sedan Level 2 - Auto (RF3); A K Sedan Level 3 - Man (RF4); A L Sedan Level 3 - Auto (RF5); A M Coupe Level 2 - Man (RF6); A N Coupe Level 2 - Auto (RF7); A T ION - Coupe - Red Line; A U Level II - Base; A V Coupe Level 3 - Man (RF8); A W Coupe Level 3 - Auto (RF9); A X Level III - Base; A Y ION - Coupe Red Line Tuner (HMD); A Z ION Level 2 Sedan Man (RF2); B2f D N = CTS-V. C3g: Z 2 FWD Manual; Z 3 FWD Auto."),
    "s2005e": mid("8eff0f68-bb7c-44e8-b36d-8a3485e0191a", "NHTSA 01-022-N11B-9605, General Motors 2003-07-23, MY2005 initial VIN standard, text layer",
                  "Engine table: 'P 2.0L, L4 MFI, DOHC, SC, Alum, Lotus, LSJ, Saturn'; Table B2g lists 'ION Red Line'; C3g: Z 2 FWD Manual; Z 3 FWD Auto; Z 4 AWD 4 Cyl. Cover letter: 'Added - AJ, AS Cobalt'."),
    "s2006": mid("b6880d3f-c735-4df5-a511-29ab94161ef3", "NHTSA 01-022-N11B-11174, General Motors 2006-01-20, MY2006 VIN standard (December 2005), Table B2g Saturn page B7 (page image), engine table and C3g (OCR)",
                 "A J ION - Sedan Level 2 - Auto (RF3); A K Sedan Level 3 - Man (RF4); A L Sedan Level 3 - Auto (RF5); A M Coupe Level 2 - Man (RF6); A N Coupe Level 2 - Auto (RF7); A T Coupe - Red Line; A U Level II - Base; A V Coupe Level 3 - Man (RF8); A W Coupe Level 3 - Auto (RF9); A X Level III - Base; A Y Coupe Red Line Tuner (HMD); A Z ION Level 2 Sedan Man (RF2). Engine: 'LSJ P 2.0L, L4, MFI, DOHC, SC, Lotus, Saturn'. C3g: Vue FWD Manual (2), Vue FWD Auto (3), Vue AWD 4 Cyl (4). B2f: CTS-V."),
    "s2007": mid("0b85fd4d-c769-40f3-a708-0cd796dedd09", "NHTSA 01-022-N11B-11173, General Motors 2006-01-20, MY2007 VIN standard (December 2005), Table B2g Saturn page B7 and Table C3g page C8 (page images)",
                 "B2g: A J ION - Sedan Level 2 - Auto (RF3); A K Sedan Level 3 - Man (RF4); A L Sedan Level 3 - Auto (RF5); A M Coupe Level 2 - Man (RF6); A N Coupe Level 2 - Auto (RF7); A T ION - Coupe - Red Line; A U Level II - Base; A V Coupe Level 3 - Man (RF8); A W Coupe Level 3 - Auto (RF9); A X Level III - Base; A Y ION - Coupe Red Line Tuner (HMD); A Z ION Level 2 Sedan Man (RF2); M B Sky Convertible; M G Sky turbo convertible. C3g Saturn (WMI 5GZ): Z 2 Vue FWD Manual; Z 3 Vue FWD Auto; Z 4 Vue AWD 4 Cyl; Z 5 Vue FWD 6 CYL; Z 6 Vue AWD 6Cyl. Engine: 'LSJ P 2.0L, L4, MFI, DOHC, SC, Lotus'. B2f: D N CTS-V."),
    # --- MY2008 --------------------------------------------------------------
    "m2008a": mid("53f7d7cd-abe7-402a-ae9b-86576ec2862c", "NHTSA ORG3532, General Motors (filed 2007-09-05), MY2008 VIN standard, April 2007 issue, Tables B2a/B2c (pages B2, B4, page images)",
                  "SUPERSEDED for Cobalt/G5/Solstice by the May 2008 4th revision. Cobalt: A J Base w/ auto trans, A K 1LS w auto trans, A L 1LT w/ auto trans, A M 2LT w/ auto trans, A P 1SP w/ auto trans, A N base w/ manual trans, A R 1LS w/ manual trans, A T 1LT w/ manual trans, A W 2LT w/ manual trans, A U 1SP sport w/ manual trans, A S SS coupe. G5: A L base w/auto trans, A N GT w/manual trans, A R LS w/manual trans, A S GT w/ auto trans. Solstice: M B convertible w/ manual trans, M G GXP Turbo convertible w/ manual trans, M C convertible w/ auto trans, M F GXP Turbo convertible w/ auto trans. Vibe: S L (5Y2) Vibe FWD w/ auto trans."),
    "m2008": mid("a7f649b9-08dc-4b75-9c00-3b48ad3d2514", "NHTSA ORG21681, General Motors, 'GM Standards for Vehicle Identification Number (VIN) 2008 Model Year - 4th Revision', May 2008 (MID filing date 2023-05-02), text layer",
                 "B2a Chevrolet: A J Cobalt Base; A K Cobalt 1LS; A L Cobalt 1LT; A M Cobalt Sport; A P Cobalt SS (no transmission). B2c Pontiac: A J G5 base; A L G5 SE; A N G5 GT; M B SOLSTICE Convertible w/ manual trans; M G Solstice GXP Turbo Convertible w/ auto trans; M C Solstice convertible w/ auto trans.; M F Solstice GXP Turbo convertible w/ manual trans.; M K/S/T Special Editions; S L (5Y2) Vibe FWD w/ auto trans.; S P Vibe FWD w/ manual trans. B2f Cadillac: D M CTS manual trans, rear wheel drive; D F CTS, Auto trans, RWD; D G Auto trans, AWD; D H Auto trans, AWD & Navigation; D J Auto trans & Navigation RWD; D P CTS, Manual trans, RWD, High Feature V6; D R/S/T/V Auto trans (High Feature V6); D C/E/W/X/Y/A/B/K/D/L/Z = STS. B2g Saturn: M B Sky Convertible w/ manual trans.; M G Sky turbo convertible w/ auto trans.; M C Sky convertible w/ auto trans.; M F Sky Turbo convertible w/ Manual; M J Sky Special Edition Turbo. C3b Chevrolet (VIN positions 5 and 6): A 1 HHR LS w/ auto trans; A 2 HHR 1LT w/ auto trans; A 3 HHR LS w/ manual trans; A 4 HHR 1LT w/ manual trans; A 5 HHR 2LT; A 6 HHR SS w/ auto trans; A 7 HHR SS w/ manual trans; A 8 HHR LS panel van w/auto trans; A 9 HHR LS panel van w/ manual trans; A 0 HHR LT panel van."),
    # --- MY2009 --------------------------------------------------------------
    "m2009c": mid("9817a92a-f2bf-426d-a661-c62b78700d6f", "NHTSA ORG4756, General Motors, '2009 Passenger Car VIN System' chart (1 page, page image)",
                  "4-5 Carline/Series (legend: A/T automatic transmission, M/T manual transmission). Chevrolet: A/J Cobalt Base M/T (Canada only), A/K Cobalt LS M/T, A/L Cobalt LT M/T, A/P Cobalt Sport Coupe w/MAN TRANS, A/R Cobalt Base A/T (Canada only), A/S Cobalt LS A/T, A/T Cobalt LT A/T. Pontiac: A/J G5 Base M/T (Canada, Mexico only), A/L G5 LS M/T, A/N G5 GT M/T, A/R G5 Base A/T, A/S G5 LS A/T, A/T G5 GT A/T; M/B Solstice Base M/T, M/G Solstice Turbo M/T, M/K Solstice Street Edition w/MAN TRANS, M/N Solstice Base A/T, M/T Solstice Turbo A/T, M/Z Solstice Street Edition w/MAN TRANS; S/L Vibe FWD M/T, S/M Vibe AWD A/T, S/N Vibe GT FWD M/T, S/P Vibe FWD A/T, S/R Vibe GT FWD A/T. Cadillac: D/M CTS M/T RWD, D/F CTS A/T RWD, D/G CTS A/T AWD, D/H CTS A/T AWD NAV., D/J CTS A/T RWD NAV., D/N CTS-V, D/P CTS M/T RWD High Feature V6, D/R CTS RHD, D/S CTS A/T AWD HF V6, D/T CTS A/T AWD NAV. HF V6, D/U CTS A/T RWD HF V6, D/V CTS A/T RWD NAV. HF V6. Saturn: M/B Sky Base M/T, M/G Sky Redline Turbo M/T, M/C Sky Merlot Jewel Special M/T, M/D Sky Hydro Blue Special M/T, M/H Sky Redline Merlot Jewel Turbo Spcl. M/T, M/L Sky Hydro Blue Spcl. Turbo M/T, M/N Sky Base A/T, M/P Sky Merlot Jewel Special A/T, M/R Sky Hydro Blue Special A/T, M/T Sky Redline Turbo A/T, M/V Sky Merlot Jewel Special Turbo A/T, M/X Sky Hydro Blue Special Turbo A/T."),
    "m2009t": mid("5c58ab7c-2116-4894-b546-4e011c14d6d7", "NHTSA ORG4754, General Motors, '2009 Light Duty Truck, MPV and Incomplete Vehicle VIN System' chart (page image)",
                  "5-6 Line Chassis/Series, Chevrolet/GMC: A/1 HHR LS (1/2 ton) w/AUTO TRANS; A/2 HHR LT-1LT (1/2 ton) w/AUTO TRANS; A/3 HHR LS w/MAN TRANS; A/4 HHR 1LT w/MAN TRANS; A/5 HHR 2LT; A/6 HHR SS w/AUTO TRANS; A/7 HHR SS w/MAN TRANS; A/8 HHR LS PANEL VAN w/AUTO TRANS; A/9 HHR LS PANEL VAN w/MAN TRANS; A/0 HHR LT PANEL VAN."),
    # --- MY2010-2012 ---------------------------------------------------------
    "m2010": mid("d669e6ea-cc51-407e-8d8a-022853fc8483", "NHTSA ORG5410, General Motors, MY2010 VIN standard, September 2009, Tables B2a/B2c/B2g pages B2-B4, B7 and C9 (page images)",
                 "Chevrolet (positions 4-5): A A Cobalt LS (Manual), A B Cobalt LS (Automatic), A C Cobalt 1LT (Manual), A D Cobalt 1LT (Automatic), A E Cobalt 2LT (Manual), A F Cobalt 2LT (Automatic), A G Cobalt SS, A H Cobalt Internet Model (Manual), A J Cobalt Internet Model (Automatic); Y A-Y D Corvette 1LT-4LT (Manual), Y E-Y H Corvette 1LT-4LT (Automatic), Y J/K/L Corvette Z06 1LZ/2LZ/3LZ (Manual), Y M/N Corvette ZR1 1ZR/3ZR (Manual), Y P/R/S/T Corvette Grand Sport 1LT-4LT (Manual), Y U/V/W/X Grand Sport 1LT-4LT (Automatic); F A Camaro LS (Automatic), F B LT (Automatic), F C LT2 (Automatic), F E LS (Manual), F F LT (Manual), F G LT2 (Manual), F J SS (Automatic), F K 2SS (Automatic), F S SS (Manual), F T 2SS (Manual). Pontiac: A A G5 Base (Manual), A B Base (Automatic), A C SE (Manual), A D SE (Automatic), A E GT (Manual), A F GT (Automatic); M A Solstice Base (Automatic), M B Solstice Turbo (Automatic), M D Solstice Base (Manual), M E Solstice Turbo (Manual); S L Vibe FWD (Manual), S P Vibe FWD (Automatic), S M Vibe AWD, S N Vibe GT FWD (Manual), S R Vibe GT FWD (Automatic). Saturn: M B Sky Turbo (Automatic Trans), M C Sky Preferred (Automatic Trans), M E Sky Turbo (Manual Trans), M F Sky Preferred (Manual Trans). Chevrolet truck (positions 5-6): A A HHR LS (Automatic), A B HHR LT (Automatic), A C HHR 2LT (Automatic), A D HHR SS (Automatic), A E HHR LS (Manual), A F HHR 1LT (Manual), A G HHR 2LT (Manual), A H HHR SS (Manual)."),
    "m2010b": mid("320a7a51-6788-46e0-8b11-addd82c17df6", "NHTSA ORG5807, General Motors, MY2010 VIN standard, April 2010 revision (OCR)",
                  "Same transmission-bearing line/series entries, in the same order, as the September 2009 issue (Cobalt, Corvette, Camaro, G5, Solstice, Vibe, Sky, HHR); diffed line by line."),
    "m2011": mid("88d04ded-cf24-474e-86e5-de24593b3d32", "NHTSA ORG6450, General Motors LLC, MY2011 VIN standard, effective January 2011, pages 10 and 20 (page images)",
                 "Chevrolet passenger car 4-5: F A-F C Camaro LS/LT/LT2 (Automatic), F E-F G Camaro LS/LT/LT2 (Manual), F J SS (Automatic), F K 2SS (Automatic), F S SS (Manual), F T 2SS (Manual); P A Cruze 2LS (Canada - Automatic) AND P A Cruze 1LS (US - Manual); P B Cruze 2LS (Canada - Manual); P C Cruze 2LS (US - Automatic) and 1LS (Canada - Automatic); P D Cruze 2LS (US - Manual) and 1LS (Canada - Manual); P E Cruze 1FL (Automatic); P F Cruze 1LT (Automatic); P G 2LT (Automatic); P H LTZ (Automatic); P J Eco (Automatic); P K Eco (Manual); P L LTZ (Manual); Y A-Y D Corvette (Manual), Y E-Y H (Automatic), Y J-Y N Z06/ZR1 (Manual), Y P Grand Sport 1LT (Manual). Chevrolet truck 5-6: A A HHR LS (Automatic), A B HHR 1LT (Automatic), A C HHR 2LT (Automatic), A E HHR LS (Manual), A F HHR 1LT (Manual), A G HHR 2LT (Manual)."),
    "m2011d": mid("10ce2bf9-7c20-4ba8-8094-69e0ae89ad10", "NHTSA ORG5552, General Motors LLC, MY2011 VIN standard, effective 12/17/2009 (page images 11 and 21) - SUPERSEDED Cruze table",
                  "Draft Cruze codes that were changed before production: P F Cruze 1LT (Manual), P G 1LT (Automatic), P H 2LT (Manual), P J 2LT (Automatic), P K LTZ (Manual), P L LTZ (Automatic). Camaro, Corvette and HHR codes as in the January 2011 issue (HHR: A A/B/C (Automatic), A E/F/G (Manual))."),
    "m2012": mid("9da26fdd-6137-4610-8019-d80d53366cae", "NHTSA ORG6551, General Motors LLC, MY2012 VIN standard, effective 3/8/2011, pages 9-10 (page images)",
                 "F A Camaro LS (Automatic), F B LT (Automatic), F C LT2 (Automatic), F E LS (Manual), F F LT (Manual), F G LT2 (Manual), F J SS (Automatic), F K 2SS (Automatic), F S SS (Manual), F T 2SS (Manual); J A Sonic LS (Automatic), J B LS (Manual), J C LT (Automatic), J D LT (Manual), J E LTZ (Automatic), J F LTZ (Manual); P A Cruze 1LS (Automatic - Canada only), P B 1LS (Manual - Canada Only), P C 2LS (Automatic), P D 2LS (Manual), P E 1FL (Automatic), P F 1LT (Automatic), P G 2LT (Automatic), P H LTZ (Automatic), P J Eco (Automatic), P K Eco (Manual), P L 1LT (Manual), P M 2LT (Manual); Y A-Y D Corvette (Manual), Y E-Y H (Automatic), Y J-Y N Z06/ZR1 (Manual), Y P/R/S/T Grand Sport (Manual), Y U/V/W/X Grand Sport (Automatic)."),
    "m2013d": mid("fb4d4600-3d9c-44b5-9eff-be479854c16a", "NHTSA ORG7595, General Motors LLC, MY2013 VIN standard effective 1/27/2012 (text layer) - SUPERSEDED Cruze table",
                  "Cruze codes in this issue (P F 1LT (Automatic), P L 1LT (Manual), P M 2LT (Manual) ...) were replaced in the 4/5/2012 issue (ORG7939: P C 1LT (Automatic), P D 1LT (Manual), P F 2LT (Manual), P H Eco (Automatic), P J Eco (Manual)); lot 2013 Cruzes follow ORG7939."),
    # --- NUMMI (Pontiac Vibe 2003-2004) ---------------------------------------
    "nummi2003": mid("3958ee40-6c3f-43b7-98a1-45720cb208c4", "NHTSA 01-022-N11B-8517, New United Motor Manufacturing, Inc. 2001-11-28, 'VIN Coding System for 2003 Pontiac Vibe Vehicles', text layer",
                     "Carline & Series: SL Vibe Base, SM Vibe AWD (Opt VBY), SN Vibe GT (Opt VHP). 8th digit Engine Type: 8 = 1ZZ-FE 1.8L Engine (LV6), L = 2ZZ-GE GT Engine (LNK)."),
    "nummi2004": mid("1eb22ef0-6d02-4726-921d-8f61b701a142", "NHTSA 01-022-N11B-9260, New United Motor Manufacturing, Inc. 2002-11-25, 'VIN Coding System for 2004 Pontiac Vibe Vehicles', text layer",
                     "Carline & Series: SL Vibe Base, SM Vibe AWD (Opt VBY), SN Vibe GT (Opt VHP). 8th digit Engine Type: 1ZZ-FE 1.8L Engine (LV6), L = 2ZZ-GE GT Engine (LNK)."),
    # --- Metro engine code ------------------------------------------------------
    "e1999": mid("ecec2777-7c3e-4fd8-937e-faf425b69e69", "NHTSA 01-22-N11B-7024, General Motors 1998-10-26, MY1999 VIN standard, engine codes (VIN position 8), OCR",
                 "'6  1.0L L3 TBI  SUZUKI' (GM powertrain legend LP2)."),
    "e2000": mid("b1e3c9f9-70c4-417c-ba54-1fd3570b8b0d", "NHTSA 01-22-N11B-7504, General Motors 1999-12-02, MY2000 VIN standard, Table B4 engine codes, text layer",
                 "'6  1.0L L3 TBI  SUZUKI  LP2  Chev, GM Can'."),
    "web_ctsv": {"url": "https://grassrootsmotorsports.com/articles/buyer-guide-2004-2007-cadillac-cts-v", "doc": "Grassroots Motorsports, 'Buyer Guide: 2004-2007 Cadillac CTS-V' (read through web-search result text)",
                 "says": "'No slushbox was available, and the Tremec T56 six-speed was the only choice.'"},
    "web_cobalt_ss": {"url": "https://en.wikipedia.org/wiki/Chevrolet_Cobalt_SS", "doc": "Wikipedia, 'Chevrolet Cobalt SS' (read through web-search result text)",
                      "says": "The supercharged 2.0L LSJ coupe (2005-2007) was paired only with the Saab-designed F35 5-speed manual; the naturally aspirated 2.4L SS had the Getrag F23 manual or an automatic."},
    "web_ion_redline": {"url": "https://en.wikipedia.org/wiki/Saturn_Ion", "doc": "Wikipedia 'Saturn Ion' and Wards Auto 'Red Dawn Rising' (read through web-search result text)",
                        "says": "'The Red Line, available only as a quad coupe, uses a supercharged 2.0-litre inline four-cylinder and five-speed manual exclusively.'"},
    "web_metro": {"url": "https://consumerguide.com/used/1995-01-geochevrolet-metro/", "doc": "Consumer Guide, used 1995-2001 Geo/Chevrolet Metro (read through web-search result text)",
                  "says": "'5-speed manual gearbox was standard with both engines; 3-speed automatic optional only with the 4 cylinder.'"},
    "web_vibe_gt": {"url": "https://www.autoblog.com/2020/06/26/junkyard-gem-2004-pontiac-vibe-gt/", "doc": "Autoblog, 'Junkyard Gem: 2004 Pontiac Vibe GT' (read through web-search result text)",
                    "says": "Says the six-speed manual was the only transmission in early Vibe GTs and that an automatic was added later, contradicting other sources (Autoblog 2005 review: no automatic for the GT)."},
    "epa": {"url": EPA_URL, "doc": "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29), downloaded 2026-11-05", "says": ""},
}

# ---------------------------------------------------------------------------
# MY2013+ tables (text layers). Parsed from the latest GM filing for each model
# year; values are 'M' / 'A' / None (no transmission named in the description).
# ---------------------------------------------------------------------------
MODERN_TABLES = {'camaro': {2013: {'F9': (None, 'Chevrolet Camaro (Export Non US, Non Canada)'),
                   'FA': ('A', 'Chevrolet Camaro 2LS (Automatic)'),
                   'FB': ('A', 'Chevrolet Camaro LT (Automatic)'),
                   'FC': ('A', 'Chevrolet Camaro 2LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro LS (Manual)'),
                   'FF': ('M', 'Chevrolet Camaro LT (Manual)'),
                   'FG': ('M', 'Chevrolet Camaro 2LT (Manual)'),
                   'FJ': ('A', 'Chevrolet Camaro SS (Automatic)'),
                   'FK': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FL': ('A', 'Chevrolet Camaro ZL1 (Automatic)'),
                   'FS': ('M', 'Chevrolet Camaro SS (Manual)'),
                   'FT': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FZ': ('M', 'Chevrolet Camaro ZL1 (Manual)')},
            2014: {'F9': (None, 'Chevrolet Camaro (Export Non US, Non Canada)'),
                   'FA': ('A', 'Chevrolet Camaro 2LS (Automatic)'),
                   'FB': ('A', 'Chevrolet Camaro LT (Automatic)'),
                   'FC': ('A', 'Chevrolet Camaro 2LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro LS (Manual)'),
                   'FF': ('M', 'Chevrolet Camaro LT (Manual)'),
                   'FG': ('M', 'Chevrolet Camaro 2LT (Manual)'),
                   'FJ': ('A', 'Chevrolet Camaro SS (Automatic)'),
                   'FK': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FL': ('A', 'Chevrolet Camaro ZL1 (Automatic)'),
                   'FS': ('M', 'Chevrolet Camaro SS (Manual)'),
                   'FT': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FZ': ('M', 'Chevrolet Camaro ZL1 (Manual)')},
            2015: {'F9': (None, 'Chevrolet Camaro, Export (Non US, Non Canada)'),
                   'FA': ('M', 'Chevrolet Camaro, LS (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro, 2LS (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro, 1LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro, 1LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro, 2LT (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro, 2LT (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro, 1SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro, 1SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro, 2SS (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro, 2SS (Automatic)'),
                   'FL': ('M', 'Chevrolet Camaro, ZL1 (Manual)'),
                   'FM': ('A', 'Chevrolet Camaro, ZL1 (Automatic)'),
                   'FZ': ('M', 'Chevrolet Camaro, Z28 (Manual)')},
            2016: {'F9': (None, 'Chevrolet Camaro, (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro, 1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro, 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro, 2LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro, 2LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro, 1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro, 1SS (Automatic)'),
                   'FH': ('A', 'Chevrolet Camaro, 2SS (Automatic)')},
            2017: {'F9': (None, 'Chevrolet Camaro, (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro, 1LS or 1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro, 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro, 2LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro, 2LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro, 1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro, 1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro, 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro, 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro, ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro, ZL1 (Automatic)')},
            2018: {'F9': (None, 'Chevrolet Camaro, (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro, 1LS (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro, 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro, 2LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro, 2LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro, 1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro, 1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro, 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro, 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro, ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro, ZL1 (Automatic)')},
            2019: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')},
            2020: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1LZ/1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1LZ/1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')},
            2021: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1LZ/1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1LZ/1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')},
            2022: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1LZ/1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1LZ/1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')},
            2023: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1LZ/1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1LZ/1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')},
            2024: {'F9': (None, 'Chevrolet Camaro (Non-US, Non-Canada)'),
                   'FA': ('M', 'Chevrolet Camaro 1LS/1LT (Manual)'),
                   'FB': ('A', 'Chevrolet Camaro 1LS/ 1LT (Automatic)'),
                   'FC': ('M', 'Chevrolet Camaro 2LT/3LT (Manual)'),
                   'FD': ('A', 'Chevrolet Camaro 2LT/3LT (Automatic)'),
                   'FE': ('M', 'Chevrolet Camaro 1LZ/1SS (Manual)'),
                   'FF': ('A', 'Chevrolet Camaro 1LZ/1SS (Automatic)'),
                   'FG': ('M', 'Chevrolet Camaro 2SS (Manual)'),
                   'FH': ('A', 'Chevrolet Camaro 2SS (Automatic)'),
                   'FJ': ('M', 'Chevrolet Camaro ZL1 (Manual)'),
                   'FK': ('A', 'Chevrolet Camaro ZL1 (Automatic)')}},
 'corvette': {2013: {'Y1': ('M', 'Chevrolet Corvette 60th Anniversary (Manual)'),
                     'Y2': ('A', 'Chevrolet Corvette 60th Anniversary (Automatic)'),
                     'Y3': ('M', 'Chevrolet Corvette Grand Sport 60th Anniversary (Manual)'),
                     'Y4': ('A', 'Chevrolet Corvette Grand Sport 60th Anniversary (Automatic)'),
                     'Y5': ('M', 'Chevrolet Corvette Z06 60th Anniversary (Manual)'),
                     'YA': ('M', 'Chevrolet Corvette Standard (Manual)'),
                     'YB': ('M', 'Chevrolet Corvette Preferred (Manual)'),
                     'YC': ('M', 'Chevrolet Corvette Premium (Manual)'),
                     'YD': ('M', 'Chevrolet Corvette Custom (Manual)'),
                     'YE': ('A', 'Chevrolet Corvette Standard (Automatic)'),
                     'YF': ('A', 'Chevrolet Corvette Preferred (Automatic)'),
                     'YG': ('A', 'Chevrolet Corvette Premium (Automatic)'),
                     'YH': ('A', 'Chevrolet Corvette Custom (Automatic)'),
                     'YJ': ('M', 'Chevrolet Corvette Z06 Standard (Manual)'),
                     'YK': ('M', 'Chevrolet Corvette Z06 Premium (Manual)'),
                     'YL': ('M', 'Chevrolet Corvette Z06 Custom (Manual)'),
                     'YM': ('M', 'Chevrolet Corvette ZR1 Standard (Manual)'),
                     'YN': ('M', 'Chevrolet Corvette ZR1 Custom (Manual)'),
                     'YP': ('M', 'Chevrolet Corvette Grand Sport Standard (Manual)'),
                     'YR': ('M', 'Chevrolet Corvette Grand Sport Preferred (Manual)'),
                     'YS': ('M', 'Chevrolet Corvette Grand Sport Premium (Manual)'),
                     'YT': ('M', 'Chevrolet Corvette Grand Sport Custom (Manual)'),
                     'YU': ('A', 'Chevrolet Corvette Grand Sport Standard (Automatic)'),
                     'YV': ('A', 'Chevrolet Corvette Grand Sport Preferred (Automatic)'),
                     'YW': ('A', 'Chevrolet Corvette Grand Sport Premium (Automatic)'),
                     'YX': ('A', 'Chevrolet Corvette Grand Sport Custom (Automatic)'),
                     'YY': ('M', 'Chevrolet Corvette 427 Premium (Manual)'),
                     'YZ': ('M', 'Chevrolet Corvette 427 Custom(Manual)')},
              2014: {'Y9': (None, 'Chevrolet Corvette Stingray (Export only)'),
                     'YA': ('M', 'Chevrolet Corvette Stingray 1LT (Manual)'),
                     'YB': ('A', 'Chevrolet Corvette Stingray 1LT (Automatic)'),
                     'YC': ('M', 'Chevrolet Corvette Stingray 2LT (Manual)'),
                     'YD': ('A', 'Chevrolet Corvette Stingray 2LT (Automatic)'),
                     'YE': ('M', 'Chevrolet Corvette Stingray 3LT (Manual)'),
                     'YF': ('A', 'Chevrolet Corvette Stingray 3LT (Automatic)'),
                     'YG': ('M', 'Chevrolet Corvette Stingray 1LT (Manual) with Z51'),
                     'YH': ('A', 'Chevrolet Corvette Stingray 1LT (Automatic) with Z51'),
                     'YJ': ('M', 'Chevrolet Corvette Stingray 2LT (Manual) with Z51'),
                     'YK': ('A', 'Chevrolet Corvette Stingray 2LT (Automatic) with Z51'),
                     'YL': ('M', 'Chevrolet Corvette Stingray 3LT (Manual) with Z51'),
                     'YM': ('A', 'Chevrolet Corvette Stingray 3LT (Automatic) with Z51')},
              2015: {'Y9': (None, 'Chevrolet Corvette Stingray, Export (Non US, Non Canada)'),
                     'YA': ('M', 'Chevrolet Corvette Stingray, 1LT (Manual)'),
                     'YB': ('A', 'Chevrolet Corvette Stingray, 1LT (Automatic)'),
                     'YC': ('M', 'Chevrolet Corvette Stingray, 2LT (Manual)'),
                     'YD': ('A', 'Chevrolet Corvette Stingray, 2LT (Automatic)'),
                     'YE': ('M', 'Chevrolet Corvette Stingray, 3LT (Manual)'),
                     'YF': ('A', 'Chevrolet Corvette Stingray, 3LT (Automatic)'),
                     'YG': ('M', 'Chevrolet Corvette Stingray, 1LT (Manual) w/Z51'),
                     'YH': ('A', 'Chevrolet Corvette Stingray, 1LT (Automatic) w/Z51'),
                     'YJ': ('M', 'Chevrolet Corvette Stingray, 2LT (Manual) w/Z51'),
                     'YK': ('A', 'Chevrolet Corvette Stingray, 2LT (Automatic) w/Z51'),
                     'YL': ('M', 'Chevrolet Corvette Stingray, 3LT (Manual) w/Z51'),
                     'YM': ('A', 'Chevrolet Corvette Stingray, 3LT (Automatic) w/Z51')},
              2016: {'Y9': (None, 'Chevrolet Corvette, (Non-US, Non-Canada)'),
                     'YA': ('M', 'Chevrolet Corvette Stingray, Standard 1LT (Manual)'),
                     'YB': ('A', 'Chevrolet Corvette Stingray, Standard 1LT (Automatic)'),
                     'YC': ('M', 'Chevrolet Corvette Stingray, Preferred 2LT (Manual)'),
                     'YD': ('A', 'Chevrolet Corvette Stingray, Preferred 2LT (Automatic)'),
                     'YE': ('M', 'Chevrolet Corvette Stingray, Premium 3LT (Manual)'),
                     'YF': ('A', 'Chevrolet Corvette Stingray, Premium 3LT (Automatic)'),
                     'YG': ('M', 'Chevrolet Corvette Stingray, Standard 1LT (Manual) w/Z51'),
                     'YH': ('A', 'Chevrolet Corvette Stingray, Standard 1LT (Automatic) w/Z51'),
                     'YJ': ('M', 'Chevrolet Corvette Stingray, Preferred 2LT (Manual) w/Z51'),
                     'YK': ('A', 'Chevrolet Corvette Stingray, Preferred 2LT (Automatic) w/Z51'),
                     'YL': ('M', 'Chevrolet Corvette Stingray, Premium 3LT (Manual) w/Z51'),
                     'YM': ('A', 'Chevrolet Corvette Stingray, Premium 3LT (Automatic) w/Z51'),
                     'YN': ('M', 'Chevrolet Corvette, Standard 1LZ (Manual) w/Z06'),
                     'YP': ('A', 'Chevrolet Corvette, Standard 1LZ (Automatic) w/Z06'),
                     'YR': ('M', 'Chevrolet Corvette, Preferred 2LZ (Manual) w/Z06'),
                     'YS': ('A', 'Chevrolet Corvette, Preferred 2LZ (Automatic) w/Z06'),
                     'YT': ('M', 'Chevrolet Corvette, Premium 3LZ (Manual) w/Z06'),
                     'YU': ('A', 'Chevrolet Corvette, Premium 3LZ (Automatic) w/Z06')},
              2017: {'Y1': ('A', 'Chevrolet Corvette Grand Sport, Premium 3LT (Automatic)'),
                     'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': ('M', 'Chevrolet Corvette Stingray, Standard 1LT (Manual)'),
                     'YB': ('A', 'Chevrolet Corvette Stingray, Standard 1LT (Automatic)'),
                     'YC': ('M', 'Chevrolet Corvette Stingray, Preferred 2LT (Manual)'),
                     'YD': ('A', 'Chevrolet Corvette Stingray, Preferred 2LT (Automatic)'),
                     'YE': ('M', 'Chevrolet Corvette Stingray, Premium 3LT (Manual)'),
                     'YF': ('A', 'Chevrolet Corvette Stingray, Premium 3LT (Automatic)'),
                     'YG': ('M', 'Chevrolet Corvette Stingray, Standard 1LT (Manual) with Z51'),
                     'YH': ('A', 'Chevrolet Corvette Stingray, Standard 1LT (Automatic) with Z51'),
                     'YJ': ('M', 'Chevrolet Corvette Stingray, Preferred 2LT (Manual) with Z51'),
                     'YK': ('A', 'Chevrolet Corvette Stingray, Preferred 2LT (Automatic) with Z51'),
                     'YL': ('M', 'Chevrolet Corvette Stingray, Premium 3LT (Manual) with Z51'),
                     'YM': ('A', 'Chevrolet Corvette Stingray, Premium 3LT (Automatic) with Z51'),
                     'YN': ('M', 'Chevrolet Corvette Z06, Standard 1LZ (Manual)'),
                     'YP': ('A', 'Chevrolet Corvette Z06, Standard 1LZ (Automatic)'),
                     'YR': ('M', 'Chevrolet Corvette Z06, Preferred 2LZ (Manual)'),
                     'YS': ('A', 'Chevrolet Corvette Z06, Preferred 2LZ (Automatic)'),
                     'YT': ('M', 'Chevrolet Corvette Z06, Premium 3LZ (Manual)'),
                     'YU': ('A', 'Chevrolet Corvette Z06, Premium 3LZ (Automatic)'),
                     'YV': ('M', 'Chevrolet Corvette Grand Sport, Standard 1LT (Manual)'),
                     'YW': ('A', 'Chevrolet Corvette Grand Sport, Standard 1LT (Automatic)'),
                     'YX': ('M', 'Chevrolet Corvette Grand Sport, Preferred 2LT (Manual)'),
                     'YY': ('A', 'Chevrolet Corvette Grand Sport, Preferred 2LT (Automatic)'),
                     'YZ': ('M', 'Chevrolet Corvette Grand Sport, Premium 3LT (Manual)')},
              2018: {'Y1': ('A', 'Corvette Grand Sport Premium 3LT (Automatic)'),
                     'Y9': (None, 'Chevrolet Corvette (Export only)'),
                     'YA': ('M', 'Corvette Stingray Standard 1LT (Manual)'),
                     'YB': ('A', 'Corvette Stingray Standard 1LT (Automatic)'),
                     'YC': ('M', 'Corvette Stingray Preferred 2LT (Manual)'),
                     'YD': ('A', 'Corvette Stingray Preferred 2LT (Automatic)'),
                     'YE': ('M', 'Corvette Stingray Premium 3LT (Manual)'),
                     'YF': ('A', 'Corvette Stingray Premium 3LT (Automatic)'),
                     'YG': ('M', 'Corvette Stingray Standard 1LT (Manual) with Z51'),
                     'YH': ('A', 'Corvette Stingray Standard 1LT (Automatic) with Z51'),
                     'YJ': ('M', 'Corvette Stingray Preferred 2LT (Manual) with Z51'),
                     'YK': ('A', 'Corvette Stingray Preferred 2LT (Automatic) with Z51'),
                     'YL': ('M', 'Corvette Stingray Premium 3LT (Manual) with Z51'),
                     'YM': ('A', 'Corvette Stingray Premium 3LT (Automatic) with Z51'),
                     'YN': ('M', 'Corvette Z06 Standard 1LZ (Manual)'),
                     'YP': ('A', 'Corvette Z06 Standard 1LZ (Automatic)'),
                     'YR': ('M', 'Corvette Z06 Preferred 2LZ (Manual)'),
                     'YS': ('A', 'Corvette Z06 Preferred 2LZ (Automatic)'),
                     'YT': ('M', 'Corvette Z06 Premium 3LZ (Manual)'),
                     'YU': ('A', 'Corvette Z06 Premium 3LZ (Automatic)'),
                     'YV': ('M', 'Corvette Grand Sport Standard 1LT (Manual)'),
                     'YW': ('A', 'Corvette Grand Sport Standard 1LT (Automatic)'),
                     'YX': ('M', 'Corvette Grand Sport Preferred 2LT (Manual)'),
                     'YY': ('A', 'Corvette Grand Sport Preferred 2LT (Automatic)'),
                     'YZ': ('M', 'Corvette Grand Sport Premium 3LT (Manual)')},
              2019: {'Y1': ('A', 'Chevrolet Corvette Grand Sport Premium 3LT (Automatic)'),
                     'Y2': ('M', 'Chevrolet Corvette ZR1 Standard 1ZR (Manual)'),
                     'Y3': ('A', 'Chevrolet Corvette ZR1 Standard 1ZR (Automatic)'),
                     'Y4': ('M', 'Chevrolet Corvette ZR1 Premium 3ZR (Manual)'),
                     'Y5': ('A', 'Chevrolet Corvette ZR1 Premium 3ZR (Automatic)'),
                     'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': ('M', 'Chevrolet Corvette Stingray Standard 1LT (Manual)'),
                     'YB': ('A', 'Chevrolet Corvette Stingray Standard 1LT (Automatic)'),
                     'YC': ('M', 'Chevrolet Corvette Stingray Preferred 2LT (Manual)'),
                     'YD': ('A', 'Chevrolet Corvette Stingray Preferred 2LT (Automatic)'),
                     'YE': ('M', 'Chevrolet Corvette Stingray Premium 3LT (Manual)'),
                     'YF': ('A', 'Chevrolet Corvette Stingray Premium 3LT (Automatic)'),
                     'YG': ('M', 'Chevrolet Corvette Stingray Standard 1LT (Manual) with Z51'),
                     'YH': ('A', 'Chevrolet Corvette Stingray Standard 1LT (Automatic) with Z51'),
                     'YJ': ('M', 'Chevrolet Corvette Stingray Preferred 2LT (Manual) with Z51'),
                     'YK': ('A', 'Chevrolet Corvette Stingray Preferred 2LT (Automatic) with Z51'),
                     'YL': ('M', 'Chevrolet Corvette Stingray Premium 3LT (Manual) with Z51'),
                     'YM': ('A', 'Chevrolet Corvette Stingray Premium 3LT (Automatic) with Z51'),
                     'YN': ('M', 'Chevrolet Corvette Z06 Standard 1LZ (Manual)'),
                     'YP': ('A', 'Chevrolet Corvette Z06 Standard 1LZ (Automatic)'),
                     'YR': ('M', 'Chevrolet Corvette Z06 Preferred 2LZ (Manual)'),
                     'YS': ('A', 'Chevrolet Corvette Z06 Preferred 2LZ (Automatic)'),
                     'YT': ('M', 'Chevrolet Corvette Z06 Premium 3LZ (Manual)'),
                     'YV': ('M', 'Chevrolet Corvette Grand Sport Standard 1LT (Manual)'),
                     'YW': ('A', 'Chevrolet Corvette Grand Sport Standard 1LT (Automatic)'),
                     'YX': ('M', 'Chevrolet Corvette Grand Sport Preferred 2LT (Manual)'),
                     'YY': ('A', 'Chevrolet Corvette Grand Sport Preferred 2LT (Automatic)'),
                     'YZ': ('M', 'Chevrolet Corvette Grand Sport Premium 3LT (Manual)')},
              2020: {'Y6': (None, 'Chevrolet Corvette Standard 1LT'),
                     'Y7': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'Y8': (None, 'Chevrolet Corvette Premium 3LT'),
                     'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)')},
              2021: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Standard 1LT'),
                     'YB': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'YC': (None, 'Chevrolet Corvette Premium 3LT')},
              2022: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Standard 1LT'),
                     'YB': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'YC': (None, 'Chevrolet Corvette Premium 3LT')},
              2023: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Standard 1LT'),
                     'YB': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'YC': (None, 'Chevrolet Corvette Premium 3LT'),
                     'YD': (None, 'Chevrolet Corvette Z06 Standard1LZ'),
                     'YE': (None, 'Chevrolet Corvette Z06 Preferred 2LZ'),
                     'YF': (None, 'Chevrolet Corvette Z06 Premium 3LZ')},
              2024: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Standard 1LT'),
                     'YB': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'YC': (None, 'Chevrolet Corvette Premium 3LT'),
                     'YD': (None, 'Chevrolet Corvette Z06 Standard1LZ'),
                     'YE': (None, 'Chevrolet Corvette Z06 Preferred 2LZ'),
                     'YF': (None, 'Chevrolet Corvette Z06 Premium 3LZ'),
                     'YK': (None, 'Chevrolet Corvette E-Ray Standard1LZ'),
                     'YL': (None, 'Chevrolet Corvette E-Ray Preferred 2LZ'),
                     'YM': (None, 'Chevrolet Corvette E-Ray Premium 3LZ')},
              2025: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Standard 1LT'),
                     'YB': (None, 'Chevrolet Corvette Preferred 2LT'),
                     'YC': (None, 'Chevrolet Corvette Premium 3LT'),
                     'YD': (None, 'Chevrolet Corvette Z06 Standard1LZ'),
                     'YE': (None, 'Chevrolet Corvette Z06 Preferred 2LZ'),
                     'YF': (None, 'Chevrolet Corvette Z06 Premium 3LZ'),
                     'YG': (None, 'Chevrolet Corvette ZR1 Standard 1LZ'),
                     'YJ': (None, 'Chevrolet Corvette ZR1 Premium 3LZ'),
                     'YK': (None, 'Chevrolet Corvette E-Ray Standard 1LZ'),
                     'YL': (None, 'Chevrolet Corvette E-Ray Preferred 2LZ'),
                     'YM': (None, 'Chevrolet Corvette E-Ray Premium 3LZ')},
              2026: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Stingray 1LT'),
                     'YB': (None, 'Chevrolet Corvette Stingray 2LT'),
                     'YC': (None, 'Chevrolet Corvette Stingray 3LT'),
                     'YD': (None, 'Chevrolet Corvette Z06 1LZ'),
                     'YE': (None, 'Chevrolet Corvette Z06 2LZ'),
                     'YF': (None, 'Chevrolet Corvette Z06 3LZ'),
                     'YG': (None, 'Chevrolet Corvette ZR1 1LZ'),
                     'YJ': (None, 'Chevrolet Corvette ZR1 3LZ'),
                     'YK': (None, 'Chevrolet Corvette E-Ray 1LZ (Performance Hybrid)'),
                     'YL': (None, 'Chevrolet Corvette E-Ray 2LZ (Performance Hybrid)'),
                     'YM': (None, 'Chevrolet Corvette E-Ray 3LZ (Performance Hybrid)'),
                     'YN': (None, 'Chevrolet Corvette ZR1X 1LZ (Performance Hybrid)'),
                     'YR': (None, 'Chevrolet Corvette ZR1X 3LZ (Performance Hybrid)')},
              2027: {'Y9': (None, 'Chevrolet Corvette (Non-US, Non-Canada)'),
                     'YA': (None, 'Chevrolet Corvette Stingray 1LT'),
                     'YB': (None, 'Chevrolet Corvette Stingray 2LT'),
                     'YC': (None, 'Chevrolet Corvette Stingray 3LT'),
                     'YD': (None, 'Chevrolet Corvette Z06 1LZ'),
                     'YE': (None, 'Chevrolet Corvette Z06 2LZ'),
                     'YF': (None, 'Chevrolet Corvette Z06 3LZ'),
                     'YG': (None, 'Chevrolet Corvette ZR1 1LZ'),
                     'YJ': (None, 'Chevrolet Corvette ZR1 3LZ'),
                     'YN': (None, 'Chevrolet Corvette ZR1X 1LZ (Performance Hybrid)'),
                     'YR': (None, 'Chevrolet Corvette ZR1X 3LZ (Performance Hybrid)'),
                     'YS': (None, 'Chevrolet Corvette Grand Sport 1LT'),
                     'YT': (None, 'Chevrolet Corvette Grand Sport 2LT'),
                     'YV': (None, 'Chevrolet Corvette Grand Sport 3LT'),
                     'YW': (None, 'Chevrolet Corvette Grand Sport X 1LT (Performance Hybrid)'),
                     'YX': (None, 'Chevrolet Corvette Grand Sport X 2LT (Performance Hybrid)'),
                     'YY': (None, 'Chevrolet Corvette Grand Sport X 3LT (Performance Hybrid)')}},
 'cruze': {2013: {'P8': (None, 'Chevrolet Cruze (Export Only Non US, Non Canada)'),
                  'PA': ('A', 'Chevrolet Cruze 1LS (Automatic)'),
                  'PB': ('M', 'Chevrolet Cruze 1LS (Manual)'),
                  'PC': ('A', 'Chevrolet Cruze 1LT (Automatic)'),
                  'PD': ('M', 'Chevrolet Cruze 1LT (Manual)'),
                  'PE': ('A', 'Chevrolet Cruze 2LT (Automatic)'),
                  'PF': ('M', 'Chevrolet Cruze 2LT (Manual)'),
                  'PG': ('A', 'Chevrolet Cruze LTZ (Automatic)'),
                  'PH': ('A', 'Chevrolet Cruze Eco (Automatic)'),
                  'PJ': ('M', 'Chevrolet Cruze Eco (Manual)'),
                  'PK': ('A', 'Chevrolet Cruze 1LT/Fleet Model (Automatic)'),
                  'PL': ('A', 'Chevrolet Cruze 2LS (Automatic Canada Only)'),
                  'PM': ('M', 'Chevrolet Cruze 2LS (Manual Canada Only)')},
           2014: {'P7': ('A', 'Chevrolet Cruze Diesel (Automatic)'),
                  'P8': (None, 'Chevrolet Cruze (Export Only Non US, Non Canada)'),
                  'PA': ('A', 'Chevrolet Cruze 1LS (Automatic)'),
                  'PB': ('M', 'Chevrolet Cruze 1LS (Manual)'),
                  'PC': ('A', 'Chevrolet Cruze 1LT (Automatic)'),
                  'PD': ('M', 'Chevrolet Cruze 1LT (Manual)'),
                  'PE': ('A', 'Chevrolet Cruze 2LT (Automatic)'),
                  'PF': ('M', 'Chevrolet Cruze 2LT (Manual)'),
                  'PG': ('A', 'Chevrolet Cruze LTZ (Automatic)'),
                  'PH': ('A', 'Chevrolet Cruze Eco (Automatic)'),
                  'PJ': ('M', 'Chevrolet Cruze Eco (Manual)'),
                  'PK': ('A', 'Chevrolet Cruze 1LT/Fleet (Automatic)'),
                  'PL': ('A', 'Chevrolet Cruze 2LS (Automatic Canada Only)'),
                  'PM': ('M', 'Chevrolet Cruze 2LS (Manual Canada Only)')},
           2015: {'P7': ('A', 'Chevrolet Cruze, Diesel (Automatic)'),
                  'P8': (None, 'Chevrolet Cruze, Export (Non US, Non Canada)'),
                  'PA': ('A', 'Chevrolet Cruze, LS (Automatic)'),
                  'PB': ('M', 'Chevrolet Cruze, LS (Manual)'),
                  'PC': ('A', 'Chevrolet Cruze, 1LT (Automatic)'),
                  'PD': ('M', 'Chevrolet Cruze, 1LT (Manual)'),
                  'PE': ('A', 'Chevrolet Cruze, 2LT (Automatic)'),
                  'PF': ('M', 'Chevrolet Cruze, 2LT (Manual)'),
                  'PG': ('A', 'Chevrolet Cruze, LTZ (Automatic)'),
                  'PH': ('A', 'Chevrolet Cruze, Eco (Automatic)'),
                  'PJ': ('M', 'Chevrolet Cruze, Eco (Manual)'),
                  'PK': ('A', 'Chevrolet Cruze, 1LT Fleet (Automatic)'),
                  'PL': ('A', 'Chevrolet Cruze, 2LS (Automatic) (Canada Only)'),
                  'PM': ('M', 'Chevrolet Cruze, 2LS (Manual) (Canada Only)')},
           2016: {'B8': (None, 'Chevrolet Cruze, (Non-US, Non-Canada)'),
                  'BA': ('M', 'Chevrolet Cruze, L (Manual)'),
                  'BB': ('M', 'Chevrolet Cruze, LS (Manual)'),
                  'BC': ('A', 'Chevrolet Cruze, LS (Automatic)'),
                  'BD': ('M', 'Chevrolet Cruze, LT (Manual)'),
                  'BE': ('A', 'Chevrolet Cruze, LT (Automatic)'),
                  'BG': ('A', 'Chevrolet Cruze, Premier (Automatic)')},
           2017: {'B8': (None, 'Chevrolet Cruze, (Non-US, Non-Canada)'),
                  'BA': ('M', 'Chevrolet Cruze, L (Manual)'),
                  'BB': ('M', 'Chevrolet Cruze, LS (Manual)'),
                  'BC': ('A', 'Chevrolet Cruze, LS (Automatic)'),
                  'BD': ('M', 'Chevrolet Cruze, LT (Manual)'),
                  'BE': ('A', 'Chevrolet Cruze, LT (Automatic)'),
                  'BF': ('A', 'Chevrolet Cruze, Premier (Automatic)'),
                  'BG': ('M', 'Chevrolet Cruze, Diesel (Manual)'),
                  'BH': ('A', 'Chevrolet Cruze, Diesel (Automatic)')},
           2018: {'B8': (None, 'Chevrolet Cruze, (Non-US, Non-Canada)'),
                  'BA': ('M', 'Chevrolet Cruze, L (Manual)'),
                  'BB': ('M', 'Chevrolet Cruze, LS (Manual)'),
                  'BC': ('A', 'Chevrolet Cruze, LS (Automatic)'),
                  'BD': ('M', 'Chevrolet Cruze, LT (Manual)'),
                  'BE': ('A', 'Chevrolet Cruze, LT (Automatic)'),
                  'BF': ('A', 'Chevrolet Cruze, Premier (Automatic)'),
                  'BG': ('M', 'Chevrolet Cruze, Diesel (Manual)'),
                  'BH': ('A', 'Chevrolet Cruze, Diesel (Automatic)')},
           2019: {'B8': (None, 'Chevrolet Cruze (Non-US, Non-Canada)'),
                  'BA': ('A', 'Chevrolet Cruze L (Automatic)'),
                  'BC': ('A', 'Chevrolet Cruze LS (Automatic)'),
                  'BE': ('A', 'Chevrolet Cruze LT (Automatic)'),
                  'BF': ('A', 'Chevrolet Cruze Premier (Automatic)'),
                  'BH': ('A', 'Chevrolet Cruze Diesel (Automatic)'),
                  'BJ': ('C', 'Chevrolet Cruze (CVT)')}},
 'cruze_limited': {2016: {'P8': (None, 'Chevrolet Cruze Limited, (Non-US, Non-Canada)'),
                          'PA': ('M', 'Chevrolet Cruze Limited, L (Manual)'),
                          'PB': ('M', 'Chevrolet Cruze Limited, LS (Manual)'),
                          'PC': ('A', 'Chevrolet Cruze Limited, LS (Automatic)'),
                          'PD': ('M', 'Chevrolet Cruze Limited, 1LT (Manual)'),
                          'PE': ('A', 'Chevrolet Cruze Limited, 1LT (Automatic)'),
                          'PF': ('A', 'Chevrolet Cruze Limited, 2LT (Automatic)'),
                          'PG': ('A', 'Chevrolet Cruze Limited, LTZ (Automatic)'),
                          'PH': ('M', 'Chevrolet Cruze Limited, Eco (Manual)'),
                          'PJ': ('A', 'Chevrolet Cruze Limited, Eco (Automatic)'),
                          'PK': ('M', 'Chevrolet Cruze Limited, 2LS (Manual)(Canada Only)'),
                          'PL': ('A', 'Chevrolet Cruze Limited, 2LS (Automatic)(Canada Only)'),
                          'PM': ('A', 'Chevrolet Cruze Limited, 1LT/Fleet Model (Automatic)'),
                          'PN': ('M', 'Chevrolet Cruze Limited 2LT (Manual)(Canada Only)')}},
 'sonic': {2013: {'J8': (None, 'Chevrolet Sonic (Export Non-US, Non-Cananda)'),
                  'JA': ('A', 'Chevrolet Sonic LS (Automatic)'),
                  'JB': ('M', 'Chevrolet Sonic LS (Manual)'),
                  'JC': ('A', 'Chevrolet Sonic LT (Automatic)'),
                  'JD': ('M', 'Chevrolet Sonic LT (Manual)'),
                  'JE': ('A', 'Chevrolet Sonic LTZ (Automatic)'),
                  'JF': ('M', 'Chevrolet Sonic LTZ (Manual)'),
                  'JG': ('A', 'Chevrolet Sonic RS (Automatic)'),
                  'JH': ('M', 'Chevrolet Sonic RS (Manual)')},
           2014: {'J8': (None, 'Chevrolet Sonic (Export Non-US, Non-Cananda)'),
                  'JA': ('A', 'Chevrolet Sonic LS (Automatic)'),
                  'JB': ('M', 'Chevrolet Sonic LS (Manual)'),
                  'JC': ('A', 'Chevrolet Sonic LT (Automatic)'),
                  'JD': ('M', 'Chevrolet Sonic LT (Manual)'),
                  'JE': ('A', 'Chevrolet Sonic LTZ (Automatic)'),
                  'JF': ('M', 'Chevrolet Sonic LTZ (Manual)'),
                  'JG': ('A', 'Chevrolet Sonic RS (Automatic)'),
                  'JH': ('M', 'Chevrolet Sonic RS (Manual)')},
           2015: {'J8': (None, 'Chevrolet Sonic, Export (Non US, Non Canada)'),
                  'JA': ('A', 'Chevrolet Sonic, LS (Automatic)'),
                  'JB': ('M', 'Chevrolet Sonic, LS (Manual)'),
                  'JC': ('A', 'Chevrolet Sonic, LT (Automatic)'),
                  'JD': ('M', 'Chevrolet Sonic, LT (Manual)'),
                  'JE': ('A', 'Chevrolet Sonic, LTZ (Automatic)'),
                  'JF': ('M', 'Chevrolet Sonic, LTZ (Manual)'),
                  'JG': ('A', 'Chevrolet Sonic, RS (Automatic)'),
                  'JH': ('M', 'Chevrolet Sonic, RS (Manual)')},
           2016: {'J8': (None, 'Chevrolet Sonic (Non-US, Non Canada)'),
                  'JA': ('A', 'Chevrolet Sonic, LS (Automatic)'),
                  'JB': ('M', 'Chevrolet Sonic, LS (Manual)'),
                  'JC': ('A', 'Chevrolet Sonic, LT (Automatic)'),
                  'JD': ('M', 'Chevrolet Sonic, LT (Manual)'),
                  'JE': ('A', 'Chevrolet Sonic, LTZ (Automatic)'),
                  'JF': ('M', 'Chevrolet Sonic, LTZ (Manual)'),
                  'JG': ('A', 'Chevrolet Sonic, RS (Automatic)'),
                  'JH': ('M', 'Chevrolet Sonic, RS (Manual)')},
           2017: {'J8': (None, 'Chevrolet Sonic (Non-US, Non Canada)'),
                  'JA': ('M', 'Chevrolet Sonic, LS (Manual)'),
                  'JB': ('A', 'Chevrolet Sonic, LS (Automatic)'),
                  'JC': ('M', 'Chevrolet Sonic, LT (Manual)'),
                  'JD': ('A', 'Chevrolet Sonic, LT (Automatic)'),
                  'JE': ('M', 'Chevrolet Sonic, Premier (Manual)'),
                  'JF': ('A', 'Chevrolet Sonic, Premier (Automatic)'),
                  'JG': ('A', 'Chevrolet Sonic, FL (Automatic)')},
           2018: {'J8': (None, 'Chevrolet Sonic (Non-US, Non Canada)'),
                  'JA': ('M', 'Chevrolet Sonic, LS (Manual)'),
                  'JB': ('A', 'Chevrolet Sonic, LS (Automatic)'),
                  'JC': ('M', 'Chevrolet Sonic, LT (Manual)'),
                  'JD': ('A', 'Chevrolet Sonic, LT (Automatic)'),
                  'JE': ('M', 'Chevrolet Sonic, Premier (Manual)'),
                  'JF': ('A', 'Chevrolet Sonic, Premier (Automatic)'),
                  'JG': ('A', 'Chevrolet Sonic, FL (Automatic)')},
           2019: {'J8': (None, 'Chevrolet Sonic (Non-US, Non-Canada)'),
                  'JA': ('M', 'Chevrolet Sonic LS (Manual)'),
                  'JB': ('A', 'Chevrolet Sonic LS (Automatic)'),
                  'JC': ('M', 'Chevrolet Sonic LT (Manual)'),
                  'JD': ('A', 'Chevrolet Sonic LT (Automatic)'),
                  'JE': ('M', 'Chevrolet Sonic Premier (Manual)'),
                  'JF': ('A', 'Chevrolet Sonic Premier (Automatic)'),
                  'JG': ('A', 'Chevrolet Sonic FL (Automatic)')},
           2020: {'J8': (None, 'Chevrolet Sonic (Non-US, Non-Canada)'),
                  'JB': ('A', 'Chevrolet Sonic LS (Automatic)'),
                  'JD': ('A', 'Chevrolet Sonic LT (Automatic)'),
                  'JF': ('A', 'Chevrolet Sonic Premier (Automatic)'),
                  'JG': ('A', 'Chevrolet Sonic FL (Automatic)')}},
 'spark': {2013: {'CA': ('M', 'Chevrolet Spark LS (Manual)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual)'),
                  'CF': ('A', 'Chevrolet Spark 2LT (Automatic)')},
           2014: {'CA': ('M', 'Chevrolet Spark LS (Manual)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual)'),
                  'CF': ('A', 'Chevrolet Spark 2LT (Automatic)'),
                  'CK': (None, 'Chevrolet Spark EV 1LT'),
                  'CL': (None, 'Chevrolet Spark EV 2LT')},
           2015: {'CA': ('M', 'Chevrolet Spark, LS (Manual)'),
                  'CB': ('A', 'Chevrolet Spark, LS (Automatic)'),
                  'CC': ('M', 'Chevrolet Spark, 1LT (Manual)'),
                  'CD': ('A', 'Chevrolet Spark, 1LT (Automatic)'),
                  'CE': ('M', 'Chevrolet Spark, 2LT (Manual)'),
                  'CF': ('A', 'Chevrolet Spark, 2LT (Automatic)'),
                  'CK': (None, 'Chevrolet Spark EV, 1LT'),
                  'CL': (None, 'Chevrolet Spark EV, 2LT')},
           2016: {'CA': ('M', 'Chevrolet Spark, LS (Manual)'),
                  'CB': ('A', 'Chevrolet Spark, LS (Automatic)'),
                  'CC': ('M', 'Chevrolet Spark, 1LT (Manual)'),
                  'CD': ('A', 'Chevrolet Spark, 1LT (Automatic)'),
                  'CE': ('M', 'Chevrolet Spark, 2LT (Manual)'),
                  'CF': ('A', 'Chevrolet Spark, 2LT (Automatic)'),
                  'CK': (None, 'Chevrolet Spark EV, 1LT'),
                  'CL': (None, 'Chevrolet Spark EV, 2LT')},
           2017: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark, LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark, LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark, 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark, 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark, 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark, 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark, ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark, ACTIV (Automatic) (ACTIV)')},
           2018: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark, LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark, LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark, 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark, 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark, 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark, 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark, ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark, ACTIV (Automatic) (ACTIV)')},
           2019: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark ACTIV (Automatic) (ACTIV)')},
           2020: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark ACTIV (Automatic) (ACTIV)')},
           2021: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark ACTIV (Automatic) (ACTIV)')},
           2022: {'C9': (None, 'Chevrolet Spark (Non-US, Non-Canada)'),
                  'CA': ('M', 'Chevrolet Spark LS (Manual) (LS)'),
                  'CB': ('A', 'Chevrolet Spark LS (Automatic) (LS)'),
                  'CC': ('M', 'Chevrolet Spark 1LT (Manual) (LT)'),
                  'CD': ('A', 'Chevrolet Spark 1LT (Automatic) (LT)'),
                  'CE': ('M', 'Chevrolet Spark 2LT (Manual) (LT)'),
                  'CF': ('A', 'Chevrolet Spark 2LT(Automatic) (LT)'),
                  'CG': ('M', 'Chevrolet Spark ACTIV (Manual) (ACTIV)'),
                  'CH': ('A', 'Chevrolet Spark ACTIV (Automatic) (ACTIV)')}},
 'ss': {2014: {'F1': (None, 'Chevrolet SS')},
        2015: {'F1': (None, 'Chevrolet SS')},
        2016: {'F1': ('A', 'Chevrolet SS, (Automatic)'), 'F2': ('M', 'Chevrolet SS, (Manual)')},
        2017: {'F1': ('A', 'Chevrolet SS, (Automatic)'), 'F2': ('M', 'Chevrolet SS, (Manual)')}}}
MODERN_CITES = {2013: ('b6b88ead-1edb-4e59-90ce-95d1aca53664', 'ORG7939', '4/9/2012'),
 2014: ('48e09950-0df8-422a-a8e0-359af8ace369', 'ORG8840', '5/28/2013'),
 2015: ('a6b2d699-0c21-4328-ac05-6754c43c1817', 'ORG9102', '12/5/2013'),
 2016: ('c07d98af-f379-4bf7-abcb-aca7bc4ad77e', 'ORG13142', '8/22/2016'),
 2017: ('97625831-b145-43f1-bd45-38552cb801ba', 'ORG16931', '6/13/2019'),
 2018: ('ebbd7a16-2e09-461c-befa-6d66741512f1', 'ORG16930', '6/13/2019'),
 2019: ('443f140e-b473-445e-a764-fca220bb9fbe', 'ORG16929', '6/13/2019'),
 2020: ('54c0a5c9-b0b5-47ee-8ddc-51d84c9e1f67', 'ORG18718', '1/29/2021'),
 2021: ('92cf0842-c439-4332-a626-47d04fe42df0', 'ORG19096', '5/10/2021'),
 2022: ('d071ecc3-da49-46c7-a41f-45fbd6365eca', 'ORG22273', '10/19/2023'),
 2023: ('6aba8e7e-ed23-4a50-b8a8-5020840b8f60', 'ORG22988', '4/17/2024'),
 2024: ('fda1b26a-799a-4e39-9dcd-b6642632b4ef', 'ORG24356', '5/14/2025'),
 2025: ('085c3eed-3f5c-436e-a657-ec1d721b6483', 'ORG24917', '10/24/2025'),
 2026: ('4e07ebf8-b595-44c9-ae70-d730bb0fa553', 'ORG26694', '6/30/2026'),
 2027: ('dd6dfe86-6010-40a1-82d9-b683da0c6e53', 'ORG27118', '10/30/2026')}

for _y, (_guid, _org, _date) in MODERN_CITES.items():
    C[f"modern{_y}"] = mid(_guid, f"NHTSA {_org}, General Motors LLC, MY{_y} VIN standard (latest MY{_y} issue in MID, MID date {_date}), section '4~5: VEHICLE LINE/SERIES', text layer",
                           "Line/series descriptions name the transmission for Camaro, Corvette (to MY2019), Cruze, Cruze Limited, Sonic, Spark and Chevrolet SS, e.g. 'F A: Chevrolet Camaro, 1LS or 1LT (Manual)', 'B A: Chevrolet Cruze, L (Manual)', 'C A: Chevrolet Spark, LS (Manual)'; the codes are listed in this rule's vin_condition.")


def _modern(model: str, years) -> dict:
    out = {}
    for y in years:
        t = MODERN_TABLES[model].get(y)
        if t:
            out[y] = {c: ({"M": M, "A": A}.get(v[0]), v[1]) for c, v in t.items()}
    return out


def _merge(*tables: dict) -> dict:
    out: dict = {}
    for t in tables:
        for y, codes in t.items():
            out.setdefault(y, {}).update(codes)
    return out


def same(years, table) -> dict:
    return {y: dict(table) for y in years}


# ---------------------------------------------------------------------------
# Year tables
# ---------------------------------------------------------------------------
_S_COMMON = {"ZG": (M, "SL1 MANUAL"), "ZH": (A, "SL1 AUTO"), "ZK": (A, "SL2 AUTO"), "ZP": (A, "SC1 AUTO"),
             "ZR": (M, "SC2 MANUAL"), "ZY": (A, "SC2 AUTO"), "JR": (M, "LS MANUAL"), "JS": (A, "LS AUTO"),
             "JW": (None, "LS2, LW2 (no transmission named)")}
_ZN_BODY = (BY6, {"1": (M, "SC1 MANUAL (coupe: VIN position 6 = 1, two-door coupe)"),
                  "8": (A, "SW2 AUTO (wagon: VIN position 6 = 8, station wagon)")})
_JU_BODY = (BY6, {"5": (A, "LS1 AUTO (sedan: VIN position 6 = 5; 'LW1' wagons carry no transmission)")})
SATURN_SL = {
    2000: {**_S_COMMON, "ZF": (M, "SL MANUAL"), "ZJ": (M, "SW2 MANUAL, SL2 MANUAL"), "ZM": (A, "SW1 AUTO RHD"),
           "ZN": _ZN_BODY, "JT": (M, "LS1 MANUAL"), "JU": _JU_BODY},
    2001: {**_S_COMMON, "ZF": (None, "SL (no transmission named in MY2001)"), "ZJ": (M, "SW2 MANUAL, SL2 MANUAL"),
           "ZM": (None, "SW1"), "ZN": _ZN_BODY, "JT": (M, "LS1 MANUAL"), "JU": _JU_BODY},
    2002: {**_S_COMMON, "ZF": (M, "SL Manual"), "ZJ": (M, "SL2 MANUAL"), "ZN": (M, "SC1 MANUAL"),
           "ZS": (M, "SL MANUAL SPRING SPECIAL"), "JT": (M, "LS1/LW1 MANUAL"), "JU": (A, "LS1/LW1 AUTO")},
    2003: {"JT": (M, "L200/LW200 MANUAL"), "JU": (A, "L200/LW200 AUTO"), "JW": (None, "L300, LW300")},
}
_ION_03 = {"AF": (M, "ION Level I Sedan Manual"), "AG": (A, "ION Level I Sedan Auto"), "AJ": (A, "ION Level 2 Sedan Auto"),
           "AK": (M, "ION Level 3 Sedan Manual"), "AL": (A, "ION Level 3 Sedan Auto"), "AM": (M, "ION Level 2 Coupe Manual"),
           "AN": (A, "ION Level 2 Coupe Auto"), "AV": (M, "ION Level 3 Coupe Manual"), "AW": (A, "ION Level 3 Coupe Auto"),
           "AZ": (M, "ION Level 2 Sedan Manual")}
_ION_05 = {**_ION_03, "AH": (None, "Level I - Base"), "AT": (None, "ION - Coupe - Red Line"), "AU": (None, "Level II - Base"),
           "AX": (None, "Level III - Base"), "AY": (None, "ION - Coupe Red Line Tuner (HMD)")}
_ION_06 = {k: v for k, v in _ION_05.items() if k not in ("AF", "AG", "AH")}
SATURN_ION = {2003: dict(_ION_03), 2004: {**_ION_03, "AY": (None, "ION Red Line Coupe")}, 2005: _ION_05, 2006: _ION_06, 2007: dict(_ION_06)}
SATURN_VUE = same(yrs(2002, 2007), {"Z2": (M, "Vue FWD Manual"), "Z3": (A, "Vue FWD Auto"), "Z4": (None, "Vue AWD 4 Cyl"),
                                    "Z5": (None, "Vue FWD 6 Cyl"), "Z6": (None, "Vue AWD 6 Cyl")})
COBALT = {
    2009: {"AJ": (M, "Cobalt Base M/T (Canada only)"), "AK": (M, "Cobalt LS M/T"), "AL": (M, "Cobalt LT M/T"),
           "AP": (M, "Cobalt Sport Coupe w/MAN TRANS"), "AR": (A, "Cobalt Base A/T (Canada only)"), "AS": (A, "Cobalt LS A/T"),
           "AT": (A, "Cobalt LT A/T")},
    2010: {"AA": (M, "Cobalt LS (Manual)"), "AB": (A, "Cobalt LS (Automatic)"), "AC": (M, "Cobalt 1LT (Manual)"),
           "AD": (A, "Cobalt 1LT (Automatic)"), "AE": (M, "Cobalt 2LT (Manual)"), "AF": (A, "Cobalt 2LT (Automatic)"),
           "AG": (None, "Cobalt SS"), "AH": (M, "Cobalt Internet Model (Manual)"), "AJ": (A, "Cobalt Internet Model (Automatic)")},
}
G5 = {
    2009: {"AJ": (M, "G5 Base M/T (Canada, Mexico only)"), "AL": (M, "G5 LS M/T"), "AN": (M, "G5 GT M/T"),
           "AR": (A, "G5 Base A/T"), "AS": (A, "G5 LS A/T"), "AT": (A, "G5 GT A/T")},
    2010: {"AA": (M, "G5 Base (Manual)"), "AB": (A, "G5 Base (Automatic)"), "AC": (M, "G5 SE (Manual)"),
           "AD": (A, "G5 SE (Automatic)"), "AE": (M, "G5 GT (Manual)"), "AF": (A, "G5 GT (Automatic)")},
}
_HHR_0809 = {"A1": (A, "HHR LS w/ auto trans"), "A2": (A, "HHR 1LT w/ auto trans"), "A3": (M, "HHR LS w/ manual trans"),
             "A4": (M, "HHR 1LT w/ manual trans"), "A5": (None, "HHR 2LT"), "A6": (A, "HHR SS w/ auto trans"),
             "A7": (M, "HHR SS w/ manual trans"), "A8": (A, "HHR LS panel van w/auto trans"),
             "A9": (M, "HHR LS panel van w/ manual trans"), "A0": (None, "HHR LT panel van")}
HHR = {2008: dict(_HHR_0809), 2009: dict(_HHR_0809),
       2010: {"AA": (A, "HHR LS (Automatic)"), "AB": (A, "HHR LT (Automatic)"), "AC": (A, "HHR 2LT (Automatic)"),
              "AD": (A, "HHR SS (Automatic)"), "AE": (M, "HHR LS (Manual)"), "AF": (M, "HHR 1LT (Manual)"),
              "AG": (M, "HHR 2LT (Manual)"), "AH": (M, "HHR SS (Manual)")},
       2011: {"AA": (A, "HHR LS (Automatic)"), "AB": (A, "HHR 1LT (Automatic)"), "AC": (A, "HHR 2LT (Automatic)"),
              "AE": (M, "HHR LS (Manual)"), "AF": (M, "HHR 1LT (Manual)"), "AG": (M, "HHR 2LT (Manual)"),
              "A9": (None, "HHR (Export - Non US, Non Canada)")}}
CTS = {
    2008: {"DM": (M, "CTS manual trans, rear wheel drive"), "DF": (A, "CTS, Auto trans, rear wheel drive"),
           "DG": (A, "CTS, Auto trans, All Wheel Drive"), "DH": (A, "CTS, Auto trans, AWD & Navigation"),
           "DJ": (A, "CTS, Auto trans, & Navigation RWD"), "DP": (M, "CTS, Manual trans, RWD, High Feature V6"),
           "DR": (A, "CTS, Auto trans, RWD, High Feature V6"), "DS": (A, "CTS, Auto trans, AWD, High Feature V6"),
           "DT": (A, "CTS, Auto trans, AWD, Navigation, High Feature V6"), "DV": (A, "CTS, Auto trans, RWD, Navigation, High Feature V6")},
    2009: {"DM": (M, "CTS M/T RWD"), "DF": (A, "CTS A/T RWD"), "DG": (A, "CTS A/T AWD"), "DH": (A, "CTS A/T AWD NAV."),
           "DJ": (A, "CTS A/T RWD NAV."), "DN": (None, "CTS-V"), "DP": (M, "CTS M/T RWD High Feature V6"), "DR": (None, "CTS RHD"),
           "DS": (A, "CTS A/T AWD High Feature V6"), "DT": (A, "CTS A/T AWD NAV. High Feature V6"),
           "DU": (A, "CTS A/T RWD High Feature V6"), "DV": (A, "CTS A/T RWD NAV. High Feature V6")},
}
SOLSTICE = {
    2008: {"MB": (M, "SOLSTICE Convertible w/ manual trans"), "MG": (A, "Solstice GXP Turbo Convertible w/ auto trans"),
           "MC": (A, "Solstice convertible w/ auto trans."), "MF": (M, "Solstice GXP Turbo convertible w/ manual trans."),
           "MK": (None, "Solstice Spring Special Edition"), "MS": (None, "Solstice Special Edition"), "MT": (None, "Solstice Special Edition Turbo")},
    2009: {"MB": (M, "Solstice Base M/T"), "MG": (M, "Solstice Turbo M/T"), "MK": (M, "Solstice Street Edition w/MAN TRANS"),
           "MN": (A, "Solstice Base A/T"), "MT": (A, "Solstice Turbo A/T"), "MZ": (M, "Solstice Street Edition w/MAN TRANS")},
    2010: {"MA": (A, "Solstice Base (Automatic)"), "MB": (A, "Solstice Turbo (Automatic)"), "MD": (M, "Solstice Base (Manual)"),
           "ME": (M, "Solstice Turbo (Manual)")},
}
SKY = {
    2008: {"MB": (M, "Sky Convertible w/ manual trans."), "MG": (A, "Sky turbo convertible w/ auto trans."),
           "MC": (A, "Sky convertible w/ auto trans."), "MF": (M, "Sky Turbo convertible w/ Manual"), "MJ": (None, "Sky Special Edition Turbo")},
    2009: {"MB": (M, "Sky Base M/T"), "MG": (M, "Sky Redline Turbo M/T"), "MC": (M, "Sky Merlot Jewel Special M/T"),
           "MD": (M, "Sky Hydro Blue Special M/T"), "MH": (M, "Sky Redline Merlot Jewel Turbo Spcl. M/T"),
           "ML": (M, "Sky Hydro Blue Spcl. Turbo M/T"), "MN": (A, "Sky Base A/T"), "MP": (A, "Sky Merlot Jewel Special A/T"),
           "MR": (A, "Sky Hydro Blue Special A/T"), "MT": (A, "Sky Redline Turbo A/T"), "MV": (A, "Sky Merlot Jewel Special Turbo A/T"),
           "MX": (A, "Sky Hydro Blue Special Turbo A/T")},
    2010: {"MB": (A, "Sky Turbo (Automatic Trans)"), "MC": (A, "Sky Preferred (Automatic Trans)"), "ME": (M, "Sky Turbo (Manual Trans)"),
           "MF": (M, "Sky Preferred (Manual Trans)")},
}
VIBE = {
    2009: {"SL": (M, "Vibe FWD M/T"), "SM": (A, "Vibe AWD A/T"), "SN": (M, "Vibe GT FWD M/T"), "SP": (A, "Vibe FWD A/T"),
           "SR": (A, "Vibe GT FWD A/T")},
    2010: {"SL": (M, "Vibe FWD (Manual)"), "SP": (A, "Vibe FWD (Automatic)"), "SM": (None, "Vibe AWD"),
           "SN": (M, "Vibe GT FWD (Manual)"), "SR": (A, "Vibe GT FWD (Automatic)")},
}
_CAMARO_1012 = {"FA": (A, "Camaro LS (Automatic)"), "FB": (A, "Camaro LT (Automatic)"), "FC": (A, "Camaro LT2 (Automatic)"),
                "FE": (M, "Camaro LS (Manual)"), "FF": (M, "Camaro LT (Manual)"), "FG": (M, "Camaro LT2 (Manual)"),
                "FJ": (A, "Camaro SS (Automatic)"), "FK": (A, "Camaro 2SS (Automatic)"), "FS": (M, "Camaro SS (Manual)"),
                "FT": (M, "Camaro 2SS (Manual)"), "F9": (None, "Camaro (Export - Non US, Non Canada)")}
CAMARO = _merge(same(yrs(2010, 2012), _CAMARO_1012), _modern("camaro", yrs(2013, 2024)))
_VETTE_1012 = {"YA": (M, "Corvette Standard 1LT (Manual)"), "YB": (M, "Corvette Preferred 2LT (Manual)"),
               "YC": (M, "Corvette Premium 3LT (Manual)"), "YD": (M, "Corvette Custom 4LT (Manual)"),
               "YE": (A, "Corvette Standard 1LT (Automatic)"), "YF": (A, "Corvette Preferred 2LT (Automatic)"),
               "YG": (A, "Corvette Premium 3LT (Automatic)"), "YH": (A, "Corvette Custom 4LT (Automatic)"),
               "YJ": (M, "Corvette Z06 Standard 1LZ (Manual)"), "YK": (M, "Corvette Z06 Premium 2LZ (Manual)"),
               "YL": (M, "Corvette Z06 Custom 3LZ (Manual)"), "YM": (M, "Corvette ZR1 Standard 1ZR (Manual)"),
               "YN": (M, "Corvette ZR1 Custom 3ZR (Manual)"), "YP": (M, "Corvette Grand Sport 1LT (Manual)"),
               "YR": (M, "Corvette Grand Sport 2LT (Manual)"), "YS": (M, "Corvette Grand Sport 3LT (Manual)"),
               "YT": (M, "Corvette Grand Sport 4LT (Manual)"), "YU": (A, "Corvette Grand Sport 1LT (Automatic)"),
               "YV": (A, "Corvette Grand Sport 2LT (Automatic)"), "YW": (A, "Corvette Grand Sport 3LT (Automatic)"),
               "YX": (A, "Corvette Grand Sport 4LT (Automatic)"), "Y9": (None, "Corvette (Export - Non US, Non Canada)")}
CORVETTE = _merge(same(yrs(2010, 2012), _VETTE_1012), _modern("corvette", yrs(2013, 2019)))
CRUZE = _merge({
    2011: {"PA": (None, "CONFLICT: 'Cruze 2LS (Canada - Automatic)' and 'Cruze 1LS (US - Manual)' share PA"),
           "PB": (M, "Cruze 2LS (Canada - Manual)"), "PC": (A, "Cruze 2LS (US - Automatic) / 1LS (Canada - Automatic)"),
           "PD": (M, "Cruze 2LS (US - Manual) / 1LS (Canada - Manual)"), "PE": (A, "Cruze 1FL (Automatic)"),
           "PF": (A, "Cruze 1LT (Automatic)"), "PG": (A, "Cruze 2LT (Automatic)"), "PH": (A, "Cruze LTZ (Automatic)"),
           "PJ": (A, "Cruze Eco (Automatic)"), "PK": (M, "Cruze Eco (Manual)"), "PL": (M, "Cruze LTZ (Manual)"),
           "P9": (None, "Cruze (Export - Non US, Non Canada)")},
    2012: {"PA": (A, "Cruze 1LS (Automatic - Canada only)"), "PB": (M, "Cruze 1LS (Manual-Canada Only)"), "PC": (A, "Cruze 2LS (Automatic)"),
           "PD": (M, "Cruze 2LS (Manual)"), "PE": (A, "Cruze 1FL (Automatic)"), "PF": (A, "Cruze 1LT (Automatic)"),
           "PG": (A, "Cruze 2LT (Automatic)"), "PH": (A, "Cruze LTZ (Automatic)"), "PJ": (A, "Cruze Eco (Automatic)"),
           "PK": (M, "Cruze Eco (Manual)"), "PL": (M, "Cruze 1LT (Manual)"), "PM": (M, "Cruze 2LT (Manual)")},
}, _modern("cruze", yrs(2013, 2019)), _modern("cruze_limited", [2016]))
SONIC = _merge({2012: {"JA": (A, "Sonic LS (Automatic)"), "JB": (M, "Sonic LS (Manual)"), "JC": (A, "Sonic LT (Automatic)"),
                       "JD": (M, "Sonic LT (Manual)"), "JE": (A, "Sonic LTZ (Automatic)"), "JF": (M, "Sonic LTZ (Manual)")}},
               _modern("sonic", yrs(2013, 2020)))
SPARK = _modern("spark", yrs(2013, 2022))
CHEVY_SS = _modern("ss", [2016, 2017])

_CHEV_CAR = ["1G1", "2G1", "3G1", "KL1"]


def _years(t: dict) -> tuple:
    return (min(t), max(t))


def _modern_cites(years) -> list:
    return [f"modern{y}" for y in years if f"modern{y}" in C]


RULES = [
    # ------------------------------------------------------------ series codes
    {"id": "saturn_s_l_series_2000_2003", "make": "Saturn", "basis": "series_code",
     "models": "Saturn S-series (SL/SL1/SL2 sedan, SC1/SC2 coupe, SW wagon; carline Z) MY2000-2002 and L-series (LS/LS1/LW1/L200/LW200; carline J) MY2000-2003",
     "wmi": ["1G8"], "years": (2000, 2003), "fixed": {4: "ZJ"}, "key": [4, 5], "tables": SATURN_SL,
     "cites": ["s2000", "s2000a", "s2001", "s2002rev", "s2002", "s2002b", "s2003", "s1991", "s1993", "s1999"],
     "evidence_gaps": "MY2001 ZF ('SL') names no transmission, so 2001 SLs get no claim; MY2000 ZN / ZJ / JU mix body styles and transmissions in one code, resolved by the body-style character (position 6: 1 coupe, 5 sedan, 8 wagon) where the filing ties the transmission to the body; JU wagons (LW1, no transmission named) get no claim.",
     "notes": "GM's 1991-1999 filings list the same Saturn series letters WITHOUT a transmission (G/H both 'SC / SL1', J/K both 'SL2'), so MY1991-1999 S-series are not ruled even though the letter pairs look like manual/automatic pairs: that would be inference."},
    {"id": "saturn_ion_series_2003_2007", "make": "Saturn", "basis": "series_code",
     "models": "Saturn ION (carline A) MY2003-2007",
     "wmi": ["1G8"], "years": (2003, 2007), "fixed": {4: "A"}, "key": [4, 5], "tables": SATURN_ION,
     "cites": ["s2003", "s2004", "s2005", "s2006", "s2007"],
     "evidence_gaps": "Red Line (AT/AY) and Level I/II/III 'Base' codes name no transmission; the Red Line is covered by the engine-code rule saturn_ion_redline_2004_2007_char8_P.",
     "notes": ""},
    {"id": "saturn_vue_series_2002_2007", "make": "Saturn", "basis": "series_code",
     "models": "Saturn VUE (WMI 5GZ, line Z) MY2002-2007; VIN positions 5-6",
     "wmi": ["5GZ"], "years": (2002, 2007), "fixed": {5: "Z"}, "key": [5, 6], "tables": SATURN_VUE,
     "cites": ["s2002b", "s2003v", "s2003", "s2004", "s2005", "s2005e", "s2006", "s2007"],
     "evidence_gaps": "AWD and V6 series (4, 5, 6) name no transmission. The MY2008-2010 VUE (WMI 3GS / 5GZ, series L1-L9/U0) names none either.",
     "notes": "Series 3 ('FWD Auto') covers the VTi CVT on 2002-2005 four-cylinder FWD cars; the claim is 'not manual'."},
    {"id": "chevrolet_cobalt_series_2009_2010", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Cobalt (carline A) MY2009-2010",
     "wmi": _CHEV_CAR, "years": (2009, 2010), "fixed": {4: "A"}, "key": [4, 5], "tables": COBALT,
     "cites": ["m2009c", "m2010", "m2010b"],
     "evidence_gaps": "MY2008 is NOT ruled: the April 2007 issue split the Cobalt series by transmission but the May 2008 4th revision replaced that with plain trims (AJ Base, AK 1LS, AL 1LT, AM Sport, AP SS) and the lot's 2008 Cobalts only carry those codes. 2010 AG (SS, 2.0 turbo) names no transmission.",
     "notes": "2009 and 2010 use different letters (2009 AK = LS M/T, 2010 AA = LS Manual); the rule is year-bound."},
    {"id": "pontiac_g5_series_2009_2010", "make": "Pontiac", "basis": "series_code",
     "models": "Pontiac G5 (carline A) MY2009-2010",
     "wmi": ["1G2", "2G2", "3G2"], "years": (2009, 2010), "fixed": {4: "A"}, "key": [4, 5], "tables": G5,
     "cites": ["m2009c", "m2010", "m2010b"],
     "evidence_gaps": "MY2008 is NOT ruled (May 2008 4th revision: AJ G5 base, AL G5 SE, AN G5 GT, no transmission).",
     "notes": ""},
    {"id": "chevrolet_hhr_series_2008_2011", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet HHR (truck/MPV VIN, line A) MY2008-2011; VIN positions 5-6",
     "wmi": ["3GN", "3GC"], "years": (2008, 2011), "fixed": {5: "A"}, "key": [5, 6], "tables": HHR,
     "cites": ["m2008", "m2009t", "m2010", "m2011", "m2011d"],
     "evidence_gaps": "MY2006-2007 HHR VINs are NOT encoded (series digit = trim: on the lots 2007 A3 is the LT 2.4L); vPIC's 'manual' for every 2007 HHR is a model-level default. A5 (2LT, 2008-2009) and A0 (LT panel) name no transmission.",
     "notes": ""},
    {"id": "cadillac_cts_series_2008_2009", "make": "Cadillac", "basis": "series_code",
     "models": "Cadillac CTS sedan (carline D) MY2008-2009",
     "wmi": ["1G6"], "years": (2008, 2009), "fixed": {4: "D"}, "key": [4, 5], "tables": CTS,
     "cites": ["m2008", "m2009c"],
     "evidence_gaps": "MY2003-2007 CTS (DM/DP/DR) and MY2010+ CTS series (Base/Luxury/Performance/Premium) name no transmission. 2009 CTS-V (DN) had both transmissions and is not ruled.",
     "notes": "STS shares carline D (2008-2009 codes C/E/W/X/Y/A/B/K/D/L/Z); those codes get no claim."},
    {"id": "pontiac_solstice_series_2008_2010", "make": "Pontiac", "basis": "series_code",
     "models": "Pontiac Solstice (carline M, WMI 1G2) MY2008-2010",
     "wmi": ["1G2"], "years": (2008, 2010), "fixed": {4: "M"}, "key": [4, 5], "tables": SOLSTICE,
     "cites": ["m2008", "m2008a", "m2009c", "m2010", "m2010b"],
     "evidence_gaps": "MY2008: the April 2007 issue had MG = GXP Turbo w/ manual and MF = GXP Turbo w/ auto; the May 2008 4th revision swaps them (MG auto, MF manual). The rule follows the 4th revision; vPIC decodes both lot 2008 MG cars as automatic, which agrees with it. MY2006-2007 Solstice (MB only) is not encoded.",
     "notes": ""},
    {"id": "saturn_sky_series_2008_2010", "make": "Saturn", "basis": "series_code",
     "models": "Saturn Sky (carline M, WMI 1G8) MY2008-2010",
     "wmi": ["1G8"], "years": (2008, 2010), "fixed": {4: "M"}, "key": [4, 5], "tables": SKY,
     "cites": ["m2008", "m2009c", "m2010", "m2010b"],
     "evidence_gaps": "MY2007 Sky (MB, MG) is not encoded.",
     "notes": ""},
    {"id": "pontiac_vibe_series_2009_2010", "make": "Pontiac", "basis": "series_code",
     "models": "Pontiac Vibe 2nd generation (WMI 5Y2, carline S) MY2009-2010",
     "wmi": ["5Y2"], "years": (2009, 2010), "fixed": {4: "S"}, "key": [4, 5], "tables": VIBE,
     "cites": ["m2009c", "m2010", "m2010b"],
     "evidence_gaps": "",
     "notes": "MY2008 (SL auto / SP manual in the 4th revision) is a separate candidate rule."},
    {"id": "pontiac_vibe_series_2008_candidate", "make": "Pontiac", "basis": "series_code", "candidate": True,
     "models": "Pontiac Vibe 1st generation (NUMMI, WMI 5Y2) MY2008",
     "wmi": ["5Y2"], "years": (2008, 2008), "fixed": {4: "S"}, "key": [4, 5],
     "tables": {2008: {"SL": (A, "Vibe FWD w/ auto trans."), "SP": (M, "Vibe FWD w/ manual trans")}},
     "cites": ["m2008", "m2008a", "nummi2003", "nummi2004"],
     "evidence_gaps": "GM's MY2008 tables say SL = 'Vibe FWD w/ auto trans.', but NUMMI built the 2003-2008 Vibe and its own filings use SL for every base car ('Vibe Base'); no MY2008 NUMMI filing is in MID and every lot 2008 Vibe is SL (vPIC: 'Base', no transmission). Not counted.",
     "notes": "Candidate: the claim would only mark cars as not manual."},
    {"id": "chevrolet_camaro_series_2010_2024", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Camaro (carline F) MY2010-2024",
     "wmi": ["2G1", "1G1"], "years": _years(CAMARO), "fixed": {4: "F"}, "key": [4, 5], "tables": CAMARO,
     "cites": ["m2010", "m2010b", "m2011", "m2012"] + _modern_cites(yrs(2013, 2024)),
     "evidence_gaps": "Letters change meaning in MY2015 and MY2016 (2014 FA = 2LS Automatic, 2015 FA = LS Manual); the rule uses each year's table.",
     "notes": "Chevrolet SS (WMI 6G3) also uses carline F; it has its own rule."},
    {"id": "chevrolet_corvette_series_2010_2019", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Corvette C6/C7 (carline Y) MY2010-2019",
     "wmi": ["1G1"], "years": _years(CORVETTE), "fixed": {4: "Y"}, "key": [4, 5], "tables": CORVETTE,
     "cites": ["m2010", "m2010b", "m2011", "m2012"] + _modern_cites(yrs(2013, 2019)),
     "evidence_gaps": "MY2005-2009 Corvette (series YY, 'CORVETTE') and MY2020+ C8 (dual-clutch only; series name no transmission) are not ruled.",
     "notes": ""},
    {"id": "chevrolet_cruze_series_2011_2019", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Cruze (carline P, MY2011-2016 incl. 2016 Cruze Limited) and new Cruze (carline B, MY2016-2019)",
     "wmi": _CHEV_CAR, "years": _years(CRUZE), "fixed": {4: "PB"}, "key": [4, 5], "tables": CRUZE,
     "cites": ["m2011", "m2011d", "m2012", "m2013d"] + _modern_cites(yrs(2013, 2019)),
     "evidence_gaps": "MY2011 PA is defined twice with opposite transmissions (US 1LS manual, Canada 2LS automatic), so it gets no claim. Draft tables were changed before production (Dec-2009 MY2011 issue, Jan-2012 MY2013 issue); the rule uses the last issue for each year, which is also what the lot cars follow.",
     "notes": ""},
    {"id": "chevrolet_sonic_series_2012_2020", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Sonic (carline J) MY2012-2020",
     "wmi": _CHEV_CAR, "years": _years(SONIC), "fixed": {4: "J"}, "key": [4, 5], "tables": SONIC,
     "cites": ["m2012"] + _modern_cites(yrs(2013, 2020)),
     "evidence_gaps": "Letters change meaning in MY2017 (2016 JA = LS Automatic, 2017 JA = LS Manual).",
     "notes": ""},
    {"id": "chevrolet_spark_series_2013_2022", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet Spark (carline C, WMI KL8) MY2013-2022",
     "wmi": ["KL8"], "years": _years(SPARK), "fixed": {4: "C"}, "key": [4, 5], "tables": SPARK,
     "cites": _modern_cites(yrs(2013, 2022)),
     "evidence_gaps": "Spark EV (CL...) names no transmission.",
     "notes": ""},
    {"id": "chevrolet_ss_series_2016_2017", "make": "Chevrolet", "basis": "series_code",
     "models": "Chevrolet SS sedan (WMI 6G3, carline F) MY2016-2017",
     "wmi": ["6G3"], "years": (2016, 2017), "fixed": {4: "F"}, "key": [4, 5], "tables": CHEVY_SS,
     "cites": _modern_cites([2016, 2017]),
     "evidence_gaps": "MY2014-2015 SS (F1 only) names no transmission (the manual arrived for 2015 on the same code).",
     "notes": ""},
    # ------------------------------------------------------------ engine / sub-model codes + EPA
    {"id": "cadillac_cts_v_2004_2007_series_DN", "make": "Cadillac", "basis": "series_code_plus_epa",
     "models": "Cadillac CTS-V 1st generation (series DN) MY2004-2007",
     "wmi": ["1G6"], "years": (2004, 2007), "fixed": {4: "D", 5: "N"}, "key": [4, 5],
     "tables": same(yrs(2004, 2007), {"DN": (M, "CTS-V (5.7L LS6 MY2004-2005, 6.0L LS2 MY2006-2007): sold only with the 6-speed manual")}),
     "cites": ["s2004", "s2005", "s2006", "s2007", "web_ctsv"],
     "epa": [{"years": yrs(2004, 2007), "make": "Cadillac", "model": r"^CTS-V$", "displ": None, "claim": M}],
     "evidence_gaps": "The filing defines DN = CTS-V but names no transmission; the transmission fact is EPA's (only 'Manual 6-spd' rows for 2004-2007 CTS-V).",
     "notes": "From MY2009 the CTS-V (DN) had an automatic too; not ruled."},
    {"id": "chevrolet_cobalt_ss_sc_2005_2007_char8_P", "make": "Chevrolet", "basis": "engine_code",
     "models": "Chevrolet Cobalt SS Supercharged (carline A, engine P = 2.0L LSJ supercharged) MY2005-2007",
     "wmi": _CHEV_CAR, "years": (2005, 2007), "fixed": {4: "A"}, "key": [8],
     "tables": same(yrs(2005, 2007), {"P": (M, "2.0L L4 MFI DOHC supercharged (LSJ): sold only with the 5-speed manual")}),
     "cites": ["s2004", "s2005e", "s2006", "s2007", "web_cobalt_ss"],
     "epa": [{"years": yrs(2005, 2007), "make": "Chevrolet", "model": r"^Cobalt", "displ": 2.0, "charger": "S", "claim": M}],
     "evidence_gaps": "Engine code P = LSJ comes from GM's MY2004-2007 engine tables; the transmission fact is EPA's.",
     "notes": "The 2.0L turbo LNF (2008-2010 Cobalt SS, code X) was also manual-only in the Cobalt but shared code X with the HHR SS and Solstice/Sky turbo, which had automatics; no lot car needs it (2009 AP and 2010 Cobalts are series-coded)."},
    {"id": "saturn_ion_redline_2004_2007_char8_P", "make": "Saturn", "basis": "engine_code",
     "models": "Saturn ION Red Line (carline A, engine P = 2.0L LSJ supercharged) MY2004-2007",
     "wmi": ["1G8"], "years": (2004, 2007), "fixed": {4: "A"}, "key": [8],
     "tables": same(yrs(2004, 2007), {"P": (M, "2.0L L4 MFI DOHC supercharged (LSJ): ION Red Line, sold only with the 5-speed manual")}),
     "cites": ["s2004", "s2005", "s2006", "s2007", "web_ion_redline"],
     "epa": [{"years": yrs(2004, 2007), "make": "Saturn", "model": r"^Ion", "displ": 2.0, "charger": "S", "claim": M}],
     "evidence_gaps": "",
     "notes": "Fires only when the ION series code itself names no transmission (AT/AY Red Line)."},
    {"id": "pontiac_vibe_gt_2003_2006_series_SN_char8_L", "make": "Pontiac", "basis": "engine_code", "candidate": True,
     "models": "Pontiac Vibe GT 1st generation (series SN, engine L = 2ZZ-GE) MY2003-2006",
     "wmi": ["5Y2"], "years": (2003, 2006), "fixed": {4: "S", 5: "N"}, "key": [8],
     "tables": same(yrs(2003, 2006), {"L": (M, "Vibe GT (Opt VHP), 2ZZ-GE 1.8L (LNK): sold only with the 6-speed manual")}),
     "cites": ["nummi2003", "nummi2004", "web_vibe_gt"],
     "epa": [{"years": yrs(2003, 2006), "make": "Pontiac", "model": r"^Vibe$", "displ": 1.8, "eng": "SPORTS", "claim": M}],
     "evidence_gaps": "CANDIDATE: EPA has a 2003 Vibe 1.8 'SPORTS' (2ZZ) row with 'Automatic 4-spd' (id 18777) next to the 6-speed manual, and Autoblog says an automatic GT was added later; 2004-2006 EPA rows are manual-only but the conflict is not resolved, so no year is counted. NUMMI's MY2005-2006 Vibe filings are not in MID; SN = Vibe GT and L = 2ZZ-GE are read from the MY2003-2004 filings and vPIC decodes every lot 2005-2006 SN car as 'GT (Opt VHP)' with engine L.",
     "notes": "EPA lists the GT ('SPORTS' engine descriptor) only as 'Manual 6-spd' for 2003-2006."},
    {"id": "chevrolet_metro_10_1999_2000_char8_6", "make": "Chevrolet", "basis": "engine_code",
     "models": "Chevrolet Metro (CAMI, WMI 2C1, carline M) with the 1.0L 3-cylinder, MY1999-2000",
     "wmi": ["2C1"], "years": (1999, 2000), "fixed": {4: "M"}, "key": [8],
     "tables": same(yrs(1999, 2000), {"6": (M, "1.0L L3 TBI (Suzuki, LP2): sold only with the 5-speed manual")}),
     "cites": ["e1999", "e2000", "web_metro"],
     "epa": [{"years": yrs(1999, 2000), "make": "Chevrolet", "model": r"^Metro$", "displ": 1.0, "claim": M}],
     "evidence_gaps": "",
     "notes": "The 1.3L (code 2) had an automatic; not ruled."},
    {"id": "geo_chevrolet_metro_10_1995_1998_char8_6_candidate", "make": "Geo", "basis": "engine_code", "candidate": True,
     "models": "Geo Metro (MY1995-1997) and Chevrolet Metro (MY1998), WMI 2C1, 1.0L 3-cylinder",
     "wmi": ["2C1"], "years": (1995, 1998), "fixed": {4: "M"}, "key": [8],
     "tables": same(yrs(1995, 1998), {"6": (M, "1.0L L3 (LP2) per vPIC")}),
     "cites": ["e1999"],
     "epa": [{"years": yrs(1995, 1998), "make": None, "model": r"^Metro$", "displ": 1.0, "claim": M}],
     "evidence_gaps": "The MY1995-1998 GM engine tables in MID are scans whose OCR lost the code column (LP2 is listed, its code is not readable), so code 6 = 1.0L rests on vPIC for these years. Not counted.",
     "notes": "Geo is a GM brand no other worklist covers."},
]

ANSWER = {
    "Chevrolet": ("ENCODED for specific lines and years only, through the line/series code (positions 4-5; trucks/MPVs 5-6): Cobalt MY2009-2010, HHR MY2008-2011, "
                  "Camaro MY2010-2024, Corvette MY2010-2019, Cruze MY2011-2019 (and 2016 Cruze Limited), Sonic MY2012-2020, Spark MY2013-2022, SS MY2016-2017. "
                  "NOT ENCODED for every other Chevrolet line and year (Malibu, Impala, Cavalier, Aveo, Equinox, Silverado, S-10, Colorado, Tahoe ..., Corvette before 2010 and C8, "
                  "Cobalt 2005-2008, HHR 2006-2007): GM's VIN has no transmission position (4-5 line/series or GVWR/line, 6 body or series, 7 restraint or body, 8 engine). "
                  "Manual-only engines in uncoded years: Cobalt SS supercharged 2005-2007 (engine P), Metro 1.0 1999-2000 (engine 6)."),
    "GMC": "NOT ENCODED. No GMC line/series description in any filing read names a transmission, and no GMC engine code on the lots is manual-only (Sonoma/Canyon 4-cylinders and the full-size trucks had both or automatic only).",
    "Pontiac": ("ENCODED through the series code for G5 MY2009-2010, Solstice MY2008-2010 and Vibe MY2009-2010 (MY2008 Vibe is a candidate). NOT ENCODED otherwise "
                "(G6, Grand Am, Grand Prix, Sunfire, Firebird, Bonneville, Aztek, Montana, G8 ...; G5 2007-2008; Solstice 2006-2007). Vibe GT 2003-2006 (series SN + engine L, NUMMI filings) is manual-only."),
    "Saturn": ("ENCODED through the series code for S-series and L-series MY2000-2003 (except MY2001 SL), ION MY2003-2007, VUE MY2002-2007 (FWD 4-cylinder only), Sky MY2008-2010. "
               "NOT ENCODED for MY1991-1999 S-series (filings list the same letters without a transmission), Aura, Outlook, Relay, Astra, VUE 2008-2010, Sky 2007. "
               "ION Red Line 2004-2007 (engine P) is manual-only."),
    "Buick": "NOT ENCODED. No Buick line/series description names a transmission in any filing read (MY1985-2027); no Buick on the lots had a manual-only engine (Regal GS 2012-2013 and Verano Turbo had both, Cascada/Encore automatic).",
    "Cadillac": ("ENCODED through the series code for CTS MY2008-2009 (DM/DP manual) and, outside the lots' range, CT4-V / CT5-V Blackwing (MY2022+ 'Manual' series codes). "
                 "NOT ENCODED for every other Cadillac line and year (CTS 2003-2007 and 2010+, ATS, STS, DTS, DeVille, SRX, Escalade ...). CTS-V 2004-2007 (series DN) was manual-only (EPA)."),
    "Oldsmobile": "NOT ENCODED (GM scheme, positions 4-5 line/series with no transmission). No Oldsmobile engine code on the lots is manual-only: the 1990-1993 Calais/Achieva Quad 4 W41 and HO cars are absent from the lots, and Alero/Achieva/Cutlass four-cylinders had both transmissions.",
    "Hummer": "NOT ENCODED. H3/H3T series codes (N1-N6: base, Adventure, Luxury, H3-X, Alpha) name no transmission, and the H3's 3.5/3.7L five-cylinders had both a manual and an automatic; H1/H2 (AM General / GM) were automatic only. No Hummer rule.",
    "Geo": "NOT ENCODED (GM/CAMI scheme). Metro 1.0 (engine 6) was manual-only; MY1995-1998 is a candidate rule because the scanned GM engine tables for those years are not legible.",
}

VIN_SCHEME = {
    "passenger_car": "1-3 WMI (1G1/2G1/3G1/KL1 Chevrolet, 1G2/2G2/5Y2 Pontiac, 1G3 Oldsmobile, 1G4 Buick, 1G6 Cadillac, 1G8 Saturn, 6G3 Chevrolet SS), 4-5 carline + series, 6 body style, 7 restraint, 8 engine (RPO-mapped code), 9 check digit, 10 model year, 11 plant, 12-17 sequence.",
    "truck_mpv": "1-3 WMI (1GC/1GN/3GN ... Chevrolet, 1GT/1GK GMC, 5GZ/3GS Saturn VUE, 5GR/5GT Hummer), 4 GVWR/brake (MY2010+: GVWR/brake/body), 5 line/chassis, 6 series, 7 body type (MY2010+: restraint), 8 engine, 9 check digit, 10 model year.",
    "where_transmission_appears": "Only inside the line/series description of specific lines and years (cars: positions 4-5; trucks/MPVs: 5-6). There is no transmission position anywhere in GM's scheme.",
    "nummi_vibe_2003_2006": "NUMMI's own filings (WMI 5Y2): 4-5 carline & series (SL base, SM AWD, SN GT), 8 engine (8 = 1ZZ-FE, L = 2ZZ-GE).",
}

NOT_RULED = [
    {"what": "Saturn SL (ZF) MY2001", "why": "MY2001 table says only 'SL' (MY2000 'SL MANUAL', MY2002 'SL Manual'); vPIC decodes all five lot 2001 SLs as manual (uniform cell). Left unlabelled: the filing for that year names no transmission."},
    {"what": "Chevrolet HHR MY2006-2007", "why": "Series digits are trims (2007 A1 LS, A2 LT, A3 LT 2.4L on the lots). vPIC's uniform 'manual' for 2007 HHR is a default; keep the scraper's VPIC_TRANS_DEFAULT_CELLS drop."},
    {"what": "Chevrolet Cobalt and Pontiac G5 MY2008", "why": "The May 2008 4th revision has no transmission in the series. vPIC still decodes them with the superseded April 2007 table (see hub_findings)."},
    {"what": "Chevrolet Cruze MY2011 code PA", "why": "Defined as 1LS US Manual and 2LS Canada Automatic in the same table."},
    {"what": "Corvette C8 MY2020+", "why": "Dual-clutch only; series codes name no transmission (they would only ever be 'not manual')."},
    {"what": "Cadillac CT4-V / CT5-V Blackwing MY2022+", "why": "Filings define '(Manual)' Blackwing series codes (e.g. 'D6: Cadillac CT4 V-Blackwing (Manual)', 'D2/D3: Cadillac CT5 V-Blackwing (Manual) RWD'), but no lot car is MY2022+ CT4/CT5, so no rule was built."},
    {"what": "Cobalt SS turbo (LNF, engine X) 2008", "why": "Code X is shared with HHR SS and Solstice GXP / Sky Red Line, which had automatics; 2008 Cobalt series names no transmission."},
    {"what": "Hummer H3, GMC Canyon/Sonoma, Chevrolet Colorado/S-10, full-size trucks", "why": "No series names a transmission and every engine had both transmissions or automatic only."},
]

RULE_STATUS_NOTE = {
    "keep": "at least 20 checkable ground-truth cars and agreement >= 0.995",
    "low_sample": "fewer than 20 checkable ground-truth cars; kept because the code meaning comes from GM's (or NUMMI's) own Part 565 VIN filing (and, for engine/sub-model rules, EPA lists only that transmission)",
    "drop": "agreement below 0.995 on at least 20 checkable cars",
    "candidate": "evidence incomplete (see evidence_gaps); not counted",
}

VALIDATION_METHOD = (
    "Every lot car with a rule WMI, a 17-character VIN and a valid check digit is classified. The model year comes from VIN character 10 (the "
    "listing year only picks the 30-year cycle and must be within 2 years). A rule fires only when the VIN matches its WMI, years and fixed "
    "characters and its code (series characters, or the engine character for engine rules) has a transmission in that YEAR's table; codes whose "
    "description names no transmission give no claim, and the next rule in scope is tried. Ground truth = scraper/manual_detect/ground_truth.jsonl; "
    "uniformCell lines are unlabelled, speeds-only lines are excluded, the rest are checkable: agree means (truth is manual) == (rule says manual). "
    "GM's VIN ground truth is vPIC, which is built from these same filings (partly circular): it checks that the right year table was read, not the "
    "filing itself. Independent checks: EPA rows per engine/sub-model rule (every rule year must have rows and all must be the claimed class), and a "
    "per-car EPA union check (year, make, feed/vPIC model, vPIC displacement). Status: candidate (not counted) when flagged or when the EPA "
    "sole-offering check fails; drop when >= 20 checkable and agreement < 0.995; low_sample when < 20 checkable; keep otherwise. newly_confirmed_manual "
    "counts lot cars with no published transmission (vehicle_extras trans empty) that a keep or low_sample rule calls manual."
)


def rule_regex(r: dict) -> str:
    """Regex for the rule's MANUAL codes (union over years): WMI, fixed characters, code characters and year codes."""
    man = defaultdict(set)
    for y, t in r["tables"].items():
        for code, e in t.items():
            if e[0] == M or (e[0] == BY6 and any(v[0] == M for v in e[1].values())):
                man[code].add(y)
    if not man:
        return ""
    alts = []
    for code, ys in sorted(man.items()):
        chars = ["."] * 17
        for p, allowed in r["fixed"].items():
            chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
        for i, p in enumerate(r["key"]):
            chars[p - 1] = code[i]
        e = r["tables"][min(ys)][code]
        if e[0] == BY6:
            ok = "".join(k for k, v in e[1].items() if v[0] == M)
            chars[5] = "[" + ok + "]" if len(ok) > 1 else ok
        yc = year_chars(ys)
        chars[9] = "[" + yc + "]" if len(yc) > 1 else yc
        alts.append("".join(chars[3:]))
    return "^(" + "|".join(r["wmi"]) + ")(" + "|".join(alts) + ")"


def classify(vin: str, year: int):
    """-> (rule, claim, code, meaning) for the first rule with a claim; ('no_claim', rule, code, meaning) when every
    rule in scope has the code without a transmission; ('unknown_code', rule) when in scope but not in any table."""
    scoped, noclaim = None, None
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        scoped = scoped or r
        code = "".join(vin[p - 1] for p in r["key"])
        e = (r["tables"].get(year) or {}).get(code)
        if e is None:
            continue
        claim, meaning = e
        if claim == BY6:
            sub = meaning.get(vin[5])
            claim, meaning = sub if sub else (None, f"{code} with body character {vin[5]}: no transmission named")
        if claim in (M, A):
            return (r, claim, code, meaning)
        noclaim = noclaim or (r, code, meaning)
    if noclaim:
        return ("no_claim",) + noclaim
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

    def rule_rows(self, spec: dict) -> list[dict]:
        out = []
        for r in self.rows:
            if spec.get("make") and r["make"] != spec["make"]:
                continue
            if int(r["year"]) not in spec["years"] or not re.search(spec["model"], r["model"]):
                continue
            if spec.get("displ") is not None and (not r["displ"] or abs(float(r["displ"]) - spec["displ"]) > 0.051):
                continue
            ch = spec.get("charger")
            if ch is not None and (r["tCharger"].strip() if ch == "T" else r["sCharger"].strip() if ch == "S" else "") != ch:
                continue
            if spec.get("eng") and spec["eng"] not in (r.get("eng_dscr") or ""):
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
            same_d = {i for i in hits if self.rows[i]["displ"] and abs(float(self.rows[i]["displ"]) - displ) < 0.051}
            if same_d:
                hits = same_d
        return {ep.trany_class(self.rows[i]["trany"]) for i in hits}


def parse_displ(engine: str) -> float | None:
    m = re.match(r"\s*(\d+(?:\.\d+)?)L", engine or "")
    return float(m.group(1)) if m else None


def _title(s: str) -> str:
    return s.title() if s and s.isupper() else s


def _fmt_table(r: dict) -> dict:
    """{claim: {code: 'meaning (MY...)'}} merged over years, plus the raw per-year table."""
    byc = {M: defaultdict(list), A: defaultdict(list)}
    for y, t in sorted(r["tables"].items()):
        for code, e in t.items():
            subs = [(code, e)] if e[0] != BY6 else [(f"{code}+pos6={k}", v) for k, v in e[1].items()]
            for c2, (cl, meaning) in subs:
                if cl in (M, A):
                    byc[cl][(c2, meaning)].append(y)

    def span(ys):
        ys = sorted(ys)
        return f"MY{ys[0]}" if len(ys) == 1 else (f"MY{ys[0]}-{ys[-1]}" if ys == list(range(ys[0], ys[-1] + 1)) else "MY" + ", ".join(map(str, ys)))
    out = {}
    for cl in (M, A):
        d = defaultdict(list)
        for (code, meaning), ys in byc[cl].items():
            d[code].append(f"{meaning} ({span(ys)})")
        out[cl] = {c: "; ".join(v) for c, v in sorted(d.items())}
    per_year = {str(y): {code: (e[0] if e[0] != BY6 else {k: v[0] for k, v in e[1].items()}) for code, e in sorted(t.items())}
                for y, t in sorted(r["tables"].items())}
    return {"manual_codes": out[M], "automatic_codes": out[A], "per_year": per_year}


# ---------------------------------------------------------------------------
def main() -> int:
    inv = json.loads((DATA / "inventory_live.json").read_text())
    extras_doc = json.loads((DATA / "vehicle_extras.json").read_text())
    extras = extras_doc["extras"]
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
    noclaim_codes = defaultdict(Counter)
    unknown_codes = defaultdict(Counter)
    scan = Counter()
    make_cov = {m: Counter() for m in MAKES}
    gt_cov = {m: Counter() for m in MAKES}
    newly_manual, newly_auto, conflicts = [], [], []
    vpic_2008 = []

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
        raw = cache.get(vin) if len(vin) == 17 else None
        dec = raw if isinstance(raw, dict) else None
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
        # hub finding: MY2008 Cobalt / G5 published vPIC labels (superseded April-2007 table)
        if y == 2008 and vin[:3] in ("1G1", "1G2") and vin[3] == "A" and pub:
            vpic_2008.append({"id": vid, "vin": vin, "make": make, "model": model, "series": vin[3:5], "published_trans": pub,
                              "transSrc": ex[4] or "vin", "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        res = classify(vin, y)
        if res is None:
            scan["out_of_rule_scope"] += 1
            continue
        if res[0] == "unknown_code":
            r = res[1]
            unknown_codes[r["id"]][f"{y}:{''.join(vin[p - 1] for p in r['key'])}"] += 1
            scan["in_scope_code_not_in_table"] += 1
            continue
        if res[0] == "no_claim":
            r = res[1]
            noclaim_codes[r["id"]][f"{y}:{res[2]}: {res[3]}"] += 1
            scan["in_scope_code_names_no_transmission"] += 1
            continue
        r, claim, code, meaning = res
        rid = r["id"]
        scan["covered"] += 1
        st = per_rule[rid]
        st[claim]["in_scope"] += 1
        codes_seen[rid][f"{y} {code} {claim[0].upper()}"] += 1
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
                if g.get("source") == "listing":
                    st[claim]["checkable_listing_source"] += 1
                if not ok and len(examples[rid]["disagree"]) < 10:
                    examples[rid]["disagree"].append({"id": vid, "vin": vin, "year": y, "model": model, "code": code,
                                                      "claim": claim, "ground_truth": g.get("trans"), "source": g.get("source")})
            else:
                st[claim]["speeds_only_excluded"] += 1
        if epa.ok:
            emake = make if make in MAKES else r["make"]
            cls = epa.classes(y, emake, [model, _title((dec or {}).get("model", ""))], displ)
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
                              "rule_status": "", "code": f"{code}: {meaning}", "rule_claim": claim,
                              "published_trans": pub, "transSrc": ex[4] or "vin",
                              "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        if not pub:
            why = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if "transmission" in dec and not dec.get("transmission")
                                                              else "vpic_trans_dropped_by_scraper" if dec.get("transmission") else "cache_old_schema")
            st[claim]["no_trans_info"] += 1
            st[claim][f"no_trans_info_{why}"] += 1
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"{code}: {meaning}", "why_no_trans": why, "yard": yard}
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
        for spec in r.get("epa", []):
            rows = epa.rule_rows(spec) if epa.ok else []
            classes = sorted({ep.trany_class(x["trany"]) for x in rows})
            years_found = sorted({int(x["year"]) for x in rows})
            sole = bool(rows) and (classes == ["manual"] if spec["claim"] == M else "manual" not in classes)
            missing = sorted(set(spec["years"]) - set(years_found))
            epa_ok = epa_ok and sole and not missing
            epa_rows.append({"claim": spec["claim"], "filter": {k: v for k, v in spec.items() if k != "claim"},
                             "rows": [f"{x['year']} id {x['id']} {x['make']} '{x['model']}' {x['displ']}L {x['trany']}"
                                      + (" supercharged" if x["sCharger"].strip() else "") + (" turbo" if x["tCharger"].strip() else "")
                                      + (f" [{x['eng_dscr']}]" if x.get("eng_dscr") else "") for x in rows],
                             "classes": classes, "sole_offering_holds": sole, "years_without_epa_row": missing})
        if r.get("candidate") or not epa_ok:
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
                    "checkable_positives_manual": s["checkable_gt_manual"],
                    "checkable_from_listing_text": s["checkable_listing_source"],
                    "uniform_cell_lines_excluded": s["uniform_cell_excluded"],
                    "uniform_cell_lines_that_would_agree": s["uniform_cell_would_agree"],
                    "ground_truth_speeds_only_excluded": s["speeds_only_excluded"],
                    "epa_crosscheck_per_car": {"consistent": s["epa_consistent"], "conflict": s["epa_conflict"],
                                               "no_epa_match": s["epa_no_match"]},
                    "cars_without_trans_info": s["no_trans_info"],
                    "cars_without_trans_info_by_reason": {k[len("no_trans_info_"):]: v for k, v in s.items()
                                                          if k.startswith("no_trans_info_")}}

        tbl = _fmt_table(r)
        epa_cite = ([{"url": EPA_URL, "doc": C["epa"]["doc"],
                      "says": "; ".join(f"{e['claim']}: " + (", ".join(e["rows"]) or "no row") for e in epa_rows)}]
                    if epa_rows else [])
        pos_txt = "positions " + "-".join(str(p) for p in r["key"]) if len(r["key"]) > 1 else f"position {r['key'][0]}"
        out_rules.append({
            "id": rid, "make": r["make"], "status": status, "basis": r["basis"],
            "status_reason": RULE_STATUS_NOTE[status] + ("" if epa_ok or r.get("candidate") else " (EPA rows do not show a sole offering for every rule year)"),
            "notes": r["notes"],
            "claim": "manual for the manual codes; automatic (not manual) for the automatic codes" if tbl["automatic_codes"] else "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + (", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())) or "none"),
                                     f"decision characters: VIN {pos_txt}, looked up in that model year's table only"]},
            "vin_condition": {"positions": r["key"], "manual_codes": tbl["manual_codes"], "automatic_codes": tbl["automatic_codes"],
                              "per_year_table": tbl["per_year"]},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"]] + epa_cite,
            "evidence_gaps": r["evidence_gaps"],
            "validation": {
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": tot["checkable_gt_manual"],
                "epa_rows": epa_rows, "epa_sole_offering_holds": epa_ok if r.get("epa") else None,
                "manual_codes": side(M), "automatic_codes": side(A),
                "disagree_examples": examples[rid]["disagree"],
                "epa_conflict_examples": examples[rid]["epa_conflict"],
                "codes_seen_on_lots": dict(sorted(codes_seen[rid].items())),
                "in_scope_codes_naming_no_transmission": dict(noclaim_codes[rid].most_common()),
                "in_scope_codes_not_in_table": dict(unknown_codes[rid].most_common()),
            },
            "newly_confirmed_manual": st[M]["no_trans_info"],
            "newly_labelled_non_manual": st[A]["no_trans_info"],
        })

    status_by_id = {x["id"]: x["status"] for x in out_rules}
    for c in conflicts:
        c["rule_status"] = status_by_id[c["rule"]]
    keep_ids = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    nm_conf = [c for c in newly_manual if c["rule"] in keep_ids]
    nm_cand = [c for c in newly_manual if c["rule"] not in keep_ids]
    for mk in MAKES:
        make_cov[mk]["newly_confirmed_manual_counted"] = sum(1 for c in nm_conf if c["make"] == mk)
        make_cov[mk]["newly_confirmed_manual_candidate_rules_only"] = sum(1 for c in nm_cand if c["make"] == mk)
        make_cov[mk]["newly_labelled_non_manual_counted"] = sum(1 for c in newly_auto if c["make"] == mk and c["rule"] in keep_ids)

    def tally(cl, key):
        return sum(x["validation"][cl][key] for x in out_rules if x["id"] in keep_ids)
    man_chk, man_agr = tally("manual_codes", "checkable_ground_truth"), tally("manual_codes", "agree")
    aut_chk, aut_agr = tally("automatic_codes", "checkable_ground_truth"), tally("automatic_codes", "agree")
    man_pos = tally("manual_codes", "checkable_positives_manual")

    v08 = Counter((c["model"], c["series"], c["published_trans"]) for c in vpic_2008)
    hub_findings = [
        {"finding": "vPIC decodes MY2008 Cobalt / G5 with GM's superseded April-2007 table",
         "evidence": ("The April 2007 MY2008 issue (ORG3532) split Cobalt and G5 series by transmission; GM's May 2008 4th revision (ORG21681) "
                      "replaced it with plain trims (Cobalt AJ Base, AK 1LS, AL 1LT, AM Sport, AP SS; G5 AJ base, AL SE, AN GT) and every lot "
                      "2008 Cobalt/G5 carries only those codes (no AN/AR/AT/AW/AU Cobalts at all, which the April table would need for every "
                      "manual). vPIC nevertheless returns the April meanings: 2008 Cobalt AK 'Automatic', AL/AM 'Automated Manual (AMT)', "
                      "G5 AL 'Automatic' and G5 AN 'Manual' (GT). The G5 GT had both transmissions, so the 'Manual' badge on 2008 G5 AN "
                      "cars is not evidence about those cars."),
         "published_labels": [{"model": k[0], "series": k[1], "published_trans": k[2], "cars": n} for k, n in sorted(v08.items())],
         "suggested_action": "Hub decision (scraper change, not made here): add MY2008 Cobalt and G5 (and, for consistency, vPIC 'AMT' on 2008 Cobalts) to VPIC_TRANS_DEFAULT_CELLS-style drops so the 2008 G5 AN cars lose the Manual badge."},
        {"finding": "Two of the scraper's dropped 'uniform manual' cells are true manuals per GM's filings",
         "evidence": ("2002 Saturn VUE series 2 is 'FWD Manual' in every MY2002-2007 GM filing (C3g), and 2002 Saturn SL (ZF) is 'SL Manual' "
                      "in the latest MY2002 issue (01-022-N11B-9012). The 2001 SL (ZF = 'SL' in MY2001) and the 2007 HHR (series = trim) "
                      "are not confirmed. The series rules here relabel the 2002 VUE and 2002 SL cars as manual from the VIN itself "
                      "(counted in newly_confirmed_manual)."),
         "suggested_action": "Integration: apply saturn_vue_series_2002_2007 and saturn_s_l_series_2000_2003 ahead of VPIC_TRANS_DEFAULT_CELLS; keep the drops for 2001 SL and 2007 HHR."},
        {"finding": "GM reuses series letters with different transmission meanings from year to year and between draft and final issues",
         "evidence": ("2008 Solstice/Sky MG = turbo AUTO, 2009 MG = turbo M/T, 2010 MB = Solstice Turbo (Automatic); 2011 Cruze PF = 1LT "
                      "(Automatic) in the January 2011 issue but 1LT (Manual) in the December 2009 draft; MY2013 Cruze letters changed "
                      "between the January and April 2012 issues; MY2011 Cruze PA means 1LS US Manual AND 2LS Canada Automatic. "
                      "Any integration must look codes up per model year and use the last issue for that year."),
         "suggested_action": "none beyond per-year tables (as here)"},
    ]

    doc = {
        "worklist": "vin_rules_5",
        "makes": [m for m in MAKES if m != "Geo"],
        "makes_note": "Geo (GM/CAMI Metro) is included because no other worklist covers it.",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/vin_rules_5.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json (" + str(inv.get("scrapedAt") or inv.get("generatedAt") or "") + ")",
                   "vehicle_extras": "docs/data/vehicle_extras.json (scrapedAt " + str(extras_doc.get("scrapedAt")) + "; reflects the scraper's VPIC_TRANS_DEFAULT_CELLS drop, so 2007 HHR, 2001-2002 SL and 2002 VUE publish no transmission)",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (built 2026-11-05 before that drop; uniformCell lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA checks skipped, every engine-code rule falls to candidate)"),
                   "mid_filings": ("243 Part 565 files MID lists for the filers General Motors (MY1984-2027), New United Motor (NUMMI), GM Daewoo, "
                                   "AM General and CAMI, downloaded 2026-11-05 (search API AjaxHandler565TopLevel + displayfile). MY2013+ GM filings "
                                   "have a text layer (tables parsed from it); MY1985-2012 scans were OCR'd and every table cited was read as a page "
                                   "image. MID holds no Saturn Corporation or Hummer filings (GM filed for both) and no MY2005-2008 NUMMI Vibe filing."),
                   "web_sources": "engine/sub-model rules also cite one independent text source each (read through web-search result text; WebFetch not used); series-code rules rest on the filings alone"},
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
            "newly_confirmed_manual_by_reason": dict(Counter(c["why_no_trans"] for c in nm_conf)),
            "newly_labelled_non_manual_keep_and_low_sample_rules": len([c for c in newly_auto if c["rule"] in keep_ids]),
            "ground_truth_precision_manual_claims": {"checkable": man_chk, "agree": man_agr,
                                                     "precision": round(man_agr / man_chk, 4) if man_chk else None},
            "ground_truth_agreement_automatic_claims": {"checkable": aut_chk, "agree": aut_agr,
                                                        "agreement": round(aut_agr / aut_chk, 4) if aut_chk else None},
            "ground_truth_recall_of_checkable_manuals_in_scope": man_pos,
            "published_labels_contradicting_a_rule": len(conflicts),
            "published_labels_contradicting_a_counted_rule": sum(1 for c in conflicts if c["rule"] in keep_ids),
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
        "hub_findings": hub_findings,
        "published_vpic_labels_MY2008_cobalt_g5": vpic_2008,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("by reason:", s["newly_confirmed_manual_by_reason"])
    print("non-manual labels (keep+low_sample):", s["newly_labelled_non_manual_keep_and_low_sample_rules"])
    print("manual-claim precision:", s["ground_truth_precision_manual_claims"], " auto-claim agreement:", s["ground_truth_agreement_automatic_claims"])
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"], "(counted rules:", s["published_labels_contradicting_a_counted_rule"], ")")
    print("scan:", s["scan"])
    for x in out_rules:
        v = x["validation"]
        print(f"  {x['id']}: {x['status']} epa_ok={v['epa_sole_offering_holds']} chk={v['checkable_ground_truth']} agree={v['agree']} "
              f"pos={v['checkable_positives_manual']} new_manual={x['newly_confirmed_manual']} new_auto={x['newly_labelled_non_manual']} "
              f"unknown={v['in_scope_codes_not_in_table']} epa_car={v['manual_codes']['epa_crosscheck_per_car']}/{v['automatic_codes']['epa_crosscheck_per_car']}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
