#!/usr/bin/env python3
"""Independent check of raw records against the cached page text.

    python3 scraper/oem_fitment/aftermarket/verify_records.py raw/<site>.jsonl [N]

Re-reads each record's product page from the fetch.py cache (no network),
flattens it with fetch.text_lines (a different path from the parser's
regexes), and checks: the item number; every specs pair; every application
row's cells, in order, inside the Applications List block; every replaces
row inside the Replaces block; and that oe_numbers are exactly the numbers
under carmaker brands. Prints one line per record and a summary.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402

fetch = common.fetch


def seq_in(hay: list[str], needle: list[str], start: int) -> int:
    """index after `needle` found as consecutive items in hay[start:], or -1"""
    n = len(needle)
    for i in range(start, len(hay) - n + 1):
        if hay[i:i + n] == needle:
            return i + n
    return -1


def check(rec: dict) -> list[str]:
    errs = []
    cp = fetch.cache_path(rec["product_url"])
    if not cp.exists():
        return ["page not in local cache"]
    tl = fetch.text_lines(fetch.get(rec["product_url"])["html"])
    if rec["aftermarket_pn"] not in tl or f"Item Number: {rec['aftermarket_pn']}" not in tl:
        errs.append("item number not on page")
    for k, v in rec["specs"].items():
        if seq_in(tl, [k] + v.split("\n"), 0) < 0:
            errs.append(f"spec {k}={v} not on page")
    try:
        a0 = tl.index("Applications List", tl.index("Product Specs"))
        r0 = tl.index("Replaces These Part Numbers", a0)
    except ValueError:
        return errs + ["blocks not found"]
    app_text, pos = tl[a0:r0], 0
    for a in rec["applications"]:
        cells = [c for c in a["raw"].split(" | ")]
        cells = [c for c in cells if c]  # empty cells vanish in text_lines
        p = seq_in(app_text, cells, pos)
        if p < 0:
            errs.append(f"application row not found in order: {a['raw']}")
        else:
            pos = p
        y = str(a["years"][0]) if a["years"][0] == a["years"][1] else f"{a['years'][0]}-{a['years'][1]}"
        if y not in cells:
            errs.append(f"years {a['years']} not in row {a['raw']}")
    n_rows = sum(1 for x in app_text if x.isdigit() and len(x) == 4 and 1940 <= int(x) <= 2035)  # not "1500"/"3116"
    if n_rows != len(rec["applications"]):
        errs.append(f"page shows {n_rows} year cells, record has {len(rec['applications'])} applications")
    rep_text = tl[r0:]
    for r in rec["replaces"]:
        if seq_in(rep_text, [r["brand"], ", ".join(r["numbers"])], 0) < 0:
            errs.append(f"replaces row not on page: {r['brand']}")
    want = [(r["brand"], n) for r in rec["replaces"] for n in r["numbers"]
            if r["brand"].strip().upper() in common.CARMAKER_BRANDS]
    got = [(o["brand"], o["pn"]) for o in rec["oe_numbers"] if "role_basis" not in o]
    if want != got:
        errs.append(f"oe_numbers mismatch: page {want} vs record {got}")
    return errs


def main() -> None:
    path = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
    ok = bad = 0
    for i, line in enumerate(open(path)):
        if i >= n:
            break
        rec = json.loads(line)
        e = check(rec)
        status = "OK " if not e else "BAD"
        ok += not e
        bad += bool(e)
        print(f"{status} {rec['category']} {rec['aftermarket_pn']} apps={len(rec['applications'])} "
              f"replaces={len(rec['replaces'])} oe={len(rec['oe_numbers'])} {'; '.join(e)[:400]}")
    print(f"summary: {ok} ok, {bad} with differences")


if __name__ == "__main__":
    main()
