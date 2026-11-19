# Release workstream — status (updated 2026-11-16)

Owns: version bumps and store submissions via `release-ios.yml` and
`release-android.yml`, `fastlane/metadata/`, release notes.
Procedure: `RELEASING.md`. **Dispatch only after the owner says "ship".**

## Shipped

| Version | iOS | Android |
|---|---|---|
| 1.13.3 | DISPATCHED 2026-11-19 19:29 UTC (owner, 2026-11-19 18:24 UTC: "lets just push 1.13.3 accross the board dont wait for apple to approve the first iteration"). Built from main a48aac2b (sw jh-v220). iOS build 44, **submit=true**, run 44598878122: build uploaded and version bump pushed (322344e9, "submitted"); the submit step replaces what is in Apple's queue (1.13.1 build 42, waiting since 11-18 15:03). 1.13.2 build 43 stays in TestFlight, never submitted. | versionCode 43, track production, run 44598850958, succeeded 19:32. play-status 44600698366: production 1.13.3 (43), status completed, rollout 100% (Google review pending). |
| 1.13.2 | BUILT 2026-11-19 07:27 UTC (owner, 2026-11-19 ~06:40 UTC: "Ship"). Built from main 3591e082 (sw jh-v215, round 5 parts gates). iOS build 43, **submit=false** (TestFlight only), run 44479745314, succeeded 07:31. NOT submitted: 1.13.1 build 42 is still WAITING_FOR_REVIEW (asc-status 44480392647, 07:33) and the workflow's submit step withdraws whatever is in the queue. When 1.13.1 is READY_FOR_SALE: `release-ios.yml` with `submit_only=true`, `build_number=43`, `marketing_version=1.13.2` and the notes below. | versionCode 42, track production, run 44479741801, succeeded 07:32. play-status 44480389133: production 1.13.2 (42), status completed, rollout 100% (Google review pending). |
| 1.13.0 | SHIPPED 2026-11-16 13:29 UTC (owner: "Do it and ship!"). Built from main 67fa5d2b (sw jh-v202). iOS build 41, submit=true, run 43876188232. asc-status 43877889988: 1.13.0 build 41 WAITING_FOR_REVIEW, submitted 13:39 UTC, automatic release on approval; listing text and six new screenshots went up with it. | versionCode 40, run 43876161947, uploaded 13:32 UTC. play-status 43876886357: production 1.13.0 (40), status completed, rollout 100% (Google review pending). Play listing text and screenshots NOT sent yet: send after 1.13.0 is live. |
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

## 1.13.1 — dispatched 2026-11-18 14:52 UTC (owner, 2026-11-17: "Ship")

Built from main after `release/1.13.1` (sw `jh-v208`) went to main as a
fast-forward. Regression run 11 on the release tree: 81 suites, the full
layout check (6 widths) and the six API suites all pass.
In it: petrol accent and the name in one colour (app icon, splash, Play
icon recoloured; `release/brand-petrol`), "Know what to pull before you
drive" in the site descriptions and the Play banner (rebuilt from
`docs/brand/feature-graphic.html`, 300+ yards), new store screenshots
(`tools/capture_store_shots.py`), and every website change since 1.13.0:
the alert card, one price Pro box, photo-first within a day, the Cars-tab
return fix, the free emailed alert (web only; hidden in the apps).
What's New (both stores): `scratchpad/release/whatsnew_1131.txt`.
After both stores accept: dispatch `store-listing.yml` and
`play-subscription-listing.yml` (new screenshots and banner on Play; iOS
screenshots go up with the submission).

## Apple notice 2026-11-18: ITMS-90725, iOS 27 SDK required from April 2027

On the 1.13.1 build 42 delivery (a warning; delivery succeeded and the
build is in review): "This app was built with the iOS 26.5 SDK. Starting
April 2027, iOS and iPadOS apps must be built with the iOS 27 SDK or later,
included in Xcode 27 or later."
- Why: `release-ios.yml` runs on `macos-latest` and uses whatever Xcode is
  that image's default (26.5 today); it never selects a version.
- To do, well before April 2027: add a step that selects Xcode 27 on the
  runner (list `/Applications/Xcode_*.app`, `sudo xcode-select -s` the
  newest 27.x, fail loudly if none), build ONCE to TestFlight only
  (`submit=false`), and have the owner open it on a phone before any store
  submission uses it: a new SDK can change how the web view and system
  controls look. Hub check-in suggested for mid-January 2027.

## 1.13.2 — dispatched 2026-11-19 07:27 UTC (owner, 2026-11-19: "Ship")

Why: the store apps carry their own copy of the web shell, and 1.13.1 was cut
at `jh-v208`, before the parts gates. Those apps show every catalog donor as
a plain row whatever the part's limit (about 12,000 contradicted pairs and
14,000 "if equipped" pairs on the pinned lot).
Built from main 3591e082 = the round 5 tree 982adbf3 plus ops and scan data
(no shell or native change in between). Checks on that tree: builder's full
regression 102 passed, 2 failed (both layout halves, browser crashed with the
disk full); hub's quick regression 71/0/0; hub's full layout suite on
982adbf3 after freeing disk: both halves pass, 1,332 checks each, 0 failures.
Live check of the website at 07:15 UTC: `jh-v215`.
In it since 1.13.1: catalog donors honour each part's limits (drive, body,
cab, engine, fuel, transmission, build window); a donor whose listing and VIN
disagree is never a plain row; "list has not changed for a while" on a
yard's page; the Parts tab re-runs its search when a late zip arrives; links
and price sheets for Intermountain Auto iPull, S&S U-Pull-It and Standard
UPIC. The free emailed alert stays web only.

What's New (both stores):

    More accurate parts matches.
    • Donor cars are now checked against each part's limits: 2WD or 4WD, body style, cab, engine, transmission and build date. Cars that can't fit are hidden, and uncertain ones tell you what to check.
    • A car whose listing and VIN disagree is marked "check the car".
    • A yard whose list hasn't updated in a while now says so.
    • Links and price lists for newly added yards.

Still to do: submit iOS build 43 once 1.13.1 is live (see the table row);
then `store-listing.yml` and `play-subscription-listing.yml` as planned for
1.13.1.

## Google Play listing in the petrol look: pushed 2026-11-19 14:28 UTC

`store-listing.yml` run 44543912651 (icon, feature graphic, six phone
screenshots, text) and `play-subscription-listing.yml` run 44543917581 (the
four benefit lines), both success. Covered by the 11-17 "Ship" for 1.13.1.
Not waiting for Apple any more: the Play page has nothing to do with the App
Store review. iOS screenshots still go up with the iOS submission.

## 1.13.3 — dispatched 2026-11-19 19:29 UTC (owner, 2026-11-19: "lets just push 1.13.3 accross the board dont wait for apple to approve the first iteration")

Built from main a48aac2b (sw `jh-v220`). Checks on that tree: hub's full
regression on `hub/rc5-1119` 113 passed, 0 failed, 0 skipped (both layout
halves); after the icon-link merge, quick regression 76/0 and the share /
landing tests 3/0. Live check of the website at 19:29 UTC: `jh-v220`, an
Infiniti window-regulator search shows catalog rows with "window motor
only", no page errors.
In it since 1.13.2: the Cars list order (two newest days, nearest yard
first); the Parts "Best yards for this part" card; the arrival forecast on
Parts, Cars and each watch, with donor models and the "N of M cars of these
models are donors" line on the Parts card; the reader for the newer catalog
field, so Nissan and Infiniti catalog rows show (older app versions show
none); the car-card mismatch tooltip wording.

What's New (both stores):

    Know where to go, and when.
    • Search a part and see the best yards for it: donor cars at each yard, distance, newest arrival and the yard's own price.
    • Arrival forecast: how often your model, or the models a part comes from, has landed near you over the last 8 weeks. On Parts, Cars and each alert.
    • Newest arrivals now lead with the yards closest to you.
    • Nissan and Infiniti added to factory-catalog parts matching: window regulators and motors, mirrors, climate controls.

Still to do: confirm Apple's state after the submit step (asc-status); when
Apple approves, check the App Store shows 1.13.3.
