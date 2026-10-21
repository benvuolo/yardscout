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

- **Shot 4 (alerts)** — re-captured 2026-10-21 (owner call): **no push
  wording at all** while Android has no push (FCM is being built for 1.2).
  The capture hides every push surface (web Notification-API button, native
  `#native-alerts-note` push panel, web-only "Get the iOS app" and
  email-alerts panels) and renders in-app-only copy: "Watched cars light up
  right here the moment they arrive at a yard in your radius." The Pro
  tier-comparison row renders "In-app alerts within hours…" without the
  app's "(push coming to Android soon)" parenthetical. The capture asserts
  zero visible "push"/"coming soon" strings before shooting.
  - **When FCM ships in 1.2:** restore the push-state rendering of
    `alerts_shot` in `_capture_android.py` from git
    (`git show b66d882:play-assets/_capture_android.py`), re-capture
    `--alerts-only`, and swap the slide in the Play listing.
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
