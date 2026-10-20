# YardScout Pro entitlements — owner setup checklist

The cross-platform Pro system (web Stripe purchase + cross-device email-code
unlock + iOS email link) is **built, tested, and deployed**. The Worker is live
at `yardscout.io/api/ent/*` with everything switched off until the secrets
below exist — the web UI hides its purchase button until then, so nothing
looks broken in the meantime.

How it works (30 seconds): there are **no accounts**. An email address is the
entitlement. Buy Pro on the web → the email you give Stripe is Pro. Buy Pro on
iOS → optionally link an email in the app ("Use Pro on other devices").
Either way, that email + a 6-digit emailed code unlocks Pro on any other
device. Nobody is ever required to enter an email to buy or to use Pro where
they bought it.

```
Browser ──Stripe Checkout──▶ Stripe ──webhook──▶ ┌──────────────────────────┐
iOS app ──StoreKit JWS─────────verify-ios──────▶ │ yardscout-site Worker    │
Android ──Play token─(later)──verify-android──▶ │ KV: email → entitlement  │
Any device ──email → 6-digit code → redeem────▶ └──────────────────────────┘
```

---

## 1. Stripe (web purchase) — ~20 minutes

1. **Create the account**: https://dashboard.stripe.com/register → verify your
   email → you land in **test mode** (orange banner). Everything below works in
   test mode first; repeat the key/webhook steps with live keys when you
   activate the account (Stripe asks for business/bank details at that point).
2. **Create the product**: Products → **+ Add product**
   - Name: `YardScout Pro`
   - Price: **$8.99 / month, recurring** (this mirrors the iOS
     `yardscout_pro_monthly` subscription — keep them matching)
   - Save, then copy the **price id** (`price_…`).
3. **Paste the price id** into `backend/site-proxy/wrangler.toml` →
   `STRIPE_PRICE_PRO = "price_…"`.
4. **Secret key**: Developers → API keys → copy the **Secret key**
   (`sk_test_…`), then from `backend/site-proxy/`:
   ```bash
   npx wrangler secret put STRIPE_SECRET_KEY   # paste sk_test_…
   ```
5. **Webhook**: Developers → Webhooks → **+ Add endpoint**
   - URL: `https://yardscout.io/api/ent/stripe-webhook`
   - Events: `checkout.session.completed`,
     `customer.subscription.created`, `customer.subscription.updated`,
     `customer.subscription.deleted`
   - After creating, reveal the **Signing secret** (`whsec_…`):
   ```bash
   npx wrangler secret put STRIPE_WEBHOOK_SECRET   # paste whsec_…
   ```
6. **Customer portal** (for the "Manage billing" button): Settings →
   Billing → Customer portal → click **Activate** (defaults are fine; make
   sure "cancel subscriptions" is allowed).
7. **Deploy the price id change**: `cd backend/site-proxy && npx wrangler deploy`

> The moment `STRIPE_SECRET_KEY` + `STRIPE_PRICE_PRO` are both set, the
> **"Get Pro — $8.99/mo"** button appears on yardscout.io automatically
> (`/api/ent/config` flips to `{"billing":true}`). Nothing else to flip.

## 2. Resend (unlock-code emails) — ~10 min, +DNS

1. Sign up at https://resend.com (free tier: 100 emails/day — plenty).
2. For **testing** you can skip DNS: the default sender
   `onboarding@resend.dev` is already configured in `wrangler.toml` and works
   for emails sent **to your own Resend account address** immediately.
3. For **real users**, verify the domain: Resend → Domains → **Add domain** →
   `yardscout.io`. Resend shows 3 DNS records to add in Cloudflare
   (dash.cloudflare.com → yardscout.io → DNS):
   - TXT `resend._domainkey` (DKIM) — value from Resend
   - TXT `send` (SPF: `v=spf1 include:amazonses.com ~all`) — exactly as shown
   - MX `send` (`feedback-smtp.us-east-1.amazonses.com`, priority 10)
   Wait for "Verified" (minutes), then edit `wrangler.toml`:
   `EMAIL_FROM = "YardScout <codes@yardscout.io>"` and redeploy.
4. API key: Resend → API Keys → **Create** ("sending access" is enough):
   ```bash
   npx wrangler secret put RESEND_API_KEY   # paste re_…
   ```

## 3. Verify end-to-end (test mode)

1. `curl https://yardscout.io/api/ent/config` → `{"billing":true}`.
2. On yardscout.io: Pro pill → **Get Pro — $8.99/mo** → pay with Stripe's test
   card `4242 4242 4242 4242` (any future expiry/CVC), any email you can read.
3. On return, the sheet should show **You're Pro ✓** within a few seconds,
   with "linked to \<email\>" and a **Manage billing** button that opens the
   Stripe portal.
4. Cross-device: open yardscout.io in a private window → Pro pill →
   **Already have Pro?** → your email → enter the 6-digit code from the email
   → Pro unlocks there too.
5. Cancel the test subscription in the Stripe dashboard → within a day the
   devices drop back to free (or immediately after clearing
   `ys_ent_checked` in localStorage and reloading, if you're impatient).
6. iOS (once 1.4 ships / in a dev build): subscribe via StoreKit → Pro state
   in the upgrade sheet shows **Use Pro on other devices** → link an email →
   redeem it on the web with the code flow. Sandbox StoreKit transactions are
   rejected in production by design — test with `ALLOW_SANDBOX_IAP=1` set
   temporarily as a var, or just rely on the committed `test/e2e.sh` coverage.
7. Going live later: switch the Stripe account to live mode, repeat the key +
   webhook steps with `sk_live_…`/new `whsec_…`, re-put both secrets, done.

## 4. What's already done (no action)

- `yardscout-site` Worker deployed with the entitlement API + `ENTITLEMENTS`
  KV namespace (id `deb0d4c2…`). Site proxying is untouched.
- Web UI live on yardscout.io: purchase button (auto-appears with Stripe),
  "Already have Pro?" code flow, manage-billing, daily re-validation.
- iOS email-link flow implemented and committed — **ships with 1.4** (1.3 is
  in review; its bundled web assets predate this). The web bundle detects a
  pre-1.4 shell and hides the link UI there.
- Local test suites: `backend/site-proxy/test/e2e.sh` (24 API assertions,
  including offline StoreKit-JWS verification against a generated test chain).

## 5. Android (explicitly out of scope here)

`POST /api/ent/verify-android` is reserved and returns 501. When the Google
Play Billing work (separate repo) lands, its verifier should:
1. accept `{purchaseToken, productId, email}`,
2. verify the token via the Play Developer API
   (`purchases.subscriptionsv2.get`, service-account JWT),
3. call the existing `grantEntitlement(env, email, {source:'google_play', …})`
   in `backend/site-proxy/src/entitlements.js` — the same single write path
   Stripe and Apple use. Everything downstream (codes, tokens, status,
   re-validation) then works for Android with zero extra changes.

## Security notes

- Unlock codes: 6 crypto-random digits, 10-minute TTL, single-use, 6 wrong
  tries burns the code; 3 codes/15 min per email, 10/hour per IP.
- `request-code` answers identically whether or not the email has Pro — no
  "who's a subscriber" oracle.
- The Stripe redirect grants nothing by itself: the Worker re-confirms the
  checkout session with Stripe server-side, and the webhook (signature-
  verified, 5-min tolerance) is the durable source of truth.
- StoreKit JWS verification is fully offline: certificate chain pinned to
  Apple Root CA G3, validity windows + Apple's in-app-purchase marker OID
  checked, ES256 verified with the leaf key. Sandbox rejected in production.
- One email per Apple subscription (re-linking moves it, revoking the old).
