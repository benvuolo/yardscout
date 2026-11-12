# YardScout business plan (2026-11-12)

Sources: the daily ops email of 2026-11-11 and three audits run on 2026-11-12
(search and acquisition, market and channels, funnel and paywall).

## Where the business stands

| | |
|---|---|
| Paying subscribers | 6 (App Store 4, Google Play 1, web 1), about $50 a month before store fees |
| New web visitors | about 14 a day |
| App installs with notifications on | 31; 11 used in the last 7 days |
| Coverage | 304 yards, about 337,000 cars, 45 part types |
| Who shows interest | Toyota truck owners: 4Runner is 13 of 74 watches; GX 470 the most-searched car |

## Diagnosis

1. **Nobody can find it.** YardScout appeared in none of 13 searches, including
   its own name. A competitor with less data (SalvageWatch) ranks for
   "<chain> <city> inventory". Our pages have the wordmark as every headline,
   titles that don't match what people type, no links between pages, a thin
   sitemap, and static text that still says "210+ yards".
2. **The numbers were partly blind.** The iPhone and Android apps have sent no
   funnel events since 2026-11-02 (a "don't count local copies" guard also
   matched the apps). "Entered a zip" and "part searches" over-count. So "0
   checkout taps" is true for the web only.
3. **Interested visitors can't be reached again.** A watch set on the web lives
   only in that browser: no email ask, no web push. The free Monday recap email
   is built and deployed, but nobody can sign up for it. The "Alert me" buttons
   on shared car and yard pages land new visitors on a broken form.
4. **The buy button is off-screen.** On typical phones it sits 81–287 px below
   the fold of the Pro sheet, and the $1.99 first-month offer appears only
   beside it. 31 opens, 0 taps.
5. **Price is not the bottleneck; reach is.** Two rivals charge $3.99 a month
   and give one free instant alert. With 14 visitors a day a price cut cannot
   be measured, let alone pay off.
6. **A real opening exists.** Row52, the old cross-yard search, now covers only
   Pick-n-Pull. A Grassroots Motorsports thread asks "How to find JY cars
   without Row52". Searching across chains is what YardScout does.

## Priorities, in order

| # | What | Status | Who |
|---|---|---|---|
| 1 | Search basics: real headlines, query-matching titles, yard pages as inventory pages, links between pages, full sitemap, price-list pages, "300+" static text | Building (branch `seo/onpage-1`) | Hub |
| 2 | Search Console: confirm the site, submit the sitemap; add Bing Webmaster Tools | Not started | **Owner, 30 min** |
| 3 | True numbers: apps report again, counts once per person, split by platform, store-link taps | Building (branch `growth/funnel-1`) | Hub; app half needs a store release ("ship") |
| 4 | Pro sheet: buy button and first price always visible; Android visitors sent to Google Play | Building (same branch) | Hub |
| 5 | Shared-page "Alert me" lands on a working, prefilled watch form | Building (same branch) | Hub |
| 6 | Free weekly email for web watchers, asked when a watch is set | Waiting for decision D1 | Owner decides, hub builds |
| 7 | Community posts and creator emails (drafts ready) | Waiting for decision D5 | **Owner posts**, hub drafts and pulls the numbers |
| 8 | Nationwide make/model pages for the 379 models with 100+ cars | After 1 is live | Hub |
| 9 | Pricing: annual plan; one free prompt alert | Waiting for D2, D3 | Owner decides |
| 10 | Store listing text (Play description never says "junkyard") | Proposed strings ready | Owner's "ship" |

Deliberately not now: more parts-matching depth beyond what is already
audited, anything for repair shops, selling to yards, affiliate links (a day
of work for $0–10 a month at this size), a reseller tier (needs real sold
prices first), a lifetime deal.

## Positioning

- To someone hunting a specific truck or car: "YardScout watches every
  self-service yard in your range for your exact model and years, and sends
  you the yard and row the day one is set out."
- To someone who pulls parts to resell: "YardScout shows what landed near you
  since yesterday, what each yard charges for each part, and what that part
  typically goes for online, before you pay admission."
- Three claims rivals don't make: fit you can weigh (Verified or Likely, from
  carmaker catalogs); the yard's price beside the online price; how long a car
  typically lasts on that lot.
- Don't lead with "most yards": one rival claims 250+ and another 500.

## How to run it (organization)

- **Usage split until traffic passes 40 visitors a day:** about 60% growth
  (search, funnel, email, posts), 30% keeping data correct and scans healthy,
  10% new depth. The last week was close to the reverse.
- **One hub plus at most two builders at a time.** Six parallel sessions spent
  most of a week's usage in three days.
- **One weekly scorecard, five numbers:** new visitors per day (by source),
  watches created, emails captured, paywall-to-checkout rate, paying
  subscribers.
- **One store release per batch of app-side fixes.** The next one carries the
  measurement fix and the Pro sheet; it needs the owner's "ship".
- **Talk to the six subscribers.** Ask each what they would miss most and what
  nearly stopped them paying. Their words go in the store listing.

## Decisions for the owner

| # | Decision | Recommendation |
|---|---|---|
| D1 | Collect an email when a web visitor sets a watch, for the free weekly "what landed" email (privacy text updated to say so) | Yes |
| D2 | Give the one free watch a prompt alert within a short radius (both $3.99 rivals do) | Yes; it gives away part of Pro, so the radius should be short |
| D3 | Add an annual plan | Yes, $34.99, sold on the web too |
| D4 | Reword the privacy page: it says "We don't run analytics… Full stop", but the app sends anonymous counters | Yes, and soon: the page should say exactly what is counted |
| D5 | Post in communities and email creators yourself, from the drafts | Yes, about 5 hours a week for 4 weeks |
| D6 | Search Console and Bing setup | Yes, this week |
| D7 | Store listing text changes | Yes, with the next release |
| D8 | One retry each for the Mercedes and Nissan catalogs | Yes for Nissan at least |

## 30-day targets

40 new visitors a day, 100 app installs, 12–15 paying subscribers, and a
working count of where each one came from. If the Grassroots Motorsports reply
and the r/4Runner post both fall flat, change the message before adding
channels.
