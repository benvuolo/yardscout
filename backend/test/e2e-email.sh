#!/usr/bin/env bash
# Email e2e — fully local (wrangler dev + local D1 + local KV emulator).
#   Phase 1: web-Pro email alerts and the account recap (email_alerts_e2e.mjs),
#            DEV_MODE with no Resend key (log-and-succeed).
#   Phase 2: the free Monday email for web visitors (recap_signup_e2e.mjs):
#            sign-up -> confirm -> Monday recap -> unsubscribe, through the
#            REAL Resend send paths against test/mock-resend.mjs, with a small
#            RESEND_DAILY_CAP so the cap is reached on purpose.
#   Phase 3: the free emailed alert for web visitors (free_email_alert_e2e.mjs):
#            sign-up -> confirm -> scan commit -> one alert email -> the
#            per-scan and per-day limits -> unsubscribe; same mock, its own
#            database, RESEND_DAILY_CAP=40 (free alerts: 8 a day).
# Usage: from backend/:  npm run test:e2e-email
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8793}"
MOCKPORT="${YS_MOCK_PORT:-8799}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-email"
mkdir -p "$OUT"

# Stops what it starts on any exit (each server in its own process group:
# npx -> wrangler -> workerd, so workerd cannot outlive the run and hold the
# port); refuses a port that is already taken, before every phase too.
source test/servers.sh
ys_need_port "$PORT" "wrangler dev"
ys_need_port "$MOCKPORT" "mock-resend"
ys_on_exit 'rm -f .dev.vars.e2e-email .dev.vars.e2e-recap .dev.vars.e2e-falert'

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
ys_start "$OUT/dev.log" npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-email \
  --persist-to "$OUT/wrangler-state"
DEV_PID=$YS_LAST_PID
wait_up "$OUT/dev.log"
echo "── wrangler dev is up ($API)"

YS_TEST_BASE="$API" node test/email_alerts_e2e.mjs
ys_stop "$DEV_PID" "$PORT"; DEV_PID=""
ys_need_port "$PORT" "wrangler dev (next phase)"

# ---- phase 2: free Monday email for web visitors ----
echo "── starting mock-resend on :$MOCKPORT"
ys_start "$OUT/mock-resend.log" node test/mock-resend.mjs "$MOCKPORT"
MPID=$YS_LAST_PID
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
ys_start "$OUT/dev-recap.log" npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-recap \
  --persist-to "$STATE2"
DEV_PID=$YS_LAST_PID
wait_up "$OUT/dev-recap.log"
echo "── wrangler dev (mock Resend, daily cap 14) is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" YS_STATE_DIR="$STATE2" \
  YS_DEV_LOG="$OUT/dev-recap.log" node test/recap_signup_e2e.mjs
ys_stop "$DEV_PID" "$PORT"; DEV_PID=""
ys_need_port "$PORT" "wrangler dev (next phase)"

# ---- phase 3: free emailed alert for web visitors ----
cat > .dev.vars.e2e-falert <<EOF
DEV_MODE=1
UPLOAD_TOKEN=dev-upload-token-change-me
ADMIN_SECRET=dev-admin-secret-change-me
EMAIL_UNSUB_SECRET=dev-unsub-secret-change-me
RESEND_API_KEY=re_test_mock_key_0123456789
RESEND_API_URL_TEST=http://127.0.0.1:$MOCKPORT/emails
OPS_DATA_BASE_TEST=http://127.0.0.1:$MOCKPORT/data
OWNER_EMAIL=owner@example.com
RESEND_DAILY_CAP=40
EOF
STATE3="$OUT/wrangler-state-falert"
rm -rf "$STATE3"
echo "── applying migrations (local D1, phase 3)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$STATE3" >"$OUT/migrate-falert.log" 2>&1
ys_start "$OUT/dev-falert.log" npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-falert \
  --persist-to "$STATE3"
DEV_PID=$YS_LAST_PID
wait_up "$OUT/dev-falert.log"
echo "── wrangler dev (mock Resend, daily cap 40) is up ($API)"

YS_TEST_BASE="$API" YS_MOCK_BASE="http://127.0.0.1:$MOCKPORT" YS_STATE_DIR="$STATE3" \
  YS_DEV_LOG="$OUT/dev-falert.log" node test/free_email_alert_e2e.mjs
