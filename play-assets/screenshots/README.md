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
(Superseded: the 5-slide set went live Oct 21–22; see below for the Oct 23
7-slide interchange update.)

## Interchange release additions (2026-10-23)

Two new slides captured by `play-assets/_capture_android_interchange.py`
(same geometry/house rules as the rig above; zip **84047** — Midvale, Salt
Lake valley; free-tier state; real production data; the web-only
"YardScout is now a native app" banner is suppressed via `ys_app_promo` —
it never renders in the native builds):

| Play file | Mirrors iOS file | Scene |
|---|---|---|
| `screen_6_compare.png` | `screen_6_compare.png` | Yards tab — "Alternator" compared across the 7 Salt Lake–area yards in view, compare sheet open, default **cheapest-first** sort (capture asserts ascending prices) |
| `screen_7_fitment.png` | `screen_7_fitment.png` | Parts tab — 2005 Toyota Camry + alternator fitment: engine-chip question (2AZ-FE I4 chosen), 95 donors, **Verified fit** and **Likely fit — verify part #** tags both legible in frame (capture asserts both tiers visible) |

**Slide order** (uploaded + sent for review 2026-10-23, superseding the
step19/step20 5-slide order — new slides sit right after the core Live/search
pair, fitment first because the honesty tiers are the differentiator; the Pro
value shot stays last-ish and alerts still closes the deck):

1. `screen_1_live.png`
2. `screen_2_search.png`
3. `screen_7_fitment.png` *(new)*
4. `screen_6_compare.png` *(new)*
5. `screen_3_yards.png`
6. `screen_5_pro.png`
7. `screen_4_alerts.png`

Upload evidence: `play-assets/listing-update/46c-after-full-order.png`
(editor, 7/8 slot) and `47d-after-submit.png` (change in review). The vc9
(1.5) production release had already cleared and published before the listing
change was sent — the two reviews are independent.

The iOS pair (`appstore-assets/ios/screen_6_compare.png` /
`screen_7_fitment.png`, plus 6.5-inch and dynamic-island derived sizes) is
captured and ready but **not uploaded**: ASC is logged out (owner logs in
manually) and iOS 1.6 wasn't submitted yet at capture time. Attach them to
the 1.6 version page if it's still editable, else right after 1.6 clears
(metadata edits post-approval are allowed), in the same 7-slide order.
