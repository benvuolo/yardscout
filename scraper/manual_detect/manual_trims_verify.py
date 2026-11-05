#!/usr/bin/env python3
"""Adversarial verification pass over manual_trims.json (step 3).

Applies the outcome of the 2026-11-05 verification to the builder's output:
refuted / downgraded / narrowed trims, corrected citations, per-car
exclusions, and a "verified" block on every trim that is still counted.
Re-run after manual_trims.py (which does not carry these edits):

    python3 -I scraper/manual_detect/manual_trims.py
    python3 -I scraper/manual_detect/manual_trims_verify.py

Offline except nothing: every web check below was done once by hand and is
recorded as text. The decode-cache scan is recomputed here.
"""

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import manual_trims as mt  # noqa: E402

OUT = HERE / "manual_trims.json"
DATE = "2026-11-05"
SEARCH = "web-search result text (page not fetched)"


def cite(url, says, kind, read="page text read"):
    return {"url": url, "kind": kind, "says": says, "read": read}


# --- per-trim changes ---------------------------------------------------------
DROP_CITES = {
    # parts retailers: CLAUDE.md task rule, never cite parts-catalog sites
    "ford_mustang_bullitt_2019_2020": ["americanmuscle.com"],
    "ford_shelby_gt500_2007_2014": ["lmr.com"],
}
ADD_CITES = {
    "ford_mustang_bullitt_2019_2020": [
        cite("https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
             "EPA rows 40327 (2019) and 41995 (2020) 'Mustang Bullitt 5.0 Manual 6-spd' are the only Bullitt rows; every 2019-2020 Mustang automatic row is a non-Bullitt model name.", "epa", "epa/vehicles.csv read")],
    "ford_shelby_gt500_2007_2014": [
        cite(mt.W("Shelby_Mustang"), "2007 GT500: 'Features include the Tremec TR-6060 6-speed manual transmission'.", "wikipedia", "raw wikitext read"),
        cite("https://www.autobytel.com/ford/shelby-gt500/2013/car-buying-guides/10-things-you-need-to-know-about-the-2013-ford-shelby-gt500-115544/",
             "2013 GT500 'restricts buyers exclusively to a shift-it-yourself gearbox'; the gearbox was strengthened over 2012.", "review", SEARCH)],
    "ford_shelby_gt350_2015_2020": [
        cite("https://www.fordmuscle.com/news/lighter-better-six-speed-manual-the-only-option-for-shelby-gt350",
             "Headline: 'Lighter, Better Six-Speed Manual The Only Option For Shelby GT350' (Tremec TR-3160).", "enthusiast", SEARCH)],
    "chevrolet_camaro_ss_1le_2013_2015": [
        cite("https://motorweek.org/road_tests/2013_chevrolet_camaro_1le/",
             "2013 Camaro 1LE: a package that 'can be added to any Camaro coupe, as long as it's an SS, with manual transmission'.", "review", SEARCH)],
    "saturn_ion_red_line_2004_2007": [
        cite("https://www.auto123.com/en/news/2004-saturn-ion-red-line-quad-coupe-road-test/55847/?page=3",
             "2004 Ion Red Line road test: 'the standard 5-speed manual transmission (with no option for an automatic by the way)'.", "review"),
        cite("https://www.thetruthaboutcars.com/2007/03/saturn-ion-red-line/",
             "2007 Ion Red Line review: 'the Red Line's five-speed manual. This close-ratio version of the Saab 9-3's gearbox ...' (no automatic mentioned).", "review")],
    "bmw_m5_e34_1991_1993_e39_2000_2003": [
        cite(mt.W("BMW_M5"), "E34 infobox transmission: '5-speed manual (1988-1994)', '6-speed manual (1994-1995)'; E39 infobox '6-speed manual' and 'The transmission is the Getrag 420G six-speed manual'. The SMG first appears on the E60 (2006+ in the US).", "wikipedia", "raw wikitext read")],
    "fiat_500_abarth_2012_2014": [
        cite("https://www.autoblog.com/2014/06/24/2015-fiat-500-abarth-automatic-targets-broader-appeal/",
             "The 2015 model is the first Abarth with an automatic; until then the Abarth was one of the few manual-only cars on the US market.", "review", SEARCH + "; autoblog.com returned 403")],
    "chevrolet_cobalt_ss_supercharged_2005_2007": [
        cite(mt.W("Chevrolet_Cobalt_SS"), "'launching as a 205 hp supercharged 2.0 L coupe in late 2004, paired only with the Saab F35 5-speed manual transmission ... Production of the supercharged coupe continued until 2007'.", "wikipedia", "raw wikitext read")],
    "chevrolet_cobalt_ss_turbo_2008_2010": [
        cite(mt.W("Chevrolet_Cobalt_SS"), "2008 relaunch with the LNF turbo 2.0, 'remaining mated to the F35 5-speed manual transmission'; the 4T45 automatic is listed only for the naturally aspirated cars.", "wikipedia", "raw wikitext read")],
    "nissan_370z_nismo_2009_2014": [
        cite(mt.W("Nissan_370Z"), "'The NISMO version was introduced for the 2009 model year ... Transmission choice is limited to a 6-speed manual'.", "wikipedia", "raw wikitext read")],
    "nissan_sentra_se_r_spec_v_2007_2012": [
        cite("https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/3N1CB61E69L642925?format=json",
             "Live vPIC decodes of lot VINs 3N1CB61E28L731535 (2008), 3N1CB61E69L642925 (2009), 3N1CB6AP8AL678766 (2010), 3N1CB6AP3BL695735 (2011): OtherEngineInfo 'High output' / 'HO', 2.5 L. vPIC's pattern for position 4 'C' therefore covers the MY2008-2010 charts that were not read.", "vpic", "API JSON read")],
    "hyundai_veloster_n_2019_2020": [
        cite("scraper/manual_detect/vin_rules_3.json", "Step-2 rule hyundai_veloster_n_2019_2020 (verified 2026-11-05): Hyundai Part 565 filings code the Veloster N separately; NRCan lists it M6-only for 2019-2020.", "sibling")],
}
FIX_TEXT = {
    # (trim id, url substring) -> new 'says'
    ("ford_mustang_svt_cobra_1993_2004", "Ford_Mustang_SVT_Cobra"):
        "Infobox transmissions: 5-speed Borg-Warner T-5 manual (1993), Tremec 3550 5-speed manual (1996-2001), T-56 6-speed (2003-2004). Exception: the three 1994 Indianapolis 500 pace-car convertibles (Roush-modified) 'were installed with heavy-duty four-speed automatic transmissions'.",
}
NARROW = {
    "fiat_500_abarth_2012_2014": (2012, 2013),
    "chevrolet_camaro_ss_1le_2013_2015": (2013, 2015),
}
STATUS = {
    "vw_new_beetle_turbo_s_2002_2004": "sources_conflict",
}
RSX_BASIS = ("Honda VIN: positions 4-6 'DC5' = RSX, position 7 '3' = manual (step-2 honda_vin7_digit rule: odd = manual). "
             "JH4DC53 covers every manual RSX: the Type-S (6MT) AND the base 5MT (position 8 = 8, vPIC 5-spd Manual). "
             "So it identifies 'manual RSX', not 'Type-S'; the manual claim holds for every match. "
             "VIN_TRIM_PATTERNS in junkyard_scraper.py labels JH4DC53 'Type-S', which is wrong for base 5MT cars (flagged to ops/data.md owner).")
EXCLUDE_CARS = {
    "1FALP54Y5NA210963": "yard lists a 1997 Taurus but VIN position 10 decodes 1992 (check digit valid). A 1997 SHO is an automatic-only V8; the car is not certain, so it is not counted.",
    "3C3CFFJH5ET202396": "2014 500c Abarth: MY2014 removed from the rule (Consumer Guide's 2014 500c Abarth test says 'A 6-speed automatic is optionally available'; EPA lists only the manual for 2014). Step-2 vin_rules_6 rule fiat_500_turbo_2012_2014_series_FHJ_char8_H also counts this car; flagged for the hub.",
}

CHECKED = {
    "nissan_sentra_se_r_spec_v_2007_2012": [
        "Re-downloaded the MY2007 (W-1252-Y) and MY2012 (W-1612-C, letter 2011-06-01) Nissan Part 565 PDFs and read the page images: Sentra line B, model change 6, position 4 A = 2.0L, B = 2.5L, C = 2.5L Gasoline (High output). Matches the citation.",
        "Nissan release re-fetched (global.nissannews.com, 200): 'The Spec V model is available only with a close-ratio 6-speed manual transmission.' and 'The Sentra SE-R, equipped exclusively with Nissan's Xtronic CVT'.",
        "Live vPIC decodes of 2008-2011 3N1CB6 VINs report 'High output'/'HO', closing the unread MY2008-2010 chart gap.",
        "Decode cache: 16 3N1CB6 VINs, none with a transmission; ground truth: no 3N1CB6 or 3N1BB6 line. No counterexample. Bounded by model change 6 (B17 Sentra from MY2013 is 7) and by the VIN-year check.",
        "Conflict noted: vin_rules_2.json says the 2007-12 Spec V shares its engine code with the SE-R. The filings refute that for MY2007 and MY2012; that note should be corrected by its owner."],
    "ford_focus_st_2013_2018": [
        "All 19 cached decodes and all 13 lot cars are 1FADP3L9 (position 8 = 9, 2.0 GTDI); EPA 'Focus ST FWD' / 2.0T rows 2013-2018 are manual only. No ground-truth line. Claim and scope hold; step-2 vin_rules_4 covers the same cars."],
    "ford_fiesta_st_2014_2019": ["Wikipedia re-read: 'six-speed manual transmission' for the Mexico-built US ST; EPA 'Fiesta ST FWD' 2014-2019 manual only; lot car 3FADP4GX (position 8 X), check digit valid."],
    "ford_shelby_gt500_2007_2014": ["Parts-retailer citation (lmr.com) removed. Second sources added (Wikipedia 2007 TR-6060; Autobytel 2013). EPA 5.4S/5.8S rows manual only. Lot car 1ZVBP8JZ1E5276064: 2014, 5.8, check digit valid. 2020+ GT500 (DCT) is outside the years and its 5.2 is not matched."],
    "ford_taurus_sho_30_1989_1995": ["Wikipedia re-read: 5-speed manual; the 1993+ automatic came only with the 3.2 ('A 3.2 L version ... was introduced for the automatic-equipped SHO'). EPA: every 3.0 SHO row 1990-1995 manual, every 3.2 row automatic. Engine condition 3.0 holds.",
        "Car 1FALP54Y5NA210963 excluded (yard year 1997 vs VIN 1992)."],
    "acura_integra_gsr_1992_2001": ["Wikipedia re-read: 1992-93 'The GS-R liftback came only with a 5-speed manual'; 1994-2001 'except for the GS-R which was only offered in a 5-speed manual'. Cache: 11 VINs, every one with a transmission is manual. Lot car JH4DB8584 position 7 = 5 (odd = manual under the step-2 Honda rule)."],
    "chevrolet_cobalt_ss_supercharged_2005_2007": ["Wikipedia re-read (quote added). All 5 cached 2.0 Cobalt 2005-07 VINs have position 8 = P (LSJ). The 2.4 SS (automatic available) is excluded by the engine condition."],
    "chevrolet_cobalt_ss_turbo_2008_2010": ["Wikipedia re-read (quote added). The one cached 2.0 Cobalt 2008-10 VIN (position 8 X) decodes 'Manual/Standard'."],
    "saturn_ion_red_line_2004_2007": ["Second source added (auto123 2004: no automatic option; TTAC 2007). Wikipedia: the 2.0 supercharged engine is Red Line only. All 4 cached matches have position 8 = P."],
    "dodge_neon_srt4_2003_2005": ["Wikipedia infobox re-read: '5-speed NVG T-850 manual'. All 8 cached matches 1B3ES66S (position 8 S, 2.4 turbo)."],
    "dodge_caliber_srt4_2008_2009": ["Wikipedia re-read: '6-speed Getrag manual' and engine table 'SRT4 || 2008-2009 || ... 6-speed Getrag manual, FWD'. All 3 cached matches 1B3HB68F."],
    "fiat_500_abarth_2012_2014": ["Narrowed to MY2012-2013. Consumer Guide's 2014 500c Abarth test (blog.consumerguide.com, read) says 'A 6-speed automatic is optionally available', against EPA (manual only for 2014) and Autoblog. Sources disagree for 2014, so 2014 is out (listed in not_manual_only).",
        "Wikipedia re-read: the North-America automatic Abarth is referenced to the 2015 launch article. The 500c Abarth abroad had an automated manual (MTA); US scope only."],
    "hyundai_veloster_n_2019_2020": ["EPA re-read: 2019-2020 Veloster N manual only, 2021 adds AM-S8. vin_rules_3 (verified) is the second source."],
    "acura_rsx_type_s_2002_2006": ["Refuted the identifier's stated meaning, not the claim: 16 of 41 cached JH4DC53 VINs are base RSX with a 5-speed manual (position 8 = 8). Every JH4DC53 VIN with a vPIC transmission (32) is manual. Basis text corrected; the scraper's VIN_TRIM_PATTERNS label is a data-quality issue for its owner."],
    "ford_mustang_bullitt_2019_2020": ["Parts-retailer citation (americanmuscle.com) removed; replaced by EPA 'Mustang Bullitt' rows (manual only)."],
    "ford_shelby_gt350_2015_2020": ["Second transmission source added (fordmuscle; vPIC decode identifies the engine only)."],
    "chevrolet_camaro_ss_1le_2013_2015": ["Narrowed to MY2013-2015 (the 2017-2018 claim had one source only; no 1LE in 2016). Second 2013 source added (MotorWeek)."],
    "bmw_m5_e34_1991_1993_e39_2000_2003": ["Second source added (Wikipedia infoboxes). The US E34 years 1991-1993 and E39 2000-2003 had no automatic; the SMG arrives with the E60."],
    "nissan_370z_nismo_2009_2014": ["Wikipedia re-read: NISMO from MY2009 with the 6-speed manual only; the 2015 NISMO adds the 7-speed automatic (outside the years)."],
    "ford_mustang_svt_cobra_1993_2004": ["Wikipedia re-read. The pace-car exception is 1994 (three Roush-modified convertibles), not 1993; text corrected. Not a retail configuration."],
}
DEFAULT = ("Citations not re-opened in this pass (no lot car depends on this trim today). "
           "EPA rows recomputed from epa/vehicles.csv: identical to the builder's. "
           "Ground truth scanned for any non-manual line matching the identifiers or naming the trim: none.")


def cache_scan(trims):
    cache = json.loads(gzip.decompress((mt.DATA / "vin_decodes.json.gz").read_bytes()))
    cache.pop("_exportedAt", None)
    cars = []
    for vin, raw in cache.items():
        if isinstance(raw, dict):
            dec = mt.js._correct_vpic(raw, vin)
            cars.append(({"vin": vin, "year": mt.to_int(dec.get("modelYear")), "make": "", "model": "", "dec": dec}, raw))
    out = {}
    for t in trims:
        ids = [i for i in t["identification"] if i["type"] != "feed_model"]
        c = Counter()
        for car, raw in cars:
            if any(mt.match_ident(i, car) for i in ids):
                c["matched"] += 1
                k = mt.tclass(raw.get("transmission"))
                c[k or "no_transmission"] += 1
        out[t["id"]] = dict(c)
    return out


def main():
    d = json.loads(OUT.read_text())
    if "verification" in d:
        sys.exit("manual_trims.json already carries a verification block: run manual_trims.py first")
    trims = {t["id"]: t for t in d["trims"]}
    for tid, (y0, y1) in NARROW.items():
        t = trims[tid]
        t["years_before_verification"] = t["years"]
        t["years"] = [y0, y1]
        for i in t["identification"]:
            i["years"] = [max(i["years"][0], y0), min(i["years"][1], y1)]
    for tid, st in STATUS.items():
        trims[tid]["status_before_verification"] = trims[tid]["status"]
        trims[tid]["status"] = st
        trims[tid]["counted"] = False
    for tid, subs in DROP_CITES.items():
        t = trims[tid]
        t["evidence_removed"] = [e for e in t["evidence"] if any(s in e["url"] for s in subs)]
        for e in t["evidence_removed"]:
            e["why_removed"] = "parts retailer / parts catalog: not an allowed evidence source"
        t["evidence"] = [e for e in t["evidence"] if not any(s in e["url"] for s in subs)]
    for tid, cs in ADD_CITES.items():
        trims[tid]["evidence"].extend(cs)
    for (tid, sub), says in FIX_TEXT.items():
        for e in trims[tid]["evidence"]:
            if sub in e["url"]:
                e["says"] = says
    for i in trims["acura_rsx_type_s_2002_2006"]["identification"]:
        if i["type"] == "vin_regex":
            i["basis"] = RSX_BASIS
    trims["acura_rsx_type_s_2002_2006"]["notes"] += " The VIN pattern JH4DC53 also matches base 5-speed-manual RSX; both are manual, so the claim is 'manual' for every match."

    d["not_manual_only"].append({
        "trim": "Fiat 500 / 500c Abarth", "years": [2014, 2014],
        "why": "Sources disagree: Consumer Guide's 2014 500c Abarth test says a 6-speed automatic was optional; EPA lists only the 5-speed manual for 2014. Not claimed.",
        "epa_ids": [34333], "cites": ["https://blog.consumerguide.com/test-drive-2014-fiat-500c-abarth-cabrio/"]})
    d["not_manual_only"].append({
        "trim": "Volkswagen New Beetle Turbo S", "years": [2002, 2004],
        "why": "Sources disagree: Consumer Guide's 1998-2005 New Beetle used-car page lists the 180 hp 1.8T with '6-speed manual, 6-speed automatic'; the other reviews say the Turbo S had the 6-speed manual (machinedesign: 'standard', not 'only'); the Edmunds 'no automatic' citation could not be opened (host not reachable). EPA cannot isolate the 180 hp engine.",
        "epa_ids": [17479, 17480, 19306, 19308, 19516, 19518], "cites": ["https://consumerguide.com/used/1998-05-volkswagen-new-beetle/",
                                                                     "https://www.machinedesign.com/archive/article/21813012/2002-vw-new-beetle-turbo-s"]})

    scan = cache_scan(d["trims"])

    # cars
    keep, dropped = [], []
    for c in d["newly_confirmed_manual_cars"]:
        t = trims[c["rule"]]
        y = mt.to_int((c.get("vpic") or {}).get("year")) or mt.to_int(c["year"])
        why = EXCLUDE_CARS.get(c["vin"])
        if t["status"] != "verified":
            why = why or f"rule status is now {t['status']}"
        elif not (t["years"][0] <= (y or 0) <= t["years"][1]):
            why = why or "outside the narrowed years"
        if why:
            c["counted"] = False
            c["rule_status"] = t["status"]
            c["excluded_by_verification"] = why
            dropped.append(c)
        else:
            keep.append(c)
    d["newly_confirmed_manual_cars"] = keep
    d["listed_not_counted_cars"].extend(dropped)

    # verified blocks + per-trim lot counts
    for t in d["trims"]:
        if t["status"] not in ("verified", "sources_conflict") and t["id"] not in STATUS:
            continue
        n = sum(1 for c in keep if c["rule"] == t["id"])
        blk = {"verified_utc": DATE, "verifier": "adversarial pass (manual_trims verification)",
               "verdict": ("downgraded to " + t["status"]) if t["id"] in STATUS else
                          ("kept, narrowed" if t["id"] in NARROW else "kept"),
               "checked": CHECKED.get(t["id"], []) + ([DEFAULT] if t["id"] not in CHECKED else []),
               "decode_cache_scan": scan.get(t["id"], {}),
               "newly_confirmed_after_verification": n}
        if t["id"] == "vw_new_beetle_turbo_s_2002_2004":
            blk["checked"] = ["machinedesign.com re-read: 'A six-speed manual transmission is standard on the Turbo S and is the only car in the line with this setup' (standard, not only).",
                              "Consumer Guide used 1998-2005 New Beetle (read): engine table '1.8 ... Engine HP 180 ... Avail. Trans. 6-speed manual 6-speed automatic'.",
                              "Edmunds 2002 review not reachable from this session (www.edmunds.com does not resolve); its 'no automatic' text was not confirmed.",
                              "Wikipedia: the Turbo S 'included ... six-speed manual transmission' (does not say only).",
                              "Result: not certain for every car; 4 lot cars no longer counted."]
        t["verified"] = blk
        if t["status"] != "verified":
            t["counted"] = False

    # summary
    s = d["summary"]
    s["trims_by_status"] = dict(Counter(t["status"] for t in d["trims"]))
    ver = [t for t in d["trims"] if t["status"] == "verified"]
    s["verified_trims"] = len(ver)
    s["verified_trims_with_a_vin_decode_identifier"] = sum(1 for t in ver if t.get("identifiable_from_vin_decode"))
    s["verified_trims_matching_any_lot_car"] = sum(1 for t in ver if (t.get("lots") or {}).get("matched"))
    gm = sum(t["validation"]["manual"] for t in ver)
    gn = sum(t["validation"]["non_manual"] for t in ver)
    s["ground_truth_on_verified_trims"].update({"manual": gm, "non_manual": gn, "precision": round(gm / (gm + gn), 4) if gm + gn else None})
    cm = sum(t["validation"]["decode_cache_all_vins"]["manual"] for t in ver)
    cn = sum(t["validation"]["decode_cache_all_vins"]["non_manual"] for t in ver)
    s["decode_cache_check_on_verified_trims"].update({"manual": cm, "non_manual": cn, "precision": round(cm / (cm + cn), 4) if cm + cn else None})
    s["newly_confirmed_manual_lot_cars"] = len(keep)
    s["newly_confirmed_manual_lot_cars_not_already_in_step2"] = sum(1 for c in keep if not c["also_confirmed_by_step2"])
    s["newly_confirmed_by_rule"] = dict(Counter(c["rule"] for c in keep))
    s["listed_not_counted_by_rule"] = dict(Counter(c["rule"] for c in d["listed_not_counted_cars"]))

    d["verification"] = {
        "verified_utc": DATE,
        "method": ("Adversarial re-check: re-read the Part 565 PDFs (page images) and the Nissan release behind the only new VIN rule; "
                   "re-read Wikipedia wikitext and review pages for every trim that confirms a lot car; recomputed every EPA query from vehicles.csv; "
                   "scanned all 470k cached decodes (not only those with a transmission) for every identifier and looked at trims/engines/VIN positions of the matches; "
                   "scanned ground_truth.jsonl for any non-manual line naming one of the trims; compared yard year with VIN year for every counted car; "
                   "checked VIN check digits; removed parts-retailer citations."),
        "rules_refuted": 0,
        "rules_downgraded": ["vw_new_beetle_turbo_s_2002_2004 -> sources_conflict (Consumer Guide lists a 6-speed automatic for the 180 hp 1.8T)"],
        "rules_narrowed": ["fiat_500_abarth_2012_2014 -> 2012-2013 (2014 sources conflict)",
                           "chevrolet_camaro_ss_1le_2013_2015 -> 2013-2015 (2017-18 single source)"],
        "identifier_basis_corrected": ["acura_rsx_type_s_2002_2006: JH4DC53 = manual RSX (base 5MT and Type-S 6MT), not Type-S"],
        "citations_removed": ["americanmuscle.com (Bullitt), lmr.com (GT500): parts retailers"],
        "citations_added": sorted(ADD_CITES),
        "cars_excluded": {v: w for v, w in EXCLUDE_CARS.items()},
        "count_change": f"newly confirmed manual lot cars 45 -> {len(keep)}; not already in step 2: 13 -> {s['newly_confirmed_manual_lot_cars_not_already_in_step2']}",
        "for_other_workstreams": [
            "junkyard_scraper.VIN_TRIM_PATTERNS labels every JH4DC53 RSX 'Type-S'; base 5MT RSX share the prefix (position 8 = 8). Data-quality owner.",
            "vin_rules_2.json says the 2007-12 Sentra Spec V shares its engine code with the SE-R; Nissan's MY2007/MY2012 filings give it position 4 'C' (2.5L high output).",
            "vin_rules_6.json fiat_500_turbo_2012_2014_series_FHJ_char8_H counts 3C3CFFJH5ET202396 (2014 500c Abarth), where sources disagree for MY2014."],
        "limits": "www.edmunds.com does not resolve from this session and autoblog.com/cars.com return 403; those are cited from web-search result text and marked so. manual_trims.py does not carry these edits: run this script after it.",
    }
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: s[k] for k in ("trims_by_status", "verified_trims", "ground_truth_on_verified_trims", "decode_cache_check_on_verified_trims",
                                        "newly_confirmed_manual_lot_cars", "newly_confirmed_manual_lot_cars_not_already_in_step2", "newly_confirmed_by_rule")}, indent=1))


if __name__ == "__main__":
    main()
