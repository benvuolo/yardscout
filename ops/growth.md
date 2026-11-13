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
