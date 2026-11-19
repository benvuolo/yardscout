#!/usr/bin/env python3
"""Round 4 rules (interchange 2026-11-19, branch interchange/round4-1119): the
hub's decisions after the independent nissan check
groups/_report/nissan_verify_2026-11-19d.json (2 WRONG: AWD siblings).

1. Same-option drive sibling (policy.LIKELY_DRIVE_SIBLING_RULE): T's page lists
   another number of the same part and position for the same option clause
   plus a drive word (asterisks ignored): this number does not fit that drive.
2. Build window inside a model year (policy.LIKELY_BUILD_WINDOW_RULE): the
   vehicle-year stays only with the window in the note and a "built" gate,
   which the app never confirms; a note over the cap leaves the vehicle-year
   out; supersession windows are unchanged.
3. Pages of one catalog disagree (no date on T's page, a window on another
   model-year page of the same catalog model): the narrower reading.
Also: the gate vocabulary, live_diff's comparison, the committed files."""
import json

from _util import OEM, check, done
import adapters as A
import curate as C
import policy
import validate as V

F = "Fitting Vehicle Options: "
IPD, NPD = "www.infinitipartsdeal.com", "www.nissanpartsdeal.com"

# ------------------------------------------------------------ helpers
check("windows: range, from, till, comma list, subaru yyyymm, none",
      C._row_windows(["Production Date: 08/2009-01/2010"]) == [(2009 * 12 + 8, 2010 * 12 + 1)]
      and C._row_windows(["Production Date: from 01/2010"]) == [(2010 * 12 + 1, C._WIN_OPEN)]
      and C._row_windows(["Production Date: till 05/2012"]) == [(0, 2012 * 12 + 5)]
      and len(C._row_windows(["Production Date: 02/2009-08/2010,from 08/2010"])) == 2
      and C._row_windows(["Production Date: 200409 - 200608"]) == [(2004 * 12 + 9, 2006 * 12 + 8)]
      and C._row_windows([F + "W. SE"]) == [] and C._row_windows(["Production Date: 05/2012"]) == [])
w10 = C._row_windows(["Production Date: 08/2009-01/2010"])
check("window gap / label / gate (Pathfinder 2010 27510-EA00A)",
      C._win_gap(w10, 2010) == [(2009 * 12 + 7, 2009 * 12 + 7), (2010 * 12 + 2, 2010 * 12 + 6)]
      and C._win_label(w10) == "built 08/2009-01/2010" and C._win_gate(w10) == "2009-08..2010-01"
      and C._win_label([(2010 * 12 + 1, C._WIN_OPEN)]) == "built from 01/2010"
      and C._win_gate([(0, 2005 * 12 + 12)]) == "..2005-12" and C._win_gap([(2008 * 12 + 1, C._WIN_OPEN)], 2010) == [])
check("clauses: asterisks ignored, drive words taken out of the tokens, '+' parts on config sites, Nissan AUTO",
      C._row_clauses([F + "*W. AWD. PREMIUM"], IPD) == [(("W", "PREMIUM"), {"awd"}, set())]
      and C._row_clauses([F + "*W. PREMIUM"], IPD) == [(("W", "PREMIUM"), set(), set())]
      and [t for t, _p, _n in C._row_clauses([F + "*KC. 4WD. SE + *CC. 4WD. SE"], NPD)] == [("KC", "SE"), ("CC", "SE")]
      and C._row_clauses([F + "W. AUTO. SE"], NPD)[0][1] == {"a4wd"}
      and C._row_clauses([], NPD) == [((), set(), set())])


# ------------------------------------------------------------ stubs
def lr(pn, notes, main="Mirror Assy-Outside, RH", loc=("Passenger Side",), seed=("Infiniti", "QX60", 2015),
       site=IPD, url=None, repl=None, cat="side-mirrors"):
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=url or f"https://x/{seed[1]}-{seed[2]}/{cat}.html",
                     pn=pn, section="diagram", main=main, aux="", notes=list(notes), locations=list(loc),
                     replace=repl, matched=True, excluded_by=None, product=None, retrieved="", line=1, status=200)


class _K:
    def __init__(self, pn, records=()):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), list(records), {pn}


class _Cur:
    drive_sibling = C.Curation.drive_sibling
    drive_sibling_limit = C.Curation.drive_sibling_limit
    _same_part = staticmethod(C.Curation._same_part)
    _t_drive_systems = C.Curation._t_drive_systems
    build_window = C.Curation.build_window
    _pn_list_rows = C.Curation._pn_list_rows
    _pn_other_windows = C.Curation._pn_other_windows

    def __init__(self, ns, pages, links=(), sources=None):
        self.ns = ns
        self.t_list_rows, self.list_rows = {}, []
        for T, cat, rows in pages:
            self.t_list_rows.setdefault((T, cat), []).extend(rows)
            self.list_rows += rows
        self.t_seed_records = {}
        self.t_sources = sources or {}
        self.links = {frozenset(policy.pn_key(ns, y) for y in x) for x in links}

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b or frozenset((a, b)) in self.links


T15 = ("Infiniti", "QX60", 2015)
qx_page = [lr("96301-3JA9A", [F + "W. BASE"]), lr("96301-3JA9B", [F + "*W. PREMIUM"]),
           lr("96301-3JA9C", [F + "W. PREMIUM"]), lr("96301-3JN9B", [F + "*W. AWD. BASE, *W. AWD. PREMIUM"]),
           lr("96301-3JN9C", [F + "*W. AWD. BASE"]),
           lr("96302-3JA9B", [F + "*W. PREMIUM"], main="Mirror Assy-Outside, LH", loc=("Driver Side",))]
cq = _Cur("nissan", [(T15, "side-mirrors", qx_page)])
check("decision 1: 3JA9B '*W. PREMIUM' beside 3JN9B '*W. AWD. PREMIUM' on the 2015 QX60 page -> 2WD only",
      cq.drive_sibling_limit(_K("96301-3JA9B"), "side-mirrors", T15) == ("drive", frozenset({"2wd"})))
# round5-1119 (hub decision 3) reverted round 4's "starred or not": an asterisk alone is no split
check("decision 1 (round 5): 3JA9A 'W. BASE' beside '*W. AWD. BASE' (another mark) -> no limit",
      cq.drive_sibling_limit(_K("96301-3JA9A"), "side-mirrors", T15) is None)
check("decision 1: the other side's mirror is another part (LH vs RH): the RH AWD numbers do not limit the LH one",
      cq.drive_sibling_limit(_K("96302-3JA9B"), "side-mirrors", T15) is None)
check("decision 1: an AWD number itself is not limited by the rule (its clause names the drive)",
      cq.drive_sibling_limit(_K("96301-3JN9B"), "side-mirrors", T15) is None)
# a sibling that lists the bare clause too, or the clause for both families: no split
T05 = ("Nissan", "Titan", 2005)
ti = [lr("24810-7S00E", [F + "*KC. (SE+ LE) + *CC. (SE+ LE)"], main="Combination Meter Assy-Instrument", loc=(), seed=T05, site=NPD,
         cat="gauge-cluster"),
      lr("24810-7S005", [F + "*KC. (SE+ LE) + *CC. (SE+ LE), *KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE)"],
         main="Combination Meter Assy-Instrument", loc=(), seed=T05, site=NPD, cat="gauge-cluster"),
      lr("24810-7S002", [F + "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE), KC. 4WD. (SE+ LE) + CC. 4WD. (SE+ LE)"],
         main="Combination Meter Assy-Instrument", loc=(), seed=T05, site=NPD, cat="gauge-cluster")]
ct = _Cur("nissan", [(T05, "gauge-cluster", ti)])
check("decision 1: a sibling that also lists the bare clause (7S005) or lists it for both drives (7S002) is no split",
      ct.drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05) is None)
ct2 = _Cur("nissan", [(T05, "gauge-cluster", ti[:1] + [lr("24810-7S006", [F + "KC. 2WD. (SE+ LE) + CC. 2WD. (SE+ LE)"],
                                                          main="Combination Meter Assy-Instrument", loc=(), seed=T05, site=NPD,
                                                          cat="gauge-cluster")])])
check("decision 1 (round 5): an unstarred 2WD sibling (7S006) does not split the starred 7S00E clause",
      ct2.drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05) is None)
check("decision 1: a sibling linked to the number by supersession is no split",
      _Cur("nissan", [(T15, "side-mirrors", qx_page)], links=[("96301-3JA9B", "96301-3JN9B")])
      .drive_sibling_limit(_K("96301-3JA9B"), "side-mirrors", T15) is None)
T13 = ("Infiniti", "JX35", 2013)
jx = [lr("24810-3JA1B", [F + "*W. PREMIUM"], main="Combination Meter Assy-Instrument", loc=(), seed=T13, cat="gauge-cluster"),
      lr("24810-9NA1B", ["Production Date: 06/2013-09/2014", F + "*W. FWD. PREMIUM"], main="Combination Meter Assy-Instrument",
         loc=(), seed=T13, cat="gauge-cluster")]
check("decision 1: a sibling not listed for T itself (06/2013-09/2014: one month of MY2013) is no split",
      _Cur("nissan", [(T13, "gauge-cluster", jx)]).drive_sibling_limit(_K("24810-3JA1B"), "gauge-cluster", T13) is None)
TP = ("Nissan", "Pathfinder", 2005)
pf = [lr("A1", [F + "W. SE"], seed=TP, site=NPD), lr("A2", [F + "W. 4WD. SE"], seed=TP, site=NPD),
      lr("A3", [F + "W. AUTO. LE"], seed=TP, site=NPD)]
check("decision 1: excluding 4WD where the page also names AUTO leaves both families -> drive_not 4wd",
      _Cur("nissan", [(TP, "side-mirrors", pf)]).drive_sibling_limit(_K("A1"), "side-mirrors", TP) == ("drive_not", frozenset({"4wd"})))

# ------------------------------------------------------------ build windows
P10 = ("Nissan", "Pathfinder", 2010)
CM = "Controller Assy-Air Conditioner"
pp = [lr("27510-EA00A", ["Production Date: 08/2009-01/2010"], main=CM, loc=(), seed=P10, site=NPD, repl="27510-9CA0A", cat="climate-control"),
      lr("27510-9BH0A", ["Production Date: from 01/2010"], main=CM, loc=(), seed=P10, site=NPD, repl="27510-9CA0A", cat="climate-control"),
      lr("27510-EA000", ["Production Date: 07/2008-08/2009"], main=CM, loc=(), seed=P10, site=NPD, repl="27510-9CA0A", cat="climate-control")]
w = _Cur("nissan", [(P10, "climate-control", pp)]).build_window(_K("27510-EA00A"), "climate-control", P10)
check("decision 2: EA00A 08/2009-01/2010, the rest carried by 9BH0A (only a common successor): unlinked, the window named",
      w["kind"] == "unlinked" and w["src"] == "page" and C._win_label(w["wins"]) == "built 08/2009-01/2010"
      and C._win_gate(w["wins"]) == "2009-08..2010-01" and not w["edge"])
wl = _Cur("nissan", [(P10, "climate-control", pp)], links=[("27510-EA00A", "27510-9BH0A"), ("27510-EA00A", "27510-EA000")]) \
    .build_window(_K("27510-EA00A"), "climate-control", P10)
check("decision 2: the rest carried by the number's own predecessor / successor: kind linked (gated since round 5)",
      wl["kind"] == "linked")
wn = _Cur("nissan", [(P10, "climate-control", pp[:1])]).build_window(_K("27510-EA00A"), "climate-control", P10)
check("decision 2: no dated row carries the rest: no_other_row, unchanged", wn["kind"] == "no_other_row")
pe = [lr("X1", ["Production Date: 08/2009-08/2010"], main=CM, loc=(), seed=P10, site=NPD, cat="climate-control"),
      lr("X2", ["Production Date: 07/2008-08/2009"], main=CM, loc=(), seed=P10, site=NPD, cat="climate-control")]
we = _Cur("nissan", [(P10, "climate-control", pe)]).build_window(_K("X1"), "climate-control", P10)
check("decision 2: a one-month gap at the model-year edge is still a window (edge counted)", we["kind"] == "unlinked" and we["edge"])
I12 = ("Lexus", "IS 350", 2012)
pc = [lr("C1", ["WHITE PEARL", "Production Date: 11/2011-04/2013"], main="Mirror", loc=(), seed=I12, site=NPD),
      lr("C2", ["BLACK", "Production Date: 08/2010-10/2011"], main="Mirror", loc=(), seed=I12, site=NPD),
      lr("C3", ["WHITE PEARL", "Production Date: 08/2010-10/2011"], main="Mirror", loc=(), seed=I12, site=NPD)]
check("decision 2: another configuration (another colour) does not carry the rest of the year; the same colour does",
      _Cur("nissan", [(I12, "side-mirrors", pc[:2])]).build_window(_K("C1"), "side-mirrors", I12)["kind"] == "no_other_row"
      and _Cur("nissan", [(I12, "side-mirrors", pc)]).build_window(_K("C1"), "side-mirrors", I12)["kind"] == "unlinked")
# decision 3: no date on T's page, a window for the same clause on another model-year page of the model
X01, X02 = ("Nissan", "Xterra", 2001), ("Nissan", "Xterra", 2002)
MT = "Combination Meter Assy-Instrument"
p01 = [lr("24810-7Z803", [F + "W. (VG33E + VG33ER). XE"], main=MT, loc=(), seed=X01, site=NPD, cat="gauge-cluster")]
p02 = [lr("24810-7Z803", ["Production Date: 07/2001-04/2002", F + "W. (VG33E + VG33ER). XE"], main=MT, loc=(), seed=X02, site=NPD,
          cat="gauge-cluster")]
c3 = _Cur("nissan", [(X01, "gauge-cluster", p01), (X02, "gauge-cluster", p02)])
w3 = c3.build_window(_K("24810-7Z803"), "gauge-cluster", X01)
check("decision 3: 7Z803 undated on the 2001 Xterra page, 07/2001-04/2002 on the 2002 page: the narrower reading leaves 2001 out",
      w3["src"] == "other_page" and w3["kind"] == "drop")
p02b = [lr("24810-7Z803", ["Production Date: 07/2001-04/2002", F + "W. XE. AT"], main=MT, loc=(), seed=X02, site=NPD, cat="gauge-cluster")]
check("decision 3 (round 5: matched on the number): the other page's window narrows whatever its clause",
      _Cur("nissan", [(X01, "gauge-cluster", p01), (X02, "gauge-cluster", p02b)]).build_window(_K("24810-7Z803"), "gauge-cluster", X01)["kind"]
      == "drop")
p01l = p01 + [lr("24810-7Z800", [F + "W. (VG33E + VG33ER). XE"], main=MT, loc=(), seed=X01, site=NPD, repl="24810-7Z803", cat="gauge-cluster")]
check("decision 3 (round 5): a predecessor on T's page no longer exempts the undated listing",
      _Cur("nissan", [(X01, "gauge-cluster", p01l), (X02, "gauge-cluster", p02)], links=[("24810-7Z800", "24810-7Z803")])
      .build_window(_K("24810-7Z803"), "gauge-cluster", X01)["kind"] == "drop")

# ------------------------------------------------------------ gate vocabulary, live_diff
check("gate built: ranges, open ends, runs; malformed refused",
      V.gate_problem({"built": "2009-08..2010-01"}) is None and V.gate_problem({"built": "2010-01.."}) is None
      and V.gate_problem({"built": "..2005-12"}) is None and V.gate_problem({"built": "2009-08..2010-01,2010-06.."}) is None
      and V.gate_problem({"built": ".."}) and V.gate_problem({"built": "2010-13.."}) and V.gate_problem({"built": "2011-01..2010-01"})
      and V.gate_problem({"built": ""}) and V.gate_problem({"built": ["2009-08..2010-01"]}))
check("gate drive_not alone: classes of one family", V.gate_problem({"drive_not": "4wd"}) is None
      and V.gate_problem({"drive_not": "4wd/2wd"}) and V.gate_problem({"drive_not": "x"}))
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("live_diff", OEM / "audit11_4" / "live_diff.py")
LD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LD)
check("live_diff: a built window or a lone drive_not added to an app-year narrows; dropping one widens",
      LD.gate_cmp(None, {"built": "2009-08..2010-01"}) == "narrowed"
      and LD.gate_cmp({"eng": ["4.0L"]}, {"eng": ["4.0L"], "built": "2009-08..2010-01"}) == "narrowed"
      and LD.gate_cmp(None, {"drive_not": "4wd"}) == "narrowed"
      and LD.gate_cmp({"built": "2009-08..2010-01"}, None) == "widened")

# ------------------------------------------------------------ committed files
docs = {p.stem: json.loads(p.read_text()) for p in sorted((OEM / "groups").glob("*.json"))}
docs["nissan"] = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
bad = []
for ns, d in docs.items():
    for g in d.get("likely") or []:
        for mk, md, lo, hi, gate in g.get("gates") or []:
            if "built" not in gate:
                continue
            if V.gate_problem(gate):
                bad.append((ns, g["id"], "vocabulary"))
            label = C._win_label([(int(a[:4]) * 12 + int(a[5:]) if a else 0,
                                   int(b[:4]) * 12 + int(b[5:]) if b else C._WIN_OPEN)
                                  for a, b in (r.split("..") for r in gate["built"].split(","))])
            # the model is named unless every vehicle-year of the group shares the label
            # (_limit_note: "built 08/2005-08/2006 only")
            if label not in g["note"] or (md not in g["note"] and f"; {label} only" not in g["note"]):
                bad.append((ns, g["id"], md, label))
        if len(g["note"]) > 160:
            bad.append((ns, g["id"], "note over 160"))
check("committed: every built gate is well formed and its group's note names the window and the model", not bad, bad[:5])
cand = {(g["cat"], tuple(g["pn"])): g for g in docs["nissan"]["likely"]}


def gate_of(g, mk, md, y):
    for x in g.get("gates") or []:
        if (x[0], x[1]) == (mk, md) and x[2] <= y <= x[3]:
            return x[4]
    return {}


def has_year(g, md, y):
    return any(a[1] == md and a[2] <= y <= a[3] for a in g["apps"])


ok = True
for pn in ("96301-3JA9B", "96302-3JA9B"):
    g = cand.get(("side-mirrors", (pn,)))
    if g:
        ok = ok and all(not has_year(g, "QX60", y) or gate_of(g, "Infiniti", "QX60", y).get("drive") == "2wd" for y in (2015, 2016, 2017))
check("candidate: 3JA9B (both sides) never offers QX60 2015-2017 without a 2WD gate (1119d WRONG)", ok)
g = cand.get(("gauge-cluster", ("24820-3ZD0A",)))
check("candidate: 24820-3ZD0A QX56 2013 carries the 2WD gate and its build window (1119d WRONG)",
      g is None or (gate_of(g, "Infiniti", "QX56", 2013).get("drive") == "2wd" and gate_of(g, "Infiniti", "QX56", 2013).get("built")))
g = cand.get(("climate-control", ("27510-EA00A",)))
check("candidate: 27510-EA00A Pathfinder 2010 named built 08/2009-01/2010 (1119d RISK)",
      g is None or (gate_of(g, "Nissan", "Pathfinder", 2010).get("built") == "2009-08..2010-01" and "built 08/2009-01/2010" in g["note"]))
g = cand.get(("gauge-cluster", ("24810-7Z803",)))
check("candidate: 24810-7Z803 claims no 2001 Xterra/Frontier (pages disagree, 1119d RISK)",
      g is None or not (has_year(g, "Xterra", 2001) or has_year(g, "Frontier", 2001)))
done("test_round4_1119")
