#!/usr/bin/env python3
"""Run every offline oem_fitment test (this directory and aftermarket/tests),
one subprocess per file, and print one line per file plus a summary.

    python3 scraper/oem_fitment/tests/run_all.py [-v]

Exit status 1 when any file fails. Skips inside a file are printed by that
file (CLAUDE.md rule 8); -v shows each file's full output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = sorted(HERE.glob("test_*.py")) + sorted((HERE.parent / "aftermarket" / "tests").glob("test_*.py"))


def main() -> int:
    verbose = "-v" in sys.argv[1:]
    bad = []
    for f in FILES:
        p = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=600)
        out = (p.stdout + p.stderr).strip()
        last = out.splitlines()[-1] if out else ""
        skips = sum(1 for ln in out.splitlines() if ln.startswith("SKIP"))
        print(f"{'ok  ' if p.returncode == 0 else 'FAIL'} {f.relative_to(HERE.parent)}: {last}"
              + (f"  [{skips} skip lines]" if skips else ""))
        if verbose or p.returncode != 0:
            print("    " + out.replace("\n", "\n    "))
        if p.returncode != 0:
            bad.append(f.name)
    print(f"\n{len(FILES) - len(bad)}/{len(FILES)} files pass" + (f"; failing: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
