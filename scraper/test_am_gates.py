#!/usr/bin/env python3
"""Gated aftermarket app rows (ops/interchange.md §9, hub 2026-11-09).

A Spectra / GSP-1A app row may carry a 6th element limiting it to a body
style and/or drivetrain the unit list states: {"body": "Sedan"},
{"drive": "awd"}, or the older bare string (= body). Checks:

1. junkyard_scraper._am_group_entry keeps valid gates, refuses malformed
   ones, and leaves 5-element rows unchanged.
2. docs/app.js pfAmGate (the AM-GATE block, run in node) gives the parts
   table's semantics: decode or listing naming the gate confirms it; a decode
   naming another body, or exactly one other drive class, excludes; anything
   else is "if equipped". Never inferred.
3. docs/app.js pfAmRows (extracted with stubs, run in node) offers a
   sedan-gated unit's donor that decodes as a sedan, drops a coupe, keeps an
   undecoded donor with an "if equipped" warning, and treats drive gates and
   the old string format the same way.
4. The 2026-11-09 categories ship with the right kinds and exact price tokens.

Run:  python3 scraper/test_am_gates.py
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import junkyard_scraper as js  # noqa: E402

APP = (HERE.parent / "docs" / "app.js").read_text()
failures = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------- 1. payload
def _grp(apps):
    return {"id": "t1", "cat": "radiator", "tier": "likely", "src": "aftermarket",
            "note": "Spectra Premium unit list.", "unit": "CU2345", "apps": apps}


e = js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L"]]), "spectra")
check("5-element app row ships unchanged", e["apps"] == [["Honda", "Accord", 2003, 2007, "2.4L"]])
e = js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L", {"body": "Sedan"}],
                             ["Honda", "Accord", 2003, 2007, "2.4L", {"body": "Coupe", "drive": "FWD"}]]), "spectra")
check("dict gates kept, drive lower-cased",
      e["apps"] == [["Honda", "Accord", 2003, 2007, "2.4L", {"body": "Sedan"}],
                    ["Honda", "Accord", 2003, 2007, "2.4L", {"body": "Coupe", "drive": "fwd"}]], str(e["apps"]))
e = js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L", "Sedan"]]), "spectra")
check("old string a[5] reads as a body gate", e["apps"][0][5] == {"body": "Sedan"})
e = js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L", {}]]), "spectra")
check("empty gates collapse to a 5-element row", e["apps"] == [["Honda", "Accord", 2003, 2007, "2.4L"]])
for bad, why in (({"drive": "2wd"}, "unknown drive"), ({"trim": "EX"}, "unknown key"),
                 ({"body": "<b>Sedan</b>"}, "markup"), (["Sedan"], "list")):
    try:
        js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L", bad]]), "spectra")
        check(f"refuses gates: {why}", False)
    except ValueError:
        check(f"refuses gates: {why}", True)
try:
    js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L", {"body": "Sedan"}, "x"]]), "spectra")
    check("refuses a 7-element row", False)
except ValueError:
    check("refuses a 7-element row", True)

# ------------------------------------------------------------- 4. categories
NEW = {"radiator": "combo", "ac-compressor": "combo", "ac-condenser": "exact", "heater-core": "exact",
       "evaporator": "exact", "throttle-body": "combo", "fuel-pump-module": "combo", "cv-axle": "combo",
       "strut": "body"}
PC = js.INTERCHANGE_PART_CATEGORIES
check("the 9 aftermarket-layer categories exist with their kinds",
      all(c in PC and PC[c]["kind"] == k for c, k in NEW.items()),
      str({c: PC.get(c, {}).get("kind") for c in NEW}))
check("none of them is engine kind (no engine-family / path E donors)",
      all(PC[c]["kind"] != "engine" for c in NEW))
check("each is an aftermarket category (_AM_CATS)", all(c in js._AM_CATS for c in NEW))
check("each carries notes and a rowWarn", all(PC[c]["notes"] and PC[c].get("rowWarn") for c in NEW))
check("every new price token is an exact row ('=' prefix): no substring hits a cap, fan or hood strut",
      all(t.startswith("=") for c in NEW for t in PC[c]["priceTokens"]))
_SPOT = [p["name"].lower() for e2 in js.UNOBTANIUM_DB.values() for p in e2["top_parts"]]
_bad_spot = {c: sorted({n for n in _SPOT for t in PC[c]["tokens"] if t in n
                         and re.search(r"air suspension|fan|hood|liftgate|intake/|manifold", n)})
             for c in NEW}
check("spotted-part tokens hit no fan / air-suspension / hood-strut / manifold row",
      not any(_bad_spot.values()), str({k: v for k, v in _bad_spot.items() if v}))


# ------------------------------------------------------------ 2+3. app (node)
def fn_src(name):
    m = re.search(r"^function " + re.escape(name) + r"\(", APP, re.M)
    if not m:
        raise SystemExit(f"app.js has no function {name}")
    i = APP.index("{", m.end())
    depth = 0
    for j in range(i, len(APP)):
        if APP[j] == "{":
            depth += 1
        elif APP[j] == "}":
            depth -= 1
            if depth == 0:
                return APP[m.start():j + 1]
    raise SystemExit(f"unbalanced {name}")


block = re.search(r"/\* AM-GATE BEGIN.*?/\* AM-GATE END \*/", APP, re.S)
check("app.js carries the AM-GATE block", bool(block))
node = shutil.which("node")
if not node:
    print("SKIP node not installed: app-side gate checks not run")
elif block:
    harness = "\n".join([
        block.group(0),
        fn_src("pfAmRows"), fn_src("pfAppMatches"), fn_src("pfAmSourceText"), fn_src("pfAmParseEngine"),
        fn_src("pfAmEngineAgrees"), fn_src("pfAmCarTrans"),
        r"""
const pfSquash = x => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const pfSquashModel = (m, mk) => pfSquash(m);
const canonicalMake = m => m;
const escapeHtml = x => String(x);
const vehicleDistanceMi = v => 1;
const extraIdx = { photo: 0, color: 1, engine: 2, trans: 3, transSrc: 4, body: 5 };
let EX = {}; const extrasFor = v => EX[v.id] || null;
let liveInventory = [];
const pfCat = { id: 'radiator', rowWarn: 'check the trans-cooler fittings' };
const out = {};
const G = (apps) => ({ id: 'g', cat: 'radiator', src: 'aftermarket', label: 'Spectra Premium', unit: 'CU1',
                      note: 'unit list', apps });
const S = { year: 2005, make: 'Honda', model: 'Accord' };
function run(apps, cars, ex) {
  liveInventory = cars; EX = ex || {};
  const res = new Map();
  pfAmRows(S, [G(apps)], res, 0, null);
  return Object.fromEntries([...res].map(([k, r]) => [k, r.warns]));
}
const car = (id, model, vpicDriveType) => ({ id, year: 2005, make: 'Honda', model, vpicDriveType });
// gate verdicts
out.g = {
  sedanSedan: pfAmGate({ body: 'Sedan' }, 'Accord', 'sedan', ''),
  sedanCoupe: pfAmGate({ body: 'Sedan' }, 'Accord', 'coupe', ''),
  sedanNone: pfAmGate({ body: 'Sedan' }, 'Accord', '', ''),
  coupeListing: pfAmGate({ body: 'Coupe' }, 'Accord Coupe', '', ''),
  coupeListingVsDecode: pfAmGate({ body: 'Coupe' }, 'Accord Coupe', 'sedan', ''),
  strSedanCoupe: pfAmGate('Sedan', 'Accord', 'coupe', ''),
  strSedanSedan: pfAmGate('Sedan', 'Accord', 'sedan', ''),
  crewPickup: pfAmGate({ body: 'Crew Cab Pickup' }, 'Silverado 1500', 'pickup', ''),
  crewSuv: pfAmGate({ body: 'Crew Cab Pickup' }, 'Silverado 1500', 'suv', ''),
  crewListing: pfAmGate({ body: 'Crew Cab Pickup' }, 'Silverado 1500 Crew Cab Pickup', '', ''),
  awdAwd: pfAmGate({ drive: 'awd' }, 'Escape', '', 'AWD/All-Wheel Drive'),
  awdFwd: pfAmGate({ drive: 'awd' }, 'Escape', '', 'FWD/Front-Wheel Drive/FF'),
  awd4wd: pfAmGate({ drive: 'awd' }, 'Escape', '', '4WD/4-Wheel Drive/4x4'),
  awdMixed: pfAmGate({ drive: 'awd' }, 'Escape', '', '2WD/4WD'),
  awdNone: pfAmGate({ drive: 'awd' }, 'Escape', '', ''),
  awdListing: pfAmGate({ drive: 'awd' }, 'Escape AWD', '', ''),
  fwd4x2: pfAmGate({ drive: 'fwd' }, 'Tacoma', '', '4x2'),
  both: pfAmGate({ body: 'Sedan', drive: 'awd' }, 'Legacy', 'sedan', 'AWD/All-Wheel Drive'),
  bothHalf: pfAmGate({ body: 'Sedan', drive: 'awd' }, 'Legacy', 'sedan', ''),
  none: pfAmGate(undefined, 'Accord', '', ''),
};
// pfAmRows donor selection
const cars = [car('sed', 'Accord', ''), car('cpe', 'Accord', ''), car('und', 'Accord', ''),
              car('lst', 'Accord Coupe', '')];
const ex = { sed: ['', '', '', '', '', 'sedan'], cpe: ['', '', '', '', '', 'coupe'] };
out.sedanGate = run([['Honda', 'Accord*', 2003, 2007, '', { body: 'Sedan' }]], cars, ex);
out.oldString = run([['Honda', 'Accord*', 2003, 2007, '', 'Sedan']], cars, ex);
out.ungated = run([['Honda', 'Accord*', 2003, 2007, '']], cars, ex);
out.mixed = run([['Honda', 'Accord*', 2003, 2007, '', { body: 'Sedan' }],
                 ['Honda', 'Accord*', 2003, 2007, '', { body: 'Coupe' }]], cars, ex);
const dcars = [car('awd', 'CR-V', 'AWD/All-Wheel Drive'), car('fwd', 'CR-V', 'FWD/Front-Wheel Drive'),
               car('nod', 'CR-V', '')];
S.model = 'CR-V';
out.driveGate = run([['Honda', 'CR-V', 2002, 2006, '', { drive: 'awd' }]], dcars, {});
console.log(JSON.stringify(out));
"""])
    p = subprocess.run([node, "-e", harness], capture_output=True, text=True, timeout=60)
    if p.returncode:
        check("node harness runs", False, p.stderr[-800:])
    else:
        o = json.loads(p.stdout)
        g = o["g"]
        want = {"sedanSedan": "confirm", "sedanCoupe": "exclude", "sedanNone": "unconfirmed",
                "coupeListing": "confirm", "coupeListingVsDecode": "confirm",
                "strSedanCoupe": "exclude", "strSedanSedan": "confirm",
                "crewPickup": "unconfirmed", "crewSuv": "exclude", "crewListing": "confirm",
                "awdAwd": "confirm", "awdFwd": "exclude", "awd4wd": "exclude", "awdMixed": "unconfirmed",
                "awdNone": "unconfirmed", "awdListing": "confirm", "fwd4x2": "exclude",
                "both": "confirm", "bothHalf": "unconfirmed", "none": "confirm"}
        bad = {k: (g.get(k), v) for k, v in want.items() if g.get(k) != v}
        check("pfAmGate verdicts match the parts-table gate semantics (20 cases)", not bad, str(bad))
        IFEQ = "if equipped"

        def warned(r, k):
            return any(IFEQ in w for w in r.get(k, []))
        r = o["sedanGate"]
        check("sedan-gated unit: decoded sedan donor offered, no if-equipped warning",
              "sed" in r and not warned(r, "sed"))
        check("sedan-gated unit: decoded coupe donor NOT offered", "cpe" not in r)
        check("sedan-gated unit: undecoded donor offered with an if-equipped warning",
              "und" in r and warned(r, "und"))
        # the parts table never excludes on the listing alone (match_vehicle: only a
        # decode excludes), so a listing that names another body stays "if equipped"
        check("sedan-gated unit: undecoded 'Accord Coupe' listing stays if equipped, as in the parts table",
              "lst" in r and warned(r, "lst"))
        check("old string a[5] behaves exactly like {body: ...}", o["oldString"] == o["sedanGate"])
        r = o["ungated"]
        check("ungated rows: every donor offered, no if-equipped line",
              set(r) == {"sed", "cpe", "und", "lst"} and not any(warned(r, k) for k in r))
        r = o["mixed"]
        check("sedan + coupe rows: both decoded donors offered, confirmed",
              {"sed", "cpe"} <= set(r) and not warned(r, "sed") and not warned(r, "cpe"))
        r = o["driveGate"]
        check("drive-gated unit: AWD decode offered, FWD decode dropped, no decode if equipped",
              "awd" in r and not warned(r, "awd") and "fwd" not in r and "nod" in r and warned(r, "nod"))
        check("category rowWarn rides every aftermarket row",
              all(any("trans-cooler" in w for w in ws) for ws in o["sedanGate"].values()))

print()
if failures:
    print(f"FAILED {len(failures)}: " + "; ".join(failures))
    sys.exit(1)
print("test_am_gates: all passed")
