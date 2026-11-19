# Design — workstream status

Owner brief (2026-11-06): the app "looks obviously vibecoded"; wants a unique,
user-friendly layout, keeping the logo and colour scheme. Screenshots first,
nothing to prod until the owner decides.

## State (2026-11-06, evening) — Direction A built on `design/pull-sheet`

Owner (via hub, 2026-11-06): "for the design stuff do what you think. I want no
words cut off and I want everything super clean. I'll want to test this test
flight for sure." Hub chose A and answered the three questions: part names free
(prices/values stay Pro, every other gate unchanged); "Saved" renamed "Pull
sheet" in the UI only (jh_saved and watch storage untouched, rule 6); map deferred.

- Branch `design/pull-sheet` (from main 7ae3af1; head ad26151; NOT merged). Touches only
  docs/app.js, docs/index.html, docs/styles.css, docs/sw.js (jh-v146) and adds
  backend/test/ui_no_truncation.mjs. No native, store or workflow changes.
- Steps done, one commit each: 1 tokens · 2 base styles (one button system,
  44px targets, no ellipsis/nowrap, no hazard stripe/card rails) · 3+4 car card
  (row plate, stay meter, one "Add to pull sheet" action) and car screen (pushed,
  sticky action bar with pull sheet / watch / share, "If equipped" group apart,
  VIN, directions) · 5 zip chip beside Filters · 6 Pull sheet rename + tappable
  rows, watch hits as pull-sheet cards, shorter Pro sheet with one-tap
  "Already have Pro?" placed after every purchase flow.
- Free tier now sees part names + fitment markers (alphabetical, so the value
  order stays Pro); yard price, online price, savings, sell speed stay locked.
- Guard: `node backend/test/ui_no_truncation.mjs` serves docs/ and checks 18
  screens at 320/375/390/430/768/1280, light+dark, 100%+200% text: no
  ellipsis/line-clamp, no text wider than its box or clipped, no sideways
  scroll, fields fit their text, 44px targets, WCAG AA contrast.
- Deferred: combined part-or-car search box (step 5 second half). (B's walk-by-row yard view and the
  map have since shipped: Rounds 8 and 9.)
- Not run here: python e2e scripts (backend/test/*_e2e.py need the Python
  playwright package, not installed in this container).
- Next: hub builds TestFlight from the branch for the owner. Merge to main
  only on the owner's word; releases still need the owner's "ship".

### Round 2 (2026-11-06, after the owner tested TestFlight 28: "looks good")
- Branch head a36ffbc (merged main; branch shell jh-v148, main jh-v147).
- Car screen leads with "Worth pulling": the top picks (up to 5) by value. Pro
  sees a value per pick plus a top total; free sees the same names and one
  quiet Pro line. Then "Also on this car" (collapsed), the labelled whole-car
  figure (Pro), "If equipped". Cards, pull sheet and watch hits lead with the
  top picks (free sees the value order now; hub's call).
- Tests at a36ffbc: ui_no_truncation 480/480 (20 screens); interchange_e2e
  covers the free/Pro gate on the Worth pulling block; pf_ux, yaris pass;
  part_finder fails only the known M3 data check (main identical).
- Photos: not added. Owner decision pending (chain photos were turned off in Sept).

### Round 3: photos (2026-11-06 evening)
- Branch head b4297b4 (merged main eb93379; branch shell jh-v151, since build 29 shipped jh-v150).
- Photos render only from the published `photoSources` (scraper/photo_sources.json
  patterns; no hosts in app.js; fail closed; URLs must be https on the source's
  own published host). Includes the PnP owner exception (ops/hub.md 18:40).
- Display: 4:3 box, object-fit: contain (never crop a watermark), slim
  "No photo from this yard" strip on the car screen, card photo only when one
  exists, viewer with credit, "View on <yard>" and a removal mailto.
- Tests: ui_no_truncation 552/552 (23 screens incl. photo card/screen/viewer);
  backend/test/photo_policy_unit.mjs (new) against photo_sources.json.
- Blocker for TestFlight 30: main's data has no photoSources until the next
  scan with the new scraper. Privacy policy should say images load from yards' servers.

### Round 4: Parts tab (2026-11-06 night; owner on TestFlight 30: "the parts tab seems lack luster")
- Branch head 4239892 (merged main; shell jh-v153). Screenshots only, no build requested yet.
- Start: your car (remembered) → part by name or 8 tiles → one-line search area → one button.
  Donors use the app's car card (photo, row plate, chip up front, "Why it fits",
  pull sheet, Details); Nearest/Newest sort; "Watch for another <model>" via addQuickWatch.
- Guards unchanged; pf_guards_unit now loads the real donor card. Tests: ui_no_truncation
  672/672 (28 screens), interchange/pf_ux/yaris pass, part_finder known M3 only.

### Round 5: alerts first (2026-11-06 night; owner: "alerts are the most valuable part of pro")
- Branch head 32466c5 (shell jh-v153; main jh-v152). Screenshots only, no build requested.
- Copy/order only, gates and limits unchanged: every upgrade surface (Pro sheet,
  native sheet, car-screen note, price-lock lines' sheet) leads with "Get pinged
  when the car you want lands"; restore sits after the purchase flow.
- Alerts tab, free only: "Landed X · your free recap comes Y / it was in your
  free recap Y · Pro would have pushed it the day it landed." Only for cars that
  landed after the watch was added; recap date only when a recap channel exists.
  "Left before recap" not built: app data holds only cars on the lot now.
- Car screen: lifespan line only on a model-here basis, plus "Alert me when the
  next one lands" (free: quiet "Pro: instant push"). Cars/Parts results end with
  "Want the next one?" (addQuickWatch; stored watches untouched, rule 6).
- Tests at 32466c5: ui_no_truncation 792/792 (33 screens), alerts_first_unit (new),
  watch_match_unit +5, no_pick_models_e2e 11/11, interchange/pf_ux/yaris pass,
  part_finder known M3 only. Artifact section "Round 5: alerts first".

### Final round: Pro box (2026-11-07; owner on build 32: "Make the pro a box or just look better ... then push this to prod!")
- Branch head 80f31bc (merged main; shell jh-v154 because the shell changed since build 32). Hub merges and ships; this session did not merge or release.
- One Pro box (`proBoxHtml` in app.js, `.pro-box` in styles.css): accent border, PRO badge, one line,
  chevron, the whole box opens the Pro sheet; Pro users see none. It replaces every free-user
  Pro link: car screen next-one (stacked under a full-width one-line button), watch hits,
  "Want the next one?" rows, card and part value locks, watch toast, Alerts tab, zip banner.
- Polish: tabular digits moved off body (Inter widened hyphens: "6 - cyl"); distances keep "mi" on the same line.
- Tests at 80f31bc: ui_no_truncation 792/792 (new rules: no bare "Pro" links, no box for Pro,
  next-one button one line from 375px); interchange, pf_ux, yaris, no_pick_models, all node units pass;
  part_finder known M3 only. Artifact section "Final round: the Pro box".

### Follow-up: model pickers follow the year (2026-11-08; owner: 2003 Chevrolet offered Chevelle, Chevette, Celebrity, Caprice)
- On main. App reads `modelYears` {make: {rawModel: [first, last]}} from inventory_live.json and
  inv/manifest.json (data session publishes it). With a year chosen, Parts "Your car", the Cars model
  filter and the Alerts watch builder offer only models whose span reaches within one year. No year =
  all; field missing = today's behaviour; no span = kept; a picked model is never dropped. Shell jh-v157.
- Tests: model_years_unit, model_years_e2e (both data paths), ui_no_truncation picker screens,
  interchange, pf_ux, no_pick_models, all node units pass. Reaches native apps in the next release.
- Premium lots (hub, same day): UTPAP "(Premium)" yards show a lifespan only from their own history
  (model entry, the scan's own yard figure, or their own typical in model_lifespan.json), never the
  chain/all-yards average. Orem Premium (chain 83) and Ogden Premium now show none. Shell jh-v158.
  Test: lifespan_premium_unit.

### Follow-up: heavy photo sources (2026-11-09)
- On main. `photoSources[key].heavy: true` (+ optional `approxKB`, yards session contract): never on
  cards; car screen shows the 4:3 box "Photo available — tap to load (~3.8 MB)" with the credit; the
  tap loads `large` into the box, then the viewer works as usual. In-memory for the session only, no
  auto-load. Today only sturtevant. Shell jh-v159. Tests: photo_policy_unit (+5),
  ui_no_truncation photo-heavy / photo-heavy-loaded screens.

### Round 9: lot map with bottom sheet — SHIPPED in 1.12.14 (2026-11-09)
- Owner: "Ship the latest". Hub merged `design/map-sheet` (cb8b36a8) into main as 4c1b482e,
  shell jh-v167; 1.12.14 dispatched to App Store review (build 36) and Play production (c1ae792).
- Yards tab List / Map switch. Full-height MapLibre map (OpenFreeMap positron/dark, keyless,
  attribution kept open) with a bottom sheet (peek / full / card / min); the page is locked in map
  mode. Credit line and map controls are never under the sheet (lifted, or moved into the sheet).
- Pins are our own layer: labelled yard pins, clustered by measured size so nothing overlaps at any
  zoom; pins that do not fit the open area are not drawn. "(Premium)" lots are one place with the main
  yard (pin, sheet, and List cards). Several yards at one spot open a list. Pull sheet button sits in
  the sheet header.
- Also in this release from main: Walk the rows (row-ordered yard view, "Seen" / "+ Pull sheet",
  checks expire after 24h or when the car leaves; 96641bf), drawings in place of missing photos,
  long-listed notice, tab re-tap closes the open layer then scrolls to top, labelled pins and row
  photo tags (70aa36d).
- Tests: map_regions_e2e (10 regions, 480/480 layouts), lot_rows_unit, long_listed_unit,
  tab_retap_e2e, illo_unit, ui_no_truncation (map, rows, premium, long-listed screens) all pass.
- Known: dense metros mostly show count bubbles at the fitted zoom; a shorter pin label is the
  lever if the owner wants more named pins. iOS status-bar tap to top not checked on a device.

### Round 9b: compact app banner + map first view (2026-11-09; merged by hub as 86d29797, jh-v168)
- Hub, from live jh-v167 (+ owner: "make the x so it's not its own line item"): banner was ~285px with the
  X on its own row and covered the map sheet; the map's first view near Ogden fit the whole 100 mi range,
  so the 6 Utah yards became one bubble at the sheet edge.
- Banner: one row (name, short line, "Get the app", X top-right), 62px at 320-768; hidden in the map view.
- Map: first view = yards within 25 mi (nearest 2-3) + your spot; fewer/closer until the nearest yard is a
  named pin; last resort zooms past your spot. Colliding single pins flip below their point before merging;
  side-docked sheet closes the left of the pin area; long credit moves into the sheet; key only with bells.
- Tests: app_promo_e2e (new, 174), map_regions_e2e 11 regions / 1,056 layouts, ui_no_truncation 1,296, units.
- Known (fixed in 9d): Atlanta first view, a "2 yards" bubble could cover the You dot.

### Round 9c: photos on the computer (2026-11-09; merged by hub)
- Owner: "on the computer, the images are large/wonky". Credit was under the photo (cards read "-Pull"):
  credit now above the photo, bottom-left (clear of ROW52-style watermarks). >=700px: card and car-screen
  photo boxes 3:2, no 16rem cap (no wide grey bars), cards even; never cropped, margins show a blur of the
  same loaded photo. Phones keep 4:3. jh-v170. Tests: photo_layout_e2e (new, fixture photos, 554),
  ui_no_truncation 1,296, units. WebKit not installed here: Safari/iPad-on-Mac unchecked.

### Round 9d: You dot + short phone screens (2026-11-09; merged by hub as design/you-dot-v2 56df682, jh-v173; then design/phoenix-cluster 5c28d32, jh-v174: an unsplittable bubble lists its yards nearest-first)
- Pins keep off the You dot (flip / slide; else dot on top). Short Safari screens (390x664, 375x553):
  pins slide around the zoom buttons instead of closing the top band, one-row sheet peek at <=760px tall,
  map min height 220px so the sheet never runs under the tab bar. jh-v169 (second of 9c/9d to merge
  needs jh-v171). Tests: map_regions_e2e 11 regions x 6 sizes (1,584 layouts), ui_no_truncation, units.

### Round 9e: Walk the rows on desktop (2026-11-09; merged by hub at b22c744, jh-v175)
- Sanity pass at 1024/1440/1920 with today's data: 672px column, no sideways scroll. Row thumbs get the
  photo fill (PYP 16:9 photos left beige bands), 112px at >=900px; thumbs and photo boxes isolate their
  stacking (fill layers had painted over the sticky row header). jh-v175. photo_layout_e2e 578 (adds rows
  checks; fails without the fix), ui_no_truncation 1,296, units. WebKit still unchecked.

### Round 9f: map first view made deterministic + Parts headings (2026-11-10; merged by hub at 4c748386, jh-v177; next free sw v178)
- Phoenix 375x553/200% flake: first view decided at zoom 13, then a map resize grew the open area ~5px, a
  Pull-N-Save point entered and merged with Pull-A-Part. Now the first view stays live until the map is
  moved (re-decided on any re-layout that bubbles the nearest yard below max zoom; capped), resizes go
  through mapResize(), the sheet goes to rest instantly on opening the map, and _firstViewSettled marks
  idle + fonts for tests. Phoenix 375x553 10/10 (was 6/10 failing mid-fix).
- Parts results headings: bold headline alone, line 2 starts plainly (no em dash) in browse, engine browse
  and fit search; plural labels drop "a". Checker fails a dash/lowercase line 2. jh-v177.
- Branch names: v2/v3 exist because a force-push to rewrite a rebased branch is refused in this session;
  cherry-picked onto current main instead.

### Round 9g: Parts polish and test hygiene (2026-11-10; all merged by hub)
- Aftermarket donor cards (cbfafb4, jh-v179): only the checks to make at the car stay inline (engine,
  amperage, body, drivetrain, splines/length, transmission); the listing's provenance ("listed for each of
  these vehicles", "not the carmaker's catalog", "Only the years shown", "No other unit", "Engines shown
  are", the rebuilder's fit notes) moves behind "Why it fits"; the unit stays visible on that line. App
  classifies sentences (pfAmSplitNote, fail-safe: unknown stays inline). GSP CV card at 390: ~12 -> 7 lines.
  Tests: am_notes_unit (all 1,448 notes, no word lost), ui_no_truncation pf-am-cv (max 8 lines at 390).
- interchange_e2e free-card checks: the demand badge ("Usually still there"/"Gets picked over fast") is
  turnover, not a price; free on purpose. Card surfaces check prices only; sell words stay Pro on the car
  screen; positive check that the badge carries no price (test-only).
- ui_no_truncation fixtures made data-independent (e91f429): long-listed backdates 3x the yard's typical
  + 30 days (Newark's typical reached 101, so 200 days no longer qualified); cards-mixed clears the photo of
  the unmarked cards (a car-screen-only photo correctly badges "Photo on car page"). App was right both times.
- Backlog: combined part-or-car search box (proposal to the hub first; design round, screenshots before merge).

## Earlier state (2026-11-06, exploration)

- Branch: `design/redesign-2026-11` (exploration only; nothing merged).
- Review artifact (private, owner's account): https://claude.ai/artifact/37NZkcuFtzMhH1jbcYhH2y
  — audit, current vs three directions per screen, desktop, dark/200% text,
  effort/risk, recommendation, open questions.
- Prototypes (static HTML, real data sample from the 2026-11-06 scan, zip 95112):
  - `design/pull-sheet/` — A, trip-first: row number as hero, parts checklist,
    one primary action in thumb reach. **Recommended.**
  - `design/lot-map/` — B, place-first: map home, yard view grouped by row.
  - `design/my-garage/` — C, vehicle-first: saved cars, "donors for your Civic".
  - Shared token layer `design/shared/base.css` (production palette unchanged;
    adds type scale, 4px spacing, radii, 48px touch target, focus ring).
  - Screens: `?s=home|results|car|part|watches|pro` (+`&theme=dark`, `&zoom=200`).
- Screenshots: `design/screenshots/{current,pull-sheet,lot-map,my-garage}/`
  (phone = iPhone 13 @2x, desktop = 1280). Scripts in `design/tools/`.

## Recommendation

Build A (Pull Sheet) in small CSS-first releases; later add B's per-yard
"walk by row" list as one screen inside it; park C (needs a new garage record
and alert changes; must not rewrite saved watches, rule 6).

## What implementing A touches (built on design/pull-sheet, see State)

1. `docs/styles.css` :root — add tokens only (no visual change).
2. `docs/styles.css` — one button system, Inter for sentences/mono for numbers,
   drop card rails + header hazard stripe, targets >= 44px.
3. `docs/app.js` car-card template — row plate, stay meter, single primary
   action, share into overflow. Bump `docs/sw.js` `jh-vNNN`.
4. Car detail as a pushed screen with sticky action bar; parts checklist,
   "if equipped" group unchanged in logic.
5. First run: zip chip in header, combined part-or-car search, remove notice stack.
6. Watches show live hits; shorter Pro sheet with one-tap "Already have Pro?".
Each step: Playwright before/after screenshots. Native shells load docs/, so a
store release is only needed for native-side changes (none planned). Releases
still need the owner's explicit "ship".

## Owner questions (answered 2026-11-06 via hub: names free, rename UI only, map deferred)

- Free tier shows blurred part names today. Show names free, lock only prices/demand?
- Rename "Saved" to "Pull sheet", grouped by yard?
- OK to defer the map (B)? Yard row layouts aren't in our data.

## Notes for other workstreams

- Audit saw results default-ordered with Newark (13 mi) before San Jose North
  (1 mi) and inconsistent radius copy (250 mi text vs 100 mi filter) — app.js
  owner should check when the card work starts.

- 2026-11-06: main moved to sw jh-v147 (typo fix) while this branch uses jh-v146. When merging design/pull-sheet into main, bump to jh-v148 or later so no two different shells share a cache name.

- 2026-11-12 (hub, from the r/XTerra post): a commenter said "I'd like to see
  donor cars near me without specifying a part". The Cars tab already lists
  every car near a zip, but narrowing to one model is Filters → Make → Model,
  below the fold on a phone (checked live at 390 px). The visitor read the site
  as part-search only. Proposal: a "Search a car (e.g. Xterra)" box at the top
  of the Cars tab, and a deep link (e.g. `#cars=Nissan|Xterra`) so posts can
  link straight to a model near the reader's zip. Needs an sw bump; app side
  needs the owner's "ship".

## State (2026-11-12) — car search on the Cars tab, branch `design/car-search`

Built from the r/XTerra note above; not merged (the hub reviews and merges;
going live on the web is a merge to main, the store shells need nothing).
- `docs/index.html`: "Search a car (e.g. Xterra, 4Runner)" box between the
  stats bar and the zip chip + Filters row (a textarea, like the Parts part
  box, so the placeholder wraps at 200% text). Visible above the fold at
  390x844 once a zip is set.
- `docs/app.js` CAR SEARCH: suggestions are the make + model pairs (plus
  "Make · all models") in the radius scope the Make list uses, spelling-
  insensitive (xterra, 4 runner, f150, cr v, chevy silverado). A pick sets
  the Make select + `selectedModels` through `populateModelFilter` and
  renders through `renderLive`, so it is identical to Filters -> Make ->
  Model (the e2e compares the two). Enter picks the single/only-exact
  match; arrows + Enter pick the highlighted one; x resets make + model
  (years stay, as Filters leaves them). The box follows Filters changes.
  Counts in suggestions are Pro-only, like the Make/Model lists.
- `#cars=Make|Model|YYYY-YYYY` (model, years optional; parsed like
  `#watch=`): opens Cars, applies once a zip and its inventory are in; with
  no zip the banner shows and the box is prefilled; a name not in range
  leaves every car listed with a note. Works with `?utm_source=` and while
  the app is open (hashchange). Example: https://yardscout.io/#cars=Nissan|Xterra|2005-2015
- `docs/styles.css`: car-search block; plus `.cc-head > .car-badges` may
  shrink so "Manual" + "Leaving soon" wrap at 320 px / 200% (found by the
  new truncation screens on a filtered Xterra list).
- sw `jh-v185`. Tests: `backend/test/car_search_unit.mjs`,
  `backend/test/car_search_e2e.mjs`, and three car-search screens in
  `ui_no_truncation.mjs`. Screens: scratchpad `xt/carsearch_{light,dark}.png`.
- Not changed: default sorts, free limits, watches and their matching, the
  Parts tab, backend, scraper.
- Open: Pro users who skipped the zip (nationwide, no location) have the
  Make filter disabled today, so a `#cars=` link waits for a zip for them
  too. No goatcounter event names beyond `car-search` / `car-link`.

## State (2026-11-13) — notable trims, branch `design/notable-trims`

From the owner: "For Subaru Outback, can we know which ones are Outback XT?
Same with Forester or other similar cars..." Not merged (hub reviews).
- Source of the words: the parts table's NON-option `trim` gates, published
  by the scan as `notableTrims` (scraper change, ops/data.md + ops/parts.md).
  Live with the first scan after the merge; until then the app shows no
  badge and no Trim control (checked by notable_trims_e2e).
- Badge (`.badge-trim`, Manual's sibling, keeps the table's spelling): Cars
  cards, Alerts hits, Parts donor cards, and a line on the car screen. Only
  when the decode is `usable` AND names the trim alone: multi-trim lists
  ("SE / Limited", "Sport, R/T") and "non R design" never badge. Matching is
  trimFilterMatches; a longer hit wins ("N Line" over "N"). Free for
  everyone (judgement call: the decoded trim line is Pro on cards, but the
  Trim filter was asked to be free and would reveal the same thing).
- Filters -> Trim: with exactly one model picked and a notable trim among
  the cars the other filters leave; "Any trim" + each trim present (counts
  Pro-only); note "N <Model>s have no single trim in their VIN data and are
  not shown"; counted in the Filters badge; resets when make/model change
  (state keyed to make+model); survives re-renders.
- Search box: "forester xt" -> "Subaru Forester · XT" row (sets the trim
  too); `#cars=Make|Model|years|Trim` (years may be empty). Both small and
  self-contained (CAR SEARCH header says so).
- Today's data (11-13): 1,686 cars badged across 56 make/model names; top
  pairs Mustang GT 244, Camry Hybrid 228, Monte Carlo SS 133, TL Type-S
  107, 4Runner Limited 95. Forester XT 32. Outback XT 0: no Outback XT gate
  (see ops/parts.md for the recommendation).
- sw `jh-v190`. Tests: notable_trims_unit (71), notable_trims_e2e (30),
  scraper/test_notable_trims.py, two ui_no_truncation screens
  (cards-trim-badges, cars-filters-trim). Browser tests add notableTrims to
  the served data via backend/test/notable_trims_fixture.mjs until the
  checked-out data carries it.
- Runs on this branch: ui_no_truncation (results, results-pro, car-card,
  cards-mixed, alerts-hits, cars-filters, cars-filters-gps-pro and the two
  new screens) at 320/360/375/390/402/430/1280, light+dark, 100%+200%:
  252 checks, 0 failures; part-finder-likely, pf-fit-pro, pf-am-cv,
  car-detail at 320/390: 32 checks, 0 failures. car_search_e2e 47,
  card_share_e2e 19, tab_retap_e2e 14, model_years_e2e 18, share_watch_e2e
  33, watch_match_unit, car_search_unit: all pass. All 27 scraper test
  files exit 0.
- Hub follow-up 2: free or Pro is the owner's call. One constant,
  `NOTABLE_TRIMS_FREE` in docs/app.js (true on this branch). false = Pro
  only: a free user gets no badge, no car-screen line, no trim search rows,
  no trim from a `#cars=` link (the box prefill drops it too), and Filters
  shows the standard Pro box "Filter this <Model> by trim" in the Trim
  control's place (no trim word). Both values covered in notable_trims_unit
  and notable_trims_e2e (the e2e serves app.js with the constant rewritten);
  `TRIMS_FREE=false` makes ui_no_truncation do the same. Existing behaviour
  left alone: the one free sample card still shows the decoded trim line
  ("2.5XT · AWD  PRO"), as before this branch.
- Hub follow-ups 1 and 3 (labels, multi-trim gate fix): see ops/parts.md.
  Badged cars on 11-13 now 1,842 across 61 names (labels +123; the
  "1/2 Ton" series is no longer read as a list, e.g. Yukon XL 1500 Denali
  18 -> 38). "-Line" packages never badge as the word (Explorer "ST-Line").
- Re-runs after all three: notable_trims_unit 107, notable_trims_e2e 40,
  car_search_e2e 47, card_share_e2e 19, all pass; ui_no_truncation same 9
  screens x 7 widths x 2 themes x 2 zooms: 252 checks, 0 failures; with
  TRIMS_FREE=false (cars-filters-trim, cars-filters, results, 7 widths):
  84 checks, 0 failures; 26 scraper test files importing junkyard_scraper
  + test_inventory_shards exit 0.

## 2026-11-16 Cars tab becomes a feed (owner: "intuitive, shareable, easy to scroll, Facebook Marketplace level addicting"; "Do it and ship")

Status: designed by the hub, not built. Starts when `growth/first-view` is
merged (same screen). Ships in the next app release, which the owner has
already approved ("ship", 2026-11-16).

Why: today a phone shows one car per screen (a 260 px picture, then seven
blocks of text and buttons) and a 1280 px desktop shows three. Photo cover
is good enough for a picture grid: 57% of all cars, 92% at LKQ Pick Your
Part, 99% at Pick-n-Pull (scan 2026-11-16); the rest get the existing drawing
in the car's paint colour.

What the Cars tab becomes:
1. **A grid of small tiles.** Two columns on a phone, more on wider screens.
   A tile is the picture, the year make model, the yard and distance, the
   set-out date and row, and the badges cards have today (NEW, trim). Target:
   at least four cars on the first phone screen.
2. **Tap a tile for everything.** The car screen (`openCarDetail`) holds all
   that the big card holds today: row, colour and engine, yard with hours and
   directions, set-out date and typical stay, the Pro value box, parts to
   check, add to pull sheet, share, watch this model. Nothing is removed from
   the product; it moves one tap down. Closing it returns to the same place
   in the list. Under it: "More <model> near you" tiles.
3. **Save and share on every tile** (owner asked for share on every card on
   2026-11-13): a bookmark for the pull sheet and the share button.
4. **Chips above the grid:** All, New (2 days), This week, then the makes
   with the most cars near you; picking a make shows its models as chips.
   They set the same filters as Filters and the search box.
5. **One summary line instead of three stat tiles:** cars near you, new this
   week, updated. "Updated" stays always visible (owner request 2026-10-24).
6. **Endless scroll:** tiles are added as you reach the bottom.
7. **A reason to come back:** "N set out near you since your last visit
   (date)" at the top on a return visit, and a divider in the list where the
   new ones end. Dates only: yards publish a set-out day, not a time.
8. **Share a list:** when the list is narrowed to a model, a share button
   sends the public model page (`/landed/<make>/<model>`) when one exists,
   else the tagged `#cars=` link.

Kept as they are: the accuracy note and its wording, the watch strip, the
free sample car, Pro gates and their names (`card-value` and the rest), the
search box, Filters, the pull sheet, per-tab scroll memory, no cut-off text.

## 2026-11-16 (built) Cars feed, branch `design/cars-feed` — NOT merged

From origin/main 004eeda0; pushed after every item (092a1520 … see git log).
Nothing merged, pushed to main, dispatched or sent. Web files only plus
`backend/src/attribution.js` (the one backend file allowed) and tests. sw
`jh-v201` (main jh-v200; the hub re-bumps at merge). Shared files touched
only in their own blocks: index.html (stats line, chip row), styles.css (one
"CARS FEED" block at the end, plus the per-feature rules beside it), sw.js,
ui_no_truncation.mjs (new screens, the data-hscroll exception).

What changed, per item:
1. **Tiles** (`carTileHtml`): picture (cardPhotoHtml unchanged), name, "yard ·
   12 mi · Row 31", badges + "Set out Nov 15". `class="car-card car-tile"`,
   `data-vkey`, `data-eid`, match/dim class kept. Two columns on phones
   (minmax 8.5rem; one column at 200% text on small phones), 13rem wider:
   5 columns at 1280. Phones: the tile photo box is 3:2 (16:10 at <=380px),
   contain as always, so nothing is cropped. Four tiles on the first screen
   at 360x800 and 390x844 (zip set, note acknowledged; asserted).
2. **Car screen** gained what only the card had: the card's value block
   (`card-value` Pro box + turnover badge, free; sample car unlocked as
   before), "N parts to check: …" line, the stale-yard scan line, an "Hours
   and directions" link (yardMapsUrl, as the pull sheet; plain Directions
   stays when the yard name is unknown), and "More <make model> near you":
   up to six tiles of the same make and model in range, newest first (none:
   no heading). A tile's picture opens the car screen; the car screen's
   picture opens the viewer. Closing returns to the same scroll offset (the
   list is not re-rendered).
3. **Bookmark + share** in the picture's top corners (44 px hit area, 34 px
   dot): share top-left (shareVehicle), bookmark top-right (toggleSaved, the
   `.heart-btn` hook; refreshPullBtns redraws it). The credit keeps
   bottom-left; bottom-right stays clear for chain watermarks.
4. **Summary line** `#live-stats-bar`: "17,906 cars near you · 1,837 new this
   week · updated 1h ago", wraps (never scrolls). No location: "337,647 cars
   on the lots · N new this week · updated …" (parts it lacks are left out,
   never 0).
5. **Chips** `#feed-chips`: All, New (set out today or yesterday,
   `liveNewOnly`), This week (`liveWeekOnly`), top 10 makes in range; a
   chosen make (pressed, × clears) shows all its models by count. Set
   through carSearchSetFilter, redrawn every render, so Filters, the search
   box and chips agree both ways. Counts Pro-only (as the Make list). Phones:
   one row that scrolls sideways (`data-hscroll`; ui_no_truncation allows
   that row only); 721px+: the row wraps. Make/model chip = `narrow/chip`.
   The near-you "This week" banner and its make chips went (the chip row is
   that now); the yard-week banner stays.
6. **Endless scroll**: 40 tiles, more as the bottom nears (IntersectionObserver,
   "Show more cars" button as fallback); cap 1,200 (was 400) with a plain
   line; a re-render of the same list keeps what was shown.
7. **Since your last visit**: `ys_last_visit_day` (local day, never sent);
   the day compared is fixed per session (`ys_since_day`). Counts cars whose
   set-out DAY is after the last visit's day (same day not counted; undated
   never). Line above the grid + "Show just those" (`liveSinceOnly`), and a
   divider in the newest-first list.
8. **Share a list** (one model): `/landed/<slug>/<slug>` when
   data/landed/index.json lists the model (what renderLandedModelPage reads),
   else `https://yardscout.io/?utm_source=share&utm_medium=list#cars=Make|Model`.
   Text: "57 Nissan Xterra are on self-service yard lots near me right now
   (YardScout)" (no zip in it).
9. **First visit**: "How to read this" (same element, words, Got it) moves
   after the first row of tiles on <=720px; a hidden marker keeps its home.
10. **App banner**: on the visitor's first day (`ys_first_day`) it waits for
   the third row of tiles to scroll past or 30 s after the list rendered;
   later days at once (as before). Header badges treat a waiting banner as
   showing. Dismiss and the toast step-aside unchanged.
11. **Watch strip** (web, free, location; recapEligible): the Monday-email
   ask with "Email me" and "or just watch it here". Watches made by
   addQuickWatch (source `strip`), then recapSubmit (/v1/recap/signup with
   src/cmp/med) or recapAddAll for a confirmed subscriber. Limit = upgrade
   sheet, nothing sent. The strip's watches are taken out of the toast's
   queue. Over RECAP_MAX models, Pro, apps, offer dismissed: today's strip.
   The strip keeps its Pro box (`strip-pro`, trigger `watch-toast`).

Counting: EVENTS_V 4 -> 5 (narrow/chip; email-asked also counts the strip's
field once per visit). attribution.js writes a `funnel-v5` marker. The
scorecard does not read either yet: noted in ops/growth.md (its file).
Privacy page: three sentences made true (Monday email can be asked in the
same step; chip tally from Nov 16).

Departures from the brief: "More <make model>" (not model alone: "More 300
near you" reads badly); badges sit in the tile text, not on the picture
(the corners are the buttons, credit and watermark); a "Free Pro look" badge
on the sample tile so free visitors can find it; the free car screen now
shows the card's turnover badge inside `.cd-value` (it was free on the card;
interchange_e2e checks that block for prices only, like the card); first
visit for the banner = first day, not first page load.

Tests (this branch, final run): cars_feed_e2e (new) 96/0; car_search_e2e
49/0; card_share_e2e 27/0 (rewritten for tile corners + bookmark);
coverage_gaps_e2e 26/0; funnel_events_e2e 128/0 (v5); notable_trims_e2e
40/0; tab_retap_e2e 14/0; pf_guards_unit 167/0; photo_policy_unit 48/0;
illo_unit 12/0; photo_layout_e2e 610/0; free_instant_e2e 30/0;
recap_ask_e2e 35/0; share_watch_e2e 33/0; app_promo_e2e 198/0 (waits for
the third row first); pro_sheet_fold_e2e 188/0; scorecard_unit 155/0;
funnel_counters_unit 140/0 (+chip); recap_signup_unit 97/0 (+v5 marker);
model_years_e2e 18/0; no_pick_models_e2e 11/0; pf_new_cats_e2e 162/0;
car_search_unit 75, notable_trims_unit 107, alerts_first_unit 13,
watch_match_unit 43, share_watch_unit 20 (all pass); python:
interchange_e2e 43/0 (follows the tiles), alert_freshness 15/0, pf_ux 38/0,
yaris 9/0, part_finder 74/0. ui_no_truncation, Cars screens (33 incl. 6 new)
at 320/360/390/1280, light+dark, 100%+200%: 464 checks, 0 check failures;
setup errors: cards-trim-badges (fixed, rerun 16/0) and cards-mixed,
photo-heavy, photo-heavy-loaded, which fail the same way on untouched
origin/main (the heavy source now publishes a resized copy, so there is no
tap-to-load box and the card shows the photo: test fixtures are stale).
Spot run of alerts, Parts, Yards, Pro sheet, toast at 360/390: only
`[yards] yr-where field-text-cut at 360/200%`, same on origin/main.
alerts_e2e needs a local worker (fails on main too). WebKit not checked.

Screenshots (scratchpad `feed/`): before-cars-390/1280 (origin/main),
after-cars-360/390 light+dark and 1280, car-screen-from-tile, car-screen-more,
chips-make-chosen, strip-email, since-last-visit (all 390).

Left / suggestions:
- Scorecard: read `narrow/chip` and `funnel-v5` (ops/growth.md note).
- ui_no_truncation fixtures for heavy photos (above) need the resized-copy
  case; not touched here.
- The car screen still says "No photo from this yard" where the tile shows
  the paint-coloured drawing: show the same drawing there.
- Desktop: a big make's model chips wrap to 3 rows; a "more models" fold or
  the phone's sideways row would keep the grid higher.
- Before merge, the hub re-bumps sw and merges `growth/no-gate` (zip card,
  chip, location guess): the Cars blocks there are untouched here, but the
  first-screen budget (four tiles at 360x800) depends on what sits above the
  grid; cars_feed_e2e asserts it.

## 2026-11-19 "Best yards for this part" (game-plan card, branch `feat/where-to-go-1119`)

Owner ask 2026-11-19 ("build something meaningful ... that differentiates
us"); hub chose a game plan on the Parts tab. This is the yard half; the
forecast half (`docs/forecast.js`, `YSForecast`) is another builder's.

- **Where:** fit search only (`pfRunSearch`, seeker year+make+model + part),
  a card `.pf-plan` right under `.pf-results-head` (+ its Pro box), before
  the watch line, sort and donor rows. Browse mode (no full car) has no card.
- **What it counts:** exactly the donor rows the list renders (the first
  CAP=120 rows; only Verified rows while "Verified fits only" is on; the
  toggle recounts via `pfPlanRefresh`). `pfPlanShownRows()` is the single
  source. Per yard: "N donor cars", "M to check first" (rows whose warns
  carry the list's own "if equipped" text), newest set-out
  (`pfPlanSetOutText`: today / yesterday / N days ago / date; nothing when
  unknown), the yard's published price for the part (`yardPartQuote` with
  the rows' own `quoteVariants`; nothing when not published), and the
  existing `lot-fast` "leaves fast here" when `lifespanFor` says so for a
  donor there.
- **Order (`pfPlanYards`, pure):** default Most donor cars, ties to the
  closer yard; chips Closest, Newest arrival (no dates last), Lowest price
  (no published price last); full ties by yard name. The line under the
  title states the rule and changes with the chip (`pfPlanRuleText`). Yards
  whose list has stopped changing (`yardListStale`: stale OR frozen) go
  after all others in every order and carry the app's "List unchanged since"
  badge (`yardListChipHtml`); their donors stay in the list.
- **Headline + ranks (hub review, same day):** under the title, "N donor
  cars at Y yards within R mi." from the same shown rows (singulars); when
  the list is at its 120-row cap it adds the list's own line "Showing the
  first 120 of T donors — tighten the radius to narrow." Each yard row
  starts with a plain rank numeral in the current order (held yards keep
  their numbers at the end).
- **UI:** top 3 yards, "Show all N yards" toggles. One yard: no chips. No
  donors: the card still shows "No donor cars within R mi right now." (the
  list's own `.pf-empty` stays above it). Tapping a yard hides other yards'
  rows (`.pf-yard-out`, no re-render), shows `.pf-yard-only` "Showing
  <yard> only · All yards" plus the car screen's maps link (`yardMapsUrl`,
  else `carDirectionsUrl`), and scrolls there. View state `pfPlanView`
  (order, yard, expanded) survives re-renders of the same search (sort,
  lazy files) and resets when part/car/engine/radius change.
- **Counters** (sendEvent, aggregate, no ids): `pf-yards/shown` once per
  search key, `pf-yards/tap`, `pf-yards/chip-<order>`, `pf-yards/all`. Not
  `pf/` (that prefix feeds the daily email's "most searched parts"). The
  ops email does not read them yet.
- **Forecast hook:** `<div class="pf-forecast">` inside the card;
  `ysForecastMount(el, ctx)` calls `YSForecast.mount` when defined, ctx
  `{make, model, year, yrMin, yrMax (pfGenWindow), lat, lng, radiusMi,
  where:'parts'}`. Cars tab: `watchStripHtml` adds `<div
  class="strip-forecast">` when the filter is exactly one model;
  `stripForecastMount()` runs after each list render (`where:'cars'`, year
  span from the year filters). Empty mount points are `display:none`.
- **CSS:** beside the `.pf-watch` rules in `docs/styles.css` (not at the end).
- **Tests:** `backend/test/pf_plan_unit.mjs` (pure functions),
  `backend/test/pf_plan_e2e.mjs` (count proof per yard incl. every chip,
  reset, verified-only, re-sort and one yard; ordering measured from the
  list's rows; tap/reset; empty; forecast absent and stubbed; counters),
  `ui_no_truncation` screens `pf-plan-many|long|one|none`.
  `pf_guards_unit.mjs` stubs `pfPlanStart`/`pfPlanAfterRender`.
- **Screens:** `ops/screens/where-to-go-1119-{1,2,3}.png` (2009 Camry side
  mirrors near 95112: several yards; Rancho Cordova tapped; 1985 4Runner, no
  donors).
- **Open / next:** the verified-only count proof ran on a search with 0
  Verified rows (side mirrors); a search with Verified rows would make it
  stronger. Show the counters in the ops email (backend, hub's call).

## 2026-11-19 Forecast under Alerts watch rows (branch `feat/watch-forecast-1119`, sw `jh-v218`)

- A watch row in the Alerts tab gets the compact arrival forecast
  (`<div class="watch-forecast">`, `ysForecastMount`-style call to
  `YSForecast.mount(el, {make, model, year:null, yrMin, yrMax, lat, lng,
  radiusMi, where:'alerts', compact:true})`) only when `watchForecastCtx(e)`
  says the history answers for exactly what is watched: one make AND one
  model, a saved centre (lat/lng numbers) and a finite radius > 0, and no
  trim, drive or "Parts only" (matchOnly) filter. Anything else: no mount
  point at all. A make whose arrivals file is missing or fails: empty, 0 px.
- Read only (rule 6): `renderAlerts` reads `loadWatchlist()` as before;
  nothing new writes it. `watch_forecast_e2e.mjs` proves the stored list's
  bytes are unchanged.
- `docs/forecast.js` compact mode: same subject, headline, facts and label
  words; eight 24 px bars with the same text alternative, no per-bar
  numbers; no "Most land at" line. Styles at the end of `docs/styles.css`.
- Counter `watch-forecast/shown`, once per visit, when one renders.
- Screenshot `ops/screens/watch-forecast-1119-1.png` (real data, 4Runner
  2003-2009 within 100 mi of 95112).

## 2026-11-19 Donor models in the Parts card's forecast (branch `feat/donor-forecast-1119`, sw `jh-v219`)

- **Donor set** (`pfRunSearch`, the app's main script, comments "DONOR
  MODELS"): beside the rows, the search collects the vehicle specs its own
  matching accepts, from the definitions (never from today's lot):
  - engine kinds: the chosen family's `apps` clipped to the part's years
    (Likely; engine assemblies: Verified-tier for unambiguous apps), plus
    the vg / oemVg number-list entries that name the seeker, intersected
    with the family apps (Verified-tier);
  - body kinds: the platform groups and OEM catalog groups (main and lazy
    file) that name the seeker, every app (Verified-tier only for a
    verified group and an ungated app, as the rows);
  - aftermarket units that list the seeker (`pfAmRows(..., specs)`), Likely;
  - the seeker's own generation (`pfGenWindow`), Likely.
  `pfSpecPush` skips empty ranges. `pfPlanForecastCtx` passes the specs
  (only Verified-tier with "Verified fits only" on); the toggle redraws.
- **forecast.js**: `q.specs` -> `summarySpecs`: makes split on "|",
  overlapping/touching ranges merged per make+model, every history row
  counted once (first matching spec), per-yard coverage rules unchanged; a
  "*" model matches by its letters-and-digits stem (the app's own rule for
  those rows), others as `modelRows` (same name, any case). At most 4 make
  files; more, a missing/failed file or another build -> today's own-model
  block. A make the index does not list counts 0. Specs equal to the own
  generation -> today's output byte for byte. Compact (watch rows) ignores
  specs.
- **Strings**: subject "Donor models"; existing headline/facts rules; the
  models line ("2003-09 4Runner, ..." most arrivals first, then "and N more"
  opening the rest, also in its title); caveat "Counts every car of these
  models and years. The list shows, car by car, which have the right engine
  and options."; the existing "not a promise" label.
- **Counter** `pf-forecast/donor-models` once per search when drawn. Ops
  email: "Parts card (7 d): shown, yard taps, order changes, show all,
  donor-model forecasts" and "Alert forecasts shown (7 d): N", printed at 0.
- **Fixes**: car-card mismatch tooltip now ends "...the lot sign may be
  mislabeled. Verify at the yard before you pull."
- **Gaps**: the arrivals history names models as yards list them, so a spec
  "ES 300" misses cars listed as plain "ES"; a seeker with no generation
  window whose rows come only from donors' own part-row fits gets no spec
  (the forecast stays the own model, any year). Counting every car of an
  engine family's models overstates where the model had other engines
  (2002 ES 300 alternator: every 1997-2003 Camry, 4-cyl included); the
  caveat says so, but a decoded-engine split in the arrivals data would fix it.
- **Calibration (hub review, same day; supersedes the strings above):**
  subject "Cars of the donor models"; directly under the headline, from
  today's lot (`pfPlanLotNow`, the app's own `pfAppMatches` over the specs
  in use, after Verified-only): "On lots within R mi now: D of C cars of
  these models are donors for this part." (D = the list's rows before the
  120 cap among those cars, so D <= C; singular "is a donor" / "1 car";
  no line when C is 0 or the numbers are missing). Caveat shortened to "The
  8-week counts include every car of these models and years, whatever its
  engine or options." Real data near 95112: 2004 4Runner alternator "About 6
  a week" with 42 of 61; 2002 ES 300 alternator "About 72 a week" with 363
  of 570. The ES 300 list itself offers "engine not confirmed" donors, so
  its ratio still includes cars the decode cannot rule out.
