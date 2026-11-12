/* Free Monday email for web visitors (2026-11-12, owner approved).
 *
 * A watch set on the web lives only in that browser. Right after a watch,
 * the web app offers one line: an email field for a free Monday email
 * listing cars matching that watch that were set out near the visitor. No
 * account, no password. This module is the whole server side:
 *
 *   POST /v1/recap/signup {email, watch}  store the address + a COPY of the
 *        watch criteria (pending), send ONE confirmation email
 *   GET  /v1/recap/confirm?t=             page with a "Confirm" button (a
 *        mail scanner that fetches links must not opt anyone in)
 *   POST /v1/recap/confirm  t=            double opt-in: address and its
 *        pending watches confirmed → 303 to the app (#recap=confirmed&sub=)
 *   POST /v1/recap/add {sub, watch}       a later watch joins a confirmed
 *        recap in one tap (sub = signed token handed over by the confirm
 *        redirect, so only the inbox owner holds it)
 *   GET|POST /v1/recap/unsubscribe?e=&sig=  one click: DELETES the address,
 *        every copied watch and its dedupe rows (POST = RFC 8058)
 *
 * The Monday job (alerts.js sendWeeklyDigests) reads confirmed rows only.
 *
 * Rule 6: the browser's watch is never read back or changed. The server
 * keeps its own copy (recap_watches), made at sign-up, and deletes it on
 * unsubscribe; nothing here touches watches, devices or email_watchers.
 *
 * Privacy: no IP is stored (the per-IP limit is the in-memory bucket in
 * util.js); logs carry masked addresses only (maskEmail). The response to a
 * sign-up does not say whether the address was already subscribed.
 *
 * Resend daily cap: a confirmation is an optional send. While fewer than
 * RESEND_RESERVE sends are left today (ops.js optionalEmailAllowed) the
 * sign-up is refused with 'daily_cap', nothing is stored, and the held send
 * is counted (email:confirm:held) for the daily ops email.
 */

import { json, err, sha256Hex, randomToken, isoNow, rateLimit } from './util.js';
import { resendFetch, countHeld, optionalEmailAllowed } from './ops.js';

export const RECAP_MAX_WATCHES = 5;          // the free watch limit (docs/app.js FREE_WATCH_LIMIT)
const RECAP_MAX_RADIUS = 250;                // the free search radius cap
const CONFIRM_TTL_MS = 7 * 86400_000;        // confirmation link lifetime; unconfirmed rows pruned after it
const CONFIRM_REUSE_MS = 3600_000;           // a second watch within an hour rides the link already sent
const CONFIRMS_PER_DAY = 3;                  // persistent per-address cap on confirmation emails
const IP_SIGNUPS_PER_HOUR = 8;               // in-memory, per isolate (no IP stored)
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/* ===== small helpers ===== */

/** "benvuolo@gmail.com" → "b•••@gmail.com". Logs and pages use this only. */
export function maskEmail(email) {
  const s = String(email || '');
  const at = s.lastIndexOf('@');
  if (at < 1) return '•••';
  return `${s[0]}•••${s.slice(at)}`;
}

const b64u = {
  enc: (s) => btoa(String.fromCharCode(...new TextEncoder().encode(s)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''),
  dec: (s) => {
    const bin = atob(String(s).replace(/-/g, '+').replace(/_/g, '/'));
    return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  },
};

/** HMAC over the address, one key domain per purpose ('unsub' | 'sub'). */
async function recapSig(env, purpose, email) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(`ys-recap-${purpose}:` + (env.EMAIL_UNSUB_SECRET || '')),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(email));
  return [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function apiBase(env) {
  return String(env.API_PUBLIC_URL || 'https://yardscout-api.yardscout.workers.dev').replace(/\/+$/, '');
}
function appUrl(env) {
  return String(env.APP_URL || 'https://yardscout.io/').trim();
}

/** Signed one-click unsubscribe link for the Monday email (no login, no expiry). */
export async function recapUnsubUrl(env, email) {
  return `${apiBase(env)}/v1/recap/unsubscribe?e=${encodeURIComponent(b64u.enc(email))}&sig=${await recapSig(env, 'unsub', email)}`;
}

/** The token a confirmed browser keeps to add later watches in one tap. */
export async function recapSubToken(env, email) {
  return `${b64u.enc(email)}.${await recapSig(env, 'sub', email)}`;
}
async function emailFromSubToken(env, token) {
  const m = /^([A-Za-z0-9_-]{4,400})\.([0-9a-f]{64})$/.exec(String(token || ''));
  if (!m) return null;
  let email;
  try { email = b64u.dec(m[1]); } catch { return null; }
  return m[2] === await recapSig(env, 'sub', email) ? email : null;
}

/** Postal address line for commercial email. OWNER DECISION: empty by
 * default (wrangler.toml EMAIL_POSTAL_ADDRESS); never invented. */
export function postalLine(env) {
  return String(env.EMAIL_POSTAL_ADDRESS || '').replace(/[\r\n]+/g, ', ').trim().slice(0, 200);
}

const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** The watch as the browser holds it → the copy the server keeps. Free
 * criteria only (make, model, years, centre, radius): trim and drivetrain
 * filters are Pro and are not copied. The centre is rounded to ~1 km, as
 * the apps do. null when the watch cannot drive a "near you" recap. */
export function sanitizeRecapWatch(w) {
  if (!w || typeof w !== 'object') return null;
  const make = String(w.make || '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 40);
  if (!make) return null;
  const model = String(w.model || '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 60) || null;
  const yr = (v) => (Number.isFinite(+v) && +v >= 1900 && +v <= 2100 ? Math.floor(+v) : null);
  let yearMin = yr(w.yearMin ?? w.yrMin), yearMax = yr(w.yearMax ?? w.yrMax);
  if (yearMin && yearMax && yearMax < yearMin) yearMax = null;
  const lat = +w.lat, lng = +w.lng;
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
  const r = +w.radiusMi;
  if (!Number.isFinite(r) || r <= 0) return null;
  return {
    make, model, year_min: yearMin, year_max: yearMax,
    lat: Math.round(lat * 100) / 100, lng: Math.round(lng * 100) / 100,
    radius_mi: Math.min(Math.floor(r) || 1, RECAP_MAX_RADIUS),
  };
}

const sameWatch = (a, b) => String(a.make).toLowerCase() === String(b.make).toLowerCase()
  && String(a.model || '').toLowerCase() === String(b.model || '').toLowerCase()
  && (a.year_min || null) === (b.year_min || null) && (a.year_max || null) === (b.year_max || null)
  && Math.abs(a.lat - b.lat) < 0.005 && Math.abs(a.lng - b.lng) < 0.005 && a.radius_mi === b.radius_mi;

export function watchLabel(w) {
  const yrs = w.year_min || w.year_max ? `${w.year_min || ''}–${w.year_max || ''} ` : '';
  return `${yrs}${w.make}${w.model ? ' ' + w.model : ''}`.trim();
}

async function insertWatch(env, email, w, confirmedAt) {
  await env.DB.prepare(
    `INSERT INTO recap_watches (email, make, model, year_min, year_max, lat, lng, radius_mi, created_at, confirmed_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`
  ).bind(email, w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi, isoNow(), confirmedAt).run();
}

/* ===== confirmation email ===== */

export function buildConfirmEmail(env, email, watches, link) {
  const list = watches.map((w) => `• ${watchLabel(w)}, within ${w.radius_mi} mi`).join('\n');
  const postal = postalLine(env);
  const subject = 'Confirm your free YardScout Monday email';
  const text =
    `Tap to confirm, and every Monday we'll email ${email} the cars matching these watches that were set out at yards near you this week:\n\n` +
    `${list}\n\nConfirm: ${link}\n\n` +
    `Nothing is sent until you confirm. If you didn't ask for this, ignore this email: the address is deleted within 7 days.\n\n` +
    `YardScout · ${appUrl(env)}${postal ? `\n${postal}` : ''}\n`;
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout</p>
  <h2 style="margin:0 0 12px;font-size:19px;color:#fff;">Confirm your free Monday email</h2>
  <p style="color:#ccc;font-size:14px;line-height:1.5;margin:0 0 10px;">Every Monday we'll email ${esc(email)} the cars matching these watches that were set out at yards near you this week:</p>
  <ul style="color:#eee;font-size:14px;line-height:1.6;margin:0 0 16px;padding-left:18px;">${watches.map((w) => `<li>${esc(watchLabel(w))}, within ${esc(w.radius_mi)} mi</li>`).join('')}</ul>
  <a href="${esc(link)}" style="display:inline-block;background:#ff9500;color:#141414;font-weight:700;font-size:15px;text-decoration:none;padding:11px 18px;border-radius:8px;">Confirm my Monday email</a>
  <p style="color:#999;font-size:13px;line-height:1.6;margin:18px 0 0;">Nothing is sent until you confirm. If you didn't ask for this, ignore this email: the address is deleted within 7 days.</p>
  <p style="color:#666;font-size:11px;margin:22px 0 0;border-top:1px solid #2a2a2a;padding-top:12px;">YardScout · <a href="${esc(appUrl(env))}" style="color:#888;">yardscout.io</a>${postal ? `<br>${esc(postal)}` : ''}</p>
</div></body></html>`;
  return { subject, text, html };
}

async function sendConfirmEmail(env, email, watches, token) {
  const link = `${apiBase(env)}/v1/recap/confirm?t=${encodeURIComponent(token)}`;
  const { subject, text, html } = buildConfirmEmail(env, email, watches, link);
  if (!env.RESEND_API_KEY) {
    if (env.DEV_MODE === '1') {
      console.log(`DEV recap confirmation → ${maskEmail(email)} (${watches.length} watch${watches.length === 1 ? '' : 'es'})`);
      return { ok: true, devLink: link };
    }
    return { ok: false };
  }
  let r;
  try {
    r = await resendFetch(env, 'email:confirm', email, {
      method: 'POST',
      headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
      body: JSON.stringify({ from: env.EMAIL_FROM || 'YardScout <hello@yardscout.io>', to: [email], subject, text, html }),
    });
  } catch (e) {
    console.log('recap confirmation send error:', e && e.message);
    return { ok: false };
  }
  if (!r.ok) {
    console.log('recap confirmation failed:', r.status);
    return { ok: false };
  }
  console.log(`recap confirmation sent to ${maskEmail(email)}`);
  return { ok: true };
}

/* ===== POST /v1/recap/signup ===== */

export async function handleRecapSignup(req, env, ip) {
  if (!rateLimit('recap:ip:' + ip, IP_SIGNUPS_PER_HOUR, 3600_000)) {
    return err(429, 'rate_limited', 'Too many sign-ups from this network. Try again later.');
  }
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = String((body && body.email) || '').trim().toLowerCase();
  if (!EMAIL_RE.test(email) || email.length > 254) return err(400, 'bad_email', 'Enter a valid email address.');
  const watch = sanitizeRecapWatch(body.watch);
  if (!watch) return err(400, 'bad_watch', 'This watch needs a make and a zip code.');
  // Without the signing secret an unsubscribe link could be forged.
  if (!env.EMAIL_UNSUB_SECRET && env.DEV_MODE !== '1') {
    return err(503, 'not_configured', 'The Monday email is not set up yet.');
  }

  const nowMs = Date.now(), now = new Date(nowMs).toISOString();
  const sub = await env.DB.prepare('SELECT * FROM recap_subscribers WHERE email = ?1').bind(email).first();
  const existing = sub ? ((await env.DB.prepare(
    'SELECT make, model, year_min, year_max, lat, lng, radius_mi, confirmed_at FROM recap_watches WHERE email = ?1'
  ).bind(email).all()).results || []) : [];
  const dup = existing.find((w) => sameWatch(w, watch));
  // Same reply whether or not the address was already in: a sign-up must not
  // tell a stranger what someone else receives.
  const sentReply = () => json({ ok: true, state: 'confirm-sent' });
  if (dup && dup.confirmed_at) return sentReply();
  if (!dup && existing.length >= RECAP_MAX_WATCHES) {
    return err(409, 'limit', `This address already gets ${RECAP_MAX_WATCHES} watches in its Monday email.`);
  }

  // A link sent within the hour is still in the inbox and confirms every
  // pending watch for the address, this one included: no second email.
  const live = sub && sub.confirm_hash && sub.confirm_sent_at
    && nowMs - Date.parse(sub.confirm_sent_at) < CONFIRM_REUSE_MS
    && Date.parse(sub.confirm_expires_at || '') > nowMs;
  if (live) {
    if (!dup) await insertWatch(env, email, watch, null);
    return sentReply();
  }

  const windowOpen = sub && sub.confirm_window_at && nowMs - Date.parse(sub.confirm_window_at) < 86400_000;
  const sends = windowOpen ? (sub.confirm_sends || 0) : 0;
  if (sends >= CONFIRMS_PER_DAY) {
    return err(429, 'too_many', 'We already sent this address several confirmation emails today. Use one of those, or try again tomorrow.');
  }
  if (!(await optionalEmailAllowed(env, nowMs))) {
    await countHeld(env, 'email:confirm');
    console.log(`recap confirmation held (Resend daily cap) for ${maskEmail(email)}`);
    return err(503, 'daily_cap', "Our email sender has reached today's limit. Your watch is saved here; try the email again tomorrow.");
  }

  const token = randomToken('ys_recap');
  const hash = await sha256Hex(token);
  const expires = new Date(nowMs + CONFIRM_TTL_MS).toISOString();
  if (!sub) {
    await env.DB.prepare(
      `INSERT INTO recap_subscribers (email, created_at, confirm_hash, confirm_expires_at, confirm_sent_at, confirm_sends, confirm_window_at)
       VALUES (?1, ?2, ?3, ?4, ?2, 1, ?2)`
    ).bind(email, now, hash, expires).run();
  } else {
    await env.DB.prepare(
      `UPDATE recap_subscribers SET confirm_hash = ?2, confirm_expires_at = ?3, confirm_sent_at = ?4,
              confirm_sends = ?5, confirm_window_at = ?6 WHERE email = ?1`
    ).bind(email, hash, expires, now, sends + 1, windowOpen ? sub.confirm_window_at : now).run();
  }
  if (!dup) await insertWatch(env, email, watch, null);

  const pending = (await env.DB.prepare(
    'SELECT make, model, year_min, year_max, lat, lng, radius_mi FROM recap_watches WHERE email = ?1 AND confirmed_at IS NULL ORDER BY id'
  ).bind(email).all()).results || [];
  const sent = await sendConfirmEmail(env, email, pending.length ? pending : [watch], token);
  if (!sent.ok) {
    // Nothing kept for an address we could not write to.
    if (!sub) {
      await env.DB.batch([
        env.DB.prepare('DELETE FROM recap_watches WHERE email = ?1').bind(email),
        env.DB.prepare('DELETE FROM recap_subscribers WHERE email = ?1').bind(email),
      ]);
    } else if (!dup) {
      await env.DB.prepare(
        `DELETE FROM recap_watches WHERE id = (SELECT MAX(id) FROM recap_watches WHERE email = ?1 AND confirmed_at IS NULL)`
      ).bind(email).run();
    }
    return err(502, 'email_failed', 'We could not send the confirmation email. Try again in a minute.');
  }
  // DEV only (no Resend): hand the link back so local runs can confirm.
  if (sent.devLink && env.DEV_MODE === '1') return json({ ok: true, state: 'confirm-sent', dev_link: sent.devLink });
  return sentReply();
}

/* ===== POST /v1/recap/add {sub, watch} — a confirmed browser, one tap ===== */

export async function handleRecapAdd(req, env, ip) {
  if (!rateLimit('recap:ip:' + ip, IP_SIGNUPS_PER_HOUR * 4, 3600_000)) {
    return err(429, 'rate_limited', 'Slow down.');
  }
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = await emailFromSubToken(env, body && body.sub);
  if (!email) return err(401, 'bad_sub', 'Sign up for the Monday email again.');
  const watch = sanitizeRecapWatch(body.watch);
  if (!watch) return err(400, 'bad_watch', 'This watch needs a make and a zip code.');
  const sub = await env.DB.prepare('SELECT confirmed_at FROM recap_subscribers WHERE email = ?1').bind(email).first();
  if (!sub || !sub.confirmed_at) return err(404, 'not_subscribed', 'This address is no longer subscribed.');
  const existing = (await env.DB.prepare(
    'SELECT make, model, year_min, year_max, lat, lng, radius_mi, confirmed_at FROM recap_watches WHERE email = ?1'
  ).bind(email).all()).results || [];
  const dup = existing.find((w) => sameWatch(w, watch));
  if (dup) {
    if (!dup.confirmed_at) {
      await env.DB.prepare('UPDATE recap_watches SET confirmed_at = ?2 WHERE email = ?1 AND confirmed_at IS NULL')
        .bind(email, isoNow()).run();
    }
    return json({ ok: true, state: 'added', watches: existing.length });
  }
  if (existing.length >= RECAP_MAX_WATCHES) {
    return err(409, 'limit', `Your Monday email already covers ${RECAP_MAX_WATCHES} watches.`);
  }
  await insertWatch(env, email, watch, isoNow());
  return json({ ok: true, state: 'added', watches: existing.length + 1 });
}

/* ===== confirm (GET page with a button → POST) ===== */

function page(title, inner, status = 200) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} — YardScout</title></head>
<body style="font-family:system-ui,-apple-system,sans-serif;background:#141414;color:#eee;display:grid;place-items:center;min-height:90vh;margin:0;">
<div style="max-width:28rem;padding:2rem 1rem;text-align:center;">${inner}</div></body></html>`,
  { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'referrer-policy': 'no-referrer' } });
}
const badLink = () => page('Link expired', `<h2 style="margin:0 0 .5rem;">This link has expired</h2>
<p style="color:#aaa;line-height:1.6;">It was already used, or it is more than 7 days old. Set a watch at
<a href="https://yardscout.io/" style="color:#f90;">yardscout.io</a> and ask for the Monday email again.</p>`, 400);

async function subscriberForToken(env, token) {
  if (!/^ys_recap_[A-Za-z0-9_-]{20,}$/.test(String(token || '')) || token.length > 200) return null;
  const row = await env.DB.prepare(
    'SELECT email, confirmed_at, confirm_expires_at FROM recap_subscribers WHERE confirm_hash = ?1'
  ).bind(await sha256Hex(token)).first();
  if (!row || !(Date.parse(row.confirm_expires_at || '') > Date.now())) return null;
  return row;
}

export async function handleRecapConfirmPage(req, env, url) {
  const t = String(url.searchParams.get('t') || '');
  const row = await subscriberForToken(env, t);
  if (!row) return badLink();
  return page('Confirm your Monday email', `<h2 style="margin:0 0 .5rem;">Confirm your free Monday email</h2>
<p style="color:#aaa;line-height:1.6;">For ${esc(maskEmail(row.email))}. One email a week, unsubscribe in one click.</p>
<form method="post" action="/v1/recap/confirm" style="margin:1.2rem 0 0;">
<input type="hidden" name="t" value="${esc(t)}">
<button type="submit" style="font:inherit;font-weight:700;background:#ff9500;color:#141414;border:0;border-radius:8px;padding:.75rem 1.2rem;cursor:pointer;">Confirm my Monday email</button>
</form>`);
}

export async function handleRecapConfirm(req, env) {
  let t = '';
  try {
    const ct = req.headers.get('content-type') || '';
    if (ct.includes('application/json')) t = String((await req.json()).t || '');
    else t = String(new URLSearchParams(await req.text()).get('t') || '');
  } catch { t = ''; }
  const row = await subscriberForToken(env, t);
  if (!row) return badLink();
  const now = isoNow();
  // Single use: the conditional UPDATE loses a double-click race.
  const claim = await env.DB.prepare(
    `UPDATE recap_subscribers SET confirmed_at = COALESCE(confirmed_at, ?2), confirm_hash = NULL
      WHERE email = ?1 AND confirm_hash = ?3`
  ).bind(row.email, now, await sha256Hex(t)).run();
  if (!claim.meta || !claim.meta.changes) return badLink();
  const day = now.slice(0, 10);
  const stmts = [
    env.DB.prepare('UPDATE recap_watches SET confirmed_at = ?2 WHERE email = ?1 AND confirmed_at IS NULL').bind(row.email, now),
    // An account holder who had opted out and signs up again is back in.
    env.DB.prepare('DELETE FROM recap_optout WHERE email = ?1').bind(row.email),
  ];
  if (!row.confirmed_at) {
    // The funnel counter for "email confirmed": counted here, where it is
    // certain, as one anonymous +1 (same table and shape as /v1/events).
    stmts.push(env.DB.prepare(
      `INSERT INTO events_daily (day, event, source, campaign, medium, platform, n)
       VALUES (?1, 'email-confirmed', '', '', '', 'web', 1)
       ON CONFLICT(day, event, source, campaign, medium, platform) DO UPDATE SET n = n + 1`
    ).bind(day));
  }
  await env.DB.batch(stmts);
  console.log(`recap confirmed for ${maskEmail(row.email)}`);
  const to = `${appUrl(env).replace(/#.*$/, '')}#recap=confirmed&sub=${encodeURIComponent(await recapSubToken(env, row.email))}`;
  return new Response(null, { status: 303, headers: { location: to, 'cache-control': 'no-store' } });
}

/* ===== unsubscribe: deletes the address and everything copied for it ===== */

export async function deleteRecapAddress(env, email) {
  const isAccount = await env.DB.prepare('SELECT 1 AS x FROM users WHERE email = ?1').bind(email).first();
  const stmts = [
    env.DB.prepare('DELETE FROM recap_watches WHERE email = ?1').bind(email),
    env.DB.prepare('DELETE FROM recap_subscribers WHERE email = ?1').bind(email),
    env.DB.prepare('DELETE FROM recap_sent WHERE email = ?1').bind(email),
    env.DB.prepare('DELETE FROM sale_alerts_sent WHERE user_id = ?1').bind('recap:' + email),
  ];
  // A magic-link account's own recap stops too; the account is left alone.
  if (isAccount) {
    stmts.push(env.DB.prepare('INSERT OR REPLACE INTO recap_optout (email, at) VALUES (?1, ?2)').bind(email, isoNow()));
  }
  await env.DB.batch(stmts);
}

export async function handleRecapUnsubscribe(req, env, url) {
  let email;
  try { email = b64u.dec(url.searchParams.get('e') || ''); } catch { email = ''; }
  const sig = String(url.searchParams.get('sig') || '');
  if (!email || !/^[0-9a-f]{64}$/.test(sig) || sig !== await recapSig(env, 'unsub', email)) {
    return req.method === 'POST' ? err(400, 'bad_link', 'This unsubscribe link is invalid.')
      : page('Invalid link', '<h2 style="margin:0 0 .5rem;">This unsubscribe link is invalid</h2><p style="color:#aaa;">Email yardscout.io@gmail.com and we will remove you by hand.</p>', 400);
  }
  await deleteRecapAddress(env, email);
  console.log(`recap unsubscribe: ${maskEmail(email)} deleted`);
  if (req.method === 'POST') return json({ ok: true, unsubscribed: true });
  return page('Unsubscribed', `<h2 style="margin:0 0 .5rem;">You're unsubscribed</h2>
<p style="color:#aaa;line-height:1.6;">No more Monday emails to ${esc(maskEmail(email))}. We deleted the address and the
watches copied for it. The watches saved in your browser are unchanged at
<a href="https://yardscout.io/" style="color:#f90;">yardscout.io</a>.</p>`);
}

/* ===== readers for the Monday job and the ops email ===== */

/** Confirmed addresses → their confirmed watch copies (watchMatches shape). */
export async function loadRecapAudience(env) {
  const rows = (await env.DB.prepare(
    `SELECT w.email, w.make, w.model, w.year_min, w.year_max, w.lat, w.lng, w.radius_mi
       FROM recap_watches w JOIN recap_subscribers s ON s.email = w.email
      WHERE s.confirmed_at IS NOT NULL AND w.confirmed_at IS NOT NULL ORDER BY w.email, w.id`
  ).all()).results || [];
  const by = new Map();
  for (const r of rows) {
    if (!by.has(r.email)) by.set(r.email, []);
    by.get(r.email).push({ make: r.make, model: r.model, year_min: r.year_min, year_max: r.year_max,
      lat: r.lat, lng: r.lng, radius_mi: r.radius_mi });
  }
  return by;
}

export async function loadRecapOptouts(env) {
  const rows = (await env.DB.prepare('SELECT email FROM recap_optout').all()).results || [];
  return new Set(rows.map((r) => r.email));
}

/** Hourly: unconfirmed addresses and watches go after 7 days; recap dedupe
 * rows after 90. */
export async function pruneRecap(env, now = Date.now()) {
  const cut = new Date(now - CONFIRM_TTL_MS).toISOString();
  await env.DB.batch([
    env.DB.prepare(
      `DELETE FROM recap_watches WHERE confirmed_at IS NULL AND created_at < ?1`
    ).bind(cut),
    env.DB.prepare(
      `DELETE FROM recap_watches WHERE email IN
         (SELECT email FROM recap_subscribers WHERE confirmed_at IS NULL AND created_at < ?1)`
    ).bind(cut),
    env.DB.prepare('DELETE FROM recap_subscribers WHERE confirmed_at IS NULL AND created_at < ?1').bind(cut),
    env.DB.prepare('DELETE FROM recap_sent WHERE sent_at < ?1').bind(new Date(now - 90 * 86400_000).toISOString()),
  ]);
}

/** Aggregate counts for the daily ops email. No addresses. */
export async function recapStats(env) {
  const r = await env.DB.prepare(
    `SELECT
       (SELECT COUNT(*) FROM recap_subscribers WHERE confirmed_at IS NOT NULL) AS confirmed,
       (SELECT COUNT(*) FROM recap_subscribers WHERE confirmed_at IS NULL) AS pending,
       (SELECT COUNT(*) FROM recap_watches w JOIN recap_subscribers s ON s.email = w.email
         WHERE s.confirmed_at IS NOT NULL AND w.confirmed_at IS NOT NULL) AS watches`
  ).first();
  return { confirmed: (r && r.confirmed) || 0, pending: (r && r.pending) || 0, watches: (r && r.watches) || 0 };
}

/* ===== Monday recap held at the cap → retried the next day =====
 * sendWeeklyDigests reports how many recaps it held back. The flag below
 * makes the hourly cron re-run it on a later UTC day (dedupe makes the
 * re-run send only what was held), for up to 5 days. */
const RETRY_KEY = 'recap:retry';
export async function noteRecapHeld(env, held, now = Date.now()) {
  if (!env.ENTITLEMENTS) return;
  try {
    if (held > 0) {
      const prev = JSON.parse(await env.ENTITLEMENTS.get(RETRY_KEY) || 'null');
      await env.ENTITLEMENTS.put(RETRY_KEY, JSON.stringify({
        day: new Date(now).toISOString().slice(0, 10), held,
        since: (prev && prev.since) || new Date(now).toISOString(),
      }));
    } else {
      await env.ENTITLEMENTS.delete(RETRY_KEY);
    }
  } catch (e) { console.log('recap retry flag failed:', e && e.message); }
}
export async function recapRetryDue(env, now = Date.now()) {
  if (!env.ENTITLEMENTS) return false;
  try {
    const f = JSON.parse(await env.ENTITLEMENTS.get(RETRY_KEY) || 'null');
    if (!f) return false;
    if (now - Date.parse(f.since) > 5 * 86400_000) { await env.ENTITLEMENTS.delete(RETRY_KEY); return false; }
    return f.day < new Date(now).toISOString().slice(0, 10);
  } catch { return false; }
}
