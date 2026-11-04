#!/usr/bin/env python3
"""Coverage sweep: find self-service yards we don't track yet, ranked by how
cheap they are to add.

Read-only. Writes a report (scraper/coverage_sweep.md + .json) and never
touches the scan config — adding a yard stays a reviewed change.

Where candidates come from
  1. OpenStreetMap (Overpass API): every US place whose name looks like a
     self-service yard ("U-Pull-It", "Pick-A-Part", "Pull-N-Save", "self
     serve auto"...), with its website tag when mapped. Pick-your-own farms
     and the like are filtered out.
  2. Ario (autorecycler.io): the platform's own yard table. An org that is
     live on Ario's backend and not in ARIO_CHAINS is a near-free add.

What it skips
  - Yards within MATCH_KM of a tracked yard (docs/data/junkyards.json).
  - Yards the registry (independent_yards_registry.json) already has as
    built / candidate / blocked / retired / directory-only — listed with
    that status instead of re-checked.

How it checks a website (politely, as YardScout)
  - robots.txt first; a disallow is respected and reported.
  - One homepage GET, plus at most one same-site "inventory" page.
  - User agent "YardScout/1.12 (+https://yardscout.io)", SITE_DELAY_SEC
    between requests, short timeouts.
  - A 403/429 or a bot-check page is reported as "ask the yard". The sweep
    never tries to get past one.

Tiers in the report
  A  runs a platform our scraper already parses (Ario, VinPlus/YardSmart,
     yardconnect-pro, CRUSH/S3, iis-pro-upull, gm_vehicle_search, Wrench-A-Part)
  B  has its own online vehicle inventory (custom adapter needed)
  C  blocked us or robots.txt says no (outreach)
  D  site found, no online inventory (directory-only)
  E  no website on the map, or unreachable

Run
  python scraper/coverage_sweep.py                    # full sweep
  python scraper/coverage_sweep.py --no-osm           # Ario only
  python scraper/coverage_sweep.py --max-sites 50     # cap website checks
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

try:
    import requests
except ImportError:  # pragma: no cover - CI installs it
    requests = None

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent
TRACKED_PATH = REPO / "docs" / "data" / "junkyards.json"
REGISTRY_PATH = SCRIPT_DIR / "independent_yards_registry.json"
OUT_MD = SCRIPT_DIR / "coverage_sweep.md"
OUT_JSON = SCRIPT_DIR / "coverage_sweep.json"

UA = "YardScout/1.12 (+https://yardscout.io)"
SITE_DELAY_SEC = 1.5
TIMEOUT = 20
MATCH_KM = 3.0
# Overpass. 2026-11-03: every state lost (60 s client timeout under a 180 s
# server timeout, a dead mirror, "3 failed states -> stop"). 2026-11-04: with
# long timeouts, the whole-state NAME regex was simply too heavy for the public
# servers (502 / 210 s read timeouts, ~10 min per failed state, 5 states in 70
# min). The query now selects by exact, indexed tags first and only then
# filters names (see OSM_TAG_CLAUSES), and a failing server is skipped fast.
OSM_SERVER_TIMEOUT = 90   # [timeout:] sent to Overpass
OSM_MAXSIZE = 64 * 1024 * 1024  # [maxsize:] — results are tiny; keeps us in the cheap queue
OSM_TIMEOUT = OSM_SERVER_TIMEOUT + 30  # client read timeout: just past the server's own limit
OSM_CONNECT_TIMEOUT = 20  # a host that won't even connect is not worth waiting on
OSM_MAX_SLOT_WAIT = 120   # longest wait for a free slot announced by /api/status
OSM_BACKOFF = (30,)       # same-server retry after 429 (rate limit) only; 5xx moves on at once
OSM_DROP_SERVER_AFTER = 3 # consecutive failures before a server is skipped for the rest of the pass
OSM_SHARE = 0.65          # share of the budget for discovery (Ario + OSM); sites get the rest
OSM_ONLY_SHARE = 0.75     # --osm-pending runs: no Ario, so discovery gets more
ARIO_MIN_ROWS = 50        # an Ario yard counts as live with this many rows...
ARIO_FRESH_DAYS = 30      # ...and a set-out within this many days
US_STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ "
             "NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY").split()
OVERPASS_URLS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                 "https://overpass.private.coffee/api/interpreter")

# ---------------------------------------------------------------- names
# Overpass regex (POSIX ERE, case-insensitive). Broad on purpose; the Python
# filter below drops farms and other "pick your own" places.
OSM_NAME_RE = (
    "(u|you)[- ]?pull|pull[- ]?(a|n|and|&|it|r|your)[- ]?(part|save|pay|parts|own)?"
    "|pick[- ]?(a|n|ur|your|&|and|it)[- ]?(part|pull|pay|parts)"
    "|pi[ck]k?[- ]?a[- ]?part|self[- ]?serv(e|ice)[^;]*(auto|salvage|parts|yard)"
    "|u[- ]?pick[- ]?(it|a|parts)|wrench[- ]?a[- ]?part|tear[- ]?a[- ]?part"
)
# Whole yard phrases on word boundaries: "Casapulla's Subs", "Lilly Pulitzer"
# and "Epic Apartments" all contain an Overpass hit but none of these.
_YARD_PHRASE = re.compile(
    r"\b(u|you)[- ]?pull\b|\bpull[- ]?(a|n|and|&|it|r|your)\b([- ]?(part|parts|save|pay|own)\b)?"
    r"|\bpick[- ]?(a|n|ur|your|&|and|it)[- ]?(part|parts|pull|pay)\b|\bpi[ck]k?[- ]?a[- ]?part\b"
    r"|\bself[- ]?serv(e|ice)\b.*\b(auto|salvage|parts|yard)\b|\bu[- ]?pick[- ]?(it|a|parts)\b"
    r"|\b(wrench|tear)[- ]?a[- ]?part\b",
    re.I)
_NOT_A_YARD = re.compile(
    r"berr|farm|orchard|pumpkin|apple|peach|flower|christmas|tree|fruit|vegetable|garden|vineyard|"
    r"winery|produce|cherr|lavender|tulip|sunflower|grocery|market|pizza|church|school",
    re.I)
_NOT_A_YARD_TAGS = {
    ("landuse", "farmland"), ("landuse", "orchard"), ("landuse", "vineyard"),
    ("shop", "farm"), ("shop", "garden_centre"), ("shop", "greengrocer"), ("amenity", "restaurant"),
}


def looks_like_yard(name: str, tags: dict | None = None) -> bool:
    if not name or _NOT_A_YARD.search(name):
        return False
    tags = tags or {}
    if any((k, tags.get(k)) in _NOT_A_YARD_TAGS for k, _ in _NOT_A_YARD_TAGS):
        return False
    return bool(_YARD_PHRASE.search(name))


# ---------------------------------------------------------------- platforms
# (platform, tier-A?, needles) — searched in lowercase HTML of the homepage and
# the inventory page. Order matters: first hit wins.
FINGERPRINTS: list[tuple[str, bool, tuple[str, ...]]] = [
    ("row52 (out of scope: Pick-n-Pull's platform)", False, ("row52.com",)),
    ("Ario (autorecycler.io)", True, ("autorecycler.io",)),
    ("VinPlus / YardSmart", True, ("vinplus.texnrewards", "texnrewards.net", "yardsmartapp.com")),
    ("yardconnect-pro", True, ("yardconnect-pro", "yardconnectpro")),
    ("CRUSH / S3 Software", True, ("s3softwaresolutions", "/home/getmakes", "/home/inventory")),
    ("iis-pro-upull", True, ("iis-pro-upull",)),
    ("gm_vehicle_search (PT1)", True, ("gm_vehicle_search",)),
    ("Wrench-A-Part API", True, ("wrenchapart",)),
    ("LKQ Pick Your Part (chain we cover)", False, ("pyp.com", "lkqpickyourpart")),
    ("Pull-A-Part (chain we cover)", False, ("pullapart.com",)),
    ("Pick-n-Pull (chain we cover)", False, ("picknpull.com",)),
]
_CHALLENGE = ("cf-chl", "challenge-platform", "just a moment...", "sucuri", "attention required",
              "captcha", "access denied", "request unsuccessful. incapsula", "ddos-guard", "perimeterx")
_INV_LINK = re.compile(r"inventory|vehicle[s]?[- _]?(search|list|in[- ]?stock)?|our[- ]?cars|yard[- ]?search|in[- ]?stock|search[- ]?cars|car[- ]?list", re.I)
_INV_TABLE = re.compile(r"\byear\b.{0,400}\bmake\b.{0,400}\bmodel\b.{0,800}\b(row|stock|location|arrival|date)\b", re.I | re.S)


def fingerprint(html: str) -> tuple[str, bool] | None:
    low = html.lower()
    for name, tier_a, needles in FINGERPRINTS:
        if any(n in low for n in needles):
            return name, tier_a
    return None


def is_challenge(status: int, html: str) -> bool:
    low = html[:20000].lower()
    return status in (403, 429, 503) or (status in (200, 202) and any(c in low for c in _CHALLENGE) and len(low) < 15000)


def inventory_link(base_url: str, html: str) -> str | None:
    """First same-site link that looks like a vehicle inventory page."""
    host = urlparse(base_url).netloc.lower().removeprefix("www.")
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        if not (_INV_LINK.search(href) or _INV_LINK.search(text)):
            continue
        if re.search(r"price|parts?[- ]?list|sell|junk[- ]?car|cash|career|login|cart", href + " " + text, re.I):
            continue
        url = urljoin(base_url, href)
        if urlparse(url).netloc.lower().removeprefix("www.") == host:
            return url
    return None


# ---------------------------------------------------------------- geo + match
def km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


@dataclass
class Known:
    name: str
    city: str
    state: str
    lat: float | None
    lng: float | None
    status: str  # "tracked" or a registry status


def load_known(tracked_path: Path = TRACKED_PATH, registry_path: Path = REGISTRY_PATH) -> list[Known]:
    out: list[Known] = []
    try:
        for y in json.loads(Path(tracked_path).read_text()).get("yards", []):
            # [name, city, state, lat, lng, cars, ...]
            out.append(Known(y[0], y[1], y[2], float(y[3]), float(y[4]), "tracked"))
    except (OSError, ValueError, IndexError, TypeError):
        pass
    try:
        for c in json.loads(Path(registry_path).read_text()).get("chains", []):
            st = c.get("status") or "registry"
            for loc in c.get("locations") or [{"name": c.get("name", "")}]:
                lat, lng = loc.get("lat"), loc.get("lng")
                out.append(Known(loc.get("name") or c.get("name", ""), loc.get("city", ""), loc.get("state", ""),
                                 float(lat) if lat is not None else None, float(lng) if lng is not None else None,
                                 "tracked" if st == "adapter-built" else st))
    except (OSError, ValueError):
        pass
    return out


def match_known(name: str, city: str, state: str, lat: float | None, lng: float | None,
                known: list[Known]) -> Known | None:
    """Same place (within MATCH_KM), or same name in the same city."""
    if lat is not None and lng is not None:
        best = None
        for k in known:
            if k.lat is None or k.lng is None:
                continue
            d = km(lat, lng, k.lat, k.lng)
            if d <= MATCH_KM and (best is None or d < best[0]):
                best = (d, k)
        if best:
            return best[1]
    n, c = _norm(name), _norm(city)
    for k in known:
        if _norm(k.name) == n:  # "Pull A Part - Akron" (Ario) == "Pull-A-Part - Akron" (tracked)
            return k
    for k in known:
        kn = _norm(k.name)
        if c and _norm(k.city) == c and (n in kn or kn.split(" - ")[0] in n):
            return k
    return None


# ---------------------------------------------------------------- sources
@dataclass
class Candidate:
    name: str
    city: str = ""
    state: str = ""
    lat: float | None = None
    lng: float | None = None
    website: str = ""
    source: str = "osm"
    tier: str = ""
    platform: str = ""
    evidence: str = ""
    known_status: str = ""
    extra: dict = field(default_factory=dict)


# Exact tag values Overpass answers from its tag index. A self-service yard
# in OSM is nearly always one of these; the name regex runs inside each
# clause, only over elements carrying that tag, instead of every named object (streets included) in the
# state. Trade-off: a yard mapped with a name and no tag at all is missed —
# Ario discovery and owner requests still cover those.
OSM_TAG_CLAUSES = (
    ("shop", "car_parts"), ("shop", "car"), ("shop", "car_repair"), ("shop", "scrap_yard"),
    ("industrial", "scrap_yard"), ("industrial", "auto_wrecker"), ("landuse", "industrial"),
    ("amenity", "scrap_yard"), ("amenity", "recycling"), ("craft", "car_repair"),
)


def overpass_query(state: str) -> str:
    # The name filter sits inside every clause, so each statement filters on
    # the server before anything is collected: a separate ".t then name"
    # step would first materialise every shop=car / landuse=industrial /
    # amenity=recycling element in the state (huge for CA/TX).
    name = f'["name"~"{OSM_NAME_RE}",i]'
    union = "".join(f'nwr["{k}"="{v}"]{name}(area.s);' for k, v in OSM_TAG_CLAUSES)
    return (
        f'[out:json][timeout:{OSM_SERVER_TIMEOUT}][maxsize:{OSM_MAXSIZE}];'
        f'area["ISO3166-2"="US-{state}"]->.s;({union});out center tags qt;'
    )


def parse_overpass(data: dict) -> list[Candidate]:
    out: list[Candidate] = []
    seen: set[tuple] = set()
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        name = tags.get("name", "")
        if not looks_like_yard(name, tags):
            continue
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lng = el.get("lon", (el.get("center") or {}).get("lon"))
        key = (_norm(name), round(lat or 0, 2), round(lng or 0, 2))
        if key in seen:
            continue
        seen.add(key)
        site = tags.get("website") or tags.get("contact:website") or tags.get("url") or ""
        if site and not site.startswith("http"):
            site = "http://" + site
        out.append(Candidate(name=name, city=tags.get("addr:city", ""), state=tags.get("addr:state", ""),
                             lat=lat, lng=lng, website=site, source="osm"))
    return out


def _overpass_slot_wait(session, url: str) -> float:
    """Seconds until /api/status says this client has a free slot (0 when one
    is free now or the status page can't be read). Overpass hands out a few
    slots per IP; asking first is how its usage policy wants clients to pace."""
    try:
        r = session.get(url.rsplit("/", 1)[0] + "/status", timeout=TIMEOUT, headers={"User-Agent": UA})
        text = r.text if getattr(r, "status_code", 0) == 200 else ""
    except Exception:
        return 0.0
    if not text or re.search(r"\d+ slots? available now", text):
        return 0.0
    waits = [int(n) for n in re.findall(r"in (\d+) seconds?", text)]
    return float(min(min(waits), OSM_MAX_SLOT_WAIT)) if waits else 0.0


def _overpass_once(session, url: str, state: str, sleep) -> tuple[list[Candidate] | None, str]:
    """One state on one server. Waits for a slot, retries once after 429;
    any other failure (5xx, timeout, connection error, error remark) returns
    at once so the caller can try the next server."""
    reason = ""
    for attempt in range(len(OSM_BACKOFF) + 1):
        wait = _overpass_slot_wait(session, url)
        if wait:
            sleep(wait)
        try:
            r = session.post(url, data={"data": overpass_query(state)}, timeout=(OSM_CONNECT_TIMEOUT, OSM_TIMEOUT),
                             headers={"User-Agent": UA})
        except Exception as e:
            return None, type(e).__name__
        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                return None, "200 but not JSON"
            remark = str(data.get("remark") or "")
            if "error" in remark.lower():  # e.g. "runtime error: Query timed out" — not an empty state
                return None, f"remark: {remark[:80]}"
            return parse_overpass(data), ""
        reason = f"HTTP {r.status_code}"
        if r.status_code != 429 or attempt == len(OSM_BACKOFF):
            return None, reason
        sleep(OSM_BACKOFF[attempt])
    return None, reason


def fetch_osm(session, states=US_STATES, pause: float = 3.0, deadline: float | None = None,
              report: dict | None = None, clock=time.time, sleep=time.sleep) -> tuple[list[Candidate], str]:
    """One Overpass query per state, tried on the main server then the
    mirrors. A server that fails OSM_DROP_SERVER_AFTER times in a row is
    skipped for the rest of the pass. Failed states get one retry pass (with
    every server back in) only if some server answered in the first pass.
    Stops at `deadline`. Failed and unqueried states are named in the note
    and put in report["pending"], which main() saves for the next run."""
    out: list[Candidate] = []
    pending = list(states)
    failed: list[str] = []
    skipped: list[str] = []
    for pass_no in (1, 2):
        strikes = {u: 0 for u in OVERPASS_URLS}
        failed, answered = [], False
        for i, st in enumerate(pending):
            live = [u for u in OVERPASS_URLS if strikes[u] < OSM_DROP_SERVER_AFTER]
            if (deadline and clock() > deadline) or not live:
                skipped = list(pending[i:])
                if not live:
                    print("  osm: every Overpass server failed repeatedly, stopping this pass", flush=True)
                break
            got, why = None, []
            for url in live:
                got, reason = _overpass_once(session, url, st, sleep)
                if got is not None:
                    strikes[url] = 0
                    break
                strikes[url] += 1
                why.append(f"{urlparse(url).netloc} {reason}")
            if got is None:
                failed.append(st)
                print(f"  osm {st}: failed ({'; '.join(why)})", flush=True)
            else:
                answered = True
                for c in got:
                    c.state = c.state or st
                out += got
                print(f"  osm {st}: {len(got)}" + (" (retry)" if pass_no == 2 else ""), flush=True)
            if pause:
                sleep(pause)
        if pass_no == 2 or not failed or not answered or (deadline and clock() > deadline):
            break
        # retry the failed states before the never-queried ones
        pending, skipped = failed + skipped, []
    msg = []
    if failed:
        msg.append(f"Overpass failed for {', '.join(failed)}")
    if skipped:
        msg.append(f"not queried: {', '.join(skipped)}")
    if report is not None:
        report["pending"] = failed + skipped
        report["covered"] = [st for st in states if st not in failed + skipped]
    return out, "; ".join(msg)


def osm_state_order(prev_json: Path = OUT_JSON, states=US_STATES) -> list[str]:
    """States the last run could not cover go first, the rest keep their order."""
    try:
        pend = [s for s in json.loads(prev_json.read_text()).get("osm_pending") or [] if s in states]
    except (OSError, ValueError, AttributeError):
        pend = []
    return pend + [s for s in states if s not in pend]


def fetch_ario(session) -> tuple[list[Candidate], str]:
    """Ario orgs not in ARIO_CHAINS / the registry, with live row counts."""
    try:
        import junkyard_scraper as js
    except Exception as e:  # pragma: no cover
        return [], f"scraper import failed: {type(e).__name__}"
    known_slugs = {str(y["slug"]).lower() for ch in js.ARIO_CHAINS.values() for y in ch.get("yards", []) if y.get("slug")}
    known_ids = {str(y["org_id"]) for ch in js.ARIO_CHAINS.values() for y in ch.get("yards", []) if y.get("org_id")}
    try:
        for c in json.loads(REGISTRY_PATH.read_text()).get("chains", []):
            for loc in c.get("locations") or []:
                if loc.get("ario_slug"):
                    known_slugs.add(str(loc["ario_slug"]).lower())
    except (OSError, ValueError):
        pass
    orgs = js._ario_search_all(session, "custom.organization", [], max_pages=5)
    if not orgs:
        return [], "Ario org table fetch failed"
    out: list[Candidate] = []
    for o in orgs:
        src = o.get("_source") or {}
        slugs = {str(src.get(f) or "").strip().lower() for f in ("Slug", "id_text")} - {""}
        if not slugs or slugs & known_slugs or str(o.get("_id") or "") in known_ids:
            continue
        slug = str(src.get("Slug") or src.get("id_text")).strip().lower()  # the live frontend routes on Slug
        name = str(src.get("name_text") or src.get("name1_text") or slug).strip()
        pin = js._ario_org_pin(o)
        res = js._ario_live_post(session, "search-inventory", {
            "start_year": None, "end_year": None, "input_make": None, "input_model": None,
            "make_list": None, "model_keywords": None, "yard_list": [slug], "min_date_placed": None,
            "ario_date_removed": None, "sort_mode": "days_newest", "projection": "list",
            "surface": "yard", "per_yard_limit": 1, "item_rank_offset": 0, "limit_results": 1,
        })
        items = (res or {}).get("items") or []
        meta = next((m for m in ((res or {}).get("yards_meta") or []) if m.get("yard") == slug), {})
        total = int(meta.get("total_matching") or 0)
        newest = str((items[0].get("date_placed") if items else "") or "")[:10]
        c = Candidate(name=name, lat=pin[0] if pin else None, lng=pin[1] if pin else None,
                      website=f"https://ario.autorecycler.io/yard/{slug}", source="ario",
                      platform="Ario (autorecycler.io)", extra={"slug": slug, "live_rows": total, "newest": newest})
        fresh = False
        try:
            fresh = (datetime.now(timezone.utc).date() - datetime.fromisoformat(newest).date()).days <= ARIO_FRESH_DAYS
        except ValueError:
            pass
        # Ario's own org flag. All 25 Ario yards we list carry it (checked
        # 2026-11-03); A-1 Metals, a full-service dismantler, does not.
        self_serve = bool(src.get("is_self_service_boolean"))
        c.extra["self_service"] = self_serve
        if total >= ARIO_MIN_ROWS and fresh and not self_serve:
            c.tier, c.evidence = "D", f"live on Ario ({total} rows) but Ario lists it as not self-service"
        elif total >= ARIO_MIN_ROWS and fresh:
            c.tier, c.evidence = "A", f"live on Ario: {total} rows, newest set-out {newest}"
        elif total > 0:
            c.tier, c.evidence = "E", f"on Ario but stale: {total} rows, newest set-out {newest or 'undated'}"
        else:
            c.tier, c.evidence = "E", "Ario org exists but not on the live backend"
        out.append(c)
    return out, ""


# ---------------------------------------------------------------- site check
class Site:
    """Polite fetcher: robots.txt per host, one request every SITE_DELAY_SEC."""

    def __init__(self, session, delay: float = SITE_DELAY_SEC):
        self.session, self.delay = session, delay
        self._robots: dict[str, RobotFileParser | None] = {}
        self._last = 0.0

    def _wait(self):
        dt = time.time() - self._last
        if dt < self.delay:
            time.sleep(self.delay - dt)
        self._last = time.time()

    def allowed(self, url: str) -> bool:
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self._robots:
            rp = RobotFileParser()
            try:
                self._wait()
                r = self.session.get(base + "/robots.txt", timeout=TIMEOUT, headers={"User-Agent": UA})
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                else:
                    rp.parse([])  # no robots.txt: allowed
                self._robots[base] = rp
            except Exception:
                self._robots[base] = None  # unreachable: decided by the page fetch
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(UA, url)

    def get(self, url: str) -> tuple[int, str, str]:
        """(status, final url, html) — status 0 when unreachable."""
        self._wait()
        try:
            r = self.session.get(url, timeout=TIMEOUT, headers={"User-Agent": UA, "Accept": "text/html"},
                                 allow_redirects=True)
            return r.status_code, r.url, r.text[:400000]
        except Exception as e:
            return 0, url, type(e).__name__


def check_site(c: Candidate, site: Site) -> Candidate:
    url = c.website
    if not url:
        c.tier, c.evidence = "E", "no website on the map"
        return c
    if not site.allowed(url):
        c.tier, c.evidence = "C", "robots.txt disallows the homepage"
        return c
    status, final, html = site.get(url)
    if status == 0:
        c.tier, c.evidence = "E", f"unreachable ({html})"
        return c
    if is_challenge(status, html):
        c.tier, c.evidence = "C", f"blocked us (HTTP {status} / bot check) — ask the yard"
        return c
    if status >= 400:
        c.tier, c.evidence = "E", f"HTTP {status}"
        return c
    fp = fingerprint(html)
    inv_url = None
    if not fp or not fp[1]:
        inv_url = inventory_link(final, html)
        if inv_url:
            if not site.allowed(inv_url):
                c.tier, c.evidence = "C", f"robots.txt disallows {urlparse(inv_url).path}"
                return c
            s2, f2, h2 = site.get(inv_url)
            if s2 and is_challenge(s2, h2):
                c.tier, c.evidence = "C", f"inventory page blocked us (HTTP {s2}) — ask the yard"
                return c
            if 200 <= s2 < 400:
                fp = fingerprint(h2) or fp
                if not fp and _INV_TABLE.search(re.sub(r"<[^>]+>", " ", h2)):
                    c.tier, c.platform, c.evidence = "B", "custom", f"vehicle table at {f2}"
                    return c
    if fp:
        c.platform = fp[0]
        if fp[1]:
            c.tier, c.evidence = "A", f"{fp[0]} fingerprint" + (f" on {inv_url}" if inv_url else "")
        elif fp[0].startswith("row52"):
            c.tier, c.evidence = "D", "inventory is on Row52 (out of scope)"
        else:
            c.tier, c.evidence = "D", fp[0]
        return c
    if inv_url:
        c.tier, c.platform, c.evidence = "B", "custom", f"inventory link {inv_url} (no recognised platform; check by hand)"
    else:
        c.tier, c.evidence = "D", "site has no inventory link"
    return c


# ---------------------------------------------------------------- report
TIER_TITLES = {
    "A": "A. Runs a platform we already parse (cheapest adds)",
    "B": "B. Has its own online inventory (custom adapter)",
    "C": "C. Blocked us or robots.txt says no (outreach)",
    "D": "D. Site found, no online vehicle inventory",
    "E": "E. No website on the map, or unreachable",
}


def render_md(cands: list[Candidate], skipped: dict, notes: list[str], when: str) -> str:
    by = {t: [c for c in cands if c.tier == t] for t in "ABCDE"}
    L = [f"# Coverage sweep — {when[:10]}", "",
         "Generated by `scraper/coverage_sweep.py` (read-only). Candidates are yards that",
         "look self-service and that we don't track. Nothing here is wired into the scan;",
         "each add is a reviewed change. Tier C yards go to outreach, never a workaround.", "",
         "| | Yards |", "|---|---|"]
    for t in "ABCDE":
        L.append(f"| {TIER_TITLES[t]} | {len(by[t])} |")
    L.append(f"| Already tracked (skipped) | {skipped.get('tracked', 0)} |")
    for st, n in sorted(skipped.items()):
        if st != "tracked":
            L.append(f"| In the registry as {st} (skipped) | {n} |")
    if notes:
        L += ["", "**Notes:** " + " ".join(notes)]
    for t in "ABCDE":
        rows = sorted(by[t], key=lambda c: (c.state, c.city, c.name))
        if not rows:
            continue
        L += ["", f"## {TIER_TITLES[t]}", "", "| Yard | Where | Platform | Evidence | Link |", "|---|---|---|---|---|"]
        for c in rows:
            where = ", ".join(x for x in (c.city, c.state) if x) or (f"{c.lat:.3f}, {c.lng:.3f}" if c.lat is not None else "")
            L.append(f"| {c.name} | {where} | {c.platform or '—'} | {c.evidence} | {c.website or '—'} |")
    return "\n".join(L) + "\n"


def run(session, use_osm: bool = True, use_ario: bool = True, max_sites: int = 400,
        known: list[Known] | None = None, site: Site | None = None,
        osm_fetch=fetch_osm, ario_fetch=fetch_ario, budget_min: float | None = None,
        clock=time.time, osm_share: float = OSM_SHARE) -> tuple[list[Candidate], dict, list[str]]:
    """budget_min: total minutes. Discovery may use osm_share (default 65%) of it, website checks
    the rest; whatever is left unchecked is listed as such, and the report is
    always written."""
    known = load_known() if known is None else known
    site = site or Site(session)
    notes: list[str] = []
    raw: list[Candidate] = []
    t0 = clock()
    end = t0 + budget_min * 60 if budget_min else None
    osm_end = t0 + budget_min * 60 * osm_share if budget_min else None
    for on, label, fetch in ((use_ario, "Ario", ario_fetch), (use_osm, "OpenStreetMap", osm_fetch)):
        if not on:
            continue
        try:
            got, err = fetch(session, deadline=osm_end) if label == "OpenStreetMap" and osm_end else fetch(session)
        except Exception as e:  # one broken source must not sink the sweep
            got, err = [], f"{type(e).__name__}: {str(e)[:120]}"
        raw += got
        if err:
            notes.append(f"{label}: {err}.")
    out: list[Candidate] = []
    skipped: dict[str, int] = {}
    checked = 0
    timed_out = False
    for c in raw:
        k = match_known(c.name, c.city, c.state, c.lat, c.lng, known)
        if k:
            skipped[k.status] = skipped.get(k.status, 0) + 1
            continue
        if not c.tier:
            if checked >= max_sites:
                c.tier, c.evidence = "E", "not checked (site budget reached)"
            elif end and clock() > end:
                c.tier, c.evidence = "E", "not checked (time budget reached)"
                timed_out = True
            else:
                check_site(c, site)
                checked += 1
                if checked % 25 == 0:
                    print(f"  checked {checked} sites", flush=True)
        out.append(c)
    if checked >= max_sites:
        notes.append(f"Website checks capped at {max_sites}.")
    if timed_out:
        notes.append(f"Time budget ({budget_min:g} min) reached after {checked} website checks; re-run to cover the rest.")
    return out, skipped, notes


def merge_report(prev: dict, cands: list[Candidate], skipped: dict, notes: list[str],
                 pending: list[str], when: str) -> tuple[list[Candidate], dict, list[str], dict]:
    """--osm-pending: fold one OSM-only pass into the last full report. Earlier
    candidates stay (a re-found yard is replaced by the new row), skip counts
    add up, the old OpenStreetMap note gives way to this pass's, and
    osm_pending shrinks to what this pass still could not cover."""
    def key(c: Candidate) -> tuple:
        return (c.source, _norm(c.name), round(c.lat or 0, 2), round(c.lng or 0, 2))
    fields = set(Candidate.__dataclass_fields__)
    old = [Candidate(**{k: v for k, v in d.items() if k in fields}) for d in prev.get("candidates") or []]
    new_keys = {key(c) for c in cands}
    merged = [c for c in old if key(c) not in new_keys] + list(cands)
    sk = dict(prev.get("skipped") or {})
    for k, n in skipped.items():
        sk[k] = sk.get(k, 0) + n
    kept = [n for n in prev.get("notes") or [] if not n.startswith(("OpenStreetMap:", "OSM-only pass"))]
    covered = len([s for s in prev.get("osm_pending") or [] if s not in pending])
    kept.append(f"OSM-only pass {when}: {covered} pending state(s) covered, {len(pending)} still pending.")
    out = {"at": when, "skipped": sk, "notes": kept + notes, "osm_pending": pending,
           "candidates": [asdict(c) for c in merged]}
    return merged, sk, out["notes"], out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Find self-service yards we don't track yet.")
    ap.add_argument("--no-osm", action="store_true")
    ap.add_argument("--no-ario", action="store_true")
    ap.add_argument("--max-sites", type=int, default=400)
    ap.add_argument("--budget-min", type=float, default=70, help="total time budget; the report is always written")
    ap.add_argument("--osm-pending", action="store_true",
                    help="OSM-only pass over the states the last run left in osm_pending; merges into the report")
    args = ap.parse_args(argv)
    if requests is None:
        print("::error::python 'requests' is required")
        return 2
    session = requests.Session()
    try:
        prev = json.loads(OUT_JSON.read_text())
    except (OSError, ValueError):
        prev = {}
    osm_report: dict = {}
    if args.osm_pending:
        states = [s for s in prev.get("osm_pending") or [] if s in US_STATES]
        if not states:
            print("coverage sweep: osm_pending is empty, nothing to do")
            return 0
        print(f"OSM-only pass over {len(states)} pending state(s): {', '.join(states)}", flush=True)
        osm_fetch = functools.partial(fetch_osm, states=states, report=osm_report)
        cands, skipped, notes = run(session, use_osm=True, use_ario=False, max_sites=args.max_sites,
                                    budget_min=args.budget_min, osm_fetch=osm_fetch, osm_share=OSM_ONLY_SHARE)
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cands, skipped, notes, doc = merge_report(prev, cands, skipped, notes,
                                                  osm_report.get("pending", states), when)
        OUT_MD.write_text(render_md(cands, skipped, notes, when))
        OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    else:
        osm_fetch = functools.partial(fetch_osm, states=osm_state_order(), report=osm_report)
        cands, skipped, notes = run(session, use_osm=not args.no_osm, use_ario=not args.no_ario,
                                    max_sites=args.max_sites, budget_min=args.budget_min, osm_fetch=osm_fetch)
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        OUT_MD.write_text(render_md(cands, skipped, notes, when))
        if args.no_osm:  # nothing queried: carry the last run's list forward
            pending = prev.get("osm_pending") or []
        else:  # absent when fetch_osm raised: then no state was covered
            pending = osm_report.get("pending", list(US_STATES))
        OUT_JSON.write_text(json.dumps({"at": when, "skipped": skipped, "notes": notes, "osm_pending": pending,
                                        "candidates": [asdict(c) for c in cands]}, indent=1) + "\n")
    counts = {t: sum(1 for c in cands if c.tier == t) for t in "ABCDE"}
    print(f"coverage sweep: {len(cands)} untracked candidates — " +
          ", ".join(f"{t}:{n}" for t, n in counts.items()) +
          f"; skipped {sum(skipped.values())} known. Report: {OUT_MD}")
    for n in notes:
        print("note:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
