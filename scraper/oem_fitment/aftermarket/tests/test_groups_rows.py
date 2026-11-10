#!/usr/bin/env python3
"""groups_rows.py (GSP + 1A Auto curation), offline. Run:
    python3 scraper/oem_fitment/aftermarket/tests/test_groups_rows.py

Records come from the real fixture pages through the real parsers, plus
edited copies for the refusal cases. Also guards the owner's 1A rule
("1A im not selling the part fitment portion"): the app's aftermarket render
path has no Pro branch, and the curated output carries no price, description
or image.
"""
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import groups_rows as R  # noqa: E402
import gspnorthamerica as gsp  # noqa: E402
import oneaauto  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


class Names:  # offline stand-in for groups_am.Names (lot names = feed names)
    def canon(self, make, model):
        return (make, model, True)


class AllObs(dict):  # offline: every engine size "seen" on the lots, unless a test says otherwise
    def get(self, k, default=None):
        return {round(x / 10, 1) for x in range(5, 90)}


REAL_LOAD_OBSERVED = R.load_observed
R.load_observed = lambda *a, **k: AllObs()
FX = HERE / "fixtures"
GENS = {"honda|accord": [[1990, 1993], [1994, 1997], [1998, 2002], [2003, 2007], [2008, 2012]],
        "honda|crv": [[2017, 2022]], "honda|pilot": [[2016, 2022]]}


def B(recs, names, site, gens=None):
    return R.build(recs, names, site, gens=GENS if gens is None else gens)
G0 = gsp.parse_product("https://gspnorthamerica.com/products/ncv36167xd",
                       (FX / "gsp_product_ncv36167xd.html").read_text(), "2026-11-09T21:00:00Z", "cv-axle")
A0 = oneaauto.parse_product("https://www.1aauto.com/x-strut-and-spring-assembly-trq-sca27339/i/1asts01815",
                            (FX / "oneaauto_product_1asts01815.html").read_text(), "2026-11-09T21:00:00Z", "strut")


def gsp_rec(pn, rows, engines=("2.4",), pos="Front Left", flags=()):
    r = copy.deepcopy(G0)
    r.update(aftermarket_pn=pn, title_engines=list(engines), title_position=pos, flags=list(flags),
             applications=[{"years": [lo, hi], "make": mk, "model": md, "submodel": sub, "position": pos,
                            "engine": "", "type": "", "notes": "", "raw": ""} for lo, hi, mk, md, sub in rows])
    return r


# ---- GSP
d = B([G0], Names(), "gspnorthamerica.com")
check("real NCV36167XD refused (duplicate 2019 row)", d["summary"]["groups"] == 0
      and d["summary"]["refused_units"].get("cv-axle:flag") == 1)
clean = gsp_rec("NCV1", [(2017, 2022, "Honda", "CR-V", "")], engines=("1.5", "2.4"))
d = B([clean], Names(), "gspnorthamerica.com")
g = d["groups"][0]
check("clean unit -> one Likely aftermarket group per position", d["summary"]["groups"] == 1 and g["tier"] == "likely"
      and g["src"] == "aftermarket" and g["position"] == "front left" and g["id"] == "am:gsp:cv-axle:NCV1:front-left")
check("title engines go on every app, no drive/trans", g["apps"] == [["Honda", "CR-V", 2017, 2022, "1.5L"],
                                                                  ["Honda", "CR-V", 2017, 2022, "2.4L"]])
check("cv-axle note leaves drive to the app's own check-drive line (D1)", "trim and suspension" in g["note"]
      and "drive" not in g["note"].lower() and "Transmission" in g["note"]
      and "GSP NCV1" in g["note"])
other = gsp_rec("NCV2", [(2019, 2019, "Honda", "CR-V", "")])
d = B([clean, other], Names(), "gspnorthamerica.com")
check("two units for one corner: that year is dropped from both", d["groups"][0]["apps"][0][2:4] == [2017, 2018]
      and d["groups"][0]["apps"][-1][2:4] == [2020, 2022] and all(x["unit"] != "NCV2" for x in d["groups"]))
trim = gsp_rec("NCV3", [(2019, 2019, "Honda", "CR-V", "EX")])
d = B([clean, trim], Names(), "gspnorthamerica.com")
check("a trim row is refused but still claims (splits the 2019 corner)",
      not any(a[2] <= 2019 <= a[3] for a in d["groups"][0]["apps"]) and d["refused_rows"].get("submodel") == 1)
right = gsp_rec("NCV4", [(2019, 2019, "Honda", "CR-V", "")], pos="Front Right")
d = B([clean, right], Names(), "gspnorthamerica.com")
check("other side does not conflict", len(d["groups"]) == 2 and d["groups"][0]["apps"][0][2:4] == [2017, 2022])
bare = gsp_rec("NCV5", [(2019, 2019, "Honda", "CR-V", "")], pos="Front")
d = B([clean, bare], Names(), "gspnorthamerica.com")
check("a bare 'Front' unit conflicts with a front-left unit", not any(a[2] <= 2019 <= a[3] for g in d["groups"]
                                                                     for a in g["apps"]))
for name, rec, why in [
        ("no title engine", gsp_rec("X1", [(2010, 2012, "Honda", "Civic", "")], engines=()), "no_title_engine"),
        ("AWD in the title", gsp_rec("X2", [(2010, 2012, "Honda", "Civic", "")], engines=("AWD",)), "title_token"),
        ("duplicate rows flag", gsp_rec("X4", [(2010, 2012, "Honda", "Civic", "")], flags=["duplicate_rows"]), "flag"),
        ("no position", gsp_rec("X5", [(2010, 2012, "Honda", "Civic", "")], pos=""), "title_position")]:
    d = B([rec], Names(), "gspnorthamerica.com")
    check(f"GSP refuses: {name}", not d["groups"] and any(k.endswith(":" + why) for k in d["summary"]["refused_units"]))

mm = gsp_rec("X6", [(1999, 2003, "Acura", "TL", ""), (1998, 2002, "Honda", "Accord", "")], engines=("3.0",))
OBS = {("Acura", "tl", y): {3.2} for y in range(1999, 2004)}
OBS.update({("Honda", "accord", y): {2.3, 3.0} for y in range(1998, 2003)})
d = R.build([mm], Names(), "gspnorthamerica.com", observed=OBS)
check("multi-model unit: a model-year whose lot cars include an engine outside the title is dropped "
      "(Accord 2.3 present) and TL (no 3.0) too", not d["groups"]
      and d["refused_rows"].get("no_lot_car_with_title_engine") == 5 and d["refused_rows"].get("lot_engine_outside_unit_title") == 5)
OBSa = {("Acura", "tl", y): {3.2} for y in range(1999, 2004)}
OBSa.update({("Honda", "accord", y): {3.0} for y in range(1998, 2003)})
d = R.build([mm], Names(), "gspnorthamerica.com", observed=OBSa)
check("multi-model unit: kept where every lot car of the model-year has a title engine",
      {(a[1], a[4]) for a in d["groups"][0]["apps"]} == {("Accord", "3.0L")})
sf = gsp_rec("X13", [(2017, 2018, "Hyundai", "Santa Fe", ""), (2013, 2018, "Hyundai", "Santa Fe Sport", "")],
             engines=("2.0", "2.4"))
OBS3 = {("Hyundai", "santafe", y): {2.0, 2.4} for y in (2017, 2018)}
OBS3.update({("Hyundai", "santafesport", y): {2.0, 2.4} for y in range(2013, 2019)})
d = R.build([sf], Names(), "gspnorthamerica.com", observed=OBS3)
check("round-3 regression: base 'Santa Fe' rows refused next to 'Santa Fe Sport' (yards lump them)",
      d["groups"] and {a[1] for a in d["groups"][0]["apps"]} == {"Santa Fe Sport"}
      and d["refused_rows"].get("sibling_model_name") == 1)
spec = gsp_rec("X14", [(2017, 2022, "Honda", "CR-V", "")], engines=("1.5", "2.4"))
spec["specs"] = {"Inboard Spline Quantity": "27", "Outboard Spline Quantity": "30", "Compressed Length (MM)": "671"}
note = R.build([spec], Names(), "gspnorthamerica.com")["groups"][0]["note"]
check("cv-axle note carries GSP's own physical check (splines, length)",
      "inboard splines 27, outboard splines 30, compressed length 671 mm" in note and "drive" not in note.lower())
ct = gsp_rec("X11", [(2017, 2020, "Cadillac", "CT6", "")], engines=("2.0", "4.2"))
OBS2 = {("Cadillac", "ct6", 2017): {2.0, 3.6}, ("Cadillac", "ct6", 2018): {2.0, 3.0},
        ("Cadillac", "ct6", 2019): {2.0, 4.2}, ("Cadillac", "ct6", 2020): {4.2}}
apps = sorted(map(tuple, R.build([ct], Names(), "gspnorthamerica.com", observed=OBS2)["groups"][0]["apps"]))
check("per-year engines: CT6 4.2L only from 2019 (lot-observed), 2.0L through 2019",
      apps == [("Cadillac", "CT6", 2017, 2019, "2.0L"), ("Cadillac", "CT6", 2019, 2020, "4.2L")])
nd = R.build([gsp_rec("X12", [(2010, 2011, "Honda", "Fit", "")], engines=("1.5",))], Names(), "gspnorthamerica.com",
             observed={})
check("no decoded lot car for the model-year -> row dropped", not nd["groups"] and nd["refused_rows"].get("no_decoded_lot_car") == 2)
sm1 = gsp_rec("X7", [(2017, 2022, "Honda", "CR-V", "")], engines=("1.5", "2.4"))
check("single-model GSP unit keeps its title engines", {a[4] for a in R.build([sm1], Names(), "gspnorthamerica.com")["groups"][0]["apps"]}
      == {"1.5L", "2.4L"})

# ---- donor drive gate (d), hub 2026-11-10: every corner x every drive value
CASES = {  # drive_type (vPIC wording) -> (front, rear)
    "FWD/Front-Wheel Drive": ("pass", "exclude"), "Front-Wheel Drive": ("pass", "exclude"),
    "RWD/Rear-Wheel Drive": ("exclude", "pass"), "Rear-Wheel Drive": ("exclude", "pass"),
    "AWD/All-Wheel Drive": ("pass", "pass"), "4WD/4-Wheel Drive/4x4": ("pass", "pass"),
    "4x4": ("pass", "pass"), "4x2": ("exclude", "check"), "2WD": ("exclude", "check"),
    "RWD/Rear-Wheel Drive 4x2": ("exclude", "pass"), "": ("check", "check"), "Part-time": ("check", "check"),
    "FWD/RWD": ("check", "check"),
}
bad = [(dt, ax) for dt, (f, r) in CASES.items() for ax, want in (("front", f), ("rear", r))
       if R.axle_donor_verdict(ax, dt) != want]
check(f"drive gate (d): corner x drive table, {len(CASES) * 2} cases (failures: {bad})", not bad)
check("drive gate (d): unknown axle is never excluded", R.axle_donor_verdict("", "RWD") == "check")
ga = R.build([gsp_rec("X8", [(2017, 2022, "Honda", "CR-V", "")], engines=("1.5",), pos="Rear Left")],
             Names(), "gspnorthamerica.com")["groups"][0]
check("cv-axle groups carry driven_axle from the corner", ga["driven_axle"] == "rear")
# ---- unit-level generation guard
mg = gsp_rec("X9", [(1998, 2002, "Honda", "Accord", ""), (2003, 2007, "Honda", "Accord", "")], engines=("2.4",))
d = R.build([mg], Names(), "gspnorthamerica.com")
check("a unit whose rows for one model span two generations is refused",
      not d["groups"] and d["summary"]["refused_units"].get("cv-axle:unit_spans_generations") == 1)
one = gsp_rec("X10", [(2003, 2004, "Honda", "Accord", ""), (2005, 2007, "Honda", "Accord", "")], engines=("2.4",))
check("rows inside one generation pass", R.build([one], Names(), "gspnorthamerica.com")["groups"] != [])

# ---- lot snapshot pinning (hub 2026-11-10)
t1, m1 = R.lot_snapshot("HEAD")
t2, m2 = R.lot_snapshot("HEAD")
check("lot snapshot from a commit is reproducible (same sha256 twice) and names the commit",
      m1 == m2 and len(m1["ref"]) == 40 and all(len(h) == 64 for h in m1["sha256"].values()))
check("observed engines come from the given snapshot texts", REAL_LOAD_OBSERVED({R.LOT_FILES[0]: json.dumps(
    {"fields": ["id", "year", "make", "model"], "vehicles": [[1, 2010, "Honda", "Fit"]]}), R.LOT_FILES[1]: json.dumps(
    {"extraFields": ["photo", "color", "engine"], "extras": {"1": ["", "", "1.5L 4-cyl"]}})}) == {("Honda", "fit", 2010): {1.5}})

# ---- 1A Auto
d = B([A0], Names(), "www.1aauto.com")
g = d["groups"][0] if d["groups"] else {}
check("real 1A unit -> group labelled 1A Auto + item number", g.get("unit") == "1ASTS01815"
      and g.get("label") == "1A Auto front right" and g.get("apps") == [["Honda", "Pilot", 2016, 2022, ""]])
check("1A group is never Pro-gated", g.get("pro_gated") is False)


def a_rec(sku, rows, brand="TRQ", bpn="SCA1"):
    r = copy.deepcopy(A0)
    r.update(aftermarket_pn=sku, house_brand=brand, house_brand_pn=bpn,
             applications=[{"years": [lo, hi], "make": "Honda", "model": "Accord", "type": "", "engine": "",
                            "notes": "", "raw": "", "description": f"Honda Accord {q}{p} Strut & Spring Assembly {brand} {bpn}"}
                           for lo, hi, q, p in rows])
    return r


u1 = a_rec("1A1", [(2008, 2012, "", "Front Driver Side")])
u2 = a_rec("1A2", [(2010, 2010, "Sport ", "Front Driver Side")], bpn="SCA2")
d = B([u1, u2], Names(), "www.1aauto.com")
check("1A: a trim-qualified unit of the same brand splits that year",
      d["groups"][0]["apps"] == [["Honda", "Accord", 2008, 2009, ""], ["Honda", "Accord", 2011, 2012, ""]]
      and d["refused_rows"].get("q: Sport") == 1)
u3 = a_rec("1A3", [(2010, 2010, "", "Front Driver Side")], brand="KYB Excel-G", bpn="339999")
d = B([u1, u3], Names(), "www.1aauto.com")
check("1A: another brand's unit for the same corner is an equivalent, not a split",
      d["groups"][0]["apps"] == [["Honda", "Accord", 2008, 2012, ""]] and len(d["groups"]) == 2)
u4 = a_rec("1A4", [(2008, 2012, "V6 3.0L ", "Front Driver Side")], bpn="SCA4")
d = B([u4], Names(), "www.1aauto.com")
check("1A: an engine qualifier refuses too (V6 3.2L does not exclude a Type-S)", not d["groups"]
      and d["refused_rows"].get("q: V6 3.0L") == 1)
# shakeout 2026-11-09 regressions
fwd = a_rec("1AW", [(2019, 2022, "Front Wheel Drive ", "Front Passenger Side")])
_, _, rows = R.oneaauto_rows(fwd)
check("drive phrase: side kept from the LAST position phrase, drive is a refused qualifier",
      rows[0][1] == "front right" and rows[0][3] == "qualifier:Front Wheel Drive")
check("drive-qualified unit yields no group", not B([fwd], Names(), "www.1aauto.com")["groups"])
sib = a_rec("1AS", [(2003, 2004, "", "Rear Driver Side"), (2005, 2007, "LX ", "Rear Driver Side")])
d = B([sib], Names(), "www.1aauto.com")
check("unqualified row refused when the same unit qualifies the same model elsewhere",
      not d["groups"] and d["refused_rows"].get("sibling_row_qualified") == 1)
plain = a_rec("1AP", [(2003, 2004, "", "Front Driver Side")])
opt = a_rec("1AO", [(1997, 2001, "without Electronic Suspension ", "Front Driver Side")], bpn="SCA9")
d = B([plain, opt], Names(), "www.1aauto.com")
check("strut: a model the source ever qualifies by suspension option refuses its plain rows",
      not d["groups"] and d["refused_rows"].get("model_has_suspension_options") == 1)
mv = copy.deepcopy(plain)
mv["interchange_numbers"] = [{"brand": "KYB", "pn": "SR4150"}, {"brand": "KYB", "pn": "SR4054"}]
check("one brand cross-referenced to two numbers -> unit refused", not B([mv], Names(), "www.1aauto.com")["groups"])
lr = copy.deepcopy(plain)
lr["interchange_numbers"] = [{"brand": "Hollander", "pn": "527-59373L"}, {"brand": "Hollander", "pn": "527-59373R"}]
check("a left/right pair is not a merged variant", B([lr], Names(), "www.1aauto.com")["groups"] != [])
for q in ("Sedan ", "without Electronic Suspension ", "Hybrid ", "From 1/01/06 Production Date "):
    d = B([a_rec("1AQ", [(2008, 2012, q, "Front Driver Side")])], Names(), "www.1aauto.com")
    check(f"1A refuses the qualifier {q.strip()!r}", not d["groups"])
d = B([a_rec("1AF", [(2008, 2012, "", "Front Driver Side")])] , Names(), "www.1aauto.com")
bad = copy.deepcopy(A0)
bad["flags"] = ["slug_not_category"]
check("1A refuses a flagged unit", not B([bad], Names(), "www.1aauto.com")["groups"])

# ---- generation spans (hub 2026-11-09)
cross = a_rec("1AG", [(2006, 2009, "", "Front Driver Side")])
d = B([cross], Names(), "www.1aauto.com")
check("a row crossing a generation boundary (Accord 2006-09) is refused", not d["groups"]
      and d["refused_rows"].get("generation_span") == 1)
inside = a_rec("1AI", [(2008, 2012, "", "Front Driver Side")])
check("a row inside one generation passes", B([inside], Names(), "www.1aauto.com")["groups"] != [])
d = B([inside], Names(), "www.1aauto.com", gens={})
check("no generation entry: a 5-year span passes", d["groups"] != [])
long_ = a_rec("1AL", [(2001, 2009, "", "Front Driver Side")])
check("no generation entry: a 9-year span is refused", not B([long_], Names(), "www.1aauto.com", gens={})["groups"])
check("the app's own table is loaded", "toyota|camry" in R.load_generations())


# ---- junkyard-demand lines: grammar on real 1A descriptions (probe 2026-11-09)
def d_rec(sku, cat, desc, years=(2003, 2007), make="Honda", model="Accord", brand="TRQ", bpn="X1", ic=None):
    r = copy.deepcopy(A0)
    r.update(aftermarket_pn=sku, category=cat, house_brand=brand, house_brand_pn=bpn, flags=[],
             interchange_numbers=ic or [],
             applications=[{"years": list(years), "make": make, "model": model, "type": "", "engine": "",
                            "notes": "", "raw": "", "description": f"{desc} {brand} {bpn}"}])
    return r


NOFL = {}
hl = d_rec("1AH", "headlight", "Honda Accord Passenger Side Headlight Assembly", years=(2003, 2005))
d = R.build([hl], Names(), "www.1aauto.com", gens=GENS, facelifts=NOFL)
check("side-only position parsed ('Passenger Side' -> right)", d["groups"] and d["groups"][0]["position"] == "right")
d = R.build([d_rec("1AH2", "headlight", "Honda Accord Passenger Side Headlight Assembly")], Names(), "www.1aauto.com",
            gens=GENS, facelifts={"accord": [2006, 2011]})
check("lamp row crossing a facelift (Accord 2003-07 over 2006) is refused", not d["groups"]
      and d["refused_rows"].get("facelift_span") == 1)
st = d_rec("1AST", "strut", "Honda Accord Front Driver Side Strut & Spring Assembly")
check("facelift guard applies to lamps only", R.build([st], Names(), "www.1aauto.com", gens=GENS,
                                                      facelifts={"accord": [2006]})["groups"] != [])
tl = d_rec("1AT", "tail-light", "Honda Accord Sedan Driver Side Tail Light", years=(2006, 2007))
d = R.build([tl], Names(), "www.1aauto.com", gens=GENS, facelifts=NOFL)
check("body-qualified row waits for the app body gate (refused today)", not d["groups"]
      and d["refused_rows"].get("body_gate_pending") == 1)
mi = d_rec("1AM", "mirror", "Honda Accord Sedan Passenger Side Power Paint to Match Mirror", years=(1998, 2002))
_, _, rows = R.oneaauto_rows(mi)
check("mirror grammar: body sedan, option power, cosmetic finish, kind mirror",
      rows[0][4] == {"kind": "mirror", "options": ("power",), "body": "sedan", "cosmetic": True})
dh = d_rec("1AD", "door-handle-ext", "Honda Accord 4 Door Front Driver Side with Manual Door Locks Black Exterior Door Handle",
           years=(1990, 1993))
_, _, rows = R.oneaauto_rows(dh)
check("handle grammar: 4 Door body, manual-locks option, color cosmetic",
      rows[0][4]["options"] == ("manual door locks",) and rows[0][4]["cosmetic"] and rows[0][4]["kind"] == "exterior door handle"
      and rows[0][1] == "front left")
pm = d_rec("1AP2", "mirror", "Honda Accord Passenger Side Power Heated Mirror", years=(1998, 2002))
pn = d_rec("1AP3", "mirror", "Honda Accord Passenger Side Power Mirror", years=(1998, 2002), bpn="X2")
d = R.build([pm, pn], Names(), "www.1aauto.com", gens=GENS, facelifts=NOFL)
check("units told apart by stated options both publish, each 'if equipped'",
      sorted(g["if_equipped"] for g in d["groups"]) == [["heated", "power"], ["power"]]
      and all(g["option"] and "If equipped:" in g["note"] for g in d["groups"]))
pl = d_rec("1AP4", "mirror", "Honda Accord Passenger Side Mirror", years=(1998, 2002), bpn="X3")
d = R.build([pm, pl], Names(), "www.1aauto.com", gens=GENS, facelifts=NOFL)
check("a plain unit next to an option unit for one corner is a split (both dropped)", not d["groups"])
bt = d_rec("1AB", "blower-motor", "Acura TL HVAC Blower Motor Assembly", years=(2004, 2008), make="Acura", model="TL")
d = R.build([bt], Names(), "www.1aauto.com", gens={}, facelifts=NOFL)
check("plain blower row (no position) -> group", d["groups"] and d["groups"][0]["position"] == "")
un = d_rec("1AU", "mirror", "Honda Accord Passenger Side Power Mirror with Blind Spot Detection", years=(1998, 2002))
check("a qualifier outside the grammar refuses", not R.build([un], Names(), "www.1aauto.com", gens=GENS,
                                                             facelifts=NOFL)["groups"])
fog = d_rec("1AF2", "fog-light", "Honda Civic Sedan L4 2.4L Driver Side Fog Light", make="Honda", model="Civic", years=(2013, 2015))
check("engine words outside the grammar refuse (fog light 'L4 2.4L')",
      not R.build([fog], Names(), "www.1aauto.com", gens={}, facelifts=NOFL)["groups"])
# rule 5: separators and case only (hub 2026-11-09)
check("rule 5: 47-1578R == 471578R (one number)", not R.merged_variants(
    [{"brand": "CARDONE Reman", "pn": "47-1578R"}, {"brand": "Cardone reman", "pn": "471578r"}]))
check("rule 5: 821578AR next to 47-1578R is two numbers (refuse)", R.merged_variants(
    [{"brand": "CARDONE Reman", "pn": "821578AR"}, {"brand": "CARDONE Reman", "pn": "47-1578R"}]))
check("rule 5: Honda 33551SDAA32 == 33551-SDA-A32", not R.merged_variants(
    [{"brand": "Honda", "pn": "33551SDAA32"}, {"brand": "Honda", "pn": "33551-SDA-A32"}]))
check("rule 5: real Honda mirror variants refuse", R.merged_variants(
    [{"brand": "Honda", "pn": "76200-S84-A21ZF"}, {"brand": "Honda", "pn": "76200-S4K-A41ZF"}]))


# ---- emitted category ids are the app's (hub 2026-11-09)
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parents[1]))
import junkyard_scraper as JS  # noqa: E402
import crawl as CR  # noqa: E402
cm = set(re.findall(r'^\s{4}"([a-z0-9-]+)": \{"label"', (HERE.parents[1] / "coverage_matrix.py").read_text(), re.M))
PENDING_WAVE2 = {"door-handle-int", "backup-camera", "tailgate-handle"}   # ops/interchange.md §10, wave 2
known = set(JS.INTERCHANGE_PART_CATEGORIES) | {c for v in CR.TIERS.values() for c in v} | cm | PENDING_WAVE2
emitted = {R.CAT_OUT.get(c, c) for c in oneaauto.CATEGORIES} | {R.CAT_OUT.get(c, c) for c in gsp.CATEGORIES}
check(f"every emitted category id is an app/tier/pending id (unknown: {sorted(emitted - known)})", emitted <= known)
lamp = R.build([d_rec("1AH9", "headlight", "Honda Accord Passenger Side Headlight Assembly", years=(2003, 2005))],
               Names(), "www.1aauto.com", gens=GENS, facelifts={})["groups"][0]
check("headlight groups emit cat 'headlights' and an id to match", lamp["cat"] == "headlights"
      and lamp["id"].startswith("am:1a:headlights:"))

many = d_rec("1AX", "mirror", "Honda Accord Passenger Side Power Folding Heated Memory with Turn Signal Power Manual with Power Door Locks Mirror",
             years=(1998, 2002))
check("more than 6 options -> unit refused (app limit)", not R.build([many], Names(), "www.1aauto.com", gens=GENS,
                                                                    facelifts={})["groups"])
check("option labels fit the app's shape (<=60 chars, no markup)",
      all(len(lab) <= 60 and "<" not in lab for _, lab in R.OPTION_Q))

# ---- release (hub 2026-11-10): shipped categories == AM_RELEASED, gap makes off, pinned
check("GSP SHIP_CATS equals junkyard_scraper.AM_RELEASED['gspnorthamerica']",
      set(R.SHIP_CATS["gspnorthamerica.com"]) == set(JS.AM_RELEASED.get("gspnorthamerica", ())))
_sh = R.ship({"site": "gspnorthamerica.com", "raw": "x", "sha256": "y", "lot_snapshot": {},
              "groups": [{"id": "a", "cat": "cv-axle", "tier": "likely", "src": "aftermarket", "label": "GSP", "unit": "U",
                          "note": "n", "retrieved": "r", "driven_axle": "front",
                          "apps": [["Isuzu", "Rodeo", 2001, 2002, "3.2L"], ["Honda", "CR-V", 2017, 2018, "1.5L"]]},
                         {"id": "b", "cat": "strut", "tier": "likely", "src": "aftermarket", "label": "GSP", "unit": "V",
                          "note": "n", "retrieved": "r", "apps": [["Honda", "Civic", 2010, 2011, ""]]}]})
check("ship(): released cats only, gap-make apps dropped, driven_axle kept",
      [g["id"] for g in _sh["groups"]] == ["a"] and _sh["groups"][0]["apps"] == [["Honda", "CR-V", 2017, 2018, "1.5L"]]
      and _sh["groups"][0]["driven_axle"] == "front" and _sh["skipped"] == {"cat_not_released:strut": 1, "gap_make_apps": 1})

# ---- facts only; owner's free-fitment rule
out = json.dumps(B([A0, u1, u4], Names(), "www.1aauto.com"))
check("1A output carries no price / description / image / interchange numbers",
      not re.search(r'"(?:price|description|image|images|body_html|interchange_numbers)"', out)
      and "SCA27339" not in out and "Strut & Spring" not in out)
app = (HERE.parents[3] / "docs" / "app.js").read_text()


def fn_body(name):
    i = app.index(f"function {name}(")
    j = app.index("\n}\n", i)
    return app[i:j]


paths = [fn_body(n) for n in ("pfAmRows", "pfAmSourceText", "pfAppMatches", "pfAmEngineAgrees")]
check("app aftermarket render path has no Pro branch (1A rows render the same for free and Pro)",
      not any(re.search(r"isPro|\bpro\b|entitle|subscri", b, re.I) for b in paths))

print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
