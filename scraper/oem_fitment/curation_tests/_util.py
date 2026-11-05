"""Shared helpers for the curation tests (offline; run each file with
python3 scraper/oem_fitment/curation_tests/test_<x>.py). Skips print their
reason (CLAUDE.md rule 8)."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OEM = HERE.parent
SCRAPER = OEM.parent
sys.path.insert(0, str(OEM))
sys.path.insert(0, str(SCRAPER))
FIX = HERE / "fixtures"

FAILS: list = []
COUNT = [0]


def check(name: str, cond, detail: str = "") -> None:
    COUNT[0] += 1
    tag = "ok  " if cond else "FAIL"
    print(f"{tag} {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def skip(name: str, why: str) -> None:
    print(f"SKIP {name}: {why}")


def done(label: str) -> None:
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S) of {COUNT[0]}:", *FAILS, sep="\n  - ")
        sys.exit(1)
    print(f"OK {COUNT[0]} checks ({label})")


def real(name: str) -> list:
    return [json.loads(x) for x in (FIX / "real" / name).read_text().splitlines() if x.strip()]


def by_pn(lines: list, pn: str) -> dict:
    return copy.deepcopy(next(r for r in lines if r["pn"] == pn))


TOY = "www.toyotapartsnow.com"
JEEP = "www.jeeppartsdeal.com"
NOW = "2026-11-05T01:23:03Z"


def write_raw(files: dict) -> str:
    """files: {"raw/<site>.jsonl": [obj | raw string], ...} -> temp dir path."""
    d = Path(tempfile.mkdtemp(prefix="oemcur_"))
    for rel, lines in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(lines, str):
            p.write_text(lines)
            continue
        p.write_text("".join((x if isinstance(x, str) else json.dumps(x)) + "\n" for x in lines))
    return str(d)


_JS = None
_MM = None


def js():
    global _JS
    if _JS is None:
        import junkyard_scraper
        _JS = junkyard_scraper
    return _JS


def model_map():
    global _MM
    if _MM is None:
        import model_map as MM
        _MM = MM.ModelMap(MM.load())
    return _MM


def confirmed(*pairs, policy_sha="", raw_commit="fixtures") -> dict:
    """A CATEGORY_STATUS table with audit records for (site, cat) pairs."""
    tbl: dict = {}
    for site, cat in pairs:
        tbl.setdefault(site, {})[cat] = {"status": "confirmed", "errors": 0, "sample_n": 60,
                                         "date": "2026-11-05", "auditor_session": "fixture",
                                         "policy_sha256": policy_sha, "raw_commit": raw_commit}
    return tbl


def run(ns: str, files: dict, **kw):
    import adapters as A
    import curate as C
    o = C.Options(fixtures=kw.pop("fixtures", True), model_map=kw.pop("model_map", None) or model_map(),
                  js=js(), **kw)
    src = A.RawSource(raw_dir=write_raw(files))
    cur = C.Curation(ns, src, o).run()
    doc = cur.build_doc()
    return cur, doc


# ------------------------------------------------------- synthetic records
def toyota_record(pn, cat, seed, list_sub, name, aux, position, fit_rows, notes=None, location=None,
                  replaces=None, replaced_by=None, retrieved=NOW, other_names=None, section="diagram"):
    """A SimplePart (toyotapartsnow) record that passes the evidence re-check
    and the site's own rule. fit_rows: [(lo, hi, make, model, [trims], [engines])]."""
    mk, md, y = seed
    stem = f"{y}-{mk.lower()}-{md.lower().replace(' ', '-')}"
    fit, ev = [], []
    if replaced_by:
        ev += ["Replaced By", *replaced_by]
    if replaces:
        ev += ["Replaces", *replaces]
    if position:
        ev += ["Position", position]
    ev += ["Vehicle Fitment", "Year Make Model", "Trim", "Engine"]
    for lo, hi, fmk, fmd, trims, engines in fit_rows:
        yrs = f"{lo}-{hi}" if lo != hi else f"{lo}"
        raw = f"{yrs} {fmk} {fmd} | {', '.join(trims)} | {', '.join(engines)}"
        fit.append({"years": [lo, hi], "make": fmk, "model": fmd, "trims": list(trims), "engines": list(engines),
                    "raw": raw})
        ev += [f"{yrs} {fmk} {fmd}", ", ".join(trims), ", ".join(engines)]
    return {"site": TOY, "category": cat, "seed": {"make": mk, "model": md, "year": y}, "segment": [y, y],
            "list_url": f"https://{TOY}/parts-list/{stem}/{list_sub}", "pn": pn, "name": name, "aux_desc": aux,
            "product_url": f"https://{TOY}/oem/toyota~part~{pn}", "list_section": section,
            "list_notes": list(notes or []), "list_location": list(location or []), "list_replaced_by": None,
            "reman": False, "description": aux or name, "other_names": other_names or aux, "position": position,
            "replaces": list(replaces or []), "replaced_by": list(replaced_by or []), "fitment": fit,
            "evidence_lines": ev, "fitment_rows_rendered": len(fit), "fitment_rows_total": len(fit),
            "retrieved": retrieved, "synthetic": True}


def year_manifest(site, seed, title, subs, trims=(), engines=(), retrieved=NOW, status=200, variants=()):
    mk, md, y = seed
    url = f"https://{site}/catalog/{y}-{mk.lower()}-{md.lower().replace(' ', '-')}-parts"
    return {"kind": "year", "site": site, "seed": {"make": mk, "model": md, "year": y}, "variant": "",
            "year_url": url, "status": status, "final_url": url, "title": title, "subs": list(subs),
            "trims": list(trims), "engines": list(engines), "variants": list(variants), "retrieved": retrieved,
            "synthetic": True}


def list_manifest(site, seed, cat, sub, rows, retrieved=NOW, status=200):
    """rows: [(pn, main, aux, [notes], [locations], matched, excluded_by)]"""
    mk, md, y = seed
    stem = f"{y}-{mk.lower()}-{md.lower().replace(' ', '-')}"
    out = []
    for pn, main, aux, notes, locs, matched, excl in rows:
        extra = [{"name": "Part Notes", "desc": n} for n in notes] + [{"name": "Location", "desc": x} for x in locs]
        out.append({"pn": pn, "section": "diagram", "main": main, "aux": aux, "extra": extra, "replace": None,
                    "url": f"/oem/toyota~part~{pn}", "matched": matched, "excluded_by": excl,
                    "product": "ok" if matched else None})
    return {"kind": "list", "site": site, "seed": {"make": mk, "model": md, "year": y}, "variant": "", "cat": cat,
            "list_url": f"https://{site}/parts-list/{stem}/{sub}", "status": status, "retrieved": retrieved,
            "rows": out, "synthetic": True}
