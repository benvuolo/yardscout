#!/usr/bin/env python3
"""plan_sites.py (crawl matrix planner), offline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import plan_sites as p  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


s = p.adapter_sites()
check("ok adapters listed", {"www.dbelectrical.com", "ecat.spectrapremium.com", "www.1aauto.com", "gspnorthamerica.com"} <= set(s))
check("unreachable adapters excluded", "www.densoautoparts.com" not in s and "www.tycamericas.com" not in s)
check("curation modules excluded (no product())", s.count("www.dbelectrical.com") == 1)
check(".done and .blocked skipped", p.plan("all", lambda x: x.endswith("www.dbelectrical.com.done") or x.endswith("www.1aauto.com.blocked"))
      == sorted(set(s) - {"www.dbelectrical.com", "www.1aauto.com"}))
check("explicit list filters", p.plan("www.1aauto.com, unknown.example", lambda x: False) == ["www.1aauto.com"])
print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
