# Release workstream — status (updated 2026-11-06)

Owns: version bumps and store submissions via `release-ios.yml` and
`release-android.yml`, `fastlane/metadata/`, release notes.
Procedure: `RELEASING.md`. **Dispatch only after the owner says "ship".**

## Shipped

| Version | iOS | Android |
|---|---|---|
| 1.12.10 | build 26, live (READY_FOR_SALE) | — |
| 1.12.11 | — | versionCode 33, Play production, in review |
| 1.12.13 | TestFlight only, from branch design/pull-sheet via release-ios source_ref: build 28 (redesign), 29 (Worth pulling), 30 (photos, branch e3d09b4 + bump; VALID 2026-11-06 ~21:00 UTC). 31 (new Parts tab + onCards), 32 (alerts first + noPick models, branch 32466c5 + bump; VALID 2026-11-07 ~01:15 UTC). Owner testing 32. Not submitted. To ship: merge the branch into main (sw jh-v153 or later; main is jh-v152), then submit_only build 32. | not built |
| 1.12.12 | build 27, submitted 2026-11-05 19:42 UTC, WAITING_FOR_REVIEW, auto-release on approval | versionCode 34, Play production, status completed, rollout 100% (Google review pending) |

1.12.11 added the review prompt (`ReviewPlugin.swift` / `ReviewPlugin.java`,
`maybeAskForReview` in app.js) and the keyword/title retune.

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
