/* UTM attribution — which channel actually produces searches, watches and
 * Pro, so the owner only spends on channels that convert.
 *
 *   POST /v1/events              {e, src, cmp, med, p}  → +1 on a daily counter
 *   GET  /v1/admin/attribution   ?days=30               → per-source funnel
 *
 * Deliberately coarse: no ids, no IPs, no timestamps finer than a day. The
 * client sends a source only when it arrived through a utm_source link (web)
 * or remembered one from a prior web visit; everything else counts under the
 * empty source so totals still add up. */
import { json, err } from './util.js';

const EVENT_RE = /^[a-z0-9][a-z0-9/_-]{0,47}$/;
const clip = (v, n) => String(v == null ? '' : v).trim().toLowerCase().slice(0, n).replace(/[^a-z0-9._-]/g, '');

export async function handleEvent(req, env) {
  let body;
  // Sent as text/plain so the browser's sendBeacon needs no CORS preflight.
  try { body = JSON.parse(await req.text()); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  if (!body || typeof body !== 'object') return err(400, 'bad_json', 'Body must be JSON.');
  const event = String(body.e || '').trim().toLowerCase();
  if (!EVENT_RE.test(event)) return err(400, 'bad_event', 'Unknown event name.');
  const source = clip(body.src, 40), campaign = clip(body.cmp, 60), medium = clip(body.med, 30);
  const platform = ['web', 'ios', 'android'].includes(body.p) ? body.p : 'web';
  const day = new Date().toISOString().slice(0, 10);
  await env.DB.prepare(
    `INSERT INTO events_daily (day, event, source, campaign, medium, platform, n)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, 1)
     ON CONFLICT(day, event, source, campaign, medium, platform) DO UPDATE SET n = n + 1`
  ).bind(day, event, source, campaign, medium, platform).run();
  return json({ ok: true });
}

export async function handleAttribution(req, env) {
  const q = new URL(req.url).searchParams;
  let days = parseInt(q.get('days') || '30', 10);
  if (!Number.isFinite(days) || days < 1) days = 30;
  days = Math.min(days, 365);
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const { results } = await env.DB.prepare(
    `SELECT source, campaign, medium, platform, event, SUM(n) AS n
       FROM events_daily WHERE day >= ?1
      GROUP BY source, campaign, medium, platform, event
      ORDER BY source, campaign, medium, platform, event`
  ).bind(since).all();
  // Pivot: one row per channel with the funnel events as columns.
  const rows = new Map();
  for (const r of results || []) {
    const key = [r.source, r.campaign, r.medium, r.platform].join('|');
    if (!rows.has(key)) rows.set(key, { source: r.source, campaign: r.campaign, medium: r.medium, platform: r.platform, events: {} });
    rows.get(key).events[r.event] = r.n;
  }
  const FUNNEL = ['first-visit', 'zip-entered', 'part-first-search', 'watch-created', 'push-enabled', 'checkout-start', 'pro-converted'];
  return json({ since, days, funnel: FUNNEL, channels: [...rows.values()] });
}
