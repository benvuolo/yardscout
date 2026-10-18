#!/bin/bash
# Snapshot Ace Pick-A-Part's (Jacksonville FL) inventory + price list from
# THIS machine.
#
# WHY: Cloudflare blanket-403s GitHub Actions' datacenter IPs on everything —
# the /search-inventory/ page AND every ajax.php POST (confirmed in the
# 2026-10-17/18 scan runs) — while serving residential IPs normally.
# robots.txt is allow-all, so this is generic datacenter-IP filtering, not an
# anti-scrape signal. Same situation and same remedy as Indy-U-Pull-It
# (update_indy_snapshot.sh): this script runs on the dev Mac via launchd
# (io.yardscout.ace-snapshot, daily 08:25), runs the real adapter from a
# residential IP, commits the normalized inventory to
# scraper/snapshots/ace_inventory.json.gz plus a fresh docs/data/
# ace_pricing.json, and the CI scan's adapter falls back to the snapshot
# whenever its live crawl yields zero vehicles.
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

vehicles = js.fetch_ace_inventory()
# Refuse to snapshot a failed/suspiciously small crawl (yard runs ~2,500 cars).
if len(vehicles) < 500:
    print(f"only {len(vehicles)} vehicles — not snapshotting", file=sys.stderr)
    sys.exit(1)
payload = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "vehicles": vehicles}
# mtime=0 so unchanged content = unchanged file (like gzip -n).
with open("scraper/snapshots/ace_inventory.json.gz", "wb") as f:
    with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(json.dumps(payload, separators=(",", ":")).encode())
print(f"snapshotted {len(vehicles)} vehicles")
js.refresh_ace_pricing_file()
EOF

git add scraper/snapshots/ace_inventory.json.gz docs/data/ace_pricing.json
git diff --cached --quiet && { echo "snapshot unchanged"; exit 0; }
git commit -q -m "chore: Ace Pick-A-Part snapshot $(date +%F)"
git -c rebase.autoStash=true pull --rebase -q origin main
git push -q origin main
echo "snapshot pushed $(date)"
