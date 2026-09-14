/* Web Push from the Worker — no libraries, just WebCrypto.
 *
 * Two standards do the work:
 *   - VAPID (RFC 8292): an ES256 JWT proves to the push service (Apple/Google/
 *     Mozilla) that we're the same server the user subscribed to.
 *   - Message Encryption (RFC 8291): the payload is ECDH+HKDF+AES-128-GCM
 *     encrypted to the subscription's keys, so the push service can't read it.
 *
 * Env:
 *   VAPID_PUBLIC_KEY  (var)    base64url, 65-byte uncompressed P-256 point
 *   VAPID_PRIVATE_JWK (secret) the matching private key as a JSON JWK
 *   VAPID_SUBJECT     (var)    mailto: or https: contact, e.g. mailto:you@x.com
 *
 * Generate keys once with: node backend/scripts/gen-vapid.mjs
 */

/* ---------- base64url helpers ---------- */

export function b64uToBytes(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export function bytesToB64u(bytes) {
  let bin = '';
  const arr = new Uint8Array(bytes);
  for (let i = 0; i < arr.length; i++) bin += String.fromCharCode(arr[i]);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/* ---------- VAPID JWT (ES256) ---------- */

async function vapidAuthHeader(env, endpointOrigin) {
  const now = Math.floor(Date.now() / 1000);
  const header = bytesToB64u(new TextEncoder().encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const claims = bytesToB64u(new TextEncoder().encode(JSON.stringify({
    aud: endpointOrigin,
    exp: now + 12 * 3600,
    sub: env.VAPID_SUBJECT || 'mailto:admin@example.com',
  })));
  const signingInput = header + '.' + claims;
  const key = await crypto.subtle.importKey(
    'jwk', JSON.parse(env.VAPID_PRIVATE_JWK), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']
  );
  // WebCrypto ECDSA emits raw r||s (64 bytes) — exactly the JOSE format ES256 wants.
  const sig = await crypto.subtle.sign(
    { name: 'ECDSA', hash: 'SHA-256' }, key, new TextEncoder().encode(signingInput)
  );
  return `vapid t=${signingInput}.${bytesToB64u(sig)}, k=${env.VAPID_PUBLIC_KEY}`;
}

/* ---------- RFC 8291 payload encryption (aes128gcm) ---------- */

async function hkdf(salt, ikm, info, length) {
  const key = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt, info }, key, length * 8
  ));
}

function concatBytes(...arrays) {
  const total = arrays.reduce((n, a) => n + a.length, 0);
  const out = new Uint8Array(total);
  let off = 0;
  for (const a of arrays) { out.set(a, off); off += a.length; }
  return out;
}

async function encryptPayload(payloadBytes, p256dhB64u, authB64u) {
  const uaPublic = b64uToBytes(p256dhB64u);   // 65-byte uncompressed point
  const authSecret = b64uToBytes(authB64u);   // 16 bytes

  // Ephemeral application-server ECDH keypair (fresh per message).
  const asKeys = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asPublicRaw = new Uint8Array(await crypto.subtle.exportKey('raw', asKeys.publicKey));
  const uaKey = await crypto.subtle.importKey('raw', uaPublic, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const ecdhSecret = new Uint8Array(await crypto.subtle.deriveBits(
    { name: 'ECDH', public: uaKey }, asKeys.privateKey, 256
  ));

  // IKM = HKDF(salt=auth_secret, ecdh_secret, "WebPush: info" || 0x00 || ua_public || as_public)
  const ikmInfo = concatBytes(new TextEncoder().encode('WebPush: info\0'), uaPublic, asPublicRaw);
  const ikm = await hkdf(authSecret, ecdhSecret, ikmInfo, 32);

  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, new TextEncoder().encode('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, new TextEncoder().encode('Content-Encoding: nonce\0'), 12);

  // Single record: payload || 0x02 (final-record delimiter).
  const record = concatBytes(payloadBytes, new Uint8Array([2]));
  const aesKey = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const ciphertext = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, aesKey, record));

  // aes128gcm body header: salt(16) | record_size(4) | keyid_len(1) | as_public(65)
  const rs = new Uint8Array(4);
  new DataView(rs.buffer).setUint32(0, 4096);
  return concatBytes(salt, rs, new Uint8Array([asPublicRaw.length]), asPublicRaw, ciphertext);
}

/* ---------- send ---------- */

/** Send one push. Returns {ok, gone} — gone=true means the subscription is
 * dead (unsubscribed / app removed) and should be deleted. */
export async function sendWebPush(env, sub, payload) {
  try {
    const endpoint = new URL(sub.endpoint);
    const body = await encryptPayload(
      new TextEncoder().encode(typeof payload === 'string' ? payload : JSON.stringify(payload)),
      sub.p256dh, sub.auth
    );
    const r = await fetch(sub.endpoint, {
      method: 'POST',
      headers: {
        authorization: await vapidAuthHeader(env, endpoint.origin),
        'content-encoding': 'aes128gcm',
        'content-type': 'application/octet-stream',
        ttl: '86400',
        urgency: 'normal',
      },
      body,
    });
    if (r.status === 404 || r.status === 410) return { ok: false, gone: true };
    if (!r.ok) console.log('push send failed:', r.status, (await r.text()).slice(0, 200));
    return { ok: r.ok, gone: false };
  } catch (e) {
    console.log('push send error:', e && e.message);
    return { ok: false, gone: false };
  }
}

export function pushConfigured(env) {
  return !!(env.VAPID_PUBLIC_KEY && env.VAPID_PRIVATE_JWK);
}
