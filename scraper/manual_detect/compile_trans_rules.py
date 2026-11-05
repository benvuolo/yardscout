#!/usr/bin/env python3
"""Compile the verified manual-detection worklists into one runtime table.

Reads (all in scraper/manual_detect/, each already adversarially verified):
  vin_rules_0.json .. vin_rules_7.json   track 1: VIN codes from the makers'
                                         Part 565 filings (NHTSA MID)
  manual_trims.json                      track 3: manual-only trims
  epa_sole.json                          track 2: EPA sole offering
plus the generator modules vin_rules_0.py .. vin_rules_7.py for their
structured code tables (the JSON regexes are a union over codes and years;
the tables say which years each code means what), and the scraper's
docs/data/vin_decodes.json.gz / inventory_live.json for two identity lists
(Honda codes NHTSA decodes; the EPA rules' make/model identities).

Writes scraper/manual_detect/trans_rules.json, which
scraper/trans_evidence.py loads at scan time. Rebuild after any worklist
changes:

    python3 -I scraper/manual_detect/compile_trans_rules.py

What is compiled (and what is not):
  * Only rules whose verified status is counted: vin_rules keep /
    keep_low_sample / low_sample; manual_trims verified; epa_sole years
    whose status_by_year is low_sample / keep. Candidates, holds, drops and
    refuted rules are left out.
  * VIN rules give both claims (manual and automatic codes). The runtime
    publishes only manual claims; automatic claims are used to detect
    disagreement (two sources disagree -> nothing is recorded).
  * CONFLICT_ONLY lists rules that are not counted but whose claim is still
    used to withhold a disagreeing value (never to publish one). Today: the
    1997 Accord rule (vin_rules_0, hub decision pending), where Honda's own
    filing and EPA contradict vPIC's decode.
  * Each manual clause is the generator's own regex for ONE code and that
    code's years, AND the worklist's published regex (which carries hand
    narrowing made during verification, e.g. the Fiat 500 series H rule).
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = REPO / "docs" / "data"
OUT = HERE / "trans_rules.json"
sys.path.insert(0, str(HERE))

COUNTED_VIN = {"keep", "keep_low_sample", "low_sample"}
COUNTED_EPA_YEAR = {"keep", "low_sample"}
# Not counted, but used only to withhold a disagreeing published value.
CONFLICT_ONLY = {"honda_accord_1997_vin7_manual", "honda_accord_1997_vin7_automatic"}
# Worklists whose counts left out cars at Canadian yards (US-market claims).
US_ONLY_FILES = {"vin_rules_2.json", "vin_rules_3.json", "vin_rules_7.json", "manual_trims.json"}
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def first_url(cites) -> list[str]:
    out = []
    for c in cites or []:
        u = c.get("url") if isinstance(c, dict) else None
        if u and u not in out:
            out.append(u)
    return out[:4]


# ---------------------------------------------------------------- vin_rules_0
def compile_honda(doc: dict) -> tuple[list[dict], list[str]]:
    m = importlib.import_module("vin_rules_0")
    status = {r["id"]: r["status"] for r in doc["rules"]}
    jre = {r["id"]: r.get("vin_regex") or "" for r in doc["rules"]}
    cites = {r["id"]: first_url(r.get("citations")) for r in doc["rules"]}
    H, A = sorted(m.HONDA_WMI), sorted(m.ACURA_WMI)
    out: list[dict] = []

    def add(rid, claim, wmi, body, years, label, need_doc, not_re=""):
        st = status.get(rid)
        if st not in COUNTED_VIN and rid not in CONFLICT_ONLY:
            return
        rx = "^(" + "|".join(wmi) + ")" + body
        out.append({"id": rid, "src": "vin_rules_0.json", "status": st, "claim": claim,
                    "conflict_only": rid in CONFLICT_ONLY, "us_only": False, "hint": "decode",
                    "wmi": wmi, "re": rx, "and_re": jre.get(rid, "") if claim == "manual" else "",
                    "not_re": not_re, "years": years, "need_documented": need_doc,
                    "label": label, "citations": cites.get(rid, [])})

    for brand, wmi, lo in (("honda", H, 1987), ("acura", A, 1986)):
        for code, (claim, meaning) in m.DIGIT_T7.items():
            rid = f"{brand}_vin7_digit_{lo}_2009_{claim}"
            label = f"VIN character 7 = {code}: {meaning} (Honda Part 565 filings)"
            if brand == "honda":
                # MY1997 Accord (chars 4-5 CD/CE) is carved out into the
                # honda_accord_1997 rule; every other line of 1997 stays.
                add(rid, claim, wmi, f"...{code}", [y for y in range(lo, 2010) if y != 1997], label, True)
                add(rid, claim, wmi, f"...{code}", [1997], label, True, not_re="^...(CD|CE)")
            else:
                add(rid, claim, wmi, f"...{code}", list(range(lo, 2010)), label, True)
        for code, (claim, meaning) in m.LETTER_T7.items():
            add(f"{brand}_vin7_letter_2010_on_{claim}", claim, wmi, f"...{code}", list(range(2010, 2040)),
                f"VIN character 7 = {code}: {meaning} (Honda Part 565 filings)", True)
    # 1997 Accord carve-out (conflict-only): Honda wmi, lines CD/CE, digit char 7
    for code, (claim, meaning) in m.DIGIT_T7.items():
        add(f"honda_accord_1997_vin7_{claim}", claim, ["1HG", "JHM"], f"(CD|CE).{code}", [1997],
            f"1997 Accord VIN character 7 = {code}: {meaning}", False)
    # MY1984-1986 Honda: character 6 = transmission, per (year, line) group
    for (y, line), allowed in sorted(m.OLD_T6_ALLOWED.items()):
        for code in allowed:
            claim, meaning = m.OLD_T6[code]
            add(f"honda_vin6_1984_1986_{claim}", claim, H, f"{line}{code}[2345]", [y],
                f"{y} Honda line {line}, VIN character 6 = {code}: {meaning}", False)

    # (model year, chars 4-7) NHTSA's vPIC decodes to a model (the codes Honda filed)
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    documented = set()
    for vin, d in cache.items():
        vin = (vin or "").strip().upper()
        if len(vin) != 17 or not m.brand_of(vin) or not isinstance(d, dict) or not d.get("model"):
            continue
        if not m.check_digit_ok(vin):
            continue
        try:
            y = m.vin_year(vin, int(str(d.get("modelYear") or 0)[:4]) or None)
        except ValueError:
            y = None
        if y:
            documented.add(f"{y}:{vin[3:7]}")
    return out, sorted(documented)


# ------------------------------------------------------------ vin_rules_1..7
def _years_of(fileno: int, ys) -> list[int]:
    if ys is None:
        return []
    if fileno in (1, 2) and isinstance(ys, tuple) and len(ys) == 2:
        return list(range(ys[0], ys[1] + 1))
    return sorted(int(y) for y in ys)


def compile_generic(fileno: int, doc: dict) -> list[dict]:
    m = importlib.import_module(f"vin_rules_{fileno}")
    src = f"vin_rules_{fileno}.json"
    M, A = m.M, m.A
    jrules = {r["id"]: r for r in doc["rules"]}
    out: list[dict] = []
    for r in m.RULES:
        j = jrules.get(r["id"])
        if not j or j["status"] not in COUNTED_VIN:
            continue
        lo, hi = r["years"]
        rule_years = set(range(lo, hi + 1))
        and_re = j.get("vin_regex_manual") or ""
        cites = first_url(j.get("citations"))

        def emit(claim, rx, years, label):
            ys = sorted(set(years) & rule_years)
            if not rx or not ys:
                return
            out.append({"id": r["id"], "src": src, "status": j["status"], "claim": claim,
                        "conflict_only": False, "us_only": src in US_ONLY_FILES, "hint": "listing",
                        "wmi": list(r["wmi"]), "re": rx,
                        "and_re": and_re if claim == "manual" else "", "not_re": "",
                        "years": ys, "need_documented": False, "label": label, "citations": cites})

        if "tables" in r:                      # vin_rules_5: per-year tables keyed by r["key"]
            for y, table in r["tables"].items():
                for code, e in table.items():
                    if e[0] in (M, A):
                        rr = {**r, "tables": {y: {code: (M, e[1])}}}
                        emit(e[0], m.rule_regex(rr), [y], f"{y}: VIN positions {r['key']} = {code}: {e[1]}")
                    elif e[0] == m.BY6:
                        for k, (cl, meaning) in e[1].items():
                            if cl in (M, A):
                                rr = {**r, "tables": {y: {code: (m.BY6, {k: (M, meaning)})}}}
                                emit(cl, m.rule_regex(rr), [y],
                                     f"{y}: VIN positions {r['key']} = {code}, position 6 = {k}: {meaning}")
            continue
        for code, (cl, meaning, ys) in r["codes"].items():
            if cl not in (M, A):
                continue
            years = _years_of(fileno, ys)
            rr = copy.copy(r)
            rr["codes"] = {code: (M, meaning, ys)}
            rr.pop("extra_codes", None)
            emit(cl, m.rule_regex(rr), years, f"VIN code {code}: {meaning}")
        for (y, code), (cl, meaning) in (r.get("extra_codes") or {}).items():
            if cl not in (M, A):
                continue
            rr = {**r, "codes": {}, "extra_codes": {(y, code): (M, meaning)}}
            emit(cl, m.rule_regex(rr), [y], f"{y}: VIN code {code}: {meaning}")
    return out


# --------------------------------------------------------------- manual_trims
def compile_trims(doc: dict) -> list[dict]:
    out = []
    for t in doc["trims"]:
        if t.get("status") != "verified" or not t.get("counted") or t.get("claim") != "manual":
            continue
        out.append({"id": t["id"], "src": "manual_trims.json", "status": t["status"], "claim": "manual",
                    "us_only": (t.get("market") or "US") == "US", "years": t["years"],
                    "label": f'{t["make"]} {t["model"]} {t["trim"]}',
                    "idents": t["identification"],
                    "citations": first_url(t.get("evidence"))})
    return out


# ------------------------------------------------------------------- epa_sole
def compile_epa(doc: dict) -> list[dict]:
    inv = json.loads((DATA / "inventory_live.json").read_text())
    fi = {f: i for i, f in enumerate(inv["fields"])}
    by_id = {str(row[fi["id"]]): row for row in inv["vehicles"]}
    cache = json.loads(gzip.decompress((DATA / "vin_decodes.json.gz").read_bytes()))
    idents: dict[str, set] = defaultdict(set)
    for c in doc.get("newly_confirmed_manual_cars", []):
        row = by_id.get(str(c["id"]))
        dec = cache.get((c.get("vin") or "").upper())
        if not row or not isinstance(dec, dict):
            continue
        idents[c["rule"]].add((row[fi["make"]] or "", row[fi["model"]] or "",
                               (dec.get("make") or "").upper(), dec.get("model") or ""))
    out = []
    for r in doc["rules"]:
        ys = sorted(int(y) for y, s in (r.get("status_by_year") or {}).items() if s in COUNTED_EPA_YEAR)
        if not ys or r.get("claim") != "manual":
            continue
        sc = r["scope"]
        eng = sc.get("engine") or {}
        drive = (sc.get("drive") or "")
        drive = drive if drive in ("4wd", "awd", "2wd", "fwd", "rwd", "4x2") else ""
        level = sc.get("level") or "engine"
        ids = sorted(idents.get(r["id"], ()))
        if not ids:
            # No placed car to pin the make/model identity: the rule cannot
            # be applied without the EPA name tables, so it is left out.
            continue
        out.append({"id": r["id"], "src": "epa_sole.json", "status": r["status"], "claim": "manual",
                    "us_only": False, "years": ys, "level": level,
                    "displ": eng.get("displacementL"), "cyl": eng.get("cylinders"), "drive": drive,
                    "identities": [list(x) for x in ids],
                    "epa_names": sc.get("epa_model_names") or [],
                    "label": f'EPA {sc.get("epa_make")} {sc.get("epa_base_models")} '
                             + (f'{eng.get("displacementL")}L' if level == "engine" else "all engines")
                             + (f" {drive}" if drive else ""),
                    "citations": first_url(r.get("citations"))})
    return out


def main() -> int:
    files = [f"vin_rules_{i}.json" for i in range(8)] + ["manual_trims.json", "epa_sole.json"]
    docs = {f: json.loads((HERE / f).read_text()) for f in files}
    vin, documented = compile_honda(docs["vin_rules_0.json"])
    for i in range(1, 8):
        vin += compile_generic(i, docs[f"vin_rules_{i}.json"])
    trims = compile_trims(docs["manual_trims.json"])
    epa = compile_epa(docs["epa_sole.json"])
    # sanity: every regex compiles, every manual and_re compiles
    for c in vin:
        re.compile(c["re"])
        if c["and_re"]:
            re.compile(c["and_re"])
    for t in trims:
        for i in t["idents"]:
            for k in ("regex", "make", "model", "trim", "engine", "drive", "vin"):
                if i.get(k):
                    re.compile(i[k])
    out = {
        "version": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scraper/manual_detect/compile_trans_rules.py",
        "sources": {f: sha(HERE / f) for f in files + [f"vin_rules_{i}.py" for i in range(8)]},
        "precedence": ["vpic", "listing", "vin_code", "trim", "epa"],
        "note": ("Runtime table for scraper/trans_evidence.py. Manual claims publish a Manual "
                 "transmission only when no other source disagrees; automatic claims and "
                 "conflict_only rules are used only to withhold a disagreeing value."),
        "counts": {
            "vin_clauses": len(vin),
            "vin_rules": len({c["id"] for c in vin}),
            "vin_manual_clauses": sum(c["claim"] == "manual" for c in vin),
            "trim_rules": len(trims), "epa_rules": len(epa),
            "honda_documented_codes": len(documented),
        },
        "vin_rules": vin,
        "honda_documented": documented,
        "trim_rules": trims,
        "epa_rules": epa,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n")
    print(json.dumps(out["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
