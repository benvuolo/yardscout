/* Free emailed alert for web visitors (2026-11-17, owner: "do the free
 * emailed alert").
 *
 * The apps give a free install ONE instant push watch within 50 mi
 * (devices.js, since 1.13.0). On the website emailed alerts were Pro only
 * (email_alerts.js). This module is the website's free counterpart:
 *
 *   ONE watch per email address, cars set out within FREE_ALERT_RADIUS_MI of
 *   its centre (the same 50 mi, the same constant, as the free instant
 *   push), no account. Pro stays: every watch, any distance.
 *
 *   POST /v1/free-alert/signup {email, watch, sub?}  ask for the alert. The
 *        address + a COPY of the watch's free criteria are stored as
 *        PENDING and ONE confirmation email goes out. With `sub` (the signed
 *        token a browser holds after a confirmation click, for the same
 *        address) the watch is set at once and no email is sent: this is how
 *        the page changes the car.
 *   GET  /v1/free-alert/confirm?t=   page with a "Confirm" button (a mail
 *        scanner that fetches links must not opt anyone in)
 *   POST /v1/free-alert/confirm  t=  double opt-in: the pending watch
 *        becomes THE watch for the address (replacing any other)
 *        → 303 to the app (#falert=confirmed&sub=)
 *   POST /v1/free-alert/status {sub} what the server holds for the address
 *   POST /v1/free-alert/off {sub}    turn it off: deletes the address
 *   GET|POST /v1/free-alert/unsubscribe?e=&sig=  one click from any alert
 *        email: DELETES the address, its watch and its dedupe rows
 *        (POST = RFC 8058)
 *
 * It reuses the Monday email's machinery (recap_signup.js): the same
 * confirmation-token scheme, link lifetime and reuse window, per-address and
 * per-IP limits (sign-ups share the Monday email's per-IP sign-up bucket; a
 * car change has its own, IP_ADDS_PER_HOUR), the same signed browser token
 * (so an address confirmed for the Monday email in this browser needs no
 * second confirmation email), masked addresses in logs, a reply that never
 * says whether an address was already in.
 *
 * Sending (dispatchFreeEmailAlerts, called from admin.js handleCommit AFTER
 * the Pro email dispatch of the same commit): at most ONE email per address
 * per scan, deduped per (address, car) in free_email_alerts_sent. Copy says
 * "same day", never "instant": scans run about every 4 hours.
 *
 * Email budget: this is the LOWEST class of mail (ops.js freeAlertBudget).
 * A matched alert the budget cannot carry is held: counted
 * (email:free-alert:held, shown in the daily ops email), not marked sent,
 * and retried on later scans for FREE_ALERT_CATCHUP_MS; after that the car
 * is not emailed. The page and the emails say so.
 *
 * Rule 6: the browser's watches are never read back or changed. Privacy: no
 * IP is stored; logs carry masked addresses only.
 */

import { json, err, sha256Hex, randomToken, isoNow, rateLimit } from './util.js';
import { resendFetch, countHeld, optionalEmailAllowed, freeAlertBudget, FREE_ALERT_CHANNEL } from './ops.js';
import { clipAttribution } from './attribution.js';
import { hasRoom } from './commit_budget.js';
import { watchMatches, loadArrivals } from './alerts.js';
import { FREE_INSTANT_RADIUS_MI } from './devices.js';
import { entActive } from './email_alerts.js';
import {
  sanitizeRecapWatch, watchLabel, maskEmail, postalLine, recapSig, recapSubToken, emailFromSubToken,
  b64u, apiBase, appUrl, esc, page, EMAIL_RE,
  CONFIRM_TTL_MS, CONFIRM_REUSE_MS, CONFIRMS_PER_DAY, IP_SIGNUPS_PER_HOUR, IP_ADDS_PER_HOUR,
} from './recap_signup.js';

/** The free tier's distance: the free instant push's own constant. */
export const FREE_ALERT_RADIUS_MI = FREE_INSTANT_RADIUS_MI;
/** At most this many free alert emails per scan commit (the commit's other
 * dispatchers share one small subrequest budget). */
export const FREE_ALERT_MAX_PER_SCAN = 5;
/** A held alert's cars are retried on later scans for this long. */
export const FREE_ALERT_CATCHUP_MS = 48 * 3600_000;
const MAX_VEHICLES_PER_EMAIL = 10;
const SENT_ROWS_PER_STMT = 30;          // 3 binds a row; D1 caps a statement at 100
const EMAILS_PER_IN = 90;               // addresses per IN (...) list
/** Server-counted funnel events (events_daily; a client may not post them). */
export const FREE_ALERT_CONFIRMED_EVENT = 'free-alert-confirmed';
export const FREE_ALERT_FIRST_EMAIL_EVENT = 'free-alert-first-email';

/* ===== the watch ===== */

/** The watch as the browser holds it → the one copy the server keeps: free
 * criteria only (recap_signup.js sanitizeRecapWatch: make, model, years, the
 * centre rounded to ~1 km), radius clamped to the free alert's 50 mi. */
export function sanitizeFreeAlertWatch(w) {
  const s = sanitizeRecapWatch(w);
  if (!s) return null;
  return { ...s, radius_mi: Math.min(s.radius_mi, FREE_ALERT_RADIUS_MI) };
}

function parseWatch(text) {
  if (!text) return null;
  try {
    const w = JSON.parse(text);
    if (!w || !w.make || w.lat == null || w.lng == null || !w.radius_mi) return null;
    // Re-clamp on read: the stored row is trusted, but the rule is the rule.
    return { ...w, radius_mi: Math.min(w.radius_mi, FREE_ALERT_RADIUS_MI) };
  } catch { return null; }
}

/** A cheap test that is true for every car within the watch's radius (and a
 * few just outside): a latitude/longitude box. A scan can carry thousands of
 * cars nationwide; the exact rule (alerts.js watchMatches) then runs only on
 * the few near this watch. It never decides a match by itself. */
export function nearBox(w) {
  const dLat = w.radius_mi / 68;                      // a degree of latitude is 68.7 to 69.4 mi
  const edge = Math.min(89.9, Math.abs(w.lat) + dLat);  // meridians are closest at the poleward edge
  const dLng = w.radius_mi / (68 * Math.cos((edge * Math.PI) / 180));
  return (v) => {
    if (v.lat == null || v.lng == null) return false;
    if (Math.abs(v.lat - w.lat) > dLat) return false;
    let d = Math.abs(v.lng - w.lng);
    if (d > 180) d = 360 - d;
    return d <= dLng;
  };
}
/** The cars a free alert watch covers: watchMatches, behind the box. */
const matchesOf = (watch, cars) => { const near = nearBox(watch); return cars.filter((v) => near(v) && watchMatches(watch, v)); };

/** What the page may know about the stored watch (never the centre). */
const publicWatch = (w) => ({ make: w.make, model: w.model || '', yearMin: w.year_min || null, yearMax: w.year_max || null, radiusMi: w.radius_mi });

const shortLabel = (w) => `${w.make}${w.model ? ' ' + w.model : ''}`;

export async function freeAlertUnsubUrl(env, email) {
  return `${apiBase(env)}/v1/free-alert/unsubscribe?e=${encodeURIComponent(b64u.enc(email))}&sig=${await recapSig(env, 'alert-unsub', email)}`;
}

const bumpEvent = (env, event, a, day) => env.DB.prepare(
  `INSERT INTO events_daily (day, event, source, campaign, medium, platform, n)
   VALUES (?1, ?2, ?3, ?4, ?5, 'web', 1)
   ON CONFLICT(day, event, source, campaign, medium, platform) DO UPDATE SET n = n + 1`
).bind(day, event, (a && a.source) || '', (a && a.campaign) || '', (a && a.medium) || '');

/** Alerts are for FUTURE arrivals (the same contract as Pro email alerts and
 * devices): the dedupe log starts over with every car that already matches. */
async function seedSent(env, email, watch, now) {
  const existing = await loadArrivals(env);
  const ids = matchesOf(watch, existing).map((v) => String(v.id));
  const stmts = [env.DB.prepare('DELETE FROM free_email_alerts_sent WHERE email = ?1').bind(email)];
  for (let i = 0; i < ids.length; i += SENT_ROWS_PER_STMT) {
    const chunk = ids.slice(i, i + SENT_ROWS_PER_STMT);
    stmts.push(env.DB.prepare(
      `INSERT OR IGNORE INTO free_email_alerts_sent (email, vehicle_id, sent_at) VALUES ${chunk.map(() => '(?, ?, ?)').join(', ')}`
    ).bind(...chunk.flatMap((id) => [email, id, now])));
  }
  await env.DB.batch(stmts);
  return ids.length;
}

/* ===== confirmation email ===== */

export function buildFreeAlertConfirmEmail(env, email, watch, link, { replaces = null } = {}) {
  const label = watchLabel(watch);
  const postal = postalLine(env);
  const subject = 'Confirm your free YardScout email alert';
  const what = `when a ${label} is set out at a yard within ${watch.radius_mi} mi`;
  const repl = replaces ? `This replaces your current alert (${watchLabel(replaces)}): the free alert covers one car.` : '';
  const how = 'One car, one address, no account. Scans run about every 4 hours, so an alert usually reaches you the same day a car is listed. '
    + 'Free emails share a small daily sending limit, so one can arrive late or be skipped.';
  const ignore = replaces
    ? "Nothing changes until you confirm. If you didn't ask for this, ignore this email."
    : "Nothing is sent until you confirm. If you didn't ask for this, ignore this email: the address is deleted within 7 days.";
  const text =
    `Tap to confirm, and we'll email ${email} ${what}.\n\n` +
    `Confirm: ${link}\n\n` +
    (repl ? `${repl}\n\n` : '') +
    `${how}\n\n${ignore}\n\n` +
    `YardScout · ${appUrl(env)}${postal ? `\n${postal}` : ''}\n`;
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout</p>
  <h2 style="margin:0 0 12px;font-size:19px;color:#fff;">Confirm your free email alert</h2>
  <p style="color:#ccc;font-size:14px;line-height:1.5;margin:0 0 16px;">We'll email ${esc(email)} when a <strong style="color:#fff;">${esc(label)}</strong> is set out at a yard within ${esc(watch.radius_mi)} mi.</p>
  <a href="${esc(link)}" style="display:inline-block;background:#2BB3CC;color:#141414;font-weight:700;font-size:15px;text-decoration:none;padding:11px 18px;border-radius:8px;">Confirm my email alert</a>
  ${repl ? `<p style="color:#ccc;font-size:13px;line-height:1.6;margin:18px 0 0;">${esc(repl)}</p>` : ''}
  <p style="color:#999;font-size:13px;line-height:1.6;margin:18px 0 0;">${esc(how)}</p>
  <p style="color:#999;font-size:13px;line-height:1.6;margin:10px 0 0;">${esc(ignore)}</p>
  <p style="color:#666;font-size:11px;margin:22px 0 0;border-top:1px solid #2a2a2a;padding-top:12px;">YardScout · <a href="${esc(appUrl(env))}" style="color:#888;">yardscout.io</a>${postal ? `<br>${esc(postal)}` : ''}</p>
</div></body></html>`;
  return { subject, text, html };
}

async function sendConfirmEmail(env, email, watch, token, replaces) {
  const link = `${apiBase(env)}/v1/free-alert/confirm?t=${encodeURIComponent(token)}`;
  const { subject, text, html } = buildFreeAlertConfirmEmail(env, email, watch, link, { replaces });
  if (!env.RESEND_API_KEY) {
    if (env.DEV_MODE === '1') {
      console.log(`DEV free alert confirmation → ${maskEmail(email)} (${shortLabel(watch)})`);
      return { ok: true, devLink: link };
    }
    return { ok: false };
  }
  let r;
  try {
    // Same class as the Monday email's confirmation: optional mail.
    r = await resendFetch(env, 'email:confirm', email, {
      method: 'POST',
      headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
      body: JSON.stringify({ from: env.EMAIL_FROM || 'YardScout <hello@yardscout.io>', to: [email], subject, text, html }),
    });
  } catch (e) {
    console.log('free alert confirmation send error:', e && e.message);
    return { ok: false };
  }
  if (!r.ok) {
    console.log('free alert confirmation failed:', r.status);
    return { ok: false };
  }
  console.log(`free alert confirmation sent to ${maskEmail(email)}`);
  return { ok: true };
}

/* ===== POST /v1/free-alert/signup ===== */

export async function handleFreeAlertSignup(req, env, ip) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = String((body && body.email) || '').trim().toLowerCase();
  // A browser that already confirmed this address (signed token) is changing
  // its car, not signing up: its own, wider bucket (as wide as the Monday
  // email's "add"). A sign-up shares the Monday email's per-IP sign-up bucket.
  const proved = !!(body && body.sub) && EMAIL_RE.test(email) && (await emailFromSubToken(env, body.sub)) === email;
  const allowed = proved
    ? rateLimit('falert:chg:ip:' + ip, IP_ADDS_PER_HOUR, 3600_000)
    : rateLimit('recap:ip:' + ip, IP_SIGNUPS_PER_HOUR, 3600_000);
  if (!allowed) return err(429, 'rate_limited', 'Too many sign-ups from this network. Try again later.');
  if (!EMAIL_RE.test(email) || email.length > 254) return err(400, 'bad_email', 'Enter a valid email address.');
  const watch = sanitizeFreeAlertWatch(body.watch);
  if (!watch) return err(400, 'bad_watch', 'This watch needs a make and a zip code.');
  // Without the signing secret an unsubscribe link could be forged.
  if (!env.EMAIL_UNSUB_SECRET && env.DEV_MODE !== '1') {
    return err(503, 'not_configured', 'The email alert is not set up yet.');
  }

  const nowMs = Date.now(), now = new Date(nowMs).toISOString();
  const row = await env.DB.prepare('SELECT * FROM free_email_alerts WHERE email = ?1').bind(email).first();

  if (proved) {
    // The inbox is known to be theirs: this alert's own confirmation, or the
    // Monday email's, was clicked and this browser holds the token for it.
    const known = (row && row.confirmed_at)
      || !!(await env.DB.prepare('SELECT 1 AS x FROM recap_subscribers WHERE email = ?1 AND confirmed_at IS NOT NULL').bind(email).first());
    if (known) {
      const first = !(row && row.confirmed_at);
      const stmts = [env.DB.prepare(
        `INSERT INTO free_email_alerts (email, created_at, confirmed_at, watch_json, watch_set_at)
         VALUES (?1, ?2, ?2, ?3, ?2)
         ON CONFLICT (email) DO UPDATE SET confirmed_at = COALESCE(confirmed_at, ?2), watch_json = ?3, watch_set_at = ?2,
           pending_json = NULL, confirm_hash = NULL, pending_source = NULL, pending_campaign = NULL, pending_medium = NULL,
           held_at = NULL`
      ).bind(email, now, JSON.stringify(watch))];
      // Counted where it is certain, under the link this visit came from.
      if (first) stmts.push(bumpEvent(env, FREE_ALERT_CONFIRMED_EVENT, clipAttribution(body), now.slice(0, 10)));
      await env.DB.batch(stmts);
      await seedSent(env, email, watch, now);
      console.log(`free alert set for ${maskEmail(email)} (token, no email)`);
      return json({ ok: true, state: 'on', sub: await recapSubToken(env, email), watch: publicWatch(watch) });
    }
    // A token for an address that has since been removed proves nothing now:
    // it goes through the confirmation email like anyone else.
  }

  // Same reply whether or not the address already has an alert: a sign-up
  // must not tell a stranger what someone else receives.
  const sentReply = () => json({ ok: true, state: 'confirm-sent' });
  const pendingJson = JSON.stringify(watch);

  // A link sent within the hour is still in the inbox and confirms whatever
  // is pending for the address: the newest choice rides it, no second email.
  const live = row && row.confirm_hash && row.confirm_sent_at
    && nowMs - Date.parse(row.confirm_sent_at) < CONFIRM_REUSE_MS
    && Date.parse(row.confirm_expires_at || '') > nowMs;
  if (live) {
    await env.DB.prepare('UPDATE free_email_alerts SET pending_json = ?2 WHERE email = ?1').bind(email, pendingJson).run();
    return sentReply();
  }

  const windowOpen = row && row.confirm_window_at && nowMs - Date.parse(row.confirm_window_at) < 86400_000;
  const sends = windowOpen ? (row.confirm_sends || 0) : 0;
  if (sends >= CONFIRMS_PER_DAY) {
    return err(429, 'too_many', 'We already sent this address several confirmation emails today. Use one of those, or try again tomorrow.');
  }
  if (!(await optionalEmailAllowed(env, nowMs))) {
    await countHeld(env, 'email:confirm');
    console.log(`free alert confirmation held (Resend daily cap) for ${maskEmail(email)}`);
    return err(503, 'daily_cap', "Our email sender has reached today's limit. Your watch is saved here; try the email again tomorrow.");
  }

  const token = randomToken('ys_falert');
  const hash = await sha256Hex(token);
  const expires = new Date(nowMs + CONFIRM_TTL_MS).toISOString();
  // The link source rides with the confirmation link only while the address
  // is not confirmed yet (it is counted once, at the first click).
  const a = row && row.confirmed_at ? { source: null, campaign: null, medium: null } : clipAttribution(body);
  if (!row) {
    await env.DB.prepare(
      `INSERT INTO free_email_alerts (email, created_at, pending_json, confirm_hash, confirm_expires_at, confirm_sent_at,
                                      confirm_sends, confirm_window_at, pending_source, pending_campaign, pending_medium)
       VALUES (?1, ?2, ?3, ?4, ?5, ?2, 1, ?2, ?6, ?7, ?8)`
    ).bind(email, now, pendingJson, hash, expires, a.source, a.campaign, a.medium).run();
  } else {
    // An address still waiting for its first click asked again: its 7 days
    // (pruneFreeAlerts) start over with this link.
    await env.DB.prepare(
      `UPDATE free_email_alerts SET pending_json = ?2, confirm_hash = ?3, confirm_expires_at = ?4, confirm_sent_at = ?5,
              confirm_sends = ?6, confirm_window_at = ?7,
              pending_source = ?8, pending_campaign = ?9, pending_medium = ?10,
              created_at = CASE WHEN confirmed_at IS NULL THEN ?5 ELSE created_at END WHERE email = ?1`
    ).bind(email, pendingJson, hash, expires, now, sends + 1, windowOpen ? row.confirm_window_at : now, a.source, a.campaign, a.medium).run();
  }

  const replaces = row && row.confirmed_at ? parseWatch(row.watch_json) : null;
  const sent = await sendConfirmEmail(env, email, watch, token, replaces);
  if (!sent.ok) {
    // Nothing kept for an address we could not write to; a confirmed
    // address keeps its alert and only loses the change that was asked for.
    if (!row) await env.DB.prepare('DELETE FROM free_email_alerts WHERE email = ?1').bind(email).run();
    else {
      await env.DB.prepare(
        `UPDATE free_email_alerts SET pending_json = NULL, confirm_hash = NULL,
                pending_source = NULL, pending_campaign = NULL, pending_medium = NULL WHERE email = ?1`
      ).bind(email).run();
    }
    return err(502, 'email_failed', 'We could not send the confirmation email. Try again in a minute.');
  }
  // DEV only (no Resend): hand the link back so local runs can confirm.
  if (sent.devLink && env.DEV_MODE === '1') return json({ ok: true, state: 'confirm-sent', dev_link: sent.devLink });
  return sentReply();
}

/* ===== confirm (GET page with a button → POST) ===== */

const badLink = () => page('Link expired', `<h2 style="margin:0 0 .5rem;">This link has expired</h2>
<p style="color:#aaa;line-height:1.6;">It was already used, or it is more than 7 days old. Open the Alerts tab at
<a href="https://yardscout.io/#tab=alerts" style="color:#2BB3CC;">yardscout.io</a> and ask for the email alert again.</p>`, 400);

async function rowForToken(env, token) {
  if (!/^ys_falert_[A-Za-z0-9_-]{20,}$/.test(String(token || '')) || token.length > 200) return null;
  const row = await env.DB.prepare(
    `SELECT email, confirmed_at, confirm_expires_at, watch_json, pending_json, pending_source, pending_campaign, pending_medium
       FROM free_email_alerts WHERE confirm_hash = ?1`
  ).bind(await sha256Hex(token)).first();
  if (!row || !(Date.parse(row.confirm_expires_at || '') > Date.now())) return null;
  return parseWatch(row.pending_json) ? row : null;
}

export async function handleFreeAlertConfirmPage(req, env, url) {
  const t = String(url.searchParams.get('t') || '');
  const row = await rowForToken(env, t);
  if (!row) return badLink();
  const w = parseWatch(row.pending_json);
  const old = row.confirmed_at ? parseWatch(row.watch_json) : null;
  return page('Confirm your email alert', `<h2 style="margin:0 0 .5rem;">Confirm your free email alert</h2>
<p style="color:#ddd;line-height:1.6;margin:0 0 .4rem;"><strong>${esc(watchLabel(w))}</strong>, set out within ${esc(w.radius_mi)} mi</p>
<p style="color:#aaa;line-height:1.6;">For ${esc(maskEmail(row.email))}. At most one email per scan, usually the same day a car is listed; unsubscribe in one click.${old ? ` This replaces your alert for ${esc(watchLabel(old))}.` : ''}</p>
<form method="post" action="/v1/free-alert/confirm" style="margin:1.2rem 0 0;">
<input type="hidden" name="t" value="${esc(t)}">
<button type="submit" style="font:inherit;font-weight:700;background:#2BB3CC;color:#141414;border:0;border-radius:8px;padding:.75rem 1.2rem;cursor:pointer;">Confirm my email alert</button>
</form>`);
}

export async function handleFreeAlertConfirm(req, env) {
  let t = '';
  try {
    const ct = req.headers.get('content-type') || '';
    if (ct.includes('application/json')) t = String((await req.json()).t || '');
    else t = String(new URLSearchParams(await req.text()).get('t') || '');
  } catch { t = ''; }
  const row = await rowForToken(env, t);
  if (!row) return badLink();
  const watch = parseWatch(row.pending_json);
  const now = isoNow();
  // Single use: the conditional UPDATE loses a double-click race. The pending
  // watch becomes THE watch for the address (one per address: it replaces).
  const claim = await env.DB.prepare(
    `UPDATE free_email_alerts SET confirmed_at = COALESCE(confirmed_at, ?2), watch_json = pending_json, watch_set_at = ?2,
            pending_json = NULL, confirm_hash = NULL, held_at = NULL,
            pending_source = NULL, pending_campaign = NULL, pending_medium = NULL
      WHERE email = ?1 AND confirm_hash = ?3 AND pending_json IS NOT NULL`
  ).bind(row.email, now, await sha256Hex(t)).run();
  if (!claim.meta || !claim.meta.changes) return badLink();
  if (!row.confirmed_at) {
    // "Confirmed", counted where it is certain: one anonymous +1 under the
    // link the sign-up came from (read above, cleared by the claim).
    await bumpEvent(env, FREE_ALERT_CONFIRMED_EVENT,
      { source: row.pending_source, campaign: row.pending_campaign, medium: row.pending_medium }, now.slice(0, 10)).run();
  }
  await seedSent(env, row.email, watch, now);
  console.log(`free alert confirmed for ${maskEmail(row.email)}`);
  const to = `${appUrl(env).replace(/#.*$/, '')}#falert=confirmed&sub=${encodeURIComponent(await recapSubToken(env, row.email))}`;
  return new Response(null, { status: 303, headers: { location: to, 'cache-control': 'no-store' } });
}

/* ===== status / off (the browser that holds the signed token) ===== */

async function emailFromBody(req, env) {
  let body;
  try { body = await req.json(); } catch { return { error: err(400, 'bad_json', 'Body must be JSON.') }; }
  const email = await emailFromSubToken(env, body && body.sub);
  if (!email) return { error: err(401, 'bad_sub', 'Ask for the email alert again.') };
  return { email };
}

/** POST /v1/free-alert/status {sub} → {state: 'on', watch} | {state: 'off'}.
 * The page checks it so an unsubscribe done from an email shows up there. */
export async function handleFreeAlertStatus(req, env) {
  const { email, error } = await emailFromBody(req, env);
  if (error) return error;
  const row = await env.DB.prepare('SELECT confirmed_at, watch_json FROM free_email_alerts WHERE email = ?1').bind(email).first();
  const w = row && row.confirmed_at ? parseWatch(row.watch_json) : null;
  return json(w ? { ok: true, state: 'on', watch: publicWatch(w) } : { ok: true, state: 'off' });
}

export async function deleteFreeAlertAddress(env, email) {
  await env.DB.batch([
    env.DB.prepare('DELETE FROM free_email_alerts_sent WHERE email = ?1').bind(email),
    env.DB.prepare('DELETE FROM free_email_alerts WHERE email = ?1').bind(email),
  ]);
}

/** POST /v1/free-alert/off {sub} — the page's "Turn off": deletes the address. */
export async function handleFreeAlertOff(req, env) {
  const { email, error } = await emailFromBody(req, env);
  if (error) return error;
  await deleteFreeAlertAddress(env, email);
  console.log(`free alert off: ${maskEmail(email)} deleted`);
  return json({ ok: true, state: 'off' });
}

/* ===== unsubscribe: deletes the address and everything copied for it ===== */

export async function handleFreeAlertUnsubscribe(req, env, url) {
  let email;
  try { email = b64u.dec(url.searchParams.get('e') || ''); } catch { email = ''; }
  const sig = String(url.searchParams.get('sig') || '');
  if (!email || !/^[0-9a-f]{64}$/.test(sig) || sig !== await recapSig(env, 'alert-unsub', email)) {
    return req.method === 'POST' ? err(400, 'bad_link', 'This unsubscribe link is invalid.')
      : page('Invalid link', '<h2 style="margin:0 0 .5rem;">This unsubscribe link is invalid</h2><p style="color:#aaa;">Email yardscout.io@gmail.com and we will remove you by hand.</p>', 400);
  }
  await deleteFreeAlertAddress(env, email);
  console.log(`free alert unsubscribe: ${maskEmail(email)} deleted`);
  if (req.method === 'POST') return json({ ok: true, unsubscribed: true });
  return page('Unsubscribed', `<h2 style="margin:0 0 .5rem;">You're unsubscribed</h2>
<p style="color:#aaa;line-height:1.6;">No more alert emails to ${esc(maskEmail(email))}. We deleted the address and the
watch copied for it. The watches saved in your browser are unchanged at
<a href="https://yardscout.io/" style="color:#2BB3CC;">yardscout.io</a>. If you also get the free Monday email, that one has
its own unsubscribe link.</p>`);
}

/* ===== the alert email ===== */

const fmtCar = (v) => `${v.year || ''} ${v.make || ''} ${v.model || ''}`.replace(/\s+/g, ' ').trim();
const carUrl = (env, v) => `${appUrl(env).replace(/#.*$/, '').replace(/\/+$/, '')}/#car=${encodeURIComponent(String(v.id))}`;

/** Pure: subject, text, html for one alert email. */
export function buildFreeAlertEmail(env, email, watch, cars, unsubUrl) {
  const n = cars.length;
  const shown = cars.slice(0, MAX_VEHICLES_PER_EMAIL);
  const more = n - shown.length;
  const r = watch.radius_mi;
  const label = watchLabel(watch);
  const app = appUrl(env).replace(/#.*$/, '').replace(/\/+$/, '');
  const alertsUrl = `${app}/#tab=alerts`;
  const postal = postalLine(env);
  const subject = n === 1
    ? `New: ${fmtCar(cars[0])} at ${cars[0].location || 'a yard near you'}`
    : `${n} new: ${shortLabel(watch)} within ${r} mi`;
  const lead = `${n === 1 ? 'A car' : `${n} cars`} matching your free YardScout alert (${label}, within ${r} mi) `
    + `${n === 1 ? 'was' : 'were'} found by a recent inventory scan:`;
  const cadence = 'Scans run about every 4 hours, so this usually reaches you the same day a car is listed. '
    + 'Yards crush cars within weeks: fresh arrivals are your best odds.';
  const pro = `This free alert covers one car within ${FREE_ALERT_RADIUS_MI} mi. Pro alerts you on every watch, at any distance.`;
  const why = `You get this because you asked for a free email alert at yardscout.io and confirmed ${email}.`;
  const lines = shown.map((v) =>
    `• ${fmtCar(v)} — ${v.location || 'unknown yard'}${v.row ? ` (Row ${v.row})` : ''}${v.dateAdded ? `, listed ${v.dateAdded}` : ''}\n  ${carUrl(env, v)}`);
  if (more > 0) lines.push(`…and ${more} more on the site.`);
  const text =
    `${lead}\n\n${lines.join('\n\n')}\n\n${cadence}\n\n` +
    `${pro} See Pro: ${alertsUrl}\n\n--\n${why}\n` +
    `Change the car in the Alerts tab: ${alertsUrl}\n` +
    `Unsubscribe in one click (deletes your address and the watch copied for it): ${unsubUrl}\n` +
    (postal ? `${postal}\n` : '');
  const rows = shown.map((v) => `
    <tr><td style="padding:10px 0;border-bottom:1px solid #2a2a2a;">
      <a href="${esc(carUrl(env, v))}" style="color:#2BB3CC;font-weight:600;text-decoration:none;font-size:15px;">${esc(fmtCar(v))}</a><br>
      <span style="color:#999;font-size:13px;">${esc(v.location || 'unknown yard')}${v.row ? ` &middot; Row ${esc(v.row)}` : ''}${v.dateAdded ? ` &middot; listed ${esc(v.dateAdded)}` : ''}</span>
    </td></tr>`).join('');
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#141414;color:#eee;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:540px;margin:0 auto;padding:24px 16px;">
  <p style="color:#bbb;font-size:14px;margin:0 0 4px;">YardScout free alert</p>
  <h2 style="margin:0 0 6px;font-size:19px;color:#fff;">${esc(n === 1 ? `A ${shortLabel(watch)} was set out near you` : `${n} new ${shortLabel(watch)} near you`)}</h2>
  <p style="color:#999;font-size:13px;margin:0 0 8px;">${esc(label)}, within ${esc(r)} mi</p>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table>
  ${more > 0 ? `<p style="color:#999;font-size:13px;">…and ${more} more on the site.</p>` : ''}
  <p style="color:#999;font-size:13px;line-height:1.6;margin:16px 0 0;">${esc(cadence)}</p>
  <p style="color:#bbb;font-size:13px;line-height:1.6;margin:12px 0 0;">${esc(pro)} <a href="${esc(alertsUrl)}" style="color:#2BB3CC;">See Pro</a></p>
  <p style="color:#777;font-size:11px;line-height:1.5;margin:22px 0 0;border-top:1px solid #2a2a2a;padding-top:12px;">${esc(why)}
    <a href="${esc(alertsUrl)}" style="color:#999;">Change the car</a> in the Alerts tab, or
    <a href="${esc(unsubUrl)}" style="color:#999;">unsubscribe in one click</a> (deletes your address and the watch copied for it).${postal ? `<br>${esc(postal)}` : ''}</p>
</div></body></html>`;
  return { subject, text, html, to: email };
}

async function sendFreeAlertEmail(env, email, watch, cars) {
  const unsub = await freeAlertUnsubUrl(env, email);
  const { subject, text, html } = buildFreeAlertEmail(env, email, watch, cars, unsub);
  if (!env.RESEND_API_KEY) {
    // Local dev: log-and-succeed (as the Pro alert email does) so the
    // bookkeeping can be tested. Production without a key = undelivered.
    if (env.DEV_MODE === '1') {
      console.log(`DEV free alert email → ${maskEmail(email)}: ${cars.length} cars`);
      return true;
    }
    return false;
  }
  let r;
  try {
    r = await resendFetch(env, FREE_ALERT_CHANNEL, email, {
      method: 'POST',
      headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
      body: JSON.stringify({
        from: env.EMAIL_ALERTS_FROM || 'YardScout Alerts <alerts@yardscout.io>',
        to: [email], subject, text, html,
        headers: { 'List-Unsubscribe': `<${unsub}>`, 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' },
      }),
    });
  } catch (e) {
    console.log('free alert email send error:', e && e.message);
    return false;
  }
  if (!r.ok) { console.log('free alert email failed:', r.status); return false; }
  console.log(`free alert email sent to ${maskEmail(email)}: ${cars.length} cars`);
  return true;
}

/* ===== dispatch (admin.js handleCommit, after the Pro email dispatch) ===== */

const inList = (n, from = 1) => Array.from({ length: n }, (_, i) => `?${i + from}`).join(', ');

/** One email per confirmed address whose ONE watch matched new arrivals.
 * Returns {matched, emails, held, failed}. D1 work is kept small on purpose
 * (the commit's dispatchers share one budget): one read of the confirmed
 * rows; only when something matched, one batched read (dedupe + Pro
 * overlap), one small batch per email sent, one UPDATE for held rows. */
export async function dispatchFreeEmailAlerts(env, arrivals, { now = Date.now() } = {}) {
  // `carried`: alerts the scan commit's CALL budget (commit_budget.js) could
  // not carry, as opposed to `held` for the email budget. Both are kept
  // unsent and retried the same way.
  const out = { matched: 0, emails: 0, held: 0, failed: 0, carried: 0 };
  const fresh0 = Array.isArray(arrivals) ? arrivals : [];
  const rows = (await env.DB.prepare(
    `SELECT email, watch_json, watch_set_at, last_email_at, first_email_at, held_at FROM free_email_alerts
      WHERE confirmed_at IS NOT NULL AND watch_json IS NOT NULL
      ORDER BY held_at IS NULL, held_at, last_email_at IS NOT NULL, last_email_at`
  ).all()).results || [];
  if (!rows.length) return out;

  // Cars held back on an earlier scan: read back from the rolling arrivals
  // table (one read, and only while some row is inside its catch-up window).
  const heldFresh = (r) => !!r.held_at && now - Date.parse(r.held_at) < FREE_ALERT_CATCHUP_MS;
  let catchUp = [];
  if (rows.some(heldFresh)) {
    const have = new Set(fresh0.map((v) => String(v.id)));
    catchUp = (await loadArrivals(env, new Date(now - FREE_ALERT_CATCHUP_MS).toISOString())).filter((v) => !have.has(String(v.id)));
  }
  if (!fresh0.length && !catchUp.length) return out;

  const cands = [];
  for (const r of rows) {
    const watch = parseWatch(r.watch_json);
    if (!watch) continue;
    const pool = heldFresh(r)
      ? fresh0.concat(catchUp.filter((v) => !r.watch_set_at || !v.seenAt || v.seenAt >= r.watch_set_at))
      : fresh0;
    const matched = matchesOf(watch, pool);
    if (matched.length) cands.push({ row: r, watch, matched });
  }
  if (!cands.length) return out;

  // Dedupe and the Pro overlap, for the candidates only, in one round trip.
  const sent = new Map();   // email → Set(vehicle_id)
  const proOn = new Set();  // addresses with Pro email alerts switched on
  for (let i = 0; i < cands.length; i += EMAILS_PER_IN) {
    const emails = cands.slice(i, i + EMAILS_PER_IN).map((c) => c.row.email);
    const [a, b] = await env.DB.batch([
      env.DB.prepare(`SELECT email, vehicle_id FROM free_email_alerts_sent WHERE email IN (${inList(emails.length)})`).bind(...emails),
      env.DB.prepare(`SELECT email FROM email_watchers WHERE enabled = 1 AND email IN (${inList(emails.length)})`).bind(...emails),
    ]);
    for (const s of (a && a.results) || []) {
      if (!sent.has(s.email)) sent.set(s.email, new Set());
      sent.get(s.email).add(String(s.vehicle_id));
    }
    for (const p of (b && b.results) || []) proOn.add(p.email);
  }

  const budget = await freeAlertBudget(env, now);
  let left = Math.min(budget.left, FREE_ALERT_MAX_PER_SCAN);
  const holdNow = [];
  for (const c of cands) {
    const { row, watch } = c;
    const seen = sent.get(row.email);
    const fresh = c.matched.filter((v) => !(seen && seen.has(String(v.id))));
    if (!fresh.length) continue;
    // An address whose Pro email alerts are on already hears about every
    // watch in the Pro email of this same scan: never two emails for one car.
    if (proOn.has(row.email) && env.ENTITLEMENTS) {
      let ent = null;
      try { ent = await env.ENTITLEMENTS.get('ent:' + row.email, 'json'); } catch { ent = null; }
      if (entActive(ent)) continue;
    }
    out.matched++;
    // Room in the commit's call budget for one email and its one batch?
    // (Free is the last step of the commit: it gets what every other
    // dispatcher left.)
    const room = hasRoom(env, { ext: 1, svc: 2 });
    if (left <= 0 || !room) {
      // Held for a budget: not marked sent, retried on later scans for
      // FREE_ALERT_CATCHUP_MS. Counted once per held stretch, not per scan:
      // under the email budget when that is what ran out, else as carried by
      // the commit's call budget (the caller counts that).
      if (left <= 0) { if (!heldFresh(row)) { out.held++; await countHeld(env, FREE_ALERT_CHANNEL); } }
      else out.carried++;
      holdNow.push(row.email);
      continue;
    }
    left--;
    const delivered = await sendFreeAlertEmail(env, row.email, watch, fresh);
    if (!delivered) { out.failed++; continue; }   // counted by resendFetch; not retried
    out.emails++;
    const at = new Date().toISOString();
    const stmts = [];
    for (let i = 0; i < fresh.length; i += SENT_ROWS_PER_STMT) {
      const chunk = fresh.slice(i, i + SENT_ROWS_PER_STMT);
      stmts.push(env.DB.prepare(
        `INSERT OR IGNORE INTO free_email_alerts_sent (email, vehicle_id, sent_at) VALUES ${chunk.map(() => '(?, ?, ?)').join(', ')}`
      ).bind(...chunk.flatMap((v) => [row.email, String(v.id), at])));
    }
    stmts.push(env.DB.prepare(
      'UPDATE free_email_alerts SET last_email_at = ?2, first_email_at = COALESCE(first_email_at, ?2), held_at = NULL WHERE email = ?1'
    ).bind(row.email, at));
    // "First email sent": one anonymous +1 the first time an address is mailed.
    if (!row.first_email_at) stmts.push(bumpEvent(env, FREE_ALERT_FIRST_EMAIL_EVENT, null, at.slice(0, 10)));
    await env.DB.batch(stmts);
  }
  for (let i = 0; i < holdNow.length; i += EMAILS_PER_IN) {
    if (!hasRoom(env, { svc: 1 })) break;   // still unsent: the next scan's arrivals carry the same cars
    const emails = holdNow.slice(i, i + EMAILS_PER_IN);
    await env.DB.prepare(`UPDATE free_email_alerts SET held_at = ?1 WHERE email IN (${inList(emails.length, 2)})`)
      .bind(new Date(now).toISOString(), ...emails).run();
  }
  if (holdNow.length) console.log(`free email alerts: ${holdNow.length} held for the email budget (${budget.free}/${budget.dayMax} free today, ${budget.total}/${budget.cap} all mail)`);
  return out;
}

/* ===== housekeeping + numbers for the ops email ===== */

/** Hourly (index.js): unconfirmed addresses go after 7 days; a change that
 * was never confirmed is dropped when its link expires; dedupe rows go
 * after 90 days. */
export async function pruneFreeAlerts(env, now = Date.now()) {
  const cut = new Date(now - CONFIRM_TTL_MS).toISOString();
  await env.DB.batch([
    env.DB.prepare('DELETE FROM free_email_alerts WHERE confirmed_at IS NULL AND created_at < ?1').bind(cut),
    env.DB.prepare(
      `UPDATE free_email_alerts SET pending_json = NULL, confirm_hash = NULL,
              pending_source = NULL, pending_campaign = NULL, pending_medium = NULL
        WHERE confirm_hash IS NOT NULL AND (confirm_expires_at IS NULL OR confirm_expires_at < ?1)`
    ).bind(new Date(now).toISOString()),
    env.DB.prepare('DELETE FROM free_email_alerts_sent WHERE sent_at < ?1').bind(new Date(now - 90 * 86400_000).toISOString()),
  ]);
}

/** Aggregate counts for the daily ops email. No addresses. */
export async function freeAlertStats(env) {
  const r = await env.DB.prepare(
    `SELECT
       (SELECT COUNT(*) FROM free_email_alerts WHERE confirmed_at IS NOT NULL AND watch_json IS NOT NULL) AS active,
       (SELECT COUNT(*) FROM free_email_alerts WHERE confirmed_at IS NULL) AS pending,
       (SELECT COUNT(*) FROM free_email_alerts WHERE first_email_at IS NOT NULL) AS mailed`
  ).first();
  return { on: (r && r.active) || 0, pending: (r && r.pending) || 0, mailed: (r && r.mailed) || 0 };
}

/* ===== test/ops helper ===== */

/** POST /v1/admin/free-alerts/dispatch {arrivals:[...]} (x-admin-secret) —
 * runs the EXACT production path against caller-supplied arrivals, as
 * /v1/admin/email-alerts/dispatch does for the Pro emails. */
export async function handleFreeAlertDispatchRun(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  return json(await dispatchFreeEmailAlerts(env, Array.isArray(body.arrivals) ? body.arrivals : []));
}
