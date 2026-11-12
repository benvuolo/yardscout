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
- **Make/model pages** (`/cars/<make>/<model>`): needs a per-model aggregate
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
