# Expansion Candidates — Platform-First Research Pass

*Research date: 2026-10-22. Pure research — no scraper changes in this commit.
Companion to `scraper/INDEPENDENT_YARDS.md` (onboarding history) and
`scraper/independent_yards_registry.json` (machine-readable registry).*

> **2026-10-26 UPDATE:** see [§8 — Ario footprint / VinPlus sweep / Nuxt-vendor
> pass](#8-2026-10-26-scouting-pass--ario-footprint-vinplus-sweep-nuxt-vendor)
> at the bottom. Headline: the Ario/autorecycler.io adapter built for Ryan's
> Pick-a-Part generalizes to **~53 new yards / ~48,000 vehicles** enumerated
> directly from the platform's own org table. It dwarfs everything in the
> 2026-10-22 tables below (which remain valid and un-built).

**Method:** hunt inventory-software *platforms*, not individual yards. Verified via
read-only spot checks (1 req/~2s, browser-equivalent UA), certificate-transparency
subdomain enumeration (crt.sh), frontend-bundle mining, and state-by-state web
search. "Public searchable inventory" = vehicle rows (year/make/model/row) a
customer can query without auth. Yards whose sites only publish hours/prices are
listed separately as **directory-only**.

## Headline numbers

| Metric | Value |
|---|---|
| Platform families examined | 10 (5 already in our adapter stable) |
| New candidate yards with scrapeable public inventory | **25** |
| Est. new vehicles unlocked | **~25,000** |
| Biggest single-adapter unlock | **VinPlus tenant sweep: 5 yards / ~10,300 vehicles for ~zero new parsing code** |
| Directory-only candidates (no public inventory) | 5 |
| Stale registry entries corrected | 3 (Kenny U-Pull, Ecology, Garden Street) |

---

## 1. Platform / vendor landscape

### Platforms we can already parse (adapter families in production)

**VinPlus — TexN Rewards (`vinplus.texnrewards.com` → Cloud Run
`inventory-search-api-*.run.app`).** Multi-tenant React SPA; unauthenticated
`POST /searchVehicleHttp` with `yard_id` = tenant slug; `GET /api/yard-info/{slug}`
validates tenants without auth. Crucially, VinPlus fronts **multiple backend YMSs**
(`sourceSystem: yardsmart` *and* `crush` observed), so it keeps absorbing yards
regardless of their back office. Tenant sweep results (bundle mining + slug
dictionary, all verified returning live rows this pass):

- NEW tenants: `joliet_u_pull_it`, `pick_n_pull_san_antonio`, `195_used_auto_parts`,
  `pick_ur_part` — 5 new yards total (see table below).
- Already-covered chains that are ALSO VinPlus tenants: `chesterfield_auto_parts`
  (all 3 VA locations — could **replace the 80-min ASP.NET hybrid adapter** with
  clean JSON incl. full VINs), `go_pull_it` (all 4 locations **including
  Tallahassee, which we don't track** — could replace the 30–50-min capped crawl),
  `indy_u_pull_it`, `prestige_pull_your_part`, `utah_pic_a_part`,
  `road_tested_parts`, `tri_state_iron_metal`.
- Fingerprints: links to `vinplus.texnrewards.com/{slug}`, photos on
  `api.yardsmartapp.com`, TexN marketing widgets (`client.texnrewards.net`).
- Re-run the slug sweep periodically; `/api/yard-info/{slug}` is a free validity
  oracle (invalid → `{"error":"Yard not found"}`).

**CRUSH "Enterprise Websites" MVC app — S3 Software Solutions.** Confirmed this
pass: **S3 Software Solutions (Salt Lake City) is the maker of CRUSH** — one vendor
behind four of our existing adapters (Sturtevant, St. Cloud, U-Pull-It IA/NE via the
TAP WP plugin, Budget Bartow via `inventory.aspx` WebForms). Their hosted MVC
inventory app has a crisp fingerprint: `/Home/Inventory` page +
`POST /Home/GetMakes` / `/Home/GetModels` with `yardId`, `/Home/PartPrices`,
`$.ajax` search, YEAR/MAKE/MODEL/ROW table. **4 new instances found (8 yards)**:
Jalopy Jungle (×5, ID), Trusty Pick-A-Part (ID), M&M U-Pull-It (Buffalo NY),
Polk County Pick and Pay (Lakeland FL). The St. Cloud/Sturtevant parsers are the
template. Historical `*.s3softwaresolutions.com` cert names (byot, fossupi, glad,
cnc, rackautoparts, yourpart, aaa, hwy82, midtown, myst…) are dead subdomains but
are **leads to yards that moved platforms** (BYOT confirmed moved to WordPress).

**iis-pro-upull WP plugin** (Pick-A-Part VA's platform). New instance: **Ewe
Pullet** (Sioux Falls SD). URL shape `/inventory/{MAKE}/{MODEL}/?k=1` identical to
papva's card deck. robots.txt allow (admin-ajax explicitly allowed), no Cloudflare
observed (papva's TLS-fingerprint pain may not apply here).

**yardconnect-pro WP plugin — yardconnectpro.com (dev shop: Octonove), YardSmart
backend.** Existing instances: Rupert's, U-Pick-It AZ. New instance: **Pick Ur Part
(Lubbock)** — but it's also a VinPlus tenant, and VinPlus is the cheaper path.
Watch item: U-Pick-It AZ's owner is rolling YardSmart out to **four additional
yards in Omaha and Iowa** (YardSmart case study, 2026) — expect new
yardconnect/VinPlus instances there.

**gm_vehicle_search / PT1 plugin family** (U-Pull-R, Pull-N-Save, NVPAP,
Prestige). No new instances found this pass.

### Platforms that do NOT help us (documented so we stop re-checking)

- **Hollander (ITrack / Powerlink / Pinnacle), car-part.com, URG ecosystems** —
  full-service *parts interchange* catalogs; no self-serve vehicle-row public
  inventory. car-part.com search results are part listings, not yard rows.
- **Buddy Automotive Innovations (buddyai.com)** — intake tablets + auction bidding
  tools for recyclers (integrates Powerlink/Pinnacle). Back-office only; no public
  inventory surface.
- **Row52** — Pick-n-Pull-exclusive; permanently out of scope (policy).
- **Aggregator competitors** (not platforms, but useful for verification/counts):
  u-pull-it.com, junkyardindex.com, junkyardinventory.com, salvage.ninja,
  upullscan.com, jalopybot.com. Several scrape the same yards we do.

---

## 2. Summary table — platform → unlock

Adapter difficulty: 1 = config-only on existing adapter … 5 = new WAF-fighting build.

| Platform | New yards | Est. vehicles | Difficulty | Example yards |
|---|---|---|---|---|
| VinPlus (tenant additions) | 5 | ~10,300 | **1** | Joliet U-Pull-It (IL), Pick-N-Pull San Antonio (TX), 195 Used Auto Parts (TX), Pick Ur Part (TX), GO Pull-It Tallahassee (FL) |
| CRUSH MVC app (`/Home/Inventory`) | 8 | ~6,500–9,000 | **2** | Jalopy Jungle ×5 (ID), Trusty (ID), M&M Buffalo (NY), Polk County Pick and Pay (FL) |
| iis-pro-upull WP | 1 | ~1,200 | **2** | Ewe Pullet (SD) |
| Custom WP server-rendered tables (Indy/Budget pattern) | 6 | ~6,600 | **2–3** | BYOT ×3 (TX), Wilbert's ×3 (NY) |
| yardconnect-pro WP | 0 net new | — | 2 | (Pick Ur Part covered via VinPlus) |
| **Total** | **20–25** | **~25,000** | | |

---

## 3. Full per-yard candidate list

All candidates deduped against the current 211 tracked yards. "Inv" = public
searchable vehicle inventory. "PL" = published parts price list.

### VinPlus tenants (difficulty 1 — existing `fetch_vinplus_inventory` pattern)

| Yard | City/State | Website | Inv | Vehicles | PL |
|---|---|---|---|---|---|
| Joliet U-Pull-It | Joliet, IL (Chicago metro) | https://www.jolietupullit.com | yes (own site table + VinPlus `joliet_u_pull_it`) | ~3,000 (74 Toyotas in test query; UPullScan reports 3,036) | verify |
| Pick-N-Pull San Antonio (independent; NOT the national chain) | San Antonio, TX | https://www.picknpullsanantonio.com (site unreachable from this network; VinPlus `pick_n_pull_san_antonio` live) | yes (VinPlus, sourceSystem=crush) | ~4,100 | verify |
| 195 Used Auto Parts | Killeen, TX | https://www.195usedautoparts.com | yes (VinPlus `195_used_auto_parts`, sourceSystem=crush) | ~1,600 | verify |
| Pick Ur Part Auto Salvage | Lubbock, TX | https://pickurpart.com | yes (VinPlus `pick_ur_part` + yardconnect-pro on-site) | ~870 (opened Feb 2026, growing fast) | no ("call for prices") |
| GO Pull-It — Tallahassee | Tallahassee, FL | https://gopull-it.com | yes (VinPlus `go_pull_it` location `Tallahassee`) | ~675 | yes (chain PL already wired) |

Notes: VinPlus caps 100 rows/query — reuse the year-bisection helper. Pick-N-Pull
San Antonio rows include pre-2019 `dateAdded` values — apply date sanity. Joliet and
Pick Ur Part photos exist on `api.yardsmartapp.com` — ignore per no-photos policy.

### CRUSH MVC app (difficulty 2 — St. Cloud/Sturtevant parser family)

| Yard | City/State | Website | Inv | Vehicles | PL |
|---|---|---|---|---|---|
| Pick-A-Part Jalopy Jungle — Boise | Boise, ID | https://inventory.pickapartjalopyjungle.com | yes | unverified (large; 5-yard chain) | no |
| Pick-A-Part Jalopy Jungle — Caldwell | Caldwell, ID | (same app, yardId 1021) | yes | unverified | no |
| Pick-A-Part Jalopy Jungle — Nampa | Nampa, ID | (yardId 1022) | yes | unverified | no |
| Pick-A-Part Jalopy Jungle — Garden City | Garden City, ID | (yardId 1119) | yes | unverified | no |
| Pick-A-Part Jalopy Jungle — Twin Falls | Twin Falls, ID | (yardId 1099) | yes | unverified | no |
| Trusty Pick-A-Part | Caldwell, ID | https://inventory.trustypickapart.com | yes | unverified (single yard) | verify (`/Home/PartPrices`) |
| M&M U-Pull-It | Buffalo, NY | https://www.mmupullit.com/Home/Inventory | yes | unverified | yes (`/Home/PartPrices`) |
| Polk County Pick and Pay | Lakeland, FL | https://www.polkcountypickandpay.com/Home/Inventory | yes | "hundreds" | yes (`/Home/PartPrices`) |

Notes: Jalopy = **first Idaho coverage** (Treasure Valley ×4 + Twin Falls); a
third-party tracker (jalopybot.com) scrapes the same app daily, so volume is
tolerated. M&M = first western-NY yard. **Polk County Pick and Pay is ~25 mi from
Budget U-Pull-It Bartow — prime referral-geography flag** (see §5).

### WordPress custom server-rendered (difficulty 2–3 — Indy/Budget parser pattern)

| Yard | City/State | Website | Inv | Vehicles | PL |
|---|---|---|---|---|---|
| BYOT Auto Parts — Waco | Elm Mott, TX | https://www.byotautoparts.com/locations/waco/inventory/ | yes (per-location pages; Color/VIN/Stock fields) | ~1,200 | yes (pricing pages) |
| BYOT Auto Parts — Bryan/College Station | Bryan, TX | https://www.byotautoparts.com/locations/bryan-college-station/ | yes | ~930 | yes |
| BYOT Auto Parts — Beaumont | Beaumont, TX | https://www.byotautoparts.com/locations/beaumont/ | yes | ~1,170 | yes |
| Wilbert's U-Pull-It — Rochester | Williamson, NY | https://www.wilberts.com/u-pull-it/vehicle-inventory-search/ | yes (custom `wilberts-parts-search` plugin, rebuilt Jul 2026; engine/VIN/stock on cards) | unverified | verify |
| Wilbert's U-Pull-It — Bath | Bath, NY | (same search, location filter) | yes | unverified | verify |
| Wilbert's U-Pull-It — Buffalo | Buffalo (Elma), NY | (same) | yes | unverified | verify |
| Ewe Pullet (Nordstrom's) | Brandon/Sioux Falls, SD | https://ewepullet.com/inventory/ANY/ANY/?k=1 | yes (iis-pro-upull card deck; stock#, mileage, set date) | ~1,200+ | yes ("Simple Parts Pricing") |

Notes: BYOT is an ex-S3/CRUSH tenant that moved to WordPress — mechanism needs a
devtools pass (page embeds vehicle data; 225 KB inventory page). Wilbert's =
**first Rochester + Finger Lakes coverage** and 2nd/3rd Buffalo-area yards together
with M&M. Ewe Pullet = **first South Dakota coverage**; robots.txt allow-all with
admin-ajax explicitly allowed.

---

## 4. Directory-only candidates (no public vehicle inventory — map-pin material only)

| Yard | City/State | Website | Notes |
|---|---|---|---|
| West Fargo Self Service Auto Parts | West Fargo, ND | https://www.wfselfservice.com | 1,000+ cars claimed; no online inventory. Only self-serve yard in Fargo–Moorhead. |
| Vince's U-Pull-It | Marcy, NY (Utica/Syracuse) | https://www.vincesupullit.com | ~1,800–2,000 cars; interchange terminal on-site only. |
| 603 Auto Salvage | Plaistow, NH | https://603autosalvage.com | Claims "online inventory updated daily" but /inventory/ page renders no vehicle rows (JetEngine WP). **Verify with a browser session — would be first New England coverage if real.** |
| Dietz Auto & Truck Salvage | Billings, MT | http://www.dietzautoparts.com | Full-service; out of scope. |
| Chesney Auto Salvage | Duluth, MN | (prior pass) | Full-service w/ DIY allowed; no vehicle rows. Unchanged. |

## 4b. Registry corrections (stale entries found this pass)

- **Kenny U-Pull (ME): remove candidate.** Bangor closed permanently Jan 2023 (was
  the only US yard; Lewiston never had public inventory). Kenny/AIM is Canada-only
  now. The registry's "best Northeast play" note is dead.
- **Ecology Auto Parts (CA): retire.** ecoparts.com is unreachable; its old yards'
  addresses (Fontana 15228 Boyle Ave, Bloomington 221 E Santa Ana Ave) now match
  LKQ Pick Your Part locations we already track → absorbed by LKQ.
- **Garden Street U-Pull-It (Fort Myers FL): already covered.** Renamed
  U-Pull-&-Pay/Pull-A-Part Fort Myers = our "Pull-A-Part - Fort Myers".
- **U-Pull-&-Pay:** still operates as a brand under Pull-A-Part (upullandpay.com
  has its own search), but every UPAP city cross-checks to a yard already in our
  Pull-A-Part coverage. Genuinely retired as a separate target.

---

## 5. Geographic gap analysis (211 yards, 35 US states + 2 CAN provinces)

**Zero-coverage US states:** ME, NH, VT, MA, CT, NJ, DE, WV, ND, SD, MT, WY, ID,
AK, HI (+DC).

- **Idaho** — fixed by this pass: Jalopy Jungle ×5 + Trusty = 6 yards, difficulty 2.
- **South Dakota** — fixed by Ewe Pullet (Sioux Falls).
- **New England (ME/NH/VT/MA/CT) + NJ/DE** — still structurally empty: no
  self-serve chain with public vehicle inventory found across three research
  passes. Closest candidates: 603 Auto Salvage NH (verify), Harry's Pennsburg PA
  (~40 mi from Philly, covered). Document honestly; nothing feasible today.
- **ND/MT/WY/WV/AK/HI** — only full-service or no-inventory yards found.

**Thin states materially improved by this pass:** NY (3 → potentially 7: +M&M
Buffalo, +Wilbert's ×3 — first western-NY/Finger Lakes), IL (6 → 7, first
Chicago-metro independent with ~3,000 cars), TX (20 → 25), FL (15 → 17).

**Florida / Budget U-Pull-It referral flags (owner relationship):**

- **Polk County Pick and Pay (Lakeland)** — ~25 mi from Budget Bartow, same
  Lakeland–Winter Haven metro. CRUSH MVC platform (difficulty 2). Top referral
  candidate.
- **GO Pull-It Tallahassee** — same state, chain already in the app.
- Orlando flank is already saturated by covered chains (Pull-A-Part Orlando,
  U-Pull-&-Pay Orlando/West Palm Beach/Fort Myers, LKQ ×many, Ace Jacksonville,
  Budget ×2).

---

## 6. Recommended next 3 adapters

1. **VinPlus tenant expansion (difficulty 1, ~10,300 vehicles).** Add 4 tenant
   configs (Joliet, Pick-N-Pull San Antonio, 195 Used Auto Parts, Pick Ur Part) +
   the Tallahassee location to the `go_pull_it` tenant. Zero new parsing: same
   `searchVehicleHttp` + year-bisection used for RTP/Tri-State today. Biggest
   vehicles-per-engineering-hour ratio available, adds first Chicago-metro
   independent + 3 Texas metros. Bonus follow-up: migrate Go Pull-It and
   Chesterfield scans onto VinPlus to retire the two slowest/most fragile adapters
   we run.
2. **CRUSH MVC family: Jalopy Jungle + Trusty (difficulty 2, 6 yards, first Idaho
   coverage).** Same `/Home/GetMakes`→`GetModels`→search flow already parsed for
   St. Cloud; yard IDs enumerated (1021/1022/1099/1119 + Boise). Then reuse the
   same build for **M&M Buffalo** and **Polk County Pick and Pay** (Budget referral
   geography) — four sites, one parser family.
3. **Wilbert's U-Pull-It (difficulty 3, 3 yards, first Rochester/western-NY
   coverage).** Custom WP plugin (`wilberts-parts-search`, admin-ajax) with clean
   vehicle cards (VIN/stock/engine); needs one devtools pass to map the AJAX
   actions. Pairs with M&M Buffalo to turn upstate NY from "Fenix-only" into a
   real cluster. (Swap in BYOT ×3 if Texas density is preferred over NY gap-fill —
   similar effort, ~3,300 vehicles.)

## 7. Observations for the scraper owner (no action taken — hands off tonight)

- **U-Pull-R Parts (Rosemount/East Bethel MN, Toledo OH) is absent from the
  2026-10-22 05:53Z scrape** (`docs/data/inventory_live.json` has zero `U-Pull-R`
  yards; MN shows only St. Cloud). Upstream data is alive (third-party aggregator
  shows ~8,900 vehicles across the two MN stores). Likely another
  `gm_vehicle_search` plugin change like the 2026-10-13 `doApiCall→doAaaApiCall`
  rename — check the scan log's `INDEPENDENT_EXPECTED_SOURCES` warning.
- Chesterfield + Go Pull-It VinPlus consolidation opportunity (see §1/§6).

---

## 8. 2026-10-26 scouting pass — Ario footprint, VinPlus sweep, Nuxt vendor

*Read-only scouting (no scraper changes). Method: enumerated the Ario Bubble
app's own `custom.organization` table via the obfuscated `/elasticsearch/search`
endpoint the Ryan's adapter already speaks (154 orgs, 2 requests), then one
`n=1` probe per org for visible `custom.inventorysearch` rows and a paged count
for the ~70 orgs that had any (all at 2s pacing, ~400 requests total). VinPlus:
bundle mining + ~85-slug dictionary against the public `/api/yard-info/{slug}`
oracle at 1.5s. All counts are visible+non-deleted rows as of 2026-10-26.*

### Headline

| Metric | 2026-10-22 pass | This pass |
|---|---|---|
| New candidate yards | 25 | **+53 (Ario alone)** |
| Est. new vehicles | ~25,000 | **+~48,000** |
| Biggest unlock | VinPlus ×5 | **Ario org sweep: one existing adapter family → 7 chains + 17 singles** |

Current DB for scale: 221 yards / ~256k vehicles. The Ario batch alone is
+24% yards, +19% vehicles, at near-config-only cost (the Ryan's
`fetch_ryans_inventory` flow parameterizes on the org record; orgs without a
URL slug are still queryable by org `_id`).

### 8.1 Ario / autorecycler.io (Bubble app `autoscrapzen`) — THE find

**Vendor:** AutoRecycler.io "Ario", now marketed as **ari (Auto PARTnered
Solutions**, ariintel.com, Melbourne AU). Marketing claims 125k vehicles listed
across 35+ customers — matches our enumeration. Integrates CRUSH / Pinnacle /
Checkmate back-offices, so it keeps absorbing yards (same dynamic as VinPlus).
Public search pages live at `app.autorecycler.io/inventory/{slug}`; most
customer yards ALSO embed/link that search on their own sites (Ryan's iframe
precedent; EZ Pull N Pay renders the tables directly on ezpullnpay.com; Foss
points fossrecycling.com at fossupullit.com; Carolina PnP at
carolinapicknpull.com; Bevell's "Vehicle Search" on bevellspiy.com). The dead
`fossupi` / `hwy82` S3-cert leads from §1 resolved: **both moved to Ario.**

**Mirrors of yards we already track** (no action, but useful as backup/liveness
cross-checks): all ~35 Pull-A-Part cities, 12 LKQ/Pick Your Part yards,
Pick-n-Pull Oakland, Prestige Houston, Pickers Longview/Texarkana, Nevada
Pic-A-Part LV, Ryan's itself. Our Ario counts cross-check within ~6% of
UPullScan/SalvageWatch for EZ Montgomery and Foss — counts are trustworthy.

**NEW candidate chains** (vehicles = our live probe counts):

| Chain | Yards | Vehicles | States | VINs | Notes |
|---|---|---|---|---|---|
| Paul's Auto Yard | 10 | 9,809 | IN | yes | 13-location chain, 10 with live inventory (South Bend 1,634 / Ft Wayne 1,459 / Westville 1,429 / Merrillville 1,372 / Lake Station 1,232 / Elkhart 860 / Gary 593 / DeMotte 521 / Knox 436 / Logansport 273). IN currently has 5 tracked yards. |
| EZ Pull N Pay | 7 | 6,914 | GA, AL | yes | Atlanta 1,058 / Stockbridge 1,112 / Warner Robins 1,183 / Columbus 948 / Montgomery 1,023 / Decatur 1,012 / Birmingham 578 (new yard, ramping). Tables published on ezpullnpay.com. |
| Foss U-Pull-It | 6 | 5,599 | NC, VA | yes | Winston-Salem 1,338 / Jacksonville 1,167 / La Grange 970 / Chesapeake VA 816 / Wilson 752 / Havelock 556. First Hampton Roads coverage. |
| Carolina Pick N Pull | 3 | 4,317 | NC, SC | no | Cape Fear (Wilmington) 1,613 / Grand Strand (Conway SC) 1,432 / Sandhills (Fayetteville) 1,272. |
| UAPI (U-Auto-Pull-It) | 6 | 3,020 | LA, TX, AR | yes | Ark-La-Tex: Texarkana 666 / Alexandria 531 / Monroe 518 / N Shreveport 469 / S Shreveport 420 / Bossier City 416. Sister of Pipes U-Pull-It (tracked via VinPlus). |
| Auto Parts U Pull | 2 | 2,839 | NC | yes | Shelby 1,993 / Lincolnton 846. |
| TAS Recycling | 2 | ~717–1,434 | TN | no | Kingsport + Knoxville both probe exactly 717 — likely one shared pool under a shared slug; **dedupe at build time**. |

**NEW candidate singles:**

| Yard | City/State | Vehicles | VINs | Notes |
|---|---|---|---|---|
| Bevell's Pull It Yourself | Goldsboro, NC | 1,934 | no | bevellspiy.com |
| Blue & Gold Auto Salvage | Goose Creek, SC | 1,837 | no | Charleston metro; converted to self-serve |
| L AND L U-Pull Auto Parts | Kings Mountain, NC | 1,188 | yes | |
| A & A Auto Recycling | Bradenton, FL | 1,109 | yes | |
| Yank-A-Part | Poulsbo, WA | 1,032 | yes | Kitsap Co.; first WA independent (WA = 5 Pick-n-Pull today) |
| Cash-N-Carry Pull Your Part | Savannah, GA | 995 | no | cashncarryparts.com |
| Young's U-Pull-It | Dudley (Goldsboro), NC | 963 | yes | upull.youngsautocenter.com |
| Southern Auto Salvage | Cameron, NC | 936 | yes | |
| Highway 82 Pick & Pay | Poulan, GA | 897 | no | hwy82pp.com (ex-S3 `hwy82` lead); publishes price list |
| A-Z U-Pull-It | Shoemakersville, PA | 810 | yes | Reading metro; 2nd PA independent after Harry's |
| Santa Maria Recycling Center | Santa Maria, CA | ~833 live | yes | Raw visible count 4,265 is STALE (rows never hidden; sample added-dates 2024–25). 833 added since 2026-04 — **scan must date-filter**. |
| JDM Automotive & Recycling | Maysville, NC | 569 | yes | |
| Samson Auto Salvage | Los Angeles, CA | 375 | yes | verify self-serve at build |
| Kiker's U-Pull-It | Pensacola, FL | 285 | yes | Ario's own case-study customer |
| Southside U-Pull-It | Houston, TX | 281 | no | |
| Dis & Dat Auto Recycling | Las Vegas, NV | 258 | yes | distinct from NVPAP |
| A-1 Metals & Auto Salvage | Paso Robles, CA | 187 | yes | |

**Micro/out-of-scope tier** (documented so we stop re-checking): Long's Hampton
VA (37), AB Rayne LA (36), Ario KC demo (31), Green Vehicle Disposal (47 across
2 dupe orgs), Universal St Louis (6), Yeti Chilliwack BC (18, Canada), Ajax SF
(103, full-service dismantler), plus ~10 tiny CA dismantlers (1–5 rows each)
and demo orgs (Jack/Testino Autos, Sam's Worcester, Jamm Davie, Gaston Towing).

**Build notes:** generalize `fetch_ryans_inventory` into a tenant table keyed on
org `_id` (slug optional); make/model name maps are GLOBAL tables — fetch once
per scan, not per yard. ~5–10 POSTs per yard per scan → 53 yards ≈ 300–500
POSTs at 2s ≈ 10–17 min; consider a dedicated Ario stage in the scan. Exclude
rows via the Santa Maria date-filter lesson where a yard's added-date histogram
looks stale. Verify each chain's own-site embed at build time; everything above
is also publicly reachable at `app.autorecycler.io/inventory/{slug}` (or via
the yard's own search page for slugless orgs).

### 8.2 Nuxt JSON API (U-Pull and Save Pontiac) — custom, no siblings

**Verdict: in-house one-off, not a product.** Same-origin `/api/vehicles/*`
only, no vendor strings in any `_nuxt` bundle, bespoke Tailwind components,
Sentry org 49970; parent schramauto.com is plain WordPress. Schram Auto Parts
has a long-tenured IT director (Jesse Ostrander) with a documented history of
building custom inventory sites. No sibling yards exist to find. (Mason store
110 confirmed returning `[]` — "yard closed" stands.)

### 8.3 VinPlus tenant sweep — no skipped tenants; one migration signal

85-slug dictionary + SPA bundle mining against `/api/yard-info/{slug}`. All 12
known/covered tenants re-validated. New valid slugs found: only
`chesterfield_auto_parts_demo` (TexN's sales demo — ignore) and **`fenix`** =
"Fenix U-Pull Binghampton" (search `yard_id: fenix_u_pull`, single location,
rows carry FULL VINs — the current fenix adapter has none). Binghamton is
already tracked, so this is a **migration/enrichment opportunity, not a new
yard** — and a signal Fenix corporate is piloting VinPlus: re-sweep
`fenix_*`-style slugs periodically; more Fenix locations may appear. None of
the 2026-10-22 un-built candidates (Jalopy, Trusty, M&M, Polk, Ewe Pullet,
BYOT, Wilbert's) nor any of our other adapter chains resolve as tenants.

### 8.4 Still-pending from the 2026-10-22 pass (unchanged, re-verified un-built)

CRUSH MVC family (Jalopy ×5 + Trusty + M&M Buffalo + Polk County, ~6,500–9,000
vehicles, difficulty 2), Ewe Pullet (SD, ~1,200), BYOT ×3 (TX, ~3,300),
Wilbert's ×3 (NY). No OTHER new platform hit the 3+ yard threshold this pass —
Ario absorbed every lead that would have.

### 8.5 Recommended first batch (owner approval required before any build)

**Ario wave 1 — the four big chains: 26 yards, ~26,600 vehicles.**
EZ Pull N Pay ×7 + Paul's ×10 + Foss ×6 + Carolina PnP ×3. One adapter
generalization, all chains verified publishing inventory on their own sites,
VINs everywhere except Carolina PnP. Geography: IN +10 (5 today), first Hampton
Roads VA, first Savannah-adjacent GA… and EZ's Atlanta/Birmingham/Montgomery
yards sit in metros where we currently only have Pull-A-Part.
**Wave 2:** the 17 singles + UAPI ×6 + Auto Parts U Pull ×2 + TAS (~21,000
more vehicles). **Wave 3:** the 2026-10-22 CRUSH/BYOT/Wilbert's/Ewe Pullet
builds (§8.4) for the ID/SD/NY gap-fill.

### 8.6 2026-10-26 (later) — wave-1 build findings: the Bubble feed is frozen

*Built on branch `feat/ario-wave1` (not merged). Multi-tenant adapter
`fetch_ario_inventory` / `ARIO_CHAINS` + `scraper/_probe_ario_orgs.py` (the
org-table dump this pass was missing). All 26 wave-1 yards resolved and
fetched live: 25,310 vehicles across 27 Ario yards in 226 s, per-yard counts
within ~1% of §8.1 (Sandhills aside — below).*

**The finding that changes the plan: Ario's Bubble app stopped receiving new
cars in late August 2026.** Newest `added_date` per feed, scanned 2026-10-26:
Ryan's 2026-08-13, EZ Pull N Pay 2026-08-24/25 (all 7), Foss 2026-08-19..27
(all 6), Paul's 2025-10-21 (all 10 — nothing since the orgs were created),
Carolina PnP: date garbage (2000..2031; 151 undated at Grand Strand). Rows
still get *hidden* as cars leave (counts drift), so the fingerprint-based
STALE YARD check never fires — but a ~1,350-car lot with 1,300 July/August
set-outs and zero in September/October is not live. **Ryan's — already in the
app since 2026-10-23 — has been serving a two-month-old lot this whole time.**

Why: Ario migrated. The yards' own sites now embed a NEW frontend,
`ario.autorecycler.io/yard/{slug}?embed=1` (Vite SPA, Supabase project
`zqfzqcyteuemzbnwtmcr`, inventory via the `search-inventory` edge function:
`{start_year, end_year, input_make, input_model, yard_list:[slug],
limit_results}`; org records expose a `bubble_legacy_url` fallback). The old
`app.autorecycler.io/inventory/{slug}` pages still render the Bubble data —
which is exactly the frozen snapshot we scraped. Fresh inventory lives behind
the Supabase function, which has visible rate limiting ("Too many searches /
verify your email") and a per-call result cap — it needs its own adapter pass
(make × year bisection like VinPlus) before any Ario yard, Ryan's included,
can be called live. Not probed further this session (owner call: it means
calling Supabase with the site's public anon key).

Also learned this build:

- **Bubble paging is flaky.** Sandhills returned 2 visible rows on one pass
  and 1,272 (= §8.1) minutes later with the identical query; no error was
  raised. `_ario_search` now retries, and `_ario_search_all` reports
  truncation so a yard is skipped for the scan instead of published short.
- **New scan alarm, NO ARRIVALS** (`_update_yard_health`): a yard with ≥100
  cars, ≥50% dated, whose newest set-out date is ≥30 days old. Dry-run on the
  2026-10-26 10:29Z payload flags 8 yards nobody had noticed: Ryan's (74 d),
  U-Pull-It Lincoln/Omaha ×2/Des Moines (81–88 d), Prestige Houston (108 d),
  St. Cloud (167 d), Fenix Belleville (885 d — placeholder dates or a dead
  feed; check).
- **§8.3 correction:** Fenix's own table already publishes VINs (Binghamton
  1,867/1,881). The VinPlus `fenix_u_pull` tenant adds nothing — dropped.
- Carolina PnP's dates need the standard `_sanitize_date_added` clamp
  (future years, 2000-01-31 placeholders) — already applied in enrich.

#### 8.6.1 Live adapter built (same day)

Owner approved probing the new backend. Observed from a real browser (the
page's own requests, `scratchpad` Playwright runs), nothing guessed:

- `POST /functions/v1/search-inventory` body
  `{yard_list:[slug], per_yard_limit, item_rank_offset, limit_results,
  sort_mode:"days_newest", projection:"list", surface:"yard", filters null}`
  → `{items, total, yards_meta:[{yard, returned, total_matching, truncated,
  next_offset}]}`. Items: id, year, make, model, row, stock, date_placed,
  color, image_url (ignored), yard. **No VIN in the list.** The page pages
  25 then 40 at a time by `next_offset`; `total_matching` is the whole lot.
- `POST /functions/v1/get-inventory-item {inventory_id, yard_slug}` →
  `{item:{..., vin, description}}` — the only place the VIN appears.
- `GET /rest/v1/yards?slug=eq.{slug}&customer_facing_visible=eq.true` →
  the yard record (display_name, address, `data.latitude/longitude`,
  `inventory_source` e.g. `crush_xml_sync`, organization_id).
- Auth: the site's publishable anon key from the bundle (every visitor's
  browser sends it). Rate limiting exists ("Too many searches").
- **Freshness confirmed live:** Ryan's `total_matching` 1,376 with cars
  placed 2026-10-23; Foss Chesapeake 50 cars placed in the last 7 days.
  The Bubble feed had neither.

`fetch_ario_inventory` now reads this feed (offset paging per yard, server
counts trusted, incomplete lots skipped, 429 → 30 s back-off). VINs: a new
history-DB table `ario_vins` seeded once from the legacy feed (every car
that pre-dates the freeze gets its VIN for free), then `get-inventory-item`
newest-first under `ARIO_VIN_MAX_PER_RUN` (1000/scan ≈ a few days to drain
the rest, then ~100/scan steady state). Ids are unchanged, so Ryan's
history carries over. Verify with the manual `Ario adapter probe` workflow
(`scraper/_probe_ario_live.py`); the per-yard table it prints is the merge
gate.

#### 8.6.2 Wave 1 narrowed to 13 yards — Paul's and Carolina PnP are not on Ario's live backend

Per-slug browser check of all 27 configured yards against the live frontend:
Ryan's, EZ ×7 and Foss ×6 load and show set-outs from this week (EZ Atlanta
78 cars placed in the last 7 days; Foss Chesapeake 50). **Paul's ×10 and
Carolina PnP ×3 answer "Yard not found"** (`/rest/v1/yards?slug=eq.…` → 406).
Their Bubble rows explain why they looked fine to the scout: Paul's is a
one-time import (steady ~150 cars/month Mar→Oct 2025, nothing after the org
was created on 2025-10-21); Carolina's rows are a 2024 dump (Sandhills
2024-04..10, Cape Fear 2024-06..09 plus garbage years). Neither is a live
feed anywhere on Ario. Both dropped from `ARIO_CHAINS` (registry status →
candidate):

- **Carolina Pick N Pull** really publishes on its own WordPress site:
  `carolinapicknpull.com/inventory/?location={3|9|10}` (Location/Make
  form, server-rendered). Plain curl gets a WAF 403, a browser is fine —
  a curl_cffi-style adapter (Pick-A-Part VA precedent). ~4,300 cars, wave 3.
- **Paul's Auto Yard**: paulsautosalvage.com has parts/engines/"used cars for
  sale" pages but no public vehicle rows found. Directory-only for now.

Wave 1 as built: EZ Pull N Pay ×7 + Foss U-Pull-It ×6 (+ Ryan's repaired),
~13,000 live cars, VINs seeded from the legacy feed.

#### 8.6.3 Probe result and merge

CI probe (`Ario adapter probe`, run 40382136094) with `per_yard_limit` 40 —
the function answers HTTP 400 to 200: **13,986 vehicles across 14 yards in
~14 min**, every yard's newest set-out between 2026-10-07 and 2026-10-26;
EZ counts 685–1,153, Foss 529–1,326, Ryan's 1,376 (vs 1,358 frozen).
VIN seed from the legacy feed covered 6,221 (44%) — low where lots turn
over fast (Ryan's ~81-day lifespan: 1%; Warner Robins 7%), high where they
don't (Havelock/Birmingham 82–83%). The rest fill via get-inventory-item
at 600/scan (~2 days). Merged to main; the first scheduled scan after the
merge publishes the 13 new yards and un-freezes Ryan's.

#### 8.6.4 Wave 2 (same day) — which §8.1 candidates are actually on the live backend

Browser check of all 27 remaining §8.1 orgs against `ario.autorecycler.io/yard/{slug}`:

**Live (wired, branch `feat/ario-wave2`): 14 yards** — UAPI ×6 (N/S Shreveport,
Bossier City, Monroe, Alexandria, Texarkana), Auto Parts U Pull ×2 (Shelby
1,630 / Lincolnton 857), L and L (1,437, set-outs today), A & A Bradenton,
JDM Maysville, Samson LA, Southside Houston, Santa Maria (3,297 rows but
newest 2026-08-24 — never hides departures, so published with an
`added_since` cutoff). JDM/Southside show no recent set-outs on the page's
first view; the CI probe's per-yard newest date is the gate before merge.

**Not on the live backend ("Yard not found"): 13** — A-1 Metals, A-Z U-Pull-It,
Bevell's, Blue & Gold, Cash-N-Carry, Dis & Dat, Highway 82, Kiker's, Southern
Auto Salvage, TAS ×2, Yank-A-Part, Young's. Same pattern as Paul's/Carolina:
Bubble org exists, rows are a stale dump. Registry stays "candidate"; each
needs its own-site source before it can be wired.

CI probe (run 40396524689): 27,779 cars / 28 yards. **Merged: 11 wave-2 yards**
— UAPI ×6 (580–886 each, set-outs Oct 20–23), Auto Parts U Pull ×2 (1,630 /
857), L and L (1,437, set-outs the day of the probe), A & A (1,117), Samson
(349). **Dropped before merge:** JDM (newest 2026-08-26), Southside
(2026-06-16, 84 undated), Santa Maria (2026-08-24) — live backend, but no
arrivals for 2+ months. Several yards carry ghost rows never hidden (A & A
oldest 2017, Lincolnton/L and L 2021), so the live adapter now drops dated
rows older than `ARIO_LIVE_MAX_AGE_DAYS` (365). New yards start at 0% VIN
(no legacy seed); the 600/scan detail backfill fills them over ~3 days.
