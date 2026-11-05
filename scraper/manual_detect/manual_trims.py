#!/usr/bin/env python3
"""Manual-transmission detection, step 3: US-market trims sold ONLY with a
manual transmission.

A cited table of trims (make, model, trim, model years) for which every car
sold in the US had a manual gearbox, how each trim can be recognised on a
lot car, and what that recognition is worth on today's data:

  * the claim is per trim AND per model year. Years in which the same trim
    name also came with an automatic are excluded (Golf R 2015 is DSG only,
    Fiat 500 Abarth from 2015, 370Z NISMO from 2015, Veloster N from 2021,
    GR Corolla from 2025, Evo X MR, HHR SS ...) and listed under
    "not_manual_only";
  * a trim is recognised only from the VIN decode or a VIN pattern:
      vpic_trim / vpic_series  the decoded vPIC Trim or Series names the
                               trim exactly (blobs such as "Standard / Turbo /
                               R-Spec / Rally Edition" never match);
      vpic_model               vPIC's model name is the trim (S2000, Viper,
                               Lancer Evolution, Golf R ...);
      vpic_engine              the displacement vPIC decodes from the VIN
                               engine code is unique to the trim within that
                               model and years (Civic 2.0 2002-2011 = Si);
      vin_regex                a VIN pattern whose meaning comes from the
                               manufacturer's Part 565 filing or from vPIC's
                               own pattern decode (Sentra position 4 "C" =
                               2.5L high output = SE-R Spec V);
      feed_model               the yard's model text names the trim exactly
                               (only for model names that ARE the trim).
    The yard's free-text model is never used to infer a trim otherwise;
  * every trim carries its evidence: EPA fueleconomy.gov rows (computed here
    from epa/vehicles.csv, with the expectation checked), manufacturer press
    releases, Part 565 filings, Wikipedia and enthusiast references.
    status "verified" needs two independent sources (EPA counts as one only
    when its rows isolate the trim, e.g. an engine no other trim of that
    model had). Only "verified" trims are counted.

Validation: every identifier is applied to scraper/manual_detect/
ground_truth.jsonl (uniformCell lines are treated as unlabelled, see
BASELINE.md section 2). Counting: lot cars (docs/data/inventory_live.json,
current scan) matched by a verified trim whose published transmission is
empty are "newly confirmed" unless the yard is in Canada (the claims are
US-market claims). Overlap with the step-2 rule sets (vin_rules_0..7.json,
epa_sole.json) is reported, so the hub can see what is net new.

Nothing here edits the scraper, the app or the published data.

Inputs: docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz, scraper/manual_detect/ground_truth.jsonl,
        scraper/manual_detect/epa/vehicles.csv, vin_rules_*.json, epa_sole.json
Output: scraper/manual_detect/manual_trims.json

Run:  python3 -I scraper/manual_detect/manual_trims.py
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
sys.path.insert(0, str(HERE.parent))
import junkyard_scraper as js  # noqa: E402  (_correct_vpic)

OUT = HERE / "manual_trims.json"
EPA_CSV = HERE / "epa" / "vehicles.csv"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
EPA_ROW = "https://www.fueleconomy.gov/feg/noframes/{}.shtml"
MID = "https://vpic.nhtsa.dot.gov/mid/home/displayfile/"
VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{}?format=json"
CANADA = {"AB", "BC", "MB", "NB", "NL", "NS", "ON", "PE", "QC", "SK", "YT", "NT", "NU"}


def W(title):
    return "https://en.wikipedia.org/wiki/" + title


def cite(url, says, kind):
    """kind: epa | manufacturer | part565 | vpic | wikipedia | press | review | enthusiast | sibling"""
    return {"url": url, "kind": kind, "says": says}


READ_NOTE = ("Wikipedia read as raw wikitext (en.wikipedia.org/w/index.php?action=raw) "
             "through the session proxy on 2026-11-05; other pages through web-search "
             "result text or a plain page fetch the same day.")


# ---------------------------------------------------------------------------
# The table. Each identifier:
#   {"type": "vpic_trim"|"vpic_series", "make", "model", "years", "trim", ["engine"], ["drive"]}
#   {"type": "vpic_model", "make", "model", "years"}
#   {"type": "vpic_engine", "make", "model", "years", "engine"}
#   {"type": "vin_regex", "regex", "years", "basis"}
#   {"type": "feed_model", "make", "model", "years"}
# make = vPIC make (upper case) for vpic_* types, feed make for feed_model.
# Regexes are full-match, case-insensitive, except vin_regex (search from ^).
# "epa": [{"make","model","years","displ","charger","expect"}], expect is
#   "manual_only"   every row of the query must be a manual (the query isolates the trim), or
#   "manual_listed" a manual row exists (the query also holds other trims; EPA cannot isolate).
# ---------------------------------------------------------------------------

V = "verified"
SS = "single_source"          # one source only: listed, not counted
CF = "sources_conflict"       # not counted
REF = "covered_by_step2_rule"  # the step-2 VIN rule is the counted rule; kept here for completeness

TRIMS = [
    # ------------------------------------------------------------- Honda / Acura
    dict(id="honda_civic_si_1999_2000", make="Honda", model="Civic", trim="Si (coupe, EM1, 1.6 B16A2)",
         years=[1999, 2000], status=V,
         notes="US Civic Si returned for 1999-2000 as a coupe only. The 1992-1995 Civic Si hatchback and the del Sol Si are NOT in this rule (del Sol Si had a 4-speed automatic; vPIC labels confirm).",
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[1999, 2000], trim=r"S[Ii]")],
         epa=[dict(make="Honda", model=r"^Civic", years=[1999, 2000], displ="1.6", expect="manual_listed")],
         cites=[cite("https://grassrootsmotorsports.com/articles/siren-song-1999-2000-honda-civic-si-buyers-guide/",
                     "1999-2000 Civic Si buyer's guide: the only available transmission was a close-ratio five-speed manual; coupe only, B16A2 160 hp.", "review"),
                cite("https://www.hagerty.com/media/?p=4971",
                     "Hagerty 1996-2000 Civic (EK) buyer's guide: the Si was offered only with a five-speed manual.", "review")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="honda_civic_si_2002_2005", make="Honda", model="Civic", trim="Si (3-door hatch, EP3, 2.0 K20A3)",
         years=[2002, 2005], status=V,
         notes="The 2.0L K20A3 was the Si's own engine; no other 2002-2005 US Civic had a 2.0.",
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[2002, 2005], trim=r"S[Ii]"),
                dict(type="vpic_engine", make="HONDA", model="Civic", years=[2002, 2005], engine=r"2\.0L.*")],
         epa=[dict(make="Honda", model=r"^Civic", years=[2002, 2005], displ="2.0", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(seventh_generation)"), "'Shifting away from the 1.6 liter D-series engine, the seventh-generation Civic Si adopted the K-series K20A3 engine...' 'The Si/SiR (EP3) USDM had the K20A3.' (engine identity; EPA supplies the transmission)", "wikipedia"),
                cite("scraper/manual_detect/vin_rules_0.json", "Honda's Part 565 VIN code (character 7 odd = manual) marks every 2002-2005 Civic Si on the lots manual (8 of 8 ground-truth lines): an independent, per-VIN manufacturer code.", "sibling")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="honda_civic_si_2006_2011", make="Honda", model="Civic", trim="Si (coupe and sedan, 2.0 K20Z3)",
         years=[2006, 2011], status=V,
         notes="2.0L only in the Si (other Civics 1.8, Hybrid 1.3, GX 1.8 CNG).",
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[2006, 2011], trim=r"S[Ii]"),
                dict(type="vpic_engine", make="HONDA", model="Civic", years=[2006, 2011], engine=r"2\.0L.*")],
         epa=[dict(make="Honda", model=r"^Civic", years=[2006, 2011], displ="2.0", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(eighth_generation)"), "Civic Si: 'The car comes with a 2.0-liter K20Z3 i-VTEC engine that produces 197 hp ... while including a 6-speed manual transmission with a helical limited-slip differential.'", "wikipedia")],
         sibling=["honda_vin7_digit_1987_2009_manual", "honda_vin7_letter_2010_on_manual"]),
    dict(id="honda_civic_si_2012_2015", make="Honda", model="Civic", trim="Si (coupe and sedan, 2.4 K24Z7)",
         years=[2012, 2015], status=V,
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[2012, 2015], trim=r"S[Ii]"),
                dict(type="vpic_engine", make="HONDA", model="Civic", years=[2012, 2015], engine=r"2\.4L.*")],
         epa=[dict(make="Honda", model=r"^Civic", years=[2012, 2015], displ="2.4", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(ninth_generation)"), "'A 6-speed manual transmission with a helical LSD (Limited Slip Differential) was offered as the only available transmission option for the Civic Si.'", "wikipedia")],
         sibling=["honda_vin7_letter_2010_on_manual"]),
    dict(id="honda_civic_si_2017_2020", make="Honda", model="Civic", trim="Si (coupe and sedan, 1.5T L15B7)",
         years=[2017, 2020], status=V,
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[2017, 2020], trim=r"S[Ii](/S[Ii] HPT)?")],
         epa=[dict(make="Honda", model=r"^Civic Si", years=[2017, 2018], displ="1.5", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(tenth_generation)"), "'A 6-speed manual transmission or CVT is offered on all models, except for the Type R and Si models, which only come with the 6-speed manual transmission'.", "wikipedia")],
         sibling=["honda_vin7_letter_2010_on_manual"]),
    dict(id="honda_civic_si_2022_2025", make="Honda", model="Civic", trim="Si (sedan, 1.5T)",
         years=[2022, 2025], status=V,
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic", years=[2022, 2025], trim=r"S[Ii]")],
         epa=[dict(make="Honda", model=r"^Civic 4Dr", years=[2025, 2025], displ="1.5", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(eleventh_generation)"), "Si: 'Available only as a sedan since the coupe bodystyle was discontinued, it is powered by a more powerful version of the EX and Touring's 1.5-litre ... and is only available with a 6-speed manual transmission.'", "wikipedia")],
         sibling=["honda_vin7_letter_2010_on_manual"]),
    dict(id="honda_civic_type_r_2017_2025", make="Honda", model="Civic", trim="Type R (FK8 2017-2021, FL5 2023-2025, 2.0T)",
         years=[2017, 2025], status=V,
         notes="No US Type R for MY2022. EPA lists the 2.0 turbo Civic hatch (Type R) only with a manual in every year.",
         ident=[dict(type="vpic_trim", make="HONDA", model="Civic( Type R)?", years=[2017, 2025], trim=r"Type[- ]?R"),
                dict(type="vpic_model", make="HONDA", model="Civic Type R", years=[2017, 2025])],
         epa=[dict(make="Honda", model=r"^Civic 5Dr", years=[2017, 2025], displ="2.0", charger="T", expect="manual_only")],
         cites=[cite(W("Honda_Civic_(tenth_generation)"), "'...except for the Type R and Si models, which only come with the 6-speed manual transmission'.", "wikipedia")],
         sibling=["honda_vin7_letter_2010_on_manual"]),
    dict(id="honda_crx_si_hf_1988_1991", make="Honda", model="CRX", trim="CRX Si and CRX HF (second generation)",
         years=[1988, 1991], status=SS,
         notes="vPIC returns the blob 'CRX/CRX HF' (the base CRX had an automatic), so only an exact 'CRX Si' trim/series matches.",
         ident=[dict(type="vpic_series", make="HONDA", model="Civic( Si)?|CRX", years=[1988, 1991], trim=r"CRX Si"),
                dict(type="vpic_trim", make="HONDA", model="Civic( Si)?|CRX", years=[1988, 1991], trim=r"CRX Si")],
         epa=[],
         cites=[cite(W("Honda_CR-X"), "'The base model was available with either a 5-speed manual transmission or a 4-speed automatic transmission while the HF and Si only offered a 5-speed manual transmission.'", "wikipedia")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="honda_del_sol_vtec_1994_1997", make="Honda", model="del Sol", trim="VTEC (1.6 B16A3)",
         years=[1994, 1997], status=SS,
         ident=[dict(type="vpic_trim", make="HONDA", model="del Sol|Civic", years=[1994, 1997], trim=r"VTEC")],
         epa=[],
         cites=[cite(W("Honda_CR-X_del_Sol"), "'The S and Si models were available with either a 5-speed manual transmission or a 4-speed automatic while the del Sol VTEC model was only available with a 5-speed manual transmission.'", "wikipedia")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="honda_prelude_type_sh_1997_2001", make="Honda", model="Prelude", trim="Type SH",
         years=[1997, 2001], status=SS,
         ident=[dict(type="vpic_trim", make="HONDA", model="Prelude", years=[1997, 2001], trim=r"Type[- ]?SH")],
         epa=[],
         cites=[cite(W("Honda_Prelude"), "'The Type SH was only available with a 5-speed manual transmission.'", "wikipedia")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="honda_s2000_2000_2009", make="Honda", model="S2000", trim="all", years=[2000, 2009], status=V,
         ident=[dict(type="vpic_model", make="HONDA", model="S2000", years=[2000, 2009]),
                dict(type="feed_model", make="Honda", model="S2000", years=[2000, 2009])],
         epa=[dict(make="Honda", model=r"^S2000", years=[2000, 2009], expect="manual_only")],
         cites=[cite(W("Honda_S2000"), "Infobox transmission '6-speed manual'; 'The engine is mated to a six-speed manual transmission and Torsen limited-slip differential.'", "wikipedia")],
         sibling=["honda_vin7_digit_1987_2009_manual"]),
    dict(id="acura_integra_gsr_1992_2001", make="Acura", model="Integra", trim="GS-R (1.7 B17A1 1992-93, 1.8 B18C1 1994-2001)",
         years=[1992, 2001], status=V,
         notes="1992-1993: the 1.7L B17A1 was the GS-R's own engine (EPA lists it only with a manual). 1994-2001: Wikipedia.",
         ident=[dict(type="vpic_trim", make="ACURA", model="Integra", years=[1992, 2001], trim=r"GS-?R( w/leather|\(Leather Seat\))?"),
                dict(type="vpic_engine", make="ACURA", model="Integra", years=[1992, 1993], engine=r"1\.7L.*")],
         epa=[dict(make="Acura", model=r"^Integra", years=[1992, 1993], displ="1.7", expect="manual_only")],
         cites=[cite(W("Honda_Integra"), "Third generation (1994-2001): 'All trim levels were available with a 5-speed manual or 4-speed automatic transmission except for the GS-R which was only offered in a 5-speed manual with shorter gearing than other trim levels.'", "wikipedia")],
         sibling=["acura_vin7_digit_1986_2009_manual"]),
    dict(id="acura_integra_type_r_1997_2001", make="Acura", model="Integra", trim="Type R (US 1997-1998, 2000-2001)",
         years=[1997, 2001], status=SS,
         ident=[dict(type="vpic_trim", make="ACURA", model="Integra", years=[1997, 2001], trim=r"Type[- ]?R")],
         epa=[],
         cites=[cite(W("Honda_Integra"), "'Equipped with a close-ratio 5-speed manual transmission and a helical-type limited-slip differential, the Integra Type R...'", "wikipedia"),
],
         sibling=["acura_vin7_digit_1986_2009_manual"]),
    dict(id="acura_rsx_type_s_2002_2006", make="Acura", model="RSX", trim="Type-S (2.0 K20A2/K20Z1)",
         years=[2002, 2006], status=V,
         notes="EPA's only 6-speed RSX row is the Type-S; base RSX had a 5-speed manual or 5-speed automatic. vPIC sometimes decodes the 2005-2006 Type-S engine as 2.4L (vPIC error), so the engine is not used.",
         ident=[dict(type="vpic_trim", make="ACURA", model="RSX", years=[2002, 2006], trim=r"Type-?S"),
                dict(type="vin_regex", regex=r"^JH4DC53", years=[2002, 2006],
                     basis="VIN_TRIM_PATTERNS in junkyard_scraper.py: Honda model code DC53 = RSX Type-S (DC54 = base)")],
         epa=[dict(make="Acura", model=r"^RSX", years=[2002, 2006], displ="2.0", expect="manual_listed")],
         cites=[cite("https://consumerguide.com/used/2002-06-acura-rsx/", "'Only a six-speed manual gearbox came with the Type-S, but base coupes could have either a five-speed manual or five-speed automatic transmission.'", "review"),
                cite("https://www.cars.com/research/acura-rsx-2005/", "2005 RSX review: 'the Type-S comes only with a close-ratio six-speed-manual gearbox'.", "review")],
         sibling=["acura_vin7_digit_1986_2009_manual"]),
    dict(id="acura_ilx_24_2013_2015", make="Acura", model="ILX", trim="2.4 (Premium 2.4)", years=[2013, 2015], status=V,
         notes="From MY2016 the 2.4L ILX has an 8-speed dual-clutch only.",
         ident=[dict(type="vpic_engine", make="ACURA", model="ILX", years=[2013, 2015], engine=r"2\.4L.*")],
         epa=[dict(make="Acura", model=r"^ILX$", years=[2013, 2015], displ="2.4", expect="manual_only")],
         cites=[cite(W("Acura_ILX"), "Infobox: '6-speed manual (2.4 L; 2013–2015)', '8-speed dual-clutch (2.4 L; 2016–2022)'; 'a version of the Civic Si's 201 hp 2.4-liter I4 gasoline engine mated to a 6-speed manual'.", "wikipedia")],
         sibling=["acura_vin7_letter_2010_on_manual"]),
    # ------------------------------------------------------------- Subaru
    dict(id="subaru_impreza_wrx_sti_2004_2021", make="Subaru", model="Impreza WRX STI / WRX STI", trim="STI (2.5 turbo EJ257)",
         years=[2004, 2021], status=V,
         notes="EPA isolates the STI in 2004-2005 and 2015-2021 (2.5T rows are all 6-speed manual). In 2006-2014 the 2.5T EPA rows also hold the WRX (4-speed automatic until 2010); EPA lists no 5-speed automatic (the A-Line automatic was not sold in the US).",
         ident=[dict(type="vpic_trim", make="SUBARU", model="Impreza|WRX|WRX STI", years=[2004, 2021], trim=r"(WRX )?STI(-S| Limited| Type RA)?"),
                dict(type="vpic_model", make="SUBARU", model="WRX STI|Impreza WRX STI", years=[2004, 2021])],
         epa=[dict(make="Subaru", model=r"Impreza|WRX", years=[2004, 2005], displ="2.5", charger="T", expect="manual_only"),
              dict(make="Subaru", model=r"WRX", years=[2015, 2021], displ="2.5", charger="T", expect="manual_only")],
         cites=[cite(W("Subaru_WRX"), "'The WRX STI also retains the 6-speed TY85 manual transmission (the CVT is not available on the STI) from the previous generation.'", "wikipedia")],
         sibling=["subaru_fhi_G_H_1995_2026_char11", "subaru_fhi_L_6mt_2006_2014_char11", "subaru_fhi_main_plant_2014_2026_char11"]),
    dict(id="subaru_impreza_wrx_2011_2014", make="Subaru", model="Impreza", trim="WRX (2.5 turbo, non-STI)",
         years=[2011, 2014], status=SS,
         notes="EPA lists every 2011-2014 2.5T Impreza row as manual (5-speed WRX, 6-speed STI); WRX 2008-2010 had a 4-speed automatic and 2015+ a CVT. No independent text source read.",
         ident=[dict(type="vpic_trim", make="SUBARU", model="Impreza", years=[2011, 2014], trim=r"WRX( Premium| Limited)?")],
         epa=[dict(make="Subaru", model=r"Impreza", years=[2011, 2014], displ="2.5", charger="T", expect="manual_only")],
         cites=[], sibling=["subaru_fhi_G_H_1995_2026_char11", "subaru_fhi_main_plant_2014_2026_char11"]),
    dict(id="subaru_legacy_25gt_specb_2006_2009", make="Subaru", model="Legacy", trim="2.5 GT spec.B",
         years=[2006, 2009], status=V,
         notes="2006: 5-speed manual (500-unit limited edition); 2007-2009: 6-speed manual.",
         ident=[dict(type="vpic_trim", make="SUBARU", model="Legacy", years=[2006, 2009], trim=r"(2\.5 ?GT )?spec\.? ?B")],
         epa=[dict(make="Subaru", model=r"Legacy", years=[2006, 2009], displ="2.5", charger="T", expect="manual_listed")],
         cites=[cite("https://www.autoblog.com/2005/09/21/subaru-to-offer-limited-edition-legacy/", "Subaru release (2006 MY): 'The Legacy 2.5 GT spec.B is available exclusively with a 5-speed manual transmission.'", "press"),
                cite("https://www.auto123.com/en/multimedia/news/2007-subaru-legacy-25gt-specb-first-impressions/79524", "2007 Legacy 2.5GT spec.B: six-speed manual from the WRX STI; an automatic is not offered.", "review"),
                cite(W("Subaru_Legacy_(fourth_generation)"), "Transmission table: '2.5GT spec.B || MY07-MY09 || 6-speed manual'.", "wikipedia")],
         sibling=["subaru_sia_1997_2009_char11", "subaru_fhi_G_H_1995_2026_char11"]),
    # ------------------------------------------------------------- Mitsubishi
    dict(id="mitsubishi_lancer_evolution_viii_ix_2003_2006", make="Mitsubishi", model="Lancer Evolution", trim="Evolution VIII / IX (all US trims: GSR, RS, MR)",
         years=[2003, 2006], status=V,
         notes="Evolution I-VII were never sold in the US (EPA has no Lancer Evolution row before MY2003); a JDM import would be outside the US-market claim.",
         ident=[dict(type="vpic_model", make="MITSUBISHI", model="Lancer Evolution", years=[2003, 2006]),
                dict(type="feed_model", make="Mitsubishi", model="Lancer Evolution", years=[2003, 2006])],
         epa=[dict(make="Mitsubishi", model=r"Lancer Evolution", years=[2003, 2006], expect="manual_only")],
         cites=[cite(W("Mitsubishi_Lancer_Evolution"), "US Evolution VIII/IX: GSR 5-speed manual, RS close-ratio 5-speed manual; 'The MR edition was introduced to the US in 2005, with ACD and the only model with a 6-speed manual transmission.'", "wikipedia")],
         sibling=[]),
    dict(id="mitsubishi_lancer_evolution_x_gsr_2008_2015", make="Mitsubishi", model="Lancer Evolution", trim="Evolution X GSR (and 2015 Final Edition)",
         years=[2008, 2015], status=SS,
         notes="Evolution X GSR = 5-speed manual; the MR used the 6-speed TC-SST dual-clutch (EPA 'Automatic (S6)/(AM6)' rows every year). The model name alone is therefore NOT enough for 2008-2015; only an exact vPIC trim 'GSR' matches, and no Mitsubishi filing read gives the trim character.",
         ident=[dict(type="vpic_trim", make="MITSUBISHI", model="Lancer Evolution", years=[2008, 2015], trim=r"GSR")],
         epa=[dict(make="Mitsubishi", model=r"Lancer Evolution", years=[2008, 2015], expect="manual_listed")],
         cites=[], sibling=[]),
    # ------------------------------------------------------------- Mazda
    dict(id="mazdaspeed3_2007_2013", make="Mazda", model="Mazda3", trim="MAZDASPEED3 (2.3 turbo L3-VDT)",
         years=[2007, 2013], status=REF,
         ident=[dict(type="vpic_trim", make="MAZDA", model="Mazda3|MAZDASPEED3|Mazdaspeed3", years=[2007, 2013], trim=r"MAZDASPEED ?3|Mazdaspeed ?3"),
                dict(type="vpic_model", make="MAZDA", model="MAZDASPEED3|Mazdaspeed3|MAZDASPEED 3", years=[2007, 2013])],
         epa=[dict(make="Mazda", model=r"Speed 3", years=[2008, 2013], expect="manual_only")],
         cites=[cite(W("Mazdaspeed3"), "'A GKN limited-slip differential is standard, along with a six-speed manual transmission...' 'No automatic transmission option was offered.'", "wikipedia")],
         sibling=["mazda_mazdaspeed3_2007_2009_char8_L3T", "mazda_mazdaspeed3_2010_2013_char8_L3T"]),
    dict(id="mazdaspeed6_2006_2007", make="Mazda", model="Mazda6", trim="MAZDASPEED6 (2.3 turbo, AWD)",
         years=[2006, 2007], status=REF,
         ident=[dict(type="vpic_trim", make="MAZDA", model="Mazda6|MAZDASPEED6", years=[2006, 2007], trim=r"MAZDASPEED ?6|Mazdaspeed ?6")],
         epa=[dict(make="Mazda", model=r"^6$", years=[2006, 2007], displ="2.3", charger="T", expect="manual_only")],
         cites=[], sibling=["mazda_mazdaspeed6_2006_2007_char8_L3T"]),
    dict(id="mazdaspeed_protege_2003", make="Mazda", model="Protege", trim="MAZDASPEED Protege", years=[2003, 2003], status=REF,
         ident=[], epa=[], cites=[], sibling=["mazda_mazdaspeed_protege_2003_char8_FSD170"]),
    dict(id="mazdaspeed_mx5_2004_2005", make="Mazda", model="MX-5 Miata", trim="MAZDASPEED MX-5 (1.8 turbo)",
         years=[2004, 2005], status=SS,
         notes="EPA's only turbo MX-5 rows (2004-2005) are 6-speed manual. vPIC decodes the 1.8 turbo as plain '1.8L' (same as the non-turbo), so no VIN-decode identifier; no Mazda filing read gives the engine character.",
         ident=[dict(type="vpic_trim", make="MAZDA", model="MX-5|MX-5 Miata", years=[2004, 2005], trim=r"MAZDASPEED|Mazdaspeed( MX-5)?")],
         epa=[dict(make="Mazda", model=r"MX-5", years=[2004, 2005], displ="1.8", charger="T", expect="manual_only")],
         cites=[], sibling=[]),
    dict(id="mazda_rx8_r3_2009_2011", make="Mazda", model="RX-8", trim="R3", years=[2009, 2011], status=REF,
         notes="Every 2009-2011 manual RX-8 has the high-power 13B, which the step-2 rule recognises from VIN character 8; the R3 is a subset of it.",
         ident=[dict(type="vpic_trim", make="MAZDA", model="RX-8", years=[2009, 2011], trim=r"R3")],
         epa=[], cites=[cite(W("Mazda_RX-8"), "'The manual-transmission Spirit R is based on the RX-8 Type RS ... (the Japanese-market equivalents of the North American R3 ...)'", "wikipedia")],
         sibling=["mazda_rx8_2009_2011_char8_engine_power"]),
    # ------------------------------------------------------------- Toyota / Scion / Pontiac (NUMMI)
    dict(id="toyota_corolla_xrs_2005_2006", make="Toyota", model="Corolla", trim="XRS (1.8 2ZZ-GE)", years=[2005, 2006], status=REF,
         notes="The 2009-2010 Corolla XRS (2.4 2AZ-FE) had a 5-speed automatic option and is NOT manual-only.",
         ident=[dict(type="vpic_trim", make="TOYOTA", model="Corolla", years=[2005, 2006], trim=r"XRS")],
         epa=[], cites=[cite(W("Toyota_Corolla_(E120)"), "XRS: 'The close ratio C60 6-speed manual transmission (also found in the Toyota Matrix XRS) was the only transmission available.' The 2009 XRS 'was available with a 5-speed manual or 5-speed automatic'.", "wikipedia")],
         sibling=["toyota_corolla_xrs_2zzge_2005_2006"]),
    dict(id="toyota_matrix_xrs_pontiac_vibe_gt_2003_2006", make="Toyota / Pontiac", model="Matrix / Vibe", trim="Matrix XRS / Vibe GT (1.8 2ZZ-GE)", years=[2003, 2006], status=REF,
         notes="Step-2 rules: Matrix XRS 2004-2006 (low_sample) and Vibe GT 2003-2006 (candidate). The 2009-2010 Vibe GT / Matrix XRS (2.4) had automatics.",
         ident=[dict(type="vpic_trim", make="TOYOTA", model="Matrix", years=[2004, 2006], trim=r"XRS")],
         epa=[], cites=[cite(W("Pontiac_Vibe"), "'...a version with VVTL-i producing 164 hp for the GT (manual 6-speed only).'", "wikipedia")],
         sibling=["toyota_matrix_xrs_2zzge_2004_2006", "pontiac_vibe_gt_2003_2006_series_SN_char8_L"]),
    dict(id="toyota_tacoma_x_runner_2005_2013", make="Toyota", model="Tacoma", trim="X-Runner (Access Cab 4x2, 4.0 V6)",
         years=[2005, 2013], status=SS,
         notes="Not recognisable from the VIN: vPIC returns the same Series codes for X-Runner and PreRunner/base Access Cab V6 (TRN/GRN 2xx, shown by the lot decodes), and EPA lists the 4.0 Tacoma 2WD with both a 6-speed manual and a 5-speed automatic.",
         ident=[dict(type="vpic_trim", make="TOYOTA", model="Tacoma", years=[2005, 2013], trim=r"X-?Runner")],
         epa=[dict(make="Toyota", model=r"Tacoma 2WD", years=[2005, 2013], displ="4.0", expect="manual_listed")],
         cites=[cite(W("Toyota_Tacoma"), "'The X-Runner comes only with an Aisin RA60 6-speed manual transmission.'", "wikipedia")],
         sibling=[]),
    dict(id="toyota_gr_corolla_2023_2024", make="Toyota", model="GR Corolla", trim="all (1.6 turbo G16E-GTS)", years=[2023, 2024], status=V,
         notes="MY2025 added the 8-speed GR-DAT automatic (EPA row 48595).",
         ident=[dict(type="vpic_model", make="TOYOTA", model="GR Corolla", years=[2023, 2024]),
                dict(type="vpic_trim", make="TOYOTA", model="GR Corolla", years=[2023, 2024], trim=r".*"),
                dict(type="vpic_trim", make="TOYOTA", model="Corolla", years=[2023, 2024], trim=r"GR Corolla.*"),
                dict(type="feed_model", make="Toyota", model="GR Corolla", years=[2023, 2024])],
         epa=[dict(make="Toyota", model=r"GR Corolla", years=[2023, 2024], expect="manual_only")],
         cites=[cite(W("Toyota_GR_Corolla"), "'A six-speed manual transmission is standard in the GR Corolla.' Infobox: '8-speed \"GR-DAT\" automatic (2024–present)' (calendar 2024 = MY2025).", "wikipedia")],
         sibling=[]),
    dict(id="toyota_mr2_turbo_1991_1995", make="Toyota", model="MR2", trim="Turbo (3S-GTE)", years=[1991, 1995], status=REF,
         ident=[], epa=[], cites=[], sibling=["toyota_mr2_turbo_3sgte_1991_1995"]),
    # ------------------------------------------------------------- Nissan
    dict(id="nissan_sentra_se_r_spec_v_2007_2012", make="Nissan", model="Sentra", trim="SE-R Spec V (2.5 QR25DE high output, 200 hp)",
         years=[2007, 2012], status=V,
         notes="The SE-R (non-Spec V, 177 hp) of the same years was CVT-only; Nissan codes the two engines differently in VIN position 4 (B = 2.5L, C = 2.5L high output), so the VIN separates them. EPA's 2007-2012 2.5 Sentra rows are one 6-speed manual (Spec V) and one CVT (SE-R).",
         ident=[dict(type="vin_regex", regex=r"^3N1CB6", years=[2007, 2012],
                     basis="Nissan Part 565 VIN charts MY2007 (W-1252-Y), MY2011 (W-1547-Y), MY2012: Sentra line B, model change 6, position 4 C = '2.5L, Gasoline (High output)'"),
                dict(type="vpic_trim", make="NISSAN", model="Sentra", years=[2007, 2012], trim=r"SE-R Spec ?V")],
         epa=[dict(make="Nissan", model=r"^Sentra$", years=[2007, 2012], displ="2.5", expect="manual_listed")],
         cites=[cite("https://global.nissannews.com/en/releases/200-horsepower-se-r-model-joins-2007-sentra-lineup-offers-serious-performance-at-an-affordable-price",
                     "Nissan release (2007 Sentra SE-R): 'The Spec V model is available only with a close-ratio 6-speed manual transmission.' 'The Sentra SE-R, equipped exclusively with Nissan's Xtronic CVT ...' SE-R QR25DE 177 hp; Spec V 200 hp.", "manufacturer"),
                cite(MID + "e065e785-678a-42d4-8571-f933e344af25", "Nissan North America, 2006-10-04, 'Vehicle Identification Number; Model Year 2007 (Third Submission)' (ORG2521), Passenger Car chart (page image): Position 4 engine type for NISSAN SENTRA (line B, model change 6): A = 2.0L Gasoline, B = 2.5L Gasoline, C = 2.5L Gasoline (High output).", "part565"),
                cite(MID + "9ae7b3b8-bfe2-44b1-b3b2-0cfd731eb502", "Nissan North America, 2010-06-10 (ORG5926), MY2011 chart (page image): NISSAN SENTRA B / 6: A = 2.0L, B = 2.5L, C = 2.5L Gasoline (High output).", "part565"),
                cite(MID + "dd09cf01-34f5-409a-aec6-86ade2a245a7", "Nissan North America, 2011-06-01 (ORG6744), MY2012 chart (page image): NISSAN SENTRA B / 6: A = 2.0L, B = 2.5L, C = 2.5L Gasoline (High output).", "part565")],
         sibling=[]),
    dict(id="nissan_sentra_se_r_spec_v_2002_2006", make="Nissan", model="Sentra", trim="SE-R Spec V (2.5 QR25DE, 175 hp)",
         years=[2002, 2006], status=SS,
         notes="NOT recognisable from the VIN: Nissan's MY2005 chart gives the 2.5L Sentra one engine code (A) for 2.5 S, SE-R and Spec V. EPA's 2002-2006 2.5 Sentra 6-speed manual rows are the Spec V; the SE-R had a 5-speed manual or 4-speed automatic.",
         ident=[dict(type="vpic_trim", make="NISSAN", model="Sentra", years=[2002, 2006], trim=r"SE-R Spec ?V")],
         epa=[dict(make="Nissan", model=r"^Sentra$", years=[2002, 2006], displ="2.5", expect="manual_listed")],
         cites=[cite("https://www2020.theautochannel.com/news/2002/07/14/143715.html", "2002 Sentra SE-R review: the regular SE-R 'has a five-speed manual or four-speed automatic transmission, but the Spec V gets a slick-shifting close-ratio six speed manual only'.", "review"),
                cite(MID + "4d4a5a67-24f1-4b3e-8895-ed0d7826f03c", "Nissan, 2004-07-08, MY2005 VIN chart (page image): NISSAN SENTRA (line B): position 4 A = 2.5L Gasoline, C = 1.8L, D = 1.8L (EZEV); one code for every 2.5L Sentra.", "part565")],
         sibling=[]),
    dict(id="nissan_350z_nismo_2007_2008", make="Nissan", model="350Z", trim="NISMO", years=[2007, 2008], status=SS,
         notes="Not recognisable from the VIN (Nissan MY2007 chart: one 350Z engine code).",
         ident=[dict(type="vpic_trim", make="NISSAN", model="350Z", years=[2007, 2008], trim=r"NISMO")],
         epa=[], cites=[cite(W("Nissan_350Z"), "NISMO 350Z: 'This version had the same engine as the regular 350Z (VQ35HR), but was only available with a 6-speed manual transmission...'", "wikipedia")],
         sibling=[]),
    dict(id="nissan_370z_nismo_2009_2014", make="Nissan", model="370Z", trim="NISMO", years=[2009, 2014], status=V,
         notes="From MY2015 the 370Z NISMO also had a 7-speed automatic.",
         ident=[dict(type="vpic_trim", make="NISSAN", model="370Z", years=[2009, 2014], trim=r"NISMO")],
         epa=[], cites=[cite(W("Nissan_370Z"), "Transmission table: '370Z NISMO (North America) || 2013- || 6-speed manual, 7-speed automatic, (2015–2020)'; 'All models (including the 2015 Nismo) include either a 7-speed automatic ... or a 6-speed manual'.", "wikipedia"),
                                      cite("https://digitaltrends.com/car-reviews/2014-nissan-370z-nismo-review", "2014 370Z NISMO review: 'six-speed manual transmission – no automatic is offered on the 370Z NISMO'.", "review"),
                                      cite("https://www.cars.com/articles/2015-nissan-370z-nismo-gets-new-styling-transmission-1420663015990", "2015 370Z NISMO gets a newly available 7-speed automatic.", "review")],
         sibling=[]),
    dict(id="nissan_juke_nismo_rs_fwd_2014_2017", make="Nissan", model="Juke", trim="NISMO RS, front-wheel drive", years=[2014, 2017], status=V,
         notes="The AWD NISMO RS was CVT-only (EPA 'Juke Nismo RS AWD' Automatic (AV-S8)), so the rule needs vPIC drive type = FWD.",
         ident=[dict(type="vpic_trim", make="NISSAN", model="Juke", years=[2014, 2017], trim=r"NISMO RS", drive=r"FWD.*|Front.*|4x2")],
         epa=[dict(make="Nissan", model=r"^Juke Nismo RS$", years=[2015, 2017], expect="manual_only")],
         cites=[cite("https://www2020.theautochannel.com/news/2014/11/20/119488-015-nissan-juke-nismo-and-juke-nismo-rs-press-kit.html", "Nissan 2015 JUKE NISMO RS press kit: the CVT is offered only with all-wheel drive, the 6-speed manual only with front-wheel drive (215 hp 6MT / 211 hp CVT).", "manufacturer"),
                cite("https://jalopnik.com/the-nissan-juke-nismo-rs-gets-more-power-but-no-manual-1468881469", "'The Nissan Juke Nismo RS Gets More Power, But No Manual AWD'.", "review")],
         sibling=[]),
    # ------------------------------------------------------------- Ford
    dict(id="ford_contour_svt_1998_2000", make="Ford", model="Contour", trim="SVT (2.5 Duratec, 195-200 hp)", years=[1998, 2000], status=V,
         ident=[dict(type="vpic_trim", make="FORD", model="Contour", years=[1998, 2000], trim=r"SVT")],
         epa=[dict(make="Ford", model=r"^Contour", years=[1998, 2000], displ="2.5", expect="manual_listed")],
         cites=[cite(W("Ford_Contour"), "SVT: '...white-face gauges for the instrument cluster; and a standard 5-speed manual transmission.'", "wikipedia"),
                cite("https://www.thetruthaboutcars.com/2019/01/junkyard-find-1999-ford-contour-svt/", "Junkyard Find 1999 Contour SVT: the five-speed manual was the only transmission offered.", "review"),
                cite("https://www.autoblog.com/2023/12/26/junkyard-gem-1998-ford-contour-svt/", "Junkyard Gem 1998 Contour SVT: manual transmission mandatory.", "review")],
         sibling=[]),
    dict(id="ford_mustang_svt_cobra_1993_2004", make="Ford", model="Mustang", trim="SVT Cobra (incl. Cobra R)", years=[1993, 2004], status=V,
         notes="No 2002 Cobra. 2003-2004 Cobra: 4.6 DOHC supercharged, the only 6-speed manual Mustang in EPA's list; the 4-speed automatics in the 4.6 rows are GT/Mach 1. The Indy pace cars (not sold) had automatics.",
         ident=[dict(type="vpic_trim", make="FORD", model="Mustang", years=[1993, 2004], trim=r"(SVT )?Cobra( R)?")],
         epa=[dict(make="Ford", model=r"^Mustang", years=[2003, 2004], displ="4.6", expect="manual_listed")],
         cites=[cite(W("Ford_Mustang_SVT_Cobra"), "Infobox transmissions: '5-speed Borg-Warner T-5 manual' (1993), 'A Tremec 3550 5-speed manual transmission was standard' (1996-2001), T-56 6-speed (2003-2004); the 1993 Indy pace cars 'were installed with heavy-duty four-speed automatic transmissions'.", "wikipedia"),
                cite("https://stangnet.com/mustang-forums/threads/auto-cobra.441485/", "Mustang forum thread: no SVT Cobra came from the factory with an automatic (only the pace cars did).", "enthusiast"),
                cite(VPIC.format("1FAFP48Y*3F"), "vPIC pattern decode: 2003 Mustang engine code Y = 4.6L, 390 hp, 'SC', Trim 'Cobra'.", "vpic")],
         sibling=[]),
    dict(id="ford_mustang_bullitt_2019_2020", make="Ford", model="Mustang", trim="Bullitt (5.0, 480 hp)", years=[2019, 2020], status=V,
         ident=[dict(type="vpic_trim", make="FORD", model="Mustang", years=[2019, 2020], trim=r"Bullitt")],
         epa=[],
         cites=[cite("https://www.americanmuscle.com/bullitt-mustang-guide.html", "Bullitt guide: 'Ford produced three generations of Bullitt Mustangs — the 2001 (265 hp), 2008–2009 (315 hp), and 2019–2020 (480 hp) — each with ... manual-only transmissions.'", "enthusiast"),
                cite("https://www.insidehook.com/nation/ford-2019-mustang-bullitt-detroit", "'Ford Just Unveiled the Mustang Bullitt, a 6-Speed Manual Exclusive' (2019).", "review")],
         sibling=["ford_mustang_bullitt_2019_2020_series_P8K"]),
    dict(id="ford_mustang_bullitt_2001_2008_2009", make="Ford", model="Mustang", trim="Bullitt (2001 and 2008-2009)", years=[2001, 2009], status=SS,
         notes="Applies to MY2001 and MY2008-2009 only (no Bullitt 2002-2007). VIN engine codes are shared with the Mustang GT of the same years, so only an exact vPIC trim matches.",
         ident=[dict(type="vpic_trim", make="FORD", model="Mustang", years=[2001, 2001], trim=r"Bullitt"),
                dict(type="vpic_trim", make="FORD", model="Mustang", years=[2008, 2009], trim=r"Bullitt")],
         epa=[],
         cites=[cite("https://www.americanmuscle.com/bullitt-mustang-guide.html", "'The Tremec TR-3650 five-speed manual was the only available transmission' (2008-2009); every Bullitt generation had 'a manual-only transmission'.", "enthusiast")],
         sibling=[]),
    dict(id="ford_mustang_boss_302_2012_2013", make="Ford", model="Mustang", trim="Boss 302 (incl. Laguna Seca)", years=[2012, 2013], status=V,
         ident=[dict(type="vpic_trim", make="FORD", model="Mustang", years=[2012, 2013], trim=r"Boss 302.*")],
         epa=[dict(make="Ford", model=r"^Mustang$", years=[2012, 2013], displ="5.0", expect="manual_listed")],
         cites=[cite(W("Boss_302_Mustang"), "Infobox '6-speed manual (2012–2013)'; 'It came with a 6-speed MT-82 manual transmission and a solid rear axle...'", "wikipedia"),
                cite("https://edmunds.com/ford/mustang/2012/review", "Edmunds 2012 Mustang review: an automatic transmission is not available for the Boss 302 (GT and V6 offer either).", "review")],
         sibling=[]),
    dict(id="ford_shelby_gt500_2007_2014", make="Ford", model="Mustang", trim="Shelby GT500 (5.4 SC 2007-2012, 5.8 SC 2013-2014)",
         years=[2007, 2014], status=V,
         notes="The engine is unique to the trim in these years, so EPA isolates it. The 2020-2022 GT500 is a 7-speed dual-clutch only (see not_manual_only).",
         ident=[dict(type="vpic_engine", make="FORD", model="Mustang", years=[2007, 2012], engine=r"5\.4L.*"),
                dict(type="vpic_engine", make="FORD", model="Mustang", years=[2013, 2014], engine=r"5\.8L.*"),
                dict(type="vpic_trim", make="FORD", model="Mustang", years=[2007, 2014], trim=r"(Shelby )?GT ?500.*|Shelby Coupe|Shelby Convertible", engine=r"5\.[48]L.*")],
         epa=[dict(make="Ford", model=r"^Mustang$", years=[2007, 2012], displ="5.4", charger="S", expect="manual_only"),
              dict(make="Ford", model=r"^Mustang$", years=[2013, 2014], displ="5.8", charger="S", expect="manual_only")],
         cites=[cite("https://www.edmunds.com/ford/shelby-gt500/2007/st-100751537/review/", "Edmunds 2007 Shelby GT500 review: Tremec six-speed manual; no automatic transmission is available.", "review"),
                cite("https://lmr.com/products/2007-Mustang-Specifications", "2007 Mustang specifications: GT500 (coupe and convertible) only with the Tremec TR-6060 six-speed manual.", "enthusiast")],
         sibling=["ford_mustang_gt500_2013_2014_char8_Z"]),
    dict(id="ford_shelby_gt350_2015_2020", make="Ford", model="Mustang", trim="Shelby GT350 / GT350R (5.2 Voodoo)", years=[2015, 2020], status=V,
         notes="MY2020: the GT500 also has a 5.2 (supercharged, DCT only) and vPIC's engine summary drops the supercharger, so the engine identifier stops at MY2019 and MY2020 needs an exact GT350 trim.",
         ident=[dict(type="vpic_engine", make="FORD", model="Mustang", years=[2015, 2019], engine=r"5\.2L.*"),
                dict(type="vpic_trim", make="FORD", model="Mustang", years=[2015, 2020], trim=r"(Shelby )?GT ?350R?")],
         epa=[dict(make="Ford", model=r"Shelby GT350", years=[2016, 2020], displ="5.2", expect="manual_only")],
         cites=[cite(VPIC.format("1FA6P8JZ*G5"), "vPIC pattern decode: 2016 Mustang engine code Z = 5.2L, 500 hp, Trim 'Shelby Coupe'.", "vpic")],
         sibling=["ford_mustang_gt350_2016_2020_char8_Z"]),
    dict(id="ford_mustang_svo_turbo_1984_1986", make="Ford", model="Mustang", trim="SVO (and 1984 Turbo GT): 2.3 turbo", years=[1984, 1986], status=V,
         notes="vPIC decodes the 2.3 turbo as '2.3L' like the non-turbo 2.3 (which had automatics), so only an exact 'SVO' trim matches; vPIC's 'LX,GT,SV0' blob does not.",
         ident=[dict(type="vpic_trim", make="FORD", model="Mustang", years=[1984, 1986], trim=r"SVO")],
         epa=[dict(make="Ford", model=r"^Mustang$", years=[1984, 1986], displ="2.3", charger="T", expect="manual_only")],
         cites=[cite(W("Ford_Mustang_SVO"), "Infobox transmission '5-speed T-5 manual'.", "wikipedia")],
         sibling=[]),
    dict(id="ford_taurus_sho_30_1989_1995", make="Ford", model="Taurus", trim="SHO with the 3.0 Yamaha V6", years=[1989, 1995], status=V,
         notes="1989-1992 SHO: manual only. 1993-1995: the 3.0 SHO stayed manual-only; the automatic SHO got a 3.2 (excluded by the engine condition).",
         ident=[dict(type="vpic_trim", make="FORD", model="Taurus", years=[1989, 1995], trim=r"SHO", engine=r"3\.0L.*")],
         epa=[dict(make="Ford", model=r"^Taurus SHO$", years=[1990, 1995], displ="3.0", expect="manual_only")],
         cites=[cite(W("Ford_Taurus_SHO"), "'The SHO was redesigned for 1992, although it continued with the same Yamaha-built V-6 engine and 5-speed manual transmission. The lack of an automatic transmission hampered sales, a situation that Ford rectified for model year 1993.' 'A 3.2 L version ... was introduced for the automatic-equipped SHO'.", "wikipedia")],
         sibling=["ford_taurus_sho_1993_char8"]),
    dict(id="ford_gt_2005_2006", make="Ford", model="GT", trim="all", years=[2005, 2006], status=V,
         ident=[dict(type="vpic_model", make="FORD", model="GT|Ford GT", years=[2005, 2006])],
         epa=[dict(make="Ford", model=r"^GT( 2WD)?$", years=[2005, 2006], expect="manual_only")],
         cites=[cite(W("Ford_GT"), "First generation: 'A Ricardo 6-speed manual transmission is fitted featuring a helical limited-slip differential.'", "wikipedia")],
         sibling=[]),
    dict(id="ford_focus_svt_2002_2004", make="Ford", model="Focus", trim="SVT (ZX3/ZX5 SVT, 2.0 Zetec 170 hp)", years=[2002, 2004], status=REF,
         ident=[dict(type="vpic_trim", make="FORD", model="Focus", years=[2002, 2004], trim=r"(ZX[35] )?SVT")],
         epa=[], cites=[], sibling=["ford_focus_svt_2002_2004_char8_engine"]),
    dict(id="ford_focus_st_2005_2007", make="Ford", model="Focus", trim="ZX4 ST (2.3)", years=[2005, 2007], status=REF,
         ident=[dict(type="vpic_trim", make="FORD", model="Focus", years=[2005, 2007], trim=r"(ZX4 )?ST", engine=r"2\.3L.*")],
         epa=[], cites=[], sibling=["ford_focus_st_2005_2007_series_P38_char8_Z"]),
    dict(id="ford_focus_st_2013_2018", make="Ford", model="Focus", trim="ST (2.0 EcoBoost)", years=[2013, 2018], status=V,
         ident=[dict(type="vpic_trim", make="FORD", model="Focus", years=[2013, 2018], trim=r"ST", engine=r"2\.0L.*", vin=r"^.{7}9",
                     vin_basis="Ford Part 565 filings MY2013-2018 (step-2 vin_rules_4): VIN character 8 = 9 is the 2.0L GTDI (ST); 2 is the 2.0L GDI of other Focus trims")],
         epa=[dict(make="Ford", model=r"^Focus( ST)? FWD$", years=[2013, 2015], displ="2.0", charger="T", expect="manual_only"),
              dict(make="Ford", model=r"^Focus ST FWD$", years=[2016, 2018], expect="manual_only")],
         cites=[cite("https://consumerguide.com/ford/2017-focus/", "2017 Focus: turbocharged 2.0-liter (ST), 252 hp: standard transmission 6-speed manual; available transmission NA (cited by step-2 vin_rules_4).", "review")],
         sibling=["ford_focus_st_2013_2018_series_P3L_char8_9"]),
    dict(id="ford_focus_rs_2016_2018", make="Ford", model="Focus", trim="RS (2.3 EcoBoost, AWD)", years=[2016, 2018], status=V,
         ident=[dict(type="vpic_trim", make="FORD", model="Focus", years=[2016, 2018], trim=r"RS", engine=r"2\.3L.*", vin=r"^.{7}H",
                     vin_basis="Ford Part 565 filings MY2016-2018 (step-2 vin_rules_4): Focus RS (WMI WF0) engine H = 2.3L GTDI")],
         epa=[dict(make="Ford", model=r"^Focus RS AWD$", years=[2016, 2018], expect="manual_only")],
         cites=[cite("https://www.cars.com/articles/articles-2015-02-ford-focus-rs-first-look/", "'more than 315-hp, turbocharged 2.3-liter EcoBoost four-cylinder, all-wheel drive, six-speed manual transmission only' (cited by step-2 vin_rules_4).", "review")],
         sibling=["ford_focus_rs_2016_2018_series_P3T_char8_H"]),
    dict(id="ford_fiesta_st_2014_2019", make="Ford", model="Fiesta", trim="ST (1.6 EcoBoost)", years=[2014, 2019], status=V,
         notes="vPIC attaches the trim 'ST' to some Fiestas decoded with the 1.6 FFV (non-turbo) engine; those are not matched (engine must not be FFV).",
         ident=[dict(type="vpic_trim", make="FORD", model="Fiesta", years=[2014, 2019], trim=r"ST", engine=r"1\.6L 4-cyl", vin=r"^.{7}X",
                     vin_basis="Ford Part 565 filings MY2014-2019 (step-2 vin_rules_4): Fiesta VIN character 8 = X is the 1.6L GTDI (ST); J is the 1.6L Ti-VCT, which vPIC also decodes as '1.6L 4-cyl'")],
         epa=[dict(make="Ford", model=r"^Fiesta ST FWD$", years=[2014, 2019], expect="manual_only")],
         cites=[cite(W("Ford_Fiesta_(sixth_generation)"), "Infobox '6-speed B6 manual (ST)'; 'The engine is mated to a 6-speed manual transmission which features Ford's Torque Vectoring Control...'", "wikipedia")],
         sibling=["ford_fiesta_st_2014_2019_char8_X"]),
    # ------------------------------------------------------------- GM
    dict(id="chevrolet_corvette_lt4_1996", make="Chevrolet", model="Corvette", trim="LT4 (incl. Grand Sport), 1996", years=[1996, 1996], status=V,
         notes="Every 1996 Corvette with the 6-speed manual got the LT4; automatic cars got the LT1 (VIN character 8 P).",
         ident=[dict(type="vin_regex", regex=r"^1G1Y...5.T", years=[1996, 1996], basis="vPIC pattern decode: 1996 Corvette VIN character 8 = 5 -> EngineModel LT4 (P -> LT1)")],
         epa=[dict(make="Chevrolet", model=r"^Corvette$", years=[1996, 1996], displ="5.7", expect="manual_listed")],
         cites=[cite(VPIC.format("1G1YY225*T5"), "vPIC: 1996 Corvette, VIN character 8 '5' -> EngineModel 'LT4', 5.7L.", "vpic"),
                cite(VPIC.format("1G1YY22P*T5"), "vPIC: 1996 Corvette, VIN character 8 'P' -> EngineModel 'LT1'.", "vpic"),
                cite("https://corvettereport.com/zr-1-vs-1996-lt4-which-c4-corvette-should-you-buy/", "'if a customer wanted a 1996 Corvette with the automatic transmission, the car came with the 300 horsepower LT1'.", "enthusiast"),
                cite(W("Chevrolet_Corvette_(C4)"), "The LT4 'was introduced in all six-speed manual transmission equipped cars' for 1996.", "wikipedia")],
         sibling=[]),
    dict(id="chevrolet_corvette_zr1_c4_1990_1995", make="Chevrolet", model="Corvette", trim="ZR-1 (LT5)", years=[1990, 1995], status=V,
         notes="Not identified here: vPIC's pattern decode of the LT5 code gives only '5.7L' (no engine model), so no VIN identifier is cited.",
         ident=[dict(type="vpic_trim", make="CHEVROLET", model="Corvette", years=[1990, 1995], trim=r"ZR-?1")],
         epa=[], cites=[cite("https://corvettereport.com/zr-1-vs-1996-lt4-which-c4-corvette-should-you-buy/", "ZR-1 (1990-1995): LT5 with the ZF six-speed manual only.", "enthusiast"),
                        cite("https://rmsothebys.com/auctions/fl12/lots/r222-1990-chevrolet-corvette-zr1", "1990 ZR-1 lot description: the ZF six-speed manual was the only transmission.", "enthusiast")],
         sibling=[]),
    dict(id="chevrolet_corvette_z06_c5_2001_2004", make="Chevrolet", model="Corvette", trim="Z06 (C5, 5.7 LS6)", years=[2001, 2004], status=V,
         ident=[dict(type="vin_regex", regex=r"^1G1Y...S.[1234]", years=[2001, 2004], basis="vPIC pattern decode: 2001 Corvette VIN character 8 = S -> EngineModel LS6 (G -> LS1)"),
                dict(type="vpic_trim", make="CHEVROLET", model="Corvette", years=[2001, 2004], trim=r"Z06")],
         epa=[],
         cites=[cite(W("Chevrolet_Corvette_(C5)"), "'The Z06 model was only available with the six-speed manual transmission.'", "wikipedia"),
                cite("https://www.corvetteforum.com/how-tos/a/c5-corvette-general-specifications-and-information-375430", "C5 specifications: the manual transmission was required on the 2001-2004 Z06; the LS6 was used on the Z06 only.", "enthusiast"),
                cite(VPIC.format("1G1YY12S*15"), "vPIC: 2001 Corvette, VIN character 8 'S' -> EngineModel 'LS6', 5.7L, 'HO'.", "vpic")],
         sibling=[]),
    dict(id="chevrolet_corvette_z06_c6_2006_2013", make="Chevrolet", model="Corvette", trim="Z06 (C6, 7.0 LS7)", years=[2006, 2013], status=V,
         ident=[dict(type="vpic_engine", make="CHEVROLET", model="Corvette", years=[2006, 2013], engine=r"7\.0L.*"),
                dict(type="vpic_trim", make="CHEVROLET", model="Corvette", years=[2006, 2013], trim=r"Z06.*")],
         epa=[dict(make="Chevrolet", model=r"^Corvette$", years=[2006, 2013], displ="7.0", expect="manual_only")],
         cites=[cite(W("Chevrolet_Corvette_(C6)"), "2006: 'Z06 debuts; 6-speed automatic with paddle shift available on non-Z06 models'.", "wikipedia"),
                cite(VPIC.format("1G1YY26E*75"), "vPIC: 2007 Corvette VIN character 8 'E' -> EngineModel 'LS7', 7.0L.", "vpic")],
         sibling=[]),
    dict(id="chevrolet_corvette_zr1_c6_2009_2013", make="Chevrolet", model="Corvette", trim="ZR1 (C6, 6.2 LS9 supercharged)", years=[2009, 2013], status=V,
         notes="vPIC's engine summary drops the supercharger, so the 6.2 LS9 cannot be told from the 6.2 LS3 (which had automatics) by displacement; only an exact trim matches.",
         ident=[dict(type="vpic_trim", make="CHEVROLET", model="Corvette", years=[2009, 2013], trim=r"ZR-?1.*")],
         epa=[dict(make="Chevrolet", model=r"^Corvette$", years=[2009, 2013], displ="6.2", charger="S", expect="manual_only")],
         cites=[cite(W("Chevrolet_Corvette_(C6)"), "ZR1: 'The manual transmission, steering and brakes were also borrowed from the Z06.'", "wikipedia")],
         sibling=[]),
    dict(id="chevrolet_camaro_z28_2014_2015", make="Chevrolet", model="Camaro", trim="Z/28 (7.0 LS7)", years=[2014, 2015], status=V,
         ident=[dict(type="vpic_engine", make="CHEVROLET", model="Camaro", years=[2014, 2015], engine=r"7\.0L.*"),
                dict(type="vpic_trim", make="CHEVROLET", model="Camaro", years=[2014, 2015], trim=r"Z/?28")],
         epa=[dict(make="Chevrolet", model=r"^Camaro$", years=[2014, 2015], displ="7.0", expect="manual_only")],
         cites=[cite("https://www.theautochannel.com/news/2013/03/29/070701-2014-camaro-z-28-most-track-capable-camaro-ever.html", "Chevrolet release (2014 Camaro Z/28): offered exclusively with a Tremec TR6060 six-speed manual; LS7 7.0L.", "manufacturer"),
                cite("https://tremec.com/2014-camaro-z28-iconic-muscle-car-makes-a-comeback/", "TREMEC: 2014 Camaro Z/28 with the TR-6060 six-speed manual.", "manufacturer")],
         sibling=["chevrolet_camaro_series_2010_2024"]),
    dict(id="chevrolet_camaro_ss_1le_2013_2015", make="Chevrolet", model="Camaro", trim="SS 1LE package (2013-2015); V6/SS 1LE (2017-2018)", years=[2013, 2018], status=V,
         notes="A package (RPO 1LE), not a VIN-coded trim: no identifier. The ZL1 1LE later got an automatic option, so ZL1 1LE is not in this rule.",
         ident=[dict(type="vpic_trim", make="CHEVROLET", model="Camaro", years=[2013, 2018], trim=r"(1SS|2SS|SS|1LT|LT) 1LE")],
         epa=[],
         cites=[cite(W("Chevrolet_Camaro_(fifth_generation)"), "'The 1LE package was offered on 1SS and 2SS coupe models, with an exclusive Tremec TR-6060/MM6 6-speed manual transmission...'", "wikipedia"),
                cite(W("Chevrolet_Camaro_(sixth_generation)"), "'For the 2017 model year, the 1LE Performance Packages returned, tailored for the V6 and V8 powered 6-speed manual-equipped coupé models respectively.'", "wikipedia")],
         sibling=["chevrolet_camaro_series_2010_2024"]),
    dict(id="chevrolet_cobalt_ss_supercharged_2005_2007", make="Chevrolet", model="Cobalt", trim="SS Supercharged (2.0 LSJ)", years=[2005, 2007], status=V,
         notes="The 2.0L LSJ was the only 2.0 Cobalt of these years (EPA 2.0 Cobalt rows: manual only). The naturally aspirated 2.4 SS (2006-2007) had an automatic and is excluded by the engine condition.",
         ident=[dict(type="vpic_engine", make="CHEVROLET", model="Cobalt", years=[2005, 2007], engine=r"2\.0L.*"),
                dict(type="vpic_trim", make="CHEVROLET", model="Cobalt", years=[2005, 2007], trim=r"Lev4 - Sport Coupe SS|SS Supercharged.*", engine=r"2\.0L.*")],
         epa=[dict(make="Chevrolet", model=r"^Cobalt$", years=[2005, 2007], displ="2.0", expect="manual_only")],
         cites=[cite(W("Chevrolet_Cobalt_SS"), "Infobox: '5-speed Saab F35 manual / 5-speed Getrag F23 manual / 4-speed 4T45 (Sport/SS N/A) automatic' (the supercharged LSJ coupe used the F35 manual).", "wikipedia")],
         sibling=["chevrolet_cobalt_ss_sc_2005_2007_char8_P"]),
    dict(id="chevrolet_cobalt_ss_turbo_2008_2010", make="Chevrolet", model="Cobalt", trim="SS (2.0 turbo LNF)", years=[2008, 2010], status=V,
         notes="The 2.0L LNF was the only 2.0 Cobalt of these years. vPIC's 2008 'SS Coupe' trim on a VIN whose engine character is not the LNF code is not matched (engine required).",
         ident=[dict(type="vpic_engine", make="CHEVROLET", model="Cobalt", years=[2008, 2010], engine=r"2\.0L.*")],
         epa=[dict(make="Chevrolet", model=r"^Cobalt( SS Coupe)?$", years=[2008, 2010], displ="2.0", expect="manual_only")],
         cites=[cite(W("Chevrolet_Cobalt_SS"), "Infobox: '5-speed Saab F35 manual / 5-speed Getrag F23 manual / 4-speed 4T45 (Sport/SS N/A) automatic' (the automatic only with the naturally aspirated engines).", "wikipedia")],
         sibling=["chevrolet_cobalt_series_2009_2010"]),
    dict(id="saturn_ion_red_line_2004_2007", make="Saturn", model="Ion", trim="Red Line (2.0 LSJ supercharged)", years=[2004, 2007], status=V,
         notes="'Red Line' on a Saturn Vue (2008-2009) is automatic-only and is excluded by the model condition.",
         ident=[dict(type="vpic_trim", make="SATURN", model="Ion", years=[2004, 2007], trim=r"(Coupe )?Red ?Line( Coupe| Tuner)?( \(HMD\))?|Coupe Red Line Tuner( \(HMD\))?"),
                dict(type="vpic_series", make="SATURN", model="Ion", years=[2004, 2007], trim=r"(Coupe )?Red ?Line( Coupe| Tuner)?( \(HMD\))?|Coupe Red Line Tuner( \(HMD\))?"),
                dict(type="vpic_engine", make="SATURN", model="Ion", years=[2004, 2007], engine=r"2\.0L.*")],
         epa=[dict(make="Saturn", model=r"^Ion", years=[2004, 2007], displ="2.0", expect="manual_only")],
         cites=[], sibling=["saturn_ion_redline_2004_2007_char8_P"]),
    dict(id="cadillac_cts_v_2004_2007", make="Cadillac", model="CTS-V", trim="CTS-V first generation", years=[2004, 2007], status=REF,
         notes="From MY2009 the CTS-V also had an automatic.", ident=[], epa=[], cites=[],
         sibling=["cadillac_cts_v_2004_2007_series_DN"]),
    # ------------------------------------------------------------- Chrysler family
    dict(id="dodge_viper_1992_2017", make="Dodge / SRT", model="Viper", trim="all", years=[1992, 2017], status=V,
         ident=[dict(type="vpic_model", make="DODGE|SRT|CHRYSLER", model="Viper", years=[1992, 2017]),
                dict(type="feed_model", make="Dodge|SRT|Chrysler", model="Viper", years=[1992, 2017])],
         epa=[dict(make="Dodge|SRT|Chrysler", model=r"^Viper", years=[1992, 2017], expect="manual_only")],
         cites=[cite(W("Dodge_Viper"), "Every generation used a six-speed manual (e.g. 'coupled by a Tremec TR-6060 six-speed manual transmission'); the automatic Hemi 'Firepower' was a concept only.", "wikipedia")],
         sibling=[]),
    dict(id="dodge_neon_srt4_2003_2005", make="Dodge", model="Neon", trim="SRT-4 (2.4 turbo)", years=[2003, 2005], status=V,
         ident=[dict(type="vpic_trim", make="DODGE|CHRYSLER", model="Neon|SRT-4", years=[2003, 2005], trim=r"SRT-?4"),
                dict(type="vpic_engine", make="DODGE|CHRYSLER", model="Neon", years=[2003, 2005], engine=r"2\.4L.*")],
         epa=[dict(make="Dodge", model=r"Neon", years=[2003, 2005], displ="2.4", charger="T", expect="manual_only")],
         cites=[cite(W("Dodge_Neon_SRT-4"), "Infobox transmission '5-speed NVG T-850 manual'.", "wikipedia")],
         sibling=["dodge_neon_srt4_2003_2005_char8_S"]),
    dict(id="dodge_caliber_srt4_2008_2009", make="Dodge", model="Caliber", trim="SRT4 (2.4 turbo)", years=[2008, 2009], status=V,
         ident=[dict(type="vpic_trim", make="DODGE", model="Caliber", years=[2008, 2009], trim=r"SRT-?4")],
         epa=[dict(make="Dodge", model=r"^Caliber$", years=[2008, 2009], displ="2.4", charger="T", expect="manual_only")],
         cites=[cite(W("Dodge_Caliber"), "Engine table: 'SRT4 || 2008–2009 || 2.4 L World I4 turbo ... || 6-speed Getrag manual, FWD'.", "wikipedia")],
         sibling=["dodge_caliber_srt4_2008_2009_char8_F"]),
    dict(id="dodge_spirit_rt_1991_1992", make="Dodge", model="Spirit", trim="R/T (2.2 Turbo III)", years=[1991, 1992], status=V,
         notes="EPA lists the 1991-1992 Spirit 2.2 only as the turbo with a 5-speed manual. vPIC's engine summary has no turbo flag, so the identifier needs the exact R/T trim.",
         ident=[dict(type="vpic_trim", make="DODGE", model="Spirit", years=[1991, 1992], trim=r"R/?T")],
         epa=[dict(make="Dodge", model=r"^Spirit$", years=[1991, 1992], displ="2.2", charger="T", expect="manual_only")],
         cites=[cite(W("Dodge_Spirit"), "'All the Spirit R/Ts came with the A-568 heavy-duty 5-speed manual transmission.'", "wikipedia")],
         sibling=[]),
    dict(id="fiat_500_abarth_2012_2014", make="Fiat", model="500", trim="Abarth (1.4 turbo)", years=[2012, 2014], status=V,
         notes="From MY2015 the Abarth also had a 6-speed automatic (EPA row 35158).",
         ident=[dict(type="vpic_trim", make="FIAT", model="500", years=[2012, 2014], trim=r"Abarth")],
         epa=[dict(make="Fiat", model=r"^500 Abarth$", years=[2012, 2014], expect="manual_only")],
         cites=[], sibling=["fiat_500_turbo_2012_2014_series_FHJ_char8_H"]),
    dict(id="dodge_stealth_rt_turbo_mitsubishi_3000gt_vr4", make="Dodge / Mitsubishi", model="Stealth / 3000GT", trim="R/T Turbo / VR-4 (twin turbo)", years=[1991, 1999], status=REF,
         ident=[], epa=[], cites=[], sibling=["mitsubishi_3000gt_stealth_twin_turbo_1991_1992_char8", "mitsubishi_3000gt_stealth_twin_turbo_1993_1999_char8"]),
    # ------------------------------------------------------------- Hyundai / Genesis
    dict(id="hyundai_genesis_coupe_r_spec_2010_2013", make="Hyundai", model="Genesis Coupe", trim="2.0T R-Spec / 3.8 R-Spec", years=[2010, 2013], status=V,
         notes="Not recognisable from the VIN: Hyundai's model-series character covers the grade (GL/GLS), not the R-Spec, and vPIC returns only 'GL'/'GLS' grades on the lots. Years limited to the releases read (2010-2013).",
         ident=[dict(type="vpic_trim", make="HYUNDAI", model="Genesis Coupe", years=[2010, 2013], trim=r"(2\.0T |3\.8 )?R-?Spec")],
         epa=[],
         cites=[cite("https://www.autoguide.com/auto-news/2009/10/breaking-hyundai-genesis-coupe-2-0t-r-spec-is-built-for-tuners.html", "2010 Genesis Coupe 2.0T R-Spec: will only be available with a manual transmission.", "review"),
                cite("https://www.motorauthority.com/news/1049335_2011-hyundai-genesis-coupe-r-spec-priced-from-24500", "2011 Genesis Coupe 2.0T R-Spec and 3.8 R-Spec: both available only with a six-speed manual transmission.", "review"),
                cite("https://prnewswire.com/news-releases/hyundai-motor-america-announces-2013-genesis-coupe-pricing-139292923.html", "Hyundai 2013 Genesis Coupe pricing: 2.0T R-Spec and 3.8 R-Spec listed with the six-speed manual.", "manufacturer")],
         sibling=[]),
    dict(id="hyundai_veloster_turbo_r_spec_2014", make="Hyundai", model="Veloster", trim="Turbo R-Spec (1.6T)", years=[2014, 2014], status=V,
         notes="vPIC returns blobs ('Standard / Turbo / R-Spec / Rally Edition', 'GLS(1.6 STD, STyle, Tech /1.6T...') that never match. 2015-2016 R-Spec not ruled (sources read cover the 2014 launch).",
         ident=[dict(type="vpic_trim", make="HYUNDAI", model="Veloster", years=[2014, 2014], trim=r"(Turbo )?R-?Spec")],
         epa=[],
         cites=[cite("https://www.autocar.co.uk/node/58616", "Veloster Turbo R-Spec: 'only available with a six-speed manual transmission and a short-throw B&M Racing gearlever'.", "review"),
                cite("https://www.conceptcarz.com/z23402/Hyundai-Veloster-Turbo-R-Spec.aspx", "Hyundai release 'Turbo R-Spec model joins Veloster line-up': 6-speed close-ratio manual transmission.", "manufacturer")],
         sibling=[]),
    dict(id="hyundai_veloster_n_2019_2020", make="Hyundai", model="Veloster N", trim="all", years=[2019, 2020], status=V,
         notes="From MY2021 the Veloster N had an 8-speed DCT (EPA row 42927).",
         ident=[dict(type="vpic_model", make="HYUNDAI", model="Veloster N", years=[2019, 2020])],
         epa=[dict(make="Hyundai", model=r"^Veloster N$", years=[2019, 2020], expect="manual_only")],
         cites=[], sibling=["hyundai_veloster_n_2019_2020"]),
    dict(id="genesis_g70_20t_sport_mt_2019_2021", make="Genesis", model="G70", trim="2.0T Sport (manual)", years=[2019, 2021], status=REF,
         ident=[], epa=[], cites=[], sibling=["genesis_g70_20t_sport_mt_2019_2021"]),
    # ------------------------------------------------------------- VW / Audi / BMW / Saab / MINI
    dict(id="vw_r32_2004", make="Volkswagen", model="R32", trim="R32 (Mk4, 3.2 VR6)", years=[2004, 2004], status=V,
         notes="The 2008 R32 (Mk5) was DSG-only in the US (EPA row 24326).",
         ident=[dict(type="vpic_model", make="VOLKSWAGEN", model="R32|Golf R32", years=[2004, 2004]),
                dict(type="feed_model", make="Volkswagen", model="R32", years=[2004, 2004])],
         epa=[dict(make="Volkswagen", model=r"^R32$", years=[2004, 2004], expect="manual_only")],
         cites=[cite("https://www.cargurus.com/research/2004-Volkswagen-R32-c5871", "2004 R32: six-speed manual; an automatic was not available.", "review"),
                cite("https://www.cars.com/articles/2004-volkswagen-r32-whats-new-1420687141802", "2004 R32 what's new: 240 hp VR6, 6-speed manual.", "review")],
         sibling=["vw_wvw_char4_series_transmission_2006_2010"]),
    dict(id="vw_golf_r_2012_2013", make="Volkswagen", model="Golf R", trim="Golf R (Mk6)", years=[2012, 2013], status=V,
         notes="No 2014 Golf R in the US; the 2015 Golf R was DSG-only (EPA row 35939) and 2016-2019 had both.",
         ident=[dict(type="vpic_model", make="VOLKSWAGEN", model="Golf R", years=[2012, 2013]),
                dict(type="feed_model", make="Volkswagen", model="Golf R", years=[2012, 2013])],
         epa=[dict(make="Volkswagen", model=r"^Golf R$", years=[2012, 2013], expect="manual_only")],
         cites=[cite(W("Volkswagen_Golf_Mk6"), "'Volkswagen announced that the Golf R will be available in the United States beginning in 2012, in both two- and four-door versions ... but without the DSG transmission'.", "wikipedia")],
         sibling=[]),
    dict(id="vw_new_beetle_turbo_s_2002_2004", make="Volkswagen", model="New Beetle", trim="Turbo S (1.8T 180 hp)", years=[2002, 2004], status=V,
         notes="EPA's only 6-speed manual New Beetle rows (2002-2004 1.8T) are the Turbo S; the 150 hp 1.8T had a 5-speed manual or automatic.",
         ident=[dict(type="vpic_trim", make="VOLKSWAGEN", model="Beetle|New Beetle", years=[2002, 2004], trim=r"Turbo S")],
         epa=[dict(make="Volkswagen", model=r"^New Beetle$", years=[2002, 2004], displ="1.8", charger="T", expect="manual_listed")],
         cites=[cite("https://www.edmunds.com/volkswagen/new-beetle/2002/review/", "2002 New Beetle review: the 180-hp 1.8T is exclusive to the Turbo S and its six-speed manual gearbox.", "review"),
                cite("https://www.machinedesign.com/archive/2002-vw-new-beetle-turbo-s", "2002 New Beetle Turbo S: six-speed manual; no automatic available.", "review")],
         sibling=[]),
    dict(id="audi_rs4_2007_2008", make="Audi", model="RS 4", trim="RS 4 (B7, 4.2 V8)", years=[2007, 2008], status=V,
         ident=[dict(type="vpic_model", make="AUDI", model="RS ?4", years=[2007, 2008])],
         epa=[dict(make="Audi", model=r"^RS4", years=[2007, 2008], expect="manual_only")],
         cites=[cite(W("Audi_RS_4"), "B7 RS 4: infobox '6-speed manual'; 'A six-speed manual transmission ... and Audi's Torsen-based quattro system ... were standard.'", "wikipedia")],
         sibling=[]),
    dict(id="audi_tt_rs_2012_2013", make="Audi", model="TT RS", trim="TT RS (Mk2)", years=[2012, 2013], status=V,
         notes="US TT RS 2012-2013 manual only; the 2018+ TT RS is S tronic only.",
         ident=[dict(type="vpic_model", make="AUDI", model="TT RS", years=[2012, 2013])],
         epa=[dict(make="Audi", model=r"^TT RS Coupe$", years=[2012, 2013], expect="manual_only")],
         cites=[cite(W("Audi_TT"), "'The TT RS has a new short-shift close-ratio six-speed manual transmission...'", "wikipedia")],
         sibling=[]),
    dict(id="bmw_m3_e30_1988_1991", make="BMW", model="M3", trim="E30 M3", years=[1988, 1991], status=V,
         notes="The E36 M3 had a 5-speed automatic from 1995 (EPA rows 11642, 13312) and is not in this rule.",
         ident=[dict(type="vpic_model", make="BMW", model="M3", years=[1988, 1991])],
         epa=[dict(make="BMW", model=r"^M3$", years=[1988, 1991], expect="manual_only")],
         cites=[cite(W("BMW_M3"), "E30 M3: infobox '5-speed manual'; 'The transmission was a Getrag 265 5-speed manual.'", "wikipedia")],
         sibling=["bmw_ag_code_1981_1990"]),
    dict(id="bmw_z3_m_roadster_coupe_1998_2002", make="BMW", model="M Roadster / M Coupe", trim="Z3 M Roadster and M Coupe", years=[1998, 2002], status=SS,
         ident=[dict(type="vpic_model", make="BMW", model="M Roadster|M Coupe|Z3 M.*", years=[1998, 2002])],
         epa=[dict(make="BMW", model=r"^M (Roadster|Coupe)$", years=[1998, 2002], expect="manual_only")],
         cites=[], sibling=[]),
    dict(id="bmw_z4_m_2006_2008", make="BMW", model="Z4 M", trim="Z4 M Roadster and Coupe", years=[2006, 2008], status=SS,
         ident=[dict(type="vpic_model", make="BMW", model="Z4 M|Z4 M Roadster|Z4 M Coupe", years=[2006, 2008])],
         epa=[dict(make="BMW", model=r"^Z4 M", years=[2006, 2008], expect="manual_only")],
         cites=[], sibling=[]),
    dict(id="bmw_m5_e34_1991_1993_e39_2000_2003", make="BMW", model="M5", trim="E34 M5 (1991-1993) and E39 M5 (2000-2003)", years=[1991, 2003], status=V,
         notes="Years 1994-1999: no US M5. The E60 M5 (2006-2010) had the SMG (automated) and is not in this rule.",
         ident=[dict(type="vpic_model", make="BMW", model="M5", years=[1991, 1993]),
                dict(type="vpic_model", make="BMW", model="M5", years=[2000, 2003])],
         epa=[dict(make="BMW", model=r"^M5$", years=[1991, 2003], expect="manual_only")],
         cites=[], sibling=["bmw_m5_e39_manual_only"]),
    dict(id="saab_9_3_viggen_1999_2002", make="Saab", model="9-3", trim="Viggen", years=[1999, 2002], status=V,
         ident=[dict(type="vpic_trim", make="SAAB", model="9-3", years=[1999, 2002], trim=r"Viggen")],
         epa=[dict(make="Saab", model=r"9-3 Viggen", years=[1999, 2002], expect="manual_only")],
         cites=[cite(W("Saab_9-3"), "'The Viggen is only available with a five-speed manual transmission...'", "wikipedia")],
         sibling=["saab_ys3_char7_gearbox_1988_2001"]),
    dict(id="mini_john_cooper_works_2009_2012", make="MINI", model="Cooper", trim="John Cooper Works (R56/R55/R57)", years=[2009, 2012], status=REF,
         ident=[], epa=[], cites=[], sibling=["mini_john_cooper_works_2009_2012"]),
    dict(id="mini_cooper_s_r53_2003_2004", make="MINI", model="Cooper S", trim="Cooper S (R53)", years=[2003, 2004], status=REF,
         ident=[], epa=[], cites=[], sibling=["mini_cooper_s_r53_re33_2003_2004"]),
    dict(id="nissan_350z_track_2003_2005", make="Nissan", model="350Z", trim="Track", years=[2003, 2005], status=CF,
         notes="Sources disagree (dealer and auction listings describe both a 6-speed manual and a 5-speed automatic for 2003 Track cars); not ruled.",
         ident=[], epa=[], cites=[cite("https://classic.com/m/nissan/z-car/350z/track", "2003 350Z Track listings: mostly 6-speed manual; some sources describe an automatic choice.", "enthusiast")],
         sibling=[]),
]


# Trim names often believed manual-only that were NOT (for the years given).
NOT_MANUAL_ONLY = [
    dict(trim="Chevrolet HHR SS", years=[2008, 2010], why="EPA lists the 2.0T HHR with a 4-speed automatic in every SS year.", epa_ids=[25123, 25610, 28739],
         cites=[EPA_URL]),
    dict(trim="Hyundai Elantra GT N Line", years=[2019, 2020], why="EPA lists the 1.6T Elantra GT with a 7-speed dual-clutch (AM7 / AM-S7) as well as the 6-speed manual.", epa_ids=[40895, 41560], cites=[EPA_URL]),
    dict(trim="Subaru WRX (non-STI)", years=[2002, 2010], why="4-speed automatic offered (EPA 2.0T/2.5T Impreza automatic rows, e.g. 17466, 24307).", epa_ids=[17466, 24307], cites=[EPA_URL]),
    dict(trim="Subaru WRX", years=[2015, 2021], why="CVT (Sport Lineartronic) offered: EPA 'WRX Automatic (AV-S8)' rows.", epa_ids=[34668, 43628], cites=[EPA_URL, W("Subaru_WRX")]),
    dict(trim="Mitsubishi Lancer Evolution X MR", years=[2008, 2014], why="6-speed TC-SST dual-clutch only (EPA Automatic (S6)/(AM6) rows every year).", epa_ids=[25164, 28594], cites=[EPA_URL]),
    dict(trim="Nissan Sentra SE-R (non-Spec V)", years=[2007, 2012], why="Xtronic CVT only.", epa_ids=[23962], cites=["https://global.nissannews.com/en/releases/200-horsepower-se-r-model-joins-2007-sentra-lineup-offers-serious-performance-at-an-affordable-price"]),
    dict(trim="Nissan 370Z NISMO", years=[2015, 2020], why="7-speed automatic added for MY2015.", epa_ids=[], cites=["https://www.cars.com/articles/2015-nissan-370z-nismo-gets-new-styling-transmission-1420663015990"]),
    dict(trim="Nissan Juke NISMO RS AWD", years=[2015, 2017], why="CVT only (EPA 'Juke Nismo RS AWD' Automatic (AV-S8)).", epa_ids=[35944], cites=[EPA_URL]),
    dict(trim="Volkswagen Golf R", years=[2015, 2019], why="2015: DSG only (EPA 35939); 2016-2019: DSG or manual.", epa_ids=[35939, 36401], cites=[EPA_URL]),
    dict(trim="Volkswagen R32 (Mk5)", years=[2008, 2008], why="DSG only (EPA 24326).", epa_ids=[24326], cites=[EPA_URL]),
    dict(trim="Fiat 500 Abarth", years=[2015, 2019], why="6-speed automatic offered from MY2015 (EPA 35158).", epa_ids=[35158], cites=[EPA_URL]),
    dict(trim="Ford Shelby GT500", years=[2020, 2022], why="7-speed dual-clutch only (EPA 'Shelby GT500 Mustang' AM7, row 42139).", epa_ids=[42139], cites=[EPA_URL]),
    dict(trim="Ford Taurus SHO 3.2", years=[1993, 1995], why="The 3.2 SHO was automatic-only (EPA 29005, 11007, 11958).", epa_ids=[29005, 11007, 11958], cites=[EPA_URL, W("Ford_Taurus_SHO")]),
    dict(trim="Chevrolet Cobalt SS 2.4 (naturally aspirated)", years=[2006, 2007], why="4-speed 4T45 automatic offered.", epa_ids=[], cites=[W("Chevrolet_Cobalt_SS")]),
    dict(trim="Toyota Corolla XRS (2.4)", years=[2009, 2010], why="5-speed automatic offered.", epa_ids=[], cites=[W("Toyota_Corolla_(E120)")]),
    dict(trim="Toyota GR Corolla", years=[2025, 2026], why="8-speed GR-DAT automatic added (EPA 48595).", epa_ids=[48595], cites=[EPA_URL]),
    dict(trim="Hyundai Veloster N", years=[2021, 2022], why="8-speed DCT added (EPA 42927).", epa_ids=[42927, 43831], cites=[EPA_URL]),
    dict(trim="BMW M3 (E36)", years=[1995, 1999], why="5-speed automatic offered (EPA 11642, 13312, 14017).", epa_ids=[11642, 13312, 14017], cites=[EPA_URL]),
    dict(trim="Honda del Sol Si / Prelude Si / Accord Si", years=[1984, 1997], why="Automatics offered; vPIC labels on the lots include automatics for del Sol Si and Prelude Si. Only the Civic Si (1999 on) is manual-only.", epa_ids=[], cites=[W("Honda_CR-X_del_Sol")]),
    dict(trim="Mitsubishi Eclipse GS-T / GSX (turbo)", years=[1991, 1999], why="4-speed automatic offered with the 2.0 turbo from 1991 (EPA 7652); only 1990 was manual-only.", epa_ids=[7652], cites=[EPA_URL]),
    dict(trim="Chevrolet Beretta GTZ", years=[1991, 1993], why="From 1991 the GTZ could have the 3.1 V6 with a 3-speed automatic.", epa_ids=[], cites=[W("Chevrolet_Beretta")]),
    dict(trim="Pontiac Solstice GXP / Saturn Sky Red Line", years=[2007, 2010], why="5-speed automatic offered (step-2 GM filings: 2008 MG = turbo AUTO).", epa_ids=[], cites=["scraper/manual_detect/vin_rules_5.json"]),
    dict(trim="Cadillac CTS-V", years=[2009, 2015], why="6-speed automatic offered.", epa_ids=[], cites=[W("Cadillac_CTS")]),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
_TRANSLIT = {**{str(i): i for i in range(10)},
             **dict(zip("ABCDEFGH", range(1, 9))), **dict(zip("JKLMN", range(1, 6))),
             "P": 7, "R": 9, **dict(zip("STUVWXYZ", range(2, 10)))}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"


def check_digit_ok(vin):
    if len(vin) != 17 or any(ch not in _TRANSLIT for ch in vin):
        return False
    r = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS)) % 11
    return vin[8] == ("X" if r == 10 else str(r))


def vin_year(vin, hint):
    i = _YEAR_CODES.find(vin[9]) if len(vin) == 17 else -1
    if i < 0:
        return None
    cands = [1980 + i] + ([2010 + i] if i < 21 else [])
    if not hint:
        return cands[0] if len(cands) == 1 else None
    best = min(cands, key=lambda y: abs(y - hint))
    return best if abs(best - hint) <= 2 else None


def tclass(t):
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


def fm(rx, s):
    return re.fullmatch(rx, (s or "").strip(), re.I) is not None


def to_int(y):
    try:
        return int(str(y)[:4])
    except (TypeError, ValueError):
        return None


def match_ident(idn, car):
    """car: dict(vin, year (feed), make, model (feed), dec (corrected vPIC or None))."""
    t = idn["type"]
    y0, y1 = idn["years"]
    if t == "feed_model":
        y = to_int(car["year"])
        return (y is not None and y0 <= y <= y1 and fm(idn["make"], car["make"]) and fm(idn["model"], car["model"]))
    if t == "vin_regex":
        vin = car["vin"]
        if not vin or not check_digit_ok(vin) or not re.match(idn["regex"], vin):
            return False
        y = vin_year(vin, to_int(car["year"]))
        return y is not None and y0 <= y <= y1
    d = car["dec"]
    if not d:
        return False
    y = to_int(d.get("modelYear"))
    if y is None or not (y0 <= y <= y1):
        return False
    if not fm(idn["make"], d.get("make")) or not fm(idn["model"], d.get("model")):
        return False
    if t == "vpic_model":
        return True
    if t == "vpic_engine":
        return fm(idn["engine"], d.get("engine"))
    field = "trim" if t == "vpic_trim" else "series"
    if not fm(idn["trim"], d.get(field)):
        return False
    if idn.get("engine") and not fm(idn["engine"], d.get("engine")):
        return False
    if idn.get("drive") and not fm(idn["drive"], d.get("driveType")):
        return False
    if idn.get("vin") and not re.match(idn["vin"], car["vin"] or ""):
        return False
    return True


def epa_rows():
    if not EPA_CSV.exists():
        return None
    with EPA_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def epa_eval(q, rows):
    out = []
    for r in rows:
        if not re.fullmatch(q["make"], r["make"], re.I):
            continue
        if not re.search(q["model"], r["model"], re.I):
            continue
        y = int(r["year"])
        if not (q["years"][0] <= y <= q["years"][1]):
            continue
        if q.get("displ") and r["displ"] != q["displ"]:
            continue
        ch = ("T" if r["tCharger"] else "") + ("S" if r["sCharger"] == "S" else "")
        if q.get("charger") is not None and q.get("charger") != "" and q["charger"] not in ch:
            continue
        out.append({"id": int(r["id"]), "year": y, "model": r["model"], "displ": r["displ"],
                    "charger": ch, "trany": r["trany"], "drive": r["drive"],
                    "url": EPA_ROW.format(r["id"])})
    classes = Counter("manual" if x["trany"].startswith("Manual") else "other" for x in out)
    if q["expect"] == "manual_only":
        ok = bool(out) and classes["other"] == 0
    else:
        ok = classes["manual"] > 0
    years_seen = sorted({x["year"] for x in out})
    return {"query": {k: q[k] for k in q if k != "expect"}, "expect": q["expect"], "check": "pass" if ok else "FAIL",
            "rows": len(out), "manual_rows": classes["manual"], "non_manual_rows": classes["other"],
            "years_with_rows": years_seen,
            "row_ids": [x["id"] for x in sorted(out, key=lambda x: (x["year"], x["id"]))],
            "rows_detail": [f'{x["id"]} {x["year"]} {x["model"]} {x["displ"]}{x["charger"]} {x["trany"]}' for x in sorted(out, key=lambda x: (x["year"], x["id"]))][:40]}


def load_step2():
    """car ids / VINs already newly confirmed by the step-2 rule sets."""
    ids, vins, by = set(), set(), defaultdict(set)
    rule_cites = {}
    for p in sorted(HERE.glob("vin_rules_*.json")) + [HERE / "epa_sole.json"]:
        if not p.exists() or p.name.endswith("_vpic.json"):
            continue
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for r in d.get("rules", []):
            rule_cites[r.get("id")] = {"file": p.name, "status": r.get("status"),
                                       "citations": [{"url": c.get("url"), "doc": c.get("doc") or c.get("says", "")[:200]}
                                                     for c in (r.get("citations") or [])[:4] if isinstance(c, dict)]}
        for rec in d.get("newly_confirmed_manual_cars", []) or []:
            ids.add(str(rec.get("id")))
            if rec.get("vin"):
                vins.add(rec["vin"])
            by[p.name].add(str(rec.get("id")))
    return ids, vins, by, rule_cites


# ---------------------------------------------------------------------------
def main():
    inv = json.loads((DATA / "inventory_live.json").read_text())
    extras = json.loads((DATA / "vehicle_extras.json").read_text())["extras"]
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache_exported = cache.pop("_exportedAt", "")
    fi = {f: i for i, f in enumerate(inv["fields"])}
    yards = inv["yards"]
    rows = epa_rows()
    step2_ids, step2_vins, step2_by, rule_cites = load_step2()

    def decode(vin):
        raw = cache.get(vin) if vin else None
        return js._correct_vpic(raw, vin) if isinstance(raw, dict) else None

    # ---- ground truth -------------------------------------------------------
    gt = []
    with (HERE / "ground_truth.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            vin = (r.get("vin") or "").upper()
            dec = decode(vin)
            if dec is None and r.get("vpicMake"):
                dec = {"make": r.get("vpicMake"), "model": r.get("vpicModel"), "modelYear": r.get("vpicYear"),
                       "trim": r.get("trim"), "series": r.get("series"), "engine": r.get("engine") if r.get("source") == "vin" else "",
                       "driveType": r.get("drive")}
            gt.append(({"vin": vin, "year": r.get("year"), "make": r.get("make"), "model": r.get("model"), "dec": dec}, r))

    # ---- lots ----------------------------------------------------------------
    lot = []
    for row in inv["vehicles"]:
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        ex = list(extras.get(vid) or []) + [""] * 5
        y = yards[row[fi["yard"]]] if isinstance(row[fi["yard"]], int) else None
        raw = cache.get(vin) if vin else None
        lot.append({"id": vid, "vin": vin, "year": row[fi["year"]], "make": row[fi["make"]] or "", "model": row[fi["model"]] or "",
                    "yard": y[0] if y else "", "state": y[2] if y else "", "trans": ex[3] or "", "transSrc": ex[4] or "",
                    "dec": decode(vin), "inCache": isinstance(raw, dict)})

    # Every decode in the cache backup that carries a transmission (not only
    # lot cars): a wider, still vPIC-based, check of the vPIC/VIN identifiers.
    # _correct_vpic has already dropped the distrusted uniform-manual cells.
    cache_cars = []
    for vin, raw in cache.items():
        if not isinstance(raw, dict) or not raw.get("transmission"):
            continue
        dec = js._correct_vpic(raw, vin)
        if not dec.get("transmission"):
            continue
        cache_cars.append(({"vin": vin, "year": to_int(dec.get("modelYear")), "make": "", "model": "", "dec": dec},
                           tclass(dec["transmission"])))

    out_trims = []
    newly_all, conflicts_all = [], []
    cache_tot = Counter()
    totals = Counter()
    gt_tot = Counter()
    for T in TRIMS:
        idents = T.get("ident") or []
        # EPA
        epa_checks = [epa_eval(q, rows) for q in T.get("epa", [])] if rows is not None else []
        # validation
        val = Counter()
        val_by_ident = defaultdict(Counter)
        val_examples = []
        for car, r in gt:
            hit = [i for i, idn in enumerate(idents) if match_ident(idn, car)]
            if not hit:
                continue
            c = r.get("transClass") or ""
            if r.get("uniformCell"):
                key = "uniform_cell_unlabelled"
            elif c == "manual":
                key = "manual"
            elif c in ("automatic", "cvt", "dct", "amt"):
                key = "non_manual"
            else:
                key = "speeds_only_unknown"
            val[key] += 1
            val[f"source_{r.get('source')}"] += 1
            for i in hit:
                val_by_ident[i][key] += 1
            if key == "non_manual" and len(val_examples) < 10:
                val_examples.append({"id": r["id"], "vin": r.get("vin"), "year": r.get("year"), "make": r.get("make"), "model": r.get("model"),
                                     "trim": r.get("trim"), "engine": r.get("engine"), "trans": r.get("trans"), "source": r.get("source")})
        checkable = val["manual"] + val["non_manual"]
        validation = {"ground_truth_matched": sum(val[k] for k in ("manual", "non_manual", "uniform_cell_unlabelled", "speeds_only_unknown")),
                      "manual": val["manual"], "non_manual": val["non_manual"],
                      "uniform_cell_unlabelled": val["uniform_cell_unlabelled"], "speeds_only_unknown": val["speeds_only_unknown"],
                      "from_vin": val["source_vin"], "from_listing": val["source_listing"],
                      "agreement": round(val["manual"] / checkable, 4) if checkable else None,
                      "by_identifier": {f'{i}:{idents[i]["type"]}': dict(c) for i, c in sorted(val_by_ident.items())},
                      "non_manual_examples": val_examples}
        cv = Counter()
        cv_examples = []
        vidents = [i for i in idents if i["type"] != "feed_model"]
        for car, c in cache_cars:
            if any(match_ident(idn, car) for idn in vidents):
                k = "manual" if c == "manual" else ("non_manual" if c in ("automatic", "cvt", "dct", "amt") else "speeds_only_unknown")
                cv[k] += 1
                if k == "non_manual" and len(cv_examples) < 8:
                    d = car["dec"]
                    cv_examples.append({"vin": car["vin"], "vpic": f'{d.get("modelYear")} {d.get("make")} {d.get("model")} {d.get("trim")} {d.get("engine")}', "transmission": d.get("transmission")})
        validation["decode_cache_all_vins"] = {"manual": cv["manual"], "non_manual": cv["non_manual"], "speeds_only_unknown": cv["speeds_only_unknown"],
                                               "non_manual_examples": cv_examples}
        if T["status"] == V:
            cache_tot["manual"] += cv["manual"]
            cache_tot["non_manual"] += cv["non_manual"]
        if T["status"] == V:
            gt_tot["manual"] += val["manual"]
            gt_tot["non_manual"] += val["non_manual"]
            gt_tot["uniform"] += val["uniform_cell_unlabelled"]
        # lots
        lc = Counter()
        newly, conflicts = [], []
        for car in lot:
            hit = [i for i, idn in enumerate(idents) if match_ident(idn, car)]
            if not hit:
                continue
            lc["matched"] += 1
            c = tclass(car["trans"])
            if c == "manual":
                lc["already_manual"] += 1
                continue
            if c:
                lc["published_non_manual"] += 1
                conflicts.append({"id": car["id"], "vin": car["vin"], "year": car["year"], "make": car["make"], "model": car["model"],
                                  "published": car["trans"], "transSrc": car["transSrc"], "yard": car["yard"],
                                  "identifiers": [idents[i]["type"] for i in hit], "rule": T["id"]})
                continue
            if car["state"] in CANADA:
                lc["no_trans_canadian_yard"] += 1
                continue
            lc["no_trans"] += 1
            why = ("no_vin" if not car["vin"] else "vin_not_in_cache" if not car["inCache"] else "vpic_trans_blank_or_distrusted")
            in_step2 = car["id"] in step2_ids or (car["vin"] and car["vin"] in step2_vins)
            lc["no_trans_also_step2"] += in_step2
            d = car["dec"] or {}
            newly.append({"id": car["id"], "vin": car["vin"], "year": car["year"], "make": car["make"], "model": car["model"],
                          "vpic": {"model": d.get("model"), "year": d.get("modelYear"), "trim": d.get("trim"), "series": d.get("series"),
                                   "engine": d.get("engine"), "drive": d.get("driveType")},
                          "identifiers": [f'{i}:{idents[i]["type"]}' for i in hit], "why_no_trans": why,
                          "also_confirmed_by_step2": bool(in_step2), "yard": car["yard"], "rule": T["id"], "rule_status": T["status"]})
        counted = T["status"] == V
        for n in newly:
            n["counted"] = counted
        newly_all.extend(newly)
        conflicts_all.extend(conflicts)
        if counted:
            totals["newly_confirmed"] += len(newly)
            totals["newly_confirmed_not_in_step2"] += sum(1 for n in newly if not n["also_confirmed_by_step2"])
            totals["published_non_manual_conflicts"] += len(conflicts)
        epa_ok = all(e["check"] == "pass" for e in epa_checks)
        entry = {k: T[k] for k in ("id", "make", "model", "trim", "years", "status") if k in T}
        entry.update({
            "market": "US",
            "claim": "manual",
            "counted": counted,
            "notes": T.get("notes", ""),
            "identification": idents,
            "identifiable_from_vin_decode": any(i["type"] != "feed_model" for i in idents),
            "evidence": T.get("cites", []),
            "epa": epa_checks,
            "epa_checks_pass": epa_ok if epa_checks else None,
            "step2_rules": [{"id": s, **(rule_cites.get(s) or {"file": None, "status": "not found in step-2 outputs"})} for s in T.get("sibling", [])],
            "validation": validation,
            "lots": {"matched": lc["matched"], "already_manual": lc["already_manual"],
                     "published_non_manual": lc["published_non_manual"],
                     "no_trans_info": lc["no_trans"], "no_trans_info_also_confirmed_by_step2": lc["no_trans_also_step2"],
                     "no_trans_info_canadian_yard_not_counted": lc["no_trans_canadian_yard"]},
        })
        if T["status"] == V and epa_checks and not epa_ok:
            entry["status_warning"] = "an EPA expectation failed; review before use"
        out_trims.append(entry)

    # Same trim NAME on other models/years: the name alone is not evidence.
    name_check = {}
    for label, rx in (("Si", r"S[Ii]"), ("Type-S", r"Type-?S"), ("SS", r"SS"), ("R/T", r"R/T"), ("ST", r"ST"),
                      ("Red Line", r"Red ?Line"), ("GT", r"GT"), ("SRT", r"SRT.*")):
        cc = defaultdict(Counter)
        for car, r in gt:
            d = car["dec"] or {}
            if r.get("uniformCell") or not fm(rx, d.get("trim")):
                continue
            c = r.get("transClass") or ""
            cc[f'{d.get("make")} {d.get("model")} {d.get("modelYear")}']["manual" if c == "manual" else ("non_manual" if c in ("automatic", "cvt", "dct", "amt") else "unknown")] += 1
        name_check[label] = {k: dict(v) for k, v in sorted(cc.items()) if v.get("non_manual") or v.get("manual")}

    status_counts = Counter(t["status"] for t in TRIMS)
    summary = {
        "trims": len(TRIMS),
        "trims_by_status": dict(status_counts),
        "verified_trims": status_counts[V],
        "verified_trims_with_a_vin_decode_identifier": sum(1 for t in out_trims if t["status"] == V and t["identifiable_from_vin_decode"]),
        "verified_trims_matching_any_lot_car": sum(1 for t in out_trims if t["status"] == V and t["lots"]["matched"]),
        "ground_truth_on_verified_trims": {"manual": gt_tot["manual"], "non_manual": gt_tot["non_manual"],
                                           "uniform_cell_unlabelled": gt_tot["uniform"],
                                           "precision": round(gt_tot["manual"] / (gt_tot["manual"] + gt_tot["non_manual"]), 4)
                                           if gt_tot["manual"] + gt_tot["non_manual"] else None},
        "decode_cache_check_on_verified_trims": {"what": "all 459k cached VIN decodes with a vPIC transmission (lot or not), corrected by _correct_vpic",
                                                 "manual": cache_tot["manual"], "non_manual": cache_tot["non_manual"],
                                                 "precision": round(cache_tot["manual"] / (cache_tot["manual"] + cache_tot["non_manual"]), 4)
                                                 if cache_tot["manual"] + cache_tot["non_manual"] else None},
        "newly_confirmed_manual_lot_cars": totals["newly_confirmed"],
        "newly_confirmed_manual_lot_cars_not_already_in_step2": totals["newly_confirmed_not_in_step2"],
        "newly_confirmed_by_rule": dict(Counter(n["rule"] for n in newly_all if n["counted"])),
        "listed_not_counted_by_rule": dict(Counter(n["rule"] for n in newly_all if not n["counted"])),
        "published_non_manual_conflicts_on_verified_trims": totals["published_non_manual_conflicts"],
        "epa_checks_failed": [t["id"] for t in out_trims if t.get("epa_checks_pass") is False],
    }
    doc = {
        "worklist": "step 3: US-market trims sold only with a manual transmission",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/manual_trims.py",
        "inputs": {"inventory_live": "docs/data/inventory_live.json (current scan)", "vehicle_extras": "docs/data/vehicle_extras.json",
                   "vin_decodes": f"docs/data/vin_decodes.json.gz (exported {cache_exported}), corrected with junkyard_scraper._correct_vpic",
                   "ground_truth": "scraper/manual_detect/ground_truth.jsonl (build_baseline.py)",
                   "epa": "scraper/manual_detect/epa/vehicles.csv (" + EPA_URL + ")" if rows is not None else "missing",
                   "step2": "vin_rules_0..7.json, epa_sole.json (overlap only)"},
        "method": {
            "claim": "A trim is listed as manual-only for the stated US model years only. Years in which the trim name also came with an automatic are excluded and listed in not_manual_only.",
            "identification": "Only from the VIN decode (vPIC Trim/Series exact match, vPIC model name, vPIC engine displacement where it is unique to the trim) or a VIN pattern whose meaning is cited (Part 565 filing or vPIC pattern decode). feed_model only where the yard's model name IS the trim (S2000, Viper, Lancer Evolution 2003-2006, Golf R, R32, GR Corolla). Blobs naming several trims never match.",
            "status": {"verified": "two independent sources (EPA counts when its rows isolate the trim); counted",
                       "single_source": "one source only; listed, not counted",
                       "sources_conflict": "sources disagree; not counted",
                       "covered_by_step2_rule": "a step-2 VIN rule already covers the trim and is the counted rule; listed for completeness, not double counted"},
            "validation": "Every identifier is applied to ground_truth.jsonl. uniformCell lines are unlabelled (BASELINE.md section 2). Note: VIN-bearing ground truth is vPIC's own TransmissionStyle, so agreement on Honda/Acura/Subaru checks the trim table against Honda's/Subaru's VIN transmission codes, not against an independent observation.",
            "counting": "Lot cars matched by a verified trim whose published transmission (extras trans) is empty, excluding yards in Canada (US-market claims). also_confirmed_by_step2 marks cars a step-2 rule already confirms.",
            "sources_read": READ_NOTE,
        },
        "summary": summary,
        "trims": out_trims,
        "not_manual_only": NOT_MANUAL_ONLY,
        "trim_name_cross_check": {"what": "ground-truth lines (VIN decodes, uniformCell excluded) whose vPIC trim is exactly this name, by vPIC make/model/year: the same name is manual-only on some models/years and not on others, so every rule is scoped by make, model and year",
                                  "by_name": name_check},
        "newly_confirmed_manual_cars": [n for n in newly_all if n["counted"]],
        "listed_not_counted_cars": [n for n in newly_all if not n["counted"]],
        "published_label_conflicts": conflicts_all,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
