/* APNs (Apple Push Notification service) from the Worker — no libraries.
 *
 * Token-based auth (JWT ES256 signed with the .p8 key from the Apple
 * Developer account). One JWT is reused for ~45 minutes (Apple allows up to
 * 60; requires iat no older than that and rejects tokens refreshed more than
 * once per ~20 min, so caching is mandatory, not just polite).
 *
 * Env:
 *   APNS_TEAM_ID    (var)    10-char Apple Developer team id
 *   APNS_KEY_ID     (var)    10-char key id of the APNs auth key
 *   APNS_BUNDLE_ID  (var)    app bundle id, e.g. com.yardscout.app
 *   APNS_ENV        (var)    "production" | "sandbox" (dev builds use sandbox)
 *   APNS_P8         (secret) contents of the AuthKey_XXXXXXXXXX.p8 file
 */

import { bytesToB64u } from './push.js';

let cachedJwt = null;   // { token, iat } — module-global survives across requests

function p8ToPkcs8Bytes(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PRIVATE KEY-----/g, '').replace(/\s+/g, '');
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function apnsJwt(env) {
  const now = Math.floor(Date.now() / 1000);
  if (cachedJwt && now - cachedJwt.iat < 45 * 60) return cachedJwt.token;
  const header = bytesToB64u(new TextEncoder().encode(JSON.stringify({
    alg: 'ES256', kid: env.APNS_KEY_ID,
  })));
  const claims = bytesToB64u(new TextEncoder().encode(JSON.stringify({
    iss: env.APNS_TEAM_ID, iat: now,
  })));
  const signingInput = header + '.' + claims;
  const key = await crypto.subtle.importKey(
    'pkcs8', p8ToPkcs8Bytes(env.APNS_P8),
    { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign(
    { name: 'ECDSA', hash: 'SHA-256' }, key, new TextEncoder().encode(signingInput)
  );
  const token = signingInput + '.' + bytesToB64u(sig);
  cachedJwt = { token, iat: now };
  return token;
}

export function apnsConfigured(env) {
  return !!(env.APNS_TEAM_ID && env.APNS_KEY_ID && env.APNS_BUNDLE_ID && env.APNS_P8);
}

/** Send one alert push. payload: {title, body, url?}. Returns {ok, gone} —
 * gone=true means the token is dead (app deleted) and should be cleared. */
export async function sendApns(env, deviceToken, payload) {
  try {
    const host = (env.APNS_ENV || 'production') === 'sandbox'
      ? 'https://api.sandbox.push.apple.com'
      : 'https://api.push.apple.com';
    const r = await fetch(`${host}/3/device/${deviceToken}`, {
      method: 'POST',
      headers: {
        authorization: 'bearer ' + await apnsJwt(env),
        'apns-topic': env.APNS_BUNDLE_ID,
        'apns-push-type': 'alert',
        'apns-priority': '10',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        aps: { alert: { title: payload.title, body: payload.body }, sound: 'default' },
        url: payload.url || '/',
      }),
    });
    if (r.ok) return { ok: true, gone: false };
    const text = await r.text();
    // 410 = token no longer active; 400 BadDeviceToken = wrong env or garbage.
    const gone = r.status === 410 || /BadDeviceToken|Unregistered/i.test(text);
    if (!gone) console.log('apns send failed:', r.status, text.slice(0, 200));
    return { ok: false, gone };
  } catch (e) {
    console.log('apns send error:', e && e.message);
    return { ok: false, gone: false };
  }
}
