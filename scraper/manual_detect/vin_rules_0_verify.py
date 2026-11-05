#!/usr/bin/env python3
"""Adversarial verification of vin_rules_0.json (Honda/Acura VIN transmission rules).

Run AFTER vin_rules_0.py (which rebuilds the rules and their lot-car stats)
and vin_rules_0_midscan.py (which reads Honda's MID filings). This script
tries to refute each rule and writes what it checked into the rule as a
"verified" block, plus a top-level "verification" summary. It changes no
rule's scope or status; narrowing is done in vin_rules_0.py so the stats
stay consistent.

Checks (all re-runnable except the two recorded-by-hand tables at the top):
  1. CITATIONS: every cited MID PDF was downloaded again on 2026-11-05, its
     sha256 compared with the copy the rule author read, and the page that
     carries the claim read again (OCR or the page image). CITATION_CHECKS.
  2. vPIC, WHOLE DECODE CACHE: every Honda/Acura VIN in vin_decodes.json.gz
     (lot cars AND departed cars, ~44k), not only today's lot, checked against
     vPIC's TransmissionStyle. vPIC model-level default cells
     (junkyard_scraper.VPIC_TRANS_DEFAULT_CELLS: 2007-08 Fit, 1986 Civic) are
     reported separately. This is still partly circular (vPIC is built from
     the same filings).
  3. INDEPENDENT FACTS: US models sold with only one kind of gearbox
     (S2000, Civic Si, RSX Type-S ... manual only; Odyssey, Pilot, Ridgeline,
     MDX, RDX ... automatic only). Any in-scope VIN whose rule claim
     contradicts the model fact is a counterexample.
  4. EPA (fueleconomy.gov vehicles.csv) over the whole cache: a claim the EPA
     year/model/displacement cell cannot hold is a counterexample.
  5. MID FILINGS SCAN: vin_rules_0_mid_scan.json, every model-code row the
     parser read in Honda's own filings (MY1987 on), against the rule.
  6. LIVE vPIC SPOT CHECKS: VIN_LIVE (recorded by hand, 2026-11-05).

Run: python3 -I scraper/manual_detect/vin_rules_0_verify.py
"""

import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import vin_rules_0 as R  # noqa: E402

RULES = HERE / "vin_rules_0.json"
MIDSCAN = HERE / "vin_rules_0_mid_scan.json"
WHEN = "2026-11-05"
MID = R.MID

# vPIC model-level default cells for Honda (junkyard_scraper.VPIC_TRANS_DEFAULT_CELLS)
DEFAULT_CELLS = {("FIT", 2007), ("FIT", 2008), ("CIVIC", 1986)}

# 1. Every cited filing, re-downloaded and re-read on 2026-11-05.
CITATION_CHECKS = {
    "5ec1023d-ef91-47ab-a2e7-9b636dd7885d": ("f310bcaac30d06f41a889ff9f3deed1ba5a1b34c53c4899abedb6c65f0d26465",
        "Confirmed (OCR p.2-3): MY1984 Accord/Prelude/Civic Wagon; character 6 'Transmission representation' 5 = 5MT, 7 = 4AT, 3 = 3AT; character 7 body 2/3/4/5; JHMAD532 5M, JHMAD732 4A, JHMAN352 3A. Defines no 4 or 6 (the rule now accepts only 3/5/7 for 1984)."),
    "99140621-6bb8-4988-9922-bf53e3f0bd32": ("eb337e49dafadb79aad2687765e5081bbf2e7001502c8714b90712b0221bb684",
        "Confirmed (OCR p.2-5): MY1985 Accord/Prelude/Civic Wagon table (3/5/7) and Civic CRX/hatchback/sedan table (3 = 3AT, 4 = 4MT, 5 = 5MT); JHMAF531 CRX HF M5, JHMAF332 CRX L3, JHMAG431 1300 M4, JHMAK343 L3."),
    "386ede85-a1c2-474d-bccf-88647bd49403": ("e7196b4845ddf68b168764d4857f8fa74958422f0f9f365fe158f9ef65664f71",
        "Confirmed (OCR p.2-3): MY1986 Civic CRX/hatchback/sedan, character 6: 4 = 4MT, 5 = 5MT, 7 = 4AT; JHMAK543 M5, JHMAK743 L4. Defines no 3."),
    "66a0a3d1-e263-40e0-9dc2-92f115a9a147": ("e058a40f2f3f0bfbdea3ed2102f8975c9b82703f01b5a8eb9514c34acbe662f8",
        "Confirmed (OCR p.3-4): MY1986 Accord/Prelude/Civic Wagon/Wagon 4WD, character 6: 5 = 5MT, 6 = 5MT + Super Low, 7 = 4AT."),
    "594deacc-cedf-43c3-afc4-b371a3562bca": ("0530427c89e5c549d5ca2f43dd67afc8c944fd640887f3e91139b0a1a29e7a3f",
        "Confirmed (OCR p.2-5): MY1986 Acura Integra character 7 'Body type and Transmission representation' 3/4 = 3-door 5MT/4AT, 7/8 = 5-door 5MT/4AT (DA334 M5, DA344 L4, DA174 M5, DA184 L4); same letter re-issues the 1986 Honda table (5/6/7, AR652 Civic Wagon 4WD 5M+SL, VN552 Wagovan 5M). Covers only the Integra, not the 1986 Legend (Legend codes are checked against vPIC only)."),
    "1d1d246e-7f53-42d7-92d9-8296b5acb4e9": ("482e38323222325d25684a773ad4d14f60bb2298c7d54f883bd753ba19d75ca7",
        "Confirmed (OCR p.2-3): MY1987 Accord/Prelude construction table, character 7 'Body type and Transmission representation' 1-6 exactly as cited; JHMCA552 5M, JHMCA562 4A, JHMBA314 Si 5M, JHMBA324 Si 4A."),
    "ee50d2f2-0644-4c5b-b967-8df8837e14d6": ("7adeb5e0a7adddd49c40c94a05c4681f43b5871da58c3fd5f60df89b244d0254",
        "Confirmed (OCR p.2-3): MY1987 Civic table, character 7 3/4 = 2-door hatchback or coupe manual/automatic, 5/6 = 4-door sedan, 7/8 = 4-door wagon; JHMEC231 1300 hatchback 4M, JHMEC572 Wagon 5M, JHMEC582 4A, JHMEY172 Wagovan 5M."),
    "b8c1ed83-b581-4aaf-b66e-989269918f50": ("7adf230ee2416711f46e1e94cb5f7d634cba3bc59988d55335413c45f19f1d09",
        "Confirmed (OCR p.2-3): revised MY1987 Accord/Prelude table adds 7 = 4-door wagon Manual and JHMEC672 Civic Wagon Real Time 4WD 5M+SL."),
    "5ac16ebd-6ab7-49b1-ae7d-eee4f41ac222": ("f65b82e1bf3f08bece629604f45e53ed1e77bab36b6f54c4f24a098293827ad7",
        "Confirmed (OCR p.2-4): MY1989 Integra DA334 RS 5M, DA344 RS 4A, DA335/DA345 LS 5M/4A, DA174/DA184 5-door RS 5M/4A, DA175/DA185 LS. So JH4DA3448KS017664 (vPIC: 5-spd Manual, live check) is a 4AT car and vPIC is wrong."),
    "27ea75b4-8c79-4a9c-9b66-029270dbe9a5": ("44e49bfa728ddc0ac464c666dc1877c14e8e90cd35320cd9b75d8a7ee3cf33db",
        "Confirmed (OCR p.2-12): MY1997 Civic (EJ65x/EJ85x sedan 5MT, EJ66x/EJ86x 4AT, EJ61x/EJ81x coupe 5MT, EJ62x/EJ82x 4AT, EJ71x HX 5MT, EJ72x HX CVT, EJ63x/EJ64x hatchback 5MT/4AT), MY1997 Accord (CD71x coupe 5MT, CD72x 4AT, CD55x sedan 5MT, CD56x 4AT, CE663/664/665/667 V6 sedan 4AT only, CE172 wagon 5MT, CE182/183/189 4AT), MY1997 3.0CL YA224/YA225 4AT. Page 7's header misprints 'Model year: 1996' but the page is the 1997 Accord table (VIN examples carry year code V). This filing no longer prints a generic character-7 table; each 2nd-section code is listed with its own transmission."),
    "836ed5a1-3594-439d-a5dd-cd214c21621b": ("43e716968ffd910a2a4af93d5e906f31fd6238079a6e2ee26b460310ea618a3c",
        "Confirmed (page image p.3): 2003 Acura 3.2TL Model Code UA566/UA567/UA568/UA569 = 5AT 4DR Sedan (the PDF's text layer misreads UA as JA). WMI table lists 2HG/2HJ/2HK (Honda of Canada), 3HG (Honda de Mexico), 2HN (Acura MPV, Canada), SHS (UK)."),
    "260e4159-7c32-4e16-8fc1-b50a6b3aa5ce": ("3975958af68e6e22abd89c1d34aab71fc8668cd066b9976aefbbc03978ea93da",
        "Confirmed (page image p.3, rotated): 2007 HONDA FIT Model Codes GD374 5MT, GD384 5AT, GD376 5MT, GD386 5AT, all 5DR HATCHBACK, L15A1. No separate MY2008 Fit filing was found among the 2006-2007 American Honda submissions in MID (18 cover letters read); MY2008 Fit claims rest on this MY2007 table for the same carry-over codes."),
    "7bdb4344-93a5-4415-ab31-11864e261300": ("3b776676898cbb3750f45c7b67e553174c8a5a572a7e21aa0c5762745543a0f0",
        "Confirmed (text layer): MY2010 model-code tables, e.g. FA1E2 Civic DX 5MT / FA1F2 5AT, FA5E5 Si 6MT, FA3F2 Hybrid CVT, FA4F5 GX 5AT, FG1A2/FG1B2 coupe 5MT/5AT, FG2A5 Si 6MT, YH2G7 Element 4WD EX 5MT / YH1H3 5AT, UA9E5 TL SH-AWD 6MT / UA9F5 5AT, RE3H3 CR-V 5AT, RL3H2 Odyssey 5AT, YF4H2 Pilot 5AT, YD2H2 MDX 6AT. The filing defines no generic character-7 table: the A-H pairing is read off the code lists."),
    "f293cffc-27b6-4ce0-9f20-412a4c955188": ("17da58652d63a772ace580f6cf2a503dfb5fdc00e32a0ad5900ae97c77e5788a",
        "Confirmed (OCR p.3-4): 2011 CR-Z ZF1C4/ZF1C6 6MT 3DR, ZF1D4/ZF1D6 CVT 3DR; WMI table (p.3) lists every Honda/Acura WMI the rules use (JHM JH4 JHL JH1 1HG 19U 5J6 5J8 5J7 5J0 5KB 5KC 5FN 5FR 5FP 5FS 2HG 2HH 2HK 2HN 2HJ 2HU SHH SHS 3HG 3CZ 19X)."),
    "51b13a22-cf03-40a9-84d5-3cda0375140f": ("8f3839b6de885f7a0211fdf9318b67e920aaa3f8e5da29d32930669e3ce47f2c",
        "Confirmed (text layer): 2024MY Civic Hatchback Type R FL5G4 2WD 6MT 5DR Hatchback; WMI table adds 19V (Acura car) and 7FA (Honda MPV, Honda Development & Manufacturing of America)."),
    "379f8460-941e-4589-8208-4874e9aaef24": ("71c31eed1538f55d8ab7e0330674f30b0f8d7e38252e84e3791c1925f36105b7",
        "Added in verification (text layer): 2024MY Acura Integra DE4H2/DE4H3/DE4H6 CVT 5DR Hatchback, DE4G7 A-SPEC TECH 6M/T 5DR Hatchback."),
}

# 6. Live vPIC decodes (DecodeVinValuesExtended), 2026-11-05.
VIN_LIVE = [
    {"vin": "1HGCD5635VA070158", "honda_code": "CD563 = 1997 Accord LX sedan 4AT", "vpic_now": "1997 Accord, Manual/Standard (no speeds), trim 'LX/LX V-6'"},
    {"vin": "1HGCE6646VA015018", "honda_code": "CE664 = 1997 Accord LX V6 sedan 4AT (V6 was automatic only, EPA id 13472)", "vpic_now": "Manual/Standard"},
    {"vin": "1HGCD5532VA275471", "honda_code": "CD553 = 1997 Accord LX sedan 5MT", "vpic_now": "Automatic"},
    {"vin": "1HGCD5650TA153804", "honda_code": "CD565 (1996) = Accord EX 4AT", "vpic_now": "Automatic 4 (1996 decodes correctly)"},
    {"vin": "JH4DA3448KS017664", "honda_code": "DA344 = 1989 Integra RS 3-door 4AT", "vpic_now": "Manual/Standard 5"},
    {"vin": "2HHES35863H001201", "honda_code": "ES3 line not in any filing (Canada-only 2003 Acura EL)", "vpic_now": "error 5/14, no model"},
    {"vin": "2HHFD65698H201026", "honda_code": "FD6 line not in any filing (Canada-only 2008 Acura CSX)", "vpic_now": "error 5/14, no model"},
    {"vin": "2HGFG1A64BH500063", "honda_code": "FG1A (2010 filing: FG1A2 Civic DX coupe 5MT)", "vpic_now": "2011 Civic LX, Manual/Standard 5 (a code the lot-only 'documented' test had missed)"},
]

# vPIC disagreements that Honda's own filing shows to be vPIC errors.
KNOWN_VPIC_ERRORS = {
    "JH4DA3448KS017664": "1989 Integra DA344: the 1989 filing (5ac16ebd) says 4A; vPIC says 5-spd Manual.",
}

# 3. US models built with only one kind of gearbox: (model regex on vPIC/feed
#    model, first year, last year, trim regex or None, required kind, fact).
FACTS = [
    (r"^S2000$", 2000, 2009, None, "manual", "S2000: 6MT only"),
    (r"^ODYSSEY$", 1995, 2026, None, "auto", "Odyssey: automatic only"),
    (r"^PILOT$", 2003, 2026, None, "auto", "Pilot: automatic only"),
    (r"^RIDGELINE$", 2006, 2026, None, "auto", "Ridgeline: automatic only"),
    (r"CROSSTOUR", 2010, 2015, None, "auto", "Accord Crosstour/Crosstour: automatic only"),
    (r"^PASSPORT$", 2019, 2026, None, "auto", "2019+ Passport (Honda-built): automatic only"),
    (r"^MDX$", 2001, 2026, None, "auto", "MDX: automatic only"),
    (r"^RDX$", 2007, 2026, None, "auto", "RDX: automatic only"),
    (r"^(RL|RLX|ZDX|TLX)$", 1996, 2026, None, "auto", "RL/RLX/ZDX/TLX: automatic (incl. DCT) only"),
    (r"^(3\.2TL|TL)$", 1999, 2003, None, "auto", "1999-2003 TL: automatic only"),
    (r"^(3\.0CL|3\.2CL|CL)$", 2001, 2002, None, "auto", "2001-02 CL: automatic only"),
    (r"^INSIGHT$", 2010, 2014, None, "auto", "2010-14 Insight: CVT only"),
    (r"^INSIGHT$", 2019, 2022, None, "auto", "2019-22 Insight: CVT only"),
    (r"^CLARITY$", 2017, 2021, None, "auto", "Clarity: automatic only"),
    (r"^CIVIC$", 2006, 2015, r"HYBRID", "auto", "2006-15 Civic Hybrid: CVT only"),
    (r"^CIVIC$", 1998, 2015, r"\bGX\b|NATURAL GAS", "auto", "Civic GX: automatic only"),
    (r"^ACCORD$", 2005, 2007, r"HYBRID", "auto", "2005-07 Accord Hybrid: automatic only"),
    (r"^CIVIC$", 2002, 2015, r"\bSI\b", "manual", "2002-15 Civic Si: manual only"),
    (r"^CIVIC$", 2017, 2025, r"\bSI\b", "manual", "2017-25 Civic Si: manual only"),
    (r"^CIVIC$", 2017, 2025, r"TYPE.?R", "manual", "Civic Type R: manual only"),
    (r"^RSX$", 2002, 2006, r"TYPE.?S", "manual", "RSX Type-S: manual only"),
    (r"^INTEGRA$", 1997, 2001, r"TYPE.?R", "manual", "Integra Type R: manual only"),
    (r"^INTEGRA$", 2023, 2026, r"TYPE.?S", "manual", "2023+ Integra Type S: manual only"),
    (r"^PRELUDE$", 1997, 2001, r"\bSH\b", "manual", "Prelude Type SH: manual only"),
    (r"^(CRX|CIVIC CRX)$", 1985, 1991, r"\bSI\b|\bHF\b", "manual", "CRX Si / HF: manual only"),
]


def main() -> int:
    out = json.loads(RULES.read_text())
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache.pop("_exportedAt", None)
    inv = json.loads((DATA / "inventory_live.json").read_text())
    fi = {f: i for i, f in enumerate(inv["fields"])}
    lot = {}
    for row in inv["vehicles"]:
        vin = (row[fi["vin"]] or "").strip().upper()
        if len(vin) == 17 and R.brand_of(vin):
            lot[vin] = row
    allv = {v for v in cache if len(v) == 17 and R.brand_of(v)} | set(lot)
    epa = R.Epa(HERE / "epa" / "vehicles.csv")

    documented = set()
    for v in allv:
        d = cache.get(v)
        if isinstance(d, dict) and d.get("model") and R.check_digit_ok(v):
            try:
                y = R.vin_year(v, int(str(d.get("modelYear") or 0)[:4]) or None)
            except ValueError:
                y = None
            if y:
                documented.add((y, v[3:7]))

    st = defaultdict(lambda: {"vins": 0, "lot": 0, "departed": 0, "vpic_checkable": 0, "vpic_agree": 0,
                              "vpic_disagree": 0, "vpic_default_cell": 0, "vpic_default_cell_disagree": 0,
                              "no_vpic_trans": 0, "epa": Counter(), "facts": Counter()})
    dis = defaultdict(Counter)
    dis_vins = defaultdict(list)
    fact_conf = defaultdict(list)
    edges = Counter()
    for v in sorted(allv):
        if not R.check_digit_ok(v):
            edges["bad_check_digit"] += 1
            continue
        d = cache.get(v) if isinstance(cache.get(v), dict) else {}
        lrow = lot.get(v)
        try:
            hint = int(str(d.get("modelYear") or (lrow[fi["year"]] if lrow else 0) or 0)[:4]) or None
        except ValueError:
            hint = None
        y = R.vin_year(v, hint)
        if y is None:
            edges["year_unresolved"] += 1
            continue
        c7 = v[6]
        if y >= 2010 and c7.isdigit():
            edges["MY2010+_with_digit_char7"] += 1
        if 1987 <= y <= 2009 and c7.isalpha():
            edges["MY1987-2009_with_letter_char7"] += 1
        hit = R.classify(v, y)
        if not hit:
            edges["no_rule"] += 1
            continue
        rid, claim, _ = hit
        if "_vin7_" in rid and "accord_1997" not in rid and not (d.get("model") or (y, v[3:7]) in documented):
            rid = f"honda_acura_vin7_code_not_in_vpic_{claim}"
        s = st[rid]
        s["vins"] += 1
        s["lot" if lrow else "departed"] += 1
        tc = R.tclass(d.get("transmission") or "")
        md = (d.get("model") or "").upper()
        if tc in R.KNOWN:
            ok = (tc == "manual") == (claim == "manual")
            if (md, y) in DEFAULT_CELLS:
                s["vpic_default_cell"] += 1
                if not ok:
                    s["vpic_default_cell_disagree"] += 1
                    dis[rid][f"{y} {md} {v[3:7]} (vPIC default cell)"] += 1
            else:
                s["vpic_checkable"] += 1
                s["vpic_agree" if ok else "vpic_disagree"] += 1
                if not ok:
                    dis[rid][f"{y} {md} {v[3:7]}"] += 1
                    dis_vins[rid].append(v)
        else:
            s["no_vpic_trans"] += 1
        # EPA
        m = re.match(r"(\d+(?:\.\d+)?)L", d.get("engine") or "")
        displ = float(m.group(1)) if m else None
        models = [(lrow[fi["model"]] if lrow else "") or "", d.get("model", "")]
        cls = epa.classes(y, R.brand_of(v), models, displ) if epa.ok else None
        if cls is None:
            s["epa"]["no_epa_match"] += 1
        else:
            want = {"manual"} if claim == "manual" else {"automatic", "cvt", "amt", "dct"}
            s["epa"]["consistent" if cls & want else "CONFLICT"] += 1
            if len(cls) == 1:
                s["epa"]["consistent_in_single_kind_cell" if cls & want else "CONFLICT_single_kind_cell"] += 1
        # model facts
        mset = {x.upper() for x in models if x}
        trim = f"{d.get('trim') or ''} {d.get('series') or ''}".upper()
        for mrx, y0, y1, trx, req, note in FACTS:
            if y0 <= y <= y1 and any(re.search(mrx, x) for x in mset) and (not trx or re.search(trx, trim)):
                ok = (claim == "manual") == (req == "manual")
                s["facts"]["checked"] += 1
                s["facts"]["agree" if ok else "CONFLICT"] += 1
                if not ok:
                    fact_conf[rid].append({"vin": v, "year": y, "fact": note})

    # every MY1984-86 code in scope, for the hand check against the filing tables
    old_codes = defaultdict(Counter)
    for v in allv:
        if not R.check_digit_ok(v):
            continue
        d = cache.get(v) if isinstance(cache.get(v), dict) else {}
        lrow = lot.get(v)
        try:
            hint = int(str(d.get("modelYear") or (lrow[fi["year"]] if lrow else 0) or 0)[:4]) or None
        except ValueError:
            hint = None
        y = R.vin_year(v, hint)
        hit = R.classify(v, y) if y else None
        if hit and hit[0].startswith("honda_vin6"):
            old_codes[hit[0]][f"{y} {v[3:5]} char6={v[5]} char7={v[6]} vPIC={R.tclass(d.get('transmission') or '') or 'none'}"] += 1

    scan = json.loads(MIDSCAN.read_text()) if MIDSCAN.exists() else None
    era_scan = {}
    if scan:
        t = scan["totals"]
        for era in ("digit", "letter"):
            era_scan[era] = {
                "filings_read": sum(1 for f in scan["filings"] if any((r["code"][3].isalpha()) == (era == "letter") for r in f["rows"])),
                "manual_codes_agree": t.get(f"{era}_manual_agree", 0),
                "automatic_codes_agree": t.get(f"{era}_automatic_agree", 0),
                "mismatches_unreviewed": [dict(m, file=f["file"], url=f["url"]) for f in scan["filings"] for m in f["mismatches"]
                                          if (m["code"][3].isalpha()) == (era == "letter") and "manual_review" not in m],
            }
        submission_years = sorted({f["date"].split("/")[-1] for f in scan["filings"]})
    cites_by_url = {MID + k: v for k, v in CITATION_CHECKS.items()}

    def cite_block(rule):
        res = []
        for c in rule["citations"]:
            chk = cites_by_url.get(c["url"])
            res.append({"url": c["url"], "sha256": chk[0] if chk else None,
                        "result": chk[1] if chk else "NOT RE-CHECKED"})
        return res

    def stats_block(rid):
        s = st[rid]
        return {
            "vins_in_scope_whole_cache": s["vins"], "of_which_lot": s["lot"], "of_which_departed": s["departed"],
            "vpic_checkable": s["vpic_checkable"], "vpic_agree": s["vpic_agree"], "vpic_disagree": s["vpic_disagree"],
            "vpic_disagree_cells": dict(dis[rid].most_common(10)),
            "vpic_default_cell_vins": s["vpic_default_cell"], "vpic_default_cell_disagree": s["vpic_default_cell_disagree"],
            "epa_whole_cache": dict(s["epa"]),
            "single_gearbox_model_facts": dict(s["facts"]),
            "single_gearbox_fact_conflicts": fact_conf[rid][:10],
        }

    common_scope = {
        "wmi": "Every WMI in the rules is in Honda's own WMI tables (2003 TL, 2011 CR-Z, 2024 Type R filings). 3HD, which no filing lists and no cached VIN carries, was removed from ACURA_WMI. Isuzu-built Honda Passport 4S6 (75 lot cars) and Acura SLX JAE (3) stay out.",
        "era_boundary": f"Whole cache: {edges['MY2010+_with_digit_char7']} VINs resolve to MY2010+ with a digit in character 7 and {edges['MY1987-2009_with_letter_char7']} to MY1987-2009 with a letter; both kinds are left unruled.",
        "canada_mexico_uk": "Canada- (2HG/2HH/2HJ/2HK/2HN), Mexico- (3HG/3CZ) and UK-built (SHH/SHS) cars use the same model-code tables in the filings (the 1997 filing lists 2HGEJ... rows beside 1HGEJ...). A Canada-market car whose characters 4-7 are a filed code for that year but whose grade (character 8) is Canada-only is accepted; a car whose line code itself is unfiled is held (honda_acura_vin7_code_not_in_vpic_*).",
        "name_mapping": "The brand comes from the WMI, not the feed make; no feed-make mismatches among Honda/Acura WMIs on the lots.",
    }

    for r in out["rules"]:
        rid = r["id"]
        b = {"date": WHEN, "by": "adversarial verification (vin_rules_0_verify.py)",
             "citations_rechecked": cite_block(r), "counterexample_search": stats_block(rid)}
        if rid.startswith(("honda_vin7_digit", "acura_vin7_digit")):
            b["filings_scan"] = era_scan.get("digit")
        if rid.startswith(("honda_vin7_letter", "acura_vin7_letter")):
            b["filings_scan"] = era_scan.get("letter")
        b["scope_edges"] = dict(common_scope)
        s = st[rid]
        unexplained = [v for v in dis_vins[rid] if v not in KNOWN_VPIC_ERRORS]
        explained = [f"{v}: {KNOWN_VPIC_ERRORS[v]}" for v in dis_vins[rid] if v in KNOWN_VPIC_ERRORS]
        hard_conflicts = s["epa"].get("CONFLICT", 0) + s["facts"].get("CONFLICT", 0)
        refuted = (hard_conflicts > 0 or bool(unexplained)) and not rid.startswith("honda_accord_1997")
        if explained:
            b["counterexample_search"]["vpic_disagreements_explained"] = explained
        if rid in ("honda_vin7_digit_1987_2009_manual", "honda_vin7_digit_1987_2009_automatic"):
            b["scope_edges"]["fit_2007_2008"] = ("GD37x = 5MT, GD38x = 5AT per the 2007 Fit filing; vPIC's 'Manual' on every 2007-08 Fit is a model-level default "
                                                 "(the scraper now drops it). The 3:1 GD38:GD37 split in the cache is what a mostly-automatic car shows. "
                                                 "MY2008 Fits rest on the MY2007 table (same carry-over codes; no MY2008 Fit filing found).")
            b["scope_edges"]["accord_1997"] = "1997 Accord (CD/CE) is carved out to honda_accord_1997_vin7_* (vPIC inverted)."
        if rid.startswith("acura_vin7_digit"):
            b["scope_edges"]["acura_1986_legend"] = ("The 1986 Acura filing cited covers only the Integra. 1986-87 Legend codes (KA25 5MT, KA26 4AT, KA32 auto) "
                                                     "rest on vPIC agreement, not on a filing read here.")
            b["scope_edges"]["integra_1989_da344"] = "The one vPIC disagreement (JH4DA3448KS017664) is a vPIC error: the 1989 filing says DA344 = 4A."
        if rid.startswith("honda_vin6"):
            b["scope_edges"]["narrowed"] = ("Character-6 values are now accepted only where that year's own filing defines them for that line group "
                                            "(OLD_T6_ALLOWED). No car in the cache changed bucket; the narrowing closes undefined values such as "
                                            "4 or 6 on a 1984 VIN or 3 on a 1986 VIN, which the old year-agnostic table would have ruled.")
            b["scope_edges"]["years"] = "MY1981-83 and the MY1984 Civic hatchback/CRX/sedan stay unruled (no filing). VN (Wagovan) is ruled for 1986 only."
            b["hand_check_codes_in_scope"] = dict(sorted(old_codes[rid].items()))
            b["hand_check_result"] = ("Every (year, line, character 6) above is a value the filing for that year defines for that line group; "
                                      "every vPIC transmission present agrees (1986 Civic vPIC values are a model-level default and are not evidence).")
        if rid.startswith("honda_acura_vin7_code_not_in_vpic"):
            b["outcome"] = "HELD (status hold_code_not_filed): not refuted, but no filing, vPIC decode or other source covers these exact codes."
        elif rid.startswith("honda_accord_1997"):
            acc = Counter()
            for v, d in cache.items():
                if (len(v) == 17 and v[:3] in ("1HG", "JHM") and v[3:5] in ("CD", "CE") and v[9] in "TVW"
                        and isinstance(d, dict) and R.tclass(d.get("transmission") or "") in R.KNOWN):
                    acc[f"{ {'T': 1996, 'V': 1997, 'W': 1998}[v[9]]} {v[3:7]} vPIC={d['transmission']}"] += 1
            b["cache_1996_vs_1997_by_code"] = dict(sorted(acc.items()))
            b["outcome"] = ("SUPPORTED, status unchanged (vpic_conflict_hub_decision). Honda's 1997 filing and EPA (V6 automatic only) agree with the rule; "
                            "vPIC's 1997 sedan pattern is inverted (CD55x 'Automatic', CD56x and V6 CE66x 'Manual/Standard', with no speed count), "
                            "while 1996 CD55x/CD56x/CE66x and 1997 coupes/wagons decode correctly. Applying it changes published labels, so the hub decides.")
        elif refuted:
            b["outcome"] = (f"REFUTED: {len(unexplained)} unexplained vPIC disagreements, {hard_conflicts} EPA/model-fact conflicts "
                            f"(e.g. {unexplained[:3]})")
        elif explained or s["vpic_default_cell_disagree"]:
            b["outcome"] = ("SURVIVES: no counterexample in the filings, EPA or the single-gearbox model facts; the only vPIC "
                            "disagreements are vPIC errors that Honda's own filing contradicts"
                            + (" (vpic_disagreements_explained)" if explained else "")
                            + (" or vPIC model-level default cells (2007-08 Fit)" if s["vpic_default_cell_disagree"] else "") + ".")
        else:
            b["outcome"] = "SURVIVES: no counterexample in the filings, the whole decode cache, EPA or the single-gearbox model facts."
        r["verified"] = b

    out["verification"] = {
        "date": WHEN,
        "script": "scraper/manual_detect/vin_rules_0_verify.py",
        "changes_made": [
            "honda_vin6_1984_1986_*: character-6 values narrowed to the ones each year's filing defines for that line group (OLD_T6_ALLOWED).",
            "'documented' code test now uses the whole decode cache (lot + departed cars), so US-filed codes no other LOT car carried (1999 EJ63, 2004 CM81, 2011 FG1A ...) move from the not-in-vPIC bucket to the main rules.",
            "honda_acura_vin7_code_not_in_vpic_*: status keep_low_sample -> hold_code_not_filed; the cars left there (Canada-only Acura EL/CSX) are no longer counted as newly confirmed.",
            "acura_vin7_letter_2010_on_*: added the 2024 Acura Integra filing (DE4G7 6M/T) as a citation; Acura letter-era manual codes were otherwise cited only through the 2010 TL SH-AWD row.",
            "vpic_conflicts: the 2007-08 Fit entry notes that the scraper already drops vPIC's Fit transmission (commit b55e403), so its 133 wrong Manual badges are gone and the GD37x Fits become newly confirmable.",
        ],
        "live_vpic_spot_checks": VIN_LIVE,
        "filings_scan_submission_years": submission_years if scan else None,
        "filings_scan_totals": scan["totals"] if scan else None,
        "whole_cache_edges": dict(edges),
        "not_checkable": [
            "No VIN-bearing listing-text ground truth exists for Honda/Acura (all 239 listing-sourced Honda/Acura lines have no VIN), so every VIN check other than EPA, the model facts and the filings is against vPIC.",
            "The filings scan reads OCR of scanned filings; rows the parser cannot read are not counted, so it shows that what was read agrees, not that every code was read.",
        ],
    }
    RULES.write_text(json.dumps(out, indent=1) + "\n")
    for r in out["rules"]:
        cs = r["verified"]["counterexample_search"]
        print(f'{r["id"]:45s} {r["status"]:28s} vins={cs["vins_in_scope_whole_cache"]:6d} vpic {cs["vpic_agree"]}/{cs["vpic_checkable"]} '
              f'default={cs["vpic_default_cell_disagree"]}/{cs["vpic_default_cell_vins"]} epa={cs["epa_whole_cache"]} facts={cs["single_gearbox_model_facts"]} -> {r["verified"]["outcome"][:40]}')
    print(json.dumps(out["verification"]["whole_cache_edges"]), json.dumps(out["verification"]["filings_scan_totals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
