/* YardScout Pro entitlements — account-less, email-anchored. Lives in the
 * yardscout.io site Worker (same origin as the web app, no CORS pain) and
 * stores everything in the ENTITLEMENTS KV namespace.
 *
 * Design (agreed with the owner):
 *   - No accounts, no passwords. An email address IS the entitlement anchor.
 *   - Web purchase: Stripe Checkout ($8.99/mo subscription — mirrors the iOS
 *     StoreKit product yardscout_pro_monthly). Stripe collects the email; the
 *     webhook marks it Pro; the purchasing browser unlocks immediately via the
 *     checkout-session confirm endpoint.
 *   - Cross-device unlock: "Already have Pro?" → 6-digit email code (10-min
 *     expiry, rate-limited). NEVER required to buy or to use Pro on the
 *     purchase platform — it exists only for cross-device access.
 *   - iOS purchase → web: the app sends its StoreKit 2 signed transaction
 *     (JWS) + an email; we verify the JWS offline (apple-jws.js) and the email
 *     becomes redeemable anywhere. No license keys (Apple prohibits them).
 *   - Android purchase → web: the app sends its Play purchase token + an
 *     email; we verify server-side via the Play Developer API
 *     (purchases.subscriptionsv2.get with a service-account JWT — see
 *     google-play.js) and the email becomes redeemable anywhere. Until the
 *     Google secrets exist the endpoint answers a clear 503 not_configured
 *     (Pro still works on-device via Play Billing; only the email link waits).
 *
 * KV layout:
 *   ent:<email>     entitlement record (source of truth)
 *   tok:<token>     device token → email (minted on redeem/confirm; lets a
 *                   device re-validate without an email round trip)
 *   code:<email>    pending 6-digit code {hash, attempts}, 10-min TTL
 *   cust:<id>       Stripe customer id → email (webhook lookups)
 *   appletx:<id>    Apple originalTransactionId → email (one email per sub)
 *   gptok:<sha256>  Google Play purchaseToken hash → email (one email per
 *                   sub — hashed because tokens are long-lived credentials)
 *   gauth:v1        cached Google service-account access token (~1h TTL)
 *   rl:<bucket>     rate-limit counters (TTL'd)
 *
 * Env vars (wrangler.toml):  ENT_APP_URL, STRIPE_PRICE_PRO, IOS_PRODUCT_ID,
 *                            IOS_BUNDLE_ID, ANDROID_PACKAGE_NAME,
 *                            ANDROID_PRODUCT_ID, EMAIL_FROM, DEV_MODE
 * Secrets (wrangler secret put): STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
 *                            RESEND_API_KEY, GOOGLE_SA_EMAIL, GOOGLE_SA_KEY
 */

import { verifyStoreKitJws } from './apple-jws.js';
import { googlePlayConfigured, getSubscriptionV2 } from './google-play.js';

const CODE_TTL_S = 600;          // 6-digit codes live 10 minutes
const CODE_MAX_ATTEMPTS = 6;     // then the code is burned
const TOKEN_TTL_S = 400 * 24 * 3600; // device tokens — re-minted on each redeem
const SUB_GRACE_MS = 3 * 24 * 3600 * 1000;       // billing-retry grace
const SUB_PROVISIONAL_MS = 35 * 24 * 3600 * 1000; // until the first webhook lands

/* ---------- tiny helpers ---------- */

/* CORS: echo the caller's Origin rather than a bare wildcard. The native app
 * fetches from Origin `capacitor://localhost` (WKWebView); explicit echo +
 * Vary is the same battle-tested shape yardscout-api has used since 1.3 and
 * is the most compatible across WebKit versions. Requests carry no cookies,
 * so echoing any origin grants nothing. `access-control-max-age` caches the
 * preflight so the shipped 1.4 binary (which sends content-type JSON and
 * therefore preflights) does at most one OPTIONS round trip a day. */
let REQ_ORIGIN = null; // set per-request in handleEntitlements
let REQ_ACRH = null;

function corsHeaders() {
  return {
    'access-control-allow-origin': REQ_ORIGIN || '*',
    'access-control-allow-methods': 'GET, POST, OPTIONS',
    'access-control-allow-headers': REQ_ACRH || 'content-type',
    'access-control-max-age': '86400',
    vary: 'Origin',
  };
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store', ...corsHeaders() },
  });
}
const err = (status, code, message) => json({ error: code, message }, status);

/* Parse a JSON body regardless of content-type. Clients deliberately POST
 * without a content-type header: that keeps the request CORS-"simple" so the
 * native WebView (capacitor://localhost) never needs an OPTIONS preflight. */
async function readJson(req) {
  try { return JSON.parse(await req.text()); } catch { return null; }
}

function normEmail(v) {
  const email = String(v || '').trim().toLowerCase();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254 ? email : null;
}

async function sha256hex(s) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function randomToken() {
  const b = crypto.getRandomValues(new Uint8Array(32));
  return [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
}

function randomCode() {
  // 6 digits, crypto-random, rejection-sampled for uniformity.
  while (true) {
    const n = crypto.getRandomValues(new Uint32Array(1))[0];
    if (n < 4294000000) return String(n % 1000000).padStart(6, '0');
  }
}

const isoNow = () => new Date().toISOString();

/* KV-counter rate limiting. Not atomic (KV is eventually consistent), but
 * plenty to stop code-guessing and email-bombing; the per-code attempt cap
 * is the hard backstop. */
async function rateLimited(env, bucket, max, ttlS) {
  const key = 'rl:' + bucket;
  const cur = parseInt((await env.ENTITLEMENTS.get(key)) || '0', 10);
  if (cur >= max) return true;
  await env.ENTITLEMENTS.put(key, String(cur + 1), { expirationTtl: ttlS });
  return false;
}

const clientIp = (req) => req.headers.get('cf-connecting-ip') || '0.0.0.0';

/* ---------- entitlement records ---------- */

async function getEnt(env, email) {
  return env.ENTITLEMENTS.get('ent:' + email, 'json');
}

function entActive(ent) {
  return !!(ent && ent.pro && (!ent.expiresAt || Date.parse(ent.expiresAt) > Date.now()));
}

/** The single write path for ALL sources (Stripe today, Apple today, Google
 * Play later): upsert the email's record + append to its audit history. */
async function grantEntitlement(env, email, patch, note) {
  const prev = (await getEnt(env, email)) || { createdAt: isoNow(), history: [] };
  const ent = {
    ...prev,
    ...patch,
    pro: patch.pro !== undefined ? patch.pro : true,
    updatedAt: isoNow(),
    history: [...(prev.history || []), { at: isoNow(), note }].slice(-20),
  };
  await env.ENTITLEMENTS.put('ent:' + email, JSON.stringify(ent));
  return ent;
}

async function mintToken(env, email) {
  const token = randomToken();
  await env.ENTITLEMENTS.put('tok:' + token, JSON.stringify({ email, createdAt: isoNow() }),
    { expirationTtl: TOKEN_TTL_S });
  return token;
}

/* ---------- Stripe REST (no SDK — two endpoints don't warrant one) ---------- */

async function stripe(env, method, path, params) {
  const opts = { method, headers: { authorization: 'Bearer ' + env.STRIPE_SECRET_KEY } };
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

/* HMAC check of the Stripe-Signature header (t.v1 scheme, 5-min tolerance). */
async function verifyStripeSignature(rawBody, sigHeader, secret) {
  if (!sigHeader || !secret) return false;
  const parts = Object.fromEntries(sigHeader.split(',').map((p) => p.split('=', 2)));
  if (!parts.t || !parts.v1) return false;
  if (Math.abs(Date.now() / 1000 - Number(parts.t)) > 300) return false;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${parts.t}.${rawBody}`));
  const expected = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, '0')).join('');
  return timingSafeEqual(expected, parts.v1);
}

/* ---------- email sending (Resend) ---------- */

async function sendCodeEmail(env, email, code) {
  if (!env.RESEND_API_KEY) {
    if (env.DEV_MODE === '1') return { dev: true };
    throw new Error('email_unconfigured');
  }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      authorization: 'Bearer ' + env.RESEND_API_KEY,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'YardScout <onboarding@resend.dev>',
      to: [email],
      subject: code + ' is your YardScout Pro code',
      text:
        `Your YardScout Pro unlock code is:\n\n    ${code}\n\n` +
        'Enter it on the device where you requested it. The code expires in 10 minutes.\n\n' +
        "Didn't request this? Someone typed your email by mistake — you can ignore it.\n",
    }),
  });
  if (!r.ok) {
    console.log('resend error', r.status, await r.text().catch(() => ''));
    throw new Error('email_send_failed');
  }
  return {};
}

/* ======================================================================== */
/*  Route handlers                                                          */
/* ======================================================================== */

/* POST /api/ent/checkout {email?} → {url}
 * Starts Stripe Checkout for Pro ($8.99/mo subscription — mirrors iOS). */
async function handleCheckout(req, env) {
  if (!env.STRIPE_SECRET_KEY || !env.STRIPE_PRICE_PRO) {
    return err(503, 'billing_off', 'Web purchase is not live yet — Pro is available in the iOS app.');
  }
  if (await rateLimited(env, 'co:' + clientIp(req), 20, 3600)) {
    return err(429, 'slow_down', 'Too many attempts — try again in an hour.');
  }
  const body = (await readJson(req)) || {};
  const email = body.email ? normEmail(body.email) : null;
  const appUrl = (env.ENT_APP_URL || 'https://yardscout.io').replace(/\/+$/, '') + '/';

  const params = {
    mode: 'subscription',
    'line_items[0][price]': env.STRIPE_PRICE_PRO,
    'line_items[0][quantity]': 1,
    // {CHECKOUT_SESSION_ID} is substituted by Stripe; the app confirms the
    // session server-side on return (UI feedback can't self-grant Pro —
    // the confirm endpoint re-checks payment status with Stripe).
    success_url: appUrl + '?entco={CHECKOUT_SESSION_ID}',
    cancel_url: appUrl + '?entco=cancel',
    allow_promotion_codes: 'true',
    'metadata[source]': 'yardscout_web',
  };
  if (email) params.customer_email = email;

  const session = await stripe(env, 'POST', '/v1/checkout/sessions', params).catch((e) => ({ __err: e.message }));
  if (session.__err) return err(502, 'stripe_error', session.__err);
  return json({ url: session.url });
}

/* GET /api/ent/checkout-session?id=cs_… → {pro, email, token}
 * Called by the browser returning from Stripe: confirms payment with Stripe
 * directly (never trusts the redirect), grants provisionally if the webhook
 * hasn't landed yet, and mints this device's token. */
async function handleCheckoutSession(req, env, url) {
  if (!env.STRIPE_SECRET_KEY) return err(503, 'billing_off', 'Billing is not configured.');
  const id = url.searchParams.get('id') || '';
  if (!/^cs_[A-Za-z0-9_]+$/.test(id)) return err(400, 'bad_session', 'Invalid session id.');
  if (await rateLimited(env, 'cs:' + clientIp(req), 30, 3600)) {
    return err(429, 'slow_down', 'Too many attempts — try again in an hour.');
  }

  const s = await stripe(env, 'GET', '/v1/checkout/sessions/' + id).catch((e) => ({ __err: e.message }));
  if (s.__err) return err(502, 'stripe_error', s.__err);
  const paid = s.status === 'complete' && (s.payment_status === 'paid' || s.payment_status === 'no_payment_required');
  const email = normEmail(s.customer_details && s.customer_details.email);
  if (!paid || !email) return json({ pro: false });

  let ent = await getEnt(env, email);
  if (!entActive(ent)) {
    ent = await grantEntitlement(env, email, {
      source: 'stripe',
      productId: 'yardscout_pro_monthly',
      expiresAt: new Date(Date.now() + SUB_PROVISIONAL_MS).toISOString(),
      stripeCustomerId: s.customer || (ent && ent.stripeCustomerId) || null,
    }, 'checkout-session confirm ' + id);
  }
  if (s.customer) await env.ENTITLEMENTS.put('cust:' + s.customer, email);
  const token = await mintToken(env, email);
  return json({ pro: true, email, token, expiresAt: ent.expiresAt });
}

/* POST /api/ent/stripe-webhook — the durable source of truth for Stripe subs. */
async function handleStripeWebhook(req, env) {
  const rawBody = await req.text();
  const ok = await verifyStripeSignature(rawBody, req.headers.get('stripe-signature'), env.STRIPE_WEBHOOK_SECRET);
  if (!ok) return err(400, 'bad_signature', 'Invalid Stripe signature.');

  let event;
  try { event = JSON.parse(rawBody); } catch { return err(400, 'bad_json', 'Body must be JSON.'); }
  const obj = event.data && event.data.object;
  if (!obj) return json({ received: true });

  switch (event.type) {
    case 'checkout.session.completed': {
      const email = normEmail((obj.customer_details && obj.customer_details.email) || obj.customer_email);
      if (!email) { console.log('webhook: session without email', obj.id); break; }
      if (obj.customer) await env.ENTITLEMENTS.put('cust:' + obj.customer, email);
      await grantEntitlement(env, email, {
        source: 'stripe',
        productId: 'yardscout_pro_monthly',
        expiresAt: new Date(Date.now() + SUB_PROVISIONAL_MS).toISOString(),
        stripeCustomerId: obj.customer || null,
      }, 'checkout.session.completed');
      break;
    }

    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const email = await env.ENTITLEMENTS.get('cust:' + obj.customer);
      if (!email) break;
      const active = obj.status === 'active' || obj.status === 'trialing' || obj.status === 'past_due';
      // Stripe moved current_period_end from the subscription to its items in
      // newer API versions — accept either shape.
      const periodEnd = obj.current_period_end
        || (obj.items && obj.items.data && obj.items.data[0] && obj.items.data[0].current_period_end);
      if (active && periodEnd) {
        await grantEntitlement(env, email, {
          source: 'stripe',
          expiresAt: new Date(periodEnd * 1000 + SUB_GRACE_MS).toISOString(),
          stripeSubscriptionId: obj.id,
        }, `subscription ${obj.status}${obj.cancel_at_period_end ? ' (cancels at period end)' : ''}`);
      }
      break;
    }

    case 'customer.subscription.deleted': {
      const email = await env.ENTITLEMENTS.get('cust:' + obj.customer);
      if (!email) break;
      await grantEntitlement(env, email, { expiresAt: isoNow() }, 'subscription deleted');
      break;
    }

    default:
      break; // Stripe sends many event types; unhandled ones are fine
  }
  return json({ received: true });
}

/* POST /api/ent/request-code {email}
 * Sends a 6-digit unlock code IF the email has an active entitlement. The
 * response is identical either way (no Pro-ownership oracle). */
async function handleRequestCode(req, env) {
  const body = (await readJson(req)) || {};
  const email = normEmail(body.email);
  if (!email) return err(400, 'bad_email', 'Enter a valid email address.');
  if (await rateLimited(env, 'rcip:' + clientIp(req), 10, 3600)) {
    return err(429, 'slow_down', 'Too many code requests — try again in an hour.');
  }
  if (await rateLimited(env, 'rcem:' + email, 3, 900)) {
    return err(429, 'slow_down', 'Too many codes requested for this email — wait 15 minutes.');
  }

  const generic = { ok: true, message: 'If that email has Pro, a 6-digit code is on its way. It expires in 10 minutes.' };
  const ent = await getEnt(env, email);
  if (!entActive(ent)) {
    // Same response, no email sent — an attacker can't probe who's Pro.
    return json(env.DEV_MODE === '1' ? { ...generic, dev_found: false } : generic);
  }

  const code = randomCode();
  await env.ENTITLEMENTS.put('code:' + email,
    JSON.stringify({ hash: await sha256hex(code + ':' + email), attempts: 0 }),
    { expirationTtl: CODE_TTL_S });

  try {
    await sendCodeEmail(env, email, code);
  } catch (e) {
    if (e.message === 'email_unconfigured') return err(503, 'email_off', 'Email delivery is not configured yet.');
    return err(502, 'email_failed', 'Could not send the email — try again in a minute.');
  }
  return json(env.DEV_MODE === '1' ? { ...generic, dev_found: true, dev_code: code } : generic);
}

/* POST /api/ent/redeem-code {email, code} → {pro, token, expiresAt} */
async function handleRedeemCode(req, env) {
  const body = (await readJson(req)) || {};
  const email = normEmail(body.email);
  const code = String(body.code || '').trim();
  if (!email || !/^\d{6}$/.test(code)) return err(400, 'bad_input', 'Enter the email and the 6-digit code.');
  if (await rateLimited(env, 'rdip:' + clientIp(req), 30, 3600)) {
    return err(429, 'slow_down', 'Too many attempts — try again in an hour.');
  }

  const key = 'code:' + email;
  const rec = await env.ENTITLEMENTS.get(key, 'json');
  if (!rec) return err(400, 'bad_code', 'That code is wrong or expired — request a new one.');
  if (rec.attempts >= CODE_MAX_ATTEMPTS) {
    await env.ENTITLEMENTS.delete(key);
    return err(400, 'bad_code', 'Too many wrong tries — request a new code.');
  }

  const match = timingSafeEqual(await sha256hex(code + ':' + email), rec.hash);
  if (!match) {
    await env.ENTITLEMENTS.put(key, JSON.stringify({ ...rec, attempts: rec.attempts + 1 }),
      { expirationTtl: CODE_TTL_S });
    return err(400, 'bad_code', 'That code is wrong or expired — request a new one.');
  }
  await env.ENTITLEMENTS.delete(key); // single use

  const ent = await getEnt(env, email);
  if (!entActive(ent)) return err(410, 'lapsed', 'Pro on that email has lapsed.');
  const token = await mintToken(env, email);
  return json({ pro: true, token, expiresAt: ent.expiresAt || null, source: ent.source });
}

/* POST /api/ent/verify-ios {jws, email} → {linked}
 * The iOS app sends its StoreKit 2 signed transaction + the email the user
 * wants Pro linked to. Fully offline verification — no App Store Server API
 * keys needed. One email per Apple subscription (re-linking moves it). */
async function handleVerifyIos(req, env) {
  const body = (await readJson(req)) || {};
  const email = normEmail(body.email);
  if (!email) return err(400, 'bad_email', 'Enter a valid email address.');
  if (typeof body.jws !== 'string' || body.jws.length < 100 || body.jws.length > 60000) {
    return err(400, 'bad_jws', 'Missing or malformed transaction.');
  }
  if (await rateLimited(env, 'ios:' + clientIp(req), 20, 3600)) {
    return err(429, 'slow_down', 'Too many attempts — try again in an hour.');
  }

  let tx;
  try {
    // DEV TESTS ONLY: a test root CA can be injected via .dev.vars; it is
    // ignored unless DEV_MODE=1 (never set in production).
    const rootCaB64 = env.DEV_MODE === '1' ? env.APPLE_ROOT_CA_B64_TEST : undefined;
    tx = await verifyStoreKitJws(body.jws, { rootCaB64 });
  } catch (e) {
    console.log('verify-ios failed:', e.message);
    return err(400, 'verify_failed', 'The App Store transaction could not be verified.');
  }

  if (tx.bundleId !== (env.IOS_BUNDLE_ID || 'com.benvuolo.yardscout')) {
    return err(400, 'wrong_app', 'Transaction is for a different app.');
  }
  if (tx.productId !== (env.IOS_PRODUCT_ID || 'yardscout_pro_monthly')) {
    return err(400, 'wrong_product', 'Transaction is for a different product.');
  }
  if (tx.revocationDate) return err(400, 'revoked', 'That purchase was refunded or revoked.');
  if (tx.environment === 'Sandbox' && env.DEV_MODE !== '1' && env.ALLOW_SANDBOX_IAP !== '1') {
    return err(400, 'sandbox', 'Sandbox transactions are not accepted.');
  }
  const expiresMs = Number(tx.expiresDate || 0);
  if (!expiresMs || expiresMs + SUB_GRACE_MS < Date.now()) {
    return err(410, 'lapsed', 'That subscription has expired.');
  }

  // One email per Apple subscription: re-linking moves Pro to the new email.
  const txId = String(tx.originalTransactionId || tx.transactionId || '');
  if (txId) {
    const prevEmail = await env.ENTITLEMENTS.get('appletx:' + txId);
    if (prevEmail && prevEmail !== email) {
      const prevEnt = await getEnt(env, prevEmail);
      if (prevEnt && prevEnt.source === 'apple_iap' && prevEnt.appleOriginalTransactionId === txId) {
        await grantEntitlement(env, prevEmail, { pro: false, expiresAt: isoNow() },
          'moved to another email (re-link)');
      }
    }
    await env.ENTITLEMENTS.put('appletx:' + txId, email);
  }

  const ent = await grantEntitlement(env, email, {
    source: 'apple_iap',
    productId: tx.productId,
    expiresAt: new Date(expiresMs + SUB_GRACE_MS).toISOString(),
    appleOriginalTransactionId: txId || null,
    appleEnvironment: tx.environment || null,
  }, 'verify-ios (StoreKit 2 JWS)');

  return json({ linked: true, email, expiresAt: ent.expiresAt });
}

/* POST /api/ent/verify-android {purchaseToken, email, productId?} → {linked}
 * The Android app sends the Play Billing purchase token + the email the user
 * wants Pro linked to. We verify server-side with the Play Developer API
 * (purchases.subscriptionsv2.get — google-play.js); Google is the source of
 * truth, the client is never trusted. One email per Play subscription
 * (re-linking moves it) — the exact mirror of verify-ios above. */

/* subscriptionsv2 states that mean "entitled until expiryTime": ACTIVE,
 * grace period (payment retrying — matches our 3-day house grace), and
 * CANCELED (auto-renew off but the paid period hasn't ended). ON_HOLD,
 * PAUSED, EXPIRED, PENDING etc. are NOT entitled regardless of expiry. */
const PLAY_ENTITLED_STATES = [
  'SUBSCRIPTION_STATE_ACTIVE',
  'SUBSCRIPTION_STATE_IN_GRACE_PERIOD',
  'SUBSCRIPTION_STATE_CANCELED',
];

async function handleVerifyAndroid(req, env) {
  const body = (await readJson(req)) || {};
  const email = normEmail(body.email);
  if (!email) return err(400, 'bad_email', 'Enter a valid email address.');
  const purchaseToken = String(body.purchaseToken || '');
  // Play tokens are opaque url-safe strings (observed 24–200 chars); bound
  // generously but reject anything that can't possibly be one.
  if (!/^[A-Za-z0-9._-]{16,600}$/.test(purchaseToken)) {
    return err(400, 'bad_token', 'Missing or malformed purchase token.');
  }
  if (!googlePlayConfigured(env)) {
    return err(503, 'not_configured',
      'Google Play verification is not set up yet — Pro still works on this device; linking an email will be available soon.');
  }
  if (await rateLimited(env, 'and:' + clientIp(req), 20, 3600)) {
    return err(429, 'slow_down', 'Too many attempts — try again in an hour.');
  }

  let sub;
  try {
    sub = await getSubscriptionV2(env, purchaseToken);
  } catch (e) {
    console.log('verify-android failed:', e.code, e.message);
    if (e.code === 'bad_token') {
      return err(400, 'verify_failed', 'That Google Play purchase could not be verified.');
    }
    return err(502, 'google_error', 'Could not reach Google Play — try again in a minute.');
  }

  const wantProduct = env.ANDROID_PRODUCT_ID || 'yardscout_pro_monthly';
  const line = (Array.isArray(sub.lineItems) ? sub.lineItems : [])
    .find((li) => li && li.productId === wantProduct);
  if (!line) return err(400, 'wrong_product', 'Purchase is for a different product.');

  // License-tester purchases carry testPurchase — same gate as iOS Sandbox.
  if (sub.testPurchase && env.DEV_MODE !== '1' && env.ALLOW_SANDBOX_IAP !== '1') {
    return err(400, 'sandbox', 'Test purchases are not accepted.');
  }

  const state = String(sub.subscriptionState || '');
  const expiresMs = Date.parse(line.expiryTime || '') || 0;
  if (!PLAY_ENTITLED_STATES.includes(state) || !expiresMs || expiresMs + SUB_GRACE_MS < Date.now()) {
    return err(410, 'lapsed', 'That subscription has expired or is paused.');
  }

  // One email per Play subscription: re-linking moves Pro to the new email
  // (mirror of the appletx: pinning). Keyed on a hash — purchase tokens are
  // long-lived credentials and never belong in KV keys in the clear.
  const tokHash = await sha256hex('gp:' + purchaseToken);
  const prevEmail = await env.ENTITLEMENTS.get('gptok:' + tokHash);
  if (prevEmail && prevEmail !== email) {
    const prevEnt = await getEnt(env, prevEmail);
    if (prevEnt && prevEnt.source === 'google_play' && prevEnt.googleTokenHash === tokHash) {
      await grantEntitlement(env, prevEmail, { pro: false, expiresAt: isoNow() },
        'moved to another email (re-link)');
    }
  }
  await env.ENTITLEMENTS.put('gptok:' + tokHash, email);
  // Resubscribe/plan-change mints a NEW token pointing at the old one —
  // retire the old pin so a dead token can't be re-linked later.
  if (sub.linkedPurchaseToken) {
    await env.ENTITLEMENTS.delete('gptok:' + await sha256hex('gp:' + sub.linkedPurchaseToken));
  }

  const ent = await grantEntitlement(env, email, {
    source: 'google_play',
    productId: wantProduct,
    expiresAt: new Date(expiresMs + SUB_GRACE_MS).toISOString(),
    googleTokenHash: tokHash,
    googleOrderId: sub.latestOrderId || null,
  }, 'verify-android (subscriptionsv2 ' + state.replace('SUBSCRIPTION_STATE_', '') + ')');

  return json({ linked: true, email, expiresAt: ent.expiresAt });
}

/* GET /api/ent/status?token=… → {pro, expiresAt, source}
 * Device re-validation. Token-gated (no raw-email oracle). */
async function handleStatus(req, env, url) {
  const token = url.searchParams.get('token') || '';
  if (!/^[0-9a-f]{64}$/.test(token)) return err(400, 'bad_token', 'Invalid token.');
  if (await rateLimited(env, 'st:' + clientIp(req), 60, 3600)) {
    return err(429, 'slow_down', 'Too many checks — try again later.');
  }
  const rec = await env.ENTITLEMENTS.get('tok:' + token, 'json');
  if (!rec) return json({ pro: false, token_valid: false });
  const ent = await getEnt(env, rec.email);
  return json({ pro: entActive(ent), expiresAt: (ent && ent.expiresAt) || null, source: (ent && ent.source) || null });
}

/* POST /api/ent/portal {token} → {url}
 * Stripe customer portal (cancel / card / invoices) — token-gated so only a
 * device that proved email ownership can manage the subscription. */
async function handlePortal(req, env) {
  if (!env.STRIPE_SECRET_KEY) return err(503, 'billing_off', 'Billing is not configured.');
  const body = (await readJson(req)) || {};
  const token = String(body.token || '');
  if (!/^[0-9a-f]{64}$/.test(token)) return err(400, 'bad_token', 'Invalid token.');
  const rec = await env.ENTITLEMENTS.get('tok:' + token, 'json');
  if (!rec) return err(401, 'bad_token', 'Unlock Pro on this device first.');
  const ent = await getEnt(env, rec.email);
  if (!ent || !ent.stripeCustomerId) return err(404, 'no_customer', 'No web billing on that email (App Store subscriptions are managed in iOS Settings).');
  const appUrl = (env.ENT_APP_URL || 'https://yardscout.io').replace(/\/+$/, '') + '/';
  const session = await stripe(env, 'POST', '/v1/billing_portal/sessions', {
    customer: ent.stripeCustomerId,
    return_url: appUrl,
  }).catch((e) => ({ __err: e.message }));
  if (session.__err) return err(502, 'stripe_error', session.__err);
  return json({ url: session.url });
}

/* GET /api/ent/config → {billing} — lets the web UI show the purchase button
 * only once Stripe is actually configured (no broken button pre-launch). */
function handleConfig(env) {
  const billing = !!(env.STRIPE_SECRET_KEY && env.STRIPE_PRICE_PRO);
  return new Response(JSON.stringify({ billing }), {
    headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=300', ...corsHeaders() },
  });
}

/* ---------- router ---------- */

export async function handleEntitlements(req, env, url) {
  REQ_ORIGIN = req.headers.get('origin');
  REQ_ACRH = req.headers.get('access-control-request-headers');
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders() });
  const route = url.pathname.replace(/^\/api\/ent\//, '');
  try {
    if (req.method === 'GET' && route === 'config') return handleConfig(env);
    if (req.method === 'POST' && route === 'checkout') return await handleCheckout(req, env);
    if (req.method === 'GET' && route === 'checkout-session') return await handleCheckoutSession(req, env, url);
    if (req.method === 'POST' && route === 'stripe-webhook') return await handleStripeWebhook(req, env);
    if (req.method === 'POST' && route === 'request-code') return await handleRequestCode(req, env);
    if (req.method === 'POST' && route === 'redeem-code') return await handleRedeemCode(req, env);
    if (req.method === 'POST' && route === 'verify-ios') return await handleVerifyIos(req, env);
    if (req.method === 'POST' && route === 'verify-android') return await handleVerifyAndroid(req, env);
    if (req.method === 'GET' && route === 'status') return await handleStatus(req, env, url);
    if (req.method === 'POST' && route === 'portal') return await handlePortal(req, env);
  } catch (e) {
    console.log('entitlements error', route, e.message);
    return err(500, 'internal', 'Something went wrong — try again.');
  }
  return err(404, 'not_found', 'No such endpoint.');
}
