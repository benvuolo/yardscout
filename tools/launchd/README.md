# YardScout launchd snapshot jobs

Four macOS launchd agents run daily on the dev Mac to snapshot junkyard sites
whose hosts block datacenter IPs (GitHub Actions / Cloudflare Workers egress get
403/520/521, residential IPs get clean 200s). Each job runs a script from this
repo, commits the snapshot to `scraper/snapshots/`, and pushes to `origin main`.
The CI scan's adapters fall back to these snapshots whenever their live fetches
fail.

**These jobs are machine-local by necessity** (they exist precisely because CI
IPs are blocked). If the Mac dies, the only loss is snapshot freshness — the
last pushed snapshots stay in the repo and keep working until you re-create the
jobs on a new residential-IP machine.

## The jobs

| Label | Schedule (local) | Script (in repo) | What it does |
|---|---|---|---|
| `io.yardscout.indy-snapshot` | daily 08:15 | `scraper/update_indy_snapshot.sh` | curl-snapshots Indy-U-Pull-It inventory + price pages (SiteGround blocks CI IPs) → `scraper/snapshots/indy_{inventory,prices}.html.gz` |
| `io.yardscout.ace-snapshot` | daily 08:25 | `scraper/update_ace_snapshot.sh` | runs the real Ace Pick-A-Part adapter (`junkyard_scraper.fetch_ace_inventory`) → `scraper/snapshots/ace_inventory.json.gz` + fresh `docs/data/ace_pricing.json` |
| `io.yardscout.papva-snapshot` | daily 08:35 | `scraper/update_papva_snapshot.sh` | runs the Pick-A-Part VA adapter (`fetch_papva_inventory`) → `scraper/snapshots/papva_inventory.json.gz` |
| `io.yardscout.upullr-snapshot` | daily 08:45 | `scraper/update_upullr_snapshot.sh` | runs the U-Pull-R Parts adapter (`fetch_upullr_inventory`, 3 yards MN/OH; CI gets 403 on getVehicles since 2026-10-21) → `scraper/snapshots/upullr_inventory.json.gz` + fresh `docs/data/upullr_pricing.json` |

Each plist logs stdout+stderr to `/tmp/yardscout_<name>_snapshot.log`.

All four scripts refuse to overwrite snapshots with failed/suspiciously small
crawls (marker checks, minimum row/vehicle counts) and skip the commit when
content is unchanged (`gzip -n` keeps unchanged content byte-identical).

## Re-setup on a fresh Mac

1. **Clone the repo** (the plists hardcode this path — edit them if you clone
   elsewhere):

   ```bash
   git clone https://github.com/benvuolo/yardscout.git \
     ~/PODIUM_SETUP/admin/junkyard-hunter
   ```

2. **Git push credentials** — the scripts `git push origin main`, so the Mac
   needs a GitHub token stored in the keychain (first manual
   `git push` with a PAT, or `git credential-osxkeychain` already configured).

3. **Python for the Ace/PAPVA jobs.** The scripts default to the asdf install
   `~/.asdf/installs/python/3.14.3t/bin/python3` (deliberately NOT the asdf
   shim — launchd's bare PATH can't exec shims). Either reproduce that
   (`asdf install python 3.14.3t`) or point the jobs at any Python ≥3.12 by
   adding an `EnvironmentVariables` dict with `YARDSCOUT_PYTHON` to the plists.
   Install the scraper deps into that interpreter:

   ```bash
   <your-python> -m pip install curl_cffi beautifulsoup4 lxml requests
   ```

   (The Indy job needs no Python — just `curl`, `gzip`, `git`.)

4. **Install + load the agents:**

   ```bash
   cp tools/launchd/io.yardscout.*.plist ~/Library/LaunchAgents/
   # if the repo is NOT at ~/PODIUM_SETUP/admin/junkyard-hunter, fix the
   # script paths inside the plists first.
   launchctl load ~/Library/LaunchAgents/io.yardscout.indy-snapshot.plist
   launchctl load ~/Library/LaunchAgents/io.yardscout.ace-snapshot.plist
   launchctl load ~/Library/LaunchAgents/io.yardscout.papva-snapshot.plist
   launchctl load ~/Library/LaunchAgents/io.yardscout.upullr-snapshot.plist
   ```

5. **Smoke-test one** (runs immediately, check the log):

   ```bash
   launchctl start io.yardscout.indy-snapshot
   tail -f /tmp/yardscout_indy_snapshot.log
   ```

Note: `StartCalendarInterval` jobs that miss their window (Mac asleep) run once
on wake, so a laptop that sleeps overnight still snapshots daily.

## Adding a job to a Mac that already has the others

```bash
cd ~/PODIUM_SETUP/admin/junkyard-hunter && git pull origin main
cp tools/launchd/io.yardscout.upullr-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/io.yardscout.upullr-snapshot.plist
launchctl start io.yardscout.upullr-snapshot      # first run now (~4 min)
tail -f /tmp/yardscout_upullr_snapshot.log
```

The script exits 1 without committing when the crawl is blocked from the Mac
too or comes back suspiciously small; the log says which.
