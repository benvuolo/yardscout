#!/usr/bin/env python3
"""VIN decode schema-upgrade test suite — standalone, no network.

Covers _vpic_incremental_queue (new-VIN priority, old-schema upgrade queue,
cap budgeting) and the db.py persistence semantics the upgrade relies on
(replace=True overwrites, default never does; forced gz export). Run:

    python3 scraper/test_vin_schema_upgrade.py
"""
import json
import gzip
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402
import db  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    tag = "ok  " if cond else "FAIL"
    print(f"{tag} {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


OLD = {"trim": "LT", "trimQuality": "usable"}                    # pre-engine schema
NEW = {"trim": "LT", "trimQuality": "usable", "engine": "5.3L 8-cyl"}
NEW_EMPTY = {"trim": "", "trimQuality": "", "engine": ""}        # decoded, vPIC had no engine

# --- queue: never-seen VINs always win the cap ----------------------------
vin_newest = {"NEW1": "2026-10-25", "NEW2": "2026-10-26",
              "OLD1": "2026-10-24", "OLD2": "2026-10-23", "DONE": "2026-10-22"}
cached = {"OLD1": dict(OLD), "OLD2": dict(OLD), "DONE": dict(NEW)}

todo, up, n_new, n_stale = js._vpic_incremental_queue(vin_newest, cached, cap=3)
check("new VINs decoded newest-first", todo == ["NEW2", "NEW1"], str(todo))
check("leftover budget goes to old-schema upgrades, newest-first",
      up == ["OLD1"], str(up))
check("totals reported", (n_new, n_stale) == (2, 2), f"{n_new},{n_stale}")

todo, up, _, _ = js._vpic_incremental_queue(vin_newest, cached, cap=10)
check("big cap takes every new VIN and every old-schema VIN",
      todo == ["NEW2", "NEW1"] and up == ["OLD1", "OLD2"], f"{todo} {up}")
check("new-schema entries are never re-queued", "DONE" not in todo + up)

todo, up, _, _ = js._vpic_incremental_queue(vin_newest, cached, cap=2)
check("cap exhausted by new VINs leaves no upgrade budget",
      todo == ["NEW2", "NEW1"] and up == [], f"{todo} {up}")

todo, up, _, _ = js._vpic_incremental_queue(vin_newest, cached, cap=0)
check("cap 0 decodes nothing", todo == [] and up == [])

# empty-string engine (vPIC had no displacement) is NEW schema — never requeue,
# or every scan would re-decode the same hopeless VINs forever
todo, up, _, n_stale = js._vpic_incremental_queue(
    {"E1": "2026-10-26"}, {"E1": dict(NEW_EMPTY)}, cap=10)
check("empty-engine (new schema) decode is not re-queued",
      up == [] and n_stale == 0, f"{up} {n_stale}")

# --- db.py: replace semantics ---------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    db.DB_FILE = Path(tmp) / "test.db"
    db.store_vin_decodes({"V1": dict(OLD)}, "2026-09-01")
    db.store_vin_decodes({"V1": dict(NEW)}, "2026-10-26")  # default: ignored
    check("default store never overwrites (first decode wins)",
          "engine" not in db.load_vin_decodes()["V1"])
    n = db.store_vin_decodes({"V1": dict(NEW)}, "2026-10-26", replace=True)
    got = db.load_vin_decodes()["V1"]
    check("replace=True upgrades the payload",
          n == 1 and got.get("engine") == "5.3L 8-cyl", json.dumps(got))

    # --- forced gz export when the upgrade drain completes ----------------
    gz = Path(tmp) / "vin_decodes.json.gz"
    check("first export always writes", db.export_vin_decodes_gz(gz) is True)
    check("no-growth export is skipped", db.export_vin_decodes_gz(gz) is False)
    check("forced export writes despite no growth",
          db.export_vin_decodes_gz(gz, force=True) is True)
    data = json.loads(gzip.decompress(gz.read_bytes()))
    check("forced export carries the upgraded payload",
          data["V1"].get("engine") == "5.3L 8-cyl")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S): {FAILS}")
    sys.exit(1)
print("all vin schema-upgrade tests passed")
