/* Weekly scorecard (2026-11-12, growth): the five numbers the owner decides
 * marketing and pricing from, at the top of the daily ops email and as JSON
 * from GET /v1/admin/scorecard (x-admin-secret, routed in index.js).
 *
 * Always the last 7 FULL UTC days against the 7 days before them:
 *   1. new visitors a day (first-visit), by platform and by tagged link
 *   2. watches created
 *   3. Monday-email sign-ups (website): asked, gave an address, confirmed
 *   4. Pro sheet opens -> checkout starts (rate) -> Pro bought
 *   5. paying subscribers (App Store + Google Play + web) and the change
 *      from 7 days ago, from a daily snapshot this module stores
 * plus one line per tagged link: visits -> watches -> emails -> checkouts -> Pro.
 *
 * Honesty rules (the owner reads this on a phone and acts on it):
 *   - A platform whose fixed counting (attribution.js 'funnel-v2' marker)
 *     started after the first day of either window gets no change figure:
 *     "not comparable before <date>". A platform with no marker at all is
 *     not comparable either (the apps sent nothing 2026-11-02 until a fixed
 *     build ships).
 *   - 0 is a number; a platform with no counter row at all in a window is
 *     "no data", never 0.
 *   - A rate (or a % change) over a base under 20 is shown as raw counts.
 *   - Daily anonymous counters only: no ids, IPs or anything per person.
 *   - Subscriber change is only from stored snapshots: never back-filled,
 *     never estimated. Until a snapshot from 7 days ago exists it says
 *     "tracking starts <date>".
 *
 * computeScorecard is pure (fixture-tested in test/scorecard_unit.mjs);
 * loadScorecardInputs does the reads; the renderers take its output. */

import { FUNNEL_V2_MARK } from './attribution.js';

export const SUBS_HISTORY_KEY = 'ops:subs-daily';
const SUBS_HISTORY_KEEP_DAYS = 60;
export const SMALL_BASE = 20;
const TOP_SOURCES = 5;
const TOP_SOURCE_ROWS = 8;

export const SC_PLATFORMS = [['web', 'Web'], ['ios', 'iPhone app'], ['android', 'Android app']];
const EVENTS = ['first-visit', 'watch-created', 'email-asked', 'email-submitted', 'email-confirmed',
  'paywall', 'checkout-start', 'pro-converted'];
// The Monday email ask exists on the website only.
const WEB_ONLY = new Set(['email-asked', 'email-submitted', 'email-confirmed']);

const DAY_MS = 86400000;
export const addDays = (day, n) => new Date(Date.parse(day + 'T00:00:00Z') + n * DAY_MS).toISOString().slice(0, 10);
export const scDay = (day) => new Date(day + 'T00:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
const fmt = (n) => Number(n).toLocaleString('en-US');

/** The two windows for a run on `today` (UTC day): inclusive day bounds. */
export function scorecardWindows(today) {
  return {
    today,
    current: { from: addDays(today, -7), to: addDays(today, -1) },
    prior: { from: addDays(today, -14), to: addDays(today, -8) },
  };
}

/** "8% (3 of 40)" or, under SMALL_BASE, "3 of 9". null if either is missing. */
export function rateText(num, den) {
  if (num == null || den == null) return null;
  if (den < SMALL_BASE) return `${fmt(num)} of ${fmt(den)}`;
  return `${Math.round((num / den) * 100)}% (${fmt(num)} of ${fmt(den)})`;
}

/** Change between two weekly counts, as plain words. */
export function changeText(cur, prior) {
  if (cur == null || prior == null) return { kind: 'no-data', text: 'no data for one of the weeks' };
  const delta = cur - prior;
  if (prior < SMALL_BASE) {
    return { kind: 'counts', delta, text: `${fmt(cur)} vs ${fmt(prior)} the week before` };
  }
  const pct = Math.round((delta / prior) * 100);
  return { kind: 'pct', delta, pct, text: `${pct > 0 ? '+' : ''}${pct}% on the week before (${fmt(prior)})` };
}

/** Is a platform's counting the same across both windows? */
function comparability(p, v2, w) {
  const since = v2[p];
  if (!since) return { ok: false, since: null };
  return since <= w.prior.from ? { ok: true, since } : { ok: false, since };
}
function notComparableText(name, c) {
  return c.since ? `not comparable before ${scDay(c.since)}`
    : `not comparable yet (${name} update pending)`;
}

/**
 * rows:     [{day, event, source, campaign, medium, platform, n}] for days in both windows
 * presence: [{day, platform}] every (day, platform) with ANY counter row (any event)
 * v2:       {platform: first day of the fixed counting}
 * subs:     null | {error} | {apple, google, web, complete, asOf}  (today's live counts)
 * history:  {days: {day: {apple, google, web, total, complete}}} stored snapshots (before today's)
 */
export function computeScorecard({ today, rows = [], presence = [], v2 = {}, subs = null, history = null, eventsError = null, storingToday = true }) {
  const w = scorecardWindows(today);
  const inWin = (day, win) => day >= win.from && day <= win.to;
  const winOf = (day) => (inWin(day, w.current) ? 'current' : inWin(day, w.prior) ? 'prior' : null);
  const has = { current: new Set(), prior: new Set() };
  for (const r of presence) { const k = winOf(r.day); if (k) has[k].add(r.platform); }

  // totals[event][platform][window]
  const totals = {};
  const srcCur = new Map();   // "source\0campaign" -> {source, campaign, events:{}, mediums: Map}
  for (const r of rows) {
    const k = winOf(r.day);
    if (!k || !EVENTS.includes(r.event)) continue;
    const n = Number(r.n) || 0;
    const e = totals[r.event] || (totals[r.event] = {});
    const p = e[r.platform] || (e[r.platform] = { current: 0, prior: 0 });
    p[k] += n;
    if (k === 'current') {
      const key = `${r.source || ''}\u0000${r.campaign || ''}`;
      const s = srcCur.get(key) || { source: r.source || '', campaign: r.campaign || '', events: {}, mediums: new Map() };
      s.events[r.event] = (s.events[r.event] || 0) + n;
      if (r.event === 'first-visit') s.mediums.set(r.medium || '', (s.mediums.get(r.medium || '') || 0) + n);
      srcCur.set(key, s);
    }
  }

  const comp = {};
  for (const [p] of SC_PLATFORMS) comp[p] = comparability(p, v2, w);

  /** One counter for one platform: null = no data in that window. */
  const platMetric = (event, p, name) => {
    if (WEB_ONLY.has(event) && p !== 'web') return null;
    const t = (totals[event] && totals[event][p]) || { current: 0, prior: 0 };
    const current = eventsError ? null : has.current.has(p) ? t.current : null;
    const prior = eventsError ? null : has.prior.has(p) ? t.prior : null;
    let change;
    if (current == null && prior == null) change = { kind: 'no-data', text: 'no data' };
    else if (!comp[p].ok) change = { kind: 'not-comparable', since: comp[p].since, text: notComparableText(name, comp[p]) };
    else change = changeText(current, prior);
    return { current, prior, change };
  };
  /** A counter over every platform it exists on. */
  const metric = (event) => {
    const byPlatform = {};
    for (const [p, name] of SC_PLATFORMS) { const m = platMetric(event, p, name); if (m) byPlatform[p] = m; }
    const ps = Object.entries(byPlatform);
    const withCur = ps.filter(([, m]) => m.current != null);
    const withPrior = ps.filter(([, m]) => m.prior != null);
    const current = withCur.length ? withCur.reduce((a, [, m]) => a + m.current, 0) : null;
    const prior = withPrior.length ? withPrior.reduce((a, [, m]) => a + m.prior, 0) : null;
    // A total is comparable only if every platform with data in either week is.
    const involved = ps.filter(([, m]) => m.current != null || m.prior != null);
    const blocking = involved.filter(([, m]) => m.change.kind === 'not-comparable');
    let change;
    if (current == null && prior == null) change = { kind: 'no-data', text: 'no data' };
    else if (blocking.length) {
      const dated = blocking.filter(([, m]) => m.change.since).map(([, m]) => m.change.since).sort();
      const undated = blocking.filter(([, m]) => !m.change.since).map(([p]) => SC_PLATFORMS.find(([q]) => q === p)[1]);
      change = { kind: 'not-comparable', since: dated.length ? dated[dated.length - 1] : null,
        text: dated.length ? `not comparable before ${scDay(dated[dated.length - 1])}`
          : `not comparable yet (${undated.join(' and ')} update pending)` };
    } else if (involved.some(([, m]) => m.current == null || m.prior == null)) {
      change = { kind: 'no-data', text: 'no data for one of the weeks' };
    } else change = changeText(current, prior);
    return { current, prior, change, byPlatform };
  };

  const visitors = metric('first-visit');
  const perDay = (n) => (n == null ? null : Math.round((n / 7) * 10) / 10);
  visitors.perDay = perDay(visitors.current);
  visitors.priorPerDay = perDay(visitors.prior);
  for (const m of Object.values(visitors.byPlatform)) { m.perDay = perDay(m.current); m.priorPerDay = perDay(m.prior); }

  // By link (this week's first visits): tagged source / campaign, then "no tag".
  const label = (s) => (s.source ? (s.campaign ? `${s.source} / ${s.campaign}` : s.source) : 'no tag');
  const allSrc = [...srcCur.values()];
  const visitSrc = allSrc.filter((s) => (s.events['first-visit'] || 0) > 0)
    .sort((a, b) => b.events['first-visit'] - a.events['first-visit'] || label(a).localeCompare(label(b)));
  const tagged = visitSrc.filter((s) => s.source);
  const noTag = visitors.current == null ? null : ((visitSrc.find((s) => !s.source) || { events: {} }).events['first-visit'] || 0);
  const bySource = tagged.slice(0, TOP_SOURCES).map((s) => ({ source: s.source, campaign: s.campaign, label: label(s), visits: s.events['first-visit'] }));
  const otherTagged = tagged.slice(TOP_SOURCES).reduce((a, s) => a + s.events['first-visit'], 0);

  // One row per tagged link with anything this week.
  const sourceRows = allSrc.filter((s) => s.source)
    .map((s) => ({
      source: s.source, campaign: s.campaign, label: label(s),
      visits: s.events['first-visit'] || 0, watches: s.events['watch-created'] || 0,
      emails: s.events['email-submitted'] || 0, checkouts: s.events['checkout-start'] || 0, pro: s.events['pro-converted'] || 0,
      visitsByMedium: [...s.mediums].filter(([, n]) => n > 0).map(([medium, n]) => ({ medium, n }))
        .sort((a, b) => b.n - a.n || a.medium.localeCompare(b.medium)),
    }))
    .sort((a, b) => b.visits - a.visits || b.watches - a.watches || a.label.localeCompare(b.label))
    .slice(0, TOP_SOURCE_ROWS);

  const watches = metric('watch-created');
  const emails = { asked: metric('email-asked'), submitted: metric('email-submitted'), confirmed: metric('email-confirmed') };
  const opens = metric('paywall'), checkouts = metric('checkout-start'), pro = metric('pro-converted');
  const proSheet = { opens, checkouts, pro, rate: { num: checkouts.current, den: opens.current, text: rateText(checkouts.current, opens.current) } };

  const subscribers = subscriberChange(today, subs, history, { storingToday });

  // Which platforms' weeks include days before the fixed counting (for one plain note).
  const counting = SC_PLATFORMS.map(([p, name]) => ({ platform: p, name, since: comp[p].since, comparable: comp[p].ok }));

  return {
    window: w, eventsError, counting,
    visitors: { ...visitors, bySource, otherTagged, noTag },
    watches, emails, proSheet, subscribers, sourceRows,
  };
}

/** Today's paying total from the live counts + the change from the snapshot
 * stored 7 days ago (exactly that day; no nearest-day guessing). */
export function subscriberChange(today, subs, history, { storingToday = true } = {}) {
  if (!subs || subs.error) return { now: null, error: (subs && subs.error) || 'not loaded', change: { kind: 'no-data', text: 'no data' } };
  const now = snapshotOf(subs);
  const days = (history && history.days) || {};
  const stored = Object.keys(days).filter((d) => d < today).sort();
  const weekAgo = addDays(today, -7);
  const first = stored[0] || today;
  let change;
  if (!stored.length && !storingToday) change = { kind: 'tracking', since: null, text: 'change: tracking starts with the next daily email' };
  else if (!stored.length || first > weekAgo) change = { kind: 'tracking', since: first, text: `change: tracking starts ${scDay(first)}` };
  else if (!days[weekAgo]) change = { kind: 'no-data', text: `change: no count stored for ${scDay(weekAgo)}` };
  else if (!days[weekAgo].complete || !now.complete) change = { kind: 'no-data', text: 'change: a store count is missing on one of the days' };
  else {
    const d = now.total - days[weekAgo].total;
    change = { kind: 'delta', delta: d, was: days[weekAgo].total,
      text: `${d > 0 ? '+' : ''}${fmt(d)} since ${scDay(weekAgo)} (was ${fmt(days[weekAgo].total)})` };
  }
  return { now, weekAgoDay: weekAgo, change };
}

/** The numbers worth keeping from loadSubscribers' output (counts only). */
export function snapshotOf(subs) {
  const num = (v) => (Number.isFinite(v) ? v : null);
  const apple = num(subs.apple), google = num(subs.google), web = num(subs.web);
  const complete = apple != null && google != null && web != null;
  return { apple, google, web, total: (apple || 0) + (google || 0) + (web || 0), complete };
}

/** loadSubscribers (ops_monitor.js) record -> {apple, google, web}. */
export function subsFromLoaded(sb) {
  if (!sb || sb.error) return { error: (sb && sb.error) || 'not loaded' };
  const st = (k) => (sb.stores && sb.stores[k] && Number.isFinite(sb.stores[k].active) ? sb.stores[k].active : null);
  return { apple: st('apple'), google: st('google'), web: Number.isFinite(sb.stripe) ? sb.stripe : null };
}

/* ===== reads and the one write ===== */

export const FUNNEL_V2_SINCE_SQL = `SELECT platform, MIN(day) AS since FROM events_daily WHERE event = '${FUNNEL_V2_MARK}' GROUP BY platform`;

export async function loadScorecardEvents(env, today) {
  const w = scorecardWindows(today);
  const [rows, presence, v2Rows] = (await env.DB.batch([
    env.DB.prepare(
      `SELECT day, event, source, campaign, medium, platform, SUM(n) AS n FROM events_daily
        WHERE day >= ?1 AND day <= ?2 AND event IN (${EVENTS.map((e) => `'${e}'`).join(', ')})
        GROUP BY day, event, source, campaign, medium, platform`
    ).bind(w.prior.from, w.current.to),
    env.DB.prepare(
      `SELECT day, platform FROM events_daily WHERE day >= ?1 AND day <= ?2 GROUP BY day, platform`
    ).bind(w.prior.from, w.current.to),
    env.DB.prepare(FUNNEL_V2_SINCE_SQL),
  ])).map((r) => r.results || []);
  const v2 = {};
  for (const r of v2Rows) v2[r.platform] = r.since;
  return { rows, presence, v2 };
}

export async function loadSubsHistory(env) {
  try {
    const h = env.ENTITLEMENTS ? JSON.parse(await env.ENTITLEMENTS.get(SUBS_HISTORY_KEY) || 'null') : null;
    return h && typeof h.days === 'object' && h.days ? h : { days: {} };
  } catch { return { days: {} }; }
}

/** Store today's paying counts (one small KV record, last 60 days). Called
 * by the daily cron run only, never by a dry run or the admin endpoint. */
export async function storeSubsSnapshot(env, today, subs, history) {
  if (!env.ENTITLEMENTS || !subs || subs.error) return false;
  const days = { ...((history && history.days) || {}) };
  days[today] = snapshotOf(subs);
  const keepFrom = addDays(today, -SUBS_HISTORY_KEEP_DAYS);
  for (const d of Object.keys(days)) if (d < keepFrom) delete days[d];
  try { await env.ENTITLEMENTS.put(SUBS_HISTORY_KEY, JSON.stringify({ days })); return true; } catch (e) {
    console.log('subs snapshot save failed:', e && e.message);
    return false;
  }
}

/** Everything the scorecard needs, read-only. `subs` comes from the caller's
 * loadSubscribers so the daily email lists entitlements once. */
export async function buildScorecard(env, { today, subs, storingToday = false }) {
  let ev = { rows: [], presence: [], v2: {} }, eventsError = null;
  try { ev = await loadScorecardEvents(env, today); } catch (e) { eventsError = String((e && e.message) || e).slice(0, 200); }
  const history = await loadSubsHistory(env);
  return { card: computeScorecard({ today, ...ev, subs, history, eventsError, storingToday }), history };
}

/* ===== rendering (plain words; no counter names) ===== */

const nd = (v, f = fmt) => (v == null ? 'no data' : f(v));
const perDayText = (v) => (v == null ? 'no data' : v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }));

function rangeText(w) {
  const r = (x) => `${scDay(x.from)}–${scDay(x.to)}`;
  return `${r(w.current)}, compared with ${r(w.prior)}`;
}
function sourcesText(v) {
  if (v.current == null) return 'no data';
  const bits = v.bySource.map((s) => `${s.label} ${fmt(s.visits)}`);
  if (v.otherTagged) bits.push(`other links ${fmt(v.otherTagged)}`);
  bits.push(`no tag ${fmt(v.noTag)}`);
  return bits.join(' · ');
}
/** "Web 7, 7 vs 5 the week before": one platform's count and its change
 * (or why there is none). A platform with nothing reported is "no data". */
function platformText(m, name, fmtCur = (x) => nd(x.current)) {
  if (m.current == null && m.prior == null) return `${name}: no data`;
  return `${name}: ${fmtCur(m)}, ${m.change.text}`;
}
function platformLines(m, fmtCur) {
  return SC_PLATFORMS.filter(([p]) => m.byPlatform[p]).map(([p, name]) => platformText(m.byPlatform[p], name, fmtCur));
}
/** All platforms on one line: "Web 7 (7 vs 5 the week before) · iPhone app no data". */
function platformsCompact(m) {
  return SC_PLATFORMS.filter(([p]) => m.byPlatform[p]).map(([p, name]) => {
    const x = m.byPlatform[p];
    if (x.current == null && x.prior == null) return `${name} no data`;
    const ch = x.change.kind === 'not-comparable' ? x.change.text.replace(/ \(.*\)$/, '') : x.change.text;
    return `${name} ${nd(x.current)} (${ch})`;
  }).join(' · ');
}
function sourceRowText(s) {
  const pl = (n, one, many) => `${fmt(n)} ${n === 1 ? one : many}`;
  const med = s.visitsByMedium.filter((x) => x.medium);
  const medTxt = med.length > 1 || (med.length === 1 && s.visitsByMedium.length > 1)
    ? ` (${s.visitsByMedium.map((x) => `${x.medium || 'untagged'} ${fmt(x.n)}`).join(', ')})` : '';
  return `${s.label}: ${pl(s.visits, 'visit', 'visits')}${medTxt} → ${pl(s.watches, 'watch', 'watches')} → ${pl(s.emails, 'email', 'emails')}`
    + ` → ${pl(s.checkouts, 'checkout', 'checkouts')} → ${fmt(s.pro)} Pro`;
}
function countingNote(card) {
  const late = card.counting.filter((c) => !c.comparable);
  if (!late.length) return '';
  const dated = late.filter((c) => c.since).map((c) => `${c.name} ${scDay(c.since)}`);
  const undated = late.filter((c) => !c.since).map((c) => c.name);
  const bits = [];
  if (dated.length) bits.push(`counting was fixed on: ${dated.join(', ')}`);
  if (undated.length) bits.push(`not yet for the ${undated.join(' and ')} (they report again after the next store release)`);
  return `Week-on-week changes start once both weeks are on the fixed counting; ${bits.join('; ')}.`;
}

/** Five numbered items + the per-link lines, as {title, value, lines[]} for both renderers. */
export function scorecardItems(card) {
  if (card.eventsError) {
    return { range: rangeText(card.window), items: [{ title: 'Weekly numbers', value: 'no data', lines: [`could not read the counters (${card.eventsError})`] }], links: [], note: '' };
  }
  const v = card.visitors;
  const items = [];
  items.push({
    title: 'New visitors a day', value: perDayText(v.perDay),
    lines: [
      `${nd(v.current)} this week, all platforms · ${v.change.text}`,
      ...platformLines(v, (m) => `${perDayText(m.perDay)} a day`),
      `From: ${sourcesText(v)}`,
    ],
  });
  const w = card.watches;
  items.push({ title: 'Watches created', value: nd(w.current),
    lines: [`all platforms: ${w.change.text}`, platformsCompact(w)] });
  const e = card.emails;
  items.push({ title: 'Monday email sign-ups (website)', value: nd(e.submitted.current),
    lines: [`offered ${nd(e.asked.current)} → gave an address ${nd(e.submitted.current)} → confirmed ${nd(e.confirmed.current)}`,
      `addresses given: ${e.submitted.change.text}`] });
  const ps = card.proSheet;
  items.push({ title: 'Pro sheet to checkout', value: ps.rate.text == null ? 'no data' : ps.rate.text,
    lines: [`opened ${nd(ps.opens.current)} → checkout ${nd(ps.checkouts.current)} → bought Pro ${nd(ps.pro.current)}`,
      `checkouts, all platforms: ${ps.checkouts.change.text}`, `checkouts: ${platformsCompact(ps.checkouts)}`] });
  const s = card.subscribers;
  if (!s.now) items.push({ title: 'Paying subscribers', value: 'no data', lines: [`could not load (${s.error})`] });
  else {
    items.push({ title: 'Paying subscribers', value: `${s.now.complete ? '' : 'at least '}${fmt(s.now.total)}`,
      lines: [`App Store ${nd(s.now.apple)} · Google Play ${nd(s.now.google)} · Web ${nd(s.now.web)}`, s.change.text] });
  }
  // A number nobody reported in either week gets one short line, not a column of "no data".
  const empty = [v, w, e.submitted, ps.opens];
  empty.forEach((m, i) => {
    if (m.current == null && m.prior == null && (i !== 2 || (e.asked.current == null && e.confirmed.current == null))) items[i].lines = ['nothing reported in either week'];
  });
  return { range: rangeText(card.window), items, links: card.sourceRows.map(sourceRowText), note: countingNote(card) };
}

export function scorecardTextLines(card) {
  const sc = scorecardItems(card);
  const L = [`WEEKLY SCORECARD (${sc.range})`];
  sc.items.forEach((it, i) => {
    L.push(`  ${i + 1}. ${it.title}: ${it.value}`);
    for (const l of it.lines) if (l) L.push(`     ${l}`);
  });
  L.push('  What each tagged link did this week:');
  if (sc.links.length) for (const l of sc.links) L.push(`     ${l}`);
  else L.push('     no tagged visits this week (add ?utm_source=… to links you post)');
  if (sc.note) L.push(`  ${sc.note}`);
  L.push('  Small numbers (under 20) are shown as counts, not percentages. "no data" means nothing was reported, not zero.');
  return L;
}

export function scorecardHtml(card, { esc, C }) {
  const sc = scorecardItems(card);
  const rows = sc.items.map((it, i) => `<tr><td style="padding:10px 0;border-bottom:1px solid ${C.line};vertical-align:top;">
      <div style="font-size:13px;color:${C.dim};"><span style="display:inline-block;min-width:16px;font-weight:700;color:${C.accent};">${i + 1}</span>${esc(it.title)}</div>
      <div style="font-size:22px;font-weight:800;color:${C.ink};margin:2px 0 2px 16px;">${esc(it.value)}</div>
      ${it.lines.filter(Boolean).map((l) => `<div style="font-size:13px;line-height:1.45;color:${C.ink};margin-left:16px;">${esc(l)}</div>`).join('')}
    </td></tr>`).join('');
  const links = sc.links.length
    ? sc.links.map((l) => { const i = l.indexOf(': '); return `<div style="font-size:13px;line-height:1.5;margin:3px 0;"><strong>${esc(l.slice(0, i + 1))}</strong>${esc(l.slice(i + 1))}</div>`; }).join('')
    : `<div style="font-size:13px;color:${C.dim};">No tagged visits this week (add ?utm_source=… to links you post).</div>`;
  return `<tr><td style="padding:18px 22px 4px;">
    <div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:${C.accent};margin:0 0 2px;">Weekly scorecard</div>
    <div style="font-size:13px;color:${C.dim};margin:0 0 4px;">${esc(sc.range)}</div>
    <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;">${rows}</table>
    <div style="font-size:13px;font-weight:700;color:${C.ink};margin:12px 0 4px;">What each tagged link did this week</div>
    ${links}
    <div style="font-size:12px;line-height:1.5;color:${C.dim};margin-top:10px;">${sc.note ? esc(sc.note) + '<br>' : ''}Small numbers (under 20) are shown as counts, not percentages. &ldquo;No data&rdquo; means nothing was reported, not zero.</div>
  </td></tr>`;
}
