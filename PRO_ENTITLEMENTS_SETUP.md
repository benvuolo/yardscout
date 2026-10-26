# YardScout Pro entitlements — owner setup checklist

The cross-platform Pro system (web Stripe purchase + cross-device email-code
unlock + iOS and Android email link) is **built, tested, and deployed**. The
`yardscout-site` Worker serves `yardscout.io/api/ent/*`; each store-specific
piece switches itself on when its secrets exist (Stripe → purchase button,
Google pair → Android email link) and answers 503 `not_configured` until then,
so nothing looks broken in the meantime.

How it works (30 seconds): there are **no accounts**. An email address is the
entitlement. Buy Pro on the web → the email you give Stripe is Pro. Buy Pro on
iOS or Android → optionally link an email in the app ("Use Pro on other
devices"). Either way, that email + a 6-digit emailed code unlocks Pro on any
other device. Nobody is ever required to enter an email to buy or to use Pro
where they bought it.

```
Browser ──Stripe Checkout──▶ Stripe ──webhook──▶ ┌──────────────────────────┐
iOS app ──StoreKit 2 JWS────────verify-ios────▶ │ yardscout-site Worker    │
Android ──Play purchase token──verify-android─▶ │ KV: email → entitlement  │
Any device ──email → 6-digit code → redeem────▶ └──────────────────────────┘
```

Whether each secret below is already set on the live Worker is not visible
from the repo — check with `cd backend/site-proxy && npx wrangler secret list`.
(`STRIPE_PRICE_PRO` is already filled in `wrangler.toml`, which suggests the
Stripe steps were done.)

---

## 1. Stripe (web purchase) — ~20 minutes

1. **Create the account**: https://dashboard.stripe.com/register → verify your
   email → you land in **test mode** (orange banner). Everything below works in
   test mode first; repeat the key/webhook steps with live keys when you
   activate the account (Stripe asks for business/bank details at that point).
2. **Create the product**: Products → **+ Add product**
   - Name: `YardScout Pro`
   - Price: **$8.99 / month, recurring** (this mirrors the iOS + Play
     `yardscout_pro_monthly` subscription — keep them matching)
   - Save, then copy the **price id** (`price_…`).
3. **Paste the price id** into `backend/site-proxy/wrangler.toml` →
   `STRIPE_PRICE_PRO = "price_…"` (done — a `price_1US…` id is committed).
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
2. For **testing** you can skip DNS: Resend's default sender
   `onboarding@resend.dev` works for emails sent **to your own Resend account
   address** immediately (set `EMAIL_FROM` back to it temporarily).
3. For **real users**, verify the domain: Resend → Domains → **Add domain** →
   `yardscout.io`. Resend shows 3 DNS records to add in Cloudflare
   (dash.cloudflare.com → yardscout.io → DNS):
   - TXT `resend._domainkey` (DKIM) — value from Resend
   - TXT `send` (SPF: `v=spf1 include:amazonses.com ~all`) — exactly as shown
   - MX `send` (`feedback-smtp.us-east-1.amazonses.com`, priority 10)
   Wait for "Verified" (minutes). `wrangler.toml` already has
   `EMAIL_FROM = "YardScout <codes@yardscout.io>"`, and `backend/wrangler.toml`
   notes yardscout.io is verified in Resend for the alert sender.
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
6. iOS (shipped since 1.4): subscribe via StoreKit → Pro state in the upgrade
   sheet shows **Use Pro on other devices** → link an email → redeem it on
   the web with the code flow. Sandbox StoreKit transactions are rejected in
   production by design — test with `ALLOW_SANDBOX_IAP=1` set temporarily as
   a var, or just rely on the committed `test/e2e.sh` coverage.
7. Android (shipped since 1.1): same flow; the app hands its Play purchase
   token to `/verify-android`. Needs the Google pair from §5; until then the
   link UI gets the 503 "linking will be available soon" message and Pro
   still works on-device.
8. Going live later: switch the Stripe account to live mode, repeat the key +
   webhook steps with `sk_live_…`/new `whsec_…`, re-put both secrets, done.

## 4. What's already done (no action)

- `yardscout-site` Worker deployed with the entitlement API + `ENTITLEMENTS`
  KV namespace (id `deb0d4c2…`). Site proxying is untouched.
- Web UI live on yardscout.io: purchase button (auto-appears with Stripe),
  "Already have Pro?" code flow, manage-billing, daily re-validation.
- iOS email-link flow shipped with 1.4 (`Purchases.getTransactionJws` →
  `/verify-ios`); Android email-link flow shipped with 1.1
  (`Purchases.getPurchaseToken` → `/verify-android`). Current store builds
  are 1.10 on both (see `git log --grep='chore(release)'`).
- Local test suites: `backend/site-proxy/test/e2e.sh` (~40 assertions,
  including offline StoreKit-JWS verification against a generated test chain
  and verify-android against `test/mock-play.mjs`).

## 5. Android (Google Play) — built; needs two secrets

`POST /api/ent/verify-android {purchaseToken, email, productId?}` is
implemented in `backend/site-proxy/src/entitlements.js` (`handleVerifyAndroid`)
with the Play Developer API client in `src/google-play.js`:

1. Verifies the token server-side with `purchases.subscriptionsv2.get`
   (service-account JWT signed with WebCrypto, bearer token cached ~1h in KV
   under `gauth:v1`). Google is the source of truth; the client is never
   trusted. Package `io.yardscout.app`, product `yardscout_pro_monthly`
   (`ANDROID_PACKAGE_NAME` / `ANDROID_PRODUCT_ID` vars).
2. Entitled states: `ACTIVE`, `IN_GRACE_PERIOD`, `CANCELED` (paid period not
   over). `ON_HOLD`, `PAUSED`, `EXPIRED`, `PENDING` are not.
3. Calls the same `grantEntitlement(…, {source:'google_play', …})` write path
   Stripe and Apple use, so codes, tokens, status and re-validation work
   unchanged. One email per Play subscription (re-linking moves it).
4. Rate limit: 20 attempts/hour per IP. Until both secrets exist it answers
   **503 `not_configured`** (not 501).

Secrets (from `backend/site-proxy/`; the same service account the Play
release workflow uses — `RELEASING.md`):

```bash
npx wrangler secret put GOOGLE_SA_EMAIL   # the SA's client_email (…@….iam.gserviceaccount.com)
npx wrangler secret put GOOGLE_SA_KEY     # its private_key PEM from the JSON key file (literal "\n" ok)
```

The service account needs access to the app in Play Console (Users and
permissions) so `androidpublisher` can read its subscriptions.

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
- Play tokens are verified server-to-server only; the token hash is stored so
  re-linking the same subscription is idempotent.
- One email per Apple or Play subscription (re-linking moves it, revoking the
  old).
- `DEV_MODE=1` (test-only) returns codes in API responses and allows the test
  Apple root CA / mock Play endpoints. NEVER in production.
