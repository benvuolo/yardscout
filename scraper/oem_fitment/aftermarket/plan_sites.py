#!/usr/bin/env python3
"""List aftermarket sites for the crawl matrix (oem-aftermarket-crawl.yml).

    plan_sites.py --want all|site[,site...] [--branch oem-raw]

A site qualifies when an aftermarket/*.py module declares SITE = "..." and
STATUS = "ok", and oem-raw has neither aftermarket/raw/<site>.done nor
.blocked. Prints `sites=<json list>` for $GITHUB_OUTPUT.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def adapter_sites() -> list[str]:
    out = []
    for f in sorted(HERE.glob("*.py")):
        t = f.read_text()
        m = re.search(r'^SITE\s*=\s*"([^"]+)"', t, re.M)
        if m and re.search(r'^STATUS\s*=\s*"ok"', t, re.M) and re.search(r"^def product\(", t, re.M):
            out.append(m.group(1))
    return sorted(set(out))


def plan(want: str, exists) -> list[str]:
    sites = adapter_sites()
    if want.strip() != "all":
        wanted = {x.strip() for x in want.split(",") if x.strip()}
        sites = [s for s in sites if s in wanted]
    return [s for s in sites if not exists(f"aftermarket/raw/{s}.done") and not exists(f"aftermarket/raw/{s}.blocked")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--want", default="all")
    ap.add_argument("--branch", default="oem-raw")
    a = ap.parse_args()

    def exists(path: str) -> bool:
        return subprocess.run(["git", "cat-file", "-e", f"{a.branch}:{path}"], capture_output=True).returncode == 0

    print("sites=" + json.dumps(plan(a.want, exists)))


if __name__ == "__main__":
    main()
