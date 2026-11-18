#!/usr/bin/env python3
"""Per-app gates on OEM Likely groups (interchange gates-1118).

The §5.16 limits curate.py writes into a group's note ("Tahoe: 2WD only",
"1500: 4WD only", "Q70: 3.7L, gas only", "crew cab only") were only text:
the app listed every lot car of the model-year as a donor. curate.py now
writes each vehicle-year's limits as a gate beside the note ("gates":
[[make, model, lo, hi, gate]]); validate.py checks them (inside the group's
own apps, known vocabulary); the payload builder ships a gated app as
[make, model, lo, hi, null, gate] (the aftermarket row's shape), which
docs/app.js applies (backend/test/pf_guards_unit.mjs tests that side).

Hub refinement (2026-11-18, after groups/_report/restored_verify_2026-11-18b
.json): a drive limit carries its basis. "stated": the catalog states it (a
row's own code, or both drive pages read and the number on one). "unchecked":
only one drive's page is in the raw, or fitment rows that may be incomplete.
The gate is the same; the note says "<model>: only 2WD checked".
Only narrows: apps, ids and claims are unchanged."""
import json
from types import SimpleNamespace as NS

from _util import OEM, check, done, js, model_map
import curate as C
import policy
import validate as V

J = js()
F = "Fitting Vehicle Options: "
GM, JPD, FPG = "www.gmpartsgiant.com", "www.jeeppartsdeal.com", "www.fordpartsgiant.com"
TWO, FOUR = frozenset({"2wd"}), frozenset({"4wd"})

# ------------------------------------------------------------ helpers
check("drive gate: classes in a fixed order", C._drive_gate({"rwd", "fwd"}) == "fwd/rwd"
      and C._drive_gate(TWO) == "2wd" and C._drive_gate({"awd", "4wd"}) == "4wd/awd" and C._drive_gate({"a4wd"}) == "a4wd")
check("cab gate: the note's words, one spelling", C._cab_gate("crew cab") == "crew cab"
      and C._cab_gate("Super  Cab") == "supercab" and C._cab_gate("super crew") == "supercrew")
T1, T2, T3 = ("Chevrolet", "Tahoe", 2006), ("Chevrolet", "Tahoe", 2007), ("Chevrolet", "Tahoe", 2008)
runs = C._gate_runs({T1: {"drive": "2wd"}, T2: {"drive": "2wd"}, T3: {"drive": "2wd", "fuel": "gas"},
                     ("GMC", "Yukon", 2007): {"cab": "crew cab"}})
check("gate runs: consecutive years with the same gate merge; keys sorted; per model",
      runs == [["Chevrolet", "Tahoe", 2006, 2007, {"drive": "2wd"}],
               ["Chevrolet", "Tahoe", 2008, 2008, {"drive": "2wd", "fuel": "gas"}],
               ["GMC", "Yukon", 2007, 2007, {"cab": "crew cab"}]], str(runs))
check("gate runs: none for no limits", C._gate_runs({}) == [])


# ------------------------------------------------------------ drive basis
class _Cur:
    drive_basis = C.Curation.drive_basis
    _unchecked_note = C.Curation._unchecked_note

    def __init__(self, ns, list_rows=None, seeds=None, t_rows=None):
        self.ns, self.t_list_rows, self.t_seed_records, self.t_rows = ns, list_rows or {}, seeds or {}, t_rows or {}

    def _gm_page_letters(self, T):
        return frozenset()

    def note_excludes(self, notes, T, market=True):
        return False


def seed(pn, ns, page, notes=(), site=GM):
    return NS(key=policy.pn_key(ns, pn), note_texts=list(notes), site=site,
              list_url=f"https://{site}/parts-list/{page}/body/x.html")


cat = "headlights"
c = NS(key=policy.pn_key("gm", "22853025"))
only2 = _Cur("gm", seeds={(T2, cat): [seed("22853025", "gm", "2007-chevrolet-tahoe-2wd")]})
check("basis: the number on the 2wd page, the 4wd page not in the raw -> unchecked (the verifier's GM class)",
      only2.drive_basis(c, cat, T2, TWO) == "unchecked")
both = _Cur("gm", seeds={(T2, cat): [seed("22853025", "gm", "2007-chevrolet-tahoe-2wd"),
                                    seed("22853027", "gm", "2007-chevrolet-tahoe-4wd")]})
check("basis: the 4wd page read in this category without the number -> stated (the catalog states the split)",
      both.drive_basis(c, cat, T2, TWO) == "stated")
other_cat = _Cur("gm", seeds={(T2, cat): [seed("22853025", "gm", "2007-chevrolet-tahoe-2wd")],
                             (T2, "side-mirrors"): [seed("15999999", "gm", "2007-chevrolet-tahoe-4wd")]})
check("basis: the 4wd page read only for another category -> still unchecked",
      other_cat.drive_basis(c, cat, T2, TWO) == "unchecked")
lr = lambda pn, variant, matched=True, notes=(): NS(pn=pn, variant=variant, matched=matched, notes=list(notes), site=GM)  # noqa: E731
listed_there = _Cur("gm", list_rows={(T2, cat): [lr("22853025", "2wd"), lr("22853025", "4wd", matched=False)]})
check("basis: the 4wd page lists the number in a row we did not match -> unchecked, not stated",
      listed_there.drive_basis(c, cat, T2, TWO) == "unchecked")
ram = ("Ram", "1500", 2012)
cm = NS(key=policy.pn_key("mopar", "55277414AB"))
code = _Cur("mopar", seeds={(ram, "tail-lights"): [seed("55277414AB", "mopar", "2012-ram-1500",
                                                        [F + "41 - SEDAN/QUAD CAB SWB, 6 - Lt. Duty DODGE 4WD"], JPD)]})
check("basis: a sales code naming the drive on the row itself -> stated (Mopar '6 - Lt. Duty DODGE 4WD')",
      code.drive_basis(cm, "tail-lights", ram, FOUR) == "stated")


def fit(trims):
    return NS(layout="trim", trims=list(trims), options=[])


ch = NS(key=policy.pn_key("mopar", "55277409AE"))
sib = NS(key=policy.pn_key("mopar", "55277411AE"))
fit_only = _Cur("mopar", seeds={(ram, cat): [seed("55277409AE", "mopar", "2012-ram-1500", ["Left [LMA] Up To 07/23/2012"], JPD)]},
                t_rows={(ram, cat): [(ch, None, fit(["4WD SLT", "4WD ST"]), None), (sib, None, fit(["4WD SLT"]), None)]})
check("basis: fitment rows only, and no number's fitment row on the page names 2WD -> unchecked (2012 Ram headlamps)",
      fit_only.drive_basis(ch, cat, ram, FOUR) == "unchecked")
fit_both = _Cur("mopar", seeds=fit_only.t_seed_records,
                t_rows={(ram, cat): [(ch, None, fit(["4WD SLT", "4WD ST"]), None), (sib, None, fit(["2WD SLT"]), None)]})
check("basis: another number's fitment row names 2WD -> the catalog lists both drives: stated",
      fit_both.drive_basis(ch, cat, ram, FOUR) == "stated")

# ------------------------------------------------------------ wording
u = _Cur("gm")
Ts = [T2, ("Chevrolet", "Avalanche", 2007)]
check("note: one model unchecked -> '<model>: only 2WD checked'", u._unchecked_note({T2: "2WD"}, Ts) == "Tahoe: only 2WD checked")
check("note: every vehicle-year unchecked alike -> 'only FWD checked'",
      u._unchecked_note({T2: "FWD", Ts[1]: "FWD"}, Ts) == "only FWD checked")
check("note: some years of a model -> years named",
      u._unchecked_note({T1: "2WD"}, [T1, T2]) == "Tahoe 2006: only 2WD checked")
check("note: models sharing the label are named together",
      u._unchecked_note({T2: "2WD", ("GMC", "Yukon", 2007): "2WD"}, [T2, ("GMC", "Yukon", 2007), Ts[1]])
      == "Tahoe, Yukon: only 2WD checked")
check("note: none -> ''", u._unchecked_note({}, Ts) == "")
CM, FO = ("Ford", "C-Max", 2013), ("Ford", "Focus", 2012)
check("note: every vehicle-year unchecked in one family under different labels -> the family once "
      "(keeps the restored C-Max/Focus window-motor notes within 160 characters)",
      u._unchecked_note({CM: "2WD", FO: "FWD"}, [CM, FO]) == "only 2WD checked"
      and u._unchecked_note({CM: "4WD", FO: "AWD"}, [CM, FO]) == "only 4WD/AWD checked"
      and u._unchecked_note({CM: "2WD"}, [CM, FO]) == "C-Max: only 2WD checked")
check("note: the short form keeps a 2004 Trailblazer regulator note within 160 characters",
      C._likely_note_fits("GM", "19331461", "option: fits some option packages; Trailblazer: only 2WD checked",
                          C._pack_text("window-regulator", "reg", "FL")))

# ------------------------------------------------------------ validator
check("gate vocabulary: good gates pass", all(V.gate_problem(g) is None for g in (
    {"drive": "2wd", "drive_basis": "unchecked"}, {"drive": "4wd/awd"}, {"body": "coupe"}, {"body": ["sedan", "coupe"]},
    {"cab": "crew cab"}, {"eng": ["3.7L", "5.6L"]}, {"fuel": "gas"}, {"trans": "MT"})))
check("gate vocabulary: bad gates are refused", all(V.gate_problem(g) for g in (
    {}, {"drive": "2wd/4wd"}, {"drive": "xwd"}, {"drive_basis": "stated"}, {"drive": "2wd", "drive_basis": "maybe"},
    {"body": "Sedan <b>"}, {"cab": "crew"}, {"eng": "3.7L"}, {"eng": ["3.7"]}, {"fuel": "ev"}, {"trans": "manual"},
    {"trim": "SE"})))
apps = [["Chevrolet", "Avalanche", 2007, 2007], ["Chevrolet", "Tahoe", 2006, 2008]]
check("gates inside the group's apps pass", V._gates_ok([["Chevrolet", "Tahoe", 2007, 2008, {"drive": "2wd"}]], apps) is None)
check("a gate outside the apps is refused (a gate never adds a vehicle-year)",
      "outside" in (V._gates_ok([["Chevrolet", "Tahoe", 2008, 2009, {"drive": "2wd"}]], apps) or "")
      and "outside" in (V._gates_ok([["GMC", "Yukon", 2007, 2007, {"drive": "2wd"}]], apps) or ""))
check("two gates for one vehicle-year, unsorted runs, malformed runs are refused",
      V._gates_ok([["Chevrolet", "Tahoe", 2007, 2007, {"drive": "2wd"}], ["Chevrolet", "Tahoe", 2007, 2008, {"fuel": "gas"}]], apps)
      and V._gates_ok([["Chevrolet", "Tahoe", 2008, 2008, {"drive": "2wd"}], ["Chevrolet", "Avalanche", 2007, 2007, {"drive": "2wd"}]], apps)
      and V._gates_ok([["Chevrolet", "Tahoe", 2007, {"drive": "2wd"}]], apps) and V._gates_ok([], apps))

# ------------------------------------------------------------ payload shape
ga = J._oem_gated_apps(apps, [["Chevrolet", "Tahoe", 2007, 2007, {"drive": "2wd", "drive_basis": "unchecked"}]])
check("payload: a gated year is split out as [make, model, lo, hi, null, gate]; the rest is unchanged",
      ga == [["Chevrolet", "Avalanche", 2007, 2007], ["Chevrolet", "Tahoe", 2006, 2006],
             ["Chevrolet", "Tahoe", 2007, 2007, None, {"drive": "2wd", "drive_basis": "unchecked"}],
             ["Chevrolet", "Tahoe", 2008, 2008]], str(ga))
check("payload: no gates -> the apps as they are", J._oem_gated_apps(apps, None) is apps)
try:
    J._oem_gated_apps(apps, [["GMC", "Yukon", 2007, 2007, {"drive": "2wd"}]])
    check("payload: a gate outside the apps raises (the namespace is dropped, fail closed)", False)
except ValueError:
    check("payload: a gate outside the apps raises (the namespace is dropped, fail closed)", True)

# ------------------------------------------------------------ the committed files
ctx = V.context_from(J, model_map(), policy_sha=policy.tree_sha256())
by_ns = {}
for p in sorted((OEM / "groups").glob("*.json")) + [OEM / "groups" / "_report" / "nissan.candidate.json"]:
    d = json.loads(p.read_text())
    by_ns[p.name] = d
    probs = [x for x in V.structural(d, ctx) if "gate" in x]
    check(f"{p.name}: every gate passes the validator", not probs, str(probs[:3]))
bad_words, n_unc, n_st = [], 0, 0
for name, d in by_ns.items():
    for g in d["likely"]:
        for mk, md, lo, hi, gate in g.get("gates") or []:
            if "drive" not in gate:
                continue
            lab = C._drive_label(frozenset(gate["drive"].split("/")))
            if gate.get("drive_basis") == "unchecked":
                n_unc += 1
                fam = "2WD" if lab in ("2WD", "FWD", "RWD") else "4WD/AWD"
                ok = (f"only {lab} checked" in g["note"] or f"only {fam} checked" in g["note"]) \
                    and f"{lab} only" not in g["note"]
            else:
                n_st += 1
                ok = f"{lab} only" in g["note"] or f"{lab}," in g["note"]
            if not ok:
                bad_words.append((name, g["id"], md, gate, g["note"]))
check("every drive gate carries its basis, and the note words it ('X only' stated, 'only X checked' unchecked)",
      not bad_words and n_unc and n_st, str(bad_words[:3]))
# payload: the shipped OEM groups carry the gates and exactly the curated app-years
lazy = {}
for p in sorted((OEM.parents[1] / "docs" / "data" / "oem").glob("*.json")):
    for g in json.loads(p.read_text()).get("oemGroups") or []:
        lazy[g["id"]] = g
yrs = lambda apps_: {(a[0], a[1], y) for a in apps_ for y in range(a[2], a[3] + 1)}  # noqa: E731
mism, gated_ship = [], 0
for name, d in by_ns.items():
    if name.endswith("candidate.json"):
        continue
    for g in d["likely"]:
        s = lazy.get(g["id"])
        if s is None:
            continue
        if yrs(s["apps"]) != yrs(g["apps"]):
            mism.append(g["id"])
        want = {(mk, md, y): gate for mk, md, lo, hi, gate in g.get("gates") or [] for y in range(lo, hi + 1)}
        got = {(a[0], a[1], y): a[5] for a in s["apps"] if len(a) == 6 for y in range(a[2], a[3] + 1)}
        gated_ship += bool(got)
        if want != got or any(len(a) == 6 and a[4] is not None for a in s["apps"]):
            mism.append(g["id"])
check("payload files: every shipped group has exactly its curated app-years, and its gates on the gated years",
      not mism and gated_ship, str(mism[:5]))
check("nissan stays a candidate: no groups/nissan.json", not (OEM / "groups" / "nissan.json").exists())
done("test_gates_1118")
