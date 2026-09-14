/* Shared helpers: responses, CORS, crypto, rate limiting. No dependencies. */

export function isoNow() {
  return new Date().toISOString();
}

export function json(data, { status = 200, headers = {} } = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', ...headers },
  });
}

export function err(status, code, message) {
  return json({ error: code, message }, { status });
}

/** Redirect built manually — Response.redirect() headers are immutable and we
 * append CORS headers to every response on the way out. */
export function redirect(location) {
  return new Response(null, { status: 302, headers: { location } });
}

export async function sha256Hex(input) {
  const data = typeof input === 'string' ? new TextEncoder().encode(input) : input;
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** 256-bit URL-safe random token with a greppable prefix (ys_sess_..., ys_magic_...). */
export function randomToken(prefix) {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return prefix + '_' + btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Constant-time string comparison for secrets (admin/upload tokens).
 * Compares SHA-256 digests so the loop length never depends on either input. */
export async function timingSafeEqual(a, b) {
  const [ha, hb] = await Promise.all([sha256Hex(String(a ?? '')), sha256Hex(String(b ?? ''))]);
  let diff = 0;
  for (let i = 0; i < ha.length; i++) diff |= ha.charCodeAt(i) ^ hb.charCodeAt(i);
  return diff === 0;
}

export function corsHeaders(env, origin) {
  const allowed = (env.APP_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  const h = {
    'access-control-allow-methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'access-control-allow-headers': 'authorization,content-type,x-admin-secret,x-upload-token,x-content-sha256,if-none-match',
    'access-control-expose-headers': 'etag',
    'access-control-max-age': '86400',
  };
  if (origin && allowed.includes(origin)) h['access-control-allow-origin'] = origin;
  return h;
}

/* Best-effort in-memory rate limiter (fixed window, per isolate). Good enough
 * at current scale; Cloudflare's free WAF absorbs floods before they reach
 * the Worker. Auth endpoints ALSO have persistent D1-backed caps (see auth.js)
 * so isolate restarts can't be used to spam email. */
const buckets = new Map();
export function rateLimit(key, limit, windowMs) {
  const now = Date.now();
  let b = buckets.get(key);
  if (!b || now - b.start >= windowMs) {
    b = { start: now, count: 0 };
    buckets.set(key, b);
  }
  b.count++;
  if (buckets.size > 20000) {
    for (const [k, v] of buckets) if (now - v.start >= windowMs) buckets.delete(k);
  }
  return b.count <= limit;
}

export function clientIp(req) {
  return req.headers.get('cf-connecting-ip') || req.headers.get('x-forwarded-for') || 'unknown';
}

/** Decompress a stored gzip blob to text (fallback path for clients without
 * gzip support; browsers always take the pass-through path). Accepts whatever
 * D1 hands back for a BLOB column (ArrayBuffer or plain number array). */
export async function gunzipToText(buf) {
  const bytes = buf instanceof ArrayBuffer || ArrayBuffer.isView(buf) ? buf : new Uint8Array(buf);
  const stream = new Response(bytes).body.pipeThrough(new DecompressionStream('gzip'));
  return await new Response(stream).text();
}

export function haversineMiles(lat1, lng1, lat2, lng2) {
  const R = 3958.8;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

/** Bucket function for the id/VIN → yard index shards. Must stay in sync with
 * scraper/push_inventory.py (sum of UTF-8 bytes mod N). */
export function vindexBucket(token, mod) {
  const bytes = new TextEncoder().encode(String(token));
  let sum = 0;
  for (const b of bytes) sum = (sum + b) % mod;
  return sum;
}
