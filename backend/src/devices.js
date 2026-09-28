/* Anonymous native devices (iOS app): APNs push alerts with zero signup.
 *
 * The app registers {deviceId, apnsToken, tier, watches[]} and re-registers
 * whenever watches or tier change. No email, no account:
 *   - Pro devices  → instant push on every inventory commit (arrivals) and
 *                    sale-day pushes, mirroring the account-based Pro path.
 *   - Free devices → ONE weekly summary push from the Monday cron ("Your
 *                    watches matched N arrivals this week"), replacing the
 *                    old weekly digest email.
 *
 * Tier is client-claimed for now — the whole app is client-gated, so this is
 * consistent; App Store receipt validation can harden it later.
 */

import { json, err, isoNow } from './util.js';
import { sendApns, apnsConfigured } from './apns.js';
import { watchMatches, digestText, salesForWatches, fmtSaleRange } from './alerts.js';

const MAX_WATCHES_PER_DEVICE = 20;
const MAX_WATCHES_FREE = 5;
const FREE_RADIUS_CAP_MI = 250;
const MAX_SENDS_PER_COMMIT = 25;    // shares the commit's subrequest budget
const MAX_WEEKLY_PUSHES = 40;
const MAX_SALE_YARDS_PER_PUSH = 3;

function sanitizeWatches(raw, tier) {
  if (!Array.isArray(raw)) return [];
  const cap = tier === 'pro' ? MAX_WATCHES_PER_DEVICE : MAX_WATCHES_FREE;
  const out = [];
  for (const w of raw.slice(0, cap)) {
    const make = String(w.make || '').trim().slice(0, 40) || null;
    const model = String(w.model || '').trim().slice(0, 60) || null;
    if (!make && !model) continue;
    const lat = Number.isFinite(+w.lat) ? +w.lat : null;
    const lng = Number.isFinite(+w.lng) ? +w.lng : null;
    let radiusMi = Number.isFinite(+w.radiusMi) && +w.radiusMi > 0
      ? Math.min(Math.floor(+w.radiusMi), 3000) : null;
    if (tier !== 'pro') {
      // Free watches must be radius-scoped; nationwide is Pro.
      if (lat == null || lng == null || !radiusMi) continue;
      radiusMi = Math.min(radiusMi, FREE_RADIUS_CAP_MI);
    }
    out.push({
      make, model,
      year_min: Number.isFinite(+w.yearMin) && +w.yearMin > 1900 ? Math.floor(+w.yearMin) : null,
      year_max: Number.isFinite(+w.yearMax) && +w.yearMax > 1900 ? Math.floor(+w.yearMax) : null,
      lat: (lat != null && lng != null) ? lat : null,
      lng: (lat != null && lng != null) ? lng : null,
      radius_mi: radiusMi,
    });
  }
  return out;
}

/** POST /v1/device/register — {deviceId, apnsToken?, platform?, tier?, watches?}.
 * Idempotent upsert; called on push-enable and on every watch/tier change. */
export async function handleDeviceRegister(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const deviceId = String(body.deviceId || '');
  if (!/^[0-9a-f-]{36}$/i.test(deviceId)) return err(400, 'bad_device', 'deviceId must be a uuid.');
  const apnsToken = /^[0-9a-f]{32,200}$/i.test(String(body.apnsToken || ''))
    ? String(body.apnsToken).toLowerCase() : null;
  const tier = body.tier === 'pro' ? 'pro' : 'free';
  const watches = sanitizeWatches(body.watches, tier);
  const now = isoNow();

  // The APNs token must be unique — steal it from any stale row (reinstall
  // generates a fresh deviceId but Apple may hand back the same token).
  if (apnsToken) {
    await env.DB.prepare('UPDATE devices SET apns_token = NULL WHERE apns_token = ?1 AND id != ?2')
      .bind(apnsToken, deviceId).run();
  }
  await env.DB.prepare(
    `INSERT INTO devices (id, apns_token, platform, tier, watches_json, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?6)
     ON CONFLICT (id) DO UPDATE SET
       apns_token = COALESCE(?2, apns_token), tier = ?4, watches_json = ?5, updated_at = ?6`
  ).bind(deviceId, apnsToken, String(body.platform || 'ios').slice(0, 12), tier,
         JSON.stringify(watches), now).run();

  // New watches alert on FUTURE arrivals: seed dedupe with current matches.
  const existing = (await env.DB.prepare(
    'SELECT vehicle_id, year, make, model, lat, lng FROM arrivals'
  ).all()).results || [];
  const stmt = env.DB.prepare(
    'INSERT OR IGNORE INTO device_alerts_sent (device_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
  );
  const seeds = existing.filter((v) => watches.some((w) => watchMatches(w, v)))
    .map((v) => stmt.bind(deviceId, String(v.vehicle_id), now));
  for (let i = 0; i < seeds.length; i += 80) await env.DB.batch(seeds.slice(i, i + 80));

  return json({ ok: true, watches: watches.length, push: !!apnsToken && apnsConfigured(env) });
}

/** POST /v1/device/test — {deviceId}: one test push to that device. */
export async function handleDeviceTest(req, env) {
  if (!apnsConfigured(env)) return err(503, 'push_off', 'Native push is not configured yet.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const d = await env.DB.prepare('SELECT apns_token FROM devices WHERE id = ?1')
    .bind(String(body.deviceId || '')).first();
  if (!d || !d.apns_token) return err(404, 'no_token', 'Device has no push token registered.');
  const res = await sendApns(env, d.apns_token, {
    title: 'YardScout test', body: 'Push alerts are working on this device.',
  });
  return json({ ok: res.ok });
}

function parseWatches(row) {
  try { return JSON.parse(row.watches_json || '[]'); } catch { return []; }
}

async function freshOnly(env, deviceId, matched) {
  const fresh = [];
  for (const v of matched) {
    const seen = await env.DB.prepare(
      'SELECT 1 AS x FROM device_alerts_sent WHERE device_id = ?1 AND vehicle_id = ?2'
    ).bind(deviceId, String(v.id)).first();
    if (!seen) fresh.push(v);
  }
  return fresh;
}

async function markSent(env, deviceId, fresh) {
  for (const v of fresh) {
    await env.DB.prepare(
      'INSERT OR IGNORE INTO device_alerts_sent (device_id, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
    ).bind(deviceId, String(v.id), isoNow()).run();
  }
  await env.DB.prepare('UPDATE devices SET last_push_at = ?1 WHERE id = ?2')
    .bind(isoNow(), deviceId).run();
}

/** Instant arrivals push for PRO devices — called from handleCommit alongside
 * dispatchAlerts. Same shape of arrivals array. */
export async function dispatchDeviceAlerts(env, arrivals) {
  if (!apnsConfigured(env) || !Array.isArray(arrivals) || !arrivals.length) {
    return { devices: 0, sends: 0 };
  }
  const rows = (await env.DB.prepare(
    "SELECT id, apns_token, watches_json FROM devices WHERE tier = 'pro' AND apns_token IS NOT NULL"
  ).all()).results || [];
  let sends = 0, devices = 0;
  for (const d of rows) {
    if (sends >= MAX_SENDS_PER_COMMIT) { console.log('device alert budget hit'); break; }
    const watches = parseWatches(d);
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;
    const fresh = await freshOnly(env, d.id, matched);
    if (!fresh.length) continue;
    sends++;
    const res = await sendApns(env, d.apns_token, {
      title: `${fresh.length} watched car${fresh.length === 1 ? '' : 's'} just hit the yard`,
      body: digestText(fresh),
    });
    if (res.gone) {
      await env.DB.prepare('UPDATE devices SET apns_token = NULL WHERE id = ?1').bind(d.id).run();
    } else if (res.ok) {
      devices++;
      await markSent(env, d.id, fresh);
    }
  }
  return { devices, sends };
}

/** Instant sale-day push for PRO devices — called from handleCommit after
 * storeSaleEvents (dispatchSaleAlerts stores them first). */
export async function dispatchDeviceSaleAlerts(env) {
  if (!apnsConfigured(env)) return { devices: 0, sends: 0 };
  const rows = (await env.DB.prepare(
    "SELECT id, apns_token, watches_json FROM devices WHERE tier = 'pro' AND apns_token IS NOT NULL"
  ).all()).results || [];
  let sends = 0, devices = 0;
  for (const d of rows) {
    if (sends >= MAX_SENDS_PER_COMMIT) break;
    const watches = parseWatches(d).filter((w) => w.lat != null && w.radius_mi);
    if (!watches.length) continue;
    const sales = await salesForWatches(env, watches);
    const fresh = [];
    for (const s of sales) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM device_sale_alerts_sent WHERE device_id = ?1 AND event_key = ?2'
      ).bind(d.id, s.event_key).first();
      if (!seen) fresh.push(s);
    }
    if (!fresh.length) continue;
    const shown = fresh.slice(0, MAX_SALE_YARDS_PER_PUSH);
    sends++;
    const res = await sendApns(env, d.apns_token, {
      title: shown[0].pct ? `${shown[0].pct}% off sale near you` : 'Yard sale day near you',
      body: shown.map((s) =>
        `${s.yard} — ${fmtSaleRange(s.start_date, s.end_date)}${s.pct ? ` (${s.pct}% off)` : ''}`
      ).join('\n') + (fresh.length > shown.length ? `\n…and ${fresh.length - shown.length} more` : ''),
    });
    if (res.gone) {
      await env.DB.prepare('UPDATE devices SET apns_token = NULL WHERE id = ?1').bind(d.id).run();
    } else if (res.ok) {
      devices++;
      for (const s of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO device_sale_alerts_sent (device_id, event_key, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(d.id, s.event_key, isoNow()).run();
      }
    }
  }
  return { devices, sends };
}

/** Weekly summary push for FREE devices — cron entry point (replaces the
 * digest email; no email exists in the device model at all). One push per
 * device: arrivals matched this week + upcoming sale days in watch radii. */
export async function sendWeeklyDevicePushes(env) {
  if (!apnsConfigured(env)) return { devices: 0, sends: 0, arrivals: 0 };
  const since = new Date(Date.now() - 7 * 86400_000).toISOString();
  const arrivals = ((await env.DB.prepare(
    'SELECT vehicle_id, year, make, model, row, location, lat, lng FROM arrivals WHERE seen_at >= ?1'
  ).bind(since).all()).results || []).map((r) => ({
    id: r.vehicle_id, year: r.year, make: r.make, model: r.model,
    row: r.row, location: r.location, lat: r.lat, lng: r.lng,
  }));

  const rows = (await env.DB.prepare(
    "SELECT id, apns_token, watches_json FROM devices WHERE tier != 'pro' AND apns_token IS NOT NULL"
  ).all()).results || [];
  let sends = 0, devices = 0;
  for (const d of rows) {
    if (sends >= MAX_WEEKLY_PUSHES) { console.log('weekly push budget hit — deferred to next week'); break; }
    const watches = parseWatches(d);
    if (!watches.length) continue;
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    const fresh = await freshOnly(env, d.id, matched);

    const sales = await salesForWatches(env, watches.filter((w) => w.lat != null && w.radius_mi));
    const freshSales = [];
    for (const s of sales) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM device_sale_alerts_sent WHERE device_id = ?1 AND event_key = ?2'
      ).bind(d.id, s.event_key).first();
      if (!seen) freshSales.push(s);
    }
    if (!fresh.length && !freshSales.length) continue;

    const salesLine = freshSales.length
      ? `\nSale day${freshSales.length === 1 ? '' : 's'}: ` + freshSales.slice(0, 2).map((s) =>
          `${s.yard} ${fmtSaleRange(s.start_date, s.end_date)}`).join(', ')
      : '';
    sends++;
    const res = await sendApns(env, d.apns_token, {
      title: fresh.length
        ? `Your week at the yards — ${fresh.length} watched car${fresh.length === 1 ? '' : 's'} arrived`
        : 'Sale days coming up near you',
      body: (fresh.length
        ? digestText(fresh) + '\nPro members heard about each of these within hours of it landing.'
        : '') + salesLine,
    });
    if (res.gone) {
      await env.DB.prepare('UPDATE devices SET apns_token = NULL WHERE id = ?1').bind(d.id).run();
    } else if (res.ok) {
      devices++;
      await markSent(env, d.id, fresh);
      for (const s of freshSales) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO device_sale_alerts_sent (device_id, event_key, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(d.id, s.event_key, isoNow()).run();
      }
    }
  }
  // Prune dedupe logs (mirrors alerts_sent pruning).
  const cutoff = new Date(Date.now() - 90 * 86400_000).toISOString();
  await env.DB.prepare('DELETE FROM device_alerts_sent WHERE sent_at < ?1').bind(cutoff).run();
  await env.DB.prepare('DELETE FROM device_sale_alerts_sent WHERE sent_at < ?1').bind(cutoff).run();
  return { devices, sends, arrivals: arrivals.length };
}
