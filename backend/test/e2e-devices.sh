#!/usr/bin/env bash
# Native-device (FCM) alerts e2e — fully local (wrangler dev + local D1 +
# mock-fcm.mjs standing in for oauth2.googleapis.com and fcm.googleapis.com).
# Usage: from backend/:  npm run test:e2e-devices
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8794}"
MOCKPORT="${YS_MOCK_PORT:-8797}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-devices"
mkdir -p "$OUT"
# Stops what it starts on any exit (mock-fcm included: it used to start
# before the trap, and workerd outlived a plain kill of npx); refuses a port
# that is already taken.
source test/servers.sh
ys_need_port "$MOCKPORT" "mock-fcm"
ys_need_port "$PORT" "wrangler dev"
ys_on_exit 'rm -f .dev.vars.e2e-devices'

echo "── starting mock-fcm on :$MOCKPORT"
ys_start "$OUT/mock-fcm.log" node test/mock-fcm.mjs "$MOCKPORT" "$OUT"
MPID=$YS_LAST_PID
for i in $(seq 1 20); do
  sleep 0.5
  curl -sf "http://127.0.0.1:$MOCKPORT/ping" >/dev/null 2>&1 && break
  [ "$i" = 20 ] && { echo "mock-fcm never came up"; cat "$OUT/mock-fcm.log"; exit 1; }
done

# COMMIT_EXT_CEILING_TEST=25: one scan commit may make 25 outside calls here
# (45 in production, src/commit_budget.js), so the "Pro first when the budget
# is tight" check can fill it with 25 Pro devices.
# FCM_SA_KEY goes in as one line with literal \n escapes — exactly how a
# pasted JSON-key private_key arrives in production; fcm.js normalizes.
SA_KEY_ONELINE=$(awk 'BEGIN{ORS="\\n"} {print}' "$OUT/sa_key.pem")
cat > .dev.vars.e2e-devices <<EOF
DEV_MODE=1
UPLOAD_TOKEN=dev-upload-token-change-me
ADMIN_SECRET=dev-admin-secret-change-me
FCM_PROJECT_ID=yardscout-test
FCM_SA_EMAIL=test-fcm@yardscout-test.iam.gserviceaccount.com
FCM_SA_KEY=$SA_KEY_ONELINE
FCM_TOKEN_URL_TEST=http://127.0.0.1:$MOCKPORT/token
FCM_API_URL_TEST=http://127.0.0.1:$MOCKPORT
COMMIT_EXT_CEILING_TEST=25
EOF
rm -rf "$OUT/wrangler-state"


echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── starting wrangler dev on :$PORT"
ys_start "$OUT/dev.log" npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-devices \
  --persist-to "$OUT/wrangler-state"
DEV_PID=$YS_LAST_PID

for i in $(seq 1 60); do
  sleep 1
  curl -sf "$API/v1/health" >/dev/null 2>&1 && break
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" node test/device_alerts_e2e.mjs
