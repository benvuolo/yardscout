#!/usr/bin/env python3
"""Offline tests for tools/store_subscribers.py's Google report handling.
Run:  python3 tools/test_store_subscribers.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import store_subscribers as ss

fails = []
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok: fails.append(name)

csv_text = ("Date,Package Name,Product ID,Country,New Subscriptions,Cancelled Subscriptions,Active Subscriptions\n"
            "2026-11-01,io.yardscout.app,yardscout_pro_monthly,US,0,0,1\n"
            "2026-11-02,io.yardscout.app,yardscout_pro_monthly,US,1,0,2\n"
            "2026-11-02,io.yardscout.app,yardscout_pro_monthly,CA,0,0,1\n")
for label, raw in (("utf-16 with BOM", csv_text.encode("utf-16")), ("utf-8", csv_text.encode("utf-8")),
                   ("utf-16-le no BOM", csv_text.encode("utf-16-le"))):
    n, day = ss.active_from_report(ss.decode_report(raw))
    check(f"{label}: newest date summed across countries", (n, day) == (3, "2026-11-02"), f"{n} {day}")
check("active column is not 'New'/'Cancelled'", ss._col(["New Subscriptions", "Cancelled Subscriptions", "Active Subscriptions"], "active",
      avoid=("cancel", "new")) == "Active Subscriptions")
names = ["financial-stats/subscriptions/subscriptions_io.yardscout.app_202610_country.csv",
         "financial-stats/subscriptions/subscriptions_io.yardscout.app_202611_country.csv",
         "financial-stats/subscriptions/subscriptions_com.other.app_202612_country.csv"]
check("newest month for our package", ss.pick_report(names, "io.yardscout.app") == names[1])
check("no report for the package", ss.pick_report(names[2:], "io.yardscout.app") is None)
check("bucket from gs:// URI", ss.bucket_name("gs://pubsite_prod_rev_0123/") == "pubsite_prod_rev_0123")
try:
    ss.active_from_report("Foo,Bar\n1,2\n"); check("unknown columns raise", False)
except ValueError:
    check("unknown columns raise", True)
print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
