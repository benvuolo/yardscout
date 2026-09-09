#!/usr/bin/env bash
# YardScout backend end-to-end test — fully local, no Cloudflare account needed.
#
# Spins up `wrangler dev` (workerd + local D1), seeds it with real inventory
# via scraper/push_inventory.py, then exercises the whole surface:
#   upload auth → radius query → tier filtering (anon vs free vs pro) →
#   magic-link flow (single-use, DEV_MODE logged link) → admin grant →
#   vehicle detail → logout.
#
# Usage: from backend/:  npm install && npm run test:e2e
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(cd .. && pwd)"
PORT="${YS_TEST_PORT:-8788}"
API="http://127.0.0.1:$PORT"
OUT="test/.out"
mkdir -p "$OUT"

UPLOAD_TOKEN="e2e-upload-token"
ADMIN_SECRET="e2e-admin-secret"

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ✓ $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  ✗ $1"; }
check(){ if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected [$3], got [$2])"; fi; }

command -v jq >/dev/null || { echo "jq is required"; exit 1; }

INVENTORY="${YS_TEST_INVENTORY:-$ROOT/docs/data/inventory_live.json}"
[ -f "$INVENTORY" ] || { echo "No inventory file at $INVENTORY"; exit 1; }

# ── isolated dev vars + fresh local D1 state ────────────────────────────────
cat > .dev.vars.e2e <<EOF
DEV_MODE=1
UPLOAD_TOKEN=$UPLOAD_TOKEN
ADMIN_SECRET=$ADMIN_SECRET
EOF
rm -rf "$OUT/wrangler-state"

echo "── applying migrations (local D1)"
npx wrangler d1 migrations apply yardscout-db --local \
  --persist-to "$OUT/wrangler-state" >"$OUT/migrate.log" 2>&1

echo "── starting wrangler dev on :$PORT"
npx wrangler dev --port "$PORT" --env-file .dev.vars.e2e \
  --persist-to "$OUT/wrangler-state" >"$OUT/dev.log" 2>&1 &
DEV_PID=$!
trap 'kill $DEV_PID 2>/dev/null; rm -f .dev.vars.e2e' EXIT

for i in $(seq 1 60); do
  sleep 1
  if curl -sf "$API/v1/health" >/dev/null 2>&1; then break; fi
  [ "$i" = 60 ] && { echo "wrangler dev never came up:"; tail -20 "$OUT/dev.log"; exit 1; }
done
ok "wrangler dev is up ($API)"

# ── ingestion auth ──────────────────────────────────────────────────────────
echo "── ingestion"
S=$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/admin/inventory/manifest")
check "manifest without token rejected" "$S" "401"
S=$(curl -s -o /dev/null -w '%{http_code}' -H "x-upload-token: wrong" "$API/v1/admin/inventory/manifest")
check "manifest with wrong token rejected" "$S" "401"
S=$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/inventory")
check "inventory before any upload → 503" "$S" "503"

python3 "$ROOT/scraper/push_inventory.py" --file "$INVENTORY" \
  --api "$API" --token "$UPLOAD_TOKEN" --max-yards 6 >"$OUT/push.log" 2>&1 \
  && ok "push_inventory.py seeded 6 yards (see test/.out/push.log)" \
  || { bad "push_inventory.py failed"; cat "$OUT/push.log"; }

# idempotent re-push should skip everything
python3 "$ROOT/scraper/push_inventory.py" --file "$INVENTORY" \
  --api "$API" --token "$UPLOAD_TOKEN" --max-yards 6 >"$OUT/push2.log" 2>&1
grep -q "^0 of .* shards changed" "$OUT/push2.log" \
  && ok "re-push skips unchanged shards (manifest diff)" \
  || bad "re-push did not skip unchanged shards"

# ── public inventory, anonymous (free variant) ──────────────────────────────
echo "── anonymous / free tier"
YARDS=$(curl -s "$API/v1/yards")
check "yard directory count" "$(echo "$YARDS" | jq '.yards | length')" "6"

# Yard 0 is Pick-n-Pull Rancho Cordova (38.577, -121.2605); 50mi around it.
PLAN=$(curl -s "$API/v1/inventory?lat=38.58&lng=-121.26&radius=50")
check "plan tier is free" "$(echo "$PLAN" | jq -r '.tier')" "free"
N_RADIUS=$(echo "$PLAN" | jq '.yardIds | length')
N_ALL=$(curl -s "$API/v1/inventory" | jq '.yardIds | length')
check "radius filter returns all 6 test yards for no-center" "$N_ALL" "6"
[ "$N_RADIUS" -ge 1 ] && [ "$N_RADIUS" -lt "$N_ALL" ] \
  && ok "radius=50mi narrows yards ($N_RADIUS of $N_ALL)" \
  || bad "radius filter did not narrow ($N_RADIUS of $N_ALL)"

SHARD_FREE=$(curl -s --compressed "$API/v1/inventory/shard/0")
NV=$(echo "$SHARD_FREE" | jq '.vehicles | length')
[ "$NV" -gt 100 ] && ok "free shard has vehicles ($NV)" || bad "free shard empty"
MAXVAL=$(echo "$SHARD_FREE" | jq '[.vehicles[][9]] | max')
check "free shard: every maxValue zeroed" "$MAXVAL" "0"

PS_FREE=$(curl -s --compressed "$API/v1/inventory/partsets")
check "free partsets: no dollar/demand fields" "$(echo "$PS_FREE" | jq '[.[][] | has("low") or has("high") or has("cost") or has("sell_speed") or has("sell_notes")] | any')" "false"
check "free partsets: part names present" "$(echo "$PS_FREE" | jq '.[0][0] | has("name")')" "true"

ETAG=$(curl -s --compressed -D - -o /dev/null "$API/v1/inventory/shard/0" | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')
S=$(curl -s -o /dev/null -w '%{http_code}' -H "if-none-match: $ETAG" "$API/v1/inventory/shard/0")
check "conditional GET honors ETag (304)" "$S" "304"

# ── magic-link auth flow ────────────────────────────────────────────────────
echo "── magic-link auth"
S=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' \
  -d '{"email":"not-an-email"}' "$API/v1/auth/request-link")
check "bad email rejected" "$S" "400"

LINK=$(curl -s -X POST -H 'content-type: application/json' \
  -d '{"email":"tester@example.com"}' "$API/v1/auth/request-link" | jq -r '.dev_link')
[[ "$LINK" == http*token=* ]] && ok "magic link issued (DEV_MODE)" || bad "no dev_link in response: $LINK"

LOC=$(curl -s -o /dev/null -w '%{redirect_url}' "$LINK")
[[ "$LOC" == *'#session='* ]] && ok "callback redirects with #session fragment" || bad "callback redirect: $LOC"
SESSION="${LOC#*#session=}"

LOC2=$(curl -s -o /dev/null -w '%{redirect_url}' "$LINK")
[[ "$LOC2" == *'login_error=used_token'* ]] && ok "magic link is single-use" || bad "token reuse allowed?! $LOC2"

ME=$(curl -s -H "authorization: Bearer $SESSION" "$API/v1/me")
check "session works, email echoed" "$(echo "$ME" | jq -r '.email')" "tester@example.com"
check "new user starts on free tier" "$(echo "$ME" | jq -r '.tier')" "free"

SHARD_AUTH_FREE=$(curl -s --compressed -H "authorization: Bearer $SESSION" "$API/v1/inventory/shard/0")
check "signed-in free user: values still stripped" "$(echo "$SHARD_AUTH_FREE" | jq '[.vehicles[][9]] | max')" "0"

# ── admin grant → pro tier data ─────────────────────────────────────────────
echo "── admin grant + pro tier"
S=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' \
  -d '{"email":"tester@example.com","tier":"pro"}' "$API/v1/admin/grant")
check "grant without secret rejected" "$S" "401"

G=$(curl -s -X POST -H "x-admin-secret: $ADMIN_SECRET" -H 'content-type: application/json' \
  -d '{"email":"tester@example.com","tier":"pro","note":"e2e"}' "$API/v1/admin/grant")
check "grant pro via admin secret" "$(echo "$G" | jq -r '.tier')" "pro"
check "grant reflected in /v1/me" "$(curl -s -H "authorization: Bearer $SESSION" "$API/v1/me" | jq -r '.tier')" "pro"

SHARD_PRO=$(curl -s --compressed -H "authorization: Bearer $SESSION" "$API/v1/inventory/shard/0")
MAXVAL_PRO=$(echo "$SHARD_PRO" | jq '[.vehicles[][9]] | max')
[ "$MAXVAL_PRO" -gt 0 ] && ok "pro shard: real maxValue present (\$$MAXVAL_PRO)" || bad "pro shard still stripped"
PS_PRO=$(curl -s --compressed -H "authorization: Bearer $SESSION" "$API/v1/inventory/partsets")
check "pro partsets: dollar fields present" "$(echo "$PS_PRO" | jq '.[0][0] | has("low") and has("high")')" "true"

USERS=$(curl -s -H "x-admin-secret: $ADMIN_SECRET" "$API/v1/admin/users")
check "admin user list shows the tester as pro" "$(echo "$USERS" | jq -r '.users[] | select(.email=="tester@example.com") | .tier')" "pro"

# expired grants resolve back to free
curl -s -X POST -H "x-admin-secret: $ADMIN_SECRET" -H 'content-type: application/json' \
  -d '{"email":"tester@example.com","tier":"pro","expires_at":"2020-01-01T00:00:00Z"}' \
  "$API/v1/admin/grant" >/dev/null
check "expired grant resolves to free" "$(curl -s -H "authorization: Bearer $SESSION" "$API/v1/me" | jq -r '.tier')" "free"
curl -s -X POST -H "x-admin-secret: $ADMIN_SECRET" -H 'content-type: application/json' \
  -d '{"email":"tester@example.com","tier":"pro"}' "$API/v1/admin/grant" >/dev/null

# ── vehicle detail (deep links) ─────────────────────────────────────────────
echo "── vehicle detail"
VID=$(echo "$SHARD_PRO" | jq -r '.vehicles[0][0]')
VVIN=$(echo "$SHARD_PRO" | jq -r '.vehicles[0][1]')
D=$(curl -s "$API/v1/vehicles/$VID")
check "detail by id finds the vehicle" "$(echo "$D" | jq -r '.vehicle.id')" "$VID"
check "anonymous detail: maxValue stripped" "$(echo "$D" | jq -r '.vehicle.maxValue')" "0"
DP=$(curl -s -H "authorization: Bearer $SESSION" "$API/v1/vehicles/$VID")
[ "$(echo "$DP" | jq -r '.vehicle.maxValue')" != "0" ] || [ "$(echo "$SHARD_PRO" | jq -r '.vehicles[0][9]')" = "0" ] \
  && ok "pro detail: maxValue present for pro session" || bad "pro detail stripped"
if [ -n "$VVIN" ] && [ "$VVIN" != "null" ]; then
  check "detail by VIN resolves too" "$(curl -s "$API/v1/vehicles/$VVIN" | jq -r '.vehicle.vin')" "$VVIN"
fi
S=$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/vehicles/does-not-exist-123")
check "unknown vehicle → 404" "$S" "404"

# ── logout ──────────────────────────────────────────────────────────────────
echo "── logout"
curl -s -X POST -H "authorization: Bearer $SESSION" "$API/v1/auth/logout" >/dev/null
S=$(curl -s -o /dev/null -w '%{http_code}' -H "authorization: Bearer $SESSION" "$API/v1/me")
check "session dead after logout" "$S" "401"

# ── CORS ────────────────────────────────────────────────────────────────────
echo "── CORS"
ACAO=$(curl -s -D - -o /dev/null -H "origin: https://benvuolo.github.io" "$API/v1/yards" \
  | tr -d '\r' | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2}')
check "allow-listed origin gets CORS" "$ACAO" "https://benvuolo.github.io"
ACAO2=$(curl -s -D - -o /dev/null -H "origin: https://evil.example" "$API/v1/yards" \
  | tr -d '\r' | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2}')
check "unknown origin gets no CORS grant" "${ACAO2:-none}" "none"

echo
echo "════ RESULT: $PASS passed, $FAIL failed ════"
[ "$FAIL" = 0 ]
