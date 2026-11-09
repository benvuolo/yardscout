#!/usr/bin/env python3
"""Category-breadth coverage matrix (ops/interchange.md "Category breadth").

For today's lot cars (docs/data/inventory_live.json) and the data users get
today (docs/data/interchange.json + docs/data/oem/<cat>.json), per make x
Parts-tab category:

- beyond:   % of cars with at least one lot donor reached through a part-number
            group (hand platform group, OEM group, aftermarket unit group) or an
            engine-family vg, where the donor is NOT the same model in the same
            generation;
- samegen:  % of cars with no such donor but another lot car of the same model
            in the same generation (what the Parts tab offers as Likely anyway);
- none:     the rest.

Weighted by lot volume (counts are cars). Gaps are ranked by
    gap_cars (cars not "beyond") x demand,
demand = share of the yards' price lists (one per chain, docs/data/*_pricing.json)
that carry a line matching the category's priceTokens. The ops email's "Most
searched parts (7 d)" and coverage requests are recorded as given (too few to
weigh: 6 searches in 7 d on 2026-11-09; coverage requests need the admin key).

Method notes (honest limits):
- Engine kinds: engine_family_likely_pct is the share of cars whose decoded
  family reaches another model/generation on the lot (the Parts tab's
  same-engine Likely donors, no part-number evidence); it is not "beyond".
- Key level (make, model, year) with the client's app matching (measure.Fleet).
  Engine kinds use each car's decoded family (measure._family_choice); a vg
  counts when the seeker's and donor's keys sit in one vg of that family.
- VIN donor guards are not applied, so "beyond" is an upper bound of what the
  car card shows. Same-generation windows come from modelGenerations; a model
  without a window counts only its own year as same-generation.
- Candidate categories (not in the Parts tab yet) have beyond = 0 by
  definition; their samegen column is what shipping the category would offer
  on day one.

Usage: python3 scraper/oem_fitment/coverage_matrix.py [--out groups/_report/coverage_matrix.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "docs" / "data"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "aftermarket"))
import measure as M  # noqa: E402

# Candidate categories (task list, minus airbags/cats/engines/transmissions).
# priceTokens: substrings of the yards' price-list descriptions, lower-cased;
# "=x" means the whole description equals x. EXCLUDE: a line containing any of
# these is not the assembly (CURATION_SPEC §7.7 test D: clutch, hose, line,
# support, cap, fan, bottle, shroud, mech, electric steering), plus per-cat.
CANDIDATES = {
    "ac-compressor": {"label": "A/C compressor",
                      "priceTokens": ["a/c compressor", "ac compressor", "air conditioning compressor",
                                      "compressor (a/c", "compressor, a/c", "compressor a/c"]},
    "power-steering-pump": {"label": "Power steering pump",
                            "priceTokens": ["power steering pump", "p/s pump", "ps pump", "pump, power steering",
                                            "pump power steering", "steering pump"]},
    "radiator": {"label": "Radiator", "priceTokens": ["=radiator", "radiator (", "radiator -", "radiator,",
                                                      "radiator car", "radiator truck", "radiator any",
                                                      "radiator - car", "radiator w", "radiator assembly"]},
    "throttle-body": {"label": "Throttle body", "priceTokens": ["throttle body"]},
    "fuel-pump-module": {"label": "Fuel pump (in-tank module)",
                         "priceTokens": ["fuel pump", "fuel sending", "fuel sender"]},
    "abs-module": {"label": "ABS module / pump",
                   "priceTokens": ["abs pump", "abs unit", "abs module", "abs controller", "brake abs", "abs assembly",
                                   "anti-lock", "anti lock", "abs control"]},
    "blower-motor": {"label": "Blower motor", "priceTokens": ["blower motor"]},
    "maf-sensor": {"label": "MAF sensor", "priceTokens": ["air flow meter", "mass air", "maf sensor", "=maf",
                                                          "air flow sensor", "airflow"]},
    "wiper-motor": {"label": "Wiper motor", "priceTokens": ["wiper motor"]},
    "door-lock-actuator": {"label": "Door lock actuator",
                           "priceTokens": ["door lock actuator", "lock actuator", "door lock motor",
                                           "power lock actuator", "door latch"]},
    "door-handle-ext": {"label": "Exterior door handle",
                        "priceTokens": ["door handle outside", "outside door handle", "exterior door handle",
                                        "door handle exterior", "door handle ext", "ext door handle",
                                        "handle, outside", "outer door handle"]},
    "steering-column": {"label": "Steering column", "priceTokens": ["steering column"]},
    "cv-axle": {"label": "CV axle", "priceTokens": ["c-v axle", "cv axle", "c/v axle", "axle shaft cv",
                                                    "half shaft", "halfshaft", "drive axle"]},
    "knuckle": {"label": "Knuckle / spindle", "priceTokens": ["knuckle", "spindle"]},
    "strut": {"label": "Strut assembly", "priceTokens": ["strut and spring", "strut assembly", "=strut",
                                                         "strut w/", "strut (", "strut/spring", "strut assy",
                                                         "strut - ", "strut,", "loaded strut", "struts"]},
    "rear-seat": {"label": "Rear seat", "priceTokens": ["rear seat", "seat rear", "seat (rear", "back seat",
                                                        "bench seat rear", "seat, rear"]},
    "center-console": {"label": "Center console", "priceTokens": ["console (any", "=console", "center console",
                                                                  "console assembly", "console complete",
                                                                  "floor console", "console w"]},
}
EXCLUDE = ["clutch", "hose", "line", "support", "cap", "fan", "bottle", "shroud", "mech", "electric steering",
           "core", "mount", "bracket", "lid", "cover", "switch", "sensor only", "cable", "resistor", "relay",
           "arm", "blade", "transmission", "linkage", "boot", "bearing", "seal", "gasket", "filter",
           "reservoir", "pulley", "belt", "coupler", "shaft solid", "4x4 front axle", "front axle assy",
           "rear axle", "axle housing", "carrier", "cushion", "headrest", "head rest",
           "track", "inside", "clutc", "resist", "headlamp", "rear a/c", "interior", "int ", "crank", "jack"]
CAND_EXCL = {
    "abs-module": ["sensor", "ring", "wire"],
    "knuckle": ["hub only", "bearing"],
    "door-lock-actuator": ["trunk", "tailgate", "hood", "fuel door", "liftgate"],
    "door-handle-ext": ["inside", "interior", "tailgate", "liftgate", "trunk"],
    "radiator": ["bottle", "support", "cap", "hose", "fan", "overflow", "core support", "shroud"],
}


def price_match(desc: str, tokens, extra_excl=()) -> bool:
    d = desc.lower().strip()
    hit = any((d == t[1:]) if t.startswith("=") else (t in d) for t in tokens)
    if not hit:
        return False
    return not any(x in d for x in list(EXCLUDE) + list(extra_excl))


def chain_price_lists() -> dict:
    """{chain: {description lower: price}} one list per pricing file (chains
    publish one list; dict files carry one per yard, merged)."""
    out = {}
    for f in sorted(glob.glob(str(DATA / "*_pricing.json"))):
        ch = Path(f).name[:-len("_pricing.json")]
        d = json.loads(Path(f).read_text())
        L = {}

        def add(desc, p):
            try:
                L.setdefault(str(desc).lower().strip(), float(p))
            except (TypeError, ValueError):
                pass
        rows = d if isinstance(d, list) else [
            r for v in d.values() for r in (
                [{"description": k, "price": (x or {}).get("price") if isinstance(x, dict) else x}
                 for k, x in v.items()] if isinstance(v, dict) else (v if isinstance(v, list) else []))]
        for r in rows:
            if isinstance(r, dict):
                add(r.get("description", ""), r.get("price"))
        out[ch] = L
    return out


def demand(chains: dict, tokens, extra_excl=(), use_excl=True) -> dict:
    hits, prices, lines = 0, [], Counter()
    for ch, L in chains.items():
        got = [(k, p) for k, p in L.items()
               if (price_match(k, tokens, extra_excl) if use_excl else
                   any((k == t[1:]) if t.startswith("=") else (t in k) for t in tokens))]
        if got:
            hits += 1
            prices.append(min(p for _, p in got))
            for k, _ in got:
                lines[k] += 1
    prices.sort()
    return {"chains": hits, "of": len(chains), "share": round(hits / max(1, len(chains)), 3),
            "median_low_price": prices[len(prices) // 2] if prices else None,
            "top_lines": [k for k, _ in lines.most_common(6)]}


def load_today():
    inv = json.loads((DATA / "inventory_live.json").read_text())
    ex_p = DATA / "vehicle_extras.json"
    extras = json.loads(ex_p.read_text()) if ex_p.exists() else None
    payload = json.loads((DATA / "interchange.json").read_text())
    lazy = {}
    for p in sorted((DATA / "oem").glob("*.json")):
        d = json.loads(p.read_text())
        lazy[d.get("cat") or p.stem] = d
    return inv, extras, payload, lazy


def run(out_path: Path) -> dict:
    inv, extras, payload, lazy = load_today()
    fleet = M.Fleet(inv, extras)
    gm = M._gen_map(payload)
    win = {k: M.gen_window(gm, k[0], k[1], k[2]) for k in fleet.keys}
    sq = {k: M.squash_model(k[1], k[0]) for k in fleet.keys}

    def same_gen(a, b) -> bool:
        if a[0] != b[0] or sq[a] != sq[b]:
            return False
        w = win[a]
        return (w[0] <= b[2] <= w[1]) if w else a[2] == b[2]

    # same-generation donors: another car of the same model in the window
    by_model = defaultdict(list)
    for k in fleet.keys:
        by_model[(k[0], sq[k])].append(k)
    samegen_key = {}
    for k in fleet.keys:
        n = sum(fleet.n[k2] for k2 in by_model[(k[0], sq[k])] if same_gen(k, k2)) - 1
        samegen_key[k] = n > 0

    cats = {c["id"]: c for c in payload.get("categories") or []}
    cars_by_make = Counter(c[3] for c in fleet.cars)
    result = {}

    def beyond_from_groups(apps_list) -> dict:
        """key -> sources for group apps lists [(src, apps)]."""
        hit = defaultdict(set)
        for src, apps in apps_list:
            ks = fleet.keys_matching(apps)
            if len(ks) < 2:
                continue
            for k in ks:
                if any(not same_gen(k, k2) for k2 in ks if k2 != k):
                    hit[k].add(src)
        return hit

    for cid, c in cats.items():
        kind = c.get("kind")
        lz = lazy.get(cid) or {}
        car_beyond = {}                      # ci -> sorted sources
        fam_beyond = set()                   # engine kinds: same engine family, other model/gen (Likely)
        if kind == "engine":
            choice, _unk = M._family_choice(fleet, payload, cid)
            fams = {f["id"]: f for f in payload.get("engineFamilies") or []}
            vg_hits = {}
            for fid, f in fams.items():
                part = (f.get("parts") or {}).get(cid)
                if not part:
                    continue
                lists = [("hand_vg", g) for g in part.get("vg") or []]
                lists += [("oem_vg", g) for g in (((payload.get("oemVg") or {}).get(fid) or {}).get(cid) or [])]
                vg_hits[fid] = beyond_from_groups(lists)
            fam_keys = {fid: fleet.keys_matching(f["apps"]) for fid, f in fams.items() if fid in vg_hits}
            for ci, fid in choice.items():
                k = (fleet.cars[ci][3], fleet.cars[ci][4], fleet.cars[ci][2])
                if any(not same_gen(k, k2) for k2 in fam_keys.get(fid, ()) if k2 != k):
                    fam_beyond.add(ci)
                s = vg_hits.get(fid, {}).get(k)
                if s:
                    car_beyond[ci] = set(s)
            am = lz.get("amGroups") or []
            if am:
                import groups_am as GA  # noqa: E402
                cars = [(ci, x[3], x[4], x[2], x[7], fleet.trans[ci]) for ci, x in enumerate(fleet.cars)]
                mem = GA.members({"groups": am}, cars)
                for gid, ms in mem.items():
                    ks = {ci: (fleet.cars[ci][3], fleet.cars[ci][4], fleet.cars[ci][2]) for ci, _ in ms}
                    for ci, _cond in ms:
                        if any(not same_gen(ks[ci], ks[cj]) for cj in ks if cj != ci):
                            car_beyond.setdefault(ci, set()).add("aftermarket")
        elif kind == "body":
            lists = [("hand_group", g["apps"]) for g in payload.get("platformGroups") or [] if g["cat"] == cid]
            lists += [("oem_group", g["apps"]) for g in payload.get("oemGroups") or [] if g["cat"] == cid]
            lists += [("oem_group", g["apps"]) for g in lz.get("oemGroups") or []]
            lists += [("aftermarket", [a[:4] for a in g["apps"]]) for g in lz.get("amGroups") or []]
            kh = beyond_from_groups(lists)
            for k, s in kh.items():
                for ci in fleet.by_key[k]:
                    car_beyond[ci] = set(s)
        result[cid] = (c, car_beyond, fam_beyond)

    # aggregate
    makes = [m for m, _ in cars_by_make.most_common()]
    rows, matrix = [], {}
    chains = chain_price_lists()
    for cid, (c, cb, fb) in list(result.items()) + [(k, (dict(v, id=k, kind="candidate"), {}, set()))
                                                for k, v in CANDIDATES.items() if k not in result]:
        excl = CAND_EXCL.get(cid, ())
        dm = demand(chains, c.get("priceTokens") or [], excl, use_excl=(c.get("kind") == "candidate"))
        per = {}
        tot = Counter()
        src = Counter()
        for ci, car in enumerate(fleet.cars):
            mk = car[3]
            k = (car[3], car[4], car[2])
            st = "beyond" if ci in cb else ("samegen" if samegen_key.get(k) else "none")
            per.setdefault(mk, Counter())[st] += 1
            tot[st] += 1
            for s in cb.get(ci, ()):
                src[s] += 1
        n = len(fleet.cars)
        gap = n - tot["beyond"]
        entry = {"label": c.get("label"), "kind": c.get("kind"), "cars": n,
                 "beyond": tot["beyond"], "samegen_only": tot["samegen"], "none": tot["none"],
                 "beyond_pct": round(100 * tot["beyond"] / n, 2),
                 "samegen_only_pct": round(100 * tot["samegen"] / n, 2),
                 "beyond_sources": dict(src), "demand": dm,
                 "engine_family_likely_pct": round(100 * len(fb) / n, 2) if c.get("kind") == "engine" else None,
                 "gap_cars": gap, "gap_score": round(gap * dm["share"]),
                 "by_make": {m: {"cars": cars_by_make[m],
                                 "beyond_pct": round(100 * per[m]["beyond"] / cars_by_make[m], 1),
                                 "samegen_only_pct": round(100 * per[m]["samegen"] / cars_by_make[m], 1)}
                             for m in makes if m in per}}
        matrix[cid] = entry
        rows.append(cid)
    rows.sort(key=lambda r: -matrix[r]["gap_score"])
    doc = {"schema": 1, "built_from": {
        "inventory_scraped_at": inv.get("scrapedAt") or inv.get("scraped_at"),
        "interchange_builtAt": payload.get("builtAt"),
        "lazy_cats": sorted(lazy)},
        "cars": len(fleet.cars), "makes": {m: cars_by_make[m] for m in makes},
        "demand_inputs": {
            "price_lists": f"{len(chains)} chain price lists in docs/data/*_pricing.json",
            "ops_email_most_searched_7d_2026-11-09": {"hood": 3, "gauge-cluster": 2, "alternator": 1},
            "coverage_requests": "not read: GET /v1/admin/coverage needs the admin secret; no digest email found"},
        "method": __doc__.split("Usage:")[0].strip(),
        "gap_rank": rows, "categories": matrix}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1, sort_keys=False) + "\n")
    return doc


def table_md(doc, top_makes=8) -> str:
    makes = list(doc["makes"])[:top_makes]
    L = ["| rank | category | kind | beyond % | same-gen only % | demand (chains) | gap score | "
         + " | ".join(f"{m} b/s" for m in makes) + " |",
         "|" + "---|" * (7 + len(makes))]
    for i, cid in enumerate(doc["gap_rank"], 1):
        e = doc["categories"][cid]
        cells = [f"{e['by_make'].get(m, {}).get('beyond_pct', 0):.0f}/{e['by_make'].get(m, {}).get('samegen_only_pct', 0):.0f}"
                 for m in makes]
        L.append(f"| {i} | {cid} | {e['kind']} | {e['beyond_pct']:.1f} | {e['samegen_only_pct']:.1f} | "
                 f"{e['demand']['chains']}/{e['demand']['of']} | {e['gap_score']:,} | " + " | ".join(cells) + " |")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "groups" / "_report" / "coverage_matrix.json"))
    ap.add_argument("--md", action="store_true", help="print the markdown table")
    a = ap.parse_args(argv)
    doc = run(Path(a.out))
    print(table_md(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
