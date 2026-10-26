# YardScout — project handoff (current as of Oct 26, 2026)

For any agent (Cursor, Claude Code, Codex, or human) picking this up. This file is
the operator map; the git history (`git log --grep='chore(release)'`), the
Actions tab, `RELEASING.md`, `DISASTER_RECOVERY.md`, `appstore-assets/LISTING.md`
and `play-assets/LAUNCH_DAY_REPORT_20261021.md` carry the details.

NOTE: git history was squashed on 2026-10-25 (the first commit is an
auto-scan that adds the whole tree), so anything before that date is only in
the docs, not in `git log`.

## Status right now

- **Both stores ship from GitHub Actions** (since 2026-10-26, `RELEASING.md`):
  - Android **1.10 (versionCode 15)** → Play internal, then **1.10 (16)** →
    Play production (`chore(release): Android versionCode 16 / 1.10 (production)`).
  - iOS **1.10 build 3** → TestFlight (bounced at ASC: ITMS-90683, fixed in
    `241672c`), then **1.10 build 4** uploaded and **submitted for review**
    (`chore(release): iOS 1.10 build 4 (submitted)`, auto-release on approval).
  - Live state is NOT in this file: check `git log --oneline --grep='chore(release)'`
    and the Actions tab for the latest run, App Store Connect / Play Console
    for review status.
- **Everything else is live**: web app, scraper (national + independents incl.
  the Ario live adapter), both Cloudflare Workers, APNs + FCM push, StoreKit 2 +
  Play Billing + Stripe for Pro, cross-device email-code unlock.
- Privacy: `docs/privacy.html` rewritten 2026-10-26 (`0ba3568`): location is
  rounded to ~1 km and only sent when push alerts are on; APNs + FCM; Play /
  Stripe billing; deletion. ASC App Privacy and Play Data safety were updated
  the same day to declare approximate location + device ID (owner action —
  not verifiable from the repo).
- If Apple rejects: read the rejection in ASC App Review, fix on `main`, re-run
  **Release iOS** with the same marketing version and `submit=true`.

## What this project is

Freemium junkyard-inventory app ("find a donor car at a pick-a-part yard, get a
push when one arrives"). One plan: **Pro, $8.99/mo** — StoreKit 2 on iOS,
Google Play Billing on Android, Stripe Checkout on the web (product id
`yardscout_pro_monthly` on both stores). No accounts: an email is the
entitlement (`PRO_ENTITLEMENTS_SETUP.md`). Free = browse everything + weekly
recap push; Pro = part values, pull costs, price compare, value sorting,
"anywhere" watches, per-arrival push "within hours".

- **Web app (live)**: `docs/` — vanilla JS PWA on GitHub Pages at
  https://yardscout.io/ (custom domain; `DATA_BASE` in `docs/app.js`).
  Pushing to `main` deploys it.
- **Scraper (live)**: `scraper/junkyard_scraper.py`, runs in GitHub Actions
  **every 4h** (`.github/workflows/scan.yml`, cron `0 */4 * * *`; runs are
  serialized by a concurrency group), `--national --independents` — the
  independents include the Ario live adapter (Supabase backend; the whole
  story is `scraper/EXPANSION_CANDIDATES.md` §8.6). A manual
  **Ario adapter probe** workflow (`ario-probe.yml`) runs the adapter alone
  and commits nothing. The scan commits `docs/data/` and pushes shards to the
  API Worker (`scraper/push_inventory.py`; custom User-Agent
  `yardscout-push/1.0` required — Cloudflare blocks `Python-urllib` with
  error 1010).
- **Backend (live)**: two Cloudflare Workers, both deployed with
  `npx wrangler deploy` from their directory (account benvuolo123@gmail.com):
  - `backend/` → **yardscout-api** at
    `https://yardscout-api.yardscout.workers.dev` (D1 `yardscout-db`).
    Devices/watches/push: `POST /v1/device/register` takes `deviceId`,
    `platform`, `tier`, `apnsToken` (iOS) or `fcmToken` (Android) and the
    watches with lat/lng rounded to 2 decimals (`syncDeviceRegistration` in
    `docs/app.js`). `src/apns.js` + `src/fcm.js` send. `APNS_ENV =
    "production"` is correct for BOTH TestFlight and App Store (sandbox is only
    for direct-Xcode installs; the comment in `backend/wrangler.toml` saying
    TestFlight is sandbox is wrong). Secrets: `UPLOAD_TOKEN`, `ADMIN_SECRET`,
    `APNS_P8`, `FCM_SA_KEY`, … (full list in `backend/wrangler.toml` comments
    and `DISASTER_RECOVERY.md`). APNs key backup
    `backend/.dev.vars.AuthKey_53ZHWL335J.p8` (gitignored), Key ID
    53ZHWL335J, Team G23Z9MSBUG.
  - `backend/site-proxy/` → **yardscout-site** on `yardscout.io/*`: site proxy
    + Pro entitlements at `/api/ent/*` (Stripe, verify-ios, verify-android,
    6-digit codes; KV `ENTITLEMENTS`).
- **iOS app**: `ios/` + `native/` + `capacitor.config.json`. Capacitor 8, SPM,
  bundle `com.benvuolo.yardscout`, team G23Z9MSBUG. `MARKETING_VERSION` /
  `CURRENT_PROJECT_VERSION` in `project.pbxproj` are rewritten by the iOS
  workflow on every run (build number = workflow run number unless given).
- **Android app**: `android/`. applicationId `io.yardscout.app` (namespace
  `com.benvuolo.yardscout` — different on purpose), `versionCode`/`versionName`
  in `android/app/build.gradle`, rewritten by the Android workflow. Play
  Billing 8.0.0 via `android/app/src/main/java/com/benvuolo/yardscout/PurchasesPlugin.java`,
  FCM push (`google-services.json` is committed), `allowBackup=false`.
- Both native shells ship only the ~540KB web shell; all data is fetched from
  yardscout.io so inventory stays fresh without app updates.

## Hard-won gotchas (do not relearn these)

1. **Stage before sync**: `cap sync` copies the frozen snapshot `native/www`.
   After ANY `docs/` edit: `./native/stage.sh && npx cap sync ios` (or
   `android`). The release workflows do this themselves from `main`.
2. **Plugin registration**: the custom Purchases plugins are registered by hand.
   iOS: `ios/App/App/PurchasesPlugin.swift` is registered in
   `MainViewController.capacitorDidLoad`; `SceneDelegate` MUST instantiate
   `MainViewController()` (not stock `CAPBridgeViewController()`) — this broke
   once and the Subscribe button silently vanished on device while browser
   mocks passed. Android: `MainActivity.onCreate` calls
   `registerPlugin(PurchasesPlugin.class)` BEFORE `super.onCreate`. Push is
   unaffected either way (it's in `packageClassList`).
3. **iOS input auto-zoom**: the viewport does NOT use `maximum-scale` any more
   (Android Chrome honours it and it kills pinch-zoom, WCAG 1.4.4). Focus zoom
   is prevented by 16px inputs on touch screens instead
   (`@media (pointer: coarse)` in `docs/styles.css`). Don't put
   `maximum-scale` back.
4. **contentInset**: `"contentInset": "never"` in capacitor.config.json — the
   CSS `env(safe-area-inset-top)` handles the notch; "automatic" doubles it.
5. **Apple 3.1.1**: never re-enable Stripe in the native app, never link out to
   a web purchase from it. Native upgrade sheet is purchase-only (the waitlist
   is web-only fake-door). The optional "Use Pro on other devices" email link
   mentions no prices and links nowhere — keep it that way (same on Play).
6. **wrangler secrets** set before a Worker's first deploy silently don't
   persist. Verify with `npx wrangler secret list`.
7. **Honest copy**: scans run every 4h → say "within hours", never "the moment".
   ~90% of cars have values → "nearly every car", never "every car".
8. **ITMS-90683**: `Info.plist` must carry BOTH `NSLocationAlways…` purpose
   strings in addition to When-In-Use, even though only When-In-Use is ever
   requested — the Geolocation plugin binary references the Always APIs and
   ASC rejects the upload otherwise (1.10 build 3 bounced; `241672c`).
9. **Play Billing ≥ 8.0.0**: Play Console hard-rejects releases on 7.x; 8.x
   changed `queryProductDetailsAsync` to return `QueryProductDetailsResult`
   (handled in `PurchasesPlugin.queryProduct`). Version codes are permanent —
   a blocked upload still consumes one.
10. **CI signing is manual**: the iOS workflow signs with the Apple
    Distribution `.p12` + an App Store provisioning profile from secrets
    (automatic signing wants an Apple Development cert the CI keychain lacks).
    The profile expires yearly — regenerate and update the secret when the
    run says so.

## Build + upload workflow (GitHub Actions — no Mac needed)

```bash
gh workflow run release-android.yml -f version_name=1.10 -f track=internal -f notes="..."
gh workflow run release-ios.yml -f marketing_version=1.10 -f notes="..." -f submit=false
```

(or Actions → *Release Android* / *Release iOS* → *Run workflow*). Each
workflow checks out `main`, stages + syncs, bumps the version, builds,
uploads, and **commits the version bump back to `main`** (`chore(release): …`).
Android: `track=internal|production`, `versionCode` blank = current + 1.
iOS: TestFlight only by default; `submit=true` waits for Apple to process the
build (up to ~60 min), then `fastlane deliver` creates the App Store version,
sets What's New, attaches the build and submits with auto-release. If it
times out, the build is already uploaded — re-run with the same
version/build and `submit=true`, or submit from ASC. Full secrets list and
first-run order: `RELEASING.md`.

Local fallback (the pre-Actions path, still works on the owner's Mac with
Xcode signed in): `node --check docs/app.js && ./native/stage.sh && npx cap
sync ios`, then `xcodebuild … archive` + `xcodebuild -exportArchive` with an
`app-store-connect`/`upload` export plist (teamID `G23Z9MSBUG`). Android
locally: `cd android && ./gradlew bundleRelease` reads
`~/yardscout-android/keystore.properties`. Bump versions by hand if you go
this way — the stores reject reused build numbers / version codes.

## Browser validation of the native shell (before any upload)

Serve `ios/App/App/public` over HTTP; in Playwright `add_init_script`:
`window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'ios',
Plugins: { Purchases: {...mock}, PushNotifications: {...mock} } }` plus
localStorage staging (`jh_zip`, `jh_honesty_ack`, watches). Check: inventory
loads, cards render, upgrade sheet shows "Subscribe — $8.99/mo" + Restore for
non-Pro, "You're Pro ✓" for Pro. IMPORTANT: a boot integrity check revokes
`jh_pro` unless `jh_pro_source` is 'iap' or 'account' — to stage Pro you MUST
set BOTH `jh_pro=1` AND `jh_pro_source='iap'` (and mock `isEntitled: true`
in the Purchases plugin or the launch check in `nativeIapInit` will revoke it
anyway), zero console errors. `getPlatform: () => 'android'` exercises the
Play copy. REMEMBER: browser mocks can't catch native plugin registration
issues (gotcha #2) — device-test anything touching plugins.

## Credentials / access map

- **GitHub** benvuolo/yardscout: plain git; token available via
  `git credential fill`. (An earlier note said never use the gh CLI here —
  EMU work account; `RELEASING.md` shows `gh workflow run`. Unverified which
  applies on the owner's Mac; the Actions "Run workflow" button always works.)
- **GitHub Actions secrets** (repo → Settings → Secrets, set 2026-10-26; where
  each comes from is in `RELEASING.md`):
  - Android: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`,
    `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `PLAY_SERVICE_ACCOUNT_JSON`.
  - iOS: `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_API_KEY_P8`,
    `IOS_DIST_CERT_P12_BASE64`, `IOS_DIST_CERT_P12_PASSWORD`,
    `IOS_APPSTORE_PROFILE_BASE64`.
  - Scraper/alerts: `NTFY_TOPIC`, `SMTP_USER`, `SMTP_PASS`, `ALERT_EMAIL`,
    `YS_UPLOAD_TOKEN` (+ `YS_API_URL` variable).
  Releases no longer need the owner's Mac; the Mac still holds the only
  copies of the upload keystore (`~/yardscout-android/`) and the APNs .p8
  outside the secrets — see `DISASTER_RECOVERY.md`.
- **Cloudflare**: `npx wrangler login` OAuth as benvuolo123@gmail.com; config in
  `backend/wrangler.toml` and `backend/site-proxy/wrangler.toml`; deploy with
  `npx wrangler deploy` from either directory.
- **App Store Connect / developer.apple.com**: owner logs in manually
  (BENJAMIN ALEXANDER VUOLO, team G23Z9MSBUG). Agent prepares, owner clicks —
  except the release itself, which the workflow does via the ASC API key.
- **Google Play Console**: YardScout LLC, app `io.yardscout.app`; the Play
  service account (also `GOOGLE_SA_EMAIL` on yardscout-site) uploads releases.
- **APNs key**: original `~/Downloads/AuthKey_53ZHWL335J.p8` + gitignored backup
  in `backend/`.
- **Support email**: yardscout.io@gmail.com (also ASC contact, `OWNER_EMAIL`
  on the Worker, and privacy/terms/support page contact).

## Post-launch queue (in rough priority order)

1. Watch the 1.10 build 4 review; fix + re-run on rejection.
2. Strip Pro values from the public repo data (README-BACKEND cutover) once
   there are paying subscribers.
3. Icon: `assets/icon-only.png` is 1024×1024; whether it is still the upscaled
   512px art is unverified — replace with true art if so.
4. Maybe: ChatGPT-app/GPT wrapper on the free inventory API as top-of-funnel
   (free tier data only, rate-limited, no purchase links).

(Done since the earlier queue: yardscout.io bought and live as the Pages
custom domain + `DATA_BASE`; Android app shipped; push on both platforms;
Stripe web billing + cross-device unlock. Whether the $8.99 sandbox purchase
was device-tested is unverified from the repo.)

## Device/debug notes

- Owner's iPhone device row in prod D1: id `802bcb85-5d4e-46fb-9596-0216da88cf7a`
  (tier can be flipped to `pro` via D1 for instant-alert testing; unverified
  that the row survived the 1.10 reinstalls).
- There is NO dev toggle or `?pro=1` hatch anymore (they were revenue holes in
  shipped builds; the boot check in `docs/app.js` revokes anything not from
  'iap'/'account'). To test Pro on a real device, flip the device's tier to
  `pro` in prod D1, or sandbox-purchase.
- Query prod D1: `cd backend && npx wrangler d1 execute yardscout-db --remote
  --command "SELECT ..."`.
