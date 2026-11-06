#!/usr/bin/env python3
"""Offline tests for aftermarket/groups_am.py (DB Electrical -> Likely unit
groups). Synthetic records for the rules; plus, when origin/oem-raw is
fetched, a random sample of built pairs re-checked against the raw
Applications List rows. Run: python3 scraper/oem_fitment/aftermarket/tests/test_groups_am.py"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import groups_am as GA  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def app(make, model, y, eng, typ="Auto and Light Truck"):
    return {"years": [y, y], "make": make, "type": typ, "model": model, "engine": eng, "notes": "",
            "raw": f"{make} | {typ} | {model} | {y} | {eng}"}


def rec(pn, cat, apps, amps=None, flags=(), fits="", utype=None):
    specs = {"Unit Type": utype or cat.title()}
    if amps:
        specs["Amperage"] = str(amps)
    return {"site": GA.SITE, "category": cat, "aftermarket_pn": pn, "applications": apps, "specs": specs,
            "fits_text": fits, "flags": list(flags), "oe_numbers": [{"brand": "BMW", "pn": "12-31-7-000-000"}],
            "lester": [], "product_url": f"https://{GA.SITE}/products/{pn}.html", "retrieved": "2026-11-05T00:00:00Z",
            "title": f"{cat} {pn}"}


LOT = {("MINI", "Cooper"), ("Ford", "F-250 Super Duty"), ("Ford", "F-150"), ("Chevrolet", "Silverado 1500"),
       ("GMC", "Sierra 1500"), ("Isuzu", "Rodeo")}
N = GA.Names(LOT)


def ids(doc):
    return {g["id"]: g for g in doc["groups"]}


# 1. amperage: two units for one vehicle-year are two groups, never merged
d = GA.build([rec("400-1", "alternator", [app("Mini", "COOPER", 2007, "1.6L")], 105),
              rec("400-2", "alternator", [app("Mini", "Cooper", 2007, "1.6L")], 120)], N)
g = ids(d)
check("two amperages stay two groups", set(g) == {"am:dbe:alternator:400-1", "am:dbe:alternator:400-2"})
check("amperage split condition on both", all(any(c.startswith("amperage_split:105A/120A") for c in x["conditions"])
                                             for x in g.values()), str([x["conditions"] for x in g.values()]))
check("tier likely, src aftermarket", all(x["tier"] == "likely" and x["src"] == "aftermarket" for x in g.values()))
check("note names amperage and says aftermarket", all("amperage" in x["note"] and "not the carmaker" in x["note"]
                                                       for x in g.values()))
check("model canonicalised to lot name", g["am:dbe:alternator:400-1"]["apps"][0][:4] == ["MINI", "Cooper", 2007, 2007])

# 2. flagged records refused; harmless flags kept
d = GA.build([rec("400-3", "alternator", [app("Ford", "F-150", 2005, "4.6L V8")], 130,
                  flags=["unparsed_application_row:x"]),
              rec("400-4", "alternator", [app("Ford", "F-150", 2005, "4.6L V8")], 130,
                  flags=["item_number_differs:400-9"]),
              rec("400-5", "alternator", [app("Ford", "F-150", 2005, "4.6L V8")], 130,
                  flags=["no_carmaker_oe_numbers", "unparsed_replaces_row:X | 1"])], N)
check("unparsed_application_row and item_number_differs refused",
      d["summary"]["refused"] == {"flag:unparsed_application_row": 1, "flag:item_number_differs": 1},
      str(d["summary"]["refused"]))
check("harmless flags kept", [x["id"] for x in d["groups"]] == ["am:dbe:alternator:400-5"])

# 3. combined makes never guessed
d = GA.build([rec("400-6", "alternator", [app("CHEVROLET / GMC", "SILVERADO 1500", 2004, "5.3L V8")], 145)], N)
check("combined make skipped and reported", not d["groups"] and sum(d["combined_makes"].values()) == 1)

# 4. engine gate in membership
d = GA.build([rec("400-7", "alternator", [app("Ford", "F-150", 2005, "4.6L V8"), app("Ford", "F-150", 2006, "")], 130)], N)
cars = [(0, "Ford", "F-150", 2005, "4.6L 8-cyl"), (1, "Ford", "F-150", 2005, "5.4L 8-cyl"),
        (2, "Ford", "F-150", 2005, ""), (3, "Ford", "F-150", 2006, "5.4L 8-cyl"), (4, "Ford", "F-150", 2007, "4.6L 8-cyl")]
m = dict(GA.members(d, cars)["am:dbe:alternator:400-7"])
check("engine agreeing car is a plain member", m.get(0) == "")
check("other-engine car excluded", 1 not in m)
check("undecoded car kept with condition", m.get(2) == "engine_unconfirmed")
check("row without engine kept with condition", m.get(3) == "engine_unlisted")
check("year outside the rows excluded", 4 not in m)

# 5. diesel: a non-diesel row the other feed prints as diesel becomes diesel; gas car excluded
d = GA.build([rec("400-8", "alternator", [app("Ford", "F-250 Super Duty", 2005, "6000cc 6.0L V8", "Truck"),
                                          app("Ford", "F-250 SUPER-DUTY", 2005, "363cu in 6.0L V8 Diesel")], 180)], N)
cars = [(0, "Ford", "F-250 Super Duty", 2005, "6.0L 8-cyl"), (1, "Ford", "F-250 Super Duty", 2005, "6.0L 8-cyl diesel")]
m = dict(GA.members(d, cars).get("am:dbe:alternator:400-8", []))
check("diesel rows harmonised", all("diesel" in a[4] for a in d["groups"][0]["apps"]), str(d["groups"][0]["apps"]))
check("gas car not matched to diesel unit", 0 not in m and m.get(1) == "", str(m))

# 6. starter transmission gate from the unit's own fit notes
d = GA.build([rec("410-1", "starter", [app("Mini", "Cooper", 2005, "1.6L")], fits="MINI COOPER 1.6L w/AT 2002-08"),
              rec("410-2", "starter", [app("Mini", "Cooper", 2005, "1.6L")], fits="MINI COOPER 1.6L w/MT 2002-08")], N)
g = ids(d)
check("AT / MT parsed", (g["am:dbe:starter:410-1"]["trans"], g["am:dbe:starter:410-2"]["trans"]) == ("AT", "MT"))
cars = [(0, "MINI", "Cooper", 2005, "1.6L 4-cyl", "5-spd Manual"), (1, "MINI", "Cooper", 2005, "1.6L 4-cyl", "6-spd Automatic"),
        (2, "MINI", "Cooper", 2005, "1.6L 4-cyl", "")]
mm = GA.members(d, cars)
at, mt = dict(mm["am:dbe:starter:410-1"]), dict(mm["am:dbe:starter:410-2"])
check("manual car not in AT unit", 0 not in at and at.get(1) == "")
check("automatic car not in MT unit", 1 not in mt and mt.get(0) == "")
check("unknown trans kept with condition", at.get(2) == "trans_unconfirmed" and mt.get(2) == "trans_unconfirmed")
check("mixed AT+MT notes give no gate", GA.unit_trans({"fits_text": "X w/AT\nY w/MT"}) is None)

# 6b. a row contradicting the unit's own Fits text is dropped
d = GA.build([rec("410-52066", "starter", [app("Chrysler", "Voyager", 1990, "3.3L V6"),
                                           app("Fiat", "500", 2014, "1.4L 4 cyl")], fits="CHRYSLER 3.3L 1990-91")],
             GA.Names(LOT | {("Fiat", "500"), ("Chrysler", "Voyager")}))
check("row whose liters the Fits text does not state is dropped",
      [a[0] for a in d["groups"][0]["apps"]] == ["Chrysler"] and d["rows_contradicting_fits_text"] == 1,
      str(d["groups"][0]["apps"]))
check("no Fits liters -> no row guard", not GA.row_contradicts_fits({"engine": "1.4L"}, set()))

# 6c. year span vs the Fits text (400-24253: "MINI COOPER 1.6L 2006-10")
d = GA.build([rec("400-24253", "alternator", [app("Mini", "Cooper", 2008, "1.6L"), app("Mini", "Cooper", 2013, "1.6L"),
                                              app("Mini", "COOPER COUNTRYMAN", 2012, "1.6L")], 150,
                  fits="MINI COOPER 1.6L 2006-10\n6-GROOVE CLUTCH PULLEY 49.5mm OD")],
             GA.Names(LOT | {("MINI", "Countryman")}))
ys = sorted((a[1], a[2]) for a in d["groups"][0]["apps"])
check("row outside the Fits year range for that model dropped", ("Cooper", 2013) not in ys and ("Cooper", 2008) in ys, str(ys))
check("model the Fits text does not name keeps its rows", ("Countryman", 2012) in ys, str(ys))
check("year drops counted", d["rows_outside_fits_years"] == 1)
check("two-digit and -ON ranges parsed", GA.fits_year_lines({"fits_text": "FORD E-450 6.0L 2004-07\nMINI COOPER 1.6L 2007-ON"})
      == [("FORD E-450 6.0L 2004-07", [(2004, 2007)]), ("MINI COOPER 1.6L 2007-ON", [(2007, 9999)])])

# 6d. refine: same make (or evidenced twin) + same size + same fuel; OEM overrides
LOT2 = LOT | {("Mercury", "Mountaineer"), ("Ford", "Explorer"), ("Ford", "Escort"), ("Ford", "Ranger")}
N2 = GA.Names(LOT2)
u = GA.build([rec("400-9", "alternator", [app("Ford", "Explorer", 2002, "4.0L V6"), app("Mercury", "Mountaineer", 2002, "4.0L V6"),
                                          app("Ford", "Escort", 1998, "2.0L L4"), app("Ford", "Ranger", 2002, "4.0L V6"),
                                          app("Ford", "F-150", 2002, "")], 130)], N2)
TW = [("Mercury Mountaineer / Ford Explorer", ("Mercury", "Mountaineer"), ("Ford", "Explorer"))]
r = GA.refine(u, None, TW)
def fams(doc):
    return sorted(sorted({(a[0], a[1], a[4]) for a in g["apps"]}) for g in doc["groups"])
f = fams(r)
check("different engine sizes never share a sub-group",
      not any({x[2] for x in grp} >= {"4.0L 6-cyl", "2.0L 4-cyl"} for grp in f), str(f))
check("other make only via an evidenced twin",
      [("Ford", "Explorer", "4.0L 6-cyl"), ("Mercury", "Mountaineer", "4.0L 6-cyl")] in f
      and not any(("Mercury", "Mountaineer", "4.0L 6-cyl") in grp and ("Ford", "Ranger", "4.0L 6-cyl") in grp for grp in f), str(f))
check("rows without an engine size dropped", not any(x[1] == "F-150" for grp in f for x in grp)
      and r["refined"]["stats"]["rows_without_engine_size"] == 1)
dd = GA.build([rec("400-10", "alternator", [app("Ford", "F-250 SUPER-DUTY", 2005, "363cu in 6.0L V8 Diesel"),
                                            app("Ford", "F-150", 2005, "6.0L V8")], 180)], N2)
check("diesel and gas never share a sub-group", len(GA.refine(dd, None, [])["groups"]) == 2)
key = lambda md, y: ("Ford", GA.squash(md), y, 4.0)
oem = {"alternator": {key("Explorer", 2002): frozenset({"ford:a"}), key("Ranger", 2002): frozenset({"ford:b"})}}
u2 = GA.build([rec("400-11", "alternator", [app("Ford", "Explorer", 2002, "4.0L V6"), app("Ford", "Ranger", 2002, "4.0L V6"),
                                            app("Ford", "Explorer", 2003, "4.0L V6")], 130)], N2)
ro = GA.refine(u2, oem, [])
sets = [sorted((a[1], y) for a in g["apps"] for y in range(a[2], a[3] + 1)) for g in ro["groups"]]
check("OEM-disjoint keys never share a sub-group",
      not any(("Explorer", 2002) in s and ("Ranger", 2002) in s for s in sets), str(sets))
check("a key without OEM numbers pairs with each OEM side",
      all(("Explorer", 2003) in s for s in sets) and len(sets) == 2, str(sets))
check("refined groups stay likely/aftermarket", all(g["tier"] == "likely" and g["src"] == "aftermarket" for g in ro["groups"]))

# 7. parse_engine on both feeds and lot strings
check("parse feeds", GA.parse_engine("181cu in 3.0L V6") == (3.0, 6, False)
      and GA.parse_engine("2500cc, AWD, 51kW 2.5L 4 cyl, Diesel") == (2.5, 4, True)
      and GA.parse_engine("3.5L 6-cyl") == (3.5, 6, False) and GA.parse_engine("1.6L") == (1.6, None, False))

# 8. determinism
r1 = [rec("400-1", "alternator", [app("Mini", "COOPER", 2007, "1.6L")], 105),
      rec("400-2", "alternator", [app("Mini", "Cooper", 2007, "1.6L")], 120)]
check("deterministic sha", GA.build(r1, N)["sha256"] == GA.build(list(reversed(r1)), N)["sha256"])

# 9. real raw: sampled pairs re-checked against the raw application rows
try:
    recs, src = GA.load_raw(None, "origin/oem-raw")
except subprocess.CalledProcessError:
    recs = None
if recs is None:
    print("SKIP raw sample: origin/oem-raw not fetched (rule 8)")
else:
    inv_p = GA.REPO / "docs" / "data" / "inventory_live.json"
    if not inv_p.exists():
        print("SKIP raw sample: inventory_live.json absent")
    else:
        inv = json.loads(inv_p.read_text())
        F = {k: i for i, k in enumerate(inv["fields"])}
        NN = GA.Names({(v[F["make"]] or "", v[F["model"]] or "") for v in inv["vehicles"]})
        doc = GA.build(recs, NN, src)
        ex_p = GA.REPO / "docs" / "data" / "vehicle_extras.json"
        ex = json.loads(ex_p.read_text()).get("extras", {}) if ex_p.exists() else {}
        cars = []
        for i, v in enumerate(inv["vehicles"]):
            e = ex.get(str(v[F["id"]])) or []
            cars.append((i, v[F["make"]] or "", v[F["model"]] or "", int(v[F["year"]] or 0),
                         e[2] if len(e) > 2 else "", e[3] if len(e) > 3 else ""))
        mem = GA.members(doc, cars)
        by_pn = {(r["category"], r["aftermarket_pn"]): r for r in recs}
        rnd = random.Random(11)
        gids = sorted(g for g, ms in mem.items() if len(ms) >= 2)
        bad = []
        for _ in range(200):
            gid = rnd.choice(gids)
            _, _, cat, pn = gid.split(":", 3)
            r = by_pn[(cat, pn)]
            for ci, cond in rnd.sample(mem[gid], 2):
                _, mk, md, yr, eng, _tr = cars[ci]
                ce = GA.parse_engine(eng)
                ok = False
                for a in r["applications"]:
                    c = NN.canon(a["make"], a["model"])
                    if not c or c[0] != mk or GA.squash(c[1]) != GA.squash(md):
                        continue
                    if not (a["years"][0] <= yr <= a["years"][1]):
                        continue
                    re_ = GA.parse_engine(a["engine"])
                    # the raw row's own engine must not contradict the car (diesel is
                    # harmonised across feeds by build(), so compare liters/cylinders here)
                    if not a["engine"].strip() or GA.engine_agrees(re_[:2] + (ce[2],), ce) is not False:
                        ok = True
                        break
                if not ok:
                    bad.append((gid, mk, md, yr, eng))
        check("200 sampled pairs: both cars printed on the unit's raw rows", not bad, str(bad[:5]))
        check("no group claims verified", all(g["tier"] == "likely" for g in doc["groups"]))

print(f"\n{len(FAILS)} failed" if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)
