/* Email-alerts e2e against `wrangler dev` (run by test/e2e-email.sh).
 *
 * Exercises the whole web-Pro email flow: entitlement-token-gated watch sync,
 * the post-commit dispatch hook, per-(email, vehicle) dedupe, signed one-click
 * unsubscribe (GET page + RFC 8058 POST), and the send-time Pro gate (lapsed
 * entitlement = no email). DEV_MODE has no Resend key, so "delivered" means
 * the DEV log-and-succeed path marked the dedupe bookkeeping — the real
 * Resend send is verified against production separately.
 */
import { createHmac, randomBytes } from 'node:crypto';

const BASE = process.env.YS_TEST_BASE || 'http://localhost:8793';
const ADMIN = { 'x-admin-secret': 'dev-admin-secret-change-me' };
const UPLOAD = { 'x-upload-token': 'dev-upload-token-change-me' };
const UNSUB_SECRET = 'dev-unsub-secret-change-me';

let failures = 0;
function check(name, cond, extra = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`);
  if (!cond) failures++;
}

async function api(path, opts = {}) {
  const r = await fetch(BASE + path, opts);
  const text = await r.text();
  let data = {};
  try { data = JSON.parse(text); } catch { data = { __raw: text }; }
  return { status: r.status, data };
}
const J = (body, headers = {}) => ({
  method: 'POST',
  headers: { 'content-type': 'application/json', ...headers },
  body: JSON.stringify(body),
});
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

const EMAIL = 'emailwatcher@test.dev';
const TOKEN = randomBytes(32).toString('hex');

/* ---- 1. entitlement + sync gating ---- */
let r = await api('/v1/email-alerts/sync', J({ token: 'f'.repeat(64), watches: [] }));
check('unknown token rejected (401)', r.status === 401 && r.data.error === 'bad_token');

r = await api('/v1/admin/test/ent', J({ email: EMAIL, token: TOKEN }, ADMIN));
check('test entitlement seeded (DEV seam)', r.status === 200 && r.data.ok);

const WATCH = { make: 'Toyota', model: '4Runner', yearMin: 1996, yearMax: 2002,
  lat: 40.76, lng: -111.89, radiusMi: 100 };
r = await api('/v1/email-alerts/sync', J({ token: TOKEN, watches: [WATCH] }));
check('pro sync accepted', r.status === 200 && r.data.ok && r.data.email === EMAIL, JSON.stringify(r.data));
check('sync enabled by default', r.data.enabled === true);

r = await api('/v1/email-alerts/status?token=' + TOKEN);
check('status: enabled, 1 watch', r.data.enabled === true && r.data.watches === 1 && r.data.pro === true,
  JSON.stringify(r.data));

/* ---- 2. commit hook: one matching arrival → one email; dedupe holds ---- */
const arrivals = [
  { id: 9111, year: 1998, make: 'Toyota', model: '4Runner', row: '42', dateAdded: '2026-10-19',
    location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 },
  { id: 9222, year: 1998, make: 'Toyota', model: '4Runner', row: '9', dateAdded: '2026-10-19',
    location: 'Pick-n-Pull - Sacramento', city: 'Sacramento', state: 'CA', lat: 38.5, lng: -121.4 }, // outside radius
  { id: 9333, year: 2019, make: 'Honda', model: 'Civic', row: '1', dateAdded: '2026-10-19',
    location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 },    // wrong car
];
const commitBody = { directory: { yards: [], scrapedAt: new Date().toISOString() }, manifest: {}, newArrivals: arrivals };
r = await api('/v1/admin/inventory/commit', J(commitBody, UPLOAD));
check('commit accepted with arrivals', r.status === 200 && r.data.arrivals === 3);
await sleep(2500); // waitUntil dispatch

// If the commit hook dispatched (and marked dedupe), re-running the exact
// production dispatch path with the same arrivals must send nothing.
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals }, ADMIN));
check('commit hook emailed once — manual re-dispatch dedupes to zero',
  r.status === 200 && r.data.users === 0 && r.data.emails === 0, JSON.stringify(r.data));

/* ---- 3. a genuinely new arrival emails exactly once ---- */
const arrival2 = [{ id: 9444, year: 1999, make: 'Toyota', model: '4Runner', row: '7', dateAdded: '2026-10-20',
  location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 }];
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals: arrival2 }, ADMIN));
check('new arrival → one user, one email', r.data.users === 1 && r.data.emails === 1, JSON.stringify(r.data));
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals: arrival2 }, ADMIN));
check('same arrival again → dedupe sends nothing', r.data.users === 0 && r.data.emails === 0, JSON.stringify(r.data));

/* ---- 4. watch creation never alerts on cars already on the lot ---- */
const EMAIL2 = 'late-subscriber@test.dev';
const TOKEN2 = randomBytes(32).toString('hex');
await api('/v1/admin/test/ent', J({ email: EMAIL2, token: TOKEN2 }, ADMIN));
r = await api('/v1/email-alerts/sync', J({ token: TOKEN2, watches: [WATCH] }));
check('late subscriber sync seeds current matches', r.status === 200 && r.data.seeded >= 1,
  `seeded=${r.data.seeded}`);
// Re-dispatch the COMMITTED arrivals (the ones storeArrivals snapshotted and
// sync therefore seeded): the late subscriber must not hear about them, and
// the original user already did (dedupe).
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals }, ADMIN));
check('late subscriber NOT emailed about pre-existing cars', r.data.users === 0 && r.data.emails === 0,
  JSON.stringify(r.data));
// Retire the second user so later steps test exactly one subscriber.
r = await api('/v1/email-alerts/sync', J({ token: TOKEN2, watches: [WATCH], enabled: false }));
check('late subscriber turned off', r.status === 200 && r.data.enabled === false);

/* ---- 5. unsubscribe: signed link (GET page), RFC 8058 POST, channel-only ---- */
const sig = createHmac('sha256', 'ys-unsub:' + UNSUB_SECRET).update(EMAIL).digest('hex');
const e64 = Buffer.from(EMAIL).toString('base64url');

r = await api(`/v1/email-alerts/unsubscribe?e=${e64}&sig=${'0'.repeat(64)}`);
check('tampered unsubscribe signature rejected', r.status === 400);

const page = await fetch(`${BASE}/v1/email-alerts/unsubscribe?e=${e64}&sig=${sig}`);
const pageHtml = await page.text();
check('unsubscribe GET renders confirmation page', page.status === 200 && /unsubscribed/i.test(pageHtml));

r = await api(`/v1/email-alerts/unsubscribe?e=${e64}&sig=${sig}`, { method: 'POST' });
check('one-click POST unsubscribe ok (idempotent)', r.status === 200 && r.data.unsubscribed === true);

r = await api('/v1/email-alerts/status?token=' + TOKEN);
check('status reflects unsubscribe; Pro untouched', r.data.enabled === false && r.data.pro === true,
  JSON.stringify(r.data));

const arrival3 = [{ id: 9555, year: 2000, make: 'Toyota', model: '4Runner', row: '3', dateAdded: '2026-10-20',
  location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 }];
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals: arrival3 }, ADMIN));
check('unsubscribed user gets nothing', r.data.users === 0 && r.data.emails === 0, JSON.stringify(r.data));

/* ---- 6. re-enable from the app, then entitlement lapses → no email ---- */
r = await api('/v1/email-alerts/sync', J({ token: TOKEN, watches: [WATCH], enabled: true }));
check('toggle back on re-enables', r.status === 200 && r.data.enabled === true);

// Lapse the entitlement (expired yesterday) — sync must 403, dispatch must skip.
await api('/v1/admin/test/ent', J({ email: EMAIL, token: TOKEN,
  expiresAt: new Date(Date.now() - 86400_000).toISOString() }, ADMIN));
r = await api('/v1/email-alerts/sync', J({ token: TOKEN, watches: [WATCH] }));
check('lapsed Pro cannot sync (403)', r.status === 403 && r.data.error === 'pro_required');

const arrival4 = [{ id: 9666, year: 2001, make: 'Toyota', model: '4Runner', row: '5', dateAdded: '2026-10-20',
  location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 }];
r = await api('/v1/admin/email-alerts/dispatch', J({ arrivals: arrival4 }, ADMIN));
check('lapsed Pro skipped at send time', r.data.users === 0 && r.data.emails === 0, JSON.stringify(r.data));

console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
