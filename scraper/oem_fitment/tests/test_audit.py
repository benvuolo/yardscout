#!/usr/bin/env python3
"""Offline test for audit.py: real records (fixtures from the 2026-11-05 trial and
oem-raw checkpoints) pass clean; every single-field corruption is caught; the
LBK13001 bulb kit is flagged as a category suspect.
Run: python3 scraper/oem_fitment/tests/test_audit.py"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import audit  # noqa: E402

FIX = json.loads((HERE / "audit_fixtures.json").read_text())
CLEAN = [FIX["55077120AB"], FIX["23100-JA11B"], FIX["28100-20020-84"]]  # Mopar, Nissan, Toyota (SimplePart)
n = 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        raise AssertionError(msg)


for r in CLEAN:
    o = audit.audit_record(r)
    ok(not o.get("E") and not o.get("C"), f"{r['site']} {r['pn']} should be clean: {dict(o)}")

o = audit.audit_record(FIX["LBK13001"])
ok(not o.get("E") and any("Bulb" in m for m in o.get("C", [])), "LBK13001 bulb kit flagged as category suspect")


def f0(r):
    return r["fitment"][0]


def flip_position(r):
    p = r.get("position")
    r["position"] = "Left" if p == "Right" else ("Right" if p else "Driver Side")


MUTATIONS = {
    "years": lambda r: f0(r).__setitem__("years", [f0(r)["years"][0] - 1, f0(r)["years"][1]]),
    "make": lambda r: f0(r).__setitem__("make", "Honda"),
    "model": lambda r: f0(r).__setitem__("model", "X" + f0(r)["model"]),
    "trims": lambda r: f0(r).__setitem__("trims", f0(r)["trims"][1:] if f0(r)["trims"] else ["Fake"]),
    "engines": lambda r: f0(r).__setitem__("engines", ["9 Cyl 9.9L"]),
    "row_drop": lambda r: r["fitment"].pop(),
    "replaces": lambda r: r.__setitem__("replaces", list(r.get("replaces") or []) + ["ZZZ"]),
    "replaced_by": lambda r: r.__setitem__("replaced_by", (r["replaced_by"] + ["ZZZ"]) if isinstance(r.get("replaced_by"), list) else "ZZZ"),
    "position": flip_position,
    "pn": lambda r: r.__setitem__("pn", r["pn"] + "X"),
}
for name, mut in MUTATIONS.items():
    for r in CLEAN:
        m = copy.deepcopy(r)
        mut(m)
        ok(audit.audit_record(m).get("E"), f"mutation {name} not caught on {r['site']} {r['pn']}")

# duplicate detection and rate through main()-style aggregation
import tempfile  # noqa: E402
dup = Path(tempfile.mkstemp(suffix=".jsonl")[1])
dup.write_text("\n".join(json.dumps(r) for r in [FIX["55077120AB"], FIX["55077120AB"]]))
try:
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit.main([str(dup)])
    res = json.loads(buf.getvalue())["www.moparpartsgiant.com"]
    ok(len(res["D"]) == 2 and res["mismatch_rate"] == 0, "duplicates listed, not counted")
finally:
    dup.unlink()

print(f"OK {n} checks")
