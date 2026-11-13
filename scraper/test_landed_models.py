#!/usr/bin/env python3
"""Tests for docs/data/landed/ (_write_landed_models_json), the data behind
the public /landed/<make>/<model> pages in backend/site-proxy/src/share.js
(seo/model-pages, 2026-11-13).

Covers:
  1. Which models get a page: LANDED_MODEL_MIN_ON_LOTS on the lots, or
     LANDED_MODEL_MIN_WEEK set out this week; blank and no-pick names never.
  2. Counts: on the lots, set out in the last LANDED_DAYS days (old and
     undated cars excluded, same rule as landed.json), by state.
  3. Rows [year, yard, row, date, drive, trim, key], newest first, yards
     re-indexed into the make file's own short list.
  4. drive only from the VIN decode ("4x4", "AWD", "2WD"; "" when it does not
     say one thing); trim only when the app's notable-trim rule names one
     (usable decode, one trim, no "non"); otherwise "".
  5. index.json lists every page; files for makes that no longer qualify go.
  6. notable_trim_hits agrees with docs/app.js notableTrimHits (run in node
     when node is installed; skipped and said so otherwise).
  7. landed.json is unchanged by the new writer.

Run:  python3 scraper/test_landed_models.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


today = date.today().isoformat()
d1 = (date.today() - timedelta(days=1)).isoformat()
d7 = (date.today() - timedelta(days=js.LANDED_DAYS)).isoformat()      # still this week (landed.json rule)
d8 = (date.today() - timedelta(days=js.LANDED_DAYS + 1)).isoformat()  # not
old = (date.today() - timedelta(days=40)).isoformat()

MIN = js.LANDED_MODEL_MIN_ON_LOTS
WEEK = js.LANDED_MODEL_MIN_WEEK
yards = [
    ["Pick-n-Pull - Phoenix", "Phoenix", "AZ", 33.4, -112.0, 60, "yard"],
    ["Pull-A-Part - Springfield", "Springfield", "MO", 37.2, -93.3, 50, "yard"],
    ["Unused Yard", "Nowhere", "TX", 30.0, -97.0, None, None],
    ["Calgary Pick-a-Part", "Calgary", "AB", 51.0, -114.0, None, None],
    ["Stateless U-Pull", "", "", None, None, None, None],
]
vehicles = []
vpic = {}


def add(id_, vin, year, make, model, row, d, yard, vp=None):
    if vp is not None:
        vpic[str(len(vehicles))] = vp
    vehicles.append([id_, vin, year, make, model, row, d, yard, 0, 0, 0])


# Nissan Xterra: MIN on the lots, 5 this week with mixed decodes.
add(1, "XT1", 2008, "Nissan", "Xterra", "25", d1, 1, ["Off-Road", "usable", "", "4WD/4-Wheel Drive/4x4", ""])
add(2, "XT2", 2005, "Nissan", "Xterra", "", today, 0, ["SE", "usable", "", "4x2", ""])
add(3, "XT3", 2002, "Nissan", "Xterra", "A7", today, 0, ["", "empty", "", "", ""])
add(4, "", 2011, "Nissan", "Xterra", "3", d7, 3, ["Pro-4X, S", "usable", "", "2WD/4WD", ""])
add("ipull-5", "", 2001, "Nissan", "Xterra", "9", today, 4)
add(6, "XT6", 2010, "Nissan", "Xterra", "1", d8, 1)
add(7, "XT7", 2009, "Nissan", "Xterra", "2", "", 1)
for i in range(MIN - 7):
    add(100 + i, f"XTOLD{i}", 2003, "Nissan", "Xterra", "4", old, 0)
# Nissan Frontier: under MIN on the lots but WEEK set out this week.
for i in range(WEEK):
    add(500 + i, f"FR{i}", 2006, "Nissan", "Frontier", "5", today, 1, ["", "", "", "AWD/All-Wheel Drive", ""] if i == 0 else None)
# Nissan Cube: under both thresholds -> no page.
for i in range(WEEK - 1):
    add(600 + i, f"CU{i}", 2010, "Nissan", "Cube", "6", today, 1)
# Subaru Outback: MIN on the lots; XT only when the decode names it alone.
add(700, "OB1", 2008, "Subaru", "Outback", "7", today, 0, ["OBK 2.5XT LTD", "usable", "", "AWD/All-Wheel Drive", ""])
add(701, "OB2", 2008, "Subaru", "Outback", "7", today, 0, ["2.5X", "usable", "", "AWD/All-Wheel Drive", ""])
add(702, "OB3", 2008, "Subaru", "Outback", "7", today, 0, ["XT Limited", "ambiguous", "", "", ""])
add(703, "OB4", 2008, "Subaru", "Outback", "7", today, 0, ["2.5i, XT", "usable", "", "", ""])
add(704, "OB5", 2008, "Subaru", "Outback", "7", today, 0, ["non XT", "usable", "", "", ""])
for i in range(MIN - 5):
    add(800 + i, f"OBOLD{i}", 2008, "Subaru", "Outback", "7", old, 1)
# Blank model and a no-pick name: never a page however many.
for i in range(MIN):
    add(2000 + i, "", 2000, "Ford", "", "1", today, 0)
    add(3000 + i, "", 2000, "Ford", "Toyota Camry", "1", today, 0)

payload = {
    "scrapedAt": "2026-11-13T07:41:48Z",
    "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"],
    "yardFields": ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"],
    "yards": yards, "vehicles": vehicles, "vpic": vpic,
    "noPickModels": {"Ford": ["Toyota Camry"]},
    "modelYears": {"Nissan": {"Xterra": [2000, 2015]}, "Subaru": {"Outback": [2000, 2015]}},
    "notableTrims": {"Nissan": {"Xterra": ["Off-Road", "Pro-4X"]}, "Subaru": {"Outback": ["XT"]}},
}

with tempfile.TemporaryDirectory() as tmp:
    js.DATA_DIR = Path(tmp)
    js._write_landed_json(payload)
    landed_before = (Path(tmp) / "landed.json").read_text()
    (Path(tmp) / "landed").mkdir()
    (Path(tmp) / "landed" / "yugo.json").write_text("{}")      # a make from an earlier scan
    info = js._write_landed_models_json(payload)
    js._write_landed_json(payload)
    check("landed.json unchanged by the model writer", (Path(tmp) / "landed.json").read_text() == landed_before)
    files = sorted(p.name for p in (Path(tmp) / "landed").glob("*.json"))
    idx = json.loads((Path(tmp) / "landed" / "index.json").read_text())
    nissan = json.loads((Path(tmp) / "landed" / "nissan.json").read_text())
    subaru = json.loads((Path(tmp) / "landed" / "subaru.json").read_text())
    # Payload without notableTrims (a scan from before the field): the
    # writer derives the table from modelYears the way the scan does.
    p2 = dict(payload)
    del p2["notableTrims"]
    js._write_landed_models_json(p2)
    nissan2 = json.loads((Path(tmp) / "landed" / "nissan.json").read_text())

check("one file per make plus the index; stale make file removed", files == ["index.json", "nissan.json", "subaru.json"], files)
check("summary counts", info == {"makes": 2, "models": 3}, info)
models = {m["model"]: m for m in nissan["models"]}
check("Xterra (MIN on lots) and Frontier (WEEK this week) get pages; Cube does not",
      sorted(models) == ["Frontier", "Xterra"], sorted(models))
check("blank and no-pick model names never get a page", "ford.json" not in files and "Ford" not in idx["makes"])
x = models["Xterra"]
check("on the lots: every Xterra in the payload", x["total"] == MIN, x["total"])
check("this week: today..today-7 only (old, day 8 and undated left out)", x["recentCount"] == 5 and len(x["recent"]) == 5, x["recentCount"])
check("on the lots by state (stateless yard not counted)",
      x["states"] == {"AB": 1, "AZ": 2 + MIN - 7, "MO": 3}, x["states"])
check("newest first", [r[3] for r in x["recent"]] == sorted([r[3] for r in x["recent"]], reverse=True))
byk = {r[6]: r for r in x["recent"]}
check("row shape [year, yard, row, date, drive, trim, key]", byk["XT1"][0] == 2008 and byk["XT1"][2] == "25" and byk["XT1"][3] == d1, byk["XT1"])
check("key is the VIN, else the id", "ipull-5" in byk and "4" in byk, sorted(byk))
check("yard indexes point into the make file's own yard list",
      nissan["yards"][byk["XT1"][1]] == ["Pull-A-Part - Springfield", "Springfield", "MO"]
      and nissan["yards"][byk["4"][1]] == ["Calgary Pick-a-Part", "Calgary", "AB"], nissan["yards"])
check("make file carries only yards its rows use", all(y[0] != "Unused Yard" for y in nissan["yards"]))
check("drive: 4WD decode -> 4x4", byk["XT1"][4] == "4x4")
check("drive: 4x2 decode -> 2WD", byk["XT2"][4] == "2WD")
check("drive: empty decode -> unknown", byk["XT3"][4] == "")
check("drive: '2WD/4WD' -> unknown (never guessed)", byk["4"][4] == "")
check("drive: no decode at all -> unknown", byk["ipull-5"][4] == "")
check("drive: AWD named as AWD", models["Frontier"]["recent"][-1][4] == "AWD" or any(r[4] == "AWD" for r in models["Frontier"]["recent"]))
check("trim: usable single-trim decode names it", byk["XT1"][5] == "Off-Road", byk["XT1"])
check("trim: a trim that is not notable -> ''", byk["XT2"][5] == "")
check("trim: a decode listing several trims -> ''", byk["4"][5] == "", byk["4"])
check("trim: no decode -> ''", byk["XT3"][5] == "" and byk["ipull-5"][5] == "")
ob = {r[6]: r[5] for r in subaru["models"][0]["recent"]}
check("Outback XT: '2.5XT' decode is XT; '2.5X' is not", ob["OB1"] == "XT" and ob["OB2"] == "", ob)
check("Outback XT: ambiguous quality, a list, or 'non XT' -> ''", ob["OB3"] == "" and ob["OB4"] == "" and ob["OB5"] == "", ob)
check("no notableTrims in the payload: derived from modelYears (no crash)", isinstance(nissan2["models"], list))

check("index: thresholds stated", idx["minOnLots"] == MIN and idx["minWeek"] == WEEK and idx["days"] == js.LANDED_DAYS)
check("index: models with pages, most on the lots first",
      idx["makes"]["Nissan"]["models"] == [["Xterra", "xterra", MIN, 5], ["Frontier", "frontier", WEEK, WEEK]], idx["makes"]["Nissan"])
check("index: make slug and totals", idx["makes"]["Nissan"]["slug"] == "nissan" and idx["makes"]["Nissan"]["recentCount"] == 5 + WEEK)
check("index: scan time carried", idx["scrapedAt"] == payload["scrapedAt"] and nissan["scrapedAt"] == payload["scrapedAt"])

# slug: same as share.js slugify
for s, want in [("Mercedes-Benz", "mercedes-benz"), ("F-150", "f-150"), ("Grand Cherokee", "grand-cherokee"),
                ("Town & Country", "town-and-country"), ("CR-V ", "cr-v"), ("Mazda3", "mazda3"), ("", "")]:
    check(f"slug {s!r}", js.landed_slug(s) == want, js.landed_slug(s))
for d, want in [("4WD/4-Wheel Drive/4x4", "4x4"), ("4x2", "2WD"), ("FWD/Front-Wheel Drive", "2WD"),
                ("RWD/Rear-Wheel Drive", "2WD"), ("AWD/All-Wheel Drive", "AWD"), ("2WD/4WD", ""),
                ("6x4", ""), ("Other", ""), ("Not Applicable", ""), ("", ""), (None, "")]:
    check(f"drive {d!r} -> {want!r}", js.landed_drive(d) == want, js.landed_drive(d))

# 6. The port against the app's own JS.
TABLE = {
    "Subaru": {"Forester": ["XT"], "Outback": ["XT", "Wilderness"], "Impreza": ["RS", "2.5RS", "WRX", "STI"]},
    "Hyundai": {"Elantra": ["N", "Sport", "N Line"]},
    "Dodge": {"Dakota": ["R/T"]},
    "Toyota": {"4Runner": ["Trail", "TRD Off-Road", "TRD Pro", "Limited"]},
    "Volkswagen": {"Golf": ["GTI", "R", "Autobahn"], "Jetta": ["GLI", "R"]},
    "Ford": {"Fiesta": ["ST"], "Mustang": ["GT"]},
}
CASES = [
    ("Subaru", "Forester", "2.5XT", "usable", ""), ("Subaru", "Forester", "2.5X", "usable", ""),
    ("Subaru", "Outback", "OBK 2.5XT LTD", "usable", ""), ("Subaru", "Outback", "XT Limited", "usable", ""),
    ("Subaru", "Outback", "XT Limited", "ambiguous", ""), ("Subaru", "Outback", "2.5i / XT", "usable", ""),
    ("Subaru", "Impreza", "2.5RS", "usable", ""), ("Subaru", "Impreza", "WRX STI", "usable", ""),
    ("Hyundai", "Elantra", "N Line", "usable", ""), ("Hyundai", "Elantra", "N", "usable", ""),
    ("Hyundai", "Elantra", "Sport, N", "usable", ""), ("Dodge", "Dakota", "R/T", "usable", ""),
    ("Dodge", "Dakota", "Sport, R/T", "usable", ""), ("Toyota", "4Runner", "Luxury", "usable", ""),
    ("Toyota", "4Runner", "Grade: TRD Pro", "usable", ""), ("Toyota", "4Runner", "SR5", "usable", "TRD Off-Road"),
    ("Volkswagen", "Jetta", "R-Line", "usable", ""), ("Volkswagen", "Golf", "R", "usable", ""),
    ("Ford", "Fiesta", "ST-Line", "usable", ""), ("Ford", "Fiesta", "ST", "usable", ""),
    ("Ford", "Mustang", "GT Premium", "usable", "non GT"), ("Ford", "Mustang", "", "usable", ""),
    ("Ford", "Mustang", "Grand Touring", "usable", ""), ("Subaru", "Outback", "Limited w/XT", "usable", ""),
]
py = [js.notable_trim_hits(mk, TABLE[mk][md], t, q, s) for mk, md, t, q, s in CASES]
check("port: '2.5XT' is XT, '2.5X' is not", py[0] == ["XT"] and py[1] == [], py[:2])
check("port: 'N Line' beats 'N'", py[8] == ["N Line"], py[8])
check("port: 'R-Line' is not the R", py[16] == [], py[16])
node = shutil.which("node")
app = Path(__file__).resolve().parent.parent / "docs" / "app.js"
if not node:
    print("  SKIP JS cross-check: node is not installed")
else:
    js_src = r"""
const fs = require('fs'), vm = require('vm');
const [appPath, dataPath] = process.argv.slice(2);
const src = fs.readFileSync(appPath, 'utf8'), lines = src.split('\n');
const fn = (n) => { const i = lines.findIndex(l => l.startsWith(`function ${n}(`)); const j = lines.findIndex((l, k) => k > i && l === '}'); if (i < 0 || j < 0) throw new Error('missing ' + n); return lines.slice(i, j + 1).join('\n'); };
const a = src.indexOf('const TRIM_ALIASES = ['), b = src.indexOf('function vpicFilterMatches(');
const ctx = vm.createContext({});
vm.runInContext([src.slice(a, b), 'let notableTrims = null;', lines.find(x => x.startsWith('const TRIM_NEGATION =')),
  ...['setNotableTrims', 'notableTrimWords', 'trimAlternatives', 'notableTrimHits'].map(fn),
  'globalThis.__t = { setNotableTrims, notableTrimHits };'].join('\n'), ctx);
const { table, cases } = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
ctx.__t.setNotableTrims(table);
console.log(JSON.stringify(cases.map(([make, model, vpicTrim, q, vpicSeries]) => [...ctx.__t.notableTrimHits({ make, model, vpicTrim, vpicTrimQuality: q, vpicSeries })])));
"""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "c.json").write_text(json.dumps({"table": TABLE, "cases": CASES}))
        (Path(tmp) / "run.js").write_text(js_src)
        res = subprocess.run([node, str(Path(tmp) / "run.js"), str(app), str(Path(tmp) / "c.json")],
                             capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            check("JS cross-check ran", False, res.stderr.strip()[-300:])
        else:
            got = json.loads(res.stdout)
            diffs = [(c, g, p) for c, g, p in zip(CASES, got, py) if g != p]
            check(f"notable_trim_hits agrees with app.js notableTrimHits on {len(CASES)} decodes", not diffs, diffs[:3])

print(f"\n{len(failures)} failure(s)" if failures else "\nall passed")
sys.exit(1 if failures else 0)
