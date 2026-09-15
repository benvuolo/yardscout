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
const MAX_WATCHES_FREE = 5;
const MAX_VEHICLES_PER_DIGEST = 6;   // keep the notification readable
const MAX_SENDS_PER_COMMIT = 35;     // subrequest budget (free plan: 50/req)
const MAX_WEEKLY_EMAILS = 40;        // cron invocations get their own budget
const ARRIVALS_RETENTION_DAYS = 10;

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
  const tier = resolveTier(user);
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }

  const make = String(body.make || '').trim().slice(0, 40) || null;
  const model = String(body.model || '').trim().slice(0, 60) || null;
  if (!make && !model) return err(400, 'bad_watch', 'A watch needs at least a make or a model.');
  const yearMin = Number.isFinite(+body.yearMin) && +body.yearMin > 1900 ? Math.floor(+body.yearMin) : null;
  const yearMax = Number.isFinite(+body.yearMax) && +body.yearMax > 1900 ? Math.floor(+body.yearMax) : null;
  const lat = Number.isFinite(+body.lat) ? +body.lat : null;
  const lng = Number.isFinite(+body.lng) ? +body.lng : null;
  let radiusMi = Number.isFinite(+body.radiusMi) && +body.radiusMi > 0
    ? Math.min(Math.floor(+body.radiusMi), 3000) : null;

  // Free watches feed the weekly digest email; instant push stays Pro (the
  // subscribe + dispatch paths check tier). Free watches must be
  // radius-scoped — "anywhere" is the Pro tier of alerts — and free radius
  // caps at 250 mi, mirroring the app's search radius.
  if (tier !== 'pro') {
    if (!radiusMi || lat == null || lng == null) {
      return err(403, 'pro_required', 'Nationwide watches are a Pro feature — free watches need a home ZIP and radius.');
    }
    radiusMi = Math.min(radiusMi, 250);
  }

  const maxWatches = tier === 'pro' ? MAX_WATCHES_PER_USER : MAX_WATCHES_FREE;
  const n = await env.DB.prepare('SELECT COUNT(*) AS n FROM watches WHERE user_id = ?1')
    .bind(user.id).first();
  if ((n?.n || 0) >= maxWatches) {
    return err(400, 'too_many', tier === 'pro'
      ? `Max ${MAX_WATCHES_PER_USER} watches — remove one first.`
      : `Free accounts get ${MAX_WATCHES_FREE} watches — remove one first, or Pro raises the cap to ${MAX_WATCHES_PER_USER}.`);
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

async function emailDigest(env, email, matches, { weekly = false } = {}) {
  if (!env.RESEND_API_KEY) {
    // Local dev has no Resend key — log-and-succeed so e2e tests can assert
    // the dedupe bookkeeping. Production without a key correctly reports
    // undelivered (false) so nothing is marked as sent.
    if (env.DEV_MODE === '1') {
      console.log(`DEV email → ${email} (${weekly ? 'weekly' : 'instant'}): ${matches.length} matches`);
      return true;
    }
    return false;
  }
  const n = matches.length;
  const subject = weekly
    ? `Your week at the yards — ${n} watched car${n === 1 ? '' : 's'} arrived`
    : `${n} watched car${n === 1 ? '' : 's'} just hit the yard`;
  const intro = weekly
    ? 'Arrivals from the past week matching your YardScout watches:'
    : 'New arrivals matching your YardScout watches:';
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'YardScout <onboarding@resend.dev>',
      to: [email],
      subject,
      text:
        `${intro}\n\n${digestText(matches)}\n\n` +
        `Open the app for rows, VINs, and part details:\n${(env.APP_URL || '').trim()}\n\n` +
        `Yards crush cars within weeks — fresh arrivals are the best odds.` +
        (weekly ? `\n\nWant to hear the moment a watched car arrives, not a week later? Instant push alerts are part of Pro.` : ''),
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

/* ===== weekly digest (free tier) =====
 * Pro hears instantly via dispatchAlerts above; free users get one email a
 * week. Arrivals are snapshotted into D1 on every commit so the cron has a
 * week of history to match against. */

/** Called from handleCommit (via ctx.waitUntil). Upserts the commit's
 * arrivals into the rolling window and prunes old rows. */
export async function storeArrivals(env, arrivals) {
  if (!Array.isArray(arrivals) || !arrivals.length) return { stored: 0 };
  const now = isoNow();
  const stmt = env.DB.prepare(
    `INSERT INTO arrivals (vehicle_id, year, make, model, row, location, city, state, lat, lng, date_added, seen_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)
     ON CONFLICT (vehicle_id) DO NOTHING`   // first sighting wins — keeps seen_at honest
  );
  // D1 batches keep this to one round trip per chunk (a commit can carry
  // a few thousand arrivals).
  const CHUNK = 80;
  let stored = 0;
  for (let i = 0; i < arrivals.length; i += CHUNK) {
    const batch = arrivals.slice(i, i + CHUNK).map((v) => stmt.bind(
      String(v.id), v.year ?? null, v.make ?? null, v.model ?? null,
      v.row ?? null, v.location ?? null, v.city ?? null, v.state ?? null,
      v.lat ?? null, v.lng ?? null, v.dateAdded ?? null, now,
    ));
    await env.DB.batch(batch);
    stored += batch.length;
  }
  await env.DB.prepare('DELETE FROM arrivals WHERE seen_at < ?1')
    .bind(new Date(Date.now() - ARRIVALS_RETENTION_DAYS * 86400_000).toISOString()).run();
  return { stored };
}

/** Cron entry point (see wrangler.toml [triggers]): one digest email per
 * free user whose watches matched anything this week. Shares the
 * alerts_sent dedupe with instant alerts, so a user upgraded mid-week never
 * hears about the same car twice. */
export async function sendWeeklyDigests(env) {
  const since = new Date(Date.now() - 7 * 86400_000).toISOString();
  const arrivals = ((await env.DB.prepare(
    'SELECT vehicle_id, year, make, model, row, location, lat, lng FROM arrivals WHERE seen_at >= ?1'
  ).bind(since).all()).results || []).map((r) => ({
    id: r.vehicle_id, year: r.year, make: r.make, model: r.model,
    row: r.row, location: r.location, lat: r.lat, lng: r.lng,
  }));
  if (!arrivals.length) return { users: 0, emails: 0, arrivals: 0 };

  const rows = (await env.DB.prepare(
    `SELECT w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi,
            u.id AS user_id, u.email, u.tier, u.tier_expires_at
       FROM watches w JOIN users u ON u.id = w.user_id`
  ).all()).results || [];

  const byUser = new Map();
  for (const r of rows) {
    if (resolveTier(r) === 'pro') continue;   // Pro already heard instantly
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, { email: r.email, watches: [] });
    byUser.get(r.user_id).watches.push(r);
  }

  let emails = 0, usersMatched = 0;
  for (const [userId, { email, watches }] of byUser) {
    if (emails >= MAX_WEEKLY_EMAILS) { console.log('digest email budget hit — remaining users deferred to next week'); break; }
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;
    const fresh = [];
    for (const v of matched) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM alerts_sent WHERE user_id = ?1 AND vehicle_id = ?2'
      ).bind(userId, String(v.id)).first();
      if (!seen) fresh.push(v);
    }
    if (!fresh.length) continue;
    usersMatched++;
    emails++;
    const delivered = await emailDigest(env, email, fresh, { weekly: true });
    if (delivered) {
      for (const v of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO alerts_sent (user_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(userId, String(v.id), isoNow()).run();
      }
    }
  }
  return { users: usersMatched, emails, arrivals: arrivals.length };
}
