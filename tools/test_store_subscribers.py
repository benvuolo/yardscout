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
# Apple: two vendor numbers (the account became YardScout LLC on 2026-11-05)
import datetime as _dt
T = _dt.date(2026, 11, 19)
old = {"2026-11-16": (3, 0), "2026-11-17": (3, 0), "2026-11-18": (2, 0)}
llc = {"2026-11-16": (2, 0), "2026-11-17": (2, 0), "2026-11-18": (2, 1)}
r = ss.apple_combine([old, llc], T)
check("two entities, same newest day: added", (r["active"], r["trial"], r["asOf"]) == (4, 1, "2026-11-18"), str(r))
check("two entities: per-entity counts, no vendor numbers", r.get("entities") == [{"active": 2}, {"active": 2}], str(r))
r = ss.apple_combine([old, {k: v for k, v in llc.items() if k != "2026-11-18"}], T)
check("one entity a day behind: the newest day BOTH have (no double count)", (r["active"], r["asOf"]) == (5, "2026-11-17"), str(r))
r = ss.apple_combine([old, {}], T)
check("second entity with no report counts 0", (r["active"], r["asOf"], r["entities"]) == (2, "2026-11-18", [{"active": 2}, {"active": 0}]), str(r))
r = ss.apple_combine([{"2026-11-18": (2, 0)}, {"2026-11-16": (1, 0)}], T)
check("no shared day: each newest, said so", r["active"] == 3 and r["asOf"] == "2026-11-16" and "different days" in r.get("note", ""), str(r))
r = ss.apple_combine([old], T)
check("one vendor number: as before, no entities key", r == {"active": 2, "trial": 0, "asOf": "2026-11-18"}, str(r))
r = ss.apple_combine([{}, {}], T)
check("no report anywhere: 0 with the note", r["active"] == 0 and r["asOf"] == "2026-11-18" and "none active" in r["note"], str(r))
wf = (Path(__file__).resolve().parent.parent / ".github/workflows/store-subscribers.yml").read_text()
check("workflow passes the second vendor number", "ASC_VENDOR_LLC: ${{ secrets.ASC_VENDOR_NUMBER_LLC }}" in wf)
print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
