/* Inventory read API.
 *
 * Design constraint: the Workers free plan allows ~10ms CPU per request, so
 * this code never parses or transforms the (22MB raw) inventory. The GitHub
 * Action pre-computes per-yard shards in TWO variants:
 *   free — part names only; dollar values (maxValue, low/high/cost) stripped
 *   pro  — everything the scraper produced
 * and uploads them gzipped. The Worker's job is: pick yards within the radius
 * (small directory parse, cached in the isolate), then stream stored gzip
 * blobs back with ETags. Tier enforcement = which variant row is SELECTed;
 * there is no code path that can leak pro fields to a free session.
 *
 * Endpoints:
 *   GET /v1/yards                       yard directory (public — no value data)
 *   GET /v1/inventory?lat&lng&radius    query "plan": yards in radius + shard paths
 *   GET /v1/inventory/partsets          tier-variant partSets lookup table
 *   GET /v1/inventory/shard/:yardId     tier-variant vehicles for one yard
 *   GET /v1/vehicles/:idOrVin           single-vehicle detail (deep links)
 */

import { json, err, gunzipToText, haversineMiles, vindexBucket } from './util.js';
import { resolveTier, variantFor } from './auth.js';

const DEFAULT_RADIUS_MI = 100;
const MAX_RADIUS_MI = 30000; // "no limit" — the whole planet is smaller

let dirCache = { at: 0, data: null };

export async function getDirectory(env) {
  if (dirCache.data && Date.now() - dirCache.at < 30_000) return dirCache.data;
  const row = await env.DB.prepare('SELECT directory FROM inv_meta WHERE id = 1').first();
  if (!row) return null;
  dirCache = { at: Date.now(), data: JSON.parse(row.directory) };
  return dirCache.data;
}

export async function handleYards(req, env) {
  const dir = await getDirectory(env);
  if (!dir) return err(503, 'no_inventory', 'No inventory has been uploaded yet.');
  return json({
    schemaVersion: dir.schemaVersion,
    scrapedAt: dir.scrapedAt,
    yardFields: dir.yardFields,
    yards: dir.yards,
    counts: dir.counts,
  }, { headers: { 'cache-control': 'public, max-age=300' } });
}

export async function handleInventoryPlan(req, env, user) {
  const dir = await getDirectory(env);
  if (!dir) return err(503, 'no_inventory', 'No inventory has been uploaded yet.');

  const q = new URL(req.url).searchParams;
  const lat = parseFloat(q.get('lat'));
  const lng = parseFloat(q.get('lng'));
  let radius = parseFloat(q.get('radius'));
  if (!Number.isFinite(radius) || radius <= 0) radius = DEFAULT_RADIUS_MI;
  radius = Math.min(radius, MAX_RADIUS_MI);

  const hasCenter = Number.isFinite(lat) && Number.isFinite(lng)
    && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;

  const yardIds = [];
  for (let i = 0; i < dir.yards.length; i++) {
    const y = dir.yards[i]; // [location, city, state, lat, lng, ...]
    if (!hasCenter || haversineMiles(lat, lng, y[3], y[4]) <= radius) yardIds.push(i);
  }

  const tier = resolveTier(user);
  // The ?v= param is ignored server-side (the session decides the variant) but
  // keys the browser HTTP cache, so an upgrade mid-session can't be served a
  // stale free-variant shard for the cache TTL.
  const v = '?v=' + variantFor(tier);
  return json({
    schemaVersion: dir.schemaVersion,
    scrapedAt: dir.scrapedAt,
    pricesLastReviewed: dir.pricesLastReviewed,
    tier,
    fields: dir.fields,
    yardFields: dir.yardFields,
    yards: dir.yards,           // full directory — the client indexes into it
    yardIds,                    // yards within the requested radius
    center: hasCenter ? { lat, lng, radius } : null,
    partSetsPath: '/v1/inventory/partsets' + v,
    shardPathTemplate: '/v1/inventory/shard/{yardId}' + v,
    counts: dir.counts,
  }, { headers: { 'cache-control': 'no-store' } });
}

/** Serve a stored gzip blob without re-encoding. ETag = sha256 of the
 * uncompressed JSON (computed by the push script), which differs per variant,
 * so free/pro responses can never collide in a cache. */
async function serveShard(req, env, kind, key, variant, cacheSeconds) {
  const row = await env.DB.prepare(
    'SELECT sha256, body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
  ).bind(kind, String(key), variant).first();
  if (!row) return err(404, 'not_found', 'No such inventory shard.');

  const etag = `"${row.sha256}"`;
  const baseHeaders = {
    etag,
    // Tier-dependent body behind one URL → caches must key on Authorization.
    vary: 'authorization, accept-encoding',
    'cache-control': `public, max-age=${cacheSeconds}`,
  };
  if ((req.headers.get('if-none-match') || '') === etag) {
    return new Response(null, { status: 304, headers: baseHeaders });
  }
  // D1 returns BLOB columns as a plain number array — normalize to bytes.
  const body = row.body instanceof ArrayBuffer || ArrayBuffer.isView(row.body)
    ? row.body
    : new Uint8Array(row.body);
  const headers = { ...baseHeaders, 'content-type': 'application/json; charset=utf-8' };
  if (/gzip/i.test(req.headers.get('accept-encoding') || '')) {
    return new Response(body, {
      status: 200,
      headers: { ...headers, 'content-encoding': 'gzip' },
      encodeBody: 'manual', // body is already gzip — do not double-compress
    });
  }
  return new Response(await gunzipToText(body), { status: 200, headers });
}

export async function handlePartSets(req, env, user) {
  return serveShard(req, env, 'partsets', 'all', variantFor(resolveTier(user)), 300);
}

export async function handleYardShard(req, env, user, yardId) {
  if (!/^\d{1,4}$/.test(yardId)) return err(400, 'bad_yard', 'yardId must be a yard index.');
  return serveShard(req, env, 'yard', yardId, variantFor(resolveTier(user)), 300);
}

/** Vehicle detail by scraper id or VIN — powers #car= deep links without the
 * client holding the full dataset. Resolves the yard via the small vindex
 * shard, then parses ONE yard shard (largest ≈ 300KB, ~2-3ms). */
export async function handleVehicleDetail(req, env, user, token) {
  const dir = await getDirectory(env);
  if (!dir) return err(503, 'no_inventory', 'No inventory has been uploaded yet.');
  if (!token || token.length > 32) return err(400, 'bad_id', 'Pass a vehicle id or VIN.');
  if (/[a-z]/.test(token)) token = token.toUpperCase(); // VINs are stored uppercase; ids are digits

  const mod = dir.vindexMod || 64;
  const bucketRow = await env.DB.prepare(
    'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
  ).bind('vindex', String(vindexBucket(token, mod)), 'all').first();
  if (!bucketRow) return err(404, 'not_found', 'Vehicle not found in the current inventory.');

  const index = JSON.parse(await gunzipToText(bucketRow.body));
  const hit = index[token];
  if (!hit) return err(404, 'not_found', 'Vehicle not found in the current inventory.');
  const [yardIdx, id] = hit;

  const tier = resolveTier(user);
  const shardRow = await env.DB.prepare(
    'SELECT body FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3'
  ).bind('yard', String(yardIdx), variantFor(tier)).first();
  if (!shardRow) return err(404, 'not_found', 'Vehicle not found in the current inventory.');

  const shard = JSON.parse(await gunzipToText(shardRow.body));
  const f = dir.fields; // [id, vin, year, make, model, row, dateAdded, yard, partSet, maxValue, premium]
  const row = shard.vehicles.find((r) => String(r[0]) === String(id) || String(r[1]) === token);
  if (!row) return err(404, 'not_found', 'Vehicle not found in the current inventory.');

  const vehicle = {};
  f.forEach((name, i) => { vehicle[name] = row[i]; });
  const y = dir.yards[yardIdx] || [];
  return json({
    scrapedAt: dir.scrapedAt,
    tier,
    vehicle,
    vpic: shard.vpic?.[String(row[0])] || null,
    yard: { id: yardIdx, location: y[0], city: y[1], state: y[2], lat: y[3], lng: y[4] },
    // Client resolves part names/values via /v1/inventory/partsets (cacheable)
    partSetIndex: row[f.indexOf('partSet')],
  }, { headers: { vary: 'authorization' } });
}
