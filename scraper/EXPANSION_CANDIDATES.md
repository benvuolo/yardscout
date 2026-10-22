# Expansion Candidates — Platform-First Research Pass

*Research date: 2026-10-22. Pure research — no scraper changes in this commit.
Companion to `scraper/INDEPENDENT_YARDS.md` (onboarding history) and
`scraper/independent_yards_registry.json` (machine-readable registry).*

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
