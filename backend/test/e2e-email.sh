#!/usr/bin/env bash
# Email e2e — fully local (wrangler dev + local D1 + local KV emulator).
#   Phase 1: web-Pro email alerts and the account recap (email_alerts_e2e.mjs),
#            DEV_MODE with no Resend key (log-and-succeed).
#   Phase 2: the free Monday email for web visitors (recap_signup_e2e.mjs):
#            sign-up -> confirm -> Monday recap -> unsubscribe, through the
#            REAL Resend send paths against test/mock-resend.mjs, with a small
#            RESEND_DAILY_CAP so the cap is reached on purpose.
# Usage: from backend/:  npm run test:e2e-email
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8793}"
MOCKPORT="${YS_MOCK_PORT:-8799}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-email"
mkdir -p "$OUT"

# npx -> wrangler -> workerd: kill the whole tree, or workerd outlives the run
# and holds the port (and a deleted state dir) for the next one.
kill_tree() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$c"; done; kill "$1" 2>/dev/null || true; }
cleanup() {
  if [ -n "${DEV_PID:-}" ]; then kill_tree "$DEV_PID"; fi
  if [ -n "${MPID:-}" ]; then kill "$MPID" 2>/dev/null || true; fi
  rm -f .dev.vars.e2e-email .dev.vars.e2e-recap
}
trap cleanup EXIT

wait_up() {
  for i in $(seq 1 60); do
    sleep 1
    if curl -sf "$API/v1/health" >/dev/null 2>&1; then return 0; fi
  done
  echo "wrangler dev never came up:"; tail -20 "$1"; exit 1
}

# ---- phase 1: web-Pro email alerts + account recap ----
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
wait_up "$OUT/dev.log"
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" node test/email_alerts_e2e.mjs
kill_tree "$DEV_PID"; DEV_PID=""
sleep 1

# ---- phase 2: free Monday email for web visitors ----
echo "── starting mock-resend on :$MOCKPORT"
node test/mock-resend.mjs "$MOCKPORT" >"$OUT/mock-resend.log" 2>&1 &
MPID=$!
for i in $(seq 1 20); do
  sleep 0.5
  curl -sf "http://127.0.0.1:$MOCKPORT/ping" >/dev/null 2>&1 && break
  [ "$i" = 20 ] && { echo "mock-resend never came up"; cat "$OUT/mock-resend.log"; exit 1; }
done
cat > .dev.vars.e2e-recap <<EOF
DEV_MODE=1
UPLOAD_TOKEN=dev-upload-token-change-me
ADMIN_SECRET=dev-admin-secret-change-me
EMAIL_UNSUB_SECRET=dev-unsub-secret-change-me
RESEND_API_KEY=re_test_mock_key_0123456789
RESEND_API_URL_TEST=http://127.0.0.1:$MOCKPORT/emails
OPS_DATA_BASE_TEST=http://127.0.0.1:$MOCKPORT/data
OWNER_EMAIL=owner@example.com
RESEND_DAILY_CAP=14
EOF
STATE2="$OUT/wrangler-state-recap"
rm -rf "$STATE2"
echo "── applying migrations (local D1, phase 2)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$STATE2" >"$OUT/migrate-recap.log" 2>&1
npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-recap \
  --persist-to "$STATE2" >"$OUT/dev-recap.log" 2>&1 &
DEV_PID=$!
wait_up "$OUT/dev-recap.log"
echo "── wrangler dev (mock Resend, daily cap 14) is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" YS_STATE_DIR="$STATE2" \
  YS_DEV_LOG="$OUT/dev-recap.log" node test/recap_signup_e2e.mjs
