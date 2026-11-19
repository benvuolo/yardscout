#!/usr/bin/env python3
"""Round 9 (interchange 2026-11-19, branch interchange/round9-1119): after the
ninth independent nissan check (groups/_report/nissan_verify_2026-11-19i.json),
the nissan candidate says what the number is and holds the last ambiguous
vehicle-years (curate.ROUND9_NS = {nissan}; the eight live namespaces stay
byte-identical; A5 and D are measures only).

A. The note says what the number is, read from the catalog part name:
   'Motor Assy-...' is the window motor ('window motor only'); names that mix
   motor and regulator, name a component, or are missing hold the group.
B1 held_variant_unread   the year index offers variant pages not all read.
B2 held_twin_changeover  an undated number whose same-option twin changes over
                         inside the model year (also under the 5-month rule).
B3 held_body_mark        the same configuration under another body mark only.
B4 held_drive_open       the row names no drive; a same-part sibling of a
                         narrower configuration names one.
C. label and note opening name the site the records came from."""
import json
import re
from types import SimpleNamespace

from _util import OEM, check, done
import adapters as A
import curate as C
import policy

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"
IPD = "www.infinitipartsdeal.com"


def lr(pn, notes, main="Regulator Assy-Door Window, RH", loc=("Passenger side",), seed=("Nissan", "Altima", 1994),
       cat="window-regulator", site=NPD, variant="", url=None, line=1):
    return A.ListRow(site=site, seed=seed, cat=cat, list_url=url or f"https://{site}/parts-list/{seed[2]}-x/{cat}.html",
                     pn=pn, section="diagram", main=main, aux="", notes=list(notes), locations=list(loc), replace=None,
                     matched=True, excluded_by=None, product=None, retrieved="", line=line, status=200, variant=variant)


class _K:
    def __init__(self, pn, names=(), site=NPD):
        self.key, self.pns = policy.pn_key("nissan", pn), {pn}
        self.packaging = "reg?"
        self.records = [SimpleNamespace(site=site, oem_names=[n], pointer=f"{site}:records:L{i + 1}")
                        for i, n in enumerate(names)]


class _Cur:
    for _m in ("round9_tests", "_name_class", "_class_names", "_note_pack", "_group_brand"):
        locals()[_m] = getattr(C.Curation, _m)
    _same_part = staticmethod(C.Curation._same_part)

    def __init__(self, T, cat, rows, years=(), links=()):
        self.ns = "nissan"
        self.t_list_rows = {(T, cat): list(rows)} if rows else {}
        self.t_years = {T: list(years)} if years else {}
        self.links = {frozenset(policy.pn_key("nissan", y) for y in x) for x in links}
        self.rows = list(rows)

    def _pn_list_rows(self, key, cat):
        return [x for x in self.rows if policy.pn_key("nissan", x.pn) == key and x.cat == cat]

    def note_excludes(self, notes, T, market=True):
        return C._production_excludes(notes, T[2])

    def comparable(self, cat, a, b):
        return a == b or frozenset((a, b)) in self.links


T94 = ("Nissan", "Altima", 1994)
# ------------------------------------------------------------ A: names
m = _Cur(T94, "window-regulator", [lr("80730-0E700", [], main="Motor Assy-Regulator, RH")])
k = _K("80730-0E700")
nc = m._name_class(k, "window-regulator")
check("A1: 'Motor Assy-Regulator, RH' is the window motor; the note says 'window motor only'",
      nc["class"] == "motor" and not nc["hold"] and m._note_pack(k, "window-regulator") == "motor"
      and C._pack_text("window-regulator", "motor") == "window motor only", nc)
check("A1: the name's place in the raw is kept (site:lists:L<line>)",
      nc["names"] == [{"name": "Motor Assy-Regulator", "ref": f"{NPD}:lists:L1"}]
      or nc["names"][0]["ref"] == f"{NPD}:lists:L1", nc["names"])
r = _Cur(T94, "window-regulator", [lr("80720-0E700", [], main="Regulator Assy-Door Window, RH")])
k = _K("80720-0E700")
check("A1: 'Regulator Assy-Door Window' is a regulator; no packaging words (the name does not say the motor)",
      r._name_class(k, "window-regulator")["class"] == "regulator"
      and C._pack_text("window-regulator", r._note_pack(k, "window-regulator")) == "")
mx = _Cur(T94, "window-regulator", [lr("80720-0E701", [], main="Regulator Assy-Door Window, RH")])
k = _K("80720-0E701", names=["Motor Assy-Regulator, RH"])
check("A2: a number named both motor (product record) and regulator (list row) is held",
      bool(mx._name_class(k, "window-regulator")["hold"]), mx._name_class(k, "window-regulator"))
gl = _Cur(T94, "side-mirrors", [lr("96365-0E700", [], main="Glass-Mirror, RH", cat="side-mirrors")])
check("A3: a side-mirror number named 'Glass-Mirror' (a component) is held",
      "component" in str(gl._name_class(_K("96365-0E700"), "side-mirrors")["hold"]))
wp = _Cur(T94, "wiper-motor", [lr("28810-0E700", [], main="Motor Assy-Windshield Wiper", cat="wiper-motor")])
check("A3: a wiper motor is the wiper-motor category's assembly, not a component",
      wp._name_class(_K("28810-0E700"), "wiper-motor")["class"] == "assembly"
      and not wp._name_class(_K("28810-0E700"), "wiper-motor")["hold"])
check("A2: no name in the raw holds the group",
      bool(_Cur(T94, "side-mirrors", [])._name_class(_K("96301-0E700"), "side-mirrors")["hold"]))

# ------------------------------------------------------------ C: the site
cb = _Cur(T94, "x", [])
check("C: records from infinitipartsdeal name 'Infiniti', nissanpartsdeal 'Nissan', both 'Infiniti/Nissan'",
      cb._group_brand(_K("1", names=["a"], site=IPD), "Nissan") == "Infiniti"
      and cb._group_brand(_K("1", names=["a"], site=NPD), "Nissan") == "Nissan"
      and cb._group_brand(SimpleNamespace(records=[SimpleNamespace(site=IPD), SimpleNamespace(site=NPD)]),
                          "Nissan") == "Infiniti/Nissan")

# ------------------------------------------------------------ B1: variant pages
R17 = ("Nissan", "Rogue", 2017)
ym = SimpleNamespace(variant="t32u", variants=["hybrid", "t32j", "t32d", "t32u"])
row = lr("82731-4BA0A", [], seed=R17, variant="t32u",
         url=f"https://{NPD}/parts-list/2017-nissan-rogue-t32u/body_side_rear/rear_door_window_regulator.html")
t = _Cur(R17, "window-regulator", [row], years=[ym]).round9_tests(_K("82731-4BA0A"), "window-regulator", R17, {})
check("B1: Rogue 2017, only t32u read of hybrid/t32j/t32d/t32u: held (t32d, t32j unread; the hybrid has the gas gate)",
      t and t[0][0] == "held_variant_unread" and t[0][1]["unread"] == ["t32d", "t32j"], t)
row2 = lr("82731-4BA0A", [], seed=R17, url=f"https://{NPD}/parts-list/2017-nissan-rogue-t32j/x/y.html")
t = _Cur(R17, "window-regulator", [row, row2], years=[SimpleNamespace(variant="t32u", variants=["t32j", "t32u"])]) \
    .round9_tests(_K("82731-4BA0A"), "window-regulator", R17, {})
check("B1: every variant page read (variant read from the page slug): no hold", t == [], t)

# ------------------------------------------------------------ B2: twin changeover
own = lr("27510-2B000", ["F/AIR CONDITIONER-STD TYPE", F + "*FED. S. XE + *CAL. S. XE, FED. S. SE"],
         main="Controller Assy-Air Conditiner", loc=(), cat="climate-control")
twin = lr("27510-2B001", ["F/AIR CONDITIONER-STD TYPE", "Production Date: from 04/1994",
                          F + "*FED. S. XE + *CAL. S. XE, FED. S. (GXE+ SE) + CAL. S. (GXE+ SE)"],
          main="Controller Assy-Air Conditiner", loc=(), cat="climate-control")
check("B2: the twin's 'from 04/1994' overlaps 1994 by 3 months, under the 5-month listing rule",
      C._production_excludes(twin.notes, 1994))
t = _Cur(T94, "climate-control", [own, twin]).round9_tests(_K("27510-2B000"), "climate-control", T94, {})
check("B2: Altima 1994 27510-2B000 (undated) beside its twin 2B001 from 04/1994: held_twin_changeover",
      ("held_twin_changeover", {"twins": ["27510-2B001"]}) in t, t)
twin_out = lr("27510-2B001", ["F/AIR CONDITIONER-STD TYPE", "Production Date: from 08/1994",
                              F + "*FED. S. XE + *CAL. S. XE"], main="Controller Assy-Air Conditiner", loc=(),
              cat="climate-control")
check("B2: a twin starting after the model year: no hold",
      not _Cur(T94, "climate-control", [own, twin_out]).round9_tests(_K("27510-2B000"), "climate-control", T94, {}))
S95 = ("Nissan", "Stanza", 1995)
a = lr("J6301-1E400", [F + "FED. S. GLE + CAL. S. GLE"], main="Mirror Assy-Door, RH", cat="side-mirrors", seed=S95)
b = lr("J6301-2B500", ["LESS PAINT / PRIMER", F + "FED. S. GLE + CAL. S. GLE"], main="Mirror Assy-Door, RH",
       cat="side-mirrors", seed=S95)
t = _Cur(S95, "side-mirrors", [a, b], links=[("J6301-1E400", "J6301-2B500")]).round9_tests(
    _K("J6301-1E400"), "side-mirrors", S95, {})
check("B2: Stanza 1995 J6301-1E400 beside its undated successor 2B500 (broader words): held",
      ("held_twin_changeover", {"twins": ["J6301-2B500"]}) in t, t)

# ------------------------------------------------------------ B3: body mark
Q16 = ("Infiniti", "QX50", 2016)
own = lr("96302-1BA1D", [F + "*WAG. PREMIUM"], main="Mirror Assy-Door, LH", loc=("Driver side",), cat="side-mirrors",
         seed=Q16, site=IPD)
lwb = lr("96302-5UB0A", [F + "LWB. PREMIUM"], main="Mirror Assy-Door, LH", loc=("Driver side",), cat="side-mirrors",
         seed=Q16, site=IPD)
t = _Cur(Q16, "side-mirrors", [own, lwb]).round9_tests(_K("96302-1BA1D", site=IPD), "side-mirrors", Q16, {})
check("B3: QX50 2016 96302-1BA1D '*WAG' beside 5UB0A 'LWB', same option otherwise: held_body_mark",
      any(r0 == "held_body_mark" for r0, _d in t), t)
fed = lr("96302-1BA1E", [F + "CAL. PREMIUM"], main="Mirror Assy-Door, LH", loc=("Driver side",), cat="side-mirrors",
         seed=Q16, site=IPD)
own2 = lr("96302-1BA1D", [F + "FED. PREMIUM"], main="Mirror Assy-Door, LH", loc=("Driver side",), cat="side-mirrors",
          seed=Q16, site=IPD)
check("B3: FED / CAL (markets) and KC / CC / T (cab codes) are not body marks",
      not any(r0 == "held_body_mark" for r0, _d in _Cur(Q16, "side-mirrors", [own2, fed]).round9_tests(
          _K("96302-1BA1D", site=IPD), "side-mirrors", Q16, {})))

# ------------------------------------------------------------ B4: drive left open
Q13 = ("Infiniti", "QX56", 2013)
own = lr("24820-3ZD1C", ["Production Date: 02/2013-08/2014", F + "3ROW"], main="Speedometer Assy-Analog", loc=(),
         cat="gauge-cluster", seed=Q13, site=IPD)
awd = lr("24820-1ZS0A", [F + "*3ROW. AWD. PREMIUM"], main="Speedometer Assy-Analog", loc=(), cat="gauge-cluster",
         seed=Q13, site=IPD)
t = _Cur(Q13, "gauge-cluster", [own, awd]).round9_tests(_K("24820-3ZD1C", site=IPD), "gauge-cluster", Q13, {})
check("B4: QX56 2013 3ZD1C '3ROW' (no drive) beside the AWD-only 1ZS0A, no drive gate: held_drive_open",
      any(r0 == "held_drive_open" for r0, _d in t), t)
check("B4: with a drive gate the row is not held for the drive",
      not any(r0 == "held_drive_open" for r0, _d in _Cur(Q13, "gauge-cluster", [own, awd]).round9_tests(
          _K("24820-3ZD1C", site=IPD), "gauge-cluster", Q13, {"drive": "2wd"})))
own0 = lr("24820-3ZD0C", ["Production Date: 02/2013-08/2014", F + "*3ROW"], main="Speedometer Assy-Analog", loc=(),
          cat="gauge-cluster", seed=Q13, site=IPD)
check("B4: 3ZD0C '*3ROW' (the same row with the star) is held the same way: the star is not a drive",
      any(r0 == "held_drive_open" for r0, _d in _Cur(Q13, "gauge-cluster", [own0, awd]).round9_tests(
          _K("24820-3ZD0C", site=IPD), "gauge-cluster", Q13, {})))

# ------------------------------------------------------------ committed files
REP = OEM / "groups" / "_report"
cand = json.loads((REP / "nissan.candidate.json").read_text())
by = {(g["cat"], g["pn"][0]): g for g in cand["likely"]}


def claimed(cat, pn, T):
    g = by.get((cat, pn))
    return bool(g) and any(a[0] == T[0] and a[1] == T[1] and a[2] <= T[2] <= a[3] for a in g["apps"])


cen = json.loads((REP / "round9_census_2026-11-19.json").read_text())
for rule, rows in cen["b_rows"].items():
    left = [(x["pn"][0], x["t"]) for x in rows if claimed(x["cat"], x["pn"][0], tuple(x["t"]))]
    check(f"candidate: no 1119i vehicle-year of {rule} is still claimed ({len(rows)} in the census)",
          rows and not left, left[:4])
for name, T, cat, pns in (
        ("Rogue 2017", ("Nissan", "Rogue", 2017), "window-regulator", ("82731-4BA0A", "82730-4BA0A", "80730-4BA1A")),
        ("Sentra 1995-96", ("Nissan", "Sentra", 1995), "gauge-cluster", ("24820-89Y00",)),
        ("Altima 1994", ("Nissan", "Altima", 1994), "climate-control", ("27510-2B000",)),
        ("Altima 1996", ("Nissan", "Altima", 1996), "side-mirrors", ("J6301-1E400", "J6302-1E400")),
        ("Stanza 1995", ("Nissan", "Stanza", 1995), "side-mirrors", ("J6301-2B500", "J6302-2B500")),
        ("QX50 2016", ("Infiniti", "QX50", 2016), "side-mirrors", ("96301-1BA1D", "96302-1BA1D")),
        ("QX56 2013", ("Infiniti", "QX56", 2013), "gauge-cluster", ("24820-3ZD1C",))):
    check(f"candidate: the hub's named {name} is not claimed by {', '.join(pns)}",
          not any(claimed(cat, pn, T) for pn in pns))
names = json.loads((REP / "round9_names_2026-11-19.json").read_text())
mot = [r for r in names["rows"] if r["cat"] == "window-regulator" and r["class"] == "motor"]
reg = [r for r in names["rows"] if r["cat"] == "window-regulator" and r["class"] == "regulator"]
check(f"A: every motor-named window-regulator group says 'window motor only' ({len(mot)} groups)",
      mot and all("window motor only" in by[("window-regulator", r["pn"][0])]["note"] for r in mot))
check(f"A: no regulator-named group says it ({len(reg)} groups)",
      reg and not any("window motor only" in by[("window-regulator", r["pn"][0])]["note"] for r in reg))
check("A4: the names census covers every candidate group, each name with its place in the raw",
      len(names["rows"]) == len(cand["likely"])
      and all(n["ref"] and re.match(r"^www\.\w+\.com:(lists|records):L\d+$", n["ref"]) for r in names["rows"]
              for n in r["names"]))
check("C: label '<site> catalog' on every group and the note opens with it",
      all(g.get("label") in ("Nissan catalog", "Infiniti catalog", "Infiniti/Nissan catalog")
          and g["note"].startswith(g["label"] + " lists #") for g in cand["likely"]))
check("C: every note within the 160-character cap", all(len(g["note"]) <= policy.NOTE_MAX_LEN for g in cand["likely"]))
ld = (REP / "live_diff_2026-11-19_round9.txt").read_text()
summ = dict(re.findall(r"^# (\w+) LIVE: (removed 0 groups, added 0 groups, changed 0;.*)$", ld, re.M))
check("live diff vs origin/main: the 8 live namespaces are unchanged",
      sorted(summ) == ["ford", "gm", "hmg", "mb", "mopar", "subaru", "toyota", "vag"], sorted(summ))
nl = re.search(r"^# nissan LIVE: (.*)$", ld, re.M)
check("nissan: only shrinks (0 added groups, 0 gained app-years, 0 widened gates, 0 added claims)",
      nl and re.search(r"added 0 groups", nl.group(1)) and "gained 0" in nl.group(1)
      and "widened 0" in nl.group(1) and "added claims 0" in nl.group(1), nl and nl.group(1))
check("round 9 rules are nissan only, kept out of policy.py",
      C.ROUND9_NS == frozenset({"nissan"}) and "ROUND9" not in (OEM / "policy.py").read_text())
done("test_round9_1119")
