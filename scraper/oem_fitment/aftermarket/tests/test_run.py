#!/usr/bin/env python3
"""Offline test of run.py: fake site module, temp raw dir, no network.

Checks priority order (make pages before model pages, scored models before
unscored, make pagination last), de-duplication across pages, the product
cap, resume from progress, and that a network error leaves the page queued.
"""
from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run  # noqa: E402

B = "https://fake.test"
TREE = {
    B + "/alt/": {"children": [B + "/alt/mazda/", B + "/alt/zz/"], "products": [], "next": None},
    B + "/alt/mazda/": {"children": [B + "/alt/mazda/tribute/", B + "/alt/mazda/r100/"], "products": [B + "/p/1"], "next": B + "/alt/mazda/?page=2"},
    B + "/alt/mazda/?page=2": {"children": [], "products": [B + "/p/9"], "next": None},
    B + "/alt/zz/": {"children": [], "products": [], "next": None},
    B + "/alt/mazda/tribute/": {"children": [], "products": [B + "/p/1", B + "/p/2"], "next": None},
    B + "/alt/mazda/r100/": {"children": [], "products": [B + "/p/3"], "next": None},
}
order: list[str] = []
fail_once = {B + "/p/3"}

mod = types.ModuleType("fakesite")
mod.SITE, mod.STATUS, mod.BASE = "fake.test", "ok", B
mod.CATEGORIES = {"alternator": {"root": "/alt/"}}


def listing(u):
    order.append(u)
    return TREE[u]


def product(u, cat):
    if u in fail_once:
        fail_once.discard(u)
        raise run.NetworkError("simulated")
    return {"site": "fake.test", "category": cat, "aftermarket_pn": u.rsplit("/", 1)[1], "product_url": u}


mod.listing, mod.product = listing, product
run.module_for = lambda site: mod
run.build_scores = lambda: ({"mazda": 100}, {("mazda", "tribute"): 900})
run.common.fetch.cache_path = lambda u: Path("/nonexistent")  # every request counts as new

fails = 0


def ok(c, m):
    global fails
    if not c:
        fails += 1
        print("FAIL", m)


def go(*args):
    sys.argv = ["run.py", "--site", "fake.test", *args]
    try:
        run.main()
        return 0
    except SystemExit as e:
        return e.code or 0


with tempfile.TemporaryDirectory() as td:
    run.RAW = Path(td)
    ok(go("--max-products", "1") == 0, "cap exit 0")
    recs = [json.loads(x) for x in open(Path(td) / "fake.test.jsonl")]
    ok([r["aftermarket_pn"] for r in recs] == ["1"], f"first record {recs}")
    ok(order[:2] == [B + "/alt/", B + "/alt/mazda/"], f"order {order}")
    code = go()
    recs = [json.loads(x)["aftermarket_pn"] for x in open(Path(td) / "fake.test.jsonl")]
    ok(code == 0, f"exit {code}")
    # zz make page before model pages; tribute (scored) before r100; make pagination last
    ok(order.index(B + "/alt/zz/") < order.index(B + "/alt/mazda/tribute/") < order.index(B + "/alt/mazda/r100/")
       < order.index(B + "/alt/mazda/?page=2"), f"order {order}")
    ok(sorted(recs) == ["1", "2", "3", "9"], f"records {recs}")  # p/1 not duplicated; p/3 retried
    ok(order.count(B + "/alt/mazda/r100/") == 2, "page with a network error is visited again")
    ok((Path(td) / "fake.test.done").exists(), "done marker")

print("ok" if not fails else f"{fails} failures")
sys.exit(1 if fails else 0)
