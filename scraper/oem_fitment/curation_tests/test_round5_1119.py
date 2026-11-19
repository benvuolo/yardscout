#!/usr/bin/env python3
"""Round 5 rules (interchange 2026-11-19, branch interchange/round5-1119): the
hub's decisions after the independent nissan check
groups/_report/nissan_verify_2026-11-19e.json (7 WRONG, all one flaw: a
model year split between the claimed number and its own predecessor or
successor shown plain).

1. Linked windows are windows: "Replaced By" runs one way, so a vehicle-year
   whose rest is carried by the number's predecessor or successor keeps the
   claim only with the window named and a "built" gate.
2. Windows from other model-year pages match on the number, not the option
   clause (Sentra 2004 82730-3Z005); a predecessor on T's page no longer
   exempts the undated listing.
3. An asterisk alone is no drive split (Titan 2005 7S00E / 7S006).
4. A sibling-derived drive gate has basis "sibling" (with drive_sib), never
   "stated"."""
import json

from _util import OEM, check, done
import adapters as A
import curate as C
import policy
import validate as V

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"


def lr(pn, notes, main="Combination Meter Assy-Instrument", loc=(), seed=("Nissan", "Titan", 2005), cat="gauge-cluster",
       repl=None):
    return A.ListRow(site=NPD, seed=seed, cat=cat, list_url=f"https://x/{seed[1]}-{seed[2]}/{cat}.html", pn=pn,
                     section="diagram", main=main, aux="", notes=list(notes), locations=list(loc), replace=repl,
                     matched=True, excluded_by=None, product=None, retrieved="", line=1, status=200)


class _K:
    def __init__(self, pn):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), [], {pn}


class _Cur:
    drive_sibling = C.Curation.drive_sibling
    drive_sibling_limit = C.Curation.drive_sibling_limit
    _same_part = staticmethod(C.Curation._same_part)
    _t_drive_systems = C.Curation._t_drive_systems
    build_window = C.Curation.build_window
    _pn_list_rows = C.Curation._pn_list_rows
    _pn_other_windows = C.Curation._pn_other_windows
    _r7 = False     # the round-4/5 reading these checks pin (round 7: test_round7_1119.py)

    def __init__(self, pages, links=()):
        self.ns = "nissan"
        self.t_list_rows, self.list_rows = {}, []
        for T, cat, rows in pages:
            self.t_list_rows.setdefault((T, cat), []).extend(rows)
            self.list_rows += rows
        self.t_seed_records, self.t_sources = {}, {}
        self.links = {frozenset(policy.pn_key("nissan", y) for y in x) for x in links}

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b or frozenset((a, b)) in self.links


# ------------------------------------------------------------ decision 3: the "*" mark
check("clauses carry the '*' mark per configuration",
      [st for *_x, st in C._row_clauses_star([F + "*KC. (SE+ LE) + CC. SE, W"], NPD)] == [True, False, False])
T05 = ("Nissan", "Titan", 2005)
E = lr("24810-7S00E", ["Production Date: 10/2004-08/2006", F + "*KC. (SE+ LE) + *CC. (SE+ LE)"])
S006 = lr("24810-7S006", [F + "KC. 2WD. (SE+ LE) + CC. 2WD. (SE+ LE)"])
S002 = lr("24810-7S002", [F + "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE), KC. 4WD. (SE+ LE) + CC. 4WD. (SE+ LE)"])
S007 = lr("24810-7S007", [F + "*KC. 2WD. (SE+ LE) + *CC. 2WD. (SE+ LE)"])
check("decision 3: a starred / unstarred difference alone makes no drive gate (7S00E '*KC' vs 7S006 'KC. 2WD')",
      _Cur([(T05, "gauge-cluster", [E, S006])]).drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05) is None)
check("decision 3: a sibling listing the clause for 2WD under one mark and 4WD under the other (7S002) is no split",
      _Cur([(T05, "gauge-cluster", [E, S002])]).drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05) is None)
check("decision 3: the same mark and a drive word (7S007 '*KC. 2WD. (SE+ LE)') is still a split (4WD family left)",
      (_Cur([(T05, "gauge-cluster", [E, S007])]).drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05) or ("", ()))[0] == "drive"
      and set(_Cur([(T05, "gauge-cluster", [E, S007])]).drive_sibling_limit(_K("24810-7S00E"), "gauge-cluster", T05)[1]) <= C._FOUR)

# ------------------------------------------------------------ decision 1: linked windows are windows
S95 = ("Nissan", "Stanza", 1995)
MR = "Door Mirror Assy-RH"
st = [lr("96301-1E400", ["BLACK", "Production Date: 06/1992-02/1995", F + "FED. S. (XE+ GXE+ SE)"], main=MR, loc=("Passenger Side",),
         seed=S95, cat="side-mirrors", repl="96301-2B500"),
      lr("96301-2B500", ["BLACK", "Production Date: from 02/1995", F + "FED. S. (XE+ GXE+ SE)"], main=MR, loc=("Passenger Side",),
         seed=S95, cat="side-mirrors")]
w = _Cur([(S95, "side-mirrors", st)], links=[("96301-1E400", "96301-2B500")]).build_window(_K("96301-2B500"), "side-mirrors", S95)
check("decision 1: Stanza 1995 2B500 from 02/1995, the rest under its own predecessor 1E400: a linked window, named",
      w["kind"] == "linked" and C._win_label(w["wins"]) == "built from 02/1995" and C._win_gate(w["wins"]) == "1995-02..")
# decision 2: number-matched other-page windows (Sentra 2004 82730-3Z005)
S04, S05 = ("Nissan", "Sentra", 2004), ("Nissan", "Sentra", 2005)
RM = "Motor Assy-Regulator, RH"
p04 = [lr("82730-3Z005", [F + "4S. (GXE + XE)"], main=RM, seed=S04, cat="window-regulator")]
p05 = [lr("82730-3Z005", ["Production Date: from 04/2004"], main=RM, seed=S05, cat="window-regulator")]
w2 = _Cur([(S04, "window-regulator", p04), (S05, "window-regulator", p05)]).build_window(_K("82730-3Z005"), "window-regulator", S04)
check("decision 2: Sentra 2004 undated with a clause, the 2005 page dates the number from 04/2004 with none: read, under 5 months -> out",
      w2["src"] == "other_page" and w2["kind"] == "drop")

Q15, Q16 = ("Infiniti", "Q70", 2015), ("Infiniti", "Q70", 2016)
RG = "Regulator Assy-Door Window, RH"
q15 = [lr("80720-1MA0A", [F + "SEDAN, SEDAN + LSEDAN"], main=RG, loc=("Passenger Side",), seed=Q15, cat="window-regulator",
          repl="80720-1MA0B"),
       lr("80720-1MA0B", [F + "SEDAN + LSEDAN"], main=RG, loc=("Passenger Side",), seed=Q15, cat="window-regulator")]
q16 = [lr("80720-1MA0A", ["Production Date: 07/2014-02/2015"], main=RG, loc=("Passenger Side",), seed=Q16, cat="window-regulator",
          repl="80720-1MA0B"),
       lr("80720-1MA0B", ["Production Date: 02/2015-02/2018"], main=RG, loc=("Passenger Side",), seed=Q16, cat="window-regulator")]
wq = _Cur([(Q15, "window-regulator", q15), (Q16, "window-regulator", q16)], links=[("80720-1MA0A", "80720-1MA0B")]) \
    .build_window(_K("80720-1MA0B"), "window-regulator", Q15)
check("decision 1+2: Q70 2015 1MA0B and its predecessor 1MA0A both undated on the 2015 page, dated on the 2016 page: a linked window",
      wq["src"] == "other_page" and wq["kind"] == "linked" and C._win_gate(wq["wins"]) == "2015-02..2018-02")

# ------------------------------------------------------------ decision 4: gate vocabulary
check("gate: drive_basis 'sibling' with drive_sib of the other family; drive_sib refused elsewhere",
      V.gate_problem({"drive": "2wd", "drive_basis": "sibling", "drive_sib": "awd"}) is None
      and V.gate_problem({"drive": "2wd", "drive_basis": "stated", "drive_sib": "awd"})
      and V.gate_problem({"drive": "2wd", "drive_basis": "sibling", "drive_sib": "fwd"})
      and V.gate_problem({"drive_sib": "awd"}))

# ------------------------------------------------------------ committed files
docs = {p.stem: json.loads(p.read_text()) for p in sorted((OEM / "groups").glob("*.json"))}
docs["nissan"] = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())


def gate_of(g, mk, md, y):
    for x in g.get("gates") or []:
        if (x[0], x[1]) == (mk, md) and x[2] <= y <= x[3]:
            return x[4]
    return {}


def has_year(g, md, y):
    return any(a[1] == md and a[2] <= y <= a[3] for a in g["apps"])


cand = {(g["cat"], tuple(g["pn"])): g for g in docs["nissan"]["likely"]}
sib = [(ns, g["id"]) for ns, d in docs.items() for g in d.get("likely") or [] for x in g.get("gates") or []
       if x[4].get("drive_basis") == "sibling" and not x[4].get("drive_sib")]
check("committed: every sibling-basis drive gate names the sibling's drive (drive_sib)", not sib, sib[:3])
bad = []
for k, md, y in ((("gauge-cluster", ("24820-3ZD0A",)), "QX56", 2013), (("gauge-cluster", ("24820-3ZD1A",)), "QX56", 2013),
                 (("side-mirrors", ("96301-9BC9A",)), "Xterra", 2012), (("side-mirrors", ("96302-9BC9A",)), "Xterra", 2013)):
    g = cand.get(k)
    if g and gate_of(g, "Infiniti" if md == "QX56" else "Nissan", md, y).get("drive") and \
            gate_of(g, "Infiniti" if md == "QX56" else "Nissan", md, y).get("drive_basis") != "sibling":
        bad.append((k, md, y))
check("committed: the 1119e 'stated without a drive word' gates are basis sibling now", not bad, bad)
ok = True
for (cat, pn), md, y in ((("gauge-cluster", "24810-7Z809"), "Xterra", 2002), (("side-mirrors", "K6301-1MA0B"), "M56", 2011),
                         (("window-regulator", "82730-3Z005"), "Altima", 2003), (("window-regulator", "80720-1MA0B"), "Q70", 2015),
                         (("window-regulator", "82731-3Z005"), "Altima", 2003), (("side-mirrors", "96302-ZC20A"), "Armada", 2005),
                         (("window-regulator", "80730-JX30B"), "Cube", 2011)):
    g = cand.get((cat, (pn,)))
    if g and has_year(g, md, y):
        mk = "Infiniti" if md in ("M56", "Q70") else "Nissan"
        ok = ok and bool(gate_of(g, mk, md, y).get("built"))
check("candidate: every 1119e WRONG vehicle-year is gone or carries a built gate (never plain)", ok)
g = cand.get(("window-regulator", ("82730-3Z005",)))
check("candidate: 82730-3Z005 claims no Sentra 2004 (other-page window, under 5 months)", g is None or not has_year(g, "Sentra", 2004))
for pn in ("96301-2B500", "96302-2B500"):
    g = cand.get(("side-mirrors", (pn,)))
    check(f"candidate: {pn} Stanza 1995 is windowed or left out, like Altima 1995",
          g is None or not has_year(g, "Stanza", 1995) or bool(gate_of(g, "Nissan", "Stanza", 1995).get("built")))
done("test_round5_1119")
