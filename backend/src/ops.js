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

/** Write everything buffered in ONE env.DB.batch(). Never throws; a failed
 * flush drops that buffer (logged) rather than growing without bound.
 * Returns the number of statements sent (0 when nothing was pending). */
export async function flushOps(env) {
  try {
    if (!pendingCounts.size && !pendingErrors.length) return 0;
    const counts = [...pendingCounts];
    const errors = pendingErrors;
    pendingCounts.clear();
    pendingErrors = [];
    if (!env || !env.DB) return 0;
    const stmts = [];
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
