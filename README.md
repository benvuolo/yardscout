# Junkyard Hunter

**Live app: https://benvuolo.github.io/junkyard-hunter/**

Spot the valuable "unobtanium" parts that common junkyard cars originally came with, and see typical resale ranges before you drive to the yard. This is an information tool — estimates, not income promises: parts may already be pulled, and condition decides everything. Scrapes live inventory from **~150 self-service yards across four national/regional chains**:

| Chain | Yards | Coverage |
|---|---|---|
| **Pick-n-Pull** | ~48 | West Coast heavy (CA/WA/OR/NV), plus TX, MO, IL, IN, OH, VA, RI, Canada |
| **LKQ Pick Your Part** (pyp.com) | ~60 | CA, TX, FL, plus MD, NC, SC, GA, TN, OH, IN, IL, WI, MI, KS, OK, CO, AL |
| **Pull-A-Part** (incl. former U-Pull-&-Pay yards) | ~36 | Southeast/Gulf (GA/AL/TN/LA/MS/NC/SC/KY/FL), OH, IN, PA, TX, AZ, NM, CO |
| **Tear-A-Part + Utah Pic-A-Part** | 4 | Utah (SLC, Ogden, Orem) |

It cross-references every car against a curated database of rare/valuable parts and shows you exactly what to pull, what it costs (when the yard publishes a real price list), what it sells for, and where to sell it.

No engines. No transmissions. Just parts you can carry out.

## Install on your phone

1. Open **https://benvuolo.github.io/junkyard-hunter/** in Safari (iPhone) or Chrome (Android)
2. iPhone: tap the Share button, then **Add to Home Screen**. Android: tap the menu, then **Install app**
3. Launch it from your home screen — it runs full-screen like a native app and keeps working offline with the last-loaded inventory

Inventory auto-refreshes every 6 hours via GitHub Actions (see `.github/workflows/scan.yml`).

## Repo layout

```
junkyard-hunter/
├── docs/                       # Web app — served by GitHub Pages
│   ├── index.html              # App shell (markup only; no build step)
│   ├── styles.css              # All styling
│   ├── data.js                 # Static datasets: parts database, yard directory
│   ├── app.js                  # App logic: loading, filtering, rendering, saved list, alerts
│   ├── sw.js                   # Service worker (offline + instant launch)
│   ├── manifest.webmanifest    # PWA manifest + icons (icon-*.png, apple-touch-icon.png)
│   └── data/                   # Generated JSONs the app fetches
│       ├── inventory_live.json     # Latest scrape (schema v2: compact rows + lookup tables)
│       ├── picknpull_pricing.json  # Real Pick-n-Pull part prices (472 parts)
│       ├── pyp_pricing.json        # Real LKQ Pick Your Part prices, per yard (--refresh-chain-pricing)
│       ├── pap_pricing.json        # Real Pull-A-Part prices, per yard (--refresh-chain-pricing)
│       ├── tearapart_pricing.json  # Real Tear-A-Part part prices (503 parts)
│       └── utpap_pricing.json      # Utah Pic-A-Part list prices (--refresh-utpap-pricing)
├── scraper/
│   ├── junkyard_scraper.py     # Python scraper + unobtanium parts database
│   ├── db.py                   # SQLite history tracking (inventory_history.db, gitignored)
│   └── watchlist.json          # Your alert rules (export from UI or hand-edit; commit for CI)
└── .github/workflows/scan.yml  # Auto-scan every 6 hours, commits fresh inventory
```

## Quick start

### 1. Clone / copy the folder

Copy the entire `junkyard-hunter/` folder to your personal machine. All you need is:

- `index.html`
- `junkyard_scraper.py`
- `picknpull_pricing.json`
- `tearapart_pricing.json`
- `utpap_pricing.json` (optional; run `python scraper/junkyard_scraper.py --refresh-utpap-pricing` to update from [Parts Pricelist](https://utpap.com/ogden-prices/))

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
# Scan the SLC-radius yards, output to terminal (rich table); add --national for all chains
python scraper/junkyard_scraper.py

# Scan and save JSON for the web app (include ALL vehicles)
python scraper/junkyard_scraper.py --json --all > inventory_live.json

# Watch mode — rescan every 6 hours
python scraper/junkyard_scraper.py --watch --save --all

# Just list all tracked unobtanium parts
python scraper/junkyard_scraper.py --list-parts

# Filter by make
python scraper/junkyard_scraper.py --list-parts --make toyota

# Optional: NHTSA VPIC VIN decode for trim-aware matching (slower; one HTTP per unique VIN)
python scraper/junkyard_scraper.py --json --all --decode-vins > inventory_live.json
# Same via env: JUNKYARD_DECODE_VINS=1
# Optional: VPIC_WORKERS=8 (default) parallel NHTSA calls; VPIC_DELAY_SEC=0 (default) or add delay if needed
# Decode only the highest carry-profit rows (after matching), not every VIN in the fleet:
# python scraper/junkyard_scraper.py --save --all --decode-vins-profit-top 10

# NATIONAL scan — every supported yard: Pick-n-Pull US+Canada, LKQ Pick Your Part
# (~60 yards), and Pull-A-Part (~36 yards). Utah chains are always included.
python scraper/junkyard_scraper.py --save --all --national --decode-vins-profit-top 10

# Refresh per-yard price lists for Pick Your Part + Pull-A-Part (writes
# pyp_pricing.json / pap_pricing.json; the 6-hour CI scan does this automatically)
python scraper/junkyard_scraper.py --refresh-chain-pricing
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
python scraper/junkyard_scraper.py --save --all
```

Optional: `SMTP_HOST` (default `smtp.gmail.com`), `SMTP_PORT` (default `587`).

```bash
# Watch mode with alerts — checks every 6 hours, notifies on new finds
python scraper/junkyard_scraper.py --watch --save --all
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

5. The workflow [`.github/workflows/scan.yml`](.github/workflows/scan.yml) runs **every 6 hours** and on **manual dispatch**. It runs `python scraper/junkyard_scraper.py --save --all`, commits `inventory_live.json` (and `watch_alerted.json` when present) if anything changed, and sends email when new watchlist matches appear. Alert dedupe in Actions is stored in `watch_alerted.json` at the repo root so you do not get repeat emails for the same vehicle.

**Manual run:** GitHub → **Actions** → **Junkyard Scan** → **Run workflow**.

### 7. GitHub Pages (optional — open the app on your phone)

1. Repo **Settings** → **Pages** → Build from branch **main** (or your default branch), folder **/ (root)**.
2. After the first workflow run, `index.html` and `inventory_live.json` are in the repo; Pages serves the site at `https://YOUR_USERNAME.github.io/REPO_NAME/`.
3. Open that URL on your phone (use **index.html** path if needed: `.../index.html`).

## Features

### Web app tabs

| Tab | What it shows |
|---|---|
| **Live** | Every vehicle across all scanned yards, demand-first cards with resale ranges. Filter by zip + radius, GPS, make, yard. |
| **Parts** | The full unobtanium database — every tracked vehicle and its valuable parts. |
| **Alerts** | Vehicle watchlist; browser notifications; phone push via ntfy; optional **email** (Gmail) + **GitHub Actions** every 6 hours. |

### Sell channel intelligence

Every part includes:
- **Where to sell** — eBay, Facebook Marketplace, model-specific forums (T4R.org, IH8MUD, NASIOC), local classifieds
- **Speed rating** — Fast / Medium / Slow (how quickly it typically sells)
- **Tips** — e.g., "Local pickup saves $70+ shipping". eBay ranges are national; Facebook Marketplace prices vary by area — check your local market.

### Pricing sources — real price lists only

Pull costs are shown **only** when they come from that yard's own published price list, and each chain's list is applied only to that chain's yards:

- **Pick-n-Pull**: real prices from their API (472 parts)
- **LKQ Pick Your Part**: per-yard price lists from pyp.com (~40 tracked parts × 60 yards)
- **Pull-A-Part**: per-yard price lists from their pricing API (~40 tracked parts × 35 yards)
- **Tear-A-Part / Utah Pic-A-Part**: published price lists

If no real price list covers a part, the app shows "check yard price list" and the value estimate becomes a resale-only range — it never invents a pull cost.

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
python scraper/junkyard_scraper.py --json --all > inventory_live.json
python3 -m http.server 8765
```

**Option C — just copy 4 files:**

If you're in a hurry, the absolute minimum you need is:
1. `index.html`
2. `junkyard_scraper.py`
3. `picknpull_pricing.json`
4. `tearapart_pricing.json`

Everything else is generated by the scraper. AirDrop those 4 files, run the scraper, start the server.

## Quarterly price review (accuracy loop)

Resale ranges are never edited automatically. The loop that keeps them honest:

- `scraper/validate_prices.py` ranks the top ~50 parts by live-inventory
  exposure (frequency × displayed high) and classifies each displayed range
  ACCURATE / INFLATED / UNDERSTATED / UNVERIFIABLE against market evidence.
  Evidence comes from `scraper/price_baseline.json` — the machine-readable
  ranges from the most recent **manual** audit (`price_validation_report.md`)
  — plus a polite fresh eBay-sold attempt each run (eBay bot-blocks CI IPs, so
  the source backs off after two failures instead of crashing; that's expected).
- `.github/workflows/price-review.yml` runs it on the 1st of Jan/Apr/Jul/Oct
  (and on dispatch). If anything classifies INFLATED, or the report changed
  materially (DB drift vs. reviewed evidence, verdict changes, or new
  high-exposure parts with no reviewed evidence), it opens a
  `chore/price-review-<date>` PR with the regenerated report — never merging
  and never touching prices. Quiet quarters produce no PR.
- `PRICES_LAST_REVIEWED` in `scraper/junkyard_scraper.py` is exported into the
  v2 JSON and shown in the app footer ("Value ranges last reviewed …"). Bump it
  (and refresh `price_baseline.json`) whenever corrections from a review PR are
  accepted.

## Crush-risk signal (lot lifespan)

The history DB records when each vehicle appears and departs. From departed
vehicles the scraper computes an **average lot lifespan** per yard (lifespan =
departure date minus the yard-reported arrival date, so it's meaningful even
with a short scan history). Guards:

- A yard's own average is used only with **30+ recorded departures**; otherwise
  it falls back to the chain average, then the global average — the basis
  ships in the data (`avgLifespanDays` / `lifespanBasis` in the v2 yards table)
  and the UI says which one it's quoting.
- Cards show "Day 34 of ~45 typical at this yard" and a "Leaving soon (est.)"
  state past ~80% of the average. Cars past **2x** the average have already
  outlived it, so they get factual copy ("past the ~45-day typical") instead of
  false urgency, and rank below the genuine leaving window in the
  "Leaving soonest" sort.
- No usable history → no signal shown at all.

## Shareable finds

Every car has a deep link (`#car=<vin-or-id>`). The share button on each card
uses `navigator.share` on mobile (clipboard fallback elsewhere) and shares
"2010 Mercury Mountaineer — Row 30 at Pick-n-Pull - Salt Lake City, arrived
Jun 4" plus the link. Opening a shared link shows a focused single-car view
(ignoring the viewer's filters and zip state, with a "See all cars" action);
dead links get an honest "no longer in the current inventory" message.

## Incremental VIN decoding (trim accuracy)

Every scheduled scan runs `--decode-vins-incremental`:

- **Persistent cache**: decodes live in the `vin_decodes` table of
  `scraper/inventory_history.db` (persisted between CI runs by the Actions
  cache). VINs are immutable, so entries never expire — a previously-seen VIN
  costs zero API calls forever.
- **Capped drain**: only never-seen VINs hit the NHTSA vPIC API, newest
  arrivals first, capped by `VPIC_MAX_PER_RUN` (CI uses 5000). The initial
  backlog drains across successive 6-hour runs; steady-state runs only decode
  the day's new arrivals.
- **Disaster insurance**: the cache is exported to
  `docs/data/vin_decodes.json.gz` and committed, but only after ~20k new
  decodes accumulate — frequent multi-MB commits would bloat git history. If
  the Actions cache is ever evicted, the scraper re-imports the gz on start
  and at most re-decodes the recent delta.

### Accuracy rules (trim-gated parts)

- A trim-specific part is **"VIN-confirmed"** only when a *usable* decode
  (specific trim, not NHTSA's all-trims blob) names that trim. Ambiguous
  decodes never gate or un-gate parts.
- When the trim can't be confirmed from the VIN or the yard's listing title,
  the part is shown as **"if equipped — trim unconfirmed"** and only counts
  toward the *high* end of the value range.
- When a usable decode names a *different* trim, the part is excluded — the
  only case where absence is certain enough to drop it.
- When the VIN's factory decode contradicts the yard listing (year/make), the
  VIN is trusted for matching but the discrepancy is flagged on the card
  (&#9888; "VIN decodes as 2005 (listed 2004)") — the lot sign is what a
  visitor sees, so it's never silently overridden. Sub-brands that NHTSA
  reports under the parent make (Scion→Toyota etc.) are not flagged.

## Pro waitlist (fake door — no payments yet)

The web app gates value data (resale ranges, pull costs, demand badges), saves
beyond 5 cars, and instant push alerts behind a **Pro** upgrade sheet. There is
no real billing — the sheet is a waitlist email capture to measure demand.

- **Signups arrive as ntfy pushes**: subscribe to the topic `jh-pro-waitlist-7g4kx2m`
  in the ntfy app (or `curl -s "https://ntfy.sh/jh-pro-waitlist-7g4kx2m/json?poll=1"`
  for anything still in ntfy's ~12-hour cache). Each message contains the email,
  which locked feature triggered the sheet, and a timestamp. Keep the phone
  subscribed so nothing is lost; swap in a Formspree endpoint
  (`WAITLIST_NTFY_TOPIC` in `docs/app.js`) for durable storage later.
- Each browser also keeps its own submissions in `localStorage.jh_waitlist_log`.
- **Demo the unlocked experience**: open the app with `?pro=1` (or tap the
  footer version string 7 times). `?pro=0` re-locks. Client-side gating is
  bypassable by design in this phase.

## Data sources

| Source | Method | Notes |
|---|---|---|
| Pick-n-Pull | JSON API (`picknpull.com/api/vehicle/search`) | Public, no auth needed; `distance=0` = national |
| LKQ Pick Your Part | Server-rendered inventory pages (`pyp.com`) | 20 rows/page per store; store list + coords embedded on /inventory/ |
| Pull-A-Part | JSON microservices (`inventoryservice.pullapart.com`) | Anonymous website token; one search per make covers all yards |
| U-Pull-&-Pay | — merged into Pull-A-Part | Former UPAP yards (Albuquerque, Denver, Aurora, Colorado Springs, Cincinnati, ...) are in the Pull-A-Part feed |
| Tear-A-Part SLC + Ogden | WordPress AJAX (`tearapart.com/wp-admin/admin-ajax.php`) | Requires a nonce token (auto-fetched) |
| PnP part pricing | JSON API (`picknpull.com/api/parts/list/{storeId}`) | |
| PYP part pricing | JSON API (`pyp.com/DesktopModules/pyp_api/api/PriceList/`) | Per-location price lists |
| PAP part pricing | JSON API (`enterpriseservice.pullapart.com/partprice/...`) | Per-location price lists |
| TAP part pricing | Static price list (bundled in `tearapart_pricing.json`) | Manually sourced |
| Resale estimates | eBay sold listings research + community pricing | Validated March 2026 |
| Sell channels | eBay, FB Marketplace, T4R.org, IH8MUD, etc. | eBay national; FB Marketplace varies by local market |

## Requirements

- Python 3.10+
- `requests` — HTTP client
- `beautifulsoup4` — HTML parsing (used for nonce extraction)
- `rich` — Pretty terminal output (optional, falls back to plain text)
- A web browser (for the UI)
- No Node.js, no databases
- Optional: Gmail App Password for email alerts (free); GitHub Actions uses repo **Secrets** (not stored in code)
