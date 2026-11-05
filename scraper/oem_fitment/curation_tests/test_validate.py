#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_validate: one mutation per V-check must be refused."""
import copy
import json
from datetime import datetime, timedelta, timezone

from _util import TOY, check, confirmed, done, js, model_map, run, sienna_fixture
import curate as C
import validate as V

PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
cur, doc = run("toyota", sienna_fixture(), status_table=ST)
ctx = V.context_from(js(), model_map(), status_table=ST, policy_sha=PSHA)
check("baseline: the positive-control file is valid", V.structural(doc, ctx) == [] and len(doc["groups"]) == 1,
      str(V.structural(doc, ctx)[:3]))


def refused(name, mut, code, c=ctx):
    d = copy.deepcopy(doc)
    mut(d)
    p = V.structural(d, c)
    check(f"{code} refuses {name}", any(x.startswith(code) for x in p), str(p[:3]))


g0 = lambda d: d["groups"][0]  # noqa: E731
refused("tier 'verfied'", lambda d: g0(d).update(tier="verfied"), "V1")
refused("a group routed to a combo category", lambda d: g0(d).update(cat="transmission-auto"), "V10")
refused("an engine category in body groups", lambda d: g0(d).update(cat="alternator"), "V1")
refused("an app with '*'", lambda d: g0(d)["apps"].__setitem__(0, ["Toyota", "Sienna*", 2004, 2005]), "V2")
refused("an app of another namespace's make", lambda d: g0(d)["apps"].__setitem__(0, ["Honda", "Odyssey", 2004, 2005]), "V2")
refused("an app outside the model map", lambda d: g0(d)["apps"].__setitem__(0, ["Toyota", "Siena", 2004, 2005]), "V2")
refused("years past current year + 1", lambda d: g0(d)["apps"].__setitem__(0, ["Toyota", "Sienna", 2004, 2099]), "V2")


def overlap(d):
    g = copy.deepcopy(g0(d))
    g["id"] = g["id"] + "x"
    d["groups"].append(g)


refused("an overlap (one vehicle-year in two Verified groups of one category)", overlap, "V3")
refused("a missing proof (no list pointers)", lambda d: g0(d)["years"][0]["closure"].update(lists=[]), "V4")
refused("an unattested universe", lambda d: g0(d)["years"][0]["universe"].update(trims_src="unattested"), "V4")
refused("a one-year group", lambda d: (g0(d).update(apps=[["Toyota", "Sienna", 2004, 2004]]),
                                       g0(d).update(years=g0(d)["years"][:1])), "V4")
refused("stale evidence", lambda d: [y["closure"].update(oldest_retrieved="2026-06-01T00:00:00Z") for y in g0(d)["years"]], "V4")
refused("a note containing <b>", lambda d: g0(d).update(note=g0(d)["note"].replace("Toyota catalog", "<b>Toyota</b> catalog")), "V5")
refused("a note with a banned word", lambda d: g0(d).update(note=g0(d)["note"].replace("same numbers", "always same numbers")), "V5")
refused("a note naming no part number", lambda d: g0(d).update(
    note="Toyota catalog: same numbers on every trim and engine for these years (see catalog)"), "V5")
refused("a class key from another namespace", lambda d: g0(d)["sig"][0][1][0][1].__setitem__(0, "mopar:123"), "V6")
refused("a class in two slots", lambda d: g0(d)["sig"][1][1][0][1].__setitem__(0, g0(d)["sig"][0][1][0][1][0]), "V6")
refused("an unconfirmed category", lambda d: None, "V7",
        c=V.context_from(js(), model_map(), status_table={}, policy_sha=PSHA))
refused("an audit record for another raw commit", lambda d: None, "V7",
        c=V.context_from(js(), model_map(), status_table=confirmed((TOY, "window-regulator"), policy_sha=PSHA,
                                                                     raw_commit="deadbeef"), policy_sha=PSHA))
refused("an id that does not recompute", lambda d: g0(d).update(id=g0(d)["id"][:-1] + "0"), "V8")
refused("a stale policy hash", lambda d: d.update(policy_sha256="0" * 64), "V8")
refused("a rule-4 class name", lambda d: next(iter(d["classes"].values())).update(names=["Transmission Assy"]), "V10")
refused("an oem-kind (Phase 3) category", lambda d: g0(d).update(cat="ac-compressor"), "V10")

# expiry (build time): 121 days -> dropped, 119 -> kept
now = datetime.strptime(g0(doc)["years"][0]["closure"]["oldest_retrieved"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
d2, dropped = V.expire(doc, now + timedelta(days=121))
check("build-time expiry drops a group whose evidence is 121 days old", d2["groups"] == [] and dropped == [g0(doc)["id"]])
d2, dropped = V.expire(doc, now + timedelta(days=119))
check("build-time expiry keeps 119-day-old evidence", len(d2["groups"]) == 1 and not dropped)

# V9: an OEM entry injected into platformGroups is refused; demotions pass
J = js()
J.OEM_GROUPS_DIR = "/nonexistent"
before = J.build_interchange_payload()
after = copy.deepcopy(before)
after["platformGroups"].append({"id": "oem:toyota:x", "label": "Toyota catalog", "cat": "window-regulator",
                                "tier": "verified", "note": "x", "apps": [["Toyota", "Sienna", 2004, 2005]]})
check("V9 refuses an OEM entry injected into platformGroups", V.old_keys_problems(before, after) != [])
after = copy.deepcopy(before)
g = next(x for x in after["platformGroups"] if x["tier"] == "verified")
g["tier"] = "likely"
g["note"] += J._OEM_DEMOTE_NOTE
fam = next(f for f in after["engineFamilies"] if any("vg" in p for p in f["parts"].values()))
cat = next(c for c, p in fam["parts"].items() if "vg" in p)
fam["parts"][cat]["vg"] = fam["parts"][cat]["vg"][1:]
check("V9 accepts demotions (verified -> likely, a removed vg group)", V.old_keys_problems(before, after) == [],
      str(V.old_keys_problems(before, after)[:3]))
after2 = copy.deepcopy(before)
next(x for x in after2["platformGroups"] if x["tier"] == "likely")["tier"] = "verified"
check("V9 refuses a promotion (likely -> verified)", V.old_keys_problems(before, after2) != [])
after3 = copy.deepcopy(before)
f3 = next(f for f in after3["engineFamilies"] if any("vg" in p for p in f["parts"].values()))
c3 = next(c for c, p in f3["parts"].items() if "vg" in p)
f3["parts"][c3]["vg"].append([["Toyota", "Sienna", 2004, 2005]])
check("V9 refuses an added vg group", V.old_keys_problems(before, after3) != [])
after4 = copy.deepcopy(before)
after4["categories"][0]["tokens"] = after4["categories"][0]["tokens"] + ["x"]
check("V9 refuses a changed category", V.old_keys_problems(before, after4) != [])
J.OEM_GROUPS_DIR = J.SCRIPT_DIR / "oem_fitment" / "groups"

# V11: an oversize payload drops Likely groups first, lowest value first
pay = {"categories": [], "oemGroups": [
    {"id": f"L{i}", "tier": "likely", "cars": i, "note": "x" * 2000} for i in range(10)] + [
    {"id": "V0", "tier": "verified", "cars": 1, "note": "x" * 2000}], "oemVg": {}}
dropped = V.size_trim(pay, budget=12_000)
check("V11 drops Likely before Verified, lowest cars*(cars-1) first",
      dropped[:3] == ["L0", "L1", "L2"] and "V0" not in dropped and len(json.dumps(pay)) <= 12_100, str(dropped))
pay2 = copy.deepcopy(pay)
check("V11 leaves an in-budget payload alone", V.size_trim(pay2, budget=10 ** 9) == [])

# V12-V15 (full)
check("V12 refuses a file that does not reproduce", any(p.startswith("V12") for p in V.full(
    doc, lambda: {**doc, "as_of": "2026-01-01T00:00:00Z"})))
check("V12 accepts a reproducible file", V.full(doc, lambda: copy.deepcopy(doc)) == [])
check("V13 refuses shipped pairs the oracle rejects", any(p.startswith("V13") for p in V.full(
    doc, lambda: copy.deepcopy(doc), oracle_pairs=set())))
empty = copy.deepcopy(doc)
empty["groups"] = []
check("V14 churn needs --accept-churn", any(p.startswith("V14") for p in V.full(doc, lambda: copy.deepcopy(doc),
                                                                              committed=empty)))
check("V14 churn accepted with an audit file", not any(p.startswith("V14") for p in V.full(
    doc, lambda: copy.deepcopy(doc), committed=empty, accept_churn="audit.json")))
check("V15 refuses a report without refusals/contradictions", any(p.startswith("V15") for p in V.full(
    doc, lambda: copy.deepcopy(doc), report={"funnel_cars": {}})))
check("validate.py imports no network or crawler module",
      not any(m in open(V.__file__).read() for m in ("import requests", "import fetch", "from fetch", "urllib.request",
                                                     "import adapters", "import curate")))
done("test_validate")
