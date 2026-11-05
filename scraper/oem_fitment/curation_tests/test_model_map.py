#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_model_map: M1-M10 against the real
docs/data/inventory_live.json (skips with a printed reason when absent)."""
import copy
import json
import tempfile
from pathlib import Path

from _util import check, done, js, skip
import model_map as MM
import policy

doc = MM.load()
mm = MM.ModelMap(doc)
inv = MM.load_inventory()
J = js()

check("model_map.json is schema 1 with entries and an exclude table",
      doc.get("schema") == 1 and doc.get("entries") and isinstance(doc.get("exclude"), dict))
check("every entry has a basis and every exclude a reason",
      all((e.get("basis") or "").strip() for e in doc["entries"]) and all(v.strip() for v in doc["exclude"].values()))
check("no '*' model prefixes anywhere", "*\"" not in json.dumps([t["model"] for e in doc["entries"] for t in e["targets"]]))
camry = mm.targets("toyota", "Toyota", "Camry", 2009)
check("Camry maps to Camry (all trims) and Camry Hybrid (hybrid trims, 2007-2017)",
      {(t.model, t.trims if t.trims == "*" else tuple(t.trims)) for t in camry}
      == {("Camry", "*"), ("Camry Hybrid", ("hybrid*",))})
check("Camry Hybrid target only before 2018", [t.model for t in mm.targets("toyota", "Toyota", "Camry", 2018)] == ["Camry"])
check("trim pattern 'hybrid*' matches 'hybrid le' but not 'le'",
      camry[1].trim_ok("hybrid le") if camry[1].model == "Camry Hybrid" else camry[0].trim_ok("hybrid le"))

if inv is None:
    skip("M2-M10 against inventory", "docs/data/inventory_live.json is absent")
else:
    errs, warns, rep = MM.validate(mm, inv, J, policy.NAMESPACES)
    check("the committed map passes M1-M10 (no errors)", errs == [], str(errs[:5]))
    print(f"     ({len(warns)} M2 warnings: targets without cars)")
    check("M4: the 'Camry' target does not catch a 'Camry Hybrid' car",
          not J._app_matches(("Toyota", "Camry", 2007, 2017), 2009, "Toyota", "Camry Hybrid"))
    check("M10 report: mapped share per namespace", all(k in rep["M10"] for k in policy.NAMESPACES))
    check("M10: toyota, mopar, ford, nissan map at least 90% of their lot cars",
          all(rep["M10"][ns]["mapped_share"] >= 0.90 for ns in ("toyota", "mopar", "ford", "nissan")), json.dumps(rep["M10"]))
    check("M9 report present", "M9_cars_outside_catalog_years" in rep)
    check("M6 report says what it could check", "vPIC model is not in the published inventory" in rep["M6"]["note"])

    def errs_of(mut):
        d = copy.deepcopy(doc)
        mut(d)
        return MM.validate(MM.ModelMap(d), inv, J, policy.NAMESPACES)

    def first_target(d, ns, mk, md):
        return next(t for e in d["entries"] if (e["ns"], e["cat_make"], e["cat_model"]) == (ns, mk, md) for t in e["targets"])

    e, _, _ = errs_of(lambda d: first_target(d, "toyota", "Toyota", "Solara").update(model="Solara"))
    check("M1: a non-canonical spelling ('Solara' for 'Camry Solara') is an error",
          any(x.startswith("M1") for x in e), str(e[:2]))
    e, w, _ = errs_of(lambda d: d["entries"].append({"ns": "toyota", "cat_make": "Toyota", "cat_model": "Zzz",
                                                      "targets": [{"make": "Toyota", "model": "Zzz", "trims": "*"}],
                                                      "basis": "test"}))
    check("M2: a target with no car is a warning", any(x.startswith("M2") for x in w))
    e, _, _ = errs_of(lambda d: d["entries"].append({"ns": "mopar", "cat_make": "Dodge", "cat_model": "D250",
                                                      "targets": [{"make": "Dodge", "model": "D250", "trims": "*"}],
                                                      "basis": "test"}))
    check("M3: a squash key shared with another feed model is an error ('D250' / 'D-250')",
          any(x.startswith("M3") for x in e), str(e[:2]))
    e, _, _ = errs_of(lambda d: d["entries"].append({"ns": "mopar", "cat_make": "Ram", "cat_model": "Ram 1500 X",
                                                      "targets": [{"make": "Ram", "model": "Ram 1500", "trims": "*"}],
                                                      "basis": "test"}))
    check("M4: a target whose synthetic car matches another target ('Ram 1500' vs '1500') is an error",
          any(x.startswith("M4") for x in e), str([x for x in e if x.startswith("M4")][:2]))
    e, _, _ = errs_of(lambda d: d["exclude"].pop("toyota|Toyota|Highlander Hybrid"))
    check("M5: a feed model under a mapped name that is neither a target nor excluded is an error",
          any(x.startswith("M5") and "Highlander Hybrid" in x for x in e), str(e[:2]))
    e, _, _ = errs_of(lambda d: first_target(d, "toyota", "Toyota", "Sienna").update(make="Honda", model="Odyssey"))
    check("M7: a target make outside the namespace is an error", any(x.startswith("M7") for x in e))
    e, _, _ = errs_of(lambda d: [t.pop("merge") for x in d["entries"] if x["cat_model"] == "Grand Cherokee WK"
                                 for t in x["targets"]])
    check("M8: many-to-one without merge is an error", any(x.startswith("M8") for x in e), str(e[:2]))
    # M6 on a small synthetic inventory: hybrid trim subset with Gas decodes
    syn = {"vehicles": [[i, "", 2009, "Toyota", "Camry Hybrid", "", "", 0, 0, 0, 0] for i in range(20)]
           + [[100, "", 2009, "Toyota", "Camry", "", "", 0, 0, 0, 0]],
           "vpic": {str(i): ["Gas" if i == 0 else "Hybrid", "usable", "", "", ""] for i in range(20)}}
    e, _, _ = MM.validate(mm, syn, J, policy.NAMESPACES)
    check("M6: more than 1% of feed 'Camry Hybrid' decoding as vPIC 'Gas' is an error",
          any(x.startswith("M6") and "Camry Hybrid" in x for x in e), str([x for x in e if x.startswith("M6")][:2]))
    syn["vpic"]["0"][0] = "Hybrid"
    e, _, _ = MM.validate(mm, syn, J, policy.NAMESPACES)
    check("M6: all-hybrid decodes pass", not any(x.startswith("M6") for x in e))

    # curate.py refuses to run on any error
    import curate as C
    d = copy.deepcopy(doc)
    first_target(d, "toyota", "Toyota", "Solara").update(model="Solara")
    p = Path(tempfile.mkdtemp()) / "mm.json"
    p.write_text(json.dumps(d))
    rc = C.main(["--ns", "toyota", "--raw-dir", tempfile.mkdtemp(), "--model-map", str(p),
                 "--out", tempfile.mkdtemp()])
    check("curate.py refuses to run on a model map error (exit 2)", rc == 2)
done("test_model_map")
