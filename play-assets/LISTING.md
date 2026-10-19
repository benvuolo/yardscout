# Google Play Listing Kit — YardScout

Everything to fill in when you create the app in Play Console.
AAB to upload: `android/app/build/outputs/bundle/release/app-release.aab`

---

## App details

| Field | Value |
|---|---|
| App name (30 max) | `YardScout: Junkyard Inventory` |
| Package name | `io.yardscout.app` (set automatically by the AAB) |
| Category | Auto & Vehicles |
| Free/paid | Free |
| Contains ads | No |
| Email | yardscout.io@gmail.com |
| Website | https://yardscout.io |
| Privacy policy URL | https://yardscout.io/privacy.html |

## Short description (80 chars max)

```
Live inventory from 210+ self-service junkyards. Find the car before you drive.
```
(78 chars)

## Full description (4000 chars max)

```
YardScout tracks the live inventory of self-service salvage yards across the country, so you stop driving to yards on a maybe.

FIND THE CAR BEFORE YOU DRIVE
• Live inventory from 210+ self-serve yards — every major chain (Pick-n-Pull, LKQ Pick Your Part, Pull-A-Part) plus a growing set of independents — refreshed throughout the day
• Search by make, model, and year range around your ZIP
• See the row number, arrival date, and VIN before you leave the house
• Model search understands yard naming quirks — searching WRX finds every spelling

KNOW THE YARDS
• Every tracked yard near you with distance, car counts, and what arrived this week
• Each yard's own published pull-price list, right in the app — no digging through junkyard websites
• Tool rules per yard (sawzalls, compressors) so you bring the right gear

WATCH FOR THE RIGHT CAR
• Build a watchlist of makes, models, and years — picked from vehicles that actually cycle through yards, so no typos
• Watched cars light up in the app the moment they arrive at a yard in your radius

PRO (coming to Android soon)
• Resale value ranges and demand speed on nearly every car
• Cross-yard price compare — find the cheapest alternator near you
• Instant push alerts within hours of a watched car arriving — before the weekend crowd strips it
• Sale-day alerts when a yard near you runs a half-off sale

NO ACCOUNT, NO EMAIL
• The whole app works without signing up
• We never ask who you are

Finding cars is free forever.

Privacy policy: https://yardscout.io/privacy.html
Terms of use: https://yardscout.io/terms.html
```
(~1,500 chars — well under the limit)

## Graphics assets (in this folder)

| Asset | File | Spec |
|---|---|---|
| App icon | Play pulls it from the AAB automatically; if asked for a 512×512, use `assets/icon-only.png` resized | 512×512 PNG |
| Feature graphic | `feature_graphic.png` | 1024×500 |
| Phone screenshot 1 | `screen_1_live.png` | 1080×2400 — live results near Salt Lake City |
| Phone screenshot 2 | `screen_2_cards.png` | 1080×2400 — car cards with badges |
| Phone screenshot 3 | `screen_3_yards.png` | 1080×2400 — yards tab with price lists |
| Phone screenshot 4 | `screen_4_alerts.png` | 1080×2400 — watchlist / alerts |

Upload screenshots in that order (minimum 2 required, we have 4).

## Content rating questionnaire

- Category: Utility / Productivity / Communication or "All other app types"
- Violence, sexuality, drugs, gambling, hate speech: **No** to everything
- User-generated content: **No**
- Expected rating: Everyone

## Data safety form

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **Yes** (location, see below) |
| Location → Approximate location | Collected: **Yes**. Shared: **No**. Processed ephemerally: **Yes**. Required: **No** (optional — users can type a ZIP instead). Purpose: **App functionality** (find yards near the user). |
| Location → Precise location | Same answers as approximate (the "use my location" button requests fine location, used once to center the search, never stored or transmitted to a server). |
| All other categories (personal info, financial, health, messages, photos, files, audio, contacts, calendar, app activity, browsing, identifiers) | **Not collected** |
| Is all of the user data collected by your app encrypted in transit? | **Yes** |
| Do you provide a way for users to request that their data is deleted? | **Yes** — nothing is stored server-side; deleting the app deletes all data. Point to https://yardscout.io/privacy.html |
| Data sold to third parties | **No** |
| Ads | **No** |

## Target audience

- Age: 18 and over (simplest; avoids Families policy requirements)
- Not designed for children: Yes

## App access

- "All functionality is available without special access" — **Yes** (no login, no credentials needed for review)

## Release notes (first release)

```
First Android release. Live inventory from 210+ self-service junkyards, yard price lists, and a vehicle watchlist — free, no account needed.
```
