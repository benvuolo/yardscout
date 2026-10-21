/* Google Play Developer API — just enough client for verify-android.
 *
 * Auth is the plain service-account OAuth2 flow, no SDK: sign a JWT with the
 * SA's private key (RS256 via WebCrypto — Workers have no gRPC/googleapis),
 * swap it for a bearer token at oauth2.googleapis.com, call androidpublisher.
 *
 * Secrets (wrangler secret put, from backend/site-proxy/):
 *   GOOGLE_SA_EMAIL  the service account's client_email
 *                    (…@….iam.gserviceaccount.com)
 *   GOOGLE_SA_KEY    the service account's private_key — the PKCS#8 PEM from
 *                    the downloaded JSON key file. Paste it verbatim; both
 *                    real newlines and the JSON file's literal "\n" escapes
 *                    are accepted.
 * Two small secrets instead of the whole JSON key blob: nothing else in that
 * file is needed, rotation is pasting two values, and no project/client ids
 * end up in the Worker that don't have to.
 *
 * The access token (~1h) is cached in the ENTITLEMENTS KV under gauth:v1 so
 * steady-state verifications cost one androidpublisher GET, not two round
 * trips to Google.
 *
 * DEV TESTS ONLY: GOOGLE_TOKEN_URL_TEST / GOOGLE_PLAY_API_URL_TEST point both
 * endpoints at a local mock (test/mock-play.mjs). Ignored unless DEV_MODE=1 —
 * same guard as the test Apple root CA in verify-ios.
 */

const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const API_BASE = 'https://androidpublisher.googleapis.com';
const SCOPE = 'https://www.googleapis.com/auth/androidpublisher';
const GAUTH_KV_KEY = 'gauth:v1';

export function googlePlayConfigured(env) {
  return !!(env.GOOGLE_SA_EMAIL && env.GOOGLE_SA_KEY);
}

function b64url(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
const b64urlJson = (obj) => b64url(new TextEncoder().encode(JSON.stringify(obj)));

async function importSaKey(pem) {
  // Accept the PEM as-is or with the JSON key file's literal "\n" escapes.
  const body = String(pem)
    .replace(/\\n/g, '\n')
    .replace(/-----(BEGIN|END)[A-Z ]*PRIVATE KEY-----/g, '')
    .replace(/\s+/g, '');
  const der = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return crypto.subtle.importKey(
    'pkcs8', der.buffer, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
}

function tokenUrl(env) {
  return (env.DEV_MODE === '1' && env.GOOGLE_TOKEN_URL_TEST) || TOKEN_URL;
}
function apiBase(env) {
  return (env.DEV_MODE === '1' && env.GOOGLE_PLAY_API_URL_TEST) || API_BASE;
}

/** Service-account bearer token, KV-cached until shortly before expiry. */
async function getAccessToken(env) {
  const cached = await env.ENTITLEMENTS.get(GAUTH_KV_KEY);
  if (cached) return cached;

  const now = Math.floor(Date.now() / 1000);
  const url = tokenUrl(env);
  const header = { alg: 'RS256', typ: 'JWT' };
  const claims = { iss: env.GOOGLE_SA_EMAIL, scope: SCOPE, aud: url, iat: now, exp: now + 3600 };
  const unsigned = b64urlJson(header) + '.' + b64urlJson(claims);
  const key = await importSaKey(env.GOOGLE_SA_KEY);
  const sig = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(unsigned));
  const assertion = unsigned + '.' + b64url(new Uint8Array(sig));

  const body = new URLSearchParams({
    grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
    assertion,
  });
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok || !data.access_token) {
    console.log('google oauth error', r.status, data && (data.error_description || data.error));
    const e = new Error('Google auth failed');
    e.code = 'auth_failed';
    throw e;
  }
  // Cache for the token's life minus 5 minutes of slack (KV TTL min is 60s).
  const ttl = Math.max(60, Number(data.expires_in || 3600) - 300);
  await env.ENTITLEMENTS.put(GAUTH_KV_KEY, data.access_token, { expirationTtl: ttl });
  return data.access_token;
}

/** purchases.subscriptionsv2.get — the one androidpublisher call we need.
 *  Throws {code:'bad_token'} when Google says the token itself is invalid,
 *  {code:'auth_failed'|'google_error'} for config/transport problems. */
export async function getSubscriptionV2(env, purchaseToken) {
  const pkg = env.ANDROID_PACKAGE_NAME || 'io.yardscout.app';
  const run = async (accessToken) =>
    fetch(
      apiBase(env) + '/androidpublisher/v3/applications/' + encodeURIComponent(pkg)
        + '/purchases/subscriptionsv2/tokens/' + encodeURIComponent(purchaseToken),
      { headers: { authorization: 'Bearer ' + accessToken } });

  let token = await getAccessToken(env);
  let r = await run(token);
  if (r.status === 401) {
    // Cached token revoked/expired early — mint a fresh one and retry once.
    await env.ENTITLEMENTS.delete(GAUTH_KV_KEY);
    token = await getAccessToken(env);
    r = await run(token);
  }
  const data = await r.json().catch(() => ({}));
  if (r.ok) return data;

  const msg = (data.error && data.error.message) || 'HTTP ' + r.status;
  console.log('androidpublisher error', r.status, msg);
  const e = new Error(msg);
  // 400/404 = Google rejected this purchase token (malformed, for another
  // app, or purged). 401/403 = OUR credentials/permissions are wrong.
  e.code = (r.status === 400 || r.status === 404) ? 'bad_token' : 'google_error';
  throw e;
}
