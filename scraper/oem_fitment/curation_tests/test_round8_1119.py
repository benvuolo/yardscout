#!/usr/bin/env python3
"""Round 8 (interchange 2026-11-19, branch interchange/round8-1119): after the
eighth independent nissan check (groups/_report/nissan_verify_2026-11-19h.json,
branch interchange/verify-nissan-1119h; its WRONG is a lot car, not curation),
the nissan candidate claims only what a vehicle-year's own pages carry
(curate.ROUND8_NS = {nissan}; the shipped namespaces: census only,
groups/_report/round8_census_2026-11-19.json, files unchanged).

1. held_no_own_page: no list row of its own for the number in the raw.
2. held_window_other_page: the build window read from another model year's page.
3. held_undated_siblings: same-option numbers on the page, none dated.
5. 'gas only' where the hybrid's pages were never read reads 'checked on
   gas-model pages'; a year that does not fit leaves at the note cap.
6. held_plus_reading: the claim depends on '+' joining configurations of
   different engines or drives; KC / CC / T stay cab codes (counted)."""
import json
import re

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"
IPD = "www.infinitipartsdeal.com"


def lr(pn, notes, main="Mirror Assy-Outside, LH", loc=("Driver side",), seed=("Infiniti", "Q40", 2015),
       cat="side-mirrors", site=IPD):
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=f"https://x/{seed[2]}-{seed[1]}/{cat}.html", pn=pn,
                     section="diagram", main=main, aux="", notes=list(notes), locations=list(loc), replace=None,
                     matched=True, excluded_by=None, product=None, retrieved="", line=1, status=200)


class _K:
    def __init__(self, pn):
        self.key, self.records, self.pns = policy.pn_key("nissan", pn), [], {pn}


class _Cur:
    for _m in ("undated_siblings", "_round8_pre", "_gas_checked_note"):
        locals()[_m] = getattr(C.Curation, _m)
    _same_part = staticmethod(C.Curation._same_part)

    def __init__(self, T, cat, rows, seeds=(), links=()):
        self.ns = "nissan"
        self.t_list_rows = {(T, cat): list(rows)} if rows else {}
        self.t_seed_records = {(T, cat): list(seeds)} if seeds else {}
        self.links = {frozenset(policy.pn_key("nissan", y) for y in x) for x in links}

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b or frozenset((a, b)) in self.links


# ------------------------------------------------------------ decision 6: '+'
fx = C._plus_strict_notes([F + "W. VQ35HR. PREMIUM, W. VQ35HR. PREMIUM + W. VK50VE"], IPD)
check("decision 6: FX50 'W. VQ35HR. PREMIUM + W. VK50VE' (two engines joined by '+') is unread; the plain "
      "alternative stays", fx == [F + "W. VQ35HR. PREMIUM"], fx)
check("decision 6: 'W. 2WD. S + W. 4WD. S. 6MT + W. BASECAMP' (two drive families) is unread: nothing left",
      C._plus_strict_notes([F + "W. 2WD. S + W. 4WD. S. 6MT + W. BASECAMP"], NPD) is None)
check("decision 6: '+' joining cab codes only ('KC. SE + CC. SE') is kept (KC / CC / T read as cab codes)",
      C._plus_strict_notes([F + "KC. SE + CC. SE"], NPD) == [F + "KC. SE + CC. SE"])

# ------------------------------------------------------------ decision 3: undated same-option siblings
Q15 = ("Infiniti", "Q40", 2015)
own = lr("96302-1NC3A", [F + "S. JOURNEY"])
sib = lr("96302-6WJ0A", [F + "S"])
check("decision 3: Q40 2015 96302-1NC3A 'S. JOURNEY' beside 6WJ0A 'S', both undated: 6WJ0A is an undated sibling",
      _Cur(Q15, "side-mirrors", [own, sib]).undated_siblings(_K("96302-1NC3A"), "side-mirrors", Q15) == ["96302-6WJ0A"])
check("decision 3: a dated sibling is no undated sibling",
      _Cur(Q15, "side-mirrors", [own, lr("96302-6WJ0A", ["Production Date: from 06/2014", F + "S"])]).undated_siblings(
          _K("96302-1NC3A"), "side-mirrors", Q15) == [])
check("decision 3: another configuration ('S. SPORT' beside 'S. JOURNEY') is no same-option sibling",
      _Cur(Q15, "side-mirrors", [own, lr("96302-6WJ0B", [F + "S. SPORT"])]).undated_siblings(
          _K("96302-1NC3A"), "side-mirrors", Q15) == [])
check("decision 3: the number's own predecessor / successor is not counted",
      _Cur(Q15, "side-mirrors", [own, sib], links=[("96302-1NC3A", "96302-6WJ0A")]).undated_siblings(
          _K("96302-1NC3A"), "side-mirrors", Q15) == [])

# ------------------------------------------------------------ decisions 1 and 2
rec = A.Record.__new__(A.Record)
rec.key, rec.list_url, rec.note_texts, rec.site = policy.pn_key("nissan", "80720-0E715"), \
    "https://www.nissanpartsdeal.com/parts-list/1995-nissan-altima/body_side_rear/front_door_window_regulator.html", \
    [], NPD
A95 = ("Nissan", "Altima", 1995)
r = _Cur(A95, "window-regulator", [], seeds=[rec])._round8_pre(_K("80720-0E715"), "window-regulator", A95, None)
check("decision 1: no list row of its own (Altima 1995): held_no_own_page, the page for the crawl named",
      r and r[0] == "held_no_own_page" and r[1]["missing_pages"] == [rec.list_url], r)
w = {"src": "other_page", "kind": "no_other_row", "wins": [(2004 * 12 + 10, 2005 * 12 + 8)]}
A05 = ("Nissan", "Armada", 2005)
r = _Cur(A05, "side-mirrors", [lr("96301-7S600", [F + "W. LE"], seed=A05, site=NPD)])._round8_pre(
    _K("96301-7S600"), "side-mirrors", A05, w)
check("decision 2: a window read from another model year's page (Armada 2005 from the 2006 page): held",
      r and r[0] == "held_window_other_page" and "10/2004-08/2005" in r[1]["window"], r)
check("decision 2: an own-page window is kept", _Cur(A05, "side-mirrors", [lr("96301-7S600", [F + "W. LE"], seed=A05,
                                                                             site=NPD)])._round8_pre(
    _K("96301-7S600"), "side-mirrors", A05, dict(w, src="page")) is None)

# ------------------------------------------------------------ decision 5: the words
Ts = [("Nissan", "Murano", y) for y in range(2015, 2020)] + [("Nissan", "Rogue", 2017)]
check("decision 5: 'Murano 2016-2017, Rogue: checked on gas-model pages'",
      _Cur(Ts[0], "x", [])._gas_checked_note({("Nissan", "Murano", 2016), ("Nissan", "Murano", 2017),
                                             ("Nissan", "Rogue", 2017)}, Ts)
      == "Murano 2016-2017, Rogue: checked on gas-model pages")

# ------------------------------------------------------------ committed files
cand = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
by = {(g["cat"], g["pn"][0]): g for g in cand["likely"]}
cen = json.loads((OEM / "groups" / "_report" / "round8_census_2026-11-19.json").read_text())


def claimed(cat, pn, T):
    g = by.get((cat, pn))
    return bool(g) and any(a[0] == T[0] and a[1] == T[1] and a[2] <= T[2] <= a[3] for a in g["apps"])


nrows = cen
cls = {k: [x for x in v] for k, v in (nrows.get("nissan_rows") or {}).items()}
for k in ("no_own_page", "window_other_page", "undated_siblings", "plus_reading"):
    left = [(x["pn"][0], x["t"][1], x["t"][2]) for x in cls.get(k, []) if claimed(x["cat"], x["pn"][0], tuple(x["t"]))]
    check(f"candidate: no round-7 vehicle-year of class {k} is still claimed ({len(cls.get(k, []))} in the census)",
          cls.get(k) is not None and not left, left[:4])
check("candidate: the 1119h census sizes are reproduced (61 vy no own page, 56 vy gas with the hybrid unread)",
      nrows["nissan_census_on_round7_candidate"]["no_own_page"]["vehicle_years"] == 61
      and nrows["nissan_census_on_round7_candidate"]["gas_unread_hybrid"]["vehicle_years"] == 56)
check("candidate: no note says 'gas only'; the gas-checked words appear where the hybrid's pages were unread",
      not any("gas only" in g["note"] for g in cand["likely"])
      and any("checked on gas-model pages" in g["note"] for g in cand["likely"]))
check("candidate: FX50 2009-2010 on 96301/96302-1CA0A and Xterra 2007-2008 on 96301/96302-EA000 not claimed",
      not any(claimed("side-mirrors", pn, ("Infiniti", "FX50", y)) for pn in ("96301-1CA0A", "96302-1CA0A")
              for y in (2009, 2010))
      and not any(claimed("side-mirrors", pn, ("Nissan", "Xterra", y)) for pn in ("96301-EA000", "96302-EA000")
                  for y in (2007, 2008)))
check("candidate: every note within the 160-character cap", all(len(g["note"]) <= policy.NOTE_MAX_LEN
                                                                  for g in cand["likely"]))
r8 = json.loads((OEM / "groups" / "_report" / "nissan.round8_held.json").read_text())
check("held list (round 8): its four reasons only; every round-7 no-own-page vehicle-year names the page to crawl",
      all(h["reason"] in ("held_no_own_page", "held_window_other_page", "held_undated_siblings", "held_plus_reading")
          for g in r8["held"] for h in g["held"])
      and all(x["missing_pages"] for x in cls.get("no_own_page", [])))
check("census: the crawl list for the 1119h missing pages is 22 pages over 12 vehicle-years",
      nrows["nissan_crawl"]["pages"] == 22 and nrows["nissan_crawl"]["vehicle_years"] == 12)
check("census: the cab-code gates (KC / CC / T) are counted", "cab_code_gates" in nrows["nissan_census_on_round7_candidate"])
ld = (OEM / "groups" / "_report" / "live_diff_2026-11-19_round8.txt").read_text()
summ = dict(re.findall(r"^# (\w+) LIVE: (removed 0 groups, added 0 groups, changed 0;.*)$", ld, re.M))
check("live diff vs origin/main: the 8 shipped namespaces are unchanged (round 8 is census only there)",
      sorted(summ) == ["ford", "gm", "hmg", "mb", "mopar", "subaru", "toyota", "vag"], sorted(summ))
check("round 8 rules are nissan only, kept out of policy.py",
      C.ROUND8_NS == frozenset({"nissan"}) and "ROUND8" not in (OEM / "policy.py").read_text())
done("test_round8_1119")
