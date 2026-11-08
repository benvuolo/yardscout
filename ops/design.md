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
