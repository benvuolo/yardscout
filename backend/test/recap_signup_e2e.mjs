/* Free Monday email e2e against `wrangler dev` + mock-resend (phase 2 of
 * test/e2e-email.sh). The Worker takes its REAL Resend send paths against the
 * mock, so every email below is the one a person would get.
 *
 *   sign-up → one confirmation email (nothing else) → GET confirm is a page,
 *   POST confirm opts in (303 to the app with the one-tap token) → the Monday
 *   recap (cron path) contains the matching car, with a one-click unsubscribe
 *   link and List-Unsubscribe headers → the daily ops email counts the
 *   subscriber → the Resend daily cap holds sign-ups back and the ops email
 *   says so → unsubscribe deletes the address, its copied watches and its
 *   dedupe rows (checked in the local D1) → nothing more is sent.
 */
import { execFileSync } from 'node:child_process';

const BASE = process.env.YS_TEST_BASE || 'http://127.0.0.1:8793';
const MOCK = process.env.YS_MOCK_BASE || 'http://127.0.0.1:8799';
const STATE = process.env.YS_STATE_DIR || 'test/.out-email/wrangler-state-recap';
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

const EMAIL = 'monday.reader@test.dev';
const WATCH = { make: 'Toyota', model: 'Tacoma', yearMin: null, yearMax: null, lat: 40.7608, lng: -111.891, radiusMi: 100 };

/* ---- 1. sign-up → exactly one confirmation email ---- */
let before = (await sent()).length;
let r = await api('/v1/recap/signup', J({ email: EMAIL, watch: WATCH }));
check('sign-up accepted', r.status === 200 && r.data.state === 'confirm-sent', JSON.stringify(r.data));
let mails = (await sent()).slice(before);
check('exactly one email: the confirmation', mails.length === 1 && mails[0].subject === 'Confirm your free YardScout Monday email' && mails[0].to[0] === EMAIL,
  JSON.stringify(mails.map((m) => m.subject)));
check('honest sender', mails[0] && mails[0].from === 'YardScout <hello@yardscout.io>', mails[0] && mails[0].from);
const link = ((mails[0] && mails[0].text) || '').match(/https?:\/\/\S+\/v1\/recap\/confirm\?t=\S+/);
check('the confirmation carries its link', !!link);
const confirmUrl = new URL(link ? link[0] : BASE);
const t = confirmUrl.searchParams.get('t');
let rows = d1(`SELECT confirmed_at FROM recap_subscribers WHERE email = '${EMAIL}'`);
check('stored unconfirmed; one pending copied watch', rows.length === 1 && rows[0].confirmed_at === null
  && d1(`SELECT COUNT(*) AS n FROM recap_watches WHERE email = '${EMAIL}' AND confirmed_at IS NULL`)[0].n === 1);

/* ---- 2. the Monday recap does not go out before the click ---- */
const FIELDS = ['id', 'vin', 'year', 'make', 'model', 'row', 'dateAdded', 'yard', 'partSet', 'maxValue', 'premium'];
const today = new Date().toISOString().slice(0, 10);
const tacoma = (id, location, lat, lng) => ({ id, year: 2004, make: 'Toyota', model: 'Tacoma', row: '14', dateAdded: today, location, city: 'X', state: 'UT', lat, lng });
r = await api('/v1/admin/inventory/commit', J({
  directory: { yards: [['Utah Pick-A-Part - Ogden', 'Ogden', 'UT', 41.19, -111.94]], fields: FIELDS, vindexMod: 64, scrapedAt: new Date().toISOString() },
  manifest: {}, newArrivals: [tacoma(8801, 'Utah Pick-A-Part - Ogden', 41.19, -111.94), tacoma(8802, 'Pick-n-Pull - Phoenix', 33.4, -112.0)] }, UPLOAD));
check('arrivals committed', r.status === 200 && r.data.arrivals === 2, JSON.stringify(r.data));
await sleep(1500);
const LATER = new Date(Date.now() + 2 * 86400_000).toISOString();
r = await api('/v1/admin/digest/run', J({ now: LATER, preview: true }, ADMIN));
check('no recap to an unconfirmed address (double opt-in)', !(r.data.previews || []).some((p) => p.to === EMAIL), JSON.stringify(r.data));

/* ---- 3. confirm: GET is a page, POST opts in ---- */
const page = await fetch(confirmUrl.href.replace(/^https?:\/\/[^/]+/, BASE));
const pageHtml = await page.text();
check('GET confirm: a page with a button, nothing confirmed', page.status === 200 && /<form method="post"/.test(pageHtml)
  && d1(`SELECT confirmed_at FROM recap_subscribers WHERE email = '${EMAIL}'`)[0].confirmed_at === null);
r = await api('/v1/recap/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(t) });
const loc = r.headers.get('location') || '';
check('POST confirm → 303 to the app with the one-tap token', r.status === 303 && /^https:\/\/yardscout\.io\/#recap=confirmed&sub=[A-Za-z0-9_-]+\.[0-9a-f]{64}$/.test(decodeURIComponent(loc)), loc);
check('address and copied watch confirmed', d1(`SELECT COUNT(*) AS n FROM recap_watches WHERE email = '${EMAIL}' AND confirmed_at IS NOT NULL`)[0].n === 1);
check('"email confirmed" counted once (anonymous daily counter)', d1("SELECT SUM(n) AS n FROM events_daily WHERE event = 'email-confirmed'")[0].n === 1);
r = await api('/v1/recap/confirm', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 't=' + encodeURIComponent(t) });
check('the link is single-use', r.status === 400);

/* ---- 4. Monday recap (the cron's code path) contains the car ---- */
before = (await sent()).length;
r = await api('/v1/admin/digest/run', J({ now: LATER, preview: true }, ADMIN));
const pv = (r.data.previews || []).find((p) => p.to === EMAIL);
mails = (await sent()).slice(before).filter((m) => m.to[0] === EMAIL);
check('one Monday recap to the confirmed address', !!pv && mails.length === 1, JSON.stringify({ users: r.data.users, emails: r.data.emails }));
const m = mails[0] || { text: '', html: '', headers: {} };
check('the recap lists the Tacoma within 100 mi, not the one in Phoenix', m.html.includes('#car=8801') && !m.html.includes('#car=8802'));
check('subject is honest', /^Your week at the yards — 1 watched car arrived$/.test(m.subject || ''), m.subject);
const unsub = (m.text.match(/https?:\/\/\S+\/v1\/recap\/unsubscribe\?e=\S+&sig=[0-9a-f]{64}/) || [])[0];
check('one-click unsubscribe link in the text and the html', !!unsub && m.html.includes(unsub.replace(/&/g, '&amp;')));
check('List-Unsubscribe + List-Unsubscribe-Post headers', m.headers && m.headers['List-Unsubscribe'] === `<${unsub}>`
  && m.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click', JSON.stringify(m.headers));
check('footer says why it came', /because you asked for it at yardscout\.io and confirmed/.test(m.text));
r = await api('/v1/admin/digest/run', J({ now: LATER, preview: true }, ADMIN));
check('rerun sends that car again to nobody (dedupe)', !(r.data.previews || []).some((p) => p.to === EMAIL));

/* ---- 5. one-tap add with the token from the redirect ---- */
const sub = decodeURIComponent(loc.split('&sub=')[1] || '');
r = await api('/v1/recap/add', J({ sub, watch: { make: 'Ford', model: 'Ranger', lat: 40.76, lng: -111.89, radiusMi: 50 } }));
check('one-tap add joins the confirmed recap', r.status === 200 && r.data.state === 'added' && r.data.watches === 2, JSON.stringify(r.data));

/* ---- 6. the daily ops email counts the subscriber ---- */
r = await api('/v1/admin/ops/daily/run', J({ dryRun: true }, ADMIN));
const opsText = (r.data.email && r.data.email.text) || '';
check('ops email: confirmed recap subscribers line', /Monday email \(web sign-ups\): 1 confirmed subscriber \(2 watches\) · 0 waiting for the confirmation click/.test(opsText),
  opsText.split('\n').filter((l) => /Monday email/.test(l)).join(' | '));
check('ops email funnel has the three Monday email rows', /Monday email asked/.test(opsText) && /Monday email given/.test(opsText) && /Monday email confirmed/.test(opsText));

/* ---- 7. Resend daily cap (RESEND_DAILY_CAP=14 here: optional mail stops at 4 sent) ---- */
let capped = null, n = 0;
for (let i = 0; i < 6 && !capped; i++) {
  r = await api('/v1/recap/signup', J({ email: `cap${i}@test.dev`, watch: WATCH }));
  if (r.status === 503) capped = r; else n++;
}
check('at the cap a sign-up is refused with daily_cap and a plain message', !!capped && capped.data.error === 'daily_cap' && /try the email again tomorrow/.test(capped.data.message),
  JSON.stringify(capped && capped.data));
check('the refused address is not stored', capped && d1(`SELECT COUNT(*) AS n FROM recap_subscribers WHERE email = 'cap${n}@test.dev'`)[0].n === 0);
r = await api('/v1/admin/ops/daily/run', J({ dryRun: true }, ADMIN));
const held = ((r.data.email && r.data.email.text) || '').split('\n').find((l) => /HELD BACK/.test(l)) || '';
check('ops email says mail was held back at the cap', /HELD BACK at the Resend daily cap \(24 h\): 1 sign-up confirmation/.test(held), held);
check('ops html says it too', /Held back at the daily cap/.test((r.data.email && r.data.email.html) || ''));

/* ---- 8. unsubscribe deletes everything for the address ---- */
const u = unsub ? unsub.replace(/^https?:\/\/[^/]+/, BASE) : BASE;
r = await api(new URL(u).pathname + new URL(u).search.replace(/sig=[0-9a-f]{4}/, 'sig=0000'));
check('a tampered link is refused', r.status === 400);
const up = await fetch(u);
const upHtml = await up.text();
check('unsubscribe page, address masked', up.status === 200 && /unsubscribed/i.test(upHtml) && !upHtml.includes(EMAIL));
const left = d1(`SELECT (SELECT COUNT(*) FROM recap_subscribers WHERE email = '${EMAIL}') AS s,
  (SELECT COUNT(*) FROM recap_watches WHERE email = '${EMAIL}') AS w, (SELECT COUNT(*) FROM recap_sent WHERE email = '${EMAIL}') AS d`)[0];
check('address, copied watches and dedupe rows all deleted', left.s === 0 && left.w === 0 && left.d === 0, JSON.stringify(left));
r = await api(new URL(u).pathname + new URL(u).search, { method: 'POST' });
check('RFC 8058 one-click POST answers ok (idempotent)', r.status === 200 && r.data.unsubscribed === true);
r = await api('/v1/recap/add', J({ sub, watch: WATCH }));
check('the one-tap token no longer adds anything', r.status === 404);
await api('/v1/admin/inventory/commit', J({
  directory: { yards: [['Utah Pick-A-Part - Ogden', 'Ogden', 'UT', 41.19, -111.94]], fields: FIELDS, vindexMod: 64, scrapedAt: new Date().toISOString() },
  manifest: {}, newArrivals: [tacoma(8803, 'Utah Pick-A-Part - Ogden', 41.19, -111.94)] }, UPLOAD));
await sleep(1500);
r = await api('/v1/admin/digest/run', J({ now: LATER, preview: true }, ADMIN));
check('no recap after unsubscribing', !(r.data.previews || []).some((p) => p.to === EMAIL));

/* ---- 9. logs carry no full address ---- */
if (process.env.YS_DEV_LOG) {
  const { readFileSync } = await import('node:fs');
  const log = readFileSync(process.env.YS_DEV_LOG, 'utf8');
  check('worker log never names a full sign-up address', !log.includes(EMAIL) && !/cap\d@test\.dev/.test(log));
}

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
