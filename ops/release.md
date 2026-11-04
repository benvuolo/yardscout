# Release workstream — status (updated 2026-11-04)

Owns: version bumps and store submissions via `release-ios.yml` and
`release-android.yml`, `fastlane/metadata/`, release notes.
Procedure: `RELEASING.md`. **Dispatch only after the owner says "ship".**

## Shipped

| Version | iOS | Android |
|---|---|---|
| 1.12.10 | build 26, submitted 2026-11-03, waiting for review | — |
| 1.12.11 | — | versionCode 33, Play production, in review |

1.12.11 added the review prompt (`ReviewPlugin.swift` / `ReviewPlugin.java`,
`maybeAskForReview` in app.js) and the keyword/title retune.

## Pending for 1.12.12 (web changes already on main; need a native build
to reach store users who have the old shell cached)

- "Sold on eBay" labels and the sold-prices link.
- "leaves fast here" lifespan tag and urgency sort.
- Search-signal events (pf/, pf-car/).
- sw cache `jh-v139`.

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
