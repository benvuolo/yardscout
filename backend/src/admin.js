/* Admin + ingestion endpoints. Two separate secrets on purpose:
 *   UPLOAD_TOKEN  — held by the GitHub Actions scan workflow; can only write
 *                   inventory data. Leaking it cannot touch user accounts.
 *   ADMIN_SECRET  — held by the owner only; grants tiers / lists users.
 * Both checked with constant-time comparison; endpoints return 503 when the
 * secret is unconfigured (never "open by default").
 */

import { json, err, sha256Hex, isoNow, timingSafeEqual } from './util.js';

async function checkSecret(req, env, header, envKey) {
  const expected = env[envKey];
  if (!expected) return err(503, 'not_configured', `${envKey} is not configured on the server.`);
  const got = req.headers.get(header) || '';
  if (!(await timingSafeEqual(got, expected))) return err(401, 'unauthorized', 'Bad or missing credential.');
  return null;
}

export const requireUpload = (req, env) => checkSecret(req, env, 'x-upload-token', 'UPLOAD_TOKEN');
export const requireAdmin = (req, env) => checkSecret(req, env, 'x-admin-secret', 'ADMIN_SECRET');

/* ===== Inventory ingestion (called by scraper/push_inventory.py) ===== */

const VALID_KINDS = new Set(['yard', 'partsets', 'vindex']);
const VALID_VARIANTS = new Set(['free', 'pro', 'all']);
const MAX_SHARD_BYTES = 4 * 1024 * 1024; // gzipped; largest real shard ≈ 60KB

/** Current manifest — lets the push script upload only changed shards. */
export async function handleManifest(req, env) {
  const meta = await env.DB.prepare('SELECT manifest, updated_at FROM inv_meta WHERE id = 1').first();
  return json({
    manifest: meta ? JSON.parse(meta.manifest) : {},
    updatedAt: meta?.updated_at || null,
  });
}

export async function handlePutShard(req, env, kind, key, variant) {
  if (!VALID_KINDS.has(kind) || !VALID_VARIANTS.has(variant) || !/^[a-zA-Z0-9_-]{1,16}$/.test(key)) {
    return err(400, 'bad_shard_ref', 'Invalid kind/key/variant.');
  }
  const body = await req.arrayBuffer();
  if (body.byteLength < 10 || body.byteLength > MAX_SHARD_BYTES) {
    return err(400, 'bad_size', 'Shard body missing or too large.');
  }
  const head = new Uint8Array(body, 0, 2);
  if (head[0] !== 0x1f || head[1] !== 0x8b) {
    return err(400, 'not_gzip', 'Shard body must be gzip-compressed JSON.');
  }
  // sha256 of the UNcompressed content, computed by the pusher; used as the
  // ETag and for change detection. The pusher owns data integrity (it is the
  // only holder of UPLOAD_TOKEN), so we store the claimed hash as-is rather
  // than spend CPU decompressing to re-verify.
  const sha = req.headers.get('x-content-sha256') || '';
  if (!/^[0-9a-f]{64}$/.test(sha)) return err(400, 'bad_sha', 'x-content-sha256 header required (hex sha256 of the uncompressed JSON).');

  await env.DB.prepare(
    `INSERT INTO inv_shards (kind, key, variant, sha256, body, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6)
     ON CONFLICT (kind, key, variant) DO UPDATE
       SET sha256 = ?4, body = ?5, updated_at = ?6`
  ).bind(kind, key, variant, sha, body, isoNow()).run();
  return json({ ok: true, kind, key, variant, sha256: sha, bytes: body.byteLength });
}

/** Finalize an upload: store the directory + manifest, prune shards that are
 * no longer referenced (e.g. a yard closed). Readers switch to the new
 * directory within ~30s (isolate cache TTL in inventory.js). */
export async function handleCommit(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const { directory, manifest } = body || {};
  if (!directory || !Array.isArray(directory.yards) || !directory.scrapedAt || !manifest) {
    return err(400, 'bad_commit', 'Body must include {directory:{yards,scrapedAt,...}, manifest}.');
  }

  await env.DB.prepare(
    `INSERT INTO inv_meta (id, directory, manifest, updated_at) VALUES (1, ?1, ?2, ?3)
     ON CONFLICT (id) DO UPDATE SET directory = ?1, manifest = ?2, updated_at = ?3`
  ).bind(JSON.stringify(directory), JSON.stringify(manifest), isoNow()).run();

  // Prune orphans (yards that disappeared between scans).
  const rows = (await env.DB.prepare('SELECT kind, key, variant FROM inv_shards').all()).results || [];
  const keep = new Set(Object.keys(manifest));
  const orphans = rows.filter((r) => !keep.has(`${r.kind}/${r.key}/${r.variant}`));
  for (const o of orphans) {
    await env.DB.prepare('DELETE FROM inv_shards WHERE kind = ?1 AND key = ?2 AND variant = ?3')
      .bind(o.kind, o.key, o.variant).run();
  }
  return json({ ok: true, shards: keep.size, pruned: orphans.length, scrapedAt: directory.scrapedAt });
}

/* ===== Account administration ===== */

// Single paid tier ($12.99/mo). Schema keeps a free-form tier column;
// legacy 'pro_plus' rows are collapsed to pro at read time in resolveTier().
const VALID_TIERS = new Set(['free', 'pro']);

/** Manual tier grant — the TestFlight path before payments exist:
 *   curl -X POST $API/v1/admin/grant -H "x-admin-secret: ..." \
 *        -H "content-type: application/json" \
 *        -d '{"email":"tester@example.com","tier":"pro"}'
 * Optional "expires_at" (ISO 8601) makes it a time-boxed grant. Creates the
 * user if they have not signed in yet — the grant is waiting when they do. */
export async function handleGrant(req, env) {
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = String(body.email || '').trim().toLowerCase();
  const tier = String(body.tier || '').trim();
  const expiresAt = body.expires_at ? String(body.expires_at) : null;
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return err(400, 'bad_email', 'Valid email required.');
  if (!VALID_TIERS.has(tier)) return err(400, 'bad_tier', 'tier must be free or pro.');
  if (expiresAt && isNaN(new Date(expiresAt).getTime())) return err(400, 'bad_expiry', 'expires_at must be ISO 8601.');

  let user = await env.DB.prepare('SELECT id FROM users WHERE email = ?1').bind(email).first();
  if (!user) {
    user = { id: crypto.randomUUID() };
    await env.DB.prepare('INSERT INTO users (id, email, tier, created_at) VALUES (?1, ?2, ?3, ?4)')
      .bind(user.id, email, 'free', isoNow()).run();
  }
  await env.DB.prepare(
    'UPDATE users SET tier = ?1, tier_source = ?2, tier_expires_at = ?3 WHERE id = ?4'
  ).bind(tier, 'manual', expiresAt, user.id).run();
  await env.DB.prepare(
    'INSERT INTO entitlement_events (user_id, email, tier, source, expires_at, note, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)'
  ).bind(user.id, email, tier, 'manual', expiresAt, String(body.note || ''), isoNow()).run();

  return json({ ok: true, email, tier, expiresAt });
}

export async function handleListUsers(req, env) {
  // note = the most recent manual-grant note for the user (from the
  // entitlement_events audit trail) — shown by the admin page so grants
  // stay identifiable ("TestFlight tester", "press", ...).
  const rows = (await env.DB.prepare(
    `SELECT u.email, u.tier, u.tier_source, u.tier_expires_at, u.created_at, u.last_login_at,
            (SELECT e.note FROM entitlement_events e
              WHERE e.user_id = u.id AND e.source = 'manual' AND e.note IS NOT NULL AND e.note != ''
              ORDER BY e.id DESC LIMIT 1) AS note
       FROM users u ORDER BY u.created_at DESC LIMIT 500`
  ).all()).results || [];
  return json({ users: rows, count: rows.length });
}

/* ===== Apple IAP integration point (future) =====
 *
 * Plan of record (documented in README-BACKEND.md): the iOS wrapper app uses
 * RevenueCat for StoreKit receipts. After magic-link sign-in, the app calls
 * Purchases.logIn(<YardScout user id>), so RevenueCat webhook events arrive
 * with app_user_id = our users.id. This endpoint maps subscription events to
 * users.tier + tier_expires_at; resolveTier() (auth.js) already honors expiry,
 * so renewals/lapses need no extra machinery.
 *
 * Status: wired and secret-protected, but NOT battle-tested — RevenueCat can't
 * be pointed at the API until the owner creates the RC project. Treat the
 * event mapping below as a reviewed starting point, verify with RC's
 * "send test event" before launch. */
export async function handleRevenueCatWebhook(req, env) {
  if (!env.REVENUECAT_WEBHOOK_SECRET) {
    return err(503, 'not_configured', 'RevenueCat webhook secret not configured.');
  }
  const got = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
  if (!(await timingSafeEqual(got, env.REVENUECAT_WEBHOOK_SECRET))) {
    return err(401, 'unauthorized', 'Bad webhook credential.');
  }
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const ev = body?.event || {};
  const userId = String(ev.app_user_id || '');
  const user = userId
    ? await env.DB.prepare('SELECT id, email FROM users WHERE id = ?1').bind(userId).first()
    : null;
  if (!user) {
    // 200 so RevenueCat doesn't retry forever; the event is still auditable.
    await env.DB.prepare(
      'INSERT INTO entitlement_events (user_id, email, tier, source, note, raw_payload, created_at) VALUES (?1, NULL, ?2, ?3, ?4, ?5, ?6)'
    ).bind(userId || null, 'free', 'revenuecat', 'unmatched app_user_id', JSON.stringify(ev).slice(0, 4000), isoNow()).run();
    return json({ ok: true, matched: false });
  }

  const ACTIVATE = new Set(['INITIAL_PURCHASE', 'RENEWAL', 'UNCANCELLATION', 'PRODUCT_CHANGE', 'NON_RENEWING_PURCHASE']);
  const DEACTIVATE = new Set(['EXPIRATION', 'REFUND']);
  // Single paid tier: every YardScout subscription product maps to 'pro'
  // ($12.99/mo at launch). product_id still lands in entitlement_events for
  // auditing, so a future second product wouldn't lose information.
  const paidTier = 'pro';

  let tier = null;
  let expiresAt = null;
  if (ACTIVATE.has(ev.type)) {
    tier = paidTier;
    // Grace window over the store expiry so a slow renewal webhook doesn't
    // flash the user back to free.
    expiresAt = ev.expiration_at_ms
      ? new Date(Number(ev.expiration_at_ms) + 3 * 24 * 3600 * 1000).toISOString()
      : null;
  } else if (DEACTIVATE.has(ev.type)) {
    tier = 'free';
  } // CANCELLATION (auto-renew off) intentionally ignored: paid until expiry.

  if (tier) {
    await env.DB.prepare(
      'UPDATE users SET tier = ?1, tier_source = ?2, tier_expires_at = ?3 WHERE id = ?4'
    ).bind(tier, 'revenuecat', expiresAt, user.id).run();
  }
  await env.DB.prepare(
    'INSERT INTO entitlement_events (user_id, email, tier, source, expires_at, note, raw_payload, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)'
  ).bind(user.id, user.email, tier || 'unchanged', 'revenuecat', expiresAt, String(ev.type || ''), JSON.stringify(ev).slice(0, 4000), isoNow()).run();

  return json({ ok: true, matched: true, applied: tier || 'none' });
}
