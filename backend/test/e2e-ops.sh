#!/usr/bin/env bash
# Ops-monitoring e2e — fully local (wrangler dev + local D1/KV + mock-resend.mjs
# standing in for api.resend.com and the public site data files).
# Usage: from backend/:  npm run test:e2e-ops
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8795}"
MOCKPORT="${YS_MOCK_PORT:-8798}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-ops"
mkdir -p "$OUT"
# Stops what it starts on any exit; refuses a port that is already taken.
source test/servers.sh
ys_need_port "$MOCKPORT" "mock-resend"
ys_need_port "$PORT" "wrangler dev"
ys_on_exit 'rm -f .dev.vars.e2e-ops'

echo "── starting mock-resend on :$MOCKPORT"
ys_start "$OUT/mock-resend.log" node test/mock-resend.mjs "$MOCKPORT"
MPID=$YS_LAST_PID
for i in $(seq 1 20); do
  sleep 0.5
  curl -sf "http://127.0.0.1:$MOCKPORT/ping" >/dev/null 2>&1 && break
  [ "$i" = 20 ] && { echo "mock-resend never came up"; cat "$OUT/mock-resend.log"; exit 1; }
done

# RESEND_API_URL_TEST makes DEV_MODE take the REAL Resend send paths (magic
# link included) against the mock; OPS_DATA_BASE_TEST serves yard_health.json.
cat > .dev.vars.e2e-ops <<EOF
DEV_MODE=1
UPLOAD_TOKEN=dev-upload-token-change-me
ADMIN_SECRET=dev-admin-secret-change-me
RESEND_API_KEY=re_test_mock_key_0123456789
RESEND_API_URL_TEST=http://127.0.0.1:$MOCKPORT/emails
OPS_DATA_BASE_TEST=http://127.0.0.1:$MOCKPORT/data
OWNER_EMAIL=owner@example.com
EOF
rm -rf "$OUT/wrangler-state"


echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── seeding entitlement records + store counts (local KV)"
# Paying-subscribers section: one live Stripe sub, one lapsed, one comp, one
# email-linked iOS buyer (counted via Apple's report, not here), and the
# store-subscribers workflow's KV record with Google not set up.
kvput() { npx wrangler kv key put --binding ENTITLEMENTS --local --persist-to "$OUT/wrangler-state" "$1" "$2" >>"$OUT/kv.log" 2>&1; }
kvput "ent:web1@users.test" '{"pro":true,"source":"stripe","expiresAt":"2099-01-01T00:00:00Z"}'
kvput "ent:web2@users.test" '{"pro":true,"source":"stripe","expiresAt":"2020-01-01T00:00:00Z"}'
kvput "ent:friend@users.test" '{"pro":true,"source":"comp","expiresAt":"2099-01-01T00:00:00Z"}'
kvput "ent:ios1@users.test" '{"pro":true,"source":"apple_iap","expiresAt":"2099-01-01T00:00:00Z"}'
kvput "ops:store-subs" "{\"at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"apple\":{\"active\":4,\"trial\":0,\"asOf\":\"2026-11-02\"},\"google\":{\"error\":\"not set up: add the PLAY_REPORTS_BUCKET repository variable\"}}"

echo "── starting wrangler dev on :$PORT"
# --test-scheduled exposes /__scheduled?cron=… so the cron branches run for real.
ys_start "$OUT/dev.log" npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-ops --test-scheduled \
  --persist-to "$OUT/wrangler-state"
DEV_PID=$YS_LAST_PID

for i in $(seq 1 60); do
  sleep 1
  curl -sf "$API/v1/health" >/dev/null 2>&1 && break
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" node test/ops_e2e.mjs
