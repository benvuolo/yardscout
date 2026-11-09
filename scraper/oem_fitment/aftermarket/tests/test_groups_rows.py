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


FX = HERE / "fixtures"
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
d = R.build([G0], Names(), "gspnorthamerica.com")
check("real NCV36167XD refused (duplicate 2019 row)", d["summary"]["groups"] == 0
      and d["summary"]["refused_units"].get("cv-axle:flag") == 1)
clean = gsp_rec("NCV1", [(2017, 2022, "Honda", "CR-V", "")], engines=("1.5", "2.4"))
d = R.build([clean], Names(), "gspnorthamerica.com")
g = d["groups"][0]
check("clean unit -> one Likely aftermarket group per position", d["summary"]["groups"] == 1 and g["tier"] == "likely"
      and g["src"] == "aftermarket" and g["position"] == "front left" and g["id"] == "am:gsp:cv-axle:NCV1:front-left")
check("title engines go on every app, no drive/trans", g["apps"] == [["Honda", "CR-V", 2017, 2022, "1.5L"],
                                                                  ["Honda", "CR-V", 2017, 2022, "2.4L"]])
check("note: our words, says to check drive/trans", "Drive and transmission are not stated" in g["note"]
      and "GSP NCV1" in g["note"])
other = gsp_rec("NCV2", [(2019, 2019, "Honda", "CR-V", "")])
d = R.build([clean, other], Names(), "gspnorthamerica.com")
check("two units for one corner: that year is dropped from both", d["groups"][0]["apps"][0][2:4] == [2017, 2018]
      and d["groups"][0]["apps"][-1][2:4] == [2020, 2022] and all(x["unit"] != "NCV2" for x in d["groups"]))
trim = gsp_rec("NCV3", [(2019, 2019, "Honda", "CR-V", "EX")])
d = R.build([clean, trim], Names(), "gspnorthamerica.com")
check("a trim row is refused but still claims (splits the 2019 corner)",
      not any(a[2] <= 2019 <= a[3] for a in d["groups"][0]["apps"]) and d["refused_rows"].get("submodel") == 1)
right = gsp_rec("NCV4", [(2019, 2019, "Honda", "CR-V", "")], pos="Front Right")
d = R.build([clean, right], Names(), "gspnorthamerica.com")
check("other side does not conflict", len(d["groups"]) == 2 and d["groups"][0]["apps"][0][2:4] == [2017, 2022])
bare = gsp_rec("NCV5", [(2019, 2019, "Honda", "CR-V", "")], pos="Front")
d = R.build([clean, bare], Names(), "gspnorthamerica.com")
check("a bare 'Front' unit conflicts with a front-left unit", not any(a[2] <= 2019 <= a[3] for g in d["groups"]
                                                                     for a in g["apps"]))
for name, rec, why in [
        ("no title engine", gsp_rec("X1", [(2010, 2012, "Honda", "Civic", "")], engines=()), "no_title_engine"),
        ("AWD in the title", gsp_rec("X2", [(2010, 2012, "Honda", "Civic", "")], engines=("AWD",)), "title_token"),
        ("two engines across two models", gsp_rec("X3", [(2010, 2012, "Honda", "Civic", ""), (2010, 2012, "Acura", "ILX", "")],
                                                   engines=("1.8", "2.0")), "multi_engine_multi_model"),
        ("duplicate rows flag", gsp_rec("X4", [(2010, 2012, "Honda", "Civic", "")], flags=["duplicate_rows"]), "flag"),
        ("no position", gsp_rec("X5", [(2010, 2012, "Honda", "Civic", "")], pos=""), "title_position")]:
    d = R.build([rec], Names(), "gspnorthamerica.com")
    check(f"GSP refuses: {name}", not d["groups"] and any(k.endswith(":" + why) for k in d["summary"]["refused_units"]))

# ---- 1A Auto
d = R.build([A0], Names(), "www.1aauto.com")
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
d = R.build([u1, u2], Names(), "www.1aauto.com")
check("1A: a trim-qualified unit of the same brand splits that year",
      d["groups"][0]["apps"] == [["Honda", "Accord", 2008, 2009, ""], ["Honda", "Accord", 2011, 2012, ""]]
      and d["refused_rows"].get("q: Sport") == 1)
u3 = a_rec("1A3", [(2010, 2010, "", "Front Driver Side")], brand="KYB Excel-G", bpn="339999")
d = R.build([u1, u3], Names(), "www.1aauto.com")
check("1A: another brand's unit for the same corner is an equivalent, not a split",
      d["groups"][0]["apps"] == [["Honda", "Accord", 2008, 2012, ""]] and len(d["groups"]) == 2)
u4 = a_rec("1A4", [(2008, 2012, "V6 3.0L ", "Front Driver Side")], bpn="SCA4")
d = R.build([u4], Names(), "www.1aauto.com")
check("1A: an engine qualifier becomes the app's engine", d["groups"][0]["apps"] == [["Honda", "Accord", 2008, 2012, "3.0L 6-cyl"]])
for q in ("Sedan ", "without Electronic Suspension ", "Hybrid ", "From 1/01/06 Production Date "):
    d = R.build([a_rec("1AQ", [(2008, 2012, q, "Front Driver Side")])], Names(), "www.1aauto.com")
    check(f"1A refuses the qualifier {q.strip()!r}", not d["groups"])
d = R.build([a_rec("1AF", [(2008, 2012, "", "Front Driver Side")])] , Names(), "www.1aauto.com")
bad = copy.deepcopy(A0)
bad["flags"] = ["slug_not_category"]
check("1A refuses a flagged unit", not R.build([bad], Names(), "www.1aauto.com")["groups"])

# ---- facts only; owner's free-fitment rule
out = json.dumps(R.build([A0, u1, u4], Names(), "www.1aauto.com"))
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
