#!/usr/bin/env python3
"""CI gate run by oem-fitment-crawl.yml after every checkpoint.

    python3 scraper/oem_fitment/ci_audit.py raw/<site>.jsonl

Runs audit.audit_record on every record (offline, evidence_lines only) and
prints one summary line. Exit 0 = fine; exit 20 = evidence-mismatch rate above
0.5% on at least 200 records, which means a parser bug: the workflow then
writes raw/<site>.paused so no further crawl runs until a person reviews it.
Category suspects (C) are heuristic and only reported."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit  # noqa: E402

LIMIT, MIN_RECORDS = 0.005, 200
p = Path(sys.argv[1])
recs = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
e_bad = c_bad = 0
examples = []
for r in recs:
    r.setdefault("pn", r.get("aftermarket_pn"))
    o = audit.audit_record(r)
    if o.get("E"):
        e_bad += 1
        if len(examples) < 5:
            examples.append(f"{r.get('category')} {r.get('pn')}: {o['E'][0]}")
    if o.get("C"):
        c_bad += 1
n = len(recs)
rate = e_bad / n if n else 0.0
print(f"audit {p.name}: records={n} evidence_mismatch={e_bad} ({100 * rate:.2f}%) category_suspects={c_bad}")
for x in examples:
    print("  E", x)
sys.exit(20 if n >= MIN_RECORDS and rate > LIMIT else 0)
