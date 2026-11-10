"""Hosting platform of each crawled catalog site (no imports beyond the
standard library: the workflow's plan step loads this without the crawler's
dependencies).

Why (hub 2026-11-10): on 2026-11-10 07:10-07:16 UTC run 42712787314 had six
crawl jobs live (jeep, mb, nissan, subaru, ford, gm), each at fetch.py's
per-site pace, and mbpartsgiant, nissanpartsdeal and subarupartsdeal answered
HTTP 503 within six minutes, as three sites did on 2026-11-05. The stores
are one dealer-catalog platform, so per-site pacing multiplied the load on
one host network by the number of jobs. The crawl is now paced per PLATFORM:
one CI job per platform crawls its sites in turn, and fetch.py adds a
platform-wide request gap (PLATFORM_GAP) on top of the per-site one.

Platform evidence is from served markers recorded by the source scout
(SOURCES.md section 2, probe.py, 2026-11-05), never from the domain name.
Every store in PLATFORM below:
- serves the same robots.txt rule set for `*` (Disallow /Page_Customer/
  /Page_Cart/ /Page_Product/ /online/ /onlineapi/, no Crawl-delay);
- serves its terms at /service/<make>-terms_and_conditions(.html) as the
  same client-rendered shell (about 75 KB, the same size as its 404 page);
- links the other stores in its footer as sister stores (toyotapartsdeal,
  bmwpartsdeal);
- uses one of the two SimplePart store templates (/genuine/ or /oem/ product
  URLs, or the PartsGiant .html family), whose shared parser templates are
  sites/_simplepart.py and sites/_partsgiant.py.
The scout labels both families "SimplePart/PartsGiant dealer network".
"""
from __future__ import annotations

SIMPLEPART = "simplepart"

PLATFORM: dict[str, str] = {
    # SimplePart store template (/genuine/ or /catalog/ + /oem/)
    "www.toyotapartsnow.com": SIMPLEPART,
    "www.jeeppartsdeal.com": SIMPLEPART,
    "www.vwpartsgiant.com": SIMPLEPART,
    "www.mazdapartsnow.com": SIMPLEPART,
    "www.mbpartsgiant.com": SIMPLEPART,
    "www.mitsubishipartsgiant.com": SIMPLEPART,
    "www.volvopartsgiant.com": SIMPLEPART,
    "www.audipartsgiant.com": SIMPLEPART,
    # PartsGiant .html template, same network (sister-store footers,
    # identical robots and terms shell)
    "www.gmpartsgiant.com": SIMPLEPART,
    "www.fordpartsgiant.com": SIMPLEPART,
    "www.moparpartsgiant.com": SIMPLEPART,
    "www.nissanpartsdeal.com": SIMPLEPART,
    "www.infinitipartsdeal.com": SIMPLEPART,
    "www.hondapartsnow.com": SIMPLEPART,
    "www.acurapartswarehouse.com": SIMPLEPART,
    "www.hyundaipartsdeal.com": SIMPLEPART,
    "www.kiapartsnow.com": SIMPLEPART,
    "www.subarupartsdeal.com": SIMPLEPART,
    "www.lexuspartsnow.com": SIMPLEPART,
    "www.bmwpartsdeal.com": SIMPLEPART,
}

# Minimum seconds between two requests to ANY site of the platform, across
# processes on one machine (fetch.py file lock). 8.0 = the single-site pace
# used since 2026-11-05 (fetch.PER_DOMAIN_GAP), so the whole platform now gets
# what one site got before.
PLATFORM_GAP: dict[str, float] = {SIMPLEPART: 8.0}


def platform_of(site: str) -> str:
    """The site's platform; a site missing from the table is its own
    platform (isolated job) until it is classified. tests/test_platforms.py
    requires every site module to be in the table."""
    return PLATFORM.get(site) or f"site:{site}"


def groups(sites) -> list[dict]:
    """Plan-step matrix: one entry per platform, sites in the given order:
    [{"platform": "simplepart", "sites": "a b c"}, ...], sorted by platform."""
    by: dict[str, list[str]] = {}
    for s in sites:
        by.setdefault(platform_of(s), []).append(s)
    return [{"platform": p, "sites": " ".join(by[p])} for p in sorted(by)]


def rotation(sites, run_number: int) -> list[str]:
    """Round-robin start for one job: the sites in table order, starting at
    run_number mod n, so a site at the end of the list is not starved when a
    job's time budget runs out before the round ends."""
    sites = list(sites)
    if not sites:
        return []
    k = int(run_number) % len(sites)
    return sites[k:] + sites[:k]


def slice_minutes(n_sites: int, budget: int = 300, lo: int = 10, hi: int = 30) -> int:
    """Minutes per site turn: one round of the platform's sites fits the job's
    budget, between lo and hi minutes per turn."""
    if n_sites <= 0:
        return hi
    return max(lo, min(hi, budget // n_sites))
