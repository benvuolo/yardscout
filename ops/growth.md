# Growth — workstream status

Owns: the signup funnel (first visit to paying), its counters, and the copy
and layout of the steps on it. Source: the funnel audit of 2026-11-12
(read-only walk of main 01d0d7ea; its ten ranked changes are numbered below
as "audit change N"). Standing rules in `/CLAUDE.md` apply; rules 1, 3 and 6
are the ones this work touches.

## State (2026-11-12) — branch `growth/funnel-1`, NOT merged

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
3. **Free weekly email for web watchers** (audit change 2): a web watch
   still reaches nobody unless they install the app. Collecting an email is
   a data decision and needs the privacy text changed. Not built.
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
