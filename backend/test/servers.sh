# Sourced by every shell suite that starts a server (wrangler dev, the mock
# Resend / FCM / Play servers). Two rules, both from 2026-11-17, when
# e2e.sh failed 3 of 39 because it talked to a server an earlier run had left
# on its port:
#
#   1. A suite stops everything it started when it exits, however it exits
#      (normal end, a failed check, `exit`, Ctrl-C, SIGTERM from a runner).
#      `npx wrangler dev` is a tree (npx -> node wrangler -> node -> workerd)
#      and killing the npx PID, or walking its children after a middle
#      process has gone, leaves workerd holding the port. So each server is
#      started in a process group of its own (setsid) and the whole group is
#      stopped: TERM, then KILL after 5 s.
#   2. A suite refuses to start, with a clear message and exit code 2, when a
#      port it is about to use is already taken: it never talks to someone
#      else's server.
#
# Use:
#   source "$(dirname "$0")/servers.sh"      # sets the EXIT / INT / TERM traps
#   ys_need_port "$PORT" "wrangler dev"      # before starting anything on it
#   ys_start "$OUT/dev.log" npx wrangler dev --port "$PORT" ...
#   DEV_PID=$YS_LAST_PID
#   ys_stop "$DEV_PID" "$PORT"               # stop one early (e.g. to restart it)
#   ys_on_exit 'rm -f .dev.vars.e2e'         # extra cleanup, run after the stops
#
# A server killed with SIGKILL cannot clean up; the next run's ys_need_port
# then says so instead of testing against it.

YS_GROUPS=()          # process-group ids this script started
YS_EXIT_CMDS=()       # extra cleanup, in order
YS_LAST_PID=''

# True when something accepts connections on 127.0.0.1:PORT (or, per lsof,
# listens on it on any address).
ys_port_busy() {
  local port="$1"
  if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then return 0; fi
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then return 0; fi
  return 1
}

# Refuse to start when PORT is taken. WHAT names the server for the message.
ys_need_port() {
  local port="$1" what="${2:-a server}" who=''
  ys_port_busy "$port" || return 0
  if command -v lsof >/dev/null 2>&1; then
    who=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NR > 1 { print "    pid " $2 " (" $1 ")" }' | sort -u)
  fi
  {
    echo "REFUSING TO START: port $port, needed for $what by $(basename "$0"), is already in use."
    [ -n "$who" ] && echo "$who"
    echo "  Another test is running, or an earlier run left a server behind."
    echo "  Stop it (kill <pid>), or pick another port (this suite reads YS_TEST_PORT / YS_MOCK_PORT or PORT / MOCKPORT)."
  } >&2
  exit 2
}

# Start CMD... in the background in its own process group, output to LOG.
# Sets YS_LAST_PID (= the group id).
ys_start() {
  local log="$1"; shift
  if command -v setsid >/dev/null 2>&1; then
    setsid "$@" >"$log" 2>&1 < /dev/null &
  else
    # No setsid (not Linux): job control gives the job its own group.
    set -m; "$@" >"$log" 2>&1 < /dev/null & set +m
  fi
  YS_LAST_PID=$!
  YS_GROUPS+=("$YS_LAST_PID")
}

# Is anything of group PGID still alive?
ys_group_alive() { kill -0 -- "-$1" 2>/dev/null; }

# Stop process group PGID (TERM, then KILL after 5 s). With PORT, wait up to
# 10 s for the port to close and fail loudly if it does not.
ys_stop() {
  local pgid="$1" port="${2:-}" i
  [ -n "$pgid" ] || return 0
  if ys_group_alive "$pgid"; then
    kill -TERM -- "-$pgid" 2>/dev/null || true
    for i in $(seq 1 50); do ys_group_alive "$pgid" || break; sleep 0.1; done
    ys_group_alive "$pgid" && kill -KILL -- "-$pgid" 2>/dev/null || true
  fi
  # A plain PID (not a group leader) as a last resort.
  kill "$pgid" 2>/dev/null || true
  wait "$pgid" 2>/dev/null || true
  local keep=() g
  for g in ${YS_GROUPS[@]+"${YS_GROUPS[@]}"}; do [ "$g" = "$pgid" ] || keep+=("$g"); done
  YS_GROUPS=(${keep[@]+"${keep[@]}"})
  if [ -n "$port" ]; then
    for i in $(seq 1 100); do ys_port_busy "$port" || return 0; sleep 0.1; done
    echo "WARNING: port $port is still in use after stopping group $pgid" >&2
    return 1
  fi
  return 0
}

ys_on_exit() { YS_EXIT_CMDS+=("$1"); }

ys_stop_all() {
  local g c
  for g in ${YS_GROUPS[@]+"${YS_GROUPS[@]}"}; do ys_stop "$g" >/dev/null 2>&1 || true; done
  for c in ${YS_EXIT_CMDS[@]+"${YS_EXIT_CMDS[@]}"}; do eval "$c" || true; done
  YS_EXIT_CMDS=()
}

# EXIT runs on every normal end and on `exit` (set -e failures included);
# INT / TERM turn into an exit so EXIT runs too.
trap 'rc=$?; ys_stop_all; exit $rc' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
