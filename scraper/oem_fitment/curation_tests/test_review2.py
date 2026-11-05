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

# ------------------------------------------------------------------ F4
TC_ENG = ["4 Cyl 2.4 L GAS"]
STA = confirmed((TOY, "alternator"), policy_sha=PSHA)


def tc_files(alt_trims, extra=()):
    recs = [toyota_record("27060-28S01", "alternator", ("Scion", "tC", 2006), "charging-starting/alternator",
                          "Alternator", "Alternator Assembly", None, [(2005, 2010, "Scion", "tC", alt_trims, TC_ENG)])]
    for pn, cat, sub, name, aux in extra:
        recs.append(toyota_record(pn, cat, ("Scion", "tC", 2006), sub, name, aux, None,
                                  [(2005, 2010, "Scion", "tC", ["Base"], TC_ENG)]))
    lists, ys = [], []
    for y in (2006, 2007):
        seed = ("Scion", "tC", y)
        ys.append(year_manifest(TOY, seed, f"{y} Scion tC Parts", ["charging-starting/alternator"], ["Base", "Spec"],
                                TC_ENG))
        lists.append(list_manifest(TOY, seed, "alternator", "charging-starting/alternator",
                                   [("27060-28S01", "Alternator", "Alternator Assembly", [], [], True, None)]))
    return {f"raw/{TOY}.jsonl": recs, f"raw/{TOY}.lists.jsonl": lists, f"raw/{TOY}.years.jsonl": ys}


STARTERS = [(f"28100-28S0{i}", "starter", "charging-starting/starter", "Starter", "Starter Assembly") for i in range(1, 5)]
cur, doc = run("toyota", tc_files(["Base", "Spec"]), status_table=STA)
check("F4 control: an alternator listing every year-page trim attaches (vg toyota-2az, tC 2006-2007)",
      [(g["family"], g["spans"]) for g in doc["vg"]] == [("toyota-2az", [["Scion", "tC", 2006, 2007]])])
cur, doc = run("toyota", tc_files(["Base"], STARTERS), status_table=STA)
TC06 = ("Scion", "tC", 2006)
check("F4 Base-only engine rows never drop the year page's Spec trim: no vg for a Base-only alternator",
      doc["vg"] == [] and cur._trimu_f(TC06, frozenset({(4, 2.4, "gas")})) == cur.trimu[TC06],
      str([(g["family"], g["spans"]) for g in doc["vg"]]))
# the slice still narrows where the evidence ties a trim to another engine
# alone, with an attested slice (5 records, 3 categories)
CAM = ("Toyota", "Camry", 2005)
E24, E30 = "4 Cyl 2.4 L GAS", "6 Cyl 3.0 L GAS"
recs = []
for i, cat in enumerate(["alternator", "starter", "headlights", "alternator", "starter"]):
    nm = {"alternator": "Alternator", "starter": "Starter", "headlights": "Headlamp"}[cat]
    recs.append(toyota_record(f"9000{i}-24S0{i}", cat, CAM, "x/y", nm, f"{nm} Assembly",
                              "Driver Side" if cat == "headlights" else None,
                              [(2005, 2005, "Toyota", "Camry", ["LE", "XLE"], [E24])]))
recs.append(toyota_record("90009-30S09", "starter", CAM, "x/y", "Starter", "Starter Assembly", None,
                          [(2005, 2005, "Toyota", "Camry", ["SE"], [E30])]))
check("F4 fixture: every slicing record is verified", all(not r.problems for r in run("toyota", {
    f"raw/{TOY}.jsonl": recs})[0].records))
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": recs, f"raw/{TOY}.years.jsonl": [
    year_manifest(TOY, CAM, "2005 Toyota Camry Parts", ["charging-starting/alternator"], ["LE", "SE", "XLE"],
                  [E24, E30])]})
tf = cur._trimu_f(CAM, frozenset({(4, 2.4, "gas")}))
check("F4 an attested 2.4 slice drops only SE, seen on 3.0-only rows and never with a 2.4",
      tf == frozenset({("le", ""), ("xle", "")}) and cur.trimu[CAM] == frozenset({("le", ""), ("se", ""), ("xle", "")}),
      str(sorted(tf)))
recs = copy.deepcopy(recs)
recs[0]["fitment"][0]["trims"] = ["LE", "SE", "XLE"]
recs[0]["fitment"][0]["raw"] = recs[0]["fitment"][0]["raw"].replace("| LE, XLE |", "| LE, SE, XLE |")
recs[0]["evidence_lines"] = ["LE, SE, XLE" if x == "LE, XLE" else x for x in recs[0]["evidence_lines"]]
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": recs, f"raw/{TOY}.years.jsonl": [
    year_manifest(TOY, CAM, "2005 Toyota Camry Parts", ["charging-starting/alternator"], ["LE", "SE", "XLE"],
                  [E24, E30])]})
check("F4 a trim seen once beside a 2.4 is never dropped from the 2.4 slice",
      cur._trimu_f(CAM, frozenset({(4, 2.4, "gas")})) == cur.trimu[CAM] and all(not r.problems for r in cur.records),
      str(sorted(cur._trimu_f(CAM, frozenset({(4, 2.4, "gas")})))))
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": recs[2:], f"raw/{TOY}.years.jsonl": [
    year_manifest(TOY, CAM, "2005 Toyota Camry Parts", ["charging-starting/alternator"], ["LE", "SE", "XLE"],
                  [E24, E30])]})
check("F4 below the attestation threshold (3 records in the 2.4 slice) nothing is sliced",
      cur._trimu_f(CAM, frozenset({(4, 2.4, "gas")})) == cur.trimu[CAM])

# ------------------------------------------------------------------ F8
OLDE = "6 Cyl 3.3 L GAS, 6 Cyl 3.5 L GAS"
f = sienna_fixture()
for rec in f[f"raw/{TOY}.jsonl"]:
    for fr in rec["fitment"]:
        fr["engines"] = ["6 Cyl 3.3 L GAS"]
        fr["raw"] = fr["raw"].replace(OLDE, "6 Cyl 3.3 L GAS")
    rec["evidence_lines"] = ["6 Cyl 3.3 L GAS" if x == OLDE else x for x in rec["evidence_lines"]]
cur, doc = run("toyota", f, status_table=ST)
check("F8 the year page's 3.5 L is in EngineU although no row prints it",
      cur.engineu[S04] == frozenset({(6, 3.3, "gas"), (6, 3.5, "gas")}) and cur.engineu_src[S04] == "year_page",
      str(cur.engineu.get(S04)))
check("F8 so parts printed for the 3.3 L only are never 'every trim and engine' (no Verified)",
      verified(doc, WR) == [] and all(m["cover"] == "maybe" for m in cur.cells_info[(S04, WR)]["members"].values()))
f = sienna_fixture()
for ym in f[f"raw/{TOY}.years.jsonl"]:
    ym["engines"] = []
cur, doc = run("toyota", f, status_table=ST)
check("F8 without year-page engines a row-derived EngineU needs the TrimU attestation (8 records, 1 category: no)",
      cur.engineu_src[S04] == "unattested" and verified(doc, WR) == []
      and all("engines_unattested" in m["why"] for m in cur.cells_info[(S04, WR)]["members"].values()))

# ------------------------------------------------------------------ F9
f = sienna_fixture()
for lm in f[f"raw/{TOY}.lists.jsonl"]:
    if lm["seed"]["year"] == 2005 and lm["list_url"].endswith("front-door-body"):
        lm["rows"].append({"pn": "69802-08S01", "section": "other", "main": "Regulator Sub-Assy, Front Door Window, LH",
                           "aux": "", "extra": [{"name": "Part Notes", "desc": "Japan Built"}], "replace": None,
                           "url": "/oem/toyota~part~69802-08s01", "matched": False, "excluded_by": "include_miss",
                           "product": None})
cur, doc = run("toyota", f, status_table=ST)
m = cur.cells_info[(S05, WR)]["members"]["toyota:6980208S01"]
check("F9 a second, unmatched row of the same number on T's page carries its note ('Japan Built'): cover maybe",
      m["cover"] == "maybe" and "conditional_notes:plant" in m["why"] and "Japan Built" in m["page"][1],
      str(m["why"]))
check("F9 'on page' stays tied to the matched row", m["page"][0] is True)
check("F9 and nothing ships Verified", verified(doc, WR) == [])

# ------------------------------------------------------------------ F5
SUCC = "69802-08S50"


def xcat_files(succ_cat):
    f = sienna_fixture()
    for rec in f[f"raw/{TOY}.jsonl"]:
        if rec["pn"] == "69802-08S01":
            rec["replaced_by"] = [SUCC]
            rec["evidence_lines"] = ["Replaced By", SUCC] + rec["evidence_lines"]
    if succ_cat:
        f[f"raw/{TOY}.jsonl"].append(toyota_record(
            SUCC, succ_cat, S04, "body-hardware/outside-mirrors", "Mirror Assembly", "Mirror Assy, Outer Rear View, LH",
            "Driver Side", [(2004, 2010, "Toyota", "Sienna", ["CE", "LE", "Limited", "XLE", "XLE Limited"],
                             ["6 Cyl 3.3 L GAS", "6 Cyl 3.5 L GAS"])], location=["Driver Side"]))
    return f


cur, doc = run("toyota", xcat_files(None), status_table=ST)
check("F5 control: an uncrawled successor keeps the cell open (uncrawled_chain_member)",
      "uncrawled_chain_member" in cur.cells_info[(S04, WR)]["closure"] and verified(doc, WR) == [])
cur, doc = run("toyota", xcat_files("side-mirrors"), status_table=ST)
check("F5 the successor recorded only as a mirror: reported, and the regulator cell stays open",
      any(r["reason"] == "cross_category_supersession" for r in cur.refusals)
      and "uncrawled_chain_member" in cur.cells_info[(S04, WR)]["closure"] and verified(doc, WR) == [],
      str(cur.cells_info[(S04, WR)]["closure"]))
check("F5 the edge stays in both categories' graphs (the two classes are never joined)",
      ("toyota:6980208S01", "toyota:6980208S50") in cur.edges[WR]
      and ("toyota:6980208S01", "toyota:6980208S50") in cur.edges["side-mirrors"]
      and ("toyota:6980208S50", WR) not in cur.classes)
# removing the successor's record with the edge printed on the predecessor
# (as SimplePart prints 'Replaced By') keeps the cell blocked
f = sienna_fixture()
for rec in f[f"raw/{TOY}.jsonl"]:
    if rec["pn"] == "69802-08S01":
        rec["replaced_by"] = [SUCC]
        rec["evidence_lines"] = ["Replaced By", SUCC] + rec["evidence_lines"]
f[f"raw/{TOY}.jsonl"].append(toyota_record(SUCC, WR, S04, "body-hardware/front-door-body", "Window Regulator",
                                           "Regulator Sub-Assembly", "Driver Side",
                                           [(2006, 2010, "Toyota", "Sienna", ["CE", "LE"], ["6 Cyl 3.5 L GAS"])],
                                           location=["Driver Side"], replaces=["69802-08S01"]))
cur, doc = run("toyota", f, status_table=ST)
check("F5 control: a successor that does not list 2004 is chain_fitment_inconsistent",
      "chain_fitment_inconsistent" in cur.cells_info[(S04, WR)]["closure"])
f[f"raw/{TOY}.jsonl"] = [r for r in f[f"raw/{TOY}.jsonl"] if r["pn"] != SUCC]
cur, doc = run("toyota", f, status_table=ST)
check("F5 removing that successor's record leaves the predecessor's printed edge: still blocked",
      "uncrawled_chain_member" in cur.cells_info[(S04, WR)]["closure"] and verified(doc, WR) == [])

# ------------------------------------------------------------------ F11
ANC = "69802-08S00"
now = datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
old = (now - timedelta(days=110)).strftime("%Y-%m-%dT%H:%M:%SZ")
f = sienna_fixture()
for rec in f[f"raw/{TOY}.jsonl"]:
    if rec["pn"] == "69802-08S01":
        rec["replaces"] = [ANC]
        rec["evidence_lines"] = ["Replaces", ANC] + rec["evidence_lines"]
f[f"raw/{TOY}.jsonl"].append(toyota_record(ANC, WR, ("Toyota", "Sienna", 2003), "body-hardware/front-door-body",
                                           "Window Regulator", "Regulator Sub-Assembly", "Driver Side",
                                           [(1998, 2003, "Toyota", "Sienna", ["CE", "LE", "XLE"], ["6 Cyl 3.0 L GAS"])],
                                           location=["Driver Side"], replaced_by=["69802-08S01"], retrieved=old))
cur, doc = run("toyota", f, status_table=ST)
g = [x for x in doc["groups"] if x["cat"] == WR]
check("F11 control: a 110-day-old ancestor (not a member) still lets 2004-2005 ship",
      [x["apps"] for x in g] == [[["Toyota", "Sienna", 2004, 2005]]])
check("F11 the proof's oldest_retrieved is the ancestor's stamp",
      g and {y["closure"]["oldest_retrieved"] for y in g[0]["years"]} == {old})
kept, dropped = V.expire(doc, now + timedelta(days=30))
check("F11 build-time expiry 30 days later (ancestor evidence 140 days old) drops the group",
      kept["groups"] == [] and dropped == [g[0]["id"]] if g else False, str(dropped))
late = (now + timedelta(days=11)).strftime("%Y-%m-%dT%H:%M:%SZ")
cur, doc = run("toyota", f, status_table=ST, as_of=late)
check("F11 curate time: --as-of 11 days later (ancestor 121 days old, so unverified) keeps the cell open",
      {"stale", "uncrawled_chain_member"} & set(cur.cells_info[(S04, WR)]["closure"]) and verified(doc, WR) == [],
      str(cur.cells_info[(S04, WR)]["closure"]))

done("test_review2")
