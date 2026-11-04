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
        bb = tuple(float(x) for x in data["data"].split("[bbox:")[1].split("]")[0].split(","))
        st = next(k for k in cs.US_STATES if bb in cs.state_tiles(k))
        self.calls.append((url, st))
        self.timeouts.append(timeout)
        r = self.plan.get((url, st), FakeResp(504))
        if isinstance(r, list):
            r = r.pop(0) if len(r) > 1 else r[0]
        if isinstance(r, Exception):
            raise r
        if r.status_code == 200 and r._p is el:  # one yard per state, the same OSM id in every tile
            s_, w, n, e = cs.STATE_BBOX[st]
            return FakeResp(200, {"elements": [{"type": "node", "id": cs.US_STATES.index(st) + 1,
                                                "lat": (s_ + n) / 2, "lon": (w + e) / 2,
                                                "tags": {"name": "U-Pull-It", "addr:state": st}}]})
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
q = cs.overpass_query(cs.state_tiles("AL")[0])
check("osm query: [timeout:] and [maxsize:] set, client waits just past the server",
      f"[timeout:{cs.OSM_SERVER_TIMEOUT}]" in q and f"[maxsize:{cs.OSM_MAXSIZE}]" in q
      and cs.OSM_SERVER_TIMEOUT < cs.OSM_TIMEOUT <= cs.OSM_SERVER_TIMEOUT + 60, q[:80])
nf = f'["name"~"{cs.OSM_NAME_RE}",i]'
clauses = [c for c in q.split(";(")[1].split(");out")[0].split(f"{nf};") if c]
check("osm query: every union clause carries the name filter, no collect-then-filter step",
      len(clauses) == len(cs.OSM_TAG_CLAUSES)
      and all(f'nwr["{kk}"="{vv}"]{nf};' in q for kk, vv in cs.OSM_TAG_CLAUSES)
      and "->.t" not in q and ".t[" not in q and q.endswith(");out center tags qt;"), q)
check("osm query: bbox tiles, no area lookup", "[bbox:" in q and "area[" not in q and "ISO3166" not in q, q[:120])
# State bbox table + tiling.
check("bbox: all 50 states, sane extents", sorted(cs.STATE_BBOX) == sorted(cs.US_STATES)
      and all(-180 <= w < e <= -60 and 18 <= s_ < n <= 72 for s_, w, n, e in cs.STATE_BBOX.values()),
      str([k for k, (s_, w, n, e) in cs.STATE_BBOX.items() if not (w < e)]))
check("bbox: spot checks vs Census extents (RI, TX, AK clipped at the antimeridian)",
      cs.STATE_BBOX["RI"] == (41.146, -71.863, 42.019, -71.121) and cs.STATE_BBOX["TX"][0] == 25.84
      and cs.STATE_BBOX["AK"][1] == -179.2 and cs.STATE_BBOX["AK"][3] < -129)
def _union_ok(st):
    s_, w, n, e = cs.STATE_BBOX[st]
    ts = cs.state_tiles(st)
    lim = cs.OSM_TILE_DEG_BY_STATE.get(st, cs.OSM_TILE_DEG) + 1e-6
    return (all(t[2] - t[0] <= lim and t[3] - t[1] <= lim for t in ts)
            and min(t[0] for t in ts) == s_ and min(t[1] for t in ts) == w
            and abs(max(t[2] for t in ts) - n) < 1e-3 and abs(max(t[3] for t in ts) - e) < 1e-3
            and abs(sum((t[2] - t[0]) * (t[3] - t[1]) for t in ts) - (n - s_) * (e - w)) < 1e-2)
check("tiles: every state's tiles cover its bbox exactly, none larger than the tile size",
      all(_union_ok(st) for st in cs.US_STATES), str([st for st in cs.US_STATES if not _union_ok(st)]))
check("tiles: small states are one tile, TX/AK split, total stays modest",
      len(cs.state_tiles("RI")) == 1 and len(cs.state_tiles("TX")) > 1 and len(cs.state_tiles("AK")) <= 24
      and sum(len(cs.state_tiles(st)) for st in cs.US_STATES) <= 200,
      str(sum(len(cs.state_tiles(st)) for st in cs.US_STATES)))
# Results: de-dupe across tiles/states by OSM id; addr:state decides; border overlap -> no guess.
class TileOverpass(FakeOverpass):
    def __init__(self, elements):
        super().__init__({})
        self.elements = elements
    def post(self, url, data=None, timeout=None, headers=None):
        self.calls.append((url, data["data"]))
        return FakeResp(200, {"elements": self.elements})
els = [{"type": "way", "id": 7, "center": {"lat": 29.5, "lon": -98.5}, "tags": {"name": "Big U-Pull", "addr:state": "TX"}},
       {"type": "node", "id": 8, "lat": 33.01, "lon": -94.0, "tags": {"name": "Border U-Pull"}},  # TX/AR/LA bboxes overlap
       {"type": "node", "id": 9, "lat": 35.0, "lon": -92.0, "tags": {"name": "Arkansas U-Pull", "addr:state": "Arkansas"}}]
to = TileOverpass(els)
gt, _ = cs.fetch_osm(to, states=("TX", "AR"), pause=0, sleep=nosleep)
names = sorted((c.name, c.state) for c in gt)
check("tiles: each OSM element kept once across all tiles and states",
      len(gt) == 3 and len({c.extra["osm"] for c in gt}) == 3, str(names))
check("tiles: addr:state (code or full name) decides the state; border overlap leaves it blank",
      ("Big U-Pull", "TX") in names and ("Arkansas U-Pull", "AR") in names and ("Border U-Pull", "") in names, str(names))
check("tiles: one request per tile", len(to.calls) == len(cs.state_tiles("TX")) + len(cs.state_tiles("AR")), str(len(to.calls)))
# Diagnostics: per server, status + tiny query; never raises.
class DiagFake:
    def get(self, url, timeout=None, headers=None):
        if "kumi" in url:
            raise _rq.exceptions.ConnectTimeout("x")
        return FakeResp(200, text="Connected as: 1\nRate limit: 2\n2 slots available now.\n")
    def post(self, url, data=None, timeout=None, headers=None):
        if "private" in url:
            return FakeResp(502, text="<html>502 Bad Gateway</html>")
        return FakeResp(200, {"elements": [{"type": "node", "id": 1}]})
import contextlib, io  # noqa: E402,E401
with contextlib.redirect_stdout(io.StringIO()) as dbuf:
    drows = cs.diagnose(DiagFake())
check("diagnose: one row per server with status + query code and time",
      [r["server"] for r in drows] == [cs.urlparse(u).netloc for u in cs.OVERPASS_URLS]
      and drows[0]["status"]["code"] == 200 and "1 element" in drows[0]["query"]["detail"]
      and drows[1]["status"]["code"] == 0 and drows[1]["status"]["detail"] == "ConnectTimeout"
      and drows[2]["query"]["code"] == 502 and "diag overpass-api.de" in dbuf.getvalue(), str(drows))
check("diagnose: the tiny query is a bbox query, not an area lookup", "area[" not in cs.DIAG_QUERY and "](61.0," in cs.DIAG_QUERY)
_real_session = cs.requests.Session
class _BoomSession:
    def get(self, *a, **k):
        raise RuntimeError("no network")
    post = get
cs.requests.Session = _BoomSession
try:
    with contextlib.redirect_stdout(io.StringIO()) as dbuf2:
        rc_d = cs.main(["--diagnose"])
finally:
    cs.requests.Session = _real_session
check("--diagnose: exits 0 even when every call raises, logs each server",
      rc_d == 0 and dbuf2.getvalue().count("diag ") == len(cs.OVERPASS_URLS) and "RuntimeError" in dbuf2.getvalue(),
      dbuf2.getvalue())
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
check("osm: all servers failing -> pass stops after 3 states; unqueried first, failed last in pending",
      got3 == [] and len(fo3.calls) == 3 * len(cs.OVERPASS_URLS) and rep["pending"] == ["AR", "CA", "AL", "AK", "AZ"],
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
fo4 = FakeOverpass({(m, "RI"): [FakeResp(429), FakeResp(200, el)]})
got4, err4 = cs.fetch_osm(fo4, states=("RI",), pause=0, sleep=nosleep)
check("osm: 429 backs off and retries the same server", len(got4) == 1 and fo4.calls == [(m, "RI"), (m, "RI")]
      and cs.OSM_BACKOFF[0] in slept, f"{fo4.calls} {slept}")
fo4b = FakeOverpass({(m, "RI"): FakeResp(429), (k, "RI"): FakeResp(200, el)})
got4b, _ = cs.fetch_osm(fo4b, states=("RI",), pause=0, sleep=nosleep)
check("osm: 429 twice -> next server", len(got4b) == 1 and fo4b.calls == [(m, "RI"), (m, "RI"), (k, "RI")], str(fo4b.calls))
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
fo8 = SlowOverpass({(m, st): FakeResp(200, el) for st in ("RI", "CT", "DE")})
got8, err8 = cs.fetch_osm(fo8, states=("RI", "CT", "DE"), pause=0, deadline=150, report=rep8, clock=clk, sleep=nosleep)
check("osm: deadline -> covered states kept, rest pending", len(got8) == 2 and rep8["pending"] == ["DE"]
      and "not queried: DE" in err8, f"{err8} {rep8}")
# A multi-tile state cut off mid-way by the deadline stays pending (partial).
t[0] = 0.0
rep8b = {}
fo8b = SlowOverpass({(m, "TX"): FakeResp(200, el)})
cs.fetch_osm(fo8b, states=("TX",), pause=0, deadline=150, report=rep8b, clock=clk, sleep=nosleep)
check("osm: state cut off between tiles stays pending", rep8b["pending"] == ["TX"] and rep8b["covered"] == [], str(rep8b))
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
    real = cs.fetch_osm_geofabrik
    def fake_fetch(session, states=(), report=None, deadline=None, **kw):
        report["pending"] = [s for s in states if s != "AL"]
        return [cs.Candidate(name="Fresh U-Pull", lat=33.0, lng=-86.0, source="osm", tier="E", state="AL",
                             extra={"note": "no site"})], ""
    cs.fetch_osm_geofabrik = fake_fetch
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = cs.main(["--osm-pending", "--max-sites", "0", "--budget-min", "1"])
    finally:
        cs.fetch_osm_geofabrik = real
    d2 = _json.loads(cs.OUT_JSON.read_text())
    check("--osm-pending: queries only pending states, merges, shrinks osm_pending",
          rc2 == 0 and d2["osm_pending"] == ["AK", "TX"] and {c["name"] for c in d2["candidates"]} >= {"Old Ario Yard", "Fresh U-Pull"},
          f"{d2['osm_pending']} {[c['name'] for c in d2['candidates']]}")
    cs.OUT_MD, cs.OUT_JSON = saved

# Workflow: the weekly cron must be the one that switches on --osm-pending.
import re as _re  # noqa: E402
wf = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "coverage-sweep.yml").read_text()
crons = _re.findall(r'cron: "([^"]+)"', wf)
weekly = [c for c in crons if c.split()[2] == "*" and c.split()[4] != "*"]
check("workflow: one weekly cron, and the Sweep step maps exactly it to --osm-pending",
      len(weekly) == 1 and f"github.event.schedule == '{weekly[0]}') && '--osm-pending'" in wf
      and any(c.split()[2] != "*" for c in crons), str(crons))

# --- Geofabrik + osmium (default OSM source since 2026-11-04) ---------------
RS = "\x1e"
FIXTURE = "\n".join([
    RS + _json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [-86.8, 33.5]},
                      "properties": {"@type": "node", "@id": 11, "name": "Bham U-Pull-It", "shop": "car_parts",
                                     "website": "bhamupull.example"}}),
    RS + _json.dumps({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[-87.0, 32.0], [-86.0, 32.0],
                                                                                         [-86.0, 33.0], [-87.0, 33.0]]]},
                      "properties": {"@type": "way", "@id": 22, "name": "Pick-A-Part South", "landuse": "industrial",
                                     "addr:state": "AL"}}),
    RS + _json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [-85.0, 31.0]},
                      "properties": {"@type": "node", "@id": 33, "name": "Joe's Tire Shop", "shop": "car_repair"}}),
    RS + _json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [-84.9, 32.4]},
                      "properties": {"@type": "node", "@id": 44, "name": "Columbus U-Pull", "shop": "car_parts",
                                     "addr:state": "Georgia"}}),
    "not json",
])
pc0 = cs.parse_osmium_geojsonseq(FIXTURE)
check("geofabrik parse: name filter, centroids, ids, website, addr:state",
      [(c.name, c.extra["osm"], c.state) for c in pc0] == [("Bham U-Pull-It", "node/11", ""), ("Pick-A-Part South", "way/22", "AL"),
                                                          ("Columbus U-Pull", "node/44", "GA")]
      and (pc0[0].lat, pc0[0].lng) == (33.5, -86.8) and (pc0[1].lat, pc0[1].lng) == (32.5, -86.5)
      and pc0[0].website == "http://bhamupull.example", str([(c.name, c.lat, c.lng, c.state) for c in pc0]))
check("geofabrik: osmium filter mirrors OSM_TAG_CLAUSES",
      sorted(f"{k}={v}" for a in cs.osmium_filter_args() for k, vs in [a[4:].split("=")] for v in vs.split(","))
      == sorted(f"{k}={v}" for k, v in cs.OSM_TAG_CLAUSES) and all(a.startswith("nwr/") for a in cs.osmium_filter_args()))
check("geofabrik: slugs match the index page form", cs.geofabrik_slug("NY") == "new-york" and cs.geofabrik_slug("WV") == "west-virginia"
      and cs.GEOFABRIK_URL.format(slug="georgia") == "https://download.geofabrik.de/north-america/us/georgia-latest.osm.pbf")


class StreamResp:
    def __init__(self, status, body=b"", length=None):
        self.status_code, self.body = status, body
        self.headers = {"Content-Length": str(len(body) if length is None else length)}
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def iter_content(self, chunk_size=1):
        for i in range(0, len(self.body), 4):
            yield self.body[i:i + 4]


class GeoSession:
    def __init__(self, plan):
        self.plan, self.gets = plan, []
    def get(self, url, stream=False, timeout=None, headers=None):
        self.gets.append((url, headers.get("User-Agent")))
        r = self.plan.get(url.split("/us/")[1].split("-latest")[0], StreamResp(404))
        if isinstance(r, list):
            r = r.pop(0) if len(r) > 1 else r[0]
        if isinstance(r, Exception):
            raise r
        return r


class FakeOsmium:
    """Plays osmium: tags-filter writes a marker file, export writes the
    fixture for whichever state's pbf it was given."""
    def __init__(self, per_slug, fail_slug=None):
        self.per_slug, self.fail_slug, self.calls, self.present = per_slug, fail_slug, [], []
    def __call__(self, cmd, capture_output=True, text=True, timeout=None):
        self.calls.append(cmd[:2])
        class R:
            returncode, stderr = 0, ""
        work = Path(cmd[cmd.index("-o") + 1]).parent
        self.present.append(sorted(p.name for p in work.iterdir()))
        if cmd[1] == "tags-filter":
            slug = Path(cmd[2]).name.split(".osm.pbf")[0]
            if slug == self.fail_slug:
                R.returncode, R.stderr = 1, "Error: corrupt pbf"
                return R()
            Path(cmd[cmd.index("-o") + 1]).write_text(slug)
        else:
            slug = Path(cmd[2]).read_text()
            Path(cmd[cmd.index("-o") + 1]).write_text(self.per_slug.get(slug, ""))
        return R()


with tempfile.TemporaryDirectory() as td:
    wd = Path(td)
    gs = GeoSession({"alabama": StreamResp(200, b"PBFDATA-AL"), "georgia": StreamResp(200, b"PBFDATA-GA"),
                     "alaska": [StreamResp(503), StreamResp(200, b"PBFDATA-AK")], "arizona": StreamResp(200, b"PBF")})
    osm_fake = FakeOsmium({"alabama": FIXTURE, "georgia": FIXTURE, "alaska": ""}, fail_slug="arizona")
    slept.clear()
    repg = {}
    with contextlib.redirect_stdout(io.StringIO()) as gbuf:
        gg, gerr = cs.fetch_osm_geofabrik(gs, states=("AL", "GA", "AK", "AZ"), pause=0, report=repg,
                                          sleep=nosleep, run=osm_fake, workdir=wd)
    check("geofabrik: one sequential download per state, honest UA, 503 retried once after a pause",
          [u.split("/us/")[1] for u, _ in gs.gets] == ["alabama-latest.osm.pbf", "georgia-latest.osm.pbf", "alaska-latest.osm.pbf",
                                                        "alaska-latest.osm.pbf", "arizona-latest.osm.pbf"]
          and {ua for _, ua in gs.gets} == {cs.UA} and cs.GEOFABRIK_RETRY_SLEEP in slept, str(gs.gets))
    check("geofabrik: rows kept once across states; addr:state decides (Columbus -> GA, not AL)",
          sorted((c.name, c.state) for c in gg) == [("Bham U-Pull-It", "AL"), ("Columbus U-Pull", "GA"), ("Pick-A-Part South", "AL")],
          str([(c.name, c.state) for c in gg]))
    check("geofabrik: osmium failure -> state failed (last in pending), others covered",
          repg["pending"] == ["AZ"] and repg["covered"] == ["AL", "GA", "AK"] and "Geofabrik/osmium failed for AZ" in gerr,
          f"{repg} {gerr}")
    check("geofabrik: each state's pbf deleted before the next download; workdir empty at the end",
          all(sum(1 for n in names if n.endswith("-latest.osm.pbf") or (n.endswith(".osm.pbf") and n != "filtered.osm.pbf")) <= 1
              for names in osm_fake.present) and list(wd.iterdir()) == [], f"{osm_fake.present} {list(wd.iterdir())}")
    # disk guard: Content-Length larger than free space / headroom -> refused before writing
    big = StreamResp(200, b"x", length=10 ** 15)
    repd = {}
    with contextlib.redirect_stdout(io.StringIO()):
        gd, gderr = cs.fetch_osm_geofabrik(GeoSession({"california": big}), states=("CA",), pause=0, report=repd,
                                           sleep=nosleep, run=FakeOsmium({}), workdir=wd)
    check("geofabrik: refuses a download the runner disk can't hold", gd == [] and repd["pending"] == ["CA"]
          and list(wd.iterdir()) == [], gderr)
    # short read is a failure, not a silent partial file
    with contextlib.redirect_stdout(io.StringIO()) as sbuf:
        cs.fetch_osm_geofabrik(GeoSession({"texas": StreamResp(200, b"abc", length=10)}), states=("TX",), pause=0,
                               sleep=nosleep, run=FakeOsmium({}), workdir=wd)
    check("geofabrik: short read fails the state", "short read" in sbuf.getvalue(), sbuf.getvalue())
    # transient download errors: one retry after a pause, partial file removed
    class HalfStream(StreamResp):
        def iter_content(self, chunk_size=1):
            yield b"PART"
            raise _rq.exceptions.ReadTimeout("read timed out")
    slept.clear()
    gs_r = GeoSession({"washington": [HalfStream(200, b"PARTIAL-PBF"), StreamResp(200, b"PBFDATA-WA")],
                       "alabama": [_rq.exceptions.ConnectionError("reset"), _rq.exceptions.ReadTimeout("x")]})
    rep_r = {}
    with contextlib.redirect_stdout(io.StringIO()) as rbuf:
        cs.fetch_osm_geofabrik(gs_r, states=("WA", "AL"), pause=0, report=rep_r, sleep=nosleep,
                               run=FakeOsmium({"washington": ""}), workdir=wd)
    check("geofabrik: read timeout mid-download -> partial removed, one retry succeeds",
          rep_r["covered"] == ["WA"] and slept.count(cs.GEOFABRIK_RETRY_SLEEP) == 2
          and [u.split("/us/")[1] for u, _ in gs_r.gets].count("washington-latest.osm.pbf") == 2, f"{rep_r} {slept}")
    check("geofabrik: two transient failures -> state failed (pending), named in the log",
          rep_r["pending"] == ["AL"] and "after one retry" in rbuf.getvalue() and list(wd.iterdir()) == [],
          f"{rep_r} {rbuf.getvalue()}")
    # osmium missing: stop at once, everything pending
    def no_osmium(*a, **k):
        raise FileNotFoundError("osmium")
    repn = {}
    with contextlib.redirect_stdout(io.StringIO()):
        cs.fetch_osm_geofabrik(GeoSession({s_: StreamResp(200, b"p") for s_ in ("alabama", "alaska")}), states=("AL", "AK", "AZ"),
                               pause=0, report=repn, sleep=nosleep, run=no_osmium, workdir=wd)
    check("geofabrik: osmium-tool missing -> stop, all states pending", sorted(repn["pending"]) == ["AK", "AL", "AZ"], str(repn))
    # deadline
    tg = [0.0]
    class SlowGeo(GeoSession):
        def get(self, *a, **k):
            tg[0] += 100
            return super().get(*a, **k)
    repdl = {}
    with contextlib.redirect_stdout(io.StringIO()):
        cs.fetch_osm_geofabrik(SlowGeo({"rhode-island": StreamResp(200, b"p"), "delaware": StreamResp(200, b"p")}),
                               states=("RI", "DE", "CT"), pause=0, deadline=150, report=repdl, clock=lambda: tg[0],
                               sleep=nosleep, run=FakeOsmium({}), workdir=wd)
    check("geofabrik: deadline -> remaining states pending", repdl["pending"] == ["CT"] and repdl["covered"] == ["RI", "DE"], str(repdl))
check("main: geofabrik is the default OSM source", cs._osm_fn("geofabrik") is cs.fetch_osm_geofabrik
      and cs._osm_fn("overpass") is cs.fetch_osm)
_osmium = cs.shutil.which("osmium")
TINY_OSM = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="test">
  <!-- sorted like a Geofabrik extract: nodes by id, then ways -->
  <node id="1" version="1" lat="33.50" lon="-86.80"><tag k="shop" v="car_parts"/><tag k="name" v="Bham U-Pull-It"/></node>
  <node id="2" version="1" lat="32.0" lon="-87.0"/>
  <node id="3" version="1" lat="32.0" lon="-86.0"/>
  <node id="4" version="1" lat="33.0" lon="-86.0"/>
  <node id="5" version="1" lat="33.0" lon="-87.0"/>
  <node id="6" version="1" lat="31.0" lon="-85.0"><tag k="shop" v="car_repair"/><tag k="name" v="Joe's Tire Shop"/></node>
  <node id="7" version="1" lat="31.5" lon="-85.5"><tag k="amenity" v="cafe"/><tag k="name" v="U-Pull Cafe"/></node>
  <way id="10" version="1"><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="5"/><nd ref="2"/>
    <tag k="landuse" v="industrial"/><tag k="name" v="Pick-A-Part South"/></way>
</osm>
"""
if _osmium:
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td)
        (wd / "tiny.osm").write_text(TINY_OSM)
        cs.subprocess.run(["osmium", "cat", str(wd / "tiny.osm"), "-o", str(wd / "tiny.osm.pbf")], check=True,
                          capture_output=True)
        real_rows, real_err = cs._osmium_extract(wd / "tiny.osm.pbf", wd)
        check("real osmium: tags-filter + export + name filter -> two yards, once each (osmium emits a closed way twice)",
              real_err == "" and sorted((c.name, c.extra["osm"]) for c in real_rows)
              == [("Bham U-Pull-It", "node/1"), ("Pick-A-Part South", "way/10")]
              and [(c.lat, c.lng) for c in real_rows if c.name.startswith("Pick")] == [(32.5, -86.5)],
              f"{real_err} {[(c.name, c.extra, c.lat, c.lng) for c in real_rows]}")
        check("real osmium: intermediate files removed", sorted(p.name for p in wd.iterdir()) == ["tiny.osm", "tiny.osm.pbf"],
              str(list(wd.iterdir())))
else:
    print("INFO  real osmium-tool not installed here; CI installs it via apt (real-osmium test skipped)")

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
