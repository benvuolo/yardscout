#!/usr/bin/env python3
"""Adversarial verification of epa_sole.json (manual-detection track 2).

Run AFTER epa_sole.py (which reads epa_sole_citations.json, where this pass
set Liberty 2.4 2003-05 and Wrangler TJ 2.4 2005-06 to 'contradicts' and
Cougar 2.0 2001-02 to 'conflicting'):

    python3 -I scraper/manual_detect/epa_sole.py
    python3 -I scraper/manual_detect/epa_sole_verify.py

What it does to epa_sole.json (idempotent):
  * moves every rule with status 'drop' out of `rules` into `refuted_rules`
    (with the reason), so `rules` holds only surviving rules;
  * adds a `verified` block to every surviving rule: the per-rule checks made
    by hand in this pass (citations re-opened, live vPIC decodes, scope edges)
    plus computed checks re-run every time:
      - ground truth: VIN lines in the rule's scope (vPIC make/model, years,
        displacement) whose transmission is not manual  -> counterexamples;
      - vPIC decode cache: in-scope decodes that carry a non-manual
        transmission label  -> counterexamples;
      - VIN-pattern collision: for every VDS pattern (VIN 4-8) + model year
        seen with the rule's displacement, decodes of the same pattern with a
        different displacement (the decoded engine would be a guess);
  * adds a top-level `verification` block and refreshes the rule counts.
Nothing here labels a car beyond what epa_sole.py already counted; it can only
remove or annotate.
"""

import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "docs" / "data"
OUT = HERE / "epa_sole.json"
TODAY = "2026-11-05"

# ---- hand checks made in this pass (2026-11-05) --------------------------------------
# WebFetch could not resolve outside hosts (consumerguide.com etc.) from this session;
# text was read from WebSearch result text. vpic.nhtsa.dot.gov was reachable with curl
# (DecodeVinValues), so lot VINs were re-decoded live.
HAND = {
    "epa_dodge_caliber_1.8l_4cyl_anydrive": [
        "EPA re-read 2007-2009: the only 1.8 L rows are Manual 5-spd (23528, 24818, 25968); every CVT row is 2.0/2.4.",
        "New independent text (search-result text): Edmunds 2007 'the 1.8-liter ... paired to a five-speed manual only'; Cars.com: the CVT brings the 2.0 L. CarGurus' trim blurb (SE 'upgraded to the optional CVT' without an engine change) is generic and not tied to the 1.8.",
        "Decode cache: 1.8 L appears only with VIN 8 = C (lines B28 SE / B48 SXT, FWD); B/A = 2.0, K/F = 2.4. No pattern collision.",
        "Feed model 'Chrysler Caliber' (2 cars) is a yard naming slip; both VINs decode Dodge Caliber 1.8 (1B3HB28C).",
    ],
    "epa_jeep_wrangler_2.5l_4cyl_anydrive": [
        "EPA 1987-1995 re-read: every 2.5 L Wrangler row 1987-1993 is Manual 5-spd; the first 2.5 L automatic is 1994 (11513), so 1993 is the right upper edge.",
        "1987-1988 AMC-format VINs: position 4 = engine (H = 2.5, C = 4.2) and position 5 = transmission; live vPIC decode of 2BCHV81S2JB546027 returns 2.5 L, TransmissionStyle Manual/Standard, 5 speeds (VIN 5 = V). 1989-1993: VIN 8 = E (1989-90) / P (1991-93) = 2.5 L, S/T/M = 4.x L6.",
        "vin_rules_6 verifier re-read the MY1991 Chrysler filing and found the same; Wikipedia YJ and Extreme Terrain: automatic for the four-cylinder arrived in 1994.",
        "Brampton (2J4/2BC, Canada) and Toledo (1J4) builds both decode the same way; no counterexample.",
    ],
    "epa_chevrolet_metro_1.0l_3cyl_anydrive": [
        "EPA 1995-2001 re-read: every 1.0 L Metro row is Manual 5-spd; the 3-speed automatic is 1.3 L only. EPA 1994 (previous generation) lists a 1.0 L automatic, outside the rule.",
        "Live vPIC decode of 2C1MR2263W6701472 (1998): 1.0 L 3-cyl hatchback; vPIC notes '6 coded in 8th position twice' (GM's table also gives code 6 to a 1.6 L Toyota engine of another car line, WMI 1Y1/2CN), which cannot apply to WMI 2C1 + carline M. In the cache 1.0 L appears only with VIN 8 = 6 on MR22 hatchbacks; code 2 (1998-2000) and 9 (1995-97) decode 1.3 L.",
        "vin_rules_5 verifier: NRCan lists the 1995-2000 Metro/Firefly 1.0 only as M5; CAMI (Canada) build covered.",
    ],
    "epa_geo_metro_1.0l_3cyl_anydrive": [
        "Same facts as the Chevrolet Metro rule (EPA 1995-1997 1.0 L Manual 5-spd only; NRCan M5 only; Consumer Guide 1995-2001: automatic only with the 4-cylinder).",
        "Live vPIC decode of 2C1MR2266S6758873 (1995 Geo Metro LSi): 1.0 L 3-cyl in-line hatchback. The GM worklist keeps MY1995-1998 as VIN-rule candidates because the scanned engine tables are unreadable; this rule rests on vPIC's coded displacement, which is VIN-specific in the cache (code 6 = 1.0, code 9 = 1.3 on the same MR22 hatch line).",
        "Residual risk named: no MY1995-1997 GM filing was read in this pass.",
    ],
    "epa_ford_escape_2.0l_4cyl_anydrive": [
        "EPA 2001-2005 re-read: 2001-2004 2.0 L rows are all Manual 5-spd (2WD and 4WD); the first four-cylinder automatic is the 2005 2.3 L, outside the rule.",
        "Decode cache: 2.0 L only with VIN 8 = B; code 1 = 3.0 V6 (482 VINs) in every series. One 2001 lot car is U03 (XLT) with code B; live vPIC decode of 1FMYU03B31KB23314 returns XLT, 2.0 L 4-cyl SEFI-ZETEC, check digit valid. The claim follows the engine (2.0 L = manual only), not the trim, so it stands.",
        "vin_rules_4 verifier: Cars.com 2002 'the 2.0-liter four-cylinder engine teams only with a five-speed-manual shift'.",
    ],
    "epa_ford_focus_2.3l_4cyl_anydrive": [
        "EPA 2003-2008 re-read: 2003-2004 2.3 L rows list both transmissions (PZEV), 2005-2007 2.3 L rows are Manual 5-spd only; the 2005-2007 PZEV cars are filed as 2.0 L.",
        "Decode cache (1,000+ 2005-2007 Focus decodes): 2.3 L appears only on series P38 (ZX4 ST) with VIN 8 = Z; every other series decodes 2.0 L (code N). So a non-ST 2.3 L automatic cannot land in this rule.",
    ],
    "epa_ford_fiesta_1.0l_3cyl_anydrive": [
        "EPA 2014-2017: every 1.0 L Fiesta row is Manual 5-spd; Fiesta automatics are 1.6 L non-turbo.",
        "Decode cache: 1.0 L only with VIN 8 = E, on both sedan (P4B) and hatch (P4E) SE; vin_rules_4 verifier read Ford's MY2014-2017 filings (E = 1.0 L GTDI).",
    ],
    "epa_ford_focus_1.0l_3cyl_anydrive": [
        "EPA 2015: 1.0 L Focus rows are Manual 6-spd only; 2016 adds the 1.0 L automatic (36988), so the rule stays MY2015 only.",
        "Decode cache: 1.0 L only with VIN 8 = E; vin_rules_4 verifier read Ford's MY2015 filing.",
    ],
    "epa_nissan_xterra_2.4l_4cyl_anydrive": [
        "EPA 2000-2004: the only 2.4 L Xterra rows are 'Xterra 2WD Manual 5-spd'; every V6 cell lists both.",
        "Decode cache: 2.4 L only with VIN 4 = D (KA24DE) and VIN 8 = T (2WD); E/M = 3.3 L. vin_rules_2 verifier read Nissan's MY2001/2002 filings and Consumer Guide directly ('teamed only with a 5-speed manual').",
    ],
    "epa_nissan_xterra_2.4l_xcyl_anydrive": [
        "Same as the 4-cylinder Xterra rule (MY2000-2001 decodes carry no cylinder count): 2.4 L only with VIN 4 = D, VIN 8 = T; EPA 2.4 L rows Manual 5-spd only.",
    ],
    "epa_dodge_neon_srt_4_sx_2.0_2.4l_4cyl_anydrive": [
        "EPA 2003-2005: the 2.4 L 'Neon/SRT-4/SX 2.0' rows are Manual 5-spd only; the 2.0 L rows list both.",
        "Decode cache: 2.4 L only with VIN 8 = S on line ES66/AS66 (SRT-4); every other Neon decodes 2.0 L.",
    ],
    "epa_isuzu_rodeo_2.6l_4cyl_anydrive": [
        "EPA 1991-1997: every Rodeo 2.6 L row is 'Rodeo 2WD Manual 5-spd'; automatic rows are V6 only.",
        "Decode cache: 2.6 L only with VIN 8 = E (4ZE1) on lines G/K (4x2) body 8; vin_rules_1 verifier re-read Isuzu's MY1992/1995/1997 filings. Search (2026-11-05) found no source pairing the 2.6 with an automatic; Consumer Guide 1991-97 and Edmunds 1996 say manual only.",
        "Scope edge: the 2-door Amigo shares line G and had a 2.6 automatic from 1992, but its vPIC model is Amigo, so it cannot land in this rule.",
    ],
    "epa_kia_sportage_2.0l_xcyl_4wd": [
        "EPA 2005-2010: 'Sportage 4WD 2.0' is Manual 5-spd only every year; the 2.0 2WD rows list both, so the drive gate matters.",
        "Drive is VIN-specific: Kia's MY2005-2009 filings (read by the vin_rules_3 verifier) give VIN 5 E = 4WD, F = 2WD; live vPIC decode of KNDJE724X67233592 returns 2.0 L, 4WD. NRCan: Canadian Sportage 4X4 2.0 M5 only.",
        "Conflict checked: a Kia parts catalog lists '2.0 LX 4AT' and '2.0 LX AWD' trims separately, which does not pair the automatic with AWD; parts catalogs are not an allowed source and no review or spec source pairs a 2.0 4WD with an automatic.",
        "vPIC's MY2008 Kia transmission labels are a default (every 2.0 2WD decodes '5-spd Manual'), so the one agreeing 2008 ground-truth line is weak evidence.",
    ],
    "epa_kia_sportage_2.0l_4cyl_4wd": [
        "Same facts as the Sportage 2.0 4WD rule (MY2008 decodes carry a cylinder count). The single agreeing ground-truth line comes from vPIC's MY2008 default transmission label and is weak evidence; the rule rests on EPA + Cars.com + NRCan.",
    ],
    "epa_mazda_tribute_2.0l_4cyl_anydrive": [
        "EPA 2001-2004: every Tribute 2.0 L row (2WD and 4WD) is Manual 5-spd.",
        "Decode cache: 2.0 L only with VIN 8 = B; code 1 = 3.0 V6. Live vPIC decode of 4F2YU06B51KM32783: 2.0 L YFD, DX, 4WD.",
        "New independent text (search-result text): Autoblog 2002 'not available with an automatic'; Edmunds 2002; Cars.com 'only a five-speed-manual transmission is available with the four-cylinder'. vincheck.info's 'automatic optional on I4' is an unsourced VIN-report page and contradicts the reviews.",
    ],
    "epa_volkswagen_golf_gti_2.8l_6cyl_anydrive": [
        "EPA 2001-2004: the 2.8 L GTI rows are manual only (5-spd 2001, 6-spd 2003-2004); the Jetta VR6 automatics are a different model name.",
        "Live vPIC decodes of the 2 counted lot VINs (9BWDH61J..., Brazil-built): 2.8 L 6-cyl, emissions group 3VWXV02.8228 / 4VWXV02.8228; the 2004 car decodes model 'Golf', trim GTI.",
        "New independent text (search-result text): The Auto Channel 2003 GTI review (Tiptronic optional on the 1.8T), Cars.com 2003 trim list (VR6 only as 6-speed manual), Autoblog 2004 (VR6 six-speed only).",
        "MY2001 (12-valve, 5-speed) stays EPA-only and is not counted.",
    ],
    "epa_chevrolet_cobalt_2.0l_4cyl_anydrive": [
        "EPA 2005-2010: every 2.0 L Cobalt row (supercharged LSJ 2005-07, turbo LNF 2008-10) is a manual; the 2.2/2.4 rows carry the automatics.",
        "Decode cache: 2.0 L only with VIN 8 = P on coupe line AP; one cached VIN carries vPIC 'Manual/Standard' (agrees).",
    ],
    "epa_jeep_renegade_1.4l_4cyl_anydrive": [
        "EPA 2015-2018: 1.4 L rows (2WD and 4WD) are Manual 6-spd only; the 2.4 L rows are Automatic 9-spd.",
        "Decode cache: 1.4 L only with VIN 8 = H/W; 2 cached VINs carry vPIC '6-spd Manual' (agree). FCA's Renegade press release: the 1.4 MultiAir Turbo is paired with the six-speed manual, the 2.4 'exclusively' with the nine-speed automatic. Italy-built (ZAC) for the US market; the DDCT 1.4 is not a US configuration.",
    ],
    "epa_mazda_speed_3_2.3l_xcyl_anydrive": [
        "EPA 2010-2013: the only 2.3 L Mazda3-family rows are 'Speed 3' Manual 6-spd (2009 '3' 2.3 automatic is the non-turbo Mazda3 s, previous model year).",
        "Scope edge found: the two 2012 lot cars are JM1BL1L3 (VIN 7 = L, vPIC trim 'Touring/GS'), not BL1H3, so vin_rules_1's Mazdaspeed3 regex misses them. Live vPIC decode of JM1BL1L30C1630210: 2.3 L, EngineModel 'L3T Turbo Federal/Canada', Turbo = Yes; the feed also says Mazdaspeed3. L3T is fitted only to the Mazdaspeed3, which had no automatic (Wikipedia Mazdaspeed3; EPA). The trim string is vPIC's reading of VIN 7 and is not used.",
    ],
    "epa_nissan_frontier_2.4l_xcyl_4wd": [
        "EPA 1998-2004: 'Frontier 4WD 2.4' is Manual 5-spd only 1998-2000, then absent.",
        "Narrowed upstream to MY1998: the vin_rules_2 verifier found a Canadian spec page (auto123) listing an optional automatic for the 1999 4-cylinder 4x4, so EPA's manual-only 1999-2000 cells are not trusted; MY1998 rests on Consumer Guide ('initial 4x4s were manual-shift only').",
        "Drive is VIN-specific: Nissan's MY1998 filing gives VIN 8 Y = 4WD, S/T = 2WD; live vPIC decode of 1N6DD21Y9WC351130: 2.4 L, 4WD.",
    ],
    "epa_bmw_z4_3.2l_6cyl_anydrive": [
        "EPA 2006-2008: the 3.2 L Z4 rows (M Roadster / M Coupe) are Manual 6-spd only; SMG would be filed as an automatic and is absent.",
        "GoAuto 2006 (search-result text): the M roadster is manual-only, not available with SMG. Decode cache: one 3.2 L Z4 VIN (5UMBT935, trim Z4 M).",
    ],
    "epa_cadillac_cts_6.0l_8cyl_anydrive": [
        "EPA 2006-2007: the 6.0 L CTS row is Manual 6-spd only (CTS-V, LS2); the 2009+ 6.2 L CTS-V (automatic offered) is a different engine.",
        "Grassroots Motorsports 2004-2007 CTS-V buyer's guide: T56 six-speed the only choice. Decode cache: 6.0 L only on series DN.",
    ],
    "epa_ford_mustang_5.8l_8cyl_anydrive": [
        "EPA 2013-2014: the 5.8 L Mustang rows are Manual 6-spd only (Shelby GT500). vin_rules_4 verifier read Ford's MY2014 filing (Z = 5.8 L).",
    ],
    "epa_isuzu_amigo_all_engines": [
        "EPA 1990 Amigo rows (7335, 7336, 7408: 2.3 and 2.6, 2WD and 4WD) are all Manual 5-spd; 1992 adds an automatic on the RWD 2.6 (Wikipedia Isuzu MU), outside the rule.",
        "Live vPIC decode of JAACR01E0L9803444: 1990 Amigo 2.6 L 4ZE1, 4WD.",
    ],
    "epa_saturn_ion_2.0l_4cyl_anydrive": [
        "EPA 2004-2007: the 2.0 L Ion rows are Manual 5-spd only (Red Line, supercharged LSJ); 2.2/2.4 rows carry the automatics.",
        "Decode cache: 2.0 L only with VIN 8 = P on the Red Line coupe line (AY).",
    ],
}

REFUTE_NOTES = {
    "epa_jeep_liberty_cherokee_2.4l_4cyl_anydrive":
        "Refuted in verification: Wikipedia 'Jeep Liberty (KJ)' reports fleet 2.4 L Liberties with a 4-speed automatic and "
        "Cars.com 2004 says each engine teams with either transmission. Fleet builds carry the same engine code, so the "
        "decode cannot exclude them (vin_rules_6 removed its matching VIN rule for the same reason). 3 lot cars lose the "
        "proposed Manual label.",
    "epa_jeep_wrangler_tj_2.4l_4cyl_anydrive":
        "Refuted in verification: Extreme Terrain ('2.4 I-4 4-Spd 42RLE Auto (2003-2006)'), Autoblog 2005 (automatic "
        "'available on all models') and JeepSpecs 2005 say an automatic was offered with the 2.4 L in 2005-2006. "
        "Rockcrawler's press-kit reprint and Quadratec say six-speed only, so the sources conflict and EPA's missing row is "
        "not proof. 1 lot car loses the proposed Manual label.",
    "epa_ford_ranger_2.0l_4cyl_anydrive":
        "Already dropped by the builder: The Ranger Station says 1985-1988 2.0 L Rangers had the C3 automatic, which EPA does not list.",
    "epa_chevrolet_camaro_2.5l_4cyl_anydrive":
        "Already dropped by the builder: a source says the 1985 Camaro 2.5 L had an automatic, which EPA does not list.",
}
DEMOTE_NOTES = {
    "epa_mercury_cougar_2.0l_4cyl_anydrive": [
        "DEMOTED to candidate in verification (6 lot cars no longer counted). The only text source (Consumer Guide 1999-02, "
        "'4-cylinder (manual shift only)') is contradicted by EPA for 1999 (14999: 2.0 Automatic 4-spd).",
        "Machine Design's Cougar description and Cars.com '2000 Cougar: what's new' say the Zetec 2.0 came with either the MTX75 "
        "manual or the CD4E automatic; an enthusiast page says a small number of I4 automatics were built. EPA 2000-2002 "
        "list only the manual, but the claim is not certain for every car. vin_rules_4's verifier demoted its matching VIN rule too.",
        "Decode cache: 2.0 L only with VIN 5-8 = T603 (series 60, Zetec); no counterexample with a label (vPIC gives Ford no transmission before MY2017).",
    ],
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def displ_of(engine):
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*L", engine or "")
    return float(m.group(1)) if m else None


def tclass(t):
    t = (t or "").lower()
    if not t:
        return ""
    if "manual" in t and "automated" not in t:
        return "manual"
    if any(w in t for w in ("auto", "cvt", "continuously", "dual-clutch", "dct", "automated")):
        return "non_manual"
    return "other"


def main():
    d = json.loads(OUT.read_text())
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache = {k: v for k, v in cache.items() if isinstance(v, dict)}
    gt = [json.loads(l) for l in open(HERE / "ground_truth.jsonl")]

    cars_by_rule = defaultdict(list)
    for c in d.get("newly_confirmed_manual_cars", []) + d.get("candidate_rule_manual_cars", []):
        cars_by_rule[c["rule"]].append(c)

    # pattern -> displacement counter, per (make, model, year, VIN 4-8)
    pat_disp = defaultdict(Counter)
    for v, dec in cache.items():
        if len(v) == 17:
            pat_disp[(dec.get("make"), norm(dec.get("model")), dec.get("modelYear"), v[3:8])][displ_of(dec.get("engine"))] += 1

    surviving, refuted = [], list(d.get("refuted_rules", []))
    refuted_ids = {r["id"] for r in refuted}
    for r in d["rules"]:
        if r["status"] == "drop":
            if r["id"] not in refuted_ids:
                refuted.append({
                    "id": r["id"], "previous_status": "drop", "scope": r["scope"],
                    "epa_rows": r.get("epa_rows"), "citations": r.get("citations"),
                    "why": REFUTE_NOTES.get(r["id"], "dropped: " + "; ".join(sorted(set(
                        (r.get("status_reason_by_year") or {}).values())))),
                    "lot_cars_affected_without_trans_info": r["lot"].get("cars_without_trans_info", 0),
                    "removed_on": TODAY,
                })
            continue
        surviving.append(r)

    for r in surviving:
        sc = r["scope"]
        makes = {m.upper() for m in sc.get("epa_make", [])}
        names = {norm(n) for n in sc.get("epa_base_models", []) + sc.get("epa_model_names", [])}
        for fm in sc.get("feed_models_on_lots", {}):
            mk, _, md = fm.partition(" ")
            names.add(norm(md))
            makes.add(mk.upper())
        for c in cars_by_rule.get(r["id"], []):
            dec = cache.get(c["vin"])
            if dec:
                names.add(norm(dec.get("model")))
                makes.add((dec.get("make") or "").upper())
        names.discard("")
        if "GEO" in makes or "CHEVROLET" in makes and "metro" in names:
            makes |= {"GEO", "CHEVROLET"}
        years = {str(y) for y in (r.get("years_counted") or sc.get("model_years") or [])}
        dl = (sc.get("engine") or {}).get("displacementL")
        drive = sc.get("drive", "")

        def in_scope(make, model, year, engine, drv):
            if (make or "").upper() not in makes or norm(model) not in names or str(year) not in years:
                return False
            if dl is not None:
                x = displ_of(engine)
                if x is None or abs(x - dl) > 0.051:
                    return False
            if drive in ("4wd", "awd") and not re.search(r"4WD|AWD|4x4", drv or ""):
                return False
            if drive in ("4x2", "2wd") and re.search(r"4WD|AWD|4x4", drv or ""):
                return False
            return True

        gt_lines = [g for g in gt if g["source"] == "vin" and in_scope(g.get("vpicMake"), g.get("vpicModel"),
                    g.get("vpicYear"), g.get("engine"), g.get("drive"))]
        gt_counter = [g for g in gt_lines if tclass(g["trans"]) == "non_manual"]
        cache_in = [(v, dec) for v, dec in cache.items() if in_scope(dec.get("make"), dec.get("model"),
                    dec.get("modelYear"), dec.get("engine"), dec.get("driveType"))]
        cache_lab = Counter(tclass(dec.get("transmission")) or "blank" for _, dec in cache_in)
        cache_counter = [v for v, dec in cache_in if tclass(dec.get("transmission")) == "non_manual"]
        collisions = []
        if dl is not None:
            for v, dec in cache_in:
                cnt = pat_disp[(dec.get("make"), norm(dec.get("model")), dec.get("modelYear"), v[3:8])]
                other = {k: n for k, n in cnt.items() if k is not None and abs(k - dl) > 0.051}
                if other:
                    collisions.append(f"{dec.get('modelYear')} {v[3:8]}: {other}")
        collisions = sorted(set(collisions))
        listing = Counter()
        for g in gt:
            if g["source"] == "listing" and g["make"].upper() in makes and norm(g["model"]) in names \
                    and str(g["year"]) in years:
                listing[tclass(g["trans"]) or "other"] += 1

        verdict = "kept (counted)" if r["status"] in ("low_sample", "keep") else "kept as candidate (not counted)"
        checks = list(HAND.get(r["id"], []))
        if r["id"] in DEMOTE_NOTES:
            checks = DEMOTE_NOTES[r["id"]] + checks
            verdict = "demoted to candidate (not counted)"
        if not checks:
            checks = ["Not counted before or after this pass; no hand check beyond the computed scans below. "
                      "Status reason: " + "; ".join(sorted(set((r.get("status_reason_by_year") or {}).values())))]
        if gt_counter or cache_counter or collisions:
            if r["status"] in ("low_sample", "keep"):
                verdict = "NEEDS REVIEW: computed counterexample or code collision (see below)"
        r["verified"] = {
            "on": TODAY,
            "by": "adversarial verification pass (epa_sole_verify.py)",
            "verdict": verdict,
            "checks": checks,
            "computed": {
                "scope_used": {"makes": sorted(makes), "model_names_normalised": sorted(names),
                               "years": sorted(years), "displacementL": dl, "drive": drive},
                "ground_truth_vin_lines_in_scope": len(gt_lines),
                "ground_truth_counterexamples": [f"{g['vin']} {g['year']} {g['vpicModel']} {g['engine']} '{g['trans']}'"
                                                 for g in gt_counter][:10],
                "vpic_cache_in_scope": len(cache_in),
                "vpic_cache_transmission_labels": dict(cache_lab),
                "vpic_cache_counterexamples": cache_counter[:10],
                "vin_pattern_collisions": collisions[:10],
                "vinless_listing_lines_same_model_years": dict(listing),
                "vinless_listing_note": ("model-level only: listings carry no engine/drive, so an 'Automatic' "
                                         "listing of a model that also had other engines is not a counterexample"
                                         if dl is not None else
                                         "model-year-wide rule: any non-manual listing here would be a counterexample"),
            },
        }

    d["rules"] = surviving
    d["refuted_rules"] = refuted
    by_status = Counter(r["status"] for r in surviving)
    s = d["summary"]
    s["manual_rules"] = len(surviving)
    s["manual_rules_by_status"] = dict(by_status)
    s["refuted_rules_removed"] = len(refuted)
    counted = [r for r in surviving if r["status"] in ("low_sample", "keep")]
    chk = sum(r["validation"]["ground_truth_checkable"] for r in counted)
    agr = sum(r["validation"]["agree"] for r in counted)
    needs = [r["id"] for r in surviving if r["verified"]["verdict"].startswith("NEEDS REVIEW")]
    d["verification"] = {
        "on": TODAY,
        "script": "scraper/manual_detect/epa_sole_verify.py (run after epa_sole.py)",
        "method": [
            "Re-opened each counted rule's citations (WebFetch could not resolve consumerguide.com or other outside hosts "
            "from this session, so text came from WebSearch result text and from sibling worklists that read the pages).",
            "Searched the web for statements that the other transmission was offered (Caliber 1.8, GTI VR6, Tribute 2.0, "
            "Rodeo 2.6, Sportage 2.0 4WD, Cougar 2.0, Wrangler TJ 2.4).",
            "Re-read every EPA row of each rule's model names for the rule years and the years either side.",
            "Re-decoded sample lot VINs live with vPIC DecodeVinValues (vpic.nhtsa.dot.gov reachable).",
            "Scanned ground_truth.jsonl and the vPIC decode cache for in-scope cars with the other transmission and for "
            "VIN patterns whose decoded displacement varies (computed per rule, rerun each time).",
            "Cross-checked the sibling VIN-rule worklists' later verification passes (vin_rules_2/4/5/6), which removed "
            "or demoted rules covering the same cars.",
        ],
        "outcome": {
            "refuted_and_removed": ["epa_jeep_liberty_cherokee_2.4l_4cyl_anydrive (3 lot cars)",
                                    "epa_jeep_wrangler_tj_2.4l_4cyl_anydrive (1 lot car)"],
            "previously_dropped_moved_to_refuted_rules": ["epa_ford_ranger_2.0l_4cyl_anydrive",
                                                          "epa_chevrolet_camaro_2.5l_4cyl_anydrive"],
            "demoted_to_candidate": ["epa_mercury_cougar_2.0l_4cyl_anydrive (6 lot cars)"],
            "narrowed": "none beyond the above; Frontier stays MY1998 only; scope edges (Mazdaspeed3 2012 BL1L3 codes, "
                        "Escape 2001 XLT with code B, Metro code-6 collision note) checked and held",
            "rules_needing_review_from_computed_scans": needs,
        },
        "counted_rules_ground_truth": {
            "per_counted_combination": s["ground_truth_manual_claims_counted_combinations"],
            "summed_over_counted_rules_all_years": {"checkable": chk, "agree": agr, "disagree": chk - agr},
            "note": "the per-rule sum includes ground-truth cars in a counted rule's non-counted years"},
        "not_done": [
            "consumerguide.com, wikipedia.org and other outside hosts were not reachable with WebFetch; quotes rest on "
            "search-result text or on sibling worklists' reads.",
            "No pre-2005 manufacturer VIN filing was re-read in this pass (sibling verifiers re-read several).",
            "Candidate rules (not counted) got only the computed scans.",
        ],
        "inventory_note": "epa_sole.py was re-run on the current inventory before this pass; inventory drift moved "
                          "one Geo Metro off the lots (10 -> 9).",
    }
    d["generated_utc_verified"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"rules": len(surviving), "by_status": dict(by_status), "refuted": len(refuted),
                      "counted_cars": s["newly_confirmed_manual_counted"],
                      "net_new": s["newly_confirmed_manual_counted_net_new"],
                      "counted_gt": d["verification"]["counted_rules_ground_truth"], "needs_review": needs}, indent=1))


if __name__ == "__main__":
    main()
