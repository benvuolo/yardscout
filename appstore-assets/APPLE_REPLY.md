# Reply to Apple — Guideline 2.1 Information Needed (Sep 29)

Paste the "Reply text" below into the App Review conversation (App Store Connect →
App Review → reply to the message), AND copy items 2–7 into the Notes field of
App Review Information on the version page. Attach the screen recording to the reply
(or a link if it's too large).

A new build (10) is attached to the version — it fixes a visual spacing issue at the
top of the screen. No functional changes.

---

## Reply text

Thank you for the review. Responses to each item:

**1. Screen recording** — Attached. Captured on a physical iPhone running the latest
iOS. It begins at app launch and shows the typical user flow: entering a zip code,
browsing live salvage-yard inventory, opening a vehicle card, adding a vehicle to the
watchlist, enabling push notifications, and opening the subscription sheet — which
displays the subscription title (YardScout Pro), length (monthly, auto-renewing),
price ($8.99/month), and links to the privacy policy and terms of use. The app has no
account registration, no login, and no user-generated content.

**2. Purpose and target audience** — YardScout helps DIY mechanics, car enthusiasts,
and part flippers find specific vehicles at self-service salvage yards ("pick-a-part"
yards) across the US. The problem: yards receive hundreds of new vehicles weekly and
inventory turns over fast, so finding a donor car for a needed part means manually
checking many yard websites daily. YardScout aggregates the yards' own published
inventory into one searchable feed, lets users watch for specific year/make/model
ranges, and sends a push notification when a matching vehicle arrives at a yard near
them.

**3. Setup and access instructions** — No login, account, or sample files are
required. All features are accessible immediately: launch the app, enter any US zip
code (e.g. 84104) or tap "Use my location," and browse inventory. To test alerts: open
the Alerts tab, add a watch (e.g. Toyota 4Runner 1996–2002), and enable push
notifications. To view the subscription flow: tap the PRO badge in the header.

**4. External services** —
- Data source: publicly published online inventory pages of US self-service salvage
  yards (factual vehicle listings: year, make, model, VIN, row number, arrival date).
- Backend/API hosting: Cloudflare Workers with Cloudflare D1 (stores anonymous device
  IDs, push tokens, and watch criteria only).
- Push delivery: Apple Push Notification service.
- Payments: Apple In-App Purchase (StoreKit) exclusively. No third-party payment
  processor is used in the app.
- No authentication services, no AI services, no third-party analytics or ad SDKs.

**5. Regional differences** — None in functionality; the app behaves identically in
all regions. The inventory data itself currently covers salvage yards in the United
States.

**6. Regulated industry / protected material** — The app does not operate in a
regulated industry. It displays factual, publicly available used-vehicle inventory
information (year, make, model, VIN, location) published by the salvage yards
themselves, plus our own editorial estimates of part resale ranges. It contains no
protected third-party material requiring licenses or credentials.

**7. In-App Purchase overview** — One auto-renewable subscription: YardScout Pro,
$8.99/month. Finding cars is free forever; Pro unlocks the "money layer": part resale
value ranges, pull-cost information where yards publish prices, cross-yard part price
comparison, value-based sorting, unlimited saved cars and search radius, and instant
per-arrival push alerts (free users receive a weekly recap push). Navigation to the
purchase flow: tap the "PRO" badge in the top-right header from any tab, or tap any
Pro-gated feature — both open the subscription sheet with the price, renewal terms,
privacy policy and terms links, a Subscribe button, and a Restore Purchases button.

---

## Screen recording checklist (capture on your iPhone)

Settings → Control Center → add Screen Recording if not present. Then record one
continuous take (60–90 seconds is plenty):

1. Start recording from the home screen, then launch YardScout (must begin with launch).
2. Zip prompt: enter 84104 (or tap Use my location).
3. Scroll the Live feed briefly; tap one vehicle card to expand parts.
4. Yards tab: show the yard list/map for a second.
5. Alerts tab: add a watch (pick any make/model), show push alerts enabled.
6. Tap the PRO badge in the header → let the sheet sit for 2–3 seconds so the
   title, $8.99/mo price, auto-renew text, and Privacy/terms links are clearly
   visible. Tap Subscribe if the price loads (cancel the Apple payment sheet —
   that's fine on camera); if it errors, just show the sheet.
7. Stop recording.

AirDrop the video to your Mac and attach it in the App Review reply. If ASC rejects
the attachment size, upload it anywhere private (e.g. iCloud link) and paste the link.
