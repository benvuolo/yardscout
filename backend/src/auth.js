/* Magic-link email auth + bearer sessions + tier resolution.
 *
 * Flow: POST /v1/auth/request-link {email} → email (Resend) with a single-use
 * 15-minute link → GET /v1/auth/callback?token=... → session created →
 * 302 redirect to the PWA with #session=<token> in the URL fragment.
 *
 * The PWA lives on a different origin (github.io), so httpOnly cookies would
 * be third-party and Safari/ITP blocks them. Instead the session is a bearer
 * token: 256-bit random, stored SHA-256-hashed server-side, sent by the app in
 * an Authorization header, kept in localStorage client-side. The fragment
 * (#session=) is never sent to any server and the app strips it immediately.
 */

import {
  json, err, redirect, sha256Hex, randomToken, isoNow, rateLimit, clientIp,
} from './util.js';

const MAGIC_TTL_MS = 15 * 60 * 1000;          // 15 minutes
const SESSION_TTL_MS = 90 * 24 * 3600 * 1000; // 90 days

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function handleRequestLink(req, env) {
  const ip = clientIp(req);
  if (!rateLimit('link:ip:' + ip, 10, 3600_000)) {
    return err(429, 'rate_limited', 'Too many sign-in requests from this network. Try again later.');
  }
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!EMAIL_RE.test(email) || email.length > 254) {
    return err(400, 'bad_email', 'Enter a valid email address.');
  }

  // Persistent cap (survives isolate restarts): 5 links per email per hour.
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM magic_tokens WHERE email = ?1 AND created_at > ?2"
  ).bind(email, new Date(Date.now() - 3600_000).toISOString()).first();
  if ((recent?.n || 0) >= 5) {
    return err(429, 'rate_limited', 'Too many sign-in links requested for this email. Try again in an hour.');
  }

  const token = randomToken('ys_magic');
  await env.DB.prepare(
    'INSERT INTO magic_tokens (token_hash, email, expires_at, created_at, request_ip) VALUES (?1, ?2, ?3, ?4, ?5)'
  ).bind(
    await sha256Hex(token),
    email,
    new Date(Date.now() + MAGIC_TTL_MS).toISOString(),
    isoNow(),
    ip
  ).run();

  const link = new URL(req.url).origin + '/v1/auth/callback?token=' + encodeURIComponent(token);

  if (env.DEV_MODE === '1') {
    // Local dev / tests: no email sender needed — the link is logged and
    // returned so the flow can be exercised end-to-end offline.
    console.log('[DEV_MODE] magic link for ' + email + ': ' + link);
    return json({ sent: true, dev: true, dev_link: link });
  }
  if (!env.RESEND_API_KEY) {
    return err(503, 'email_unconfigured', 'Sign-in email is not configured yet (missing RESEND_API_KEY).');
  }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      authorization: 'Bearer ' + env.RESEND_API_KEY,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'YardScout <onboarding@resend.dev>',
      to: [email],
      subject: 'Your YardScout sign-in link',
      text:
        'Tap to sign in to YardScout:\n\n' + link + '\n\n' +
        'This link works once and expires in 15 minutes. ' +
        "If you didn't request it, you can ignore this email.",
    }),
  });
  if (!r.ok) {
    console.log('resend send failed:', r.status, (await r.text()).slice(0, 500));
    return err(502, 'email_failed', 'Could not send the sign-in email. Try again in a minute.');
  }
  return json({ sent: true });
}

export async function handleCallback(req, env) {
  const appUrl = env.APP_URL || 'https://benvuolo.github.io/yardscout/';
  const fail = (reason) => redirect(appUrl + '#login_error=' + encodeURIComponent(reason));

  const token = new URL(req.url).searchParams.get('token') || '';
  if (!token.startsWith('ys_magic_') || token.length > 200) return fail('bad_token');

  const hash = await sha256Hex(token);
  const row = await env.DB.prepare(
    'SELECT email, expires_at, used_at FROM magic_tokens WHERE token_hash = ?1'
  ).bind(hash).first();
  if (!row) return fail('unknown_token');
  if (new Date(row.expires_at).getTime() < Date.now()) return fail('expired_token');

  // Single-use, atomically claimed — a second redemption (or a double-click
  // race) loses the conditional UPDATE and gets bounced.
  const claim = await env.DB.prepare(
    'UPDATE magic_tokens SET used_at = ?1 WHERE token_hash = ?2 AND used_at IS NULL'
  ).bind(isoNow(), hash).run();
  if (!claim.meta.changes) return fail('used_token');

  let user = await env.DB.prepare('SELECT id FROM users WHERE email = ?1').bind(row.email).first();
  if (!user) {
    user = { id: crypto.randomUUID() };
    await env.DB.prepare(
      'INSERT INTO users (id, email, tier, created_at, last_login_at) VALUES (?1, ?2, ?3, ?4, ?4)'
    ).bind(user.id, row.email, 'free', isoNow()).run();
  } else {
    await env.DB.prepare('UPDATE users SET last_login_at = ?1 WHERE id = ?2')
      .bind(isoNow(), user.id).run();
  }

  const sess = randomToken('ys_sess');
  await env.DB.prepare(
    'INSERT INTO sessions (token_hash, user_id, created_at, expires_at, last_seen_at) VALUES (?1, ?2, ?3, ?4, ?3)'
  ).bind(
    await sha256Hex(sess),
    user.id,
    isoNow(),
    new Date(Date.now() + SESSION_TTL_MS).toISOString()
  ).run();

  return redirect(appUrl + '#session=' + encodeURIComponent(sess));
}

/** Resolve the Authorization: Bearer session, or null for anonymous. */
export async function getSessionUser(req, env) {
  const m = (req.headers.get('authorization') || '').match(/^Bearer\s+(ys_sess_[A-Za-z0-9_-]{20,})$/);
  if (!m) return null;
  const hash = await sha256Hex(m[1]);
  const row = await env.DB.prepare(
    `SELECT s.token_hash AS session_hash, s.expires_at AS session_expires,
            u.id, u.email, u.tier, u.tier_source, u.tier_expires_at
       FROM sessions s JOIN users u ON u.id = s.user_id
      WHERE s.token_hash = ?1`
  ).bind(hash).first();
  if (!row) return null;
  if (new Date(row.session_expires).getTime() < Date.now()) return null;
  return row;
}

/* ===== Entitlements =====
 * THE single place a tier decision is made. Apple IAP integration point:
 * RevenueCat's webhook (src/admin.js → handleRevenueCatWebhook) writes
 * users.tier / tier_expires_at / tier_source; this function then honors the
 * expiry automatically — a lapsed subscription resolves to 'free' with no
 * cron or cleanup job needed. */
export function resolveTier(user) {
  if (!user) return 'free';
  let tier = user.tier || 'free';
  if (tier !== 'free' && user.tier_expires_at && new Date(user.tier_expires_at).getTime() < Date.now()) {
    tier = 'free';
  }
  return ['free', 'pro', 'pro_plus'].includes(tier) ? tier : 'free';
}

/** Which pre-computed shard variant a tier reads. pro_plus sees pro data
 * (its extras — instant alerts, digests — are features, not data fields). */
export function variantFor(tier) {
  return tier === 'free' ? 'free' : 'pro';
}

export async function handleMe(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'unauthorized', 'Sign in required.');
  const tier = resolveTier(user);
  return json({
    email: user.email,
    tier,
    tierSource: user.tier_source || null,
    tierExpiresAt: user.tier_expires_at || null,
  });
}

export async function handleLogout(req, env) {
  const m = (req.headers.get('authorization') || '').match(/^Bearer\s+(ys_sess_[A-Za-z0-9_-]{20,})$/);
  if (m) {
    await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?1')
      .bind(await sha256Hex(m[1])).run();
  }
  return json({ ok: true });
}
