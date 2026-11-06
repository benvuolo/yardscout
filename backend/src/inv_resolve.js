/* Current-inventory lookup by scraper id or VIN, the way handleVehicleDetail
 * resolves a deep link: vindex bucket shard → ONE yard shard, both memoized
 * per run and the yard-shard parses budgeted. Shared by saved-car alerts
 * (saved_alerts.js) and the free weekly recap's "already gone" line
 * (alerts.js sendWeeklyDigests). */

import { gunzipToText, vindexBucket } from './util.js';

const MAX_YARD_PARSES = 40;        // largest shard ≈ 300KB / 2-3ms each

/* ----- shard resolver (memoized per run, budgeted) ----- */

export function makeResolver(env, dir, { maxYardParses = MAX_YARD_PARSES } = {}) {
  const mod = dir.vindexMod || 64;
  const buckets = new Map();   // bucket → index object | null
  const shards = new Map();    // yardIdx → parsed shard | null
  let yardParses = 0;
  const f = dir.fields || [];
  const iId = f.indexOf('id'), iVin = f.indexOf('vin'), iDate = f.indexOf('dateAdded');

  async function loadBucket(b) {
    if (buckets.has(b)) return buckets.get(b);
    const row = await env.DB.prepare(
      'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
    ).bind('vindex', String(b), 'all').first();
    const idx = row ? JSON.parse(await gunzipToText(row.body)) : null;
    buckets.set(b, idx);
    return idx;
  }
  async function loadShard(yardIdx) {
    if (shards.has(yardIdx)) return shards.get(yardIdx);
    if (yardParses >= maxYardParses) return undefined;   // budget — defer
    yardParses++;
    const row = await env.DB.prepare(
      'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
    ).bind('yard', String(yardIdx), 'free').first();   // vpic/dates identical across variants
    const shard = row ? JSON.parse(await gunzipToText(row.body)) : null;
    shards.set(yardIdx, shard);
    return shard;
  }

  /** → {state:'gone'} | {state:'present', id, yardIdx, dateAdded} | {state:'deferred'} */
  return async function resolve(key) {
    const idx = await loadBucket(vindexBucket(key, mod));
    const hit = idx && idx[key];
    if (!hit) return { state: 'gone' };
    const [yardIdx, id] = hit;
    const shard = await loadShard(yardIdx);
    if (shard === undefined) return { state: 'deferred' };
    const row = shard && shard.vehicles.find((r) => String(r[iId]) === String(id) || String(r[iVin]) === key);
    if (!row) return { state: 'gone' };
    return { state: 'present', id: row[iId], yardIdx, dateAdded: row[iDate] };
  };
}
