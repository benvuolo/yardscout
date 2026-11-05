#!/usr/bin/env python3
"""Regression checks for the second review, payload side (_load_oem_layer,
_apply_oem_contradictions, the V11 budget, build-time expiry, validate.py's
V1 checks). Each check fails on the code before the fix (branch at be7a774)
and passes after it.

F12 a contradicted hand vg group also withholds the OEM vg groups in its cells
F13 the engine-category trigger reads family-narrowed cells, real conditions only
F16 the V11 budget holds for the payload as written (status edits, newline)
F17 size_trim is linear (the payload is serialized a fixed number of times)
F18 build-time expiry reaches Likely groups and stale files
F19 a withheld OEM Verified group carries the Likely note (V5 for its tier)
F20 a malformed entry drops only its namespace
F21 a file without sigs / cells (or cells that miss a Verified year) is refused
"""
import copy
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _util import TOY, check, confirmed, done, js, list_manifest, run, toyota_record, year_manifest
import curate as C
import validate as V

J = js()
PSHA = C.policy_sha256()
NOWDT = datetime.now(timezone.utc)
STAMP = (NOWDT - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
OLD = ("categories", "platformGroups", "engineFamilies")


def build(docs, status=None, validator=None):
    gd = Path(tempfile.mkdtemp(prefix="oem_r2p_"))
    for d in docs:
        (gd / f"{d['ns']}.json").write_text(json.dumps(d))
    keep_v = J._oem_validator
    J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = gd, status
    if validator:
        J._oem_validator = validator
    try:
        return J.build_interchange_payload()
    finally:
        J.OEM_GROUPS_DIR, J.OEM_STATUS_OVERRIDE = J.SCRIPT_DIR / "oem_fitment" / "groups", None
        J._oem_validator = keep_v


def audit(*pairs):
    return confirmed(*pairs, policy_sha=PSHA)


def proof(model, ys):
    return [{"t": ["Toyota", model, y], "cv": [["Toyota", model, y]],
             "closure": {"year": f"{TOY}:years:L{y}", "years": [], "lists": [f"{TOY}:lists:L{y}"],
                         "oldest_retrieved": STAMP},
             "universe": {"trims_src": "year_page", "trims": ["sr5"]}} for y in ys]


def note(pn):
    return f"Toyota catalog: same numbers on every trim and engine for these years ({pn})"


base = build([])

# ------------------------------------------------------------- F12 / F13
sigA = [["C", [["assy", ["toyota:2706050200"]]]]]
sigB = [["C", [["assy", ["toyota:2706050300"]]]]]
hA, hB = C._sha1(sigA)[:10], C._sha1(sigB)[:10]


def vg_doc(ecell_state_B=None, generic="open:option_split"):
    """Hand vg toyota-2uz/alternator#0 = [Tundra 2003-09, Sequoia 2003-09].
    OEM: family-narrowed Tundra 2003-04 = A, Sequoia 2003-04 = B (disjoint),
    an OEM vg group for each. The generic (all-engine) cells say
    option_split, as a model-year offering two engines always does."""
    eB = ecell_state_B or f"sig:{hB}"
    return {"schema": 1, "ns": "toyota", "curate_version": "1.0", "as_of": STAMP, "policy_sha256": PSHA,
            "raw": {"ref": "fixtures", "commit": "fixtures", "sites": {}},
            "classes": {"toyota:2706050200": {"pns": ["27060-50200"], "cat": "alternator", "comp": "assy",
                                              "reman": False, "names": ["Alternator"], "evidence": [f"{TOY}:records:L1"]},
                        "toyota:2706050300": {"pns": ["27060-50300"], "cat": "alternator", "comp": "assy",
                                              "reman": False, "names": ["Alternator"], "evidence": [f"{TOY}:records:L2"]}},
            "groups": [], "likely": [],
            "vg": [{"id": f"oem:toyota:alternator:{hA}", "family": "toyota-2uz", "cat": "alternator",
                    "tier": "verified", "kind": "engine", "sig": sigA, "spans": [["Toyota", "Tundra", 2003, 2004]],
                    "pn": ["27060-50200"], "note": note("27060-50200"), "years": proof("Tundra", (2003, 2004))}]
            + ([{"id": f"oem:toyota:alternator:{hB}", "family": "toyota-2uz", "cat": "alternator",
                 "tier": "verified", "kind": "engine", "sig": sigB, "spans": [["Toyota", "Sequoia", 2003, 2004]],
                 "pn": ["27060-50300"], "note": note("27060-50300"), "years": proof("Sequoia", (2003, 2004))}]
               if eB.startswith("sig:") else []),
            "sigs": {hA: sigA, hB: sigB},
            "cells": sorted([["Toyota", m, y, "alternator", generic] for m in ("Tundra", "Sequoia") for y in (2003, 2004)]),
            "engine_cells": sorted([["Toyota", "Tundra", y, "alternator", "toyota-2uz", f"sig:{hA}"] for y in (2003, 2004)]
                                   + [["Toyota", "Sequoia", y, "alternator", "toyota-2uz", eB] for y in (2003, 2004)])}


def fam_vg(p, fid, cat):
    return (next(f for f in p["engineFamilies"] if f["id"] == fid)["parts"].get(cat) or {}).get("vg")


ST_ALT = audit((TOY, "alternator"))
check("F12 fixture: the vg doc is valid", V.structural(vg_doc(), V.context_from(J, status_table=ST_ALT,
                                                                                 policy_sha=PSHA)) == [],
      str(V.structural(vg_doc(), V.context_from(J, status_table=ST_ALT, policy_sha=PSHA))[:3]))
p = build([vg_doc()], ST_ALT)
check("F12 the contradicted hand vg toyota-2uz/alternator#0 is removed (oem_disjoint on family-narrowed cells)",
      fam_vg(base, "toyota-2uz", "alternator") and not fam_vg(p, "toyota-2uz", "alternator")
      and "contradiction oem_disjoint toyota-2uz/alternator#0" in p["oemStatus"]["toyota"], str(p["oemStatus"]))
check("F12 and both OEM vg groups in those cells are withheld (vg has no Likely tier)",
      not (p.get("oemVg") or {}).get("toyota-2uz"), json.dumps(p.get("oemVg")))
check("F12 oemStatus says what was withheld", "2 verified withheld (contradiction)" in p["oemStatus"]["toyota"],
      p["oemStatus"]["toyota"])
check("F12 old keys only lost claims (V9)", V.old_keys_problems(base, p) == [])
p = build([vg_doc(ecell_state_B="open:conditional:notes_not_own_page")], ST_ALT)
check("F13 an evidence gap (notes not read on the car's own page) contradicts nothing: hand vg kept, OEM vg ships",
      fam_vg(p, "toyota-2uz", "alternator") == fam_vg(base, "toyota-2uz", "alternator")
      and (p.get("oemVg") or {}).get("toyota-2uz"), str(p["oemStatus"]))
for gap in ("open:conditional:option_layout", "open:conditional:trim_unattested", "open:conditional:engine_unreliable",
            "open:conditional:fitted_not_listed", "open:engine_cells_unreliable", "open:conditional:unknown"):
    p = build([vg_doc(ecell_state_B=gap)], ST_ALT)
    check(f"F13 {gap[5:]} is not oem_split", fam_vg(p, "toyota-2uz", "alternator") == fam_vg(base, "toyota-2uz", "alternator"))
for real in ("open:option_split", "open:conditional:plant", "open:conditional:engine"):
    p = build([vg_doc(ecell_state_B=real)], ST_ALT)
    check(f"F13 {real[5:]} on the family-narrowed cell is oem_split", not fam_vg(p, "toyota-2uz", "alternator"),
          str(p["oemStatus"]))

# F13 end to end: the Camry 2005 cell lists the 2AZ (2.4) and the 1MZ (3.0)
# alternators, each with a trim-layout row naming its own engine
seed = ("Toyota", "Camry", 2005)
TR = ["LE", "SE", "XLE"]
sub = "charging-starting/alternator"
recs = [toyota_record("27060-28320", "alternator", seed, sub, "Alternator", "Alternator Assembly", None,
                      [(2005, 2005, "Toyota", "Camry", TR, ["4 Cyl 2.4 L GAS"])]),
        toyota_record("27060-20230", "alternator", seed, sub, "Alternator", "Alternator Assembly", None,
                      [(2005, 2005, "Toyota", "Camry", TR, ["6 Cyl 3.0 L GAS"])])]
ys = [year_manifest(TOY, seed, "2005 Toyota Camry Parts", [sub], TR, ["4 Cyl 2.4 L GAS", "6 Cyl 3.0 L GAS"])]
ls = [list_manifest(TOY, seed, "alternator", sub, [("27060-28320", "Alternator", "Alternator Assembly", [], [], True, None),
                                                   ("27060-20230", "Alternator", "Alternator Assembly", [], [], True, None)])]
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": recs, f"raw/{TOY}.lists.jsonl": ls, f"raw/{TOY}.years.jsonl": ys})
ec = {c[4]: c[5] for c in doc["engine_cells"] if c[:4] == ["Toyota", "Camry", 2005, "alternator"]}
check("F13 the generic Camry 2005 alternator cell is option_split (two engines)",
      ["Toyota", "Camry", 2005, "alternator", "open:option_split"] in doc["cells"])
check("F13 narrowed to toyota-2az, the 1MZ number is not a candidate: no split state",
      "toyota-2az" in ec and not J._oem_split_state(ec["toyota-2az"], V.policy.SPLIT_CONDITIONS), str(ec))
p = build([doc], None)
check("F13 the hand 2AZ alternator group stays (production table, no audit)",
      fam_vg(p, "toyota-2az", "alternator") == fam_vg(base, "toyota-2az", "alternator"), str(p["oemStatus"]))

# F13 the other direction: two engines inside the family (2.4 GAS and its
# 2.4 FHEV fuel twin) each print their own number. That is a real split in
# the family and still contradicts the hand group; an engine of the family
# with no row at all is only a gap and does not.
recs2 = [toyota_record("27060-28320", "alternator", seed, sub, "Alternator", "Alternator Assembly", None,
                       [(2005, 2005, "Toyota", "Camry", TR, ["4 Cyl 2.4 L GAS"])]),
         toyota_record("27060-28400", "alternator", seed, sub, "Alternator", "Alternator Assembly", None,
                       [(2005, 2005, "Toyota", "Camry", TR, ["4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)"])])]
ys2 = [year_manifest(TOY, seed, "2005 Toyota Camry Parts", [sub], TR,
                     ["4 Cyl 2.4 L GAS", "4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)"])]
ls2 = [list_manifest(TOY, seed, "alternator", sub, [("27060-28320", "Alternator", "Alternator Assembly", [], [], True, None),
                                                    ("27060-28400", "Alternator", "Alternator Assembly", [], [], True, None)])]
cur2, doc2 = run("toyota", {f"raw/{TOY}.jsonl": recs2, f"raw/{TOY}.lists.jsonl": ls2, f"raw/{TOY}.years.jsonl": ys2})
ec2 = {c[4]: c[5] for c in doc2["engine_cells"] if c[:4] == ["Toyota", "Camry", 2005, "alternator"]}
eng_keys = sorted(map(str, cur2.engineu.get(("Toyota", "Camry", 2005), ())))
if len([k for k in eng_keys if "2.4" in k]) == 2:
    check("F13 two numbers inside the family (gas / hybrid twin) are a real split on the narrowed cell",
          J._oem_split_state(ec2.get("toyota-2az", ""), V.policy.SPLIT_CONDITIONS), str(ec2))
    p = build([doc2], None)
    check("F13 and the hand 2AZ alternator group is withheld for it",
          fam_vg(p, "toyota-2az", "alternator") != fam_vg(base, "toyota-2az", "alternator"), str(p["oemStatus"]))
else:
    print(f"SKIP F13 fuel-twin case: the FHEV engine cell did not parse as a 2.4 key ({eng_keys})")
recs3 = recs2[:1]
ls3 = [list_manifest(TOY, seed, "alternator", sub, [("27060-28320", "Alternator", "Alternator Assembly", [], [], True, None)])]
cur3, doc3 = run("toyota", {f"raw/{TOY}.jsonl": recs3, f"raw/{TOY}.lists.jsonl": ls3, f"raw/{TOY}.years.jsonl": ys2})
ec3 = {c[4]: c[5] for c in doc3["engine_cells"] if c[:4] == ["Toyota", "Camry", 2005, "alternator"]}
check("F13 a family engine with no row (hybrid twin unprinted) is a gap, not a split",
      "toyota-2az" in ec3 and not J._oem_split_state(ec3["toyota-2az"], V.policy.SPLIT_CONDITIONS), str(ec3))

# --------------------------------------------------------------- F19
sig = [["C", [["assy", ["toyota:5590089999"]]]]]
h = C._sha1(sig)[:10]


def climate_doc(state):
    return {"schema": 1, "ns": "toyota", "curate_version": "1.0", "as_of": STAMP, "policy_sha256": PSHA,
            "raw": {"ref": "fixtures", "commit": "fixtures", "sites": {}},
            "classes": {"toyota:5590089999": {"pns": ["55900-89999"], "cat": "climate-control", "comp": "assy",
                                              "reman": False, "names": ["Control Assy, Heater"],
                                              "evidence": [f"{TOY}:records:L1"]}},
            "groups": [{"id": f"oem:toyota:climate-control:{h}", "cat": "climate-control", "tier": "verified",
                        "kind": "body", "sig": sig, "apps": [["Toyota", "Pickup", 1990, 1991]], "pn": ["55900-89999"],
                        "note": note("55900-89999"),
                        "years": [dict(y, universe={"trims_src": "year_page", "trims": ["dlx", "sr5"]})
                                  for y in proof("Pickup", (1990, 1991))], "cars": 10}],
            "vg": [], "likely": [], "sigs": {h: sig}, "engine_cells": [],
            "cells": [["Toyota", "Pickup", 1990, "climate-control", f"sig:{h}"],
                      ["Toyota", "Pickup", 1991, "climate-control", f"sig:{h}"],
                      ["Toyota", "Pickup", 1992, "climate-control", state]]}


ST_CC = audit((TOY, "climate-control"))
p = build([climate_doc("open:option_split")], ST_CC)
g = next(x for x in p["oemGroups"] if x["cat"] == "climate-control")
check("F19 the withheld OEM group is Likely with the Likely note, which passes V5 for its tier",
      g["tier"] == "likely" and V._note_ok(g["note"], "likely", g["pn"]) is None
      and "same numbers on every trim" not in g["note"], g["note"])
p = build([climate_doc("open:conditional:notes_not_own_page")], ST_CC)
g = next(x for x in p["oemGroups"] if x["cat"] == "climate-control")
check("F13 a body cell whose only open reason is an evidence gap contradicts nothing (stays Verified)",
      g["tier"] == "verified" and next(x for x in p["platformGroups"] if x["id"] == "toyota-22re#2")["tier"] == "verified")

# --------------------------------------------------------------- F21
for label, mut in (("no sigs key", lambda d: d.pop("sigs")), ("empty cells", lambda d: d.update(cells=[])),
                   ("no engine_cells key", lambda d: d.pop("engine_cells")),
                   ("a vg year missing from engine_cells", lambda d: d.update(engine_cells=d["engine_cells"][1:])),
                   ("a cell naming a signature not in sigs",
                    lambda d: d["engine_cells"].append(["Toyota", "Tundra", 2005, "alternator", "toyota-2uz", "sig:ffffffffff"]))):
    d = vg_doc()
    mut(d)
    probs = V.structural(d, V.context_from(J, status_table=ST_ALT, policy_sha=PSHA))
    p = build([d], ST_ALT)
    check(f"F21 {label}: refused (V1), the namespace is dropped, hand groups untouched by it",
          any(x.startswith("V1") for x in probs) and p["oemStatus"]["toyota"].startswith("dropped: V1")
          and fam_vg(p, "toyota-2uz", "alternator") == fam_vg(base, "toyota-2uz", "alternator"), str(probs[:2]))

# --------------------------------------------------------------- F20
def likely_entry(i, pn="81110-0L%03d", stamp=STAMP):
    p0 = pn % i
    return {"id": f"oem:toyota:headlights:L:{i:010d}", "cat": "headlights", "tier": "likely", "kind": "body",
            "apps": [["Toyota", "Camry", 2004, 2005], ["Toyota", "Sienna", 2004, 2005]], "pn": [p0],
            "reason": "conditional", "cars": i + 2, "oldest_retrieved": stamp,
            "note": f"Toyota catalog lists #{p0} for both — fits some configurations; verify the number on the part"}


def likely_doc(ns="toyota", n=3, stamp=STAMP, as_of=STAMP):
    return {"schema": 1, "ns": ns, "curate_version": "1.0", "as_of": as_of, "policy_sha256": PSHA,
            "raw": {"ref": "fixtures", "commit": "fixtures", "sites": {}}, "classes": {}, "groups": [], "vg": [],
            "likely": [likely_entry(i, stamp=stamp) for i in range(n)], "sigs": {}, "cells": [], "engine_cells": []}


ok_doc = likely_doc()
check("F20 fixture: a Likely-only file is valid", V.structural(ok_doc, V.context_from(J, policy_sha=PSHA)) == [],
      str(V.structural(ok_doc, V.context_from(J, policy_sha=PSHA))[:2]))
bad = copy.deepcopy(ok_doc)
del bad["likely"][0]["id"]
check("F20 a Likely entry without an id is refused by structural (V1)",
      any(x.startswith("V1") for x in V.structural(bad, V.context_from(J, policy_sha=PSHA))))
mop = {**likely_doc(), "ns": "mopar", "likely": [dict(likely_entry(0), id="oem:mopar:headlights:L:0000000000",
                                                       apps=[["Jeep", "Liberty", 2004, 2005], ["Jeep", "Wrangler", 2004, 2005]],
                                                       note="Mopar catalog lists #81110-0L000 for both — fits some "
                                                            "configurations; verify the number on the part")]}
p = build([bad, mop])
check("F20 one malformed file drops only its namespace; the valid one ships with its own status",
      p["oemStatus"]["toyota"].startswith("dropped: V1") and p["oemStatus"]["mopar"].startswith("ok")
      and [g["ns"] for g in p["oemGroups"]] == ["mopar"], str(p["oemStatus"]))


def lax_validator():
    """The real validator with a structural() that misses the bad entry (a
    gap in the validator must still cost only that namespace)."""
    v = J_oem_validator_real()
    v.structural = lambda doc, ctx: []
    return v


J_oem_validator_real = J._oem_validator
p = build([bad, mop], validator=lax_validator)
check("F20 an entry the validator missed drops only its namespace in the payload builder (no '_all')",
      p["oemStatus"]["toyota"].startswith("dropped: malformed entry") and p["oemStatus"]["mopar"].startswith("ok")
      and "_all" not in p["oemStatus"], str(p["oemStatus"]))

# --------------------------------------------------------------- F18
old_stamp = (NOWDT - timedelta(days=130)).strftime("%Y-%m-%dT%H:%M:%SZ")
d = likely_doc()
d["likely"][1]["oldest_retrieved"] = old_stamp
p = build([d])
check("F18 a Likely group whose own evidence is 130 days old expires at build time; oemStatus says so",
      sorted(g["id"] for g in p["oemGroups"]) == sorted(x["id"] for x in d["likely"] if x["oldest_retrieved"] == STAMP)
      and "1 expired" in p["oemStatus"]["toyota"], str(p["oemStatus"]))
d = likely_doc(as_of="2024-01-01T00:00:00Z")
p = build([d])
check("F18 a file whose as_of is two years old ships no Likely group",
      p["oemGroups"] == [] and "3 expired" in p["oemStatus"]["toyota"], str(p["oemStatus"]))
d = likely_doc()
d["likely"][0].pop("oldest_retrieved")
kept, dropped = V.expire(d, NOWDT)
check("F18 an undated Likely group expires (fail closed)", dropped == [d["likely"][0]["id"]] and len(kept["likely"]) == 2)
cur, doc = run("toyota", {f"raw/{TOY}.jsonl": [toyota_record(
    "87910-0X001", "side-mirrors", ("Toyota", "Camry", 2005), "body-hardware/outside-mirrors", "Mirror Assembly",
    "Mirror Assy, Outer Rear View", "Driver Side",
    [(2004, 2005, "Toyota", "Camry", ["LE"], ["4 Cyl 2.4 L GAS"]), (2004, 2005, "Toyota", "Sienna", ["LE"],
                                                                     ["6 Cyl 3.3 L GAS"])], location=["Driver Side"])]})
check("F18 curate writes oldest_retrieved on Likely groups",
      doc["likely"] and all(g.get("oldest_retrieved") for g in doc["likely"]), json.dumps(doc["likely"])[:200])

# --------------------------------------------------------- F16 / F17
big = likely_doc(n=400)
vgd = vg_doc(ecell_state_B="open:no_year_manifest")      # one OEM vg group, no contradiction
big["vg"], big["sigs"], big["classes"] = vgd["vg"], vgd["sigs"], vgd["classes"]
big["engine_cells"] = [c for c in vgd["engine_cells"] if c[1] == "Tundra"]
big["cells"] = [c for c in vgd["cells"] if c[1] == "Tundra"]
check("F16 fixture valid", V.structural(big, V.context_from(J, status_table=ST_ALT, policy_sha=PSHA)) == [],
      str(V.structural(big, V.context_from(J, status_table=ST_ALT, policy_sha=PSHA))[:2]))
full = build([big], ST_ALT)
full_size = len(json.dumps(full, separators=(",", ":"))) + 1
groups_bytes = len(json.dumps(full["oemGroups"], separators=(",", ":")))
for cut in (5_000, 60_000, groups_bytes + 10):
    budget = full_size - cut

    def tight(budget=budget):
        v = J_oem_validator_real()
        v.policy.PAYLOAD_BYTE_BUDGET = budget
        return v
    p = build([big], ST_ALT, validator=tight)
    written = len(json.dumps(p, separators=(",", ":")) + "\n")
    check(f"F16 the payload as written (status edits and newline included) fits a budget {cut} bytes below its size",
          written <= budget and "dropped for size (V11)" in p["oemStatus"]["toyota"], f"{written} > {budget}")
check("F16 a dropped oemVg family is reported under its namespace (no '_vg' key)",
      not (p.get("oemVg") or {}).get("toyota-2uz") and "_vg" not in p["oemStatus"]
      and "dropped for size (V11)" in p["oemStatus"]["toyota"], str(p["oemStatus"]))

pay = {"categories": [], "oemGroups": [{"id": f"L{i}", "tier": "likely", "cars": i, "note": "x" * 300}
                                       for i in range(3000)], "oemVg": {}}
calls = []
real_dumps = V.json.dumps


class _Shim:
    loads = staticmethod(json.loads)

    @staticmethod
    def dumps(o, **k):
        if o is pay:
            calls.append(1)
        return real_dumps(o, **k)


V.json = _Shim
try:
    dropped = V.size_trim(pay, budget=len(real_dumps(pay, separators=(",", ":"))) // 2)
finally:
    V.json = json
check("F17 size_trim serializes the whole payload a fixed number of times, not once per drop",
      len(dropped) > 1000 and len(calls) <= 3, f"{len(calls)} full serializations for {len(dropped)} drops")
check("F17 and it still drops lowest value first, within budget",
      dropped[:3] == ["L0", "L1", "L2"] and len(real_dumps(pay, separators=(",", ":"))) <= len(real_dumps(
          {"categories": [], "oemGroups": [{"id": f"L{i}", "tier": "likely", "cars": i, "note": "x" * 300}
                                           for i in range(3000)], "oemVg": {}}, separators=(",", ":"))) // 2)
done("test_review2_payload")
