# YardScout — native iOS + Android wrappers (Capacitor)

The store builds wrap the PWA in `docs/` with Capacitor 8. The shell
(HTML/JS/CSS, ~540KB) is bundled in the app; the ~36MB `data/` directory is
NOT — the native apps fetch live data from the web deployment
(`DATA_BASE = 'https://yardscout.io/'` in `docs/app.js`), so inventory stays
fresh without app updates.

Native-only behavior (all keyed off `IS_NATIVE` / `IS_ANDROID` in `docs/app.js`):
- data fetches go to `https://yardscout.io/`
- service worker registration skipped (doesn't work on `capacitor://`)
- "add to home screen" / store promo banners suppressed
- Stripe billing mode can never activate — Pro is bought through StoreKit 2
  on iOS (`ios/App/App/PurchasesPlugin.swift`) and Google Play Billing on
  Android (`android/app/src/main/java/com/benvuolo/yardscout/PurchasesPlugin.java`),
  both exposing the same `Purchases` JS surface (Apple guideline 3.1.1 / Play
  equivalent); the web waitlist never shows natively
- push is native: `@capacitor/push-notifications` yields an APNs token on iOS
  and an FCM token on Android; the device registers with the `yardscout-api`
  Worker (`syncDeviceRegistration`) only after the user taps "Enable push
  alerts" (Android 13+ `POST_NOTIFICATIONS` is requested then, never at open)
- one-shot "yards near me" via `@capacitor/geolocation` (When-In-Use only)

## Build workflow

Releases run from GitHub Actions — `.github/workflows/release-ios.yml` and
`release-android.yml` do everything below from `main`, bump the version, upload
to TestFlight / Play and commit the bump back. See `RELEASING.md`. The local
path still works:

```bash
./native/stage.sh            # copy docs/ -> native/www (minus data/, sw.js)
npx cap sync ios             # copy native/www into the Xcode project
npx cap sync android         # ... and/or the Gradle project
npx cap open ios             # open in Xcode; or: open ios/App/App.xcodeproj
npx cap open android         # Android Studio
```

Always re-run stage.sh + sync after editing anything in `docs/` — the
bundled shell does NOT update itself. `native/www/` is gitignored (generated).

Versions: iOS `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` live in
`ios/App/App.xcodeproj/project.pbxproj` (build number must be unique per
marketing version; the workflow uses its run number). Android `versionCode` /
`versionName` live in `android/app/build.gradle` (`versionCode` must always
increase — a blocked upload still consumes one). Keep both marketing
versions in step by hand.

Icons/splash are generated from `assets/` (`logo.png`, `icon-only.png`,
`splash.png`) with `npx @capacitor/assets generate --ios` / `--android`.
`assets/icon-only.png` is 1024×1024 today; whether it is still the upscaled
512px PWA icon is unverified.

## Custom plugins (register by hand — gotcha #2 in AGENT_HANDOFF_IOS.md)

- iOS: `MainViewController.capacitorDidLoad` registers `PurchasesPlugin`;
  `SceneDelegate` must instantiate `MainViewController()`, not the stock
  `CAPBridgeViewController()`. `AppDelegate` forwards the APNs device token
  to the PushNotifications plugin.
- Android: `MainActivity.onCreate` calls `registerPlugin(PurchasesPlugin.class)`
  BEFORE `super.onCreate`.
- Play Billing must be ≥ 8.0.0 (`android/app/build.gradle`) — Play Console
  rejects releases on 7.x.

## One-time machine setup (local builds only)

- Xcode from the Mac App Store (Command Line Tools alone can't build iOS).
  After install: `sudo xcode-select -s /Applications/Xcode.app` and open Xcode
  once to accept the license and install the iOS platform.
- No CocoaPods needed — the project uses Swift Package Manager
  (`ios/App/CapApp-SPM`).
- Android: JDK 21 (what CI uses) + the Android SDK; a signed release build
  reads `~/yardscout-android/keystore.properties` (`storeFile`,
  `storePassword`, `keyAlias`, `keyPassword`). Without that file only debug
  builds work. The keystore is NOT in the repo — see `DISASTER_RECOVERY.md`.
- CI needs none of this: the workflows run on `macos-latest` / `ubuntu-latest`
  with signing material from repository secrets.

## Store setup (already done — reference)

1. iOS bundle ID `com.benvuolo.yardscout`, team `G23Z9MSBUG` (change in
   Xcode + `capacitor.config.json` together if ever needed). Android
   applicationId `io.yardscout.app` (namespace stays `com.benvuolo.yardscout`).
2. App Store Connect app "YardScout"; Play Console app under YardScout LLC.
   Subscription `yardscout_pro_monthly` ($8.99/mo) exists on both stores
   (`play-assets/PLAY_IAP_CHECKLIST.md`, `play-assets/LAUNCH_DAY_REPORT_20261021.md`).
3. Privacy: no accounts, analytics off while `GOATCOUNTER_CODE` is null. What
   IS collected when push is on: a device ID, the push token, and watch
   criteria with the centre rounded to ~1 km (`docs/privacy.html`,
   rewritten 2026-10-26). `Info.plist` carries the When-In-Use purpose string
   AND both Always strings — the Always ones are never requested but ASC's
   ITMS-90683 check demands them because the Geolocation plugin references
   the API. Privacy policy URL: `https://yardscout.io/privacy.html`.
4. Screenshots: `appstore-assets/` (iOS sets + `LISTING.md`) and
   `play-assets/` (+ `LISTING.md`); updated by hand in the consoles — the
   workflows only set release notes.
5. Upload: the release workflows (TestFlight by default; `submit=true` also
   creates the App Store version and submits). Play: `track=internal` or
   `production`.
6. Review notes: data is public junkyard inventory, re-scanned about every
   4 hours; `appstore-assets/APPLE_REPLY.md` has the answers given to the
   Guideline 2.1 round.

## Known gaps

- Screenshots/metadata beyond release notes are manual in both consoles.
- The App Store provisioning profile in `IOS_APPSTORE_PROFILE_BASE64` expires
  after a year — regenerate when the iOS run says so.
- Guideline 4.2 (minimum functionality): mitigations in place — bundled
  offline shell, native purchase, native push on both platforms, location
  lookup. Keep adding native-only value rather than removing it.
