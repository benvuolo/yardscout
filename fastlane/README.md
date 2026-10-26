# Store listing source of truth

`fastlane/metadata/en-US/` (App Store) and `fastlane/metadata/android/en-US/`
(Google Play) hold the listing text the release workflows upload:

- iOS: `release-ios.yml` with `submit=true` runs `fastlane deliver` with this
  metadata (+ `fastlane/screenshots/en-US/` when present, 1320x2868 iPhone
  6.9") and the run's What's New, then submits.
- Android: `store-listing.yml` (manual) runs `fastlane supply` with the
  Android metadata (+ `images/phoneScreenshots/`, 1080x2160) — listing only,
  no binary.

Screenshots are regenerated from the local web shell with
`tools/capture_store_shots.py` (both sizes in one run). Edit the text here,
not in the consoles; `appstore-assets/LISTING.md` and `play-assets/LISTING.md`
are now history/reference only.
