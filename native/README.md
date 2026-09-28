# YardScout — native iOS wrapper (Capacitor)

The App Store build wraps the PWA in `docs/` with Capacitor. The shell
(HTML/JS/CSS, ~540KB) is bundled in the app; the ~36MB `data/` directory is
NOT — the native app fetches live data from the GitHub Pages deployment
(`DATA_BASE` in `docs/app.js`), so inventory stays fresh without app updates.

Native-only behavior (all keyed off `IS_NATIVE` in `docs/app.js`):
- data fetches go to `https://benvuolo.github.io/yardscout/`
- service worker registration skipped (doesn't work on `capacitor://`)
- iOS "add to home screen" install hint suppressed
- Stripe billing mode can never activate — Pro purchase on iOS must ship as
  StoreKit IAP (Apple guideline 3.1.1); until then natives see the waitlist

## Build workflow

```bash
./native/stage.sh        # copy docs/ -> native/www (minus data/, sw.js)
npx cap sync ios         # copy native/www into the Xcode project
npx cap open ios         # open in Xcode; or: open ios/App/App.xcodeproj
```

Always re-run stage.sh + sync after editing anything in `docs/` — the
bundled shell does NOT update itself.

Icons/splash are generated from `assets/` (`logo.png`, `icon-only.png`,
`splash.png`) with `npx @capacitor/assets generate --ios`. The current icon is
the 512px PWA icon upscaled to 1024 — replace `assets/icon-only.png` with true
1024px art before submission if possible.

## One-time machine setup

- Xcode from the Mac App Store (Command Line Tools alone can't build iOS).
  After install: `sudo xcode-select -s /Applications/Xcode.app` and open Xcode
  once to accept the license and install the iOS platform.
- No CocoaPods needed — the project uses Swift Package Manager.

## App Store submission checklist (human steps)

1. Xcode > App target > Signing & Capabilities: select your Apple Developer
   team. Bundle ID is `com.yardscout.app` (change here + `capacitor.config.json`
   together if needed).
2. App Store Connect (appstoreconnect.apple.com): My Apps > "+" > New App —
   name "YardScout", bundle ID from step 1, SKU anything.
3. Privacy: the app collects nothing personally identifying today (no
   accounts, analytics off while `GOATCOUNTER_CODE` is null). Privacy policy
   URL: use the GitHub Pages `privacy.html`.
4. Screenshots: 6.7" (iPhone Pro Max) and 5.5" sets required — take them in
   the Simulator (Cmd+S).
5. Archive & upload: Xcode > Product > Archive > Distribute App > App Store
   Connect.
6. Review notes: mention data is public junkyard inventory, refreshed daily.

## Known gaps before/after launch

- **Pro purchase**: no IAP yet — natives see the waitlist. Ship StoreKit
  (RevenueCat is the fast path) before marketing Pro on iOS. Requires the
  $9.99/mo auto-renewable subscription created in App Store Connect first.
- **Push alerts**: web push does not exist inside the wrapper. Watches +
  weekly email digest work; instant push on iOS needs the Capacitor
  Push Notifications plugin + APNs key + backend APNs sender (the Worker
  currently speaks web push only).
- **Guideline 4.2 (minimum functionality)**: wrappers get rejected when they
  are "just a website". Mitigations already in place: offline-capable bundled
  shell, app-specific behavior. Adding native push (above) is the strongest
  signal — consider shipping it before first review.
