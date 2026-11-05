#!/usr/bin/env python3
"""Offline audit of crawl output (raw/<site>.jsonl): no network, no cache.

Each record is checked against its OWN evidence_lines, re-parsed here
independently of sites/_partsgiant.py and sites/_simplepart.py (only the
sites' declared conventions are read from their CFG: option_column_is_trims,
engine_rx, bare_list_position).

  E  evidence mismatch  pn, description, position, replaces, replaced_by and
                        every fitment entry (years = a printed span, year_spans,
                        make, model, trims, engines, options), cell for cell
  C  category suspect   name / short name / list-row text lacks the category's
                        word or carries a junk word (bulb, boot, socket, bracket,
                        lens, clutch ...); heuristic: read every hit by hand
  D  duplicate          same category + pn twice in one file
  F  fitment suspect    empty fitment without a flag, years outside 1940-2027,
                        seed vehicle-year absent from its own part's fitment
E and C count toward the mismatch rate; D and F are for curators.
Record shapes: PartsGiant (sites/_partsgiant.py), SimplePart (sites/_simplepart.py)
and aftermarket/ DB Electrical (applications, replaces table, specs, item #).

Usage (from scraper/oem_fitment):
    git fetch origin oem-raw && git show origin/oem-raw:raw/<site>.jsonl > /tmp/x/<site>.jsonl
    python3 audit.py /tmp/x/*.jsonl            # JSON summary per site
    python3 audit.py --table /tmp/x/*.jsonl    # one markdown row per site + hits
A records file past crawl.PART_BYTES continues in <site>.2.jsonl, <site>.3.jsonl
...: copy every raw/<site>*.jsonl; any part given stands for the whole logical
file (rawparts.py), and .lists / .years manifest files are skipped.
Findings go to AUDIT.md. Test: tests/test_audit.py (corruption cases).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

YEARS_RE = re.compile(r"^(\d{4}(?:\s*-\s*\d{4})?(?:\s*,\s*\d{4}(?:\s*-\s*\d{4})?)*)\s+(\S+)\s+(.+)$")
SPAN_RE = re.compile(r"(\d{4})(?:\s*-\s*(\d{4}))?")
ENGINE_RE = re.compile(r"^(\d+ Cyl\b|\d\.\dL\b|Electric\b|Rotary\b)", re.I)

# words that mean "not the assembly a puller removes" for that category
JUNK_ANY = r"\bbulb\b|bulb kit|\bsocket\b|\bbracket\b|\bbolt\b|\bscrew\b|\bnut\b|\bwasher\b|gasket|\bseal\b|\bclip\b|\blabel\b|\bharness\b|\bwiring\b|\bpulley\b|\bshim\b|\bgrommet\b|\bretainer\b|\bstud\b"
JUNK = {
    "alternator": r"regulator|brush|bearing|decoupler|cover|shield",
    "starter": r"solenoid|relay|shield|cover|drive\b",
    "ac-compressor": r"clutch|coil|valve|switch|sensor|hose|\bline\b|oil|lubricant|refrigerant|relay|snap ring",
    "headlights": r"bezel|lens|cover|\bcap\b|ballast|igniter|level|adjust|motor|module|fog|washer|protector|boot",
    "tail-lights": r"bezel|lens(?! ?& ?(body|housing))|cover|\bcap\b|reflector|license|high mount|center high|fog",
    "side-mirrors": r"glass|cover|\bcap\b|motor|actuator|switch|lens|lamp|inside|interior",
    "window-regulator": r"handle|switch|channel|\brun\b|glass|crank|knob|gear cover",
    "window-switch": r"bezel|knob|lamp|mirror|seat|door lock(?! and)|ascd|hazard|sunroof|trunk|ignition|combination",
    "climate-control": r"cable|knob|bezel|button|sensor|lamp|valve|motor|actuator|vacuum|blower|resistor",
    "fuel-pump-module": r"relay|control module|driver|o.?ring|lock ring|strainer|filter|tube|hose|sender only|resistor",
    "throttle-body": r"(?<!w/throttle position )sensor|spacer|cable|heater|hose|cover|elbow|adapter",
    "power-steering-pump": r"reservoir|hose|\bcap\b|\bline\b|valve|cooler|connector",
}
EXPECT = {  # at least one of these must appear in name/description
    "alternator": r"alternat|generator",
    "starter": r"starter",
    "ac-compressor": r"compressor",
    "headlights": r"head\s*lamp|headlight|head light|lamp assy",
    "tail-lights": r"tail|combination lamp|rear lamp|stop|lens ?& ?(body|housing)|^lamp ass(y|embly)\b",
    "side-mirrors": r"mirror",
    "window-regulator": r"regulator|window motor|motor.*window",
    "window-switch": r"switch",
    "climate-control": r"control|controller|a/?c.*heater|climate",
    "fuel-pump-module": r"fuel pump|pump.*fuel|fuel.*module|module.*fuel|fuel sender|sender and pump",
    "throttle-body": r"throttle",
    "power-steering-pump": r"power steering|steering pump|pump.*steering|pump assy, vane|pump assembly, vane",
}


_CONV: dict = {}


def site_conventions(site: str) -> dict:
    """Declared per-site conventions (not parsing code) from the site module's
    CFG: option_column_is_trims, engine_rx, bare_list_position, trim_col, option_col."""
    if site not in _CONV:
        conv = {"option_trims": False, "engine_rx": None, "bare": True, "trim_col": None, "option_col": r"option|detail"}
        try:
            import importlib
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            mod = importlib.import_module("sites." + re.sub(r"[^a-z0-9]", "_", site.replace("www.", "").split(".")[0]))
            cfg = getattr(mod, "CFG", None)
            if cfg is not None:
                conv = {"option_trims": bool(getattr(cfg, "option_column_is_trims", False)),
                        "engine_rx": getattr(cfg, "engine_rx", None),
                        "bare": getattr(cfg, "bare_list_position", True),
                        "trim_col": getattr(cfg, "trim_col", None),
                        "option_col": getattr(cfg, "option_col", None) or r"option|detail"}
        except Exception as e:  # unknown module: defaults, reported once
            print(f"note: no conventions for {site}: {e}", file=sys.stderr)
        _CONV[site] = conv
    return _CONV[site]


def parse_row(cells: list[str], titles: list[str], option_trims: bool = False, engine_rx: str | None = None,
              trim_col: str | None = None, option_col: str = r"option|detail") -> list[dict]:
    """Independent parse of one evidence fitment row -> expected fitment dicts."""
    def col(rx):
        for k, t in enumerate(titles):
            if re.search(rx, t, re.I):
                return k
        return None
    c_ymm = col(r"year") or 0
    c_te = col(r"trim\s*&\s*engine")
    c_eng = None if c_te is not None else col(r"engine")
    c_trim = None if c_te is not None else col(trim_col or r"^trim")
    c_opt = col(option_col)
    get = lambda c: cells[c].strip() if c is not None and c < len(cells) else ""
    sp = lambda s: [x.strip() for x in s.split(", ") if x.strip()] if s else []
    m = YEARS_RE.match(get(c_ymm))
    if not m:
        return [{"unparsed": get(c_ymm)}]
    trims, engines = [], []
    if c_te is not None:
        te = get(c_te)
        if "|" in te:
            t, _, e = te.partition("|")
            trims, engines = sp(t), sp(e)
        elif te and all(ENGINE_RE.match(x) or (engine_rx and re.match(engine_rx, x, re.I)) for x in sp(te)):
            engines = sp(te)
        else:
            trims = sp(te)
    else:
        trims, engines = sp(get(c_trim)), sp(get(c_eng))
        if not trims and option_trims:
            trims = sp(get(c_opt))
    return [{"years": [int(a), int(b or a)], "make": m.group(2), "model": m.group(3).strip(),
             "trims": trims, "engines": engines, "options": sp(get(c_opt)),
             "_multi_pipe": get(c_te).count("|") > 1 if c_te is not None else False}
            for a, b in SPAN_RE.findall(m.group(1))]


def split_paren(s: str) -> list[str]:
    """comma split that keeps commas inside parentheses (SimplePart lists)."""
    out, depth, cur = [], 0, ""
    for ch in s or "":
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]


SP_YMM = re.compile(r"^(\d{4}(?:\s*-\s*\d{4})?(?:\s*,\s*\d{4}(?:\s*-\s*\d{4})?)*)\s+(\D.*)$")
TWO_WORD = ("Land Rover", "Alfa Romeo", "Aston Martin", "Mercedes Benz", "Rolls Royce")


def audit_simplepart(r: dict, out) -> None:
    ev = r.get("evidence_lines") or []
    pairs = {}
    top = ev.index("Vehicle Fitment") if "Vehicle Fitment" in ev else len(ev)
    for i in range(0, top - 1):
        if ev[i] in ("Position", "Replaces", "Replaced By"):
            pairs.setdefault(ev[i], ev[i + 1])
    url_pn = (r.get("product_url") or "").rsplit("~", 1)[-1]
    if url_pn.replace("-", "").lower() != (r.get("pn") or "").replace("-", "").lower() and \
            not any("pn_differs_from_url" in f for f in r.get("flags") or []):
        out["E"].append(f"pn {r.get('pn')!r} differs from url {url_pn!r} without flag")
    if (pairs.get("Position") or None) != (r.get("position") or None):
        out["E"].append(f"position {r.get('position')!r} vs evidence {pairs.get('Position')!r}")
    if split_paren(pairs.get("Replaces", "")) != (r.get("replaces") or []):
        out["E"].append(f"replaces {r.get('replaces')} vs evidence {pairs.get('Replaces')!r}")
    if split_paren(pairs.get("Replaced By", "")) != (r.get("replaced_by") or []):
        out["E"].append(f"replaced_by {r.get('replaced_by')} vs evidence {pairs.get('Replaced By')!r}")
    flags = r.get("flags") or []
    differs = any(f in ("fitment_text_differs_from_store",) or f.startswith("evidence_truncated") for f in flags)
    fit = r.get("fitment") or []
    # unique raws in order
    raws = []
    for f in fit:
        if not raws or raws[-1] != f["raw"]:
            raws.append(f["raw"])
    if top < len(ev):
        n_hdr = 0
        hdr = []
        for x in ev[top + 1:]:
            if SP_YMM.match(x):
                break
            hdr.append(x)
        ws = lambda x: re.sub(r"\s+", " ", x).strip()  # rendered HTML may double spaces
        body = [ws(x) for x in ev[top + 1 + len(hdr):] if x != "View More"]
        want = [ws(c) for raw in raws for c in raw.split(" | ") if c.strip()]
        if body != want and not differs:
            k = next((i for i, (a, b) in enumerate(zip(body, want)) if a != b), min(len(body), len(want)))
            out["E"].append(f"fitment cells differ from evidence at cell {k}: evidence {body[k:k+2]} vs record {want[k:k+2]}")
        rendered = ev[top + 1 + len(hdr):]
        if "View More" in rendered and r.get("fitment_rows_rendered") is not None:
            pass
        for f in fit:
            cells = f["raw"].split(" | ")
            col = dict(zip(hdr, cells))
            m = SP_YMM.match(col.get("Year Make Model", cells[0]))
            if not m:
                out["E"].append(f"unparsed raw {f['raw']!r}")
                continue
            spans = [[int(y) for y in re.findall(r"\d{4}", part)] for part in m.group(1).split(",")]
            spans = [[y[0], y[-1]] for y in spans]
            rest = m.group(2).strip()
            make = next((mk for mk in TWO_WORD if rest.startswith(mk + " ")), None) or rest.split(" ", 1)[0]
            model = rest[len(make):].strip()
            if list(f["years"]) not in spans:
                out["E"].append(f"years {f['years']} not printed in {f['raw']!r}")
            if len(spans) > 1 and f.get("year_spans") != spans:
                out["E"].append(f"year_spans {f.get('year_spans')} vs printed {spans}")
            if (f["make"], f["model"]) != (make, model):
                out["E"].append(f"make/model {f['make']!r} {f['model']!r} vs {rest!r}")
            if f.get("trims", []) != split_paren(col.get("Trim", "")):
                out["E"].append(f"trims {f.get('trims')} vs {col.get('Trim')!r}")
            if f.get("engines", []) != split_paren(col.get("Engine", "")):
                out["E"].append(f"engines {f.get('engines')} vs {col.get('Engine')!r}")
        # every fitment raw must be expanded once per span
        for raw in raws:
            m = SP_YMM.match(raw.split(" | ")[0])
            if m and sum(1 for f in fit if f["raw"] == raw) != len(m.group(1).split(",")):
                out["E"].append(f"span count wrong for {raw!r}")


def audit_dbelectrical(r: dict, out) -> None:
    """aftermarket/ records (DB Electrical): applications, replaces, specs and
    item number against the record's own evidence_lines."""
    ev = r.get("evidence_lines") or []
    flags = r.get("flags") or []
    item = next((x[len("Item #: "):] for x in ev if x.startswith("Item #: ")), None)
    if item != r.get("aftermarket_pn") and not any(f.startswith("item_number_differs") for f in flags):
        out["E"].append(f"aftermarket_pn {r.get('aftermarket_pn')!r} vs evidence Item # {item!r}")
    for k, v in (r.get("specs") or {}).items():
        if "\n" in v:  # multi-line spec cells print joined by " / "
            v = " / ".join(x.strip() for x in v.split("\n") if x.strip())
        if f"{k} | {v}" not in ev:
            out["E"].append(f"spec {k}={v[:40]!r} not in evidence")
    hdr = next((i for i, x in enumerate(ev) if x.startswith("MAKE | TYPE | MODEL")), None)
    rep = ev.index("Replaces These Part Numbers") if "Replaces These Part Numbers" in ev else len(ev)
    rows = ev[hdr + 1:rep] if hdr is not None else []
    cols = [c.strip() for c in ev[hdr].split(" | ")] if hdr is not None else []
    unparsed = {f.split(":", 1)[1] for f in flags if f.startswith("unparsed_application_row:")}
    apps = r.get("applications") or []
    raws = [a["raw"] for a in apps]
    if [x for x in rows if x not in unparsed] != raws:
        out["E"].append(f"applications ({len(raws)}) differ from evidence rows ({len(rows)}, {len(unparsed)} flagged unparsed)")
    for a in apps:
        cell = dict(zip(cols, [c.strip() for c in a["raw"].split(" | ")]))
        y = cell.get("YEAR", "")
        ym = re.fullmatch(r"(\d{4})(?:\s*-\s*(\d{4}))?", y)
        if not (ym and a["years"] == [int(ym.group(1)), int(ym.group(2) or ym.group(1))]):
            out["E"].append(f"years {a['years']} vs printed YEAR {y!r}")
        for k, f in (("MAKE", "make"), ("TYPE", "type"), ("MODEL", "model"), ("ENGINE", "engine")):
            if (cell.get(k) or "") != (a.get(f) or ""):
                out["E"].append(f"{f} {a.get(f)!r} vs printed {cell.get(k)!r}")
    # spans: every application row inside exactly one span with the same cells
    for a in apps:
        hit = [sp for sp in r.get("application_spans") or [] if all(sp.get(k) == a.get(k) for k in ("make", "type", "model", "engine"))
               and sp["years"][0] <= a["years"][0] <= sp["years"][1]]
        if len(hit) != 1:
            out["E"].append(f"application {a['raw']!r} in {len(hit)} spans")
    # replaces table verbatim, and every classified number comes from it
    printed = []  # rows in page order; a brand can print on several rows
    for x in ev[rep + 1:]:
        if " | " in x:
            b, _, nums = x.partition(" | ")
            printed.append((b.strip(), [n.strip() for n in nums.split(",") if n.strip()]))
    got = [(e["brand"], e["numbers"]) for e in r.get("replaces") or []]
    if got != printed and not any(f.startswith("unparsed_replaces_row") for f in flags):
        k = next((i for i, (x, y) in enumerate(zip(got, printed)) if x != y), min(len(got), len(printed)))
        out["E"].append(f"replaces row {k} differs: record {got[k:k+1]} vs evidence {printed[k:k+1]}")
    allnums = {(b.upper(), n) for b, ns in got for n in ns}
    for fld in ("oe_numbers", "oe_service_numbers", "oe_supplier_numbers", "interchange_numbers", "other_numbers", "ambiguous_numbers"):
        for e in r.get(fld) or []:
            if (e["brand"].upper(), e["pn"]) not in allnums:
                out["E"].append(f"{fld} {e['brand']} {e['pn']} not in the replaces table")
    # category / fitment suspects
    ut = (r.get("specs") or {}).get("Unit Type", "")
    if r.get("category") and ut and r["category"].lower() not in ut.lower() and not any(f.startswith("unit_type_not_") for f in flags):
        out["C"].append(f"Unit Type {ut!r} for category {r['category']} without flag")
    if not apps and not any(f.startswith("no_application_rows") or f.startswith("unparsed_application_row") for f in flags):
        out["F"].append("no applications without flag")
    for a in apps:
        if not (1940 <= a["years"][0] <= 2027):
            out["F"].append(f"odd year {a['raw']!r}")


def _common_checks(r, out):
    got = r.get("fitment") or []
    # fitment suspects
    if not got and not any(("no fitment" in f or "no_fitment" in f) for f in r.get("flags") or []):
        out["F"].append("empty fitment without a flag")
    for f in got:
        lo, hi = f["years"]
        if lo > hi or lo < 1940 or hi > 2027:
            out["F"].append(f"odd years {f['years']} in {f['raw']!r}")
    seed = r.get("seed") or {}
    norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
    if seed and got and not any(f["years"][0] <= seed.get("year", 0) <= f["years"][1] for f in got):
        out["F"].append(f"seed year {seed.get('year')} {seed.get('make')} {seed.get('model')} not in any fitment span")
    elif seed and got and not any(f["years"][0] <= seed["year"] <= f["years"][1] and
                                  (norm(f["model"]) in norm(seed["model"]) or norm(seed["model"]) in norm(f["model"]))
                                  for f in got):
        out["F"].append(f"seed {seed['year']} {seed['model']} absent: fitment lists {sorted({f['make']+' '+f['model'] for f in got})[:6]}")
    # category
    cat = r.get("category")
    # junk words are read in the OEM name, the short name and the list-row text;
    # not in the product display name ("Black Bezel") or other_names (retail synonyms)
    text = " | ".join([r.get("name") or "", r.get("aux_desc") or "",
                       " ; ".join(r.get("list_info") or []), r.get("list_remark") or ""])
    if r.get("site") == "www.fordpartsgiant.com":
        # Ford: category comes from the engineering base number; list info is fit
        # notes describing assembly contents ("Body and lens", "Includes Clutch")
        text = " | ".join([r.get("name") or "", r.get("aux_desc") or ""])
    text = re.sub(r"(?i)window and door lock|with pulley|l/pulley|pump, unit, o-ring|w/throttle position sensor|with regulator|with filter|lens ?& ?(body|housing)|tube assembly, fuel suction", "", text)
    name_text = " | ".join([r.get("name") or "", r.get("description") or ""])
    if cat in EXPECT and not re.search(EXPECT[cat], name_text, re.I):
        out["C"].append(f"{cat}: name {r.get('name')!r} / {r.get('description')!r} lacks expected word")
    j = JUNK_ANY + ("|" + JUNK[cat] if cat in JUNK else "")
    mj = re.search(j, text, re.I)
    if mj and not (cat == "alternator" and re.search(r"generator kit", text, re.I) and mj.group(0).lower() == "kit"):
        out["C"].append(f"{cat}: junk word {mj.group(0)!r} in {text[:160]!r}")


def audit_record(r: dict) -> dict[str, list[str]]:
    out = defaultdict(list)
    ev = r.get("evidence_lines") or []
    if "aftermarket_pn" in r:
        audit_dbelectrical(r, out)
        return out
    simplepart = "Vehicle Fitment" in ev or not any(x.startswith("Part Number: ") for x in ev)
    if simplepart:
        audit_simplepart(r, out)
        _common_checks(r, out)
        return out
    kv = {}
    for ln in ev:
        for key in ("Part Number", "Part Description", "Position", "Replaced By", "Replaces"):
            if ln.startswith(key + ": "):
                kv.setdefault(key, ln[len(key) + 2:])
    listed = [ln for ln in ev if ln.startswith("Parts list ")]
    # identity
    if kv.get("Part Number") != r.get("pn"):
        out["E"].append(f"pn {r.get('pn')!r} vs evidence {kv.get('Part Number')!r}")
    if kv.get("Part Description", "") != (r.get("description") or ""):
        out["E"].append(f"description {r.get('description')!r} vs evidence {kv.get('Part Description')!r}")
    # supersession
    rep = [x.strip() for x in re.split(r"[,;]", kv.get("Replaces", "")) if x.strip()]
    if rep != (r.get("replaces") or []):
        out["E"].append(f"replaces {r.get('replaces')} vs evidence {rep}")
    if (kv.get("Replaced By") or None) != (r.get("replaced_by") or None):
        out["E"].append(f"replaced_by {r.get('replaced_by')!r} vs evidence {kv.get('Replaced By')!r}")
    # position must be printed in evidence (list row or product Position line)
    pos = r.get("position")
    if pos:
        printed = [kv.get("Position")] + [ln.split(": ", 1)[1] if ": " in ln else "" for ln in listed]
        if pos not in printed:
            out["E"].append(f"position {pos!r} not in evidence {printed}")
    elif listed or kv.get("Position"):
        if not any("position conflict" in f for f in r.get("flags") or []):
            out["E"].append(f"position empty but evidence prints one ({kv.get('Position')!r}, {listed})")
    # fitment table
    hdr_i = next((i for i, ln in enumerate(ev) if ln.startswith("Year Make Model") or ln.startswith("Year/Make/Model")), None)
    expected = []
    if hdr_i is not None:
        titles = [t.strip() for t in ev[hdr_i].split(" | ")]
        conv = site_conventions(r.get("site", ""))
        rows = ev[hdr_i + 1:]
        for ln in rows:
            for f in parse_row(ln.split(" | "), titles, **{k: v for k, v in [("option_trims", conv["option_trims"]), ("engine_rx", conv["engine_rx"]), ("trim_col", conv["trim_col"]), ("option_col", conv["option_col"])]}):
                if "unparsed" in f:
                    out["E"].append(f"unparsed evidence row {ln!r}")
                    continue
                if f.pop("_multi_pipe"):
                    out["E"].append(f"Trim & Engine cell with several '|' groups: {ln!r}")
                f["raw"] = ln
                expected.append(f)
    got = [{k: f.get(k) for k in ("years", "make", "model", "trims", "engines", "options", "raw")} for f in r.get("fitment") or []]
    truncated = any("truncated" in f for f in r.get("flags") or [])
    key = lambda f: json.dumps(f, sort_keys=True)
    eg, gg = Counter(map(key, expected)), Counter(map(key, got))
    miss, extra = list((eg - gg).elements()), list((gg - eg).elements())
    # truncated evidence: every evidence row must be in fitment; extra rows are expected
    if miss or (extra and not truncated):
        out["E"].append(f"fitment differs from evidence: {len(miss)} missing, {len(extra)} extra; e.g. {(miss or extra)[:1]}")
    _common_checks(r, out)
    return out


def record_files(paths: list[str]) -> list[list[Path]]:
    """Group the given paths into logical records files (rawparts.py): any part
    of raw/<site>.jsonl stands for the whole file, read in part order; the
    .lists / .years manifest files are skipped (they hold no records)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import rawparts  # noqa: E402
    out: list[list[Path]] = []
    for p in paths:
        if rawparts.kind_of(Path(p)) != "records":
            print(f"note: skipping manifest file {p}", file=sys.stderr)
            continue
        parts = rawparts.logical_paths(Path(p))
        if parts and parts not in out:
            out.append(parts)
    return out


def main(paths: list[str], table: bool = False) -> None:
    import rawparts  # noqa: E402  (record_files put this directory on sys.path)
    summary = {}
    for parts in record_files(paths):
        recs = [r for _, r in rawparts.rows(parts) if r is not None]
        site = recs[0]["site"] if recs else str(parts[0])
        for r in recs:  # aftermarket records key on aftermarket_pn
            r.setdefault("pn", r.get("aftermarket_pn"))
        seen = Counter((r.get("category"), r.get("pn")) for r in recs)
        res = {"records": len(recs), "E": [], "C": [], "D": [], "F": []}
        bad = 0
        for r in recs:
            o = audit_record(r)
            if (r.get("category"), r.get("pn")) in seen and seen[(r.get("category"), r.get("pn"))] > 1:
                o["D"].append("duplicate category+pn")
            if o.get("E") or o.get("C"):
                bad += 1
            for k, v in o.items():
                for msg in v:
                    res[k].append({"pn": r.get("pn"), "category": r.get("category"), "list_url": r.get("list_url"),
                                   "product_url": r.get("product_url"), "msg": msg})
        res["mismatched_records"] = bad
        res["mismatch_rate"] = round(bad / len(recs), 4) if recs else 0
        summary[site] = res
    if not table:
        json.dump(summary, sys.stdout, indent=1)
        return
    print("| site | records | E | C | D | F | mismatch rate |\n|---|---|---|---|---|---|---|")
    for site, r in summary.items():
        print(f"| {site} | {r['records']} | {len(r['E'])} | {len(r['C'])} | {len(r['D'])} | {len(r['F'])} | {100 * r['mismatch_rate']:.2f}% |")
    for site, r in summary.items():
        for k in "ECDF":
            for x in r[k]:
                print(f"{site} {k} {x['category']} {x['pn']} {x['list_url']} :: {x['msg']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    tbl = "--table" in args
    main([a for a in args if a != "--table"], table=tbl)
