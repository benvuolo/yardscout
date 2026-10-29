/* FCM (Firebase Cloud Messaging) HTTP v1 from the Worker — no libraries.
 *
 * The Android counterpart of apns.js. Auth is the plain service-account
 * OAuth2 flow (same WebCrypto RS256 pattern as site-proxy/src/google-play.js):
 * sign a JWT with the SA key, swap it for a ~1h bearer token at
 * oauth2.googleapis.com, POST to fcm.googleapis.com. The bearer is cached
 * module-global (like the APNs JWT) — isolates recycle, worst case is one
 * extra token round trip.
 *
 * Env:
 *   FCM_PROJECT_ID  (var)    Firebase project id, e.g. yardscout-play
 *   FCM_SA_EMAIL    (var)    service account client_email
 *                            (yardscout-fcm-sender@….iam.gserviceaccount.com)
 *   FCM_SA_KEY      (secret) the SA's private_key — PKCS#8 PEM from the JSON
 *                            key file. Real newlines or the JSON's literal
 *                            "\n" escapes both work (same as GOOGLE_SA_KEY).
 *
 * DEV TESTS ONLY: FCM_TOKEN_URL_TEST / FCM_API_URL_TEST point both endpoints
 * at a local mock (test/mock-fcm.mjs). Ignored unless DEV_MODE=1 — same
 * guard as google-play.js.
 */

import { countOk, countFail, countGone } from './ops.js';

const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const FCM_BASE = 'https://fcm.googleapis.com';
const SCOPE = 'https://www.googleapis.com/auth/firebase.messaging';

let cachedAuth = null;   // { token, exp(sec) } — module-global, like apns.js

export function fcmConfigured(env) {
  return !!(env.FCM_PROJECT_ID && env.FCM_SA_EMAIL && env.FCM_SA_KEY);
}

function tokenUrl(env) {
  return (env.DEV_MODE === '1' && env.FCM_TOKEN_URL_TEST) || TOKEN_URL;
}
function apiBase(env) {
  return (env.DEV_MODE === '1' && env.FCM_API_URL_TEST) || FCM_BASE;
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

async function accessToken(env) {
  const now = Math.floor(Date.now() / 1000);
  if (cachedAuth && now < cachedAuth.exp) return cachedAuth.token;

  const url = tokenUrl(env);
  const claims = { iss: env.FCM_SA_EMAIL, scope: SCOPE, aud: url, iat: now, exp: now + 3600 };
  const unsigned = b64urlJson({ alg: 'RS256', typ: 'JWT' }) + '.' + b64urlJson(claims);
  const key = await importSaKey(env.FCM_SA_KEY);
  const sig = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(unsigned));
  const assertion = unsigned + '.' + b64url(new Uint8Array(sig));

  const r = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    }),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok || !data.access_token) {
    console.log('fcm oauth error', r.status, data && (data.error_description || data.error));
    throw new Error('FCM auth failed');
  }
  // Cache until 5 minutes before Google's expiry.
  cachedAuth = { token: data.access_token, exp: now + Math.max(60, Number(data.expires_in || 3600) - 300) };
  return data.access_token;
}

/** Send one notification push. payload: {title, body, url?}. Returns
 * {ok, gone} — gone=true means FCM says the token is dead (UNREGISTERED /
 * app uninstalled) and the caller should clear it, mirroring sendApns. */
export async function sendFcm(env, deviceToken, payload) {
  try {
    const body = JSON.stringify({
      message: {
        token: deviceToken,
        notification: { title: payload.title, body: payload.body },
        data: { url: payload.url || '/' },
        android: {
          priority: 'HIGH',
          notification: { sound: 'default', default_sound: true },
        },
      },
    });
    const send = async (bearer) =>
      fetch(`${apiBase(env)}/v1/projects/${env.FCM_PROJECT_ID}/messages:send`, {
        method: 'POST',
        headers: { authorization: 'Bearer ' + bearer, 'content-type': 'application/json' },
        body,
      });

    let r = await send(await accessToken(env));
    if (r.status === 401) {
      // Cached bearer revoked/expired early — mint a fresh one and retry once.
      cachedAuth = null;
      r = await send(await accessToken(env));
    }
    if (r.ok) { await countOk(env, 'fcm'); return { ok: true, gone: false }; }
    const text = await r.text();
    // 404 UNREGISTERED = app uninstalled / token rotated away.
    // 400 "not a valid FCM registration token" = garbage token — also prune.
    const gone = r.status === 404 || /UNREGISTERED|not a valid FCM registration token/i.test(text);
    if (!gone) console.log('fcm send failed:', r.status, text.slice(0, 200));
    if (gone) await countGone(env, 'fcm'); else await countFail(env, 'fcm', r.status, text);
    return { ok: false, gone };
  } catch (e) {
    console.log('fcm send error:', e && e.message);
    await countFail(env, 'fcm', 0, `error: ${e && e.message}`);
    return { ok: false, gone: false };
  }
}
