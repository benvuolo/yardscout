#!/usr/bin/env python3
"""One CI job per hosting platform (platforms.py): crawl the platform's sites
one at a time in round-robin turns.

    python3 platform_crawl.py --sites "a b c" --run-number N [--timeout-min 350]

Per turn: markers.mode decides "crawl" / "complete" / nothing; crawl.py runs
for the turn's minutes; ci_audit.py checks the evidence (exit 20 pauses the
site); ci_push_raw.sh checkpoints raw/<site>.* to oem-raw.

Guards (hub 2026-11-10):
- a site whose crawl.py exits with an unexpected code (not 0, 10, 11) is
  skipped for the rest of the run, and so is a site with 2 consecutive
  network-failure exits (11), so a broken site is not retried every round;
- a turn starts only if elapsed + turn + 10 minutes fits the job timeout
  minus 10 minutes, so the last checkpoint push happens before the runner
  kills the job.
The loop logic is `drive()`, with injectable callables for tests.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import markers  # noqa: E402
import platforms  # noqa: E402

OK_RC = {0, 10, 11}        # done / turn time up / network-failure streak
MAX_NET_STREAK = 2
PUSH_MARGIN_MIN = 10       # audit + push after the last turn
TIMEOUT_MARGIN_MIN = 10    # stay this far inside timeout-minutes


def drive(sites, run_number, timeout_min, *, mode_of, run_crawl, run_audit, push, pause, log,
          clock=time.time, sleep=time.sleep):
    """Run turns until no site has work, every site is skipped, or the
    budget would be exceeded. Returns the list of turns [(site, mode, rc)]."""
    order = platforms.rotation(sites, run_number)
    turn = platforms.slice_minutes(len(order))
    limit = (timeout_min - TIMEOUT_MARGIN_MIN) * 60
    start = clock()
    skip, streak, turns = set(), {}, []
    log(f"{len(order)} sites, {turn}-minute turns, order: {' '.join(order)}")
    while True:
        active = False
        for s in order:
            if s in skip:
                continue
            m = mode_of(s)
            if m is None:
                continue
            if clock() - start + (turn + PUSH_MARGIN_MIN) * 60 > limit:
                log(f"budget: no time for another {turn}-minute turn; stopping")
                return turns
            active = True
            rc = run_crawl(s, m, turn)
            if run_audit(s) == 20:
                pause(s)
            push(s)
            turns.append((s, m, rc))
            if rc == 11:
                streak[s] = streak.get(s, 0) + 1
                if streak[s] >= MAX_NET_STREAK:
                    skip.add(s)
                    log(f"{s}: {streak[s]} network-failure exits in a row; skipped for the rest of this run")
                else:
                    sleep(120)
            else:
                streak[s] = 0
            if rc not in OK_RC:
                skip.add(s)
                log(f"{s}: crawl.py exit {rc} (unexpected); skipped for the rest of this run")
        if not active:
            log("nothing left this run" if len(skip) < len(order) else "every site skipped this run")
            return turns


def _mode_of(site):
    wl = json.loads((HERE / "worklist.json").read_text()).get("sites", {}).get(site)
    return markers.mode(site, wl, lambda n: (HERE / "raw" / n).exists())


def _summary(text):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a") as fh:
            fh.write(text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sites", required=True)
    ap.add_argument("--run-number", type=int, default=int(os.environ.get("GITHUB_RUN_NUMBER", "0")))
    ap.add_argument("--timeout-min", type=int, default=350)
    a = ap.parse_args(argv)
    plat = os.environ.get("PLATFORM_JOB", "?")

    def log(msg):
        print(f"[platform {plat}] {msg}", flush=True)

    def run_crawl(site, mode, minutes):
        os.environ["SITE"] = site
        args = [sys.executable, "crawl.py", "--site", site, "--minutes", str(minutes)]
        if mode == "complete":
            args += ["--complete", "auto"]
        log(f"== {site}: mode {mode}, turn {minutes} min")
        rc = subprocess.run(args, cwd=HERE).returncode
        tail = (HERE / "raw" / f"{site}.log")
        lines = tail.read_text(errors="ignore").splitlines()[-3:] if tail.exists() else []
        print("\n".join(lines), flush=True)
        _summary(f"## {site} (rc {rc})\n```\n" + "\n".join(lines) + "\n```\n")
        return rc

    def run_audit(site):
        r = subprocess.run([sys.executable, "ci_audit.py", "--site", site], cwd=HERE, capture_output=True, text=True)
        print(r.stdout, end="", flush=True)
        _summary(r.stdout)
        return r.returncode

    def pause(site):
        (HERE / "raw" / f"{site}.paused").write_text(
            f"evidence mismatch above 0.5%: paused for review {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        print(f"::error::{site} paused by the evidence audit", flush=True)

    def push(site):
        rc = subprocess.run(["bash", str(HERE / "ci_push_raw.sh"), site], cwd=HERE).returncode
        if rc:
            print(f"::error::checkpoint push failed for {site}", flush=True)

    drive(a.sites.split(), a.run_number, a.timeout_min, mode_of=_mode_of, run_crawl=run_crawl,
          run_audit=run_audit, push=push, pause=pause, log=log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
