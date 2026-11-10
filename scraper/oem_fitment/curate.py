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
OPTIMISTIC_WHY = {"notes_not_own_page", "fitted_not_listed", "trims_unattested", "engines_unattested"}
CLOSURE_REASONS = ["no_year_manifest", "year_manifest_bad", "variant_unread", "no_list_manifest",
                   "list_manifest_bad", "unread_sibling_page", "unverified_product", "suspect_variant",
                   "uncrawled_chain_member", "chain_fitment_inconsistent", "stale", "unattested",
                   "ambig_target", "site_blocked", "listed_not_fitted_only"]


def _canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha1(o) -> str:
    return hashlib.sha1(_canon(o).encode()).hexdigest()


def policy_sha256(model_map_path: Path | None = None) -> str:
    """policy.py + notes.py + positions.py + model_map.json; never the audit
    store (audits.json), which the payload loader checks the same way."""
    return policy.tree_sha256(model_map_path or MM.MODEL_MAP_PATH)


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
        # policy.WHEEL_COMPACT_SPARE_RE: one record naming a compact / temporary
        # spare refuses every record of that (site, wheels, pn)
        # (policy.WHEEL_NOTES_ARE_OPTIONS: sites whose notes list the car's options)
        compact_spare = {(r.site, r.pn) for r in self.records if r.cat == "wheels" and any(
            policy.WHEEL_COMPACT_SPARE_RE.search(x or "") for x in [r.name, r.aux, r.description]
            + ([] if r.site in policy.WHEEL_NOTES_ARE_OPTIONS else r.note_texts))}
        for r in self.records:
            if r.cat == "wheels" and (r.site, r.pn) in compact_spare:
                self.refuse("wheel_compact_spare", cat=r.cat, pn=r.pn, evidence=[r.pointer],
                            detail="a record of this number names a compact / temporary spare")
                continue
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
        self._cat_ctx = cat     # the production-date rule skips PROD_RULE_SKIP_CATS (wheels: own stricter rule)
        rows = [lr for lr in self.t_list_rows.get((T, cat), []) if policy.pn_key(self.ns, lr.pn) == c.key]
        if self.t_list_rows.get((T, cat)):
            # a row restricted to another make's division ("Lincoln Division
            # Derivative" on a Ford page) is not listed for T (§5.6)
            on = [lr for lr in rows if lr.matched and not self.note_excludes(lr.notes, T)]
            # §5.6: T's own manifest rows for that pn, matched or not: a second
            # row of the same number on T's page ('Japan Built') restricts it
            # even when the crawler did not match that row (review F9).
            # 'On page' stays tied to matched rows.
            notes = [n for lr in rows for n in lr.notes]
            src = [("location", x) for lr in on for x in lr.locations] + [("slug", lr.list_url) for lr in on]
            src += [("note", n) for n in self.note_position_texts(notes, T)]     # §5.8
            return bool(on), notes, src, [lr.pointer for lr in on], "manifest"
        recs = [r for r in self.t_seed_records.get((T, cat), [])
                if r.key == c.key and not self.note_excludes(r.note_texts, T)]
        notes = [n for r in recs for n in r.note_texts]
        src = [("location", x) for r in recs for x in r.list_location] + [("slug", r.list_url) for r in recs]
        src += [("note", n) for n in self.note_position_texts(notes, T)]
        return bool(recs), notes, src, [r.pointer for r in recs], "seed"

    def note_excludes(self, notes, T, market: bool = True) -> bool:
        """§5.6 model restriction (2026-11-09): True when T's own-page row
        restricts the number to another model, body or make, so it is not
        listed for T. Option columns and notes on shared diagram pages name
        the vehicle the number is for:
        - another make's division ("Lincoln Division Derivative", Ford);
        - Mopar brand codes ("C - CHRYSLER", "D - DODGE", "E - DODGE AWD");
        - catalog model names of this namespace ("Jetta; Sedan" on a VW page
          shared by Golf/Jetta; "Camry Hybrid; SE" on a Camry page);
        - subarupartsdeal "Fitting Vehicle Options" body codes on the
          Legacy/Outback/Baja pages (S/W = Legacy, OBK/SOBK/WOBK = Outback,
          P/BAJA = Baja).
        - foreign-market notes ('FOR CANADA'; per row only, market=False in
          the class-wide pool: a Canada row on one year says nothing about
          another year's row).
        Only ever removes claims; an unparsed note restricts nothing here."""
        if market and (_market_excludes(notes) or _export_only(notes)):
            return True
        if market and self.ns == "subaru" and _subaru_manual_only(notes):
            return True
        if market and getattr(self, "_cat_ctx", None) not in PROD_RULE_SKIP_CATS \
                and _production_excludes(notes, T[2]):
            return True
        if _other_division(notes, T[0]):
            return True
        if _brand_codes_exclude(notes, T[0]):
            return True
        if self.ns == "subaru" and _subaru_body_excludes(notes, T[1]):
            return True
        if self.ns == "toyota" and market and _lexus_chassis_excludes(notes, T):
            return True
        return self._model_names_exclude(notes, T)

    def _model_names_exclude(self, notes, T) -> bool:
        names = getattr(self, "_note_model_names", None)
        if names is None:
            # catalog model names, plus the feed models they map to ('Camry
            # Hybrid' is a feed model; the catalog files it under Camry)
            pool = set(getattr(self, "ns_models", set())) | {
                md.lower() for ms in getattr(self, "class_feed_models", {}).values() for (_mk, md) in ms}
            names = sorted({m for m in pool
                            if len(m) >= 3 and m not in _MODEL_NAME_STOP and not m.isdigit()},
                           key=lambda m: (-len(m), m))
            self._note_model_names = names
            self._note_model_rx = [(m, re.compile(r"(?<![A-Za-z0-9])" + re.escape(m) + r"(?![A-Za-z0-9])", re.I))
                                   for m in names]
        own = {T[1].lower()} | {cm.lower() for (_mk, cm) in self.t_sources.get(T, set())}
        for n in notes or []:
            text = n or ""
            named = set()
            for m, rx in self._note_model_rx:
                if rx.search(text):
                    named.add(m)
                    text = rx.sub(" ", text)   # 'Camry Hybrid' is not also 'Camry'
            if named and not (named & own):
                return True
        return False

    def note_position_texts(self, notes, T) -> list:
        """§5.8: notes feed position resolution through their POSITION
        clauses only, so a colour ("Lt Gray") is not read as a side. An
        UNKNOWN clause is passed whole: it may carry a side the lexicon does
        not know, and a side read there can only add a conflict."""
        ctx = N.NoteContext(T[2], frozenset(m.lower() for _, m in self.t_sources.get(T, set())),
                            getattr(self, "ns_models_f", frozenset()))
        out = []
        for n in notes:
            for seg in N.split_note(n):
                for cl in seg:
                    c = N.classify_clause(cl, ctx)
                    if c.cls == "UNKNOWN":
                        out.append(cl)
                    else:
                        out += [a.text for a in c.atoms if a.cls == "POSITION"]
        return out

    # ------------------------------------------------------ 5.7 universes
    def universes(self):
        self.trimu, self.trimu_src, self.engineu, self.trimu_by_engine = {}, {}, {}, {}
        self.engineu_src = {}
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
            reliable = [(cat, r) for cat, c, r, f, t in good if self.reliable.get(r.site)]
            for cat, c, r, f, t in good:
                if self.reliable.get(r.site):
                    eng |= f.engine_keys()
            # review F8: the year page's engine list (R2) is part of EngineU,
            # so an engine no crawled row prints still has to be covered (an
            # unparsed one fails every universe test, §5.5). Without it, a
            # row-derived EngineU must be attested like TrimU (§5.7).
            ye = [ym for ym in self.t_years.get(T, []) if ym.engines and _status_ok(ym.status) and not ym.error]
            eng |= {A.engine_key(e) for ym in ye for e in ym.engines}
            self.engineu[T] = frozenset(eng)
            if ye:
                self.engineu_src[T] = "year_page"
            elif len({(r.site, r.line) for _, r in reliable}) >= policy.TRIMU_MIN_RECORDS and \
                    len({cat for cat, _ in reliable}) >= policy.TRIMU_MIN_CATS and eng:
                self.engineu_src[T] = "fitment"
            else:
                self.engineu_src[T] = "unattested"

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
        """§5.9: an old -> new edge. A cross-category edge (one end known only
        in another category) is reported and never joins the two classes,
        but it is never dropped either (review F5): it stays in this
        category's graph, where the far end has no class, so C5
        (uncrawled_chain_member) blocks the in-category end; and it is added
        to the far end's category too, where it blocks that end the same way.
        Adding a record can therefore never remove an edge."""
        if a == b:
            return
        cats = {cat}
        for end in (a, b):
            if end in known and cat not in known[end]:
                self.refuse("cross_category_supersession", cat=cat, pn=end,
                            evidence=[r.pointer] if r else None, detail=",".join(sorted(known[end])))
                cats |= known[end]
        for c in sorted(cats):
            self.edges[c].add((a, b))

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

    def chain_keys(self, cat, key) -> set:
        """Every ancestor and descendant C5 checks (depth CHAIN_DEPTH)."""
        return self.reach(cat, key, policy.CHAIN_DEPTH) | self.reach(cat, key, policy.CHAIN_DEPTH, down=False)

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
        if self.engineu_src.get(T, "unattested") == "unattested" and T not in self.o.trimu_force:
            why.append("engines_unattested")
        eu = self.engineu.get(T, frozenset()) if engine_set is None else engine_set
        # each trim-layout row's outcome; any row that covers the car makes it
        # 'ok'. Otherwise the reason kept is a real condition when one row
        # gives one (the row lists only some trims / engines: the catalog
        # numbers differ by configuration, which §7.6 oem_split reads), else
        # an evidence gap (blank trim cell, engine cells unaudited, an
        # unparsed or unattested engine universe), which says nothing about
        # the numbers differing.
        outcomes = set()
        for r, f, t in rows:
            if f.layout != "trim" or f.trims_from_options:
                continue
            if not f.trims:
                outcomes.add("trims_unknown")
                continue
            if not tu <= f.trim_atoms():
                outcomes.add("conditional_trims")
                continue
            if not self.reliable.get(r.site):
                outcomes.add("engines_unreliable")
                continue
            # an unparsed engine ("?", raw) fails every universe test (§5.5),
            # even when both sides print the same text
            if not eu:
                outcomes.add("engines_unattested")
                continue
            if any(not isinstance(e[0], int) for e in eu):
                outcomes.add("engines_unparsed")
                continue
            if not eu <= f.engine_keys():
                outcomes.add("conditional_engines")
                continue
            outcomes.add("ok")
        best = None
        for o in ("ok", "conditional_trims", "conditional_engines", "trims_unknown", "engines_unparsed",
                  "engines_unreliable", "engines_unattested"):
            if o in outcomes:
                best = o
                break
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
        why = _uniq(why)
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
    def required_cvs(self, T) -> list:
        """Every catalog vehicle the model map feeds into T this year (§6:
        with a merge mapping, every merged cv must close), whether or not a
        fitment row happens to name it; plus any cv a row mapped (a subset)."""
        srcs = {(t.cat_make, t.cat_model) for t in self.mm.sources(self.ns, T[0], T[1], T[2])}
        return sorted(srcs | self.t_sources.get(T, set()))

    def _longer_models(self, cmk: str, cmd: str) -> list:
        """Token lists of the namespace's other catalog models of this make
        whose name contains this one ('Wrangler JK' for 'Wrangler')."""
        key = (cmk, cmd)
        cache = self.__dict__.setdefault("_longer_cache", {})
        if key not in cache:
            mine = _tokens(cmd)
            names = {md for (ns, mk, md) in self.mm.by_cat if ns == self.ns and mk == cmk}
            names |= {k.split("|", 2)[2] for k in self.mm.exclude
                      if k.count("|") >= 2 and k.split("|", 2)[:2] == [self.ns, cmk]}
            cache[key] = [_tokens(md) for md in sorted(names)
                          if md != cmd and len(_tokens(md)) > len(mine) and _has_run(_tokens(md), mine)]
        return cache[key]

    def _title_cv(self, title: str, cmk: str, cmd: str, year: int) -> bool:
        """The year page is cv's own page: its title names cv's model and
        year, and no longer catalog model of the make that contains it
        ('2018 Jeep Wrangler JK Parts' is not the 'Wrangler' page)."""
        if not _title_names(title, cmd, year):
            return False
        toks = _tokens(title)
        return not any(_has_run(toks, other) for other in self._longer_models(cmk, cmd))

    def _year_ok(self, ym) -> bool:
        """C1 for one year manifest: HTTP 200, no crawler error, no redirect,
        and a sub list that holds at least one category page the site module
        reads (an empty or foreign sub list means the page did not parse, so
        'every category page read' would be vacuous: review F3)."""
        if not _status_ok(ym.status) or ym.error:
            return False
        if ym.final_url and ym.final_url.split("?")[0] != ym.year_url.split("?")[0]:
            return False
        if not A.year_stem(ym.year_url):
            return False
        pages = [rx for rx in A.site_cat_pages(ym.site).values() if rx is not None]
        return any(rx.search(sub) or rx.search(sub.split("/")[-1]) for sub in ym.subs for rx in pages)

    def closure(self, T, cat, members) -> list:
        reasons = []
        years = self.t_years.get(T, [])
        required = self.required_cvs(T)
        if any(t.ambig for t in self.mm.sources(self.ns, T[0], T[1], T[2])):
            reasons.append("ambig_target")
        if not years:
            reasons.append("no_year_manifest")
        # C1 per required cv: an ok year manifest that is that cv's own page
        good_by_cv = {}
        for cmk, cmd in required:
            named = [ym for ym in years if self._title_cv(ym.title, cmk, cmd, T[2])]
            okd = [ym for ym in named if _status_ok(ym.status) and not ym.error]
            if not okd or not all(self._year_ok(ym) for ym in okd):
                if years:
                    reasons.append("year_manifest_bad")
                good_by_cv[(cmk, cmd)] = []
                continue
            good_by_cv[(cmk, cmd)] = okd
            for ym in okd:
                if ym.site not in policy.SIMPLEPART_SITES:
                    read = {y.variant for y in years if y.site == ym.site}
                    if set(ym.variants or []) - read:
                        reasons.append("variant_unread")
        good_years = [ym for yms in good_by_cv.values() for ym in yms]
        good_stems = {(ym.site, A.year_stem(ym.year_url)) for ym in good_years}
        lists = [lr for lr in self.t_list_rows.get((T, cat), [])]
        manifests = {(lr.site, lr.list_url): lr for lr in lists}
        if not lists:
            reasons.append("no_list_manifest")
        else:
            if any(not _status_ok(lr.status) or lr.error for lr in manifests.values()):
                reasons.append("list_manifest_bad")
            # a list page is T's only when it hangs off one of T's own ok year
            # pages (same site and catalog stem): another year's or model's
            # page never closes T (review F10)
            if any((lr.site, A.list_stem_sub(lr.list_url)[0]) not in good_stems for lr in manifests.values()):
                reasons.append("list_manifest_bad")
            # C2: every CAT_PAGES sub on each year page read for T (every one,
            # not only the pages C1 accepted) has a list manifest from that
            # page's own stem; no unread sibling sub matching NOUN[cat]
            for ym in [y for y in years if _status_ok(y.status) and not y.error]:
                pages = A.site_cat_pages(ym.site).get(cat)
                stem = A.year_stem(ym.year_url)
                read_subs = {A.list_stem_sub(lr.list_url)[1] for lr in manifests.values()
                             if lr.site == ym.site and A.list_stem_sub(lr.list_url)[0] == stem
                             and _status_ok(lr.status) and not lr.error}
                for sub in ym.subs:
                    tail = sub.split("/")[-1]
                    hit = (pages.search(sub) or pages.search(tail)) if pages else False
                    if hit and sub not in read_subs:
                        reasons.append("unread_sibling_page")   # a category page of T was not read
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
        # C1: at least one matched pn's own fitment lists the vehicle-year;
        # per merged cv, a cv whose own pages list matched rows needs one of
        # them fitted to T through that cv
        rows = self.t_rows.get((T, cat), [])
        if members and not any(cc is m["klass"] for m in members.values() for cc, *_ in rows):
            reasons.append("listed_not_fitted_only")
        for cv, yms in sorted(good_by_cv.items()):
            stems = {(ym.site, A.year_stem(ym.year_url)) for ym in yms}
            keys = {policy.pn_key(self.ns, lr.pn) for lr in lists
                    if lr.matched and (lr.site, A.list_stem_sub(lr.list_url)[0]) in stems}
            if keys and not any(c.key in keys and (t.cat_make, t.cat_model) == cv for c, r, f, t in rows):
                reasons.append("listed_not_fitted_only")
        # C5 chain completeness
        for key, m in members.items():
            for d in self.chain_keys(cat, key):
                dc = self.classes.get((d, cat))
                if dc is None or not dc.verified:
                    reasons.append("uncrawled_chain_member")
                elif any(self.stale(r.retrieved) for r in dc.records):
                    reasons.append("stale")         # C6 covers what C5 relied on
            for d in self.reach(cat, key, policy.CHAIN_DEPTH):
                dc = self.classes.get((d, cat))
                if dc is not None and not any(cc is dc for cc, *_ in rows):
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
        """C4 for one unmatched row on T's page. Every unmatched row's head
        phrase is re-run through the site's own rule, whatever the crawler
        said (include_miss, rule:/global:, url_pn_mismatch, section_not_read,
        None, '' or a reason this code does not know): a row whose head
        phrase passes is a candidate T's cell never accounted for, so the
        cell stays open. Only reman_dropped follows its spec rule (a suspect
        for engine categories until R5b lands). When the rule cannot be
        re-run offline, the row is a suspect (fail closed)."""
        if lr.excluded_by == "reman_dropped":
            return cat in policy.ENGINE_CATS
        key = (lr.site, cat, lr.main, lr.aux, lr.group, lr.remark, lr.link, tuple(lr.notes), tuple(lr.locations))
        cache = self.__dict__.setdefault("_suspect_cache", {})
        if key in cache:
            return cache[key]
        # head phrase: the name with every qualifier phrase deleted up to the
        # next comma ("Mirror Assy, Outer Rear View, W/Turn Signal Lamp" ->
        # "Mirror Assy, Outer Rear View")
        head = lambda s: re.sub(r"[\s,;]+$", "", N.QUALIFIER_RE.sub(" ", s or "")).strip()  # noqa: E731
        info = [f"Location: {x}" for x in lr.locations] + list(lr.notes)
        fake = A.Record(site=lr.site, ns=self.ns, cat=cat, pn=lr.pn, key="", line=lr.line,
                        template=A.template_of(lr.site, {}), name=head(lr.main), aux=head(lr.aux),
                        other_names="", description="", list_url=lr.list_url, section=lr.section, position="",
                        list_location=[], note_texts=[], replaces=[], replaced_by=[], list_replaced_by=[],
                        chain_unknown=False, reman_flag=False, rows=[], flags=[], evidence_lines=[],
                        rendered=None, total=None, retrieved=lr.retrieved, seed=lr.seed, via=None,
                        recrawl_of=None, product_url=lr.link,
                        raw={"list_group": lr.group, "list_remark": head(lr.remark), "list_info": info})
        m = A.rule_matches(fake)
        cache[key] = m is not False
        return cache[key]

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
                # real condition classes first (the numbers differ by
                # configuration), then evidence gaps, so a cell's first reason
                # names a real split whenever there is one (§7.6)
                for x in sorted(cls, key=lambda x: (x not in policy.SPLIT_CONDITIONS, x)):
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
        # funnel order (§10.3): split, conditional, chain member, reman, blocked, gated;
        # inside "split": option_split, packaging_*, chain crossings, positions, slots
        reasons = sorted(_uniq(reasons), key=lambda r: (STAGES.index(_stage_of(r)), _split_rank(r)))
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
            elif info["closure"]:
                cells.append([T[0], T[1], T[2], cat, f"open:{reason}"])
            else:
                # a closed cell names a real split first when it has one, so
                # §7.6 oem_split never reads an evidence gap as a split
                trig = [r for r in info["elig"] if _split_trigger(r)]
                cells.append([T[0], T[1], T[2], cat, f"open:{trig[0] if trig else reason}"])
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
        for g in vg:
            sigs[g["id"].rsplit(":", 1)[-1]] = g["sig"]
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
            # §7.6: per-family states of engine-category cells (never shipped)
            "engine_cells": sorted(getattr(self, "engine_cells", [])),
        }
        return doc

    def _proof(self, T, cat):
        info = self.cells_info[(T, cat)]
        lists = sorted({lr.pointer for lr in self.t_list_rows.get((T, cat), [])})
        years = sorted({ym.pointer for ym in self.t_years.get(T, [])})
        # every record closure relied on ages the proof, including the chain
        # members C5 walked (review F11: build-time expiry reads this stamp)
        chain = {d for k in info["members"] for d in self.chain_keys(cat, k)}
        stamps = [lr.retrieved for lr in self.t_list_rows.get((T, cat), [])] + \
                 [ym.retrieved for ym in self.t_years.get(T, [])] + \
                 [r.retrieved for m in info["members"].values() for r in m["klass"].records] + \
                 [r.retrieved for d in sorted(chain) for r in (self.classes.get((d, cat)) or Klass(d, cat, set(), [])).records]
        stamps = sorted(s for s in stamps if _ts(s))
        return {"t": list(T), "cv": sorted([[cmk, cmd, T[2]] for cmk, cmd in self.t_sources.get(T, set())]),
                "closure": {"year": years[0] if years else None, "years": years, "lists": lists,
                            "oldest_retrieved": stamps[0] if stamps else None},
                "universe": {"trims_src": self.trimu_src.get(T), "trims": sorted(
                    " ".join(x for x in a if x) for a in self.trimu.get(T, ()))}}

    # ---------------------------------------------- 5.13 engine attachment
    def _ef(self, T, fam) -> frozenset:
        """E_f(cv) (§5.13): EngineU keys with the family's cylinder count and
        liters (within 0.05), regardless of fuel."""
        return frozenset(e for e in self.engineu.get(T, ()) if _fam_engine(e, fam))

    def engine_cell_state(self, T, cat, info, fam) -> str:
        """§7.6 per-family state of an engine-category cell: what the hand
        vg contradiction test reads, never a claim. The generic cell mixes
        every engine the model-year offers, so a second number that belongs
        to another family made it option_split and removed correct hand
        groups (review F13). Here the cell is narrowed to the family (5.13:
        E_f, TrimU_f), and a candidate whose every fitment row prints only
        engines outside the family (trim layout, parsed) is not one of its
        candidates. 'sig:<h>' when that narrowed cell is eligible, else
        'open:<reason>' with a real split (option_split or a
        policy.SPLIT_CONDITIONS class) named first when there is one."""
        if info["closure"]:
            return f"open:{info['closure'][0]}"
        ef = self._ef(T, fam)
        if not ef:
            return "open:family_gap"
        rows = self.t_rows.get((T, cat), [])
        per = []
        for e in sorted(ef, key=str):
            mem = self.cell(T, cat, engine_set=frozenset([e]))
            mem = {k: m for k, m in mem.items()
                   if any(e in f.engine_keys() for cc, r, f, t in rows if cc is m["klass"] and f.layout == "trim")}
            per.append(_canon(sorted(mem)))
        if len(set(per)) != 1:
            # two engines of the family each with their own printed numbers:
            # the numbers differ inside the family, a real split (§7.6). An
            # engine with no row at all is only a gap.
            if all(x != _canon([]) for x in per):
                return "open:conditional:engine"
            return "open:family_nonuniform"
        members = self.cell(T, cat, engine_set=ef, trim_u=self._trimu_f(T, ef))

        def other_engine_only(m):
            fr = [f for cc, r, f, t in rows if cc is m["klass"]]
            return bool(fr) and all(f.layout == "trim" and f.engine_keys()
                                    and all(isinstance(e[0], int) and not _fam_engine(e, fam) for e in f.engine_keys())
                                    for f in fr)
        members = {k: m for k, m in members.items() if not other_engine_only(m)}
        elig, slots = self.eligibility(T, cat, members)
        if not elig:
            return f"sig:{_sha1(self.sig_of(slots))[:10]}"
        trig = [r for r in elig if _split_trigger(r)]
        return f"open:{(trig or elig)[0]}"

    def engine_groups(self, groups_by, sigs):
        js = self.js
        out = defaultdict(list)
        self.engine_refusals = []
        self.engine_cells = []
        for (T, cat), info in sorted(self.cells_info.items()):
            if cat not in policy.ENGINE_CATS:
                continue
            # (a)/(b) are reported for every cell, closed or not
            fams = js.engine_families_for(T[2], T[0], T[1], cat if cat != "ignition-coils" else None)
            for fid_, fam_, _app in fams:
                self.engine_cells.append([T[0], T[1], T[2], cat, fid_, self.engine_cell_state(T, cat, info, fam_)])
            if not fams:
                self.engine_refusals.append({"reason": "family_gap", "t": list(T), "cat": cat})
                continue
            if len(fams) != 1:
                self.engine_refusals.append({"reason": "family_ambiguous", "t": list(T), "cat": cat})
                continue
            if info["closure"]:
                continue
            fid, fam, app = fams[0]
            if js._app_flags(app).get("ambig"):
                self.engine_refusals.append({"reason": "family_ambig", "t": list(T), "cat": cat})
                continue
            ef = self._ef(T, fam)
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
        """§5.7 engine-sliced trims, never wider in claims than TrimU allows
        (review F4): rows that print engines inside E_f show which trims DO
        carry the family, but a trim missing from them is not proof it does
        not. So TrimU_f is TrimU (year page, or attested fitment) minus only
        the trims the evidence ties to other engines alone: seen on verified
        trim-layout rows whose engines all lie outside E_f, never on a row
        that prints an E_f engine, and only when the E_f slice itself is
        attested like TrimU (>= TRIMU_MIN_RECORDS records from >=
        TRIMU_MIN_CATS categories). A car whose every engine is in the family
        has nothing to slice."""
        tu = self.trimu.get(T, frozenset())
        eu = self.engineu.get(T, frozenset())
        if not ef or eu <= ef:
            return tu
        good = [(cat, f, r, t) for (cat, c, r, f, t) in self.rows_by_T.get(T, [])
                if f.layout == "trim" and not r.problems and not f.trims_from_options and f.engine_keys()]
        inside = [(cat, f, r, t) for cat, f, r, t in good if f.engine_keys() <= ef]
        recs = {(r.site, r.line) for _, _, r, _ in inside}
        cats = {cat for cat, *_ in inside}
        if len(recs) < policy.TRIMU_MIN_RECORDS or len(cats) < policy.TRIMU_MIN_CATS:
            return tu
        with_f = {a for _, f, _, _ in good if f.engine_keys() & ef for a in f.trim_atoms()}
        only_other = {a for _, f, _, _ in good if not (f.engine_keys() & ef) for a in f.trim_atoms()}
        return frozenset(a for a in tu if not (a in only_other and a not in with_f))

    # ------------------------------------------------------- 5.16 likely
    def likely_groups(self, brand):
        out = []
        self.likely_own_page_drops = Counter()   # cat -> vehicle-years left out (§5.16 own-page rule)
        self.own_page_missing = defaultdict(lambda: defaultdict(set))  # T -> cat -> class keys (R3 input)
        self.held_exterior = []                  # §5.16 exterior hold (owner checklist)
        self.likely_note_restricted = Counter()
        self.likely_generation_cut = Counter()     # cat -> vehicle-years cut at a generation break  # cat -> vehicle-years a class-wide note restricts away
        self.release_allow = policy.release_allowlist()   # §5.16 exact owner-approved releases
        self.release_notes = policy.release_notes()
        self.released_exterior = []
        for (key, cat), c in sorted(self.classes.items()):
            if self.kinds.get(cat) != "body" or cat in policy.PHASE3_CATS:
                continue
            if not c.verified or "universal_part_suspect" in c.problems:
                continue
            # only vehicle-years where the class is a member of the cell
            # (cover yes / maybe, §5.16): a record that resolves out of the
            # category there (Mopar passenger window switch 4602540AF) makes
            # no claim. A window switch must also resolve to the driver
            # master slot: an unresolved side may be a passenger or
            # single-gang switch (4602531AD "1 gang", quantity 2).
            cand, class_notes, dropped = [], [], []
            for T in sorted(self.class_Ts.get((key, cat), ())):
                m = (self.cells_info.get((T, cat)) or {}).get("members", {}).get(key)
                if not m or m["cover"] not in ("yes", "maybe"):
                    continue
                if cat == "window-switch" and (m["slot"].reason or m["slot"].slots != ("DM",)):
                    continue
                on, notes = self.own_page(T, cat, c)[:2]
                if policy.LIKELY_REQUIRES_OWN_PAGE and not on:
                    # §5.16 own-page rule: the product page's fitment table
                    # alone can be a platform rollup
                    self.likely_own_page_drops[cat] += 1
                    dropped.append(T)
                    continue
                cand.append((T, m))
                class_notes += notes
            # R3 own-page completion input: the left-out vehicle-years of a
            # class that would span 2+ feed models if their own pages listed it
            if dropped and len({(T[0], T[1]) for T in dropped} | {(T[0], T[1]) for T, _ in cand}) >= 2:
                for T in dropped:
                    self.own_page_missing[T][cat].add(key)
            # §5.6 model restriction, class-wide (2026-11-09): one own page
            # restricting the number to a make/model/body ('C - CHRYSLER' on
            # the 2006 300 page for mirror 1BY421R3AA) contradicts a twin's
            # page that lists it bare (2007 Charger); fail closed for Likely
            Ts, whys, slots = [], set(), set()
            for T, m in cand:
                if self.note_excludes(class_notes, T, market=False):
                    self.likely_note_restricted[cat] += 1
                    continue
                Ts.append(T)
                whys |= set(m["why"])
                slots |= set(m["slot"].slots)
            Ts = self._drop_catchall_twins(Ts)
            if len({(T[0], T[1]) for T in Ts}) < 2:
                continue        # single-model: the same-model generation loop covers it
            Ts2 = self._generation_cut(c, Ts)
            if Ts2 != Ts:
                self.likely_generation_cut[cat] += len(Ts) - len(Ts2)
                Ts = Ts2
                if len({(T[0], T[1]) for T in Ts}) < 2:
                    continue
            reason, text = _likely_reason(whys)
            text = policy.GROUP_NOTES.get((self.ns, cat, sorted(c.pns)[0]), text)
            cab = self._cab_only(c, cat, Ts)
            if cab:
                text = f"{text}; {cab}"
                if len(_likely_note(brand, sorted(c.pns)[0], text, _pack_text(cat, c.packaging))) > policy.NOTE_MAX_LEN:
                    self.refuse("held_cab_qualifier", cat=cat, pn=sorted(c.pns)[0],
                                evidence=[r.pointer for r in c.records], detail=cab)
                    continue
            pns = sorted(c.pns)
            apps = _runs(Ts)
            rkey = (self.ns, cat, tuple(pns), tuple(tuple(a) for a in apps))
            released = rkey in self.release_allow
            if released and rkey in self.release_notes:
                text = self.release_notes[rkey]     # the split its source states (hub 2026-11-09)
            if released:
                self.released_exterior.append({"cat": cat, "pn": pns, "apps": apps})
            hold = policy.held_cross_model_cat(self.ns, cat)
            if not released and hold and \
                    len({policy.base_model(T[0], T[1]) for T in Ts}) > 1:
                # §5.16 exterior hold: only removes claims; kept for the owner checklist
                urls = sorted({u for r in c.records for u in (r.product_url, r.list_url) if u})
                self.refuse(hold, cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                            detail=";".join(f"{a[0]} {a[1]} {a[2]}-{a[3]}" for a in apps))
                self.held_exterior.append({"ns": self.ns, "cat": cat, "pn": pns, "apps": apps,
                                           "note": _likely_note(brand, pns[0], text, _pack_text(cat, c.packaging)),
                                           "reason": reason, "urls": urls})
                continue
            if cat == "wheels":
                why_w = self.wheel_group_refusal(Ts, cat, c)
                if why_w:
                    self.refuse(why_w[0], cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail=why_w[1])
                    continue
            slot = "+".join(sorted(slots)) or "C"
            note = _likely_note(brand, pns[0], text, _pack_text(cat, c.packaging))
            # its own evidence date: build-time expiry drops a Likely group
            # whose oldest record passes 120 days (review F18)
            stamps = sorted(r.retrieved for r in c.records if _ts(r.retrieved))
            out.append({"id": f"oem:{self.ns}:{cat}:{slot}:{_sha1([pns, apps])[:10]}", "cat": cat,
                        "tier": "likely", "kind": "body", "apps": apps, "pn": pns, "reason": reason,
                        "note": note, "keys": [key], "cars": sum(self.inv_counts.get(T, 0) for T in Ts),
                        "oldest_retrieved": stamps[0] if stamps else None})
        return out

    def wheel_group_refusal(self, Ts, cat, c):
        """(code, detail) when a wheels Likely group lacks a stated, agreeing
        basis on every app's own page (policy.WHEEL_DIAMETER_RE etc.), else None."""
        if self.ns not in policy.WHEELS_AUDITED_NS:
            return "wheels_not_audited", f"{self.ns}: no passed §11.4 wheels audit yet"
        if self.ns in policy.WHEEL_SAME_MODEL_ONLY_NS and len({(T[0], T[1]) for T in Ts}) > 1:
            return "wheel_cross_model_chassis", "; ".join(sorted({f"{T[0]} {T[1]}" for T in Ts}))
        # a record whose own description names a spare ("Spare Wheel, Steel",
        # Mopar 5105665AA; 19 of 541 Mopar wheel records) is not offered
        for r in c.records:
            if policy.WHEEL_SPARE_NOTE_RE.search(r.description or ""):
                return "wheel_spare_description", f"{r.pn}: {r.description[:80]}"
        sizes, widths = {}, set()
        bodies, spokes = [], set()
        for T in Ts:
            notes = [n or "" for n in self.own_page(T, cat, c)[1]]
            text = " ; ".join(notes)
            if policy.WHEEL_SPARE_NOTE_RE.search(text):
                return "wheel_spare_note", f"{T[0]} {T[1]} {T[2]}: {text[:120]}"
            own_num = set(policy.MODEL_NUMBER_RE.findall(T[1]))
            other = set(policy.MODEL_NUMBER_RE.findall(text)) - own_num
            if other:
                return "wheel_model_other", f"{T[0]} {T[1]} {T[2]}: names {sorted(other)}"
            # rows of this number on T's own page vs every wheel row of that page
            prow = [lr for lr in self.t_list_rows.get((T, cat), []) if policy.pn_key(self.ns, lr.pn) == c.key]
            norm = lambda x: re.sub(r"\s+", " ", x.lower()).strip()
            if len({(t[0], t[1]) for t in Ts}) > 1 and prow:
                page_b = {norm(m.group(1)) for lr in self.t_list_rows.get((T, cat), []) for n in lr.notes
                          for m in policy.WHEEL_BODY_OPTION_RE.finditer(n or "")}
                pn_b = {norm(m.group(1)) for lr in prow for n in lr.notes
                        for m in policy.WHEEL_BODY_OPTION_RE.finditer(n or "")}
                # the product page's fitment rows count too (529101M550: list row
                # bare, product page "Coupe - 2Door 5P" only)
                pn_b |= {norm(m.group(1)) for r in c.records for f in r.rows
                         for m in policy.WHEEL_BODY_OPTION_RE.finditer(f.raw or "")}
                if pn_b and page_b - pn_b:
                    return "wheel_body_option", f"{T[1]} {T[2]}: row {sorted(pn_b)} of page {sorted(page_b)}"
            spans = []
            for lr in prow:
                rs = [m for n in lr.notes for m in policy.WHEEL_PRODUCTION_RE.finditer(n or "")]
                if not rs:
                    spans = None
                    break
                spans += [(int(m.group(1)), int(m.group(2) or m.group(1))) for m in rs]
            if spans and not any(a <= T[2] <= b + 1 for a, b in spans):
                return "wheel_production_date", f"{T[1]} {T[2]}: production {sorted(set(spans))}"
            if policy.WHEEL_AXLE_RE.search(text):
                return "wheel_axle_limited", f"{T[0]} {T[1]} {T[2]}: {text[:120]}"
            bodies.append(frozenset(m.group(1).lower() for m in policy.WHEEL_BODY_RE.finditer(text)))
            spokes |= {m.group(1) for m in policy.WHEEL_SPOKE_RE.finditer(text)}
            d = {m.group(1) for m in policy.WHEEL_DIAMETER_RE.finditer(text)}
            if not d:
                return "wheel_size_unstated", f"{T[0]} {T[1]} {T[2]}"
            sizes[T] = d
            widths |= {float(m.group(1)) for m in policy.WHEEL_WIDTH_RE.finditer(text)}
        allsz = set().union(*sizes.values()) if sizes else set()
        if len(allsz) != 1:
            return "wheel_size_conflict", "; ".join(f"{T[1]} {T[2]}: {sorted(v)}" for T, v in sizes.items())
        if len(widths) > 1:
            return "wheel_width_conflict", f"widths {sorted(widths)}"
        if len(set(bodies)) > 1:
            return "wheel_body_conflict", "; ".join(sorted("/".join(sorted(b)) or "-" for b in set(bodies)))
        if len(spokes) > 1:
            return "wheel_design_conflict", f"spokes {sorted(spokes)}"
        return None

    def _drop_catchall_twins(self, Ts):
        """Make breadth 2026-11-09: a feed name whose series is unknown
        ('Silverado', an ambig catch-all target) is left out of a Likely
        group when the group already holds a series-filtered target of the
        same catalog model and year ('Silverado 1500'): the catch-all car may
        be a 2500HD, and pairing it with the 1500 claims the 1500 part for it.
        Only removes claims."""
        def tg(T):
            return self.mm.sources(self.ns, T[0], T[1], T[2])
        precise = {(t.cat_make, t.cat_model, T[2]) for T in Ts for t in tg(T) if t.series}
        if not precise:
            return Ts
        out = []
        for T in Ts:
            ts = tg(T)
            if ts and all(t.ambig and not t.series for t in ts) and \
                    any((t.cat_make, t.cat_model, T[2]) in precise for t in ts):
                continue
            out.append(T)
        return out

    def _gen_breaks(self, model: str):
        """GENERATION_BREAKS for a feed model: longest leading-word key."""
        G = getattr(self.js, "GENERATION_BREAKS", None) or {}
        w = (model or "").lower().split()
        for i in range(len(w), 0, -1):
            if " ".join(w[:i]) in G:
                return G[" ".join(w[:i])]
        return None

    def _generation_cut(self, c, Ts):
        """Hub 2026-11-09 (GM 20945139: a GMT900 regulator whose product page
        'Replaces' four older numbers, listed on the 1999-2000 Silverado
        pages): a Likely group of a superseding number may not span a
        hand-curated generation break (GENERATION_BREAKS) of any of its base
        models. Supersession runs old -> new, so the vehicle-years before the
        newest break crossed are left out (every model, so a twin such as the
        2004 Sierra goes too). A number with no supersession keeps every
        vehicle-year: each already has its own page (§5.16). Only removes claims."""
        sup = any(r.replaces or r.replaced_by or r.list_replaced_by or r.via for r in c.records)
        if not sup:
            return Ts
        cut = None
        by = defaultdict(list)
        for T in Ts:
            by[policy.base_model(T[0], T[1])].append(T)
        for bm, ts in by.items():
            br = self._gen_breaks(ts[0][1]) or []
            ys = [T[2] for T in ts]
            crossed = [b for b in br if min(ys) < b <= max(ys)]
            if crossed:
                cut = max(cut or 0, max(crossed))
        if cut is None:
            return Ts
        return [T for T in Ts if T[2] >= cut]

    _CAB_RE = re.compile(r"\b(REGULAR CAB|EXTENDED CAB|CREW CAB|SUPER ?CAB|SUPER ?CREW|DOUBLE CAB|QUAD CAB|CREWMAX|ACCESS CAB|KING CAB)\b", re.I)

    def _cab_only(self, c, cat, Ts) -> str:
        """Hub 2026-11-09 (GM 15844876: Silverado fitment rows name extended
        cab only): when every fitment row crediting a model names one cab
        type, the group says '<model>: <cab> only' for it. '' when none does."""
        out = []
        for mk, md in sorted({(T[0], T[1]) for T in Ts}):
            cabs, all_cab = set(), True
            for T in Ts:
                if (T[0], T[1]) != (mk, md):
                    continue
                for (cc, r, f, t) in self.t_rows.get((T, cat), []):
                    if cc is not c:
                        continue
                    for tr in (f.trims or []):
                        m = self._CAB_RE.search(tr)
                        if not m:
                            all_cab = False
                        else:
                            cabs.add(re.sub(r"\s+", " ", m.group(1).lower()))
                    if not f.trims:
                        all_cab = False
            if all_cab and len(cabs) == 1:
                out.append(f"{md}: {next(iter(cabs))} only")
        return "; ".join(out)

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
                        "likely_app_years_without_own_page": dict(sorted(
                            getattr(self, "likely_own_page_drops", Counter()).items())),
                        "released_by_allowlist": len(getattr(self, "released_exterior", [])),
                        "likely_app_years_note_restricted": dict(sorted(
                            getattr(self, "likely_note_restricted", Counter()).items())),
                        "likely_app_years_generation_cut": dict(sorted(
                            getattr(self, "likely_generation_cut", Counter()).items())),
                        "blocked_sites": sorted(self.blocked),
                        "why_no_verified": _why_none(self), "gates": global_gates(self)},
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


    def own_page_completion(self, inv_counts: Counter):
        """R3 input for the §5.16 own-page rule (site-agnostic): one row per
        vehicle-year whose own catalog page was never read for a category in
        which a Likely candidate class names it. Each row carries the site
        that navigates its make (the site whose records were seeded on that
        make), so `crawl.py --complete` on any site reads only its own rows.
        Ordered by cars on the lots x classes waiting, then name. Only reads
        pages; a row whose page does not list the number stays out."""
        seed_site = defaultdict(Counter)
        for r in self.records:
            seed_site[r.seed[0]][r.site] += 1
        rows, unrouted = [], Counter()
        for T, by_cat in self.own_page_missing.items():
            sites = seed_site.get(T[0])
            if not sites:
                unrouted[T[0]] += 1
                continue
            site = sorted(sites.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            n = sum(len(v) for v in by_cat.values())
            cars = inv_counts.get(T, 0)
            rows.append({"site": site, "make": T[0], "model": T[1], "year": T[2], "cats": sorted(by_cat),
                         "classes": n, "cars": cars, "gain": cars * n})
        rows.sort(key=lambda r: (-r["gain"], -r["classes"], r["site"], r["make"], r["model"], r["year"]))
        return {"ns": self.ns, "as_of": self.as_of, "kind": "own_page",
                "note": "R3 input (CURATION_SPEC 3.2 R3, 5.16): vehicle-years left out of Likely candidate "
                        "classes because their own page was never read; crawl.py --complete reads those "
                        "pages and the curator re-checks them. Never shipped.",
                "unrouted_makes": dict(sorted(unrouted.items())), "rows": rows}

    # ------------------------------------------- 5.18 Phase 2 (report only)
    def phase2_cond(self, T, cat, key):
        """cond(pn, T) as a DNF over translatable atoms, or None. Notes from
        T's own page; a trim-layout row that lists every universe trim except
        the hybrid ones adds fuel=gas. Computed, never shipped (§5.18)."""
        c = self.classes[(key, cat)]
        on, notes, _src, _p, _how = self.own_page(T, cat, c)
        ctx = N.NoteContext(T[2], frozenset(m.lower() for _, m in self.t_sources.get(T, set())), self.ns_models_f)
        dnf = N.cond_dnf(N.classify(notes, ctx))
        if dnf is None:
            return None
        tu = self.trimu.get(T, frozenset())
        extra = None
        for cc, r, f, t in self.t_rows.get((T, cat), []):
            if cc is not c or f.layout != "trim":
                continue
            missing = tu - f.trim_atoms()
            if not missing:
                extra = {}
                break
            if all("hybrid" in a[0] for a in missing):
                extra = {"fuel": "gas"}
        if extra is None:
            return None
        out = []
        for d in dnf:
            if "fuel" in d and extra.get("fuel") and d["fuel"] != extra["fuel"]:
                continue
            out.append({**d, **extra})
        return out


def cond_satisfied(dnf, answers: dict) -> bool:
    """True only when some disjunct's every atom is answered and equal.
    An unanswered or unknown atom never satisfies (gives Likely)."""
    if dnf is None:
        return False
    return any(all(answers.get(k) is not None and answers.get(k) == v for k, v in d.items()) for d in dnf)


def directional_verified(seeker: dict, donor: dict) -> bool:
    """§2 Phase 2 directional test on two closed cells: seeker / donor are
    {"slots": {slot: {key: cover}}, "eligible": bool}. The donor must be
    eligible; for every slot of the seeker, the donor's candidates are a
    subset of the seeker's cover=yes members, and the donor lists every slot
    the seeker lists. The seeker need not be one chain."""
    if not donor.get("eligible") or not seeker.get("closed", True) or not donor.get("closed", True):
        return False
    ss, ds = seeker["slots"], donor["slots"]
    if not set(ds) >= set(ss):
        return False
    for slot, mem in ss.items():
        yes = {k for k, cov in mem.items() if cov == "yes"}
        if not set(ds[slot]) or not set(ds[slot]) <= yes:
            return False
    return True


# ------------------------------------------------------------------ helpers
def _row_maps(f: A.FitRow, t: MM.Target) -> bool:
    """A row maps to a trim-subset target only when its trims meet the subset
    (or when the row prints no trims: then it is a candidate, never coverage).
    A series target (model_map `series`) maps only rows whose trims match its
    series; a row with no trims does not map (fail closed)."""
    if t.series:
        if not any(re.search(p, tr, re.I) for p in t.series for tr in (f.trims or [])):
            return False
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


def _tokens(s: str) -> list:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def _has_run(hay: list, needle: list) -> bool:
    """needle is a contiguous run of hay (token lists)."""
    n = len(needle)
    return n > 0 and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


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


def _fam_engine(e, fam) -> bool:
    return isinstance(e[0], int) and e[0] == fam["engine"]["cyl"] and \
        any(abs(e[1] - L) <= 0.05 for L in fam["engine"]["liters"])


def _split_trigger(reason: str) -> bool:
    """§7.6 oem_split: option_split, or a conditional class that says the
    numbers differ by configuration (policy.SPLIT_CONDITIONS)."""
    return reason == "option_split" or (reason.startswith("conditional:")
                                        and reason.split(":", 1)[1] in policy.SPLIT_CONDITIONS)


def _cond_class(why: str) -> str:
    if why.startswith("conditional_notes:"):
        return why.split(":", 1)[1]
    return {"conditional_trims": "trim", "conditional_engines": "engine", "option_layout": "option_layout",
            "trims_unknown": "trim_unknown", "trims_unattested": "trim_unattested",
            "engines_unattested": "engine_unattested", "engines_unparsed": "engine_unparsed",
            "engines_unreliable": "engine_unreliable",
            "notes_not_own_page": "notes_not_own_page",
            "fitted_not_listed": "fitted_not_listed", "listed_not_fitted": "listed_not_fitted",
            "qualifier_phrase": "qualifier", "unverified": "unverified", "disputed": "disputed",
            "rule_drift": "rule_drift"}.get(why, why)


def _split_rank(reason: str) -> int:
    for i, p in enumerate(("option_split", "packaging", "chain_crosses_slot", "position", "slot", "no_candidates")):
        if reason.startswith(p):
            return i
    return 9


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


# What the number is, for packagings a seeker could mistake for the whole
# assembly (§5.8; hub decisions P1 door modules and T1 climate switch
# modules, ops/interchange.md). "reg?" says nothing: the name does not say.
PACK_TEXT = {"motor": "window motor only", "reg": "regulator without motor", "assy": "regulator with motor",
             "door-module": "whole door module panel with the regulator",
             "switch-module": "single switch module, not the full control panel"}
_PACK_CATS = {"window-regulator": ("motor", "reg", "assy", "door-module"),
              "climate-control": ("switch-module",)}


def _pack_text(cat: str, packaging: str) -> str:
    """Packaging words for a Likely note, only in the category they describe
    (2026-11-09 GM resample: climate-control panels with packaging 'assy'
    read 'regulator with motor'; a full control panel needs no words)."""
    return PACK_TEXT.get(packaging, "") if packaging in _PACK_CATS.get(cat, ()) else ""


_LIKELY_TAIL = "; verify the number on the part"


# words that are catalog model names somewhere but also ordinary note words
_MODEL_NAME_STOP = {"base", "sport", "limited", "classic", "touring", "sedan", "coupe", "wagon", "hybrid", "van",
                    "cab", "plus", "premium", "custom", "deluxe", "special", "standard", "turbo", "diesel", "sx",
                    "gt", "gl", "gls", "se", "le", "xle", "ex", "lx", "si", "rs", "ss", "st", "sl", "sle", "slt",
                    "ls", "lt", "ltz", "xl", "xlt", "all", "cargo", "passenger", "pickup", "chassis", "cabrio",
                    "convertible", "hatchback", "the", "and", "with", "without", "front", "rear", "left", "right"}
_BRAND_CODE_RE = re.compile(r"(?:^|[,:]\s*)[A-Z0-9*]{1,3}\s+-\s+(CHRYSLER|DODGE|JEEP|RAM|PLYMOUTH|FIAT|EAGLE)\b")


_MARKETS = (r"CANADA|CANADIAN|CHILE|EUROPE|EUROPEAN|EUR|EC|AUSTRALIA|AUSTRALIAN|AUS|JAPAN|JPN|JAPANESE|GENERAL|GEN|"
            r"MEXICO|MEXICAN|KOREA|KOREAN|TAIWAN|CHINA|CHINESE|MIDDLE\s+EAST|GCC|UK|U\.K\.|NEW\s+ZEALAND|NZ|"
            r"ASIA|AFRICA|SOUTH\s+AFRICA|LATIN\s+AMERICA|PUERTO\s+RICO|RUSSIA|ISRAEL|PHILIPPINES|THAILAND|INDONESIA")
_MARKET_RE = re.compile(r"(?:\bFOR\s+(?:" + _MARKETS + r")\b|\b(?:" + _MARKETS + r")\s*(?:SPEC|MODEL|MKT|MARKET)\b)", re.I)
_US_MARKET_RE = re.compile(r"\b(USA|U\.S\.A?\.?|US\s+SPEC|FOR\s+US|FEDERAL|CALIFORNIA|50\s*STATE)\b", re.I)


def _market_excludes(notes) -> bool:
    """Every feed car is a US car. A row whose note names only foreign
    markets ('FOR CANADA', 'FOR CANADA,CHILE', 'KOREA SPEC&...') is not
    listed for it (hub 2026-11-09: Subaru 72311AE08D). Alternatives split at
    ' / '; any alternative without a foreign market, or naming the US,
    keeps the row."""
    for n in notes or []:
        alts = [a for a in re.split(r"\s/\s", n or "") if a.strip()]
        if alts and all(_MARKET_RE.search(a) and not _US_MARKET_RE.search(a) for a in alts):
            return True
    return False


_EXPORT_RE = re.compile(r"(?<!EXC )(?<!EXC\()\bEXPORT\b", re.I)


def _export_only(notes) -> bool:
    """Hub 2026-11-09 (GM 25876716 'CK1,2(DE2,Z5X)(EXPORT)'): a row whose
    every option alternative names EXPORT is not for US feed cars, like a
    foreign-market note. Alternatives split at ', ' (GM writes 'CK1,2(...)'
    inside one). 'EXC EXPORT' keeps the row. Per row; only removes claims."""
    for n in notes or []:
        body = re.sub(r"^\s*Fitting Vehicle Options\s*:\s*", "", n or "", flags=re.I)
        alts = [a for a in re.split(r",\s+", body) if a.strip()]
        if alts and all(_EXPORT_RE.search(a) for a in alts):
            return True
    return False


def _brand_codes_exclude(notes, make: str) -> bool:
    """moparpartsgiant option column brand codes ('C - CHRYSLER, F - BRAND
    AWD'): a row naming only other brands is not for T's make."""
    named = {m.group(1).lower() for n in notes or [] for m in _BRAND_CODE_RE.finditer(n or "")}
    return bool(named) and (make or "").lower() not in named


def _split_top(text: str) -> list:
    """Split a subarupartsdeal option expression at top-level ',' and ' +'."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and (ch == "," or (ch == "+" and cur.endswith(" "))):
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    if cur.strip():
        out.append(cur.strip())
    return out


_SUBARU_OBK = re.compile(r"^(OBK|SUS|SOBK|WOBK)")          # Outback family (SUS = Outback sport-utility sedan)
_SUBARU_NONBODY = re.compile(r"^(AT|MT|\d?[AM]T|EJ\w*|EZ\w*|FB\w*|FA\w*|\d+\w*)$")   # transmission / engine codes


def _subaru_alt_models(alt: str):
    """Feed models one option alternative allows on the Legacy/Outback/Baja
    pages, or None when it names no body/model (engine, transmission, trim).
    Outback-family codes (OBK*, SUS*, SOBK, WOBK) mean the Outback in every
    generation, including the 2000-04 'Legacy Outback' years (hub
    2026-11-09: 72311AE06A '*W.OBKLTD.AT', 91031AE43BGA 'OBK6 +SUS6 ...')."""
    alt = alt.strip().lstrip("*")
    head, _, rest = alt.partition(".")
    heads = re.findall(r"[A-Z0-9#/]+", head) if head.startswith("(") else [head.strip()]
    quals = [q for q in re.findall(r"[A-Z0-9#]+", rest) if not _SUBARU_NONBODY.match(q)]
    allowed = set()
    for h in heads:
        if _SUBARU_OBK.match(h):
            allowed.add("outback")
        elif h == "P" or h.startswith("BAJA"):
            allowed.add("baja")
        elif h in ("S", "W"):
            obk = [q for q in quals if _SUBARU_OBK.match(q)]
            if quals and len(obk) == len(quals):
                allowed.add("outback")
            elif obk:
                allowed |= {"legacy", "outback"}
            else:
                allowed.add("legacy")   # S/W without Outback codes: the Legacy body
        else:
            return None
    return allowed or None


def _subaru_body_excludes(notes, model: str) -> bool:
    m = (model or "").lower()
    fam = "outback" if "outback" in m else "baja" if "baja" in m else "legacy" if "legacy" in m else None
    if fam is None:
        return False
    for n in notes or []:
        mm = re.match(r"^\s*Fitting Vehicle Options\s*:\s*(.+)$", n or "", re.I)
        if not mm:
            continue
        allowed = set()
        for alt in _split_top(mm.group(1)):
            a = _subaru_alt_models(alt)
            if a is None:
                allowed = None
                break
            allowed |= a
        if allowed is not None and fam not in allowed:
            return True
    return False


_SUBARU_MANUAL = re.compile(r"^\d?MT$")


def _subaru_manual_only(notes) -> bool:
    """§5.6 (2026-11-09 Subaru resample): a 'Fitting Vehicle Options' note
    whose every alternative requires a manual transmission (MT/5MT/6MT).
    A yard listing does not show the transmission, and some manual
    configurations were never sold in the US (2015 Legacy/Outback 6MT
    gauge clusters 85002AL06A/AL07A: Canada only). Per row, like a market
    note. Only removes claims."""
    for n in notes or []:
        mm = re.match(r"^\s*Fitting Vehicle Options\s*:\s*(.+)$", n or "", re.I)
        if not mm:
            continue
        alts = [a.strip().lstrip("*") for a in _split_top(mm.group(1)) if a.strip()]
        if alts and all(any(_SUBARU_MANUAL.match(q) for q in re.findall(r"[A-Z0-9#]+", a.partition(".")[2]))
                        for a in alts):
            return True
    return False


_PROD_RE = re.compile(r"Production Date\s*:\s*(\d{1,2})/(\d{4})\s*-\s*(?:(\d{1,2})/(\d{4}))?", re.I)
_PROD_MIN_MONTHS = 5
# wheels have their own, stricter whole-group production-date refusal
# (wheel_production_date); a per-row cut first would let a group that rule
# refuses through, so the per-row rule never adds a claim there
PROD_RULE_SKIP_CATS = frozenset({"wheels"})


def _production_excludes(notes, year: int) -> bool:
    """Production-date windows (2026-11-10, live-accuracy audit of 39 shipped
    toyota/ford groups: 29 vehicle-years credited outside the window of the
    row that lists them, e.g. Lexus IS 2007 cluster 83800-53580 'Production
    Date: 09/2005-06/2006', RX 330 2004 cluster 83800-0E011 '09/2004-02/2006').
    A row whose every window overlaps the model year, taken as 07/(year-1) -
    06/year, by fewer than 5 months is not listed for that year. An open end
    runs on. Per row. Verified against 51 independently judged vehicle-years:
    drops all 29 that do not fit, keeps 0 that do not; it also drops 16 that do
    (early-launch builds such as the 2006 GS from 01/2005, supersessions),
    accepted as losses (hub rule (a)). Only removes claims."""
    lo, hi = (year - 1) * 12 + 7, year * 12 + 6
    for n in notes or []:
        wins = _PROD_RE.findall(n or "")
        if not wins:
            continue
        ok = False
        for m1, y1, m2, y2 in wins:
            a = int(y1) * 12 + int(m1)
            b = int(y2) * 12 + int(m2) if y2 else 10 ** 9
            if min(b, hi) - max(a, lo) + 1 >= _PROD_MIN_MONTHS:
                ok = True
        if not ok:
            return True
    return False


# Lexus chassis codes (2026-11-10 live audit: lexuspartsnow rows carry the
# chassis a number is for, e.g. 'GRS19#' = V6 GS, 'MCU3#.. JPP' = RX 330, and
# curation credited them to other engines: GS 430 2006 from GRS19# headlamp rows,
# RX 350 2007 from MCU3# rows). US chassis families per feed model; a model not
# listed here is not gated.
_LEXUS_CHASSIS = {
    "GS 300": ("JZS160", "JZS161", "GRS190", "GRS195"), "GS 400": ("UZS160",),
    "GS 430": ("UZS161", "UZS190"), "GS 350": ("GRS191", "GRS196", "GRL10", "GRL15", "GRL12", "GRL16"),
    "GS 460": ("URS190",), "GS 450h": ("GWS191", "GWL10"),
    "IS 300": ("JCE10", "JCE15", "ASE30", "GSE37"), "IS 250": ("GSE20", "GSE25", "GSE30", "GSE35"),
    "IS 350": ("GSE21", "GSE26", "GSE31", "GSE36"), "IS F": ("USE20",),
    "RX 300": ("MCU10", "MCU15"), "RX 330": ("MCU33", "MCU38"),
    "RX 350": ("GSU30", "GSU31", "GSU35", "GSU36", "GGL10", "GGL15", "GGL16", "GGL25"),
    "RX 400h": ("MHU33", "MHU38"), "RX 450h": ("GYL10", "GYL15", "GYL16", "GYL25"),
    "ES 300": ("VCV10", "MCV10", "MCV20", "MCV30"), "ES 330": ("MCV31",), "ES 350": ("GSV40", "GSV60"),
    "LS 400": ("UCF10", "UCF11", "UCF20", "UCF21"), "LS 430": ("UCF30", "UCF31"),
    "LS 460": ("USF40", "USF41", "USF45", "USF46"),
    "SC 300": ("JZZ31",), "SC 400": ("UZZ30", "UZZ31"), "SC 430": ("UZZ40",),
    "GX 470": ("UZJ120",), "GX 460": ("GRJ150",), "LX 470": ("UZJ100",), "LX 570": ("URJ200",),
}
_CHASSIS_TOKEN = re.compile(r"(?<![A-Z0-9])([A-Z]{3}\d[0-9#]{0,3})(?![A-Z0-9])")


def _chassis_match(code: str, chassis: str) -> bool:
    code = code.rstrip("#")
    return chassis.startswith(code) if len(code) <= len(chassis) else code.startswith(chassis)


def _lexus_chassis_excludes(notes, T) -> bool:
    """True when a note names Lexus chassis codes and none is T's (per note;
    pooled class-wide like the Subaru body codes). Only removes claims."""
    if T[0] != "Lexus":
        return False
    fam = _LEXUS_CHASSIS.get(T[1])
    if not fam:
        return False
    for n in notes or []:
        codes = _chassis_codes(n)
        if codes and not any(_chassis_match(c, ch) for c in codes for ch in fam):
            return True
    return False


_CHASSIS_RUN = re.compile(r"(?<![A-Z0-9])([A-Z]{3})(\d[0-9#]{0,3})((?:\s*,\s*\d[0-9#]{0,3}(?![0-9#]))*)")


def _chassis_codes(note: str) -> list:
    """Lexus chassis codes in a note, with comma continuations expanded:
    'GSE20, 21.. ATM' -> GSE20, GSE21 (2026-11-10 audit: IS 350 2012 mirrors)."""
    out = []
    for pre, first, rest in _CHASSIS_RUN.findall(note or ""):
        if pre not in _LEXUS_CHASSIS_PREFIXES:
            continue
        out.append(pre + first)
        for tail in re.findall(r"\d[0-9#]{0,3}", rest):
            # '21' after 'GSE20' replaces the last len(tail) characters
            out.append((pre + first)[: len(pre + first) - len(tail)] + tail)
    return out


_LEXUS_CHASSIS_PREFIXES = frozenset(ch[:3] for fam in _LEXUS_CHASSIS.values() for ch in fam)


_DIVISION_RE = re.compile(r"\b([A-Za-z]+)\s+Division\s+Derivative\b", re.I)


def _other_division(notes, make: str) -> bool:
    """True when a note restricts the row to another make's division: Ford
    list pages print shared platform rows with 'Lincoln Division Derivative'
    / 'Mercury Division Derivative' (fordpartsgiant AH6Z-8200-ACP, an MKZ
    grille, on the 2010 Milan and 2012 Fusion pages; 1,706 such rows on
    oem-raw@42683f9). A note naming T's own make, or none, does not."""
    named = {m.group(1).lower() for n in notes or [] for m in _DIVISION_RE.finditer(n or "")}
    return bool(named) and (make or "").lower() not in named


def _likely_note(brand: str, pn: str, text: str, pack: str = "") -> str:
    """'<Brand> catalog lists #<pn> for both — [<packaging>; ]<reason>; verify
    the number on the part' (§5.16), always within NOTE_MAX_LEN: the reason
    text is cut, never the template, so V5 cannot refuse the namespace."""
    head = _sanitize(f"{brand} catalog lists #{pn} for both — ")
    mid = _sanitize(f"{pack}; {text}" if pack else text)
    room = policy.NOTE_MAX_LEN - len(head) - len(_LIKELY_TAIL)
    if len(mid) > room:
        mid = mid[:max(room - 3, 1)].rstrip(" ,;") + "..."
    return head + mid + _LIKELY_TAIL


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


def global_gates(cur: Curation) -> list:
    """Every namespace-wide reason that stands between this raw and any
    Verified group (each one alone is enough; §10.3 reports the per-cell
    first reasons)."""
    out = []
    sites = sorted(s for s in cur.nsd["sites"] if s in cur.raw_meta)
    if not cur.list_rows and not cur.years:
        out.append("no R1 list manifests and no R2 year manifests on this raw ref, so no cell can close (C1/C2); "
                   "Verified is impossible by design until the crawler writes them")
    elif not cur.list_rows:
        out.append("no R1 list manifests on this raw ref, so no cell can close (C2)")
    elif not cur.years:
        out.append("no R2 year manifests on this raw ref, so no cell can close (C1)")
    if not any(policy.category_status(s, c, cur.status_table) for s in sites for c in (cur.status_table.get(s) or {})):
        out.append("no (site, category) of this namespace has passed the audit gate (audits.json has no "
                   "record; spec 11.4, E5/V7)")
    unrel = [s for s in sites if not cur.reliable.get(s)]
    if unrel:
        out.append(f"engine cells not audited as reliable on {', '.join(unrel)}: every engine test there is maybe "
                   "(spec 4, 5.5), so none of their records can be cover yes in any category (5.10) and E7 blocks "
                   "engine categories; the completion worklist cannot rank their cells until an audit flips "
                   "ENGINE_CELLS_RELIABLE")
    for s in sites:
        rows = [f for r in cur.records if r.site == s for f in r.rows]
        if not rows:
            continue
        usable = [f for f in rows if f.layout == "trim" and not f.trims_from_options]
        share = len(usable) / len(rows)
        if share < 0.1:
            why = ("its option column holds trims (option_column_is_trims), which count only after a namespace "
                   "audit (spec 5.2)") if any(f.trims_from_options for f in rows) else \
                  "it prints an option column, and option-layout rows are never coverage (spec 5.5)"
            out.append(f"{s}: only {share:.0%} of its {len(rows)} fitment rows can be coverage: {why}")
        elif usable and sum(1 for f in usable if not f.engines) / len(usable) > 0.9:
            out.append(f"{s} prints no engine cell on most trim-layout rows: EngineU stays empty, so cover yes is "
                       "impossible there (spec 5.10) even after an engine audit; needs a spec decision")
    if cur.blocked:
        out.append(f"blocked by the crawl breaker: {', '.join(sorted(cur.blocked))} (their cells never close, C9)")
    return out


def _why_none(cur: Curation) -> str:
    return "; ".join(global_gates(cur)) or "see funnel_cars"


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
             f"- blocked sites: {', '.join(s['blocked_sites']) or 'none'}", "",
             "## Gates standing for the whole namespace", ""]
    lines += [f"- {g}" for g in s.get("gates") or []] or ["- none: see the funnel"]
    lines += ["",
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
    lines += ["", "## Contradictions with hand-curated groups (spec 7.6)", ""]
    lines += [f"- {c['trigger']}: {c['kind']} {c['id']} ({c['cat']})" for c in rep.get("contradictions") or []] \
        or ["- none (a contradiction needs an OEM-closed cell inside a hand group)"]
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


def hand_payload(js) -> dict | None:
    """The interchange payload built from hand data only (no OEM groups), for
    the §7.6 contradiction report."""
    import tempfile
    if not hasattr(js, "_oem_contradictions"):
        return None
    saved = js.OEM_GROUPS_DIR
    js.OEM_GROUPS_DIR = Path(tempfile.mkdtemp(prefix="oem_none_"))
    try:
        return js.build_interchange_payload()
    finally:
        js.OEM_GROUPS_DIR = saved


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
    hand = hand_payload(js)
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
        # §7.6, the same test the payload builder runs (it demotes; this reports)
        rep["contradictions"] = js._oem_contradictions(hand, {ns: doc}) if hand else []
        rep["validator"] = problems
        write_json(out / "_report" / f"{ns}.json", rep)
        (out / "_report" / f"{ns}.md").write_text(report_md(rep))
        write_json(out / "_report" / f"{ns}.completion.json", completion)
        write_json(out / "_report" / f"{ns}.own_page_completion.json", cur.own_page_completion(inv_counts))
        if a.propose_map:
            # §6: proposals for humans; `model_map.py merge` applies the draft
            label = f"oem-raw@{(src.commit or 'fixtures')[:7]}"
            write_json(out / "_report" / f"{ns}.map-proposals.json", {
                "ns": ns, "raw": doc["raw"]["commit"], "proposals": rep["map_proposals"],
                "draft": MM.draft_identity(ns, cur.cat_models, inv, js, mm, policy.NAMESPACES, label)})
        if problems:
            print(f"[curate] {ns}: validator refused the groups file: {problems[:3]}", file=sys.stderr)
        elif a.write_groups:
            write_json(out / f"{ns}.json", doc)
        s = rep["summary"]
        print(f"[curate] {ns}: records {s['records']} cells {s['cells']} verified {s['verified_groups']} "
              f"vg {s['vg_groups']} likely {s['likely_groups']}; {s['why_no_verified']}", file=sys.stderr)
    held = [h for ns in sorted(results) for h in getattr(results[ns], "held_exterior", [])]
    if held or any(getattr(c, "held_exterior", None) is not None for c in results.values()):
        write_json(out / "_report" / "held_exterior.json", {
            "note": "Likely groups held by the exterior cross-model rule (policy.EXTERIOR_HOLD_CATS, owner "
                    "decision 2026-11-06); not shipped. Owner checklist: each needs a visual check before release.",
            "namespaces": sorted(results), "count": len(held), "groups": held})
    coll = cross_ns_collisions(results)
    if coll:
        write_json(out / "_report" / "cross_ns_string_collisions.json", coll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
