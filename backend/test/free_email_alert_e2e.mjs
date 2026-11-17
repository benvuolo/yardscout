/* Free emailed alert e2e against `wrangler dev` + mock-resend (phase 3 of
 * test/e2e-email.sh, RESEND_DAILY_CAP=40 there, so the free-alert limits are
 * 8 a day and none once 28 emails of any kind have gone out). The Worker
 * takes its REAL Resend send paths against the mock, so every email below is
 * the one a person would get. Every address is an example.com one.
 *
 *   sign-up → exactly one confirmation email → a scan commit BEFORE the click
 *   mails nothing → GET confirm is a page, POST confirm opts in (303 to the
 *   app with the browser token) → the next scan commit (the real commit hook)
 *   sends ONE alert email: the car inside 50 mi only, List-Unsubscribe
 *   headers, signed link → the same scan again sends nothing (dedupe) →
 *   status / change car with the token → 7 addresses on one scan: 5 emails,
 *   2 held, counted; the next commit (no new cars) delivers the 2 → the day's
 *   8 are used: a new car is held for everyone and the daily ops email says
 *   so → unsubscribe (one-click POST) deletes the address and its rows
 *   (checked in the local D1) → nothing more is sent to it.
 */
import { execFileSync } from 'node:child_process';

const BASE = process.env.YS_TEST_BASE || 'http://127.0.0.1:8793';
const MOCK = process.env.YS_MOCK_BASE || 'http://127.0.0.1:8799';
const STATE = process.env.YS_STATE_DIR || 'test/.out-email/wrangler-state-falert';
const ADMIN = { 'x-admin-secret': 'dev-admin-secret-change-me' };
const UPLOAD = { 'x-upload-token': 'dev-upload-token-change-me' };

let failures = 0;
function check(name, cond, extra = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra && !cond ? ' — ' + extra : ''}`);
  if (!cond) failures++;
}
async function api(path, opts = {}) {
  const r = await fetch(BASE + path, { redirect: 'manual', ...opts });
  const text = await r.text();
  let data = {};
  try { data = JSON.parse(text); } catch { data = { __raw: text }; }
  return { status: r.status, data, headers: r.headers };
}
const J = (body, headers = {}) => ({ method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) });
const sent = async () => (await (await fetch(MOCK + '/sent')).json());
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const d1 = (sql) => JSON.parse(execFileSync('npx', ['wrangler', 'd1', 'execute', 'yardscout-db', '--local', '--persist-to', STATE, '--json', '--command', sql],
  { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }))[0].results;
/** Emails the mock accepted since `from`, once `n` have arrived (or the wait is over). */
async function mailSince(from, n, ms = 8000) {
  const t0 = Date.now();
  let got = [];
  do { await sleep(400); got = (await sent()).slice(from); } while (got.length < n && Date.now() - t0 < ms);
  return got;
}
const isAlert = (m) => /YardScout Alerts/.test(m.from || '');

const EMAIL = 'alert.reader@example.com';
const SLC = { lat: 40.7608, lng: -111.891 };
// The browser's watch says 250 mi; the free alert covers 50.
const WATCH = { make: 'Toyota', model: 'Tacoma', yearMin: null, yearMax: null, ...SLC, radiusMi: 250 };
const FIELDS = ['id', 'vin', 'year', 'make', 'model', 'row', 'dateAdded', 'yard', 'partSet', 'maxValue', 'premium'];
const today = new Date().toISOString().slice(0, 10);
const tacoma = (id, location, lat, lng) => ({ id, year: 2004, make: 'Toyota', model: 'Tacoma', row: '14', dateAdded: today, location, city: 'X', state: 'UT', lat, lng });
const NEAR = (id) => tacoma(id, 'Utah Pick-A-Part - Ogden', 41.19, -111.94);        // ~30 mi north of Salt Lake City
const FAR = (id) => tacoma(id, 'Utah Pick-A-Part - Logan', 41.74, -111.83);        // ~68 mi: past the free 50
const commit = (newArrivals) => api('/v1/admin/inventory/commit', J({
  directory: { yards: [['Utah Pick-A-Part - Ogden', 'Ogden', 'UT', 41.19, -111.94]], fields: FIELDS, vindexMod: 64, scrapedAt: new Date().toISOString() },
  manifest: {}, newArrivals }, UPLOAD));

/* ---- 1. sign-up → exactly one confirmation email ---- */
let before = (await sent()).length;
let r = await api('/v1/free-alert/signup', J({ email: EMAIL, watch: WATCH, src: 'reddit', cmp: 'e2e', med: 'post' }));
check('sign-up accepted', r.status === 200 && r.data.state === 'confirm-sent', JSON.stringify(r.data));
let mails = await mailSince(before, 1);
check('exactly one email: the confirmation', mails.length === 1 && mails[0].subject === 'Confirm your free YardScout email alert' && mails[0].to[0] === EMAIL,
  JSON.stringify(mails.map((m) => m.subject)));
check('it names the car and the 50 mi (the watch said 250)', /Toyota Tacoma is set out at a yard within 50 mi/.test((mails[0] && mails[0].text) || ''));
const link = ((mails[0] && mails[0].text) || '').match(/https?:\/\/\S+\/v1\/free-alert\/confirm\?t=\S+/);
check('the confirmation carries its link', !!link);
const confirmUrl = new URL(link ? link[0] : BASE);
const t = confirmUrl.searchParams.get('t');
let rows = d1(`SELECT confirmed_at, watch_json, pending_json FROM free_email_alerts WHERE email = '${EMAIL}'`);
check('stored unconfirmed, the copy pending', rows.length === 1 && rows[0].confirmed_at === null && rows[0].watch_json === null && /Tacoma/.test(rows[0].pending_json || ''));

/* ---- 2. a scan before the click mails nothing ---- */
before = (await sent()).length;
r = await commit([NEAR(9801)]);
check('arrivals committed', r.status === 200 && r.data.arrivals === 1, JSON.stringify(r.data));
await sleep(2500);
check('no alert email to an unconfirmed address (double opt-in)', (await sent()).slice(before).filter(isAlert).length === 0);

/* ---- 3. confirm: GET is a page, POST opts in ---- */
const page = await fetch(confirmUrl.href.replace(/^https?:\/\/[^/]+/, BASE));
const pageHtml = await page.text();
check('GET confirm: a page with a button that names the car, nothing confirmed', page.status === 200 && /<form method="post"/.test(pageHtml) && /Toyota Tacoma/.test(pageHtml)
  && !pageHtml.includes(EMAIL) && d1(`SELECT confirmed_at FROM free_email_alerts WHERE email = '${EMAIL}'`)[0].confirmed_at === null);
r = await api('/v1/free-alert/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(t) });
const loc = decodeURIComponent(r.headers.get('location') || '');
check('POST confirm → 303 to the app with the browser token', r.status === 303 && /^https:\/\/yardscout\.io\/#falert=confirmed&sub=[A-Za-z0-9_-]+\.[0-9a-f]{64}$/.test(loc), loc);
const sub = loc.split('&sub=')[1] || '';
rows = d1(`SELECT confirmed_at, watch_json, pending_json FROM free_email_alerts WHERE email = '${EMAIL}'`);
check('confirmed; the one watch is set, clamped to 50 mi', rows[0].confirmed_at && JSON.parse(rows[0].watch_json).radius_mi === 50 && rows[0].pending_json === null);
check('"confirmed" counted once, under the link (anonymous daily counter)',
  JSON.stringify(d1("SELECT source, n FROM events_daily WHERE event = 'free-alert-confirmed'")) === JSON.stringify([{ source: 'reddit', n: 1 }]));
r = await api('/v1/free-alert/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(t) });
check('the link is single-use', r.status === 400);
check('the car from before the click is known, not owed (future arrivals only)', d1(`SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE email = '${EMAIL}' AND vehicle_id = '9801'`)[0].n === 1);

/* ---- 4. the next scan commit: ONE alert email ---- */
before = (await sent()).length;
r = await commit([NEAR(9801), NEAR(9802), FAR(9803), { ...NEAR(9804), model: 'Tundra' }]);
mails = (await mailSince(before, 1)).filter(isAlert);
await sleep(1200);
mails = (await sent()).slice(before).filter(isAlert);
check('one alert email for the scan', mails.length === 1 && mails[0].to[0] === EMAIL, JSON.stringify(mails.map((m) => [m.to[0], m.subject])));
const m = mails[0] || { text: '', html: '', headers: {} };
check('it has the new Tacoma 30 mi away', m.text.includes('#car=9802') && m.html.includes('#car=9802'));
check('not the one 68 mi away, the Tundra, or the car that was there before the click', !/9803|9804|9801/.test(m.text + m.html));
check('subject is honest', m.subject === 'New: 2004 Toyota Tacoma at Utah Pick-A-Part - Ogden', m.subject);
check('sent from the alerts sender', m.from === 'YardScout Alerts <alerts@yardscout.io>', m.from);
check('says "same day", never "instant"', /same day a car is listed/.test(m.text) && !/instant/i.test(m.subject + m.text + m.html));
const unsub = (m.text.match(/https?:\/\/\S+\/v1\/free-alert\/unsubscribe\?e=\S+&sig=[0-9a-f]{64}/) || [])[0];
check('one-click unsubscribe link in the text and the html', !!unsub && m.html.includes(unsub.replace(/&/g, '&amp;')));
check('List-Unsubscribe + List-Unsubscribe-Post headers', m.headers && m.headers['List-Unsubscribe'] === `<${unsub}>`
  && m.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click', JSON.stringify(m.headers));
check('footer says why it came', /because you asked for a free email alert at yardscout\.io and confirmed/.test(m.text));
check('"first email sent" counted once', d1("SELECT SUM(n) AS n FROM events_daily WHERE event = 'free-alert-first-email'")[0].n === 1);
check('the send is counted on its own channel', d1("SELECT n FROM ops_counters WHERE metric = 'email:free-alert:ok'")[0]?.n === 1);

before = (await sent()).length;
await commit([NEAR(9802)]);
await sleep(2500);
check('the same car in the next scan: no second email (dedupe)', (await sent()).slice(before).filter(isAlert).length === 0);

/* ---- 5. the browser token: status, change car without an email ---- */
r = await api('/v1/free-alert/status', J({ sub }));
check('status: on, the watch without its centre or the address', r.status === 200 && r.data.state === 'on' && r.data.watch.model === 'Tacoma' && r.data.watch.radiusMi === 50
  && !/lat|lng|example\.com/.test(JSON.stringify(r.data)), JSON.stringify(r.data));
before = (await sent()).length;
r = await api('/v1/free-alert/signup', J({ email: EMAIL, sub, watch: { ...WATCH, model: '4Runner', radiusMi: 25 } }));
check('with the token the car changes at once', r.status === 200 && r.data.state === 'on' && r.data.watch.model === '4Runner' && r.data.watch.radiusMi === 25, JSON.stringify(r.data));
await sleep(800);
check('...and no email is sent for it', (await sent()).length === before);
check('still one row, one watch', d1(`SELECT COUNT(*) AS n FROM free_email_alerts WHERE email = '${EMAIL}'`)[0].n === 1
  && JSON.parse(d1(`SELECT watch_json FROM free_email_alerts WHERE email = '${EMAIL}'`)[0].watch_json).model === '4Runner');
r = await api('/v1/free-alert/signup', J({ email: EMAIL, sub, watch: WATCH }));
check('back to the Tacoma', r.data.state === 'on' && r.data.watch.model === 'Tacoma');

/* ---- 6. seven addresses, one scan: 5 emails, 2 held; then the day's limit ---- */
const more = Array.from({ length: 6 }, (_, i) => `crowd${i}@example.com`);
for (const e of more) {
  before = (await sent()).length;
  r = await api('/v1/free-alert/signup', J({ email: e, watch: WATCH }));
  const cm = (await mailSince(before, 1))[0];
  const tk = new URL((cm.text.match(/https?:\/\/\S+\/v1\/free-alert\/confirm\?t=\S+/) || [BASE])[0]).searchParams.get('t');
  await api('/v1/free-alert/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(tk) });
}
check('seven confirmed addresses', d1('SELECT COUNT(*) AS n FROM free_email_alerts WHERE confirmed_at IS NOT NULL')[0].n === 7);
before = (await sent()).length;
await commit([NEAR(9810)]);
await mailSince(before, 5);
await sleep(1500);
mails = (await sent()).slice(before).filter(isAlert);
check('one scan, seven matches: five emails (the per-scan cap), one per address', mails.length === 5 && new Set(mails.map((x) => x.to[0])).size === 5, String(mails.length));
check('two are held: flagged, the car NOT marked sent', d1('SELECT COUNT(*) AS n FROM free_email_alerts WHERE held_at IS NOT NULL')[0].n === 2
  && d1("SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE vehicle_id = '9810'")[0].n === 5);
check('held is counted (email:free-alert:held = 2)', d1("SELECT n FROM ops_counters WHERE metric = 'email:free-alert:held'")[0]?.n === 2);
before = (await sent()).length;
await commit([]);   // the next scan brings no new car
await mailSince(before, 2);
await sleep(1500);
mails = (await sent()).slice(before).filter(isAlert);
check('the next scan delivers the two held alerts', mails.length === 2 && mails.every((x) => x.text.includes('#car=9810'))
  && d1("SELECT COUNT(*) AS n FROM free_email_alerts_sent WHERE vehicle_id = '9810'")[0].n === 7, String(mails.length));
check('free alert emails today: 8 (1 + 5 + 2), the day\'s limit at this cap', d1("SELECT n FROM ops_counters WHERE metric = 'email:free-alert:ok'")[0]?.n === 8);
before = (await sent()).length;
await commit([NEAR(9811)]);
await sleep(3000);
check('at the daily limit a new car is mailed to nobody', (await sent()).slice(before).filter(isAlert).length === 0);
check('...all seven are held and counted (2 + 7)', d1('SELECT COUNT(*) AS n FROM free_email_alerts WHERE held_at IS NOT NULL')[0].n === 7
  && d1("SELECT n FROM ops_counters WHERE metric = 'email:free-alert:held'")[0]?.n === 9);
before = (await sent()).length;
r = await api('/v1/free-alert/signup', J({ email: 'still.room@example.com', watch: WATCH }));
check('other mail is not starved: a confirmation email still goes out', r.status === 200 && (await mailSince(before, 1)).some((x) => /Confirm your free YardScout email alert/.test(x.subject)));

/* ---- 7. the daily ops email says all of it ---- */
r = await api('/v1/admin/ops/daily/run', J({ dryRun: true }, ADMIN));
const opsText = (r.data.email && r.data.email.text) || '';
const opsHtml = (r.data.email && r.data.email.html) || '';
check('ops email: the free email alert line', /Free email alert \(web\): 7 addresses with an alert on · 1 waiting for the confirmation click · 7 emailed at least once/.test(opsText),
  opsText.split('\n').filter((l) => /Free email alert/.test(l)).join(' | '));
const held = opsText.split('\n').find((l) => /HELD BACK for the free-alert email budget/.test(l)) || '';
check('ops email: held free alert emails', /HELD BACK for the free-alert email budget \(24 h\): 9 free alert emails \(lowest class of mail; retried on later scans for 48 h, then not sent\)/.test(held), held);
check('ops html says both too', /Held back for the free-alert email budget \(24 h\): 9 free alert emails/.test(opsHtml) && /Free email alert \(web\): 7 addresses/.test(opsHtml));
check('ops email funnel has the four free alert rows', ['Free alert offered', 'Free alert asked', 'Free alert confirmed', 'Free alert 1st email'].every((x) => opsText.includes(x)));
check('ops email sends table lists the channel', /email:free-alert\s+8 \/ 0/.test(opsText), opsText.split('\n').filter((l) => /email:free-alert/.test(l)).join(' | '));

/* ---- 8. unsubscribe deletes everything for the address ---- */
const u = unsub ? unsub.replace(/^https?:\/\/[^/]+/, BASE) : BASE;
r = await api(new URL(u).pathname + new URL(u).search.replace(/sig=[0-9a-f]{4}/, 'sig=0000'), { method: 'POST' });
check('a tampered link is refused', r.status === 400);
r = await api(new URL(u).pathname + new URL(u).search, { method: 'POST' });
check('RFC 8058 one-click POST answers ok', r.status === 200 && r.data.unsubscribed === true);
const left = d1(`SELECT (SELECT COUNT(*) FROM free_email_alerts WHERE email = '${EMAIL}') AS a,
  (SELECT COUNT(*) FROM free_email_alerts_sent WHERE email = '${EMAIL}') AS d`)[0];
check('address, copied watch and dedupe rows all deleted', left.a === 0 && left.d === 0, JSON.stringify(left));
const up = await fetch(u);
const upHtml = await up.text();
check('the link opened again: the page, address masked (idempotent)', up.status === 200 && /unsubscribed/i.test(upHtml) && !upHtml.includes(EMAIL));
r = await api('/v1/free-alert/status', J({ sub }));
check('status: off', r.status === 200 && r.data.state === 'off');
before = (await sent()).length;
r = await api('/v1/free-alert/signup', J({ email: EMAIL, sub, watch: WATCH }));
check('the old token does not switch it back on: it asks the inbox again', r.status === 200 && r.data.state === 'confirm-sent' && !r.data.sub
  && d1(`SELECT confirmed_at FROM free_email_alerts WHERE email = '${EMAIL}'`)[0].confirmed_at === null);
r = await api('/v1/free-alert/off', J({ sub }));
check('"Turn off" removes even that pending row', r.status === 200 && r.data.state === 'off' && d1(`SELECT COUNT(*) AS n FROM free_email_alerts WHERE email = '${EMAIL}'`)[0].n === 0);

/* ---- 9. the Pro email alerts of the same commits were not disturbed ---- */
const devLog = process.env.YS_DEV_LOG ? (await import('node:fs')).readFileSync(process.env.YS_DEV_LOG, 'utf8') : '';
if (devLog) {
  // A commit with new cars logs the Pro line, then the free line; a commit
  // with none logs the free line alone.
  const order = devLog.split('\n').filter((l) => /(^|\s)email alerts: |free email alerts: /.test(l)).map((l) => (/free email alerts/.test(l) ? 'free' : 'pro'));
  const pros = order.filter((x) => x === 'pro').length;
  const ok = pros >= 4 && order.every((x, i) => x !== 'pro' || order[i + 1] === 'free') && order[0] === 'pro';
  check('in every commit with new cars the Pro email dispatch finished before the free one started', ok, order.join(','));
  check('worker log never names a full sign-up address', !devLog.includes(EMAIL) && !/crowd\d@example\.com/.test(devLog) && !devLog.includes('still.room@example.com'));
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
