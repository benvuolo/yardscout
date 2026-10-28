#!/usr/bin/env python3
"""Generate the tier-3 yard→inventory-page map shipped in docs/app.js.

Every car card links to the yard's own site (free feature, tiered):
  tier 1 — per-car page (Wrench-A-Part family / Fenix / Go Pull-It; templates
           live in yardPageUrl() in docs/app.js, not here)
  tier 2 — filtered make/model search (Pick-A-Part VA, Rupert's; also in
           yardPageUrl())
  tier 3 — the yard's inventory page (THIS map): the fallback that guarantees
           every card links somewhere sensible.

This script is the single source of truth for tier 3. It merges:
  - independent_yards_registry.json  (curated inventory_url per chain)
  - BIG_CHAINS below                 (the 5 majors the registry doesn't cover)
  - OVERRIDES below                  (registry URLs that have gone stale)
then validates that every yard in docs/data/inventory_live.json matches
exactly one pattern, and rewrites the generated block in docs/app.js between
the GEN:YARD_INVENTORY_PAGES markers. Inventory payload growth: zero.

Usage:
  python3 scraper/gen_yard_site_links.py           # validate + rewrite app.js
  python3 scraper/gen_yard_site_links.py --check   # also HTTP-check every URL
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_JS = ROOT / "docs" / "app.js"
PAYLOAD = ROOT / "docs" / "data" / "inventory_live.json"
REGISTRY = ROOT / "scraper" / "independent_yards_registry.json"

BEGIN = "/* GEN:YARD_INVENTORY_PAGES:BEGIN (gen_yard_site_links.py) */"
END = "/* GEN:YARD_INVENTORY_PAGES:END */"

# (js_regex_source, registry_chain_name_or_None, url_or_None, comment)
# Order matters: first match wins, so yard-specific entries come before chain
# entries and tightly-anchored chains come before loose ones.
#
# BUSINESS DECISION — Pick-n-Pull cars deliberately link to picknpull.com's own
# check-inventory page, NOT Row52 (which has nicer per-car pages). Row52 is a
# direct competitor to this app; do not "helpfully" add Row52 links.
ENTRIES: list[tuple[str, str | None, str | None, str]] = [
    # --- per-yard entries (chains whose yards have distinct pages/sites) ---
    (r"^utah pic-a-part - ogden \(premium\)", None,
     "https://utpap.com/ogden-premium-inventory/", "UTPAP per-yard page"),
    (r"^utah pic-a-part - ogden", None,
     "https://utpap.com/ogden-inventory/", "UTPAP per-yard page"),
    (r"^utah pic-a-part - orem \(premium\)", None,
     "https://utpap.com/orem-premium-inventory/", "UTPAP per-yard page"),
    (r"^utah pic-a-part - orem", None,
     "https://utpap.com/orem-inventory/", "UTPAP per-yard page"),
    (r"^budget u-pull-it - bartow", None,
     "http://budgetupullit.s3softwaresolutions.com/inventory.aspx",
     "Bartow runs a separate legacy site (http-only)"),

    # --- the 5 majors (not in the independents registry) ---
    (r"^pick[\s-]*n[\s-]*pull", None,
     "https://www.picknpull.com/check-inventory", "Pick-n-Pull"),
    (r"^pick your part", None,
     "https://www.pyp.com/inventory/", "LKQ Pick Your Part (pyp.com)"),
    (r"^pull[\s-]*a[\s-]*part", None,
     "https://www.pullapart.com/used-auto-parts/search-car-inventory/",
     "Pull-A-Part (their ?Locations=&MakeID= deep-link params exist in app.js "
     "source but do not auto-load on the live site — re-test before promoting "
     "to tier 2)"),
    (r"^tear[\s-]*a[\s-]*part", None,
     "https://tearapart.com/inventory/", "Tear-A-Part"),

    # --- independents: URL pulled from independent_yards_registry.json ---
    (r"wrench[\s-]*a[\s-]*part", "Wrench-A-Part", None,
     "also matches Primo/Roosevelt — same site, same photo viewer"),
    (r"^fenix", "Fenix U-Pull", None, ""),
    (r"^go pull[\s-]*it", "Go Pull-It", None, ""),
    (r"^pull[\s-]*n[\s-]*save", "Pull-N-Save", None, ""),
    (r"^parts galore", "Parts Galore", None, ""),
    (r"^sturtevant", "Sturtevant Auto", None, ""),
    (r"^ace pick", "Ace Pick-A-Part", None, ""),
    (r"^harry'?s", "Harry's U-Pull-It", None,
     "tier 3 only: recycled stock ids + no photos make per-car links useless, "
     "and the site's Sucuri challenge blocks cheap verification of filters"),
    (r"^indy[\s-]*u[\s-]*pull", "Indy-U-Pull-It", None, ""),
    # Two unrelated "U-Pull-It Auto Parts" chains (WA iis-pro-upull, TN CRUSH
    # MVC) must be matched before the IA/NE catch-all below.
    (r"^u-pull-it auto parts - (pasco|kennewick|yakima)", "U-Pull-It Auto Parts (WA)", None,
     "go2upullit.com: 3 WA yards share one inventory deck"),
    (r"^u-pull-it auto parts - (memphis|millington)", "U-Pull-It Auto Parts", None,
     "upullitap.com (TN); was falling through to the IA/NE entry"),
    (r"^u[\s-]*pull[\s-]*it\b", "U-Pull-It (IA/NE)", None,
     "anchored: Budget/Indy/Harry's/Rupert's/Pipes U-Pull-Its differ upfront"),
    (r"^rupert", "Rupert's U-Pull-It", None, "tier 2 handles cars with a make"),
    (r"^chesterfield", "Chesterfield Auto Parts", None, "search form is POST-only"),
    (r"^ipull", "iPull-uPull", None, ""),
    (r"^st\.?\s*cloud", "St. Cloud U Pull", None, ""),
    (r"^pick-a-part va", "Pick-A-Part VA", None, "tier 2 handles make+model"),
    (r"^nevada pic", None, "https://www.nvpap.com/",
     "registry's used-car-inventory.html went 404 (2026-10); the homepage IS "
     "their inventory browser"),
    (r"^bessler", "Road Tested Parts (VinPlus)", None, ""),
    (r"^bluegrass", "Road Tested Parts (VinPlus)", None, ""),
    (r"^raceway", "Road Tested Parts (VinPlus)", None, ""),
    (r"^rtp\b", "Road Tested Parts (VinPlus)", None, ""),
    (r"^pickers\b", "Pickers / Pipes U-Pull-It (VinPlus)", None, ""),
    (r"^pipes\b", "Pickers / Pipes U-Pull-It (VinPlus)", None, ""),
    (r"^joliet u[\s-]*pull[\s-]*it", "Joliet U-Pull-It (VinPlus)", None,
     "own Wix site renders the same inventory the VinPlus API serves"),
    (r"^san antonio pick[\s-]*n[\s-]*pull",
     "San Antonio Pick-N-Pull (Independent) (VinPlus)", None,
     "independent yard (picknpullsa.com) — NOT the Pick-n-Pull chain; the "
     "display name never starts with 'Pick-N-Pull' so the chain entries above "
     "can't shadow this one"),
    (r"^195 used auto parts", "195 Used Auto Parts (VinPlus)", None,
     "own site runs the CRUSH MVC app"),
    (r"^pick ur part", "Pick Ur Part Auto Salvage (VinPlus)", None,
     "yardconnect-pro inventory on their own WordPress site"),
    (r"^u[\s-]*pick[\s-]*it az", "U-Pick-It AZ", None, ""),
    (r"^barry'?s", "Barry's U Pull It", None, ""),
    (r"^prestige", "Prestige Pull-Your-Part", None, ""),
    (r"^budget", "Budget U-Pull-It", None, "Winter Garden (Bartow matched above)"),
    (r"^ryan'?s pick", "Ryan's Pick-a-Part", None,
     "the Ario iframe host has no deep links; the CRUSH /Home/Inventory page "
     "embeds it"),
    (r"^us auto supply", "US Auto Supply", None, ""),
    (r"^u[\s-]*pull and save", "U-Pull and Save", None,
     "tier 1 handles per-car /vehicles/{id} links; anchored so the U-Pull-It "
     "chains can't collide"),
    # --- CRUSH MVC tenants (2026-10-27) — one app per tenant, no deep links ---
    (r"^pick-a-part jalopy jungle", "Pick-A-Part Jalopy Jungle", None,
     "5 Idaho yards share one inventory app (yard picker on the page)"),
    (r"^trusty pick-a-part", "Trusty Pick-A-Part", None, ""),
    (r"^m&m u-pull-it", "M&M U-Pull-It", None, ""),
    (r"^polk county pick and pay", "Polk County Pick and Pay", None, ""),
    # (2026-10-28: these 10-27 tenants were live without a tier-3 entry,
    # which made validate() exit; registry URLs already existed.)
    (r"^buddy'?s upull", "Buddy's Upull", None, ""),
    (r"^marion county auto parts", "Marion County Auto Parts", None, ""),
    (r"^662 self serve", "662 Self Serve Auto Parts", None, ""),
    (r"^cp'?s u-pull-it", "CP's U-Pull-It", None, ""),
    (r"^genesis metal recycling", "Genesis Metal Recycling", None, ""),
    # --- yardconnect-pro tenants (2026-10-27) — whole-lot table pages, no deep links ---
    (r"^chuck & eddie'?s", "Chuck & Eddie's Self Service", None,
     "Southington self-service lot only (New Haven/Hartford are full-service)"),
    (r"^robertson'?s u[\s-]*pull[\s-]*it", "Robertson's U-Pull-It", None,
     "U-Pull-It side of Robertson's Auto Salvage (Hollander full-service stock ignored)"),
    # --- 2026-10-27 SD/NY/TX wave ---
    (r"^byot auto parts - waco", None,
     "https://www.byotautoparts.com/locations/waco/inventory/",
     "BYOT per-location inventory page"),
    (r"^byot auto parts - bryan", None,
     "https://www.byotautoparts.com/locations/bryan-college-station/inventory/",
     "BYOT per-location inventory page"),
    (r"^byot auto parts - beaumont", None,
     "https://www.byotautoparts.com/locations/beaumont/inventory/",
     "BYOT per-location inventory page"),
    (r"^byot auto parts - baton rouge", None,
     "https://www.byotautoparts.com/locations/baton-rouge/inventory/",
     "BYOT per-location inventory page"),
    (r"^byot auto parts - jackson", None,
     "https://www.byotautoparts.com/locations/jackson-ms/inventory/",
     "BYOT per-location inventory page"),
    (r"^wilbert'?s u-pull-it", "Wilbert's U-Pull-It", None,
     "3 NY yards share one search page (location picker on the page)"),
    # --- 2026-10-28 iis-pro-upull + CRUSH static-table wave ---
    (r"^aesop u-pull", "AESOP Self Serve", None, "Tulsa deck (&id=OO95)"),
    (r"^midway u-pull", "Midway U-Pull", None,
     "Muncie + Liberty share one site (location picker on the page)"),
    (r"^hwy 82 pick", "Hwy 82 Pick & Pay", None, ""),
    (r"^route 34 u-pull-m", "Route 34 U-Pull-M", None, ""),
    (r"^sunshine auto salvage", "Sunshine Auto Salvage", None, ""),
    # --- 2026-10-28 single-host adapters (Kiker's / Weller / Cagle's) ---
    (r"^kiker'?s u-pull-it", "Kiker's U-Pull-It", None, ""),
    (r"^weller self serve", "Weller Self Serve", None, ""),
    (r"^cagle'?s u-pull-it", "Cagle's U-Pull-It", None,
     "WebForms make/model postbacks: no deep links"),
]


def _js_regex_escape(s: str) -> str:
    return re.sub(r"([.*+?^${}()|\[\]\\/])", r"\\\1", s)


def ario_rows() -> list[tuple[str, str]]:
    """Per-yard tier-3 links for the multi-tenant Ario chains, derived from
    ARIO_CHAINS in the scraper so a new yard is one config entry: every Ario
    org has a public inventory page at app.autorecycler.io/inventory/{slug}.
    Ryan's keeps its curated registry entry (its own site embeds the page)."""
    sys.path.insert(0, str(ROOT / "scraper"))
    import junkyard_scraper as js  # noqa: E402
    rows = []
    for source, chain in js.ARIO_CHAINS.items():
        if source == "ryans":
            continue
        for y in chain["yards"]:
            rows.append((f"^{_js_regex_escape(y['name'].lower())}$",
                         f"https://app.autorecycler.io/inventory/{y['slug']}"))
    return rows


def build_rows() -> list[tuple[str, str]]:
    registry = json.loads(REGISTRY.read_text())
    by_name = {c["name"]: c for c in registry["chains"]}
    # Exact per-yard anchors first: they can't shadow anything else.
    rows = ario_rows()
    for pattern, reg_name, url, _comment in ENTRIES:
        if url is None:
            chain = by_name.get(reg_name)
            if not chain or not chain.get("inventory_url"):
                sys.exit(f"ERROR: registry has no inventory_url for {reg_name!r}")
            url = chain["inventory_url"]
        rows.append((pattern, url))
    return rows


def validate(rows: list[tuple[str, str]]) -> dict:
    payload = json.loads(PAYLOAD.read_text())
    yards = [y[0] for y in payload["yards"]]
    compiled = [(re.compile(p, re.I), u) for p, u in rows]
    unmatched = [y for y in yards if not any(rx.search(y) for rx, _ in compiled)]
    if unmatched:
        sys.exit(f"ERROR: {len(unmatched)} yards have no tier-3 link: {unmatched}")

    # Tier coverage report (mirrors yardPageUrl() in docs/app.js).
    fields = payload["fields"]
    ii, vi, yi = fields.index("id"), fields.index("vin"), fields.index("yard")
    mki = fields.index("make")
    wap = re.compile(r"wrench[\s-]*a[\s-]*part", re.I)
    papva = re.compile(r"^pick-a-part va", re.I)
    rup = re.compile(r"^rupert", re.I)
    tiers = {1: 0, 2: 0, 3: 0}
    for v in payload["vehicles"]:
        vid, loc = str(v[ii]), yards[v[yi]]
        if (wap.search(loc) and v[vi]) or vid.startswith(("fenix-", "gopullit-")):
            tiers[1] += 1
        elif (papva.search(loc) or rup.search(loc)) and v[mki]:
            tiers[2] += 1
        else:
            tiers[3] += 1
    total = len(payload["vehicles"])
    print(f"Tier coverage of {total:,} vehicles:")
    for t in (1, 2, 3):
        print(f"  tier {t}: {tiers[t]:>7,}  ({tiers[t] / total * 100:.1f}%)")
    return tiers


def emit(rows: list[tuple[str, str]]) -> None:
    lines = ["const YARD_INVENTORY_PAGES = ["]
    for pattern, url in rows:
        lines.append(f"  [/{pattern}/i, '{url}'],")
    lines.append("];")
    block = BEGIN + "\n" + "\n".join(lines) + "\n" + END
    src = APP_JS.read_text()
    if BEGIN not in src or END not in src:
        sys.exit("ERROR: GEN:YARD_INVENTORY_PAGES markers not found in docs/app.js")
    new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block,
                 src, count=1, flags=re.S)
    APP_JS.write_text(new)
    print(f"Wrote {len(rows)} entries into docs/app.js")
    # Same map as JSON for the share pages (backend/site-proxy/src/share.js):
    # [[regex source, url], ...] — the Worker rebuilds the RegExp with the i flag.
    out = ROOT / "docs" / "data" / "yard_site_links.json"
    out.write_text(json.dumps([[pattern, url] for pattern, url in rows], separators=(",", ":")))
    print(f"Wrote {len(rows)} entries into {out.relative_to(ROOT)}")


def http_check(rows: list[tuple[str, str]]) -> None:
    import urllib.request
    ok = True
    seen = set()
    for _p, url in rows:
        if url in seen:
            continue
        seen.add(url)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/130.0 Safari/537.36"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"  {r.status}  {url}")
                if r.status >= 400:
                    ok = False
        except Exception as e:  # Sucuri/WAF pages often reject bots; note, don't fail
            print(f"  WARN {url}: {e}")
    if not ok:
        sys.exit("ERROR: some tier-3 URLs returned >=400")


if __name__ == "__main__":
    rows = build_rows()
    validate(rows)
    emit(rows)
    if "--check" in sys.argv:
        http_check(rows)
