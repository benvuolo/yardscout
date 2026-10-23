#!/usr/bin/env bash
# Coverage-request e2e — fully local (wrangler dev + local D1), no account needed.
#
# Exercises the Parts-tab "ask us to add it" surface:
#   validation (kind/email/empty) → request-key normalization & aggregation →
#   admin auth → owner digest (send + one-per-day throttle) → per-IP rate limit.
#
# Usage: from backend/:  npm install && npm run test:e2e-coverage
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${YS_TEST_PORT:-8791}"
API="http://127.0.0.1:$PORT"
OUT="test/.out-coverage"
mkdir -p "$OUT"

ADMIN_SECRET="e2e-admin-secret"

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ✓ $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  ✗ $1"; }
check(){ if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected [$3], got [$2])"; fi; }

command -v jq >/dev/null || { echo "jq is required"; exit 1; }

# ── isolated dev vars + fresh local D1 state ────────────────────────────────
cat > .dev.vars.e2e-coverage <<EOF
DEV_MODE=1
UPLOAD_TOKEN=e2e-upload-token
ADMIN_SECRET=$ADMIN_SECRET
OWNER_EMAIL=owner@example.com
EOF
rm -rf "$OUT/wrangler-state"

echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── starting wrangler dev on :$PORT"
npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e-coverage \
  --persist-to "$OUT/wrangler-state" >"$OUT/dev.log" 2>&1 &
DEV_PID=$!
trap 'kill $DEV_PID 2>/dev/null; rm -f .dev.vars.e2e-coverage' EXIT

for i in $(seq 1 60); do
  sleep 1
  if curl -sf "$API/v1/health" >/dev/null 2>&1; then break; fi
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
ok "wrangler dev is up ($API)"

post() { # post <json> → "<status> <body>"
  curl -s -w '\n%{http_code}' -X POST "$API/v1/coverage/request" \
    -H 'content-type: application/json' -d "$1"
}
status_of() { echo "$1" | tail -1; }

# ── validation (system boundary) ────────────────────────────────────────────
echo "── validation"
R=$(post '{"kind":"car","year":2005,"make":"Toyota","model":"Camry","part":"Alternator","zip":"84101","email":"seeker@example.com","note":"3.0 V6"}')
check "valid full request accepted" "$(status_of "$R")" "200"

R=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/v1/coverage/request" -H 'content-type: application/json' -d 'not json')
check "malformed JSON rejected" "$R" "400"

R=$(post '{"kind":"car","make":"Toyota","model":"Camry","part":"Alternator","email":"not-an-email"}')
check "bad email rejected" "$(status_of "$R")" "400"

R=$(post '{"kind":"part","email":"a@b.co"}')
check "empty request (no part, no car) rejected" "$(status_of "$R")" "400"

R=$(post '{"kind":"everything","part":"Alternator"}')
check "unknown kind rejected" "$(status_of "$R")" "400"

# ── request-key normalization & aggregation ─────────────────────────────────
echo "── aggregation"
R=$(post '{"kind":"engine","year":1999,"make":"Ford","model":"F-150","part":"Engine assembly","email":"f150@example.com"}')
check "dupe A (F-150) accepted" "$(status_of "$R")" "200"
R=$(post '{"kind":"engine","year":1999,"make":"Ford","model":"F150","part":"engine ASSEMBLY"}')
check "dupe B (F150, case differs) accepted" "$(status_of "$R")" "200"

# zip is validated server-side: junk zip stores as null, request still lands
R=$(post '{"kind":"part","part":"Supercharger","zip":"abc12"}')
check "junk zip tolerated (stored null)" "$(status_of "$R")" "200"

S=$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/admin/coverage")
check "admin list without secret rejected" "$S" "401"

LIST=$(curl -s -H "x-admin-secret: $ADMIN_SECRET" "$API/v1/admin/coverage")
N=$(echo "$LIST" | jq '[.grouped[] | select(.make=="Ford")] | .[0].requests')
check "F-150/F150 aggregate under one request_key (2 requests)" "$N" "2"
WE=$(echo "$LIST" | jq '[.grouped[] | select(.make=="Ford")] | .[0].with_email')
check "aggregate counts the one email left" "$WE" "1"
Z=$(echo "$LIST" | jq -r '.recent[] | select(.part=="Supercharger") | .zip')
check "junk zip stored as null" "$Z" "null"
TOTAL=$(echo "$LIST" | jq '.total')
check "total requests so far" "$TOTAL" "4"

# ── owner digest: send once, then throttle ──────────────────────────────────
echo "── owner digest"
D1=$(curl -s -X POST -H "x-admin-secret: $ADMIN_SECRET" "$API/v1/admin/coverage/digest/run")
check "digest sends when new requests exist (DEV log-send)" "$(echo "$D1" | jq '.sent')" "true"
check "digest covers all 4 requests" "$(echo "$D1" | jq '.requests')" "4"
D2=$(curl -s -X POST -H "x-admin-secret: $ADMIN_SECRET" "$API/v1/admin/coverage/digest/run")
check "second digest within 24h is throttled" "$(echo "$D2" | jq -r '.reason')" "throttled"
grep -q "DEV coverage digest → owner@example.com" "$OUT/dev.log" \
  && ok "digest addressed to OWNER_EMAIL" || bad "digest addressed to OWNER_EMAIL"

# ── per-IP rate limit (10/hour on the public POST) ──────────────────────────
echo "── rate limit"
# 8 POSTs consumed above; the limiter runs before validation so all count.
S=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/v1/coverage/request" -H 'content-type: application/json' -d '{"kind":"part","part":"widget 9"}')
check "request 9 of 10 still accepted" "$S" "200"
S=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/v1/coverage/request" -H 'content-type: application/json' -d '{"kind":"part","part":"widget 10"}')
check "request 10 of 10 still accepted" "$S" "200"
S=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/v1/coverage/request" -H 'content-type: application/json' -d '{"kind":"part","part":"widget 11"}')
check "request 11 rate-limited (429)" "$S" "429"

echo
echo "coverage e2e: $PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]
