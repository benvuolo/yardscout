/* Saved-car alerts (Pro): "it's gone" / "leaving soon" for the yard-visit list.
 *
 * Clients mirror their saved cars (docs/app.js savedCars — VIN-or-id keys
 * plus year/make/model/location for the message) on the SAME sync paths
 * that carry watches: native devices via /v1/device/register (saved_json on
 * `devices`), web Pro members via /v1/email-alerts/sync (saved_json on
 * `email_watchers`). Capped at 50 keys per owner.
 *
 * Dispatch rides the post-scan commit hook (admin.js handleCommit →
 * ctx.waitUntil) next to the watch dispatches. For each owner's keys it
 * resolves the car exactly like handleVehicleDetail: vindex bucket shard →
 * ONE yard shard (never a scan of all vehicles), both memoized for the run.
 *   - key not in the vindex (or not in its yard shard) → "gone" alert, once,
 *     ever (saved_alerts_sent kind='gone' ends the key's story). Guarded by
 *     the saved yard still being in the directory, so a yard that dropped out
 *     of a scan doesn't read as "everything there got crushed".
 *   - present and daysOn >= 0.8 × the yard's avgLifespanDays (and not past
 *     2× — the card stops claiming "leaving soon" there too) → "leaving soon"
 *     alert, once per key.
 * Pro is enforced per owner: devices by tier, email watchers by the KV
 * entitlement at send time. Free users get nothing here.
 *
 * CPU budget: shard parses are capped per run (MAX_YARD_PARSES) and so are
 * keys (MAX_KEYS_PER_RUN); anything deferred is picked up on the next commit
 * (~every 4 hours), which is well inside the "leaving soon" window.
 */

import { json, err, isoNow, gunzipToText, vindexBucket } from './util.js';
import { getDirectory } from './inventory.js';
import { sendDevicePush, devicePushConfigured } from './devices.js';
import { entActive, esc, unsubUrl } from './email_alerts.js';
import { resendFetch } from './ops.js';

const MAX_SAVED_PER_OWNER = 50;
const MAX_KEYS_PER_RUN = 300;      // ~2 resolves/ms worst case; well under the budget
const MAX_YARD_PARSES = 40;        // largest shard ≈ 300KB / 2-3ms each
const MAX_SENDS_PER_RUN = 20;      // shares the commit's subrequest budget
const LEAVING_RATIO = 0.8;         // mirrors the card's "leavingSoon" rule
const PAST_TYPICAL_RATIO = 2;      // past this the card stops claiming "soon"
const SENT_RETENTION_DAYS = 180;

/** Client payload → stored shape. Keys are VIN (uppercase) or scraper id. */
export function sanitizeSaved(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  const seen = new Set();
  for (const s of raw.slice(0, MAX_SAVED_PER_OWNER)) {
    let key = String((s && s.key) || '').trim().slice(0, 32);
    if (/[a-z]/.test(key)) key = key.toUpperCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push({
      key,
      year: Number.isFinite(+s.year) ? Math.floor(+s.year) : null,
      make: String(s.make || '').trim().slice(0, 40),
      model: String(s.model || '').trim().slice(0, 60),
      location: String(s.location || '').trim().slice(0, 80),
    });
  }
  return out;
}

function parseSaved(rowJson) {
  try { const v = JSON.parse(rowJson || '[]'); return Array.isArray(v) ? v : []; } catch { return []; }
}

function daysOnLot(dateAdded) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(dateAdded || ''));
  if (!m) return null;
  const t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  if (!Number.isFinite(t) || t > Date.now() + 2 * 86400_000) return null;
  return Math.max(0, Math.floor((Date.now() - t) / 86400_000));
}

function carName(s) {
  return `${s.year || ''} ${s.make || ''} ${s.model || ''}`.replace(/\s+/g, ' ').trim() || 'car';
}

/** Alert copy — the only place the wording lives. */
export function savedAlertPayload(ev) {
  const name = carName(ev.saved);
  const where = ev.saved.location ? ` at ${ev.saved.location}` : '';
  if (ev.kind === 'gone') {
    return {
      title: 'Saved car is off the yard’s list',
      body: `Your saved ${name}${where} is off the yard’s list — pulled or crushed.`,
      url: '/',
    };
  }
  const basis = ev.basis === 'yard' ? 'cars at this yard'
    : ev.basis === 'chain' ? 'cars at this chain' : 'cars at covered yards';
  return {
    title: `${name} — leaving soon?`,
    body: `Day ${ev.daysOn + 1} on the lot${where} — ${basis} typically last ~${ev.avg} days. Go soon if you want it.`,
    url: '/#alert=' + encodeURIComponent(String(ev.id)),
  };
}

/* ----- shard resolver (memoized per run, budgeted) ----- */

function makeResolver(env, dir) {
  const mod = dir.vindexMod || 64;
  const buckets = new Map();   // bucket → index object | null
  const shards = new Map();    // yardIdx → parsed shard | null
  let yardParses = 0;
  const f = dir.fields || [];
  const iId = f.indexOf('id'), iVin = f.indexOf('vin'), iDate = f.indexOf('dateAdded');

  async function loadBucket(b) {
    if (buckets.has(b)) return buckets.get(b);
    const row = await env.DB.prepare(
      'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
    ).bind('vindex', String(b), 'all').first();
    const idx = row ? JSON.parse(await gunzipToText(row.body)) : null;
    buckets.set(b, idx);
    return idx;
  }
  async function loadShard(yardIdx) {
    if (shards.has(yardIdx)) return shards.get(yardIdx);
    if (yardParses >= MAX_YARD_PARSES) return undefined;   // budget — defer
    yardParses++;
    const row = await env.DB.prepare(
      'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
    ).bind('yard', String(yardIdx), 'free').first();   // vpic/dates identical across variants
    const shard = row ? JSON.parse(await gunzipToText(row.body)) : null;
    shards.set(yardIdx, shard);
    return shard;
  }

  /** → {state:'gone'} | {state:'present', id, yardIdx, dateAdded} | {state:'deferred'} */
  return async function resolve(key) {
    const idx = await loadBucket(vindexBucket(key, mod));
    const hit = idx && idx[key];
    if (!hit) return { state: 'gone' };
    const [yardIdx, id] = hit;
    const shard = await loadShard(yardIdx);
    if (shard === undefined) return { state: 'deferred' };
    const row = shard && shard.vehicles.find((r) => String(r[iId]) === String(id) || String(r[iVin]) === key);
    if (!row) return { state: 'gone' };
    return { state: 'present', id: row[iId], yardIdx, dateAdded: row[iDate] };
  };
}

/* ----- per-owner evaluation ----- */

async function sentFor(env, ownerKind, ownerId) {
  const rows = (await env.DB.prepare(
    'SELECT vehicle_key, kind FROM saved_alerts_sent WHERE owner_kind = ?1 AND owner_id = ?2'
  ).bind(ownerKind, ownerId).all()).results || [];
  const m = new Map();
  for (const r of rows) m.set(r.vehicle_key + '|' + r.kind, true);
  return m;
}

async function markSent(env, ownerKind, ownerId, events) {
  const stmt = env.DB.prepare(
    'INSERT OR IGNORE INTO saved_alerts_sent (owner_kind, owner_id, vehicle_key, kind, sent_at) VALUES (?1, ?2, ?3, ?4, ?5)'
  );
  const now = isoNow();
  await env.DB.batch(events.map((ev) => stmt.bind(ownerKind, ownerId, ev.saved.key, ev.kind, now)));
}

/** Events for one owner's saved list. budget.keys is decremented. */
async function eventsFor(env, dir, resolve, ownerKind, ownerId, saved, budget) {
  const sent = await sentFor(env, ownerKind, ownerId);
  const yardByLoc = dir._yardByLoc;
  const out = [];
  for (const s of saved) {
    if (!s || !s.key || sent.has(s.key + '|gone')) continue;
    if (budget.keys <= 0) { budget.deferred++; continue; }
    budget.keys--;
    const r = await resolve(s.key);
    if (r.state === 'deferred') { budget.deferred++; continue; }
    if (r.state === 'gone') {
      // Only when the saved yard is still being tracked — otherwise the
      // whole yard vanished from the scan, which says nothing about the car.
      if (s.location && yardByLoc.has(s.location)) out.push({ kind: 'gone', saved: s });
      continue;
    }
    if (sent.has(s.key + '|leaving')) continue;
    const y = dir.yards[r.yardIdx] || [];
    const avg = y[5];
    const daysOn = daysOnLot(r.dateAdded);
    if (!avg || daysOn == null) continue;
    if (daysOn >= LEAVING_RATIO * avg && daysOn <= PAST_TYPICAL_RATIO * avg) {
      out.push({ kind: 'leaving', saved: s, id: r.id, daysOn, avg, basis: y[6] || 'all' });
    }
  }
  return out;
}

/* ----- email channel (web Pro members) ----- */

async function sendSavedEmail(env, email, events) {
  const unsub = await unsubUrl(env, email);
  const lines = events.map((ev) => savedAlertPayload(ev));
  const subject = events.length === 1
    ? lines[0].title
    : `${events.length} updates on your saved cars`;
  const text = lines.map((l) => `${l.title}\n${l.body}`).join('\n\n')
    + `\n\nOpen your saved list: ${(env.APP_URL || 'https://yardscout.io/')}\n`
    + `Unsubscribe from email alerts (Pro is unaffected): ${unsub}\n`;
  const html = `<!doctype html><body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout saved-car alert</p>
  ${lines.map((l) => `<h2 style="margin:14px 0 4px;font-size:17px;color:#fff;">${esc(l.title)}</h2>
  <p style="color:#ccc;font-size:14px;line-height:1.6;margin:0;">${esc(l.body)}</p>`).join('')}
  <p style="margin:18px 0 0;"><a href="${esc(env.APP_URL || 'https://yardscout.io/')}" style="color:#ff9500;font-size:13px;">Open your saved list</a></p>
  <p style="color:#666;font-size:11px;margin:22px 0 0;border-top:1px solid #2a2a2a;padding-top:12px;">
    You get these because email alerts are on for ${esc(email)} (a YardScout Pro perk).
    <a href="${unsub}" style="color:#888;">Unsubscribe from email alerts</a> — your Pro membership is unaffected.</p>
</div></body>`;
  if (!env.RESEND_API_KEY) {
    if (env.DEV_MODE === '1') { console.log(`DEV saved-car email → ${email}: ${events.length} events`); return true; }
    return false;
  }
  const r = await resendFetch(env, 'email:saved', email, {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_ALERTS_FROM || 'YardScout Alerts <alerts@yardscout.io>',
      to: [email], subject, text, html,
      headers: { 'List-Unsubscribe': `<${unsub}>`, 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' },
    }),
  });
  if (!r.ok) console.log('saved-car email failed:', r.status, (await r.text()).slice(0, 200));
  return r.ok;
}

/* ----- entry point (handleCommit → ctx.waitUntil) ----- */

export async function dispatchSavedCarAlerts(env) {
  const stats = { devices: 0, emails: 0, sends: 0, gone: 0, leaving: 0, deferred: 0 };
  const dir = await getDirectory(env);
  if (!dir || !Array.isArray(dir.yards)) return stats;
  dir._yardByLoc = new Map(dir.yards.map((y, i) => [y[0], i]));
  const resolve = makeResolver(env, dir);
  const budget = { keys: MAX_KEYS_PER_RUN, deferred: 0 };

  // Native Pro devices → one push per event.
  if (devicePushConfigured(env)) {
    const rows = (await env.DB.prepare(
      `SELECT id, apns_token, fcm_token, saved_json FROM devices
        WHERE tier = 'pro' AND saved_json IS NOT NULL AND (apns_token IS NOT NULL OR fcm_token IS NOT NULL)`
    ).all()).results || [];
    for (const d of rows) {
      if (stats.sends >= MAX_SENDS_PER_RUN || budget.keys <= 0) break;
      const events = await eventsFor(env, dir, resolve, 'device', d.id, parseSaved(d.saved_json), budget);
      const delivered = [];
      for (const ev of events) {
        if (stats.sends >= MAX_SENDS_PER_RUN) break;
        stats.sends++;
        const res = await sendDevicePush(env, d, savedAlertPayload(ev));
        if (res.ok) delivered.push(ev);
      }
      if (delivered.length) {
        stats.devices++;
        await markSent(env, 'device', d.id, delivered);
        for (const ev of delivered) stats[ev.kind]++;
      }
    }
  }

  // Web Pro members with email alerts on → one email per member per run.
  if (env.ENTITLEMENTS) {
    const rows = (await env.DB.prepare(
      'SELECT email, saved_json FROM email_watchers WHERE enabled = 1 AND saved_json IS NOT NULL'
    ).all()).results || [];
    for (const row of rows) {
      if (stats.sends >= MAX_SENDS_PER_RUN || budget.keys <= 0) break;
      const events = await eventsFor(env, dir, resolve, 'email', row.email, parseSaved(row.saved_json), budget);
      if (!events.length) continue;
      const ent = await env.ENTITLEMENTS.get('ent:' + row.email, 'json');
      if (!entActive(ent)) continue;   // lapsed Pro: nothing, row kept
      stats.sends++;
      if (await sendSavedEmail(env, row.email, events)) {
        stats.emails++;
        await markSent(env, 'email', row.email, events);
        for (const ev of events) stats[ev.kind]++;
      }
    }
  }

  stats.deferred = budget.deferred;
  await env.DB.prepare('DELETE FROM saved_alerts_sent WHERE sent_at < ?1')
    .bind(new Date(Date.now() - SENT_RETENTION_DAYS * 86400_000).toISOString()).run();
  return stats;
}

/** POST /v1/admin/saved-alerts/dispatch (x-admin-secret) — manual trigger of
 * the exact production path against the live inventory shards. */
export async function handleSavedAlertsDispatchRun(req, env) {
  try {
    return json(await dispatchSavedCarAlerts(env));
  } catch (e) {
    return err(500, 'dispatch_failed', String(e && e.message || e));
  }
}
