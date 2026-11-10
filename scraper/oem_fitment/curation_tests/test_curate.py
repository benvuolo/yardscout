#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_curate: one block per case of the table (1-23).
Each case asserts the groups and the exact open reason. R = real lines from
oem-raw (fixtures/real, provenance.json); manifests (R1/R2) are synthetic
fixtures that follow the spec exactly, because the crawler has written none."""
from collections import Counter
import copy
from pathlib import Path
import tempfile
import json
import random
from datetime import datetime, timedelta, timezone

from _util import (JEEP, NOW, TOY, by_pn, check, confirmed, done, js, list_manifest, model_map, real, run,
                   toyota_record, write_raw, year_manifest)
import adapters as A
import curate as C
import validate as V

toy = real("toyota_f2652c3.jsonl")
jeep = real("jeep_94f03a3.jsonl")
nis = real("nissan_94f03a3.jsonl")
PSHA = C.policy_sha256()
SIENNA_TRIMS = ["CE", "LE", "Limited", "XLE", "XLE Limited"]
SIENNA_ENG = ["6 Cyl 3.3 L GAS", "6 Cyl 3.5 L GAS"]


def toy_raw(*recs, lists=(), years=()):
    f = {f"raw/{TOY}.jsonl": list(recs)}
    if lists:
        f[f"raw/{TOY}.lists.jsonl"] = list(lists)
    if years:
        f[f"raw/{TOY}.years.jsonl"] = list(years)
    return f


def info(cur, T, cat):
    return cur.cells_info.get((T, cat)) or {}


def key(ns, pn):
    import policy
    return policy.pn_key(ns, pn)


# ---------------------------------------------------------------- case 1
recs = [by_pn(toy, p) for p in ("87910-06925", "87910-06926", "87910-33670-B2", "87940-33630-B1")]
cur, doc = run("toyota", toy_raw(*recs))
I = info(cur, ("Toyota", "Camry", 2009), "side-mirrors")
check("1 Camry 2009 mirrors: open first on closure (no manifests: no_year_manifest)",
      I.get("closure", [None])[0] == "no_year_manifest", str(I.get("closure")))
check("1 Camry 2009 mirrors: the eligibility verdict is option_split (US/Japan x heated x colour)",
      I.get("elig", [None])[0] == "option_split", str(I.get("elig")))
check("1 no Verified group", doc["groups"] == [] and doc["vg"] == [])
lk = {p: g for g in doc["likely"] for p in g["pn"]}
check("1 Likely groups only, with plant/option reasons",
      all(p in lk and lk[p]["reason"] in ("plant", "option") for p in ("87910-06925", "87910-06926", "87910-33670-B2")),
      str({p: lk.get(p, {}).get("reason") for p in ("87910-06925", "87910-06926", "87910-33670-B2")}))

# ---------------------------------------------------------------- case 2
recs = [by_pn(toy, p) for p in ("69804-AA010", "69840-AA040", "85720-AA030")]
st = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
cur, doc = run("toyota", toy_raw(*recs), trimu_force={("Toyota", "Camry", 1999): ["CE", "LE", "XLE"]},
               status_table=st)
I = info(cur, ("Toyota", "Camry", 1999), "window-regulator")
m = I.get("members", {})
check("2 Camry 1999 rear door: packaging_unstated (69840-AA040 'Regulator Assembly' has no stated packaging)",
      "packaging_unstated" in I.get("elig", []), str(I.get("elig")))
check("2 'Power' / 'Manual' notes condition the rows (conditional_notes:option)",
      "conditional_notes:option" in m[key("toyota", "69804-AA010")]["why"]
      and "conditional_notes:option" in m[key("toyota", "69840-AA040")]["why"])
check("2 never Verified (regression for conflict #2), even with the category confirmed",
      doc["groups"] == [] and all(not c[4].startswith("sig:") for c in doc["cells"]))

# ---------------------------------------------------------------- case 3
r3 = by_pn(toy, "81560-06240")
T07 = ("Toyota", "Camry", 2007)
cur, doc = run("toyota", toy_raw(r3), trimu_force={T07: ["Base", "CE", "Hybrid", "LE", "SE", "XLE"]})
m = info(cur, T07, "tail-lights")["members"][key("toyota", "81560-06240")]
check("3 tail lamp 81560-06240 'US Built, 2007-09' is maybe (plant, conditional_trims)",
      m["cover"] == "maybe" and "conditional_notes:plant" in m["why"] and "conditional_trims" in m["why"], str(m["why"]))
cond = cur.phase2_cond(T07, "tail-lights", key("toyota", "81560-06240"))
check("3 Phase 2 cond is fuel=gas AND plant=US", cond == [{"plant": "US", "fuel": "gas"}], str(cond))
check("3 a J-VIN donor is never Verified", not C.cond_satisfied(cond, {"plant": "JP", "fuel": "gas"}))
check("3 an unanswered atom never satisfies (Likely)", not C.cond_satisfied(cond, {"plant": "US"}))
check("3 US + gas satisfies the Phase 2 condition", C.cond_satisfied(cond, {"plant": "US", "fuel": "gas"}))

# ---------------------------------------------------------------- case 4
r4 = by_pn(toy, "85720-33161")
cur, doc = run("toyota", toy_raw(r4), trimu_force={T07: ["Base", "Hybrid", "LE", "SE", "XLE"]})
m = info(cur, T07, "window-regulator")["members"][key("toyota", "85720-33161")]
check("4 85720-33161: the table lists every trim but the own-page note 'Japan Built, With XLE' makes it maybe",
      m["cover"] == "maybe" and "conditional_trims" not in m["why"]
      and "conditional_notes:trim" in m["why"] and "conditional_notes:plant" in m["why"], str(m["why"]))

# ---------------------------------------------------------------- case 5
s84, s00 = by_pn(toy, "28100-20020-84"), by_pn(toy, "28100-20020")
s84_clean = copy.deepcopy(s84)
s84_clean["list_notes"] = []
force = {T07: ["Base", "CE", "LE", "SE", "XLE"]}
cur, doc = run("toyota", toy_raw(s84_clean, s00), trimu_force=force)
k84, k00 = key("toyota", "28100-20020-84"), key("toyota", "28100-20020")
I = info(cur, T07, "starter")
check("5a 28100-20020-84 (raw reman:false) is classed reman by its -84 suffix",
      cur.classes[(k84, "starter")].reman and not s84["reman"])
check("5a the option-layout ancestor 28100-20020 has cover maybe",
      I["members"][k00]["cover"] == "maybe" and "option_layout" in I["members"][k00]["why"], str(I["members"][k00]["why"]))
check("5a E2 blocks: chain_member_conditional", "chain_member_conditional" in I["elig"], str(I["elig"]))
cur, doc = run("toyota", toy_raw(s84_clean), trimu_force=force)
check("5b ancestor record removed: uncrawled_chain_member",
      "uncrawled_chain_member" in info(cur, T07, "starter")["closure"], str(info(cur, T07, "starter")["closure"]))
s84_alone = copy.deepcopy(s84_clean)
s84_alone["replaces"] = []
cur, doc = run("toyota", toy_raw(s84_alone), trimu_force=force)
check("5c ancestor removed from the graph entirely: reman_only (E4)",
      "reman_only" in info(cur, T07, "starter")["elig"], str(info(cur, T07, "starter")["elig"]))

# ---------------------------------------------------------------- case 6
a6 = by_pn(toy, "27060-28320")
cur, doc = run("toyota", toy_raw(a6))
m = info(cur, T07, "alternator")["members"][key("toyota", "27060-28320")]
check("6 option-layout alternator 27060-28320 is never coverage", m["cover"] == "maybe" and "option_layout" in m["why"])
check("6 its model-wide engine column never narrows engines (EngineU empty)", cur.engineu.get(T07) == frozenset())
check("6 no vg and no Likely group (Likely is body-only)", doc["vg"] == [] and doc["likely"] == [])

# ---------------------------------------------------------------- case 7
m7 = by_pn(toy, "87910-33670-B2")
pre = [toyota_record(pn, "side-mirrors", ("Toyota", "Camry", 2007), "body-hardware/outside-mirrors", "Mirror Assembly",
                     "Mirror Assembly Outer Rearview", "Passenger Side",
                     [(2007, 2011, "Toyota", "Camry", ["Base", "CE", "Hybrid", "LE", "SE", "XLE"], ["4 Cyl 2.4 L GAS"])],
                     location=["Passenger Side"], replaced_by=["87910-33670-B2"])
       for pn in ("87910-33660-B2", "87910-33660-B0")]
cur, doc = run("toyota", toy_raw(m7, *pre))
check("7 87910-33670-B2 consolidates -33660-B2 and -B0 (both list Camry 2007): option_split",
      info(cur, T07, "side-mirrors")["elig"][0] == "option_split", str(info(cur, T07, "side-mirrors")["elig"]))

# ---------------------------------------------------------------- case 8
SL_REG, SL_MOT = by_pn(toy, "69804-08010"), by_pn(toy, "85720-08020")
FIT = [(2004, 2010, "Toyota", "Sienna", SIENNA_TRIMS, SIENNA_ENG)]
SEED = ("Toyota", "Sienna", 2004)
syn = {
    "FL": [("69802-08S01", "front-door-body", "Driver Side", "reg"), ("85720-08S01", "front-door-body", "Driver Side", "motor")],
    "FR": [("69801-08S01", "front-door-body", "Passenger Side", "reg"), ("85710-08S01", "front-door-body", "Passenger Side", "motor")],
    "SR": [("69803-08S01", "sliding-door-body", "Passenger Side", "reg"), ("85710-08S02", "sliding-door-body", "Passenger Side", "motor")],
}
NAMES = {"reg": ("Window Regulator", "Regulator Sub-Assembly"), "motor": ("Motor", "Motor Assembly, Power Window")}
sienna_recs = [SL_REG, SL_MOT]
rows_by_sub = {"front-door-body": [], "sliding-door-body": []}
for slot, items in syn.items():
    for pn, sub, side, pack in items:
        sienna_recs.append(toyota_record(pn, "window-regulator", SEED, f"body-hardware/{sub}", NAMES[pack][0],
                                         NAMES[pack][1], side, FIT, location=[side]))
        rows_by_sub[sub].append((pn, NAMES[pack][0], NAMES[pack][1], [], [side], True, None))
rows_by_sub["sliding-door-body"] += [("69804-08010", "Window Regulator", "Regulator Sub-Assembly", [], ["Driver Side"], True, None),
                                     ("85720-08020", "Motor", "Motor Assembly, Power Window", [], ["Driver Side"], True, None)]
SUBS = ["body-hardware/front-door-body", "body-hardware/sliding-door-body", "body-hardware/outside-mirrors"]


def sienna_files(years=(2004, 2005), drop_list=None):
    lists, ys = [], []
    for y in years:
        seed = ("Toyota", "Sienna", y)
        ys.append(year_manifest(TOY, seed, f"{y} Toyota Sienna Parts", SUBS, SIENNA_TRIMS, SIENNA_ENG))
        for sub, rows in rows_by_sub.items():
            if drop_list == (y, sub):
                continue
            lists.append(list_manifest(TOY, seed, "window-regulator", f"body-hardware/{sub}", rows))
    return toy_raw(*sienna_recs, lists=lists, years=ys)


st8 = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
cur, doc = run("toyota", sienna_files(), status_table=st8)
I4, I5 = info(cur, ("Toyota", "Sienna", 2004), "window-regulator"), info(cur, ("Toyota", "Sienna", 2005), "window-regulator")
check("8 positive control: Sienna 2004 and 2005 close", I4["closure"] == [] and I5["closure"] == [],
      f"{I4.get('closure')} {I5.get('closure')}")
check("8 both are eligible (every door P2, every member cover yes)", I4["elig"] == [] and I5["elig"] == [],
      f"{I4.get('elig')} {I5.get('elig')}")
wr = [g for g in doc["groups"] if g["cat"] == "window-regulator"]
check("8 exactly one Verified group, Sienna 2004-2005", len(wr) == 1 and wr[0]["apps"] == [["Toyota", "Sienna", 2004, 2005]],
      json.dumps([g["apps"] for g in wr]))
ctx8 = V.context_from(js(), model_map(), status_table=st8, policy_sha=PSHA)
check("8 the generated file passes the validator", V.structural(doc, ctx8) == [], str(V.structural(doc, ctx8)[:3]))
check("8 sig names every door with reg + motor",
      wr and [s[0] for s in wr[0]["sig"]] == ["FL", "FR", "SL", "SR"]
      and all([p for p, _ in s[1]] == ["motor", "reg"] for s in wr[0]["sig"]))
check("8 the same file fails V7 without the audit record", any(p.startswith("V7") for p in V.structural(
    doc, V.context_from(js(), model_map(), status_table={}, policy_sha=PSHA))))
cur, doc = run("toyota", sienna_files(drop_list=(2005, "front-door-body")), status_table=st8)
check("8 removing any manifest makes it open (unread_sibling_page), and no group remains",
      "unread_sibling_page" in info(cur, ("Toyota", "Sienna", 2005), "window-regulator")["closure"]
      and doc["groups"] == [], str(info(cur, ("Toyota", "Sienna", 2005), "window-regulator")["closure"]))
cur, doc = run("toyota", sienna_files(years=(2004,)), status_table=st8)
check("8 a single closed vehicle-year is no group (needs 2)", doc["groups"] == [])

# ---------------------------------------------------------------- case 9
r9 = by_pn(toy, "85710-AE010")
cur, doc = run("toyota", toy_raw(r9))
m = info(cur, ("Toyota", "Sienna", 2004), "window-regulator")["members"][key("toyota", "85710-AE010")]
check("9 notes only from another seed's page: maybe (notes_not_own_page)",
      m["cover"] == "maybe" and "notes_not_own_page" in m["why"], str(m["why"]))

# --------------------------------------------------------------- case 10
r10 = by_pn(toy, "87910-06925")
T09 = ("Toyota", "Camry", 2009)
lm = list_manifest(TOY, T09, "side-mirrors", "body-hardware/outside-mirrors",
                   [("87910-06925", "Mirror Assembly", "Mirror Assembly Outer Rearview", ["US Built"], ["Passenger Side"], True, None),
                    ("87910-06555", "Mirror Assembly", "Mirror Assy, Outer Rear View, W/Turn Signal Lamp", [], ["Passenger Side"],
                     False, "rule:lamp")])
ym = year_manifest(TOY, T09, "2009 Toyota Camry Parts", ["body-hardware/outside-mirrors"], ["Base", "CE", "LE", "SE", "XLE"])
cur, doc = run("toyota", toy_raw(r10, lists=[lm], years=[ym]))
check("10 an excluded row whose head phrase passes the include rule is a suspect_variant (C4)",
      "suspect_variant" in info(cur, T09, "side-mirrors")["closure"], str(info(cur, T09, "side-mirrors")["closure"]))
lm2 = copy.deepcopy(lm)
lm2["rows"][1]["aux"] = "Cover, Outer Mirror"
lm2["rows"][1]["excluded_by"] = "rule:cover"
cur, doc = run("toyota", toy_raw(r10, lists=[lm2], years=[ym]))
check("10 an excluded mirror cover is not a suspect", "suspect_variant" not in info(cur, T09, "side-mirrors")["closure"])
# review F2: whatever the crawler wrote as the reason (url_pn_mismatch, None,
# '' or a reason this code does not know), an unmatched row whose head
# phrase passes the site's rule is a suspect; only a re-run that fails clears it
for excl in ("url_pn_mismatch", None, "", "section_not_read", "brand_new_reason"):
    lm3 = copy.deepcopy(lm)
    lm3["rows"][1]["aux"] = "Mirror Assy, Outer Rear View"
    lm3["rows"][1]["excluded_by"] = excl
    cur, doc = run("toyota", toy_raw(r10, lists=[lm3], years=[ym]))
    check(f"10 an unmatched mirror row with excluded_by={excl!r} is a suspect_variant",
          "suspect_variant" in info(cur, T09, "side-mirrors")["closure"], str(info(cur, T09, "side-mirrors")["closure"]))
lm4 = copy.deepcopy(lm2)
lm4["rows"][1]["excluded_by"] = "include_miss"
cur, doc = run("toyota", toy_raw(r10, lists=[lm4], years=[ym]))
check("10 an include_miss row whose re-run fails (a mirror cover) is not a suspect",
      "suspect_variant" not in info(cur, T09, "side-mirrors")["closure"])

# --------------------------------------------------------------- case 11
alts = [by_pn(jeep, p) for p in ("4801477AA", "4801477AG", "4801323AD", "4801323AK")]
P14 = ("Jeep", "Patriot", 2014)
PT = ["75th Anniversary", "Latitude", "Latitude X", "Limited", "Sport"]
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": alts}, trimu_force={P14: PT})
I = info(cur, P14, "alternator")
kAA, kAG = key("mopar", "4801477AA"), key("mopar", "4801477AG")
check("11 Patriot 2014 alternators are two chains: option_split", I["elig"][0] == "option_split", str(I["elig"]))
check("11 4801477AA (option layout) has cover maybe", I["members"][kAA]["cover"] == "maybe")
seeker14 = {"slots": {"C": {k: m["cover"] for k, m in I["members"].items()}}, "eligible": False}
donor16 = {"slots": {"C": {kAG: "yes"}}, "eligible": True}
check("11 Phase 2 directional: a 2016 donor {AG} verifies for the 2014 seeker iff cover(AG, 2014) = yes",
      C.directional_verified(seeker14, donor16) == (I["members"][kAG]["cover"] == "yes")
      and I["members"][kAG]["cover"] == "yes", str(I["members"][kAG]["why"]))
seeker16 = {"slots": {"C": {kAG: "yes"}}, "eligible": True}
donor14 = {"slots": {"C": {k: m["cover"] for k, m in I["members"].items()}}, "eligible": False}
check("11 a 2014 donor never verifies for a 2016 seeker", not C.directional_verified(seeker16, donor14))
cur2, _ = run("mopar", {f"raw/{JEEP}.jsonl": alts})
I2 = info(cur2, P14, "alternator")
s2 = {"slots": {"C": {k: m["cover"] for k, m in I2["members"].items()}}, "eligible": False}
check("11 without an attested trim universe AG is maybe, and the directional test fails",
      I2["members"][kAG]["cover"] == "maybe" and not C.directional_verified(s2, donor16))
check("11 Phase 1 ships nothing", doc["groups"] == [] and doc["vg"] == [])

# --------------------------------------------------------------- case 12
ag = by_pn(jeep, "4801477AG")
hl = toyota_record("5303999ZZ", "headlights", P14, "headlights-lighting/headlamps", "Headlamp", None, "Front Driver Side",
                   [(2014, 2014, "Jeep", "Patriot", ["Latitude"], ["4 Cyl 2.4 L GAS"]),
                    (2009, 2009, "Dodge", "Caliber", ["SE"], ["4 Cyl 2.0 L GAS"])], location=["Driver Side"])
hl.update(site=JEEP, product_url=f"https://{JEEP}/oem/mopar~headlamp~5303999ZZ",
          list_url=f"https://{JEEP}/parts-list/2014-jeep-patriot/headlights-lighting/headlamps")
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": [ag, hl]})
check("12 synthetic Mopar headlamp passes the jeeppartsdeal rule (so it is a candidate, not drift)",
      A.rule_matches(A.to_record(JEEP, "mopar", 1, hl)) is True)
CAL = ("Dodge", "Caliber", 2009)
check("12 sister make Dodge Caliber (seen only in Jeep fitment) is not closed",
      "no_year_manifest" in info(cur, CAL, "alternator")["closure"])
inv = [g for g in doc["groups"] + doc["vg"] for y in g["years"] if y["t"][0] == "Dodge"]
check("12 Caliber is absent from Verified", inv == [])
# §5.16 own-page rule (2026-11-06): Caliber is known only from the Jeep part's
# product-page fitment table (a possible platform rollup), so it makes no
# Likely claim; once a record seeded on Caliber's own page lists the number,
# Caliber joins.
check("12 own-page rule: Caliber (product page only) is not in Likely",
      not any(a[:2] == ["Dodge", "Caliber"] for g in doc["likely"] for a in g["apps"]))
check("12 own-page rule: the left-out vehicle-years are counted",
      sum(cur.likely_own_page_drops.values()) > 0, str(dict(cur.likely_own_page_drops)))
# R3 own-page completion input: Caliber's own headlights page goes on the
# worklist, routed to the site seeded on its make's pages (none here: the
# only seeds are Jeep), so it is counted as unrouted, never guessed
_opc = cur.own_page_completion(Counter({CAL: 3}))
check("12 R3 input: Caliber headlights waits, unrouted (no seed on a Dodge page)",
      _opc["rows"] == [] and _opc["unrouted_makes"] == {"Dodge": 1} and not [(r["make"], r["model"], r["year"], r["cats"]) for r in _opc["rows"]] == [("Dodge", "Caliber", 2009, ["headlights"])],
      str(_opc)[:300])
cur.records[0].seed = ("Dodge",) + tuple(cur.records[0].seed[1:])
_opc3 = cur.own_page_completion(Counter({CAL: 3}))
check("12 R3 input: routed by the seed site of the make, ranked by cars x classes",
      [(r["site"], r["make"], r["model"], r["year"], r["cats"], r["gain"]) for r in _opc3["rows"]]
      == [(JEEP, "Dodge", "Caliber", 2009, ["headlights"], 3)], str(_opc3)[:300])
# the crawler records a number once per site; a later page that lists it
# shows up in the R1 list manifest
lm_cal = list_manifest(JEEP, CAL, "headlights", "headlights-lighting/headlamps",
                       [("5303999ZZ", "Headlamp", None, [], ["Driver Side"], True, None)])
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": [ag, hl], f"raw/{JEEP}.lists.jsonl": [lm_cal]})
# with Caliber's own page the class spans Patriot + Caliber; a headlamp across
# two base models is held by the exterior rule (owner decision 2026-11-06),
# never shipped, and kept for the owner checklist with its record URLs
h12 = [h for h in cur.held_exterior if "5303999ZZ" in h["pn"]]
check("12 exterior hold: Patriot + Caliber headlamp is held, not shipped",
      h12 and not any("5303999ZZ" in g["pn"] for g in doc["likely"])
      and any(a[:2] == ["Dodge", "Caliber"] for a in h12[0]["apps"]), str(h12)[:300])
check("12 exterior hold: refusal held_exterior_cross_model, entry carries note and record URLs",
      any(r["reason"] == "held_exterior_cross_model" and r["pn"] == "5303999ZZ" for r in cur.refusals)
      and h12[0]["urls"] and h12[0]["note"].startswith("Mopar catalog lists #5303999ZZ"), str(h12)[:300])
# §5.16 release allowlist (2026-11-09): an exact (ns, cat, pn, apps) entry
# releases a held group; a differing entry, or a withheld namespace, does not
import policy as _P  # noqa: E402
_apps12 = h12[0]["apps"]
_rel = Path(tempfile.mkdtemp()) / "allow.json"


def _with_allow(entries):
    _rel.write_text(json.dumps({"groups": entries}))
    old = _P.RELEASE_ALLOWLIST_PATH
    _P.RELEASE_ALLOWLIST_PATH = _rel
    try:
        return run("mopar", {f"raw/{JEEP}.jsonl": [ag, hl], f"raw/{JEEP}.lists.jsonl": [lm_cal]})
    finally:
        _P.RELEASE_ALLOWLIST_PATH = old


c_ok, d_ok = _with_allow([{"ns": "mopar", "cat": "headlights", "pn": ["5303999ZZ"], "apps": _apps12}])
check("12 allowlist: an exact entry releases the held headlamp into Likely",
      any("5303999ZZ" in g["pn"] for g in d_ok["likely"]) and not any("5303999ZZ" in h["pn"] for h in c_ok.held_exterior))
_bad = [list(a) for a in _apps12]
_bad[0][3] += 1
c_no, d_no = _with_allow([{"ns": "mopar", "cat": "headlights", "pn": ["5303999ZZ"], "apps": _bad}])
check("12 allowlist: an entry whose apps differ by one year leaves it held",
      not any("5303999ZZ" in g["pn"] for g in d_no["likely"]) and any("5303999ZZ" in h["pn"] for h in c_no.held_exterior))
# subaru re-shipped 2026-11-09: the withheld mechanism is tested with it set again
_wh = _P.WITHHELD_NS
_P.WITHHELD_NS = frozenset({"subaru"})
try:
    c_ns, d_ns = _with_allow([{"ns": "subaru", "cat": "headlights", "pn": ["5303999ZZ"], "apps": _apps12}])
    check("12 allowlist: a withheld namespace's entry never releases (and the wrong ns does not match)",
          not any("5303999ZZ" in g["pn"] for g in d_ns["likely"]) and _P.release_allowlist(_rel) == set())
finally:
    _P.WITHHELD_NS = _wh
check("12 allowlist notes: an entry's note is keyed like the release (hoods name the turbo split)",
      any("Turbo hood" in v for v in _P.release_notes().values())
      and set(_P.release_notes()) <= _P.release_allowlist())
check("12 allowlist: the committed allowlist is part of the policy hash",
      "release_allowlist.json" in _P.POLICY_INPUTS)
check("12 base model: Camry / Camry Hybrid and RX 350 / RX 450h stay together; Grand Caravan = Caravan",
      _P.base_model("Toyota", "Camry") == _P.base_model("Toyota", "Camry Hybrid")
      and _P.base_model("Lexus", "RX 350") == _P.base_model("Lexus", "RX 450h")
      and _P.base_model("Dodge", "Grand Caravan") == _P.base_model("Dodge", "Caravan"))
check("12 base model: Legacy/Outback, DeVille/Seville, Caravan/Durango, Fusion/Milan differ",
      _P.base_model("Subaru", "Legacy") != _P.base_model("Subaru", "Outback")
      and _P.base_model("Cadillac", "DeVille") != _P.base_model("Cadillac", "Seville")
      and _P.base_model("Dodge", "Caravan") != _P.base_model("Dodge", "Durango")
      and _P.base_model("Ford", "Fusion") != _P.base_model("Mercury", "Milan"))
check("12 hold covers exterior styling only (mirrors and window parts are not held)",
      "side-mirrors" not in _P.EXTERIOR_HOLD_CATS and "window-regulator" not in _P.EXTERIOR_HOLD_CATS
      and {"grille", "headlights", "tail-lights", "bumper-front"} <= _P.EXTERIOR_HOLD_CATS)
# hub 2026-11-09 (Subaru resample: 91036FJ100 non-heated mirror credited to the US XV):
# subaru cross-model side-mirror groups are held; other namespaces' mirrors are not
check("12 option hold: subaru side-mirrors held, other ns mirrors and subaru regulators not",
      _P.held_cross_model_cat("subaru", "side-mirrors") == "held_option_cross_model"
      and _P.held_cross_model_cat("toyota", "side-mirrors") is None
      and _P.held_cross_model_cat("subaru", "window-regulator") is None
      and _P.held_cross_model_cat("gm", "hood") == "held_exterior_cross_model")

# --------------------------------------------------------------- case 13
tr = toyota_record("12345-67890", "headlights", ("Toyota", "Camry", 2007), "headlights-lighting/headlamps", "Headlamp",
                   "Headlamp Assembly", "Driver Side", [(2007, 2009, "Toyota", "Camry", ["LE"], ["4 Cyl 2.4 L GAS"])])
jr = copy.deepcopy(hl)
jr.update(pn="1234567890", product_url=f"https://{JEEP}/oem/mopar~headlamp~1234567890")
c_t, _ = run("toyota", toy_raw(tr))
c_m, _ = run("mopar", {f"raw/{JEEP}.jsonl": [jr]})
coll = C.cross_ns_collisions({"toyota": c_t, "mopar": c_m})
check("13 the same string in two namespaces never merges: two classes, one per ns",
      ("toyota:1234567890", "headlights") in c_t.classes and ("mopar:1234567890", "headlights") in c_m.classes)
check("13 cross_ns_string_collision is reported", coll == [["1234567890", ["mopar", "toyota"]]], str(coll))

# --------------------------------------------------------------- case 14
r14 = by_pn(toy, "85720-AE010")
cur, doc = run("toyota", toy_raw(r14))
tc = sorted(T[2] for (T, cat) in cur.t_rows if T[:2] == ("Scion", "tC") and cat == "window-regulator")
check("14 tC spans 2007-2008 and 2011-2013 cover exactly those years (2009-10 not covered)",
      tc == [2007, 2008, 2011, 2012, 2013], str(tc))
tcc = sorted(c[2] for c in doc["cells"] if c[:2] == ["Scion", "tC"] and c[3] == "window-regulator")
check("14 no cell (so no span) exists for the open years 2009-10", tcc == [2007, 2008, 2011, 2012, 2013], str(tcc))
check("14 85720-AE010 lists more than 12 feed models: universal_part_suspect, no Likely",
      any(r["reason"] == "universal_part_suspect" and r["pn"] == "85720-AE010" for r in cur.refusals)
      and not any("85720-AE010" in g["pn"] for g in doc["likely"]))
check("14 _runs never bridges a gap", C._runs([("Scion", "tC", 2007), ("Scion", "tC", 2008), ("Scion", "tC", 2011)])
      == [["Scion", "tC", 2007, 2008], ["Scion", "tC", 2011, 2011]])

# --------------------------------------------------------------- case 15
base = by_pn(toy, "81560-06240")
flagged = copy.deepcopy(base)
flagged["flags"] = ["fitment_text_differs_from_store"]
cur, doc = run("toyota", toy_raw(flagged))
c = cur.classes[(key("toyota", "81560-06240"), "tail-lights")]
check("15 any flag makes the record unverified", not c.verified and "flagged" in c.records[0].problems)
bad = copy.deepcopy(base)
bad["fitment"][0]["raw"] = "2007-2009 Toyota Camry | Base, CE, LE, SE, XLE, XSE | 4 Cyl 2.4 L GAS, 6 Cyl 3.5 L GAS"
cur, doc = run("toyota", toy_raw(bad))
c = cur.classes[(key("toyota", "81560-06240"), "tail-lights")]
check("15 an evidence mismatch makes the record unverified", "evidence_mismatch" in c.records[0].problems)
check("15 >2% failures in a (site, cat): the (site, cat) is unconfirmed (systemic)",
      (TOY, "tail-lights") in cur.systemic)
st15 = confirmed((TOY, "tail-lights"), policy_sha=PSHA)
cur, doc = run("toyota", toy_raw(bad), status_table=st15)
check("15 systemic failure withholds even a confirmed category",
      "category_unconfirmed" in info(cur, T07, "tail-lights")["elig"])

# --------------------------------------------------------------- case 16
d1 = copy.deepcopy(base)
d2 = copy.deepcopy(base)
d2["fitment"] = d2["fitment"][:1]
d2["fitment"][0]["years"] = [2007, 2008]
d2["fitment"][0]["raw"] = "2007-2008 Toyota Camry | Base, CE, LE, SE, XLE | 4 Cyl 2.4 L GAS, 6 Cyl 3.5 L GAS"
d2["evidence_lines"] = [x.replace("2007-2009 Toyota Camry", "2007-2008 Toyota Camry") for x in d2["evidence_lines"]]
cur, doc = run("toyota", toy_raw(d1, d2))
c = cur.classes[(key("toyota", "81560-06240"), "tail-lights")]
check("16 differing duplicates: both kept, disputed (unverified)", c.disputed and len(c.records) == 2)
check("16 reported as disputed_duplicate", any(r["reason"] == "disputed_duplicate" for r in cur.refusals))
d3 = copy.deepcopy(d2)
d3["recrawl_of"] = "1"
cur, doc = run("toyota", toy_raw(d1, d3))
c = cur.classes[(key("toyota", "81560-06240"), "tail-lights")]
check("16 with recrawl_of the newer record replaces the older one (resolved)",
      not c.disputed and len(c.records) == 1 and c.records[0].line == 2
      and any(r["reason"] == "recrawl_resolved" for r in cur.refusals))
d4 = copy.deepcopy(d1)
cur, doc = run("toyota", toy_raw(d1, d4))
check("16 identical duplicates collapse", len(cur.classes[(key("toyota", "81560-06240"), "tail-lights")].records) == 1)

# --------------------------------------------------------------- case 17
good = json.dumps(base)
cur, _ = run("toyota", {f"raw/{TOY}.jsonl": good + "\n" + good[:40] + "\n"})
check("17 torn tail: skipped and reported, the rest is read",
      any(i["reason"] == "torn_tail" for i in cur.input_issues) and len(cur.records) == 1)
cur, _ = run("toyota", {f"raw/{TOY}.jsonl": good + "\n" + good[:40] + "\n" + good + "\n"})
check("17 corrupt middle line: the whole site file is refused (corrupt_raw)",
      any(r["reason"] == "corrupt_raw" for r in cur.refusals) and len(cur.records) == 0)
syn = copy.deepcopy(base)
syn["synthetic"] = True
cur, _ = run("toyota", toy_raw(syn), fixtures=False)
check("17 a synthetic line without --fixtures is refused",
      len(cur.records) == 0 and any(i["reason"] == "synthetic_refused" for i in cur.input_issues))

# --------------------------------------------------------------- case 18
late = (datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=121)).strftime("%Y-%m-%dT%H:%M:%SZ")
cur, doc = run("toyota", sienna_files(), status_table=st8, as_of=late)
check("18 --as-of 121 days later: stale, nothing ships",
      "stale" in info(cur, ("Toyota", "Sienna", 2004), "window-regulator")["closure"] and doc["groups"] == [])
late119 = (datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=119)).strftime("%Y-%m-%dT%H:%M:%SZ")
cur, doc = run("toyota", sienna_files(), status_table=st8, as_of=late119)
check("18 119 days later the evidence is still fresh", len(doc["groups"]) == 1)

# --------------------------------------------------------------- case 19
TC_TRIMS, TC_ENG = ["Base", "Spec"], ["4 Cyl 2.4 L GAS"]


def tc_files(years=(2006, 2007), hybrid_year=None, iM=False):
    recs, lists, ys = [], [], []
    alt = toyota_record("27060-28S01", "alternator", ("Scion", "tC", years[0]), "charging-starting/alternator", "Alternator",
                        "Alternator Assembly", None, [(2005, 2010, "Scion", "tC", TC_TRIMS, TC_ENG)])
    recs.append(alt)
    if hybrid_year:
        recs.append(toyota_record("81110-21S01", "headlights", ("Scion", "tC", hybrid_year), "headlights-lighting/headlamps",
                                  "Headlamp", "Headlamp Assembly", "Driver Side",
                                  [(hybrid_year, hybrid_year, "Scion", "tC", TC_TRIMS,
                                    TC_ENG + ["4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)"])]))
    if iM:
        recs.append(toyota_record("27060-37S01", "alternator", ("Scion", "iM", 2016), "charging-starting/alternator",
                                  "Alternator", "Alternator Assembly", None,
                                  [(2016, 2016, "Scion", "iM", ["Base"], ["4 Cyl 1.8 L GAS"])]))
    for y in list(years) + ([hybrid_year] if hybrid_year else []):
        seed = ("Scion", "tC", y)
        ys.append(year_manifest(TOY, seed, f"{y} Scion tC Parts", ["charging-starting/alternator"], TC_TRIMS, TC_ENG))
        lists.append(list_manifest(TOY, seed, "alternator", "charging-starting/alternator",
                                   [("27060-28S01", "Alternator", "Alternator Assembly", [], [], True, None)]))
    return toy_raw(*recs, lists=lists, years=ys)


st19 = confirmed((TOY, "alternator"), policy_sha=PSHA)
ef_before = json.dumps(js().ENGINE_FAMILIES, sort_keys=True, default=str)
cur, doc = run("toyota", tc_files(), status_table=st19)
vg = [g for g in doc["vg"] if g["cat"] == "alternator"]
check("19 family-uniform 2AZ years attach: one OEM vg group (toyota-2az, tC 2006-2007)",
      len(vg) == 1 and vg[0]["family"] == "toyota-2az" and vg[0]["spans"] == [["Scion", "tC", 2006, 2007]],
      json.dumps([(g["family"], g["spans"]) for g in vg]) + str(getattr(cur, "engine_refusals", [])[:3]))
ctx19 = V.context_from(js(), model_map(), status_table=st19, policy_sha=PSHA)
check("19 the vg file passes the validator", V.structural(doc, ctx19) == [], str(V.structural(doc, ctx19)[:3]))
check("19 OEM data never edits ENGINE_FAMILIES", json.dumps(js().ENGINE_FAMILIES, sort_keys=True, default=str) == ef_before)
cur, doc = run("toyota", tc_files(years=(2006, 2007), hybrid_year=2008), status_table=st19)
check("19 a year whose EngineU holds 2.4 FHEV beside 2.4 GAS is family_nonuniform",
      {"reason": "family_nonuniform", "t": ["Scion", "tC", 2008], "cat": "alternator"} in cur.engine_refusals,
      str(cur.engine_refusals))
cur, doc = run("toyota", tc_files(iM=True), status_table=st19)
check("19 a span outside every family's apps is family_gap (never extended)",
      not js().engine_families_for(2016, "Scion", "iM", "alternator")
      and any(r["reason"] == "family_gap" and r["t"] == ["Scion", "iM", 2016] for r in cur.engine_refusals),
      str(cur.engine_refusals))
cur, doc = run("toyota", tc_files(), status_table=st19, engine_reliable={})
check("19 engine cells not reliable for the namespace: E7 blocks, no vg",
      "engine_cells_unreliable" in info(cur, ("Scion", "tC", 2006), "alternator")["elig"] and doc["vg"] == [])
NIS = "www.nissanpartsdeal.com"
cur, doc = run("nissan", {f"raw/{NIS}.jsonl": nis})
cells = [i for (T, cat), i in cur.cells_info.items() if cat == "alternator"]
check("19 a PartsGiant namespace (nissanpartsdeal) is E7-gated",
      cells and all("engine_cells_unreliable" in i["elig"] for i in cells))

# --------------------------------------------------------------- case 20
J = js()
pay0 = J.build_interchange_payload()
hand = next(g for g in pay0["platformGroups"] if g["id"] == "toyota-22re#2")
check("20 fixture hand group toyota-22re#2 (climate-control) ships Verified today", hand["tier"] == "verified")


def contradiction_doc(state):
    now = datetime.now(timezone.utc)
    stamp = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sig = [["C", [["assy", ["toyota:5590089999"]]]]]
    h = C._sha1(sig)[:10]
    years = [{"t": ["Toyota", "Pickup", y], "cv": [["Toyota", "Pickup", y]],
              "closure": {"year": f"{TOY}:years:L{y - 1989}", "years": [], "lists": [f"{TOY}:lists:L{y - 1989}"],
                          "oldest_retrieved": stamp},
              "universe": {"trims_src": "year_page", "trims": ["dlx", "sr5"]}} for y in (1990, 1991)]
    return {"schema": 1, "ns": "toyota", "curate_version": "1.0", "as_of": stamp, "policy_sha256": PSHA,
            "raw": {"ref": "fixtures", "commit": "fixtures", "sites": {}},
            "classes": {"toyota:5590089999": {"pns": ["55900-89999"], "cat": "climate-control", "comp": "assy",
                                              "reman": False, "names": ["Control Assy, Heater"],
                                              "evidence": [f"{TOY}:records:L1"]}},
            "groups": [{"id": f"oem:toyota:climate-control:{h}", "cat": "climate-control", "tier": "verified",
                        "kind": "body", "sig": sig, "apps": [["Toyota", "Pickup", 1990, 1991]], "pn": ["55900-89999"],
                        "note": "Toyota catalog: same numbers on every trim and engine for these years (55900-89999)",
                        "years": years, "cars": 10}],
            "vg": [], "likely": [], "sigs": {h: sig}, "engine_cells": [],
            "cells": [["Toyota", "Pickup", 1990, "climate-control", f"sig:{h}"],
                      ["Toyota", "Pickup", 1991, "climate-control", f"sig:{h}"],
                      ["Toyota", "Pickup", 1992, "climate-control", state]]}


import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402
gd = Path(tempfile.mkdtemp(prefix="oemgroups_"))
pf_before = json.dumps(J.PLATFORM_FAMILIES["toyota-22re"], sort_keys=True, default=str)
(gd / "toyota.json").write_text(json.dumps(contradiction_doc("open:option_split")))
J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = gd, confirmed((TOY, "climate-control"), policy_sha=PSHA)
pay = J.build_interchange_payload()
h2 = next(g for g in pay["platformGroups"] if g["id"] == "toyota-22re#2")
check("20 the contradicted hand group is demoted to Likely with the OEM caveat",
      h2["tier"] == "likely" and h2["note"].endswith(J._OEM_DEMOTE_NOTE), str(h2["tier"]))
og = [g for g in pay["oemGroups"] if g["cat"] == "climate-control"]
check("20 the OEM Verified group touching those cells is withheld (Likely)", og and all(g["tier"] == "likely" for g in og))
check("20 the contradiction is in oemStatus", "contradiction oem_split toyota-22re#2" in pay["oemStatus"]["toyota"],
      pay["oemStatus"].get("toyota"))
check("20 hand data (PLATFORM_FAMILIES) is never edited, only the payload copy",
      json.dumps(J.PLATFORM_FAMILIES["toyota-22re"], sort_keys=True, default=str) == pf_before)
(gd / "toyota.json").write_text(json.dumps(contradiction_doc("open:no_year_manifest")))
pay = J.build_interchange_payload()
h3 = next(g for g in pay["platformGroups"] if g["id"] == "toyota-22re#2")
og = [g for g in pay["oemGroups"] if g["cat"] == "climate-control"]
check("20 an OEM cell that is merely not closed contradicts nothing (group stays Verified)",
      h3["tier"] == "verified" and og and og[0]["tier"] == "verified")
J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = J.SCRIPT_DIR / "oem_fitment" / "groups", None

dir_before = J.OEM_GROUPS_DIR
hp = C.hand_payload(J)
found = J._oem_contradictions(hp, {"toyota": contradiction_doc("open:option_split")})
check("20 the curate report finds the same contradiction from a hand-only build (V15 report field)",
      "oemGroups" not in hp and [c["id"] for c in found] == ["toyota-22re#2"] and found[0]["trigger"] == "oem_split",
      json.dumps(found)[:200])
check("20 hand_payload restores the OEM groups directory", J.OEM_GROUPS_DIR == dir_before)

# --------------------------------------------------------------- case 21
files = sienna_files()
src_dir = write_raw(files)
o = lambda: C.Options(fixtures=True, model_map=model_map(), js=js(), status_table=st8)  # noqa: E731
d1 = C.Curation("toyota", A.RawSource(raw_dir=src_dir), o()).run().build_doc()
d2 = C.Curation("toyota", A.RawSource(raw_dir=src_dir), o()).run().build_doc()
check("21 two runs are byte-identical", C._canon(d1) == C._canon(d2))
rnd = random.Random(21)
shuf = {k: (rnd.sample(v, len(v)) if isinstance(v, list) else v) for k, v in files.items()}
shuf = {k: [json.loads(json.dumps(x, sort_keys=bool(rnd.random() < 0.5))) if isinstance(x, dict) else x for x in v]
        for k, v in shuf.items()}
d3 = C.Curation("toyota", A.RawSource(raw_dir=write_raw(shuf)), o()).run().build_doc()
import re  # noqa: E402
def norm(d):
    d = json.loads(json.dumps(d))
    for m in d["raw"]["sites"].values():      # input file hashes identify the bytes read
        for k in [k for k in m if k.endswith("_sha256")]:
            m.pop(k)
    return re.sub(r":L\d+", ":L#", C._canon(d))
check("21 shuffled input lines give identical output (line pointers aside)", norm(d1) == norm(d3))
check("21 the Verified group survives the shuffle with the same id",
      [g["id"] for g in d1["groups"]] == [g["id"] for g in d3["groups"]] and d1["groups"])

# --------------------------------------------------------------- case 22
r22 = toyota_record("33000-99S01", "alternator", T07, "charging-starting/alternator", "Alternator",
                    "Alternator Assembly", None, [(2007, 2009, "Toyota", "Camry", ["LE"], ["4 Cyl 2.4 L GAS"])])
r22["aux_desc"] = "Transmission Assy"
try:
    run("toyota", toy_raw(r22), strict=True)
    raised = False
except C.LintError:
    raised = True
check("22 a rule-4 name ('Transmission Assy') is a lint error (strict)", raised)
cur, doc = run("toyota", toy_raw(r22))
check("22 non-strict: the lint is reported and the record never verifies",
      cur.lint and "rule4" in cur.records[0].problems)

# --------------------------------------------------------------- case 23
sw = [by_pn(jeep, p) for p in ("4602785AD", "4602780AD", "4602782AB")]
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": sw})
I = info(cur, P14, "window-switch")
check("23 Jeep 4602785AD (Front Right) is out of window-switch",
      key("mopar", "4602785AD") not in I["members"] and key("mopar", "4602780AD") in I["members"])
check("23 DM is present", "DM" in I["slots"], str(I["slots"]))
check("23 jeeppartsdeal/window-switch is unconfirmed, so nothing is Verified",
      "category_unconfirmed" in I["elig"] and doc["groups"] == [])
# make breadth 2026-11-09 (hub): GM series filter. Feed 'Silverado 1500' maps only rows
# whose option column names the 1500 / 1/2 TON series; CLASSIC rows and rows with no
# series never map; the unknown-series catch-all 'Silverado' leaves a group that holds
# the 1500 twin of the same catalog model and year.
import model_map as _MM
_SER = ("^(?!.*CLASSIC)1500(?!\\s*HD)\\b", "^(?!.*CLASSIC).*\\b1/2 TON\\b")
_t15 = _MM.Target("gm", "Chevrolet", "Silverado", "Chevrolet", "Silverado 1500", "*", (2008, 2026), False, "s", _SER)
_tall = _MM.Target("gm", "Chevrolet", "Silverado", "Chevrolet", "Silverado", "*", None, False, "any series")
def _fr(trims):
    return A.FitRow(0, 2010, 2010, "Chevrolet", "Silverado", trims, [], trims, "trim", "", trims_from_options=True)
check("series: 1500 and 1/2 TON rows map to Silverado 1500",
      C._row_maps(_fr(["1500 REGULAR CAB LONG BOX"]), _t15)
      and C._row_maps(_fr(["EXTENDED CAB 6'6\" BOX 1/2 TON"]), _t15)
      and C._row_maps(_fr(["2500 REGULAR CAB", "1500 CREW CAB"]), _t15))
check("series: 2500/3500, HD, CLASSIC and no-series rows do not map to Silverado 1500",
      not C._row_maps(_fr(["2500 REGULAR CAB"]), _t15) and not C._row_maps(_fr(["3500 CREW CAB"]), _t15)
      and not C._row_maps(_fr(["1500 HD CREW CAB"]), _t15)
      and not C._row_maps(_fr(["CLASSIC 1500 REGULAR CAB LONG BOX"]), _t15)
      and not C._row_maps(_fr([]), _t15) and not C._row_maps(_fr(["EXTENDED CAB 3/4 TON"]), _t15))
check("series: the catch-all target still maps any row", C._row_maps(_fr(["2500 REGULAR CAB"]), _tall))
class _FakeMM:
    def sources(self, ns, mk, md, y):
        return [_t15] if md == "Silverado 1500" else [_tall] if md == "Silverado" else []
_cur = C.Curation.__new__(C.Curation); _cur.ns = "gm"; _cur.mm = _FakeMM()
_Ts = [("Chevrolet", "Silverado", 2010), ("Chevrolet", "Silverado 1500", 2010), ("Chevrolet", "Avalanche", 2010),
       ("Chevrolet", "Silverado", 2011)]
check("catch-all twin: Silverado 2010 leaves when Silverado 1500 2010 is in the group; 2011 and others stay",
      _cur._drop_catchall_twins(_Ts) == [("Chevrolet", "Silverado 1500", 2010), ("Chevrolet", "Avalanche", 2010),
                                         ("Chevrolet", "Silverado", 2011)])
check("catch-all twin: no series target in the group, nothing dropped",
      _cur._drop_catchall_twins([("Chevrolet", "Silverado", 2010), ("Chevrolet", "Avalanche", 2010)])
      == [("Chevrolet", "Silverado", 2010), ("Chevrolet", "Avalanche", 2010)])
check("option hold: subaru gauge clusters held (Canada km/h clusters unmarked)",
      _P.held_cross_model_cat("subaru", "gauge-cluster") == "held_option_cross_model")
# hub 2026-11-09 rules 1-3 (GM 20945139, 25876716, 15844876), both ways
from types import SimpleNamespace as _NS
_FO = "Fitting Vehicle Options: "
check("EXPORT: an export-only option row is not for US cars (25876716, 10381000)",
      C._export_only([_FO + "CK1,2(DE2,Z5X)(EXPORT)"]) and C._export_only([_FO + "KE(DR4,Z5X)(EXPORT)"]))
check("EXPORT: a row with a non-export alternative, or EXC EXPORT, stays",
      not C._export_only([_FO + "CK1,2(DE2,Z5X)(EXPORT), CK1,2(DL8)"])
      and not C._export_only([_FO + "CK1,2(DL8)(EXC EXPORT)"]) and not C._export_only([_FO + "CK1,2(5B5)"]))
_gc = C.Curation.__new__(C.Curation)
_gc.js = _NS(GENERATION_BREAKS={"silverado": [2007, 2014], "sierra": [2007, 2014], "avalanche": [2007]})
_rec = lambda rep: _NS(replaces=rep, replaced_by=[], list_replaced_by=[], via=None)
_gTs = [("Chevrolet", "Silverado", 1999), ("Chevrolet", "Silverado", 2008), ("GMC", "Sierra", 2004),
        ("Chevrolet", "Avalanche", 2007)]
check("generation cut: a superseding number spanning a break keeps only the newest generation (twins too)",
      _gc._generation_cut(_NS(records=[_rec(["15880567"])]), _gTs)
      == [("Chevrolet", "Silverado", 2008), ("Chevrolet", "Avalanche", 2007)])
check("generation cut: no supersession keeps every vehicle-year; no break crossed keeps every one",
      _gc._generation_cut(_NS(records=[_rec([])]), _gTs) == _gTs
      and _gc._generation_cut(_NS(records=[_rec(["X"])]), [("Chevrolet", "Silverado", 2008), ("Chevrolet", "Avalanche", 2010)])
      == [("Chevrolet", "Silverado", 2008), ("Chevrolet", "Avalanche", 2010)])
check("generation cut: the longest leading-word key is used ('silverado hd' before 'silverado')",
      C.Curation._gen_breaks(_NS(js=_NS(GENERATION_BREAKS={"silverado": [2007], "silverado hd": [2001]})), "Silverado HD 2500")
      == [2001])
_cc = C.Curation.__new__(C.Curation)
_k = object()
_fr2 = lambda trims: _NS(trims=trims)
_T1, _T2 = ("Chevrolet", "Silverado", 2008), ("Cadillac", "Escalade", 2007)
_cc.t_rows = {(_T1, "window-regulator"): [(_k, None, _fr2(["1500 EXTENDED CAB LONG BOX", "2500 EXTENDED CAB STANDARD BOX"]), None)],
              (_T2, "window-regulator"): [(_k, None, _fr2(["YUKON/DENALI/ESCALADE"]), None)]}
check("cab note: every crediting row names one cab -> '<model>: <cab> only'; other models no note",
      _cc._cab_only(_k, "window-regulator", [_T1, _T2]) == "Silverado: extended cab only")
_cc.t_rows[(_T1, "window-regulator")].append((_k, None, _fr2(["1500 CREW CAB LONG BOX"]), None))
check("cab note: two cab types, or a row without a cab, gives no note",
      _cc._cab_only(_k, "window-regulator", [_T1, _T2]) == "")
check("pack text: a climate-control 'assy' gets no regulator words; regulators and switch modules keep theirs",
      C._pack_text("climate-control", "assy") == "" and C._pack_text("window-regulator", "assy") == "regulator with motor"
      and C._pack_text("climate-control", "switch-module").startswith("single switch module")
      and C._pack_text("side-mirrors", "motor") == "")
check("group notes: 20862099 names the towing/standard split; keys are (ns, cat, pn)",
      "towing" in _P.GROUP_NOTES[("gm", "side-mirrors", "20862099")]
      and all(len(k) == 3 for k in _P.GROUP_NOTES))
check("hmg variants: Forte Koup / Optima Hybrid / Soul EV are their own base model for the holds; Camry Hybrid is not",
      _P.hold_base_model("hmg", "Kia", "Forte Koup") != _P.hold_base_model("hmg", "Kia", "Forte")
      and _P.hold_base_model("hmg", "Kia", "Optima Hybrid") != _P.hold_base_model("hmg", "Kia", "Optima")
      and _P.hold_base_model("hmg", "Kia", "Soul EV") != _P.hold_base_model("hmg", "Kia", "Soul")
      and _P.hold_base_model("hmg", "Hyundai", "Santa Fe") == _P.hold_base_model("hmg", "Hyundai", "Santa Fe")
      and _P.hold_base_model("toyota", "Toyota", "Camry Hybrid") == _P.hold_base_model("toyota", "Toyota", "Camry")
      and _P.held_cross_model_cat("hmg", "side-mirrors") == "held_option_cross_model")
done("test_curate")
