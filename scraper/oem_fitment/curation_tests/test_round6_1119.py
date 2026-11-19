#!/usr/bin/env python3
"""Round 6 (interchange 2026-11-19, branch interchange/round6-1119): the hub's
decisions after the sixth independent nissan check
(groups/_report/nissan_verify_2026-11-19f.json, on branch
interchange/verify-nissan-1119f): 2 WRONG, both a cab gate the part's own row
does not carry.

1. A cab gate is stated only when the number's own row for the vehicle-year
   carries the cab; an inferred one holds the vehicle-year (held_cab_inferred).
2. A claim resting only on starred clauses is held (held_starred_only).
3. A gas-only gate also rules out the hybrid's displacement (eng_not).
4. Every build window cutting the model-year span is gated, or its
   vehicle-year leaves at the note cap.
5. Option text tying the part to a transmission the gates do not enforce holds
   the vehicle-year (held_option_tie).
6. Other pages that date the number differently are read narrowly.
Claims only go down: a round-5b reading of the windows runs beside the new one."""
import json
import re

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"
IPD = "www.infinitipartsdeal.com"


def lr(pn, notes, main="Regulator Assy-Door Window", loc=("Passenger Side",), seed=("Nissan", "Titan", 2005),
       cat="window-regulator", site=NPD, url=None):
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=url or f"https://x/{seed[1]}-{seed[2]}/{cat}.html", pn=pn,
                     section="diagram", main=main, aux="", notes=list(notes), locations=list(loc), replace=None,
                     matched=True, excluded_by=None, product=None, retrieved="", line=1, status=200)


class _K:
    def __init__(self, pn):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), [], {pn}


class _Cur:
    for _m in ("cab_stated", "_own_list_or_seed", "option_tie", "_t_drive_systems", "hybrid_only_disps",
               "_pn_other_windows", "_pn_list_rows"):
        locals()[_m] = getattr(C.Curation, _m)
    _tie_cfgs = staticmethod(C.Curation._tie_cfgs)
    _same_part = staticmethod(C.Curation._same_part)
    _CAB_RE, _NISSAN_CAB3 = C.Curation._CAB_RE, C.Curation._NISSAN_CAB3

    def __init__(self, T, cat, rows, trans=("manual", "auto")):
        self.ns = "nissan"
        self.t_list_rows, self.t_seed_records, self.t_rows = {(T, cat): rows}, {}, {}
        self.list_rows = list(rows)
        self._trans = frozenset(trans)

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b

    def _t_trans_seen(self, T):
        return self._trans


# ------------------------------------------------------------ decision 1: cab basis
T05 = ("Nissan", "Titan", 2005)
R = lr("82720-7S000", ["Production Date: 10/2003-12/2005", "Replaced By: 82720-ZV50A"])
cur = _Cur(T05, "window-regulator", [R, lr("82300-8S500", [F + "CC"], main="Glass-Door Window")])
check("decision 1: 82720-7S000's own row carries no cab: a 'crew cab' gate is not stated (the 1119f WRONG)",
      not cur.cab_stated(_K("82720-7S000"), "window-regulator", T05, "crew cab"))
cur = _Cur(T05, "window-regulator", [lr("80721-2Z700", [F + "CC. SE + CC. XE"])])
check("decision 1: an own row coding CC states 'crew cab'",
      cur.cab_stated(_K("80721-2Z700"), "window-regulator", T05, "crew cab"))
cur = _Cur(T05, "window-regulator", [lr("80721-2Z700", [F + "KC. SE + CC. XE"])])
check("decision 1: an own row coding KC and CC does not state 'crew cab' only (but states the list)",
      not cur.cab_stated(_K("80721-2Z700"), "window-regulator", T05, "crew cab")
      and cur.cab_stated(_K("80721-2Z700"), "window-regulator", T05, ["king cab", "crew cab"]))

# ------------------------------------------------------------ decision 5: transmission ties
X13 = ("Nissan", "Xterra", 2013)
EA = lr("96302-EA000", [F + "W. 2WD + W. S. 6MT"], main="Mirror Assy-Outside, LH", loc=("Driver side",), seed=X13,
        cat="side-mirrors")
EA5 = lr("96302-EA005", [F + "W. 4WD. X + W. S. 5AT + W. PRO-4X"], main="Mirror Assy-Outside, LH",
         loc=("Driver side",), seed=X13, cat="side-mirrors")
tie = _Cur(X13, "side-mirrors", [EA, EA5]).option_tie(_K("96302-EA000"), "side-mirrors", X13, {})
check("decision 5: Xterra 2013 96302-EA000 'W. 2WD + W. S. 6MT' leaves the 4WD automatic out: held, via own",
      tie and tie["uncovered"] == [("4", "auto")] and tie["via"] == "own" and tie["fit"] is None, tie)
EA07 = lr("96302-EA000", [F + "W. 2WD. S + W. 4WD. S. 6MT + W. BASECAMP"], main="Mirror Assy-Outside, LH",
          loc=("Driver side",), seed=X13, cat="side-mirrors")
check("decision 5: a configuration naming no drive or transmission (W. BASECAMP) covers every pair: no tie",
      _Cur(X13, "side-mirrors", [EA07, EA5]).option_tie(_K("96302-EA000"), "side-mirrors", X13, {}) is None)
check("decision 5: a model-year whose pages show one transmission has no tie",
      _Cur(X13, "side-mirrors", [EA, EA5], trans=("auto",)).option_tie(_K("96302-EA000"), "side-mirrors", X13, {})
      is None)
G08 = ("Infiniti", "G37", 2008)
JD = lr("24820-JK61D", [F + "S. 2WD. (JOURNEY+ PREMIUM) + S. 2WD. (SPORT+ SPORT/P). 5AT + S. AWD + S. LEATHER"],
        main="Speedometer Assy", loc=(), seed=G08, cat="gauge-cluster", site=IPD)
JB = lr("24820-JK61B", ["Production Date: 08/2007-08/2008", F + "S. 6MT"], main="Speedometer Assy", loc=(), seed=G08,
        cat="gauge-cluster", site=IPD)
tie = _Cur(G08, "gauge-cluster", [JD, JB]).option_tie(_K("24820-JK61D"), "gauge-cluster", G08, {})
check("decision 5: JK61D beside JK61B 'S. 6MT' (every 6MT sedan): the manuals take JK61B, held via sibling, "
      "a trans AT gate would fit",
      tie and tie["via"] == "sibling" and {t for _f, t in tie["uncovered"]} == {"manual"}
      and tie["fit"] == {"drive": None, "trans": ["auto"]}, tie)
check("decision 5: the same with a trans AT gate is enforced (no hold)",
      _Cur(G08, "gauge-cluster", [JD, JB]).option_tie(_K("24820-JK61D"), "gauge-cluster", G08, {"trans": "AT"}) is None)
check("decision 5: a sibling that also lists one of our configurations bare is an alternative, not a split",
      _Cur(G08, "gauge-cluster", [JD, lr("24820-JK61B", [F + "S. 6MT, S"], main="Speedometer Assy", loc=(), seed=G08,
                                          cat="gauge-cluster", site=IPD)]).option_tie(
          _K("24820-JK61D"), "gauge-cluster", G08, {}) is None)

# ------------------------------------------------------------ decision 6: pages that disagree
check("decision 6: two windows intersect to the months both list", C._win_intersect(
    [(2004 * 12 + 12, 2008 * 12 + 6)], [(2007 * 12 + 9, 2008 * 12 + 6)]) == [(2007 * 12 + 9, 2008 * 12 + 6)])
M06 = ("Infiniti", "M35", 2006)
p8 = lr("80720-EH100", ["Production Date: 12/2004-06/2008"], seed=("Infiniti", "M35", 2008), site=IPD)
p9 = lr("80720-EH100", ["Production Date: 09/2007-06/2008"], seed=("Infiniti", "M35", 2009), site=IPD)
cur = _Cur(M06, "window-regulator", [p8, p9])
check("decision 6: 80720-EH100 dated 12/2004-06/2008 on the 2008 page and 09/2007-06/2008 on the 2009 page reads "
      "09/2007-06/2008", cur._pn_other_windows(policy.pn_key("nissan", "80720-EH100"), "window-regulator", M06,
                                               {IPD}, {("Infiniti", "M35")}) == [(2007 * 12 + 9, 2008 * 12 + 6)])
cur._r6_narrow = False
check("decision 6: the round-5b reading (beside it, for the only-narrows guard) is the union",
      cur._pn_other_windows(policy.pn_key("nissan", "80720-EH100"), "window-regulator", M06, {IPD},
                            {("Infiniti", "M35")}) == [(2004 * 12 + 12, 2008 * 12 + 6)])
check("decision 4: no_other_row windows are gated now", "no_other_row" in C.ROUND6_WINDOW_KINDS)

# ------------------------------------------------------------ decision 3: the hybrid's displacement
h = _Cur(("Infiniti", "QX60", 2016), "window-regulator", [])
h._t_fit_engines = lambda T: (frozenset({2.5, 3.5}), frozenset(), frozenset({2.5, 3.5}), frozenset(), True)
h._t_engines = lambda T, cat, gas_only=False: {3.5}
check("decision 3: QX60 (gas 3.5L, year page offers a hybrid, 2.5L attested): eng_not 2.5L",
      h.hybrid_only_disps(("Infiniti", "QX60", 2016)) == [2.5])
h._t_fit_engines = lambda T: (frozenset({2.5, 3.5}), frozenset(), frozenset({2.5, 3.5}), frozenset(), False)
check("decision 3: no hybrid catalog on the year page: nothing", h.hybrid_only_disps(("Infiniti", "QX60", 2016)) == [])
check("decisions 2 and 3 are nissan only; policy.py carries none of round 6",
      C.HYBRID_ENG_NOT_NS == frozenset({"nissan"}) and C.STARRED_SCOPE_NS == frozenset({"nissan"})
      and "ROUND6" not in (OEM / "policy.py").read_text())

# ------------------------------------------------------------ committed files
cand = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
by = {(g["cat"], g["pn"][0]): g for g in cand["likely"]}


def claim(cat, pn, mk, md, y):
    g = by.get((cat, pn))
    if not g or not any(a[0] == mk and a[1] == md and a[2] <= y <= a[3] for a in g["apps"]):
        return None
    return next((x[4] for x in g.get("gates") or [] if (x[0], x[1]) == (mk, md) and x[2] <= y <= x[3]), {})


bad = [(pn, y) for pn, ys in (("82720-7S000", (2005,)), ("82721-7S000", (2005,)), ("82730-7S000", (2010, 2011)),
                              ("82731-7S000", (2010, 2011)), ("82730-9FJ0A", (2012,)), ("82731-9FJ0A", (2012,)))
       for y in ys if (claim("window-regulator", pn, "Nissan", "Titan", y) or {}).get("cab")]
check("candidate: no 1119f cab-without-basis vehicle-year keeps its cab gate (6 groups, 8 vehicle-years)", not bad, bad)
cabs = [(g["pn"][0], x[1], x[2]) for g in cand["likely"] for x in g.get("gates") or [] if x[4].get("cab")
        and re.search(r"rear", g["cat"] + json.dumps(g.get("note")), re.I) and g["cat"] == "window-regulator"
        and set(g["id"].split(":")[3].split("+")) <= {"RL", "RR"}]
check("candidate: no rear-door regulator keeps a cab gate (rear_cab_of is never a basis)", not cabs, cabs[:3])
qx = [(g["pn"][0], x[2]) for g in cand["likely"] for x in g.get("gates") or []
      if x[1] in ("QX60", "JX35") and x[4].get("fuel") == "gas" and "2.5L" not in (x[4].get("eng_not") or [])]
check("candidate: every QX60 / JX gas-only gate rules out 2.5L (decision 3)", not qx, qx[:3])
check("candidate: Xterra 2013 not claimed on 96301/96302-EA000; JK61D claims no G35/G37 2008 (decision 5)",
      all(claim("side-mirrors", pn, "Nissan", "Xterra", 2013) is None for pn in ("96301-EA000", "96302-EA000"))
      and all(claim("gauge-cluster", "24820-JK61D", "Infiniti", md, 2008) is None for md in ("G35", "G37")))
check("candidate: claims resting only on '*' are gone (80730-7B400 Frontier 1999-2000, 96301-3EV0B QX70 2016-2017, "
      "24820-JK61C)", all(claim("window-regulator", "80730-7B400", "Nissan", "Frontier", y) is None for y in (1999, 2000))
      and all(claim("side-mirrors", "96301-3EV0B", "Infiniti", "QX70", y) is None for y in (2016, 2017))
      and ("gauge-cluster", "24820-JK61C") not in by)
a05 = claim("side-mirrors", "96302-7S600", "Nissan", "Armada", 2005)
q14 = claim("gauge-cluster", "24820-1MA5A", "Infiniti", "Q70", 2014)
check("candidate: Q70 2014 24820-1MA5A gated built 01/2013-11/2013; Armada 2005 96302-7S600 gated from 10/2004 "
      "(decision 4); or, since round 7 (M37 2013 / Titan 2006 gated too, the note over the cap), not claimed",
      (q14 is None or q14.get("built") == "2013-01..2013-11") and (a05 is None or a05.get("built", "").startswith("2004-10")))
r6 = json.loads((OEM / "groups" / "_report" / "nissan.round6_held.json").read_text())
check("held list (round 6): reasons are cab_inferred / option_tie, each with the own rows; ties name what is uncovered",
      all(set(h["reasons"]) <= {"held_cab_inferred", "held_option_tie"} and h["own_rows"] is not None
          and ("held_option_tie" not in h["reasons"] or h["tie"]["uncovered"]) for e in r6["held"] for h in e["held"]))
sh = json.loads((OEM / "groups" / "_report" / "nissan.starred_held.json").read_text())
check("held list (starred): starred_only is a kind of its own", sh["vehicle_years_by_kind"].get("starred_only", 0) > 0)
ld = (OEM / "groups" / "_report" / "live_diff_2026-11-19_round6.txt").read_text()
summ = re.findall(r"^# (\w+) LIVE: removed (\d+) groups, added (\d+) groups.*?gained (\d+);.*?widened (\d+); "
                  r"added claims (\d+)$", ld, re.M)
check("live diff vs origin/main: 9 namespaces, 0 added groups, 0 gained app-years, 0 widened gates",
      len(summ) == 9 and all(a == g == w == ac == "0" for _ns, _r, a, g, w, ac in summ), summ)
pay = json.loads((OEM.parent.parent / "docs" / "data" / "interchange.json").read_text())
# round 9 E: nissan ships (in oemGroups2, junkyard_scraper.OEM_NEW_FIELD_NS)
check("payload: oemStatus ok for the 8 shipped namespaces and nissan",
      sorted(pay["oemStatus"]) == ["ford", "gm", "hmg", "mb", "mopar", "nissan", "subaru", "toyota", "vag"]
      and all(v.startswith("ok ") for v in pay["oemStatus"].values()), pay["oemStatus"])
done("test_round6_1119")
