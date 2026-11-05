"""Raw evidence -> one normalized model (CURATION_SPEC.md §3.1, §5.1, §5.2).

Both dealer templates (SimplePart: toyotapartsnow, jeeppartsdeal; PartsGiant:
the .html catalogs) are normalized into Record / FitRow, and the crawler's
manifests (R1 `raw/<site>.lists.jsonl`, R2 `raw/<site>.years.jsonl`, not
written yet on 2026-11-05) into ListRow / YearManifest. Raw is read from a
git ref (`git show <ref>:raw/<file>`, no checkout) or from a directory.

No network: nothing here imports fetch.py. The rule-drift matcher loads a
site module with a stub `fetch` whose get() raises.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import policy  # noqa: E402

KINDS = {"records": ".jsonl", "lists": ".lists.jsonl", "years": ".years.jsonl"}


# ------------------------------------------------------------------ sources
class RawSource:
    """Reads raw/<site>.<kind> from a git ref or a directory."""

    def __init__(self, ref: str | None = None, raw_dir: str | None = None, repo: str | None = None):
        if bool(ref) == bool(raw_dir):
            raise ValueError("exactly one of ref / raw_dir")
        self.ref, self.raw_dir = ref, (Path(raw_dir) if raw_dir else None)
        self.repo = repo or str(HERE.parents[1])
        self.commit = None
        self._ls: set[str] | None = None
        if ref:
            self.commit = subprocess.run(["git", "-C", self.repo, "rev-parse", ref], check=True,
                                         capture_output=True, text=True).stdout.strip()

    def files(self) -> set[str]:
        if self._ls is None:
            if self.ref:
                out = subprocess.run(["git", "-C", self.repo, "ls-tree", "-r", "--name-only", self.commit],
                                     check=True, capture_output=True, text=True).stdout
                self._ls = {p for p in out.splitlines()}
            else:
                self._ls = {str(p.relative_to(self.raw_dir)).replace(os.sep, "/")
                            for p in self.raw_dir.rglob("*") if p.is_file()}
        return self._ls

    def read(self, path: str) -> str | None:
        if path not in self.files():
            return None
        if self.ref:
            return subprocess.run(["git", "-C", self.repo, "show", f"{self.commit}:{path}"], check=True,
                                  capture_output=True, text=True).stdout
        return (self.raw_dir / path).read_text()

    def sites(self) -> list[str]:
        out = set()
        for p in self.files():
            m = re.match(r"^raw/([^/]+?)\.jsonl$", p)
            if m:
                out.add(m.group(1))
        return sorted(out)

    def has(self, site: str, suffix: str) -> bool:
        return f"raw/{site}{suffix}" in self.files()

    def describe(self) -> dict:
        return {"ref": self.ref or None, "commit": self.commit or "fixtures",
                "dir": str(self.raw_dir) if self.raw_dir else None}


def sha256(text: str | None) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


@dataclass
class Parsed:
    objs: list = field(default_factory=list)          # [(line_no, obj)]
    issues: list = field(default_factory=list)         # [(reason, line_no, detail)]
    refused: str | None = None                         # whole-file refusal reason


def parse_jsonl(text: str | None, fixtures: bool) -> Parsed:
    """§5.1 input acceptance: a bad last line is a torn tail (skipped and
    reported); any other bad line refuses the whole file (corrupt_raw);
    `"synthetic": true` lines are refused unless --fixtures."""
    p = Parsed()
    if not text:
        return p
    lines = text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    last = len(lines)
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            o = json.loads(line)
            if not isinstance(o, dict):
                raise ValueError("not an object")
        except Exception as e:  # noqa: BLE001 - any parse failure is evidence of corruption
            if i == last:
                p.issues.append(("torn_tail", i, str(e)[:80]))
                continue
            p.refused = f"corrupt_raw: line {i}: {str(e)[:80]}"
            p.objs = []
            return p
        if o.get("synthetic") and not fixtures:
            p.issues.append(("synthetic_refused", i, ""))
            continue
        p.objs.append((i, o))
    return p


# ------------------------------------------------------------------ model
@dataclass
class FitRow:
    idx: int
    lo: int
    hi: int
    make: str
    model: str
    trims: list
    engines: list
    options: list
    layout: str        # "trim" | "option"
    raw: str
    trims_from_options: bool = False
    # SimplePart option-layout columns as printed ({header: value}); the
    # evidence re-check compares them with the printed row (§5.3)
    other_columns: dict = field(default_factory=dict)

    def trim_atoms(self) -> frozenset:
        return frozenset(a for t in self.trims for a in trim_atoms(t))

    def engine_keys(self) -> frozenset:
        return frozenset(engine_key(e) for e in self.engines)


@dataclass
class Record:
    site: str
    ns: str
    cat: str
    pn: str
    key: str
    line: int
    template: str
    name: str
    aux: str
    other_names: str
    description: str
    list_url: str
    section: str
    position: str
    list_location: list
    note_texts: list           # this record's own seed-page notes
    replaces: list
    replaced_by: list
    list_replaced_by: list
    chain_unknown: bool
    reman_flag: bool
    rows: list
    flags: list
    evidence_lines: list
    rendered: int | None
    total: int | None
    retrieved: str
    seed: tuple
    via: str | None
    recrawl_of: str | None
    product_url: str
    raw: dict
    problems: list = field(default_factory=list)

    @property
    def pointer(self) -> str:
        return f"{self.site}:records:L{self.line}"

    @property
    def oem_names(self) -> list:
        return [n for n in (self.name, self.aux) if n]


@dataclass
class ListRow:
    site: str
    seed: tuple
    cat: str
    list_url: str
    pn: str
    section: str
    main: str
    aux: str
    notes: list          # note strings (Part Notes / Notes / remark / info)
    locations: list      # Location values
    replace: str | None
    matched: bool
    excluded_by: str | None
    product: str | None
    retrieved: str
    line: int
    status: object
    variant: str = ""

    @property
    def pointer(self) -> str:
        return f"{self.site}:lists:L{self.line}"


@dataclass
class YearManifest:
    site: str
    seed: tuple
    variant: str
    year_url: str
    status: object
    final_url: str
    title: str
    subs: list
    trims: list
    engines: list
    variants: list
    retrieved: str
    line: int

    @property
    def pointer(self) -> str:
        return f"{self.site}:years:L{self.line}"


# --------------------------------------------------------------- normalizers
def _clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def trim_atoms(trim: str) -> list:
    """'Base (4WD, FWD)' -> [('base', '4wd'), ('base', 'fwd')]; 'LE' ->
    [('le', '')] (§5.5). Case-folded, whitespace collapsed."""
    t = _clean(trim).lower()
    m = re.match(r"^(.*?)\s*\((.*)\)\s*$", t)
    if m and m.group(1):
        subs = [x.strip() for x in m.group(2).split(",") if x.strip()]
        return [(m.group(1).strip(), s) for s in subs] or [(m.group(1).strip(), "")]
    return [(t, "")] if t else []


def engine_key(printed: str):
    """§5.5 engine keys; anything unparsed is ('?', raw), which fails every
    universe test."""
    s = _clean(printed)
    u = s.upper()
    m = re.match(r"^(\d+)\s*CYL\s+(\d+\.\d+)\s*L\b(.*)$", u)
    if m:
        cyl, lit, rest = int(m.group(1)), float(m.group(2)), m.group(3)
        if "FCEV" in rest or "FUEL CELL" in rest:
            return ("?", s)
        if "PHEV" in rest or "PLUG-IN" in rest:
            fuel = "phev"
        elif "HYBRID" in rest or "FHEV" in rest or "HEV" in rest:
            fuel = "hybrid"
        elif "CNG" in rest:
            fuel = "cng"
        elif "FLEX" in rest:
            fuel = "flex"
        elif "DIESEL" in rest:
            fuel = "diesel"
        elif "GAS" in rest:
            fuel = "gas"
        elif rest.strip() == "":
            fuel = None
        else:
            return ("?", s)
        return (cyl, lit, fuel)
    m = re.match(r"^(\d+\.\d+)\s*L\s+(?:L|I|V|H|W)(\d+)$", u)
    if m:
        return (int(m.group(2)), float(m.group(1)), None)
    return ("?", s)


def _seed(o: dict) -> tuple:
    sd = o.get("seed") or {}
    try:
        return (sd.get("make") or "", sd.get("model") or "", int(sd.get("year") or 0))
    except (TypeError, ValueError):
        return (sd.get("make") or "", sd.get("model") or "", 0)


def template_of(site: str, o: dict) -> str:
    if "list_section" in o or site in policy.SIMPLEPART_SITES:
        return "simplepart"
    return "partsgiant"


_POS_ONLY = re.compile(r"^(?:(?:front|rear)\s+)?(?:left|right|driver|passenger|lh|rh)(?:\s+side)?$", re.I)


def _split_pns(s) -> list:
    if not s:
        return []
    if isinstance(s, list):
        return [_clean(x) for x in s if _clean(x)]
    return [x for x in re.split(r"[,\s]+", _clean(s)) if x]


def to_record(site: str, ns: str, line: int, o: dict) -> Record:
    tpl = template_of(site, o)
    cat = o.get("category") or ""
    pn = _clean(o.get("pn"))
    rows = []
    if tpl == "simplepart":
        name, aux = _clean(o.get("name")), _clean(o.get("aux_desc"))
        notes = [n for n in (o.get("list_notes") or []) if _clean(n)]
        locs = [x for x in (o.get("list_location") or []) if _clean(x)]
        rb = _split_pns(o.get("replaced_by"))
        lrb = _split_pns(o.get("list_replaced_by"))
        chain_unknown = False
        for i, f in enumerate(o.get("fitment") or []):
            other = f.get("other_columns")
            rows.append(FitRow(i, int(f["years"][0]), int(f["years"][1]), _clean(f.get("make")),
                               _clean(f.get("model")), list(f.get("trims") or []),
                               list(f.get("engines") or []), [], "option" if other else "trim",
                               f.get("raw") or "",
                               other_columns=dict(other) if isinstance(other, dict) else
                               ({"?": str(other)} if other else {})))
    else:
        name, aux = _clean(o.get("name")), ""
        info = [_clean(x) for x in (o.get("list_info") or []) if _clean(x)]
        notes, locs, lrb = [], [], []
        if _clean(o.get("list_remark")):
            notes.append(_clean(o.get("list_remark")))
        for x in info:
            m = re.match(r"^location\s*:\s*(.+)$", x, re.I)
            if m:
                locs.append(m.group(1))
                continue
            m = re.match(r"^replaced\s+by\s*:\s*(.+)$", x, re.I)
            if m:
                lrb += _split_pns(m.group(1))
                continue
            if _POS_ONLY.match(x):       # Mopar bare "Right" / "Left" list position
                locs.append(x)
                continue
            notes.append(x)
        rb_raw = o.get("replaced_by")
        chain_unknown = bool(rb_raw and re.search(r"multisupersession", str(rb_raw), re.I))
        rb = [] if chain_unknown else _split_pns(rb_raw)
        if any(re.search(r"multisupersession", x, re.I) for x in lrb):
            chain_unknown = True
            lrb = [x for x in lrb if not re.search(r"multisupersession", x, re.I)]
        opt_trims = policy.OPTION_COLUMN_IS_TRIMS.get(site, False)
        for i, f in enumerate(o.get("fitment") or []):
            opts = list(f.get("options") or [])
            layout = "option" if (opts and not opt_trims) else "trim"
            rows.append(FitRow(i, int(f["years"][0]), int(f["years"][1]), _clean(f.get("make")),
                               _clean(f.get("model")), list(f.get("trims") or []),
                               list(f.get("engines") or []), opts, layout, f.get("raw") or "",
                               trims_from_options=bool(opts and opt_trims)))
    return Record(
        site=site, ns=ns, cat=cat, pn=pn, key=policy.pn_key(ns, pn), line=line, template=tpl,
        name=name, aux=aux, other_names=_clean(o.get("other_names")),
        description=_clean(o.get("description")), list_url=o.get("list_url") or "",
        section=o.get("list_section") or "diagram", position=_clean(o.get("position")),
        list_location=locs, note_texts=notes, replaces=_split_pns(o.get("replaces")),
        replaced_by=rb, list_replaced_by=lrb, chain_unknown=chain_unknown,
        reman_flag=bool(o.get("reman")), rows=rows,
        # list_flags (Honda bare "Switch Assy." rows) are flags too (§5.3)
        flags=[str(x) for x in list(o.get("flags") or []) + list(o.get("list_flags") or []) if str(x).strip()],
        evidence_lines=list(o.get("evidence_lines") or []),
        rendered=o.get("fitment_rows_rendered"), total=o.get("fitment_rows_total"),
        retrieved=o.get("retrieved") or "", seed=_seed(o), via=o.get("via"),
        recrawl_of=(str(o["recrawl_of"]) if o.get("recrawl_of") is not None else None),
        product_url=o.get("product_url") or "", raw=o)


def _extra_split(extra) -> tuple[list, list]:
    notes, locs = [], []
    for e in extra or []:
        if isinstance(e, str):
            name, desc = "", e
        else:
            name, desc = _clean(e.get("name")), _clean(e.get("desc"))
        if not desc:
            continue
        nl = name.lower()
        if nl == "location":
            locs.append(desc)
        elif nl in ("part notes", "notes", "remark", "part remark"):
            notes.append(desc)
        elif nl:
            # any other named extra (e.g. "Replaced By") is not a condition
            # clause, but unknown names are kept as notes so they restrict
            if nl not in ("replaced by", "replaces", "superseded by"):
                notes.append(f"{name}: {desc}")
        else:
            m = re.match(r"^location\s*:\s*(.+)$", desc, re.I)
            if m:
                locs.append(m.group(1))
            elif re.match(r"^replaced\s+by\s*:", desc, re.I):
                continue
            elif _POS_ONLY.match(desc):
                locs.append(desc)
            else:
                notes.append(desc)
    return notes, locs


def to_list_rows(site: str, line: int, o: dict) -> list:
    out = []
    seed = _seed(o)
    for r in o.get("rows") or []:
        notes, locs = _extra_split(r.get("extra"))
        out.append(ListRow(
            site=site, seed=seed, cat=o.get("cat") or "", list_url=o.get("list_url") or "",
            pn=_clean(r.get("pn")), section=r.get("section") or "diagram", main=_clean(r.get("main")),
            aux=_clean(r.get("aux")), notes=notes, locations=locs,
            replace=_clean(r.get("replace")) or None, matched=bool(r.get("matched")),
            excluded_by=r.get("excluded_by"), product=r.get("product"),
            retrieved=o.get("retrieved") or "", line=line, status=o.get("status"),
            variant=o.get("variant") or ""))
    return out


def to_year_manifest(site: str, line: int, o: dict) -> YearManifest:
    return YearManifest(site=site, seed=_seed(o), variant=o.get("variant") or "",
                        year_url=o.get("year_url") or "", status=o.get("status"),
                        final_url=o.get("final_url") or "", title=o.get("title") or "",
                        subs=list(o.get("subs") or []), trims=list(o.get("trims") or []),
                        engines=list(o.get("engines") or []), variants=list(o.get("variants") or []),
                        retrieved=o.get("retrieved") or "", line=line)


# ------------------------------------------------------- evidence re-check
def _label_values(ev: list, label: str) -> list:
    """Values printed after a label: PartsGiant "Label: a, b" lines, or
    SimplePart "Label" followed by value lines until the next label."""
    out = []
    labels = {"Replaced By", "Replaces", "Position", "Vehicle Fitment", "Notes", "Part Number",
              "Part Description", "View More"}
    for i, line in enumerate(ev):
        if line.startswith(label + ":"):
            out.append(line[len(label) + 1:].strip())
        elif line == label:
            j = i + 1
            while j < len(ev) and ev[j] not in labels:
                out.append(ev[j])
                j += 1
    return out


def evidence_problems(r: Record) -> list:
    """§5.3 evidence re-check, independent of the site parsers: pn, every
    fitment row's cells in order, position, replaces / replaced_by. Returns
    the list of mismatches (empty = verified).

    Whitespace runs are collapsed on both sides: the SimplePart template
    collapses them on purpose and pages print doubled spaces ("2023,
    2012-2014"; AUDIT.md, VW and Jeep 68242286AB). Nothing else is
    normalized."""
    ev = [_clean(x) for x in r.evidence_lines]
    probs = []
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", (s or "").upper())  # noqa: E731
    # pn: PartsGiant prints "Part Number:"; SimplePart's evidence starts at the
    # fitment block, so its pn is checked against the product URL (AUDIT.md
    # convention) unless the parser flagged pn_differs_from_url.
    if r.template == "partsgiant":
        if not any(norm(v) == norm(r.pn) for v in _label_values(ev, "Part Number")):
            probs.append("pn_not_in_evidence")
    else:
        tail = r.product_url.rsplit("~", 1)[-1] if "~" in r.product_url else ""
        if norm(tail) != norm(r.pn):
            probs.append("pn_not_in_product_url")
    # fitment rows: each distinct raw in order
    raws = []
    for f in r.rows:
        if not raws or raws[-1] != _clean(f.raw):
            raws.append(_clean(f.raw))
    if r.template == "partsgiant":
        try:
            start = next(i for i, x in enumerate(ev) if x.startswith("Year Make Model"))
        except StopIteration:
            start = None
        if raws and start is None:
            probs.append("no_fitment_header")
        elif raws:
            pos = start + 1
            for raw in raws:
                try:
                    pos = ev.index(raw, pos) + 1
                except ValueError:
                    probs.append("fitment_row_not_in_evidence")
                    break
    else:
        try:
            start = ev.index("Vehicle Fitment")
        except ValueError:
            start = None
        if raws and start is None:
            probs.append("no_fitment_header")
        elif raws:
            vm = ev.index("View More") if "View More" in ev else None
            pos = start + 1
            for ri, raw in enumerate(raws):
                # empty cells ("2010-2012 Dodge Caliber |  | SE, SXT") print no line
                cells = [c.strip() for c in raw.split("|") if c.strip()]
                if vm is not None and r.rendered is not None and ri >= r.rendered and pos < vm:
                    pos = vm + 1
                ok = True
                for c in cells:
                    try:
                        pos = ev.index(c, pos) + 1
                    except ValueError:
                        ok = False
                        break
                if not ok:
                    probs.append("fitment_row_not_in_evidence")
                    break
    # fitment fields equal to the printed row, cell by cell (not substrings:
    # "LE" is inside "XLE", "Toyota Camry" inside "Toyota Camry Solara")
    for f in r.rows:
        why = _row_fields_problem(r.template, f)
        if why:
            probs.append(why)
            break
    # the printed header must be the one the parsed layout implies (a 4th
    # option column the record does not carry changes the layout)
    if r.template == "simplepart" and r.rows:
        why = _simplepart_header_problem(ev, r.rows)
        if why:
            probs.append(why)
    # position: the parsed value is printed, and a printed Position is parsed
    pos_vals = _label_values(ev, "Position")
    if r.position:
        list_lines = [x.split(": ", 1)[1] for x in ev if x.startswith("Parts list ") and ": " in x]
        if r.template == "partsgiant":
            if r.position not in pos_vals and r.position not in list_lines:
                probs.append("position_not_in_evidence")
        elif r.position not in pos_vals:
            probs.append("position_not_in_evidence")
    elif pos_vals and not any(str(x).startswith("position conflict") for x in r.flags):
        # (a PartsGiant list/product side conflict leaves position empty on
        # purpose and is flagged, which already makes the record unverified)
        probs.append("printed_position_not_in_record")
    # replaces / replaced_by, both ways: every parsed number is printed after
    # its label, and every number printed after the label is in the record
    # (a dropped "Replaced By" would hide a successor from closure C5)
    for label, vals in (("Replaces", r.replaces), ("Replaced By", r.replaced_by)):
        printed = " ".join(_label_values(ev, label))
        pn_printed = {norm(x) for x in re.split(r"[,\s]+", printed) if norm(x)}
        for v in vals:
            if norm(v) not in pn_printed:
                probs.append(f"{label.lower().replace(' ', '_')}_not_in_evidence")
                break
        if label == "Replaced By" and r.chain_unknown:
            continue      # "(MultiSupersession)": chain_unknown already blocks (§5.2)
        parsed = {norm(v) for v in vals}
        if label == "Replaced By":
            parsed |= {norm(v) for v in r.list_replaced_by}
        if pn_printed - parsed:
            probs.append(f"printed_{label.lower().replace(' ', '_')}_not_in_record")
    return probs


def _cell(s) -> str:
    """A printed cell for comparison: whitespace runs collapsed and the
    space around list commas normalized ("Technology , Sport" and
    "Technology, Sport" are one cell). Nothing else is normalized."""
    return re.sub(r"\s*,\s*", ", ", _clean(s)).strip(" ,")


def _joined(items) -> str:
    return _cell(", ".join(_clean(x) for x in items or []))


def _ymm_problem(f: FitRow, ymm: str) -> str | None:
    """The year/make/model cell must be exactly '<spans> <make> <model>'
    with (lo, hi) one of the printed spans."""
    suffix = f" {f.make} {f.model}"
    if not f.make or not f.model or not ymm.endswith(suffix):
        return "fitment_model_not_printed"
    spans = []
    for part in ymm[: -len(suffix)].split(","):
        m = re.fullmatch(r"\s*(\d{4})(?:\s*-\s*(\d{4}))?\s*", part)
        if not m:
            return "fitment_years_not_printed"
        spans.append((int(m.group(1)), int(m.group(2) or m.group(1))))
    if (f.lo, f.hi) not in spans or f.lo > f.hi:
        return "fitment_years_not_printed"
    return None


def _row_fields_problem(template: str, f: FitRow) -> str | None:
    cells = [_clean(c) for c in (f.raw or "").split("|")]
    why = _ymm_problem(f, cells[0] if cells else "")
    if why:
        return why
    if template == "simplepart":
        # trim layout: Year Make Model | Trim | Engine
        # option layout: Year Make Model | Engine | <each other column>
        if f.layout == "trim":
            if len(cells) != 3:
                return "fitment_cell_count"
            if _cell(cells[1]) != _joined(f.trims) or _cell(cells[2]) != _joined(f.engines):
                return "fitment_cell_not_printed"
            return None
        if len(cells) != 2 + len(f.other_columns):
            return "fitment_cell_count"
        if _cell(cells[1]) != _joined(f.engines) or f.trims:
            return "fitment_cell_not_printed"
        if [_cell(c) for c in cells[2:]] != [_cell(v) for v in f.other_columns.values()]:
            return "fitment_cell_not_printed"
        return None
    # PartsGiant prints the columns its catalog has (trims, engines, the
    # options column), some empty, some joined by a bare "|": the printed
    # non-empty cells must be, in order, exactly the parsed non-empty fields.
    # Where the options column is the trims (option_column_is_trims), the
    # parsed trims must equal that column.
    if f.trims_from_options:
        if _joined(f.trims) != _joined(f.options):
            return "fitment_cell_not_printed"
        want = [_joined(f.engines), _joined(f.options)]
    else:
        want = [_joined(f.trims), _joined(f.engines), _joined(f.options)]
    want = [c for c in want if c]
    got = [_cell(c) for c in cells[1:] if _cell(c)]
    if got != want:
        return "fitment_cell_not_printed"
    return None


def _simplepart_header_problem(ev: list, rows: list) -> str | None:
    """SimplePart prints 'Vehicle Fitment', 'Year Make Model', then the
    column headers: 'Trim', 'Engine' (trim layout) or 'Engine' and each
    option column's header (option layout). One table, one header: rows of
    both layouts in one record cannot both be what the page printed."""
    heads = set()
    for f in rows:
        heads.add(("Trim", "Engine") if f.layout == "trim" else ("Engine",) + tuple(_clean(k) for k in f.other_columns))
    if len(heads) != 1:
        return "fitment_layouts_mixed"
    try:
        s = ev.index("Vehicle Fitment")
    except ValueError:
        return "no_fitment_header"
    # the header, then directly the first row's Year Make Model cell (an
    # extra header column the record does not carry sits in between)
    first = _clean((rows[0].raw or "").split("|")[0])
    want = ["Year Make Model", *next(iter(heads)), first]
    if ev[s + 1: s + 1 + len(want)] != want:
        return "fitment_header_not_layout"
    return None


# --------------------------------------------------------- rule drift matcher
def _stub_fetch() -> types.ModuleType:
    m = types.ModuleType("fetch")

    def get(url, *a, **k):  # pragma: no cover - must never be reached offline
        raise RuntimeError(f"offline curation: refusing network fetch of {url}")
    m.get = get
    m.text_lines = lambda html: []
    m.links = lambda html, pattern: []
    m.Refused = type("Refused", (Exception,), {})
    return m


_MATCHERS: dict = {}


def site_module(site: str):
    """The site module, imported with a stub fetch (no network possible)."""
    name = site.replace("www.", "").rsplit(".", 1)[0]
    if name in _MATCHERS:
        return _MATCHERS[name]
    saved = sys.modules.get("fetch")
    sys.modules["fetch"] = _stub_fetch()
    try:
        mod = importlib.import_module(f"sites.{name}")
    except Exception:  # noqa: BLE001 - a missing/broken module means drift is unchecked
        mod = None
    finally:
        if saved is not None:
            sys.modules["fetch"] = saved
    _MATCHERS[name] = mod
    return mod


def rule_matches(r: Record) -> bool | None:
    """Re-run the site's own category rule on the stored names (§5.3 rule
    drift). True / False, or None when the rule cannot be re-run offline."""
    mod = site_module(r.site)
    if mod is None:
        return None
    if r.template == "simplepart":
        t = getattr(mod, "_T", None)
        if t is None or r.cat not in getattr(t, "rules", {}):
            return None
        slug = r.product_url.split("~")[1] if r.product_url.count("~") >= 2 else ""
        try:
            return bool(t.match(r.cat, r.name, r.aux, slug))
        except Exception:  # noqa: BLE001
            return None
    cfg = getattr(mod, "CFG", None)
    if cfg is None or r.cat not in cfg.parts:
        return None
    T = sys.modules.get("sites._partsgiant")
    remark = _clean(r.raw.get("list_remark"))
    main = r.name
    if remark and main.endswith(", " + remark):
        main = main[: -len(", " + remark)]
    row = {"pn": r.pn, "group": _clean(r.raw.get("list_group")), "main": main, "remark": remark,
           "info": [_clean(x) for x in (r.raw.get("list_info") or [])], "url": r.product_url}
    return pg_row_matches(T, cfg, r.cat, row)


def pg_row_matches(T, cfg, cat: str, r: dict) -> bool:
    """Mirror of sites/_partsgiant.parts_on_page's per-row test (include,
    exclude_head, exclude_full, COMMON_EXCLUDE), without fetching.
    curation_tests/test_adapters.py checks it against the template."""
    rule = cfg.parts[cat]
    info = "; ".join(r["info"])
    text = f"{r['group']} | {r['main']} | {r['remark']} | {info}"
    if callable(rule):
        if not rule(r, text):
            return False
    else:
        inc, exc_head, exc_full = (tuple(rule) + (None, None))[:3]
        head = cfg.head_fn(r) if cfg.head_fn else f"{r['group']} | {r['main']} | {r['remark'].split('(')[0]}"
        if not re.search(inc, text, re.I):
            return False
        if exc_head and re.search(exc_head, head, re.I):
            return False
        if exc_full and re.search(exc_full, text, re.I):
            return False
    if T.COMMON_EXCLUDE.search(cfg.head_fn(r) if cfg.head_fn else f"{r['group']} | {r['main']}"):
        return False
    return True


def site_cat_pages(site: str) -> dict:
    """{cat: compiled regex} of the year-page subs the site module reads for
    each category (SimplePart CAT_PAGES, PartsGiant SUBCATS), for closure C2."""
    mod = site_module(site)
    if mod is None:
        return {}
    if getattr(mod, "_T", None) is not None and hasattr(mod._T, "cat_pages"):
        return dict(mod._T.cat_pages)
    cfg = getattr(mod, "CFG", None)
    if cfg is not None:
        return {k: re.compile(v, re.I) for k, v in cfg.subcats.items()}
    return {}
