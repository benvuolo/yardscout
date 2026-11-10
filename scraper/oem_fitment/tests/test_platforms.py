#!/usr/bin/env python3
"""Per-platform crawl pacing (hub 2026-11-10, after three 503s with six
per-site jobs live): platform table, plan-step grouping, round-robin turns,
fetch.py platform lock and refusal log. Offline; no request is made."""
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OEM = HERE.parent
sys.path.insert(0, str(OEM))
import platforms  # noqa: E402
import fetch  # noqa: E402

FAILS = 0


def check(name, ok, got=None):
    global FAILS
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
    if not ok:
        FAILS += 1


sites = []
for f in sorted((OEM / "sites").glob("*.py")):
    if f.name.startswith("_"):
        continue
    m = re.search(r'^SITE\s*=\s*"([^"]+)"', f.read_text(), re.M)
    if m:
        sites.append(m.group(1))
missing = [s for s in sites if s not in platforms.PLATFORM]
check("every crawled site module has a platform in the table", not missing, missing)
check("every crawled catalog site is on the SimplePart platform (served markers, SOURCES.md 2)",
      {platforms.PLATFORM[s] for s in sites if s in platforms.PLATFORM} == {platforms.SIMPLEPART})
check("the platform gap equals the old single-site pace (fetch.PER_DOMAIN_GAP)",
      platforms.PLATFORM_GAP[platforms.SIMPLEPART] == fetch.PER_DOMAIN_GAP)

g = platforms.groups(["www.gmpartsgiant.com", "www.example-new.com", "www.kiapartsnow.com"])
check("groups: one entry per platform, sites kept in order, unknown site isolated",
      g == [{"platform": "simplepart", "sites": "www.gmpartsgiant.com www.kiapartsnow.com"},
            {"platform": "site:www.example-new.com", "sites": "www.example-new.com"}], g)
check("groups of all live sites: exactly one job", len(platforms.groups(sites)) == 1)
check("groups of nothing: empty matrix", platforms.groups([]) == [])

r = ["a", "b", "c", "d"]
check("rotation starts at run_number mod n and keeps every site once",
      platforms.rotation(r, 6) == ["c", "d", "a", "b"] and sorted(platforms.rotation(r, 13)) == r
      and platforms.rotation(r, 0) == r and platforms.rotation([], 5) == [])
check("over n consecutive runs every site goes first once",
      {platforms.rotation(r, k)[0] for k in range(4)} == set(r))
check("turn length: 15 sites -> 20 min, 2 sites -> 30 (cap), 40 sites -> 10 (floor)",
      (platforms.slice_minutes(15), platforms.slice_minutes(2), platforms.slice_minutes(40)) == (20, 30, 10))

# fetch.py: the platform lock is taken for a platform site, not for others
calls = []
_orig = fetch._locked_wait
fetch._locked_wait = lambda name, gap: calls.append((name, gap))
try:
    fetch._platform_wait("www.kiapartsnow.com")
    fetch._platform_wait("en.wikipedia.org")
finally:
    fetch._locked_wait = _orig
check("fetch: a SimplePart site waits on the shared platform lock at 8 s; a non-platform host takes none",
      calls == [("platform_simplepart", 8.0)], calls)
src = (OEM / "fetch.py").read_text()
check("fetch: both request paths (robots and page) take the platform lock and count the request",
      src.count("_platform_wait(u.netloc)") == 2 and src.count("_note_request(u.netloc)") == 2)
check("fetch: a refusal or challenge is logged before the breaker is written",
      src.index("_log_refusal(u.netloc, url, r.status_code)") < src.index("_breaker(u.netloc).write_text"))

# refusal log line
d = Path(tempfile.mkdtemp())
fetch.REFUSAL_LOG_DIR = d
fetch._REQ_TIMES.clear()
for t in (1000.0, 1250.0, 1290.0):
    fetch._note_request("www.kiapartsnow.com", t)
fetch._note_request("www.gmpartsgiant.com", 1295.0)
p = fetch._log_refusal("www.kiapartsnow.com", "https://www.kiapartsnow.com/x", 503, now=1300.0)
rec = json.loads(p.read_text().splitlines()[-1])
check("refusal log: one JSON line in raw/<site>.refusals.jsonl with time, status, platform",
      p.name == "www.kiapartsnow.com.refusals.jsonl" and rec["status"] == 503 and rec["platform"] == "simplepart"
      and rec["ts"].startswith("1970-01-01T00:21:40"), rec)
check("refusal log: recent request counts per host (60/300/900 s)",
      rec["counts"]["www.kiapartsnow.com"] == {"60s": 2, "300s": 3, "900s": 3}
      and rec["counts"]["www.gmpartsgiant.com"]["60s"] == 1, rec["counts"])

wf = (OEM.parents[1] / ".github" / "workflows" / "oem-fitment-crawl.yml").read_text()
check("workflow: plan emits platform groups; matrix is per platform; max-parallel = platforms",
      "platforms.groups(sites)" in wf and "group: ${{ fromJSON(needs.plan.outputs.groups) }}" in wf
      and "max-parallel: ${{ fromJSON(needs.plan.outputs.nplat) }}" in wf)
check("workflow: one concurrency group per platform; sites crawled in turn with rotation and checkpoints",
      "oem-crawl-platform-${{ matrix.group.platform }}" in wf and "platforms.rotation(" in wf
      and 'push_raw "$SITE"' in wf and "ci_audit.py --site" in wf and "raw/$SITE.paused" in wf)
check("workflow: no per-site matrix left", "site: ${{ fromJSON(needs.plan.outputs.sites) }}" not in wf)

print(f"\n{'OK' if not FAILS else 'FAILED'} test_platforms ({FAILS} failures)")
sys.exit(1 if FAILS else 0)
