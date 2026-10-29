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

echo "── starting mock-resend on :$MOCKPORT"
node test/mock-resend.mjs "$MOCKPORT" >"$OUT/mock-resend.log" 2>&1 &
MPID=$!
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

# npx → wrangler → workerd: kill the whole tree, or workerd outlives the run
# and holds the port (and a deleted state dir) for the next one.
kill_tree() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$c"; done; kill "$1" 2>/dev/null || true; }
trap 'kill $MPID 2>/dev/null || true; [ -n "${DEV_PID:-}" ] && kill_tree $DEV_PID; rm -f .dev.vars.e2e-ops' EXIT

echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── starting wrangler dev on :$PORT"
# --test-scheduled exposes /__scheduled?cron=… so the cron branches run for real.
npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-ops --test-scheduled \
  --persist-to "$OUT/wrangler-state" >"$OUT/dev.log" 2>&1 &
DEV_PID=$!

for i in $(seq 1 60); do
  sleep 1
  curl -sf "$API/v1/health" >/dev/null 2>&1 && break
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" node test/ops_e2e.mjs
