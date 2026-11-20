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
import copy
import hashlib
import json
import re
import sys
from collections import ChainMap, Counter, defaultdict
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
    model_bodies: dict | None = None        # {(make, model): {body style}} from vPIC decodes (rear wiper gate)
    body_counts: dict | None = None         # {(make, model, year): Counter(silhouette)} (§5.16 body-variant rule)
    # {(make, model, year): {"lits": frozenset, "hybrid": bool, "gas": bool}} from the lot's
    # decoded engines (lot_engines(); round3-1119 engine-column materiality). None: no extras
    # input, every engine the catalog attests counts (fail closed: more limits)
    lot_engines: dict | None = None


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
        self.model_bodies = opts.model_bodies or {}
        self.body_counts = opts.body_counts or {}
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
            c.packaging = P.packaging(cat, self.ns, sorted(c.pns)[0], names,
                                      [n for r in c.records for n in r.note_texts] if cat == "wiper-motor" else ())
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
        # §5.16 body-variant rule: every body-named catalog page offered for T
        self.t_body_variants = defaultdict(set)
        for lr in self.list_rows:
            for T in self.targets_of_seed(lr.seed):
                self.t_body_variants[T] |= _body_words(lr.variant)
        for ym in self.years:
            for T in self.targets_of_seed(ym.seed):
                for v in [ym.variant] + list(ym.variants or []):
                    self.t_body_variants[T] |= _body_words(v)

    def body_need(self, T) -> set:
        """§5.16 body-variant rule: the bodies T comes in, from the lot (vPIC
        decodes, LIKELY_BODY_MIN_SHARE / _MIN_CARS) and from the body-named
        catalog pages offered for T."""
        need = set(self.t_body_variants.get(T, ()))
        fixed = policy.model_body_table(T[0], T[1], T[2])
        if fixed is not None:
            # policy.MODEL_BODY_TABLE (2026-11-18): the model's own line-up,
            # not the lot decodes (1998 200SX coupes decoded as sedans)
            return need | set(fixed)
        cnt = self.body_counts.get(T) or {}
        tot = sum(cnt.values())
        for b, n in cnt.items():
            if n >= policy.LIKELY_BODY_MIN_CARS and n >= policy.LIKELY_BODY_MIN_SHARE * tot:
                need.add(b)
        return need

    def body_ok(self, T, cat, c: Klass) -> bool:
        """§5.16 body-variant rule: False when T comes in 2+ bodies and T's own
        pages do not show the number for every one of them (fail closed: OEM
        Likely apps carry no body gate in the app)."""
        if not policy.LIKELY_BODY_GATE or cat in policy.LIKELY_BODY_SKIP_CATS:
            return True
        need = self.body_need(T)
        if len(need) < 2:
            return True
        ctx = N.NoteContext(T[2], frozenset(m.lower() for _, m in self.t_sources.get(T, set())),
                            getattr(self, "ns_models_f", frozenset()))
        if self.t_list_rows.get((T, cat)):
            items = [(lr.variant, lr.notes, lr.site) for lr in self.t_list_rows[(T, cat)]
                     if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched and not self.note_excludes(lr.notes, T)]
        else:
            items = [(_catalog_of(r.list_url), r.note_texts, r.site) for r in self.t_seed_records.get((T, cat), [])
                     if r.key == c.key and not self.note_excludes(r.note_texts, T)]
        # does any row on T's pages in this category name a body? (then an
        # unparsed clause may be a body split and keeps restricting). The
        # product page's fitment trims for T may also split by body ("4 DOOR"
        # only for a Cobalt regulator whose own row reads "FRONT SIDE DOOR
        # WINDOW(MANUAL)"): then the clause keeps restricting too.
        if self.t_list_rows.get((T, cat)):
            page_body = any(_row_names_body(lr.notes, lr.site) for lr in self.t_list_rows[(T, cat)])
        else:
            page_body = any(_row_names_body(r.note_texts, r.site) for r in self.t_seed_records.get((T, cat), []))
        if not page_body and not self.fit_bodies_plausible(T, cat, c, need):
            page_body = True
        covered = set()
        for variant, notes, site in items:
            vb = _body_words(variant)
            rc = _row_body_cover(notes, ctx, site, page_body)
            if vb:
                covered |= vb if rc is None else (vb & rc)
            else:
                covered |= need if rc is None else rc
        return need <= covered

    def fit_bodies_plausible(self, T, cat, c: Klass, need) -> bool:
        """False when the product page's fitment trims for T name bodies or
        door counts (gmpartsgiant '4 DOOR', '2 DOOR, CONVERTIBLE') that leave a
        body of `need` out; True when they carry no body information. Used
        only to keep a clause restricting (never to add a body)."""
        words, doors, info = set(), set(), False
        for (cc, r, f, t) in getattr(self, "t_rows", {}).get((T, cat), []):
            if cc is not c or f.layout != "trim":
                continue
            for tr in f.trims or []:
                w = _body_words(tr)
                d = {int(x) for x in _DOOR_RE.findall(tr)}
                words |= w
                doors |= d
                info = info or bool(w or d)
        if not info:
            return True
        for b in need:
            if b in words:
                continue
            ok = _BODY_DOORS.get(b)
            if ok is not None and not (doors & ok):
                return False
        return True

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
        if self.ns == "nissan" and market and _infiniti_engine_excludes(notes, T):
            return True
        if self.ns == "nissan" and market and _nissan_body_code_excludes(notes, self.body_need(T)):
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
        if cat == "wiper-motor" and c.packaging == "linkage":
            # Ford "Linkage Assy - Wiper": a linkage, not a motor
            return P.Resolution((), "out_of_category", res.side, res.door)
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
                if cat in _ONE_PACK_CATS:
                    packs = {members[k]["klass"].packaging for k in keys}
                    if "module" in packs:
                        reasons.append("packaging_unstated")
                    elif len(packs) > 1:
                        reasons.append("packaging_split")
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
        self.likely_body_mixed = Counter()        # cat -> vehicle-years left out by the §5.16 body-variant rule
        self.likely_engine_conflict = Counter()   # cat -> Infiniti vehicle-years whose fitment rows name other engines
        self.likely_drive_dropped = Counter()     # cat -> vehicle-years left out by the §5.16 drive rule (ambiguous)
        self.likely_drive_noted = Counter()       # cat -> groups whose note names a drive limit
        self.likely_drive_single = Counter()      # cat -> vehicle-years whose limit is dropped: one drive only
        self.likely_generation_cut = Counter()     # cat -> vehicle-years cut at a generation break  # cat -> vehicle-years a class-wide note restricts away
        self.likely_fit_hybrid_dropped = Counter()   # cat -> Hybrid-named vehicle-years on a gas-only engine column
        self.likely_fit_engine_dropped = Counter()   # cat -> vehicle-years whose engine column names none of T's engines
        self.likely_ambiguous_feed_dropped = Counter()   # cat -> vehicle-years of a two-model feed year (Rogue 2014-15)
        # round4-1119 (hub decisions 1-3)
        self.likely_window_dropped = Counter()    # cat -> vehicle-years another page's window leaves out (decision 3)
        self.likely_window_gated = Counter()      # cat -> vehicle-years kept with a build window (decision 2)
        self.likely_window_edge = Counter()       # cat -> of those, 1-2 months at a model-year edge
        self.likely_window_note_cap = Counter()   # cat -> vehicle-years left out: the window's note would pass the cap
        self.likely_drive_sibling = Counter()     # cat -> vehicle-years limited by a same-option drive sibling
        self.likely_drive_sibling_dropped = Counter()   # cat -> vehicle-years whose siblings contradict
        # round5b-1119: vehicle-years a starred configuration decides (STARRED_SCOPE_NS)
        self.likely_starred_scope = Counter()
        self.starred_held = []
        # round6-1119: (reason, cat) -> vehicle-years held; their list
        self.likely_round6_held = Counter()
        self.round6_held = []
        self.round7_held = []       # round7-1119 decision 4: cross-position groups
        self.round8_rows = []       # round8-1119: vehicle-years held, one row each
        self.release_allow = policy.release_allowlist()   # §5.16 exact owner-approved releases
        self.release_notes = policy.release_notes()
        self.released_exterior = []
        self.round9_rows, self.round9_names = [], []
        self.round10_rows = []
        self.round11_rows = []
        brand0 = brand
        for (key, cat), c in sorted(self.classes.items()):
            if self.kinds.get(cat) != "body" or cat in policy.PHASE3_CATS:
                continue
            if not c.verified or "universal_part_suspect" in c.problems:
                continue
            # round9-1119 C: the site the pages came from names the catalog
            brand = self._group_brand(c, brand0) if self.ns in ROUND9_NS else brand0
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
                # T's own-page notes join the class-wide pool even when the
                # body rule leaves T out: the pool may only restrict more
                class_notes += notes
                if not self.body_ok(T, cat, c):
                    # §5.16 body-variant rule: T comes in bodies its own pages
                    # do not show the number for (only removes claims)
                    self.likely_body_mixed[cat] += 1
                    continue
                if self.ns == "nissan" and _infiniti_fitment_engine_conflict(c, T):
                    # the product page ties the number to another engine than
                    # the Infiniti model T ever had (only removes claims)
                    self.likely_engine_conflict[cat] += 1
                    continue
                cand.append((T, m))
            if cand and _kmh_part(c, class_notes):
                # round3-1119: a km/h (Canada) cluster is no US car's part
                self.refuse("held_market_kph", cat=cat, pn=sorted(c.pns)[0],
                            evidence=[r.pointer for r in c.records], detail="km/h-first unit")
                continue
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
            slot_T = {}             # round7-1119 decision 4: the number's position per vehicle-year
            for T, m in cand:
                if self.note_excludes(class_notes, T, market=False):
                    self.likely_note_restricted[cat] += 1
                    continue
                Ts.append(T)
                whys |= set(m["why"])
                slots |= set(m["slot"].slots)
                if m["slot"].reason is None:            # a known position (not missing / conflicting)
                    slot_T[T] = frozenset(m["slot"].slots)
            Ts = self._drop_catchall_twins(Ts)
            if len({(T[0], T[1]) for T in Ts}) < 2:
                continue        # single-model: the same-model generation loop covers it
            Ts2 = self._generation_cut(c, Ts)
            if Ts2 != Ts:
                self.likely_generation_cut[cat] += len(Ts) - len(Ts2)
                Ts = Ts2
                if len({(T[0], T[1]) for T in Ts}) < 2:
                    continue
            drive_by_T = {}
            if policy.LIKELY_DRIVE_RULE:
                # §5.16 drive rule: a vehicle-year limited to one drive family is
                # named in the note; ambiguous drive evidence leaves it out
                for T in Ts:
                    d = self.drive_of(c, cat, T)
                    if d and d != DRIVE_AMBIGUOUS:
                        # hub 2026-11-18: no limit where the model-year comes
                        # in one drive family only (catalog structure, else
                        # policy.SINGLE_DRIVE_TABLE)
                        mat = self.drive_material(T, d)
                        if mat is False:
                            self.likely_drive_single[cat] += 1
                            d = None
                        elif mat == DRIVE_AMBIGUOUS:
                            d = DRIVE_AMBIGUOUS
                    if d == DRIVE_AMBIGUOUS:
                        self.likely_drive_dropped[cat] += 1
                        continue
                    drive_by_T[T] = d
                if len(drive_by_T) != len(Ts):
                    Ts = [T for T in Ts if T in drive_by_T]
                    if len({(T[0], T[1]) for T in Ts}) < 2:
                        continue
            # round3-1119: a feed name that says Hybrid on a number whose engine
            # column prints gas engines only, and a feed model-year that also
            # holds another catalog model (policy.AMBIGUOUS_FEED_YEARS: 2014-15
            # "Rogue" = Rogue Select too) where that model's pages do not list
            # the number, leave the vehicle-year out
            keep = []
            for T in Ts:
                if re.search(r"hybrid", T[1], re.I) and self.fit_engine_limit(c, cat, T)[1] == "gas":
                    self.likely_fit_hybrid_dropped[cat] += 1
                    continue
                if self.fit_engine_conflict(c, cat, T):
                    # the engine column names none of T's engines (Q40 2015 '2.5L')
                    self.likely_fit_engine_dropped[cat] += 1
                    continue
                alt = policy.ambiguous_feed_alt(T[0], T[1], T[2])
                if alt and not self._listed_on_seed(c, cat, (T[0], alt, T[2])):
                    self.likely_ambiguous_feed_dropped[cat] += 1
                    continue
                keep.append(T)
            if len(keep) != len(Ts):
                Ts = keep
                drive_by_T = {T: d for T, d in drive_by_T.items() if T in set(Ts)}
                if len({(T[0], T[1]) for T in Ts}) < 2:
                    continue
            # round4-1119, hub decisions 1-3 (2026-11-19): another model-year
            # page's window that leaves T out (3); a same-option drive sibling
            # that limits T's drive (1); a build window inside T's model year
            # whose other builds carry an unlinked number (2). Only narrows.
            # the vehicle-years and drive limits round 3 would have used: a group
            # it refuses stays refused (round4 only narrows; no group comes back
            # because a vehicle-year whose words were too long left)
            Ts_r3, drive_r3 = list(Ts), dict(drive_by_T)
            win_by_T, sib_T, dnot_by_T, keep = {}, {}, {}, []
            # round6-1119: the round-5b reading of the windows beside the new
            # one (no narrowing, no_other_row ungated): the note cap below runs
            # on both and the group keeps only what both keep (only narrows)
            win_old, keep_old = {}, []
            win_6, keep_6 = {}, []          # round7-1119: the round-6 reading too
            keep7, pre8 = [], {}            # round8-1119: the round-7 reading; vehicle-years held before the cap
            for T in Ts:
                w = self.build_window(c, cat, T)
                self._r7 = False
                w6 = self.build_window(c, cat, T)
                self._r6_narrow = False
                w_old = self.build_window(c, cat, T)
                self._r6_narrow, self._r7 = True, True
                if (w and w["kind"] == "drop") and (w_old and w_old["kind"] == "drop") and \
                        (w6 and w6["kind"] == "drop"):
                    self.likely_window_dropped[cat] += 1
                    continue
                sl = self.drive_sibling_limit(c, cat, T) if policy.LIKELY_DRIVE_RULE else None
                if sl and sl[0] == "drive":
                    mat = self.drive_material(T, sl[1])
                    if mat is False:
                        sl = None           # built in one drive only (policy.SINGLE_DRIVE_TABLE)
                    elif mat == DRIVE_AMBIGUOUS:
                        sl = (DRIVE_AMBIGUOUS, None)
                if sl and sl[0] == DRIVE_AMBIGUOUS:
                    self.likely_drive_sibling_dropped[cat] += 1
                    continue
                if sl:
                    d = drive_by_T.get(T)
                    if sl[0] == "drive":
                        fam = _FOUR if set(sl[1]) <= _FOUR else _TWO
                        if d and not set(d) <= fam:
                            self.likely_drive_sibling_dropped[cat] += 1
                            continue        # the row's own drive and the siblings disagree
                        if not d:
                            drive_by_T[T] = frozenset(sl[1])
                            # the sibling's own drive words (round5: basis "sibling")
                            sib_T[T] = frozenset().union(*[h[2] for h in self.drive_sibling(c, cat, T)[1]])
                    elif d:
                        d2 = frozenset(set(d) - set(sl[1]))
                        if not d2:
                            self.likely_drive_sibling_dropped[cat] += 1
                            continue
                        drive_by_T[T] = d2
                    else:
                        dnot_by_T[T] = frozenset(sl[1])
                    self.likely_drive_sibling[cat] += 1
                # round5-1119 (hub decision 1): a window split with the number's own
                # predecessor or successor is a window like any other.
                # round6-1119 (hub decision 4): so is a window no other row
                # carries the rest of (launch, end of production, a gap): every
                # window that starts or ends inside the model-year span is gated,
                # or its vehicle-year leaves at the note cap below
                if not (w_old and w_old["kind"] == "drop"):
                    keep_old.append(T)
                    if w_old and w_old["kind"] in ("unlinked", "no_page", "linked"):
                        win_old[T] = w_old
                if not (w6 and w6["kind"] == "drop"):
                    keep_6.append(T)
                    if w6 and w6["kind"] in ROUND6_WINDOW_KINDS:
                        win_6[T] = w6
                if w and w["kind"] == "drop":
                    self.likely_window_dropped[cat] += 1
                    if self.ns in ROUND8_NS and w.get("src") == "other_page":
                        pre8[T] = ("held_window_other_page", {"window": _win_label(w["wins"]), "kind": "drop"})
                    continue
                if w and w["kind"] in ROUND7_WINDOW_KINDS:
                    win_by_T[T] = w
                keep7.append(T)
                r8 = self._round8_pre(c, cat, T, w) if self.ns in ROUND8_NS else None
                if r8:
                    pre8[T] = r8
                    continue
                keep.append(T)
            for T, (r8, d8) in pre8.items():
                self.round8_rows.append({"cat": cat, "pn": sorted(c.pns), "t": list(T), "reason": r8, **d8})
                self.likely_round6_held[(r8, cat)] += 1
            if len(keep) != len(Ts):
                Ts = keep
                drive_by_T = {T: d for T, d in drive_by_T.items() if T in set(keep_old) | set(keep_6)}
                if len({(T[0], T[1]) for T in Ts}) < 2:
                    if pre8 and len({(T[0], T[1]) for T in keep7}) >= 2:
                        code = "held_no_own_page" if any(v[0] == "held_no_own_page" for v in pre8.values()) \
                            else "held_window_other_page"
                        self.refuse(code, cat=cat, pn=sorted(c.pns)[0], evidence=[r.pointer for r in c.records],
                                    detail="; ".join(f"{T[1]} {T[2]} {v[0]}" for T, v in sorted(pre8.items()))[:400])
                    continue
            if cat in policy.STRICT_NOTE_CATS:
                why_s = self._strict_refusal(c, cat, [(T, m) for T, m in cand if T in set(Ts_r3)], slots)
                if why_s:
                    self.refuse(why_s[0], cat=cat, pn=sorted(c.pns)[0],
                                evidence=[r.pointer for r in c.records], detail=why_s[1])
                    continue
            reason, text = _likely_reason(whys)
            text = policy.GROUP_NOTES.get((self.ns, cat, sorted(c.pns)[0]), text)
            slot = "+".join(sorted(slots)) or "C"
            # round4-1119 (hub decision 2): a build window whose words take the
            # note past the cap leaves that vehicle-year out (never cut), one at
            # a time, the longest label first; other limits refuse as before
            def cap_loop(Ts_l, win, record):
                # the round-3 test reads the round-3 words (round8: not the
                # 'checked on gas-model pages' phrase, which the loop below fits)
                self._gas_note_off = True
                lim_l = self._likely_limits(c, cat, Ts_r3, slots, drive_r3, set(), {}, {}, text, brand)
                self._gas_note_off = False
                while lim_l["status"] == "ok" or lim_l.get("retry"):
                    lim_l = self._likely_limits(c, cat, Ts_l, slots, drive_by_T, sib_T, dnot_by_T, win, text, brand)
                    wTs = [T for T in Ts_l if T in win]
                    gTs = [T for T in Ts_l if T in set(lim_l.get("gas") or ())]
                    if lim_l["status"] != "held_drive_qualifier":
                        break
                    if wTs and self._likely_limits(c, cat, Ts_l, slots, drive_by_T, sib_T, dnot_by_T, {}, text,
                                                   brand)["status"] == "ok":
                        drop = max(wTs, key=lambda T: (len(lim_l["labels"].get(T, "")), T))
                    else:
                        # round8-1119 decision 5: the 'checked on gas-model pages'
                        # words do not fit: a gas-checked year leaves, not the group
                        self._gas_note_off = True
                        fits = gTs and self._likely_limits(c, cat, Ts_l, slots, drive_by_T, sib_T, dnot_by_T, win,
                                                           text, brand)["status"] == "ok"
                        self._gas_note_off = False
                        if not fits:
                            break           # not the window's or the gas words: refused as before
                        drop = max(gTs)
                    Ts_l = [T for T in Ts_l if T != drop]
                    if record:
                        self.likely_window_note_cap[cat] += 1
                    if len({(T[0], T[1]) for T in Ts_l}) < 2:
                        if record:
                            self.refuse("held_window_note_cap", cat=cat, pn=sorted(c.pns)[0],
                                        evidence=[r.pointer for r in c.records], detail=lim_l["detail"])
                        lim_l = {"status": "skip"}
                        break
                    lim_l["retry"] = True
                return lim_l, Ts_l
            # round6-1119: the round-5b reading first; a group it refuses stays
            # refused (as round 5b refused it), and the new reading keeps only
            # vehicle-years the round-5b reading keeps: a stricter window note
            # cap that drops another year brings nothing round 5b dropped back
            lim_old, Ts_old = cap_loop(list(keep_old), win_old, False)
            lim_6, Ts_6 = cap_loop(list(keep_6), win_6, False) if lim_old["status"] == "ok" else (lim_old, [])
            lim_7, Ts_7 = cap_loop(list(keep7), win_by_T, False) if pre8 and lim_6["status"] == "ok" \
                else (lim_6, list(keep7))
            if lim_old["status"] != "ok":
                lim, Ts = cap_loop(list(keep_old), win_old, True)
            elif lim_6["status"] != "ok":
                lim, Ts = cap_loop(list(keep_6), win_6, True)     # refused as round 6 refused it
            elif lim_7["status"] != "ok":
                lim, Ts = cap_loop(list(keep7), win_by_T, True)   # refused as round 7 refused it
            else:
                lim, Ts = cap_loop(Ts, win_by_T, True)
                both = set(Ts_old) & set(Ts_6) & set(Ts_7)
                if lim["status"] == "ok" and [T for T in Ts if T not in both]:
                    self.likely_round6_held[("earlier_cap_kept_out", cat)] += sum(T not in both for T in Ts)
                    Ts = [T for T in Ts if T in both]
                    if len({(T[0], T[1]) for T in Ts}) < 2:
                        self.refuse("held_window_note_cap", cat=cat, pn=sorted(c.pns)[0],
                                    evidence=[r.pointer for r in c.records], detail="as round 5b")
                        continue
                    lim = self._likely_limits(c, cat, Ts, slots, drive_by_T, sib_T, dnot_by_T, win_by_T, text, brand)
            if lim["status"] == "skip":
                continue
            if lim["status"] in ("held_engine_conflict", "held_fuel_conflict"):
                T = lim["T"]
                self.refuse(lim["status"], cat=cat, pn=sorted(c.pns)[0], evidence=[r.pointer for r in c.records],
                            detail=f"{T[0]} {T[1]} {T[2]}: " + ("engine limit excludes the model's only engine"
                                                              if lim["status"] == "held_engine_conflict" else
                                                              "hybrid feed name, gas page only"))
                continue
            if lim["drv"]:
                self.likely_drive_noted[cat] += 1
            if lim["status"] != "ok":
                self.refuse(lim["status"], cat=cat, pn=sorted(c.pns)[0],
                            evidence=[r.pointer for r in c.records], detail=lim["detail"])
                continue
            base_text = text
            text, drv, gate_by_T = lim["text"], lim["drv"], lim["gates"]
            for T in Ts:
                if T in win_by_T:
                    self.likely_window_gated[cat] += 1
                    self.likely_window_edge[cat] += bool(win_by_T[T].get("edge"))
            pns = sorted(c.pns)
            apps = _runs(Ts)
            if (self.ns, cat, pns[0]) in policy.GROUP_HOLDS:
                # per-group hold with a cited outside basis (hub, after a §11.4 verdict)
                self.refuse("held_group_audit", cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                            detail=policy.GROUP_HOLDS[(self.ns, cat, pns[0])][:200])
                continue
            rkey = (self.ns, cat, tuple(pns), tuple(tuple(a) for a in apps))
            released = rkey in self.release_allow
            if released and rkey in self.release_notes:
                text = self.release_notes[rkey]     # the split its source states (hub 2026-11-09)
                if drv:
                    text = f"{text}; {drv}"         # §5.16 drive rule: the limit is never dropped
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
                                           "note": _likely_note(brand, pns[0], text,
                                                                _pack_text(cat, self._note_pack(c, cat))),
                                           "reason": reason, "urls": urls})
                continue
            if cat == "wheels":
                why_w = self.wheel_group_refusal(Ts, cat, c)
                if why_w:
                    self.refuse(why_w[0], cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail=why_w[1])
                    continue
            # round5b / round6-1119: vehicle-years held on the catalog's own
            # words. Read on the group round 5 ships, after every hold that
            # depends on its vehicle-years (exterior cross-model, wheels, a
            # release), so it only narrows: nothing held or left out comes back.
            #   held_cab_inferred  a cab gate the number's own row does not carry (6/1)
            #   held_starred_only  listed for T only through starred clauses (6/2)
            #   held_starred_scope a starred clause decides drive or engine (5b)
            #   held_option_tie    a transmission tie the gates do not enforce (6/5)
            # round7-1119 (hub decision 4): a number that sits in another door
            # or position on another model of the group (80730-89915: rear
            # right on the Murano pages, front right on the Versa pages) is
            # held whole until the note can name the donor's door
            pos = defaultdict(set)
            for T in Ts:
                pos[(T[0], T[1])] |= set(slot_T.get(T, ()))
            if len({frozenset(v) for v in pos.values() if v}) > 1:
                self.likely_round6_held[("held_cross_position", cat)] += len(Ts)
                self.round7_held.append({
                    "cat": cat, "pn": pns, "unit": "group", "reason": "held_cross_position",
                    "reason_text": "the number sits in another door or position on another model; the note names "
                                   "no door", "apps": apps,
                    "positions": {f"{mk} {md}": sorted(v) for (mk, md), v in sorted(pos.items())}})
                self.refuse("held_cross_position", cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                            detail="; ".join(f"{md}: {'+'.join(sorted(v))}" for (_mk, md), v in sorted(pos.items())))
                continue
            held, why6 = {}, {}
            for T in Ts:
                g = gate_by_T.get(T, {})
                rs = []
                if g.get("cab") and not self.cab_stated(c, cat, T, g["cab"]):
                    rs.append(("held_cab_inferred", {"cab": g["cab"]}))
                if self.ns in STARRED_SCOPE_NS:
                    if self._own_starred_only(c, cat, T):
                        rs.append(("held_starred_only", {}))
                    sc = self.starred_scope(c, cat, T, slots, gas_only=(g.get("fuel") == "gas"))
                    if sc:
                        held[T] = sc
                tie = self.option_tie(c, cat, T, g)
                if tie:
                    rs.append(("held_option_tie", tie))
                if self.ns in ROUND8_NS:
                    us = self.undated_siblings(c, cat, T)
                    if us:
                        rs.append(("held_undated_siblings", {"siblings": us}))
                    pl = self.plus_dependent(c, cat, T, slots, gas_only=(g.get("fuel") == "gas"))
                    if pl:
                        rs.append(("held_plus_reading", pl))
                if self.ns in ROUND9_NS:
                    for r9, d9 in self.round9_tests(c, cat, T, g):
                        rs.append((r9, d9))
                if rs:
                    why6[T] = rs
            if held or why6:
                Ts0 = list(Ts)
                Ts = [T for T in Ts if T not in held and T not in why6]
                self.likely_starred_scope[cat] += len(held)
                for T, rs in why6.items():
                    for r6, _d in rs:
                        self.likely_round6_held[(r6, cat)] += 1
                unit, lim2 = "group", None
                why_g = "release of the exact apps" if released else "fewer than two models left"
                if not released and len({(T[0], T[1]) for T in Ts}) >= 2:
                    lim2 = self._likely_limits(c, cat, Ts, slots, drive_by_T, sib_T, dnot_by_T, win_by_T,
                                               base_text, brand)
                    if lim2["status"] == "ok" and not (cat == "wheels" and self.wheel_group_refusal(Ts, cat, c)):
                        unit = "vehicle-year"
                    else:
                        why_g = f"the rest no longer passes ({lim2['status']})"
                self._unit_why = None if unit == "vehicle-year" else why_g
                star_T = {T: sc for T, sc in held.items()}
                only_T = {T for T, rs in why6.items() if any(r6 == "held_starred_only" for r6, _d in rs)}
                if star_T or only_T:
                    self.starred_held.append(self._starred_entry(c, cat, Ts0, star_T, unit, only_T, kept=Ts))
                for T, rs in why6.items():
                    for r6, d6 in rs:
                        if r6 in ("held_undated_siblings", "held_plus_reading"):
                            self.round8_rows.append({"cat": cat, "pn": pns, "t": list(T), "reason": r6, **d6})
                        if r6 in ("held_variant_unread", "held_twin_changeover", "held_body_mark", "held_drive_open"):
                            self.round9_rows.append({"cat": cat, "pn": pns, "t": list(T), "reason": r6, **d6})
                r6_T = {T: [x for x in rs if x[0] in ("held_cab_inferred", "held_option_tie")]
                        for T, rs in why6.items()}
                r6_T = {T: rs for T, rs in r6_T.items() if rs}
                if r6_T:
                    self.round6_held.append(self._round6_entry(c, cat, Ts0, r6_T, Ts, unit, slots))
                if unit == "group":
                    # fewer than two models left, the rest's note no longer
                    # fits, or an owner release of the exact apps: held whole
                    reasons = {r6 for rs in why6.values() for r6, _d in rs} | ({"held_starred_scope"} if held else set())
                    code = next(r for r in ("held_cab_inferred", "held_starred_only", "held_starred_scope",
                                            "held_option_tie", "held_undated_siblings", "held_plus_reading",
                                            "held_variant_unread", "held_twin_changeover", "held_body_mark",
                                            "held_drive_open")
                                if r in reasons)
                    self.refuse(code, cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail="; ".join(
                                    f"{T[0]} {T[1]} {T[2]} " + "/".join(sorted(
                                        {r6 for r6, _d in why6.get(T, [])} |
                                        ({"held_starred_scope"} if T in held else set())))
                                    for T in sorted(set(held) | set(why6)))[:400])
                    continue
                text, drv, gate_by_T = lim2["text"], lim2["drv"], lim2["gates"]
                apps = _runs(Ts)
            slot = "+".join(sorted(slots)) or "C"
            if self.ns in ROUND10B_NS and self.ns not in ROUND10_NS and cat == "window-regulator":
                dis = self._name_disagree(c, cat)
                if dis:
                    why = "the names disagree in kind (" + "/".join(dis["kinds"]) + ")"
                    self.refuse("held_name_disagree", cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail=why)
                    self.round10_rows.append({"cat": cat, "pn": pns, "class": None, "change": "held",
                                              "reason": "held_name_disagree", "detail": why,
                                              "names_all_fields": dis["names"]})
                    continue
            if self.ns in ROUND9_NS:
                # round9-1119 A: the number's catalog part name decides the
                # note's words; a name the rule cannot place holds the group
                nm = self._name_class(c, cat)
                if nm["hold"]:
                    self.refuse("held_part_name", cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail=nm["hold"])
                    self.round9_rows.append({"cat": cat, "pn": pns, "reason": "held_part_name", "unit": "group",
                                             "detail": nm["hold"], "names": nm["names"]})
                    continue
            note = _likely_note(brand, pns[0], text, _pack_text(cat, self._note_pack(c, cat), slot))
            if self.ns in ROUND10_NS and cat == "window-regulator":
                r10 = self._r10_class(c, cat)
                pack0 = _pack_text(cat, self._note_pack(c, cat), slot)
                row = {"cat": cat, "pn": pns, "class": r10["class"], "names": r10["names"], "old_note": note}
                why10 = None
                dis = self._name_disagree(c, cat)
                row["names_all_fields"] = [{"field": f, "name": n, "ref": p_, "kind": _kind10b(n) or None}
                                           for f, n, p_ in self._wide_names(c, cat)]
                if dis:
                    why10 = ("held_name_disagree", "the names disagree in kind (" + "/".join(dis["kinds"]) + ")")
                elif r10["class"] not in ("motor", "regulator"):
                    why10 = ("held_part_name", r10["hold"])
                elif r10["class"] == "motor" and pack0 != PACK_TEXT["motor"]:
                    if pack0:
                        why10 = ("held_part_name", f"motor name, packaging words '{pack0}'")
                    elif not _likely_note_fits(brand, pns[0], text, PACK_TEXT["motor"]):
                        why10 = ("held_motor_words_cap", "'window motor only' takes the note past "
                                                         f"{policy.NOTE_MAX_LEN} characters")
                    else:
                        note = _likely_note(brand, pns[0], text, PACK_TEXT["motor"])
                        self.round10_rows.append(dict(row, change="phrase", new_note=note))
                if why10:
                    self.refuse(why10[0], cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                detail=why10[1][:200])
                    self.round10_rows.append(dict(row, change="held", reason=why10[0], detail=why10[1]))
                    continue
            if self.ns in ROUND11_NS and cat in ("bumper-front", "bumper-rear", "tail-lights", "window-regulator"):
                r11 = self._r11_words(c, cat, note, slot)
                if r11:
                    row = {"cat": cat, "pn": pns, "kinds": r11["kinds"], "names": r11["names"], "old_note": note}
                    why11 = r11.get("hold")
                    if not why11 and r11.get("phrase"):
                        if not _likely_note_fits(brand, pns[0], text, r11["phrase"]):
                            why11 = ("held_words_cap", f"'{r11['phrase']}' takes the note past "
                                                       f"{policy.NOTE_MAX_LEN} characters")
                        else:
                            note = _likely_note(brand, pns[0], text, r11["phrase"])
                            self.round11_rows.append(dict(row, change="phrase", phrase=r11["phrase"],
                                                          new_note=note, pages_reinforcement=r11.get("reinf")))
                    if why11:
                        self.refuse(why11[0], cat=cat, pn=pns[0], evidence=[r.pointer for r in c.records],
                                    detail=why11[1][:200])
                        self.round11_rows.append(dict(row, change="held", reason=why11[0], detail=why11[1]))
                        continue
            if self.ns in ROUND9_NS:
                nm = self._name_class(c, cat)
                self.round9_names.append({"cat": cat, "pn": pns, "class": nm["class"], "names": nm["names"],
                                          "phrase": _pack_text(cat, self._note_pack(c, cat), slot) or None,
                                          "label": f"{brand} catalog", "note": note})
            # its own evidence date: build-time expiry drops a Likely group
            # whose oldest record passes 120 days (review F18)
            stamps = sorted(r.retrieved for r in c.records if _ts(r.retrieved))
            gates = _gate_runs(gate_by_T)
            out.append({"id": f"oem:{self.ns}:{cat}:{slot}:{_sha1([pns, apps])[:10]}", "cat": cat,
                        "tier": "likely", "kind": "body", "apps": apps, "pn": pns, "reason": reason,
                        "note": note, "keys": [key], "cars": sum(self.inv_counts.get(T, 0) for T in Ts),
                        "oldest_retrieved": stamps[0] if stamps else None,
                        **({"label": f"{brand} catalog"} if self.ns in ROUND9_NS else {}),
                        **({"gates": gates} if gates else {})})
        self._likely_out = out
        return out

    def _likely_limits(self, c, cat, Ts, slots, drive_by_T, sib_T, dnot_by_T, win_by_T, text, brand) -> dict:
        """§5.16 limits of a Likely group's vehicle-years, their note text and
        gates (moved out of likely_groups in round4-1119 so a build window
        that takes the note past the cap can leave its vehicle-year out and
        the rest be tried again). status 'ok' | 'held_cab_qualifier' |
        'held_drive_qualifier' | 'held_engine_conflict' | 'held_fuel_conflict'."""
        slot = "+".join(sorted(slots)) or "C"
        pack = _pack_text(cat, self._note_pack(c, cat), slot)
        cab_map = self._cab_only_map(c, cat, Ts)
        cab = "; ".join(f"{md}: {cb} only" for (_mk, md), cb in cab_map.items())
        # round3-1119: cab / body lists the page splits by number, per
        # model-year (labels and gates below; a model already limited to
        # one cab by _cab_only_map keeps that)
        cab_list_T = {T: v for T, v in self._cab_list_by_T(c, cat, Ts, slots).items()
                      if not cab_map.get((T[0], T[1]))}
        body_list_T = self._body_list_by_T(c, cat, Ts, slots)
        # a model whose every vehicle-year carries the same list is named
        # once ("Frontier: king cab/crew cab only"); otherwise per year
        cab_model, body_model = {}, {}
        for lst_T, out_m in ((cab_list_T, cab_model), (body_list_T, body_model)):
            for mk, md in sorted({(T[0], T[1]) for T in Ts}):
                vals = [tuple(lst_T[T]) if T in lst_T else None for T in Ts if (T[0], T[1]) == (mk, md)]
                if vals and vals[0] is not None and all(v == vals[0] for v in vals):
                    out_m[(mk, md)] = list(vals[0])
        extra = [f"{md}: {'/'.join(v)} only" for (_mk, md), v in sorted(cab_model.items())] + \
                [f"{md}: {' or '.join(v)} only" for (_mk, md), v in sorted(body_model.items())]
        if extra:
            cab = "; ".join(x for x in [cab] + extra if x)
        # §5.16 limits per vehicle-year: rear-door crew cab, drive, engine,
        # transmission, fuel (2026-11-18); ambiguous fuel leaves T out.
        # The same limits become the vehicle-year's gate (gates-1118): the
        # app hides a donor whose own decode or listing contradicts one.
        label_by_T, gate_by_T, unchecked_by_T = {}, {}, {}
        gas_checked = set()     # round8-1119 decision 5: gas pages read, the hybrid's never
        for T in Ts:
            labs, gate = [], {}
            rc = self.rear_cab_of(c, cat, T, slots)
            if rc and f"{T[1]}: crew cab only" not in cab:
                labs.append(rc)
            if cab_map.get((T[0], T[1])) or rc:
                gate["cab"] = _cab_gate(cab_map.get((T[0], T[1])) or rc)
            elif cab_list_T.get(T):
                cl = cab_list_T[T]
                if (T[0], T[1]) not in cab_model:
                    labs.append("/".join(cl))
                gate["cab"] = _cab_gate(cl[0]) if len(cl) == 1 else [_cab_gate(x) for x in cl]
            if body_list_T.get(T):
                b = body_list_T[T]
                if (T[0], T[1]) not in body_model:
                    labs.append(" or ".join(b))
                gate["body"] = b[0] if len(b) == 1 else list(b)
            if drive_by_T.get(T):
                d = drive_by_T[T]
                # a limit read from a same-option drive sibling (round4) is the
                # catalog's own words about ANOTHER number: basis "sibling"
                # (round5-1119, hub decision 4: "stated" only when the
                # number's own row names the drive), with the sibling's drive
                basis = "sibling" if T in sib_T else self.drive_basis(c, cat, T, d)
                # round3-1119 item 4: "4WD" beside an All-Mode "AUTO" number
                pt = set(d) == {"4wd"} and self._auto_sibling(c, cat, T, slots)
                lab = "part-time 4WD" if pt else _drive_label(d)
                if basis in ("stated", "sibling"):
                    labs.append(lab)
                else:
                    # hub 2026-11-18: same gate, honest words (checked drive only)
                    unchecked_by_T[T] = lab
                gate["drive"] = _drive_gate(d)
                gate["drive_basis"] = basis
                if basis == "sibling" and sib_T.get(T):
                    gate["drive_sib"] = _drive_gate(sib_T[T])
                if pt:
                    gate["drive_not"] = "a4wd"
            elif dnot_by_T.get(T):
                # round4-1119: the siblings rule out one system of a family
                # whose other system the page also names (4WD beside AUTO)
                labs.append("not " + _drive_label(dnot_by_T[T]))
                gate["drive_not"] = _drive_gate(dnot_by_T[T])
            fu = self.fuel_of(c, cat, T)
            if fu == DRIVE_AMBIGUOUS:
                return {"status": "held_fuel_conflict", "T": T, "drv": ""}
            # the engine column's fuel (round3-1119): 'hybrid' / 'gas' for a
            # feed name that does not say Hybrid (a Hybrid name on a gas
            # column left T out above; on a hybrid column it says it)
            ffu = self.fit_engine_limit(c, cat, T)[1]
            if ffu and not re.search(r"hybrid", T[1], re.I):
                if fu and fu != ffu:
                    return {"status": "held_fuel_conflict", "T": T, "drv": ""}
                fu = ffu
            eng, tr = self.engine_trans_of(c, cat, T, gas_only=(fu == "gas"))
            if eng == DRIVE_AMBIGUOUS:
                return {"status": "held_engine_conflict", "T": T, "drv": ""}
            labs += [x for x in (eng, tr) if x]
            if eng:
                gate["eng"] = eng.split("/")
            if tr:
                gate["trans"] = _TRANS_GATE[tr]
            if fu:
                if fu == "gas" and self.ns in ROUND8_NS and self._hybrid_unread(T):
                    gas_checked.add(T)      # the gate stays; the note says what was checked
                else:
                    labs.append(fu)
                gate["fuel"] = fu
            if fu == "gas" and not eng:
                # the fuel gate reads the decode too (round3-1119): an
                # attested displacement the engine column leaves out
                nots = self.fit_engine_not(c, cat, T)
                if self.ns in HYBRID_ENG_NOT_NS:
                    # round6-1119 (hub decision 3): the hybrid's own displacement
                    # too, where the engine column prints it beside the gas
                    # engine (QX60 2014-2017 regulators and mirrors: "2.5L
                    # QR25DER" with 3.5L), so a decoded 2.5L QX60 is not plain
                    nots = sorted(set(nots) | set(self.hybrid_only_disps(T)))
                if nots:
                    gate["eng_not"] = [f"{x:.1f}L" for x in nots]
            if T in win_by_T:
                # round4-1119 (hub decision 2): listed for these builds only;
                # no VIN decode gives the build month, so the app never
                # confirms it ("check the build date on the door sticker")
                labs.append(_win_label(win_by_T[T]["wins"]))
                gate["built"] = _win_gate(win_by_T[T]["wins"])
            label_by_T[T] = ", ".join(labs)
            if gate:
                gate_by_T[T] = gate
        if cab:
            text = f"{text}; {cab}"
            if not _likely_note_fits(brand, sorted(c.pns)[0], text, pack):
                return {"status": "held_cab_qualifier", "detail": cab, "drv": "", "labels": label_by_T}
        drv = "; ".join(x for x in (self._limit_note(label_by_T), self._unchecked_note(unchecked_by_T, Ts),
                                    self._gas_checked_note(gas_checked, Ts)) if x)
        if drv:
            text = f"{text}; {drv}"
            if not _likely_note_fits(brand, sorted(c.pns)[0], text, pack):
                return {"status": "held_drive_qualifier", "detail": drv, "drv": drv, "labels": label_by_T,
                        "gas": sorted(gas_checked)}
        return {"status": "ok", "text": text, "drv": drv, "gates": gate_by_T, "labels": label_by_T,
                "gas": sorted(gas_checked)}

    def _strict_refusal(self, c, cat, cand, slots):
        """(code, detail) for a strict-note category (policy.STRICT_NOTE_CATS,
        hub 2026-11-09 18:20) when an app's own-page note is anything but a
        position, or the class does not sit in exactly one clean slot with
        one stated packaging; else None. Only removes claims."""
        if c.packaging in ("module", "linkage", ""):
            return "packaging_unstated", c.packaging or "none"
        bad = sorted({m["slot"].reason for _, m in cand if m["slot"].reason})
        if bad or len(slots) != 1:
            return "strict_position", ";".join(bad) or "+".join(sorted(slots))
        # §11.4 seed 811023 (G06, mopar 55154863AC "MOTOR Windshield wiper"):
        # a row or name of the same number calling it a pivot or linkage means
        # the packaging is not a bare motor
        if c.packaging != "drive":
            texts = [r.other_names for r in c.records] + \
                [f"{lr.main} | {lr.aux}" for lr in self.list_rows
                 if lr.cat == cat and policy.pn_key(self.ns, lr.pn) == c.key]
            hit = next((t for t in texts if t and re.search(r"\b(pivot|linkage|link)\b", t, re.I)), None)
            if hit:
                return "packaging_conflict", hit[:80]
        # §11.4 seed 811023 (G13 2017 Compass two rear motors, G19/G22 2009 G37
        # sedan vs coupe, G10 2013 Charger R/T): another number in the same slot
        # of any app's cell means the car's number depends on its configuration
        for T, _ in cand:
            for k, m in ((self.cells_info.get((T, cat)) or {}).get("members") or {}).items():
                if k != c.key and set(m["slot"].slots) & slots and not self.comparable(cat, c.key, k):
                    return "strict_slot_split", f"{T[0]} {T[1]} {T[2]}: also {k}"
        names = " | ".join(n for r in c.records for n in r.oem_names)
        if re.search(policy.WIPER_OPTION_RE, names, re.I):
            return "strict_option_name", names[:80]
        if slots == {"R"}:
            # a body without a rear wiper decoded in any of the group's own
            # model-years refuses; a model with no decoded body at all refuses
            for mk, md in sorted({(T[0], T[1]) for T, _ in cand}):
                yb = set().union(*[self.model_bodies.get((mk, md, T[2])) or () for T, _ in cand
                                   if (T[0], T[1]) == (mk, md)])
                if not self.model_bodies.get((mk, md)) or yb & policy.NO_REAR_WIPER_BODIES:
                    return "rear_body_gate", f"{mk} {md}: decoded bodies {','.join(sorted(yb)) or 'none'}"
        if slots & {"FL", "FR"}:
            # a twin-motor half only when every app's cell holds both halves:
            # Honda/Ford print "Front Driver Side" on single motors
            for T, _ in cand:
                have = set((self.cells_info.get((T, cat)) or {}).get("slots") or {})
                if not {"FL", "FR"} <= have:
                    return "strict_position", f"{T[0]} {T[1]} {T[2]}: lone {'+'.join(sorted(slots))}"
        for T, _ in cand:
            notes = self.own_page(T, cat, c)[1]
            ctx = N.NoteContext(T[2], frozenset(m.lower() for _, m in self.t_sources.get(T, set())),
                                self.ns_models_f)
            v = N.classify(notes, ctx)
            extra = sorted(v.classes - policy.STRICT_NOTE_ALLOWED)
            if extra:
                return "strict_note", f"{T[0]} {T[1]} {T[2]}: {','.join(extra)}"
        return None

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
        return "; ".join(f"{md}: {cab} only" for (_mk, md), cab in self._cab_only_map(c, cat, Ts).items())

    def _cab_only_map(self, c, cat, Ts) -> dict:
        """{(make, model): cab} behind _cab_only's note (the per-app cab gate,
        2026-11-18), in the note's order."""
        out = {}
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
                out[(mk, md)] = next(iter(cabs))
        if not out and getattr(self, "ns", None) == "nissan":
            return self._nissan_cab_only_map(c, cat, Ts)
        return out

    # ------------------------------------------- §5.16 drive rule (2026-11-18)
    def _gm_page_letters(self, T):
        """GM series letters on every own page of T (all categories)."""
        cache = self.__dict__.setdefault("_gm_letters", {})
        if T not in cache:
            letters = set()
            for (t, _cat), rows in self.t_list_rows.items():
                if t != T:
                    continue
                for lr in rows:
                    for n in lr.notes:
                        m = _FVO_BODY_RE.match(n or "")
                        s = _gm_series_letters(m.group(1)) if m else None
                        if s:
                            letters |= s
            cache[T] = frozenset(letters)
        return cache[T]

    def drive_of(self, c, cat, T):
        """§5.16 drive rule: the drive classes T's evidence limits class c to,
        None when nothing limits it, DRIVE_AMBIGUOUS when the evidence is
        ambiguous or contradicts itself (the vehicle-year is left out)."""
        gm_letters = self._gm_page_letters(T) if self.ns == "gm" else None
        if self.t_list_rows.get((T, cat)):
            own = [lr for lr in self.t_list_rows[(T, cat)]
                   if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched and not self.note_excludes(lr.notes, T)]
            own_d = [_row_drive(lr.notes, lr.site, gm_letters, lr.variant) for lr in own]
        else:
            own = [r for r in self.t_seed_records.get((T, cat), [])
                   if r.key == c.key and not self.note_excludes(r.note_texts, T)]
            own_d = [_row_drive(r.note_texts, r.site, gm_letters, _catalog_of(r.list_url)) for r in own]
        d_own = _drive_union(own_d) if own_d else None
        fit = [f for (cc, r, f, t) in self.t_rows.get((T, cat), []) if cc is c]
        d_fit = _drive_union([_fit_drive(f) for f in fit]) if fit else None
        if DRIVE_AMBIGUOUS in (d_own, d_fit):
            return DRIVE_AMBIGUOUS
        if d_own is None or d_fit is None:
            d = d_own if d_fit is None else d_fit
        else:
            d = d_own & d_fit
            if not d:
                return DRIVE_AMBIGUOUS
        if d is None:
            return None
        # a feed model whose name states its drive ('Prius AWD-e')
        mp, mn, _ = _drive_terms(T[1])
        md = _drive_allowed(mp, mn)
        if md:
            return None if md <= d else DRIVE_AMBIGUOUS
        return d

    # --------------------------- drive limit basis (gates-1118, hub refinement)
    # The independent check of rules-1118 (groups/_report/restored_verify_2026-
    # 11-18b.json) found most GM "<model>: 2WD only" limits rest on the 4wd
    # catalog page never having been read (only the 2wd page is in the raw),
    # and the Mopar "1500: 4WD only" on 2012 Ram fitment rows that list 4WD
    # trims for every number on the page. Those limits are not the catalog's
    # statement. drive_basis says which kind a vehicle-year's limit is; the
    # gate is the same for both (only donors of the checked drive are shown),
    # the note words the second kind "<model>: only 2WD checked".
    def drive_material(self, T, d):
        """Hub 2026-11-18 (after the gates review): is T's drive limit d a
        real split? A limit needs the model-year to come in the other drive
        family too. Decided by the catalog's own structure where it files a
        model-year by drive (gmpartsgiant '2007-chevrolet-tahoe-2wd' / '-4wd',
        '2011-chevrolet-traverse-2wd' / '-awd': the year page's variants):
        True when a catalog of the other family is offered for T (read or
        not), False when only d's family is. Where the catalog does not file
        by drive (one catalog per model-year: Ford, Mopar, Mercedes, Nissan),
        policy.SINGLE_DRIVE_TABLE decides: False for a listed model-year in
        d's family, DRIVE_AMBIGUOUS when the table's drive is the other family
        (the evidence contradicts itself: the vehicle-year is left out), True
        otherwise (unchanged). Only removes limits the model cannot have, or
        vehicle-years; never adds one."""
        fam = _FOUR if set(d) <= _FOUR else _TWO
        other = _TWO if fam is _FOUR else _FOUR
        offered = set()
        for ym in self.t_years.get(T, []):
            for v in [ym.variant] + list(ym.variants or []):
                vd = _variant_drive(v)
                if vd:
                    offered |= set(vd)
        if offered:
            return bool(offered & other)
        single = policy.single_drive(T[0], T[1], T[2])
        if single is None:
            return True
        return False if set(single) <= fam else DRIVE_AMBIGUOUS

    def drive_basis(self, c, cat, T, d) -> str:
        """'stated' when the catalog states T's drive limit for class c:
        every own-page row of the number names the drive itself (option code,
        GM series letter, a drive note) or sits on a drive-named catalog page
        of T while a page of T of the other drive family was read in this
        category without the number; or, when the limit comes from the product
        pages' fitment rows, another number's fitment row for T in this
        category names the other drive family. 'unchecked' otherwise: the
        other drive's page is not in the raw, or no fitment row on T's page
        names the other drive (rows that may be incomplete)."""
        fam = _FOUR if d and set(d) <= _FOUR else _TWO
        other = _TWO if fam is _FOUR else _FOUR
        gm_letters = self._gm_page_letters(T) if self.ns == "gm" else None
        if self.t_list_rows.get((T, cat)):
            page = [(lr.variant, policy.pn_key(self.ns, lr.pn)) for lr in self.t_list_rows[(T, cat)]]
            own = [(lr.notes, lr.site, lr.variant) for lr in self.t_list_rows[(T, cat)]
                   if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched and not self.note_excludes(lr.notes, T)]
        else:
            recs = self.t_seed_records.get((T, cat), [])
            page = [(_catalog_of(r.list_url), r.key) for r in recs]
            own = [(r.note_texts, r.site, _catalog_of(r.list_url)) for r in recs
                   if r.key == c.key and not self.note_excludes(r.note_texts, T)]
        other_pages = {v for v, _k in page if (vd := _variant_drive(v)) and vd <= other}
        other_has_it = any(k == c.key for v, k in page if v in other_pages)
        verdicts = []
        for notes, site, variant in own:
            rd = _row_drive(notes, site, gm_letters, "")
            if rd not in (None, DRIVE_AMBIGUOUS) and rd <= fam:
                verdicts.append(True)           # the row's own code or note names the drive
                continue
            vd = _variant_drive(variant)
            if vd and vd <= fam:
                verdicts.append(bool(other_pages) and not other_has_it)
                continue
            verdicts.append(None)               # the row says nothing about the drive
        if verdicts and all(v is True for v in verdicts):
            return "stated"
        if any(v is False for v in verdicts):
            return "unchecked"
        for (cc, _r, f, _t) in self.t_rows.get((T, cat), []):
            if cc is c:
                continue
            fd = _fit_drive(f)
            if fd not in (None, DRIVE_AMBIGUOUS) and fd <= other:
                return "stated"
        return "unchecked"

    def _hybrid_unread(self, T) -> bool:
        """T's year page offers a hybrid catalog and no list page of T in the
        raw is a hybrid variant page (round8 decision 5)."""
        vs = {str(v).lower() for ym in self.t_years.get(T, []) for v in [ym.variant] + list(ym.variants or []) if v}
        if not any("hybrid" in v for v in vs):
            return False
        return not any("hybrid" in f"{lr.variant} {lr.list_url}".lower()
                       for (t, _cat), rows in self.t_list_rows.items() if t == T for lr in rows)

    def _gas_checked_note(self, gas_checked, Ts) -> str:
        """'checked on gas-model pages' (every vehicle-year), else '<model>[
        years]: checked on gas-model pages'; '' for none (round8 decision 5)."""
        if not gas_checked or getattr(self, "_gas_note_off", False):
            return ""
        if set(gas_checked) == set(Ts):
            return "checked on gas-model pages"
        names = []
        for mk, md in sorted({(T[0], T[1]) for T in gas_checked}):
            ys = sorted(T[2] for T in gas_checked if (T[0], T[1]) == (mk, md))
            alls = sorted(T[2] for T in Ts if (T[0], T[1]) == (mk, md))
            names.append(md if ys == alls else f"{md} " + ", ".join(
                f"{a}-{b}" if b != a else f"{a}" for a, b in ((r[0], r[-1]) for r in _year_runs(ys))))
        return ", ".join(names) + ": checked on gas-model pages"

    def _unchecked_note(self, unchecked_by_T, Ts) -> str:
        """'<model>: only 2WD checked' for vehicle-years whose drive limit is
        'unchecked': the hub's "checked for 2WD; 4WD not checked", in words
        short enough for the 160-character note (the long form does not fit
        the 2004 Trailblazer regulator notes, which would be refused). Models
        sharing the label are named together; '<model> 2005-2007' when only
        some of its years are; no model when every vehicle-year of the group
        is. When every vehicle-year is unchecked within one drive family but
        under different labels (C-Max 2WD, Focus FWD), the family is named
        once ('only 2WD checked': FWD is a 2-wheel drive), which keeps those
        notes within 160 characters. '' for none."""
        if not unchecked_by_T:
            return ""
        allT = set(Ts)
        labs = set(unchecked_by_T.values())
        if set(unchecked_by_T) == allT and len(labs) > 1:
            if labs <= {"2WD", "FWD", "RWD"}:
                return "only 2WD checked"
            if not labs & {"2WD", "FWD", "RWD"}:
                return "only 4WD/AWD checked"
        by = defaultdict(list)
        for T, lab in unchecked_by_T.items():
            by[lab].append(T)
        parts = []
        for lab, ts in sorted(by.items()):
            if set(ts) == allT:
                parts.append(f"only {lab} checked")
                continue
            names = []
            for mk, md in sorted({(T[0], T[1]) for T in ts}):
                ys = sorted(T[2] for T in ts if (T[0], T[1]) == (mk, md))
                if set(ys) == {T[2] for T in allT if (T[0], T[1]) == (mk, md)}:
                    names.append(md)
                    continue
                run = []
                for y in ys:
                    if run and y == run[-1][1] + 1:
                        run[-1][1] = y
                    else:
                        run.append([y, y])
                names += [f"{md} {a}{'-' + str(b) if b != a else ''}" for a, b in run]
            parts.append(f"{', '.join(names)}: only {lab} checked")
        return "; ".join(parts)

    def _drive_note(self, drive_by_T) -> str:
        """The drive part of the §5.16 limit note (see _limit_note)."""
        return self._limit_note({T: (_drive_label(d) if d else "") for T, d in drive_by_T.items()})

    def _limit_note(self, label_by_T) -> str:
        """'<model>: <label> only' per model whose vehicle-years carry a limit
        label ('4WD', 'crew cab, 4WD, 2.4L'); '<model> 2005-2008: ... only'
        when only some years do or the years differ; one '<label> only' when
        every vehicle-year of the group has the same label. '' for none."""
        by = defaultdict(dict)
        for T, lab in label_by_T.items():
            by[(T[0], T[1])][T[2]] = lab or ""
        labels = {lab for ys in by.values() for lab in ys.values()}
        if labels <= {""}:
            return ""
        if len(labels) == 1:
            return f"{next(iter(labels))} only"
        parts = []
        for (mk, md), ys in sorted(by.items()):
            labs = {lab for lab in ys.values()}
            if labs == {""}:
                continue
            if len(labs) == 1:
                parts.append(f"{md}: {next(iter(labs))} only")
                continue
            run = []
            for y in sorted(ys):
                if run and ys[y] == run[-1][2] and y == run[-1][1] + 1:
                    run[-1][1] = y
                else:
                    run.append([y, y, ys[y]])
            for a0, b0, lab in run:
                if lab:
                    parts.append(f"{md} {a0}{'-' + str(b0) if b0 != a0 else ''}: {lab} only")
        return "; ".join(parts)

    # ------------------------------ §5.16 engine / transmission / fuel / rear cab (2026-11-18)
    def _own_rows(self, c, cat, T):
        """[(notes, site, page variant, list_url)] of T's own-page rows listing class c."""
        if self.t_list_rows.get((T, cat)):
            return [(lr.notes, lr.site, lr.variant, lr.list_url) for lr in self.t_list_rows[(T, cat)]
                    if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched and not self.note_excludes(lr.notes, T)]
        return [(r.note_texts, r.site, _catalog_of(r.list_url), r.list_url) for r in self.t_seed_records.get((T, cat), [])
                if r.key == c.key and not self.note_excludes(r.note_texts, T)]

    def _t_trans_seen(self, T):
        """Transmission classes any own-page row of T (all categories) names."""
        cache = self.__dict__.setdefault("_trans_seen", {})
        if T not in cache:
            seen = set()
            for (t, _cat), rows in self.t_list_rows.items():
                if t == T:
                    for lr in rows:
                        for n in lr.notes:
                            m = _FVO_BODY_RE.match(n or "")
                            if m:
                                seen |= _trans_terms(m.group(1))
            for (t, _cat), recs in self.t_seed_records.items():
                if t == T:
                    for r in recs:
                        for n in r.note_texts:
                            m = _FVO_BODY_RE.match(n or "")
                            if m:
                                seen |= _trans_terms(m.group(1))
            cache[T] = frozenset(seen)
        return cache[T]

    def _engine_limit(self, c, cat, T, gas_only=False):
        """frozenset of litres the option column limits class c to on T, or
        None: every configuration of every own row names an engine code; or
        (sibling rule) another number in the same slot of T's cell is listed
        for an engine our rows never name (2014 Q70: 24820-6AH1B 'SEDAN.
        VQ37VHR. PREMIUM + SEDAN. (BASE+ SPORTPRE)' while the VK56VD clusters
        are 24820-6AH1C/-6AH1D), so that engine is not ours."""
        rows = self._own_rows(c, cat, T)
        if not rows:
            return None
        es = [_row_engine_trans(n, st)[0] for n, st, _v, _u in rows]
        if all(e is not None for e in es):
            return frozenset().union(*es)
        U = self._t_engines(T, cat, gas_only)
        if not U:
            return None
        named = set().union(*[_row_engine_names(n, st) for n, st, _v, _u in rows])
        members = (self.cells_info.get((T, cat)) or {}).get("members") or {}
        me = members.get(c.key)
        if not me:
            return None
        mine = set(me["slot"].slots)
        excluded = set()
        for k, m in members.items():
            if k == c.key or not (set(m["slot"].slots) & mine) or self.comparable(cat, c.key, k):
                continue
            sib = self.classes.get((k, cat))
            if sib is None or sib.packaging != c.packaging:
                continue        # a motor is no alternative to a bare regulator in the same door
            srows = self._own_rows(sib, cat, T)
            se = [_row_engine_trans(n, st)[0] for n, st, _v, _u in srows]
            if srows and all(e is not None for e in se):
                excluded |= set().union(*se) - named
        allowed = U - excluded
        if excluded and allowed and allowed < U:
            return frozenset(allowed)
        return None

    def _t_engines(self, T, cat, gas_only=False):
        """The displacements T comes in: the year page's engine list when it
        has one (all parsed), else every engine a row on T's own pages names,
        in any category (2014 Q70 gauge clusters: VQ37VHR and VK56VD rows; the
        2000 Xterra regulator page names VG33E only, its mirror page KA24DE
        too); None when
        neither says. Hybrid keys are left out for a gas-only number."""
        keys = [k for k in self.engineu.get(T, ()) if not (gas_only and len(k) > 2 and k[2] == "hybrid")]
        if keys and self.engineu_src.get(T) == "year_page":
            if any(not isinstance(k[0], int) for k in keys):
                return None
            return {round(k[1], 1) for k in keys}
        cache = self.__dict__.setdefault("_t_page_engines", {})
        if T not in cache:
            page = set()
            for (t, _c), rows in self.t_list_rows.items():
                if t == T:
                    for lr in rows:
                        page |= _row_engine_names(lr.notes, lr.site)
            for (t, _c), recs in self.t_seed_records.items():
                if t == T:
                    for r in recs:
                        page |= _row_engine_names(r.note_texts, r.site)
            cache[T] = frozenset(page)
        return set(cache[T]) or None

    def _listed_on_seed(self, c, cat, seed) -> bool:
        """True when a catalog page seeded as `seed` (make, catalog model,
        year) lists class c in cat: a matched manifest row, or a record seeded
        there (policy.AMBIGUOUS_FEED_YEARS; the seed need not map to a feed
        model, 'Rogue Select' does not)."""
        cache = self.__dict__.setdefault("_seed_keys", None)
        if cache is None:
            cache = defaultdict(set)
            for lr in self.list_rows:
                if lr.matched:
                    cache[(tuple(lr.seed), lr.cat)].add(policy.pn_key(self.ns, lr.pn))
            for r in self.records:
                cache[(tuple(r.seed), r.cat)].add(r.key)
            self._seed_keys = cache
        return c.key in cache.get((tuple(seed), cat), ())

    def _t_fit_engines(self, T):
        """(all, hybrid, gas) displacements T's model-year offers on the
        catalog's own evidence: every product-page fitment row of T in any
        category (rows_by_T) and T's year page (engine list, or fordpartsgiant
        engine sub-catalog slugs). A row's engines span its years, so this can
        hold an engine of a neighbouring year; a limit read against it can
        only narrow (round3-1119)."""
        cache = self.__dict__.setdefault("_fit_engines_cache", {})
        if T not in cache:
            U, UH, UG, YP, YPH = set(), set(), set(), set(), False
            es = [e for (_cat, _c, _r, f, _t) in self.rows_by_T.get(T, []) for e in (f.engines or [])]
            for ym in self.t_years.get(T, []):
                if ym.error or not _status_ok(ym.status):
                    continue
                for e in ym.engines or []:
                    x = _fit_lit(e)
                    if x is not None:
                        YP.add(x)
                        U.add(x)
                        (UH if _FIT_HYBRID_RE.search(e) else UG).add(x)
                for s in [ym.variant] + list(ym.variants or []) + list(ym.trims or []):
                    m = _FIT_SLUG_LIT_RE.search(str(s or ""))
                    if m:
                        x = round(int(m.group(1)) + int(m.group(2)) / 10, 1)
                        YP.add(x)
                        U.add(x)
                    if re.search(r"hybrid", str(s or ""), re.I):
                        YPH = True
            for e in es:
                x = _fit_lit(e)
                if x is None:
                    continue
                U.add(x)
                (UH if _FIT_HYBRID_RE.search(e) else UG).add(x)
            cache[T] = (frozenset(U), frozenset(UH), frozenset(UG), frozenset(YP), YPH)
        return cache[T]

    def _fit_engine_column(self, c, cat, T):
        """(L, LH, LG, gas_said) of class c's product-page engine column for
        T, or None when a fitment row prints no displacement (or there is no
        row): L every printed displacement, LH / LG the hybrid / other ones,
        gas_said every non-hybrid engine names gasoline ("GAS", "FLEX")."""
        fit = [f for (cc, _r, f, _t) in self.t_rows.get((T, cat), []) if cc is c]
        if not fit:
            return None
        L, LH, LG, gas_said = set(), set(), set(), True
        for f in fit:
            es = [e for e in (f.engines or []) if _fit_lit(e) is not None]
            if not es:
                return None
            for e in es:
                x = _fit_lit(e)
                L.add(x)
                if _FIT_HYBRID_RE.search(e):
                    LH.add(x)
                else:
                    LG.add(x)
                    # "2.4L L4" says no fuel: the Camry Hybrid's 2.4L prints the same
                    # way on that site, so only "GAS" / "FLEX" words make a gas limit
                    if not _FIT_GAS_RE.search(e) or _FIT_DIESEL_RE.search(e):
                        gas_said = False
        return L, LH, LG, gas_said

    def fit_engine_conflict(self, c, cat, T) -> bool:
        """policy.LIKELY_FIT_ENGINE_RULE: the engine column names none of the
        displacements T's model-year offers (the catalog attests it for T and
        T's year page or a lot car of T has it): 80730-JK00C's '2015 Infiniti
        Q40 | 6 Cyl 2.5L' row, while every Q40 is a 3.7L. T is left out."""
        if not policy.LIKELY_FIT_ENGINE_RULE:
            return False
        col = self._fit_engine_column(c, cat, T)
        if col is None:
            return False
        L = col[0]
        U, _UH, _UG, YP, _YPH = self._t_fit_engines(T)
        lots = self.o.lot_engines
        lot = frozenset() if lots is None else (lots.get(T) or {}).get("lits", frozenset())
        offers = [u for u in U if _lit_in(YP, u) or _lit_in(lot, u)]
        return bool(offers) and not any(_lit_in(L, u) for u in offers)

    def hybrid_only_disps(self, T) -> list:
        """round6-1119 (hub decision 3, HYBRID_ENG_NOT_NS): the displacements
        T's model-year offers (_t_fit_engines) that no gas-catalog page of the
        model names, when T's year page offers a hybrid catalog: the hybrid's
        own engine (QX60 2014-2017: 2.5L QR25DER beside the gas 3.5L VQ35DE).
        The gas engines are read from T's own pages, else from the model's
        other years' pages (QX60 2016's pages name no engine). [] when the
        year page offers no hybrid, or no page of the model names an engine."""
        U, _UH, _UG, _YP, YPH = self._t_fit_engines(T)
        if not YPH or not U:
            return []
        gas = self._t_engines(T, "", gas_only=True)
        if not gas:
            gas = set()
            for t in {t for (t, _cat) in self.t_list_rows if (t[0], t[1]) == (T[0], T[1])}:
                gas |= set(self._t_engines(t, "", gas_only=True) or ())
        if not gas:
            return []
        return sorted(u for u in U if not _lit_in(gas, u))

    def fit_engine_not(self, c, cat, T) -> list:
        """The displacements a "gas only" vehicle-year's fuel gate also rules
        out by the decode (gate "eng_not", round3-1119, class 2 of the
        2026-11-18c check): every displacement the catalog attests for T that
        the number's engine column leaves out (QX60 2016 2.5L, Murano 2016
        2.5L, Rogue 2017 2.0L: the hybrids, listed and decoded as plain
        "QX60" with nothing saying hybrid). [] without an engine column."""
        if not policy.LIKELY_FIT_ENGINE_RULE:
            return []
        col = self._fit_engine_column(c, cat, T)
        if col is None:
            return []
        U = self._t_fit_engines(T)[0]
        return sorted(u for u in U if not _lit_in(col[0], u))

    def fit_engine_limit(self, c, cat, T):
        """(displacements, fuel) the product page's engine column limits class
        c to on T (policy.LIKELY_FIT_ENGINE_RULE): every fitment row of c for
        T prints at least one displacement, and their union leaves out one T's
        model-year offers -> frozenset of litres, else None; fuel 'hybrid' when
        every printed engine is a hybrid and T has gas engines, 'gas' when
        every printed engine says gasoline ("GAS", "FLEX"; a bare "2.4L L4"
        says nothing) and T has a hybrid, else ''. A row with no displacement (no engine
        column, 'BATTERY EV') limits nothing.
        "Offers": the catalog attests the displacement for T (_t_fit_engines)
        AND T's year page lists it or a car of T on the pinned lot is decoded
        with it (Options.lot_engines). A fitment row's engines
        span its years and often several catalog models (one Camry row covers
        2007-2017 with 2.4L/2.5L/3.5L; "GS350, GS430"), so the catalog alone
        would put "2.4L/3.5L only" on every 2007 Camry part; the lot's own
        decodes are the cars a missing displacement would wrongly show plain.
        Likewise a fuel limit needs T's year page offering a hybrid catalog or
        a hybrid (gas) car of T on the lot. Without the lot input (lot_engines
        None) every displacement the catalog attests for T counts: more limits.
        A "gas only" year also gets fit_engine_not (no label)."""
        if not policy.LIKELY_FIT_ENGINE_RULE:
            return None, ""
        col = self._fit_engine_column(c, cat, T)
        if col is None:
            return None, ""
        L, LH, LG, gas_said = col
        U, UH, UG, YP, YPH = self._t_fit_engines(T)
        lots = self.o.lot_engines
        lot = None if lots is None else (lots.get(T) or {"lits": frozenset(), "hybrid": False, "gas": False})
        missing = [u for u in U if not _lit_in(L, u)]
        if lot is not None:
            # offered: the catalog attests it for T and T's year page lists it
            # or a lot car of T is decoded with it. A lot decode the catalog
            # never attests for T (a "2000 F-150" decoded 7.3L: a Super Duty
            # listed as F-150) is a listing/VIN mismatch, not an engine of T
            missing = [u for u in missing if _lit_in(YP, u) or _lit_in(lot["lits"], u)]
        lim = frozenset(L) if missing else None
        fuel = ""
        if LH and not LG and UG and (lot is None or lot["gas"]):
            fuel = "hybrid"
        elif LG and not LH and gas_said and UH and (lot is None or lot["hybrid"] or YPH):
            fuel = "gas"
        return lim, fuel

    def engine_trans_of(self, c, cat, T, gas_only=False):
        """(engine label, transmission label) the evidence limits class c to
        on T, '' when none. Engine: the option column (_engine_limit names
        fewer displacements than T's engine list; config-tuple option columns,
        policy.DRIVE_CONFIG_FVO_SITES) and the product page's engine column
        (fit_engine_limit, every site), intersected; an empty intersection is
        DRIVE_AMBIGUOUS. Transmission: every configuration names one class
        and T's own pages show the other class (config-tuple columns only)."""
        rows = self._own_rows(c, cat, T)
        E_fit = self.fit_engine_limit(c, cat, T)[0]
        if not policy.LIKELY_ENGINE_TRANS_RULE:
            return "", ""
        xs = [_row_engine_trans(n, st)[1] for n, st, _v, _u in rows]
        E = self._engine_limit(c, cat, T, gas_only) if rows else None
        disp = _INFINITI_DISP.get(re.sub(r"\s+", "", str(T[1])).upper()) if T[0] == "Infiniti" else None
        if E:
            U = self._t_engines(T, cat, gas_only)
            if disp and round(disp / 10, 1) in E:
                E = None
            elif disp:
                # the limit leaves out the only engine the name allows (FX45
                # mirror 96301-CL21A: the sibling rule takes 4.5L away): the
                # evidence contradicts itself for this vehicle-year
                return DRIVE_AMBIGUOUS, ""
            elif U and U <= E:
                E = None
        if E_fit and disp:
            if not _lit_in(E_fit, round(disp / 10, 1)):
                return DRIVE_AMBIGUOUS, ""     # the engine column leaves out the name's engine
            E_fit = None                       # the name says the engine: no label needed
        if E and E_fit:
            both = frozenset(x for x in E if _lit_in(E_fit, x))
            if not both:
                return DRIVE_AMBIGUOUS, ""     # option column and engine column disagree
            E = both
        else:
            E = E or E_fit
        eng = "/".join(f"{x:.1f}L" for x in sorted(E)) if E else ""
        tr = ""
        if xs and all(x for x in xs) and len(set(xs)) == 1:
            x = xs[0]
            other = {"manual": "auto", "auto": "manual"}[x]
            if other in self._t_trans_seen(T):
                tr = "manual" if x == "manual" else "automatic"
        return eng, tr

    def fuel_of(self, c, cat, T):
        """'gas' / 'hybrid' when T's catalog offers a hybrid page (year page
        variants: infinitipartsdeal 2014 Q70 'gas' + 'hybrid') and class c sits
        on one of the two only; '' for none; DRIVE_AMBIGUOUS when the feed name
        says hybrid and the number is on the gas page only."""
        if not policy.LIKELY_FUEL_RULE:
            return ""
        vs = {v.lower() for ym in self.t_years.get(T, []) for v in [ym.variant] + list(ym.variants or []) if v}
        if not any("hybrid" in v for v in vs):
            return ""
        rows = self._own_rows(c, cat, T)
        if not rows:
            return ""
        fuels = {"hybrid" if re.search(r"hybrid", (v or "") + " " + (u or ""), re.I) else "gas"
                 for _n, _s, v, u in rows}
        named_h = bool(re.search(r"hybrid", T[1], re.I))
        if fuels == {"gas"}:
            return DRIVE_AMBIGUOUS if named_h else "gas"
        if fuels == {"hybrid"}:
            return "" if named_h else "hybrid"
        return ""

    def rear_cab_of(self, c, cat, T, slots) -> str:
        """'crew cab' for a rear-door window part on T when T's own page for
        it is split by cab code (nissanpartsdeal Titan/Frontier rear-door
        glass 'KC. S' beside 'CC') and the part's own row names no cab: the
        King Cab rear access door has its own glass and no such part. '' else."""
        if self.ns != "nissan" or cat not in ("window-regulator", "window-switch") or not slots \
                or not set(slots) <= {"RL", "RR"}:
            return ""
        rows = self._own_rows(c, cat, T)
        if not rows or any(_fvo_cab_codes(n) for n, _s, _v, _u in rows):
            return ""
        return "crew cab" if {"KC", "CC"} <= self._model_rear_cabs(T[0], T[1], cat) else ""

    def _model_rear_cabs(self, mk, md, cat):
        """Cab codes on the model's own rear-door pages in cat, any year
        (nissanpartsdeal '.../rear_door_window_regulator.html': glass
        82300-7S200 'KC. S' beside 82300-8S500 'CC'). A year without its own
        manifest (2004 Titan, seed page only) takes the model's structure."""
        cache = self.__dict__.setdefault("_rear_cabs", {})
        key = (mk, md, cat)
        if key not in cache:
            codes = set()
            for (t, cc), rows in self.t_list_rows.items():
                if (t[0], t[1]) != (mk, md) or cc != cat:
                    continue
                for lr in rows:
                    if re.search(r"rear[_-]door", lr.list_url or "", re.I):
                        codes |= _fvo_cab_codes(lr.notes) or set()
            cache[key] = frozenset(codes)
        return cache[key]

    # nissanpartsdeal option-column cab codes (interchange 2026-11-18): the
    # Frontier and Titan pages code each row "KC" (King Cab) or "CC" (Crew
    # Cab), e.g. 2010 Frontier climate controls 27510-9CA0A "CC. S" beside
    # 27510-9BA0A "KC. S"; Nissan's own store names KC/CC parts the same way
    # (parts.nissanusa.com 999T1-BR103KC "King Cab, Crew Cab"). The product
    # page's fitment trims print no cab, so the GM rule above never fires.
    _NISSAN_CABS = {"CC": "crew cab", "KC": "king cab"}

    def _nissan_cab_only(self, c, cat, Ts) -> str:
        """Same note as _cab_only, from the own-page option column: when every
        own-page row listing the number for a model codes only one cab, the
        group says '<model>: <cab> only'. A row without a code, or with any
        other code, leaves that model without a note."""
        return "; ".join(f"{md}: {cab} only" for (_mk, md), cab in self._nissan_cab_only_map(c, cat, Ts).items())

    def _nissan_cab_only_map(self, c, cat, Ts) -> dict:
        """{(make, model): cab} behind _nissan_cab_only's note."""
        out = {}
        for mk, md in sorted({(T[0], T[1]) for T in Ts}):
            cabs, all_cab = set(), True
            for T in Ts:
                if (T[0], T[1]) != (mk, md):
                    continue
                rows = [lr for lr in self.t_list_rows.get((T, cat), [])
                        if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched]
                if not rows:
                    all_cab = False
                for lr in rows:
                    codes = _fvo_cab_codes(lr.notes)
                    if codes is None:
                        all_cab = False
                    else:
                        cabs |= codes
            if all_cab and len(cabs) == 1:
                out[(mk, md)] = self._NISSAN_CABS[next(iter(cabs))]
        return out

    # ------------------------- §5.16 cab / body lists, All-Mode sibling (round3-1119)
    _NISSAN_CAB3 = {"T": "regular cab", "KC": "king cab", "CC": "crew cab"}
    _CAB_ORDER = ("regular cab", "extended cab", "king cab", "access cab", "double cab", "quad cab",
                  "super cab", "supercab", "crew cab", "super crew", "supercrew", "crewmax")

    def _slot_mates(self, c, cat, T, slots):
        """Class keys of T's cell in cat whose slots overlap class c's (any
        member when slots are unknown), c itself left out."""
        members = (self.cells_info.get((T, cat)) or {}).get("members") or {}
        mine = set(slots or ())
        out = set()
        for k, m in members.items():
            if k == c.key:
                continue
            if not mine or set(m["slot"].slots) & mine or not m["slot"].slots:
                out.add(k)
        return out

    def _cab_order(self, cabs):
        return sorted(cabs, key=lambda x: (self._CAB_ORDER.index(x) if x in self._CAB_ORDER else len(self._CAB_ORDER), x))

    def _cab_list_by_T(self, c, cat, Ts, slots) -> dict:
        """policy.LIKELY_CAB_LIST_RULE: {T: [cab, ...]} for each vehicle-year
        where the number's own evidence names a cab for every configuration
        (every fitment trim names a cab; or, on the Nissan pages, every own-page
        alternative starts with T / KC / CC) and the same category on T's
        pages lists a cab it leaves out under another number of the same slot.
        Per model-year: the 2002 Frontier page lists power regulator 80721-3S500
        for KC + CC only beside 3S510 'T + KC + CC', while 1998-2001 list 3S500
        for T, KC and CC too, so only 2002 is limited. On the Nissan pages the
        cabs the model-year comes in are read from every category
        (_t_page_cabs): the 2003-2004 Frontier pages code 80721-2Z700 KC / CC
        only and print no regular-cab regulator in that slot, while other
        categories there code T."""
        if not policy.LIKELY_CAB_LIST_RULE:
            return {}
        out = {}
        for T in Ts:
            ours, page = set(), set()
            mates = self._slot_mates(c, cat, T, slots)
            fit = [f for (cc, _r, f, _t) in self.t_rows.get((T, cat), []) if cc is c]
            fcabs, fall = set(), bool(fit)
            for f in fit:
                for tr in (f.trims or []):
                    m = self._CAB_RE.search(tr)
                    if m:
                        fcabs.add(re.sub(r"\s+", " ", m.group(1).lower()))
                    else:
                        fall = False
                if not f.trims:
                    fall = False
            if fall and fcabs:
                ours = fcabs
                for (cc, _r, f, _t) in self.t_rows.get((T, cat), []):
                    if cc is not c and cc.key in mates:
                        for tr in (f.trims or []):
                            m = self._CAB_RE.search(tr)
                            if m:
                                page.add(re.sub(r"\s+", " ", m.group(1).lower()))
            elif self.ns == "nissan":
                rows = [lr for lr in self.t_list_rows.get((T, cat), [])
                        if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched]
                codes = [_fvo_cab_set(lr.notes) for lr in rows]
                if not rows or any(x is None for x in codes):
                    continue
                ours = {self._NISSAN_CAB3[x] for st in codes for x in st}
                for lr in self.t_list_rows.get((T, cat), []):
                    if policy.pn_key(self.ns, lr.pn) != c.key and policy.pn_key(self.ns, lr.pn) in mates:
                        page |= {self._NISSAN_CAB3[x] for x in (_fvo_cab_heads(lr.notes) or ())}
            if not (fall and fcabs):
                page |= self._t_page_cabs(T)
            if ours and page - ours:
                out[T] = self._cab_order(ours)
        return out

    def _t_page_cabs(self, T) -> set:
        """Every Nissan cab code (T / KC / CC) an option column on T's own
        pages names, in any category: the cabs the model-year comes in. Only
        the option-column codes: they name the cab of each configuration.
        Fitment trims mix cab words into trim names (GM "LT Crew Cab"), so a
        trim list without "Regular Cab" limits only beside a regular-cab
        number of the same slot (_cab_list_by_T)."""
        cache = self.__dict__.setdefault("_page_cabs", {})
        if T not in cache:
            cabs = set()
            if self.ns == "nissan":
                for (t, _cat), rows in self.t_list_rows.items():
                    if t == T:
                        for lr in rows:
                            cabs |= {self._NISSAN_CAB3[x] for x in (_fvo_cab_heads(lr.notes) or ())}
            cache[T] = frozenset(cabs)
        return set(cache[T])

    _BODY_WORDS = {"coupe": "coupe", "sedan": "sedan", "notchback": "sedan", "wagon": "wagon",
                   "hatchback": "hatchback", "liftback": "hatchback", "convertible": "convertible"}
    _BODY_WORD_RE = re.compile(r"\b(coupe|sedan|notchback|wagon|hatchback|liftback|convertible)\b", re.I)

    def _body_list_by_T(self, c, cat, Ts, slots) -> dict:
        """policy.LIKELY_CAB_LIST_RULE, bodies: {T: [silhouette, ...]} where
        every fitment trim of the number for T names a silhouette (coupe,
        sedan/notchback, wagon, hatchback, convertible) and the same category
        on T's pages lists another silhouette under another number of the same
        slot (Alero 2001 regulators: coupe trims beside the sedan's). The gate
        is the number's silhouettes."""
        if not policy.LIKELY_CAB_LIST_RULE or cat in policy.LIKELY_BODY_SKIP_CATS:
            return {}
        out = {}
        for T in Ts:
            mates = self._slot_mates(c, cat, T, slots)
            fit = [f for (cc, _r, f, _t) in self.t_rows.get((T, cat), []) if cc is c]
            ours, page, all_ours = set(), set(), bool(fit)
            for f in fit:
                if not f.trims:
                    all_ours = False
                for tr in (f.trims or []):
                    ws = {self._BODY_WORDS[w.lower()] for w in self._BODY_WORD_RE.findall(tr)}
                    if ws:
                        ours |= ws
                    else:
                        all_ours = False
            for (cc, _r, f, _t) in self.t_rows.get((T, cat), []):
                if cc is not c and cc.key in mates:
                    for tr in (f.trims or []):
                        page |= {self._BODY_WORDS[w.lower()] for w in self._BODY_WORD_RE.findall(tr)}
            if all_ours and ours and page - ours:
                out[T] = sorted(ours)
        return out

    def _auto_sibling(self, c, cat, T, slots) -> bool:
        """policy.LIKELY_AUTO_SIBLING_RULE: T's own pages in cat list another
        number of the same slot for the Nissan drive field AUTO (All-Mode 4WD),
        so this number's "4WD" is the part-time system only."""
        if not policy.LIKELY_AUTO_SIBLING_RULE or self.ns != "nissan":
            return False
        mates = self._slot_mates(c, cat, T, slots)
        for lr in self.t_list_rows.get((T, cat), []):
            k = policy.pn_key(self.ns, lr.pn)
            if k == c.key or k not in mates:
                continue
            for n in lr.notes:
                m = _FVO_BODY_RE.match(n or "")
                if m and any(re.search(r"(?:^|\.)\s*\*?AUTO\s*(?:\.|$)", part)
                             for alt in _split_top_plus(m.group(1), ",") for part in _split_top_plus(alt, "+")):
                    return True
        return False

    # ------------------------- round4-1119: hub decisions 1-3 (2026-11-19)
    @staticmethod
    def _same_part(a, b) -> bool:
        """Two list rows of one page name the same part in the same position."""
        def nm(s):
            return re.sub(r"\s+", " ", str(s or "").strip().lower())
        return nm(a.main) == nm(b.main) and sorted(nm(x) for x in a.locations) == sorted(nm(x) for x in b.locations)

    def _t_drive_systems(self, T) -> frozenset:
        """Drive classes any own-page row of T names (all categories): the
        option columns' words, the Nissan AUTO field, free notes."""
        cache = self.__dict__.setdefault("_t_drives", {})
        if T not in cache:
            seen = set()
            for (t, _cat), rows in self.t_list_rows.items():
                if t == T:
                    for lr in rows:
                        for _tk, pos, _neg in _row_clauses(lr.notes, lr.site):
                            seen |= pos
            cache[T] = frozenset(seen)
        return cache[T]

    def drive_sibling(self, c, cat, T):
        """policy.LIKELY_DRIVE_SIBLING_RULE (hub decision 1, 2026-11-19): T's
        page lists, for the same part and position, another number whose
        option clause is one of this number's own clauses plus a drive word
        ("*W. AWD. PREMIUM" beside "*W. PREMIUM", the "*" mark the same on
        both: round5-1119, hub decision 3, reverting round 4's "starred or
        not"): the
        configuration of that drive takes the other number, so this number's
        clause does not cover it. Not read as a drive split: a sibling that
        also lists the bare clause, or lists the clause for both drive
        families (the Titan clusters: drive is not what separates the two
        numbers); a sibling linked to this number by supersession; one not
        listed for T itself (note_excludes: another model, a production
        window under 5 months of T's year) or whose build window does not
        overlap this row's. A clause that names a drive itself is the drive
        rule's (drive_of) and allows every drive here. Returns (allowed
        classes or None, [(row, sibling, classes)]): the union over this
        number's own rows and clauses of what each clause allows; None when
        that is every drive."""
        if not policy.LIKELY_DRIVE_SIBLING_RULE:
            return None, []
        rows = self.t_list_rows.get((T, cat)) or []
        if not rows:
            return None, []
        by_url = defaultdict(list)
        for lr in rows:
            by_url[lr.list_url].append(lr)
        allowed, hits = [], []
        for _url, page in sorted(by_url.items()):
            own = [lr for lr in page if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched
                   and not self.note_excludes(lr.notes, T)]
            for r in own:
                rw = _row_windows(r.notes)
                sibs = []
                for s in page:
                    k2 = policy.pn_key(self.ns, s.pn)
                    if k2 == c.key or not self._same_part(r, s) or self.comparable(cat, c.key, k2):
                        continue
                    if self.note_excludes(s.notes, T):
                        continue
                    sw = _row_windows(s.notes)
                    if rw and sw and not any(_win_overlap(sw, a, b) for a, b in rw):
                        continue
                    sibs.append((s, _row_clauses_star(s.notes, s.site)))
                row_ok = set()
                for toks, pos, neg, star in _row_clauses_star(r.notes, r.site):
                    if pos or neg:
                        row_ok |= set(_DRIVE_ALL)       # stated drive: drive_of reads it
                        continue
                    excl = set()
                    for s, cls in sibs:
                        # round5-1119 (hub decision 3): no drive split may rest on
                        # a "*" difference alone. The drive word must sit on the
                        # same clause with the same mark (7S006 'KC. 2WD' does not
                        # split 7S00E '*KC'); and a sibling that lists the clause
                        # bare or for the other drive family under either mark
                        # (7S002 '*KC. 2WD' + 'KC. 4WD') shows drive is not what
                        # separates the two numbers
                        anym = [(p2, n2) for t2, p2, n2, _st in cls if t2 == toks]
                        if any(not p2 and not n2 for p2, n2 in anym):
                            continue        # the sibling lists this configuration bare too
                        named = set().union(*[p2 for t2, p2, _n2, st2 in cls if t2 == toks and st2 == star and p2]
                                            or [set()])
                        every = set().union(*[p2 for p2, _n2 in anym if p2] or [set()])
                        if not named or (every & _FOUR and every & _TWO):
                            continue        # no same-mark drive word, or both families: no split
                        excl |= named
                        hits.append((r, s, frozenset(named)))
                    row_ok |= set(_DRIVE_ALL) - excl
                allowed.append(row_ok)
        if not allowed:
            return None, hits
        u = frozenset(set().union(*allowed))
        return (None if u >= _DRIVE_ALL else u), hits

    def drive_sibling_limit(self, c, cat, T):
        """Decision 1 as a limit on T: ('drive', classes) when the siblings
        leave this number one drive family of T's (the drive words T's pages
        use: a QX60 page names AWD only, so excluding AWD leaves 2WD);
        ('drive_not', classes) when they leave both families (the excluded
        class beside another system of its family, e.g. 4WD beside AUTO);
        (DRIVE_AMBIGUOUS, None) when they exclude something of both
        families; None when nothing is excluded."""
        u, hits = self.drive_sibling(c, cat, T)
        if u is None:
            return None
        excl = _DRIVE_ALL - u
        e4, e2 = excl & _FOUR, excl & _TWO
        if e4 and e2:
            return DRIVE_AMBIGUOUS, None
        sysT = self._t_drive_systems(T)
        if e4:
            t4 = sysT & _FOUR
            if not t4 or t4 <= e4:
                return "drive", frozenset({"2wd"})
            return "drive_not", frozenset(e4 & t4)
        t4 = sysT & _FOUR
        return "drive", (frozenset(t4) if t4 else frozenset({"4wd", "awd"}))

    # ------------------------------ round6-1119: cab basis, option ties (hub 2026-11-19)
    def _own_list_or_seed(self, c, cat, T) -> list:
        """[(notes, site, list_url, pn)] of the number's own rows on T's page
        (list rows, else the records seeded there), as _own_rows reads them."""
        rows = self.t_list_rows.get((T, cat))
        if rows:
            return [(lr.notes, lr.site, lr.list_url, lr.pn) for lr in rows
                    if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched and not self.note_excludes(lr.notes, T)]
        return [(r.note_texts, r.site, r.list_url, r.pn) for r in self.t_seed_records.get((T, cat), [])
                if r.key == c.key and not self.note_excludes(r.note_texts, T)]

    def cab_stated(self, c, cat, T, cab) -> bool:
        """Decision 1: the cab gate's cabs are what the number's own evidence
        for T names: every own row's option column codes cabs (T / KC / CC),
        or its notes print cab words, or every fitment trim of the number for
        T names a cab; and those cabs are the gate's. A limit read from the
        page's structure (rear_cab_of) or another year of the model
        (_cab_only_map) is not stated."""
        want = set(cab) if isinstance(cab, list) else {cab}
        fit = [f for (cc, _r, f, _t) in self.t_rows.get((T, cat), []) if cc is c]
        if fit and all(f.trims for f in fit):
            cabs = {_cab_gate(m.group(1)) for f in fit for tr in f.trims for m in [self._CAB_RE.search(tr)] if m}
            if all(self._CAB_RE.search(tr) for f in fit for tr in f.trims) and cabs == want:
                return True
        own = self._own_list_or_seed(c, cat, T)
        if not own:
            return False
        cabs = set()
        for notes, site, _u, _p in own:
            codes = _fvo_cab_set(notes) if site in _NISSAN_SITES else None
            if codes:
                cabs |= {_cab_gate(self._NISSAN_CAB3[x]) for x in codes}
                continue
            words = {_cab_gate(m.group(1)) for n in notes for m in self._CAB_RE.finditer(n or "")}
            if not words:
                return False            # a row that names no cab covers every cab
            cabs |= words
        return cabs == want

    @staticmethod
    def _tie_cfgs(notes, site, T_fams, T_trans):
        """[(star, tokens, {(family, trans)}, names a transmission)] per configuration of one row
        (as _row_clauses_star reads them): the drive families and
        transmissions it names, every one of T's where it names none.
        Tokens leave out drive and transmission words."""
        out = []
        fvo, other = [], []
        for n in notes or []:
            if _CLAUSE_SKIP_RE.match(n or ""):
                continue
            m = _FVO_BODY_RE.match(n or "")
            if m:
                for alt in _split_top_plus(m.group(1), ","):
                    fvo += _split_top_plus(alt, "+") if site in policy.DRIVE_CONFIG_FVO_SITES else [alt]
            else:
                other.append(n)
        rest = " | ".join(other)
        for alt in fvo or [""]:
            text = f"{alt} | {rest}" if rest else alt
            pos, neg, left = _drive_terms(text)
            if site in _NISSAN_SITES and _NISSAN_AUTO_RE.search(alt):
                pos = set(pos) | {"a4wd"}
                left = re.sub(r"(?:(?<=\.)|^)\s*\*?AUTO\s*(?=\.|$)", " ", left)
            d = _drive_allowed(pos, neg)
            fams = {("4" if set(d) <= _FOUR else "2")} & T_fams if d and "*" not in T_fams else set(T_fams)
            tr = _trans_terms(text)
            trs = (tr & T_trans) if len(tr) == 1 else set(T_trans)
            left = _AUTO_RE.sub(" ", _MANUAL_RE.sub(" ", left))
            out.append((alt.lstrip().startswith("*"), frozenset(_clause_tokens(left)),
                        {(f, t) for f in fams for t in trs}, len(tr) == 1))
        return out

    def option_tie(self, c, cat, T, gate) -> dict | None:
        """Decision 5 (config-tuple option columns, policy.DRIVE_CONFIG_FVO_SITES):
        the (drive family, transmission) pairs T comes in (T's pages' drive
        systems and transmissions) that the vehicle-year's gates let through
        but no configuration of the number covers; a configuration that names
        no transmission loses the one a same-part sibling on the page lists
        for the same or a broader configuration under the same mark (G35
        2008 24820-JK61D 'S. AWD' beside JK61B 'S. 6MT': 6MT sedans take
        JK61B). None when the gates cover it, T comes in one transmission, or
        the rows are not config-tuple columns. Else {uncovered, via, fit}:
        via 'own' when the number's configurations alone leave the pairs out
        (Xterra 2013 96302-EA000 'W. 2WD + W. S. 6MT': no 4WD automatic),
        'sibling' when only a sibling's transmission does; fit the gate
        that would express it when the pairs left form one (drive x trans)."""
        Tr = set(self._t_trans_seen(T))
        if len(Tr) < 2:
            return None
        own = self._own_list_or_seed(c, cat, T)
        if not own or any(st not in policy.DRIVE_CONFIG_FVO_SITES for _n, st, _u, _p in own):
            return None
        sysT = self._t_drive_systems(T)
        F = ({"2"} if sysT & _TWO else set()) | ({"4"} if sysT & _FOUR else set()) or {"*"}

        def nm(s):
            return re.sub(r"\s+", " ", str(s or "").strip().lower())
        # T's page in cat: its list rows, else the records seeded there (G35
        # 2008: the page is in the raw as records only), as (pn, notes, site,
        # url, part identity)
        if self.t_list_rows.get((T, cat)):
            page = [(lr.pn, lr.notes, lr.site, lr.list_url, (nm(lr.main), tuple(sorted(nm(x) for x in lr.locations))))
                    for lr in self.t_list_rows[(T, cat)]]
        else:
            page = [(r.pn, r.note_texts, r.site, r.list_url, (nm(r.name), nm(r.position or r.list_location)))
                    for r in self.t_seed_records.get((T, cat), [])]
        A_own, A = set(), set()
        for notes, site, url, pn in own:
            me = next((x for x in page if x[3] == url and x[0] == pn), None)
            sibs = []
            if me is not None:
                for spn, snotes, ssite, surl, sid in page:
                    k2 = policy.pn_key(self.ns, spn)
                    if k2 == c.key or surl != url or sid != me[4] or \
                            self.comparable(cat, c.key, k2) or self.note_excludes(snotes, T):
                        continue
                    rw, sw = _row_windows(notes), _row_windows(snotes)
                    if rw and sw and not any(_win_overlap(sw, a, b) for a, b in rw):
                        continue
                    sibs.append(self._tie_cfgs(snotes, ssite, F, Tr))
            for star, toks, pairs, named in self._tie_cfgs(notes, site, F, Tr):
                A_own |= pairs
                keep = set(pairs)
                if not named:
                    for scf in sibs:
                        # a sibling that also lists this configuration with no
                        # transmission is an alternative number, not a split
                        if any(s2 == star and t2 <= toks and not n2 for s2, t2, _p2, n2 in scf):
                            continue
                        for s2, t2, p2, n2 in scf:
                            if n2 and s2 == star and t2 <= toks:
                                keep -= p2
                A |= keep
        gd = gate.get("drive")
        if gd:
            dd = set(str(gd).split("/"))
            Gd = ({"2"} if dd & _TWO else set()) | ({"4"} if dd & _FOUR else set())
            Gd = Gd & F or F
        else:
            Gd = set(F)
        Gt = {{"MT": "manual", "AT": "auto"}[gate["trans"]]} if gate.get("trans") else set(Tr)
        G = {(f, t) for f in Gd for t in Gt}
        if G <= A:
            return None
        left = A & G
        fit = None
        fs, ts = {f for f, _t in left}, {t for _f, t in left}
        if left and left == {(f, t) for f in fs for t in ts}:
            fit = {"drive": sorted(fs) if fs != Gd else None, "trans": sorted(ts) if ts != Gt else None}
        return {"uncovered": sorted(G - A), "via": "own" if not G <= A_own else "sibling", "fit": fit}

    # ------------------------------ round9-1119 (hub 2026-11-19 after 1119i)
    def _group_brand(self, c, default):
        """C: 'Infiniti' when every record of the class comes from the
        Infiniti site, 'Nissan' from the Nissan site, 'Nissan/Infiniti' when
        both."""
        bs = sorted({_SITE_BRAND.get(r.site, default) for r in c.records})
        return "/".join(bs) if bs else default

    def _class_names(self, c, cat) -> list:
        """[(name, 'site:file:Lline')] the catalog prints for the number: the
        list rows' part name on every page and the product records' name."""
        out = set()
        for lr in self._pn_list_rows(c.key, cat):
            if lr.main and lr.main.strip():
                out.add((lr.main.strip().rstrip(","), f"{lr.site}:lists:L{lr.line}"))
        for r in c.records:
            for n in r.oem_names:
                if n and n.strip():
                    out.add((n.strip().rstrip(","), r.pointer))
        return sorted(out)

    def _name_class(self, c, cat) -> dict:
        """A: {class, names, hold}. class 'motor' / 'regulator' (window-
        regulator), 'assembly' (the category's own assembly), 'component';
        hold a reason when the names mix a motor and a regulator, name another
        component, or none is in the raw."""
        names = self._class_names(c, cat)
        heads = sorted({re.sub(r"\s+", " ", n.split(",")[0]).strip() for n, _p in names})
        kinds = set()
        for h in heads:
            if cat == "window-regulator" and _NAME_MOTOR_RE.match(h):
                kinds.add("motor")
            elif cat == "window-regulator" and _NAME_REG_RE.match(h):
                kinds.add("regulator")
            elif _NAME_COMPONENT_RE.match(h) and not (cat == "wiper-motor" and re.match(r"\s*(motor|drive)\b", h, re.I)):
                kinds.add("component")
            else:
                kinds.add("assembly")
        out = {"names": [{"name": n, "ref": p} for n, p in names], "class": "/".join(sorted(kinds)) or None,
               "hold": None}
        if not names:
            out["hold"] = "no catalog part name in the raw"
        elif kinds == {"motor", "regulator"} or len(kinds) > 1:
            out["hold"] = "the names mix " + " and ".join(sorted(kinds)) + ": " + "; ".join(heads)[:200]
        elif kinds == {"component"}:
            out["hold"] = "a component, not the assembly the category names: " + "; ".join(heads)[:200]
        return out

    def _note_pack(self, c, cat) -> str:
        """The packaging the note words: 'motor' where every catalog name of a
        nissan window-regulator number is 'Motor Assy-...' (A), else the
        class's packaging."""
        if self.ns in ROUND9_NS and cat == "window-regulator":
            cache = self.__dict__.setdefault("_note_pack_c", {})
            if (c.key, cat) not in cache:
                cache[(c.key, cat)] = "motor" if self._name_class(c, cat)["class"] == "motor" else c.packaging
            return cache[(c.key, cat)]
        return c.packaging

    def _wide_names(self, c, cat) -> list:
        """round10b: [(field, name, 'site:file:Lline')] every naming field the
        raw prints for the number: list rows on every page (main, aux) and the
        product records (name, aux, description, other_names), each
        ';'-separated value on its own."""
        out = set()
        for lr in self._pn_list_rows(c.key, cat):
            for fld in ("main", "aux"):
                for n in str(getattr(lr, fld, "") or "").split(";"):
                    if n.strip():
                        out.add((f"list.{fld}", n.strip(), f"{lr.site}:lists:L{lr.line}"))
        for r in c.records:
            for fld in ("name", "aux", "description", "other_names"):
                for n in str(getattr(r, fld, "") or "").split(";"):
                    if n.strip():
                        out.add((f"record.{fld}", n.strip(), r.pointer))
        return sorted(out)

    def _name_disagree(self, c, cat) -> dict | None:
        """round10b: {'kinds', 'names'} when the number's names disagree in
        kind (a motor beside a regulator or regulator-with-motor), else None."""
        names = self._wide_names(c, cat)
        kinds = {k for _f, n, _p in names if (k := _kind10b(n))}
        if "motor" in kinds and kinds & {"regulator", "regulator+motor"}:
            return {"kinds": sorted(kinds),
                    "names": [{"field": f, "name": n, "ref": p_, "kind": _kind10b(n) or None} for f, n, p_ in names]}
        return None

    def _r11_words(self, c, cat, note, slot) -> dict | None:
        """round11: None when the round adds nothing and holds nothing for the
        group, else {kinds, names, phrase | hold, reinf}."""
        names = self._wide_names(c, cat)
        vals = [{"field": f, "name": n, "ref": p_, "kind": _kind11(cat, n) or None} for f, n, p_ in names]
        kinds = sorted({v["kind"] for v in vals if v["kind"]})
        out = {"kinds": kinds, "names": vals}
        has_now = [w for w in PACK_TEXT.values() if f"— {w}; " in note]
        if cat in ("bumper-front", "bumper-rear"):
            if not set(kinds) & {"cover", "guard"}:
                return None
            if len(kinds) > 1:
                out["hold"] = ("held_name_disagree", "the names disagree in kind (" + "/".join(kinds) + ")")
            elif kinds == ["guard"]:
                out["phrase"] = _R11_PHRASE["guard"]
            else:
                urls = sorted({lr.list_url for lr in self._pn_list_rows(c.key, cat) if lr.list_url})
                idx = self.__dict__.get("_rows_by_url")
                if idx is None:
                    idx = defaultdict(list)
                    for lr in self.list_rows:
                        idx[lr.list_url].append(lr)
                    self._rows_by_url = idx
                reinf = {u: sorted({f"{o.pn} {o.main}".strip() for o in idx[u]
                                    if policy.pn_key(self.ns, o.pn) != c.key
                                    and re.search(r"reinf", f"{o.main} {o.aux}", re.I)}) for u in urls}
                out["reinf"] = reinf
                out["phrase"] = _R11_PHRASE["cover_only"] if urls and all(reinf.values()) else _R11_PHRASE["cover"]
            return out
        if cat == "tail-lights":
            if "lens-body" not in kinds:
                return None
            if len(kinds) > 1:
                out["hold"] = ("held_name_disagree", "the names disagree in kind (" + "/".join(kinds) + ")")
            else:
                out["phrase"] = _R11_PHRASE["lens-body"]
            return out
        # window-regulator
        if "motor" in kinds and set(kinds) & {"regulator", "regulator+motor"}:
            out["hold"] = ("held_name_disagree", "the names disagree in kind (" + "/".join(kinds) + ")")
            return out
        if "regulator+motor" in kinds and any(re.search(r"\b(?:w/o|without|less)\s*motor\b", v["name"], re.I)
                                              for v in vals):
            out["hold"] = ("held_name_disagree", "one name has the motor, another says without it")
            return out
        # the product record's part name carries the motor (GM's full catalog
        # name "REGULATOR, ... (INCLUDES MOTOR)" beside its list row's bare
        # "REGULATOR"); with no record, every list row's name must say it
        rec = [v["kind"] for v in vals if v["field"] == "record.name"]
        lst = [v["kind"] for v in vals if v["field"] == "list.main"]
        if (rec and all(k == "regulator+motor" for k in rec) and all(k in ("regulator+motor", "regulator") for k in lst)) \
                or (not rec and lst and all(k == "regulator+motor" for k in lst)):
            if _R11_PHRASE["regulator+motor"] in has_now:
                return None
            if has_now:
                out["hold"] = ("held_part_name", "regulator with motor by name, the note says '" + has_now[0] + "'")
            else:
                out["phrase"] = _R11_PHRASE["regulator+motor"]
            return out
        return None

    def _r10_class(self, c, cat) -> dict:
        """round10: 'motor' / 'regulator' from every catalog name the raw prints
        for the number (list rows on every page, product records); 'mixed' when
        both, 'other' when a name is neither, None (held) with no name."""
        names = self._class_names(c, cat)
        heads = sorted({re.sub(r"\s+", " ", n.split(",")[0]).strip() for n, _p in names})
        kinds = {"motor" if _R10_MOTOR_RE.match(h) else "regulator" if _R10_REG_RE.match(h) else "other"
                 for h in heads}
        cls = None if not kinds else "mixed" if {"motor", "regulator"} <= kinds else \
            "other" if "other" in kinds else kinds.pop()
        hold = None if cls in ("motor", "regulator") else \
            "no catalog part name in the raw" if cls is None else \
            ("the names mix a motor and a regulator: " if cls == "mixed" else "a name is neither a motor nor a "
             "regulator: ") + "; ".join(heads)[:160]
        return {"class": cls, "names": [{"name": n, "ref": p_} for n, p_ in names], "heads": heads, "hold": hold}

    def round9_tests(self, c, cat, T, gate) -> list:
        """B1-B4 for one vehicle-year: [(reason, detail)]."""
        out = []
        rows = self.t_list_rows.get((T, cat)) or []
        # B1: the year index's variant pages (the hybrid aside: the gas gate
        # and its words cover it) that no list page of T in cat comes from
        offered = set()
        for ym in self.t_years.get(T, []):
            for v in [ym.variant] + list(ym.variants or []):
                if v and "hybrid" not in str(v).lower():
                    offered.add(str(v).lower())
        if len(offered) > 1 and rows:
            read = set()
            for lr in rows:
                slug = (lr.list_url or "").lower()
                read |= {v for v in offered if v == str(lr.variant or "").lower() or re.search(
                    r"-" + re.escape(v) + r"(?:/|$)", slug)}
            missing = sorted(offered - read)
            if missing:
                out.append(("held_variant_unread", {"offered": sorted(offered), "read": sorted(read),
                                                    "unread": missing}))
        own = [lr for lr in rows if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched
               and not self.note_excludes(lr.notes, T)]
        if not own:
            return out
        undated = not any(_row_windows(lr.notes) for lr in own)
        lo, hi = _my_range(T[2])
        mine_cls = [(t, p, n) for lr in own for t, p, n in _row_clauses(lr.notes, lr.site)]
        mine = [set(t) for t, _p, _n in mine_cls]
        tw, bm, dv = [], [], []
        for sr in rows:
            k2 = policy.pn_key(self.ns, sr.pn)
            if k2 == c.key or not any(lr.list_url == sr.list_url and self._same_part(lr, sr) for lr in own):
                continue
            # a twin whose window overlaps T by under five months is not listed
            # for T (production rule), but its changeover still falls inside
            # T's span (27510-2B001 'from 04/1994' on the Altima 1994 page):
            # B2 reads it; every other exclusion skips the row
            prod_only = self.note_excludes(sr.notes, T) and not self.note_excludes(
                [n for n in sr.notes or [] if not re.search(r"production\s+date", n or "", re.I)], T)
            if self.note_excludes(sr.notes, T) and not prod_only:
                continue
            cls2 = _row_clauses(sr.notes, sr.site)
            theirs = [set(t) for t, _p, _n in cls2]
            sw = _row_windows(sr.notes)
            # B2 (undated number): a twin listed for our configuration or a
            # broader one that changes over inside the span, or the number's
            # own predecessor / successor listed for it undated
            covers = any(b <= a for a in mine for b in theirs)
            overlap = covers or any(a <= b for a in mine for b in theirs)
            if undated and ((covers and any(lo < a <= hi or lo <= b < hi for a, b in sw))
                            or (overlap and not sw and self.comparable(cat, c.key, k2))):
                tw.append(sr.pn)
            if prod_only:
                continue
            # B3 (both undated): the same configuration under another leading
            # body code only, the sibling listed for none of ours
            if undated and not sw and not any(set(t2) == a for a in mine for t2, _p, _n in cls2):
                for t1, _p1, _n1 in mine_cls:
                    for t2, _p2, _n2 in cls2:
                        if t1 and t2 and t1[1:] == t2[1:] and t1[0] != t2[0] and \
                                not {t1[0], t2[0]} & {"KC", "CC", "T", "FED", "CAL"}:
                            bm.append(f"{sr.pn} {t2[0]} beside {t1[0]}")
            # B4: our row names no drive and no gate reads one; a same-part
            # number lists a narrower configuration (or ours under another
            # mark) with a drive word: the pages do not say this one is the
            # other drive only
            if not gate.get("drive") and not gate.get("drive_not") and not any(p or n for _t, p, n in mine_cls):
                for t2, p2, n2 in cls2:
                    if (p2 or n2) and any(a <= set(t2) for a in mine):
                        dv.append(f"{sr.pn} {'/'.join(sorted(p2 or n2))}")
                        break
        if tw:
            out.append(("held_twin_changeover", {"twins": sorted(set(tw))}))
        if bm:
            out.append(("held_body_mark", {"marks": sorted(set(bm))[:4]}))
        if dv:
            out.append(("held_drive_open", {"siblings": sorted(set(dv))[:4]}))
        return out

    # ------------------------------ round8-1119: own pages only (hub 2026-11-19 after 1119h)
    def _round8_pre(self, c, cat, T, w):
        """(reason, detail) for a vehicle-year held before the note cap, else
        None: no list row of its own for the number in the raw (decision 1;
        the page the claim was seen on, from the records, for the crawl), or
        a build window read from another model year's page (decision 2)."""
        rows = self.t_list_rows.get((T, cat)) or []
        own = [lr for lr in rows if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched]
        if not own:
            seen = sorted({r.list_url for r in self.t_seed_records.get((T, cat), []) if r.key == c.key and r.list_url})
            return "held_no_own_page", {"page_in_raw": bool(rows), "missing_pages": seen,
                                        "claim_from": "product records" if seen else "other pages"}
        if w and w.get("src") == "other_page" and w.get("kind") != "full":
            return "held_window_other_page", {"window": _win_label(w["wins"]), "kind": w["kind"]}
        return None

    def undated_siblings(self, c, cat, T) -> list:
        """Decision 3: the other numbers T's page lists, undated, for the same
        part, position and configuration (one configuration's words inside the
        other's: 96302-6WJ0A 'S' beside 1NC3A 'S. JOURNEY'), when the number's
        own rows there are undated too; its predecessors and successors aside."""
        rows = self.t_list_rows.get((T, cat)) or []
        own = [lr for lr in rows if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched
               and not self.note_excludes(lr.notes, T)]
        if not own or any(_row_windows(lr.notes) for lr in own):
            return []
        mine = [set(t) for lr in own for t, _p, _n in _row_clauses(lr.notes, lr.site)]
        out = set()
        for sr in rows:
            k2 = policy.pn_key(self.ns, sr.pn)
            if k2 == c.key or _row_windows(sr.notes) or self.comparable(cat, c.key, k2) or \
                    self.note_excludes(sr.notes, T) or \
                    not any(lr.list_url == sr.list_url and self._same_part(lr, sr) for lr in own):
                continue
            theirs = [set(t) for t, _p, _n in _row_clauses(sr.notes, sr.site)]
            if any(a <= b or b <= a for a in mine for b in theirs):
                out.add(sr.pn)
        return sorted(out)

    def plus_dependent(self, c, cat, T, slots, gas_only=False) -> dict | None:
        """Decision 6: {dims} when the claim depends on reading '+' as 'or'
        between configurations that name different engines or drive families
        (FX50 2009 96302-1CA0A 'W. VQ35HR. PREMIUM, W. VQ35HR. PREMIUM + W.
        VK50VE': the VK50VE car is listed only through the '+'). Re-read T's
        page with every such alternative unread: the number no longer listed
        for T, or its drive / engine limit changed."""
        own = self._own_rows(c, cat, T)
        if not own or not any(st in policy.DRIVE_CONFIG_FVO_SITES for _n, st, _v, _u in own):
            return None
        v = self._star_view(c, cat, T, plus=True)
        if not v._own_rows(c, cat, T):
            return {"listing": "the number is listed for this vehicle-year only through a '+' joining "
                               "configurations of different engines or drives"}
        full, alt = self._scopes(c, cat, T, slots, gas_only), v._scopes(c, cat, T, slots, gas_only)
        dims = {k: (self._scope_text(k, full[k]), self._scope_text(k, alt[k])) for k in full if full[k] != alt[k]}
        return {"scope": dims} if dims else None

    # ------------------------------ round5b-1119: starred clauses (hub 2026-11-19)
    # caches filled from catalog rows; a starred view starts its own
    _ROW_CACHES = ("_longer_cache", "_suspect_cache", "_gm_letters", "_seed_keys", "_fit_engines_cache",
                   "_rear_cabs", "_page_cabs", "_pn_rows", "_cat_ctx")

    def _own_starred_only(self, c, cat, T) -> bool:
        """The number is listed for T only through starred configurations: no
        own row on T's page keeps an unstarred configuration that still lists
        it for T (note_excludes; 96301-1CA0B FX35 2009 '*W. VQ35HR. PREMIUM +
        *W. VK50VE, W. VK50VE': the unstarred 'W. VK50VE' names the FX50's
        engine only). Leaving the starred configurations out would remove
        the claim, not narrow its scope."""
        rows = self.t_list_rows.get((T, cat))
        if rows:
            own = [(lr.notes, lr.site) for lr in rows if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched
                   and not self.note_excludes(lr.notes, T)]
        else:
            own = [(r.note_texts, r.site) for r in self.t_seed_records.get((T, cat), [])
                   if r.key == c.key and not self.note_excludes(r.note_texts, T)]
        left = [n2 for n, st in own for n2 in [_unstar_notes(n, st)] if n2 is not None]
        return bool(own) and not any(not self.note_excludes(n2, T) for n2 in left)

    def _star_view(self, c, cat, T, siblings=True, blind=False, plus=False):
        """This curation with T's page rows in cat (the only rows T's drive and
        engine limits read) re-read for STARRED_SCOPE_NS: starred
        configurations are left out (_unstar_notes; a row with nothing
        unstarred left is gone), the other numbers' only when siblings is
        True. Where the number is listed for T only through starred
        configurations (_own_starred_only), leaving them out would remove the
        claim itself, not its scope, so there its own starred configurations
        stay, with their drive and engine words unread (_unstate_notes); a
        number those words alone list for T is then not listed (_UNLISTED,
        _scopes). What the model-year comes in (the drive
        systems, engines and transmissions T's pages name in every category)
        is read from every row as printed: it describes the car, not what this
        number fits."""
        v = copy.copy(self)
        for k in self._ROW_CACHES:
            v.__dict__.pop(k, None)
        v._t_drive_systems, v._t_engines, v._t_trans_seen = self._t_drive_systems, self._t_engines, \
            self._t_trans_seen
        unstate = self._own_starred_only(c, cat, T)
        if blind or plus:
            # round7-1119 (hub decision 5): every configuration read without
            # its mark (as round 4 read them), own and siblings'; round8:
            # every '+' joining different engines or drives unread
            unstate = None

        def re_read(o, attr, own):
            notes = getattr(o, attr)
            if plus:
                n2 = _plus_strict_notes(notes, o.site)     # round8 decision 6
            elif blind:
                n2 = _blind_notes(notes, o.site)
            elif own:
                n2 = _unstate_notes(notes, o.site) if unstate else _unstar_notes(notes, o.site)
            elif siblings:
                n2 = _unstar_notes(notes, o.site)
            else:
                return o
            if n2 is None:
                return None
            if n2 == list(notes or []):
                return o
            o2 = copy.copy(o)
            setattr(o2, attr, n2)
            return o2
        k = (T, cat)
        lrs = [re_read(lr, "notes", policy.pn_key(self.ns, lr.pn) == c.key) for lr in self.t_list_rows.get(k) or []]
        recs = [re_read(r, "note_texts", r.key == c.key) for r in self.t_seed_records.get(k) or []]
        v.t_list_rows = ChainMap({k: [x for x in lrs if x is not None]}, self.t_list_rows)
        v.t_seed_records = ChainMap({k: [x for x in recs if x is not None]}, self.t_seed_records)
        return v

    def drive_scope(self, c, cat, T, slots):
        """The drive limit likely_groups gives class c on T, as one value:
        (drive classes or None, drive_not classes or None, part-time 4WD), or
        DRIVE_AMBIGUOUS when T is left out (the drive rule, drive_material and
        the same-option drive sibling rule, in likely_groups' order)."""
        d = None
        if policy.LIKELY_DRIVE_RULE:
            d = self.drive_of(c, cat, T)
            if d and d != DRIVE_AMBIGUOUS:
                mat = self.drive_material(T, d)
                if mat is False:
                    d = None
                elif mat == DRIVE_AMBIGUOUS:
                    d = DRIVE_AMBIGUOUS
            if d == DRIVE_AMBIGUOUS:
                return DRIVE_AMBIGUOUS
        dnot = None
        sl = self.drive_sibling_limit(c, cat, T) if policy.LIKELY_DRIVE_RULE else None
        if sl and sl[0] == "drive":
            mat = self.drive_material(T, sl[1])
            if mat is False:
                sl = None
            elif mat == DRIVE_AMBIGUOUS:
                sl = (DRIVE_AMBIGUOUS, None)
        if sl and sl[0] == DRIVE_AMBIGUOUS:
            return DRIVE_AMBIGUOUS
        if sl:
            if sl[0] == "drive":
                fam = _FOUR if set(sl[1]) <= _FOUR else _TWO
                if d and not set(d) <= fam:
                    return DRIVE_AMBIGUOUS
                if not d:
                    d = frozenset(sl[1])
            elif d:
                d = frozenset(set(d) - set(sl[1]))
                if not d:
                    return DRIVE_AMBIGUOUS
            else:
                dnot = frozenset(sl[1])
        pt = bool(d) and set(d) == {"4wd"} and self._auto_sibling(c, cat, T, slots)
        return (frozenset(d) if d else None, dnot, pt)

    def _scopes(self, c, cat, T, slots, gas_only, base=None):
        out = {"drive": self.drive_scope(c, cat, T, slots), "engine": self.engine_trans_of(c, cat, T, gas_only)[0]}
        if base is not None and base._own_starred_only(c, cat, T) and not self._own_rows(c, cat, T):
            # the number is no longer listed for T once its starred
            # configurations' drive and engine words are unread: those words
            # are what list it (96301-1CA0B FX35 '*W. VQ35HR. PREMIUM')
            for k in _starred_dims(base._own_rows(c, cat, T)):
                out[k] = _UNLISTED
        return out

    def starred_scope(self, c, cat, T, slots, gas_only=False):
        """STARRED_SCOPE_NS: {dimension: (as curated, re-read, via)} for
        'drive' and 'engine' where re-reading T's page without the starred
        configurations (_star_view) changes T's limit (DRIVE_AMBIGUOUS: T would
        be left out; _UNLISTED: no longer listed for T); via 'own' when
        re-reading the number's own rows alone changes it, else 'sibling'
        (only another number's starred configuration decides). {} when no
        starred configuration decides either."""
        full = self._scopes(c, cat, T, slots, gas_only)
        alt = self._star_view(c, cat, T)._scopes(c, cat, T, slots, gas_only, base=self)
        dims = [k for k in full if full[k] != alt[k]]
        if not dims and getattr(self, "_r7", True):
            # round7-1119 (hub decision 5): the mark decides when reading the
            # starred configurations as plain ones changes the limit (96301-
            # 3JA9A 'W. BASE' beside 3JN9B '*W. AWD. BASE': read without the
            # mark, the AWD base car takes 3JN9B and 3JA9A is 2WD only)
            bl = self._star_view(c, cat, T, blind=True)._scopes(c, cat, T, slots, gas_only)
            return {k: (full[k], bl[k], "star_blind") for k in full if full[k] != bl[k]}
        if not dims:
            return {}
        own = self._star_view(c, cat, T, siblings=False)._scopes(c, cat, T, slots, gas_only, base=self)
        return {k: (full[k], alt[k], "own" if own[k] != full[k] else "sibling") for k in dims}

    @staticmethod
    def _scope_text(dim, v):
        if v == _UNLISTED:
            return "not listed (only a starred configuration's " + dim + " words list the number)"
        if v == DRIVE_AMBIGUOUS:
            return "left out (contradicts itself)"
        if dim == "engine":
            return v or "no limit"
        d, dnot, pt = v
        if d:
            return ("part-time 4WD" if pt else _drive_label(d)) + " only"
        return f"not {_drive_label(dnot)}" if dnot else "no limit"

    def _starred_entry(self, c, cat, Ts0, held, unit, only_T=(), kept=None) -> dict:
        """One group's line of the held list (groups/_report/<ns>.starred_held.json).
        kinds: a = a drive gate a starred configuration decides, b = an engine
        gate, c_drive / c_engine = no gate, and re-reading without the starred
        configurations would add one (or leave the vehicle-year out);
        starred_only (round6-1119, hub decision 2) = the number is listed for
        T only through starred configurations. reasons per vehicle-year:
        held_starred_scope / held_starred_only. kept_apps: what the group
        ships after every round-5b / round-6 hold."""
        yrs = []
        for T in sorted(set(held) | set(only_T)):
            sc = held.get(T, {})
            kinds = []
            if "drive" in sc:
                fd = sc["drive"][0]
                kinds.append("a" if fd != DRIVE_AMBIGUOUS and (fd[0] or fd[1]) else "c_drive")
            if "engine" in sc:
                kinds.append("b" if sc["engine"][0] else "c_engine")
            if T in only_T:
                kinds.append("starred_only")
            yrs.append({"t": list(T), "kinds": kinds,
                        "reasons": (["held_starred_scope"] if sc else []) + (["held_starred_only"] if T in only_T else []),
                        "listed_only_starred": self._own_starred_only(c, cat, T),
                        **{dim: {"as_curated": self._scope_text(dim, f), "without_starred": self._scope_text(dim, u),
                                 "via": via}
                           for dim, (f, u, via) in sorted(sc.items())},
                        "clauses": self._starred_evidence(c, cat, T, set(sc))})
        kept = [T for T in Ts0 if T not in held and T not in set(only_T)] if kept is None else kept
        return {"cat": cat, "pn": sorted(c.pns), "unit": unit,
                "reason": "held_starred_scope" if held else "held_starred_only",
                "reason_text": "starred clause decides scope" if held else "claim rests only on starred clauses",
                "round5_apps": _runs(Ts0), "kept_apps": [] if unit == "group" else _runs(kept),
                **({"group_reason": self._unit_why} if unit == "group" else {}), "held": yrs}

    _ROUND6_TEXT = {"held_cab_inferred": "cab limit not on the number's own row",
                    "held_option_tie": "option text ties the part to a transmission the gates do not enforce"}

    def _round6_entry(self, c, cat, Ts0, r6_T, kept, unit, slots) -> dict:
        """One group's line of groups/_report/<ns>.round6_held.json: the
        vehicle-years held by round6-1119 decisions 1 (held_cab_inferred) and
        5 (held_option_tie), each with the number's own option notes on T's
        page and, for a tie, the sibling rows on the page."""
        yrs = []
        for T, rs in sorted(r6_T.items()):
            own = self._own_list_or_seed(c, cat, T)
            y = {"t": list(T), "reasons": [r for r, _d in rs],
                 "own_rows": [{"pn": p, "page": u, "notes": [n for n in nt if not _CLAUSE_SKIP_RE.match(n or "")
                                                             or _PROD_FIELD_RE.match(n or "")]}
                              for nt, _s, u, p in own]}
            for r, d in rs:
                if r == "held_cab_inferred":
                    y["cab_gate"] = d["cab"]
                    y["cab_source"] = "rear_cab_of (rear-door part read as crew cab from the page's cab split)" \
                        if self.rear_cab_of(c, cat, T, slots) else \
                        "another year's or the model's evidence, not this vehicle-year's own rows"
                else:
                    y["tie"] = {"uncovered": [f"{'2WD' if f == '2' else '4WD/AWD' if f == '4' else 'any drive'} "
                                              f"{'manual' if t == 'manual' else 'automatic'}" for f, t in d["uncovered"]],
                                "via": d["via"], "a_gate_would_fit": d["fit"]}
                    urls = {u for _n, _s, u, _p in own}
                    pg = [(lr.pn, lr.notes, lr.list_url) for lr in self.t_list_rows.get((T, cat)) or []] or \
                        [(r.pn, r.note_texts, r.list_url) for r in self.t_seed_records.get((T, cat)) or []]
                    y["siblings"] = [{"pn": spn, "notes": [n for n in sn if _FVO_BODY_RE.match(n or "")]}
                                     for spn, sn, su in pg
                                     if su in urls and policy.pn_key(self.ns, spn) != c.key
                                     and any(_trans_terms(n) for n in sn if _FVO_BODY_RE.match(n or ""))][:12]
            yrs.append(y)
        reasons = sorted({r for rs in r6_T.values() for r, _d in rs})
        return {"cat": cat, "pn": sorted(c.pns), "unit": unit, "reasons": reasons,
                "reason_text": "; ".join(self._ROUND6_TEXT[r] for r in reasons),
                "round5_apps": _runs(Ts0), "kept_apps": [] if unit == "group" else _runs(kept),
                **({"group_reason": self._unit_why} if unit == "group" else {}), "held": yrs}

    def _starred_evidence(self, c, cat, T, dims=()) -> list:
        """The number's own option notes on T's page (with its starred
        configurations), and, for the dimensions decided (dims), the sibling
        rows the drive / engine sibling rules read, as printed and re-read."""
        k = (T, cat)
        rows = list(self.t_list_rows.get(k) or []) or list(self.t_seed_records.get(k) or [])

        def pn_of(o):
            return getattr(o, "pn", None) or sorted(c.pns)[0]

        def notes_of(o):
            return o.notes if isinstance(o, A.ListRow) else o.note_texts

        def key_of(o):
            return o.key if not isinstance(o, A.ListRow) else policy.pn_key(self.ns, o.pn)
        out = [{"pn": pn_of(o), "role": "own", "page": o.list_url,
                "notes": [n for n in notes_of(o) if _FVO_BODY_RE.match(n or "")],
                "starred": _starred_cfgs(notes_of(o), o.site)}
               for o in rows if key_of(o) == c.key and getattr(o, "matched", True)
               and not self.note_excludes(notes_of(o), T)]
        keys = set()
        for view in (self, self._star_view(c, cat, T), self._star_view(c, cat, T, blind=True)):
            if "drive" in dims:
                keys |= {(h[1].list_url, h[1].pn) for h in view.drive_sibling(c, cat, T)[1]}
            if "engine" in dims:
                members = (view.cells_info.get(k) or {}).get("members") or {}
                me = members.get(c.key)
                for k2, m in members.items():
                    if not me or k2 == c.key or not (set(m["slot"].slots) & set(me["slot"].slots)) or \
                            view.comparable(cat, c.key, k2):
                        continue
                    for o in list(view.t_list_rows.get(k) or []) or list(view.t_seed_records.get(k) or []):
                        if key_of(o) == k2 and getattr(o, "matched", True) and \
                                _row_engine_trans(notes_of(o), o.site)[0]:
                            keys.add((o.list_url, pn_of(o)))
        out += [{"pn": pn_of(o), "role": "sibling", "page": o.list_url,
                 "notes": [n for n in notes_of(o) if _FVO_BODY_RE.match(n or "")],
                 "starred": _starred_cfgs(notes_of(o), o.site)}
                for o in rows if key_of(o) != c.key and (o.list_url, pn_of(o)) in keys]
        return out

    def build_window(self, c, cat, T):
        """policy.LIKELY_BUILD_WINDOW_RULE (hub decisions 2 and 3,
        2026-11-19). None when this number's own rows on T's pages print no
        window inside T's model year, else a dict:
          wins   the window(s) (months), merged
          src    'page' (T's own rows) or 'other_page' (decision 3: T's page
                 prints no date, another model-year page of the same catalog
                 model prints a window for the number; the narrower reading)
          gap    [(a, b)] months of the model year outside the window
          kind   'full' (no gap) | 'drop' (src other_page and under
                 _PROD_MIN_MONTHS of the model year: not listed, as if T's page
                 printed it) | 'no_other_row' (no dated row of the same part
                 carries the gap) | 'linked' (every row that does is this
                 number's predecessor or successor; gated since round5) |
                 'unlinked' | 'no_page' (T's page is not in the raw: the rest
                 of the year unknown)
          others [(pn, wins, linked)] the dated rows carrying the gap
          edge   the gap is 1-2 months at a model-year edge
        'linked', 'unlinked' and 'no_page' become a window limit (round5:
        "Replaced By" runs one way); 'drop' leaves T out."""
        if not policy.LIKELY_BUILD_WINDOW_RULE or cat in PROD_RULE_SKIP_CATS:
            return None
        self._cat_ctx = cat
        rows = self.t_list_rows.get((T, cat)) or []
        if rows:
            own = [lr for lr in rows if policy.pn_key(self.ns, lr.pn) == c.key and lr.matched
                   and not self.note_excludes(lr.notes, T)]
            items = [(lr.notes, lr) for lr in own]
        else:
            items = [(r.note_texts, None) for r in self.t_seed_records.get((T, cat), [])
                     if r.key == c.key and not self.note_excludes(r.note_texts, T)]
        if not items:
            return None
        per = [_row_windows(n) for n, _lr in items]
        src = "page"
        sites = {lr.site for _n, lr in items if lr is not None} or {r.site for r in c.records}
        models = {(lr.seed[0], lr.seed[1]) for _n, lr in items if lr is not None and lr.seed} or \
            set(self.t_sources.get(T, set()))
        r7 = getattr(self, "_r7", True)
        r7_kind = None
        if r7 and any(per):
            # round7-1119 (hub decision 1): the cut test runs on each page that
            # lists the number (body variants: the 2007 Versa sedan page dates
            # 80730-89915 12/2006-07/2007, the hatchback page 05/2006-01/2007),
            # never on their union. A page with an undated row covers the year;
            # when a dated page cuts the span, the gate is the months every
            # dated page lists (the narrower reading); pages with no month in
            # common leave the vehicle-year out.
            pages = defaultdict(list)
            for (n, lr0), ws in zip(items, per):
                pages[lr0.list_url if lr0 is not None else None].append(ws)
            dated = [_win_merge([x for ws in v for x in ws]) for v in pages.values() if all(v)]
            if not dated:
                return None         # every page has a dateless row: listed for the whole year
            if any(_win_gap(w, T[2]) for w in dated):
                wins = dated[0]
                for w in dated[1:]:
                    wins = _win_intersect(wins, w)
                if len(dated) > 1:
                    r7_kind = "pages"
                if not wins:
                    return {"wins": _win_merge([x for w in dated for x in w]), "src": "page", "gap": [],
                            "others": [], "edge": False, "kind": "drop", "r7": "pages_disjoint"}
            elif all(per):
                wins = _win_merge([w for ws in per for w in ws])
            else:
                wins = _win_merge([x for w in dated for x in w])
                r7_kind = "dated_page_covers"
        elif all(per):
            wins = _win_merge([w for ws in per for w in ws])
        elif any(per):
            return None             # a dateless own row: listed for the whole year
        else:
            # decision 3: the same catalog model's other model-year pages
            # round5-1119 (hub decisions 1-2): the window is read from the
            # NUMBER's dated rows on the catalog model's other model-year
            # pages, whatever their option clause (Sentra 2004 82730-3Z005:
            # the 2004 rows carry a clause, the 2005 dated rows none), and a
            # predecessor / successor on T's page no longer exempts it
            # ("Replaced By" runs one way). Pages within _OTHER_PAGE_SPAN
            # model years of T (None: every year of the model).
            other = self._pn_other_windows(c.key, cat, T, sites, models, c.records)
            if r7:
                # round7-1119 (hub decision 3): T's page lists the number
                # undated beside a same-option sibling, and another page (any
                # model of the site: 80721-EA000 / ZL90A split at 04/2010 on the
                # 2010-2011 Pathfinder and Xterra pages, the Frontier pages date
                # neither) dates the split: the narrower reading, gated
                split, cross = self._split_windows(c, cat, T, self._same_option_sibs(c, cat, T, items), sites)
                if split:
                    # the model's own pages' window when they date the number
                    # (decision 6 reading), else the pages that show the split
                    other = other or cross
                    r7_kind = "split"
            if not other:
                return None
            wins, src = _win_merge(other), "other_page"
        lo, hi = _my_range(T[2])
        out = {"wins": wins, "src": src, "gap": _win_gap(wins, T[2]), "others": [], "edge": False}
        if r7_kind:
            out["r7"] = r7_kind
        if src == "other_page" and _win_overlap(wins, lo, hi) < _PROD_MIN_MONTHS:
            out["kind"] = "drop"
            return out
        if not out["gap"]:
            if r7 and r7_kind == "split":
                out["kind"] = "split"
                return out
            if r7 and src == "page":
                # round7-1119 (hub decision 2): a changeover month with a
                # same-option number on the page inside the model-year span,
                # widened a month either way for the 07-06 convention (FX35
                # 2006 80721-CL00A to 06/2006, CL70B from 06/2006): gated
                # on both sides
                co = self._changeover(items, self._same_option_sibs(c, cat, T, items), T)
                if co:
                    out["kind"], out["changeover"] = "changeover", co
                    return out
            out["kind"] = "full"
            return out
        months = sum(b - a + 1 for a, b in out["gap"])
        out["edge"] = months <= 2 and all(a == lo or b == hi for a, b in out["gap"])
        # the rest of the year's builds of the SAME configuration: a dated row
        # of the same part and position whose option clause is one of ours
        # (drive words and asterisks aside; a row with no option text covers
        # every configuration). Another colour or package is another car.
        mine = {t for n, lr0 in items if lr0 is not None for t, _p, _n2 in _row_clauses(n, lr0.site)}
        others = []
        for lr in rows:
            k2 = policy.pn_key(self.ns, lr.pn)
            if k2 == c.key or not any(lr0 is not None and lr0.list_url == lr.list_url and self._same_part(lr0, lr)
                                      for _n, lr0 in items):
                continue
            theirs = {t for t, _p, _n2 in _row_clauses(lr.notes, lr.site)}
            if not (mine & theirs or () in mine or () in theirs):
                continue
            # an undated row of the same part on T's page: its window from the
            # model's other model-year pages (round5: Q70 2015 80720-1MA0A /
            # 1MA0B, both undated on the 2015 page, dated on the 2016 page)
            ow = _row_windows(lr.notes) or self._pn_other_windows(k2, cat, T, sites, models)
            if ow and any(_win_overlap(ow, a, b) for a, b in out["gap"]):
                others.append((lr.pn, _win_merge(ow), self.comparable(cat, c.key, k2)))
        out["others"] = sorted(set((p, tuple(w), lk) for p, w, lk in others))
        if not rows:
            # T's page in this category is not in the raw (the record's seed-
            # page notes only): nothing shows the rest of the year is this
            # number's own predecessor or successor, so the window stands
            out["kind"] = "no_page"
        elif not others:
            out["kind"] = "no_other_row"
        elif all(lk for _p, _w, lk in others):
            out["kind"] = "linked"
        else:
            out["kind"] = "unlinked"
        return out

    def _same_option_sibs(self, c, cat, T, items) -> list:
        """Rows of other numbers on T's page in cat for the same part and
        position whose option clause is one of ours (build_window's test:
        drive words and asterisks aside; a row with no option text covers
        every configuration)."""
        rows = self.t_list_rows.get((T, cat)) or []
        mine = {t for n, lr0 in items if lr0 is not None for t, _p, _n2 in _row_clauses(n, lr0.site)}
        out = []
        for lr in rows:
            if policy.pn_key(self.ns, lr.pn) == c.key or not any(
                    lr0 is not None and lr0.list_url == lr.list_url and self._same_part(lr0, lr) for _n, lr0 in items):
                continue
            theirs = {t for t, _p, _n2 in _row_clauses(lr.notes, lr.site)}
            if mine & theirs or () in mine or () in theirs:
                out.append(lr)
        return out

    @staticmethod
    def _adjacent(W, SW):
        """The changeover month when one window list ends where the other
        starts (the same month or the next): (month, 'end' | 'start'), else None."""
        for a, b in W:
            for a2, b2 in SW:
                if b < _WIN_OPEN and a2 > 0 and a2 in (b, b + 1):
                    return b, "end"
                if a > 0 and b2 < _WIN_OPEN and b2 in (a, a - 1):
                    return a, "start"
        return None

    def _changeover(self, items, sibs, T):
        """Round7 decision 2: '<mm/yyyy> <sibling pn>' when the number's own
        dated row on T's page and a same-option sibling on that page change
        over in a month inside T's model-year span widened a month either way
        (07/(y-1)-06/y +- 1)."""
        lo, hi = _my_range(T[2])
        for n, lr0 in items:
            if lr0 is None:
                continue
            W = _row_windows(n)
            for s in sibs:
                if s.list_url != lr0.list_url:
                    continue
                adj = self._adjacent(W, _row_windows(s.notes))
                if adj and lo - 1 <= adj[0] <= hi + 1:
                    return f"{_mm(adj[0])} {s.pn}"
        return None

    def _split_windows(self, c, cat, T, sibs, sites):
        """Round7 decision 3: (split, windows). split: the number's dated rows
        and a dated row of one of T's same-option siblings change over (one
        ends where the other starts) on the site's pages, T's own page aside
        (96302-7S600 to 08/2006 on the 2007 Titan page, 96302-ZC400 from
        08/2006 on the 2008 page). windows: the number's windows on the pages
        whose rows make that changeover, read narrowly (every page's common
        months; their union if none), for a model none of whose own pages
        dates the number (80721-EA000 on the Frontier: only the Pathfinder and
        Xterra pages date it)."""
        if not sibs:
            return None, []
        own_urls = {s.list_url for s in sibs}
        sib_keys = {policy.pn_key(self.ns, s.pn) for s in sibs}
        sw = [w for k in sib_keys for lr in self._pn_list_rows(k, cat)
              if lr.site in sites and lr.list_url not in own_urls for w in _row_windows(lr.notes)]
        if not sw:
            return None, []
        pages, split = [], None
        for lr in self._pn_list_rows(c.key, cat):
            if lr.site not in sites or lr.list_url in own_urls:
                continue
            W = _row_windows(lr.notes)
            adj = W and self._adjacent(W, sw)
            if adj:
                split = split or _mm(adj[0])
                pages.append(_win_merge(W))
        if not split:
            return None, []
        narrow = pages[0]
        for p in pages[1:]:
            narrow = _win_intersect(narrow, p)
        return split, (narrow or _win_merge([w for p in pages for w in p]))

    def _pn_other_windows(self, key, cat, T, sites, models, records=()):
        """Windows the number's dated rows print on the catalog model's other
        model-year pages (same site, same seed make/model; within
        _OTHER_PAGE_SPAN years of T, None = every year), whatever their
        option clause (round5-1119, hub decision 2)."""
        by_page = defaultdict(list)
        srcs = [(lr.site, lr.seed, lr.notes) for lr in self._pn_list_rows(key, cat)] + \
            [(r.site, r.seed, r.note_texts) for r in records]
        for site, seed, notes in srcs:
            if site in sites and seed and (seed[0], seed[1]) in models and seed[2] != T[2] \
                    and (_OTHER_PAGE_SPAN is None or abs(seed[2] - T[2]) <= _OTHER_PAGE_SPAN):
                by_page[(site, tuple(seed))] += _row_windows(notes)
        pages = [_win_merge(w) for w in by_page.values() if w]
        if not pages:
            return []
        if not getattr(self, "_r6_narrow", True):
            return _win_merge([w for p in pages for w in p])      # the round-5b reading (union)
        # round6-1119 (hub decision 6): pages that date the number differently
        # (96302-7S600) are read narrowly: the months every dating page lists
        narrow = pages[0]
        for p in pages[1:]:
            narrow = _win_intersect(narrow, p)
        if not narrow:
            self.__dict__.setdefault("_window_disagree_disjoint", set()).add((key, cat, T))
            return _win_merge([w for p in pages for w in p])
        if any(p != narrow for p in pages):
            self.__dict__.setdefault("_window_narrowed", set()).add((key, cat, T))
        return narrow

    def _pn_list_rows(self, key, cat):
        idx = self.__dict__.get("_pn_rows")
        if idx is None:
            idx = defaultdict(list)
            for lr in self.list_rows:
                idx[(policy.pn_key(self.ns, lr.pn), lr.cat)].append(lr)
            self._pn_rows = idx
        return idx.get((key, cat), [])

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
                        "likely_app_years_body_mixed": dict(sorted(
                            getattr(self, "likely_body_mixed", Counter()).items())),
                        "likely_app_years_engine_conflict": dict(sorted(
                            getattr(self, "likely_engine_conflict", Counter()).items())),
                        "likely_app_years_drive_ambiguous": dict(sorted(
                            getattr(self, "likely_drive_dropped", Counter()).items())),
                        "likely_groups_drive_noted": dict(sorted(
                            getattr(self, "likely_drive_noted", Counter()).items())),
                        # round5b-1119: only where a starred configuration decided one
                        **({"likely_app_years_starred_scope": dict(sorted(self.likely_starred_scope.items()))}
                           if getattr(self, "likely_starred_scope", None) else {}),
                        **({"likely_app_years_round6_held": {f"{r}:{cc}": n for (r, cc), n in
                                                            sorted(self.likely_round6_held.items())}}
                           if getattr(self, "likely_round6_held", None) else {}),
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
# categories whose slot members must all share one packaging (tier C wiper)
_ONE_PACK_CATS = {"wiper-motor"}


_WIPER_END = {"F": "windshield wiper motor", "R": "rear wiper motor",
              "FL": "driver-side windshield wiper motor (twin-motor)",
              "FR": "passenger-side windshield wiper motor (twin-motor)"}
_WIPER_PACK = {"motor": "", "drive": " with linkage", "kit": " kit", "motor-ecb": " without circuit board",
               "motor-ctl": " with integral control module"}


def _pack_text(cat: str, packaging: str, slot: str = "") -> str:
    """Packaging words for a Likely note, only in the category they describe
    (2026-11-09 GM resample: climate-control panels with packaging 'assy'
    read 'regulator with motor'; a full control panel needs no words).
    wiper-motor names its end and packaging ("rear wiper motor with linkage")."""
    if cat == "wiper-motor":
        return _WIPER_END[slot] + _WIPER_PACK[packaging] if slot in _WIPER_END and packaging in _WIPER_PACK else ""
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
        if alts and all(_foreign_alt(a) and not _US_MARKET_RE.search(a) for a in alts):
            return True
    return False


# round3-1119 (policy.LIKELY_MARKET_UNIT_RULE): km/h-first speedometers and
# mandatory export equipment groups. "MPH/KMH" is the US dual-scale unit;
# "KMH/MPH", "KPH/MPH" and "Instrument-Kph" the Canada one (fordpartsgiant
# AE5Z-10849-LA "With MPH/KMH Speedometer" vs -MA "With KMH/MPH"). A negated
# group ("(-)GCC", "EXC", "W/O") keeps the row.
_KMH_RE = re.compile(r"(?<![A-Za-z])(?:KPH|KMH|KM\s*/\s*H)(?![A-Za-z])", re.I)
_MPH_RE = re.compile(r"(?<![A-Za-z])MPH(?![A-Za-z])", re.I)
_EXPORT_GROUP_RE = re.compile(r"(?<!EXC )(?<!W/O )(?<!WITHOUT )(?<!\(-\))\b(?:EUROPEAN|EUROPE|MIDDLE\s+EAST|EXPORT|GULF|"
                              r"GCC|MEXICAN|MEXICO|CANADIAN|CANADA)\s+EQUIPMENT\s+GROUP\b|"
                              r"(?<!EXC )\bEXPORT\s+Mandatory\b", re.I)


def _kmh_first(text: str) -> bool:
    """True when text names a km/h unit before any MPH ('KMH/MPH', 'Instrument-Kph')."""
    m = _KMH_RE.search(str(text or ""))
    if not m:
        return False
    p = _MPH_RE.search(str(text or ""))
    return not p or p.start() > m.start()


def _foreign_alt(a: str) -> bool:
    if _MARKET_RE.search(a):
        return True
    return bool(policy.LIKELY_MARKET_UNIT_RULE and (_EXPORT_GROUP_RE.search(a) or _kmh_first(a)))


def _kmh_part(c, notes) -> bool:
    """policy.LIKELY_MARKET_UNIT_RULE, class-wide: the product record itself
    (name, description, other names) or any own-page note of the class names a
    km/h-first unit: the part is the Canada cluster, for every vehicle-year."""
    if not policy.LIKELY_MARKET_UNIT_RULE:
        return False
    texts = [x for r in c.records for x in (r.name, r.aux, r.description, r.other_names)] + list(notes or [])
    return any(_kmh_first(t) for t in texts if t)


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
# "Production Date: from 12/2002" (open end; 610 rows on nissanpartsdeal, 969 on
# lexuspartsnow at oem-raw@57e8b5b9) and the same inside a comma list
# ("02/2009-08/2010,from 08/2010"); interchange 2026-11-18, nissan §11.4 round 3
_PROD_FROM_RE = re.compile(r"(?:^|[\s:,])from\s+(\d{1,2})/(\d{4})", re.I)
_PROD_MIN_MONTHS = 5
# wheels have their own, stricter whole-group production-date refusal
# (wheel_production_date); a per-row cut first would let a group that rule
# refuses through, so the per-row rule never adds a claim there
PROD_RULE_SKIP_CATS = frozenset({"wheels"})

# §5.16 body-variant rule (policy.LIKELY_BODY_GATE). Body words as catalogs
# print them in a catalog/variant name ("2009-infiniti-g37-sedan") or a note;
# vPIC files one crossover as "wagon" or "SUV" (Infiniti QX50 17 / 4 on the
# lots, 2026-11-18), so the two count as one silhouette here.
_BODY_WORDS = (
    ("sedan", re.compile(r"\b(?:sedan|saloon)", re.I)),
    ("coupe", re.compile(r"\b(?:coupe|koup)", re.I)),
    ("convertible", re.compile(r"\b(?:convertible|cabrio|roadster)", re.I)),
    ("hatchback", re.compile(r"\b(?:hatch(?:back)?|liftback)", re.I)),
    ("wagon", re.compile(r"\b(?:wagon|sportwagen|avant|estate)\b", re.I)),
    ("van", re.compile(r"\b(?:mini)?van\b", re.I)),
    ("pickup", re.compile(r"\bpick-?up\b", re.I)),
)
_SILHOUETTE = {"suv": "wagon"}
_FVO_RE = re.compile(r"^\s*fitting\s+vehicle\s+options", re.I)   # PartsGiant option column (body codes S/C/KC...)
_PROD_CLAUSE_RE = re.compile(r"^\s*production\s+date", re.I)


def _body_words(text) -> set:
    t = str(text or "").replace("_", " ").replace("-", " ")
    return {_SILHOUETTE.get(b, b) for b, rx in _BODY_WORDS if rx.search(t)}


def _catalog_of(list_url: str) -> str:
    """The catalog segment of a parts-list URL (".../parts-list/2008-infiniti-g35-sedan/...")."""
    m = re.search(r"/parts-list/([^/]+)/", list_url or "")
    return m.group(1) if m else ""


# Infiniti feed models whose name fixes the engine displacement (interchange
# 2026-11-18, nissan §11.4 round 1: 24820-6AH1A "SEDAN. VQ37VHR" claimed for
# the M56 and 24820-6AH1C "SEDAN. VK56VD" for the M37; 24820-1NP0C "VQ35HR"
# for the M45). infinitipartsdeal files M35/M45 and M37/M56 under one catalog
# and the option column names the engine (VQ35HR 3.5L, VK45DE 4.5L, VQ37VHR
# 3.7L, VK56VD 5.6L, VK50VE 5.0L, VQ25HR 2.5L, VQ30DE 3.0L, VH45DE 4.5L, SR20
# 2.0L: the two digits after the family letters). Post-2014 names (Q40, Q50,
# Q60, Q70, QX50/60/70/80) do not encode the engine and are not listed.
_INFINITI_DISP = {"G20": 20, "G25": 25, "G35": 35, "G37": 37, "G37X": 37, "I30": 30, "I35": 35, "J30": 30,
                  "M30": 30, "M35": 35, "M35H": 35, "M37": 37, "M45": 45, "M56": 56, "Q45": 45, "FX35": 35,
                  "FX37": 37, "FX45": 45, "FX50": 50, "EX35": 35, "EX37": 37, "JX35": 35, "QX56": 56}
_NISSAN_ENGINE_CODE_RE = re.compile(r"\b(?:VQ|VK|VG|VH|QR|KA|SR|MR|HR|VR)(\d{2})(?:[A-Z]{1,4})?\b")


def _infiniti_engine_excludes(notes, T) -> bool:
    """True when an own-page row's option column restricts the number to
    engines the Infiniti model T never had: every alternative names an engine
    code and none has T's displacement. Per row only (never pooled across
    pages, like the Lexus chassis gate). Only removes claims."""
    if T[0] != "Infiniti":
        return False
    disp = _INFINITI_DISP.get(re.sub(r"\s+", "", str(T[1])).upper())
    if not disp:
        return False
    for n in notes or []:
        m = re.match(r"^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$", n or "", re.I)
        if not m:
            continue
        alts = _split_top_plus(m.group(1), ",")
        found = [{int(d) for d in _NISSAN_ENGINE_CODE_RE.findall(x)} for x in alts]
        if alts and all(f for f in found) and not any(disp in f for f in found):
            return True
    return False


_ENGINE_LITRE_RE = re.compile(r"\b(\d)\.(\d)\s*L\b", re.I)


def _infiniti_fitment_engine_conflict(c, T) -> bool:
    """nissan §11.4 round 2 (24820-6AH2A: the product page prints '2013
    Infiniti M56 | Base, Premium, SportPre | 6 Cyl 3.7L | VQ37VHR'): True when
    every product-page fitment row of the class for the Infiniti model T and
    T's year names engines (engine cell or engine code), and none has T's
    displacement (_INFINITI_DISP). Engine cells are never used to ADD a claim
    (§5.5); here they only remove one."""
    if T[0] != "Infiniti":
        return False
    disp = _INFINITI_DISP.get(re.sub(r"\s+", "", str(T[1])).upper())
    if not disp:
        return False
    want = re.sub(r"\s+", "", str(T[1])).upper()
    rows = [f for r in c.records for f in r.rows
            if re.sub(r"\s+", "", str(f.model)).upper() == want and f.lo <= T[2] <= f.hi]
    if not rows:
        return False
    for f in rows:
        found = {int(d) for x in (f.options or []) for d in _NISSAN_ENGINE_CODE_RE.findall(str(x))}
        found |= {int(a) * 10 + int(b) for x in (f.engines or []) for a, b in _ENGINE_LITRE_RE.findall(str(x))}
        if not found or disp in found:
            return False
    return True


# nissanpartsdeal option-column body codes (nissan §11.4 round 4): shared
# catalog pages list each body's number behind a leading body code, e.g. the
# B14 Sentra/200SX page: 24820-8B700 "C. GA16DE" (coupe = 200SX) on the 1999
# Sentra page and 24820-89Y02 "4S. (E + XE + GXE)" (4-door sedan) on the 1996
# 200SX page; the G35 sedan page codes coupe parts "C" and sedan parts "S";
# Versa "SED."; Xterra/Pathfinder "W." (wagon). Region prefixes FED./CAL. and
# plant prefixes J/ U/ come first.
_NISSAN_BODY_CODES = {"4S": "sedan", "2S": "sedan", "S": "sedan", "SED": "sedan", "SEDAN": "sedan",
                      "LSEDAN": "sedan", "C": "coupe", "CPE": "coupe", "COUPE": "coupe", "W": "wagon",
                      "WAG": "wagon", "WAGON": "wagon", "HB": "hatchback", "CONV": "convertible"}
_NISSAN_PREFIX_RE = re.compile(r"^(?:(?:FED|CAL)\.\s*|[JU]/)+", re.I)


def _nissan_body_code_excludes(notes, bodies) -> bool:
    """True when a row's option column names a body for every alternative
    (and every '+'-joined part) and none of them is a body the car comes in
    (bodies: Curation.body_need, lot vPIC + catalog pages). No known body
    for the car: no exclusion. Per row only. Only removes claims."""
    if not bodies:
        return False
    for n in notes or []:
        m = re.match(r"^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$", n or "", re.I)
        if not m:
            continue
        named, all_coded = set(), True
        for alt in _split_top_plus(m.group(1), ","):
            for part in _split_top_plus(alt, "+"):
                part = _NISSAN_PREFIX_RE.sub("", part.strip().lstrip("*").lstrip("(").strip())
                tok = re.match(r"^([A-Za-z0-9]+)(?=[.\s)]|$)", part)
                b = _NISSAN_BODY_CODES.get(tok.group(1).upper()) if tok else None
                if not b:
                    all_coded = False
                    break
                named.add(b)
            if not all_coded:
                break
        if all_coded and named and not (named & set(bodies)):
            return True
    return False


def _fvo_cab_codes(notes) -> set | None:
    """{"CC"} / {"KC"} / both when every alternative of the row's option
    column ("Fitting Vehicle Options: CC. S, CC. XE") starts with a cab code;
    None when the row has no option column or an alternative names no cab
    or another code ("(KC+ SC). XD")."""
    codes, seen = set(), False
    for n in notes or []:
        m = re.match(r"^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$", n or "", re.I)
        if not m:
            continue
        seen = True
        for alt in _split_top_plus(m.group(1), ","):
            # '+' joins configurations inside one alternative ("*KC. 4WD. LE +
            # *CC. 4WD. LE" is both cabs): every joined part needs its own code
            for part in _split_top_plus(alt, "+"):
                part = part.strip().lstrip("*")
                grp = re.match(r"^\(([^)]*)\)", part)
                heads = _split_top_plus(grp.group(1), "+") if grp else [part]
                for h in heads:
                    mm = re.match(r"^\*?(KC|CC)(?![A-Za-z0-9])", h.strip())
                    if not mm:
                        return None
                    codes.add(mm.group(1))
    return codes if seen else None


def _fvo_cab_parts(notes):
    """[(code or None)] for every configuration of the row's option column,
    reading the Nissan pickup cab field T (regular cab), KC, CC (round3-1119:
    the 2002 Frontier page lists 80721-3S510 'KC + CC. SB + CC. XB, T + KC +
    CC' beside 3S500 '*KC + *CC'); None when the row has no option column."""
    out, seen = [], False
    for n in notes or []:
        m = re.match(r"^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$", n or "", re.I)
        if not m:
            continue
        seen = True
        for alt in _split_top_plus(m.group(1), ","):
            for part in _split_top_plus(alt, "+"):
                part = part.strip().lstrip("*")
                grp = re.match(r"^\(([^)]*)\)", part)
                heads = _split_top_plus(grp.group(1), "+") if grp else [part]
                for h in heads:
                    mm = re.match(r"^\*?(T|KC|CC)(?![A-Za-z0-9])", h.strip())
                    out.append(mm.group(1) if mm else None)
    return out if seen else None


def _fvo_cab_set(notes):
    """{T / KC / CC} when every configuration of the row starts with a cab
    code, else None."""
    parts = _fvo_cab_parts(notes)
    if not parts or any(p is None for p in parts):
        return None
    return set(parts)


def _fvo_cab_heads(notes) -> set:
    """Every cab code a configuration of the row starts with (others ignored)."""
    return {p for p in (_fvo_cab_parts(notes) or []) if p}


def _split_top_plus(text: str, sep: str) -> list:
    """Split on sep outside parentheses ("CC. 4WD. (S+ SV). 6MT" stays whole)."""
    out, depth, cur = [], 0, ""
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
            continue
        cur += ch
    out.append(cur)
    return [x for x in (y.strip() for y in out) if x]


def _row_body_cover(notes, ctx, site: str = "", page_body: bool = True) -> set | None:
    """None when a row's notes cannot restrict the body (no body word, no
    option-column code, no unparsed clause other than a production date):
    the row covers every body of its page. Otherwise the bodies its notes
    name, in words or (2026-11-18) in a fully decoded option-column body code
    (_fvo_bodies: subarupartsdeal S./W./OBK, gmpartsgiant body styles 37/69/
    67, nissanpartsdeal C./4S.), possibly none. PartsGiant quantity, callout
    and colour fields restrict nothing. With page_body False (no row on T's
    pages in the category names a body or carries a body code), an unparsed
    clause without a body-like word ('Fit Note: Power Front Windows One
    Touch Up/Do') restricts nothing either: the page does not split by body."""
    named, unsafe = set(), False
    for n in notes or []:
        if _NEUTRAL_FIELD_RE.match(n or ""):
            continue
        fm = _FVO_BODY_RE.match(n or "")
        if fm:
            dec = _fvo_bodies(fm.group(1), site)
            named |= dec if dec else _body_words(fm.group(1))
            unsafe = True
            continue
        for seg in N.split_note(n):
            for cl in seg:
                c = N.classify_clause(cl, ctx)
                if c.cls == "BODY" or any(a.cls == "BODY" for a in c.atoms) or _FVO_RE.match(cl):
                    named |= _body_words(cl)
                    unsafe = True
                elif c.cls == "UNKNOWN" and not _PROD_CLAUSE_RE.match(cl):
                    if page_body or _BODYISH_RE.search(cl):
                        unsafe = True
    return named if unsafe else None


# fitment-trim door counts ("4 DOOR", "LS 5 DOOR HATCHBACK", "2DR"); a body
# with a door set here is plausible only when the trims name one of them
_DOOR_RE = re.compile(r"(?<![A-Za-z0-9])([2-5])\s*-?\s*(?:DOORS?|DR)(?![A-Za-z0-9])", re.I)
_BODY_DOORS = {"coupe": {2, 3}, "convertible": {2}, "sedan": {4}}


# PartsGiant row fields that never name a body (Nissan/GM "Require Quantity:
# 02", "Package Quantity: 1", Ford "Callout Name: 14553", "Interior Color:")
_NEUTRAL_FIELD_RE = re.compile(r"^\s*(?:require\s+quantity|package\s+quantity|callout\s+name|interior\s+colou?r|"
                               r"exterior\s+colou?r)\s*:", re.I)
# words that may name a body or a cab in free text; an unparsed clause holding
# one always restricts
_BODYISH_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d\s?-?doors?|[2-5]\s?-?dr|sedan|saloon|coupe|koup|wagon|hatch\w*|"
                         r"liftback|notchback|fastback|convertible|cabrio\w*|roadster|van|pickup|pick-up|cab|crew|"
                         r"king|access|suv|utility|estate|avant|sportback|body)(?![A-Za-z0-9])", re.I)
# gmpartsgiant body-style codes (the 2-digit group after the series:
# "AP(37)", "J(67)", "F(87)"), passenger-car styles only; truck cab and box
# codes (03/53/43/36/06...) stay undecoded and keep restricting
_GM_BODY_STYLE = {"27": {"coupe"}, "37": {"coupe"}, "47": {"coupe"}, "57": {"coupe"},
                  "87": {"coupe", "hatchback"}, "19": {"sedan"}, "69": {"sedan"}, "67": {"convertible"},
                  "35": {"wagon"}, "48": {"hatchback"}, "68": {"hatchback"}}
# subarupartsdeal alternative heads ("S.(25GT+25GTLTD) +W.(...) +WOBK.25GTLTD")
_SUBARU_BODY_HEADS = {"S": {"sedan"}, "W": {"wagon"}, "SW": {"wagon"}, "TW": {"wagon"}, "WOBK": {"wagon"},
                      "SOBK": {"sedan"}, "P": {"pickup"}}


def _subaru_head_bodies(h: str):
    h = h.strip().lstrip("*")
    if h in _SUBARU_BODY_HEADS:
        return _SUBARU_BODY_HEADS[h]
    if re.fullmatch(r"OBK\w*", h):
        return {"wagon"}          # Outback wagon (OBK, OBK6, OBKLTD...)
    if re.fullmatch(r"SUS\w*", h):
        return {"sedan"}          # Outback sport-utility sedan
    if re.fullmatch(r"BAJA\w*", h):
        return {"pickup"}
    return None


def _fvo_bodies(body: str, site: str):
    """The bodies an option column names when EVERY alternative carries a
    body code this table knows; None otherwise (it then restricts like any
    unparsed option column)."""
    out = set()
    if site == "www.subarupartsdeal.com":
        alts = _split_top(body)
        if not alts:
            return None
        for alt in alts:
            head = alt.strip().lstrip("*").partition(".")[0]
            heads = re.findall(r"[A-Z0-9#]+", head) if head.startswith("(") else [head]
            for h in heads:
                b = _subaru_head_bodies(h)
                if not b:
                    return None
                out |= b
        return out or None
    if site == "www.gmpartsgiant.com":
        alts = _split_top_plus(body, ",")
        if not alts:
            return None
        for alt in alts:
            g = re.match(r"^\s*[A-Z]{1,2}\d*\s*\(\s*(\d{2}(?:\s*[-,]\s*\d{2})*)\s*\)", alt)
            if not g:
                return None
            for code in re.split(r"\s*[-,]\s*", g.group(1)):
                b = _GM_BODY_STYLE.get(code)
                if not b:
                    return None
                out |= b
        return out or None
    if site in ("www.nissanpartsdeal.com", "www.infinitipartsdeal.com"):
        alts = _split_top_plus(body, ",")
        if not alts:
            return None
        for alt in alts:
            for part in _split_top_plus(alt, "+"):
                part = _NISSAN_PREFIX_RE.sub("", part.strip().lstrip("*").lstrip("(").strip())
                tok = re.match(r"^([A-Za-z0-9]+)(?=[.\s)]|$)", part)
                b = _NISSAN_BODY_CODES.get(tok.group(1).upper()) if tok else None
                if not b:
                    return None
                out.add(b)
        return out or None
    return None


def _row_names_body(notes, site: str) -> bool:
    """True when a row's notes name a body (word or decoded body code) or
    carry a body-like word: the page splits by body."""
    for n in notes or []:
        if _NEUTRAL_FIELD_RE.match(n or ""):
            continue
        fm = _FVO_BODY_RE.match(n or "")
        if fm and _fvo_bodies(fm.group(1), site):
            return True
        if _body_words(n) or _BODYISH_RE.search(n or ""):
            return True
    return False


# ------------------------------------------------ §5.16 drive rule (2026-11-18)
# Drive classes. FOUR / TWO are the two families a yard car belongs to; a
# restriction is material only when it leaves one family out.
# "a4wd": nissanpartsdeal's "AUTO" drive field (2006 Pathfinder clusters are
# coded "W. 2WD", "W. 4WD" and "*W. AUTO" in the same field: All-Mode 4WD), a
# four-wheel drive of its own, never the part-time 4WD's number
_FOUR = frozenset({"4wd", "awd", "a4wd"})
_TWO = frozenset({"2wd", "fwd", "rwd"})
_DRIVE_ALL = _FOUR | _TWO
_DB = r"(?<![A-Za-z0-9/])"           # "6-1/4x4-3/4" (a Mopar mirror glass size) is no drive
_DE = r"(?![A-Za-z0-9]|-\d|/\d)"
_DRIVE_PATTERNS = (
    # GM "FOR 2 OR 4 DOOR MODELS W/2 OR 4 WHEEL DRIVE": both families
    (("2wd", "4wd"), re.compile(r"(?<![A-Za-z0-9])2\s*(?:OR|/|&)\s*4[\s-]*WHEEL[\s-]*DRIVE" + _DE, re.I)),
    (("2wd", "4wd"), re.compile(_DB + r"4\s?X\s?2\s*(?:OR|/|&)\s*4\s?X\s?4" + _DE, re.I)),
    (("4wd",), re.compile(_DB + r"(?:4\s?WD|4\s?X\s?4|FOUR[\s-]*WHEEL[\s-]*DRIVE|4[\s-]*WHEEL[\s-]*DRIVE)" + _DE, re.I)),
    (("awd",), re.compile(_DB + r"(?:SH-AWD|AWD|ALL[\s-]*WHEEL[\s-]*DRIVE|4\s?MATIC|4\s?MOTION|QUATTRO|XDRIVE)" + _DE, re.I)),
    (("2wd",), re.compile(_DB + r"(?:2\s?WD|4\s?X\s?2|TWO[\s-]*WHEEL[\s-]*DRIVE|2[\s-]*WHEEL[\s-]*DRIVE)" + _DE, re.I)),
    (("fwd",), re.compile(_DB + r"(?:FWD|FRONT[\s-]*WHEEL[\s-]*DRIVE)" + _DE, re.I)),
    (("rwd",), re.compile(_DB + r"(?:RWD|REAR[\s-]*WHEEL[\s-]*DRIVE)" + _DE, re.I)),
)
_DRIVE_NEG_RE = re.compile(r"(?:\bwithout|\bw/o|\bless|\bnon|\bexc(?:ept)?\.?|\bexcluding|\bnot)[\s-]*\(?\s*$", re.I)
# words a clean drive clause may hold besides the drive itself ("With AWD",
# "(FWD)", "4x2 or 4x4", "Four-Wheel Drive only"); anything else makes a free
# text clause that names a drive ambiguous ("4x4 Hi & Lo - IND#194 / ...")
_DRIVE_FILLER_RE = re.compile(r"\b(?:with|w/o|w/|without|less|non|exc|except|excluding|only|models?|vehicles?|"
                              r"and|or|for|drive|all)\b|[()\[\]&,.:;/*+-]", re.I)
DRIVE_AMBIGUOUS = "?"


# round3-1119 (item 3 of the 2026-11-18c check): infinitipartsdeal joins the
# drive code to the steering code in one token ("*SEDAN. 2WDHICAS. SPORTTEC",
# "*SEDAN. 2WDSTD. BASE"; the M37/Q70 pages, 771 rows). These two are the only
# joined forms in the raw (census of oem-raw@57e8b5b9 and @dca9cd84).
_JOINED_DRIVE_RE = re.compile(r"(?<![A-Za-z0-9])(2WD|4WD|AWD)(STD|HICAS)(?![A-Za-z0-9])", re.I)


def _drive_terms(text: str):
    """(positive classes, negated classes, leftover text) named in text."""
    pos, neg = set(), set()
    s = _JOINED_DRIVE_RE.sub(r"\1 \2", str(text or ""))
    for classes, rx in _DRIVE_PATTERNS:
        while True:
            m = rx.search(s)
            if not m:
                break
            (neg if _DRIVE_NEG_RE.search(s[:m.start()]) else pos).update(classes)
            s = s[:m.start()] + " " * (m.end() - m.start()) + s[m.end():]
    return pos, neg, s


def _drive_allowed(pos: set, neg: set):
    """The drive classes a clause allows, or None when it allows both families.
    'Without AWD' allows the 2-wheel family (a car that is not AWD is 2WD)."""
    if pos:
        allowed = set(pos)
    elif neg:
        allowed = set(_DRIVE_ALL)
        if neg & _FOUR:
            allowed -= _FOUR
        if neg & _TWO:
            allowed -= _TWO
    else:
        return None
    allowed = frozenset(allowed)
    if not allowed or (allowed & _FOUR and allowed & _TWO):
        return None
    return allowed


_DRIVE_LABELS = {"4wd": "4WD", "awd": "AWD", "a4wd": "4WD AUTO"}


def _drive_label(allowed) -> str:
    a = frozenset(allowed or ())
    if a and a <= _FOUR:
        return "/".join(_DRIVE_LABELS[x] for x in ("4wd", "awd", "a4wd") if x in a)
    if a and a <= _TWO:
        return "FWD" if a == {"fwd"} else "RWD" if a == {"rwd"} else "2WD"
    return ""


# Per-app gates (interchange gates-1118): the §5.16 limits of a vehicle-year,
# structured, beside the note that names them. The payload builder ships them
# as the 6th element of the app ([make, model, lo, hi, null, gate]), the form
# the aftermarket rows already use, and docs/app.js (OEM-GATE) hides a donor
# whose own decode or listing contradicts one. validate.gate_problem holds the
# vocabulary. Only ever narrows which lot cars are offered; apps, ids and notes
# are unchanged.
_GATE_DRIVE_ORDER = ("2wd", "fwd", "rwd", "4wd", "awd", "a4wd")
_TRANS_GATE = {"manual": "MT", "automatic": "AT"}


def _drive_gate(allowed) -> str:
    """frozenset({'fwd', 'rwd'}) -> 'fwd/rwd' (classes in a fixed order)."""
    return "/".join(x for x in _GATE_DRIVE_ORDER if x in set(allowed or ()))


def _cab_gate(cab: str) -> str:
    """The note's cab words as one gate value ('super cab' -> 'supercab')."""
    c = re.sub(r"\s+", " ", str(cab or "").strip().lower())
    return {"super cab": "supercab", "super crew": "supercrew", "crew max": "crewmax"}.get(c, c)


def _gate_runs(gate_by_T: dict) -> list:
    """[[make, model, lo, hi, gate], ...]: per feed model, maximal runs of
    consecutive gated years with the same gate (keys sorted)."""
    by = defaultdict(dict)
    for (mk, md, y), g in gate_by_T.items():
        by[(mk, md)][y] = {k: g[k] for k in sorted(g)}
    out = []
    for (mk, md), ys in sorted(by.items()):
        run = None
        for y in sorted(ys):
            if run and y == run[3] + 1 and ys[y] == run[4]:
                run[3] = y
            else:
                if run:
                    out.append(run)
                run = [mk, md, y, y, ys[y]]
        out.append(run)
    return out


def _variant_drive(variant: str):
    """Drive a catalog page's name gives ('2007-chevrolet-tahoe-2wd' -> {'2wd'}), or None."""
    pos, neg, _ = _drive_terms(re.sub(r"[_-]+", " ", variant or ""))
    return _drive_allowed(pos, neg)


def _drive_union(ds):
    """Union of per-row drive sets: None when any row is unrestricted,
    DRIVE_AMBIGUOUS when any is ambiguous (and none unrestricted), else the
    union, which may stop being material (both families)."""
    ds = list(ds)
    if not ds or any(d is None for d in ds):
        return None
    if any(d == DRIVE_AMBIGUOUS for d in ds):
        return DRIVE_AMBIGUOUS
    u = frozenset().union(*ds)
    return None if (u & _FOUR and u & _TWO) else u


def _mopar_codes(body: str) -> list:
    """'41 - SEDAN/QUAD CAB SWB, C - CHRYSLER, F - BRAND AWD' -> [('41', 'SEDAN/QUAD CAB SWB'), ...]."""
    return [(m.group(1), m.group(2).strip()) for m in
            re.finditer(r"(?:^|,\s*)([A-Z0-9*]{1,4})\s+-\s+((?:(?!,\s*[A-Z0-9*]{1,4}\s+-\s).)*)", body)]


_NISSAN_SITES = frozenset({"www.nissanpartsdeal.com", "www.infinitipartsdeal.com"})
_MOPAR_LINE_RE = re.compile(r"\b(?:CHRYSLER|DODGE|JEEP|RAM|PLYMOUTH|FIAT|EAGLE|BRAND|DUTY)\b", re.I)


def _fvo_drive(body: str, site: str):
    """Drive allowed by one 'Fitting Vehicle Options' column (site semantics,
    policy.DRIVE_CONFIG_FVO_SITES), None when it does not restrict the drive."""
    if site in policy.DRIVE_CONFIG_FVO_SITES:
        out = []
        for alt in _split_top_plus(body, ","):
            for part in _split_top_plus(alt, "+"):
                pos, neg, _ = _drive_terms(part)
                if site in _NISSAN_SITES and re.search(r"(?:^|\.)\s*\*?AUTO\s*(?:\.|$)", part):
                    pos.add("a4wd")      # the drive field: 2WD / 4WD / AUTO
                if not pos and not neg:
                    return None          # this configuration fits any drive
                out.append(_drive_allowed(pos, neg))
        return _drive_union(out) if out else None
    if site in ("www.jeeppartsdeal.com", "www.moparpartsgiant.com"):
        # sales-code lists: a brand/line code without a drive word ('C - CHRYSLER'
        # beside 'F - BRAND AWD', 'D - DODGE' beside 'E - DODGE AWD') leaves the
        # drive open; otherwise the drive words of the line codes are the drives
        codes = _mopar_codes(body)
        pos, neg = set(), set()
        for _code, text in codes:
            p, n, _ = _drive_terms(text)
            if _MOPAR_LINE_RE.search(text) and not p and not n:
                return None
            pos |= p
            neg |= n
        if not codes:
            pos, neg, _ = _drive_terms(body)
        return _drive_allowed(pos, neg)
    pos, neg, _ = _drive_terms(body)
    return _drive_allowed(pos, neg)


def _free_note_drive(text: str):
    """Drive allowed by one free-text note ('Sedan, FWD'; '2009-2012, Without
    AWD'; 'A;B' = alternatives): None when some alternative names no drive,
    DRIVE_AMBIGUOUS when a clause names a drive among other words."""
    segs = N.split_note(text)
    if not segs:
        return None
    out = []
    for seg in segs:
        pos, neg, ambiguous = set(), set(), False
        for cl in seg:
            p, n, rest = _drive_terms(cl)
            if not p and not n:
                continue
            pos |= p
            neg |= n
            if _DRIVE_FILLER_RE.sub(" ", rest).strip():
                ambiguous = True
        if not pos and not neg:
            return None
        a = _drive_allowed(pos, neg)
        if a is None:
            return None
        out.append(DRIVE_AMBIGUOUS if ambiguous else a)
    return _drive_union(out)


def _gm_series_letters(body: str):
    """gmpartsgiant series letters of an option column ('CK1,2(...)' -> {C,K};
    'K207(53)(...), CK209(...)' -> {C,K}); None when an alternative's head is
    not a truck-style series (letters followed by a digit: 'U', 'UM,UT', 'JB')."""
    letters = set()
    alts = _split_top_plus(body, ",")
    # 'CK1,2,3' splits into 'CK1', '2', '3' outside parentheses: a bare
    # number continues the previous series
    seen_any = False
    for alt in alts:
        head = alt.split("(")[0].strip()
        if not head:
            return None
        if re.fullmatch(r"\d+", head) and seen_any:
            continue
        m = re.fullmatch(r"([A-Z]{1,2})(\d+)", head)
        if not m:
            return None
        letters |= set(m.group(1))
        seen_any = True
    return frozenset(letters) if letters else None


def _row_drive(notes, site: str, gm_page_letters=None, variant: str = ""):
    """Drive allowed by one own-page row (its notes are conjunctive, and the
    catalog page it sits on may name a drive: gmpartsgiant files Silverado
    pages as '1500_2wd' / '1500_4wd', audipartsgiant 'a4_quattro'): None, a
    frozenset of classes, or DRIVE_AMBIGUOUS. On gmpartsgiant the row's own
    series code is the part's application: 'ST1' on the 2wd page names both
    series, so it overrides the page's drive."""
    allowed, restricted, ambiguous, both = set(_DRIVE_ALL), False, False, False
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if m:
            d = _fvo_drive(m.group(1), site)
            if site == "www.gmpartsgiant.com":
                g = _gm_series_drive(m.group(1), gm_page_letters)
                if g == "both":
                    both = True
                elif g == DRIVE_AMBIGUOUS:
                    ambiguous = True
                elif g is not None:
                    d = g if d is None else (d & g) or DRIVE_AMBIGUOUS
        else:
            d = _free_note_drive(n)
        if d is None:
            continue
        if d == DRIVE_AMBIGUOUS:
            ambiguous = True
            continue
        allowed &= d
        restricted = True
    if not both:
        vp, vn, _ = _drive_terms(re.sub(r"[_-]+", " ", variant or ""))
        va = _drive_allowed(vp, vn)
        if va:
            allowed &= va
            restricted = True
    if ambiguous:
        return DRIVE_AMBIGUOUS
    if not restricted:
        return None
    return frozenset(allowed) if allowed else DRIVE_AMBIGUOUS


_FVO_BODY_RE = re.compile(r"^\s*fitting\s+vehicle\s+options\s*:\s*(.*)$", re.I)


def _gm_series_drive(body: str, page_letters):
    """GM series code of one option column (policy.GM_SERIES_DRIVE): 'both'
    when it names every series of a known pair (CK1, ST1, LM1, RV1), the
    drive classes of a single series of a pair (K1, T1), DRIVE_AMBIGUOUS
    when it names fewer series than T's own pages show and the pair is not
    in the table (Savana H1 beside G1), else None."""
    row = _gm_series_letters(body)
    if not row:
        return None
    for pair, drive in policy.GM_SERIES_DRIVE.items():
        if row <= pair:
            return "both" if row == pair else frozenset(drive[x] for x in row)
    if page_letters and row < page_letters:
        return DRIVE_AMBIGUOUS
    return None


# engine codes in config-tuple option columns: Nissan/Infiniti families
# (VQ37VHR 3.7L, KA24DE 2.4L, VG33E 3.3L, QR25DE 2.5L, VK56DE 5.6L), Subaru
# EJ/EZ/FB/FA, and Hyundai/Kia litres ("2.0L Theta", "[1.6L - GAMMA]")
_ENGINE_CODE_RE = re.compile(r"(?<![A-Z0-9])(?:VQ|VK|VG|VH|QR|KA|SR|MR|HR|VR|GA|KR|CD|YD|RB|CA|EJ|EZ|FB|FA)"
                             r"(\d{2})(?:[A-Z#]{0,4}\d?)?(?![A-Z0-9])")
_LITRE_RE = re.compile(r"(?<![0-9.])(\d)\.(\d)\s*L(?![A-Za-z])", re.I)
_MANUAL_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d?MT|M/T)(?![A-Za-z0-9])|\[\s*Manual\b", re.I)
_AUTO_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d?AT|A/T|CVT|E-?CVT)(?![A-Za-z0-9])|\[\s*Auto\b", re.I)


def _engine_terms(text: str) -> set:
    t = str(text or "")
    out = {int(d) / 10 for d in _ENGINE_CODE_RE.findall(t.upper())}
    out |= {int(a) + int(b) / 10 for a, b in _LITRE_RE.findall(t)}
    return {round(x, 1) for x in out}


# product-page engine column (policy.LIKELY_FIT_ENGINE_RULE, round3-1119):
# "6 Cyl 3.5L DOHC", "2.4L L4", "4 Cyl 2.4 L FULL HYBRID EV-GAS (FHEV)"; a
# year page's engine sub-catalog slug ("8_cyl_5_0l-4at_4r70w", fordpartsgiant)
_FIT_LIT_RE = re.compile(r"(?<![0-9.])(\d{1,2}\.\d)\s*L(?![A-Za-z])", re.I)
_FIT_SLUG_LIT_RE = re.compile(r"(?:^|_)(\d{1,2})_(\d)l(?:-|_|$)", re.I)
# fordpartsgiant prints the Fusion / MKZ / Milan hybrid as "4 Cyl 2.5L PFI
# Gas/Electric" (census of every engine string on oem-raw@dca9cd84 and @57e8b5b9)
_FIT_HYBRID_RE = re.compile(r"HYBRID|\bFHEV\b|\bHEV\b|\bPHEV\b|\bMHEV\b|PLUG-IN|GAS\s*/\s*ELECTRIC|GAS-ELECTRIC|"
                            r"(?<![A-Za-z])ELECTRIC(?![A-Za-z])", re.I)
# an engine that names its fuel as gasoline ("4 Cyl 2.5 L GAS", "5.3L V8 - Flex");
# hybrids are read first ("FULL HYBRID EV-GAS")
_FIT_GAS_RE = re.compile(r"(?<![A-Za-z-])(?:GAS(?:OLINE)?|FLEX(?:[\s-]?FUEL)?|FFV|E85)(?![A-Za-z])", re.I)
_FIT_DIESEL_RE = re.compile(r"DIESEL|(?<![A-Za-z])(?:TDI|CRD|ECODIESEL|DURAMAX|POWER\s*STROKE)(?![A-Za-z])", re.I)


def _fit_lit(e: str):
    m = _FIT_LIT_RE.search(str(e or ""))
    return round(float(m.group(1)), 1) if m else None


def _lit_in(xs, x) -> bool:
    return any(abs(x - y) < 0.05 for y in xs)


def _trans_terms(text: str) -> set:
    t = str(text or "")
    return ({"manual"} if _MANUAL_RE.search(t) else set()) | ({"auto"} if _AUTO_RE.search(t) else set())


def _row_engine_names(notes, site: str) -> set:
    """Every engine (litres) a row's option column names anywhere."""
    if site not in policy.DRIVE_CONFIG_FVO_SITES:
        return set()
    out = set()
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if m:
            out |= _engine_terms(m.group(1))
    return out


def _row_engine_trans(notes, site: str):
    """(engines, trans) one own-page row's option column limits it to:
    engines = frozenset of litres when every configuration names an engine,
    trans = 'manual' / 'auto' when every configuration names one class; None
    for no limit. Config-tuple option columns only."""
    if site not in policy.DRIVE_CONFIG_FVO_SITES:
        return None, None
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if not m:
            continue
        parts = [pt for alt in _split_top_plus(m.group(1), ",") for pt in _split_top_plus(alt, "+")]
        if not parts:
            return None, None
        es = [_engine_terms(pt) for pt in parts]
        xs = [_trans_terms(pt) for pt in parts]
        eng = frozenset().union(*es) if all(es) else None
        tr = next(iter(xs[0])) if all(len(x) == 1 for x in xs) and len({next(iter(x)) for x in xs}) == 1 else None
        return eng, tr
    return None, None


def _fit_drive(f) -> object:
    """Drive allowed by one product-page fitment row: every trim naming a
    drive ('SUV AWD, SUV LT AWD'), or the drive values of an option-layout
    row ('..., Four-Wheel Drive'). None when it does not restrict."""
    if f.layout == "trim" and f.trims:
        # each trim (or, on gmpartsgiant, each option-column configuration)
        # is one configuration: a trim without a drive fits any drive
        out = []
        for tr in f.trims:
            pos, neg, _ = _drive_terms(tr)
            if not pos and not neg:
                return None
            out.append(_drive_allowed(pos, neg))
        return _drive_union(out)
    pos, neg = set(), set()
    for o in f.options or []:
        p, n, _ = _drive_terms(o)
        pos |= p
        neg |= n
    return _drive_allowed(pos, neg)


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
        if re.search(r"production\s+date", n or "", re.I):
            wins += [(m1, y1, "", "") for m1, y1 in _PROD_FROM_RE.findall(n or "")]
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


# ------------------------------------------- round4-1119 (hub decisions 1-3)
# Build windows (policy.LIKELY_BUILD_WINDOW_RULE). Months are year*12+month;
# an open end is _WIN_OPEN. The forms the catalogs print in a "Production
# Date" field (census of oem-raw@dca9cd84 and @57e8b5b9): "08/2009-01/2010",
# "from 01/2010" (nissan/infiniti/lexus/ford), "till 05/2012" (hyundai), comma
# lists of those, and subarupartsdeal's "200409 - 200608". A bare "05/2012"
# (hyundai/kia/lexus, 138 rows) says neither start nor end and is not read.
_WIN_OPEN = 10 ** 6
# round5-1119: other model-year pages whose dated rows of a number narrow an
# undated listing on T's page (decision 3): within this many model years of T
_OTHER_PAGE_SPAN = None
_WIN_RANGE_RE = re.compile(r"(?<![0-9/])(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})/(\d{4})(?![0-9/])")
_WIN_FROM_RE = re.compile(r"(?:^|[\s,:])from\s+(\d{1,2})/(\d{4})(?![0-9/])", re.I)
_WIN_TILL_RE = re.compile(r"(?:^|[\s,:])(?:till|until|up\s+to)\s+(\d{1,2})/(\d{4})(?![0-9/])", re.I)
_WIN_SUBARU_RE = re.compile(r"(?<![0-9])((?:19|20)\d{2})(0[1-9]|1[0-2])\s*-\s*((?:19|20)\d{2})(0[1-9]|1[0-2])(?![0-9])")
_PROD_FIELD_RE = re.compile(r"^\s*production\s+date\s*:\s*(.*)$", re.I)


def _row_windows(notes) -> list:
    """[(a, b)] month windows a row's "Production Date" field prints, [] when
    it prints none (the row is listed for the whole model year)."""
    out = []
    for n in notes or []:
        m = _PROD_FIELD_RE.match(n or "")
        if not m:
            continue
        body = m.group(1)
        for m1, y1, m2, y2 in _WIN_RANGE_RE.findall(body):
            out.append((int(y1) * 12 + int(m1), int(y2) * 12 + int(m2)))
        for m1, y1 in _WIN_FROM_RE.findall(body):
            out.append((int(y1) * 12 + int(m1), _WIN_OPEN))
        for m1, y1 in _WIN_TILL_RE.findall(body):
            out.append((0, int(y1) * 12 + int(m1)))
        for y1, m1, y2, m2 in _WIN_SUBARU_RE.findall(body):
            out.append((int(y1) * 12 + int(m1), int(y2) * 12 + int(m2)))
    return out


def _my_range(year: int) -> tuple:
    """The model year as the production-date rule takes it: 07/(year-1) - 06/year."""
    return (year - 1) * 12 + 7, year * 12 + 6


def _win_merge(wins) -> list:
    out = []
    for a, b in sorted(wins):
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _win_gap(wins, year: int) -> list:
    """Months of the model year the windows leave out, as [(a, b)] runs."""
    lo, hi = _my_range(year)
    gaps, cur = [], lo
    for a, b in _win_merge(wins):
        if b < cur or a > hi:
            continue
        if a > cur:
            gaps.append((cur, min(a - 1, hi)))
        cur = max(cur, b + 1)
        if cur > hi:
            break
    if cur <= hi:
        gaps.append((cur, hi))
    return gaps


def _win_intersect(x, y) -> list:
    """Months both merged window lists cover."""
    out = []
    for a1, b1 in _win_merge(x):
        for a2, b2 in _win_merge(y):
            a, b = max(a1, a2), min(b1, b2)
            if a <= b:
                out.append((a, b))
    return _win_merge(out)


def _win_overlap(wins, a: int, b: int) -> int:
    return sum(max(0, min(y, b) - max(x, a) + 1) for x, y in _win_merge(wins))


def _mm(m: int) -> str:
    return f"{(m - 1) % 12 + 1:02d}/{(m - 1) // 12}"


def _ym(m: int) -> str:
    return f"{(m - 1) // 12}-{(m - 1) % 12 + 1:02d}"


def _win_label(wins) -> str:
    """'built 08/2009-01/2010' / 'built from 01/2010' / 'built to 12/2005' (the
    window as the catalog prints it)."""
    parts = []
    for a, b in _win_merge(wins):
        if b >= _WIN_OPEN:
            parts.append(f"from {_mm(a)}")
        elif a <= 0:
            parts.append(f"to {_mm(b)}")
        else:
            parts.append(f"{_mm(a)}-{_mm(b)}")
    return "built " + ", ".join(parts)


def _win_gate(wins) -> str:
    """The app gate value: '2009-08..2010-01', '2010-01..', '..2005-12'; runs
    joined by ','."""
    parts = []
    for a, b in _win_merge(wins):
        parts.append(f"{_ym(a) if a > 0 else ''}..{_ym(b) if b < _WIN_OPEN else ''}")
    return ",".join(parts)


# Same-option drive siblings (policy.LIKELY_DRIVE_SIBLING_RULE): the option
# clauses of a row (each "Fitting Vehicle Options" alternative, with the
# row's other condition notes), compared with a sibling's after its drive
# words are taken out; asterisks (Nissan option markers) are ignored.
_CLAUSE_SKIP_RE = re.compile(r"^\s*(?:production\s+date|require\s+quantity|package\s+quantity|callout\s+name|"
                             r"location|replaced\s+by|replaces)\s*:", re.I)
_NISSAN_AUTO_RE = re.compile(r"(?:^|\.)\s*\*?AUTO\s*(?:\.|$)")


def _clause_tokens(text: str) -> tuple:
    return tuple(re.findall(r"[A-Z0-9#/]+", str(text or "").upper().replace("*", "")))


def _row_clauses(notes, site: str) -> list:
    """[(tokens without drive words, positive drive classes, negated classes)]
    per configuration of one row: each "Fitting Vehicle Options" alternative
    (on the config-tuple sites, policy.DRIVE_CONFIG_FVO_SITES, each "+" part
    too, as _fvo_drive reads them), joined with the row's other condition
    notes; [((), set(), set())] for a row with no option text."""
    return [c[:3] for c in _row_clauses_star(notes, site)]


def _row_clauses_star(notes, site: str) -> list:
    """_row_clauses with a 4th field: True when the configuration carries the
    catalog's leading "*" (round5-1119, hub decision 3: an asterisk alone is
    not a drive split, so a sibling clause must carry the same mark)."""
    fvo, other = [], []
    for n in notes or []:
        if _CLAUSE_SKIP_RE.match(n or ""):
            continue
        m = _FVO_BODY_RE.match(n or "")
        if m:
            for alt in _split_top_plus(m.group(1), ","):
                fvo += _split_top_plus(alt, "+") if site in policy.DRIVE_CONFIG_FVO_SITES else [alt]
        else:
            other.append(n)
    rest = " | ".join(other)
    out = []
    for alt in fvo or [""]:
        text = f"{alt} | {rest}" if rest else alt
        pos, neg, left = _drive_terms(text)
        if site in _NISSAN_SITES and _NISSAN_AUTO_RE.search(alt):
            pos = set(pos) | {"a4wd"}       # the Nissan drive field: 2WD / 4WD / AUTO
            left = re.sub(r"(?:(?<=\.)|^)\s*\*?AUTO\s*(?=\.|$)", " ", left)
        out.append((_clause_tokens(left), set(pos), set(neg), alt.lstrip().startswith("*")))
    return out


# round5b-1119 (hub decision 1, 2026-11-19): the leading "*" of a Nissan
# option clause has no legend in the raw (census of oem-raw@57e8b5b9 and
# @dca9cd84: no text names what it marks), so a vehicle-year whose drive or
# engine limit a starred configuration decides is not a claim the catalog
# states (rule 3) and is held, reason "held_starred_scope", until the mark is
# explained. "Decides": re-reading T's page without the starred
# configurations (the number's own and its siblings') changes the vehicle-
# year's drive limit (drive / drive_not / part-time) or its engine limit, or
# leaves it out. Where the number is listed for T only through starred
# configurations (leaving them out would remove the claim, not its scope),
# they are kept with their drive and engine words unread instead, and held
# when the number is then no longer listed for T (Curation._star_view).
# A starred configuration that changes neither stays as it is. Namespaces it
# applies to: kept here, not in policy.py, so policy_sha256 and every shipped
# namespace's claims stay as they are (hub decision 3); move it to policy.py
# with the next policy edit.
STARRED_SCOPE_NS = frozenset({"nissan"})

# round6-1119 (hub decisions 2026-11-19 ~10:10 UTC, after the sixth
# independent nissan check, groups/_report/nissan_verify_2026-11-19f.json):
#  1 a cab gate is stated only when the number's own evidence for the
#    vehicle-year carries the cab (own-row KC/CC/T codes or cab words, or every
#    fitment trim of the number for that year naming it); an inferred cab
#    limit (rear_cab_of: a rear-door part read as crew cab from the page's
#    structure) holds the vehicle-year out, reason held_cab_inferred (every
#    namespace);
#  2 a vehicle-year the number is listed for only through starred
#    configurations is held, reason held_starred_only (STARRED_SCOPE_NS);
#  3 a gas-only gate also rules out the hybrid's own displacement
#    (HYBRID_ENG_NOT_NS);
#  4 every build window that cuts the model-year span is gated
#    (ROUND6_WINDOW_KINDS adds no_other_row) or leaves at the note cap;
#  5 option text that ties the part to a transmission (or to a drive for one
#    transmission) the gates do not enforce holds the vehicle-year, reason
#    held_option_tie (config-tuple sites; a gate whose wording would state a
#    basis the row does not carry is not added: no app change);
#  6 other model-year pages that date the number differently are read
#    narrowly (_pn_other_windows).
# Kept here, not in policy.py: policy_sha256 does not move.
HYBRID_ENG_NOT_NS = frozenset({"nissan"})
ROUND6_WINDOW_KINDS = ("unlinked", "no_page", "linked", "no_other_row")
# round7-1119 (hub 2026-11-19 ~11:40 UTC, after check 1119g): per-page cut
# test (1), changeover months gated on both sides (2), date splits read from
# other pages (3); cross-position groups held (4); the star-blind reading in
# starred_scope (5).
ROUND7_WINDOW_KINDS = ROUND6_WINDOW_KINDS + ("changeover", "split")
# round8-1119 (hub 2026-11-19 after check 1119h): the nissan candidate claims
# only what a vehicle-year's own pages carry. Vehicle-years held:
#   held_no_own_page        no list page of its own in the raw for the number (1)
#   held_window_other_page  its build window read from another model year's page (2)
#   held_undated_siblings   same-option numbers on its page, none dated (3)
#   held_plus_reading       the claim depends on reading "+" as "or" between
#                           configurations naming different engines or drives (6)
# "gas only" where the hybrid's pages were never read is worded "checked on
# gas-model pages" (5). Shipped namespaces: census only (round8_census).
ROUND8_NS = frozenset({"nissan"})
# round9-1119 (hub 2026-11-19 after check 1119i, before nissan ships):
#  A  the note says what the number is, from the catalog's own part name:
#     "Motor Assy-Regulator" -> "window motor only"; a group whose names mix a
#     motor and a regulator, name another component, or cannot be read from
#     the raw is held (held_part_name); census <ns>.round9_names.json;
#  B1 held_variant_unread: the year index offers variant pages (other than
#     the hybrid one, which the gas gate covers) the raw does not hold;
#  B2 held_twin_changeover: undated beside a same-option number that changes
#     over inside the model year (dated edge inside the span, or the number's
#     own predecessor / successor listed for the same configuration);
#  B3 held_body_mark: undated beside a same-option number that differs only
#     in an unexplained leading body code (WAG / LWB; KC / CC / T read as cabs);
#  B4 held_drive_open: a narrower same-part number lists the configuration
#     with a drive word, the row names none and no gate reads it;
#  C  the label and note name the site the pages came from (Infiniti catalog).
ROUND9_NS = frozenset({"nissan"})
# round10-1119 (hub 2026-11-19, after round 9's A5 measure): live makes whose
# window-regulator motor numbers ("Motor - Window Regulator", "Window Motor",
# "Motor Assembly-Regulator") said nothing about it: positions.packaging()
# reads those names as 'reg?' because the head also says "Regulator", and
# 'reg?' has no words. positions.py feeds policy_sha256, so the reading is
# here: the finished note gains 'window motor only' and nothing else changes;
# a note the words would take past the cap, a number whose names mix a motor
# and a regulator, or one with no name in the raw, holds the group.
ROUND10_NS = frozenset({"mopar", "subaru"})
_R10_MOTOR_RE = re.compile(r"^\s*(?:power\s+)?(?:window\s+)?motor\b", re.I)
# round10b-1119 (hub, after the round-10 check: mopar 68079283AB is named
# "Motor - Window Regulator" / "Window Motor" but its record's description
# says "Window Regulator, Front Driver Side"): the kind is read from every
# naming field the raw prints (list rows main, aux; records name, aux,
# description, other_names; ';'-separated values apart). A number whose
# names disagree in kind, a motor beside a regulator or a regulator with its
# motor, gets no packaging words and its group is held (mopar, subaru, nissan).
ROUND10B_NS = frozenset({"mopar", "subaru", "nissan"})
_R10B_REGMOTOR_RE = re.compile(r"\bmotor\s+(?:and|&)\s+regulator\b|\bregulator\s+(?:and|&)\s+motor\b|"
                               r"\bregulator\b.*\b(?:with|w/)\s*motor\b", re.I)
_R10B_MOTOR_RE = re.compile(r"^\s*(?:power\s+)?(?:window\s+)?motor\b|\b(?:window|regulator)\s+motor\b|"
                            r"\bmotor\s+ass(?:y|embly)\b", re.I)
_R10B_REG_RE = re.compile(r"\bregulator\b", re.I)


def _kind10b(name: str) -> str:
    """'regulator+motor' | 'motor' | 'regulator' | '' (says neither)."""
    if _R10B_REGMOTOR_RE.search(name):
        return "regulator+motor"
    if _R10B_MOTOR_RE.search(name):
        return "motor"
    return "regulator" if _R10B_REG_RE.search(name) else ""


# round11-1120 (hub 2026-11-20, from round 10's item-4 measure): packaging
# words read from every naming field the raw prints (as round 10b), on every
# live namespace. bumper-front / bumper-rear: a number named as the cover
# ("Cover, Front Bumper", "Bumper Cover", "Fascia") says "bumper cover", and
# "bumper cover only" when each of its own pages lists a reinforcement as a
# separate number; "Cover, Front Bumper Guard" says "bumper guard cover".
# tail-lights: "Lens & Body" (or "Lens & Housing") says "lens and body unit".
# window-regulator: a number whose name fields all name the regulator with its
# motor says "regulator with motor". Values that disagree in kind (a cover
# beside a bumper or reinforcement, a lens-and-body unit beside a lamp
# assembly, a motor beside a regulator) hold the group, as does a note the
# words would take past the cap or a group whose note already carries other
# packaging words. Nothing else in a group changes.
ROUND11_NS = frozenset({"gm", "mopar", "toyota", "ford", "hmg", "subaru", "vag", "mb", "nissan"})
_R11_PHRASE = {"cover": "bumper cover", "cover_only": "bumper cover only", "guard": "bumper guard cover",
               "lens-body": "lens and body unit", "regulator+motor": "regulator with motor"}


def _kind11(cat: str, name: str) -> str:
    """The kind one naming value carries in cat ('' says nothing)."""
    if cat in ("bumper-front", "bumper-rear"):
        if re.search(r"bumper\s+guard", name, re.I):
            return "guard"
        if re.search(r"\bcover\b|\bfascia\b", name, re.I):
            return "cover"
        if re.search(r"reinf|impact\s+bar|\bbeam\b", name, re.I):
            return "reinforcement"
        return "bumper" if re.search(r"\bbumper\b|face\s*bar", name, re.I) else ""
    if cat == "tail-lights":
        if re.search(r"lens\s*(?:&|and)\s*(?:body|housing)", name, re.I):
            return "lens-body"
        if re.search(r"^\s*lens\b", name, re.I):
            return "lens"
        if re.search(r"bulb|socket|harness|\bwire\b", name, re.I):
            return "socket"
        return "assembly" if re.search(r"\bass(?:y|embly)\b", name, re.I) else ""
    if cat == "window-regulator":
        if re.search(r"\bincludes?\s+motor\b", name, re.I):
            return "regulator+motor"
        return _kind10b(name)
    return ""


_R10_REG_RE = re.compile(r"^\s*(?:power\s+)?(?:(?:front|rear)\s+)?(?:door\s+)?(?:window\s+)?regulator\b", re.I)
_NAME_MOTOR_RE = re.compile(r"^\s*motor\s+ass(?:y|embly)\b", re.I)
_NAME_REG_RE = re.compile(r"^\s*regulator\s+ass(?:y|embly)\b", re.I)
_NAME_COMPONENT_RE = re.compile(r"^\s*(glass|cover|lens|bezel|knob|cap|garnish|holder|bulb|socket|finisher|"
                                r"housing|base|bracket|switch|cable|harness|motor)\b", re.I)
_SITE_BRAND = {"www.nissanpartsdeal.com": "Nissan", "www.infinitipartsdeal.com": "Infiniti"}


def _starred(cfg: str) -> bool:
    return str(cfg or "").lstrip().startswith("*")


def _unstar_notes(notes, site: str):
    """notes with the starred configurations of each "Fitting Vehicle Options"
    note left out (each "," alternative; on the config-tuple sites,
    policy.DRIVE_CONFIG_FVO_SITES, each "+" part, as _row_clauses_star reads
    them); None when such a note lists configurations and every one is
    starred (nothing unstarred is left of the row)."""
    out = []
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if not m:
            out.append(n)
            continue
        alts, had = [], False
        for alt in _split_top_plus(m.group(1), ","):
            had = True
            if site in policy.DRIVE_CONFIG_FVO_SITES:
                parts = [p for p in _split_top_plus(alt, "+") if not _starred(p)]
                if parts:
                    alts.append(" + ".join(parts))
            elif not _starred(alt):
                alts.append(alt)
        if not had:
            out.append(n)
            continue
        if not alts:
            return None
        out.append(n[:m.start(1)] + ", ".join(alts))
    return out


_ENGINE_WORD_RE = re.compile(_ENGINE_CODE_RE.pattern, re.I)


def _unstate_cfg(cfg: str) -> str:
    """A starred configuration with its drive words (and the Nissan AUTO
    field) and engine words blanked: the configuration stays, what it says
    about drive and engine is not read."""
    _p, _n, left = _drive_terms(cfg)
    left = re.sub(r"(?:(?<=\.)|^)\s*\*?AUTO\s*(?=\.|$)", " ", left)
    left = _LITRE_RE.sub(" ", _ENGINE_WORD_RE.sub(" ", left))
    return left if _starred(left) else "*" + left.lstrip()


def _unstate_notes(notes, site: str) -> list:
    """notes with each starred configuration's drive and engine words unread
    (_unstate_cfg); the configurations themselves stay."""
    out = []
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if not m:
            out.append(n)
            continue
        alts = []
        for alt in _split_top_plus(m.group(1), ","):
            if site in policy.DRIVE_CONFIG_FVO_SITES:
                alts.append(" + ".join(_unstate_cfg(p) if _starred(p) else p for p in _split_top_plus(alt, "+")))
            else:
                alts.append(_unstate_cfg(alt) if _starred(alt) else alt)
        out.append(n[:m.start(1)] + ", ".join(alts) if alts else n)
    return out


_UNLISTED = "unlisted"


def _starred_dims(rows) -> set:
    """'drive' / 'engine' when a starred configuration of these own rows
    [(notes, site, variant, url)] names a drive (or the AUTO field) / an
    engine."""
    out = set()
    for notes, site, _v, _u in rows:
        for cfg in _starred_cfgs(notes, site):
            p, n, _left = _drive_terms(cfg)
            if p or n or _NISSAN_AUTO_RE.search(cfg):
                out.add("drive")
            if _engine_terms(cfg):
                out.add("engine")
    return out


def _plus_strict_notes(notes, site: str):
    """Round8 decision 6: notes with every option alternative unread whose
    '+' parts name different engines or different drive families (read as one
    configuration, it would contradict itself); None when a note had
    alternatives and none is left."""
    if site not in policy.DRIVE_CONFIG_FVO_SITES:
        return list(notes or [])
    out = []
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if not m:
            out.append(n)
            continue
        alts, had = [], False
        for alt in _split_top_plus(m.group(1), ","):
            had = True
            parts = _split_top_plus(alt, "+")
            engs = {frozenset(e) for e in (_engine_terms(x) for x in parts) if e}
            fams = set()
            for x in parts:
                pos, neg, _l = _drive_terms(x)
                if _NISSAN_AUTO_RE.search(x):
                    pos = set(pos) | {"a4wd"}
                d = _drive_allowed(pos, neg)
                if d:
                    fams.add("4" if set(d) <= _FOUR else "2")
            if len(engs) > 1 or len(fams) > 1:
                continue
            alts.append(alt)
        if had and not alts:
            return None
        out.append(n[:m.start(1)] + ", ".join(alts) if alts else n)
    return out


def _blind_notes(notes, site: str) -> list:
    """notes with the leading '*' of every option configuration taken off."""
    out = []
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if not m:
            out.append(n)
            continue
        alts = []
        for alt in _split_top_plus(m.group(1), ","):
            if site in policy.DRIVE_CONFIG_FVO_SITES:
                alts.append(" + ".join(x.lstrip().lstrip("*").strip() for x in _split_top_plus(alt, "+")))
            else:
                alts.append(alt.lstrip().lstrip("*").strip())
        out.append(n[:m.start(1)] + ", ".join(alts) if alts else n)
    return out


def _year_runs(ys) -> list:
    out = []
    for y in sorted(ys):
        if out and y == out[-1][-1] + 1:
            out[-1].append(y)
        else:
            out.append([y])
    return out


def _starred_cfgs(notes, site: str) -> list:
    """The starred configurations of a row's option notes, as printed."""
    out = []
    for n in notes or []:
        m = _FVO_BODY_RE.match(n or "")
        if m:
            for alt in _split_top_plus(m.group(1), ","):
                parts = _split_top_plus(alt, "+") if site in policy.DRIVE_CONFIG_FVO_SITES else [alt]
                out += [p for p in parts if _starred(p)]
    return out


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


def _likely_note_fits(brand: str, pn: str, text: str, pack: str = "") -> bool:
    """True when the §5.16 note holds text whole: _likely_note cuts an
    over-long reason with '...', which must never cut a cab or drive limit
    (2026-11-18: the old length test compared the already-cut note, so it
    could not fail)."""
    head = _sanitize(f"{brand} catalog lists #{pn} for both — ")
    mid = _sanitize(f"{pack}; {text}" if pack else text)
    return len(head) + len(mid) + len(_LIKELY_TAIL) <= policy.NOTE_MAX_LEN


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


def _sha256_file(path) -> str | None:
    import hashlib
    p = Path(path or "")
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def lot_engines(inv, extras_path) -> dict | None:
    """{(make, model, year): {"lits", "hybrid", "gas"}} over the inventory's
    cars (round3-1119, the engine column's materiality): the displacements
    their decoded engines name (docs/data/vehicle_extras.json "engine", read
    the way docs/app.js pfAmParseEngine reads it), whether one is a hybrid
    (the listing, the VIN series, the VIN trim when usable, or the engine
    naming Hybrid / Electric, as pfOemCarFuel) and whether one is a
    non-hybrid with a decoded engine. None when either input is missing:
    every displacement the catalog attests then counts (fail closed)."""
    p = Path(extras_path or "")
    if not inv or not p.exists():
        return None
    ex = json.loads(p.read_text())
    fields = ex.get("extraFields") or []
    ei = fields.index("engine") if "engine" in fields else 2
    extras = ex.get("extras") or {}
    f = inv.get("fields") or []
    iid, imk, imd, iy = f.index("id"), f.index("make"), f.index("model"), f.index("year")
    vp = inv.get("vpic") or {}
    out = defaultdict(lambda: {"lits": set(), "hybrid": False, "gas": False})
    for i, r in enumerate(inv["vehicles"]):
        e = extras.get(str(r[iid]))
        es = str(e[ei]) if e and len(e) > ei and e[ei] else ""
        v = vp.get(str(i)) or ["", "", "", "", ""]
        name = " ".join(str(x) for x in (r[imd], v[2] if len(v) > 2 else "",
                                         v[0] if len(v) > 1 and v[1] == "usable" else "") if x)
        m = re.search(r"(\d+\.\d+)\s*l\b", es.lower()) or re.search(r"(\d+\.\d+)l", es.lower())
        d = out[(r[imk], r[imd], r[iy])]
        if m:
            d["lits"].add(round(float(m.group(1)), 1))
        if re.search(r"\bhybrid\b", name + " " + es, re.I) or re.search(r"\belectric\b", es, re.I):
            d["hybrid"] = True
        elif m:
            d["gas"] = True
    return {k: {"lits": frozenset(v["lits"]), "hybrid": v["hybrid"], "gas": v["gas"]} for k, v in out.items()}


def model_bodies(inv, js, decodes_path) -> dict:
    """{(make, model): {body style}} and {(make, model, year): {body style}}
    over the inventory's VINs, from the vPIC
    decode cache via junkyard_scraper.body_style_from_vpic (never from the
    model name). Unknown bodies are left out. Missing inputs give {}, which
    refuses every rear-wiper group (fail closed)."""
    import gzip
    p = Path(decodes_path or "")
    if not inv or js is None or not p.exists():
        return {}
    dec = json.loads(gzip.open(p).read())
    f = inv.get("fields") or []
    iv, imk, imd, iy = f.index("vin"), f.index("make"), f.index("model"), f.index("year")
    out = defaultdict(set)
    for r in inv["vehicles"]:
        b = js.body_style_from_vpic(dec.get(r[iv]), r[imk])
        if b:
            out[(r[imk], r[imd])].add(b)
            out[(r[imk], r[imd], r[iy])].add(b)
    return {k: frozenset(v) for k, v in out.items()}


def model_body_counts(inv, js, decodes_path) -> dict:
    """{(make, model, year): {silhouette: cars}} over the inventory's VINs
    from the vPIC decode cache (junkyard_scraper.body_style_from_vpic; wagon
    and SUV count as one silhouette). Unknown bodies are left out. Missing
    inputs give {}: the §5.16 body-variant rule then reads catalog pages only."""
    import gzip
    p = Path(decodes_path or "")
    if not inv or js is None or not p.exists():
        return {}
    dec = json.loads(gzip.open(p).read())
    f = inv.get("fields") or []
    iv, imk, imd, iy = f.index("vin"), f.index("make"), f.index("model"), f.index("year")
    out = defaultdict(Counter)
    for r in inv["vehicles"]:
        vp = dec.get(r[iv])
        b = js.body_style_from_vpic(vp, r[imk])
        # a car whose decode names another model is not a body of this feed
        # model (lots list some Outbacks as "Legacy": vPIC model Outback, SUV)
        dm, fm = _squash_model((vp or {}).get("model")), _squash_model(r[imd])
        if b and (not dm or dm.startswith(fm) or fm.startswith(dm)):
            out[(r[imk], r[imd], r[iy])][_SILHOUETTE.get(b, b)] += 1
    return {k: dict(v) for k, v in out.items()}


def _squash_model(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


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
    ap.add_argument("--decodes", default=str(MM.INVENTORY_PATH.parent / "vin_decodes.json.gz"),
                    help="vPIC decode cache (rear wiper body gate); missing file: every rear wiper group refused")
    ap.add_argument("--extras", default=str(MM.INVENTORY_PATH.parent / "vehicle_extras.json"),
                    help="the lot's decoded engines (engine-column limits need a model-year to offer the "
                         "missing displacement: year page or a lot car); missing file: every displacement "
                         "the catalog attests counts (more limits)")
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
    bodies = model_bodies(inv, js, a.decodes)
    body_counts = model_body_counts(inv, js, a.decodes)
    lot_eng = lot_engines(inv, a.extras)
    if lot_eng is None:
        print(f"[curate] no lot engines ({a.extras}): every displacement the catalog attests counts",
              file=sys.stderr)
    out = Path(a.out)
    results = {}
    no_ns = [s for s in src.sites() if s not in policy.SITE_NS]
    for ns in nss:
        opts = Options(as_of=a.as_of, fixtures=a.fixtures, model_map=mm, model_map_path=Path(a.model_map),
                       inventory=inv, js=js, model_bodies=bodies, body_counts=body_counts,
                       lot_engines=lot_eng)
        cur, doc = curate(ns, src, opts)
        results[ns] = cur
        if not cur.raw_meta:
            print(f"[curate] {ns}: no raw for its sites; skipped", file=sys.stderr)
            continue
        problems = V.structural(doc, V.context_from(js, mm))
        rep, completion = cur.report(doc, inv_counts)
        rep["model_map_report"] = mrep
        # curation inputs outside the policy hash, pinned by content (hub 2026-11-10):
        # a changed decodes or inventory file must never change shipped groups unseen
        rep["inputs"] = {"inventory": a.inventory, "inventory_sha256": _sha256_file(a.inventory),
                         "decodes": a.decodes, "decodes_sha256": _sha256_file(a.decodes),
                         "extras": a.extras, "extras_sha256": _sha256_file(a.extras)}
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
    for ns in sorted(results):
        sh = getattr(results[ns], "starred_held", None)
        if ns in STARRED_SCOPE_NS and sh is not None:
            vy = Counter(k for g in sh for h in g["held"] for k in h["kinds"])
            write_json(out / "_report" / f"{ns}.starred_held.json", {
                "note": "round5b-1119 (hub decision 1, 2026-11-19): vehicle-years held because a starred ('*') "
                        "option configuration decides their drive or engine limit; the mark has no legend in the "
                        "raw. reason held_starred_scope ('starred clause decides scope'). round6-1119 (hub "
                        "decision 2): also every vehicle-year the number is listed for only through starred "
                        "configurations, reason held_starred_only, kind starred_only. unit vehicle-year: the "
                        "group ships without them (kept_apps, after every hold); unit group: the whole group is "
                        "held. kinds: a = drive gate, b = engine gate, c_drive / c_engine = no gate, the starred "
                        "configuration widens it. Not shipped; they come back when the mark is explained.",
                "ns": ns, "raw": results[ns].src.commit or "fixtures",
                "groups": len(sh), "groups_held_whole": sum(g["unit"] == "group" for g in sh),
                "vehicle_years": sum(len(g["held"]) for g in sh),
                "vehicle_years_by_kind": dict(sorted(vy.items())),
                "groups_by_kind": {k: sum(any(k in h["kinds"] for h in g["held"]) for g in sh)
                                   for k in ("a", "b", "c_drive", "c_engine", "starred_only")},
                "held": sh})
        r6 = getattr(results[ns], "round6_held", None)
        if r6:
            rv = Counter(r for g in r6 for h in g["held"] for r in h["reasons"])
            write_json(out / "_report" / f"{ns}.round6_held.json", {
                "note": "round6-1119 (hub decisions 2026-11-19 ~10:10 UTC): vehicle-years held out. "
                        "held_cab_inferred (decision 1): a cab gate the number's own row for that vehicle-year "
                        "does not carry (read from page structure or another year); not reworded, held. "
                        "held_option_tie (decision 5): the option text ties the part to a transmission (or to "
                        "a drive for one transmission) that no gate the app has can state from the row itself "
                        "(uncovered = what the gates would let through that no configuration covers; via "
                        "sibling = only a same-part sibling's transmission makes the tie). unit vehicle-year: "
                        "the group ships without them (kept_apps, after every hold); unit group: held whole.",
                "ns": ns, "raw": results[ns].src.commit or "fixtures",
                "groups": len(r6), "groups_held_whole": sum(g["unit"] == "group" for g in r6),
                "vehicle_years_by_reason": dict(sorted(rv.items())),
                "groups_by_reason": {k: sum(any(k in h["reasons"] for h in g["held"]) for g in r6) for k in sorted(rv)},
                "held": r6})
        r8 = getattr(results[ns], "round8_rows", None)
        if ns in ROUND8_NS and r8 is not None:
            cur8 = results[ns]
            shipped = {(g["cat"], tuple(g["pn"])) for g in getattr(cur8, "_likely_out", [])}
            refs = {}
            for x in cur8.refusals:
                if x.get("pn"):
                    refs.setdefault((x["cat"], x["pn"]), x["reason"])
            groups = defaultdict(list)
            for row in r8:
                groups[(row["cat"], tuple(row["pn"]))].append({k: v for k, v in row.items() if k not in ("cat", "pn")})
            held8 = [{"cat": cat8, "pn": list(pn8),
                      "group": "ships without these" if (cat8, pn8) in shipped else
                      f"not shipped ({refs.get((cat8, pn8[0]), 'other')})", "held": rows8}
                     for (cat8, pn8), rows8 in sorted(groups.items())]
            byr = Counter(row["reason"] for row in r8)
            pages = sorted({u for row in r8 if row["reason"] == "held_no_own_page" for u in row["missing_pages"]})
            by_model = Counter(re_m.group(1) for u in pages for re_m in [re.search(r"/(\d{4}-[a-z0-9-]+?)/", u)] if re_m)
            write_json(out / "_report" / f"{ns}.round8_held.json", {
                "note": "round8-1119 (hub decisions 2026-11-19 after check 1119h): the candidate claims only what "
                        "a vehicle-year's own pages carry. held_no_own_page: no list row of its own for the number "
                        "in the raw (missing_pages: the page the claim was seen on, from the product records, for "
                        "a targeted crawl); held_window_other_page: its build window read from another model "
                        "year's page (kind drop: under 5 months of the year); held_undated_siblings: same-option "
                        "numbers on its page, none dated; held_plus_reading: the claim depends on reading '+' as "
                        "'or' between configurations of different engines or drives. Rows are recorded where the "
                        "rule held them; 'group' says whether the group still ships.",
                "ns": ns, "raw": cur8.src.commit or "fixtures", "vehicle_years_by_reason": dict(sorted(byr.items())),
                "groups_by_reason": {k: len({(g["cat"], tuple(g["pn"])) for g in held8 for h in g["held"]
                                             if h["reason"] == k}) for k in sorted(byr)},
                "crawl": {"pages": len(pages), "pages_by_model_year": dict(sorted(by_model.items())),
                          "list": pages},
                "held": held8})
        r9 = getattr(results[ns], "round9_rows", None)
        if ns in ROUND9_NS and r9 is not None:
            cur9 = results[ns]
            shipped9 = {(g["cat"], tuple(g["pn"])) for g in getattr(cur9, "_likely_out", [])}
            write_json(out / "_report" / f"{ns}.round9_held.json", {
                "note": "round9-1119 (hub 2026-11-19 after check 1119i): held_part_name (group), "
                        "held_variant_unread, held_twin_changeover, held_body_mark, held_drive_open (vehicle-years); "
                        "rows are recorded where the rule held them, 'ships' says whether the group still ships.",
                "ns": ns, "raw": cur9.src.commit or "fixtures",
                "vehicle_years_by_reason": dict(sorted(Counter(r["reason"] for r in r9 if "t" in r).items())),
                "groups_by_reason": {k: len({(r["cat"], tuple(r["pn"])) for r in r9 if r["reason"] == k})
                                     for k in sorted({r["reason"] for r in r9})},
                "held": [dict(r, ships=(r["cat"], tuple(r["pn"])) in shipped9) for r in r9]})
            write_json(out / "_report" / f"{ns}.round9_names.json", {
                "note": "round9-1119 A: every candidate group's catalog part names (list rows on every page and "
                        "product records, with site:file:line), the class the rule assigned and the note's words.",
                "ns": ns, "groups": len(cur9.round9_names),
                "by_category_class": dict(sorted(Counter(f"{x['cat']}:{x['class']}" for x in cur9.round9_names).items())),
                "rows": cur9.round9_names})
        r10 = getattr(results[ns], "round10_rows", None)
        if ns in ROUND10B_NS and r10 is not None:
            write_json(out / "_report" / f"{ns}.round10.json", {
                "note": "round10-1119: window-regulator groups whose catalog part name is a motor gain 'window "
                        "motor only' on the finished note (change 'phrase'); a note the words take past the cap, "
                        "mixed or unreadable names hold the group (change 'held'). Names with site:file:line.",
                "ns": ns, "raw": results[ns].src.commit or "fixtures",
                "changed": sum(r["change"] == "phrase" for r in r10), "held": sum(r["change"] == "held" for r in r10),
                "rows": r10})
        r11 = getattr(results[ns], "round11_rows", None)
        if ns in ROUND11_NS and r11:
            write_json(out / "_report" / f"{ns}.round11.json", {
                "note": "round11-1120: packaging words from every naming field (bumper cover, bumper guard cover, "
                        "lens and body unit, regulator with motor) on the finished note (change 'phrase'); names "
                        "that disagree in kind, a note past the cap, or other words already on the note hold the "
                        "group (change 'held'). Names with field, kind and site:file:line.",
                "ns": ns, "raw": results[ns].src.commit or "fixtures",
                "changed": sum(r["change"] == "phrase" for r in r11), "held": sum(r["change"] == "held" for r in r11),
                "rows": r11})
        r7 = getattr(results[ns], "round7_held", None)
        if r7:
            write_json(out / "_report" / f"{ns}.round7_held.json", {
                "note": "round7-1119 (hub decisions 2026-11-19 ~11:40 UTC, decision 4): groups whose number sits in "
                        "another door or position on another model of the group (positions: the slots the number "
                        "takes on each model's own pages), held whole, reason held_cross_position, until the note "
                        "can name the donor's door.",
                "ns": ns, "raw": results[ns].src.commit or "fixtures", "groups": len(r7), "held": r7})
    coll = cross_ns_collisions(results)
    if coll:
        write_json(out / "_report" / "cross_ns_string_collisions.json", coll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
