#!/usr/bin/env bash
# Checkpoint raw/<site>.* to the oem-raw branch worktree ($RAW_WORKTREE) and
# push it (CI only; platform_crawl.py calls it after every turn).
set -u
SITE="$1"
W="${RAW_WORKTREE:?RAW_WORKTREE not set}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cp "$HERE"/raw/"$SITE".* "$W/raw/" 2>/dev/null || true
cd "$W"
git add raw
if git diff --cached --quiet; then exit 0; fi
git commit -q -m "oem-raw: $SITE checkpoint $(date -u +%Y-%m-%dT%H:%MZ)"
for t in 1 2 3 4 5 6; do
  git push -q origin HEAD:oem-raw && exit 0
  git fetch -q origin oem-raw && git rebase -q FETCH_HEAD || git rebase --abort || true
  sleep $((t * 5))
done
echo "::error::could not push checkpoint"
exit 1
