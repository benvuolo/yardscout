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
for n in ("Smith Farm U-Pick Strawberries", "Pick-A-Peck Orchard", "U-Pick Blueberries", "Pick N Pull Pumpkins"):
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
md = cs.render_md(out, skipped, notes, "2026-11-02T00:00:00Z")
check("report: tier A table lists the PT1 yard", "## A." in md and "New U-Pull" in md and "gm_vehicle_search" in md)

print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}"))
sys.exit(1 if failures else 0)
