#!/usr/bin/env bash
# tools/regress.sh: the whole regression, one test at a time, under the shared
# test lock. Exit 0 only when every test passed; 1 when anything failed, was
# skipped or left a server behind; 2 on a usage error.
#
#   tools/regress.sh            full run (about an hour and a half)
#   tools/regress.sh --quick    units, scraper and tools tests only (minutes)
#   tools/regress.sh --list     print what would run, then stop (no lock)
#   tools/regress.sh --only RE  only tests whose name matches the regex RE
#   tools/regress.sh --out DIR  logs and summary in DIR (default
#                               /tmp/ys-regress/<UTC time>)
#
# What runs, in this order (each test its own log, DIR/logs/<name>.log; one
# line per test in DIR/summary.txt and on screen):
#   unit      backend/test/*_unit.mjs, backend/site-proxy/test/*_unit.mjs
#   scraper   scraper/test_*.py                         (python3 scraper/test_x.py)
#   tools     tools/test_*.py (the workflow-step tests)
#   browser   backend/test/*_e2e.mjs and *_e2e.py that are self-contained
#   api       backend/test/e2e.sh, e2e-ops.sh, e2e-devices.sh, e2e-coverage.sh,
#             e2e-email.sh, browser_e2e.py               (wrangler dev + mocks)
#   layout    backend/test/ui_no_truncation.mjs at its six widths, as two
#             halves side by side (320,375,390 and 430,768,1280; each serves
#             docs/ on a port the OS picks, so they cannot collide)
# --quick runs the unit, scraper and tools groups only.
#
# Left out on purpose (not self-contained), with the reason:
#   backend/test/map_regions_e2e.mjs   needs tiles.openfreemap.org and unpkg.com
#   backend/test/alerts_e2e.mjs        needs a wrangler dev on :8788 started by
#                                      test/e2e-alerts.sh, which no longer exists
#   backend/test/billing_e2e.py        needs a wrangler dev on :8788 started by hand
#   backend/test/{device_alerts,ops,email_alerts,recap_signup,free_email_alert}_e2e.mjs
#                                      API drivers: each runs inside its shell
#                                      suite above (they need its server)
#   backend/site-proxy/test/e2e.sh     overwrites backend/site-proxy/.dev.vars
#                                      (a developer's local file); run it by hand
#
# The lock: the script takes `flock /tmp/ys-test.lock` itself (other sessions
# run their server and browser tests under the same lock) and holds it for the
# whole run, so the tests inside it are started WITHOUT flock (a second flock
# on the same file from a child would wait forever). Never run it under flock.
#
# Servers: every suite that starts one stops it on exit and refuses a taken
# port (backend/test/servers.sh). Before each test the runner notes which of
# the fixed test ports are free; a port that is listening afterwards was left
# by that test, which then counts as failed ("left a server on :8794").
# Nothing is killed by the runner: a server it did not start is not its to
# stop.
#
# Needs: node 22, python3, Playwright (node and python), jq, curl, lsof or
# /dev/tcp, backend/node_modules (wrangler; `npm ci` in backend/). A group
# whose tool is missing is SKIPPED with the reason, and a skip fails the run.
#
# For the runner's own test only (backend/test/regress_unit.mjs):
# YS_TEST_LOCK replaces the lock file and YS_REGRESS_PORTS the watched ports.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="${YS_TEST_LOCK:-/tmp/ys-test.lock}"
QUICK=0; LIST=0; ONLY=''; OUTDIR=''
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1 ;;
    --list) LIST=1 ;;
    --only) ONLY="${2:-}"; shift ;;
    --out) OUTDIR="${2:-}"; shift ;;
    -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "regress.sh: unknown option $1 (see --help)" >&2; exit 2 ;;
  esac
  shift
done

# Take the lock once, for the whole run (unless only listing).
if [ "$LIST" = 0 ] && [ -z "${YS_REGRESS_HOLDS_LOCK:-}" ]; then
  if ! flock -n "$LOCK" true 2>/dev/null; then
    echo "regress.sh: waiting for $LOCK (another session's test is running)..."
  fi
  ARGS=()
  [ "$QUICK" = 1 ] && ARGS+=(--quick)
  [ -n "$ONLY" ] && ARGS+=(--only "$ONLY")
  [ -n "$OUTDIR" ] && ARGS+=(--out "$OUTDIR")
  exec env YS_REGRESS_HOLDS_LOCK=1 flock "$LOCK" bash "$0" ${ARGS[@]+"${ARGS[@]}"}
fi

cd "$ROOT" || exit 2
OUTDIR="${OUTDIR:-/tmp/ys-regress/$(date -u +%Y%m%d-%H%M%S)}"
LOGS="$OUTDIR/logs"
SUMMARY="$OUTDIR/summary.txt"
[ "$LIST" = 1 ] || { mkdir -p "$LOGS" && : > "$SUMMARY"; }

# Every fixed port a test here uses (and wrangler's inspector, 9229).
TEST_PORTS="${YS_REGRESS_PORTS:-8619 8631 8788 8791 8792 8793 8794 8795 8797 8798 8799 9229}"
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
free_ports() { local p out=''; for p in $TEST_PORTS; do port_busy "$p" || out="$out $p"; done; echo "$out"; }

NPASS=0; NFAIL=0; NSKIP=0; FAILED=()
line() { echo "$1" | tee -a "$SUMMARY"; }

# run GROUP NAME TIMEOUT_S CMD...  (CMD runs from the repo root)
run() {
  local group="$1" name="$2" t="$3"; shift 3
  if [ -n "$ONLY" ] && ! [[ "$name" =~ $ONLY ]]; then return 0; fi
  if [ "$LIST" = 1 ]; then printf '%-8s %s\n' "$group" "$name"; return 0; fi
  local log="$LOGS/$(echo "$name" | tr '/' '_').log" before after start rc left='' p
  before=$(free_ports)
  start=$(date +%s)
  timeout --kill-after=30 "$t" "$@" > "$log" 2>&1 < /dev/null
  rc=$?
  after=$(free_ports)
  for p in $before; do case " $after " in *" $p "*) ;; *) left="$left :$p" ;; esac; done
  local secs=$(( $(date +%s) - start )) status
  if [ "$rc" = 0 ] && [ -z "$left" ]; then status=PASS; NPASS=$((NPASS+1))
  else
    status="FAIL"; NFAIL=$((NFAIL+1)); FAILED+=("$name|$log")
    [ "$rc" = 124 ] && status="FAIL (timeout ${t}s)"
    [ "$rc" != 0 ] && [ "$rc" != 124 ] && status="FAIL (exit $rc)"
    [ -n "$left" ] && status="$status (left a server on$left)"
  fi
  line "$(printf '%-22s %5ss  %-8s %s' "$status" "$secs" "$group" "$name")"
}
skip() {  # GROUP NAME REASON
  if [ -n "$ONLY" ] && ! [[ "$2" =~ $ONLY ]]; then return 0; fi
  if [ "$LIST" = 1 ]; then printf '%-8s %s   (would be skipped: %s)\n' "$1" "$2" "$3"; return 0; fi
  NSKIP=$((NSKIP+1)); FAILED+=("$2|")
  line "$(printf '%-22s %5s   %-8s %s  (%s)' 'SKIP' '-' "$1" "$2" "$3")"
}

[ "$LIST" = 1 ] || line "regress.sh $( [ "$QUICK" = 1 ] && echo --quick ) on $(git rev-parse --short HEAD 2>/dev/null) ($(git rev-parse --abbrev-ref HEAD 2>/dev/null)), $(date -u +%Y-%m-%dT%H:%M:%SZ); logs in $LOGS"

HAVE_WRANGLER=1; [ -x backend/node_modules/.bin/wrangler ] || HAVE_WRANGLER=0
HAVE_PW_NODE=1; ( cd backend/test && node -e "require('module').createRequire(process.cwd() + '/x.js')('playwright')" ) >/dev/null 2>&1 || HAVE_PW_NODE=0
HAVE_PW_PY=1; python3 -c 'import playwright.sync_api' >/dev/null 2>&1 || HAVE_PW_PY=0
HAVE_JQ=1; command -v jq >/dev/null 2>&1 || HAVE_JQ=0

# ---- unit ----
for f in backend/test/*_unit.mjs backend/site-proxy/test/*_unit.mjs; do
  [ -e "$f" ] && run unit "$f" 600 node "$f"
done
# ---- scraper ----
for f in scraper/test_*.py; do
  [ -e "$f" ] && run scraper "$f" 900 python3 "$f"
done
# ---- tools ----
for f in tools/test_*.py; do
  [ -e "$f" ] && run tools "$f" 300 python3 "$f"
done

if [ "$QUICK" = 0 ]; then
  # ---- browser (self-contained) ----
  NOT_SELF_CONTAINED=" map_regions_e2e.mjs alerts_e2e.mjs billing_e2e.py browser_e2e.py device_alerts_e2e.mjs ops_e2e.mjs email_alerts_e2e.mjs recap_signup_e2e.mjs free_email_alert_e2e.mjs "
  for f in backend/test/*_e2e.mjs; do
    case "$NOT_SELF_CONTAINED" in *" $(basename "$f") "*) continue ;; esac
    if [ "$HAVE_PW_NODE" = 1 ]; then run browser "$f" 1500 node "$f"; else skip browser "$f" "node Playwright not found"; fi
  done
  for f in backend/test/*_e2e.py; do
    case "$NOT_SELF_CONTAINED" in *" $(basename "$f") "*) continue ;; esac
    if [ "$HAVE_PW_PY" = 1 ]; then run browser "$f" 1500 python3 "$f"; else skip browser "$f" "python Playwright not found"; fi
  done
  # ---- api (wrangler dev + mocks) ----
  for s in e2e.sh e2e-ops.sh e2e-devices.sh e2e-coverage.sh e2e-email.sh; do
    if [ "$HAVE_WRANGLER" = 0 ]; then skip api "backend/test/$s" "no backend/node_modules: run npm ci in backend/"
    elif [ "$HAVE_JQ" = 0 ] && { [ "$s" = e2e.sh ] || [ "$s" = e2e-coverage.sh ]; }; then skip api "backend/test/$s" "jq not found"
    else run api "backend/test/$s" 1800 bash "backend/test/$s"; fi
  done
  if [ "$HAVE_WRANGLER" = 0 ] || [ "$HAVE_PW_PY" = 0 ]; then skip api backend/test/browser_e2e.py "needs wrangler and python Playwright"
  else run api backend/test/browser_e2e.py 1800 python3 backend/test/browser_e2e.py; fi
  # ---- layout: six widths as two halves side by side ----
  if [ -n "$ONLY" ] && ! [[ "ui_no_truncation" =~ $ONLY ]]; then :
  elif [ "$LIST" = 1 ]; then printf '%-8s %s\n' layout 'backend/test/ui_no_truncation.mjs WIDTHS=320,375,390 | WIDTHS=430,768,1280 (side by side)'
  elif [ "$HAVE_PW_NODE" = 0 ]; then skip layout backend/test/ui_no_truncation.mjs "node Playwright not found"
  else
    start=$(date +%s)
    ( WIDTHS=320,375,390 timeout --kill-after=30 5400 node backend/test/ui_no_truncation.mjs > "$LOGS/ui_no_truncation_a.log" 2>&1 < /dev/null; echo $? > "$LOGS/.ui_a.rc" ) &
    ( WIDTHS=430,768,1280 timeout --kill-after=30 5400 node backend/test/ui_no_truncation.mjs > "$LOGS/ui_no_truncation_b.log" 2>&1 < /dev/null; echo $? > "$LOGS/.ui_b.rc" ) &
    wait
    secs=$(( $(date +%s) - start ))
    for half in a b; do
      rc=$(cat "$LOGS/.ui_$half.rc" 2>/dev/null || echo 99); rm -f "$LOGS/.ui_$half.rc"
      w=$([ "$half" = a ] && echo 320,375,390 || echo 430,768,1280)
      if [ "$rc" = 0 ]; then st=PASS; NPASS=$((NPASS+1)); else st="FAIL (exit $rc)"; NFAIL=$((NFAIL+1)); FAILED+=("ui_no_truncation $w|$LOGS/ui_no_truncation_$half.log"); fi
      line "$(printf '%-22s %5ss  %-8s %s' "$st" "$secs" layout "backend/test/ui_no_truncation.mjs WIDTHS=$w")"
    done
  fi
fi

[ "$LIST" = 1 ] && exit 0
line "──── $NPASS passed, $NFAIL failed, $NSKIP skipped$( [ "$QUICK" = 1 ] && echo ' (--quick: units, scraper and tools tests only)' ) ────"
if [ "${#FAILED[@]}" -gt 0 ]; then
  echo
  echo "Not passed (last 20 lines of each log):"
  for x in "${FAILED[@]}"; do
    n="${x%%|*}"; l="${x#*|}"
    echo "── $n"
    if [ -n "$l" ] && [ -f "$l" ]; then tail -20 "$l" | sed 's/^/   /'; else echo "   (skipped: see the summary line)"; fi
  done
  exit 1
fi
exit 0
