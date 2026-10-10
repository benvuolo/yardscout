# YardScout — project handoff (current as of Oct 6, 2026)

For any agent (Cursor, Claude Code, Codex, or human) picking this up. This file is
the single source of truth for project state; the git history and
`appstore-assets/LISTING.md` + `appstore-assets/APPLE_REPLY.md` carry the details.

## Status right now

- **App Store submission PENDING**: version 1.0 + YardScout Pro subscription +
  subscription group submitted together, **build 12** attached, status "Waiting
  for Review" since Oct 1 (one Guideline 2.1 info-request round was answered
  Sep 30 with a screen recording + written answers — see APPLE_REPLY.md; the
  same text lives in the ASC Review Notes field).
- **Everything else is DONE and live**: web app, scraper pipeline, Cloudflare
  Worker backend, APNs push (verified on real hardware), StoreKit IAP plugin,
  Paid Applications agreement + banking + tax all Active in ASC.
- If Apple rejects: read the rejection in ASC App Review, fix, bump a build,
  resubmit. If approved: app goes live automatically (auto-release enabled).

## What this project is

Freemium junkyard-inventory app ("find a donor car at a pick-a-part yard, get a
push when one arrives"). One plan: **Pro, $8.99/mo** via Apple IAP only.
Free = browse everything + weekly recap push; Pro = part values, pull costs,
price compare, value sorting, instant per-arrival push.

- **Web app (live)**: `docs/` — vanilla JS PWA on GitHub Pages:
  https://yardscout.io/. Pushing to `main` deploys it.
- **Scraper (live)**: `scraper/junkyard_scraper.py`, runs in GitHub Actions
  every 6h (`.github/workflows/scan.yml`), commits data + pushes shards to the
  Worker (`scraper/push_inventory.py`; custom User-Agent required — Cloudflare
  blocks `Python-urllib` with error 1010).
- **Backend (live)**: `backend/` — Cloudflare Worker + D1 at
  `https://yardscout-api.yardscout.workers.dev` (account benvuolo123@gmail.com).
  Devices/watches/push. `APNS_ENV = "production"` is correct for BOTH TestFlight
  and App Store (sandbox is only for direct-Xcode installs). Secrets on the
  Worker: `UPLOAD_TOKEN`, `ADMIN_SECRET`, `APNS_P8` (local record in gitignored
  `backend/.dev.vars.production`; APNs key backup
  `backend/.dev.vars.AuthKey_53ZHWL335J.p8`, Key ID 53ZHWL335J, Team G23Z9MSBUG).
- **iOS app**: `ios/` + `native/` + `capacitor.config.json`. Capacitor 8, SPM,
  bundle `com.benvuolo.yardscout`. Ships only the ~540KB shell; all data is
  fetched from GitHub Pages so inventory stays fresh without app updates.

## Hard-won gotchas (do not relearn these)

1. **Stage before sync**: `cap sync` copies the frozen snapshot `native/www`.
   After ANY `docs/` edit: `./native/stage.sh && npx cap sync ios`.
2. **PurchasesPlugin registration**: the custom StoreKit plugin
   (`ios/App/App/PurchasesPlugin.swift`) is registered in
   `MainViewController.capacitorDidLoad`. `SceneDelegate` MUST instantiate
   `MainViewController()` (not stock `CAPBridgeViewController()`) — this broke
   once and the Subscribe button silently vanished on device while browser
   mocks passed. Push is unaffected either way (it's in `packageClassList`).
3. **iOS input auto-zoom**: viewport has `maximum-scale=1.0` to stop WKWebView
   zooming the whole app when a <16px input (zip field) gets focus. Keep it.
4. **contentInset**: `"contentInset": "never"` in capacitor.config.json — the
   CSS `env(safe-area-inset-top)` handles the notch; "automatic" doubles it.
5. **Apple 3.1.1**: never re-enable Stripe in the native app, never link out to
   a web purchase from it. Native upgrade sheet is purchase-only (no waitlist —
   that's web-only fake-door).
6. **wrangler secrets** set before a Worker's first deploy silently don't
   persist. Verify with `npx wrangler secret list`.
7. **Honest copy**: scans run every 6h → say "within hours", never "the moment".
   ~90% of cars have values → "nearly every car", never "every car".

## Build + upload workflow (no Xcode GUI needed)

```bash
# after editing docs/:
node --check docs/app.js && ./native/stage.sh && npx cap sync ios
# archive + upload to TestFlight/ASC (build number auto-increments):
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -project ios/App/App.xcodeproj -scheme App -sdk iphoneos \
  -destination 'generic/platform=iOS' archive -archivePath /tmp/ys_archiveN.xcarchive \
  -allowProvisioningUpdates
xcodebuild -exportArchive -archivePath /tmp/ys_archiveN.xcarchive \
  -exportOptionsPlist /tmp/ys_export.plist -allowProvisioningUpdates
```

`/tmp/ys_export.plist`: method `app-store-connect`, destination `upload`,
teamID `G23Z9MSBUG`, `manageAppVersionAndBuildNumber` true. If /tmp was wiped,
recreate it with those keys. Signing uses the Apple ID already logged into
Xcode on this Mac. Builds 1–12 shipped this way; TestFlight internal group
"Main Tester" needs no beta review (external "Friends" group waits on beta
review which rides the main app review).

## Browser validation of the native shell (before any upload)

Serve `ios/App/App/public` over HTTP; in Playwright `add_init_script`:
`window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios',
Plugins: { Purchases: {...mock}, PushNotifications: {...mock} } }` plus
localStorage staging (`jh_zip`, `jh_honesty_ack`, watches). Check: inventory
loads, cards render, upgrade sheet shows "Subscribe — $8.99/mo" + Restore for
non-Pro, "You're Pro ✓" for Pro. IMPORTANT: a boot integrity check revokes
`jh_pro` unless `jh_pro_source` is 'iap' or 'account' — to stage Pro you MUST
set BOTH `jh_pro=1` AND `jh_pro_source='iap'` (and mock `isEntitled: true`
in the Purchases plugin or `refreshNativeIapUi` will revoke it anyway), zero console
errors. REMEMBER: browser mocks can't catch native plugin registration issues
(gotcha #2) — device-test anything touching plugins.

## Credentials / access map

- **GitHub** benvuolo/yardscout: plain git; token available via
  `git credential fill` (never use gh CLI here — EMU work account).
- **Cloudflare**: `npx wrangler login` OAuth as benvuolo123@gmail.com; config in
  `backend/wrangler.toml`; deploy with `cd backend && npm run deploy`.
- **App Store Connect / developer.apple.com**: owner logs in manually
  (BENJAMIN ALEXANDER VUOLO, team G23Z9MSBUG). Agent prepares, owner clicks.
- **APNs key**: original `~/Downloads/AuthKey_53ZHWL335J.p8` + gitignored backup
  in `backend/`.
- **Support email**: yardscout.io@gmail.com (also ASC contact + privacy/terms
  /support page contact).

## Post-launch queue (in rough priority order)

1. Sandbox-test the $8.99 purchase on device (agreement is Active, works now).
2. Name-privacy sequence (git history already scrubbed to YardScout authorship
   Oct 9 — local `backup-pre-scrub` branch keeps the old history, never push it):
   buy yardscout.io → set as GitHub Pages custom domain (old github.io URLs then
   301-redirect, shipped builds keep working) → update ASC privacy/terms/support
   URLs → transfer repo to a GitHub org (e.g. yardscout-app) → THEN optionally
   split source into a private repo (Cloudflare Pages deploy) leaving the public
   repo as a data-only mirror; requires a 1.2 build with new DATA_BASE first.
3. Buy yardscout.io (Cloudflare Registrar), CNAME GitHub Pages, update
   `DATA_BASE` in docs/app.js + ASC URLs, restage/resync/re-release.
3. Strip Pro values from the public repo data (README-BACKEND cutover) once
   there are paying subscribers.
4. Replace the upscaled 1024px icon with true art.
5. Maybe: ChatGPT-app/GPT wrapper on the free inventory API as top-of-funnel
   (free tier data only, rate-limited, no purchase links).

## Device/debug notes

- Owner's iPhone device row in prod D1: id `802bcb85-5d4e-46fb-9596-0216da88cf7a`
  (tier can be flipped to `pro` via D1 for instant-alert testing).
- There is NO dev toggle or `?pro=1` hatch anymore (removed Oct 9 — they were
  revenue holes in shipped builds). To test Pro on a real device, flip the
  device's tier to `pro` in prod D1, or sandbox-purchase.
- Query prod D1: `cd backend && npx wrangler d1 execute yardscout-db --remote
  --command "SELECT ..."`.
