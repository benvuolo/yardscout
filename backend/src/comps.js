/* Owner comps: hardcode a friend into Pro (or take it back).
 *
 *   POST /v1/admin/ent/grant   header x-ent-admin: <ENT_ADMIN_SECRET>
 *   { email, months?: 12, expires_at?: ISO, revoke?: false, note?: "friend" }
 *
 * Writes the SAME entitlement record the site Worker's Stripe/Apple/Google
 * flows write (ENTITLEMENTS KV is shared, key ent:<email>), so the friend
 * unlocks like any Pro member: Pro sheet → "Already have Pro?" → email →
 * 6-digit code, on web, iPhone and Android. Lives on this Worker because
 * yardscout.io sits behind the zone's bot challenge, which blocks the
 * GitHub runner that the grant-pro workflow uses; 503 until the secret is set. */
import { json, err, timingSafeEqual, isoNow } from './util.js';

const normEmail = (v) => { const s = String(v || '').trim().toLowerCase(); return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s) ? s : ''; };

export async function handleCompGrant(req, env) {
  if (!env.ENT_ADMIN_SECRET) return err(503, 'not_configured', 'ENT_ADMIN_SECRET is not set.');
  const given = req.headers.get('x-ent-admin') || '';
  if (!given || !(await timingSafeEqual(given, env.ENT_ADMIN_SECRET))) return err(401, 'unauthorized', 'Bad admin secret.');
  if (!env.ENTITLEMENTS) return err(503, 'not_configured', 'ENTITLEMENTS KV is not bound.');
  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const email = normEmail(body.email);
  if (!email) return err(400, 'bad_email', 'Valid email required.');
  const note = String(body.note || 'owner comp').slice(0, 120);

  const key = 'ent:' + email;
  const prev = (await env.ENTITLEMENTS.get(key, 'json')) || { createdAt: isoNow(), history: [] };
  let patch;
  if (body.revoke) {
    patch = { pro: false, expiresAt: isoNow() };
  } else {
    let expiresAt = null;
    if (body.expires_at) {
      if (Number.isNaN(Date.parse(body.expires_at))) return err(400, 'bad_date', 'expires_at must be an ISO date.');
      expiresAt = new Date(body.expires_at).toISOString();
    } else if (body.months !== undefined && body.months !== null && body.months !== '') {
      const m = Number(body.months);
      if (!Number.isFinite(m) || m <= 0 || m > 120) return err(400, 'bad_months', 'months must be 1-120.');
      const d = new Date(); d.setMonth(d.getMonth() + Math.round(m)); expiresAt = d.toISOString();
    }
    patch = { pro: true, expiresAt, source: 'comp' };
  }
  const ent = {
    ...prev, ...patch, updatedAt: isoNow(),
    history: [...(prev.history || []), { at: isoNow(), note: (body.revoke ? 'comp revoked: ' : 'comp: ') + note }].slice(-20),
  };
  await env.ENTITLEMENTS.put(key, JSON.stringify(ent));
  const active = !!(ent.pro && (!ent.expiresAt || Date.parse(ent.expiresAt) > Date.now()));
  return json({ ok: true, email, pro: active, expiresAt: ent.expiresAt || null, source: ent.source || null });
}
