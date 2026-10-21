#!/usr/bin/env bash
# Email-alerts e2e — fully local (wrangler dev + local D1 + local KV emulator).
# Usage: from backend/:  npm run test:e2e-email
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8793}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-email"
mkdir -p "$OUT"

cat > .dev.vars.e2e-email <<EOF
DEV_MODE=1
UPLOAD_TOKEN=dev-upload-token-change-me
ADMIN_SECRET=dev-admin-secret-change-me
EMAIL_UNSUB_SECRET=dev-unsub-secret-change-me
EOF
rm -rf "$OUT/wrangler-state"

echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── starting wrangler dev on :$PORT"
npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-email \
  --persist-to "$OUT/wrangler-state" >"$OUT/dev.log" 2>&1 &
DEV_PID=$!
trap 'kill $DEV_PID 2>/dev/null; rm -f .dev.vars.e2e-email' EXIT

for i in $(seq 1 60); do
  sleep 1
  if curl -sf "$API/v1/health" >/dev/null 2>&1; then break; fi
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" node test/email_alerts_e2e.mjs
