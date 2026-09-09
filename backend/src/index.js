/* YardScout API — Cloudflare Worker entry point / router.
 *
 * Public (tier-aware where noted):
 *   GET  /v1/health
 *   GET  /v1/yards
 *   GET  /v1/inventory?lat&lng&radius        (tier-aware plan)
 *   GET  /v1/inventory/partsets              (tier-aware)
 *   GET  /v1/inventory/shard/:yardId         (tier-aware)
 *   GET  /v1/vehicles/:idOrVin               (tier-aware)
 *   POST /v1/auth/request-link
 *   GET  /v1/auth/callback?token=
 *   GET  /v1/me                              (session required)
 *   POST /v1/auth/logout
 * Secret-protected:
 *   GET  /v1/admin/inventory/manifest             x-upload-token
 *   PUT  /v1/admin/inventory/shard/:kind/:key/:variant  x-upload-token
 *   POST /v1/admin/inventory/commit               x-upload-token
 *   POST /v1/admin/grant                          x-admin-secret
 *   GET  /v1/admin/users                          x-admin-secret
 *   POST /v1/iap/revenuecat                       RevenueCat webhook auth
 */

import { json, err, corsHeaders, rateLimit, clientIp } from './util.js';
import {
  handleRequestLink, handleCallback, handleMe, handleLogout, getSessionUser,
} from './auth.js';
import {
  handleYards, handleInventoryPlan, handlePartSets, handleYardShard, handleVehicleDetail,
} from './inventory.js';
import {
  requireUpload, requireAdmin, handleManifest, handlePutShard, handleCommit,
  handleGrant, handleListUsers, handleRevenueCatWebhook,
} from './admin.js';

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const cors = corsHeaders(env, req.headers.get('origin'));
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    let resp;
    try {
      resp = await route(req, env, url);
    } catch (e) {
      console.log('unhandled error:', e && (e.stack || e.message || e));
      resp = err(500, 'internal', 'Internal error.');
    }
    // All handlers build their own Response objects, so headers are mutable.
    for (const [k, v] of Object.entries(cors)) resp.headers.set(k, v);
    return resp;
  },
};

async function route(req, env, url) {
  const path = url.pathname.replace(/\/+$/, '') || '/';
  const method = req.method;
  const ip = clientIp(req);

  // Blanket per-IP limit on everything public; admin/upload paths have their
  // own secrets and the scan workflow bursts ~300 PUTs per run.
  const isAdminPath = path.startsWith('/v1/admin/') || path === '/v1/iap/revenuecat';
  if (!isAdminPath && !rateLimit('ip:' + ip, 300, 60_000)) {
    return err(429, 'rate_limited', 'Slow down.');
  }

  if (method === 'GET' && path === '/v1/health') {
    return json({ ok: true, service: 'yardscout-api', at: new Date().toISOString() });
  }

  /* ----- auth ----- */
  if (method === 'POST' && path === '/v1/auth/request-link') {
    if (!rateLimit('link2:ip:' + ip, 20, 60_000)) return err(429, 'rate_limited', 'Slow down.');
    return handleRequestLink(req, env);
  }
  if (method === 'GET' && path === '/v1/auth/callback') return handleCallback(req, env);
  if (method === 'GET' && path === '/v1/me') return handleMe(req, env);
  if (method === 'POST' && path === '/v1/auth/logout') return handleLogout(req, env);

  /* ----- inventory (tier-aware: anonymous OK, session upgrades the variant) ----- */
  if (method === 'GET' && path.startsWith('/v1/')) {
    const user = ['/v1/yards', '/v1/inventory', '/v1/vehicles'].some(
      (p) => path === p || path.startsWith(p + '/')
    ) ? await getSessionUser(req, env) : null;

    if (path === '/v1/yards') return handleYards(req, env);
    if (path === '/v1/inventory') return handleInventoryPlan(req, env, user);
    if (path === '/v1/inventory/partsets') return handlePartSets(req, env, user);
    let m = path.match(/^\/v1\/inventory\/shard\/([^/]+)$/);
    if (m) return handleYardShard(req, env, user, decodeURIComponent(m[1]));
    m = path.match(/^\/v1\/vehicles\/([^/]+)$/);
    if (m) return handleVehicleDetail(req, env, user, decodeURIComponent(m[1]));
  }

  /* ----- ingestion (x-upload-token) ----- */
  if (path.startsWith('/v1/admin/inventory/')) {
    const denied = await requireUpload(req, env);
    if (denied) return denied;
    if (method === 'GET' && path === '/v1/admin/inventory/manifest') return handleManifest(req, env);
    const m = path.match(/^\/v1\/admin\/inventory\/shard\/([^/]+)\/([^/]+)\/([^/]+)$/);
    if (method === 'PUT' && m) {
      return handlePutShard(req, env, decodeURIComponent(m[1]), decodeURIComponent(m[2]), decodeURIComponent(m[3]));
    }
    if (method === 'POST' && path === '/v1/admin/inventory/commit') return handleCommit(req, env);
  }

  /* ----- admin (x-admin-secret) ----- */
  if (path === '/v1/admin/grant' || path === '/v1/admin/users') {
    const denied = await requireAdmin(req, env);
    if (denied) return denied;
    if (method === 'POST' && path === '/v1/admin/grant') return handleGrant(req, env);
    if (method === 'GET' && path === '/v1/admin/users') return handleListUsers(req, env);
  }

  /* ----- IAP webhook (own auth) ----- */
  if (method === 'POST' && path === '/v1/iap/revenuecat') return handleRevenueCatWebhook(req, env);

  return err(404, 'not_found', 'No such endpoint.');
}
