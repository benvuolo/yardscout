# Release workstream — status (updated 2026-11-16)

Owns: version bumps and store submissions via `release-ios.yml` and
`release-android.yml`, `fastlane/metadata/`, release notes.
Procedure: `RELEASING.md`. **Dispatch only after the owner says "ship".**

## Shipped

| Version | iOS | Android |
|---|---|---|
| 1.13.0 | DISPATCHED 2026-11-16 13:29 UTC (owner: "Do it and ship!"). Built from main 67fa5d2b (sw jh-v202). iOS build 41, submit=true, run 43876188232; listing text and six new screenshots go up with it. | DISPATCHED 2026-11-16 13:28 UTC, run 43876161947, track production (versionCode 40 expected). |
| 1.12.16 | SHIPPED 2026-11-14 17:03 UTC (owner: "ship"). Built from main ac24bcb5 (sw jh-v196). iOS build 40, submit=true, run 43618949981. asc-status: 1.12.16 build 40 WAITING_FOR_REVIEW, submitted 17:13 UTC, automatic release on approval. Carries: Cars-tab search box, per-tab scroll, filter panel fix, card share button, trim badge and filter, model-range line, hours and directions links, narrowing and checkout-outcome counters. | versionCode 39, Play production, status completed, rollout 100% (run 43618947678); Google review pending |
| 1.12.15 | build 37, live (READY_FOR_SALE) | versionCode 38, Play production, completed |
| 1.12.10 | build 26, live (READY_FOR_SALE) | — |
| 1.12.11 | — | versionCode 33, Play production, in review |
| 1.12.14 | SHIPPED 2026-11-09 14:24 UTC (owner: "Ship the latest"). Round 9 map merged to main (4c1b482e, sw jh-v167). iOS build 36, submit=true, run 42634279207: the workflow withdrew 1.12.13 build 34 from review (WAITING_FOR_REVIEW since 11-07 04:40, built at jh-v155 without the price-copy fix). asc-status confirms 1.12.14 build 36 WAITING_FOR_REVIEW, submitted 14:46 UTC, automatic release on approval. Build 35 is TestFlight only. | versionCode 37, Play production, committed 14:27 UTC (run 42634274314); Google review pending |
| 1.12.13 | SHIPPED 2026-11-07 (owner: "push this to prod"). design/pull-sheet merged to main (4331322, sw jh-v154), then the coverage-count fix (sw jh-v155). Build 33 was submitted and then replaced by build 34 (with the fix), WAITING_FOR_REVIEW since 04:40 UTC. 1.12.12 was withdrawn and never reached iOS users; 1.12.13 includes it. | versionCode 35, then 36 (with the fix): Play production, completed, rollout 100% |
| 1.12.12 | build 27, submitted 2026-11-05 19:42 UTC, WAITING_FOR_REVIEW, auto-release on approval | versionCode 34, Play production, status completed, rollout 100% (Google review pending) |

1.12.11 added the review prompt (`ReviewPlugin.swift` / `ReviewPlugin.java`,
`maybeAskForReview` in app.js) and the keyword/title retune.

## In 1.13.0 (owner said "Do it and ship!" 2026-11-16)

- Cars feed: photo tiles, chips, endless scroll, since-last-visit, share a
  list, the car screen from a tile.
- No zip gate on the first visit (a guessed place, never saved, never a
  watch centre); yard and place links.
- Free instant alert: one watch per install, within 50 miles (apps only).
- Resized photos from five more yards in the list.
- Fixes since 1.12.16: yard request form, "search <year> instead" on the
  Parts empty state, long-listed label on tiles.
- Pre-flight on the merged tree: see `ops/hub.md` 2026-11-16 13:16 UTC.
- After both stores show it live: flip the two held website sentences
  (`docs/index.html`), dispatch `store-listing.yml` and
  `play-subscription-listing.yml` for the Play listing.

## In 1.12.12 (owner said "ship" 2026-11-05)

- Native "Already have Pro?" unlock (Owen's iOS report): redeem block shown outside the purchase form.
- Phase 0 part-finder guards (hybrid splits, VIN-confirmed chip fails closed).
- Manual badge source labels.

- "Sold on eBay" labels and the sold-prices link.
- "leaves fast here" lifespan tag and urgency sort.
- Search-signal events (pf/, pf-car/).
- sw cache `jh-v144`.
- Pre-flight: all scraper tests pass, site-proxy redirects ALL PASS, app.js/sw.js syntax OK.

## Next: 1.12.13 when OEM-verified matches can be displayed (§7.4 client).

## Checklist when the owner says ship

1. `git pull`; confirm `docs/` tests pass (`backend/test/e2e.sh` subset the
   change touches; `node backend/site-proxy/test/redirects_unit.mjs`).
2. Bump sw cache name if the shell changed.
3. Write notes (what users see, two lines).
4. Dispatch Android to internal, then production; dispatch iOS with
   `submit=true`. Use `gh api -X POST .../dispatches`.
5. Watch the runs; `asc-status.yml` / `play-status.yml` to confirm.
6. iOS archive note: the workflow mints a fresh provisioning profile via the
   ASC API; a 403 there means an Apple account change is in progress.
