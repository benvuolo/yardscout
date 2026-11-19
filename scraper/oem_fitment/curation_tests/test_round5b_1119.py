#!/usr/bin/env python3
"""Round 5b (interchange 2026-11-19, branch interchange/round5b-1119): the
leading "*" of a Nissan option clause has no legend in the raw, so a
vehicle-year whose drive or engine limit a starred configuration decides is
held (reason held_starred_scope, "starred clause decides scope") until the
mark is explained (hub decision 1, rule 3). Nissan candidate only: the shipped
namespaces' claims and policy_sha256 do not move (hub decision 3).

"Decides": re-reading T's page without the starred configurations (the
number's own and its siblings') changes T's drive or engine limit, or leaves
T out. Where every own configuration is starred, its own starred
configurations are kept with their drive and engine words unread instead
(leaving them out would remove the claim, not its scope)."""
import json

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"
IPD = "www.infinitipartsdeal.com"

# ------------------------------------------------------------ note filters
check("unstar: starred ',' alternatives and '+' parts are left out, the rest kept as printed",
      C._unstar_notes(["Production Date: from 10/2003", F + "*KC. 2WD. SE + KC. 4WD. SE, *W, CC. XE"], NPD)
      == ["Production Date: from 10/2003", F + "KC. 4WD. SE, CC. XE"])
check("unstar: a row whose every configuration is starred has nothing left (None)",
      C._unstar_notes([F + "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE)"], NPD) is None)
check("unstar: a row with no option column is unchanged (it covers every configuration)",
      C._unstar_notes(["Production Date: 10/2004-08/2006"], NPD) == ["Production Date: 10/2004-08/2006"])
u = C._unstate_notes([F + "*SEDAN. 2WDHICAS. SPORTTEC, *SEDAN. 2WDSTD. VQ37VHR. BASE + SEDAN. AWD. VK56VD"], IPD)
check("unstate: a starred configuration keeps its option words, loses its drive and engine words; unstarred untouched",
      C._row_drive(u, IPD) is None and [st for *_x, st in C._row_clauses_star(u, IPD)] == [True, True, False]
      and "SPORTTEC" in u[0] and "VQ37VHR" not in u[0] and "SEDAN. AWD. VK56VD" in u[0], u)
check("the rule is scoped to nissan only (kept out of policy.py: the shipped policy_sha256 stays)",
      C.STARRED_SCOPE_NS == frozenset({"nissan"}) and "STARRED" not in (OEM / "policy.py").read_text())


# ------------------------------------------------------------ the decision, on synthetic pages
def lr(pn, notes, main="Combination Meter Assy-Instrument", seed=("Nissan", "Titan", 2005), cat="gauge-cluster",
       site=NPD):
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=f"https://x/{seed[1]}-{seed[2]}/{cat}.html", pn=pn,
                     section="diagram", main=main, aux="", notes=list(notes), locations=[], replace=None,
                     matched=True, excluded_by=None, product=None, retrieved="", line=1, status=200)


class _K:
    def __init__(self, pn):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), [], {pn}


class _Cur:
    for _m in ("drive_of", "drive_material", "drive_sibling", "drive_sibling_limit", "_t_drive_systems", "drive_scope",
               "engine_trans_of", "_engine_limit", "_own_rows", "_t_engines", "_t_trans_seen", "_scopes",
               "starred_scope", "_star_view", "_own_starred_only"):
        locals()[_m] = getattr(C.Curation, _m)
    _same_part = staticmethod(C.Curation._same_part)
    _ROW_CACHES = C.Curation._ROW_CACHES

    def __init__(self, T, cat, rows):
        self.ns = "nissan"
        self.t_list_rows, self.t_seed_records = {(T, cat): rows}, {}
        self.t_rows, self.t_years, self.cells_info, self.classes, self.engineu, self.engineu_src = {}, {}, {}, {}, {}, {}

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b

    def fit_engine_limit(self, c, cat, T):
        return None, ""

    def _auto_sibling(self, c, cat, T, slots):
        return False


def scope(T, rows, pn, cat="gauge-cluster"):
    return _Cur(T, cat, rows).starred_scope(_K(pn), cat, T, {"C"})


T05 = ("Nissan", "Titan", 2005)
E = lr("24810-7S00E", ["Production Date: 10/2004-08/2006", F + "*KC. (SE+ LE) + *CC. (SE+ LE)"])
S007 = lr("24810-7S007", [F + "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE)"])
S006 = lr("24810-7S006", [F + "KC. 2WD. (SE+ LE) + CC. 2WD. (SE+ LE)"])
sc = scope(T05, [E, S007], "24810-7S00E")
check("item 2: Titan 2005 7S00E's 4WD gate rests on 7S007 '*KC. 2WD. (SE+ LE)', a starred clause: held, via the sibling",
      set(sc) == {"drive"} and sc["drive"][0][0] and set(sc["drive"][0][0]) <= C._FOUR and sc["drive"][1] == (None, None, False)
      and sc["drive"][2] == "sibling", sc)
check("no drive gate (7S006 unstarred beside starred 7S00E: round 5): nothing for a star to decide",
      scope(T05, [E, S006], "24810-7S00E") == {})
T06 = ("Nissan", "Titan", 2006)
sc = scope(T06, [lr("24810-7S005", [F + "*KC. 2WD. SE + *CC. 2WD. SE"], seed=T06)], "24810-7S005")
check("(a) a drive gate stated by starred clauses only (7S005 '*KC. 2WD. SE'): held, via own",
      set(sc) == {"drive"} and sc["drive"][2] == "own", sc)
check("kept: the same drive also stated by an unstarred configuration ('*KC. 2WD. SE' + 'CC. 2WD. SE')",
      scope(T06, [lr("24810-7S005", [F + "*KC. 2WD. SE, CC. 2WD. SE"], seed=T06)], "24810-7S005") == {})
sc = scope(T06, [lr("24810-7S005", [F + "*KC. SE, CC. 4WD. SE"], seed=T06)], "24810-7S005")
check("(c) ungated, the starred configuration ('*KC. SE', any drive) widens the unstarred 'CC. 4WD. SE': held",
      set(sc) == {"drive"} and sc["drive"][0] == (None, None, False) and sc["drive"][1][0] == frozenset({"4wd"}), sc)
check("kept: every configuration starred, no gate ('*KC. 2WD. SE' + '*KC. 4WD. SE'): no unstarred configuration to differ",
      scope(T06, [lr("24810-7S005", [F + "*KC. 2WD. SE, *KC. 4WD. SE"], seed=T06)], "24810-7S005") == {})
check("kept: a starred clause that names no drive or engine ('*KC. SE' only): it decides nothing about scope",
      scope(T06, [lr("24810-7S005", [F + "*KC. SE + *CC. SE"], seed=T06)], "24810-7S005") == {})
X00 = ("Nissan", "Xterra", 2000)
sc = scope(X00, [lr("96301-3S500", [F + "*W. VG33E"], main="Mirror Assy-Door", seed=X00, cat="side-mirrors"),
                 lr("96301-S3800", [F + "W. KA24DE + W. VG33E. XE"], main="Mirror Assy-Door", seed=X00,
                    cat="side-mirrors")], "96301-3S500", cat="side-mirrors")
check("(b) an engine gate stated by a starred clause only (Xterra 2000 3S500 '*W. VG33E'): held",
      set(sc) == {"engine"} and sc["engine"][0] == "3.3L" and sc["engine"][1] == "" and sc["engine"][2] == "own", sc)

# ------------------------------------------------------------ committed files
cand = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
held = json.loads((OEM / "groups" / "_report" / "nissan.starred_held.json").read_text())
rep = json.loads((OEM / "groups" / "_report" / "nissan.json").read_text())
by = {(g["cat"], tuple(g["pn"])): g for g in cand["likely"]}


def years(apps):
    return {(a[0], a[1], y) for a in apps for y in range(a[2], a[3] + 1)}


bad = []
for e in held["held"]:
    g = by.get((e["cat"], tuple(e["pn"])))
    hy = {tuple(h["t"]) for h in e["held"]}
    if e["unit"] == "group" and g is not None:
        bad.append(("group still listed", e["pn"]))
    if e["unit"] == "vehicle-year" and (g is None or years(g["apps"]) != years(e["kept_apps"]) or years(g["apps"]) & hy):
        bad.append(("kept apps", e["pn"]))
check("candidate: no held vehicle-year is claimed; a vehicle-year hold leaves exactly kept_apps", not bad, bad[:3])
# round6-1119 (hub decision 2): the same file also lists held_starred_only (kind starred_only)
R6 = ("held_cab_inferred", "held_starred_only", "held_starred_scope", "held_option_tie")
check("held list: known reasons and kinds, every held vehicle-year shows a starred configuration",
      all(e["reason"] in ("held_starred_scope", "held_starred_only")
          and all(set(h["kinds"]) <= {"a", "b", "c_drive", "c_engine", "starred_only"} and h["kinds"]
                  and any(x["starred"] for x in h["clauses"]) for h in e["held"])
          for e in held["held"]))
whole = {(e["cat"], e["pn"][0]) for e in held["held"] if e["unit"] == "group"}
refd = {(r["cat"], r["pn"]) for r in rep["refusals"] if r["reason"] in R6}
check("report: every group held whole has its round-5b/6 refusal; the scope counter matches the a/b/c kinds",
      whole <= refd and rep["summary"].get("likely_app_years_starred_scope")
      and sum(rep["summary"]["likely_app_years_starred_scope"].values())
      == sum(any(k != "starred_only" for k in h["kinds"]) for e in held["held"] for h in e["held"]), sorted(whole - refd)[:3])


def claims(cat, pn, mk, md, y):
    g = by.get((cat, (pn,)))
    return bool(g) and (mk, md, y) in years(g["apps"])


check("candidate: Titan 2005 not claimed on 24810-7S00E (its 4WD gate's basis 7S007 is starred)",
      not claims("gauge-cluster", "24810-7S00E", "Nissan", "Titan", 2005))
check("candidate: the 1119e '*' RISK items are held (K6301-1PM0B M37 2012, 96301-3EV0B QX70 2014, 24820-3ZD0A QX56 2013)",
      not claims("side-mirrors", "K6301-1PM0B", "Infiniti", "M37", 2012)
      and not claims("side-mirrors", "96301-3EV0B", "Infiniti", "QX70", 2014)
      and not claims("gauge-cluster", "24820-3ZD0A", "Infiniti", "QX56", 2013))
check("candidate: 96301/96302-1CA0B claim no FX35 (listed for it only by the starred '*W. VQ35HR. PREMIUM')",
      not any(claims("side-mirrors", pn, "Infiniti", "FX35", y) for pn in ("96301-1CA0B", "96302-1CA0B")
              for y in range(2009, 2013)))
check("candidate: kept where every starred configuration repeats an unstarred one (80720-2Z700 Xterra 2002)",
      claims("window-regulator", "80720-2Z700", "Nissan", "Xterra", 2002))
for p in sorted((OEM / "groups").glob("*.json")):
    check(f"shipped groups/{p.name}: no held_starred_scope claim removed (nissan candidate only)",
          not (OEM / "groups" / "_report" / f"{p.stem}.starred_held.json").exists())
done("test_round5b_1119")
