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
check("workflow: one concurrency group per platform; the job runs the platform driver",
      "oem-crawl-platform-${{ matrix.group.platform }}" in wf and "platform_crawl.py --sites" in wf
      and "--timeout-min 350" in wf and "timeout-minutes: 350" in wf)
drv = (OEM / "platform_crawl.py").read_text()
check("driver: rotation, markers.mode per turn, audit (20 pauses), checkpoint push after every turn",
      "platforms.rotation(" in drv and "markers.mode(" in drv and "== 20" in drv and "ci_push_raw.sh" in drv)

# driver behaviour with fakes (hub fixes: crash loop, budget edge)
import platform_crawl as PC  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def sim(sites, rcs, modes=None, timeout=350, turn_secs=None):
    """rcs: {site: [rc, rc, ...]} consumed per turn; a site with no rc left
    reports rc 0 and mode None afterwards."""
    clk, logs, pushed, paused = Clock(), [], [], []
    left = {s: list(v) for s, v in rcs.items()}
    done = set()

    def mode_of(s):
        return None if s in done else (modes or {}).get(s, "crawl")

    def run_crawl(s, m, minutes):
        clk.t += turn_secs if turn_secs is not None else minutes * 60
        if not left.get(s):
            done.add(s)
            return 0
        rc = left[s].pop(0)
        if rc == 0:
            done.add(s)
        return rc

    turns = PC.drive(sites, 0, timeout, mode_of=mode_of, run_crawl=run_crawl, run_audit=lambda s: 0,
                     push=pushed.append, pause=paused.append, log=logs.append, clock=clk,
                     sleep=lambda x: None)
    return turns, logs, pushed, clk.t


t, lg, pu, _ = sim(["a", "b"], {"a": [2, 2, 2], "b": [10, 0]})
check("driver: an unexpected crawl exit (2) skips the site for the rest of the run (one turn only)",
      [x for x in t if x[0] == "a"] == [("a", "crawl", 2)] and any("a: crawl.py exit 2" in m for m in lg), t)
check("driver: the other site keeps its turns and every turn is pushed",
      [x[2] for x in t if x[0] == "b"] == [10, 0] and pu == [x[0] for x in t], (t, pu))
t, lg, _, _ = sim(["a", "b"], {"a": [11, 11, 10], "b": [10, 10, 0]})
check("driver: 2 consecutive network-failure exits (11) skip the site",
      [x[2] for x in t if x[0] == "a"] == [11, 11] and any("2 network-failure exits" in m for m in lg), t)
t, _, _, _ = sim(["a"], {"a": [11, 10, 11, 0]})
check("driver: an 11 followed by a normal turn resets the streak",
      [x[2] for x in t] == [11, 10, 11, 0], t)
t, lg, _, end = sim(["a"], {"a": [10] * 100}, timeout=350)
check("driver: no turn starts unless elapsed + turn + 10 min fits timeout - 10 (340 min)",
      end <= 340 * 60 and end + (30 + 10) * 60 > 340 * 60 and any("budget" in m for m in lg), (end / 60, len(t)))
t, _, _, end = sim(["a", "b", "c"], {"a": [10] * 99, "b": [10] * 99, "c": [10] * 99})
check("driver: with 3 sites each gets turns in rotation until the budget",
      [x[0] for x in t][:6] == ["a", "b", "c", "a", "b", "c"] and end <= 340 * 60, [x[0] for x in t][:6])
t, lg, _, _ = sim(["a", "b"], {"a": [], "b": []})
check("driver: sites with nothing to do end the run at once",
      t == [("a", "crawl", 0), ("b", "crawl", 0)] and lg[-1] == "nothing left this run", (t, lg[-1:]))
check("workflow: no per-site matrix left", "site: ${{ fromJSON(needs.plan.outputs.sites) }}" not in wf)

print(f"\n{'OK' if not FAILS else 'FAILED'} test_platforms ({FAILS} failures)")
sys.exit(1 if FAILS else 0)
