/* Unit test: the free emailed alert for web visitors (src/free_email_alert.js,
 * the budget helpers in src/ops.js, the commit hook in src/admin.js). Runs
 * the real handlers against an in-memory SQLite with every migration applied
 * (a small D1 shim over node:sqlite) and a stubbed Resend. No Worker needed.
 *
 *   limits   one watch per address (a second replaces, only after its own
 *            confirmation click); the free instant push's 50 mi; free
 *            criteria only
 *   opt-in   nothing is ever sent to an unconfirmed address; GET confirm is a
 *            page; the click confirms once
 *   sending  one email per address per scan, deduped per (address, car),
 *            future arrivals only, List-Unsubscribe headers, "same day"
 *   budget   per scan, per day, the reserve under all other mail; a held
 *            alert is counted once, kept unsent and retried for 48 h
 *   removal  unsubscribe link / "Turn off" delete the address and its rows
 *
 * Run: node test/free_email_alert_unit.mjs */
import { DatabaseSync } from 'node:sqlite';
import { readdirSync, readFileSync } from 'node:fs';
import {
  handleFreeAlertSignup, handleFreeAlertConfirmPage, handleFreeAlertConfirm, handleFreeAlertStatus,
  handleFreeAlertOff, handleFreeAlertUnsubscribe, dispatchFreeEmailAlerts, pruneFreeAlerts, freeAlertStats,
  sanitizeFreeAlertWatch, freeAlertUnsubUrl, buildFreeAlertEmail, buildFreeAlertConfirmEmail, nearBox,
  FREE_ALERT_RADIUS_MI, FREE_ALERT_MAX_PER_SCAN, FREE_ALERT_CATCHUP_MS,
} from '../src/free_email_alert.js';
import { haversineMiles } from '../src/util.js';
import { FREE_INSTANT_RADIUS_MI } from '../src/devices.js';
import { handleRecapSignup, handleRecapConfirm, recapSubToken, recapUnsubUrl } from '../src/recap_signup.js';
import { flushOps, freeAlertLimits, freeAlertBudget, optionalEmailAllowed, CHANNELS, RESEND_RESERVE } from '../src/ops.js';
import { handleEvent } from '../src/attribution.js';
import { resendVolumeDetail, evaluateConditions } from '../src/ops_monitor.js';
import { handleCommit } from '../src/admin.js';
import { storeArrivals } from '../src/alerts.js';

let failures = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra && !ok ? ' — ' + extra : ''}`); if (!ok) failures++; };

/* ---- D1 shim (batch returns each statement's rows, as D1 does) ---- */
let statements = 0;
function d1(db) {
  const isRead = (sql) => /^\s*SELECT/i.test(sql);
  const wrap = (sql, args = []) => ({
    bind: (...a) => wrap(sql, a),
    first: async () => { statements++; return db.prepare(sql).get(...args) ?? null; },
    all: async () => { statements++; return { results: db.prepare(sql).all(...args) }; },
    run: async () => { statements++; const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
    _exec: () => (isRead(sql) ? { results: db.prepare(sql).all(...args) } : (db.prepare(sql).run(...args), { results: [] })),
  });
  return {
    prepare: (sql) => wrap(sql),
    batch: async (stmts) => {
      statements++;
      db.exec('BEGIN');
      try { const out = stmts.map((s) => s._exec()); db.exec('COMMIT'); return out; } catch (e) { db.exec('ROLLBACK'); throw e; }
    },
  };
}
function freshEnv(extra = {}) {
  const db = new DatabaseSync(':memory:');
  const dir = new URL('../migrations/', import.meta.url);
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.sql')).sort()) db.exec(readFileSync(new URL(f, dir), 'utf8'));
  const kv = new Map();
  return {
    raw: db, kv,
    DB: d1(db),
    ENTITLEMENTS: { get: async (k, type) => { const v = kv.get(k) ?? null; return v && type === 'json' ? JSON.parse(v) : v; },
      put: async (k, v) => { kv.set(k, v); }, delete: async (k) => { kv.delete(k); } },
    RESEND_API_KEY: 're_test_key', EMAIL_UNSUB_SECRET: 'unit-secret', APP_URL: 'https://yardscout.io/',
    API_PUBLIC_URL: 'https://api.test', EMAIL_FROM: 'YardScout <hello@yardscout.io>',
    ...extra,
  };
}

/* ---- Resend stub (global fetch) ---- */
let outbox = [];
let resendStatus = 200;
globalThis.fetch = async (url, init) => {
  if (String(url) === 'https://api.resend.com/emails') {
    if (resendStatus !== 200) return new Response(JSON.stringify({ name: 'validation_error', message: 'nope' }), { status: resendStatus });
    outbox.push(JSON.parse(init.body));
    return new Response(JSON.stringify({ id: 'stub-' + outbox.length }), { status: 200, headers: { 'content-type': 'application/json' } });
  }
  return new Response('not found', { status: 404 });
};
// Never log a full address: watch console output for one.
const logged = [];
const origLog = console.log;
console.log = (...a) => { logged.push(a.join(' ')); if (/^(PASS|FAIL)|FAILURES|ALL PASS/.test(String(a[0]))) origLog(...a); };

let ipN = 0;
const nextIp = () => '198.51.100.' + (++ipN % 250) + '.' + Math.floor(ipN / 250);
const post = (path, body) => new Request('https://api.test' + path, {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
const signup = (env, body, ip = nextIp()) => handleFreeAlertSignup(post('/v1/free-alert/signup', body), env, ip);
const jsonOf = async (r) => ({ status: r.status, data: await r.json() });
const tokenFrom = (mail) => decodeURIComponent(((mail && mail.text.match(/https:\/\/api\.test\/v1\/free-alert\/confirm\?t=([^\s]+)/)) || [])[1] || '');
const confirmPost = (env, t) => handleFreeAlertConfirm(new Request('https://api.test/v1/free-alert/confirm', {
  method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(t) }), env);
const rows = (env, sql, ...a) => env.raw.prepare(sql).all(...a);
const events = (env, e) => rows(env, 'SELECT source, n FROM events_daily WHERE event = ?', e);
/** Sign up + click the confirmation link; returns the browser token. */
async function optIn(env, email, watch, extra = {}) {
  outbox = [];
  const r = await jsonOf(await signup(env, { email, watch, ...extra }));
  if (r.status !== 200 || outbox.length !== 1) throw new Error('optIn: sign-up failed ' + JSON.stringify(r));
  const res = await confirmPost(env, tokenFrom(outbox[0]));
  if (res.status !== 303) throw new Error('optIn: confirm failed ' + res.status);
  outbox = [];
  return decodeURIComponent((res.headers.get('location') || '').split('sub=')[1] || '');
}

const NOW = Date.now();
const SLC = { lat: 40.76012, lng: -111.89123 };
// ~0.0145 degrees of latitude per mile.
const northOf = (mi) => ({ lat: SLC.lat + mi * 0.01449, lng: SLC.lng });
const car = (id, extra = {}) => ({ id, year: 2005, make: 'Toyota', model: '4Runner', row: '14',
  location: 'Test Yard - Salt Lake', city: 'Salt Lake City', state: 'UT', lat: 40.7, lng: -111.9,
  dateAdded: new Date(NOW).toISOString().slice(0, 10), ...extra });
const seedArrival = (e, v, seenAt = new Date(NOW - 2 * 86400_000).toISOString()) => e.raw.prepare(
  `INSERT INTO arrivals (vehicle_id, year, make, model, row, location, city, state, lat, lng, date_added, seen_at, vpic_json)
   VALUES (?, ?, ?, ?, ?, ?, '', 'UT', ?, ?, ?, ?, NULL)`).run(String(v.id), v.year, v.make, v.model, v.row, v.location, v.lat, v.lng, v.dateAdded, seenAt);

const EMAIL = 'Visitor.One@Example.com';
const LOWER = EMAIL.toLowerCase();
// What the browser holds: the watch as docs/app.js stores it.
const browserWatch = { make: 'Toyota', model: '4Runner', yrMin: 2003, yrMax: 2009, matchOnly: true, radiusMi: 250,
  ...SLC, addedAt: '2026-11-12T10:00:00.000Z~abc123', driveFilter: '4x4', trimFilter: 'SR5' };
const browserBefore = JSON.stringify(browserWatch);

/* ---- 1. the limits: the free instant push's 50 mi, free criteria only ---- */
check('the distance IS the free instant push constant (devices.js), 50 mi', FREE_ALERT_RADIUS_MI === FREE_INSTANT_RADIUS_MI && FREE_ALERT_RADIUS_MI === 50);
const sw = sanitizeFreeAlertWatch(browserWatch);
check('copy keeps make/model/years', sw && sw.make === 'Toyota' && sw.model === '4Runner' && sw.year_min === 2003 && sw.year_max === 2009, JSON.stringify(sw));
check('a 250 mi watch is clamped to 50 mi', sw.radius_mi === 50);
check('a smaller radius is kept (25 mi)', sanitizeFreeAlertWatch({ ...browserWatch, radiusMi: 25 }).radius_mi === 25);
check('centre rounded to ~1 km', sw.lat === 40.76 && sw.lng === -111.89, `${sw.lat},${sw.lng}`);
check('Pro trim/drive filters and the browser key are not copied', !/SR5|4x4|abc123|matchOnly/.test(JSON.stringify(sw)));
check('no centre → refused', sanitizeFreeAlertWatch({ make: 'Honda', model: 'Civic', radiusMi: 50 }) === null);
check('no make → refused', sanitizeFreeAlertWatch({ model: 'Civic', ...SLC, radiusMi: 50 }) === null);
check("'email:free-alert' is a counted channel", CHANNELS.includes('email:free-alert'));

/* ---- 2. sign-up → one confirmation, nothing confirmed, nothing sent ---- */
let env = freshEnv();
seedArrival(env, car(7001));   // already in the yard when the alert is asked for
outbox = [];
let r = await jsonOf(await signup(env, { email: EMAIL, watch: browserWatch, src: 'Reddit', cmp: 'r/Toyota', med: 'post' }));
check('sign-up accepted', r.status === 200 && r.data.state === 'confirm-sent', JSON.stringify(r.data));
check('reply carries no token and no link outside DEV', !r.data.sub && !r.data.dev_link);
check('one confirmation email', outbox.length === 1 && outbox[0].to[0] === LOWER
  && outbox[0].subject === 'Confirm your free YardScout email alert', JSON.stringify(outbox.map((m) => m.subject)));
check('it names the car and the 50 mi', /2003–2009 Toyota 4Runner is set out at a yard within 50 mi/.test(outbox[0].text), outbox[0].text.split('\n')[0]);
check('it is honest about the budget and the cadence', /can arrive late or be skipped/.test(outbox[0].text) && /same day/.test(outbox[0].text)
  && !/instant|every time/i.test(outbox[0].text + outbox[0].html));
check('honest sender', outbox[0].from === 'YardScout <hello@yardscout.io>');
let row = rows(env, 'SELECT * FROM free_email_alerts')[0];
check('address stored lowercased, unconfirmed, no active watch', row && row.email === LOWER && row.confirmed_at === null && row.watch_json === null);
check('the chosen watch is a pending COPY', JSON.parse(row.pending_json).model === '4Runner' && JSON.parse(row.pending_json).radius_mi === 50
  && !row.pending_json.includes('abc123'));
check('only the token hash is stored', /^[0-9a-f]{64}$/.test(row.confirm_hash) && !JSON.stringify(row).includes('ys_falert_'));
check('link source kept with the pending sign-up', row.pending_source === 'reddit' && row.pending_campaign === 'rtoyota' && row.pending_medium === 'post', JSON.stringify(row));
check('browser watch object untouched', JSON.stringify(browserWatch) === browserBefore);
check('no IP stored anywhere', !JSON.stringify(rows(env, 'SELECT * FROM free_email_alerts')).includes('198.51.100'));
check('nothing counted as confirmed yet', events(env, 'free-alert-confirmed').length === 0);

// Unconfirmed is never mailed, whatever lands.
outbox = [];
let d = await dispatchFreeEmailAlerts(env, [car(7002), car(7003)]);
check('no alert email before the confirmation click (double opt-in)', outbox.length === 0 && d.emails === 0 && d.matched === 0, JSON.stringify(d));

/* ---- 3. confirm: GET is a page, POST confirms once ---- */
outbox = [];
await signup(env, { email: EMAIL, watch: browserWatch });   // within the hour: rides the link already sent
check('asking again within the hour sends no second email', outbox.length === 0);
env.raw.prepare('UPDATE free_email_alerts SET confirm_sent_at = ?').run(new Date(NOW - 2 * 3600_000).toISOString());
await signup(env, { email: EMAIL, watch: browserWatch, src: 'reddit', cmp: 'r/Toyota', med: 'post' });
check('after the hour a new confirmation goes out', outbox.length === 1);
const t = tokenFrom(outbox[0]);
check('confirmation link present', /^ys_falert_/.test(t), t.slice(0, 12));
const pageUrl = new URL('https://api.test/v1/free-alert/confirm?t=' + encodeURIComponent(t));
let res = await handleFreeAlertConfirmPage(new Request(pageUrl), env, pageUrl);
let html = await res.text();
check('GET confirm: a page with a button that names the car, confirms nothing', res.status === 200 && /<form method="post"/.test(html)
  && /2003–2009 Toyota 4Runner<\/strong>, set out within 50 mi/.test(html) && rows(env, 'SELECT confirmed_at FROM free_email_alerts')[0].confirmed_at === null);
check('the page masks the address', html.includes('v•••@example.com') && !html.includes(LOWER));
res = await confirmPost(env, t);
const loc = decodeURIComponent(res.headers.get('location') || '');
check('POST confirm → 303 to the app with the browser token', res.status === 303 && /^https:\/\/yardscout\.io\/#falert=confirmed&sub=[A-Za-z0-9_-]+\.[0-9a-f]{64}$/.test(loc), loc);
const SUB = loc.split('sub=')[1];
check('the token is the Monday email\'s token scheme (reused, not a second one)', SUB === await recapSubToken(env, LOWER));
row = rows(env, 'SELECT * FROM free_email_alerts')[0];
check('confirmed: the pending copy is now THE watch', row.confirmed_at && JSON.parse(row.watch_json).model === '4Runner' && row.pending_json === null && row.confirm_hash === null);
check('link source cleared at the click', row.pending_source === null && row.pending_campaign === null && row.pending_medium === null);
check('"confirmed" counted once, under the link', JSON.stringify(events(env, 'free-alert-confirmed')) === JSON.stringify([{ source: 'reddit', n: 1 }]), JSON.stringify(events(env, 'free-alert-confirmed')));
res = await confirmPost(env, t);
check('the link works once', res.status === 400 && events(env, 'free-alert-confirmed')[0].n === 1);
check('cars already in the yard are seeded as known (future arrivals only)',
  rows(env, 'SELECT vehicle_id FROM free_email_alerts_sent').map((x) => x.vehicle_id).join() === '7001');

/* ---- 4. a scan: one email, inside 50 mi only, deduped ---- */
outbox = [];
const arrivals1 = [
  car(7001),                                                    // was already there: seeded
  car(7010, northOf(20)),                                       // 20 mi: in
  car(7011, { ...northOf(49), location: 'Edge Yard - Ogden' }), // 49 mi: in
  car(7012, { ...northOf(60), location: 'Far Yard - Logan' }),  // 60 mi: past the free 50 (the watch said 250)
  car(7013, { model: 'Tacoma' }),                               // another model
  car(7014, { year: 2015 }),                                    // outside the years
];
d = await dispatchFreeEmailAlerts(env, arrivals1);
check('one email for the scan', outbox.length === 1 && d.emails === 1 && d.matched === 1 && d.held === 0, JSON.stringify(d));
const mail = outbox[0] || { text: '', html: '', headers: {} };
check('it lists the two cars inside 50 mi', /#car=7010/.test(mail.text) && /#car=7011/.test(mail.text));
check('not the one 60 mi out, the other model, the other year, or the car that was already there',
  !/7012|7013|7014|7001/.test(mail.text + mail.html), mail.text);
check('subject says what and where, never "instant"', mail.subject === '2 new: Toyota 4Runner within 50 mi' && !/instant/i.test(mail.subject + mail.text + mail.html), mail.subject);
check('copy says "same day"', /same day a car is listed/.test(mail.text) && /same day a car is listed/.test(mail.html));
check('sent from the alerts sender', mail.from === 'YardScout Alerts <alerts@yardscout.io>', mail.from);
const unsub = await freeAlertUnsubUrl(env, LOWER);
check('signed one-click unsubscribe link in the body', mail.text.includes(unsub) && mail.html.includes(unsub.replace(/&/g, '&amp;')));
check('List-Unsubscribe headers, exactly like the Pro emails', mail.headers && mail.headers['List-Unsubscribe'] === `<${unsub}>`
  && mail.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click', JSON.stringify(mail.headers));
check('one Pro line, no price', (mail.text.match(/Pro alerts you on every watch/g) || []).length === 1 && !/\$\d/.test(mail.text + mail.html));
check('it says why it came', /because you asked for a free email alert at yardscout\.io and confirmed visitor\.one@example\.com/.test(mail.text));
check('"first email sent" counted once', events(env, 'free-alert-first-email').length === 1 && events(env, 'free-alert-first-email')[0].n === 1);
row = rows(env, 'SELECT * FROM free_email_alerts')[0];
check('last/first email stamped', !!row.last_email_at && !!row.first_email_at);

outbox = [];
d = await dispatchFreeEmailAlerts(env, arrivals1);
check('the same cars again (overlapping scan): no second email', outbox.length === 0 && d.emails === 0);
d = await dispatchFreeEmailAlerts(env, [car(7010, northOf(20)), car(7020, northOf(5))]);
check('a later scan with one new car: one email, the new car only', outbox.length === 1 && /#car=7020/.test(outbox[0].text) && !/7010/.test(outbox[0].text)
  && outbox[0].subject === 'New: 2005 Toyota 4Runner at Test Yard - Salt Lake', outbox[0] && outbox[0].subject);
check('"first email sent" is still 1', events(env, 'free-alert-first-email')[0].n === 1);
// Many cars in one scan: still one email.
outbox = [];
d = await dispatchFreeEmailAlerts(env, Array.from({ length: 40 }, (_, i) => car(7100 + i, northOf(3))));
check('40 new cars in one scan: ONE email, 10 listed, the rest counted', outbox.length === 1 && (outbox[0].text.match(/#car=/g) || []).length === 10
  && /and 30 more on the site/.test(outbox[0].text));
check('all 40 are marked sent', rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE vehicle_id >= 7100 AND vehicle_id < 7140')[0].n === 40);

/* ---- 5. one watch per address: a different car replaces, after ITS click ---- */
outbox = [];
const civic = { make: 'Honda', model: 'Civic', yrMin: null, yrMax: null, radiusMi: 50, ...SLC };
r = await jsonOf(await signup(env, { email: EMAIL, watch: civic }));   // anyone could type this address: no token
check('a different car without the token: same reply, a confirmation email', r.status === 200 && r.data.state === 'confirm-sent' && outbox.length === 1);
check('the confirmation says it replaces the current alert', /This replaces your current alert \(2003–2009 Toyota 4Runner\)/.test(outbox[0].text)
  && /Nothing changes until you confirm/.test(outbox[0].text));
check('still ONE row for the address', rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 1);
const civicToken = tokenFrom(outbox[0]);
outbox = [];
d = await dispatchFreeEmailAlerts(env, [car(7200, { make: 'Honda', model: 'Civic' }), car(7201, northOf(2))]);
check('before the click the old watch still alerts, the new one does not', outbox.length === 1 && /7201/.test(outbox[0].text) && !/7200/.test(outbox[0].text));
res = await confirmPost(env, civicToken);
row = rows(env, 'SELECT * FROM free_email_alerts')[0];
check('after the click the Civic is THE watch (replaced, still one row)', res.status === 303 && JSON.parse(row.watch_json).model === 'Civic'
  && rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 1);
check('"confirmed" is not counted twice for one address', events(env, 'free-alert-confirmed')[0].n === 1);
outbox = [];
d = await dispatchFreeEmailAlerts(env, [car(7210, { make: 'Honda', model: 'Civic' }), car(7211, northOf(2))]);
check('now only the Civic alerts', outbox.length === 1 && /7210/.test(outbox[0].text) && !/7211/.test(outbox[0].text), outbox[0] && outbox[0].text);

/* ---- 6. the browser token: change the car with no email; status; off ---- */
outbox = [];
r = await jsonOf(await signup(env, { email: EMAIL, watch: { make: 'Subaru', model: 'Outback', radiusMi: 25, ...SLC }, sub: SUB }));
check('with the token the car changes at once, no email', r.status === 200 && r.data.state === 'on' && outbox.length === 0
  && r.data.watch.model === 'Outback' && r.data.watch.radiusMi === 25, JSON.stringify(r.data));
check('the reply never carries the centre', !('lat' in r.data.watch) && !JSON.stringify(r.data).includes('40.76'));
check('still one row, one watch', rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 1
  && JSON.parse(rows(env, 'SELECT watch_json FROM free_email_alerts')[0].watch_json).model === 'Outback');
const otherSub = await recapSubToken(env, 'someone.else@example.com');
outbox = [];
r = await jsonOf(await signup(env, { email: EMAIL, watch: civic, sub: otherSub }));
check('(this address has had its 3 confirmation emails today: a 4th ask is refused)', r.status === 429 && r.data.error === 'too_many' && outbox.length === 0, JSON.stringify(r));
env.raw.prepare('UPDATE free_email_alerts SET confirm_sends = 0').run();   // another day
r = await jsonOf(await signup(env, { email: EMAIL, watch: civic, sub: otherSub }));
check("someone else's token changes nothing: the ask goes to the inbox as a confirmation", r.status === 200 && r.data.state === 'confirm-sent' && !r.data.sub && outbox.length === 1, JSON.stringify(r));
check('...and the watch is still the Outback', JSON.parse(rows(env, 'SELECT watch_json FROM free_email_alerts')[0].watch_json).model === 'Outback');
r = await jsonOf(await handleFreeAlertStatus(post('/v1/free-alert/status', { sub: SUB }), env));
check('status: on, with the watch, without the centre or the address', r.data.state === 'on' && r.data.watch.make === 'Subaru'
  && !/lat|lng|example\.com/.test(JSON.stringify(r.data)), JSON.stringify(r.data));
r = await jsonOf(await handleFreeAlertStatus(post('/v1/free-alert/status', { sub: 'garbage' }), env));
check('status without a valid token: 401', r.status === 401);
r = await jsonOf(await handleFreeAlertOff(post('/v1/free-alert/off', { sub: SUB }), env));
check('"Turn off" deletes the address and its dedupe rows', r.data.state === 'off' && rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 0
  && rows(env, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent')[0].n === 0);
r = await jsonOf(await handleFreeAlertStatus(post('/v1/free-alert/status', { sub: SUB }), env));
check('status after: off', r.data.state === 'off');
outbox = [];
r = await jsonOf(await signup(env, { email: EMAIL, watch: civic, sub: SUB }));
check('an old token does not bring a removed address back without a new confirmation', r.data.state === 'confirm-sent' && outbox.length === 1
  && rows(env, 'SELECT confirmed_at FROM free_email_alerts')[0].confirmed_at === null);
d = await dispatchFreeEmailAlerts(env, [car(7300, { make: 'Honda', model: 'Civic' })]);
check('...and nothing is mailed to it meanwhile', d.emails === 0);

/* ---- 7. an address confirmed for the Monday email in this browser ---- */
{
  const e = freshEnv();
  outbox = [];
  await handleRecapSignup(post('/v1/recap/signup', { email: 'monday@example.com', watch: { make: 'Toyota', model: 'Tacoma', ...SLC, radiusMi: 100 } }), e, nextIp());
  const rt = decodeURIComponent((outbox[0].text.match(/\/v1\/recap\/confirm\?t=([^\s]+)/) || [])[1]);
  const cr = await handleRecapConfirm(new Request('https://api.test/v1/recap/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(rt) }), e);
  const mondaySub = decodeURIComponent(cr.headers.get('location')).split('sub=')[1];
  outbox = [];
  const rr = await jsonOf(await signup(e, { email: 'monday@example.com', watch: browserWatch, sub: mondaySub, src: 'page' }));
  check('Monday-email token for the same address: alert on with no second confirmation email', rr.data.state === 'on' && outbox.length === 0, JSON.stringify(rr.data));
  check('...counted as confirmed, under this visit\'s link', JSON.stringify(events(e, 'free-alert-confirmed')) === JSON.stringify([{ source: 'page', n: 1 }]));
  const dd = await dispatchFreeEmailAlerts(e, [car(7400)]);
  check('...and it is mailed', dd.emails === 1 && outbox.length === 1 && outbox[0].to[0] === 'monday@example.com');
  // The two lists unsubscribe separately.
  const mondayUnsub = new URL(await recapUnsubUrl(e, 'monday@example.com'));
  const bad = await handleFreeAlertUnsubscribe(new Request(mondayUnsub.href.replace('/v1/recap/', '/v1/free-alert/')), e, new URL(mondayUnsub.href.replace('/v1/recap/', '/v1/free-alert/')));
  check('a Monday-email unsubscribe signature does not unsubscribe the alert (own key)', bad.status === 400 && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 1);
  await flushOps(e);
}

/* ---- 8. unsubscribe link: one click deletes ---- */
{
  const e = freshEnv();
  await optIn(e, 'leaver@example.com', browserWatch);
  await dispatchFreeEmailAlerts(e, [car(7500)]);
  check('(setup) mailed once', outbox.length === 1 && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent')[0].n === 1);
  const u = new URL(outbox[0].headers['List-Unsubscribe'].slice(1, -1));
  const tampered = new URL(u.href.replace(/sig=[0-9a-f]{4}/, 'sig=0000'));
  let x = await handleFreeAlertUnsubscribe(new Request(tampered, { method: 'POST' }), e, tampered);
  check('a tampered link is refused', x.status === 400 && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 1);
  x = await handleFreeAlertUnsubscribe(new Request(u, { method: 'POST' }), e, u);
  check('POST (RFC 8058 one-click) deletes the address, its watch and its dedupe rows', x.status === 200 && (await x.json()).unsubscribed === true
    && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 0 && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent')[0].n === 0);
  outbox = [];
  const dd = await dispatchFreeEmailAlerts(e, [car(7501)]);
  check('nothing is sent after unsubscribing', dd.emails === 0 && outbox.length === 0);
  await optIn(e, 'leaver2@example.com', browserWatch);
  const u2 = new URL(await freeAlertUnsubUrl(e, 'leaver2@example.com'));
  x = await handleFreeAlertUnsubscribe(new Request(u2), e, u2);
  const body = await x.text();
  check('GET shows a page (masked address) and deletes too', x.status === 200 && /You're unsubscribed/.test(body) && body.includes('l•••@example.com')
    && !body.includes('leaver2@') && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 0);
  await flushOps(e);
}

/* ---- 9. the budget: per scan, per day, the reserve; held = counted, kept, retried ---- */
check('limits at the free tier cap of 100: 20 a day, none once 70 have gone out',
  JSON.stringify(freeAlertLimits({})) === JSON.stringify({ cap: 100, dayMax: 20, reserve: 30 }), JSON.stringify(freeAlertLimits({})));
check('the reserve is always above the optional-mail reserve', [12, 14, 40, 100, 1000].every((c) => freeAlertLimits({ RESEND_DAILY_CAP: String(c) }).reserve > RESEND_RESERVE));
check('per scan cap is 5', FREE_ALERT_MAX_PER_SCAN === 5);
{
  await flushOps(env);
  const e = freshEnv();
  const who = Array.from({ length: 7 }, (_, i) => `scan${i}@example.com`);
  for (const w of who) await optIn(e, w, browserWatch);
  await flushOps(e);
  e.raw.prepare("DELETE FROM ops_counters").run();   // the 7 confirmations are not what is measured here
  const fresh = [car(8001, northOf(4))];
  await storeArrivals(e, fresh);                      // as the commit hook does (the catch-up reads this table)
  outbox = [];
  let dd = await dispatchFreeEmailAlerts(e, fresh);
  check('7 addresses matched one scan: 5 emails, 2 held', dd.matched === 7 && dd.emails === 5 && dd.held === 2 && outbox.length === 5, JSON.stringify(dd));
  check('each address got exactly one', new Set(outbox.map((m) => m.to[0])).size === 5);
  await flushOps(e);
  check('held is counted for the ops email (email:free-alert:held = 2)', rows(e, "SELECT n FROM ops_counters WHERE metric = 'email:free-alert:held'")[0]?.n === 2);
  check('sent is counted (email:free-alert:ok = 5)', rows(e, "SELECT n FROM ops_counters WHERE metric = 'email:free-alert:ok'")[0]?.n === 5);
  const heldRows = rows(e, 'SELECT email FROM free_email_alerts WHERE held_at IS NOT NULL').map((x) => x.email);
  check('the 2 held addresses are flagged, their car NOT marked sent', heldRows.length === 2
    && heldRows.every((h) => rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE email = ? AND vehicle_id = ?', h, '8001')[0].n === 0));
  outbox = [];
  dd = await dispatchFreeEmailAlerts(e, []);   // the next scan brings nothing new
  check('the next scan delivers the 2 held alerts (and only those)', dd.emails === 2 && outbox.length === 2
    && outbox.map((m) => m.to[0]).sort().join() === heldRows.sort().join() && outbox.every((m) => /#car=8001/.test(m.text)), JSON.stringify(dd));
  check('nobody was mailed twice for the car', rows(e, "SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE vehicle_id = '8001'")[0].n === 7);
  check('held flags cleared after sending', rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts WHERE held_at IS NOT NULL')[0].n === 0);
  await flushOps(e);
  check('"first email sent" counted for all 7, once each', events(e, 'free-alert-first-email')[0].n === 7);

  // Per day: 20 free alert emails, then held.
  e.raw.prepare("UPDATE ops_counters SET n = 20 WHERE metric = 'email:free-alert:ok'").run();
  const b = await freeAlertBudget(e);
  check('budget: 20 free alerts sent today → 0 left', b.left === 0 && b.free === 20 && b.dayMax === 20, JSON.stringify(b));
  outbox = [];
  const fresh2 = [car(8002, northOf(4))];
  await storeArrivals(e, fresh2);
  dd = await dispatchFreeEmailAlerts(e, fresh2);
  check('at the daily cap: nothing sent, all 7 held and counted', dd.emails === 0 && dd.held === 7 && outbox.length === 0, JSON.stringify(dd));
  dd = await dispatchFreeEmailAlerts(e, []);
  check('still over budget on the next scan: nothing sent, and not counted again', dd.emails === 0 && dd.held === 0 && dd.matched === 7, JSON.stringify(dd));
  await flushOps(e);
  check('held counter = 2 + 7 (once per held stretch)', rows(e, "SELECT n FROM ops_counters WHERE metric = 'email:free-alert:held'")[0]?.n === 9);
  check('nothing was marked sent while held', rows(e, "SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE vehicle_id = '8002'")[0].n === 0);

  // The reserve: other mail has used the day. Free alerts stop at 70, while
  // optional mail (confirmations) is still allowed until 90.
  e.raw.prepare("UPDATE ops_counters SET n = 0 WHERE metric = 'email:free-alert:ok'").run();
  e.raw.prepare("INSERT INTO ops_counters (day, metric, n) VALUES (?, 'email:pro-alert:ok', 70)").run(new Date().toISOString().slice(0, 10));
  const b2 = await freeAlertBudget(e);
  check('budget: 70 emails of any kind today → 0 left for free alerts', b2.left === 0 && b2.total >= 70, JSON.stringify(b2));
  check('...while confirmations and recaps are still allowed (they stop at 90)', await optionalEmailAllowed(e) === true);
  outbox = [];
  dd = await dispatchFreeEmailAlerts(e, []);
  check('inside the reserve: free alerts wait, nothing sent', dd.emails === 0 && outbox.length === 0);
  e.raw.prepare("UPDATE ops_counters SET n = 67 WHERE metric = 'email:pro-alert:ok'").run();
  dd = await dispatchFreeEmailAlerts(e, []);
  check('3 sends above the reserve: exactly 3 go out, the rest stay held', dd.emails === 3 && outbox.length === 3, JSON.stringify(dd));

  // After 48 h a held car is no longer emailed.
  e.raw.prepare("DELETE FROM ops_counters").run();
  outbox = [];
  dd = await dispatchFreeEmailAlerts(e, [], { now: Date.now() + FREE_ALERT_CATCHUP_MS + 3600_000 });
  check('a held alert older than 48 h is not sent', dd.emails === 0 && outbox.length === 0, JSON.stringify(dd));

  // Counters unreadable → the lowest class does not send blind.
  const broken = { ...e, DB: { ...e.DB, prepare: (sql) => (/ops_counters/.test(sql) ? { bind: () => ({ all: async () => { throw new Error('d1 down'); } }) } : e.DB.prepare(sql)) } };
  check('budget unreadable → 0 left', (await freeAlertBudget(broken)).left === 0);
  await flushOps(e);
}

/* ---- 10. a failed send is not marked sent ---- */
{
  const e = freshEnv();
  await optIn(e, 'bounce@example.com', browserWatch);
  resendStatus = 422;
  let dd = await dispatchFreeEmailAlerts(e, [car(8101)]);
  resendStatus = 200;
  check('Resend refused: counted as failed, nothing marked sent', dd.failed === 1 && dd.emails === 0
    && rows(e, 'SELECT COUNT(*) AS n FROM free_email_alerts_sent')[0].n === 0 && rows(e, 'SELECT first_email_at FROM free_email_alerts')[0].first_email_at === null);
  await flushOps(e);
  check('...and it shows as a failure for the ops check', rows(e, "SELECT n FROM ops_counters WHERE metric = 'email:free-alert:fail'")[0]?.n === 1);
}

/* ---- 11. Pro email alerts on for the same address: no second email ---- */
{
  const e = freshEnv();
  await optIn(e, 'pro@example.com', browserWatch);
  await optIn(e, 'lapsed@example.com', browserWatch);
  const nowIso = new Date().toISOString();
  for (const em of ['pro@example.com', 'lapsed@example.com']) {
    e.raw.prepare("INSERT INTO email_watchers (email, watches_json, enabled, created_at, updated_at) VALUES (?, '[]', 1, ?, ?)").run(em, nowIso, nowIso);
  }
  e.kv.set('ent:pro@example.com', JSON.stringify({ pro: true, expiresAt: null }));
  e.kv.set('ent:lapsed@example.com', JSON.stringify({ pro: true, expiresAt: '2020-01-01T00:00:00Z' }));
  outbox = [];
  const dd = await dispatchFreeEmailAlerts(e, [car(8201)]);
  check('an active Pro address with email alerts on is left to the Pro email', !outbox.some((m) => m.to[0] === 'pro@example.com'));
  check('a lapsed Pro address still gets its free alert', outbox.some((m) => m.to[0] === 'lapsed@example.com') && dd.emails === 1, JSON.stringify(dd));
  await flushOps(e);
}

/* ---- 12. abuse limits (shared with the Monday email) ---- */
{
  const e = freshEnv();
  let limited = 0;
  for (let i = 0; i < 10; i++) {
    const x = await signup(e, { email: `ip${i}@example.com`, watch: browserWatch }, '203.0.113.9');
    if (x.status === 429) limited++;
  }
  check('per-IP sign-up limit: 8 an hour, then 429', limited === 2, `limited=${limited}`);
  let x = await handleRecapSignup(post('/v1/recap/signup', { email: 'ipx@example.com', watch: { make: 'Toyota', ...SLC, radiusMi: 50 } }), e, '203.0.113.9');
  check('...one bucket with the Monday email sign-up (same IP is still limited there)', x.status === 429);
  outbox = [];
  for (let i = 0; i < 4; i++) {
    e.raw.prepare("UPDATE free_email_alerts SET confirm_sent_at = ? WHERE email = 'three@example.com'").run(new Date(NOW - 2 * 3600_000).toISOString());
    x = await jsonOf(await signup(e, { email: 'three@example.com', watch: browserWatch }));
  }
  check('4th confirmation in a day refused (3/day per address)', outbox.length === 3 && x.status === 429 && x.data.error === 'too_many', `${outbox.length} ${x.status}`);
  x = await jsonOf(await signup(e, { email: 'not-an-address', watch: browserWatch }));
  check('a bad address is refused', x.status === 400 && x.data.error === 'bad_email');
  x = await jsonOf(await signup(e, { email: 'ok@example.com', watch: { make: 'Toyota' } }));
  check('a watch with no centre is refused', x.status === 400 && x.data.error === 'bad_watch');
  await flushOps(e);

  // The sender's daily cap: confirmations are optional mail.
  const c = freshEnv({ RESEND_DAILY_CAP: '12' });
  c.raw.prepare("INSERT INTO ops_counters (day, metric, n) VALUES (?, 'email:auth:ok', 2)").run(new Date().toISOString().slice(0, 10));
  outbox = [];
  x = await jsonOf(await signup(c, { email: 'late@example.com', watch: browserWatch }));
  check('at the cap a sign-up is refused with the reason, nothing stored, nothing sent', x.status === 503 && x.data.error === 'daily_cap'
    && outbox.length === 0 && rows(c, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 0, JSON.stringify(x));
  await flushOps(c);
  check('...and the held confirmation is counted', rows(c, "SELECT n FROM ops_counters WHERE metric = 'email:confirm:held'")[0]?.n === 1);

  // Resend refuses the confirmation: nothing is kept for a new address.
  const f = freshEnv();
  resendStatus = 500;
  x = await jsonOf(await signup(f, { email: 'nosend@example.com', watch: browserWatch }));
  resendStatus = 200;
  check('confirmation could not be sent: 502 and no row kept', x.status === 502 && rows(f, 'SELECT COUNT(*) AS n FROM free_email_alerts')[0].n === 0);
  const nokey = freshEnv({ EMAIL_UNSUB_SECRET: '' });
  x = await jsonOf(await signup(nokey, { email: 'a@example.com', watch: browserWatch }));
  check('no signing secret (production) → 503 not_configured', x.status === 503 && x.data.error === 'not_configured');
  await flushOps(f);
}

/* ---- 13. within the hour the newest choice rides the link already sent ---- */
{
  const e = freshEnv();
  outbox = [];
  await signup(e, { email: 'two@example.com', watch: browserWatch });
  await signup(e, { email: 'two@example.com', watch: civic });
  check('two asks within the hour: one email', outbox.length === 1);
  const u = new URL('https://api.test/v1/free-alert/confirm?t=' + encodeURIComponent(tokenFrom(outbox[0])));
  const pg = await (await handleFreeAlertConfirmPage(new Request(u), e, u)).text();
  check('the confirm page names the car that will actually be set (the newest)', /Honda Civic<\/strong>/.test(pg) && !/4Runner/.test(pg));
  await confirmPost(e, tokenFrom(outbox[0]));
  check('...and that is the one watch', JSON.parse(rows(e, 'SELECT watch_json FROM free_email_alerts')[0].watch_json).model === 'Civic');
  await flushOps(e);
}

/* ---- 14. prune: unconfirmed after 7 days; an unconfirmed change expires ---- */
{
  const e = freshEnv();
  await signup(e, { email: 'never@example.com', watch: browserWatch });
  await optIn(e, 'stays@example.com', browserWatch);
  e.raw.prepare("UPDATE free_email_alerts SET confirm_sent_at = ? WHERE email = 'stays@example.com'").run(new Date(NOW - 2 * 3600_000).toISOString());
  await signup(e, { email: 'stays@example.com', watch: civic });   // a change nobody confirms
  await pruneFreeAlerts(e, Date.now() + 6 * 86400_000);
  check('day 6: the unconfirmed address is still there', rows(e, "SELECT COUNT(*) AS n FROM free_email_alerts WHERE email = 'never@example.com'")[0].n === 1);
  await pruneFreeAlerts(e, Date.now() + 8 * 86400_000);
  check('day 8: the unconfirmed address is deleted', rows(e, "SELECT COUNT(*) AS n FROM free_email_alerts WHERE email = 'never@example.com'")[0].n === 0);
  const s = rows(e, "SELECT * FROM free_email_alerts WHERE email = 'stays@example.com'")[0];
  check('a confirmed address stays, its alert unchanged, the expired change dropped', s && JSON.parse(s.watch_json).model === '4Runner' && s.pending_json === null && s.confirm_hash === null);
  const st = await freeAlertStats(e);
  check('stats for the ops email (no addresses)', st.on === 1 && st.pending === 0 && st.mailed === 0 && !JSON.stringify(st).includes('@'), JSON.stringify(st));
  await flushOps(e);
}

/* ---- 15. the commit hook: after the Pro emails, also with no new arrivals ---- */
{
  const e = freshEnv();
  await optIn(e, 'hook@example.com', browserWatch);
  const waits = [];
  const ctx = { waitUntil: (p) => waits.push(p) };
  const commit = (newArrivals) => handleCommit(post('/v1/admin/inventory/commit', {
    directory: { yards: [['Test Yard - Salt Lake', 'Salt Lake City', 'UT', 40.7, -111.9]], fields: ['id'], scrapedAt: new Date().toISOString() },
    manifest: {}, newArrivals }), e, ctx);
  outbox = [];
  let cr = await commit([car(9001)]);
  await Promise.all(waits);
  check('a scan commit sends the free alert', cr.status === 200 && outbox.filter((m) => m.to[0] === 'hook@example.com').length === 1);
  const order = logged.filter((l) => /^email alerts: |^free email alerts: /.test(l)).slice(-2).map((l) => l.split(':')[0]);
  check('...after the Pro email dispatch of the same commit', order.join(' > ') === 'email alerts > free email alerts', order.join(' > '));
  outbox = [];
  waits.length = 0;
  cr = await commit([]);
  await Promise.all(waits);
  check('a commit with no new cars runs it too (held alerts can go out), and sends nothing new', cr.status === 200 && outbox.length === 0
    && logged.some((l) => /^free email alerts: 0 emailed of 0 matched/.test(l)));
  await flushOps(e);
}

/* ---- 16. a quiet scan costs one statement ---- */
{
  const e = freshEnv();
  statements = 0;
  await dispatchFreeEmailAlerts(e, [car(9101)]);
  check('nobody signed up: one D1 statement per scan', statements === 1, String(statements));
  await optIn(e, 'quiet@example.com', browserWatch);
  statements = 0;
  await dispatchFreeEmailAlerts(e, [car(9102, { model: 'Tacoma' })]);
  check('a scan that matches nobody: still one statement', statements === 1, String(statements));
  statements = 0;
  outbox = [];
  await dispatchFreeEmailAlerts(e, [car(9103)]);
  check('one address mailed: 4 statements (rows, dedupe+Pro, budget, mark sent)', statements === 4 && outbox.length === 1, String(statements));
  await flushOps(e);
}

/* ---- 17. the two server-counted events cannot be posted by a client ---- */
{
  const e = freshEnv();
  const evPost = (b) => handleEvent(new Request('https://api.test/v1/events', { method: 'POST', body: JSON.stringify(b) }), e);
  check('a client may post "free-alert-shown" and "free-alert-asked"', (await evPost({ e: 'free-alert-shown', p: 'web' })).status === 200
    && (await evPost({ e: 'free-alert-asked', p: 'web' })).status === 200);
  check('...but not "free-alert-confirmed" or "free-alert-first-email"', (await evPost({ e: 'free-alert-confirmed', p: 'web' })).status === 400
    && (await evPost({ e: 'free-alert-first-email', p: 'web' })).status === 400);
  check('"email-confirmed" is still refused', (await evPost({ e: 'email-confirmed', p: 'web' })).status === 400);
}

/* ---- 18. pure builders ---- */
{
  const e = freshEnv({ EMAIL_POSTAL_ADDRESS: 'YardScout LLC, PO Box 1, Salt Lake City, UT 84101' });
  const w = sanitizeFreeAlertWatch({ make: 'Toyota', ...SLC, radiusMi: 100 });
  const m = buildFreeAlertEmail(e, 'a@example.com', w, [car(1, { location: '', row: '', dateAdded: null })], 'https://api.test/u');
  check('make-only watch, sparse car: builds without "undefined"/"null"', !/undefined|null/.test(m.subject + m.text + m.html), m.subject);
  check('postal line printed only when the owner set one', m.text.includes('PO Box 1') && m.html.includes('PO Box 1')
    && !buildFreeAlertEmail(freshEnv(), 'a@example.com', w, [car(1)], 'https://api.test/u').text.includes('PO Box'));
  const c = buildFreeAlertConfirmEmail(e, 'a@example.com', w, 'https://api.test/c');
  check('confirmation for a new address says it is deleted if ignored', /the address is deleted within 7 days/.test(c.text) && /Toyota is set out at a yard within 50 mi/.test(c.text));
  const x = buildFreeAlertEmail(e, 'a@example.com', w, [car(2, { make: '<b>Toy', location: 'Yard & <Sons>' })], 'https://api.test/u?a=1&b=2');
  check('HTML is escaped', !/<b>Toy|<Sons>/.test(x.html) && x.html.includes('&lt;b&gt;Toy'));
}

/* ---- 19. the nearby box never hides a car the real rule would match ---- */
{
  let seed = 20261117;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
  let missed = 0, inside = 0, kept = 0, n = 0;
  for (let i = 0; i < 400; i++) {
    const w = { make: 'Toyota', lat: 18 + rnd() * 53, lng: -170 + rnd() * 110, radius_mi: [1, 10, 25, 50][i % 4] };
    const near = nearBox(w);
    for (let k = 0; k < 60; k++) {
      // Points scattered out to about twice the radius, in every direction.
      const v = { lat: w.lat + (rnd() - 0.5) * 4 * (w.radius_mi / 69), lng: w.lng + (rnd() - 0.5) * 4 * (w.radius_mi / (69 * Math.cos(w.lat * Math.PI / 180))) };
      n++;
      const real = haversineMiles(w.lat, w.lng, v.lat, v.lng) <= w.radius_mi;
      if (real) inside++;
      if (near(v)) kept++;
      if (real && !near(v)) missed++;
    }
  }
  check('24,000 points from Hawaii to the Arctic: every car within the radius passes the box', missed === 0 && inside > 3000, `${missed} missed of ${inside}`);
  check('...and the box does its job (it drops most of the rest)', kept < n * 0.6, `${kept} of ${n}`);
  const aleut = { make: 'Toyota', lat: 52, lng: 179.95, radius_mi: 50 };
  check('across the 180th meridian too', nearBox(aleut)({ lat: 52, lng: -179.95 }) === true && haversineMiles(52, 179.95, 52, -179.95) < 50);
  check('a car with no position never passes (as in the real rule)', nearBox(aleut)({ lat: null, lng: null }) === false);
}

/* ---- 20. logs never carry a full address ---- */
/* ---- the hourly "Resend near daily cap" check names free alerts among what is held (2026-11-18) ---- */
{
  const d = resendVolumeDetail({});
  check('near-cap wording: free alert emails are named, first, at their own numbers (70 sent today, 20 a day)',
    /lowest class first: free alert emails \(web\) once 70 emails of any kind went out today \(and after 20 free alert emails/.test(d), d);
  check('near-cap wording: then confirmations (both kinds) and recaps at 10 or fewer left', /then sign-up confirmations \(Monday email and free alert\) and Monday recaps once 10 or fewer sends are left/.test(d), d);
  const big = resendVolumeDetail({ RESEND_DAILY_CAP: '1000' });
  check('near-cap wording follows RESEND_DAILY_CAP (1,000: 700 and 200)', /once 700 emails/.test(big) && /after 200 free alert emails/.test(big) && /stops at 1000\/day/.test(big), big);
  const e = freshEnv();
  e.raw.prepare("INSERT INTO ops_counters (day, metric, n) VALUES (?, 'email:pro-alert:ok', 95)").run(new Date().toISOString().slice(0, 10));
  const { conditions } = await evaluateConditions(e);
  const rv = conditions.find((c) => c.id === 'resend-volume');
  check('the hourly check fires at 95 of 100 and carries that wording', !!rv && rv.detail === d && /95 of 100/.test(rv.title), JSON.stringify(rv));
}

const leaked = logged.filter((l) => !/^(PASS|FAIL)/.test(l)).filter((l) => /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]/.test(l) && !/•••@/.test(l));
check('no full email address in any log line', leaked.length === 0, leaked.slice(0, 3).join(' | '));

console.log = origLog;
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
