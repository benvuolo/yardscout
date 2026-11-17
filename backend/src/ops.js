/* Send accounting (migration 0014). Every outbound notification — native
 * push, web push, every Resend email — records its outcome here so the
 * hourly ops check and the daily health email (ops_monitor.js) can see
 * breakage instead of it failing silently for weeks (2026-10-29 incident:
 * sandbox sender, digests + magic links went nowhere, nobody knew).
 *
 * Contract: these helpers NEVER throw into the send path. count* only
 * buffers in memory (zero D1 statements per send); flushOps() writes the
 * buffer in one D1 batch and swallows its own errors — a D1 hiccup costs
 * counters, never a send.
 *
 * Privacy: ops_errors.detail is scrubbed — truncated, email addresses
 * reduced to their domain, long token-like strings and API keys redacted.
 */

import { meteredFetch, BudgetExhausted } from './commit_budget.js';

export const CHANNELS = [
  'apns', 'fcm', 'webpush',
  'email:auth', 'email:digest', 'email:pro-alert', 'email:saved', 'email:coverage', 'email:ops',
  'email:confirm',
  // Free emailed alert for web visitors (free_email_alert.js): the lowest
  // class of mail, see freeAlertBudget below.
  'email:free-alert',
];

/* Not a channel: accepted free instant pushes (devices.js), counted on top of
 * their apns / fcm send. ops_monitor.js shows it as one line under the sends
 * and keeps it out of the per-channel rows. */
export const FREE_INSTANT_METRIC = 'free-instant';

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

/* ----- in-memory buffer, flushed in ONE D1 batch -----
 * Counting must not cost D1 statements per send: a commit invocation runs
 * every dispatcher (web push, devices, email, saved cars, check-ins) via
 * waitUntil and shares one per-invocation D1/subrequest budget. So count*
 * only touches this module-level buffer; flushOps(env) writes it with a
 * single env.DB.batch() — at most ceil(rows/30) counter upserts (one in
 * practice) + one multi-row ops_errors insert. Callers flush at the end of
 * each dispatch chain / scheduled branch / request (index.js, admin.js).
 * The buffer is isolate-wide, which is fine: counters are global anyway, so
 * whichever flush runs first simply writes everything pending. */
const pendingCounts = new Map();   // "day|metric" → n
let pendingErrors = [];            // newest MAX_ERRORS_PER_FLUSH failure rows
const MAX_ERRORS_PER_FLUSH = 20;
const COUNTER_ROWS_PER_STMT = 30;  // 3 binds/row; D1 caps a statement at 100 binds

function bump(channel, outcome, now) {
  const metric = `${channel}:${outcome}`;
  const day = utcDay(now);
  for (const key of [`${day}|${metric}`, `${day}|${metric}@${utcHour(now)}`]) {
    pendingCounts.set(key, (pendingCounts.get(key) || 0) + 1);
  }
}

export async function countOk(env, channel) {
  try { bump(channel, 'ok', Date.now()); } catch (e) { console.log('ops countOk failed:', channel, e && e.message); }
}

/** A push token the provider says is dead (uninstall/rotation). Normal churn,
 * not breakage — counted apart from failures. */
export async function countGone(env, channel) {
  try { bump(channel, 'gone', Date.now()); } catch (e) { console.log('ops countGone failed:', channel, e && e.message); }
}

export async function countFail(env, channel, status, detail) {
  try {
    const now = Date.now();
    bump(channel, 'fail', now);
    pendingErrors.push([new Date(now).toISOString(), channel, Number.isFinite(+status) ? +status : 0, scrub(detail)]);
    if (pendingErrors.length > MAX_ERRORS_PER_FLUSH) pendingErrors = pendingErrors.slice(-MAX_ERRORS_PER_FLUSH);
  } catch (e) { console.log('ops countFail failed:', channel, e && e.message); }
}

/** A send we chose NOT to make because the Resend daily cap is near
 * (recap_signup.js confirmations, the Monday recap). Not a failure: the
 * daily email lists it so the owner knows mail was held back. */
export async function countHeld(env, channel) {
  try { bump(channel, 'held', Date.now()); } catch (e) { console.log('ops countHeld failed:', channel, e && e.message); }
}

/* ----- the scan commit's call budget (commit_budget.js) -----
 * What a commit could not fit is carried to the next scan and counted here,
 * per step, as "<channel>:held" so sendStats (ops_monitor.js) reads it like
 * any other held count:
 *   commit:<step>            recipients that had something to send
 *   commit-unchecked:<step>  recipients the step never got to look at
 * COMMIT_STEPS is the order the steps run in (admin.js), Pro first. The
 * busiest commit of each UTC day is kept as two day-level maxima. */
export const COMMIT_STEPS = [
  ['pro-webpush', 'Pro web push alerts'],
  ['pro-device', 'Pro app push alerts'],
  ['pro-email', 'Pro email alerts'],
  ['saved', 'saved-car alerts (Pro)'],
  ['sales', 'sale-day pushes (Pro)'],
  ['arrivals-store', 'arrivals for the Monday recap'],
  ['coverage', 'coverage digest to the owner'],
  ['free-instant', 'free instant pushes'],
  ['checkin', 'first-watch check-ins'],
  ['free-email', 'free alert emails'],
];
export const COMMIT_EXT_MAX_METRIC = 'commit:ext:max';
export const COMMIT_SVC_MAX_METRIC = 'commit:svc:max';
const pendingMax = new Map();      // "day|metric" → largest value seen

/** n recipients of `step` carried to the next scan (kind 'carried'), or never
 * looked at (kind 'unchecked'). Buffered like every other counter. */
export async function countCarried(env, step, n, kind = 'carried') {
  try {
    const now = Date.now();
    const channel = (kind === 'unchecked' ? 'commit-unchecked:' : 'commit:') + step;
    for (let i = 0; i < n; i++) bump(channel, 'held', now);
  } catch (e) { console.log('ops countCarried failed:', step, e && e.message); }
}

/** Keep the day's largest value of a metric (the busiest commit). */
export async function countMax(env, metric, value) {
  try {
    const key = `${utcDay(Date.now())}|${metric}`;
    if (!(pendingMax.get(key) >= value)) pendingMax.set(key, value);
  } catch (e) { console.log('ops countMax failed:', metric, e && e.message); }
}

/* ----- the Resend daily cap (free tier: 100 emails per UTC day) -----
 * Optional sends (sign-up confirmations, the Monday recap) stop while fewer
 * than RESEND_RESERVE sends are left today, so sign-in links, Pro alerts and
 * the ops emails still have room. RESEND_DAILY_CAP (env) overrides the cap
 * for a paid plan, and for the tests. */
export const RESEND_DAILY_CAP = 100;
export const RESEND_RESERVE = 10;
export function resendDailyCap(env) {
  const n = parseInt((env && env.RESEND_DAILY_CAP) || '', 10);
  return Number.isFinite(n) && n > 0 ? n : RESEND_DAILY_CAP;
}

/** Emails Resend accepted today (UTC): the stored counters plus whatever
 * this isolate has counted but not flushed yet. Never throws (0 on error). */
export async function emailsSentToday(env, now = Date.now()) {
  const day = utcDay(now);
  let n = 0;
  for (const [key, v] of pendingCounts) {
    const cut = key.indexOf('|');
    if (key.slice(0, cut) === day && /^email:[^@]+:ok$/.test(key.slice(cut + 1))) n += v;
  }
  try {
    const row = await env.DB.prepare(
      "SELECT COALESCE(SUM(n), 0) AS n FROM ops_counters WHERE day = ?1 AND metric LIKE 'email:%:ok' AND metric NOT LIKE '%@%'"
    ).bind(day).first();
    n += (row && row.n) || 0;
  } catch (e) { console.log('ops emailsSentToday failed:', e && e.message); }
  return n;
}

/** True while an optional email may still go out today. */
export async function optionalEmailAllowed(env, now = Date.now()) {
  return (await emailsSentToday(env, now)) < resendDailyCap(env) - RESEND_RESERVE;
}

/* ----- free emailed alerts: the lowest class of mail (2026-11-17) -----
 * A free web visitor's one emailed alert (free_email_alert.js) must never
 * take room from Pro alert emails, sign-in links, confirmations, the Monday
 * recap or the ops emails. Two limits, both shares of the daily cap so they
 * follow RESEND_DAILY_CAP if the plan changes (at the free tier's 100/day:
 * 20 a day, and none once 70 emails of any kind have gone out):
 *   - at most FREE_ALERT_DAY_SHARE of the day's cap goes to free alerts;
 *   - none while fewer than FREE_ALERT_RESERVE_SHARE of the cap is left
 *     today, always more than RESEND_RESERVE, so free alerts stop well
 *     before the optional mail (confirmations, recaps) does.
 * The dispatcher adds its own per-scan cap. A skipped send is counted with
 * countHeld(env, FREE_ALERT_CHANNEL). */
export const FREE_ALERT_CHANNEL = 'email:free-alert';
export const FREE_ALERT_DAY_SHARE = 0.2;
export const FREE_ALERT_RESERVE_SHARE = 0.3;
export function freeAlertLimits(env) {
  const cap = resendDailyCap(env);
  return {
    cap,
    dayMax: Math.floor(cap * FREE_ALERT_DAY_SHARE),
    reserve: Math.max(Math.ceil(cap * FREE_ALERT_RESERVE_SHARE), RESEND_RESERVE + 1),
  };
}

/** How many free alert emails may still go out right now: {left, total,
 * free, cap, dayMax, reserve}. One D1 read, plus whatever this isolate has
 * counted but not flushed. Never throws. If the counters cannot be read the
 * answer is 0: the lowest class does not send blind. */
export async function freeAlertBudget(env, now = Date.now()) {
  const { cap, dayMax, reserve } = freeAlertLimits(env);
  const day = utcDay(now);
  let total = 0, free = 0;
  const add = (metric, n) => {
    if (!/^email:[^@]+:ok$/.test(metric)) return;
    total += n;
    if (metric === FREE_ALERT_CHANNEL + ':ok') free += n;
  };
  for (const [key, v] of pendingCounts) {
    const cut = key.indexOf('|');
    if (key.slice(0, cut) === day) add(key.slice(cut + 1), v);
  }
  let known = true;
  try {
    const rows = (await env.DB.prepare(
      "SELECT metric, n FROM ops_counters WHERE day = ?1 AND metric LIKE 'email:%:ok' AND metric NOT LIKE '%@%'"
    ).bind(day).all()).results || [];
    for (const r of rows) add(String(r.metric), r.n || 0);
  } catch (e) {
    known = false;
    console.log('ops freeAlertBudget failed:', e && e.message);
  }
  const left = known ? Math.max(0, Math.min(dayMax - free, cap - reserve - total)) : 0;
  return { left, total, free, cap, dayMax, reserve };
}

/** Write everything buffered in ONE env.DB.batch(). Never throws; a failed
 * flush drops that buffer (logged) rather than growing without bound.
 * Returns the number of statements sent (0 when nothing was pending). */
export async function flushOps(env) {
  try {
    if (!pendingCounts.size && !pendingErrors.length && !pendingMax.size) return 0;
    const counts = [...pendingCounts];
    const errors = pendingErrors;
    const maxima = [...pendingMax];
    pendingCounts.clear();
    pendingErrors = [];
    pendingMax.clear();
    if (!env || !env.DB) return 0;
    const stmts = [];
    for (let i = 0; i < maxima.length; i += COUNTER_ROWS_PER_STMT) {
      const chunk = maxima.slice(i, i + COUNTER_ROWS_PER_STMT);
      stmts.push(env.DB.prepare(
        `INSERT INTO ops_counters (day, metric, n) VALUES ${chunk.map(() => '(?, ?, ?)').join(', ')}
         ON CONFLICT (day, metric) DO UPDATE SET n = MAX(n, excluded.n)`
      ).bind(...chunk.flatMap(([key, n]) => { const cut = key.indexOf('|'); return [key.slice(0, cut), key.slice(cut + 1), n]; })));
    }
    for (let i = 0; i < counts.length; i += COUNTER_ROWS_PER_STMT) {
      const chunk = counts.slice(i, i + COUNTER_ROWS_PER_STMT);
      const binds = [];
      for (const [key, n] of chunk) {
        const cut = key.indexOf('|');
        binds.push(key.slice(0, cut), key.slice(cut + 1), n);
      }
      stmts.push(env.DB.prepare(
        `INSERT INTO ops_counters (day, metric, n) VALUES ${chunk.map(() => '(?, ?, ?)').join(', ')}
         ON CONFLICT (day, metric) DO UPDATE SET n = n + excluded.n`
      ).bind(...binds));
    }
    if (errors.length) {
      stmts.push(env.DB.prepare(
        `INSERT INTO ops_errors (at, channel, status, detail) VALUES ${errors.map(() => '(?, ?, ?, ?)').join(', ')}`
      ).bind(...errors.flat()));
    }
    await env.DB.batch(stmts);
    return stmts.length;
  } catch (e) {
    console.log('ops flush failed:', e && e.message);
    return 0;
  }
}

/** Promise-chain helper: `.finally(opsFlusher(env))` at the end of a
 * waitUntil dispatch chain. */
export const opsFlusher = (env) => () => flushOps(env);

/** Hourly (ops_monitor.js): keep the newest MAX_ERRORS rows. */
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
    r = await meteredFetch(env, resendUrl(env), init);
  } catch (e) {
    // The scan commit's call budget is used up (commit_budget.js): nothing
    // was sent and nothing failed. Callers ask hasRoom() first; this is the
    // backstop.
    if (e instanceof BudgetExhausted) throw e;
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
