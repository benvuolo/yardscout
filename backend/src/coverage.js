/* Coverage requests — the Parts tab's "we don't cover this yet — ask us to
 * add it" flow (owner request, 2026-10).
 *
 *   POST /v1/coverage/request          public, rate-limited in index.js
 *   GET  /v1/admin/coverage            x-admin-secret — counts by request_key
 *   POST /v1/admin/coverage/digest/run x-admin-secret — manual digest trigger
 *
 * Demand surfacing: every inventory commit calls maybeSendCoverageDigest()
 * (ctx.waitUntil in admin.js handleCommit — same piggyback as alert dispatch).
 * If at least one new request arrived since the last digest (window floor
 * ~24h), ONE short email goes to OWNER_EMAIL — never more than one per day,
 * throttled through the coverage_digest_state row so isolate restarts can't
 * double-send. Future coverage workers mine GET /v1/admin/coverage.
 */

import { json, err, isoNow } from './util.js';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const VALID_KINDS = new Set(['car', 'engine', 'part']);

/* Mirrors the app's pfSquash: lowercase alphanumerics only, so "F-150",
 * "F150" and "f 150" aggregate under one request_key. */
const squash = (s) => String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9]/g, '');

/** POST /v1/coverage/request — system boundary: everything validated/clipped
 * server-side, whatever the client claims. No login, append-only. */
export async function handleCoverageRequest(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const clip = (v, n) => String(v == null ? '' : v).trim().slice(0, n);

  const kind = clip(body.kind, 16);
  if (!VALID_KINDS.has(kind)) return err(400, 'bad_kind', 'kind must be car, engine, or part.');

  const year = Number.isFinite(+body.year) && +body.year >= 1900 && +body.year <= 2100
    ? Math.floor(+body.year) : null;
  const make = clip(body.make, 40) || null;
  const model = clip(body.model, 60) || null;
  const part = clip(body.part, 80) || null;
  if (!part && !make && !model) {
    return err(400, 'bad_request', 'Tell us the part or the car — an empty request is nothing to add.');
  }

  const zipRaw = clip(body.zip, 10);
  const zip = /^\d{5}$/.test(zipRaw) ? zipRaw : null;
  const email = clip(body.email, 254).toLowerCase() || null;
  if (email && !EMAIL_RE.test(email)) return err(400, 'bad_email', 'Enter a valid email address (or leave it blank).');
  const note = clip(body.note, 500) || null;

  const requestKey = [kind, year || '', squash(make), squash(model), squash(part)].join('|');
  await env.DB.prepare(
    `INSERT INTO coverage_requests (request_key, kind, year, make, model, part, zip, email, note, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`
  ).bind(requestKey, kind, year, make, model, part, zip, email, note, isoNow()).run();

  return json({ ok: true });
}

/** GET /v1/admin/coverage (x-admin-secret) — request counts grouped by the
 * normalized key (what future coverage workers mine), plus recent raw rows. */
export async function handleCoverageList(req, env) {
  const grouped = (await env.DB.prepare(
    `SELECT request_key, COUNT(*) AS requests,
            MAX(created_at) AS latest_at, MIN(created_at) AS first_at,
            SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) AS with_email,
            MAX(kind) AS kind, MAX(year) AS year, MAX(make) AS make,
            MAX(model) AS model, MAX(part) AS part
       FROM coverage_requests
      GROUP BY request_key
      ORDER BY requests DESC, latest_at DESC
      LIMIT 500`
  ).all()).results || [];
  const recent = (await env.DB.prepare(
    `SELECT request_key, kind, year, make, model, part, zip, email, note, created_at
       FROM coverage_requests ORDER BY id DESC LIMIT 200`
  ).all()).results || [];
  return json({ grouped, recent, keys: grouped.length, total: grouped.reduce((n, g) => n + g.requests, 0) });
}

/* ===== owner digest (piggybacks the inventory-commit hook) ===== */

function fmtReqLine(g) {
  const what = [g.year, g.make, g.model].filter(Boolean).join(' ');
  const label = [what, g.part].filter(Boolean).join(' — ') || g.request_key;
  return `${g.requests}× ${label}  [${g.kind}]${g.with_email ? `  (${g.with_email} left an email)` : ''}`;
}

async function sendDigestEmail(env, groups, total) {
  const to = env.OWNER_EMAIL;
  if (!to) { console.log('coverage digest: OWNER_EMAIL not configured — skipped'); return false; }
  const lines = groups.map(fmtReqLine);
  const subject = `YardScout coverage requests — ${total} new`;
  const text =
    `${total} new coverage request${total === 1 ? '' : 's'} from the Parts tab since the last digest:\n\n`
    + lines.map((l) => `• ${l}`).join('\n')
    + `\n\nFull list (emails + notes): GET /v1/admin/coverage with x-admin-secret.\n`
    + `Requests like these decide what the coverage workers verify next.\n`;
  const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const html =
    `<!doctype html><body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout — Parts tab</p>
  <h2 style="margin:0 0 14px;font-size:19px;color:#fff;">${total} new coverage request${total === 1 ? '' : 's'}</h2>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${groups.map((g) => `
    <tr><td style="padding:8px 0;border-bottom:1px solid #2a2a2a;color:#ddd;font-size:14px;">${esc(fmtReqLine(g))}</td></tr>`).join('')}
  </table>
  <p style="color:#999;font-size:13px;line-height:1.6;margin:16px 0 0;">
    Full list with emails and notes: <code>GET /v1/admin/coverage</code> (x-admin-secret).
    Requests like these decide what the coverage workers verify next.</p>
</div></body>`;

  if (!env.RESEND_API_KEY) {
    // Same convention as the alert senders: local dev logs-and-succeeds so the
    // e2e can assert throttle bookkeeping; prod without a key = undelivered.
    if (env.DEV_MODE === '1') {
      console.log(`DEV coverage digest → ${to}: ${total} requests, ${groups.length} keys`);
      return true;
    }
    return false;
  }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.EMAIL_ALERTS_FROM || 'YardScout Alerts <alerts@yardscout.io>',
      to: [to], subject, text, html,
    }),
  });
  if (!r.ok) {
    console.log('coverage digest email failed:', r.status, (await r.text()).slice(0, 200));
    return false;
  }
  const sent = await r.json().catch(() => ({}));
  console.log(`coverage digest sent to ${to}: ${total} requests, resend id ${sent.id || '?'}`);
  return true;
}

/** Called from handleCommit via ctx.waitUntil (scans run ~every 4h) and from
 * the manual admin trigger. Sends at most one digest email per 24h, covering
 * everything since the last digest (floor: 24h ago on the first ever run so
 * an old backlog doesn't arrive as a wall of text — it lives in the admin GET). */
export async function maybeSendCoverageDigest(env) {
  const state = await env.DB.prepare('SELECT last_sent_at FROM coverage_digest_state WHERE id = 1').first();
  const dayAgo = new Date(Date.now() - 24 * 3600_000).toISOString();
  if (state && state.last_sent_at > dayAgo) {
    return { sent: false, reason: 'throttled', lastSentAt: state.last_sent_at };
  }
  const since = state && state.last_sent_at < dayAgo ? state.last_sent_at : dayAgo;
  const groups = (await env.DB.prepare(
    `SELECT request_key, COUNT(*) AS requests,
            SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) AS with_email,
            MAX(kind) AS kind, MAX(year) AS year, MAX(make) AS make,
            MAX(model) AS model, MAX(part) AS part
       FROM coverage_requests WHERE created_at > ?1
      GROUP BY request_key ORDER BY requests DESC LIMIT 50`
  ).bind(since).all()).results || [];
  const total = groups.reduce((n, g) => n + g.requests, 0);
  if (!total) return { sent: false, reason: 'no_new_requests', since };

  const delivered = await sendDigestEmail(env, groups, total);
  if (delivered) {
    await env.DB.prepare(
      `INSERT INTO coverage_digest_state (id, last_sent_at) VALUES (1, ?1)
       ON CONFLICT (id) DO UPDATE SET last_sent_at = ?1`
    ).bind(isoNow()).run();
  }
  return { sent: delivered, requests: total, keys: groups.length, since };
}
