/* Alerts e2e against `wrangler dev` (run by test/e2e-alerts.sh).
 *
 * Plays the browser AND the push service: generates a real P-256 subscription
 * keypair, runs a local HTTP server as the fake push endpoint, then verifies
 * the Worker's pushes arrive VAPID-signed and aes128gcm-encrypted by actually
 * DECRYPTING them with the subscription's private key (full RFC 8291 loop).
 */
import http from 'node:http';
import { webcrypto as wc } from 'node:crypto';

const BASE = 'http://localhost:8788';
const ADMIN = { 'x-admin-secret': 'dev-admin-secret-change-me' };
const UPLOAD = { 'x-upload-token': 'dev-upload-token-change-me' };

const b64u = (b) => Buffer.from(b).toString('base64url');
let failures = 0;
function check(name, cond, extra = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`);
  if (!cond) failures++;
}

async function api(path, opts = {}) {
  const r = await fetch(BASE + path, opts);
  return { status: r.status, data: await r.json().catch(() => ({})) };
}
const J = (body) => ({ headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });

/* ---- 1. account: sign in, initially free ---- */
let { data } = await api('/v1/auth/request-link', { method: 'POST', ...J({ email: 'watcher@test.dev' }) });
const token = new URL(data.dev_link).searchParams.get('token');
const cb = await fetch(`${BASE}/v1/auth/callback?token=${token}`, { redirect: 'manual' });
const session = decodeURIComponent(cb.headers.get('location').split('#session=')[1]);
const AUTH = { authorization: 'Bearer ' + session };

/* free user cannot create a watch */
let r = await api('/v1/watches', { method: 'POST', headers: { ...AUTH, 'content-type': 'application/json' }, body: JSON.stringify({ make: 'Toyota' }) });
check('free user blocked from watches (403)', r.status === 403 && r.data.error === 'pro_required');

/* grant pro, then create watches */
await api('/v1/admin/grant', { method: 'POST', headers: { ...ADMIN, 'content-type': 'application/json' }, body: JSON.stringify({ email: 'watcher@test.dev', tier: 'pro', note: 'e2e' }) });
r = await api('/v1/watches', { method: 'POST', headers: { ...AUTH, 'content-type': 'application/json' },
  body: JSON.stringify({ make: 'Toyota', model: '4Runner', yearMin: 1996, yearMax: 2002, lat: 40.76, lng: -111.89, radiusMi: 100 }) });
check('pro user creates watch', r.status === 200 && r.data.id);
r = await api('/v1/watches', { headers: AUTH });
check('watch list shows 1', r.data.watches?.length === 1);

/* ---- 2. push subscription with real client keys ---- */
const uaKeys = await wc.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
const uaPubRaw = new Uint8Array(await wc.subtle.exportKey('raw', uaKeys.publicKey));
const authSecret = wc.getRandomValues(new Uint8Array(16));

const received = [];
const catcher = http.createServer((req, res) => {
  const chunks = [];
  req.on('data', (c) => chunks.push(c));
  req.on('end', () => {
    received.push({ headers: req.headers, body: Buffer.concat(chunks) });
    res.writeHead(201).end();
  });
});
await new Promise((res) => catcher.listen(8791, '127.0.0.1', res));

r = await api('/v1/push/subscribe', { method: 'POST', headers: { ...AUTH, 'content-type': 'application/json' },
  body: JSON.stringify({ subscription: { endpoint: 'http://127.0.0.1:8791/push/dev1', keys: { p256dh: b64u(uaPubRaw), auth: b64u(authSecret) } } }) });
check('push subscribe accepted', r.status === 200);

/* ---- 3. commit with arrivals: one matching, two not ---- */
const arrivals = [
  { id: 111, year: 1998, make: 'Toyota', model: '4Runner', row: '42', dateAdded: '2026-09-14',
    location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 },
  { id: 222, year: 1998, make: 'Toyota', model: '4Runner', row: '9', dateAdded: '2026-09-14',
    location: 'Pick-n-Pull - Sacramento', city: 'Sacramento', state: 'CA', lat: 38.5, lng: -121.4 }, // outside radius
  { id: 333, year: 2019, make: 'Honda', model: 'Civic', row: '1', dateAdded: '2026-09-14',
    location: 'Utah Pick-A-Part - Ogden', city: 'Ogden', state: 'UT', lat: 41.19, lng: -111.94 },   // wrong car
];
const commitBody = { directory: { yards: [], scrapedAt: new Date().toISOString() }, manifest: {}, newArrivals: arrivals };
r = await api('/v1/admin/inventory/commit', { method: 'POST', headers: { ...UPLOAD, 'content-type': 'application/json' }, body: JSON.stringify(commitBody) });
check('commit accepted with arrivals', r.status === 200 && r.data.arrivals === 3);

await new Promise((res) => setTimeout(res, 2500)); // waitUntil dispatch
check('exactly one push delivered (radius + car filters applied)', received.length === 1, `got ${received.length}`);

/* ---- 4. verify the push: VAPID header + full RFC8291 decryption ---- */
if (received.length) {
  const p = received[0];
  check('content-encoding aes128gcm', p.headers['content-encoding'] === 'aes128gcm');
  check('VAPID authorization header', /^vapid t=.+, k=.+/.test(p.headers.authorization || ''));

  const jwt = (p.headers.authorization.match(/t=([^,]+)/) || [])[1];
  const claims = JSON.parse(Buffer.from(jwt.split('.')[1], 'base64url').toString());
  check('VAPID aud matches endpoint origin', claims.aud === 'http://127.0.0.1:8791');

  // Decrypt: header = salt(16) rs(4) idlen(1) asPub(65) | ciphertext
  const body = p.body;
  const salt = body.subarray(0, 16);
  const idlen = body[20];
  const asPub = body.subarray(21, 21 + idlen);
  const ct = body.subarray(21 + idlen);
  const asKey = await wc.subtle.importKey('raw', asPub, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const ecdh = new Uint8Array(await wc.subtle.deriveBits({ name: 'ECDH', public: asKey }, uaKeys.privateKey, 256));
  const hkdf = async (s, ikm, info, len) => new Uint8Array(await wc.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: s, info },
    await wc.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']), len * 8));
  const ikmInfo = Buffer.concat([Buffer.from('WebPush: info\0'), uaPubRaw, asPub]);
  const ikm = await hkdf(authSecret, ecdh, ikmInfo, 32);
  const cek = await hkdf(salt, ikm, Buffer.from('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, Buffer.from('Content-Encoding: nonce\0'), 12);
  const aes = await wc.subtle.importKey('raw', cek, 'AES-GCM', false, ['decrypt']);
  const plain = Buffer.from(await wc.subtle.decrypt({ name: 'AES-GCM', iv: nonce }, aes, ct));
  const payload = JSON.parse(plain.subarray(0, plain.lastIndexOf(2)).toString());
  check('payload decrypts to alert digest', /watched car/.test(payload.title || ''), payload.title);
  check('digest names the matching car only', /4Runner/.test(payload.body) && !/Civic/.test(payload.body) && !/Sacramento/.test(payload.body));
}

/* ---- 5. dedupe: same commit again → no second push ---- */
r = await api('/v1/admin/inventory/commit', { method: 'POST', headers: { ...UPLOAD, 'content-type': 'application/json' }, body: JSON.stringify(commitBody) });
await new Promise((res) => setTimeout(res, 2000));
check('repeat commit sends nothing (dedupe)', received.length === 1, `got ${received.length}`);

/* ---- 6. self-test endpoint ---- */
r = await api('/v1/push/test', { method: 'POST', headers: AUTH });
check('push self-test sends', r.status === 200 && r.data.sent === 1);

/* ---- 7. watch delete ---- */
const { data: wl } = await api('/v1/watches', { headers: AUTH });
r = await api('/v1/watches/' + wl.watches[0].id, { method: 'DELETE', headers: AUTH });
check('watch deleted', r.status === 200);

catcher.close();
console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
process.exit(failures ? 1 : 0);
