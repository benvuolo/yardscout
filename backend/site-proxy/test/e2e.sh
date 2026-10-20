#!/bin/bash
# End-to-end test of the entitlements API against a local `wrangler dev`.
# Covers: the full Stripe-webhook → request-code → redeem-code → status round
# trip, rate/attempt limits, offline StoreKit JWS verification (happy path +
# tamper + wrong product), the Android stub, and webhook signature rejection.
#
# Usage: bash test/e2e.sh        (from backend/site-proxy/)
# Needs: node, openssl, curl, python3. Spawns wrangler dev on port 8799.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT=${PORT:-8799}
BASE="http://127.0.0.1:$PORT"
OUT=test/.out
WHSEC="whsec_testsecret123"
EMAIL="buyer@example.com"
IOS_EMAIL="iosuser@example.com"

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "  ✓ $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  ✗ $1  ← GOT: $2"; }
# assert <desc> <haystack> <needle>
assert() { case "$2" in *"$3"*) ok "$1";; *) bad "$1" "$2";; esac; }

echo "── generating test StoreKit chain + JWS"
rm -rf "$OUT"; mkdir -p "$OUT"
node test/make-test-jws.mjs "$OUT" >/dev/null
node test/make-test-jws.mjs "$OUT" '{"productId":"some_other_product"}' jws-wrongproduct.txt >/dev/null
JWS=$(cat "$OUT/jws.txt")
JWS_WRONG=$(cat "$OUT/jws-wrongproduct.txt")
ROOT_B64=$(cat "$OUT/root_b64.txt")

echo "── writing .dev.vars (DEV_MODE, test root, webhook secret)"
cat > .dev.vars <<EOF
DEV_MODE=1
STRIPE_WEBHOOK_SECRET=$WHSEC
APPLE_ROOT_CA_B64_TEST=$ROOT_B64
EOF

echo "── starting wrangler dev on :$PORT (fresh local KV state)"
rm -rf .wrangler/state
npx wrangler dev --port $PORT --local > "$OUT/wrangler.log" 2>&1 &
WPID=$!
trap 'kill $WPID 2>/dev/null || true' EXIT
for i in $(seq 1 60); do
  sleep 1
  if curl -s -o /dev/null "$BASE/api/ent/status?token=$(printf '0%.0s' {1..64})"; then break; fi
  if ! kill -0 $WPID 2>/dev/null; then echo "wrangler dev died:"; tail -20 "$OUT/wrangler.log"; exit 1; fi
done

post() { curl -s -X POST "$BASE/api/ent/$1" -H 'content-type: application/json' -d "$2"; }

echo "── unknown endpoint + Android stub"
R=$(post verify-android '{"purchaseToken":"x"}'); assert "verify-android is a 501 stub" "$R" "not_implemented"
R=$(curl -s "$BASE/api/ent/nope"); assert "unknown route → 404" "$R" "not_found"

echo "── checkout without Stripe configured"
R=$(post checkout '{}'); assert "checkout → billing_off 503" "$R" "billing_off"

echo "── request-code for an email with no entitlement (no oracle)"
R=$(post request-code "{\"email\":\"$EMAIL\"}")
assert "generic response" "$R" "on its way"
assert "dev flag says not found" "$R" '"dev_found":false'

echo "── Stripe webhook: bad signature rejected"
BODY='{"type":"checkout.session.completed","data":{"object":{}}}'
R=$(curl -s -X POST "$BASE/api/ent/stripe-webhook" -H 'stripe-signature: t=1,v1=deadbeef' -d "$BODY")
assert "bad signature → 400" "$R" "bad_signature"

sign_webhook() { # $1 = raw body ; echoes the stripe-signature header value
  local t sig
  t=$(date +%s)
  sig=$(printf '%s.%s' "$t" "$1" | openssl dgst -sha256 -hmac "$WHSEC" -hex | sed 's/^.*= //')
  echo "t=$t,v1=$sig"
}

echo "── Stripe webhook: checkout.session.completed grants Pro"
BODY=$(cat <<EOF
{"type":"checkout.session.completed","data":{"object":{"id":"cs_test_1","mode":"subscription","customer":"cus_test_1","customer_details":{"email":"$EMAIL"}}}}
EOF
)
R=$(curl -s -X POST "$BASE/api/ent/stripe-webhook" -H "stripe-signature: $(sign_webhook "$BODY")" -d "$BODY")
assert "webhook accepted" "$R" '"received":true'

echo "── request-code now sends (dev mode returns the code)"
R=$(post request-code "{\"email\":\"$EMAIL\"}")
assert "dev flag says found" "$R" '"dev_found":true'
CODE=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["dev_code"])')
[ ${#CODE} = 6 ] && ok "got a 6-digit code" || bad "got a 6-digit code" "$CODE"

echo "── redeem: wrong code rejected, right code mints a token (single use)"
R=$(post redeem-code "{\"email\":\"$EMAIL\",\"code\":\"000000\"}")
# (1-in-a-million flake if the real code IS 000000 — rerun if so.)
assert "wrong code → bad_code" "$R" "bad_code"
R=$(post redeem-code "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}")
assert "right code → pro" "$R" '"pro":true'
TOKEN=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
R=$(post redeem-code "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}")
assert "code is single-use" "$R" "bad_code"

echo "── status with the minted token"
R=$(curl -s "$BASE/api/ent/status?token=$TOKEN")
assert "status → pro:true" "$R" '"pro":true'
R=$(curl -s "$BASE/api/ent/status?token=$(printf 'a%.0s' {1..64})")
assert "bogus token → pro:false" "$R" '"token_valid":false'

echo "── rate limit: 3 codes / 15 min per email"
post request-code "{\"email\":\"$EMAIL\"}" >/dev/null
post request-code "{\"email\":\"$EMAIL\"}" >/dev/null
R=$(post request-code "{\"email\":\"$EMAIL\"}")
assert "4th request → slow_down" "$R" "slow_down"

echo "── subscription cancelled → Pro lapses"
BODY='{"type":"customer.subscription.deleted","data":{"object":{"id":"sub_1","customer":"cus_test_1","status":"canceled"}}}'
R=$(curl -s -X POST "$BASE/api/ent/stripe-webhook" -H "stripe-signature: $(sign_webhook "$BODY")" -d "$BODY")
assert "webhook accepted" "$R" '"received":true'
R=$(curl -s "$BASE/api/ent/status?token=$TOKEN")
assert "status → pro:false after cancel" "$R" '"pro":false'

echo "── subscription renewed → Pro returns (items-shape period end)"
PEND=$(( $(date +%s) + 2592000 ))
BODY="{\"type\":\"customer.subscription.updated\",\"data\":{\"object\":{\"id\":\"sub_1\",\"customer\":\"cus_test_1\",\"status\":\"active\",\"items\":{\"data\":[{\"current_period_end\":$PEND}]}}}}"
curl -s -X POST "$BASE/api/ent/stripe-webhook" -H "stripe-signature: $(sign_webhook "$BODY")" -d "$BODY" >/dev/null
R=$(curl -s "$BASE/api/ent/status?token=$TOKEN")
assert "status → pro:true after renewal" "$R" '"pro":true'

echo "── verify-ios: offline JWS verification"
R=$(post verify-ios "{\"email\":\"$IOS_EMAIL\",\"jws\":\"$JWS\"}")
assert "valid JWS links the email" "$R" '"linked":true'
TAMPERED=$(echo "$JWS" | sed 's/\./x./')
R=$(post verify-ios "{\"email\":\"$IOS_EMAIL\",\"jws\":\"$TAMPERED\"}")
assert "tampered JWS rejected" "$R" "verify_failed"
# Tamper the payload only (signature no longer matches)
H=$(echo "$JWS" | cut -d. -f1); P=$(echo "$JWS" | cut -d. -f2); S=$(echo "$JWS" | cut -d. -f3)
P2=$(python3 - <<EOF
import base64, json
p = "$P"; raw = base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))
d = json.loads(raw); d["expiresDate"] = 9999999999999
print(base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("="))
EOF
)
R=$(post verify-ios "{\"email\":\"$IOS_EMAIL\",\"jws\":\"$H.$P2.$S\"}")
assert "payload-swapped JWS rejected" "$R" "verify_failed"
R=$(post verify-ios "{\"email\":\"$IOS_EMAIL\",\"jws\":\"$JWS_WRONG\"}")
assert "wrong product rejected" "$R" "wrong_product"

echo "── iOS-linked email works in the code flow too"
R=$(post request-code "{\"email\":\"$IOS_EMAIL\"}")
CODE=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["dev_code"])')
R=$(post redeem-code "{\"email\":\"$IOS_EMAIL\",\"code\":\"$CODE\"}")
assert "redeem for iOS-linked email → pro" "$R" '"pro":true'
assert "source is apple_iap" "$R" '"source":"apple_iap"'

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ $FAIL = 0 ]
