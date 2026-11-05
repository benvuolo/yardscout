#!/usr/bin/env python3
"""Run every curation test file as its own process (as CLAUDE.md asks:
`python3 scraper/oem_fitment/curation_tests/test_x.py`) and print one line
per file plus every SKIP line, so a skip is never silent (rule 8).

    python3 scraper/oem_fitment/curation_tests/run_all.py [name-filter]

Exit 1 when any file fails."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv) -> int:
    flt = argv[1] if len(argv) > 1 else ""
    bad = 0
    for p in sorted(HERE.glob("test_*.py")):
        if flt and flt not in p.name:
            continue
        t0 = time.time()
        r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
        out = (r.stdout or "").splitlines()
        last = next((x for x in reversed(out) if x.strip()), "(no output)")
        print(f"{'PASS' if r.returncode == 0 else 'FAIL'} {p.name}: {last} ({time.time() - t0:.1f}s)")
        for x in out:
            if x.startswith("SKIP") or x.startswith("FAIL"):
                print("     " + x)
        if r.returncode != 0:
            bad += 1
            print("     " + "\n     ".join((r.stderr or "").strip().splitlines()[-8:]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
