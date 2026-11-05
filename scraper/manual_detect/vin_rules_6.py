#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 6: Dodge, Chrysler, Jeep,
Ram, Plymouth, Fiat (the Chrysler / FCA / Stellantis family).

What the manufacturers' own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say. All 351 filings MID lists for the filers
"Chrysler", "FCA", "Stellantis", "Fiat", "Jeep Corporation", "American
Motors" and "DaimlerChrysler" (MY1984-MY2027) were downloaded 2026-11-05;
the text layers were searched and the scanned ones that matter were read as
page images.

  * AMC-era Jeep VINs (Jeep Corporation / American Motors format, MY1981-1988,
    WMI 1JC / 1JT / 2BC / 2CC) DO encode the transmission: position 4 is the
    engine and position 5 the transmission (Jeep Corporation filings
    01-22-N11B-1748 and -1794, MY1985: H/N/S/W manual, J/D automatic). The
    base tables for the other letters vPIC decodes (L, M, V manual; A, B, E,
    R, T, U automatic) are not in MID, so those letters are a candidate rule.
  * Every Chrysler-format VIN from MY1989 on (Chrysler Motors, Chrysler
    Corp., DaimlerChrysler, Chrysler LLC/Group, FCA US, FCA Italy, FCA
    Mexico) does NOT encode the transmission for US-market vehicles:
    4 restraint (cars) or GVWR/brakes (trucks), 5 line, 6 series, 7 body,
    8 engine (FCA 2011+: 5-7 brand/line/series/drive/body, 8 engine). The
    only transmission character is an export one: on European-market VINs
    (MY1993 car guide, "Europe Only") and on BUX export vehicles with sales
    code ABB / YAB (MY2006-2009 guides) position 6 carries a transmission
    letter instead of the series digit. No lot car carries such a VIN.
  * So, as for Ford, the remaining VIN evidence is an engine code (position
    8), gated by the line/series characters, that the maker sold with only
    one transmission. Each rule names the filings that define the code, the
    EPA rows (fueleconomy.gov vehicles.csv, independent of vPIC) that list
    only that transmission, and an independent text source. A rule whose
    transmission evidence is contradicted by an independent source, or has
    no EPA row, is a candidate and its cars are NOT counted.

Every rule is validated against ground_truth.jsonl (uniformCell lines are
unlabelled), cross-checked per car against EPA, and counted for the lot cars
WITHOUT transmission info it would newly confirm as manual. Published labels
that contradict a rule are listed (published_label_conflicts), and so are the
vPIC "manual" labels on this family's MY2011+ cars that EPA contradicts or
cannot confirm (hub_findings).

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (optional, EPA cross-check).
Output: scraper/manual_detect/vin_rules_6.json

Run:  python3 -I scraper/manual_detect/vin_rules_6.py
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

OUT = HERE / "vin_rules_6.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
MAKES = ("Dodge", "Chrysler", "Jeep", "Ram", "Plymouth", "Fiat")
M, A = "manual", "automatic"

# ---------------------------------------------------------------------------
# VIN helpers (same conventions as vin_rules_0..4)
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
# Citations. MID files downloaded 2026-11-05 (MID search + displayfile);
# "page image" = scanned filing read as a rendered image.
# ---------------------------------------------------------------------------
def mid(guid: str, doc: str, says: str) -> dict:
    return {"url": MID + guid, "doc": doc, "says": says}


def web(url: str, doc: str, says: str) -> dict:
    return {"url": url, "doc": doc, "says": says}


C = {
    # --- Jeep Corporation (AMC era) -----------------------------------------
    "jc1748": mid("e6746588-4508-4046-a7c6-d89d828b0354",
                  "NHTSA 01-22-N11B-1748, Jeep Corporation 1984-07-31, amended 1985 MY multipurpose passenger vehicle VIN information (Toledo), 2 pp, page image",
                  "Cover letter: 'These changes include additional information at VIN character positions four and five.' Attachment: VIN char. pos. 4 Engine: B = 2.1 L Turbo Diesel - Renault. VIN char. pos. 5 Transmission (with transfer case): H = 4-Speed Manual-Floor (Full Time); J = Automatic column (Full Time); N = 5-Speed Manual-Floor (Full Time)."),
    "jc1794": mid("252c4f7a-ee5d-4bc1-937d-0d9afc53fc46",
                  "NHTSA 01-22-N11B-1794, Jeep Corporation 1985-01-02, amended 1985 MY MPV VIN information, 2 pp, page image",
                  "VIN char. pos. 5 Transmission (transfer case): S = 4-Speed Manual - Floor (None); D = Automatic - Floor (None); W = 5-Speed Manual - Floor (None). Pos. 6-7: 73 = Cherokee MPV 2 DR Wagon, 74 = Cherokee 4 DR Wagon."),
    "jc2064": mid("333743a4-027b-4fe6-ad68-80656ec6a262",
                  "NHTSA 01-22-N11B-2064, Jeep Corporation 1985-07-30, '1986 Jeep VIN Codes' (amendment), 2 pp, page image",
                  "Pos. 6-7: 65/66 = Comanche truck 2-door cab 4x4/4x2; pos. 8 = GVWR (CJ-7, J-10, Grand Wagoneer, J-20) or package trim + GVWR (Cherokee/Wagoneer/Comanche). Confirms the AMC layout (4 engine, 5 transmission, 6-7 line/series/body, 8 GVWR/trim) is still in use for MY1986."),
    # --- Chrysler Motors / Chrysler Corporation ------------------------------
    "c3342": mid("618a70e9-18f5-4ac0-98df-72bc8ffc2e48",
                 "NHTSA 01-22-N11B-3342, Chrysler Motors Corporation 1989-02-28, 1989 MY VIN decoding guide (passenger car and MPV/truck tables), 6 pp, page image",
                 "Passenger car columns: 1 country, 2 make, 3 vehicle type, 4 other (restraint), 5 line, 6 series, 7 body, 8 engine, 9 check digit, 10 year, 11 plant. MPV/truck page 2 (issued 10/31/88): JEEP J = Cherokee 4x4, T = Cherokee 4x2, Y = Wrangler (US), YJ (Can) 4x4; DODGE L = Dakota 4x2, G = Dakota 4x4. Page 3 (revised 02-08-89) position 8: E = 2.5L 4 cyl gasoline (TBI) 121 HP CMC; G = 2.5L 4 cyl gasoline (TBI) 99 HP CMC; L = 4.0L; M/T = 4.2L 2BBL. No position names a transmission."),
    "c3340": mid("e0dc0747-46ec-4851-9ab1-a79985682280",
                 "NHTSA 01-22-N11B-3340, Chrysler Motors Corporation 1989-03-01, 1990 MY VIN tables, 6 pp, page image",
                 "MPV/truck page 3 position 8: E = 2.5L 4 cyl gasoline (TBI) 121 HP CMC; G = 2.5L 4 cyl gasoline (TBI) 99 HP CMC; L = 4.0L; T = 4.2L. 1990 model year = L. No transmission position."),
    "c3704": mid("b4bc142a-7a4f-4e8b-8c66-41af859d854d",
                 "NHTSA 01-22-N11B-3704, Chrysler Corporation 1990-07-23, 1991 MY VIN tables (reissued 7/19/90), 6 pp, page image",
                 "MPV/truck page 3 of 3 position 8: P = 2.5L 4 cyl gasoline (MPI) 121 HP CMC; G = 2.5L 4 cyl gasoline (TBI) 99 HP CMC; S = 4.0L 6 cyl (MPI) 177 HP. No transmission position."),
    "c4749": mid("c0b4b6c1-e9fe-4b82-a91b-69f1b9671c81",
                 "NHTSA 01-22-N11B-4749, Chrysler Corporation 1991-09-09, 1992 MY VIN tables (five copies of a 5-page set), 26 pp, page image",
                 "MPV/truck page 3 of 3 (reissued 9/09/91) position 8: P = 2.5L 4 cyl gasoline (MPI) 121 HP CMC; G = 2.5L 4 cyl gasoline (TBI) 99 HP CMC; S = 4.0L 190 HP; C = 5.9L 6 cyl diesel turbo intercooler 160 HP Cummins. No transmission position."),
    "c5018": mid("8e231e5e-e210-4c2f-bbd3-03a84689b004",
                 "NHTSA 01-22-N11B-5018, Chrysler Corporation 1993-01-28, 1993 MY passenger car VIN tables, 16 pp, page image",
                 "Page 3 (issued 4/22/92, rev. 8/14/92), position 6 column: A = 3 Speed Auto. Trans. --Europe Only--; B = 4 Speed Auto. Trans. --Europe Only--; C = 6 Speed Manual Trans. --Europe Only--; M = 4 Speed Manual Trans. --Europe Only--; N = 5 Speed Manual Trans. --Europe Only--. US vehicles use digits for series in position 6."),
    "c7962": mid("df405eea-4055-4b59-a81f-1e655c554456",
                 "NHTSA 01-022-N11B-7962, DaimlerChrysler Corporation 2000-08-31, 2001 MY VIN decoding tables (text layer)",
                 "MPV/truck engine table: P = 2.5L 4 CYL Gasoline (MPI) (EPE); 6 = 5.9L 6 CYL Turbo Diesel-24 Valve Cummins (ETC); 7 = 5.9L 6 CYL Turbo Diesel-HO Cummins (ETH); 0 = 2.4L 4 CYL MPI 16V (DOHC). No transmission position."),
    "c8535": mid("370aa448-296c-4dd0-99f1-c51d6408065f",
                 "NHTSA 01-022-N11B-8535, DaimlerChrysler Corporation 2001-11-09, 2002 MY MPV/truck VIN decoding guide, 11 pp, read as page image (page 9)",
                 "Position 8: F = 1.6L I4; 9 = 2.0L I4; 1 = 2.4L I4 CYL Gasoline (DOHC) (ED1); B = 2.4L I4 Gasoline (DOHC 16V) (EDZ); P = 2.5L I4 Gasoline (MPI) (EPE); K = 3.7L V6 (EKG); S = 4.0L I6 (ERH); C = 5.9L I6 High Output Turbo Diesel (ETH). Page 3: JEEP (KJ family) Liberty 4x2 / 4x4. No transmission position."),
    "c8827": mid("b152bbc1-f1bc-409b-9ac7-f9428f3af538",
                 "NHTSA 01-022-N11B-8827, DaimlerChrysler Corporation 2002-06-05, 2003 MY VIN decoding tables, 10 pp, read as page image (page 8, issued 4/22/02)",
                 "MPV/truck position 8: 1 = 2.4L I4 CYL Gasoline (DOHC) (ED1); G = 2.4L I4 Gasoline (DOHC 16V H.O.) (EDV); B = 2.4L I4 (DOHC 16V) (EDZ); K = 3.7L V6 (EKG); S = 4.0L I6 (ERH); N = 4.7L V8 (EVA). Body 9 = Open Body {Wrangler/TJ}; 8 = Sport Utility 4 Dr {Durango/Grand Cherokee/Liberty ...}."),
    "c9008": mid("dbc122c1-8afd-412e-b735-808769dae833",
                 "NHTSA 01-022-N11B-9008, DaimlerChrysler Corporation 2002-04-26, 2003 MY passenger car VIN tables, 8 pp, read as page image (page 8)",
                 "Position 8: S = 2.4L 4 CYL 16V Gasoline DOHC Turbo (EDV); R/T = 2.7L V6; Z = 8.3L V10. No transmission position."),
    "c9602": mid("1338b000-68fb-411b-b3af-e93c10f38f74",
                 "NHTSA 01-022-N11B-9602, DaimlerChrysler Corporation 2003-06-25, 2004 MY passenger car VIN tables, 8 pp, read as page image (page 7)",
                 "Position 8: C = 2.0L SOHC (ECB); F = 2.0L High Performance (ECH); Y = 2.0L DOHC (ECC); S = 2.4L 4 CYL 16V Gasoline DOHC High Output Turbo (EDV); X = 2.4L DOHC (EDZ); J = 2.4L PZEV (ED2). No transmission position."),
    "c9987": mid("01718526-741f-4077-b8ed-0f3e0eab7148",
                 "NHTSA 01-022-N11B-9987, DaimlerChrysler Corporation 2004-04-20, '2005 Passenger Car Vehicles V.I.N. Coding Guide' issued 03/16/2004, 6 pp, page image",
                 "5th position, Dodge: S = Neon (PL family U.S.), S = SX2.0 (Canada PL family), S = SRT (U.S. PL family). 8th position: S = 2.4L 4 Cyl 16V DOHC High Output Turbo Gasoline (EDV); E = 2.4L 4 Cyl 16V DOHC Turbo Gasoline (EDT); X = 2.4L DOHC (EDZ)."),
    "c467": mid("a8460bbd-cf69-4762-80cd-17f7f34136a9",
                "NHTSA ORG467, DaimlerChrysler 2005-06-20, '2006 MPV's, Truck's, Incomplete Vehicles V.I.N. Coding Guide' revised 20 June 2005, 16 pp, page image",
                "8th position (page 16): 1 = 2.4L I4 CYL DOHC Gasoline (ED1); B = 2.4L DOHC SMPI (EDZ); G = 2.4L DOHC 16V H.O. Turbo (EDV); 8 = 2.4L Turbo (EDT); 5 = 2.8L I4 Turbo Diesel (ENR); S = 4.0L I6 (ERH); K = 3.7L V6 (EKG). 6th position: 'Sales Code ABB Converts The 6th Position To Transmission Type' for BUX export families."),
    "c3153": mid("45df3bbe-e298-4749-99bf-488b7617da99",
                 "NHTSA ORG3153, DaimlerChrysler 2007-02-08, '2007 Passenger Car Vehicles V.I.N. Coding Guide' revised 08 February 2007, 13 pp, page image",
                 "5th position: Dodge PM family B = Caliber (FWD), E = Caliber (AWD). 8th position (page 10): C = 1.8L I4 16V DOHC Dual VVT Gasoline (EBA); B = 2.0L Dual VVT (ECN); K = 2.4L Dual VVT (ED3); F = 2.4L I4 16V DOHC Turbo Gasoline (ED4); E = 2.4L Turbo (EDT); S = 2.4L High Output Turbo (EDV)."),
    "c6104": mid("83c13785-518f-4bbd-9119-9fffdb65b479",
                 "NHTSA ORG6104, Chrysler LLC 2007-09-04, '2008 MPV's, Truck's, Incomplete Vehicles V.I.N. Coding Guide' revised 01 December 2007 (text layer)",
                 "'* Sales Code \"ABB\" Converts The 6Th Position To Transmission Type ... Use The Following Values For Transmission Instead Of Series Codes': B = 4 Speed Automatic, E = 5 Speed Automatic, H = 6 Speed Automatic, N = 5 Speed Manual, C = 6 Speed Manual (BUX export vehicles only)."),
    "c6105": mid("8f5b06a6-75b5-4efe-b58d-38fb6b30838f",
                 "NHTSA ORG6105, Chrysler LLC 2007-12-01, '2009 Passenger Car Vehicles, V.I.N. Coding Guide' revised 01 October 2007 (text layer)",
                 "5th position Dodge 'PM' family: 3 = Caliber (FWD) (RHD) BUX, B = Caliber (FWD) (LHD) U.S., Canada, Mexico, BUX, E = Caliber (AWD). 6th position: 2 = Caliber SE, 4 = SXT, 6 = Caliber SRT4, 7 = Caliber R/T; 'Sales Codes ABB Converts The 6th Position To Transmission Type' (BUX: G = CVT, B = 4-spd auto, E = 5-spd auto, N = 5-spd manual, F = 6-spd auto, C = 6-spd manual). 8th position: C = 1.8L 4 CYL Gasoline Non-Turbo (EBA); F = 2.4L 4 CYL Gasoline Turbo (ED4); 8 = 2.4L Turbo (EDT); Z = 8.4L V10."),
    "c7564": mid("c1ad6936-57db-4d8a-801d-1f9cf92472c4",
                 "NHTSA ORG7564, Chrysler Group LLC 2012-03-06, '2013 Passenger Car Vehicle Identification Number Code Guide' (text layer)",
                 "Position 8: R = 1.4 Liter, 4 cyl, Gas, Turbo No (EAB, EAC, EAE, EAJ, EAK); H = 1.4 Liter, 4 cyl, Gas, Turbo Yes (EAF). Positions 5-7 Fiat 500 (FF): FFA Pop, FFB Sport, FFC Lounge, FFH 500T Sport, FFF Abarth (2 Door Hatchback), FFG Electric, FFD Pop, FFE Lounge, FFJ Abarth (2 Door Convertible). Revision log: 'December 14, 2011 Added for Fiat 500 FF: (FFJ) Abarth'; 'December 1, 2011 Added for Fiat 500 FF: (FFH) 500T Sport'. Dodge Dart (PF) is DF + series; its 1.4 turbo is also H. No transmission position."),
    # --- FCA Italy (Renegade / 500X) ----------------------------------------
    "f10561": mid("d0fbacf1-2ed0-4477-a374-059a224bc885",
                  "NHTSA ORG10561, FCA Italy 2014-12-18, 'Vehicle Identification Number Code Guide NAFTA MPV / Truck MODEL YEAR 2015' (text layer)",
                  "Position 8: H = 1.4 turbo gasoline 165 hp; T = 2.4 non-turbo gasoline 184 hp; W = 1.4 turbo gasoline 160 hp. Positions 5-6-7 brand/marketing name/drive wheels/body/drive position/series; JEEP Renegade MPV. No transmission position."),
    "f10937": mid("1128b1e1-5deb-49b9-b6c6-c5787455e6c1",
                  "NHTSA ORG10937, FCA Italy 2015-07-30, NAFTA MPV/Truck VIN code guide MODEL YEAR 2016 (text layer)",
                  "Position 8: H = 1.4 turbo; T = 2.4 non-turbo; W = 1.4 turbo. Renegade ZAC J A x (FWD) / J B x (AWD), series A Sport, B Latitude, C Trailhawk, D Limited; 500X ZFB F X x (FWD) / F Y x (AWD), series A POP, B EASY, C LOUNGE, D TREKKING, E TREKKING PLUS. No transmission position."),
    "f12773": mid("42bb0d5c-c33d-4cc0-aa3c-ee9e69a3e2a8",
                  "NHTSA ORG12773, FCA Italy 2016-05-18, NAFTA MPV/Truck VIN code guide MODEL YEAR 2017, rev. May 10, 2016 (text layer)",
                  "Position 8: H = 1.4 turbo; B = 2.4 non-turbo. Revision log 'March 31, 2016 ... 8 New identification of engines starting with MY 17'."),
    "f14586": mid("3e12920e-7b92-4f65-a6d0-461aa2936c00",
                  "NHTSA ORG14586, FCA Italy 2017-06-21, NAFTA MPV/Truck VIN code guide MODEL YEAR 2018, rev. June 19, 2017 (text layer)",
                  "Position 4 brake system & GVWR; positions 5-6-7 brand, marketing name, drive wheels, cab/body type, drive position, price series; position 8 engine: B = 2.4 I4 gasoline (500X 180 hp, Renegade 180 hp), H = 1.4 turbo I4 gasoline (500L 160, 500X 160, Renegade 160). Renegade ZAC J A A/B/D (FWD Sport/Latitude/Limited), J B A/B/C/D (AWD incl. Trailhawk). No transmission position."),
    # --- independent text sources (read via web-search result text) ---------
    "src_yj": web("https://en.wikipedia.org/wiki/Jeep_Wrangler_(YJ)",
                  "Wikipedia 'Jeep Wrangler (YJ)'; Extreme Terrain YJ overview (https://extremeterrain.com/jeep-wrangler-yj-overview.html); Quadratec 1994 YJ specs; search-result excerpts 2026-11-05",
                  "An automatic option for four-cylinder Wranglers arrived in 1994 (Wikipedia); 'Automatic transmission was introduced in 1994 for 4-cylinder models' (Extreme Terrain); the 1994 automatic for the 2.5L is the 3-speed 30RH/A904 (Quadratec). Before 1994 the 2.5L used the Aisin AX-5 five-speed."),
    "src_tj24": web("https://www.quadratec.com/jeep_knowledgebase/article-102.htm",
                    "Quadratec 'Jeep Wrangler 2005-2006 TJ Specifications'; California Air Resources Board DriveClean 2005/2006 Wrangler/TJ 4WD listings (https://driveclean.ca.gov/taxonomy/term/36753); search-result excerpts 2026-11-05",
                    "Quadratec's 2005-2006 table lists the 2.4L (SE) with a six-speed manual only; DriveClean lists the 2005 and 2006 2.4L only as manual (the 4.0L with an automatic) and a 2004 2.4L with a four-speed automatic. JeepSpecs' 2006 guide is ambiguous (no engine pairing)."),
    "src_liberty": web("https://www.autoblog.com/buy/2004-Jeep-Liberty/review/",
                       "Autoblog 2002 and 2004 Jeep Liberty reviews (https://www.autoblog.com/buy/2002-Jeep-Liberty/review/); CarGurus 2005 Liberty; Engine Builder 'Rebuilding Liberty: Engine Notes on Jeep's 2.4L I4' (https://www.enginebuildermag.com/2014/02/rebuilding-liberty-engine-notes-jeeps-2-4l-i4-engine/); search-result excerpts 2026-11-05",
                       "Autoblog 2004: 'The four-cylinder engine is only available with a five-speed manual gearbox' (the V6 with manual or 4-speed automatic); Autoblog 2002: four-cylinder only with the five-speed manual; CarGurus 2005: Sport four-cylinder only with a six-speed manual; Engine Builder: NSG370 six-speed from 2005, 2.4L dropped after 2005/2006. Conflicting generic wording: Cars.com 2004 'Each engine teams with a four-speed-automatic or five-speed-manual transmission' (https://www.cars.com/articles/2004-jeep-liberty-whats-new-1420687138026/)."),
    "src_caliber": web("https://ipfs.ssi.eecc.de/ipns/en.wikipedia-on-ipfs.org/wiki/Dodge_Caliber",
                       "Wikipedia 'Dodge Caliber' (engine/transmission table, IPFS mirror); Cars.com 2009 Caliber specs (https://cars.com/research/dodge-caliber-2009/specs); CarGurus 2007 Caliber trims; search-result excerpts 2026-11-05",
                       "The SE's 1.8 L 148 hp World I4 is 'attached to a Magna Drivetrain T355 5-speed manual transmission'; the CVT is listed with the 2.0 L and 2.4 L ('A 2.0-liter, 158-hp I4 with a ... CVT ... is optional for both SE and SXT'); the 1.8 is listed for 2007-2009."),
    "src_caliber_srt4": web("https://www.autoguide.com/manufacturer/dodge/2008-dodge-caliber-srt4-review-817.html",
                            "AutoGuide 2008 Caliber SRT4 review; Consumer Guide 'Dodge Caliber SRT4' (https://blog.consumerguide.com/dodge-caliber-srt4/); Auto123 2008 Caliber SRT4 review; search-result excerpts 2026-11-05",
                            "285 hp turbocharged 2.4 L; 'Power is sent ... via a six-speed manual transmission, the only transmission offered for the Caliber SRT4' (Getrag DMT-6); built for 2008 and 2009 only."),
    "src_neon_srt4": web("https://en.wikipedia.org/wiki/Dodge_Neon_SRT-4",
                         "Wikipedia 'Dodge Neon SRT-4'; CarGurus Neon SRT-4 buying guide (https://www.cargurus.com/Cars/articles/dodge-neon-srt-4-buying-guide); Autoblog 2005 Neon review; search-result excerpts 2026-11-05",
                         "The SRT-4 'is available only with manual transmission' - the New Venture Gear T850 five-speed (2003-2005); the four-speed automatic was optional only on the base Neon SE."),
    "src_renegade": web("https://www.media.stellantisnorthamerica.com/newsrelease.do?id=15531",
                        "Stellantis North America media release id 15531 (2015 Jeep Renegade); Jalopnik 'The 2015 Jeep Renegade Is A Six-Speed Manual 4x4 For Under $20,000' (https://jalopnik.com/2015-jeep-renegade-is-your-six-speed-manual-4x4-for-und-1681172682); search-result excerpts 2026-11-05 (the media host is not reachable from this session)",
                        "'Paired with a six-speed manual transmission, the 1.4-liter MultiAir Turbo four-cylinder engine generates 160 horsepower ... on Sport and Latitude 4x2 and 4x4 models'; the 2.4-liter Tigershark MultiAir2 'is paired exclusively with the nine-speed automatic transmission'. Jalopnik's trim listing reads '6-speed manual (9-speed auto available with packages)', i.e. the 2.4L package, not a 1.4L automatic."),
    "src_fiat500": web("https://media.stellantisnorthamerica.com/newsrelease.do?id=15515",
                       "Stellantis North America release 'Fiat 500 Abarth and Abarth Cabrio Offer Automatic Transmission Option for 2015' (id 15515); PR Newswire 'Production Begins for 2015 Fiat 500 Abarth with New Automatic Transmission' (https://prnewswire.com/news-releases/production-begins-for-2015-fiat-500-abarth-with-new-automatic-transmission-264218541.html); J.D. Power Fiat 500 Abarth history (https://www.jdpower.com/cars/1971/fiat); search-result excerpts 2026-11-05",
                       "The 2015 Abarth and Abarth Cabrio add 'an optional six-speed automatic transmission as an alternative to the five-speed manual'; the Abarth 'was originally only offered ... with a five-speed manual gearbox'; the automatic also came to the 500 Turbo for 2015 (Autoblog 2015 Fiat 500)."),
    "src_500x": web("https://www.media.stellantisnorthamerica.com/text.do?id=16187",
                    "Stellantis North America release id 16187 (2016 Fiat 500X); The Auto Channel 2016 500X review (https://www2020.theautochannel.com/news/2016/09/22/285895-2016-fiat-500x-with-2017-updates-review-by-carey-russ.html); CONFLICTING: Autoblog 2016 500X listing (https://www.autoblog.com/best-deal/2016-FIAT-500X-Easy__4dr_All_Wheel_Drive/); search-result excerpts 2026-11-05",
                    "The 2.4 is 'paired exclusively to a nine-speed automatic transmission on all-wheel-drive and front-wheel-drive models'; The Auto Channel: the Pop 'is the only one with the MultiAir/stick combination'. Autoblog: the 1.4 'came with a choice of a six-speed manual or a nine-speed automatic' (contradicts EPA, which lists only Manual 6-spd for the 1.4)."),
    "src_dakota": web("https://www.edmunds.com/dodge/dakota/1997/features-specs.html",
                      "Edmunds 1997 Dakota features & specs; CONFLICTING: Auto123 '1999-2004 Dodge Dakota pre-owned' (https://www.auto123.com/en/news/1999-2004-dodge-dakota-pre-owned/50186/), CarGurus 1997 Dakota research (https://www.cargurus.com/research/1997-Dodge-Dakota-c1724), Autoevolution Dakota; search-result excerpts 2026-11-05",
                      "Edmunds lists the 2.5L 2dr Regular Cab only as '2.5L 4cyl ... 5M'. Auto123: 'The Dakota range started with a 2.5 litre four-cylinder ... A five-speed stick or four-speed automatic was available here.' CarGurus/Autoevolution: manual standard, 4-speed automatic optional (range-level wording). No source found that states the 2.5L was manual-only."),
    "src_xj25": web("https://www.thecarspec.net/car-detail/jeep-cherokee-ii-xj-25-i-se-130-hp-automatic-1993",
                    "CONFLICTING: thecarspec.net 'Jeep Cherokee II (XJ) 2.5 i SE Automatic 1993'; auto-data.net XJ 2.5 i automatic 1993-1995; 4WD Mechanix forum ('though rare, there were automatic-equipped XJ Cherokee 2.5L models ... 904/999'); search-result excerpts 2026-11-05",
                    "Spec sites list a 1993 XJ 2.5i automatic; EPA lists only Manual 5-spd for the 2.5L in 1991-1993 (8440, 8486, 9508, 9561, 10503, 10546)."),
    "src_cummins": web("https://www.xtremediesel.com/blog/?p=5773",
                       "XtremeDiesel 5.9 Cummins history; CONFLICTING: dealer listing 2001 Ram 2500 'Long Bed' (https://vms.autorevo.com/ebrochure/7240182); search-result excerpts 2026-11-05",
                       "2001 introduced a High Output 24-valve engine (245 hp, 505 lb-ft) and an NV5600 with a 1.375-inch input shaft 'used exclusively on the 2001-2002 High-Output diesel'. No source states the HO was manual-only, and one listing shows a 245 hp truck with a 4-speed automatic. EPA does not cover these trucks."),
    "epa": web(EPA_URL, "EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29), fetched once 2026-11-05 by the baseline step", ""),
}


# ---------------------------------------------------------------------------
# Rules. pos = the VIN position whose code decides; fixed = other positions
# that must match (line / series gates); codes = {code: (claim, meaning, years)}.
# ---------------------------------------------------------------------------
_AMC_WMI = ["1JC", "1JT", "2BC", "2CC"]

RULES = [
    {"id": "jeep_amc_1984_1988_char5_transmission", "make": "Jeep", "basis": "transmission_code",
     "models": "AMC-era Jeep VINs (Jeep Corporation format): CJ/Scrambler, Cherokee/Wagoneer XJ, Comanche, Grand Wagoneer/J-series, Wrangler YJ 1987-1988",
     "wmi": _AMC_WMI, "years": (1984, 1988), "fixed": {}, "pos": 5,
     "codes": {"H": (M, "4-Speed Manual-Floor (full-time transfer case)", yrs(1984, 1988)),
               "N": (M, "5-Speed Manual-Floor (full-time transfer case)", yrs(1984, 1988)),
               "S": (M, "4-Speed Manual-Floor (no transfer case)", yrs(1984, 1988)),
               "W": (M, "5-Speed Manual-Floor (no transfer case)", yrs(1984, 1988)),
               "J": (A, "Automatic, column shift (full-time transfer case)", yrs(1984, 1988)),
               "D": (A, "Automatic, floor shift (no transfer case)", yrs(1984, 1988))},
     "cites": ["jc1748", "jc1794", "jc2064"], "epa": [],
     "evidence_gaps": "The filings in MID are the MY1985 amendments only; the base MY1984-1988 tables (which carry the other letters, see the vPIC-codes candidate rule) are not in MID. The rule applies the filed letters to MY1984-1988 because every lot VIN with one of them decodes in vPIC to the same meaning (J on 1985/1987/1988 Grand Wagoneer and 1987 J10, W on 1986/1988 Comanche).",
     "notes": "This is the only family where the VIN itself encodes the transmission. vPIC already decodes these VINs, so every lot car this rule covers already shows a transmission."},
    {"id": "jeep_amc_1981_1988_char5_vpic_only_codes", "make": "Jeep", "basis": "transmission_code",
     "candidate": True,
     "models": "AMC-era Jeep VINs, position-5 letters whose meaning comes only from vPIC",
     "wmi": _AMC_WMI, "years": (1981, 1988), "fixed": {}, "pos": 5,
     "codes": {"L": (M, "5-speed manual (vPIC)", yrs(1981, 1988)),
               "M": (M, "4-speed manual (vPIC)", yrs(1981, 1988)),
               "V": (M, "5-speed manual (vPIC; every 1988 Wrangler on the lots)", yrs(1981, 1988)),
               "A": (A, "automatic (vPIC)", yrs(1981, 1988)), "B": (A, "automatic (vPIC)", yrs(1981, 1988)),
               "E": (A, "3-speed automatic (vPIC)", yrs(1981, 1988)), "R": (A, "4-speed automatic (vPIC)", yrs(1981, 1988)),
               "T": (A, "4-speed automatic (vPIC)", yrs(1981, 1988)), "U": (A, "4-speed automatic (vPIC)", yrs(1981, 1988))},
     "cites": ["jc1748", "jc1794", "jc2064"], "epa": [],
     "evidence_gaps": "Position 5 is the transmission character (Jeep Corporation filings), but the meaning of these letters is not in any MID filing; only vPIC supplies it, and the enthusiast VIN charts (jeepfan.com, quadratec.com) could not be reached from this session.",
     "notes": "Candidate: not counted. The six 1988 Wranglers (code V) are the cars whose vPIC transmission the scraper now drops as a 'model-level default' (VPIC_TRANS_DEFAULT_CELLS, JEEP WRANGLER 1988). Their transmission comes from this VIN character, not from a model default, but V's meaning is still unconfirmed by a filing."},
    {"id": "jeep_wrangler_yj_25_1989_1993_char8", "make": "Jeep", "basis": "engine_code",
     "models": "Jeep Wrangler YJ (line Y) with the 2.5L I4, MY1989-1993",
     "wmi": ["2J4", "1J4"], "years": (1989, 1993), "fixed": {5: "Y"}, "pos": 8,
     "codes": {"E": (M, "2.5L I4 TBI 121 hp (AMC): 5-speed manual only", [1989, 1990]),
               "P": (M, "2.5L I4 MPI 121 hp (AMC): 5-speed manual only", [1991, 1992, 1993])},
     "cites": ["c3342", "c3340", "c3704", "c4749", "c8535", "src_yj"],
     "epa": [{"years": yrs(1989, 1993), "model": r"^Wrangler", "displ": 2.5, "claim": M}],
     "evidence_gaps": "No MY1993 truck table was found in MID; P = 2.5L MPI in the MY1991 and MY1992 tables (and MY2001-2003), and vPIC decodes every lot 1993 code-P Wrangler as 2.5L.",
     "notes": "MY1994 on, the 2.5L Wrangler had a 3-speed automatic option (EPA 11513 ...), so the rule stops at 1993. The 4.2L (T) and 4.0L (S) had both transmissions."},
    {"id": "jeep_wrangler_tj_24_2005_2006_char8_1", "make": "Jeep", "basis": "engine_code",
     "models": "Jeep Wrangler TJ (line A) with the 2.4L I4, MY2005-2006",
     "wmi": ["1J4"], "years": (2005, 2006), "fixed": {5: "A"}, "pos": 8,
     "codes": {"1": (M, "2.4L I4 DOHC PowerTech (ED1): 6-speed manual only", [2005, 2006])},
     "cites": ["c8827", "c467", "src_tj24"],
     "epa": [{"years": [2005, 2006], "model": r"^Wrangler", "displ": 2.4, "claim": M}],
     "evidence_gaps": "The MY2004-2005 truck tables are not in MID; code 1 = 2.4L ED1 in the MY2002, MY2003 and MY2006 tables.",
     "notes": "MY2003-2004 2.4L Wranglers had a 4-speed automatic (EPA 19191, 20317), so those years are not ruled."},
    {"id": "jeep_liberty_24_2003_2005_char8_1", "make": "Jeep", "basis": "engine_code",
     "models": "Jeep Liberty KJ (line K 4x2 / L 4x4) with the 2.4L I4, MY2003-2005",
     "wmi": ["1J4", "1J8"], "years": (2003, 2005), "fixed": {5: "KL"}, "pos": 8,
     "codes": {"1": (M, "2.4L I4 DOHC PowerTech (ED1): manual only (5-speed 2003-2004, 6-speed NSG370 2005)", yrs(2003, 2005))},
     "cites": ["c8535", "c8827", "c467", "src_liberty"],
     "epa": [{"years": yrs(2003, 2005), "model": r"Liberty", "displ": 2.4, "claim": M}],
     "evidence_gaps": "The MY2004-2005 truck tables are not in MID; code 1 = 2.4L ED1 in the MY2002, MY2003 and MY2006 tables. Cars.com's 2004 review uses generic wording ('each engine teams with a four-speed-automatic or five-speed-manual'); EPA and Autoblog's explicit statement are taken over it.",
     "notes": "The 3.7L V6 (K) had both transmissions; the 2.8L CRD (5) is not ruled."},
    {"id": "jeep_liberty_24_2002_char8_1", "make": "Jeep", "basis": "engine_code", "candidate": True,
     "models": "Jeep Liberty KJ 2.4L, MY2002",
     "wmi": ["1J4", "1J8"], "years": (2002, 2002), "fixed": {5: "KL"}, "pos": 8,
     "codes": {"1": (M, "2.4L I4 DOHC (ED1)", [2002])},
     "cites": ["c8535", "src_liberty"],
     "epa": [{"years": [2002], "model": r"Liberty", "displ": 2.4, "claim": M}],
     "evidence_gaps": "EPA lists no 2002 Liberty 2.4L row at all, so the sole-offering check cannot be made for MY2002 (Autoblog's 2002 review says the four-cylinder came only with the five-speed manual).",
     "notes": "Candidate: not counted."},
    {"id": "jeep_cherokee_xj_25_1991_1993_char8_P", "make": "Jeep", "basis": "engine_code", "candidate": True,
     "models": "Jeep Cherokee XJ (line J 4x4 / T 4x2) with the 2.5L I4, MY1991-1993",
     "wmi": ["1J4", "1J8"], "years": (1991, 1993), "fixed": {5: "JT"}, "pos": 8,
     "codes": {"P": (M, "2.5L I4 MPI 121 hp (AMC)", yrs(1991, 1993))},
     "cites": ["c3704", "c4749", "src_xj25"],
     "epa": [{"years": yrs(1991, 1993), "model": r"^Cherokee", "displ": 2.5, "claim": M}],
     "evidence_gaps": "EPA lists only manuals, but spec sites list a 1993 XJ 2.5 automatic and a forum reports rare 2.5L automatics (904/999).",
     "notes": "Candidate: not counted."},
    {"id": "jeep_renegade_14t_2015_2018_char8_H_W", "make": "Jeep", "basis": "engine_code",
     "models": "Jeep Renegade BU (WMI ZAC, line J, A = FWD / B = AWD) with the 1.4L MultiAir Turbo, MY2015-2018",
     "wmi": ["ZAC"], "years": (2015, 2018), "fixed": {5: "J", 6: "AB"}, "pos": 8,
     "codes": {"H": (M, "1.4L MultiAir Turbo I4: 6-speed manual only", yrs(2015, 2018)),
               "W": (M, "1.4L MultiAir Turbo I4 160 hp: 6-speed manual only", [2015, 2016])},
     "cites": ["f10561", "f10937", "f12773", "f14586", "src_renegade"],
     "epa": [{"years": yrs(2015, 2018), "model": r"^Renegade", "displ": 1.4, "charger": "T", "claim": M}],
     "evidence_gaps": "",
     "notes": "MY2019 on, the 1.4L turbo was gone (1.3L turbo and 2.4L, automatic only), so the rule stops at 2018."},
    {"id": "jeep_renegade_24_2015_2018_char8_T_B_automatic", "make": "Jeep", "basis": "engine_code",
     "models": "Jeep Renegade BU (WMI ZAC, line J, A = FWD / B = AWD) with the 2.4L Tigershark, MY2015-2018",
     "wmi": ["ZAC"], "years": (2015, 2018), "fixed": {5: "J", 6: "AB"}, "pos": 8,
     "codes": {"T": (A, "2.4L Tigershark I4 (MY2015-2016 code): 9-speed automatic only", [2015, 2016]),
               "B": (A, "2.4L Tigershark I4 (MY2017-2018 code): 9-speed automatic only", [2017, 2018])},
     "cites": ["f10561", "f10937", "f12773", "f14586", "src_renegade"],
     "epa": [{"years": yrs(2015, 2018), "model": r"^Renegade", "displ": 2.4, "claim": A}],
     "evidence_gaps": "",
     "notes": ("Automatic claim only (adds no Manual badge). Its ground-truth agreement is low because 20 of the 25 checkable lines "
               "are vPIC decodes of 2018 Sport/Latitude Renegades with engine B that read '6-spd Manual'. FCA Italy's MY2018 filing "
               "makes B the 2.4L, EPA lists only 'Automatic 9-spd' for every 2015-2018 Renegade 2.4L (36037, 36108, 37056, 37060, "
               "38304, 38305, 39775, 39779, 39804), and the Jeep press release says the 2.4L is 'paired exclusively with the nine-speed "
               "automatic'. The disagreeing lines are vPIC's trim-standard transmission (Sport/Latitude came standard with the 1.4L "
               "manual), so the rule's status is left as the bar computes it and the conflict goes to the hub (published_label_conflicts, "
               "hub_findings).")},
    {"id": "fiat_500x_2016_2018_char8_engine", "make": "Fiat", "basis": "engine_code", "candidate": True,
     "models": "Fiat 500X (WMI ZFB, line F, X = FWD / Y = AWD), MY2016-2018",
     "wmi": ["ZFB"], "years": (2016, 2018), "fixed": {5: "F", 6: "XY"}, "pos": 8,
     "codes": {"H": (M, "1.4L MultiAir Turbo I4", yrs(2016, 2018)),
               "W": (M, "1.4L MultiAir Turbo I4 160 hp", [2016]),
               "T": (A, "2.4L Tigershark I4 (MY2016 code): 9-speed automatic only", [2016]),
               "B": (A, "2.4L Tigershark I4 (MY2017-2018 code): 9-speed automatic only", [2017, 2018])},
     "cites": ["f10937", "f12773", "f14586", "src_500x"],
     "epa": [{"years": yrs(2016, 2018), "model": r"^500 X$", "displ": 1.4, "charger": "T", "claim": M},
             {"years": yrs(2016, 2018), "model": r"^500 X", "displ": 2.4, "claim": A}],
     "evidence_gaps": "Autoblog's 2016 500X listing says the 1.4 had a choice of manual or 9-speed automatic, contradicting EPA (Manual 6-spd only).",
     "notes": "Candidate: not counted. No lot 500X carries the 1.4 turbo code anyway."},
    {"id": "fiat_500_turbo_2012_2014_series_FHJ_char8_H", "make": "Fiat", "basis": "series_code",
     "models": "Fiat 500 Abarth (series F hatch / J cabrio) and 500 Turbo '500T Sport' (series H), MY2012-2014",
     "wmi": ["3C3"], "years": (2012, 2014), "fixed": {5: "F", 6: "F", 7: "FHJ"}, "pos": 8,
     "codes": {"H": (M, "series FFF/FFJ Abarth or FFH 500T Sport with the 1.4L MultiAir Turbo (EAF): 5-speed manual only until the MY2015 automatic", yrs(2012, 2014))},
     "cites": ["c7564", "src_fiat500"],
     "epa": [{"years": yrs(2012, 2014), "model": r"^500( Abarth)?$", "displ": 1.4, "charger": "T", "claim": M}],
     "evidence_gaps": "The MY2012 and MY2014 passenger-car tables in MID are scans that were not read; the MY2013 table and its December 2011 revision entries define FFF/FFJ Abarth, FFH 500T Sport and H = 1.4 turbo, and vPIC decodes every lot car in scope as Abarth / 500T Sport 1.4L.",
     "notes": "MY2015 added an automatic to the Abarth and the Turbo (EPA 35155, 35158), so the rule stops at 2014. The Dodge Dart's 1.4 turbo is also code H, hence the FF gate."},
    {"id": "dodge_caliber_18_2007_2009_char8_C", "make": "Dodge", "basis": "engine_code",
     "models": "Dodge Caliber PM (line B, FWD LHD) with the 1.8L I4, MY2007-2009",
     "wmi": ["1B3"], "years": (2007, 2009), "fixed": {5: "B"}, "pos": 8,
     "codes": {"C": (M, "1.8L I4 DOHC Dual VVT (EBA): 5-speed manual only (Magna T355)", yrs(2007, 2009))},
     "cites": ["c3153", "c6105", "src_caliber"],
     "epa": [{"years": yrs(2007, 2009), "model": r"^Caliber", "displ": 1.8, "claim": M}],
     "evidence_gaps": "The MY2008 passenger-car table is not in MID; C = 1.8L EBA in the MY2007 and MY2009 tables.",
     "notes": "The 2.0L (B 2007-2008, A 2009+) and 2.4L (K/B) had the CVT; not ruled."},
    {"id": "dodge_caliber_srt4_2008_2009_char8_F", "make": "Dodge", "basis": "engine_code",
     "models": "Dodge Caliber SRT4 (line B, 2.4L turbo), MY2008-2009",
     "wmi": ["1B3"], "years": (2008, 2009), "fixed": {5: "B"}, "pos": 8,
     "codes": {"F": (M, "2.4L I4 DOHC Turbo (ED4), Caliber SRT4: 6-speed manual only", [2008, 2009])},
     "cites": ["c3153", "c6105", "src_caliber_srt4"],
     "epa": [{"years": [2008, 2009], "model": r"^Caliber", "displ": 2.4, "charger": "T", "claim": M}],
     "evidence_gaps": "The MY2008 passenger-car table is not in MID; F = 2.4L Turbo ED4 in the MY2007 and MY2009 tables (MY2009: series 6 = Caliber SRT4).",
     "notes": ""},
    {"id": "dodge_neon_srt4_2003_2005_char8_S", "make": "Dodge", "basis": "engine_code",
     "models": "Dodge Neon SRT-4 (line S = Neon PL family, 2.4L high-output turbo), MY2003-2005",
     "wmi": ["1B3"], "years": (2003, 2005), "fixed": {5: "S"}, "pos": 8,
     "codes": {"S": (M, "2.4L I4 DOHC (High Output) Turbo (EDV): 5-speed manual only (NVG T850)", yrs(2003, 2005))},
     "cites": ["c9008", "c9602", "c9987", "src_neon_srt4"],
     "epa": [{"years": yrs(2003, 2005), "model": r"Neon", "displ": 2.4, "charger": "T", "claim": M}],
     "evidence_gaps": "",
     "notes": "The line gate matters: the PT Cruiser GT (line Y) used turbo 2.4L codes too and had an automatic."},
    {"id": "dodge_dakota_25_1990_2002_char8", "make": "Dodge", "basis": "engine_code", "candidate": True,
     "models": "Dodge Dakota 4x2 (line L) with the 2.5L I4, MY1990-2002",
     "wmi": ["1B7"], "years": (1990, 2002), "fixed": {5: "L"}, "pos": 8,
     "codes": {"G": (M, "2.5L I4 TBI 99 hp (Chrysler)", yrs(1990, 1995)),
               "P": (M, "2.5L I4 MPI (AMC)", yrs(1996, 2002))},
     "cites": ["c3342", "c3340", "c3704", "c4749", "c7962", "c8535", "src_dakota"],
     "epa": [{"years": yrs(1990, 2002), "model": r"^Dakota Pickup", "displ": 2.5, "claim": M}],
     "evidence_gaps": "EPA lists only Manual 5-spd for the 2.5L in all 13 years (an automatic only in 1989, id 5979), but Auto123 says 'a five-speed stick or four-speed automatic was available' for the 2.5L, and no text source states it was manual-only. The MY1993-2000 truck tables were not read (G = 2.5L TBI in MY1989-1992; P = 2.5L MPI in MY2001-2002).",
     "notes": "Candidate: not counted. One manufacturer source (a 1996-2002 Dakota order guide or press kit) stating the transmission for the 2.5L would settle it; this is the largest candidate in this worklist."},
    {"id": "ram_hd_ho_cummins_2001_2002_char8", "make": "Dodge", "basis": "engine_code", "candidate": True,
     "models": "Dodge Ram 2500/3500 with the High Output 5.9L Cummins, MY2001-2002",
     "wmi": ["1B7", "3B7", "1B6", "3B6"], "years": (2001, 2002), "fixed": {}, "pos": 8,
     "codes": {"7": (M, "5.9L I6 Turbo Diesel High Output Cummins (ETH)", [2001]),
               "C": (M, "5.9L I6 High Output Turbo Diesel (ETH)", [2002])},
     "cites": ["c7962", "c8535", "c8827", "src_cummins"], "epa": [],
     "evidence_gaps": "EPA does not cover heavy-duty pickups; no source found states the HO was manual-only, and one listing pairs 245 hp with a 4-speed automatic.",
     "notes": "Candidate: not counted."},
]

RULE_STATUS_NOTE = {
    "candidate": "not counted: the evidence does not meet the bar (see notes / evidence_gaps)",
    "low_sample": f"fewer than {MIN_SAMPLE} checkable ground-truth cars; kept because the code meaning comes from the manufacturer's own Part 565 VIN filing and the one-transmission fact from EPA plus an independent source (or, for the AMC rule, the filing names the transmission itself)",
    "keep": f">= {MIN_SAMPLE} checkable cars and agreement >= {MIN_AGREEMENT}",
    "drop": f"agreement below {MIN_AGREEMENT}",
}

ANSWER = {
    "Dodge": ("NOT ENCODED on US-market VINs, MY1981 to today. Every Chrysler/DaimlerChrysler/FCA filing read (MY1989-1993, "
              "2001-2009, 2013, 2015-2027 text layers searched) uses 4 restraint (cars) or GVWR+brakes (trucks), 5 line, 6 series, "
              "7 body, 8 engine (FCA 2011+: 5-7 brand/line/series/drive/body, 8 engine). The only transmission character is for "
              "export VINs: position 6 carries a transmission letter on 'Europe Only' vehicles (MY1993 car table: A 3-spd auto, B "
              "4-spd auto, C 6-spd manual, M 4-spd manual, N 5-spd manual) and on BUX vehicles with sales code ABB/YAB (MY2006-2009: "
              "B 4-spd auto, E 5-spd auto, F/H 6-spd auto, G CVT, N 5-spd manual, C 6-spd manual). No lot car carries such a VIN. "
              "Manual-only engine codes ruled: Caliber 1.8L (C, 2007-2009), Caliber SRT4 (F, 2008-2009), Neon SRT-4 (S, 2003-2005). "
              "Candidates (not counted): Dakota 2.5L (G 1990-1995, P 1996-2002), Ram HD High Output Cummins (7 in 2001, C in 2002)."),
    "Chrysler": ("NOT ENCODED (same Chrysler scheme). No Chrysler-brand engine or series code on the lots is manual-only: PT Cruiser "
                 "GT turbo, Crossfire, Sebring/Stratus coupes and Neon all had both transmissions or no lot car; everything else "
                 "(300, 200, Town & Country, Pacifica, Sebring sedan, Concorde, LHS) was automatic-only. Lot cars the feed files as "
                 "'Chrysler Caliber/Dart' carry Dodge WMIs and fall under the Dodge rules."),
    "Jeep": ("ENCODED for AMC-era VINs, MY1981-1988 (WMI 1JC/1JT/2BC/2CC): position 4 = engine, position 5 = transmission "
             "(Jeep Corporation filings 01-22-N11B-1748 and -1794: H 4-spd manual, N 5-spd manual, S 4-spd manual, W 5-spd "
             "manual, J automatic column, D automatic floor). NOT ENCODED from MY1989 (Chrysler format) and on FCA Italy Renegades. "
             "Engine-code rules: Wrangler YJ 2.5L (E 1989-1990, P 1991-1993), Wrangler TJ 2.4L (1, 2005-2006), Liberty 2.4L "
             "(1, 2003-2005), Renegade 1.4 turbo manual / 2.4 automatic (2015-2018). Candidates: AMC letters known only from vPIC "
             "(L, M, V manual; A, B, E, R, T, U automatic), Liberty 2.4L 2002 (no EPA row), Cherokee XJ 2.5L 1991-1993 (contradicted)."),
    "Ram": ("NOT ENCODED (FCA scheme; ProMaster City uses the FCA Italy scheme). No Ram-brand engine code is manual-only: the "
            "HD 6.7 Cummins and 5.7 had the G56 manual and automatics on the same engine codes; ProMaster/ProMaster City were "
            "automatic-only."),
    "Plymouth": ("NOT ENCODED (Chrysler scheme). No Plymouth engine code on the lots is manual-only. The 1990 Laser RS Turbo "
                 "(2 lot cars, EPA manual-only) is a Diamond-Star (Mitsubishi) build whose VIN codes are in Mitsubishi's filings, "
                 "so it is left to the Mitsubishi worklist."),
    "Fiat": ("NOT ENCODED (Chrysler Group/FCA Mexico 3C3 and FCA Italy ZFB schemes). Series/engine rule: Fiat 500 Abarth "
             "(series F/J) and 500T Sport (series H) with the 1.4 turbo (H), MY2012-2014. Candidate: 500X 1.4 turbo (contradicted; "
             "no lot car). 500L 1.4 turbo had manual, DDCT and automatic on the same code."),
}

VIN_SCHEME = {
    "AMC / Jeep Corporation (MY1981-1988)": {
        "positions": {"1-3": "WMI (1JC Jeep MPV, 1JT Jeep truck, 2BC/2CC Canada)", "4": "engine",
                      "5": "TRANSMISSION (and transfer case): filed letters H, N, S, W manual; J, D automatic",
                      "6-7": "line, series, cab/body, chassis", "8": "GVWR or package trim + GVWR", "9": "check digit",
                      "10": "model year", "11": "plant", "12-17": "sequence"},
        "transmission": "position 5 (Jeep Corporation 01-22-N11B-1748, 01-22-N11B-1794)"},
    "Chrysler Motors / Chrysler Corp. / DaimlerChrysler / Chrysler LLC (MY1981-2010)": {
        "positions": {"1-3": "WMI", "4": "restraint system (cars) / GVWR + brakes (MPV, trucks)", "5": "line",
                      "6": "series (digit); on export VINs (Europe Only MY1993; BUX sales code ABB/YAB MY2006-2009) a transmission letter",
                      "7": "body style", "8": "engine", "9": "check digit", "10": "model year (BUX/ABB: a tracking code)",
                      "11": "plant", "12-17": "sequence"},
        "transmission": "none on US-market VINs; export-only letter in position 6"},
    "Chrysler Group / FCA US / FCA Mexico (MY2011 on)": {
        "positions": {"1-3": "WMI", "4": "restraint system (cars) / brake system + GVWR (MPV, trucks)",
                      "5-7": "brand, marketing name, price series, drive position, drive type, body type", "8": "engine",
                      "9": "check digit", "10": "model year", "11": "plant", "12-17": "sequence"},
        "transmission": "none (text layers of every FCA US filing MY2013-2027 searched: the word 'transmission' does not occur)"},
    "FCA Italy (Renegade, 500X, 500L, ProMaster City; MY2015 on)": {
        "positions": {"1-3": "WMI (ZAC, ZFB)", "4": "brake system & GVWR range",
                      "5-7": "brand, marketing name, drive wheels, cab/body type, drive position, price series", "8": "engine",
                      "9": "check digit", "10": "model year", "11": "plant", "12-17": "sequence"},
        "transmission": "none"},
}

NOT_RULED = [
    {"make": "Dodge/Chrysler/Plymouth", "scope": "every US-market car and truck MY1989 on outside the rules", "why": "no transmission character, and the engine/series codes were sold with both transmissions or with automatics only"},
    {"make": "Dodge", "scope": "Viper 1992-2017 (manual-only model)", "why": "no Viper on the lots, so no rule was built (EPA lists only Manual 6-spd for every Viper year)"},
    {"make": "Dodge", "scope": "Stealth R/T Turbo 1991-1996 (2 lot cars, JB3XE74C), Plymouth Laser RS Turbo 1990 (2 lot cars, 4P3CS44U)", "why": "manual-only per EPA, but these are Mitsubishi/Diamond-Star builds whose VIN tables were filed by Mitsubishi (Chrysler's 1986 letter: 'submitted separately by Mitsubishi Motors'); left to the Mitsubishi worklist"},
    {"make": "Dodge", "scope": "Dart 1.4 turbo 2013-2016 (code H, 128 lot cars)", "why": "6-speed manual or 6-speed dual-clutch (EPA AM6); a dual-clutch is not a manual"},
    {"make": "Dodge", "scope": "Stratus/Plymouth Breeze 2.0L (code C)", "why": "EPA lists only manuals for the 1998-1999 Stratus 2.0, but automatics for other years and for the Breeze; no lot car in a manual-only year"},
    {"make": "Dodge", "scope": "Ram 1500 SRT-10 2004-2006 (8.3L V10)", "why": "no lot car carries the code"},
    {"make": "Dodge/Chrysler/Plymouth", "scope": "1984-1993 K-car turbos (Daytona, Shadow, Spirit, LeBaron, Omni GLH)", "why": "EPA manual-only cells exist for some 2.2 turbo years, but the turbo engine codes were shared with automatic cars in other lines/years and no filing for those years was read; 0-2 lot cars per cell"},
    {"make": "Jeep", "scope": "Wrangler 2.5L 1994-2002, 2.4L 2003-2004; Cherokee XJ 2.5L 1984-1990, 1994-2000; Liberty 3.7L; Compass/Patriot; Wrangler JK/JL 3.6/2.0T; Gladiator", "why": "both transmissions offered for the same engine code (EPA)"},
    {"make": "Jeep", "scope": "Grand Cherokee 1995 on, Commander, Cherokee KL 2014 on, Liberty 2008 on", "why": "automatic-only models; no manual claim possible, so no rule"},
    {"make": "Fiat", "scope": "500 1.4 non-turbo (R), 500L 1.4 turbo, 500X 2019 on (1.3T)", "why": "both transmissions or automatic-only"},
    {"make": "Ram", "scope": "every Ram-brand vehicle", "why": "no manual-only engine or series code"},
]

VALIDATION_METHOD = (
    "Every lot car with a rule WMI, a 17-character VIN and a valid check digit is classified. The model year comes from VIN "
    "character 10 (the listing year only picks the 30-year cycle and must be within 2 years). A rule fires only when the VIN "
    "matches its WMI, years and fixed characters and its decision character is in its table for that year; other codes get no "
    "claim. Ground truth = scraper/manual_detect/ground_truth.jsonl; uniformCell lines are unlabelled, speeds-only lines are "
    "excluded, the rest are checkable: agree means (truth is manual) == (rule says manual). This family's VIN ground truth is "
    "almost all vPIC decodes of MY2017+ cars and AMC-era Jeeps (vPIC gives no Chrysler-format transmission before then) plus "
    "VIN-less listing lines, so only the AMC rules and the Renegade rule have checkable cars, and those are vPIC-derived "
    "(partly circular). Independent checks: (1) epa_rows, the EPA rows for the rule's exact model/engine (row ids; all must be the "
    "claimed class and every rule year must have a row); (2) a per-car EPA union check (year, the rule's make, feed/vPIC model "
    "names, vPIC displacement). Status: candidate (not counted) when flagged (transmission evidence contradicted, or the code's "
    "meaning comes only from vPIC) or when the EPA sole-offering check fails; drop when >= 20 checkable and agreement < 0.995; "
    "low_sample when < 20 checkable; keep otherwise. newly_confirmed_manual counts lot cars with no published transmission "
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
    """-> (rule, claim, code, meaning); ('unknown_code', rule) when in scope but the code is not in any table."""
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
    unknown_codes = defaultdict(Counter)
    scan = Counter()
    make_cov = {m: Counter() for m in MAKES}
    gt_cov = {m: Counter() for m in MAKES}
    newly_manual, newly_auto, conflicts = [], [], []
    vpic_suspects = []

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
            # hub finding: vPIC 'manual' labels on MY2011+ cars of this family, checked against EPA
            if pcls == "manual" and (ex[4] or "vin") == "vin" and isinstance(fyear, int) and fyear >= 2011 and epa.ok:
                displ = parse_displ((dec or {}).get("engine", "") or ex[2])
                emake = _title((dec or {}).get("make", "")) or make
                emake = emake if emake in MAKES else make
                cls = epa.classes(fyear, emake, [model, _title((dec or {}).get("model", ""))], displ)
                vpic_suspects.append({"id": vid, "vin": vin, "year": fyear, "make": make, "model": model,
                                      "vpic_trim": (dec or {}).get("trim", ""), "engine": (dec or {}).get("engine", "") or ex[2],
                                      "published_trans": pub, "uniformCell": (g or {}).get("uniformCell", ""),
                                      "epa_classes": sorted(cls) if cls else None,
                                      "verdict": ("no_epa_match" if cls is None else
                                                  "contradicted_by_epa" if "manual" not in cls else
                                                  "epa_lists_both" if cls - {"manual"} else "epa_manual_only"),
                                      "yard": yard})
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
            cls = epa.classes(y, r["make"], [model, _title((dec or {}).get("model", ""))], displ)
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
                              "rule_status": "", "code": f"char{r['pos']}={code}: {meaning}", "rule_claim": claim,
                              "published_trans": pub, "transSrc": ex[4] or "vin",
                              "uniformCell": (g or {}).get("uniformCell", ""), "yard": yard})
        if not pub:
            why = "not_in_cache_backup" if dec is None else ("vpic_trans_blank" if "transmission" in dec and not dec.get("transmission")
                                                              else "vpic_trans_dropped_by_scraper" if dec.get("transmission") else "cache_old_schema")
            st[claim]["no_trans_info"] += 1
            st[claim][f"no_trans_info_{why}"] += 1
            rec = {"id": vid, "vin": vin, "year": y, "make": make, "model": model, "rule": rid,
                   "code": f"char{r['pos']}={code} ({vin[3:8]}): {meaning}", "why_no_trans": why, "yard": yard}
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
            sole = bool(rows) and (classes == ["manual"] if spec["claim"] == M else "manual" not in classes)
            missing = sorted(set(spec["years"]) - set(years_found))
            epa_ok = epa_ok and sole and not missing
            epa_rows.append({"claim": spec["claim"], "filter": {k: v for k, v in spec.items() if k != "claim"},
                             "rows": [f"{x['year']} id {x['id']} '{x['model']}' {x['displ']}L {x['trany']}"
                                      + (" turbo" if x["tCharger"].strip() else "") for x in rows],
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
            return v[1] + (f" (MY{ys[0]})" if len(ys) == 1 else f" (MY{ys[0]}-{ys[-1]})" if ys == list(range(ys[0], ys[-1] + 1))
                           else f" (MY{', '.join(map(str, ys))})")
        man_codes = {c: fmt(v) for c, v in r["codes"].items() if v[0] == M}
        aut_codes = {c: fmt(v) for c, v in r["codes"].items() if v[0] == A}
        epa_cite = ([{"url": EPA_URL, "doc": C["epa"]["doc"],
                      "says": "; ".join(f"{e['claim']}: " + (", ".join(e["rows"]) or "no row") for e in epa_rows)}]
                    if epa_rows else [])
        out_rules.append({
            "id": rid, "make": r["make"], "status": status, "basis": r["basis"],
            "status_reason": RULE_STATUS_NOTE[status] + ("" if epa_ok or r.get("candidate") else " (EPA rows do not show a sole offering for every rule year)"),
            "notes": r["notes"],
            "claim": "manual for the manual codes; automatic (not manual) for the automatic codes" if aut_codes else "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": list(r["years"]), "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + (", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())) or "none")]},
            "vin_condition": {"position": r["pos"], "manual_codes": man_codes, "automatic_codes": aut_codes},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"]] + epa_cite,
            "evidence_gaps": r["evidence_gaps"],
            "validation": {
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": tot["checkable_gt_manual"],
                "epa_rows": epa_rows, "epa_sole_offering_holds": epa_ok if r["epa"] else None,
                "manual_codes": side(M), "automatic_codes": side(A),
                "disagree_examples": examples[rid]["disagree"],
                "epa_conflict_examples": examples[rid]["epa_conflict"],
                "codes_seen_on_lots": dict(codes_seen[rid].most_common()),
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

    sus_counter = Counter((s["verdict"]) for s in vpic_suspects)
    sus_groups = Counter((s["verdict"], s["year"], s["make"], s["model"], s["vin"][3:8] if s["vin"] else "", s["vpic_trim"] or "", s["engine"])
                         for s in vpic_suspects)
    hub_findings = [
        {"finding": "vPIC returns the trim's standard transmission for FCA MY2018+ VINs, not the car's",
         "evidence": ("2018 Renegade Sport/Latitude with the 2.4L (engine B) decode as '6-spd Manual' although FCA Italy's MY2018 filing "
                      "(ORG14586) makes B the 2.4L and EPA plus the Jeep press release make the 2.4L automatic-only; a 2021 Wrangler 2.0T "
                      "decodes '6-spd Manual' although EPA lists only 'Automatic 8-spd' for the 2.0T (2019-2022). 2018 Compass "
                      "Sport/Latitude 4x4, 2019 Challenger R/T and 2022 Gladiator Rubicon decode 'manual' where EPA lists both a manual and "
                      "an automatic, so those labels are the standard transmission, not evidence about the car."),
         "published_manual_badges_by_verdict": dict(sus_counter),
         "groups": [{"verdict": k[0], "year": k[1], "make": k[2], "model": k[3], "vin_4_8": k[4], "vpic_trim": k[5], "engine": k[6], "cars": n}
                    for k, n in sorted(sus_groups.items(), key=lambda kv: (kv[0][0], -kv[1]))],
         "suggested_action": ("Hub decision (scraper change, not made here): drop the vPIC transmission for this family's MY2018+ decodes "
                              "unless EPA lists only that transmission for the year/model/engine, and drop it where EPA contradicts it "
                              "('contradicted_by_epa'). The Renegade rule's automatic codes already contradict the 2.4L ones.")},
        {"finding": "The 1988 Wrangler 'uniform manual' cell is a VIN-encoded transmission, not a model default",
         "evidence": ("AMC-era Jeep VINs carry the transmission in position 5 (Jeep Corporation filings 01-22-N11B-1748 and -1794). "
                      "All six 1988 Wranglers on the lots have position 5 = V, which vPIC decodes as a 5-speed manual; V itself is not "
                      "in any MID filing (the MY1988 base table is not in MID), so this worklist keeps V as a candidate and does not "
                      "count it. Two of the six are 2.5L cars (2BCHV81S...), and EPA lists only a manual for the 1988 Wrangler 2.5L."),
         "suggested_action": ("Keep the scraper's VPIC_TRANS_DEFAULT_CELLS entry for JEEP WRANGLER 1988 until a MY1987-1988 Jeep VIN "
                              "table confirms V; the reason recorded there ('model-level default') should read 'VIN position 5 code "
                              "not confirmed by a filing'.")},
        {"finding": "Chrysler encodes the transmission only on export VINs",
         "evidence": ("Position 6 holds a transmission letter instead of the series digit on 'Europe Only' cars (MY1993 car table, "
                      "01-22-N11B-5018) and on BUX export vehicles with sales code ABB/YAB (MY2006 ORG467, MY2008 ORG6104, MY2009 "
                      "ORG6105). Of the 22,946 lot VINs of this family for MY1993-2010, 7 have a letter in position 6; they look "
                      "mistyped (WMIs such as '12D' and '204', a 1996 Ram 1500 'HFF13'), so none is read as an export transmission code "
                      "and no rule uses this scheme."),
         "suggested_action": "none (no lot car affected)"},
    ]

    doc = {
        "worklist": "vin_rules_6",
        "makes": list(MAKES),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/vin_rules_6.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json (" + str(inv.get("scrapedAt") or inv.get("generatedAt") or "") + ")",
                   "vehicle_extras": "docs/data/vehicle_extras.json (scrapedAt " + str(extras_doc.get("scrapedAt")) + "; reflects the scraper's VPIC_TRANS_DEFAULT_CELLS drop, so 1988 Wranglers and 2002 Neons publish no transmission)",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (built 2026-11-05 before that drop; uniformCell lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA checks skipped, every engine-code rule falls to candidate)"),
                   "mid_filings": ("all 351 Part 565 filings MID lists for the filer names Chrysler, FCA, Stellantis, Fiat, Jeep, American Motors "
                                   "and DaimlerChrysler (search API AjaxHandler565TopLevel + displayfile), downloaded 2026-11-05; text layers "
                                   "searched, the cited scanned ones read as page images. No MY2004/MY2005 truck table and no MY2008 passenger-car "
                                   "table is in MID."),
                   "web_sources": ("independent text sources read through web-search result text; WebFetch could not reach "
                                   "media.stellantisnorthamerica.com, jeepfan.com or quadratec.com from this session (hosts outside the "
                                   "session's allowed network domains); quotes are in each citation")},
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
            "published_labels_contradicting_a_counted_rule": sum(1 for c in conflicts if c["rule"] in keep_ids),
            "published_vpic_manual_badges_MY2011_plus_by_epa_verdict": dict(sus_counter),
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
        "published_vpic_manual_badges_MY2011_plus": vpic_suspects,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("non-manual labels (keep+low_sample):", s["newly_labelled_non_manual_keep_and_low_sample_rules"])
    print("manual-claim precision:", s["ground_truth_precision_manual_claims"], " auto-claim agreement:", s["ground_truth_agreement_automatic_claims"])
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"], "(counted rules:", s["published_labels_contradicting_a_counted_rule"], ")")
    print("vPIC MY2011+ manual badges by EPA verdict:", s["published_vpic_manual_badges_MY2011_plus_by_epa_verdict"])
    print("scan:", s["scan"])
    for x in out_rules:
        v = x["validation"]
        print(f"  {x['id']}: {x['status']} epa_ok={v['epa_sole_offering_holds']} chk={v['checkable_ground_truth']} agree={v['agree']} "
              f"new_manual={x['newly_confirmed_manual']} new_auto={x['newly_labelled_non_manual']} codes={v['codes_seen_on_lots']} unknown={v['in_scope_codes_not_in_table']} "
              f"epa_car={v['manual_codes']['epa_crosscheck_per_car']}/{v['automatic_codes']['epa_crosscheck_per_car']}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
