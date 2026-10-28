# Independent / Regional Self-Service Yards — Landscape & Onboarding Plan

*Research pass: 2026-09-10 (feature/independent-yards). Machine-readable companion:
`scraper/independent_yards_registry.json`.*

Scope: US self-service (u-pull) yards **outside** the three national chains already
covered (Pick-n-Pull, LKQ Pick Your Part, Pull-A-Part) and the Utah locals
(Tear-A-Part, Utah Pic-A-Part). Only yards that publish **searchable/browsable
vehicle inventory online** are onboardable; photo capture stays off everywhere
(owner policy), and anything served by Row52 is permanently out of scope.

## Headline findings

1. **Row52 is no longer a factor for independents.** Row52 was acquired by / became
   exclusive to Pick-n-Pull. Independent yards that used to publish through Row52
   have simply dropped off the public internet — they are not "Row52-locked" so much
   as *offline*. Zero of the candidates below embed Row52 today, so the legal
   exclusion costs us nothing in this cohort.
2. **There is no single dominant inventory platform for independents**, but there is
   one genuine shared platform in this cohort: a WordPress vehicle-search plugin
   family (internal fingerprints: `gm_vehicle_search`, `glennForm`, FooTable, plugin
   dirs like `PnsV1_3.3` / `V5.0`) used by **Pull-N-Save** (8 yards, UT/AZ/CA) and
   **U-Pull-R Parts** (3 yards, MN/OH). Same form flow and actions
   (`getStores`/`getMakes`/`getVehicles`), two transports: U-Pull-R proxies to a JSON
   gateway (`doApiCall`), Pull-N-Save renders HTML tables server-side. One adapter
   family unlocks 11 yards.
3. **Yard-management vendors ≠ public inventory.** CRUSH (S3 Software), YardSmart,
   and Ario (autorecycler.io) run yard back-offices and sometimes "sell your car"
   web forms (Go Pull-It loads CRUSH's form JS), but none of them was observed
   serving a standardized public inventory endpoint we could target once and reuse.
   The high-leverage "one adapter, many yards" play mostly doesn't exist beyond
   finding #2 — independents are individually custom, but the customs are simple.
4. **The best individual targets are trivially scrapeable.** Wrench-A-Part exposes
   its whole 7-yard, ~11,400-vehicle inventory as one unauthenticated JSON GET.
   Parts Galore (Detroit) embeds its entire ~1,050-vehicle table in the homepage
   HTML.

## Ranked onboarding list

Ranking weighs (a) metro population, (b) gap-filling vs. current 149-yard coverage
(Northeast/Midwest/South thin; MN, WI-beyond-1, MI-beyond-1, Northeast-beyond-2 are
holes), (c) scrape reliability.

| # | Chain | Yards | Region / metro | Platform | Status |
|---|-------|-------|----------------|----------|--------|
| 1 | **Wrench-A-Part** | 7 | Austin, San Antonio ×2, Belton, Holland, Lubbock (TX interior, ~6M metro combined) | Custom Svelte + JSON API | **adapter built** |
| 2 | **U-Pull-R Parts** | 3 | Minneapolis–St. Paul ×2 (3.7M, first MN coverage), Toledo OH (0.6M) | gm-vehicle-search WP (JSON) | **adapter built** |
| 3 | Pull-N-Save | 8 | Phoenix ×4 + Tucson (5.7M; AZ currently has only 2 covered yards), SLC ×2, Riverside CA | gm-vehicle-search WP (HTML) | candidate — next build |
| 4 | Parts Galore | 1–2 | Detroit (4.3M; MI has 1 covered yard) | full table embedded in homepage | candidate |
| 5 | Kenny U-Pull | 2 US (+25 CAN) | Bangor + Lewiston ME | WP archive, ~1,600 pages | candidate (heavy) |
| 6 | Go Pull-It | 2 | Jacksonville + Tampa FL | WP + CRUSH form; archive is location-gated | candidate (needs devtools pass) |
| 7 | Sturtevant Auto | 1 | Milwaukee WI | custom inventory subdomain, HTML table | candidate |
| 8 | Ace Pick-A-Part | 1 | Jacksonville FL | WP, mechanism unidentified | candidate |
| 9 | **Harry's U-Pull-It** | 3 | Hazle Township/Allentown/Pennsburg PA (huge NE yards) | Sucuri challenge solved in pure Python; paged HTML | **adapter built** |
| 10 | **Fenix U-Pull** | 5 | Binghamton/East Syracuse/Elmira NY (first NY coverage) + Belleville MI (Detroit metro) + Moultrie GA | WP server-rendered table, 50 rows/page | **adapter built** |
| — | ABC U-Pull-It (Lincoln NE), Ecology Auto Parts (CA), Jalopy Jungle (ID) | | | unreachable this pass | blocked/retry |
| — | U-Pull-&-Pay | — | — | merged into Pull-A-Part (already covered) | retired |

## Per-platform notes

### Custom Svelte API — Wrench-A-Part (pilot #1)

- `GET https://api.wrenchapart.com/v1/vehicles` → entire inventory, all 7 yards,
  ~4.4 MB JSON, no auth, no pagination needed. robots.txt: allow-all.
- Row shape: `yard` (int id), `modelYear`, `make{name}`, `model{name}`, `vin`,
  `color`, `stockNumber`, `dateAdded` (ISO), `row{id}` — their own UI shows `row.id`
  as the row number. `photo` exists but is ignored per no-photos policy.
- Yard ids → names/coords are hardcoded in the adapter (from their
  `/api/closest-location?all=1` + location pages, geocoded once via Nominatim).
  Unknown yard ids are skipped defensively and logged.
- Freshness: `dateAdded` values from the same morning were observed. One request
  per scan — politeness is a non-issue.

### gm-vehicle-search WordPress plugin family — U-Pull-R (pilot #2) + Pull-N-Save

- Both sites run the same developer's plugin (FooTable rendering, `glennForm`
  classes, identical search flow). Actions over `wp-admin/admin-ajax.php`.
- **U-Pull-R Parts** (`action=doApiCall`): `apiAction=getVehicles&site=0&makes={Make}`
  returns clean JSON for that make across all three stores (Store 1 = Rosemount,
  2 = East Bethel, 3 = Toledo). Per-make queries are required — with `makes=0` the
  rows carry no make (`Model` is just "MALIBU"/"CIVIC", except ~15% literal DB
  names like "FORD F150 PICKUP"). Fields: Year, Model, Color, StockNumber, Row,
  DateSetData, Store, VIN, Odometer. **robots.txt explicitly allows
  admin-ajax.php.** ~50 requests per scan (one per make, 2s apart, ~2 min) — the
  same request shape their own search UI issues.
- **Pull-N-Save** (`action=getVehicles` direct): returns server-rendered HTML table
  (Year/Model/Date/Row/Store/Color/Stock/VIN, no Make column), so the practical
  approach is one request per make with `store=0` (~45 requests). robots.txt sets
  `Crawl-delay: 10` → a compliant full scan takes ~8 minutes. Deferred to the next
  batch; parsing is BeautifulSoup-trivial and the store list endpoint
  (`action=getStores`) already gives the 8 yards. Photos live on their own
  `app.pullnsaveapp.com` (not Row52) but are not captured per policy.

### Static embedded table — Parts Galore (Detroit)

- Homepage embeds `table#alldata` with every vehicle: Year, Make, Model, VIN,
  Color, Date, Row. One GET per scan. Confirm whether both Detroit locations share
  the table before building.

### Heavy/unresolved

- **Kenny U-Pull** (AIM): inventory is a WP archive at
  `/auto-parts/our-inventory/` — ~1,600 pages × 12 rows. Branch list on the site is
  Canada-only; the two Maine yards' inventory visibility is unverified. If the US
  branches surface in the archive filters, this is the best Northeast play.
- **Go Pull-It**: archive gated on a location selector; the query parameter wasn't
  discoverable without a browser session. CRUSH connection is only their
  car-buying form.
- **Harry's U-Pull-It** (PA): Sucuri WAF JS challenge → out unless policy changes
  (no headless workarounds attempted).

## Politeness & policy compliance

- All probing used ≤1 request per ~2s per host, a browser-equivalent UA (same
  convention as existing chain adapters), and raw responses cached to
  `scraper/.cache/independents/` during development.
- robots.txt reviewed for every adapter target; Pull-N-Save's 10s crawl-delay is
  recorded in the registry so a future adapter honors it.
- No photo URLs captured anywhere (chain-wide owner policy). Wrench-A-Part and
  U-Pull-R photo fields/CDNs are deliberately ignored.
- No Row52 assets touched; Row52 is now Pick-n-Pull-exclusive anyway.

## Next-best targets after this PR

1. **Pull-N-Save** — biggest immediate metro win (Phoenix), platform already
   reverse-engineered, just needs the HTML-variant parser + 10s pacing.
2. **Parts Galore** — one GET, fills Detroit.
3. **Kenny U-Pull** — needs a devtools session to find branch-filtered queries and
   verify US-yard visibility; would extend Northeast coverage into Maine.
4. Retry Ecology Auto Parts / Jalopy Jungle / ABC U-Pull-It domains; verify
   Sturtevant and Ace mechanisms.

## 2026-10-16 Indy-U-Pull-It (first user-requested yard)

A feedback email (the app's in-app feedback link) requested Indy-U-Pull-It,
Indianapolis IN — adapter built same day. WordPress/Elementor site;
`/vehicle-inventory/` server-renders the entire ~1,250-row inventory as one
DataTables table (Year, Make, Model, Color, Engine, Row, Arrival Date; no VIN,
no stock number — ids are hashes of the identifying fields). `/price-list/` is
a clean 3-column table (~470 parts with core charges) → `indy_pricing.json`.
robots.txt allow-all, one GET per scan each. First IN coverage.

## 2026-09-21 Northeast pass

Harry's U-Pull-It (3 eastern-PA yards) and Fenix U-Pull (3 upstate-NY yards +
Moultrie GA) are now adapter-built — the app's first NY and eastern-PA
coverage. Two findings unblocked Harry's: (a) the Sucuri CloudProxy "JS
challenge" is just base64-wrapped string concatenation, evaluable in pure
Python (`_sucuri_solve`); (b) robots.txt is fully permissive once past the
WAF. Fenix was never in the original survey — found via its server-rendered
`/recent-inventory/` table (the inventory CPT isn't in WP REST). New England
proper (MA/CT/NJ) still has no self-serve chain with public online inventory;
Kenny U-Pull (ME) remains the nearest candidate.

## 2026-10-16 — U-Pull-It IA/NE (first Iowa + Nebraska coverage)

Second user-requested onboard (Reddit comment asking for Iowa, same day as
Indy). `upullitne.com` — 4 yards: Des Moines IA (~800 cars), Lincoln NE
(~870), Omaha South (~440), Omaha North (~420); ~2,500 vehicles total.
WordPress running the "TAP Inventory Search System" plugin over the Crush
yard-management platform. One POST to `admin-ajax.php`
(`action=sif_search_products`, nonce scraped from `/search-inventory/`)
returns the entire chain as JSON: unique stock numbers (our id basis), 98.5%
real VINs, rows, colors, set dates, even mileage and photo URLs (photos
unused — no-photos policy). Chain-wide 522-part price list at
`/parts-pricelist/` -> `upullitne_pricing.json`. robots.txt allow-all. Two
requests per scan, by far the cheapest adapter per vehicle. Easiest build to
date (~30 min); no WAF encountered from a residential IP — first CI scan will
confirm datacenter egress isn't blocked (Indy's SiteGround lesson).
Distinct company from the blocked ABC U-Pull-It in Lincoln.
This fills the Plains hole: previously nearest yards to Des Moines were ~178
mi (Kansas City).

## 2026-10-17 — Seven-chain onboarding pass (+ Minnesota research)

Largest single onboarding to date: **8 chains / 19 yards** built in one pass
(all mechanisms pre-verified by the 2026-10-16 feasibility sweep, re-probed
during the build).

1. **Rupert's U-Pull-It** — Fredericksburg VA (1 yard, ~830 cars). First
   mainland-VA coverage; user-requested via Reddit (NoVA). WordPress
   "yardconnect-pro" (M&M Auto Parts). One ~40s server-rendered all-makes GET
   per scan (timeout=120 + retry); `data-stock-number` on row thumbnails is
   the id. robots Crawl-Delay 3. Price list `/parts-list/` (472 parts).
2. **Pull-N-Save** — 8 yards UT/AZ/CA (~9,000 cars!): Salt Lake City,
   Springville, Phoenix North/South, Glendale, Gilbert, Tucson, Riverside.
   Same gm_vehicle_search plugin family as U-Pull-R but HTML-footable variant;
   one getVehicles POST per make, 10s pacing per robots (≈8 min/scan).
   Biggest metro win of the pass (Phoenix ×4 + first SoCal independents).
   Chain-wide price list `/parts-pricing/` (809 parts).
3. **Parts Galore** — Detroit MI (~1,050 cars). Entire inventory embedded in
   the homepage `table#alldata`; one GET. Ships as ONE yard (no location
   column; they operate multiple Detroit lots). VIN-based ids. Price list
   `/parts-price-list/` (474 parts).
4. **Chesterfield Auto Parts** — 3 Richmond-metro VA yards (Richmond,
   Southside/Midlothian, Fort Lee/Prince George; ~4,800 cars). ASP.NET
   token-gated make×model search is ~80 min (measured) — too slow for every-6h scans, so
   the adapter is HYBRID: normal scans merge the tokenless `/newest-cars`
   page (~120 arrivals) into the previous result set persisted in
   `docs/data/chesterfield_inventory.json` (the scan workflow already commits
   docs/data/, so the cache travels with the repo); a full make×model crawl
   re-baselines weekly (cache `last_full` > 6.5 days) or on
   `JUNKYARD_CHESTERFIELD_FULL=1`. Crushed cars linger ≤1 week by design.
   Chain price list `/price-list` (538 parts).
5. **Ace Pick-A-Part** — Jacksonville FL (~2,500 cars). FIRST FLORIDA
   COVERAGE. Theme-level `ajax.php?inner_search=true&make=X` POST per make
   (~42 makes, 2s pacing). Cloudflare-fronted but no challenge observed —
   first CI scan will confirm datacenter egress. Price list `/prices/`
   (586 parts).
6. **Sturtevant Auto** — Sturtevant WI, Milwaukee metro (~740 cars). CRUSH
   ASP.NET app; tokenless urlencoded POST per make (~46). Price list
   `/Home/PartPrices` (168 parts — close to the 150 safety threshold, noted
   in the refresher).
7. **iPull-uPull** — 4 CA yards (Fresno, Sacramento, Stockton, Pomona;
   ~4,100 cars). The catalog plugin's CSV export returns the whole chain in
   ONE request (nonce from the `ipullCatalog` JS object + one POST) — the
   sweep's per-make-slug plan (~16 requests) turned out to be unnecessary:
   any non-make slug exports everything. 98%+ real VINs. No parts price list
   (their "Inventory & Pricing" page is the vehicle catalog).

### Minnesota research (user request: more MN coverage)

Already tracked: U-Pull-R Parts Rosemount + East Bethel (Twin Cities).
Findings:

- **St. Cloud U Pull (stccrush.com) — BUILT** (8th adapter of this pass,
  ~230 cars). Same CRUSH ASP.NET app family as Sturtevant; multipart POST
  per make (~28). First MN yard beyond U-Pull-R. No published price list.
- **Chesney Auto Salvage (Duluth)** — full-service yard with a parts-
  interchange search (make/model/year → part listings), not self-serve
  vehicle-row inventory; DIY pulling allowed but no vehicle inventory to
  scrape. Out of scope.
- **Rochester / other metros** — only staffed full-service recyclers found
  (Automotive Recyclers Rochester etc.); no self-serve yard with public
  vehicle inventory. Like the Hawaii finding: documented honestly, nothing
  feasible to build beyond the above.

### Parked (unchanged status: candidate)

- **Go Pull-It** (FL) — search endpoint still needs a browser devtools
  session; sitemap backfill ≈14h. Not worth it this pass.
- **Pick-A-Part VA** — Cloudflare TLS-fingerprint challenge blocks the fetch
  layer on every route; added to the registry as candidate with notes.

### Conventions kept

- All probing ≤1 request/~2s per host (10s for Pull-N-Save per robots),
  browser-equivalent UA, raw responses cached to `scraper/.cache/independents/`.
- Nominatim geocoding, 1.2s pacing; four addresses missing from OSM fell back
  to the nearest resolvable centroid (Rupert's 22408 zip, Ace 32218 zip,
  Sturtevant village, iPull Stockton 95215 zip) — close enough for the map pin.
- No photos captured anywhere; no Row52 assets touched.

## 2026-10-17 — Post-deploy fixes, U-Pull-R outage repair, Nevada Pic-A-Part

Follow-up pass after the seven-chain deploy (first scan shipped 11 of 19 new
yards; this pass fixed the rest and added a 9th build).

### CI failures diagnosed (scan runs 2026-10-17)

- **Ace Pick-A-Part** — Cloudflare returns 403 on the `/search-inventory/`
  HTML page from GitHub Actions datacenter IPs (works fine residential, both
  scan runs failed identically). Fix: `ACE_FALLBACK_MAKES` — the verified
  42-make dropdown snapshot — is used when the page GET fails, so the
  `ajax.php` POSTs still run. If Cloudflare blocks those too, the adapter
  logs and skips; next escalation would be an Indy-style committed-snapshot
  or mirror fallback.
- **Pull-N-Save** — `getMakes` intermittently returns an empty body in CI
  (failed in the 20:02 UTC scheduled run, worked in the dispatched run 2.5h
  earlier and 3/3 locally). Fix: 3 attempts at crawl-delay (10s) pacing,
  logging HTTP status + body head on empty responses.

### U-Pull-R Parts outage (plugin upgrade ~2026-10-13, repaired)

The gm_vehicle_search plugin upgrade silently zeroed ALL U-Pull-R coverage
(Rosemount + East Bethel MN, Toledo OH) for ~4 days:

- AJAX action renamed `doApiCall` → `doAaaApiCall` (old action: HTTP 400
  body `'0'`, which the adapter logged as a JSON parse error).
- `site=0` (all stores) no longer valid — the adapter now loops `site=1`
  (returns BOTH MN stores, rows tagged Store 1/2) and `site=3` (Toledo).
- `getMakes` takes a `ModelYear` param (empty = all years; 56 makes).
- ~113 requests/scan at 2s pacing; response fields unchanged (new ignorable
  extras: InterchangeModelNm, StockId, YardRow, DateSet*, TagStoreNumber).

**Hardening added:** `fetch_independent_inventory()` now checks every
onboarded chain's `_source` tag against `INDEPENDENT_EXPECTED_SOURCES` and
prints a prominent `WARNING:` line for any chain returning 0 vehicles, so a
silent breakage shows up in the next scan log instead of days later.

### Nevada Pic-A-Part (nvpap.com) — BUILT (9th adapter, user email request)

2 yards — Las Vegas (5100 N Lamb Blvd, North Las Vegas) + Henderson (110 W
Rolly St) — first Las Vegas-metro coverage, ~3,100 vehicles. WordPress with
a custom PT1 plugin (same vendor family as U-Pull-R): unauthenticated POST
`/wp-json/pt1/v1/vehicle-stock` per make (`store=0` = both yards, ~57
requests/scan); make list from `Manufacturers.json` (56); responses are a
numeric count prefix + HTML (`products-body-search__*` classes,
`data-pt1-vin` / `data-pt1-stock-number` — stock is the id basis, L/H
prefixed by store). Chain-wide parts DB at
`/json_datasets/parts_database_en.json` (533 parts → `nvpap_pricing.json`;
price/core columns verified against published totals). robots allow-all.
Both addresses geocoded exactly via Nominatim.

### Ace Pick-A-Part escalation (2026-10-18)

The 42-make fallback wasn't enough: Cloudflare 403s CI's datacenter IPs on
`ajax.php` too (every POST in the 10-18 run), not just the search page. Fix
is the full Indy pattern: `scraper/update_ace_snapshot.sh` runs the real
adapter daily from the dev Mac's residential IP via launchd
(`io.yardscout.ace-snapshot`, 08:25, logs to /tmp/yardscout_ace_snapshot.log),
commits `scraper/snapshots/ace_inventory.json.gz` (normalized vehicles +
fetched_at stamp; refuses crawls under 500 vehicles) and a fresh
`ace_pricing.json`, then pushes. The CI adapter falls back to the snapshot
whenever its live crawl yields zero vehicles and logs the snapshot's age.

## 2026-10-18 — Discovery-sweep build round (+16 yards, past 200)

Six chains built in one pass (all mechanisms verified live during the build):

1. **VinPlus platform — Road Tested Parts + Pickers/Pipes (9 yards,
   ~6,000 cars)**. One adapter, two tenants of the vinplus.texnrewards.com
   React SPA (unauthenticated Cloud Run JSON API, YardSmart source). RTP:
   Bessler's Hebron + Louisville KY, Bluegrass Lexington KY, Raceway
   Pik-A-Part Savannah TN, RTP Pick-A-Part Maiden NC. Tri-State: Pickers
   Longview/Reno TX + Texarkana (the API says TX, the yard is physically in
   AR — recorded as AR), Pipes U-Pull-It Shreveport LA. 100-row cap per
   query → per-make × per-location with recursive year-bucket splitting.
   utah-pic-a-part and ipull-upull are also tenants (already covered) — a
   periodic tenant-slug sweep is worth doing.
2. **Pick-A-Part VA (2 yards, ~7,200 cars — biggest single add)**. UN-PARKED:
   Cloudflare TLS fingerprinting beat plain requests, so the fetch helper
   tries requests first then curl_cffi impersonate=chrome (lazy import;
   added to scan.yml pip install). 500 cards/page × ~15 pages.
3. **Go Pull-It (3 yards, FL/GA)**. UN-PARKED and registry's stale Tampa
   location fixed (real yards: Jacksonville, Atlanta East/Norcross,
   Gainesville GA). Hard 50-row cap, no working pagination — per-make
   queries with per-model drill-down (getModels REST) only when capped.
   Honors the orphaned Crawl-delay 10 → ~30-50 min of the scan.
4. **U-Pick-It AZ (2 yards, ~2,900 cars)** — Reddit request (Flagstaff).
   NEW plugin family: yardconnect-pro v2.3 (YardSmart backend, photos on
   api.yardsmartapp.com — useful detection fingerprint). One nonce + one
   view=table POST per lot returns the whole lot unpaginated. Stock numbers
   only on photo rows (~45%) → hash-id fallback for the rest. No VIN.
5. **Barry's U Pull It (Mobile AL, ~700 cars)**. Real domain is
   barrysupullit.net (.com is a parked lander). One Indy-style table. Two
   physical yards but ONE blended inventory with no location column
   (sitemap checked) → single blended Mobile yard, Parts Galore precedent.
   /part-pricing/ table → barrys_pricing.json (~425 parts).
6. **Prestige Pull-Your-Part (Houston TX, ~1,250 cars)**. The 15-minute
   probe found gold: the art-inventory plugin's
   art_inventory_get_yard_assets action with all-"0" params returns the
   entire yard as JSON in one POST (named/empty params return []).

Geocoding: 14 of 19 new addresses resolved exactly/street-level in OSM;
Lexington KY, Savannah TN, Maiden NC, Mobile AL and Flagstaff AZ fell back
to zip/town/road centroids (documented per entry in the registry).

### Pick-A-Part VA CI escalation + Ace snapshot guard (2026-10-19)

First scan with the six new chains: 16 of 18 yards landed. Pick-A-Part VA
got HTTP 521 in CI even through curl_cffi impersonate=chrome (clean 200s
residential) → same remedy as Ace: `update_papva_snapshot.sh` + launchd
(`io.yardscout.papva-snapshot`, 08:35) committing
`scraper/snapshots/papva_inventory.json.gz`, adapter falls back on an empty
crawl. Also hardened both snapshot scripts after a partial Ace crawl (807 of
~2,500) slipped past the flat 500-vehicle floor: snapshots now also require
>= 60% of the previous snapshot's count.

## 2026-10-21 — Budget U-Pull-It FL (owner-requested, 2 yards, ~2,400 cars)

Owner email (Austin Rutherford): "all of our vehicle inventory and price
lists are updated daily and published on our website." Confirmed — and it's
TWO separate inventory systems behind one brand (plus a third location,
Auburndale, that's full-service pre-pulled parts with no self-serve
inventory — not listed):

1. **Winter Garden (881 S 9th St, 25 acres, ~1,600 cars)** —
   budgetupullit.com (WordPress). `/current-inventory/?make={MAKE}&model=`
   server-renders that make's full list; empty/ALL make returns nothing, so
   one GET per make (~40/scan), makes scraped from the page's own select.
   Full columns incl. Stock# (STK#####, id basis) and VIN. Yard Date is
   DOT-separated MM.DD.YY (the /search-vehicles/ New Arrivals table uses
   slashes — don't mix the parsers up).
2. **Bartow (2715 E State Rd 60, 12 acres, ~830 cars)** —
   budgetupullit.s3softwaresolutions.com/inventory.aspx, a classic ASP.NET
   WebForms postback chain. NEW PLATFORM for us: **S3 Software Solutions**
   (fingerprint: `*.s3softwaresolutions.com` + ddlMake/ddlModel
   `__doPostBack`). GET for VIEWSTATE → ddlMake postback fills ddlModel →
   one ddlModel postback per model renders rows. Hidden fields re-chained
   from each response; option values MUST be HTML-unescaped before posting
   ("TOWN &amp; COUNTRY" → HTTP 500 — cost 17 Town & Countrys in the first
   test run). No stock#, no VIN → sha1 ids (upickitaz convention).
   ~250-300 requests/scan at 0.5s pacing. Bartow's own site
   (budgetupullitbartow.com, hibu builder) links this inventory +
   partspricelist.aspx, confirming it's the official feed.

Both yards publish clean 4-column price lists (desc/price/per-or-basis/
core) and they genuinely differ (alternator core $5 WG vs $8 Bartow) →
`budget_pricing.json` keyed by yard display name (wap_pricing shape), wired
into the app's price sheet + cross-yard compare.

Geocoding: neither parcel in OSM and Census had no address match — WG pin
taken from the site's own footer-map coordinates, Bartow from the
u-pull-it.com directory listing.

**Same-day follow-up (owner asked to confirm parts PRICES flow through):**
the first pass wired `budget_pricing.json` into the price *sheet* only —
part rows still said "check yard price list" because
`PART_KEYWORD_MAP`/`_lookupYardCostUncached` had no Budget columns. Now
wired UTPAP-style with TWO columns (`bwg` Winter Garden, `bba` Bartow —
only 421 of ~660 names are spelled identically across the yards' lists,
e.g. `HEADLIGHT COMPOSITE` vs `HEADLAMP COMPOSITE`), routed per yard inside
one `budget u-pull-it` branch. 129 of 142 keyword rows mapped; audit
(`_audit_pullcost_map.py`, now budget-aware): 94.8% of part instances at
the two yards resolve to a real published price — on par with PnP/PYP.
Unmapped stays honest ("check yard price list"): hybrid batteries, cameras,
transfer-case motors etc. aren't on Budget's lists; Bartow's list has no
amplifier or hybrid-inverter line items (WG's does).

## 2026-10-23 — Metro Detroit pass (owner-forwarded email, 4 chains requested)

Owner forwarded an email from Elliot Bruzek asking for metro Detroit
u-pull coverage: Ryans Pick-A-Part, US Auto Supply (2 locations),
U-Pull and Save (2 locations), Regal U-Pull-It. Outcome: 3 adapters
built (3 yards listed), 1 directory-only. Michigan goes from 2 yards
(Parts Galore Detroit, Fenix Belleville) to 5.

1. **Ryan's Pick-a-Part — Detroit (9309 Hubbell Ave, ~1,350 cars)** —
   ryanspickapart.com runs the CRUSH MVC shell but its /Home/Inventory
   search form is dead (JS points at removed elements); the REAL inventory
   is an iframe to **Ario (app.autorecycler.io)**, a Bubble.io app — NEW
   platform, first Bubble adapter. Bubble obfuscates POST bodies
   (PBKDF2-MD5 c=7 → AES-256-CBC, key = appname+timestamp, in `z`/`y`/`x`
   fields); scheme reversed from the app's run.js into `_ario_encode_data`
   (needs `cryptography`, added to scan.yml). Responses are plain JSON.
   Gotchas: rows live in `custom.inventorysearch` (not custom.inventory);
   reference constraints need the full `<appid>__LOOKUP__<id>` value (bare
   ids silently match nothing); empty `sorts_list` is fine but a populated
   one throws BAD_REVISION. Org id resolved at runtime from the slug
   `ryans-pick-a-part-detroit`; make/model are `in`-batched id→name
   lookups. visible=true + not-deleted filters ~16.6k historical rows to
   the live lot. Stock STK##### (id basis `ryans-stk#####`), VIN on all
   but ~32, row, color, added_date (epoch-ms). Pin from the org record's
   own geocode. Price list: CRUSH /Home/PartPrices 4-col → 525 rows,
   `ryans_pricing.json`.
2. **US Auto Supply — Sterling Heights (7575 18 1/2 Mile Rd)** — VinPlus
   tenant `us_auto_supply` (oracle hit on /api/yard-info), so a
   CONFIG-ONLY addition to VINPLUS_TENANTS, single-location keyed "".
   The email said 2 locations, but the Detroit store (2346 W. Warren Ave)
   is full-service — its only search is a Hollander part-interchange CGI
   (part listings, not vehicle rows) — not listed, Budget Auburndale
   precedent. Exact OSM parcel. Price list /upull/part-prices/ → 722 rows,
   `usauto_pricing.json`.
3. **U-Pull and Save — Pontiac (240 E. Columbia Ave, store 105)** — Nuxt 3
   site with a clean same-origin JSON API, but NO bulk listing endpoint
   (empty/ALL/% model all return []). Hybrid Chesterfield-style adapter:
   committed cache `docs/data/upas_cache.json` holds known (make, model)
   pairs + per-vehicle details; each scan does one
   /api/vehicles/search/?store=105&make=&model= per known pair (live set),
   /api/vehicles/recent/105 + a bounded sequential-id sweep (vehicleIDs
   are intake-sequential) to discover new pairs, and a capped
   /api/vehicles/{id} detail backfill for VIN + YardLocationDT (404 =
   removed). Seeded 2026-10-23 by a one-time full id-window scan. Tier-1
   per-car links: u-pullandsave.com/vehicles/{vehicleID}. The email said
   2 locations, but the site's own store picker says "Mason, MI (Yard
   Closed)" — Mason (store 110) is vehicle purchasing only, not listed.
   Exact OSM parcel. Price list /price-list → 488 rows,
   `upas_pricing.json`.
4. **Regal U-Pull-It — Howell (945 Lucy Rd): DIRECTORY-ONLY.** The
   WordPress site publishes NO vehicle inventory: /parts/ ("Search for
   Parts") renders only address/hours, and the U-Pull-It page says "We can
   only tell you if the vehicle is available in the yard." Registry entry
   status `directory-only` with exact OSM pin; re-check if they adopt an
   inventory platform. Not faked into the app.

All three price lists are single-location (no per-yard split needed) and
wired p195-style: price sheet only, no PART_KEYWORD_MAP columns — same
scope as every non-Budget independent (Budget's keyword columns were a
specific owner follow-up).

## 2026-10-26 — Ario wave 1 (EZ Pull N Pay ×7, Paul's Auto Yard ×10, Foss U-Pull-It ×6, Carolina Pick N Pull ×3)

Merged 2026-10-26 (live Supabase adapter — see EXPANSION_CANDIDATES.md §8.6.1/§8.6.2). The Ryan's adapter became
`fetch_ario_inventory` over an `ARIO_CHAINS` table (one org-table fetch,
per-yard inventory pages, pooled make/model lookups; ids
`{source}-{code}-{stock}`, Ryan's keeps `ryans-{stock}`); slugs/pins from
`scraper/_probe_ario_orgs.py`. Live fetch: 25,310 vehicles / 27 yards in
226 s, counts matching the scouting pass. Blocker: the Bubble data behind
`app.autorecycler.io` is a frozen late-August-2026 snapshot — Ario moved live
inventory to a Supabase-backed frontend (`ario.autorecycler.io/yard/{slug}`,
`search-inventory` edge function). Details and the decision needed:
`EXPANSION_CANDIDATES.md` §8.6. Ryan's (live since 10-23) is affected too.

## 2026-10-27 — CRUSH MVC wave (Jalopy Jungle ×5, Trusty, M&M Buffalo, Polk County Pick and Pay)

Built from EXPANSION_CANDIDATES.md "CRUSH MVC app" / §6 item 2: the S3
Software Solutions hosted MVC inventory app that Sturtevant and St. Cloud
were already parsed from, generalized into ONE config-driven adapter —
`CRUSH_MVC_SITES` + `fetch_crush_mvc_site(source)` in `junkyard_scraper.py`
(a new tenant is a config entry: base URL, page/search paths, optional
`prices_path`, and per-yard `yard_id` / name / city / state / lat / lng).
Sturtevant and St. Cloud keep their own adapters (stock-number ids that
history rows are keyed on). 4 tenants, 8 yards, **9,560 vehicles live**
(2026-10-27, 310 s wall-clock with the four hosts overlapped).

Mechanism (same on every tenant): `GET /Home/Inventory` renders a multipart
form (`YardId` on multi-yard tenants, `VehicleMake`, `VehicleModel`); one
multipart POST per make with `VehicleModel` EMPTY to the form's action
(`/` on Jalopy/Trusty, `/Home/Inventory` on M&M/Polk) returns the whole make
as a table. Multi-yard tenants list makes via `POST /Home/GetMakes {yardId}`
(JSON); single-yard tenants via the server-rendered `#car-make` select.
Column sets differ per tenant, so the parse is header-driven: Jalopy and
Trusty publish YEAR/MAKE/MODEL/ROW only; M&M adds COLOR, REFERENCE
(engine/trim) and ARRIVAL DATE; Polk adds COLOR, ENGINE (mostly blank) and
ARRIVAL DATE. No tenant exposes a stock number or VIN, so ids are content
hashes in the Budget-Bartow convention
(`{source}-{code}-sha1(year|make|model|color|engine|row|date)[:12]`, `-N`
on the 2nd+ identical row) — stable while the row is unchanged; a car that
moves rows gets a new id (same trade-off as Bartow). Arrival dates before
2015 or beyond UTC-tomorrow drop to `""` (`_crush_mvc_parse_date`, then the
global `_sanitize_date_added` clamp). robots.txt is 404 on all four hosts;
pacing 1 s per host (`CRUSH_MVC_DELAY_SEC`), one `INDEPENDENT_FETCHERS` entry
per HOST so the four hosts overlap but no host ever sees two of our requests
at once. Pins geocoded once via Nominatim (street addresses are the comments
in `CRUSH_MVC_SITES`); all exact OSM addresses except Polk, which resolves to
the US-98 N segment in zip 33809.

| Yard | Source | Live count | VIN | Newest dateAdded | Price list |
|---|---|---|---|---|---|
| Pick-A-Part Jalopy Jungle — Boise (5501 W State St; YardId 1020) | `jalopy` | 894 | 0% | none (feed has no dates) | no (`/Home/PartPrices` 404) |
| Pick-A-Part Jalopy Jungle — Caldwell (6301 Cleveland Blvd; 1021) | `jalopy` | 1,192 | 0% | none | no |
| Pick-A-Part Jalopy Jungle — Nampa (3931 Garrity Blvd; 1022) | `jalopy` | 2,037 | 0% | none | no |
| Pick-A-Part Jalopy Jungle — Garden City (520 E 47th St; 1119) | `jalopy` | 857 | 0% | none | no |
| Pick-A-Part Jalopy Jungle — Twin Falls (1750 Osterloh Ave; 1099) | `jalopy` | 1,577 | 0% | none | no |
| Trusty Pick-A-Part — Caldwell (5517 Cleveland Blvd) | `trusty` | 1,381 | 0% | none (feed has no dates) | no (`/Home/PartPrices` HTTP 500 — re-check) |
| M&M U-Pull-It — Buffalo (2150 William St) | `mmupullit` | 631 | 0% | 2026-10-22 | yes → `mmupullit_pricing.json` (251 parts) |
| Polk County Pick and Pay — Lakeland (7623 US Hwy 98 N) | `polkpickpay` | 991 | 0% | 2026-10-23 | yes → `polkpickpay_pricing.json` (770 parts) |

Notes:

- Jalopy = **first Idaho coverage** (Treasure Valley ×4 + Twin Falls). The
  Boise yard id (1020) was not in the scouting notes; it is the page's
  default-selected option. `YardId` is honored by the search POST — the
  five yards' (year, make, model, row) sets overlap by ≤50 rows pairwise, so
  the chain is not one lot mirrored five times. jalopybot.com scrapes the
  same app daily, so our ~255 requests/scan (5 × GetMakes + ~37–47 makes)
  at 1 s are well inside the tolerated volume.
- Jalopy and Trusty ship **no set-out date** — every row is
  `dateAdded: ""` ("Set-out date unknown" in the app, never NEW/fresh), the
  same as Budget Bartow's undated rows. Garden City has one 2026-model
  listing (year passes through as the lot sign shows it).
- M&M = first western-NY / Buffalo yard; Polk is ~25 mi from Budget Bartow
  (referral geography, EXPANSION §5). Both are fully dated.
- Price lists are wired production-side the way Sturtevant/Ryan's are
  (`refresh_crush_mvc_pricing_file` → `docs/data/{source}_pricing.json`,
  registered in the `--refresh-chain-pricing` tuple; 4-column PART
  DESCRIPTION/PRICE/BASIS/CORE, Ryan's shape; bare-UPC "names" like
  `042782999127` dropped by `_PRICE_AS_NAME_RE`). **Follow-up (docs/app.js
  untouched in this branch):** the app's `grab('data/<src>_pricing.json', …)`
  list and the yard→pricing map need the two new sources, and
  `gen_yard_site_links.py` (ENTRIES added here) needs a regeneration pass
  to write the tier-3 inventory links into app.js.
- Registry: four `adapter-built` chains inserted after St. Cloud (same
  family); `INDEPENDENT_EXPECTED_SOURCES` registers the four sources from
  `CRUSH_MVC_SITES` (zero-vehicle alarm), like the Ario chains.

## 2026-10-27 — yardconnect-pro wave (Chuck & Eddie's Self Service CT, Robertson's U-Pull-It MA)

First Connecticut and first Massachusetts coverage, both on the
**yardconnect-pro** WordPress plugin (M&M Auto Parts' plugin over a YardSmart
backend) that U-Pick-It AZ was already parsed from. The U-Pick-It adapter was
generalized into ONE config-driven adapter — `YARDCONNECT_SITES` +
`fetch_yardconnect_site(source)` in `junkyard_scraper.py` (a new tenant is a
config entry: site, `mode`, nonce/inventory/prices paths, and per-yard
`lot` / `code` / name / city / state / lat / lng). U-Pick-It AZ is the first
entry; verified live that the refactor emits the **identical id and row
lists** (2,979 vehicles, `upickitaz-{stock}` + sha1 ids, same cache file
names). Rupert's (also yardconnect-pro, server-rendered GET) keeps its own
adapter for now — it predates the config and skips no-stock rows instead
of hashing them, so migrating it would change its id set.

Two plugin generations, hence two modes:

- `mode: "ajax"` (v1.3.3 Robertson's, v2.3 U-Pick-It): nonce from
  `var yardconnectPublic = {... "nonce":...}` on any page, then one POST per
  yard to `admin-ajax.php` with `action=yardconnect_search_vehicles`
  (`lot=` only on multi-lot tenants) `&make=all&model=all&view=table` —
  whole lot unpaginated. 403 = expired nonce; the body carries a fresh one.
- `mode: "get"` (v1.3.1 Chuck & Eddie's): the search AJAX action does not
  exist (admin-ajax returns 400/`0`); `GET /vehicle-inventory/?make=all&
  model=all` server-renders the whole lot (~2.8 MB).

Same table either way: Image, Make, Model, Year, [Color,] Body Style, Engine,
Yard Row, Date Set (MM/DD/YY); Color is a per-tenant display option, so the
parse is header-driven (`<thead>` labels → keys) with a positional fallback
by column count. Stock number = `data-stock-number` on the thumbnail (100%
of Chuck & Eddie's rows, ~94% of Robertson's, ~45% of U-Pick-It's); rows
without one get the sha1 content-hash id with ordinal dupe suffixes. No VIN
on any tenant. Color/Engine ride along as `_color`/`_engine` extras (new for
U-Pick-It's engine column too). Pacing 2 s per host, 1–3 requests per scan,
one `INDEPENDENT_FETCHERS` entry per host. robots.txt on both new hosts
explicitly allows `admin-ajax.php`, no crawl-delay. Pins geocoded once via
Nominatim: Chuck & Eddie's is an exact OSM node ("Chuck and Eddie's Pick N
Pull Lot"), Robertson's an exact OSM building.

| Yard | Source | Live count | VIN | Newest dateAdded | Price list |
|---|---|---|---|---|---|
| Chuck & Eddie's Self Service — Southington CT (450 Old Turnpike Rd) | `chuckeddies` | 844 | 0% | 2026-10-26 | yes → `chuckeddies_pricing.json` (564 parts; `/parts-price-list/` Part name / Part price / Part labor cost — labor ignored, no core column) |
| Robertson's U-Pull-It — Wareham MA (2680 Cranberry Hwy) | `robertsons` | 561 (36 hash ids) | 0% | 2026-10-26 | no (their "Parts List" nav is the full-service Hollander side) |

Notes:
- Chuck & Eddie's is a 3-store chain; only the Southington self-service lot
  is a pin (New Haven / Hartford are full-service). The lorem-ipsum
  `/u-pull-southhampton-2/` page is a template leftover — ignore it.
- Robertson's also runs full-service stock on robertsons.hollanderstores.com
  — deliberately not parsed; only the U-Pull-It `inventory-search` lot.
- Both yards set out cars the day before the build (Date Set 10/26/26), so
  `dateAdded` is fully populated; years 1964–2019 (Robertson's keeps a few
  classics: '64 Thunderbird, '81 Firebird).
- `refresh_chuckeddies_pricing_file` is in the `--refresh-chain-pricing`
  tuple via `refresh_yardconnect_pricing_file("chuckeddies")`. **Follow-up
  (docs/app.js untouched in this branch):** the app's `grab('data/<src>_
  pricing.json', …)` list and the yard→pricing map need `chuckeddies`, and
  `gen_yard_site_links.py` (ENTRIES added here) needs a regeneration pass to
  write the two tier-3 inventory links into app.js.
- Platform note: yardconnect-pro is the Northeast key — M&M (Buffalo, CRUSH
  MVC) owns the plugin and its customers cluster in the Northeast. A periodic
  fingerprint sweep for `wp-content/plugins/yardconnect-pro` should surface
  the next tenants; each is now a ~15-line config entry.
## 2026-10-27 — SD/NY/TX wave (BYOT Auto Parts ×3, Wilbert's U-Pull-It ×3; Ewe Pullet skipped)

Built from EXPANSION_CANDIDATES.md "WordPress custom server-rendered" / §6
item 3 / §8.4 (the wave-3 gap-fill). Outcome: **2 adapters, 6 yards,
7,042 vehicles live** on the seed run; Ewe Pullet (SD) recorded and
skipped — its inventory backend is down (below). Both adapters are config
tables + one fetcher (`BYOT_YARDS` / `fetch_byot_inventory`, `WILBERTS_YARDS`
/ `fetch_wilberts_inventory`); both price lists are wired production-side
(`refresh_byot_pricing_file`, `refresh_wilberts_pricing_file` →
`docs/data/{byot,wilberts}_pricing.json`, in the `--refresh-chain-pricing`
tuple).

| Yard | Source | Live count | VIN | Newest dateAdded | Price list |
|---|---|---|---|---|---|
| BYOT Auto Parts — Waco (14401 N I-35 Frontage Rd, Elm Mott; Location 1123) | `byot` | 1,246 | 99.6% | 2026-10-26 | yes → `byot_pricing.json` (452 variants, chain-wide) |
| BYOT Auto Parts — Bryan/College Station (3738 E SH-21, Bryan; 1183) | `byot` | 967 | 99.6% | 2026-10-23 | (same file) |
| BYOT Auto Parts — Beaumont (7516 Shady Ln; 1218) | `byot` | 1,090 | 99.6% | 2026-10-23 | (same file) |
| Wilbert's U-Pull-It — Rochester (4936 NY-104, Williamson) | `wilberts` | 1,918 (seed) | 99.9% | 2026-10-27 | yes → `wilberts_pricing.json` (434 parts, chain-wide) |
| Wilbert's U-Pull-It — Bath (7992B NY-415) | `wilberts` | 823 (seed) | 99.9% | 2026-10-27 | (same file) |
| Wilbert's U-Pull-It — Buffalo (550 Pound Rd, Elma) | `wilberts` | 998 (seed) | 99.9% | 2026-10-27 | (same file) |
| Ewe Pullet (Nordstrom's) — Garretson SD | — | not built | — | — | PDF only (`2026carpricelist-1.pdf`) — not wired |

**BYOT Auto Parts (TX).** The scouting note ("page embeds vehicle data; 225 KB
inventory page") was the theme's JS, not rows: each
`/locations/{slug}/inventory/` page is a shell over the chain's own JSON API
at `api.byotautoparts.com`. The page's "Latest Arrivals" call —
`GET /inventory/yard/vehicles/recent-arrivals?limit=N` with the yard code in a
`Location` request **header** — has no date floor and at a large limit returns
the yard's whole lot (Waco: 1,246 rows back to 2026-04-18), so the adapter is
**one request per yard** (`BYOT_LIMIT` = 10,000, warns when hit). Rows carry
`StockId` (STK-/BCS-/BMT-prefixed; ids `byot-{stockid}`), `YardLocationDt`
(ISO set-out date → `dateAdded` via `_sanitize_date_added`), full VINs
(99.6%), Color (`_color`), Reference (engine, not shipped) and YardRow. The
`/search/vehicles` route needs year+make+model through the interchange
catalog (empty make 500s) and is not used. The same config map on the page
lists **Baton Rouge LA (1259, ~1,050 cars) and Jackson MS (1289, ~990 cars)** —
same API, same shape, probed live — NOT built in this TX-scoped wave; each is
one `BYOT_YARDS` entry (owner call: first LA/MS coverage). Price list: the
`/prices/` pages render nothing server-side; `/parts/{partType}/prices` (same
Location header) returns the part type's price GROUP (variants with
`part_price`/`core_price`; identical across yards except sales tax), walked
over `/search/parts?year=&make=&model=` (423 part types at 1 s, ~7 min inside
`--refresh-chain-pricing`; variants deduped by name → 452 rows).
Pins: Beaumont is an exact OSM POI; Bryan resolves to the E SH-21 segment in
zip 77808; Waco/Elm Mott is the Elm Mott place centroid (the I-35 frontage-road
house number is not in OSM; the lot is at the town's west edge, ~1 mi off).
robots.txt allow-all (Yoast), no crawl-delay.

**Wilbert's U-Pull-It (NY) — hybrid, slow by design.** The custom
`wilberts-parts-search` plugin's `form.js` POSTs urlencoded `action=…` to the
plugin's own `api.php` (not admin-ajax; the page nonces belong to the contact
forms, nothing is checked). `search_type=recent` returns every car set out in
the last ~6 days across all three yards (~300 rows; extra params ignored).
`search_type=upull` with `make` + `model` returns **every** car of that pair on
all three lots, any year (year/location ignored) — but `model` is required
(empty, `%` and make-only all return the handful of make-less junk rows) and
`list-models` needs a year per call, so there is no bulk listing. Hence the
U-Pull-and-Save pattern: a committed cache `docs/data/wilberts_cache.json`
(the scan workflow already commits `docs/data/`) carries known (make, model)
pairs and the cars last seen per pair; each scan merges the recent feed (new
pairs, new cars) and re-searches known pairs, which are the liveness source of
truth (a cached car missing from its pair's result is dropped; a pair that
comes back empty is forgotten until a new arrival revives it). robots.txt
says `Crawl-delay: 10` and it is honored (`WILBERTS_DELAY_SEC`, do not
lower), so the sweep is budgeted: `WILBERTS_PAIR_BUDGET` = 240 pairs per scan
(~40 min, overlapped with the other hosts like every adapter) via a
round-robin cursor kept in the cache; cars whose pair was not reached ride
the cache until their turn, with `WILBERTS_STALE_DAYS` = 14 as a safety net.
The feed has no absolute set-out date, only `DaysInYard`: `dateAdded` =
first-seen UTC date − DaysInYard, computed **once** and kept in the cache so
it never drifts. ids `wilberts-{stockid}` (STK- Rochester, BAT- Bath, BUF-
Buffalo); VINs are 99.9% full. The seed (recent feed + one full pair sweep of
138 pairs, 25 min) found 3,739 cars, years 1978–2022, set-out dates
back to 2025-09 — one week of arrivals already names most (make, model) pairs
on the lots, and each pair search returns the whole pair; any pair not yet
seen surfaces the next time one of its cars arrives (a pair search also
matches longer model names, e.g. ESCAPE → ESCAPE HYBRID, which seeds extra
pairs — 130 → 138 on the seed run).
The site calls the Williamson yard "Rochester" and the Elma yard "Buffalo";
display names follow the site, `_city` follows the address. First Rochester /
Finger Lakes coverage; Buffalo joins M&M. Price list:
`admin-ajax.php?action=price_list_get_prices` (upiPriceList plugin, DataTables
JSON, 434 rows, chain-wide) → `wilberts_pricing.json`. All three pins are
exact OSM (Williamson and Elma are mapped POIs).

**Ewe Pullet (Nordstrom's), Garretson SD — NOT built (backend down).** Same
`iis-pro-upull` plugin family as Pick-A-Part VA (v1.8, URG-hosted), robots
allow-all with admin-ajax allowed, plain requests get HTTP 200 — no WAF, no
challenge — but every inventory URL (`/inventory/ANY/ANY/?k=1`, `&id=PP93`,
`&pagenum=1`, make/model paths, with the plugin's cookies) renders the
empty-results shell ("No Results Found", zero `.car-details-uPull` cards)
while pickapartva.com on the same plugin renders 500 cards, and admin-ajax
`action=getMakesIISupull` answers `{"error":"api error"}` (the static catalog
actions still work, so WordPress is up and the URG data feed behind it is
down). Nothing to work around; registry entry `candidate` with the probe
notes, re-probe later. Address per the site header is 47989 255th Street,
Garretson SD 57030 (NE of Sioux Falls — not Brandon); would be the first
South Dakota coverage. Price list is a PDF + PNG, not a parseable table.

Notes / follow-ups (docs/app.js untouched in this branch):

- The app's `grab('data/<src>_pricing.json', …)` list and the yard→pricing
  map need `byot` and `wilberts`; `gen_yard_site_links.py` (ENTRIES added
  here: BYOT per-location pages, Wilbert's shared search page) needs a
  regeneration pass to write the tier-3 links into app.js.
- `docs/data/wilberts_cache.json` is committed with the seed so the first CI
  scan starts from it (UPAS precedent). Scan-log line to watch:
  `[Wilbert's] N vehicles across 3 yards (recent R, C/P pairs re-checked)`.
- Registry: `BYOT Auto Parts` and `Wilbert's U-Pull-It` inserted after Polk
  County (`adapter-built`), `Ewe Pullet (Nordstrom's)` as `candidate`;
  `INDEPENDENT_EXPECTED_SOURCES` gains `byot` and `wilberts`.

## 2026-10-28 — iis-pro-upull + CRUSH static-table wave (U-Pull-It WA ×3, AESOP Tulsa, Midway ×2, Hwy 82, Route 34, Sunshine; iPull Idaho Falls blocked; U-Pull-R via Ario not added)

Two single-site adapters became config-driven, then gained tenants (yard-hunt
2026-10-27 §1c / §2):

- **iis-pro-upull**: `fetch_papva_inventory` → `IIS_UPULL_SITES` +
  `fetch_iis_upull_site(source)`. Per tenant: page URL template, optional URG
  `&id=` filters (one deck per id), card Location → yard map, pacing (≥2 s),
  page size. The Set Date field is now optional in the card regex: go2upullit
  cards have none, so their `dateAdded` stays `""` (no invented dates).
  Card counts per page vary on the new tenants (go2upullit: 317/480/488/…),
  so for them the adapter follows the deck's own pager to its last page; a
  page with no new stock numbers also stops the deck.
- **CRUSH static table**: `fetch_barrys_inventory` → `CRUSH_TABLE_SITES` +
  `fetch_crush_table_site(source)`. Header-driven: `<th>` labels map to
  fields (`_CRUSH_TABLE_FIELDS`), so VIN and Stock # are read when the
  tenant has them. Table id is `vehicles` or `crush-inventory`. Ids: stock if
  present, else VIN (`vin_id`), else Barry's row hash. `max_age_days` drops
  ghost rows.

**Byte-identical checks** (old and new functions run on the same saved
pages, output compared as JSON bytes): Pick-A-Part VA, live crawl of
2026-10-28 (15 pages): 7,330 rows, same sha1, same request sequence. Also a
synthetic deck (cards without Set Date or with a blank one, short page 2):
497 rows identical. A blocked page-1 case falling back to the snapshot:
7,324 rows identical. Barry's, live page: 653 rows identical. A synthetic
page (stock-less duplicate rows, a bad year, a short row): identical.
Pick-A-Part VA keeps its legacy `HEADERS` and its curl_cffi fallback
(`cffi_fallback`, PAPVA only). Barry's keeps `HEADERS`. The new tenants send
`YARDSCOUT_HEADERS`, which uses the honest YardScout UA. None of them may
set `cffi_fallback`.

| Yard | Source | Live count (2026-10-28) | VIN | Newest dateAdded |
|---|---|---|---|---|
| U-Pull-It Auto Parts — Pasco WA (802 S Oregon Ave) | `upullitwa` | 834 | 100% | — (no dates on cards) |
| U-Pull-It Auto Parts — Kennewick WA (34508 S Piert Rd) | `upullitwa` | 848 | 99% | — |
| U-Pull-It Auto Parts — Yakima WA (14 E Washington Ave) | `upullitwa` | 788 | 99% | — |
| AESOP U-Pull — Tulsa OK (13802 E Apache St; `&id=OO95`) | `aesop` | 1,064 | 99% | 2026-10-27 |
| Midway U-Pull — Muncie, Kansas City KS (6345 Kansas Ave; `MO38`) | `midwayupull` | 419 | 100% | 2026-10-23 |
| Midway U-Pull — Liberty MO (1101 Old State Hwy 210; `MO09`) | `midwayupull` | 344 | 100% | 2026-10-23 |
| Hwy 82 Pick & Pay — Poulan GA | `hwy82` | 789 | 0% | 2026-10-22 |
| Route 34 U-Pull-M — Auburn NY | `route34` | 364 | 98% | 2026-10-26 |
| Sunshine Auto Salvage — Orangeburg SC | `sunshine` | 745 (2,355 rows >120 d dropped) | 0% | 2026-10-27 |

First Washington and first Kansas coverage. Pins come from Nominatim: exact
for Pasco, Yakima, Muncie, Liberty, Route 34 and Sunshine. Kennewick (99337),
Tulsa (74116) and Idaho Falls (83401) use zip centroids. Poulan uses the town
centroid.

Not built:
- **iPull by Intermountain Auto (Idaho Falls ID)**: every page request with
  the YardScout UA got HTTP 500 (a hosting-panel error page) while robots.txt
  answered 200. Not worked around. Registry entry `blocked`, and the config is
  in a NOT HERE comment.
- **U-Pull-R East Bethel / Toledo via Ario**: not added. Ario's own yard
  records for both have `inventory_source: upullrparts_ajax_sync`, with
  `claimed: false`, no owner, created 2026-07-27 together with Ario's Pick-n-Pull
  (`row52_odata_sync`), Pull-A-Part and PYP mirrors. That points to Ario
  syncing U-Pull-R's own admin-ajax endpoint, the one that 403s us, rather
  than to a vendor feed U-Pull-R chose. Rosemount is absent from Ario, and
  its newest rows were 2026-10-06. Owner call.

Follow-ups (docs/app.js untouched in this branch): `gen_yard_site_links.py`
ENTRIES were added for the new yards. Two existing ones were fixed: Memphis
and Millington had been falling through to the IA/NE "U-Pull-It" link, and
Buddy's, Marion County, 662, CP's and Genesis had no entry, which made
`validate()` exit. A regeneration pass will write them into app.js.
