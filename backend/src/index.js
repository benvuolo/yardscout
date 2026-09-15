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
 *   POST /v1/admin/digest/run                     x-admin-secret (manual weekly-digest trigger)
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
  handleWaitlistJoin, handleWaitlistList,
} from './admin.js';
import { handleCheckout, handlePortal, handleStripeWebhook } from './billing.js';
import {
  handleWatchesList, handleWatchCreate, handleWatchDelete,
  handleVapidKey, handlePushSubscribe, handlePushUnsubscribe, handlePushTest,
  sendWeeklyDigests,
} from './alerts.js';

export default {
  /* Cron (wrangler.toml [triggers]): weekly digest email for free users
   * whose watches matched arrivals this week. Pro users hear instantly via
   * dispatchAlerts on each inventory commit and are skipped here. */
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      sendWeeklyDigests(env)
        .then((r) => console.log(`weekly digest: ${r.users} users, ${r.emails} emails, ${r.arrivals} arrivals in window`))
        .catch((e) => console.log('weekly digest failed:', e && (e.stack || e.message)))
    );
  },

  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const cors = corsHeaders(env, req.headers.get('origin'));
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    let resp;
    try {
      resp = await route(req, env, url, ctx);
    } catch (e) {
      console.log('unhandled error:', e && (e.stack || e.message || e));
      resp = err(500, 'internal', 'Internal error.');
    }
    // All handlers build their own Response objects, so headers are mutable.
    for (const [k, v] of Object.entries(cors)) resp.headers.set(k, v);
    return resp;
  },
};

async function route(req, env, url, ctx) {
  const path = url.pathname.replace(/\/+$/, '') || '/';
  const method = req.method;
  const ip = clientIp(req);

  // Blanket per-IP limit on everything public; admin/upload paths have their
  // own secrets and the scan workflow bursts ~300 PUTs per run.
  const isAdminPath = path.startsWith('/v1/admin/') || path === '/v1/iap/revenuecat'
    || path === '/v1/stripe/webhook'; // signature-verified; Stripe retries in bursts
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

  /* ----- waitlist (public join, tight rate limit) ----- */
  if (method === 'POST' && path === '/v1/waitlist') {
    if (!rateLimit('wl:ip:' + ip, 10, 3600_000)) return err(429, 'rate_limited', 'Slow down.');
    return handleWaitlistJoin(req, env);
  }

  /* ----- alerts: watches + web push (session-scoped) ----- */
  if (path === '/v1/watches' && method === 'GET') return handleWatchesList(req, env);
  if (path === '/v1/watches' && method === 'POST') return handleWatchCreate(req, env);
  let wm = path.match(/^\/v1\/watches\/([0-9a-f-]{36})$/);
  if (wm && method === 'DELETE') return handleWatchDelete(req, env, wm[1]);
  if (path === '/v1/push/vapid' && method === 'GET') return handleVapidKey(env);
  if (path === '/v1/push/subscribe' && method === 'POST') return handlePushSubscribe(req, env);
  if (path === '/v1/push/unsubscribe' && method === 'POST') return handlePushUnsubscribe(req, env);
  if (path === '/v1/push/test' && method === 'POST') return handlePushTest(req, env);

  /* ----- billing (Stripe) ----- */
  if (method === 'POST' && path === '/v1/billing/checkout') return handleCheckout(req, env);
  if (method === 'POST' && path === '/v1/billing/portal') return handlePortal(req, env);
  if (method === 'POST' && path === '/v1/stripe/webhook') return handleStripeWebhook(req, env);

  /* ----- ingestion (x-upload-token) ----- */
  if (path.startsWith('/v1/admin/inventory/')) {
    const denied = await requireUpload(req, env);
    if (denied) return denied;
    if (method === 'GET' && path === '/v1/admin/inventory/manifest') return handleManifest(req, env);
    const m = path.match(/^\/v1\/admin\/inventory\/shard\/([^/]+)\/([^/]+)\/([^/]+)$/);
    if (method === 'PUT' && m) {
      return handlePutShard(req, env, decodeURIComponent(m[1]), decodeURIComponent(m[2]), decodeURIComponent(m[3]));
    }
    if (method === 'POST' && path === '/v1/admin/inventory/commit') return handleCommit(req, env, ctx);
  }

  /* ----- admin (x-admin-secret) ----- */
  if (path === '/v1/admin/grant' || path === '/v1/admin/users' || path === '/v1/admin/waitlist'
      || path === '/v1/admin/digest/run') {
    const denied = await requireAdmin(req, env);
    if (denied) return denied;
    if (method === 'POST' && path === '/v1/admin/grant') return handleGrant(req, env);
    if (method === 'GET' && path === '/v1/admin/users') return handleListUsers(req, env);
    if (method === 'GET' && path === '/v1/admin/waitlist') return handleWaitlistList(req, env);
    // Manual digest trigger — same code path as the Monday cron. Handy for
    // ops ("did anyone match this week?") and exercised by the e2e test.
    if (method === 'POST' && path === '/v1/admin/digest/run') {
      return json(await sendWeeklyDigests(env));
    }
  }

  /* ----- IAP webhook (own auth) ----- */
  if (method === 'POST' && path === '/v1/iap/revenuecat') return handleRevenueCatWebhook(req, env);

  return err(404, 'not_found', 'No such endpoint.');
}
