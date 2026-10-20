# YardScout Disaster Recovery

What survives if the dev Mac dies, what doesn't, and how to rebuild from zero.
Last audited: 2026-10-20.

## TL;DR — what lives where

| Thing | Where it lives | Machine-independent? |
|---|---|---|
| All code, site (`docs/`), scraper, snapshots, workflows | GitHub `benvuolo/yardscout` | ✅ |
| Live customer entitlements | Cloudflare KV namespace `ENTITLEMENTS` (`deb0d4c244fb4eb09a109050000d0e1b`), bound to the `yardscout-site` Worker | ✅ (Cloudflare-hosted) |
| Accounts/sessions/inventory shards (API) | Cloudflare D1 `yardscout-db` (`b81475d5-a998-4ede-8d43-b0932f8e236a`), bound to `yardscout-api` | ✅ (Cloudflare-hosted) |
| Worker secrets | Cloudflare (write-only) — re-creatable from vendor dashboards, see below | ✅ (re-creatable) |
| Daily yard-snapshot launchd jobs | This Mac — plists + full re-setup guide in [`tools/launchd/`](tools/launchd/README.md) | ⚠️ re-create on new Mac; last snapshots stay in repo |
| **Android upload keystore + passwords** | **`~/yardscout-android/` ONLY — NOT in repo, NOT in cloud** | ❌ **MANUAL BACKUP REQUIRED** |
| **APNs auth key (`AuthKey_53ZHWL335J.p8`)** | `backend/.dev.vars.AuthKey_53ZHWL335J.p8` (gitignored) + already set as `APNS_P8` secret on `yardscout-api` | ❌ **MANUAL BACKUP REQUIRED** (Apple won't re-issue the same key) |
| Local dev secrets (`backend/.dev.vars`, `backend/site-proxy/.dev.vars`) | This Mac only (gitignored) | ⚠️ dev convenience only; rebuild from dashboards |
| `scraper/inventory_history.db`, caches, logs | This Mac (gitignored by design) | OK to lose — CI keeps its own via Actions cache |

## Manual backups you must do NOW (password manager / iCloud)

1. **`~/yardscout-android/upload-keystore.jks`** — the Play upload keystore.
2. **`~/yardscout-android/keystore.properties`** — contains `storeFile`,
   `storePassword`, `keyAlias`, `keyPassword`. The passwords exist nowhere else.
3. **`backend/.dev.vars.AuthKey_53ZHWL335J.p8`** — the APNs key. Apple only
   lets you download a .p8 once; losing it means revoking and creating a new
   key (then updating `APNS_KEY_ID` in `backend/wrangler.toml` and re-putting
   the `APNS_P8` secret).

If the keystore is lost anyway: Play App Signing is enabled (Google holds the
final signing key), so recovery is possible via a Play support request for an
upload-key reset — slow but not fatal.

## Accounts inventory

| Account | Used for |
|---|---|
| GitHub (`benvuolo`) | repo, Actions (scan/parts-research/price-review/coverage-mine), Pages origin |
| Cloudflare | `yardscout-api` + `yardscout-site` Workers, D1, KV, DNS for `yardscout.io` |
| Stripe | web Pro subscription ($8.99/mo, live price `price_1UShwjITsj7pDGFWNBNeEXR8`) + webhook |
| Resend | transactional email (unlock codes from `codes@yardscout.io`, magic links); yardscout.io domain verified |
| Apple Developer / App Store Connect | iOS app `com.benvuolo.yardscout` (team `G23Z9MSBUG`), APNs key `53ZHWL335J` |
| Google Play Console | Android app, Play App Signing |

## Cloudflare Workers — config and secrets

Both Workers deploy from this repo with `npx wrangler deploy`. All non-secret
config is in the committed `wrangler.toml` files. Secrets are set with
`npx wrangler secret put <NAME>` from the Worker's directory.

### `yardscout-site` (`backend/site-proxy/`) — serves yardscout.io, entitlements

| Secret | Re-create from |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe dashboard → Developers → API keys (`sk_live_…`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe dashboard → Developers → Webhooks → the `/api/ent/stripe-webhook` endpoint (`whsec_…`); re-create the endpoint if rebuilding Stripe |
| `RESEND_API_KEY` | Resend dashboard → API Keys (`re_…`) |

The `ENTITLEMENTS` KV namespace holds live customer Pro entitlements. **The
data itself lives on Cloudflare** — nothing to back up locally; just don't
delete the namespace. Its id is pinned in `backend/site-proxy/wrangler.toml`.

### `yardscout-api` (`backend/`) — accounts API, push, weekly digest cron

Secrets (full list in `backend/wrangler.toml` comments): `UPLOAD_TOKEN` (must
match the GitHub Actions secret `YS_UPLOAD_TOKEN`), `ADMIN_SECRET`,
`RESEND_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`VAPID_PRIVATE_JWK` (regenerate with `node backend/scripts/gen-vapid.mjs`,
also updates `VAPID_PUBLIC_KEY` var), `APNS_P8` (the .p8 above).
D1 schema rebuilds from `backend/migrations/` via
`npx wrangler d1 migrations apply yardscout-db --remote`.

## GitHub Actions secrets (repo → Settings → Secrets)

`ALERT_EMAIL`, `ANTHROPIC_API_KEY`, `NTFY_TOPIC`, `OPENAI_API_KEY`,
`SMTP_PASS`, `SMTP_USER`, `YS_UPLOAD_TOKEN`. All re-creatable from the
respective vendor dashboards / your email provider.

## iOS signing

Nothing to back up: distribution certificates and provisioning profiles are
regenerated on demand via Xcode (automatic signing) or developer.apple.com.
The only non-regenerable iOS asset is the APNs .p8 key (see manual backups).

## launchd snapshot jobs (dev-Mac resident by design)

Three daily agents snapshot yards whose hosts block CI/datacenter IPs:
`io.yardscout.indy-snapshot` (08:15), `io.yardscout.ace-snapshot` (08:25),
`io.yardscout.papva-snapshot` (08:35). Scripts are in `scraper/`, plists and
the full fresh-Mac re-setup procedure in [`tools/launchd/README.md`](tools/launchd/README.md).
If the Mac dies, the app keeps working off the last pushed snapshots; just
re-create the jobs on any residential-IP Mac.

## Fresh-machine bootstrap sequence

1. `git clone https://github.com/benvuolo/yardscout.git` (to
   `~/PODIUM_SETUP/admin/junkyard-hunter` if you want the launchd plists to
   work unedited). Configure a GitHub PAT in the keychain for pushes.
2. Restore manual backups: `~/yardscout-android/` (keystore + properties) from
   the password manager; the APNs .p8 wherever convenient.
3. Web/backend dev: `cd backend && npm install` (same in `backend/site-proxy/`).
   `npx wrangler login`. Deploys work immediately — secrets/KV/D1 live on
   Cloudflare and were never local. Optionally re-create `.dev.vars` from
   `.dev.vars.example` for local dev.
4. Scraper + launchd jobs: follow [`tools/launchd/README.md`](tools/launchd/README.md)
   (asdf Python 3.14.3t or any ≥3.12 + `curl_cffi beautifulsoup4 lxml requests`,
   `cp` plists, `launchctl load`).
5. iOS: `npm install` at repo root, `npx cap sync ios`, open `ios/` in Xcode,
   sign in with the Apple ID — automatic signing regenerates certs/profiles.
6. Android: open `android/` in Android Studio; release builds read
   `~/yardscout-android/keystore.properties` (restored in step 2).
