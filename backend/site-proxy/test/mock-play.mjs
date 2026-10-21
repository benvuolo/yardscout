#!/usr/bin/env node
/* Local mock of the two Google endpoints /api/ent/verify-android talks to:
 *   POST /token                     (oauth2.googleapis.com/token stand-in)
 *   GET  /androidpublisher/v3/applications/:pkg/purchases/subscriptionsv2/tokens/:tok
 *
 * The Worker only talks to this mock when DEV_MODE=1 and the
 * GOOGLE_TOKEN_URL_TEST / GOOGLE_PLAY_API_URL_TEST overrides are set (see
 * google-play.js) — the same guard style as the test Apple root CA.
 *
 * It generates a real RSA keypair and VERIFIES the Worker's RS256
 * service-account assertion against it, so the WebCrypto JWT signing path is
 * genuinely exercised, not stubbed. Purchase tokens map to canned
 * subscriptionsv2 states (see FIXTURES) with expiry times computed at request
 * time, mirroring the response shapes in Google's docs.
 *
 * Usage: node mock-play.mjs <port> <outdir>
 * Writes <outdir>/sa_key.pem (private key for .dev.vars GOOGLE_SA_KEY) and
 * prints "mock-play listening" when ready. SA email is fixed: SA_EMAIL below.
 */
import { createServer } from 'node:http';
import { generateKeyPairSync, createVerify } from 'node:crypto';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const port = Number(process.argv[2] || 8798);
const outdir = process.argv[3] || '.out';
mkdirSync(outdir, { recursive: true });

export const SA_EMAIL = 'test-sa@yardscout-test.iam.gserviceaccount.com';
const PKG = 'io.yardscout.app';
const PRODUCT = 'yardscout_pro_monthly';
const ACCESS_TOKEN = 'mock-play-access-token';

const { publicKey, privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
writeFileSync(join(outdir, 'sa_key.pem'), privateKey.export({ type: 'pkcs8', format: 'pem' }));

const DAY = 24 * 3600 * 1000;
const iso = (deltaMs) => new Date(Date.now() + deltaMs).toISOString();

/* purchaseToken (prefix match) → subscriptionsv2 response factory. */
const FIXTURES = {
  'tok-active': () => sub('SUBSCRIPTION_STATE_ACTIVE', 30 * DAY),
  // Payment retry: state says grace; Play often leaves expiryTime in the
  // recent past — the Worker's own 3-day grace must carry it.
  'tok-grace': () => sub('SUBSCRIPTION_STATE_IN_GRACE_PERIOD', -1 * DAY),
  // Auto-renew turned off but the paid period runs on → still entitled.
  'tok-canceled': () => sub('SUBSCRIPTION_STATE_CANCELED', 10 * DAY),
  'tok-expired': () => sub('SUBSCRIPTION_STATE_EXPIRED', -30 * DAY),
  // ON_HOLD with a future expiry: the STATE must gate, not just the date.
  'tok-onhold': () => sub('SUBSCRIPTION_STATE_ON_HOLD', 30 * DAY),
  'tok-wrongproduct': () => sub('SUBSCRIPTION_STATE_ACTIVE', 30 * DAY, 'some_other_product'),
  // License-tester purchase — carries testPurchase like the real API.
  'tok-testpurchase': () => ({ ...sub('SUBSCRIPTION_STATE_ACTIVE', 30 * DAY), testPurchase: {} }),
  // Resubscribe: new token pointing at a retired old one.
  'tok-relinked': () => ({
    ...sub('SUBSCRIPTION_STATE_ACTIVE', 30 * DAY),
    linkedPurchaseToken: 'tok-active-0000000000',
  }),
};

function sub(state, expiryDeltaMs, productId = PRODUCT) {
  return {
    kind: 'androidpublisher#subscriptionPurchaseV2',
    startTime: iso(-5 * DAY),
    subscriptionState: state,
    latestOrderId: 'GPA.0000-0000-0000-00000',
    acknowledgementState: 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED',
    lineItems: [{ productId, expiryTime: iso(expiryDeltaMs) }],
  };
}

const b64urlToBuf = (s) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64');

function verifyAssertion(jwt) {
  const [h, p, s] = String(jwt).split('.');
  if (!h || !p || !s) return 'malformed jwt';
  const header = JSON.parse(b64urlToBuf(h));
  const claims = JSON.parse(b64urlToBuf(p));
  if (header.alg !== 'RS256') return 'alg must be RS256';
  const v = createVerify('RSA-SHA256');
  v.update(`${h}.${p}`);
  if (!v.verify(publicKey, b64urlToBuf(s))) return 'bad signature';
  if (claims.iss !== SA_EMAIL) return 'wrong iss';
  if (!String(claims.scope || '').includes('androidpublisher')) return 'wrong scope';
  if (!(claims.exp > Date.now() / 1000)) return 'expired';
  return null;
}

const json = (res, status, obj) => {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
};
const gerr = (res, code, message) => json(res, code, { error: { code, message, status: 'INVALID_ARGUMENT' } });

createServer((req, res) => {
  const url = new URL(req.url, 'http://x');

  if (req.method === 'GET' && url.pathname === '/ping') return json(res, 200, { ok: true });

  if (req.method === 'POST' && url.pathname === '/token') {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      const form = new URLSearchParams(body);
      if (form.get('grant_type') !== 'urn:ietf:params:oauth:grant-type:jwt-bearer') {
        return json(res, 400, { error: 'unsupported_grant_type' });
      }
      const why = verifyAssertion(form.get('assertion'));
      if (why) return json(res, 400, { error: 'invalid_grant', error_description: why });
      json(res, 200, { access_token: ACCESS_TOKEN, expires_in: 3600, token_type: 'Bearer' });
    });
    return;
  }

  const m = url.pathname.match(
    /^\/androidpublisher\/v3\/applications\/([^/]+)\/purchases\/subscriptionsv2\/tokens\/([^/]+)$/);
  if (req.method === 'GET' && m) {
    if (req.headers.authorization !== 'Bearer ' + ACCESS_TOKEN) {
      return gerr(res, 401, 'Request had invalid authentication credentials.');
    }
    if (decodeURIComponent(m[1]) !== PKG) {
      return gerr(res, 404, 'The application ' + m[1] + ' was not found.');
    }
    const tok = decodeURIComponent(m[2]);
    const fixture = Object.keys(FIXTURES).find((k) => tok.startsWith(k));
    if (!fixture) return gerr(res, 400, 'Invalid Value');
    return json(res, 200, FIXTURES[fixture]());
  }

  gerr(res, 404, 'Not found');
}).listen(port, '127.0.0.1', () => console.log('mock-play listening on', port));
