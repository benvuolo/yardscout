/* One shared budget for everything a scan commit does (admin.js handleCommit).
 *
 * Why: a Worker invocation on the free plan may make only so many calls out.
 * Every dispatcher the commit runs (Pro pushes, Pro emails, saved-car alerts,
 * sale alerts, the free instant push, check-ins, the free emailed alert)
 * used to keep its own cap (35 + 25 + 20 + 5 + 20 ...) and they ran side by
 * side, so a busy scan could pass the platform limit and whichever send
 * happened to be in flight failed, unseen. Now they run one after another, in
 * priority order (Pro first, free last), against ONE budget, and what does
 * not fit is carried to the next scan and counted.
 *
 * Documented limits (Workers Free, read 2026-11-17; sources and the
 * arithmetic are in ops/growth.md, "Watertight: the commit budget"):
 *   - 50 subrequests to the outside (fetch) per invocation;
 *   - 1,000 subrequests to Cloudflare services (D1, KV) per invocation, per
 *     the Workers limits page and the 2026-02-11 changelog. The D1 limits
 *     page gives 50 queries per invocation for Free; the two pages disagree
 *     and this budget is built to the Workers page (see the note in
 *     ops/growth.md for what the stricter reading would take);
 *   - ctx.waitUntil work may run for up to 30 seconds after the response.
 * The ceilings below sit inside each, with room for what the count cannot
 * see (a redirect, the final counter write).
 *
 * How it holds, by construction:
 *   - every outside call a dispatcher makes goes through meteredFetch(), and
 *     every D1 / KV call through the env that withBudget() returns. Both
 *     count BEFORE the call and refuse (BudgetExhausted) at the ceiling, so
 *     the platform's own limit is never the thing that stops a send;
 *   - a dispatcher asks hasRoom() before each send for the send AND the
 *     bookkeeping that follows it, so it stops between recipients, never
 *     between a send and the row that says it was sent;
 *   - a recipient that was not served has no "sent" row, and every scan
 *     carries the last 3 days of arrivals, so the next scan finds the same
 *     cars for them. Recipients are taken longest-unserved first.
 * Outside a scan commit (admin test routes, the Monday cron) env carries no
 * budget and nothing here changes what those paths do.
 */

export const PLATFORM_LIMITS = {
  ext: 50,            // outside subrequests per invocation (Workers Free)
  svc: 1000,          // subrequests to Cloudflare services per invocation
  waitUntilMs: 30_000,
};
/** Outside calls one commit may make: 5 under the limit. */
export const COMMIT_EXT_CEILING = 45;
/** D1 + KV calls one commit's dispatchers may make: 100 under the limit. */
export const COMMIT_SVC_CEILING = 900;
/** No new send is started this long after the commit began. */
export const COMMIT_DEADLINE_MS = 25_000;

export class BudgetExhausted extends Error {
  constructor(kind) {
    super(`commit budget exhausted (${kind})`);
    this.name = 'BudgetExhausted';
    this.kind = kind;
  }
}

export class CommitBudget {
  constructor({ ext = COMMIT_EXT_CEILING, svc = COMMIT_SVC_CEILING, ms = COMMIT_DEADLINE_MS, now = () => Date.now() } = {}) {
    this.cap = { ext, svc };
    this.used = { ext: 0, svc: 0 };
    this.ms = ms;
    this.now = now;
    this.t0 = now();
    this.step = 'commit';
    // Set the first time a send finds no room for its outside calls. From
    // then on nothing that needs an outside call is started in this commit,
    // so a lower-priority step can never slip a cheap send past a
    // higher-priority one that was carried.
    this.extClosed = false;
    this.by = {};      // step → { ext, svc } spent
    this.cuts = {};    // step → { carried, unchecked, stopped }
  }
  elapsed() { return this.now() - this.t0; }
  timeUp() { return this.elapsed() >= this.ms; }
  left(kind) { return Math.max(0, this.cap[kind] - this.used[kind]); }
  /** Room to START something that needs this much? False after the deadline. */
  fits({ ext = 0, svc = 0 } = {}) {
    if (this.timeUp()) return false;
    if (ext > 0) {
      if (this.extClosed) return false;
      if (this.used.ext + ext > this.cap.ext) { this.extClosed = true; return false; }
    }
    if (this.used.svc + svc <= this.cap.svc) return true;
    // A send refused for lack of D1/KV room is carried just the same, so
    // outside calls close here too: a cheaper, lower-priority send must not
    // go out after it.
    if (ext > 0) this.extClosed = true;
    return false;
  }
  /** Count a call that is about to be made; throws at the ceiling. The
   * deadline does not stop it: bookkeeping for a send already made must
   * still be written. */
  spend(kind, n = 1) {
    if (this.used[kind] + n > this.cap[kind]) throw new BudgetExhausted(kind);
    this.used[kind] += n;
    const b = this.by[this.step] || (this.by[this.step] = { ext: 0, svc: 0 });
    b[kind] += n;
  }
  /** Record what a step could not do: `carried` recipients had something to
   * send and were not served; `unchecked` were not looked at; `stopped` = the
   * step ended on the ceiling itself (the backstop). */
  cut(step, { carried = 0, unchecked = 0, stopped = 0 } = {}) {
    const c = this.cuts[step] || (this.cuts[step] = { carried: 0, unchecked: 0, stopped: 0 });
    c.carried += carried; c.unchecked += unchecked; c.stopped += stopped;
  }
  summary() {
    const cuts = Object.entries(this.cuts)
      .map(([s, c]) => `${s} ${c.carried} carried${c.unchecked ? `, ${c.unchecked} not checked` : ''}${c.stopped ? ', stopped at the ceiling' : ''}`);
    return `commit budget: outside calls ${this.used.ext}/${this.cap.ext}, D1+KV calls ${this.used.svc}/${this.cap.svc}, ${(this.elapsed() / 1000).toFixed(1)} s`
      + (cuts.length ? `; carried to the next scan: ${cuts.join('; ')}` : '');
  }
}

/** The budget for one scan commit. DEV TESTS ONLY: COMMIT_EXT_CEILING_TEST
 * lowers the outside-call ceiling so an e2e can make the budget tight with a
 * handful of devices; ignored unless DEV_MODE=1 (the same guard as the FCM
 * and Resend test overrides) and never above the real ceiling. */
export function budgetFor(env) {
  const n = env && env.DEV_MODE === '1' ? parseInt(env.COMMIT_EXT_CEILING_TEST || '', 10) : NaN;
  return new CommitBudget(Number.isFinite(n) && n >= 0 && n < COMMIT_EXT_CEILING ? { ext: n } : {});
}

/** The budget this env carries, or null (not inside a scan commit). */
export function budgetOf(env) { return (env && env.__commitBudget) || null; }

/** True when there is room to start `need` ({ext, svc}). Always true outside
 * a scan commit. */
export function hasRoom(env, need) {
  const b = budgetOf(env);
  return !b || b.fits(need);
}

/** A Pro dispatcher's own per-commit send cap (35 web, 25 app, 20 email ...).
 * Those caps were each dispatcher's private guess at the shared limit. Inside
 * a scan commit the shared budget IS the limit and the order of the steps is
 * the priority, so the private cap is lifted there (else a Pro user could be
 * carried by a cap while a free send went out). Elsewhere it stands. */
export function ownCap(env, cap) { return budgetOf(env) ? Infinity : cap; }

/** fetch() for every outside call a dispatcher makes (push services, Resend). */
export async function meteredFetch(env, input, init) {
  const b = budgetOf(env);
  if (b) b.spend('ext');
  return fetch(input, init);
}

function meteredDb(db, budget) {
  const wrap = (stmt) => ({
    __raw: stmt,
    bind: (...a) => wrap(stmt.bind(...a)),
    first: async (...a) => { budget.spend('svc'); return stmt.first(...a); },
    all: async (...a) => { budget.spend('svc'); return stmt.all(...a); },
    run: async (...a) => { budget.spend('svc'); return stmt.run(...a); },
    raw: async (...a) => { budget.spend('svc'); return stmt.raw(...a); },
  });
  return {
    prepare: (sql) => wrap(db.prepare(sql)),
    // One batch is one call to D1, whatever it holds.
    batch: async (stmts) => { budget.spend('svc'); return db.batch(stmts.map((s) => (s && s.__raw) || s)); },
    exec: async (sql) => { budget.spend('svc'); return db.exec(sql); },
  };
}

function meteredKv(kv, budget) {
  const call = (name) => async (...a) => { budget.spend('svc'); return kv[name](...a); };
  return { get: call('get'), put: call('put'), delete: call('delete'), list: call('list'), getWithMetadata: call('getWithMetadata') };
}

/** env for the commit's dispatchers: the same bindings, with D1 and KV
 * counted against `budget` and the budget itself on board. */
export function withBudget(env, budget) {
  return {
    ...env,
    DB: meteredDb(env.DB, budget),
    ...(env.ENTITLEMENTS ? { ENTITLEMENTS: meteredKv(env.ENTITLEMENTS, budget) } : {}),
    __commitBudget: budget,
  };
}
