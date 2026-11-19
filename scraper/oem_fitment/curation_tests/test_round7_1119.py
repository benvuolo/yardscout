#!/usr/bin/env python3
"""Round 7 (interchange 2026-11-19, branch interchange/round7-1119): the hub's
decisions after the seventh independent nissan check
(groups/_report/nissan_verify_2026-11-19g.json, branch
interchange/verify-nissan-1119g): 1 WRONG, 80730-89915 Versa 2007 plain while
both of its 2007 pages end the number inside the model year.

Cause (confirmed in curate.build_window): the windows of every own row on T's
pages were merged before the cut test. The sedan page's 12/2006-07/2007 and
the hatchback page's 05/2006-01/2007 together cover 07/2006-06/2007.

1. The cut test runs per page; a dated page that cuts the span gates the year
   with the months every dated page lists (pages with none in common: out).
2. A changeover month with a same-option number on T's page inside the span
   (widened a month either way) gates the year on both sides.
3. Undated on T's page beside a same-option number, the split dated on other
   pages (any model of the site): the narrower reading, gated.
4. A number in another door or position on another model: the group is held
   (held_cross_position).
5. The mark alone decides a limit (the star-blind reading): held_starred_scope.
Claims only go down: the round-6 and round-5b readings run beside the new one."""
import json
import re

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"
IPD = "www.infinitipartsdeal.com"


def lr(pn, notes, main="Regulator Assy-Door Window", loc=("Passenger Side",), seed=("Nissan", "Versa", 2007),
       cat="window-regulator", variant="", site=NPD):
    url = f"https://x/{seed[2]}-{seed[1]}{'-' + variant if variant else ''}/{cat}.html"
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=url, pn=pn, section="diagram", main=main, aux="",
                     notes=list(notes), locations=list(loc), replace=None, matched=True, excluded_by=None,
                     product=None, retrieved="", line=1, status=200, variant=variant)


class _K:
    def __init__(self, pn):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), [], {pn}


class _Cur:
    for _m in ("build_window", "_pn_list_rows", "_pn_other_windows", "_same_option_sibs", "_split_windows",
               "_changeover"):
        locals()[_m] = getattr(C.Curation, _m)
    _same_part = staticmethod(C.Curation._same_part)
    _adjacent = staticmethod(C.Curation._adjacent)

    def __init__(self, pages):
        self.ns = "nissan"
        self.t_list_rows, self.list_rows = {}, []
        for T, cat, rows in pages:
            self.t_list_rows.setdefault((T, cat), []).extend(rows)
            self.list_rows += rows
        self.t_seed_records, self.t_sources = {}, {}

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b


def ym(y, m):
    return y * 12 + m


# ------------------------------------------------------------ decision 1: per page
V07 = ("Nissan", "Versa", 2007)
sed = [lr("80730-89915", ["Production Date: 12/2006-07/2007"], variant="sedan"),
       lr("80730-8991A", ["Production Date: 07/2007-06/2011"], variant="sedan")]
hat = [lr("80730-89915", ["Production Date: 05/2006-01/2007"], variant="hatchback"),
       lr("80730-8991A", ["Production Date: 01/2007-06/2011"], variant="hatchback")]
cur = _Cur([(V07, "window-regulator", sed + hat)])
w = cur.build_window(_K("80730-89915"), "window-regulator", V07)
check("decision 1: Versa 2007 sedan 12/2006-07/2007 + hatchback 05/2006-01/2007: gated with the months both list "
      "(12/2006-01/2007), not plain", w and w["kind"] in C.ROUND7_WINDOW_KINDS and w["wins"] == [(ym(2006, 12), ym(2007, 1))]
      and w.get("r7") == "pages", w)
cur._r7 = False
w6 = cur.build_window(_K("80730-89915"), "window-regulator", V07)
check("decision 1, the cause: the round-6 reading merged the two pages and found the year covered (kind full)",
      w6 and w6["kind"] == "full" and w6["wins"] == [(ym(2006, 5), ym(2007, 7))], w6)
dis = [lr("80730-89915", ["Production Date: 01/2007-06/2007"], variant="sedan"),
       lr("80730-89915", ["Production Date: 07/2006-12/2006"], variant="hatchback")]
w = _Cur([(V07, "window-regulator", dis)]).build_window(_K("80730-89915"), "window-regulator", V07)
check("decision 1: pages with no month in common leave the vehicle-year out", w and w["kind"] == "drop", w)
mix = [lr("80730-89915", ["Production Date: 12/2006-07/2007"], variant="sedan"),
       lr("80730-89915", [], variant="hatchback")]
w = _Cur([(V07, "window-regulator", mix)]).build_window(_K("80730-89915"), "window-regulator", V07)
check("decision 1: an undated page beside a dated page that cuts: gated with the dated window (round 6: plain)",
      w and w["kind"] in C.ROUND7_WINDOW_KINDS and w["wins"] == [(ym(2006, 12), ym(2007, 7))], w)

# ------------------------------------------------------------ decision 2: changeover months
FX6 = ("Infiniti", "FX35", 2006)
fx = [lr("80721-CL00A", ["Production Date: 09/2004-06/2006"], loc=("Driver side",), seed=FX6, site=IPD),
      lr("80721-CL70B", ["Production Date: from 06/2006"], loc=("Driver side",), seed=FX6, site=IPD)]
w = _Cur([(FX6, "window-regulator", fx)]).build_window(_K("80721-CL00A"), "window-regulator", FX6)
check("decision 2: FX35 2006 80721-CL00A to 06/2006, CL70B from 06/2006: the changeover is in the span, gated",
      w and w["kind"] == "changeover" and w["changeover"].startswith("06/2006"), w)
G12 = ("Infiniti", "G25", 2012)
g25 = [lr("80730-JK60C", ["Production Date: 06/2011-06/2014"], seed=G12, site=IPD),
       lr("80730-JK60B", ["Production Date: 08/2010-06/2011"], seed=G12, site=IPD)]
w = _Cur([(G12, "window-regulator", g25)]).build_window(_K("80730-JK60C"), "window-regulator", G12)
check("decision 2: G25 2012 JK60C from 06/2011 (a month before the span), JK60B to 06/2011: widened by a month, gated",
      w and w["kind"] == "changeover", w)
T06 = ("Nissan", "Titan", 2006)
t6 = [lr("96302-7S200", ["Production Date: 10/2004-08/2006", F + "KC. SE + CC. SE"], main="Mirror Assy-Outside, LH",
         loc=("Driver side",), seed=T06, cat="side-mirrors"),
      lr("96302-ZH10A", ["Production Date: from 08/2006", F + "KC. SE + CC. SE"], main="Mirror Assy-Outside, LH",
         loc=("Driver side",), seed=T06, cat="side-mirrors")]
w = _Cur([(T06, "side-mirrors", t6)]).build_window(_K("96302-7S200"), "side-mirrors", T06)
check("decision 2: a changeover two months after the span (Titan 2006 7S200 / ZH10A at 08/2006) stays plain "
      "(the widening is one month)", w and w["kind"] == "full", w)
other_colour = [fx[0], lr("80721-CL70B", ["Production Date: from 06/2006", F + "BLACK"], loc=("Driver side",),
                          seed=FX6, site=IPD)]
w = _Cur([(FX6, "window-regulator", [lr("80721-CL00A", ["Production Date: 09/2004-06/2006", F + "SILVER"],
                                        loc=("Driver side",), seed=FX6, site=IPD), other_colour[1]])]).build_window(
    _K("80721-CL00A"), "window-regulator", FX6)
check("decision 2: a number for another option is no changeover", w and w["kind"] == "full", w)

# ------------------------------------------------------------ decision 3: date splits read from other pages
M = "Mirror Assy-Outside, LH"
t6p = [lr("96302-7S600", [F + "KC. LE + CC. LE"], main=M, loc=("Driver side",), seed=T06, cat="side-mirrors"),
       lr("96302-ZC400", [F + "KC. LE + CC. LE"], main=M, loc=("Driver side",), seed=T06, cat="side-mirrors")]
t7p = [lr("96302-7S600", ["Production Date: 10/2004-08/2006", F + "KC. LE + CC. LE"], main=M, loc=("Driver side",),
          seed=("Nissan", "Titan", 2007), cat="side-mirrors"),
       lr("96302-ZC400", [F + "KC. LE + CC. LE"], main=M, loc=("Driver side",), seed=("Nissan", "Titan", 2007),
          cat="side-mirrors")]
t8p = [lr("96302-ZC400", ["Production Date: 08/2006-04/2007", F + "KC. LE + CC. LE"], main=M, loc=("Driver side",),
          seed=("Nissan", "Titan", 2008), cat="side-mirrors")]
cur = _Cur([(T06, "side-mirrors", t6p), (("Nissan", "Titan", 2007), "side-mirrors", t7p),
            (("Nissan", "Titan", 2008), "side-mirrors", t8p)])
w = cur.build_window(_K("96302-7S600"), "side-mirrors", T06)
check("decision 3: Titan 2006 lists 7S600 and ZC400 undated; 7S600 to 08/2006 (2007 page), ZC400 from 08/2006 "
      "(2008 page): the narrower reading, gated 10/2004-08/2006", w and w["kind"] == "split"
      and w["wins"] == [(ym(2004, 10), ym(2006, 8))], w)
cur._r7 = False
w6 = cur.build_window(_K("96302-7S600"), "side-mirrors", T06)
check("decision 3: the round-6 reading kept it plain (the window covers the year)", w6 and w6["kind"] == "full", w6)
F10 = ("Nissan", "Frontier", 2010)
R = "Regulator Assy-Door Window"
fr = [lr("80721-EA000", [F + "CC. (LE + OFFROAD)"], loc=("Driver side",), seed=F10),
      lr("80721-ZL90A", [F + "CC. (LE + OFFROAD)"], loc=("Driver side",), seed=F10)]
pf = [lr("80721-EA000", ["Production Date: 07/2008-04/2010"], loc=("Driver side",), seed=("Nissan", "Pathfinder", 2010)),
      lr("80721-ZL90A", ["Production Date: 04/2010-08/2011"], loc=("Driver side",), seed=("Nissan", "Pathfinder", 2010))]
w = _Cur([(F10, "window-regulator", fr), (("Nissan", "Pathfinder", 2010), "window-regulator", pf)]).build_window(
    _K("80721-EA000"), "window-regulator", F10)
check("decision 3: no Frontier page dates EA000; the Pathfinder page dates the EA000 / ZL90A split: its window is read",
      w and w["wins"] == [(ym(2008, 7), ym(2010, 4))] and w.get("r7") == "split" and w["kind"] != "full", w)
w = _Cur([(F10, "window-regulator", fr[:1]), (("Nissan", "Pathfinder", 2010), "window-regulator", pf)]).build_window(
    _K("80721-EA000"), "window-regulator", F10)
check("decision 3: without the same-option sibling on T's page, another model's page is not read (round 6)", w is None, w)

# ------------------------------------------------------------ decision 5: the mark alone
check("decision 5: the star-blind reading takes every configuration's mark off",
      C._blind_notes([F + "*W. AWD. BASE, W. BASE + *W"], IPD) == [F + "W. AWD. BASE, W. BASE + W"])

# ------------------------------------------------------------ committed files
cand = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
by = {(g["cat"], g["pn"][0]): g for g in cand["likely"]}


def claim(cat, pn, mk, md, y):
    g = by.get((cat, pn))
    if not g or not any(a[0] == mk and a[1] == md and a[2] <= y <= a[3] for a in g["apps"]):
        return None
    return next((x[4] for x in g.get("gates") or [] if (x[0], x[1]) == (mk, md) and x[2] <= y <= x[3]), {})


v = claim("window-regulator", "80730-89915", "Nissan", "Versa", 2007)
check("candidate: Versa 2007 80730-89915 is never plain (the 1119g WRONG)", v is None or bool(v.get("built")), v)
plain = [(pn, md, y) for pn, md, y in (("80721-CL00A", "FX35", 2006), ("80721-CL00A", "FX45", 2006),
                                      ("80730-JK60C", "G25", 2012), ("80721-EH100", "M35", 2008),
                                      ("80721-EH100", "M45", 2008), ("80720-EH100", "M35", 2008))
         if claim("window-regulator", pn, "Infiniti", md, y) == {}]
plain += [(pn, md, 1997) for pn in ("82720-0E717",) for md in ("Altima", "Stanza")
          if claim("window-regulator", pn, "Nissan", md, 1997) == {}]
check("candidate: the 1119g changeover vehicle-years (FX 2006, G25 2012, M 2008, Altima/Stanza 1997) are not plain "
      "(decision 2)", not plain, plain)
sp = [(pn, md, y) for pn, cat, md, y in (("96302-7S600", "side-mirrors", "Titan", 2006),
                                         ("80721-EA000", "window-regulator", "Frontier", 2010),
                                         ("80721-EA000", "window-regulator", "Frontier", 2011),
                                         ("80720-2Z710", "window-regulator", "Xterra", 2002),
                                         ("80720-2Z710", "window-regulator", "Xterra", 2003))
      if claim(cat, pn, "Nissan", md, y) == {}]
check("candidate: the 1119g split vehicle-years (G12 Titan 2006, G24 Frontier 2010-11, G27 Xterra 2002-03) are not "
      "plain (decision 3)", not sp, sp)
r7 = json.loads((OEM / "groups" / "_report" / "nissan.round7_held.json").read_text())
ids = {(e["cat"], e["pn"][0]) for e in r7["held"]}
cross = [("window-regulator", p) for p in ("80730-8991A", "80730-JX30B", "80730-JX30C", "82730-3Z005", "82731-3Z005")]
check("candidate: the 1119g cross-door groups are held (decision 4; 80730-89915 left earlier at the note cap)",
      all(k in ids and k not in by for k in cross) and ("window-regulator", "80730-89915") not in by,
      sorted(set(cross) - ids))
check("held list (round 7): every entry names its models' positions, which differ",
      all(e["reason"] == "held_cross_position" and len({tuple(v) for v in e["positions"].values()}) > 1
          for e in r7["held"]))
check("candidate: 96301/96302-3JA9A held under the starred reason (decision 5)",
      ("side-mirrors", "96301-3JA9A") not in by and ("side-mirrors", "96302-3JA9A") not in by
      and any(e["pn"][0] == "96301-3JA9A" for e in json.loads(
          (OEM / "groups" / "_report" / "nissan.starred_held.json").read_text())["held"]))
for p in sorted((OEM / "groups" / "_report").glob("*.round7_held.json")):
    ns = p.name.split(".")[0]
    if ns != "nissan":
        g = {(x["cat"], tuple(x["pn"])) for x in json.loads((OEM / "groups" / f"{ns}.json").read_text())["likely"]}
        check(f"{p.name}: no listed group is still shipped", not any((e["cat"], tuple(e["pn"])) in g
                                                                     for e in json.loads(p.read_text())["held"]))
ld = (OEM / "groups" / "_report" / "live_diff_2026-11-19_round7.txt").read_text()
summ = re.findall(r"^# (\w+) LIVE: removed (\d+) groups, added (\d+) groups.*?gained (\d+);.*?widened (\d+); "
                  r"added claims (\d+)$", ld, re.M)
check("live diff vs origin/main: 9 namespaces, 0 added groups, 0 gained app-years, 0 widened gates",
      len(summ) == 9 and all(a == g == w_ == ac == "0" for _ns, _r, a, g, w_, ac in summ), summ)
pay = json.loads((OEM.parent.parent / "docs" / "data" / "interchange.json").read_text())
check("payload: oemStatus ok for the 8 shipped namespaces",
      sorted(pay["oemStatus"]) == ["ford", "gm", "hmg", "mb", "mopar", "subaru", "toyota", "vag"]
      and all(x.startswith("ok ") for x in pay["oemStatus"].values()), pay["oemStatus"])
done("test_round7_1119")
