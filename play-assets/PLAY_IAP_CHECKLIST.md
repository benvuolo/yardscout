# Play Console checklist — YardScout Pro subscription (v1.1)

The 1.1 AAB (versionCode 2) ships Google Play Billing for the Pro subscription.
The code queries ONE product: **`yardscout_pro_monthly`** — a monthly
auto-renewing **subscription** at **$8.99/mo**, matching the iOS StoreKit
product exactly (same id, same type, same price). Everything below happens in
Play Console (https://play.google.com/console) — do it in this order, and do
NOT touch the current 1.0 release while it's still in review.

## 0. Wait for 1.0 to clear review

Don't create a new release or edit store listing while 1.0 is "In review".
Creating the subscription product (steps 2–3) is safe at any time — products
are independent of releases.

## 1. Payments profile (one-time, required before anything sells)

- Play Console → **Settings → Payments profile** (or "Monetization setup"
  prompts you). Link/create a Google payments merchant profile for the
  developer account.
- Google will ask for identity + bank details and may take a day or two to
  verify. Until this is done, in-app products can't be activated.
- US tax info (W-9) is collected in the payments profile flow.

## 2. Create the subscription product

- Play Console → your app → **Monetize → Products → Subscriptions → Create
  subscription**.
- **Product ID: `yardscout_pro_monthly`** — must match EXACTLY (this is what
  the code queries; it cannot be changed after creation).
- Name: "YardScout Pro" (shown in the Play purchase sheet).
- Add a **base plan**:
  - Base plan ID: e.g. `monthly` (code doesn't care — it uses the first
    offer/base plan it finds).
  - Type: **Auto-renewing**, billing period **1 month**.
  - Price: **$8.99 USD** (let Play auto-convert other currencies, same as
    App Store pricing).
  - Grace period / account hold: defaults are fine.
- **Activate** the subscription and the base plan. The app's Subscribe button
  loads price/availability live from Play, so no app update is needed when
  the product goes live — but the product must exist on a version of the app
  Play knows about (see step 4).

## 3. License testers (test the purchase for FREE before release)

- Play Console (account level) → **Settings → License testing**.
- Add your Gmail address (the one signed into the Play Store on your test
  device) to a license-tester list.
- License testers see real purchase flows but **are not charged**, and test
  subscriptions renew on an accelerated schedule (a "monthly" sub renews
  every ~5 minutes) so you can watch renewal/cancel/restore behavior quickly.
- Testing requires a build distributed THROUGH Play (internal testing track
  works — see step 4). A sideloaded debug APK can query products but
  purchases only work when Play knows the installed app.

## 4. Upload the 1.1 AAB (after 1.0 is live)

- File: `android/app/build/outputs/bundle/release/app-release.aab`
  (versionCode 2, versionName 1.1, signed with the upload keystore in
  `~/yardscout-android/`).
- Recommended path: **Testing → Internal testing → Create release** → upload
  the AAB → add yourself as a tester → install via the opt-in link → verify
  the full purchase flow with your license-tester account (Subscribe shows
  "$8.99/mo", purchase completes, Pro unlocks, kill + relaunch keeps Pro,
  uninstall + reinstall → "Restore purchases" brings Pro back).
- Then **Production → Create release** → promote the same build (or upload
  fresh) → roll out. Release notes idea: "YardScout Pro is now available on
  Android — part values, pull costs, price compare, and instant alerts."

## 5. Post-release sanity checks

- Buy (or license-test) once on production; confirm the purchase is
  **Acknowledged** in Play Console → Order management (the app acknowledges
  automatically; unacknowledged subs auto-refund after 3 days).
- Cancel the test sub in Play Store → Subscriptions and confirm the app drops
  Pro after the period lapses (entitlement is re-checked on every launch).

## What the app does (for reference while testing)

- On every launch: queries Play for an active `yardscout_pro_monthly` sub →
  sets/revokes `jh_pro` + `jh_pro_source='iap'` in the web layer (same
  mechanism as iOS).
- "Restore purchases" re-queries Play for the signed-in Google account —
  covers reinstalls and new devices.
- If Play/billing is unreachable, the app keeps the last known Pro state and
  shows "Google Play billing isn't available on this device right now."
  Nothing crashes (verified in an emulator without Play).
- Push alerts are still iOS-only; Android copy says in-app alerts + "push
  coming soon" (no FCM project yet).
