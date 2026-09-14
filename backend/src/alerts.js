/* Per-account alerts: server-side watches + dispatch on inventory commit.
 *
 * Flow: the scan's push_inventory.py includes recent arrivals in the commit
 * body → dispatchAlerts() matches them against every Pro user's watches →
 * one digest Web Push per device (and an email fallback for users with no
 * push subscription). alerts_sent dedupes so overlapping scans never
 * re-alert the same (user, vehicle) pair.
 *
 * Sends run in ctx.waitUntil after the commit response, capped to stay inside
 * the Workers free-plan subrequest budget (50/request). With more users than
 * the cap, upgrade the Worker to paid ($5/mo → 1000 subrequests).
 */

import { json, err, isoNow, haversineMiles } from './util.js';
import { getSessionUser, resolveTier } from './auth.js';
import { sendWebPush, pushConfigured } from './push.js';

const MAX_WATCHES_PER_USER = 20;
const MAX_VEHICLES_PER_DIGEST = 6;   // keep the notification readable
const MAX_SENDS_PER_COMMIT = 35;     // subrequest budget (free plan: 50/req)

/* ===== watches CRUD (session + Pro) ===== */

export async function handleWatchesList(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  const rows = (await env.DB.prepare(
    'SELECT id, make, model, year_min, year_max, lat, lng, radius_mi, created_at FROM watches WHERE user_id = ?1 ORDER BY created_at DESC'
  ).bind(user.id).all()).results || [];
  return json({ watches: rows, tier: resolveTier(user) });
}

export async function handleWatchCreate(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  if (resolveTier(user) !== 'pro') {
    return err(403, 'pro_required', 'Alerts are a Pro feature.');
  }
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }

  const make = String(body.make || '').trim().slice(0, 40) || null;
  const model = String(body.model || '').trim().slice(0, 60) || null;
  if (!make && !model) return err(400, 'bad_watch', 'A watch needs at least a make or a model.');
  const yearMin = Number.isFinite(+body.yearMin) && +body.yearMin > 1900 ? Math.floor(+body.yearMin) : null;
  const yearMax = Number.isFinite(+body.yearMax) && +body.yearMax > 1900 ? Math.floor(+body.yearMax) : null;
  const lat = Number.isFinite(+body.lat) ? +body.lat : null;
  const lng = Number.isFinite(+body.lng) ? +body.lng : null;
  const radiusMi = Number.isFinite(+body.radiusMi) && +body.radiusMi > 0
    ? Math.min(Math.floor(+body.radiusMi), 3000) : null;

  const n = await env.DB.prepare('SELECT COUNT(*) AS n FROM watches WHERE user_id = ?1')
    .bind(user.id).first();
  if ((n?.n || 0) >= MAX_WATCHES_PER_USER) {
    return err(400, 'too_many', `Max ${MAX_WATCHES_PER_USER} watches — remove one first.`);
  }

  const id = crypto.randomUUID();
  await env.DB.prepare(
    `INSERT INTO watches (id, user_id, make, model, year_min, year_max, lat, lng, radius_mi, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`
  ).bind(id, user.id, make, model, yearMin, yearMax,
         (lat != null && lng != null) ? lat : null,
         (lat != null && lng != null) ? lng : null,
         radiusMi, isoNow()).run();
  return json({ ok: true, id });
}

export async function handleWatchDelete(req, env, watchId) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  await env.DB.prepare('DELETE FROM watches WHERE id = ?1 AND user_id = ?2')
    .bind(watchId, user.id).run();
  return json({ ok: true });
}

/* ===== push subscriptions ===== */

export function handleVapidKey(env) {
  if (!pushConfigured(env)) return err(503, 'push_off', 'Push is not configured yet.');
  return json({ publicKey: env.VAPID_PUBLIC_KEY });
}

export async function handlePushSubscribe(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const sub = body.subscription || body;
  const endpoint = String(sub.endpoint || '');
  const p256dh = sub.keys && String(sub.keys.p256dh || '');
  const auth = sub.keys && String(sub.keys.auth || '');
  // Real push services are always https; localhost is allowed only in dev so
  // the e2e test can stand in as the push service.
  const okEndpoint = endpoint.startsWith('https://')
    || (env.DEV_MODE === '1' && /^http:\/\/(127\.0\.0\.1|localhost):/.test(endpoint));
  if (!okEndpoint || !p256dh || !auth) {
    return err(400, 'bad_subscription', 'Missing endpoint or keys.');
  }
  await env.DB.prepare(
    `INSERT INTO push_subscriptions (endpoint, user_id, p256dh, auth, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5)
     ON CONFLICT (endpoint) DO UPDATE SET user_id = ?2, p256dh = ?3, auth = ?4`
  ).bind(endpoint, user.id, p256dh, auth, isoNow()).run();
  return json({ ok: true });
}

export async function handlePushUnsubscribe(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1 AND user_id = ?2')
    .bind(String(body.endpoint || ''), user.id).run();
  return json({ ok: true });
}

/** Self-test: sends a push to every device the signed-in user registered. */
export async function handlePushTest(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  if (!pushConfigured(env)) return err(503, 'push_off', 'Push is not configured yet.');
  const subs = (await env.DB.prepare(
    'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1 LIMIT 5'
  ).bind(user.id).all()).results || [];
  if (!subs.length) return err(404, 'no_subscriptions', 'No devices registered for push on this account.');
  let sent = 0;
  for (const sub of subs) {
    const res = await sendWebPush(env, sub, {
      title: 'YardScout test',
      body: 'Push alerts are working on this device.',
      url: '/',
    });
    if (res.gone) {
      await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1').bind(sub.endpoint).run();
    } else if (res.ok) sent++;
  }
  return json({ ok: true, sent, devices: subs.length });
}

/* ===== dispatch on inventory commit ===== */

function watchMatches(w, v) {
  if (w.make && String(v.make || '').toLowerCase() !== w.make.toLowerCase()) return false;
  if (w.model && String(v.model || '').toLowerCase() !== w.model.toLowerCase()) return false;
  if (w.year_min && (!v.year || v.year < w.year_min)) return false;
  if (w.year_max && (!v.year || v.year > w.year_max)) return false;
  if (w.lat != null && w.lng != null && w.radius_mi) {
    if (v.lat == null || v.lng == null) return false;
    if (haversineMiles(w.lat, w.lng, v.lat, v.lng) > w.radius_mi) return false;
  }
  return true;
}

function digestText(matches) {
  const lines = matches.slice(0, MAX_VEHICLES_PER_DIGEST).map((v) =>
    `${v.year || ''} ${v.make} ${v.model} — ${v.location}${v.row ? ` (row ${v.row})` : ''}`.trim());
  const more = matches.length - MAX_VEHICLES_PER_DIGEST;
  if (more > 0) lines.push(`…and ${more} more`);
  return lines.join('\n');
}

async function emailDigest(env, email, matches) {
  if (!env.RESEND_API_KEY) return false;
  const n = matches.length;
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'YardScout <onboarding@resend.dev>',
      to: [email],
      subject: `${n} watched car${n === 1 ? '' : 's'} just hit the yard`,
      text:
        `New arrivals matching your YardScout watches:\n\n${digestText(matches)}\n\n` +
        `Open the app for rows, VINs, and part details:\n${(env.APP_URL || '').trim()}\n\n` +
        `Yards crush cars within weeks — fresh arrivals are the best odds.`,
    }),
  });
  if (!r.ok) console.log('alert email failed:', r.status, (await r.text()).slice(0, 200));
  return r.ok;
}

/** Called from handleCommit (via ctx.waitUntil) with the commit's newArrivals:
 * [{id, year, make, model, row, location, city, state, lat, lng, dateAdded}]. */
export async function dispatchAlerts(env, arrivals) {
  if (!Array.isArray(arrivals) || !arrivals.length) return { users: 0, sends: 0 };

  // Active watches for users whose tier is currently pro (expiry honored).
  const rows = (await env.DB.prepare(
    `SELECT w.id AS wid, w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi,
            u.id AS user_id, u.email, u.tier, u.tier_expires_at
       FROM watches w JOIN users u ON u.id = w.user_id`
  ).all()).results || [];

  const byUser = new Map();
  for (const r of rows) {
    if (resolveTier(r) !== 'pro') continue;
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, { email: r.email, watches: [] });
    byUser.get(r.user_id).watches.push(r);
  }
  if (!byUser.size) return { users: 0, sends: 0 };

  let sends = 0;
  let usersAlerted = 0;

  for (const [userId, { email, watches }] of byUser) {
    if (sends >= MAX_SENDS_PER_COMMIT) { console.log('alert send budget hit — remaining users deferred'); break; }
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;

    // Dedupe: drop vehicles this user was already alerted about.
    const fresh = [];
    for (const v of matched) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM alerts_sent WHERE user_id = ?1 AND vehicle_id = ?2'
      ).bind(userId, String(v.id)).first();
      if (!seen) fresh.push(v);
    }
    if (!fresh.length) continue;

    const payload = {
      title: `${fresh.length} watched car${fresh.length === 1 ? '' : 's'} just hit the yard`,
      body: digestText(fresh),
      url: '/',
    };

    const subs = (await env.DB.prepare(
      'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?1 LIMIT 3'
    ).bind(userId).all()).results || [];

    let delivered = false;
    if (pushConfigured(env)) {
      for (const sub of subs) {
        if (sends >= MAX_SENDS_PER_COMMIT) break;
        sends++;
        const res = await sendWebPush(env, sub, payload);
        if (res.gone) {
          await env.DB.prepare('DELETE FROM push_subscriptions WHERE endpoint = ?1').bind(sub.endpoint).run();
        } else if (res.ok) delivered = true;
      }
    }
    if (!delivered && sends < MAX_SENDS_PER_COMMIT) {
      sends++;
      delivered = await emailDigest(env, email, fresh);
    }

    if (delivered) {
      usersAlerted++;
      for (const v of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO alerts_sent (user_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, String(v.id), isoNow()).run();
      }
    }
  }

  // Prune dedupe rows older than 90 days (yard cycles are ~6 weeks).
  await env.DB.prepare("DELETE FROM alerts_sent WHERE sent_at < ?1")
    .bind(new Date(Date.now() - 90 * 86400_000).toISOString()).run();

  return { users: usersAlerted, sends };
}
