# Search (SEO) workstream

Getting YardScout's server-rendered pages found in search. Owns
`backend/site-proxy/src/share.js` (the rendered pages and sitemap), the routes
for them in `backend/site-proxy/src/index.js`, their tests
(`backend/site-proxy/test/junkyards_unit.mjs`, `prices_unit.mjs`, the www
cases in `redirects_unit.mjs`), `docs/404.html`, and the search-facing parts
of the `docs/index.html` head. Starts on an owner ask. The audit behind this
work is dated 2026-11-12 (YardScout appeared in none of 13 searches, its own
name included).

## Rules for every rendered page (tests enforce them)

- One `<h1>`, and it says what the page is. The header wordmark is a `<p>`.
- Titles, descriptions and counts come only from the data file that render
  used. No "best", no ratings, no fitment claims.
- JSON-LD is `BreadcrumbList` and `ItemList` only (plus `WebSite`,
  `Organization`, `MobileApplication` on the home page). Never `Vehicle`,
  `Product`, `Offer` or `aggregateRating`.
- No new fetches beyond the data files the worker already reads; price files
  and the junkyards index are parsed once per isolate and cached.

## Model pages: branch `seo/model-pages`, not merged, not deployed (2026-11-13)

Business plan priority 8 and the r/XTerra lesson (a weekly per-model list,
state first). `/landed/<make>/<model>`, e.g. `/landed/nissan/xterra`
(slugs are `slugify()` of the scan's make and model names).

- **Threshold:** 100+ cars on the lots now, or 10+ set out in the last 7
  days. 2026-11-13 scan: 380 + 25 = **405 model pages across 40 makes**.
  No-pick and blank model names never get a page. Constants
  `LANDED_MODEL_MIN_ON_LOTS` / `LANDED_MODEL_MIN_WEEK` in the scraper.
- **Data:** `docs/data/landed/index.json` (~14 KB: models with pages and
  their counts) and one file per make (`landed/<make>.json`, 41 files,
  ~2.1 MB in all, Ford largest at ~290 KB), written each scan by
  `_write_landed_models_json` beside landed.json (same counting rules).
  Per car: year, yard, row, date, drive ("4x4"/"AWD"/"2WD"/"" from the VIN
  decode), notable trim ("" unless the app's badge rule names one; Python
  port of `notableTrimHits`, checked equal to app.js on all 108,723
  candidate decodes of the 11-13 scan), share key.
- **Pages:** query-shaped title/H1, lead with count, yards, states, scan time;
  the whole week's list by state (A–Z), then yard (newest first), then car;
  jump list; "On the lots now" by-state table (so a zero week still has a
  page); CTAs `/#cars=Make|Model` and `/#watch=Make|Model`; stores line;
  honest note; links up (make), across (sibling models), hub (junkyards).
  JSON-LD BreadcrumbList + ItemList (newest 100 cars). Unknown → 404 noindex;
  data unreadable → 503 "briefly unavailable"; **before the first scan writes
  `docs/data/landed/`** (index 404) → 503 noindex holding page linking the
  make page. Nothing links to model pages until the index exists.
- **Wired:** sitemap (lastmod = scan), make pages (model headings + "every
  model" grid), `/landed` hub (top 24 models this week), car pages ("Every
  <Make> <Model> set out this week"), yard pages (model tiles link).
- Tests: `node test/model_pages_unit.mjs` (57) beside the three above;
  scraper `python3 scraper/test_landed_models.py` (52 checks, incl. a node
  run of app.js for the trim rule).

**On merge:** `deploy-workers.yml` deploys the Worker (path `backend/**`);
the next 4-hourly `scan.yml` run that starts after the merge writes
`docs/data/landed/`; GitHub Pages serves it a few minutes after that scan's
commit. Until then model URLs answer the holding page. Owner: submit the
sitemap again in Search Console once the files are live.

**Open / next:**
- The make page caps its list at 40 ("the nationwide search is Pro's Any
  distance"); model pages list the whole week, as the Reddit post did.
  Owner's call if that should change.
- AWD is printed as "AWD" (neither bold 4x4 nor 2WD).
- Truck trims (TRD Pro, FX4, PRO-4X…) rarely show: the VIN decode does not
  name them (ops/hub.md 11-13).
- Suggest: a "this week in <state>" filter or `/landed/<make>/<model>/<state>`
  pages if the model pages get traffic; Reddit replies can link the model
  page (`ops/reddit.md`) instead of the app hash.

## Status: branch `seo/onpage-1`, not merged, not deployed (2026-11-12)

Merging to main deploys the worker (`deploy-workers.yml`) and the Pages
files. The hub merges after review.

1. **On-page basics.** Real `<h1>`s; query-shaped titles; BreadcrumbList and
   ItemList; links between yard, city, state, make and car pages; sitemap
   with `<lastmod>`, the home page, and `/sitemap.xml` (it returned 503);
   `Last-Modified` headers; www to apex 301 for rendered routes (after
   `/open` and `?app=1`); "near <metro>" pages for Seattle, Las Vegas and
   San Diego; `docs/404.html`; home title, static "300+", JSON-LD and
   visible hub links (sw `jh-v181`).
2. **Yard pages are inventory pages.** H1 "<Yard> inventory", cars by make
   (top 12) and model (top 15, with model-year span), newest arrivals, map
   link. Counts only: the car-by-car list and search stay in the app.
3. **Price lists.** `/prices`, `/prices/<chain>`, `/prices/<chain>/<yard>`
   (only where a yard's list differs). Car pages link to them instead of
   carrying the list; yard pages show a short common-parts table.

Tests: `cd backend/site-proxy && node test/junkyards_unit.mjs && node
test/redirects_unit.mjs && node test/prices_unit.mjs` (222 + 51 + 39 checks).

## After the merge (owner)

- Search Console and Bing Webmaster Tools: confirm the property, submit
  `https://yardscout.io/sitemap.xml`, request indexing for `/junkyards`,
  `/yards`, `/landed`, `/prices`. No session can do this.
- Check on the live site: `/sitemap.xml` is 200, a made-up path shows the
  branded 404, `www.yardscout.io/landed` redirects, and the iPhone
  "Open the app" button still opens the app.

## Owner decisions open

- Price pages show each yard's full published list, engine and transmission
  rows included, as the app's price sheet does. Catalytic converter rows are
  never shown. Say if engines and transmissions should be hidden too.
- Yard pages now show counts by make and model. Say if that is more of the
  lot than should be public.
- Car pages stay indexable (the audit suggested `noindex` until they had
  content of their own; they now do, and the price list is gone from them).

## Deliberately left

- **Measurement beacon** on rendered pages (referrer, landing page type,
  crawler counts): waits for the owner's wording of the "no analytics" line
  in `docs/privacy.html`.
- **Make/model pages**: built as `/landed/<make>/<model>` (see above); was: needs a per-model aggregate
  from the scan (scraper change) and a call on free versus Pro detail.
- **Interchange pages**: the Interchange workstream's release gate applies.
- **Store listing text**: needs the owner's "ship" (standing rule 1).
- **Yard deep link** for the "Search this yard" button: a `docs/app.js`
  change, not made here.
- **Price list read date**: the price files carry none. Adding one is a
  scraper change (Yards or Data workstream); the pages will show it once it
  exists.
- **A gone car's yard and make** on its 404 page: the API keeps no record of
  a car once it leaves, so the page links to the hubs instead.
- `robots.txt` still names `/sitemap-yards.xml` (same body as
  `/sitemap.xml`). `ops/README.md` has no row for this workstream yet.

## Store screenshots, round 2 (2026-11-12)

Branch `store/screenshots-2` (not merged): six new slides per store, a
headline over a real light-theme capture, built by
`tools/capture_store_shots.py` (rewritten: serves docs/ itself, runs the page
as the native shell with stubbed plugins, blocks API/analytics calls, then
composes the slides). Zip 78219 (San Antonio, Wrench-A-Part photos carry no
watermark; Pick-n-Pull photos carry a ROW52 mark and Pick Your Part a PYP
logo, so those yards were avoided). Files renamed 01_cars … 06_value; the old
01_live … 06_alerts were removed so the upload does not carry twelve.
Waiting on the owner's look. Upload: iOS goes up with the next
`release-ios.yml` run with `submit=true` (needs "ship"); Play with a manual
`store-listing.yml` dispatch.
