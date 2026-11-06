# Yards workstream — status (updated 2026-11-06, vehicle photos)

Owns: independent-yard adapters in `scraper/junkyard_scraper.py`
(`INDEPENDENT_FETCHERS`), `scraper/independent_yards_registry.json`,
`scraper/INDEPENDENT_YARDS.md`, `scraper/coverage_sweep.py` +
`coverage-sweep.yml` (monthly, 70-min budget), `coverage_sweep.md/json`,
`scraper/gen_yard_site_links.py` → `docs/data/yard_site_links.json`.

## Rule

No bypasses. A yard that blocks the scraper (Cloudflare, Sucuri, captcha)
gets an email asking for a feed or permission. The existing Harry's Sucuri
solver is left as is; no new solvers. Yards without inventory online are
directory-only entries.

## State

| Yard | State |
|---|---|
| Bevell's Pull It Yourself (NC) | adapter live (`fetch_bevells_inventory`, 50 rows/page, hash ids) |
| Blue & Gold | directory-only, no website |
| Ewe Pullet | not added: site renders no inventory cards |
| U-Pull-R | blocked (Cloudflare Turnstile). Email sent 2026-11-03 to sales@ and jessef@upullrparts.com. sales@ bounced (Microsoft 365 550 5.4.1, address rejected); jessef@ (the contact from the owner's call) did not bounce, so it was delivered. Do not use sales@ again; reader stops at the first 403. Watch in `ops/hub.md`. |
| Harry's | Sucuri; the owner is sending a note via their contact form |
| Pull-N-Save, Budget, Route 34 | outreach sent 2026-11-02, no reply yet. Budget: sales@budgetupullit.com delivered; the CC to Craig@budgetfl.com bounced (user does not exist). |
| Harold's Auto Parts U-Pull-It (Briggs TX) | registry `candidate`. Ario feed embedded on their own site, 612 cars, but all set out 2026-09-09..09-29 and none since (looks like a one-time load). Wire it as config-only in `ARIO_CHAINS` once set-outs newer than 30 days appear. Refine the pin to the parcel first. |
| Young's U-Pull-It (Dudley NC) | directory-only. The site's "inventory" is a full-service part-type search; latest-arrivals shows no cars |
| Sam's Pull-A-Part (Worcester MA) | directory-only. Linder's recent-arrivals is their full-service stock, not the self-service lot |
| Route 50 U-Pull-It (Mays Landing NJ), U-Pull It Auto Salvage of Paducah (KY) | directory-only, no website |
| **OKC Pull-A-Part** (Oklahoma City OK) | **adapter live** (`fetch_okcpap_inventory`): 1,025 cars at build, from one WebForms POST per make. The name avoids the "Pull-A-Part" prefix, which the app keys the national chain on. No dates or VIN on the site. Test: `test_okcpap.py` |
| UAPI Bossier City / South Shreveport | already tracked. Their pins were copies of North Shreveport's and are now fixed (address geocodes) |
| Ewe Pullet (SD) | still `candidate`: no cards render on any inventory page (re-checked 2026-11-04) |
| Wally's U-Pull-It (Oshkosh WI) | directory-only. Devtools check 2026-11-04: its "inventory" is the URG iis-pro-v2 parts locator (year → catalog make → model → part category). The make list is a parts catalog (2010 lists Tesla, Kenworth) and no endpoint lists lot vehicles |
| Littleton U-Pull (CO), Andersen's U-Pull-It (Greeley CO, now Alter Trading), One Stop You Pull It (Klamath Falls OR), Vince's U-Pull-It (Marcy NY) | directory-only, no online inventory |
| U-Pull and Save Mason (MI), Pick A Part of Arizona (Phoenix, Mesa), A-1 Metals (CA) | registry `retired` so the sweep skips them: vehicle purchasing only / closed to the public / not self-service |

Outreach drafts: `ops/yard-outreach-drafts.md` (all sent except Harry's).
No new drafts from the 2026-11-04 sweep review, because no checked yard blocked us.

## 2026-11-04 sweep review

`coverage_sweep.md` (2026-11-03) had 0 tier A, 0 tier B and 0 tier C, so no
adapters were built and no outreach was needed. I checked every named tier D/E
yard by hand. Per-yard outcomes are in `scraper/INDEPENDENT_YARDS.md`, under the
2026-11-04 section. Not added: A-Z U-Pull-It PA (listed closed), TAS Kingsport,
Salisbury MA and A-1 Metals CA (full-service), Jamm, Jalopy Wizards, Southern
Auto Salvage and Gaston Towing (no site, self-service unconfirmed), Yank A Part
(1 row from 2024), and vendor test/demo orgs. I added `ario_slug` to Bevell's,
Blue & Gold and Prestige so the sweep stops re-listing them.
`coverage_candidates.md` is the Parts workstream's report and has no yard tiers.

Sweep coverage gap. On 2026-11-03 OSM covered no state at all (60 s client
timeout, dead mirror, "3 failed states → stop", Ario eating the discovery
budget). The first fix (ff72088) made the timeouts long and the retries
patient. Its run (41852487799, 2026-11-04, 70 min, dispatched by the hub)
covered only 5 states: AR 2 yards, CA 20. AL, AK and AZ failed on all three
servers (overpass-api.de 502, kumi and private.coffee read timeouts at 210 s),
about 10 minutes each. The real problem was the query: a case-insensitive name
regex over every named object in a state is too heavy for the public servers.
`osm_pending` now holds the 48 uncovered states, and the next run resumes from
them.

Second fix (this commit, unconfirmed live):
- `overpass_query` selects by exact, indexed tags first (`OSM_TAG_CLAUSES`:
  shop=car_parts/car/car_repair/scrap_yard, industrial=scrap_yard/auto_wrecker,
  landuse=industrial, amenity=scrap_yard/recycling, craft=car_repair). The
  name regex sits inside every clause (`nwr["shop"="car_parts"]["name"~RE,i](area.s);`),
  so nothing is collected before it is filtered. A collect-then-filter step
  would first materialise every shop=car or landuse=industrial element in
  CA or TX (the hub's review). The query uses `[timeout:90]` and
  `[maxsize:64MB]`, and the client read timeout is 120 s.
- Trade-off: a yard mapped with a name and no tag is missed. Compare CA's
  count with the 20 found by the name-only query.
- 502/503/504 move to the next server at once. Only 429 gets a same-server
  retry (after 30 s).
- Any server failure is a strike, and 3 in a row skip that server for the
  pass. If every server fails the first states, the pass stops (worst case
  about 3 states × 3 servers × 2 min) and everything stays pending.
- The retry pass runs only when some server answered.
- No geographic tiling: the repo has no reliable state bounding boxes, and the
  indexed query should make a whole state cheap. If the next run still fails
  on whole states, add tiling then.
- New `--osm-pending` mode, also the `osm_pending` dispatch input of
  coverage-sweep.yml (plus a `budget_min` input). It skips Ario, queries only
  the pending states with 75% of the budget, checks the new sites, merges into
  the existing report and shrinks `osm_pending`. Dispatch it repeatedly until
  the list is empty. With nothing pending it exits without changes.
- Weekly schedule (owner-requested 2026-11-04): `17 11 * * 1` (Mondays,
  11:17 UTC) runs the `--osm-pending` pass. It exits with no commit when
  `osm_pending` is empty. The monthly full sweep (`43 9 3 * *`) is unchanged
  and shares the concurrency group, so the two never overlap.

Third run (41861399360, osm_pending, on d982e71): covered 0 of 48 states. AL,
AK and AZ failed on all three servers (overpass-api.de 502 or read timeout,
both mirrors read timeouts), then the pass stopped as designed after
17 minutes. Even AK failed with the cheap per-clause query, so query size is
not the cause. The suspects now are the `area["ISO3166-2"=...]` lookup, or the
servers refusing or throttling GitHub runner IPs.

Third fix (unconfirmed live):
- **Diagnostic step:** before the sweep, `coverage-sweep.yml` runs
  `coverage_sweep.py --diagnose` (continue-on-error, 5 min cap). For each
  server it logs GET /api/status and a tiny Anchorage bbox query, each with
  its HTTP code and seconds.
- **Bbox tiles:** `area[...]` is gone. States come from `STATE_BBOX`, the
  Census 2023 cartographic boundary extents. Alaska is clipped at 179.2 W, at
  the antimeridian.
- **Tiling:** states larger than 4° are tiled (Alaska at 8°), 179 tiles in
  total. A state counts as covered only when all its tiles answer.
- **De-duplication:** results are de-duped across tiles and states by OSM
  element id. A row whose `addr:state` names another state is left to that
  state. A row with no `addr:state` in an overlap of several state boxes keeps
  a blank state instead of a guess.
- **Pending order:** `osm_pending` now lists unqueried states first and
  failed ones last, so a pass no longer hits the same failing states first
  every time.
- **Stop rule:** if the diagnostics show the servers refuse runner IPs
  outright, the hub takes it to the owner. Nothing will work around it.

Fourth run (41868290780, on 56fae4b): the diagnostics showed the runners are
**not refused**; the public servers are just overloaded. overpass-api.de took
35.8 s to answer a 1-element bbox query and its /api/status timed out. kumi
and private.coffee timed out on both checks. Then AL, AK and AZ failed again,
and 0 states were covered.

Fourth fix: discovery now uses **Geofabrik state extracts**
(`fetch_osm_geofabrik`, the default; `--osm-source overpass` keeps the old
path).
- One sequential download per state from
  `download.geofabrik.de/north-america/us/<slug>-latest.osm.pbf`, with the
  honest UA, 5 s between states and one retry after 429/503.
- Slugs and sizes are from Geofabrik's index page (2026-11-04): 21 MB (DE) to
  1.2 GB (CA), about 11.6 GB for all 50. The page states no download limits
  beyond the ODbL licence.
- Each file is filtered locally with `osmium tags-filter` (the same tags as
  `OSM_TAG_CLAUSES`) and `osmium export -f geojsonseq -a type,id`. The name
  filter and centroids are done in Python, one row per OSM id.
- The pbf and intermediates are deleted before the next state. A download is
  refused when free disk is under 2.5× its size, and short reads fail.
- Same `osm_pending` contract (unqueried first, failed last) and deadline.
- The workflow installs osmium-tool via apt and logs `df` before the sweep.
  The Overpass diagnostics step runs only with `osm_source=overpass`.
- Tests: mocked downloads and osmium cover the retry, disk guard, short read,
  cleanup, a missing osmium, the deadline and de-duplication across states.
  A real osmium 1.16 test on an inline .osm fixture (skipped where osmium is
  absent) caught that osmium exports a closed area way twice, as a LineString
  and a Polygon. That is now de-duped, and the closing point is no longer
  counted in centroids.

Tests: `scraper/test_coverage_sweep.py` all pass offline, with mocked cases for
the query shape, fast failover on 502, the stop when all servers fail, the
retry pass, 429 handling, the merge, and the `--osm-pending` paths. Live
Overpass is unreachable from the Claude sandbox, so the speed of the new query
is untested until a run happens. After that run, review any tier A/B rows.

## 2026-11-04 review of the Geofabrik sweep (runs 41872828891 + 41881651649)

The Geofabrik source covered 48 of 50 states; WA and AL hit download read
timeouts. The report had A:1, B:5, D:4. I checked each by hand:
- **A, Ewe Pullet:** unchanged, no cards. Stays candidate.
- **B, U Auto Pull It (Bossier City):** already tracked as UAPI. The
  sweep missed it because our pin was wrong: three UAPI yards shared the
  North Shreveport pin. Fixed (c58e2a6).
- **B, U-Pull and Save (MI):** the Mason store. The site says "Vehicle
  Purchasing Only" and its store has 0 arrivals. Recorded as retired.
- **B, Pull-A-Part Auto Parts Yard (OKC):** independent, self-service,
  inventory open on its own site. Adapter built (6e9bcb4).
- **B, Pick A Part (Phoenix, Mesa):** "Closed to the Public", inventory
  empty since 11/17/24. Recorded as retired.
- **D:** Littleton (dead site), Andersen's (Alter Trading, no inventory
  page) and One Stop Klamath Falls (no inventory) became directory-only.
  A-1 Metals (not self-service) was recorded as retired.
- **E, quick pass:** Wally's became a candidate and Vince's directory-only.
  Danny's U-Pull (Tulsa), Lambert's Pick-a-Part (Powell TN), Grand Junction
  Pick-A-Part (CO) and the rest have no website, so they stay in tier E.
  Barry's Pass Christian MS is the second Barry's yard, already inside
  Barry's blended table (documented in the adapter).

No yard blocked us, so no outreach drafts. No emails were sent.

Sweep follow-ups (mine):
- **Done:** Geofabrik downloads now retry once on a transient network error,
  with a 300 s read timeout (f9838c7). WA and AL stay pending for Monday's
  pass.
- **Fixed (owner-requested, 2026-11-04):** six of the seven chain-yard pins
  the sweep exposed. Pull-A-Part Jackson, Memphis, El Paso and Aurora were
  ZIP centroids 3.6–4.6 km off. Utah Pic-A-Part Orem was 3.2 km off and
  U-Pick-It Flagstaff 8 km off (a Leupp Road centroid). Each was re-pinned
  from the yard's street address: Pull-A-Part's own Location API, utpap.com
  and upickitaz.com. Each was checked against a Nominatim or Census geocode
  and/or the named OSM yard feature on the right road. Pick-n-Pull Portland
  South was already correct: Pick-n-Pull's feed pin matches 6241 SE 111th
  Ave exactly. The OSM "Pick-n-Pull" way/318885801 9 km away is a different
  or stale feature. The app shows the new pins after the next scan
  rewrites docs/data/junkyards.json.
- **Done (owner-requested, 2026-11-04):** the other 31 `PAP_COORDS` entries
  were ZIP centroids 0.5–6 km off. They are now geocoded from the street
  addresses in Pull-A-Part's Location API:
  - 21 confirmed by the US Census geocoder and Nominatim agreeing within
    500 m.
  - 1 (Atlanta East) confirmed by a named OSM "Pull-A-Part Atlanta East"
    yard 170 m from the Census point.
  - 9 are Census exact-address matches only (Augusta, New Orleans West
    (Harvey LA), Baton Rouge, Indianapolis, Tucson, West Palm Beach, Orlando,
    Colorado Springs, Pittsburgh). For these Nominatim found nothing, the
    wrong place, or only the street, and pullapart.com's pages give only
    "directions to <address>" links.
  - Each entry's comment names its basis. Largest moves: Tucson 6.1 km,
    Albuquerque 5.6 km.
  - The app shows the new pins after the next scan.

## 2026-11-06 vehicle photos: coverage, capture, native fit

**Status: done.** Study, capture, remote kill switch and design hand-off.
Basis, from `ops/hub.md`:
- 2026-11-06 ~18:30 UTC: chain-hosted photos, own URL, credit, kill switch.
- ~18:40 UTC owner exception, verbatim: "its fine to put pick-n-pull photos
  even with the water mark. I'll take it down if they request it but it
  attracts customers to them". Pick-n-Pull's API photo URLs (Row52 CDN) are
  now captured under their own switch. Nothing else from Row52.

Owner priority (via hub): "low risk but the best UX. No lawsuits."

### Coverage (scan of 2026-11-06 16:51Z: 334,499 lot cars)

Lot counts come from `inventory_live.json`. Photo counts come from the
`vehicle_extras.json` photo column, plus one sample request per source for
chains not captured today. No crawling beyond what `scan.yml` already
fetches.

| Chain | Lot cars | With photo URL | Host | https | Whose host | Captured before today | Sample (≤3 imgs, plain GET; with and without a yardscout.io Referer) | Stable across scans | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| LKQ Pick Your Part | 72,188 | 66,041 (91%) | cdn.pypapps.com | yes | LKQ's own CDN (PYP watermark) | yes, `p<id>` | 3/3 200, image/webp, 640×427, 17–40 KB, no referer check, no CORP, max-age 7 d | 65,075/65,075 identical over 16 h | **pass** |
| Wrench-A-Part | 11,274 (`wap-*`) | 9,612 (85%) | storage.googleapis.com/wrench-car-photos | yes | WAP's own GCS bucket | **no, added today** (`w` code) | thumb 240×320 JPEG ~15 KB; old ".png" shape is served as a 320×240–392×294 JPEG, 40–70 KB; full 1536×2048 ~450 KB; 200 both ways; max-age 1 h | path carries an upload timestamp; first capture, so not yet compared across scans | **pass** |
| Weller Self Serve | 1,380 | 1,373 | ik.imagekit.io/rm8xun1iy5t | yes | Weller's own ImageKit account (a CDN vendor, not a competitor) | yes, full URL | 3/3 200 JPEG 960×1280, 68–136 KB, max-age 1 y | 1,363/1,363 | **pass** |
| Pasco EZ Pull It | 901 | 901 | cdn.shopify.com | yes | the yard's own Shopify store files | yes, full URL | 3/3 200 JPEG 400×533 / 400×300, 20–50 KB | 901/901 | **pass** |
| Kiker's U-Pull-It | 656 | 656 | www.kikersupullit.com | yes | own site | yes, full URL | 3/3 200 JPEG 1600×1200, **320–420 KB**, immutable | 653/653 | **pass**, but heavy (see data cost) |
| Army's Auto Wrecking | 238 | 14 | api.yardsmartapp.com | yes | YardSmart (platform vendor) | yes, full URL | 3/3 **404**: signed blob URLs whose token expires within hours | 0/14 | **fail**, do not enable |
| Pull-N-Save | 9,008 | every row (658/658 in a Honda sample) | app.pullnsaveapp.com | yes | own app domain | no | URL is built from the stock #. A real photo is a 200×200 PNG of ~100 KB; a car without one gets a 3,474 B "no image" PNG at the same kind of URL | n/a | **fail**: the feed can't tell real photos from placeholders without fetching every one |
| Pick-n-Pull | 47,440 | ~47,150 (99.4%: 4,754 of 4,782 in a national Honda sample) | cdn.row52.com (Azure blob) | yes | **Row52, PnP's photo partner and a competitor**; owner exception 2026-11-06 | **added today** (`n` + 32 hex, from the API's `imageName`) | all 200 with and without a yardscout.io Referer; `access-control-allow-origin: *`; no content-type header but no `nosniff` either, so `<img>` sniffs it (real JPEG); imageName 600×400 ~41–47 KB with the Row52 watermark intact; max-age 600 | blob GUID with last-modified = upload time; not yet compared across scans | **pass** (owner exception) |
| Pull-A-Part | 42,385 | 0 | — | — | — | — | `Vehicle/Search` has no image field | — | none |
| Fenix U-Pull | 5,758 | 0 | — | — | — | — | page 1: all 50 rows show the theme's `placeholder-150x100.jpg` | — | none |
| yardconnect-pro tenants (U-Pick-It AZ 3,098; Chuck & Eddie's, Genesis, Robertson's, Barry's, Hwy 82, Route 34, Sunshine) | — | thumbnails in table | api.yardsmartapp.com | — | YardSmart | no | **not sampled**; same signed-blob backend as Army's, so expect the same expiry | — | not pursued |
| Ario tenants, CRUSH (Sturtevant, St. Cloud), Ace | — | image column/field noted in code | — | — | — | no | **not sampled** (Ario is rate-limited; Ace is Cloudflare-blocked in CI) | — | open |
| All other chains | — | not checked: their fetchers note no image field | | | | | | | open |

**Total that passes: ~125,700 of 334,499 lot cars (~37.6%).** LKQ 66,041,
Pick-n-Pull ~47,150, Wrench-A-Part 9,612, Weller 1,373, Pasco 901,
Kiker's 656.

LKQ crop: the original is 1280×720 with the PYP watermark bottom-right. The
old card URL used `mode=crop` to 640×427, which trims the sides and can
clip the mark. The card now uses `mode=max` (640×360, whole image), and the
large form is the original file. Pick-n-Pull's 600×400 image already shows
its full Row52 watermark.

### Capture (on main, data only)

Commits: 9343692d (Wrench-A-Part) and 3662bf2c (kill switch + Pick-n-Pull).
`fetch_wrenchapart_inventory` now stores `_photo` = `_wap_photo_code(item)`.
The code takes one of two forms:

- `w{yard}/{VIN}/{ms}.j` for the feed's `photoThumb`
  `…/v1%2F{yard}%2F{VIN}%2F{ms}-front_driver-thumb.jpg`
- `w{yard}/{VIN}/{ms}.p` for the older `photo` `…%2F{ms}.png`

Any other URL shape gets no code. Test: `scraper/test_wap_photo.py`.
`_pnp_ingest_group` stores `n<32 hex>` from the API's own `imageName`
(`_pnp_photo_code`). Test: `scraper/test_photo_sources.py`. All 21
`scraper/test_*.py` pass.

`vehicle_extras.json` size, simulated on today's data: 14,898,768 B before.
After WAP it is 15,246,089 B (+2.3%). After WAP + PnP + photoSources it is
16,807,722 B (+12.8%); gzip goes 2.03 → 3.03 MB, because GUIDs don't
compress. It is still lazy and off the critical path. The `inv/` shards carry
the same per-car codes for their own yards. It stays a
lazy shard. The app renders nothing for `w` codes until a `PHOTO_SOURCES`
entry exists and is enabled. Army's capture is left as is: its URLs are dead
on arrival, and `photoInfo` must never render them (see the hand-off).

### Remote kill switch (`scraper/photo_sources.json`)

Each source has `enabled`, `label`, `host`, and `patterns`: anchored regexes
valid in both Python and JS, with `card`/`large` URL templates using `{1}`…
At write time (`_write_extras_and_shards`, after stale-keep) the scraper
blanks every photo code that no enabled pattern matches. It publishes the
enabled sources as `photoSources` in `vehicle_extras.json` and in
`data/inv/manifest.json`. The app renders only through that published map,
so a source missing from it means no photo, even if a stale code survives
somewhere. Missing or unreadable file means no sources: it fails closed.
`armys` is listed but off. Pull-N-Save has no entry and no capture.

### Photo takedown

1. In `scraper/photo_sources.json`, set the chain's `"enabled": false`
   (do not delete the entry). Commit to main: `photos: takedown <chain>
   (<who asked, date>)`.
2. Dispatch a scan:
   `gh api -X POST repos/benvuolo/yardscout/actions/workflows/scan.yml/dispatches --input body.json`
   with `{"ref":"main"}`. Takes the usual scan time.
3. The scan commit drops that chain from `photoSources` and blanks its codes
   in `vehicle_extras.json` and `inv/` shards. Web and every installed native
   version stop showing the photos on their next data fetch: the manifest is
   revalidated on each launch, and no app release is needed.
4. Check: `photoSources` in `docs/data/inv/manifest.json` on main lacks the
   chain, and `grep -c` of its code prefix/host in `vehicle_extras.json` is 0.
5. Reply to the requester (the terms page promises usually within 24 h) and
   log it under this section with the date.

### Native fit (iOS WKWebView / Android WebView, Capacitor 8)

- No CSP anywhere: no `<meta http-equiv>` in `docs/index.html`, none in
  `backend/site-proxy`, no `_headers`. Nothing blocks `img-src`.
- iOS: `Info.plist` has no `NSAppTransportSecurity`, so default ATS applies.
  All passing hosts are https on major CDNs. TLS couldn't be checked from here
  (the session proxy terminates TLS). The one small origin worth a device check
  is www.kikersupullit.com (needs TLS 1.2+ with forward secrecy).
- Android: no `networkSecurityConfig`, and cleartext is off by default. All
  passing hosts are https, so nothing changes.
- `capacitor.config.json` `server.allowNavigation` only governs navigation,
  not `<img>` subresources, so no change is needed.
- **No native project changes are needed.**
- The service worker skips cross-origin requests (`docs/sw.js:41`), so yard
  images are never cached or rehosted by us. The `jh-vNNN` name is unaffected
  unless the shell changes.
- Referer: WKWebView on `capacitor://localhost` sends none, and Android sends
  `https://localhost/`. Every host returned 200 with no Referer and with a
  cross-site Referer.
- Lazy loading: `loading="lazy"` works in WKWebView on iOS 15.4+ and in
  Android WebView (Chromium 77+). WebP (LKQ) works on iOS 14+.
- Decode size: cards should use the small form. A full 1536×2048 WAP shot
  decodes to ~12.6 MB RGBA; a Kiker's 1600×1200 to ~7.7 MB. Load the large
  form only on tap-to-enlarge, with `decoding="async"` and width/height set.
- Cellular cost per car screen (one photo): LKQ ~17–40 KB, WAP thumb ~15 KB
  (old shape 40–70 KB), Pasco 20–50 KB, Weller 68–136 KB, Kiker's 320–420 KB.
  A list screen of 20 LKQ cards is ~0.5–0.8 MB. Kiker's only offers the
  full-size file. Weller's ImageKit could serve a smaller size with `?tr=w-480`
  (not tested here).
- Privacy note for the owner: a hotlinked image sends the viewer's IP and UA
  to the yard's host. The privacy policy / App Privacy answers should say
  that images load from yards' servers. No tracking is involved.

### Hand-off to design (sent 2026-11-06 to session_016ZzJfKjBN7He2RMxFV9A8z)

Superseded by a second message (also 2026-11-06). The app now renders from the
published `photoSources` (no hard-coded hosts), uses object-fit: contain
(never crop a watermark), and adds a viewer credit, a "View on <yard>" link
and a "Photo owner? Request removal" mailto. Pick-n-Pull is added; sw must be
jh-v150+. The first message is kept below for the record.

> Photos, from the yards workstream (owner decision: ops/hub.md 2026-11-06
> ~18:30). `docs/app.js` `PHOTO_SOURCES` / `photoInfo` on
> design/pull-sheet:
> 1. `pyp`: keep the entry and set `enabled: true`. Code `p<id>`, label
>    "Photo: LKQ Pick Your Part", URL as now (640×427 webp).
> 2. Add `wap`: label "Photo: Wrench-A-Part". Code `w{yard}/{VIN}/{ms}.j|.p`.
>    `const [y,vin,ms]=code.slice(1,-2).split('/'), b='https://storage.googleapis.com/wrench-car-photos/v1%2F'+y+'%2F'+vin+'%2F'+ms;`
>    For `.j`, card = `b+'-front_driver-thumb.jpg'` and large = `b+'-front_driver.jpg'`.
>    For `.p`, card = large = `b+'.png'`.
> 3. Full-URL codes (start with `https://`): pick the source by exact host,
>    and render only these hosts:
>    `www.kikersupullit.com` → "Photo: Kiker's U-Pull-It";
>    `ik.imagekit.io` with path prefix `/rm8xun1iy5t/` → "Photo: Weller Self Serve";
>    `cdn.shopify.com` with path prefix `/s/files/1/0731/9250/5650/` → "Photo: Pasco EZ Pull It".
>    Never render `api.yardsmartapp.com` (Army's signed URLs expire, 404),
>    `cdn.row52.com`, or `r…` codes. Unknown hosts → null.
> 4. Each source keeps its own `enabled` kill switch, and `photoInfo` returns
>    null when it is off.
> Display: photo on the car card and the car screen. `loading="lazy"`,
> `decoding="async"`, inside a fixed aspect-ratio box (4:3 is fine; object-fit:
> cover) so nothing shifts. A clean CSS placeholder sits under it; `onerror`
> hides the img, so no broken-image icon ever shows. The credit line
> "Photo: <yard>" sits under the image. Tap opens the large form. The photo
> must not affect the no-truncation check (the box takes its own row/column;
> titles and part names keep their width). Kiker's files are 320–420 KB:
> fine on the car screen, and acceptable on cards with lazy load.
> No native config changes are needed (no CSP/ATS/Android rules block these
> https hosts). Details: ops/yards.md "2026-11-06 vehicle photos".

## Next

1. When a reply arrives: build the adapter from whatever feed they offer,
   add a `test_<yard>.py`, register in `INDEPENDENT_FETCHERS`, add the pin
   and site link.
2. Re-check Harold's Ario feed for fresh set-outs (one `_ario_live_post` call).
3. After each monthly sweep: review tiers A–B in `coverage_sweep.md`, verify
   each has self-service inventory online before adding.
4. Chains frozen for 6+ scans show in the daily email as `chain-frozen:<chain>`.
5. Photos: after the next scan, confirm `photoSources` in `inv/manifest.json` and real PnP/WAP code counts; compare PnP/WAP URLs across scans. Sample the Ario, CRUSH and remaining chains, and re-check WAP URL stability after a few scans.
