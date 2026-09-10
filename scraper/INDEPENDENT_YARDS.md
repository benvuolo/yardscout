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
| 5 | Kenny U-Pull | 2 US (+25 CAN) | Bangor + Lewiston ME; only real Northeast play found | WP archive, ~1,600 pages | candidate (heavy) |
| 6 | Go Pull-It | 2 | Jacksonville + Tampa FL | WP + CRUSH form; archive is location-gated | candidate (needs devtools pass) |
| 7 | Sturtevant Auto | 1 | Milwaukee WI | custom inventory subdomain, HTML table | candidate |
| 8 | Ace Pick-A-Part | 1 | Jacksonville FL | WP, mechanism unidentified | candidate |
| 9 | Harry's U-Pull-It | 3 | Hazleton/Allentown/Pennsburg PA (huge NE yards) | behind Sucuri JS challenge | **blocked** |
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
   verify US-yard visibility; would open the Northeast.
4. Retry Ecology Auto Parts / Jalopy Jungle / ABC U-Pull-It domains; verify
   Sturtevant and Ace mechanisms.
