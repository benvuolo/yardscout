/* Unit test: free Monday email sign-up for web visitors (src/recap_signup.js
 * and its use in alerts.js sendWeeklyDigests). Runs the real handlers
 * against an in-memory SQLite with every migration applied (a small D1
 * shim over node:sqlite) and a stubbed Resend. No Worker needed.
 * Run: node test/recap_signup_unit.mjs */
import { DatabaseSync } from 'node:sqlite';
import { readdirSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import {
  handleRecapSignup, handleRecapAdd, handleRecapConfirmPage, handleRecapConfirm, handleRecapUnsubscribe,
  sanitizeRecapWatch, maskEmail, recapUnsubUrl, recapSubToken, pruneRecap, recapStats, buildConfirmEmail,
} from '../src/recap_signup.js';
import { sendWeeklyDigests, buildDigestEmail } from '../src/alerts.js';
import { flushOps } from '../src/ops.js';
import { handleEvent } from '../src/attribution.js';

let failures = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`); if (!ok) failures++; };

/* ---- D1 shim ---- */
function d1(db) {
  const wrap = (sql, args = []) => ({
    bind: (...a) => wrap(sql, a),
    first: async () => db.prepare(sql).get(...args) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    run: async () => { const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
    _exec: () => db.prepare(sql).run(...args),
  });
  return {
    prepare: (sql) => wrap(sql),
    batch: async (stmts) => { db.exec('BEGIN'); try { for (const s of stmts) s._exec(); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); throw e; } return []; },
  };
}
function freshEnv(extra = {}) {
  const db = new DatabaseSync(':memory:');
  const dir = new URL('../migrations/', import.meta.url);
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.sql')).sort()) db.exec(readFileSync(new URL(f, dir), 'utf8'));
  const kv = new Map();
  return {
    raw: db,
    DB: d1(db),
    ENTITLEMENTS: { get: async (k) => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); }, delete: async (k) => { kv.delete(k); } },
    RESEND_API_KEY: 're_test_key', EMAIL_UNSUB_SECRET: 'unit-secret', APP_URL: 'https://yardscout.io/',
    API_PUBLIC_URL: 'https://api.test', EMAIL_FROM: 'YardScout <hello@yardscout.io>',
    ...extra,
  };
}

/* ---- Resend stub (global fetch) ---- */
let outbox = [];
globalThis.fetch = async (url, init) => {
  if (String(url) === 'https://api.resend.com/emails') {
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
const post = (path, body, ip) => new Request('https://api.test' + path, {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
const signup = (env, body, ip = '198.51.100.' + (++ipN)) => handleRecapSignup(post('/v1/recap/signup', body), env, ip);
const add = (env, body, ip = '198.51.100.' + (++ipN)) => handleRecapAdd(post('/v1/recap/add', body), env, ip);
const jsonOf = async (r) => ({ status: r.status, data: await r.json() });
const linkFrom = (mail) => (mail.text.match(/https:\/\/api\.test\/v1\/recap\/confirm\?t=([^\s]+)/) || [])[1];
const confirmPost = (env, t) => handleRecapConfirm(new Request('https://api.test/v1/recap/confirm', {
  method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + t }), env);
const rows = (env, sql, ...a) => env.raw.prepare(sql).all(...a);

const EMAIL = 'Visitor.One@Example.com';
const LOWER = EMAIL.toLowerCase();
// What the browser holds: the watch as docs/app.js stores it.
const browserWatch = { make: 'Chevrolet', model: 'Equinox', yrMin: 2010, yrMax: 2017, matchOnly: false, radiusMi: 50,
  lat: 40.76012, lng: -111.89123, addedAt: '2026-11-12T10:00:00.000Z~abc123', driveFilter: 'AWD', trimFilter: 'LTZ' };
const browserBefore = JSON.stringify(browserWatch);

/* ---- 1. sanitize: free criteria only, centre rounded, radius capped ---- */
const sw = sanitizeRecapWatch(browserWatch);
check('copy keeps make/model/years/centre/radius', sw && sw.make === 'Chevrolet' && sw.model === 'Equinox'
  && sw.year_min === 2010 && sw.year_max === 2017 && sw.radius_mi === 50, JSON.stringify(sw));
check('centre rounded to ~1 km', sw.lat === 40.76 && sw.lng === -111.89, `${sw.lat},${sw.lng}`);
check('Pro trim/drive filters are not copied', !('drive_filter' in sw) && !('trim_filter' in sw) && !JSON.stringify(sw).includes('LTZ'));
check('no centre → refused', sanitizeRecapWatch({ make: 'Honda', model: 'Civic' }) === null);
check('radius capped at the free 250 mi', sanitizeRecapWatch({ make: 'Honda', lat: 1, lng: 1, radiusMi: 900 }).radius_mi === 250);
check('maskEmail', maskEmail('benvuolo@gmail.com') === 'b•••@gmail.com', maskEmail('benvuolo@gmail.com'));

/* ---- 2. signup → one confirmation, nothing confirmed yet ---- */
let env = freshEnv();
outbox = [];
let r = await jsonOf(await signup(env, { email: EMAIL, watch: browserWatch }));
check('signup accepted', r.status === 200 && r.data.state === 'confirm-sent', JSON.stringify(r.data));
check('one confirmation email sent', outbox.length === 1 && outbox[0].to[0] === LOWER
  && outbox[0].subject === 'Confirm your free YardScout Monday email', JSON.stringify(outbox.map((m) => m.subject)));
check('confirmation lists the watch', /2010–2017 Chevrolet Equinox, within 50 mi/.test(outbox[0].text), outbox[0].text.split('\n')[2]);
check('honest sender', outbox[0].from === 'YardScout <hello@yardscout.io>');
let sub = rows(env, 'SELECT * FROM recap_subscribers')[0];
check('address stored lowercased, unconfirmed', sub && sub.email === LOWER && sub.confirmed_at === null);
check('only the token hash is stored', sub.confirm_hash && /^[0-9a-f]{64}$/.test(sub.confirm_hash)
  && !rows(env, 'SELECT * FROM recap_subscribers').some((x) => JSON.stringify(x).includes('ys_recap_')));
const stored = rows(env, 'SELECT * FROM recap_watches');
check('criteria COPIED (own row, pending), not referenced', stored.length === 1 && stored[0].make === 'Chevrolet'
  && stored[0].confirmed_at === null && !JSON.stringify(stored[0]).includes('abc123'), JSON.stringify(stored[0]));
check('browser watch object untouched', JSON.stringify(browserWatch) === browserBefore);
check('no IP stored anywhere', !JSON.stringify(rows(env, 'SELECT * FROM recap_subscribers')).includes('198.51.100'));

// Nothing goes out before the confirmation click.
const NOW = Date.now();
const car = (id, extra = {}) => ({ id, year: 2014, make: 'Chevrolet', model: 'Equinox', row: '12',
  location: 'Test Yard - Salt Lake', lat: 40.7, lng: -111.9, dateAdded: new Date(NOW).toISOString().slice(0, 10), ...extra });
const seedArrival = (e, v) => e.raw.prepare(
  `INSERT INTO arrivals (vehicle_id, year, make, model, row, location, city, state, lat, lng, date_added, seen_at, vpic_json)
   VALUES (?, ?, ?, ?, ?, ?, '', 'UT', ?, ?, ?, ?, NULL)`).run(String(v.id), v.year, v.make, v.model, v.row, v.location, v.lat, v.lng, v.dateAdded, new Date(NOW - 2 * 86400_000).toISOString());
seedArrival(env, car(7001));
seedArrival(env, car(7002, { lat: 33.4, lng: -112.0, location: 'Far Yard - Phoenix' }));   // outside 50 mi
outbox = [];
let pv = [];
let wk = await sendWeeklyDigests(env, { now: NOW, previews: pv });
check('no recap before confirmation (double opt-in)', wk.emails === 0 && outbox.length === 0, JSON.stringify(wk));

/* ---- 3. a second watch within the hour rides the same link ---- */
outbox = [];
r = await jsonOf(await signup(env, { email: EMAIL, watch: { make: 'Honda', model: 'Civic', radiusMi: 50, lat: 40.76, lng: -111.89 } }));
check('second watch accepted, no second email within the hour', r.status === 200 && outbox.length === 0);
check('two pending copies', rows(env, 'SELECT * FROM recap_watches WHERE confirmed_at IS NULL').length === 2);

/* ---- 4. confirm: GET is a page (scanners do not opt in), POST confirms ---- */
env.raw.prepare("UPDATE recap_subscribers SET confirm_sent_at = ?").run(new Date(NOW - 2 * 3600_000).toISOString());
outbox = [];
r = await jsonOf(await signup(env, { email: EMAIL, watch: browserWatch }));
check('after the hour a new confirmation goes out (lists both)', outbox.length === 1 && /Honda Civic/.test(outbox[0].text) && /Equinox/.test(outbox[0].text));
const t = decodeURIComponent(linkFrom(outbox[0]) || '');
check('confirmation link present', /^ys_recap_/.test(t), t.slice(0, 12));
const pageRes = await handleRecapConfirmPage(new Request('https://api.test/v1/recap/confirm?t=' + t), env, new URL('https://api.test/v1/recap/confirm?t=' + encodeURIComponent(t)));
const pageHtml = await pageRes.text();
check('GET confirm shows a button and confirms nothing', pageRes.status === 200 && /<form method="post"/.test(pageHtml)
  && rows(env, 'SELECT confirmed_at FROM recap_subscribers')[0].confirmed_at === null);
check('confirm page masks the address', !pageHtml.includes(LOWER) && pageHtml.includes('v•••@example.com'));
const conf = await confirmPost(env, encodeURIComponent(t));
const loc = conf.headers.get('location') || '';
check('POST confirm → 303 to the app with a sub token', conf.status === 303 && loc.startsWith('https://yardscout.io/#recap=confirmed&sub='), loc.slice(0, 60));
check('subscriber and both watches confirmed', rows(env, 'SELECT * FROM recap_subscribers')[0].confirmed_at
  && rows(env, 'SELECT * FROM recap_watches WHERE confirmed_at IS NULL').length === 0);
check('"email confirmed" counted once, server side', rows(env, "SELECT n FROM events_daily WHERE event = 'email-confirmed'")[0]?.n === 1);
const again = await confirmPost(env, encodeURIComponent(t));
check('confirmation link is single-use', again.status === 400);
check('expired/used link page on GET', (await handleRecapConfirmPage(null, env, new URL('https://api.test/v1/recap/confirm?t=' + encodeURIComponent(t)))).status === 400);

/* ---- 5. Monday recap contains the car, with unsubscribe link + headers ---- */
outbox = [];
pv = [];
wk = await sendWeeklyDigests(env, { now: NOW, previews: pv });
check('Monday recap: one email to the confirmed address', wk.emails === 1 && outbox.length === 1 && outbox[0].to[0] === LOWER, JSON.stringify(wk));
const mail = outbox[0] || { text: '', html: '', headers: {} };
check('recap lists the matching car, not the far one', mail.html.includes('#car=7001') && !mail.html.includes('#car=7002'));
const unsub = await recapUnsubUrl(env, LOWER);
check('recap text + html carry the one-click unsubscribe link', mail.text.includes(unsub) && mail.html.includes(unsub.replace(/&/g, '&amp;')));
check('List-Unsubscribe + One-Click headers', mail.headers && mail.headers['List-Unsubscribe'] === `<${unsub}>`
  && mail.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click');
check('footer says why it came', /because you asked for it at yardscout\.io and confirmed/.test(mail.text));
check('no postal line when EMAIL_POSTAL_ADDRESS is empty', !/PO Box|Suite/.test(mail.text));
wk = await sendWeeklyDigests(env, { now: NOW });
check('recap rerun dedupes to nothing', wk.emails === 0, JSON.stringify(wk));
const withPostal = buildDigestEmail({ ...env, EMAIL_POSTAL_ADDRESS: 'YardScout LLC, PO Box 1, Ogden, UT 84401' }, LOWER, [car(1)], { weekly: true, unsubUrl: unsub, signup: true });
check('postal line printed when the owner sets it', withPostal.text.includes('PO Box 1, Ogden') && withPostal.html.includes('PO Box 1, Ogden'));
check('confirmation email carries the postal line too', buildConfirmEmail({ EMAIL_POSTAL_ADDRESS: 'X LLC, PO Box 2' }, LOWER, [sw], 'https://l').text.includes('PO Box 2'));

/* ---- 6. one-tap add with the sub token ---- */
const subTok = decodeURIComponent(loc.split('&sub=')[1] || '');
check('sub token from the redirect verifies', subTok === await recapSubToken(env, LOWER));
r = await jsonOf(await add(env, { sub: subTok, watch: { make: 'Ford', model: 'Ranger', lat: 40.76, lng: -111.89, radiusMi: 50 } }));
check('one-tap add joins the recap, confirmed at once', r.status === 200 && r.data.state === 'added'
  && rows(env, "SELECT confirmed_at FROM recap_watches WHERE make = 'Ford'")[0]?.confirmed_at);
r = await jsonOf(await add(env, { sub: subTok.replace(/.$/, (c) => (c === 'a' ? 'b' : 'a')), watch: { make: 'Ford', lat: 1, lng: 1, radiusMi: 5 } }));
check('forged sub token refused', r.status === 401);

/* ---- 7. unsubscribe deletes the address and every copy ---- */
const u = new URL(unsub);
let res = await handleRecapUnsubscribe(new Request(unsub.replace('e=', 'e=x')), env, new URL(unsub.replace('sig=', 'sig=0')));
check('tampered unsubscribe refused', res.status === 400);
res = await handleRecapUnsubscribe(new Request(unsub), env, u);
const uhtml = await res.text();
check('unsubscribe GET page', res.status === 200 && /unsubscribed/i.test(uhtml) && !uhtml.includes(LOWER));
check('address, copied watches and dedupe rows deleted', rows(env, 'SELECT * FROM recap_subscribers').length === 0
  && rows(env, 'SELECT * FROM recap_watches').length === 0 && rows(env, 'SELECT * FROM recap_sent').length === 0);
res = await handleRecapUnsubscribe(new Request(unsub, { method: 'POST' }), env, u);
check('RFC 8058 POST is idempotent', res.status === 200 && (await res.json()).unsubscribed === true);
r = await jsonOf(await add(env, { sub: subTok, watch: { make: 'Ford', lat: 1, lng: 1, radiusMi: 5 } }));
check('after unsubscribe the sub token adds nothing', r.status === 404 && rows(env, 'SELECT * FROM recap_watches').length === 0);
seedArrival(env, car(7003));
outbox = [];
wk = await sendWeeklyDigests(env, { now: NOW });
check('nothing sent after unsubscribe', wk.emails === 0 && outbox.length === 0);

/* ---- 8. rate limit per IP (in memory, IP never stored) ---- */
env = freshEnv();
let limited = 0;
for (let i = 0; i < 10; i++) {
  const x = await signup(env, { email: `rl${i}@example.com`, watch: browserWatch }, '203.0.113.9');
  if (x.status === 429) limited++;
}
check('per-IP sign-up limit: 8 an hour, then 429', limited === 2, `limited=${limited}`);
check('IP not in the database', !JSON.stringify(rows(env, 'SELECT * FROM recap_subscribers')).includes('203.0.113.9'));

/* ---- 9. per-address cap on confirmation emails ---- */
env = freshEnv();
outbox = [];
for (let i = 0; i < 4; i++) {
  env.raw.prepare('UPDATE recap_subscribers SET confirm_sent_at = ?').run(new Date(Date.now() - 2 * 3600_000).toISOString());
  r = await jsonOf(await signup(env, { email: 'cap@example.com', watch: { ...browserWatch, model: 'M' + i } }));
}
check('4th confirmation in a day refused (3/day per address)', outbox.length === 3 && r.status === 429 && r.data.error === 'too_many', `${outbox.length} ${r.status}`);

/* ---- 10. Resend daily cap: confirmation held, nothing stored, counted ---- */
await flushOps(env);   // the send counters are isolate-wide: write the earlier sections' into their own DB
env = freshEnv({ RESEND_DAILY_CAP: '12' });   // 2 left before the reserve of 10
outbox = [];
const okA = await jsonOf(await signup(env, { email: 'a@example.com', watch: browserWatch }));
const okB = await jsonOf(await signup(env, { email: 'b@example.com', watch: browserWatch }));
const capped = await jsonOf(await signup(env, { email: 'c@example.com', watch: browserWatch }));
check('sends allowed below the cap minus reserve', okA.status === 200 && okB.status === 200 && outbox.length === 2);
check('at the cap: 503 daily_cap with a plain message', capped.status === 503 && capped.data.error === 'daily_cap'
  && /try the email again tomorrow/.test(capped.data.message), JSON.stringify(capped.data));
check('capped sign-up stores nothing', rows(env, "SELECT * FROM recap_subscribers WHERE email = 'c@example.com'").length === 0
  && rows(env, "SELECT * FROM recap_watches WHERE email = 'c@example.com'").length === 0);
await flushOps(env);
const heldRow = rows(env, "SELECT n FROM ops_counters WHERE metric = 'email:confirm:held'")[0];
check('held confirmation counted for the ops email', heldRow && heldRow.n === 1, JSON.stringify(heldRow));

// Monday recap at the cap: held, not marked sent, retry flag set.
for (const e of ['a@example.com', 'b@example.com']) {
  env.raw.prepare("UPDATE recap_subscribers SET confirmed_at = ?, confirm_hash = NULL WHERE email = ?").run(new Date().toISOString(), e);
  env.raw.prepare("UPDATE recap_watches SET confirmed_at = ? WHERE email = ?").run(new Date().toISOString(), e);
}
seedArrival(env, car(7101));
outbox = [];
wk = await sendWeeklyDigests(env, { now: NOW });
check('recap at the cap: both held, none sent', wk.emails === 0 && wk.held === 2 && outbox.length === 0, JSON.stringify(wk));
check('held recap not marked sent (retry can deliver it)', rows(env, 'SELECT * FROM recap_sent').length === 0);
check('retry flag stored', !!(await env.ENTITLEMENTS.get('recap:retry')));
await flushOps(env);
check('held recaps counted', rows(env, "SELECT n FROM ops_counters WHERE metric = 'email:digest:held'")[0]?.n === 2);
env.RESEND_DAILY_CAP = '1000';
outbox = [];
wk = await sendWeeklyDigests(env, { now: NOW });
check('retry with room sends them and clears the flag', wk.emails === 2 && outbox.length === 2 && !(await env.ENTITLEMENTS.get('recap:retry')), JSON.stringify(wk));

/* ---- 11. no secret configured in production → sign-up refused ---- */
env = freshEnv({ EMAIL_UNSUB_SECRET: '' });
r = await jsonOf(await signup(env, { email: 'x@example.com', watch: browserWatch }));
check('no signing secret → 503 not_configured (forgeable links never sent)', r.status === 503 && r.data.error === 'not_configured');

/* ---- 12. privacy of replies, prune, stats ---- */
env = freshEnv();
await signup(env, { email: 'p@example.com', watch: browserWatch });
const t2 = decodeURIComponent(linkFrom(outbox[outbox.length - 1]));
await confirmPost(env, encodeURIComponent(t2));
outbox = [];
r = await jsonOf(await signup(env, { email: 'p@example.com', watch: browserWatch }));
check('re-signup of a confirmed watch: same reply, no email (no enumeration)', r.status === 200 && r.data.state === 'confirm-sent' && outbox.length === 0);
await signup(env, { email: 'q@example.com', watch: browserWatch });
let st = await recapStats(env);
check('stats: 1 confirmed (1 watch), 1 pending', st.confirmed === 1 && st.watches === 1 && st.pending === 1, JSON.stringify(st));
await pruneRecap(env, Date.now() + 8 * 86400_000);
st = await recapStats(env);
check('unconfirmed address deleted after 7 days; confirmed kept', st.confirmed === 1 && st.pending === 0
  && rows(env, "SELECT * FROM recap_watches WHERE email = 'q@example.com'").length === 0, JSON.stringify(st));

/* ---- 13. account recap: unsubscribe link too; opt-out stops it, account untouched ---- */
env = freshEnv();
env.raw.prepare("INSERT INTO users (id, email, tier, created_at) VALUES ('u1', 'acct@example.com', 'free', '2026-11-01')").run();
env.raw.prepare("INSERT INTO watches (id, user_id, make, model, lat, lng, radius_mi, created_at) VALUES ('w1', 'u1', 'Chevrolet', 'Equinox', 40.76, -111.89, 50, '2026-11-01')").run();
seedArrival(env, car(7201));
outbox = [];
await sendWeeklyDigests(env, { now: NOW });
const am = outbox[0] || { text: '', headers: {} };
check('account recap now has an unsubscribe link + header', am.text.includes('/v1/recap/unsubscribe?') && !!am.headers['List-Unsubscribe']);
check('account recap footer names the account reason', /because your YardScout account/.test(am.text));
await handleRecapUnsubscribe(new Request(await recapUnsubUrl(env, 'acct@example.com')), env, new URL(await recapUnsubUrl(env, 'acct@example.com')));
seedArrival(env, car(7202));
outbox = [];
await sendWeeklyDigests(env, { now: NOW });
check('account opted out: no recap; account and its watch untouched', outbox.length === 0
  && rows(env, 'SELECT * FROM users').length === 1 && rows(env, 'SELECT * FROM watches').length === 1);

/* ---- logs never carry a full address ---- */
const leaked = logged.filter((l) => !/^(PASS|FAIL)/.test(l)).filter((l) => /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]/.test(l) && !/•••@/.test(l));
check('no full email address in any log line', leaked.length === 0, leaked.slice(0, 2).join(' | '));

/* ---- sign-ups by link (2026-11-13, migration 0016) ----
 * The visitor's remembered link {src, cmp, med} rides with the sign-up, is
 * kept only on the pending row, counts 'email-confirmed' under it at the
 * click and is cleared in the same step. */
{
  const W = { make: 'Nissan', model: 'Xterra', radiusMi: 50, lat: 40.76, lng: -111.89 };
  const confirmedRows = (e) => rows(e, "SELECT source, campaign, medium, platform, n FROM events_daily WHERE event = 'email-confirmed' ORDER BY source");
  const pendingOf = (e, em) => rows(e, 'SELECT pending_source AS s, pending_campaign AS c, pending_medium AS m FROM recap_subscribers WHERE email = ?', em)[0];

  // 1. tagged sign-up -> confirmed under its link, source gone afterwards
  let e = freshEnv(); outbox = [];
  let res = await jsonOf(await signup(e, { email: 'tagged@example.com', watch: W, src: 'Reddit', cmp: 'XTerra Post!', med: 'comment' }));
  check('by link: tagged sign-up accepted', res.status === 200, JSON.stringify(res.data));
  check('by link: source kept with the pending sign-up, cleaned like the counters', JSON.stringify(pendingOf(e, 'tagged@example.com')) === JSON.stringify({ s: 'reddit', c: 'xterrapost', m: 'comment' }),
    JSON.stringify(pendingOf(e, 'tagged@example.com')));
  check('by link: nothing counted before the click', confirmedRows(e).length === 0);
  let tok = decodeURIComponent(linkFrom(outbox[0]) || '');
  let cr = await confirmPost(e, tok);
  check('by link: confirm redirects as before', cr.status === 303);
  check('by link: email-confirmed counted once under reddit / xterrapost / comment (web)',
    JSON.stringify(confirmedRows(e)) === JSON.stringify([{ source: 'reddit', campaign: 'xterrapost', medium: 'comment', platform: 'web', n: 1 }]), JSON.stringify(confirmedRows(e)));
  check('by link: the source is cleared at confirmation', JSON.stringify(pendingOf(e, 'tagged@example.com')) === JSON.stringify({ s: null, c: null, m: null }), JSON.stringify(pendingOf(e, 'tagged@example.com')));
  check('by link: no trace of the source left on the address', !JSON.stringify(rows(e, 'SELECT * FROM recap_subscribers')).includes('reddit')
    && !JSON.stringify(rows(e, 'SELECT * FROM recap_watches')).includes('reddit'));
  cr = await confirmPost(e, tok);
  check('by link: a second click (reused link) counts nothing more', cr.status === 400 && confirmedRows(e)[0].n === 1, JSON.stringify(confirmedRows(e)));

  // 2. a sign-up with no remembered link: the empty source, as before
  outbox = [];
  await signup(e, { email: 'plain@example.com', watch: W });
  await confirmPost(e, decodeURIComponent(linkFrom(outbox[0]) || ''));
  const plain = confirmedRows(e).find((x) => x.source === '');
  check('by link: no source -> counted under the empty source', plain && plain.campaign === '' && plain.medium === '' && plain.n === 1, JSON.stringify(confirmedRows(e)));
  check('by link: no source -> nothing kept after confirmation either', JSON.stringify(pendingOf(e, 'plain@example.com')) === JSON.stringify({ s: null, c: null, m: null }));

  // 3. a second watch within the hour rides the link already sent: its source stays the first one
  e = freshEnv(); outbox = [];
  await signup(e, { email: 'two@example.com', watch: W, src: 'forum', cmp: 'nissan' });
  await signup(e, { email: 'two@example.com', watch: { ...W, model: 'Frontier' }, src: 'reddit' });
  check('by link: reuse within the hour sends no second email and keeps the first link\'s source', outbox.length === 1 && pendingOf(e, 'two@example.com').s === 'forum', JSON.stringify(pendingOf(e, 'two@example.com')));
  await confirmPost(e, decodeURIComponent(linkFrom(outbox[0]) || ''));
  check('by link: one confirmation (two watches) counts once, under forum / nissan',
    JSON.stringify(confirmedRows(e)) === JSON.stringify([{ source: 'forum', campaign: 'nissan', medium: '', platform: 'web', n: 1 }]), JSON.stringify(confirmedRows(e)));

  // 4. after the hour a new link replaces the old one, with the new request's source
  e = freshEnv(); outbox = [];
  await signup(e, { email: 'later@example.com', watch: W, src: 'forum' });
  const oldTok = decodeURIComponent(linkFrom(outbox[0]) || '');
  e.raw.prepare('UPDATE recap_subscribers SET confirm_sent_at = ?').run(new Date(Date.now() - 2 * 3600_000).toISOString());
  outbox = [];
  await signup(e, { email: 'later@example.com', watch: W, src: 'share', med: 'car' });
  check('by link: a new link after the hour carries the new request\'s source', outbox.length === 1 && pendingOf(e, 'later@example.com').s === 'share' && pendingOf(e, 'later@example.com').m === 'car');
  check('by link: the replaced link no longer confirms (and counts nothing)', (await confirmPost(e, oldTok)).status === 400 && confirmedRows(e).length === 0);
  await confirmPost(e, decodeURIComponent(linkFrom(outbox[0]) || ''));
  check('by link: counted under the link of the confirmation actually clicked', JSON.stringify(confirmedRows(e).map((x) => [x.source, x.medium, x.n])) === JSON.stringify([['share', 'car', 1]]), JSON.stringify(confirmedRows(e)));

  // 5. an expired link: the source is dropped by the hourly prune, the click counts nothing
  e = freshEnv(); outbox = [];
  await signup(e, { email: 'slow@example.com', watch: W, src: 'reddit' });
  const slowTok = decodeURIComponent(linkFrom(outbox[0]) || '');
  e.raw.prepare('UPDATE recap_subscribers SET confirm_expires_at = ?').run(new Date(Date.now() - 60_000).toISOString());
  await pruneRecap(e, Date.now());
  check('by link: an expired link\'s source is cleared by the prune (row itself kept until day 7)', rows(e, 'SELECT * FROM recap_subscribers').length === 1
    && JSON.stringify(pendingOf(e, 'slow@example.com')) === JSON.stringify({ s: null, c: null, m: null }), JSON.stringify(pendingOf(e, 'slow@example.com')));
  check('by link: clicking the expired link counts nothing', (await confirmPost(e, slowTok)).status === 400 && confirmedRows(e).length === 0);
  // A live link's source survives the prune.
  outbox = [];
  await signup(e, { email: 'live@example.com', watch: W, src: 'forum' });
  await pruneRecap(e, Date.now());
  check('by link: a live link keeps its source through the prune', pendingOf(e, 'live@example.com').s === 'forum');
  await pruneRecap(e, Date.now() + 8 * 86400_000);
  check('by link: an unconfirmed address (and its source) is gone after 7 days', rows(e, 'SELECT * FROM recap_subscribers').length === 0);

  // 6. an address that is already confirmed keeps no source on a new sign-up
  e = freshEnv(); outbox = [];
  await signup(e, { email: 'old@example.com', watch: W });
  await confirmPost(e, decodeURIComponent(linkFrom(outbox[0]) || ''));
  outbox = [];
  e.raw.prepare('UPDATE recap_subscribers SET confirm_sent_at = ?').run(new Date(Date.now() - 2 * 3600_000).toISOString());
  const rr = await jsonOf(await signup(e, { email: 'old@example.com', watch: { ...W, model: 'Pathfinder' }, src: 'reddit' }));
  check('by link: a confirmed address signing up again stores no source', rr.status === 200 && JSON.stringify(pendingOf(e, 'old@example.com')) === JSON.stringify({ s: null, c: null, m: null }), JSON.stringify(pendingOf(e, 'old@example.com')));
  if (outbox.length) await confirmPost(e, decodeURIComponent(linkFrom(outbox[0]) || ''));
  check('by link: and is not counted as a second confirmation', JSON.stringify(confirmedRows(e).map((x) => [x.source, x.n])) === JSON.stringify([['', 1]]), JSON.stringify(confirmedRows(e)));

  // 7. unsubscribe deletes the pending source with the row
  e = freshEnv(); outbox = [];
  await signup(e, { email: 'gone@example.com', watch: W, src: 'reddit' });
  const unsub = await recapUnsubUrl(e, 'gone@example.com');
  await handleRecapUnsubscribe(new Request(unsub, { method: 'POST' }), e, new URL(unsub));
  check('by link: unsubscribe removes the row and its source', rows(e, 'SELECT * FROM recap_subscribers').length === 0);

  // 8. the events API: a client may not post the confirmation or the v3 marker; a v3 event writes both markers
  e = freshEnv();
  const evPost = (b) => handleEvent(new Request('https://api.test/v1/events', { method: 'POST', body: JSON.stringify(b) }), e);
  check('events API: email-confirmed from a client refused', (await evPost({ e: 'email-confirmed', src: 'reddit' })).status === 400);
  check('events API: funnel-v3 from a client refused', (await evPost({ e: 'funnel-v3', p: 'web' })).status === 400);
  await evPost({ e: 'narrow/search', p: 'web', v: 3, src: 'reddit' });
  await evPost({ e: 'first-visit', p: 'ios', v: 2 });
  const evRows = rows(e, 'SELECT event, source, platform, n FROM events_daily ORDER BY event, platform');
  check('events API: a v3 event bumps funnel-v2 and funnel-v3; a v2 event only funnel-v2',
    JSON.stringify(evRows.map((x) => [x.event, x.platform])) === JSON.stringify([['first-visit', 'ios'], ['funnel-v2', 'ios'], ['funnel-v2', 'web'], ['funnel-v3', 'web'], ['narrow/search', 'web']]), JSON.stringify(evRows));
  check('events API: narrow/search counted under its source like any event', evRows.find((x) => x.event === 'narrow/search').source === 'reddit');
  // Counting rules v4 (checkout outcomes): its own marker, which a client may not post.
  check('events API: funnel-v4 from a client refused', (await evPost({ e: 'funnel-v4', p: 'android', v: 4 })).status === 400);
  await evPost({ e: 'checkout-end/failed-network', p: 'android', v: 4 });
  const v4Rows = rows(e, "SELECT event, platform, n FROM events_daily WHERE platform = 'android' ORDER BY event");
  check('events API: a v4 event bumps funnel-v2, -v3 and -v4 for its platform',
    JSON.stringify(v4Rows.map((x) => [x.event, x.n])) === JSON.stringify([['checkout-end/failed-network', 1], ['funnel-v2', 1], ['funnel-v3', 1], ['funnel-v4', 1]]), JSON.stringify(v4Rows));
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
