#!/usr/bin/env python3
"""Manual-transmission detection, track 2: the EPA sole-offering table.

For every (model year, make, model, displacement, cylinders, drive, turbo,
supercharger) combination in EPA fueleconomy.gov's vehicles.csv, record
whether every EPA entry is a manual, or every entry is NOT a manual
(automatic, CVT, automated manual / DCT), or both kinds are listed. Then
place each lot car in the EPA rows its OWN vPIC decode points to, and claim
a transmission only where every EPA row the car could be is one kind.

Reads   scraper/manual_detect/epa/vehicles.csv (raw EPA download, gitignored;
        https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip)
        docs/data/inventory_live.json, docs/data/vehicle_extras.json,
        docs/data/vin_decodes.json.gz
        scraper/manual_detect/ground_truth.jsonl (validation)
        scraper/manual_detect/epa_sole_citations.json (independent sources,
        hand-curated: what each source says about a rule's engine/years)
Writes  scraper/manual_detect/epa_sole.json

How a car is placed (all of it must hold, or the car gets no claim):
  * identity: the car's VIN decode gives make, model and model year; the
    model year must equal the listing year. EPA rows are the UNION of every
    row whose model or baseModel answers to the feed model name OR the vPIC
    model name, under the feed make OR the vPIC make (Geo/Chevrolet,
    Scion/Toyota). The union matters: 2004 Xterra is 'Xterra 2WD' (manual
    only) and 'Xterra V6 2WD'; a closest-name match invents manual-only
    cells. When both names map to EPA rows, the union is used; when the
    vPIC model maps to nothing and differs from the feed model, the car is
    skipped (the listing name alone does not identify the car).
  * engine: the decode's DisplacementL (+/- 0.05 L) and EngineCylinders
    (when given). No displacement -> no engine-level claim.
  * drive: the decode's DriveType narrows the rows only when it is a single
    drive. If the drive changes the answer, the drive must be shown to be
    VIN-specific (the vPIC make/model/year has more than one drive in the
    decode cache); otherwise no claim.
  * turbo / supercharger / fuel: not in the compact decode, so the rows are
    the union over them (a 2.0 non-turbo and a 2.0 turbo count together).
Guards (each skips the car, counted by reason):
  * the VIN fails its check digit (49 CFR 565.15(c));
  * heavy duty (EPA does not cover > 8,500 lb GVWR): F-250/350, E-250/350,
    2500/3500/HD/Super Duty in the feed model, vPIC model, series or trim;
  * engine-default: the decoded engine is not shown to be VIN-specific (one
    engine across the vPIC make/model/year in the decode cache) while EPA
    lists more than one engine for the model-year;
  * neighbour engine: EPA lists another engine within 0.15 L (same
    cylinders) for the model-year whose rows include the other class, so a
    rounding difference could move the car;
  * sibling name: an EPA row of the same year/make/engine/drive outside
    the union whose name shares a word with the feed or vPIC model, and
    which is of the other class (catches naming variants the union missed);
  * incomplete EPA cell: a row with a blank transmission, or every row of
    the cell is a 'CA model' / '(CAL)' row (the federal car is missing);
  * automated manual filed as manual (KNOWN_AMT_AS_MANUAL: MR2 Spyder SMT
    2002-2005); EPA files SMG/F1/e-gear/Cambiocorsa as automatics;
  * vPIC model names broader than EPA names (EXTRA_EPA_NAMES: vPIC and
    yards call the 2009+ VW CC 'Passat') add those EPA rows to the union.
Flag (not a skip): EPA lists the other class for the same names/engine/
drive in the year before or after ('epa_adjacent_years_other_class').
Status: a manual claim is COUNTED only when an independent editorial or
reference source (epa_sole_citations.json) says that engine/year was
manual-only and nothing disagrees (low_sample), or >= 20 ground-truth cars
of the combination all agree (keep). EPA-only cells stay candidates: EPA
lists manual-only cells for cars that had automatics (1985 Camaro 2.5,
1985 944, 1985-87 Ranger 2.0).
Model-year-wide claims: when every EPA row of the model-year (all engines,
all drives) is one class, the decode identity alone places the car; no
engine is needed.

Validation: ground_truth.jsonl. uniformCell = manual lines are unlabelled
(vPIC model-level defaults, BASELINE.md section 2); speeds-only lines are
excluded; agree means (truth is manual) == (claim is manual). A combination
with any disagreement is dropped, and the other years of that rule become
candidates. VIN-less listing lines (Ace Jacksonville) are checked against
model-year-wide cells by feed name, the only label independent of vPIC.

Run:  python3 -I scraper/manual_detect/epa_sole.py
"""

import csv
import gzip
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"
EPA_CSV = HERE / "epa" / "vehicles.csv"
EPA_ZIP = HERE / "epa" / "vehicles.csv.zip"
CITES = HERE / "epa_sole_citations.json"
sys.path.insert(0, str(HERE.parent))
import junkyard_scraper as js  # noqa: E402  (_correct_vpic)

NEIGHBOUR_L = 0.15
KEEP_MIN = 20           # checkable ground-truth cars before a rule can be "keep"
KEEP_AGREE = 0.995

# ---------------------------------------------------------------- names ---

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&", "and"))


_EPA_STRIP = re.compile(
    r"\b(2wd|4wd|awd|fwd|rwd|4x4|4x2|pickup|cab\s*chassis|chassis\s*cab|"
    r"wagon|van|ffv|cng|lpg|conversion)\b", re.I)


def epa_stripped(s: str) -> str:
    return norm(_EPA_STRIP.sub(" ", s or ""))


def epa_keys(r: dict) -> set[str]:
    """Every key an EPA row answers to (same as epa_profile.py, union use)."""
    out = {r["model"].strip().lower(), norm(r["model"]), epa_stripped(r["model"]),
           norm(r["baseModel"])}
    for part in r["model"].split("/"):
        out.add(epa_stripped(part))
    for part in r["baseModel"].split("/"):
        out.add(norm(part))
    out.add(epa_stripped(re.sub(r"\(.*?\)", " ", r["model"])))
    return {k for k in out if k}


def name_keys(make: str, model: str) -> set[str]:
    """Keys a feed or vPIC model name looks up (epa_profile.feed_keys plus
    the stripped form, so vPIC 'S-10 Pickup' / 'Astro Van' also look up)."""
    n = norm(model)
    keys = {model.strip().lower(), n, epa_stripped(model)}
    mk = norm(make)
    if mk and n.startswith(mk) and len(n) > len(mk):
        keys.add(n[len(mk):])                          # Mazda3 -> 3
    m = re.match(r"^(.*?)(1500|2500|3500)$", n)
    if m and m.group(1):                               # Silverado 1500 -> Silverado C15/K15
        base, cls = m.group(1), m.group(2)[:2]
        keys |= {base + "c" + cls, base + "k" + cls, base + cls}
    return {k for k in keys if k}


_STOP = {"2wd", "4wd", "awd", "fwd", "rwd", "4x4", "4x2", "pickup", "cab", "chassis",
         "wagon", "van", "ffv", "cng", "lpg", "conversion", "coupe", "sedan",
         "convertible", "hatchback", "hatch", "door", "2dr", "4dr", "5dr", "3dr",
         "the", "and", "of", "incl", "new", "plus", "class", "series", "sport",
         "utility", "truck", "cargo", "passenger", "base", "hybrid", "turbo", "gt",
         "limited", "classic", "edition", "wd", "ii", "iii"}


def tokens(s: str) -> set[str]:
    toks = {t for t in re.split(r"[^a-z0-9]+", (s or "").lower().replace("&", " and "))
            if len(t) >= 2 and t not in _STOP}
    # numeric-only words ('1500', '300') link unrelated models; keep them
    # only when the name has nothing else (Mazda '3', Chrysler '300').
    alpha = {t for t in toks if not t.isdigit()}
    return alpha or toks


# Heavy duty: EPA does not cover vehicles over 8,500 lb GVWR (MDPVs before
# 2011), so EPA rows for a model name can describe only its light-duty part.
_HD_ANY = re.compile(r"(\b(2500|3500|4500|5500)\b|[CK]-?[23]500|super\s*duty|(\b|\d)HD\b)", re.I)
_HD_BY_MAKE = {
    "ford": re.compile(r"(\b[FE]-?(250|350|450|550)\b|\bexcursion\b|\btransit\b.*\b(250|350)\b)", re.I),
    "mercury": re.compile(r"\b[FE]-?(250|350)\b", re.I),
    "dodge": re.compile(r"\b[DWB]?(250|350)\b|\bsprinter\b", re.I),
    "ram": re.compile(r"\b[DWB]?(250|350)\b|\bpromaster\b", re.I),
    "plymouth": re.compile(r"\b[DWB]?(250|350)\b", re.I),
    "chevrolet": re.compile(r"\b[CKVGPR](20|30)\b|\b[CKG]?(2|3)500\b|\bkodiak\b", re.I),
    "gmc": re.compile(r"\b[CKVGPR](20|30)\b|\b[CKG]?(2|3)500\b|\btopkick\b", re.I),
    "hummer": re.compile(r"\bH[12]\b", re.I),
    "freightliner": re.compile(r".", re.I),
    "mercedes-benz": re.compile(r"\bsprinter\b", re.I),
    "nissan": re.compile(r"\bXD\b|\bNV\s?(2500|3500)\b", re.I),
}


def heavy_duty(makes: set[str], text: str) -> bool:
    if _HD_ANY.search(text):
        return True
    return any(_HD_BY_MAKE[m].search(text) for m in makes if m in _HD_BY_MAKE)

# ---------------------------------------------------------------- EPA -----

def trany_class(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("Manual"):
        return "manual"
    if "(AM" in t:
        return "amt"            # automated manual (EPA puts DCTs here too)
    if "(AV" in t or "variable gear" in t:
        return "cvt"
    if t.startswith("Automatic"):
        return "automatic"
    return "unknown"


def side(cls: str) -> str:
    """manual vs non-manual: the app's badge question."""
    return {"manual": "M", "automatic": "A", "cvt": "A", "amt": "A"}.get(cls, "?")


_DRIVE_MAP = {
    "fwd": {"Front-Wheel Drive", "2-Wheel Drive"},
    "rwd": {"Rear-Wheel Drive", "2-Wheel Drive"},
    "4x2": {"Front-Wheel Drive", "Rear-Wheel Drive", "2-Wheel Drive"},
    "awd": {"All-Wheel Drive", "4-Wheel or All-Wheel Drive", "4-Wheel Drive",
            "Part-time 4-Wheel Drive"},
    "4wd": {"4-Wheel Drive", "4-Wheel or All-Wheel Drive", "Part-time 4-Wheel Drive",
            "All-Wheel Drive"},
}


def vpic_drive_key(d: str) -> str:
    d = (d or "").lower()
    if not d or "," in d or d.startswith("2wd/4wd"):
        return ""
    for k in ("fwd", "rwd", "awd", "4wd", "4x2"):
        if d.startswith(k):
            return k
    return ""


def epa_drive_short(d: str) -> str:
    return {"Front-Wheel Drive": "FWD", "Rear-Wheel Drive": "RWD", "All-Wheel Drive": "AWD",
            "4-Wheel or All-Wheel Drive": "4WD/AWD", "4-Wheel Drive": "4WD",
            "Part-time 4-Wheel Drive": "PT4WD", "2-Wheel Drive": "2WD"}.get(d, d or "?")


_ENG = re.compile(r"^(?:(\d+(?:\.\d+)?)L)?\s*(?:(\d+)-cyl)?\s*(.*)$")


def parse_engine(e: str):
    m = _ENG.match((e or "").strip())
    if not m:
        return None, None, ""
    d = float(m.group(1)) if m.group(1) else None
    c = int(m.group(2)) if m.group(2) else None
    return d, c, (m.group(3) or "").strip()


def gt_class(t: str) -> str:
    s = (t or "").strip()
    if not s:
        return ""
    if re.search(r"manual", s, re.I) and not re.search(r"automated", s, re.I):
        return "manual"
    if re.search(r"automatic|continuously variable|\bcvt\b|dual.clutch|\bdct\b|automated|\bamt\b", s, re.I):
        return "non_manual"
    return "other"


# EPA codes the Toyota MR2 Spyder's SMT (a clutchless sequential automated
# manual, which the app does NOT call manual) as "Manual 5-spd" (2002) and
# "Manual 6-spd" (2003-2005). EPA codes the other automated manuals of that
# era as automatics (BMW SMG "Automatic (S6)", Ferrari F1, Lamborghini
# e-gear, Maserati Cambiocorsa), checked 2026-11-05. (EPA make lower-case,
# model regex, first year, last year, why).
KNOWN_AMT_AS_MANUAL = [
    ("toyota", r"^MR2", 2002, 2005,
     "MR2 Spyder SMT (sequential manual, clutchless) is listed by EPA as a manual; "
     "the toyota_mr2 note in vin_rules_2.json says the VIN does not tell it apart"),
]

# vPIC model names that cover a car EPA lists under another name. Found by
# validation: vPIC (and many yards) call the 2009+ VW CC "Passat"; EPA lists
# "CC" (with a 6-speed manual) apart from "Passat" (automatic only in
# 2009-2010), so 6 VIN-decoded manual CCs disagreed with an automatic-only
# claim. Adding rows can only make a cell more mixed, never manufacture a
# claim. (make lower-case, vPIC/feed model lower-case, first year, last
# year, extra EPA model keys).
EXTRA_EPA_NAMES = [
    ("volkswagen", "passat", 2009, 2017, ["cc", "cc4motion"]),
]

STATUS_ORDER = ["keep", "low_sample", "candidate", "drop"]


_TRANSLIT = {**{str(i): i for i in range(10)},
             **dict(zip("ABCDEFGH", range(1, 9))), **dict(zip("JKLMN", range(1, 6))),
             "P": 7, "R": 9, **dict(zip("STUVWXYZ", range(2, 10)))}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def check_digit_ok(vin: str) -> bool:
    """49 CFR 565.15(c) check digit (same as vin_rules_*.py). A VIN that fails
    it may be mistyped and decode to another car's engine."""
    if len(vin) != 17 or any(ch not in _TRANSLIT for ch in vin):
        return False
    r = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS)) % 11
    return vin[8] == ("X" if r == 10 else str(r))


def slug(s: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9.]+", "_", s.lower())).strip("_")


def main() -> int:
    if not EPA_CSV.exists():
        print(f"missing {EPA_CSV}; download vehicles.csv.zip first", file=sys.stderr)
        return 2
    with open(EPA_CSV, newline="", encoding="utf-8") as f:
        epa = list(csv.DictReader(f))
    for r in epa:
        r["_y"] = int(r["year"])
        r["_mk"] = r["make"].strip().lower()
        r["_d"] = float(r["displ"]) if re.fullmatch(r"\d+(\.\d+)?", r["displ"] or "") else None
        r["_c"] = int(r["cylinders"]) if (r["cylinders"] or "").isdigit() else None
        r["_cls"] = trany_class(r["trany"])
        r["_s"] = side(r["_cls"])
        r["_keys"] = epa_keys(r)
        r["_tok"] = tokens(r["model"]) | tokens(r["baseModel"])
        r["_ca"] = bool(re.search(r"CA model|\(CAL\)", r["eng_dscr"] or ""))
        r["_amt_as_manual"] = next((why for mk, rx, y0, y1, why in KNOWN_AMT_AS_MANUAL
                                    if r["_mk"] == mk and re.search(rx, r["model"]) and y0 <= r["_y"] <= y1), "")
    by_id = {r["id"]: r for r in epa}
    zip_sha = hashlib.sha256(EPA_ZIP.read_bytes()).hexdigest() if EPA_ZIP.exists() else ""

    # ---- 1. the EPA sole-offering table ------------------------------------
    # key: (year, make, model, displ, cylinders, drive, turbo, supercharger)
    combo = defaultdict(list)
    for r in epa:
        combo[(r["_y"], r["make"], r["model"], r["displ"], r["cylinders"], r["drive"],
               r["tCharger"] == "T", r["sCharger"] == "S")].append(r)
    table_rows = []
    table_counts = Counter()
    table_by_year = defaultdict(Counter)
    for k, rows in sorted(combo.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        sides = {r["_s"] for r in rows}
        sole = ("manual" if sides == {"M"} else "automatic" if sides == {"A"}
                else "unknown" if "?" in sides else "mixed")
        table_counts[sole] += 1
        table_by_year[k[0]][sole] += 1
        table_rows.append([k[0], k[1], k[2], k[3], k[4], k[5], int(k[6]), int(k[7]), sole,
                           sorted({r["trany"] for r in rows}), [int(r["id"]) for r in rows]])

    # ---- indexes --------------------------------------------------------------
    idx = defaultdict(set)              # (year, make_l, key) -> row ids
    by_ym = defaultdict(list)           # (year, make_l) -> rows
    for r in epa:
        for k in r["_keys"]:
            idx[(r["_y"], r["_mk"], k)].add(r["id"])
        by_ym[(r["_y"], r["_mk"])].append(r)
    MAKE_ALIAS = {"amc": "american motors corporation"}
    epa_makes_l = {r["_mk"] for r in epa}

    def make_l(m: str) -> str:
        m = (m or "").strip().lower()
        return MAKE_ALIAS.get(m, m)

    def rows_for_name(year: int, makes: set[str], make_disp: str, model: str) -> set[str]:
        out = set()
        if not model:
            return out
        for mk in makes:
            for k in name_keys(make_disp, model):
                out |= idx.get((year, mk, k), set())
        return out

    inv = json.loads((DATA / "inventory_live.json").read_text())
    fi = {f: i for i, f in enumerate(inv["fields"])}
    yards = inv["yards"]
    extras_doc = json.loads((DATA / "vehicle_extras.json").read_text())
    extras = extras_doc["extras"]
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    cache_exported = cache.pop("_exportedAt", "")
    cache = {k: v for k, v in cache.items() if isinstance(v, dict)}

    # vPIC make/model/year cells over the WHOLE decode cache: does vPIC give
    # different engines / drives inside the cell (the value comes from the
    # VIN), or one value for every VIN (possibly a model-level default)?
    cell_eng = defaultdict(Counter)
    cell_drv = defaultdict(Counter)
    for v in cache.values():
        k = (v.get("make", "").upper(), v.get("model", "").upper(), v.get("modelYear", ""))
        d, c, _ = parse_engine(v.get("engine", ""))
        if d is not None:
            cell_eng[k][(d, c)] += 1
        dk = vpic_drive_key(v.get("driveType", ""))
        if dk:
            cell_drv[k]["2wd" if dk in ("fwd", "rwd", "4x2") else "4wd"] += 1

    # ---- 2. per-car placement ---------------------------------------------------
    def place(year_feed, feed_make: str, feed_model: str, dec: dict | None, vin: str) -> dict:
        """{'state': manual | non_manual | mixed | <skip reason>, ...}"""
        if not dec:
            return {"state": "no_decode"}
        vy = str(dec.get("modelYear", ""))
        if not vy.isdigit():
            return {"state": "no_decode_year"}
        year = int(vy)
        if str(year_feed) != vy:
            return {"state": "year_conflict"}
        if year < 1984:
            return {"state": "pre_1984"}
        if not check_digit_ok(vin):
            return {"state": "bad_check_digit"}
        vmake, vmodel = dec.get("make", ""), dec.get("model", "")
        hay = " ".join([feed_model, vmodel, dec.get("series", ""), dec.get("trim", "")])
        if heavy_duty({(feed_make or "").lower(), (vmake or "").lower()}, hay):
            return {"state": "heavy_duty"}
        makes = {make_l(feed_make), make_l(vmake)} & epa_makes_l
        if not makes:
            return {"state": "no_epa_make"}

        def names_rows(y):
            Fy = rows_for_name(y, makes, feed_make, feed_model)
            Vy = rows_for_name(y, makes, vmake.title(), vmodel)
            for mk_, md_, y0, y1, keys in EXTRA_EPA_NAMES:
                if mk_ in makes and y0 <= y <= y1 and md_ in (feed_model.lower(), vmodel.lower()):
                    for k in keys:
                        Vy = Vy | idx.get((y, mk_, k), set())
            return Fy, Vy
        F, V = names_rows(year)
        if not V and vmodel and norm(vmodel) != norm(feed_model) \
                and not (norm(vmodel) in norm(feed_model) or norm(feed_model) in norm(vmodel)):
            return {"state": "identity_unverified" if F else "unmatched"}
        U = F | V
        if not U:
            return {"state": "unmatched"}
        urows = [by_id[i] for i in U]
        if any(r["_s"] == "?" for r in urows):
            return {"state": "epa_cell_incomplete"}
        ident_tok = tokens(feed_model) | tokens(vmodel)
        conflict = bool(F and V and not (F & V))
        sibling_pool = [r for mk in makes for r in by_ym[(year, mk)] if r["id"] not in U
                        and (r["_tok"] & ident_tok)]
        dk = vpic_drive_key(dec.get("driveType", ""))

        def drive_ok(r, key=dk):
            return not key or not r["drive"] or r["drive"] in _DRIVE_MAP[key]

        base = {"year": year, "names": sorted({r["model"] for r in urows}), "nameConflict": conflict}

        def adjacent(filt, s):
            """Same names/engine/drive in year-1 and year+1: rows of the other side."""
            out = []
            for y in (year - 1, year + 1):
                Fy, Vy = names_rows(y)
                other = sorted({f"{y} id {r['id']} '{r['model']}' {r['displ']}L {r['trany']}"
                                for r in (by_id[i] for i in Fy | Vy) if filt(r) and r["_s"] not in (s, "?")})
                out += other
            return out

        def finish(rows, s, level, extra):
            if s == "M":
                amt = sorted({r["_amt_as_manual"] for r in rows if r["_amt_as_manual"]})
                if amt:
                    return {**base, "state": "automated_manual_listed_as_manual", "why": amt[0]}
            if all(r["_ca"] for r in rows):
                return {**base, "state": "epa_ca_model_rows_only"}
            return {**base, **extra, "state": "manual" if s == "M" else "non_manual", "level": level,
                    "rows": sorted((r["id"] for r in rows), key=int),
                    "trany": sorted({r["trany"] for r in rows}),
                    "epaMakes": sorted({r["make"] for r in rows}),
                    "bases": sorted({r["baseModel"] or r["model"] for r in rows})}

        # model-year-wide: every row for the name union is one class
        all_sides = {r["_s"] for r in urows}
        if len(all_sides) == 1:
            s = next(iter(all_sides))
            sib_other = [r for r in sibling_pool if r["_s"] != s]
            if sib_other:
                return {**base, "state": "sibling_name", "level": "model_year",
                        "sibling": sorted({r["model"] for r in sib_other})[:6]}
            return finish(urows, s, "model_year",
                          {"displ": None, "cyl": None, "drive": "",
                           "adjacent": adjacent(lambda r: True, s)})

        d, c, fuel = parse_engine(dec.get("engine", ""))
        if d is None:
            return {**base, "state": "no_engine"}

        def eng_match(r, dd=d):
            return (r["_d"] is not None and abs(r["_d"] - dd) < 0.051
                    and (c is None or r["_c"] == c))
        erows_all = [r for r in urows if eng_match(r)]
        if not erows_all:
            return {**base, "state": "engine_not_in_epa"}
        erows = [r for r in erows_all if drive_ok(r)]
        if not erows:
            return {**base, "state": "drive_not_in_epa"}
        sides = {r["_s"] for r in erows}
        if len(sides) > 1:
            return {**base, "state": "mixed", "level": "engine"}
        s = next(iter(sides))
        other = "A" if s == "M" else "M"
        vk = (vmake.upper(), vmodel.upper(), vy)
        drive_used = ""
        if {r["_s"] for r in erows_all} != sides:
            if len(cell_drv.get(vk, Counter())) < 2:
                return {**base, "state": "drive_not_vin_specific"}
            drive_used = dk
        epa_engines = {(round(r["_d"], 1), r["_c"]) for r in urows if r["_d"] is not None}
        if len(epa_engines) > 1 and len(cell_eng.get(vk, Counter())) < 2:
            return {**base, "state": "engine_not_vin_specific"}
        for r in urows:
            if (r["_d"] is not None and 0.051 <= abs(r["_d"] - d) <= NEIGHBOUR_L + 1e-9
                    and (c is None or r["_c"] == c) and drive_ok(r) and r["_s"] == other):
                return {**base, "state": "neighbour_engine",
                        "neighbour": f"{r['displ']}L {r['model']} {r['trany']}"}
        sib = [r for r in sibling_pool if eng_match(r) and drive_ok(r) and r["_s"] == other]
        if sib:
            return {**base, "state": "sibling_name", "level": "engine",
                    "sibling": sorted({f"{r['model']} ({r['trany']})" for r in sib})[:6]}
        dfilt = (lambda r: eng_match(r) and drive_ok(r, drive_used)) if drive_used else eng_match
        # when drive does not change the answer, cite every EPA row of the engine
        return finish(erows if drive_used else erows_all, s, "engine",
                      {"displ": d, "cyl": c, "drive": drive_used,
                       "turbo": sorted({bool(r["tCharger"]) for r in erows}),
                       "super": sorted({bool(r["sCharger"]) for r in erows}),
                       "adjacent": adjacent(dfilt, s)})

    def family_of(p: dict) -> str:
        bases = "+".join(p["bases"])
        mk = "+".join(p["epaMakes"])
        if p["level"] == "model_year":
            return f"{mk}|{bases}|all engines|{p['state']}"
        return f"{mk}|{bases}|{p['displ']}L/{p['cyl'] or '?'}cyl|{p['drive'] or 'any drive'}|{p['state']}"

    combos: dict[str, dict] = {}

    def combo_for(p: dict) -> dict:
        fam = family_of(p)
        ck = f"{p['year']}|{fam}"
        if ck not in combos:
            combos[ck] = {"key": ck, "family": fam, "claim": p["state"], "year": p["year"],
                          "level": p["level"], "epaMakes": p["epaMakes"], "bases": p["bases"],
                          "names": p["names"], "displ": p["displ"], "cyl": p["cyl"], "drive": p["drive"],
                          "rows": p["rows"], "trany": p["trany"], "turbo": p.get("turbo"),
                          "super": p.get("super"), "adjacent": p.get("adjacent", []),
                          "nameConflict": False, "lot": Counter(), "feedModels": Counter(),
                          "gt": Counter(), "gtDisagree": [], "listingDisagree": []}
        cb = combos[ck]
        cb["nameConflict"] |= p["nameConflict"]
        # cars of one combination can use different drive-filtered rows
        # (a 2WD and a 4WD car when drive does not matter): keep them all
        cb["rows"] = sorted(set(cb["rows"]) | set(p["rows"]), key=int)
        cb["trany"] = sorted(set(cb["trany"]) | set(p["trany"]))
        cb["names"] = sorted(set(cb["names"]) | set(p["names"]))
        cb["adjacent"] = sorted(set(cb["adjacent"]) | set(p.get("adjacent", [])))
        return cb

    # ---- 3. lot cars ------------------------------------------------------------
    lot_state = Counter()
    lot_state_no_trans = Counter()
    lot_cars = []
    for ri, row in enumerate(inv["vehicles"]):
        vid = str(row[fi["id"]])
        vin = (row[fi["vin"]] or "").strip().upper()
        mk, md, yr = row[fi["make"]] or "", row[fi["model"]] or "", row[fi["year"]]
        ex = list(extras.get(vid) or []) + [""] * 5
        trans = ex[3] or ""
        raw = cache.get(vin) if vin else None
        dec = js._correct_vpic(raw, vin) if raw else None
        if not vin:
            p = {"state": "no_vin"}
        elif dec is None:
            p = {"state": "vin_not_in_decode_backup"}
        else:
            p = place(yr, mk, md, dec, vin)
        lot_state[p["state"]] += 1
        if not trans:
            lot_state_no_trans[p["state"]] += 1
        if p["state"] not in ("manual", "non_manual"):
            continue
        cb = combo_for(p)
        cb["lot"]["cars"] += 1
        cb["feedModels"][f"{mk} {md}"] += 1
        pub = gt_class(trans)
        cb["lot"]["no_trans" if not trans else f"published_{pub}"] += 1
        lot_cars.append({"id": vid, "vin": vin, "year": yr, "make": mk, "model": md,
                         "combo": cb["key"], "claim": p["state"], "published": trans,
                         "transSrc": (ex[4] or "vin") if trans else "",
                         "why_no_trans": ("" if trans else "vpic_trans_blank"),
                         "trim": dec.get("trim", ""), "engine": dec.get("engine", ""),
                         "drive": dec.get("driveType", ""),
                         "yard": yards[row[fi["yard"]]][0] if isinstance(row[fi["yard"]], int) else ""})

    # ---- 4. ground truth ----------------------------------------------------------
    gt_state = Counter()
    gt_by_make = defaultdict(Counter)
    listing_check = Counter()
    listing_contam = set()             # (make_l, baseModel) of a listing disagreement
    listing_disagree = []
    with open(HERE / "ground_truth.jsonl") as f:
        for line in f:
            g = json.loads(line)
            tc = gt_class(g["trans"])
            if g["source"] == "listing":
                # the only labels independent of vPIC (no VIN): model-year-wide
                # EPA cells by feed name
                if tc not in ("manual", "non_manual") or not str(g["year"]).isdigit():
                    listing_check["excluded_speeds_only_or_no_year"] += 1
                    continue
                y = int(g["year"])
                mks = {make_l(g["make"])} & epa_makes_l
                U = rows_for_name(y, mks, g["make"], g["model"]) if mks else set()
                if not U or heavy_duty({g["make"].lower()}, g["model"]):
                    listing_check["no_epa_name"] += 1
                    continue
                sides = {by_id[i]["_s"] for i in U}
                if sides in ({"M"}, {"A"}):
                    claim_m = sides == {"M"}
                    ok = claim_m == (tc == "manual")
                    listing_check[f"{'manual' if claim_m else 'non_manual'}_claim_{'agree' if ok else 'disagree'}"] += 1
                    if not ok:
                        for i in U:
                            listing_contam.add((by_id[i]["_mk"], by_id[i]["baseModel"] or by_id[i]["model"]))
                        listing_disagree.append({"year": y, "make": g["make"], "model": g["model"],
                                                 "yard": g["yard"], "listing": g["trans"],
                                                 "epa": sorted({by_id[i]["trany"] for i in U}),
                                                 "epa_names": sorted({by_id[i]["model"] for i in U}),
                                                 "epa_ids": sorted(U, key=int)})
                else:
                    listing_check["mixed"] += 1
                continue
            if g["uniformCell"] == "manual":
                gt_state["uniform_manual_unlabelled"] += 1
                continue
            if tc not in ("manual", "non_manual"):
                gt_state["speeds_only_excluded"] += 1
                continue
            vin = g["vin"]
            raw = cache.get(vin) if vin else None
            dec = js._correct_vpic(raw, vin) if raw else None
            if dec is not None and not dec.get("transmission"):
                gt_state["label_now_distrusted_by_scraper"] += 1   # VPIC_TRANS_DEFAULT_CELLS
                continue
            p = place(g["year"], g["make"], g["model"], dec, vin) if dec else {"state": "vin_not_in_decode_backup"}
            gt_state[p["state"]] += 1
            if p["state"] not in ("manual", "non_manual"):
                continue
            claim_m = p["state"] == "manual"
            truth_m = tc == "manual"
            ok = claim_m == truth_m
            cb = combo_for(p)
            cb["gt"]["checkable"] += 1
            cb["gt"]["agree" if ok else "disagree"] += 1
            if truth_m:
                cb["gt"]["truth_manual"] += 1
            if g["uniformCell"] == "auto":
                cb["gt"]["uniform_auto_lines"] += 1
            sk = "manual_claim" if claim_m else "non_manual_claim"
            gt_by_make[g["make"]][f"{sk}_checkable"] += 1
            gt_by_make[g["make"]][f"{sk}_{'agree' if ok else 'disagree'}"] += 1
            if not ok:
                cb["gtDisagree"].append({"vin": vin, "year": g["year"], "make": g["make"], "model": g["model"],
                                         "trim": g["trim"], "engine": g["engine"], "drive": g["drive"],
                                         "truth": g["trans"], "uniformCell": g["uniformCell"],
                                         "yard": g["yard"]})

    # ---- 5. citations and statuses --------------------------------------------------
    cites = json.loads(CITES.read_text()) if CITES.exists() else {"entries": []}

    def cite_entries(cb: dict) -> list[dict]:
        out = []
        for e in cites["entries"]:
            if e.get("claim", "manual") != cb["claim"]:
                continue
            if not any(e["make"].lower() == m.lower() for m in cb["epaMakes"]):
                continue
            if not any(re.search(e["base"], b, re.I) for b in cb["bases"] + cb["names"]):
                continue
            if (e.get("displ") is None) != (cb["level"] == "model_year"):
                continue
            if e.get("displ") is not None and abs(e["displ"] - (cb["displ"] or 0)) > 0.051:
                continue
            if e.get("cyl") is not None and cb["cyl"] is not None and e["cyl"] != cb["cyl"]:
                continue
            if e.get("drive") is not None and e["drive"] != cb["drive"]:
                continue
            if not (e["years"][0] <= cb["year"] <= e["years"][1]):
                continue
            out.append(e)
        return out

    fam_disagree = defaultdict(list)
    for cb in combos.values():
        if cb["gt"]["disagree"]:
            fam_disagree[cb["family"]].append(cb["year"])
        cb["listingContaminated"] = any((m.lower(), b) in listing_contam for m in cb["epaMakes"] for b in cb["bases"])

    for cb in combos.values():
        es = cite_entries(cb)
        verdicts = {e["verdict"] for e in es}
        cb["citationIds"] = [e["id"] for e in es]
        cb["verdict"] = ("contradicts" if "contradicts" in verdicts else "conflicting" if "conflicting" in verdicts
                         else "supports" if "supports" in verdicts else "")
        n, agree = cb["gt"]["checkable"], cb["gt"]["agree"]
        listing_hit = any(ld["year"] == cb["year"] and set(ld["epa_names"]) & set(cb["names"])
                          for ld in listing_disagree)
        if cb["claim"] == "non_manual":
            cb["status"] = "drop" if cb["gt"]["disagree"] or listing_hit else "not_for_badge"
            cb["statusReason"] = ("ground truth disagrees" if cb["gt"]["disagree"] else
                                  "a VIN-less listing disagrees" if listing_hit else
                                  "automatic/CVT/AMT-only cell: adds no Manual badge; kept for validation")
            continue
        if cb["gt"]["disagree"]:
            cb["status"], cb["statusReason"] = "drop", "a ground-truth car of this combination is not manual"
        elif listing_hit:
            cb["status"], cb["statusReason"] = "drop", "a VIN-less yard listing of this model-year says automatic"
        elif cb["verdict"] == "contradicts":
            cb["status"], cb["statusReason"] = "drop", "an independent source says an automatic was offered"
        elif fam_disagree.get(cb["family"]):
            cb["status"] = "candidate"
            cb["statusReason"] = f"another year of this rule disagrees with ground truth ({sorted(set(fam_disagree[cb['family']]))})"
        elif cb["listingContaminated"]:
            cb["status"], cb["statusReason"] = "candidate", "a VIN-less listing of this model line (another year) says automatic"
        elif n >= KEEP_MIN and agree / n >= KEEP_AGREE:
            cb["status"], cb["statusReason"] = "keep", f">= {KEEP_MIN} checkable ground-truth cars, agreement >= {KEEP_AGREE}"
        elif cb["verdict"] == "supports":
            cb["status"] = "low_sample"
            cb["statusReason"] = (f"fewer than {KEEP_MIN} checkable ground-truth cars; counted because an "
                                  "independent editorial/reference source states this engine/year was manual-only")
        elif cb["verdict"] == "conflicting":
            cb["status"], cb["statusReason"] = "candidate", "independent sources conflict"
        else:
            cb["status"] = "candidate"
            cb["statusReason"] = ("EPA is the only source" + (" and EPA lists an automatic for this engine in an "
                                  "adjacent year" if cb["adjacent"] else ""))

    # ---- 6. rules (families) ------------------------------------------------------------
    sibling_counted, sibling_candidate = {}, {}
    sibling_files = []
    for fpath in sorted(HERE.glob("vin_rules_[0-9].json")):
        sibling_files.append(fpath.name)
        try:
            d = json.loads(fpath.read_text())
        except (OSError, ValueError):
            continue
        for car in d.get("newly_confirmed_manual_cars", []):
            sibling_counted[str(car.get("id"))] = f"{fpath.name}:{car.get('rule')}"
        for car in d.get("candidate_rule_manual_cars", []):
            sibling_candidate[str(car.get("id"))] = f"{fpath.name}:{car.get('rule')}"

    fams = defaultdict(list)
    for cb in combos.values():
        fams[cb["family"]].append(cb)
    cite_by_id = {e["id"]: e for e in cites["entries"]}
    rules = []
    combo_rule = {}
    for fam, cbs in fams.items():
        cbs.sort(key=lambda c: c["year"])
        c0 = cbs[0]
        if c0["claim"] != "manual":
            continue
        statuses = Counter(c["status"] for c in cbs)
        counted = [c for c in cbs if c["status"] in ("keep", "low_sample")]
        best = min(statuses, key=STATUS_ORDER.index)
        rid = "epa_" + slug(f"{'_'.join(c0['epaMakes'])}_{'_'.join(c0['bases'])}_" +
                            ("all_engines" if c0["level"] == "model_year" else
                             f"{c0['displ']}l_{c0['cyl'] or 'x'}cyl_{c0['drive'] or 'anydrive'}"))
        for c in cbs:
            combo_rule[c["key"]] = rid
        feed_models = Counter()
        for c in cbs:
            feed_models.update(c["feedModels"])
        cids = sorted({i for c in cbs for i in c["citationIds"]})
        gt = Counter()
        for c in cbs:
            gt.update(c["gt"])
        rules.append({
            "id": rid,
            "claim": "manual",
            "status": best,
            "status_by_year": {str(c["year"]): c["status"] for c in cbs},
            "status_reason_by_year": {str(c["year"]): c["statusReason"] for c in cbs},
            "years_counted": [c["year"] for c in counted],
            "scope": {
                "epa_make": c0["epaMakes"],
                "epa_base_models": sorted({b for c in cbs for b in c["bases"]}),
                "epa_model_names": sorted({n for c in cbs for n in c["names"]}),
                "feed_models_on_lots": dict(feed_models.most_common()),
                "model_years": [c["year"] for c in cbs],
                "engine": None if c0["level"] == "model_year" else
                {"displacementL": c0["displ"], "cylinders": c0["cyl"],
                 "turbo_in_epa_rows": sorted({t for c in cbs for t in (c["turbo"] or [])}),
                 "supercharger_in_epa_rows": sorted({t for c in cbs for t in (c["super"] or [])})},
                "drive": c0["drive"] or "any (the answer does not depend on drive)",
                "level": c0["level"],
                "conditions": [
                    "the car's own vPIC decode (cache backup) gives make, model and ModelYear; ModelYear equals the listing year",
                    "EPA rows = union of every row whose model/baseModel answers to the feed model or the vPIC model name, "
                    "under the feed or vPIC make",
                    ("every EPA row of the model-year (all engines, drives) is a manual"
                     if c0["level"] == "model_year" else
                     f"decoded DisplacementL = {c0['displ']} (+/-0.05)" +
                     (f" and EngineCylinders = {c0['cyl']}" if c0["cyl"] else " (vPIC gives no cylinder count; rows of any cylinder count at that displacement are included)") +
                     (f"; decoded DriveType = {c0['drive']} (VIN-specific in vPIC for this model-year)" if c0["drive"] else "") +
                     "; every EPA row for that engine is a manual"),
                    "not heavy duty; no neighbouring EPA engine (0.15 L) or sibling EPA name of the other class; "
                    "engine (and drive, when it matters) shown to be VIN-specific in vPIC",
                ],
            },
            "vin_condition": "none: the rule reads the decoded make/model/year/DisplacementL/EngineCylinders"
                             + ("/DriveType" if c0["drive"] else "") + ", not a VIN character",
            "epa_rows": [{"year": c["year"], "ids": [int(i) for i in c["rows"]], "trany": c["trany"],
                          "names": c["names"]} for c in cbs],
            "epa_adjacent_years_other_class": sorted({a for c in cbs for a in c["adjacent"]})[:12],
            "citations": [{"source_id": i, "verdict": cite_by_id[i]["verdict"],
                           "years": cite_by_id[i]["years"], "sources": cite_by_id[i]["sources"],
                           "note": cite_by_id[i].get("note", "")} for i in cids]
                         + [{"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                             "doc": f"EPA fueleconomy.gov vehicles.csv (Last-Modified 2026-09-29, sha256 {zip_sha[:12]}...)",
                             "says": "; ".join(f"{c['year']}: ids {','.join(c['rows'][:6])}{'...' if len(c['rows']) > 6 else ''} "
                                               f"{'/'.join(c['trany'])}" for c in cbs)}],
            "validation": {
                "ground_truth_checkable": gt["checkable"], "agree": gt["agree"], "disagree": gt["disagree"],
                "agreement": round(gt["agree"] / gt["checkable"], 4) if gt["checkable"] else None,
                "checkable_positives_manual": gt["truth_manual"],
                "uniform_auto_lines": gt["uniform_auto_lines"],
                "disagree_examples": [x for c in cbs for x in c["gtDisagree"]][:10],
                "listing_contaminated": any(c["listingContaminated"] for c in cbs),
                "name_conflict_feed_vs_vpic": any(c["nameConflict"] for c in cbs),
            },
            "lot": {
                "cars": sum(c["lot"]["cars"] for c in cbs),
                "cars_without_trans_info": sum(c["lot"]["no_trans"] for c in cbs),
                "newly_confirmed_manual_counted": sum(c["lot"]["no_trans"] for c in counted),
                "published_manual": sum(c["lot"]["published_manual"] for c in cbs),
                "published_non_manual": sum(c["lot"]["published_non_manual"] for c in cbs),
            },
        })
    rules.sort(key=lambda r: (STATUS_ORDER.index(r["status"]), -r["lot"]["cars_without_trans_info"], r["id"]))

    combo_status = {c["key"]: c["status"] for c in combos.values()}

    newly, candidate_cars, published_conflicts = [], [], []
    for car in lot_cars:
        st = combo_status[car["combo"]]
        if car["claim"] == "manual" and not car["published"]:
            rec = {k: car[k] for k in ("id", "vin", "year", "make", "model", "trim", "engine", "drive", "why_no_trans", "yard")}
            rec["rule"] = combo_rule[car["combo"]]
            rec["status"] = st
            rec["also_vin_rule_counted"] = sibling_counted.get(car["id"], "")
            rec["also_vin_rule_candidate"] = sibling_candidate.get(car["id"], "")
            (newly if st in ("keep", "low_sample") else candidate_cars).append(rec)
        elif car["published"]:
            pub_m = gt_class(car["published"]) == "manual"
            if (car["claim"] == "manual") != pub_m and gt_class(car["published"]) in ("manual", "non_manual"):
                published_conflicts.append({k: car[k] for k in ("id", "vin", "year", "make", "model", "trim",
                                                                  "engine", "published", "transSrc", "yard")}
                                           | {"claim": car["claim"], "combo_status": st,
                                              "epa": combos[car["combo"]]["trany"],
                                              "epa_ids": combos[car["combo"]]["rows"][:8]})
    newly.sort(key=lambda r: (r["make"], r["model"], str(r["year"]), r["id"]))
    candidate_cars.sort(key=lambda r: (r["make"], r["model"], str(r["year"]), r["id"]))

    # ---- 7. per-make summaries ------------------------------------------------------------
    per_make = defaultdict(Counter)
    for car in lot_cars:
        st = combo_status[car["combo"]]
        m = per_make[car["make"]]
        m[f"{car['claim']}_claims"] += 1
        if car["claim"] == "manual" and not car["published"]:
            m["manual_no_trans_counted" if st in ("keep", "low_sample") else f"manual_no_trans_{st}"] += 1
        if car["claim"] == "non_manual" and not car["published"]:
            m["non_manual_no_trans"] += 1
    for mk, c in gt_by_make.items():
        for k, v in c.items():
            per_make[mk][f"gt_{k}"] += v
    per_make_out = {}
    for mk, c in sorted(per_make.items(), key=lambda kv: -sum(kv[1].values())):
        o = dict(c)
        for sk in ("manual_claim", "non_manual_claim"):
            n = c[f"gt_{sk}_checkable"]
            if n:
                o[f"gt_{sk}_agreement"] = round(c[f"gt_{sk}_agree"] / n, 4)
        per_make_out[mk] = o

    gt_tot = Counter()
    for c in gt_by_make.values():
        gt_tot.update(c)
    counted_combos = [c for c in combos.values() if c["claim"] == "manual" and c["status"] in ("keep", "low_sample")]
    gt_counted = Counter()
    for c in counted_combos:
        gt_counted.update(c["gt"])
    nm = [c for c in combos.values() if c["claim"] == "non_manual"]
    nm_dropped = [c for c in nm if c["status"] == "drop"]

    epa_manual_only = [r for r in table_rows if r[8] == "manual"]
    summary = {
        "epa_table_combinations": dict(table_counts),
        "epa_manual_only_combinations": len(epa_manual_only),
        "lot_cars": len(inv["vehicles"]),
        "lot_cars_without_trans_info": sum(lot_state_no_trans.values()),
        "lot_placement": dict(lot_state.most_common()),
        "lot_placement_cars_without_trans_info": dict(lot_state_no_trans.most_common()),
        "manual_rules": len(rules),
        "manual_rules_by_status": dict(Counter(r["status"] for r in rules)),
        "manual_combinations_by_status": dict(Counter(c["status"] for c in combos.values() if c["claim"] == "manual")),
        "newly_confirmed_manual_counted": len(newly),
        "newly_confirmed_manual_counted_also_counted_by_vin_rules": sum(1 for r in newly if r["also_vin_rule_counted"]),
        "newly_confirmed_manual_counted_net_new": sum(1 for r in newly if not r["also_vin_rule_counted"]),
        "newly_confirmed_manual_counted_by_make": dict(Counter(r["make"] for r in newly).most_common()),
        "newly_confirmed_manual_counted_by_rule": dict(Counter(r["rule"] for r in newly).most_common()),
        "candidate_rule_manual_cars_not_counted": len(candidate_cars),
        "candidate_rule_manual_cars_by_status": dict(Counter(r["status"] for r in candidate_cars)),
        "ground_truth_placement": dict(gt_state.most_common()),
        "ground_truth_manual_claims_all_combinations": {
            "checkable": gt_tot["manual_claim_checkable"], "agree": gt_tot["manual_claim_agree"],
            "disagree": gt_tot["manual_claim_disagree"],
            "precision": round(gt_tot["manual_claim_agree"] / gt_tot["manual_claim_checkable"], 4)
            if gt_tot["manual_claim_checkable"] else None},
        "ground_truth_manual_claims_counted_combinations": {
            "checkable": gt_counted["checkable"], "agree": gt_counted["agree"], "disagree": gt_counted["disagree"],
            "precision": round(gt_counted["agree"] / gt_counted["checkable"], 4) if gt_counted["checkable"] else None},
        "ground_truth_non_manual_claims": {
            "checkable": gt_tot["non_manual_claim_checkable"], "agree": gt_tot["non_manual_claim_agree"],
            "disagree": gt_tot["non_manual_claim_disagree"],
            "agreement": round(gt_tot["non_manual_claim_agree"] / gt_tot["non_manual_claim_checkable"], 4)
            if gt_tot["non_manual_claim_checkable"] else None,
            "combinations": len(nm), "combinations_dropped": len(nm_dropped)},
        "listing_check_model_year_cells": dict(listing_check),
        "published_labels_contradicting_an_epa_sole_cell": len(published_conflicts),
        "published_labels_contradicting_by_kind": dict(Counter(
            f"{c['claim']}_cell_vs_published_{gt_class(c['published'])}" for c in published_conflicts)),
    }

    out = {
        "worklist": "epa_sole",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/epa_sole.py",
        "inputs": {
            "epa": {"url": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
                    "file": "scraper/manual_detect/epa/vehicles.csv (gitignored)", "sha256_zip": zip_sha,
                    "rows": len(epa)},
            "inventory_live": f"docs/data/inventory_live.json ({inv.get('scrapedAt')})",
            "vehicle_extras": f"docs/data/vehicle_extras.json ({extras_doc.get('scrapedAt')}; reflects the scraper's "
                              "VPIC_TRANS_DEFAULT_CELLS drop)",
            "vin_decodes": f"docs/data/vin_decodes.json.gz (exported {cache_exported}, {len(cache)} decodes)",
            "ground_truth": "scraper/manual_detect/ground_truth.jsonl (built 2026-11-05 before the "
                            "VPIC_TRANS_DEFAULT_CELLS drop; uniformCell=manual lines and lines whose decode the "
                            "scraper now distrusts are unlabelled)",
            "citations": "scraper/manual_detect/epa_sole_citations.json",
            "sibling_vin_rules": f"overlap only, read at run time: {', '.join(sibling_files)}",
        },
        "answer": (
            f"EPA lists only manuals for {len(epa_manual_only)} of {sum(table_counts.values())} "
            "year/make/model/engine/drive/turbo combinations. Placed by each car's own vPIC decode (union of EPA "
            f"names, decoded engine and drive, with guards), {sum(lot_state[k] for k in ('manual',))} lot cars fall "
            f"in a manual-only cell; {len(newly)} of them have no transmission today and sit in a counted rule "
            f"(independent source + no ground-truth disagreement), {sum(1 for r in newly if not r['also_vin_rule_counted'])} "
            "of them not already counted by a VIN-rule worklist. EPA alone is not enough: 1985 Camaro 2.5, 1985 "
            "944, 1985 MR2 (one CA row) and 1985-87 Ranger 2.0 are manual-only in EPA although automatics were "
            "sold, and the 2002-05 MR2 SMT is filed as a manual. So EPA-only cells stay candidates "
            f"({len(candidate_cars)} lot cars without transmission info)."),
        "method": __doc__.split("Run:")[0].strip(),
        "status_definitions": {
            "keep": f">= {KEEP_MIN} checkable ground-truth cars in the combination and agreement >= {KEEP_AGREE}",
            "low_sample": f"< {KEEP_MIN} checkable, no disagreement, and an independent editorial/reference source "
                          "(not a sale listing, forum post or EPA-derived table) states the engine/year was manual-only; "
                          "counted",
            "candidate": "not counted: EPA is the only source, sources conflict, or another year of the same rule "
                         "disagrees with ground truth / a listing",
            "drop": "a ground-truth car or VIN-less listing of the combination is not manual, a source says an "
                    "automatic was offered, or EPA's manual row is a known automated manual",
            "not_for_badge": "automatic/CVT/AMT-only combination; adds no Manual badge, reported for validation",
        },
        "summary": summary,
        "per_make": per_make_out,
        "rules": rules,
        "newly_confirmed_manual_cars": newly,
        "candidate_rule_manual_cars": candidate_cars,
        "published_label_conflicts": published_conflicts,
        "non_manual_combinations_dropped": [{"key": c["key"], "trany": c["trany"], "rows": c["rows"][:8],
                                            "gt": dict(c["gt"]), "disagree_examples": c["gtDisagree"][:5]}
                                           for c in nm_dropped],
        "listing_disagreements": listing_disagree,
        "epa_table": {
            "key": ["year", "make", "model", "displ", "cylinders", "drive", "turbo", "supercharger"],
            "counts": dict(table_counts),
            "counts_by_year": {str(y): dict(c) for y, c in sorted(table_by_year.items())},
            "full_table_file": "scraper/manual_detect/epa_sole_table.json.gz",
            "manual_only_columns": ["year", "make", "model", "displ", "cylinders", "drive", "turbo",
                                    "supercharger", "sole", "trany", "epa_ids"],
            "manual_only": epa_manual_only,
        },
    }
    (HERE / "epa_sole.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    with gzip.open(HERE / "epa_sole_table.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"source": out["inputs"]["epa"],
                   "columns": out["epa_table"]["manual_only_columns"],
                   "sole_values": "manual = every EPA row is a manual; automatic = every row is an automatic, CVT "
                                  "or automated manual/DCT; mixed = both; unknown = a row has no transmission",
                   "rows": table_rows}, f, separators=(",", ":"))
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
