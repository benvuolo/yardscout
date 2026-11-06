# Design — workstream status

Owner brief (2026-11-06): the app "looks obviously vibecoded"; wants a unique,
user-friendly layout, keeping the logo and colour scheme. Screenshots first,
nothing to prod until the owner decides.

## State (2026-11-06)

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

## What implementing A would touch (not started — needs owner go-ahead)

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

## Open questions for the owner

- Free tier shows blurred part names today. Show names free, lock only prices/demand?
- Rename "Saved" to "Pull sheet", grouped by yard?
- OK to defer the map (B)? Yard row layouts aren't in our data.

## Notes for other workstreams

- Audit saw results default-ordered with Newark (13 mi) before San Jose North
  (1 mi) and inconsistent radius copy (250 mi text vs 100 mi filter) — app.js
  owner should check when the card work starts.
