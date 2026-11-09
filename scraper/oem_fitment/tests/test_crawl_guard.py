#!/usr/bin/env python3
"""crawl.py local-run guard (hub 2026-11-09): a local run never crawls a domain
the CI crawl has work pending on. CI (GITHUB_ACTIONS=true) is exempt;
--scratch-offline makes fetch cache-only. Offline: no request is made.
Run: python3 scraper/oem_fitment/tests/test_crawl_guard.py"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import crawl  # noqa: E402
import fetch  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


def exits(fn):
    try:
        fn()
        return None
    except SystemExit as e:
        return str(e)


real_pending = crawl.ci_pending
os.environ.pop("GITHUB_ACTIONS", None)

crawl.ci_pending = lambda site, wl, repo: "crawl"
msg = exits(lambda: crawl.local_guard("www.toyotapartsnow.com", False))
check("pending CI work (crawl) refuses a local run", bool(msg) and "work pending" in msg)
crawl.ci_pending = lambda site, wl, repo: "complete"
check("pending CI work (complete) refuses a local run",
      bool(exits(lambda: crawl.local_guard("www.toyotapartsnow.com", False))))


def boom(site, wl, repo):
    raise RuntimeError("no git")


crawl.ci_pending = boom
msg = exits(lambda: crawl.local_guard("www.toyotapartsnow.com", False))
check("unreadable CI state refuses (fails closed)", bool(msg) and "unknown" in msg)

crawl.ci_pending = lambda site, wl, repo: None
fetch.OFFLINE = False
check("no CI work pending: local run allowed, network on",
      exits(lambda: crawl.local_guard("www.toyotapartsnow.com", False)) is None and fetch.OFFLINE is False)

crawl.ci_pending = lambda site, wl, repo: "crawl"
check("--scratch-offline: allowed, fetch cache-only",
      exits(lambda: crawl.local_guard("www.toyotapartsnow.com", True)) is None and fetch.OFFLINE is True)
try:
    fetch.get("https://www.toyotapartsnow.com/__never_cached_test_page__")
    check("offline fetch of an uncached page raises NetworkError (no request)", False)
except fetch.NetworkError as e:
    check("offline fetch of an uncached page raises NetworkError (no request)", "offline" in str(e))
fetch.OFFLINE = False

os.environ["GITHUB_ACTIONS"] = "true"
crawl.ci_pending = boom
check("CI run (GITHUB_ACTIONS=true) is exempt", exits(lambda: crawl.local_guard("www.toyotapartsnow.com", False)) is None)
os.environ.pop("GITHUB_ACTIONS", None)
crawl.ci_pending = real_pending

# tier pass keys: a placeholder pass's done seeds are re-read when the pass number rises
check("tier_key: flag true -> plain tier", crawl.tier_key("D", {"tierD": True}) == "D")
check("tier_key: flag 1 -> plain tier", crawl.tier_key("D", {"tierD": 1}) == "D")
check("tier_key: flag 2 -> D2 (re-reads the placeholder pass's seeds)", crawl.tier_key("D", {"tierD": 2}) == "D2")
check("tier_key: ungated tiers unchanged", crawl.tier_key("A", {}) == "A" and crawl.tier_key("C", {"tierC": True}) == "C")

print()
if fails:
    print(f"FAILED {len(fails)}")
    sys.exit(1)
print("test_crawl_guard: all passed")
