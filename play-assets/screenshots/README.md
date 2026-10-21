# Google Play phone screenshots

Captured 2026-10-21 by `play-assets/_capture_android.py` (Playwright against the
live production app at yardscout.io — all numbers, inventory, and prices are
real production data at capture time).

**Dimensions: 1080 x 2160 PNG (exactly 2:1 portrait).** Google Play phone
screenshots require PNG/JPG, each side 320–3840 px, and portrait aspect no
taller than 2:1 — the iOS App Store set (1320 x 2868, ~2.17:1) is too tall for
Play, so these are re-rendered at a Play-legal geometry (viewport 432 x 864
@ 2.5x device scale), not downscaled/cropped iOS images. Text proportions match
the approved iOS set (CSS width 432 vs iOS 440).

## Mapping to the approved iOS set (`appstore-assets/ios/`)

| Play file | Mirrors iOS file | Scene |
|---|---|---|
| `screen_1_live.png` | `screen_1_live.png` | Live tab, zip 84101, free tier — stats chips + fresh arrivals |
| `screen_2_search.png` | `screen_2_search.png` | Live tab filtered to a popular make/model (Honda Civic at capture time, same candidate logic) |
| `screen_3_yards.png` | `screen_3_yards.png` | Yards tab — yard cards with price-list links |
| `screen_4_alerts.png` | `screen_4_alerts.png` | Alerts tab — **rendered in the Android build's state**, see below |
| `screen_5_pro.png` | `screen_5_option_a.png` | Pro state: the same 2019 Ford F-150 @ Utah Pic-A-Part – Ogden, expanded sellable-part values |

## Android-specific honesty notes

- **Shot 4 (alerts)** — re-captured 2026-10-21 after **1.2 (vc6) with FCM
  push was published**: now renders the unified native push state that the
  shipped Android app shows — native intro ("weekly recap push" free,
  "instant push alerts" Pro) and the Push alerts panel with its live
  "Enable push notifications" button. app.js dropped its Android-only
  "coming soon" branches in the FCM release, so iOS and Android share this
  copy. The capture still asserts no "coming soon"/iOS-specific strings in
  the alerts tab before shooting. (History: the interim no-push honest
  version lived at `5281bb1`; the pre-FCM push-hedged version at `b66d882`.)
- **Shot 5 (Pro)** follows the house rules from the iOS review: a yard with
  real published prices (every part row carries a concrete UTPAP list price —
  no "check yard price list" fallbacks) and no option-dependent
  "VIN-confirmed" badges (only honest "if equipped — unconfirmed" labels).
- Coverage numbers in the header ticker are computed live from production data
  (showing the exact yard count, e.g. "212 YARDS COAST TO COAST", at capture
  time — no rounded-tier change was live in production yet).

## Upload status

**Not uploaded.** 1.1 (versionCode 3) is in Google review — the Play Console
stays untouched until it clears. Upload these to
Store presence → Main store listing → Phone screenshots afterwards.
