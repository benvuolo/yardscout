#!/bin/bash
# Snapshot Pick-A-Part VA's (Fredericksburg + Stafford) inventory from THIS
# machine.
#
# WHY: pickapartva.com's Cloudflare returns HTTP 521 to GitHub Actions even
# through curl_cffi impersonate=chrome (2026-10-19 scan), while residential
# IPs get clean 200s. Same remedy as Ace/Indy: this script runs on the dev
# Mac via launchd (io.yardscout.papva-snapshot, daily 08:35), runs the real
# adapter from a residential IP, commits the normalized inventory to
# scraper/snapshots/papva_inventory.json.gz, and the CI scan's adapter falls
# back to the snapshot whenever its live crawl yields zero vehicles.
set -euo pipefail
cd "$(dirname "$0")/.."

# NOT the asdf shim — launchd's bare PATH has no `asdf` and the shim exec fails (127).
PY="${YARDSCOUT_PYTHON:-$HOME/.asdf/installs/python/3.14.3t/bin/python3}"
mkdir -p scraper/snapshots

"$PY" - <<'EOF'
import gzip, json, sys
from datetime import datetime, timezone
sys.path.insert(0, "scraper")
import junkyard_scraper as js

vehicles = js.fetch_papva_inventory()
# Refuse a failed/suspiciously small crawl (the two yards run ~7,200 cars;
# also require >= 60% of the previous snapshot to catch partial crawls).
prev = 0
snap_path = "scraper/snapshots/papva_inventory.json.gz"
try:
    prev = len(json.loads(gzip.decompress(open(snap_path, "rb").read()))["vehicles"])
except Exception:
    pass
floor = max(2000, int(prev * 0.6))
if len(vehicles) < floor:
    print(f"only {len(vehicles)} vehicles (floor {floor}, prev {prev}) — not snapshotting",
          file=sys.stderr)
    sys.exit(1)
payload = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "vehicles": vehicles}
with open(snap_path, "wb") as f:
    with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(json.dumps(payload, separators=(",", ":")).encode())
print(f"snapshotted {len(vehicles)} vehicles")
EOF

git add scraper/snapshots/papva_inventory.json.gz
git diff --cached --quiet && { echo "snapshot unchanged"; exit 0; }
git commit -q -m "chore: Pick-A-Part VA snapshot $(date +%F)"
git -c rebase.autoStash=true pull --rebase -q origin main
git push -q origin main
echo "snapshot pushed $(date)"
