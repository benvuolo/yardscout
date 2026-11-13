/* Unit test: the weekly scorecard (src/scorecard.js) at the top of the daily
 * ops email. Fixed fixture rows, no Worker:
 *
 *   windows        last 7 full UTC days vs the 7 before; today and older days ignored
 *   change         % over a base of 20+, raw counts under it
 *   comparable     no change figure for a platform whose fixed counting
 *                  (funnel-v2 marker) started after the first day shown, or
 *                  that has no marker; a total is blocked by any such platform
 *   missing data   a platform with no counter row in a week is "no data", a
 *                  platform that reported but had none of an event is 0
 *   small base     a rate under 20 is "2 of 9", not a %
 *   by source      source / campaign rollup across mediums and days, top 5 +
 *                  other links + "no tag"; one row per tagged link
 *   subscribers    change only from a stored snapshot exactly 7 days back;
 *                  "tracking starts <date>" before that; snapshots pruned at 60 d
 *   narrowing      "How people narrowed the Cars list (7 days)": routes add up,
 *                  no data (no v3 client) vs 0, "counting starts <date>",
 *                  website only until an app reports, per-platform lines
 *   by link        emails given and confirmed per tagged link
 *   integration    loadScorecardEvents on SQLite with every migration, and the
 *                  whole daily email (buildDailyReport) with the scorecard first
 *
 * Run: node backend/test/scorecard_unit.mjs
 * SCORECARD_OUT=<dir> also writes the rendered email to <dir>/email.html. */
import { DatabaseSync } from 'node:sqlite';
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import {
  computeScorecard, scorecardWindows, rateText, changeText, subscriberChange, storeSubsSnapshot,
  scorecardTextLines, scorecardHtml, scorecardItems, narrowingItems, loadScorecardEvents, buildScorecard, subsFromLoaded, SUBS_HISTORY_KEY,
} from '../src/scorecard.js';
import { buildDailyReport } from '../src/ops_monitor.js';

let failures = 0, passes = 0;
const check = (name, ok, extra = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${!ok && extra ? ' — ' + extra : ''}`);
  if (ok) passes++; else failures++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/* ---------- windows ---------- */
const w = scorecardWindows('2026-11-26');
check('current window = the 7 full days before today', w.current.from === '2026-11-19' && w.current.to === '2026-11-25', JSON.stringify(w));
check('prior window = the 7 days before that', w.prior.from === '2026-11-12' && w.prior.to === '2026-11-18', JSON.stringify(w));
const wm = scorecardWindows('2026-12-01');
check('windows cross a month end', wm.current.from === '2026-11-24' && wm.current.to === '2026-11-30' && wm.prior.from === '2026-11-17');

/* ---------- small helpers ---------- */
check('rate under 20: raw counts', rateText(2, 9) === '2 of 9', rateText(2, 9));
check('rate at 19: raw counts', rateText(5, 19) === '5 of 19');
check('rate at 20+: percent with counts', rateText(3, 40) === '8% (3 of 40)', rateText(3, 40));
check('rate of 0 opens: "0 of 0", no division', rateText(0, 0) === '0 of 0');
check('rate with missing data: null', rateText(null, 5) === null && rateText(1, null) === null);
check('change over 20: %', changeText(70, 50).text === '+40% on the week before (50)', changeText(70, 50).text);
check('change down: negative %', changeText(30, 40).text === '-25% on the week before (40)', changeText(30, 40).text);
check('change under 20: counts', changeText(12, 9).text === '12 vs 9 the week before', changeText(12, 9).text);
check('change from 0: counts, no %', changeText(5, 0).kind === 'counts');
check('change with a missing week: no data', changeText(null, 5).kind === 'no-data' && changeText(5, null).kind === 'no-data');

/* ---------- fixture rows ---------- */
const R = (day, event, n, { src = '', cmp = '', med = '', p = 'web' } = {}) => ({ day, event, source: src, campaign: cmp, medium: med, platform: p, n });
const pres = (days, p) => days.map((day) => ({ day, platform: p }));
const days = (from, n) => Array.from({ length: n }, (_, i) => new Date(Date.parse(from + 'T00:00:00Z') + i * 864e5).toISOString().slice(0, 10));
const CUR = days('2026-11-19', 7), PRI = days('2026-11-12', 7);

const rowsA = [
  // web visitors: 70 this week (reddit/xterra post 20 + comment 10, reddit 3, 6 other sources, 25 no tag), 50 the week before
  R('2026-11-20', 'first-visit', 12, { src: 'reddit', cmp: 'xterra', med: 'post' }),
  R('2026-11-21', 'first-visit', 8, { src: 'reddit', cmp: 'xterra', med: 'post' }),
  R('2026-11-21', 'first-visit', 10, { src: 'reddit', cmp: 'xterra', med: 'comment' }),
  R('2026-11-22', 'first-visit', 3, { src: 'reddit' }),
  R('2026-11-22', 'first-visit', 4, { src: 'forum', cmp: 'nissan' }),
  R('2026-11-22', 'first-visit', 2, { src: 'share' }),
  R('2026-11-23', 'first-visit', 2, { src: 'creator', cmp: 'a' }),
  R('2026-11-23', 'first-visit', 2, { src: 'creator', cmp: 'b' }),
  R('2026-11-23', 'first-visit', 1, { src: 'news' }),
  R('2026-11-23', 'first-visit', 1, { src: 'zzz' }),
  R('2026-11-24', 'first-visit', 25),
  R('2026-11-15', 'first-visit', 50),
  // outside both windows: today and 15 days back
  R('2026-11-26', 'first-visit', 999), R('2026-11-11', 'first-visit', 999),
  // watches: web 4 tagged + 3 untagged this week (7), 5 the week before
  R('2026-11-21', 'watch-created', 4, { src: 'reddit', cmp: 'xterra', med: 'post' }),
  R('2026-11-21', 'watch-created', 3),
  R('2026-11-14', 'watch-created', 5),
  // Monday email (web): asked 9, submitted 2 (tagged), confirmed 1 (server, untagged)
  R('2026-11-21', 'email-asked', 9),
  R('2026-11-21', 'email-submitted', 2, { src: 'reddit', cmp: 'xterra', med: 'comment' }),
  R('2026-11-22', 'email-confirmed', 1),
  // an app posting an email counter is not counted (web only)
  R('2026-11-22', 'email-asked', 50, { p: 'android' }),
  // Pro sheet: 9 opens, 2 checkouts (1 tagged), 1 Pro; prior 12 checkouts
  R('2026-11-21', 'paywall', 9),
  R('2026-11-21', 'checkout-start', 1, { src: 'reddit', cmp: 'xterra', med: 'post' }),
  R('2026-11-22', 'checkout-start', 1),
  R('2026-11-23', 'pro-converted', 1),
  R('2026-11-13', 'checkout-start', 12),
  // android: older installs, prior week only
  R('2026-11-13', 'first-visit', 3, { p: 'android' }),
  // a counter that is not on the scorecard
  R('2026-11-21', 'zip-entered', 40),
];
const presenceA = [...pres(CUR, 'web'), ...pres(PRI, 'web'), ...pres(['2026-11-13', '2026-11-22'], 'android')];
const subsA = { apple: 4, google: 2, web: 8 };
const A = computeScorecard({ today: '2026-11-26', rows: rowsA, presence: presenceA, v2: { web: '2026-11-12' }, subs: subsA, history: null });

const v = A.visitors;
check('visitors: web this week 70 (today and 15-days-back rows ignored)', v.byPlatform.web.current === 70, JSON.stringify(v.byPlatform.web));
check('visitors: web the week before 50', v.byPlatform.web.prior === 50);
check('visitors: web per day 10.0, prior 7.1', v.byPlatform.web.perDay === 10 && v.byPlatform.web.priorPerDay === 7.1, JSON.stringify(v.byPlatform.web));
check('visitors: web comparable (fixed counting from the first day of the week before) -> +40%',
  v.byPlatform.web.change.kind === 'pct' && v.byPlatform.web.change.pct === 40, JSON.stringify(v.byPlatform.web.change));
check('missing data: iPhone app reported nothing -> no data, not 0', v.byPlatform.ios.current === null && v.byPlatform.ios.prior === null && v.byPlatform.ios.change.text === 'no data');
check('android: reported this week (an email counter only) -> 0 visitors, not "no data"', v.byPlatform.android.current === 0, JSON.stringify(v.byPlatform.android));
check('android: no fixed counting yet -> not comparable, says why', v.byPlatform.android.change.kind === 'not-comparable'
  && /^not comparable yet \(Android app update pending\)$/.test(v.byPlatform.android.change.text), v.byPlatform.android.change.text);
check('visitors total = 70 (web + android 0; iOS no data left out)', v.current === 70 && v.prior === 53, `${v.current}/${v.prior}`);
check('total blocked by a not-comparable platform with data -> no change figure', v.change.kind === 'not-comparable' && v.change.pct === undefined, JSON.stringify(v.change));

check('by source: top 5 tagged links by visits, source / campaign rolled up across mediums and days',
  eq(v.bySource.map((s) => [s.label, s.visits]), [['reddit / xterra', 30], ['forum / nissan', 4], ['reddit', 3], ['creator / a', 2], ['creator / b', 2]]), JSON.stringify(v.bySource));
check('by source: the rest as "other links" (share 2 + news 1 + zzz 1)', v.otherTagged === 4, String(v.otherTagged));
check('by source: "no tag" = the empty source', v.noTag === 25, String(v.noTag));
const xt = A.sourceRows.find((s) => s.label === 'reddit / xterra');
check('link row: reddit / xterra 30 visits -> 4 watches -> 2 emails -> 1 checkout -> 0 Pro',
  xt && xt.visits === 30 && xt.watches === 4 && xt.emails === 2 && xt.checkouts === 1 && xt.pro === 0, JSON.stringify(xt));
check('link row: visits split by medium (post 20, comment 10)', xt && eq(xt.visitsByMedium, [{ medium: 'post', n: 20 }, { medium: 'comment', n: 10 }]), JSON.stringify(xt && xt.visitsByMedium));
check('link rows: tagged only, most visits first, at most 8', A.sourceRows.length === 8 && A.sourceRows[0].label === 'reddit / xterra' && !A.sourceRows.some((s) => s.label === 'no tag'), JSON.stringify(A.sourceRows.map((s) => s.label)));

check('watches: 7 this week (web), 5 before; 0-row platforms that reported are 0', A.watches.current === 7 && A.watches.byPlatform.web.current === 7 && A.watches.byPlatform.android.current === 0);
check('watches: web change under 20 -> counts', A.watches.byPlatform.web.change.text === '7 vs 5 the week before', A.watches.byPlatform.web.change.text);
check('emails: web only (android posting one is ignored)', !A.emails.asked.byPlatform.android && A.emails.asked.current === 9, JSON.stringify(A.emails.asked));
check('emails: asked 9, submitted 2, confirmed 1', A.emails.submitted.current === 2 && A.emails.confirmed.current === 1);
check('emails: comparable on web alone -> counts change (prior 0 with data that week)', A.emails.submitted.change.text === '2 vs 0 the week before', A.emails.submitted.change.text);
check('pro sheet: 9 opens, 2 checkouts, 1 Pro', A.proSheet.opens.current === 9 && A.proSheet.checkouts.current === 2 && A.proSheet.pro.current === 1);
check('pro sheet: rate over 9 opens is "2 of 9", not a %', A.proSheet.rate.text === '2 of 9', A.proSheet.rate.text);
check('pro sheet: web checkouts 2 vs 12 -> counts (base under 20)', A.proSheet.checkouts.byPlatform.web.change.text === '2 vs 12 the week before');

check('subscribers: total 14 from 4 + 2 + 8, complete', A.subscribers.now.total === 14 && A.subscribers.now.complete);
check('subscribers: no history -> "tracking starts" today (the daily run stores today)', A.subscribers.change.kind === 'tracking' && A.subscribers.change.text === 'change: tracking starts Nov 26', A.subscribers.change.text);

/* ---------- not comparable before the marker ---------- */
const B = computeScorecard({ today: '2026-11-19', rows: [R('2026-11-15', 'first-visit', 40), R('2026-11-08', 'first-visit', 30),
  R('2026-11-15', 'first-visit', 4, { p: 'ios' }), R('2026-11-16', 'paywall', 40), R('2026-11-16', 'checkout-start', 3)],
presence: [...pres(days('2026-11-05', 14), 'web'), ...pres(['2026-11-15'], 'ios')], v2: { web: '2026-11-12', ios: '2026-11-14' }, subs: subsA });
check('web marker Nov 12 inside the windows (Nov 5-18) -> "not comparable before Nov 12"',
  B.visitors.byPlatform.web.change.kind === 'not-comparable' && B.visitors.byPlatform.web.change.text === 'not comparable before Nov 12', B.visitors.byPlatform.web.change.text);
check('iOS marker Nov 14 -> "not comparable before Nov 14"', B.visitors.byPlatform.ios.change.text === 'not comparable before Nov 14');
check('total: latest blocking date', B.visitors.change.text === 'not comparable before Nov 14', B.visitors.change.text);
check('counts still shown when not comparable (web 40 this week, 30 before)', B.visitors.byPlatform.web.current === 40 && B.visitors.byPlatform.web.prior === 30);
check('rate at 40 opens -> percent', B.proSheet.rate.text === '8% (3 of 40)', B.proSheet.rate.text);
const Bc = computeScorecard({ today: '2026-11-26', rows: [], presence: pres([...CUR, ...PRI], 'web'), v2: { web: '2026-11-13' } });
check('marker one day after the first day shown -> still not comparable', Bc.visitors.byPlatform.web.change.kind === 'not-comparable');
const Bok = computeScorecard({ today: '2026-11-26', rows: [], presence: pres([...CUR, ...PRI], 'web'), v2: { web: '2026-11-12' } });
check('zero both weeks with data -> 0 and a counts change, not "no data"', Bok.visitors.current === 0 && Bok.visitors.change.text === '0 vs 0 the week before', JSON.stringify(Bok.visitors.change));
const Bgap = computeScorecard({ today: '2026-11-26', rows: [R('2026-11-20', 'first-visit', 5)], presence: pres(CUR, 'web'), v2: { web: '2026-11-01' } });
check('comparable platform with a silent week before -> "no data for one of the weeks"', Bgap.visitors.byPlatform.web.change.kind === 'no-data' && Bgap.visitors.change.kind === 'no-data', JSON.stringify(Bgap.visitors.change));

/* ---------- counters unreadable ---------- */
const E = computeScorecard({ today: '2026-11-26', eventsError: 'D1 down', subs: subsA });
check('counters unreadable -> every count "no data", never 0', E.visitors.current === null && E.watches.current === null && E.proSheet.rate.text === null);
check('counters unreadable -> one "no data" item in the email', scorecardItems(E).items[0].value === 'no data');

const Z = scorecardItems(computeScorecard({ today: '2026-11-26', subs: subsA }));
check('nothing reported in either week -> "no data" + one short line, never 0', Z.items[0].value === 'no data' && eq(Z.items[0].lines, ['nothing reported in either week']) && Z.items[3].value === 'no data', JSON.stringify(Z.items[0]));

/* ---------- subscriber change ---------- */
const snap = (apple, google, web) => ({ apple, google, web, total: (apple || 0) + (google || 0) + (web || 0), complete: apple != null && google != null && web != null });
let s = subscriberChange('2026-11-26', subsA, { days: { '2026-11-22': snap(1, 1, 1) } });
check('history younger than 7 days -> "tracking starts <first day>"', s.change.kind === 'tracking' && s.change.text === 'change: tracking starts Nov 22', s.change.text);
s = subscriberChange('2026-11-26', subsA, { days: { '2026-11-18': snap(3, 2, 5), '2026-11-19': snap(3, 2, 6) } });
check('snapshot exactly 7 days back -> +3 since Nov 19 (was 11)', s.change.kind === 'delta' && s.change.delta === 3 && s.change.text === '+3 since Nov 19 (was 11)', s.change.text);
s = subscriberChange('2026-11-26', subsA, { days: { '2026-11-18': snap(3, 2, 5) } });
check('day 7 back missing (gap) -> no data, no nearest-day guess', s.change.kind === 'no-data' && /no count stored for Nov 19/.test(s.change.text), s.change.text);
s = subscriberChange('2026-11-26', { apple: 4, google: null, web: 8 }, { days: { '2026-11-19': snap(3, 2, 6) } });
check('a store count missing today -> at least 12, no change figure', !s.now.complete && s.now.total === 12 && s.change.kind === 'no-data');
const Sm = computeScorecard({ today: '2026-11-26', subs: { apple: 4, google: null, web: 8 }, history: null });
check('missing store renders as "no data" and the total as "at least"', /at least 12/.test(scorecardItems(Sm).items[4].value) && /Google Play no data/.test(scorecardItems(Sm).items[4].lines[0]), JSON.stringify(scorecardItems(Sm).items[4]));
s = subscriberChange('2026-11-26', subsA, { days: { '2026-11-26': snap(9, 9, 9) } });
check('a snapshot from today (dry run after the cron) is not "history"', s.change.kind === 'tracking' && s.change.since === '2026-11-26');
s = subscriberChange('2026-11-26', subsA, null, { storingToday: false });
check('admin endpoint with no history: does not claim today starts tracking', /next daily email/.test(s.change.text), s.change.text);
s = subscriberChange('2026-11-26', { error: 'KV down' }, null);
check('subscribers unreadable -> no data', s.now === null && s.change.kind === 'no-data');
check('subsFromLoaded maps store counts and Stripe', eq(subsFromLoaded({ stripe: 8, stores: { apple: { active: 4 }, google: { error: 'x' } } }), { apple: 4, google: null, web: 8 }));

const kv = new Map();
const kvEnv = { ENTITLEMENTS: { get: async (k) => kv.get(k) ?? null, put: async (k, val) => { kv.set(k, val); } } };
await storeSubsSnapshot(kvEnv, '2026-11-26', subsA, { days: { '2026-09-01': snap(1, 1, 1), '2026-11-19': snap(3, 2, 6) } });
const stored = JSON.parse(kv.get(SUBS_HISTORY_KEY));
check('snapshot stored for today with counts only', eq(stored.days['2026-11-26'], { apple: 4, google: 2, web: 8, total: 14, complete: true }), JSON.stringify(stored));
check('snapshots older than 60 days pruned, recent kept', !stored.days['2026-09-01'] && !!stored.days['2026-11-19']);
check('no snapshot stored when subscribers failed to load', (await storeSubsSnapshot(kvEnv, '2026-11-27', { error: 'x' }, stored)) === false);

/* ---------- rendering: plain words ---------- */
const text = scorecardTextLines(A).join('\n');
const C = { ink: '#1c1c1a', dim: '#6b675f', line: '#e4e0d6', soft: '#f6f4ee', accent: '#b84a0a' };
const esc = (x) => String(x == null ? '' : x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const html = scorecardHtml(A, { esc, C });
for (const id of ['first-visit', 'watch-created', 'email-asked', 'email-submitted', 'email-confirmed', 'checkout-start', 'pro-converted', 'funnel-v2', 'paywall', 'events_daily', 'undefined', 'NaN', 'null']) {
  check(`email text/html shows no "${id}"`, !text.includes(id) && !html.includes(id));
}
check('text: reddit / xterra line', text.includes('reddit / xterra: 30 visits (post 20, comment 10) → 4 watches → 2 emails given, 0 confirmed → 1 checkout → 0 Pro'), text);
check('text: "From:" line with no tag', /From: reddit \/ xterra 30 · forum \/ nissan 4 · reddit 3 · creator \/ a 2 · creator \/ b 2 · other links 4 · no tag 25/.test(text), text);
check('text: iPhone app shows "no data"', /iPhone app: no data/.test(text) && !/no data a day/.test(text));
check('text: web visitors with their change', text.includes('Web: 10.0 a day, +40% on the week before (50)'), text);
check('text: Android visitors say not comparable instead of a change', text.includes('Android app: 0.0 a day, not comparable yet (Android app update pending)'), text);
check('text: rate "2 of 9"', /Pro sheet to checkout: 2 of 9/.test(text));
check('text: five numbered items', [1, 2, 3, 4, 5].every((i) => text.includes(`  ${i}. `)));
check('text: counting note names Android as not yet fixed', /not yet for the iPhone app and Android app/.test(text), text);

/* ---------- how people narrowed the Cars list (7 days) ---------- */
{
  const N = (day, kind, n, p = 'web') => R(day, 'narrow/' + kind, n, { p });
  const v3p = (ds, p = 'web') => ds.map((day) => ({ day, platform: p }));
  const nw = (args) => computeScorecard({ today: '2026-11-26', rows: [], presence: presenceA, v2: { web: '2026-11-12' }, subs: subsA, ...args }).narrowing;

  // 1. nothing on v3 yet: no data, even with stray rows
  const n0 = nw({ rows: [N('2026-11-22', 'search', 4)] });
  const i0 = narrowingItems(n0);
  check('narrow: no v3 client yet -> no data (stray rows ignored), never 0', n0.total === null && i0.head === 'no data', JSON.stringify(n0));
  check('narrow: no v3 client yet -> "counting starts with the first visit to the updated website"', eq(i0.lines, ['counting starts with the first visit to the updated website']), JSON.stringify(i0.lines));

  // 2. counting started inside the window (Nov 22): 4 of 7 days; apps not on it
  const rows2 = [N('2026-11-22', 'search', 3), N('2026-11-24', 'search', 2), N('2026-11-23', 'search-trim', 2),
    N('2026-11-22', 'filters-model', 4), N('2026-11-25', 'filters-make', 3), N('2026-11-24', 'trim', 1), N('2026-11-23', 'link', 9),
    N('2026-11-26', 'search', 50), N('2026-11-18', 'link', 50),          // today and before the window: outside
    N('2026-11-23', 'search', 7, 'ios'),                                  // a platform with no v3 marker: ignored
  ];
  const n2 = nw({ rows: rows2, v3: { web: '2026-11-22' }, v3Presence: v3p(['2026-11-22', '2026-11-23', '2026-11-24', '2026-11-25']) });
  const i2 = narrowingItems(n2);
  check('narrow: window = the scorecard\'s last 7 full days', n2.window.from === '2026-11-19' && n2.window.to === '2026-11-25', JSON.stringify(n2.window));
  check('narrow: routes add up (search box 5 + 2 trim rows = 7, Filters 4 model + 3 make only = 7, link 9, trim 1)',
    eq(n2.total, { search: 7, searchTrim: 2, filters: 7, filtersModel: 4, filtersMake: 3, link: 9, trim: 1 }), JSON.stringify(n2.total));
  check('narrow: head line in plain words', i2.head === 'search box 7 · Filters 7 · link 9 · trim filter 1', i2.head);
  check('narrow: the split under it', i2.lines[0] === 'search box: 5 make or model, 2 trim row · Filters: 4 model, 3 make only', i2.lines[0]);
  check('narrow: "counting starts Nov 22: 4 of 7 days so far" until 7 days are covered', n2.daysCounted === 4 && !n2.full && i2.lines.includes('counting starts Nov 22: 4 of 7 days so far'), JSON.stringify(i2.lines));
  check('narrow: website only until the next app update', i2.lines.includes('website only until the next app update') && !i2.lines.some((l) => /^iPhone app:/.test(l)), JSON.stringify(i2.lines));
  check('narrow: says a person counts once a day per way', i2.lines[i2.lines.length - 1] === 'A person counts at most once a day for each way.');

  // 3. a full week; a way nobody used is 0, not "no data"
  const n3 = nw({ rows: [N('2026-11-19', 'search', 14), N('2026-11-25', 'link', 22)], v3: { web: '2026-11-15' }, v3Presence: v3p(CUR) });
  const i3 = narrowingItems(n3);
  check('narrow: full week -> no "counting starts" line', n3.full && n3.daysCounted === 7 && !i3.lines.some((l) => /counting starts/.test(l)), JSON.stringify(i3.lines));
  check('narrow: unused ways are 0 (the website reported all week)', i3.head === 'search box 14 · Filters 0 · link 22 · trim filter 0', i3.head);
  check('narrow: first v3 day exactly on the window\'s first day counts as a full week', nw({ v3: { web: '2026-11-19' }, v3Presence: v3p(CUR) }).full === true);
  const n3b = nw({ v3: { web: '2026-11-15' }, v3Presence: v3p(['2026-11-21']) });
  check('narrow: reporting but nobody narrowed -> all 0', eq(n3b.total, { search: 0, searchTrim: 0, filters: 0, filtersModel: 0, filtersMake: 0, link: 0, trim: 0 }), JSON.stringify(n3b.total));

  // 4. started today: nothing in the window yet
  const n4 = nw({ v3: { web: '2026-11-26' }, v3Presence: [] });
  check('narrow: counting started today -> no data, "counting starts Nov 26"', n4.total === null && eq(narrowingItems(n4).lines, ['counting starts Nov 26']), JSON.stringify(narrowingItems(n4)));

  // 5. the iPhone app on v3, Android not: per-platform lines
  const n5 = nw({ rows: [N('2026-11-20', 'search', 10), N('2026-11-21', 'search', 3, 'ios'), N('2026-11-21', 'link', 1, 'ios'), N('2026-11-21', 'link', 5, 'android')],
    v3: { web: '2026-11-12', ios: '2026-11-20' }, v3Presence: [...v3p(CUR), ...v3p(['2026-11-20', '2026-11-21'], 'ios')] });
  const i5 = narrowingItems(n5);
  check('narrow: total over the reporting platforms only (Android rows without v3 ignored)', n5.total.search === 13 && n5.total.link === 1, JSON.stringify(n5.total));
  check('narrow: per-platform lines once an app reports', i5.lines.includes('Web: search box 10 · Filters 0 · link 0 · trim filter 0')
    && i5.lines.includes('iPhone app: search box 3 · Filters 0 · link 1 · trim filter 0') && i5.lines.includes('Android app: no data'), JSON.stringify(i5.lines));
  check('narrow: names the app still waiting for its update', i5.lines.includes('Android app: not counted until its next update') && !i5.lines.includes('website only until the next app update'), JSON.stringify(i5.lines));

  // 6. counters unreadable
  const n6 = computeScorecard({ today: '2026-11-26', eventsError: 'D1 down', subs: subsA }).narrowing;
  check('narrow: unreadable counters -> no data with the reason', narrowingItems(n6).head === 'no data' && /D1 down/.test(narrowingItems(n6).lines[0]));

  // 7. both renderers place it directly under the scorecard
  const card = computeScorecard({ today: '2026-11-26', rows: [...rowsA, ...rows2], presence: presenceA, v2: { web: '2026-11-12' }, v3: { web: '2026-11-22' },
    v3Presence: v3p(['2026-11-22', '2026-11-23', '2026-11-24', '2026-11-25']), subs: subsA });
  const tl = scorecardTextLines(card);
  const at = tl.findIndex((l) => l.startsWith('  How people narrowed the Cars list (7 days): '));
  check('narrow text: last block of the scorecard, after the small-numbers note', at > 0 && /Small numbers/.test(tl[at - 1]), JSON.stringify(tl.slice(-8)));
  check('narrow text: head on the title line', tl[at] === '  How people narrowed the Cars list (7 days): search box 7 · Filters 7 · link 9 · trim filter 1', tl[at]);
  const hh = scorecardHtml(card, { esc: (x) => String(x), C: { line: '#ddd', dim: '#666', ink: '#111', accent: '#b84a0a' } });
  check('narrow html: inside the scorecard block, after the link lines', hh.indexOf('How people narrowed the Cars list') > hh.indexOf('What each tagged link did this week')
    && hh.includes('search box 7 · Filters 7 · link 9 · trim filter 1') && hh.includes('counting starts Nov 22: 4 of 7 days so far'));
  check('narrow: other scorecard numbers unchanged by the narrowing rows', card.visitors.byPlatform.web.current === 70 && card.watches.current === A.watches.current);
}

/* ---------- confirmed Monday-email sign-ups by link ---------- */
{
  const rowsC = [
    R('2026-11-20', 'first-visit', 10, { src: 'reddit', cmp: 'xterra', med: 'post' }),
    R('2026-11-20', 'email-submitted', 3, { src: 'reddit', cmp: 'xterra', med: 'post' }),
    R('2026-11-21', 'email-confirmed', 2, { src: 'reddit', cmp: 'xterra', med: 'post' }),
    R('2026-11-21', 'email-confirmed', 1),   // a sign-up with no remembered link
  ];
  const C1 = computeScorecard({ today: '2026-11-26', rows: rowsC, presence: presenceA, v2: { web: '2026-11-12' }, subs: subsA });
  const r = C1.sourceRows.find((s) => s.label === 'reddit / xterra');
  check('by link: confirmed sign-ups counted per link (2 of 3 given)', r && r.emails === 3 && r.confirmed === 2, JSON.stringify(r));
  check('by link: total confirmed still counts the untagged one', C1.emails.confirmed.current === 3, JSON.stringify(C1.emails.confirmed));
  const line = scorecardTextLines(C1).find((l) => l.includes('reddit / xterra:'));
  check('by link: the line reads "3 emails given, 2 confirmed"', /→ 3 emails given, 2 confirmed → /.test(line), line);
  const one = scorecardTextLines(computeScorecard({ today: '2026-11-26', rows: [R('2026-11-20', 'first-visit', 1, { src: 'x' }), R('2026-11-20', 'email-submitted', 1, { src: 'x' })], presence: presenceA, subs: subsA }))
    .find((l) => l.includes('x: '));
  check('by link: singular "1 email given, 0 confirmed"', /→ 1 email given, 0 confirmed → /.test(one), one);
}

/* ---------- integration: SQLite with every migration (D1 shim) ---------- */
function d1(db) {
  const wrap = (sql, args = []) => ({
    bind: (...a) => wrap(sql, a),
    first: async () => db.prepare(sql).get(...args) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    run: async () => { const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
  });
  return { prepare: (sql) => wrap(sql), batch: async (stmts) => Promise.all(stmts.map((st) => st.all())) };
}
const db = new DatabaseSync(':memory:');
const mdir = new URL('../migrations/', import.meta.url);
for (const f of readdirSync(mdir).filter((x) => x.endsWith('.sql')).sort()) db.exec(readFileSync(new URL(f, mdir), 'utf8'));
const ins = db.prepare('INSERT INTO events_daily (day, event, source, campaign, medium, platform, n) VALUES (?, ?, ?, ?, ?, ?, ?)');
for (const r of rowsA) ins.run(r.day, r.event, r.source, r.campaign, r.medium, r.platform, r.n);
// presence the way the API leaves it: the v2 marker row per (day, platform)
for (const d of [...CUR, ...PRI]) ins.run(d, 'funnel-v2', '', '', '', 'web', 1);
// v3 web client from Nov 22: its marker rows and what it counted (narrowing)
for (const d of ['2026-11-22', '2026-11-23', '2026-11-24', '2026-11-25']) ins.run(d, 'funnel-v3', '', '', '', 'web', 1);
for (const [d, k, n] of [['2026-11-22', 'search', 9], ['2026-11-23', 'search-trim', 2], ['2026-11-22', 'filters-model', 6], ['2026-11-24', 'filters-make', 3],
  ['2026-11-23', 'link', 22], ['2026-11-25', 'trim', 3], ['2026-11-22', 'search', 3]]) ins.run(d, 'narrow/' + k, d === '2026-11-22' && k === 'search' && n === 3 ? 'reddit' : '', '', '', 'web', n);
const kv2 = new Map();
const env = {
  DB: d1(db),
  ENTITLEMENTS: {
    get: async (k, type) => { const x = kv2.get(k) ?? null; return type === 'json' && x != null ? JSON.parse(x) : x; },
    put: async (k, val) => { kv2.set(k, val); }, delete: async (k) => { kv2.delete(k); },
    list: async ({ prefix }) => ({ keys: [...kv2.keys()].filter((k) => k.startsWith(prefix)).map((name) => ({ name })), list_complete: true }),
  },
};
const ev = await loadScorecardEvents(env, '2026-11-26');
check('D1: marker day read back (web since Nov 12)', ev.v2.web === '2026-11-12' && !ev.v2.android, JSON.stringify(ev.v2));
const I = computeScorecard({ today: '2026-11-26', ...ev, subs: subsA });
check('D1: same visitors as the fixture (web 70 / 50)', I.visitors.byPlatform.web.current === 70 && I.visitors.byPlatform.web.prior === 50);
check('D1: android present via its rows only (Nov 13, Nov 22)', I.visitors.byPlatform.android.current === 0 && I.visitors.byPlatform.android.prior === 3);
check('D1: same link row', eq(I.sourceRows[0], A.sourceRows[0]));
check('D1: v3 start and marker days read back', ev.v3.web === '2026-11-22' && ev.v3Presence.length === 4 && !ev.v3.ios, JSON.stringify([ev.v3, ev.v3Presence]));
check('D1: narrowing summed across sources and days (search 12 + 2 trim rows, Filters 6 + 3, link 22, trim 3)',
  eq(I.narrowing.total, { search: 14, searchTrim: 2, filters: 9, filtersModel: 6, filtersMake: 3, link: 22, trim: 3 }), JSON.stringify(I.narrowing.total));
check('D1: the markers are not counted as narrowing or as funnel events', I.visitors.byPlatform.web.current === 70);

// The whole daily email: stores, entitlements and public files as fixtures.
kv2.set('ent:a@users.test', JSON.stringify({ pro: true, source: 'stripe', expiresAt: '2099-01-01T00:00:00Z' }));
kv2.set('ent:b@users.test', JSON.stringify({ pro: true, source: 'stripe', expiresAt: '2099-01-01T00:00:00Z' }));
kv2.set('ent:c@users.test', JSON.stringify({ pro: true, source: 'comp', expiresAt: '2099-01-01T00:00:00Z' }));
kv2.set('ops:store-subs', JSON.stringify({ at: '2026-11-26T09:00:00Z', apple: { active: 4, trial: 1, asOf: '2026-11-25' }, google: { active: 2, asOf: '2026-11-25' } }));
kv2.set(SUBS_HISTORY_KEY, JSON.stringify({ days: { '2026-11-19': snap(3, 2, 1) } }));
db.prepare("INSERT OR REPLACE INTO inv_meta (id, updated_at, manifest, directory) VALUES (1, ?, '{}', ?)").run('2026-11-26T11:00:00Z',
  JSON.stringify({ yards: [['Y1'], ['Y2']], counts: { yards: 2, vehicles: 1541 }, scrapedAt: '2026-11-26T10:40:00Z' }));
const realFetch = globalThis.fetch;
globalThis.fetch = async (url) => {
  const u = String(url);
  if (u.endsWith('/yard_health.json')) return new Response(JSON.stringify({ scrapedAt: '2026-11-26T10:40:00Z', yards: { 'Pick-n-Pull - Phoenix': { lastChangedAt: '2026-11-26T08:00:00Z', unchangedScans: 0 } } }));
  if (u.endsWith('/inventory_meta.json')) return new Response(JSON.stringify({ vehicles: 1541 }));
  if (u.endsWith('/models.json')) return new Response(JSON.stringify({ makes: { Nissan: { Xterra: 1 } } }));
  return new Response('not found', { status: 404 });
};
const now = Date.parse('2026-11-26T13:07:00Z');
const quiet = console.log; console.log = () => {};
let rep;
try { rep = await buildDailyReport(env, { now }); } finally { console.log = quiet; }
check('daily report carries the scorecard', rep.scorecard && rep.scorecard.visitors.byPlatform.web.current === 70, JSON.stringify(rep.scorecard && rep.scorecard.eventsError));
check('daily: subscribers 4 + 2 + 2 web = 8; change from Nov 19 snapshot (6) = +2', rep.scorecard.subscribers.now.total === 8 && rep.scorecard.subscribers.change.text === '+2 since Nov 19 (was 6)', JSON.stringify(rep.scorecard.subscribers));
check('daily: build without storeSnapshot stores nothing', !JSON.parse(kv2.get(SUBS_HISTORY_KEY)).days['2026-11-26']);
const t = rep.email.text, h = rep.email.html;
check('daily text: scorecard before OPEN ISSUES', t.indexOf('WEEKLY SCORECARD') > 0 && t.indexOf('WEEKLY SCORECARD') < t.indexOf('OPEN ISSUES'));
check('daily text: narrowing block under the scorecard, before OPEN ISSUES',
  t.includes('  How people narrowed the Cars list (7 days): search box 14 · Filters 9 · link 22 · trim filter 3')
  && t.indexOf('How people narrowed') > t.indexOf('WEEKLY SCORECARD') && t.indexOf('How people narrowed') < t.indexOf('OPEN ISSUES')
  && t.includes('counting starts Nov 22: 4 of 7 days so far') && t.includes('website only until the next app update'), t.slice(t.indexOf('How people'), t.indexOf('OPEN ISSUES')));
check('daily html: narrowing block before Open issues', h.indexOf('How people narrowed the Cars list') > h.indexOf('Weekly scorecard') && h.indexOf('How people narrowed the Cars list') < h.indexOf('Open issues'));
check('daily html: scorecard before Open issues', h.indexOf('Weekly scorecard') > 0 && h.indexOf('Weekly scorecard') < h.indexOf('Open issues'));
check('daily html: existing sections still there', ['Open issues', 'Scan', 'Paying subscribers', 'Funnel'].every((x) => h.includes(x)));
check('daily email leaks no subscriber address', !/users\.test/.test(t) && !/users\.test/.test(h));
console.log = () => {};
try { await buildDailyReport(env, { now, storeSnapshot: true }); } finally { console.log = quiet; }
check('daily: the real run stores today\'s snapshot', eq(JSON.parse(kv2.get(SUBS_HISTORY_KEY)).days['2026-11-26'], { apple: 4, google: 2, web: 2, total: 8, complete: true }));
const adminCard = (await buildScorecard(env, { today: '2026-11-26', subs: { apple: 4, google: 2, web: 2 } })).card;
check('admin JSON: same numbers as the email', adminCard.visitors.current === rep.scorecard.visitors.current && eq(adminCard.sourceRows, rep.scorecard.sourceRows));
check('admin JSON: carries the narrowing numbers', eq(adminCard.narrowing.total, rep.scorecard.narrowing.total) && adminCard.narrowing.since === '2026-11-22'
  && adminCard.narrowing.daysCounted === 4 && eq(adminCard.narrowing.appsReporting, []), JSON.stringify(adminCard.narrowing));
check('admin JSON: no per-person fields', !/@|"ip"|"id"|device/i.test(JSON.stringify(adminCard)), JSON.stringify(adminCard).match(/@|"ip"|"id"|device/i));
globalThis.fetch = realFetch;

if (process.env.SCORECARD_OUT) {
  mkdirSync(process.env.SCORECARD_OUT, { recursive: true });
  writeFileSync(`${process.env.SCORECARD_OUT}/email.html`, h);
  writeFileSync(`${process.env.SCORECARD_OUT}/email.txt`, t);
  console.log(`wrote ${process.env.SCORECARD_OUT}/email.html`);
}

console.log(failures ? `\n${failures} FAILURE(S), ${passes} passed` : `\nALL PASS (${passes})`);
process.exit(failures ? 1 : 0);
