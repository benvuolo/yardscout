#!/usr/bin/env python3
"""Aftermarket interchange layer: DB Electrical application lists -> Likely
alternator / starter groups. Offline; no network import.

    python3 scraper/oem_fitment/aftermarket/groups_am.py \
        [--raw FILE | --raw-ref origin/oem-raw] [--out FILE] [--report FILE]

What a group claims (and what it does not):

- One group per DB Electrical unit (category + item number). Cars in a group
  are the vehicles DB Electrical prints in that unit's Applications List, so
  two lot cars in one group take the same aftermarket unit. That is
  aftermarket evidence, not the carmaker's: tier is always "likely", src is
  "aftermarket", and nothing here can reach Verified (CURATION_SPEC §12).
- Different units are never merged, so different amperages are never
  collapsed. When one vehicle-year/engine appears on units of different
  amperage, every app row involved carries an `amperage_split` condition
  naming the amperages (the puller matches the tag).
- Each app row keeps the engine DB Electrical printed. A lot car belongs to
  a row only when its decoded engine agrees (liters within 0.05, cylinders
  when both sides state them, diesel only with diesel); an undecoded engine
  or a row with no engine is kept with a condition, never as a match.
- Records the crawler flagged as unverified are not used (README:
  "Treat flagged records as unverified"), except the two flags that do not
  touch applications: `no_carmaker_oe_numbers` and `unparsed_replaces_row`.
- Models: the application make/model goes through the scraper's own
  normalize_make / normalize_model. Combined makes ("Chevrolet / GMC") and
  names that match no lot model are reported, never guessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SITE = "www.dbelectrical.com"
RAW_PATH = f"aftermarket/raw/{SITE}.jsonl"
CATS = ("alternator", "starter")
HARMLESS_FLAGS = ("no_carmaker_oe_numbers", "unparsed_replaces_row")
SCHEMA = 1


# ----------------------------------------------------------------- engines
def parse_engine(s: str):
    """(liters, cylinders, diesel) from either feed's engine cell or a lot
    engine string ("3.5L 6-cyl"). Unknown parts are None."""
    sl = str(s or "").lower()
    lm = re.search(r"(\d+\.\d+)\s*l\b", sl) or re.search(r"(\d+\.\d+)l", sl)
    lit = float(lm.group(1)) if lm else None
    cyl = None
    m = (re.search(r"(\d+)[\s-]*cyl", sl) or re.search(r"\b[vlih](\d{1,2})\b", sl)
         or re.search(r"\bw(\d{1,2})\b", sl))
    if m:
        cyl = int(m.group(1))
    return lit, cyl, ("diesel" in sl)


def engine_agrees(row_eng, car_eng) -> bool | None:
    """True / False when both engines are known, None when either side is
    missing (kept, but only with a condition)."""
    rl, rc, rd = row_eng
    cl, cc, cd = car_eng
    if rl is None or cl is None:
        return None
    if abs(rl - cl) >= 0.05:
        return False
    if rc is not None and cc is not None and rc != cc:
        return False
    if rd != cd:
        return False
    return True


_TRANS = [(re.compile(r"\bw/\s*(?:a/?t|auto)\b|\bauto(?:matic)?\s+trans", re.I), "AT"),
          (re.compile(r"\bw/\s*(?:m/?t|man)\b|\bmanual\s+trans|\bfor manual\b", re.I), "MT")]


def unit_trans(r: dict):
    """"AT" / "MT" when every transmission mention in the unit's own Fits
    text and Unit Type agrees on one; None otherwise (no gate)."""
    text = " ".join([r.get("fits_text") or "", str((r.get("specs") or {}).get("Unit Type") or ""),
                     r.get("title") or ""])
    seen = {t for rx, t in _TRANS if rx.search(text)}
    return seen.pop() if len(seen) == 1 else None


def car_trans(s: str):
    sl = str(s or "").lower()
    if "manual" in sl:
        return "MT"
    if "automatic" in sl or "cvt" in sl or "auto" in sl:
        return "AT"
    return None


# ----------------------------------------------------------------- records
def load_raw(raw: str | None, raw_ref: str | None) -> tuple[list, str]:
    if raw:
        text = Path(raw).read_text()
        src = raw
    else:
        ref = raw_ref or "origin/oem-raw"
        text = subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{RAW_PATH}"],
                              check=True, capture_output=True, text=True).stdout
        sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", ref], check=True,
                             capture_output=True, text=True).stdout.strip()
        src = f"{ref}@{sha[:8]}:{RAW_PATH}"
    return [json.loads(l) for l in text.splitlines() if l.strip()], src


def accept(r: dict) -> str | None:
    """None if the record may be used, else the refusal reason."""
    if r.get("site") != SITE:
        return "other_site"
    if r.get("category") not in CATS:
        return "category"
    for f in r.get("flags") or []:
        if not f.startswith(HARMLESS_FLAGS):
            return "flag:" + f.split(":")[0]
    if not r.get("applications"):
        return "no_applications"
    return None


def fits_liters(r: dict) -> set:
    """Engine sizes the unit's own Fits text states (e.g. "CHRYSLER 3.3L
    1990-91" -> {3.3}). Empty when it states none."""
    return {float(x) for x in re.findall(r"(\d+\.\d)\s*l\b", str(r.get("fits_text") or "").lower())}


def row_contradicts_fits(a: dict, fl: set) -> bool:
    """An application row whose engine size is not among the sizes the
    unit's own Fits text states. Seen on real records: Fiat 500 1.4L rows
    on 410-52066 ("CHRYSLER 3.3L 1990-91") and 410-52033 ("DODGE TRUCKS
    3.9L, 5.2L, 5.9L"). Such rows are dropped, never claimed."""
    if not fl:
        return False
    lit = parse_engine(a.get("engine", ""))[0]
    return lit is not None and not any(abs(lit - x) < 0.05 for x in fl)


_YR = re.compile(r"\b((?:19|20)\d\d)\s*-\s*((?:19|20)?\d\d|on)\b", re.I)


def fits_year_lines(r: dict) -> list:
    """[(upper-case line, [(lo, hi), ...])] for every Fits line that states
    an explicit year range ("MINI COOPER 1.6L 2006-10" -> 2006-2010;
    "2007-ON" -> open-ended)."""
    out = []
    for line in str(r.get("fits_text") or "").splitlines():
        spans = []
        for a, b in _YR.findall(line):
            lo = int(a)
            if b.lower() == "on":
                hi = 9999
            elif len(b) == 2:
                hi = (lo // 100) * 100 + int(b)
                if hi < lo:
                    hi += 100
            else:
                hi = int(b)
            spans.append((lo, hi))
        if spans:
            out.append((line.upper(), spans))
    return out


def _names_in(line: str, word: str) -> bool:
    w = str(word or "").upper().strip()
    return bool(w) and re.search(r"(?<![A-Z0-9])" + re.escape(w) + r"(?![A-Z0-9])", line) is not None


def row_outside_fits_years(a: dict, canon, yl: list) -> bool:
    """True when the unit's own Fits text gives an explicit year range for
    this row's make AND model and the row's years fall outside every such
    range. Seen: 400-24253 Fits "MINI COOPER 1.6L 2006-10" while its rows
    list Cooper to 2015. Models the Fits text does not name keep their rows."""
    if not yl:
        return False
    mk = canon[0] if canon else a.get("make", "")
    models = {a.get("model", "")} | ({canon[1]} if canon else set())
    spans = [sp for line, sps in yl for sp in sps
             if (_names_in(line, mk) or _names_in(line, a.get("make", "")))
             and any(_names_in(line, m) for m in models)]
    if not spans:
        return False
    y0, y1 = a["years"]
    return not any(lo <= y0 and y1 <= hi for lo, hi in spans)


def amps(r: dict):
    a = str((r.get("specs") or {}).get("Amperage") or "").strip()
    return int(a) if a.isdigit() else None


# ------------------------------------------------------------------ models
class Names:
    """make/model canonicaliser backed by the scraper's own normalizers,
    plus the lot's (make, model) list to report names that match nothing."""

    def __init__(self, lot_models: set | None = None):
        sys.path.insert(0, str(HERE.parents[1]))
        import junkyard_scraper as js  # noqa: E402  (no network at import)
        self.js = js
        self.lot = lot_models
        self.lot_sq = None
        if lot_models is not None:
            self.lot_sq = defaultdict(dict)
            for mk, md in lot_models:
                self.lot_sq[mk][squash(md)] = md
        self._c: dict = {}

    def canon(self, make: str, model: str):
        k = (make, model)
        if k in self._c:
            return self._c[k]
        out = None
        mk = self.js.normalize_make(make, model)
        if mk and "/" not in mk:
            cands = [model, self.js.normalize_model(model, mk)]
            if self.lot_sq is not None:
                hit = next((self.lot_sq.get(mk, {}).get(squash(c)) for c in cands
                            if squash(c) in self.lot_sq.get(mk, {})), None)
                out = (mk, hit, True) if hit else (mk, cands[1], False)
            else:
                out = (mk, cands[1], None)
        self._c[k] = out
        return out


def squash(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


# ------------------------------------------------------------------ build
def _runs(years: list) -> list:
    ys = sorted(set(years))
    out, lo = [], None
    for i, y in enumerate(ys):
        if lo is None:
            lo = y
        if i + 1 == len(ys) or ys[i + 1] != y + 1:
            out.append((lo, y))
            lo = None
    return out


def _eng_label(e: str) -> str:
    lit, cyl, dsl = parse_engine(e)
    if lit is None:
        return ""
    return f"{lit:.1f}L" + (f" {cyl}-cyl" if cyl else "") + (" diesel" if dsl else "")


def build(records: list, names: Names, src: str = "") -> dict:
    refused = Counter()
    unmapped = Counter()
    combined = Counter()
    dropped_rows = Counter()
    dropped_years = Counter()
    groups = []
    for r in sorted(records, key=lambda r: (r.get("category", ""), r.get("aftermarket_pn", ""))):
        why = accept(r)
        if why:
            refused[why] += 1
            continue
        rows = defaultdict(list)       # (make, model, engine label) -> years
        dsl = set()                    # (make, model, year, liters) printed as diesel on this unit
        fl = fits_liters(r)
        yl = fits_year_lines(r)
        apps_in = []
        for a in r["applications"]:
            if row_contradicts_fits(a, fl):
                dropped_rows[f"{r['aftermarket_pn']}: {a.get('raw', '')}"] += 1
                continue
            if row_outside_fits_years(a, names.canon(a.get("make", ""), a.get("model", "")), yl):
                dropped_years[f"{r['aftermarket_pn']}: {a.get('raw', '')}"] += 1
                continue
            apps_in.append(a)
        for a in apps_in:
            c = names.canon(a.get("make", ""), a.get("model", ""))
            lit, _cy, d = parse_engine(a.get("engine", ""))
            if c and d and lit is not None:
                for y in range(a["years"][0], a["years"][1] + 1):
                    dsl.add((c[0], c[1], y, lit))
        for a in apps_in:
            c = names.canon(a.get("make", ""), a.get("model", ""))
            if c is None:
                combined[f"{a.get('make')} | {a.get('model')}"] += 1
                continue
            mk, md, on_lot = c
            if on_lot is False:
                unmapped[f"{mk} | {a.get('model')}"] += 1
            y0, y1 = a["years"]
            lit, _cy, d = parse_engine(a.get("engine", ""))
            for y in range(y0, y1 + 1):
                eng = a.get("engine", "")
                if not d and lit is not None and (mk, md, y, lit) in dsl:
                    eng += " diesel"       # the other feed printed this row as diesel
                rows[(mk, md, _eng_label(eng))].append(y)
        apps = []
        for (mk, md, eng), ys in sorted(rows.items()):
            for lo, hi in _runs(ys):
                apps.append([mk, md, lo, hi, eng])
        if not apps:
            refused["no_mapped_applications"] += 1
            continue
        gid = f"am:dbe:{r['category']}:{r['aftermarket_pn']}"
        groups.append({
            "id": gid, "cat": r["category"], "tier": "likely", "src": "aftermarket",
            "label": "DB Electrical application list", "unit": r["aftermarket_pn"],
            "amps": amps(r) if r["category"] == "alternator" else None,
            "trans": unit_trans(r) if r["category"] == "starter" else None,
            "apps": apps,
            "oe": sorted({f"{o['brand']} {o['pn']}" for o in r.get("oe_numbers") or []}),
            "lester": sorted(r.get("lester") or []),
            "fits_text": r.get("fits_text") or "",
            "url": r.get("product_url", ""), "retrieved": r.get("retrieved", ""),
            "conditions": [],
        })
    _mark_splits(groups)
    for g in groups:
        g["note"] = _note(g)
    doc = {"schema": SCHEMA, "src": "aftermarket", "site": SITE, "raw": src, "tier": "likely",
           "groups": groups,
           "summary": {"records": len(records), "groups": len(groups),
                       "refused": dict(sorted(refused.items())),
                       "apps": sum(len(g["apps"]) for g in groups)},
           "unmapped_models": dict(unmapped.most_common()),
           "rows_contradicting_fits_text": len(dropped_rows),
           "rows_contradicting_fits_text_sample": sorted(dropped_rows)[:40],
           "rows_outside_fits_years": len(dropped_years),
           "rows_outside_fits_years_sample": sorted(dropped_years)[:40],
           "combined_makes": dict(combined.most_common())}
    doc["sha256"] = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    return doc


def _mark_splits(groups: list) -> None:
    """Amperage (alternator) or unit (starter) splits: the same vehicle-year
    and engine label printed on more than one unit."""
    seen = defaultdict(set)            # (cat, make, model, year, eng) -> {group index}
    for i, g in enumerate(groups):
        for mk, md, lo, hi, eng in g["apps"]:
            for y in range(lo, hi + 1):
                seen[(g["cat"], mk, md, y, eng)].add(i)
    for key, idx in seen.items():
        if len(idx) < 2:
            continue
        cat = key[0]
        if cat == "alternator":
            am = sorted({groups[i]["amps"] for i in idx}, key=lambda a: (a is None, a or 0))
            if len(am) > 1:
                tag = "amperage_split:" + "/".join("?" if a is None else f"{a}A" for a in am)
            else:
                tag = "unit_split"
        else:
            tag = "unit_split"
        for i in idx:
            c = f"{tag} {key[1]} {key[2]} {key[3]}" + (f" {key[4]}" if key[4] else "")
            groups[i]["conditions"].append(c)
    for g in groups:
        g["conditions"] = sorted(set(g["conditions"]))


def _note(g: dict) -> str:
    what = f"{g['amps']}A unit" if g.get("amps") else "unit"
    s = (f"DB Electrical {g['unit']} ({what}) lists these vehicles; aftermarket application data, "
         f"not the carmaker's catalog. Match the engine")
    if g["cat"] == "alternator":
        s += " and the amperage on the tag"
    if g.get("trans"):
        s += f"; {'automatic' if g['trans'] == 'AT' else 'manual'} transmission only"
    if any(c.startswith("amperage_split") for c in g["conditions"]):
        s += "; some of these years also came with a different amperage"
    fits = " / ".join(x.strip() for x in (g.get("fits_text") or "").splitlines() if x.strip())
    if fits:
        s += f". DB Electrical fit notes: {fits[:240]}"
    return s + "."


# ------------------------------------------------------------- membership
def members(doc: dict, cars) -> dict:
    """group id -> [(car index, condition)] where condition is "" (engine
    agrees, and transmission where the unit is AT- or MT-only),
    "engine_unconfirmed", "engine_unlisted" or "trans_unconfirmed".
    cars: iterable of (index, make, model, year, engine string[, trans])."""
    by_mk = defaultdict(list)
    for c in cars:
        ci, mk, md, yr, eng = c[:5]
        tr = car_trans(c[5]) if len(c) > 5 else None
        by_mk[(mk, squash(md))].append((ci, yr, parse_engine(eng), tr))
    out = {}
    for g in doc["groups"]:
        got = {}
        gt = g.get("trans")
        for mk, md, lo, hi, eng in g["apps"]:
            re_ = parse_engine(eng)
            for ci, yr, ce, tr in by_mk.get((mk, squash(md)), ()):
                if not (lo <= yr <= hi):
                    continue
                if gt and tr and tr != gt:
                    continue
                if not eng:
                    cond = "engine_unlisted"
                else:
                    v = engine_agrees(re_, ce)
                    if v is False:
                        continue
                    cond = "" if v else "engine_unconfirmed"
                if gt and not tr and not cond:
                    cond = "trans_unconfirmed"
                if ci not in got or (got[ci] and not cond):
                    got[ci] = cond
        if got:
            out[g["id"]] = sorted(got.items())
    return out


def report_md(doc: dict, cov: dict | None = None) -> str:
    s = doc["summary"]
    L = [f"# DB Electrical aftermarket groups ({doc['raw']})", "",
         f"- records {s['records']}, groups {s['groups']}, app rows {s['apps']}",
         f"- refused: {json.dumps(s['refused'], sort_keys=True)}",
         f"- combined-make rows skipped: {sum(doc['combined_makes'].values())}",
         f"- app rows dropped because their engine size is not in the unit's own Fits text: "
         f"{doc.get('rows_contradicting_fits_text', 0)}",
         f"- app rows dropped because their year falls outside a range the unit's Fits text gives for that "
         f"make and model: {doc.get('rows_outside_fits_years', 0)}",
         f"- app rows whose model matches no lot model: {sum(doc['unmapped_models'].values())} "
         f"({len(doc['unmapped_models'])} names; top: "
         + ", ".join(f"{k} ({v})" for k, v in list(doc['unmapped_models'].items())[:12]) + ")",
         f"- groups sha256 {doc['sha256'][:16]}"]
    if cov:
        L += ["", "Tier: Likely only (src aftermarket). Cars covered = lot cars in at least one unit "
              "group with at least one other engine-compatible lot car in the same group.", ""]
        L += ["| make | lot cars | alternator | starter | either | engine-confirmed either |",
              "|---|---:|---:|---:|---:|---:|"]
        for mk, row in cov["by_make"].items():
            L.append(f"| {mk} | {row['cars']} | {row['alternator']} | {row['starter']} | {row['either']} | "
                     f"{row['either_engine_confirmed']} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raw")
    ap.add_argument("--raw-ref", default="origin/oem-raw")
    ap.add_argument("--inventory", default=str(REPO / "docs" / "data" / "inventory_live.json"))
    ap.add_argument("--out", default=str(HERE.parent / "groups" / "_report" / "aftermarket-dbelectrical.json"))
    a = ap.parse_args(argv)
    recs, src = load_raw(a.raw, a.raw_ref)
    lot = None
    inv_p = Path(a.inventory)
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        F = {k: i for i, k in enumerate(inv["fields"])}
        lot = {(v[F["make"]] or "", v[F["model"]] or "") for v in inv["vehicles"]}
    doc = build(recs, Names(lot), src)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(report_md(doc))
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
