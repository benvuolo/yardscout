/* Stripe billing: Checkout for Pro (subscription) and Weekend Pass (one-time),
 * webhook-driven entitlements, and the customer portal for cancel/manage.
 *
 * Design notes:
 *   - No Stripe SDK — the Worker talks to api.stripe.com with form-encoded
 *     fetch calls (the SDK is heavyweight and unnecessary for three endpoints).
 *   - The webhook is the single source of truth for entitlements. Checkout
 *     redirect fragments (#checkout=success) are UI feedback only — a user
 *     can't grant themselves Pro by visiting the success URL.
 *   - Every tier change writes to entitlement_events, same audit trail the
 *     manual admin grants use.
 *   - Weekend Pass = tier 'pro' with a 72-hour expiry; the existing
 *     expired-tier-resolves-to-free logic does the cleanup for free.
 *
 * Env (secrets): STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
 * Env (vars):    STRIPE_PRICE_PRO (recurring price id), STRIPE_PRICE_PASS
 *                (one-time price id), APP_URL
 */

import { json, err, isoNow, timingSafeEqual } from './util.js';
import { getSessionUser } from './auth.js';

const PASS_HOURS = 72;
// Grace period past a subscription period end before Pro lapses — covers
// retry-cycle payment hiccups without a support ticket.
const SUB_GRACE_MS = 3 * 24 * 3600 * 1000;
// Provisional entitlement right after checkout, corrected by the first
// customer.subscription.updated event (which carries current_period_end).
const SUB_PROVISIONAL_MS = 35 * 24 * 3600 * 1000;

/* ---------- Stripe REST helper ---------- */

async function stripe(env, method, path, params) {
  const opts = {
    method,
    headers: { authorization: 'Bearer ' + env.STRIPE_SECRET_KEY },
  };
  if (params) {
    const body = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) body.set(k, String(v));
    }
    opts.body = body;
    opts.headers['content-type'] = 'application/x-www-form-urlencoded';
  }
  const r = await fetch('https://api.stripe.com' + path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    console.log('stripe error', path, r.status, data && data.error && data.error.message);
    throw new Error((data && data.error && data.error.message) || 'Stripe API error');
  }
  return data;
}

/* ---------- entitlement writes (shared shape with admin grants) ---------- */

async function setTier(env, { userId, email, tier, expiresAt, source, note, raw }) {
  await env.DB.prepare(
    'UPDATE users SET tier = ?1, tier_source = ?2, tier_expires_at = ?3 WHERE id = ?4'
  ).bind(tier, source, expiresAt, userId).run();
  await env.DB.prepare(
    'INSERT INTO entitlement_events (user_id, email, tier, source, expires_at, note, raw_payload, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)'
  ).bind(userId, email, tier, source, expiresAt, note || '', raw ? JSON.stringify(raw).slice(0, 4000) : null, isoNow()).run();
}

async function userByStripeCustomer(env, customerId) {
  return env.DB.prepare('SELECT id, email FROM users WHERE stripe_customer_id = ?1')
    .bind(customerId).first();
}

/* ---------- POST /v1/billing/checkout  {plan: "pro" | "pass"} ---------- */

export async function handleCheckout(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first — your purchase needs an account to attach to.');
  if (!env.STRIPE_SECRET_KEY) return err(503, 'billing_off', 'Billing is not configured yet.');

  let body;
  try { body = await req.json(); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const plan = String(body.plan || '');
  if (plan !== 'pro' && plan !== 'pass') return err(400, 'bad_plan', 'plan must be "pro" or "pass".');
  const price = plan === 'pro' ? env.STRIPE_PRICE_PRO : env.STRIPE_PRICE_PASS;
  if (!price) return err(503, 'billing_off', 'Price not configured for this plan.');

  const appUrl = (env.APP_URL || '').replace(/\/+$/, '') + '/';
  const params = {
    mode: plan === 'pro' ? 'subscription' : 'payment',
    'line_items[0][price]': price,
    'line_items[0][quantity]': 1,
    client_reference_id: user.id,
    success_url: appUrl + '#checkout=success',
    cancel_url: appUrl + '#checkout=cancel',
    allow_promotion_codes: 'true',
    'metadata[plan]': plan,
    'metadata[user_id]': user.id,
  };
  // Reuse the Stripe customer across purchases so the portal shows history;
  // otherwise let Checkout create one keyed to the account email.
  if (user.stripe_customer_id) params.customer = user.stripe_customer_id;
  else params.customer_email = user.email;
  if (plan === 'pass') params['payment_intent_data[description]'] = 'YardScout Weekend Pass (72h)';

  const session = await stripe(env, 'POST', '/v1/checkout/sessions', params);
  return json({ url: session.url });
}

/* ---------- POST /v1/billing/portal ---------- */

export async function handlePortal(req, env) {
  const user = await getSessionUser(req, env);
  if (!user) return err(401, 'auth_required', 'Sign in first.');
  if (!user.stripe_customer_id) return err(404, 'no_customer', 'No billing history on this account.');
  const appUrl = (env.APP_URL || '').replace(/\/+$/, '') + '/';
  const session = await stripe(env, 'POST', '/v1/billing_portal/sessions', {
    customer: user.stripe_customer_id,
    return_url: appUrl,
  });
  return json({ url: session.url });
}

/* ---------- POST /v1/stripe/webhook ---------- */

/** Verify the Stripe-Signature header: HMAC-SHA256 of "<t>.<rawBody>" with the
 * webhook signing secret, 5-minute timestamp tolerance. */
async function verifyStripeSignature(rawBody, sigHeader, secret) {
  if (!sigHeader || !secret) return false;
  const parts = Object.fromEntries(sigHeader.split(',').map((p) => p.split('=', 2)));
  const t = parts.t;
  const v1 = parts.v1;
  if (!t || !v1) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > 300) return false;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${t}.${rawBody}`));
  const expected = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, '0')).join('');
  return timingSafeEqual(expected, v1);
}

export async function handleStripeWebhook(req, env) {
  const rawBody = await req.text();
  const ok = await verifyStripeSignature(rawBody, req.headers.get('stripe-signature'), env.STRIPE_WEBHOOK_SECRET);
  if (!ok) return err(400, 'bad_signature', 'Invalid Stripe signature.');

  let event;
  try { event = JSON.parse(rawBody); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const obj = event.data && event.data.object;
  if (!obj) return json({ received: true });

  switch (event.type) {
    case 'checkout.session.completed': {
      const userId = obj.client_reference_id || (obj.metadata && obj.metadata.user_id);
      let user = userId
        ? await env.DB.prepare('SELECT id, email FROM users WHERE id = ?1').bind(userId).first()
        : null;
      // Fallback: match by the email Stripe collected — covers sessions created
      // outside the normal flow (payment links, dashboard-sent invoices).
      if (!user) {
        const email = ((obj.customer_details && obj.customer_details.email) || obj.customer_email || '').toLowerCase();
        if (email) user = await env.DB.prepare('SELECT id, email FROM users WHERE email = ?1').bind(email).first();
      }
      if (!user) { console.log('stripe webhook: no matching user for session', obj.id); break; }
      // Remember the Stripe customer for portal access + future webhook lookups.
      if (obj.customer) {
        await env.DB.prepare('UPDATE users SET stripe_customer_id = ?1 WHERE id = ?2')
          .bind(obj.customer, user.id).run();
      }
      const plan = (obj.metadata && obj.metadata.plan) || (obj.mode === 'payment' ? 'pass' : 'pro');
      const expiresAt = plan === 'pass'
        ? new Date(Date.now() + PASS_HOURS * 3600_000).toISOString()
        : new Date(Date.now() + SUB_PROVISIONAL_MS).toISOString();
      await setTier(env, {
        userId: user.id, email: user.email, tier: 'pro', expiresAt,
        source: plan === 'pass' ? 'stripe_pass' : 'stripe',
        note: `checkout.session.completed (${plan})`,
        raw: { id: obj.id, mode: obj.mode, customer: obj.customer },
      });
      break;
    }

    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const user = await userByStripeCustomer(env, obj.customer);
      if (!user) break;
      const active = obj.status === 'active' || obj.status === 'trialing' || obj.status === 'past_due';
      if (active && obj.current_period_end) {
        const expiresAt = new Date(obj.current_period_end * 1000 + SUB_GRACE_MS).toISOString();
        await setTier(env, {
          userId: user.id, email: user.email, tier: 'pro', expiresAt, source: 'stripe',
          note: `subscription ${obj.status}${obj.cancel_at_period_end ? ' (cancels at period end)' : ''}`,
          raw: { id: obj.id, status: obj.status, current_period_end: obj.current_period_end },
        });
      }
      // Non-active states: entitlement simply runs out at its recorded expiry.
      break;
    }

    case 'customer.subscription.deleted': {
      const user = await userByStripeCustomer(env, obj.customer);
      if (!user) break;
      await setTier(env, {
        userId: user.id, email: user.email, tier: 'pro',
        expiresAt: isoNow(), // effective immediately; resolves to free on next request
        source: 'stripe', note: 'subscription deleted',
        raw: { id: obj.id, status: obj.status },
      });
      break;
    }

    default:
      break; // unhandled event types are fine — Stripe sends many
  }
  return json({ received: true });
}
