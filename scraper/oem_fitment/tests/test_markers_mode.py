#!/usr/bin/env python3
"""markers.mode, completion first (hub 2026-11-10): one check per case.
Offline, pure function."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import markers  # noqa: E402

FAILS = 0


def check(name, ok, got=None):
    global FAILS
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
    if not ok:
        FAILS += 1


def m(entry, have):
    return markers.mode("s", entry, lambda n: n in have)


C = {"file": "completion/x.json", "version": 1}
check("first pass, no marker of any version: crawl (unchanged, e.g. gm)",
      m({"complete": C}, set()) == "crawl", m({"complete": C}, set()))
check("first pass of a re-opened v1 entry without complete: crawl",
      m({}, set()) == "crawl")
check("re-opened (v4, v3 marker present), completion open: complete first",
      m({"version": 4, "complete": C}, {"s.v3.done"}) == "complete")
check("re-opened, only the v1 .done present: complete first",
      m({"version": 3, "complete": C}, {"s.done"}) == "complete")
check("re-opened, completion done (c1.done): back to the current pass (crawl)",
      m({"version": 4, "complete": C}, {"s.v3.done", "s.c1.done"}) == "crawl")
check("re-opened, no completion configured: crawl",
      m({"version": 4}, {"s.v3.done"}) == "crawl")
check("re-opened, a new completion version (c2) not done while c1 is: complete",
      m({"version": 4, "complete": {"file": "f", "version": 2}}, {"s.v3.done", "s.c1.done"}) == "complete")
check("current marker present, completion open: complete (unchanged)",
      m({"version": 2, "complete": C}, {"s.v2.done"}) == "complete")
check("current marker and completion done: nothing (unchanged)",
      m({"version": 2, "complete": C}, {"s.v2.done", "s.c1.done"}) is None)
check("blocked: nothing, even with completion open",
      m({"version": 4, "complete": C}, {"s.v3.done", "s.blocked"}) is None)
check("paused: nothing",
      m({"version": 4, "complete": C}, {"s.v3.done", "s.paused"}) is None)
check("prev_done ignores the current version's own marker name",
      not markers.prev_done("s", {"version": 1}, lambda n: True))
print(f"\n{'OK' if not FAILS else 'FAILED'} test_markers_mode ({FAILS} failures)")
sys.exit(1 if FAILS else 0)
