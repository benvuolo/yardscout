# Android launch day — Oct 21, 2026 (execution log)

Executed the PLAY_IAP_CHECKLIST.md launch plan in the live Play Console
(YardScout LLC, account 9052149026359320771, app io.yardscout.app).
Screenshots for every step: `play-assets/launch-screens/`.

## What shipped

| Step | Status |
|---|---|
| Merchant/payments profile verified | DONE — bank "Checking ••••133" is Primary, no pending-verification banners (06/07/08 screenshots) |
| Subscription `yardscout_pro_monthly` | DONE — created exactly as specified, name "YardScout Pro" (35a/35b) |
| Base plan `monthly` | DONE — auto-renewing, 1 month, $8.99 USD, 175 countries auto-priced, **Active** (43b, 44) |
| License testers | DONE — list "YardScout internal testers" (yardscout.io@gmail.com), enabled account-wide, RESPOND_NORMALLY (32) |
| Internal testing | DONE — release "3 (1.1)" live for testers 06:37 (20b) |
| Production | SUBMITTED — full rollout (100%), sent for Google review 06:47; release notes as planned (50b) |

## IMPORTANT: versionCode 3, not 2 — Billing 8 rebuild

Play Console now **hard-rejects releases using Play Billing < 8.0.0**.
The prebuilt AAB (versionCode 2, Billing 7.1.1) uploaded fine but blocked at
review with an error (screenshot 15). Fixed in commit 3b8432f:

- `android/app/build.gradle`: billing 7.1.1 → 8.0.0, versionCode 2 → 3
  (vc2 was consumed by the blocked upload; version codes are permanent).
- `PurchasesPlugin.queryProduct`: 8.x returns `QueryProductDetailsResult`
  instead of `List<ProductDetails>`.

The AAB at `android/app/build/outputs/bundle/release/app-release.aab`
(sha256 b336ac9d…) is the exact binary uploaded as 3 (1.1). It was built
06:33 — **before** commit b23d09c added `getPurchaseToken` to the plugin.
That's fine and internally consistent: the bundled `native/www/app.js` is
also the pre-b23d09c version that never calls it. The b23d09c work
(cross-device email link on Android) needs a future release that bundles
BOTH the new plugin method AND a `docs/app.js → native/www` sync — don't
ship one without the other.

## verify-android / cross-device status

- The Worker already runs the full implementation (NOT a 501 stub —
  PRO_ENTITLEMENTS_SETUP.md §5 is stale). Secrets GOOGLE_SA_EMAIL /
  GOOGLE_SA_KEY are set in Cloudflare.
- BUT live probe returns 502 `google_error`: the service account is **not
  invited to the Play Console** (Users and permissions shows only
  yardscout.io@gmail.com). androidpublisher rejects it with 401/403.
- OWNER ACTION: Play Console → Users and permissions → Invite new user →
  the service account's `…@….iam.gserviceaccount.com` email → grant at
  least "View app information" + "Manage orders and subscriptions".
  Propagation can take up to ~24h. Until then: Android purchase → local
  Pro works; "Use Pro on other devices" → "Could not reach Google Play".

## What a human must still test (no Android device available here)

1. Join internal testing (opt-in link under Internal testing → Testers →
   "Copy link") with yardscout.io@gmail.com, install, and verify:
   Subscribe shows $8.99/mo → license-tester purchase (free) → Pro unlocks
   → relaunch keeps Pro → uninstall/reinstall → Restore purchases.
2. After production clears review: one real purchase, confirm Acknowledged
   in Order management.
3. After the SA invite: re-test "Use Pro on other devices" end-to-end.
