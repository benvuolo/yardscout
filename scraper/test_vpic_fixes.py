#!/usr/bin/env python3
"""VPIC_TRANS_FIXES: known NHTSA decode errors are corrected, nothing else moves.

Run:  python3 scraper/test_vpic_fixes.py
"""
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        failures.append(name)


lr3 = {"make": "LAND ROVER", "model": "LR3", "modelYear": "2005", "engine": "4.4L 8-cyl", "transmission": "5-spd Automatic"}
fixed = js._correct_vpic(lr3)
check("2005 LR3 becomes 6-spd", fixed["transmission"] == "6-spd Automatic" and fixed.get("transmissionFixed") is True)
check("input not mutated", lr3["transmission"] == "5-spd Automatic")
for dec, why in (
    ({**lr3, "modelYear": "2006", "transmission": "6-spd Automatic"}, "2006 LR3 already right"),
    ({**lr3, "model": "Range Rover"}, "2005 Range Rover really is a 5-speed"),
    ({**lr3, "make": "JAGUAR", "model": "XJ8", "modelYear": "1998", "transmission": "5-spd Automatic"}, "1998 XJ8 really is a 5-speed"),
    ({**lr3, "transmission": "5-spd Manual/Standard"}, "only the exact wrong text is replaced"),
    ({**lr3, "transmission": ""}, "empty transmission untouched"),
):
    check(f"unchanged: {why}", js._correct_vpic(dec) == dec, str(js._correct_vpic(dec)))
check("None passes through", js._correct_vpic(None) is None)

# Against the real cache: every 2005 LR3 decode is corrected, nothing else changes.
cache = json.load(gzip.open(Path(__file__).resolve().parent.parent / "docs" / "data" / "vin_decodes.json.gz"))
changed = {vin for vin, d in cache.items() if isinstance(d, dict) and js._correct_vpic(d) != d}
lr3_2005 = {vin for vin, d in cache.items() if isinstance(d, dict) and d.get("model") == "LR3" and d.get("modelYear") == "2005" and d.get("transmission")}
check("real cache: exactly the 2005 LR3 decodes change", changed == lr3_2005 and len(changed) > 0, f"{len(changed)} vs {len(lr3_2005)}")
check("real cache: the reported car is among them", "SALAD25445A319797" in changed)

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
