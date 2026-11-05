#!/usr/bin/env python3
"""CI gate run by oem-fitment-crawl.yml after every checkpoint.

    python3 scraper/oem_fitment/ci_audit.py --site <site>      (reads raw/<site>.jsonl)
    python3 scraper/oem_fitment/ci_audit.py raw/<site>.jsonl

Runs audit.audit_record on every record (offline, evidence_lines only) and
prints one summary line. The records file is read whole: raw/<site>.jsonl
and every size-capped continuation part (<site>.2.jsonl, <site>.3.jsonl ...,
rawparts.py), never the .lists / .years manifests. Exit 0 = fine; exit 20 =
evidence-mismatch rate above 0.5% on at least 200 records, which means a
parser bug: the workflow then writes raw/<site>.paused so no further crawl
runs until a person reviews it. Category suspects (C) are heuristic and only
reported. A line that does not parse (a torn tail the next crawl start cuts)
is counted as unreadable, not audited."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit  # noqa: E402
import rawparts  # noqa: E402

LIMIT, MIN_RECORDS = 0.005, 200


def records_paths(argv: list[str]) -> list[Path]:
    if len(argv) >= 2 and argv[0] == "--site":
        return rawparts.part_paths(HERE / "raw", argv[1])
    p = Path(argv[0])
    if rawparts.kind_of(p) != "records":
        sys.exit(f"ci_audit: {p} is a manifest file, not records")
    return rawparts.logical_paths(p) if p.exists() else []


def main(argv: list[str]) -> int:
    paths = records_paths(argv)
    e_bad = c_bad = n = unreadable = 0
    examples = []
    for _, r in rawparts.rows(paths):
        if not isinstance(r, dict):
            unreadable += 1
            continue
        n += 1
        r.setdefault("pn", r.get("aftermarket_pn"))
        o = audit.audit_record(r)
        if o.get("E"):
            e_bad += 1
            if len(examples) < 5:
                examples.append(f"{r.get('category')} {r.get('pn')}: {o['E'][0]}")
        if o.get("C"):
            c_bad += 1
    rate = e_bad / n if n else 0.0
    name = paths[0].name if paths else (argv[1] if argv[0] == "--site" else Path(argv[0]).name)
    print(f"audit {name}: parts={len(paths)} records={n} evidence_mismatch={e_bad} ({100 * rate:.2f}%) "
          f"category_suspects={c_bad}" + (f" unreadable={unreadable}" if unreadable else ""))
    for x in examples:
        print("  E", x)
    return 20 if n >= MIN_RECORDS and rate > LIMIT else 0


if __name__ == "__main__":
    if not sys.argv[1:]:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
