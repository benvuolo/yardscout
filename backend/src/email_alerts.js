/* Email alerts for web Pro members — the web counterpart of the native APNs
 * flow in devices.js.
 *
 * The web app has no accounts. A Pro member's identity is their entitlement
 * email (ENTITLEMENTS KV, written by the site Worker's entitlements.js; the
 * same namespace is bound to this Worker read/write so sync can validate
 * device tokens and dispatch can re-check Pro at send time). The web app
 * mirrors its localStorage watchlist here exactly like the native app mirrors
 * watches into `devices`:
 *
 *   POST /v1/email-alerts/sync {token, watches[], enabled?}
 *     token = the 64-hex entitlement device token (tok:<token> → email).
 *     Pro-gated: a lapsed entitlement cannot sync.
 *
 * Dispatch rides the same post-scan commit hook as push (admin.js
 * handleCommit → ctx.waitUntil): ONE email per subscriber per scan cycle
 * listing every new match, deduped per (email, vehicle) in email_alerts_sent
 * so overlapping scan windows never re-email the same car.
 *
 * Deliverability (non-negotiable):
 *   - every email carries a signed one-click unsubscribe link (no login), plus
 *     List-Unsubscribe / List-Unsubscribe-Post headers for mailbox providers;
 *   - unsubscribing kills the email channel only (enabled=0) — Pro is untouched;
 *   - the entitlement is re-checked in KV at send time, so a lapsed
 *     subscription stops emailing without any extra machinery.
 *
 * Copy stays honest about cadence: scans run ~every 6 hours, so alerts say
 * "same day", never "instant".
 */

import { json, err, isoNow } from './util.js';
import { watchMatches } from './alerts.js';

const MAX_WATCHES = 20;                 // mirrors MAX_WATCHES_PER_USER / device cap
const MAX_EMAILS_PER_COMMIT = 20;       // subrequest budget (shared with push sends)
const MAX_VEHICLES_PER_EMAIL = 30;      // one digest email, never one-per-car

/* ===== entitlement lookups (ENTITLEMENTS KV — shared with the site Worker) ===== */

function entActive(ent) {
  return !!(ent && ent.pro && (!ent.expiresAt || Date.parse(ent.expiresAt) > Date.now()));
}

/** 64-hex device token → {email, ent} or null. Same tok:/ent: layout the
 * site Worker writes (backend/site-proxy/src/entitlements.js). */
async function resolveEntToken(env, token) {
  if (!env.ENTITLEMENTS || !/^[0-9a-f]{64}$/.test(String(token || ''))) return null;
  const rec = await env.ENTITLEMENTS.get('tok:' + token, 'json');
  if (!rec || !rec.email) return null;
  const ent = await env.ENTITLEMENTS.get('ent:' + rec.email, 'json');
  return { email: rec.email, ent };
}

/* ===== watch sanitizing (same shape devices.js stores) ===== */

function sanitizeWatches(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  for (const w of raw.slice(0, MAX_WATCHES)) {
    const make = String(w.make || '').trim().slice(0, 40) || null;
    const model = String(w.model || '').trim().slice(0, 60) || null;
    if (!make && !model) continue;
    const lat = Number.isFinite(+w.lat) ? +w.lat : null;
    const lng = Number.isFinite(+w.lng) ? +w.lng : null;
    const radiusMi = Number.isFinite(+w.radiusMi) && +w.radiusMi > 0
      ? Math.min(Math.floor(+w.radiusMi), 3000) : null;
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

/* ===== signed unsubscribe tokens (no login, no expiry) ===== */

const b64u = {
  enc: (s) => btoa(String.fromCharCode(...new TextEncoder().encode(s)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''),
  dec: (s) => {
    const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/'));
    return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  },
};

async function unsubSig(env, email) {
  const secret = env.EMAIL_UNSUB_SECRET || '';
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode('ys-unsub:' + secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(email));
  return [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function unsubUrl(env, email) {
  const base = (env.API_PUBLIC_URL || 'https://yardscout-api.yardscout.workers.dev').replace(/\/+$/, '');
  return `${base}/v1/email-alerts/unsubscribe?e=${encodeURIComponent(b64u.enc(email))}&sig=${await unsubSig(env, email)}`;
}

/* ===== sync + status (called by the web app) ===== */

/** POST /v1/email-alerts/sync {token, watches?, enabled?} — upsert the
 * subscriber row for the token's entitlement email. Pro-gated. */
export async function handleEmailAlertsSync(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const resolved = await resolveEntToken(env, body.token);
  if (!resolved) return err(401, 'bad_token', 'Unlock Pro on this device first.');
  if (!entActive(resolved.ent)) {
    return err(403, 'pro_required', 'Email alerts are a Pro feature — your Pro has lapsed.');
  }
  const email = resolved.email;
  const watches = sanitizeWatches(body.watches);
  const enabled = body.enabled === false ? 0 : 1;
  const now = isoNow();

  await env.DB.prepare(
    `INSERT INTO email_watchers (email, watches_json, enabled, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?4)
     ON CONFLICT (email) DO UPDATE SET watches_json = ?2, enabled = ?3, updated_at = ?4`
  ).bind(email, JSON.stringify(watches), enabled, now).run();

  // Watches alert on FUTURE arrivals only (same contract as accounts and
  // devices): seed the dedupe log with everything currently matching.
  const existing = (await env.DB.prepare(
    'SELECT vehicle_id, year, make, model, lat, lng FROM arrivals'
  ).all()).results || [];
  const stmt = env.DB.prepare(
    'INSERT OR IGNORE INTO email_alerts_sent (email, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
  );
  const seeds = existing.filter((v) => watches.some((w) => watchMatches(w, v)))
    .map((v) => stmt.bind(email, String(v.vehicle_id), now));
  for (let i = 0; i < seeds.length; i += 80) await env.DB.batch(seeds.slice(i, i + 80));

  return json({ ok: true, email, enabled: !!enabled, watches: watches.length, seeded: seeds.length });
}

/** GET /v1/email-alerts/status?token= → {pro, email, enabled, watches} */
export async function handleEmailAlertsStatus(req, env, url) {
  const resolved = await resolveEntToken(env, url.searchParams.get('token'));
  if (!resolved) return err(401, 'bad_token', 'Unlock Pro on this device first.');
  const pro = entActive(resolved.ent);
  const row = await env.DB.prepare(
    'SELECT watches_json, enabled FROM email_watchers WHERE email = ?1'
  ).bind(resolved.email).first();
  let n = 0;
  try { n = JSON.parse(row?.watches_json || '[]').length; } catch { /* count stays 0 */ }
  return json({
    pro, email: resolved.email,
    enabled: !!(row && row.enabled), synced: !!row, watches: n,
  });
}

/* ===== unsubscribe (signed link — GET from the email, POST for RFC 8058
 * one-click from mailbox providers). Kills the email channel only. ===== */

export async function handleEmailAlertsUnsubscribe(req, env, url) {
  let email;
  try { email = b64u.dec(url.searchParams.get('e') || ''); } catch { email = ''; }
  const sig = String(url.searchParams.get('sig') || '');
  if (!email || !/^[0-9a-f]{64}$/.test(sig) || sig !== await unsubSig(env, email)) {
    return err(400, 'bad_link', 'This unsubscribe link is invalid.');
  }
  await env.DB.prepare(
    `INSERT INTO email_watchers (email, watches_json, enabled, created_at, updated_at)
     VALUES (?1, '[]', 0, ?2, ?2)
     ON CONFLICT (email) DO UPDATE SET enabled = 0, updated_at = ?2`
  ).bind(email, isoNow()).run();

  if (req.method === 'POST') return json({ ok: true, unsubscribed: true });
  return new Response(
    `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unsubscribed — YardScout</title>
<body style="font-family:system-ui,sans-serif;background:#111;color:#eee;display:grid;place-items:center;min-height:90vh;margin:0;">
<div style="max-width:28rem;padding:2rem;text-align:center;">
<h2 style="margin:0 0 .5rem;">You're unsubscribed</h2>
<p style="color:#aaa;line-height:1.6;">No more email alerts to <strong>${email.replace(/</g, '&lt;')}</strong>.
Your Pro membership and your watchlist are unchanged — you can turn email alerts
back on any time from the Alerts tab at
<a href="https://yardscout.io/" style="color:#f90;">yardscout.io</a>.</p>
</div>`,
    { headers: { 'content-type': 'text/html; charset=utf-8' } });
}

/* ===== dispatch (called from handleCommit via ctx.waitUntil) ===== */

function fmtCar(v) {
  return `${v.year || ''} ${v.make || ''} ${v.model || ''}`.replace(/\s+/g, ' ').trim();
}

function carUrl(env, v) {
  const base = (env.APP_URL || 'https://yardscout.io/').replace(/\/+$/, '');
  return `${base}/#car=${encodeURIComponent(String(v.id))}`;
}

const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

async function sendAlertEmail(env, email, matches) {
  const unsub = await unsubUrl(env, email);
  const n = matches.length;
  const shown = matches.slice(0, MAX_VEHICLES_PER_EMAIL);
  const more = n - shown.length;

  const textLines = shown.map((v) =>
    `• ${fmtCar(v)} — ${v.location || 'unknown yard'}${v.row ? ` (Row ${v.row})` : ''}\n  ${carUrl(env, v)}`);
  if (more > 0) textLines.push(`…and ${more} more on the site.`);
  const text =
    `${n} watched car${n === 1 ? '' : 's'} just showed up at the yard — found by the latest inventory scan:\n\n` +
    textLines.join('\n\n') +
    `\n\nYards crush cars within weeks — fresh arrivals are your best odds.\n` +
    `Scans run about every 6 hours, so you hear the same day a car is listed.\n\n` +
    `Manage watches: ${(env.APP_URL || 'https://yardscout.io/')}\n` +
    `Unsubscribe from email alerts (Pro is unaffected): ${unsub}\n`;

  const htmlRows = shown.map((v) => `
    <tr><td style="padding:10px 0;border-bottom:1px solid #2a2a2a;">
      <a href="${carUrl(env, v)}" style="color:#ff9500;font-weight:600;text-decoration:none;font-size:15px;">${esc(fmtCar(v))}</a><br>
      <span style="color:#999;font-size:13px;">${esc(v.location || 'unknown yard')}${v.row ? ` &middot; Row ${esc(v.row)}` : ''}${v.dateAdded ? ` &middot; listed ${esc(v.dateAdded)}` : ''}</span>
    </td></tr>`).join('');
  const html =
    `<!doctype html><body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout alert</p>
  <h2 style="margin:0 0 14px;font-size:19px;color:#fff;">${n} watched car${n === 1 ? '' : 's'} just hit the yard</h2>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${htmlRows}</table>
  ${more > 0 ? `<p style="color:#999;font-size:13px;">…and ${more} more on the site.</p>` : ''}
  <p style="color:#999;font-size:13px;line-height:1.6;margin:16px 0 0;">
    Yards crush cars within weeks — fresh arrivals are your best odds.
    Scans run about every 6 hours, so you hear the same day a car is listed.</p>
  <p style="margin:18px 0 0;"><a href="${esc((env.APP_URL || 'https://yardscout.io/'))}" style="color:#ff9500;font-size:13px;">Manage your watchlist</a></p>
  <p style="color:#666;font-size:11px;margin:22px 0 0;border-top:1px solid #2a2a2a;padding-top:12px;">
    You get these because email alerts are on for ${esc(email)} (a YardScout Pro perk).
    <a href="${unsub}" style="color:#888;">Unsubscribe from email alerts</a> — your Pro membership is unaffected.</p>
</div></body>`;

  if (!env.RESEND_API_KEY) {
    // Local dev: log-and-succeed so e2e can assert dedupe bookkeeping (same
    // convention as emailDigest in alerts.js). Prod without a key = undelivered.
    if (env.DEV_MODE === '1') {
      console.log(`DEV alert email → ${email}: ${n} matches; unsub ${unsub}`);
      return true;
    }
    return false;
  }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_ALERTS_FROM || 'YardScout Alerts <alerts@yardscout.io>',
      to: [email],
      subject: `${n} watched car${n === 1 ? '' : 's'} just hit the yard`,
      text, html,
      headers: {
        'List-Unsubscribe': `<${unsub}>`,
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
      },
    }),
  });
  if (!r.ok) {
    console.log('alert email failed:', r.status, (await r.text()).slice(0, 200));
    return false;
  }
  // Log the Resend id — lets ops cross-check a send in the Resend dashboard.
  const sent = await r.json().catch(() => ({}));
  console.log(`alert email sent to ${email}: ${n} cars, resend id ${sent.id || '?'}`);
  return true;
}

/** One digest email per subscriber whose watches matched this commit's new
 * arrivals. Pro is re-checked in KV per subscriber at send time. */
export async function dispatchEmailAlerts(env, arrivals) {
  if (!Array.isArray(arrivals) || !arrivals.length || !env.ENTITLEMENTS) {
    return { users: 0, emails: 0 };
  }
  const rows = (await env.DB.prepare(
    'SELECT email, watches_json FROM email_watchers WHERE enabled = 1'
  ).all()).results || [];

  let emails = 0, users = 0;
  for (const row of rows) {
    if (emails >= MAX_EMAILS_PER_COMMIT) { console.log('email alert budget hit — remaining deferred'); break; }
    let watches;
    try { watches = JSON.parse(row.watches_json || '[]'); } catch { watches = []; }
    if (!watches.length) continue;
    const matched = arrivals.filter((v) => watches.some((w) => watchMatches(w, v)));
    if (!matched.length) continue;

    // Dedupe BEFORE the (costly) entitlement read.
    const fresh = [];
    for (const v of matched) {
      const seen = await env.DB.prepare(
        'SELECT 1 AS x FROM email_alerts_sent WHERE email = ?1 AND vehicle_id = ?2'
      ).bind(row.email, String(v.id)).first();
      if (!seen) fresh.push(v);
    }
    if (!fresh.length) continue;

    // Pro gate at send time: entitlement lapsed/refunded → no email, row kept
    // (re-subscribing after a renewal needs no re-sync).
    const ent = await env.ENTITLEMENTS.get('ent:' + row.email, 'json');
    if (!entActive(ent)) continue;

    emails++;
    const delivered = await sendAlertEmail(env, row.email, fresh);
    if (delivered) {
      users++;
      for (const v of fresh) {
        await env.DB.prepare(
          'INSERT OR IGNORE INTO email_alerts_sent (email, vehicle_id, sent_at) VALUES (?1, ?2, ?3)'
        ).bind(row.email, String(v.id), isoNow()).run();
      }
      await env.DB.prepare('UPDATE email_watchers SET last_email_at = ?1 WHERE email = ?2')
        .bind(isoNow(), row.email).run();
    }
  }
  // Prune dedupe rows alongside the other sent-logs (90 days).
  await env.DB.prepare('DELETE FROM email_alerts_sent WHERE sent_at < ?1')
    .bind(new Date(Date.now() - 90 * 86400_000).toISOString()).run();
  return { users, emails };
}

/* ===== test/ops helpers ===== */

/** POST /v1/admin/email-alerts/dispatch {arrivals:[...]} (x-admin-secret) —
 * manual dispatch trigger. Runs the EXACT production path (matching, dedupe,
 * send-time Pro gate, Resend send) against caller-supplied arrivals, without
 * touching the inventory tables. Used by the e2e test and for ops smoke
 * tests against production. */
export async function handleEmailAlertsDispatchRun(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const r = await dispatchEmailAlerts(env, Array.isArray(body.arrivals) ? body.arrivals : []);
  return json(r);
}

/** POST /v1/admin/test/ent {email, token, pro?, expiresAt?} — DEV ONLY seam:
 * writes tok:/ent: records into the (local, empty) ENTITLEMENTS KV so the e2e
 * test can mint entitlements without the site Worker. 404s outside DEV_MODE. */
export async function handleTestEntitlement(req, env) {
  if (env.DEV_MODE !== '1') return err(404, 'not_found', 'No such endpoint.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = String(body.email || '').toLowerCase();
  const token = String(body.token || '');
  if (!email || !/^[0-9a-f]{64}$/.test(token)) return err(400, 'bad_input', 'email + 64-hex token required.');
  await env.ENTITLEMENTS.put('ent:' + email, JSON.stringify({
    pro: body.pro !== false,
    source: 'test',
    expiresAt: body.expiresAt || null,
    createdAt: isoNow(),
  }));
  await env.ENTITLEMENTS.put('tok:' + token, JSON.stringify({ email, createdAt: isoNow() }));
  return json({ ok: true, email });
}
