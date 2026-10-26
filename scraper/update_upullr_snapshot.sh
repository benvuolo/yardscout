#!/bin/bash
# Snapshot U-Pull-R Parts' (Rosemount + East Bethel MN, Toledo OH) inventory
# from THIS machine.
#
# WHY: since 2026-10-21 every getVehicles POST to upullrparts.com's
# admin-ajax gateway returns HTTP 403 from GitHub Actions' datacenter IPs
# (getMakes still answers 200, the site's own search UI works from
# residential IPs), so the CI scan has been carrying the yard on stale-keep.
# Same situation and same remedy as Ace (update_ace_snapshot.sh): this script
# runs on the dev Mac via launchd (io.yardscout.upullr-snapshot, daily 08:45),
# runs the real adapter from a residential IP, commits the normalized
# inventory to scraper/snapshots/upullr_inventory.json.gz plus a fresh
# docs/data/upullr_pricing.json, and the CI scan's adapter falls back to the
# snapshot whenever its live crawl yields zero vehicles.
set -euo pipefail
cd "$(dirname "$0")/.."

# NOT the asdf shim — launchd's bare PATH has no `asdf` and the shim exec fails (127).
PY="${YARDSCOUT_PYTHON:-$HOME/.asdf/installs/python/3.14.3t/bin/python3}"
mkdir -p scraper/snapshots

"$PY" - <<'PYEOF'
import gzip, json, sys
from datetime import datetime, timezone
sys.path.insert(0, "scraper")
import junkyard_scraper as js

# The adapter itself falls back to the committed snapshot when live yields
# zero — snapshotting that would just re-commit the old file, so detect it.
snap_path = "scraper/snapshots/upullr_inventory.json.gz"
prev = 0
try:
    prev = len(json.loads(gzip.decompress(open(snap_path, "rb").read()))["vehicles"])
except Exception:
    pass
import io, contextlib
err = io.StringIO()
with contextlib.redirect_stderr(err):
    vehicles = js.fetch_upullr_inventory()
sys.stderr.write(err.getvalue())
if "using committed snapshot" in err.getvalue():
    print("live crawl failed from this machine too — not snapshotting", file=sys.stderr)
    sys.exit(1)
# Refuse a failed/suspiciously small crawl (the three yards run ~3,000 cars
# together; also require >= 60% of the previous snapshot's count).
floor = max(300, int(prev * 0.6))
if len(vehicles) < floor:
    print(f"only {len(vehicles)} vehicles (floor {floor}, prev {prev}) — not snapshotting",
          file=sys.stderr)
    sys.exit(1)
payload = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "vehicles": vehicles}
# mtime=0 so unchanged content = unchanged file (like gzip -n).
with open(snap_path, "wb") as f:
    with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(json.dumps(payload, separators=(",", ":")).encode())
print(f"snapshotted {len(vehicles)} vehicles across "
      f"{len({v['_location'] for v in vehicles})} yards")
js.refresh_upullr_pricing_file()
PYEOF

git add scraper/snapshots/upullr_inventory.json.gz docs/data/upullr_pricing.json
git diff --cached --quiet && { echo "snapshot unchanged"; exit 0; }
git commit -q -m "chore: U-Pull-R snapshot $(date +%F)"
git -c rebase.autoStash=true pull --rebase -q origin main
git push -q origin main
echo "snapshot pushed $(date)"
