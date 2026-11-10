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

# 1A fields: if_equipped (options) and cosmetic (paint)
g1 = _grp([["Honda", "Accord", 2003, 2007, "2.4L"]])
g1.update({"if_equipped": ["Fog lamp package", " Heated mirrors "], "cosmetic": True})
e = js._am_group_entry(g1, "1a")
check("1A if_equipped / cosmetic pass through (trimmed)",
      e.get("ifEquipped") == ["Fog lamp package", "Heated mirrors"] and e.get("cosmetic") is True, str(e))
e = js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L"]]), "1a")
check("no if_equipped / cosmetic: no keys emitted", "ifEquipped" not in e and "cosmetic" not in e)
for bad, why in (({"if_equipped": "Fog"}, "if_equipped not a list"), ({"if_equipped": ["<b>x</b>"]}, "markup"),
                 ({"if_equipped": ["x"] * 7}, "over 6 options"), ({"cosmetic": "yes"}, "cosmetic not bool")):
    gb = _grp([["Honda", "Accord", 2003, 2007, "2.4L"]])
    gb.update(bad)
    try:
        js._am_group_entry(gb, "1a")
        check(f"refuses {why}", False)
    except ValueError:
        check(f"refuses {why}", True)

# ---------------------------------------------- 5. groups held for new categories
# hub 2026-11-09 23:04: the 14 new categories ship with same-generation donors
# only; no OEM or aftermarket group for them reaches the payload or a lazy file
check("GROUP_HOLD_CATS covers the 14 new categories",
      {"radiator", "ac-compressor", "ac-condenser", "heater-core", "evaporator", "throttle-body",
       "fuel-pump-module", "cv-axle", "strut", "sunroof", "center-console", "door-panel",
       "blower-motor", "fog-lights"} <= js.GROUP_HOLD_CATS)
_real_load = js._load_am_layer
# hub 2026-11-10: release is per SOURCE (AM_RELEASED). am:h1 is a radiator group
# from a source NOT released (gsp): held. am:sp1 is a Spectra radiator group:
# released, so radiator gets a lazy file carrying only am:sp1.
_fake_am = [dict(js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L"]]), "gsp"), id="am:h1"),
            dict(js._am_group_entry(_grp([["Honda", "Accord", 2003, 2007, "2.4L"]]), "spectrapremium"), id="am:sp1"),
            dict(js._am_group_entry({**_grp([["Honda", "Accord", 2003, 2007, "2.4L"]]), "cat": "alternator"},
                                    "dbelectrical"), id="am:ok1")]
js._load_am_layer = lambda now=None: {"groups": _fake_am, "status": {"gsp": "ok", "spectrapremium": "ok"},
                                      "site_of": {"am:h1": "gsp", "am:sp1": "spectrapremium",
                                                  "am:ok1": "dbelectrical"}}
_fake_oem = [{"id": "oem:toyota:x1", "cat": "fog-lights", "ns": "toyota", "tier": "likely", "src": "oem",
              "label": "Toyota catalog", "note": "n", "pn": ["1"], "apps": [["Toyota", "Camry", 2007, 2009, ""]]}]
_pl = {"builtAt": "2026-11-09T00:00:00Z", "oemStatus": {}}
_lo = {"oem": _fake_oem}
js._attach_lazy_layers(_pl, _lo)
js._load_am_layer = _real_load
_cats_out = set(_lo.get("files", {}))
_released_out = {c for c in _cats_out if c in js.AM_RELEASED["spectrapremium"]}
check("held categories get no lazy file, except a category released for the source that has a group in it",
      (_cats_out & js.GROUP_HOLD_CATS) == {"radiator"} == _released_out, str(sorted(_cats_out)))
_rad = _lo.get("files", {}).get("radiator", {})
check("released Spectra radiator group gets the radiator lazy file; the non-released source's group does not",
      [g["id"] for g in _rad.get("amGroups", [])] == ["am:sp1"] and not _rad.get("oemGroups"),
      str([g["id"] for g in _rad.get("amGroups", [])]))
check("the held OEM fog-lights group gets no lazy file", "fog-lights" not in _cats_out)
check("a category outside the hold still gets its aftermarket file", "alternator" in _cats_out, str(sorted(_cats_out)))
check("the lazy index names no held category except the released radiator (aftermarket only)",
      (set((_pl.get("oemLazy") or {}).get("cats", {})) & js.GROUP_HOLD_CATS) <= {"radiator"}
      and (_pl.get("oemLazy") or {}).get("cats", {}).get("radiator", {}).get("oem", 0) == 0)
_main = js.build_interchange_payload()
check("main payload: no oemGroups / platformGroups / oemVg entry for a held category",
      not [g for g in _main.get("oemGroups") or [] if g["cat"] in js.GROUP_HOLD_CATS]
      and not [g for g in _main.get("platformGroups") or [] if g["cat"] in js.GROUP_HOLD_CATS]
      and not [c for cats in (_main.get("oemVg") or {}).values() for c in cats if c in js.GROUP_HOLD_CATS])
check("main payload ships every held category as a Parts-tab category (same-generation donors)",
      js.GROUP_HOLD_CATS <= {c["id"] for c in _main["categories"]})

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
S.model = 'Accord';
liveInventory = [car('x1', 'Accord', '')]; EX = {};
{ const res = new Map();
  pfAmRows(S, [{ ...G([['Honda', 'Accord*', 2003, 2007, '']]), ifEquipped: ['Fog lamp package'], cosmetic: true }], res, 0, null);
  out.ife = res.get('x1') ? { tier: res.get('x1').tier, warns: res.get('x1').warns } : null; }
{ const res = new Map();
  pfAmRows(S, [{ ...G([['Honda', 'Accord*', 2003, 2007, '']]), note: 'Mirror. If equipped: power, heated. Color or finish may differ; it may need paint.',
                 ifEquipped: ['power', 'heated'], cosmetic: true, option: true }], res, 0, null);
  out.ifeDup = res.get('x1') ? { tier: res.get('x1').tier, warns: res.get('x1').warns } : null; }
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
        r = o["ife"]
        check("1A if_equipped renders 'If equipped: <options>' and cosmetic 'may need paint'; row stays Likely",
              bool(r) and r["tier"] == "likely"
              and any("If equipped: Fog lamp package" in w for w in r["warns"])
              and any("may need paint" in w for w in r["warns"]), str(r))
        r = o["ifeDup"]
        check("1A note already saying 'If equipped' / 'paint': shown once, not repeated; row stays Likely",
              bool(r) and r["tier"] == "likely"
              and sum("If equipped" in w for w in r["warns"]) == 1
              and sum("paint" in w for w in r["warns"]) == 1, str(r))
        check("category rowWarn rides every aftermarket row",
              all(any("trans-cooler" in w for w in ws) for ws in o["sedanGate"].values()))

# 5. Per-SOURCE release from GROUP_HOLD_CATS (hub 2026-11-10): Spectra ships in
# its released held categories; an OEM group in the same category, a Spectra
# group in a held category not on its list, and a fuel-tank group do not.
import tempfile  # noqa: E402
sys.path.insert(0, str(HERE / "oem_fitment" / "aftermarket"))
import groups_spectra as GS  # noqa: E402

check("AM_RELEASED['spectrapremium'] == groups_spectra.SHIP_CATS (the categories its §11.4 cleared)",
      js.AM_RELEASED.get("spectrapremium") == frozenset(GS.SHIP_CATS))
check("fuel-tank is not an aftermarket category", "fuel-tank" not in js._AM_CATS)
check("released held categories are still in GROUP_HOLD_CATS (release is per source)",
      {"radiator", "ac-compressor", "ac-condenser", "heater-core", "evaporator", "throttle-body",
       "fuel-pump-module"} <= js.GROUP_HOLD_CATS)


def _am_g(gid, cat, unit, apps):
    return {"id": gid, "cat": cat, "tier": "likely", "src": "aftermarket", "label": "x", "unit": unit,
            "retrieved": "2026-11-09T20:00:00Z", "apps": apps,
            "note": f"Spectra Premium {unit} is listed for each of these vehicles; aftermarket application data."}


def _run_release(files: dict, oem: list):
    old = js.OEM_GROUPS_DIR
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / js.OEM_AM_DIR_NAME).mkdir()
        for stem, groups in files.items():
            (Path(td) / js.OEM_AM_DIR_NAME / f"{stem}.json").write_text(json.dumps(
                {"schema": 1, "src": "aftermarket", "tier": "likely", "raw": "test", "groups": groups}))
        js.OEM_GROUPS_DIR = td
        try:
            payload, lazy = {"builtAt": "2026-11-10T00:00:00Z", "oemStatus": {}}, {"oem": oem}
            js._attach_lazy_layers(payload, lazy)
        finally:
            js.OEM_GROUPS_DIR = old
    return payload, lazy.get("files") or {}


APPS = [["Honda", "Civic", 2012, 2015, "1.8L 4-cyl"], ["Acura", "ILX", 2013, 2015, "2.4L 4-cyl"]]
sp = [_am_g("am:spp:radiator:CU13221", "radiator", "CU13221", APPS),
      _am_g("am:spp:ignition-coils:C-900", "ignition-coils", "C-900", APPS),
      _am_g("am:spp:ac-condenser:7-3965", "ac-condenser", "7-3965", [APPS[0] + [{"body": "Sedan"}]]),
      _am_g("am:spp:cv-axle:X1", "cv-axle", "X1", APPS),            # held, NOT on Spectra's list
      _am_g("am:spp:fuel-tank:F1", "fuel-tank", "F1", APPS)]        # no Parts-tab category
other = [_am_g("am:oth:radiator:R9", "radiator", "R9", APPS)]       # another aftermarket source
oem = [{"id": "oem:toyota:radiator:1640031", "cat": "radiator", "tier": "likely", "src": "oem",
        "apps": [["Toyota", "Camry", 2012, 2014]], "note": "x"}]
payload, files = _run_release({"spectrapremium": sp, "othersite": other}, oem)
am_ids = {c: {g["id"] for g in d.get("amGroups", [])} for c, d in files.items()}
oem_ids = {c: {g["id"] for g in d.get("oemGroups", [])} for c, d in files.items()}
check("Spectra group in a released held category (radiator) reaches the lazy file",
      "am:spp:radiator:CU13221" in am_ids.get("radiator", set()), str(am_ids))
check("Spectra ignition-coils group reaches the lazy file", "am:spp:ignition-coils:C-900" in am_ids.get("ignition-coils", set()))
check("Spectra body-gated condenser row reaches the lazy file with its gate",
      any(a[5:] == [{"body": "Sedan"}] for g in files.get("ac-condenser", {}).get("amGroups", [])
          for a in g["apps"]))
check("OEM group in the same released category stays held",
      not any("oem:toyota:radiator:1640031" in v for v in oem_ids.values()))
check("another aftermarket source in the same category stays held",
      not any("am:oth:radiator:R9" in v for v in am_ids.values()))
check("Spectra group in a held category NOT on its release list (cv-axle) stays held",
      "cv-axle" not in files and not any("am:spp:cv-axle:X1" in v for v in am_ids.values()))
check("Spectra fuel-tank group is dropped (refused, never shipped)",
      not any("am:spp:fuel-tank:F1" in v for v in am_ids.values())
      and "fuel-tank" not in files and "ok" in (payload.get("amStatus") or {}).get("spectrapremium", ""),
      str(payload.get("amStatus")))
# fail closed per source for EVERY category (category-breadth review 2026-11-10)
coil_other = [_am_g("am:gsp:ignition-coils:G1", "ignition-coils", "G1", APPS)]
alt_db = [dict(_am_g("am:dbe:alternator:400-1", "alternator", "400-1", APPS), amps=90)]
alt_new = [_am_g("am:new:alternator:N1", "alternator", "N1", APPS)]
_p2, files2 = _run_release({"gsp": coil_other, "dbelectrical": alt_db, "newsite": alt_new}, [])
ids2 = {g["id"] for d in files2.values() for g in d.get("amGroups", [])}
check("a non-released source's ignition-coils group (coils not held) gets no lazy file",
      "am:gsp:ignition-coils:G1" not in ids2 and "ignition-coils" not in files2, str(sorted(ids2)))
check("dbelectrical alternator still ships", "am:dbe:alternator:400-1" in ids2, str(sorted(ids2)))
check("an unknown source's alternator group ships nothing", "am:new:alternator:N1" not in ids2)
check("lazy index counts the Spectra rows", (payload.get("oemLazy") or {}).get("cats", {}).get("radiator", {}).get("am") == 1)

print()
if failures:
    print(f"FAILED {len(failures)}: " + "; ".join(failures))
    sys.exit(1)
print("test_am_gates: all passed")
