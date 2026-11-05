#!/usr/bin/env python3
"""Regression checks for the second review of the curation pipeline
(branch at be7a774, 2026-11-05). Each block reproduces one finding on a
fixture: the check fails on the code before the fix and passes after it.
Every fix only removes claims; the positive controls show the evidence that
should still ship does.

F1  merge mappings: every merged catalog model must close, rows or not
F2  C4 suspect variant: every unmatched row's head phrase is re-run (test_curate case 10)
F3  a year manifest whose sub list did not parse never closes a car
F4  engine-sliced trims never narrow below the year-page trim universe without proof
F5  a cross-category supersession edge still blocks its in-category end
F8  EngineU includes the year page's engines
F9  own-page notes come from every row of the number on T's page, matched or not
F10 a list page closes T only when it hangs off one of T's own year pages
F11 chain records C5 relied on age the proof (build-time expiry)
"""
import copy
from datetime import datetime, timedelta, timezone

from _util import (JEEP, NOW, TOY, check, confirmed, done, js, list_manifest, model_map, run, sienna_fixture,
                   toyota_record, year_manifest)
import curate as C
import validate as V

PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
S04, S05 = ("Toyota", "Sienna", 2004), ("Toyota", "Sienna", 2005)
WR = "window-regulator"


def verified(doc, cat=None):
    return [g["apps"] for g in doc["groups"] if cat is None or g["cat"] == cat]


def ctx(st):
    return V.context_from(js(), model_map(), status_table=st, policy_sha=PSHA)


base_cur, base_doc = run("toyota", sienna_fixture(), status_table=ST)
check("control: the Sienna positive control ships Verified 2004-2005",
      verified(base_doc, WR) == [[["Toyota", "Sienna", 2004, 2005]]] and V.structural(base_doc, ctx(ST)) == [],
      str(verified(base_doc, WR)))

# ------------------------------------------------------------------ F1
JL_TRIMS = ["Rubicon", "Sahara", "Sport"]
JL_ENG = ["4 Cyl 2.0 L GAS", "6 Cyl 3.6 L GAS"]
MIR = [("68300000AA", "Driver Side"), ("68300001AA", "Passenger Side")]


def jeep_record(pn, seed, side, fit_rows):
    mk, md, y = seed
    stem = f"{y}-{mk.lower()}-{md.lower().replace(' ', '-')}"
    ev = ["Position", side, "Vehicle Fitment", "Year Make Model", "Trim", "Engine"]
    fit = []
    for lo, hi, fmk, fmd, trims, engines in fit_rows:
        yrs = f"{lo}-{hi}" if lo != hi else f"{lo}"
        fit.append({"years": [lo, hi], "make": fmk, "model": fmd, "trims": list(trims), "engines": list(engines),
                    "raw": f"{yrs} {fmk} {fmd} | {', '.join(trims)} | {', '.join(engines)}"})
        ev += [f"{yrs} {fmk} {fmd}", ", ".join(trims), ", ".join(engines)]
    return {"site": JEEP, "category": "side-mirrors", "seed": {"make": mk, "model": md, "year": y}, "segment": [y, y],
            "list_url": f"https://{JEEP}/parts-list/{stem}/body-hardware/outside-mirrors", "pn": pn,
            "name": "Mirror - Outside Rearview", "aux_desc": "Mirror",
            "product_url": f"https://{JEEP}/oem/mopar~mirror-outside-rearview~{pn.lower()}", "list_section": "diagram",
            "list_notes": [], "list_location": [side], "list_replaced_by": None, "reman": False,
            "description": "Mirror", "other_names": "Mirror - Outside Rearview", "position": side, "replaces": [],
            "replaced_by": [], "fitment": fit, "evidence_lines": ev, "fitment_rows_rendered": len(fit),
            "fitment_rows_total": len(fit), "retrieved": NOW, "synthetic": True}


def jeep_files(years):
    lo, hi = min(years), max(years)
    recs = [jeep_record(pn, ("Jeep", "Wrangler", lo), side, [(lo, hi, "Jeep", "Wrangler", JL_TRIMS, JL_ENG)])
            for pn, side in MIR]
    lists, ys = [], []
    for y in years:
        seed = ("Jeep", "Wrangler", y)
        ys.append(year_manifest(JEEP, seed, f"{y} Jeep Wrangler Parts", ["body-hardware/outside-mirrors"],
                                JL_TRIMS, JL_ENG))
        lm = list_manifest(JEEP, seed, "side-mirrors", "body-hardware/outside-mirrors",
                           [(pn, "Mirror - Outside Rearview", "Mirror", [], [side], True, None) for pn, side in MIR])
        for r in lm["rows"]:
            r["url"] = f"/oem/mopar~mirror-outside-rearview~{r['pn'].lower()}"
        lists.append(lm)
    return {f"raw/{JEEP}.jsonl": recs, f"raw/{JEEP}.lists.jsonl": lists, f"raw/{JEEP}.years.jsonl": ys}


STJ = confirmed((JEEP, "side-mirrors"), policy_sha=PSHA)
mm = model_map()
check("F1 the model map feeds Wrangler 2018 from 'Wrangler' and 'Wrangler JK' (merge), 2019 from 'Wrangler' only",
      sorted((t.cat_model, t.merge) for t in mm.sources("mopar", "Jeep", "Wrangler", 2018))
      == [("Wrangler", True), ("Wrangler JK", True)]
      and [t.cat_model for t in mm.sources("mopar", "Jeep", "Wrangler", 2019)] == ["Wrangler"])
check("F1 likewise Grand Cherokee 2022 only (the WK carryover)",
      len(mm.sources("mopar", "Jeep", "Grand Cherokee", 2022)) == 2
      and len(mm.sources("mopar", "Jeep", "Grand Cherokee", 2021)) == 1)
cur, doc = run("mopar", jeep_files((2018, 2019)), status_table=STJ)
I18 = cur.cells_info[(("Jeep", "Wrangler", 2018), "side-mirrors")]
check("F1 a merged cv with no rows ('Wrangler JK' 2018, no JK page read) keeps 2018 open",
      "year_manifest_bad" in I18["closure"] and not cur.t_sources[("Jeep", "Wrangler", 2018)] - {("Jeep", "Wrangler")},
      str(I18["closure"]))
check("F1 so no Verified group spans the JK carryover year", verified(doc) == [], str(verified(doc)))
cur, doc = run("mopar", jeep_files((2019, 2020)), status_table=STJ)
check("F1 control: JL-only years 2019-2020 close on the Wrangler pages and ship Verified",
      verified(doc) == [[["Jeep", "Wrangler", 2019, 2020]]] and V.structural(doc, ctx(STJ)) == [],
      str(verified(doc)) + str(cur.cells_info[(("Jeep", "Wrangler", 2019), "side-mirrors")]["closure"]))
f = jeep_files((2018, 2019))
f[f"raw/{JEEP}.years.jsonl"].append(year_manifest(JEEP, ("Jeep", "Wrangler", 2018), "2018 Jeep Wrangler JK Parts",
                                                  ["body-hardware/outside-mirrors"], JL_TRIMS, JL_ENG))
f[f"raw/{JEEP}.years.jsonl"][-1]["year_url"] = f[f"raw/{JEEP}.years.jsonl"][-1]["final_url"] = \
    f"https://{JEEP}/catalog/2018-jeep-wrangler-jk-parts"
cur, doc = run("mopar", f, status_table=STJ)
check("F1 the JK year page read but its mirror page not read: still open (unread_sibling_page)",
      "unread_sibling_page" in cur.cells_info[(("Jeep", "Wrangler", 2018), "side-mirrors")]["closure"]
      and verified(doc) == [], str(cur.cells_info[(("Jeep", "Wrangler", 2018), "side-mirrors")]["closure"]))
check("F1 a 'Wrangler JK' title is not the 'Wrangler' page (longest catalog model wins)",
      not cur._title_cv("2018 Jeep Wrangler JK Parts", "Jeep", "Wrangler", 2018)
      and cur._title_cv("2018 Jeep Wrangler JK Parts", "Jeep", "Wrangler JK", 2018)
      and cur._title_cv("2018 Jeep Wrangler Parts", "Jeep", "Wrangler", 2018))

# ------------------------------------------------------------------ F3
SLIDE = ("69803-08S01", "85710-08S02", "69804-08010", "85720-08020")


def front_only(empty_subs):
    files = sienna_fixture(years=(2005, 2006), drop_records=SLIDE)
    files[f"raw/{TOY}.lists.jsonl"] = [lm for lm in files[f"raw/{TOY}.lists.jsonl"]
                                       if not lm["list_url"].endswith("sliding-door-body")]
    if empty_subs is not None:
        for ym in files[f"raw/{TOY}.years.jsonl"]:
            ym["subs"] = list(empty_subs)
    return files


cur, doc = run("toyota", front_only(None), status_table=ST)
check("F3 control: the unread sliding-door page keeps 2005 open",
      "unread_sibling_page" in cur.cells_info[(S05, WR)]["closure"])
for label, subs in (("an empty sub list", []), ("a sub list with no category page", ["misc/labels"])):
    cur, doc = run("toyota", front_only(subs), status_table=ST)
    check(f"F3 {label} on the year page is year_manifest_bad, never 'every page read'",
          "year_manifest_bad" in cur.cells_info[(S05, WR)]["closure"] and verified(doc) == [],
          str(cur.cells_info[(S05, WR)]["closure"]))
f = front_only(None)
for ym in f[f"raw/{TOY}.years.jsonl"]:
    ym["error"] = "no parts-list links"
cur, doc = run("toyota", f, status_table=ST)
check("F3 a year manifest the crawler marked with an error is year_manifest_bad",
      "year_manifest_bad" in cur.cells_info[(S05, WR)]["closure"])

# ------------------------------------------------------------------ F10
f = sienna_fixture()
for lm in f[f"raw/{TOY}.lists.jsonl"]:
    if lm["seed"]["year"] == 2005:
        lm["list_url"] = lm["list_url"].replace("2005-toyota-sienna", "2004-toyota-sienna")
cur, doc = run("toyota", f, status_table=ST)
check("F10 2005's list manifests pointing at the 2004 pages never close 2005",
      "list_manifest_bad" in cur.cells_info[(S05, WR)]["closure"] and verified(doc) == [],
      str(cur.cells_info[(S05, WR)]["closure"]))

done("test_review2")
