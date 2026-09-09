# YardScout Backend — Accounts, Tiers, and the Real Paywall

This is the monetization backend that moves YardScout's valuable data (resale
ranges, pull costs, demand signals) behind a real API with accounts and tier
entitlements. Until now the Pro gate was client-side decoration — every browser
downloaded the full dataset and `?pro=1` unlocked everything. With this
backend, **free sessions never receive the value data at all**.

**Nothing changes for the live site yet.** The API is additive: the public
`docs/data/inventory_live.json` keeps working exactly as before, and the app
only talks to the API behind an off-by-default feature flag. The cutover
(shrinking/removing the public file) is a later, explicit step — see
[Cutover plan](#cutover-plan).

---

## Stack: Cloudflare Workers + D1 (and why)

| Piece | Choice | Why |
|---|---|---|
| Compute | **Cloudflare Workers** (free plan) | No server to patch or babysit; 100k requests/day free; global edge; deploys in seconds with `wrangler deploy`. |
| Storage | **D1** (Cloudflare's SQLite, free plan) | One store for *everything* — users, sessions, magic tokens, audit log, AND the inventory shards. 5GB / 5M row-reads/day / 100k row-writes/day free is orders of magnitude above current needs. |
| Email | **Resend** (free plan) | Magic-link sign-in emails. 3,000/month, 100/day free; 5-minute signup; one API key. |

Alternatives considered and rejected:

- **Workers KV** for inventory — free plan caps at **1,000 writes/day**; the
  scan pushes ~300 shards (149 yards × 2 tier variants) up to 4×/day ≈ 1,200
  writes. D1 allows 100k row-writes/day. KV also can't do the relational auth
  side.
- **R2** for inventory — fine technically, but enabling R2 requires putting a
  payment method on the Cloudflare account. D1 doesn't. Fewer signup steps,
  same $0.
- **Supabase** — great auth story, but the free tier **pauses the project
  after 7 days of inactivity** (a solo owner's nightmare: app breaks silently),
  and it's a second vendor. Fly.io means a real server to keep alive.

The one hard constraint that shaped the design: the Workers **free plan allows
~10ms CPU per request**, so the Worker can never parse the 22MB inventory.
Instead, the GitHub Action **pre-computes small per-yard shards in both tier
variants** and uploads them gzipped; the Worker streams stored bytes and never
transforms data. Tier enforcement is *which database row gets selected*, not a
filter that could have bugs.

### Cost expectations

**$0/month at current scale**, with headroom for roughly 100× growth:

- Workers free: 100k req/day. A user session ≈ 10 requests (1 plan + ~8 yard
  shards + partsets, then browser-cached via ETag). ≈ 10k daily sessions fit.
- D1 free: 5M row reads/day (a request reads 1–3 rows), 100k row writes/day
  (a full inventory push writes ~370; 4×/day ≈ 1,500).
- Resend free: 100 sign-in emails/day.

First paid step if the app outgrows this: Workers Paid, $5/month.

---

## Architecture

```
                      ┌──────────────────────────────────────────────┐
                      │ GitHub Actions (scan.yml, every 6h)          │
                      │  scraper → inventory_live.json                │
                      │    ├─ commit to repo (public file — for now)  │
                      │    └─ push_inventory.py                       │
                      │        builds per-yard shards ×2 variants     │
                      │        (free: no $ values / pro: everything)  │
                      │        + vindex (id/VIN→yard) + directory     │
                      │        uploads only CHANGED shards            │
                      └───────────────┬──────────────────────────────┘
                                      │ PUT shard (x-upload-token, gzip)
                                      │ POST commit (directory+manifest)
                                      ▼
        ┌──────────────────────────────────────────────────────────┐
        │ Cloudflare Worker: yardscout-api        (backend/src/)   │
        │                                                          │
        │  GET /v1/inventory?lat&lng&radius → plan (yards in       │
        │      radius + shard URLs)      ┌───────────────────────┐ │
        │  GET /v1/inventory/shard/:yard │ D1 (yardscout-db)     │ │
        │      → streams pre-gzipped     │  inv_shards (gzip)    │ │
        │      free|pro blob by SESSION  │  inv_meta (directory) │ │
        │  GET /v1/vehicles/:idOrVin     │  users / sessions     │ │
        │  POST /v1/auth/request-link ───│  magic_tokens         │ │
        │  GET  /v1/auth/callback        │  entitlement_events   │ │
        │  GET  /v1/me   POST /v1/auth/logout └──────────────────┘ │
        │  POST /v1/admin/grant (x-admin-secret)                   │
        │  POST /v1/iap/revenuecat (Apple IAP — future)            │
        └──────┬───────────────────────────────────┬───────────────┘
               │ magic-link email                  │ JSON + CORS
               ▼                                   ▼
        ┌────────────┐            ┌────────────────────────────────┐
        │ Resend     │            │ PWA (docs/ on GitHub Pages)    │
        │ (free tier)│            │  api.js — flag-gated API layer │
        └────────────┘            │  falls back to static file     │
                                  │  session: bearer in localStorage│
                                  └────────────────────────────────┘
```

Auth flow: `request-link` emails a single-use, 15-minute magic link → callback
verifies + creates a 90-day session → 302 back to the app with
`#session=<token>` (a URL *fragment* — never sent to any server) → app stores
it in localStorage and sends `Authorization: Bearer`. The PWA is on a
different origin than the API, so httpOnly cookies would be third-party
(Safari blocks them); a bearer token is the pragmatic choice, and tokens are
stored SHA-256-hashed server-side and revocable.

Tier data contract (matches the app's existing free UI):

| | Free / anonymous | Pro / Pro+ |
|---|---|---|
| Vehicles, VINs, arrival dates, yard/row | ✓ | ✓ |
| Part names, rarity, trim status, sell channel | ✓ | ✓ |
| Resale ranges (low/high), pull costs, `maxValue` | stripped server-side | ✓ |
| Demand speed / sell notes | stripped server-side | ✓ |

---

## Owner setup — going live (~30 minutes)

### 1. Cloudflare (the API)

1. Create a free account at [dash.cloudflare.com](https://dash.cloudflare.com)
   (no card needed).
2. In a terminal:

   ```bash
   cd backend
   npm install
   npx wrangler login                      # opens browser once
   npx wrangler d1 create yardscout-db    # prints a database_id
   ```

3. Paste the printed `database_id` into `backend/wrangler.toml` (replacing the
   zeros placeholder). Commit that — an id is not a secret.
4. Create the schema and set secrets (generate strong random values for the
   first two, e.g. `openssl rand -hex 32`, and save them in your password
   manager):

   ```bash
   npx wrangler d1 migrations apply yardscout-db --remote
   npx wrangler secret put UPLOAD_TOKEN    # paste random value #1
   npx wrangler secret put ADMIN_SECRET    # paste random value #2
   npx wrangler secret put RESEND_API_KEY  # from step 2 below
   npm run deploy
   ```

   Deploy prints your API URL, e.g.
   `https://yardscout-api.<your-subdomain>.workers.dev` — note it.

### 2. Resend (sign-in emails)

1. Sign up free at [resend.com](https://resend.com), create an API key, use it
   in the `RESEND_API_KEY` secret above.
2. Out of the box, emails send from Resend's shared `onboarding@resend.dev`
   (fine for TestFlight). For a proper sender later: verify a domain in Resend
   and change `EMAIL_FROM` in `wrangler.toml`, then `npm run deploy`.

### 3. GitHub repo (the data pipeline)

In the repo settings → Secrets and variables → Actions:

- **Secret** `YS_UPLOAD_TOKEN` = the same random value #1 you gave the Worker.
- **Variable** `YS_API_URL` = your Worker URL.

The next 6-hour scan (or a manual "Run workflow") pushes inventory to the API.
Until these are set, the push step prints "not configured — skipping" and the
pipeline behaves exactly as today.

### 4. Verify

```bash
API=https://yardscout-api.<your-subdomain>.workers.dev
curl $API/v1/health
curl "$API/v1/inventory?lat=40.76&lng=-111.89&radius=50" | head -c 400
# free variant: part entries have names but no "low"/"high"/"cost"
```

Then open the app with the flag on:
`https://benvuolo.github.io/yardscout/?api=1&apibase=<your API URL>`
— cars load through the API (Network tab shows `/v1/inventory/...`), the Pro
sheet gains a sign-in box, and value data appears only for Pro accounts.

### 5. Grant Pro to TestFlight testers (before payments exist)

```bash
curl -X POST "$API/v1/admin/grant" \
  -H "x-admin-secret: <ADMIN_SECRET>" -H "content-type: application/json" \
  -d '{"email":"tester@example.com","tier":"pro","note":"TestFlight wave 1"}'
```

Optional `"expires_at":"2027-01-01T00:00:00Z"` makes it time-boxed (expiry is
enforced at request time — no cleanup job). `"tier":"free"` revokes. List
everyone: `curl -H "x-admin-secret: ..." $API/v1/admin/users`.

---

## Local development & tests (no accounts needed)

Everything runs locally via `wrangler dev` (bundled `workerd` + local D1
SQLite). `DEV_MODE=1` logs magic links and returns them in the API response
instead of sending email — a built-in mail catcher.

```bash
cd backend
npm install
cp .dev.vars.example .dev.vars     # gitignored local secrets
npm run migrate:local
npm run dev                        # API on http://127.0.0.1:8787
# seed real data (6 yards):
python3 ../scraper/push_inventory.py --api http://127.0.0.1:8787 \
    --token dev-upload-token-change-me --max-yards 6
```

Two test suites (both start/stop their own servers):

- `npm run test:e2e` — 37 curl-level checks: upload auth, manifest diff-skip,
  radius filtering, free-vs-pro field stripping, ETag/304, magic-link
  issue/redeem/single-use/expiry, grants, expired grants, vehicle detail by id
  and VIN, logout, CORS allow-list.
- `../.venv/bin/python test/browser_e2e.py` — 17 Playwright checks driving the
  real PWA against the real Worker: static fallback, API inventory assembly,
  sign-in through the account UI (full magic-link redirect round-trip), tier
  gates flipping on grant, logout clean-up, zero JS errors.

Both suites pass as of this commit (see PR description for the transcript).

---

## Security notes

- **No secrets in the repo** — `wrangler.toml` holds only public config;
  runtime secrets live in Cloudflare (`wrangler secret put`) and GitHub
  Actions secrets; local ones in gitignored `.dev.vars`.
- Magic-link tokens and session tokens: 256-bit random, stored only as SHA-256
  hashes, single-use (magic) / revocable (sessions), expiring (15 min / 90 d).
- Upload and admin are separate secrets — the CI-held upload token can only
  write inventory, never touch accounts. Both compared constant-time.
- Rate limits: per-IP in-memory (best-effort) + persistent D1-backed caps on
  email sending (5/email/hour, 10/IP/hour).
- CORS is an explicit origin allow-list (`APP_ORIGINS`).
- The public repo stays clean: test credentials in scripts are obvious
  dummies (`e2e-upload-token` etc.) that only ever bind to localhost.

---

## Cutover plan (later, explicit step — do NOT do casually)

Goal: stop shipping value data in the public repo file so the paywall is real.

1. **Enable API mode for everyone**: in `docs/api.js`, set
   `YS_API_BASE = 'https://yardscout-api...workers.dev'` and change
   `enabled()` to not require the `jh_use_api` flag. Bump the service-worker
   cache version. The static file automatically becomes the fallback for
   API outages.
2. **Reduce the public file to the free variant**: in `scan.yml`, replace the
   committed `inventory_live.json` with a free-variant build (same shape,
   `maxValue`/`premium` zeroed, partSets stripped to
   name/rarity/trim/sell-channel — `push_inventory.py`'s `build_shards()`
   already produces exactly this; a `--write-free-file` flag is a ~10-line
   addition). The app's offline/fallback path then never contains dollar data.
   Also gate or stop committing `*_pricing.json` (pull costs) the same way.
3. **History scrub decision**: old git commits still contain past values.
   Either accept that (it's stale data, decreasingly valuable) or squash/reset
   the repo history at cutover. Recommendation: accept it; freshness is the
   product.
4. Watch the Worker dashboard for a week (requests/day vs the 100k free cap).

Rollback at any point: set `YS_API_BASE = ''` — the app reverts to the static
file path.

## Apple IAP / TestFlight integration plan

Designed-in integration point: **RevenueCat** (free up to $2.5k MTR) so the
iOS app never talks to Apple receipts directly.

1. iOS wrapper app (or PWA-in-WKWebView) signs the user in via the same
   magic-link flow, then calls `Purchases.logIn(<user id from /v1/me>)` —
   RevenueCat's `app_user_id` becomes the YardScout user id.
2. Create App Store subscription products; include `plus` in the Pro+ product
   id (the webhook maps product ids containing "plus" → `pro_plus`, otherwise
   `pro`).
3. In RevenueCat: add a webhook → `https://<api>/v1/iap/revenuecat`, set an
   Authorization header value, and store the same value as the Worker secret:
   `npx wrangler secret put REVENUECAT_WEBHOOK_SECRET`.
4. The already-implemented handler (`backend/src/admin.js`,
   `handleRevenueCatWebhook`) maps INITIAL_PURCHASE / RENEWAL /
   UNCANCELLATION / PRODUCT_CHANGE → paid tier with the store expiry (+3-day
   grace), EXPIRATION / REFUND → free. Every event lands in
   `entitlement_events` for auditing. **Send RevenueCat's test event before
   trusting it** — the handler is reviewed and tested at the HTTP level but has
   not seen real RC traffic.
5. TestFlight testers before that exists: manual grants (section 5 above).

## Repo layout added by this PR

```
backend/
├── wrangler.toml           # Worker config (public — no secrets)
├── package.json            # wrangler dev-dependency + npm scripts
├── migrations/0001_init.sql# D1 schema (users/sessions/tokens/shards/audit)
├── src/
│   ├── index.js            # router, CORS, rate limits
│   ├── auth.js             # magic links, sessions, resolveTier()
│   ├── inventory.js        # plan/shards/partsets/vehicle-detail
│   ├── admin.js            # ingestion, grants, RevenueCat webhook
│   └── util.js             # crypto/response/gzip helpers
├── test/e2e.sh             # 37-check curl suite (local, accountless)
├── test/browser_e2e.py     # 17-check Playwright suite (real PWA ↔ real API)
└── .dev.vars.example       # local dev secrets template
scraper/push_inventory.py   # shard builder + differential uploader (stdlib only)
docs/api.js                 # frontend API layer (flag-gated, static fallback)
```
