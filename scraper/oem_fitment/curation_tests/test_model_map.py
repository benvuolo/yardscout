#!/usr/bin/env python3
"""CURATION_SPEC.md §9 test_model_map: M1-M10 against the PINNED inventory
the committed groups were curated on (interchange gates-1118): every scan
that brought a new one-car feed spelling ("Focus Htbk", "Civic 2Dr", "Eos
Conv", "Passat Tdi") used to fail M5 here, although the shipped groups were
curated on another inventory and an unmapped spelling gets no claim (no
target, no app that matches it). The pin is read from git and checked by
sha256; without it (a shallow clone) M2-M10 SKIP with the reason. The live
docs/data/inventory_live.json is still validated, and what it finds is
REPORTED, not failed: a new spelling there is for the next re-curation (add a
map exclusion or entry, then re-curate on the newer inventory and move PIN)."""
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from _util import OEM, check, done, js, skip
import model_map as MM
import policy

# The inventory the shipped groups and the nissan candidate were curated on
# (curate --inventory; groups/_report/nissan.json "inputs"; audit11_4/README.md).
# Move it together with a re-curation on a newer inventory.
PIN = {"ref": "a85c654", "path": "docs/data/inventory_live.json",
       "sha256": "1a9cfa73e9c15e41809e1149c2e752504e797efd91c18de4668df454364ce1d6"}


def pinned_inventory():
    """(inventory dict, '') or (None, why) from git, sha256-checked."""
    try:
        raw = subprocess.run(["git", "-C", str(OEM), "show", f"{PIN['ref']}:{PIN['path']}"],
                             capture_output=True, check=True, timeout=300).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git show {PIN['ref']}:{PIN['path']} failed ({type(e).__name__}); a shallow clone has no pin"
    got = hashlib.sha256(raw).hexdigest()
    if got != PIN["sha256"]:
        return None, f"pinned inventory sha256 {got[:12]} != {PIN['sha256'][:12]}"
    return json.loads(raw), ""


doc = MM.load()
mm = MM.ModelMap(doc)
inv, pin_why = pinned_inventory()
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

live = MM.load_inventory()
if live is None:
    skip("report on the live inventory", "docs/data/inventory_live.json is absent")
else:
    lerrs, _lw, _lr = MM.validate(mm, live, J, policy.NAMESPACES)
    print(f"     live inventory ({live.get('scrapedAt', '?')}): {len(lerrs)} finding(s), reported, not failed"
          + (" (curate.py on this inventory refuses to run until the map covers them)" if lerrs else ""))
    for e in lerrs[:40]:
        print(f"     REPORT {e}")
    if len(lerrs) > 40:
        print(f"     REPORT ... {len(lerrs) - 40} more")

if inv is None:
    skip("M2-M10 against the pinned inventory", pin_why)
else:
    errs, warns, rep = MM.validate(mm, inv, J, policy.NAMESPACES)
    check(f"the committed map passes M1-M10 on the pinned inventory ({PIN['ref']}, no errors)", errs == [], str(errs[:5]))
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

# ---------------------------------------------- identity draft (§6 proposals)
from collections import Counter  # noqa: E402

feed = [("Chevrolet", "Cobalt", 3), ("Chevrolet", "Silverado", 2), ("Chevrolet", "Silverado 1500", 5),
        ("Chevrolet", "Silverado 2500HD", 1), ("Chevrolet", "Malibu", 4), ("Chevrolet", "Malibu Hybrid", 1),
        ("Chevrolet", "S-10", 2), ("Chevrolet", "Sonic", 10), ("Toyota", "T100", 2), ("Toyota", "T100 Pickup", 1)]
rows = []
for mk, md, n in feed:
    rows += [[len(rows), "", 2008, mk, md, "", "", 0, 0, 0, 0] for _ in range(n)]
sonic = [i for i, r in enumerate(rows) if r[4] == "Sonic"]
syn_inv = {"scrapedAt": "2026-11-05T00:00:00Z", "vehicles": rows,
           "vpic": {str(sonic[0]): ["LT", "usable", "", "", "VIN decodes as Pontiac G3"]}}
empty = {"schema": 1, "entries": [], "exclude": {}}
cat = Counter({("Chevrolet", "Cobalt"): 4, ("Chevrolet", "Silverado"): 9, ("Chevrolet", "Malibu"): 2,
               ("Chevrolet", "Zzz"): 1, ("Chevrolet", "S10"): 1, ("Chevrolet", "S-10"): 1, ("Chevrolet", "Sonic"): 3})
dg = MM.draft_identity("gm", cat, syn_inv, J, MM.ModelMap(empty), policy.NAMESPACES, "oem-raw@test")
ent = {e["cat_model"]: e for e in dg["entries"]}
why = {s["cat_model"]: s["why"] for s in dg["skipped"]}
check("draft: an identity entry where the canonical feed model has cars (trims '*', basis names the raw)",
      ent.get("Cobalt", {}).get("targets") == [{"make": "Chevrolet", "model": "Cobalt", "trims": "*"}]
      and "oem-raw@test" in ent["Cobalt"]["basis"])
check("draft: a feed name the feed splits by series is ambig (Likely only)",
      "ambig" in ent.get("Silverado", {}).get("targets", [{}])[0])
check("draft: series sub-models under the catalog name are excluded with a reason",
      "gm|Chevrolet|Silverado 1500" in dg["exclude"] and "gm|Chevrolet|Silverado 2500HD" in dg["exclude"])
check("draft: a hybrid sub-model under a mapped name is excluded as hybrid",
      dg["exclude"].get("gm|Chevrolet|Malibu Hybrid", "").startswith("hybrid sub-model"))
check("draft: no entry without a feed car", "Zzz" not in ent and "no feed car" in why.get("Zzz", ""))
check("draft: two catalog names on one feed model are left unmapped (M8 needs a reviewed merge)",
      "S10" not in ent and "S-10" not in ent and "M8" in why.get("S10", "") and "M8" in why.get("S-10", ""))
check("draft: a target over the M6 make-mismatch share is left unmapped",
      "Sonic" not in ent and "M6" in why.get("Sonic", ""), why.get("Sonic", ""))
dt = MM.draft_identity("toyota", Counter({("Toyota", "T100"): 2}), syn_inv, J, MM.ModelMap(empty),
                       policy.NAMESPACES, "oem-raw@test")
check("draft: a squash key shared with another feed model is left unmapped (M3)",
      not dt["entries"] and "M3" in dt["skipped"][0]["why"], str(dt["skipped"]))
merged, added = MM.merge_draft(empty, [dg])
e, _, _ = MM.validate(MM.ModelMap(merged), syn_inv, J, policy.NAMESPACES)
check("draft: the merged draft passes M1-M10 on its inventory", e == [], str(e[:3]))
held = {"schema": 1, "exclude": {"gm|Chevrolet|Malibu Hybrid": "hand reason"},
        "entries": [{"ns": "gm", "cat_make": "Chevrolet", "cat_model": "Cobalt", "basis": "hand entry",
                     "targets": [{"make": "Chevrolet", "model": "Cobalt", "trims": ["ls"]}]}]}
merged2, _ = MM.merge_draft(held, [MM.draft_identity("gm", cat, syn_inv, J, MM.ModelMap(held), policy.NAMESPACES, "x"),
                                   dg])
check("merge never changes an existing entry or exclusion",
      next(x for x in merged2["entries"] if x["cat_model"] == "Cobalt")["basis"] == "hand entry"
      and merged2["exclude"]["gm|Chevrolet|Malibu Hybrid"] == "hand reason")
check("model_map.json keeps its own layout (dump() round-trips the committed file)",
      MM.dump(MM.load()) == MM.MODEL_MAP_PATH.read_text())
done("test_model_map")
