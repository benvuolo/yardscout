/* Ops monitoring: hourly owner alerts + a daily health email.
 *
 * Why: 2026-10 the free weekly digest and every magic-link email silently
 * went nowhere for weeks (sandbox Resend sender) and nothing told anyone.
 * Every send now records its outcome (ops.js → ops_counters / ops_errors);
 * this module reads those numbers plus the scan state and emails OWNER_EMAIL.
 *
 * Hourly (cron "23 * * * *", right after the scan watchdog) — runOpsCheck:
 *   stale            inv_meta.updated_at older than 6 h (scans run every 4 h)
 *   fail:<channel>   >= 3 failures in the last hour, or > 20 % of >= 5
 *                    attempts in the last 24 h
 *   gone:<channel>   > 50 % of >= 10 push attempts in 24 h rejected as dead
 *                    tokens (mass uninstall — or e.g. a wrong APNS_ENV, which
 *                    makes every token look dead and prunes them all)
 *   resend-volume    >= 90 emails sent today (UTC); Resend free tier = 100/day
 *   resend-limit     any Resend 429 / 403 in the last hour
 *   watchdog         scan watchdog's last action was 'error'
 * All newly-firing conditions go out in ONE email. Each condition is deduped
 * in KV (ops:alert-state): at most one email per condition per 6 h while it
 * stays open, and one "all clear" when it recovers. A failed send leaves the
 * state untouched so the next hour retries.
 *
 * Daily (cron "7 13 * * *" ≈ 7am Mountain) — runDailyReport: one scannable
 * plain-text summary. Subject "[YardScout daily] All good | N issues · …".
 *
 * Resend budget: 1 daily + a handful of alert emails per day at most.
 * Nothing here logs or emails secrets, tokens or user email addresses.
 */

import { json, err } from './util.js';
import { CHANNELS, utcDay, resendFetch, pruneOpsErrors } from './ops.js';

const H = 3600_000;
const DAY = 24 * H;
const STALE_AFTER_MS = 6 * H;
const REALERT_MS = 6 * H;
const RESEND_DAILY_CAP = 100;
const RESEND_WARN_AT = 90;
const DORMANT_MS = 120 * DAY;
const FROZEN_MS = 2 * DAY;
const COUNTER_RETENTION_DAYS = 60;
const STATE_KEY = 'ops:alert-state';
const MAX_YARD_NAMES = 40;

const hours = (ms) => +(ms / H).toFixed(1);
const fmtTime = (iso) => (iso ? String(iso).replace(/:\d\d(\.\d+)?Z$/, 'Z') : 'never');
const fmtInt = (n) => (n == null ? '?' : Number(n).toLocaleString('en-US'));

const CHECK_HINT = {
  apns: 'APNS_P8 / APNS_KEY_ID / APNS_TEAM_ID secrets, APNS_ENV (production vs sandbox), key not revoked at developer.apple.com.',
  fcm: 'FCM_SA_KEY secret, yardscout-fcm-sender role, FCM API enabled in the yardscout-play GCP project.',
  webpush: 'VAPID_PUBLIC_KEY / VAPID_PRIVATE_JWK pair; push-service status.',
  email: 'Resend dashboard (resend.com → Emails / Domains): sender domain still verified, API key valid, daily quota.',
};
const hintFor = (c) => CHECK_HINT[c] || (c.startsWith('email:') ? CHECK_HINT.email : 'Worker logs (wrangler tail).');

function apiBase(env) {
  return String(env.API_PUBLIC_URL || 'https://yardscout-api.yardscout.workers.dev').replace(/\/+$/, '');
}

/** Public data files. GitHub Pages first (the yardscout.io site Worker only
 * proxies it), yardscout.io as the fallback. DEV TESTS ONLY:
 * OPS_DATA_BASE_TEST (honored only with DEV_MODE=1) points at a mock. */
function dataBases(env) {
  if (env.DEV_MODE === '1' && env.OPS_DATA_BASE_TEST) return [env.OPS_DATA_BASE_TEST];
  return ['https://benvuolo.github.io/yardscout/data', 'https://yardscout.io/data'];
}

async function fetchPublicJson(env, file) {
  let lastErr = 'unreachable';
  for (const base of dataBases(env)) {
    try {
      const r = await fetch(`${base}/${file}`, {
        headers: { 'user-agent': 'yardscout-ops-monitor' },
        signal: AbortSignal.timeout(8000),
      });
      if (r.ok) return { data: await r.json() };
      lastErr = `HTTP ${r.status}`;
    } catch (e) { lastErr = (e && e.message) || 'fetch error'; }
  }
  return { error: lastErr };
}

async function loadWatchdog(env) {
  try {
    return env.ENTITLEMENTS ? JSON.parse(await env.ENTITLEMENTS.get('ops:scan-watchdog') || 'null') : null;
  } catch { return null; }
}

function fmtWatchdog(w) {
  if (!w) return 'no decision recorded';
  const bits = [w.action];
  if (w.reason) bits.push(w.reason);
  if (w.status) bits.push(`HTTP ${w.status}`);
  if (w.ageHours != null) bits.push(`last good scan ${w.ageHours} h ago`);
  return `${bits.join(', ')} (at ${fmtTime(w.at)})`;
}

async function loadState(env) {
  try {
    const s = JSON.parse(await env.ENTITLEMENTS.get(STATE_KEY) || '{}');
    return s && typeof s === 'object' ? s : {};
  } catch { return {}; }
}

/* ===== numbers ===== */

/** Per-channel ok/fail/gone for the rolling 24 h (hour buckets) and today
 * (UTC day totals), failures in the last hour, and recent error rows. */
export async function sendStats(env, now = Date.now()) {
  const rows = (await env.DB.prepare('SELECT day, metric, n FROM ops_counters WHERE day >= ?1')
    .bind(utcDay(now - DAY)).all()).results || [];
  const today = utcDay(now);
  const windowStart = Math.floor(now / H) * H - 23 * H;   // 24 hour buckets ending with the current one
  const channels = {};
  const get = (c) => channels[c] || (channels[c] = {
    last24h: { ok: 0, fail: 0, gone: 0 }, today: { ok: 0, fail: 0, gone: 0 }, failLastHour: 0,
  });
  for (const c of CHANNELS) get(c);
  for (const r of rows) {
    const m = String(r.metric).match(/^(.+):(ok|fail|gone)(?:@(\d\d))?$/);
    if (!m) continue;
    const s = get(m[1]);
    if (m[3] == null) {
      if (r.day === today) s.today[m[2]] += r.n;
    } else {
      const t = Date.parse(`${r.day}T${m[3]}:00:00Z`);
      if (t >= windowStart && t <= now) s.last24h[m[2]] += r.n;
    }
  }
  const nowIso = new Date(now).toISOString();
  const errorsLastHour = (await env.DB.prepare(
    `SELECT channel, status, COUNT(*) AS n FROM ops_errors
      WHERE at > ?1 AND at <= ?2 GROUP BY channel, status`
  ).bind(new Date(now - H).toISOString(), nowIso).all()).results || [];
  for (const e of errorsLastHour) get(e.channel).failLastHour += e.n;
  const recentErrors = (await env.DB.prepare(
    `SELECT at, channel, status, detail FROM ops_errors
      WHERE at > ?1 AND at <= ?2 ORDER BY at DESC LIMIT 20`
  ).bind(new Date(now - DAY).toISOString(), nowIso).all()).results || [];
  const emailsToday = Object.entries(channels)
    .filter(([c]) => c.startsWith('email:')).reduce((n, [, s]) => n + s.today.ok, 0);
  return { channels, errorsLastHour, recentErrors, emailsToday };
}

/** Every alert condition that is true right now. Read-only. */
export async function evaluateConditions(env, now = Date.now()) {
  const stats = await sendStats(env, now);
  const meta = await env.DB.prepare('SELECT updated_at FROM inv_meta WHERE id = 1').first();
  const watchdog = await loadWatchdog(env);
  const conditions = [];

  const lastCommitAt = (meta && meta.updated_at) || null;
  const ageMs = lastCommitAt ? now - Date.parse(lastCommitAt) : null;
  if (ageMs == null || ageMs > STALE_AFTER_MS) {
    conditions.push({
      id: 'stale', short: 'data stale',
      title: lastCommitAt
        ? `Inventory data is stale: last scan commit ${hours(ageMs)} h ago`
        : 'Inventory data is stale: no scan commit recorded',
      detail: `Last commit ${fmtTime(lastCommitAt)}; alert threshold 6 h (scans run every 4 h). `
        + `Scan watchdog: ${fmtWatchdog(watchdog)}.`,
      check: 'GitHub Actions → scan.yml on benvuolo/yardscout (failed, cancelled or never started?); '
        + `${apiBase(env)}/v1/health → scanWatchdog.`,
    });
  }

  for (const [c, s] of Object.entries(stats.channels)) {
    const a = s.last24h.ok + s.last24h.fail + s.last24h.gone;
    const rate = a ? s.last24h.fail / a : 0;
    const last = stats.recentErrors.find((e) => e.channel === c);
    const lastTxt = last ? `Latest: HTTP ${last.status || 'network error'} at ${fmtTime(last.at)} — ${last.detail || '(no detail)'}` : '';
    if (s.failLastHour >= 3 || (a >= 5 && rate > 0.2)) {
      conditions.push({
        id: `fail:${c}`, short: `${c} failing`,
        title: `${c} sends failing: ${s.failLastHour} in the last hour, ${s.last24h.fail} of ${a} (${Math.round(rate * 100)}%) in 24 h`,
        detail: lastTxt || 'No error detail recorded.',
        check: hintFor(c),
      });
    }
    if (!c.startsWith('email:') && a >= 10 && s.last24h.gone / a > 0.5) {
      conditions.push({
        id: `gone:${c}`, short: `${c} tokens rejected`,
        title: `${c}: ${s.last24h.gone} of ${a} push attempts in 24 h rejected as dead tokens`,
        detail: 'Dead tokens are pruned automatically. A mass uninstall is unlikely; a config mismatch '
          + '(e.g. APNS_ENV sandbox vs production, wrong bundle/project id) makes every token look dead.',
        check: hintFor(c),
      });
    }
  }

  if (stats.emailsToday >= RESEND_WARN_AT) {
    conditions.push({
      id: 'resend-volume', short: 'Resend near daily cap',
      title: `Resend volume: ${stats.emailsToday} of ${RESEND_DAILY_CAP} emails sent today (UTC)`,
      detail: 'The Resend free tier stops at 100/day; later sends (magic links included) fail until the quota resets.',
      check: 'Which channel is sending (daily email / admin ops daily run); Resend plan & usage page.',
    });
  }

  const limited = stats.errorsLastHour.filter((e) => String(e.channel).startsWith('email:') && (e.status === 429 || e.status === 403));
  if (limited.length) {
    const n = limited.reduce((k, e) => k + e.n, 0);
    const codes = [...new Set(limited.map((e) => e.status))].join('/');
    const where = [...new Set(limited.map((e) => e.channel))].join(', ');
    const last = stats.recentErrors.find((e) => String(e.channel).startsWith('email:') && (e.status === 429 || e.status === 403));
    conditions.push({
      id: 'resend-limit', short: `Resend ${codes}`,
      title: `Resend rejected ${n} email${n === 1 ? '' : 's'} with HTTP ${codes} in the last hour (${where})`,
      detail: '403 = sender/domain not allowed (sandbox sender, unverified domain) or bad API key; 429 = rate limit or daily quota.'
        + (last ? ` Latest: ${last.detail || '(no detail)'}` : ''),
      check: CHECK_HINT.email,
    });
  }

  if (watchdog && watchdog.action === 'error') {
    conditions.push({
      id: 'watchdog', short: 'scan watchdog error',
      title: `Scan watchdog errored${watchdog.status ? ` (GitHub API HTTP ${watchdog.status})` : ''}`,
      detail: `Last decision: ${fmtWatchdog(watchdog)}. While it errors it cannot re-dispatch missed scans.`,
      check: 'SCAN_DISPATCH_TOKEN (expired? needs Actions: Read and write on benvuolo/yardscout); githubstatus.com.',
    });
  }

  return { conditions, stats, facts: { lastCommitAt, ageHours: ageMs == null ? null : hours(ageMs), watchdog } };
}

/* ===== sending ===== */

/** One plain-text email to OWNER_EMAIL (channel email:ops). Returns true
 * when Resend accepted it. Never throws. */
export async function sendOpsEmail(env, { subject, text }) {
  try {
    const to = env.OWNER_EMAIL;
    if (!to) { console.log('ops email: OWNER_EMAIL not configured — skipped'); return false; }
    if (!env.RESEND_API_KEY) {
      if (env.DEV_MODE === '1') { console.log(`DEV ops email: ${subject}`); return true; }
      console.log('ops email: RESEND_API_KEY missing — not sent:', subject);
      return false;
    }
    const r = await resendFetch(env, 'email:ops', to, {
      method: 'POST',
      headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
      body: JSON.stringify({
        from: env.EMAIL_FROM || 'YardScout <hello@yardscout.io>',
        to: [to], subject, text,
      }),
    });
    if (!r.ok) console.log('ops email failed:', r.status);
    return r.ok;
  } catch (e) {
    console.log('ops email error:', e && e.message);
    return false;
  }
}

/* ===== hourly check ===== */

function composeAlertEmail(env, { fire, clear, ongoing, state, now }) {
  let subject;
  if (fire.length === 1) subject = `[YardScout alert] ${fire[0].title}`;
  else if (fire.length > 1) subject = `[YardScout alert] ${fire.length} problems: ${fire.map((c) => c.short).join(', ')}`;
  else subject = `[YardScout alert] All clear: ${clear.map((c) => c.short || c.id).join(', ')}`;
  if (subject.length > 150) subject = subject.slice(0, 149) + '…';

  const out = [];
  for (const c of fire) {
    const prev = state[c.id];
    out.push(`PROBLEM: ${c.title}${prev ? `  (still open — since ${fmtTime(prev.since)}, ${hours(now - Date.parse(prev.since))} h)` : ''}`);
    out.push(`  ${c.detail}`);
    out.push(`  Check: ${c.check}`);
    out.push('');
  }
  for (const c of clear) {
    out.push(`RECOVERED: ${c.short || c.id} — OK again after ${Math.max(0, hours(now - Date.parse(c.since)))} h (was: ${c.title || c.id}).`);
  }
  if (clear.length) out.push('');
  if (ongoing.length) {
    out.push(`Still open (already alerted, reminder every 6 h): ${ongoing.map((c) => c.short).join(', ')}`);
    out.push('');
  }
  out.push('— YardScout hourly ops check (yardscout-api). Max one email per problem per 6 h; one "all clear" on recovery.');
  out.push(`Health: ${apiBase(env)}/v1/health`);
  return { subject, text: out.join('\n') + '\n' };
}

/** The hourly check. Returns a JSON-able report; sends unless dryRun. */
export async function runOpsCheck(env, { now = Date.now(), dryRun = false } = {}) {
  const nowIso = new Date(now).toISOString();
  if (!dryRun) {
    try {
      await pruneOpsErrors(env);
      await env.DB.prepare('DELETE FROM ops_counters WHERE day < ?1')
        .bind(utcDay(now - COUNTER_RETENTION_DAYS * DAY)).run();
    } catch (e) { console.log('ops prune failed:', e && e.message); }
  }
  const ev = await evaluateConditions(env, now);
  const state = env.ENTITLEMENTS ? await loadState(env) : {};
  const activeIds = new Set(ev.conditions.map((c) => c.id));
  const fire = ev.conditions.filter((c) => {
    const s = state[c.id];
    return !s || !(now - Date.parse(s.lastSentAt) < REALERT_MS);
  });
  const clear = Object.keys(state).filter((id) => !activeIds.has(id)).map((id) => ({ id, ...state[id] }));
  const ongoing = ev.conditions.filter((c) => !fire.includes(c));

  let email = null, sent = false, reason = 'nothing new';
  if (fire.length || clear.length) {
    email = composeAlertEmail(env, { fire, clear, ongoing, state, now });
    if (dryRun) reason = 'dry run';
    else if (!env.ENTITLEMENTS) reason = 'no KV binding — cannot dedupe, not sending';
    else {
      sent = await sendOpsEmail(env, email);
      reason = sent ? 'sent' : 'send failed (state unchanged; retries next hour)';
      if (sent) {
        for (const c of fire) {
          state[c.id] = { since: (state[c.id] && state[c.id].since) || nowIso, lastSentAt: nowIso, title: c.title, short: c.short };
        }
        for (const c of clear) delete state[c.id];
        try { await env.ENTITLEMENTS.put(STATE_KEY, JSON.stringify(state)); } catch (e) { console.log('ops state save failed:', e && e.message); }
      }
    }
  }
  return {
    at: nowIso, dryRun,
    active: ev.conditions.map((c) => ({ id: c.id, title: c.title })),
    alerted: fire.map((c) => c.id),
    cleared: clear.map((c) => c.id),
    deduped: ongoing.map((c) => c.id),
    email, sent, reason,
    emailsToday: ev.stats.emailsToday,
  };
}

/* ===== daily health email ===== */

function yardFlags(h) {
  if (!h || typeof h.yards !== 'object' || !h.yards) return null;
  const scraped = Date.parse(h.scrapedAt) || Date.now();
  const dormant = [], frozen = [];
  for (const [name, y] of Object.entries(h.yards)) {
    if (!y || typeof y !== 'object') continue;
    const newest = y.newestDateAdded ? Date.parse(String(y.newestDateAdded).slice(0, 10) + 'T00:00:00Z') : NaN;
    if (Number.isFinite(newest) && scraped - newest > DORMANT_MS) dormant.push({ name, newestDateAdded: y.newestDateAdded });
    const changed = y.lastChangedAt ? Date.parse(y.lastChangedAt) : NaN;
    if (Number.isFinite(changed) && scraped - changed > FROZEN_MS) frozen.push({ name, lastChangedAt: y.lastChangedAt });
  }
  dormant.sort((a, b) => String(a.newestDateAdded).localeCompare(String(b.newestDateAdded)));
  frozen.sort((a, b) => String(a.lastChangedAt).localeCompare(String(b.lastChangedAt)));
  return { scrapedAt: h.scrapedAt || null, yards: Object.keys(h.yards).length, dormant, frozen };
}

function nameList(items, fmt) {
  const shown = items.slice(0, MAX_YARD_NAMES).map(fmt);
  return shown.join('; ') + (items.length > shown.length ? `; +${items.length - shown.length} more` : '');
}

const FUNNEL_ROWS = [
  ['first-visit', 'First visits'], ['zip-entered', 'Entered a zip'], ['part-first-search', 'Part searches'],
  ['watch-created', 'Watches created'], ['push-enabled', 'Alerts turned on'], ['checkout-start', 'Checkout taps'],
  ['pro-converted', 'Purchases'],
];

function usageLines(u, audience) {
  if (!u || u.error) return [`USAGE: could not load (${(u && u.error) || 'unknown'})`];
  const L = ['USAGE'];
  const d = u.devices;
  L.push(`  App devices: ${fmtInt(d.total)} (${fmtInt(d.pro)} pro) · alerts on ${fmtInt(d.push)}`
    + ` · with a watch ${fmtInt(d.withWatches)} (${fmtInt(d.watches)} watches)`);
  if (d.byPlatform.length) L.push(`    ${d.byPlatform.map((r) => `${r.platform} ${r.tier} ${fmtInt(r.n)}`).join(' · ')}`);
  L.push(`  New devices: ${fmtInt(d.newYesterday)} yesterday · ${fmtInt(d.new7d)} in 7 d · used in last 7 d: ${fmtInt(d.active7d)}`);
  L.push(`  Web accounts: ${fmtInt(u.web.accounts)} (${fmtInt(u.web.pro)} pro, ${fmtInt(u.web.active30d)} signed in 30 d)`
    + ` · web watches ${fmtInt(u.web.watches)} · email-alert watchers ${fmtInt(audience && audience.emailWatchers)}`);
  L.push(`  Funnel (all platforms)       yesterday     7 d`);
  for (const [k, label] of FUNNEL_ROWS) {
    const f = u.funnel[k] || { yesterday: 0, week: 0 };
    L.push(`    ${label.padEnd(24)} ${String(fmtInt(f.yesterday)).padStart(9)} ${String(fmtInt(f.week)).padStart(7)}`);
  }
  L.push(`  Tagged sources (first visits, 7 d): ${u.sources.length
    ? u.sources.map((s) => `${s.source} ${fmtInt(s.n)}`).join(', ') : 'none (add ?utm_source=… to links you post)'}`);
  if (u.topWatches.length) L.push(`  Most watched: ${u.topWatches.map((w) => `${w.name} ${fmtInt(w.n)}`).join(', ')}`);
  return L;
}

function composeDaily(r) {
  const L = [];
  const d = new Date(r.at);
  L.push(`YardScout daily — ${d.toUTCString().slice(0, 16)} (${d.toISOString().slice(11, 16)} UTC)`);
  L.push(`Verdict: ${r.verdict}`);
  L.push('');
  L.push(`OPEN ISSUES${r.openConditions.length ? ` (${r.openConditions.length})` : ''}`);
  if (r.openConditions.length) for (const c of r.openConditions) L.push(`  - ${c.title}`);
  else L.push('  none');
  L.push('');
  L.push('SCAN');
  L.push(`  Last commit: ${fmtTime(r.scan.lastCommitAt)}${r.scan.ageHours != null ? ` (${r.scan.ageHours} h ago)` : ''}`
    + `${r.scan.scrapedAt ? ` · scraped ${fmtTime(r.scan.scrapedAt)}` : ''}`);
  L.push(`  Live: ${fmtInt(r.inventory.yards)} yards · ${fmtInt(r.inventory.vehicles)} vehicles`
    + (r.inventory.publicVehicles != null && r.inventory.publicVehicles !== r.inventory.vehicles
      ? ` (public inventory_meta.json: ${fmtInt(r.inventory.publicVehicles)})` : ''));
  L.push(`  Watchdog: ${fmtWatchdog(r.watchdog)}`);
  L.push('');
  const yh = r.yardHealth;
  if (yh && !yh.error) {
    L.push(`YARD HEALTH (yard_health.json: ${yh.yards} yards, scraped ${fmtTime(yh.scrapedAt)})`);
    L.push(`  Dormant, no new car in 120+ d: ${yh.dormant.length}${yh.dormant.length ? ' — ' + nameList(yh.dormant, (y) => `${y.name} (newest ${y.newestDateAdded})`) : ''}`);
    L.push(`  Frozen, unchanged 2+ d: ${yh.frozen.length}${yh.frozen.length ? ' — ' + nameList(yh.frozen, (y) => `${y.name} (${String(y.lastChangedAt).slice(5, 10)})`) : ''}`);
  } else {
    L.push(`YARD HEALTH: could not load yard_health.json (${(yh && yh.error) || 'unknown'})`);
  }
  L.push('');
  L.push('SENDS, last 24 h (ok / fail / dead tokens)');
  const active = Object.entries(r.channels).filter(([, s]) => s.ok + s.fail + s.gone > 0);
  if (active.length) {
    for (const [c, s] of active) {
      L.push(`  ${c.padEnd(15)} ${String(s.ok).padStart(5)} / ${s.fail}${c.startsWith('email:') ? '' : ` / ${s.gone}`}${s.fail ? '  <-' : ''}`);
    }
  } else L.push('  no sends recorded');
  L.push(`  Resend today (UTC): ${r.resend.sentToday} / ${r.resend.dailyCap}`);
  if (r.recentErrors.length) {
    // Identical errors collapse to one line with a count.
    const groups = [];
    for (const e of r.recentErrors) {
      const g = groups.find((x) => x.channel === e.channel && x.status === e.status && x.detail === e.detail);
      if (g) g.n++; else groups.push({ ...e, n: 1 });
    }
    L.push('  Latest errors:');
    for (const e of groups.slice(0, 3)) {
      L.push(`    ${fmtTime(e.at).slice(11)} ${e.channel} HTTP ${e.status || 'net'}${e.n > 1 ? ` ×${e.n}` : ''} — ${String(e.detail || '').slice(0, 140)}`);
    }
  }
  L.push('');
  L.push(...usageLines(r.usage, r.audience));
  L.push('');
  L.push('— YardScout daily health (yardscout-api, 13:07 UTC). Problems also alert hourly with subject "[YardScout alert]".');
  return L.join('\n') + '\n';
}

/** Who is using the app: devices, accounts, watches and the funnel counters
 * (events_daily). Aggregate counts only — no ids, emails or tokens. One D1
 * batch; a failure here never blocks the rest of the daily email. */
async function loadUsage(env, now) {
  const today = utcDay(now), yesterday = utcDay(now - DAY), weekAgo = utcDay(now - 7 * DAY);
  const iso = (ms) => new Date(ms).toISOString();
  const watchesOk = `watches_json IS NOT NULL AND json_valid(watches_json)`;
  const [dev, users, webWatches, events, sources, top] = (await env.DB.batch([
    env.DB.prepare(
      `SELECT platform, tier, COUNT(*) AS n,
              SUM(CASE WHEN apns_token IS NOT NULL OR fcm_token IS NOT NULL THEN 1 ELSE 0 END) AS push,
              SUM(CASE WHEN ${watchesOk} AND json_array_length(watches_json) > 0 THEN 1 ELSE 0 END) AS withWatches,
              SUM(CASE WHEN ${watchesOk} THEN json_array_length(watches_json) ELSE 0 END) AS watches,
              SUM(CASE WHEN updated_at >= ?1 THEN 1 ELSE 0 END) AS active7d,
              SUM(CASE WHEN created_at >= ?2 AND created_at < ?3 THEN 1 ELSE 0 END) AS newYesterday,
              SUM(CASE WHEN created_at >= ?1 THEN 1 ELSE 0 END) AS new7d
         FROM devices GROUP BY platform, tier ORDER BY platform, tier`
    ).bind(iso(now - 7 * DAY), `${yesterday}T00:00:00`, `${today}T00:00:00`),
    env.DB.prepare(
      `SELECT tier, COUNT(*) AS n, SUM(CASE WHEN last_login_at >= ?1 THEN 1 ELSE 0 END) AS active30d
         FROM users GROUP BY tier`
    ).bind(iso(now - 30 * DAY)),
    env.DB.prepare('SELECT COUNT(*) AS n FROM watches'),
    env.DB.prepare(
      `SELECT event, SUM(CASE WHEN day = ?1 THEN n ELSE 0 END) AS yesterday, SUM(n) AS week
         FROM events_daily WHERE day >= ?2 AND day < ?3 GROUP BY event`
    ).bind(yesterday, weekAgo, today),
    env.DB.prepare(
      `SELECT source, SUM(n) AS n FROM events_daily
        WHERE event = 'first-visit' AND source != '' AND day >= ?1 AND day < ?2
        GROUP BY source ORDER BY n DESC LIMIT 5`
    ).bind(weekAgo, today),
    env.DB.prepare(
      `SELECT json_extract(w.value, '$.make') AS make, json_extract(w.value, '$.model') AS model, COUNT(*) AS n
         FROM devices d, json_each(d.watches_json) w
        WHERE d.watches_json IS NOT NULL AND json_valid(d.watches_json)
        GROUP BY make, model ORDER BY n DESC LIMIT 5`
    ),
  ])).map((r) => r.results || []);
  const sum = (rows, k) => rows.reduce((a, r) => a + (r[k] || 0), 0);
  const funnel = {};
  for (const e of events) funnel[e.event] = { yesterday: e.yesterday || 0, week: e.week || 0 };
  return {
    devices: {
      total: sum(dev, 'n'), pro: sum(dev.filter((r) => r.tier === 'pro'), 'n'),
      push: sum(dev, 'push'), withWatches: sum(dev, 'withWatches'), watches: sum(dev, 'watches'),
      active7d: sum(dev, 'active7d'), newYesterday: sum(dev, 'newYesterday'), new7d: sum(dev, 'new7d'),
      byPlatform: dev.map((r) => ({ platform: r.platform, tier: r.tier, n: r.n })),
    },
    web: {
      accounts: sum(users, 'n'), pro: sum(users.filter((r) => r.tier !== 'free'), 'n'),
      active30d: sum(users, 'active30d'), watches: (webWatches[0] && webWatches[0].n) || 0,
    },
    funnel,
    sources: sources.map((r) => ({ source: r.source, n: r.n })),
    topWatches: top.map((r) => ({ name: [r.make, r.model].filter(Boolean).join(' ') || 'any', n: r.n })),
  };
}

/** Builds the daily report (JSON + the email it would send). Read-only. */
export async function buildDailyReport(env, { now = Date.now() } = {}) {
  const ev = await evaluateConditions(env, now);
  const row = await env.DB.prepare('SELECT directory FROM inv_meta WHERE id = 1').first();
  let dir = null;
  try { dir = row ? JSON.parse(row.directory) : null; } catch { dir = null; }
  const [health, pubMeta] = await Promise.all([
    fetchPublicJson(env, 'yard_health.json'),
    fetchPublicJson(env, 'inventory_meta.json'),
  ]);
  const yardHealth = health.data ? (yardFlags(health.data) || { error: 'unexpected shape' }) : { error: health.error };

  const tiers = (await env.DB.prepare(
    `SELECT tier, COUNT(*) AS n FROM devices
      WHERE apns_token IS NOT NULL OR fcm_token IS NOT NULL GROUP BY tier`
  ).all()).results || [];
  const watchers = await env.DB.prepare('SELECT COUNT(*) AS n FROM email_watchers WHERE enabled = 1').first();
  let usage;
  try { usage = await loadUsage(env, now); } catch (e) { usage = { error: String((e && e.message) || e).slice(0, 200) }; }

  const channels = {};
  for (const [c, s] of Object.entries(ev.stats.channels)) channels[c] = { ...s.last24h };
  const n = ev.conditions.length;
  const report = {
    at: new Date(now).toISOString(),
    verdict: n ? `${n} issue${n === 1 ? '' : 's'}` : 'All good',
    openConditions: ev.conditions.map((c) => ({ id: c.id, title: c.title })),
    scan: { lastCommitAt: ev.facts.lastCommitAt, ageHours: ev.facts.ageHours, scrapedAt: (dir && dir.scrapedAt) || null },
    inventory: {
      yards: dir ? (Array.isArray(dir.yards) ? dir.yards.length : (dir.counts && dir.counts.yards)) : null,
      vehicles: dir && dir.counts ? dir.counts.vehicles : null,
      publicVehicles: pubMeta.data && Number.isFinite(+pubMeta.data.vehicles) ? +pubMeta.data.vehicles : null,
      publicScrapedAt: (pubMeta.data && pubMeta.data.scrapedAt) || null,
    },
    yardHealth,
    channels,
    resend: { sentToday: ev.stats.emailsToday, dailyCap: RESEND_DAILY_CAP },
    recentErrors: ev.stats.recentErrors.slice(0, 5),
    watchdog: ev.facts.watchdog,
    audience: {
      proDevices: tiers.filter((t) => t.tier === 'pro').reduce((k, t) => k + t.n, 0),
      freeDevices: tiers.filter((t) => t.tier !== 'pro').reduce((k, t) => k + t.n, 0),
      emailWatchers: (watchers && watchers.n) || 0,
    },
    usage,
  };
  const tail = report.inventory.yards != null
    ? ` · ${fmtInt(report.inventory.yards)} yards · ${fmtInt(report.inventory.vehicles)} cars` : '';
  report.email = { subject: `[YardScout daily] ${report.verdict}${tail}`, text: composeDaily(report) };
  return report;
}

export async function runDailyReport(env, { now = Date.now(), dryRun = false } = {}) {
  const report = await buildDailyReport(env, { now });
  report.dryRun = dryRun;
  report.sent = dryRun ? false : await sendOpsEmail(env, report.email);
  return report;
}

/* ===== admin triggers (x-admin-secret; routed in index.js) ===== */

async function opsBody(req, env) {
  let body = {};
  try { body = await req.json(); } catch { body = {}; }
  // Simulated clock for tests only — in production the check always runs "now".
  const off = env.DEV_MODE === '1' && Number.isFinite(+body.nowOffsetHours) ? +body.nowOffsetHours : 0;
  return { dryRun: body.dryRun === true, now: Date.now() + off * H };
}

/** POST /v1/admin/ops/check/run {dryRun?} — the hourly alert check, now. */
export async function handleOpsCheckRun(req, env) {
  try {
    return json(await runOpsCheck(env, await opsBody(req, env)));
  } catch (e) {
    console.log('ops check failed:', e && (e.stack || e.message));
    return err(500, 'ops_check_failed', 'Ops check failed — see Worker logs.');
  }
}

/** POST /v1/admin/ops/daily/run {dryRun?} — build (and send) the daily email. */
export async function handleOpsDailyRun(req, env) {
  try {
    return json(await runDailyReport(env, await opsBody(req, env)));
  } catch (e) {
    console.log('ops daily failed:', e && (e.stack || e.message));
    return err(500, 'ops_daily_failed', 'Daily report failed — see Worker logs.');
  }
}
