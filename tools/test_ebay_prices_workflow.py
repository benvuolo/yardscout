#!/usr/bin/env python3
"""Offline test: the "Commit if changed" step of .github/workflows/ebay-prices.yml.

While there are no eBay keys the refresh step only warns and writes no
docs/data/ebay_prices.json; the commit step then failed on `git add` of a path
that does not exist, so the workflow went red every Monday (ops/ebay.md,
2026-11-16). This runs the step's own shell, taken from the workflow file, in
a scratch repository:
  - no bands file            -> exit 0, "no bands file yet"   (was: exit != 0)
  - file tracked, unchanged  -> exit 0, "nothing to commit"
  - file new or changed      -> committed and pushed, exit 0

Run: python3 tools/test_ebay_prices_workflow.py
(WORKFLOW=<another copy of the yml> tests that copy.)
"""
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = pathlib.Path(os.environ.get("WORKFLOW") or ROOT / ".github/workflows/ebay-prices.yml")

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        fails += 1


def step_script(text, step_name):
    """The `run: |` block of the named step, dedented. No YAML library needed."""
    lines = text.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.strip() == f"- name: {step_name}")
    j = next(k for k in range(i + 1, len(lines)) if lines[k].strip() == "run: |")
    indent = len(lines[j]) - len(lines[j].lstrip()) + 2
    out = []
    for ln in lines[j + 1:]:
        if ln.strip() and len(ln) - len(ln.lstrip()) < indent:
            break
        out.append(ln[indent:])
    return "\n".join(out) + "\n"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def scratch_repo(tmp):
    """A clone on branch main with a local bare `origin`, like the Actions checkout."""
    origin, work = tmp / "origin.git", tmp / "work"
    git(tmp, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp, "init", "-q", "-b", "main", str(work))
    for k, v in (("user.name", "t"), ("user.email", "t@example.com"), ("commit.gpgsign", "false")):
        git(work, "config", k, v)
    (work / "docs/data").mkdir(parents=True)
    (work / "README").write_text("x\n")
    git(work, "add", "README")
    git(work, "commit", "-q", "-m", "init")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "-u", "origin", "main")
    return work, origin


def run_step(script, work):
    return subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], cwd=work, capture_output=True, text=True, timeout=120)


def main():
    script = step_script(WORKFLOW.read_text(), "Commit if changed")
    check("the step's shell was found in the workflow", "git add docs/data/ebay_prices.json" in script)
    bands = "docs/data/ebay_prices.json"

    with tempfile.TemporaryDirectory() as d:
        work, origin = scratch_repo(pathlib.Path(d))
        r = run_step(script, work)
        check("no bands file (no keys): the step succeeds", r.returncode == 0, f"exit {r.returncode}: {(r.stdout + r.stderr).strip()[-200:]}")
        check("no bands file: it says so", "no bands file yet" in r.stdout, r.stdout.strip()[-120:])
        check("no bands file: nothing was committed", git(work, "rev-list", "--count", "HEAD").stdout.strip() == "1")

    with tempfile.TemporaryDirectory() as d:
        work, origin = scratch_repo(pathlib.Path(d))
        (work / bands).write_text('{"a": 1}\n')
        r = run_step(script, work)
        check("a new bands file: committed and pushed", r.returncode == 0
              and git(origin, "log", "--format=%s", "-1", "main").stdout.startswith("chore: eBay price bands"),
              f"exit {r.returncode}: {(r.stdout + r.stderr).strip()[-200:]}")
        r = run_step(script, work)
        check("the same file again: nothing to commit", r.returncode == 0 and "nothing to commit" in r.stdout, r.stdout.strip()[-120:])
        (work / bands).write_text('{"a": 2}\n')
        r = run_step(script, work)
        check("a changed bands file: committed and pushed", r.returncode == 0
              and git(origin, "rev-list", "--count", "main").stdout.strip() == "3",
              f"exit {r.returncode}: {(r.stdout + r.stderr).strip()[-200:]}")

    print("\nALL PASS" if not fails else f"\n{fails} FAILURE(S)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
