# Junkyard Hunter

Find valuable "unobtanium" parts on common junkyard cars in Utah and flip them for profit. Scrapes live inventory from **Pick-n-Pull (SLC)**, **Tear-A-Part (SLC + Ogden)**, and **Utah Pic-A-Part (Ogden + Orem)** (XML feeds covering standard and premium lot rows, with VINs), cross-references against a curated database of rare/valuable parts, and shows you exactly what to pull, what it costs, what it sells for, and where to sell it.

No engines. No transmissions. Just parts you can carry out.

## What's in the box

```
junkyard-hunter/
├── index.html                # Single-file web app (HTML/CSS/JS, no build step)
├── junkyard_scraper.py       # Python scraper + unobtanium database
├── inventory_live.json       # Latest scrape: `{schemaVersion, scrapedAt (UTC ISO), vehicles[]}` (older runs may be a bare array)
├── picknpull_pricing.json    # Real Pick-n-Pull part prices (472 parts)
├── tearapart_pricing.json    # Real Tear-A-Part part prices (503 parts)
├── utpap_pricing.json        # Utah Pic-A-Part list prices (from utpap.com/1064Carpricelist.php; refresh with --refresh-utpap-pricing)
├── tearapart_inventory.json  # Cached Tear-A-Part raw inventory
├── inventory_data.json       # Cached raw inventory snapshot
├── watchlist.json            # Your alert rules (export from UI or hand-edit; commit for CI)
├── watch_alerted.json        # Dedupe state for email alerts in GitHub Actions (auto-created in CI)
└── .cache/                   # Local alert dedupe + seen-vehicle tracking (auto-created)
```

## Quick start

### 1. Clone / copy the folder

Copy the entire `junkyard-hunter/` folder to your personal machine. All you need is:

- `index.html`
- `junkyard_scraper.py`
- `picknpull_pricing.json`
- `tearapart_pricing.json`
- `utpap_pricing.json` (optional; run `python junkyard_scraper.py --refresh-utpap-pricing` to update from [Parts Pricelist](https://utpap.com/ogden-prices/))

The JSON inventory files are regenerated every time you run the scraper.

### 2. Set up Python

Requires **Python 3.10+** (tested on 3.13).

```bash
cd junkyard-hunter

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install requests beautifulsoup4 rich
```

### 3. Run the scraper

```bash
# Scan both yards, output to terminal (rich table)
python junkyard_scraper.py

# Scan and save JSON for the web app (include ALL vehicles)
python junkyard_scraper.py --json --all > inventory_live.json

# Watch mode — rescan every 6 hours
python junkyard_scraper.py --watch --save --all

# Just list all tracked unobtanium parts
python junkyard_scraper.py --list-parts

# Filter by make
python junkyard_scraper.py --list-parts --make toyota

# Optional: NHTSA VPIC VIN decode for trim-aware matching (slower; one HTTP per unique VIN)
python junkyard_scraper.py --json --all --decode-vins > inventory_live.json
# Same via env: JUNKYARD_DECODE_VINS=1
# Optional: VPIC_WORKERS=8 (default) parallel NHTSA calls; VPIC_DELAY_SEC=0 (default) or add delay if needed
# Decode only the highest carry-profit rows (after matching), not every VIN in the fleet:
# python junkyard_scraper.py --save --all --decode-vins-profit-top 10

# NATIONAL scan — every Pick-n-Pull yard in the US + Canada (~49 yards), one API call per make.
# Tear-A-Part and Utah Pic-A-Part are Utah-only chains and are always included as-is.
python junkyard_scraper.py --save --all --national --decode-vins-profit-top 10
```

### Phone push notifications (ntfy — free, no account)

1. Install the **ntfy** app ([iOS](https://apps.apple.com/us/app/ntfy/id1625396347) / Android).
2. Pick a hard-to-guess topic name, e.g. `junkyard-hunter-bv-8k2j`, and **subscribe** to it in the app.
3. Run the scraper with `NTFY_TOPIC=junkyard-hunter-bv-8k2j` in the environment
   (locally or as a GitHub Actions secret `NTFY_TOPIC`).

Watchlist hits then push straight to your phone. Up to 12 hits are sent as
individual notifications; more than that collapses into one summary. Email
alerts (if SMTP is configured) arrive as a single digest per run.

Watchlist entries in `watchlist.json` accept an optional `"states"` list to
scope alerts on national scans, e.g. `{"make": "Toyota", "model": "4Runner",
"states": ["UT", "NV"]}` — omit it to get hits from every yard nationwide.

```bash
```

VPIC uses the public [decodevinvaluesextended](https://vpic.nhtsa.dot.gov/api/) API (no key). When the API returns a **single** trim (or ≤2 comma-separated trims), that text is merged into trim matching for parts that list a `trim` requirement; each vehicle row then includes **`vpicDecodeWell`: true** in JSON and a **“VIN trim OK”** badge in the UI. Some manufacturers return a **long comma-separated list of every trim** for the model; those are treated as **ambiguous** (`vpicDecodeWell`: false) and matching falls back to the yard’s year/make/model only (so we do not false-positive trim-specific parts).

### 4. Start the web app

The app loads `inventory_live.json` via `fetch()`, so you need a local HTTP server (browsers block `fetch` from `file://` URLs).

```bash
# Must run from the junkyard-hunter folder (where index.html lives), or you get 404
cd junkyard-hunter

python3 -m http.server 8765

# Open in your browser
open http://localhost:8765/index.html
```

That's it. No npm, no webpack, no build step.

### 5. Set up alerts (optional)

Add vehicles to your watchlist in the Alerts tab of the web app, then click "Export for Scraper" to download a `watchlist.json` file. Place it in the `junkyard-hunter/` folder next to the scraper.

When you run the scraper (especially in `--watch` mode), it reads `watchlist.json` and sends **macOS desktop notifications** when a watched vehicle appears.

**Email (phone via Gmail app):** set these environment variables before running the scraper. Uses Gmail SMTP; no extra Python packages.

```bash
export SMTP_USER="you@gmail.com"
export SMTP_PASS="xxxx xxxx xxxx xxxx"   # Gmail App Password, not your login password
export ALERT_EMAIL="you@gmail.com"       # where to receive alerts (can match SMTP_USER)
python junkyard_scraper.py --save --all
```

Optional: `SMTP_HOST` (default `smtp.gmail.com`), `SMTP_PORT` (default `587`).

```bash
# Watch mode with alerts — checks every 6 hours, notifies on new finds
python junkyard_scraper.py --watch --save --all
```

You can also hand-edit `watchlist.json`:
```json
[
  {"make": "Toyota", "model": "Tacoma", "yrMin": null, "yrMax": null, "matchOnly": true},
  {"make": "Toyota", "model": "4Runner", "yrMin": 1996, "yrMax": 2002, "matchOnly": true},
  {"make": "Jeep", "model": "Wrangler", "yrMin": null, "yrMax": null, "matchOnly": false}
]
```

### 6. GitHub Actions (runs every 6 hours, email alerts, free)

Use this when you want the scraper to run **without your laptop being on**, and get **emails on your phone** (Gmail app).

You do **not** need to be logged into GitHub or Gmail on the machine where you develop. Push from any machine that has your personal GitHub auth, then add secrets in the browser.

1. **Create a repo** on your personal GitHub account (private is fine) and push **this folder as the repo root** (so `junkyard_scraper.py` is at the top level).

2. **Gmail App Password** (on your phone or any browser, logged into your Google account):
   - Enable 2-Step Verification on the Google account.
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords), create one for Mail, copy the 16-character password.

3. **Repository secrets** (GitHub → your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**):
   - `SMTP_USER` — your Gmail address
   - `SMTP_PASS` — the App Password (spaces optional)
   - `ALERT_EMAIL` — where to send alerts (usually the same Gmail; you get push notifications from the Gmail app)

4. **Commit `watchlist.json`** to the repo (export from the Alerts tab or create by hand). Without it, the workflow still updates inventory but sends no watchlist emails.

5. The workflow [`.github/workflows/scan.yml`](.github/workflows/scan.yml) runs **every 6 hours** and on **manual dispatch**. It runs `python junkyard_scraper.py --save --all`, commits `inventory_live.json` (and `watch_alerted.json` when present) if anything changed, and sends email when new watchlist matches appear. Alert dedupe in Actions is stored in `watch_alerted.json` at the repo root so you do not get repeat emails for the same vehicle.

**Manual run:** GitHub → **Actions** → **Junkyard Scan** → **Run workflow**.

### 7. GitHub Pages (optional — open the app on your phone)

1. Repo **Settings** → **Pages** → Build from branch **main** (or your default branch), folder **/ (root)**.
2. After the first workflow run, `index.html` and `inventory_live.json` are in the repo; Pages serves the site at `https://YOUR_USERNAME.github.io/REPO_NAME/`.
3. Open that URL on your phone (use **index.html** path if needed: `.../index.html`).

## Features

### Web app tabs

| Tab | What it shows |
|---|---|
| **Live Inventory** | Every vehicle in both yards, color-coded green→red by profit potential. Sortable by profit, freshness, sell speed, etc. |
| **Profit Breakdown** | Per-part profit table with real yard costs (PnP + TAP), resale estimates, ROI, freshness decay, and where to sell each part. |
| **Value Database** | The full unobtanium database — every tracked vehicle and its valuable parts. |
| **Part Explorer** | Search/filter individual parts across all vehicles. |
| **Alerts** | Vehicle watchlist; browser notifications; macOS alerts; optional **email** (Gmail) + **GitHub Actions** every 6 hours. |

### Sell channel intelligence

Every part includes:
- **Where to sell** — KSL Classifieds, eBay, Facebook Marketplace, T4R.org, IH8MUD, NASIOC, etc.
- **Speed rating** — Fast / Medium / Slow (how quickly it typically sells)
- **Tips** — e.g., "Local pickup saves $70+ shipping" or "Huge 3rd-gen community in UT, sells in days"

### Pricing sources

- **Pick-n-Pull**: Real prices pulled from their API (472 parts)
- **Tear-A-Part**: Real prices from their published price list (503 parts)
- Parts not found in either list show an estimated cost with an "est" badge

### Freshness scoring

Newer arrivals are more likely to still have valuable parts. The app applies a time-decay multiplier:

| Days since added | Freshness |
|---|---|
| 0–3 days | 100% |
| 4–7 days | 90% |
| 8–14 days | 75% |
| 15–30 days | 55% |
| 30+ days | 35% |

### Trim & generation matching

Parts are matched to the actual vehicle, not just the model:
- STI Brembo calipers only show on WRX STI, not base Impreza
- TRD Pro grille only shows on 2014+ 4Runners
- 3rd gen headlights won't show on a 5th gen, etc.

## CLI reference

```
usage: junkyard_scraper.py [-h] [--json] [--all] [--watch] [--interval N]
                           [--list-parts] [--make MAKE] [--save]

options:
  --json          Output JSON to stdout (pipe to file)
  --all           Include vehicles with no unobtanium match
  --watch         Continuous mode — rescan on interval
  --interval N    Seconds between scans in watch mode (default: 21600 = 6hr)
  --list-parts    Print the full unobtanium parts database
  --make MAKE     Filter --list-parts by make (e.g., toyota)
  --save          Write JSON directly to inventory_live.json
```

## Easiest way to move this to another machine

**Option A — zip and transfer:**
```bash
# From this machine
cd /path/to/admin
zip -r junkyard-hunter.zip junkyard-hunter/ \
  -x "junkyard-hunter/.venv/*" \
  -x "junkyard-hunter/.cache/*" \
  -x "junkyard-hunter/scraper_err.log"

# Transfer the zip however you like (AirDrop, USB, email, etc.)
# On the new machine, unzip and follow Quick Start above
```

**Option B — git (recommended if you want to keep it updated):**
```bash
# Initialize a standalone repo
cd junkyard-hunter
git init
# .gitignore is already in this project; or: echo -e ".venv/\n.cache/\n*.log\n..." > .gitignore
git add -A
git commit -m "Initial commit — Junkyard Hunter"

# Push to your personal GitHub
gh repo create junkyard-hunter --private --source=. --push
# OR
git remote add origin git@github.com:YOUR_USERNAME/junkyard-hunter.git
git push -u origin main

# On the new machine
git clone git@github.com:YOUR_USERNAME/junkyard-hunter.git
cd junkyard-hunter
python3 -m venv .venv && source .venv/bin/activate
pip install requests beautifulsoup4 rich
python junkyard_scraper.py --json --all > inventory_live.json
python3 -m http.server 8765
```

**Option C — just copy 4 files:**

If you're in a hurry, the absolute minimum you need is:
1. `index.html`
2. `junkyard_scraper.py`
3. `picknpull_pricing.json`
4. `tearapart_pricing.json`

Everything else is generated by the scraper. AirDrop those 4 files, run the scraper, start the server.

## Data sources

| Source | Method | Notes |
|---|---|---|
| Pick-n-Pull SLC | JSON API (`picknpull.com/api/vehicle/search`) | Public, no auth needed |
| Tear-A-Part SLC + Ogden | WordPress AJAX (`tearapart.com/wp-admin/admin-ajax.php`) | Requires a nonce token (auto-fetched) |
| PnP part pricing | JSON API (`picknpull.com/api/parts/list/{storeId}`) | Store 74 = SLC |
| TAP part pricing | Static price list (bundled in `tearapart_pricing.json`) | Manually sourced |
| Resale estimates | eBay sold listings research + community pricing | Validated March 2026 |
| Sell channels | KSL, eBay, FB Marketplace, T4R.org, IH8MUD, etc. | Based on real market research |

## Requirements

- Python 3.10+
- `requests` — HTTP client
- `beautifulsoup4` — HTML parsing (used for nonce extraction)
- `rich` — Pretty terminal output (optional, falls back to plain text)
- A web browser (for the UI)
- No Node.js, no databases
- Optional: Gmail App Password for email alerts (free); GitHub Actions uses repo **Secrets** (not stored in code)
