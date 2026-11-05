#!/usr/bin/env python3
"""Offline, deterministic curation: raw OEM evidence -> groups/<ns>.json plus
groups/_report/<ns>.{json,md,completion.json} (CURATION_SPEC.md §4-§6, §10).

    python3 scraper/oem_fitment/curate.py --ns all --raw-ref origin/oem-raw
    python3 scraper/oem_fitment/curate.py --ns toyota --raw-dir <fixtures> --fixtures --write-groups

Verified (§2, Phase 1): two feed vehicle-years share a group only when both
are closed (every list page of the category read, every matched product
read and verified, every chain member read), every slot's candidate set is
one supersession chain whose every member the carmaker lists for every trim
and engine of that car with clean own-page notes, the signatures are equal,
and the (site, category) passed its audit. Every ambiguity removes claims.
No rule adds a pair by inference.

By default only reports are written. `--write-groups` also writes
groups/<ns>.json, which the payload builder ships (new keys only): the first
merge per namespace waits for the owner's review of _report/<ns>.md (§11.5).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import adapters as A  # noqa: E402
import model_map as MM  # noqa: E402
import notes as N  # noqa: E402
import policy  # noqa: E402
import positions as P  # noqa: E402

GROUPS_DIR = HERE / "groups"
REPORT_DIR = GROUPS_DIR / "_report"

# funnel stages (§10.3), in order
STAGES = ["unmapped", "no_records", "not_closed", "split", "conditional", "chain_member_conditional",
          "reman_only", "blocked", "gated", "eligible", "grouped"]
# cover reasons a closing crawl removes (own-page notes and listing from R1,
# the year-page trim list from R2); assumed clean ONLY in the optimistic
# ranking of the completion worklist (§10.4), never for any claim
OPTIMISTIC_WHY = {"notes_not_own_page", "fitted_not_listed", "trims_unattested"}
CLOSURE_REASONS = ["no_year_manifest", "year_manifest_bad", "variant_unread", "no_list_manifest",
                   "list_manifest_bad", "unread_sibling_page", "unverified_product", "suspect_variant",
                   "uncrawled_chain_member", "chain_fitment_inconsistent", "stale", "unattested",
                   "ambig_target", "site_blocked", "listed_not_fitted_only"]


def _canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha1(o) -> str:
    return hashlib.sha1(_canon(o).encode()).hexdigest()


def policy_sha256(model_map_path: Path | None = None) -> str:
    h = hashlib.sha256()
    for p in (HERE / "policy.py", HERE / "notes.py", HERE / "positions.py",
              Path(model_map_path or MM.MODEL_MAP_PATH)):
        h.update(p.read_bytes())
    return h.hexdigest()


def _ts(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


@dataclass
class Options:
    as_of: str | None = None
    fixtures: bool = False
    model_map: MM.ModelMap | None = None
    model_map_path: Path | None = None
    inventory: dict | None = None
    status_table: dict | None = None        # CATEGORY_STATUS override (tests)
    engine_reliable: dict | None = None     # ENGINE_CELLS_RELIABLE override (tests)
    sibling_ignore: dict | None = None
    js: object = None                       # junkyard_scraper module
    trimu_force: dict = field(default_factory=dict)   # {(make, model, year): [trims]} test hook (case 2)
    strict: bool = False                    # raise on lint errors (tests)


class LintError(Exception):
    pass


@dataclass
class Klass:
    key: str
    cat: str
    pns: set
    records: list
    reman: bool = False
    disputed: bool = False
    chain_unknown: bool = False
    packaging: str = ""
    problems: set = field(default_factory=set)

    @property
    def verified(self) -> bool:
        return not self.problems and not self.disputed and all(not r.problems for r in self.records)


# =========================================================================
class Curation:
    def __init__(self, ns: str, src: A.RawSource, opts: Options):
        self.ns, self.src, self.o = ns, src, opts
        self.js = opts.js
        self.mm = opts.model_map
        self.nsd = policy.NAMESPACES[ns]
        self.status_table = policy.CATEGORY_STATUS if opts.status_table is None else opts.status_table
        self.reliable = policy.ENGINE_CELLS_RELIABLE if opts.engine_reliable is None else opts.engine_reliable
        self.sibling_ignore = policy.SIBLING_IGNORE if opts.sibling_ignore is None else opts.sibling_ignore
        self.refusals: list = []
        self.input_issues: list = []
        self.raw_meta: dict = {}
        self.records: list[A.Record] = []
        self.list_rows: list[A.ListRow] = []
        self.years: list[A.YearManifest] = []
        self.blocked: set = set()
        self.unknown_clauses: Counter = Counter()
        self.lint: list = []
        inv = opts.inventory
        self.inv_counts = Counter((r[3], r[4], r[2]) for r in inv["vehicles"]) if inv else Counter()
        kinds = getattr(self.js, "INTERCHANGE_PART_CATEGORIES", {}) if self.js else {}
        self.kinds = {k: v.get("kind") for k, v in kinds.items()}

    def refuse(self, reason, t=None, cat=None, pn=None, evidence=None, detail=None):
        self.refusals.append({"reason": reason, "t": list(t) if t else None, "cat": cat, "pn": pn,
                              "evidence": sorted(evidence or []), **({"detail": detail} if detail else {})})

    # ------------------------------------------------------------ 5.1 input
    def load(self):
        for site in self.nsd["sites"]:
            meta = {"records": 0, "lists": 0, "years": 0, "done": self.src.has(site, ".done"),
                    "blocked": self.src.has(site, ".blocked")}
            if meta["blocked"]:
                self.blocked.add(site)
            present = False
            for kind, suf in A.KINDS.items():
                text = self.src.read(f"raw/{site}{suf}")
                meta[f"{kind}_sha256"] = A.sha256(text) if text is not None else None
                if text is None:
                    continue
                present = True
                p = A.parse_jsonl(text, self.o.fixtures)
                for reason, line, detail in p.issues:
                    self.input_issues.append({"site": site, "file": kind, "reason": reason, "line": line,
                                              "detail": detail})
                if p.refused:
                    self.input_issues.append({"site": site, "file": kind, "reason": "corrupt_raw",
                                              "detail": p.refused})
                    self.refuse("corrupt_raw", evidence=[f"{site}:{kind}"], detail=p.refused)
                    continue
                for line, o in p.objs:
                    if kind == "records":
                        self.records.append(A.to_record(site, self.ns, line, o))
                        meta["records"] += 1
                    elif kind == "lists":
                        self.list_rows += A.to_list_rows(site, line, o)
                        meta["lists"] += 1
                    else:
                        self.years.append(A.to_year_manifest(site, line, o))
                        meta["years"] += 1
            if present:
                self.raw_meta[site] = meta
        self.records.sort(key=lambda r: (r.site, r.line))
        self.list_rows.sort(key=lambda r: (r.site, r.line, r.pn))
        self.years.sort(key=lambda y: (y.site, y.line))
        # --as-of defaults to the newest retrieved in the input (no wall clock)
        stamps = [r.retrieved for r in self.records] + [x.retrieved for x in self.list_rows] + \
                 [y.retrieved for y in self.years]
        stamps = [s for s in stamps if _ts(s)]
        self.as_of = self.o.as_of or (max(stamps) if stamps else "1970-01-01T00:00:00Z")
        self.as_of_dt = _ts(self.as_of)

    def stale(self, retrieved: str) -> bool:
        t = _ts(retrieved)
        return t is None or (self.as_of_dt - t) > timedelta(days=policy.EVIDENCE_MAX_AGE_DAYS)

    # ------------------------------------------- 5.1 dups, 5.3 verification
    def verify(self):
        kept = []
        for r in self.records:
            why = policy.EXCLUDE_AT_CURATION.get((r.site, r.cat, r.pn))
            if why:
                self.refuse("exclude_at_curation", cat=r.cat, pn=r.pn, evidence=[r.pointer], detail=why)
                continue
            if self.js and r.cat in ("side-mirrors",) and any(
                    policy.TOW_RE.search(x or "") for x in [r.name, r.aux] + r.note_texts):
                r.cat = "tow-mirrors"     # §5.3 projection
            kept.append(r)
        # duplicates of (site, cat, pn)
        groups = defaultdict(list)
        for r in kept:
            groups[(r.site, r.cat, r.pn)].append(r)
        self.records = []
        self.disputed_keys = set()
        for (site, cat, pn), rs in sorted(groups.items()):
            if len(rs) == 1:
                self.records.append(rs[0])
                continue
            uniq = {}
            for r in rs:
                uniq.setdefault(_canon(r.raw), r)
            rs = sorted(uniq.values(), key=lambda r: r.line)
            if len(rs) == 1:
                self.records.append(rs[0])
                continue
            superseded = {int(r.recrawl_of) for r in rs if r.recrawl_of and str(r.recrawl_of).isdigit()}
            live = [r for r in rs if r.line not in superseded]
            if len(live) == 1 and superseded:
                self.records.append(live[0])
                self.refuse("recrawl_resolved", cat=cat, pn=pn, evidence=[r.pointer for r in rs])
                continue
            for r in rs:
                r.problems.append("disputed_duplicate")
                self.records.append(r)
            self.refuse("disputed_duplicate", cat=cat, pn=pn, evidence=[r.pointer for r in rs])
        # per-record checks
        fails = Counter()
        totals = Counter()
        for r in self.records:
            totals[(r.site, r.cat)] += 1
            if r.flags:
                r.problems.append("flagged")
            ev = A.evidence_problems(r)
            if ev:
                r.problems.append("evidence_mismatch")
                fails[(r.site, r.cat)] += 1
                self.refuse("evidence_mismatch", cat=r.cat, pn=r.pn, evidence=[r.pointer], detail=",".join(ev))
            m = A.rule_matches(r) if r.cat != "tow-mirrors" else True
            if m is False:
                r.problems.append("rule_drift")
                self.refuse("rule_drift", cat=r.cat, pn=r.pn, evidence=[r.pointer])
            elif m is None:
                r.problems.append("rule_unchecked")
            names = [r.name, r.aux]
            if any(policy.KIT_RE.search(x or "") for x in names):
                r.problems.append("kit_set_pair")
            if any(policy.RHD_RE.search(x or "") for x in [f.raw for f in r.rows] + r.note_texts + names):
                r.problems.append("rhd")
            if any(policy.RULE4_RE.search(x or "") for x in names):
                self.lint.append(f"rule4: {r.pointer} {r.pn} {r.name!r}")
                r.problems.append("rule4")
            if self.stale(r.retrieved):
                r.problems.append("stale")
        if self.lint and self.o.strict:
            raise LintError("; ".join(self.lint))
        self.systemic = set()
        for k, n in totals.items():
            if n and fails[k] / n > policy.SYSTEMIC_FAIL_RATE:
                self.systemic.add(k)
                self.refuse("systemic_evidence_failure", cat=k[1], detail=f"{k[0]}: {fails[k]}/{n}")

    # ------------------------------------------------------- 5.4 classes
    def build_classes(self):
        self.classes: dict[tuple, Klass] = {}
        for r in self.records:
            k = (r.key, r.cat)
            c = self.classes.get(k)
            if c is None:
                c = self.classes[k] = Klass(r.key, r.cat, set(), [])
            c.pns.add(r.pn)
            c.records.append(r)
        by_key = defaultdict(list)
        for (key, cat), c in self.classes.items():
            by_key[key].append(c)
            sigs = {frozenset((f.lo, f.hi, f.make, f.model, f.layout, tuple(sorted(f.trims)),
                               tuple(sorted(f.engines))) for f in r.rows) for r in c.records}
            if len(sigs) > 1:
                c.disputed = True
                self.refuse("disputed_class", cat=cat, pn=sorted(c.pns)[0],
                            evidence=[r.pointer for r in c.records], detail="records disagree on fitment")
            if any("disputed_duplicate" in r.problems for r in c.records):
                c.disputed = True
            c.chain_unknown = any(r.chain_unknown for r in c.records)
            c.reman = any(r.reman_flag for r in c.records) or any(
                policy.REMAN_NAME_RE.search(x or "") for r in c.records for x in [r.name, r.aux] + r.note_texts) \
                or any(policy.is_reman_pn(self.ns, pn) for pn in c.pns)
            names = [n for r in c.records for n in r.oem_names]
            c.packaging = P.packaging(cat, self.ns, sorted(c.pns)[0], names)
        for key, cs in by_key.items():
            if len(cs) > 1:
                for c in cs:
                    c.disputed = True
                self.refuse("cross_category_pn", pn=key, detail=",".join(sorted(c.cat for c in cs)))

    # ------------------------------------------------- 5.5 / 6 mapping
    def build_mapping(self):
        """cv -> targets; T -> rows; universes."""
        mk_ok = set(self.nsd["makes"])
        self.unmapped = Counter()
        self.cat_models = Counter()
        self.ns_models = set()
        self.t_rows = defaultdict(list)      # (T, cat) -> [(klass, record, row)]
        self.t_sources = defaultdict(set)    # T -> {(cat_make, cat_model)}
        self.catalog_years = defaultdict(set)
        self.class_feed_models = defaultdict(set)
        self.class_Ts = defaultdict(set)
        for (key, cat), c in sorted(self.classes.items()):
            for r in c.records:
                for f in r.rows:
                    self.ns_models.add(f.model.lower())
                    if f.make not in mk_ok:
                        continue      # evidence only (§4)
                    self.cat_models[(f.make, f.model)] += 1
                    for y in range(f.lo, f.hi + 1):
                        self.catalog_years[(self.ns, f.make, f.model)].add(y)
                        tgts = self.mm.targets(self.ns, f.make, f.model, y)
                        if not tgts:
                            self.unmapped[(f.make, f.model)] += 1
                            continue
                        for t in tgts:
                            if not _row_maps(f, t):
                                continue
                            T = (t.make, t.model, y)
                            self.t_rows[(T, cat)].append((c, r, f, t))
                            self.t_sources[T].add((t.cat_make, t.cat_model))
                            self.class_feed_models[(key, cat)].add((t.make, t.model))
                            self.class_Ts[(key, cat)].add(T)
        for k, ms in self.class_feed_models.items():
            if len(ms) > policy.UNIVERSAL_CAP:
                self.classes[k].problems.add("universal_part_suspect")
                self.refuse("universal_part_suspect", cat=k[1], pn=sorted(self.classes[k].pns)[0],
                            detail=f"{len(ms)} feed models")
        self.ns_models_f = frozenset(self.ns_models)

    def targets_of_seed(self, seed: tuple) -> set:
        """Feed targets whose catalog page is the seed's page (same cv)."""
        mk, md, y = seed
        srcs = {(t.cat_make, t.cat_model) for t in self.mm.sources(self.ns, mk, md, y)}
        out = set()
        for cmk, cmd in srcs:
            for t in self.mm.targets(self.ns, cmk, cmd, y):
                out.add((t.make, t.model, y))
        return out

    def index_pages(self):
        """T -> own-page evidence: manifest rows (R1) when the crawler wrote
        any for T; otherwise the seed-page proxy of records whose seed is T."""
        self.t_list_rows = defaultdict(list)     # (T, cat) -> [ListRow]
        self.t_list_manifests = defaultdict(set)  # T -> {(site, cat, list_url)}
        for lr in self.list_rows:
            for T in self.targets_of_seed(lr.seed):
                self.t_list_rows[(T, lr.cat)].append(lr)
                self.t_list_manifests[T].add((lr.site, lr.cat, lr.list_url, lr.status, lr.retrieved, lr.line))
        self.t_years = defaultdict(list)
        for ym in self.years:
            for T in self.targets_of_seed(ym.seed):
                self.t_years[T].append(ym)
        self.t_seed_records = defaultdict(list)  # (T, cat) -> records seeded on T's page
        for r in self.records:
            for T in self.targets_of_seed(r.seed):
                self.t_seed_records[(T, r.cat)].append(r)

    def own_page(self, T, cat, c: Klass):
        """(on_page, notes, position sources, pointers) for class c on T."""
        rows = [lr for lr in self.t_list_rows.get((T, cat), []) if policy.pn_key(self.ns, lr.pn) == c.key]
        if self.t_list_rows.get((T, cat)):
            on = [lr for lr in rows if lr.matched]
            notes = [n for lr in on for n in lr.notes]
            src = [("location", x) for lr in on for x in lr.locations] + [("slug", lr.list_url) for lr in on]
            return bool(on), notes, src, [lr.pointer for lr in on], "manifest"
        recs = [r for r in self.t_seed_records.get((T, cat), []) if r.key == c.key]
        notes = [n for r in recs for n in r.note_texts]
        src = [("location", x) for r in recs for x in r.list_location] + [("slug", r.list_url) for r in recs]
        return bool(recs), notes, src, [r.pointer for r in recs], "seed"

    # ------------------------------------------------------ 5.7 universes
    def universes(self):
        self.trimu, self.trimu_src, self.engineu, self.trimu_by_engine = {}, {}, {}, {}
        rows_by_T = defaultdict(list)
        for (T, cat), lst in self.t_rows.items():
            for c, r, f, t in lst:
                rows_by_T[T].append((cat, c, r, f, t))
        self.rows_by_T = rows_by_T
        for T, lst in rows_by_T.items():
            good = [(cat, c, r, f, t) for cat, c, r, f, t in lst
                    if f.layout == "trim" and not r.problems and not f.trims_from_options]
            yt = [ym for ym in self.t_years.get(T, []) if ym.trims and _status_ok(ym.status)]
            if T in self.o.trimu_force:
                atoms = {a for tr in self.o.trimu_force[T] for a in A.trim_atoms(tr)}
                self.trimu[T], self.trimu_src[T] = frozenset(atoms), "forced_by_test"
            elif yt:
                atoms = {a for ym in yt for tr in ym.trims for a in A.trim_atoms(tr)}
                t0 = good[0][4] if good else None
                if t0 is not None:
                    atoms = {a for a in atoms if t0.trim_ok(a[0])}
                self.trimu[T], self.trimu_src[T] = frozenset(atoms), "year_page"
            else:
                recs = {(r.site, r.line) for _, _, r, _, _ in good}
                cats = {cat for cat, *_ in good}
                atoms = set()
                for cat, c, r, f, t in good:
                    atoms |= {a for a in f.trim_atoms() if t.trim_ok(a[0])}
                if len(recs) >= policy.TRIMU_MIN_RECORDS and len(cats) >= policy.TRIMU_MIN_CATS and atoms:
                    self.trimu[T], self.trimu_src[T] = frozenset(atoms), "fitment"
                else:
                    self.trimu[T], self.trimu_src[T] = frozenset(atoms), "unattested"
            eng = set()
            for cat, c, r, f, t in good:
                if self.reliable.get(r.site):
                    eng |= f.engine_keys()
            self.engineu[T] = frozenset(eng)

    # --------------------------------------------------- 5.9 supersession
    def build_graph(self):
        self.edges = defaultdict(set)      # (cat) -> {(old, new)}
        known = defaultdict(set)
        for (key, cat) in self.classes:
            known[key].add(cat)
        for (key, cat), c in sorted(self.classes.items()):
            for r in c.records:
                for x in r.replaces:
                    self._edge(cat, policy.pn_key(self.ns, x), key, known, r)
                for y in r.replaced_by + r.list_replaced_by:
                    self._edge(cat, key, policy.pn_key(self.ns, y), known, r)
        for lr in self.list_rows:
            if lr.replace and lr.cat:
                self._edge(lr.cat, policy.pn_key(self.ns, lr.pn), policy.pn_key(self.ns, lr.replace), known, None)
        self.succ = {cat: defaultdict(set) for cat in self.edges}
        self.pred = {cat: defaultdict(set) for cat in self.edges}
        for cat, es in self.edges.items():
            for a, b in es:
                self.succ[cat][a].add(b)
                self.pred[cat][b].add(a)
        # cycles: SCCs with more than one node
        self.cyclic = set()
        for cat in self.edges:
            for comp in _sccs(self.succ[cat]):
                if len(comp) > 1:
                    self.cyclic |= {(k, cat) for k in comp}

    def _edge(self, cat, a, b, known, r):
        if a == b:
            return
        for end in (a, b):
            if end in known and cat not in known[end]:
                self.refuse("cross_category_supersession", cat=cat, pn=end,
                            evidence=[r.pointer] if r else None)
                return
        self.edges[cat].add((a, b))

    def reach(self, cat, a, depth=None, down=True) -> set:
        nxt = (self.succ if down else self.pred).get(cat, {})
        seen, frontier, d = set(), {a}, 0
        while frontier and (depth is None or d < depth):
            frontier = {y for x in frontier for y in nxt.get(x, ())} - seen - {a}
            seen |= frontier
            d += 1
        return seen

    def comparable(self, cat, a, b) -> bool:
        return a == b or b in self.reach(cat, a) or a in self.reach(cat, b)

    # --------------------------------------------- 5.10 cover / candidates
    def cover(self, T, cat, c: Klass, engine_set=None, trim_u=None):
        """('yes'|'maybe'|'no', [reasons], own-page info)."""
        rows = [(r, f, t) for cc, r, f, t in self.t_rows.get((T, cat), []) if cc is c]
        on, notes, possrc, ptrs, how = self.own_page(T, cat, c)
        if not rows and not on:
            return "no", ["not_listed"], (on, notes, possrc, ptrs, how)
        why = []
        if not c.verified:
            why.append("unverified")
        if not rows:
            why.append("listed_not_fitted")
        if rows and not on:
            why.append("fitted_not_listed" if how == "manifest" else "notes_not_own_page")
        tu = self.trimu.get(T, frozenset()) if trim_u is None else trim_u
        if self.trimu_src.get(T) == "unattested" and T not in self.o.trimu_force:
            why.append("trims_unattested")
        eu = self.engineu.get(T, frozenset()) if engine_set is None else engine_set
        best = None
        for r, f, t in rows:
            if f.layout != "trim" or f.trims_from_options:
                continue
            if not f.trims:
                best = best or "trims_unknown"
                continue
            if not tu <= f.trim_atoms():
                best = best if best in ("ok",) else "conditional_trims"
                continue
            if not self.reliable.get(r.site):
                best = best if best == "ok" else "conditional_engines"
                continue
            if not eu or not eu <= f.engine_keys():
                best = best if best == "ok" else "conditional_engines"
                continue
            best = "ok"
        if rows and best is None:
            why.append("option_layout")
        elif best and best != "ok":
            why.append(best)
        ctx = N.NoteContext(T[2], frozenset(m.lower() for _, m in self.t_sources.get(T, set())), self.ns_models_f)
        v = N.classify(notes, ctx)
        for u in v.unknown:
            self.unknown_clauses[u] += 1
        if not v.clean:
            for cl in sorted(v.classes):
                why.append(f"conditional_notes:{cl.lower()}")
        qual = []
        for r in c.records:
            for x in (r.name, r.aux, r.other_names):
                qual += N.qualifier_phrases(x, policy.CONTENT_TOKENS.get(cat, ()), cat)
        if qual:
            why.append("qualifier_phrase")
        if c.disputed:
            why.append("disputed")
        if any("rule_drift" in r.problems for r in c.records):
            why.append("rule_drift")
        return ("yes" if not why else "maybe"), why, (on, notes, possrc, ptrs, how)

    def slot_of(self, T, cat, c: Klass, possrc) -> P.Resolution:
        src = []
        for r in c.records:
            src += [("position", r.position), ("name", r.name), ("name", r.aux)]
        src += possrc
        ctx = N.NoteContext(T[2], frozenset(), frozenset())
        res = P.resolve(cat, [s for s in src if s[1]])
        if cat == "window-switch":
            name = " | ".join(n for r in c.records for n in r.oem_names)
            slot, why = P.window_switch_slot(name, "", res.side, res.door)
            if why == "out_of_category":
                return P.Resolution((), "out_of_category", res.side, res.door)
            return P.Resolution(("DM",), why or res.reason, res.side, res.door)
        if cat == "climate-control":
            return P.Resolution(("CSW",) if c.packaging == "switch-module" else ("C",), res.reason)
        del ctx
        return res

    def cell(self, T, cat, engine_set=None, trim_u=None):
        """Everything known about (T, cat): slots -> members, reasons."""
        cands = {}
        for c, r, f, t in self.t_rows.get((T, cat), []):
            cands[(c.key, c.cat)] = c
        for lr in self.t_list_rows.get((T, cat), []):
            if lr.matched:
                k = (policy.pn_key(self.ns, lr.pn), cat)
                if k in self.classes:
                    cands[k] = self.classes[k]
        for r in self.t_seed_records.get((T, cat), []):
            cands[(r.key, r.cat)] = self.classes[(r.key, r.cat)]
        members = {}
        for k, c in sorted(cands.items()):
            cov, why, page = self.cover(T, cat, c, engine_set, trim_u)
            if cov == "no":
                continue
            res = self.slot_of(T, cat, c, page[2])
            if res.reason == "out_of_category":
                continue
            members[c.key] = {"klass": c, "cover": cov, "why": why, "slot": res, "page": page}
        return members

    # ------------------------------------------------------ 5.10 closure
    def closure(self, T, cat, members) -> list:
        reasons = []
        sources = self.t_sources.get(T, set())
        years = self.t_years.get(T, [])
        t_entries = [t for (cmk, cmd) in sources for t in self.mm.targets(self.ns, cmk, cmd, T[2])
                     if (t.make, t.model) == (T[0], T[1])]
        if any(t.ambig for t in t_entries):
            reasons.append("ambig_target")
        for cmk, cmd in sorted(sources):
            ok = [ym for ym in years if _status_ok(ym.status) and _title_names(ym.title, cmd, T[2])]
            if not years:
                reasons.append("no_year_manifest")
                break
            if not ok:
                reasons.append("year_manifest_bad")
                continue
            if any(ym.final_url and ym.final_url.split("?")[0] != ym.year_url.split("?")[0] for ym in ok):
                reasons.append("year_manifest_bad")
            for ym in ok:
                if ym.site not in policy.SIMPLEPART_SITES:
                    read = {y.variant for y in years if y.site == ym.site}
                    if set(ym.variants or []) - read:
                        reasons.append("variant_unread")
        if not years:
            if "no_year_manifest" not in reasons:
                reasons.append("no_year_manifest")
        lists = [lr for lr in self.t_list_rows.get((T, cat), [])]
        manifests = {(lr.site, lr.list_url): lr for lr in lists}
        if not lists:
            reasons.append("no_list_manifest")
        else:
            if any(not _status_ok(lr.status) for lr in manifests.values()):
                reasons.append("list_manifest_bad")
            # C2: every CAT_PAGES sub on the year page has a list manifest; no
            # unread sibling sub matching NOUN[cat]
            for ym in years:
                pages = A.site_cat_pages(ym.site).get(cat)
                read_subs = {lr.list_url.rstrip("/").split("/parts-list/", 1)[-1].split("/", 1)[-1]
                             .replace(".html", "") for lr in lists if lr.site == ym.site}
                for sub in ym.subs:
                    tail = sub.split("/")[-1]
                    hit = pages.search(sub) or pages.search(tail) if pages else False
                    if hit and sub not in read_subs and tail not in {s.split("/")[-1] for s in read_subs}:
                        reasons.append("no_list_manifest")
                    elif not hit and re.search(policy.NOUN.get(cat, r"$^"), sub, re.I) \
                            and sub not in (self.sibling_ignore.get(ym.site, {}).get(cat, {})):
                        reasons.append("unread_sibling_page")
            # C3 every matched row has a verified product record
            for lr in lists:
                if lr.matched:
                    k = (policy.pn_key(self.ns, lr.pn), cat)
                    c = self.classes.get(k)
                    if c is None or not c.verified:
                        reasons.append("unverified_product")
                # C4 suspect variant
                elif self._suspect(lr, cat):
                    reasons.append("suspect_variant")
            # C6 manifests fresh
            if any(self.stale(lr.retrieved) for lr in lists) or any(self.stale(y.retrieved) for y in years):
                reasons.append("stale")
        # C5 chain completeness
        for key, m in members.items():
            for d in self.reach(cat, key, policy.CHAIN_DEPTH) | self.reach(cat, key, policy.CHAIN_DEPTH, down=False):
                dc = self.classes.get((d, cat))
                if dc is None or not dc.verified:
                    reasons.append("uncrawled_chain_member")
            for d in self.reach(cat, key, policy.CHAIN_DEPTH):
                dc = self.classes.get((d, cat))
                if dc is not None and not any(cc is dc for cc, *_ in self.t_rows.get((T, cat), [])):
                    reasons.append("chain_fitment_inconsistent")
        # C6 records fresh
        if any(self.stale(r.retrieved) for m in members.values() for r in m["klass"].records):
            reasons.append("stale")
        # C7 universe attested
        if self.trimu_src.get(T, "unattested") == "unattested" and T not in self.o.trimu_force:
            reasons.append("unattested")
        # C9 blocked sites never close
        if any(r.site in self.blocked for m in members.values() for r in m["klass"].records) or \
                any(lr.site in self.blocked for lr in lists):
            reasons.append("site_blocked")
        return _uniq(reasons)

    def _suspect(self, lr: A.ListRow, cat: str) -> bool:
        if lr.excluded_by in (None, "", "include_miss", "url_pn_mismatch"):
            return False
        if lr.excluded_by == "reman_dropped":
            return cat in policy.ENGINE_CATS
        head = lambda s: re.split(r",", N.QUALIFIER_RE.sub(" ", s or ""), 1)[0].strip()  # noqa: E731
        fake = A.Record(site=lr.site, ns=self.ns, cat=cat, pn=lr.pn, key="", line=lr.line,
                        template=A.template_of(lr.site, {}), name=head(lr.main), aux=head(lr.aux),
                        other_names="", description="", list_url=lr.list_url, section=lr.section, position="",
                        list_location=[], note_texts=[], replaces=[], replaced_by=[], list_replaced_by=[],
                        chain_unknown=False, reman_flag=False, rows=[], flags=[], evidence_lines=[],
                        rendered=None, total=None, retrieved=lr.retrieved, seed=lr.seed, via=None,
                        recrawl_of=None, product_url="", raw={"list_group": "", "list_remark": "",
                                                              "list_info": []})
        m = A.rule_matches(fake)
        # a head phrase that matches the include rule but was excluded is a
        # suspect; when the rule cannot be re-run offline, fail closed
        return m is not False

    # --------------------------------------------------- 5.11 eligibility
    def eligibility(self, T, cat, members, engine_mode=False) -> tuple[list, dict]:
        """(reasons, slots {slot: [(packaging, key)]})."""
        reasons = []
        slots = defaultdict(list)
        for key, m in sorted(members.items()):
            res = m["slot"]
            if res.reason:
                reasons.append(res.reason if res.reason.startswith("position") else res.reason)
            for s in res.slots:
                slots[s].append(key)
        if not members:
            return ["no_candidates"], {}
        pol = policy.cat_policy(cat)
        present = set(slots)
        if not any(set(req) == present for req in pol["required"]):
            # a side or door the car must have is missing, or a slot shows up
            # that no allowed configuration has: either way, no claim
            if any(present <= set(req) for req in pol["required"]):
                reasons.append("slot_missing")
            else:
                reasons.append("slot_unexpected")
        # E1 one chain per slot (window-regulator: allowed packaging)
        chains = {}
        for s, keys in slots.items():
            if cat == "window-regulator":
                comp = _chain_ids(keys, lambda a, b: self.comparable(cat, a, b))
                chains.update(comp)
                why = P.regulator_slot_ok([(k, members[k]["klass"].packaging) for k in keys], comp)
                if why:
                    reasons.append(why)
            else:
                if any(not self.comparable(cat, a, b) for i, a in enumerate(keys) for b in keys[i + 1:]):
                    reasons.append("option_split")
        # chain crossing slots / packaging
        for (a, b) in self.edges.get(cat, ()):
            if a in members and b in members:
                ma, mb = members[a], members[b]
                if set(ma["slot"].slots) != set(mb["slot"].slots) or ma["klass"].packaging != mb["klass"].packaging:
                    reasons.append("chain_crosses_slot")
        # E2 cover yes for every member
        maybe = {k: m for k, m in members.items() if m["cover"] != "yes"}
        if maybe:
            heads = {k for k in members if not (self.reach(cat, k) & set(members))}
            if all(k not in heads for k in maybe) and len(members) > 1:
                reasons.append("chain_member_conditional")
            else:
                cls = set()
                for m in maybe.values():
                    for w in m["why"]:
                        if w in ("unverified", "disputed", "rule_drift"):
                            continue      # E3 (unverified_member) reports these
                        cls.add(_cond_class(w))
                for x in sorted(cls):
                    reasons.append(f"conditional:{x}")
        # E3
        for key, m in members.items():
            c = m["klass"]
            if (key, cat) in self.cyclic:
                reasons.append("cyclic")
            if not c.verified:
                reasons.append("unverified_member")
            if c.chain_unknown:
                reasons.append("chain_unknown")
            if "universal_part_suspect" in c.problems:
                reasons.append("universal_part_suspect")
        # E4 reman
        remans = [k for k, m in members.items() if m["klass"].reman]
        if remans:
            non = [k for k, m in members.items() if not m["klass"].reman]
            if not any(all(r in self.reach(cat, n) for r in remans) for n in non):
                reasons.append("reman_only")
        # E5 category status for every contributing site
        sites = {r.site for m in members.values() for r in m["klass"].records} | \
            {lr.site for lr in self.t_list_rows.get((T, cat), [])}
        if any(policy.category_status(s, cat, self.status_table) is None for s in sites):
            reasons.append("category_unconfirmed")
        if any((s, cat) in self.systemic for s in sites):
            reasons.append("category_unconfirmed")
        # E7 / E8
        kind = self.kinds.get(cat)
        if cat in policy.PHASE3_CATS or kind not in ("body", "engine"):
            reasons.append("kind_not_phase1")
        if kind == "engine" or cat in policy.ENGINE_CATS:
            if any(not self.reliable.get(s) for s in sites):
                reasons.append("engine_cells_unreliable")
        sl = {s: sorted((members[k]["klass"].packaging, k) for k in keys) for s, keys in slots.items()}
        # funnel order (§10.3): split, conditional, chain member, reman, blocked, gated
        reasons = sorted(_uniq(reasons), key=lambda r: STAGES.index(_stage_of(r)))
        return reasons, sl

    # ------------------------------------------------------------ run
    def run(self):
        self.load()
        self.verify()
        self.build_classes()
        self.build_mapping()
        self.index_pages()
        self.universes()
        self.build_graph()
        cats = sorted({c for (_, c) in self.classes} | {lr.cat for lr in self.list_rows})
        Ts = sorted({T for (T, _) in self.t_rows} | {T for (T, _) in self.t_list_rows})
        self.cells_info = {}
        for cat in cats:
            for T in Ts:
                if not self.t_rows.get((T, cat)) and not self.t_list_rows.get((T, cat)):
                    continue
                members = self.cell(T, cat)
                clos = self.closure(T, cat, members)
                elig, slots = self.eligibility(T, cat, members)
                # optimistic upper bound for ranking crawler work only: what a
                # closing crawl (R1/R2) would supply is assumed clean
                opt = {k: {**m, "why": [w for w in m["why"] if w not in OPTIMISTIC_WHY]} for k, m in members.items()}
                for m in opt.values():
                    m["cover"] = "yes" if not m["why"] else "maybe"
                elig_opt, slots_opt = self.eligibility(T, cat, opt)
                self.cells_info[(T, cat)] = {"members": members, "closure": clos, "elig": elig, "slots": slots,
                                             "elig_opt": elig_opt, "slots_opt": slots_opt}
        return self

    # ---------------------------------------------------------- outputs
    def sig_of(self, slots: dict) -> list:
        out = []
        for s in sorted(slots):
            byp = defaultdict(list)
            for pack, key in slots[s]:
                byp[pack].append(key)
            out.append([s, [[p, sorted(ks)] for p, ks in sorted(byp.items())]])
        return out

    def first_reason(self, info, hypothetical=False, optimistic=False) -> tuple[str, str]:
        """The cell's first open reason. hypothetical=True assumes closure
        (C1-C9) and the audit gate (E5) pass (§10.3); optimistic=True also
        assumes what a closing crawl supplies is clean (OPTIMISTIC_WHY), to
        rank crawler work (§10.4). Both are labelled and never shipped."""
        if info["closure"] and not (hypothetical or optimistic):
            return "not_closed", info["closure"][0]
        for r in info["elig_opt" if optimistic else "elig"]:
            if (hypothetical or optimistic) and r == "category_unconfirmed":
                continue
            st = _stage_of(r)
            return st, r
        return "eligible", ""

    def build_doc(self):
        js = self.js
        groups_by = defaultdict(list)
        sigs = {}
        cells = []
        hyp_groups = defaultdict(list)
        self.opt_groups = defaultdict(list)
        for (T, cat), info in sorted(self.cells_info.items()):
            stage, reason = self.first_reason(info)
            hstage, hreason = self.first_reason(info, hypothetical=True)
            ostage, _oreason = self.first_reason(info, optimistic=True)
            if ostage == "eligible":
                self.opt_groups[(cat, _sha1(self.sig_of(info["slots_opt"]))[:10])].append(T)
            sig = self.sig_of(info["slots"]) if info["slots"] else []
            h = _sha1(sig)[:10]
            info["stage"], info["reason"], info["hstage"], info["hreason"], info["sig"], info["sigh"] = \
                stage, reason, hstage, hreason, sig, h
            if stage == "eligible":
                sigs[h] = sig
                groups_by[(cat, h)].append(T)
                cells.append([T[0], T[1], T[2], cat, f"sig:{h}"])
            else:
                cells.append([T[0], T[1], T[2], cat, f"open:{reason}"])
            if hstage == "eligible":
                hyp_groups[(cat, h)].append(T)
        self.hyp_groups = hyp_groups
        groups, vg = [], []
        brand = self.nsd["brand"]
        for (cat, h), Ts in sorted(groups_by.items()):
            if len(Ts) < policy.MIN_GROUP_VEHICLE_YEARS:
                continue
            kind = self.kinds.get(cat)
            if kind != "body":
                continue          # engine categories go through vg (below)
            apps = _runs(Ts)
            keys = sorted({k for s in sigs[h] for _, ks in s[1] for k in ks})
            pns = sorted({pn for k in keys for pn in self.classes[(k, cat)].pns})
            note = _verified_note(brand, pns)
            years = [self._proof(T, cat) for T in sorted(Ts)]
            groups.append({"id": f"oem:{self.ns}:{cat}:{h}", "cat": cat, "tier": "verified", "kind": "body",
                           "sig": sigs[h], "apps": apps, "pn": pns, "note": note, "years": years,
                           "cars": sum(self.inv_counts.get(T, 0) for T in Ts)})
        vg = self.engine_groups(groups_by, sigs) if js else []
        likely = self.likely_groups(brand)
        used = {k for g in groups + vg for s in g["sig"] for _, ks in s[1] for k in ks}
        used |= {k for g in likely for k in g.get("keys", [])}
        classes = {}
        for (key, cat), c in sorted(self.classes.items()):
            if key in used:
                classes[key] = {"pns": sorted(c.pns), "cat": cat, "comp": c.packaging or None, "reman": c.reman,
                                "names": sorted({n for r in c.records for n in r.oem_names}),
                                "evidence": sorted(r.pointer for r in c.records)}
        for g in likely:
            g.pop("keys", None)
        doc = {
            "schema": policy.SCHEMA, "ns": self.ns, "curate_version": policy.CURATE_VERSION,
            "as_of": self.as_of, "policy_sha256": policy_sha256(self.o.model_map_path),
            "raw": {"ref": self.src.ref or "fixtures", "commit": self.src.commit or "fixtures",
                    "sites": {s: {k: v for k, v in m.items()} for s, m in sorted(self.raw_meta.items())}},
            "classes": classes, "groups": groups, "vg": vg, "likely": likely,
            "sigs": {h: sigs[h] for h in sorted(sigs)},
            "cells": sorted(cells),
        }
        return doc

    def _proof(self, T, cat):
        info = self.cells_info[(T, cat)]
        lists = sorted({lr.pointer for lr in self.t_list_rows.get((T, cat), [])})
        years = sorted({ym.pointer for ym in self.t_years.get(T, [])})
        stamps = [lr.retrieved for lr in self.t_list_rows.get((T, cat), [])] + \
                 [ym.retrieved for ym in self.t_years.get(T, [])] + \
                 [r.retrieved for m in info["members"].values() for r in m["klass"].records]
        stamps = sorted(s for s in stamps if _ts(s))
        return {"t": list(T), "cv": sorted([[cmk, cmd, T[2]] for cmk, cmd in self.t_sources.get(T, set())]),
                "closure": {"year": years[0] if years else None, "years": years, "lists": lists,
                            "oldest_retrieved": stamps[0] if stamps else None},
                "universe": {"trims_src": self.trimu_src.get(T), "trims": sorted(
                    " ".join(x for x in a if x) for a in self.trimu.get(T, ()))}}

    # ---------------------------------------------- 5.13 engine attachment
    def engine_groups(self, groups_by, sigs):
        js = self.js
        out = defaultdict(list)
        self.engine_refusals = []
        for (T, cat), info in sorted(self.cells_info.items()):
            if cat not in policy.ENGINE_CATS:
                continue
            if info["closure"]:
                continue
            fams = js.engine_families_for(T[2], T[0], T[1], cat if cat != "ignition-coils" else None)
            if not fams:
                self.engine_refusals.append({"reason": "family_gap", "t": list(T), "cat": cat})
                continue
            if len(fams) != 1:
                self.engine_refusals.append({"reason": "family_ambiguous", "t": list(T), "cat": cat})
                continue
            fid, fam, app = fams[0]
            if js._app_flags(app).get("ambig"):
                self.engine_refusals.append({"reason": "family_ambig", "t": list(T), "cat": cat})
                continue
            ef = frozenset(e for e in self.engineu.get(T, ()) if isinstance(e[0], int)
                           and e[0] == fam["engine"]["cyl"]
                           and any(abs(e[1] - L) <= 0.05 for L in fam["engine"]["liters"]))
            if not ef:
                self.engine_refusals.append({"reason": "family_gap", "t": list(T), "cat": cat})
                continue
            # (c) family uniformity: each engine key alone gives the same signature
            per = set()
            for e in sorted(ef, key=str):
                mem = self.cell(T, cat, engine_set=frozenset([e]))
                mem = {k: m for k, m in mem.items()
                       if any(e in f.engine_keys() for cc, r, f, t in self.t_rows.get((T, cat), [])
                              if cc is m["klass"] and f.layout == "trim")}
                per.add(_canon(sorted(mem)))
            if len(per) != 1:
                self.engine_refusals.append({"reason": "family_nonuniform", "t": list(T), "cat": cat})
                continue
            trim_f = self._trimu_f(T, ef)
            members = self.cell(T, cat, engine_set=ef, trim_u=trim_f)
            elig, slots = self.eligibility(T, cat, members)
            if elig:
                self.engine_refusals.append({"reason": elig[0], "t": list(T), "cat": cat})
                continue
            part = fam["parts"].get(cat) or {}
            yrs = part.get("years")
            if yrs and not (yrs[0] <= T[2] <= yrs[1]):
                self.engine_refusals.append({"reason": "part_years", "t": list(T), "cat": cat})
                continue
            sig = self.sig_of(slots)
            out[(fid, cat, _sha1(sig)[:10])].append((T, sig))
        vg = []
        for (fid, cat, h), lst in sorted(out.items()):
            Ts = [T for T, _ in lst]
            if len(Ts) < policy.MIN_GROUP_VEHICLE_YEARS:
                continue
            sig = lst[0][1]
            keys = sorted({k for s in sig for _, ks in s[1] for k in ks})
            pns = sorted({pn for k in keys for pn in self.classes[(k, cat)].pns})
            vg.append({"id": f"oem:{self.ns}:{cat}:{h}", "family": fid, "cat": cat, "tier": "verified",
                       "kind": "engine", "sig": sig, "spans": _runs(Ts), "pn": pns,
                       "note": _verified_note(self.nsd["brand"], pns),
                       "years": [self._proof(T, cat) for T in sorted(Ts)]})
        return vg

    def _trimu_f(self, T, ef):
        rows = [(f, r) for (cat, c, r, f, t) in self.rows_by_T.get(T, [])
                if f.layout == "trim" and not r.problems and f.engine_keys() and f.engine_keys() <= ef]
        recs = {(r.site, r.line) for f, r in rows}
        if len(recs) >= policy.TRIMU_MIN_RECORDS:
            return frozenset(a for f, r in rows for a in f.trim_atoms())
        return self.trimu.get(T, frozenset())

    # ------------------------------------------------------- 5.16 likely
    def likely_groups(self, brand):
        out = []
        for (key, cat), c in sorted(self.classes.items()):
            if self.kinds.get(cat) != "body" or cat in policy.PHASE3_CATS:
                continue
            if not c.verified or "universal_part_suspect" in c.problems:
                continue
            fms = self.class_feed_models.get((key, cat), set())
            if len(fms) < 2:
                continue        # single-model: the same-model generation loop covers it
            Ts = sorted(self.class_Ts.get((key, cat), ()))
            if not Ts:
                continue
            whys = set()
            slots = set()
            for T in Ts:
                info = self.cells_info.get((T, cat))
                m = (info or {}).get("members", {}).get(key)
                if m:
                    whys |= set(m["why"])
                    slots |= set(m["slot"].slots)
            reason, text = _likely_reason(whys)
            pns = sorted(c.pns)
            apps = _runs(Ts)
            slot = "+".join(sorted(slots)) or "C"
            note = _sanitize(f"{brand} catalog lists #{pns[0]} for both — {text}; verify the number on the part")
            out.append({"id": f"oem:{self.ns}:{cat}:{slot}:{_sha1([pns, apps])[:10]}", "cat": cat,
                        "tier": "likely", "kind": "body", "apps": apps, "pn": pns, "reason": reason,
                        "note": note, "keys": [key], "cars": sum(self.inv_counts.get(T, 0) for T in Ts)})
        return out

    # ------------------------------------------------------------ report
    def report(self, doc, inv_counts: Counter):
        funnel = defaultdict(lambda: defaultdict(Counter))
        hyp = defaultdict(lambda: defaultdict(Counter))
        mk_ok = set(self.nsd["makes"])
        cats = sorted({cat for (_, cat) in self.cells_info} | {c for (_, c) in self.classes})
        grouped = {(T, g["cat"]) for g in doc["groups"] for y in g["years"] for T in [tuple(y["t"])]}
        grouped |= {(tuple(y["t"]), g["cat"]) for g in doc["vg"] for y in g["years"]}
        hyp_grouped = {(T, cat) for (cat, h), Ts in self.hyp_groups.items() if len(Ts) >= 2 for T in Ts}
        for (mk, md, y), n in sorted(inv_counts.items()):
            if mk not in mk_ok:
                continue
            T = (mk, md, y)
            mapped = bool(self.mm.sources(self.ns, mk, md, y))
            for cat in cats:
                info = self.cells_info.get((T, cat))
                if not mapped:
                    st = st2 = ("unmapped", "")
                elif info is None:
                    st = st2 = ("no_records", "")
                else:
                    st = (info["stage"], info["reason"])
                    st2 = (info["hstage"], info["hreason"])
                    if st[0] == "eligible" and (T, cat) in grouped:
                        st = ("grouped", "")
                    if st2[0] == "eligible" and (T, cat) in hyp_grouped:
                        st2 = ("grouped", "")
                funnel[cat][st[0]][st[1]] += n
                hyp[cat][st2[0]][st2[1]] += n
        def fz(f):
            return {cat: {s: dict(sorted(f[cat][s].items())) for s in STAGES if f[cat].get(s)} for cat in sorted(f)}
        unmapped = []
        for (cmk, cmd), rows in sorted(self.unmapped.items()):
            mk = self.js.normalize_make(cmk, cmd) if self.js else cmk
            md = self.js.normalize_model(cmd, mk) if self.js else cmd
            cars = sum(n for (a, b, y), n in inv_counts.items() if (a, b) == (mk, md))
            unmapped.append({"cat_make": cmk, "cat_model": cmd, "row_years": rows, "feed": [mk, md],
                             "feed_cars": cars, "excluded": self.mm.excluded(self.ns, cmk, cmd)})
        near = []
        for lr in self.list_rows:
            if not lr.matched and re.search(policy.NOUN.get(lr.cat, r"$^"), f"{lr.main} {lr.aux}", re.I):
                near.append({"pn": lr.pn, "cat": lr.cat, "main": lr.main, "aux": lr.aux,
                             "excluded_by": lr.excluded_by, "evidence": lr.pointer})
        completion = self.completion(inv_counts)
        rep = {
            "ns": self.ns, "as_of": self.as_of, "raw": doc["raw"],
            "summary": {"records": len(self.records), "classes": len(self.classes),
                        "list_rows": len(self.list_rows), "year_manifests": len(self.years),
                        "cells": len(self.cells_info), "verified_groups": len(doc["groups"]),
                        "vg_groups": len(doc["vg"]), "likely_groups": len(doc["likely"]),
                        "blocked_sites": sorted(self.blocked),
                        "why_no_verified": _why_none(self)},
            "funnel_cars": fz(funnel),
            "funnel_cars_hypothetical_if_every_year_closed": {
                "label": "HYPOTHETICAL: closure (C1-C9) and the audit gate (E5) assumed, current candidate "
                         "state; ranks crawler work, never shipped",
                "by_cat": fz(hyp)},
            "open_reasons_cells": dict(sorted(Counter(i["reason"] or i["stage"] for i in self.cells_info.values()).items())),
            "refusals": sorted(self.refusals, key=_canon),
            "engine_refusals": sorted(getattr(self, "engine_refusals", []), key=_canon),
            "input_issues": self.input_issues,
            "unknown_note_clauses": dict(sorted(self.unknown_clauses.items(), key=lambda x: (-x[1], x[0]))),
            "unmapped_catalog_models": unmapped,
            "contradictions": [],
            "audit_sample": {"closures": [], "pairs": [],
                             "note": "no eligible closure or Verified pair to sample" if not doc["groups"] else ""},
            "map_proposals": MM.propose(self.ns, self.cat_models, self.o.inventory, self.js, self.mm)
            if self.js else [],
            "near_miss_rows": near,
            "lint": self.lint,
        }
        return rep, completion

    def completion(self, inv_counts: Counter):
        """§10.4: for every open cell, the Verified pairs (cars x cars) that
        would flip if it closed with its current candidate state."""
        gain = Counter()
        cats = defaultdict(set)
        for (cat, h), Ts in self.opt_groups.items():
            if len(Ts) < 2:
                continue
            cars = {T: inv_counts.get(T, 0) for T in Ts}
            tot = sum(cars.values())
            for T in Ts:
                info = self.cells_info[(T, cat)]
                if info["stage"] == "not_closed":
                    g = cars[T] * (tot - cars[T])
                    if g:
                        gain[T] += g
                        cats[T].add(cat)
        rows = [{"make": T[0], "model": T[1], "year": T[2], "cats": sorted(cats[T]), "gain_pairs": g}
                for T, g in gain.items()]
        rows.sort(key=lambda r: (-r["gain_pairs"], r["make"], r["model"], r["year"]))
        return {"ns": self.ns, "as_of": self.as_of,
                "note": "R3 input: rows ordered by Verified ordered car pairs gained if the cell closed "
                        "with its current candidate state and its own pages carried no restricting note "
                        "(optimistic upper bound for ranking crawl work; never shipped)", "rows": rows}


# ------------------------------------------------------------------ helpers
def _row_maps(f: A.FitRow, t: MM.Target) -> bool:
    """A row maps to a trim-subset target only when its trims meet the subset
    (or when the row prints no trims: then it is a candidate, never coverage)."""
    if t.trims == "*":
        return True
    if f.layout == "trim" and f.trims:
        return any(t.trim_ok(a[0]) for a in f.trim_atoms())
    return True


def _status_ok(s) -> bool:
    return s in (200, "200", "ok", "OK")


def _title_names(title: str, cat_model: str, year: int) -> bool:
    t = re.sub(r"[^a-z0-9]", "", (title or "").lower())
    return str(year) in (title or "") and re.sub(r"[^a-z0-9]", "", cat_model.lower()) in t


def _uniq(xs):
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


def _sccs(succ: dict) -> list:
    index, low, stack, on, out = {}, {}, [], set(), []
    counter = [0]
    nodes = sorted(set(succ) | {y for v in succ.values() for y in v})

    def strong(v):
        work = [(v, iter(sorted(succ.get(v, ()))))]
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        while work:
            node, it = work[-1]
            nxt = next(it, None)
            if nxt is None:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    comp = set()
                    while True:
                        w = stack.pop()
                        on.discard(w)
                        comp.add(w)
                        if w == node:
                            break
                    out.append(comp)
            elif nxt not in index:
                index[nxt] = low[nxt] = counter[0]
                counter[0] += 1
                stack.append(nxt)
                on.add(nxt)
                work.append((nxt, iter(sorted(succ.get(nxt, ())))))
            elif nxt in on:
                low[node] = min(low[node], index[nxt])
    for v in nodes:
        if v not in index:
            strong(v)
    return out


def _chain_ids(keys, comparable) -> dict:
    """Connected components of 'comparable' among keys (ids by smallest key)."""
    keys = sorted(set(keys))
    parent = {k: k for k in keys}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if comparable(a, b):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    return {k: find(k) for k in keys}


def _cond_class(why: str) -> str:
    if why.startswith("conditional_notes:"):
        return why.split(":", 1)[1]
    return {"conditional_trims": "trim", "conditional_engines": "engine", "option_layout": "option_layout",
            "trims_unknown": "trim", "trims_unattested": "trim_unattested", "notes_not_own_page": "notes_not_own_page",
            "fitted_not_listed": "fitted_not_listed", "listed_not_fitted": "listed_not_fitted",
            "qualifier_phrase": "qualifier", "unverified": "unverified", "disputed": "disputed",
            "rule_drift": "rule_drift"}.get(why, why)


def _stage_of(reason: str) -> str:
    if reason in ("option_split",) or reason.startswith("packaging") or reason.startswith("position") \
            or reason in ("slot_missing", "slot_unexpected", "chain_crosses_slot", "no_candidates"):
        return "split"
    if reason.startswith("conditional"):
        return "conditional"
    if reason == "chain_member_conditional":
        return "chain_member_conditional"
    if reason == "reman_only":
        return "reman_only"
    if reason in ("category_unconfirmed", "engine_cells_unreliable", "kind_not_phase1"):
        return "gated"
    return "blocked"


def _runs(Ts) -> list:
    """Per feed (make, model): maximal runs of consecutive years (§5.15)."""
    by = defaultdict(list)
    for mk, md, y in Ts:
        by[(mk, md)].append(y)
    out = []
    for (mk, md), ys in sorted(by.items()):
        ys = sorted(set(ys))
        lo = prev = ys[0]
        for y in ys[1:]:
            if y != prev + 1:
                out.append([mk, md, lo, prev])
                lo = y
            prev = y
        out.append([mk, md, lo, prev])
    return out


def _sanitize(s: str) -> str:
    s = s.replace("&", "and").replace('"', "").replace("<", "").replace(">", "")
    s = "".join(ch for ch in s if policy.NOTE_CHARSET.match(ch))
    return s[: policy.NOTE_MAX_LEN]


def _verified_note(brand: str, pns: list) -> str:
    shown = ", ".join(pns[:2]) + (f", +{len(pns) - 2} more" if len(pns) > 2 else "")
    return _sanitize(f"{brand} catalog: same numbers on every trim and engine for these years ({shown})")


def _likely_reason(whys: set) -> tuple[str, str]:
    if "conditional_notes:plant" in whys:
        return "plant", "plant-specific (US / Japan built)"
    if "conditional_trims" in whys or "conditional_notes:trim" in whys:
        return "trim", "trim-limited"
    if any(w.startswith("conditional_notes:option") for w in whys):
        return "option", "option: fits some option packages"
    if whys == {"option_layout"} or ("option_layout" in whys and len(whys) <= 2):
        return "older", "older catalog-only number"
    return "conditional", "fits some configurations"


def _why_none(cur: Curation) -> str:
    if not cur.list_rows and not cur.years:
        return ("no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close "
                "(C1/C2); Verified is impossible by design until the crawler writes them")
    return "see funnel_cars"


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def report_md(rep: dict) -> str:
    s = rep["summary"]
    lines = [f"# OEM curation report: {rep['ns']}", "",
             f"Raw: `{rep['raw']['ref']}` @ `{rep['raw']['commit'][:12]}`; as of {rep['as_of']}.", "",
             f"- records {s['records']}, classes {s['classes']}, list rows {s['list_rows']}, "
             f"year manifests {s['year_manifests']}, cells {s['cells']}",
             f"- Verified groups {s['verified_groups']}, engine vg groups {s['vg_groups']}, "
             f"Likely groups {s['likely_groups']}",
             f"- blocked sites: {', '.join(s['blocked_sites']) or 'none'}",
             f"- why no Verified: {s['why_no_verified']}", "",
             "## Funnel (lot cars per category, first open reason)", "",
             "| category | stage | reason | cars |", "|---|---|---|---|"]
    for cat, st in rep["funnel_cars"].items():
        for stage, rs in st.items():
            for reason, n in rs.items():
                lines.append(f"| {cat} | {stage} | {reason or '-'} | {n} |")
    lines += ["", "## Hypothetical funnel (closure assumed; never shipped)", "",
              "| category | stage | reason | cars |", "|---|---|---|---|"]
    for cat, st in rep["funnel_cars_hypothetical_if_every_year_closed"]["by_cat"].items():
        for stage, rs in st.items():
            for reason, n in rs.items():
                lines.append(f"| {cat} | {stage} | {reason or '-'} | {n} |")
    lines += ["", "## Refusals by reason", ""]
    for r, n in sorted(Counter(x["reason"] for x in rep["refusals"]).items()):
        lines.append(f"- {r}: {n}")
    lines += ["", "## Unknown note clauses (top 30)", ""]
    for c, n in list(rep["unknown_note_clauses"].items())[:30]:
        lines.append(f"- `{c}`: {n}")
    lines += ["", "## Unmapped catalog models", ""]
    for u in rep["unmapped_catalog_models"][:60]:
        lines.append(f"- {u['cat_make']} {u['cat_model']}: feed {u['feed'][1]!r} {u['feed_cars']} cars"
                     + (f" (excluded: {u['excluded']})" if u["excluded"] else ""))
    return "\n".join(lines) + "\n"


def cross_ns_collisions(results: dict) -> list:
    """§5.4 / test 13: the same pn string in two namespaces never merges; it
    is reported."""
    by = defaultdict(set)
    for ns, cur in results.items():
        for (key, cat) in cur.classes:
            by[key.split(":", 1)[1]].add(ns)
    return sorted([[k, sorted(v)] for k, v in by.items() if len(v) > 1])


def curate(ns: str, src: A.RawSource, opts: Options):
    cur = Curation(ns, src, opts).run()
    doc = cur.build_doc()
    return cur, doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ns", action="append", default=[], help="namespace (repeatable) or 'all'")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--raw-ref", help="git ref holding raw/ (e.g. origin/oem-raw)")
    g.add_argument("--raw-dir", help="directory holding raw/ (fixtures)")
    ap.add_argument("--as-of")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--out", default=str(GROUPS_DIR))
    ap.add_argument("--write-groups", action="store_true",
                    help="also write <out>/<ns>.json (shipped by the payload builder)")
    ap.add_argument("--propose-map", action="store_true")
    ap.add_argument("--model-map", default=str(MM.MODEL_MAP_PATH))
    ap.add_argument("--inventory", default=str(MM.INVENTORY_PATH))
    a = ap.parse_args(argv)
    import junkyard_scraper as js  # noqa: E402  (offline: curated tables + normalizers)
    import validate as V  # noqa: E402
    nss = sorted(policy.NAMESPACES) if (not a.ns or "all" in a.ns) else a.ns
    mm = MM.ModelMap(MM.load(a.model_map))
    inv = MM.load_inventory(a.inventory)
    errs, warns, mrep = MM.validate(mm, inv, js, policy.NAMESPACES)
    if errs:
        print("model_map.json fails validation; curate refuses to run:", *errs, sep="\n  ", file=sys.stderr)
        return 2
    if mrep.get("skipped"):
        print("model map checks skipped:", ", ".join(mrep["skipped"]), file=sys.stderr)
    src = A.RawSource(ref=a.raw_ref) if a.raw_ref else A.RawSource(raw_dir=a.raw_dir)
    inv_counts = Counter((r[3], r[4], r[2]) for r in inv["vehicles"]) if inv else Counter()
    out = Path(a.out)
    results = {}
    no_ns = [s for s in src.sites() if s not in policy.SITE_NS]
    for ns in nss:
        opts = Options(as_of=a.as_of, fixtures=a.fixtures, model_map=mm, model_map_path=Path(a.model_map),
                       inventory=inv, js=js)
        cur, doc = curate(ns, src, opts)
        results[ns] = cur
        if not cur.raw_meta:
            print(f"[curate] {ns}: no raw for its sites; skipped", file=sys.stderr)
            continue
        problems = V.structural(doc, V.context_from(js, mm))
        rep, completion = cur.report(doc, inv_counts)
        rep["model_map_report"] = mrep
        rep["sites_without_namespace"] = no_ns
        rep["validator"] = problems
        write_json(out / "_report" / f"{ns}.json", rep)
        (out / "_report" / f"{ns}.md").write_text(report_md(rep))
        write_json(out / "_report" / f"{ns}.completion.json", completion)
        if problems:
            print(f"[curate] {ns}: validator refused the groups file: {problems[:3]}", file=sys.stderr)
        elif a.write_groups:
            write_json(out / f"{ns}.json", doc)
        s = rep["summary"]
        print(f"[curate] {ns}: records {s['records']} cells {s['cells']} verified {s['verified_groups']} "
              f"vg {s['vg_groups']} likely {s['likely_groups']}; {s['why_no_verified']}", file=sys.stderr)
    coll = cross_ns_collisions(results)
    if coll:
        write_json(out / "_report" / "cross_ns_string_collisions.json", coll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
