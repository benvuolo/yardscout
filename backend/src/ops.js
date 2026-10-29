/* Send accounting (migration 0014). Every outbound notification — native
 * push, web push, every Resend email — records its outcome here so the
 * hourly ops check and the daily health email (ops_monitor.js) can see
 * breakage instead of it failing silently for weeks (2026-10-29 incident:
 * sandbox sender, digests + magic links went nowhere, nobody knew).
 *
 * Contract: these helpers NEVER throw into the send path. Every write is
 * wrapped; a D1 hiccup costs a counter, never a send.
 *
 * Privacy: ops_errors.detail is scrubbed — truncated, email addresses
 * reduced to their domain, long token-like strings and API keys redacted.
 */

export const CHANNELS = [
  'apns', 'fcm', 'webpush',
  'email:auth', 'email:digest', 'email:pro-alert', 'email:saved', 'email:coverage', 'email:ops',
];

const MAX_ERRORS = 500;
const DETAIL_MAX = 200;

export const utcDay = (ms) => new Date(ms).toISOString().slice(0, 10);
const utcHour = (ms) => new Date(ms).toISOString().slice(11, 13);

/** Strip anything sensitive from a free-text error detail. */
export function scrub(s, max = DETAIL_MAX) {
  return String(s == null ? '' : s)
    .replace(/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)/g, '*@$1')
    .replace(/\b(?:re|sk|pk|rk|whsec|ys_[a-z]+)_[A-Za-z0-9_-]{6,}/g, '[key]')
    .replace(/[A-Za-z0-9_\-:.+/=]{40,}/g, '[redacted]')   // push tokens, JWTs, bearers
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

/** "Name <a@b.com>" | "a@b.com" | ["a@b.com"] → "b.com" (or ''). */
export function emailDomain(to) {
  const s = String(Array.isArray(to) ? to[0] : (to || ''));
  const m = s.match(/@([A-Za-z0-9.-]+)/);
  return m ? m[1].toLowerCase() : '';
}

async function bump(env, channel, outcome, now) {
  const metric = `${channel}:${outcome}`;
  await env.DB.prepare(
    `INSERT INTO ops_counters (day, metric, n) VALUES (?1, ?2, 1), (?1, ?3, 1)
     ON CONFLICT (day, metric) DO UPDATE SET n = n + 1`
  ).bind(utcDay(now), metric, `${metric}@${utcHour(now)}`).run();
}

export async function countOk(env, channel) {
  try {
    if (env && env.DB) await bump(env, channel, 'ok', Date.now());
  } catch (e) { console.log('ops countOk failed:', channel, e && e.message); }
}

/** A push token the provider says is dead (uninstall/rotation). Normal churn,
 * not breakage — counted apart from failures. */
export async function countGone(env, channel) {
  try {
    if (env && env.DB) await bump(env, channel, 'gone', Date.now());
  } catch (e) { console.log('ops countGone failed:', channel, e && e.message); }
}

export async function countFail(env, channel, status, detail) {
  try {
    if (!env || !env.DB) return;
    const now = Date.now();
    await bump(env, channel, 'fail', now);
    await env.DB.prepare('INSERT INTO ops_errors (at, channel, status, detail) VALUES (?1, ?2, ?3, ?4)')
      .bind(new Date(now).toISOString(), channel, Number.isFinite(+status) ? +status : 0, scrub(detail)).run();
    // Cheap amortized prune (the hourly check prunes too).
    if (Math.random() < 0.05) await pruneOpsErrors(env);
  } catch (e) { console.log('ops countFail failed:', channel, e && e.message); }
}

export async function pruneOpsErrors(env) {
  await env.DB.prepare(
    `DELETE FROM ops_errors WHERE rowid NOT IN
       (SELECT rowid FROM ops_errors ORDER BY rowid DESC LIMIT ?1)`
  ).bind(MAX_ERRORS).run();
}

/** Resend endpoint. DEV TESTS ONLY: RESEND_API_URL_TEST points at a local
 * mock (test/mock-resend.mjs); ignored unless DEV_MODE=1 — same guard as
 * the FCM test overrides. */
export function resendUrl(env) {
  return (env.DEV_MODE === '1' && env.RESEND_API_URL_TEST) || 'https://api.resend.com/emails';
}

/** fetch() to Resend + outcome accounting. Semantics are exactly the caller's
 * old `fetch('https://api.resend.com/emails', init)`: returns the Response,
 * rethrows network errors. `to` is only used for the recipient DOMAIN in a
 * failure detail. */
export async function resendFetch(env, channel, to, init) {
  let r;
  try {
    r = await fetch(resendUrl(env), init);
  } catch (e) {
    await countFail(env, channel, 0, `fetch error: ${e && e.message}`);
    throw e;
  }
  try {
    if (r.ok) {
      await countOk(env, channel);
    } else {
      let body = '';
      try { body = await r.clone().text(); } catch { body = ''; }
      // Resend errors are {statusCode, name, message}: keep the readable part.
      try {
        const j = JSON.parse(body);
        body = [j.name, j.message].filter(Boolean).join(': ') || body;
      } catch { /* not JSON — keep raw */ }
      const dom = emailDomain(to);
      await countFail(env, channel, r.status, `${dom ? `to *@${dom}: ` : ''}${body.slice(0, 400)}`);
    }
  } catch (e) { console.log('ops resend accounting failed:', e && e.message); }
  return r;
}
