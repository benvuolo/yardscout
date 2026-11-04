#!/usr/bin/env python3
"""Offline tests for scraper/coverage_sweep.py (no network).

  1. Name filter keeps yards, drops pick-your-own farms.
  2. Overpass parsing: centers for ways, website normalisation, de-dupe.
  3. Platform fingerprints and bot-check detection.
  4. Matching against tracked yards and registry entries (distance + name).
  5. check_site tiers with a fake site: platform on the homepage, platform on
     the inventory page, custom vehicle table, robots disallow, blocked, no
     inventory, unreachable. A blocked site is reported, never retried.
  6. run(): skips known yards, respects the site budget, renders a report.

Run:  python3 scraper/test_coverage_sweep.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coverage_sweep as cs  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        failures.append(name)


# 1. names
for n in ("U-Pull-It Omaha", "Pick-A-Part Jalopy Jungle", "Pull-N-Save", "Joe's Self Serve Auto Salvage",
          "Pik-A-Part", "Wrench-A-Part", "You Pull It Auto Parts"):
    check(f"yard kept: {n}", cs.looks_like_yard(n), n)
for n in ("Smith Farm U-Pick Strawberries", "Pick-A-Peck Orchard", "U-Pick Blueberries", "Pick N Pull Pumpkins",
          "Casapulla's Subs", "Lilly Pullitzer", "Pullara Drive", "Epic Apartments"):
    check(f"farm dropped: {n}", not cs.looks_like_yard(n), n)
check("farm tag dropped", not cs.looks_like_yard("Pick-A-Part", {"landuse": "orchard"}))

# 2. overpass parse
data = {"elements": [
    {"type": "node", "lat": 41.2, "lon": -96.0, "tags": {"name": "U-Pull-It", "website": "upullit.example", "addr:city": "Omaha", "addr:state": "NE"}},
    {"type": "way", "center": {"lat": 41.2001, "lon": -96.0001}, "tags": {"name": "U-Pull-It"}},  # duplicate of the node
    {"type": "way", "center": {"lat": 30.1, "lon": -90.1}, "tags": {"name": "Pick-A-Part", "contact:website": "https://pap.example/"}},
    {"type": "node", "lat": 40.0, "lon": -80.0, "tags": {"name": "U-Pick Berry Farm"}},
]}
cands = cs.parse_overpass(data)
check("overpass: farm dropped, duplicate merged", len(cands) == 2, str([c.name for c in cands]))
check("overpass: website gets a scheme", cands[0].website == "http://upullit.example" and cands[0].city == "Omaha")
check("overpass: way center + contact:website", cands[1].lat == 30.1 and cands[1].website == "https://pap.example/")

# 3. fingerprints
check("fingerprint: Ario iframe", cs.fingerprint('<iframe src="https://ario.autorecycler.io/yard/x?embed=1">') == ("Ario (autorecycler.io)", True))
check("fingerprint: VinPlus link", cs.fingerprint('<a href="https://vinplus.texnrewards.com/abc">')[1] is True)
check("fingerprint: yardconnect-pro plugin", cs.fingerprint('/wp-content/plugins/yardconnect-pro/x.js')[0] == "yardconnect-pro")
check("fingerprint: CRUSH", cs.fingerprint("$.ajax({url:'/Home/GetMakes'})")[0] == "CRUSH / S3 Software")
check("fingerprint: Row52 is not tier A", cs.fingerprint('<img src="https://cdn.row52.com/x.jpg">')[1] is False)
check("fingerprint: none", cs.fingerprint("<html>hours and directions</html>") is None)
check("bot check: 403", cs.is_challenge(403, "nope"))
check("bot check: Cloudflare interstitial", cs.is_challenge(200, "<title>Just a moment...</title><div id=cf-chl>"))
check("bot check: a normal page that mentions captcha far down is not one", not cs.is_challenge(200, "x" * 20000 + "captcha"))
link = cs.inventory_link("https://yard.example/", '<a href="/price-list">Prices</a><a href="/our-inventory/">Vehicle Inventory</a><a href="https://other.example/inventory">x</a>')
check("inventory link: same-site, skips price list", link == "https://yard.example/our-inventory/", str(link))

# 4. matching
known = [cs.Known("Pull-A-Part - Atlanta", "Atlanta", "GA", 33.75, -84.39, "tracked"),
         cs.Known("Kenny U-Pull - Bangor", "Bangor", "ME", None, None, "candidate")]
check("match: within 3 km", cs.match_known("Pull A Part", "", "", 33.76, -84.39, known).status == "tracked")
check("match: far away is new", cs.match_known("Pull A Part", "", "", 34.5, -84.39, known) is None)
check("match: registry by name + city without coords", cs.match_known("Kenny U-Pull", "Bangor", "ME", None, None, known).status == "candidate")
check("match: same name, punctuation aside, no coords or city", cs.match_known("Pull A Part - Atlanta", "", "", None, None, known).status == "tracked")


class FakeResp:
    def __init__(self, status, payload=None, text=""):
        self.status_code, self._p, self.text = status, payload or {}, text

    def json(self):
        return self._p


class FakeOverpass:
    """plan[(url, state)] is one response, or a list served in order (the
    last one repeats); an Exception instance is raised. status[url] is the
    /api/status text."""

    def __init__(self, plan, status=None):
        self.plan, self.status, self.calls, self.timeouts = plan, status or {}, [], []

    def get(self, url, timeout=None, headers=None):
        base = url.rsplit("/", 1)[0] + "/interpreter"
        t = self.status.get(base)
        return FakeResp(200, text=t) if t is not None else FakeResp(404)

    def post(self, url, data=None, timeout=None, headers=None):
        st = data["data"].split('"US-')[1][:2]
        self.calls.append((url, st))
        self.timeouts.append(timeout)
        r = self.plan.get((url, st), FakeResp(504))
        if isinstance(r, list):
            r = r.pop(0) if len(r) > 1 else r[0]
        if isinstance(r, Exception):
            raise r
        return r


slept = []
def nosleep(sec):
    slept.append(sec)


m, k, pc = cs.OVERPASS_URLS
el = {"elements": [{"type": "node", "lat": 41.0, "lon": -96.0, "tags": {"name": "U-Pull-It"}}]}
fo = FakeOverpass({(m, "NE"): FakeResp(200, el), (k, "IA"): FakeResp(200, el)})
got, err = cs.fetch_osm(fo, states=("NE", "IA", "KS"), pause=0, sleep=nosleep)
check("osm: per-state, mirror on failure, failed states named",
      len(got) == 2 and got[0].state == "NE" and got[1].state == "IA" and err == "Overpass failed for KS"
      and (k, "IA") in fo.calls, f"{err} {fo.calls}")


# 5. check_site with a fake site
class FakeSite:
    def __init__(self, pages, disallow=()):
        self.pages, self.disallow, self.gets = pages, set(disallow), []

    def allowed(self, url):
        return url not in self.disallow

    def get(self, url):
        self.gets.append(url)
        st, html = self.pages.get(url, (0, "ConnectionError"))
        return st, url, html


def tier(pages, url="https://y.example/", disallow=()):
    fs = FakeSite(pages, disallow)
    c = cs.check_site(cs.Candidate(name="Y", website=url), fs)
    return c, fs


c, _ = tier({"https://y.example/": (200, '<script src="/wp-content/plugins/yardconnect-pro/a.js"></script>')})
check("site: platform on homepage -> A", c.tier == "A" and c.platform == "yardconnect-pro", c.evidence)
c, fs = tier({"https://y.example/": (200, '<a href="/inventory/">Inventory</a>'),
              "https://y.example/inventory/": (200, '<iframe src="https://ario.autorecycler.io/yard/y?embed=1">')})
check("site: platform on the inventory page -> A", c.tier == "A" and "inventory" in c.evidence, c.evidence)
c, _ = tier({"https://y.example/": (200, '<a href="/vehicles">Our Cars</a>'),
             "https://y.example/vehicles": (200, "<table><tr><th>Year</th><th>Make</th><th>Model</th><th>Row</th></tr></table>")})
check("site: custom vehicle table -> B", c.tier == "B" and c.platform == "custom", c.evidence)
c, fs = tier({"https://y.example/": (200, "x")}, disallow={"https://y.example/"})
check("site: robots disallow -> C, nothing fetched", c.tier == "C" and not fs.gets, c.evidence)
c, fs = tier({"https://y.example/": (403, "Forbidden")})
check("site: blocked -> C, fetched once, not retried", c.tier == "C" and len(fs.gets) == 1 and "ask the yard" in c.evidence, c.evidence)
c, _ = tier({"https://y.example/": (200, "<a href='/hours'>Hours</a>")})
check("site: no inventory -> D", c.tier == "D", c.evidence)
c, _ = tier({})
check("site: unreachable -> E", c.tier == "E", c.evidence)
c, _ = tier({}, url="")
check("site: no website -> E", c.tier == "E" and "no website" in c.evidence)

# 6. run()
osm = [cs.Candidate(name="Pull-A-Part", lat=33.751, lng=-84.391),               # tracked
       cs.Candidate(name="New U-Pull", lat=45.0, lng=-93.0, website="https://n1.example/"),
       cs.Candidate(name="Other U-Pull", lat=46.0, lng=-93.0, website="https://n2.example/")]
fs = FakeSite({"https://n1.example/": (200, "gm_vehicle_search"), "https://n2.example/": (200, "hours")})
out, skipped, notes = cs.run(None, known=known, site=fs, max_sites=1,
                             osm_fetch=lambda s: (osm, ""), ario_fetch=lambda s: ([], "offline"))
check("run: tracked yard skipped", skipped == {"tracked": 1}, str(skipped))
check("run: budget respected", fs.gets == ["https://n1.example/"] and out[1].evidence.startswith("not checked"), str(fs.gets))
check("run: notes carry source errors and the cap", any("Ario" in n for n in notes) and any("capped" in n for n in notes), str(notes))
# time budget: a fake clock that jumps 10 minutes per check
tick = [0.0]
def clock():
    return tick[0]
class SlowSite(FakeSite):
    def get(self, url):
        tick[0] += 600
        return super().get(url)
many = [cs.Candidate(name=f"U-Pull {i}", lat=40 + i, lng=-100.0, website=f"https://s{i}.example/") for i in range(6)]
ss = SlowSite({f"https://s{i}.example/": (200, "hours") for i in range(6)})
out3, _, notes3 = cs.run(None, known=[], site=ss, osm_fetch=lambda s, deadline=None: (many, ""),
                         ario_fetch=lambda s: ([], ""), budget_min=30, clock=clock)
check("run: time budget stops site checks, report still complete",
      len(out3) == 6 and sum(1 for c in out3 if "time budget" in c.evidence) == 2 and any("Time budget" in n for n in notes3),
      f"{[c.evidence for c in out3]} {notes3}")
fo2 = FakeOverpass({(m, "NE"): FakeResp(200, el)})
got2, err2 = cs.fetch_osm(fo2, states=("NE", "IA"), pause=0, deadline=1.0, sleep=nosleep)
check("osm: deadline in the past skips the remaining states", got2 == [] and "not queried: NE, IA" in err2, err2)

# --- Overpass resilience (2026-11-03 run: every state lost to 60 s client
# timeouts, a dead mirror, and the old "3 failed states -> stop" rule).
import requests as _rq  # noqa: E402
TO = _rq.exceptions.ReadTimeout("read timed out")
q = cs.overpass_query("AL")
check("osm query: [timeout:] and [maxsize:] set, client waits just past the server",
      f"[timeout:{cs.OSM_SERVER_TIMEOUT}]" in q and f"[maxsize:{cs.OSM_MAXSIZE}]" in q
      and cs.OSM_SERVER_TIMEOUT < cs.OSM_TIMEOUT <= cs.OSM_SERVER_TIMEOUT + 60, q[:80])
nf = f'["name"~"{cs.OSM_NAME_RE}",i]'
clauses = [c for c in q.split("(area.s);") if 'nwr["' in c]
check("osm query: every union clause carries the name filter, no collect-then-filter step",
      len(clauses) == len(cs.OSM_TAG_CLAUSES)
      and all(f'nwr["{kk}"="{vv}"]{nf}(area.s);' in q for kk, vv in cs.OSM_TAG_CLAUSES)
      and all(nf in c for c in clauses) and "->.t" not in q and ".t[" not in q
      and q.endswith(");out center tags qt;"), q)
# The exact 2026-11-03/04 failure: every server fails the first states. The
# pass must stop after OSM_DROP_SERVER_AFTER states (bounded cost) and leave
# all of them pending for the next run, not burn the budget.
plan = {}
for st in ("AL", "AK", "AZ", "AR", "CA"):
    plan[(m, st)] = FakeResp(502)
    plan[(k, st)] = TO
    plan[(pc, st)] = _rq.exceptions.ConnectionError("refused")
rep = {}
fo3 = FakeOverpass(plan)
got3, err3 = cs.fetch_osm(fo3, states=("AL", "AK", "AZ", "AR", "CA"), pause=0, report=rep, sleep=nosleep)
check("osm: all servers failing -> pass stops after 3 states, all 5 pending, no retry pass",
      got3 == [] and len(fo3.calls) == 3 * len(cs.OVERPASS_URLS) and rep["pending"] == ["AL", "AK", "AZ", "AR", "CA"],
      f"{len(fo3.calls)} {rep}")
check("osm: every request uses the short connect / bounded read timeout",
      set(fo3.timeouts) == {(cs.OSM_CONNECT_TIMEOUT, cs.OSM_TIMEOUT)} and cs.OSM_TIMEOUT > cs.OSM_SERVER_TIMEOUT,
      str(set(fo3.timeouts)))
# A state that fails while others answer is retried at the end and recovered.
slept.clear()
fo3b = FakeOverpass({(m, "AL"): [FakeResp(502), FakeResp(200, el)], (k, "AL"): FakeResp(504), (pc, "AL"): TO,
                     (m, "AK"): FakeResp(200, el), (m, "AZ"): FakeResp(200, el)})
rep3b = {}
got3b, err3b = cs.fetch_osm(fo3b, states=("AL", "AK", "AZ"), pause=0, report=rep3b, sleep=nosleep)
check("osm: failed state retried after the others and recovered",
      sorted(c.state for c in got3b) == ["AK", "AL", "AZ"] and rep3b["pending"] == [] and err3b == ""
      and [st for _, st in fo3b.calls][-1] == "AL", f"{err3b} {fo3b.calls}")
check("osm: 502/504 move to the next server at once (no backoff sleep)", slept == [], str(slept))
# 429 then 200 on the same server: backoff, no mirror needed.
slept.clear()
fo4 = FakeOverpass({(m, "NE"): [FakeResp(429), FakeResp(200, el)]})
got4, err4 = cs.fetch_osm(fo4, states=("NE",), pause=0, sleep=nosleep)
check("osm: 429 backs off and retries the same server", len(got4) == 1 and fo4.calls == [(m, "NE"), (m, "NE")]
      and cs.OSM_BACKOFF[0] in slept, f"{fo4.calls} {slept}")
fo4b = FakeOverpass({(m, "NE"): FakeResp(429), (k, "NE"): FakeResp(200, el)})
got4b, _ = cs.fetch_osm(fo4b, states=("NE",), pause=0, sleep=nosleep)
check("osm: 429 twice -> next server", len(got4b) == 1 and fo4b.calls == [(m, "NE"), (m, "NE"), (k, "NE")], str(fo4b.calls))
# /api/status says wait: the client waits before posting (capped).
slept.clear()
fo5 = FakeOverpass({(m, "NE"): FakeResp(200, el)},
                   status={m: "Rate limit: 2\nSlot available after: 2026-11-04T15:00:12Z, in 12 seconds.\n"
                              "Slot available after: 2026-11-04T15:00:40Z, in 40 seconds.\n"})
cs.fetch_osm(fo5, states=("NE",), pause=0, sleep=nosleep)
check("osm: waits for the slot /api/status announces", slept[:1] == [12.0], str(slept))
slept.clear()
fo5b = FakeOverpass({(m, "NE"): FakeResp(200, el)}, status={m: "Rate limit: 2\n2 slots available now.\n"})
cs.fetch_osm(fo5b, states=("NE",), pause=0, sleep=nosleep)
check("osm: no wait when a slot is free", slept == [], str(slept))
# 200 with a runtime-error remark is a failure, not an empty state.
bad = {"elements": [], "remark": "runtime error: Query timed out in \"query\" at line 1 after 181 seconds."}
fo6 = FakeOverpass({(m, "TX"): FakeResp(200, bad), (k, "TX"): FakeResp(200, el)})
got6, err6 = cs.fetch_osm(fo6, states=("TX",), pause=0, sleep=nosleep)
check("osm: runtime-error remark falls through to the mirror", len(got6) == 1 and (k, "TX") in fo6.calls, f"{fo6.calls}")
# Everything down: stops once all servers are dropped, names the rest pending.
rep7 = {}
fo7 = FakeOverpass({(u, st): _rq.exceptions.ConnectionError("refused") for u in cs.OVERPASS_URLS for st in cs.US_STATES})
got7, err7 = cs.fetch_osm(fo7, states=cs.US_STATES, pause=0, report=rep7, sleep=nosleep)
check("osm: all servers refusing -> stops early, every state pending",
      got7 == [] and len(fo7.calls) == len(cs.OVERPASS_URLS) * cs.OSM_DROP_SERVER_AFTER
      and sorted(rep7["pending"]) == sorted(cs.US_STATES), f"{len(fo7.calls)} {len(rep7['pending'])}")
# Deadline mid-run: covered states are not pending, the rest are.
t = [0.0]
def clk():
    return t[0]
class SlowOverpass(FakeOverpass):
    def post(self, *a, **kw):
        t[0] += 100
        return super().post(*a, **kw)
rep8 = {}
fo8 = SlowOverpass({(m, st): FakeResp(200, el) for st in ("NE", "IA", "KS")})
got8, err8 = cs.fetch_osm(fo8, states=("NE", "IA", "KS"), pause=0, deadline=150, report=rep8, clock=clk, sleep=nosleep)
check("osm: deadline -> covered states kept, rest pending", len(got8) == 2 and rep8["pending"] == ["KS"]
      and "not queried: KS" in err8, f"{err8} {rep8}")
# Next run asks the pending states first.
import tempfile, json as _json  # noqa: E402,E401
with tempfile.TemporaryDirectory() as td:
    pj = Path(td) / "sweep.json"
    pj.write_text(_json.dumps({"osm_pending": ["TX", "CA", "ZZ"]}))
    order = cs.osm_state_order(pj)
    check("osm: last run's pending states go first, nothing lost",
          order[:2] == ["TX", "CA"] and sorted(order) == sorted(cs.US_STATES), str(order[:4]))
    check("osm: no previous report -> plain order", cs.osm_state_order(Path(td) / "none.json") == list(cs.US_STATES))


def boom(_):
    raise RuntimeError("needs cryptography")
out2, _, notes2 = cs.run(None, known=known, site=FakeSite({}), osm_fetch=lambda s: ([], ""), ario_fetch=boom)
check("run: a source that raises becomes a note", out2 == [] and any("needs cryptography" in n for n in notes2), str(notes2))
md = cs.render_md(out, skipped, notes, "2026-11-02T00:00:00Z")
check("report: tier A table lists the PT1 yard", "## A." in md and "New U-Pull" in md and "gm_vehicle_search" in md)

# --osm-pending: merge one OSM-only pass into the last full report.
prev = {"at": "2026-11-04T15:42:08Z", "skipped": {"tracked": 76},
        "notes": ["OpenStreetMap: Overpass failed for AL, AK, AZ; not queried: CO, TX.", "Website checks capped at 400."],
        "osm_pending": ["AL", "AK", "TX"],
        "candidates": [{"name": "Old Ario Yard", "source": "ario", "tier": "E", "lat": 1.0, "lng": 2.0},
                       {"name": "Dup U-Pull", "source": "osm", "tier": "E", "lat": 30.0, "lng": -97.0, "state": "TX"}]}
newc = [cs.Candidate(name="Dup U-Pull", lat=30.001, lng=-97.0, source="osm", tier="A", state="TX"),
        cs.Candidate(name="Fresh U-Pull", lat=33.0, lng=-86.0, source="osm", tier="B", state="AL")]
mc, msk, mnotes, doc = cs.merge_report(prev, newc, {"tracked": 3}, ["OpenStreetMap: Overpass failed for AK."],
                                       ["AK"], "2026-11-05T00:00:00Z")
check("merge: old rows kept, re-found yard replaced, new yard added",
      sorted((c.name, c.tier) for c in mc) == [("Dup U-Pull", "A"), ("Fresh U-Pull", "B"), ("Old Ario Yard", "E")],
      str([(c.name, c.tier) for c in mc]))
check("merge: skip counts add, pending shrinks, old OSM note replaced",
      msk == {"tracked": 79} and doc["osm_pending"] == ["AK"]
      and not any("AL, AK, AZ" in n for n in mnotes) and any("2 pending state(s) covered, 1 still pending" in n for n in mnotes)
      and "Website checks capped at 400." in mnotes, f"{msk} {mnotes}")
import contextlib, io  # noqa: E402,E401
with tempfile.TemporaryDirectory() as td:
    saved = (cs.OUT_MD, cs.OUT_JSON)
    cs.OUT_MD, cs.OUT_JSON = Path(td) / "s.md", Path(td) / "s.json"
    cs.OUT_JSON.write_text(_json.dumps({"osm_pending": []}))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cs.main(["--osm-pending"])
    check("--osm-pending with nothing pending: exits 0, writes nothing",
          rc == 0 and "nothing to do" in buf.getvalue() and not cs.OUT_MD.exists(), buf.getvalue())
    # pending AL: a fake fetch covers it, the report is merged
    cs.OUT_JSON.write_text(_json.dumps(prev))
    real = cs.fetch_osm
    def fake_fetch(session, states=(), report=None, deadline=None, **kw):
        report["pending"] = [s for s in states if s != "AL"]
        return [cs.Candidate(name="Fresh U-Pull", lat=33.0, lng=-86.0, source="osm", tier="E", state="AL",
                             extra={"note": "no site"})], ""
    cs.fetch_osm = fake_fetch
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = cs.main(["--osm-pending", "--max-sites", "0", "--budget-min", "1"])
    finally:
        cs.fetch_osm = real
    d2 = _json.loads(cs.OUT_JSON.read_text())
    check("--osm-pending: queries only pending states, merges, shrinks osm_pending",
          rc2 == 0 and d2["osm_pending"] == ["AK", "TX"] and {c["name"] for c in d2["candidates"]} >= {"Old Ario Yard", "Fresh U-Pull"},
          f"{d2['osm_pending']} {[c['name'] for c in d2['candidates']]}")
    cs.OUT_MD, cs.OUT_JSON = saved

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
