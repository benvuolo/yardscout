#!/bin/bash
# Snapshot Indy-U-Pull-It's inventory + price pages from THIS machine.
#
# WHY: the yard's host (SiteGround) hard-blocks both GitHub Actions' Azure
# ranges and Cloudflare Workers egress (connection resets / 520s), but serves
# residential IPs normally. robots.txt there is allow-all — it's generic
# datacenter-IP filtering, not an anti-scrape signal. So this script runs on
# the dev Mac via launchd (io.yardscout.indy-snapshot, daily 08:15), commits
# gzipped snapshots, and the CI scan's adapter falls back to them when its
# live fetches fail (scraper/junkyard_scraper.py: _indy_get_with_mirror).
set -euo pipefail
cd "$(dirname "$0")/.."

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
mkdir -p scraper/snapshots

INV=$(curl -s --max-time 90 -A "$UA" "https://indyupullit.com/vehicle-inventory/")
echo "$INV" | grep -q 'id="vehicles"' || { echo "inventory marker missing — not snapshotting"; exit 1; }
PRC=$(curl -s --max-time 90 -A "$UA" "https://indyupullit.com/price-list/")
[ "$(echo "$PRC" | grep -c '<td')" -gt 300 ] || { echo "price table too small — not snapshotting"; exit 1; }

# gzip -n: no timestamp in the header, so unchanged content = unchanged file.
printf '%s' "$INV" | gzip -9 -n > scraper/snapshots/indy_inventory.html.gz
printf '%s' "$PRC" | gzip -9 -n > scraper/snapshots/indy_prices.html.gz

git add scraper/snapshots
git diff --cached --quiet && { echo "snapshots unchanged"; exit 0; }
git commit -q -m "chore: Indy-U-Pull-It snapshot $(date +%F)"
git -c rebase.autoStash=true pull --rebase -q origin main
git push -q origin main
echo "snapshot pushed $(date)"
