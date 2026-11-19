#!/usr/bin/env python3
"""Round 3 rules (interchange 2026-11-19, branch interchange/round3-1119): the
five flaw classes of the independent nissan check
(groups/_report/nissan_verify_2026-11-18c.json), on every make.

1. Product-page engine column: a limit when it leaves out an engine the
   model-year offers (the catalog attests it for T and T's year page or a lot
   car of T has it); a column naming none of T's engines leaves T out; a
   gas-limited year takes the column as its engine gate (the hybrid's own
   displacement is ruled out by the decode).
2. Fuel from the column only when the words say it: "GAS"/"FLEX" for gas,
   HYBRID/FHEV/"Gas/Electric" for hybrid; a bare "2.4L L4" says nothing.
3. km/h-first units and mandatory export equipment groups are not US parts.
4. Cab and body lists per model-year (2002 Frontier 80721-3S500).
5. Joined drive tokens (2WDSTD, 2WDHICAS); the All-Mode "AUTO" sibling makes
   a "4WD" number part-time only (drive_not a4wd).
Also: the Rogue / Rogue Select feed years, the gate vocabulary, lot engines,
live_diff's gate comparison, and the committed candidate."""
import json
import tempfile
from pathlib import Path

from _util import OEM, check, done
import adapters as A
import curate as C
import policy
import validate as V

F = "Fitting Vehicle Options: "
NPD = "www.nissanpartsdeal.com"

# ------------------------------------------------------------ 2. engine strings
check("hybrid words: FHEV / PHEV / MHEV / Hybrid / Ford 'PFI Gas/Electric'",
      all(C._FIT_HYBRID_RE.search(e) for e in ("4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)", "4 Cyl 2.5L PFI Gas/Electric",
                                               "4 Cyl 2.3L Hybrid Gas/Electric DOHC", "2.0L H4 Hybrid",
                                               "6 Cyl 3.0 L MILD HYBRID EV-GAS (MHEV)"))
      and not any(C._FIT_HYBRID_RE.search(e) for e in ("4 Cyl 2.4 L GAS", "2.4L L4", "8 Cyl 5.3L Flex", "6 Cyl 3.3 L CNG")))
check("gas words: GAS / Flex / FFV; diesel and a bare displacement are not gas",
      all(C._FIT_GAS_RE.search(e) for e in ("4 Cyl 2.4 L GAS", "8 Cyl 5.3L Flex", "4 Cyl 2.5L Duratec FFV (125kW/170PS)",
                                            "6 Cyl 3.6 L FLEX"))
      and not any(C._FIT_GAS_RE.search(e) for e in ("2.4L L4", "6 Cyl 3.5L", "6 Cyl 3.3 L CNG"))
      and C._FIT_DIESEL_RE.search("8 Cyl 6.6L Diesel") and C._FIT_DIESEL_RE.search("4 Cyl 2.0 L DIESEL"))
check("displacement: '4 Cyl 2.4 L FULL HYBRID', '2.4L L4', none in 'Electric Motor'",
      C._fit_lit("4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)") == 2.4 and C._fit_lit("2.4L L4") == 2.4
      and C._fit_lit("Electric Motor") is None and C._lit_in({2.4, 3.5}, 3.5) and not C._lit_in({2.4}, 2.5))


# ------------------------------------------------------------ 1. engine column on stubs
def fr(lo, hi, model, engines, trims=()):
    return A.FitRow(idx=0, lo=lo, hi=hi, make="X", model=model, trims=list(trims), engines=list(engines),
                    options=[], layout="trim", raw="")


class _K:
    def __init__(self, key="K"):
        self.key = key


class _YM:
    def __init__(self, engines=(), variant="", variants=()):
        self.engines, self.variant, self.variants, self.trims = list(engines), variant, list(variants), []
        self.error, self.status = "", 200


class _O:
    def __init__(self, lot):
        self.lot_engines = lot


class _E:
    _fit_engine_column = C.Curation._fit_engine_column
    _t_fit_engines = C.Curation._t_fit_engines
    fit_engine_limit = C.Curation.fit_engine_limit
    fit_engine_conflict = C.Curation.fit_engine_conflict

    def __init__(self, T, cat, k, own, others=(), years=(), lot=None):
        self.t_rows = {(T, cat): [(k, None, f, None) for f in own]}
        self.rows_by_T = {T: [(cat, k, None, f, None) for f in own] + [("x", _K("O"), None, f, None) for f in others]}
        self.t_years = {T: list(years)} if years else {}
        self.o = _O(lot)


CAM11, CAT = ("Toyota", "Camry", 2011), "bumper-front"
k = _K()
HYB = fr(2010, 2011, "Camry", ["4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)"], ["Hybrid"])
ALL = [fr(2007, 2017, "Camry", ["2.4L L4", "2.5L L4", "3.5L V6"])]
LOT11 = {CAM11: {"lits": frozenset({2.4, 2.5}), "hybrid": True, "gas": True}}
check("engine column: a 2011 Camry part listed for the 2.4L hybrid only is '2.4L, hybrid' (gas 2.5L Camrys out)",
      _E(CAM11, CAT, k, [HYB], ALL, lot=LOT11).fit_engine_limit(k, CAT, CAM11) == (frozenset({2.4}), "hybrid"))
check("engine column: '2.4L L4, 2.5L L4, 3.5L V6' (no fuel words) limits nothing (the hybrid prints the same way)",
      _E(CAM11, CAT, k, ALL, ALL, lot=LOT11).fit_engine_limit(k, CAT, CAM11) == (None, ""))
CAM07 = ("Toyota", "Camry", 2007)
ROW07 = fr(2007, 2009, "Camry", ["2.4L L4", "3.5L V6"])
LOT07 = {CAM07: {"lits": frozenset({2.4, 3.5}), "hybrid": True, "gas": True}}
check("materiality: a displacement only a neighbouring year's row attests (2.5L on a 2007-2017 row) is no limit",
      _E(CAM07, CAT, k, [ROW07], ALL, lot=LOT07).fit_engine_limit(k, CAT, CAM07) == (None, ""))
check("materiality: without the lot input every attested displacement counts (fail closed)",
      _E(CAM07, CAT, k, [ROW07], ALL, lot=None).fit_engine_limit(k, CAT, CAM07)[0] == frozenset({2.4, 3.5}))
F150 = ("Ford", "F-150", 2000)
ROWF = fr(2000, 2001, "F-150", ["6 Cyl 4.2L", "8 Cyl 4.6L", "8 Cyl 5.4L"])
LOTF = {F150: {"lits": frozenset({4.2, 4.6, 5.4, 7.3}), "hybrid": False, "gas": True}}
check("materiality: a lot decode the catalog never attests for T (a 7.3L 'F-150') makes no limit",
      _E(F150, "gauge-cluster", k, [ROWF], [], lot=LOTF).fit_engine_limit(k, "gauge-cluster", F150) == (None, ""))
FUS = ("Ford", "Fusion", 2012)
ROWH = fr(2011, 2012, "Fusion", ["4 Cyl 2.5L PFI Gas/Electric"])
OTH = [fr(2010, 2012, "Fusion", ["4 Cyl 2.5L", "6 Cyl 3.0L", "6 Cyl 3.5L"])]
LOTFU = {FUS: {"lits": frozenset({2.5, 3.0, 3.5}), "hybrid": True, "gas": True}}
check("Ford 'PFI Gas/Electric' column: '2.5L, hybrid' (3.0L/3.5L out by decode, a gas 2.5L is 'if equipped')",
      _E(FUS, "gauge-cluster", k, [ROWH], OTH, lot=LOTFU).fit_engine_limit(k, "gauge-cluster", FUS)
      == (frozenset({2.5}), "hybrid"))
QX = ("Infiniti", "QX60", 2016)
ROWQ = fr(2014, 2017, "QX60", ["6 Cyl 3.5L"])
OTHQ = [fr(2014, 2017, "QX60", ["4 Cyl 2.5L", "6 Cyl 3.5L"])]
LOTQ = {QX: {"lits": frozenset({3.5}), "hybrid": False, "gas": True}}
_E.fit_engine_not = C.Curation.fit_engine_not
e = _E(QX, "side-mirrors", k, [ROWQ], OTHQ, lot=LOTQ)
check("gas-limited year: no engine limit (no 2.5L QX60 2016 on the lot yet), but the gas gate rules out 2.5L decodes",
      e.fit_engine_limit(k, "side-mirrors", QX) == (None, "") and e.fit_engine_not(k, "side-mirrors", QX) == [2.5]
      and _E(QX, "side-mirrors", k, [fr(2014, 2017, "QX60", [])], OTHQ, lot=LOTQ).fit_engine_not(k, "side-mirrors", QX) == [])
Q40 = ("Infiniti", "Q40", 2015)
ROW40 = fr(2015, 2015, "Q40", ["6 Cyl 2.5L"])
OTH40 = [fr(2015, 2015, "Q40", ["6 Cyl 3.7L"])]
check("engine column naming none of T's engines leaves T out (80730-JK00C '2015 Q40 | 2.5L'; every Q40 is 3.7L)",
      _E(Q40, "window-regulator", k, [ROW40], OTH40,
         lot={Q40: {"lits": frozenset({3.7}), "hybrid": False, "gas": True}}).fit_engine_conflict(k, "window-regulator", Q40)
      and not _E(CAM11, CAT, k, [HYB], ALL, lot=LOT11).fit_engine_conflict(k, CAT, CAM11)
      and not _E(Q40, "window-regulator", k, [ROW40], OTH40, lot={}).fit_engine_conflict(k, "window-regulator", Q40))
check("year page engines count as offered (no lot car needed)",
      _E(CAM07, CAT, k, [ROW07], ALL, years=[_YM(["2.4L", "2.5L", "3.5L"])], lot={}).fit_engine_limit(k, CAT, CAM07)[0]
      == frozenset({2.4, 3.5}))
check("policy: engine-column, market-unit, cab-list and All-Mode rules are on",
      policy.LIKELY_FIT_ENGINE_RULE and policy.LIKELY_MARKET_UNIT_RULE and policy.LIKELY_CAB_LIST_RULE
      and policy.LIKELY_AUTO_SIBLING_RULE)

# ------------------------------------------------------------ 3. market units
check("km/h first: 'KMH/MPH', 'Instrument-Kph' are the Canada unit; 'MPH/KMH' and 'Instrument Mph' the US one",
      C._kmh_first("Fit Note: With KMH/MPH Speedometer") and C._kmh_first("Meter Assy-Combined,Instrument-Kph")
      and not C._kmh_first("Fit Note: With MPH/KMH Speedometer") and not C._kmh_first("Meter Assy-Combined,Instrument Mph"))
check("export equipment groups: 'Mandatory (EUROPEAN EQUIPMENT GROUP)', 'EXPORT Mandatory' exclude the row",
      C._market_excludes(["Right [GTK,GUE], Up to 11-23-01, Molded in Color Mandatory (EUROPEAN EQUIPMENT GROUP)"])
      and C._market_excludes(["Right [GT5], EXPORT Mandatory (Middle East Equipment Group)"])
      and C._market_excludes(["Fit Note: Ford And Mercury Derivative, With KMH/MPH Speedometer"])
      and not C._market_excludes(["Fit Note: With MPH/KMH Speedometer"])
      and not C._market_excludes(["Right [GT5]"]))


class _R:
    def __init__(self, name, desc=""):
        self.name, self.aux, self.description, self.other_names = name, "", desc, ""


class _C:
    def __init__(self, recs):
        self.records = recs


check("km/h part, class-wide: the record name 'Instrument-Kph' refuses the class (24810-EC44C)",
      C._kmh_part(_C([_R("Meter Assy-Combined,Instrument-Kph")]), [])
      and not C._kmh_part(_C([_R("Meter Assy-Combined,Instrument Mph")]), ["W. 4WD. SE"]))

# ------------------------------------------------------------ 5. drive tokens
check("joined drive tokens: 2WDHICAS / 2WDSTD read as 2WD (24820-1MK5A, 24820-6AH2A)",
      C._drive_terms("*SEDAN. 2WDHICAS. SPORTTEC")[0] == {"2wd"} and C._drive_terms("*SEDAN. 2WDSTD. BASE")[0] == {"2wd"}
      and C._drive_terms("SEDAN. AWD. BASE")[0] == {"awd"})

# ------------------------------------------------------------ 4. cab / body lists per model-year
check("nissan cab codes: every configuration's head (T regular, KC, CC)",
      C._fvo_cab_parts([F + "*KC + *CC, *KC + *CC. SB + *CC. XB"]) == ["KC", "CC", "KC", "CC", "CC"]
      and C._fvo_cab_set([F + "KC + CC. SB + CC. XB, T + KC + CC"]) == {"T", "KC", "CC"}
      and C._fvo_cab_set([F + "W. SE"]) is None and C._fvo_cab_heads([F + "KC. KA24DE + W. SE"]) == {"KC"})


def lr(T, pn, notes, cat="window-regulator"):
    return A.ListRow(site=NPD, seed=T, cat=cat, list_url="u", pn=pn, section="d", main="m", aux="", notes=list(notes),
                     locations=[], replace=None, matched=True, excluded_by=None, product=None,
                     retrieved="2026-11-10T00:00:00Z", line=1, status=200)


class _Slot:
    def __init__(self, slots):
        self.slots, self.reason = tuple(slots), None


class _CL:
    _cab_order = C.Curation._cab_order
    _cab_list_by_T = C.Curation._cab_list_by_T
    _t_page_cabs = C.Curation._t_page_cabs
    _body_list_by_T = C.Curation._body_list_by_T
    _slot_mates = C.Curation._slot_mates
    _auto_sibling = C.Curation._auto_sibling
    _CAB_RE = C.Curation._CAB_RE
    _NISSAN_CAB3 = C.Curation._NISSAN_CAB3
    _CAB_ORDER = C.Curation._CAB_ORDER
    _BODY_WORDS = C.Curation._BODY_WORDS
    _BODY_WORD_RE = C.Curation._BODY_WORD_RE

    def __init__(self, ns, list_rows=None, t_rows=None, members=None):
        self.ns, self.t_list_rows, self.t_rows = ns, list_rows or {}, t_rows or {}
        self.cells_info = {key: {"members": members} for key in set(self.t_list_rows) | set(self.t_rows)}


FR01, FR02 = ("Nissan", "Frontier", 2001), ("Nissan", "Frontier", 2002)
WR = "window-regulator"
P500, P510 = policy.pn_key("nissan", "80721-3S500"), policy.pn_key("nissan", "80721-3S510")
MEM = {P500: {"slot": _Slot(["FL"])}, P510: {"slot": _Slot(["FL"])}}
ROWS = {(FR01, WR): [lr(FR01, "80721-3S500", [F + "*KC + *CC, *KC + *CC. SB + *CC. XB, *T + *KC + *CC"]),
                     lr(FR01, "80721-3S510", [F + "KC + CC. SB + CC. XB, T + KC + CC"])],
        (FR02, WR): [lr(FR02, "80721-3S500", [F + "*KC + *CC, *KC + *CC. SB + *CC. XB"]),
                     lr(FR02, "80721-3S510", [F + "KC + CC. SB + CC. XB, T + KC + CC"])]}
cl = _CL("nissan", ROWS, members=MEM)
k500 = _K(P500)
check("cab list per model-year: 2002 Frontier 3S500 is king cab/crew cab (regular cab under 3S510); 2001 lists all three",
      cl._cab_list_by_T(k500, WR, [FR01, FR02], ("FL",)) == {FR02: ["king cab", "crew cab"]})
check("cab list: a page with no other cab under another number limits nothing",
      _CL("nissan", {(FR02, WR): [lr(FR02, "80721-3S500", [F + "*KC + *CC"])]}, members=MEM)
      ._cab_list_by_T(k500, WR, [FR02], ("FL",)) == {})
FR03 = ("Nissan", "Frontier", 2003)
P700 = policy.pn_key("nissan", "80721-2Z700")
R03 = {(FR03, WR): [lr(FR03, "80721-2Z700", [F + "*KC + *CC. SB + *CC. XB, KC + CC. SB + CC. XB"])],
       (FR03, "side-mirrors"): [lr(FR03, "96301-3S510", [F + "T + KC + CC"], "side-mirrors")]}
c3 = _CL("nissan", R03, members={P700: {"slot": _Slot(["FL"])}})
check("cab list: the model-year's cabs come from T's pages in any category (2003 Frontier 2Z700 KC/CC; mirrors code T)",
      c3._cab_list_by_T(_K(P700), WR, [FR03], ("FL",)) == {FR03: ["king cab", "crew cab"]})
SIL = ("Chevrolet", "Silverado 1500", 2008)
kS, kR = _K("20835552"), _K("REG")
GMROWS = {(SIL, "window-switch"): [(kS, None, fr(2007, 2013, "Silverado", [], ["Extended Cab", "Crew Cab"]), None),
                                   (kR, None, fr(2007, 2013, "Silverado", [], ["Regular Cab"]), None)]}
cg = _CL("gm", t_rows=GMROWS, members={"20835552": {"slot": _Slot(["DM"])}, "REG": {"slot": _Slot(["DM"])}})
check("cab list from fitment trims: Silverado master switch extended/crew beside the regular-cab switch",
      cg._cab_list_by_T(kS, "window-switch", [SIL], ("DM",)) == {SIL: ["extended cab", "crew cab"]})
cg1 = _CL("gm", t_rows={(SIL, "side-mirrors"): [(kS, None, fr(2007, 2013, "Silverado", [], ["LT Extended Cab", "LTZ Crew Cab"]),
                                                  None)]}, members={"20835552": {"slot": _Slot(["L"])}})
check("cab list from fitment trims: no regular-cab number in the slot, no limit (trim names carry cab words)",
      cg1._cab_list_by_T(kS, "side-mirrors", [SIL], ("L",)) == {})
ALE = ("Oldsmobile", "Alero", 2001)
kC, kD = _K("19152000"), _K("SED")
BROWS = {(ALE, WR): [(kC, None, fr(1999, 2004, "Alero", [], ["Coupe GL", "Coupe GLS"]), None),
                     (kD, None, fr(1999, 2004, "Alero", [], ["Sedan GL"]), None)]}
cb = _CL("gm", t_rows=BROWS, members={"19152000": {"slot": _Slot(["FL"])}, "SED": {"slot": _Slot(["FL"])}})
check("body list: Alero 2001 coupe-only regulator beside the sedan's is 'coupe'",
      cb._body_list_by_T(kC, WR, [ALE], ("FL",)) == {ALE: ["coupe"]})
PF05, GC = ("Nissan", "Pathfinder", 2005), "gauge-cluster"
kA, kB = policy.pn_key("nissan", "24810-EA48D"), policy.pn_key("nissan", "24810-EA47D")
ca = _CL("nissan", {(PF05, GC): [lr(PF05, "24810-EA48D", [F + "W. 4WD"], GC), lr(PF05, "24810-EA47D", [F + "*W. AUTO"], GC)]},
         members={kA: {"slot": _Slot(["C"])}, kB: {"slot": _Slot(["C"])}})
check("All-Mode sibling: Pathfinder 2005 EA48D 'W. 4WD' beside EA47D '*W. AUTO' is part-time 4WD only",
      ca._auto_sibling(_K(kA), GC, PF05, ("C",)) and not ca._auto_sibling(_K(kB), GC, PF05, ("C",)))

# ------------------------------------------------------------ feed years holding two catalog models
check("Rogue 2014-2015 also holds the Rogue Select; 2013 and 2016 do not",
      policy.ambiguous_feed_alt("Nissan", "Rogue", 2014) == "Rogue Select"
      and policy.ambiguous_feed_alt("Nissan", "Rogue", 2015) == "Rogue Select"
      and policy.ambiguous_feed_alt("Nissan", "Rogue", 2016) is None
      and policy.ambiguous_feed_alt("Nissan", "Murano", 2015) is None)

# ------------------------------------------------------------ gate vocabulary, app shape
check("gate: drive_not a4wd only beside a 4WD-family drive without a4wd",
      V.gate_problem({"drive": "4wd", "drive_basis": "stated", "drive_not": "a4wd"}) is None
      and V.gate_problem({"drive": "2wd", "drive_not": "a4wd"}) and V.gate_problem({"drive": "a4wd", "drive_not": "a4wd"})
      # round4-1119: drive_not alone (a same-option drive sibling) is classes of ONE family
      and V.gate_problem({"drive_not": "a4wd"}) is None and V.gate_problem({"drive_not": "a4wd/2wd"}))
check("gate: eng_not only on a gas gate without an engine list",
      V.gate_problem({"fuel": "gas", "eng_not": ["2.5L"]}) is None
      and V.gate_problem({"eng_not": ["2.5L"]}) and V.gate_problem({"fuel": "hybrid", "eng_not": ["2.5L"]})
      and V.gate_problem({"fuel": "gas", "eng": ["3.5L"], "eng_not": ["2.5L"]})
      and V.gate_problem({"fuel": "gas", "eng_not": ["2.5"]}) and V.gate_problem({"fuel": "gas", "eng_not": []}))
check("gate: a cab list holds two or more distinct cabs; one cab stays a string",
      V.gate_problem({"cab": ["king cab", "crew cab"]}) is None and V.gate_problem({"cab": "crew cab"}) is None
      and V.gate_problem({"cab": ["king cab"]}) and V.gate_problem({"cab": ["king cab", "king cab"]})
      and V.gate_problem({"cab": ["king cab", "boat"]}))

# ------------------------------------------------------------ lot engines
with tempfile.TemporaryDirectory() as td:
    ex = Path(td) / "extras.json"
    ex.write_text(json.dumps({"extraFields": ["photo", "color", "engine", "trans", "transSrc", "body"],
                              "extras": {"1": ["", "", "2.5L 4-cyl", "", "", "sedan"],
                                         "2": ["", "", "2.4L 4-cyl", "", "", "sedan"],
                                         "3": ["", "", "", "", "", ""]}}))
    inv = {"fields": ["id", "vin", "year", "make", "model"],
           "vehicles": [[1, "V1", 2011, "Toyota", "Camry"], [2, "V2", 2011, "Toyota", "Camry"],
                        [3, "V3", 2011, "Toyota", "Camry"]],
           "vpic": {"1": ["Hybrid", "usable", "", "", ""]}}
    le = C.lot_engines(inv, str(ex))
    check("lot engines: displacements per model-year, hybrid from the VIN trim, gas from a decoded non-hybrid",
          le[("Toyota", "Camry", 2011)] == {"lits": frozenset({2.4, 2.5}), "hybrid": True, "gas": True})
    check("lot engines: no extras file -> None (every attested displacement counts)",
          C.lot_engines(inv, str(Path(td) / "missing.json")) is None)

# ------------------------------------------------------------ live_diff gate comparison
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("live_diff", OEM / "audit11_4" / "live_diff.py")
LD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LD)
check("live_diff: an added or tightened limit narrows; a dropped or loosened one widens",
      LD.gate_cmp(None, {"eng": ["2.4L"], "fuel": "hybrid"}) == "narrowed"
      and LD.gate_cmp({"drive": "4wd"}, {"drive": "4wd", "drive_not": "a4wd"}) == "narrowed"
      and LD.gate_cmp({"cab": ["king cab", "crew cab"]}, {"cab": "crew cab"}) == "narrowed"
      and LD.gate_cmp({"eng": ["3.5L"]}, None) == "widened"
      and LD.gate_cmp({"cab": "crew cab"}, {"cab": ["king cab", "crew cab"]}) == "widened"
      and LD.gate_cmp({"eng": ["3.5L"]}, {"eng": ["2.5L", "3.5L"]}) == "widened"
      and LD.gate_cmp({"fuel": "gas"}, {"fuel": "gas", "eng_not": ["2.5L"]}) == "narrowed"
      and LD.gate_cmp({"fuel": "gas", "eng_not": ["2.0L", "2.5L"]}, {"fuel": "gas", "eng_not": ["2.5L"]}) == "widened"
      and LD.gate_cmp({"drive": "2wd", "drive_basis": "unchecked"}, {"drive": "2wd", "drive_basis": "stated"}) == "narrowed")

# ------------------------------------------------------------ committed candidate
cand = json.loads((OEM / "groups" / "_report" / "nissan.candidate.json").read_text())
pns = {p for g in cand["likely"] for p in g["pn"]}
check("candidate: the km/h cluster 24810-EC44C is not in it", "24810-EC44C" not in pns)
check("candidate: no Rogue 2014-2015 app (Rogue Select pages list none of its numbers for both years)",
      not any(a[1] == "Rogue" and a[2] <= 2015 and a[3] >= 2014 for g in cand["likely"] for a in g["apps"]))
check("candidate: every gate passes the vocabulary", all(V.gate_problem(x[4]) is None
                                                       for g in cand["likely"] for x in g.get("gates") or []))
q = next((g for g in cand["likely"] if "24810-3JA1B" in g["pn"]), None)
# round6-1119: the group is held when its claim rests on starred clauses only
held6 = json.loads((OEM / "groups" / "_report" / "nissan.starred_held.json").read_text())["held"]
check("candidate: 24810-3JA1B's QX60 gate rules out the 2.5L hybrid by engine (or the group is held, round 6)",
      (q is not None and any(x[1] == "QX60" and x[4].get("eng") == ["3.5L"] for x in q.get("gates") or []))
      or (q is None and (any("24810-3JA1B" in e["pn"] for e in held6) or any("24810-3JA1B" in e["pn"] for e in json.loads(
          (OEM / "groups" / "_report" / "nissan.round8_held.json").read_text())["held"]))),
      json.dumps(q and q.get("gates")))
done("test_round3_1119")
