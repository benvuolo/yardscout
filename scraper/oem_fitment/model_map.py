"""Model map: catalog (ns, make, model) -> feed targets (CURATION_SPEC.md §6).

model_map.json is hand-curated; every entry carries a basis. This module
loads it, answers lookups, validates it against the live inventory
(M1-M10) and writes proposals for humans to review (`curate.py
--propose-map`). curate.py refuses to run while any error stands.

A target: {"make", "model", "trims": "*" | [patterns], "years"?: [lo, hi],
"merge"?: true, "ambig"?: "<why>"}. Trim patterns are case-folded catalog
trim names; a trailing "*" matches any continuation ("hybrid*" matches
"hybrid le"). There are never "*" model prefixes.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL_MAP_PATH = HERE / "model_map.json"
INVENTORY_PATH = HERE.parents[1] / "docs" / "data" / "inventory_live.json"


@dataclass(frozen=True)
class Target:
    ns: str
    cat_make: str
    cat_model: str
    make: str
    model: str
    trims: object          # "*" or tuple of patterns
    years: tuple | None
    merge: bool
    ambig: str

    def covers_year(self, y: int) -> bool:
        return self.years is None or self.years[0] <= y <= self.years[1]

    def trim_ok(self, atom_name: str) -> bool:
        if self.trims == "*":
            return True
        a = atom_name.lower()
        for p in self.trims:
            p = p.lower()
            if (p.endswith("*") and a.startswith(p[:-1])) or a == p:
                return True
        return False


def load(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or MODEL_MAP_PATH).read_text())


class ModelMap:
    def __init__(self, doc: dict):
        self.doc = doc
        self.by_cat: dict[tuple, list[Target]] = defaultdict(list)
        self.by_feed: dict[tuple, list[Target]] = defaultdict(list)
        for e in doc.get("entries") or []:
            for t in e.get("targets") or []:
                tr = t.get("trims", "*")
                tg = Target(e["ns"], e["cat_make"], e["cat_model"], t["make"], t["model"],
                            "*" if tr == "*" else tuple(tr), tuple(t["years"]) if t.get("years") else None,
                            bool(t.get("merge")), t.get("ambig") or "")
                self.by_cat[(e["ns"], e["cat_make"], e["cat_model"])].append(tg)
                self.by_feed[(e["ns"], t["make"], t["model"])].append(tg)
        self.exclude = dict(doc.get("exclude") or {})

    def targets(self, ns: str, cat_make: str, cat_model: str, year: int) -> list[Target]:
        return [t for t in self.by_cat.get((ns, cat_make, cat_model), []) if t.covers_year(year)]

    def sources(self, ns: str, make: str, model: str, year: int) -> list[Target]:
        """Catalog models feeding one feed target in one year."""
        return [t for t in self.by_feed.get((ns, make, model), []) if t.covers_year(year)]

    def is_mapped_catalog(self, ns, cat_make, cat_model) -> bool:
        return (ns, cat_make, cat_model) in self.by_cat

    def excluded(self, ns: str, make: str, model: str) -> str | None:
        return self.exclude.get(f"{ns}|{make}|{model}")


def load_inventory(path: str | Path | None = None) -> dict | None:
    p = Path(path or INVENTORY_PATH)
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return d


def inventory_counts(inv: dict) -> Counter:
    return Counter((r[3], r[4]) for r in inv["vehicles"])


# M6: at most this share of a target's cached vPIC decodes may name another make
M6_MAX_MAKE_MISMATCH = 0.02


def vpic_counts(inv: dict) -> dict:
    """(make, model) -> Counter(decoded, make_mismatch, gas, hybrid) over the
    published vpic block ([trim, quality, series, drive, mismatch])."""
    per_t: dict = defaultdict(Counter)
    vrows = inv["vehicles"]
    for k, v in (inv.get("vpic") or {}).items():
        try:
            r = vrows[int(k)]
        except (ValueError, IndexError):
            continue
        c = per_t[(r[3], r[4])]
        c["decoded"] += 1
        if v[4] and re.search(r"decodes as [A-Z][a-z]", v[4]) and not re.search(r"decodes as \d{4}", v[4]):
            c["make_mismatch"] += 1
        if (v[0] or "").strip().lower() == "gas":
            c["gas"] += 1
        if "hybrid" in (v[0] or "").lower() or "hybrid" in (v[2] or "").lower():
            c["hybrid"] += 1
    return per_t


def validate(mm: ModelMap, inv: dict | None, js, namespaces: dict, catalog_years: dict | None = None):
    """M1-M10. Returns (errors, warnings, report). `js` is junkyard_scraper
    (normalize_make, normalize_model, _squash_model, _app_matches).
    Without the inventory, M2/M5/M6/M9/M10 cannot run and are reported as
    skipped (rule 8)."""
    errors, warns = [], []
    report: dict = {"skipped": []}
    targets = [t for ts in mm.by_cat.values() for t in ts]
    # M1 canonical, M7 make guard
    for t in targets:
        if js.normalize_make(t.make, t.model) != t.make or js.normalize_model(t.model, t.make) != t.model:
            errors.append(f"M1 not canonical: {t.make!r} {t.model!r} (catalog {t.cat_make} {t.cat_model})")
        if t.make not in namespaces[t.ns]["makes"]:
            errors.append(f"M7 make {t.make!r} outside namespace {t.ns}")
        if "*" in t.model:
            errors.append(f"M1 '*' model prefix: {t.make} {t.model}")
        if t.years and not (1950 <= t.years[0] <= t.years[1] <= 2100):
            errors.append(f"M9 bad years {t.years} for {t.make} {t.model}")
    for e in mm.doc.get("entries") or []:
        if not (e.get("basis") or "").strip():
            errors.append(f"entry without basis: {e.get('ns')} {e.get('cat_make')} {e.get('cat_model')}")
        if e["ns"] not in namespaces or e["cat_make"] not in namespaces[e["ns"]]["makes"]:
            errors.append(f"M7 catalog make {e['cat_make']!r} outside namespace {e['ns']}")
    for k, why in mm.exclude.items():
        if not (why or "").strip():
            errors.append(f"exclude without reason: {k}")
    # M8 many-to-one without merge
    for (ns, mk, md), ts in mm.by_feed.items():
        for y in range(1950, 2031):
            src = [t for t in ts if t.covers_year(y)]
            cats = {(t.cat_make, t.cat_model) for t in src}
            if len(cats) > 1 and not all(t.merge for t in src):
                errors.append(f"M8 {mk} {md} {y}: fed by {sorted(cats)} without merge")
                break
    # M4 match self-test
    feed_targets = sorted({(t.make, t.model, t.years) for t in targets})
    for mk, md, yrs in feed_targets:
        lo, hi = yrs or (1990, 2026)
        for y in sorted({lo, hi}):
            if not js._app_matches((mk, md, lo, hi), y, mk, md):
                errors.append(f"M4 {mk} {md} {y} does not match its own app")
            for mk2, md2, yrs2 in feed_targets:
                if (mk2, md2) == (mk, md):
                    continue
                lo2, hi2 = yrs2 or (1950, 2030)
                if js._app_matches((mk2, md2, lo2, hi2), y, mk, md):
                    errors.append(f"M4 synthetic {y} {mk} {md} also matches target {mk2} {md2}")
    # M3 squash uniqueness needs the feed's model list
    if inv is None:
        report["skipped"] += ["M2", "M3", "M5", "M6", "M9", "M10 (inventory_live.json absent)"]
        return errors, warns, report
    counts = inventory_counts(inv)
    feed_models = defaultdict(set)
    for (mk, md) in counts:
        feed_models[mk].add(md)
    for t in targets:
        sq = js._squash_model(t.model, t.make)
        clash = [m for m in feed_models.get(t.make, ()) if m != t.model and js._squash_model(m, t.make) == sq]
        if clash:
            errors.append(f"M3 {t.make} {t.model} squash {sq!r} shared with {clash}")
        if counts.get((t.make, t.model), 0) == 0:
            warns.append(f"M2 no car of {t.make} {t.model} on the lots")
    # M5 no silent drops
    tset = {(t.ns, t.make, t.model) for t in targets}
    for ns, d in namespaces.items():
        cat_sq = {(e["cat_make"], js._squash_model(e["cat_model"], e["cat_make"]))
                  for e in mm.doc.get("entries") or [] if e["ns"] == ns}
        for (mk, md), n in counts.items():
            if mk not in d["makes"]:
                continue
            sq = js._squash_model(md, mk)
            hit = [c for (cmk, c) in cat_sq if c and sq.startswith(c) and cmk in d["makes"]]
            if hit and (ns, mk, md) not in tset and not mm.excluded(ns, mk, md):
                errors.append(f"M5 {ns}: feed {mk} {md} ({n} cars) squashes under mapped "
                              f"catalog {sorted(hit)} but is neither a target nor excluded")
    # M6 VIN agreement (partial: the published vpic block has no decoded
    # model, only [trim, quality, series, drive, mismatch])
    per_t = vpic_counts(inv)
    vrows = inv["vehicles"]
    m6 = {}
    for t in targets:
        c = per_t.get((t.make, t.model), Counter())
        if c["decoded"]:
            share = c["make_mismatch"] / c["decoded"]
            if share > M6_MAX_MAKE_MISMATCH:
                errors.append(f"M6 {t.make} {t.model}: {share:.1%} of decodes name another make")
        if t.trims != "*" and any(p.lower().startswith("hybrid") for p in t.trims) and c["decoded"]:
            gas = c["gas"] / c["decoded"]
            if gas > 0.01:
                errors.append(f"M6 {t.make} {t.model}: {gas:.1%} of decodes are vPIC trim 'Gas'")
        m6[f"{t.make}|{t.model}"] = dict(c)
    report["M6"] = {"note": "vPIC model is not in the published inventory; checked make mismatches "
                            "and, for hybrid trim subsets, vPIC trim 'Gas'", "by_target": m6}
    # M9 year sanity, M10 coverage
    years_by = defaultdict(Counter)
    for r in vrows:
        years_by[(r[3], r[4])][r[2]] += 1
    m9 = {}
    if catalog_years:
        for t in targets:
            cy = catalog_years.get((t.ns, t.cat_make, t.cat_model))
            if not cy:
                continue
            lo, hi = t.years or (min(cy), max(cy))
            out = sum(n for y, n in years_by[(t.make, t.model)].items() if not (lo <= y <= hi) or y not in cy)
            if out:
                m9[f"{t.make}|{t.model}"] = out
    report["M9_cars_outside_catalog_years"] = m9
    m10 = {}
    for ns, d in namespaces.items():
        total = sum(n for (mk, md), n in counts.items() if mk in d["makes"])
        mapped = sum(n for (mk, md), n in counts.items() if mk in d["makes"] and (ns, mk, md) in tset)
        m10[ns] = {"cars": total, "mapped_cars": mapped,
                   "mapped_share": round(mapped / total, 4) if total else 0.0}
    report["M10"] = m10
    return errors, warns, report


_SERIES_RX = re.compile(r"\b(1500|2500|3500|hd|xl|esv|ext|ld|heavy duty|super duty)\b", re.I)
_HYBRID_RX = re.compile(r"\bhybrid\b", re.I)


def draft_identity(ns: str, catalog_models: Counter, inv: dict | None, js, mm: ModelMap, namespaces: dict,
                   raw_label: str) -> dict:
    """A deterministic identity draft for catalog models with no entry yet
    (§6 proposals; a human merges it with `model_map.py merge`). One rule,
    the one the committed entries follow:

    - an entry only where normalize_make / normalize_model turn the printed
      catalog name into a canonical feed (make, model) that has cars on the
      lots, with trims "*" (the full catalog trim universe applies);
    - nothing where two catalog names land on one feed model (M8 needs a
      reviewed `merge`), where another feed model squashes to the same key
      (M3), or where the feed model is already some entry's target;
    - every feed model that would then fall under a mapped catalog squash
      (M5) is excluded with a reason: no claims until a reviewed entry;
    - a target whose feed name the feed also splits by series (Silverado /
      Silverado 1500 / 2500HD) gets `ambig`: Likely-only, because the
      catalog prints one model with the series only in its option column.

    Returns {"entries": [...], "exclude": {...}, "skipped": [...]}. It
    never edits an existing entry or exclusion."""
    if inv is None:
        return {"entries": [], "exclude": {}, "skipped": [{"why": "inventory_live.json absent"}]}
    makes = set(namespaces[ns]["makes"])
    counts = inventory_counts(inv)
    inv_date = str(inv.get("scrapedAt") or "")[:10]
    feed_by_make: dict = defaultdict(dict)
    for (mk, md), n in counts.items():
        feed_by_make[mk][md] = n
    existing_targets = {(t.ns, t.make, t.model) for ts in mm.by_cat.values() for t in ts}
    vp = vpic_counts(inv)
    skipped, by_target = [], defaultdict(list)
    for (cmk, cmd), nrows in sorted(catalog_models.items()):
        if cmk not in makes or mm.is_mapped_catalog(ns, cmk, cmd) or mm.excluded(ns, cmk, cmd):
            continue
        mk = js.normalize_make(cmk, cmd)
        md = js.normalize_model(cmd, mk)
        base = {"cat_make": cmk, "cat_model": cmd, "feed": [mk, md]}
        if mk not in makes:
            skipped.append({**base, "why": "normalized make outside the namespace"})
            continue
        n = counts.get((mk, md), 0)
        if n == 0:
            skipped.append({**base, "why": "no feed car under the canonical name"})
            continue
        if js.normalize_make(mk, md) != mk or js.normalize_model(md, mk) != md:
            skipped.append({**base, "why": "canonical name does not normalize to itself (M1)"})
            continue
        sq = js._squash_model(md, mk)
        clash = sorted(m for m in feed_by_make[mk] if m != md and js._squash_model(m, mk) == sq)
        if clash:
            skipped.append({**base, "why": f"feed models {clash} share the squash key {sq!r} (M3)"})
            continue
        if (ns, mk, md) in existing_targets:
            skipped.append({**base, "why": "feed model already fed by another catalog model (merge needs review)"})
            continue
        vc = vp.get((mk, md)) or Counter()
        if vc["decoded"] and vc["make_mismatch"] / vc["decoded"] > M6_MAX_MAKE_MISMATCH:
            skipped.append({**base, "why": f"{vc['make_mismatch']}/{vc['decoded']} vPIC decodes name another "
                                           f"make (M6 over {M6_MAX_MAKE_MISMATCH:.0%})"})
            continue
        by_target[(mk, md)].append((cmk, cmd, nrows, n))
    entries = []
    for (mk, md), lst in sorted(by_target.items()):
        if len(lst) > 1:
            for cmk, cmd, _r, _n in lst:
                skipped.append({"cat_make": cmk, "cat_model": cmd, "feed": [mk, md],
                                "why": f"{len(lst)} catalog models land on one feed model (M8 needs a reviewed merge)"})
            continue
        cmk, cmd, nrows, n = lst[0]
        entries.append({"ns": ns, "cat_make": cmk, "cat_model": cmd,
                        "targets": [{"make": mk, "model": md, "trims": "*"}],
                        "basis": f"catalog prints '{cmd}' ({nrows} fitment rows, {raw_label}); normalize_model "
                                 f"canon '{md}', {n} feed cars (inventory {inv_date}); identity draft"})
    # M5: every feed model of the namespace makes under a mapped catalog
    # squash (any make of the namespace, as validate() checks) is a target
    # or excluded
    all_entries = [e for e in mm.doc.get("entries") or [] if e["ns"] == ns] + entries
    cat_sq = sorted({js._squash_model(e["cat_model"], e["cat_make"]) for e in all_entries} - {""})
    tset = existing_targets | {(ns, t["make"], t["model"]) for e in entries for t in e["targets"]}
    exclude, series_of = {}, defaultdict(list)
    for (mk, md), n in sorted(counts.items()):
        if mk not in makes or (ns, mk, md) in tset or mm.excluded(ns, mk, md):
            continue
        sq = js._squash_model(md, mk)
        hit = [c for c in cat_sq if sq.startswith(c)]
        if not hit:
            continue
        under = max(hit, key=len)
        if _HYBRID_RX.search(md):
            why = (f"hybrid sub-model; how this catalog files hybrids is not reviewed yet ({n} cars, under "
                   f"catalog squash '{under}'); unmapped until a reviewed entry exists")
        else:
            why = (f"feed spelling or sub-model the catalog does not print as its own model ({n} cars, under "
                   f"catalog squash '{under}'); unmapped until a reviewed entry exists")
        exclude[f"{ns}|{mk}|{md}"] = why
        if _SERIES_RX.search(md):
            series_of[(mk, under)].append(md)
    for e in entries:
        t = e["targets"][0]
        sub = sorted(series_of.get((t["make"], js._squash_model(t["model"], t["make"])), []))
        if sub:
            t["ambig"] = (f"feed splits '{t['model']}' by series ({', '.join(sub[:4])}); the catalog prints one "
                          f"model with the series only in its option column")
            e["basis"] += "; ambig (Likely only): the feed name is coarser than the series the catalog splits"
    return {"entries": entries, "exclude": exclude, "skipped": skipped}


def merge_draft(doc: dict, drafts: list[dict]) -> tuple[dict, list]:
    """Add drafted entries and exclusions to a model-map document. Existing
    entries and exclusions are never changed. Returns (doc, added keys)."""
    out = json.loads(json.dumps(doc))
    have = {(e["ns"], e["cat_make"], e["cat_model"]) for e in out["entries"]}
    added = []
    for d in drafts:
        for e in d.get("entries") or []:
            k = (e["ns"], e["cat_make"], e["cat_model"])
            if k not in have:
                out["entries"].append(e)
                have.add(k)
                added.append("|".join(k))
        for k, why in sorted((d.get("exclude") or {}).items()):
            if k not in out["exclude"]:
                out["exclude"][k] = why
                added.append("exclude " + k)
    out["entries"].sort(key=lambda e: (e["ns"], e["cat_make"], e["cat_model"]))
    return out, added


def dump(doc: dict) -> str:
    """model_map.json's own layout (indent 1, sorted keys, no ASCII escapes)."""
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False)


def main(argv=None) -> int:
    """python3 scraper/oem_fitment/model_map.py merge <map-proposals.json>...
    Merges the identity drafts that `curate.py --propose-map` wrote, then
    runs M1-M10; the file is written only when no error stands."""
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=main.__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["merge", "check"])
    ap.add_argument("proposals", nargs="*")
    ap.add_argument("--map", default=str(MODEL_MAP_PATH))
    ap.add_argument("--inventory", default=str(INVENTORY_PATH))
    a = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    import junkyard_scraper as js  # noqa: E402
    import policy  # noqa: E402
    doc = load(a.map)
    added = []
    if a.cmd == "merge":
        drafts = [json.loads(Path(p).read_text()).get("draft") or {} for p in a.proposals]
        doc, added = merge_draft(doc, drafts)
    errs, warns, _rep = validate(ModelMap(doc), load_inventory(a.inventory), js, policy.NAMESPACES)
    for e in errs:
        print("ERROR", e, file=sys.stderr)
    print(f"{len(added)} additions, {len(errs)} errors, {len(warns)} warnings", file=sys.stderr)
    if errs:
        return 2
    if a.cmd == "merge":
        Path(a.map).write_text(dump(doc))
    return 0


def propose(ns: str, catalog_models: Counter, inv: dict | None, js, mm: ModelMap) -> list[dict]:
    """Proposals for catalog models that have no entry: normalize_make /
    normalize_model plus same-squash-prefix feed neighbours. Humans decide."""
    counts = inventory_counts(inv) if inv else Counter()
    feed_by_make = defaultdict(list)
    for (mk, md), n in counts.items():
        feed_by_make[mk].append((md, n))
    out = []
    for (cmk, cmd), nrows in sorted(catalog_models.items()):
        if mm.is_mapped_catalog(ns, cmk, cmd) or mm.excluded(ns, cmk, cmd):
            continue
        mk = js.normalize_make(cmk, cmd)
        md = js.normalize_model(cmd, mk)
        sq = js._squash_model(md, mk)
        neighbours = sorted([(m, n) for m, n in feed_by_make.get(mk, []) if js._squash_model(m, mk).startswith(sq)
                             and m != md], key=lambda x: -x[1])
        out.append({"ns": ns, "cat_make": cmk, "cat_model": cmd, "fitment_rows": nrows,
                    "proposed": {"make": mk, "model": md, "trims": "*"},
                    "feed_cars": counts.get((mk, md), 0), "squash_neighbours": neighbours[:10]})
    return out


if __name__ == "__main__":
    raise SystemExit(main())
