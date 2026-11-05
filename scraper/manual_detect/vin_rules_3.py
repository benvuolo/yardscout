#!/usr/bin/env python3
"""Manual-transmission detection, step 2, worklist 3: Hyundai, Kia, Genesis.

What the manufacturers' own Part 565 VIN filings (NHTSA Manufacturer
Information Database, MID) say, read filing by filing (Hyundai MY1986-2027,
Kia MY1995-2027, Genesis MY2017-2027; all filed by Hyundai Motor America /
HATCI for both brands since the 1990s):

  * Layout, every year read: 1-3 WMI, 4 line, 5 model series (grade or
    trim, cars) or series/drive (Kia SUVs), 6 body type (cars) or drive
    (Hyundai SUVs: 1 FWD, 7 AWD), 7 restraint (cars) or GVWR class (SUVs),
    8 engine (Kia cars MY1995-2009: engine + restraint), 9 check digit,
    10 year, 11 plant. There is NO transmission position in any year.
  * The model-series character (5) sometimes names a transmission:
      - Genesis G70 MY2019-2021: code 2 = "2.0T Sport (MT)" (MY2019-2020
        code 4 includes "2.0T Sport (AT)"). Real listings agree (two 2021
        KMTG24LA... cars are 6-speed manuals). RULED (manual, low_sample).
      - Kia Rio MY2014 (L = "1.6 Manual Trans LX STD", M = "1.6 AT LX") and
        MY2016 revised guide (L = "LX M/T", M = "LX A/T"). Real 2014 and
        2016 Rio LX cars with a 6-speed manual carry M, so the factory coded
        the grade, not the gearbox, and the table's transmission wording is
        not reliable. DROPPED.
      - Kia Soul MY2020: code 2 = "LX MT, LX AT, X-Line, RSC" (both).
  * Manual-only models/engines reachable by the line, drive and engine
    characters (claim rests on EPA + an independent reference):
      - Hyundai Veloster N MY2019-2020 (KMHT3..., 6MT only until the 2021 DCT).
      - Kia Sportage 2.0 4WD MY2005-2009 (KNDJE7.[24]).
      - Candidates only (sources conflict or code table incomplete): Hyundai
        Tucson 2.0 AWD MY2005-2009 (KM8J?7?B), Kia Sportage 2WD 2.0 SOHC
        MY1995-1996 (KNDJB7?1), Hyundai Elantra 1.6 MY1993-1995 (KMHJ???R).

vPIC carries a TransmissionStyle for Hyundai/Kia only in MY2008 and
MY2017+, and both are engine/model-level defaults (no VIN position supports
them). The MY2008 "manual" labels (all of today's Hyundai/Kia VIN manuals)
are keyed on the engine character alone: every 4-cylinder decodes "5-spd
Manual", every V6 "Automatic". They are reported in hub_findings and treated
as unlabelled in validation.

Every rule is validated against ground_truth.jsonl (uniformCell lines and
Hyundai/Kia vPIC engine-default lines are reported separately as
unlabelled), cross-checked against the EPA cell it relies on, cross-checked
against a live vPIC decode of each in-scope VIN (saved in
vin_rules_3_vpic.json so the run is offline), and counted for the lot cars
WITHOUT transmission info it would newly confirm. Cars at Canadian yards are
counted but NOT newly confirmed (the manual-only facts are US-market facts).

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv (EPA cross-check),
        scraper/manual_detect/vin_rules_3_vpic.json (live vPIC decodes).
Output: scraper/manual_detect/vin_rules_3.json

Run:  python3 -I scraper/manual_detect/vin_rules_3.py            (offline)
      python3 -I scraper/manual_detect/vin_rules_3.py --fetch    (refresh in-scope VIN + pattern decodes in vin_rules_3_vpic.json; network)
      python3 -I scraper/manual_detect/vin_rules_3.py --sweep    (re-run the position-5 vPIC sweep, ~11k patterns; network)
"""

import csv
import gzip
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"

OUT = HERE / "vin_rules_3.json"
VPIC_FILE = HERE / "vin_rules_3_vpic.json"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
VPIC_BATCH = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
MIN_SAMPLE = 20
MIN_AGREEMENT = 0.995
CANADA = {"AB", "BC", "MB", "NB", "NL", "NS", "ON", "PE", "QC", "SK"}
FEED_MAKES = ("Hyundai", "Kia", "Genesis")
HK_VPIC_MAKES = {"HYUNDAI", "KIA", "GENESIS"}

# ---------------------------------------------------------------------------
# VIN helpers (same as vin_rules_1/2)
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


def year_char(y: int) -> str:
    return _YEAR_CODES[(y - 1980) % 30]


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
    # --- Hyundai filings ----------------------------------------------------
    "hy_1986": mid("9da5a20f-14aa-459d-9dad-215d4fac3abd",
                   "NHTSA 01-22-N11B-2196, Hyundai Motor America letter 1985-12-20, 'Submission pursuant to 49 CFR 565.5, VIN for Hyundai Excel' (4 pp.)",
                   "KMH L A 3 1 J _ G U: VIN 4 line & drive (L = LHD Excel), 5 body type (A 5-door hatchback, F 4-door sedan, D 3-door hatchback), 6 body style & version (1 L, 2 GL, 3 GLS), 7 restraint (1 active 3-point), 8 engine (J 1468 cc), 9 check digit, 10 year (G 1986, H 1987, J 1988), 11 plant (U Ulsan). No transmission position."),
    "hy_1994a": mid("9e4c45a3-5a5b-46bb-8c39-db1b37d55ffd",
                    "NHTSA 01-22-N11B-5639, Hyundai filing 1994-03-14, 'VIN for Hyundai Elantra, Excel, Scoupe and Sonata' (model years G 1986 - U 1997)",
                    "VIN 4 line & drive (B Sonata 1989-94, C Sonata 1995-, L Excel 1986-89, V Excel and Scoupe 1990-, J Elantra), 5 body type, 6 body style & version (1 L, 2 GL, 3 GLS), 7 restraint (1 active, 2 passive belt), 8 engine (D 1975 cc, F 1997 cc, J 1468 cc, M 1836 cc, N 1495 cc, R 1596 cc, S 2351 cc, T 2972 cc). No transmission position."),
    "hy_1994_2003": mid("65f03093-b278-434f-8ca8-cb4b609ab02b",
                        "MID ORG11264 '94MY HMC V.I.N Decoding Guide' and the same-format MY1995-2003 guides ORG11267 (95MY), ORG11268 (96MY), ORG11269 (97MY), ORG11270 (98MY), ORG11271 (99MY), ORG11272/ORG11273 (00MY), ORG11248/ORG11249/ORG11250 (01MY incl. Santa Fe), ORG11257/ORG11259 (02MY), ORG11261 (03MY)",
                        "Passenger car: 1 country, 2 maker, 3 vehicle type, 4 line, 5 body (to MY1999) or model series (MY2000-), 6 series/grade or body type, 7 restraint, 8 engine, 9 check digit, 10 year, 11 plant. MY1994: engine R = ELANTRA (G 1596cc), M = ELANTRA (G 1836cc), N = SCOUPE (G 1495cc, turbo and non-turbo share N). Santa Fe MY2001-02 (WMI KM8): 4 S, 5 model & series A-E, 6 1 wagon FWD / 7 wagon AWD, 7 GVWR, 8 engine (B 2.4, D 2.7, E 3.5). No transmission position in any of them."),
    "hy_2004_2009": mid("52474028-e5f6-49f0-8f05-e8cba6e4e98a",
                        "MID ORG10859 (2004MY HMC guide) and the same-format guides ORG10862 (2005MY), ORG10865 (2006MY), ORG10861 (2007MY), ORG10864 (2008MY), ORG10856 (2009MY)",
                        "Cars: 4 line, 5 model & series (grade), 6 body type, 7 restraint, 8 engine. SUV (WMI KM8 / 5NM): 4 line (J Tucson JM, S Santa Fe, N Veracruz), 5 model & series, 6 drive (1 Wagon FWD, 7 Wagon AWD), 7 GVWR, 8 engine. Tucson engine: B = 2.0 DOHC (JM) (MY2005: 'JM 2.0L / SM 2.4L'; MY2007: '2.0 DOHC (JM), 3.5 DOHC (EN)'), D = 2.7 DOHC (JM). MY2008 guide (ORG10864): no transmission position for any model, so vPIC's MY2008 transmission values do not come from it."),
    "hy_2010": mid("4c9718bb-f537-4b14-8ca5-ca7fe8010c7c",
                   "MID ORG4707, HATCI letter 2009-02-12, '2010MY Hyundai and Kia V.I.N Decoding Guides' (Genesis Coupe, Sonata, Soul, Borrego, Forte)",
                   "Genesis Coupe (BK): KMH H, 5 = S L / T GL / U GLS / V GDS / W HGS (grade), 6 = 6 coupe, 7 restraint, 8 = D 2.0 DOHC / H 3.8 DOHC. Forte, Soul, Borrego: line, grade, body, restraint, engine. No transmission position; R-Spec trims are not separated."),
    "hy_2015": mid("b9e3d17a-39db-4630-9fc3-9cad7526e766",
                   "MID ORG9933, HATCI letter 2014-07-11, '2015 Hyundai Part 565 VIN Decoding' (Elantra, Elantra Coupe, Veloster, Sonata Hybrid, Genesis Coupe, Equus, Tucson, Santa Fe Sport, Santa Fe, Accent, Azera, Elantra GT)",
                   "Every line: 4 line, 5 model series = grade (L, GL, GLS, HGS, TOP), 6 body/drive, 7 restraint, 8 engine. No transmission wording."),
    "hy_2019_veloster": mid("8260a4f1-0d2f-4a76-9cef-53eb30ea79cd",
                            "MID ORG15358, HATCI letter 2018-02-12, '2019MY Hyundai Veloster' VIN decoding guide",
                            "Veloster (KMH T): 5 = F L, G 2.0L and 2.0L Premium, H 'Turbo R-Spec, Turbo and Turbo Ultimate', J HGS, K TOP; 6 = 6 coupe; 8 = B 1.6 T-GDI, F 2.0 MPI. The manual-only R-Spec shares code H with automatic trims."),
    "hy_2020_veloster_n": mid("bb5e5fd1-4a81-419a-8dbc-9f07db2eb7d0",
                              "MID ORG16641, HATCI letter 2019-03-08, '2020MY Hyundai Veloster' and '2020MY Hyundai Veloster N' VIN decoding guides",
                              "Veloster N: K M H, 4 = T 'Hyundai, Veloster N', 5 = 3 'Veloster N', 6 = 6 coupe, 7 = A/D/F/J/L/P/R restraint, 8 = H 'HMC Gasoline 2.0L DOHC T-GDI THETA II (Standard Pack 250 HP, Performance Pack 275 HP)', 10 = L 2020, 11 = U Ulsan. No transmission position."),
    "hy_2022_veloster_n": mid("4611e18e-505e-4f53-87d5-79c385922747",
                              "MID ORG18888, HATCI letter 2021-03-15, '2022MY Hyundai Veloster N'",
                              "Same codes as MY2020 (T, 3, 6, J, 2.0 T-GDI 275 HP); the DCT car of MY2021-2022 is not separated, so MY2021+ is out of scope."),
    "hy_2027": mid("c7486858-4c85-497c-80a5-70076f42299a",
                   "MID ORG26490, HATCI letter 2026-04-24, 2027MY Santa Fe / Santa Fe Hybrid / Sonata / Sonata Hybrid (typical of the 336 text-layer guides filed 2016-2026)",
                   "Columns: Manufacturer & Type (1-3), Make & Line (4), Model Series (5), Body Type (6), Restraint (7), Engine (8), Check digit, Year, Plant, Seq. no. No transmission column."),
    # --- Kia filings --------------------------------------------------------
    "kia_1995": mid("c9473710-f4f8-453f-8f77-29327e9184fb",
                    "NHTSA 01-22-N11B-5812, Kia Motors Corporation letter 1994-09-14, '1995 Model Year VIN Code Information' (model years S 1995, T 1996)",
                    "Cars (Sephia KNAFA12?): 4-5 line/series, 6-7 body type, 8 engine/restraint. MPV (Sportage, KND): 4 J, 5 A = 4WD / B = 2WD, 6-7 body + GVWR (6 2-door, 7 4-door; 2 = 4001-5000 lb), 8 engine (1 = 2.0 EGI SOHC 94 hp, 3 = 2.0 EGI DOHC 120 hp). The 2WD row (J B 7 2 1) lists only the 2.0 SOHC. No transmission position."),
    "kia_2001_2009": mid("5db7edc1-c870-496f-986c-5961e3f29888",
                         "MID ORG11251 (Kia VIN decoding information 2001-04-27, MY2001-02) and the same-format Kia guides ORG11260 (2002-05-13, MY2002-03), 01-022-N11B-9379 (2002-09-05, MY2003), ORG10863 (2003-08-09), ORG10855 (2004-06-08, MY2004-05), ORG10858 (2005-04-15, MY2006), ORG10854 (2006-04-18, MY2007), ORG10857 (2008MY), ORG10860 (2007-12-10, 2009MY)",
                         "Cars: 4-5 line/series, 6-7 body type, 8 engine/restraint. MPV/SUV: 4-5 line/series (Sportage KM: J + E = 4WD, J + F = 2WD), 6 body type (7 = 4-door SUV), 7 GVWR, 8 engine (Sportage: 2 = 2.0L DOHC Federal, 4 = 2.0L DOHC 50-State, 3 = 2.7L V6; MY2009 also 2 = Borrego 4.6 V8, which never pairs with line J + E). No transmission position; the MY2008 guide has none either, so vPIC's MY2008 Kia transmission values do not come from it."),
    "kia_2014_rio": mid("0c1cfe54-c9c8-48af-841c-9de408d534cd",
                        "MID ORG9014, HATCI letter 2013-10-01, '2014 Kia Part 565 VIN Decoding 131001', page 3 '2014MY V.I.N Decoding Guide - Rio (UB 4DR/5DR)'",
                        "KNA D, VIN 5 = L '1.6 Manual Trans LX STD', M '1.6 AT LX STD / Power', N '1.6 AT EX STD / Conv / Eco', P '1.6 AT SX STD / Premium'; 6 = 4/5; 7 = A/F; 8 = 1 1.2 Kappa, 2 1.4 Gamma, 3 1.6 Gamma; 10 = E; 11 = 6 Sohari."),
    "kia_2015": mid("d5a50cf4-4c9e-49d6-90b1-7cd58612b3fb",
                    "MID ORG9934, HATCI letter 2014-07-11, '2015 Kia Part 565 VIN Decoding' (Soul EV, Sedona, Optima HEV, Rio, Forte, Forte Koup, Soul, Optima, Cadenza, Sportage, Rondo)",
                    "Every line: model series = grade (L, GL, GLS/JSL/TAX, HGS, TOP); Rio MY2015 L = 'L (Low Grade)'. No transmission wording."),
    "kia_2016_rio_orig": mid("b63e2bd2-1085-474c-8424-584ecceeefeb",
                             "MID ORG10385, HATCI letter 2015-01-06, '2016 Kia Rio NHTSA Part 565 VIN Decoding 150105'",
                             "Rio (UB): VIN 5 = L 'L', M 'GL', N 'GLS,JSL,TAX', P 'HGS', R 'TOP' (grade codes)."),
    "kia_2016_rio_rev": mid("b2968c4c-d1b8-4b1d-9fc9-eb56f3259ce4",
                            "MID ORG10572, HATCI letter 2015-01-30, '2016MY Kia VIN system decoding submission 150119', page 7 (Rio, dated 2-Feb-15)",
                            "Rio (UB): VIN 5 = L 'LX M/T', M 'LX A/T', N 'LX A/T Power Pkg', P 'EX', R 'EX ECO (ISG)', S 'EX Color Pack (PE4)', T 'SX'; 8 = 3 1.6 Gamma; 10 = G. Other 2016 Kia lines in the same submission (Forte, Forte Koup, K900, Optima Hybrid, Rondo, Sedona, Soul, Soul EV, Sportage) use grade/trim names without a transmission."),
    "kia_2020_soul": mid("2c3a6ac2-5a1e-47be-9654-a73292dbcc2c",
                         "MID ORG16419, HATCI letter 2018-12-03, 2020MY Kia Soul and Sportage",
                         "Soul (KND J): VIN 5 = 2 'LX MT, LX AT, X-Line, RSC' (manual and automatic share the code), 3 EX/EXD, 5/6 GTL."),
    # --- Genesis filings ----------------------------------------------------
    "gen_2019_g70": mid("8d45bcde-d30e-4a06-8777-8047db74a582",
                        "MID ORG15239, HATCI letter 2018-01-12, '2019MY Genesis G70' VIN decoding guide (dated 10-Nov-17)",
                        "K M T, 4 = G 'GENESIS, G70', 5 = 2 '2.0T Sport (MT)', 3 '2.0T Elite, 3.3T Prestige, 3.3T Sport, 3.3T Dynamic Edition, 3.3T Design Edition', 4 '2.0T Prestige, 2.0T Dynamic, 2.0T Sport (AT)', 5 '3.3T Advanced', 6 '2.0T Advanced', 7 '3.3T Elite'; 6 = 4 sedan; 8 = A 2.0L T-GDI Theta II FR, E 3.3L T-GDI Lambda II; 10 = K; 11 = U Ulsan."),
    "gen_2020_g70": mid("535aa9bb-1fdf-4f65-95f2-58ea14265f79",
                        "MID ORG16822, HATCI letter 2019-05-13, '2020MY Genesis G70'",
                        "5 = 2 '2.0T Sport (MT)', 3 '2.0T Elite, 3.3T Prestige, 3.3T Sport', 4 '2.0T Prestige, 2.0T Sport (AT)', 5 '3.3T', 6 '2.0T', 7 '3.3T Elite'; 8 = A '2.0L T-GDI Theta II FR (252HP for AT, 255HP for MT)', E 3.3T; 10 = L."),
    "gen_2021_g70": mid("77cb1eed-00ff-4c9b-a326-9cdd2f881723",
                        "MID ORG17605, HATCI letter 2020-02-14, '2021MY Genesis G70'",
                        "5 = 2 '2.0T Sport (MT)', 3 '2.0T Elite, 3.3T Prestige, 3.3T Sport', 4 '2.0T Prestige', 6 '2.0T', 7 '3.3T'; 8 = A 2.0 T-GDI (252HP AT / 255HP MT), E 3.3T; 10 = M."),
    "gen_2022_on_g70": mid("df3aaf07-1c19-4a7b-92fa-4f77ec8db7d9",
                           "MID ORG18795 (2022MY G70/GV70, 2021-02-19); also ORG20026 (2023MY), ORG23926 (2026MY, 2025-01-08), ORG24921 (2026MY revised, 2025-10-27)",
                           "MY2022: 5 = 1 '3.3T Launch Edition', 3 '2.0T, 2.0T Prestige', 5 '3.3T ...' (no code 2, no MT). MY2026: 5 = 2 '2.5T Prestige RWD' (automatic), so code 2 means MT only in MY2019-2021."),
    # --- vPIC, EPA and independent references ------------------------------
    "vpic_live": web("https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/",
                     "NHTSA vPIC live decodes 2026-11-05 (saved in scraper/manual_detect/vin_rules_3_vpic.json: every in-scope lot VIN plus partial-VIN pattern decodes per rule code and model year)",
                     "Engine model / displacement / drive / trim per code and year: see each rule's vpic_check and vpic_partial_pattern_decodes."),
    "ref_g70_mt": web("https://www.edmunds.com/genesis/g70/2021/st-401855582/features-specs",
                      "Edmunds '2021 Genesis G70 2.0T M/T Sport'; Autotrader 2021 G70 research; The Drive / TFLcar / Carscoops on the manual ending after MY2021; listings KMTG24LA3MU067440 (Passport Auto Group, '6-Speed Manual') and KMTG24LAXMU070819 (2021 2.0T Sport, Capital One / Prime Motors); search-result excerpts, 2026-11-05",
                      "The 2.0T Sport RWD was the dedicated trim for the 6-speed manual; 2021 was the last manual year; MY2019-2020 also sold a 2.0T Sport automatic (filed as code 4). Both 2021 listings with VIN position 5 = 2 are manuals."),
    "ref_veloster_n": web("https://prnewswire.com/news-releases/2021-hyundai-veloster-n-offers-n-eight-speed-wet-dual-clutch-transmission-301101735.html",
                          "Hyundai Motor America press release '2021 Hyundai Veloster N offers N eight-speed wet dual-clutch transmission' (2020); SlashGear, TFLcar 'No longer just a manual'; search-result excerpts, 2026-11-05",
                          "The 8-speed wet DCT was new for the 2021 Veloster N as an alternative to the standard 6-speed manual; earlier Veloster N (MY2019-2020) were manual-only."),
    "ref_sportage": web("https://www.cars.com/reviews/our-view-2005-kia-sportage-1420689220097",
                        "Cars.com 2005 Sportage trims ('4dr LX 4WD I4 Manual'; the only I4 automatic is front-drive), Consumer Guide 2005-10 Sportage pricing (AWD LX 4-cylinder listed only with manual), Autobytel 2005 first drive (Sportmatic automatic on the front-drive LX), Autotrader.ca 2008 ('AWD on the four-cylinder ... only when combined with a manual'), CarGurus 2009 LX 4WD (2.0 'with its five-speed manual'); search-result excerpts, 2026-11-05 (pages not fetched: host not reachable from this session)",
                        "The 2005-2010 Sportage 2.0 four-cylinder with 4WD/AWD came only with the 5-speed manual; the 4-speed automatic was front-drive (or V6) only. No source found that lists a 2.0 4WD automatic."),
    "ref_tucson": web("https://www.jalopnik.com/2292908/years-hyundai-tucson-manual-transmission-united-states/",
                      "Jalopnik on Tucson manual years; Autotrader.ca 2006 Tucson; Cars.com 2005 Tucson trims; Consumer Guide 2005-09 Tucson pricing; conflicting: Cars.com 2007 review, Auto123 2006 GL AWD spec page, Edmunds 2009 review; search-result excerpts, 2026-11-05",
                      "Supporting: 'on the GL, AWD required the manual transmission' (Jalopnik); 'the 2.0-litre GL can also be ordered in all-wheel drive, but with a manual transmission only' (Autotrader.ca); Cars.com lists '4dr GL 4WD 2.0L I4 Manual'. Conflicting: Cars.com 2007 says both gearboxes 'can be equipped with front-wheel drive or optional four-wheel drive'; Auto123's 2006 GL AWD spec page lists an optional 4-speed automatic; Edmunds 2009 says AWD only with the V6."),
    "ref_sportage_9596": web("https://consumerguide.com/used/1995-02-kia-sportage/",
                             "Consumer Guide used 1995-2002 Kia Sportage; Retro Cars Wiki; Carwhere 1996 Sportage specs; search-result excerpts, 2026-11-05",
                             "Consumer Guide: 'Only a 5-speed manual transmission was available in the 2WD version'; the 4-speed automatic came to 2WD models for 1997; rear-drive models had the single-cam 94 hp engine. Conflicting: Carwhere lists a 1996 2WD with both a manual and an automatic."),
    "ref_elantra_16": web("https://consumerguide.com/used/1992-95-hyundai-elantra/",
                          "Consumer Guide used 1992-95 Hyundai Elantra; Carwhere 1993/1995 Elantra specs; search-result excerpts, 2026-11-05",
                          "Consumer Guide: from 1993 the 1.8 went 'on the GLS and all automatic-transmission models. Manual-shift base models stuck with the original 113-horsepower engine' (so 1.6 = manual). Conflicting: Carwhere's 1993 listing shows both engines with manual and automatic."),
    "ref_rio_listings": web("https://www.edmunds.com/kia/rio/2016/vin/KNADM4A3XG6667944/",
                            "Listings found by web search 2026-11-05: 2016 Rio LX manual KNADM4A3XG6667944 (Edmunds); 2014 Rio LX 6-speed manual KNADM5A35E6347367 (fivestarforddallas.com); 2014 Rio manual KNADM4A31E6355377 (bid.cars); 2014 Rio KNADM4A34E6351405 'MANUAL, 6-SPD'; 2016 Rio LX manuals with KNADM4A3 at Volvo Cars Richmond and Huffines. All check digits valid.",
                            "Manual Rio LX cars of MY2014 and MY2016 carry VIN 5 = M, the code Kia's own tables label '1.6 AT LX' (MY2014) and 'LX A/T' (MY2016). No VIN with KNADL was found on the lots or on the web."),
    "epa": web(EPA_URL, "EPA fueleconomy.gov vehicles.csv (downloaded 2026-11-05, Last-Modified 2026-09-29)", ""),
}

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
M, A = "manual", "automatic"

RULES = [
    dict(id="genesis_g70_20t_sport_mt_2019_2021", make="Genesis", wmi=["KMT"], years=(2019, 2021),
         fixed={4: "G"}, pos=5,
         codes={"2": (M, "'2.0T Sport (MT)': Genesis's own model-series code for the 6-speed-manual 2.0T Sport RWD", [2019, 2020, 2021])},
         not_ruled_codes={"3, 5, 6, 7": "other 2.0T/3.3T grades: 8-speed automatic", "4": "MY2019-2020 '2.0T Prestige, 2.0T Dynamic, 2.0T Sport (AT)'; MY2021 '2.0T Prestige': automatic",
                          "2 in MY2026+": "'2.5T Prestige RWD' (automatic): the year bound is essential"},
         models="Genesis G70 2.0T Sport manual (VIN KMTG2*), MY2019-2021",
         vin_scheme_source="manufacturer",
         cites=["gen_2019_g70", "gen_2020_g70", "gen_2021_g70", "gen_2022_on_g70", "vpic_live", "ref_g70_mt", "epa"],
         epa_cell=dict(make="Genesis", model=r"^G70 RWD$", displ="2.0", drive="2", dscr=None), epa_mode="manual_offered",
         epa_ids=["39913 (2019)", "41380 (2020)", "42495 (2021): G70 RWD 2.0 Manual 6-spd (the only G70 manual rows; AWD and 3.3 rows are Automatic (S8) only)", "2022 for contrast: 43926/43927 Automatic (S8) only"],
         vpic_expect=dict(engine=r"THETA II|^$", displ="2.0", trim=r"\(MT\)"),
         evidence_gaps="No G70 with code 2 is on the lots today (G70s on the lots carry 3 or 4), so the rule has no checkable car; it rests on Genesis's three filings, EPA, Edmunds/Autotrader and two 2021 listings whose code-2 VINs are manuals. vPIC already returns 'Manual/Standard' (with a wrong '8' speeds) for MY2021 code 2, and only the trim text for MY2019-2020."),
    dict(id="hyundai_veloster_n_2019_2020", make="Hyundai", wmi=["KMH"], years=(2019, 2020),
         fixed={4: "T"}, pos=5,
         codes={"3": (M, "Veloster N (2.0 T-GDI Theta II): 6-speed manual only until the 8-speed wet DCT arrived for MY2021", [2019, 2020])},
         not_ruled_codes={"3 in MY2021-2022": "Veloster N with 6MT or 8-speed DCT", "F/G/H/J/K": "Veloster 2.0 MPI / 1.6 T-GDI grades: 6MT, 6AT or 7DCT"},
         models="Hyundai Veloster N (VIN KMHT3*), MY2019-2020",
         vin_scheme_source="manufacturer",
         cites=["hy_2020_veloster_n", "hy_2019_veloster", "hy_2022_veloster_n", "vpic_live", "ref_veloster_n", "epa"],
         epa_cell=dict(make="Hyundai", model=r"^Veloster N$", displ="2.0", drive="2", dscr=None), epa_mode="manual_only",
         epa_ids=["40693 (2019)", "41385 (2020): Veloster N 2.0 turbo Manual 6-spd only", "2021 for contrast: 42927 Automatic (AM-S8), 42928 Manual 6-spd"],
         vpic_expect=dict(engine=r"THETA", displ="2.0", trim=None),
         evidence_gaps="The MY2019 Veloster N guide was not among the MID filings downloaded (the MY2019 Veloster guide ORG15358 covers the regular car only); MY2019 rests on vPIC, which decodes KMHT36AH*K as 'Veloster N', 2.0 T-GDI Theta II."),
    dict(id="kia_sportage_20_4wd_2005_2009", make="Kia", wmi=["KND"], years=(2005, 2009),
         fixed={4: "J", 5: "E"}, pos=8,
         codes={"2": (M, "2.0L DOHC (Federal) in a Sportage 4WD (line J + E): 5-speed manual only", [2005, 2006, 2007, 2008, 2009]),
                "4": (M, "2.0L DOHC (50-State) in a Sportage 4WD (line J + E): 5-speed manual only", [2005, 2006, 2007, 2008, 2009])},
         not_ruled_codes={"3": "2.7L V6: 4-speed automatic", "char5=F (2WD) + 2/4": "Sportage 2.0 front-drive: 5MT or 4AT"},
         models="Kia Sportage (KM) 2.0 four-cylinder 4WD (VIN KNDJE7*2 / KNDJE7*4), MY2005-2009",
         vin_scheme_source="manufacturer",
         cites=["kia_2001_2009", "vpic_live", "ref_sportage", "epa"],
         epa_cell=dict(make="Kia", model=r"^Sportage 4WD$", displ="2.0", drive="4", dscr=None), epa_mode="manual_only",
         epa_ids=["21588 (2005)", "22537 (2006)", "23814 (2007)", "25039 (2008)", "25354 (2009): Sportage 4WD 2.0 Manual 5-spd only (the 2.7 4WD rows are Automatic 4-spd; the 2.0 2WD rows list both)", "28802 (2010) also Manual 5-spd only, but the MY2010 Sportage guide was not read, so MY2010 is out of scope"],
         vpic_expect=dict(engine=None, displ="2.0", drive=r"4WD|AWD|4x4"),
         evidence_gaps="Codes read in the MY2005 (ORG10855), MY2006 (ORG10858), MY2007 (ORG10854), MY2008 (ORG10857) and MY2009 (ORG10860) guides. MY2010 (new VIN layout KNDK..) not read."),
    dict(id="hyundai_tucson_20_awd_2005_2009", make="Hyundai", wmi=["KM8"], years=(2005, 2009),
         fixed={4: "J", 6: "7"}, pos=8, candidate=True,
         codes={"B": (M, "2.0L DOHC Beta (JM) with VIN 6 = 7 (Wagon AWD): EPA lists Manual 5-spd only", [2005, 2006, 2007, 2008, 2009])},
         not_ruled_codes={"D": "2.7L V6: 4-speed automatic", "char6=1 (FWD) + B": "Tucson 2.0 FWD: 5MT or 4AT"},
         models="Hyundai Tucson (JM) 2.0 AWD (VIN KM8J?7?B), MY2005-2009",
         vin_scheme_source="manufacturer",
         candidate_reason="EPA lists only 'Tucson 4WD 2.0 Manual 5-spd' every year and Jalopnik, Autotrader.ca and Cars.com's 2005 trim list say the 2.0 AWD came only with the manual, but Cars.com's 2007 review says both gearboxes could be had with optional four-wheel drive and Auto123's 2006 GL AWD spec page lists an optional automatic. Not certain enough for a badge.",
         cites=["hy_2004_2009", "vpic_live", "ref_tucson", "epa"],
         epa_cell=dict(make="Hyundai", model=r"^Tucson 4WD$", displ="2.0", drive="4", dscr=None), epa_mode="manual_only",
         epa_ids=["21410 (2005)", "22517 (2006)", "23795 (2007)", "25027 (2008)", "25348 (2009): Tucson 4WD 2.0 Manual 5-spd only; 2.7 4WD rows Automatic 4-spd only", "2010 (new 2.4 Tucson) for contrast: 29948 Automatic 6-spd, 29949 Manual 6-spd"],
         vpic_expect=dict(engine=None, displ="2.0", drive=r"AWD|4WD|4x4"),
         evidence_gaps="Codes read in the MY2005-2009 guides (ORG10862, ORG10865, ORG10861, ORG10864, ORG10856)."),
    dict(id="kia_sportage_2wd_sohc_1995_1996", make="Kia", wmi=["KND"], years=(1995, 1996),
         fixed={4: "J", 5: "B"}, pos=8, candidate=True,
         codes={"1": (M, "2.0 EGI SOHC in the 2WD Sportage (J + B): EPA lists Manual 5-spd only for the 2WD", [1995, 1996])},
         not_ruled_codes={"3 (2WD DOHC)": "not in the MY1995-96 filing; the two 1996 2WD lot cars carry it and are not ruled", "A (4WD)": "5MT or 4AT"},
         models="Kia Sportage 2WD 2.0 SOHC (VIN KNDJB7?1), MY1995-1996",
         vin_scheme_source="manufacturer",
         candidate_reason="EPA (one 2WD row per year, Manual 5-spd) and Consumer Guide agree, but Carwhere lists a 1996 2WD automatic, and the lot's 1996 2WD cars carry engine code 3 (DOHC), which the MY1995-96 filing does not list for the 2WD, so the code table does not cover every 2WD build.",
         cites=["kia_1995", "vpic_live", "ref_sportage_9596", "epa"],
         epa_cell=dict(make="Kia", model=r"^Sportage 2WD$", displ="2.0", drive="2", dscr=None), epa_mode="manual_only",
         epa_ids=["12423 (1995)", "13157 (1996): Sportage 2WD 2.0 Manual 5-spd only", "1997 for contrast: 13882 Automatic 4-spd, 13883 Manual 5-spd"],
         vpic_expect=dict(engine=None, displ="2.0", drive=r"4x2|RWD|2WD|Rear"),
         evidence_gaps="MY1995-96 filing read (01-22-N11B-5812)."),
    dict(id="hyundai_elantra_16_1993_1995", make="Hyundai", wmi=["KMH"], years=(1993, 1995),
         fixed={4: "J"}, pos=8, candidate=True,
         codes={"R": (M, "1596 cc Elantra engine: EPA lists Manual 5-spd only from MY1993 (automatics got the 1.8)", [1993, 1994, 1995])},
         not_ruled_codes={"M": "1.8 (1795/1836 cc): 5MT or 4AT"},
         models="Hyundai Elantra 1.6 (VIN KMHJ???R), MY1993-1995",
         vin_scheme_source="manufacturer",
         candidate_reason="EPA and Consumer Guide agree that from 1993 the 1.6 was manual-only, but Carwhere lists a 1993 1.6 automatic; no lot car is in scope.",
         cites=["hy_1994a", "hy_1994_2003", "vpic_live", "ref_elantra_16", "epa"],
         epa_cell=dict(make="Hyundai", model=r"^Elantra$", displ="1.6", drive=None, dscr=None), epa_mode="manual_only",
         epa_ids=["9931 (1993)", "10907 (1994)", "11858 (1995): Elantra 1.6 Manual 5-spd only; 1.8 rows list both"],
         vpic_expect=dict(engine=None, displ="1.6", drive=None),
         evidence_gaps="Engine code R read in 01-22-N11B-5639 and the MY1994/1995 guides."),
    dict(id="kia_rio_code_L_lx_mt_2014_2016", make="Kia", wmi=["KNA"], years=(2014, 2016),
         fixed={4: "D"}, pos=5, drop=True,
         codes={"L": (M, "MY2014 '1.6 Manual Trans LX STD', MY2016 (revised guide) 'LX M/T'", [2014, 2016])},
         not_ruled_codes={"M": "MY2014 '1.6 AT LX', MY2016 'LX A/T', but real manual LX cars carry M", "L in MY2015": "'L (Low Grade)'"},
         models="Kia Rio (UB) MY2014 and MY2016 (VIN KNADL*)",
         vin_scheme_source="manufacturer",
         drop_reason="The manufacturer's own table is contradicted by real VINs: 2014 and 2016 Rio LX cars with a 6-speed manual carry code M, which the same tables label automatic. Kia evidently coded the grade (the original MY2016 guide used L/M/N/P/R = L/GL/GLS/HGS/TOP), so the transmission wording cannot be trusted for L either. No KNADL VIN was found on the lots or on the web.",
         cites=["kia_2014_rio", "kia_2016_rio_rev", "kia_2016_rio_orig", "kia_2015", "vpic_live", "ref_rio_listings", "epa"],
         epa_cell=dict(make="Kia", model=r"^Rio$", displ="1.6", drive=None, dscr=None), epa_mode="manual_offered",
         epa_ids=["Rio 1.6 lists Automatic 6-spd and Manual 6-spd rows in 2014 and 2016"],
         vpic_expect=dict(engine=None, displ="1.6", drive=None),
         evidence_gaps="Kept in the file as a dropped rule so it is not re-derived later."),
]

ANSWER = {
    "hyundai": "The VIN does NOT encode the transmission in any model year read (MY1986-88 Excel, MY1986-97 codes, every guide MY1994-2009, MY2010 new lines, MY2015, MY2019-2027 text guides). Positions: 4 line, 5 grade/model series (cars) or model series (SUVs), 6 body type (cars) or drive (SUVs: 1 FWD, 7 AWD), 7 restraint (cars) or GVWR (SUVs), 8 engine. Manual-only cells reachable by line/drive/engine: Veloster N MY2019-2020 (KMHT3, line code). Candidates only: Tucson 2.0 AWD MY2005-2009 (sources conflict), Elantra 1.6 MY1993-1995 (no lot car). Trim-level manuals (Genesis Coupe R-Spec, Veloster Turbo R-Spec) share their code with automatic trims.",
    "kia": "The VIN does NOT encode the transmission (MY1995 filing, MY2001-2009 guides, MY2010 new lines, MY2015, MY2016, MY2017-2027 text guides): 4-5 line/series, 6-7 body type, 8 engine/restraint (cars to MY2009); SUVs 4-5 line/series+drive, 6 body, 7 GVWR, 8 engine. Exception on paper: the Rio MY2014 and revised MY2016 guides name 'Manual Trans'/'M/T' (L) and 'AT'/'A/T' (M/N/P) in position 5, but real manual Rio LX cars carry M, so the wording is not reliable and that rule is dropped. Manual-only cell ruled: Sportage 2.0 4WD MY2005-2009 (J + E with engine 2/4). Candidate: Sportage 2WD 2.0 SOHC MY1995-96.",
    "genesis": "The VIN DOES encode a manual for one car: G70 MY2019-2021, position 5 = 2 '2.0T Sport (MT)' (Genesis filings for MY2019, 2020, 2021). Every other Genesis code (G70 other grades, G80, G90, GV60/70/80) is automatic-only and no manual was offered after MY2021. Genesis Coupe (sold as a Hyundai, KMHH) does not encode it.",
    "vpic_already_decodes_it": "vPIC returns a transmission for Hyundai/Kia only in MY2008 and MY2017+, and neither comes from a VIN position: the MY2008 values are keyed on the engine character (every 4-cylinder decodes '5-spd Manual', every V6 'Automatic'), and the MY2017+ values are model/engine defaults (for example every 2018 Elantra 2.0 decodes '6-spd Automatic' though a 6MT was offered). So every one of today's 562 Hyundai/Kia VIN-sourced 'confirmed manuals' is a vPIC default, not evidence about the car (hub_findings).",
}

VIN_SCHEME = {
    "hyundai_passenger_car_1986_1999": "VIN 4 line (& drive), 5 body type, 6 body style & version (1 L, 2 GL, 3 GLS), 7 restraint, 8 engine (01-22-N11B-2196, 01-22-N11B-5639, MY1994-99 guides).",
    "hyundai_passenger_car_2000_on": "VIN 4 line, 5 model series (grade, later trim names), 6 body type, 7 restraint, 8 engine (MY2000-2027 guides).",
    "hyundai_suv": "VIN 4 line, 5 model series, 6 drive / body (1 Wagon FWD, 7 Wagon AWD; from the 2010s 4/D = 4x2/4x4 wagon class), 7 GVWR (later restraint), 8 engine.",
    "kia_passenger_car_1995_2009": "VIN 4-5 line/series, 6-7 body type, 8 engine + restraint (01-22-N11B-5812, ORG11251 ... ORG10860).",
    "kia_mpv_suv_1995_2009": "VIN 4-5 line/series (Sportage: A/E 4WD, B/F 2WD), 6 body type, 7 GVWR, 8 engine.",
    "kia_2010_on": "VIN 4 line, 5 model series (grade/trim), 6 body type (SUVs: wagon class + 4x2/4x4), 7 restraint, 8 engine.",
    "genesis": "VIN 1-3 KMT (cars) / KMU / 5NM (SUVs), 4 line, 5 model series (trim), 6 body/drive, 7 restraint, 8 engine. G70 MY2019-2021 5 = 2 '2.0T Sport (MT)'.",
    "transmission_character": "none, in any filing read for these three makes; the only transmission wording sits inside model-series names (G70 code 2 MY2019-2021; Rio L/M/N/P MY2014 and MY2016 revised, contradicted by real VINs; Soul MY2020 code 2 'LX MT, LX AT, ...' shared).",
}

NOT_RULED = [
    "Hyundai, Kia and Genesis VINs carry no transmission character, so for nearly all of these cars (Elantra, Sonata, Accent, Santa Fe, Tucson 2.4, Veloster, Genesis Coupe, Rio, Forte, Optima, Soul, Sportage 2.4 ...) the VIN cannot say manual vs automatic. Those cars need listing text, a build-sheet source, or the owner.",
    "Kia Rio MY2014 / MY2016 code L ('Manual Trans LX' / 'LX M/T') and M ('AT LX' / 'LX A/T'): dropped, real manual LX cars carry M (rule kia_rio_code_L_lx_mt_2014_2016).",
    "Hyundai Genesis Coupe R-Spec (2.0T and 3.8, 6MT only) and Veloster Turbo R-Spec (MY2016-2020, 6MT only): their model-series code is shared with automatic trims (Genesis Coupe 5 = T/U are GL/GLS grades; Veloster H = 'Turbo R-Spec, Turbo and Turbo Ultimate'). Not ruled.",
    "Hyundai Scoupe Turbo (MY1993-95, EPA Manual 5-spd only): engine code N is shared with the non-turbo Scoupe/Accent 1.5 (MY1994-95 guides). Not ruled.",
    "Kia Sportage 2.0 4WD MY2010 (EPA Manual 5-spd only): new VIN layout (KNDK..) and the MY2010 Sportage guide was not read; no MY2010 2.0 4WD Sportage is on the lots. Not ruled.",
    "Hyundai Elantra N / Kona N, Kia Forte GT, Veloster N MY2021-22, Genesis G70 3.3T and every other DCT/automatic-only or MT-or-DCT model: no manual-only code. Not ruled.",
    "Cars without a 17-character VIN (summary.three_make_coverage.<make>.no_vin) cannot be reached by VIN rules.",
    "Cars at Canadian yards are scanned but not newly confirmed: the manual-only facts are US-market facts (EPA).",
]

VALIDATION_METHOD = (
    "For each rule, every lot car is matched by WMI, valid check digit, VIN model year (character 10, listing year picks the 30-year cycle) and the fixed + coded characters. "
    "'checkable' = its ground_truth.jsonl line has class manual/automatic/cvt/amt/dct, uniformCell is empty, and it is not a Hyundai/Kia vPIC engine-default line "
    "(source vin and vPIC make Hyundai/Kia/Genesis: no Hyundai/Kia VIN position carries the transmission, so every such vPIC value is a model/engine default; these are counted separately as 'vpic_default_lines'). "
    "Agreement = same manual-vs-not-manual answer; 'raw' agreement including the vPIC default lines is reported too. "
    "epa_cell = the EPA rows the claim rests on, re-read per model year ('manual_only' rules need EPA to list only manuals every rule year; 'manual_offered' rules need a manual row every year). "
    "vpic_check = live vPIC decode of each in-scope VIN (vin_rules_3_vpic.json): displacement / drive / engine model / trim must match the code's meaning. "
    "Status: drop when flagged (evidence contradicts the table) or when >= 20 checkable and agreement < 99.5%; candidate when flagged (evidence short of certain); "
    "low_sample when < 20 checkable (kept: the code table is the manufacturer's own Part 565 filing, and the manual claim has EPA plus an independent reference); keep otherwise. "
    "'newly_confirmed_manual' = in-scope cars at US yards whose published extras transmission is empty today."
)


# ---------------------------------------------------------------------------
def all_years(r):
    ys = set()
    for v in r["codes"].values():
        ys.update(v[2])
    return sorted(ys)


def rule_regex(r: dict) -> str:
    chars = ["."] * 17
    for p, allowed in r["fixed"].items():
        chars[p - 1] = "[" + allowed + "]" if len(allowed) > 1 else allowed
    man = "".join(c for c, v in r["codes"].items() if v[0] == M)
    if not man:
        return ""
    chars[r["pos"] - 1] = "[" + man + "]" if len(man) > 1 else man
    ys = "".join(dict.fromkeys(year_char(y) for y in all_years(r)))
    chars[9] = "[" + ys + "]" if len(ys) > 1 else ys
    return "^(" + "|".join(r["wmi"]) + ")" + "".join(chars[3:])


def classify(vin: str, year: int):
    for r in RULES:
        if vin[:3] not in r["wmi"] or not (r["years"][0] <= year <= r["years"][1]):
            continue
        if any(vin[p - 1] not in allowed for p, allowed in r["fixed"].items()):
            continue
        hit = r["codes"].get(vin[r["pos"] - 1])
        if hit and year in hit[2]:
            return r, hit[0], vin[r["pos"] - 1], hit[1]
    return None


class Epa:
    def __init__(self, path: Path):
        self.ok = path.exists()
        self.rows = []
        if self.ok:
            with open(path, newline="", encoding="utf-8") as f:
                self.rows = [r for r in csv.DictReader(f) if r["make"] in FEED_MAKES]

    def cell(self, spec: dict, years) -> dict:
        out = {}
        for y in years:
            cls, ids = set(), []
            for r in self.rows:
                if int(r["year"]) != y or r["make"] != spec["make"] or not re.search(spec["model"], r["model"]):
                    continue
                if r["displ"] != spec["displ"]:
                    continue
                four = ("4-Wheel" in r["drive"] or "All-Wheel" in r["drive"] or "4WD" in r["model"] or "AWD" in r["model"])
                if spec.get("drive") == "4" and not four:
                    continue
                if spec.get("drive") == "2" and four:
                    continue
                if spec.get("dscr") and not re.search(spec["dscr"], r["eng_dscr"]):
                    continue
                cls.add(epa_tclass(r["trany"]))
                ids.append(f"{r['id']} {r['model']} {r['trany']}")
            out[y] = {"classes": sorted(cls), "rows": ids}
        return out

    def classes_for(self, year: int, model: str, displ) -> set:
        """EPA transmission classes for year / base model / displacement (hub findings)."""
        m = (model or "").lower()
        cls = set()
        for r in self.rows:
            if int(r["year"]) != year:
                continue
            if r["baseModel"].lower() != m and not r["model"].lower().startswith(m + " ") and r["model"].lower() != m:
                continue
            if displ is not None and r["displ"] and abs(float(r["displ"]) - float(displ)) > 0.05:
                continue
            cls.add(epa_tclass(r["trany"]))
        return cls


def pattern_queries():
    """Partial-VIN patterns per rule code and year for the vPIC cross-check."""
    q = []
    for r in RULES:
        for code, v in r["codes"].items():
            for y in v[2]:
                chars = ["*"] * 10
                for i, ch in enumerate(r["wmi"][0]):
                    chars[i] = ch
                for p, allowed in r["fixed"].items():
                    chars[p - 1] = allowed[0]
                chars[r["pos"] - 1] = code
                chars[9] = year_char(y)
                q.append((r["id"], code, y, "".join(chars)))
    return q


def vpic_batch(items):
    import requests
    s = requests.Session()
    out = []
    for i in range(0, len(items), 50):
        chunk = items[i:i + 50]
        data = ";".join(f"{v},{y}" for v, y in chunk)
        res = s.post(VPIC_BATCH, data={"format": "json", "data": data}, timeout=120).json()["Results"]
        out.extend(res)
        time.sleep(0.5)
    return out


KEEP_FIELDS = ("Make", "Model", "ModelYear", "Trim", "Series", "EngineModel", "DisplacementL", "EngineCylinders", "DriveType",
               "TransmissionStyle", "TransmissionSpeeds", "BodyClass", "ErrorCode")


SWEEP_CODES = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"
TRANS_WORDS = re.compile(r"(\bM/?T\b|\bA/?T\b|manual|automatic|\bauto\b|\bDCT\b|\bCVT\b|\bIVT\b|\d\s?MT\b|\d\s?AT\b|stick)", re.I)


def sweep_queries(inv: dict) -> list:
    """Every position-5 character for every Hyundai/Kia/Genesis line (WMI + VIN 4) and model
    year MY2006-2026 on the lots, with that line's commonest positions 6-8."""
    fi = {f: i for i, f in enumerate(inv["fields"])}
    groups = defaultdict(Counter)
    for r in inv["vehicles"]:
        make, vin, y = r[fi["make"]], (r[fi["vin"]] or "").upper(), r[fi["year"]]
        if make not in FEED_MAKES or len(vin) != 17 or not y or not (2006 <= y <= 2026) or vin[9] != year_char(y):
            continue
        groups[(vin[:3], vin[3], y)][vin[5:8]] += 1
    q = []
    for (wmi, p4, y), c in sorted(groups.items()):
        p678 = c.most_common(1)[0][0]
        for p5 in SWEEP_CODES:
            q.append({"vin": wmi + p4 + p5 + p678 + "*" + year_char(y), "year": y, "wmi": wmi, "p4": p4, "p5": p5, "p678": p678})
    return q


def sweep_summary(raw: list) -> dict:
    named = [x for x in raw if x.get("model")]
    hits = [x for x in named if TRANS_WORDS.search(" ".join(str(x.get(k) or "") for k in ("trim", "trim2", "series")))]
    per_line = defaultdict(Counter)
    for x in named:
        per_line[(x["year"], x["wmi"] + x["p4"], x["make"], x["model"])][x.get("ts") or ""] += 1
    with_ts = {k: v for k, v in per_line.items() if any(v2 for v2 in v if v2)}
    varies = {k: v for k, v in with_ts.items() if len([t for t in v if t]) > 1 or "" in v}
    return {
        "method": "For each Hyundai/Kia/Genesis line (WMI + VIN 4) and model year MY2006-2026 that has a lot car, every position-5 character (33) was decoded by vPIC DecodeVINValuesBatch with that line's commonest positions 6-8 and '*' for the check digit (2026-11-05). vPIC's Trim/Series text is its transcription of the filing's model-series names.",
        "queries": len(raw), "codes_vpic_knows": len(named),
        "codes_whose_model_series_names_a_transmission": [{"year": x["year"], "vin_1_5": x["wmi"] + x["p4"] + x["p5"], "model": x["model"], "trim": x["trim"], "vpic_transmission": x.get("ts") or ""} for x in sorted(hits, key=lambda x: (x["year"], x["wmi"], x["p4"], x["p5"]))],
        "lines_where_vpic_returns_a_transmission": len(with_ts),
        "of_which_transmission_varies_with_position_5": [{"year": k[0], "vin_1_4": k[1], "model": k[3], "values": dict(v)} for k, v in sorted(varies.items())],
        "finding": "Only Kia Rio MY2014 (L '1.6 Manual Trans LX STD', M/N/P '1.6 AT ...') and MY2016 (L 'LX M/T', M 'LX A/T', N 'LX A/T Power Pkg') name a transmission in position 5 (rule kia_rio_code_L_lx_mt_2014_2016, dropped). Where vPIC returns a TransmissionStyle (MY2008, MY2017+), it is the same for every position-5 code of the line (line/engine-level default), apart from the lines listed under of_which_transmission_varies_with_position_5.",
    }


def run_sweep(inv: dict) -> list:
    qs = sweep_queries(inv)
    res = vpic_batch([(q["vin"], q["year"]) for q in qs])
    return [{**q, "make": x["Make"], "model": x["Model"], "trim": x["Trim"], "trim2": x["Trim2"], "series": x["Series"],
             "ts": x["TransmissionStyle"], "tsp": x["TransmissionSpeeds"], "displ": x["DisplacementL"], "eng": x["EngineModel"],
             "drive": x["DriveType"], "err": x["ErrorCode"]} for q, x in zip(qs, res)]


def fetch(in_scope: list) -> None:
    vins = vpic_batch([(v, y) for v, y in in_scope])
    pats = pattern_queries()
    pres = vpic_batch([(p[3], p[2]) for p in pats])
    old = json.loads(VPIC_FILE.read_text()) if VPIC_FILE.exists() else {}
    doc = {"fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
           "source": VPIC_BATCH,
           "vins": {x["VIN"]: {k: x.get(k, "") for k in KEEP_FIELDS} for x in vins},
           "partial": [{"rule": p[0], "code": p[1], "year": p[2], "pattern": p[3], **{k: x.get(k, "") for k in KEEP_FIELDS}} for p, x in zip(pats, pres)],
           "sweep": old.get("sweep", {})}
    VPIC_FILE.write_text(json.dumps(doc, indent=1) + "\n")
    print("wrote", VPIC_FILE, len(doc["vins"]), "VINs,", len(doc["partial"]), "patterns")


def store_sweep(raw: list) -> None:
    doc = json.loads(VPIC_FILE.read_text()) if VPIC_FILE.exists() else {"vins": {}, "partial": []}
    doc["sweep"] = sweep_summary(raw)
    VPIC_FILE.write_text(json.dumps(doc, indent=1) + "\n")
    print("stored sweep summary in", VPIC_FILE, doc["sweep"]["queries"], "queries")


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
    all_wmi = {w for r in RULES for w in r["wmi"]}

    st = {r["id"]: defaultdict(Counter) for r in RULES}
    ex_dis = {r["id"]: [] for r in RULES}
    vchk = {r["id"]: Counter() for r in RULES}
    vbad = {r["id"]: [] for r in RULES}
    codes_seen = {r["id"]: Counter() for r in RULES}
    years_seen = {r["id"]: Counter() for r in RULES}
    models_seen = {r["id"]: Counter() for r in RULES}
    make_cov = {m: Counter() for m in FEED_MAKES}
    scan = Counter()
    newly, canada_cars, in_scope, conflicts = [], [], [], []

    for row in inv["vehicles"]:
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        fyear = row[fi["year"]]
        make = row[fi["make"]] or ""
        model = row[fi["model"]] or ""
        yd = yards[row[fi["yard"]]] if isinstance(row[fi["yard"]], int) else ["", "", ""]
        ex = list(extras.get(vid) or []) + [""] * 5
        pub = ex[3] or ""
        if make in FEED_MAKES:
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
        in_scope.append((vin, y))
        if make in FEED_MAKES:
            make_cov[make]["covered_by_rule"] += 1
        g = gt.get(vid)
        if g is not None:
            gcls = g.get("transClass", "")
            vdefault = g.get("source") == "vin" and (g.get("vpicMake") or "").upper() in HK_VPIC_MAKES
            if gcls in KNOWN and not g.get("uniformCell"):
                s["raw_checkable"] += 1
                s["raw_agree" if (gcls == "manual") == (claim == M) else "raw_disagree"] += 1
            if g.get("uniformCell"):
                s["uniform_cell_excluded"] += 1
            elif vdefault and gcls in KNOWN:
                s["vpic_default_excluded"] += 1
                s["vpic_default_excluded_" + gcls] += 1
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
        lv = vlive.get(vin)
        if lv is None:
            vchk[rid]["not_decoded"] += 1
        else:
            exp = r["vpic_expect"]
            try:
                dl = str(round(float(lv.get("DisplacementL") or 0), 1))
            except ValueError:
                dl = ""
            okv = (dl == exp["displ"]) and \
                (not exp.get("engine") or bool(re.search(exp["engine"], lv.get("EngineModel", "") or ""))) and \
                (not exp.get("drive") or bool(re.search(exp["drive"], lv.get("DriveType", "") or ""))) and \
                (not exp.get("trim") or bool(re.search(exp["trim"], lv.get("Trim", "") or "")))
            vchk[rid]["consistent" if okv else "inconsistent"] += 1
            if lv.get("TransmissionStyle"):
                vchk[rid]["vpic_has_transmission"] += 1
            if not okv and len(vbad[rid]) < 10:
                vbad[rid].append({"vin": vin, "year": y, "EngineModel": lv.get("EngineModel"), "DisplacementL": lv.get("DisplacementL"), "DriveType": lv.get("DriveType"), "Trim": lv.get("Trim")})
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

    if "--fetch" in sys.argv:
        fetch(sorted(set(in_scope)))
        return 0
    if "--sweep" in sys.argv:            # live, ~230 batch calls
        store_sweep(run_sweep(inv))
        return 0
    if "--sweep-from" in sys.argv:       # a saved raw sweep (list of decoded queries)
        store_sweep(json.loads(Path(sys.argv[sys.argv.index("--sweep-from") + 1]).read_text()))
        return 0

    out_rules = []
    for r in RULES:
        rid = r["id"]
        tot = Counter()
        for cl in (M, A):
            tot.update(st[rid][cl])
        chk, agr = tot["checkable"], tot["agree"]
        agreement = round(agr / chk, 4) if chk else None
        if r.get("drop"):
            status = "drop"
        elif chk >= MIN_SAMPLE and agreement is not None and agreement < MIN_AGREEMENT:
            status = "drop"
        elif r.get("candidate"):
            status = "candidate"
        elif chk < MIN_SAMPLE:
            status = "low_sample"
        else:
            status = "keep"
        yrs = all_years(r)
        cell = epa.cell(r["epa_cell"], yrs) if epa.ok else {}
        if r["epa_mode"] == "manual_only":
            ok_years = [y for y, v in cell.items() if v["classes"] == ["manual"]]
        else:
            ok_years = [y for y, v in cell.items() if "manual" in v["classes"]]
        other_years = {y: v["classes"] for y, v in cell.items() if y not in ok_years}
        sm = st[rid][M]
        partial = [p for p in vp.get("partial", []) if p.get("rule") == rid]
        out_rules.append({
            "id": rid,
            "make": r["make"],
            "status": status,
            "claim": "manual",
            "scope": {"make": r["make"], "models": r["models"], "model_years": yrs, "wmi": r["wmi"],
                      "conditions": ["VIN is 17 characters with a valid check digit (character 9); VINs that fail it are skipped",
                                     "model year from VIN character 10; the listing year only picks the 30-year cycle and must be within 2 years",
                                     "fixed characters: " + ", ".join(f"char{p} in [{v}]" for p, v in sorted(r["fixed"].items())),
                                     "car is at a US yard (Canadian-market offerings are not covered by the EPA evidence)"]},
            "vin_condition": {"position": r["pos"], "manual_codes": {c: v[1] + " (MY" + ", ".join(str(y) for y in v[2]) + ")" for c, v in r["codes"].items()},
                              "codes_not_ruled": r["not_ruled_codes"], "code_table_source": r["vin_scheme_source"]},
            "vin_regex_manual": rule_regex(r),
            "citations": [C[k] for k in r["cites"] if k != "epa"] + [{"url": C["epa"]["url"], "doc": C["epa"]["doc"], "says": "; ".join(r["epa_ids"])}],
            "candidate_reason": r.get("candidate_reason", ""),
            "drop_reason": r.get("drop_reason", ""),
            "evidence_gaps": r.get("evidence_gaps", ""),
            "validation": {
                "in_scope_lot_cars": sm["in_scope"],
                "checkable_ground_truth": chk, "agree": agr, "disagree": tot["disagree"], "agreement": agreement,
                "checkable_positives_manual": tot["checkable_gt_manual"],
                "raw_including_vpic_defaults": {"checkable": tot["raw_checkable"], "agree": tot["raw_agree"], "disagree": tot["raw_disagree"]},
                "vpic_default_lines_excluded": tot["vpic_default_excluded"],
                "vpic_default_lines_excluded_by_class": {k[len("vpic_default_excluded_"):]: v for k, v in tot.items() if k.startswith("vpic_default_excluded_")},
                "uniform_cell_lines_excluded": tot["uniform_cell_excluded"],
                "ground_truth_speeds_only_excluded": tot["speeds_only_excluded"],
                "disagree_examples": ex_dis[rid][:10],
                "epa_cell": {"filter": r["epa_cell"], "mode": r["epa_mode"], "years_meeting_mode": ok_years, "years_failing": other_years,
                             "all_rule_years_meet_mode": len(ok_years) == len(yrs),
                             "rows": {y: v["rows"] for y, v in cell.items()}},
                "vpic_check": {**dict(vchk[rid]), "expect": r["vpic_expect"], "inconsistent_examples": vbad[rid]},
                "vpic_partial_pattern_decodes": [{k: p.get(k) for k in ("code", "year", "pattern", "Make", "Model", "Trim", "EngineModel", "DisplacementL", "DriveType", "TransmissionStyle", "TransmissionSpeeds", "ErrorCode")} for p in partial],
                "codes_seen_on_lots": dict(codes_seen[rid]),
                "years_seen_on_lots": dict(sorted(years_seen[rid].items())),
                "models_seen_on_lots": dict(models_seen[rid].most_common()),
                "cars_without_trans_info_us_yards": sm["no_trans_info"],
                "cars_without_trans_info_by_reason": {k[len("no_trans_info_"):]: v for k, v in sm.items() if k.startswith("no_trans_info_") and k != "no_trans_info_canadian_yard"},
                "cars_without_trans_info_canadian_yards_not_counted": sm["no_trans_info_canadian_yard"],
            },
            "newly_confirmed_manual": sm["no_trans_info"],
        })

    # ---- hub findings: what the published Hyundai/Kia/Genesis transmission labels are
    hk_lines = [g for g in gt.values() if g.get("make") in FEED_MAKES]
    vin_man = [g for g in hk_lines if g.get("source") == "vin" and g.get("transClass") == "manual"]
    by_cell = Counter()
    epa_auto = Counter()
    for g in vin_man:
        key = (g.get("vpicYear"), g.get("vpicModel"), (g.get("vin") or "")[:8], g.get("engine"), g.get("drive", "")[:3], g.get("trans"), "uniform" if g.get("uniformCell") else "mixed-cell")
        by_cell[key] += 1
        y = int(g["vpicYear"]) if (g.get("vpicYear") or "").isdigit() else g.get("year")
        cls = epa.classes_for(y, g.get("vpicModel") or g.get("model"), g.get("displL")) if epa.ok and y else set()
        four = bool(re.search(r"4WD|AWD|4x4", g.get("drive", "") or ""))
        if g.get("vpicModel") == "Sportage" and four and (g.get("displL") == 2.0):
            epa_auto["epa_manual_only (Sportage 2.0 4WD, agrees with rule kia_sportage_20_4wd_2005_2009)"] += 1
        elif "automatic" in cls:
            epa_auto["epa_lists_automatic_too"] += 1
        elif not cls:
            epa_auto["epa_cell_not_matched"] += 1
        else:
            epa_auto["epa_" + "_".join(sorted(cls))] += 1
    vin_years = Counter(g.get("vpicYear") for g in vin_man)
    auto_uncertain = Counter()
    for g in hk_lines:
        if g.get("source") != "vin" or g.get("transClass") not in ("automatic", "cvt"):
            continue
        y = int(g["vpicYear"]) if (g.get("vpicYear") or "").isdigit() else None
        if not y or not epa.ok:
            continue
        cls = epa.classes_for(y, g.get("vpicModel"), g.get("displL"))
        if "manual" in cls:
            auto_uncertain[(y, g.get("vpicModel"), g.get("displL"), g.get("trans"))] += 1
    hub = {
        "hk_vpic_manual_labels": {
            "what": "Every Hyundai/Kia/Genesis lot car whose published transmission is a vPIC 'manual' (transSrc vin).",
            "lines": len(vin_man),
            "by_vpic_model_year": dict(vin_years),
            "in_uniform_cells": sum(1 for g in vin_man if g.get("uniformCell")),
            "in_mixed_cells_not_flagged_by_baseline": sum(1 for g in vin_man if not g.get("uniformCell")),
            "epa_check": dict(epa_auto),
            "finding": "All of them are MY2008 vPIC values keyed on the engine character alone: every MY2008 Hyundai/Kia 4-cylinder (and the Santa Fe 2.7 V6) decodes '5-spd Manual/Standard', every other V6 'Automatic'. Neither the MY2008 Hyundai guide (ORG10864) nor the Kia guide (ORG10857) has a transmission position. The baseline flagged the 17 uniform cells; the 2008 Santa Fe 2.7 (5NMSG.3D) and Sportage 2.0 (KNDJ[EF]724) manuals sit in mixed cells (their V6 siblings decode automatic) and are the same default. Only the Sportage 2.0 4WD (KNDJE724) labels happen to be right (rule kia_sportage_20_4wd_2005_2009); the rest are not evidence about the car.",
            "cells": [{"vpicYear": k[0], "vpicModel": k[1], "vin_prefix": k[2], "engine": k[3], "drive": k[4], "vpic_trans": k[5], "cell": k[6], "lines": v} for k, v in by_cell.most_common()],
            "hub_decision_needed": "Whether to stop showing the Manual badge for Hyundai/Kia/Genesis vPIC MY2008 'manual' values (integration change in the scraper/app; not made here).",
        },
        "hk_vpic_automatic_labels_epa_lists_manual": {
            "what": "Hyundai/Kia/Genesis lot cars with a vPIC automatic/CVT label in a year/model/displacement where EPA also lists a manual: these are vPIC defaults, so a later manual rule would show them as false 'disagreements'.",
            "lines": sum(auto_uncertain.values()),
            "cells": [{"year": k[0], "vpicModel": k[1], "displL": k[2], "vpic_trans": k[3], "lines": v} for k, v in auto_uncertain.most_common()],
        },
    }

    kept = {x["id"] for x in out_rules if x["status"] in ("keep", "low_sample")}
    cand = {x["id"] for x in out_rules if x["status"] == "candidate"}
    nm_conf = [c for c in newly if c["rule"] in kept]
    nm_cand = [c for c in newly if c["rule"] in cand]
    man_chk = sum(x["validation"]["checkable_ground_truth"] for x in out_rules if x["id"] in kept)
    man_agr = sum(x["validation"]["agree"] for x in out_rules if x["id"] in kept)
    raw_chk = sum(x["validation"]["raw_including_vpic_defaults"]["checkable"] for x in out_rules if x["id"] in kept)
    raw_agr = sum(x["validation"]["raw_including_vpic_defaults"]["agree"] for x in out_rules if x["id"] in kept)
    doc = {
        "worklist": "vin_rules_3",
        "makes": list(FEED_MAKES),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "generator": "scraper/manual_detect/vin_rules_3.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json", "vehicle_extras": "docs/data/vehicle_extras.json",
                   "vin_decodes": "docs/data/vin_decodes.json.gz",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (uniformCell lines and Hyundai/Kia vPIC default lines treated as unlabelled)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv" + ("" if epa.ok else " (MISSING: EPA cross-check skipped)"),
                   "vpic_live": "scraper/manual_detect/vin_rules_3_vpic.json" + ("" if vlive else " (MISSING: run with --fetch)"),
                   "mid_filings_read": "NHTSA MID Part 565 files for Hyundai Motor Co / HATCI / Kia / Genesis (589 unique filings listed via the MID search API; 397+ downloaded 2026-11-05 from vpic.nhtsa.dot.gov/mid displayfile). Read: Hyundai MY1986, MY1986-97 codes, every guide MY1994-2009 (text layer), MY2010 new lines, MY2015, MY2019-2022 Veloster/Veloster N; Kia MY1995, MY2001-2009 (text layer), MY2014 Rio, MY2015, MY2016 Rio (original and revised) and the 2016 Kia submission; Genesis G70 MY2019-2027; plus a keyword scan of the 336 text-layer guides filed 2016-2026 (no 'transmission', 'manual' or 'M/T' column or name except G70 '2.0T Sport (MT)' and Soul MY2020 'LX MT, LX AT, ...'). Scanned MY2011-2014 and MY2017-18 guides were checked through vPIC's transcription of their model-series names (vpic_model_series_sweep)."},
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
                                                                "raw_including_vpic_defaults": {"checkable": raw_chk, "agree": raw_agr,
                                                                                                "precision": round(raw_agr / raw_chk, 4) if raw_chk else None},
                                                                "note": "no in-scope car has an independent (non-vPIC-default) ground-truth label" if not man_chk else ""},
            "published_labels_contradicting_a_rule": len(conflicts),
            "scan": dict(scan),
            "three_make_coverage": {m: dict(v) for m, v in make_cov.items()},
        },
        "validation_method": VALIDATION_METHOD,
        "rules": out_rules,
        "newly_confirmed_manual_cars": nm_conf,
        "candidate_rule_manual_cars": nm_cand,
        "canadian_yard_cars": canada_cars,
        "published_label_conflicts": conflicts,
        "hub_findings": hub,
        "vpic_model_series_sweep": vp.get("sweep", {}),
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s = doc["summary"]
    print(f"rules {s['rules']} {s['rules_by_status']}")
    print(f"newly confirmed manual (keep+low_sample): {s['newly_confirmed_manual_keep_and_low_sample_rules']}  candidate-only: {s['newly_confirmed_manual_candidate_rules_only']}  canadian not counted: {s['canadian_yard_cars_not_counted']}")
    print("by rule:", json.dumps(s["newly_confirmed_manual_by_rule"]))
    print("manual-claim precision (kept):", json.dumps(s["ground_truth_precision_manual_claims_kept_rules"]))
    print("published labels contradicting:", s["published_labels_contradicting_a_rule"])
    for x in out_rules:
        v = x["validation"]
        print(f"  {x['id']}: {x['status']} in_scope={v['in_scope_lot_cars']} chk={v['checkable_ground_truth']} raw={v['raw_including_vpic_defaults']} epa_ok={v['epa_cell']['all_rule_years_meet_mode']} failing={v['epa_cell']['years_failing']} vpic={ {k: v['vpic_check'][k] for k in v['vpic_check'] if k not in ('expect', 'inconsistent_examples')} }")
    print("hub: vPIC HK manual lines", hub["hk_vpic_manual_labels"]["lines"], hub["hk_vpic_manual_labels"]["by_vpic_model_year"], hub["hk_vpic_manual_labels"]["epa_check"])
    print("hub: vPIC HK automatic lines where EPA lists a manual", hub["hk_vpic_automatic_labels_epa_lists_manual"]["lines"])
    print("scan:", s["scan"])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
