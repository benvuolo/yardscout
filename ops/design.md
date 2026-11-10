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
- Deferred: combined part-or-car search box (step 5 second half), B's
  walk-by-row yard view, map.
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
- Known: Atlanta first view, a "2 yards" bubble can cover the You dot. Waiting on hub review/merge.

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

### Round 9f: map first view made deterministic + Parts headings (2026-11-10, branch design/firstview-settle-v3 fd0b8c0, in hub regression)
- Phoenix 375x553/200% flake: first view decided at zoom 13, then a map resize grew the open area ~5px, a
  Pull-N-Save point entered and merged with Pull-A-Part. Now the first view stays live until the map is
  moved (re-decided on any re-layout that bubbles the nearest yard below max zoom; capped), resizes go
  through mapResize(), the sheet goes to rest instantly on opening the map, and _firstViewSettled marks
  idle + fonts for tests. Phoenix 375x553 10/10 (was 6/10 failing mid-fix).
- Parts results headings: bold headline alone, line 2 starts plainly (no em dash) in browse, engine browse
  and fit search; plural labels drop "a". Checker fails a dash/lowercase line 2. jh-v177.
- Branch names: v2/v3 exist because a force-push to rewrite a rebased branch is refused in this session;
  cherry-picked onto current main instead.

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
