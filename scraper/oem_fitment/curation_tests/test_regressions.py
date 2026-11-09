#!/usr/bin/env python3
"""Regression checks for fail-open paths found in review (2026-11-05, after
the first real-data run on oem-raw@d1108d0). Each check fails on the code
before the fix and passes after it; ambiguity may only remove claims.

1. A regulator name's "W/Motor" phrase is packaging (§5.8), but a phrase
   that says more than packaging still conditions the car (§5.6).
2. An unparsed engine key ("?", raw) fails every universe test (§5.5),
   even when the universe and the row print the same text.
3. Notes feed position resolution through POSITION clauses only (§5.8): a
   colour ("Lt Gray") is not a side, while "Left" on a passenger part is
   still a conflict.
"""
import copy

from _util import TOY, check, confirmed, done, run, sienna_fixture
import curate as C
import notes as N

PSHA = C.policy_sha256()
ST = confirmed((TOY, "window-regulator"), policy_sha=PSHA)
S04 = ("Toyota", "Sienna", 2004)

# ------------------------------------------------------------------ 1
q = lambda s: N.qualifier_phrases(s, (), "window-regulator")  # noqa: E731
check("1 'W/Motor' on a regulator is packaging, not a qualifier",
      q("Regulator Assy, Front Door Window, W/Motor") == [])
check("1 'W/O Power Window Motor' is packaging", q("Regulator Sub-Assy W/O Power Window Motor") == [])
check("1 'W/Motor For Models With Jam Protection' still conditions the car",
      q("Regulator Assy W/Motor For Models With Jam Protection") != [],
      str(q("Regulator Assy W/Motor For Models With Jam Protection")))
check("1 'W/Motor & Auto Up' still conditions the car", q("Regulator Assy W/Motor & Auto Up") != [])
check("1 the exemption is regulator-only: 'W/Motor' on a mirror is a qualifier",
      N.qualifier_phrases("Mirror Assy W/Motor", (), "side-mirrors") != [])

# ------------------------------------------------------------------ 2
base_cur, base_doc = run("toyota", sienna_fixture(), status_table=ST)
check("2 control: the Sienna positive control ships one Verified group",
      len([g for g in base_doc["groups"] if g["cat"] == "window-regulator"]) == 1)

OLD = "6 Cyl 3.3 L GAS, 6 Cyl 3.5 L GAS"
NEW = "FUEL CELL EV (FCEV)"
files = sienna_fixture()
for rec in files[f"raw/{TOY}.jsonl"]:
    for f in rec["fitment"]:
        f["engines"] = [NEW]
        f["raw"] = f["raw"].replace(OLD, NEW)
    rec["evidence_lines"] = [NEW if x == OLD else x for x in rec["evidence_lines"]]
cur, doc = run("toyota", files, status_table=ST)
I = cur.cells_info[(S04, "window-regulator")]
check("2 every record still passes the evidence re-check",
      all(not r.problems for r in cur.records), str([(r.pn, r.problems) for r in cur.records if r.problems][:3]))
check("2 EngineU holds the unparsed key (beside the year page's own engines, review F8)",
      cur.engineu.get(S04) == frozenset({("?", NEW), (6, 3.3, "gas"), (6, 3.5, "gas")}), str(cur.engineu.get(S04)))
check("2 an unparsed engine key on both sides is never cover yes (engines_unparsed, an evidence gap)",
      all(m["cover"] == "maybe" and "engines_unparsed" in m["why"] for m in I["members"].values()),
      str([(k, m["why"]) for k, m in I["members"].items()][:2]))
check("2 no Verified group from an unparsed engine universe",
      not [g for g in doc["groups"] if g["cat"] == "window-regulator"])

# ------------------------------------------------------------------ 3
PASS_REG = "69801-08S01"      # passenger front regulator in the fixture
files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Lt Gray"], (2005, PASS_REG): ["Lt Gray"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 a colour note ('Lt Gray') is not a side: the passenger regulator stays in FR",
      m["slot"].slots == ("FR",) and m["slot"].reason is None, f"{m['slot']}")
check("3 the colour note still restricts the row (cover maybe, colour)",
      m["cover"] == "maybe" and "conditional_notes:colour" in m["why"], str(m["why"]))
check("3 and the restricted cell ships no Verified group", doc["groups"] == [])

files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Left"], (2005, PASS_REG): ["Left"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 'Left' on a passenger part is still a position conflict (blocks every slot)",
      m["slot"].reason == "position_conflict" and set(m["slot"].slots) >= {"FL", "FR"}, f"{m['slot']}")

files = sienna_fixture(extra_notes={(2004, PASS_REG): ["Lt"], (2005, PASS_REG): ["Lt"]})
cur, doc = run("toyota", files, status_table=ST)
m = cur.cells_info[(S04, "window-regulator")]["members"]["toyota:6980108S01"]
check("3 an UNKNOWN clause ('Lt' alone) is read whole and may add a conflict",
      m["slot"].reason == "position_conflict", f"{m['slot']}")
# ------------------------------------------------------------------ 4
# Real Jeep coil 68242286AB (oem-raw@d1108d0 line 769): the page prints
# "2023,  2012-2014, 2007-2010 Chrysler 300" with a doubled space; the
# template collapses it in `raw`. The re-check collapses whitespace on both
# sides (as AUDIT.md's auditor does) and nothing else.
import adapters as A  # noqa: E402
from _util import real  # noqa: E402

coil = real("jeep_d1108d0.jsonl")[0]
rec = A.to_record("www.jeeppartsdeal.com", "mopar", 769, coil)
check("4 real 68242286AB with a doubled space in its evidence passes the re-check",
      A.evidence_problems(rec) == [], str(A.evidence_problems(rec)))
bad = copy.deepcopy(coil)
bad["evidence_lines"] = [x.replace("2023,  2012-2014", "2022,  2012-2014") for x in bad["evidence_lines"]]
check("4 a changed year in the same line still fails",
      A.evidence_problems(A.to_record("www.jeeppartsdeal.com", "mopar", 769, bad)) != [])
bad = copy.deepcopy(coil)
bad["evidence_lines"] = [x.replace("C SRT8", "C  SRT9") for x in bad["evidence_lines"]]
check("4 a changed trim cell still fails",
      A.evidence_problems(A.to_record("www.jeeppartsdeal.com", "mopar", 769, bad)) != [])
# ------------------------------------------------------------------ 5
# Likely groups (§5.16) come only from vehicle-years where the class is a
# cell member; a window switch must resolve to the driver master slot.
# Real oem-raw@d1108d0 output had Likely window-switch groups for the
# passenger switch 4602785AD and for unresolved Mopar switches.
from _util import JEEP, by_pn  # noqa: E402

jeep = real("jeep_94f03a3.jsonl")
sw = [by_pn(jeep, p) for p in ("4602785AD", "4602780AD")]
# §5.16 own-page rule: a second model's own page must list the number
from _util import list_manifest  # noqa: E402
lm_av = list_manifest(JEEP, ("Dodge", "Avenger", 2010), "window-switch", "body-hardware/front-door",
                      [("4602780AD", "Switch - Window And Door Lock", "Window Switch", [], ["Front Left"], True, None)])
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": sw, f"raw/{JEEP}.lists.jsonl": [lm_av]})
lk = {g["pn"][0]: g for g in doc["likely"] if g["cat"] == "window-switch"}
check("5 the Front Driver Side switch 4602780AD (several models) ships a Likely DM group",
      "4602780AD" in lk and ":DM:" in lk["4602780AD"]["id"], str(sorted(lk)))
check("5 the Front Right passenger switch 4602785AD ships no window-switch group", "4602785AD" not in lk)
nopos = by_pn(jeep, "4602780AD")
nopos["position"] = None
nopos["list_location"] = []
ev, out, skip_next = nopos["evidence_lines"], [], False
for x in ev:
    if skip_next:
        skip_next = False
        continue
    if x == "Position":
        skip_next = True
        continue
    out.append(x)
nopos["evidence_lines"] = out
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": [nopos]})
check("5 the same switch with no printed side passes the re-check but ships no Likely group",
      not cur.records[0].problems and not [g for g in doc["likely"] if g["cat"] == "window-switch"],
      str((cur.records[0].problems, [g["id"] for g in doc["likely"]])))

# ------------------------------------------------------------------ 6
import validate as V  # noqa: E402

n = C._likely_note("Toyota", "69804-02150", "plant-specific (US / Japan built)", C.PACK_TEXT["door-module"])
check("6 a door-module Likely note says it is the whole module panel (hub decision P1)",
      "whole door module panel" in n and V._note_ok(n, "likely", ["69804-02150"]) is None, n)
long_ = C._likely_note("Hyundai/Kia", "82471-3Q000-ABCDEFGH", "trim-limited " + "x" * 300, C.PACK_TEXT["motor"])
check("6 an over-long reason is cut, never the template: the note stays valid (V5)",
      len(long_) <= 160 and V._note_ok(long_, "likely", []) is None, long_)
# ------------------------------------------------------------------ 7
# Reports name every namespace-wide gate (the task: say exactly why).
cur, doc = run("toyota", sienna_fixture(), status_table=ST)
check("7 the closed, audited positive control has no namespace gate", C.global_gates(cur) == [],
      str(C.global_gates(cur)))
cur, doc = run("toyota", sienna_fixture())
check("7 without an audit record the gate is named", any("audit gate" in g for g in C.global_gates(cur)))
cur, doc = run("mopar", {f"raw/{JEEP}.jsonl": [by_pn(jeep, "4602780AD")]})
g7 = C.global_gates(cur)
check("7 no manifests and no audit: both named", any("R1 list manifests" in g for g in g7)
      and any("audit gate" in g for g in g7), str(g7))
pg = {"site": "www.nissanpartsdeal.com", "category": "alternator", "pn": "23100-JA00A", "name": "Alternator Assy",
      "seed": {"make": "Nissan", "model": "Altima", "year": 2012}, "evidence_lines": [], "retrieved": "2026-11-05T01:00:00Z",
      "fitment": [{"years": [2012, 2012], "make": "Nissan", "model": "Altima", "trims": [], "engines": [],
                   "options": ["QR25DE"], "raw": "2012 Nissan Altima | | QR25DE"}]}
cur, doc = run("nissan", {"raw/www.nissanpartsdeal.com.jsonl": [pg]})
g7 = C.global_gates(cur)
check("7 a PartsGiant site: unreliable engine cells block every category, option-layout rows are named",
      any("in any category" in g for g in g7) and any("can be coverage" in g and "option column" in g for g in g7),
      str(g7))

# ------------------------------------------- §5.6 other-division rows (2026-11-06)
# fordpartsgiant prints shared platform rows on every twin's page, with the
# variant in a Fit Note: AH6Z-8200-ACP (MKZ grille) on the 2010 Milan page
# reads "Less Appearance Group, With Wood Appearance Package, Lincoln Division
# Derivative" -> not listed for a Mercury or Ford T.
import curate as _C  # noqa: E402
_n = ["Less Appearance Group, With Wood Appearance Package, Lincoln Division Derivative"]
check("division: a Lincoln-division row is not listed for a Mercury", _C._other_division(_n, "Mercury"))
check("division: ... nor for a Ford", _C._other_division(_n, "Ford"))
check("division: it is listed for the Lincoln", not _C._other_division(_n, "Lincoln"))
check("division: no division note, no restriction", not _C._other_division(["With Heavy Duty Trailer Towing"], "Ford"))


# ------------------------------- §5.6 model/body restriction in notes (2026-11-09)
# subarupartsdeal "Fitting Vehicle Options" encodes the body: S = Legacy sedan,
# W = wagon, OBK/SOBK/WOBK = Outback, P/BAJA = Baja (2011 Outback fender
# 57120AJ00/01 = S only; 2015 headlamp 84001AL00A = S.25I only)
F = "Fitting Vehicle Options: "
check("subaru: S only is not for the Outback", _C._subaru_body_excludes([F + "S"], "Outback"))
check("subaru: S.25I (Legacy sedan trim) is not for the Outback", _C._subaru_body_excludes([F + "S.25I"], "Outback"))
check("subaru: OBK is for the Outback, not the Legacy",
      not _C._subaru_body_excludes([F + "OBK"], "Outback") and _C._subaru_body_excludes([F + "OBK"], "Legacy"))
check("subaru: Baja-only mirror rows are not for Legacy/Outback",
      _C._subaru_body_excludes([F + "BAJA +P.S/S +BAJAB.MT"], "Legacy")
      and _C._subaru_body_excludes([F + "P.BAJA"], "Outback") and not _C._subaru_body_excludes([F + "P.BAJA"], "Baja"))
check("subaru: W.(OBK...) qualifiers credit the Outback; SOBK/WOBK exclude the Legacy",
      not _C._subaru_body_excludes([F + "S.SUS# +W.(OBKLTD+OBK6+OBK6LB)"], "Outback")
      and _C._subaru_body_excludes([F + "SOBK +WOBK.(I#+25GTLTD+R#), WOBK.(25GT+25GLI)"], "Legacy"))
check("subaru: engine/transmission codes restrict no model",
      not _C._subaru_body_excludes([F + "EZ30D"], "Legacy") and not _C._subaru_body_excludes([F + "AT.EJ25#"], "Outback"))
check("subaru: other models (Impreza) are not body-restricted here", not _C._subaru_body_excludes([F + "S"], "Impreza"))
# moparpartsgiant brand codes
B = "Fitting Vehicle Options: 48 - SEDAN TYPE #8, C - CHRYSLER, F - BRAND AWD"
check("mopar: a C - CHRYSLER row is not for a Dodge", _C._brand_codes_exclude([B], "Dodge"))
check("mopar: ... but is for the Chrysler", not _C._brand_codes_exclude([B], "Chrysler"))
check("mopar: E - DODGE AWD names Dodge", not _C._brand_codes_exclude(["49 - HATCHBACK TYPE #2, D - DODGE, E - DODGE AWD"], "Dodge"))
check("mopar: engine codes name no brand", not _C._brand_codes_exclude(["EGA - 6 Cyl 3.3L OHV, EGH - 6 Cyl 3.8L OHV"], "Dodge"))
# catalog/feed model names in notes (VW shared pages, Toyota hybrids)
_cur = object.__new__(_C.Curation)
_cur.ns = "vag"
_cur.ns_models = {"golf", "jetta", "gti", "r32", "passat"}
_cur.class_feed_models = {}
_cur.t_sources = {}
check("names: a 'Jetta; Sedan' note is not for a Golf",
      _cur.note_excludes(["Jetta; Sedan; All; Diesel Engine; Auto Transmission"], ("Volkswagen", "Golf", 2003)))
check("names: ... but is for the Jetta",
      not _cur.note_excludes(["Jetta; Sedan; All; Diesel Engine"], ("Volkswagen", "Jetta", 2003)))
check("names: 'Golf, GTI, R32; Power' is for the GTI", not _cur.note_excludes(["Golf, GTI, R32; Power; Left"], ("Volkswagen", "GTI", 2007)))
check("names: a note naming no model restricts nothing", not _cur.note_excludes(["2 Door, Power"], ("Volkswagen", "Golf", 2003)))
_t = object.__new__(_C.Curation)
_t.ns, _t.ns_models, _t.t_sources = "toyota", {"camry", "corolla"}, {}
_t.class_feed_models = {("x", "c"): {("Toyota", "Camry"), ("Toyota", "Camry Hybrid")}}
check("names: 'Camry Hybrid; SE' is not for a gas Camry (longest name first)",
      _t.note_excludes(["Camry Hybrid; SE; Without Audio-Avn/6 Speaker"], ("Toyota", "Camry", 2015)))
check("names: ... but is for the Camry Hybrid",
      not _t.note_excludes(["Camry Hybrid; SE; Without Audio-Avn/6 Speaker"], ("Toyota", "Camry Hybrid", 2015)))
check("names: a note naming both keeps both",
      not _t.note_excludes(["Camry Hybrid; Right; With HID;Camry; With HID; Right"], ("Toyota", "Camry", 2012)))


# ---------------------- Subaru Outback-family codes and market notes (hub 2026-11-09)
# the research sample's 4 WRONG: 2000-04 BE/BH numbers whose option column
# names only Outback codes, credited to 'Legacy' by the product page
for _pn, _n in (("72311AE06A", [F + "*W.OBKLTD.AT"]),
                ("72311AE08D", [F + "OBK6 +SUS6 +OBK6S"]),
                ("91031AE41AFR", ["C4", F + "W.OBKLTD.AT"]),
                ("91031AE43BGA", [F + "OBK6 +SUS6 +OBK6S +OBK6LB +OBKLTD +SUSLTD"])):
    check(f"subaru {_pn}: Outback-only codes are not for the Legacy (incl. Legacy Wagon)",
          _C._subaru_body_excludes(_n, "Legacy") and _C._subaru_body_excludes(_n, "Legacy Wagon"))
    check(f"subaru {_pn}: ... and are for the Outback", not _C._subaru_body_excludes(_n, "Outback"))
check("subaru: S.SUS6 +W.OBK6 (Outback sedan + wagon) is Outback-only",
      _C._subaru_body_excludes([F + "S.SUS6 +W.OBK6"], "Legacy") and not _C._subaru_body_excludes([F + "S.SUS6 +W.OBK6"], "Outback"))
check("subaru: S +W.(L+OBK) still credits the Legacy", not _C._subaru_body_excludes([F + "S +W.(L+OBK)"], "Legacy"))
check("market: 'FOR CANADA' / 'FOR CANADA,CHILE' (72311AE08D 2002-03 rows) are not for US cars",
      _C._market_excludes(["FOR CANADA"]) and _C._market_excludes(["FOR CANADA,CHILE"]))
check("market: Korea/Taiwan-spec-only notes are not for US cars",
      _C._market_excludes(["KOREA SPEC&PREMIUM PACKAGE&W/SEAT HEATER / TAIWAN SPEC&PREMIUM PACKAGE&W/SEAT HEATER"]))
check("market: a note with a non-market alternative keeps the row",
      not _C._market_excludes(["CANADA SPEC / CANADA SPEC&W/SEAT HEATER / SEAT HEATER-WITH(DRIVER & PASSENGER)"]))
check("market: plant notes are not markets", not _C._market_excludes(["Japan Built"]) and not _C._market_excludes(["US Built"]))
check("market: a US note keeps the row", not _C._market_excludes(["FOR USA, CANADA"]))

done("test_regressions")
