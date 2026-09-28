# YardScout — iOS App Store handoff

For the agent picking this up on a new machine. Goal: build the already-scaffolded
Capacitor iOS app in Xcode, get it on TestFlight, then through App Store review.
Everything web/scraper/backend-side is DONE and deployed — do not rebuild it.

## What this project is

YardScout: freemium junkyard-inventory app for people who pull their own parts.

- **Web app (live)**: `docs/` — vanilla JS PWA, deployed by GitHub Pages at
  https://benvuolo.github.io/yardscout/. 188k+ vehicles across 9 self-serve
  chains, refreshed daily by GitHub Actions (`.github/workflows/scan.yml`).
- **Backend (live)**: `backend/` — Cloudflare Worker + D1. Powers watches/alerts
  and (dormant, feature-flagged) Stripe billing. NOT needed for iOS work.
- **Scraper**: `scraper/junkyard_scraper.py`. Runs in CI. NOT needed for iOS work.
- **iOS wrapper (this handoff)**: `ios/` + `native/` + `capacitor.config.json`.
  Scaffolded, adapted, and browser-validated; never yet built in Xcode
  (the previous machine had no Xcode).

## Product/monetization state

- One plan: **Pro, $9.99/mo**. Free tier: browse everything with locks on VIN
  factory specs, per-car part values, cross-yard price compare, instant alerts.
- Pro is currently unlocked client-side by `localStorage jh_pro === '1'`
  (useful for QA: set it in the JS console to preview Pro UI).
- Stripe billing exists in the Worker but is dormant behind a flag; the public
  app shows a fake-door waitlist in the upgrade sheet.
- **Apple rule that shapes everything**: digital subscriptions in a native app
  MUST use StoreKit IAP (guideline 3.1.1). The native build therefore hard-locks
  Stripe out (`IS_NATIVE` guard) and shows the waitlist until IAP ships. Never
  re-enable Stripe checkout inside the native app; never link out to a web
  purchase page from it.

## iOS wrapper architecture (read `native/README.md` too)

- Capacitor 8, Swift Package Manager (no CocoaPods). App ID `com.yardscout.app`,
  name "YardScout".
- The app bundles only the ~540KB shell. The ~36MB `data/` directory is
  deliberately NOT bundled: `IS_NATIVE` (top of `docs/app.js`) makes the app
  fetch all data from `DATA_BASE = https://benvuolo.github.io/yardscout/`,
  so inventory stays fresh daily with zero app updates. GitHub Pages sends
  `Access-Control-Allow-Origin: *`, so CORS is fine from `capacitor://localhost`.
- `IS_NATIVE` also: skips service-worker registration (unsupported scheme),
  suppresses the Safari "add to home screen" hint, and blocks Stripe (above).
- Icons/splash generated from `assets/` via `npx @capacitor/assets generate --ios`.
  NOTE: current icon is the 512px PWA icon upscaled to 1024 — replacing
  `assets/icon-only.png` with true 1024px art and regenerating is a nice-to-have
  before submission.

## Build workflow (every time `docs/` changes)

```bash
npm install                    # once per machine
./native/stage.sh              # docs/ -> native/www (excludes data/, sw.js)
npx cap sync ios
npx cap open ios               # or: open ios/App/App.xcodeproj
```

Gotcha that already bit once: `cap sync` copies from `native/www`, which is a
frozen snapshot. If you edit `docs/app.js` and forget `./native/stage.sh`, the
app builds with stale code.

## Machine setup

1. Xcode from the Mac App Store (Command Line Tools are NOT enough), then
   `sudo xcode-select -s /Applications/Xcode.app`, open Xcode once to accept
   license + install the iOS platform.
2. Node 20+ and `npm install` at repo root.
3. No CocoaPods, no Ruby setup needed (SPM).

## Verifying without / before the Simulator

The native environment can be simulated in any browser: serve
`ios/App/App/public/` over HTTP and inject
`window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios' }`
before page scripts run (Playwright `add_init_script` works). Checks that
matter:

- inventory loads from GitHub Pages (header shows "N SET OUT THIS WEEK")
- set a ZIP (e.g. `setZipCenter('84101')` in console) → Live cards + Yards render
- `openUpgradeSheet('test')` shows the WAITLIST form, not checkout — even with
  `localStorage jh_use_api = '1'`
- zero console errors

All four passed on the last validated commit.

## App Store path (in order)

1. Xcode > App target > Signing & Capabilities > select the personal Apple
   Developer team (account already purchased 2026-09-28).
2. Run on Simulator — smoke-test the checks above plus tab navigation and the
   prices sheet on a yard card.
3. App Store Connect > My Apps > New App: name "YardScout", bundle
   `com.yardscout.app`. If the name is taken, decide a suffix ("YardScout —
   Junkyard Finder" style) — owner's call.
4. Privacy questionnaire: no accounts, no tracking, no third-party analytics
   (GoatCounter is OFF — `GOATCOUNTER_CODE` is null). Location: ZIP is typed or
   geolocated but never leaves the device except as lat/lng to the yards list
   fetch — answer "Location: not linked to identity, app functionality only" if
   geolocation permission is added; today the app only asks the browser API.
   Privacy policy URL: https://benvuolo.github.io/yardscout/privacy.html
5. Screenshots (6.7" required, 5.5" often still requested) from Simulator Cmd+S.
6. Product > Archive > Distribute > App Store Connect > TestFlight first.
7. Review notes: "Data is public junkyard row inventory, refreshed daily from
   the chains' own published lists. Free tier is fully functional; paid tier is
   not yet purchasable in-app (waitlist only)."

## Known risks & queued work

- **Guideline 4.2 "minimum functionality"**: the main rejection risk for wrapped
  web apps. Strongest mitigation: add native push before first review (below).
  If rejected on 4.2, that's the answer, not a rewrite.
- **Native push (queued)**: web push doesn't exist inside the wrapper. Watches +
  weekly email digest still work. Instant Pro alerts on iOS need:
  `@capacitor/push-notifications` plugin, APNs key from the dev account, and an
  APNs sender in the Cloudflare Worker (`backend/src/alerts.js` currently
  speaks web push only). Design decision needed: store APNs device tokens in D1
  alongside the existing push subscriptions.
- **StoreKit IAP (queued, before marketing Pro on iOS)**: create the $9.99/mo
  auto-renewable subscription in App Store Connect; RevenueCat is the fast
  integration path. Server-side: Pro entitlement should become account/receipt
  based (today it's a localStorage flag; the Worker's D1 already has a users
  table from the dormant billing work — see `README-BACKEND.md`).
- **Custom domain**: yardscout.io purchase was planned (Cloudflare Registrar).
  If the site moves off benvuolo.github.io, update `DATA_BASE` in
  `docs/app.js` AND restage/resync/re-release the app. Consider doing the
  domain BEFORE submitting so the bundled URL never has to change.

## Repo conventions

- GitHub: https://github.com/benvuolo/yardscout, branch `main`, plain git
  (no gh CLI needed on a personal machine).
- `git pull --rebase origin main` before pushing — CI commits data refreshes
  to main daily, so the remote moves.
- Pushing to main deploys the web app (GitHub Pages serves `docs/`) — shared
  code in `docs/app.js` runs on BOTH web and native; keep web behavior intact
  (everything native-only goes behind `IS_NATIVE`).
