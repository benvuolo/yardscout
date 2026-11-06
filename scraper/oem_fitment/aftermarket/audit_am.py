#!/usr/bin/env python3
"""Agreement audit: DB Electrical unit groups vs the OEM catalogs' own part
numbers, for alternator and starter (hub follow-up 2, spec §11.4 spirit).
Offline; reads oem-raw with `git show`.

    python3 scraper/oem_fitment/aftermarket/audit_am.py [--raw-ref origin/oem-raw] [--out FILE]

Why part numbers and not curate.py groups: on the current oem-raw curate.py
emits no alternator/starter Likely group in any namespace. Likely groups are
body-only (spec §5.16), and engine kinds need closed cells (vg), which no
namespace has yet. So the OEM side here is each catalog's raw fitment rows:
key = (make, model, year, liters) on the lot, value = the OEM numbers whose
own fitment rows print that key with that engine size. Numbers linked by the
catalog's replaces / replaced-by (incl. reman -84) are one class.

For every pair of lot keys that share a DB unit (same category), where both
keys have OEM numbers in the SAME namespace:
  agree       their OEM classes intersect;
  contradict  disjoint (the catalog sells them different numbers).
And the reverse, for OEM-joined pairs (shared class), where both keys sit
in at least one DB unit: split = DB never puts them in one unit.
Rows without an engine size are not used (an option row's engine column can
list every engine of the model; spec §1 item 6).
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import groups_am as GA  # noqa: E402
import policy  # noqa: E402

CATS = ("alternator", "starter")


def _lst(v):
    if isinstance(v, list):
        return v
    if not v or v == "None":
        return []
    try:
        x = ast.literal_eval(v) if isinstance(v, str) else v
    except (ValueError, SyntaxError):
        return [v]
    return x if isinstance(x, list) else [x]


class UF:
    def __init__(self):
        self.p = {}

    def f(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def _norm_pn(pn: str) -> str:
    return GA.squash(pn)


def oem_index(raw_ref: str, names: GA.Names, lot_keys: set) -> tuple[dict, dict]:
    """(ns, cat) -> {(make, sq model, year, liters): {class}} and per-class
    example pns."""
    files = subprocess.run(["git", "-C", str(GA.REPO), "ls-tree", "--name-only", f"{raw_ref}", "raw/"],
                           check=True, capture_output=True, text=True).stdout.split()
    idx = defaultdict(lambda: defaultdict(set))
    uf = {}
    rows = []
    for f in files:
        site = f.split("/")[-1][: -len(".jsonl")] if f.endswith(".jsonl") else None
        if not site or site not in policy.SITE_NS:
            continue
        ns = policy.SITE_NS[site]
        text = subprocess.run(["git", "-C", str(GA.REPO), "show", f"{raw_ref}:{f}"], check=True,
                              capture_output=True, text=True).stdout
        for line in text.splitlines():
            r = json.loads(line)
            cat = r.get("category")
            if cat not in CATS:
                continue
            pn = _norm_pn(r.get("pn"))
            if not pn:
                continue
            u = uf.setdefault((ns, cat), UF())
            u.f(pn)
            for o in _lst(r.get("replaces")) + _lst(r.get("replaced_by")) + _lst(r.get("list_replaced_by")):
                if o and str(o) != "None":
                    u.u(pn, _norm_pn(o))
            for fr in _lst(r.get("fitment")):
                if not isinstance(fr, dict):
                    continue
                lits = {GA.parse_engine(e)[0] for e in fr.get("engines") or []} - {None}
                if len(lits) != 1:
                    continue           # no engine, or an option row listing several
                c = names.canon(fr.get("make", ""), fr.get("model", ""))
                if not c:
                    continue
                y0, y1 = fr.get("years") or [0, -1]
                lit = lits.pop()
                for y in range(int(y0), int(y1) + 1):
                    k = (c[0], GA.squash(c[1]), y, round(lit, 1))
                    if k in lot_keys:
                        rows.append(((ns, cat), k, pn, r.get("pn"), site))
    examples = defaultdict(set)
    for nc, k, pn, raw_pn, site in rows:
        cl = uf[nc].f(pn)
        idx[nc][k].add(cl)
        examples[(nc, cl)].add(raw_pn)
    return idx, examples


def db_index(doc: dict, lot_keys: set) -> dict:
    """cat -> {lot key: {unit}} (engine-known rows only)."""
    out = {c: defaultdict(set) for c in CATS}
    for g in doc["groups"]:
        for mk, md, lo, hi, eng in g["apps"]:
            lit = GA.parse_engine(eng)[0]
            if lit is None:
                continue
            for y in range(lo, hi + 1):
                k = (mk, GA.squash(md), y, round(lit, 1))
                if k in lot_keys:
                    out[g["cat"]][k].add(g["id"])
    return out


def audit(doc, oem, examples, dbi, lot_n: Counter) -> dict:
    res = {}
    for (ns, cat), om in sorted(oem.items()):
        db = dbi[cat]
        keys = sorted(k for k in om if k in db)
        units = defaultdict(list)
        for k in keys:
            for u in db[k]:
                units[u].append(k)
        agree = contra = 0
        w_agree = w_contra = 0
        sl_agree = sl_contra = 0          # same engine size pairs only
        bad_units = Counter()
        bad_ex = {}
        seen = set()
        for u, ks in units.items():
            for a, b in combinations(sorted(ks), 2):
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                w = lot_n[a] * lot_n[b]
                same = a[3] == b[3]
                if om[a] & om[b]:
                    agree += 1
                    w_agree += w
                    sl_agree += same
                else:
                    contra += 1
                    w_contra += w
                    sl_contra += same
                    bad_units[u] += 1
                    if u not in bad_ex:
                        bad_ex[u] = [list(a), sorted(p for c in om[a] for p in examples[((ns, cat), c)])[:3],
                                     list(b), sorted(p for c in om[b] for p in examples[((ns, cat), c)])[:3]]
        # reverse: OEM-joined pairs that DB splits
        by_cl = defaultdict(list)
        for k in keys:
            for c in om[k]:
                by_cl[c].append(k)
        joined = split = 0
        split_ex = []
        seen2 = set()
        for c, ks in by_cl.items():
            for a, b in combinations(sorted(set(ks)), 2):
                if (a, b) in seen2:
                    continue
                seen2.add((a, b))
                joined += 1
                if not (db[a] & db[b]):
                    split += 1
                    if len(split_ex) < 5:
                        split_ex.append([list(a), sorted(db[a])[:3], list(b), sorted(db[b])[:3],
                                         sorted(examples[((ns, cat), c)])[:2]])
        n = agree + contra
        res[f"{ns}/{cat}"] = {
            "keys_both_sources": len(keys),
            "db_pairs_checked": n, "agree": agree, "contradict": contra,
            "contradict_rate": round(contra / n, 4) if n else None,
            "same_liters_pairs": sl_agree + sl_contra, "same_liters_contradict": sl_contra,
            "same_liters_contradict_rate": round(sl_contra / (sl_agree + sl_contra), 4) if (sl_agree + sl_contra) else None,
            "lot_weighted_contradict_rate": round(w_contra / (w_agree + w_contra), 4) if (w_agree + w_contra) else None,
            "oem_pairs_checked": joined, "db_splits": split,
            "db_split_rate": round(split / joined, 4) if joined else None,
            "worst_units": [[u, n_, bad_ex[u]] for u, n_ in bad_units.most_common(5)],
            "split_examples": split_ex,
        }
    return res


def lot_keys_from(inv_p: Path, ex_p: Path | None = None) -> set:
    import twins  # noqa: E402
    ex_p = ex_p or GA.REPO / "docs" / "data" / "vehicle_extras.json"
    keys = set()
    for _i, mk, md, yr, eng, _tr in twins.load_cars(inv_p, ex_p):
        lit = GA.parse_engine(eng)[0]
        if lit is not None:
            keys.add((mk, GA.squash(md), yr, round(lit, 1)))
    return keys


ELIGIBLE_MAX = 0.05
ELIGIBLE_MIN_PAIRS = 30
GAP_MAKES = ("MINI", "Land Rover", "Jaguar", "Suzuki", "Isuzu", "Fiat", "Porsche", "Smart", "Saab", "Plymouth", "Geo")


def compare(a) -> int:
    """Eligibility is judged on the rule-1 residual: after the OEM override
    the residual on measurable pairs is 0 by construction (the same OEM
    numbers removed them), so it says nothing about pairs without OEM
    numbers. The rule-1 rate on measurable pairs is the estimate for those."""
    import twins  # noqa: E402
    cars = twins.load_cars(Path(a.inventory), Path(a.extras))
    lot_n = Counter()
    for _i, mk, md, yr, eng, _tr in cars:
        lit = GA.parse_engine(eng)[0]
        if lit is not None:
            lot_n[(mk, GA.squash(md), yr, round(lit, 1))] += 1
    lot_keys = set(lot_n)
    names = GA.Names({(c[1], c[2]) for c in cars})
    gp = Path(a.groups)
    after = json.loads(gp.read_text())
    unit = json.loads(gp.with_name(gp.stem + ".unit.json").read_text())
    rule1 = GA.refine(unit, None, twins.TWINS)
    oem, ex = oem_index(a.raw_ref, names, lot_keys)
    views = {"before": unit, "rule1": rule1, "after": after}
    res = {v: audit(d, oem, ex, db_index(d, lot_keys), lot_n) for v, d in views.items()}
    cov = {}
    for v, d in views.items():
        mem = GA.members(d, cars)
        cat_of = {g["id"]: g["cat"] for g in d["groups"]}
        hit = defaultdict(set)
        for gid, ms in mem.items():
            if len(ms) >= 2:
                for ci, _c in ms:
                    hit[cat_of[gid]].add(ci)
        by = {}
        for mk in GAP_MAKES:
            n = sum(1 for c in cars if c[1] == mk)
            al = {ci for ci in hit["alternator"] if cars[ci][1] == mk}
            st = {ci for ci in hit["starter"] if cars[ci][1] == mk}
            by[mk] = {"cars": n, "alternator": len(al), "starter": len(st), "either": len(al | st)}
        by["all makes"] = {"cars": len(cars), "alternator": len(hit["alternator"]), "starter": len(hit["starter"]),
                           "either": len(hit["alternator"] | hit["starter"])}
        cov[v] = by
    elig = {}
    for k in sorted(res["rule1"]):
        r1 = res["rule1"][k]
        n, rate = r1["db_pairs_checked"], r1["contradict_rate"]
        elig[k] = {"eligible": bool(n >= ELIGIBLE_MIN_PAIRS and rate is not None and rate <= ELIGIBLE_MAX),
                   "rule1_pairs": n, "rule1_rate": rate,
                   "before_pairs": res["before"].get(k, {}).get("db_pairs_checked"),
                   "before_rate": res["before"].get(k, {}).get("contradict_rate"),
                   "after_pairs": res["after"].get(k, {}).get("db_pairs_checked"),
                   "after_rate": res["after"].get(k, {}).get("contradict_rate")}
    sha = subprocess.run(["git", "-C", str(GA.REPO), "rev-parse", a.raw_ref], check=True, capture_output=True,
                         text=True).stdout.strip()
    out = {"raw": f"{a.raw_ref}@{sha[:8]}", "rule": GA.refine.__doc__.split("\n\n")[0],
           "eligibility": f"rule-1 residual <= {ELIGIBLE_MAX} on >= {ELIGIBLE_MIN_PAIRS} measurable pairs",
           "eligibility_by_ns_cat": elig, "coverage": cov,
           "worst_rule1": {k: v["worst_units"][:3] for k, v in res["rule1"].items() if v["contradict"]},
           "refined_stats": after.get("refined")}
    op = Path(a.out).with_name("aftermarket-audit-refined.json")
    op.write_text(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print("| ns/cat | before pairs | before rate | rule-1 pairs | rule-1 rate | after pairs | after rate | eligible |")
    print("|---|---:|---:|---:|---:|---:|---:|---|")
    for k, e in elig.items():
        print(f"| {k} | {e['before_pairs']} | {e['before_rate']} | {e['rule1_pairs']} | {e['rule1_rate']} | "
              f"{e['after_pairs']} | {e['after_rate']} | {'yes' if e['eligible'] else 'no'} |")
    print("\n| make | lot cars | before either | rule 1 either | after either | status |\n|---|---:|---:|---:|---:|---|")
    for mk in list(GAP_MAKES) + ["all makes"]:
        st = "unaudited (no OEM catalog)" if mk in GAP_MAKES else ""
        print(f"| {mk} | {cov['after'][mk]['cars']} | {cov['before'][mk]['either']} | {cov['rule1'][mk]['either']} | "
              f"{cov['after'][mk]['either']} | {st} |")
    print(f"wrote {op}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raw-ref", default="origin/oem-raw")
    ap.add_argument("--groups", default=str(HERE.parent / "groups" / "_report" / "aftermarket-dbelectrical.json"))
    ap.add_argument("--inventory", default=str(GA.REPO / "docs" / "data" / "inventory_live.json"))
    ap.add_argument("--extras", default=str(GA.REPO / "docs" / "data" / "vehicle_extras.json"))
    ap.add_argument("--out", default=str(HERE.parent / "groups" / "_report" / "aftermarket-audit.json"))
    ap.add_argument("--compare", action="store_true",
                    help="before (unit-wide, <groups stem>.unit.json) vs rule 1 only vs rule 1 + OEM override (--groups)")
    a = ap.parse_args(argv)
    if a.compare:
        return compare(a)
    sys.path.insert(0, str(HERE))
    import twins  # noqa: E402
    cars = twins.load_cars(Path(a.inventory), Path(a.extras))
    lot_n = Counter()
    for _i, mk, md, yr, eng, _tr in cars:
        lit = GA.parse_engine(eng)[0]
        if lit is not None:
            lot_n[(mk, GA.squash(md), yr, round(lit, 1))] += 1
    lot_keys = set(lot_n)
    names = GA.Names({(c[1], c[2]) for c in cars})
    doc = json.loads(Path(a.groups).read_text())
    oem, ex = oem_index(a.raw_ref, names, lot_keys)
    res = audit(doc, oem, ex, db_index(doc, lot_keys), lot_n)
    sha = subprocess.run(["git", "-C", str(GA.REPO), "rev-parse", a.raw_ref], check=True, capture_output=True,
                         text=True).stdout.strip()
    out = {"raw": f"{a.raw_ref}@{sha[:8]}", "groups_sha256": doc.get("sha256"), "by_ns_cat": res}
    Path(a.out).write_text(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print("| ns/cat | keys in both | DB pairs | contradict | rate | lot-weighted | same-size pairs | same-size rate "
          "| OEM pairs | DB splits | split rate |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, r in res.items():
        print(f"| {k} | {r['keys_both_sources']} | {r['db_pairs_checked']} | {r['contradict']} | "
              f"{r['contradict_rate']} | {r['lot_weighted_contradict_rate']} | {r['same_liters_pairs']} | "
              f"{r['same_liters_contradict_rate']} | {r['oem_pairs_checked']} | "
              f"{r['db_splits']} | {r['db_split_rate']} |")
    print(f"wrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
