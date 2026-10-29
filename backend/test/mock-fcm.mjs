#!/usr/bin/env node
/* Local mock of the two Google endpoints src/fcm.js talks to:
 *   POST /token                              (oauth2.googleapis.com stand-in)
 *   POST /v1/projects/:project/messages:send (fcm.googleapis.com stand-in)
 *
 * The Worker only talks to this mock when DEV_MODE=1 and the
 * FCM_TOKEN_URL_TEST / FCM_API_URL_TEST overrides are set (see fcm.js) —
 * the same guard style as mock-play.mjs, whose shape this file follows.
 *
 * It generates a real RSA keypair and VERIFIES the Worker's RS256
 * service-account assertion against it, so the WebCrypto JWT signing path is
 * genuinely exercised, not stubbed. Device-token behavior:
 *   - tokens containing "dead-token"   → 404 UNREGISTERED (prune contract)
 *   - tokens containing "malformed"    → 400 "not a valid FCM registration token"
 *   - tokens containing "server-error" → 500 INTERNAL (a real failure, not a dead token)
 *   - anything else                    → 200 (recorded)
 * GET /sent returns every accepted send as [{token, title, body, data}] so
 * the e2e can assert deliveries and payloads.
 *
 * Usage: node mock-fcm.mjs <port> <outdir>
 * Writes <outdir>/sa_key.pem (private key for .dev.vars FCM_SA_KEY) and
 * prints "mock-fcm listening" when ready.
 */
import { createServer } from 'node:http';
import { generateKeyPairSync, createVerify } from 'node:crypto';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const port = Number(process.argv[2] || 8797);
const outdir = process.argv[3] || '.out-devices';
mkdirSync(outdir, { recursive: true });

export const SA_EMAIL = 'test-fcm@yardscout-test.iam.gserviceaccount.com';
const PROJECT = 'yardscout-test';
const ACCESS_TOKEN = 'mock-fcm-access-token';

const { publicKey, privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
writeFileSync(join(outdir, 'sa_key.pem'), privateKey.export({ type: 'pkcs8', format: 'pem' }));

const sent = [];   // accepted sends, exposed via GET /sent

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
  if (!String(claims.scope || '').includes('firebase.messaging')) return 'wrong scope';
  if (!(claims.exp > Date.now() / 1000)) return 'expired';
  return null;
}

const json = (res, status, obj) => {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
};
// FCM error envelope (matches the real v1 API shapes).
const ferr = (res, code, status, message, errorCode) => json(res, code, {
  error: {
    code, message, status,
    details: errorCode ? [{
      '@type': 'type.googleapis.com/google.firebase.fcm.v1.FcmError',
      errorCode,
    }] : [],
  },
});

createServer((req, res) => {
  const url = new URL(req.url, 'http://x');

  if (req.method === 'GET' && url.pathname === '/ping') return json(res, 200, { ok: true });
  if (req.method === 'GET' && url.pathname === '/sent') return json(res, 200, sent);

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

  const m = url.pathname.match(/^\/v1\/projects\/([^/]+)\/messages:send$/);
  if (req.method === 'POST' && m) {
    if (req.headers.authorization !== 'Bearer ' + ACCESS_TOKEN) {
      return ferr(res, 401, 'UNAUTHENTICATED', 'Request had invalid authentication credentials.');
    }
    if (decodeURIComponent(m[1]) !== PROJECT) {
      return ferr(res, 403, 'PERMISSION_DENIED', `Permission denied on project ${m[1]}.`);
    }
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      let msg;
      try { msg = JSON.parse(body).message || {}; } catch { msg = {}; }
      const tok = String(msg.token || '');
      if (!tok) return ferr(res, 400, 'INVALID_ARGUMENT', 'message.token required', 'INVALID_ARGUMENT');
      if (tok.includes('dead-token')) {
        return ferr(res, 404, 'NOT_FOUND', 'Requested entity was not found.', 'UNREGISTERED');
      }
      if (tok.includes('server-error')) {
        return ferr(res, 500, 'INTERNAL', 'Internal error encountered.');
      }
      if (tok.includes('malformed')) {
        return ferr(res, 400, 'INVALID_ARGUMENT',
          'The registration token is not a valid FCM registration token', 'INVALID_ARGUMENT');
      }
      sent.push({
        token: tok,
        title: msg.notification && msg.notification.title,
        body: msg.notification && msg.notification.body,
        data: msg.data || {},
      });
      json(res, 200, { name: `projects/${PROJECT}/messages/${sent.length}` });
    });
    return;
  }

  ferr(res, 404, 'NOT_FOUND', 'Not found');
}).listen(port, '127.0.0.1', () => console.log('mock-fcm listening on', port));
