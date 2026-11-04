# YardScout — rules for any Claude session

YardScout (yardscout.io) tracks cars on US self-service junkyard lots and
tells owners which parts to pull. Owner: Ben (GitHub benvuolo,
yardscout.io@gmail.com, they/them). Accuracy and dependability come first.

## Standing rules (the owner set these; do not relax them)

1. **Never dispatch a store release without the owner's explicit "ship".**
   Previews, builds to internal tracks, and status checks are fine. Submitting
   to App Store review or Play production is not, until the owner says so.
2. **No bot-check, WAF, captcha, TLS-fingerprint, user-agent or proxy
   workarounds.** The existing Harry's Sucuri solver stays as it is; nothing
   new of that kind is written. A yard that refuses the scraper gets an
   outreach email, not a bypass. No eBay page scraping (robots.txt disallows
   /sch/); eBay data comes only through its APIs.
3. **Never invent fitment.** A parts row is added only with a stated basis
   (see `scraper/PARTS_GAPS_2026-11.md`). Option parts (spoilers, leather,
   wheels, HID, sunroofs, premium audio) are flagged `option`: they ship
   "if equipped" and add $0 to ranking. Coupe/hatch parts use the `body`
   gate, AWD parts the `drive` gate.
4. **No engines, transmissions or catalytic converters** in the parts table.
5. **Never print secrets.** Workflows read them from GitHub secrets. Do not
   echo tokens, keys or `.p8` contents into logs, chat or files.
6. **Saved watches are never rewritten.** Match logic may improve; stored
   user watches are not migrated or edited.
7. Row52 is out of scope.
8. Report outcomes faithfully. Failed tests are reported with output. Skipped
   steps are named.

## Layout

| Path | What |
|---|---|
| `docs/` | the web app (GitHub Pages) and `docs/data/*.json` the scraper publishes; `docs/app.js` is the app; `docs/sw.js` cache name `jh-vNNN` must be bumped when the shell changes |
| `scraper/junkyard_scraper.py` | scraper, VIN decode (vPIC), parts matching, gap curation, lifespan writer; `scraper/db.py` inventory history; `scraper/ebay_prices.py`; `scraper/coverage_sweep.py` |
| `scraper/test_*.py` | offline tests, run each as `python3 scraper/test_x.py` |
| `backend/src/` | Cloudflare Worker API (entitlements, alerts, push, ops email `ops_monitor.js`); `backend/test/` e2e scripts (`e2e-*.sh`) |
| `backend/site-proxy/` | yardscout.io edge worker (redirects, OG) |
| `ios/`, `android/`, `native/` | Capacitor shells; plugins registered in `MainViewController.swift` / `MainActivity.java` |
| `fastlane/metadata/` | store listings (keywords, title, benefits) |
| `.github/workflows/` | everything operational: `scan.yml` (4-hourly), `release-ios.yml`, `release-android.yml`, `store-listing.yml`, `store-subscribers.yml`, `ebay-prices.yml`, `coverage-sweep.yml`, `asc-status.yml`, `play-status.yml` |
| `tools/` | one-off operator scripts; `tools/store_subscribers.py` counts paid subs |
| `ops/` | **workstream status files — read the one for your task first, update it when you stop** |

## Working conventions

- `gh workflow run` fails here (GraphQL blocked). Dispatch with
  `gh api -X POST repos/benvuolo/yardscout/actions/workflows/<file>/dispatches --input body.json`.
- Commit and push small, often. Sessions are ephemeral; the repo and `ops/`
  are the memory. Commit messages: `area: what changed`.
- Release docs: `RELEASING.md`. Current versions: `android/app/build.gradle`
  `versionName`, `ios/App/App.xcodeproj/project.pbxproj` `MARKETING_VERSION`.
- Parts curation basis and history: `scraper/PARTS_GAPS_2026-11.md`.
- Yard registry and outreach history: `scraper/INDEPENDENT_YARDS.md`,
  `scraper/independent_yards_registry.json`, `ops/yards.md`.
- Keep one session per workstream (`ops/README.md`). Do not take on another
  workstream's files in passing; note the need in that workstream's file.
