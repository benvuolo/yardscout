#!/bin/bash
# End-to-end test of the entitlements API against a local `wrangler dev`.
# Covers: the full Stripe-webhook → request-code → redeem-code → status round
# trip, rate/attempt limits, offline StoreKit JWS verification (happy path +
# tamper + wrong product), Google Play verify-android (unconfigured 503, then
# every subscriptionsv2 state against a mocked androidpublisher — the Worker
# is restarted with the Google test vars for that phase), and webhook
# signature rejection.
#
# Usage: bash test/e2e.sh        (from backend/site-proxy/)
# Needs: node, openssl, curl, python3. Spawns wrangler dev on port 8799 and
# the Play mock (test/mock-play.mjs) on port 8798.
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
# npx -> wrangler -> workerd: kill the whole tree, or workerd keeps the port
# and the restart below silently talks to the OLD server (no Google vars).
kill_tree() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$c"; done; kill "$1" 2>/dev/null || true; }
trap 'kill_tree $WPID' EXIT
for i in $(seq 1 60); do
  sleep 1
  if curl -s -o /dev/null "$BASE/api/ent/status?token=$(printf '0%.0s' {1..64})"; then break; fi
  if ! kill -0 $WPID 2>/dev/null; then echo "wrangler dev died:"; tail -20 "$OUT/wrangler.log"; exit 1; fi
done

# NO content-type on purpose: real clients post "simple" requests (no CORS
# preflight); the Worker must parse JSON bodies regardless of content-type.
post() { curl -s -X POST "$BASE/api/ent/$1" -d "$2"; }

echo "── CORS: preflight + origin echo for the native app (case-insensitive hdrs)"
R=$(curl -s -i -X OPTIONS "$BASE/api/ent/verify-ios" -H 'Origin: capacitor://localhost' \
  -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type' \
  | tr 'A-Z' 'a-z')
assert "ACAO echoes capacitor origin" "$R" "access-control-allow-origin: capacitor://localhost"
assert "preflight cached a day" "$R" "access-control-max-age: 86400"
R=$(curl -s -i -X POST "$BASE/api/ent/request-code" -H 'Origin: capacitor://localhost' \
  -H 'content-type: application/json' -d '{"email":"cors@example.com"}' | tr 'A-Z' 'a-z')
assert "1.4-style JSON content-type still accepted" "$R" "on its way"
assert "POST response echoes origin too" "$R" "access-control-allow-origin: capacitor://localhost"

echo "── unknown endpoint + verify-android input checks / unconfigured 503"
R=$(curl -s "$BASE/api/ent/nope"); assert "unknown route → 404" "$R" "not_found"
# Input validation fires before the config check (bad requests stay 400s
# even on an unconfigured deploy); with no GOOGLE_* secrets in this phase,
# a well-formed request gets the honest not_configured 503.
R=$(post verify-android '{"purchaseToken":"tok-active-0000000000","email":"nope"}')
assert "bad email → bad_email" "$R" "bad_email"
R=$(post verify-android '{"purchaseToken":"x","email":"and@example.com"}')
assert "malformed token → bad_token" "$R" "bad_token"
R=$(post verify-android '{"purchaseToken":"tok-active-0000000000","email":"and@example.com"}')
assert "no Google secrets → not_configured" "$R" "not_configured"

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

# ────────────────────────────────────────────────────────────────────────
# Phase 2: verify-android against a mocked androidpublisher. The mock mints
# a real RSA keypair and verifies the Worker's RS256 service-account JWT, so
# the whole auth path (WebCrypto signing → oauth swap → bearer GET) runs for
# real. Wrangler is restarted because .dev.vars is read once at boot; KV
# state is kept (the earlier grants/limits don't collide with these emails).
# ────────────────────────────────────────────────────────────────────────
AND_EMAIL="androiduser@example.com"
AND_EMAIL2="androiduser2@example.com"
MOCKPORT=${MOCKPORT:-8798}

echo "── starting the Play mock on :$MOCKPORT + restarting wrangler with Google vars"
node test/mock-play.mjs $MOCKPORT "$OUT" > "$OUT/mock-play.log" 2>&1 &
MPID=$!
trap 'kill_tree $WPID; kill $MPID 2>/dev/null || true' EXIT
for i in $(seq 1 20); do
  sleep 0.5
  if curl -s -o /dev/null "http://127.0.0.1:$MOCKPORT/ping"; then break; fi
  if ! kill -0 $MPID 2>/dev/null; then echo "mock-play died:"; cat "$OUT/mock-play.log"; exit 1; fi
done

# GOOGLE_SA_KEY goes in as one line with literal \n escapes — exactly how a
# pasted JSON-key private_key arrives in production; google-play.js normalizes.
SA_KEY_ONELINE=$(awk 'BEGIN{ORS="\\n"} {print}' "$OUT/sa_key.pem")
cat >> .dev.vars <<EOF
GOOGLE_SA_EMAIL=test-sa@yardscout-test.iam.gserviceaccount.com
GOOGLE_SA_KEY=$SA_KEY_ONELINE
GOOGLE_TOKEN_URL_TEST=http://127.0.0.1:$MOCKPORT/token
GOOGLE_PLAY_API_URL_TEST=http://127.0.0.1:$MOCKPORT
EOF
kill_tree $WPID; wait $WPID 2>/dev/null || true
for i in $(seq 1 20); do curl -s -o /dev/null "$BASE/" || break; sleep 0.5; done   # port actually free
npx wrangler dev --port $PORT --local > "$OUT/wrangler2.log" 2>&1 &
WPID=$!
trap 'kill_tree $WPID; kill $MPID 2>/dev/null || true' EXIT
for i in $(seq 1 60); do
  sleep 1
  if curl -s -o /dev/null "$BASE/api/ent/status?token=$(printf '0%.0s' {1..64})"; then break; fi
  if ! kill -0 $WPID 2>/dev/null; then echo "wrangler dev died:"; tail -20 "$OUT/wrangler2.log"; exit 1; fi
done

echo "── verify-android: ACTIVE links the email (real JWT → oauth → GET)"
R=$(post verify-android "{\"purchaseToken\":\"tok-active-0000000000\",\"email\":\"$AND_EMAIL\"}")
assert "active sub links" "$R" '"linked":true'
R=$(post verify-android "{\"purchaseToken\":\"tok-active-0000000000\",\"email\":\"$AND_EMAIL\"}")
assert "re-verification is idempotent" "$R" '"linked":true'

echo "── android-linked email works in the code flow (source google_play)"
R=$(post request-code "{\"email\":\"$AND_EMAIL\"}")
CODE=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["dev_code"])')
R=$(post redeem-code "{\"email\":\"$AND_EMAIL\",\"code\":\"$CODE\"}")
assert "redeem for Play-linked email → pro" "$R" '"pro":true'
assert "source is google_play" "$R" '"source":"google_play"'
AND_TOKEN=$(echo "$R" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# State tests use their own email so AND_EMAIL's entitlement stays pinned to
# tok-active (the re-link test below depends on that pin being intact).
AND_EMAIL_STATES="androidstates@example.com"
echo "── subscriptionsv2 states: grace + canceled entitle, expired/on-hold don't"
R=$(post verify-android "{\"purchaseToken\":\"tok-grace-00000000000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "grace period (expiry -1d, house 3d grace) links" "$R" '"linked":true'
R=$(post verify-android "{\"purchaseToken\":\"tok-canceled-00000000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "canceled-but-not-expired links" "$R" '"linked":true'
R=$(post verify-android "{\"purchaseToken\":\"tok-expired-000000000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "expired → lapsed" "$R" "lapsed"
R=$(post verify-android "{\"purchaseToken\":\"tok-onhold-0000000000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "on-hold (future expiry!) → lapsed" "$R" "lapsed"

echo "── wrong product / bogus token / license-tester gate"
R=$(post verify-android "{\"purchaseToken\":\"tok-wrongproduct-0000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "wrong product rejected" "$R" "wrong_product"
R=$(post verify-android "{\"purchaseToken\":\"tok-bogus-00000000000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "unknown token → verify_failed" "$R" "verify_failed"
# testPurchase is accepted here ONLY because DEV_MODE=1 — the same gate as
# iOS Sandbox (prod needs ALLOW_SANDBOX_IAP=1 for license-tester validation).
R=$(post verify-android "{\"purchaseToken\":\"tok-testpurchase-0000\",\"email\":\"$AND_EMAIL_STATES\"}")
assert "license-tester purchase allowed under DEV_MODE" "$R" '"linked":true'

echo "── one email per Play subscription: re-link moves Pro"
R=$(post verify-android "{\"purchaseToken\":\"tok-active-0000000000\",\"email\":\"$AND_EMAIL2\"}")
assert "re-link to a new email works" "$R" '"linked":true'
R=$(curl -s "$BASE/api/ent/status?token=$AND_TOKEN")
assert "old email lost Pro after re-link" "$R" '"pro":false'

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ $FAIL = 0 ]
