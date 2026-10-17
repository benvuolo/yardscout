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
