# Growth — workstream status

Owns: the signup funnel (first visit to paying), its counters, and the copy
and layout of the steps on it. Source: the funnel audit of 2026-11-12
(read-only walk of main 01d0d7ea; its ten ranked changes are numbered below
as "audit change N"). Standing rules in `/CLAUDE.md` apply; rules 1, 3 and 6
are the ones this work touches.

## Free Monday email for web watchers (audit change 2) — branch `growth/email-signup`, NOT merged

Owner approved 2026-11-12. Built on origin/main d6a83c10 (which already
contains `growth/funnel-1`). Pushed for the hub to review; nothing deployed,
merged, dispatched or released. Merging deploys the web app and the API
worker, and the deploy workflow applies migration 0015 (new tables only).

**What the visitor sees (web only; never in the app shells; not for Pro).**
Right after a new watch (card/car-screen bell, Cars watch strip, Parts watch,
the share-page one-tap card, and the Alerts form's Add), the watch toast's
second line becomes: "Get a free Monday email listing every **<Make Model>**
set out within <N> mi." + an email field + "Email me". Then: "Check your
inbox. Tap the link we sent to v•••@example.com to start your Monday email.
Nothing is sent until you do." The watch is saved before the offer shows.
The x, or 30 s untouched, = not asked again this visit (sessionStorage). The
confirmation button lands on `/#recap=confirmed&sub=<token>`: "You're in.
Your free Monday email to v•••@… is confirmed." Later watches: "Add <Make
Model> to your free Monday email?" + "Add" (one tap, no field).

**Server (`backend/src/recap_signup.js`, migration 0015).**
`POST /v1/recap/signup` stores the address + a COPY of the watch criteria
(make, model, years, centre rounded to ~1 km, radius ≤ 250; no trim/drive,
no browser ids), pending, and sends ONE confirmation (`email:confirm`). A
second watch within the hour rides the same link. `GET /v1/recap/confirm`
is a page with a button (mail scanners cannot opt anyone in); `POST`
confirms, counts `email-confirmed` server-side, 303s to the app with a
signed one-tap token. `POST /v1/recap/add {sub, watch}` adds a confirmed
copy. `GET|POST /v1/recap/unsubscribe` (signed, one click, RFC 8058) DELETES
the address, its copied watches, its recap dedupe and sale dedupe rows.
Unconfirmed addresses are deleted after 7 days (hourly cron). Limits: 8
sign-ups/hour per IP (in-memory bucket, IP never stored), 3 confirmation
emails/day per address, 5 watches per address. The reply never says whether
an address was already subscribed. Logs mask addresses.
Monday job (`alerts.js sendWeeklyDigests`): confirmed copies join the
existing recap (same email, same Pro teaser); dedupe in `recap_sent`; an
address that is also a free account gets one email.
**Every** weekly recap (accounts too) now has a footer saying why it came, a
one-click unsubscribe link and List-Unsubscribe headers; an account holder
who unsubscribes goes in `recap_optout` (account and its watches untouched).
**Resend cap:** confirmations and recaps are optional mail and stop while
fewer than 10 sends are left today (`ops.js optionalEmailAllowed`,
`RESEND_DAILY_CAP` env overrides 100). A held sign-up gets "Our email sender
has reached today's limit. Your watch is saved here; try the email again
tomorrow." and stores nothing; a held recap is not marked sent and the hourly
cron retries it on a later day (up to 5 days). Both are counted
(`<channel>:held`).

**Ops email.** USAGE: "Monday email (web sign-ups): N confirmed subscribers
(M watches) · K waiting for the confirmation click" (text + HTML). Funnel rows
"Monday email asked / given / confirmed" (web only; dashes for the apps).
SENDS: "HELD BACK at the Resend daily cap (24 h): …" when anything was held.

**Privacy page:** the web "never leaves your device" sentence names this one
opt-in exception; new section "The free Monday email (website)" says exactly
what is stored, why, how to unsubscribe, deleted on unsubscribe; tallies list
includes the three events. Date: November 12, 2026.

**Tests.** `recap_signup_unit.mjs` (65, real handlers on SQLite with all
migrations), `recap_ask_e2e.mjs` (35, client), `e2e-email.sh` phase 2 +
`recap_signup_e2e.mjs` (33, against mock Resend; mock now records html and
headers), `ui_no_truncation.mjs` screens `watch-toast-recap`, `-msg`,
`-sent`, `-add`. sw.js jh-v184.

**Needs the owner.**
1. Postal address for commercial email: `EMAIL_POSTAL_ADDRESS` in
   `backend/wrangler.toml` is empty, so no address line is printed. Set it
   (exact text to print) before relying on the recap commercially.
2. Sender: confirmations and recaps go from `EMAIL_FROM` = "YardScout
   <hello@yardscout.io>" (subject "Confirm your free YardScout Monday email"
   / "Your week at the yards — N watched cars arrived"). Keep or change.
3. `EMAIL_UNSUB_SECRET` must be set in production (it already signs Pro
   unsubscribe links); without it sign-up answers 503 `not_configured`.

**Seen, not fixed (other files / pre-existing).**
- Before this branch the free weekly recap had no unsubscribe link or
  List-Unsubscribe header (fixed here for all recaps). The Pro instant email
  fallback in `alerts.js` (API-mode accounts, unused) still has none.
- Full addresses in logs: `email_alerts.js` prod log "alert email sent to
  <email>", the Pro unsubscribe page shows the full address, `auth.js` DEV
  log of magic links; `magic_tokens.request_ip` stores the requester's IP.
- `ui_no_truncation`: with the `yards-map-watch` screen in the run, the
  Alerts tab badge "99+" sits past the right edge at 200% text on 320–390 px
  (same on main d6a83c10; tab bar, not this work).
- At 320 px and 200% text the toast head wraps "Watchi-ng" mid-word
  (existing head markup).

**Left.** The same field on the Parts results watch prompt is covered (it
goes through the toast); a standing "Monday email" row on the Alerts tab for
someone who dismissed the offer is not built. `utm_source=recap` on the
recap's links is not added.

## State (2026-11-12) — branch `growth/funnel-1` (since merged to main)

Three commits from main cd8e57e5, pushed for the hub to review. Nothing was
deployed, dispatched or released. Merging to main deploys the web app (GitHub
Pages) and the API worker. **The app shells bundle the web app, so app users
get none of this until a later store release, which needs the owner's
"ship" (rule 1).**

Touches `docs/app.js`, `docs/index.html` (Pro sheet markup only),
`docs/styles.css`, `docs/sw.js` (jh-v182; `seo/onpage-1` takes jh-v181),
`backend/src/attribution.js`, `backend/src/ops_monitor.js`, and tests under
`backend/test/`. No migration, no workflow, no native code, nothing under
`backend/site-proxy/`.

### 1. analytics: the funnel numbers are true (audit change 3)

- **The apps report again.** Both shells load the bundle from the hostname
  `localhost`, and the "never count local copies" guard (2026-11-02) matched
  it, so every app build made since sent no funnel events. The guard now
  exempts the native apps from the hostname rule; a local web copy and any
  automated browser stay silent.
- **Counted once.** "Entered a zip" fires when a zip is entered or changed,
  not on every launch with a saved one. A part search (and the "most
  searched" part and car signals) counts once per distinct part + car while
  the app is open, not on every re-render. "Paywall opens" count only someone
  who is not Pro; the re-opens after a checkout or an unlock code go under a
  name that is not a funnel counter. "Alerts turned on" in the apps counts a
  granted permission, not the tap. Saving an edited watch is not a new watch.
- **New counters.** Store-link taps, per store and place
  (`store-click/<appstore|play>-<sheet|toast|banner|header|footer|alerts>`),
  web only. Web checkout taps and purchases now carry their gate, like the
  apps' (`checkout/<gate>`, `purchase/<gate>`).
- **Privacy promise unchanged.** Still one anonymous +1 per event: no ids, no
  IPs, nothing stored about a person. Each event now also carries `v: 2`
  (the counting-rules version). The API writes one marker row per day and
  platform (`funnel-v2`) so the email knows which days predate the fix.

In the daily email:

- "Funnel" is by platform: Web / iOS / Android, each cell "yesterday / 7 d"
  (the text part has six number columns). Numbers are as each platform
  reported; nothing is apportioned.
- New row "Store link taps" (a dash for the apps, where there is no store
  link), and under the table "Store link taps (7 d, web): App Store N, Google
  Play N · from: app banner N, watch toast N, Pro sheet N".
- "Rating prompts" shows a dash for the web.
- Notes under the table say which columns predate the fix, and drop out by
  themselves: "Web: fixed counters since <day>. The 7 d column still includes
  N earlier days of the old counting…" (gone after seven days), and "iOS and
  Android: no app build with the fixed counters has reported yet…" (gone for
  each platform on the first day a fixed build reports, i.e. after the next
  store release).
- "App devices" is now "App installs with notifications turned on" (HTML
  tile: "Apps with alerts on"), with the line "An install that never turns
  notifications on is not counted here or anywhere else on the server." The
  old "alerts on" figure is "reachable by push now" ("Push token live").
- "What opens the Pro sheet": the Checkout and Bought columns now include the
  web.

What to expect after the merge: web "Entered a zip" and "Part searches" drop
(they were launches and re-renders), web "Paywall opens" drops by the Pro and
code-redemption opens, and the app columns stay near zero until a store
release. Do not compare the first week with the week before.

### 2. pro-sheet: buy button and first price pinned (audit change 1, and the store link from change 7)

- The sheet's primary button and one price line are in a pinned footer; the
  pitch, feature list and fine print scroll above it. Button bottom edge at
  100% text, before and after: 390x844 955 -> 805, 375x667 954 -> 628,
  320x568 1056 -> 529 (web; the apps 950 / 928 / 1031 -> the same 805 / 628 /
  529). In view at 200% text too, light and dark.
- Web: "Get Pro — $8.99/mo" + "$8.99/month, cancel anytime." Apps: "Start
  for $1.99 — first month" + "Then $8.99/mo. Cancel anytime." (the store's
  intro offer, when the store reports it). No price, product id or gate
  changed; the copy is the sheet's own, shortened to fit.
- On the web an Android visitor's "Prefer the app?" link goes to Google Play
  with Play's wording (it went to the App Store with "cancel in iOS
  Settings"). One builder (`webStorePlatform` + `storeLink`) now serves the
  sheet, the watch toast and the app banner.

In the daily email: "Checkout taps" / "Paywall opens" per platform (web now;
apps after a release), and the Checkout column of "What opens the Pro sheet".

### 3. alerts: share-page "Alert me" lands on a watch that can be set (audit change 4)

- `/#tab=alerts` from `/car/<vin>` shows a card at the top of Alerts: "Get
  told when another <make model> lands near you", with a zip field in the
  card when no location is saved, and one "Watch" button. The form below is
  prefilled with the same make and model. From `/landed/<make>` the form's
  make is prefilled. The car comes from the referrer (our own page) and the
  published scan's key index.
- The watch form's Make and Model lists come from `data/models.json` until
  the whole scan is loaded (they were empty for a visitor with no location).
- Any free visitor on the Alerts tab with no location gets the zip field
  there; the form's Add with no location asks for the zip in that card and
  then finishes the Add (it was a browser alert pointing at the Cars tab).
- The four "Set your zip code up top first" browser alerts (card bell, car
  screen "next one", Parts watch, Cars watch strip) are a zip field in the
  toast, which then makes that watch.
- Creation path only: every watch is still made by `addQuickWatch` /
  `addWatchItem`; stored watches are not read back, rewritten or migrated
  (rule 6; `share_watch_e2e.mjs` checks them byte for byte).

In the daily email: "Watches created" (web), and first-visit to watch per
source once the share links carry `utm_source` (below).

**For whoever owns `backend/site-proxy/src/share.js` (not edited here):**
the app now also accepts `/#watch=<make>|<model>|<years>` (URL-encoded;
model and years optional; years `2005-2009`, `2005-`, `-2009` or `2007`).
It does not depend on the referrer, which in-app browsers can strip.
Suggested: the car page's alert link becomes
`${SITE}/?utm_source=share&utm_medium=car#watch=${encodeURIComponent(v.make + '|' + v.model)}`,
the make page's `…#watch=${encodeURIComponent(mk)}`; the "gone" page can use
the same when the car is known. `#tab=alerts` keeps working.

### Tests added or extended

`backend/test/funnel_counters_unit.mjs`, `funnel_events_e2e.mjs`,
`pro_sheet_fold_e2e.mjs`, `share_watch_unit.mjs`, `share_watch_e2e.mjs`;
`ui_no_truncation.mjs` gained the fold check and the screens
`pro-sheet-store-ios|android`, `pro-sheet-app`, `pro-sheet-app-android`,
`pro-sheet-member`, `alerts-intent-car`, `alerts-intent-zip`,
`alerts-intent-car-located`, `watch-toast-zip`; `ops_e2e.mjs` follows the new
email. The hub runs the full `ui_no_truncation.mjs` before merging (only the
Pro sheet and watch/alerts screens were run here).

## Needs the owner

1. **"ship" for the app half** (rule 1). Until a store release, the apps
   keep sending nothing and keep the old sheet.
2. **Privacy text.** `docs/privacy.html` says "We don't run analytics or
   trackers… Full stop." The anonymous daily counters have existed since
   2026-10-26 and "What the app fetches" does not list them. Not changed
   here; the wording is the owner's call.
3. **Free weekly email for web watchers** (audit change 2): approved by the
   owner 2026-11-12; built on `growth/email-signup` (section above).
4. **Pricing** (audit change 10): annual plan, a short pass, a web first
   month to match the apps' $1.99. Not touched.

## Left, no owner decision needed

- First-run flow (audit change 5): a car and the job after the zip, the
  install banner later. Touches the approved Pull Sheet design.
- The free sample card where it is seen (6); the web sheet's promise of a
  push that a web purchase cannot deliver, and the out-of-date "one-tap
  watch" Pro bullet (7, copy); first donor car directly under the result
  count (8, owner confirms the notes may fold); keep asking for
  notifications and reorder Alerts (9).
- `ops/README.md` has no row for this file yet (hub's table).

## Weekly scorecard — branch `growth/scorecard`, NOT merged (2026-11-12)

Built on origin/main 5df6f218. Nothing deployed, merged, dispatched, sent
or called in production.

**What it is.** A "Weekly scorecard" block at the top of the daily ops email
(text and HTML, every day) and the same numbers as JSON from
`GET /v1/admin/scorecard` (x-admin-secret, like `/v1/admin/attribution`).
Always the last 7 full UTC days vs the 7 before. Five numbers: new visitors a
day (by platform, and "From:" top 5 tagged source / campaign + other links +
"no tag"); watches created; Monday email offered → address given → confirmed
(website only); Pro sheet opened → checkout → bought Pro with the rate; paying
subscribers (App Store + Google Play from KV `ops:store-subs`, web = Stripe
entitlements as the email already counts them). Then one line per tagged link:
visits (split by medium when there is more than one) → watches → emails
(addresses given; confirmations are counted server-side without a source) →
checkouts → Pro. Code: `backend/src/scorecard.js`; wiring in `ops_monitor.js`
(`buildDailyReport`, `composeDaily`, `composeDailyHtml`, `handleScorecard`)
and `index.js` (route).

**Honesty rules as built.** No change figure for a platform whose
`funnel-v2` marker day is after the first day of the earlier week: "not
comparable before <date>"; a platform with no marker (the apps until a fixed
build ships) says "not comparable yet (<app> update pending)". A total gets a
change only if every platform with data is comparable; per-platform changes
are still shown. A platform with no counter row at all in a week is "no data";
one that reported but had none of an event is 0. Changes and rates over a base
under 20 are raw counts ("2 of 9", "7 vs 5 the week before").

**Subscriber history (new KV key, no migration).** No history existed, so the
real 13:07 daily run now stores one small record in ENTITLEMENTS KV
`ops:subs-daily` = `{days: {YYYY-MM-DD: {apple, google, web, total,
complete}}}` (counts only, last 60 days). Dry runs and the admin endpoint
store nothing. The change compares with the snapshot from exactly 7 days
earlier; until one exists the email says "change: tracking starts <first
day>" (nothing back-filled or estimated; a gap says "no count stored for
<day>"; a missing store count on either day gives no change).

**What to expect the first week.** Web's marker day is when the v2 build
first reported; for 14 days after it, web changes read "not comparable
before <that day>". The apps read "not comparable yet" until a store release
with the fixed counters (needs the owner's "ship"). Subscriber change appears
7 days after the first daily run after the deploy.

**Tests.** `node backend/test/scorecard_unit.mjs` (96, fixture rows +
SQLite with all migrations + the whole daily email); `ops_e2e.mjs` gained
the admin route (401 / 200 / no addresses) and "scorecard before OPEN
ISSUES" (e2e-ops.sh 150 pass).

**App counters.** None needed for this. Not built: a per-source count of
confirmed Monday emails (the server counts the confirmation without the
visitor's source; carrying it would mean storing the source with the pending
sign-up — a decision for this workstream later, not done here).

## Narrowing counters + confirmed sign-ups by link — branch `growth/narrowing-counters`, NOT merged (2026-11-13)

Built on origin/main b3005269, main merged in at 946f2b71 (no conflicts).
Nothing deployed, merged, dispatched, sent or called in production.

**Why.** (A) The owner will decide in two weeks whether the Cars search box
(added 2026-11-12) stays; its picks went only to the switched-off analytics
(`track('car-search')`, GOATCOUNTER_CODE null), so nothing was counted. (B)
The scorecard's per-link line could show addresses given but not confirmed.

**A. Counters (docs/app.js, EVENTS_V 2 -> 3).** Through `/v1/events` as
ordinary anonymous daily counters (no ids, no IPs), names `narrow/<kind>`:
- `narrow/search` a make or model picked from the search box;
- `narrow/search-trim` a trim row picked from it (not also `search`);
- `narrow/filters-model` Filters Make -> Model: counted when the Model list
  closes with a changed, non-empty choice (Done, tap outside, closing
  Filters), never per checkbox tick;
- `narrow/filters-make` a Filters make NOT followed by a Filters model or
  another route; counted when the person moves on (another make, leaving the
  Cars tab, closing Filters, the page going to the background);
- `narrow/trim` the Filters Trim control set to a trim;
- `narrow/link` a `#cars=` link opened (was `car-link`, off-analytics only).
Once per device per UTC day per kind: the day each kind last counted is kept
in the browser's own storage (`ys_narrow`, never sent); memory fallback in
private mode. (The v2 rules have no per-day rule; the nearest is "a part
search once per distinct search while open", also decided on the device.)
One action, one route: a search pick or link sets the filters directly and
cancels any Filters choice in progress; the box syncing to Filters is not a
pick; the week chips and the box's clear button dispatch a tagged change so
the make select does not count them as Filters. Week chips count nothing.
A v3 event also writes a `funnel-v3` marker per (day, platform) (like
`funnel-v2`); clients may not post either marker.

**Email + JSON.** Directly under the scorecard's notes, text and HTML:
"How people narrowed the Cars list (7 days): search box 14 · Filters 9 ·
link 22 · trim filter 3", then "search box: 12 make or model, 2 trim rows ·
Filters: 6 model, 3 make only", "counting starts Nov 22: 4 of 7 days so far"
(until the first v3 day is on or before the window's first day), "website
only until the next app update" (until an app sends v3), "A person counts at
most once a day for each way." No v3 marker in the window = "no data" with
"counting starts …"; reporting but unused = 0. Per-platform lines appear only
once an app reports. `/v1/admin/scorecard` gains `narrowing` (window, since,
daysCounted, full, total, platforms, appsReporting).

**B. Sign-ups by link (migration 0016).** The sign-up request carries the
remembered `src/cmp/med`; `recap_subscribers.pending_source/_campaign/_medium`
hold it only while the address waits for its click; the click counts
`email-confirmed` under it and NULLs it in the same UPDATE. A link reused
within the hour keeps the first request's source; a new link (after the hour)
takes the new request's; an already-confirmed address stores none; the hourly
prune NULLs an expired link's source; unconfirmed rows still go at 7 days.
No source -> the empty source, as before. Per-link line now reads
"3 emails given, 2 confirmed".

**Privacy page** (dated November 13, 2026): tallies list adds "how the Cars
list was narrowed: by the search box, the filters, a car link or the trim
filter (each counted at most once a day per device)"; the Monday email
section adds the link source kept until confirmation, then deleted.
sw.js jh-v192.

**Merging triggers:** GitHub Pages (web app) and Deploy Workers
(`backend/**`): `wrangler d1 migrations apply --remote` (0016: three
`ALTER TABLE … ADD COLUMN`, nothing back-filled) then the API worker deploy.
Nothing by hand. The apps count narrowing only after the next store release
(owner's "ship").

**Tests (merged tree):** scorecard_unit 128, funnel_counters_unit 87,
recap_signup_unit 91, recap_unit 28, ops_quiet_unit 10, funnel_events_e2e 49,
car_search_e2e 47, notable_trims_e2e 40, card_share_e2e 19, tab_retap_e2e 14,
recap_ask_e2e 35, e2e-ops.sh 150 — all pass. ui_no_truncation not run (no
screen changed).

**When to decide on the box.** Counting starts the day the merge reaches
users; a full 7-day line exists 8 days later. Two weeks of numbers ≈ 15 days
after the merge.

**Suggestions.** (1) Count the week chips too if the owner wants every route
(today they count nothing). (2) `ops/README.md` still has no row for this
file. (3) Rename nothing else: `car-search` / `car-link` are gone from the
code; GoatCounter would see `narrow/*` if it is ever switched on.

## Checkout outcomes — branch `growth/checkout-outcomes`, NOT merged (2026-11-13)

Built on origin/main db015e9c (main since moved only in `ops/hub.md`).
Nothing deployed, merged, dispatched, sent or called in production. No
native file changed.

**Why.** Scorecard day one: iPhone Pro sheet 11 opens, 7 subscribe taps, 0
bought, and nothing between the tap and a purchase was counted.

**Counters (docs/app.js, EVENTS_V 3 -> 4; same anonymous daily counters).**
- `checkout-try`: a tap on Subscribe (apps) or Get Pro (web), counted only by
  v4 clients (the base for "no result recorded"; `checkout-start` still counts
  every client's taps as before).
- exactly one `checkout-end/<outcome>` per attempt: `bought`, `cancelled`,
  `pending`, `incomplete` (store answered without entitled/pending/cancelled),
  `unconfirmed` (web: back from Stripe, Pro not confirmed when the 8 polls
  gave up), `failed-<class>`. Classes: `product-unavailable`, `network`,
  `store-unavailable`, `unverified`, `store`, `not-configured` (web 503),
  `server` (web other answer), `unknown`. Never the error text; an unlisted
  name is sent as `failed-unknown`.
- `iap-product-failed/<class>` (apps): `getProduct` did not return a product
  when the Pro sheet opened (the "button keeps its baked-in price" path),
  once per open.
- Web attempts span the Stripe redirect via sessionStorage `ys_co_try` ("1"),
  cleared at the end. A tap whose end never arrives (app killed, tab closed
  at Stripe) is "no result recorded" = taps - ends.
- v4 events bump a `funnel-v4` marker per (day, platform) (client may not
  post it).

**What the plugins can tell apart today (no native change made).**
- iOS (`PurchasesPlugin.swift`): bought, cancelled, pending, "did not
  complete" (`@unknown default`), reject "Product not available.",
  "Purchase could not be verified."; every other error is StoreKit's
  localized description -> `store` (network, payments not allowed, etc. are
  NOT separable without a native change).
- Android (`PurchasesPlugin.java`): bought, cancelled, pending, incomplete;
  rejects "billing isn't available on this device" (BILLING_UNAVAILABLE /
  SERVICE_UNAVAILABLE / SERVICE_DISCONNECTED -> `store-unavailable`), "Can't
  reach Google Play" (NETWORK_ERROR -> `network`), "Product not available."
  (no offer), "Purchase failed." (no activity -> `unknown`); everything else
  (ITEM_ALREADY_OWNED, ITEM_UNAVAILABLE, DEVELOPER_ERROR, ERROR, and a
  product query that returns OK but empty) -> Play debug text or "Google
  Play billing error." -> `store`.
- Suggested (needs a store release): reject with a code
  (`call.reject(msg, "network")`) in both plugins so `store` splits.

**Email + JSON.** Item 4 of the scorecard gains, text and HTML:
"how checkout taps ended (website): of 7 checkout taps: 0 bought ·
5 cancelled · 1 failed (store product not available) · 1 no result
recorded"; per platform once an app reports; apps also "the store product
did not load on N Pro sheet opens (class n, …)"; "checkout outcomes:
counting starts <date>: N of 7 days so far"; "website only until the next
app update". No v4 marker in the window = "no data (counting starts …)".
Funnel by platform gains Checkout cancelled / pending / incomplete / failed,
Paid, not confirmed, Checkout: no result, Store price not loaded (a dash
where it cannot happen or the platform has no v4 build) and a note.
`/v1/admin/scorecard` carries `proSheet.outcomes`.

**Privacy page:** tallies list adds how a checkout ended (dated November
13, 2026; adjust if merged later). sw.js jh-v194.

**Merging triggers:** GitHub Pages (web app) and Deploy Workers (API worker;
no migration). The apps count outcomes only after a store release (owner's
"ship").

**Tests:** funnel_counters_unit, scorecard_unit 155, recap_signup_unit,
ops_quiet_unit, funnel_events_e2e 128, car_search_e2e 49,
notable_trims_e2e 40, card_share_e2e 19, e2e-ops.sh 150 — all pass.

## Free instant alert (apps) — branch `growth/free-instant-alert`, NOT merged (2026-11-16)

Owner decision 2026-11-16. Built on origin/main f9bae8c0. Nothing deployed,
merged, dispatched or released. Merging deploys the web app (Pages) and the
API worker, and the deploy applies **migration 0017** (one nullable column +
a partial index on `devices`). The apps get the control only after a store
release (owner's "ship"); deploy the worker first.

**Rule as built.** A free app install has ONE instant watch: cars matching it
within 50 mi of its centre (or its own radius if smaller) get the same
arrivals push Pro gets, on each inventory commit. Other watches, and cars
farther out, stay on the Monday summary. Default: the first watch in the
list; "Make this my instant alert" moves it (one at a time; only among the
first 5, the ones free alerts at all). Pro unchanged. Web unchanged (Monday
email). "One per phone": no accounts; one device row carries at most one
instant watch, and registration already steals a push token from any other
row (now also clearing that row's instant watch), so a reinstall that gets
the same token leaves one pushable row. A reinstall that gets a NEW token
(FCM usually does) leaves the old row with a dead token, pruned on the first
send (UNREGISTERED / 410).

**Payload.** `POST /v1/device/register` `watches[]`: the chosen entry carries
`instant: true`. Server (`sanitizeWatches`) keeps the first flagged KEPT
watch of a free device, clamps `radius_mi` to `FREE_INSTANT_RADIUS_MI` (50),
stores it in `devices.instant_watch_json`; every re-registration rewrites it
(no flag = NULL = today's behaviour; Pro = NULL). The response adds
`instant: {make, model, radiusMi}` only when one was kept.

**Dispatch.** `dispatchDeviceAlerts`: Pro first; then free devices with an
instant watch, longest-unpushed first, from what Pro left of
`MAX_SENDS_PER_COMMIT` (25). Same payload, `device_alerts_sent` dedupe and
token pruning. A budget cut marks nothing sent, so the Monday summary still
lists the car. Counter `free-instant:ok` (ops_counters).

**Monday summary / check-in.** For a device with an instant watch, the one
Pro line becomes "<N of these are | Both are | This one is> outside your
instant alert (Volvo 240, 50 mi); Pro pushes every watch at any distance."
counting only cars the instant watch certainly does not cover; if none, the
old line. The first-watch check-in says "Your instant alert is <watch>
within 50 mi; the rest come in the Monday recap. Pro pushes every watch."
Devices without the flag: unchanged text.

**Ops daily report.** Under SENDS: "of the app pushes, free instant alerts:
N" (24 h); kept out of the per-channel rows.

**App.** `docs/app.js` FREE INSTANT ALERT block: `ys_instant_watch` = the
chosen watch's `addedAt` (stored watches never edited); badge "Instant
alert, within 50 mi" (`badge badge-new`), link-button on the others. Near-
miss lines and the card recap line no longer claim "Pro would have / your
recap" for cars inside the instant scope. Copy changed: Alerts intro (web
and native), native push panel, its Pro box, web app-store panel,
`PRO_PUSH_LINE`, `watchGateLead` (native variant), native Pro sheet intro and
alerts bullet, native free watch toast line, "Push is on" status, privacy
page (flag listed; date Nov 16). sw.js jh-v199. No funnel event added.

**Store listings to fix (hub):** `fastlane/metadata/en-US/description.txt`
and `android/en-US/full_description.txt` line 24 ("Free watches get a
weekly recap push…") and line 28 (Pro "a push within hours…" reads as
Pro-only); `android/en-US/pro_subscription_benefits.txt` line 1 ("Alerts
within hours when a car lands").

**Tests (all pass):** e2e-devices.sh 74 (new: old build no push; flag inside
50 / none at 80 mi; 25 mi radius kept; two flags keep the first; Pro ignores
flag; move + drop flag; 25 Pro devices use the budget and the free car lands
in Monday; token moved = one push; ops count), e2e-coverage 27, e2e-ops 151,
free_instant_e2e 30, ui_no_truncation (alerts, alerts-hits, alerts-instant
new, r5-alerts-recap, pro-sheet; 6 widths, light/dark, 1x/2x) 120 checks 0
failures, alerts_first_unit 13 (3 new), pf_guards_unit, funnel_events_e2e
128, tab_retap_e2e 14, share_watch_e2e 33, notable_trims_e2e 40,
recap_ask_e2e 35, pro_sheet_fold_e2e 188, app_promo_e2e 174, and every
*_unit.mjs. e2e.sh: 38 pass, 1 fail ("radius filter did not narrow"), the
same failure on untouched origin/main, so pre-existing.

**Left.** Store listings (above). The web Pro sheet text still says "Free
gets a Monday recap instead" (true for the web). `freeDeliveryNote()` (in the
first-view builder's strip) is unchanged and still true, but does not
mention the instant watch.

## No zip gate on the first visit — branch `growth/no-gate`, NOT merged (2026-11-16)

Owner: "make it as intuitive as possible", "Do it and ship". Built on
origin/main 004eeda0. Nothing merged, deployed, dispatched or released; no
file in `ios/`, `android/`, `native/`, `fastlane/`, `scraper/`. Merging
deploys the web app (Pages), the site Worker (yardscout.io pages) and the API
worker (attribution, ops email, scorecard; no migration). The apps get the
app half only with a store release (owner's "ship").

**1. A first visit shows cars.** With no saved place (no zip, no GPS, not
Pro "browse nationwide") the app asks `/geo` once per page load
(`DATA_BASE + 'geo'`, gives up after 2.5 s). Ok: the Cars list around that
point at the default radius, with a line above it: "Showing yards near
**Sacramento, CA**. That is a guess from your internet connection." + zip
field, "Show me", "Use my location" (no city: "near your internet
connection's location. That is a guess."). Not ok, failing, slow or abroad:
today's zip card, unchanged. While the answer is on its way the list shows
its loading state (no flash of the zip prompt).
- Rules (app.js block "A PLACE FOR THIS VISIT ONLY"): the guess lives in
  `_tempPlace` + `activeZipCoords` for the page only; never written to
  `jh_zip`, `jh_zip_coords`, `jh_gps`. **Helper for the strip:
  `locationIsGuess()`** (true while a guess or a link's place is on screen
  for someone with nothing saved). Also `ownCenter()` (the visitor's own
  zip/GPS centre, never a guess) and `needOwnZip()`. `addQuickWatch` answers
  'no-zip' while `locationIsGuess()` (Pro too), so `askZipForWatch` runs;
  watch centres in `addQuickWatch`, `addWatchItem`, `syncWatchToServer`
  (legacy), `deviceSyncWatches`, `inInstantScope`, the Alerts watch card and
  `recapNoteNewWatch` read `ownCenter()`. A zip (any field) or GPS replaces
  the guess for good (`placeReplaced`).
- The radius loader and the yard filter read `activeZipCoords` as before, so
  they work from the guess unchanged. The zip chip hides while the line shows.
  The Parts tab's "Searching within 100 mi of …" says "Sacramento, CA (a guess)".
- **Counters** (no new counting-rules version; same anonymous +1):
  `first-view-guess` once per visit (sessionStorage) when the list opens on
  a guess, and `guess-replaced` once per visit when a zip or GPS then
  replaces it. Decision: two names, not one, because "Entered a zip" also
  counts people who saw the zip card, so it cannot say how many corrected a
  guess. API: both in `attribution.js` FUNNEL; daily email funnel rows "Saw
  cars from a guess" / "Entered a zip" / "Guess then corrected". iOS/Android
  columns stay 0 until a store release.
- Privacy page (`#first-view`): what is read (the city the connection
  appears to come from, as Cloudflare reports it), used for that one answer,
  not stored or logged by us, kept only while the page is open, never a watch
  or Monday-email centre, replaced by a zip; the tallies list and "What the
  app fetches" say the same.

**2. Zip card names the car** when it shows and the page came with a cars
link: "Find a Nissan Xterra near you" / "Enter your zip or postal code and
we'll list every Nissan Xterra in the self-service yards near you." (make
only when no model; "an" before A/E/I/O; an all-lowercase link word is
capitalised). Without a cars link: unchanged.

**3. Links that carry a place** (parsed beside `#cars=`, combine with it as
`#yard=…&cars=…`): `#yard=<name as in the data>` centres on the yard's
coordinates from the inventory manifest (else the loaded inventory) and sets
the Yard filter; `#near=<lat>,<lng>,<label>` (US/Canada bounds, label plain
text ≤ 40). Line: "Showing yards near <label> (from the page you came
from)." Same rules as a guess. A visitor with a saved zip or GPS keeps it:
the link's place is for this visit, the line offers "Back to <zip>" ("Back to
my location" for GPS), and their watches keep their own centre. An unknown
yard or a bad `#near=`: ignored (zip card / own place). No `/geo` call when
a link carries a place.

**4. Search pages' buttons** (`backend/site-proxy/src/share.js`): yard page
"Search this yard" → `#yard=`; state and city pages → `#near=` at a point
among their yards (`pointAmongYards`: the yard with most of the group within
100 mi; a metro alias page uses its own point), labelled "See the cars in
Dallas" / "See the cars in Texas yards" / "See the cars near Seattle"; make
page's second button → `#cars=<Make>` ("See every Ford near you"); model
pages keep `#cars=`/`#watch=`. Every button into the app, and the header's
"Open the app", carries `?utm_source=page&utm_medium=<yard|city|state|model|
make|landed|prices|yards|car>&utm_campaign=<slug>` and `rel="nofollow"`;
`docs/robots.txt` adds `Disallow: /?utm_source=`. The /junkyards hub uses
medium `state`, campaign `all`; a gone car uses `car`/`gone`. App side:
`ATTRIB` keeps a remembered outside source when the new one is `page`
(`attribKeepsStored`), tags still stripped from the address bar.

**5. Scorecard** per-link line: "30 visits → 12 entered a zip → 4 watches →
…" (`zip-entered` added to the scorecard's events; tagged zips only).

sw.js `jh-v201` (hub re-bumps at merge).

**Tests (final tree, all pass):** no_gate_e2e 76, ui_no_truncation (home,
results, place-guess, place-link, place-link-saved, zip-card-car at 320/360/
390/1280, light/dark, 100/200%) 96 checks 0 failures, site units redirects 52,
model_pages 60, junkyards 236, prices 39, geo 13; car_search_e2e 48,
coverage_gaps 26, funnel_events 128, tab_retap 14 (one run failed 309 vs 300
while eight browser tests ran beside it; passed twice alone), free_instant 30,
recap_ask 35, share_watch 33, pf_guards 167, scorecard_unit 155,
funnel_counters_unit, e2e.sh 39, e2e-ops.sh ALL PASS, alert_freshness 15,
browser_e2e 17, app_promo 174, card_share 24, model_years 18, notable_trims
40, photo_layout 584, pro_sheet_fold 188, map_regions, no_pick_models,
pf_new_cats.
New `backend/test/no_gate_e2e.mjs` (the real bundle served as yardscout.io,
beacons caught; `NOGATE_SHOTS=<dir>` writes 390 px light/dark shots);
`ui_no_truncation.mjs` screens `place-guess`, `place-link`,
`place-link-saved`, `zip-card-car`; site units (junkyards_unit sweeps 13
rendered pages for tagged nofollow buttons + robots); `ops_e2e.mjs`
(attribution columns, email rows); `scorecard_unit`; `funnel_counters_unit`
harness gained stubs for the new names `setZipCenter` uses.

**For the hub at merge (other workstream's code, not edited here):**
- Car screen (`renderCarDetail`): "N mi from <zip>" reads `jh_zip`; while a
  link's place is on screen for someone with a saved zip, the distance is
  from the link's place but labelled with their zip. One-word fix there:
  `zip && !_tempPlace`.
- `#live-stats-bar` says "Cars near you" and the header "N yards in your
  range" under a guess; the line above says it is a guess. The strip
  (`watchStripHtml`) should use `locationIsGuess()` if it wants to word the
  offer differently ("enter your zip to watch").

**Seen, not changed.** The Yards tab and its map centre on a guess too, with
no line saying so (the Cars line is the only label). iPhone/Android "Open in
YardScout" and the header button are rewritten to app paths by the page's
script, so the utm tag only rides on desktop and as the Android browser
fallback. Car links on yard and city pages (`/yard/…` newest arrivals, city
"Newest arrivals") have no `rel="nofollow"` (model and make pages do);
`/car/` is disallowed in robots.txt either way. The stores line's "web
version" link and the logo are left untagged (links, not buttons).

**Suggestions.** (1) Count the line's "Use my location" separately from a
typed zip if the owner wants to know which correction people use. (2) Put
the same guess line on the Yards tab. (3) A "Not here?" link on the stats
bar for a guess, once the Cars-feed work settles.
## Note from design/cars-feed (2026-11-16): counting rules v5, for this workstream

The Cars feed branch (`design/cars-feed`, not merged) bumped `EVENTS_V` to
5 in docs/app.js and added the `funnel-v5` marker in
`backend/src/attribution.js` (with a recap_signup_unit check). Two changes
the scorecard does not read yet (backend/src/scorecard.js is this
workstream's file, so it was left alone):
- a new narrowing kind `narrow/chip` (a make or model chip above the Cars
  grid, once per device per UTC day, like the others). `NARROW_EVENTS` and
  the "How people narrowed the Cars list" block need a "chips" route, with
  "counting starts" from the first `funnel-v5` day;
- `email-asked` now also counts the Monday-email field in the Cars watch
  strip (once per visit), not only the one in the watch toast. Asked can
  rise without more watches from the day v5 reaches users; the scorecard
  could note "since <first funnel-v5 day> asked includes the Cars strip".
Privacy page already updated on that branch (chip tally, the strip).

## Free emailed alert (website) — branch `growth/free-email-alert`, NOT merged (2026-11-17)

Owner decision 2026-11-17 ("do the free emailed alert"). Built on origin/main
6f6e545d. Nothing deployed, merged, dispatched or released; no file in
`ios/`, `android/`, `native/`, `fastlane/`, `scraper/`; no price or
entitlement rule changed. Merging deploys the web app (Pages) and the API
worker, and the deploy applies **migration 0018** (two new tables, nothing
existing altered).

**Rule as built.** On the website a free visitor (not Pro, never in the app
shells) gets ONE emailed alert: one of their watches, one email address, cars
set out within 50 mi of that watch's centre (or its own radius if smaller),
no account. It is the web counterpart of the apps' free instant push and
uses the same distance constant. Pro is unchanged: every watch, any
distance. The Monday email is unchanged and separate (own tables, own
unsubscribe link).

**What the visitor sees** (`docs/app.js` block FREE EMAILED ALERT ON THE
WEB; card `#free-alert` in `docs/index.html`; styles at the end of
`docs/styles.css`). A card under the watchlist in Alerts, above the matches:
- *Ask:* "Free email alert. Pick one car and we email you when one is set
  out within 50 mi, usually the same day. One car, one address, no account."
  Then their watches as rows to pick from (only when there is more than one;
  only the first 5, the ones free alerts at all; rows, not a drop-down,
  because a drop-down cut a long name off at 320 px with large text), an
  email field, "Email me", and "Free emails share a small daily sending
  limit, so one can arrive late or be skipped." With one watch the car is
  named ("For Toyota 4Runner") and the line starts "Get an email when…". No
  watch yet: no card.
- *Waiting:* "Check your inbox. Tap the link we sent to v•••@example.com to
  turn on your email alert for (car). Nothing is sent until you do." and
  "Use a different address or car". Goes back to the ask after 7 days.
- *On:* "Free email alert is on. (car), within N mi, to v•••@example.com. At
  most one email per scan, usually the same day a car is listed." with
  "Change car" (the other watches as rows, Save / Cancel; one request, no
  new confirmation email) and "Turn off". The watch it stands for wears a mark in the list
  ("Email alert, within N mi"). If that watch is removed from the list, the
  card says the alert keeps running until changed or turned off.
- The confirmation button lands on `/#falert=confirmed&sub=(token)`: Alerts
  opens, toast "Your free email alert is on."
- One sentence is added after `#alerts-intro-copy` by app.js (element
  `#alerts-free-email-copy`, free web visitors only): "On this website, free
  gets one watch emailed: pick it under your watchlist and we email you when
  one is set out within 50 mi." The two sentences the hub owns
  (`#alerts-intro-copy`, `#appstore-alerts-panel`) and the check in
  `free_instant_e2e.mjs` are not touched, and `index.html` has no change next
  to them, so the hub's rewording merges without a conflict.
- No Pro prompt in the card. The existing "Email alerts (Pro)" panel further
  down is as it was (its one "See Pro" button for a free visitor).
- Rule 6: stored watches are never edited, moved or reordered. The browser
  keeps its own key `ys_falert` (address, state, token, which watch, label,
  miles); the server keeps its own COPY of the one watch's free criteria
  (make, model, years, centre rounded to about 1 km, radius at most 50; no
  trim, drive or "parts only"). A watch with no centre of its own (made
  before the radius picker) is sent centred on the visitor's zip; the stored
  watch is not changed.

**Server** (`backend/src/free_email_alert.js`, migration
`0018_free_email_alert.sql`). It reuses the Monday email's machinery from
`recap_signup.js` (helpers exported there, no behaviour change): the
confirmation-token scheme, the signed browser token, masked addresses in
logs, the same limits.
- `POST /v1/free-alert/signup`: stores the address and the copy as PENDING
  and sends ONE confirmation email ("Confirm your free YardScout email
  alert", from `EMAIL_FROM`). The reply never says whether the address
  already has an alert. With the token a browser holds after a confirmation
  click for the same address (this alert's or the Monday email's) the watch
  is set at once and no email goes out.
- `GET /v1/free-alert/confirm` is a page with a button that names the car
  (mail scanners cannot opt anyone in); `POST` confirms: the pending copy
  becomes THE watch for the address (a different car replaces the old one,
  and only after its own click), then 303 to the app with the token.
- `POST /v1/free-alert/status`, `POST /v1/free-alert/off` (the page's "Turn
  off": deletes the address).
- `GET|POST /v1/free-alert/unsubscribe` (signed, one click, RFC 8058):
  DELETES the address, its watch and its dedupe rows.
- Alerts are for FUTURE arrivals: when a watch is set, the cars already
  listed are recorded as known (as the Pro email alerts do).
- An address whose Pro email alerts are on (and Pro active) is left to the
  Pro email: never two emails for one car.

**Sending** (`dispatchFreeEmailAlerts`, called from `admin.js` handleCommit).
It starts only after that commit's Pro email dispatch has finished, and runs
on every commit (also one with no new cars, so held alerts can go out). At
most ONE email per address per scan, deduped per (address, car) in
`free_email_alerts_sent`. From `EMAIL_ALERTS_FROM`, with the signed
unsubscribe link in the body and `List-Unsubscribe` +
`List-Unsubscribe-Post` headers, as the Pro emails. Copy says "usually the
same day", never "instant". One Pro line, no price. Up to 10 cars listed
per email, "…and N more on the site" for the rest (all marked sent).

**Every limit, and where it lives.**

| Limit | Value | Where |
|---|---|---|
| Distance | 50 mi, or the watch's own radius if smaller | `FREE_ALERT_RADIUS_MI` = `FREE_INSTANT_RADIUS_MI` (`devices.js`), imported in `free_email_alert.js`; `FREE_EMAIL_ALERT_RADIUS_MI` in `docs/app.js` (a test holds them equal) |
| Watches | 1 per address (primary key = address, one `watch_json`); 1 alert per browser (`ys_falert`) | migration 0018; `docs/app.js` |
| Which watches can carry it | the first 5 | `FREE_WATCH_LIMIT`, `falertChoices` in `docs/app.js` |
| Free alert emails per scan | 5 | `FREE_ALERT_MAX_PER_SCAN`, `free_email_alert.js` |
| Free alert emails per UTC day | 20 (20% of the daily cap) | `FREE_ALERT_DAY_SHARE`, `ops.js` |
| Reserve under all other mail | none once 70 emails of any kind went out today (30% of the cap kept back; always more than the 10 kept for confirmations and recaps) | `FREE_ALERT_RESERVE_SHARE`, `freeAlertBudget`, `ops.js` |
| Retry of a held alert | later scans, for 48 h, then not sent | `FREE_ALERT_CATCHUP_MS`, `free_email_alert.js` |
| Confirmation link | 7 days; a second ask within 1 h rides the link already sent | `CONFIRM_TTL_MS`, `CONFIRM_REUSE_MS`, `recap_signup.js` |
| Confirmation emails | 3 a day per address; refused ("try tomorrow") while fewer than 10 sends are left today | `CONFIRMS_PER_DAY`, `optionalEmailAllowed` |
| Sign-ups per network | 8 an hour per IP, one bucket shared with the Monday email sign-up; 32 an hour for token changes | `IP_SIGNUPS_PER_HOUR` |
| Unconfirmed address | deleted 7 days after the last ask (hourly job) | `pruneFreeAlerts` |
| Dedupe rows | 90 days | `pruneFreeAlerts` |

The daily cap is the Resend free tier's 100 (`RESEND_DAILY_CAP`; the env
variable overrides it). The two shares follow it if the plan changes.

**The budget, plainly.** Free alert emails are the lowest class of mail. The
daily ops email, sign-in links, Pro alerts, saved-car emails, confirmations
and the Monday recap all still have room after free alerts have stopped. A
matched alert the budget cannot carry is HELD: counted
(`email:free-alert:held`, once per held stretch), not marked sent, flagged
on its row (`held_at`), and retried on later scans (longest-waiting first)
for 48 h. After that the car is not emailed. A send Resend refuses is
counted as a failure and not retried. If the send counters cannot be read,
nothing is sent (held). The page, the confirmation email and the privacy
page all say an email "can arrive late or be skipped".

**Cost per scan** (the commit's dispatchers share one small budget): nobody
signed up, or nobody matched = 1 D1 statement. Otherwise 3, plus 1 per email
sent, plus 1 when something is held, plus 1 read while a held alert is
waiting; at most 5 calls to Resend. A latitude/longitude box runs before the
exact match rule, so a nationwide scan costs little per address.

**Counting** (no counting-rules version step; counting starts on the deploy
day). The app sends `free-alert-shown` (the ask on screen, once a visit) and
`free-alert-asked` (an address given; a car change is not counted). The API
counts `free-alert-confirmed` (the click, under the link the sign-up came
from, once per address) and `free-alert-first-email` (the first alert email
an address is sent); a client cannot post those two. All four are in
`/v1/admin/attribution` and in the daily email's funnel table ("Free alert
offered / asked / confirmed / 1st email", web only). The daily email also
has, under USAGE, "Free email alert (web): N addresses with an alert on · K
waiting for the confirmation click · M emailed at least once"; under SENDS,
the `email:free-alert` row and, when anything was held, "HELD BACK for the
free-alert email budget (24 h): N free alert emails (lowest class of mail;
retried on later scans for 48 h, then not sent)".

**Privacy page** (`docs/privacy.html`, dated November 17, 2026). New section
"The free email alert (website)": what is stored (the address, the copy of
the one watch, dates, the link source until the click, the list of cars
already emailed), one watch per address, how to remove it (the unsubscribe
link in every email, "Turn off" in Alerts, or writing to us; each deletes
the address, the watch and the list), what the browser keeps, and that an
email can be late or not sent. The location and watchlist paragraphs name it
as the third opt-in exception; the tallies list has the four events.

**Deploy order.** One push to main is enough. "Deploy Workers" applies
migration 0018 and then deploys the API; Pages publishes the web app on its
own. If Pages is first by a minute, the card answers "We could not reach
our server… try again in a minute" until the API is up (a 404 is treated as
unreachable); nothing is lost. No new secret or variable.
`EMAIL_UNSUB_SECRET` must be set in production (it already signs the Pro
and Monday links); without it a sign-up answers 503. sw.js `jh-v205` (hub
renumbers at merge).

**Not done.**
- The watch toast still offers the Monday email after a new watch and does
  not mention the alert. The alert is found in the Alerts tab only.
- The weekly scorecard does not read the four events.
- A browser that is "waiting" cannot tell that the link was opened on
  another device; it shows "check your inbox" until the visitor starts over
  or 7 days pass. The alert itself works.
- No count of alerts dropped after the 48 h (only "held").
- A Pro member who had a free alert keeps getting it unless their Pro email
  alerts are on for the same address; the card is hidden for Pro, so they
  stop it with the unsubscribe link.
- "Parts only" on a watch is a display filter in the browser; the emailed
  alert covers every matching car.
- No postal address line unless `EMAIL_POSTAL_ADDRESS` is set (as for the
  Monday email; still empty).

**Decisions taken here that the owner may want to change.** (1) 5 per scan,
20 a day, stop at 70. (2) Held alerts retry for 48 h. (3) The card sits
under the watchlist, not in "How alerts reach you" at the bottom of the tab.
(4) An address already confirmed for the Monday email in the same browser
needs no second confirmation email. (5) The alert and the Monday email
unsubscribe separately. (6) One Pro line in the alert email, with a link, no
price. (7) Subjects: "New: 2004 Toyota Tacoma at (yard)" for one car, "3
new: Toyota Tacoma within 50 mi" for several.

**Tests (final tree; server, wrangler and browser runs each behind the
shared lock).** New: `free_email_alert_unit.mjs` 141 (real handlers on SQLite
with every migration: limits, opt-in, dedupe, budget, held and retried,
removal, the commit hook order, statements per scan, logs),
`free_email_alert_client_unit.mjs` 42 (the page's pure rules against the
server's; app.js parses), `free_email_alert_ui_e2e.mjs` 79 (free web visitor
through every state, Pro unchanged, both app shells hidden, rule 6 byte for
byte), `e2e-email.sh` phase 3 = `free_email_alert_e2e.mjs` 53 (wrangler +
mock Resend: sign-up, confirm, real scan commits, one email, per-scan and
per-day limits, ops email lines, unsubscribe). `ui_no_truncation.mjs`
gained 8 screens (`alerts-falert-ask`, `-ask-one`, `-ask-cap`, `-pending`,
`-on`, `-change`, `-on-gone`, `-off`); run for those plus `alerts`,
`alerts-hits`, `alerts-instant` at 320 / 390 / 768 / 1280, light and dark,
100% and 200%: 176 checks, 0 failures.
Existing, all pass: `e2e-email.sh` 118 in all (phases 1 and 2 unchanged),
`e2e.sh` 39, `e2e-devices.sh` 74, `e2e-ops.sh` 154, `free_instant_e2e` 30,
`funnel_events_e2e` 128, `recap_ask_e2e` 35, `share_watch_e2e` 33,
`tab_retap_e2e` 15, `cars_feed_e2e` 117, `no_gate_e2e` 78, and all 22
`*_unit.mjs`.
Not run: the full `ui_no_truncation` (only the screens above, as the hub
asked), `e2e-coverage.sh`, the other browser suites (pro sheet, app promo,
trims, photos, car search, card share, part finder, the `.py` ones) and the
site-proxy units; none of their files were touched.
What the tests caught on the way, now fixed: the first card used a
drop-down, which cut "Mercedes-Benz" at 320 px with 200% text (also on the
existing `alerts-instant` screen), and its "Use a different address or car"
link was 4.22:1 on the card's tint; the cars are rows now and that is a
plain button. The server e2e once died on a closed keep-alive socket to the
local mock (the test's own request, fixed in the test). One browser check
read the watchlist before the scan had filled it (the test now waits).

**Seen, not fixed.**
- A typed address is wider than a phone's field at 200% text (19 characters
  need 336 px, the field has 226). The field scrolls, as every one-line
  field does, and the Monday-email field is the same; no screen in the
  layout check holds a whole address in a field.
- A watch with the email alert on still shows the near-miss line with its
  Pro box ("Would have sent a push within hours") for cars the free email
  may already have covered. The apps leave that line out for the instant
  watch's own nearby cars (`inInstantScope`); the web does not know when the
  alert was set. Other workstream's block (`renderAlerts` near-miss).
- `alerts.js` says "free plan: 50/req" for the commit's subrequest budget.
  Web push (35), device pushes (25), Pro emails (20) and the rest already
  add up past 50 on a busy commit; this adds at most 5 emails and about 10
  statements. If that limit is hit, later sends in the commit fail,
  whichever dispatcher they belong to. Worth a look at the plan's real limit.
- `/v1/recap/add` and `/v1/recap/signup` share one per-IP bucket with
  different limits, so adds use up the sign-up allowance.
- The hourly check's "Resend near daily cap" text names only confirmations
  and recaps as held; free alerts now stop earlier (at 70).

**Suggestions.** (1) Offer the alert in the watch toast instead of, or
beside, the Monday email: it is the stronger free promise and today it is
only found by opening Alerts. (2) Add the four events to the weekly
scorecard as one line (offered, asked, confirmed, first email). (3) If free
alerts are held on most days, a paid Resend plan lifts every limit here by
setting `RESEND_DAILY_CAP`. (4) Count alerts dropped after 48 h, so "held"
and "never sent" can be told apart.

## Watertight — branch `hub/watertight-1117`, NOT merged (2026-11-17)

Hub brief of 2026-11-17 (owner: "I want everything large done ... watertight
features"). Built on origin/main 56f108c5. Nothing deployed, merged,
dispatched or released; no file in `scraper/`, `fastlane/`, `ios/`,
`android/`; no price or entitlement rule changed; no migration. One commit
per item; items 5 to 7 (test scripts, the regression runner, the eBay
workflow) are in the builder's report to the hub, not here.

### 1. The commit budget: alerts cannot fail unseen on a busy scan

**What was wrong.** `handleCommit` started every dispatcher at once, each
with a private cap on *sends*: web push 35, app push 25, Pro email 20,
saved-car 20, sale pushes 35 + 25, check-ins 20, free email 5, the owner's
coverage digest 1. That is up to 186 sends in one Worker invocation, and an
FCM push can cost 2 to 4 calls (token request, retry). The new test's
worst-case load made **162 outside calls, up to 5 at once**, on the old
tree. Past the platform limit a send simply fails, whichever dispatcher it
belongs to, and nothing recorded which.

**The documented limits (Workers Free).** Read 2026-11-17. NOTE: this
session could not open developers.cloudflare.com itself (the host is not in
its allowed network); the figures below are what the search tool returned
from these pages, quoted as returned. Worth one look by a person.
- Outside calls: "50 subrequests per invocation" on Free (10,000 on Paid,
  configurable to 10 million). Every `fetch()` counts, and "each subrequest
  in a redirect chain counts against this limit".
  <https://developers.cloudflare.com/workers/platform/limits/> (page dated
  2026-07-28 by the search result)
- Cloudflare's own services (D1, KV): "Workers on the free plan remain
  limited to 50 external subrequests and 1000 subrequests to Cloudflare
  services per invocation."
  <https://developers.cloudflare.com/changelog/post/2026-02-11-subrequests-limit/>
  (the Workflows limits page repeats 50 / 1,000:
  <https://developers.cloudflare.com/workflows/reference/limits/>)
- D1's own page gives a different number: "Queries per Worker invocation
  (read subrequest limits): 1000 (Workers Paid) / 50 (Free)", and says a
  `batch()` counts as one. <https://developers.cloudflare.com/d1/platform/limits/>
  **The two pages disagree for D1 on Free (1,000 or 50).** See "The open
  question" below.
- `ctx.waitUntil` work may run "for up to 30 seconds" after the response.
  At most six connections wait for response headers at once. CPU time on
  Free is 10 ms per request (same limits page).
- Not a per-commit limit, but new: D1 Free's daily row limits are enforced
  since 2026-09-01 (queries fail past them).
  <https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/>

**What is built** (`backend/src/commit_budget.js`, the runner
`runCommitDispatch` in `admin.js`).
- ONE budget per commit: **45 outside calls** (limit 50), **900 D1 + KV
  calls** (limit 1,000; plus the one counter write at the end), and no new
  send or step starts **25 s** after the commit began (limit 30 s).
- It holds by construction, not by counting sends: every outside call in
  the commit path goes through `meteredFetch` (APNs, FCM and its token
  request, web push, Resend) and every D1 / KV call through a metered `env`;
  both count before the call and refuse at the ceiling. A test fails if any
  file in the commit path has a bare `fetch(`.
- The dispatchers run **one after another, in priority order**:
  1. Pro web push (email fallback) 2. Pro app push 3. Pro email alerts
  4. saved-car alerts (Pro) 5. sale-day pushes (Pro) 6. storing the arrivals
  for the Monday recap (no outside call) 7. the owner's coverage digest
  8. free instant push 9. first-watch check-ins 10. free emailed alert.
  The order of sacrifice is the reverse: the free emailed alert loses first.
  Once any step is carried for lack of outside calls, no later step sends in
  that commit (a cheap free send cannot slip past a carried Pro one).
- Before each send a dispatcher asks for room for the send AND the write
  that records it, so it stops between recipients, never between a send and
  its "sent" row.
- **Carried, never dropped.** A recipient that was not served has no "sent"
  row, and every scan carries the last 3 days of arrivals
  (`push_inventory.py`, `ARRIVAL_WINDOW_DAYS`), so the next scan finds the
  same cars. Recipients are now taken longest-unserved first (Pro web users
  by their last alert, devices by `last_push_at`, Pro email by
  `last_email_at`), so whoever was cut leads the next scan. A carried free
  emailed alert is flagged `held_at` as before and keeps its 48 h catch-up.
- **Counted.** Per step, in `ops_counters`: `commit:<step>:held` (had
  something to send, not served) and `commit-unchecked:<step>:held` (never
  looked at), plus the day's busiest commit (`commit:ext:max`,
  `commit:svc:max`). The daily ops email gains, under SENDS: "Busiest scan
  since yesterday (UTC): N of 45 outside calls, M of 900 database calls" and,
  when anything was carried, "CARRIED TO THE NEXT SCAN by the per-scan call
  budget (24 h): ..." per step. Carried **Pro** alerts are also an open
  issue in the verdict line ("N Pro alerts were carried to a later scan").
  Each commit logs one line: `commit budget: outside calls 12/45, ...`.
- Private Pro caps (35 / 25 / 20 / 20) no longer apply inside a commit (the
  shared budget is the limit; otherwise a Pro user could be carried by a cap
  while a free send went out). They still apply on the admin test routes.
  The free tier's own limits are unchanged: 5 free alert emails a scan,
  20 check-ins a scan, the Resend shares.
- D1 round trips cut: the per-car "already sent?" reads and "sent" writes of
  web push, app push, Pro email and the Monday pushes go as D1 batches (one
  round trip per 100 cars instead of one per car); orphan shard deletes too.
- Outside a commit (admin routes, Monday cron) there is no budget and
  nothing changes.

**Worst-case arithmetic** (test `commit_budget_unit.mjs`, counted at the
network stub and the D1 shim, not by the code under test). Load: 60 Pro web
users, 40 Pro devices, 30 Pro email members, 30 free instant devices, 20
check-ins due, 10 free alert addresses, a sale, a coverage request, 4,000
arrivals (the scraper's cap).

| | outside calls | D1 + KV calls |
|---|---|---|
| limit (Workers Free) | 50 | 1,000 (D1's page: 50) |
| old tree, same load | **162** | not the problem measured |
| new: worst case | **45** | 364 (Pro web 153, Pro app 41, Pro email 62, arrivals store 51, free instant 31, rest 26) |
| new: busy scan (10 + 10 + 5 Pro, 30 free instant) | 45 | 146 |
| new: quiet scan | 0 | 21 |

Capacity that follows: 45 pushes or emails per scan, about 270 a day at six
scans. The worst case above (262 sends owed) cleared in 7 scans, everyone
reached exactly once. Today's real load is about 10 Pro devices.

**Promises.** None changed. Pro: every watch, pushed within hours, first in
line. Free instant and the free emailed alert already said "from what Pro
left" / "can arrive late or be skipped". What IS new and should be known: if
Pro alone ever needs more than 45 sends in one scan, the rest arrive one
scan (about 4 h) later and the free tier gets nothing that scan; a car
carried for more than 3 days (the arrivals window) is lost. Both show in the
daily email long before that. The paid Workers plan ($5/mo) lifts it.

**The open question (stopped here, on purpose).** If D1 really allows only
50 queries per invocation on Free (its own page), no arrangement inside one
invocation is enough: storing 4,000 arrivals alone takes 51 batches today
(and did before this change), and the fixed reads of ten dispatchers come to
about 45. Staying inside *that* reading means splitting the commit across
invocations (the scan calling one endpoint per dispatcher, or an outbox the
hourly cron drains), which touches `scraper/push_inventory.py` or needs a
migration. Not done; it needs the hub's call. **One check settles which page
is right:** `wrangler tail` (or the Workers logs) on the next scan commit.
`arrivals stored: 4000` together with the new `commit budget:` line means D1
calls are not capped at 50. A line `... failed: Too many API requests` (or a
missing `arrivals stored`) means they are, and then alerts have been failing
unseen on busy scans for some time.

**Tests.** `backend/test/commit_budget_unit.mjs`: 73 checks, all pass (the
limits under the worst case; order of sacrifice; counted and shown; nothing
marked sent for the unserved; carry-over until everyone is reached once; the
deadline; the backstop at the network; no bare `fetch(`). Against the old
sources (`YS_SRC=<old src> node test/commit_budget_unit.mjs`) it fails at
once: "outside calls stay under the platform's 50 a commit: made 162",
"one outside call at a time: up to 5 at once". All other `*_unit.mjs` pass.
`e2e-devices.sh` runs one commit with the ceiling lowered to 25 (dev-only
`COMMIT_EXT_CEILING_TEST`, ignored unless `DEV_MODE=1`) for its existing
"Pro first when the budget is tight" check.

**Decisions here the owner may want to change.** (1) Order among Pro: web
push, then app push, then Pro email, then saved cars, then sale pushes (the
order they ran in before). Most paying members are on the apps; putting app
push first is one line. (2) The owner's coverage digest goes before the free
tier. (3) Ceilings 45 / 900 / 25 s. (4) Carried Pro alerts are an open issue
in the daily email but do NOT raise an hourly "[YardScout alert]".

**Not done / known limits.** Saved-car and sale pushes are not rotated
(same owners first each scan; both re-evaluate every commit). No count of
alerts lost after 3 days of carry-over. The 10 ms CPU limit is not measured
or guarded here (see the report to the hub). The saved-car step was not in
the worst-case load (it needs inventory shards); it goes through the same
meter.

## Watertight, continued — branch `hub/watertight-1117`, NOT merged (2026-11-18)

Second builder on the hub's brief (the first stopped at a usage limit after
items 1 and 7). Same base, same rules: nothing deployed, merged, dispatched
or released; no file in `scraper/`, `fastlane/`, `ios/`, `android/`,
`backend/src/inventory.js`, `backend/src/jsonpick.js`; no price or
entitlement rule changed; no migration. Items 5 and 6 are in the report to
the hub.

### 1. The commit budget: review

**Re-run.** `commit_budget_unit.mjs` 73 of 73 on the branch; against the
sources before the change (`YS_SRC=<56f108c5 src>`) it fails at once ("made
162", "up to 5 at once"), so the test does fail without the fix. All 23
`*_unit.mjs` pass. `e2e-devices.sh` passes (its "tight budget" checks
included).

**The limits, checked again (2026-11-18).** developers.cloudflare.com is not
reachable from this session either; these are from search results quoting
the pages, the same as the first builder's.
- Workers limits page and the 2026-02-11 changelog: Free = **50 outside
  subrequests and 1,000 subrequests to Cloudflare services (D1, KV) per
  invocation**; Paid = 10,000 (raisable to 10 million).
  <https://developers.cloudflare.com/workers/platform/limits/>,
  <https://developers.cloudflare.com/changelog/post/2026-02-11-subrequests-limit/>
- D1 limits page: "Queries per Worker invocation (read subrequest limits):
  1000 (Workers Paid) / 50 (Free)", pointing at the Workers page.
  <https://developers.cloudflare.com/d1/platform/limits/>
- **The open question is settled on paper:** the D1 row still gives Paid
  1,000, the figure the 2026-02-11 change replaced with 10,000, so that row
  is the old Workers table copied before the change, and the Workers page it
  points to governs: 1,000 on Free. The first builder's `wrangler tail`
  check (an `arrivals stored: 4000` line next to the `commit budget:` line on
  a real scan) is still the proof and costs nothing.
- Not confirmed by an official page I could read: that a D1 `batch()` counts
  as ONE subrequest (a third-party write-up says so; Cloudflare's D1
  introduction calls a batch one round trip). The budget's 900 assumes it.
  If a batch counted per statement, the worst case would be about 4,450 D1
  calls (the 4,000 arrival rows alone), far past 1,000; again the tail line
  settles it.

**Arithmetic, worst case** (test load: 60 Pro web users, 40 Pro devices, 30
Pro email, 30 free instant, 20 check-ins, 10 free alert addresses, a sale, a
coverage request, 4,000 arrivals): outside calls **45 of 50** (Pro web push
took all 45; 5 left for redirects); D1 + KV **364 of 1,000** (36%), plus the
one counter write; one call at a time (the six-connection limit is never
near); no step starts after 25 s of the 30 s `waitUntil` allows. It holds.

**Fixed in review.** `fits()` closed outside calls only when the OUTSIDE
count was short. A send refused because D1 room was short is carried just
the same, but a later, cheaper, lower-priority send could still go out:
the priority promise broken in a corner. It now closes outside calls in
that case too. New check "fits: a send refused for D1 room closes outside
calls too" (fails on the first builder's `fits()`, passes now).

**NOT solvable by this design: the 10 ms CPU limit (new, 2026-11-18).** The
commit is one request, and the dispatch runs in its `waitUntil`; CPU spent
there is (by every account I found; not stated on a page I could open)
counted against the same request. Measured in Node 22 on this machine (the
same V8 engine, not a Worker; scratch script, not in the repo): a commit
body with 4,000 arrivals is about 1.1 MB and `JSON.parse` of it takes about
**6 ms**; `watchMatches` over 4,000 arrivals takes about **4.7 ms per
watch**, so 50 watches is about 175 ms. Every dispatcher matches every
arrival against its watches, so a commit's CPU grows with arrivals x
watches and is far past 10 ms today (the hub's count on 11-17: 87 watches
on devices alone). Budgeting calls cannot fix that; if Cloudflare stops the
commit for CPU, the dispatch ends wherever it was and no `commit budget:`
line or counter is written, which is exactly the silent failure item 1 is
about. Whether it happens is in the usage report the hub already has (CPU
stops on `POST /v1/admin/inventory/commit`). Options, none done here: (a)
Workers Paid ($5/mo: 30 s CPU, 10,000 subrequests) lifts both limits at
once; (b) make matching cheaper (memoize the make/model normalisation per
string, precompute each watch once, bucket arrivals by make): perhaps 5 to
10 times less, still not 10 ms at 4,000 arrivals; (c) have the scan send
only arrivals new since the last commit (touches `scraper/push_inventory.py`,
another workstream). Recommendation: (a), then (b).

### 2. Parts tab: a zip that arrives late (`docs/app.js`, sw `jh-v208`)

**What was wrong.** A part picked while the zip lookup was still out left
"Set a zip code (or use your location) up top" on the Parts tab after the
zip arrived (the hub's note in `ops/interchange.md`, 2026-11-16). Testing
the obvious fix found a second half: run again the moment the zip lands,
the search saw only the cars loaded so far and said "No cars within 100 mi
listing a spotted headlights right now", because the radius-first loader
had not yet fetched the cars around the new centre, and nothing re-ran the
Parts search when they came.

**What changed.**
- The waiting line carries `data-wait-place`. `pfSyncWhere()`, which every
  centre change already goes through (a zip lookup coming back, the /geo
  guess and links through `afterPlaceChange`, "Use my location"), now ends
  with `pfRerunIfPlaceArrived()`: when that line is on screen, a part is
  picked and a centre exists, it runs the search again.
- The launch call: a saved zip is restored (and, with its coordinates
  cached, `setZipCenter` runs to its end) before `let pfCat` is
  initialised. The new function reads the results box first; it is empty at
  launch, so `pfCat` is never read before it exists.
- A Parts search that runs while the cars around its centre are still
  loading (`invViewPending({ focus: false })`) is marked, and
  `afterInventoryChange` runs it once more when they land (the mark clears
  when the area is in). Counting is unchanged: `pfCountSearch` already
  counts one search once.
- Also covered by the same hook, not asked for: the same stale line after a
  late /geo guess or a late "Use my location".

**Test.** `backend/test/pf_late_zip_e2e.mjs` (new; the real `docs/` served
as https://yardscout.io/ through Playwright, no port, the zip lookup held
until the test releases it): typed zip, late; saved zip, late; saved zip
with cached coordinates (the launch order). 13 of 13. With
`PF_DOCS=<docs before the fix>` it fails 2: "once the zip arrives, the
results come" in both late cases, with the waiting line still on screen.
`pf_guards_unit.mjs` gained a stub for the loader check. Also run, all pass:
`no_gate_e2e` 78, `pf_new_cats_e2e`, `part_finder_e2e.py`,
`pf_ux_e2e.py`, `interchange_e2e.py`, `funnel_events_e2e`, all 23
`*_unit.mjs`.

### 3. Free emailed alert: the four loose ends

**(a) No "would have sent a push" for cars the alert covers** (`docs/app.js`
near-miss in `renderAlerts`). The line "One landed on …, after you set this
watch" with its Pro box "Would have sent a push within hours" now leaves out,
on the one watch whose free email alert is on, the cars that alert covers:
within the copy's radius of the copy's centre (exactly as
`falertWatchBody` sends them) and listed no earlier than the day before the
alert went on (the API records the cars already listed as known, so earlier
ones were never emailed and stay a near-miss). The browser now records when
it saw the alert go on (`onAt` in its own `ys_falert`; no watch touched).
With no `onAt` (an alert turned on before this change, or changed from
another browser) every car in range counts as covered: the line must never
claim a miss the email may have brought. Pending (no click yet) covers
nothing. Pure helper `falertCovers`. Not known to the page: whether a
covered car's email was actually sent or held past 48 h by the daily limit;
such a car shows no near-miss line.
Test: `free_email_alert_ui_e2e.mjs` case 7b (8 checks, 3 fail on the docs
before the change, run with the new `YS_DOCS` override);
`free_email_alert_client_unit.mjs` +11 checks of `falertCovers`.

**(b) The watch toast offers the free email alert** (`showWatchToast`). After
a new watch on the website, a free visitor who has not asked for the alert
in this browser is offered THAT for the new watch, in place of the Monday
email: "Free email alert for (car): we email you when one is set out within
50 mi, usually the same day. One car, one address, no account.", one field,
"Email me". One offer, no Pro box, no store link. The reply is the card's:
"Check your inbox … to turn on your email alert for (car)" (or "on" at once
when this browser already holds a token for the address). The Monday email
offer comes back, as before, once the alert is asked for, for a batch of
several new watches, for a watch past the first 5, and after the alert offer
was dismissed (x or 30 s) this visit (`ys_falert_no`, session). Counted as
the card is: `free-alert-shown` once a visit (shared key), `free-alert-asked`
on an address; `email-asked` is not counted when the Monday offer is not
shown. The request is the card's own (`falertSignup`, now shared by the card,
"Change car" and the toast). Layout check gained `watch-toast-falert`,
`-msg`, `-sent`.
Test: `free_email_alert_ui_e2e.mjs` cases 10 and 10b (17 checks: the offer,
wording, one field and no Pro box, counts, a bad address, the request is a
copy of the NEW watch, pending state keyed to it, rule 6 byte for byte, the
card waits for the click, the next watch gets the Monday offer, dismissal);
`recap_ask_e2e.mjs` now runs its web cases with the alert already asked for
(the state in which the toast still offers the Monday email).

**(c) Per-IP buckets** (`backend/src/recap_signup.js`). `/v1/recap/add` (32
an hour) and `/v1/recap/signup` (8 an hour) bumped one counter, so eight
one-tap adds from a network used up its sign-ups. Adds now have
`recap:add:ip:` and the named constant `IP_ADDS_PER_HOUR` (also used by the
free alert's car change, in its own `falert:chg:ip:`). Sign-ups (Monday
email and free alert, both send a confirmation) still share `recap:ip:`.
Test: `recap_signup_unit.mjs` 8b (3 checks; "10 adds from one network leave
its sign-ups untouched" fails with 429 on the shared bucket).

**(d) Hourly "Resend near daily cap"** (`backend/src/ops_monitor.js`). The
detail now reads: "Held back before that, lowest class first: free alert
emails (web) once 70 emails of any kind went out today (and after 20 free
alert emails; held alerts are retried on later scans), then sign-up
confirmations (Monday email and free alert) and Monday recaps once 10 or
fewer sends are left." Built from the limits `ops.js` enforces, so it
follows `RESEND_DAILY_CAP`. Test: `free_email_alert_unit.mjs` +4 (wording at
100 and 1,000 a day; the real hourly check firing at 95 of 100 with it).

**Decisions the owner may want to change.** (1) The toast offers the alert
INSTEAD of the Monday email until the alert is asked for; the Monday email
is then offered on later watches. (2) Dismissing the alert offer brings the
Monday offer back on the next watch the same visit (not nothing). (3) An
alert with an unknown start counts every car in range as covered (fewer Pro
prompts rather than a wrong one).

### 4. The weekly scorecard: the alert card and the free emailed alert (`backend/src/scorecard.js`)

Two lines, this week's counts only, in the style of item 3's "offered →
gave an address → confirmed" line:
- under item 2 (Watches created), every platform summed (the feed is the
  same in the apps): `alert card in the Cars feed: shown 42 → "Set an
  alert" 5 · dismissed 6`
- under item 3 (Monday email sign-ups), website only:
  `free email alert (website): offered 40 → gave an address 6 → confirmed
  4 → first email 2`

Honesty rules, as for the other lines: "no data" when no platform it
exists on reported anything this week; "nothing counted yet" when
platforms reported but none of these counters exists in either week (not a
row of 0s); a first counter inside this week adds "(counting started Nov
22)" (no counting-rules marker exists for these events, so the first
counted day is the start). No week-on-week change on either line yet (both
started on 11-16 and 11-17). The seven events are added to the one read
the scorecard already makes (daily email and the admin route; no public
request path).

Test: `scorecard_unit.mjs` 169 (14 new: both lines, sums across
platforms, web only for the free alert, placement under items 2 and 3, the
HTML email, "counting started", "nothing counted yet", "no data", last week
only, a read error, and the lines read back from SQLite with every
migration). Against the scorecard before the change the new checks fail.

Decision the owner may want to change: the free alert line sits under the
Monday email item rather than as a sixth numbered item.

### Final run (branch head 5c0e402c, 2026-11-18 16:47 UTC)

`tools/regress.sh` (new in this branch, item 6), one test at a time under
the shared lock: **93 passed, 1 failed, 0 skipped**, about 80 minutes. The
one failure is `cars_feed_e2e.mjs` "New: only cars set out today or
yesterday" (0 such cars in the test's area): it fails the same way against
the docs before this branch. The checked-in inventory on this base was
scraped 11-17 18:45 and the check reads today's date, so it should pass on
fresher data. Layout check at six widths: 2,472 checks, 0 failures. All six
API suites pass and left nothing listening.

## The Cars watch strip asks for the free email alert — branch `growth/strip-falert-1118`, NOT merged (2026-11-18)

Hub brief 2026-11-18: in the 7 days to 11-18 the Monday-email ask (strip and
toast, `email-asked`) was shown 17 times and no one gave an address; the free
emailed alert (live since 11-17 16:46 UTC, hub.md) was only offered in the
Alerts card. The watch toast already offers the alert on this base
(5c0e402c, "Watertight, continued" 3b), so this branch is the Cars watch
STRIP only, on the toast's own rule and request. Built on
`origin/hub/watertight-merge-1118` (fe91f512), then merged its head ca283423
and main fee45c10. Nothing deployed, merged into main, dispatched or sent.

**What the strip shows** (website, a make picked in the Cars list, not
already watched; `stripAskKind`, block "the free email alert comes first"
under ONE-STEP MONDAY EMAIL IN THE WATCH STRIP in `docs/app.js`):

| Case | Strip |
|---|---|
| One model, free, a location, no alert on or waiting here, not declined this visit, a free list with room | "Want the next one? Free email alert for **Nissan Xterra**: we email you when another is set out within 50 mi, usually the same day. One car, one address, no account." [email] [Email me], "or just watch it here". No cars in the list: "None here right now. … when one is set out …". The distance is the alert's (the list's radius, at most 50). No Pro prompt in the ask; the strip's Pro box under it is unchanged. |
| …after "Email me" | One watch through `addQuickWatch` (source `strip`, the list's radius, as before), one `POST /v1/free-alert/signup` with a copy of it (make, model, years, centre rounded, at most 50 mi; the toast's `falertToastSubmit` / `falertSignup`). The strip: "✓ Watching X; new ones light up in Alerts." and "Check your inbox. Tap the link we sent to v•••@… to turn on your email alert for X. Nothing is sent until you do." With a token this browser holds for that address (a confirmed Monday subscriber): "Your free email alert is on for X, to v•••@…" and no confirmation email. `ys_falert` pending (or on); the Alerts card shows the same. |
| …a later render (a scan coming in) | "Watching X — new ones light up in Alerts. Check your inbox to turn on its email alert." / "Its free email alert is on." (new: before, a re-render dropped the "check your inbox" line). |
| Several models (2 to 5) or the whole make | The Monday email, as before ("Add X to your free Monday email?" for a confirmed subscriber). More than 5: the plain strip. |
| An alert on or waiting for its click here | The Monday email (or "Add"). No "change your alert to this car": it would silently replace the car chosen for the one alert; "Change car" stays in the Alerts card. |
| The alert declined this visit (toast x or 30 s, or the strip's "or just watch it here") | The Monday email; both declined: the plain strip. |
| A free list at 5 watches | The Monday strip, as before (its submit opens the upgrade sheet, nothing sent): a full list cannot make the alert's watch. |
| Pro / the app shells | The plain strip with its Watch button, unchanged. |
| No location at all | The plain strip; Watch asks for the zip in the toast, and the toast then offers the alert (unchanged path). |
| A guessed place or a link's place | The alert ask carries the zip field (`stripZipFirst`): "within 50 mi of your zip"; the zip is saved first and the watch is centred on it, never on the guess. With a saved zip under a link's place: "of your own location". |

"or just watch it here" on the alert ask makes the watch (`jhWatchSearch`)
and counts as declining the alert this visit (`ys_falert_no`), so the toast
that follows offers the Monday email, not the same ask again.

**The toast** is as 5c0e402c built it. Its rule is now one function,
`falertAskOpen()` (free web visitor, no alert on or waiting here, not
declined this visit), which `falertToastPick` and the strip both call; no
behaviour change in the toast.

**Counting (dated; the daily email compares weeks).** From the day this is
deployed the strip's alert ask counts `free-alert-shown` ("Free alert
offered"): when at least half of it is on screen, once a visit, under the
key the card and the toast use (`ys_falert_seen`), so a visit that sees the
ask in two places counts once. An address given counts `free-alert-asked`.
`email-asked` still means the Monday-email field only and is NOT counted for
the alert's ask. So "Monday email asked" falls and "Free alert offered" rises
by the visits whose strip covered one model; weeks across the deploy day are
not like for like on those two rows. No counting-rules version step (as for
the alert itself). Written in `docs/app.js` (EVENTS_V comment, FUNNEL_EVENTS,
the strip block).

**Rule 6.** Watches are made only by `addQuickWatch`, exactly as before;
stored watches are never edited (byte-for-byte checks in three suites). The
alert keeps its own key `ys_falert`.

**Files.** `docs/app.js`, `docs/sw.js` (`jh-v211`); tests
`backend/test/cars_feed_e2e.mjs` (11, 11a, 11b rewritten: 43 strip checks),
`strip_guess_e2e.mjs` (the alert under a guess; the Monday email under a
guess with an alert waiting: 20), `free_email_alert_ui_e2e.mjs` case 11 (15,
real beacons; against the base docs its first checks fail and the case stops
at the missing ask), `free_email_alert_client_unit.mjs` (+19: `stripAskKind`
for every case above, the shared rule, the ask's wording, no Pro prompt in
it), `ui_no_truncation.mjs` (`feed-strip-mail` now with an alert waiting;
new `feed-strip-falert`, `-zip`, `-msg`, `-sent`, longest model in range with
years: those plus the toast's alert screen and `r5-cars-next` at six widths,
light and dark, 100% and 200%: 168 checks, 0 failures).

**Decisions the owner may want to change.** (1) One model only: a whole
make keeps the Monday email. (2) No "change your alert to this car" in the
strip. (3) "or just watch it here" declines the alert for the visit; the
toast then offers the Monday email. (4) A full free list keeps the Monday
strip (and its upgrade sheet) rather than the plain strip.

**Seen, not fixed.**
- With 5 free watches the strip still asks for an email and then opens the
  upgrade sheet (before this branch too); the plain strip would be kinder.
- The strip names a year range after the car ("Silverado 1500 2003–2007")
  and the alert before it ("2003–2007 Silverado 1500"), so the reply shows
  both forms.
- On the Monday strip (several models), "or just watch it here" is followed
  by the toast asking for the Monday email again (before this branch too;
  `cars_feed_e2e` 11b checks it).
- `backend/` has no `package-lock.json`, so `npm ci` stops with EUSAGE; the
  run below used the main checkout's `backend/node_modules` through a link
  (as the hub did), not committed.
- `tools/regress.sh` takes the shared lock itself and says never to run it
  under `flock`: wrapped in `flock /tmp/ys-test.lock` it would wait on itself
  forever. Run as `bash tools/regress.sh --out DIR`.

**Suggestions.** (1) The scorecard's Monday-email item could say "the Cars
strip asks for the free alert first since (deploy day)", so the drop in
"asked" is not read as interest falling. (2) A strip that says "Watching X"
could offer the alert for that watch when `falertAskOpen()` and it is among
the first 5 (today only the Alerts card does). (3) With 17 asks a week, give
it two weeks before judging the switch.

**Final run** (branch head 3e881c5e = the work above merged with main
fee45c10; 2026-11-18 19:14 UTC): `bash tools/regress.sh --out DIR`, one
test at a time under the shared lock it takes itself: **104 passed, 0
failed, 0 skipped** (units, scraper, tools, every self-contained browser
suite, the six API suites, the layout check). Layout at six widths: 2,664
checks, 0 failures. `cars_feed_e2e` passed in full this time (its "New:
only cars set out today or yesterday" check, which failed on the older
inventory in the watertight run, passes on today's data).
