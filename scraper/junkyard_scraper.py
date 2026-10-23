#!/usr/bin/env python3
"""
YardScout — Self-Service Junkyard Inventory Scraper
=========================================
Pulls LIVE inventory from Pick-n-Pull (SLC), Tear-A-Part (SLC + Ogden), and
Utah Pic-A-Part (Ogden + Orem) via public XML inventory feeds, cross-references
against the unobtanium database. Vehicle VINs are present when the source API
provides them (Pick-n-Pull, Tear-A-Part, and Utah Pic-A-Part XML).
Outputs JSON for the web app or a rich terminal report.

No engines. No transmissions. Just parts you can carry out and flip.

Usage:
    python junkyard_scraper.py                      # Scan & print results
    python junkyard_scraper.py --json               # Output JSON for web app
    python junkyard_scraper.py --json > inventory_live.json  # Save for UI (wrapped JSON with scrapedAt + vehicles)
    python junkyard_scraper.py --all                # Show ALL vehicles, not just matches
    python junkyard_scraper.py --watch              # Poll every 6 hours
    python junkyard_scraper.py --list-parts         # Show all tracked parts
    python junkyard_scraper.py --list-parts --make toyota
    python junkyard_scraper.py --json --decode-vins   # NHTSA VPIC trim (parallel; see README)
    python junkyard_scraper.py --save --all --decode-vins-profit-top 10   # VPIC only for top 10 rows by carry profit

    Optional: JUNKYARD_DECODE_VINS=1 enables VPIC without passing --decode-vins.

Requirements:
    pip install requests beautifulsoup4 rich

Email alerts (optional):
    SMTP_USER, SMTP_PASS, ALERT_EMAIL — Gmail App Password recommended.
    Optional: SMTP_HOST (default smtp.gmail.com), SMTP_PORT (default 587).
    In GitHub Actions, alert dedupe is written to watch_alerted.json at repo root.

Part price bands: UNOBTANIUM_DB stores anchor ranges; at match time they are
adjusted toward typical US used eBay sold resale (_resale_sold_calibrate).
Set JUNKYARD_RAW_PRICES=1 to disable adjustment (raw DB numbers).
"""

import argparse
import base64
import concurrent.futures
import hashlib
import html
import json
import os
import re
import smtplib
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install dependencies: pip install requests rich")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
# Generated JSONs live under docs/data so GitHub Pages serves them to the web app.
DATA_DIR = REPO_ROOT / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = SCRIPT_DIR / ".cache"
SEEN_FILE = CACHE_DIR / "seen_vehicles.json"
LIVE_FILE = DATA_DIR / "inventory_live.json"
# Photo/spec enrichment shard — lazy-loaded by the UI so the main inventory
# payload (the critical rendering path) stays exactly as small as before.
#
# PHOTO POLICY (owner directive, Sep 2026): photos are captured ONLY when the
# chain itself hosts them (e.g. LKQ photos on LKQ's cdn.pypapps.com, carrying
# LKQ's own PYP watermark). Pick-n-Pull's API returns photo URLs, but they
# live on cdn.row52.com with a Row52 watermark — Row52 is PnP's inventory/
# photo partner and a direct competitor, so those images are never captured,
# hotlinked, or referenced. (PnP's "own" API at picknpull.com/api is in fact
# Row52-powered under the hood — responses carry Row52 account ids and CDN
# URLs. The factual inventory data from it is fine to use; the images are not.)
EXTRAS_FILE = DATA_DIR / "vehicle_extras.json"

PNP_API = "https://www.picknpull.com/api"
SLC_ZIP = "84101"
SEARCH_RADIUS = 100
# The national search (distance=0) silently TRUNCATES at exactly 5,000 rows
# per make. Ford / Chevrolet / Honda exceed that (Toyota and Nissan are close),
# and WHICH 5,000 you get is arbitrary — diagnosed 2026-10-21 when a scan that
# ran hours after Pick-n-Pull SLC posted new arrivals was still missing 161 of
# the yard's 1,103 cars (91 Fords, 40 Chevys, some dating back to August).
# When a make's national response comes back at exactly the cap, re-sweep that
# make with one query per yard postal code (radius below) and union by id —
# validated to recover Ford 5,000 -> 7,077 in ~25s.
PNP_NATIONAL_CAP = 5000
PNP_SWEEP_RADIUS = 25
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

# NHTSA vPIC — no API key. Unique VINs are decoded in parallel (VPIC_WORKERS); no per-VIN sleep.
VPIC_DECODEVIN_EXTENDED = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvaluesextended/{vin}"
VPIC_BATCH_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"

# Date the UNOBTANIUM_DB resale ranges were last human-reviewed against market
# evidence (see scraper/price_validation_report.md). Bump when accepting
# corrections from a quarterly price-review PR. Exported to the v2 JSON and
# shown in the web app's pricing-transparency footer.
PRICES_LAST_REVIEWED = "2026-10-22"  # consensus-evergreens expansion: new category bands researched + baseline evidence added (see scraper/consensus_parts_research.md)
VPIC_BATCH_SIZE = 50
_VPIC_CACHE: dict[str, dict | None] = {}
def _vpic_workers() -> int:
    try:
        return max(1, int(os.environ.get("VPIC_WORKERS", "8")))
    except ValueError:
        return 8


_VPIC_WORKERS = _vpic_workers()
# Legacy: optional throttle after each HTTP decode (default 0 = rely on worker cap only).
_VPIC_DELAY_SEC = float(os.environ.get("VPIC_DELAY_SEC", "0"))

# Tear-A-Part API (WordPress AJAX)
TAP_AJAX = "https://tearapart.com/wp-admin/admin-ajax.php"
TAP_STORES = ["SALT LAKE CITY", "OGDEN"]

# Utah Pic-A-Part — full inventory + VINs from published XML (same feeds as premium lot UIs).
UTPAP_BASE = "https://utpap.com"
# Embedded iframe on https://utpap.com/ogden-prices/ — official part price table (Ogden; same list for Orem).
UTPAP_PRICELIST_URL = f"{UTPAP_BASE}/1064Carpricelist.php"
UTPAP_STORES = [
    {"slug": "ogden", "label": "Ogden", "city": "Ogden", "state": "UT"},
    {"slug": "orem", "label": "Orem", "city": "Orem", "state": "UT"},
]
# invupdPremiumOgden.html / invupdPremiumOrem.html filter by VEHICLE_ROW to these ranges
UTPAP_XML_BY_SLUG = {"ogden": "1064_inventory.xml", "orem": "1065_inventory.xml"}
UTPAP_PREMIUM_ROW_RANGE = {"ogden": (294, 300), "orem": (900, 925)}
TAP_MAKES = [
    "TOYOTA", "HONDA", "FORD", "CHEVROLET", "JEEP", "SUBARU",
    "NISSAN", "DODGE", "RAM", "HYUNDAI", "KIA", "BMW", "AUDI", "LEXUS", "VOLKSWAGEN",
    "GMC", "CHRYSLER", "MAZDA", "MITSUBISHI", "MERCURY", "LINCOLN",
    "BUICK", "CADILLAC", "INFINITI", "ACURA", "LAND ROVER", "GENESIS", "SCION",
]

# LKQ Pick Your Part — rebranded to pyp.com in 2026 (~60 self-service yards:
# CA/TX/FL heavy, plus MD/NC/SC/GA/TN/OH/IN/IL/WI/MI/KS/OK/CO/AL). Inventory is
# server-rendered HTML, 20 rows per page per store; store list (with lat/lng and
# state) is embedded in the /inventory/ page. Per-location price lists are JSON.
PYP_BASE = "https://www.pyp.com"
PYP_INVENTORY_API = f"{PYP_BASE}/DesktopModules/pyp_vehicleInventory/getVehicleInventory.aspx"
PYP_PRICELIST_API = f"{PYP_BASE}/DesktopModules/pyp_api/api/PriceList/"
PYP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html, application/json, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{PYP_BASE}/inventory/",
}
PYP_PAGE_SIZE = 20  # server-fixed; pageSize param is ignored
def _pyp_workers() -> int:
    try:
        return max(1, int(os.environ.get("PYP_WORKERS", "6")))
    except ValueError:
        return 6

US_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}

# Makes whose names are two words — needed to split "2004 LAND ROVER DISCOVERY".
TWO_WORD_MAKES = {"LAND ROVER", "ALFA ROMEO", "ASTON MARTIN", "AMERICAN MOTORS"}

# Chains disagree on make casing (FORD vs Ford, Bmw vs BMW) — normalize at output
# so the web UI's make filter doesn't show duplicates.
MAKE_ACRONYMS = {"BMW", "GMC", "AMC", "MG", "MINI"}
def _canon_make(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return s
    if s.upper() in MAKE_ACRONYMS:
        return s.upper()
    return " ".join(
        w.upper() if w.upper() in MAKE_ACRONYMS else w.title() for w in s.split()
    )

# Pull-A-Part — 36 yards (Southeast/Gulf/Midwest + former U-Pull-&-Pay yards in
# AZ/NM/CO after the two chains merged; upullandpay.com now redirects here).
# Clean JSON microservices: anonymous website tokens, then one Vehicle/Search
# POST per make across every location at once.
PAP_SITE = "https://www.pullapart.com"
PAP_TOKEN_URL = f"{PAP_SITE}/api/internal/gettoken/"
PAP_INVENTORY_API = "https://inventoryservice.pullapart.com"
PAP_ENTERPRISE_API = "https://enterpriseservice.pullapart.com"
# Their location API has no coordinates; these are geocoded from each yard's zip.
PAP_COORDS = {
    3: (33.6369, -84.3371),    # Atlanta South, GA 30288
    4: (33.9381, -84.1972),    # Atlanta North, GA 30071
    5: (33.5594, -86.8153),    # Birmingham, AL 35207
    6: (36.1546, -86.8602),    # Nashville, TN 37209
    7: (35.2836, -80.7638),    # Charlotte, NC 28213
    8: (38.1593, -85.778),     # Louisville, KY 40214
    9: (33.4601, -81.973),     # Augusta, GA 30901
    10: (36.032, -83.8021),    # Knoxville, TN 37924
    11: (41.4342, -81.8044),   # Cleveland West, OH 44135
    12: (30.2077, -92.0656),   # Lafayette, LA 70506
    13: (32.3257, -86.3104),   # Montgomery, AL 36105
    14: (29.8725, -90.0673),   # New Orleans West, LA 70058
    15: (32.2435, -90.2612),   # Jackson, MS 39212
    16: (30.4848, -91.0689),   # Baton Rouge, LA 70814
    17: (35.0514, -89.9265),   # Memphis, TN 38118
    18: (39.8082, -86.1014),   # Indianapolis, IN 46218
    19: (36.144, -80.2376),    # Winston-Salem, NC 27105
    20: (34.0635, -81.0265),   # Columbia, SC 29203
    21: (33.7356, -84.1009),   # Atlanta East, GA 30058
    24: (40.7598, -81.35),     # Canton, OH 44707
    25: (41.0479, -81.4916),   # Akron, OH 44306
    27: (32.1707, -110.9719),  # Tucson, AZ 85714
    29: (31.7677, -106.3016),  # El Paso, TX 79936
    30: (27.7762, -97.4271),   # Corpus Christi, TX 78405
    33: (26.6644, -80.1741),   # West Palm Beach, FL 33411
    34: (28.3932, -81.3622),   # Orlando, FL 32824
    35: (39.2003, -84.4859),   # Cincinnati, OH 45216
    36: (35.0448, -106.6893),  # Albuquerque, NM 87105
    37: (33.4564, -112.1284),  # Phoenix, AZ 85009
    38: (38.7902, -104.8199),  # Colorado Springs, CO 80906
    39: (39.7378, -104.8152),  # Aurora, CO 80011
    40: (39.838, -104.9988),   # Denver, CO 80221
    41: (29.6223, -95.26),     # Houston, TX 77075
    42: (40.4598, -79.8224),   # Pittsburgh, PA 15235
    43: (26.6466, -81.8429),   # Fort Myers, FL 33916
}

# Part descriptions worth carrying into per-yard price files (keyword-mapped by
# the web UI). Everything else in the chains' 400-800 row price lists is noise.
PYP_PRICE_DESCRIPTIONS = {
    "HEADLIGHT", "SEAT WITH AIR BAG FRONT", "SEAT NO AIR BAG FRONT", "SEAT REAR",
    "SEAT THIRD ROW", "INTERCOOLER", "GPS TV SCREEN", "RADIO WITH DISPLAY",
    "FRONT BUMPER (STEEL)", "BUMPER COVER, FRONT", "STEERING WHEEL", "SPOILER REAR",
    "FRONT LAMP (FOG/PARKING/TURN/MARKER)", "BRAKE CALIPER", "MIRROR (SIDE VIEW)",
    "AMPLIFIER", "RADIO SPEAKER", "SPEAKER (SUB-WOOFER)", "ROOF GLASS (SUN ROOF)",
    "SLIDING DOOR MOTOR", "DECKLID/TAILGATE (BARE)", "CHASSIS CONTROL MODULE",
    "SENSOR CAMERAS", "ROOF RACK ASSEMBLY", "ROOF RACK RAIL/ CROSS BAR (EACH)",
    "GRILLE", "RUNNING BOARD", "FENDER EXTENSION", "WINDOW REGULATOR FRONT (ELECTRIC)",
    "TAILLIGHT (QUARTER MOUNTED)", "TAILLIGHT TRUNK LID/HATCH MOUNTED", "CABLE",
    "SEAT TRACK, (ELECTRIC)", "DASH PAD", "CENTER CONSOLE", "MUD FLAP/SPLASH GUARD",
    "EMBLEMS", "ELECTRIC WIPER MOTOR, WINDSHIELD", "ACTUATOR", "TRANSFER CASE MOTOR",
    # coverage expansion (2026-09): clusters, tailgates, shifters, hybrid,
    # glass, suspension, tops — every name verified against the live PriceList API.
    "ALTERNATOR", "INSTRUMENT CLUSTER", "GAUGES", "SHIFT ASSEMBLY",
    "DOOR ELECTRICAL SWITCH (MULTI)", "TRANSFER CASE SWITCH (4X4)", "CARGO COVER",
    "SKID PLATE", "DC CONVERTER (HYBRID/ELECTRIC)", "BATTERY (HYBRID BATTERY)",
    "TRAILER HITCH", "GLASS DOOR REAR", "GLASS BACK", "ROOF GLASS (T-TOP)",
    "ROOF GLASS PANORAMIC (FULL GLASS ROOF ASSEMBLY)", "CONVERTIBLE TOP MOTOR",
    "TIRE/WHEEL SET", "SHOCK ABSORBER", "STRUT (AIR)", "SUSPENSION COMPRESSOR/PUMP",
    "INTAKE MANIFOLD", "BRAKE/CLUTCH PEDAL BOX", "CARRIER ASSEMBLY", "WATER PUMP",
    "DOOR PANEL FRONT (BARE)", "TRANSFER CASE",
}
PAP_PRICE_PARTNAMES = {
    "HEADLIGHT ASSEMBLY (NON-HID/BALLAST)", "HEADLIGHT LED OR HID LAMP ASSEMBLY W/BALLAST",
    "SEAT, BUCKET W/ POWER TRACK (LEATHER)", "SEAT, BUCKET W/ MANUAL TRACK",
    "SEAT, REAR - EACH SECTION (CLOTH)", "SEAT, BENCH/3RD ROW MANUAL TRACK",
    "SEAT, BENCH W/ POWER TRACK (LEATHER)", "TURBO INTERCOOLER", "RADIO W/NAV DISPLAY",
    "RADIO  - W/CD OR MEDIA PLAYER", "BUMPER COVER ASSEMBLY", "BUMPER COVER",
    "BUMPER STEEL OR ALUMINUM", "STEERING WHEEL", "SPOILER - BOLT ON (EACH)",
    "FOG LAMP (EACH)", "BRAKE CALIPER", "DOOR MIRROR, OUTSIDE ELECTRIC REMOTE",
    "AMPLIFIER", "SPEAKER (ANY)", "SUNROOF/COVER/SHADE ASSEMBLY W/MOTOR",
    "DOOR/HATCH MOTOR, (SLIDING VAN/SUV)", "MODULE - BODY / CHASSIS / GATEWAY/ FUEL",
    "CAMERA, ON BOARD OR BACK UP", "LUGGAGE RACK", "LUGGAGE RACK CROSS BAR",
    "GRILLE PLASTIC (BARE) - ANY", "RUNNING BOARD (EACH)", "FENDER FLARE OR SKIRT",
    "WINDOW REGULATOR W/MOTOR", "TAILLIGHT ASSEMBLY - SINGLE SIDE", "VIDEO SCREEN",
    "CABLE - BRAKE/CLUTCH/SHIFTER/THROTTLE/RELEASE", "SEAT TRACK, ELECTRIC W/MOTOR",
    "DASH PAD (OVER 24in LENGTH)", "CONSOLE LID", "CONSOLE (OVER 16in LENGTH)",
    "MUD FLAP OR SPLASH GUARD", "EMBLEM", "WINDSHIELD WIPER MOTOR", "ACTUATOR",
    "4 WHEEL DRIVE ACTUATOR VACUUM OR ELECTRIC",
    # coverage expansion (2026-09) — verified against GetPartsTermSearch.
    "TRUCK GATE FOR BED", "ALTERNATOR (NON HYBRID)", "INSTRUMENT CLUSTER ASSEMBLY",
    "CLOCK OR SMALL GAUGES (EACH)", "SPEEDOMETER OR TACHOMETER",
    "TRANSMISSION FLOOR SHIFTER", "SWITCH, POWER WINDOW (MULTIPLE) ONLY",
    "SWITCH, MISC.", "SKID PLATE", "CARGO COVER, SHADE TYPE",
    "HYBRID POWER CONTROL MODULE/INVERTER", "HYBRID BATTERY ANY",
    "TRAILER HITCH RECEIVER", "DOOR GLASS (BARE)", "SHOCK ABSORBER (REGULAR)",
    "SHOCK ABSORBER AIR OR AIRBAG TYPE", "HATCH OR HOOD SHOCK (MANUAL)",
    "AIR COMPRESSOR (AIR SUSPENSION)", "TOP, T-TOP (EACH)", "HARDTOP W/O DOORS",
    "TOP - CONVERTIBLE TOP MOTOR", "TOP - CONVERTIBLE (NO RAMS)",
    "TOP - SUNROOF FRAME WITH GLASS", "TOP - SUNROOF GLASS ONLY",
    "TOP MOTOR, SUNROOF", "INTAKE PLENUM, UPPER",
    "INTERIOR TRIM PANEL (OVER 8IN LONG)", "PEDAL, BRAKE & CLUTCH ASSEMBLY",
    "DIFFERENTIAL (FRONT, REAR OR 3RD MEMBER DROP-OUT)", "TRUCK BED RAIL (EACH)",
    "AUXILIARY WATER PUMP", "TRANSFER CASE, 4X4", "SPARE TIRE COVER",
}

# ---------------------------------------------------------------------------
# Unobtanium DB — parts you can carry out. No engines, no transmissions.
# Keys are lowercase model substrings matched against PnP model names.
# low/high = anchor bands; at match time _resale_sold_calibrate() maps them toward
# typical US used eBay *sold* (not dealer list / insurance). Override with
# JUNKYARD_RAW_PRICES=1 to see raw DB numbers.
# ---------------------------------------------------------------------------
UNOBTANIUM_DB = {
    # --- TOYOTA ---
    # Parts use optional yr_min/yr_max to restrict by generation, and
    # optional "trim" list — if present, vehicle model must contain one of
    # those strings (case-insensitive) or the part is skipped.
    # Optional "option": True marks factory OPTIONS (tow packages, sunroofs,
    # hardtops...) that year/model/trim can never determine and vPIC never
    # decodes — match_vehicle() forces those to trim_status "unconfirmed"
    # (shown as "if equipped") and they contribute $0 to ranking value.
    "4runner": {
        "display": "Toyota 4Runner",
        "make": "Toyota",
        "year_range": (1990, 2024),
        "top_parts": [
            # Factory rear e-locker was an option package, never standard (3rd-gen option;
            # 5th-gen TRD trims are trim-gated in the gen-split entries).
            {"name": "Rear E-Locker Actuator Motor", "rarity": "Legendary", "low": 250, "high": 500, "cost": 15, "option": True},
            {"name": "TRD Pro Grille", "rarity": "Legendary", "low": 300, "high": 600, "cost": 40, "yr_min": 2014},
            {"name": "KDSS Sway Bar Actuators", "rarity": "Legendary", "low": 200, "high": 500, "cost": 20, "yr_min": 2003, "yr_max": 2009},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 400, "high": 800, "cost": 60, "yr_min": 2014},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20, "yr_max": 2009},
            {"name": "Roof Rack Crossbars", "rarity": "Rare", "low": 84, "high": 250, "cost": 20},
            {"name": "Transfer Case Shift Motor", "rarity": "Epic", "low": 90, "high": 200, "cost": 15},
            {"name": "Center Console Lid (uncracked)", "rarity": "Rare", "low": 50, "high": 250, "cost": 8},
            {"name": "Heated Side Mirrors (pair)", "rarity": "Rare", "low": 80, "high": 175, "cost": 15, "yr_min": 1996},
        ],
    },
    "tacoma": {
        "display": "Toyota Tacoma",
        "make": "Toyota",
        "year_range": (1995, 2024),
        "top_parts": [
            {"name": "TRD Pro Grille", "rarity": "Legendary", "low": 200, "high": 450, "cost": 30, "yr_min": 2016},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 350, "high": 700, "cost": 50, "yr_min": 2016},
            {"name": "OEM Fender Flares (color-matched)", "rarity": "Epic", "low": 200, "high": 500, "cost": 30, "yr_min": 2016},
            {"name": "TRD Skid Plate", "rarity": "Epic", "low": 150, "high": 350, "cost": 25, "yr_min": 2005},
            {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 30},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20, "yr_max": 2015},
        ],
    },
    "tundra": {
        "display": "Toyota Tundra",
        "make": "Toyota",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2018},
            {"name": "TRD Pro Grille", "rarity": "Epic", "low": 200, "high": 400, "cost": 30, "yr_min": 2014},
            # Tow mirrors (all entries below, every truck/van line) are a towing-package
            # option — never standard equipment, never VIN-decodable, and present on maybe a
            # third of trucks. Option flag = honest 'if equipped'.
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 420, "cost": 30, "yr_min": 2007, "option": True},  # new quality aftermarket pairs ~$400-450 — 80% ceiling (2026-09)
            {"name": "Tailgate (w/ camera)", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2014},
            {"name": "JBL Speakers + Amp", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 70, "high": 170, "cost": 20, "yr_max": 2013},  # new DEPO/TYC pairs ~$110-160 — 80% ceiling (2026-09)
        ],
    },
    "sequoia": {
        "display": "Toyota Sequoia",
        "make": "Toyota",
        "year_range": (2001, 2024),
        "top_parts": [
            # 3rd row NOT option-flagged: standard on Sequoia (8-passenger std).
            {"name": "3rd Row Seat (complete)", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
            # Rear load-leveling air springs were optional (std only on Platinum).
            {"name": "Rear Air Suspension Bags", "rarity": "Epic", "low": 150, "high": 350, "cost": 20, "yr_min": 2008, "option": True},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2008},
        ],
    },
    "highlander": {
        "display": "Toyota Highlander",
        "make": "Toyota",
        "year_range": (2001, 2024),
        "top_parts": [
            # Highlander 3rd row was optional most years (plenty of 5-seat examples) — unlike
            # Tahoe/Suburban/minivans where it's effectively universal.
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 400, "cost": 35, "option": True},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2008},
        ],
    },
    "camry": {
        "display": "Toyota Camry",
        "make": "Toyota",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2018},
            {"name": "BSM Side Mirror (heated, power fold)", "rarity": "Uncommon", "low": 75, "high": 150, "cost": 15, "yr_min": 2012},  # new aftermarket BSM-capable units ~$140-180 each — 80% ceiling (2026-09)
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_max": 2017},
        ],
    },
    "corolla": {
        "display": "Toyota Corolla",
        "make": "Toyota",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 35, "yr_min": 2020},
            {"name": "Steering Wheel (leather, w/ controls)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 10, "yr_min": 2009},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 20, "yr_max": 2019},
            {"name": "Entune / Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35, "yr_min": 2014, "yr_max": 2019},
        ],
    },
    "sienna": {
        "display": "Toyota Sienna",
        "make": "Toyota",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Epic", "low": 150, "high": 350, "cost": 15},
            {"name": "Power Sliding Door Cable", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
            # Rear DVD/entertainment is a textbook option package everywhere it appears.
            {"name": "Rear Entertainment Screen", "rarity": "Rare", "low": 75, "high": 200, "cost": 15, "yr_min": 2007, "option": True},
        ],
    },
    "prius": {
        "display": "Toyota Prius",
        "make": "Toyota",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "DC-DC Converter", "rarity": "Rare", "low": 150, "high": 350, "cost": 20},
            {"name": "Hybrid Inverter Pump", "rarity": "Rare", "low": 100, "high": 275, "cost": 20},
            {"name": "Hybrid Battery Cells (bulk)", "rarity": "Epic", "low": 20, "high": 50, "cost": 3},
            # Gen-2/gen-3 split: packs, meters and inverters are the classic
            # Prius junkyard pulls (PriusChat-documented failure items).
            {"name": "Hybrid Battery Pack (complete)", "rarity": "Epic", "low": 250, "high": 550, "cost": 100,
             "yr_min": 2004, "yr_max": 2009,
             "verify": "Load-test or log cell voltages before reselling — packs sit dead at yards"},
            {"name": "Hybrid Battery Pack (complete)", "rarity": "Epic", "low": 300, "high": 600, "cost": 100,
             "yr_min": 2010, "yr_max": 2015,
             "verify": "Load-test or log cell voltages before reselling — packs sit dead at yards"},
            {"name": "Combination Meter (dash display)", "rarity": "Rare", "low": 60, "high": 150, "cost": 10,
             "yr_min": 2004, "yr_max": 2009,
             "verify": "Known failure item — dead displays strand working cars; grab even untested"},
            {"name": "Inverter Assembly (complete)", "rarity": "Rare", "low": 150, "high": 350, "cost": 40,
             "yr_min": 2004, "yr_max": 2009},
            {"name": "Inverter Assembly (complete)", "rarity": "Rare", "low": 175, "high": 400, "cost": 40,
             "yr_min": 2010, "yr_max": 2015},
        ],
    },
    "rav4": {
        "display": "Toyota RAV4",
        "make": "Toyota",
        "year_range": (1996, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2019},
        ],
    },
    "fj cruiser": {
        "display": "Toyota FJ Cruiser",
        "make": "Toyota",
        "year_range": (2007, 2014),
        "top_parts": [
            {"name": "OEM Roof Rack (full)", "rarity": "Legendary", "low": 300, "high": 700, "cost": 40},
            {"name": "Rear Swing-Out Tire Carrier", "rarity": "Epic", "low": 200, "high": 450, "cost": 30},
            # Rear locker std on 6MT FJs but optional on autos — most FJs are autos.
            {"name": "Rear Diff Locker Actuator", "rarity": "Epic", "low": 150, "high": 300, "cost": 15, "option": True},
        ],
    },
    "land cruiser": {
        "display": "Toyota Land Cruiser",
        "make": "Toyota",
        "year_range": (1990, 2024),
        "top_parts": [
            {"name": "AHC Height Control Pump", "rarity": "Legendary", "low": 400, "high": 900, "cost": 40, "yr_min": 1998},
            # Factory triple-locker pkg was a rare OPTION on US 80/100-series — most Land
            # Cruisers don't have it.
            {"name": "Factory Locker Actuators", "rarity": "Legendary", "low": 300, "high": 700, "cost": 25, "option": True},
            {"name": "Uncracked Dash Pad", "rarity": "Epic", "low": 150, "high": 350, "cost": 15, "yr_max": 2007},
        ],
    },
    "avalon": {
        "display": "Toyota Avalon",
        "make": "Toyota",
        "year_range": (1995, 2022),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2019},
            {"name": "JBL Speaker System", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 15},
            {"name": "Heated/Cooled Seat Module", "rarity": "Rare", "low": 75, "high": 200, "cost": 10, "yr_min": 2005},
        ],
    },
    "matrix": {
        "display": "Toyota Matrix / Pontiac Vibe",
        "make": "Toyota",
        "year_range": (2003, 2014),
        "top_parts": [
            {"name": "XRS Steering Wheel", "rarity": "Rare", "low": 50, "high": 125, "cost": 10, "trim": ["XRS"]},
            {"name": "OEM Roof Rack", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 10},
        ],
    },
    # --- LEXUS ---
    "rx": {
        "display": "Lexus RX",
        "make": "Lexus",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "Mark Levinson Amp/Speakers", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2016},
        ],
    },
    "gx": {
        "display": "Lexus GX",
        "make": "Lexus",
        "year_range": (2003, 2024),
        "top_parts": [
            {"name": "KDSS Hydraulic Actuators", "rarity": "Legendary", "low": 300, "high": 700, "cost": 30, "yr_min": 2010},
            {"name": "Center Diff Lock Actuator", "rarity": "Epic", "low": 100, "high": 250, "cost": 10},
            {"name": "Mark Levinson Amp/Speakers", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
        ],
    },
    # Key must be "lexus is" — short "is" matches inside "Nissan", "Isuzu", etc.
    "lexus is": {
        "display": "Lexus IS",
        "make": "Lexus",
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "F-Sport Brake Calipers", "rarity": "Epic", "low": 200, "high": 450, "cost": 30, "trim": ["F Sport", "F-Sport", "350", "500"]},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2014},
            # Base cars pre-2014 previously had zero un-gated parts.
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 22, "yr_max": 2013},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    # --- HONDA ---
    "civic": {
        "display": "Honda Civic",
        "make": "Honda",
        "year_range": (1996, 2024),
        "top_parts": [
            {"name": "Si/Type R Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si", "Type R", "Type-R"]},
            {"name": "Si Front Lip (OEM)", "rarity": "Rare", "low": 75, "high": 175, "cost": 12, "trim": ["Si"]},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 35, "yr_min": 2016},
            {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35, "yr_min": 2016},
            {"name": "Power Side Mirror (heated)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 30, "yr_min": 2006},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22, "yr_max": 2015},
            {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
            {"name": "OEM Radio / Climate Panel", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15, "yr_max": 2015},
        ],
    },
    "accord": {
        "display": "Honda Accord",
        "make": "Honda",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 300, "high": 550, "cost": 40, "yr_min": 2018},
            {"name": "Sport Front Lip", "rarity": "Rare", "low": 75, "high": 200, "cost": 12, "trim": ["Sport"]},
            {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35, "yr_min": 2013},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 25, "yr_max": 2017},
            {"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 35, "high": 110, "cost": 18},
            {"name": "Gauge Cluster / IPC", "rarity": "Uncommon", "low": 55, "high": 160, "cost": 20},
        ],
    },
    "cr-v": {
        "display": "Honda CR-V",
        "make": "Honda",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "1st Gen Picnic Table", "rarity": "Legendary", "low": 100, "high": 300, "cost": 10, "yr_max": 2001},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2017},
        ],
    },
    "odyssey": {
        "display": "Honda Odyssey",
        "make": "Honda",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Epic", "low": 150, "high": 350, "cost": 15},
            {"name": "2nd Row Magic Seats", "rarity": "Rare", "low": 200, "high": 450, "cost": 35, "yr_min": 2018},
        ],
    },
    "element": {
        "display": "Honda Element",
        "make": "Honda",
        "year_range": (2003, 2011),
        "top_parts": [
            {"name": "OEM Roof Rack (full)", "rarity": "Epic", "low": 150, "high": 350, "cost": 25},
            {"name": "Suicide Door Latch/Hinge", "rarity": "Epic", "low": 75, "high": 200, "cost": 10},
        ],
    },
    "pilot": {
        "display": "Honda Pilot",
        "make": "Honda",
        "year_range": (2003, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
            # Factory/dealer accessory, not standard.
            {"name": "OEM Running Boards", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 15, "option": True},
        ],
    },
    # --- SUBARU ---
    "outback": {
        "display": "Subaru Outback",
        "make": "Subaru",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "Eyesight Camera Module", "rarity": "Epic", "low": 200, "high": 500, "cost": 25, "yr_min": 2013},
            # Wilderness trim didn't exist before MY2022 — row used to claim 2000-2024.
            {"name": "Wilderness Grille/Cladding", "rarity": "Epic", "low": 150, "high": 350, "cost": 25, "yr_min": 2022, "trim": ["Wilderness"]},
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 20},
        ],
    },
    "forester": {
        "display": "Subaru Forester",
        "make": "Subaru",
        "year_range": (1998, 2024),
        "top_parts": [
            # XT = the turbo Forester; scoop is trim-confirmable from VIN decode.
            {"name": "XT Hood Scoop", "rarity": "Rare", "low": 80, "high": 200, "cost": 15, "trim": ["XT"]},
            {"name": "Panoramic Sunroof Assembly", "rarity": "Rare", "low": 120, "high": 300, "cost": 30, "option": True},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            # Manual Foresters carry a viscous rear LSD — swap fodder for lifted builds.
            {"name": "Rear Viscous LSD Diff", "rarity": "Rare", "low": 100, "high": 250, "cost": 40, "manual": True},
            {"name": "Eyesight Camera Module", "rarity": "Epic", "low": 200, "high": 450, "cost": 25, "yr_min": 2014},
            {"name": "XT Turbo Intercooler + Piping", "rarity": "Epic", "low": 150, "high": 350, "cost": 20, "trim": ["XT"]},
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 20},
        ],
    },
    "impreza": {
        "display": "Subaru Impreza",
        "make": "Subaru",
        "year_range": (1993, 2024),
        "top_parts": [
            {"name": "Eyesight Camera Module", "rarity": "Epic", "low": 200, "high": 450, "cost": 25, "yr_min": 2012},
            {"name": "OEM Headlights (clear)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 35},
            {"name": "Roof Rails", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_min": 2012},
        ],
    },
    "wrx": {
        "display": "Subaru WRX/STI",
        "make": "Subaru",
        "year_range": (2002, 2024),
        "top_parts": [
            {"name": "STI Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 700, "cost": 60, "trim": ["STI", "STi"]},
            {"name": "STI/Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["STI", "STi"]},
            {"name": "STI Wing (OEM)", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "trim": ["STI", "STi"]},
            {"name": "Hood Scoop (functional)", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 15},
            {"name": "Turbo Intercooler (TMIC)", "rarity": "Rare", "low": 100, "high": 250, "cost": 50},
        ],
    },
    "legacy": {
        "display": "Subaru Legacy",
        "make": "Subaru",
        "year_range": (1995, 2024),
        "top_parts": [
            {"name": "Eyesight Camera Module", "rarity": "Epic", "low": 200, "high": 450, "cost": 25, "yr_min": 2015},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_max": 2014},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30, "yr_min": 2015, "trim": ["Limited", "Sport", "GT"], "option": True},
        ],
    },
    # --- JEEP ---
    "cherokee": {
        "display": "Jeep Cherokee",
        "make": "Jeep",
        "year_range": (1984, 2024),
        "top_parts": [
            {"name": "XJ Header Panel (clean)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 25, "yr_max": 2001},
            {"name": "Clean Fenders (no rust)", "rarity": "Epic", "low": 100, "high": 275, "cost": 20, "yr_max": 2001},
            {"name": "Overhead Console (digital)", "rarity": "Rare", "low": 75, "high": 200, "cost": 10, "yr_max": 2001},
        ],
    },
    "grand cherokee": {
        "display": "Jeep Grand Cherokee",
        "make": "Jeep",
        "year_range": (1993, 2024),
        "top_parts": [
            {"name": "Transfer Case Shift Motor", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
            {"name": "Heated Leather Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_min": 1999},
            # Quadra-Lift air is optional on most Grand Cherokee trims.
            {"name": "Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2005, "option": True},
        ],
    },
    "wrangler": {
        "display": "Jeep Wrangler",
        "make": "Jeep",
        "year_range": (1987, 2024),
        "top_parts": [
            # YJ/TJ full steel doors are chronically stripped — strong national demand.
            {"name": "Full Steel Doors (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40, "yr_max": 2006},
            {"name": "Tailgate", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 20},
            # Soft top was standard on every Wrangler generation — the hardtop is an option
            # (dual-top group etc.), so it can never be assumed present.
            {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 400, "high": 1500, "cost": 60, "option": True},
            {"name": "Half Doors (pair)", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
            {"name": "Rubicon Locker Actuators", "rarity": "Epic", "low": 100, "high": 275, "cost": 10, "trim": ["Rubicon"]},
        ],
    },
    # --- FORD ---
    "f-150": {
        "display": "Ford F-150",
        "make": "Ford",
        "year_range": (1997, 2024),
        "top_parts": [
            # Power-retract boards std only on Limited/Platinum-tier trims, optional elsewhere
            # (same for every power-board entry below).
            {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 300, "high": 700, "cost": 40, "yr_min": 2015, "option": True},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2015},
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 550, "cost": 40, "yr_min": 2004, "option": True},
            {"name": "Raptor Grille", "rarity": "Legendary", "low": 200, "high": 500, "cost": 25, "trim": ["Raptor"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_max": 2014},
        ],
    },
    "f150": {
        "display": "Ford F-150",
        "make": "Ford",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "Power-Fold Tow Mirrors", "rarity": "Epic", "low": 250, "high": 550, "cost": 40, "yr_min": 2004, "option": True},
        ],
    },
    "explorer": {
        "display": "Ford Explorer",
        "make": "Ford",
        "year_range": (1991, 2024),
        "top_parts": [
            # 3rd row optional on 2002-2010 Explorers (std from 2011).
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_min": 2002, "option": True},
            {"name": "Rear Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2006, "option": True},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22, "yr_max": 2005},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_min": 2006, "yr_max": 2010},
        ],
    },
    "mustang": {
        "display": "Ford Mustang",
        "make": "Ford",
        "year_range": (2005, 2024),
        "top_parts": [
            {"name": "Recaro Seats (PP/GT350)", "rarity": "Epic", "low": 500, "high": 1200, "cost": 75, "yr_min": 2012, "trim": ["GT350", "GT500", "Shelby", "Mach 1"], "option": True},
            {"name": "GT Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2007, "trim": ["GT"]},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2015},
        ],
    },
    # --- CHEVY ---
    "silverado": {
        "display": "Chevy Silverado",
        "make": "Chevrolet",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 35, "yr_min": 2014, "option": True},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2019},
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 300, "high": 600, "cost": 30, "yr_min": 2007, "option": True},
            {"name": "MultiPro Tailgate Steps", "rarity": "Epic", "low": 200, "high": 500, "cost": 30, "yr_min": 2019},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_max": 2018},
        ],
    },
    "tahoe": {
        "display": "Chevy Tahoe/Suburban/Yukon",
        "make": "Chevrolet",
        "year_range": (1995, 2024),
        "top_parts": [
            {"name": "AutoRide Rear Shocks (pair)", "rarity": "Epic", "low": 150, "high": 350, "cost": 20, "yr_min": 2000},
            # 3rd row NOT option-flagged: near-universal take rate on Tahoe/Suburban/Yukon.
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        ],
    },
    "suburban": {
        "display": "Chevy Suburban",
        "make": "Chevrolet",
        "year_range": (1992, 2024),
        "top_parts": [
            # 3rd row NOT option-flagged: effectively standard on Suburban.
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        ],
    },
    "camaro": {
        "display": "Chevy Camaro",
        "make": "Chevrolet",
        "year_range": (2010, 2024),
        "top_parts": [
            {"name": "IROC-Z / Z28 Wheels (set)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40, "yr_max": 1992, "trim": ["IROC", "Z28"]},
            {"name": "Digital Dash Cluster", "rarity": "Rare", "low": 100, "high": 280, "cost": 20, "yr_max": 1989, "option": True},
            {"name": "SS/Z28 Rear Spoiler", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 20, "yr_min": 1993, "yr_max": 2002, "trim": ["SS", "Z28"]},
            {"name": "LS1 Intake + Accessories", "rarity": "Rare", "low": 100, "high": 300, "cost": 30, "yr_min": 1998, "yr_max": 2002, "trim": ["SS", "Z28"]},
            {"name": "SS Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["SS", "ZL1", "Z28", "1LE"]},
            {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SS", "ZL1", "1LE"], "option": True},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 400, "cost": 40, "yr_min": 2016},
        ],
    },
    # --- DODGE/RAM ---
    "ram": {
        "display": "Ram / Dodge Ram Truck",
        "make": "Ram",
        "year_range": (1994, 2024),
        "top_parts": [
            {"name": "12\" Uconnect Touchscreen", "rarity": "Epic", "low": 400, "high": 800, "cost": 50, "yr_min": 2019},
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 500, "cost": 35, "yr_min": 2009, "option": True},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25, "yr_max": 2008},
            {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
            {"name": "Gauge Cluster", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 20, "yr_max": 2010},
        ],
    },
    # --- NISSAN ---
    "frontier": {
        "display": "Nissan Frontier",
        "make": "Nissan",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "Utili-track Bed Rails + Cleats", "rarity": "Rare", "low": 80, "high": 200, "cost": 25, "option": True},
            {"name": "Bed Extender", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "option": True},
            {"name": "Roof Rack Crossbars", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15, "option": True},
            {"name": "PRO-4X Skid Plates", "rarity": "Rare", "low": 100, "high": 225, "cost": 15, "trim": ["PRO-4X", "Pro-4X"]},
            {"name": "Bilstein Shocks (PRO-4X)", "rarity": "Rare", "low": 150, "high": 300, "cost": 30, "trim": ["PRO-4X", "Pro-4X"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        ],
    },
    "xterra": {
        "display": "Nissan Xterra",
        "make": "Nissan",
        "year_range": (2000, 2015),
        "top_parts": [
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15},
            {"name": "Side Steps / Rock Rails (pair)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 20},
            {"name": "Center Console (lid intact)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 12},
            {"name": "OEM Roof Rack (tube-style)", "rarity": "Epic", "low": 150, "high": 350, "cost": 25},
            {"name": "Rear Diff Locker Switch", "rarity": "Rare", "low": 50, "high": 125, "cost": 5, "trim": ["PRO-4X", "Off-Road"]},
        ],
    },
    "pathfinder": {
        "display": "Nissan Pathfinder",
        "make": "Nissan",
        "year_range": (1996, 2024),
        "top_parts": [
            {"name": "4WD Actuator Motor", "rarity": "Rare", "low": 75, "high": 175, "cost": 10},
            {"name": "OEM Roof Rack", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 10},
        ],
    },
    "focus": {
        "display": "Ford Focus",
        "make": "Ford",
        "year_range": (2000, 2018),
        "top_parts": [
            # Both bands RAISED per the 2026-09 audit (UNDERSTATED verdicts):
            # ST3/RS HID pairs sold $400-1,300; ST/RS Recaro pairs $950-2,000.
            # Generation-fits: the US Focus ST launched 2013, RS 2016 — these
            # are gen-3 parts only; the old rows claimed fits 2000-2018.
            # HIDs were ST3-package-only pre-facelift (ST2+ 2017-18); branded
            # Recaros were ST2/ST3 package content (ST1 = unbranded cloth).
            # Both std on RS — "option" under-claims RS, which is acceptable.
            {"name": "ST3/RS HID Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1600, "cost": 45, "yr_min": 2013, "trim": ["ST", "RS"], "option": True},
            {"name": "Recaro Seats (pair, ST/RS)", "rarity": "Epic", "low": 1100, "high": 2600, "cost": 71, "yr_min": 2013, "trim": ["ST", "RS"], "option": True},
            {"name": "ST/RS Intercooler", "rarity": "Rare", "low": 60, "high": 160, "cost": 95, "yr_min": 2013, "trim": ["ST", "RS"]},
            {"name": "ST/RS Steering Wheel", "rarity": "Rare", "low": 100, "high": 225, "cost": 37, "yr_min": 2013, "trim": ["ST", "RS"]},
            {"name": "RS Brake Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 28, "yr_min": 2016, "trim": ["RS"]},  # RS sold 2016-2018 only
            {"name": "SYNC 3 Touchscreen (8\")", "rarity": "Rare", "low": 150, "high": 350, "cost": 45, "yr_min": 2015},
            {"name": "OEM Fog Lights + Bezels", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 22, "yr_min": 2008},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 35},
        ],
    },
    "fusion": {
        "display": "Ford Fusion",
        "make": "Ford",
        "year_range": (2006, 2020),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 45, "yr_min": 2017},
            {"name": "SYNC 3 Touchscreen (8\")", "rarity": "Rare", "low": 150, "high": 350, "cost": 45, "yr_min": 2016},
            {"name": "Sport Twin-Turbo Intercooler", "rarity": "Epic", "low": 100, "high": 250, "cost": 95, "trim": ["Sport"]},
            {"name": "Power Heated Mirrors (BSM, pair)", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 42, "yr_min": 2013},
            {"name": "Heated/Cooled Seat Module", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 29, "yr_min": 2013},
            {"name": "Sony Audio Amp + Speakers", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 44},
        ],
    },
    "elantra": {
        "display": "Hyundai Elantra",
        "make": "Hyundai",
        "year_range": (2001, 2023),
        "top_parts": [
            # Generation-fits: Elantra Sport (1.6T) arrived with the 2017 AD,
            # N Line/N with the 2021 CN7 — these rows used to claim 2001-2023.
            {"name": "N/Sport Front Bumper Assembly", "rarity": "Epic", "low": 200, "high": 450, "cost": 73, "yr_min": 2017, "trim": ["N", "Sport", "N Line"]},
            {"name": "N Line Steering Wheel", "rarity": "Rare", "low": 100, "high": 225, "cost": 37, "yr_min": 2017, "trim": ["N", "N Line"]},
            {"name": "Sport/N Rear Spoiler", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 40, "yr_min": 2021, "trim": ["N", "N Line"]},  # 2017-20 Sport sedan had no factory spoiler; std on 2021+ N/N Line
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 400, "cost": 45, "yr_min": 2017},
            {"name": "Touchscreen Infotainment", "rarity": "Rare", "low": 200, "high": 400, "cost": 60, "yr_min": 2017},
            {"name": "Smart Cruise Radar Module", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 22, "yr_min": 2017},
            {"name": "Wireless Charging Pad Module", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 29, "yr_min": 2019},
        ],
    },
    "grand caravan": {
        "display": "Dodge Grand Caravan",
        "make": "Dodge",
        "year_range": (1996, 2020),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Rare", "low": 65, "high": 80, "cost": 47},
            {"name": "Power Sliding Door Control Module", "rarity": "Rare", "low": 100, "high": 165, "cost": 29},
            {"name": "Stow-N-Go 2nd Row Seat (each)", "rarity": "Rare", "low": 200, "high": 450, "cost": 55, "yr_min": 2005},
            {"name": "Stow-N-Go 3rd Row Seat", "rarity": "Rare", "low": 100, "high": 250, "cost": 34, "yr_min": 2005},
            {"name": "Rear Entertainment Screen + DVD", "rarity": "Rare", "low": 75, "high": 200, "cost": 60, "yr_min": 2008, "option": True},
            {"name": "Power Sliding Door Cable/Track", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 29},
            {"name": "Uconnect Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 45, "yr_min": 2011},
        ],
    },
    "sonata": {
        "display": "Hyundai Sonata",
        "make": "Hyundai",
        "year_range": (1999, 2023),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 45, "yr_min": 2018},
            {"name": "Touchscreen Infotainment", "rarity": "Rare", "low": 200, "high": 450, "cost": 60, "yr_min": 2015},
            {"name": "Heads-Up Display Module", "rarity": "Epic", "low": 300, "high": 700, "cost": 60, "yr_min": 2020, "trim": ["Limited"]},
            # Sunroof/moonroof entries (here and below): factory option on virtually every
            # non-luxury model, never decodable from the VIN.
            {"name": "Panoramic Sunroof Glass", "rarity": "Rare", "low": 150, "high": 350, "cost": 44, "yr_min": 2011, "option": True},
            # Infinity premium audio started with the 2006 NF Sonata — was claiming 1999+.
            {"name": "Bose/Infinity Amp + Speakers", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 44, "yr_min": 2006},
            {"name": "Smart Cruise Radar Module", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 22, "yr_min": 2018},
            {"name": "Wireless Charging Pad Module", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 29, "yr_min": 2019},
        ],
    },
    # --- TOP NO-MATCH MODELS + easy flips ---
    "altima": {
        "display": "Nissan Altima",
        "make": "Nissan",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2019},
            {"name": "Bose Door Speakers + Amp", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 22, "yr_min": 2013},
            {"name": "Touchscreen / NissanConnect Unit", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45, "yr_min": 2013},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22, "yr_max": 2018},
            {"name": "Blind Spot Radar Module", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 22, "yr_min": 2016},
        ],
    },
    "maxima": {
        "display": "Nissan Maxima",
        "make": "Nissan",
        "year_range": (1995, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 45, "yr_min": 2016},
            {"name": "Bose Subwoofer + Amp", "rarity": "Rare", "low": 100, "high": 250, "cost": 35},
            {"name": "Panoramic Sunroof Motor", "rarity": "Rare", "low": 100, "high": 220, "cost": 22, "yr_min": 2009, "option": True},
            # A32/A33 VQ30 era (floor extended from 2000).
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20, "yr_max": 1999},
            {"name": "Adaptive Cruise Radar", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 22, "yr_min": 2016},
        ],
    },
    "sentra": {
        "display": "Nissan Sentra",
        "make": "Nissan",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 400, "cost": 38, "yr_min": 2020},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20, "yr_max": 2019},
            {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 180, "cost": 35, "yr_min": 2013},
        ],
    },
    "impala": {
        "display": "Chevrolet Impala",
        "make": "Chevrolet",
        "year_range": (2000, 2020),
        "top_parts": [
            {"name": "MyLink / Touchscreen Head Unit", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45, "yr_min": 2014},
            {"name": "Heated Leather Front Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 55, "yr_min": 2006},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 22},
            {"name": "Amplifier + Door Speakers", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 22},
        ],
    },
    "cruze": {
        "display": "Chevrolet Cruze",
        "make": "Chevrolet",
        "year_range": (2011, 2019),
        "top_parts": [
            {"name": "MyLink Touchscreen", "rarity": "Uncommon", "low": 100, "high": 220, "cost": 45, "yr_min": 2013},
            {"name": "Turbo Intercooler + Pipes", "rarity": "Rare", "low": 80, "high": 200, "cost": 35, "trim": ["Turbo", "RS"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 22},
        ],
    },
    "malibu": {
        "display": "Chevrolet Malibu",
        "make": "Chevrolet",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "MyLink / Infotainment Screen", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2013},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2016},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 22, "yr_max": 2015},
        ],
    },
    "cobalt": {
        "display": "Chevrolet Cobalt",
        "make": "Chevrolet",
        "year_range": (2005, 2010),
        "top_parts": [
            {"name": "SS Supercharged / Turbo Parts", "rarity": "Epic", "low": 150, "high": 400, "cost": 45, "trim": ["SS"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Cluster / Gauges", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15},
        ],
    },
    "equinox": {
        "display": "Chevrolet Equinox",
        "make": "Chevrolet",
        "year_range": (2005, 2024),
        "top_parts": [
            {"name": "MyLink Touchscreen", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2013},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 250, "cost": 18, "yr_min": 2010},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25},
        ],
    },
    "trailblazer": {
        "display": "Chevrolet TrailBlazer",
        "make": "Chevrolet",
        "year_range": (2002, 2024),
        "top_parts": [
            {"name": "SS Intake / Engine Bay Trim", "rarity": "Rare", "low": 100, "high": 280, "cost": 30, "trim": ["SS"]},
            {"name": "Transfer Case / 4WD Selector", "rarity": "Rare", "low": 100, "high": 250, "cost": 25},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 22},
        ],
    },
    "escape": {
        "display": "Ford Escape",
        "make": "Ford",
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "SYNC 3 / Touchscreen Head Unit", "rarity": "Rare", "low": 200, "high": 450, "cost": 45, "yr_min": 2017},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 240, "cost": 18, "yr_min": 2013},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25},
        ],
    },
    "taurus": {
        "display": "Ford Taurus",
        "make": "Ford",
        "year_range": (2000, 2019),
        "top_parts": [
            {"name": "SYNC / MyFord Touch Screen", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45, "yr_min": 2010},
            {"name": "SHO Turbo / Intercooler Parts", "rarity": "Epic", "low": 200, "high": 500, "cost": 55, "trim": ["SHO"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 22},
        ],
    },
    "expedition": {
        "display": "Ford Expedition",
        "make": "Ford",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 300, "high": 600, "cost": 35, "yr_min": 2007, "option": True},
            {"name": "SYNC 3 / Large Touchscreen", "rarity": "Rare", "low": 250, "high": 500, "cost": 50, "yr_min": 2015},
            # 3rd row NOT option-flagged: std on Expedition since 2003, near-universal before.
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
        ],
    },
    "durango": {
        "display": "Dodge Durango",
        "make": "Dodge",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "Uconnect 8.4\" Touchscreen", "rarity": "Rare", "low": 250, "high": 500, "cost": 50, "yr_min": 2014},
            # Durango 3rd row genuinely optional across gens (plenty of 2-row SXTs).
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "option": True},
            {"name": "Tow Hitch + Wiring Harness", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 25},
        ],
    },
    "avenger": {
        "display": "Dodge Avenger",
        "make": "Dodge",
        "year_range": (2008, 2014),
        "top_parts": [
            {"name": "Touchscreen / Radio Bezel", "rarity": "Uncommon", "low": 75, "high": 180, "cost": 35},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 22},
        ],
    },
    "town & country": {
        "display": "Chrysler Town & Country",
        "make": "Chrysler",
        "year_range": (2001, 2016),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Rare", "low": 65, "high": 85, "cost": 47},
            {"name": "Stow-N-Go 2nd Row Seat (each)", "rarity": "Rare", "low": 200, "high": 450, "cost": 55, "yr_min": 2005},
            {"name": "Rear Entertainment Screen + DVD", "rarity": "Rare", "low": 75, "high": 200, "cost": 60, "yr_min": 2008, "option": True},
            {"name": "Uconnect Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 45, "yr_min": 2011},
        ],
    },
    "liberty": {
        "display": "Jeep Liberty",
        "make": "Jeep",
        "year_range": (2002, 2012),
        "top_parts": [
            {"name": "Skid Plates (set)", "rarity": "Uncommon", "low": 75, "high": 180, "cost": 20},
            {"name": "Transfer Case Motor", "rarity": "Rare", "low": 100, "high": 220, "cost": 18},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 22},
        ],
    },
    "mazda3": {
        "display": "Mazda Mazda3",
        "make": "Mazda",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "Mazdaspeed Turbo / Intercooler", "rarity": "Epic", "low": 200, "high": 500, "cost": 55, "trim": ["Mazdaspeed", "SPEED"]},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 420, "cost": 40, "yr_min": 2019},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 22, "yr_max": 2018},
        ],
    },
    "mazda6": {
        "display": "Mazda Mazda6",
        "make": "Mazda",
        "year_range": (2003, 2024),
        "top_parts": [
            {"name": "Bose Door Speakers + Amp", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 30},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25},
            {"name": "Touchscreen / Commander Knob Unit", "rarity": "Uncommon", "low": 150, "high": 320, "cost": 50, "yr_min": 2014},
        ],
    },
    "soul": {
        "display": "Kia Soul",
        "make": "Kia",
        "year_range": (2010, 2024),
        "top_parts": [
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 28},  # new TYC/DEPO pairs ~$100-140 — 80% ceiling; old band beat new price (2026-09)
            {"name": "Touchscreen / UVO Head Unit", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2014},
            # Optional even within Exclaim/GT-Line — trim gate limits availability, option
            # flag keeps it 'if equipped'.
            {"name": "Panoramic Sunroof Assembly", "rarity": "Rare", "low": 200, "high": 450, "cost": 44, "yr_min": 2014, "trim": ["Exclaim", "GT-Line"], "option": True},
        ],
    },
    "optima": {
        "display": "Kia Optima",
        "make": "Kia",
        "year_range": (2001, 2020),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 220, "high": 480, "cost": 42, "yr_min": 2016},
            # Infinity audio arrived with the 2011 gen-3 (TF) Optima — was claiming 2001+.
            {"name": "Infinity Audio + Amp", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30, "yr_min": 2011},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_max": 2015},
        ],
    },
    "ranger": {
        "display": "Ford Ranger",
        "make": "Ford",
        # Floor extended to 1983 — first-gen Rangers show up at yards steadily
        # and the tailgate/headlight parts below apply unchanged.
        "year_range": (1983, 2024),
        "top_parts": [
            {"name": "Tailgate (clean)", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
            {"name": "SYNC / Touchscreen Head Unit", "rarity": "Uncommon", "low": 200, "high": 450, "cost": 45, "yr_min": 2019},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 22},
        ],
    },
    "passat": {
        "display": "Volkswagen Passat",
        "make": "Volkswagen",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "Headlights (clear, OEM)", "rarity": "Uncommon", "low": 90, "high": 200, "cost": 35},  # new DEPO pairs ~$140-200 — 80% ceiling caps used high (2026-09)
            {"name": "Touchscreen / MIB Unit", "rarity": "Uncommon", "low": 150, "high": 350, "cost": 50, "yr_min": 2012},
        ],
    },
    "chrysler 200": {
        "display": "Chrysler 200",
        "make": "Chrysler",
        "year_range": (2011, 2017),
        "top_parts": [
            {"name": "Uconnect Touchscreen", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2012},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 28},  # new TYC/DEPO pairs ~$90-130 — 80% ceiling; old band beat new price (2026-09)
        ],
    },
    "sonic": {
        "display": "Chevrolet Sonic",
        "make": "Chevrolet",
        "year_range": (2012, 2020),
        "top_parts": [
            {"name": "MyLink Touchscreen", "rarity": "Uncommon", "low": 100, "high": 220, "cost": 42, "yr_min": 2013},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 22},
        ],
    },
    # --- Enthusiast / strong resale (easy-to-move electronics, lighting, seats) ---
    "brz": {
        "display": "Subaru BRZ",
        "make": "Subaru",
        "year_range": (2013, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "yr_min": 2017},
            {"name": "Touchscreen / Starlink Head Unit", "rarity": "Rare", "low": 200, "high": 450, "cost": 45, "yr_min": 2017},
            {"name": "Instrument Cluster (full LCD)", "rarity": "Rare", "low": 250, "high": 550, "cost": 40, "yr_min": 2017},
            {"name": "Limited/Sport Seats (pair)", "rarity": "Rare", "low": 300, "high": 650, "cost": 55, "trim": ["Limited", "tS"]},
        ],
    },
    "fr-s": {
        "display": "Scion FR-S",
        "make": "Scion",
        "year_range": (2013, 2016),
        "top_parts": [
            {"name": "Front Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 40},
            # Torsen LSD was standard equipment on the FR-S.
            {"name": "Torsen Rear Diff", "rarity": "Rare", "low": 150, "high": 400, "cost": 50},
            {"name": "OEM Headlights (pair)", "rarity": "Rare", "low": 250, "high": 550, "cost": 45},
            {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 150, "high": 350, "cost": 40},
            {"name": "TRD / Performance Exhaust Mid-Pipe", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 25, "trim": ["TRD"]},
        ],
    },
    "gt86": {
        "display": "Toyota 86 / GT86",
        "make": "Toyota",
        "year_range": (2013, 2021),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "yr_min": 2017},
            {"name": "Touchscreen / Entune Head Unit", "rarity": "Rare", "low": 180, "high": 400, "cost": 42},
            {"name": "TRD Wheels (set)", "rarity": "Rare", "low": 400, "high": 900, "cost": 80, "trim": ["TRD"]},
        ],
    },
    "gr86": {
        "display": "Toyota GR86",
        "make": "Toyota",
        "year_range": (2022, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1000, "cost": 70},
            {"name": "Digital Cluster / HUD Module", "rarity": "Epic", "low": 350, "high": 750, "cost": 50},
            {"name": "GR Sport Seats (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 75, "trim": ["GR", "Premium"]},
        ],
    },
    "mx-5": {
        "display": "Mazda MX-5 Miata",
        "make": "Mazda",
        "year_range": (1990, 2024),
        "top_parts": [
            # NA/NB removable hardtops are the single most demanded Miata part.
            {"name": "OEM Removable Hardtop", "rarity": "Legendary", "low": 500, "high": 1200, "cost": 60, "yr_max": 2005, "option": True},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "Nardi Steering Wheel + Knob", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "option": True},
            {"name": "OEM Soft Top (clean)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            # Removable hardtop was a dealer option/accessory, never standard.
            {"name": "OEM Hardtop (ND)", "rarity": "Legendary", "low": 800, "high": 1800, "cost": 100, "yr_min": 2016, "option": True},
            {"name": "BBS / Club Wheels (set)", "rarity": "Epic", "low": 600, "high": 1400, "cost": 90, "trim": ["Club", "Grand Touring"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2006},
        ],
    },
    "350z": {
        "display": "Nissan 350Z",
        "make": "Nissan",
        "year_range": (2003, 2009),
        "top_parts": [
            {"name": "OEM Xenon Headlights (pair)", "rarity": "Epic", "low": 300, "high": 650, "cost": 50},
            {"name": "Brembo Calipers (set)", "rarity": "Epic", "low": 350, "high": 700, "cost": 55, "trim": ["Track", "Nismo"]},
            {"name": "Bose / Rockford Amp + Speakers", "rarity": "Rare", "low": 100, "high": 250, "cost": 25},
        ],
    },
    "370z": {
        "display": "Nissan 370Z",
        "make": "Nissan",
        "year_range": (2009, 2020),
        "top_parts": [
            {"name": "OEM Xenon/LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 850, "cost": 60},
            {"name": "Nismo Body Kit Pieces", "rarity": "Epic", "low": 300, "high": 800, "cost": 60, "trim": ["Nismo"]},
            {"name": "Bose Audio Amp + Sub", "rarity": "Rare", "low": 120, "high": 280, "cost": 30},
        ],
    },
    # --- AUDI (keywords use "audi …" where needed so Q5 ≠ Infiniti Q50, etc.)
    "audi a3": {
        "display": "Audi A3 / S3",
        "make": "Audi",
        "year_range": (2006, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 350, "high": 800, "cost": 55, "yr_min": 2015},
            {"name": "MMI / Virtual Cockpit Module", "rarity": "Epic", "low": 200, "high": 550, "cost": 42, "yr_min": 2015},
            {"name": "Bang & Olufsen / Premium Audio", "rarity": "Rare", "low": 180, "high": 450, "cost": 38, "trim": ["S3", "Prestige", "Premium Plus"], "option": True},
            {"name": "Quattro / Haldex Differential (rear)", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2006, "drive": ["awd"]},
        ],
    },
    "audi s3": {
        "display": "Audi S3",
        "make": "Audi",
        "year_range": (2015, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 65, "yr_min": 2015},
            {"name": "Digital Cluster / Virtual Cockpit", "rarity": "Epic", "low": 350, "high": 800, "cost": 48, "yr_min": 2017},
            {"name": "B&O / Premium Audio", "rarity": "Rare", "low": 200, "high": 500, "cost": 38, "yr_min": 2015},
            {"name": "Sport Seats / S Embroidered (pair)", "rarity": "Rare", "low": 400, "high": 900, "cost": 55, "yr_min": 2015},
        ],
    },
    "audi rs3": {
        "display": "Audi RS3",
        "make": "Audi",
        "year_range": (2017, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Legendary", "low": 800, "high": 2000, "cost": 85, "yr_min": 2017},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 1200, "high": 2800, "cost": 120, "yr_min": 2017},
            {"name": "Digital Cockpit / MMI Navigation Plus", "rarity": "Epic", "low": 400, "high": 950, "cost": 50, "yr_min": 2017},
            {"name": "OEM Wheels (19–20\", set)", "rarity": "Epic", "low": 1000, "high": 2500, "cost": 100, "yr_min": 2017},
        ],
    },
    "audi a4": {
        "display": "Audi A4 / Allroad",
        "make": "Audi",
        "year_range": (2002, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 950, "cost": 58, "yr_min": 2009},
            {"name": "MMI / MMI Touch / Screen Assembly", "rarity": "Epic", "low": 220, "high": 600, "cost": 45, "yr_min": 2009},
            {"name": "Bang & Olufsen / B&O Sound System", "rarity": "Rare", "low": 200, "high": 520, "cost": 40, "trim": ["Prestige", "Premium Plus"], "option": True},
            {"name": "Instrument Cluster (virtual cockpit)", "rarity": "Epic", "low": 350, "high": 850, "cost": 45, "yr_min": 2017},
        ],
    },
    "audi s4": {
        "display": "Audi S4",
        "make": "Audi",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1150, "cost": 65, "yr_min": 2010},
            {"name": "Sport Differential / Quattro Controller", "rarity": "Epic", "low": 400, "high": 950, "cost": 45, "yr_min": 2010, "option": True},
            {"name": "B&O / Premium Audio", "rarity": "Rare", "low": 220, "high": 550, "cost": 38, "yr_min": 2010},
            {"name": "S Sport Seats (pair)", "rarity": "Rare", "low": 450, "high": 1000, "cost": 58, "yr_min": 2010},
        ],
    },
    "audi rs4": {
        "display": "Audi RS4",
        "make": "Audi",
        "year_range": (2007, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Legendary", "low": 900, "high": 2200, "cost": 90, "yr_min": 2018},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 1500, "high": 3500, "cost": 130, "yr_min": 2018},
            {"name": "Carbon Interior Trim Set", "rarity": "Epic", "low": 400, "high": 1000, "cost": 45, "yr_min": 2018},
        ],
    },
    "audi rs5": {
        "display": "Audi RS5",
        "make": "Audi",
        "year_range": (2010, 2024),
        "top_parts": [
            {"name": "OEM Laser / Matrix Headlights (pair)", "rarity": "Legendary", "low": 1000, "high": 2400, "cost": 92, "yr_min": 2018},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 1600, "high": 3800, "cost": 135, "yr_min": 2010},
            {"name": "Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 3000, "high": 7500, "cost": 300, "yr_min": 2018},
        ],
    },
    "audi s5": {
        "display": "Audi S5",
        "make": "Audi",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 62, "yr_min": 2008},
            {"name": "Sport Differential / Drive Controller", "rarity": "Epic", "low": 380, "high": 900, "cost": 42, "yr_min": 2012, "option": True},
            {"name": "B&O Sound System", "rarity": "Rare", "low": 240, "high": 580, "cost": 38, "yr_min": 2008},
            {"name": "S Sport Seats (pair)", "rarity": "Rare", "low": 480, "high": 1050, "cost": 55, "yr_min": 2008},
        ],
    },
    "audi s6": {
        "display": "Audi S6",
        "make": "Audi",
        "year_range": (2007, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 600, "high": 1350, "cost": 68, "yr_min": 2013},
            {"name": "MMI / Virtual Cockpit", "rarity": "Epic", "low": 380, "high": 900, "cost": 48, "yr_min": 2013},
            # S-tuned adaptive air suspension is STANDARD on the US S6 — no option flag.
            {"name": "Air Suspension Compressor", "rarity": "Legendary", "low": 380, "high": 950, "cost": 44, "yr_min": 2013},
            {"name": "B&O Advanced Audio", "rarity": "Epic", "low": 450, "high": 1050, "cost": 48, "trim": ["Prestige"], "option": True},
        ],
    },
    "audi s7": {
        "display": "Audi S7",
        "make": "Audi",
        "year_range": (2012, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Epic", "low": 650, "high": 1450, "cost": 72, "yr_min": 2012},
            {"name": "MMI / Dual Touchscreens", "rarity": "Epic", "low": 400, "high": 950, "cost": 50, "yr_min": 2012},
            # Standard on US S7 — no option flag.
            {"name": "Sport Air Suspension Valve Block", "rarity": "Legendary", "low": 400, "high": 1000, "cost": 45, "yr_min": 2012},
        ],
    },
    "audi s8": {
        "display": "Audi S8",
        "make": "Audi",
        "year_range": (2007, 2024),
        "top_parts": [
            {"name": "OEM Laser / LED Headlights (pair)", "rarity": "Legendary", "low": 900, "high": 2100, "cost": 85, "yr_min": 2013},
            {"name": "Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 3500, "high": 8500, "cost": 350, "yr_min": 2013},
            {"name": "B&O Advanced Sound", "rarity": "Epic", "low": 650, "high": 1500, "cost": 52, "yr_min": 2013, "option": True},
        ],
    },
    "audi a5": {
        "display": "Audi A5 / S5",
        "make": "Audi",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 450, "high": 1000, "cost": 60, "yr_min": 2008},
            {"name": "MMI / Virtual Cockpit", "rarity": "Epic", "low": 280, "high": 700, "cost": 46, "yr_min": 2013},
            {"name": "B&O Premium Audio", "rarity": "Rare", "low": 220, "high": 560, "cost": 40, "trim": ["Prestige", "Premium Plus"], "option": True},
            {"name": "Convertible Top Motor (Cabriolet)", "rarity": "Legendary", "low": 500, "high": 1300, "cost": 60, "trim": ["Cabriolet", "Convertible"]},
        ],
    },
    "audi a6": {
        "display": "Audi A6 / S6",
        "make": "Audi",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Epic", "low": 550, "high": 1300, "cost": 70, "yr_min": 2012},
            {"name": "MMI Touch / Dual Screen Assembly", "rarity": "Epic", "low": 350, "high": 850, "cost": 48, "yr_min": 2012},
            # Air suspension only exists on the S6 here (standard there, never fitted to a
            # plain A6) — listings rarely distinguish S6 from A6, so option flag.
            {"name": "Air Suspension Compressor / Valve Block", "rarity": "Legendary", "low": 300, "high": 850, "cost": 40, "yr_min": 2012, "option": True},
            {"name": "Bang & Olufsen 3D / Advanced Sound", "rarity": "Epic", "low": 400, "high": 1000, "cost": 48, "trim": ["Prestige"], "option": True},
            {"name": "Heated / Ventilated Seats (pair)", "rarity": "Rare", "low": 400, "high": 1000, "cost": 55, "yr_min": 2012},
        ],
    },
    "audi rs6": {
        "display": "Audi RS6",
        "make": "Audi",
        "year_range": (2003, 2024),
        "top_parts": [
            {"name": "OEM Laser / LED Headlights (pair)", "rarity": "Legendary", "low": 1200, "high": 3000, "cost": 100, "yr_min": 2021},
            {"name": "Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 4000, "high": 10000, "cost": 400, "yr_min": 2021},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 2000, "high": 5000, "cost": 200, "yr_min": 2021},
        ],
    },
    "audi a7": {
        "display": "Audi A7 / S7",
        "make": "Audi",
        "year_range": (2012, 2024),
        "top_parts": [
            {"name": "OEM LED / HD Matrix Headlights (pair)", "rarity": "Epic", "low": 600, "high": 1400, "cost": 72, "yr_min": 2012},
            {"name": "MMI / Pop-Up Screen + Controller", "rarity": "Epic", "low": 300, "high": 750, "cost": 45, "yr_min": 2012},
            # Same as A6/S6: only the S7 carries air (std there), plain A7 never.
            {"name": "Air Suspension Module", "rarity": "Legendary", "low": 350, "high": 900, "cost": 42, "yr_min": 2012, "option": True},
            {"name": "B&O Advanced Sound", "rarity": "Epic", "low": 450, "high": 1100, "cost": 50, "trim": ["Prestige"], "option": True},
        ],
    },
    "audi rs7": {
        "display": "Audi RS7",
        "make": "Audi",
        "year_range": (2014, 2024),
        "top_parts": [
            {"name": "OEM Laser / Matrix Headlights (pair)", "rarity": "Legendary", "low": 1000, "high": 2500, "cost": 95, "yr_min": 2014},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 1800, "high": 4200, "cost": 180, "yr_min": 2014},
            {"name": "Carbon Brakes / Rotors (set)", "rarity": "Legendary", "low": 2500, "high": 6000, "cost": 250, "yr_min": 2014},
        ],
    },
    "audi a8": {
        "display": "Audi A8 / S8",
        "make": "Audi",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "OEM LED / Laser Headlights (pair)", "rarity": "Legendary", "low": 800, "high": 2000, "cost": 88, "yr_min": 2011},
            {"name": "Rear Seat Entertainment / Screens", "rarity": "Epic", "low": 400, "high": 1000, "cost": 35, "yr_min": 2011},
            # Adaptive air std on every A8/S8 — no option flag.
            {"name": "Air Suspension Compressor / Struts", "rarity": "Legendary", "low": 400, "high": 1100, "cost": 45, "yr_min": 2004},
            {"name": "Bang & Olufsen Advanced Sound", "rarity": "Epic", "low": 600, "high": 1500, "cost": 55, "trim": ["L", "Prestige"], "option": True},
            {"name": "Night Vision / Thermal Camera", "rarity": "Legendary", "low": 500, "high": 1200, "cost": 40, "yr_min": 2011},
        ],
    },
    "audi q3": {
        "display": "Audi Q3",
        "make": "Audi",
        "year_range": (2015, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 55, "yr_min": 2015},
            {"name": "MMI / Virtual Cockpit", "rarity": "Epic", "low": 250, "high": 600, "cost": 42, "yr_min": 2015},
            {"name": "Panoramic Sunroof Motor", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2015, "option": True},
        ],
    },
    "audi q4": {
        "display": "Audi Q4 e-tron",
        "make": "Audi",
        "year_range": (2022, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 62, "yr_min": 2022},
            {"name": "MMI / Touch Display Assembly", "rarity": "Epic", "low": 400, "high": 950, "cost": 50, "yr_min": 2022},
            {"name": "On-Board Charger / DC-DC (verify)", "rarity": "Epic", "low": 400, "high": 1000, "cost": 40, "yr_min": 2022},
        ],
    },
    "audi q5": {
        "display": "Audi Q5 / SQ5",
        "make": "Audi",
        "year_range": (2009, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 450, "high": 1050, "cost": 60, "yr_min": 2009},
            {"name": "MMI / MMI Touch + Screen", "rarity": "Epic", "low": 280, "high": 700, "cost": 45, "yr_min": 2009},
            {"name": "Bang & Olufsen / B&O Audio", "rarity": "Rare", "low": 220, "high": 560, "cost": 38, "trim": ["Premium Plus", "Prestige"], "option": True},
            {"name": "Panoramic Roof Motor / Tracks", "rarity": "Rare", "low": 180, "high": 480, "cost": 32, "yr_min": 2009},
            {"name": "Quattro / Differential Controller", "rarity": "Rare", "low": 200, "high": 500, "cost": 30, "yr_min": 2009},
        ],
    },
    "audi sq5": {
        "display": "Audi SQ5",
        "make": "Audi",
        "year_range": (2014, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Epic", "low": 550, "high": 1250, "cost": 65, "yr_min": 2014},
            {"name": "Sport Differential / Adaptive Damper Module", "rarity": "Epic", "low": 450, "high": 1000, "cost": 52, "yr_min": 2014, "option": True},
            {"name": "B&O / Premium Audio", "rarity": "Rare", "low": 260, "high": 620, "cost": 40, "yr_min": 2014},
            {"name": "S Sport Seats (pair)", "rarity": "Rare", "low": 500, "high": 1100, "cost": 58, "yr_min": 2014},
        ],
    },
    "audi q7": {
        "display": "Audi Q7 / SQ7",
        "make": "Audi",
        "year_range": (2007, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 550, "high": 1300, "cost": 68, "yr_min": 2011},
            {"name": "MMI / Virtual Cockpit + Rear Tablets", "rarity": "Epic", "low": 350, "high": 900, "cost": 48, "yr_min": 2017},
            # Optional adaptive-chassis pkg on Q7 (std on the SQ7 entry below).
            {"name": "Air Suspension Compressor", "rarity": "Legendary", "low": 350, "high": 950, "cost": 42, "yr_min": 2011, "option": True},
            {"name": "Third Row / Power Seat Motors", "rarity": "Rare", "low": 200, "high": 550, "cost": 32, "yr_min": 2015},
            {"name": "B&O 3D Sound", "rarity": "Epic", "low": 500, "high": 1200, "cost": 50, "trim": ["Prestige"], "option": True},
        ],
    },
    "audi sq7": {
        "display": "Audi SQ7",
        "make": "Audi",
        "year_range": (2017, 2024),
        "top_parts": [
            {"name": "OEM HD Matrix LED (pair)", "rarity": "Legendary", "low": 800, "high": 1900, "cost": 78, "yr_min": 2017},
            {"name": "Sport Air Suspension / Roll Control Module", "rarity": "Legendary", "low": 500, "high": 1200, "cost": 48, "yr_min": 2017},
            {"name": "B&O 3D Advanced Audio", "rarity": "Epic", "low": 550, "high": 1300, "cost": 52, "yr_min": 2017},
        ],
    },
    "audi q8": {
        "display": "Audi Q8 / RS Q8",
        "make": "Audi",
        "year_range": (2019, 2024),
        "top_parts": [
            {"name": "OEM HD Matrix LED (pair)", "rarity": "Legendary", "low": 900, "high": 2200, "cost": 85, "yr_min": 2019},
            {"name": "MMI Touch Response / Dual Screens", "rarity": "Epic", "low": 450, "high": 1000, "cost": 52, "yr_min": 2019},
            {"name": "B&O Advanced 3D Audio", "rarity": "Epic", "low": 600, "high": 1400, "cost": 55, "trim": ["Prestige"]},  # KEEP trim-gated: B&O Premium 3D std on Q8 Prestige (2019+)
            # 2019+ Q8: air suspension is the $2,750 Adaptive Chassis Package, optional on
            # every trim (std setup is steel + adaptive dampers).
            {"name": "Air Suspension + Roll Stabilization Module", "rarity": "Legendary", "low": 500, "high": 1300, "cost": 48, "yr_min": 2019, "option": True},
        ],
    },
    "audi rs q8": {
        "display": "Audi RS Q8",
        "make": "Audi",
        # Yards often list without the space ("RSQ8") — one entry, two spellings.
        "match": ["rs q8", "rsq8"],
        "year_range": (2020, 2024),
        "top_parts": [
            {"name": "OEM Laser / Matrix Headlights (pair)", "rarity": "Legendary", "low": 1200, "high": 2800, "cost": 95, "yr_min": 2020},
            {"name": "Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 5000, "high": 12000, "cost": 450, "yr_min": 2020},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 2200, "high": 5000, "cost": 200, "yr_min": 2020},
        ],
    },
    "audi sq8": {
        "display": "Audi SQ8",
        "make": "Audi",
        "year_range": (2020, 2024),
        "top_parts": [
            {"name": "OEM HD Matrix LED (pair)", "rarity": "Legendary", "low": 950, "high": 2300, "cost": 88, "yr_min": 2020},
            {"name": "Sport Air Suspension Module", "rarity": "Legendary", "low": 550, "high": 1350, "cost": 50, "yr_min": 2020},
            {"name": "B&O Advanced Audio", "rarity": "Epic", "low": 650, "high": 1450, "cost": 54, "yr_min": 2020, "option": True},
        ],
    },
    "audi tt": {
        "display": "Audi TT / TTS / TT RS",
        "make": "Audi",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 55, "yr_min": 2008},
            {"name": "Virtual Cockpit Cluster", "rarity": "Epic", "low": 350, "high": 800, "cost": 45, "yr_min": 2015},
            {"name": "Magnetic Ride / Suspension Module", "rarity": "Rare", "low": 250, "high": 650, "cost": 35, "trim": ["TTS", "RS"]},
            {"name": "Convertible Top Motor (Roadster)", "rarity": "Legendary", "low": 500, "high": 1300, "cost": 58, "trim": ["Roadster"]},
        ],
    },
    "audi e-tron": {
        "display": "Audi e-tron / e-tron GT",
        "make": "Audi",
        "year_range": (2019, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Epic", "low": 700, "high": 1600, "cost": 75, "yr_min": 2019},
            {"name": "MMI / Dual Touchscreens", "rarity": "Epic", "low": 450, "high": 1000, "cost": 50, "yr_min": 2019},
            {"name": "Bang & Olufsen 3D Sound", "rarity": "Epic", "low": 500, "high": 1200, "cost": 50, "yr_min": 2019},
            {"name": "Air Suspension / Compressor", "rarity": "Legendary", "low": 400, "high": 1100, "cost": 45, "yr_min": 2019},
        ],
    },
    "bmw 3": {
        "display": "BMW 3 Series",
        "make": "BMW",
        "year_range": (1999, 2024),
        # 2026-09 generation-fits audit: clusters, iDrive units, lights and
        # seats don't interchange across E36/E46/E90/F30/G20 — one wide band
        # produced "fits 1992-2024" badges. Split per generation:
        # E36 1992-1998, E46 1999-2005, E90 2006-2011, F30 2012-2018, G20 2019+.
        "top_parts": [
            # E36 (1992-1998) — enthusiast/drift demand keeps interior + lights moving
            {"name": "Headlights (E36, pair)", "rarity": "Rare", "low": 80, "high": 220, "cost": 25, "yr_max": 1998},
            {"name": "Instrument Cluster (E36, M3/sport worth more)", "rarity": "Rare", "low": 80, "high": 280, "cost": 20, "yr_max": 1998},
            {"name": "Sport Seats (E36 Vaders top the range, pair)", "rarity": "Rare", "low": 250, "high": 700, "cost": 55, "yr_max": 1998, "trim": ["M Sport", "328", "M3"]},
            # E46 (1999-2005) — the volume yard 3-series; angel-eye xenons sell on sight
            {"name": "OEM Headlight Assembly (E46 halogen/xenon, pair)", "rarity": "Rare", "low": 120, "high": 350, "cost": 30, "yr_min": 1999, "yr_max": 2005},
            {"name": "Instrument Cluster (E46, M3/sport worth more)", "rarity": "Rare", "low": 100, "high": 400, "cost": 20, "yr_min": 1999, "yr_max": 2005},
            {"name": "Sport Seats (E46, pair)", "rarity": "Rare", "low": 300, "high": 700, "cost": 55, "yr_min": 1999, "yr_max": 2005, "trim": ["M Sport", "330", "M3"]},
            # German-sensor adds (2026-09-21 audit): used tested E46 DSC hydraulic
            # modules $250 US / €59-225 EU vs $2,030 new OEM — rebuilders and
            # owners both buy. MAF: new OEM VDO $171-272; cheap clones exist but
            # BMW buyers pay the OEM premium (clone MAFs are a known lemon).
            {"name": "ABS/DSC Hydraulic Module (E46)", "rarity": "Epic", "low": 80, "high": 220, "cost": 15, "yr_min": 1999, "yr_max": 2005},
            {"name": "MAF (OEM Siemens/VDO, M54)", "rarity": "Uncommon", "low": 40, "high": 90, "cost": 10, "yr_min": 1999, "yr_max": 2005},
            # E90 (2006-2011) — first iDrive cars; CCC screens die, working pulls move fast
            {"name": "iDrive Head Unit (E90 CCC/CIC)", "rarity": "Rare", "low": 120, "high": 320, "cost": 40, "yr_min": 2006, "yr_max": 2011},
            {"name": "Harman Kardon / Logic7 Amp + Speakers (E90)", "rarity": "Rare", "low": 120, "high": 320, "cost": 35, "yr_min": 2006, "yr_max": 2011},
            {"name": "Sport Seats (E90, pair)", "rarity": "Rare", "low": 300, "high": 700, "cost": 55, "yr_min": 2006, "yr_max": 2011, "trim": ["M Sport", "335i"]},
            # F30 (2012-2018) — NBT iDrive > the old CCC; LED/adaptive xenon pairs
            {"name": "iDrive Head Unit (F30 NBT)", "rarity": "Epic", "low": 200, "high": 500, "cost": 50, "yr_min": 2012, "yr_max": 2018},
            {"name": "OEM LED/Adaptive Headlights (F30, pair)", "rarity": "Epic", "low": 350, "high": 800, "cost": 65, "yr_min": 2012, "yr_max": 2018},
            {"name": "Harman Kardon Amp + Speakers (F30)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2012, "yr_max": 2018},
            {"name": "Sport Seats (F30, pair)", "rarity": "Rare", "low": 300, "high": 700, "cost": 55, "yr_min": 2012, "yr_max": 2018, "trim": ["M Sport", "335i", "340i"]},
            # G20 (2019+) — MGU touch iDrive + full-LED/laser lights top the 3er range
            {"name": "iDrive Touch Head Unit (G20 MGU)", "rarity": "Epic", "low": 250, "high": 600, "cost": 50, "yr_min": 2019},
            {"name": "OEM LED/Laser Headlights (G20, pair)", "rarity": "Epic", "low": 450, "high": 1000, "cost": 65, "yr_min": 2019},
            {"name": "Harman Kardon Amp + Speakers (G20)", "rarity": "Rare", "low": 180, "high": 450, "cost": 35, "yr_min": 2019},
            {"name": "Sport Seats (G20, pair)", "rarity": "Rare", "low": 350, "high": 750, "cost": 55, "yr_min": 2019, "trim": ["M Sport", "330i", "M340i"]},
        ],
    },
    "bmw m3": {
        "display": "BMW M3",
        "make": "BMW",
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "Carbon Roof Panel", "rarity": "Legendary", "low": 800, "high": 2000, "cost": 100, "yr_min": 2008},
            {"name": "OEM Carbon Bucket Seats (pair)", "rarity": "Legendary", "low": 2000, "high": 4500, "cost": 200, "yr_min": 2015},
            {"name": "Competition Wheels (set)", "rarity": "Epic", "low": 1200, "high": 2800, "cost": 150, "yr_min": 2015},
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 70, "yr_min": 2015},
        ],
    },
    # --- BMW SUVs (keyword matches model substring: X1, X3, X3 M40i, etc.)
    "x1": {
        "display": "BMW X1",
        "make": "BMW",
        "year_range": (2013, 2024),
        "top_parts": [
            {"name": "OEM LED / Xenon Headlights (pair)", "rarity": "Epic", "low": 350, "high": 800, "cost": 55, "yr_min": 2016},
            {"name": "iDrive / Navigation Module (CIC/NBT)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40, "yr_min": 2013},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 120, "high": 320, "cost": 30, "yr_min": 2013, "option": True},
            {"name": "Power Liftgate Motor + Struts", "rarity": "Rare", "low": 100, "high": 280, "cost": 22, "yr_min": 2016},
        ],
    },
    "x2": {
        "display": "BMW X2",
        "make": "BMW",
        "year_range": (2018, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "yr_min": 2018},
            {"name": "iDrive Touchscreen / Head Unit", "rarity": "Epic", "low": 250, "high": 600, "cost": 45, "yr_min": 2018},
            {"name": "Harman Kardon / Premium Audio", "rarity": "Rare", "low": 150, "high": 380, "cost": 32, "yr_min": 2018},
        ],
    },
    "x3": {
        "display": "BMW X3",
        "make": "BMW",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 950, "cost": 60, "yr_min": 2011},
            {"name": "Panoramic Sunroof Motor + Tracks", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2011, "option": True},
            {"name": "iDrive / CIC / NBT Navigation Unit", "rarity": "Epic", "low": 220, "high": 580, "cost": 45, "yr_min": 2007},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 140, "high": 380, "cost": 32, "yr_min": 2007, "option": True},
            {"name": "Transfer Case Actuator (common failure)", "rarity": "Epic", "low": 200, "high": 500, "cost": 25, "yr_min": 2004},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 120, "high": 320, "cost": 22, "yr_min": 2011},
        ],
    },
    "x4": {
        "display": "BMW X4",
        "make": "BMW",
        "year_range": (2015, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 450, "high": 1000, "cost": 65, "yr_min": 2015},
            {"name": "iDrive / Digital Cockpit Module", "rarity": "Epic", "low": 280, "high": 650, "cost": 48, "yr_min": 2018},
            {"name": "Harman Kardon / Premium Audio", "rarity": "Rare", "low": 160, "high": 420, "cost": 35, "yr_min": 2015},
        ],
    },
    # X5 headlights: low/high ≈ typical eBay *sold* used OEM pairs (varies by trim; laser/G05 top end).
    "x5": {
        "display": "BMW X5",
        "make": "BMW",
        # E53 launched as MY2000 — floor extended from 2001.
        "year_range": (2000, 2024),
        "top_parts": [
            # E53/E70 self-leveling rear air suspension — same failure-driven
            # demand and band as the audited Quadra-Lift/Explorer compressors.
            {"name": "Rear Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_max": 2013},
            {"name": "Headlight assemblies (pair, E70 xenon/halogen)", "rarity": "Rare", "low": 140, "high": 420, "cost": 45, "yr_min": 2007, "yr_max": 2013},
            {"name": "Headlight assemblies (pair, F15 LED adaptive)", "rarity": "Epic", "low": 260, "high": 680, "cost": 58, "yr_min": 2014, "yr_max": 2018},
            {"name": "Headlight assemblies (pair, G05+ LED / laser)", "rarity": "Epic", "low": 420, "high": 1100, "cost": 65, "yr_min": 2019},
            {"name": "Air Suspension Compressor / Valve Block", "rarity": "Legendary", "low": 250, "high": 700, "cost": 35, "yr_min": 2007},
            {"name": "iDrive / Navigation (CIC/NBT)", "rarity": "Epic", "low": 220, "high": 600, "cost": 45, "yr_min": 2007},
            # X5 3rd row is a genuine (rare) option — old '(if equipped)' name suffix
            # normalized to the option flag.
            {"name": "Third Row / Power Seat Motors", "rarity": "Rare", "low": 150, "high": 450, "cost": 30, "yr_min": 2014, "option": True},
            {"name": "Harman Kardon / Logic7 Amp + Speakers", "rarity": "Rare", "low": 150, "high": 420, "cost": 35, "yr_min": 2004},
            {"name": "Transfer Case / XDrive Actuator", "rarity": "Epic", "low": 180, "high": 480, "cost": 28, "yr_min": 2004},
        ],
    },
    "x6": {
        "display": "BMW X6",
        "make": "BMW",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "Headlight assemblies (pair, E71)", "rarity": "Rare", "low": 150, "high": 450, "cost": 48, "yr_min": 2008, "yr_max": 2014},
            {"name": "Headlight assemblies (pair, F16 / G06 LED)", "rarity": "Epic", "low": 280, "high": 780, "cost": 65, "yr_min": 2015},
            {"name": "iDrive / Wide Screen Assembly", "rarity": "Epic", "low": 280, "high": 700, "cost": 48, "yr_min": 2012},
            {"name": "Air Suspension Module / Compressor", "rarity": "Legendary", "low": 280, "high": 750, "cost": 38, "yr_min": 2008},
            {"name": "Harman Kardon / B&O Premium Audio", "rarity": "Rare", "low": 180, "high": 480, "cost": 38, "yr_min": 2008},
        ],
    },
    "x7": {
        "display": "BMW X7",
        "make": "BMW",
        "year_range": (2019, 2024),
        "top_parts": [
            {"name": "OEM Laser / LED Headlights (pair)", "rarity": "Legendary", "low": 800, "high": 2200, "cost": 90, "yr_min": 2019},
            {"name": "Curved Display / iDrive 8 Module", "rarity": "Legendary", "low": 500, "high": 1200, "cost": 60, "yr_min": 2019},
            {"name": "Bowers & Wilkins / Premium Audio", "rarity": "Epic", "low": 400, "high": 1000, "cost": 50, "option": True},
            {"name": "Air Suspension Compressor", "rarity": "Epic", "low": 350, "high": 900, "cost": 40, "yr_min": 2019},
        ],
    },
    # --- BMW sedans / coupes by chassis line (keyword in "bmw 528i", "5 series", etc.)
    "bmw 1": {
        "display": "BMW 1 Series",
        "make": "BMW",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "iDrive / Business Navigation", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2008},
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 300, "high": 750, "cost": 50, "yr_min": 2012},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 120, "high": 320, "cost": 28, "yr_min": 2012, "option": True},
            {"name": "Sport / M Sport Seats (pair)", "rarity": "Rare", "low": 250, "high": 600, "cost": 45, "trim": ["M Sport", "135", "128"]},
        ],
    },
    "bmw 4": {
        "display": "BMW 4 Series",
        "make": "BMW",
        "year_range": (2014, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 450, "high": 1000, "cost": 62, "yr_min": 2014},
            {"name": "iDrive / NBT / Touch Controller", "rarity": "Epic", "low": 240, "high": 580, "cost": 45, "yr_min": 2014},
            {"name": "Harman Kardon / Premium Audio", "rarity": "Rare", "low": 160, "high": 420, "cost": 35, "yr_min": 2014},
            {"name": "Retractable Hardtop Motors (convertible)", "rarity": "Legendary", "low": 400, "high": 1100, "cost": 55, "trim": ["Convertible"]},
        ],
    },
    "bmw 5": {
        "display": "BMW 5 Series",
        "make": "BMW",
        "year_range": (1997, 2024),
        # 2026-09 generation-fits audit: every electronics/lighting/seat part
        # below used one 2004-2024 band, but an E60 cluster, F10 cluster and
        # G30 cluster are entirely different parts (same for CCC/CIC vs NBT vs
        # EVO iDrive, xenon vs LED vs laser lights). Split per generation:
        # E39 1997-2003, E60 2004-2010, F10 2011-2016, G30 2017-2023 (+G60 '24).
        "top_parts": [
            # E39 (1997-2003) — angel-eye halogen/xenon pairs sell steadily to the enthusiast crowd
            {"name": "Headlights (E39 halo, pair)", "rarity": "Rare", "low": 100, "high": 280, "cost": 30, "yr_max": 2003},
            {"name": "Instrument Cluster (E39, pixel-perfect worth more)", "rarity": "Rare", "low": 60, "high": 160, "cost": 20, "yr_max": 2003},
            {"name": "DSP Amp + Speakers (E39)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 25, "yr_max": 2003},
            {"name": "Comfort Seats (E39, pair)", "rarity": "Rare", "low": 200, "high": 500, "cost": 50, "yr_max": 2003, "trim": ["540", "530", "M Sport"]},
            # shares the E46-family DSC hydraulic unit — same evidence (2026-09-21)
            {"name": "ABS/DSC Hydraulic Module (E39)", "rarity": "Epic", "low": 80, "high": 220, "cost": 15, "yr_max": 2003},
            # E60 (2004-2010) — xenon pairs cheaper than the later LED stuff; CCC/CIC units age poorly
            {"name": "OEM Xenon Headlights (E60, pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 45, "yr_min": 2004, "yr_max": 2010},
            {"name": "iDrive Head Unit (E60 CCC/CIC)", "rarity": "Rare", "low": 100, "high": 280, "cost": 40, "yr_min": 2004, "yr_max": 2010},
            {"name": "Harman Kardon / Logic7 System (E60)", "rarity": "Rare", "low": 100, "high": 280, "cost": 35, "yr_min": 2004, "yr_max": 2010},
            {"name": "Comfort Seats / Multi-Contour (E60, pair)", "rarity": "Rare", "low": 300, "high": 700, "cost": 55, "yr_min": 2004, "yr_max": 2010, "trim": ["M Sport", "535", "540", "550"]},
            {"name": "Instrument Cluster (E60)", "rarity": "Rare", "low": 80, "high": 220, "cost": 25, "yr_min": 2004, "yr_max": 2010},
            # F10 (2011-2016) — adaptive xenon/LED; NBT retrofits keep head-unit demand strong
            {"name": "OEM Adaptive Xenon/LED Headlights (F10, pair)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "yr_min": 2011, "yr_max": 2016},
            {"name": "iDrive Head Unit (F10 CIC/NBT — NBT worth more)", "rarity": "Epic", "low": 180, "high": 450, "cost": 45, "yr_min": 2011, "yr_max": 2016},
            {"name": "Harman Kardon System (F10)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2011, "yr_max": 2016},
            {"name": "Comfort Seats / Multi-Contour (F10, pair)", "rarity": "Rare", "low": 350, "high": 850, "cost": 55, "yr_min": 2011, "yr_max": 2016, "trim": ["M Sport", "535", "540", "550"]},
            {"name": "Instrument Cluster (F10, HUD cars worth more)", "rarity": "Rare", "low": 120, "high": 320, "cost": 28, "yr_min": 2011, "yr_max": 2016},
            # G30 (2017+) — full-LED/laser lights and EVO touch iDrive command the top of the range
            {"name": "OEM LED/Laser Headlights (G30, pair)", "rarity": "Epic", "low": 400, "high": 950, "cost": 60, "yr_min": 2017},
            {"name": "iDrive Touch Head Unit (G30 EVO)", "rarity": "Epic", "low": 250, "high": 600, "cost": 48, "yr_min": 2017},
            {"name": "Harman Kardon / B&W System (G30)", "rarity": "Rare", "low": 180, "high": 450, "cost": 38, "yr_min": 2017},
            {"name": "Comfort Seats / Multi-Contour (G30, pair)", "rarity": "Rare", "low": 400, "high": 900, "cost": 55, "yr_min": 2017, "trim": ["M Sport", "535", "540", "550"]},
            {"name": "Digital Instrument Cluster (G30 Live Cockpit)", "rarity": "Epic", "low": 200, "high": 500, "cost": 30, "yr_min": 2017},
        ],
    },
    "bmw 6": {
        "display": "BMW 6 Series",
        "make": "BMW",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 550, "high": 1300, "cost": 70, "yr_min": 2012},
            {"name": "iDrive / Wide Display", "rarity": "Epic", "low": 300, "high": 750, "cost": 48, "yr_min": 2004},
            {"name": "Harman Kardon / Premium Audio", "rarity": "Rare", "low": 200, "high": 520, "cost": 38, "yr_min": 2004},
            {"name": "Convertible Top Motor / Hydraulics", "rarity": "Legendary", "low": 500, "high": 1400, "cost": 60, "trim": ["Convertible"]},
        ],
    },
    "bmw 7": {
        "display": "BMW 7 Series",
        "make": "BMW",
        "year_range": (2002, 2024),
        "top_parts": [
            {"name": "OEM LED / Laser Headlights (pair)", "rarity": "Legendary", "low": 700, "high": 1800, "cost": 85, "yr_min": 2009},
            {"name": "Rear Seat Entertainment Screens", "rarity": "Epic", "low": 300, "high": 800, "cost": 35, "yr_min": 2006},
            {"name": "Air Suspension Compressor / Valve", "rarity": "Legendary", "low": 300, "high": 850, "cost": 38, "yr_min": 2002},
            {"name": "Bowers & Wilkins / Premium Audio", "rarity": "Epic", "low": 400, "high": 1100, "cost": 48, "option": True},
            {"name": "iDrive / Curved Display Module", "rarity": "Epic", "low": 400, "high": 1000, "cost": 55, "yr_min": 2016},
        ],
    },
    "z3": {
        "display": "BMW Z3",
        "make": "BMW",
        "year_range": (1996, 2002),
        "top_parts": [
            {"name": "Manual / SMG Cluster + Gauges", "rarity": "Rare", "low": 120, "high": 350, "cost": 18},
            {"name": "Soft Top Frame + Latches (roadster)", "rarity": "Rare", "low": 200, "high": 500, "cost": 35},
            {"name": "OEM Headlights (pair)", "rarity": "Uncommon", "low": 80, "high": 220, "cost": 22},
        ],
    },
    "z4": {
        "display": "BMW Z4",
        "make": "BMW",
        "year_range": (2003, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 55, "yr_min": 2009},
            {"name": "iDrive / Navigation (E89/G29)", "rarity": "Epic", "low": 200, "high": 550, "cost": 40, "yr_min": 2009},
            # Retractable hardtop = E89 (2009+) only, where it's standard; 2006-08 E85
            # roadsters were soft-top (year fix, no option flag needed).
            {"name": "Retractable Hardtop Motor / Hydraulics", "rarity": "Legendary", "low": 500, "high": 1400, "cost": 60, "yr_min": 2009},
            {"name": "Harman Kardon Audio", "rarity": "Rare", "low": 150, "high": 400, "cost": 32, "yr_min": 2006},
        ],
    },
    # M5 / M550: "bmw 5" does not match "bmw m5" (letter M between); M550i matches "bmw m5" substring
    "bmw m5": {
        "display": "BMW M5",
        "make": "BMW",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "OEM Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 2000, "high": 5000, "cost": 200, "yr_min": 2012},
            {"name": "Competition Wheels (set)", "rarity": "Epic", "low": 1500, "high": 3500, "cost": 120, "yr_min": 2018},
            {"name": "OEM LED / Laser Headlights (pair)", "rarity": "Epic", "low": 600, "high": 1400, "cost": 72, "yr_min": 2012},
            {"name": "M Sport Exhaust (axle-back / valved)", "rarity": "Rare", "low": 400, "high": 1200, "cost": 45, "yr_min": 2005},
            {"name": "iDrive / Digital Cockpit Module", "rarity": "Epic", "low": 350, "high": 850, "cost": 50, "yr_min": 2012},
        ],
    },
    "charger": {
        "display": "Dodge Charger",
        "make": "Dodge",
        "year_range": (2006, 2024),
        "top_parts": [
            {"name": "Uconnect 8.4\" Touchscreen", "rarity": "Epic", "low": 250, "high": 550, "cost": 45, "yr_min": 2011},
            {"name": "SRT / Scat Brembo Calipers (set)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SRT", "Scat", "Hellcat", "Redeye"]},
            {"name": "Power-Fold Mirrors (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 28, "yr_min": 2011},
            {"name": "Alpine / Beats Amp + Speakers", "rarity": "Rare", "low": 120, "high": 300, "cost": 30},
        ],
    },
    "challenger": {
        "display": "Dodge Challenger",
        "make": "Dodge",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "R/T Shaker Hood + Intake", "rarity": "Epic", "low": 300, "high": 700, "cost": 60, "option": True},
            {"name": "HID/LED Headlights (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 30, "option": True},
            {"name": "Uconnect 8.4\" Touchscreen", "rarity": "Epic", "low": 250, "high": 550, "cost": 45, "yr_min": 2011},
            {"name": "SRT / Hellcat Hood (composite)", "rarity": "Epic", "low": 400, "high": 1000, "cost": 55, "trim": ["SRT", "Hellcat", "Demon", "Redeye"]},
            {"name": "SRT Brembo Calipers (set)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SRT", "Hellcat"]},
        ],
    },
    "golf": {
        "display": "Volkswagen Golf / GTI / R",
        "make": "Volkswagen",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "yr_min": 2015},
            {"name": "Discover Pro / MIB Touchscreen", "rarity": "Epic", "low": 250, "high": 550, "cost": 50, "yr_min": 2015},
            {"name": "Fender / Dynaudio Amp + Sub", "rarity": "Rare", "low": 150, "high": 350, "cost": 35, "trim": ["GTI", "R", "Autobahn"]},
            {"name": "GTI/R Recaro Seats (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 75, "trim": ["GTI", "R", "Clubsport"], "option": True},
        ],
    },
    "gti": {
        "display": "Volkswagen GTI",
        "make": "Volkswagen",
        "year_range": (2006, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "yr_min": 2015},
            {"name": "Discover Pro / MIB Touchscreen", "rarity": "Epic", "low": 250, "high": 550, "cost": 50, "yr_min": 2015},
            {"name": "Fender / Dynaudio Amp + Sub", "rarity": "Rare", "low": 150, "high": 350, "cost": 35},
            {"name": "GTI Recaro Seats (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 75, "option": True},
        ],
    },
    "jetta": {
        "display": "Volkswagen Jetta / GLI",
        "make": "Volkswagen",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Rare", "low": 250, "high": 550, "cost": 45, "yr_min": 2019},
            {"name": "MIB / Composition Touchscreen", "rarity": "Rare", "low": 180, "high": 400, "cost": 45, "yr_min": 2016},
            {"name": "GLI Brembo Calipers (set)", "rarity": "Epic", "low": 175, "high": 500, "cost": 50, "trim": ["GLI"]},
        ],
    },
    "g70": {
        "display": "Genesis G70",
        "make": "Genesis",
        "year_range": (2019, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1000, "cost": 65},
            {"name": "Lexicon Amp + Speakers", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
            {"name": "Digital Cluster / HUD Module", "rarity": "Rare", "low": 350, "high": 750, "cost": 50},
        ],
    },
    "cadillac cts": {
        "display": "Cadillac CTS / CTS-V",
        "make": "Cadillac",
        "year_range": (2003, 2019),
        "top_parts": [
            {"name": "Cue / Infotainment Touchscreen", "rarity": "Epic", "low": 200, "high": 500, "cost": 45, "yr_min": 2013},
            {"name": "Magnetic Ride Shocks (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["V", "V-Sport"]},
            {"name": "Brembo Calipers (set)", "rarity": "Epic", "low": 400, "high": 900, "cost": 55, "trim": ["V"]},
            # Base pre-2013 cars previously had zero un-gated parts.
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "ats": {
        "display": "Cadillac ATS / ATS-V",
        "make": "Cadillac",
        "year_range": (2013, 2019),
        "top_parts": [
            {"name": "Cue Touchscreen / Cluster", "rarity": "Epic", "low": 200, "high": 500, "cost": 45},
            {"name": "Bose / Premium Audio Amp", "rarity": "Rare", "low": 120, "high": 280, "cost": 30},
            {"name": "ATS-V Recaro Seats (pair)", "rarity": "Epic", "low": 800, "high": 1800, "cost": 100, "trim": ["V"], "option": True},
        ],
    },
    # =====================================================================
    # JDM / CLASSIC TOYOTA & FRIENDS — enthusiast communities where nearly
    # everything sells.  Keys use "make model" when the bare model string is
    # too generic (e.g. "pickup").
    # =====================================================================
    "toyota pickup": {
        "display": "Toyota Pickup (Hilux)",
        "make": "Toyota",
        "year_range": (1979, 1995),
        "top_parts": [
            {"name": "Tailgate (straight, w/ TOYOTA stamp)", "rarity": "Legendary", "low": 150, "high": 450, "cost": 30},
            {"name": "22RE EFI Intake/Throttle Body", "rarity": "Epic", "low": 100, "high": 250, "cost": 20},
            {"name": "Front Grille + Corner Lights (chrome)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Bench Seat (uncracked)", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
            {"name": "Rear Steel Bumper (straight)", "rarity": "Rare", "low": 60, "high": 150, "cost": 15},
            {"name": "Gauge Cluster w/ Tach", "rarity": "Epic", "low": 100, "high": 250, "cost": 10},
            {"name": "Sliding Rear Window", "rarity": "Rare", "low": 60, "high": 150, "cost": 10},
            # Vintage-EFI electronics (2026-09-21 audit): used OEM 22RE AFMs ask
            # ~$175 and sell out (importapart); new OEM Denso runs $600-1,200
            # where it exists at all. Band kept conservative vs asking prices.
            # yr_min 1985: EFI (22R-E) arrived MY1985 — earlier trucks are carbureted 22R, no AFM.
            {"name": "22RE AFM (Air Flow Meter)", "rarity": "Epic", "low": 80, "high": 180, "cost": 10, "yr_min": 1985},
            # NLA fragile interior: heater/climate panels crack and knobs walk
            # off — asks $80-250 for working units (2026-09-21).
            {"name": "Climate Control Panel (works, knobs intact)", "rarity": "Rare", "low": 40, "high": 100, "cost": 10},
        ],
    },
    "t100": {
        "display": "Toyota T100",
        "make": "Toyota",
        "year_range": (1993, 1998),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Epic", "low": 150, "high": 350, "cost": 30},
            {"name": "3RZ Intake/EFI Components", "rarity": "Epic", "low": 80, "high": 200, "cost": 15},
            {"name": "Bench Seat", "rarity": "Rare", "low": 80, "high": 250, "cost": 25},
            {"name": "Headlights + Corner Lights (clear)", "rarity": "Rare", "low": 60, "high": 150, "cost": 15},
        ],
    },
    "mr2": {
        "display": "Toyota MR2",
        "make": "Toyota",
        "year_range": (1985, 2005),
        "top_parts": [
            {"name": "T-Top Panels (pair, unleaky)", "rarity": "Legendary", "low": 300, "high": 800, "cost": 40, "yr_max": 1995},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            {"name": "Engine Lid / Trunk Lid", "rarity": "Epic", "low": 150, "high": 400, "cost": 25},
            {"name": "Rear Spoiler", "rarity": "Rare", "low": 100, "high": 250, "cost": 15},
            {"name": "SMT/Manual Shifter Assembly", "rarity": "Rare", "low": 80, "high": 200, "cost": 10},
        ],
    },
    "celica": {
        "display": "Toyota Celica",
        "make": "Toyota",
        "year_range": (1985, 2005),
        "top_parts": [
            {"name": "GT-S Seats (pair)", "rarity": "Epic", "low": 200, "high": 450, "cost": 40, "yr_min": 2000},
            {"name": "TRD/Action Package Body Pieces", "rarity": "Epic", "low": 150, "high": 400, "cost": 25, "yr_min": 2000},
            {"name": "Pop-Up Headlight Assemblies (pair)", "rarity": "Epic", "low": 150, "high": 350, "cost": 25, "yr_max": 1993},
            {"name": "Sunroof Assembly (complete)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20, "option": True},
            {"name": "Rear Spoiler", "rarity": "Rare", "low": 75, "high": 200, "cost": 15},
        ],
    },
    "supra": {
        "display": "Toyota Supra",
        "make": "Toyota",
        "year_range": (1979, 1998),
        "top_parts": [
            {"name": "Anything — whole car is gold (2JZ/7M, targa, interior)", "rarity": "Legendary", "low": 500, "high": 2000, "cost": 100},
            {"name": "Targa Top", "rarity": "Legendary", "low": 400, "high": 1200, "cost": 50},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 300, "high": 800, "cost": 50},
            {"name": "Gauge Cluster", "rarity": "Epic", "low": 150, "high": 400, "cost": 10},
        ],
    },
    "cressida": {
        "display": "Toyota Cressida",
        "make": "Toyota",
        "year_range": (1981, 1992),
        "top_parts": [
            {"name": "7M-GE Engine Accessories / Harness", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Power Seats (pair, clean)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
            {"name": "Gauge Cluster / Digital Dash", "rarity": "Epic", "low": 100, "high": 250, "cost": 10},
            {"name": "Grille + Trim (chrome)", "rarity": "Rare", "low": 60, "high": 150, "cost": 10},
        ],
    },
    "previa": {
        "display": "Toyota Previa",
        "make": "Toyota",
        "year_range": (1991, 1997),
        "top_parts": [
            {"name": "Supercharger (S/C models)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 30, "yr_min": 1994},
            # Captain chairs were an LE-package option.
            {"name": "Middle Captain Chairs (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40, "option": True},
            {"name": "Ice Maker / Cooler Console", "rarity": "Epic", "low": 100, "high": 250, "cost": 10},
            {"name": "AWD (All-Trac) Driveline Components", "rarity": "Rare", "low": 80, "high": 250, "cost": 30},
        ],
    },
    "lexus ls": {
        "display": "Lexus LS400 / LS430",
        "make": "Lexus",
        "year_range": (1990, 2006),
        "top_parts": [
            {"name": "1UZ-FE Starter/Coils/Accessories (swap gold)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 2000},
            {"name": "Nakamichi Amp + Speakers", "rarity": "Epic", "low": 150, "high": 350, "cost": 25},
            {"name": "Front Seats (heated, uncracked)", "rarity": "Rare", "low": 150, "high": 350, "cost": 40},
            {"name": "Wood Trim Kit (complete)", "rarity": "Rare", "low": 80, "high": 250, "cost": 10},
            {"name": "OEM Wheels (set)", "rarity": "Rare", "low": 150, "high": 350, "cost": 60},
        ],
    },
    "lexus sc": {
        "display": "Lexus SC300 / SC400",
        "make": "Lexus",
        "year_range": (1992, 2000),
        "top_parts": [
            {"name": "2JZ-GE Accessories / Harness (SC300)", "rarity": "Legendary", "low": 150, "high": 400, "cost": 25},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            {"name": "5-Speed Pedal Box / Shifter (manual SC300)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 15},
            {"name": "Headlights (clear)", "rarity": "Rare", "low": 100, "high": 250, "cost": 20},
            {"name": "Gauge Cluster", "rarity": "Rare", "low": 80, "high": 200, "cost": 10},
        ],
    },
    "lexus gs": {
        "display": "Lexus GS300 / GS400 / GS430",
        "make": "Lexus",
        "year_range": (1993, 2011),
        "top_parts": [
            {"name": "2JZ-GE Accessories / Harness", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 2005},
            {"name": "Front Seats (heated)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 120, "high": 300, "cost": 25, "yr_min": 1998},
            {"name": "Mark Levinson Amp", "rarity": "Rare", "low": 100, "high": 250, "cost": 20, "yr_min": 2006},
        ],
    },
    # --- ACURA (previously zero coverage) ---
    "integra": {
        "display": "Acura Integra",
        "make": "Acura",
        "year_range": (1990, 2001),
        "top_parts": [
            {"name": "B18 Engine Accessories / Intake Manifold", "rarity": "Legendary", "low": 150, "high": 400, "cost": 25},
            {"name": "OEM Seats (pair, unshredded)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            {"name": "Rear Disc Brake Conversion Parts (trailing arms)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
            {"name": "Door Panels / Interior Trim (clean)", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
            {"name": "OEM Lip / Spoiler", "rarity": "Epic", "low": 100, "high": 300, "cost": 15},
            {"name": "Gauge Cluster", "rarity": "Rare", "low": 60, "high": 150, "cost": 10},
        ],
    },
    "rsx": {
        "display": "Acura RSX",
        "make": "Acura",
        "year_range": (2002, 2006),
        "top_parts": [
            {"name": "K20 Intake Manifold / Throttle Body", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Type-S Recaro-style Seats (pair)", "rarity": "Epic", "low": 250, "high": 600, "cost": 45, "trim": ["Type-S", "Type S"]},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 40},
            {"name": "Shift Assembly (manual)", "rarity": "Rare", "low": 80, "high": 200, "cost": 10},
            {"name": "OEM Lip Kit Pieces", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
        ],
    },
    "acura tsx": {
        "display": "Acura TSX",
        "make": "Acura",
        "year_range": (2004, 2014),
        "top_parts": [
            {"name": "K24A2 Intake Manifold / Accessories (swap favorite)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 2008},
            {"name": "6MT Shifter Assembly + Pedals", "rarity": "Epic", "low": 100, "high": 250, "cost": 15},
            {"name": "Front Seats (leather, heated)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
        ],
    },
    "acura tl": {
        "display": "Acura TL",
        "make": "Acura",
        "year_range": (1999, 2014),
        "top_parts": [
            {"name": "Brembo Front Calipers (Type-S)", "rarity": "Legendary", "low": 250, "high": 600, "cost": 40, "trim": ["Type-S", "Type S"]},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 350, "cost": 25, "yr_min": 2004},
            {"name": "ELS Audio Amp + Sub", "rarity": "Rare", "low": 100, "high": 250, "cost": 20, "yr_min": 2004},
            {"name": "Front Seats (leather, heated)", "rarity": "Rare", "low": 100, "high": 275, "cost": 40},
        ],
    },
    "legend": {
        "display": "Acura Legend",
        "make": "Acura",
        "year_range": (1986, 1995),
        "top_parts": [
            {"name": "6MT/5MT Manual Swap Parts (pedals, shifter)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 15},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
            {"name": "Chrome Trim / Grille", "rarity": "Rare", "low": 60, "high": 175, "cost": 10},
        ],
    },
    # --- INFINITI (previously zero coverage) ---
    "g35": {
        "display": "Infiniti G35",
        "make": "Infiniti",
        "year_range": (2003, 2008),
        "top_parts": [
            {"name": "VQ35DE Intake/Plenum/Accessories (350Z twin)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Brembo Calipers (set, sport pkg)", "rarity": "Legendary", "low": 300, "high": 700, "cost": 55, "option": True},
            {"name": "6MT Shifter + Pedal Assembly", "rarity": "Epic", "low": 100, "high": 250, "cost": 15},
            {"name": "Coupe Seats (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
            {"name": "Viscous LSD Rear Diff", "rarity": "Epic", "low": 150, "high": 400, "cost": 50, "option": True},
        ],
    },
    "g37": {
        "display": "Infiniti G37",
        "make": "Infiniti",
        "year_range": (2008, 2015),
        "top_parts": [
            {"name": "Sport Pkg Brembo/Akebono Calipers (set)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "option": True},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 400, "cost": 25},
            {"name": "Coupe Seats (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "Bose Amp + Speakers", "rarity": "Rare", "low": 80, "high": 200, "cost": 20},
        ],
    },
    "g sedan": {
        "display": "Infiniti G Sedan (G25/G37)",
        "make": "Infiniti",
        "year_range": (2009, 2013),
        "top_parts": [
            {"name": "Sport Pkg Akebono Calipers (set)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 400, "cost": 25},
            {"name": "Front Seats (leather, heated)", "rarity": "Rare", "low": 100, "high": 275, "cost": 40},
        ],
    },
    "g coupe": {
        "display": "Infiniti G Coupe (G37)",
        "make": "Infiniti",
        "year_range": (2009, 2015),
        "top_parts": [
            {"name": "Sport Pkg Akebono Calipers (set)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55},
            {"name": "Coupe Seats (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 400, "cost": 25},
        ],
    },
    "qx4": {
        "display": "Infiniti QX4 (Pathfinder twin)",
        "make": "Infiniti",
        "year_range": (1997, 2003),
        "top_parts": [
            {"name": "Rear LSD Differential", "rarity": "Epic", "low": 150, "high": 350, "cost": 50, "option": True},
            {"name": "Front Seats (leather, heated)", "rarity": "Rare", "low": 100, "high": 250, "cost": 40},
            {"name": "OEM Roof Rack", "rarity": "Rare", "low": 60, "high": 150, "cost": 15},
        ],
    },
    # --- NISSAN JDM ---
    "240sx": {
        "display": "Nissan 240SX (S13/S14)",
        "make": "Nissan",
        "year_range": (1989, 1998),
        "top_parts": [
            {"name": "Anything — drift tax on every part", "rarity": "Legendary", "low": 300, "high": 1000, "cost": 60},
            {"name": "Steering Knuckles (pair)", "rarity": "Legendary", "low": 150, "high": 400, "cost": 20},
            {"name": "Rear Subframe + Diff", "rarity": "Epic", "low": 200, "high": 500, "cost": 60},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 150, "high": 450, "cost": 40},
            {"name": "Manual Pedal Box / Shifter", "rarity": "Epic", "low": 100, "high": 300, "cost": 10},
        ],
    },
    "300zx": {
        "display": "Nissan 300ZX (Z31/Z32)",
        "make": "Nissan",
        "year_range": (1984, 1996),
        "top_parts": [
            {"name": "T-Top Panels (pair)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 40},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 150, "high": 400, "cost": 40},
            {"name": "VG30 Accessories / Harness", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Digital Dash / Cluster", "rarity": "Epic", "low": 100, "high": 300, "cost": 10},
        ],
    },
    "nissan pickup": {
        "display": "Nissan Pickup / Hardbody (720/D21)",
        "make": "Nissan",
        "year_range": (1980, 1997),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
            {"name": "KA24E Intake/EFI Parts", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
            {"name": "Front Grille + Headlight Bezels", "rarity": "Rare", "low": 60, "high": 150, "cost": 10},
            {"name": "Bench Seat", "rarity": "Rare", "low": 60, "high": 200, "cost": 25},
            {"name": "4x4 Transfer Case Shifter / Hubs", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
        ],
    },
    "sentra se-r": {
        "display": "Nissan Sentra SE-R",
        "make": "Nissan",
        "year_range": (1991, 2006),
        "top_parts": [
            {"name": "SR20DE Intake / Accessories", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 1994},
            {"name": "SE-R Seats (pair)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
        ],
    },
    # --- MITSUBISHI (previously zero coverage) ---
    "eclipse": {
        "display": "Mitsubishi Eclipse (DSM + 3G)",
        "make": "Mitsubishi",
        "year_range": (1990, 2012),
        "top_parts": [
            {"name": "4G63T Turbo Drivetrain Parts (1G/2G DSM)", "rarity": "Legendary", "low": 200, "high": 600, "cost": 40, "yr_max": 1999},
            {"name": "AWD Rear Diff + Driveshaft (GSX)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 60, "yr_max": 1999, "drive": ["awd"]},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
            {"name": "Sunroof / Spoiler", "rarity": "Rare", "low": 60, "high": 175, "cost": 15, "option": True},
        ],
    },
    "lancer evolution": {
        "display": "Mitsubishi Lancer Evolution",
        "make": "Mitsubishi",
        "year_range": (2003, 2015),
        "top_parts": [
            {"name": "Anything — Evo parts are gold (Brembos, Recaros, diffs, turbo)", "rarity": "Legendary", "low": 400, "high": 1500, "cost": 80},
        ],
    },
    "lancer": {
        "display": "Mitsubishi Lancer",
        "make": "Mitsubishi",
        "year_range": (2002, 2017),
        "top_parts": [
            {"name": "Ralliart Turbo / TC-SST Parts", "rarity": "Epic", "low": 200, "high": 500, "cost": 40, "trim": ["Ralliart"]},
            {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Ralliart", "Evolution", "GTS"], "option": True},
            {"name": "OEM Spoiler", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 15},
        ],
    },
    "montero": {
        "display": "Mitsubishi Montero / Montero Sport",
        "make": "Mitsubishi",
        "year_range": (1989, 2006),
        "top_parts": [
            # Factory rear locker was an option on Gen2/2.5 Montero.
            {"name": "Rear Diff Locker Components (Gen2/2.5)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 30, "yr_max": 2000, "option": True},
            {"name": "Super Select Transfer Case Shifter/Motor", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "OEM Roof Rack", "rarity": "Rare", "low": 80, "high": 200, "cost": 20},
            {"name": "Inclinometer Gauge Pod", "rarity": "Epic", "low": 80, "high": 200, "cost": 8},
        ],
    },
    "3000gt": {
        "display": "Mitsubishi 3000GT / Dodge Stealth",
        "make": "Mitsubishi",
        "year_range": (1991, 1999),
        "top_parts": [
            {"name": "Pop-Up Headlights (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_max": 1993},
            {"name": "VR-4 Twin Turbo / AWD Parts", "rarity": "Legendary", "low": 300, "high": 800, "cost": 60, "trim": ["VR-4", "VR4", "R/T Turbo"]},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 120, "high": 350, "cost": 40},
            {"name": "Active Aero Spoiler", "rarity": "Epic", "low": 100, "high": 300, "cost": 15},
        ],
    },
    "stealth": {
        "display": "Dodge Stealth (3000GT twin)",
        "make": "Dodge",
        "year_range": (1991, 1996),
        "top_parts": [
            {"name": "R/T Turbo AWD Parts", "rarity": "Legendary", "low": 300, "high": 800, "cost": 60, "trim": ["R/T"]},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 120, "high": 350, "cost": 40},
        ],
    },
    # --- MAZDA ROTARY + HONDA JDM ---
    "rx-7": {
        "display": "Mazda RX-7",
        "make": "Mazda",
        "year_range": (1979, 1995),
        "top_parts": [
            {"name": "Anything — rotary community buys it all", "rarity": "Legendary", "low": 300, "high": 1000, "cost": 60},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            {"name": "Gauge Cluster", "rarity": "Epic", "low": 100, "high": 300, "cost": 10},
        ],
    },
    "rx-8": {
        "display": "Mazda RX-8",
        "make": "Mazda",
        "year_range": (2004, 2011),
        "top_parts": [
            {"name": "Rear Diff (Torsen LSD — Miata swap favorite)", "rarity": "Epic", "low": 200, "high": 450, "cost": 50, "manual": True},
            {"name": "Front Seats (pair, leather/Recaro)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 120, "high": 300, "cost": 25},
            {"name": "Ignition Coils (set, low-mile)", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 10},
        ],
    },
    "prelude": {
        "display": "Honda Prelude",
        "make": "Honda",
        "year_range": (1988, 2001),
        "top_parts": [
            {"name": "H22 Intake / Accessories", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_min": 1992},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 150, "high": 400, "cost": 40},
            {"name": "5MT Shifter / Pedal Assembly", "rarity": "Rare", "low": 80, "high": 200, "cost": 10},
            # NOT option-flagged: power moonroof was standard on nearly every US Prelude.
            {"name": "Sunroof Assembly", "rarity": "Rare", "low": 60, "high": 175, "cost": 20},
        ],
    },
    "crx": {
        "display": "Honda CRX",
        "make": "Honda",
        "year_range": (1984, 1991),
        "top_parts": [
            {"name": "Anything — CRX parts all sell", "rarity": "Legendary", "low": 200, "high": 700, "cost": 40},
            {"name": "Si Seats / Sunroof / Glass Hatch", "rarity": "Legendary", "low": 200, "high": 600, "cost": 40},
        ],
    },
    "del sol": {
        "display": "Honda Del Sol",
        "make": "Honda",
        "year_range": (1993, 1997),
        "top_parts": [
            {"name": "Targa Top (unleaky)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 30},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            {"name": "Trunk/Engine Lids (straight)", "rarity": "Rare", "low": 80, "high": 250, "cost": 20},
        ],
    },
    "s2000": {
        "display": "Honda S2000",
        "make": "Honda",
        "year_range": (2000, 2009),
        "top_parts": [
            {"name": "Anything — S2000 parts are gold", "rarity": "Legendary", "low": 500, "high": 2000, "cost": 100},
        ],
    },
    # =====================================================================
    # DOMESTIC CULT — OBS trucks, GMC badge twins, panther platform, LS-swap
    # donors, and the classics that occasionally roll into a self-serve yard.
    # =====================================================================
    "c/k": {
        "display": "Chevy C/K OBS Truck",
        "make": "Chevrolet",
        "year_range": (1973, 2000),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
            {"name": "Front Grille + Bezels (chrome)", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
            {"name": "Bench Seat (60/40, uncracked)", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
            {"name": "Tow Mirrors (pair)", "rarity": "Rare", "low": 60, "high": 150, "cost": 15, "option": True},
            {"name": "Interior Trim / Dash Pieces (clean)", "rarity": "Rare", "low": 50, "high": 175, "cost": 10},
        ],
    },
    "k1500": {
        "display": "Chevy K1500 OBS",
        "make": "Chevrolet",
        "year_range": (1988, 1999),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
            {"name": "Bench Seat (60/40)", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
            {"name": "Front Grille + Bezels", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
        ],
    },
    "c1500": {
        "display": "Chevy C1500 OBS",
        "make": "Chevrolet",
        "year_range": (1988, 1999),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
            {"name": "Bench Seat (60/40)", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
        ],
    },
    "s10": {
        "display": "Chevy S10 / GMC Sonoma",
        "make": "Chevrolet",
        "year_range": (1982, 2004),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Rare", "low": 80, "high": 200, "cost": 25},
            {"name": "Extended Cab Jump Seats", "rarity": "Rare", "low": 50, "high": 150, "cost": 15},
            {"name": "ZR2 Suspension/Body Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 30, "trim": ["ZR2"]},
            {"name": "Front Clip Pieces (V8-swap crowd)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 20},
        ],
    },
    "sonoma": {
        "display": "GMC Sonoma (S10 twin)",
        "make": "GMC",
        "year_range": (1991, 2004),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Rare", "low": 80, "high": 200, "cost": 25},
            {"name": "Highrider/ZR2 Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
        ],
    },
    "blazer": {
        "display": "Chevy Blazer (K5 + S10)",
        "make": "Chevrolet",
        "year_range": (1973, 2005),
        "top_parts": [
            {"name": "K5 Removable Hardtop Parts", "rarity": "Legendary", "low": 200, "high": 600, "cost": 40, "yr_max": 1991},
            {"name": "K5 Tailgate w/ Power Window", "rarity": "Legendary", "low": 200, "high": 500, "cost": 30, "yr_max": 1991},
            {"name": "Rear Cargo/Jump Seat", "rarity": "Rare", "low": 80, "high": 250, "cost": 20},
            {"name": "Front Grille + Bezels", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
        ],
    },
    "astro": {
        "display": "Chevy Astro / GMC Safari",
        "make": "Chevrolet",
        "year_range": (1985, 2005),
        "top_parts": [
            {"name": "AWD Transfer Case (van-life gold)", "rarity": "Epic", "low": 150, "high": 400, "cost": 50},
            {"name": "Dutch Door Glass + Hardware", "rarity": "Rare", "low": 80, "high": 250, "cost": 20},
            {"name": "Rear Bench Seats", "rarity": "Rare", "low": 60, "high": 200, "cost": 25},
            {"name": "Roof Rack", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 15},
        ],
    },
    "safari": {
        "display": "GMC Safari (Astro twin)",
        "make": "GMC",
        "year_range": (1985, 2005),
        "top_parts": [
            {"name": "AWD Transfer Case", "rarity": "Epic", "low": 150, "high": 400, "cost": 50},
            {"name": "Dutch Door Glass + Hardware", "rarity": "Rare", "low": 80, "high": 250, "cost": 20},
        ],
    },
    "corvette": {
        "display": "Chevy Corvette",
        "make": "Chevrolet",
        "year_range": (1968, 2013),
        "top_parts": [
            {"name": "Targa Top / T-Tops", "rarity": "Legendary", "low": 300, "high": 900, "cost": 50},
            {"name": "Seats (pair)", "rarity": "Epic", "low": 250, "high": 700, "cost": 45},
            {"name": "OEM Wheels (set)", "rarity": "Epic", "low": 300, "high": 800, "cost": 80},
            {"name": "Gauge Cluster / Interior Electronics", "rarity": "Epic", "low": 150, "high": 400, "cost": 15},
        ],
    },
    "el camino": {
        "display": "Chevy El Camino",
        "make": "Chevrolet",
        "year_range": (1964, 1987),
        "top_parts": [
            {"name": "Anything — classic parts all sell", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        ],
    },
    # --- GMC BADGE TWINS (Sierra/Yukon had ZERO coverage despite Chevy twins) ---
    "sierra": {
        "display": "GMC Sierra (Silverado twin)",
        "make": "GMC",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 50, "yr_min": 2016},
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 600, "cost": 30, "yr_min": 2014, "option": True},
            {"name": "Tailgate (w/ camera)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40, "yr_min": 2014},
            {"name": "Denali Grille / Trim", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "trim": ["Denali"]},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 20},
        ],
    },
    "yukon": {
        "display": "GMC Yukon (Tahoe twin)",
        "make": "GMC",
        "year_range": (1995, 2024),
        "top_parts": [
            {"name": "3rd Row Seat (complete)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 80, "high": 225, "cost": 15, "yr_min": 2007},
            {"name": "Denali Grille / 6.2 Accessories", "rarity": "Rare", "low": 100, "high": 300, "cost": 25, "trim": ["Denali"]},
            {"name": "Autoride Rear Air Shocks", "rarity": "Rare", "low": 100, "high": 250, "cost": 20, "yr_min": 2000},
        ],
    },
    "jimmy": {
        "display": "GMC Jimmy (Blazer twin)",
        "make": "GMC",
        "year_range": (1973, 2001),
        "top_parts": [
            {"name": "Full-Size Hardtop/Tailgate Parts", "rarity": "Epic", "low": 150, "high": 450, "cost": 30, "yr_max": 1991},
            {"name": "Front Grille + Bezels", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
        ],
    },
    # --- FORD TRUCK/CULT ---
    "bronco": {
        "display": "Ford Bronco (full-size)",
        "make": "Ford",
        "year_range": (1966, 1996),
        "top_parts": [
            {"name": "Rear Hardtop Section", "rarity": "Legendary", "low": 300, "high": 900, "cost": 50},
            {"name": "Tailgate (straight, glass works)", "rarity": "Legendary", "low": 250, "high": 600, "cost": 30},
            {"name": "Rear Fold Seat", "rarity": "Epic", "low": 150, "high": 400, "cost": 25},
            {"name": "Front Grille + Bezels", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
        ],
    },
    "bronco ii": {
        "display": "Ford Bronco II",
        "make": "Ford",
        "year_range": (1984, 1990),
        "top_parts": [
            {"name": "Rear Seat / Cargo Trim", "rarity": "Rare", "low": 60, "high": 175, "cost": 20},
            {"name": "Front Grille + Bezels", "rarity": "Rare", "low": 50, "high": 150, "cost": 15},
        ],
    },
    "f-250": {
        "display": "Ford F-250 / Super Duty",
        "make": "Ford",
        "year_range": (1980, 2024),
        "top_parts": [
            {"name": "7.3L Powerstroke Parts (turbo, HPOP — verify engine)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 50, "yr_min": 1994, "yr_max": 2003},
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 420, "cost": 30, "yr_min": 2008, "option": True},  # new Super Duty pairs $415-515 (AmericanTrucks/BoostAuto) — 80% ceiling (2026-09)
            {"name": "Tailgate (w/ step)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40, "yr_min": 2008},
            {"name": "Crew Cab Rear Bench", "rarity": "Uncommon", "low": 80, "high": 225, "cost": 25},
        ],
    },
    "f-350": {
        "display": "Ford F-350 / Super Duty",
        "make": "Ford",
        "year_range": (1980, 2024),
        "top_parts": [
            {"name": "7.3L Powerstroke Parts (turbo, HPOP — verify engine)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 50, "yr_min": 1994, "yr_max": 2003},
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 420, "cost": 30, "yr_min": 2008, "option": True},  # new Super Duty pairs $415-515 (AmericanTrucks/BoostAuto) — 80% ceiling (2026-09)
            {"name": "Dually Fenders / Bed Parts", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
        ],
    },
    "excursion": {
        "display": "Ford Excursion",
        "make": "Ford",
        "year_range": (2000, 2005),
        "top_parts": [
            {"name": "7.3L Powerstroke Parts (verify engine)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 50, "yr_max": 2003},
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            {"name": "Rear Barn Doors / Glass", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
        ],
    },
    # --- PANTHER PLATFORM ---
    "crown victoria": {
        "display": "Ford Crown Victoria",
        "make": "Ford",
        "year_range": (1992, 2011),
        "top_parts": [
            {"name": "P71 Police Parts (spotlight, steelies, calipers)", "rarity": "Epic", "low": 100, "high": 300, "cost": 25},
            {"name": "Front Seats (cloth, unworn)", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 40},
            {"name": "Rear Air Springs / Watts Link Parts", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 15},
        ],
    },
    "grand marquis": {
        "display": "Mercury Grand Marquis (Panther)",
        "make": "Mercury",
        "year_range": (1992, 2011),
        "top_parts": [
            {"name": "Panther Interchange Parts (calipers, suspension)", "rarity": "Uncommon", "low": 50, "high": 175, "cost": 20},
            {"name": "Front Seats (leather)", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 40},
        ],
    },
    "town car": {
        "display": "Lincoln Town Car (Panther)",
        "make": "Lincoln",
        "year_range": (1990, 2011),
        "top_parts": [
            {"name": "Rear Air Springs + Compressor", "rarity": "Rare", "low": 80, "high": 225, "cost": 20},
            {"name": "Front Seats (leather, heated)", "rarity": "Uncommon", "low": 60, "high": 200, "cost": 40},
        ],
    },
    # --- MOPAR / GM PERFORMANCE ---
    "ram 2500": {
        "display": "Ram 2500 (Cummins candidates)",
        "make": "Dodge",
        "year_range": (1994, 2024),
        "top_parts": [
            {"name": "Cummins Parts (injectors, turbo — verify engine)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 50},
            {"name": "Tow Mirrors (pair)", "rarity": "Rare", "low": 150, "high": 280, "cost": 30, "yr_min": 2010, "option": True},  # new quality manual-fold tow pairs ~$280-350 — 80% ceiling (2026-09)
            {"name": "Tailgate (straight)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
        ],
    },
    "ram 3500": {
        "display": "Ram 3500 (Cummins candidates)",
        "make": "Dodge",
        "year_range": (1994, 2024),
        "top_parts": [
            {"name": "Cummins Parts (injectors, turbo — verify engine)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 50},
            {"name": "Dually Fenders / Bed Parts", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
        ],
    },
    "magnum": {
        "display": "Dodge Magnum",
        "make": "Dodge",
        "year_range": (2005, 2008),
        "top_parts": [
            {"name": "Rear Hatch + Spoiler", "rarity": "Rare", "low": 120, "high": 300, "cost": 30},
            {"name": "SRT8 Seats / Brakes", "rarity": "Epic", "low": 250, "high": 600, "cost": 50, "trim": ["SRT"]},
            {"name": "HEMI Accessories (5.7)", "rarity": "Rare", "low": 80, "high": 225, "cost": 20, "trim": ["R/T", "SRT"]},
        ],
    },
    "neon": {
        "display": "Dodge Neon (SRT-4 hunt)",
        "make": "Dodge",
        "year_range": (1995, 2005),
        "top_parts": [
            {"name": "SRT-4 Turbo Drivetrain (gold if present)", "rarity": "Legendary", "low": 300, "high": 800, "cost": 60, "trim": ["SRT"]},
            {"name": "SRT-4 Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 45, "trim": ["SRT"]},
        ],
    },
    "firebird": {
        "display": "Pontiac Firebird / Trans Am",
        "make": "Pontiac",
        "year_range": (1982, 2002),
        "top_parts": [
            {"name": "T-Top Panels (pair)", "rarity": "Legendary", "low": 250, "high": 700, "cost": 40},
            {"name": "OEM Seats (pair)", "rarity": "Epic", "low": 150, "high": 400, "cost": 40},
            {"name": "WS6 Hood / Spoiler", "rarity": "Epic", "low": 150, "high": 450, "cost": 30, "trim": ["WS6", "Trans Am"], "option": True, "verify": "Twin-nostril Ram Air hood = WS6 package"},
            {"name": "LS1 Accessories (98-02)", "rarity": "Epic", "low": 100, "high": 300, "cost": 25, "yr_min": 1998},
        ],
    },
    "pontiac gto": {
        "display": "Pontiac GTO (LS gold)",
        "make": "Pontiac",
        "year_range": (2004, 2006),
        "top_parts": [
            {"name": "LS1/LS2 Accessories + Interior — everything sells", "rarity": "Legendary", "low": 300, "high": 900, "cost": 60},
        ],
    },
    "g8": {
        "display": "Pontiac G8 (LS gold)",
        "make": "Pontiac",
        "year_range": (2008, 2009),
        "top_parts": [
            {"name": "Anything — G8 parts are unobtanium", "rarity": "Legendary", "low": 300, "high": 1000, "cost": 60},
        ],
    },
    "fiero": {
        "display": "Pontiac Fiero",
        "make": "Pontiac",
        "year_range": (1984, 1988),
        "top_parts": [
            {"name": "Anything — cult classic, all parts sell", "rarity": "Epic", "low": 100, "high": 400, "cost": 30},
        ],
    },
    "vibe": {
        "display": "Pontiac Vibe (Matrix twin)",
        "make": "Pontiac",
        "year_range": (2003, 2010),
        "top_parts": [
            {"name": "Rear Cargo Rail System", "rarity": "Rare", "low": 60, "high": 150, "cost": 10},
            {"name": "GT (2ZZ) Engine Accessories", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "trim": ["GT"]},
            {"name": "Headlights (clear)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
        ],
    },
    # =====================================================================
    # 4x4 / IMPORT CULT + EURO + MISC
    # =====================================================================
    "samurai": {
        "display": "Suzuki Samurai",
        "make": "Suzuki",
        "year_range": (1986, 1995),
        "top_parts": [
            {"name": "Transfer Case (crawler gold)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 50},
            {"name": "Axles (front/rear)", "rarity": "Epic", "low": 150, "high": 400, "cost": 60},
            # Samurai sold both soft-top and tin-top — hardtop presence is a coin flip and not
            # decodable (same for Sidekick/Tracker below).
            {"name": "Hardtop / Doors", "rarity": "Epic", "low": 150, "high": 450, "cost": 30, "option": True},
        ],
    },
    "sidekick": {
        "display": "Suzuki Sidekick / Geo Tracker",
        "make": "Suzuki",
        "year_range": (1989, 1998),
        "top_parts": [
            {"name": "Transfer Case + 4x4 Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 40},
            {"name": "Hardtop / Soft Top Frame", "rarity": "Rare", "low": 80, "high": 250, "cost": 25, "option": True},
        ],
    },
    "tracker": {
        "display": "Geo/Chevy Tracker (Sidekick twin)",
        "make": "Geo",
        "year_range": (1989, 2004),
        "top_parts": [
            {"name": "Transfer Case + 4x4 Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 40},
            {"name": "Hardtop / Soft Top Frame", "rarity": "Rare", "low": 80, "high": 250, "cost": 25, "option": True},
        ],
    },
    "trooper": {
        "display": "Isuzu Trooper",
        "make": "Isuzu",
        "year_range": (1984, 2002),
        "top_parts": [
            {"name": "Rear Diff (often LSD) + 4x4 Parts", "rarity": "Epic", "low": 120, "high": 350, "cost": 50},
            {"name": "Rear Barn Doors / Glass", "rarity": "Rare", "low": 80, "high": 225, "cost": 20},
            {"name": "OEM Roof Rack", "rarity": "Rare", "low": 60, "high": 150, "cost": 15},
        ],
    },
    "rodeo": {
        "display": "Isuzu Rodeo",
        "make": "Isuzu",
        "year_range": (1991, 2004),
        "top_parts": [
            {"name": "4x4 Transfer Case / Diff Parts", "rarity": "Rare", "low": 80, "high": 250, "cost": 40, "drive": ["4wd"]},
            {"name": "Rear Gate + Glass", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 20},
        ],
    },
    "passport": {
        "display": "Honda Passport (Rodeo twin)",
        "make": "Honda",
        "year_range": (1994, 2002),
        "top_parts": [
            {"name": "4x4 Transfer Case / Diff Parts", "rarity": "Rare", "low": 80, "high": 250, "cost": 40, "drive": ["4wd"]},
        ],
    },
    "baja": {
        "display": "Subaru Baja",
        "make": "Subaru",
        "year_range": (2003, 2006),
        "top_parts": [
            {"name": "Bed Extender + Switchback Parts", "rarity": "Legendary", "low": 150, "high": 400, "cost": 20},
            {"name": "Hard Tonneau / Bed Caps", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "Turbo Parts (04-06 Baja Turbo)", "rarity": "Epic", "low": 150, "high": 400, "cost": 30, "yr_min": 2004},
        ],
    },
    "svx": {
        "display": "Subaru SVX",
        "make": "Subaru",
        "year_range": (1992, 1997),
        "top_parts": [
            {"name": "Window-in-Window Glass + Trim", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
            {"name": "EG33 Accessories", "rarity": "Rare", "low": 80, "high": 250, "cost": 20},
        ],
    },
    "cj5": {
        "display": "Jeep CJ",
        "make": "Jeep",
        "year_range": (1955, 1986),
        "top_parts": [
            {"name": "Anything — CJ parts all sell", "rarity": "Legendary", "low": 150, "high": 600, "cost": 40},
        ],
    },
    "cj7": {
        "display": "Jeep CJ7",
        "make": "Jeep",
        "year_range": (1976, 1986),
        "top_parts": [
            {"name": "Anything — CJ parts all sell", "rarity": "Legendary", "low": 150, "high": 600, "cost": 40},
        ],
    },
    "wagoneer": {
        "display": "Jeep Wagoneer (classic)",
        "make": "Jeep",
        "year_range": (1963, 1993),
        "top_parts": [
            {"name": "Anything — full-size Jeep parts are gold", "rarity": "Legendary", "low": 150, "high": 600, "cost": 40},
        ],
    },
    "comanche": {
        "display": "Jeep Comanche (MJ)",
        "make": "Jeep",
        "year_range": (1986, 1992),
        "top_parts": [
            {"name": "Bed / Tailgate (straight)", "rarity": "Legendary", "low": 200, "high": 600, "cost": 40},
            {"name": "Anything MJ-specific", "rarity": "Epic", "low": 100, "high": 400, "cost": 25},
        ],
    },
    "volvo 24": {
        "display": "Volvo 240/245 (brick)",
        "make": "Volvo",
        "year_range": (1975, 1993),
        "top_parts": [
            {"name": "Interior Trim / Seats (clean)", "rarity": "Rare", "low": 80, "high": 250, "cost": 30},
            {"name": "Chrome Bumpers / Trim", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
            {"name": "Gauge Cluster / Switches", "rarity": "Rare", "low": 50, "high": 150, "cost": 10},
        ],
    },
    "benz 300": {
        "display": "Mercedes W123/W124 300",
        "make": "Mercedes-Benz",
        "year_range": (1976, 1995),
        "top_parts": [
            {"name": "OM61x Diesel Injection Pump / Turbo (verify engine)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 40},
            {"name": "MB-Tex Seats (uncracked)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
            {"name": "Euro Headlights / Chrome Trim", "rarity": "Rare", "low": 80, "high": 250, "cost": 15},
        ],
    },
    "beetle": {
        "display": "VW Beetle (air-cooled)",
        "make": "Volkswagen",
        "year_range": (1938, 1979),
        "top_parts": [
            {"name": "Anything — air-cooled parts all sell", "rarity": "Legendary", "low": 150, "high": 600, "cost": 30},
        ],
    },
    "vanagon": {
        "display": "VW Vanagon",
        "make": "Volkswagen",
        "year_range": (1980, 1991),
        "top_parts": [
            {"name": "Anything — Westy/vanlife community buys it all", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        ],
    },
    "eurovan": {
        "display": "VW Eurovan",
        "make": "Volkswagen",
        "year_range": (1992, 2003),
        "top_parts": [
            {"name": "Interior Seats / Bed Hardware", "rarity": "Epic", "low": 150, "high": 450, "cost": 40},
            {"name": "Sliding Door + Hardware", "rarity": "Rare", "low": 100, "high": 300, "cost": 25},
        ],
    },
    "mini cooper": {
        "display": "Mini Cooper (R50/R53)",
        "make": "Mini",
        "year_range": (2002, 2013),
        "top_parts": [
            {"name": "Supercharger (R53 Cooper S — verify)", "rarity": "Legendary", "low": 250, "high": 600, "cost": 40, "yr_max": 2006},
            {"name": "Xenon Headlights", "rarity": "Rare", "low": 120, "high": 300, "cost": 25},
            {"name": "Panoramic Sunroof Parts", "rarity": "Rare", "low": 80, "high": 225, "cost": 20, "option": True},
        ],
    },
    "discovery": {
        "display": "Land Rover Discovery",
        "make": "Land Rover",
        "year_range": (1994, 2004),
        "top_parts": [
            {"name": "Rear Diff / CDL Transfer Case Parts", "rarity": "Epic", "low": 120, "high": 350, "cost": 50},
            {"name": "Safari/Roof Rack + Ladder", "rarity": "Epic", "low": 150, "high": 400, "cost": 25},
            {"name": "Jump Seats (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
        ],
    },
    "lr3": {
        "display": "Land Rover LR3",
        "make": "Land Rover",
        "year_range": (2005, 2009),
        "top_parts": [
            # NOT option-flagged: air suspension std on nearly all LR3s (coil base V6 rare).
            {"name": "Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 20},
            # Optional rear e-diff — '(if equipped)' name suffix normalized to the flag.
            {"name": "Rear Locking Diff", "rarity": "Epic", "low": 150, "high": 400, "cost": 50, "option": True},
        ],
    },
    "range rover": {
        "display": "Range Rover",
        "make": "Land Rover",
        "year_range": (1995, 2020),
        "top_parts": [
            # NOT option-flagged: air suspension is standard on Range Rover.
            {"name": "Air Suspension Compressor + Struts", "rarity": "Rare", "low": 120, "high": 350, "cost": 25},
            {"name": "OEM Wheels (set)", "rarity": "Rare", "low": 200, "high": 500, "cost": 80},
            {"name": "Front Seats (leather, heated/cooled)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
        ],
    },
    "datsun": {
        "display": "Datsun (anything)",
        "make": "Datsun",
        "year_range": (1960, 1986),
        "top_parts": [
            {"name": "Anything — Datsun parts all sell", "rarity": "Legendary", "low": 150, "high": 700, "cost": 30},
        ],
    },
    "scion tc": {
        "display": "Scion tC",
        "make": "Scion",
        "year_range": (2005, 2016),
        "top_parts": [
            {"name": "OEM Alloy Wheels (set)", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 40},
            {"name": "Pioneer Premium Head Unit", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 12},
            {"name": "Rear Spoiler", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 15, "option": True},
            {"name": "Panoramic Roof Glass", "rarity": "Rare", "low": 100, "high": 250, "cost": 25},
            {"name": "TRD Parts (springs, exhaust bits)", "rarity": "Rare", "low": 80, "high": 225, "cost": 20},
        ],
    },
    "scion xb": {
        "display": "Scion xB (gen1 cult)",
        "make": "Scion",
        "year_range": (2004, 2015),
        "top_parts": [
            # Gen1 center-dash cluster is the classic xB failure/theft piece.
            {"name": "Center Dash Gauge Cluster", "rarity": "Rare", "low": 60, "high": 160, "cost": 12, "yr_max": 2006},
            {"name": "OEM Roof Spoiler", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15, "option": True},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 50, "high": 120, "cost": 15, "yr_min": 2008},
            {"name": "Gen1 Bumpers / Body Panels (straight)", "rarity": "Rare", "low": 80, "high": 250, "cost": 25, "yr_max": 2006},
            {"name": "Gen1 Interior Trim / Cluster", "rarity": "Rare", "low": 60, "high": 175, "cost": 10, "yr_max": 2006},
        ],
    },
    "genesis coupe": {
        "display": "Hyundai Genesis Coupe",
        "make": "Hyundai",
        # Longer keyword listed first so its hit contains "hyundai genesis" and
        # the sedan entry is substring-dropped on coupe listings.
        "match": ["hyundai genesis coupe", "genesis coupe"],
        "year_range": (2010, 2016),
        "top_parts": [
            {"name": "Brembo Calipers (set, Track/R-Spec)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "trim": ["Track", "R-Spec", "Ultimate"]},
            {"name": "Turbo + 2.0T Parts", "rarity": "Epic", "low": 150, "high": 400, "cost": 30},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            # LSD std only on Track/R-Spec/Ultimate but listings rarely say — '(if equipped)'
            # name suffix normalized to the option flag.
            {"name": "Rear LSD Diff", "rarity": "Epic", "low": 150, "high": 400, "cost": 50, "option": True},
        ],
    },
    "tiburon": {
        "display": "Hyundai Tiburon",
        "make": "Hyundai",
        "year_range": (1997, 2008),
        "top_parts": [
            {"name": "Rear Spoiler", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15},
            {"name": "Infinity Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 15, "option": True},
            {"name": "GT V6 6MT Parts (shifter, pedals)", "rarity": "Rare", "low": 80, "high": 225, "cost": 15, "trim": ["GT"]},
            {"name": "OEM Seats (pair)", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 40},
        ],
    },
    "veloster": {
        "display": "Hyundai Veloster",
        "make": "Hyundai",
        "year_range": (2012, 2022),
        "top_parts": [
            {"name": "Panoramic Sunroof Assembly", "rarity": "Rare", "low": 120, "high": 300, "cost": 30, "option": True},
            {"name": "Turbo Front Bumper + Grille", "rarity": "Rare", "low": 100, "high": 250, "cost": 25, "trim": ["Turbo"]},
            {"name": "Dimension Premium Amp", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 12, "option": True},
            {"name": "Turbo Parts (1.6T)", "rarity": "Rare", "low": 120, "high": 300, "cost": 30, "trim": ["Turbo", "N"]},
            {"name": "3rd Door / Hatch Glass", "rarity": "Rare", "low": 80, "high": 225, "cost": 25},
        ],
    },
    "geo metro": {
        "display": "Geo Metro (mileage cult)",
        "make": "Geo",
        "year_range": (1989, 2001),
        "top_parts": [
            {"name": "1.0L 3-Cylinder Engine Parts", "rarity": "Rare", "low": 60, "high": 200, "cost": 15},
            {"name": "XFi-Specific Parts", "rarity": "Epic", "low": 80, "high": 250, "cost": 15, "trim": ["XFi"]},
        ],
    },
    "cayenne": {
        "display": "Porsche Cayenne",
        "make": "Porsche",
        "year_range": (2003, 2018),
        "top_parts": [
            {"name": "OEM Wheels (set)", "rarity": "Rare", "low": 250, "high": 600, "cost": 80},
            {"name": "Bi-Xenon Headlights", "rarity": "Rare", "low": 150, "high": 400, "cost": 25},
            {"name": "Brembo-Style Calipers (set)", "rarity": "Rare", "low": 200, "high": 500, "cost": 55},
        ],
    },
    "928": {
        "display": "Porsche 928",
        "make": "Porsche",
        "year_range": (1978, 1995),
        "top_parts": [
            {"name": "Anything — 928 parts are unobtanium", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        ],
    },
    "924": {
        "display": "Porsche 924/944",
        "make": "Porsche",
        "year_range": (1977, 1991),
        "top_parts": [
            {"name": "Anything — transaxle Porsche parts all sell", "rarity": "Legendary", "low": 150, "high": 600, "cost": 40},
        ],
    },
    "econoline": {
        "display": "Ford Econoline (vanlife)",
        "make": "Ford",
        "year_range": (1992, 2014),
        "top_parts": [
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 20, "option": True},
            {"name": "Bench Seats (rear rows)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
            {"name": "7.3L Powerstroke Parts (verify engine)", "rarity": "Epic", "low": 200, "high": 600, "cost": 50, "yr_max": 2003},
        ],
    },
}

# ---------------------------------------------------------------------------
# 2026-09 BREADTH EXPANSION
#
# Audit of the live national inventory showed ~36% of vehicles matched nothing
# — partly year-range floors that excluded older enthusiast generations (a
# 1988 4Runner matched zero parts), partly recent-year-only part gates (a 2005
# CR-V matched the model but every part had yr_min >= 2017), partly feed
# spelling mismatches ("Town And Country" vs the "town & country" key,
# "Mazda 3" vs "mazda3"), and partly ~50 high-volume models with no entry.
#
# Standards for every entry below (same discipline the price audit validated):
# conservative low/high anchor ranges for typical US sold prices, carryable
# parts only (no engines/transmissions as units), sell_speed grounded via
# SELL_GUIDE, condition notes in the part name where condition is the market.
# "manual": True gates a part on confirmed manual transmission; "drive":
# ["4wd"] on confirmed drivetrain — both use the listing/VIN/if-equipped
# honesty trilogy in match_vehicle, never inference.
# ---------------------------------------------------------------------------

def _extend_entry(key: str, *, year_range: tuple | None = None, parts: list | None = None) -> None:
    e = UNOBTANIUM_DB[key]
    if year_range:
        e["year_range"] = year_range
    if parts:
        e["top_parts"].extend(parts)


# --- Year-range floors lowered to include earlier generations with real markets ---
_extend_entry("4runner", year_range=(1984, 2024), parts=[
    # 1st/2nd gen (solid-axle era) — the owner's test case, huge enthusiast market
    {"name": "Manual Locking Hubs (pair)", "rarity": "Epic", "low": 80, "high": 200, "cost": 20, "yr_max": 1995, "drive": ["4wd"]},
    {"name": "Corner/Marker Lights (pair, uncracked)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12, "yr_max": 1995},
    {"name": "Rear Liftgate Glass + Regulator (works)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30, "yr_max": 2002},
    {"name": "Manual Shifter + Knob (5-spd)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12, "manual": True},
    {"name": "Bucket Seats (clean pair)", "rarity": "Uncommon", "low": 80, "high": 250, "cost": 40, "yr_max": 2002},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15, "yr_max": 2002},
])
_extend_entry("mustang", year_range=(1979, 2024), parts=[
    # Fox-body / SN95 / New Edge
    {"name": "Fox Dash Pad (uncracked)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 1993},
    {"name": "Rear Seat (clean)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25, "yr_max": 2004},
    {"name": "Manual Pedal Assembly (clutch swap gold)", "rarity": "Epic", "low": 80, "high": 220, "cost": 20, "yr_max": 2004, "manual": True},
    {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20, "yr_max": 2014},
])
_extend_entry("f-150", year_range=(1980, 2024), parts=[
    # OBS (1980-1996) — rust-free body parts are the market
    {"name": "OBS Grille + Headlight Bezels", "rarity": "Epic", "low": 80, "high": 250, "cost": 20, "yr_max": 1996},
    {"name": "Tailgate (straight, rust-free)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30, "yr_max": 1996},
    {"name": "Bench Seat (uncracked)", "rarity": "Uncommon", "low": 60, "high": 200, "cost": 30, "yr_max": 1996},
])
_extend_entry("accord", year_range=(1990, 2024), parts=[
    {"name": "Manual Shifter Assembly + Knob", "rarity": "Rare", "low": 40, "high": 130, "cost": 12, "manual": True},
    {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
])
_extend_entry("camry", year_range=(1992, 2024), parts=[
    {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    {"name": "Alternator (spin-test at yard)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 20},
])
_extend_entry("jetta", year_range=(1985, 2024), parts=[
    {"name": "Manual Shifter + Linkage", "rarity": "Rare", "low": 40, "high": 120, "cost": 15, "manual": True},
    {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20, "yr_max": 2018},
])
_extend_entry("bmw 3", year_range=(1992, 2024), parts=[
    # E36 era now included
    {"name": "Manual Shift Assembly (E36/E46 swap demand)", "rarity": "Rare", "low": 60, "high": 180, "cost": 20, "yr_max": 2006, "manual": True},
])
_extend_entry("sienna", year_range=(1998, 2024))
_extend_entry("cr-v", parts=[
    {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    {"name": "Rear Cargo Cover", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 10},
])
_extend_entry("rav4", parts=[
    {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 15},
    {"name": "Spare Tire Cover (hard shell)", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 10, "yr_max": 2005},
])
_extend_entry("tahoe", parts=[
    {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
])
_extend_entry("suburban", parts=[
    {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
    {"name": "Rear Barn Door Glass + Hardware", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "yr_max": 2006},
])
# Evergreen commuter parts for high-volume entries whose old years matched thin
for _k in ("corolla", "altima", "sentra", "malibu", "cruze", "escape", "explorer"):
    _extend_entry(_k, parts=[
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ])

# --- New entries: high-volume models the audit found uncovered ---
UNOBTANIUM_DB.update({
    # -- Nissan volume --
    "rogue": {
        "display": "Nissan Rogue", "make": "Nissan", "year_range": (2008, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2017},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2014},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "versa": {
        "display": "Nissan Versa", "make": "Nissan", "year_range": (2007, 2024),
        "top_parts": [
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 20},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 15},
            {"name": "Window Regulator + Motor (front)", "rarity": "Uncommon", "low": 30, "high": 75, "cost": 12},
        ],
    },
    "murano": {
        "display": "Nissan Murano", "make": "Nissan", "year_range": (2003, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2015},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2009},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 15},
        ],
    },
    "titan": {
        "display": "Nissan Titan", "make": "Nissan", "year_range": (2004, 2024),
        "top_parts": [
            {"name": "Tow Mirrors (pair)", "rarity": "Rare", "low": 80, "high": 200, "cost": 25, "option": True},  # new quality tow pairs ~$200-260 — 80% ceiling (2026-09)
            {"name": "Tailgate (straight)", "rarity": "Uncommon", "low": 100, "high": 280, "cost": 30},
            {"name": "Rockford Fosgate Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "armada": {
        "display": "Nissan Armada", "make": "Nissan", "year_range": (2004, 2024),
        # 2004-2007 titles say "Pathfinder Armada" — the longer keyword makes
        # the plain pathfinder entry a substring casualty on those.
        "match": ["pathfinder armada", "armada"],  # longer first so its hit substring-drops "pathfinder"
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 70, "high": 180, "cost": 25, "option": True},
        ],
    },
    "quest": {
        "display": "Nissan Quest", "make": "Nissan", "year_range": (1999, 2017),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2004},
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 30},
        ],
    },
    # -- GM volume --
    "traverse": {
        "display": "Chevrolet Traverse", "make": "Chevrolet", "year_range": (2009, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2018},
            {"name": "Rear Entertainment Screen", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 15, "option": True},
        ],
    },
    "acadia": {
        "display": "GMC Acadia", "make": "GMC", "year_range": (2007, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "terrain": {
        "display": "GMC Terrain", "make": "GMC", "year_range": (2010, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 400, "cost": 40, "yr_min": 2018},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 15},
            {"name": "Pioneer Amp + Speakers", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
        ],
    },
    "envoy": {
        "display": "GMC Envoy", "make": "GMC", "year_range": (2002, 2009),
        "top_parts": [
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
            {"name": "Sunroof Motor + Glass", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "option": True},
        ],
    },
    "hhr": {
        "display": "Chevrolet HHR", "make": "Chevrolet", "year_range": (2006, 2011),
        "top_parts": [
            {"name": "SS Front Fascia + Grille", "rarity": "Epic", "low": 120, "high": 350, "cost": 25, "trim": ["SS"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Roof Rails (pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 12},
        ],
    },
    "cavalier": {
        "display": "Chevrolet Cavalier", "make": "Chevrolet", "year_range": (1995, 2005),
        "top_parts": [
            {"name": "Z24 Ground Effects / Spoiler", "rarity": "Rare", "low": 60, "high": 180, "cost": 20, "trim": ["Z24"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            {"name": "Manual Shifter Assembly", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 12, "manual": True},
        ],
    },
    "express": {
        "display": "Chevrolet Express", "make": "Chevrolet", "year_range": (1996, 2024),
        "top_parts": [
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "option": True},
            {"name": "Rear Barn Door Glass (pair)", "rarity": "Uncommon", "low": 50, "high": 130, "cost": 20},
            {"name": "Bench Seats (rear rows)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
        ],
    },
    "monte carlo": {
        "display": "Chevrolet Monte Carlo", "make": "Chevrolet", "year_range": (1978, 2007),
        "top_parts": [
            {"name": "G-body Trim + Emblems (78-88)", "rarity": "Epic", "low": 60, "high": 200, "cost": 15, "yr_max": 1988},
            {"name": "SS Spoiler + Badging", "rarity": "Rare", "low": 60, "high": 180, "cost": 15, "trim": ["SS"]},
            {"name": "Dash Pad (uncracked, G-body)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 1988},
            # W-body era (1995+) base cars previously had zero un-gated parts.
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15, "yr_min": 1995},
        ],
    },
    "cutlass": {
        "display": "Oldsmobile Cutlass", "make": "Oldsmobile", "year_range": (1978, 1999),
        "top_parts": [
            {"name": "G-body Trim + Emblems", "rarity": "Epic", "low": 60, "high": 200, "cost": 15, "yr_max": 1988},
            {"name": "Dash Pad (uncracked, G-body)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 1988},
            {"name": "Rally Wheels (set)", "rarity": "Rare", "low": 80, "high": 250, "cost": 40, "yr_max": 1988},
        ],
    },
    # -- Buick/Cadillac/Pontiac volume --
    "lesabre": {
        "display": "Buick LeSabre", "make": "Buick", "year_range": (1992, 2005),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
            {"name": "Alternator (spin-test at yard)", "rarity": "Uncommon", "low": 35, "high": 85, "cost": 20},
        ],
    },
    "lacrosse": {
        "display": "Buick LaCrosse", "make": "Buick", "year_range": (2005, 2019),
        "top_parts": [
            {"name": "OEM HID/LED Headlights", "rarity": "Rare", "low": 150, "high": 350, "cost": 35, "yr_min": 2010},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "century": {
        "display": "Buick Century", "make": "Buick", "year_range": (1982, 2005),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 15},
        ],
    },
    "regal": {
        "display": "Buick Regal", "make": "Buick", "year_range": (1978, 2020),
        "top_parts": [
            {"name": "Grand National / T-Type Trim", "rarity": "Legendary", "low": 150, "high": 500, "cost": 25, "yr_max": 1987, "trim": ["Grand National", "T-Type", "GNX"]},
            {"name": "G-body Dash Pad (uncracked)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20, "yr_max": 1987},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18, "yr_min": 1997},
        ],
    },
    "lucerne": {
        "display": "Buick Lucerne", "make": "Buick", "year_range": (2006, 2011),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "verano": {
        "display": "Buick Verano", "make": "Buick", "year_range": (2012, 2017),
        "top_parts": [
            {"name": "HID Headlights (pair)", "rarity": "Rare", "low": 120, "high": 300, "cost": 30},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
        ],
    },
    "enclave": {
        "display": "Buick Enclave", "make": "Buick", "year_range": (2008, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "deville": {
        "display": "Cadillac DeVille", "make": "Cadillac", "year_range": (1994, 2005),
        "top_parts": [
            {"name": "HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 280, "cost": 30, "yr_min": 2000},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
            {"name": "Chrome Wheels (set)", "rarity": "Uncommon", "low": 100, "high": 300, "cost": 60},
        ],
    },
    "escalade": {
        "display": "Cadillac Escalade", "make": "Cadillac", "year_range": (1999, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 700, "cost": 60, "yr_min": 2015},
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 320, "cost": 35},
            # Power-retract steps optional on most Escalade years.
            {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 40, "yr_min": 2007, "option": True},
            {"name": "Bose/AKG Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 180, "cost": 25},
        ],
    },
    "pontiac g6": {
        "display": "Pontiac G6", "make": "Pontiac", "year_range": (2005, 2010),
        "top_parts": [
            {"name": "GXP Front Fascia + Spoiler", "rarity": "Rare", "low": 80, "high": 220, "cost": 25, "trim": ["GXP"]},  # GTP (2005-07) never had the GXP fascia
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            # Convertible body style only — body style isn't decodable here and most G6s are
            # coupes/sedans.
            {"name": "Hardtop-Convertible Roof Motor", "rarity": "Rare", "low": 80, "high": 220, "cost": 25, "option": True},
        ],
    },
    "grand prix": {
        "display": "Pontiac Grand Prix", "make": "Pontiac", "year_range": (1997, 2008),
        "top_parts": [
            {"name": "GTP Supercharger Accessories (pulleys/brackets)", "rarity": "Rare", "low": 60, "high": 180, "cost": 20, "trim": ["GTP", "GXP"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 20},
            {"name": "Rear Spoiler", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 15},
        ],
    },
    "grand am": {
        "display": "Pontiac Grand Am", "make": "Pontiac", "year_range": (1996, 2005),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
        ],
    },
    # -- Mopar volume --
    "journey": {
        "display": "Dodge Journey", "make": "Dodge", "year_range": (2009, 2020),
        "top_parts": [
            {"name": "Uconnect Touchscreen Head Unit", "rarity": "Uncommon", "low": 70, "high": 180, "cost": 40},
            # Journey 3rd row optional (5-seat versions very common).
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 260, "cost": 30, "option": True},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
        ],
    },
    "dakota": {
        "display": "Dodge Dakota", "make": "Dodge", "year_range": (1987, 2011),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Uncommon", "low": 80, "high": 220, "cost": 30},
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "option": True},
            {"name": "Manual Shifter Assembly", "rarity": "Rare", "low": 40, "high": 120, "cost": 15, "manual": True},
            {"name": "R/T Badging + Trim", "rarity": "Rare", "low": 50, "high": 150, "cost": 12, "trim": ["R/T"]},
        ],
    },
    "caliber": {
        "display": "Dodge Caliber", "make": "Dodge", "year_range": (2007, 2012),
        "top_parts": [
            {"name": "SRT-4 Recaro-style Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 60, "trim": ["SRT"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18},
        ],
    },
    "dart": {
        "display": "Dodge Dart", "make": "Dodge", "year_range": (2013, 2016),
        "top_parts": [
            {"name": "Uconnect 8.4 Touchscreen", "rarity": "Rare", "low": 100, "high": 250, "cost": 40},
            {"name": "HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 280, "cost": 30},
            {"name": "Manual Shifter Assembly", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15, "manual": True},
        ],
    },
    "sebring": {
        "display": "Chrysler Sebring", "make": "Chrysler", "year_range": (1996, 2010),
        "top_parts": [
            {"name": "Convertible Top Motor + Pump", "rarity": "Rare", "low": 60, "high": 180, "cost": 20},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18},
        ],
    },
    "chrysler 300": {
        "display": "Chrysler 300", "make": "Chrysler", "year_range": (2005, 2023),
        "top_parts": [
            {"name": "HID/LED Headlights (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2011},
            {"name": "Chrome Grille", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 15},
            {"name": "Uconnect 8.4 Touchscreen", "rarity": "Rare", "low": 100, "high": 250, "cost": 40, "yr_min": 2011},
            {"name": "SRT Spoiler + Badging", "rarity": "Rare", "low": 80, "high": 220, "cost": 20, "trim": ["SRT"]},
        ],
    },
    "pt cruiser": {
        "display": "Chrysler PT Cruiser", "make": "Chrysler", "year_range": (2001, 2010),
        "top_parts": [
            {"name": "GT Turbo Trim + Spoiler", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 15, "trim": ["GT"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 18},
            {"name": "Chrome Accessories (shifter/vents)", "rarity": "Uncommon", "low": 25, "high": 70, "cost": 10},
        ],
    },
    # -- Ford/Lincoln/Mercury volume --
    "ford edge": {
        "display": "Ford Edge", "make": "Ford", "year_range": (2007, 2024),
        "top_parts": [
            {"name": "SYNC 3 Touchscreen + APIM", "rarity": "Rare", "low": 100, "high": 260, "cost": 40, "yr_min": 2016},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 420, "cost": 40, "yr_min": 2015},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
            {"name": "Panoramic Sunroof Glass", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30, "yr_min": 2011, "option": True},
        ],
    },
    "fiesta": {
        "display": "Ford Fiesta", "make": "Ford", "year_range": (2011, 2019),
        "top_parts": [
            {"name": "ST Steering Wheel", "rarity": "Rare", "low": 70, "high": 170, "cost": 12, "trim": ["ST"]},
            {"name": "ST Rear Spoiler", "rarity": "Rare", "low": 60, "high": 150, "cost": 15, "trim": ["ST"]},
            {"name": "Heated Side Mirrors (pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 12, "option": True},
            # US Fiesta ST launched 2014 — row used to claim 2011+.
            {"name": "ST Recaro Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 75, "yr_min": 2014, "trim": ["ST"], "option": True},
            {"name": "SYNC Touchscreen", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 35, "yr_min": 2014},
            {"name": "Manual Shifter Assembly", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15, "manual": True},
        ],
    },
    "navigator": {
        "display": "Lincoln Navigator", "make": "Lincoln", "year_range": (1998, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "yr_min": 2015},
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            # Optional on Navigator until ~2018.
            {"name": "Power Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 40, "yr_min": 2007, "option": True},
            # NOT option-flagged: air std on Navigator (4-corner '98-'06, rear after).
            {"name": "Air Suspension Compressor", "rarity": "Rare", "low": 80, "high": 220, "cost": 25},
        ],
    },
    # -- Kia/Hyundai volume --
    "sorento": {
        "display": "Kia Sorento", "make": "Kia", "year_range": (2003, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 420, "cost": 40, "yr_min": 2016},
            # Sorento sold in 5- and 7-seat configs — 3rd row optional.
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 260, "cost": 30, "yr_min": 2011, "option": True},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "sportage": {
        "display": "Kia Sportage", "make": "Kia", "year_range": (2005, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 400, "cost": 40, "yr_min": 2017},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "sedona": {
        "display": "Kia Sedona", "make": "Kia", "year_range": (2002, 2021),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2006},
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 90, "high": 240, "cost": 30},
        ],
    },
    "spectra": {
        "display": "Kia Spectra", "make": "Kia", "year_range": (2000, 2009),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 18},
            {"name": "Alternator (spin-test at yard)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 20},
        ],
    },
    "forte": {
        "display": "Kia Forte", "make": "Kia", "year_range": (2010, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 150, "high": 380, "cost": 40, "yr_min": 2019},
            {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 35, "yr_min": 2014},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "santa fe": {
        "display": "Hyundai Santa Fe", "make": "Hyundai", "year_range": (2001, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 420, "cost": 40, "yr_min": 2017},
            # Infinity audio first offered on the 2007 CM Santa Fe — was claiming 2001+.
            {"name": "Infinity Amp + Speakers", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20, "yr_min": 2007},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2013},
        ],
    },
    "tucson": {
        "display": "Hyundai Tucson", "make": "Hyundai", "year_range": (2005, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 400, "cost": 40, "yr_min": 2016},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "accent": {
        "display": "Hyundai Accent", "make": "Hyundai", "year_range": (2000, 2024),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
            {"name": "Window Regulator + Motor (front)", "rarity": "Uncommon", "low": 30, "high": 75, "cost": 12},
        ],
    },
    # -- Saturn / Mazda / Volvo / Mercedes volume --
    "vue": {
        "display": "Saturn VUE", "make": "Saturn", "year_range": (2002, 2010),
        "top_parts": [
            {"name": "Red Line Trim + Wheels", "rarity": "Rare", "low": 80, "high": 250, "cost": 40, "trim": ["Red Line"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
        ],
    },
    "cx-9": {
        "display": "Mazda CX-9", "make": "Mazda", "year_range": (2007, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 260, "cost": 30},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 420, "cost": 40, "yr_min": 2016},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "cx-5": {
        "display": "Mazda CX-5", "make": "Mazda", "year_range": (2013, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 180, "high": 420, "cost": 40, "yr_min": 2016},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "xc90": {
        "display": "Volvo XC90", "make": "Volvo", "year_range": (2003, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 260, "cost": 30},
            {"name": "Headlights (clear/xenon pair)", "rarity": "Rare", "low": 80, "high": 240, "cost": 25},
            {"name": "Integrated Child Booster Seats", "rarity": "Rare", "low": 60, "high": 160, "cost": 15},
        ],
    },
    "volvo 850": {
        "display": "Volvo 850 (brick era)", "make": "Volvo", "year_range": (1993, 1997),
        "top_parts": [
            {"name": "T-5R/R Trim + Spoiler", "rarity": "Legendary", "low": 100, "high": 350, "cost": 20, "trim": ["T-5R", " R"]},
            {"name": "Headlights + Corners (pair)", "rarity": "Rare", "low": 50, "high": 150, "cost": 20},
            {"name": "Manual Shifter Assembly", "rarity": "Rare", "low": 40, "high": 120, "cost": 15, "manual": True},
        ],
    },
    "volvo 940": {
        "display": "Volvo 940/960 (brick era)", "make": "Volvo", "year_range": (1991, 1998),
        "top_parts": [
            {"name": "Headlights + Grille (pair)", "rarity": "Rare", "low": 50, "high": 140, "cost": 20},
            {"name": "Tow Hitch (bolt-on)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "c-class": {
        "display": "Mercedes-Benz C-Class", "make": "Mercedes-Benz", "year_range": (1994, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "yr_min": 2015},
            {"name": "Wood Trim Set (unbroken)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 15},
            {"name": "AMG Trim + Badging", "rarity": "Rare", "low": 80, "high": 240, "cost": 20, "trim": ["AMG"]},
            {"name": "Side Mirrors (power fold, pair)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
        ],
    },
    "e-class": {
        "display": "Mercedes-Benz E-Class", "make": "Mercedes-Benz", "year_range": (1996, 2024),
        "top_parts": [
            {"name": "OEM LED/Xenon Headlights", "rarity": "Epic", "low": 200, "high": 550, "cost": 55, "yr_min": 2010},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 170, "cost": 25, "option": True},
            {"name": "Wood Trim Set (unbroken)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 15},
            {"name": "AMG Trim + Badging", "rarity": "Rare", "low": 80, "high": 240, "cost": 20, "trim": ["AMG"]},
            # SBC era only: W211 E-Class 2003-2006 (facelift dropped SBC). Used
            # tested units €449-£528, reman $400-600, new OEM $4,716 + $550 core
            # — rebuilders buy untested pulls as cores (2026-09-21)
            {"name": "SBC Brake Hydraulic Unit (W211)", "rarity": "Epic", "low": 150, "high": 400, "cost": 20, "yr_min": 2003, "yr_max": 2006},
        ],
    },
    # -- Jeep compact volume --
    "patriot": {
        "display": "Jeep Patriot", "make": "Jeep", "year_range": (2007, 2017),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18},
            {"name": "Roof Rails (pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 12},
            {"name": "Manual Shifter Assembly", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15, "manual": True},
        ],
    },
    "compass": {
        "display": "Jeep Compass", "make": "Jeep", "year_range": (2007, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 150, "high": 380, "cost": 40, "yr_min": 2017},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18, "yr_max": 2016},
            {"name": "Uconnect Touchscreen", "rarity": "Uncommon", "low": 70, "high": 180, "cost": 40, "yr_min": 2017},
        ],
    },
    # -- Toyota gaps --
    "yaris": {
        "display": "Toyota Yaris", "make": "Toyota", "year_range": (2007, 2020),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 95, "cost": 18},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
            {"name": "Manual Shifter + Knob", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 12, "manual": True},
        ],
    },
    "echo": {
        "display": "Toyota Echo (mileage cult)", "make": "Toyota", "year_range": (2000, 2005),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 18},
            {"name": "Manual Shifter + Knob", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 12, "manual": True},
        ],
    },
})

UNOBTANIUM_DB.update({
    "mdx": {
        "display": "Acura MDX", "make": "Acura", "year_range": (2001, 2024),
        "top_parts": [
            {"name": "OEM LED (Jewel Eye) Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "yr_min": 2014},
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 260, "cost": 30},
            {"name": "ELS/Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 20},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2007},
        ],
    },
    "galant": {
        "display": "Mitsubishi Galant", "make": "Mitsubishi", "year_range": (1999, 2012),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
        ],
    },
    "volvo s60": {
        "display": "Volvo S60", "make": "Volvo", "year_range": (2001, 2024),
        "top_parts": [
            {"name": "Xenon/LED Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
            {"name": "R Trim Seats (pair)", "rarity": "Epic", "low": 200, "high": 500, "cost": 60, "trim": [" R", "T6 R"]},
            {"name": "Side Mirrors (heated, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "avalanche": {
        "display": "Chevrolet Avalanche", "make": "Chevrolet", "year_range": (2002, 2013),
        "top_parts": [
            {"name": "Bed Cover Panels (set of 3)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
            {"name": "Midgate Glass + Hardware", "rarity": "Rare", "low": 80, "high": 220, "cost": 25},
        ],
    },
    "colorado": {
        "display": "Chevrolet Colorado", "make": "Chevrolet", "year_range": (2004, 2024),
        "top_parts": [
            {"name": "Tailgate (straight)", "rarity": "Uncommon", "low": 100, "high": 280, "cost": 30},
            {"name": "Z71/ZR2 Trim + Skid Plates", "rarity": "Rare", "low": 80, "high": 250, "cost": 25, "trim": ["Z71", "ZR2"]},
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "option": True},
        ],
    },
    "pacifica": {
        "display": "Chrysler Pacifica", "make": "Chrysler", "year_range": (2004, 2024),
        "top_parts": [
            {"name": "Power Sliding Door Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15, "yr_min": 2017},
            {"name": "Uconnect Touchscreen", "rarity": "Rare", "low": 100, "high": 250, "cost": 40, "yr_min": 2017},
            # Optional on the 2004-08 Pacifica crossover (5/6-seat common); std on the 2017+
            # minivan — flag errs honest for the junkyard-age fleet.
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 30, "option": True},
        ],
    },
    "commander": {
        "display": "Jeep Commander", "make": "Jeep", "year_range": (2006, 2010),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 90, "high": 240, "cost": 30},
            {"name": "Sunroof Glass (front/rear)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20, "option": True},
        ],
    },
    "aveo": {
        "display": "Chevrolet Aveo", "make": "Chevrolet", "year_range": (2004, 2011),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 18},
            {"name": "Window Regulator + Motor (front)", "rarity": "Uncommon", "low": 30, "high": 70, "cost": 12},
        ],
    },
    "kia rio": {
        "display": "Kia Rio", "make": "Kia", "year_range": (2001, 2024),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 18},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 15},
        ],
    },
    "five hundred": {
        "display": "Ford Five Hundred", "make": "Ford", "year_range": (2005, 2007),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
        ],
    },
    "rendezvous": {
        "display": "Buick Rendezvous", "make": "Buick", "year_range": (2002, 2007),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
            # Optional (sold as 5- or 7-seat).
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30, "option": True},
        ],
    },
})
_extend_entry("corolla", year_range=(1993, 2024))
_extend_entry("malibu", year_range=(1997, 2024))

# --- Feed-spelling aliases: same entry object, different key the feeds use ---
# ("Town And Country" never contained "town & country"; "Mazda 3" has a space.)
for _alias, _key in (
    ("town and country", "town & country"),
    ("mazda 3", "mazda3"),
    ("mazda 6", "mazda6"),
    ("crv", "cr-v"),
    ("dodge caravan", "grand caravan"),
    ("e-series", "econoline"),
):
    UNOBTANIUM_DB[_alias] = UNOBTANIUM_DB[_key]

# ---------------------------------------------------------------------------
# 2026-09 GENERATION SPLITS
#
# Audit finding: single entries spanning several generations of a model carried
# ONE price band and parts list across generations with very different markets
# (a 1996-2002 3rd-gen 4Runner and a 2003-2009 4th-gen share almost no
# valuable parts; a Fox-body Mustang and an S550 share none). Worse, some
# parts were gated to the wrong generation entirely (KDSS listed for the
# 2003-2009 4Runner — that's GX470/5th-gen Trail hardware; "Air Suspension
# Compressor" on 2005-2010 Grand Cherokees — Quadra-Lift arrived with the
# 2011 WK2).
#
# Each split below replaces one entry with per-generation entries that share a
# "match" keyword but carry disjoint year ranges, so any vehicle hits exactly
# one. Generation break years are the accepted US-market ones. Price bands are
# carried over from the audited entry unless market evidence said otherwise —
# every changed band cites its basis in a comment and, for the significant
# ones, in scraper/price_baseline.json.
# ---------------------------------------------------------------------------


def _split_generations(base_key: str, *, display: str, make: str,
                       gens: list[dict], match: list[str] | None = None,
                       drop_keys: tuple = ()) -> None:
    """Replace UNOBTANIUM_DB[base_key] with one entry per generation."""
    for k in (base_key, *drop_keys):
        UNOBTANIUM_DB.pop(k, None)
    keywords = match or [base_key]
    for g in gens:
        lo, hi = g["years"]
        UNOBTANIUM_DB[f"{base_key} {lo}-{hi}"] = {
            "display": f"{display} ({g['label']})",
            "make": make,
            "gen": g["label"],
            "match": keywords,
            "year_range": (lo, hi),
            "top_parts": g["parts"],
        }


_split_generations("4runner", display="Toyota 4Runner", make="Toyota", gens=[
    {"label": "1st/2nd gen", "years": (1984, 1995), "parts": [
        # new Aisin FHT-018 ~$101-149/hub ($200-300 pair, newparts/yotashop); cheap clones ~$60-120 — OEM premium real, used OEM sold $120-220, ceiling 0.8x$250 OK (2026-09)
        {"name": "Manual Locking Hubs (pair)", "rarity": "Epic", "low": 80, "high": 200, "cost": 20, "drive": ["4wd"]},
        {"name": "Rear Liftgate Glass + Regulator (works)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
        {"name": "Corner/Marker Lights (pair, uncracked)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12},
        {"name": "Manual Shifter + Knob (5-spd)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12, "manual": True},
        {"name": "Bucket Seats (clean pair)", "rarity": "Uncommon", "low": 80, "high": 250, "cost": 40},
        {"name": "Roof Rack Crossbars", "rarity": "Rare", "low": 84, "high": 250, "cost": 20},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        # used OEM 22RE/3VZE AFMs ask ~$175 and sell out; new OEM $600-1,200 & near-NLA (2026-09-21).
        # yr_min 1985: EFI (22R-E) arrived MY1985 — '84s are carbureted 22R, no AFM.
        {"name": "AFM (Air Flow Meter, 22RE/3.0)", "rarity": "Epic", "low": 80, "high": 180, "cost": 10, "yr_min": 1985},
        {"name": "Climate Control Panel (works, knobs intact)", "rarity": "Rare", "low": 40, "high": 100, "cost": 10},
    ]},
    {"label": "3rd gen", "years": (1996, 2002), "parts": [
        # Factory rear e-locker is a 3rd-gen option — previously claimed for ALL years.
        {"name": "Rear E-Locker Actuator Motor", "rarity": "Legendary", "low": 250, "high": 500, "cost": 15, "option": True},
        # Sport/Highlander scooped hood (1999-2002 only): documented junkyard
        # pulls sold $300-350, clean painted example $395; repro hood + scoop
        # insert + paint runs ~$500 all-in. Sell local — shipping is freight. (2026-09-21)
        {"name": "Hood w/ Scoop (Sport/Highlander pkg)", "rarity": "Epic", "low": 200, "high": 400, "cost": 45, "yr_min": 1999, "option": True},
        {"name": "Rear Liftgate Glass + Regulator (works)", "rarity": "Epic", "low": 100, "high": 300, "cost": 30},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 80, "high": 180, "cost": 20},  # new DEPO/TYC pair $148-172 (HeadlightsDepot 2026-09) — 80% ceiling caps used high
        # electric t-case shift is Limited multi-mode gear; SR5s use a lever (2026-09-21 audit)
        {"name": "Transfer Case Shift Motor", "rarity": "Epic", "low": 90, "high": 200, "cost": 15, "drive": ["4wd"], "option": True},
        {"name": "Heated Side Mirrors (pair)", "rarity": "Rare", "low": 80, "high": 130, "cost": 15},  # new heated power pairs (Dorman/Kool Vue) ~$100-160 — 80% ceiling ~$104 displayed (2026-09)
        {"name": "Center Console Lid (uncracked)", "rarity": "Rare", "low": 50, "high": 250, "cost": 8},
        {"name": "Roof Rack Crossbars", "rarity": "Rare", "low": 84, "high": 250, "cost": 20},
        {"name": "Manual Shifter + Knob (5-spd)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12, "manual": True},
        {"name": "Bucket Seats (clean pair)", "rarity": "Uncommon", "low": 80, "high": 250, "cost": 40},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        # fragile-interior adds (2026-09-21): working climate units ask $100-250,
        # master window switches $50-160 — bands conservative vs asks
        {"name": "Climate Control Unit (works)", "rarity": "Rare", "low": 40, "high": 110, "cost": 12},
        {"name": "Window Master Switch", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 10},
    ]},
    {"label": "4th gen", "years": (2003, 2009), "parts": [
        # 4th gen ran X-REAS (not KDSS — that was a GX470/5th-gen-Trail thing);
        # band aligned with other electronic-shock pairs (AutoRide evidence).
        # Sport/Limited equipment, not on SR5 — flag as option (2026-09-21 audit).
        {"name": "X-REAS Suspension Shocks (pair)", "rarity": "Epic", "low": 150, "high": 350, "cost": 20, "option": True},
        # 3rd row was a rare option on the 4th-gen 4Runner.
        {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35, "option": True},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20},
        # electric shift = V8/full-time cars; V6 SR5s use a lever (2026-09-21 audit)
        {"name": "Transfer Case Shift Motor", "rarity": "Epic", "low": 90, "high": 200, "cost": 15, "drive": ["4wd"], "option": True},
        {"name": "Heated Side Mirrors (pair)", "rarity": "Rare", "low": 80, "high": 130, "cost": 15},  # new heated power pairs ~$100-160 — 80% ceiling (2026-09)
        {"name": "Center Console Lid (uncracked)", "rarity": "Rare", "low": 50, "high": 250, "cost": 8},
        {"name": "Roof Rack Crossbars", "rarity": "Rare", "low": 84, "high": 250, "cost": 20},
        {"name": "Window Master Switch", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 10},
    ]},
    {"label": "5th gen", "years": (2010, 2024), "parts": [
        {"name": "TRD Pro Grille", "rarity": "Legendary", "low": 300, "high": 600, "cost": 40, "yr_min": 2014},
        {"name": "OEM LED Headlights", "rarity": "Epic", "low": 400, "high": 800, "cost": 60, "yr_min": 2014},
        # KDSS moved here from the mis-gated 2003-2009 range — Trail/TRD Off-Road only.
        {"name": "KDSS Sway Bar Actuators", "rarity": "Legendary", "low": 200, "high": 500, "cost": 20, "trim": ["Trail", "TRD Off-Road", "TRD Pro"]},
        {"name": "Rear E-Locker Actuator Motor", "rarity": "Epic", "low": 200, "high": 450, "cost": 15, "trim": ["Trail", "TRD Off-Road", "TRD Pro"]},
        # electric shift = Limited full-time 4WD; SR5/TRD use a lever (2026-09-21 audit)
        {"name": "Transfer Case Shift Motor", "rarity": "Epic", "low": 90, "high": 200, "cost": 15, "drive": ["4wd"], "option": True},
        {"name": "Heated Side Mirrors (pair)", "rarity": "Rare", "low": 80, "high": 130, "cost": 15},  # new heated power pairs ~$120-180 (Kool Vue) — 80% ceiling (2026-09)
        {"name": "Roof Rack Crossbars", "rarity": "Rare", "low": 84, "high": 250, "cost": 20},
        {"name": "Center Console Lid (uncracked)", "rarity": "Rare", "low": 50, "high": 250, "cost": 8},
    ]},
])

_split_generations("tacoma", display="Toyota Tacoma", make="Toyota", gens=[
    {"label": "1st gen", "years": (1995, 2004), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 20},  # DEAD-FLIP tier: new DEPO pairs $74-84 (HeadlightsDepot/Amazon 2026-09) — used can only be scrap-cheap
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 30},
        {"name": "Manual Shifter + Knob (5-spd)", "rarity": "Rare", "low": 40, "high": 120, "cost": 12, "manual": True},
        # fragile-interior adds (2026-09-21): working 01-04 climate units ask
        # $100-250, master window switches $50-160 — bands conservative vs asks
        {"name": "Climate Control Unit (works)", "rarity": "Rare", "low": 40, "high": 110, "cost": 12},
        {"name": "Window Master Switch", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 10},
    ]},
    {"label": "2nd gen", "years": (2005, 2015), "parts": [
        {"name": "TRD Skid Plate", "rarity": "Epic", "low": 150, "high": 350, "cost": 25},
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 30},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 50, "high": 140, "cost": 20},  # new DEPO/TYC pairs ~$85-160 — 80% ceiling caps used high (2026-09)
        {"name": "Window Master Switch", "rarity": "Uncommon", "low": 30, "high": 80, "cost": 10},
    ]},
    {"label": "3rd gen", "years": (2016, 2024), "parts": [
        {"name": "TRD Pro Grille", "rarity": "Legendary", "low": 200, "high": 450, "cost": 30},
        {"name": "OEM LED Headlights", "rarity": "Epic", "low": 350, "high": 700, "cost": 50},
        {"name": "OEM Fender Flares (color-matched)", "rarity": "Epic", "low": 200, "high": 500, "cost": 30},
        {"name": "TRD Skid Plate", "rarity": "Epic", "low": 150, "high": 350, "cost": 25},
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 30},
        # 16-21 master switch (84820-04080) asks $160 used (2026-09-21) — conservative band
        {"name": "Window Master Switch", "rarity": "Uncommon", "low": 40, "high": 100, "cost": 10},
    ]},
])

_split_generations("civic", display="Honda Civic", make="Honda", gens=[
    # New coverage: EG/EH (5th gen) — big enthusiast market, previously below
    # the entry's 1996 floor and matched nothing.
    {"label": "5th gen EG", "years": (1992, 1995), "parts": [
        {"name": "Si Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si"]},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
        {"name": "OEM Radio / Climate Panel", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22},
    ]},
    {"label": "6th gen EK", "years": (1996, 2000), "parts": [
        {"name": "Si/Type R Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si", "Type R", "Type-R"]},
        {"name": "Si Front Lip (OEM)", "rarity": "Rare", "low": 75, "high": 175, "cost": 12, "trim": ["Si"]},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
        {"name": "OEM Radio / Climate Panel", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22},
    ]},
    {"label": "7th gen", "years": (2001, 2005), "parts": [
        {"name": "Si/Type R Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si", "Type R", "Type-R"]},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
        {"name": "OEM Radio / Climate Panel", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22},
    ]},
    {"label": "8th gen", "years": (2006, 2011), "parts": [
        {"name": "Si/Type R Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si", "Type R", "Type-R"]},
        {"name": "Si Front Lip (OEM)", "rarity": "Rare", "low": 75, "high": 175, "cost": 12, "trim": ["Si"]},
        {"name": "Power Side Mirror (heated)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 30},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22},
        {"name": "OEM Radio / Climate Panel", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
    {"label": "9th gen", "years": (2012, 2015), "parts": [
        {"name": "Si Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si"]},
        {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35, "yr_min": 2014},
        {"name": "Power Side Mirror (heated)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 30},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 22},
    ]},
    {"label": "10th/11th gen", "years": (2016, 2024), "parts": [
        {"name": "Si/Type R Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Si", "Type R", "Type-R"]},
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35},
        {"name": "Power Side Mirror (heated)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 30},
        {"name": "Instrument Cluster", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 18},
    ]},
])

_split_generations("accord", display="Honda Accord", make="Honda", gens=[
    {"label": "1990-1997 (CB/CD)", "years": (1990, 1997), "parts": [
        {"name": "Manual Shifter Assembly + Knob", "rarity": "Rare", "low": 40, "high": 130, "cost": 12, "manual": True},
        {"name": "Gauge Cluster / IPC", "rarity": "Uncommon", "low": 55, "high": 160, "cost": 20},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 25},
    ]},
    {"label": "6th gen", "years": (1998, 2002), "parts": [
        {"name": "Manual Shifter Assembly + Knob", "rarity": "Rare", "low": 40, "high": 130, "cost": 12, "manual": True},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 25},
        {"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 35, "high": 110, "cost": 18},
        {"name": "Gauge Cluster / IPC", "rarity": "Uncommon", "low": 55, "high": 160, "cost": 20},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "7th/8th gen", "years": (2003, 2012), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 25},
        {"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 35, "high": 110, "cost": 18},
        {"name": "Gauge Cluster / IPC", "rarity": "Uncommon", "low": 55, "high": 160, "cost": 20},
        {"name": "Manual Shifter Assembly + Knob", "rarity": "Rare", "low": 40, "high": 130, "cost": 12, "manual": True},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "9th gen", "years": (2013, 2017), "parts": [
        {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35},
        {"name": "Sport Front Lip", "rarity": "Rare", "low": 75, "high": 200, "cost": 12, "trim": ["Sport"]},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 25},
        {"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 35, "high": 110, "cost": 18},
        {"name": "Gauge Cluster / IPC", "rarity": "Uncommon", "low": 55, "high": 160, "cost": 20},
    ]},
    {"label": "10th/11th gen", "years": (2018, 2024), "parts": [
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 300, "high": 550, "cost": 40},
        {"name": "Sport Front Lip", "rarity": "Rare", "low": 75, "high": 200, "cost": 12, "trim": ["Sport"]},
        {"name": "Touchscreen Head Unit", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 35},
        {"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 35, "high": 110, "cost": 18},
    ]},
])

_split_generations("mustang", display="Ford Mustang", make="Ford", gens=[
    {"label": "Fox body", "years": (1979, 1993), "parts": [
        {"name": "Fox Dash Pad (uncracked)", "rarity": "Epic", "low": 100, "high": 300, "cost": 20},
        {"name": "Manual Pedal Assembly (clutch swap gold)", "rarity": "Epic", "low": 80, "high": 220, "cost": 20, "manual": True},
        {"name": "Rear Seat (clean)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
    ]},
    {"label": "SN95/New Edge", "years": (1994, 2004), "parts": [
        {"name": "Manual Pedal Assembly (clutch swap gold)", "rarity": "Epic", "low": 80, "high": 220, "cost": 20, "manual": True},
        {"name": "Rear Seat (clean)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
    ]},
    {"label": "S197", "years": (2005, 2014), "parts": [
        {"name": "GT Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2007, "trim": ["GT"]},
        {"name": "Recaro Seats (Boss/GT500)", "rarity": "Epic", "low": 500, "high": 1200, "cost": 75, "yr_min": 2012, "trim": ["GT500", "Shelby", "Boss"], "option": True},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 20},
    ]},
    {"label": "S550/S650", "years": (2015, 2024), "parts": [
        {"name": "Recaro Seats (PP/GT350)", "rarity": "Epic", "low": 500, "high": 1200, "cost": 75, "trim": ["GT350", "GT500", "Shelby", "Mach 1"], "option": True},
        {"name": "GT Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["GT"]},
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
    ]},
])

_split_generations("f-150", display="Ford F-150", make="Ford",
                   match=["f-150", "f150"], drop_keys=("f150",), gens=[
    {"label": "OBS", "years": (1980, 1996), "parts": [
        {"name": "OBS Grille + Headlight Bezels", "rarity": "Epic", "low": 80, "high": 250, "cost": 20},
        {"name": "Tailgate (straight, rust-free)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
        {"name": "Bench Seat (uncracked)", "rarity": "Uncommon", "low": 60, "high": 200, "cost": 30},
    ]},
    {"label": "10th gen", "years": (1997, 2003), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        # Same audited tailgate market as Ram/Ranger ($50-900 sold, condition-driven).
        {"name": "Tailgate (straight)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
    ]},
    {"label": "11th/12th gen", "years": (2004, 2014), "parts": [
        # LOWERED from 500-1300: the $450-1,200 sold evidence was 2021+ trucks (camera/BLIS);
        # 09-14 quality aftermarket pairs are $400-550 new — 80% ceiling caps used (2026-09).
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 40, "option": True},
        # RAISED from 200-500: audited sold evidence $525-600.
        {"name": "Raptor Grille", "rarity": "Legendary", "low": 550, "high": 750, "cost": 25, "yr_min": 2010, "trim": ["Raptor"]},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        {"name": "Tailgate (straight)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
    ]},
    {"label": "13th/14th gen", "years": (2015, 2024), "parts": [
        {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 300, "high": 700, "cost": 40, "option": True},
        # Generation-fits: 13th-gen (15-20) and 14th-gen (21+) lights/grilles
        # don't interchange; 21+ LED assemblies (zone lighting, BLIS wiring)
        # pull noticeably more.
        {"name": "OEM LED Headlights (13th gen)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_max": 2020},
        {"name": "OEM LED Headlights (14th gen)", "rarity": "Epic", "low": 350, "high": 750, "cost": 55, "yr_min": 2021},
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 500, "high": 1300, "cost": 40, "option": True},
        # Gen-2 Raptor arrived 2017 (no 15-16 Raptor); gen-3 grille differs.
        {"name": "Raptor Grille (gen 2)", "rarity": "Legendary", "low": 550, "high": 750, "cost": 25, "yr_min": 2017, "yr_max": 2020, "trim": ["Raptor"]},
        {"name": "Raptor Grille (gen 3)", "rarity": "Legendary", "low": 550, "high": 800, "cost": 25, "yr_min": 2021, "trim": ["Raptor"]},
    ]},
])

_split_generations("silverado", display="Chevy Silverado", make="Chevrolet", gens=[
    {"label": "GMT800", "years": (1999, 2006), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        {"name": "Tow Mirrors (manual, pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
        {"name": "Tailgate (straight)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
    ]},
    {"label": "GMT900", "years": (2007, 2013), "parts": [
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 300, "high": 420, "cost": 30, "option": True},  # new quality aftermarket pairs ~$360-420 — 80% ceiling (2026-09)
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        {"name": "Tailgate (straight)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
    ]},
    {"label": "K2XX", "years": (2014, 2018), "parts": [
        {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 35, "option": True},
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 300, "high": 420, "cost": 30, "option": True},  # new power-fold pairs $410 (AmericanTrucks 14-18) — 80% ceiling $328 displayed (2026-09)
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
    ]},
    {"label": "T1XX", "years": (2019, 2024), "parts": [
        {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50},
        {"name": "Multi-Flex Tailgate Steps", "rarity": "Epic", "low": 200, "high": 500, "cost": 30},
        {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 35, "option": True},
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 300, "high": 520, "cost": 30, "option": True},  # new pairs $515 (AmericanTrucks 19-26) — 80% ceiling $412 displayed (2026-09)
    ]},
])

_split_generations("sierra", display="GMC Sierra (Silverado twin)", make="GMC", gens=[
    {"label": "GMT800", "years": (1999, 2006), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        {"name": "Tow Mirrors (manual, pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
        {"name": "Tailgate (straight)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
        {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 20},
    ]},
    {"label": "GMT900", "years": (2007, 2013), "parts": [
        {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 420, "cost": 30, "option": True},  # new quality aftermarket pairs ~$360-420 — 80% ceiling (2026-09)
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
        {"name": "Denali Grille / Trim", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "trim": ["Denali"]},
        {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 20},
    ]},
    {"label": "K2XX", "years": (2014, 2018), "parts": [
        {"name": "OEM LED Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 50, "yr_min": 2016},
        {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 420, "cost": 30, "option": True},  # new power-fold pairs $410 (AmericanTrucks 14-18) — 80% ceiling (2026-09)
        {"name": "Tailgate (w/ camera)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
        {"name": "Denali Grille / Trim", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "trim": ["Denali"]},
        {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 20},
    ]},
    {"label": "T1XX", "years": (2019, 2024), "parts": [
        {"name": "OEM LED Headlights", "rarity": "Epic", "low": 250, "high": 600, "cost": 50},
        {"name": "MultiPro Tailgate Steps", "rarity": "Epic", "low": 200, "high": 500, "cost": 30},
        {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 300, "high": 520, "cost": 30, "option": True},  # new pairs $515 (AmericanTrucks 19-26) — 80% ceiling (2026-09)
        {"name": "Denali Grille / Trim", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "trim": ["Denali"]},
        {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 175, "cost": 20},
    ]},
])

_split_generations("ram", display="Ram / Dodge Ram Truck", make="Ram", gens=[
    {"label": "2nd gen", "years": (1994, 2001), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
        {"name": "Gauge Cluster", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 20},
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
    ]},
    {"label": "3rd gen", "years": (2002, 2008), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
        {"name": "Gauge Cluster", "rarity": "Uncommon", "low": 75, "high": 200, "cost": 20},
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
    ]},
    {"label": "4th gen", "years": (2009, 2018), "parts": [
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 35, "option": True},  # new Ram power-fold pairs ~$450-550 — 80% ceiling (2026-09)
        {"name": "Uconnect 8.4 Touchscreen", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45, "yr_min": 2013},
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
    ]},
    {"label": "5th gen", "years": (2019, 2024), "parts": [
        {"name": "12\" Uconnect Touchscreen", "rarity": "Epic", "low": 400, "high": 800, "cost": 50},
        {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 35, "option": True},  # new Ram power-fold pairs ~$450-550 — 80% ceiling (2026-09)
        {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
    ]},
])

_split_generations("explorer", display="Ford Explorer", make="Ford", gens=[
    {"label": "1st/2nd gen", "years": (1991, 2001), "parts": [
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
    {"label": "3rd/4th gen", "years": (2002, 2010), "parts": [
        # Optional on 2002-2010 Explorers; std from 2011, so later gens unflagged.
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "option": True},
        {"name": "Rear Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2006, "option": True},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22, "yr_max": 2005},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_min": 2006},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
    {"label": "5th gen", "years": (2011, 2019), "parts": [
        # 3rd row std on 2011+ Explorer — no option flag from here on.
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
        {"name": "SYNC / MyFord Touch Screen", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
    {"label": "6th gen", "years": (2020, 2024), "parts": [
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40},
        {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
])

_split_generations("grand cherokee", display="Jeep Grand Cherokee", make="Jeep", gens=[
    {"label": "ZJ/WJ", "years": (1993, 2004), "parts": [
        {"name": "Transfer Case Shift Motor", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
        # RAISED from 150-350: WJ pairs sold $175-500 (forums/recyclers, 2026-09).
        {"name": "Heated Leather Seats (pair)", "rarity": "Rare", "low": 175, "high": 450, "cost": 30, "yr_min": 1999},
    ]},
    {"label": "WK", "years": (2005, 2010), "parts": [
        # NOTE: no air suspension this gen — Quadra-Lift arrived with the 2011
        # WK2; the old entry wrongly claimed it from 2005.
        {"name": "Transfer Case Shift Motor", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
        {"name": "Heated Leather Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
    ]},
    {"label": "WK2", "years": (2011, 2021), "parts": [
        # Quadra-Lift optional on most WK2 trims.
        {"name": "Air Suspension Compressor (Quadra-Lift)", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "option": True},
        {"name": "Heated Leather Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
        {"name": "Transfer Case Shift Motor", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
    ]},
    {"label": "WL", "years": (2022, 2024), "parts": [
        {"name": "Air Suspension Compressor (Quadra-Lift)", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "option": True},
        {"name": "Heated Leather Seats (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30},
    ]},
])

_split_generations("wrangler", display="Jeep Wrangler", make="Jeep", gens=[
    # Hardtop bands per generation from tracked FB/Craigslist/forum sales
    # (YJ $300-900, TJ $600-1,400, JK $1,000-2,000, JL $1,200-2,800) — the old
    # single 400-1500 band understated JK/JL and overstated YJ.
    {"label": "YJ", "years": (1987, 1995), "parts": [
        # Soft top std every Wrangler gen — hardtop is an option (all gens flagged).
        {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 350, "high": 900, "cost": 60, "option": True},
        {"name": "Half Doors (pair)", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
    ]},
    {"label": "TJ", "years": (1996, 2006), "parts": [
        {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 700, "high": 1600, "cost": 60, "option": True},
        {"name": "Half Doors (pair)", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        {"name": "Rubicon Locker Actuators", "rarity": "Epic", "low": 100, "high": 275, "cost": 10, "yr_min": 2003, "trim": ["Rubicon"]},
    ]},
    {"label": "JK", "years": (2007, 2017), "parts": [
        {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 1100, "high": 2400, "cost": 60, "option": True},
        {"name": "Half Doors (pair)", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        {"name": "Rubicon Locker Actuators", "rarity": "Epic", "low": 100, "high": 275, "cost": 10, "trim": ["Rubicon"]},
    ]},
    {"label": "JL", "years": (2018, 2024), "parts": [
        {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 1400, "high": 3300, "cost": 60, "option": True},
        {"name": "Half Doors (pair)", "rarity": "Legendary", "low": 200, "high": 800, "cost": 40},
        {"name": "Rubicon Locker Actuators", "rarity": "Epic", "low": 100, "high": 275, "cost": 10, "trim": ["Rubicon"]},
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 300, "high": 600, "cost": 50, "trim": ["Sahara", "Rubicon", "High Altitude", "Moab"], "option": True},
    ]},
])

_split_generations("tahoe", display="Chevy Tahoe", make="Chevrolet", gens=[
    {"label": "GMT400/800", "years": (1995, 2006), "parts": [
        # LOWERED from 150-350: used electronic AutoRide shocks have a thin
        # market (bladder-failure risk) — forum pairs move around $100.
        {"name": "AutoRide Rear Shocks (pair)", "rarity": "Epic", "low": 100, "high": 250, "cost": 20, "yr_min": 2000},
        # 3rd row arrived with the 2000 GMT800 — the old entry claimed it for 1995+.
        # 3rd row NOT option-flagged on Tahoe — near-universal take rate.
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35, "yr_min": 2000},
        {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "GMT900", "years": (2007, 2014), "parts": [
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        {"name": "AutoRide Rear Shocks (pair)", "rarity": "Epic", "low": 100, "high": 250, "cost": 20},
        {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "K2XX/T1XX", "years": (2015, 2024), "parts": [
        {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 80, "high": 225, "cost": 15},
        {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
    ]},
])

_split_generations("cherokee", display="Jeep Cherokee", make="Jeep", gens=[
    {"label": "XJ", "years": (1984, 2001), "parts": [
        {"name": "XJ Header Panel (clean)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 25},
        {"name": "Clean Fenders (no rust)", "rarity": "Epic", "low": 100, "high": 275, "cost": 20},
        {"name": "Overhead Console (digital)", "rarity": "Rare", "low": 75, "high": 200, "cost": 10},
    ]},
    # KL (2014+) — previously inside the XJ entry's year range but every part
    # was gated pre-2002, so these matched NOTHING. Modest commuter parts only.
    {"label": "KL", "years": (2014, 2024), "parts": [
        {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
        {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 18},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
])

_split_generations("camaro", display="Chevy Camaro", make="Chevrolet", gens=[
    # 3rd/4th gen were previously uncovered (entry floor was 2010).
    # T-top basis: used glass sets list/sell $75-300 (3rd gen) and $195-350
    # (4th gen); specialty retail singles run $450 (2026-09 search).
    {"label": "3rd gen", "years": (1982, 1992), "parts": [
        {"name": "T-Top Glass Panels (pair)", "rarity": "Epic", "low": 150, "high": 350, "cost": 30},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "4th gen", "years": (1993, 2002), "parts": [
        {"name": "T-Top Glass Panels (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 30},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
    ]},
    {"label": "5th gen", "years": (2010, 2015), "parts": [
        {"name": "SS Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["SS", "ZL1", "Z28", "1LE"]},
        {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SS", "ZL1", "1LE"], "option": True},
        {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20},
    ]},
    {"label": "6th gen", "years": (2016, 2024), "parts": [
        {"name": "SS Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["SS", "ZL1", "Z28", "1LE"]},
        {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SS", "ZL1", "1LE"], "option": True},
        {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 400, "cost": 40},
    ]},
])

_split_generations("scion xb", display="Scion xB", make="Scion", gens=[
    {"label": "1st gen", "years": (2004, 2006), "parts": [
        {"name": "Gen1 Bumpers / Body Panels (straight)", "rarity": "Rare", "low": 80, "high": 250, "cost": 25},
        {"name": "Gen1 Interior Trim / Cluster", "rarity": "Rare", "low": 60, "high": 175, "cost": 10},
    ]},
    # 2nd gen (2008-2015) sat inside the old entry's range with zero un-gated
    # parts, so those cars matched nothing. Commuter-band coverage only.
    {"label": "2nd gen", "years": (2008, 2015), "parts": [
        {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 18},
        {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    ]},
])

# Twin/derivative entries lost parts to the new specificity guard — give the
# specific entries the generic parts they genuinely share with the base model.
_extend_entry("ram 2500", parts=[
    {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 35, "yr_min": 2010, "option": True},  # new Ram power-fold pairs ~$450-550 — 80% ceiling (2026-09)
    {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
])
_extend_entry("ram 3500", parts=[
    {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 450, "cost": 35, "yr_min": 2010, "option": True},  # new Ram power-fold pairs ~$450-550 — 80% ceiling (2026-09)
    {"name": "Tailgate (clean)", "rarity": "Rare", "low": 150, "high": 400, "cost": 35},
])
_extend_entry("sentra se-r", parts=[
    {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
])
_extend_entry("lancer evolution", parts=[
    {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
    {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
])

# ---------------------------------------------------------------------------
# 2026-09 COVERAGE EXPANSION — feed-name misses and uncovered volume models
#
# The offline rematch (scraper/dry_run_match.py) over the cached national scan
# showed these as the highest-frequency zero-match make/models with genuine
# resale demand. Bands reuse audited cross-model bands for the same part
# category unless a fresh basis is cited.
# ---------------------------------------------------------------------------

# Mercedes feeds name cars "C300"/"E320"/"Ml350", never "C-Class"/"E-Class".
# Numeric tokens are make-qualified ("benz c250") so GM C/K truck names like
# "Suburban C2500" can't collide.
UNOBTANIUM_DB["c-class"]["match"] = ["c-class"] + [
    f"benz {t}" for t in ("c230", "c240", "c250", "c280", "c300", "c320", "c350", "c400", "c43", "c63")]
UNOBTANIUM_DB["e-class"]["match"] = ["e-class"] + [
    f"benz {t}" for t in ("e300", "e320", "e350", "e400", "e420", "e430", "e500", "e550", "e55", "e63")]
# Ford van feeds say "E-150"/"E-250"/"E-350", not "Econoline".
UNOBTANIUM_DB["econoline"]["match"] = [
    "econoline", "e-series", "e-150", "e-250", "e-350",
    "ford e150", "ford e250", "ford e350"]
# Chevy feeds spell it "S-10".
UNOBTANIUM_DB["s10"]["match"] = ["s10", "s-10"]
# DTS is the DeVille's 2006-2011 successor — same parts market.
UNOBTANIUM_DB["deville"]["match"] = ["deville", "dts"]
UNOBTANIUM_DB["deville"]["display"] = "Cadillac DeVille / DTS"
UNOBTANIUM_DB["deville"]["year_range"] = (1994, 2011)
# B5/B6 A4s (1996-2001) were below the old floor; 1.8T-era swap parts sell.
UNOBTANIUM_DB["audi a4"]["year_range"] = (1996, 2024)
UNOBTANIUM_DB["audi a4"]["top_parts"].append(
    {"name": "Manual Shift Assembly + Pedals (swap gold)", "rarity": "Rare", "low": 60, "high": 180, "cost": 20, "yr_max": 2005, "manual": True})
# Gen1/2 Taurus SHO (1989-1999) was below the old floor; SHO trim gate applies.
UNOBTANIUM_DB["taurus"]["year_range"] = (1990, 2019)

UNOBTANIUM_DB.update({
    "new beetle": {
        "display": "VW New Beetle / Beetle", "make": "Volkswagen",
        # Shares the "beetle" keyword with the air-cooled entry — disjoint
        # year ranges keep them from double-matching.
        "match": ["beetle"], "year_range": (1998, 2019),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Turbo Parts (1.8T/2.0T — verify engine)", "rarity": "Rare", "low": 100, "high": 250, "cost": 30},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "lexus es": {
        "display": "Lexus ES", "make": "Lexus", "year_range": (1992, 2024),
        "top_parts": [
            {"name": "Mark Levinson Amp/Speakers", "rarity": "Rare", "low": 150, "high": 350, "cost": 25, "yr_min": 2007},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2013},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_max": 2012},
        ],
    },
    "m-class": {
        "display": "Mercedes-Benz M-Class (ML)", "make": "Mercedes-Benz",
        "match": ["m-class", "ml250", "ml320", "ml350", "ml430", "ml500", "ml550", "ml55", "ml63"],
        "year_range": (1998, 2015),
        "top_parts": [
            {"name": "Xenon/HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 170, "cost": 25, "option": True},
            # Optional accessory on the ML.
            {"name": "Running Boards (pair)", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 25, "option": True},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "s-class": {
        # Depreciation-trap flagship: yards are full of $100k cars whose gadgets
        # still sell. Most toys were standard on the S, so few option gates.
        "display": "Mercedes-Benz S-Class", "make": "Mercedes-Benz",
        "match": ["s-class", "s320", "s350", "s400", "s420", "s430", "s500", "s550", "s560", "s600", "s63", "s65"],
        "year_range": (1992, 2020),
        "top_parts": [
            {"name": "Xenon/LED Headlights (pair)", "rarity": "Epic", "low": 200, "high": 550, "cost": 30},
            {"name": "Soft-Close Door Motors (each)", "rarity": "Rare", "low": 80, "high": 220, "cost": 20},
            {"name": "Airmatic Suspension Compressor", "rarity": "Rare", "low": 100, "high": 260, "cost": 25, "yr_min": 2000},
            {"name": "COMAND Screen / Head Unit", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "yr_min": 2000},
            {"name": "Harman Kardon / Burmester Amp", "rarity": "Rare", "low": 80, "high": 250, "cost": 25},
            {"name": "Front Seats (heated/vented, pair)", "rarity": "Rare", "low": 200, "high": 500, "cost": 60},
            # Distronic radar cruise was an option box even on the S.
            {"name": "Distronic Radar Module", "rarity": "Rare", "low": 100, "high": 280, "cost": 20, "yr_min": 2000, "option": True},
        ],
    },
    "flex": {
        "display": "Ford Flex", "make": "Ford", "year_range": (2009, 2019),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "SYNC / MyFord Touch Screen", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 45, "yr_min": 2011},
            {"name": "EcoBoost Turbo Intercooler (verify engine)", "rarity": "Rare", "low": 85, "high": 185, "cost": 25},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
        ],
    },
    "honda fit": {
        "display": "Honda Fit", "make": "Honda", "year_range": (2007, 2020),
        "top_parts": [
            # Complete assemblies from dismantlers; new OEM cushion pads alone
            # run $340-480, so a working used rear seat holds real value.
            {"name": "Magic Seat (rear, complete)", "rarity": "Uncommon", "low": 80, "high": 250, "cost": 30},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "9-3": {
        "display": "Saab 9-3", "make": "Saab", "year_range": (1999, 2011),
        "top_parts": [
            # SID pixel failure is universal — working displays sell on sight.
            {"name": "SID Info Display (good pixels)", "rarity": "Rare", "low": 60, "high": 160, "cost": 12},
            {"name": "Xenon Headlights (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "option": True},
            {"name": "Convertible Top Hydraulic Pump", "rarity": "Rare", "low": 100, "high": 240, "cost": 25, "option": True},
            {"name": "Aero Front Bumper / Trim", "rarity": "Rare", "low": 100, "high": 300, "cost": 30, "trim": ["Aero", "Viggen"]},
            {"name": "Leather Seats (pair)", "rarity": "Uncommon", "low": 80, "high": 220, "cost": 40},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
        ],
    },
    "ion": {
        "display": "Saturn ION (Redline hunt)", "make": "Saturn", "year_range": (2003, 2007),
        "top_parts": [
            # Forum sales of front+rear Recaro sets: $75-400 (2026-09 search).
            {"name": "Redline Recaro Seats (set)", "rarity": "Epic", "low": 150, "high": 450, "cost": 40, "trim": ["Redline", "Red Line"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
        ],
    },
    "solara": {
        "display": "Toyota Camry Solara", "make": "Toyota", "year_range": (1999, 2008),
        # "camry solara" makes the plain camry entry a substring casualty on
        # "Camry Solara" listings — the coupe/convertible entry should win.
        "match": ["camry solara", "solara"],  # longer first so its hit substring-drops "camry"
        "top_parts": [
            # Recycler-listed used units $75-345 (2026-09 search).
            {"name": "Convertible Top Motor/Pump", "rarity": "Rare", "low": 100, "high": 300, "cost": 20, "yr_min": 2000},
            {"name": "JBL Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 20},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 120, "cost": 20},
        ],
    },
    "mountaineer": {
        "display": "Mercury Mountaineer (Explorer twin)", "make": "Mercury", "year_range": (1997, 2010),
        "top_parts": [
            # Same optional 3rd row as the 2002-2010 Explorer it twins.
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_min": 2002, "option": True},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "sable": {
        "display": "Mercury Sable (Taurus twin)", "make": "Mercury", "year_range": (1992, 2009),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "mariner": {
        "display": "Mercury Mariner (Escape twin)", "make": "Mercury", "year_range": (2005, 2011),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "tribute": {
        "display": "Mazda Tribute (Escape twin)", "make": "Mazda", "year_range": (2001, 2011),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "nitro": {
        "display": "Dodge Nitro", "make": "Dodge", "year_range": (2007, 2012),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 20},
            {"name": "Roof Rack Crossbars", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "outlander": {
        "display": "Mitsubishi Outlander", "make": "Mitsubishi", "year_range": (2003, 2024),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20, "yr_max": 2015},
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "transit connect": {
        "display": "Ford Transit Connect", "make": "Ford", "year_range": (2010, 2023),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Side Mirrors (power, pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "ford transit": {
        "display": "Ford Transit (vanlife)", "make": "Ford",
        # "transit" would also hit Transit Connect — the specificity guard
        # prefers the longer "transit connect" keyword on those.
        "match": ["transit"], "year_range": (2015, 2024),
        "top_parts": [
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},
            {"name": "Bench Seats (rear rows)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "tiguan": {
        "display": "VW Tiguan", "make": "Volkswagen", "year_range": (2009, 2024),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20, "yr_max": 2017},
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 15},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "volkswagen cc": {
        "display": "VW CC", "make": "Volkswagen",
        "match": ["volkswagen cc", "vw cc"], "year_range": (2009, 2017),
        "top_parts": [
            {"name": "Xenon/LED Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "acura rl": {
        "display": "Acura RL", "make": "Acura", "year_range": (1996, 2012),
        "top_parts": [
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 125, "high": 225, "cost": 30, "yr_min": 2005},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "m35": {
        "display": "Infiniti M (M35/M45/M37/M56)", "make": "Infiniti",
        "match": ["m35", "m45", "m37", "m56"], "year_range": (2003, 2013),
        "top_parts": [
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 125, "high": 225, "cost": 30},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "cx-7": {
        "display": "Mazda CX-7", "make": "Mazda", "year_range": (2007, 2012),
        "top_parts": [
            {"name": "Turbo Intercooler (2.3 DISI)", "rarity": "Rare", "low": 85, "high": 185, "cost": 25},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    # These next models previously "matched" only via substring accidents
    # ("srx"→"rx", "fx35"→"x3", "qx56"→"x5") and were being priced with the
    # WRONG model's parts. Honest entries of their own:
    "srx": {
        "display": "Cadillac SRX", "make": "Cadillac", "year_range": (2004, 2016),
        "top_parts": [
            {"name": "Xenon/HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
    "infiniti fx": {
        "display": "Infiniti FX", "make": "Infiniti",
        "match": ["fx35", "fx45", "fx37", "fx50"], "year_range": (2003, 2013),
        "top_parts": [
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 125, "high": 225, "cost": 30},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "qx56": {
        "display": "Infiniti QX56/QX80", "make": "Infiniti",
        "match": ["qx56", "qx80"], "year_range": (2004, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Uncommon", "low": 120, "high": 300, "cost": 35},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Power Liftgate Motor", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 15},
        ],
    },
    "hyundai genesis": {
        # Sedan only — the make-qualified keyword avoids the coupe entry,
        # which substring-drops this one on "Genesis Coupe" listings.
        "display": "Hyundai Genesis Sedan", "make": "Hyundai",
        "match": ["hyundai genesis"], "year_range": (2009, 2016),
        "top_parts": [
            {"name": "Lexicon Amp + Speakers", "rarity": "Uncommon", "low": 60, "high": 170, "cost": 25},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 125, "high": 225, "cost": 30},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "ridgeline": {
        "display": "Honda Ridgeline", "make": "Honda", "year_range": (2006, 2024),
        "top_parts": [
            {"name": "Dual-Action Tailgate (clean)", "rarity": "Rare", "low": 100, "high": 280, "cost": 30},
            {"name": "In-Bed Trunk Lid", "rarity": "Rare", "low": 75, "high": 200, "cost": 15},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 140, "cost": 20},
        ],
    },
    "xc70": {
        "display": "Volvo XC70 / V70 Cross Country", "make": "Volvo", "year_range": (1998, 2016),
        "top_parts": [
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 15},
            {"name": "Cargo Cover / Dog Gate", "rarity": "Uncommon", "low": 40, "high": 120, "cost": 10},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "protege": {
        "display": "Mazda Protege", "make": "Mazda", "year_range": (1990, 2003),
        "top_parts": [
            {"name": "Mazdaspeed/MP3 Seats + Trim", "rarity": "Epic", "low": 150, "high": 400, "cost": 40, "trim": ["Mazdaspeed", "MP3"]},
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 18},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 30, "high": 85, "cost": 15},
        ],
    },
    "milan": {
        "display": "Mercury Milan (Fusion twin)", "make": "Mercury", "year_range": (2006, 2011),
        "top_parts": [
            {"name": "Headlights (clear pair)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "volvo s80": {
        "display": "Volvo S80", "make": "Volvo",
        "match": ["s80"], "year_range": (1999, 2016),
        "top_parts": [
            {"name": "Xenon/HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 35, "high": 100, "cost": 15},
        ],
    },
    "cadillac sts": {
        "display": "Cadillac STS", "make": "Cadillac",
        "match": ["sts", "cadillac seville"], "year_range": (1992, 2011),
        "top_parts": [
            {"name": "Xenon/HID Headlights (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 30, "yr_min": 2005},
            {"name": "Bose Amp + Speakers", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 20},
            {"name": "Tail Lights (pair, uncracked)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 15},
        ],
    },
})

# ---------------------------------------------------------------------------
# 2026-10 CONSENSUS EVERGREENS — closing the taxonomy's commodity-seller gap.
#
# Every public flipper source we cross-checked (self-service-chain buying
# guides, parts-flipper blogs, several creators' publicly stated lists, eBay
# sold-comp guidance, r/Flipping threads) agrees on a core set of used parts
# that sell reliably off ANY high-population vehicle: alternators, starters,
# gauge clusters, climate control panels, power window regulators + master
# switches, and engine/body control modules. Pre-expansion the taxonomy
# covered those on a handful of models (alternator: 3 of 385 entries) — a
# base Focus matched nothing but headlights while carrying four consensus
# sellers. Per-category source trail (3+ independent public sources each) and
# sold-comp bases: scraper/consensus_parts_research.md. No single creator's
# list or wording is reproduced — facts are synthesized across sources
# (owner/legal directive, 2026-10).
#
# Honesty rules carried over: bands are conservative working-pull resale
# anchors (calibrated down toward eBay sold by _resale_sold_calibrate like
# every other part); cluster/module caveats (mileage disclosure, programming)
# ride in SELL_GUIDE notes. AIRBAGS ARE DELIBERATELY ABSENT from this entire
# DB: eBay prohibits all airbag / inflator / airbag-cover listings sitewide
# (policy effective 2026-09-24) and the federal render-inoperative rule
# (49 U.S.C. 30122) puts used SRS parts out of bounds — steering wheels are
# listed only for pre-airbag-era trucks, where the wheel ships bare.
#
# Applied only to high-population entries (ranked against the 2026-10 national
# scan) so low-volume classic/exotic entries keep their curated, model-
# specific lists. A category an entry already tracks is skipped (token dedupe
# in _apply_consensus_evergreens), so hand-tuned bands always win.
# ---------------------------------------------------------------------------

# (part def, dedupe tokens): the part is skipped when the entry already has a
# part whose name contains any token.
_EVERGREEN_PARTS: tuple[tuple[dict, tuple[str, ...]], ...] = (
    ({"name": "Alternator (spin-test at yard)", "rarity": "Uncommon", "low": 35, "high": 90, "cost": 20},
     ("alternator",)),  # used OEM sold $35-80; quality reman new $90-180 — reuses the audited Camry band (2026-10)
    ({"name": "Starter (verify part number)", "rarity": "Uncommon", "low": 30, "high": 75, "cost": 18},
     ("starter",)),  # used OEM sold $30-65; quality new reman $80-150 (2026-10)
    ({"name": "Gauge Cluster", "rarity": "Uncommon", "low": 50, "high": 140, "cost": 15},
     ("cluster", "gauge", "speedometer", "digital dash", "cockpit")),  # used sold $40-150 on commuters, tach/digital higher; new often dealer-only $400+ (2026-10)
    ({"name": "Climate Control Panel (works, knobs intact)", "rarity": "Uncommon", "low": 40, "high": 110, "cost": 12},
     ("climate",)),  # used sold mostly $40-120 — matches the existing hand-entered bands (2026-10)
    ({"name": "Window Regulator + Motor (front)", "rarity": "Uncommon", "low": 30, "high": 75, "cost": 12, "yr_min": 1994},
     ("window regulator",)),  # used OEM sold $35-85; audited band reused; yr_min: power windows weren't near-universal before the mid-90s (2026-10)
    ({"name": "Power Window Master Switch", "rarity": "Uncommon", "low": 30, "high": 90, "cost": 10, "yr_min": 1994},
     ("master switch", "window switch")),  # used sold $25-80; audited band reused (2026-10)
    ({"name": "Engine/Body Control Module (match part #)", "rarity": "Uncommon", "low": 40, "high": 140, "cost": 15},
     ("control module", "ecm", "ecu", "bcm", "engine computer")),  # used sold $40-150 on high-population apps; programming caveat disclosed via SELL_GUIDE (2026-10)
)

# High-population entries from the 2026-10 national scan (volume-ranked; each
# dict key named exactly once — gen-split rows listed per generation).
_EVERGREEN_TARGET_KEYS: tuple[str, ...] = (
    # sedans / hatches
    "acura tl", "altima", "accent", "accord 1990-1997", "accord 1998-2002",
    "accord 2003-2012", "accord 2013-2017", "accord 2018-2024", "avenger",
    "camry", "century", "charger", "chrysler 200", "chrysler 300",
    "civic 1996-2000", "civic 2001-2005", "civic 2006-2011", "civic 2012-2015",
    "civic 2016-2024", "cobalt", "corolla", "cruze", "elantra", "fiesta",
    # ("aura" lives in parts_overlay.json, which merges AFTER this section —
    #  overlay-created rows can't be targeted here.)
    "focus", "fusion", "galant", "hhr", "impala", "jetta", "lacrosse",
    "lesabre", "lucerne", "malibu", "maxima", "mazda3", "optima", "passat",
    "pontiac g6", "regal", "sentra", "sonata", "taurus", "verano", "versa",
    # SUVs / CUVs / vans
    "acadia", "cr-v", "durango", "enclave", "equinox", "escape", "expedition",
    "explorer 1991-2001", "explorer 2002-2010", "explorer 2011-2019",
    "explorer 2020-2024", "ford edge", "forester", "grand caravan",
    "grand cherokee 1993-2004", "grand cherokee 2005-2010",
    "grand cherokee 2011-2021", "journey", "liberty", "murano", "odyssey",
    "outback", "pathfinder", "patriot", "pilot", "rav4", "rendezvous",
    "rogue", "santa fe", "sienna", "sorento", "soul", "suburban",
    "tahoe 1995-2006", "tahoe 2007-2014", "tahoe 2015-2024",
    "town & country", "trailblazer", "traverse", "vue", "yukon",
    # trucks / work vans
    "colorado", "dakota", "econoline", "f-150 1980-1996", "f-150 1997-2003",
    "f-150 2004-2014", "f-150 2015-2024", "f-250", "frontier", "ranger",
    "ram 1994-2001", "ram 2002-2008", "ram 2009-2018", "ram 2019-2024",
    "sierra 1999-2006", "sierra 2007-2013", "sierra 2014-2018",
    "sierra 2019-2024", "silverado 1999-2006", "silverado 2007-2013",
    "silverado 2014-2018", "silverado 2019-2024", "tacoma 1995-2004",
    "tacoma 2005-2015", "tacoma 2016-2024", "titan", "tundra",
)


def _apply_consensus_evergreens() -> None:
    """Append the consensus commodity sellers to each high-volume entry.

    A missing key fails loud (KeyError) rather than silently skipping — if an
    entry is renamed, this list must follow. Each part is copied so later
    generation-splitting can set per-copy year bounds safely."""
    for key in _EVERGREEN_TARGET_KEYS:
        info = UNOBTANIUM_DB[key]
        have = " | ".join(p["name"].lower() for p in info["top_parts"])
        for part, tokens in _EVERGREEN_PARTS:
            if any(t in have for t in tokens):
                continue  # entry already tracks this category with a hand-tuned band
            info["top_parts"].append(dict(part))


_apply_consensus_evergreens()

# ---- 2026-10 Phase A: enthusiast platforms, evergreens BY GENERATION ------
# Enthusiast entries often span several body generations under one key
# (mx-5 1990-2024, supra 1979-1998, corvette 1968-2013). Blanket evergreens
# there would ship "fits 1990–2024"-style claims that cross generations.
# Instead each copy is year-gated to one published generation window, so the
# body-part finder's same-model match ("fits YYYY–YYYY") stays honest.
# Windows are factory generation boundaries (US model years, manufacturer
# press/parts literature); an empty tuple means the entry already covers a
# single generation and gets ungated copies.
_ENTHUSIAST_EVERGREEN_GENS: dict[str, tuple[tuple[int, int], ...]] = {
    # Mazda
    "mx-5": ((1990, 1997), (1999, 2005), (2006, 2015), (2016, 2024)),
    "rx-7": ((1979, 1985), (1986, 1992), (1993, 1995)),
    "rx-8": (),
    # Honda / Acura
    "crx": ((1984, 1987), (1988, 1991)),
    "civic 1992-1995": (),
    "del sol": (),
    "integra": ((1990, 1993), (1994, 2001)),
    "rsx": (),
    "prelude": ((1988, 1991), (1992, 1996), (1997, 2001)),
    "s2000": (),
    # Toyota / Lexus / Scion / Subaru
    "supra": ((1979, 1981), (1982, 1986), (1987, 1992), (1993, 1998)),
    "celica": ((1985, 1985), (1986, 1989), (1990, 1993), (1994, 1999),
               (2000, 2005)),
    "mr2": ((1985, 1989), (1990, 1995), (2000, 2005)),
    "scion tc": ((2005, 2010), (2011, 2016)),
    "wrx": ((2002, 2007), (2008, 2014), (2015, 2021), (2022, 2024)),
    "impreza": ((1993, 2001), (2002, 2007), (2008, 2011), (2012, 2016),
                (2017, 2024)),
    "brz": ((2013, 2020), (2022, 2024)),
    "fr-s": (),
    # Nissan / Infiniti
    "240sx": ((1989, 1994), (1995, 1998)),
    "300zx": ((1984, 1989), (1990, 1996)),
    "350z": (),
    "370z": (),
    "g35": ((2003, 2006), (2007, 2008)),
    # Mitsubishi
    "eclipse": ((1990, 1994), (1995, 1999), (2000, 2005), (2006, 2012)),
    "lancer": ((2002, 2007), (2008, 2017)),
    "lancer evolution": ((2003, 2006), (2008, 2015)),
    # German
    "bmw 3": ((1992, 1998), (1999, 2006), (2007, 2011), (2012, 2018),
              (2019, 2024)),
    "bmw m3": ((2001, 2006), (2008, 2013), (2015, 2018), (2021, 2024)),
    "z4": ((2003, 2008), (2009, 2016), (2019, 2024)),
    "golf": ((1999, 2005), (2006, 2009), (2010, 2014), (2015, 2021),
             (2022, 2024)),
    "gti": ((2006, 2009), (2010, 2014), (2015, 2021), (2022, 2024)),
    # American (gen-split keys already bound one generation each)
    "camaro 1982-1992": (), "camaro 1993-2002": (), "camaro 2010-2015": (),
    "camaro 2016-2024": (),
    "mustang 1979-1993": (), "mustang 1994-2004": (), "mustang 2005-2014": (),
    "mustang 2015-2024": (),
    "firebird": ((1982, 1992), (1993, 2002)),
    "corvette": ((1968, 1982), (1984, 1996), (1997, 2004), (2005, 2013)),
    "wrangler 1987-1995": (), "wrangler 1996-2006": (),
    "wrangler 2007-2017": (), "wrangler 2018-2024": (),
}


def _apply_enthusiast_gen_evergreens() -> None:
    """Append evergreen copies to enthusiast entries, year-gated per gen.

    Same token-dedupe rule as _apply_consensus_evergreens: a hand-tuned part
    of the same category anywhere in the entry suppresses ALL windows for
    that category (hand bands always win). Window bounds are intersected with
    any evergreen-intrinsic yr_min (e.g. power-window parts floor at 1994);
    empty intersections are skipped."""
    for key, windows in _ENTHUSIAST_EVERGREEN_GENS.items():
        info = UNOBTANIUM_DB[key]
        lo, hi = info["year_range"]
        have = " | ".join(p["name"].lower() for p in info["top_parts"])
        for part, tokens in _EVERGREEN_PARTS:
            if any(t in have for t in tokens):
                continue  # entry already tracks this category
            for wlo, whi in windows or ((lo, hi),):
                copy = dict(part)
                copy["yr_min"] = max(wlo, lo, copy.get("yr_min", wlo))
                copy["yr_max"] = min(whi, hi, copy.get("yr_max", whi))
                if copy["yr_min"] > copy["yr_max"]:
                    continue  # window entirely outside entry/part bounds
                info["top_parts"].append(copy)


_apply_enthusiast_gen_evergreens()

# 90s-2000s full-size trucks: manual/telescoping tow mirrors were the one
# high-consensus truck category still missing on pre-power-fold generations
# (the power-fold rows only start when that option did). Option-flagged like
# every other tow-mirror row: towing packages were never standard and never
# VIN-decodable. Band mirrors the audited Silverado/Sierra GMT800 row.
for _k in ("f-150 1980-1996", "f-150 1997-2003", "ram 1994-2001",
           "ram 2002-2008", "c1500"):
    _extend_entry(_k, parts=[
        {"name": "Tow Mirrors (manual, pair)", "rarity": "Uncommon", "low": 60, "high": 160, "cost": 25, "option": True},  # used pairs sold $60-150; new quality pairs $140-280 — 80% ceiling (2026-10)
    ])

# Pre-airbag truck steering wheels — the one steering-wheel market multiple
# sources agree on (old Ford/Chevy work trucks). Year-gated to model years
# BEFORE driver airbags arrived (Ford/Dodge trucks 1994, GM C/K 1995), so the
# wheel ships bare and no SRS part ever changes hands through this app.
_extend_entry("f-150 1980-1996", parts=[
    {"name": "Steering Wheel (pre-airbag era)", "rarity": "Rare", "low": 50, "high": 150, "cost": 12, "yr_max": 1993},  # used sold $50-150; most OEM wheels NLA new (2026-10)
])
_extend_entry("c/k", parts=[
    {"name": "Steering Wheel (pre-airbag era)", "rarity": "Rare", "low": 50, "high": 150, "cost": 12, "yr_max": 1994},
])
_extend_entry("c1500", parts=[
    {"name": "Steering Wheel (pre-airbag era)", "rarity": "Rare", "low": 50, "high": 150, "cost": 12, "yr_max": 1994},
])
_extend_entry("dakota", parts=[
    {"name": "Steering Wheel (pre-airbag era)", "rarity": "Rare", "low": 50, "high": 150, "cost": 12, "yr_max": 1993},
])

# ---------------------------------------------------------------------------
# 2026-09 GENERATION-FITS AUDIT — interchange-sensitive parts must never carry
# a fits badge spanning vehicle generations.
#
# Problem: many parts carried one wide year band across several generations of
# a model even though the part doesn't physically interchange (an E60 5-series
# cluster is not an F10 cluster; a gen-3 CR-V tail light doesn't fit a gen-4).
# The value-differentiated cases (BMW 3/5 iDrive/clusters/lights, F-150 LEDs,
# Focus ST/RS, Elantra N, ...) are hand-split in their entries above with
# per-generation prices. Everything else is handled here mechanically: each
# base model gets its accepted US-market generation breakpoints (the first
# model year of each new generation), and _apply_generation_bounds() splits any
# interchange-sensitive part whose effective span crosses a breakpoint into
# per-generation rows with yr_min/yr_max bounds. Prices/rarity/flags are
# carried over unchanged — these are the parts whose used value is roughly
# flat across generations; only the fits badge needed correcting.
#
# Mechanical/carry-over parts (alternators, actuators, motors, hitches,
# roof racks, mirrors...) are deliberately NOT split — many genuinely
# interchange or sell on function, not body fitment.
# ---------------------------------------------------------------------------

# Interchange-sensitive part names: body panels, lighting, glass/tops, seats,
# clusters, head units, audio systems, steering wheels.
_GEN_SENSITIVE_RE = re.compile(
    r"cluster|digital dash|cockpit"
    r"|head unit|touchscreen|infotainment|navigation|radio|idrive|\bmmi\b"
    r"|\bsync\b|uconnect|mylink|entune|starlink|nissanconnect|\buvo\b|\bcue\b"
    r"|entertainment scree|video screen|display"
    r"|headlight|tail light|taillight|marker light|corner light|fog light"
    r"|seat|bumper|grille|fender|hood|tailgate|spoiler|dash pad"
    r"|door panel|barn door|dutch door|\bglass\b"
    r"|soft top|hardtop|targa|t-top"
    r"|\bamp\b|speaker|audio"
    r"|steering wheel"
    # Wheel SETS are generation-styled (design, offset, TPMS) even when the
    # bolt pattern carries over — a C4 Corvette sawblade is not a C6 wheel.
    # "wheels" (plural) avoids wheel bearings / flywheels / steering wheel
    # (already matched above).
    r"|wheels \(|wheels\b",
    re.IGNORECASE,
)
# ...but never electric/mechanical assemblies that happen to share those words
# (power liftgate MOTORS, seat track motors, sliding-door cables, etc.).
_GEN_MECH_EXCLUDE_RE = re.compile(r"motor|cable|regulator|compressor|actuator|pump", re.IGNORECASE)

# First model year of each new US-market generation (interior breakpoints only;
# the entry's own year_range provides the outer bounds). Models absent from
# this table are left untouched — single-generation entries, or long-tail
# entries whose spans were audited as acceptable.
GENERATION_BREAKS = {
    # --- Toyota / Lexus / Scion ---
    "4runner": [1990, 1996, 2003, 2010],
    "tacoma": [2005, 2016],
    "tundra": [2007, 2014, 2022],
    "sequoia": [2008, 2023],
    "highlander": [2008, 2014, 2020],
    "camry": [1997, 2002, 2007, 2012, 2018],
    "corolla": [1998, 2003, 2009, 2014, 2020],
    "sienna": [2004, 2011, 2021],
    "rav4": [2001, 2006, 2013, 2019],
    "land cruiser": [1998, 2008],          # 80 -> 100 -> 200 series
    "avalon": [2000, 2005, 2013, 2019],
    "matrix": [2009],
    "yaris": [2012, 2019],
    "solara": [2004],
    "celica": [1990, 1994, 2000],
    "mr2": [1990, 2000],
    "supra": [1982, 1986, 1993],
    "cressida": [1985, 1989],
    "toyota pickup": [1984, 1989],
    "gt86": [2017],                        # facelift swapped lights + head unit
    "rx": [2004, 2010, 2016, 2023],
    "gx": [2010],
    "lexus is": [2006, 2014, 2021],
    "lexus es": [1997, 2002, 2007, 2013, 2019],
    "lexus ls": [1995, 2001],
    "lexus gs": [1998, 2006, 2013],
    "scion xb": [2008],
    # --- Honda / Acura ---
    "civic": [1996, 2001, 2006, 2012, 2016, 2022],
    "accord": [1994, 1998, 2003, 2008, 2013, 2018, 2023],
    "cr-v": [2002, 2007, 2012, 2017, 2023],
    "odyssey": [2005, 2011, 2018],
    "pilot": [2009, 2016, 2023],
    "honda fit": [2009, 2015],
    "ridgeline": [2017],
    "prelude": [1992, 1997],
    "integra": [1994],
    "legend": [1991],
    "acura tl": [2004, 2009],
    "acura tsx": [2009],
    "acura rl": [2005],
    "mdx": [2007, 2014, 2022],
    # --- Nissan / Infiniti ---
    "altima": [2002, 2007, 2013, 2019],
    "sentra": [2007, 2013, 2020],
    "sentra se-r": [1995, 2000],
    "maxima": [2000, 2004, 2009, 2016],
    "murano": [2009, 2015],
    "rogue": [2014, 2021],
    "versa": [2012, 2020],
    "frontier": [2005, 2022],
    "titan": [2017],
    "armada": [2017],
    "quest": [2004, 2011],
    "pathfinder": [2005, 2013, 2022],
    "240sx": [1995],
    "300zx": [1990],
    "nissan pickup": [1987],               # 720 -> D21 Hardbody
    "infiniti fx": [2009],
    "m35": [2006, 2011],
    "qx56": [2011, 2017],
    # --- Ford / Lincoln / Mercury ---
    "f-150": [1987, 1992, 1997, 2004, 2009, 2015, 2021],
    "f-250": [1999, 2008, 2017, 2023],
    "f-350": [1999, 2008, 2017, 2023],
    "ranger": [1993, 1998, 2019],
    "explorer": [1995, 2002, 2006, 2011, 2020],
    "expedition": [2003, 2007, 2018],
    "escape": [2008, 2013, 2020],
    "fusion": [2013],
    "focus": [2008, 2012],
    "taurus": [1992, 1996, 2000, 2008, 2010],
    "mustang": [1994, 1999, 2005, 2010, 2015],
    "crown victoria": [1998],
    "grand marquis": [1998],
    "town car": [1998, 2003],
    "bronco": [1978, 1980],
    "ford edge": [2015],
    "transit connect": [2014],
    "navigator": [2003, 2007, 2018],
    "mountaineer": [2002, 2006],
    "sable": [1996, 2000, 2008],
    "tribute": [2008],
    # --- GM ---
    "silverado": [2007, 2014, 2019],
    "sierra": [2007, 2014, 2019],
    "tahoe": [2000, 2007, 2015, 2021],
    "suburban": [2000, 2007, 2015, 2021],
    "yukon": [2000, 2007, 2015, 2021],
    "escalade": [2002, 2007, 2015, 2021],
    "equinox": [2010, 2018],
    "traverse": [2018],
    "acadia": [2017],
    "terrain": [2018],
    "enclave": [2018],
    "impala": [2006, 2014],
    "malibu": [2004, 2008, 2013, 2016],
    "cruze": [2016],
    "monte carlo": [1995, 2000],
    "trailblazer": [2021],                 # 02-09 SUV vs 21+ crossover revival
    "colorado": [2015, 2023],
    "avalanche": [2007],
    "astro": [1995],
    "safari": [1995],
    "express": [2003],
    "s10": [1994],
    "sonoma": [1994],
    "blazer": [1992, 1995],
    "jimmy": [1992, 1995],
    "c/k": [1988],                         # squarebody -> OBS
    "corvette": [1984, 1997, 2005],        # C3 -> C4 -> C5 -> C6
    "camaro": [1993, 2010, 2016],
    "firebird": [1993],
    "grand prix": [2004],
    "grand am": [1999],
    "lesabre": [2000],
    "lacrosse": [2010, 2017],
    "century": [1997],
    "regal": [1988, 1997, 2011, 2018],
    "deville": [2000, 2006],
    "srx": [2010],
    "cadillac cts": [2008, 2014],
    "cadillac sts": [1998, 2005],
    "vue": [2008],
    # --- Chrysler / Dodge / Jeep / Ram ---
    "ram": [2002, 2009, 2019],
    "ram 2500": [2003, 2010, 2019],
    "ram 3500": [2003, 2010, 2019],
    "dakota": [1997, 2005],
    "durango": [2004, 2011],
    "charger": [2011],
    "challenger": [2015],                  # facelift swapped the Uconnect unit
    "chrysler 300": [2011],
    "grand caravan": [2001, 2008],
    "town & country": [2008],
    "pacifica": [2017],                    # 04-08 crossover vs 17+ minivan
    "sebring": [2001, 2007],
    "neon": [2000],
    "liberty": [2008],
    "compass": [2017],
    "cherokee": [2002, 2014],              # XJ vs KL (no US Cherokee between)
    "grand cherokee": [1999, 2005, 2011, 2022],
    "wrangler": [1997, 2007, 2018],
    # --- Hyundai / Kia ---
    "sonata": [2006, 2011, 2015, 2020],
    "elantra": [2007, 2011, 2017, 2021],
    "santa fe": [2007, 2013, 2019],
    "tucson": [2010, 2016, 2022],
    "accent": [2006, 2012, 2018],
    "veloster": [2019],
    "tiburon": [2003],
    "optima": [2007, 2011, 2016],
    "sorento": [2011, 2016, 2021],
    "sportage": [2011, 2017, 2023],
    "sedona": [2006, 2015],
    "soul": [2014, 2020],
    "forte": [2014, 2019],
    "kia rio": [2006, 2012, 2018],
    "spectra": [2005],
    # --- Subaru ---
    "outback": [2005, 2010, 2015, 2020],
    "forester": [2003, 2009, 2014, 2019],
    "impreza": [2002, 2008, 2012, 2017, 2024],
    "legacy": [2000, 2005, 2010, 2015, 2020],
    "wrx": [2008, 2015, 2022],
    "brz": [2022],
    # --- Mazda / Mitsubishi ---
    "mazda3": [2010, 2014, 2019],
    "mazda6": [2009, 2014],
    "cx-5": [2017],
    "cx-9": [2016],
    "mx-5": [1999, 2006, 2016],            # NA -> NB -> NC -> ND
    "rx-7": [1986, 1993],
    "protege": [1995, 1999],
    "outlander": [2007, 2014, 2022],
    "lancer": [2008],
    "lancer evolution": [2008],            # Evo 8/9 -> Evo X
    "galant": [2004],
    "eclipse": [1995, 2000, 2006],
    # --- VW / Audi ---
    "jetta": [1993, 1999, 2006, 2011, 2019],
    "passat": [2006, 2012, 2020],
    "golf": [2006, 2010, 2015, 2022],
    "gti": [2006, 2010, 2015, 2022],
    "new beetle": [2012],
    "tiguan": [2018],
    "audi a3": [2015, 2022],
    "audi s3": [2022],
    "audi a4": [2002, 2009, 2017],
    "audi s4": [2010, 2018],
    "audi a5": [2018],
    "audi s5": [2018],
    "audi a6": [2005, 2012, 2019],
    "audi s6": [2012, 2020],
    "audi a7": [2019],
    "audi s7": [2020],
    "audi a8": [2011, 2019],
    "audi s8": [2013, 2020],
    "audi rs5": [2018],
    "audi rs7": [2021],
    "audi q3": [2019],
    "audi q5": [2018],
    "audi sq5": [2018],
    "audi q7": [2017],
    "audi tt": [2008, 2016],
    # --- BMW ---
    "bmw 1": [2014],                       # US 1-series ended 2013 (2-series after)
    "bmw 3": [1999, 2006, 2012, 2019],     # E36/E46/E90/F30/G20
    "bmw 4": [2021],
    "bmw 5": [2004, 2011, 2017, 2024],     # E39/E60/F10/G30/G60
    "bmw 6": [2012],
    "bmw 7": [2009, 2016, 2023],
    "bmw m3": [2008, 2015, 2021],
    "bmw m5": [2006, 2012, 2018],
    "x1": [2016, 2023],
    "x3": [2011, 2018],
    "x4": [2019],
    "x5": [2007, 2014, 2019],
    "x6": [2015, 2020],
    "z4": [2009, 2019],
    "mini cooper": [2007],
    # --- Mercedes / Volvo / other Euro ---
    "c-class": [2001, 2008, 2015, 2022],
    "e-class": [2003, 2010, 2017, 2024],
    "m-class": [2006, 2012],
    "benz 300": [1986],                    # W123 -> W124
    "volvo s60": [2011, 2019],
    "volvo s80": [2007],
    "xc90": [2016],
    "xc70": [2008],
    "9-3": [2003],
    "discovery": [1999],
    "range rover": [2003, 2013],
    "cayenne": [2011, 2019],
    "trooper": [1992],
    "sidekick": [1996],
    "tracker": [1999],
    "rodeo": [1998],
    "scion tc": [2011],
}


def _apply_generation_bounds() -> None:
    """Split interchange-sensitive parts so no fits badge spans a generation.

    For every entry with known generation breakpoints, any sensitive part
    whose effective year span (entry year_range narrowed by its own
    yr_min/yr_max) crosses a breakpoint is replaced by one copy per
    generation segment, each bounded with yr_min/yr_max. All other fields
    (price band, rarity, cost, trim/option/manual/drive gates) carry over.
    """
    seen: set[int] = set()
    for key, e in list(UNOBTANIUM_DB.items()):
        if id(e) in seen:
            continue  # feed-spelling alias of an entry already processed
        seen.add(id(e))
        # Generation-split entries are keyed "<base> <lo>-<hi>".
        base = re.sub(r" \d{4}-\d{4}$", "", key)
        breaks = GENERATION_BREAKS.get(base)
        if not breaks:
            continue
        lo, hi = e["year_range"]
        new_parts: list[dict] = []
        for p in e["top_parts"]:
            plo = max(lo, p.get("yr_min", lo))
            phi = min(hi, p.get("yr_max", hi))
            name = p["name"]
            if (plo > phi or not _GEN_SENSITIVE_RE.search(name)
                    or _GEN_MECH_EXCLUDE_RE.search(name)):
                new_parts.append(p)
                continue
            cuts = [b for b in breaks if plo < b <= phi]
            if not cuts:
                new_parts.append(p)
                continue
            for seg_lo, seg_hi_excl in zip([plo] + cuts, cuts + [phi + 1]):
                q = dict(p)
                q["yr_min"], q["yr_max"] = seg_lo, seg_hi_excl - 1
                new_parts.append(q)
        e["top_parts"] = new_parts


_apply_generation_bounds()


def _merge_parts_overlay() -> None:
    """Merge scraper/parts_overlay.json into UNOBTANIUM_DB (append-only).

    The overlay is the self-growing half of the knowledge base: owner tips and
    the weekly research_parts.py run land there instead of editing this file.
    Matching mirrors match_vehicle(): an overlay entry applies to every DB row
    with the same make whose keyword set contains one of the entry's match
    terms. Generation-split rows all receive the part — each part's own
    yr_min/yr_max plus the row's year_range intersection keeps display honest.
    Match terms with no existing row create a new row (no gen-splitting; the
    part-level year gates do that work). Malformed overlay content is skipped,
    never fatal — a bad auto-research commit must not take down the scan.
    """
    path = Path(__file__).resolve().parent / "parts_overlay.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"[overlay] parts_overlay.json unreadable, skipping: {exc}")
        return
    allowed = ("name", "rarity", "low", "high", "cost", "yr_min", "yr_max", "trim", "option")
    for ent in data.get("entries", []):
        make = (ent.get("make") or "").strip()
        terms = [str(t).lower().strip() for t in (ent.get("match") or []) if str(t).strip()]
        clean = []
        for p in ent.get("parts") or []:
            try:
                name = str(p["name"]).strip()
                low, high = int(p["low"]), int(p["high"])
            except (KeyError, TypeError, ValueError):
                continue
            if not name or not (0 < low <= high):
                continue
            q = {k: p[k] for k in allowed if k in p}
            q["name"], q["low"], q["high"] = name, low, high
            q.setdefault("rarity", "Rare")
            q.setdefault("cost", 10)
            clean.append(q)
        if not (make and terms and clean):
            continue
        seen_ids: set[int] = set()
        hit = False
        for key, info in UNOBTANIUM_DB.items():
            if id(info) in seen_ids:
                continue
            seen_ids.add(id(info))
            if (info.get("make") or "").lower() != make.lower():
                continue
            kws = [str(k).lower() for k in (info.get("match") or (key,))]
            if not any(t in kws for t in terms):
                continue
            hit = True
            have = {pp["name"].lower() for pp in info["top_parts"]}
            info["top_parts"].extend(pp for pp in clean if pp["name"].lower() not in have)
        if not hit:
            new_key = terms[0]
            if new_key in UNOBTANIUM_DB:
                continue  # keyword collision with another make — leave alone
            yr = ent.get("year_range") or [1990, 2026]
            UNOBTANIUM_DB[new_key] = {
                "display": ent.get("display") or f"{make} {terms[0].title()}",
                "make": make,
                "match": terms,
                "year_range": (int(yr[0]), int(yr[1])),
                "top_parts": clean,
            }


_merge_parts_overlay()


# Gate-token regexes (trim/drive/transmission gates), compiled once per token.
# Unlike model keywords (where "rx" must still hit "RX350"), gate tokens match
# only as whole words: trim "st" hits "Fiesta ST" but never the inside of
# "Fiesta", and "n" hits "Elantra N Line" but never "Elantra". This is the
# word-boundary fix for the substring trim-matching bug — substring gates
# silently VIN-confirmed trim parts on every car of the model.
_GATE_RE: dict[str, re.Pattern] = {}


def _gate_pattern(tok: str) -> re.Pattern:
    pat = _GATE_RE.get(tok)
    if pat is None:
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(tok) + r"(?![a-z0-9])")
        _GATE_RE[tok] = pat
    return pat


def _gate_hit(tokens, text: str) -> bool:
    """True when any gate token appears as a whole word in text.

    The single chokepoint for trim/drive/manual gate matching — match_vehicle
    and lint_gate_tokens() both route through here, so a regression back to
    substring matching trips the lint immediately."""
    return any(_gate_pattern(t).search(text) for t in tokens)


def lint_gate_tokens() -> list[str]:
    """DB lint: no trim/drive gate token may 'confirm' itself from the bare
    model name.  The substring-matching bug this guards against: trim "st"
    matched inside "fiesta", so every Fiesta shipped VIN-confirmed ST Recaros.

    Routes through the same _gate_hit() used by match_vehicle(), so a
    regression back to substring matching fails this lint instantly.  Tokens
    that are a whole WORD of the entry's own keyword ("se-r" in "sentra se-r")
    are intended self-matches — that model name IS the trim — and are skipped.
    Returns a list of problem strings; empty means clean."""
    problems: list[str] = []
    seen: set[int] = set()
    for key, info in UNOBTANIUM_DB.items():
        if id(info) in seen:
            continue
        seen.add(id(info))
        kws = [str(x).lower() for x in (info.get("match") or (key,))]
        for p in info["top_parts"]:
            tokens = [str(t).lower() for t in p.get("trim", [])]
            tokens += [str(t).lower() for t in p.get("drive", [])]
            for t in tokens:
                if not t.strip():
                    problems.append(f"{key}: empty gate token on {p['name']!r}")
                    continue
                for kw in kws:
                    # Whole-word membership = keyword deliberately names the
                    # trim; checked WITHOUT regex so it can't mask a matching
                    # regression below.
                    if t in re.split(r"[^a-z0-9-]+", kw):
                        continue
                    haystack = f"{(info.get('make') or '').lower()} {kw}"
                    if _gate_hit([t], haystack):
                        problems.append(
                            f"{key}: gate token {t!r} self-triggers on bare "
                            f"model listing {haystack!r} ({p['name']})")
    return problems


# Fail fast at import: a self-triggering gate silently confirms trim parts on
# every car of that model — worse than crashing any tool that loads the DB.
_gate_problems = lint_gate_tokens()
if _gate_problems:
    raise ValueError(
        "UNOBTANIUM_DB gate-token lint failed:\n  " + "\n  ".join(_gate_problems))


# ---------------------------------------------------------------------------
# PLATFORM FAMILIES — hand-curated interchange groups.
#
# Badge-engineered twins and platform-mates share physical units: a Sierra
# tailgate IS a Silverado tailgate, a Commander transfer-case motor IS a WK
# Grand Cherokee motor.  Each family below encodes a small set of *verified*
# shared parts (forum/part-number sourced — citations in the curation notes of
# the interchange PR).  House rule: under-claim.  Every group carries a terse
# caveat, and anything gated by trim/drive is never copied to a sibling
# without an explicit copy_gates flag.
#
# Schema per family:
#   display  — family name (report/debug only, not shipped)
#   members  — {UNOBTANIUM_DB key: short display label used in provenance}
#   shared   — list of groups:
#       part    — canonical row name
#       names   — optional {member key: row name} when a twin spells the row
#                 differently ("Autoride Rear Air Shocks" vs
#                 "AutoRide Rear Shocks (pair)")
#       members — {member key: (yr_lo, yr_hi)} interchange window per member
#       copy_to — member keys that DON'T have the row yet: the engine copies
#                 the canonical row (with the member's window) onto them.
#                 Members not in copy_to MUST already carry the row — the
#                 lint errors either way, so the data stays self-auditing.
#       note    — honesty caveat appended to the provenance string (keep
#                 terse: it ships in the payload per part-set)
#       copy_gates — allow copying a trim/drive-gated row (default: refuse)
#       donor   — one-way swap provenance ("Integra arms bolt into 92-00
#                 Civics"). The note ships verbatim as the row's sharedWith;
#                 no member labels, no copies, single-member groups allowed.
#                 Use when the swap TARGET isn't the car carrying the part —
#                 a Civic never carries Integra trailing arms, so a two-way
#                 group would lie.
#
# _apply_platform_families() attaches p["sharedWith"] = "Label 2007–13 ·
# Label 2003–09 — caveat" to each member's row (each member keeps its OWN
# pricing) and runs at import, right after this table.  match_vehicle()
# forwards sharedWith automatically via its {**p} enrichment.

PLATFORM_FAMILIES: dict[str, dict] = {
    # ------------------------------------------------------------------ GM
    "gmt800-truck": {
        "display": "GM full-size trucks (GMT800)",
        "members": {"silverado 1999-2006": "Silverado",
                    "sierra 1999-2006": "Sierra"},
        "shared": [
            {"part": "Tailgate (straight)",
             "members": {"silverado 1999-2006": (1999, 2006),
                         "sierra 1999-2006": (1999, 2006)},
             "note": "same fleetside box incl. 2007 Classic; Avalanche differs"},
            {"part": "Tow Mirrors (manual, pair)",
             "members": {"silverado 1999-2006": (1999, 2006),
                         "sierra 1999-2006": (1999, 2006)},
             "note": "manual tow mirrors only; 03+ power versions differ"},
        ],
    },
    "gmt900-truck": {
        "display": "GM full-size trucks (GMT900)",
        "members": {"silverado 2007-2013": "Silverado",
                    "sierra 2007-2013": "Sierra"},
        "shared": [
            {"part": "Power-Fold Tow Mirrors (pair)",
             "names": {"sierra 2007-2013": "Power Fold Tow Mirrors (pair)"},
             "members": {"silverado 2007-2013": (2007, 2013),
                         "sierra 2007-2013": (2007, 2013)},
             "note": "new-body 07+ only — 2007 Classic uses GMT800 mirrors"},
            {"part": "Tailgate (straight)",
             "members": {"silverado 2007-2013": (2007, 2013),
                         "sierra 2007-2013": (2007, 2013)},
             "copy_to": ["sierra 2007-2013"],
             "note": "Chevy/GMC share the bed; camera/step tailgates differ"},
        ],
    },
    "gmt800-suv": {
        "display": "GM full-size SUVs (GMT800, short wheelbase)",
        "members": {"tahoe 1995-2006": "Tahoe",
                    "yukon": "Yukon",
                    "escalade": "Escalade"},
        "shared": [
            {"part": "3rd Row Seat",
             "names": {"yukon": "3rd Row Seat (complete)"},
             "members": {"tahoe 1995-2006": (2000, 2006),
                         "yukon": (2000, 2006),
                         "escalade": (2002, 2006)},
             "note": "SWB seats only — Suburban/Yukon XL differ; match color"},
            {"part": "AutoRide Rear Shocks (pair)",
             "names": {"yukon": "Autoride Rear Air Shocks"},
             "members": {"tahoe 1995-2006": (2000, 2006),
                         "yukon": (2000, 2006)},
             "note": "RPO Z55 Autoride; verify connector style"},
        ],
    },
    "gmt900-suv": {
        "display": "GM full-size SUVs (GMT900, short wheelbase)",
        "members": {"tahoe 2007-2014": "Tahoe",
                    "yukon": "Yukon",
                    "escalade": "Escalade"},
        "shared": [
            {"part": "3rd Row Seat",
             "names": {"yukon": "3rd Row Seat (complete)"},
             "members": {"tahoe 2007-2014": (2007, 2014),
                         "yukon": (2007, 2014),
                         "escalade": (2007, 2014)},
             "note": "SWB seats; manual vs power-fold NOT interchangeable"},
            {"part": "AutoRide Rear Shocks (pair)",
             "names": {"yukon": "Autoride Rear Air Shocks"},
             "members": {"tahoe 2007-2014": (2007, 2014),
                         "yukon": (2007, 2014)},
             "note": "RPO Z55 Autoride; verify connector style"},
        ],
    },
    "k2xx-suv": {
        "display": "GM full-size SUVs (K2XX, short wheelbase)",
        "members": {"tahoe 2015-2024": "Tahoe",
                    "yukon": "Yukon",
                    "escalade": "Escalade"},
        "shared": [
            {"part": "3rd Row Seat",
             "names": {"yukon": "3rd Row Seat (complete)"},
             "members": {"tahoe 2015-2024": (2015, 2020),
                         "yukon": (2015, 2020),
                         "escalade": (2015, 2020)},
             "note": "K2XX 15–20 only (21+ T1XX differs); Suburban/XL/ESV differ"},
            {"part": "Power Liftgate Motor",
             "members": {"tahoe 2015-2024": (2015, 2020),
                         "yukon": (2015, 2020)},
             "note": "K2XX 15–20 gate motor; 21+ T1XX differs"},
        ],
    },
    "lambda": {
        "display": "GM Lambda crossovers (1st gen)",
        "members": {"traverse": "Traverse",
                    "acadia": "Acadia",
                    "enclave": "Enclave"},
        "shared": [
            {"part": "3rd Row Seat",
             "members": {"traverse": (2009, 2017),
                         "acadia": (2007, 2016),
                         "enclave": (2008, 2017)},
             "note": "Lambda platform; manual vs power-fold NOT interchangeable"},
            {"part": "Power Liftgate Motor",
             "members": {"traverse": (2009, 2017),
                         "acadia": (2007, 2016),
                         "enclave": (2008, 2017)},
             "note": "1st-gen Lambda; verify connector"},
        ],
    },
    "s10-sonoma": {
        "display": "GM compact trucks (S10/Sonoma)",
        "members": {"s10": "S10", "sonoma": "Sonoma"},
        "shared": [
            {"part": "Tailgate (straight)",
             "members": {"s10": (1982, 1993), "sonoma": (1991, 1993)},
             "note": "1st-gen beds identical Chevy/GMC"},
            {"part": "Tailgate (straight)",
             "members": {"s10": (1994, 2004), "sonoma": (1994, 2004)},
             "note": "2nd-gen beds identical Chevy/GMC"},
        ],
    },
    # ---------------------------------------------------------------- Ford
    "panther": {
        "display": "Ford Panther platform",
        "members": {"crown victoria": "Crown Vic",
                    "grand marquis": "Grand Marquis",
                    "town car": "Town Car"},
        "shared": [
            {"part": "Rear Air Springs / Watts Link Parts",
             "names": {"town car": "Rear Air Springs + Compressor"},
             "members": {"crown victoria": (1992, 2011),
                         "grand marquis": (1992, 2011),
                         "town car": (1992, 2011)},
             "copy_to": ["grand marquis"],
             "note": "Panther rear air springs interchange; check bag age"},
        ],
    },
    "ford-superduty": {
        "display": "Ford Super Duty",
        "members": {"f-250": "F-250", "f-350": "F-350",
                    "excursion": "Excursion"},
        "shared": [
            {"part": "7.3L Powerstroke Parts (turbo, HPOP — verify engine)",
             "names": {"excursion": "7.3L Powerstroke Parts (verify engine)"},
             "members": {"f-250": (1994, 2003), "f-350": (1994, 2003),
                         "excursion": (2000, 2003)},
             "note": "same 7.3 PSD; turbo/HPOP are year-specific — verify"},
            {"part": "Power Fold Tow Mirrors (pair)",
             "members": {"f-250": (2008, 2016), "f-350": (2008, 2016)},
             "note": "Super Duty mirrors; match power/heat/signal options"},
            {"part": "Tailgate (w/ step)",
             "members": {"f-250": (2008, 2016), "f-350": (2008, 2016)},
             "copy_to": ["f-350"],
             "note": "F-250/F-350 share the box; step/camera options vary"},
        ],
    },
    "explorer-mountaineer": {
        "display": "Ford Explorer / Mercury Mountaineer",
        "members": {"explorer 2002-2010": "Explorer",
                    "mountaineer": "Mountaineer"},
        "shared": [
            {"part": "3rd Row Seat",
             "members": {"explorer 2002-2010": (2002, 2005),
                         "mountaineer": (2002, 2005)},
             "note": "U152 twins, 02–05 gen; match color"},
            {"part": "3rd Row Seat",
             "members": {"explorer 2002-2010": (2006, 2010),
                         "mountaineer": (2006, 2010)},
             "note": "U251 twins, 06–10 gen; match color"},
        ],
    },
    "escape-cd2": {
        "display": "Ford Escape / Mazda Tribute / Mercury Mariner",
        "members": {"escape": "Escape", "tribute": "Tribute",
                    "mariner": "Mariner"},
        "shared": [
            {"part": "Side Mirrors (power, pair)",
             "members": {"escape": (2001, 2011), "tribute": (2001, 2011),
                         "mariner": (2005, 2011)},
             "copy_to": ["tribute", "mariner"],
             "note": "CD2 triplets share doors; match heated/signal type"},
        ],
    },
    "f150-expedition": {
        "display": "Ford F-150 / Expedition (PN96 front end)",
        "members": {"f-150 1997-2003": "F-150",
                    "expedition": "Expedition"},
        "shared": [
            {"part": "Headlights (clear, non-hazed)",
             "members": {"f-150 1997-2003": (1997, 2002),
                         "expedition": (1997, 2002)},
             "copy_to": ["expedition"],
             "note": "same front clip 97–02; 03+ Expedition differs"},
        ],
    },
    # -------------------------------------------------------------- Mopar
    "mopar-lx": {
        "display": "Mopar LX/LD platform",
        "members": {"charger": "Charger", "chrysler 300": "300",
                    "challenger": "Challenger"},
        "shared": [
            {"part": 'Uconnect 8.4" Touchscreen',
             "names": {"chrysler 300": "Uconnect 8.4 Touchscreen"},
             "members": {"charger": (2011, 2014), "chrysler 300": (2011, 2014),
                         "challenger": (2011, 2014)},
             "note": "RE2/RB5 swap across LX 11–14; dealer PIN + your bezel; 15+ differs"},
            {"part": "SRT / Scat Brembo Calipers (set)",
             "names": {"challenger": "SRT Brembo Calipers (set)"},
             "members": {"charger": (2006, 2024), "challenger": (2008, 2024)},
             "note": "verify 4- vs 6-piston and rotor size by year"},
        ],
    },
    "jeep-wk-xk": {
        "display": "Jeep WK Grand Cherokee / XK Commander",
        "members": {"grand cherokee 2005-2010": "Grand Cherokee",
                    "commander": "Commander"},
        "shared": [
            {"part": "Transfer Case Shift Motor",
             "members": {"grand cherokee 2005-2010": (2005, 2010),
                         "commander": (2006, 2010)},
             "copy_to": ["commander"],
             "note": "WK/XK shared driveline; verify NV140 vs NV245 case"},
        ],
    },
    "chrysler-rt-vans": {
        "display": "Chrysler RT minivans",
        "members": {"grand caravan": "Grand Caravan",
                    "town & country": "Town & Country"},
        "shared": [
            {"part": "Stow-N-Go 2nd Row Seat (each)",
             "members": {"grand caravan": (2005, 2007),
                         "town & country": (2005, 2007)},
             "note": "05–07 gen only — won't fit 08+; match color"},
            {"part": "Stow-N-Go 2nd Row Seat (each)",
             "members": {"grand caravan": (2008, 2016),
                         "town & country": (2008, 2016)},
             "note": "08+ gen only — won't fit 05–07; match color"},
            {"part": "Power Sliding Door Motor",
             "members": {"grand caravan": (2008, 2016),
                         "town & country": (2008, 2016)},
             "note": "RT vans share door hardware"},
            {"part": "Uconnect Touchscreen Head Unit",
             "members": {"grand caravan": (2011, 2016),
                         "town & country": (2011, 2016)},
             "note": "match RB/RE unit type; dealer PIN to activate"},
        ],
    },
    # ------------------------------------------------------------- Toyota
    "toyota-elocker": {
        "display": "Toyota 8-inch rear e-locker",
        "members": {"4runner 1996-2002": "4Runner",
                    "tacoma 1995-2004": "Tacoma",
                    "tacoma 2005-2015": "Tacoma"},
        "shared": [
            {"part": "Rear E-Locker Actuator Motor",
             "members": {"4runner 1996-2002": (1996, 2002),
                         "tacoma 1995-2004": (1996, 2004),
                         "tacoma 2005-2015": (2005, 2015)},
             "copy_to": ["tacoma 1995-2004"],
             "note": "8\" diff actuators (SAT-008/009); plug & vent routing differ — verify"},
        ],
    },
    "tundra-sequoia": {
        "display": "Toyota Tundra / Sequoia (1st gen)",
        "members": {"tundra": "Tundra", "sequoia": "Sequoia"},
        "shared": [
            {"part": "JBL Speakers + Amp",
             "members": {"tundra": (2000, 2006), "sequoia": (2001, 2007)},
             "copy_to": ["sequoia"],
             "note": "1st-gen JBL option; verify amp P/N and connectors"},
        ],
    },
    # -------------------------------------------------------------- Honda
    "honda-eg-dc": {
        "display": "Honda Civic / Acura Integra seat swap",
        "members": {"civic 1992-1995": "Civic",
                    "civic 1996-2000": "Civic",
                    "integra": "Integra"},
        "shared": [
            {"part": "OEM Seats (pair, unshredded)",
             "names": {"civic 1992-1995": "Si Seats (pair)",
                       "civic 1996-2000": "Si/Type R Seats (pair)"},
             "members": {"integra": (1994, 2001),
                         "civic 1992-1995": (1992, 1995),
                         "civic 1996-2000": (1996, 2000)},
             "note": "rails bolt up across EG/EK/DC — seats differ by trim, mounts swap"},
        ],
    },
    # ------------------------------------------------------------- Subaru
    "subaru-ej-turbo": {
        "display": "Subaru EJ turbo (TMIC)",
        "members": {"wrx": "WRX", "forester": "Forester XT",
                    "baja": "Baja Turbo", "impreza": "Impreza WRX"},
        "shared": [
            {"part": "Turbo Intercooler (TMIC)",
             "names": {"forester": "XT Turbo Intercooler + Piping",
                       "baja": "Turbo Parts (04-06 Baja Turbo)",
                       "impreza": "WRX Top-Mount Intercooler"},
             "members": {"wrx": (2002, 2014), "forester": (2004, 2013),
                         "baja": (2004, 2006), "impreza": (2002, 2014)},
             "note": "06–08 FXT = 06–07 WRX TMIC (same P/N); earlier BPV mount differs; Baja needs WRX brackets"},
        ],
    },
    "subaru-swap-donors": {
        "display": "Subaru swap donors",
        "members": {"impreza": "Impreza", "forester": "Forester"},
        "shared": [
            # NASIOC seat-swap threads: GD rails interchange 02-07; the
            # 08+ (GR/GH) seat-base bracket does NOT fit 02-07 cars.
            {"donor": True, "part": "WRX / STI Front Seats (pair)",
             "members": {"impreza": (2002, 2007)},
             "note": "02–07 rails swap across Impreza; bolt into 03–08 Forester (keep Forester base for height); 08+ rails differ — check airbag plugs"},
            # R160 diff swap culture: ratio must match the transmission.
            {"donor": True, "part": "Rear Viscous LSD Diff",
             "members": {"forester": (1998, 2008)},
             "note": "R160 LSD swaps into Impreza/Legacy rears — MATCH final-drive ratio (4.11 vs 4.44) to the trans"},
        ],
    },
    "legacy-outback": {
        "display": "Subaru Legacy / Outback / Baja",
        "members": {"legacy": "Legacy", "outback": "Outback",
                    "baja": "Baja"},
        "shared": [
            # 84001AE15A/14A housing: Outback + Baja share the Legacy GT
            # lamp; the base-Legacy housing (84001AE13A) differs.
            {"part": "Headlights (clear, non-hazed)",
             "members": {"legacy": (2000, 2004), "outback": (2000, 2004),
                         "baja": (2003, 2006)},
             "copy_to": ["outback", "baja"],
             "note": "Legacy GT housing only (84001AE14A/15A) — base Legacy lamp differs; verify P/N"},
            {"part": "Headlights (clear, non-hazed)",
             "members": {"legacy": (2005, 2007), "outback": (2005, 2007)},
             "copy_to": ["outback"],
             "note": "05–07 halogen housings shared — HID and the 08–09 facelift differ"},
        ],
    },
    # --------------------------------------------------------- Toyota deep
    "toyota-1mz-alt": {
        "display": "Toyota/Lexus 1MZ V6 alternator",
        "members": {"camry": "Camry V6", "avalon": "Avalon",
                    "solara": "Solara V6", "sienna": "Sienna",
                    "highlander": "Highlander V6", "lexus es": "ES300",
                    "rx": "RX300"},
        "shared": [
            # Denso 101211-7440/7450 = Toyota 27060-20230 / 27060-0A070,
            # 100A 6-groove, shared across the 1MZ-FE family (ToyotaNation
            # + Denso catalog). 130A tow-package variant differs; 04+ 3MZ
            # uses a different harness plug.
            # Windows start at the 97+ Denso unit — Hollander spot-check
            # (601-58691) crosses Camry V6 97-01 = ES300 97-01; earlier
            # 1MZ cars used a different alternator.
            {"part": "Alternator (spin-test at yard)",
             "members": {"camry": (1997, 2003), "avalon": (1997, 2003),
                         "solara": (1999, 2003), "sienna": (1998, 2003),
                         "highlander": (2001, 2003),
                         "lexus es": (1997, 2003), "rx": (1999, 2003)},
             # sienna gets its alternator row from the consensus-evergreen
             # expansion (6e37bcf) — it takes provenance, not a copy.
             "copy_to": ["avalon", "solara", "highlander",
                         "lexus es", "rx"],
             "note": "V6 (1MZ) Denso unit only — 4-cyl differs; match plug & amps (100A vs 130A tow pkg); 04+ 3MZ plug differs"},
        ],
    },
    "toyota-22re": {
        "display": "Toyota Pickup / 4Runner (22RE era)",
        "members": {"toyota pickup": "Toyota Pickup",
                    "4runner 1984-1995": "4Runner"},
        "shared": [
            # Same 22RE engine in both; the 3.0 V6 (3VZ-E) AFM differs
            # (22RE Performance / YotaTech).
            {"part": "22RE AFM (Air Flow Meter)",
             "names": {"4runner 1984-1995": "AFM (Air Flow Meter, 22RE/3.0)"},
             "members": {"toyota pickup": (1985, 1995),
                         "4runner 1984-1995": (1985, 1995)},
             "note": "same 22RE AFM across truck & 4Runner — 3.0 V6 AFM differs, match engine"},
            {"part": "22RE EFI Intake/Throttle Body",
             "members": {"toyota pickup": (1985, 1995),
                         "4runner 1984-1995": (1985, 1995)},
             "copy_to": ["4runner 1984-1995"],
             "note": "same 22RE EFI across truck & 4Runner — 4-cyl only"},
            # ToyotaNation: 84-88 truck = 84-89 4Runner dash era; 89-95
            # truck = 90-95 4Runner. Two eras that don't cross.
            {"part": "Climate Control Panel (works, knobs intact)",
             "members": {"toyota pickup": (1984, 1995),
                         "4runner 1984-1995": (1984, 1995)},
             "note": "84–88 truck = 84–89 4Runner, 89–95 truck = 90–95 4Runner — two eras, don't mix"},
            {"part": "Gauge Cluster w/ Tach",
             "members": {"toyota pickup": (1984, 1995),
                         "4runner 1984-1995": (1984, 1995)},
             "copy_to": ["4runner 1984-1995"],
             "note": "same clusters by era (84–88 / 89–95); cable vs electronic speedo (~'92) and senders must match"},
            {"part": "Manual Locking Hubs (pair)",
             "names": {"toyota pickup": "Manual Locking Hubs (pair)"},
             "members": {"4runner 1984-1995": (1984, 1995),
                         "toyota pickup": (1984, 1995)},
             "copy_to": ["toyota pickup"], "copy_gates": True,
             "note": "Aisin hubs interchange across 79–95 Toyota 4x4s — match spline count"},
        ],
    },
    "matrix-vibe": {
        "display": "Toyota Matrix / Pontiac Vibe (NUMMI twins)",
        "members": {"matrix": "Matrix", "vibe": "Vibe"},
        "shared": [
            # Jointly built twins: mechanically identical, different
            # sheet metal/trim/HVAC (Wikipedia, GenVibe).
            {"part": "Rear Cargo Rail System",
             "members": {"vibe": (2003, 2008), "matrix": (2003, 2008)},
             "copy_to": ["matrix"],
             "note": "NUMMI twins — mechanicals identical; nose/tail styling & HVAC trim differ"},
            {"donor": True, "part": "GT (2ZZ) Engine Accessories",
             "members": {"vibe": (2003, 2006)},
             "note": "2ZZ-GE shared with Celica GT-S, Matrix XRS & Corolla XRS — manifolds/mounts differ by car"},
        ],
    },
    "toyota-swap-donors": {
        "display": "Toyota swap donors",
        "members": {"land cruiser": "Land Cruiser", "prius": "Prius"},
        "shared": [
            # IH8MUD: LX470 is the 100-series twin; AHC standard on LX.
            {"donor": True, "part": "AHC Height Control Pump",
             "members": {"land cruiser": (1998, 2007)},
             "note": "100-series AHC = Lexus LX470 (standard on LX) — pump & globes interchange"},
            # IH8MUD: 80-series actuators retrofit into 100-series rears
            # with a connector splice + shaft-length mod.
            {"donor": True, "part": "Factory Locker Actuators",
             "members": {"land cruiser": (1990, 2007)},
             "note": "80↔100-series actuators retrofit (LX450/LX470 too) — plug & shaft length differ, easy mods"},
            # PriusChat: the 28 NiMH modules interchange across every
            # 04-15 pack; the cases do not.
            {"donor": True, "part": "Hybrid Battery Pack (complete)",
             "members": {"prius": (2004, 2009)},
             "note": "NiMH modules interchange across ALL 04–15 packs — swap all 28 into your case, match capacity; cases & Li-ion do NOT"},
            {"donor": True, "part": "Hybrid Battery Pack (complete)",
             "members": {"prius": (2010, 2015)},
             "note": "NiMH modules interchange across ALL 04–15 packs — swap all 28 into your case, match capacity; cases & Li-ion do NOT"},
            {"donor": True, "part": "Hybrid Battery Cells (bulk)",
             "members": {"prius": (2004, 2015)},
             "note": "NiMH modules interchange across ALL 04–15 packs — match capacity, never mix with Li-ion"},
        ],
    },
    # ---------------------------------------------------------- Honda deep
    "honda-swap-donors": {
        "display": "Honda/Acura swap donors",
        "members": {"integra": "Integra", "prelude": "Prelude",
                    "rsx": "RSX", "crx": "CRX", "acura tl": "TL"},
        "shared": [
            # Honda-Tech: trailing arms identical minus hub across
            # Integra 94-01 / Civic 92-00 / del Sol.
            {"donor": True,
             "part": "Rear Disc Brake Conversion Parts (trailing arms)",
             "members": {"integra": (1994, 2001)},
             "note": "bolt-in rear-disc swap for 92–00 Civic/del Sol — skip 5-lug Type R; grab prop valve & e-brake cables too"},
            {"donor": True,
             "part": "B18 Engine Accessories / Intake Manifold",
             "members": {"integra": (1994, 2001)},
             "note": "B-series swap staple for 88–00 Civic/CRX/del Sol — mounts & axles differ by chassis"},
            {"donor": True, "part": "H22 Intake / Accessories",
             "members": {"prelude": (1992, 2001)},
             "note": "H22 swaps into 90–97 Accord — use donor mounts & wiring"},
            {"donor": True, "part": "K20 Intake Manifold / Throttle Body",
             "members": {"rsx": (2002, 2006)},
             "note": "K-swap staple; RSX-S (K20A2) parts upgrade the EP3 Civic Si's K20A3"},
            {"donor": True, "part": "Si Seats / Sunroof / Glass Hatch",
             "members": {"crx": (1988, 1991)},
             "note": "EF-chassis seats bolt into 88–91 Civic"},
            # Honda-Tech: NOT a caliper-only bolt-on for TSX/Accord —
            # needs the complete TL-S knuckles + outer tie-rod ends.
            {"donor": True, "part": "Brembo Front Calipers (Type-S)",
             "members": {"acura tl": (2004, 2008)},
             "note": "popular TSX/Accord big-brake donor — take the complete TL-S knuckles + outer tie-rod ends; calipers alone don't bolt on"},
        ],
    },
    # ------------------------------------------------------ older favorites
    "jeep-yj-tj": {
        "display": "Jeep Wrangler YJ / TJ",
        "members": {"wrangler 1987-1995": "Wrangler YJ",
                    "wrangler 1996-2006": "Wrangler TJ"},
        "shared": [
            # Door openings identical 87-06; strikers differ (YJ pin vs
            # TJ hoop). Full doors & hardtops do NOT cross (JeepForum).
            {"part": "Half Doors (pair)",
             "members": {"wrangler 1987-1995": (1987, 1995),
                         "wrangler 1996-2006": (1997, 2006)},
             "note": "87–06 lower halves interchange; swap latch/striker (YJ pin vs TJ hoop); full doors & tops do NOT cross"},
        ],
    },
    "gm-classic-trucks": {
        "display": "GM square-body / OBS trucks",
        "members": {"blazer": "K5 Blazer", "jimmy": "Jimmy",
                    "c/k": "C/K", "k1500": "K1500"},
        "shared": [
            # CK5 forum: 76-91 half-cab tops interchange; 73-75 full
            # convertible tops do not; tailgates same 73-91.
            {"part": "K5 Removable Hardtop Parts",
             "names": {"jimmy": "Full-Size Hardtop/Tailgate Parts"},
             "members": {"blazer": (1976, 1991), "jimmy": (1976, 1991)},
             "note": "76–91 half-cab tops swap K5↔Jimmy; 73–75 full tops differ; tailgates same 73–91"},
            {"part": "Front Grille + Bezels",
             "names": {"c/k": "Front Grille + Bezels (chrome)"},
             "members": {"blazer": (1973, 1987), "c/k": (1973, 1987)},
             "note": "K5 shares the square-body truck front clip by facelift era — Chevy vs GMC grilles differ"},
            {"part": "Tailgate (straight)",
             "members": {"c/k": (1988, 1998), "k1500": (1988, 1998)},
             "note": "88–98 Fleetside tailgates interchange; Stepside & 99–00 'classic' differ"},
        ],
    },
    "gbody": {
        "display": "GM G-body",
        "members": {"monte carlo": "Monte Carlo", "cutlass": "Cutlass",
                    "regal": "Regal"},
        "shared": [
            {"part": "Dash Pad (uncracked, G-body)",
             "names": {"regal": "G-body Dash Pad (uncracked)"},
             "members": {"monte carlo": (1978, 1988),
                         "cutlass": (1978, 1988), "regal": (1978, 1987)},
             "note": "A/G-body pads interchange — match color & A/C vs non-A/C dash"},
            {"part": "G-body Trim + Emblems (78-88)",
             "names": {"cutlass": "G-body Trim + Emblems"},
             "members": {"monte carlo": (1978, 1988),
                         "cutlass": (1978, 1988)},
             "note": "shared brightwork; marque emblems & clips differ"},
        ],
    },
    "w-body-l67": {
        "display": "GM W-body L67",
        "members": {"grand prix": "Grand Prix GTP"},
        "shared": [
            # 3800Pro/ZZP: Gen-3 M90 shared 97-03 GTP / Regal GS /
            # Bonneville SSEi + 04-05 Impala SS / Monte SS; 04+ GTP is
            # the Gen-5 Series III; GXP is the V8.
            {"donor": True,
             "part": "GTP Supercharger Accessories (pulleys/brackets)",
             "members": {"grand prix": (1997, 2003)},
             "note": "Gen-3 M90/L67 bits also fit Regal GS, Bonneville SSEi & 04–05 Impala/Monte SS; 04+ GTP is Gen-5 — GXP is the V8"},
        ],
    },
    "s197-brembo": {
        "display": "Mustang S197 Brembo",
        "members": {"mustang 2005-2014": "Mustang"},
        "shared": [
            {"donor": True, "part": "GT Brembo Calipers (set)",
             "members": {"mustang 2005-2014": (2007, 2014)},
             "note": "GT500/track-pack Brembos bolt to any 05–14 Mustang spindle — pair with 14-in rotors; needs 18-in+ wheels"},
        ],
    },
    # ----------------------------------------------------------- VW/Audi
    "vw-mk7": {
        "display": "VW Golf MK7 family",
        "members": {"golf": "Golf/R", "gti": "GTI"},
        "shared": [
            {"part": "Discover Pro / MIB Touchscreen",
             "members": {"golf": (2015, 2021), "gti": (2015, 2021)},
             "note": "MK7 MIB2 units; component protection — needs coding to car"},
            {"part": "OEM LED Headlights (pair)",
             "members": {"golf": (2015, 2021), "gti": (2015, 2021)},
             "note": "MK7 Golf/GTI/R share housings; match halogen vs LED"},
        ],
    },
    "pl71": {
        "display": "VW/Porsche PL71 SUVs",
        "members": {"touareg": "Touareg", "cayenne": "Cayenne"},
        "shared": [
            {"part": "Air Suspension Compressor",
             "members": {"touareg": (2004, 2010), "cayenne": (2003, 2010)},
             "copy_to": ["cayenne"],
             "note": "shared WABCO unit (Q7 4L variant differs) — verify P/N, replace relay"},
        ],
    },
    "audi-b8": {
        "display": "Audi B8 platform MMI",
        "members": {"audi a4": "A4", "audi a5": "A5", "audi q5": "Q5"},
        "shared": [
            {"part": "MMI / MMI Touch / Screen Assembly",
             "names": {"audi a5": "MMI / Virtual Cockpit",
                       "audi q5": "MMI / MMI Touch + Screen"},
             "members": {"audi a4": (2009, 2016), "audi a5": (2013, 2016),
                         "audi q5": (2009, 2017)},
             "note": "B8 MMI 3G vs 3G+ must match — check P/N and nav version"},
        ],
    },
    # ---------------------------------------------------------------- BMW
    "bmw-e8x-e9x": {
        "display": "BMW E8x/E9x iDrive",
        "members": {"bmw 1": "1 Series", "bmw 3": "3 Series"},
        "shared": [
            {"part": "iDrive Head Unit (E90 CCC/CIC)",
             "names": {"bmw 1": "iDrive / Business Navigation"},
             "members": {"bmw 3": (2006, 2011), "bmw 1": (2008, 2013)},
             "note": "CCC vs CIC generations must match; coding to VIN required"},
        ],
    },
    # -------------------------------------------------------------- Nissan
    "titan-armada": {
        "display": "Nissan Titan / Armada (1st gen)",
        "members": {"titan": "Titan", "armada": "Armada"},
        "shared": [
            {"part": "Tow Mirrors (pair)",
             "members": {"titan": (2004, 2015), "armada": (2004, 2015)},
             "note": "shared cab/doors 04–15; match power/heat harness"},
        ],
    },
}


def _year_label(lo: int, hi: int) -> str:
    """'2007–13' — terse year span for provenance strings."""
    hi_s = str(hi)
    if str(lo)[:2] == hi_s[:2]:
        hi_s = hi_s[2:]
    return f"{lo}\u2013{hi_s}"


def _apply_platform_families() -> list[str]:
    """Attach sharedWith provenance to family rows; copy rows onto members
    listed in copy_to.  Returns problem strings (empty = clean).  Mutates
    UNOBTANIUM_DB in place, replacing touched part dicts with copies so a
    row shared between generation-split entries never leaks a sharedWith
    meant for one sibling onto another."""
    problems: list[str] = []
    for fam_id, fam in PLATFORM_FAMILIES.items():
        entries: dict[str, dict] = {}
        for key in fam["members"]:
            info = UNOBTANIUM_DB.get(key)
            if info is None:
                problems.append(f"{fam_id}: unknown member key {key!r}")
            else:
                entries[key] = info
        for grp in fam["shared"]:
            gmembers: dict[str, tuple] = grp["members"]
            copy_to = set(grp.get("copy_to", ()))
            donor = bool(grp.get("donor"))
            bad = [k for k in gmembers if k not in fam["members"]]
            bad += [k for k in copy_to if k not in gmembers]
            if donor and (copy_to or not grp.get("note")):
                problems.append(
                    f"{fam_id}: donor group {grp['part']!r} must have a note "
                    "and no copy_to")
                continue
            if bad or len(gmembers) < (1 if donor else 2):
                problems.append(
                    f"{fam_id}: group {grp['part']!r} bad member refs {bad}")
                continue
            if any(k not in entries for k in gmembers):
                continue  # unknown key already reported above

            def row_name(k: str) -> str:
                return grp.get("names", {}).get(k, grp["part"])

            # Locate each member's row: the name-matching row whose year
            # window overlaps the group window the most (gen-split entries
            # carry several same-named rows).
            rows: dict[str, dict | None] = {}
            canonical_key = None
            for k, (lo, hi) in gmembers.items():
                want = row_name(k).lower()
                best, best_ov = None, 0
                for p in entries[k]["top_parts"]:
                    if p["name"].lower() != want:
                        continue
                    plo = max(p.get("yr_min", lo), lo)
                    phi = min(p.get("yr_max", hi), hi)
                    ov = phi - plo + 1
                    if ov > best_ov:
                        best, best_ov = p, ov
                rows[k] = best
                if k in copy_to:
                    if best is not None:
                        problems.append(
                            f"{fam_id}: {k!r} already has {row_name(k)!r} — "
                            "drop it from copy_to")
                elif best is None:
                    problems.append(
                        f"{fam_id}: {k!r} missing row {row_name(k)!r} "
                        f"overlapping {gmembers[k]} (add to copy_to?)")
            canonical_key = next(
                (k for k in gmembers if k not in copy_to and rows[k]), None)
            if donor:
                # One-way provenance: the note ships verbatim, nothing is
                # copied, and every listed member must already carry the row
                # (missing rows were reported above).
                for k, (lo, hi) in gmembers.items():
                    row = rows[k]
                    if row is None:
                        continue
                    new = dict(row)
                    new["sharedWith"] = (
                        new["sharedWith"] + " \u00b7 " + grp["note"]
                        if new.get("sharedWith") else grp["note"])
                    old_sy = new.get("sharedYears")
                    new["sharedYears"] = (
                        (min(old_sy[0], lo), max(old_sy[1], hi)) if old_sy
                        else (lo, hi))
                    top = entries[k]["top_parts"]
                    top[top.index(row)] = new
                    rows[k] = new
                continue
            if canonical_key is None:
                problems.append(
                    f"{fam_id}: group {grp['part']!r} has no source row")
                continue
            canonical = rows[canonical_key]
            if copy_to and not grp.get("copy_gates") and (
                    canonical.get("trim") or canonical.get("drive")):
                problems.append(
                    f"{fam_id}: refusing to copy trim/drive-gated "
                    f"{grp['part']!r} (set copy_gates if intended)")
                continue

            for k, (lo, hi) in gmembers.items():
                others = [m for m in gmembers if m != k]
                label = " \u00b7 ".join(
                    f"{fam['members'][m]} {_year_label(*gmembers[m])}"
                    for m in others)
                shared_txt = label + (
                    f" \u2014 {grp['note']}" if grp.get("note") else "")
                row = rows[k]
                top = entries[k]["top_parts"]
                if row is None:  # copy_to member
                    row = dict(canonical)
                    row["yr_min"], row["yr_max"] = lo, hi
                    row["sharedWith"] = shared_txt
                    row["sharedYears"] = (lo, hi)
                    top.append(row)
                    continue
                # Replace with a copy: part dicts can be shared across
                # gen-split entries, so never mutate the original in place.
                new = dict(row)
                new["sharedWith"] = (
                    new["sharedWith"] + " \u00b7 " + shared_txt
                    if new.get("sharedWith") else shared_txt)
                # Widest window across this row's groups: match_vehicle drops
                # the provenance for vehicle years outside it.
                old_sy = new.get("sharedYears")
                new["sharedYears"] = (
                    (min(old_sy[0], lo), max(old_sy[1], hi)) if old_sy
                    else (lo, hi))
                top[top.index(row)] = new
                rows[k] = new
                if row is canonical:
                    canonical = new
    return problems


# Fail fast at import, same contract as the gate lint: a family referencing a
# missing row or silently copying a gated part is a data bug, not a runtime
# condition.
_family_problems = _apply_platform_families()
if _family_problems:
    raise ValueError(
        "PLATFORM_FAMILIES lint failed:\n  " + "\n  ".join(_family_problems))


# ===========================================================================
# TRIM PLATFORM GROUPS — performance trims share BODY parts with their
# platform siblings even when the engine is trim-unique. An E46 M3's window
# regulator is an E46 coupe regulator; its S54 engine interchanges with
# nothing else on a yard lot. Each family below maps a performance-trim
# model string (as the live feed spells it — audited 2026-10) onto its
# platform siblings for the body-part categories that genuinely carry over.
#
# House rule: under-claim. These are reasoned platform claims, NOT published
# part-number lists, so every category ships at tier "likely" with an honest
# caveat. Categories where the trim diverges (gauge clusters with unique
# faces/redlines, aero mirrors, trim-specific panels) are omitted on purpose
# — reasoning per family in scraper/interchange_research.md.
#
# Schema:
#   display       — label shown on donor rows
#   engine_note   — optional; shipped when the trim's ENGINE is unique and
#                   unpublished, so the engine-part search can explain itself
#                   instead of showing a bare "no data" (apps = trim_apps)
#   trim_apps     — (make, model, lo, hi) spans for the trim's feed strings
#   platform_apps — sibling spans (feed spellings, gen-windowed)
#   cats          — {category id: donor-row caveat}
#
# NOTE (model normalization): a parallel worker is canonicalizing feed model
# strings on main ("330I" -> "330i"). pf matching squashes case/punctuation,
# so these spellings survive that change, but re-check alias tuples against
# their canonical-forms test file at the next rebase onto main.
TRIM_PLATFORM_GROUPS: dict[str, dict] = {
    "bmw-e46-m3": {
        "display": "BMW E46 platform (M3)",
        "engine_note": ("The M3's S54 engine is M3-specific — engine parts "
                        "only interchange with other E46 M3s, and no "
                        "published application list covers the S54 yet."),
        "trim_apps": [("BMW", "M3", 2001, 2006)],
        "platform_apps": [
            ("BMW", "3 Series", 1999, 2006),
            ("BMW", "323i", 1999, 2000), ("BMW", "323ci", 2000, 2000),
            ("BMW", "325i", 2001, 2006), ("BMW", "325ci", 2001, 2006),
            ("BMW", "325xi", 2001, 2006),
            ("BMW", "328i", 1999, 2000), ("BMW", "328ci", 2000, 2000),
            ("BMW", "330i", 2001, 2006), ("BMW", "330ci", 2001, 2006),
            ("BMW", "330xi", 2001, 2006),
        ],
        "cats": {
            "window-regulator": "M3 is coupe/convertible — use Ci coupe/"
                                "convertible donors for door hardware; E46 "
                                "sedan/wagon front regulators differ",
            "window-switch": "switch packs are shared across the E46 range",
            "climate-control": "same IHKA climate panel across the E46 range",
            "headlights": "match body style AND facelift: coupe/convertible "
                          "housings (00-03 pre-LCI / 04-06 LCI) differ from "
                          "sedan; halogen vs xenon also differ",
            "tail-lights": "coupe/convertible lenses only, matched pre/post "
                           "facelift — sedan/wagon lenses differ",
        },
    },
    "bmw-e60-m5": {
        "display": "BMW E60 platform (M5)",
        "engine_note": ("The 2006-2010 M5's S85 V10 is M5-specific — engine "
                        "parts only interchange with other E60 M5s, and no "
                        "published application list covers the S85."),
        "trim_apps": [("BMW", "M5", 2006, 2010)],
        "platform_apps": [
            ("BMW", "5 Series", 2004, 2010),
            ("BMW", "525i", 2004, 2007), ("BMW", "525xi", 2006, 2007),
            ("BMW", "528i", 2008, 2010), ("BMW", "528xi", 2008, 2008),
            ("BMW", "530i", 2004, 2007), ("BMW", "530xi", 2006, 2007),
            ("BMW", "535i", 2008, 2010), ("BMW", "535xi", 2008, 2008),
            ("BMW", "545i", 2004, 2005), ("BMW", "550i", 2006, 2010),
        ],
        "cats": {
            "window-regulator": "same E60 sedan door shell across the range",
            "window-switch": "switch packs shared across the E60 range",
            "climate-control": "same panel; high/low IHKA versions — match "
                               "button layout",
            "headlights": "M5 ran adaptive xenon — match halogen/xenon/"
                          "adaptive type and pre/post-LCI (08+) housings",
            "tail-lights": "sedan lenses shared; match pre/post-LCI (08+)",
        },
    },
    "bmw-f10-m5": {
        "display": "BMW F10 platform (M5)",
        "engine_note": ("The 2011-2016 M5's S63 twin-turbo V8 is M-specific "
                        "— engine parts only interchange with other F10 M5s, "
                        "and no published application list covers it."),
        "trim_apps": [("BMW", "M5", 2011, 2016)],
        "platform_apps": [
            ("BMW", "5 Series", 2011, 2016),
            ("BMW", "528i", 2011, 2016), ("BMW", "528I Xdrive", 2011, 2016),
            ("BMW", "535i", 2011, 2015), ("BMW", "535I Xdrive", 2011, 2016),
            ("BMW", "550i", 2011, 2015), ("BMW", "550I Xdrive", 2012, 2014),
        ],
        "cats": {
            "window-regulator": "same F10 sedan door shell across the range "
                                "(5-Series GT is a different body — skip it)",
            "window-switch": "switch packs shared across the F10 range",
            "climate-control": "same panel across the F10 range",
        },
    },
    "cadillac-ctsv1": {
        "display": "Cadillac CTS platform (CTS-V gen 1)",
        "engine_note": ("The 2004-2007 CTS-V's LS6/LS2 V8 has no published "
                        "application rows in our catalog edition — engine "
                        "parts only interchange with other gen-1 CTS-Vs."),
        "trim_apps": [("Cadillac", "Cts-V", 2004, 2007)],
        "platform_apps": [("Cadillac", "CTS", 2003, 2007)],
        "cats": {
            "window-regulator": "same Sigma-platform door shell as the CTS",
            "window-switch": "switchgear shared with the 03-07 CTS",
            "climate-control": "same HVAC panel as the 03-07 CTS",
            "headlights": "same housings as the 03-07 CTS",
            "tail-lights": "same lenses as the 03-07 CTS",
        },
    },
    "mopar-srt4-body": {
        "display": "Dodge Neon platform (SRT-4)",
        "trim_apps": [("Dodge", "Neon Srt-4", 2003, 2005)],
        "platform_apps": [
            ("Dodge", "Neon", 2000, 2005),
            ("Dodge", "Neon Pl", 2001, 2005),
        ],
        "cats": {
            "window-regulator": "same PL door shell as the 00-05 Neon",
            "window-switch": "switchgear shared with the 00-05 Neon",
            "climate-control": "same HVAC panel as the 00-05 Neon",
            "headlights": "03-05 facelift housings only — match donor year "
                          "03+",
            "tail-lights": "03-05 facelift lenses only — match donor year "
                           "03+",
        },
    },
    "ford-focus-svt-body": {
        "display": "Ford Focus platform (SVT)",
        "engine_note": ("The SVT Focus 2.0 Zetec-SVT only appears in "
                        "qualified build-date rows — engine parts stay "
                        "unverified; other Focus donors are NOT safe."),
        "trim_apps": [("Ford", "Focus Svt", 2002, 2004)],
        "platform_apps": [
            ("Ford", "Focus", 2000, 2004),
            ("Ford", "Focus Wagon", 2000, 2004),
        ],
        "cats": {
            "window-regulator": "SVT is the 3/5-door hatch — match the donor "
                                "body style and door count",
            "window-switch": "switchgear shared across the 00-04 Focus range",
            "climate-control": "same HVAC panel across the 00-04 Focus",
            "headlights": "00-04 housings shared (SVT HID option differs — "
                          "halogen cars only)",
        },
    },
    "panther-marauder-body": {
        "display": "Ford Panther platform (Marauder)",
        "trim_apps": [("Mercury", "Marauder", 2003, 2004)],
        "platform_apps": [
            ("Mercury", "Grand Marquis", 2003, 2011),
            ("Ford", "Crown Victoria", 2003, 2011),
            ("Lincoln", "Town Car", 2003, 2011),
        ],
        "cats": {
            "window-regulator": "same 03+ Panther door hardware (chassis "
                                "revision in 2003 — stick to 03+ donors)",
            "window-switch": "switchgear shared across 03+ Panthers",
            "headlights": "Marauder uses Grand Marquis housings (dark trim "
                          "is cosmetic) — Grand Marquis donors only",
            "tail-lights": "Grand Marquis lenses fit — Grand Marquis donors "
                           "only",
        },
    },
    "subaru-gr-wrx-body": {
        "display": "Subaru GR/GE platform (Impreza WRX)",
        "trim_apps": [("Subaru", "Impreza WRX", 2008, 2014),
                      ("Subaru", "WRX", 2008, 2014)],
        "platform_apps": [("Subaru", "Impreza", 2008, 2014)],
        "cats": {
            "window-regulator": "WRX was sedan and hatch — match the donor "
                                "body style",
            "window-switch": "switchgear shared across the 08-14 Impreza "
                             "range",
            "climate-control": "same panel across the 08-14 Impreza range",
        },
    },
    "subaru-va-wrx-body": {
        "display": "Subaru VA WRX / GJ Impreza sedan",
        "trim_apps": [("Subaru", "WRX", 2015, 2021)],
        "platform_apps": [("Subaru", "Impreza", 2012, 2016)],
        "cats": {
            "window-regulator": "VA WRX uses the 2012-16 Impreza sedan door "
                                "shell (aftermarket fitment lists cover "
                                "both) — sedan donors only, verify the part "
                                "number",
            "window-switch": "switchgear shared with the 12-16 Impreza sedan",
        },
    },
    "vw-mk5-r32-body": {
        "display": "VW Golf MkV platform (R32)",
        "trim_apps": [("Volkswagen", "R32", 2008, 2008)],
        "platform_apps": [
            ("Volkswagen", "GTI", 2006, 2009),
            ("Volkswagen", "Golf Gti", 2006, 2009),
            ("Volkswagen", "Rabbit", 2006, 2009),
            ("Volkswagen", "Golf", 2006, 2009),
        ],
        "cats": {
            "window-regulator": "R32 is the 2-door MkV shell — match the "
                                "donor door count",
            "window-switch": "switchgear shared across the MkV Golf range",
            "climate-control": "same Climatic/Climatronic panel — match "
                               "manual vs auto climate",
        },
    },
    # --- Mercedes AMG: each AMG string maps onto its class, gen-windowed.
    # AMG shares the class body shell; door hardware/switchgear carry over.
    # Clusters (AMG faces) and exterior panels/mirrors are omitted. Lights
    # are omitted for Mercedes: halogen/xenon + facelift splits make an
    # unqualified claim dishonest. The feed spells most classes two ways
    # ("E-Class" and "Mercedes E-Class") — both are mapped.
    "mb-w210-e55": {
        "display": "Mercedes W210 platform (E55 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "E55 Amg", 1999, 2002)],
        "platform_apps": [("Mercedes-Benz", "E-Class", 1996, 2002),
                          ("Mercedes-Benz", "Mercedes E-Class", 1996, 2002)],
        "cats": {
            "window-regulator": "same W210 sedan door shell",
            "window-switch": "switchgear shared across the W210 range",
            "climate-control": "same panel across the W210 range",
        },
    },
    "mb-w211-e55": {
        "display": "Mercedes W211 platform (E55 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "E55 Amg", 2003, 2006)],
        "platform_apps": [("Mercedes-Benz", "E-Class", 2003, 2009),
                          ("Mercedes-Benz", "Mercedes E-Class", 2003, 2009)],
        "cats": {
            "window-regulator": "same W211 sedan door shell",
            "window-switch": "switchgear shared across the W211 range",
            "climate-control": "same panel across the W211 range",
        },
    },
    "mb-w208-clk55": {
        "display": "Mercedes W208 platform (CLK55 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "Clk55 Amg", 2001, 2002)],
        "platform_apps": [("Mercedes-Benz", "CLK-Class", 1998, 2003)],
        "cats": {
            "window-regulator": "W208 coupe/cabrio door shell — match body "
                                "style",
            "window-switch": "switchgear shared across the W208 range",
        },
    },
    "mb-w215-cl55": {
        "display": "Mercedes C215 platform (CL55 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "Cl55 Amg", 2001, 2006)],
        "platform_apps": [("Mercedes-Benz", "CL-Class", 2000, 2006),
                          ("Mercedes-Benz", "Mercedes Cl-Class", 2000, 2006)],
        "cats": {
            "window-regulator": "same C215 coupe door shell",
            "window-switch": "switchgear shared across the C215 range",
        },
    },
    "mb-w163-ml55": {
        "display": "Mercedes W163 platform (ML55 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "Ml55 Amg", 2000, 2003)],
        "platform_apps": [("Mercedes-Benz", "M-Class", 1998, 2005),
                          ("Mercedes-Benz", "Ml-Class", 1998, 2005),
                          ("Mercedes-Benz", "Mercedes Ml-Class", 1998, 2005)],
        "cats": {
            "window-regulator": "same W163 door shell across the range",
            "window-switch": "switchgear shared across the W163 range",
            "climate-control": "same panel across the W163 range",
        },
    },
    "mb-w221-s63": {
        "display": "Mercedes W221 platform (S63 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) — no verified engine groups; "
                        "AMG engines interchange with other same-code AMGs "
                        "only."),
        "trim_apps": [("Mercedes-Benz", "S63 Amg", 2007, 2013)],
        "platform_apps": [("Mercedes-Benz", "S-Class", 2007, 2013),
                          ("Mercedes-Benz", "Mercedes S-Class", 2007, 2013)],
        "cats": {
            "window-regulator": "same W221 sedan door shell",
            "window-switch": "switchgear shared across the W221 range",
            "climate-control": "same panel across the W221 range",
        },
    },
    "mb-w205-c43": {
        "display": "Mercedes W205 platform (C43 AMG)",
        "engine_note": ("Mercedes engine rows in our catalog are vendor-"
                        "mixed (Bosch/Valeo) and stop around 2015 — no "
                        "verified engine groups for the C43's M276 biturbo."),
        "trim_apps": [("Mercedes-Benz", "C43 Amg", 2015, 2021)],
        "platform_apps": [("Mercedes-Benz", "C-Class", 2015, 2020),
                          ("Mercedes-Benz", "Mercedes C-Class", 2015, 2020)],
        "cats": {
            "window-regulator": "same W205 door shell — match sedan/coupe "
                                "body style",
            "window-switch": "switchgear shared across the W205 range",
        },
    },
}

_VALID_TRIM_CATS = {"gauge-cluster", "climate-control", "window-regulator",
                    "window-switch", "tail-lights", "headlights",
                    "side-mirrors"}


def _lint_trim_platform_groups() -> list[str]:
    """Import-time sanity: body categories only, well-formed spans, notes."""
    probs = []
    for tid, t in TRIM_PLATFORM_GROUPS.items():
        if not t.get("trim_apps"):
            probs.append(f"{tid}: no trim_apps")
        if not t.get("platform_apps"):
            probs.append(f"{tid}: no platform_apps")
        for a in list(t.get("trim_apps", [])) + list(t.get("platform_apps", [])):
            if len(a) != 4 or not (1900 < a[2] <= a[3] < 2035):
                probs.append(f"{tid}: bad span {a}")
        if not t.get("cats"):
            probs.append(f"{tid}: no cats")
        for cid, note in t.get("cats", {}).items():
            if cid not in _VALID_TRIM_CATS:
                probs.append(f"{tid}: {cid} is not a body category")
            if not note or len(note) < 15:
                probs.append(f"{tid}/{cid}: missing/terse caveat")
    return probs


_trim_problems = _lint_trim_platform_groups()
if _trim_problems:
    raise ValueError(
        "TRIM_PLATFORM_GROUPS lint failed:\n  " + "\n  ".join(_trim_problems))


# ===========================================================================
# PART-FIRST INTERCHANGE (v2) — "I need an alternator" search.
#
# PLATFORM_FAMILIES (above) answers "this car on the lot shares part X with
# its siblings" — card provenance. The part-first flow inverts the question:
# the USER names a part and THEIR car, and we list every donor vehicle in
# nearby yards carrying a part that fits. Two data sources answer it:
#
#   1. ENGINE_FAMILIES — engine-driven parts (alternator, starter) follow the
#      ENGINE, not the model: a 2AZ-FE alternator from a Scion tC fits a
#      Camry 2.4. Each family lists the US-market vehicles/years that carried
#      the engine; the VIN-decode engine string ("2.4L 4-cyl") confirms a
#      donor actually has it.
#   2. PLATFORM_FAMILIES two-way groups — body/interior parts (clusters,
#      regulators, lights) follow the platform/generation; the hand-verified
#      groups above are exported as-is. (One-way "donor" groups stay card
#      provenance only — they describe swaps INTO cars we can't enumerate.)
#
# Honesty contract (owner directive 2026-10-22: "I need accuracy, and
# breadth" — a false positive sends someone on a wasted drive):
#   - Two confidence tiers ship to the UI and nothing else:
#       "verified" — the SEEKER and the DONOR both sit inside one published
#                    part-number application list (a "verified group" below —
#                    e.g. TYC 2-11034's fitment table spans 04–06 Camry,
#                    04–07 Highlander 2.4, 04–05 RAV4, 04–08 Solara, 05–10
#                    tC: any pairing inside that list is a verified fit).
#                    Citation REQUIRED, in scraper/interchange_research.md
#                    under the family id. Research (2026-10-22) showed
#                    family-wide verified flags overstate: the 2AZ family
#                    alone spans at least three distinct alternator units.
#       "likely"   — same engine family, so the part very likely carries
#                    over, but this exact pairing isn't inside a verified
#                    application list. UI must say "verify part number".
#   - An app marked sole=False means the model also came with other engines;
#     a donor without a usable engine decode can only ever be "likely" with
#     an "engine unverified" warning. sole=True (every US example of those
#     model-years carried a family engine) lets a decode-less donor stay at
#     the part's own tier.
#   - ambig: the model offered ANOTHER engine with the SAME displacement/
#     cylinder count in these years (Vulcan vs Duratec 3.0, NA vs turbo EJ25,
#     NA vs EcoBoost 3.5) — the decode string cannot tell them apart, so
#     donors from this app are ALWAYS capped at "likely" and the ambig note
#     ships verbatim. Accuracy > coverage.
#
# Deliberate exclusions (accuracy forced them — see research notes):
#   - ECM/BCM: calibration/part-number specific even within one model-year.
#   - Diesel engines (Cummins/Powerstroke/Duramax): different accessory
#     ecosystems; cylinder-count/displacement guards exclude them.
#   - One-way swap-culture groups (B-series, H22...): not enumerable donors.
#
# App tuple: (make, model, yr_lo, yr_hi[, flags]) — flags: {"sole": True} /
# {"ambig": "note"}. model may end with "*" for prefix match ("Silverado*"
# catches Silverado / Silverado 1500 / 2500 spellings; the engine check keeps
# wrong-engine donors out). make may be "A|B" when feeds split a marque
# (Dodge|Ram). Years are the US model years the family engine was OFFERED in
# that model — not the model's full run.
# ===========================================================================

INTERCHANGE_PART_CATEGORIES: dict[str, dict] = {
    # kind "engine": matched through ENGINE_FAMILIES only.
    # kind "body":   matched through same-model generation windows (client
    #                side, via each part row's "fits" range) + exported
    #                PLATFORM_FAMILIES groups.
    # tokens:      lowercase substrings locating the part row in a vehicle's
    #              part set (for eBay-value display).
    # priceTokens: substrings for the yards' published price lists.
    "alternator": {
        "label": "Alternator", "kind": "engine",
        "tokens": ["alternator"], "priceTokens": ["alternator"]},
    "starter": {
        "label": "Starter", "kind": "engine",
        "tokens": ["starter"], "priceTokens": ["starter"]},
    "gauge-cluster": {
        "label": "Gauge cluster", "kind": "body",
        "tokens": ["cluster"],
        "priceTokens": ["instrument cluster", "speedometer", "cluster"]},
    "climate-control": {
        "label": "Climate control panel", "kind": "body",
        "tokens": ["climate control"],
        "priceTokens": ["climate control", "heater control", "temperature control"]},
    "window-regulator": {
        "label": "Window regulator + motor", "kind": "body",
        "tokens": ["window regulator"],
        "priceTokens": ["window regulator"]},
    "window-switch": {
        "label": "Power window switch", "kind": "body",
        "tokens": ["master switch", "window switch"],
        "priceTokens": ["window switch", "master switch"]},
    "tail-lights": {
        "label": "Tail lights", "kind": "body",
        "tokens": ["tail light"],
        "priceTokens": ["tail light", "taillight", "tail lamp", "taillamp"]},
    "headlights": {
        "label": "Headlights", "kind": "body",
        "tokens": ["headlight"],
        "priceTokens": ["headlight", "headlamp"]},
    "side-mirrors": {
        "label": "Side mirrors", "kind": "body",
        "tokens": ["side mirror"],
        "priceTokens": ["door mirror", "side mirror", "mirror"]},
    "tow-mirrors": {
        "label": "Tow mirrors", "kind": "body",
        "tokens": ["tow mirror"], "priceTokens": ["mirror"]},
    "third-row-seat": {
        "label": "3rd row seat", "kind": "body",
        "tokens": ["3rd row"], "priceTokens": ["third", "3rd", "seat"]},
    "tailgate": {
        "label": "Tailgate", "kind": "body",
        "tokens": ["tailgate"], "priceTokens": ["tailgate"]},
}

# Default caveat lines — families override where the family has a sharper one.
_ALT_NOTE = ("match amperage, pulley and plug before buying — options "
             "packages used higher-amp units")
_STR_NOTE = "match the part number — nose cone / tooth count can differ"

ENGINE_FAMILIES: dict[str, dict] = {
    # ------------------------------------------------------------- Toyota
    "toyota-22re": {
        "display": "Toyota 22RE 2.4 I4 (EFI)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Toyota", "Pickup", 1985, 1995),
            ("Toyota", "4Runner", 1985, 1995),
        ],
        "parts": {
            "alternator": {"note": "22RE only — the 3.0 V6 (3VZ-E) unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-rz": {
        # 2RZ-FE (2.4) and 3RZ-FE (2.7) share alternator part numbers in
        # every Denso catalog year row, so one family covers both — a 2.4
        # Tacoma donor genuinely serves a 2.7 seeker for these parts.
        "display": "Toyota 2RZ/3RZ-FE 2.4/2.7 I4",
        "engine": {"liters": [2.4, 2.7], "cyl": 4},
        "apps": [
            ("Toyota", "Tacoma", 1995, 2004),
            ("Toyota", "4Runner", 1996, 2000),
            ("Toyota", "T100", 1994, 1998),
        ],
        "parts": {
            "alternator": {"note": "2RZ and 3RZ share the same published units in every year — the 3.4 V6 unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-5vz": {
        "display": "Toyota 5VZ-FE 3.4 V6",
        "engine": {"liters": [3.4], "cyl": 6},
        "apps": [
            ("Toyota", "Tacoma", 1995, 2004),
            ("Toyota", "4Runner", 1996, 2002),
            ("Toyota", "T100", 1995, 1998),
            ("Toyota", "Tundra", 2000, 2004),
        ],
        "parts": {
            "alternator": {"note": "3.4 (5VZ) unit — 60/70/80A revisions across the years, match amps and part number; the 2.4/2.7 I4 unit differs"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-5s": {
        "display": "Toyota 5S-FE 2.2 I4",
        "engine": {"liters": [2.2], "cyl": 4},
        "apps": [
            ("Toyota", "Camry", 1992, 2001),
            ("Toyota", "Celica", 1994, 1999),
            ("Toyota", "Solara", 1999, 2001),
            ("Toyota", "Camry Solara", 1999, 2001),  # feed spelling
            ("Toyota", "MR2", 1991, 1995),
        ],
        "parts": {
            "alternator": {"note": "4-cyl (5S-FE) unit — the V6 Camry unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-1mz": {
        "display": "Toyota/Lexus 1MZ-FE 3.0 V6",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Toyota", "Camry", 1994, 2006),
            ("Toyota", "Avalon", 1995, 2004, {"sole": True}),
            ("Toyota", "Solara", 1999, 2003),
            ("Toyota", "Camry Solara", 1999, 2003),  # feed spelling
            ("Toyota", "Sienna", 1998, 2003, {"sole": True}),
            ("Toyota", "Highlander", 2001, 2003),
            ("Lexus", "ES 300", 1994, 2003, {"sole": True}),
            ("Lexus", "RX 300", 1999, 2003, {"sole": True}),
        ],
        "parts": {
            # Window mirrors the hand-researched platform family above:
            # Hollander 601-58691 crosses the 97+ Denso unit; earlier 1MZ
            # cars used a different alternator, and the 04+ 3MZ plug differs.
            "alternator": {"years": (1997, 2003),
                           "note": "V6 (1MZ) Denso unit, 97–03 window — match plug & amps (100A vs 130A tow pkg)",
                           "verified": {
                               "evidence": "Hollander interchange 601-58691 (retrieved 2026-10-22) crosses Camry V6 97-01 = ES 300 97-01; Denso 101211-7440/7450 = Toyota 27060-20230 100A across the 1MZ family per Denso catalog + ToyotaNation cross-reference",
                               "groups": [[("Toyota", "Camry", 1997, 2001),
                                           ("Lexus", "ES 300", 1997, 2001)]],
                           }},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-3mz": {
        "display": "Toyota/Lexus 3MZ-FE 3.3 V6",
        "engine": {"liters": [3.3], "cyl": 6},
        "apps": [
            ("Toyota", "Camry", 2004, 2006),
            ("Toyota", "Solara", 2004, 2008),
            ("Toyota", "Camry Solara", 2004, 2008),  # feed spelling
            ("Toyota", "Sienna", 2004, 2006, {"sole": True}),
            ("Toyota", "Highlander", 2004, 2007),
            ("Lexus", "ES 330", 2004, 2006, {"sole": True}),
            ("Lexus", "RX 330", 2004, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "3.3 (3MZ) unit — the older 1MZ plug differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2gr": {
        "display": "Toyota/Lexus 2GR-FE 3.5 V6",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Toyota", "Camry", 2007, 2017),
            ("Toyota", "Avalon", 2005, 2018, {"sole": True}),
            ("Toyota", "Sienna", 2007, 2016),
            ("Toyota", "Highlander", 2008, 2016),
            ("Toyota", "RAV4", 2006, 2012),
            ("Toyota", "Venza", 2009, 2015),
            ("Lexus", "ES 350", 2007, 2018, {"sole": True}),
            ("Lexus", "RX 350", 2007, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2GR-FE unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2az": {
        "display": "Toyota/Scion 2AZ-FE 2.4 I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Toyota", "Camry", 2002, 2009),
            ("Toyota", "Solara", 2004, 2008),
            ("Toyota", "Camry Solara", 2004, 2008),  # feed spelling
            ("Toyota", "RAV4", 2004, 2008),
            ("Toyota", "Highlander", 2001, 2007),
            ("Scion", "tC", 2005, 2010, {"sole": True}),
            ("Scion", "xB", 2008, 2015, {"sole": True}),
            ("Toyota", "Matrix", 2009, 2013),
            ("Toyota", "Corolla", 2009, 2010),
        ],
        "parts": {
            # Three distinct Denso units inside one engine family — the
            # reason tiers are computed per verified GROUP, never family-wide.
            "alternator": {"note": "2AZ-FE unit — 4-cyl only, the V6 differs; at least 3 distinct units across the family's years, match part number",
                           "verified": {
                               "evidence": "TYC 2-11034 fitment table (standardautopart.com, retrieved 2026-10-22): Camry 2.4 04-06, Highlander 2.4 04-07, RAV4 04-05, Solara 2.4 04-08 + DB Electrical AND0288 adds tC 05-10 (Toyota 27060-0H100/28260/28270). Toyota 27060-0H111-84 OEM listing (toyota.oempartsonline.com, retrieved 2026-10-22): Camry 2.4 07-09, Matrix 2.4 09-13, Corolla 2.4 09-10.",
                               "groups": [
                                   [("Toyota", "Camry", 2004, 2006),
                                    ("Toyota", "Highlander", 2004, 2007),
                                    ("Toyota", "RAV4", 2004, 2005),
                                    ("Toyota", "Solara", 2004, 2008),
                                    ("Toyota", "Camry Solara", 2004, 2008),
                                    ("Scion", "tC", 2005, 2010)],
                                   [("Toyota", "Camry", 2007, 2009),
                                    ("Toyota", "Matrix", 2009, 2013),
                                    ("Toyota", "Corolla", 2009, 2010)],
                               ],
                           }},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2ar": {
        "display": "Toyota/Scion 2AR-FE 2.5 I4",
        "engine": {"liters": [2.5], "cyl": 4},
        "apps": [
            ("Toyota", "Camry", 2010, 2017),
            ("Toyota", "RAV4", 2009, 2012),
            ("Toyota", "RAV4", 2013, 2018, {"sole": True}),
            ("Scion", "tC", 2011, 2016, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2AR-FE unit — hybrid Camrys have no belt alternator; the 10–11 XV40 Camry unit differs from the 12+ one, match part number",
                           "verified": {
                               "evidence": "Denso 104210-2270/-2340 (Toyota 27060-36010/36011, Lester 11402) application tables (dcalltech.com + rareelectrical.com, retrieved 2026-10-22): Scion tC 2.5 2011-16, Camry 2.5 2012-15, RAV4 2.5 2009-12.",
                               "groups": [[("Scion", "tC", 2011, 2016),
                                           ("Toyota", "Camry", 2012, 2015),
                                           ("Toyota", "RAV4", 2009, 2012)]],
                           }},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-1zz": {
        "display": "Toyota/Pontiac 1ZZ-FE 1.8 I4",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Toyota", "Corolla", 1998, 2008, {"sole": True}),
            ("Toyota", "Matrix", 2003, 2008),
            ("Pontiac", "Vibe", 2003, 2008),
            ("Toyota", "Celica", 2000, 2005),
            ("Toyota", "MR2 Spyder", 2000, 2005, {"sole": True}),
            ("Chevrolet", "Prizm", 1998, 2002, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "1ZZ-FE unit — the 2ZZ (Celica GT-S/XRS) differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2zr": {
        "display": "Toyota/Scion 2ZR-FE 1.8 I4",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Toyota", "Corolla", 2009, 2010),
            ("Toyota", "Corolla", 2011, 2019, {"sole": True}),
            ("Toyota", "Matrix", 2009, 2013),
            ("Pontiac", "Vibe", 2009, 2010),
            ("Scion", "xD", 2008, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2ZR-FE unit — Prius 1.8 (2ZR-FXE hybrid) has no belt alternator; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2uz": {
        "display": "Toyota/Lexus 2UZ-FE 4.7 V8",
        "engine": {"liters": [4.7], "cyl": 8},
        "apps": [
            ("Toyota", "Tundra", 2000, 2009),
            ("Toyota", "Sequoia", 2001, 2009),
            ("Toyota", "Land Cruiser", 1998, 2007, {"sole": True}),
            ("Toyota", "4Runner", 2003, 2009),
            ("Lexus", "GX 470", 2003, 2009, {"sole": True}),
            ("Lexus", "LX 470", 1998, 2007, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2UZ unit — 05+ VVT-i brackets can differ, verify; " + _ALT_NOTE},
            "starter": {"note": "under-intake starter on 2UZ — " + _STR_NOTE},
        },
    },
    "toyota-1gr": {
        "display": "Toyota 1GR-FE 4.0 V6",
        "engine": {"liters": [4.0], "cyl": 6},
        "apps": [
            ("Toyota", "Tacoma", 2005, 2015),
            ("Toyota", "4Runner", 2003, 2021),
            ("Toyota", "Tundra", 2005, 2010),
            ("Toyota", "FJ Cruiser", 2007, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "1GR unit — 2010+ dual-VVT-i revision, verify bracket/plug; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # -------------------------------------------------------- Honda/Acura
    "honda-a20": {
        "display": "Honda A20 2.0 I4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Honda", "Accord", 1986, 1989, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "carbureted (A20A1) and fuel-injected (A20A3) cars use different units across the same years — check which yours is before buying"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-f22": {
        "display": "Honda F22 2.2 I4",
        "engine": {"liters": [2.2], "cyl": 4},
        "apps": [
            ("Honda", "Accord", 1990, 1997),
        ],
        "parts": {
            "alternator": {"note": "94-97 splits VTEC (F22B1, 90A) vs non-VTEC (F22B2, 80A) — match the part number; the 95-97 2.7 V6 unit differs"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-d16": {
        "display": "Honda D16 1.6 SOHC I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 1996, 2000),
            ("Honda", "Civic del Sol", 1996, 1997),
        ],
        "parts": {
            "alternator": {"note": "D16Y-era unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-d17": {
        "display": "Honda D17 1.7 I4",
        "engine": {"liters": [1.7], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 2001, 2005),
        ],
        "parts": {
            "alternator": {"note": "D17 unit — hybrid & Si (2.0) differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-r18": {
        "display": "Honda R18 1.8 I4",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 2006, 2011),
            ("Honda", "Civic", 2012, 2015),
        ],
        "parts": {
            "alternator": {"note": "R18A (06–11) vs R18Z (12–15) — stay inside your window or match part number; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-f23": {
        "display": "Honda F23 2.3 I4",
        "engine": {"liters": [2.3], "cyl": 4},
        "apps": [
            ("Honda", "Accord", 1998, 2002),
            ("Acura", "CL", 1998, 1999),
        ],
        "parts": {
            "alternator": {"note": "F23A unit — the V6 Accord unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-k24a": {
        "display": "Honda/Acura K24 2.4 I4 (02–09 era)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Honda", "Accord", 2003, 2007),
            ("Honda", "CR-V", 2002, 2009, {"sole": True}),
            ("Honda", "Element", 2003, 2011, {"sole": True}),
            ("Acura", "TSX", 2004, 2008, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "K24A-era Denso unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-k24z": {
        "display": "Honda/Acura K24Z 2.4 I4 (08–15 era)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Honda", "Accord", 2008, 2012),
            ("Honda", "CR-V", 2010, 2014, {"sole": True}),
            ("Honda", "Civic", 2012, 2015),
            ("Honda", "Crosstour", 2012, 2015),
            ("Acura", "TSX", 2009, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "K24Z-era unit — earlier K24A plug/bracket can differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-j30": {
        "display": "Honda/Acura J30 3.0 V6 (Accord)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Honda", "Accord", 1998, 2002),
            ("Honda", "Accord", 2003, 2007),
            ("Acura", "CL", 1997, 1999),
        ],
        "parts": {
            "alternator": {"note": "J30A unit — 98–02 vs 03–07 generations differ, stay in your window; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-j35-early": {
        "display": "Honda J35 3.5 V6 (99–04 era)",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Honda", "Odyssey", 1999, 2004, {"sole": True}),
            ("Honda", "Pilot", 2003, 2005, {"sole": True}),
            ("Acura", "MDX", 2001, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "J35A unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-j35-mid": {
        "display": "Honda J35 3.5 V6 (05–10 era)",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Honda", "Odyssey", 2005, 2010, {"sole": True}),
            ("Honda", "Pilot", 2006, 2008, {"sole": True}),
            ("Honda", "Ridgeline", 2006, 2008, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "VCM-era J35A6/A7/A9 — match part number across VCM vs non-VCM; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-j35-z": {
        "display": "Honda J35Z/Y 3.5 V6 (08–17 era)",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Honda", "Accord", 2008, 2012),
            ("Honda", "Odyssey", 2011, 2017, {"sole": True}),
            ("Honda", "Pilot", 2009, 2015, {"sole": True}),
            ("Honda", "Ridgeline", 2009, 2014, {"sole": True}),
            ("Honda", "Crosstour", 2010, 2015),
        ],
        "parts": {
            "alternator": {"note": "J35Z-era unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "acura-j32": {
        "display": "Acura J32 3.2 V6 (TL/CL)",
        "engine": {"liters": [3.2], "cyl": 6},
        "apps": [
            ("Acura", "TL", 1999, 2008, {"sole": True}),
            ("Acura", "CL", 2001, 2003, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "J32A unit — 99–03 vs 04–08 TL generations differ, stay in your window; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # -------------------------------------------------------------- Nissan
    "nissan-ka24": {
        "display": "Nissan KA24E/DE 2.4 I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Nissan", "Altima", 1993, 2001, {"sole": True}),
            ("Nissan", "240SX", 1989, 1998, {"sole": True}),
            ("Nissan", "Frontier", 1998, 2004),
            ("Nissan", "Xterra", 2000, 2004),
            ("Nissan", "Pickup", 1990, 1997),
        ],
        "parts": {
            "alternator": {"note": "KA24DE unit — truck vs car brackets can differ, verify; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-qr25": {
        "display": "Nissan QR25DE 2.5 I4",
        "engine": {"liters": [2.5], "cyl": 4},
        "apps": [
            ("Nissan", "Altima", 2002, 2018),
            ("Nissan", "Sentra", 2002, 2006),
            ("Nissan", "Rogue", 2008, 2020, {"sole": True}),
            ("Nissan", "Rogue Select", 2014, 2015, {"sole": True}),
            ("Nissan", "Frontier", 2005, 2019),
        ],
        "parts": {
            "alternator": {"note": "QR25 unit — 02–06 vs 07+ plugs differ, stay in your window or match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-vq35de": {
        "display": "Nissan/Infiniti VQ35DE 3.5 V6",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Nissan", "Altima", 2002, 2006),
            ("Nissan", "Maxima", 2002, 2014, {"sole": True}),
            ("Nissan", "Murano", 2003, 2014, {"sole": True}),
            ("Nissan", "Pathfinder", 2001, 2004),
            ("Nissan", "Quest", 2004, 2009, {"sole": True}),
            ("Nissan", "Quest", 2011, 2017, {"sole": True}),
            ("Infiniti", "M35", 2006, 2008, {"sole": True}),
            ("Infiniti", "JX35", 2013, 2013, {"sole": True}),
            ("Infiniti", "QX60", 2014, 2020),
            ("Nissan", "350Z", 2003, 2006, {"sole": True}),
            ("Infiniti", "G35", 2003, 2006, {"sole": True}),
            ("Infiniti", "I35", 2002, 2004, {"sole": True}),
            ("Infiniti", "FX35", 2003, 2008, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "VQ35DE unit — 07+ HR-block cars differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-vq40": {
        "display": "Nissan VQ40DE 4.0 V6",
        "engine": {"liters": [4.0], "cyl": 6},
        "apps": [
            ("Nissan", "Pathfinder", 2005, 2012),
            ("Nissan", "Frontier", 2005, 2019),
            ("Nissan", "Xterra", 2005, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "VQ40 unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-mr20": {
        "display": "Nissan MR20DE 2.0 I4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Nissan", "Sentra", 2007, 2012),
        ],
        "parts": {
            "alternator": {"note": "base 2.0 (MR20DE) unit — the SE-R 2.5 differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-vk56": {
        "display": "Nissan VK56DE 5.6 V8",
        "engine": {"liters": [5.6], "cyl": 8},
        "apps": [
            ("Nissan", "Titan", 2004, 2015, {"sole": True}),
            ("Nissan", "Armada", 2005, 2015, {"sole": True}),
            ("Nissan", "Pathfinder Armada", 2004, 2004, {"sole": True}),
            ("Infiniti", "QX56", 2004, 2010, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "VK56DE unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-mr18": {
        "display": "Nissan MR18DE 1.8 I4",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Nissan", "Versa", 2007, 2012),
            ("Nissan", "Cube", 2009, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "MR18 unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "nissan-hr16": {
        "display": "Nissan HR16DE 1.6 I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Nissan", "Versa", 2012, 2019),
            ("Nissan", "Versa Note", 2014, 2019, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "HR16 unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ---------------------------------------------------------------- Ford
    "ford-46-2v": {
        "display": "Ford 4.6 2V Modular V8",
        "engine": {"liters": [4.6], "cyl": 8},
        "apps": [
            ("Ford", "F-150", 1997, 2008),
            ("Ford", "F-150 Heritage", 2004, 2004),
            ("Ford", "Expedition", 1997, 2004),
            ("Ford", "Crown Victoria", 1992, 2011, {"sole": True}),
            ("Mercury", "Grand Marquis", 1992, 2011, {"sole": True}),
            ("Lincoln", "Town Car", 1991, 2011, {"sole": True}),
            ("Ford", "Mustang", 1996, 2004),
            ("Ford", "Explorer", 2002, 2005),
        ],
        "parts": {
            "alternator": {"note": "truck vs Panther vs Mustang brackets/plugs differ by era — match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-54-2v": {
        "display": "Ford 5.4 2V Triton V8",
        "engine": {"liters": [5.4], "cyl": 8},
        "apps": [
            ("Ford", "F-150", 1997, 2003),
            ("Ford", "F-150 Heritage", 2004, 2004),
            ("Ford", "Expedition", 1997, 2004),
        ],
        "parts": {
            "alternator": {"note": "shared with the 4.6 truck unit in most years — match plug & amps"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-54-3v": {
        "display": "Ford 5.4 3V Triton V8",
        "engine": {"liters": [5.4], "cyl": 8},
        "apps": [
            ("Ford", "F-150", 2004, 2010),
            ("Ford", "Expedition", 2005, 2014),
        ],
        "parts": {
            "alternator": {"note": "3V-era unit — the 97–03 2V unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-vulcan30": {
        "display": "Ford 3.0 Vulcan V6",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Ford", "Taurus", 1986, 2007,
             {"ambig": "Taurus also offered DOHC 3.0 V6s (Duratec) — same decode string; confirm which 3.0 before buying"}),
            ("Mercury", "Sable", 1986, 2005,
             {"ambig": "Sable also offered the Duratec 3.0 — same decode string; confirm which 3.0"}),
            ("Ford", "Ranger", 1991, 2008),
        ],
        "parts": {
            "alternator": {"note": "pushrod Vulcan unit — Duratec DOHC 3.0 does NOT interchange; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-duratec30": {
        "display": "Ford/Mazda Duratec 3.0 DOHC V6",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Ford", "Fusion", 2006, 2012),
            ("Ford", "Escape", 2001, 2012),
            ("Mercury", "Milan", 2006, 2011),
            ("Mercury", "Mariner", 2005, 2011),
            ("Mazda", "Tribute", 2001, 2011),
            ("Ford", "Five Hundred", 2005, 2007, {"sole": True}),
            ("Mercury", "Montego", 2005, 2007, {"sole": True}),
            ("Ford", "Taurus", 1996, 2007,
             {"ambig": "Taurus 3.0s split Vulcan (pushrod) vs Duratec (DOHC) — same decode string; confirm DOHC before buying"}),
        ],
        "parts": {
            "alternator": {"note": "DOHC Duratec unit — Vulcan pushrod 3.0 does NOT interchange; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-mzr": {
        "display": "Ford/Mazda MZR-Duratec 2.0/2.3/2.5 I4",
        "engine": {"liters": [2.0, 2.3, 2.5], "cyl": 4},
        "apps": [
            # Fusion 2.5 carried into the 2013-14 refresh — the 210-0615
            # list spans the 2.5 AND the 2.0T those years (shared unit).
            ("Ford", "Fusion", 2006, 2014),
            ("Ford", "Escape", 2005, 2012),
            ("Ford", "Focus", 2005, 2011),
            # Bare "3"/"6" match every feed spelling ("3", "Mazda3",
            # "Mazda 3") via the make-stripped squash; "Mazda3" did not.
            ("Mazda", "3", 2004, 2013),
            ("Mazda", "5", 2006, 2010),
            ("Mazda", "6", 2003, 2013),
            ("Mercury", "Milan", 2006, 2011),
            ("Mercury", "Mariner", 2005, 2011),
            ("Mazda", "Tribute", 2005, 2011),
            ("Ford", "Ranger", 2001, 2011),
        ],
        "parts": {
            "alternator": {"note": "MZR family — displacement variants share accessories in most years, but verify plug & pulley; turbo (Mazdaspeed/EcoBoost) differs"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-cyclone": {
        "display": "Ford 3.5/3.7 Cyclone V6 (non-turbo)",
        "engine": {"liters": [3.5, 3.7], "cyl": 6},
        "apps": [
            ("Ford", "Edge", 2007, 2015),
            ("Mercury", "Sable", 2008, 2009, {"sole": True}),
            ("Lincoln", "MKZ", 2007, 2012, {"sole": True}),
            ("Lincoln", "MKS", 2009, 2016,
             {"ambig": "MKS EcoBoost is the 3.5 twin-turbo — same decode string; confirm non-turbo"}),
            ("Lincoln", "MKX", 2007, 2015, {"sole": True}),
            ("Ford", "Taurus", 2008, 2019,
             {"ambig": "SHO is the 3.5 EcoBoost twin-turbo — same decode string; confirm non-turbo"}),
            ("Ford", "Explorer", 2011, 2019,
             {"ambig": "Explorer Sport/Platinum is 3.5 EcoBoost — same decode string; confirm non-turbo"}),
            ("Ford", "Flex", 2009, 2019,
             {"ambig": "Flex EcoBoost shares the 3.5 decode string; confirm non-turbo"}),
            ("Ford", "Mustang", 2011, 2014),
            ("Ford", "Mustang", 2011, 2017),
            ("Ford", "F-150", 2011, 2014),
        ],
        "parts": {
            "alternator": {"note": "non-turbo Cyclone unit — EcoBoost accessories differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-40sohc": {
        "display": "Ford 4.0 SOHC V6",
        "engine": {"liters": [4.0], "cyl": 6},
        "apps": [
            ("Ford", "Explorer", 1997, 2000,
             {"ambig": "97–00 Explorers split 4.0 OHV vs 4.0 SOHC — same decode string; confirm SOHC"}),
            ("Ford", "Explorer", 2001, 2010),
            ("Ford", "Explorer Sport Trac", 2001, 2010),
            ("Ford", "Ranger", 2001, 2011),
            ("Ford", "Mustang", 2005, 2010),
            ("Mercury", "Mountaineer", 1998, 2010),
            ("Ford", "Explorer Sport", 2001, 2003),
        ],
        "parts": {
            "alternator": {"note": "SOHC unit — the older OHV 4.0 differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-3g-50": {
        "display": "Ford 5.0/5.8 Windsor V8 (3G era)",
        "engine": {"liters": [5.0, 5.8], "cyl": 8},
        "apps": [
            ("Ford", "Mustang", 1987, 1995),
            ("Ford", "F-150", 1987, 1996),
            ("Ford", "Bronco", 1987, 1996),
        ],
        "parts": {
            "alternator": {"note": "2G/3G era — many swap UP to the 130A 3G; match case style & plug"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ------------------------------------------------------------------ GM
    "ford-escape-16eb": {
        "display": "Ford Escape 1.6 EcoBoost I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Ford", "Escape", 2013, 2016),
        ],
        "parts": {
            "alternator": {"note": "1.6 EcoBoost unit — the 2.0 and 2.5 Escapes use different units; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-escape-20eb": {
        "display": "Ford Escape 2.0 EcoBoost I4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Ford", "Escape", 2013, 2016),
        ],
        "parts": {
            "alternator": {"note": "2.0 EcoBoost unit — the 1.6 and 2.5 Escapes use different units; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-vortec43": {
        "display": "GM Vortec 4.3 V6",
        "engine": {"liters": [4.3], "cyl": 6},
        "apps": [
            ("Chevrolet", "S-10*", 1994, 2004),
            ("GMC", "Sonoma", 1994, 2004),
            ("Chevrolet", "Blazer*", 1995, 2005, {"sole": True}),
            ("GMC", "Jimmy*", 1995, 2001, {"sole": True}),
            ("Chevrolet", "Astro*", 1994, 2005, {"sole": True}),
            ("GMC", "Safari*", 1994, 2005, {"sole": True}),
            ("Oldsmobile", "Bravada", 1996, 2001, {"sole": True}),
            ("Chevrolet", "Express*", 1996, 2008),
            ("GMC", "Savana*", 1996, 2008),
        ],
        "parts": {
            "alternator": {"note": "4.3 Vortec CS130/AD-series units — several amp and case revisions across the years, match the part number; 2000 S-trucks split mid-year by VIN"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-vortec-van": {
        "display": "Chevy/GMC Vortec V8 van (Express/Savana)",
        "engine": {"liters": [4.8, 5.0, 5.3, 5.7, 6.0], "cyl": 8},
        "apps": [
            ("Chevrolet", "Express*", 1996, 2010),
            ("GMC", "Savana*", 1996, 2010),
        ],
        "parts": {
            "alternator": {"note": "the published lists span the 5.0/5.7 (96-00) and 4.8/5.3/6.0 (05-10) together — two case styles exist, match the rear-cover style and part number; 01-04 vans left unverified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "cadillac-northstar": {
        "display": "Cadillac Northstar 4.6 V8",
        "engine": {"liters": [4.6], "cyl": 8},
        "apps": [
            ("Cadillac", "Deville", 1994, 2005, {"sole": True}),
            ("Cadillac", "Eldorado", 1994, 2002, {"sole": True}),
            ("Cadillac", "Seville", 1994, 2004, {"sole": True}),
            ("Cadillac", "DTS", 2006, 2011, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Northstar unit — buried under the intake side; limousine/hearse builds use a higher-amp unit, " + _ALT_NOTE},
            "starter": {"note": "under-intake starter on Northstar — " + _STR_NOTE},
        },
    },
    "gm-ecotec22": {
        "display": "GM Ecotec 2.2 I4 (L61)",
        "engine": {"liters": [2.2], "cyl": 4},
        "apps": [
            ("Chevrolet", "Cavalier", 2002, 2005),
            ("Chevrolet", "Cobalt", 2005, 2010),
            ("Chevrolet", "Malibu", 2004, 2008),
            ("Chevrolet", "HHR", 2006, 2010),
            ("Saturn", "ION", 2003, 2007),
            ("Pontiac", "G5", 2007, 2009),
            ("Pontiac", "Sunfire", 2002, 2005),
            ("Saturn", "VUE", 2002, 2007),
        ],
        "parts": {
            "alternator": {"note": "L61 Ecotec unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-ecotec24": {
        "display": "GM Ecotec 2.4 I4 (LE5/LE9/LEA)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Chevrolet", "Cobalt", 2006, 2010),
            ("Chevrolet", "Malibu", 2008, 2012),
            ("Chevrolet", "Equinox", 2010, 2017),
            ("Chevrolet", "HHR", 2008, 2011),
            ("GMC", "Terrain", 2010, 2017),
            ("Pontiac", "G6", 2006, 2009),
            ("Chevrolet", "Captiva Sport", 2012, 2015),
            ("Saturn", "VUE", 2008, 2010),
            ("Buick", "Verano", 2012, 2017),
            ("Saturn", "Aura", 2007, 2009),
            ("Buick", "Regal", 2011, 2013),
        ],
        "parts": {
            "alternator": {"note": "Ecotec 2.4 unit — direct-injection (LEA/LUK) era plugs can differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-14t": {
        "display": "GM 1.4 Turbo I4 (LUJ/LUV)",
        "engine": {"liters": [1.4], "cyl": 4},
        "apps": [
            ("Chevrolet", "Cruze", 2011, 2015),
            ("Chevrolet", "Cruze Limited", 2016, 2016),
            ("Chevrolet", "Sonic", 2012, 2018),
            ("Buick", "Encore", 2013, 2021),
            ("Chevrolet", "Trax", 2013, 2021),
        ],
        "parts": {
            "alternator": {"note": "gen-1 1.4T unit — the 16+ Cruze (LE2) differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-gen3-truck": {
        "display": "GM Gen III Vortec truck V8 (4.8/5.3/6.0)",
        "engine": {"liters": [4.8, 5.3, 6.0], "cyl": 8},
        "apps": [
            ("Chevrolet", "Silverado*", 1999, 2007),
            ("GMC", "Sierra*", 1999, 2007),
            ("Chevrolet", "Tahoe", 2000, 2006),
            ("GMC", "Yukon*", 2000, 2006),
            ("Chevrolet", "Suburban*", 2000, 2006),
            ("Chevrolet", "Avalanche", 2002, 2006),
            ("Cadillac", "Escalade*", 2002, 2006),
        ],
        "parts": {
            "alternator": {"note": "4.8/5.3/6.0 share brackets — match amps (105 vs 145) & plug; diesel/8.1 differ"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-gen4-truck": {
        "display": "GM Gen IV Vortec truck V8 (4.8/5.3/6.0/6.2)",
        "engine": {"liters": [4.8, 5.3, 6.0, 6.2], "cyl": 8},
        "apps": [
            ("Chevrolet", "Silverado*", 2007, 2013),
            ("GMC", "Sierra*", 2007, 2013),
            ("Chevrolet", "Tahoe", 2007, 2014),
            ("GMC", "Yukon*", 2007, 2014),
            ("Chevrolet", "Suburban*", 2007, 2014),
            ("Chevrolet", "Avalanche", 2007, 2013),
            ("Cadillac", "Escalade*", 2007, 2014),
        ],
        "parts": {
            "alternator": {"note": "GMT900-era unit — match amps & 2-pin plug; the 07 'Classic' body keeps Gen III parts"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-atlas42": {
        "display": "GM Atlas 4.2 I6 (LL8)",
        "engine": {"liters": [4.2], "cyl": 6},
        "apps": [
            ("Chevrolet", "Trailblazer", 2002, 2009),
            ("GMC", "Envoy", 2002, 2009),
            ("Oldsmobile", "Bravada", 2002, 2004, {"sole": True}),
            ("Buick", "Rainier", 2004, 2007),
            ("Saab", "9-7x", 2005, 2009),
            ("Isuzu", "Ascender", 2003, 2008),
            ("Chevrolet", "Trailblazer Ext", 2002, 2006),
            ("GMC", "Envoy Xl", 2002, 2006),
        ],
        "parts": {
            "alternator": {"note": "LL8 unit shared across the GMT360 twins; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-3800": {
        "display": "GM 3800 Series II/III V6",
        "engine": {"liters": [3.8], "cyl": 6},
        "apps": [
            ("Buick", "Lesabre", 1996, 2005, {"sole": True}),
            ("Pontiac", "Grand Prix", 1997, 2008),
            ("Pontiac", "Bonneville", 1996, 2005),
            ("Chevrolet", "Impala", 2000, 2005),
            ("Chevrolet", "Monte Carlo", 1998, 2005),
            ("Buick", "Regal", 1997, 2004, {"sole": True}),
            ("Buick", "Park Avenue", 1997, 2005, {"sole": True}),
            ("Buick", "Lucerne", 2006, 2008),
            ("Buick", "Lacrosse", 2005, 2009),
            ("Chevrolet", "Camaro", 1995, 2002),
            ("Pontiac", "Firebird", 1995, 2002),
        ],
        "parts": {
            "alternator": {"note": "NA 3800 unit — supercharged (GTP/SSEi) accessories differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-60deg": {
        "display": "GM 60° 2.8/3.1/3.4 V6",
        "engine": {"liters": [2.8, 3.1, 3.4], "cyl": 6},
        "apps": [
            ("Chevrolet", "Camaro", 1987, 1995),
            ("Pontiac", "Firebird", 1987, 1995),
            ("Chevrolet", "Venture", 1997, 2005, {"sole": True}),
            ("Pontiac", "Montana", 1999, 2005, {"sole": True}),
            ("Pontiac", "Grand Am", 1999, 2005),
            ("Oldsmobile", "Alero", 1999, 2004),
            ("Chevrolet", "Impala", 2000, 2005),
            ("Chevrolet", "Monte Carlo", 2000, 2005),
            ("Chevrolet", "Malibu", 1997, 2005),
            ("Buick", "Century", 1997, 2005, {"sole": True}),
            ("Pontiac", "Aztek", 2001, 2005, {"sole": True}),
            ("Buick", "Rendezvous", 2002, 2007),
            ("Chevrolet", "Equinox", 2005, 2009),
            ("Pontiac", "Torrent", 2006, 2009),
        ],
        "parts": {
            "alternator": {"note": "3.1/3.4 60° family shares mounts in most years — match plug & amps"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-hv-v6": {
        "display": "GM High Value 3.5/3.9 V6",
        "engine": {"liters": [3.5, 3.9], "cyl": 6},
        "apps": [
            ("Chevrolet", "Impala", 2006, 2011),
            ("Chevrolet", "Monte Carlo", 2006, 2007),
            ("Chevrolet", "Malibu", 2004, 2010),
            ("Pontiac", "G6", 2005, 2009),
            ("Chevrolet", "Uplander", 2005, 2009),
            ("Buick", "Terraza", 2005, 2007),
            ("Saturn", "Aura", 2007, 2008),
            ("Buick", "Lucerne", 2009, 2011),
        ],
        "parts": {
            "alternator": {"note": "LZ-series unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "gm-llt36": {
        "display": "GM 3.6 V6 (LY7/LLT/LFX high-feature)",
        "engine": {"liters": [3.6], "cyl": 6},
        "apps": [
            ("Chevrolet", "Traverse", 2009, 2017, {"sole": True}),
            ("GMC", "Acadia", 2007, 2016, {"sole": True}),
            ("Buick", "Enclave", 2008, 2017, {"sole": True}),
            ("Saturn", "Outlook", 2007, 2010, {"sole": True}),
            ("Chevrolet", "Impala", 2012, 2019),
            ("Chevrolet", "Impala Limited", 2014, 2016),
            ("Chevrolet", "Camaro", 2010, 2015),
            ("Chevrolet", "Equinox", 2013, 2017),
            ("GMC", "Terrain", 2013, 2017),
            ("Buick", "Lacrosse", 2010, 2016),
            ("Cadillac", "CTS", 2004, 2014),
            ("Cadillac", "SRX", 2004, 2016),
            ("Cadillac", "STS", 2005, 2011),
        ],
        "parts": {
            "alternator": {"note": "LY7 vs LLT vs LFX bracket/plug can differ by year — match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ------------------------------------------------------- Chrysler/Jeep
    "mopar-pentastar": {
        "display": "Chrysler Pentastar 3.6 V6",
        "engine": {"liters": [3.6], "cyl": 6},
        "apps": [
            ("Dodge", "Grand Caravan", 2011, 2020, {"sole": True}),
            ("Chrysler", "Town & Country", 2011, 2016, {"sole": True}),
            # The live feed spells it out — "&" squashes away, "And" doesn't.
            ("Chrysler", "Town And Country", 2011, 2016, {"sole": True}),
            ("Chrysler", "Town &amp; Country", 2011, 2016, {"sole": True}),  # raw feed HTML entity
            # feed sometimes drops the "Grand" on 2011+ Grand Caravans
            ("Dodge", "Caravan", 2011, 2019, {"sole": True}),
            ("Chrysler", "Caravan", 2011, 2019, {"sole": True}),
            ("Volkswagen", "Routan", 2011, 2014, {"sole": True}),
            ("Dodge", "Journey", 2011, 2020),
            ("Chrysler", "Journey", 2011, 2020),
            ("Dodge", "Avenger", 2011, 2014),
            ("Chrysler", "Avenger", 2011, 2014),
            ("Chrysler", "200", 2011, 2017),
            ("Dodge", "Charger", 2011, 2023),
            ("Dodge", "Challenger", 2011, 2023),
            ("Chrysler", "300", 2011, 2023),
            ("Dodge", "Durango", 2011, 2024),
            ("Jeep", "Grand Cherokee", 2011, 2021),
            ("Jeep", "Wrangler", 2012, 2018),
            ("Dodge|Ram", "Ram*", 2013, 2024),
            # Ram-branded feeds carry make "Ram" with bare "1500" models —
            # the Ram* prefix can't reach those, so they get their own apps.
            ("Ram", "1500*", 2013, 2024),
        ],
        "parts": {
            "alternator": {"note": "Pentastar unit — 160/180/220A variants and RWD vs FWD brackets; match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-world24": {
        "display": "Chrysler World/GEMA 2.4 I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Dodge", "Avenger", 2008, 2014),
            ("Chrysler", "Avenger", 2008, 2014),  # feed wrong-make rows
            ("Chrysler", "200", 2011, 2014),
            ("Dodge", "Journey", 2009, 2020),
            ("Chrysler", "Journey", 2009, 2020),  # feed wrong-make rows
            ("Dodge", "Caliber", 2007, 2012),
            ("Jeep", "Patriot", 2007, 2017),
            ("Jeep", "Compass", 2007, 2017),
            ("Chrysler", "Sebring", 2007, 2010),
        ],
        "parts": {
            "alternator": {"note": "GEMA 2.4 unit — the 15+ Tigershark 2.4 (200/Dart/Cherokee) differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-minivan": {
        "display": "Chrysler 3.3/3.8 OHV V6",
        "engine": {"liters": [3.3, 3.8], "cyl": 6},
        "apps": [
            ("Dodge", "Caravan", 1996, 2007),
            ("Dodge", "Grand Caravan", 1996, 2010),
            ("Chrysler", "Town & Country", 1996, 2010),
            ("Chrysler", "Town And Country", 1996, 2010),
            ("Plymouth|Chrysler", "Voyager", 1996, 2003),
            ("Jeep", "Wrangler", 2007, 2011),
        ],
        "parts": {
            "alternator": {"note": "3.3/3.8 share accessories in most years — match plug & amps; JK Wrangler bracket same engine"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-47": {
        "display": "Chrysler PowerTech 4.7 V8",
        "engine": {"liters": [4.7], "cyl": 8},
        "apps": [
            ("Jeep", "Grand Cherokee", 1999, 2009),
            ("Dodge", "Dakota", 2000, 2011),
            ("Dodge", "Durango", 2000, 2009),
            ("Dodge|Ram", "Ram*", 2002, 2013),
            ("Chrysler|Dodge", "Dodge 1500", 2002, 2008),  # feed alias
            ("Ram", "1500*", 2011, 2013),
            ("Jeep", "Commander", 2006, 2009),
            ("Chrysler", "Aspen", 2007, 2009),
        ],
        "parts": {
            "alternator": {"note": "4.7 PowerTech unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-37": {
        "display": "Chrysler PowerTech 3.7 V6",
        "engine": {"liters": [3.7], "cyl": 6},
        "apps": [
            ("Jeep", "Liberty", 2002, 2012),
            ("Dodge", "Dakota", 2004, 2011),
            ("Dodge|Ram", "Ram*", 2002, 2012),
            ("Ram", "1500*", 2011, 2012),
            ("Jeep", "Grand Cherokee", 2005, 2010),
            ("Dodge", "Nitro", 2007, 2011),
            ("Jeep", "Commander", 2006, 2010),
        ],
        "parts": {
            "alternator": {"note": "3.7 PowerTech unit (shares architecture with the 4.7); " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "jeep-40": {
        "display": "Jeep 4.0 I6",
        "engine": {"liters": [4.0], "cyl": 6},
        "apps": [
            ("Jeep", "Grand Cherokee", 1993, 2004),
            ("Jeep", "Cherokee", 1991, 2001),
            ("Jeep", "Wrangler", 1991, 2006),
            ("Jeep", "Comanche", 1991, 1992),
        ],
        "parts": {
            "alternator": {"note": "4.0 HO era — 91–98 vs 99–06 units differ, stay in your window; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-hemi57": {
        "display": "Chrysler 5.7 HEMI V8",
        "engine": {"liters": [5.7], "cyl": 8},
        "apps": [
            ("Dodge|Ram", "Ram*", 2003, 2024),
            ("Chrysler|Dodge", "Dodge 1500", 2003, 2008),  # feed alias
            ("Ram", "1500*", 2011, 2024),
            ("Ram", "2500*", 2011, 2024),
            ("Ram", "3500*", 2011, 2024),
            ("Dodge", "Charger", 2006, 2023),
            ("Dodge", "Challenger", 2009, 2023),
            ("Chrysler", "300", 2005, 2023),
            ("Dodge", "Magnum", 2005, 2008),
            ("Jeep", "Grand Cherokee", 2005, 2021),
            ("Dodge", "Durango", 2011, 2023),
            ("Jeep", "Commander", 2006, 2009),
            ("Chrysler", "Aspen", 2007, 2009),
        ],
        "parts": {
            "alternator": {"note": "03–08 vs 09+ Eagle HEMI accessories differ — stay in your window & match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-magnum": {
        "display": "Dodge Magnum 5.2/5.9 V8",
        "engine": {"liters": [5.2, 5.9], "cyl": 8},
        "apps": [
            ("Dodge|Ram", "Ram*", 1994, 2001),
            ("Chrysler|Dodge", "Dodge 1500", 1994, 2001),  # feed alias
            ("Dodge", "Dakota", 1992, 2003),
            ("Dodge", "Durango", 1998, 2003),
            ("Jeep", "Grand Cherokee", 1993, 1998),
        ],
        "parts": {
            "alternator": {"note": "5.2/5.9 Magnum V8 only — the 5.9 Cummins (6-cyl) is a different world; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ---------------------------------------------------------- Hyundai/Kia
    "mopar-pt24": {
        "display": "Chrysler PT Cruiser 2.4 I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Chrysler", "PT Cruiser", 2001, 2010, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "non-turbo 100A unit — the GT/Turbo (03-09) takes a different 130-145A unit, check which yours is; 2001 cars left unverified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-dart": {
        "display": "Dodge Dart 1.4T/2.0/2.4 I4",
        "engine": {"liters": [1.4, 2.0, 2.4], "cyl": 4},
        "apps": [
            ("Dodge", "Dart*", 2013, 2016, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "120A and 160A options across all three engines — match amperage; 2016 cars left unverified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-theta-mpi": {
        "display": "Hyundai/Kia Theta 2.4 MPI I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Sonata", 2006, 2010),
            ("Kia", "Optima", 2006, 2010),
            ("Kia", "Rondo", 2007, 2010),
        ],
        "parts": {
            "alternator": {"note": "port-injected Theta — the 11+ GDI unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-theta-gdi": {
        "display": "Hyundai/Kia Theta II 2.4 GDI I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Sonata", 2011, 2019),
            ("Kia", "Optima", 2011, 2020),
            ("Hyundai", "Santa Fe Sport", 2013, 2018),
            ("Kia", "Sorento", 2011, 2020),
            ("Kia", "Sportage", 2011, 2016),
            ("Hyundai", "Tucson", 2010, 2015),
        ],
        "parts": {
            "alternator": {"note": "GDI-era Theta II — port-injected 06–10 unit differs; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-nu": {
        "display": "Hyundai/Kia Nu 1.8/2.0 I4",
        "engine": {"liters": [1.8, 2.0], "cyl": 4},
        "apps": [
            ("Hyundai", "Elantra", 2011, 2020),
            ("Hyundai", "Elantra GT", 2013, 2017),
            ("Kia", "Soul", 2012, 2019),
            ("Kia", "Forte", 2014, 2018),
            ("Hyundai", "Tucson", 2016, 2021),
        ],
        "parts": {
            "alternator": {"note": "Nu family — 1.8 MPI vs 2.0 GDI variants; match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-alpha": {
        "display": "Hyundai/Kia Alpha 1.5/1.6 I4",
        "engine": {"liters": [1.5, 1.6], "cyl": 4},
        "apps": [
            ("Hyundai", "Accent", 1995, 2011, {"sole": True}),
            ("Kia", "Rio", 2001, 2011, {"sole": True}),
            ("Kia", "Rio5", 2006, 2011, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Mando and Valeo units overlap 2003-2009 — match the part number on the donor; 2012+ Accents are the Gamma 1.6 (separate family)"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-mu-lambda": {
        "display": "Hyundai 2.7/3.3/3.8 V6 (Mu/Lambda)",
        "engine": {"liters": [2.7, 3.3, 3.8], "cyl": 6},
        "apps": [
            ("Hyundai", "Santa Fe", 2007, 2009, {"sole": True}),
            ("Hyundai", "Azera", 2006, 2011, {"sole": True}),
            ("Hyundai", "Veracruz", 2007, 2012, {"sole": True}),
            ("Hyundai", "Entourage", 2007, 2008, {"sole": True}),
            ("Kia", "Sorento", 2007, 2009, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "one Denso 130A unit spans the 2.7/3.3/3.8 in 07-08 — 2009+ builds split Denso vs non-Denso vendors, match the part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-gamma16": {
        "display": "Hyundai/Kia Gamma 1.6 I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Hyundai", "Accent", 2012, 2017),
            ("Kia", "Rio", 2012, 2017),
            ("Kia", "Soul", 2012, 2019),
            ("Hyundai", "Veloster", 2012, 2017),
        ],
        "parts": {
            "alternator": {"note": "Gamma GDI unit — turbo Veloster accessories differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hk-beta20": {
        "display": "Hyundai/Kia Beta 1.8/2.0 I4",
        "engine": {"liters": [1.8, 2.0], "cyl": 4},
        "apps": [
            ("Hyundai", "Elantra", 1996, 2012),
            ("Hyundai", "Tiburon", 1997, 2008),
            ("Hyundai", "Tucson", 2005, 2009),
            ("Kia", "Sportage", 2005, 2010),
            ("Kia", "Soul", 2010, 2011),
        ],
        "parts": {
            "alternator": {"note": "Beta II unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # --------------------------------------------------------------- Subaru
    "subaru-ej25na": {
        "display": "Subaru EJ25 2.5 SOHC H4 (non-turbo)",
        "engine": {"liters": [2.5], "cyl": 4},
        "apps": [
            ("Subaru", "Outback", 2000, 2009,
             {"ambig": "XT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo"}),
            ("Subaru", "Legacy", 2000, 2009,
             {"ambig": "GT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo"}),
            ("Subaru", "Forester", 1999, 2010,
             {"ambig": "XT models are the turbo EJ255 — same 2.5 decode string; confirm non-turbo"}),
            ("Subaru", "Impreza", 2006, 2011,
             {"ambig": "WRX/turbo models share the 2.5 decode string; confirm non-turbo"}),
            ("Subaru", "Baja", 2003, 2006,
             {"ambig": "Baja Turbo shares the 2.5 decode string; confirm non-turbo"}),
        ],
        "parts": {
            "alternator": {"note": "NA SOHC EJ25 unit — turbo cars route differently; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "subaru-ej25t": {
        "display": "Subaru EJ255/EJ257 2.5 turbo H4",
        "engine": {"liters": [2.5], "cyl": 4},
        "apps": [
            ("Subaru", "Impreza", 2006, 2014,
             {"ambig": "only WRX/STI trims carry the turbo EJ — confirm turbo before buying"}),
            ("Subaru", "WRX", 2008, 2014, {"sole": True}),
            ("Subaru", "Impreza WRX", 2006, 2014, {"sole": True}),
            ("Subaru", "Forester", 2004, 2013,
             {"ambig": "only XT trims are turbo — confirm before buying"}),
            ("Subaru", "Legacy", 2005, 2012,
             {"ambig": "only GT trims are turbo — confirm before buying"}),
            ("Subaru", "Outback", 2005, 2009,
             {"ambig": "only XT trims are turbo — confirm before buying"}),
            ("Subaru", "Baja", 2004, 2006,
             {"ambig": "only Baja Turbo is turbo — confirm before buying"}),
        ],
        "parts": {
            "alternator": {"note": "turbo EJ unit; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "subaru-fb25": {
        "display": "Subaru FB25 2.5 H4",
        "engine": {"liters": [2.5], "cyl": 4},
        "apps": [
            ("Subaru", "Forester", 2011, 2018,
             {"ambig": "11–13 XT is the turbo EJ255 — same 2.5 decode string; confirm FB non-turbo"}),
            ("Subaru", "Outback", 2013, 2019, {"sole": True}),
            ("Subaru", "Legacy", 2013, 2019, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "FB25 unit — the EJ-era unit does NOT carry over; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "subaru-fa20dit": {
        "display": "Subaru FA20DIT 2.0 turbo H4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Subaru", "WRX", 2015, 2021, {"sole": True}),
            ("Subaru", "Forester", 2014, 2018,
             {"ambig": "only 2.0XT trims carry the FA20DIT — base Foresters are the 2.5 FB; confirm turbo"}),
        ],
        "parts": {
            "alternator": {"note": "FA20DIT unit — the NA FA20 (BRZ) and FB engines differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ---------------------------------------------------------------- Euro
    "mini-r50": {
        "display": "MINI Cooper 1.6 (R50/R52/R53)",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("MINI", "Cooper", 2002, 2006),
        ],
        "parts": {
            "alternator": {"note": "W10 (base) and W11 (supercharged S) use different units — check which yours is; 2007+ hardtops are the newer N-series engine (not this family)"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ------------------------------------------------------------------ VW
    "vw-25": {
        "display": "VW 2.5 I5",
        "engine": {"liters": [2.5], "cyl": 5},
        "apps": [
            ("Volkswagen", "Jetta", 2005, 2014),
            ("Volkswagen", "Rabbit", 2006, 2009, {"sole": True}),
            ("Volkswagen", "Golf", 2010, 2014),
            ("Volkswagen", "Beetle", 2012, 2014),
            ("Volkswagen", "Passat", 2012, 2014),
        ],
        "parts": {
            "alternator": {"note": "5-cyl unit (the decode's '5-cyl' is the tell); " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ================= 2026-10 PHASE A — enthusiast platforms =============
    # ------------------------------------------------------------- Toyota
    "toyota-4a": {
        "display": "Toyota 4A/7A 1.6/1.8 I4 (Corolla era)",
        "engine": {"liters": [1.6, 1.8], "cyl": 4},
        "apps": [
            ("Toyota", "Corolla", 1985, 1997, {"sole": True}),
            ("Geo|Chevrolet", "Prizm", 1989, 1997, {"sole": True}),
            ("Toyota", "Celica", 1990, 1999),
        ],
        "parts": {
            "alternator": {"note": "4A-F/4A-FE/7A-FE share published units per year span; the twin-cam 4A-GE (85-89) uses its own — match part number on a GT-S"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-3s": {
        "display": "Toyota 2S/3S 2.0 I4 (Celica/MR2 Turbo)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Toyota", "Celica", 1986, 1993),
            ("Toyota", "MR2", 1991, 1995),
        ],
        "parts": {
            "alternator": {"note": "2.0 (2S/3S-FE/3S-GE/3S-GTE) unit — the 1.6 and 2.2 Celica units differ; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-m6": {
        "display": "Toyota 5M/7M 2.8/3.0 I6 (Supra MK3/Cressida)",
        "engine": {"liters": [2.8, 3.0], "cyl": 6},
        "apps": [
            ("Toyota", "Supra", 1986, 1992, {"sole": True}),
            ("Toyota", "Cressida", 1985, 1992, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Supra rows split by turbo and transmission — Supra pairs stay Likely; Cressida rows anchor the verified groups"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-2jz": {
        "display": "Toyota/Lexus 2JZ 3.0 I6 (Supra MK4/SC/GS/IS)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Toyota", "Supra", 1993, 1998, {"sole": True}),
            ("Lexus", "SC300", 1992, 2000, {"sole": True}),
            ("Lexus", "GS300", 1993, 2005, {"sole": True}),
            ("Lexus", "IS300", 2001, 2005, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Supra NA (2JZ-GE) and twin-turbo (GTE) alternators differ, and the turbo splits again by transmission — Supra pairs stay Likely; Lexus GE units anchor the verified groups"},
            "starter": {"note": "the 93-98 Supra, 95-00 SC300 and 93-97 GS300 share one published starter — " + _STR_NOTE},
        },
    },
    # -------------------------------------------------------------- Honda
    "honda-d-ef": {
        "display": "Honda D15/D16 1.5/1.6 I4 (EF Civic/CRX)",
        "engine": {"liters": [1.5, 1.6], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 1988, 1991, {"sole": True}),
            ("Honda", "CRX", 1988, 1991, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "88-89 rows are vendor-split (Denso vs Mitsubishi source) — match the unit on your car; 90-91 is one published unit"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-d-eg": {
        "display": "Honda D15/D16 1.5/1.6 I4 (EG Civic/Del Sol)",
        "engine": {"liters": [1.5, 1.6], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 1992, 1995, {"sole": True}),
            ("Honda", "Civic Del Sol", 1993, 1995,
             {"ambig": "VTEC (B16A3 1.6 DOHC) Del Sols use a different unit — this family covers the D-series singles-cam cars; confirm the engine code"}),
            ("Honda", "Del Sol", 1993, 1995,
             {"ambig": "VTEC (B16A3 1.6 DOHC) Del Sols use a different unit — this family covers the D-series single-cam cars; confirm the engine code"}),
        ],
        "parts": {
            "alternator": {"note": "D15 rows are one unit; the D16Z6 is dual-sourced (Denso 210-0213 / Mitsubishi 210-4133, identical spans) — match the vendor tag on a 1.6"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-b18": {
        "display": "Honda/Acura B17/B18 1.7/1.8 I4 (Integra)",
        "engine": {"liters": [1.7, 1.8], "cyl": 4},
        "apps": [
            ("Acura", "Integra", 1990, 2001, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "96-01: the Type R (B18C5) uses Denso 210-4190 — every other trim shares 210-0199; match part number on a 96+ car"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-k20": {
        "display": "Honda/Acura K20 2.0 I4 (Civic Si/RSX)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Honda", "Civic", 2002, 2011),
            ("Acura", "RSX", 2002, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "RSX splits by trim (Type S 210-0507 vs base 210-4168) — RSX pairs stay Likely; Civic Si spans anchor the verified groups"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-f20c": {
        "display": "Honda F20C/F22C 2.0/2.2 I4 (S2000)",
        "engine": {"liters": [2.0, 2.2], "cyl": 4},
        "apps": [
            ("Honda", "S2000", 2000, 2009, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "AP1 (2.0, 00-03) and AP2 (2.2, 04-09) units differ; 06-09 is the same F22C1 as 04-05 but past this catalog edition — verify part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "honda-h22": {
        "display": "Honda H22/H23/F22 2.2/2.3 I4 (Prelude)",
        "engine": {"liters": [2.2, 2.3], "cyl": 4},
        "apps": [
            ("Honda", "Prelude", 1992, 2001, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "92-96 splits three ways (F22A1 non-VTEC / H22A1 VTEC / H23A1 2.3) — those pairs stay Likely; 97+ H22A4 spans are verified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # -------------------------------------------------------------- Mazda
    "mazda-miata-16": {
        "display": "Mazda B6 1.6 I4 (Miata NA)",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Mazda", "Miata", 1990, 1993, {"sole": True}),
            ("Mazda", "MX-5*", 1990, 1993, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "91-93 rows split by transmission (M/T 210-4184 / A/T 210-4270) — match yours; 1990 is one unit"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mazda-miata-18": {
        "display": "Mazda BP 1.8 I4 (Miata NA/NB)",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Mazda", "Miata", 1994, 2005, {"sole": True}),
            ("Mazda", "MX-5*", 1994, 2005, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "94-97 (NA8) splits by transmission — match yours; 99-00 and 01-05 NB units are year-split, match amps"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mazda-miata-nc": {
        "display": "Mazda MZR 2.0 I4 (Miata NC)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Mazda", "Miata", 2006, 2015, {"sole": True}),
            ("Mazda", "MX-5*", 2006, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "06-08 (NC1) and 09-12 (NC2) units differ; 13-15 is past this catalog edition — verify part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mazda-rx7": {
        "display": "Mazda 13B rotary (RX-7)",
        "engine": {"liters": [1.3], "cyl": 2},
        "apps": [
            ("Mazda", "RX-7", 1986, 1995, {"sole": True}),
            ("Mazda", "RX7", 1986, 1995, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "FD (93-95) is one published unit; FC turbo (86-88) has its own and 89-92 FC rows aren't published in this catalog — match part number on an FC"},
            "starter": {"note": "FC starters split by transmission — match part number"},
        },
    },
    "mazda-rx8": {
        "display": "Mazda 13B-MSP Renesis rotary (RX-8)",
        "engine": {"liters": [1.3], "cyl": 2},
        "apps": [
            ("Mazda", "RX-8", 2004, 2011, {"sole": True}),
            ("Mazda", "RX8", 2004, 2011, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "05-07 and 09-11 are year-split units; early-build 2004 and the 2008 model year aren't cleanly published — verify part number on those"},
            "starter": {"note": "most rows split by transmission — match part number"},
        },
    },
    # ------------------------------------------------------------- Nissan
    "nissan-z32": {
        "display": "Nissan VG30DE/DETT 3.0 V6 (300ZX Z32)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Nissan", "300ZX", 1990, 1996, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "NA (VG30DE) and twin-turbo (VG30DETT) alternators differ and the decode can't tell them apart — all pairs stay Likely; match part number"},
            "starter": {"note": "one published starter covers every 90-96 Z32, NA and twin-turbo"},
        },
    },
    "nissan-vq-hr": {
        "display": "Nissan/Infiniti VQ35HR/VQ37VHR 3.5/3.7 V6",
        "engine": {"liters": [3.5, 3.7], "cyl": 6},
        "apps": [
            ("Nissan", "350Z", 2007, 2009, {"sole": True}),
            ("Nissan", "370Z", 2009, 2020, {"sole": True}),
            ("Infiniti", "G35", 2007, 2008, {"sole": True}),
            ("Infiniti", "G37", 2008, 2013, {"sole": True}),
            ("Infiniti", "M35", 2009, 2010, {"sole": True}),
            ("Infiniti", "Q50", 2014, 2019),
        ],
        "parts": {
            "alternator": {"note": "one 150A unit spans the HR cars (350Z 07-09, G35 07-08, G37 08-10, early 370Z); late 370Z (from 02/2010) revises it — match part number there"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ---------------------------------------------------------- Mitsubishi
    "mitsu-dsm": {
        "display": "Mitsubishi 4G63/420A 1.8/2.0 I4 (DSM Eclipse/Talon)",
        "engine": {"liters": [1.8, 2.0], "cyl": 4},
        "apps": [
            ("Mitsubishi", "Eclipse", 1990, 1995, {"sole": True}),
            ("Mitsubishi", "Eclipse", 1996, 1999),
            ("Eagle", "Talon", 1990, 1998, {"sole": True}),
            ("Plymouth", "Laser", 1990, 1994, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "90-98 rows split by transmission and turbo — match part number; 1999 is one published unit for 420A and 4G63 turbo alike"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mitsu-24": {
        "display": "Mitsubishi 4G64/4G69 2.4 I4",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Mitsubishi", "Eclipse", 2000, 2012),
            ("Mitsubishi", "Galant", 1994, 2012),
            ("Mitsubishi", "Lancer", 2005, 2017),
            ("Mitsubishi", "Outlander", 2003, 2006, {"sole": True}),
            ("Mitsubishi", "Outlander", 2007, 2013),
            ("Mitsubishi", "Outlander Sport", 2015, 2017),
        ],
        "parts": {
            "alternator": {"note": "one published 110A unit spans Eclipse 06-11, Galant 04-11 and Lancer 2.4 05-06; earlier Galant spans are year-split — match amps"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mitsu-6g72": {
        "display": "Mitsubishi 6G72 3.0 V6 (Eclipse/Galant)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Mitsubishi", "Eclipse", 2000, 2005),
            ("Mitsubishi", "Galant", 1999, 2003),
            ("Chrysler", "Sebring", 2001, 2005),
            ("Dodge", "Stratus", 2001, 2005),
            ("Mitsubishi", "Montero Sport", 1997, 2004),
        ],
        "parts": {
            "alternator": {"note": "one published 85A unit spans the 3.0 Eclipse and Galant; " + _ALT_NOTE},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mitsu-6g75": {
        "display": "Mitsubishi 6G75 3.8 V6 (Eclipse/Galant)",
        "engine": {"liters": [3.8], "cyl": 6},
        "apps": [
            ("Mitsubishi", "Eclipse", 2006, 2012),
            ("Mitsubishi", "Galant", 2004, 2009),
            ("Mitsubishi", "Endeavor", 2004, 2011, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "one published 110A unit spans Eclipse 06-11 and Galant 05-09; the 2004 Galant 3.8 unit is its own — match part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mitsu-evo": {
        "display": "Mitsubishi Evo 2.0 turbo I4 (4G63T/4B11T)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Mitsubishi", "Lancer Evolution", 2003, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Evo VIII/IX (4G63T, 03-06) and Evo X (4B11T, 08-15) units differ; 12-15 is past this catalog edition — verify part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # -------------------------------------------------------------- Subaru
    "subaru-ej205": {
        "display": "Subaru EJ205 2.0 turbo H4 (WRX 02-05)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Subaru", "WRX", 2002, 2005, {"sole": True}),
            ("Subaru", "Impreza WRX", 2002, 2005, {"sole": True}),
            ("Subaru", "Impreza", 2002, 2005,
             {"ambig": "only WRX trims carry the 2.0 turbo — confirm turbo before buying"}),
        ],
        "parts": {
            "alternator": {"note": "one published 75A unit spans every 02-05 EJ205 WRX; " + _ALT_NOTE},
            "starter": {"note": "02-05 WRX starters split by transmission — match part number"},
        },
    },
    # ----------------------------------------------------------------- BMW
    "bmw-m52": {
        "display": "BMW M50/M52/S50/S52 I6 (E36/E39/Z3)",
        "engine": {"liters": [2.5, 2.8, 3.0, 3.2], "cyl": 6},
        "apps": [
            ("BMW", "3 Series", 1992, 1999),
            ("BMW", "325i", 1992, 1995),
            ("BMW", "325is", 1992, 1995),
            ("BMW", "328i", 1996, 1999),
            ("BMW", "328is", 1996, 1998),
            ("BMW", "323i", 1998, 1999),
            ("BMW", "323is", 1998, 1999),
            ("BMW", "M3", 1995, 1999, {"sole": True}),
            ("BMW", "Z3", 1996, 2002),
            ("BMW", "525i", 1992, 1995),
            ("BMW", "528i", 1997, 2000),
        ],
        "parts": {
            "alternator": {"note": "most E36-era rows are case-size or OEM-number qualified (Bosch vs Valeo sourcing) — match the tag on your unit; the 528i 97-98 140A unit is the clean published span"},
            "starter": {"note": "one published starter covers M3 96-99 and every Z3 96-02"},
        },
    },
    "bmw-m54": {
        "display": "BMW M54 2.5/3.0 I6 (E46/E39/E53/E85)",
        "engine": {"liters": [2.5, 3.0], "cyl": 6},
        "apps": [
            ("BMW", "3 Series", 2000, 2006),
            ("BMW", "325i", 2001, 2006),
            ("BMW", "325ci", 2001, 2006),
            ("BMW", "325xi", 2001, 2006),
            ("BMW", "330i", 2001, 2006),
            ("BMW", "330ci", 2001, 2006),
            ("BMW", "330xi", 2001, 2006),
            ("BMW", "525i", 2001, 2003),
            ("BMW", "530i", 2001, 2003),
            ("BMW", "X3", 2004, 2006),
            ("BMW", "X5", 2001, 2006),
            ("BMW", "Z4", 2003, 2005),
        ],
        "parts": {
            "alternator": {"note": "every published M54 alternator row is OEM-number qualified (Bosch vs Valeo split) — all pairs stay Likely; match the number stamped on your unit"},
            "starter": {"note": "the 3.0 X5 starter span is the published anchor; " + _STR_NOTE},
        },
    },
    # ------------------------------------------------------------------ VW
    "vw-20t": {
        "display": "VW 2.0T EA113/EA888 I4 (GTI/Jetta)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Volkswagen", "GTI", 2006, 2014, {"sole": True}),
            ("Volkswagen", "Jetta", 2006, 2013),
            ("Volkswagen", "Passat", 2006, 2010),
            ("Volkswagen", "CC", 2009, 2017),
            ("Volkswagen", "Tiguan", 2009, 2017, {"sole": True}),
            ("Volkswagen", "Eos", 2007, 2016),
        ],
        "parts": {
            "alternator": {"note": "every published 2.0T alternator row is vendor-qualified (Bosch vs Valeo) — all pairs stay Likely; match the unit on your car"},
            "starter": {"note": "GTI 06-09 and 10-11 starters are clean published spans; Jetta rows split by fuel/transmission — match part number"},
        },
    },
    # ---------------------------------------------------------- Ford perf
    "ford-46-3v": {
        "display": "Ford 4.6 3V Modular V8 (Mustang GT S197)",
        "engine": {"liters": [4.6], "cyl": 8},
        "apps": [
            ("Ford", "Mustang", 2005, 2010),
        ],
        "parts": {
            "alternator": {"note": "05 and 06-08 are year-split units; 09-10 rows split by transmission — match part number there"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-coyote": {
        "display": "Ford Coyote 5.0 V8 (Mustang GT/F-150)",
        "engine": {"liters": [5.0], "cyl": 8},
        "apps": [
            ("Ford", "Mustang", 2011, 2023),
            ("Ford", "F-150", 2011, 2023),
            ("Ford", "F150*", 2011, 2023),
        ],
        "parts": {
            "alternator": {"note": "11-14 Mustang rows split by transmission except the 12-13 150A unit; 15+ is past this catalog edition — verify part number"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-essex38": {
        "display": "Ford Essex 3.8/3.9 V6 (Mustang SN95)",
        "engine": {"liters": [3.8, 3.9], "cyl": 6},
        "apps": [
            ("Ford", "Mustang", 1994, 2004),
        ],
        "parts": {
            "alternator": {"note": "94-00 lists two interchangeable published units (210-5207/210-5310) — match yours; 01-04 is one unit"},
            "starter": {"note": _STR_NOTE},
        },
    },
    # ------------------------------------------------------------- GM perf
    "gm-fbody-tpi": {
        "display": "GM 5.0/5.7 TBI/TPI V8 (F-body/C4 Corvette)",
        "engine": {"liters": [5.0, 5.7], "cyl": 8},
        "apps": [
            ("Chevrolet", "Camaro", 1982, 1992),
            ("Pontiac", "Firebird", 1982, 1992),
            ("Chevrolet", "Corvette", 1985, 1991, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Camaro/Firebird 5.0 and 5.7 share the published unit within each span; C4 Corvette alternator rows aren't published in this catalog — Corvette pairs stay Likely"},
            "starter": {"note": "5.0 and 5.7 starters differ — match displacement and part number"},
        },
    },
    "gm-fbody-lt1": {
        "display": "GM LT1 5.7 V8 (F-body/C4 Corvette)",
        "engine": {"liters": [5.7], "cyl": 8},
        "apps": [
            ("Chevrolet", "Camaro", 1993, 1997),
            ("Pontiac", "Firebird", 1993, 1997),
            ("Chevrolet", "Corvette", 1992, 1996, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "LT1 alternator rows aren't published in this catalog (Delco CS-series cars) — all pairs stay Likely; match the CS130/CS144 number on your unit"},
            "starter": {"note": "90-95 Corvette rows exclude the ZR1 — a ZR1 needs its own number"},
        },
    },
    "gm-ls1-car": {
        "display": "GM LS1/LS6 5.7 V8 (F-body/C5 Corvette)",
        "engine": {"liters": [5.7], "cyl": 8},
        "apps": [
            ("Chevrolet", "Camaro", 1998, 2002),
            ("Pontiac", "Firebird", 1998, 2002),
            ("Chevrolet", "Corvette", 1997, 2004, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Camaro and Firebird share one published 102A unit; C5 alternator rows are published for 2004 only (03 splits by transmission) — match part number on a C5"},
            "starter": {"note": "one published starter covers LS1 F-bodies 98-01 and the C5 97-01"},
        },
    },
    "gm-corvette-c6": {
        "display": "GM Gen IV LS V8 (Corvette C6/Camaro SS)",
        "engine": {"liters": [6.0, 6.2, 7.0], "cyl": 8},
        "apps": [
            ("Chevrolet", "Corvette", 2005, 2013, {"sole": True}),
            ("Chevrolet", "Camaro", 2010, 2015),
        ],
        "parts": {
            "alternator": {"note": "one published 145A unit spans Corvette 05-12 incl. the Z06 7.0; the supercharged ZR1 (09-13) uses its own — ZR1 years stay out of the verified span; Camaro SS 12-13 is its own published unit"},
            "starter": {"note": "one published starter covers every 06-13 Corvette incl. ZR1"},
        },
    },
    # ================= 2026-10 PHASE B — high-volume commuters =============
    "nissan-ga16": {
        "display": "Nissan GA16DE 1.6 I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Nissan", "Sentra", 1995, 1999),
            ("Nissan", "200SX", 1995, 1998),
        ],
        "parts": {
            "alternator": {"note": "one published unit per era (95-96, 97-99); SE-R SR20 cars are a different engine"},
            "starter": {"note": "every published starter row splits M/T vs A/T and California — all pairs stay Likely"},
        },
    },
    "nissan-qg18": {
        "display": "Nissan QG18DE 1.8 I4",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Nissan", "Sentra", 2000, 2006),
        ],
        "parts": {
            "alternator": {"note": "clean published spans 00-01 and 02-06"},
            "starter": {"note": "clean published spans 00-01, 03-05 and 06"},
        },
    },
    "nissan-vg30-maxima": {
        "display": "Nissan VG30E/VE30DE 3.0 V6 (Maxima)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Nissan", "Maxima", 1989, 1994),
        ],
        "parts": {
            "alternator": {"note": "89-91 is one published unit; 92-94 splits SOHC (VG30E) vs DOHC (VE30DE) and stays Likely"},
            "starter": {"note": "89-91 is one published unit; 92-94 DOHC A/T cars take a different starter"},
        },
    },
    "nissan-vq30": {
        "display": "Nissan VQ30DE 3.0 V6 (Maxima/I30)",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Nissan", "Maxima", 1995, 2001, {"sole": True}),
            ("Infiniti", "I30", 1996, 2001, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "95-97 one unit (Maxima + I30); 98-01 splits by trim some years — see verified groups"},
            "starter": {"note": "ONE published starter covers every 95-01 Maxima and 96-01 I30"},
        },
    },
    "nissan-vg33": {
        "display": "Nissan VG33E 3.3 V6 (Pathfinder/Xterra/Frontier)",
        "engine": {"liters": [3.3], "cyl": 6},
        "apps": [
            ("Nissan", "Pathfinder", 1996, 2000, {"sole": True}),
            ("Infiniti", "QX4*", 1997, 2000, {"sole": True}),
            ("Nissan", "Xterra", 2000, 2004),
            ("Nissan", "Frontier", 1999, 2004),
            ("Nissan", "Quest", 1999, 2002, {"sole": True}),
            ("Mercury", "Villager", 1999, 2002, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Pathfinder 98-00 one unit (97 split by production date); Xterra/Frontier 03-04 one unit incl. the supercharged VG33ER"},
            "starter": {"note": "one unit covers Pathfinder 96-00; another covers Xterra/Frontier 99-04"},
        },
    },
    "honda-b20": {
        "display": "Honda B20 2.0 I4 (CR-V)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Honda", "CR-V", 1997, 2001, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "97-98 one published unit; 99-01 splits M/T vs A/T and stays Likely"},
            "starter": {"note": "97 unqualified; 98-01 splits M/T vs A/T"},
        },
    },
    "gm-ecotec-lcv": {
        "display": "GM Ecotec Gen3 2.0T/2.4/2.5 I4 (Malibu 8th gen)",
        "engine": {"liters": [2.0, 2.4, 2.5], "cyl": 4},
        "apps": [
            ("Chevrolet", "Malibu", 2013, 2015, {"sole": True}),
            ("Chevrolet", "Malibu Limited", 2016, 2016, {"sole": True}),
            ("Chevrolet", "Impala", 2014, 2015),
        ],
        "parts": {
            "alternator": {"note": "2013 Malibu ships one published alternator across 2.0T, 2.4 eAssist and 2.5; 14-15 rows are beyond this catalog edition"},
            "starter": {"note": "2013 2.0T/2.5 share one published starter"},
        },
    },
    "gm-atlas-i45": {
        "display": "GM Atlas I4/I5 2.8/2.9/3.5/3.7 (Colorado/Canyon)",
        "engine": {"liters": [2.8, 2.9, 3.5, 3.7], "cyl": 5},
        "apps": [
            ("Chevrolet", "Colorado", 2004, 2008, {"sole": True}),
            ("GMC", "Canyon", 2004, 2008, {"sole": True}),
            ("Chevrolet", "Colorado", 2009, 2012),
            ("GMC", "Canyon", 2009, 2012),
            ("Hummer", "H3*", 2006, 2010),
        ],
        "parts": {
            "alternator": {"note": "04-06 2.8/3.5 share one published unit; 07-09 2.9/3.7 share another — both across Colorado and Canyon"},
            "starter": {"note": "08-12 2.9/3.7 share one published unit (Canyon 2.9 published from 09)"},
        },
    },
    "hyundai-santafe1": {
        "display": "Hyundai Santa Fe 2.4/2.7/3.5 (1st gen)",
        "engine": {"liters": [2.4, 2.7, 3.5], "cyl": 6},
        "apps": [
            ("Hyundai", "Santa Fe", 2001, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2.7 02-04 and 2.4 01-04 each have one clean unit, but the mixed-engine years keep cross-engine spans at Likely; 05 rows are dual-sourced"},
            "starter": {"note": "one published starter covers ALL 05-06 engines; the same unit covers 2.7 back to 01 and 3.5 back to 03, but 2.4 03-04 splits M/T vs A/T, so earlier years stay Likely"},
        },
    },
    "toyota-1nz": {
        "display": "Toyota 1NZ-FE 1.5 I4 (Yaris/Echo/xA/xB)",
        "engine": {"liters": [1.5], "cyl": 4},
        "apps": [
            ("Toyota", "Yaris", 2007, 2015, {"sole": True}),
            ("Toyota", "Echo", 2000, 2005, {"sole": True}),
            ("Scion", "xA", 2004, 2006, {"sole": True}),
            ("Scion", "xB", 2004, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Yaris 07-09 and 10-14 each one published unit; Echo/xA/xB rows are not in this catalog edition"},
            "starter": {"note": "Yaris 12 and 13-15 published clean; 07-11 splits M/T vs A/T"},
        },
    },
    "honda-l15": {
        "display": "Honda L15 1.5 I4 (Fit)",
        "engine": {"liters": [1.5], "cyl": 4},
        "apps": [
            ("Honda", "Fit", 2007, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "07-08 one published unit; 2015 splits CVT vs M/T"},
            "starter": {"note": "07-08 and 10-13 each one published unit; 2009 was dual-sourced between the two — match your part number"},
        },
    },
    "kia-spectra": {
        "display": "Kia Spectra 1.8/2.0 I4",
        "engine": {"liters": [1.8, 2.0], "cyl": 4},
        "apps": [
            ("Kia", "Spectra", 2000, 2009, {"sole": True}),
            ("Kia", "Spectra5", 2005, 2009, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "1.8 00-01 and 2.0 08-09 publish clean; 05-07 splits Valeo vs Mando vendor"},
            "starter": {"note": "every published row splits M/T vs A/T — all pairs stay Likely"},
        },
    },
    "kia-forte1": {
        "display": "Kia Forte 1.6T/2.0/2.4 I4",
        "engine": {"liters": [1.6, 2.0, 2.4], "cyl": 4},
        "apps": [
            ("Kia", "Forte", 2010, 2015),
            ("Kia", "Forte Koup", 2010, 2015, {"sole": True}),
            ("Kia", "Forte5", 2010, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "Koup 10-13 publishes one clean unit for 2.0 and 2.4; sedan 2.0 splits hydraulic vs electric power steering"},
            "starter": {"note": "Koup 14-15 publishes one clean unit (1.6T and 2.0); 10-11 rows split by build date"},
        },
    },
    "mazda-cx7": {
        "display": "Mazda CX-7 2.3T/2.5",
        "engine": {"liters": [2.3, 2.5], "cyl": 4},
        "apps": [
            ("Mazda", "CX-7", 2007, 2012, {"sole": True}),
            ("Mazda", "CX7", 2007, 2012, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers 2.3T 07-11 and 2.5 10-11"},
            "starter": {"note": "07-09 one unit; 2011 (both engines) another; 2010/2012 rows absent from this edition"},
        },
    },
    "mazda-cx9": {
        "display": "Mazda CX-9 3.5/3.7 V6",
        "engine": {"liters": [3.5, 3.7], "cyl": 6},
        "apps": [
            ("Mazda", "CX-9", 2007, 2015, {"sole": True}),
            ("Mazda", "CX9", 2007, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers 3.5 (07) and 3.7 (08-11)"},
            "starter": {"note": "07-09 one unit; 10-12 another"},
        },
    },
    "mopar-pacifica": {
        "display": "Chrysler Pacifica 3.5/3.8/4.0 V6",
        "engine": {"liters": [3.5, 3.8, 4.0], "cyl": 6},
        "apps": [
            ("Chrysler", "Pacifica*", 2004, 2008, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "04 (3.5-only year) publishes clean; 07-08 units differ 3.8 vs 4.0 so those years stay Likely across engines"},
            "starter": {"note": "2005 (3.5 and 3.8) shares one published unit; 06-08 splits by engine"},
        },
    },
    "ford-mod-sd": {
        "display": "Ford Modular 4.6/5.4 V8 (Super Duty/E-Series/Navigator)",
        "engine": {"liters": [4.6, 5.4], "cyl": 8},
        "apps": [
            ("Ford", "F-250*", 1999, 2010),
            ("Ford", "F250*", 1999, 2010),
            ("Ford", "F-350*", 1999, 2010),
            ("Ford", "F350*", 1999, 2010),
            ("Ford", "Excursion", 2000, 2005),
            ("Ford", "E-150*", 1997, 2014),
            ("Ford", "E150*", 1997, 2014),
            ("Ford", "E-250*", 1997, 2014),
            ("Ford", "E-350*", 1997, 2014),
            ("Ford", "E-Series", 1997, 2014),
            ("Ford", "Econoline*", 1997, 2014),
            ("Lincoln", "Navigator*", 1998, 2014, {"sole": True}),
            ("Ford", "Navigator*", 1998, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "most van/SD rows split by case diameter and battery-post options — see the few clean verified spans; diesels are separate units entirely"},
            "starter": {"note": "ONE published gas starter covers F-250 Super Duty 5.4/V10 99-08, another covers E-150 4.6/5.4 97-12, and Navigator 99-14 is one unit"},
        },
    },
    "vw-b5-v6": {
        "display": "VW/Audi B5 V6 2.8/3.0 (Passat/A4)",
        "engine": {"liters": [2.8, 3.0], "cyl": 6},
        "apps": [
            ("Volkswagen", "Passat*", 1998, 2005),
            ("Audi", "A4", 1996, 2006),
            ("Audi", "A4 Quattro", 1996, 2006),
            ("Audi", "A4 Avant", 1996, 2006),
        ],
        "parts": {
            "alternator": {"note": "every published alternator row carries Bosch/Valeo vendor qualifiers — all pairs stay Likely"},
            "starter": {"note": "ONE published starter covers Passat 2.8 00-05, A4 2.8 00-01 and A4 3.0 02-06"},
        },
    },
    "vw-b5-18t": {
        "display": "VW/Audi 1.8T I4 (Passat/A4 longitudinal)",
        "engine": {"liters": [1.8], "cyl": 4},
        "apps": [
            ("Volkswagen", "Passat*", 1997, 2005),
            ("Audi", "A4", 1997, 2006),
            ("Audi", "A4 Quattro", 1997, 2006),
            ("Audi", "A4 Avant", 1997, 2006),
        ],
        "parts": {
            "alternator": {"note": "every published alternator row carries Bosch/Valeo vendor qualifiers — all pairs stay Likely"},
            "starter": {"note": "one published unit covers Passat 1.8T 02-04 and A4 1.8T 04 (05 splits by chassis number)"},
        },
    },
    "gm-aveo": {
        "display": "Chevrolet Aveo 1.6 I4",
        "engine": {"liters": [1.6], "cyl": 4},
        "apps": [
            ("Chevrolet", "Aveo", 2004, 2011, {"sole": True}),
            ("Chevrolet", "Aveo5", 2006, 2011, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "no unqualified alternator rows in this catalog edition — pairs stay Likely"},
            "starter": {"note": "04-08 one published unit; 10-11 another (2009 rows absent)"},
        },
    },
    "kia-sedona1": {
        "display": "Kia Sedona 3.5/3.8 V6",
        "engine": {"liters": [3.5, 3.8], "cyl": 6},
        "apps": [
            ("Kia", "Sedona", 2002, 2012, {"sole": True}),
            ("Kia", "Sedona", 2014, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "02-05, 06-07 and 11-12/14 each publish one clean unit; 08-09 splits by rear-DVD option"},
            "starter": {"note": "02-05 and 06-07 each one unit; 08-12 one number spans both engines (a second number was dual-sourced 08-12 — match yours)"},
        },
    },
    "kia-sorento1": {
        "display": "Kia Sorento 3.5 V6 (1st gen)",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Kia", "Sorento", 2003, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers all 03-06"},
            "starter": {"note": "ONE published unit covers all 03-06"},
        },
    },
    "ford-focus3": {
        "display": "Ford Focus 2.0 I4 (Mk3)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Ford", "Focus", 2012, 2018),
        ],
        "parts": {
            "alternator": {"note": "2012+ alternator rows are not published unqualified in this catalog edition — pairs stay Likely"},
            "starter": {"note": "ONE published starter covers 12-14 across both 2.0 VIN codes (GDI and ST turbo)"},
        },
    },
    "hk-delta27": {
        "display": "Hyundai/Kia Delta 2.7 V6",
        "engine": {"liters": [2.7], "cyl": 6},
        "apps": [
            ("Hyundai", "Tucson", 2005, 2009),
            ("Hyundai", "Tiburon", 2003, 2008),
            ("Kia", "Sportage", 2005, 2010),
            ("Hyundai", "Sonata", 1999, 2005),
            ("Kia", "Optima", 2001, 2006),
            ("Hyundai", "Santa Fe", 2001, 2006),
        ],
        "parts": {
            "alternator": {"note": "one published 120A unit covers the 05+ 2.7s across Tucson/Tiburon/Sportage/Sonata/Santa Fe"},
            "starter": {"note": "ONE published starter covers the 2.7 across six models and up to a decade — see the verified group"},
        },
    },
    "hk-sirius24": {
        "display": "Hyundai/Kia Sirius 2.4 I4 (Sonata/Optima)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Sonata", 1999, 2005),
            ("Kia", "Optima", 2001, 2006),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers Sonata 2.4 99-05 and Optima 2.4 01-06"},
            "starter": {"note": "every published row splits M/T vs A/T — pairs stay Likely"},
        },
    },
    "hk-theta24": {
        "display": "Hyundai/Kia Theta 2.4 I4 (Sonata/Optima NF)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Sonata", 2006, 2010),
            ("Kia", "Optima", 2006, 2010),
        ],
        "parts": {
            "alternator": {"note": "one published unit covers Sonata 06-08 and Optima 06-10; Sonata 09-10 rows are option-qualified"},
            "starter": {"note": "ONE published starter covers Sonata 06-08; Optima rows split by transmission — those pairs stay Likely"},
        },
    },
    "hk-theta2gdi": {
        "display": "Hyundai/Kia Theta-II 2.0T/2.4 GDI (Sonata/Optima)",
        "engine": {"liters": [2.0, 2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Sonata", 2011, 2014, {"sole": True}),
            ("Kia", "Optima", 2011, 2015, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "one published unit covers Sonata 2014 (both engines) + 2.0T 11-13 and Optima 12-13; Sonata 2.4 11-13 rows aren't published — those pairs stay Likely"},
            "starter": {"note": "starters were dual-sourced (Denso/Delco) across these years — pairs stay Likely, match your part number"},
        },
    },
    "honda-j37": {
        "display": "Acura J37 3.7 V6 (MDX 2nd gen)",
        "engine": {"liters": [3.7], "cyl": 6},
        "apps": [
            ("Acura", "MDX", 2007, 2013, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "07-09 and 10-13 each one published unit (the 07-09 unit carries over from the 03-06 3.5)"},
            "starter": {"note": "07-09 and 10-13 each one published unit"},
        },
    },
    "acura-tl": {
        "display": "Acura TL 3.2/3.5/3.7 V6",
        "engine": {"liters": [3.2, 3.5, 3.7], "cyl": 6},
        "apps": [
            ("Acura", "TL", 1999, 2014, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "one published unit per generation — 09-14 covers both the 3.5 and the SH-AWD 3.7"},
            "starter": {"note": "99-03 one published unit; 04-08 and 10-14 rows split by transmission — those pairs stay Likely"},
        },
    },
    "ford-windstar38": {
        "display": "Ford Windstar 3.8 Essex V6",
        "engine": {"liters": [3.8], "cyl": 6},
        "apps": [
            ("Ford", "Windstar", 1995, 2003),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers all 3.8 Windstars 99-03; the 1995 3.8 splits by build date"},
            "starter": {"note": "every published starter row splits by switch-terminal style — match the terminal on your old unit"},
        },
    },
    "mopar-neon": {
        "display": "Dodge/Plymouth Neon 2.0 I4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Dodge", "Neon", 1995, 2005),
            ("Plymouth", "Neon", 1995, 2001),
        ],
        "parts": {
            "alternator": {"note": "four published units by year band (95 / 96-97 / 98-99 / 00-05); 2003 also lists a 145A option unit — match amperage"},
            "starter": {"note": "three published units by year band (96-97 / 98-99 / 00-02); 1995 is dual-listed — match your part number"},
        },
    },
    "gm-jbody22": {
        "display": "GM J-body 2.2 I4 (Cavalier/Sunfire)",
        "engine": {"liters": [2.2], "cyl": 4},
        "apps": [
            ("Chevrolet", "Cavalier", 1995, 2005),
            ("Pontiac", "Sunfire", 1995, 2005),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers all 2.2 Cavaliers and Sunfires 96-02 — the 2.3/2.4 Quad-4 cars use a different unit"},
            "starter": {"note": "03-05 Ecotec cars share one published unit; 96-97 OHV cars share another (the 98 rows carry a thru-bolt qualifier)"},
        },
    },
    "gm-vortec57": {
        "display": "GM 5.7 Vortec/TBI V8 (GMT400 trucks)",
        "engine": {"liters": [5.7], "cyl": 8},
        "apps": [
            ("Chevrolet", "Tahoe", 1995, 2000),
            ("Chevrolet", "Suburban", 1992, 1999),
            ("GMC", "Yukon", 1995, 1999),
            # GMT400 pickups — feed uses several spellings
            ("Chevrolet", "C/K 1500", 1988, 1999),
            ("Chevrolet", "C/K 1500 Series", 1988, 1999),
            ("Chevrolet", "K1500", 1988, 1999),
            ("Chevrolet", "C1500", 1988, 1999),
            ("Chevrolet", "Gmt-400", 1988, 2000),
            ("Chevrolet", "C/K 2500", 1988, 2000),
            ("GMC", "Sierra", 1989, 1998),
            ("GMC", "Suburban", 1993, 1999),
        ],
        "parts": {
            "alternator": {"note": "every published alternator row splits by case diameter or rear-cover style — match the case on your old unit"},
            "starter": {"note": "ONE published starter covers 95-96 and 99-00 Tahoe/Suburban 5.7; 97 uses its own unit; 98 rows carry a thru-bolt qualifier"},
        },
    },
    "gm-vortec-gen3": {
        "display": "GM Gen-III/IV 4.8/5.3 V8 (full-size SUVs)",
        "engine": {"liters": [4.8, 5.3], "cyl": 8},
        "apps": [
            ("Chevrolet", "Tahoe", 2000, 2014),
            ("Chevrolet", "Suburban", 2000, 2014),
            ("GMC", "Yukon", 2000, 2014),
            ("Chevrolet", "Avalanche", 2002, 2013),
            ("Chevrolet", "Avalanche 1500", 2002, 2006),
        ],
        "parts": {
            "alternator": {"note": "most years split by case diameter (145 vs 156mm) — match the case; 11-12 Tahoe publishes one unqualified unit"},
            "starter": {"note": "ONE published starter covers 4.8/5.3 Tahoe+Suburban 03-08; another covers Tahoe 09-14"},
        },
    },
    "mitsu-4b11": {
        "display": "Mitsubishi 4B11 2.0 I4 (Lancer)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Mitsubishi", "Lancer", 2008, 2017),
            ("Mitsubishi", "Outlander Sport", 2011, 2017),
        ],
        "parts": {
            "alternator": {"note": "turbo (Ralliart/Evo) and non-turbo 2.0s use different published units — confirm which you have; pairs stay Likely"},
            "starter": {"note": "2010 publishes one unit for both NA and Evo GSR; other years split by turbo/build date — match part number"},
        },
    },
    "mitsu-4g94": {
        "display": "Mitsubishi 4G94 2.0 I4 (Lancer 02-07)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Mitsubishi", "Lancer", 2002, 2007),
        ],
        "parts": {
            "alternator": {"note": "2002 and 2007 each publish one clean unit; 03-06 rows carry a non-turbo qualifier because the Evo shares the 2.0 badge — confirm non-turbo"},
            "starter": {"note": "03+ rows carry non-turbo qualifiers (Evo years) — match part number"},
        },
    },
    "acura-rl": {
        "display": "Acura RL 3.5/3.7 V6",
        "engine": {"liters": [3.5, 3.7], "cyl": 6},
        "apps": [
            ("Acura", "RL", 1996, 2012, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "one published unit per generation (96-04 / 05-08 / 09-12), all unqualified"},
            "starter": {"note": "96-04, 05-08 and 09-10 each one published unit; 2011-12 is dual-listed — match your part number"},
        },
    },
    "ford-freestar": {
        "display": "Ford Freestar/Mercury Monterey 3.9/4.2 V6",
        "engine": {"liters": [3.9, 4.2], "cyl": 6},
        "apps": [
            ("Ford", "Freestar", 2004, 2007, {"sole": True}),
            ("Mercury", "Monterey", 2004, 2007, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers both the 3.9 and 4.2 Freestar 04-06"},
            "starter": {"note": "ONE published starter covers both engines across the full 04-07 run"},
        },
    },
    "lincoln-ls39": {
        "display": "Lincoln LS 3.9 V8",
        "engine": {"liters": [3.9], "cyl": 8},
        "apps": [
            ("Lincoln", "LS", 2000, 2006),
        ],
        "parts": {
            "alternator": {"note": "00-02 and 03-06 each one published unit; the V6 3.0's 03-04 rows split by transmission — V6 pairs stay Likely"},
            "starter": {"note": "ONE published starter covers every 3.9 LS 00-06"},
        },
    },
    "mazda-mpv30": {
        "display": "Mazda MPV 3.0 V6",
        "engine": {"liters": [3.0], "cyl": 6},
        "apps": [
            ("Mazda", "MPV", 1989, 1998),
            ("Mazda", "MPV", 2002, 2006),
        ],
        "parts": {
            "alternator": {"note": "89-98 one published unit; 02-05 another — the 00-01 MPV is the 2.5 Duratec (different family)"},
            "starter": {"note": "02-06 one published unit; 92-95 another (96-98 rows split Std/Opt)"},
        },
    },
    "mazda-protege": {
        "display": "Mazda Protege 1.5/1.6/1.8/2.0 I4",
        "engine": {"liters": [1.5, 1.6, 1.8, 2.0], "cyl": 4},
        "apps": [
            ("Mazda", "Protege", 1992, 2003),
            ("Mazda", "Protege5", 2002, 2003, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "02-03 2.0 cars (incl. Protege5) share one published unit; 97-98 another; other years mix engines on different units — match part number"},
            "starter": {"note": "every published starter row splits by transmission — match part number"},
        },
    },
    "mopar-minivan-ohv": {
        "display": "Chrysler minivan 3.3/3.8 OHV V6 (01-10)",
        "engine": {"liters": [3.3, 3.8], "cyl": 6},
        "apps": [
            ("Dodge", "Grand Caravan", 2001, 2010),
            ("Chrysler", "Grand Caravan", 2001, 2010),  # feed wrong-make rows
            ("Dodge", "Caravan", 2001, 2007),
            ("Chrysler", "Caravan", 2001, 2007),
            ("Chrysler", "Town & Country", 2000, 2010),
            ("Chrysler", "Town And Country", 2000, 2010),
            ("Chrysler", "Town &amp; Country", 2000, 2010),  # raw feed HTML entity
            ("Chrysler", "Voyager", 2001, 2003),
        ],
        "parts": {
            "alternator": {"note": "every published alternator row splits Std vs Opt amperage — match the amp rating on your old unit"},
            "starter": {"note": "ONE published starter per band (01-03 / 04-05 / 06-10) covers both the 3.3 and 3.8 — the 08-10 4.0 uses its own unit"},
        },
    },
    "ford-escort": {
        "display": "Ford Escort 1.9/2.0 I4",
        "engine": {"liters": [1.9, 2.0], "cyl": 4},
        "apps": [
            ("Ford", "Escort", 1991, 2003),
            ("Ford", "Escort ZX2", 1998, 2003, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "91-93, 94-96 and 98-03 SPI each one published unit (98-03 has two case styles — match yours); the ZX2's Zetec uses its own unit"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "ford-40ohv": {
        "display": "Ford 4.0 OHV V6 (Explorer 1st gen)",
        "engine": {"liters": [4.0], "cyl": 6},
        "apps": [
            ("Ford", "Explorer", 1991, 1996),
            ("Ford", "Aerostar", 1990, 1997),
        ],
        "parts": {
            "alternator": {"note": "91-92 one published unit; 93-98 rows split by trim package / door keypad — match amperage"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "toyota-rav4-1": {
        "display": "Toyota RAV4 2.0 I4 (1st/2nd gen)",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Toyota", "RAV4", 1996, 2003, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "96-97 and 98-00 (3S-FE) each one published unit; 01-03 (1AZ-FE) rows split by transmission"},
            "starter": {"note": "01-03 rows carry a Mfd-in-Japan qualifier — match part number"},
        },
    },
    "subaru-legacy25": {
        "display": "Subaru Legacy/Outback 2.2/2.5 H4",
        "engine": {"liters": [2.2, 2.5], "cyl": 4},
        "apps": [
            ("Subaru", "Legacy", 1990, 2014),
            ("Subaru", "Outback", 1995, 2014),
        ],
        "parts": {
            "alternator": {"note": "one published unit per band (90-94 / 96-99 2.2+2.5 / 00-04 / 06-09 incl. GT turbo / 10-11 / 13-14); 2005 and 2012 split by turbo or are unpublished"},
            "starter": {"note": "published rows split by transmission — match part number"},
        },
    },
    "gm-lumina31": {
        "display": "Chevrolet Lumina 3.1 V6",
        "engine": {"liters": [3.1], "cyl": 6},
        "apps": [
            ("Chevrolet", "Lumina", 1990, 2001),
            ("Chevrolet", "Monte Carlo", 1995, 1999),
        ],
        "parts": {
            "alternator": {"note": "five published units by year band (90-94 / 95-97 / 98-99 / 00 / 01) — all unqualified for the 3.1"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "isuzu-6vd1": {
        "display": "Isuzu 6VD1 3.2 V6 (Rodeo/Passport)",
        "engine": {"liters": [3.2], "cyl": 6},
        "apps": [
            ("Isuzu", "Rodeo", 1992, 2004),
            ("Honda", "Passport", 1994, 2002),
            ("Isuzu", "Trooper", 1992, 1997),
        ],
        "parts": {
            "alternator": {"note": "99-01 and 97 each one published unit; 96 rows carry a plug-position qualifier"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "lexus-1uz": {
        "display": "Lexus LS 400 1UZ-FE 4.0 V8",
        "engine": {"liters": [4.0], "cyl": 8},
        "apps": [
            ("Lexus", "LS 400", 1990, 2000, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "four published units by year band (90-92 / 93-94 / 95-97 / 99-00); 1998 splits by production date"},
            "starter": {"note": "two published units: 90-94 and 95-00 — both unqualified"},
        },
    },
    "lexus-3uz": {
        "display": "Lexus LS 430 3UZ-FE 4.3 V8",
        "engine": {"liters": [4.3], "cyl": 8},
        "apps": [
            ("Lexus", "LS 430", 2001, 2006, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "01-04 and 05-06 each one published unit, unqualified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "saturn-s19": {
        "display": "Saturn S-Series 1.9 I4",
        "engine": {"liters": [1.9], "cyl": 4},
        "apps": [
            ("Saturn", "S-Series", 1991, 2002, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers every SL/SC/SW 91-96 (SOHC and DOHC); 1997 rows carry an external-fan qualifier"},
            "starter": {"note": "98-99 one published unit; other years split — match part number"},
        },
    },
    "hyundai-genesis38": {
        "display": "Hyundai Genesis sedan 3.8 V6",
        "engine": {"liters": [3.8], "cyl": 6},
        "apps": [
            ("Hyundai", "Genesis", 2009, 2015),
        ],
        "parts": {
            "alternator": {"note": "year-banded published units (09-11 / 12 / 13 / 14-15) — the V8s share the 14-15 unit"},
            "starter": {"note": "2009 one published unit (shared with the 4.6); later years split — match part number"},
        },
    },
    "hyundai-gencoupe20": {
        "display": "Hyundai Genesis Coupe 2.0T I4",
        "engine": {"liters": [2.0], "cyl": 4},
        "apps": [
            ("Hyundai", "Genesis Coupe", 2010, 2014),
        ],
        "parts": {
            "alternator": {"note": "10-12 and 13-14 each one published unit, unqualified"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hyundai-gencoupe38": {
        "display": "Hyundai Genesis Coupe 3.8 V6",
        "engine": {"liters": [3.8], "cyl": 6},
        "apps": [
            ("Hyundai", "Genesis Coupe", 2010, 2015),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers 10-15 (2012 is dual-listed with the 2.0T's unit — match yours)"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "acura-rdx": {
        "display": "Acura RDX 2.3T I4 (1st gen)",
        "engine": {"liters": [2.3], "cyl": 4},
        "apps": [
            ("Acura", "RDX", 2007, 2012, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers every 2.3T RDX 07-12"},
            "starter": {"note": "two published units (07-09 / 10-12), both unqualified"},
        },
    },
    "acura-rdx35": {
        "display": "Acura RDX 3.5 V6 (2nd gen)",
        "engine": {"liters": [3.5], "cyl": 6},
        "apps": [
            ("Acura", "RDX", 2013, 2018, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": _ALT_NOTE},
            "starter": {"note": "ONE published unit covers 13-15"},
        },
    },
    "lexus-is2": {
        "display": "Lexus IS 250/350 (2nd gen)",
        "engine": {"liters": [2.5, 3.5], "cyl": 6},
        "apps": [
            ("Lexus", "IS 250", 2006, 2015, {"sole": True}),
            ("Lexus", "IS 350", 2006, 2015, {"sole": True}),
            ("Lexus", "IS", 2006, 2015),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers IS 250 AND IS 350 06-09 (10-13 rows carry a Base-trim qualifier)"},
            "starter": {"note": "ONE published starter covers the IS 250 06-11; IS 350 starters aren't published unqualified"},
        },
    },
    "mopar-lh27": {
        "display": "Chrysler LH 2.7 V6 (Intrepid/Concorde)",
        "engine": {"liters": [2.7], "cyl": 6},
        "apps": [
            ("Dodge", "Intrepid", 1998, 2004),
            ("Chrysler", "Concorde", 1998, 2004),
            ("Chrysler", "300M", 1999, 2004),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers the 2.7 Intrepid 99-01; the 3.2/3.5 use their own units and 03-04 rows split Std/Opt"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "hyundai-santafe2": {
        "display": "Hyundai Santa Fe 2.4 (2nd/3rd gen)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Hyundai", "Santa Fe", 2010, 2012),
            ("Hyundai", "Santa Fe Sport", 2013, 2016),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers the 2.4 Santa Fe 10-12 (shared with the Sonata); 13+ Sport rows carry trim/AMS qualifiers"},
            "starter": {"note": _STR_NOTE},
        },
    },
    "mopar-srt4": {
        "display": "Dodge SRT-4 2.4 Turbo (EDV)",
        "engine": {"liters": [2.4], "cyl": 4},
        "apps": [
            ("Dodge", "Neon Srt-4", 2003, 2005, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "2.4 turbo rows are published clean — "
                                   "do NOT use 2.0 Neon units"},
            "starter": {"note": "04-05 published; the 2003 2.4 starter row "
                                "is not in this catalog edition"},
        },
    },
    "mercury-marauder": {
        "display": "Mercury Marauder 4.6 DOHC",
        "engine": {"liters": [4.6], "cyl": 8},
        "apps": [
            ("Mercury", "Marauder", 2003, 2004, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": "published rows carry a Police/Ford-unit "
                                   "qualifier — match the unit on your car"},
            "starter": {"note": "two published case styles — match yours"},
        },
    },
    "vw-r32-32": {
        "display": "VW R32 3.2 VR6 (MkV)",
        "engine": {"liters": [3.2], "cyl": 6},
        "apps": [
            ("Volkswagen", "R32", 2008, 2008, {"sole": True}),
        ],
        "parts": {
            "alternator": {"note": _ALT_NOTE},
            "starter": {"note": "two published case styles — match yours"},
        },
    },
    "ford-tc": {
        "display": "Ford Transit Connect 1.6/2.0/2.5",
        "engine": {"liters": [1.6, 2.0, 2.5], "cyl": 4},
        "apps": [
            ("Ford", "Transit Connect", 2010, 2014),
        ],
        "parts": {
            "alternator": {"note": "ONE published unit covers the 2.0 in 2010 and 2012-13 (the 2011 row carries a vendor qualifier); 2014's 1.6 and 2.5 each use their own unit"},
            "starter": {"note": _STR_NOTE},
        },
    },
}


def _parse_engine_str(s: str) -> tuple[float | None, int | None]:
    """('2.4L 4-cyl Flexible Fuel...' -> (2.4, 4)); (None, None) when the
    string carries neither. Diesel/Electric markers are NOT handled here —
    callers that must exclude them check the raw string."""
    if not s:
        return None, None
    sl = s.lower()
    m = re.search(r"(\d+\.\d+)\s*l", sl)
    liters = float(m.group(1)) if m else None
    m = re.search(r"(\d+)[\s-]*cyl", sl)
    cyl = int(m.group(1)) if m else None
    return liters, cyl


def _squash_model(model: str, make: str = "") -> str:
    """Matching key for feed model spellings: lowercase alphanumerics, any
    leading make token dropped ('Ford F150 Pickup' -> 'f150pickup' ->
    'f150'), a trailing 'pickup' dropped when something remains."""
    sm = re.sub(r"[^a-z0-9]", "", (model or "").lower())
    mk = re.sub(r"[^a-z0-9]", "", (make or "").lower())
    if mk and sm.startswith(mk) and len(sm) > len(mk):
        sm = sm[len(mk):]
    if sm.endswith("pickup") and len(sm) > len("pickup"):
        sm = sm[: -len("pickup")]
    return sm


def _app_matches(app: tuple, year: int, make: str, model: str) -> bool:
    a_make, a_model, lo, hi = app[0], app[1], app[2], app[3]
    if not (lo <= year <= hi):
        return False
    mk = (make or "").lower()
    if mk not in (m.lower() for m in a_make.split("|")):
        return False
    # Try both the make-stripped squash and the raw squash: 'Ram Ram 2500'
    # needs the strip, while a 'Ram 2500' under make 'Ram' must NOT lose its
    # leading 'ram' or the 'Ram*' pattern can never match it.
    candidates = {_squash_model(model, make), _squash_model(model)}
    am = re.sub(r"[^a-z0-9]", "", a_model.rstrip("*").lower())
    if a_model.endswith("*"):
        return any(sm.startswith(am) for sm in candidates)
    return am in candidates


def _app_flags(app: tuple) -> dict:
    return app[4] if len(app) > 4 else {}


def engine_families_for(year: int, make: str, model: str,
                        part: str | None = None) -> list[tuple[str, dict, tuple]]:
    """All (family_id, family, matching app) for a seeker's car. More than one
    result means the model offered several family engines in that year — the
    UI must ask which engine the seeker has. With `part`, families that don't
    offer the part for the seeker's year (missing, or outside the part's own
    researched window) are dropped — the same rule the client applies."""
    out = []
    for fam_id, fam in ENGINE_FAMILIES.items():
        if part is not None:
            p = fam["parts"].get(part)
            if p is None:
                continue
            yrs = p.get("years")
            if yrs is not None and not (yrs[0] <= year <= yrs[1]):
                continue
        for app in fam["apps"]:
            if _app_matches(app, year, make, model):
                out.append((fam_id, fam, app))
                break
    return out


def engine_matches_family(engine_str: str, fam: dict) -> bool | None:
    """True/False when the decode string confirms/denies the family engine;
    None when there's no usable engine data. Diesel strings always deny —
    no family here covers one."""
    if engine_str and "diesel" in engine_str.lower():
        return False
    liters, cyl = _parse_engine_str(engine_str)
    if liters is None:
        return None
    spec = fam["engine"]
    if not any(abs(liters - want) < 0.05 for want in spec["liters"]):
        return False
    want_cyl = spec.get("cyl")
    if cyl is not None and want_cyl is not None and cyl != want_cyl:
        return False
    return True


# --- Verified alternator application groups -------------------------------
# Each entry is keyed by family id and merged into that family's alternator
# part below. "groups" lists one published part number's application list per
# inner list — the evidence string cites where each list was retrieved.
# Research notes with full citations live in scraper/interchange_research.md.
_ALT_VERIFIED: dict = {
    "toyota-rz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), identical units for the 2.4 (2RZFE) and 2.7 (3RZFE) in every year row: 210-0448 (60A) Tacoma 1995-1996, T100 2.7 1994-1996; 210-0188 (70A) Tacoma 1997-1999, T100 2.7 1997-1998, 4Runner 2.7 1996-1999; 210-0390 (80A) Tacoma 2000-2004, 4Runner 2.7 2000 (the same list runs to the 2005 base-2.7 Tacoma, outside this family's years).",
        "groups": [
            [("Toyota", "Tacoma", 1995, 1996),
             ("Toyota", "T100", 1994, 1996)],
            [("Toyota", "Tacoma", 1997, 1999),
             ("Toyota", "T100", 1997, 1998),
             ("Toyota", "4Runner", 1996, 1999)],
            [("Toyota", "Tacoma", 2000, 2004),
             ("Toyota", "4Runner", 2000, 2000)],
        ],
    },
    "toyota-5vz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 5VZFE 3.4: 210-0447 (60A) Tacoma 1995-1996 and 1998-1999, T100 1995-1998, 4Runner 1998, Tundra 2000 std; 210-0180 (70A) 4Runner 1996-1998, T100 1997-1998, Tacoma 1997-1999, Tundra 2000-2002; 210-0434 (80A) 4Runner 1999-2002, Tacoma 2000-2004, Tundra 2001-2002 and 2000 opt; 210-0513 (80A) Tundra 2003-2004.",
        "groups": [
            [("Toyota", "Tacoma", 1995, 1996),
             ("Toyota", "Tacoma", 1998, 1999),
             ("Toyota", "T100", 1995, 1998),
             ("Toyota", "4Runner", 1998, 1998),
             ("Toyota", "Tundra", 2000, 2000)],
            [("Toyota", "4Runner", 1996, 1998),
             ("Toyota", "T100", 1997, 1998),
             ("Toyota", "Tacoma", 1997, 1999),
             ("Toyota", "Tundra", 2000, 2002)],
            [("Toyota", "4Runner", 1999, 2002),
             ("Toyota", "Tacoma", 2000, 2004),
             ("Toyota", "Tundra", 2000, 2002)],
            [("Toyota", "Tundra", 2003, 2004)],
        ],
    },
    "honda-a20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0233 (65A) Accord 2.0 A20A3 w/ fuel injection 1986-1989 and 210-0389 (65A) Accord 2.0 A20A1 carbureted 1986-1989 — both published lists span the same four years; match FI vs carb when pulling.",
        "groups": [[("Honda", "Accord", 1986, 1989)]],
    },
    "honda-f22": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0216 (90A) Accord 2.2 F22A1/A6 1990-1993; 210-0208 (80A) Accord 2.2 F22B2 1994-1997 and 210-0209 (90A) Accord 2.2 F22B1 VTEC 1994-1997 — the 94-97 lists split by VTEC trim but each spans all four years.",
        "groups": [
            [("Honda", "Accord", 1990, 1993)],
            [("Honda", "Accord", 1994, 1997)],
        ],
    },
    "nissan-mr20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4301 (110A) Sentra 2.0 MR20DE 2007-2010 (the same list serves the Versa 1.8 and NV200). 2011-2012 Sentra 2.0 keeps the MR20DE but is past this catalog edition — left at likely.",
        "groups": [[("Nissan", "Sentra", 2007, 2010)]],
    },
    "nissan-vk56": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3160 (130A) engine-coded VK56DE — Titan 2004-2006, Armada 2005-2006, Pathfinder Armada 2004. Later VK56DE years are past this catalog edition — left at likely.",
        "groups": [[("Nissan", "Titan", 2004, 2006),
                    ("Nissan", "Armada", 2005, 2006),
                    ("Nissan", "Pathfinder Armada", 2004, 2004)]],
    },
    "ford-escape-16eb": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0604 (170A) Escape 1.6 2013-2014. 2015-2016 1.6 cars are past this catalog edition — left at likely.",
        "groups": [[("Ford", "Escape", 2013, 2014)]],
    },
    "ford-escape-20eb": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4202 (135A) Escape 2.0 2013-2014. 2015-2016 2.0 cars are past this catalog edition — left at likely.",
        "groups": [[("Ford", "Escape", 2013, 2014)]],
    },
    "gm-vortec43": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), 4.3 V6 rows: 210-5112 (100A) S10 1994-1995, Sonoma 1994-1995, Blazer 1995; 210-5111 (105A) Astro and Safari 1994-1995; 210-5119 (105A) S10/Sonoma/Blazer/Jimmy 1996-1997, Astro/Safari 1996-1999, Express/Savana 4.3 1996-2000 (w/ black plastic rear cover — the w/o-cover vans take 210-5190, same vehicle list); 210-5120 (105A) S10/Blazer 1998-1999, Sonoma/Jimmy 1998-2000, Astro/Safari 2000; 210-5159 (100A) S10/Sonoma/Blazer 2001-2004, Jimmy 2001; 210-5384 (145A) Express/Savana 4.3 2005-2008. The 2000 S10/Blazer split mid-year by VIN — excluded from verified.",
        "groups": [
            [("Chevrolet", "S-10*", 1994, 1995),
             ("GMC", "Sonoma", 1994, 1995),
             ("Chevrolet", "Blazer*", 1995, 1995)],
            [("Chevrolet", "Astro*", 1994, 1995),
             ("GMC", "Safari*", 1994, 1995)],
            [("Chevrolet", "S-10*", 1996, 1997),
             ("GMC", "Sonoma", 1996, 1997),
             ("Chevrolet", "Blazer*", 1996, 1997),
             ("GMC", "Jimmy*", 1996, 1997),
             ("Chevrolet", "Astro*", 1996, 1999),
             ("GMC", "Safari*", 1996, 1999),
             ("Chevrolet", "Express*", 1996, 2000),
             ("GMC", "Savana*", 1996, 2000)],
            [("Chevrolet", "S-10*", 1998, 1999),
             ("Chevrolet", "Blazer*", 1998, 1999),
             ("GMC", "Sonoma", 1998, 2000),
             ("GMC", "Jimmy*", 1998, 2000),
             ("Chevrolet", "Astro*", 2000, 2000),
             ("GMC", "Safari*", 2000, 2000)],
            [("Chevrolet", "S-10*", 2001, 2004),
             ("GMC", "Sonoma", 2001, 2004),
             ("Chevrolet", "Blazer*", 2001, 2004),
             ("GMC", "Jimmy*", 2001, 2001)],
            [("Chevrolet", "Express*", 2005, 2008),
             ("GMC", "Savana*", 2005, 2008)],
        ],
    },
    "gm-vortec-van": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5190 (124A, w/o black plastic rear cover) Express/Savana 5.0 and 5.7 1996-2000 across 1500/2500/3500 (the w/-cover vans take 210-5119, same vehicle list — match the case style); 210-5384 (145A Delco) Express/Savana 4.8/5.3/6.0 2005-2008 across 1500/2500/3500. The 2001-2004 vans and 2009-2010 case-size splits are left at likely.",
        "groups": [
            [("Chevrolet", "Express*", 1996, 2000),
             ("GMC", "Savana*", 1996, 2000)],
            [("Chevrolet", "Express*", 2005, 2008),
             ("GMC", "Savana*", 2005, 2008)],
        ],
    },
    "cadillac-northstar": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), 4.6 Northstar rows: 210-5184 (140A) Deville, Eldorado and Seville 1997 (unqualified; the 1994-1996 rows carry a 'w/o heated windshield' qualifier — excluded); 210-5185 (140A) Deville and Eldorado 1998-1999; 210-0467 (140A) Deville 2001-2005 and Seville 2001-2003, exc. limousine; 210-0639 (150A) DTS 2006-2011 exc. limousine (limos take 220A 210-0676).",
        "groups": [
            [("Cadillac", "Deville", 1997, 1997),
             ("Cadillac", "Eldorado", 1997, 1997),
             ("Cadillac", "Seville", 1997, 1997)],
            [("Cadillac", "Deville", 1998, 1999),
             ("Cadillac", "Eldorado", 1998, 1999)],
            [("Cadillac", "Deville", 2001, 2005),
             ("Cadillac", "Seville", 2001, 2003)],
            [("Cadillac", "DTS", 2006, 2011)],
        ],
    },
    "mopar-pt24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), non-turbo rows: 210-4177 (120A) PT Cruiser 2002; 210-4201 (100A) PT Cruiser 2003-2005; 210-4228 (100A) PT Cruiser 2006-2010. GT/Turbo takes separate 130-145A units (210-0558/0559/0803) — noted, and 2001 is not in this edition — left at likely.",
        "groups": [
            [("Chrysler", "PT Cruiser", 2002, 2002)],
            [("Chrysler", "PT Cruiser", 2003, 2005)],
            [("Chrysler", "PT Cruiser", 2006, 2010)],
        ],
    },
    "mopar-dart": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4237 (120A) Dart 1.4T 2013-2014, 2.0 2013-2015, 2.4 2014-2015; 210-4239 (160A) Dart 2.0/2.4 2013-2015 — every 2013-2015 engine/year pairing sits inside at least the 120A list. 2016 is past this edition — left at likely.",
        "groups": [[("Dodge", "Dart*", 2013, 2015)]],
    },
    "hk-alpha": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6012 (90A) Accent 1.5 1995-1999; 211-6005 (90A) Accent 1.5 2000-2003 and 1.6 2001-2002 (the 2003-2005 1.6 rows carry a Mando-unit qualifier — excluded); 211-6016 (90A) Accent 1.6 2010-2011 plus Rio and Rio5 1.6 2010-2011 in the same published set; 211-6006 (80A) Rio 1.5 2001-2002 and 1.6 2003-2005; 211-6002 (90A) Rio 1.6 2006-2009 and Rio5 2006-2007 (the Rio5 08-09 rows are Valeo-qualified). The Accent 2006-2009 rows are Mando-qualified — left at likely.",
        "groups": [
            [("Hyundai", "Accent", 1995, 1999)],
            [("Hyundai", "Accent", 2000, 2002)],
            [("Hyundai", "Accent", 2010, 2011),
             ("Kia", "Rio", 2010, 2011),
             ("Kia", "Rio5", 2010, 2011)],
            [("Kia", "Rio", 2001, 2005)],
            [("Kia", "Rio", 2006, 2009), ("Kia", "Rio5", 2006, 2007)],
        ],
    },
    "hk-mu-lambda": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0712 (130A) Santa Fe 2.7 2007-2009 and 3.3 2007-2008, Azera 3.3 2007-2009 and 3.8 2007-2008 (the 2009+ rows carry Denso-unit vendor qualifiers — group capped at 2008), plus Sorento 3.8 2007-2009 and 3.3 2008-2009 in the same published set (2007 Sorentos are all 3.8, so the span is clean).",
        "groups": [[("Hyundai", "Santa Fe", 2007, 2008),
                    ("Hyundai", "Azera", 2007, 2008),
                    ("Kia", "Sorento", 2007, 2009)]],
    },
    "mini-r50": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0844 (105A) Cooper W10 2002-2004 plus 2005 coupe and convertible rows; the supercharged S (W11, 210-0524) spans 2002-2006 — match trim. Group capped at 2002-2005 where both published lists cover every body style.",
        "groups": [[("MINI", "Cooper", 2002, 2005)]],
    },
    "subaru-fa20dit": {
        "evidence": "Subaru OEM 23700AA911 (replaces AA910) fitment (subarupartsdeal.com, retrieved 2026-10-22): WRX 2.0 turbo 2015-2020. The Forester 2.0XT shares its unit with the FB25 Forester (23700AB030), not the WRX — left at likely.",
        "groups": [[("Subaru", "WRX", 2015, 2020)]],
    },
    "subaru-ej25t": {
        "evidence": "Mitsubishi A3TG0491 / Subaru 23700-AA520/AA521/AA570 application list (maniacelectricmotors.com + HC-Cargo 115453, retrieved 2026-10-22): Forester XT 2006-2010, Impreza WRX/STI 2006-2010, Legacy GT 2005, Outback XT 2005, Saab 9-2X 2006. Subaru OEM 23700AA871 (subarupartsdeal.com): Forester XT 2011-2013, Impreza WRX/STI 2011-2014, WRX/WRX STI 2.5 turbo 2015-2020.",
        "groups": [
            [("Subaru", "Forester", 2006, 2010),
             ("Subaru", "Impreza", 2006, 2010),
             ("Subaru", "Impreza WRX", 2006, 2010),
             ("Subaru", "Legacy", 2005, 2005),
             ("Subaru", "Outback", 2005, 2005)],
            [("Subaru", "Forester", 2011, 2013),
             ("Subaru", "Impreza", 2011, 2014),
             ("Subaru", "Impreza WRX", 2011, 2014),
             ("Subaru", "WRX", 2011, 2014)],
        ],
    },
    "subaru-fb25": {
        "evidence": "Subaru OEM fitment (subarupartsdeal.com, retrieved 2026-10-22): 23700AB030 (replaces 23700AA760/AA761) Forester 2014-2018 (2.5i and 2.0XT trims); 23700AA91B Legacy 2.5i 2015-2017; 23700AB01A Legacy/Outback 2.5i 2018-2019.",
        "groups": [
            [("Subaru", "Forester", 2014, 2018)],
            [("Subaru", "Legacy", 2015, 2017)],
            [("Subaru", "Legacy", 2018, 2019),
             ("Subaru", "Outback", 2018, 2019)],
        ],
    },
    "mopar-47": {
        "evidence": "Mopar OEM 56029914AC (160A Denso, replaces 56029914AA) fitment (jeeppartsdeal.com, retrieved 2026-10-22): Durango 3.7/4.7 2001-2007, Grand Cherokee 3.7/4.7 2005-2006; Denso 421000-0040 vendor table adds Commander 3.7/4.7 2006-2010. Mopar RL041120AC (Ram 1500 3.7/4.7 2002-2007) and 56029700AD (Ram 1500 2008) cover the trucks.",
        "groups": [
            [("Dodge", "Durango", 2001, 2007),
             ("Jeep", "Grand Cherokee", 2005, 2006),
             ("Jeep", "Commander", 2006, 2009)],
            [("Dodge|Ram", "Ram*", 2002, 2008)],
        ],
    },
    "mopar-37": {
        "evidence": "Mopar OEM 56029914AC fitment (jeeppartsdeal.com, retrieved 2026-10-22): Liberty 3.7 2002-2005, Grand Cherokee 3.7 2005-2006; Denso 421000-0040 vendor table: Commander 3.7 2006-2010. Mopar RL041120AC/56029700AD: Ram 3.7 2002-2008 (same units as the 4.7 trucks).",
        "groups": [
            [("Jeep", "Liberty", 2002, 2005),
             ("Jeep", "Grand Cherokee", 2005, 2006),
             ("Jeep", "Commander", 2006, 2010)],
            [("Dodge|Ram", "Ram*", 2002, 2008)],
        ],
    },
    "mopar-magnum": {
        "evidence": "Lester 13354 (Denso 121000-3530, Chrysler 56027912) application list (maniacelectricmotors.com + aspwholesale.com, retrieved 2026-10-22): Dakota 1992-1998, Ram 1500/2500/3500 1994-1998, Durango 1998, Grand Cherokee 5.2/5.9 1993-1998, Ramcharger 1992-1993. Corroborated by Lester 13742 (Chrysler 56027913, 136A) with the same spans. Lester 13920/13914 (Bosch/Denso 136A, Chrysler 56028237) application table (dssautoparts.com): Ram 1999-2003, Durango 5.9 2001-2003.",
        "groups": [
            [("Dodge|Ram", "Ram*", 1994, 1998),
             ("Dodge", "Dakota", 1992, 1998),
             ("Dodge", "Durango", 1998, 1998),
             ("Jeep", "Grand Cherokee", 1993, 1998)],
            [("Dodge|Ram", "Ram*", 1999, 2001),
             ("Dodge", "Durango", 2001, 2003)],
        ],
    },
    "gm-60deg": {
        "evidence": "Lester 13993 (GM 10317647/10440635, Valeo SG10S029) application list (dbelectrical.com 400-40079, retrieved 2026-10-22): Venture 3.4 2002-2005, Montana 3.4 2002-2005, Silhouette 3.4 2002-2004. Grand Am/Alero/Impala/Malibu 3.4 use CS130D-era Delco units with multiple amp options — left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5132 (100A) Camaro and Firebird 2.8 1987-1989 and 3.1 1990-1992, one unit across both displacements; 210-5126 (105A) Camaro and Firebird 3.4 1993-1995.",
        "groups": [[("Chevrolet", "Venture", 2002, 2005),
                    ("Pontiac", "Montana", 2002, 2005)],
                   [("Chevrolet", "Camaro", 1987, 1992),
                    ("Pontiac", "Firebird", 1987, 1992)],
                   [("Chevrolet", "Camaro", 1993, 1995),
                    ("Pontiac", "Firebird", 1993, 1995)]],
    },
    "gm-hv-v6": {
        "evidence": "Lester 11185 (Bosch 0-124-425-032, GM 20911162) application list (TYC 2-11185 via finditparts.com + maniacelectricmotors.com, retrieved 2026-10-22): Impala 3.5/3.9 2006-2011, Monte Carlo 3.5/3.9 2006-2007. Malibu/G6/Uplander use different units — left at likely.",
        "groups": [[("Chevrolet", "Impala", 2006, 2011),
                    ("Chevrolet", "Monte Carlo", 2006, 2007)]],
    },
    "gm-ecotec22": {
        "evidence": "Lester 11265 (Valeo, GM 15828450/22762984) application list (am-autoparts.com + maniacelectricmotors.com, retrieved 2026-10-22): Cobalt 2008-2010, Malibu 2.4 2008-2012, G5 2008-2009, Saturn Aura/Sky/Vue 2008-2010. Denso unit Lester 11140: Cobalt 2.2/2.4 2006-2007. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0546 (110A) Saturn Vue 2.2 2004-2007 (the same unit also serves the 2.4 and Honda-3.5 Vues those years). Earlier Cavalier/Sunfire/ION use other units — left at likely.",
        "groups": [
            [("Chevrolet", "Cobalt", 2008, 2010),
             ("Chevrolet", "Malibu", 2008, 2012),
             ("Pontiac", "G5", 2008, 2009)],
            [("Chevrolet", "Cobalt", 2006, 2007)],
            [("Saturn", "VUE", 2004, 2007)],
        ],
    },
    "toyota-22re": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0116 (60A) Pickup 22RE 1994-1995 and 1993 std; same unit listed for 4Runner 22RE w/ M/T only, while A/T trucks take 210-0297/0299 — transmission splits the unit, so only the unqualified Pickup 1994-1995 span is treated as verified.",
        "groups": [[("Toyota", "Pickup", 1994, 1995)]],
    },
    "toyota-5s": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0187 (80A) Camry 5SFE 1997-2001 and Solara 5SFE 1999 and 2001. Celica/MR2 5S use earlier units — left at likely.",
        "groups": [[("Toyota", "Camry", 1997, 2001),
                    ("Toyota", "Solara", 1999, 2001),
                    ("Toyota", "Camry Solara", 1999, 2001)]],
    },
    "toyota-3mz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0543 (100A std) Lexus ES330 2004-2006, RX330 2004-2006 (Japan-built std), Camry 3.3 2004, Highlander 3.3 2004-2007; 210-0545 (130A opt) RX330 2004-2006 (US-built opt) and Sienna 3.3 2004-2006. Amp option splits noted in research notes.",
        "groups": [
            [("Lexus", "ES 330", 2004, 2006),
             ("Lexus", "RX 330", 2004, 2006),
             ("Toyota", "Camry", 2004, 2004),
             ("Toyota", "Highlander", 2004, 2007)],
            [("Lexus", "RX 330", 2004, 2006),
             ("Toyota", "Sienna", 2004, 2006)],
        ],
    },
    "toyota-2zr": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0699 (100A clutch pulley) Scion xD 1.8 2008-2009 and Corolla 1.8 2009 (Japan-built). Later 2ZR Corolla/Matrix years use successor units — left at likely.",
        "groups": [[("Scion", "xD", 2008, 2009),
                    ("Toyota", "Corolla", 2009, 2009)]],
    },
    "honda-d16": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4134 (70A) Civic 1.6 D16Y5/D16Y7/D16Y8/D16B5 1996-2000 (exc Canada/Si) and Civic del Sol 1.6 1996-1997. Corroborated by Lester 13649 (Honda 31100-P2E-A01) listings.",
        "groups": [[("Honda", "Civic", 1996, 2000),
                    ("Honda", "Civic del Sol", 1996, 1997)]],
    },
    "honda-d17": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4148 (70A) Civic 1.7 D17A1/A2/A6/A7 2001-2005 (exc Canada). Corroborated by Lester 13893 (Honda 31100-PLM-A02) listings incl. Acura EL 1.7.",
        "groups": [[("Honda", "Civic", 2001, 2005)]],
    },
    "honda-r18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4236 (90A) Civic 1.8 R18A1 2006-2011. Corroborated by TYC 2-11176 / Lester 11176 (Honda 31100-RNA-A01) listings. 2012-2015 R18Z Civic uses a different unit — left at likely.",
        "groups": [[("Honda", "Civic", 2006, 2011)]],
    },
    "honda-f23": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0192 (80A) Accord 2.3 1998-2002 (coupe/ULEV splits) and 210-0193 (80A) Accord 2.3 sedan exc-ULEV 1998-2001 + Acura CL 2.3 1998-1999. Both units cover the Accord span; the CL pairs via 210-0193.",
        "groups": [
            [("Honda", "Accord", 1998, 2002)],
            [("Honda", "Accord", 1998, 2001),
             ("Acura", "CL", 1998, 1999)],
        ],
    },
    "acura-j32": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0675 (105A) CL 3.2 2001-2003 (exc Type S; Type S w/ M/T 2003) and TL 3.2 2000-2003; Type S w/ A/T uses 210-0453 (120A) in both models 2001-2003. TL 2004-2008 (J32A3) uses 210-0580 — left at likely.",
        "groups": [[("Acura", "CL", 2001, 2003),
                    ("Acura", "TL", 2000, 2003)]],
    },
    "nissan-ka24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3146 (100A) Altima KA24DE 1998-2001; 210-3156 (70A) Frontier and Xterra KA24DE 2002-2004; 210-3118 (70A) Frontier 1998-2000 and Xterra 2000; 210-3170 (80A) 240SX KA24E 1989-1990. The 91-98 (KA24DE) 240SX and early Altima use other units — left at likely.",
        "groups": [
            [("Nissan", "Altima", 1998, 2001)],
            [("Nissan", "Frontier", 2002, 2004),
             ("Nissan", "Xterra", 2002, 2004)],
            [("Nissan", "Frontier", 1998, 2000),
             ("Nissan", "Xterra", 2000, 2000)],
            [("Nissan", "240SX", 1989, 1990)],
        ],
    },
    "nissan-mr18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4301 (110A) Versa MR18DE 2007-2009 (to 09/2008) and Cube MR18DE 2009; 210-4329 (110A, 7-groove) Cube 2010-2012.",
        "groups": [
            [("Nissan", "Versa", 2007, 2009),
             ("Nissan", "Cube", 2009, 2009)],
            [("Nissan", "Cube", 2010, 2012)],
        ],
    },
    "nissan-hr16": {
        "evidence": "Nissan OEM 23100-3BE1A fitment (nissanpartsdeal.com, retrieved 2026-10-22): Versa 1.6 HR16DE 2012-2019, Versa Note 1.6 2014-2019. Cross-referenced Lester 11547 / Mitsubishi A2TJ1791 vendor tables show identical spans.",
        "groups": [[("Nissan", "Versa", 2012, 2019),
                    ("Nissan", "Versa Note", 2014, 2019)]],
    },
    "hk-gamma16": {
        "evidence": "Lester 13209 (Hyundai/Kia 37300-2B300/2B500/2B510, Valeo) application lists (dbelectrical.com 400-40153 + mymromarts.com, retrieved 2026-10-22): Accent 1.6 2012-2017, Veloster 1.6 2012-2017, Rio 1.6 2012-2013. Soul 1.6 uses 37300-2B760 (Lester 11609) — left at likely.",
        "groups": [[("Hyundai", "Accent", 2012, 2017),
                    ("Hyundai", "Veloster", 2012, 2017),
                    ("Kia", "Rio", 2012, 2013)]],
    },
    "hk-beta20": {
        "evidence": "Lester 13973 (Hyundai/Kia 37300-23600, Mando AB190147) application lists (qpselectric.com + partshawk.com, retrieved 2026-10-22): Elantra 2.0 2001-2006, Tiburon 2.0 2003-2004 and 2007-2008 (w/ Mando unit), Tucson 2.0 2005, Sportage 2.0 2005-2006. Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6008 (90A) Elantra 2.0 2007-2012 and Soul 2.0 2010-2011 unqualified (the same published unit); 211-6012 (90A) Elantra 1.8/2.0 1996-2000 and Tiburon 1.8/2.0 1997-2001 unqualified.",
        "groups": [[("Hyundai", "Elantra", 2001, 2006),
                    ("Hyundai", "Tiburon", 2003, 2004),
                    ("Hyundai", "Tiburon", 2007, 2008),
                    ("Hyundai", "Tucson", 2005, 2005),
                    ("Kia", "Sportage", 2005, 2006)],
                   [("Hyundai", "Elantra", 2007, 2012),
                    ("Kia", "Soul", 2010, 2011)],
                   [("Hyundai", "Elantra", 1996, 2000),
                    ("Hyundai", "Tiburon", 1997, 2001)]],
    },
    "ford-3g-50": {
        "evidence": "Lester 7750 (Ford F07U-10300, 3G 95A side-mount) application list (maniacelectricmotors.com, retrieved 2026-10-22): F-150/F-250 5.0/5.8 1993-1996, Bronco 5.0/5.8 1993-1996, E-150 5.0/5.8 1993-1996; 1987-93 trucks (2G era) left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5123 and 210-5305 both list Mustang 5.0 1988-1993 with identical spans (two published case styles — match yours); 210-5310 Mustang 5.0 1994-1995 and 5.8 1995 (the same list also covers the 3.8 those years).",
        "groups": [[("Ford", "F-150", 1993, 1996),
                    ("Ford", "Bronco", 1993, 1996)],
                   [("Ford", "Mustang", 1988, 1993)],
                   [("Ford", "Mustang", 1994, 1995)]],
    },
    "honda-j30": {
        "evidence": "Lester 8220 (Delco CS130D, Honda 31100-P8A-A01/P8C-A02) application lists (alternatorparts.com + thewrenchmonkey.ca, retrieved 2026-10-22): Accord 3.0 1998-2002, Acura CL 3.0 1997-1999. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0606 (110A) Accord 3.0 J30A4/J30A5 2004-2007 unqualified (2003 shipped 210-0511 shared with the 2.4).",
        "groups": [[("Honda", "Accord", 1998, 2002),
                    ("Acura", "CL", 1997, 1999)],
                   [("Honda", "Accord", 2004, 2007)]],
    },
    "honda-j35-mid": {
        "evidence": "TYC 2-11151 fitment (partshawk.com; Honda 31100-RJA-A02 OEM list on hondapartsnow.com, retrieved 2026-10-22): Odyssey 2005-2007, Pilot 2005-2008, Ridgeline 2006-2008 (+ MDX/TL/RL). Honda 31100-RGW-A01 (CSF92, hondapartsconnection.com): Odyssey 2008-2011 is the follow-on unit.",
        "groups": [
            [("Honda", "Odyssey", 2005, 2007),
             ("Honda", "Pilot", 2005, 2008),
             ("Honda", "Ridgeline", 2006, 2008)],
            [("Honda", "Odyssey", 2008, 2010)],
        ],
    },
    "honda-j35-z": {
        "evidence": "Honda 31100-RGW-A01 (CSF92, Denso) OEM listing (hondapartsconnection.com, retrieved 2026-10-22): Odyssey/Pilot/Ridgeline 2008-2011 share one unit — clipped to this family's 2009+ apps.",
        "groups": [[("Honda", "Pilot", 2009, 2011),
                    ("Honda", "Ridgeline", 2009, 2011)]],
    },
    "honda-j35-early": {
        "evidence": "TYC 2-13918 fitment (partshawk.com + a-premium.com; Honda 31100-PGK-A01/A03, Denso 104210-3090, retrieved 2026-10-22): MDX 2001-2002, Odyssey 3.5 2002-2004, Pilot 2003-2004. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0580 (130A) MDX 3.5 J35A5 2003-2006 (the same published unit continues on the 3.7 MDX through 2009). The 99-01 Odyssey unit differs — left at likely.",
        "groups": [[("Acura", "MDX", 2001, 2002),
                    ("Honda", "Odyssey", 2002, 2004),
                    ("Honda", "Pilot", 2003, 2004)],
                   [("Acura", "MDX", 2003, 2006)]],
    },
    "honda-k24z": {
        "evidence": "Lester 11390 (Honda 31100-R40-A01, Denso 104210-5890) application tables (dssautoparts.com + FVP/autofactsdb.com + DB Electrical 400-52394, retrieved 2026-10-22): Accord 2.4 2008-2012, TSX 2.4 2009-2014. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0808 (105A) CR-V 2.4 K24Z7 2012-2014 unqualified.",
        "groups": [[("Honda", "Accord", 2008, 2012),
                    ("Acura", "TSX", 2009, 2014)],
                   [("Honda", "CR-V", 2012, 2014)]],
    },
    "mopar-world24": {
        "evidence": "Lester 11231 (Chrysler 4801323AC, Mitsubishi A2TJ0481) application tables (qpselectric.com + thenthgear.com + TYC 2-11231, retrieved 2026-10-22): Sebring 2.4 2007-2010, 200 2.4 2011-2013, Avenger 2.4 2008-2013, Caliber 2007-2012, Compass 2007-2017, Patriot 2007-2017. Journey uses a different unit — left at likely.",
        "groups": [[("Chrysler", "Sebring", 2007, 2010),
                    ("Chrysler", "200", 2011, 2013),
                    ("Dodge", "Avenger", 2008, 2013),
                    ("Dodge", "Caliber", 2007, 2012),
                    ("Jeep", "Compass", 2007, 2017),
                    ("Jeep", "Patriot", 2007, 2017)]],
    },
    "jeep-40": {
        "evidence": "TYC 2-13341 fitment (partshawk.com; Chrysler 56005685AB, Denso 121000-3440, retrieved 2026-10-22): Cherokee 1991-1998, Comanche 1991-1992, Wrangler 1991-1998, Grand Cherokee 1993-1998. TYC 2-13876 (Jeep 56041864AB, standardautopart.com): Wrangler 4.0 2001-2006 is its own unit.",
        "groups": [
            [("Jeep", "Cherokee", 1991, 1998),
             ("Jeep", "Comanche", 1991, 1992),
             ("Jeep", "Wrangler", 1991, 1998),
             ("Jeep", "Grand Cherokee", 1993, 1998)],
            [("Jeep", "Wrangler", 2001, 2006)],
        ],
    },
    "hk-theta-mpi": {
        "evidence": "Lester 11189 (Hyundai/Kia 37300-25201, Valeo TG11C076) fitment (WAI 11189N partshawk.com + DB Electrical 400-40062, retrieved 2026-10-22): Sonata 2.4 2006-2010, Optima 2.4 2006-2010, Rondo 2.4 2007-2010.",
        "groups": [[("Hyundai", "Sonata", 2006, 2010),
                    ("Kia", "Optima", 2006, 2010),
                    ("Kia", "Rondo", 2007, 2010)]],
    },
    "hk-nu": {
        "evidence": "Lester 11610 (Hyundai 37300-2E200, Valeo FG10T011) fitment (TYC 2-11610 finditparts.com + dahkee.com + thenthgear.com, retrieved 2026-10-22): Elantra 1.8/2.0 2011-2016, Forte 2014-2016, Soul 2.0 2012-2013.",
        "groups": [[("Hyundai", "Elantra", 2011, 2016),
                    ("Kia", "Forte", 2014, 2016),
                    ("Kia", "Soul", 2012, 2013)]],
    },
    "subaru-ej25na": {
        "evidence": "Subaru OEM 23700-AA31A/AA37A/AA430 listing (LEESENEVO/amazon.com, retrieved 2026-10-22): Legacy 2.5 2005-2009, Outback 2.5 2005-2009. Forester/Impreza 2.5 use 23700-AA52x — a different unit, left at likely.",
        "groups": [[("Subaru", "Legacy", 2005, 2009),
                    ("Subaru", "Outback", 2005, 2009)]],
    },
    "vw-25": {
        "evidence": "Lester 11254 (VW 07K903023A, Bosch 0-124-525-062) fitment (A-Premium APALT130 + miamialternators.com, retrieved 2026-10-22): Jetta 2.5 2005-2014, Rabbit 2.5 2006-2009, Golf 2.5 2010-2014.",
        "groups": [[("Volkswagen", "Jetta", 2005, 2014),
                    ("Volkswagen", "Rabbit", 2006, 2009),
                    ("Volkswagen", "Golf", 2010, 2014)]],
    },
    "nissan-vq40": {
        "evidence": "Nissan OEM 23100-EA20B fitment (nissanpartsdeal.com, retrieved 2026-10-22): Frontier/Pathfinder/Xterra 4.0 2005-2008 (110A). Nissan 23100-ZH00D (130A): Frontier 4.0 2007-2019. Match amperage — both units appear in the 07-08 overlap.",
        "groups": [
            [("Nissan", "Frontier", 2005, 2008),
             ("Nissan", "Pathfinder", 2005, 2008),
             ("Nissan", "Xterra", 2005, 2008)],
            [("Nissan", "Frontier", 2007, 2019)],
        ],
    },
    "gm-3800": {
        "evidence": "Lester 8245 listing (OCPTY/amazon.com, GM 10464439/10480411, retrieved 2026-10-22): LeSabre 3.8 2000-2004, Bonneville 3.8 2000-2004. W-body 3800s (Grand Prix/Impala/Monte Carlo/Regal) use different mounting-era units — left at likely. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5118 (105A, engine code K) Camaro 3.8 1995-1999 and Firebird 3.8 1995-1999, both unqualified.",
        "groups": [[("Buick", "Lesabre", 2000, 2004),
                    ("Pontiac", "Bonneville", 2000, 2004)],
                   [("Chevrolet", "Camaro", 1995, 1999),
                    ("Pontiac", "Firebird", 1995, 1999)]],
    },
    "toyota-2gr": {
        "evidence": "TYC 2-11137 application table (tycamericas.com, retrieved 2026-10-22; Toyota 27060-31111-84, Lester 11137, 130A): Camry 3.5 2007-2017, Avalon 2005-2018, Highlander 3.5 2008-2013, RAV4 3.5 2009-2010, Venza 3.5 2009-2015, ES 350 2007-2018, RX 350 2007-2009. Sienna and RAV4 06-08 are NOT in this unit — left at likely.",
        "groups": [[("Toyota", "Camry", 2007, 2017),
                    ("Toyota", "Avalon", 2005, 2018),
                    ("Toyota", "Highlander", 2008, 2013),
                    ("Toyota", "RAV4", 2009, 2010),
                    ("Toyota", "Venza", 2009, 2015),
                    ("Lexus", "ES 350", 2007, 2018),
                    ("Lexus", "RX 350", 2007, 2009)]],
    },
    "toyota-1zz": {
        "evidence": "TYC 2-13878 application table (tycamericas.com) + discountstarterandalternator.com VIN-qualified list (Lester 13878, Toyota 27060-22040, retrieved 2026-10-22): Corolla 1ZZ 2003-2008, Matrix 2003-2008 (excl XRS), Vibe 2003-2008 (excl GT), Celica GT 2000-2005, MR2 Spyder 2000-2005. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0432 (80A) Corolla 1ZZ-FE 1998-2001 and Chevrolet Prizm 1.8 1998-2002, both unqualified (the 2002 Corolla splits by build plant — excluded).",
        "groups": [[("Toyota", "Corolla", 2003, 2008),
                    ("Toyota", "Matrix", 2003, 2008),
                    ("Pontiac", "Vibe", 2003, 2008),
                    ("Toyota", "Celica", 2000, 2005),
                    ("Toyota", "MR2 Spyder", 2000, 2005)],
                   [("Toyota", "Corolla", 1998, 2001),
                    ("Chevrolet", "Prizm", 1998, 2002)]],
    },
    "toyota-2uz": {
        "evidence": "Lester 13994 application list (aspwholesale.com, retrieved 2026-10-22; Denso 104210-3380, Toyota 27060-0F040): Tundra 4.7 2003-2009, Sequoia 4.7 2003-2009. Toyota lists a separate OEM number (27060-50320-84) for the 4.7 4Runner — kept out of the group.",
        "groups": [[("Toyota", "Tundra", 2003, 2009),
                    ("Toyota", "Sequoia", 2003, 2009)]],
    },
    "toyota-1gr": {
        "evidence": "Lester 13984 listings (txasap.com: 4Runner 4.0 2003-2009; OEG amazon.com: Tacoma 4.0 2005-2015; Eagle High: FJ Cruiser 2007-2010, Tundra 4.0 2006-2010; Toyota 27060-31020/31021, Denso 104210-3470/4870, retrieved 2026-10-22).",
        "groups": [[("Toyota", "Tacoma", 2005, 2015),
                    ("Toyota", "4Runner", 2003, 2009),
                    ("Toyota", "FJ Cruiser", 2007, 2010),
                    ("Toyota", "Tundra", 2006, 2010)]],
    },
    "nissan-qr25": {
        "evidence": "TYC 2-13939 application table (tycamericas.com, retrieved 2026-10-22) + DB Electrical 400-44053 (Lester 13939, Hitachi LR1110-726): Altima 2.5 2002-2006, Sentra 2.5 (SE-R/Spec V) 2002-2006. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3163 (110A) Frontier 2.5 QR25DE 2005-2011 unqualified.",
        "groups": [[("Nissan", "Altima", 2002, 2006),
                    ("Nissan", "Sentra", 2002, 2006)],
                   [("Nissan", "Frontier", 2005, 2011)]],
    },
    "ford-46-2v": {
        "evidence": "OEG/PartsPlayer listing for Ford F75U-10300-CA/CB 130A 3G (amazon.com, retrieved 2026-10-22): F-150 4.6/5.4 1997-2003, Expedition 5.4 1997-2002. TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08252 Mustang 4.6 SOHC 99-04 is its own 6G unit; 2-07776 Crown Victoria 95-99; 2-07795 Grand Marquis 98-02.",
        "groups": [
            [("Ford", "F-150", 1997, 2003),
             ("Ford", "Expedition", 1997, 2002)],
            [("Ford", "Mustang", 1999, 2004)],
            [("Ford", "Crown Victoria", 1995, 1999)],
            [("Mercury", "Grand Marquis", 1998, 2002)],
        ],
    },
    "ford-54-2v": {
        "evidence": "OEG/PartsPlayer listing for Ford F75U-10300-CA/CB 130A 3G (amazon.com, retrieved 2026-10-22): F-150 4.6/5.4 1997-2003, Expedition 5.4 1997-2002 share one unit.",
        "groups": [[("Ford", "F-150", 1997, 2003),
                    ("Ford", "Expedition", 1997, 2002)]],
    },
    "ford-54-3v": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08318 (Ford 6L3Z-10346-AA) F-150 5.4 2004-2008. Lester 11292 (Ford 9L3Z-10346-C) application table (everychina.com/koeep.com, retrieved 2026-10-22): F-150 4.6/5.4 2009-2010 + Expedition 5.4 2009-2014.",
        "groups": [
            [("Ford", "F-150", 2004, 2008)],
            [("Ford", "F-150", 2009, 2010),
             ("Ford", "Expedition", 2009, 2014)],
        ],
    },
    "gm-gen3-truck": {
        "evidence": "CarQuest weblink part 8292A (Lester 8292, Delco AD244 145A) application summary + aspwholesale.com table (retrieved 2026-10-22): Silverado/Sierra 2003-2006, Tahoe 2003-2004, Yukon 2003-2006, Suburban 2003-2006, Avalanche 2003-2006, Escalade 2003-2005. Earlier 99-02 trucks use the AD230-era unit — left at likely.",
        "groups": [[("Chevrolet", "Silverado*", 2003, 2006),
                    ("GMC", "Sierra*", 2003, 2006),
                    ("Chevrolet", "Tahoe", 2003, 2004),
                    ("GMC", "Yukon*", 2003, 2006),
                    ("Chevrolet", "Suburban*", 2003, 2006),
                    ("Chevrolet", "Avalanche", 2003, 2006),
                    ("Cadillac", "Escalade*", 2003, 2005)]],
    },
    "gm-gen4-truck": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08302 (GM 15225927) C/K pickup 4.8/5.3 2005-2010 — clipped to this family's 2007+ window.",
        "groups": [[("Chevrolet", "Silverado*", 2007, 2010),
                    ("GMC", "Sierra*", 2007, 2010)]],
    },
    "gm-ecotec24": {
        "evidence": "TYC 2-11459 application table (tycamericas.com, retrieved 2026-10-22; Lester 11459, GM 13512759): Equinox 2.4 2010-2017, Terrain 2.4 2010-2017. Lester 11265 (Valeo, GM 15828450/22762984) application list (am-autoparts.com, retrieved 2026-10-22) includes Saturn Vue 2.4 2008-2010. Cobalt/Malibu/G6-era LE5 uses a different unit — left at likely.",
        "groups": [[("Chevrolet", "Equinox", 2010, 2017),
                    ("GMC", "Terrain", 2010, 2017)],
                   [("Saturn", "VUE", 2008, 2010)]],
    },
    "gm-llt36": {
        "evidence": "BBB Industries 11252 fitment table (partcatalog.com) + Brillman Denso 170A listing (GM 25815839/23105717, retrieved 2026-10-22): Traverse 2009-2017, Acadia 2007-2016, Enclave 2008-2017, Outlook 2007-2010. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0531 (130A) CTS 3.6 2004-2005 (also the 2.8); 210-0641 (145A) CTS 3.6 2008-2009; 210-0765 (150A) CTS 3.0/3.6 2010-2013; 210-0576 (150A) SRX 3.6 2004-2009 and STS 3.6 2005-2011. SRX 2010+ rows carry pulley qualifiers — left at likely.",
        "groups": [[("Chevrolet", "Traverse", 2009, 2017),
                    ("GMC", "Acadia", 2007, 2016),
                    ("Buick", "Enclave", 2008, 2017),
                    ("Saturn", "Outlook", 2007, 2010)],
                   [("Cadillac", "CTS", 2004, 2005)],
                   [("Cadillac", "CTS", 2008, 2009)],
                   [("Cadillac", "CTS", 2010, 2013)],
                   [("Cadillac", "SRX", 2004, 2009),
                    ("Cadillac", "STS", 2005, 2011)]],
    },
    "mopar-pentastar": {
        "evidence": "TYC 2-11570 fitment list (finditparts.com) + BBB 11570 table (partcatalog.com; Chrysler 68272108AD, Denso 421000-0770, retrieved 2026-10-22): Grand Caravan 2011-2020, Town & Country 2011-2016, Journey 3.6 2011-2019, Avenger 3.6 2011-2014, 200 3.6 2011-2014.",
        "groups": [[("Dodge", "Grand Caravan", 2011, 2020),
                    ("Chrysler", "Town & Country", 2011, 2016),
                    ("Chrysler", "Town And Country", 2011, 2016),
                    ("Dodge", "Journey", 2011, 2019),
                    ("Dodge", "Avenger", 2011, 2014),
                    ("Chrysler", "200", 2011, 2014)]],
    },
    "hk-theta-gdi": {
        "evidence": "Hyundai 37300-2G150 (Lester 11491/11492, Valeo TG11C087) listings (rareelectrical.com + amazon.com, retrieved 2026-10-22): Sonata 2.4 2011-2013, Optima 2.4 2011-2013. The 2.0T and 2014+ units differ — left at likely.",
        "groups": [[("Hyundai", "Sonata", 2011, 2013),
                    ("Kia", "Optima", 2011, 2013)]],
    },
    "nissan-vq35de": {
        "evidence": "OCPTY Lester 13940 listing (Hitachi LR1110-721, Nissan 23100-8J100, retrieved 2026-10-22): Altima 3.5 2002-2006, Maxima 2002-2003, Murano 2003-2007, Infiniti I35 2002-2004. Nissan OEM 23100-7Y020 (nissanpartsdeal.com): Maxima 3.5 2004-2008 is a separate unit. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4255 (130A) Maxima 3.5 2009-2010 and Murano 2009 — later A35 Maximas (2011-14) use the same VQ35DE but this catalog edition ends there, left at likely; 210-4211 (110A) 350Z VQ35DE 2003-2006 and G35 2004-2006 (the 2003 G35 sedan row is body-qualified and excluded); 210-4207 (110A) Pathfinder 3.5 2003-2004; 210-3150 (110A) Pathfinder 3.5 2002.",
        "groups": [
            [("Nissan", "Altima", 2002, 2006),
             ("Nissan", "Maxima", 2002, 2003),
             ("Nissan", "Murano", 2003, 2007),
             ("Infiniti", "I35", 2002, 2004)],
            [("Nissan", "Maxima", 2004, 2008)],
            [("Nissan", "Maxima", 2009, 2010),
             ("Nissan", "Murano", 2009, 2009)],
            [("Nissan", "350Z", 2003, 2006),
             ("Infiniti", "G35", 2004, 2006)],
            [("Nissan", "Pathfinder", 2003, 2004)],
            [("Nissan", "Pathfinder", 2002, 2002)],
        ],
    },
    "honda-k24a": {
        "evidence": "TYC 2-13980 application table (tycamericas.com, retrieved 2026-10-22; Honda 31100-RAA-A05, Lester 13980): Accord 2.4 2003-2007, Element 2003-2011, TSX 2004-2008, CR-V 2007-2011. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4168 (90A) CR-V 2.4 K24A1 2002-2006 — its own published unit, unqualified.",
        "groups": [[("Honda", "Accord", 2003, 2007),
                    ("Honda", "Element", 2003, 2011),
                    ("Acura", "TSX", 2004, 2008),
                    ("Honda", "CR-V", 2007, 2011)],
                   [("Honda", "CR-V", 2002, 2006)]],
    },
    "gm-14t": {
        "evidence": "Rareelectrical FG12S031/Lester 11399 listing (GM 13577154/13597226, retrieved 2026-10-22): Cruze 1.4T 2011 ONLY, Encore 2013-2021, Trax 2015-2021. Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6019 (130A) Cruze 1.4 2012-2013 unqualified.",
        "groups": [[("Chevrolet", "Cruze", 2011, 2011),
                    ("Buick", "Encore", 2013, 2021),
                    ("Chevrolet", "Trax", 2015, 2021)],
                   [("Chevrolet", "Cruze", 2012, 2013)]],
    },
    "ford-mzr": {
        "evidence": "Lester 11172 application table (cautop.com; Mitsubishi A3TJ0891, Ford 6E5Z-10346-AA, retrieved 2026-10-22): Fusion 2.3 2006-2009, Milan 2.3 2006-2009. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4214 (90A) Mazda3 2.0 2004-2009, Mazda3 2.3 2004-2006 and non-turbo 2007-2009, Mazda5 2.3 2006-2007; 210-4303 (100A) Mazda3 2.0 2010-2011; 210-4327 (110A) Mazda5 2.3 2008-2010; 210-4238 (100A) Mazda6 2.3 2008 and 2.5 2009; 210-0615 (170A) Fusion 2.5 AND 2.0 Turbo 2013-2014 (one unit spans both engines); 210-4304 (150A) Focus 2.0 2009-2010 unqualified (2008 splits by trim vendor, 2011 is Mitsubishi-unit-qualified). Mazda6 2.3 03-05 splits by transmission and Mazdaspeed turbos differ — left at likely.",
        "groups": [[("Ford", "Fusion", 2006, 2009),
                    ("Mercury", "Milan", 2006, 2009)],
                   [("Mazda", "3", 2004, 2009),
                    ("Mazda", "5", 2006, 2007)],
                   [("Mazda", "3", 2010, 2011)],
                   [("Mazda", "5", 2008, 2010)],
                   [("Mazda", "6", 2008, 2009)],
                   [("Ford", "Fusion", 2013, 2014)],
                   [("Ford", "Focus", 2009, 2010)]],
    },
    "ford-cyclone": {
        "evidence": "DSS/TRQ Lester 11273 application table (Ford 7T4Z-10346-A, Mitsubishi A3TJ1291, retrieved 2026-10-22): Edge 2007-2014, Taurus 3.5 2008-2012. Quality-Built 11271 175A (Ford 8A4Z-10346-A, partshawk.com): Taurus 2008-2012, Flex 2009-2012, Edge 2011-2013, Explorer 2011-2012. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0533 (150A) Mustang 3.7 and 5.0 2012-2013 unqualified (11/14 rows split by transmission — excluded); 210-4316 (150A) Edge 3.5 2010-2015, Taurus 3.5 2008-2009 and 2012 (10-11 rows are option-qualified), Sable 3.5 2008-2009, MKZ 3.5 2011-2012.",
        "groups": [
            [("Ford", "Edge", 2007, 2014),
             ("Ford", "Taurus", 2008, 2012)],
            [("Ford", "Taurus", 2008, 2012),
             ("Ford", "Flex", 2009, 2012),
             ("Ford", "Edge", 2011, 2013),
             ("Ford", "Explorer", 2011, 2012)],
            [("Ford", "Mustang", 2012, 2013)],
            [("Ford", "Edge", 2010, 2015),
             ("Ford", "Taurus", 2008, 2009),
             ("Ford", "Taurus", 2012, 2012),
             ("Mercury", "Sable", 2008, 2009),
             ("Lincoln", "MKZ", 2011, 2012)],
        ],
    },
    "gm-atlas42": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08290 (GM 19151920) Trailblazer/Envoy 4.2 L6 2002-2006.",
        "groups": [[("Chevrolet", "Trailblazer", 2002, 2006),
                    ("GMC", "Envoy", 2002, 2006)]],
    },
    "ford-40sohc": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-07787 (Ford 1L2Z-10346-AB) Explorer 4.0 1997-2003 (97-01 SOHC, 02-03 all); 2-08258 (1L5Z-10346-BA) Ranger 4.0 2001-2005; 2-08437 (6R3Z-10346-A) Mustang 4.0 2005-2008. Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0701 (150A) Mustang 4.0 2009-2010; Mountaineer 4.0: 210-5320 (130A) 1998-2001 (one number covers OHV and SOHC), 210-5316 (130A) 2005-2008, 210-4307 (115A) 2009-2010, all unqualified (02-04 rows carry rear-cover/build-date qualifiers).",
        "groups": [
            [("Ford", "Explorer", 1997, 2003)],
            [("Ford", "Ranger", 2001, 2005)],
            [("Ford", "Mustang", 2005, 2008)],
            [("Ford", "Mustang", 2009, 2010)],
            [("Mercury", "Mountaineer", 1998, 2001)],
            [("Mercury", "Mountaineer", 2005, 2008)],
            [("Mercury", "Mountaineer", 2009, 2010)],
        ],
    },
    "ford-vulcan30": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08263 (YF1Z-10V346-FA) Taurus/Sable 3.0 OHV 2000-2001; 2-08268 (3F1Z-10346-AB) Taurus/Sable 3.0 OHV 2002-2006. Fitment data exists, but the Vulcan/Duratec decode ambiguity keeps every pair at likely in the app.",
        "groups": [
            [("Ford", "Taurus", 2000, 2001),
             ("Mercury", "Sable", 2000, 2001)],
            [("Ford", "Taurus", 2002, 2006),
             ("Mercury", "Sable", 2002, 2005)],
        ],
    },
    "ford-duratec30": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-08259 (1L8Z-10V346-CCRM) Escape 3.0 2001-2004; 2-08403 (ZZC2-18-300) Escape 3.0 2005-2006; 2-08269 (2F1Z-10346-BA) Taurus 3.0 DOHC 2002-2005; 2-08442 (6F9Z-10346-AA) Five Hundred 3.0 2005-2007.",
        "groups": [
            [("Ford", "Escape", 2001, 2004)],
            [("Ford", "Escape", 2005, 2006)],
            [("Ford", "Taurus", 2002, 2005)],
            [("Ford", "Five Hundred", 2005, 2007)],
        ],
    },
    "mopar-minivan": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-11295 (Chrysler 4801304AC) Caravan 3.3/3.8 2008-2010.",
        "groups": [[("Dodge", "Grand Caravan", 2008, 2010)]],
    },
    "mopar-hemi57": {
        "evidence": "TYC catalog PDF (wordwideparts.com, retrieved 2026-10-22): 2-11298 (Chrysler 5602869, Denso 7S) Ram 5.7 2007-2008.",
        "groups": [[("Dodge|Ram", "Ram*", 2007, 2008)]],
    },
    # ================= 2026-10 PHASE A — enthusiast platforms ==============
    "toyota-4a": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0100 (17mm shaft) and 210-0101 (15mm shaft) both list Corolla 4A-FE 1.6 and 7A-FE 1.8 1993-1997 with identical spans — two published shaft diameters, match yours; 210-0152 Corolla 4A-FE 1990 unqualified (1991-92 rows are stamp-number-qualified, 88-89 split 4A-F/FE vs the twin-cam 4A-GE, and Prizm rows are fan- or vendor-qualified — all excluded).",
        "groups": [
            [("Toyota", "Corolla", 1993, 1997)],
            [("Toyota", "Corolla", 1990, 1990)],
        ],
    },
    "toyota-3s": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0103 (70A) Celica 3S-FE and 3S-GE 1988-1989, one unit for both; 210-0274 (60A) Celica 3S-FE/3S-GE 1987; 210-0264 (80A) Celica All-Trac 3S-GTE 1992-1993 (the only 2.0 Celica those years). The 90-93 5S-FE 2.2 rows split by transmission and belong to toyota-5s anyway; MR2 Turbo rows aren't separately published — MR2 pairs stay Likely.",
        "groups": [
            [("Toyota", "Celica", 1988, 1989)],
            [("Toyota", "Celica", 1987, 1987)],
            [("Toyota", "Celica", 1992, 1993)],
        ],
    },
    "toyota-m6": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0158 (80A) Cressida 7M-GE 1989-1992 unqualified (the Supra rows for the same unit are turbo/transmission-qualified and excluded); 210-0167 (60A) Cressida 5M-GE 1987-1988; 210-0111 (60A) Cressida 5M-GE 1984-1986 (clipped to this family's 1985 start).",
        "groups": [
            [("Toyota", "Cressida", 1989, 1992)],
            [("Toyota", "Cressida", 1987, 1988)],
            [("Toyota", "Cressida", 1985, 1986)],
        ],
    },
    "toyota-2jz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 2JZGE and unqualified: 210-0506 (100A) GS300 2001-2005 and IS300 2001-2005; 210-0286 (100A) GS300 1999-2000 (the 1998 row is production-split and excluded); 210-0293 (80A) GS300 1996-1997; 210-0169 (80A) GS300 1993-1995; 210-0290 (80A) SC300 1997-2000; 210-0287 (80A) SC300 1996 (the 1995 rows are production-split); 210-0168 (100A) SC300 1992-1994. Supra rows split NA/turbo and by transmission — excluded.",
        "groups": [
            [("Lexus", "GS300", 2001, 2005), ("Lexus", "IS300", 2001, 2005)],
            [("Lexus", "GS300", 1999, 2000)],
            [("Lexus", "GS300", 1996, 1997)],
            [("Lexus", "GS300", 1993, 1995)],
            [("Lexus", "SC300", 1997, 2000)],
            [("Lexus", "SC300", 1996, 1996)],
            [("Lexus", "SC300", 1992, 1994)],
        ],
    },
    "honda-d-ef": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0227 (60A) Civic D15B2 1990-1991, Civic D16A6 1990-1991, CRX D15B2/D15B6 1990-1991 and CRX D16A6 1990-1991 — one unqualified unit across both engines and models. The 1988-89 rows are vendor-split (DENSO Unit) and excluded.",
        "groups": [
            [("Honda", "Civic", 1990, 1991), ("Honda", "CRX", 1990, 1991)],
        ],
    },
    "honda-d-eg": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4133 lists Civic D15B7/B8/Z1 1994-1995 and Del Sol D15B7 1993-1995 unqualified; for the 1.6 D16Z6 (Civic 92-95, Del Sol 93-95) the catalog publishes two interchange-equivalent sourcings with identical spans — Denso-built 210-0213 and Mitsubishi-built 210-4133 — so every 92-95 D-series car is covered by a published list; match the vendor tag on a 1.6 (3MZ-precedent dual-list note). VTEC (B16A3) Del Sols are a different engine and capped by the app-level ambiguity flag.",
        "groups": [
            [("Honda", "Civic", 1992, 1995),
             ("Honda", "Civic Del Sol", 1993, 1995),
             ("Honda", "Del Sol", 1993, 1995)],
        ],
    },
    "honda-b18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0223 (65A) Integra B18A1 1990-1991; 210-0214 (80A) Integra B18A1 1992-1993 and B17A1 1993; 210-0211 (90A) Integra B18B1 and B18C1 1994-1995, one unit for both. The 96-01 span splits by trim (Type R B18C5 210-4190 vs all others 210-0199) — excluded from verified; match part number there.",
        "groups": [
            [("Acura", "Integra", 1990, 1991)],
            [("Acura", "Integra", 1992, 1993)],
            [("Acura", "Integra", 1994, 1995)],
        ],
    },
    "honda-k20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0525 (80A) Civic 2.0 (K20A3, EP3 Si) 2002-2005 unqualified; 210-0609 (105A) Civic 2.0 K20Z3 (FG/FA Si) 2006-2011 unqualified. RSX rows split by trim (Type S 210-0507 vs base 210-4168) and are excluded.",
        "groups": [
            [("Honda", "Civic", 2002, 2005)],
            [("Honda", "Civic", 2006, 2011)],
        ],
    },
    "honda-f20c": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0458 (105A) S2000 F20C1 2000-2003; 210-0597 (105A) S2000 F22C1 2004-2005, both unqualified. 2006-09 (same F22C1) is past this catalog edition — left at likely.",
        "groups": [
            [("Honda", "S2000", 2000, 2003)],
            [("Honda", "S2000", 2004, 2005)],
        ],
    },
    "honda-h22": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0197 (90A) Prelude H22A4 1997-1998; 210-0456 (90A) Prelude H22A4 1999-2001, both unqualified. The 92-96 span splits three ways (F22A1 non-VTEC 210-0216 / H22A1 VTEC 210-0217 / H23A1 2.3 210-0215) — year spans can't separate the trims, so 92-96 stays at likely.",
        "groups": [
            [("Honda", "Prelude", 1997, 1998)],
            [("Honda", "Prelude", 1999, 2001)],
        ],
    },
    "mazda-miata-16": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4184 (60A) Miata 1.6 1990 unqualified — the 1991-93 rows for the same and sibling units are transmission-qualified (M/T 210-4184 / A/T 210-4270) and excluded.",
        "groups": [
            [("Mazda", "Miata", 1990, 1990), ("Mazda", "MX-5*", 1990, 1990)],
        ],
    },
    "mazda-miata-18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3155 (70A) Miata 1.8 1999-2000; 210-3157 (80A) Miata 1.8 2001-2005, both unqualified. The 1994-97 (NA8) rows split by transmission (210-4157 A/T / 210-4284 M/T) and are excluded.",
        "groups": [
            [("Mazda", "Miata", 1999, 2000), ("Mazda", "MX-5*", 1999, 2000)],
            [("Mazda", "Miata", 2001, 2005), ("Mazda", "MX-5*", 2001, 2005)],
        ],
    },
    "mazda-miata-nc": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4238 (100A) MX-5 Miata 2.0 2006-2008 (the same published list covers the 2006-09 Mazda6); 210-4334 (100A) MX-5 Miata 2.0 2009-2012, both unqualified. 2013-15 is past this catalog edition — left at likely.",
        "groups": [
            [("Mazda", "Miata", 2006, 2008), ("Mazda", "MX-5*", 2006, 2008)],
            [("Mazda", "Miata", 2009, 2012), ("Mazda", "MX-5*", 2009, 2012)],
        ],
    },
    "mazda-rx7": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4241 (100A) RX-7 1.3 rotary 1993-1995 unqualified (the FD span). The 86-88 FC row is turbo-qualified and 89-92 FC rows aren't published — both excluded.",
        "groups": [
            [("Mazda", "RX-7", 1993, 1995), ("Mazda", "RX7", 1993, 1995)],
        ],
    },
    "mazda-rx8": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4213 (100A) RX-8 2005-2007 (the 2004 row is build-date-qualified 'From 04/04/2003' and excluded); 210-4343 (110A) RX-8 2009-2011, unqualified. No 2008 alternator row is published — 2008 stays at likely.",
        "groups": [
            [("Mazda", "RX-8", 2005, 2007), ("Mazda", "RX8", 2005, 2007)],
            [("Mazda", "RX-8", 2009, 2011), ("Mazda", "RX8", 2009, 2011)],
        ],
    },
    "nissan-vq-hr": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4313 (150A) in one published application set — 350Z VQ35HR 2007-2009, G35 VQ35HR 2007-2008 (both 07 trim rows carry the same number), G37 VQ37VHR 2008-2010, 370Z VQ37VHR 2009 (the 2010 370Z rows are build-date-qualified 'To 02/2010' and excluded).",
        "groups": [
            [("Nissan", "350Z", 2007, 2009),
             ("Infiniti", "G35", 2007, 2008),
             ("Infiniti", "G37", 2008, 2010),
             ("Nissan", "370Z", 2009, 2009)],
        ],
    },
    "mitsu-dsm": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4120 (90A) Eclipse 1999 listed for the 420A and the 4G63 turbo alike, unqualified — one published unit for every 99 Eclipse. All earlier DSM rows split by transmission, turbo or drivetrain and are excluded.",
        "groups": [
            [("Mitsubishi", "Eclipse", 1999, 1999)],
        ],
    },
    "mitsu-24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 4G64/4G69 and unqualified: 210-4215 (110A) Eclipse 2.4 2006-2011, Galant 2.4 2004-2011 and Lancer 2.4 2005-2006 — one published unit across all three; 210-4142 (85A) Galant 2.4 2000-2003; 210-4156 (90A) Galant 2.4 1997-1999; 210-4160 (90A) Eclipse 2.4 2000-2001 (the 02-05 rows split by transmission and are excluded).",
        "groups": [
            [("Mitsubishi", "Eclipse", 2006, 2011),
             ("Mitsubishi", "Galant", 2004, 2011),
             ("Mitsubishi", "Lancer", 2005, 2006)],
            [("Mitsubishi", "Galant", 2000, 2003)],
            [("Mitsubishi", "Galant", 1997, 1999)],
            [("Mitsubishi", "Eclipse", 2000, 2001)],
        ],
    },
    "mitsu-6g72": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4179 (85A) in one published set — Eclipse 3.0 2002-2005 and 2000, Galant 3.0 2002-2003 and 1999-2000, plus Sebring 3.0 coupe 2001-2005, all unqualified (2001 rows aren't printed for Eclipse/Galant, so their 2001 cars sit between spans).",
        "groups": [
            [("Mitsubishi", "Eclipse", 2002, 2005),
             ("Chrysler", "Sebring", 2001, 2005),
             ("Mitsubishi", "Eclipse", 2000, 2000),
             ("Mitsubishi", "Galant", 2002, 2003),
             ("Mitsubishi", "Galant", 1999, 2000)],
        ],
    },
    "mitsu-6g75": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4230 (110A) Eclipse 3.8 2006-2011 and Galant 3.8 2005-2009, one published unit, unqualified; 210-4208 (110A) Galant 3.8 2004.",
        "groups": [
            [("Mitsubishi", "Eclipse", 2006, 2011),
             ("Mitsubishi", "Galant", 2005, 2009)],
            [("Mitsubishi", "Galant", 2004, 2004)],
        ],
    },
    "mitsu-evo": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4229 (90A) Lancer 4G63 'w/ Turbo' 2003-2006 — every US Lancer Evolution those years is the 4G63 turbo, so the span is exact for the Evolution model; 210-4338 (130A) Lancer 4B11 'w/ Turbo' 2008-2011 — the Evo X span (the Ralliart shares the engine but is a separate feed model). 2012-15 Evo X is past this catalog edition — left at likely.",
        "groups": [
            [("Mitsubishi", "Lancer Evolution", 2003, 2006)],
            [("Mitsubishi", "Lancer Evolution", 2008, 2011)],
        ],
    },
    "subaru-ej205": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4167 (75A) Impreza EJ205 2.0 2002-2005 unqualified (the same published list covers the 03-04 EJ251 2.5 NA, which lives in subaru-ej25na).",
        "groups": [
            [("Subaru", "WRX", 2002, 2005),
             ("Subaru", "Impreza WRX", 2002, 2005)],
        ],
    },
    "bmw-m52": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5395 (140A) 528i 2.8 1997-1998 unqualified — the Z3 2.8 rows for the same unit are case-size-qualified and excluded; every other E36-era row is OEM-number- or case-qualified (Bosch vs Valeo sourcing) and excluded.",
        "groups": [
            [("BMW", "528i", 1997, 1998)],
        ],
    },
    "ford-46-3v": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5367 (135A) Mustang 4.6 2006-2008 unqualified (the 2009 row for the same unit is transmission-qualified and excluded); 210-5355 (135A) Mustang 4.6 2005. 09-10 rows split by transmission — left at likely.",
        "groups": [
            [("Ford", "Mustang", 2006, 2008)],
            [("Ford", "Mustang", 2005, 2005)],
        ],
    },
    "ford-coyote": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0533 (150A) Mustang 5.0 2012-2013 unqualified (the same published list covers the 3.7 and the 13 GT500 5.8); 210-0743 (200A) F-150 5.0 2012-2014 unqualified (the 11-14 'w/ Power Converter' rows are option-qualified and excluded).",
        "groups": [
            [("Ford", "Mustang", 2012, 2013)],
            [("Ford", "F-150", 2012, 2014), ("Ford", "F150*", 2012, 2014)],
        ],
    },
    "ford-essex38": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5207 and 210-5310 both list Mustang 3.8 1994-2000 with identical spans (two published 130A case styles — match yours); 210-5348 (110A) Mustang 3.8 2001-2004 and 3.9 2004, unqualified.",
        "groups": [
            [("Ford", "Mustang", 1994, 2000)],
            [("Ford", "Mustang", 2001, 2004)],
        ],
    },
    "gm-fbody-tpi": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5144 (100A) Camaro and Firebird 5.0 (E/F) and 5.7 (8) 1988-1989 — one unqualified unit across both displacements and models; 210-5102 (100A) the same four applications 1990-1992. Pre-88 rows and C4 Corvette alternator rows aren't published — left at likely.",
        "groups": [
            [("Chevrolet", "Camaro", 1988, 1989),
             ("Pontiac", "Firebird", 1988, 1989)],
            [("Chevrolet", "Camaro", 1990, 1992),
             ("Pontiac", "Firebird", 1990, 1992)],
        ],
    },
    "gm-ls1-car": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5164 (102A, engine code G) Camaro 5.7 1998-2002 and Firebird 5.7 1998-2002, one published unit, unqualified. Denso First Time Fit 211-6025 (145A) Corvette 5.7 2004 (the 2003 row is transmission/design-qualified and excluded; 97-02 C5 alternator rows aren't published).",
        "groups": [
            [("Chevrolet", "Camaro", 1998, 2002),
             ("Pontiac", "Firebird", 1998, 2002)],
            [("Chevrolet", "Corvette", 2004, 2004)],
        ],
    },
    "gm-corvette-c6": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6020 (145A) Corvette 6.0 2005-2007, 7.0 2006-2012 and 6.2 2008-2012 — one published unit across the LS2/LS3/LS7; the supercharged ZR1 (211-6028) is its own unit, so the verified span stops at 2008 before the ZR1 enters the fleet. Denso reman 210-0325 (150A) Camaro 6.2 2012-2013 (the 2014 row is stamp-qualified and excluded).",
        "groups": [
            [("Chevrolet", "Corvette", 2005, 2008)],
            [("Chevrolet", "Camaro", 2012, 2013)],
        ],
    },
    # ================= 2026-10 PHASE B — high-volume commuters =============
    "nissan-ga16": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3127 (80A) Sentra 1.6 GA16DE 1997-1999 unqualified; 210-3117 (70A) Sentra 1.6 1995-1996 unqualified. 200SX rows are not published separately in this edition.",
        "groups": [
            [("Nissan", "Sentra", 1997, 1999)],
            [("Nissan", "Sentra", 1995, 1996)],
        ],
    },
    "nissan-qg18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3158 (80A) Sentra 1.8 QG18DE 2002-2006 unqualified; 210-3147 (100A) Sentra 1.8 2000-2001 unqualified.",
        "groups": [
            [("Nissan", "Sentra", 2002, 2006)],
            [("Nissan", "Sentra", 2000, 2001)],
        ],
    },
    "nissan-vg30-maxima": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3131 (90A) Maxima 3.0 VG30E 1989-1991 unqualified (the 92-94 rows are SOHC-vs-DOHC split between 210-3131 and 210-3135 and stay Likely).",
        "groups": [[("Nissan", "Maxima", 1989, 1991)]],
    },
    "nissan-vq30": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3106 (125A) in one published set — Maxima 3.0 VQ30DE 1995-1997 and I30 1996-1997; 210-3105 (110A) Maxima 1999 and 2001 (1998 splits SE vs Exc. SE) and I30 1998-2001; 210-3137 (100A) Maxima 2000.",
        "groups": [
            [("Nissan", "Maxima", 1995, 1997), ("Infiniti", "I30", 1996, 1997)],
            [("Nissan", "Maxima", 1999, 1999), ("Nissan", "Maxima", 2001, 2001),
             ("Infiniti", "I30", 1998, 2001)],
            [("Nissan", "Maxima", 2000, 2000)],
        ],
    },
    "nissan-vg33": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3134 (90A) Pathfinder 3.3 VG33E 1998-2000 (1997 splits 1st/2nd production); 210-3128 (80A) Xterra 3.3 2000 and Frontier 3.3 1999-2000; 210-3149 (100A) Xterra and Frontier 3.3 2003-2004 incl. the supercharged VG33ER.",
        "groups": [
            [("Nissan", "Pathfinder", 1998, 2000)],
            [("Nissan", "Xterra", 2000, 2000), ("Nissan", "Frontier", 1999, 2000)],
            [("Nissan", "Xterra", 2003, 2004), ("Nissan", "Frontier", 2003, 2004)],
        ],
    },
    "honda-b20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0196 (95A) CR-V 2.0 B20B4 1997-1998 unqualified. The 99-01 B20Z2 rows split M/T vs A/T and stay Likely.",
        "groups": [[("Honda", "CR-V", 1997, 1998)]],
    },
    "gm-ecotec-lcv": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0255 (110A) Malibu 2013 — one published unit across the 2.0 turbo, 2.4 and 2.5. 2014-15 alternator rows are beyond this catalog edition.",
        "groups": [[("Chevrolet", "Malibu", 2013, 2013)]],
    },
    "toyota-1nz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0799 (80A) Yaris 1.5 1NZ-FE 2010-2014 unqualified; 210-0619 (80A) Yaris 1.5 2007-2009 unqualified.",
        "groups": [
            [("Toyota", "Yaris", 2010, 2014)],
            [("Toyota", "Yaris", 2007, 2009)],
        ],
    },
    "honda-l15": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4299 (75A) Fit 1.5 L15A1 2007-2008 unqualified (2015 rows split CVT vs M/T).",
        "groups": [[("Honda", "Fit", 2007, 2008)]],
    },
    "kia-spectra": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6002 (90A) Spectra 2.0 2008-2009 unqualified (05-07 rows split Valeo vs Mando vendor; the 2004 2.0 row is excluded because early-2004 1.8 cars used the vendor-split unit); 211-6011 (90A) Spectra 1.8 2000-2001 unqualified.",
        "groups": [
            [("Kia", "Spectra", 2008, 2009)],
            [("Kia", "Spectra", 2000, 2001)],
        ],
    },
    "kia-forte1": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6014 (100A) Forte Koup 2.0 and 2.4 2010-2013, one published unit, unqualified (sedan 2.0 splits hydraulic vs electric power steering those years and stays Likely).",
        "groups": [[("Kia", "Forte Koup", 2010, 2013)]],
    },
    "mazda-cx7": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4312 (110A) — one published unit for CX-7 2.3 turbo 2007-2011 and 2.5 2010-2011.",
        "groups": [
            [("Mazda", "CX-7", 2007, 2011), ("Mazda", "CX7", 2007, 2011)],
        ],
    },
    "mazda-cx9": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4321 (110A) — one published unit for CX-9 3.5 2007 and 3.7 2008-2011.",
        "groups": [
            [("Mazda", "CX-9", 2007, 2011), ("Mazda", "CX9", 2007, 2011)],
        ],
    },
    "mopar-pacifica": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0671 (120A) Pacifica 3.5 2004-2006 — kept to 2004 only (the sole-3.5 model year); 05-06 also fielded the 3.8 whose alternator is not published for those years, and 07-08 units differ 3.8 (210-4340) vs 4.0 (210-0632), so cross-engine years stay Likely.",
        "groups": [[("Chrysler", "Pacifica*", 2004, 2004)]],
    },
    "ford-mod-sd": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5350 (110A) F-250 Super Duty 5.4 and V10 6.8 2002-2003, unqualified; 210-5205 (115A) Navigator 5.4 2000-2002; 210-0760 (150A) Navigator 5.4 2005-2009. E-Series rows split by case diameter/battery-post options and stay Likely.",
        "groups": [
            [("Ford", "F-250*", 2002, 2003), ("Ford", "F250*", 2002, 2003)],
            [("Lincoln", "Navigator*", 2000, 2002),
             ("Ford", "Navigator*", 2000, 2002)],
            [("Lincoln", "Navigator*", 2005, 2009),
             ("Ford", "Navigator*", 2005, 2009)],
        ],
    },
    "kia-sedona1": {
        "evidence": "Denso First Time Fit + reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6013 (120A) Sedona 3.5 2002-2005 unqualified; 210-0711 (130A) Sedona 3.8 2006-2007 unqualified (08-09 split by rear-DVD option); 210-5000 (150A) Sedona 3.5 2011-2012 and 2014 (2015 is AMS-qualified).",
        "groups": [
            [("Kia", "Sedona", 2002, 2005)],
            [("Kia", "Sedona", 2006, 2007)],
            [("Kia", "Sedona", 2011, 2012), ("Kia", "Sedona", 2014, 2014)],
        ],
    },
    "kia-sorento1": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6003 (120A) Sorento 3.5 2003-2006 — one published unit, unqualified.",
        "groups": [[("Kia", "Sorento", 2003, 2006)]],
    },
    "hk-delta27": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6010 (120A) in one published set — Tucson 2.7 2005-2009, Tiburon 2.7 2005-2008, Sportage 2.7 2005-2010, Sonata 2.7 2005 and Santa Fe 2.7 2005-2006, all unqualified (Sonata/Tiburon 03-04 rows carry pulley/build-date qualifiers).",
        "groups": [
            [("Hyundai", "Tucson", 2005, 2009),
             ("Hyundai", "Tiburon", 2005, 2008),
             ("Kia", "Sportage", 2005, 2010),
             ("Hyundai", "Sonata", 2005, 2005),
             ("Hyundai", "Santa Fe", 2005, 2006)],
        ],
    },
    "hk-sirius24": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6007 (110A) — one published unit for Sonata 2.4 1999-2005 and Optima 2.4 2001-2006, unqualified.",
        "groups": [
            [("Hyundai", "Sonata", 1999, 2005), ("Kia", "Optima", 2001, 2006)],
        ],
    },
    "hk-theta24": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6014 (110A) Sonata 2.4 2006-2008 and Optima 2.4 2006-2010 — one published unit, unqualified (Sonata 09-10 rows are option-qualified — excluded).",
        "groups": [
            [("Hyundai", "Sonata", 2006, 2008), ("Kia", "Optima", 2006, 2010)],
        ],
    },
    "hk-theta2gdi": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6030 (110A) Sonata 2.4 2014 and 2.0T 2011-2013 (SE and Limited rows cover the turbo lineup) and Optima 2.4 2012-2013 and 2.0T 2011-2013 — spans capped to the years where BOTH engines publish the one number (Sonata 2.4 11-13 rows are absent from this catalog edition).",
        "groups": [
            [("Hyundai", "Sonata", 2014, 2014), ("Kia", "Optima", 2012, 2013)],
        ],
    },
    "honda-j37": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0580 (130A) MDX 3.7 J37A1 2007-2009 (continues from the 03-06 3.5); 210-0750 (130A) MDX 3.7 2010-2013, both unqualified.",
        "groups": [
            [("Acura", "MDX", 2007, 2009)],
            [("Acura", "MDX", 2010, 2013)],
        ],
    },
    "acura-tl": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0750 (130A) TL 3.5 (J35Z6) AND 3.7 (J37A4) 2009-2014 — one unit for both engines; 210-0580 (130A) TL 3.2 (J32A3) 2004-2008 and 3.5 (J35A8) 2007-2008; 210-0675 (105A) TL 3.2 2000-2003 base — Type S 02-03 uses its own unit (210-0453), so the verified span stops at 2001; 210-0444 (105A) TL 3.2 1999.",
        "groups": [
            [("Acura", "TL", 2009, 2014)],
            [("Acura", "TL", 2004, 2008)],
            [("Acura", "TL", 2000, 2001)],
            [("Acura", "TL", 1999, 1999)],
        ],
    },
    "ford-windstar38": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5343 (135A) Windstar 3.8 1999-2003 — one published unit, unqualified (the 1995 3.8 rows split by build date; 96-98 Windstars are 3.0-only).",
        "groups": [[("Ford", "Windstar", 1999, 2003)]],
    },
    "mopar-neon": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Dodge rows all unqualified: 210-4139 (85A) Neon 2.0 2000-2005 (a 145A option unit, 210-0558, is also listed for 2003 — match amperage); 210-4138 (83A) 1998-1999; 210-4119 (83A) 1996-1997; 210-4233 (85A) 1995. Plymouth spans not separately published — left at likely.",
        "groups": [
            [("Dodge", "Neon", 2000, 2005)],
            [("Dodge", "Neon", 1998, 1999)],
            [("Dodge", "Neon", 1996, 1997)],
            [("Dodge", "Neon", 1995, 1995)],
        ],
    },
    "gm-jbody22": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5117 (105A) Cavalier 2.2 1996-2002 and Sunfire 2.2 1996-2002 — one published unit, unqualified; 210-5157 (105A) both cars 1995.",
        "groups": [
            [("Chevrolet", "Cavalier", 1996, 2002),
             ("Pontiac", "Sunfire", 1996, 2002)],
            [("Chevrolet", "Cavalier", 1995, 1995),
             ("Pontiac", "Sunfire", 1995, 1995)],
        ],
    },
    "gm-vortec-gen3": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5381 (160A) Tahoe 5.3 2011-2012 — the one unqualified row; every other year splits by case diameter (145 vs 156mm) and is excluded.",
        "groups": [[("Chevrolet", "Tahoe", 2011, 2012)]],
    },
    "ford-escort": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5218 (75A) Escort 1.9 1991-1993; 210-5200 (75A) Escort 1.9 1994-1996; 210-5203 and 210-5314 (95A) both list Escort 2.0 SPI 1998-2003 with identical spans (two published case styles — match yours); 210-5201 (75A) ZX2 2.0 Zetec 1997-2002, all unqualified.",
        "groups": [
            [("Ford", "Escort", 1991, 1993)],
            [("Ford", "Escort", 1994, 1996)],
            [("Ford", "Escort", 1998, 2003)],
            [("Ford", "Escort ZX2", 1998, 2002)],
        ],
    },
    "ford-40ohv": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5210 (95A) Explorer 4.0 OHV 1991-1992 — unqualified (93-94 rows split by Limited trim, 95-98 by door keypad).",
        "groups": [[("Ford", "Explorer", 1991, 1992)]],
    },
    "toyota-rav4-1": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0186 (80A) RAV4 2.0 3S-FE 1996-1997; 210-0436 (80A) RAV4 2.0 3S-FE 1998-2000 — both unqualified (01-03 1AZ-FE rows split by transmission).",
        "groups": [
            [("Toyota", "RAV4", 1996, 1997)],
            [("Toyota", "RAV4", 1998, 2000)],
        ],
    },
    "subaru-legacy25": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified unless noted: 210-3142 (70A) Legacy 2.2 1990-1994; 210-3144 (85A) Legacy 2.2 AND 2.5 1996-1999; 210-4140 (90A) Legacy 2.5 2000 and 2002-2004 plus Outback 2.5 2002-2003 (2001 rows are M/T-qualified); 210-4216 (110A) Legacy/Outback 2.5 2006-2009 — one row covers EJ253 AND the EJ255 GT turbo; 210-4309 (110A) Legacy/Outback 2.5 2010-2011 (incl. 2.5GT); 210-4203 (110A) Legacy/Outback 2.5 FB25 2013-2014.",
        "groups": [
            [("Subaru", "Legacy", 1990, 1994)],
            [("Subaru", "Legacy", 1996, 1999)],
            [("Subaru", "Legacy", 2000, 2000),
             ("Subaru", "Legacy", 2002, 2004),
             ("Subaru", "Outback", 2002, 2003)],
            [("Subaru", "Legacy", 2006, 2009), ("Subaru", "Outback", 2006, 2009)],
            [("Subaru", "Legacy", 2010, 2011), ("Subaru", "Outback", 2010, 2011)],
            [("Subaru", "Legacy", 2013, 2014), ("Subaru", "Outback", 2013, 2014)],
        ],
    },
    "gm-lumina31": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Lumina 3.1 rows all unqualified: 210-5106 (100A) 1990-1994; 210-5109 (105A) 1995-1997; 210-5114 (105A) 1998-1999; 210-5160 (102A) 2000; 210-5161 (102A) 2001. Monte Carlo spans not separately verified — left at likely.",
        "groups": [
            [("Chevrolet", "Lumina", 1990, 1994)],
            [("Chevrolet", "Lumina", 1995, 1997)],
            [("Chevrolet", "Lumina", 1998, 1999)],
            [("Chevrolet", "Lumina", 2000, 2000)],
            [("Chevrolet", "Lumina", 2001, 2001)],
        ],
    },
    "isuzu-6vd1": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-3145 (90A) Rodeo 3.2 1999-2001; 210-3140 (60A) Rodeo 3.2 1997 — both unqualified (1996 rows carry a plug-position qualifier). Passport/Trooper spans not separately verified — left at likely.",
        "groups": [
            [("Isuzu", "Rodeo", 1999, 2001)],
            [("Isuzu", "Rodeo", 1997, 1997)],
        ],
    },
    "lexus-1uz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0170 (100A) LS 400 1990-1992; 210-0282 (100A) 1993-1994; 210-0174 (80A) 1995-1997; 210-0176 (100A) 1999-2000 (1998 splits by production date).",
        "groups": [
            [("Lexus", "LS 400", 1990, 1992)],
            [("Lexus", "LS 400", 1993, 1994)],
            [("Lexus", "LS 400", 1995, 1997)],
            [("Lexus", "LS 400", 1999, 2000)],
        ],
    },
    "lexus-3uz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0508 (130A) LS 430 2001-2004; 210-0570 (130A) LS 430 2005-2006 — both unqualified.",
        "groups": [
            [("Lexus", "LS 430", 2001, 2004)],
            [("Lexus", "LS 430", 2005, 2006)],
        ],
    },
    "saturn-s19": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5100 (96A) published for SL/SL1/SL2/SC/SC1/SC2 1.9 1991-1996 — one unit across every S-Series nameplate, SOHC and DOHC, unqualified (1997 rows carry an external-fan qualifier).",
        "groups": [[("Saturn", "S-Series", 1991, 1996)]],
    },
    "hyundai-genesis38": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Genesis sedan 3.8 rows all unqualified: 210-0715 (150A) 2009-2011 and 2013; 210-0827 (200A) 2012; 210-0717 (180A) 2014-2015 (shared with the V8s).",
        "groups": [
            [("Hyundai", "Genesis", 2009, 2011)],
            [("Hyundai", "Genesis", 2013, 2013)],
            [("Hyundai", "Genesis", 2012, 2012)],
            [("Hyundai", "Genesis", 2014, 2015)],
        ],
    },
    "hyundai-gencoupe20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 211-6017 (110A) Genesis Coupe 2.0T 2010-2012; 210-0713 (130A) Genesis Coupe 2.0T 2013-2014 — both unqualified.",
        "groups": [
            [("Hyundai", "Genesis Coupe", 2010, 2012)],
            [("Hyundai", "Genesis Coupe", 2013, 2014)],
        ],
    },
    "hyundai-gencoupe38": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0713 (130A) Genesis Coupe 3.8 2010-2015 — one published unit, unqualified (2012 is also dual-listed with 211-6017 — match yours).",
        "groups": [[("Hyundai", "Genesis Coupe", 2010, 2015)]],
    },
    "acura-rdx": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0788 (110A) RDX 2.3 K23A1 2007-2012 — one published unit, unqualified.",
        "groups": [[("Acura", "RDX", 2007, 2012)]],
    },
    "lexus-is2": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0657 (150A) IS 250 2006-2009 AND IS 350 2006-2009 — one published unit for both engines, unqualified (the 2010-2013 rows carry a Base-trim qualifier — excluded).",
        "groups": [
            [("Lexus", "IS 250", 2006, 2009), ("Lexus", "IS 350", 2006, 2009)],
        ],
    },
    "mopar-lh27": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0686 (120A) Intrepid 2.7 1999-2001 — one published unit, unqualified (the 3.2/3.5 use their own units; 02-04 rows split Std/Opt). Concorde/300M spans not separately verified — left at likely.",
        "groups": [[("Dodge", "Intrepid", 1999, 2001)]],
    },
    "hyundai-santafe2": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 211-6030 (110A) Santa Fe 2.4 2010-2012 — one published unit (the same number as the Sonata/Optima Theta-II GDI), unqualified.",
        "groups": [[("Hyundai", "Santa Fe", 2010, 2012)]],
    },
    "ford-tc": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4304 (150A) Transit Connect 2.0 2010 and 2012-2013 unqualified (the 2011 row carries a Mitsubishi-unit qualifier — excluded).",
        "groups": [
            [("Ford", "Transit Connect", 2010, 2010),
             ("Ford", "Transit Connect", 2012, 2013)],
        ],
    },
    "mopar-srt4": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Neon 2.4 turbo rows unqualified: 210-0559 (130A) 2004-2005; 210-0558 (145A) 2003 (that number also covers the 2003 2.0 — the one year both engines share a unit).",
        "groups": [
            [("Dodge", "Neon Srt-4", 2004, 2005)],
            [("Dodge", "Neon Srt-4", 2003, 2003)],
        ],
    },
    "mitsu-4g94": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4165 (85A) Lancer 2.0 2002 — clean row (03-04 rows carry a non-turbo qualifier because the Evo arrived in 2003); 210-4271 (105A) Lancer 2.0 4G94 2007 — clean row (the Evo IX ended in 2006).",
        "groups": [
            [("Mitsubishi", "Lancer", 2002, 2002)],
            [("Mitsubishi", "Lancer", 2007, 2007)],
        ],
    },
    "acura-rl": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 210-0204 (110A) RL 3.5 C35A1 1996-2004; 210-0580 (130A) RL 3.5 J35A8 2005-2008; 210-0750 (130A) RL 3.7 J37A2 2009-2012.",
        "groups": [
            [("Acura", "RL", 1996, 2004)],
            [("Acura", "RL", 2005, 2008)],
            [("Acura", "RL", 2009, 2012)],
        ],
    },
    "ford-freestar": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-5361 (135A) Freestar 3.9 2004-2006 AND 4.2 2004-2006 — one published unit for both engines, unqualified.",
        "groups": [[("Ford", "Freestar", 2004, 2006)]],
    },
    "lincoln-ls39": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-0532 (150A) LS 3.9 2003-2006; 210-5344 (110A) LS 3.9 2000-2002 — both unqualified (the V6 3.0's rows split by transmission and sit outside this 3.9 family).",
        "groups": [
            [("Lincoln", "LS", 2003, 2006)],
            [("Lincoln", "LS", 2000, 2002)],
        ],
    },
    "mazda-mpv30": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4180 (110A) MPV 3.0 2002-2005; 210-4105 (70A) MPV 3.0 1989-1998 — both unqualified.",
        "groups": [
            [("Mazda", "MPV", 2002, 2005)],
            [("Mazda", "MPV", 1989, 1998)],
        ],
    },
    "mazda-protege": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 210-4163 (80A) Protege 2.0 2001-2003 and Protege5 2.0 2002-2003 — span capped to 02-03 because the 1.6 (its own unit) was still sold in 2001; 210-4200 (70A) Protege 1.5 and 1.8 1997-1998 — one unit for both engines (the 99-01 1.8 rows aren't published, so those years are excluded).",
        "groups": [
            [("Mazda", "Protege", 2002, 2003), ("Mazda", "Protege5", 2002, 2003)],
            [("Mazda", "Protege", 1997, 1998)],
        ],
    },
}

for _fid, _v in _ALT_VERIFIED.items():
    ENGINE_FAMILIES[_fid]["parts"]["alternator"]["verified"] = _v
del _fid, _v


# --- Verified starter application groups -----------------------------------
# Same contract as _ALT_VERIFIED, for the starter category. Added 2026-10
# (Phase A): several platforms publish clean starter spans where every
# alternator row is turbo-, vendor- or OEM-number-qualified (Z32 300ZX, BMW
# M54, VW 2.0T, LT1 F-bodies) — those families are starter-verified and their
# alternators honestly stay at Likely.
_STR_VERIFIED: dict = {
    "toyota-4a": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0305 Prizm 1.6/1.8 1994-1997 unqualified (the matching Corolla rows those years are Cold-Spec-qualified and excluded); 280-0304 Prizm 1.6/1.8 1993; 280-0100 Corolla 1.6/1.8 1997 unqualified.",
        "groups": [
            [("Geo|Chevrolet", "Prizm", 1994, 1997)],
            [("Geo|Chevrolet", "Prizm", 1993, 1993)],
            [("Toyota", "Corolla", 1997, 1997)],
        ],
    },
    "toyota-m6": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0107 in one published set — Supra 3.0 1986-1990 and Cressida 2.8/3.0 1983-1990 (clipped to this family's 1985 start; the 81-82 rows are option-qualified); 280-0121 Supra 3.0 1991-1992 and Cressida 3.0 1991-1992.",
        "groups": [
            [("Toyota", "Supra", 1986, 1990), ("Toyota", "Cressida", 1985, 1990)],
            [("Toyota", "Supra", 1991, 1992), ("Toyota", "Cressida", 1991, 1992)],
        ],
    },
    "toyota-2jz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows engine-coded 2JZGE/unqualified: 280-0234 GS300 1998-2005 and IS300 2001-2005; 280-0163 Supra 3.0 1993-1998, SC300 1995-2000 and GS300 1993-1997 — one published starter across the NA and twin-turbo Supra alike.",
        "groups": [
            [("Lexus", "GS300", 1998, 2005), ("Lexus", "IS300", 2001, 2005)],
            [("Toyota", "Supra", 1993, 1998), ("Lexus", "SC300", 1995, 2000),
             ("Lexus", "GS300", 1993, 1997)],
        ],
    },
    "honda-b18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0194 Integra 1.8 1990-1993 and 1.7 1993, unqualified. 94-01 rows split by transmission and are excluded.",
        "groups": [[("Acura", "Integra", 1990, 1993)]],
    },
    "mazda-miata-16": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4160 Miata 1.6 1990-1993 unqualified (the same published list covers the 94-97 1.8 M/T cars, which are transmission-qualified rows).",
        "groups": [
            [("Mazda", "Miata", 1990, 1993), ("Mazda", "MX-5*", 1990, 1993)],
        ],
    },
    "mazda-miata-18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4137 Miata 1.8 1999-2005 unqualified. The 94-97 rows split by transmission and are excluded.",
        "groups": [
            [("Mazda", "Miata", 1999, 2005), ("Mazda", "MX-5*", 1999, 2005)],
        ],
    },
    "mazda-miata-nc": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4334 MX-5 Miata 2.0 2006-2008; 280-4336 MX-5 Miata 2.0 2009-2012, both unqualified.",
        "groups": [
            [("Mazda", "Miata", 2006, 2008), ("Mazda", "MX-5*", 2006, 2008)],
            [("Mazda", "Miata", 2009, 2012), ("Mazda", "MX-5*", 2009, 2012)],
        ],
    },
    "mazda-rx8": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4342 RX-8 2011 (engine codes M, P) unqualified — the 2009-10 rows for the same unit are transmission-qualified and excluded.",
        "groups": [
            [("Mazda", "RX-8", 2011, 2011), ("Mazda", "RX8", 2011, 2011)],
        ],
    },
    "nissan-z32": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4122 300ZX 3.0 1990-1996 unqualified — one published starter for every Z32, NA and twin-turbo (the 1989 Z31 row is vendor-qualified and excluded).",
        "groups": [[("Nissan", "300ZX", 1990, 1996)]],
    },
    "nissan-vq-hr": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3143 370Z 3.7 2010-2011 and G37 3.7 2011, unqualified (350Z/G35 HR starter rows are build-date- or trim-qualified and excluded).",
        "groups": [
            [("Nissan", "370Z", 2010, 2011), ("Infiniti", "G37", 2011, 2011)],
        ],
    },
    "nissan-ka24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4109 240SX 2.4 1991-1996 unqualified (the 89-90 rows are vendor-split and excluded); 280-4175 Xterra and Frontier KA24DE 2002-2004 unqualified; 280-4100 Xterra and Frontier KA24DE 2000-2001 unqualified (98-99 Frontier splits 2WD vs 4WD).",
        "groups": [[("Nissan", "240SX", 1991, 1996)],
                   [("Nissan", "Xterra", 2002, 2004),
                    ("Nissan", "Frontier", 2002, 2004)],
                   [("Nissan", "Xterra", 2000, 2001),
                    ("Nissan", "Frontier", 2000, 2001)]],
    },
    "nissan-vq35de": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3133 350Z VQ35DE 2003-2006 unqualified (the 2007 HR rows are build-date-qualified; G35 rows are drivetrain-qualified and excluded); 280-4222 Pathfinder 3.5 2001-2004 unqualified; 280-4237 Maxima 3.5 2007-2008 unqualified (02-06 Maxima splits M/T vs A/T).",
        "groups": [[("Nissan", "350Z", 2003, 2006)],
                   [("Nissan", "Pathfinder", 2001, 2004)],
                   [("Nissan", "Maxima", 2007, 2008)]],
    },
    "bmw-m52": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5355 M3 3.2 1996-1999 and every Z3 1996-2002 (1.9/2.5/2.8/3.0/3.2 rows all carry the one number), unqualified; 280-5346 M3 3.0 1995.",
        "groups": [
            [("BMW", "M3", 1996, 1999), ("BMW", "Z3", 1996, 2002)],
            [("BMW", "M3", 1995, 1995)],
        ],
    },
    "bmw-m54": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5371 X5 3.0 2001-2006 unqualified — the one clean published M54 starter span (3-Series starter rows aren't published in this edition).",
        "groups": [[("BMW", "X5", 2001, 2006)]],
    },
    "vw-20t": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5338 GTI 2.0 2006-2009, Jetta 2.0 2006-2008 and Passat 2.0T 2007-2009 in one published set, unqualified (the 2010 Passat row carries a Bosch-unit qualifier and 07-10 Passats are also dual-listed with 281-6001 — match yours); 281-6001 (First Time Fit) GTI 2.0 2010-2011 unqualified. Later Jetta rows split by fuel, body and transmission and are excluded.",
        "groups": [
            [("Volkswagen", "GTI", 2006, 2009),
             ("Volkswagen", "Jetta", 2006, 2008),
             ("Volkswagen", "Passat", 2007, 2009)],
            [("Volkswagen", "GTI", 2010, 2011)],
        ],
    },
    "gm-fbody-tpi": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0299 Corvette 5.7 1988-1989 unqualified (the 90-95 rows exclude the ZR1 and the 96 row anchors the LT1 family). F-body starter rows split 5.0 vs 5.7 within the same years — excluded to avoid cross-displacement claims.",
        "groups": [[("Chevrolet", "Corvette", 1988, 1989)]],
    },
    "gm-fbody-lt1": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5109 Camaro 5.7 (P) 1995-1997 and Firebird 5.7 1995-1997, unqualified; 280-5160 Camaro and Firebird 5.7 1987-1994 (the LT1 years 93-94 of that span sit in this family); 280-0299 Corvette 5.7 1996 (the 90-95 rows are 'Exc. ZR1' and excluded).",
        "groups": [
            [("Chevrolet", "Camaro", 1995, 1997),
             ("Pontiac", "Firebird", 1995, 1997)],
            [("Chevrolet", "Camaro", 1987, 1994),
             ("Pontiac", "Firebird", 1987, 1994)],
            [("Chevrolet", "Corvette", 1996, 1996)],
        ],
    },
    "gm-ls1-car": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5112 in one published set — Camaro 5.7 1998-2001, Firebird 5.7 1998-2001 and Corvette 5.7 1997-2001, unqualified.",
        "groups": [
            [("Chevrolet", "Camaro", 1998, 2001),
             ("Pontiac", "Firebird", 1998, 2001),
             ("Chevrolet", "Corvette", 1997, 2001)],
        ],
    },
    "gm-corvette-c6": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5391 Corvette 6.0 2006-2007, 6.2 2008-2013 and 7.0 2006-2013, unqualified — one published starter for the whole C6 including the ZR1; 280-4331 Camaro 6.2 2012 and 2015 (the 10-11 rows are vendor-qualified and excluded).",
        "groups": [
            [("Chevrolet", "Corvette", 2006, 2013)],
            [("Chevrolet", "Camaro", 2012, 2012),
             ("Chevrolet", "Camaro", 2015, 2015)],
        ],
    },
    "gm-3800": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5100 Camaro 3.8 (K) 1995-1997 and Firebird 3.8 1995-1997, unqualified.",
        "groups": [
            [("Chevrolet", "Camaro", 1995, 1997),
             ("Pontiac", "Firebird", 1995, 1997)],
        ],
    },
    # ================= 2026-10 PHASE B — high-volume commuters =============
    "nissan-qg18": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5373 Sentra 1.8 2003-2005 unqualified (three CID spellings, one number); 280-3138 Sentra 1.8 QG18DE 2006; 280-3137 Sentra 1.8 2000-2001.",
        "groups": [
            [("Nissan", "Sentra", 2003, 2005)],
            [("Nissan", "Sentra", 2006, 2006)],
            [("Nissan", "Sentra", 2000, 2001)],
        ],
    },
    "nissan-vg30-maxima": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3106 Maxima 3.0 1989-1991 unqualified (92-94 rows split SOHC/DOHC and M/T vs A/T).",
        "groups": [[("Nissan", "Maxima", 1989, 1991)]],
    },
    "nissan-vq30": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-3126 — ONE published starter for Maxima 3.0 1995-2001 and I30 1996-2001, unqualified.",
        "groups": [
            [("Nissan", "Maxima", 1995, 2001), ("Infiniti", "I30", 1996, 2001)],
        ],
    },
    "nissan-vg33": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4135 Pathfinder 3.3 1996-2000 unqualified; 280-4136 Xterra 3.3 2000-2004 and Frontier 3.3 1999-2004 (incl. VG33ER), unqualified.",
        "groups": [
            [("Nissan", "Pathfinder", 1996, 2000)],
            [("Nissan", "Xterra", 2000, 2004), ("Nissan", "Frontier", 1999, 2004)],
        ],
    },
    "nissan-vq40": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4302 — one published starter for Pathfinder 4.0 2005-2011, Xterra 4.0 2005-2011 and 2015, Frontier 4.0 2005-2011 and 2015 (12-14 rows are not in this edition).",
        "groups": [
            [("Nissan", "Pathfinder", 2005, 2011),
             ("Nissan", "Xterra", 2005, 2011),
             ("Nissan", "Frontier", 2005, 2011)],
        ],
    },
    "nissan-qr25": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4282 Frontier 2.5 QR25DE 2005-2011 unqualified (Altima/Sentra QR25 starters split M/T vs A/T and stay Likely).",
        "groups": [[("Nissan", "Frontier", 2005, 2011)]],
    },
    "honda-b20": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0185 CR-V 2.0 1997 unqualified (98-01 rows split M/T vs A/T).",
        "groups": [[("Honda", "CR-V", 1997, 1997)]],
    },
    "honda-k24a": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6005 CR-V 2.4 K24A1 2002-2006 unqualified; 280-6007 CR-V 2.4 2007-2009 and Accord 2.4 K24A8 2006-2007, one published set, unqualified.",
        "groups": [
            [("Honda", "CR-V", 2002, 2006)],
            [("Honda", "CR-V", 2007, 2009), ("Honda", "Accord", 2006, 2007)],
        ],
    },
    "honda-k24z": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6010 CR-V 2.4 K24Z6 2010-2011 unqualified (Accord 08-12 rows split by region/transmission).",
        "groups": [[("Honda", "CR-V", 2010, 2011)]],
    },
    "honda-j30": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 Accord 3.0 J30A1 1998-2002 unqualified (03-07 rows split by transmission/trim; the hybrid uses 280-4333).",
        "groups": [[("Honda", "Accord", 1998, 2002)]],
    },
    "honda-l15": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0412 Fit 1.5 2010-2013 unqualified; 280-0368 Fit 1.5 2007-2008 unqualified. 2009 was dual-sourced between the two — groups capped either side; match your part number in 2009.",
        "groups": [
            [("Honda", "Fit", 2010, 2013)],
            [("Honda", "Fit", 2007, 2008)],
        ],
    },
    "gm-ecotec-lcv": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0434 Malibu 2013 2.0 turbo and 2.5, one published unit, unqualified.",
        "groups": [[("Chevrolet", "Malibu", 2013, 2013)]],
    },
    "gm-atlas-i45": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5394 Colorado 2.9 and 3.7 2008-2012; Canyon 3.7 2008-2012 and 2.9 2009-2012 (the Canyon span starts at 2009 because the 2008 2.9 row is not published).",
        "groups": [
            [("Chevrolet", "Colorado", 2008, 2012), ("GMC", "Canyon", 2009, 2012)],
        ],
    },
    "hyundai-santafe1": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 Santa Fe — 2.7 2001-2006, 3.5 2003-2006 and 2.4 2005-2006 in one published set. The verified span is capped to 2005-2006, the years where ALL family engines carry this number (2.4 02-04 splits M/T vs A/T).",
        "groups": [[("Hyundai", "Santa Fe", 2005, 2006)]],
    },
    "toyota-1nz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0401 Yaris 1.5 2013-2015 unqualified; 280-0395 Yaris 1.5 2012 unqualified (07-11 rows split M/T vs A/T).",
        "groups": [
            [("Toyota", "Yaris", 2013, 2015)],
            [("Toyota", "Yaris", 2012, 2012)],
        ],
    },
    "kia-forte1": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6017 Forte Koup 2.0 2014-2015 and 1.6 2014, one published unit, unqualified (sedan 14-15 rows carry start/stop-feature qualifiers; 10-11 rows split by build date).",
        "groups": [[("Kia", "Forte Koup", 2014, 2015)]],
    },
    "mazda-cx7": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4230 CX-7 2.3 turbo 2007-2009 unqualified; 280-4323 CX-7 2011 (2.3 and 2.5), unqualified.",
        "groups": [
            [("Mazda", "CX-7", 2007, 2009), ("Mazda", "CX7", 2007, 2009)],
            [("Mazda", "CX-7", 2011, 2011), ("Mazda", "CX7", 2011, 2011)],
        ],
    },
    "mazda-cx9": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4326 CX-9 3.5 2007 and 3.7 2008-2009; 280-4329 CX-9 3.7 2010-2012, both unqualified.",
        "groups": [
            [("Mazda", "CX-9", 2007, 2009), ("Mazda", "CX9", 2007, 2009)],
            [("Mazda", "CX-9", 2010, 2012), ("Mazda", "CX9", 2010, 2012)],
        ],
    },
    "mopar-pacifica": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0349 Pacifica 3.5 2005-2006 and 3.8 2005 — the verified span is 2005 only, the year both engines carry the one number (2006 3.8 moved to 280-0360; 2004 splits by build date).",
        "groups": [[("Chrysler", "Pacifica*", 2005, 2005)]],
    },
    "ford-mod-sd": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5315 — one published gas starter for F-250 Super Duty 5.4 and V10 6.8 1999-2008 AND Navigator 5.4 1999-2014 (2009 splits by build date on the SD); 280-5312 — one published starter for E-150 4.6 and 5.4 1997-2012 and Econoline Super Duty 5.4/V10 1997-1999.",
        "groups": [
            [("Ford", "F-250*", 1999, 2008), ("Ford", "F250*", 1999, 2008),
             ("Lincoln", "Navigator*", 1999, 2014),
             ("Ford", "Navigator*", 1999, 2014)],
            [("Ford", "E-150*", 1997, 2012), ("Ford", "E150*", 1997, 2012),
             ("Ford", "Econoline*", 1997, 1999)],
        ],
    },
    "vw-b5-v6": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5364 — one published starter for Passat 2.8 2000-2005, A4 2.8 2000-2001, A4 3.0 2002-2005, A4 Quattro 2.8 2000-2001 and 3.0 2003-2006 (A4 Quattro 2002 is not published — spans split around it).",
        "groups": [
            [("Volkswagen", "Passat*", 2000, 2005),
             ("Audi", "A4", 2000, 2005),
             ("Audi", "A4 Quattro", 2000, 2001),
             ("Audi", "A4 Quattro", 2003, 2006)],
        ],
    },
    "vw-b5-18t": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6111 Passat 1.8 AWM 2002-2004, A4 1.8 2004 and A4 Quattro 1.8 2004 (2005 rows split by chassis number).",
        "groups": [
            [("Volkswagen", "Passat*", 2002, 2004),
             ("Audi", "A4", 2004, 2004),
             ("Audi", "A4 Quattro", 2004, 2004)],
        ],
    },
    "gm-aveo": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5397 Aveo 1.6 2004-2008 and Aveo5 2007-2008; 280-5377 Aveo and Aveo5 1.6 2010-2011 (2009 rows absent from this edition).",
        "groups": [
            [("Chevrolet", "Aveo", 2004, 2008), ("Chevrolet", "Aveo5", 2007, 2008)],
            [("Chevrolet", "Aveo", 2010, 2011), ("Chevrolet", "Aveo5", 2010, 2011)],
        ],
    },
    "kia-sedona1": {
        "evidence": "Denso reman + First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 Sedona 3.5 2002-2005 unqualified; 280-5379 Sedona 3.8 2006-2007; 280-5375 Sedona 3.8 2008-2010 and 3.5 2011-2012, one number (a second number, 281-6009, was dual-sourced over 08-12 — match yours).",
        "groups": [
            [("Kia", "Sedona", 2002, 2005)],
            [("Kia", "Sedona", 2006, 2007)],
            [("Kia", "Sedona", 2008, 2012)],
        ],
    },
    "kia-sorento1": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6002 Sorento 3.5 2003-2006 — one published unit, unqualified.",
        "groups": [[("Kia", "Sorento", 2003, 2006)]],
    },
    "hk-mu-lambda": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5001 Sorento 3.8 2007-2009 and 3.3 2008-2009, unqualified (280-5376 was dual-sourced on 08-09 — match yours).",
        "groups": [[("Kia", "Sorento", 2007, 2009)]],
    },
    "ford-focus3": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4241 Focus 2.0 2012-2014 — the 13-14 rows list both 2.0 VIN engine codes (GDI and EcoBoost ST) on the one number, unqualified.",
        "groups": [[("Ford", "Focus", 2012, 2014)]],
    },
    "mopar-world24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4273 in one published set — Caliber 2.0/2.4 2007-2011, Compass 2.0/2.4 2008-2011 and 2015, Patriot 2.0/2.4 2008-2011 and 2015, Sebring 2.4 2007-2010, Avenger 2.4 2008-2010, Journey 2.4 2009-2010 and 2015, all unqualified (the gap years carry build-date splits — excluded).",
        "groups": [
            [("Dodge", "Caliber", 2007, 2011),
             ("Jeep", "Compass", 2008, 2011),
             ("Jeep", "Compass", 2015, 2015),
             ("Jeep", "Patriot", 2008, 2011),
             ("Jeep", "Patriot", 2015, 2015),
             ("Chrysler", "Sebring", 2007, 2010),
             ("Dodge", "Avenger", 2008, 2010),
             ("Dodge", "Journey", 2009, 2010),
             ("Dodge", "Journey", 2015, 2015)],
        ],
    },
    "mopar-pentastar": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0438 Avenger 3.6 2011-2014 and Journey 3.6 2011-2014 — the rows carry a 'FLEX Fuel' tag, but every 3.6 Pentastar in these models is flex-fuel, so it doesn't discriminate.",
        "groups": [
            [("Dodge", "Avenger", 2011, 2014), ("Dodge", "Journey", 2011, 2014)],
        ],
    },
    "ford-cyclone": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4266 MKZ 3.5 2007-2010; 280-4235 MKZ 3.5 2011-2012 — each one published unit, unqualified. Ford-badged rows in this catalog split by transmission/option — excluded.",
        "groups": [
            [("Lincoln", "MKZ", 2007, 2010)],
            [("Lincoln", "MKZ", 2011, 2012)],
        ],
    },
    "gm-hv-v6": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5390 Impala 3.5/3.9 2006-2011; 280-5386 Malibu 3.5/3.9 2007-2010 and Aura 3.5 2007-2008 — each one published unit, unqualified (the 2006 Malibu 3.5 row is absent, so it stays outside the span).",
        "groups": [
            [("Chevrolet", "Impala", 2006, 2011)],
            [("Chevrolet", "Malibu", 2007, 2010), ("Saturn", "Aura", 2007, 2008)],
        ],
    },
    "gm-ecotec24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5396 Malibu 2.4 2008-2012, Verano 2.4 2012-2015 and Aura 2.4 2007-2009 — one published unit, unqualified.",
        "groups": [
            [("Chevrolet", "Malibu", 2008, 2012), ("Buick", "Verano", 2012, 2015),
             ("Saturn", "Aura", 2007, 2009)],
        ],
    },
    "gm-14t": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4209 Cruze 1.4 2011-2014 — one published unit, unqualified.",
        "groups": [[("Chevrolet", "Cruze", 2011, 2014)]],
    },
    "hk-delta27": {
        "evidence": "Denso First Time Fit catalog (densoautoparts.com, retrieved 2026-10-22): 281-6004 in one published set — Tucson 2.7 2005-2009, Tiburon 2.7 2003-2008, Sportage 2.7 2005-2009, Sonata 2.7 2002-2005, Optima 2.7 2002-2006, Santa Fe 2.7 2001-2006, all unqualified.",
        "groups": [
            [("Hyundai", "Tucson", 2005, 2009),
             ("Hyundai", "Tiburon", 2003, 2008),
             ("Kia", "Sportage", 2005, 2009),
             ("Hyundai", "Sonata", 2002, 2005),
             ("Kia", "Optima", 2002, 2006),
             ("Hyundai", "Santa Fe", 2001, 2006)],
        ],
    },
    "hk-theta24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5372 Sonata 2.4 2006-2008 — one published unit, unqualified (Optima rows carry trans qualifiers — excluded).",
        "groups": [[("Hyundai", "Sonata", 2006, 2008)]],
    },
    "mitsu-24": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4213 Galant 2.4 2005-2009 and Lancer 2.4 2005-2006 (both 4G69), unqualified — the 2004 Galant row carries a From-09/2003 build-date qualifier, so 2004 stays outside the span.",
        "groups": [[("Mitsubishi", "Galant", 2005, 2009),
                    ("Mitsubishi", "Lancer", 2005, 2006)]],
    },
    "mitsu-6g75": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4212 Galant 3.8 2004-2009 — one published unit, unqualified.",
        "groups": [[("Mitsubishi", "Galant", 2004, 2009)]],
    },
    "mitsu-6g72": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4165 Galant 3.0 1999-2003 and Sebring 3.0 coupe 2001-2005 — one published unit, unqualified.",
        "groups": [
            [("Mitsubishi", "Galant", 1999, 2003),
             ("Chrysler", "Sebring", 2001, 2005)],
        ],
    },
    "honda-j35-early": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 MDX 3.5 2001-2002; 280-4207 MDX 3.5 2003-2006 — each one published unit, unqualified.",
        "groups": [
            [("Acura", "MDX", 2001, 2002)],
            [("Acura", "MDX", 2003, 2006)],
        ],
    },
    "honda-j37": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0404 MDX 3.7 2007-2009; 280-0405 MDX 3.7 2010-2013 — each one published unit, unqualified.",
        "groups": [
            [("Acura", "MDX", 2007, 2009)],
            [("Acura", "MDX", 2010, 2013)],
        ],
    },
    "acura-tl": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6000 TL 3.2 1999-2003 — one published row, unqualified (covers Type S too); 280-0403 TL 3.5 2009-2011 and 3.7 2009 — the 2009 model year has both engines on the one number. 04-08 and 10-14 rows split by transmission — excluded.",
        "groups": [
            [("Acura", "TL", 1999, 2003)],
            [("Acura", "TL", 2009, 2009)],
        ],
    },
    "mopar-neon": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Dodge rows unqualified: 280-5370 Neon 2.0 2000-2002; 280-6109 1998-1999; 280-5349 1996-1997 (the 1995 year is dual-listed with 280-6108 — excluded).",
        "groups": [
            [("Dodge", "Neon", 2000, 2002)],
            [("Dodge", "Neon", 1998, 1999)],
            [("Dodge", "Neon", 1996, 1997)],
        ],
    },
    "gm-jbody22": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5378 Cavalier 2.2 2003-2005 and Sunfire 2.2 2003-2005 (the 2002 rows carry a DOHC/Ecotec qualifier — excluded); 280-5167 Cavalier 2.2 1996-1997 and Sunfire 2.2 1996-1997 (the 1998 rows carry a thru-bolt qualifier — excluded).",
        "groups": [
            [("Chevrolet", "Cavalier", 2003, 2005),
             ("Pontiac", "Sunfire", 2003, 2005)],
            [("Chevrolet", "Cavalier", 1996, 1997),
             ("Pontiac", "Sunfire", 1996, 1997)],
        ],
    },
    "gm-vortec57": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5101 Tahoe 5.7 1995-1996 and 1999-2000, Suburban (C/K 1500-2500) 5.7 1995-1996 and 1999-2000 — one published unit across both spans, unqualified; 280-5164 both models 1997 (the 1998 rows carry a thru-bolt qualifier — excluded).",
        "groups": [
            [("Chevrolet", "Tahoe", 1995, 1996),
             ("Chevrolet", "Suburban", 1995, 1996),
             ("Chevrolet", "Tahoe", 1999, 2000),
             ("Chevrolet", "Suburban", 1999, 1999)],
            [("Chevrolet", "Tahoe", 1997, 1997),
             ("Chevrolet", "Suburban", 1997, 1997)],
        ],
    },
    "gm-vortec-gen3": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5383 Tahoe 4.8/5.3 2003-2008 and Suburban 4.8/5.3 2003-2008 — one published unit for both engines, unqualified; 280-5398 Tahoe 5.3 2009-2014 (and the lone 2009 4.8) — unqualified.",
        "groups": [
            [("Chevrolet", "Tahoe", 2003, 2008),
             ("Chevrolet", "Suburban", 2003, 2008)],
            [("Chevrolet", "Tahoe", 2009, 2014)],
        ],
    },
    "mitsu-4b11": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4317 Lancer 2.0 2010 — the one year where both the naturally-aspirated row and the Evolution GSR turbo row carry the same number (the Evo MR's dual-clutch starter isn't published; other years split by turbo or build date).",
        "groups": [[("Mitsubishi", "Lancer", 2010, 2010)]],
    },
    "acura-rl": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), all rows unqualified: 280-4197 RL 3.5 1996-2004; 280-4328 RL 3.5 2005-2008; 280-0403 RL 3.7 2009-2010 (2011-12 is dual-listed with 280-0423/281-6001 — excluded).",
        "groups": [
            [("Acura", "RL", 1996, 2004)],
            [("Acura", "RL", 2005, 2008)],
            [("Acura", "RL", 2009, 2010)],
        ],
    },
    "ford-freestar": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5314 Freestar 3.9 2004-2007 AND 4.2 2004-2007 — one published unit for both engines, unqualified.",
        "groups": [[("Ford", "Freestar", 2004, 2007)]],
    },
    "lincoln-ls39": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5317 LS 3.9 2000-2006 — ONE published starter for every 3.9 LS, unqualified.",
        "groups": [[("Lincoln", "LS", 2000, 2006)]],
    },
    "mazda-mpv30": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4192 MPV 3.0 2002-2006; 280-4116 MPV 3.0 1992-1995 — both unqualified (96-98 rows split Std/Opt — excluded).",
        "groups": [
            [("Mazda", "MPV", 2002, 2006)],
            [("Mazda", "MPV", 1992, 1995)],
        ],
    },
    "mopar-minivan-ohv": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22), Grand Caravan rows unqualified for both the 3.3 and 3.8: 280-0360 2006-2010; 280-0349 2004-2005; 280-0321 2001-2003 (the 2003 FLEX Fuel/GAS tags don't discriminate — both carry the same number). Caravan/Town & Country spans not separately verified — left at likely.",
        "groups": [
            [("Dodge", "Grand Caravan", 2006, 2010)],
            [("Dodge", "Grand Caravan", 2004, 2005)],
            [("Dodge", "Grand Caravan", 2001, 2003)],
        ],
    },
    "lexus-1uz": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0164 LS 400 1990-1994; 280-0165 LS 400 1995-2000 — both unqualified.",
        "groups": [
            [("Lexus", "LS 400", 1990, 1994)],
            [("Lexus", "LS 400", 1995, 2000)],
        ],
    },
    "saturn-s19": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 281-6000 SL 1.9 1998-1999 — unqualified.",
        "groups": [[("Saturn", "S-Series", 1998, 1999)]],
    },
    "hyundai-genesis38": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5380 Genesis sedan 3.8 2009 (the 4.6 carries the same number) — unqualified.",
        "groups": [[("Hyundai", "Genesis", 2009, 2009)]],
    },
    "toyota-2az": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0174 RAV4 2.4 2004-2005; 280-0345 RAV4 2.4 2006-2008 (the 3.5 V6 carries the same number) — both unqualified.",
        "groups": [
            [("Toyota", "RAV4", 2004, 2005)],
            [("Toyota", "RAV4", 2006, 2008)],
        ],
    },
    "acura-rdx": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-6018 RDX 2.3 2007-2009; 280-6019 RDX 2.3 2010-2012 — both unqualified.",
        "groups": [
            [("Acura", "RDX", 2007, 2009)],
            [("Acura", "RDX", 2010, 2012)],
        ],
    },
    "acura-rdx35": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0440 RDX 3.5 J35Z2 2013-2015 — one published unit, unqualified.",
        "groups": [[("Acura", "RDX", 2013, 2015)]],
    },
    "lexus-is2": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-0366 IS 250 2.5 2006-2011 — one published unit, unqualified.",
        "groups": [[("Lexus", "IS 250", 2006, 2011)]],
    },
    "mopar-srt4": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-4278 Neon 2.4 2004-2005 unqualified (no 2003 2.4 starter row is published in this edition).",
        "groups": [[("Dodge", "Neon Srt-4", 2004, 2005)]],
    },
    "mercury-marauder": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5105 AND 280-5312 are both listed for the Marauder 4.6 2003-2004 with no qualifiers — two published case styles, match yours.",
        "groups": [[("Mercury", "Marauder", 2003, 2004)]],
    },
    "vw-r32-32": {
        "evidence": "Denso reman catalog (densoautoparts.com, retrieved 2026-10-22): 280-5338 R32 3.2 2008 unqualified, dual-listed with 281-6001 (First Time Fit, CBRA engine code) — two published case styles, match yours.",
        "groups": [[("Volkswagen", "R32", 2008, 2008)]],
    },
}

for _fid, _v in _STR_VERIFIED.items():
    ENGINE_FAMILIES[_fid]["parts"]["starter"]["verified"] = _v
del _fid, _v


def _lint_engine_families() -> list[str]:
    problems: list[str] = []
    for fam_id, fam in ENGINE_FAMILIES.items():
        if not fam.get("display"):
            problems.append(f"{fam_id}: missing display")
        spec = fam.get("engine") or {}
        liters = spec.get("liters") or []
        if not liters or not all(isinstance(x, float) and 0.5 <= x <= 8.5 for x in liters):
            problems.append(f"{fam_id}: bad liters {liters!r}")
        if spec.get("cyl") not in (2, 3, 4, 5, 6, 8, 10):  # 2 = rotary rotors (13B)
            problems.append(f"{fam_id}: bad cyl {spec.get('cyl')!r}")
        apps = fam.get("apps") or []
        if not apps:
            problems.append(f"{fam_id}: no apps")
        for app in apps:
            if len(app) not in (4, 5) or not app[0] or not app[1]:
                problems.append(f"{fam_id}: malformed app {app!r}")
                continue
            if not (1950 <= app[2] <= app[3] <= 2027):
                problems.append(f"{fam_id}: bad years in app {app!r}")
            flags = _app_flags(app)
            if flags.get("sole") and flags.get("ambig"):
                problems.append(
                    f"{fam_id}: app {app[:2]} can't be both sole and ambig")
        parts = fam.get("parts") or {}
        if not parts:
            problems.append(f"{fam_id}: no parts")
        for cat, p in parts.items():
            pc = INTERCHANGE_PART_CATEGORIES.get(cat)
            if not pc or pc["kind"] != "engine":
                problems.append(f"{fam_id}: {cat!r} is not an engine part category")
            if "tier" in p:
                problems.append(
                    f"{fam_id}: {cat} carries a 'tier' — tiers are computed "
                    "from verified groups now, never declared")
            if not p.get("note"):
                problems.append(f"{fam_id}: {cat} missing honesty note")
            yrs = p.get("years")
            if yrs is not None and not (
                    len(yrs) == 2 and 1950 <= yrs[0] <= yrs[1] <= 2027):
                problems.append(f"{fam_id}: {cat} bad part window {yrs!r}")
            ver = p.get("verified")
            if ver is not None:
                if len(ver.get("evidence", "")) < 20:
                    problems.append(
                        f"{fam_id}: {cat} verified groups without a real "
                        "evidence citation")
                groups = ver.get("groups") or []
                if not groups:
                    problems.append(f"{fam_id}: {cat} verified with no groups")
                for g in groups:
                    if not g:
                        problems.append(f"{fam_id}: {cat} empty verified group")
                    for span in g:
                        if (len(span) != 4 or not span[0] or not span[1]
                                or not (1950 <= span[2] <= span[3] <= 2027)):
                            problems.append(
                                f"{fam_id}: {cat} bad verified span {span!r}")
    return problems


def interchange_tier(fam: dict, cat: str, seeker: tuple, donor: tuple) -> str | None:
    """'verified' when seeker (year, make, model) and donor (year, make,
    model) both sit inside one of the part's verified-group application
    lists; 'likely' when both merely match the family's apps; None when
    either car isn't a family application at all. Callers still apply the
    engine-confirmation and ambig downgrades on top — this is fitment only."""
    p = fam["parts"].get(cat)
    if p is None:
        return None
    yrs = p.get("years")
    for who in (seeker, donor):
        if yrs is not None and not (yrs[0] <= who[0] <= yrs[1]):
            return None
        if not any(_app_matches(a, *who) for a in fam["apps"]):
            return None
    ver = p.get("verified")
    if ver:
        for g in ver["groups"]:
            if (any(_app_matches((s[0], s[1], s[2], s[3]), *seeker) for s in g)
                    and any(_app_matches((s[0], s[1], s[2], s[3]), *donor) for s in g)):
                return "verified"
    return "likely"


_engine_family_problems = _lint_engine_families()
if _engine_family_problems:
    raise ValueError(
        "ENGINE_FAMILIES lint failed:\n  " + "\n  ".join(_engine_family_problems))


# Platform-family keys whose UNOBTANIUM_DB key doesn't directly name the
# feed's (make, model): resolved here for the part-first export. Model may
# use the trailing-* prefix convention.
_PLATFORM_KEY_EXPORT: dict[str, tuple[str, str]] = {
    "chrysler 300": ("Chrysler", "300*"),
    "lexus es": ("Lexus", "ES*"),
    "rx": ("Lexus", "RX*"),
    "bmw 1": ("BMW", "1 Series*"),
    "bmw 3": ("BMW", "3 Series*"),
    "audi a4": ("Audi", "A4"),
    "audi a5": ("Audi", "A5"),
    "audi q5": ("Audi", "Q5"),
    "acura tl": ("Acura", "TL"),
    "toyota pickup": ("Toyota", "Pickup"),
    "c/k": ("Chevrolet", "C/K*"),
    "k1500": ("Chevrolet", "K1500*"),
}


def _platform_member_app(key: str) -> tuple[str, str] | None:
    """(make, model_pattern) for an UNOBTANIUM_DB member key, or None when
    the key can't be resolved to a feed model."""
    if key in _PLATFORM_KEY_EXPORT:
        return _PLATFORM_KEY_EXPORT[key]
    info = UNOBTANIUM_DB.get(key)
    if not info or not info.get("make"):
        return None
    model = re.sub(r"\s+\d{4}-\d{4}$", "", key).strip()
    return (info["make"], model)


def _category_for_part_name(name: str) -> str | None:
    nl = name.lower()
    for cat, pc in INTERCHANGE_PART_CATEGORIES.items():
        if pc["kind"] == "body" and any(t in nl for t in pc["tokens"]):
            return cat
    return None


def build_interchange_payload() -> dict:
    """The part-first search table shipped to the app as
    docs/data/interchange.json. Pure curated data — no scan required."""
    cats = [
        {"id": cid, "label": pc["label"], "kind": pc["kind"],
         "tokens": pc["tokens"], "priceTokens": pc["priceTokens"]}
        for cid, pc in INTERCHANGE_PART_CATEGORIES.items()
    ]
    fams = []
    for fam_id, fam in ENGINE_FAMILIES.items():
        fams.append({
            "id": fam_id,
            "label": fam["display"],
            "liters": fam["engine"]["liters"],
            "cyl": fam["engine"]["cyl"],
            "apps": [
                [a[0], a[1], a[2], a[3],
                 1 if _app_flags(a).get("sole") else 0,
                 _app_flags(a).get("ambig", "")]
                for a in fam["apps"]
            ],
            "parts": {
                cat: {"note": p["note"],
                      **({"years": list(p["years"])} if p.get("years") else {}),
                      # vg: verified groups — each a published part-number
                      # application list; seeker+donor inside one = verified.
                      **({"vg": [[list(s) for s in g]
                                 for g in p["verified"]["groups"]]}
                         if p.get("verified") else {})}
                for cat, p in fam["parts"].items()
            },
        })
    groups = []
    for fam_id, fam in PLATFORM_FAMILIES.items():
        for gi, grp in enumerate(fam["shared"]):
            if grp.get("donor"):
                continue  # one-way swap provenance: donors aren't enumerable
            cat = _category_for_part_name(grp["part"])
            if cat is None:
                continue  # no part-first category for this group
            apps = []
            for k, (lo, hi) in grp["members"].items():
                resolved = _platform_member_app(k)
                if resolved is None:
                    apps = []
                    break
                apps.append([resolved[0], resolved[1], lo, hi])
            if not apps:
                continue
            groups.append({
                "id": f"{fam_id}#{gi}",
                "label": fam["display"],
                "cat": cat,
                "tier": "verified",   # two-way groups are hand-verified (see research notes)
                "note": grp.get("note", ""),
                "apps": apps,
            })
    # Performance-trim platform groups: reasoned body-part platform claims
    # (NOT published part-number lists), shipped at tier "likely" so the UI
    # stays honest. See TRIM_PLATFORM_GROUPS curation notes.
    trim_engine_notes = []
    for tid, t in TRIM_PLATFORM_GROUPS.items():
        all_apps = [list(a) for a in
                    list(t["trim_apps"]) + list(t["platform_apps"])]
        for cid, note in t["cats"].items():
            groups.append({
                "id": f"{tid}#{cid}",
                "label": t["display"],
                "cat": cid,
                "tier": "likely",
                "note": note,
                "apps": all_apps,
            })
        if t.get("engine_note"):
            trim_engine_notes.append({
                "note": t["engine_note"],
                "apps": [list(a) for a in t["trim_apps"]],
            })
    return {
        "schemaVersion": 1,
        "builtAt": _iso_utc_z_interchange(),
        "categories": cats,
        "engineFamilies": fams,
        "platformGroups": groups,
        "trimEngineNotes": trim_engine_notes,
    }


def _iso_utc_z_interchange() -> str:
    # Local copy: _iso_utc_z is defined later in the file (module ordering).
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_interchange_payload() -> None:
    out = DATA_DIR / "interchange.json"
    out.write_text(json.dumps(build_interchange_payload(),
                              separators=(",", ":")) + "\n")
    print(f"  [interchange] wrote {out}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Sell-channel guide — where each part actually moves and how fast.
# Keyed by lowercase substring found in part name.  Checked longest-match-first.
# "sell_at" = best channel(s), "speed" = Fast/Medium/Slow,
# "notes" = colour for the UI / helpful context.
# ---------------------------------------------------------------------------
SELL_GUIDE = [
    # --- Toyota off-road (huge community → forums/local classifieds) ---
    {"kw": "e-locker actuator",        "sell_at": "T4R.org / local classifieds",       "speed": "Fast",   "notes": "Huge 3rd-gen community, sells in days"},
    {"kw": "trd pro grille",           "sell_at": "T4R.org / local classifieds",       "speed": "Fast",   "notes": "Very sought-after, post w/ photos"},
    {"kw": "kdss sway bar",            "sell_at": "eBay / T4R.org",      "speed": "Medium", "notes": "Niche but high-value, national market"},
    {"kw": "roof rack crossbars",      "sell_at": "FB Marketplace / local classifieds","speed": "Fast",   "notes": "Local pickup saves $70+ shipping"},
    {"kw": "roof rack",                "sell_at": "FB Marketplace / local classifieds","speed": "Fast",   "notes": "Local pickup saves shipping"},
    {"kw": "roof rails",               "sell_at": "FB Marketplace / local classifieds","speed": "Medium", "notes": "Local pickup preferred"},
    {"kw": "transfer case shift",      "sell_at": "eBay",                "speed": "Medium", "notes": "National market, $90-200 real sold"},
    {"kw": "center console lid",       "sell_at": "T4R.org / local classifieds",       "speed": "Medium", "notes": "Condition is everything—must be uncracked"},
    {"kw": "heated side mirror",       "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "Pair sells better than singles"},
    {"kw": "ahc height control",       "sell_at": "eBay / IH8MUD",       "speed": "Medium", "notes": "Land Cruiser forums pay premium"},
    {"kw": "factory locker",           "sell_at": "eBay / IH8MUD",       "speed": "Medium", "notes": "LC community is global"},
    {"kw": "uncracked dash",           "sell_at": "IH8MUD / eBay",       "speed": "Fast",   "notes": "Every LC owner needs this, instant sell"},
    # --- FJ Cruiser ---
    {"kw": "swing-out tire",           "sell_at": "FJ forums / local classifieds",     "speed": "Fast",   "notes": "FJ community almost as strong as 4Runner"},
    # --- Wrangler ---
    {"kw": "hardtop",                  "sell_at": "FB Marketplace / local classifieds","speed": "Fast",   "notes": "Wrangler hardtops often sell same-day locally"},
    {"kw": "half doors",               "sell_at": "FB Marketplace / local classifieds","speed": "Fast",   "notes": "Huge Jeep community, summer demand"},
    {"kw": "rubicon locker",           "sell_at": "JeepForum / local classifieds",     "speed": "Medium", "notes": "Jeep forums pay fair prices"},
    # --- XJ Cherokee ---
    {"kw": "xj header panel",          "sell_at": "FB XJ groups / local classifieds","speed": "Fast",   "notes": "XJ parts are gold, rust-free = premium"},
    {"kw": "clean fenders",            "sell_at": "FB XJ groups / local classifieds","speed": "Fast",   "notes": "Rust-free fenders are rare nationally"},
    # --- Minivan sliding doors (national eBay play) ---
    {"kw": "power sliding door motor", "sell_at": "eBay",                "speed": "Fast",   "notes": "Common failure item, high-volume $65-80 real"},
    {"kw": "sliding door control",     "sell_at": "eBay",                "speed": "Medium", "notes": "Steady demand, $100-165 real sold"},
    {"kw": "sliding door cable",       "sell_at": "eBay",                "speed": "Medium", "notes": "Often sold with motor as a kit"},
    {"kw": "stow-n-go",               "sell_at": "eBay / FB Marketplace","speed": "Slow",   "notes": "Heavy = expensive shipping. Pair >$400 local"},
    {"kw": "magic seats",             "sell_at": "eBay / FB Marketplace","speed": "Slow",   "notes": "Heavy, local is better for margins"},
    # --- Seats (performance) ---
    {"kw": "recaro seat",              "sell_at": "eBay / Enthusiast FB","speed": "Medium", "notes": "Wide audience, ship or sell local"},
    {"kw": "sti/recaro",               "sell_at": "eBay / NASIOC",       "speed": "Medium", "notes": "Subaru forums pay well"},
    {"kw": "si/type r seat",           "sell_at": "eBay / CivicX",       "speed": "Medium", "notes": "Honda community is huge"},
    # --- Brake calipers ---
    {"kw": "brembo caliper",           "sell_at": "eBay",                "speed": "Medium", "notes": "National market, well-known upgrade"},
    {"kw": "brake caliper",            "sell_at": "eBay",                "speed": "Medium", "notes": "Performance calipers sell nationally"},
    # --- LED Headlights (universal eBay) ---
    {"kw": "led headlight",            "sell_at": "eBay",                "speed": "Medium", "notes": "Always in demand, verify not hazed/cracked"},
    {"kw": "hid headlight",            "sell_at": "eBay",                "speed": "Medium", "notes": "HID assemblies sell well complete"},
    {"kw": "headlights (clear",        "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "Only if truly clear, not yellowed"},
    {"kw": "headlight",                "sell_at": "eBay",                "speed": "Medium", "notes": "Check condition carefully"},
    # --- Touchscreens / Infotainment ---
    {"kw": "uconnect touchscreen",     "sell_at": "eBay",                "speed": "Medium", "notes": "Verify it powers on before pulling"},
    {"kw": "sync 3 touchscreen",       "sell_at": "eBay",                "speed": "Medium", "notes": "Ford SYNC 3 in high demand"},
    {"kw": "touchscreen",              "sell_at": "eBay",                "speed": "Medium", "notes": "Test before pulling if possible"},
    {"kw": "infotainment",             "sell_at": "eBay",                "speed": "Medium", "notes": "Test before pulling if possible"},
    {"kw": "head unit",                "sell_at": "eBay",                "speed": "Medium", "notes": "Verify it works"},
    # --- Rear entertainment ---
    {"kw": "rear entertainment",       "sell_at": "eBay / FB Marketplace","speed": "Slow",  "notes": "Niche market, families w/ kids"},
    # --- Commuter evergreens (2026-09 breadth expansion) ---
    {"kw": "tail lights",              "sell_at": "eBay / FB Marketplace", "speed": "Medium", "notes": "Uncracked lenses only — check for moisture"},
    {"kw": "window regulator",         "sell_at": "eBay",                "speed": "Medium", "notes": "Common failure part, steady demand"},
    {"kw": "alternator",               "sell_at": "eBay / FB Marketplace", "speed": "Medium", "notes": "Spin-test at the yard; sell as tested-pull"},
    # --- 2026-10 consensus evergreens (see scraper/consensus_parts_research.md) ---
    {"kw": "starter",                  "sell_at": "eBay / FB Marketplace", "speed": "Medium", "notes": "Dead-battery returns are common — tell buyers how to rule out the battery first"},
    {"kw": "gauge cluster",            "sell_at": "eBay",                "speed": "Medium", "notes": "Disclose the mileage shown; many 2000s+ cars need the cluster programmed to the car"},
    {"kw": "climate control",          "sell_at": "eBay",                "speed": "Medium", "notes": "Quick pull, steady demand — test every button and knob before pulling"},
    {"kw": "master switch",            "sell_at": "eBay",                "speed": "Medium", "notes": "Common spill/wear failure — test every window from the driver seat first"},
    {"kw": "control module",           "sell_at": "eBay",                "speed": "Medium", "notes": "Match the OEM part number exactly; many need programming — say so in the listing"},
    {"kw": "steering wheel (pre-airbag", "sell_at": "eBay / FB Marketplace", "speed": "Medium", "notes": "Wheel only — airbags can't be resold (eBay ban + federal SRS rules)"},
    {"kw": "manual shifter",           "sell_at": "eBay / enthusiast forums", "speed": "Medium", "notes": "Swap crowd buys these steadily"},
    {"kw": "manual pedal",             "sell_at": "eBay / enthusiast forums", "speed": "Medium", "notes": "Auto-to-manual swappers need the whole box"},
    {"kw": "manual locking hubs",      "sell_at": "eBay / forums",       "speed": "Medium", "notes": "Solid-axle crowd pays for clean hubs"},
    {"kw": "shift knob",               "sell_at": "eBay",                "speed": "Medium", "notes": "OEM knobs ship cheap, sell steadily"},
    {"kw": "liftgate glass",           "sell_at": "local classifieds",   "speed": "Medium", "notes": "Glass = local pickup only"},
    {"kw": "dash pad",                 "sell_at": "eBay / forums",       "speed": "Medium", "notes": "Uncracked pads are scarce for older trucks"},
    # --- 2026-09 generation-split additions ---
    {"kw": "t-top",                    "sell_at": "FB Marketplace / local classifieds", "speed": "Medium", "notes": "Glass — local pickup; check for delamination"},
    {"kw": "convertible top motor",    "sell_at": "eBay",                "speed": "Medium", "notes": "Common failure on Solara/convertibles, test if possible"},
    {"kw": "magic seat",               "sell_at": "eBay / FB Marketplace", "speed": "Slow",  "notes": "Heavy — local pickup preferred"},
    {"kw": "x-reas",                   "sell_at": "eBay / T4R.org",      "speed": "Medium", "notes": "Sport-package owners replace failed units in pairs"},
    # --- Tow mirrors ---
    {"kw": "tow mirror",               "sell_at": "eBay / local classifieds",          "speed": "Fast",   "notes": "Truck owners always need these"},
    {"kw": "power-fold tow",           "sell_at": "eBay / local classifieds",          "speed": "Fast",   "notes": "Power-fold command premium"},
    # --- Tailgates ---
    {"kw": "tailgate",                 "sell_at": "FB Marketplace / local classifieds","speed": "Medium", "notes": "Local preferred—heavy to ship"},
    {"kw": "multipro tailgate",        "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "GM MultiPro in demand"},
    # --- Hybrid parts ---
    {"kw": "dc-dc converter",          "sell_at": "eBay",                "speed": "Medium", "notes": "Prius owners DIY, good eBay market"},
    {"kw": "hybrid inverter",          "sell_at": "eBay",                "speed": "Medium", "notes": "Verify part number before listing"},
    {"kw": "hybrid battery cell",      "sell_at": "eBay",                "speed": "Fast",   "notes": "Sell in bulk sets, always in demand"},
    # --- Air suspension ---
    {"kw": "air suspension",           "sell_at": "eBay",                "speed": "Medium", "notes": "Common failure, steady demand"},
    {"kw": "autoride",                 "sell_at": "eBay",                "speed": "Medium", "notes": "GM AutoRide always failing"},
    # --- 3rd row seats ---
    {"kw": "3rd row seat",             "sell_at": "FB Marketplace / local classifieds","speed": "Slow",   "notes": "Heavy, sell local to avoid shipping"},
    # --- Skid plates ---
    {"kw": "skid plate",               "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "Off-road crowd, local is easier"},
    # --- Wings / spoilers ---
    {"kw": "wing",                     "sell_at": "eBay / Enthusiast FB","speed": "Medium", "notes": "STI wing is iconic, easy to ship"},
    {"kw": "spoiler",                  "sell_at": "eBay",                "speed": "Slow",   "notes": "Niche, make sure no cracks"},
    # --- Intercoolers ---
    {"kw": "intercooler",              "sell_at": "eBay / Forums",       "speed": "Medium", "notes": "Performance crowd, verify no damage"},
    # --- Audio ---
    {"kw": "mark levinson",            "sell_at": "eBay",                "speed": "Medium", "notes": "Premium OEM audio — strong eBay market"},
    {"kw": "jbl speaker",              "sell_at": "eBay",                "speed": "Medium", "notes": "Sell as complete set for max value"},
    {"kw": "bose",                     "sell_at": "eBay",                "speed": "Medium", "notes": "Sell amp+speakers together"},
    {"kw": "infinity amp",             "sell_at": "eBay",                "speed": "Medium", "notes": "Sell amp+speakers together"},
    {"kw": "sony audio",               "sell_at": "eBay",                "speed": "Medium", "notes": "Ford Sony systems in demand"},
    {"kw": "amp + speaker",            "sell_at": "eBay",                "speed": "Medium", "notes": "Complete sets sell best"},
    # --- Eyesight cameras ---
    {"kw": "eyesight camera",          "sell_at": "eBay",                "speed": "Fast",   "notes": "Subaru Eyesight repairs are expensive at dealer"},
    # --- Running boards ---
    {"kw": "running board",            "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "Power retractable = premium"},
    # --- Smart cruise / radar ---
    {"kw": "smart cruise",             "sell_at": "eBay",                "speed": "Medium", "notes": "Part of ADAS system, verify P/N"},
    {"kw": "radar module",             "sell_at": "eBay",                "speed": "Medium", "notes": "Part of ADAS system, verify P/N"},
    # --- Catch-all ---
    {"kw": "mirror",                   "sell_at": "eBay / local classifieds",          "speed": "Medium", "notes": "Heated/power mirrors sell best"},
    {"kw": "seat",                     "sell_at": "eBay / FB Marketplace","speed": "Medium", "notes": "Heavy—local pickup preferred"},
    {"kw": "fog light",                "sell_at": "eBay",                "speed": "Slow",   "notes": "Low margin, bundle with other parts"},
    {"kw": "steering wheel",           "sell_at": "eBay",                "speed": "Medium", "notes": "Leather w/ controls = higher value"},
    {"kw": "charging pad",             "sell_at": "eBay",                "speed": "Slow",   "notes": "Low value, only if already pulling other stuff"},
    {"kw": "sunroof",                  "sell_at": "eBay",                "speed": "Slow",   "notes": "Fragile to ship, local preferred"},
    {"kw": "liftgate",                 "sell_at": "eBay",                "speed": "Medium", "notes": "Power liftgate motors fail often"},
    {"kw": "fender",                   "sell_at": "FB Marketplace / local classifieds","speed": "Medium", "notes": "Body panels sell local, no shipping"},
    {"kw": "bumper",                   "sell_at": "FB Marketplace / local classifieds","speed": "Medium", "notes": "Local pickup, heavy to ship"},
]

# Sort SELL_GUIDE by keyword length descending for longest-match-first
SELL_GUIDE.sort(key=lambda x: len(x["kw"]), reverse=True)


def _lookup_sell_info(part_name: str, vehicle_make: str | None = None) -> dict:
    """Find the best sell-channel match for a part name.

    Some keywords (e.g. Mark Levinson) appear on multiple makes; notes must not
    imply the donor car is Lexus when it is not.
    """
    lower = part_name.lower()
    for entry in SELL_GUIDE:
        if entry["kw"] in lower:
            notes = entry["notes"]
            make = (vehicle_make or "").strip().lower()
            if entry["kw"] == "mark levinson" and make == "lexus":
                notes = "Lexus audio buyers pay well on eBay"
            # "hardtop" matches far more than Wranglers (Miata, SLK, Z4,
            # Bronco, K5, Samurai...) — only Jeeps get the Jeep-flavored note.
            if entry["kw"] == "hardtop" and make != "jeep":
                notes = "Removable hardtops are in strong local demand — often sell same-day in summer"
            return {"sell_at": entry["sell_at"], "sell_speed": entry["speed"], "sell_notes": notes}
    return {"sell_at": "eBay / FB Marketplace", "sell_speed": "Medium", "sell_notes": ""}


def _round_price_band(lo: int, hi: int) -> tuple[int, int]:
    """Keep bands in sane integers; enforce low <= high."""
    lo = max(10, int(round(lo / 5) * 5))
    hi = max(lo + 5, int(round(hi / 5) * 5))
    hi = min(hi, 50000)
    return lo, hi


def _resale_sold_calibrate(low: int, high: int, part_name: str, year: int) -> tuple[int, int]:
    """Map DB anchor low/high toward typical US used eBay *sold* OEM-ish resale.

    Category rules (first match wins; tuned for yard pulls, not showroom).
    Set JUNKYARD_RAW_PRICES=1 to disable.
    """
    if os.environ.get("JUNKYARD_RAW_PRICES", "").strip() in ("1", "true", "yes"):
        return low, high
    if high < low or low < 0:
        low, high = max(0, low), max(low, high)
    n = part_name.lower()
    # (low_scale, high_scale) — highs carry most retail inflation vs sold
    ls, hs = 0.90, 0.78

    if any(k in n for k in ("headlight", "headlamp", "fog lamp", "fog light")):
        ls, hs = 0.88, 0.68
    elif any(k in n for k in (
        "touchscreen", "idrive", "mmi", "navigation", "cockpit", "cluster",
        "virtual cockpit", "digital display", "uconnect", "mib", "entune", "sync",
        "head unit", "radio", "screen",
    )):
        # "screen" can be broad; headlight already matched first
        ls, hs = 0.90, 0.74
    elif any(k in n for k in (
        "mark levinson", "bang & olufsen", "b&o", "bose", "harman", "infinity",
        "amp", "speaker", "audio", "sony audio", "bowers", "fender audio",
        "dynaudio", "beats",
    )):
        ls, hs = 0.90, 0.78
    elif any(k in n for k in ("brake", "caliper", "ceramic")):
        ls, hs = 0.88, 0.76
    elif any(k in n for k in ("seat", "recaro", "bench", "bucket seat")):
        ls, hs = 0.88, 0.76
    elif any(k in n for k in ("bumper", "hood", "spoiler", "fender", "grille", "molding")):
        ls, hs = 0.88, 0.78
    elif any(k in n for k in ("suspension", "compressor", "shock", "strut", "air suspension")):
        ls, hs = 0.86, 0.72
    elif any(k in n for k in ("differential", "transfer case", "xdrive", "quattro", "haldex")):
        ls, hs = 0.85, 0.74
    elif any(k in n for k in ("wheel", "rim", "tire")):
        ls, hs = 0.88, 0.74
    elif "mirror" in n:
        ls, hs = 0.90, 0.78
    elif any(k in n for k in ("turbo", "intercooler", "supercharger")):
        ls, hs = 0.85, 0.74
    elif any(k in n for k in ("door panel", "tailgate", "liftgate", "hatch", "convertible", "soft top", "hardtop")):
        ls, hs = 0.87, 0.76
    elif any(k in n for k in ("steering", "column", "rack")):
        ls, hs = 0.88, 0.76
    elif ("on-board" in n or "onboard" in n) and "charger" in n:
        ls, hs = 0.88, 0.75

    nl = low * ls
    nh = high * hs
    # Newer matrix/laser headlights hold a bit more; older halogen/xenon comps lower
    if "headlight" in n or "headlamp" in n:
        if year >= 2020:
            nh *= 1.05
        if year <= 2010:
            nh *= 0.94
            nl *= 0.96

    return _round_price_band(nl, nh)


def _max_entry_calibrated_high(info: dict) -> int:
    """Largest calibrated *high* for a vehicle entry (for sorting list-parts)."""
    lo, hi = info["year_range"]
    ymid = (lo + hi) // 2
    return max(_resale_sold_calibrate(p["low"], p["high"], p["name"], ymid)[1] for p in info["top_parts"])


def _vehicle_carry_profit(v: dict) -> float:
    """Estimated haul profit using part bands vs default yard cost (same idea as the web UI profit tab)."""
    parts = v.get("_top_parts") or []
    if not parts:
        return 0.0
    total = 0.0
    for p in parts:
        lo, hi = float(p.get("low", 0)), float(p.get("high", 0))
        cost = float(p.get("cost", 0) or 0)
        total += (lo + hi) / 2.0 - cost
    return total


def _normalize_vin(vin: str) -> str:
    """Return 17-char VIN or empty if invalid."""
    v = re.sub(r"[^A-Za-z0-9]", "", (vin or "")).strip().upper()
    if len(v) != 17:
        return ""
    # VIN alphabet excludes I, O, Q
    if any(c not in "0123456789ABCDEFGHJKLMNPRSTUVWXYZ" for c in v):
        return ""
    return v


def _vpic_trim_quality(trim: str) -> str:
    """NHTSA sometimes returns one trim (usable) or a comma-separated list of all trims (ambiguous)."""
    t = (trim or "").strip()
    if not t:
        return "empty"
    parts = [p.strip() for p in t.split(",") if p.strip()]
    if len(parts) > 2 or len(t) > 80:
        return "ambiguous"
    return "usable"


def fetch_vpic_decode(vin: str) -> dict | None:
    """Decode VIN via NHTSA decodevinvaluesextended; cached per process. Returns None on failure."""
    vin = _normalize_vin(vin)
    if not vin:
        return None
    if vin in _VPIC_CACHE:
        return _VPIC_CACHE[vin]
    url = VPIC_DECODEVIN_EXTENDED.format(vin=vin) + "?format=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = data.get("Results") or []
        if not results:
            _VPIC_CACHE[vin] = None
            return None
        row = results[0]
    except Exception:
        _VPIC_CACHE[vin] = None
        return None
    dec = _vpic_row_to_decode(row)
    _VPIC_CACHE[vin] = dec
    if _VPIC_DELAY_SEC > 0:
        time.sleep(_VPIC_DELAY_SEC)
    return dec


def _vpic_row_to_decode(row: dict) -> dict:
    trim = (row.get("Trim") or "").strip()
    # Compact engine/transmission summaries (e.g. "3.7L 6-cyl", "6-spd Automatic").
    # Only present on decodes made after this shipped; older cache entries
    # backfill naturally as inventory turns over (~45-day lot lifespans).
    eng_bits = []
    disp = (row.get("DisplacementL") or "").strip()
    if disp:
        try:
            eng_bits.append(f"{float(disp):.1f}L")
        except ValueError:
            pass
    cyl = (row.get("EngineCylinders") or "").strip()
    if cyl:
        eng_bits.append(f"{cyl}-cyl")
    fuel = (row.get("FuelTypePrimary") or "").strip()
    if fuel and fuel.lower() != "gasoline":
        eng_bits.append(fuel)
    tstyle = (row.get("TransmissionStyle") or "").strip()
    tspeed = (row.get("TransmissionSpeeds") or "").strip()
    trans = ((f"{tspeed}-spd " if tspeed else "") + tstyle).strip()
    return {
        "trim": trim,
        "series": (row.get("Series") or "").strip(),
        "driveType": (row.get("DriveType") or "").strip(),
        "trimQuality": _vpic_trim_quality(trim),
        "bodyClass": (row.get("BodyClass") or "").strip(),
        "engine": " ".join(eng_bits),
        "transmission": trans,
        # Factory identity per the VIN — used to cross-check the yard listing.
        "modelYear": (row.get("ModelYear") or "").strip(),
        "make": (row.get("Make") or "").strip(),
        "model": (row.get("Model") or "").strip(),
    }


def _decode_vpic_batch(vins: list[str]) -> None:
    """Decode via vPIC's DecodeVINValuesBatch POST (50 VINs per call) into
    _VPIC_CACHE. ~50x fewer HTTP requests than per-VIN GETs — the per-VIN
    flood gets throttled hard on CI runner IPs (observed 98% failures), while
    batch calls are the API's intended bulk path. VINs in failed batches stay
    uncached, so a later run retries them."""
    errors: dict[str, int] = {}
    ok_batches = 0
    for i in range(0, len(vins), VPIC_BATCH_SIZE):
        chunk = vins[i:i + VPIC_BATCH_SIZE]
        try:
            r = requests.post(
                VPIC_BATCH_URL,
                data={"format": "json", "data": ";".join(chunk)},
                headers=HEADERS,
                timeout=60,
            )
            r.raise_for_status()
            results = r.json().get("Results") or []
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", "")
            key = f"{type(e).__name__} {status}".strip()
            errors[key] = errors.get(key, 0) + 1
            time.sleep(2.0)
            continue
        for row in results:
            rvin = _normalize_vin(row.get("VIN") or "")
            if rvin:
                _VPIC_CACHE[rvin] = _vpic_row_to_decode(row)
        ok_batches += 1
        time.sleep(0.3)
    if errors:
        print(f"  VPIC batch: {ok_batches} batches OK, errors: {errors}", file=sys.stderr)


def _decode_vpic_unique_parallel(unique_vins: list[str]) -> list[dict | None]:
    """Decode each VIN once in parallel; results populate _VPIC_CACHE for the per-vehicle pass."""
    if not unique_vins:
        return []
    workers = min(_VPIC_WORKERS, max(1, len(unique_vins)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fetch_vpic_decode, unique_vins))


# Keyword-match regexes, compiled once per keyword. A keyword hits only when it
# starts at a word boundary: "rx" still matches "RX350" / "RX 350" but no longer
# fires inside "WRX", and "blazer" no longer fires inside "TrailBlazer".
_KW_RE: dict[str, re.Pattern] = {}


def _kw_pattern(kw: str) -> re.Pattern:
    pat = _KW_RE.get(kw)
    if pat is None:
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(kw))
        _KW_RE[kw] = pat
    return pat


# Generic tokens that would false-hint an option part from a listing title
# (e.g. "manual" in "F-150 5-speed manual" must not confirm manual tow mirrors).
_OPTION_HINT_STOPWORDS = {
    "pair", "power", "fold", "oem", "full", "clean", "front", "rear", "middle",
    "assembly", "complete", "motor", "motors", "glass", "seat", "seats", "parts",
    "manual", "with", "set", "components",
}


def _option_hint_tokens(name: str) -> list[str]:
    """Distinctive words of an option part's name ("tow", "sunroof",
    "hardtop"...) used to spot the rare yard listing that names the option."""
    return [t for t in re.split(r"[^a-z0-9]+", name.lower())
            if len(t) >= 3 and t not in _OPTION_HINT_STOPWORDS]


# "How to spot it" hints for option-gated parts — the VIN can't confirm a
# ticked option box, but almost every option has a physical tell you can see
# from outside the car. Keyword-matched against the part name (longest match
# wins); a DB entry's own "verify" field overrides. Shipped to the UI as the
# "spot it" note on "if equipped" parts.
VERIFY_HINTS = [
    ("tow mirror", "Telescoping heads that pull/fold outward — visibly deeper than standard mirrors; power-fold switch on the driver door panel."),
    ("running board", "Boards tucked up under the rocker panels with a visible motor/linkage — they deploy when a door opens (no power needed to see the hinge arms)."),
    ("air suspension", "Rubber air bladders instead of coil springs at the rear axle; compressor pump mounted near the spare tire well."),
    ("x-reas", "Yellow-bodied shocks with braided crossover lines running diagonally between corners."),
    ("hood w/ scoop", "Just look at the hood — the scoop is molded in, not bolted on."),
    ("scoop", "Visible from the front of the car — factory scoops are molded into the hood panel."),
    ("3rd row", "Look through the rear glass for the extra seat row or its floor anchor points if folded/removed."),
    ("third row", "Look through the rear glass for the extra seat row or its floor anchor points if folded/removed."),
    ("sunroof", "Visible glass panel in the roof — check the headliner switch too."),
    ("rear entertainment", "Screen folded into the headliner or seatbacks; look for headphone jacks in the rear trim."),
    ("subwoofer", "Check the trunk sidewall, under-floor well, or under a front seat for the sub enclosure and amp."),
    ("amp", "Amp is usually mounted in the trunk sidewall, under the rear deck, or under a front seat."),
    ("digital dash", "Look through the windshield — the cluster face shows segmented LCD panels instead of needle gauges."),
    ("hardtop", "Visible — verify all latches/hinge points are present and the glass isn't cracked."),
    ("bed extender", "Folding cage clipped inside the tailgate opening — visible in the bed."),
    ("utili-track", "Metal rails inset along the bed walls/floor with sliding tie-down cleats."),
    ("roof rack", "Crossbars mounted on the roof rails — check that end caps and locks are intact."),
    ("transfer case shift motor", "Only on 4WD units — look for a 4WD badge, floor shift lever, or dash selector switch."),
    # No VIN database records factory lockers (tested: Toyota's own build record
    # lists both locker and non-locker diff carriers for the same VIN — the
    # locker lives in the door-jamb AXLE code, not the VIN). Physical check is
    # the only proof, so these hints carry the whole feature.
    ("e-locker", "The proof is under the truck: an electric actuator motor with a wiring pigtail bolted to the rear diff housing — open diffs are bare metal. Cross-check the RR DIFF LOCK dash switch and the AXLE code on the driver door-jamb sticker. No motor on the diff = no e-locker, whatever the trim says."),
    ("locker", "Crawl to the rear diff: factory lockers have an electric actuator motor (wiring pigtail attached) bolted to the housing — an open diff has none. A diff-lock switch in the cab supports it, but the motor on the axle is the ground truth."),
    ("locker actuator", "Crawl to the rear diff: factory lockers have an electric actuator motor (wiring pigtail attached) bolted to the housing — an open diff has none. A diff-lock switch in the cab supports it, but the motor on the axle is the ground truth."),
    ("locking diff", "Look at the rear diff housing for an electric actuator motor with a wiring pigtail — that motor IS the locker. No motor means an open diff, regardless of badges or switches."),
    ("diff lock", "Dash/console switch labeled DIFF LOCK plus a wired actuator on the diff or transfer case — check both ends of that wire before pulling."),
    ("winch", "Check behind the front bumper cover for the winch drum and fairlead."),
    ("headlight washer", "Small spray nozzle caps in the front bumper below each headlight."),
]


def _verify_hint(name: str) -> str:
    lower = name.lower()
    best = ""
    best_len = 0
    for kw, hint in VERIFY_HINTS:
        if kw in lower and len(kw) > best_len:
            best, best_len = hint, len(kw)
    return best


def match_vehicle(year: int, make: str, model: str, vin_decode: dict | None = None) -> list[dict]:
    """Match a vehicle against the unobtanium database, filtering parts by
    year range and trim requirements.  Attaches sell-channel info to each part.

    Matching rules:
      - An entry's keywords are its dict key, or the "match" list when present
        (generation-split entries share one keyword with disjoint year ranges,
        so a vehicle hits exactly one of them).
      - Keywords must start at a word boundary in "make model" (see _kw_pattern).
      - Entries stored under several alias keys (same dict object) match once.
      - When two entries match and one's keyword is a substring of the other's
        ("cherokee" vs "grand cherokee", "ram" vs "ram 2500"), the less
        specific entry is dropped — it belongs to a different vehicle.
      - Every matched part carries a "fits" year range (entry generation range
        intersected with the part's own year gates) for UI provenance.

    Trim-gated parts carry a "trim_status" honesty flag:
      - "listing":     the yard's own listing title names the trim
      - "vin":         a usable (single-trim) vPIC decode confirms the trim
      - "unconfirmed": trim unknown/ambiguous — part listed as "if equipped"
    When a USABLE decode names a different trim (and series doesn't match
    either), the part is excluded — that's the only case where we're confident
    the car doesn't have it. Ambiguous/empty decodes never gate parts.

    Parts flagged "option": True are factory options whose presence no VIN
    decode or trim can confirm — they land "unconfirmed" even when the trim
    is known, unless the yard listing itself names the part (rare).
    Each match's "max_value" counts CONFIRMED parts only (trim_status of
    None/"vin"/"listing"): an unconfirmed part still ships to the UI as
    "if equipped" but contributes $0, so a base Focus can't outrank real
    finds on Recaro seats it probably doesn't have."""
    model_lower = model.lower()
    make_lower = make.lower()
    matches = []
    vin_usable = bool(vin_decode and vin_decode.get("trimQuality") == "usable")
    vin_tokens = ""
    if vin_decode:
        if vin_usable:
            vin_tokens += " " + (vin_decode.get("trim") or "").strip().lower()
        ser = (vin_decode.get("series") or "").strip().lower()
        if ser:
            vin_tokens += " " + ser
    # Drivetrain and transmission from the VIN decode, for drive-/manual-gated
    # parts. Same honesty trilogy as trim gates: confirmed / excluded only when
    # the decode is definite / "if equipped" otherwise.
    drive_str = (vin_decode.get("driveType") or "").lower() if vin_decode else ""
    trans_str = (vin_decode.get("transmission") or "").lower() if vin_decode else ""
    is_manual = "manual" in trans_str and "automated" not in trans_str
    is_definitely_auto = bool(trans_str) and not is_manual and any(
        t in trans_str for t in ("automatic", "cvt", "dual-clutch", "automated"))
    haystack = f"{make_lower} {model_lower}"
    seen_entries: set[int] = set()
    candidates: list[tuple[str, dict]] = []
    for keyword, info in UNOBTANIUM_DB.items():
        if id(info) in seen_entries:
            continue  # alias key pointing at an entry object we already tested
        keywords = info.get("match") or (keyword,)
        hit = next((k for k in keywords if _kw_pattern(k).search(haystack)), None)
        if hit is None:
            continue
        seen_entries.add(id(info))
        lo, hi = info["year_range"]
        if lo <= year <= hi:
            candidates.append((hit, info))
    # Specificity guard: when "grand cherokee" matched, the plain "cherokee"
    # (XJ) entry is a different vehicle — drop any candidate whose keyword is
    # a proper substring of another candidate's keyword.
    matched_kws = [kw for kw, _ in candidates]
    for keyword, info in candidates:
        if any(keyword != other and keyword in other for other in matched_kws):
            continue
        low, high = info["year_range"]
        filtered_parts = []
        for p in info["top_parts"]:
            if "yr_min" in p and year < p["yr_min"]:
                continue
            if "yr_max" in p and year > p["yr_max"]:
                continue
            trim_status = None
            if "trim" in p:
                trims = [t.lower() for t in p["trim"]]
                if _gate_hit(trims, model_lower):
                    trim_status = "listing"
                elif vin_tokens and _gate_hit(trims, vin_tokens):
                    trim_status = "vin"
                elif vin_usable:
                    # Decode is specific and names a different trim:
                    # confident the car doesn't have this part.
                    continue
                else:
                    trim_status = "unconfirmed"
            if p.get("manual"):
                # Manual-transmission-only part (shifters, pedal boxes...).
                if is_manual:
                    trim_status = "vin"
                elif is_definitely_auto:
                    continue  # decode is definite: automatic, part absent
                elif _gate_hit(("manual", "5-speed"), model_lower):
                    trim_status = "listing"
                else:
                    trim_status = trim_status or "unconfirmed"
            if "drive" in p:
                # Drivetrain-gated part; gate tokens like ["4wd", "awd"].
                DRIVE_SYNONYMS = {
                    "4wd": ("4wd", "4x4", "four-wheel"),
                    "awd": ("awd", "all-wheel"),
                    "rwd": ("rwd", "rear-wheel"),
                    "fwd": ("fwd", "front-wheel"),
                }
                gate_tokens = []
                for g in p["drive"]:
                    gate_tokens += DRIVE_SYNONYMS.get(g.lower(), (g.lower(),))
                if drive_str and _gate_hit(gate_tokens, drive_str):
                    trim_status = "vin"
                elif _gate_hit(gate_tokens, model_lower):
                    trim_status = "listing"
                elif drive_str:
                    # vPIC drive strings are synonym lists for ONE
                    # class ("FWD/Front-Wheel Drive"). Exclude only
                    # when the decode names exactly one class and it
                    # isn't in the gate; a string spanning classes
                    # (e.g. "2WD/4WD") stays unconfirmed.
                    classes = {c for c, toks in DRIVE_SYNONYMS.items()
                               if _gate_hit(toks, drive_str)}
                    if _gate_hit(("2wd",), drive_str):
                        classes.add("2wd")
                    if len(classes) == 1:
                        continue
                    trim_status = trim_status or "unconfirmed"
                else:
                    trim_status = trim_status or "unconfirmed"
            if p.get("option"):
                # Factory-option gate: an option package (or accessory) whose
                # presence can't be determined from year/model/trim — and vPIC
                # never decodes option content. This overrides trim/VIN
                # confirmation: knowing the trim still doesn't tell you the
                # box was ticked. Only the yard's own listing naming the part
                # (rare — e.g. "... w/ tow mirrors") counts as confirmation.
                hinted = any(
                    re.search(rf"\b{re.escape(t)}\b", model_lower)
                    for t in _option_hint_tokens(p["name"])
                )
                trim_status = "listing" if hinted else "unconfirmed"
            cl, ch = _resale_sold_calibrate(p["low"], p["high"], p["name"], year)
            enriched = {**p, "low": cl, "high": ch, **_lookup_sell_info(p["name"], make)}
            # Provenance: the model years this part actually fits — the
            # entry's (generation) year range narrowed by the part's own
            # yr_min/yr_max gates. Shipped to the UI as "fits 1996–2002".
            enriched["fits"] = f"{max(low, p.get('yr_min', low))}–{min(high, p.get('yr_max', high))}"
            if trim_status:
                enriched["trim_status"] = trim_status
            # Interchange provenance is scoped to the family group's year
            # window, which can be narrower than the row's own fit range
            # (e.g. LX Uconnect: row runs 2011+, interchange claim is 11–14).
            # Outside the window the claim doesn't apply — drop it.
            sy = enriched.get("sharedYears")
            if sy is not None:
                enriched.pop("sharedYears", None)
                if not (sy[0] <= year <= sy[1]):
                    enriched.pop("sharedWith", None)
            # "Spot it" hint for unconfirmed option parts: the entry's own
            # verify text wins, else the keyword table's physical tell.
            if trim_status == "unconfirmed" and not enriched.get("verify"):
                hint = _verify_hint(p["name"])
                if hint:
                    enriched["verify"] = hint
            filtered_parts.append(enriched)
        if filtered_parts:
            # Ranking value counts only parts we can stand behind: ungated,
            # VIN-confirmed, or named by the listing. "If equipped" parts
            # still ship to the UI but contribute $0 — a match whose parts
            # are ALL unconfirmed keeps max_value 0 (still "worth a look",
            # it just can't outrank confirmed cars in value sorts).
            confirmed = [p for p in filtered_parts
                         if p.get("trim_status") != "unconfirmed"]
            max_val = max((p["high"] for p in confirmed), default=0)
            matches.append({**info, "top_parts": filtered_parts, "max_value": max_val})
    return matches


def _pnp_ingest_group(loc_data: dict, out: list[dict]) -> None:
    """Enrich and append one search-response location group's vehicles."""
    loc = loc_data.get("location") or {}
    # The API occasionally returns a location stub with null
    # name/city/state — skip those groups rather than emitting a
    # phantom "None" yard; the vehicles come back on the next scan.
    if not loc.get("name"):
        return
    for v in loc_data.get("vehicles", []):
        # NOTE: the feed carries photo URLs, but they are Row52
        # assets (cdn.row52.com, Row52 watermark) — deliberately
        # NOT captured. See PHOTO POLICY at EXTRAS_FILE.
        # Spec fields exist in the schema but are null in every
        # observed response; captured defensively if they appear —
        # facts aren't copyrightable, so these are fine regardless
        # of where the photos live.
        for src, dst in (("color", "_color"), ("engine", "_engine"),
                         ("transmission", "_trans")):
            val = (v.get(src) or "").strip() if isinstance(v.get(src), str) else ""
            if val:
                v[dst] = val
        v["_location"] = loc.get("name")
        v["_city"] = loc.get("city") or ""
        v["_state"] = loc.get("state") or ""
        v["_lat"] = loc.get("mapLatitude")
        v["_lng"] = loc.get("mapLongitude")
        out.append(v)


def fetch_pnp_inventory(make_ids: list[int] | None = None, *, national: bool = False) -> list[dict]:
    """Fetch live inventory from Pick-n-Pull API.

    national=True uses distance=0, which the PnP API treats as unlimited —
    one request per make returns every yard in the US + Canada network.
    CAVEAT: unlimited in radius, NOT in rows — national responses truncate at
    PNP_NATIONAL_CAP rows per make, so any make that comes back at exactly the
    cap is re-swept per yard postal code and unioned by id (see constant)."""
    if make_ids is None:
        makes_resp = requests.get(f"{PNP_API}/vehicle/makes", headers=HEADERS, timeout=15)
        all_makes = makes_resp.json()
        make_ids = [m["id"] for m in all_makes]

    distance = 0 if national else SEARCH_RADIUS
    all_vehicles: list[dict] = []
    capped_make_ids: list[int] = []
    yard_zips: set[str] = set()
    for mid in make_ids:
        try:
            r = requests.get(
                f"{PNP_API}/vehicle/search",
                params={"makeId": mid, "distance": distance, "zip": SLC_ZIP},
                headers=HEADERS,
                timeout=60 if national else 15,
            )
            groups = r.json()
            raw_rows = 0
            for loc_data in groups:
                raw_rows += len(loc_data.get("vehicles") or [])
                loc = loc_data.get("location") or {}
                pc = (loc.get("postalCode") or "").strip()
                if pc:
                    yard_zips.add(pc)
                _pnp_ingest_group(loc_data, all_vehicles)
            if national and raw_rows >= PNP_NATIONAL_CAP:
                capped_make_ids.append(mid)
        except Exception:
            continue

    # Second pass: the national query is not just row-capped (see
    # PNP_NATIONAL_CAP) — its per-yard index also LAGS the per-zip search that
    # picknpull.com itself uses, by DAYS. Diagnosed 2026-10-21: SLC's national
    # slice was byte-identical for 6+ consecutive scans while the yard's site
    # showed fresh arrivals, and 256 Toyotas with set-out dates back to Oct 15
    # were missing nationally even though Toyota (~4.2k rows) never hit the
    # cap — that lag hid a watched Oct-20 4Runner for two days. So ALWAYS
    # re-sweep every yard zip with one make-less query (returns that area's
    # full, fresh inventory — observed 1.1-4.1k rows/zip) and union by id.
    # Guard: if a dense zip's make-less response itself comes back at the cap,
    # fall back to one query per make for that zip.
    if national and capped_make_ids:
        print(f"  [PnP] makeId(s) {capped_make_ids} hit the {PNP_NATIONAL_CAP}-row "
              f"national cap (recovered by the per-zip sweep below)", file=sys.stderr)
    if national and yard_zips:
        seen_ids = {str(v.get("id")) for v in all_vehicles}
        recovered = 0
        capped_zips: list[str] = []

        def _sweep(pc: str, mid: int | None) -> list[dict] | None:
            params: dict = {"distance": PNP_SWEEP_RADIUS, "zip": pc}
            if mid is not None:
                params["makeId"] = mid
            try:
                r = requests.get(f"{PNP_API}/vehicle/search", params=params,
                                 headers=HEADERS, timeout=60)
                groups = r.json()
            except Exception:
                return None
            rows: list[dict] = []
            for loc_data in groups:
                _pnp_ingest_group(loc_data, rows)
            return rows

        def _union(rows: list[dict]) -> int:
            n = 0
            for v in rows:
                vid = str(v.get("id"))
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    all_vehicles.append(v)
                    n += 1
            return n

        for pc in sorted(yard_zips):
            rows = _sweep(pc, None)
            if rows is None:
                continue
            if len(rows) >= PNP_NATIONAL_CAP:
                capped_zips.append(pc)
                continue
            recovered += _union(rows)
        for pc in capped_zips:
            for mid in make_ids:
                recovered += _union(_sweep(pc, mid) or [])
        print(f"  [PnP] per-zip freshness sweep over {len(yard_zips)} zips "
              f"({len(capped_zips)} dense zip(s) re-swept per make) recovered "
              f"{recovered} vehicles the national index was missing", file=sys.stderr)

    return all_vehicles


def _tap_get_nonce() -> str:
    """Get the verification nonce from Tear-A-Part's inventory page.

    The site has used both sif_ajax_nonce (in sif_ajax_object) and sif_verify_request;
    try both so inventory keeps working when they change markup.
    """
    try:
        resp = requests.get("https://tearapart.com/inventory/", headers=HEADERS, timeout=20)
        text = resp.text
        for pattern in (
            r'sif_ajax_nonce["\s:]+["\']([a-f0-9]+)',
            r'sif_verify_request["\s:]+["\']([a-f0-9]+)',
        ):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return "338b8c7d8d"  # stale fallback; TAP will usually return no products


def fetch_tearapart_inventory() -> list[dict]:
    """Fetch live inventory from Tear-A-Part (SLC + Ogden) via their WordPress AJAX API."""
    nonce = _tap_get_nonce()
    all_vehicles = []

    for store in TAP_STORES:
        for make in TAP_MAKES:
            try:
                resp = requests.post(TAP_AJAX, data={
                    "sif_form_field_store": store,
                    "sif_form_field_make": make,
                    "makes-sorting-order": "0",
                    "sif_form_field_model": "Any",
                    "models-sorting-order": "0",
                    "action": "sif_search_products",
                    "sif_verify_request": nonce,
                    "sorting[key]": "iyear",
                    "sorting[state]": "0",
                    "sorting[type]": "int",
                }, headers={
                    **HEADERS,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://tearapart.com/inventory/",
                    "Origin": "https://tearapart.com",
                }, timeout=15)

                data = resp.json()
                if data.get("success") and data.get("products"):
                    for product in data["products"]:
                        vehicle = {
                            "id": product.get("stocknumber", ""),
                            "vin": product.get("vin", ""),
                            "year": int(product.get("iyear", 0)),
                            "make": product.get("make", "").title(),
                            "model": product.get("model", "").title(),
                            "row": product.get("vehicle_row", ""),
                            "dateAdded": product.get("yard_in_date", ""),
                            "_location": f"Tear-A-Part - {store.title()}",
                            "_city": product.get("yard_city", store).title(),
                            "_state": product.get("yard_state", "UT"),
                            "_source": "tearapart",
                        }
                        all_vehicles.append(vehicle)
            except Exception:
                continue

    # Deduplicate by stock number
    seen_ids = set()
    unique = []
    for v in all_vehicles:
        vid = v["id"]
        if vid not in seen_ids:
            seen_ids.add(vid)
            unique.append(v)

    return unique


def _utpap_format_label(s: str) -> str:
    """Title-case make/model from UTPAP; keep short all-caps tokens (TL, MDX, CR-V)."""
    s = (s or "").strip()
    if not s:
        return s
    if s.isupper() and len(s) <= 4:
        return s
    if s.isupper():
        return s.title()
    return s


def _utpap_xml_text(asset: ET.Element, tag: str, default: str = "") -> str:
    el = asset.find(tag)
    if el is None or el.text is None:
        return default
    return el.text.strip()


def _utpap_yard_date_to_iso(s: str) -> str:
    """Parse YARD_DATE from XML like 2026-03-12T09:55:18.323 to ISO date."""
    s = (s or "").strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    return s


def _utpap_is_premium_row(slug: str, row_int: int, reference: str) -> bool:
    """Match utpap.com premium inventory pages (row bands) plus REFERENCE hints."""
    ref = (reference or "").upper()
    if "PREMIUM" in ref:
        return True
    pr = UTPAP_PREMIUM_ROW_RANGE.get(slug)
    if pr and pr[0] <= row_int <= pr[1]:
        return True
    return False


def fetch_utpap_inventory() -> list[dict]:
    """Fetch live inventory from Utah Pic-A-Part (Ogden + Orem).

    Uses published XML feeds (1064 / 1065) — same source as the standard and
    premium inventory tools on utpap.com. Premium-lot rows are labeled in
    _location; VINs are included when present in the feed.
    """
    all_vehicles: list[dict] = []
    session = requests.Session()
    session.headers.update({**HEADERS, "Accept": "application/xml, text/xml, */*"})

    for store in UTPAP_STORES:
        slug = store["slug"]
        xml_name = UTPAP_XML_BY_SLUG.get(slug)
        if not xml_name:
            continue
        url = f"{UTPAP_BASE}/{xml_name}"
        try:
            r = session.get(url, timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Utah Pic-A-Part {store['label']}] failed to load XML: {e}", file=sys.stderr)
            continue

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            print(f"  [Utah Pic-A-Part {store['label']}] XML parse error: {e}", file=sys.stderr)
            continue

        base_loc = f"Utah Pic-A-Part - {store['label']}"
        for asset in root.findall(".//ASSET"):
            stock = _utpap_xml_text(asset, "STOCKNUMBER")
            if not stock:
                continue
            try:
                year = int(_utpap_xml_text(asset, "iYEAR", "0"))
            except ValueError:
                year = 0
            make_s = _utpap_xml_text(asset, "MAKE")
            model_s = _utpap_xml_text(asset, "MODEL")
            vin = _utpap_xml_text(asset, "VIN")
            reference = _utpap_xml_text(asset, "REFERENCE")
            try:
                row_int = int(_utpap_xml_text(asset, "VEHICLE_ROW", "0"))
            except ValueError:
                row_int = 0
            row_s = str(row_int) if row_int else _utpap_xml_text(asset, "VEHICLE_ROW")
            date_iso = _utpap_yard_date_to_iso(_utpap_xml_text(asset, "YARD_DATE"))

            premium = _utpap_is_premium_row(slug, row_int, reference)
            loc_name = f"{base_loc} (Premium)" if premium else base_loc

            vid = f"utpap-{slug}-{stock}"
            all_vehicles.append({
                "id": vid,
                "vin": vin,
                "year": year,
                "make": _utpap_format_label(make_s),
                "model": _utpap_format_label(model_s),
                "row": row_s,
                "dateAdded": date_iso,
                "_location": loc_name,
                "_city": store["city"],
                "_state": store["state"],
                "_source": "utpap",
                "_utpap_premium": premium,
            })

    # Deduplicate by id (defensive)
    seen: set[str] = set()
    unique: list[dict] = []
    for v in all_vehicles:
        i = v.get("id", "")
        if i and i not in seen:
            seen.add(i)
            unique.append(v)

    print(f"  [Utah Pic-A-Part] {len(unique)} vehicles (Ogden + Orem)", file=sys.stderr)
    return unique


def refresh_utpap_pricing_file() -> Path:
    """Download Utah Pic-A-Part published pricelist HTML and write utpap_pricing.json for the web UI."""
    r = requests.get(UTPAP_PRICELIST_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    rows: list[dict] = []
    for m in re.finditer(r"<tr><td>([^<]+)</td><td>([\d.]+)</td><td>([\d.]+)</td>", r.text):
        desc, price, core = m.group(1).strip(), m.group(2), m.group(3)
        tp = float(price) + float(core)
        rows.append({
            "description": desc,
            "price": price,
            "corePrice": core,
            "totalPrice": f"{tp:.2f}",
        })
    out = DATA_DIR / "utpap_pricing.json"
    out.write_text(json.dumps(rows, indent=2))
    return out


# ---------------------------------------------------------------------------
# LKQ Pick Your Part (pyp.com)
# ---------------------------------------------------------------------------

def fetch_pyp_stores() -> list[dict]:
    """Store list (code, name, state, lat, lng) embedded in pyp.com/inventory/."""
    r = requests.get(f"{PYP_BASE}/inventory/", headers=PYP_HEADERS, timeout=30)
    r.raise_for_status()
    stores = []
    for m in re.finditer(
        r'option value="(\d+)" data-state="([^"]+)" data-lat="([^"]+)" '
        r'data-lng="([^"]+)" data-name="([^"]+)"',
        r.text,
    ):
        code, state_full, lat, lng, name = m.groups()
        city = name.split(" - ", 1)[1] if " - " in name else name
        stores.append({
            "code": code,
            "name": name.strip(),
            "city": city.strip(),
            "state": US_STATE_ABBREV.get(state_full.strip().lower(), state_full.strip()),
            "lat": float(lat),
            "lng": float(lng),
        })
    return stores


def _split_ymm(ymm: str) -> tuple[int, str, str]:
    """'2004 LAND ROVER DISCOVERY' -> (2004, 'Land Rover', 'Discovery')."""
    parts = ymm.split()
    if not parts:
        return 0, "", ""
    try:
        year = int(parts[0])
        parts = parts[1:]
    except ValueError:
        year = 0
    rest = " ".join(parts)
    make, model = (parts[0] if parts else ""), " ".join(parts[1:])
    for twm in TWO_WORD_MAKES:
        if rest.upper().startswith(twm):
            make = rest[: len(twm)]
            model = rest[len(twm):].strip()
            break
    return year, _utpap_format_label(make), _utpap_format_label(model)


def _fetch_pyp_store_inventory(store: dict, session: requests.Session) -> list[dict]:
    """Paginate one store's inventory (20 rows/page, server-fixed)."""
    vehicles: list[dict] = []
    page = 0
    while page < 200:  # hard stop: no store holds 4,000 cars
        try:
            r = session.get(
                PYP_INVENTORY_API,
                params={"page": page, "filter": "", "store": store["code"]},
                headers=PYP_HEADERS,
                timeout=30,
            )
            r.raise_for_status()
        except Exception:
            break
        if not HAS_BS4:
            break
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select(".pypvi_resultRow")
        if not rows:
            break
        for row in rows:
            ymm_el = row.select_one(".pypvi_ymm")
            year, make, model = _split_ymm(ymm_el.get_text(" ", strip=True) if ymm_el else "")
            vin = ""
            color = ""
            for det in row.select(".pypvi_detailItem"):
                txt = det.get_text(" ", strip=True)
                if txt.upper().startswith("VIN"):
                    vin = txt[3:].strip()
                elif "\u00b7" in txt and not color:
                    # First detail item reads "Silver · 1134-55851" (color · stock)
                    cand = txt.split("\u00b7")[0].strip()
                    if cand and len(cand) <= 20 and not cand[0].isdigit():
                        color = cand
            # Each row carries one CDN photo whose URL is derived from a
            # numeric image id — store just the id ("p<id>").
            photo = ""
            img_el = row.select_one("img")
            if img_el is not None:
                m = re.search(r"/carbuy/CAR-FRONT-LEFT_(\d+)_front_left_corner\.jpg",
                              img_el.get("src") or "")
                if m:
                    photo = "p" + m.group(1)
            date_iso = ""
            t = row.select_one(".pypvi_available time")
            if t is not None and t.get("datetime"):
                date_iso = str(t["datetime"])[:10]
            section = row_no = space = ""
            for td in row.select("table.locate td"):
                label_el, val_el = td.select_one("span"), td.select_one("b")
                label = label_el.get_text(strip=True).lower() if label_el else ""
                val = val_el.get_text(strip=True) if val_el else ""
                if label == "section":
                    section = val
                elif label == "row":
                    row_no = val
                elif label == "space":
                    space = val
            row_label = row_no or ""
            if section and row_no:
                row_label = f"{section}-{row_no}"
            vehicles.append({
                "id": row.get("id", ""),  # "1134-55524" — store code + stock
                "vin": vin,
                "year": year,
                "make": make,
                "model": model,
                "row": row_label,
                "space": space,
                "dateAdded": date_iso,
                "_photo": photo,
                "_color": color,
                "_location": store["name"],
                "_city": store["city"],
                "_state": store["state"],
                "_lat": store["lat"],
                "_lng": store["lng"],
                "_source": "pyp",
            })
        if len(rows) < PYP_PAGE_SIZE:
            break
        page += 1
        time.sleep(0.15)  # be gentle: ~6 req/s across the whole worker pool
    return vehicles


def fetch_pyp_inventory() -> list[dict]:
    """Fetch live inventory from every LKQ Pick Your Part yard (pyp.com)."""
    try:
        stores = fetch_pyp_stores()
    except Exception as e:
        print(f"  [Pick Your Part] store list failed: {e}", file=sys.stderr)
        return []
    if not stores:
        print("  [Pick Your Part] no stores found on inventory page", file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    workers = _pyp_workers()
    print(f"  [Pick Your Part] {len(stores)} yards, {workers} workers...", file=sys.stderr)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        def _one(store: dict) -> list[dict]:
            session = requests.Session()
            return _fetch_pyp_store_inventory(store, session)
        for res in pool.map(_one, stores):
            all_vehicles.extend(res)

    # Dedupe by id (store-code + stock number)
    seen: set[str] = set()
    unique = []
    for v in all_vehicles:
        vid = v.get("id") or ""
        if vid and vid not in seen:
            seen.add(vid)
            unique.append(v)
    print(f"  [Pick Your Part] {len(unique)} vehicles", file=sys.stderr)
    return unique


def refresh_pnp_pricing_file(store_id: int = 74) -> Path:
    """Refresh Pick-n-Pull's published price list -> picknpull_pricing.json.

    PnP's parts API is a prefix search (api/parts/list/{store}?partKeyword=X),
    so iterate a-z/0-9 and dedupe by itemNumber. The list is chain-wide
    standard pricing; store 74 is used as the reference store. The existing
    file is only overwritten when the fetch looks complete (>300 parts), so a
    partial/failed run never clobbers good data."""
    seen: dict[str, dict] = {}
    for kw in "abcdefghijklmnopqrstuvwxyz0123456789":
        try:
            r = requests.get(
                f"{PNP_API}/parts/list/{store_id}",
                params={"language": "english", "partKeyword": kw},
                headers=HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            for p in r.json() or []:
                item = p.get("itemNumber")
                if item and item not in seen:
                    seen[item] = p
        except Exception as e:
            print(f"  [PnP pricing] keyword '{kw}': {e}", file=sys.stderr)
        time.sleep(0.2)
    path = DATA_DIR / "picknpull_pricing.json"
    if len(seen) > 300:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [PnP pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(
            f"  [PnP pricing] only {len(seen)} parts fetched — keeping existing file",
            file=sys.stderr,
        )
    return path


def refresh_pyp_pricing_file(stores: list[dict] | None = None) -> Path:
    """Per-yard PYP price lists -> pyp_pricing.json, keyed by yard display name.
    Only the keyword-mapped part descriptions are kept."""
    if stores is None:
        stores = fetch_pyp_stores()
    out: dict[str, dict] = {}
    for store in stores:
        try:
            r = requests.get(
                PYP_PRICELIST_API,
                params={"locationCode": store["code"]},
                headers=PYP_HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            rows = r.json()
        except Exception as e:
            print(f"  [PYP pricing] {store['name']}: {e}", file=sys.stderr)
            continue
        prices = {}
        for p in rows:
            desc = (p.get("Description") or "").strip()
            if desc in PYP_PRICE_DESCRIPTIONS and p.get("Price"):
                prices[desc] = {"price": p["Price"], "core": p.get("Core") or 0}
        if prices:
            out[store["name"]] = prices
        time.sleep(0.15)
    path = DATA_DIR / "pyp_pricing.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  [PYP pricing] wrote {len(out)} yard price lists", file=sys.stderr)
    return path


# ---------------------------------------------------------------------------
# Pull-A-Part (pullapart.com — includes former U-Pull-&-Pay yards)
# ---------------------------------------------------------------------------

def _pap_token(scope: str) -> str:
    r = requests.get(PAP_TOKEN_URL, params={"scope": scope}, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, str):  # endpoint double-encodes the JSON payload
        data = json.loads(data)
    return data["access_token"]


def fetch_pap_locations() -> list[dict]:
    tok = _pap_token("EnterpriseService.External")
    r = requests.get(
        f"{PAP_ENTERPRISE_API}/Location",
        params={"siteTypeID": -1},
        headers={**HEADERS, "Authorization": f"Bearer {tok}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def fetch_pap_inventory() -> list[dict]:
    """Fetch live inventory from every Pull-A-Part yard.

    One Vehicle/Search POST per make covers all ~36 locations at once, so a full
    national pull is only ~80 requests."""
    try:
        locations = fetch_pap_locations()
        inv_tok = _pap_token("InventoryService.External")
        auth = {**HEADERS, "Authorization": f"Bearer {inv_tok}",
                "Content-Type": "application/json", "Origin": PAP_SITE}
        makes_r = requests.get(f"{PAP_INVENTORY_API}/Make", headers=auth, timeout=30)
        makes_r.raise_for_status()
        makes = makes_r.json()
    except Exception as e:
        print(f"  [Pull-A-Part] setup failed: {e}", file=sys.stderr)
        return []

    loc_by_id = {l["locationID"]: l for l in locations}
    loc_ids = sorted(loc_by_id)
    all_vehicles: list[dict] = []
    print(f"  [Pull-A-Part] {len(loc_ids)} yards, {len(makes)} makes...", file=sys.stderr)
    for mk in makes:
        try:
            r = requests.post(
                f"{PAP_INVENTORY_API}/Vehicle/Search",
                json={"Locations": loc_ids, "MakeID": mk["makeID"], "Models": [], "Years": []},
                headers=auth,
                timeout=60,
            )
            r.raise_for_status()
            groups = r.json()
        except Exception:
            continue
        for grp in groups if isinstance(groups, list) else []:
            for item in (grp.get("exact") or []):
                loc = loc_by_id.get(item.get("locID")) or {}
                coords = PAP_COORDS.get(item.get("locID"))
                all_vehicles.append({
                    "id": f"pap-{item.get('locID')}-{item.get('ticketID')}-{item.get('lineID')}",
                    "vin": item.get("vin") or "",
                    "year": int(item.get("modelYear") or 0),
                    "make": _utpap_format_label(item.get("makeName") or ""),
                    "model": _utpap_format_label(item.get("modelName") or ""),
                    "row": str(item.get("row") or ""),
                    "dateAdded": str(item.get("dateYardOn") or "")[:10],
                    "_location": f"Pull-A-Part - {item.get('locName') or loc.get('locationName', '')}",
                    "_city": loc.get("cityName") or "",
                    "_state": loc.get("stateName") or "",
                    "_lat": coords[0] if coords else None,
                    "_lng": coords[1] if coords else None,
                    "_source": "pap",
                })
        time.sleep(0.2)

    seen: set[str] = set()
    unique = []
    for v in all_vehicles:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    print(f"  [Pull-A-Part] {len(unique)} vehicles", file=sys.stderr)
    return unique


def refresh_pap_pricing_file(locations: list[dict] | None = None) -> Path:
    """Per-yard Pull-A-Part price lists -> pap_pricing.json, keyed by yard
    display name (matches _location on inventory rows)."""
    if locations is None:
        locations = fetch_pap_locations()
    tok = _pap_token("EnterpriseService.External")
    auth = {**HEADERS, "Authorization": f"Bearer {tok}"}
    out: dict[str, dict] = {}
    for loc in locations:
        lid = loc["locationID"]
        try:
            r = requests.get(
                f"{PAP_ENTERPRISE_API}/partprice/GetPartsTermSearch/{lid}/",
                params={"exact": 0, "searchTerm": ""},
                headers=auth,
                timeout=45,
            )
            r.raise_for_status()
            rows = r.json()
        except Exception as e:
            print(f"  [PAP pricing] {loc.get('locationName')}: {e}", file=sys.stderr)
            continue
        prices = {}
        for p in rows if isinstance(rows, list) else []:
            name = (p.get("partname") or "").strip()
            if name in PAP_PRICE_PARTNAMES and p.get("price"):
                # Keep the cheapest variant when duplicate names appear.
                prev = prices.get(name)
                if prev is None or p["price"] < prev["price"]:
                    prices[name] = {"price": p["price"], "core": p.get("corePrice") or 0}
        if prices:
            out[f"Pull-A-Part - {loc.get('locationName', '')}"] = prices
        time.sleep(0.2)
    path = DATA_DIR / "pap_pricing.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  [PAP pricing] wrote {len(out)} yard price lists", file=sys.stderr)
    return path


# ---------------------------------------------------------------------------
# Independent / regional yards — opt-in via --independents (or
# JUNKYARD_INDEPENDENTS=1) so the scheduled scan enables them deliberately.
# Registry + research: scraper/independent_yards_registry.json and
# scraper/INDEPENDENT_YARDS.md. No photos are captured from any independent
# (chain-wide owner policy), and nothing here touches Row52 (competitor;
# Row52 is Pick-n-Pull-exclusive since their acquisition anyway).
# ---------------------------------------------------------------------------

INDEP_CACHE_DIR = CACHE_DIR / "independents"


def _indep_cache_raw(name: str, content: bytes) -> None:
    """Cache the raw upstream response (dev aid + parser forensics). Best-effort;
    the dir is gitignored with the rest of .cache."""
    try:
        INDEP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (INDEP_CACHE_DIR / name).write_bytes(content)
    except OSError:
        pass


# Wrench-A-Part (7 self-service yards, all TX) — public JSON API used by their
# own Svelte inventory page (wrenchapart.com/vehicle-search.html). One
# unauthenticated GET returns the ENTIRE multi-yard inventory (~11k vehicles);
# robots.txt allows everything. Yard ids come from their
# /api/closest-location?all=1 endpoint; coords geocoded once via Nominatim and
# hardcoded (same convention as YARD_COORDS). The feed's photo field is
# deliberately ignored (no-photos policy).
WAP_VEHICLES_API = "https://api.wrenchapart.com/v1/vehicles"
WAP_YARDS = {
    2: {"name": "Wrench-A-Part - Austin", "city": "Del Valle", "state": "TX",
        "lat": 30.1888, "lng": -97.5654},
    3: {"name": "Wrench-A-Part - Lubbock", "city": "Lubbock", "state": "TX",
        "lat": 33.5170, "lng": -101.7780},
    4: {"name": "Wrench-A-Part - Belton", "city": "Belton", "state": "TX",
        "lat": 31.0517, "lng": -97.5176},
    5: {"name": "Wrench-A-Part - San Antonio", "city": "San Antonio", "state": "TX",
        "lat": 29.4379, "lng": -98.3753},
    8: {"name": "Wrench-A-Part - Holland", "city": "Holland", "state": "TX",
        "lat": 30.9184, "lng": -97.3639},
    9: {"name": "Primo Wrench-A-Part - Del Valle", "city": "Del Valle", "state": "TX",
        "lat": 30.1892, "lng": -97.5648},
    10: {"name": "Roosevelt Wrench-A-Part - San Antonio", "city": "San Antonio",
         "state": "TX", "lat": 29.3120, "lng": -98.4745},
}


def fetch_wrenchapart_inventory() -> list[dict]:
    """Fetch live inventory from every Wrench-A-Part yard (single request)."""
    try:
        r = requests.get(WAP_VEHICLES_API, headers=HEADERS, timeout=120)
        r.raise_for_status()
        _indep_cache_raw("wrenchapart_vehicles.json", r.content)
        rows = r.json()
    except Exception as e:
        print(f"  [Wrench-A-Part] inventory fetch failed: {e}", file=sys.stderr)
        return []

    vehicles: list[dict] = []
    unknown_yards: set = set()
    for item in rows if isinstance(rows, list) else []:
        yard = WAP_YARDS.get(item.get("yard"))
        if yard is None:
            unknown_yards.add(item.get("yard"))
            continue
        stock = (item.get("stockNumber") or "").strip()
        if not stock:
            continue
        make_s = ((item.get("make") or {}).get("name") or "").strip()
        model_s = ((item.get("model") or {}).get("name") or "").strip()
        # Their UI displays row.id as the row number; lat/lng on the row object
        # is usually null so the hardcoded yard coords are used instead.
        row_obj = item.get("row") or {}
        row_s = str(row_obj.get("id") or "")
        vehicles.append({
            "id": f"wap-{stock}",
            "vin": (item.get("vin") or "").strip(),
            "year": int(item.get("modelYear") or 0),
            "make": _utpap_format_label(make_s),
            "model": _utpap_format_label(model_s),
            "row": row_s,
            "dateAdded": str(item.get("dateAdded") or "")[:10],
            "_color": (item.get("color") or "").strip().title(),
            "_location": yard["name"],
            "_city": yard["city"],
            "_state": yard["state"],
            "_lat": yard["lat"],
            "_lng": yard["lng"],
            "_source": "wrenchapart",
        })
    if unknown_yards:
        print(f"  [Wrench-A-Part] skipped unknown yard id(s): {sorted(unknown_yards)} "
              "— update WAP_YARDS/registry", file=sys.stderr)

    seen: set[str] = set()
    unique = []
    for v in vehicles:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    print(f"  [Wrench-A-Part] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Wrench-A-Part publishes a real per-location price list through the same API
# their Svelte price-list pages use (wrenchapart.com/{slug}-price-list).
# Prices genuinely differ per yard, and each item carries one or more price
# groups: STANDARD at the regular yards, PREMIUM at Primo (late-model yard) —
# prefer STANDARD, fall back to PREMIUM.
WAP_PRICELIST_API = "https://api.wrenchapart.com/price-list"

# Part names worth carrying into the per-yard price file (keyword-mapped by the
# web UI) — same size-control convention as PYP_PRICE_DESCRIPTIONS above.
WAP_PRICE_PARTNAMES = {
    "HEADLAMP COMP HID", "HEADLAMP COMPOSITE NO HID", "TAIL LIGHT SMALL",
    "FOG LIGHT", "BENCH SEAT", "SEAT TRACK ELECTRIC", "INSTRUMENT CLUSTER DIGITAL",
    "INSTRUMENT CLUSTER ANALOG", "GAUGE (SINGLE/MISC)", "ALTERNATOR",
    "HYBRID BATTERY", "WATER PUMP", "INVERTER HYBRID", "AMPLIFIER OEM",
    'SPEAKER 0-5.9"', "RADIO (SCREEN)", "RADIO (NO SCREEN)", "HEADREST SCREEN",
    "BUMPER ASSEMBLY FRONT CAR", "BUMPER COVER FRONT (BARE)", "TAILGATE BARE",
    "SPOILER NO LIGHT", 'GRILLE 19-48"', "RUNNING BOARD NON-ELECTRIC",
    "FENDER TRIM/ FLARES", "EMBLEM (SMALL)", "SKID PLATE",
    "DOOR MIRROR POWER REGULAR", "LUGGAGE RACK", "CARGO COVER RETRACTABLE",
    "TRAILERHITCH RECEIVER", "SUNROOF ASSEMBLY ELECTRIC", "SUNROOF GLASS ONLY",
    "CONVERTIBLE TOP MOTOR", "CONVERTIBLE TOP ASSEMBLY", "CONVERTIBLE TOP CLOTH ONLY",
    "DOOR GLASS TRUCK", "BACK GLASS TRUCK", "BACK GLASS HATCH",
    "WINDOW REGULATOR W/ MOTOR", "SWITCH, MASTER WINDOW", 'TRIM LARGE 18"+',
    'TRIM MEDIUM 9-18"', "DASH PAD", "CONSOLE LID", 'CONSOLE LG 17"+',
    "SHIFTER LEVER ASSY", "PEDAL ASSEMBLY", "TRANSFER CASE MOTOR",
    "SWITCH, SINGLE", "DIFFERENTIAL CARRIER W/ GEARS", "INTAKE MANIFOLD OEM",
    "INTERCOOLER", "SUSPENSION AIR BAG", "HOOD SHOCK", "HATCH SHOCK",
    "AIR SHOCK ONLY", "SHOCK ABSORBER NO SPRING", "CALIPER 4 PISTON",
    "CALIPER 1 PISTON", "STEERING WHEEL NO AIR BAG", "MODULE, BODY CONTROL",
    "CAMERA", "CABLE (MISCELLANEOUS)", "WIPER MOTOR", "4X4 ACTUATOR",
    "TRANSFER CASE ASSEMBLY", "FLOOR MAT/ SPARE TIRE COVER",
}


def refresh_wap_pricing_file() -> Path:
    """Per-yard Wrench-A-Part price lists -> wap_pricing.json, keyed by yard
    display name (matches _location on inventory rows)."""
    out: dict[str, dict] = {}
    for yard_id, yard in WAP_YARDS.items():
        try:
            r = requests.get(
                WAP_PRICELIST_API,
                params={"locationId": str(yard_id)},
                headers=HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            rows = r.json()
        except Exception as e:
            print(f"  [WAP pricing] {yard['name']}: {e}", file=sys.stderr)
            continue
        prices = {}
        for p in rows if isinstance(rows, list) else []:
            name = (p.get("name") or "").strip()
            if name not in WAP_PRICE_PARTNAMES:
                continue
            # Group names vary by yard ("STANDARD", "Standard", "PREMIUM" at
            # the Primo late-model yard) — prefer standard, else take any.
            groups = {k.upper(): v for k, v in (p.get("prices") or {}).items()}
            entry = groups.get("STANDARD") or groups.get("PREMIUM") or next(iter(groups.values()), None)
            if not entry:
                continue
            try:
                price = float(entry.get("price"))
            except (TypeError, ValueError):
                continue
            try:
                core = float(entry.get("core"))
            except (TypeError, ValueError):
                core = 0.0  # the API uses "-" for no core charge
            prices[name] = {"price": price, "core": core}
        if prices:
            out[yard["name"]] = prices
        time.sleep(0.2)
    path = DATA_DIR / "wap_pricing.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  [WAP pricing] wrote {len(out)} yard price lists", file=sys.stderr)
    return path


# U-Pull-R Parts (Rosemount + East Bethel MN, Toledo OH) — WordPress
# admin-ajax gateway returning clean JSON; robots.txt explicitly allows
# admin-ajax.php. Same vendor plugin family as Pull-N-Save
# ("gm_vehicle_search" — see INDEPENDENT_YARDS.md). The scan is getVehicles
# per make × site. A single makes=0 request would be cheaper, but its rows
# carry no make: Model is just "MALIBU"/"CIVIC" except for ~15% of literal DB
# names like "FORD F150 PICKUP", so per-make queries (the same flow their own
# search UI uses) are the only reliable source of the make.
# PLUGIN UPGRADE 2026-10-13 (silently broke the adapter for 4 days; fixed
# 2026-10-17): the AJAX action was renamed doApiCall → doAaaApiCall (the old
# one returns HTTP 400 body '0'), site=0 is no longer valid — site=1 returns
# BOTH MN stores (rows tagged Store 1 Rosemount / 2 East Bethel) and site=3
# Toledo — and getMakes takes a ModelYear param (empty = all, 56 makes).
# Response fields are unchanged apart from ignorable extras. ~112 requests
# per scan (56 makes × 2 sites) at 2s pacing.
UPR_AJAX = "https://upullrparts.com/wp-admin/admin-ajax.php"
UPR_STORES = {
    1: {"name": "U-Pull-R Parts - Rosemount", "city": "Rosemount", "state": "MN",
        "lat": 44.7185, "lng": -93.1261},
    2: {"name": "U-Pull-R Parts - East Bethel", "city": "East Bethel", "state": "MN",
        "lat": 45.3887, "lng": -93.2341},
    3: {"name": "U-Pull-R Parts - Toledo", "city": "Toledo", "state": "OH",
        "lat": 41.7188, "lng": -83.5380},
}
UPR_DELAY_SEC = 2.0  # ~1 request / 2s per host
UPR_HEADERS = {
    **HEADERS,
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://upullrparts.com/inventory/",
    "Origin": "https://upullrparts.com",
}


def fetch_upullr_inventory() -> list[dict]:
    """Fetch live inventory from U-Pull-R Parts (2 MN yards + Toledo OH).

    One getVehicles POST per make × site (site=1 = both MN stores, site=3 =
    Toledo), ~2s apart — the same flow their own search UI issues since the
    2026-10 plugin upgrade; ~112 requests / ~4 min per scan."""
    session = requests.Session()

    def _post(api_action: str, **extra) -> requests.Response:
        return session.post(
            UPR_AJAX,
            data={"action": "doAaaApiCall", "apiAction": api_action, **extra},
            headers=UPR_HEADERS,
            timeout=60,
        )

    try:
        r = _post("getMakes", ModelYear="")
        r.raise_for_status()
        makes = json.loads(r.text) if r.text else []
    except Exception as e:
        print(f"  [U-Pull-R] getMakes failed: {e}", file=sys.stderr)
        return []
    makes = [m.strip() for m in makes if isinstance(m, str) and m.strip()]

    all_vehicles: list[dict] = []
    for make_name in makes:
        rows = []
        for site in ("1", "3"):  # 1 = Rosemount + East Bethel, 3 = Toledo
            time.sleep(UPR_DELAY_SEC)
            try:
                r = _post("getVehicles", site=site, makes=make_name, models="0",
                          years="0", beginDate="", endDate="")
                r.raise_for_status()
                site_rows = json.loads(r.text) if r.text.strip() else []
            except Exception as e:
                print(f"  [U-Pull-R] make {make_name!r} site {site} fetch failed: {e}",
                      file=sys.stderr)
                continue
            if isinstance(site_rows, list):
                rows.extend(site_rows)
        if not rows:
            continue
        _indep_cache_raw(f"upullr_{re.sub(r'[^A-Za-z0-9]+', '_', make_name)}.json",
                         json.dumps(rows).encode())
        for item in rows:
            stock = str(item.get("StockNumber") or "").strip()
            if not stock:
                continue
            store = UPR_STORES.get(item.get("Store"))
            if store is None:
                continue
            # Some DB model names repeat the make ("MAZDA 6", "FORD F150
            # PICKUP") — strip it so the UI doesn't show "Mazda Mazda 6".
            model_s = str(item.get("Model") or "").strip()
            if model_s.upper().startswith(make_name.upper() + " "):
                model_s = model_s[len(make_name):].strip()
            color = str(item.get("Color") or "").strip().title()
            all_vehicles.append({
                "id": f"upullr-{item.get('Store')}-{stock}",
                "vin": str(item.get("VIN") or "").strip(),
                "year": int(item.get("Year") or 0),
                "make": _utpap_format_label(make_name),
                "model": _utpap_format_label(model_s),
                "row": str(item.get("Row") or ""),
                "dateAdded": str(item.get("DateSetData") or "")[:10],
                "_color": "" if color.lower() == "unknown" else color,
                "_location": store["name"],
                "_city": store["city"],
                "_state": store["state"],
                "_lat": store["lat"],
                "_lng": store["lng"],
                "_source": "upullr",
            })

    seen: set[str] = set()
    unique = []
    for v in all_vehicles:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    print(f"  [U-Pull-R] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# U-Pull-R publishes one chain-wide flat-rate price list (same prices at all
# three yards) at upullrparts.com/part-pricing/ — standard Elementor price-list
# widgets, parsed with a regex. Stored flat like tearapart/utpap pricing.
UPR_PRICING_URL = "https://upullrparts.com/part-pricing/"

# The page's hidden style-template widget contains placeholder rows.
_UPR_PLACEHOLDER_ROWS = {
    "do not delete this list widget",
    "it is used to style the main list",
    "second item on the list",
    "third item on the list",
}


def refresh_upullr_pricing_file() -> Path:
    """Refresh U-Pull-R's published price list -> upullr_pricing.json.

    The existing file is only overwritten when the fetch looks complete
    (>200 parts), so a partial/failed run never clobbers good data."""
    import html as html_mod

    try:
        r = requests.get(UPR_PRICING_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [U-Pull-R pricing] fetch failed: {e}", file=sys.stderr)
        return DATA_DIR / "upullr_pricing.json"

    rows = re.findall(
        r'elementor-price-list-title">([^<]+)</span>.*?'
        r'elementor-price-list-price">\$?\s*([0-9][0-9.,]*)</span>\s*</div>'
        r'(?:<p class="elementor-price-list-description">([^<]*)</p>)?',
        page,
        re.S,
    )
    seen: dict[str, dict] = {}
    for name, price, desc in rows:
        name = html_mod.unescape(name).strip()
        if not name or name.lower() in _UPR_PLACEHOLDER_ROWS:
            continue
        try:
            price_f = float(price.replace(",", ""))
        except ValueError:
            continue
        core = 0.0
        m = re.search(r"Core Price:\s*\$?\s*([0-9.]+)", desc or "")
        if m:
            core = float(m.group(1))
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core:.2f}",
                "totalPrice": f"{price_f + core:.2f}",
            }

    path = DATA_DIR / "upullr_pricing.json"
    if len(seen) > 200:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [U-Pull-R pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(
            f"  [U-Pull-R pricing] only {len(seen)} parts parsed — keeping existing file",
            file=sys.stderr,
        )
    return path


# Fenix U-Pull (fenixupull.com) — 3 upstate-NY yards + Belleville MI (Detroit
# metro) + Moultrie GA. First Northeast (NY) coverage in the app.
# WordPress/Divi, but /recent-inventory/
# server-renders the entire multi-yard list as a plain HTML table, 50 rows a
# page (?pg=N, newest-first), ~130 pages / ~6,500 rows. robots.txt allows all
# (an orphaned Crawl-delay:10 sits above the UA group; we pace at 2s like the
# other independents). Coords geocoded once via Nominatim (same convention as
# YARD_COORDS). No photo capture (chain-wide owner policy).
FENIX_INVENTORY_URL = "https://fenixupull.com/recent-inventory/"
FENIX_DELAY_SEC = 2.0
FENIX_MAX_PAGES = 250  # hard stop; ~130 pages observed 2026-09
FENIX_YARDS = {
    # keyed by the inventory table's "Location" column, lowercased
    "binghamton, ny": {"name": "Fenix U-Pull - Binghamton", "city": "Binghamton",
                       "state": "NY", "lat": 42.1095, "lng": -75.8218},
    "east syracuse, ny": {"name": "Fenix U-Pull - East Syracuse", "city": "East Syracuse",
                          "state": "NY", "lat": 43.0939, "lng": -76.0391},
    "elmira, ny": {"name": "Fenix U-Pull - Elmira", "city": "Elmira",
                   "state": "NY", "lat": 42.1561, "lng": -76.8627},
    "moultrie, ga": {"name": "Fenix U-Pull - Moultrie", "city": "Moultrie",
                     "state": "GA", "lat": 31.1759, "lng": -83.7494},
    "belleville, mi": {"name": "Fenix U-Pull - Belleville", "city": "Belleville",
                       "state": "MI", "lat": 42.1726, "lng": -83.5419},
}

_FENIX_ROW_RE = re.compile(r"<tr>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)
_FENIX_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def _fenix_parse_page(page: str) -> list[list[str]]:
    """Rows of stripped cell text from a /recent-inventory/ page."""
    rows = []
    for block in _FENIX_ROW_RE.findall(page):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in _FENIX_TD_RE.findall(block)]
        if len(cells) >= 8:
            rows.append(cells)
    return rows


def _fenix_parse_date(date_raw: str) -> str:
    """MM/DD/YY(YY) from the Fenix inventory table -> 'YYYY-MM-DD' or ''.

    Two-digit years are windowed, not blindly '20'-prefixed: Fenix's feed
    carries Unix-epoch placeholder rows dated 01/01/70 (seen at Moultrie,
    2026-10; garbage VINs too), which '20'+yy turned into 2070-01-01 — the
    app then showed them as 'Set out Jan 1 · fresh' with a NEW badge.
    yy >= 69 is read as 19yy, so the placeholders become 1970-01-01 and the
    global _sanitize_date_added() clamp drops them as implausibly old."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{2,4})", date_raw.strip())
    if not m:
        return ""
    yy = m.group(3)
    if len(yy) == 4:
        year = yy
    else:
        year = ("19" + yy) if int(yy) >= 69 else ("20" + yy)
    return f"{year}-{m.group(1)}-{m.group(2)}"


def fetch_fenix_inventory() -> list[dict]:
    """Fetch live inventory from every Fenix U-Pull yard (paged HTML table).

    Columns: date placed (MM/DD/YY), make, model, year, row, VIN, stock number,
    location ("City, ST"), image, more-info link."""
    session = requests.Session()
    base_params = {"sort_column": "date_placed", "sort_direction": "DESC"}

    all_vehicles: list[dict] = []
    unknown_yards: set = set()
    total_pages = FENIX_MAX_PAGES
    pg = 1
    while pg <= min(total_pages, FENIX_MAX_PAGES):
        page = None
        for attempt in (1, 2):
            try:
                r = session.get(FENIX_INVENTORY_URL, params={**base_params, "pg": pg},
                                headers={**HEADERS, "Accept": "text/html"}, timeout=45)
                r.raise_for_status()
                page = r.text
                break
            except Exception as e:
                print(f"  [Fenix] page {pg} attempt {attempt} failed: {e}", file=sys.stderr)
                time.sleep(5)
        if page is None:
            break
        if pg == 1:
            _indep_cache_raw("fenix_page1.html", r.content)
            pg_links = [int(n) for n in re.findall(r"pg=(\d+)", page)]
            if pg_links:
                total_pages = max(pg_links)
        rows = _fenix_parse_page(page)
        if not rows:
            break
        for cells in rows:
            date_raw, make, model, year_s = cells[0], cells[1], cells[2], cells[3]
            row_n = cells[4] if len(cells) > 4 else ""
            vin = cells[5] if len(cells) > 5 else ""
            stock = cells[6] if len(cells) > 6 else ""
            loc_raw = cells[7] if len(cells) > 7 else ""
            yard = FENIX_YARDS.get(loc_raw.strip().lower())
            if yard is None:
                unknown_yards.add(loc_raw)
                continue
            if not stock:
                continue
            date_iso = _fenix_parse_date(date_raw)
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            all_vehicles.append({
                "id": f"fenix-{stock}",
                "vin": vin.strip(),
                "year": year_i,
                "make": _utpap_format_label(make),
                "model": _utpap_format_label(model),
                "row": row_n,
                "dateAdded": date_iso,
                "_location": yard["name"],
                "_city": yard["city"],
                "_state": yard["state"],
                "_lat": yard["lat"],
                "_lng": yard["lng"],
                "_source": "fenix",
            })
        pg += 1
        time.sleep(FENIX_DELAY_SEC)

    if unknown_yards:
        print(f"  [Fenix] unknown Location values skipped: {sorted(unknown_yards)}",
              file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Fenix] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Fenix publishes a per-location price list on /parts-prices/ — the location
# is selected via an fnx_location cookie (1=Elmira, 2=Binghamton,
# 3=East Syracuse, 4=Moultrie; Belleville has no list yet — their own JS
# resets its id). Server-rendered <table class="fnx-table"> rows:
# <td>PART</td><td>Price: $X.XX</br>Core: $Y.YY</td>. Stored per-yard like
# wap_pricing.json since the GA list differs from the NY ones.
FENIX_PRICE_URL = "https://fenixupull.com/parts-prices/"
FENIX_PRICE_LOCATIONS = {
    1: "Fenix U-Pull - Elmira",
    2: "Fenix U-Pull - Binghamton",
    3: "Fenix U-Pull - East Syracuse",
    4: "Fenix U-Pull - Moultrie",
}
_FENIX_PRICE_ROW_RE = re.compile(
    r"<td>([^<]+)</td>\s*<td>\s*Price:\s*\$\s*([\d.,]+)\s*(?:</?br/?>\s*Core:\s*\$\s*([\d.,]+))?",
    re.S,
)


def refresh_fenix_pricing_file() -> Path:
    """Refresh Fenix U-Pull's per-location price lists -> fenix_pricing.json.

    Only overwrites when every location parsed non-trivially (>200 parts each),
    so a partial/failed run never clobbers good data."""
    import html as html_mod

    out: dict[str, dict] = {}
    for loc_id, yard_name in FENIX_PRICE_LOCATIONS.items():
        try:
            r = requests.get(FENIX_PRICE_URL,
                             headers={**HEADERS, "Accept": "text/html",
                                      "Cookie": f"fnx_location={loc_id}"},
                             timeout=30)
            r.raise_for_status()
            page = r.text
        except Exception as e:
            print(f"  [Fenix pricing] location {loc_id} fetch failed: {e}",
                  file=sys.stderr)
            return DATA_DIR / "fenix_pricing.json"
        parts: dict[str, dict] = {}
        for name, price, core in _FENIX_PRICE_ROW_RE.findall(page):
            name = html_mod.unescape(name).strip().upper()
            if not name:
                continue
            try:
                parts.setdefault(name, {
                    "price": float(price.replace(",", "")),
                    "core": float(core.replace(",", "")) if core else 0.0,
                })
            except ValueError:
                continue
        if len(parts) < 200:
            print(f"  [Fenix pricing] only {len(parts)} parts for {yard_name} — "
                  "keeping existing file", file=sys.stderr)
            return DATA_DIR / "fenix_pricing.json"
        out[yard_name] = parts
        time.sleep(FENIX_DELAY_SEC)

    path = DATA_DIR / "fenix_pricing.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"  [Fenix pricing] wrote {sum(len(v) for v in out.values())} rows "
          f"across {len(out)} yards", file=sys.stderr)
    return path


# Harry's U-Pull-It (wegotused.com) — 3 large eastern-PA yards (Hazle Township,
# Allentown, Pennsburg). Site sits behind Sucuri CloudProxy's JS cookie
# challenge: the response is a small page whose base64 payload builds a
# sucuri_cloudproxy_uuid_* cookie out of string concatenation, then reloads.
# _sucuri_solve() evaluates that concatenation in pure Python (no JS engine);
# the cookie is UA-bound and lasts 24h. Past the challenge, /our-inventory/
# server-renders 15 rows a page (?inv[page]=N), ~285 pages / ~4,300 rows.
# robots.txt allows all. Coords geocoded once via Nominatim.
HARRYS_INVENTORY_URL = "https://wegotused.com/our-inventory/"
HARRYS_DELAY_SEC = 1.0
HARRYS_MAX_PAGES = 400  # hard stop; ~285 pages observed 2026-09
HARRYS_YARDS = {
    # keyed by the inventory table's "Yard City" column, uppercased
    "HAZLE TOWNSHIP": {"name": "Harry's U-Pull-It - Hazle Township", "city": "Hazle Township",
                       "state": "PA", "lat": 40.9564, "lng": -76.0113},
    "ALLENTOWN": {"name": "Harry's U-Pull-It - Allentown", "city": "Allentown",
                  "state": "PA", "lat": 40.6314, "lng": -75.4346},
    "PENNSBURG": {"name": "Harry's U-Pull-It - Pennsburg", "city": "Pennsburg",
                  "state": "PA", "lat": 40.3813, "lng": -75.4622},
}


def _sucuri_solve(page: str) -> str | None:
    """Solve a Sucuri CloudProxy JS challenge page -> 'name=value' cookie.

    The decoded payload is only ever string concatenation of quoted literals
    and String.fromCharCode(n) assigned to a variable, then a document.cookie
    line that concatenates the cookie name, '=', the variable, and attributes.
    Anything unexpected returns None (the caller skips the chain this scan)."""
    m = re.search(r"S='([^']+)'", page)
    if not m:
        return None
    try:
        js = base64.b64decode(m.group(1)).decode("utf-8", "replace")
        assign, cookie_part = js.split(";document.cookie=", 1)
        var_name, var_expr = assign.split("=", 1)
    except Exception:
        return None

    token_re = re.compile(
        r"String\.fromCharCode\((\d+)\)|'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|([A-Za-z_]\w*)"
    )

    def concat(expr: str, env: dict) -> str:
        out = []
        for t in token_re.finditer(expr):
            if t.group(1):
                out.append(chr(int(t.group(1))))
            elif t.group(4):
                out.append(env.get(t.group(4), ""))
            else:
                out.append(t.group(2) if t.group(2) is not None else (t.group(3) or ""))
        return "".join(out)

    val = concat(var_expr, {})
    cookie = concat(cookie_part, {var_name.strip(): val}).split(";")[0]
    return cookie if "=" in cookie and len(cookie) > 10 else None


_HARRYS_TR_RE = re.compile(r"<tr>\s*((?:<!--.*?-->\s*)?(?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)
_HARRYS_TOTAL_RE = re.compile(r"of\s+([\d,]+)\s+records")


def fetch_harrys_inventory() -> list[dict]:
    """Fetch live inventory from every Harry's U-Pull-It yard (paged HTML)."""
    session = requests.Session()
    session.headers.update({**HEADERS, "Accept": "text/html"})
    cookie: str | None = None

    def get_page(n: int) -> str | None:
        nonlocal cookie
        for attempt in (1, 2, 3):
            try:
                hdrs = {"Cookie": cookie} if cookie else {}
                r = session.get(HARRYS_INVENTORY_URL,
                                params={"inv[yard]": "all", "inv[page]": str(n)},
                                headers=hdrs, timeout=45)
                page = r.text
            except Exception as e:
                print(f"  [Harry's] page {n} attempt {attempt} failed: {e}",
                      file=sys.stderr)
                time.sleep(5 * attempt)
                continue
            if "sucuri_cloudproxy" not in page:
                return page
            cookie = _sucuri_solve(page)
            if cookie is None:
                print("  [Harry's] unrecognized Sucuri challenge — skipping this scan",
                      file=sys.stderr)
                return None
        return None

    first = get_page(1)
    if first is None:
        return []
    _indep_cache_raw("harrys_page1.html", first.encode())
    m = _HARRYS_TOTAL_RE.search(first)
    total = int(m.group(1).replace(",", "")) if m else 0
    pages = min(HARRYS_MAX_PAGES, max(1, -(-total // 15))) if total else 1

    all_vehicles: list[dict] = []
    unknown_yards: set = set()

    def parse(page: str) -> None:
        for block in _HARRYS_TR_RE.findall(page):
            cells = [re.sub(r"<[^>]+>", "", c).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            # Drop the hidden Laravel-blade yard_name cell and the contact-
            # button cell; remaining order: Yard City, Year, Make, Model,
            # Manufacturer, Color, Yard Date (MM/DD/YYYY), Row, VIN.
            cells = [c for c in cells if not c.startswith("{{")]
            if len(cells) < 9:
                continue
            yard_city, year_s, make, model = cells[0], cells[1], cells[2], cells[3]
            color, date_raw, row_n, vin = cells[5], cells[6], cells[7], cells[8]
            yard = HARRYS_YARDS.get(yard_city.strip().upper())
            if yard is None:
                unknown_yards.add(yard_city.strip())
                continue
            vin = vin.strip().upper()
            if not vin:
                continue
            m2 = re.match(r"(\d{2})/(\d{2})/(\d{4})", date_raw)
            date_iso = f"{m2.group(3)}-{m2.group(1)}-{m2.group(2)}" if m2 else ""
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            color_t = color.strip().title()
            all_vehicles.append({
                "id": f"harrys-{vin}",
                "vin": vin,
                "year": year_i,
                "make": _utpap_format_label(make),
                "model": _utpap_format_label(model),
                "row": row_n,
                "dateAdded": date_iso,
                "_color": "" if color_t.lower() in ("", "unknown") else color_t,
                "_location": yard["name"],
                "_city": yard["city"],
                "_state": yard["state"],
                "_lat": yard["lat"],
                "_lng": yard["lng"],
                "_source": "harrys",
            })

    parse(first)
    for n in range(2, pages + 1):
        time.sleep(HARRYS_DELAY_SEC)
        page = get_page(n)
        if page is None:
            break
        before = len(all_vehicles)
        parse(page)
        if len(all_vehicles) == before:  # ran off the end
            break

    if unknown_yards:
        print(f"  [Harry's] unknown Yard City values skipped: {sorted(unknown_yards)}",
              file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Harry's] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Harry's publishes one chain-wide price list (same prices at all three PA
# yards) at /price-list/, behind the same Sucuri cookie as the inventory.
# Plain table: <td>Part</td><td>$Price</td><td>Core</td>. Stored flat like
# tearapart/utpap pricing.
HARRYS_PRICE_URL = "https://wegotused.com/price-list/"
_HARRYS_PRICE_ROW_RE = re.compile(
    r"<td>([^<]+)</td>\s*<td>\s*\$\s*([\d.,]+)\s*</td>\s*<td>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_harrys_pricing_file() -> Path:
    """Refresh Harry's U-Pull-It's chain-wide price list -> harrys_pricing.json.

    Only overwritten when the fetch looks complete (>150 parts), so a
    partial/failed run never clobbers good data."""
    import html as html_mod

    cookie: str | None = None
    page = None
    for attempt in (1, 2, 3):
        try:
            hdrs = {**HEADERS, "Accept": "text/html"}
            if cookie:
                hdrs["Cookie"] = cookie
            r = requests.get(HARRYS_PRICE_URL, headers=hdrs, timeout=45)
            text = r.text
        except Exception as e:
            print(f"  [Harry's pricing] attempt {attempt} failed: {e}", file=sys.stderr)
            time.sleep(5 * attempt)
            continue
        if "sucuri_cloudproxy" not in text:
            page = text
            break
        cookie = _sucuri_solve(text)
        if cookie is None:
            print("  [Harry's pricing] unrecognized Sucuri challenge — keeping existing file",
                  file=sys.stderr)
            return DATA_DIR / "harrys_pricing.json"
    if page is None:
        return DATA_DIR / "harrys_pricing.json"

    seen: dict[str, dict] = {}
    for name, price, core in _HARRYS_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(name).strip()
        if not name:
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }

    path = DATA_DIR / "harrys_pricing.json"
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Harry's pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Harry's pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Indy-U-Pull-It (indyupullit.com) — single independent yard, Indianapolis IN.
# First user-requested yard (feedback email, 2026-10-16). WordPress/Elementor;
# /vehicle-inventory/ server-renders the whole inventory as one DataTables
# <table id="vehicles"> (~1,250 rows). Columns: Year, Make, Model, Color,
# Engine, Row, Arrival Date (MM/DD/YY; the epoch placeholder 01/01/70 means
# unknown). No VIN and no stock number anywhere, so ids are a stable hash of
# the identifying fields, with an ordinal suffix for exact duplicates (two
# identical cars in the same row added the same day stay distinct, and ids
# only shift within that identical group). robots.txt: allow all. One GET per
# scan. Address: 940 W 16th St (geocoded once via Nominatim, YARD_COORDS
# convention).
INDY_INVENTORY_URL = "https://indyupullit.com/vehicle-inventory/"
# indyupullit.com's host hard-blocks GitHub Actions' Azure IP ranges
# (connection resets / WAF challenge pages) while serving residential and
# Cloudflare egress normally — so the scan falls back to a fixed-allowlist
# mirror route on the yardscout-site Worker (backend/site-proxy), which
# fetches the same URL from Cloudflare's network and caches it 1h.
INDY_INVENTORY_MIRROR = "https://yardscout.io/_upstream/indy-inventory"
INDY_YARD = {"name": "Indy-U-Pull-It - Indianapolis", "city": "Indianapolis",
             "state": "IN", "lat": 39.7961, "lng": -86.1760}

_INDY_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)
_INDY_TABLE_RE = re.compile(r'<table[^>]*id="vehicles"[^>]*>(.*?)</table>', re.S)


def _indy_get_with_mirror(direct_url: str, mirror_url: str, marker_re,
                          snapshot_name: str) -> str | None:
    """GET direct_url; on failure retry the Worker mirror; on failure fall back
    to the committed snapshot (scraper/snapshots/, pushed daily from a
    residential IP by scraper/update_indy_snapshot.sh — SiteGround blocks both
    GitHub Actions and Cloudflare egress). Returns the first page whose
    content matches marker_re."""
    for label, u in (("direct", direct_url), ("mirror", mirror_url)):
        try:
            r = requests.get(u, headers={**HEADERS, "Accept": "text/html"}, timeout=60)
            r.raise_for_status()
            if marker_re.search(r.text):
                if label == "mirror":
                    print("  [Indy] direct fetch blocked — used Worker mirror", file=sys.stderr)
                return r.text
            print(f"  [Indy] {label} fetch returned page without expected content "
                  f"({len(r.content)} bytes)", file=sys.stderr)
        except Exception as e:
            print(f"  [Indy] {label} fetch failed: {e}", file=sys.stderr)
        time.sleep(3)
    snap = Path(__file__).parent / "snapshots" / snapshot_name
    if snap.exists():
        import gzip as gzip_mod
        try:
            text = gzip_mod.decompress(snap.read_bytes()).decode("utf-8", "replace")
            if marker_re.search(text):
                print(f"  [Indy] live fetches blocked — using committed snapshot "
                      f"{snapshot_name}", file=sys.stderr)
                return text
        except Exception as e:
            print(f"  [Indy] snapshot {snapshot_name} unreadable: {e}", file=sys.stderr)
    return None


def fetch_indyupullit_inventory() -> list[dict]:
    """Fetch Indy-U-Pull-It's inventory (one server-rendered table, one GET)."""
    import html as html_mod
    page = _indy_get_with_mirror(INDY_INVENTORY_URL, INDY_INVENTORY_MIRROR, _INDY_TABLE_RE,
                                 "indy_inventory.html.gz")
    if page is None:
        print("  [Indy] inventory unreachable via direct and mirror — skipping", file=sys.stderr)
        return []
    _indep_cache_raw("indy_inventory.html", page.encode())
    m = _INDY_TABLE_RE.search(page)
    if not m:
        print("  [Indy] table#vehicles not found — site layout changed?", file=sys.stderr)
        return []
    vehicles: list[dict] = []
    dupes: dict[str, int] = {}
    for block in _INDY_ROW_RE.findall(m.group(1)):
        cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _FENIX_TD_RE.findall(block)]
        if len(cells) < 7:
            continue
        year_s, make, model, color, engine, row_n, date_raw = cells[:7]
        if not make or not model:
            continue
        date_iso = ""
        dm = re.match(r"(\d{2})/(\d{2})/(\d{2,4})", date_raw)
        if dm and date_raw != "01/01/70":
            yy = dm.group(3)
            date_iso = f"{yy if len(yy) == 4 else '20' + yy}-{dm.group(1)}-{dm.group(2)}"
        try:
            year_i = int(year_s)
        except ValueError:
            year_i = 0
        base = f"{year_s}|{make}|{model}|{color}|{engine}|{row_n}|{date_iso}".lower()
        h = hashlib.sha1(base.encode()).hexdigest()[:12]
        dupes[h] = dupes.get(h, 0) + 1
        vehicles.append({
            "id": f"indy-{h}" if dupes[h] == 1 else f"indy-{h}-{dupes[h]}",
            "vin": "",
            "year": year_i,
            "make": _utpap_format_label(make),
            "model": _utpap_format_label(model),
            "row": row_n,
            "dateAdded": date_iso,
            "_location": INDY_YARD["name"],
            "_city": INDY_YARD["city"],
            "_state": INDY_YARD["state"],
            "_lat": INDY_YARD["lat"],
            "_lng": INDY_YARD["lng"],
            "_source": "indy",
        })
    print(f"  [Indy] {len(vehicles)} vehicles", file=sys.stderr)
    return vehicles


# Indy-U-Pull-It publishes a single yard-wide price list on /price-list/ —
# a server-rendered 3-column table (part, price, core charge). Same shape as
# Harry's: one chain-wide list keyed by description.
INDY_PRICE_URL = "https://indyupullit.com/price-list/"
INDY_PRICE_MIRROR = "https://yardscout.io/_upstream/indy-prices"
_INDY_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_indy_pricing_file() -> Path:
    """Refresh Indy-U-Pull-It's price list -> indy_pricing.json."""
    import html as html_mod
    page = _indy_get_with_mirror(INDY_PRICE_URL, INDY_PRICE_MIRROR, _INDY_PRICE_ROW_RE,
                                 "indy_prices.html.gz")
    if page is None:
        return DATA_DIR / "indy_pricing.json"

    seen: dict[str, dict] = {}
    for name_html, price, core in _INDY_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name:
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }

    path = DATA_DIR / "indy_pricing.json"
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Indy pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Indy pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# U-Pull-It (upullitne.com) — 4-yard chain: Des Moines IA, Omaha North/South
# and Lincoln NE. First Iowa AND first Nebraska coverage (user-requested via
# Reddit, 2026-10-16). WordPress + "TAP Inventory Search System" plugin backed
# by the Crush yard-management platform (s3clientid/crush_version in rows):
# POST admin-ajax.php action=sif_search_products with a nonce scraped from
# /search-inventory/ returns the ENTIRE chain's inventory as one JSON response
# (~2,500 rows): yard name/city/state, year, make, model, row, color, VIN
# (98.5% real 17-char), unique stock number, set date MM-DD-YYYY. All rows are
# istatus=0/location=YARD (on the lot). robots.txt: allow all (Yoast default).
# Two requests per scan: nonce GET + search POST. Not to be confused with the
# registry's blocked "ABC U-Pull-It" (also Lincoln NE — different company) or
# U-Pull-R Parts MN/OH. Coordinates geocoded once via Nominatim (YARD_COORDS
# convention).
UPULLITNE_SEARCH_URL = "https://upullitne.com/search-inventory/"
UPULLITNE_AJAX_URL = "https://upullitne.com/wp-admin/admin-ajax.php"
_UPULLITNE_NONCE_RE = re.compile(r'"sif_ajax_nonce"\s*:\s*"([0-9a-f]+)"')
UPULLITNE_YARDS = {
    "U PULL IT IA": {"name": "U-Pull-It - Des Moines", "city": "Des Moines",
                     "state": "IA", "lat": 41.6405, "lng": -93.5988},
    "U-PULL-IT INC OMAHA SOUTH": {"name": "U-Pull-It - Omaha South", "city": "Omaha",
                                  "state": "NE", "lat": 41.2045, "lng": -96.0048},
    "U-PULL-IT INC OMAHA NORTH": {"name": "U-Pull-It - Omaha North", "city": "Omaha",
                                  "state": "NE", "lat": 41.2768, "lng": -95.9364},
    "U-PULL-IT INC LINCOLN": {"name": "U-Pull-It - Lincoln", "city": "Lincoln",
                              "state": "NE", "lat": 40.8702, "lng": -96.6245},
}


def fetch_upullitne_inventory() -> list[dict]:
    """Fetch U-Pull-It's (IA/NE) 4-yard chain inventory (nonce GET + one POST)."""
    try:
        r = requests.get(UPULLITNE_SEARCH_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        m = _UPULLITNE_NONCE_RE.search(r.text)
        if not m:
            print("  [U-Pull-It IA/NE] nonce not found — site layout changed?",
                  file=sys.stderr)
            return []
        resp = requests.post(
            UPULLITNE_AJAX_URL,
            headers={**HEADERS, "Accept": "application/json",
                     "Referer": UPULLITNE_SEARCH_URL},
            data={"action": "sif_search_products", "sif_verify_request": m.group(1),
                  "make": "Any", "model": "Any", "location": "Any",
                  "year_start": "", "year_end": "", "sorting": "0"},
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"  [U-Pull-It IA/NE] fetch failed: {e}", file=sys.stderr)
        return []
    if not payload.get("success"):
        print(f"  [U-Pull-It IA/NE] search returned success=false: "
              f"{str(payload.get('message'))[:120]}", file=sys.stderr)
        return []
    products = payload.get("products") or []
    _indep_cache_raw("upullitne_inventory.json", resp.content)

    vehicles: list[dict] = []
    unknown_yards: set[str] = set()
    for p in products:
        yard = UPULLITNE_YARDS.get((p.get("yard_name") or "").strip())
        if yard is None:
            unknown_yards.add((p.get("yard_name") or "?").strip())
            continue
        make = (p.get("make") or "").strip()
        model = (p.get("model") or "").strip()
        if not make or not model:
            continue
        date_iso = ""
        dm = re.match(r"(\d{2})-(\d{2})-(\d{4})", (p.get("yard_date") or "").strip())
        if dm:
            date_iso = f"{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
        try:
            year_i = int(p.get("iyear") or 0)
        except ValueError:
            year_i = 0
        stock = (p.get("stocknumber") or "").strip()
        if not stock:  # never seen, but ids must stay stable and unique
            stock = hashlib.sha1(
                f"{year_i}|{make}|{model}|{p.get('vin')}|{p.get('vehicle_row')}"
                .lower().encode()).hexdigest()[:12]
        vin = (p.get("vin") or "").strip().upper()
        vehicles.append({
            "id": f"upullitne-{stock.lower()}",
            "vin": vin if len(vin) == 17 else "",
            "year": year_i,
            "make": _utpap_format_label(make),
            "model": _utpap_format_label(model),
            "row": (p.get("vehicle_row") or "").strip(),
            "dateAdded": date_iso,
            "_location": yard["name"],
            "_city": yard["city"],
            "_state": yard["state"],
            "_lat": yard["lat"],
            "_lng": yard["lng"],
            "_source": "upullitne",
        })
    if unknown_yards:
        print(f"  [U-Pull-It IA/NE] skipped rows from unmapped yard(s): "
              f"{sorted(unknown_yards)}", file=sys.stderr)
    print(f"  [U-Pull-It IA/NE] {len(vehicles)} vehicles across "
          f"{len({v['_location'] for v in vehicles})} yards", file=sys.stderr)
    return vehicles


# U-Pull-It (IA/NE) publishes one chain-wide price list on /parts-pricelist/ —
# a server-rendered 4-column table (Part Name, Price, Core, Labor; Labor is
# $0.00 across the board today and is ignored). Same harrys-style output shape.
UPULLITNE_PRICE_URL = "https://upullitne.com/parts-pricelist/"
_UPULLITNE_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_upullitne_pricing_file() -> Path:
    """Refresh U-Pull-It's (IA/NE) price list -> upullitne_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "upullitne_pricing.json"
    try:
        r = requests.get(UPULLITNE_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [U-Pull-It IA/NE pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path

    seen: dict[str, dict] = {}
    for name_html, price, core in _UPULLITNE_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() == "part name":
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }

    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [U-Pull-It IA/NE pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [U-Pull-It IA/NE pricing] only {len(seen)} parts parsed — "
              f"keeping existing file", file=sys.stderr)
    return path


# Rupert's U-Pull-It (rupertsupullit.com) — single yard, Fredericksburg VA.
# First mainland-Virginia yard (user-requested via Reddit, Northern VA,
# 2026-10-16). WordPress running the "yardconnect-pro" plugin (owned by M&M
# Auto Parts). GET /search-our-inventory/?make=all&... server-renders the
# ENTIRE inventory as one table (~830 rows, ~6.7 MB): Make, Model, Year, Body
# Style, Engine, Yard Row, Date Set (MM/DD/YY). Each row's thumbnail <img>
# carries a unique data-stock-number (the id basis). CAVEAT: the all-makes
# query takes ~35-45s server-side — timeout=120 with one retry. robots.txt:
# Crawl-Delay 3, no disallows; one request per scan. Price list at
# /parts-list/ (~470 parts: name, price, core, labor-ignored). Address:
# 11000 Houser Dr, Fredericksburg VA 22408 (Nominatim resolves the 22408
# centroid; Houser Dr itself is not in OSM).
RUPERTS_INVENTORY_URL = ("https://rupertsupullit.com/search-our-inventory/"
                         "?make=all&model=all&year_start=1963&year_end=2026")
RUPERTS_YARD = {"name": "Rupert's U-Pull-It - Fredericksburg", "city": "Fredericksburg",
                "state": "VA", "lat": 38.2453, "lng": -77.4653}

_RUPERTS_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)
_RUPERTS_STOCK_RE = re.compile(r'data-stock-number="([^"]+)"')


def fetch_ruperts_inventory() -> list[dict]:
    """Fetch Rupert's U-Pull-It inventory (one slow server-rendered GET)."""
    import html as html_mod
    page = None
    for attempt in (1, 2):  # the ~40s query occasionally times out — one retry
        try:
            r = requests.get(RUPERTS_INVENTORY_URL,
                             headers={**HEADERS, "Accept": "text/html"}, timeout=120)
            r.raise_for_status()
            if "data-stock-number" in r.text:
                page = r.text
                break
            print(f"  [Rupert's] attempt {attempt} returned page without inventory "
                  f"({len(r.content)} bytes)", file=sys.stderr)
        except Exception as e:
            print(f"  [Rupert's] attempt {attempt} failed: {e}", file=sys.stderr)
        time.sleep(5)
    if page is None:
        print("  [Rupert's] inventory unreachable — skipping", file=sys.stderr)
        return []
    _indep_cache_raw("ruperts_inventory.html", page.encode())

    vehicles: list[dict] = []
    for block in _RUPERTS_ROW_RE.findall(page):
        cells = _FENIX_TD_RE.findall(block)
        if len(cells) < 8:
            continue
        sm = _RUPERTS_STOCK_RE.search(cells[0])
        if not sm:
            continue  # header or non-vehicle row
        stock = sm.group(1).strip()
        make, model, year_s, _body, _engine, row_n, date_raw = [
            html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells[1:8]]
        if not make or not model or not stock:
            continue
        date_iso = ""
        dm = re.match(r"(\d{2})/(\d{2})/(\d{2})$", date_raw)
        if dm:
            date_iso = f"20{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
        try:
            year_i = int(year_s)
        except ValueError:
            year_i = 0
        vehicles.append({
            "id": f"ruperts-{stock.lower()}",
            "vin": "",
            "year": year_i,
            "make": _utpap_format_label(make),
            "model": _utpap_format_label(model),
            "row": row_n,
            "dateAdded": date_iso,
            "_location": RUPERTS_YARD["name"],
            "_city": RUPERTS_YARD["city"],
            "_state": RUPERTS_YARD["state"],
            "_lat": RUPERTS_YARD["lat"],
            "_lng": RUPERTS_YARD["lng"],
            "_source": "ruperts",
        })
    seen: set[str] = set()
    unique = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Rupert's] {len(unique)} vehicles", file=sys.stderr)
    return unique


# Rupert's publishes one yard-wide price list at /parts-list/ — a
# server-rendered 4-column table (Part Name, Price, Core, Labor; labor is the
# we-pull-it charge and is ignored). Harrys-style output shape.
RUPERTS_PRICE_URL = "https://rupertsupullit.com/parts-list/"
_RUPERTS_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_ruperts_pricing_file() -> Path:
    """Refresh Rupert's U-Pull-It price list -> ruperts_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "ruperts_pricing.json"
    try:
        r = requests.get(RUPERTS_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Rupert's pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _RUPERTS_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() == "part name":
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Rupert's pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Rupert's pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Pull-N-Save (pullnsave.com) — 8-yard chain: Salt Lake City + Springville UT,
# Phoenix North/South + Glendale + Gilbert + Tucson AZ, Riverside CA. Biggest
# single-chain metro win to date (Phoenix ×4). Same "gm_vehicle_search" WP
# plugin family as U-Pull-R, but getVehicles returns an HTML footable instead
# of JSON: img, Year, Model, Date Received (ISO in data-value), Row, Store
# (display name), Color, Stock#, VIN. action=getMakes returns <option> HTML.
# One POST per make with store=0 (all stores). robots.txt mandates
# Crawl-delay: 10 — honored via PNS_DELAY_SEC, so a full scan is ~45 requests
# x 10s ≈ 8 min (the scan workflow has no job timeout; default 6h). Chain-wide
# price list at /parts-pricing/ (~810 unique parts). Store coords geocoded
# once via Nominatim (YARD_COORDS convention); vehicle photos at
# app.pullnsaveapp.com are ignored (no-photos policy).
PNS_AJAX = "https://pullnsave.com/wp-admin/admin-ajax.php"
PNS_DELAY_SEC = 10.0  # robots.txt Crawl-delay: 10 — do not lower
PNS_HEADERS = {
    **HEADERS,
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.pullnsave.com/inventory-search/",
    "Origin": "https://www.pullnsave.com",
}
PNS_STORES = {  # keyed by the vehicle table's Store display name (== getStores StoreName)
    "Salt Lake City": {"name": "Pull-N-Save - Salt Lake City", "city": "Salt Lake City",
                       "state": "UT", "lat": 40.7260, "lng": -112.0343},
    "Springville": {"name": "Pull-N-Save - Springville", "city": "Springville",
                    "state": "UT", "lat": 40.1445, "lng": -111.6447},
    "Phoenix - North": {"name": "Pull-N-Save - Phoenix North", "city": "Phoenix",
                        "state": "AZ", "lat": 33.4451, "lng": -112.1207},
    "Phoenix - South": {"name": "Pull-N-Save - Phoenix South", "city": "Phoenix",
                        "state": "AZ", "lat": 33.4432, "lng": -112.1195},
    "Glendale": {"name": "Pull-N-Save - Glendale", "city": "Glendale",
                 "state": "AZ", "lat": 33.5521, "lng": -112.2065},
    "Gilbert": {"name": "Pull-N-Save - Gilbert", "city": "Gilbert",
                "state": "AZ", "lat": 33.3613, "lng": -111.8052},
    "Tucson": {"name": "Pull-N-Save - Tucson", "city": "Tucson",
               "state": "AZ", "lat": 32.1341, "lng": -110.8529},
    "Riverside": {"name": "Pull-N-Save - Riverside", "city": "Riverside",
                  "state": "CA", "lat": 33.9902, "lng": -117.3533},
}
_PNS_OPTION_RE = re.compile(r"<option value='([^']+)'")
_PNS_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)
_PNS_DATE_RE = re.compile(r"data-value='(\d{4}-\d{2}-\d{2})'")


def fetch_pns_inventory() -> list[dict]:
    """Fetch Pull-N-Save's 8-yard inventory (one getVehicles POST per make,
    10s apart per their robots.txt crawl-delay — ~8 min per scan)."""
    import html as html_mod
    session = requests.Session()
    # getMakes is intermittently empty from CI (killed the whole chain in the
    # 2026-10-17 20:02 UTC run while the same call worked 2.5h earlier) — retry
    # a few times at crawl-delay pacing and log what came back on failure.
    makes: list[str] = []
    for attempt in (1, 2, 3):
        try:
            r = session.post(PNS_AJAX, data={"action": "getMakes"}, headers=PNS_HEADERS,
                             timeout=60)
            r.raise_for_status()
            makes = [m for m in _PNS_OPTION_RE.findall(r.text) if m != "0"]
            if makes:
                break
            print(f"  [Pull-N-Save] getMakes attempt {attempt} returned no makes "
                  f"(HTTP {r.status_code}, {len(r.content)}b: {r.text[:80]!r})",
                  file=sys.stderr)
        except Exception as e:
            print(f"  [Pull-N-Save] getMakes attempt {attempt} failed: {e}", file=sys.stderr)
        time.sleep(PNS_DELAY_SEC)
    if not makes:
        print("  [Pull-N-Save] getMakes returned no makes after 3 attempts — skipping",
              file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    unknown_stores: set[str] = set()
    for make_name in makes:
        time.sleep(PNS_DELAY_SEC)
        try:
            r = session.post(PNS_AJAX,
                             data={"action": "getVehicles", "makes": make_name,
                                   "models": "0", "store": "0"},
                             headers=PNS_HEADERS, timeout=90)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Pull-N-Save] make {make_name!r} fetch failed: {e}", file=sys.stderr)
            continue
        _indep_cache_raw(f"pns_{re.sub(r'[^A-Za-z0-9]+', '_', make_name)}.html", r.content)
        for block in _PNS_ROW_RE.findall(r.text):
            raw_cells = _FENIX_TD_RE.findall(block)
            if len(raw_cells) < 9:
                continue
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in raw_cells]
            _img, year_s, model_s, _date_txt, row_n, store_s, color, stock, vin = cells[:9]
            if not stock or not model_s:
                continue
            store = PNS_STORES.get(store_s)
            if store is None:
                unknown_stores.add(store_s or "?")
                continue
            # data-value sits on the date <td>'s tag (not in the cell text),
            # so search the whole row block — each row carries exactly one.
            dm = _PNS_DATE_RE.search(block)
            date_iso = dm.group(1) if dm else ""
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            vin = vin.strip().upper()
            color = color.strip().title()
            all_vehicles.append({
                "id": f"pns-{stock.lower()}",
                "vin": vin if len(vin) == 17 else "",
                "year": year_i,
                "make": _utpap_format_label(make_name),
                "model": _utpap_format_label(model_s),
                "row": row_n,
                "dateAdded": date_iso,
                "_color": color,
                "_location": store["name"],
                "_city": store["city"],
                "_state": store["state"],
                "_lat": store["lat"],
                "_lng": store["lng"],
                "_source": "pns",
            })
    if unknown_stores:
        print(f"  [Pull-N-Save] skipped rows from unmapped store(s): "
              f"{sorted(unknown_stores)} — update PNS_STORES/registry", file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Pull-N-Save] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Pull-N-Save publishes one chain-wide price list at /parts-pricing/ — a huge
# (~6 MB) server-rendered table repeated per store tab; rows are
# (description, long name, type, item cost, enviro fee, core, warranty,
# total). We keep description + item cost + core (first occurrence wins —
# prices are identical across the repeats), harrys-style shape.
PNS_PRICE_URL = "https://www.pullnsave.com/parts-pricing/"


def refresh_pns_pricing_file() -> Path:
    """Refresh Pull-N-Save's chain-wide price list -> pns_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "pns_pricing.json"
    try:
        r = requests.get(PNS_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=120)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Pull-N-Save pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for block in _PNS_ROW_RE.findall(page):
        cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _FENIX_TD_RE.findall(block)]
        if len(cells) < 8 or not cells[0] or "$" not in cells[3]:
            continue
        name = cells[0]
        try:
            price_f = float(cells[3].replace("$", "").replace(",", ""))
            core_f = float(cells[5].replace("$", "").replace(",", ""))
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Pull-N-Save pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Pull-N-Save pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Parts Galore (parts-galore.com) — Detroit MI. First Michigan self-serve
# metro yard besides Fenix Belleville. The homepage embeds the ENTIRE
# inventory server-side as <table id="alldata"> (~1,050 rows; client JS only
# filters it): Year, Make, Model, VIN, Color, Yard Date (ISO), Row. One GET
# per scan. The table has no location column, so this ships as ONE yard even
# though Parts Galore operates multiple Detroit locations (noted in the
# registry) — main address 11360 E 8 Mile Rd. No stock number; the VIN (not
# always 17-char on pre-1981 cars) is the id basis, falling back to a hash of
# the identifying fields, with ordinal suffixes for exact dupes (Indy
# convention). Price list at /parts-price-list/ (~520 parts). robots: none.
PG_HOME_URL = "https://parts-galore.com/"
PG_YARD = {"name": "Parts Galore - Detroit", "city": "Detroit",
           "state": "MI", "lat": 42.4486, "lng": -83.0088}
_PG_TABLE_RE = re.compile(r'<table[^>]*id="alldata"[^>]*>(.*?)</table>', re.S)
_PG_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)


def fetch_partsgalore_inventory() -> list[dict]:
    """Fetch Parts Galore's inventory (embedded in the homepage, one GET)."""
    import html as html_mod
    try:
        r = requests.get(PG_HOME_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Parts Galore] fetch failed: {e}", file=sys.stderr)
        return []
    m = _PG_TABLE_RE.search(page)
    if not m:
        print("  [Parts Galore] table#alldata not found — site layout changed?",
              file=sys.stderr)
        return []
    _indep_cache_raw("partsgalore_home.html", page.encode())

    vehicles: list[dict] = []
    dupes: dict[str, int] = {}
    for block in _PG_ROW_RE.findall(m.group(1)):
        cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _FENIX_TD_RE.findall(block)]
        if len(cells) < 7:
            continue
        year_s, make, model, vin, color, date_raw, row_n = cells[:7]
        if not make or not model:
            continue
        try:
            year_i = int(year_s)
        except ValueError:
            year_i = 0
        vin = vin.strip().upper()
        date_iso = date_raw if re.match(r"\d{4}-\d{2}-\d{2}$", date_raw) else ""
        if vin:
            base = vin.lower()
        else:
            base = hashlib.sha1(
                f"{year_s}|{make}|{model}|{color}|{row_n}|{date_iso}".lower().encode()
            ).hexdigest()[:12]
        dupes[base] = dupes.get(base, 0) + 1
        vehicles.append({
            "id": f"pg-{base}" if dupes[base] == 1 else f"pg-{base}-{dupes[base]}",
            "vin": vin if len(vin) == 17 else "",
            "year": year_i,
            "make": _utpap_format_label(make),
            "model": _utpap_format_label(model),
            "row": row_n,
            "dateAdded": date_iso,
            "_color": color.title(),
            "_location": PG_YARD["name"],
            "_city": PG_YARD["city"],
            "_state": PG_YARD["state"],
            "_lat": PG_YARD["lat"],
            "_lng": PG_YARD["lng"],
            "_source": "partsgalore",
        })
    print(f"  [Parts Galore] {len(vehicles)} vehicles", file=sys.stderr)
    return vehicles


# Parts Galore publishes one yard-wide price list at /parts-price-list/ —
# a 3-column table (description, price with 45-day exchange, core).
PG_PRICE_URL = "https://parts-galore.com/parts-price-list/"
_PG_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*(?:\$?\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_partsgalore_pricing_file() -> Path:
    """Refresh Parts Galore's price list -> partsgalore_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "partsgalore_pricing.json"
    try:
        r = requests.get(PG_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Parts Galore pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _PG_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower().startswith("parts description"):
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Parts Galore pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Parts Galore pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Chesterfield Auto Parts (chesterfieldauto.com) — 3-yard chain, Richmond
# metro VA: Richmond (5111 Old Midlothian Tpke), Southside (12910 Genito Rd,
# Midlothian) and Fort Lee (4855 Puddledock Rd, Prince George).
# MIGRATED TO THE VINPLUS API (2026-10-22): the old ASP.NET hybrid adapter
# (weekly ~80-min token-gated make×model crawl + /newest-cars incremental
# merges persisted in docs/data/chesterfield_inventory.json) is retired —
# the chain is a VinPlus tenant (yard_id chesterfield_auto_parts, sourceSystem
# yardsmart) and the API serves MORE than the crawl ever did: full 17-char
# VINs (99.5% of rows), real chain-unique stock numbers (the crawl had
# neither — ids were field hashes), engine strings, and no weekly staleness
# window (crushed cars used to linger in the cache up to 6.5 days). Verified
# before cutover: API 2,240 rows vs 2,486 cached crawl rows, 1,982
# tuple-matched on (store, year, make, model, row) — the crawl surplus was
# stale rows from the 10-17 full crawl. See VINPLUS_TENANTS. Only the price
# list is still scraped from chesterfieldauto.com below.
CHESTERFIELD_BASE = "https://chesterfieldauto.com"


# Chesterfield publishes one chain-wide price list at /price-list — a clean
# 3-column table (Part Name, Price, Core). Harrys-style output shape.
CHESTERFIELD_PRICE_URL = CHESTERFIELD_BASE + "/price-list"
_CHESTERFIELD_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_chesterfield_pricing_file() -> Path:
    """Refresh Chesterfield Auto Parts' price list -> chesterfield_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "chesterfield_pricing.json"
    try:
        r = requests.get(CHESTERFIELD_PRICE_URL,
                         headers={**HEADERS, "Accept": "text/html"}, timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Chesterfield pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _CHESTERFIELD_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() == "part name":
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Chesterfield pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Chesterfield pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Ace Pick-A-Part (acepickapart.com) — single yard, Jacksonville FL. FIRST
# FLORIDA COVERAGE. WordPress (jupiter theme); the search page server-renders
# the make list (select#search_make) and an unauthenticated POST to the
# theme's ajax.php per make returns an HTML table: Image, Year, Make, Model,
# Exterior, Interior, Engine, Trans, Stock #, Row, Date In Yard (M/D/YYYY).
# An empty make returns nothing, so the scan is one POST per make (~42, 2s
# apart). Stock numbers ("F271121") are the id basis. CLOUDFLARE: residential
# egress is clean, but CI's datacenter IPs get a blanket 403 on EVERYTHING —
# the HTML search page AND every ajax.php POST (confirmed in the 2026-10-17
# and 10-18 scan runs; the ACE_FALLBACK_MAKES retry below is kept for the
# day the WAF rule relaxes, but it currently can't help). So, Indy-style:
# scraper/update_ace_snapshot.sh runs daily on the dev Mac via launchd
# (io.yardscout.ace-snapshot, 08:25) from a residential IP, commits the
# normalized inventory to scraper/snapshots/ace_inventory.json.gz (and
# refreshes ace_pricing.json), and the adapter falls back to that snapshot
# whenever the live crawl yields zero vehicles. Yard-wide price list at
# /prices/ (~590 parts). robots.txt: allow all. Address: 9152 N Main St
# (Nominatim resolves the 32218 zip centroid; the exact parcel is not in OSM).
ACE_SEARCH_URL = "https://acepickapart.com/search-inventory/"
ACE_AJAX_URL = "https://www.acepickapart.com/wp-content/themes/jupiter/ajax.php"
ACE_DELAY_SEC = 2.0
# select#search_make snapshot, verified 2026-10-17 — used when the search page
# itself is WAF-blocked. New makes appear in the dropdown rarely; the snapshot
# is refreshed whenever the live list is reachable and differs.
ACE_FALLBACK_MAKES = (
    "ACURA", "AUDI", "BMW", "BUICK", "CADILLAC", "CHEVROLET", "CHRYSLER",
    "DODGE", "FIAT", "FORD", "GEO", "GMC", "HONDA", "HUMMER", "HYUNDAI",
    "INFINITI", "ISUZU", "JAGUAR", "JEEP", "KIA", "LAND ROVER", "LEXUS",
    "LINCOLN", "MAZDA", "MERCEDES", "MERCURY", "MINI", "MITSUBISHI", "NISSAN",
    "OLDSMOBILE", "PLYMOUTH", "PONTIAC", "PORSCHE", "RAM", "SAAB", "SATURN",
    "SCION", "SUBARU", "SUZUKI", "TOYOTA", "VOLKSWAGEN", "VOLVO",
)
ACE_YARD = {"name": "Ace Pick-A-Part - Jacksonville", "city": "Jacksonville",
            "state": "FL", "lat": 30.4560, "lng": -81.6424}
_ACE_MAKES_RE = re.compile(r'<select[^>]*id="search_make"[^>]*>(.*?)</select>', re.S)
_ACE_OPTION_RE = re.compile(r'<option value="([^"]+)"')
_ACE_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)

# Listing transmission cells arrive in yard shorthand ("MANUAL 5SP",
# "AUTO 4SP", "AUTO CVT"). The app's manual/automatic checks are written
# against the VIN-decode display format ("5-spd Manual", "6-spd Automatic"),
# so normalize to that here. Anything unparseable or explicitly unknown
# returns "" — the transmission stays unknown, never guessed.
_LISTING_TRANS_SPEED_RE = re.compile(r"(\d+)\s*-?\s*SP(?:D|EED)?\b")


def _normalize_listing_trans(raw: str) -> str:
    t = (raw or "").strip().upper()
    if not t or t in {"UNKNOWN", "UNK", "N/A", "NA", "-", "NONE"}:
        return ""
    m = _LISTING_TRANS_SPEED_RE.search(t)
    speed = f"{m.group(1)}-spd " if m else ""
    if "MANUAL" in t or re.search(r"\bMAN\b", t):
        return f"{speed}Manual"
    if "CVT" in t:
        return f"{speed}Automatic (CVT)"
    if "AUTO" in t:
        return f"{speed}Automatic"
    return ""


def fetch_ace_inventory() -> list[dict]:
    """Fetch Ace Pick-A-Part's inventory (one ajax.php POST per make)."""
    import html as html_mod
    makes: list[str] = []
    try:
        r = requests.get(ACE_SEARCH_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        m = _ACE_MAKES_RE.search(r.text)
        makes = _ACE_OPTION_RE.findall(m.group(1)) if m else []
    except Exception as e:
        print(f"  [Ace] make-list fetch failed: {e}", file=sys.stderr)
    if not makes:
        # Cloudflare 403s the HTML page from datacenter IPs — the ajax.php
        # endpoint may still answer, so proceed with the snapshot make list.
        print(f"  [Ace] falling back to the {len(ACE_FALLBACK_MAKES)}-make snapshot list",
              file=sys.stderr)
        makes = list(ACE_FALLBACK_MAKES)

    all_vehicles: list[dict] = []
    for make_name in makes:
        time.sleep(ACE_DELAY_SEC)
        try:
            r = requests.post(ACE_AJAX_URL,
                              params={"inner_search": "true", "make": make_name},
                              headers={**HEADERS, "Accept": "text/html",
                                       "Referer": ACE_SEARCH_URL},
                              timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Ace] make {make_name!r} fetch failed: {e}", file=sys.stderr)
            continue
        for block in _ACE_ROW_RE.findall(r.text):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            if len(cells) < 10:
                continue
            # The image cell nests extra markup; the data is the LAST 10 cells.
            year_s, make, model, color, _interior, _engine, trans_raw, stock, row_n, date_raw = cells[-10:]
            if not stock or not make or not model:
                continue
            if not year_s.isdigit():  # the header row uses <td class="head-td">
                continue
            date_iso = ""
            dm = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", date_raw)
            if dm:
                date_iso = f"{dm.group(3)}-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}"
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            # Ace cars carry no VINs, so the listing's own transmission cell
            # is the only transmission signal they will ever have.
            trans_norm = _normalize_listing_trans(trans_raw)
            all_vehicles.append({
                "id": f"ace-{stock.lower()}",
                "vin": "",
                "year": year_i,
                "make": _utpap_format_label(make),
                "model": _utpap_format_label(model),
                "row": row_n,
                "dateAdded": date_iso,
                **({"_trans": trans_norm} if trans_norm else {}),
                "_color": color.title(),
                "_location": ACE_YARD["name"],
                "_city": ACE_YARD["city"],
                "_state": ACE_YARD["state"],
                "_lat": ACE_YARD["lat"],
                "_lng": ACE_YARD["lng"],
                "_source": "ace",
            })
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    if not unique:
        # Cloudflare blanket-403s CI's datacenter IPs — fall back to the
        # committed snapshot pushed daily from a residential IP (see header).
        snap = Path(__file__).parent / "snapshots" / "ace_inventory.json.gz"
        if snap.exists():
            import gzip as gzip_mod
            try:
                data = json.loads(gzip_mod.decompress(snap.read_bytes()))
                unique = data.get("vehicles", [])
                print(f"  [Ace] live crawl blocked — using committed snapshot "
                      f"({len(unique)} vehicles, fetched {data.get('fetched_at', '?')})",
                      file=sys.stderr)
            except Exception as e:
                print(f"  [Ace] snapshot unreadable: {e}", file=sys.stderr)
    print(f"  [Ace] {len(unique)} vehicles", file=sys.stderr)
    return unique


# Ace publishes one yard-wide price list at /prices/ — a 3-column table
# (Description, Price, Core Charge), repeated for mobile/desktop variants
# (first occurrence wins). Harrys-style output shape.
ACE_PRICE_URL = "https://acepickapart.com/prices/"
_ACE_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*(?:<td[^>]*>\s*</td>\s*)?<td[^>]*>(.*?)</td>\s*"
    r"<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_ace_pricing_file() -> Path:
    """Refresh Ace Pick-A-Part's price list -> ace_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "ace_pricing.json"
    try:
        r = requests.get(ACE_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Ace pricing] fetch failed: {e} — keeping existing file", file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _ACE_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() == "description":
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Ace pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Ace pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Sturtevant Auto (inventory.sturtevantauto.com) — single yard, Sturtevant WI
# (Milwaukee metro; second WI coverage). Dedicated ASP.NET inventory app on
# the CRUSH platform (/Home/* routes): the landing page server-renders the
# make list and a tokenless POST per make (VehicleMake=X&VehicleModel=)
# returns the full table: Image, Year, Make, Model, Color, Reference
# (engine), Stock # ("STK048287"), Row, Arrival Date (MM/DD/YYYY). ~46 makes
# at 2s pacing. Price list at /Home/PartPrices (~168 parts; the you-pull-it
# column). No robots.txt (404) — default pacing conventions apply.
# Coordinates: Nominatim resolves the Sturtevant village centroid (2145 NE
# Frontage Rd itself is not in OSM).
STURTEVANT_URL = "https://inventory.sturtevantauto.com/"
STURTEVANT_DELAY_SEC = 2.0
STURTEVANT_YARD = {"name": "Sturtevant Auto - Sturtevant", "city": "Sturtevant",
                   "state": "WI", "lat": 42.6981, "lng": -87.8945}
_STURTEVANT_MAKES_RE = re.compile(r"<select[^>]*>(.*?)</select>", re.S)
_STURTEVANT_OPTION_RE = re.compile(r'<option value="([^"]+)"')
_STURTEVANT_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)


def fetch_sturtevant_inventory() -> list[dict]:
    """Fetch Sturtevant Auto's inventory (one tokenless POST per make)."""
    import html as html_mod
    try:
        r = requests.get(STURTEVANT_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        m = _STURTEVANT_MAKES_RE.search(r.text)
        makes = [v for v in (_STURTEVANT_OPTION_RE.findall(m.group(1)) if m else []) if v]
    except Exception as e:
        print(f"  [Sturtevant] make-list fetch failed: {e}", file=sys.stderr)
        return []
    if not makes:
        print("  [Sturtevant] no makes parsed — site layout changed?", file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    for make_name in makes:
        time.sleep(STURTEVANT_DELAY_SEC)
        try:
            r = requests.post(STURTEVANT_URL,
                              data={"VehicleMake": make_name, "VehicleModel": ""},
                              headers={**HEADERS, "Accept": "text/html",
                                       "Content-Type": "application/x-www-form-urlencoded",
                                       "Referer": STURTEVANT_URL},
                              timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Sturtevant] make {make_name!r} fetch failed: {e}", file=sys.stderr)
            continue
        for block in _STURTEVANT_ROW_RE.findall(r.text):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            if len(cells) < 9:
                continue
            _img, year_s, make, model, color, engine, stock, row_n, date_raw = cells[-9:]
            if not stock or not make or not model:
                continue
            date_iso = ""
            dm = re.match(r"(\d{2})/(\d{2})/(\d{4})$", date_raw)
            if dm:
                date_iso = f"{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            all_vehicles.append({
                "id": f"sturtevant-{stock.lower()}",
                "vin": "",
                "year": year_i,
                "make": _utpap_format_label(make),
                "model": _utpap_format_label(model),
                "row": row_n,
                "dateAdded": date_iso,
                "_color": color.title(),
                "_location": STURTEVANT_YARD["name"],
                "_city": STURTEVANT_YARD["city"],
                "_state": STURTEVANT_YARD["state"],
                "_lat": STURTEVANT_YARD["lat"],
                "_lng": STURTEVANT_YARD["lng"],
                "_source": "sturtevant",
            })
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Sturtevant] {len(unique)} vehicles", file=sys.stderr)
    return unique


# Sturtevant publishes a price list at /Home/PartPrices — a 7-column table
# (PART DESCRIPTION, YOU PULL IT, BASIS, CORE, WE PULL IT, BASIS, CORE). The
# you-pull-it price + its core are kept. NOTE: the list is ~168 parts, close
# to the 150-part safety threshold — if they trim the published list the
# refresh keeps the existing file rather than clobbering it.
STURTEVANT_PRICE_URL = "https://inventory.sturtevantauto.com/Home/PartPrices"
_STURTEVANT_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>.*?</td>\s*<td[^>]*>\s*(?:\$\s*([\d.,]+))?\s*</td>",
    re.S,
)


def refresh_sturtevant_pricing_file() -> Path:
    """Refresh Sturtevant Auto's price list -> sturtevant_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "sturtevant_pricing.json"
    try:
        r = requests.get(STURTEVANT_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Sturtevant pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _STURTEVANT_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() == "part description":
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Sturtevant pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Sturtevant pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# iPull-uPull (ipullupull.com) — 4-yard CA chain: Fresno, Sacramento,
# Stockton, Pomona. WordPress with a custom "ipullupull-catalog" plugin whose
# export endpoint returns the ENTIRE chain as one CSV: POST admin-ajax.php
# action=ipull_export_catalog with an _ajax_nonce scraped from any catalog
# page's ipullCatalog JS object. Any non-make-filtered slug (we send
# "inventory") exports everything (~4,100 rows): Stock Number
# (city-prefixed, unique), Status, Yard Date (ISO), Yard City, Year, Make,
# Model, Vehicle Row, Color, Vin (98%+ real 17-char). Only
# Status == "Available" rows are kept (a handful are "Sold (n unsold
# parts)"). Two requests per scan. No parts price list published (the
# "Inventory & Pricing" page is the vehicle catalog). robots.txt: Yoast
# allow-all plus a few page disallows — admin-ajax and /inventory/ are
# allowed. Coordinates geocoded once via Nominatim (Stockton resolves the
# 95215 zip centroid; the Frontage Rd parcel is not in OSM).
IPULL_NONCE_URL = "https://ipullupull.com/inventory-pricing/"
IPULL_AJAX_URL = "https://ipullupull.com/wp-admin/admin-ajax.php"
_IPULL_NONCE_RE = re.compile(r'ipullCatalog\s*=\s*\{[^{}]*?"nonce"\s*:\s*"([0-9a-f]+)"')
IPULL_YARDS = {  # keyed by the CSV's "Yard City" column
    "FRESNO": {"name": "iPull-uPull - Fresno", "city": "Fresno",
               "state": "CA", "lat": 36.6852, "lng": -119.7475},
    "POMONA": {"name": "iPull-uPull - Pomona", "city": "Pomona",
               "state": "CA", "lat": 34.0556, "lng": -117.7248},
    "SACRAMENTO": {"name": "iPull-uPull - Sacramento", "city": "Sacramento",
                   "state": "CA", "lat": 38.4812, "lng": -121.4246},
    "STOCKTON": {"name": "iPull-uPull - Stockton", "city": "Stockton",
                 "state": "CA", "lat": 37.9525, "lng": -121.2240},
}


def fetch_ipull_inventory() -> list[dict]:
    """Fetch iPull-uPull's 4-yard chain inventory (nonce GET + one CSV POST)."""
    import csv
    import io
    try:
        r = requests.get(IPULL_NONCE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        m = _IPULL_NONCE_RE.search(r.text)
        if not m:
            print("  [iPull-uPull] ipullCatalog nonce not found — site layout changed?",
                  file=sys.stderr)
            return []
        resp = requests.post(
            IPULL_AJAX_URL,
            headers={**HEADERS, "Accept": "text/csv,*/*",
                     "Referer": IPULL_NONCE_URL},
            data={"action": "ipull_export_catalog", "slug": "inventory",
                  "type": "inventory", "format": "csv",
                  "export_action": "download", "_ajax_nonce": m.group(1)},
            timeout=120,
        )
        resp.raise_for_status()
        if not resp.text.startswith('"Stock Number"'):
            print(f"  [iPull-uPull] export did not return the CSV "
                  f"({resp.text[:80]!r})", file=sys.stderr)
            return []
    except Exception as e:
        print(f"  [iPull-uPull] fetch failed: {e}", file=sys.stderr)
        return []
    _indep_cache_raw("ipull_inventory.csv", resp.content)

    vehicles: list[dict] = []
    unknown_yards: set[str] = set()
    for row in csv.DictReader(io.StringIO(resp.text)):
        stock = (row.get("Stock Number") or "").strip()
        make = (row.get("Make") or "").strip()
        model = (row.get("Model") or "").strip()
        if not stock or not make or not model:
            continue
        if (row.get("Status") or "").strip().lower() != "available":
            continue
        yard = IPULL_YARDS.get((row.get("Yard City") or "").strip().upper())
        if yard is None:
            unknown_yards.add((row.get("Yard City") or "?").strip())
            continue
        date_raw = (row.get("Yard Date") or "").strip()
        date_iso = date_raw[:10] if re.match(r"\d{4}-\d{2}-\d{2}", date_raw) else ""
        try:
            year_i = int(row.get("Year") or 0)
        except ValueError:
            year_i = 0
        vin = (row.get("Vin") or "").strip().upper()
        vehicles.append({
            "id": f"ipull-{stock.lower()}",
            "vin": vin if len(vin) == 17 else "",
            "year": year_i,
            "make": _utpap_format_label(make),
            "model": _utpap_format_label(model),
            "row": (row.get("Vehicle Row") or "").strip(),
            "dateAdded": date_iso,
            "_color": (row.get("Color") or "").strip().title(),
            "_location": yard["name"],
            "_city": yard["city"],
            "_state": yard["state"],
            "_lat": yard["lat"],
            "_lng": yard["lng"],
            "_source": "ipull",
        })
    if unknown_yards:
        print(f"  [iPull-uPull] skipped rows from unmapped yard(s): "
              f"{sorted(unknown_yards)}", file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [iPull-uPull] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# St. Cloud U Pull (stccrush.com) — single yard, St. Cloud MN. Found during
# the 2026-10-17 Minnesota coverage research (first new MN yard beyond
# U-Pull-R Rosemount/East Bethel). Same CRUSH-platform ASP.NET app family as
# Sturtevant (/Home/* routes): GET /Home/Inventory server-renders the make
# list; one multipart POST per make (VehicleMake=X, VehicleModel empty — the
# form is enctype=multipart/form-data) returns the table: Photo, Year, Make,
# Model, Color, Reference (engine), Stock # ("STK000031"), Row, Yard Date
# (MM/DD/YYYY). ~28 makes at 2s pacing. No published price list found on
# stccrush.com or stcloudupull.com. No robots.txt (404). Address: 2333 12th
# St SE, St. Cloud MN 56304 (geocoded via Nominatim).
STCLOUD_URL = "https://stccrush.com/Home/Inventory"
STCLOUD_DELAY_SEC = 2.0
STCLOUD_YARD = {"name": "St. Cloud U Pull - St. Cloud", "city": "St. Cloud",
                "state": "MN", "lat": 45.5519, "lng": -94.1169}
_STCLOUD_MAKES_RE = re.compile(r"<select[^>]*>(.*?)</select>", re.S)
_STCLOUD_OPTION_RE = re.compile(r'<option value="([^"]+)"')
_STCLOUD_ROW_RE = re.compile(r"<tr[^>]*>\s*((?:<td[^>]*>.*?</td>\s*)+)</tr>", re.S)


def fetch_stcloud_inventory() -> list[dict]:
    """Fetch St. Cloud U Pull's inventory (one multipart POST per make)."""
    import html as html_mod
    try:
        r = requests.get(STCLOUD_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        m = _STCLOUD_MAKES_RE.search(r.text)
        makes = [v for v in (_STCLOUD_OPTION_RE.findall(m.group(1)) if m else []) if v]
    except Exception as e:
        print(f"  [St. Cloud] make-list fetch failed: {e}", file=sys.stderr)
        return []
    if not makes:
        print("  [St. Cloud] no makes parsed — site layout changed?", file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    for make_name in makes:
        time.sleep(STCLOUD_DELAY_SEC)
        try:
            r = requests.post(STCLOUD_URL,
                              files={"VehicleMake": (None, make_name),
                                     "VehicleModel": (None, "")},
                              headers={**HEADERS, "Accept": "text/html",
                                       "Referer": STCLOUD_URL},
                              timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"  [St. Cloud] make {make_name!r} fetch failed: {e}", file=sys.stderr)
            continue
        for block in _STCLOUD_ROW_RE.findall(r.text):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            if len(cells) < 9:
                continue
            _photo, year_s, make, model, color, engine, stock, row_n, date_raw = cells[-9:]
            if not stock or not make or not model:
                continue
            date_iso = ""
            dm = re.match(r"(\d{2})/(\d{2})/(\d{4})$", date_raw)
            if dm:
                date_iso = f"{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
            try:
                year_i = int(year_s)
            except ValueError:
                year_i = 0
            all_vehicles.append({
                "id": f"stcloud-{stock.lower()}",
                "vin": "",
                "year": year_i,
                "make": _utpap_format_label(make),
                "model": _utpap_format_label(model),
                "row": row_n,
                "dateAdded": date_iso,
                "_color": color.title(),
                "_location": STCLOUD_YARD["name"],
                "_city": STCLOUD_YARD["city"],
                "_state": STCLOUD_YARD["state"],
                "_lat": STCLOUD_YARD["lat"],
                "_lng": STCLOUD_YARD["lng"],
                "_source": "stcloud",
            })
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [St. Cloud] {len(unique)} vehicles", file=sys.stderr)
    return unique


# VinPlus platform (vinplus.texnrewards.com) — multi-tenant React SPA over an
# unauthenticated Cloud Run JSON API. VinPlus fronts MULTIPLE backend YMSs
# (sourceSystem: yardsmart AND crush observed), so it keeps absorbing yards
# regardless of their back office. One adapter, these tenants:
#   road_tested_parts — Road Tested Parts network: Bessler's U Pull & Save
#     (Hebron KY + Louisville KY), Bluegrass U Pull & Save (Lexington KY),
#     Raceway Pik-A-Part (Savannah TN), RTP Pick-A-Part (Maiden NC)
#   pickers_longview — Tri-State Iron & Metal network: Pickers (Longview TX,
#     Texarkana AR — the API says TX but the yard is at 5512 E 9th St on the
#     Arkansas side — and Reno TX), Pipes U-Pull-It (Shreveport LA)
#   joliet_u_pull_it — Joliet U-Pull-It (Joliet IL, 1014 E Washington St) —
#     first Chicago-metro independent (2026-10-22 expansion pass)
#   pick_n_pull_san_antonio — INDEPENDENT yard at 11795 Applewhite Rd, San
#     Antonio TX (picknpullsa.com). NOT the national Pick-n-Pull chain: the
#     display name deliberately does NOT start with "Pick-N-Pull" because the
#     app (and db.py) dispatch the chain's pricing/links/tool rules on that
#     name prefix.
#   195_used_auto_parts — 195 Used Auto Parts (12077 State Highway 195,
#     Killeen TX; zip-centroid coords, parcel missing from OSM)
#   pick_ur_part — Pick Ur Part Auto Salvage (4125 E Slaton Rd, Lubbock TX;
#     road-level coords, house number missing from OSM; opened Feb 2026)
# GET /api/yard-info/{tenant} → business name + locations (location_id).
# Single-location tenants report locations: [] — their location key below is
# "" and searchVehicleHttp gets location_id null (verified 2026-10-22).
# CAREFUL: the Pickers tenant's SEARCH yard_id is tri_state_iron_metal (the
# business name), not the pickers_longview URL slug — the slug silently
# returns zero matches.
# GET /api/vehicle-groups → global 49-make catalog (the SPA's make dropdown).
# POST /searchVehicleHttp {"yard_id","make","model","year_min","year_max",
# "location_id"} → rows with year/make/model/vin/stock/vehicleRow/color/
# engine/dateAdded (ISO tz)/yardLocation/daysInYard. RESULTS CAP AT 100 — the
# scan loops make × location and recursively bisects year ranges on any
# exactly-100 response. Base requests = 49 makes × locations at 2s pacing,
# all serial on the one API host. Stock numbers ("000000109811", "STK076062")
# are the id basis, location-code qualified (override with "id_prefix" when a
# migrated chain must keep its historical id scheme). Per-location "source"
# overrides _source so migrated chains keep their zero-vehicle alarm label.
# NOTE: utah-pic-a-part and ipull-upull are ALSO VinPlus tenants (already
# covered by their own adapters) — a periodic tenant-slug sweep is worth
# doing; /api/yard-info/{slug} is a free validity oracle.
# robots.txt (vinplus.texnrewards.com): allow all. Addresses from the
# tenants' sites; Lexington/Savannah/Maiden parcels missing from OSM →
# zip/town centroids.
VINPLUS_API = "https://inventory-search-api-581547763015.us-central1.run.app"
VINPLUS_DELAY_SEC = 2.0
VINPLUS_TENANTS = {
    "road_tested_parts": {
        "bessler_s_hebron": {"code": "hebron", "name": "Bessler's U Pull & Save - Hebron",
                             "city": "Hebron", "state": "KY", "lat": 39.0685, "lng": -84.7193},
        "bessler_s_louisville": {"code": "louisville", "name": "Bessler's U Pull & Save - Louisville",
                                 "city": "Louisville", "state": "KY", "lat": 38.1816, "lng": -85.7551},
        "bluegrass_lexington": {"code": "lex", "name": "Bluegrass U Pull & Save - Lexington",
                                "city": "Lexington", "state": "KY", "lat": 38.0439, "lng": -84.4995},
        "raceway": {"code": "savannah", "name": "Raceway Pik-A-Part - Savannah",
                    "city": "Savannah", "state": "TN", "lat": 35.1979, "lng": -88.2014},
        "road_tested_parts_maiden_nc": {"code": "maiden", "name": "RTP Pick-A-Part - Maiden",
                                        "city": "Maiden", "state": "NC", "lat": 35.5766, "lng": -81.2139},
    },
    # NOTE: the SEARCH yard_id is the business name, NOT the URL slug
    # (vinplus.texnrewards.com/pickers-longview + /api/yard-info/pickers_longview
    # both work, but searchVehicleHttp wants tri_state_iron_metal — a slug
    # yard_id silently returns match_count 0).
    "tri_state_iron_metal": {
        "pickers_longview": {"code": "longview", "name": "Pickers - Longview",
                             "city": "Longview", "state": "TX", "lat": 32.5130, "lng": -94.8262},
        "pickers_texarkana": {"code": "texarkana", "name": "Pickers - Texarkana",
                              "city": "Texarkana", "state": "AR", "lat": 33.4300, "lng": -93.9760},
        "pickers_reno": {"code": "reno", "name": "Pickers - Reno",
                         "city": "Reno", "state": "TX", "lat": 33.6634, "lng": -95.4537},
        "pipes_shreveport": {"code": "shreveport", "name": "Pipes U-Pull-It - Shreveport",
                             "city": "Shreveport", "state": "LA", "lat": 32.5290, "lng": -93.7721},
    },
    # --- 2026-10-22 expansion pass (single-location tenants; location_id null) ---
    "joliet_u_pull_it": {
        "": {"code": "joliet", "name": "Joliet U-Pull-It",
             "city": "Joliet", "state": "IL", "lat": 41.5231, "lng": -88.0575},
    },
    "pick_n_pull_san_antonio": {
        "": {"code": "pnpsa", "name": "San Antonio Pick-N-Pull (Independent)",
             "city": "San Antonio", "state": "TX", "lat": 29.2989, "lng": -98.5474},
    },
    "195_used_auto_parts": {
        "": {"code": "hwy195", "name": "195 Used Auto Parts",
             "city": "Killeen", "state": "TX", "lat": 31.0647, "lng": -97.7219},
    },
    "pick_ur_part": {
        "": {"code": "pickurpart", "name": "Pick Ur Part Auto Salvage",
             "city": "Lubbock", "state": "TX", "lat": 33.5200, "lng": -101.7805},
    },
    # --- migrated from the retired WordPress crawl (2026-10-22) ---
    # source stays "gopullit" for the zero-vehicle alarm; id_prefix keeps the
    # historical gopullit-{stock} scheme (stocks carry per-yard GPI*/ATL*/
    # GVL*/TAL* prefixes, chain-unique) because app.js builds tier-1 per-car
    # links from it: gopullit.com/inventory/{stock}/.
    "go_pull_it": {
        "jacksonville": {"code": "gpijax", "name": "Go Pull-It - Jacksonville",
                         "city": "Jacksonville", "state": "FL", "lat": 30.3373, "lng": -81.7697,
                         "source": "gopullit", "id_prefix": "gopullit-"},
        "atlanta_east": {"code": "gpiatl", "name": "Go Pull-It - Atlanta East",
                         "city": "Norcross", "state": "GA", "lat": 33.9631, "lng": -84.1803,
                         "source": "gopullit", "id_prefix": "gopullit-"},
        "gainesville": {"code": "gpigvl", "name": "Go Pull-It - Gainesville",
                        "city": "Gainesville", "state": "GA", "lat": 34.2810, "lng": -83.7860,
                        "source": "gopullit", "id_prefix": "gopullit-"},
        # NEW with the migration — the crawl never covered Tallahassee
        # (3900 Woodville Hwy, Tallahassee FL 32305; exact OSM parcel).
        "tallahassee": {"code": "gpital", "name": "Go Pull-It - Tallahassee",
                        "city": "Tallahassee", "state": "FL", "lat": 30.3870, "lng": -84.2752,
                        "source": "gopullit", "id_prefix": "gopullit-"},
    },
    # --- migrated from the retired ASP.NET hybrid adapter (2026-10-22) ---
    # source stays "chesterfield" so the zero-vehicle alarm keeps its own
    # label; id_prefix drops the location code because stock numbers are
    # chain-unique (verified: 2,240 stocks, 2,240 unique).
    "chesterfield_auto_parts": {
        "richmond": {"code": "cfrichmond", "name": "Chesterfield Auto Parts - Richmond",
                     "city": "Richmond", "state": "VA", "lat": 37.5067, "lng": -77.4912,
                     "source": "chesterfield", "id_prefix": "chesterfield-"},
        "southside": {"code": "cfsouthside", "name": "Chesterfield Auto Parts - Southside",
                      "city": "Midlothian", "state": "VA", "lat": 37.4367, "lng": -77.6046,
                      "source": "chesterfield", "id_prefix": "chesterfield-"},
        "fort_lee": {"code": "cffortlee", "name": "Chesterfield Auto Parts - Fort Lee",
                     "city": "Prince George", "state": "VA", "lat": 37.2465, "lng": -77.3674,
                     "source": "chesterfield", "id_prefix": "chesterfield-"},
    },
}


def _vinplus_search(tenant: str, make: str, location_id: str,
                    year_min: int | None = None, year_max: int | None = None,
                    depth: int = 0) -> list[dict]:
    """One searchVehicleHttp query; recursively bisect year ranges when the
    100-row cap is hit (cap responses have match_count == 100 exactly)."""
    time.sleep(VINPLUS_DELAY_SEC)
    try:
        r = requests.post(f"{VINPLUS_API}/searchVehicleHttp",
                          json={"yard_id": tenant, "make": make, "model": None,
                                "year_min": year_min, "year_max": year_max,
                                "location_id": location_id},
                          headers=HEADERS, timeout=60)
        r.raise_for_status()
        d = r.json()
    except Exception as e:
        print(f"  [VinPlus] {tenant}/{location_id} make {make!r} "
              f"({year_min}-{year_max}) fetch failed: {e}", file=sys.stderr)
        return []
    rows = d.get("matches") or []
    if len(rows) >= 100:
        y0 = year_min if year_min is not None else 1900
        y1 = year_max if year_max is not None else 2035
        if y1 > y0 and depth < 8:
            mid = (y0 + y1) // 2
            return (_vinplus_search(tenant, make, location_id, y0, mid, depth + 1)
                    + _vinplus_search(tenant, make, location_id, mid + 1, y1, depth + 1))
        print(f"  [VinPlus] {tenant}/{location_id} {make} {y0}-{y1}: still capped "
              f"at 100 on a leaf range — accepting partial", file=sys.stderr)
    return rows


def fetch_vinplus_inventory() -> list[dict]:
    """Fetch every VinPlus tenant's inventory (make x location loop)."""
    try:
        r = requests.get(f"{VINPLUS_API}/api/vehicle-groups", headers=HEADERS, timeout=60)
        r.raise_for_status()
        makes = sorted((r.json().get("data") or {}).keys())
    except Exception as e:
        print(f"  [VinPlus] vehicle-groups fetch failed: {e}", file=sys.stderr)
        return []
    if not makes:
        print("  [VinPlus] no makes in vehicle-groups — API changed?", file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    for tenant, locations in VINPLUS_TENANTS.items():
        for loc_id, yard in locations.items():
            loc_rows: list[dict] = []
            for make_name in makes:
                # Single-location tenants (locations: [] in yard-info) key
                # their one yard as "" here and search with location_id null.
                loc_rows.extend(_vinplus_search(tenant, make_name, loc_id or None))
            _indep_cache_raw(f"vinplus_{yard['code']}.json",
                             json.dumps(loc_rows).encode())
            id_prefix = yard.get("id_prefix") or f"vinplus-{yard['code']}-"
            for row in loc_rows:
                stock = str(row.get("stock") or "").strip()
                if not stock:
                    continue
                vin = str(row.get("vin") or "").strip().upper()
                date_s = str(row.get("dateAdded") or "")[:10]
                try:
                    year_i = int(row.get("year") or 0)
                except (TypeError, ValueError):
                    year_i = 0
                engine = str(row.get("engine") or "").strip()
                all_vehicles.append({
                    "id": f"{id_prefix}{stock.lower()}",
                    "vin": vin if len(vin) == 17 else "",
                    "year": year_i,
                    "make": _utpap_format_label(str(row.get("make") or "")),
                    "model": _utpap_format_label(str(row.get("model") or "")),
                    "row": str(row.get("vehicleRow") or "").strip(),
                    "dateAdded": date_s,
                    "_color": str(row.get("color") or "").strip().title(),
                    **({"_engine": engine} if engine else {}),
                    "_location": yard["name"],
                    "_city": yard["city"],
                    "_state": yard["state"],
                    "_lat": yard["lat"],
                    "_lng": yard["lng"],
                    "_source": yard.get("source", "vinplus"),
                })
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [VinPlus] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# 195 Used Auto Parts publishes a price list at /Home/PartPrices (their own
# site runs the CRUSH MVC app) — a clean 3-column table (name, $price, $core),
# ~700 rows. Chesterfield-style parse/output shape.
P195_PRICE_URL = "https://www.195usedautoparts.com/Home/PartPrices"
_P195_PRICE_ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>"
    r"\s*<td[^>]*>\s*\$?\s*([\d.,]+)\s*</td>",
    re.S,
)


def refresh_p195_pricing_file() -> Path:
    """Refresh 195 Used Auto Parts' price list -> p195_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "p195_pricing.json"
    try:
        r = requests.get(P195_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [195 pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for name_html, price, core in _P195_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", name_html)).strip()
        if not name or name.lower() in ("part", "part name", "part description"):
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [195 pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [195 pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# San Antonio Pick-N-Pull (Independent) publishes a price list at /price-list —
# ~980 rows of <span class="pl-part">/<span class="pl-desc"> (abbreviated +
# optional expanded name; the expanded one is kept when present) with
# td.pl-price / td.pl-core cells (core is an em-dash when absent).
PNPSA_PRICE_URL = "https://www.picknpullsa.com/price-list"
_PNPSA_PRICE_ROW_RE = re.compile(
    r'<span class="pl-part">(.*?)</span>\s*(?:<span class="pl-desc">(.*?)</span>)?'
    r'\s*</td>\s*<td class="pl-price">\s*\$?\s*([\d.,]+)\s*</td>'
    r'\s*<td class="pl-core[^"]*">\s*\$?\s*([\d.,]*)',
    re.S,
)


def refresh_pnpsa_pricing_file() -> Path:
    """Refresh San Antonio Pick-N-Pull's (independent) price list -> pnpsa_pricing.json."""
    import html as html_mod
    path = DATA_DIR / "pnpsa_pricing.json"
    try:
        r = requests.get(PNPSA_PRICE_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [PnPSA pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for short_html, desc_html, price, core in _PNPSA_PRICE_ROW_RE.findall(page):
        name = html_mod.unescape(re.sub(r"<[^>]+>", "", desc_html or short_html)).strip()
        if not name:
            continue
        try:
            price_f = float(price.replace(",", ""))
            core_f = float(core.replace(",", "")) if core else 0.0
        except ValueError:
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [PnPSA pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [PnPSA pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Nevada Pic-A-Part (nvpap.com) — 2-yard chain: Las Vegas (5100 N Lamb Blvd,
# North Las Vegas) + Henderson (110 W Rolly St). FIRST LAS VEGAS-METRO
# COVERAGE (~3,100 vehicles); user-requested by email 2026-10-17. WordPress
# with a custom "PT1" plugin exposing an unauthenticated WP REST search (same
# vendor family as U-Pull-R): POST /wp-json/pt1/v1/vehicle-stock with
# makes={Make}&models=0&years=0&beginDate=&store=0 returns BOTH yards per
# make. The response is a short numeric prefix then HTML — everything before
# the first '<' is stripped. Vehicle divs carry products-body-search__year /
# __model (combined "Subaru Legacy" — make prefix stripped per the upullr
# convention) / __row ("Row 706") / __store ("Las Vegas"|"Henderson") /
# __color / __stock / __date ("Oct 16, 2026" set date) plus data-pt1-vin and
# data-pt1-stock-number (chain-unique, L/H prefixed — the id basis). Make
# list: GET /json_datasets/vehicles_lookup_cache/Manufacturers.json (56).
# Parts price DB: /json_datasets/parts_database_en.json (533 rows:
# [id, name, price, tax, core, env, warranty, total, aliases, blurb]).
# robots.txt allow-all, no crawl-delay; ~57 requests/scan at 2s pacing.
# Coords geocoded once via Nominatim (exact house numbers resolved).
NVPAP_STOCK_URL = "https://www.nvpap.com/wp-json/pt1/v1/vehicle-stock"
NVPAP_MAKES_URL = "https://www.nvpap.com/json_datasets/vehicles_lookup_cache/Manufacturers.json"
NVPAP_DELAY_SEC = 2.0
NVPAP_HEADERS = {
    **HEADERS,
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.nvpap.com/",
    "Origin": "https://www.nvpap.com",
}
NVPAP_YARDS = {  # keyed by the __store display name
    "Las Vegas": {"name": "Nevada Pic-A-Part - Las Vegas", "city": "North Las Vegas",
                  "state": "NV", "lat": 36.2531, "lng": -115.0799},
    "Henderson": {"name": "Nevada Pic-A-Part - Henderson", "city": "Henderson",
                  "state": "NV", "lat": 36.0564, "lng": -115.0040},
}
_NVPAP_ITEM_RE = re.compile(
    r'<div class="products-body-search__item"[^>]*>(.*?)'
    r'(?=<div class="products-body-search__item"|$)', re.S)
_NVPAP_FIELD_RES = {
    "stock": re.compile(r'data-pt1-stock-number="([^"]+)"'),
    "year": re.compile(r'__year">\s*(\d+)\s*<'),
    "model": re.compile(r'__model">\s*([^<]+?)\s*<'),
    "row": re.compile(r'__row">(?:\s*<span>)?\s*([^<]*?)\s*(?:</span>)?\s*<'),
    "store": re.compile(r'__store">\s*([^<]+?)\s*<'),
    "color": re.compile(r'__color">(?:<span[^>]*>\s*</span>)?\s*([^<]*?)\s*<'),
    "vin": re.compile(r'data-pt1-vin="([^"]*)"'),
    "date": re.compile(r'__date">\s*([^<]+?)\s*<'),
}


def fetch_nvpap_inventory() -> list[dict]:
    """Fetch Nevada Pic-A-Part's 2-yard inventory (one REST POST per make)."""
    import html as html_mod
    try:
        r = requests.get(NVPAP_MAKES_URL, headers=HEADERS, timeout=60)
        r.raise_for_status()
        makes = [m.strip() for m in (r.json().get("manufacturers") or [])
                 if isinstance(m, str) and m.strip()]
    except Exception as e:
        print(f"  [Nevada Pic-A-Part] make-list fetch failed: {e}", file=sys.stderr)
        return []
    if not makes:
        print("  [Nevada Pic-A-Part] no makes parsed — site layout changed?",
              file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    unknown_stores: set[str] = set()
    for make_name in makes:
        time.sleep(NVPAP_DELAY_SEC)
        try:
            r = requests.post(NVPAP_STOCK_URL,
                              data={"makes": make_name, "models": "0", "years": "0",
                                    "beginDate": "", "store": "0"},
                              headers=NVPAP_HEADERS, timeout=60)
            r.raise_for_status()
            page = r.text
        except Exception as e:
            print(f"  [Nevada Pic-A-Part] make {make_name!r} fetch failed: {e}",
                  file=sys.stderr)
            continue
        lt = page.find("<")  # numeric result-count prefix before the HTML
        if lt < 0:
            continue
        page = page[lt:]
        for block in _NVPAP_ITEM_RE.findall(page):
            f = {k: (rx.search(block).group(1).strip() if rx.search(block) else "")
                 for k, rx in _NVPAP_FIELD_RES.items()}
            if not f["stock"] or not f["model"]:
                continue
            store = NVPAP_YARDS.get(f["store"])
            if store is None:
                unknown_stores.add(f["store"] or "?")
                continue
            model_s = html_mod.unescape(f["model"])
            if model_s.upper().startswith(make_name.upper() + " "):
                model_s = model_s[len(make_name):].strip()
            date_iso = ""
            try:
                date_iso = datetime.strptime(f["date"], "%b %d, %Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
            try:
                year_i = int(f["year"])
            except ValueError:
                year_i = 0
            vin = f["vin"].upper()
            all_vehicles.append({
                "id": f"nvpap-{f['stock'].lower()}",
                "vin": vin if len(vin) == 17 else "",
                "year": year_i,
                "make": _utpap_format_label(make_name),
                "model": _utpap_format_label(model_s),
                "row": re.sub(r"(?i)^row\s+", "", f["row"]),
                "dateAdded": date_iso,
                "_color": f["color"].title(),
                "_location": store["name"],
                "_city": store["city"],
                "_state": store["state"],
                "_lat": store["lat"],
                "_lng": store["lng"],
                "_source": "nvpap",
            })
    if unknown_stores:
        print(f"  [Nevada Pic-A-Part] skipped rows from unmapped store(s): "
              f"{sorted(unknown_stores)} — update NVPAP_YARDS/registry", file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Nevada Pic-A-Part] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Nevada Pic-A-Part publishes one chain-wide parts price database as JSON
# (the /auto-part-prices.html page renders it client-side). Row layout:
# [id, NAME, price, tax, core, env fee, warranty, total, aliases, blurb] —
# the component sums were verified against the published totals.
NVPAP_PARTS_URL = "https://www.nvpap.com/json_datasets/parts_database_en.json"


def refresh_nvpap_pricing_file() -> Path:
    """Refresh Nevada Pic-A-Part's parts price DB -> nvpap_pricing.json."""
    path = DATA_DIR / "nvpap_pricing.json"
    try:
        r = requests.get(NVPAP_PARTS_URL, headers=HEADERS, timeout=60)
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"  [Nevada Pic-A-Part pricing] fetch failed: {e} — keeping existing file",
              file=sys.stderr)
        return path
    seen: dict[str, dict] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, list) or len(row) < 8:
            continue
        name = str(row[1]).strip()
        if not name:
            continue
        try:
            price_f = float(row[2])
            core_f = float(row[4])
        except (TypeError, ValueError):
            continue
        if name not in seen:
            seen[name] = {
                "description": name,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Nevada Pic-A-Part pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Nevada Pic-A-Part pricing] only {len(seen)} parts parsed — "
              f"keeping existing file", file=sys.stderr)
    return path


# Pick-A-Part VA (pickapartva.com) — 2 yards: Fredericksburg (9001 Patriot
# Hwy, ~5,300 cards) + Stafford (164 Norman Rd, ~2,000), ~7,300 vehicles.
# WordPress + "iis-pro-upull" plugin; GET /inventory/ANY/ANY/?k=1&pagenum=N
# returns 500 server-rendered cards per page (~15 pages). Card fields:
# Stock (PAP######, the id basis), Year, Make/Model (combined, YardSmart
# style with the make often repeated — "SATURN SATURN S SERIES"), Vin,
# Location (Fredericksburg|Stafford), Row (often blank), Set Date (ISO).
# CLOUDFLARE: TLS-fingerprint challenge blocks plain requests (residential
# AND datacenter) — _papva_get() tries plain requests first (in case the WAF
# posture relaxes) then falls back to curl_cffi with impersonate="chrome"
# (lazy import; CI installs curl_cffi in scan.yml). This un-parks the chain
# registered as candidate on 2026-10-17. robots.txt: allow all (wp-admin
# excepted). ~16 requests/scan at 2s pacing. Both addresses geocode exactly.
PAPVA_PAGE_URL = "https://pickapartva.com/inventory/ANY/ANY/?k=1&pagenum={n}"
PAPVA_DELAY_SEC = 2.0
PAPVA_MAX_PAGES = 40
PAPVA_YARDS = {  # keyed by the card's Location value
    "Fredericksburg": {"name": "Pick-A-Part VA - Fredericksburg", "city": "Fredericksburg",
                       "state": "VA", "lat": 38.2714, "lng": -77.4927},
    "Stafford": {"name": "Pick-A-Part VA - Stafford", "city": "Stafford",
                 "state": "VA", "lat": 38.4612, "lng": -77.3635},
}
_PAPVA_CARD_RE = re.compile(
    r'<b>Stock:</b>\s*([^<]*)<br/>\s*<b>Year:</b>\s*([^<]*)<br/>\s*'
    r'<b>Make/Model :</b>\s*([^<]*)<br/>\s*<b>Vin :</b>\s*([^<]*)<br/>\s*'
    r'<b>Location: </b>\s*([^<]*)<br/>\s*<b>Row: </b>\s*([^<]*)<br/>'
    r'<b>Set Date: </b>\s*([^<]*)<br/>', re.S)
_PAPVA_TWO_WORD_MAKES = ("LAND ROVER", "ALFA ROMEO", "ASTON MARTIN")


def _papva_get(url: str) -> str | None:
    """GET through Cloudflare: plain requests first, curl_cffi fallback."""
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "text/html"}, timeout=60)
        r.raise_for_status()
        if "iis-uPull" in r.text or "car-details-uPull" in r.text:
            return r.text
    except Exception:
        pass
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        print("  [Pick-A-Part VA] plain fetch challenged and curl_cffi not "
              "installed — skipping", file=sys.stderr)
        return None
    try:
        r = cffi_requests.get(url, impersonate="chrome", timeout=60)
        if r.status_code == 200:
            return r.text
        print(f"  [Pick-A-Part VA] curl_cffi got HTTP {r.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  [Pick-A-Part VA] curl_cffi fetch failed: {e}", file=sys.stderr)
    return None


def fetch_papva_inventory() -> list[dict]:
    """Fetch Pick-A-Part VA's 2-yard inventory (paginated card deck)."""
    import html as html_mod
    all_vehicles: list[dict] = []
    unknown_locs: set[str] = set()
    for n in range(1, PAPVA_MAX_PAGES + 1):
        if n > 1:
            time.sleep(PAPVA_DELAY_SEC)
        page = _papva_get(PAPVA_PAGE_URL.format(n=n))
        if page is None:
            break
        cards = _PAPVA_CARD_RE.findall(page)
        if not cards:
            break
        if n == 1:
            _indep_cache_raw("papva_page1.html", page.encode())
        for stock_s, year_s, mm_s, vin_s, loc_s, row_s, date_s in cards:
            stock = stock_s.strip()
            mm = html_mod.unescape(mm_s).strip()
            if not stock or not mm:
                continue
            yard = PAPVA_YARDS.get(loc_s.strip())
            if yard is None:
                unknown_locs.add(loc_s.strip() or "?")
                continue
            mm_up = mm.upper()
            make_s = next((p for p in _PAPVA_TWO_WORD_MAKES if mm_up.startswith(p + " ")),
                          mm.split()[0])
            model_s = mm[len(make_s):].strip()
            if model_s.upper().startswith(make_s.upper() + " "):
                model_s = model_s[len(make_s):].strip()  # "SATURN SATURN S SERIES"
            vin = vin_s.strip().upper()
            try:
                year_i = int(year_s.strip())
            except ValueError:
                year_i = 0
            all_vehicles.append({
                "id": f"papva-{stock.lower()}",
                "vin": vin if len(vin) == 17 else "",
                "year": year_i,
                "make": _utpap_format_label(make_s),
                "model": _utpap_format_label(model_s),
                "row": row_s.strip(),
                "dateAdded": date_s.strip(),
                "_location": yard["name"],
                "_city": yard["city"],
                "_state": yard["state"],
                "_lat": yard["lat"],
                "_lng": yard["lng"],
                "_source": "papva",
            })
        if len(cards) < 500:  # short page = last page
            break
    if unknown_locs:
        print(f"  [Pick-A-Part VA] skipped cards from unmapped location(s): "
              f"{sorted(unknown_locs)}", file=sys.stderr)
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    if not unique:
        # CI gets HTTP 521 even through curl_cffi (2026-10-19 scan) while
        # residential works — same remedy as Ace: committed snapshot pushed
        # daily by scraper/update_papva_snapshot.sh (launchd).
        snap = Path(__file__).parent / "snapshots" / "papva_inventory.json.gz"
        if snap.exists():
            import gzip as gzip_mod
            try:
                data = json.loads(gzip_mod.decompress(snap.read_bytes()))
                unique = data.get("vehicles", [])
                print(f"  [Pick-A-Part VA] live crawl blocked — using committed snapshot "
                      f"({len(unique)} vehicles, fetched {data.get('fetched_at', '?')})",
                      file=sys.stderr)
            except Exception as e:
                print(f"  [Pick-A-Part VA] snapshot unreadable: {e}", file=sys.stderr)
    print(f"  [Pick-A-Part VA] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Go Pull-It (gopullit.com) — 4 yards: Jacksonville FL, Atlanta East
# (Norcross GA), Gainesville GA and Tallahassee FL (NEW with the migration).
# MIGRATED TO THE VINPLUS API (2026-10-22): the old WordPress crawl (hard
# 50-row cap, honored 10s crawl-delay, state-pruned rotation drill-down from
# the 2026-10-22 request-budget rework — ~45 min steady state, 30-50 min
# before) is retired. The chain is a VinPlus tenant (yard_id go_pull_it,
# sourceSystem crush) and one API pass serves all 4 locations in the shared
# VinPlus make x location loop. Verified before cutover: per-yard id overlap
# 99%+ (Jacksonville 2,269/2,276, Atlanta East 888/891, Gainesville 795/796)
# with the API seeing fresher arrivals, VINs on ~99% of rows, stock/date/row
# on 100%, and the SAME gopullit-{stock} id scheme (stocks GPI*/ATL*/GVL*/
# TAL* come straight from the API), so the app's tier-1 per-car links
# (gopullit.com/inventory/{stock}/ — verified live for GPI and TAL stocks)
# keep working. The drill-state machinery (GPI_STATE_FILE, rotation phases,
# docs/data/gopullit_state.json.gz, test_gopullit_state.py) went with it.
# See VINPLUS_TENANTS.


# U-Pick-It AZ (upickitaz.com) — 2 yards: Flagstaff (7320 Leupp Rd) +
# Prescott Valley (10440 E Valley Rd), ~2,900 vehicles. User-requested from
# Reddit (Flagstaff, zip 86015). WordPress + yardconnect-pro v2.3 plugin — a
# NEW plugin family over a YardSmart backend (photos on api.yardsmartapp.com;
# fingerprint for platform detection: wp-content/plugins/yardconnect-pro/).
# Mechanism: regex the nonce from `var yardconnectPublic = {... "nonce":...}`
# on any site page (even their 404 page carries it — don't raise on status),
# then ONE POST per lot to admin-ajax.php with
# action=yardconnect_search_vehicles&lot={Lot}&make=all&model=all&engine=&
# year_start=1949&year_end=2026&view=table. view=table is CRITICAL: it
# returns the whole lot unpaginated (1.5-2.8 MB fragment); grid view is
# paginated ~20/page. Columns: Image, Make, Model, Year, Color, Body Style,
# Engine, Yard Row, Date Set (MM/DD/YY). Stock number only exists on rows
# with photos (data-stock-number in the thumbnail cell; ~45% of rows) → ids
# are upickitaz-{stock} when present else the sha1-hash convention with
# ordinal dupe suffixes. No VIN anywhere. Expired nonce self-heals: HTTP 403
# returns JSON {data:{nonce:"<fresh>"}} — retry once with that. ~3 requests/
# scan. robots.txt explicitly allows admin-ajax.php. No parts price list
# found. Flagstaff's parcel is missing from OSM → Leupp Road centroid;
# Prescott Valley geocodes exactly.
UPICKIT_SITE = "https://upickitaz.com"
UPICKIT_AJAX = f"{UPICKIT_SITE}/wp-admin/admin-ajax.php"
UPICKIT_DELAY_SEC = 2.0
UPICKIT_YARDS = {  # keyed by the `lot` param value
    "Flagstaff": {"name": "U-Pick-It AZ - Flagstaff", "city": "Flagstaff",
                  "state": "AZ", "lat": 35.2872, "lng": -111.3546},
    "Prescott Valley": {"name": "U-Pick-It AZ - Prescott Valley", "city": "Prescott Valley",
                        "state": "AZ", "lat": 34.5836, "lng": -112.2791},
}
_UPICKIT_NONCE_RE = re.compile(r'yardconnectPublic\s*=\s*{[^}]*"nonce"\s*:\s*"([0-9a-f]+)"')
_UPICKIT_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_UPICKIT_STOCK_RE = re.compile(r'data-stock-number="([^"]+)"')


def fetch_upickitaz_inventory() -> list[dict]:
    """Fetch U-Pick-It AZ's 2-yard inventory (one table-view POST per lot)."""
    import hashlib
    import html as html_mod
    session = requests.Session()
    nonce = ""
    for path in ("/", "/inventory/"):
        try:
            r = session.get(UPICKIT_SITE + path, headers={**HEADERS, "Accept": "text/html"},
                            timeout=60)  # no raise_for_status: their 404 page has the nonce
            m = _UPICKIT_NONCE_RE.search(r.text)
            if m:
                nonce = m.group(1)
                break
        except Exception as e:
            print(f"  [U-Pick-It AZ] nonce page {path} fetch failed: {e}", file=sys.stderr)
    if not nonce:
        print("  [U-Pick-It AZ] no yardconnectPublic nonce found — plugin changed?",
              file=sys.stderr)
        return []

    all_vehicles: list[dict] = []
    dupes: dict[str, int] = {}
    for lot, yard in UPICKIT_YARDS.items():
        time.sleep(UPICKIT_DELAY_SEC)
        page = None
        for attempt in (1, 2):
            try:
                r = session.post(UPICKIT_AJAX,
                                 data={"action": "yardconnect_search_vehicles",
                                       "nonce": nonce, "lot": lot, "make": "all",
                                       "model": "all", "engine": "", "year_start": "1949",
                                       "year_end": "2026", "view": "table"},
                                 headers=HEADERS, timeout=120)
                if r.status_code == 403 and attempt == 1:
                    try:  # expired nonce self-heal: fresh one in the 403 body
                        nonce = r.json()["data"]["nonce"]
                        print("  [U-Pick-It AZ] nonce expired — retrying with fresh one",
                              file=sys.stderr)
                        continue
                    except Exception:
                        pass
                r.raise_for_status()
                page = r.text
            except Exception as e:
                print(f"  [U-Pick-It AZ] lot {lot!r} fetch failed: {e}", file=sys.stderr)
            break
        if page is None:
            continue
        _indep_cache_raw(f"upickitaz_{lot.split()[0].lower()}.html", page.encode())
        if "No vehicles found" in page:
            print(f"  [U-Pick-It AZ] lot {lot!r}: no vehicles", file=sys.stderr)
            continue
        for block in _UPICKIT_ROW_RE.findall(page):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            if len(cells) < 9:
                continue
            _, make_s, model_s, year_s, color_s, body_s, engine_s, row_s, date_s = cells[-9:]
            if not year_s.isdigit():  # header row
                continue
            date_iso = ""
            m = re.match(r"(\d{2})/(\d{2})/(\d{2})$", date_s)
            if m:
                date_iso = f"20{m.group(3)}-{m.group(1)}-{m.group(2)}"
            sm = _UPICKIT_STOCK_RE.search(block)
            if sm:
                vid = f"upickitaz-{sm.group(1).lower()}"
            else:  # ~55% of rows have no photo and no stock number
                basis = "|".join((lot, make_s, model_s, year_s, color_s, body_s,
                                  engine_s, row_s, date_s)).lower()
                vid = "upickitaz-" + hashlib.sha1(basis.encode()).hexdigest()[:12]
                n = dupes.get(vid, 0) + 1
                dupes[vid] = n
                if n > 1:
                    vid = f"{vid}-{n}"
            all_vehicles.append({
                "id": vid,
                "vin": "",
                "year": int(year_s),
                "make": _utpap_format_label(make_s),
                "model": _utpap_format_label(model_s),
                "row": re.sub(r"(?i)^yard\s+", "", row_s),
                "dateAdded": date_iso,
                "_color": color_s.title(),
                "_location": yard["name"],
                "_city": yard["city"],
                "_state": yard["state"],
                "_lat": yard["lat"],
                "_lng": yard["lng"],
                "_source": "upickitaz",
            })
    seen: set[str] = set()
    unique = [v for v in all_vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [U-Pick-It AZ] {len(unique)} vehicles across "
          f"{len({v['_location'] for v in unique})} yards", file=sys.stderr)
    return unique


# Barry's U Pull It (barrysupullit.net — NOTE: .com is a parked lander) —
# two physical yards (Mobile/Theodore AL at 5385 Barry Dr; Pass Christian MS
# at 8270 Firetower Rd) but ONE blended inventory: the entire site has a
# single /vehicle-inventory-2/ page server-rendering one <table id=
# "vehicles"> (~700 rows; Year, Make, Model, Engine, Color, VIN, Stock#,
# Row#, Arrival Date MM/DD/YY) with NO location column and no per-yard page
# (sitemap checked). Following the Parts Galore precedent the adapter maps
# everything to "Barry's U Pull It - Mobile" with a registry note; split if
# they ever expose per-yard inventory. Stock numbers (STK######) are the id
# basis. Indy-style one GET/scan. /part-pricing/ table (~425 parts: desc,
# price, unit, core) -> barrys_pricing.json. robots.txt: allow all. Neither
# parcel is in OSM → zip centroids (36582 Mobile; 39571 recorded in registry
# for the MS yard).
BARRYS_INVENTORY_URL = "https://barrysupullit.net/vehicle-inventory-2/"
BARRYS_PRICES_URL = "https://barrysupullit.net/part-pricing/"
BARRYS_YARD = {"name": "Barry's U Pull It - Mobile", "city": "Mobile",
               "state": "AL", "lat": 30.5391, "lng": -88.1828}
_BARRYS_TABLE_RE = re.compile(r'<table[^>]*id="vehicles"[^>]*>(.*?)</table>', re.S)
_BARRYS_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)


def fetch_barrys_inventory() -> list[dict]:
    """Fetch Barry's U Pull It's blended inventory (one server-rendered table)."""
    import hashlib
    import html as html_mod
    try:
        r = requests.get(BARRYS_INVENTORY_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=120)
        r.raise_for_status()
        page = r.text
    except Exception as e:
        print(f"  [Barry's] inventory fetch failed: {e}", file=sys.stderr)
        return []
    m = _BARRYS_TABLE_RE.search(page)
    if not m:
        print("  [Barry's] table#vehicles not found — site layout changed?", file=sys.stderr)
        return []
    _indep_cache_raw("barrys_inventory.html", page.encode())
    vehicles: list[dict] = []
    dupes: dict[str, int] = {}
    for block in _BARRYS_ROW_RE.findall(m.group(1)):
        cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _FENIX_TD_RE.findall(block)]
        if len(cells) < 9:
            continue
        year_s, make_s, model_s, engine_s, color_s, vin_s, stock_s, row_s, date_s = cells[:9]
        if not year_s.isdigit():
            continue
        date_iso = ""
        dm = re.match(r"(\d{2})/(\d{2})/(\d{2})$", date_s)
        if dm:
            date_iso = f"20{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
        stock = stock_s.strip()
        if stock:
            vid = f"barrys-{stock.lower()}"
        else:
            basis = "|".join((make_s, model_s, year_s, color_s, vin_s, row_s, date_s)).lower()
            vid = "barrys-" + hashlib.sha1(basis.encode()).hexdigest()[:12]
            n = dupes.get(vid, 0) + 1
            dupes[vid] = n
            if n > 1:
                vid = f"{vid}-{n}"
        vin = vin_s.strip().upper()
        vehicles.append({
            "id": vid,
            "vin": vin if len(vin) == 17 else "",
            "year": int(year_s),
            "make": _utpap_format_label(make_s),
            "model": _utpap_format_label(model_s),
            "row": row_s.strip(),
            "dateAdded": date_iso,
            "_color": color_s.title(),
            "_location": BARRYS_YARD["name"],
            "_city": BARRYS_YARD["city"],
            "_state": BARRYS_YARD["state"],
            "_lat": BARRYS_YARD["lat"],
            "_lng": BARRYS_YARD["lng"],
            "_source": "barrys",
        })
    seen: set[str] = set()
    unique = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Barry's] {len(unique)} vehicles", file=sys.stderr)
    return unique


# Barry's /part-pricing/ table ships a handful of TOOLS-section rows with the
# PRICE in the description cell (source HTML is literally
# <td>5.00</td><td>5.00</td><td>Each</td><td>0.00</td> — a data-entry hole on
# their site, not a parse slip). A price can never be a part name, so
# numeric/price-punctuation-only descriptions are dropped at parse time
# (2026-10-22; the frontend had been filtering them display-side since
# 535c604 — the data itself must be clean).
_PRICE_AS_NAME_RE = re.compile(r"^[\s\d.,$-]+$")


def _barrys_parse_pricing_rows(page: str) -> list[dict]:
    """Parse the /part-pricing/ HTML table into pricing entries, dropping
    rows whose description is a price-like string (no recoverable name)."""
    import html as html_mod
    seen: dict[str, dict] = {}
    dropped = 0
    for block in _BARRYS_ROW_RE.findall(page):
        cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _FENIX_TD_RE.findall(block)]
        if len(cells) < 4:
            continue
        desc, price_s, _unit, core_s = cells[:4]
        try:
            price_f = float(price_s.replace("$", "").replace(",", ""))
            core_f = float(core_s.replace("$", "").replace(",", "")) if core_s else 0.0
        except ValueError:
            continue
        if desc and _PRICE_AS_NAME_RE.match(desc):
            dropped += 1
            continue
        if desc and desc not in seen:
            seen[desc] = {
                "description": desc,
                "price": f"{price_f:.2f}",
                "corePrice": f"{core_f:.2f}",
                "totalPrice": f"{price_f + core_f:.2f}",
            }
    if dropped:
        print(f"  [Barry's pricing] dropped {dropped} row(s) with a price-like "
              f"description (source data-entry holes)", file=sys.stderr)
    return list(seen.values())


def refresh_barrys_pricing_file() -> Path:
    """Refresh Barry's U Pull It's /part-pricing/ table -> barrys_pricing.json."""
    path = DATA_DIR / "barrys_pricing.json"
    try:
        r = requests.get(BARRYS_PRICES_URL, headers={**HEADERS, "Accept": "text/html"},
                         timeout=60)
        r.raise_for_status()
    except Exception as e:
        print(f"  [Barry's pricing] fetch failed: {e} — keeping existing file", file=sys.stderr)
        return path
    parts = _barrys_parse_pricing_rows(r.text)
    seen = {p["description"]: p for p in parts}
    if len(seen) > 150:
        path.write_text(json.dumps(list(seen.values()), separators=(",", ":")))
        print(f"  [Barry's pricing] wrote {len(seen)} parts", file=sys.stderr)
    else:
        print(f"  [Barry's pricing] only {len(seen)} parts parsed — keeping existing file",
              file=sys.stderr)
    return path


# Prestige Pull-Your-Part (prestigepullyourpart.com) — single Houston TX yard
# (7615 E Mount Houston Rd, ~1,250 vehicles). WordPress running BOTH the
# gm_inventory_search family plugin AND a newer "art-inventory" plugin — the
# live search uses art-inventory: regex the nonce from
# `art_inventory_sf_ajax = {"url":..., "nonce":"..."}` on /vehicle-search/,
# then ONE POST to admin-ajax.php with action=art_inventory_get_yard_assets&
# security={nonce}&yard=0&make=0&model=0&year=0 → the ENTIRE yard as JSON
# ("0" params are the magic; named/empty values return []). Rows carry
# stock_number (PRE######, the id basis), iyear, make, model, vehicle_row,
# yard_date ("YYYY-MM-DD HH:MM:SS"), color, vin (often truncated — only
# 17-char values kept), yard_name/city/state. 2 requests/scan. robots.txt:
# allow all. Street geocodes to road centroid (parcel not in OSM).
PRESTIGE_SEARCH_URL = "https://prestigepullyourpart.com/vehicle-search/"
PRESTIGE_AJAX = "https://prestigepullyourpart.com/wp-admin/admin-ajax.php"
PRESTIGE_YARD = {"name": "Prestige Pull-Your-Part - Houston", "city": "Houston",
                 "state": "TX", "lat": 29.8912, "lng": -95.3000}
_PRESTIGE_NONCE_RE = re.compile(r'art_inventory_sf_ajax\s*=\s*{[^}]*"nonce":"([0-9a-f]+)"')


def fetch_prestige_inventory() -> list[dict]:
    """Fetch Prestige Pull-Your-Part's inventory (one all-yard JSON POST)."""
    session = requests.Session()
    try:
        r = session.get(PRESTIGE_SEARCH_URL, headers={**HEADERS, "Accept": "text/html"},
                        timeout=60)
        r.raise_for_status()
        m = _PRESTIGE_NONCE_RE.search(r.text)
        if not m:
            print("  [Prestige] art_inventory nonce not found — plugin changed?",
                  file=sys.stderr)
            return []
        nonce = m.group(1)
    except Exception as e:
        print(f"  [Prestige] search page fetch failed: {e}", file=sys.stderr)
        return []
    time.sleep(2)
    try:
        r = session.post(PRESTIGE_AJAX,
                         data={"action": "art_inventory_get_yard_assets",
                               "security": nonce, "yard": "0", "make": "0",
                               "model": "0", "year": "0"},
                         headers={**HEADERS, "Referer": PRESTIGE_SEARCH_URL}, timeout=120)
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"  [Prestige] yard-assets fetch failed: {e}", file=sys.stderr)
        return []
    if not isinstance(rows, list) or not rows:
        print("  [Prestige] yard-assets returned no rows", file=sys.stderr)
        return []
    _indep_cache_raw("prestige_assets.json", r.content)
    vehicles: list[dict] = []
    for row in rows:
        stock = str(row.get("stock_number") or "").strip()
        make_s = str(row.get("make") or "").strip()
        if not stock or not make_s:
            continue
        model_s = str(row.get("model") or "").strip()
        if model_s.upper().startswith(make_s.upper() + " "):
            model_s = model_s[len(make_s):].strip()
        vin = str(row.get("vin") or "").strip().upper()
        try:
            year_i = int(row.get("iyear") or 0)
        except (TypeError, ValueError):
            year_i = 0
        vehicles.append({
            "id": f"prestige-{stock.lower()}",
            "vin": vin if len(vin) == 17 else "",
            "year": year_i,
            "make": _utpap_format_label(make_s),
            "model": _utpap_format_label(model_s),
            "row": str(row.get("vehicle_row") or "").strip(),
            "dateAdded": str(row.get("yard_date") or "")[:10],
            "_color": str(row.get("color") or "").strip().title(),
            "_location": PRESTIGE_YARD["name"],
            "_city": PRESTIGE_YARD["city"],
            "_state": PRESTIGE_YARD["state"],
            "_lat": PRESTIGE_YARD["lat"],
            "_lng": PRESTIGE_YARD["lng"],
            "_source": "prestige",
        })
    seen: set[str] = set()
    unique = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Prestige] {len(unique)} vehicles", file=sys.stderr)
    return unique


# Budget U-Pull-It (FL) — owner-requested (Austin Rutherford email, Oct 2026:
# "all of our vehicle inventory and price lists are updated daily and
# published on our website"). TWO self-serve yards on TWO separate inventory
# systems (a third location, Auburndale, is full-service pre-pulled parts
# with no self-serve inventory — not listed):
#  - Winter Garden (881 S 9th St, 25 acres): budgetupullit.com, WordPress.
#    /current-inventory/?make={MAKE}&model= server-renders that make's full
#    list — make MUST be a specific make (empty/ALL return nothing), so one
#    GET per make (~40/scan), makes scraped from the page's own <select>.
#    Cells (quoted data-label): Year, Make, Model, Stock# (STK#####, the id
#    basis), Row, Vin, Date (DOT-separated MM.DD.YY — the /search-vehicles/
#    New Arrivals table uses slashes, this one uses dots). Pin from the
#    site's own footer map (parcel not in OSM; Census: no match).
#  - Bartow (2715 E State Rd 60, 12 acres): budgetupullit
#    .s3softwaresolutions.com/inventory.aspx — classic ASP.NET WebForms
#    postbacks (S3 Software Solutions; first of this platform here, linked
#    as the official inventory from budgetupullitbartow.com): GET for
#    VIEWSTATE + make list, __doPostBack ddlMake -> model list, postback
#    ddlModel -> rows (Year, Make, Model, Row #, Arrival Date MM/DD/YYYY).
#    Hidden fields re-chained from each response. NO stock# and NO VIN ->
#    sha1-hash ids with ordinal dupe suffixes (upickitaz convention).
#    1 + makes + Σmodels requests (~250-300/scan at 0.5s pacing). Pin from
#    the u-pull-it.com directory listing (parcel not in OSM).
# Both yards publish clean price lists (WG /used-car-part-prices/: PART
# DESCRIPTION/PRICE/PER/CORE; Bartow /partspricelist.aspx: Description/
# Price/Basis/Core, ~670 parts) -> budget_pricing.json keyed by yard display
# name (wap_pricing shape — the two lists differ). robots.txt:
# budgetupullit.com allow all (Yoast); s3softwaresolutions none (404);
# budgetupullitbartow.com allow all.
BUDGET_WG_SITE = "https://budgetupullit.com"
BUDGET_WG_INVENTORY_URL = f"{BUDGET_WG_SITE}/current-inventory/"
BUDGET_WG_PRICES_URL = f"{BUDGET_WG_SITE}/used-car-part-prices/"
BUDGET_BARTOW_INVENTORY_URL = "http://budgetupullit.s3softwaresolutions.com/inventory.aspx"
BUDGET_BARTOW_PRICES_URL = "http://budgetupullit.s3softwaresolutions.com/partspricelist.aspx"
BUDGET_WG_DELAY_SEC = 1.5
BUDGET_BARTOW_DELAY_SEC = 0.5
BUDGET_YARDS = {
    "wg": {"name": "Budget U-Pull-It - Winter Garden", "city": "Winter Garden",
           "state": "FL", "lat": 28.5539, "lng": -81.5750},
    "bartow": {"name": "Budget U-Pull-It - Bartow", "city": "Bartow",
               "state": "FL", "lat": 27.9031, "lng": -81.8087},
}
# WG's WordPress form: single-quoted option values in <select name="make">.
_BUDGET_WG_MAKE_SELECT_RE = re.compile(r'<select[^>]*name="make"[^>]*>(.*?)</select>', re.S)
_BUDGET_WG_OPTION_RE = re.compile(r"<option value='([^']*)'")
_BUDGET_WG_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
# Bartow's ASP.NET page: double-quoted everywhere.
_BUDGET_BARTOW_HIDDEN_RE = re.compile(
    r'<input type="hidden" name="(__[A-Z0-9]+)" id="[^"]*" value="([^"]*)"')
_BUDGET_BARTOW_SELECT_RE = r'<select[^>]*name="{name}"[^>]*>(.*?)</select>'
_BUDGET_BARTOW_OPTION_RE = re.compile(r'<option(?: selected="selected")? value="([^"]*)"')


def _budget_wg_vehicles(session: "requests.Session") -> list[dict]:
    """Winter Garden: one GET per make against /current-inventory/."""
    import html as html_mod
    yard = BUDGET_YARDS["wg"]
    try:
        r = session.get(BUDGET_WG_INVENTORY_URL, headers={**HEADERS, "Accept": "text/html"},
                        timeout=60)
        r.raise_for_status()
        m = _BUDGET_WG_MAKE_SELECT_RE.search(r.text)
        makes = _BUDGET_WG_OPTION_RE.findall(m.group(1)) if m else []
    except Exception as e:
        print(f"  [Budget WG] make-list fetch failed: {e}", file=sys.stderr)
        return []
    if not makes:
        print("  [Budget WG] no makes parsed from form — layout changed?", file=sys.stderr)
        return []
    vehicles: list[dict] = []
    for make_name in makes:
        time.sleep(BUDGET_WG_DELAY_SEC)
        try:
            r = session.get(BUDGET_WG_INVENTORY_URL,
                            params={"make": make_name, "model": ""},
                            headers={**HEADERS, "Accept": "text/html"}, timeout=90)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Budget WG] make {make_name!r} fetch failed: {e}", file=sys.stderr)
            continue
        _indep_cache_raw(f"budget_wg_{re.sub(r'[^A-Za-z0-9]+', '_', make_name)}.html",
                         r.content)
        for block in _BUDGET_WG_ROW_RE.findall(r.text):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            # Year, Make, Model, Stock#, Row#, VIN, Yard Date
            if len(cells) != 7 or not cells[0].isdigit():
                continue
            year_s, make_s, model_s, stock_s, row_s, vin_s, date_s = cells
            stock = stock_s.strip()
            if not stock:
                continue
            date_iso = ""
            dm = re.match(r"(\d{2})\.(\d{2})\.(\d{2})$", date_s)
            if dm:
                date_iso = f"20{dm.group(3)}-{dm.group(1)}-{dm.group(2)}"
            vin = vin_s.strip().upper()
            vehicles.append({
                "id": f"budget-{stock.lower()}",
                "vin": vin if len(vin) == 17 else "",
                "year": int(year_s),
                "make": _utpap_format_label(make_s),
                "model": _utpap_format_label(model_s),
                "row": row_s.strip(),
                "dateAdded": date_iso,
                "_location": yard["name"],
                "_city": yard["city"],
                "_state": yard["state"],
                "_lat": yard["lat"],
                "_lng": yard["lng"],
                "_source": "budget",
            })
    return vehicles


def _budget_bartow_options(page: str, name: str) -> list[str]:
    import html as html_mod
    m = re.search(_BUDGET_BARTOW_SELECT_RE.format(name=name), page, re.S)
    if not m:
        return []
    # unescape: "TOWN &amp; COUNTRY" must POST back as "TOWN & COUNTRY"
    # (the escaped form draws an HTTP 500 from the ASP.NET event validator)
    return [html_mod.unescape(v) for v in _BUDGET_BARTOW_OPTION_RE.findall(m.group(1))
            if v and not v.startswith("SELECT ")]


def _budget_bartow_vehicles(session: "requests.Session") -> list[dict]:
    """Bartow: ASP.NET make->model postback chain on s3softwaresolutions.com."""
    import hashlib
    import html as html_mod
    yard = BUDGET_YARDS["bartow"]

    def postback(page: str, target: str, make: str, model: str) -> str | None:
        data = dict(_BUDGET_BARTOW_HIDDEN_RE.findall(page))
        data.update({"__EVENTTARGET": target, "__EVENTARGUMENT": "", "__LASTFOCUS": "",
                     "ddlMake": make, "ddlModel": model})
        try:
            r = session.post(BUDGET_BARTOW_INVENTORY_URL, data=data,
                             headers={**HEADERS, "Accept": "text/html"}, timeout=60)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"  [Budget Bartow] postback {make}/{model} failed: {e}", file=sys.stderr)
            return None

    try:
        r = session.get(BUDGET_BARTOW_INVENTORY_URL,
                        headers={**HEADERS, "Accept": "text/html"}, timeout=60)
        r.raise_for_status()
        base = r.text
    except Exception as e:
        print(f"  [Budget Bartow] inventory.aspx fetch failed: {e}", file=sys.stderr)
        return []
    _indep_cache_raw("budget_bartow_base.html", base.encode())
    makes = _budget_bartow_options(base, "ddlMake")
    if not makes:
        print("  [Budget Bartow] no makes in ddlMake — page changed?", file=sys.stderr)
        return []
    vehicles: list[dict] = []
    dupes: dict[str, int] = {}
    for make_name in makes:
        time.sleep(BUDGET_BARTOW_DELAY_SEC)
        make_page = postback(base, "ddlMake", make_name, "SELECT MODEL")
        if make_page is None:
            continue
        page = make_page
        for model_name in _budget_bartow_options(make_page, "ddlModel"):
            time.sleep(BUDGET_BARTOW_DELAY_SEC)
            resp = postback(page, "ddlModel", make_name, model_name)
            if resp is None:
                continue
            page = resp  # re-chain VIEWSTATE from the latest response
            for block in _BUDGET_WG_ROW_RE.findall(resp):
                cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                         for c in _FENIX_TD_RE.findall(block)]
                # Year, Make, Model, Row #, Arrival Date — no stock#, no VIN
                if len(cells) != 5 or not cells[0].isdigit():
                    continue
                year_s, make_s, model_s, row_s, date_s = cells
                date_iso = ""
                dm = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", date_s)
                if dm:
                    date_iso = f"{dm.group(3)}-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}"
                basis = "|".join(("bartow", make_s, model_s, year_s, row_s, date_s)).lower()
                vid = "budget-bartow-" + hashlib.sha1(basis.encode()).hexdigest()[:12]
                n = dupes.get(vid, 0) + 1
                dupes[vid] = n
                if n > 1:
                    vid = f"{vid}-{n}"
                vehicles.append({
                    "id": vid,
                    "vin": "",
                    "year": int(year_s),
                    "make": _utpap_format_label(make_s),
                    "model": _utpap_format_label(model_s),
                    "row": row_s.strip(),
                    "dateAdded": date_iso,
                    "_location": yard["name"],
                    "_city": yard["city"],
                    "_state": yard["state"],
                    "_lat": yard["lat"],
                    "_lng": yard["lng"],
                    "_source": "budget",
                })
    return vehicles


def fetch_budget_inventory() -> list[dict]:
    """Fetch Budget U-Pull-It's two FL yards (separate inventory systems)."""
    session = requests.Session()
    vehicles = _budget_wg_vehicles(session)
    n_wg = len(vehicles)
    time.sleep(2)
    vehicles += _budget_bartow_vehicles(session)
    seen: set[str] = set()
    unique = [v for v in vehicles if not (v["id"] in seen or seen.add(v["id"]))]
    print(f"  [Budget U-Pull-It] {len(unique)} vehicles "
          f"(Winter Garden {n_wg}, Bartow {len(unique) - n_wg})", file=sys.stderr)
    return unique


def refresh_budget_pricing_file() -> Path:
    """Both Budget U-Pull-It price lists -> budget_pricing.json, keyed by yard
    display name (wap_pricing shape — WG and Bartow lists differ)."""
    import html as html_mod
    path = DATA_DIR / "budget_pricing.json"
    out: dict[str, dict] = {}
    for slug, url in (("wg", BUDGET_WG_PRICES_URL), ("bartow", BUDGET_BARTOW_PRICES_URL)):
        yard_name = BUDGET_YARDS[slug]["name"]
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "text/html"}, timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"  [Budget pricing] {yard_name}: {e}", file=sys.stderr)
            continue
        prices: dict[str, dict] = {}
        for block in _BUDGET_WG_ROW_RE.findall(r.text):
            cells = [html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in _FENIX_TD_RE.findall(block)]
            # WG: PART DESCRIPTION, PRICE, PER, CORE; Bartow: Description,
            # Price, Basis, Core ("$40.00" style) — same 4-cell shape.
            if len(cells) < 4:
                continue
            desc, price_s, _unit, core_s = cells[:4]
            if not desc or desc in (".", "Description", "PART DESCRIPTION") or desc in prices:
                continue
            try:
                price_f = float(price_s.replace("$", "").replace(",", ""))
                core_f = float(core_s.replace("$", "").replace(",", "")) if core_s else 0.0
            except ValueError:
                continue
            prices[desc] = {"price": price_f, "core": core_f}
        if len(prices) > 150:
            out[yard_name] = prices
        else:
            print(f"  [Budget pricing] {yard_name}: only {len(prices)} parts parsed — "
                  f"skipping this yard's list", file=sys.stderr)
        time.sleep(1)
    if len(out) == len(BUDGET_YARDS):
        path.write_text(json.dumps(out, separators=(",", ":")))
        print(f"  [Budget pricing] wrote {sum(len(v) for v in out.values())} parts "
              f"across {len(out)} yards", file=sys.stderr)
    else:
        print(f"  [Budget pricing] only {len(out)}/{len(BUDGET_YARDS)} yards parsed — "
              f"keeping existing file", file=sys.stderr)
    return path


# Chains the scan EXPECTS to return vehicles (source tag -> display name).
# After the U-Pull-R plugin upgrade silently zeroed all MN/OH coverage for 4
# days (2026-10-13 → 10-17), any onboarded chain coming back empty now prints
# a prominent warning in the scan log.
INDEPENDENT_EXPECTED_SOURCES = {
    "wrenchapart": "Wrench-A-Part",
    "upullr": "U-Pull-R Parts",
    "fenix": "Fenix U-Pull",
    "harrys": "Harry's U-Pull-It",
    "indy": "Indy-U-Pull-It",
    "upullitne": "U-Pull-It (IA/NE)",
    "ruperts": "Rupert's U-Pull-It",
    "pns": "Pull-N-Save",
    "partsgalore": "Parts Galore",
    "chesterfield": "Chesterfield Auto Parts",
    "ace": "Ace Pick-A-Part",
    "sturtevant": "Sturtevant Auto",
    "ipull": "iPull-uPull",
    "stcloud": "St. Cloud U Pull",
    "nvpap": "Nevada Pic-A-Part",
    "vinplus": "VinPlus (RTP KY/TN/NC, Pickers TX/AR/LA, Joliet IL, "
               "San Antonio PnP TX, 195 TX, Pick Ur Part TX)",
    "papva": "Pick-A-Part VA",
    "upickitaz": "U-Pick-It AZ",
    "gopullit": "Go Pull-It",
    "barrys": "Barry's U Pull It",
    "prestige": "Prestige Pull-Your-Part",
    "budget": "Budget U-Pull-It (FL)",
}


# Canonical adapter order. The parallel fetch below concatenates results in
# THIS order, so the combined vehicle list (and therefore the saved payload's
# row order) is byte-identical to what the old sequential loop produced.
INDEPENDENT_FETCHERS: list = [
    ("Wrench-A-Part", fetch_wrenchapart_inventory),
    ("U-Pull-R", fetch_upullr_inventory),
    ("Fenix", fetch_fenix_inventory),
    ("Harry's", fetch_harrys_inventory),
    ("Indy", fetch_indyupullit_inventory),
    ("U-Pull-It IA/NE", fetch_upullitne_inventory),
    ("Rupert's", fetch_ruperts_inventory),
    ("Pull-N-Save", fetch_pns_inventory),
    ("Parts Galore", fetch_partsgalore_inventory),
    ("Ace", fetch_ace_inventory),
    ("Sturtevant", fetch_sturtevant_inventory),
    ("iPull-uPull", fetch_ipull_inventory),
    ("St. Cloud", fetch_stcloud_inventory),
    ("Nevada Pic-A-Part", fetch_nvpap_inventory),
    ("VinPlus", fetch_vinplus_inventory),
    ("Pick-A-Part VA", fetch_papva_inventory),
    ("U-Pick-It AZ", fetch_upickitaz_inventory),
    ("Barry's", fetch_barrys_inventory),
    ("Prestige", fetch_prestige_inventory),
    ("Budget U-Pull-It", fetch_budget_inventory),
]


def fetch_independent_inventory() -> list[dict]:
    """All enabled independent-yard adapters (registry status: adapter-built).

    Adapters run CONCURRENTLY (2026-10-22): the sequential loop made the
    independents the dominant term in scan wall-clock (~3h of a ~3.2h scan)
    even though every adapter talks to a DIFFERENT host. Each adapter stays
    strictly sequential INSIDE (its per-host *_DELAY_SEC politeness is
    untouched; VinPlus, the only adapter whose yards share one API host,
    was already serial internally), so no single yard's site ever sees
    concurrent requests from us — we only overlap waits across hosts.
    The old inter-adapter 2s courtesy sleeps were cross-host cadence and are
    meaningless once adapters overlap, so they're gone.

    An adapter that raises still aborts the scan, exactly like the
    sequential version did (fetch errors are caught inside each adapter;
    an uncaught exception means a bug worth failing loudly on)."""
    workers = max(1, int(os.environ.get(
        "INDEP_FETCH_WORKERS", str(len(INDEPENDENT_FETCHERS)))))
    results: list[list[dict] | None] = [None] * len(INDEPENDENT_FETCHERS)
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="indep") as pool:
        futs = {pool.submit(fn): i for i, (_label, fn) in enumerate(INDEPENDENT_FETCHERS)}
        for fut in concurrent.futures.as_completed(futs):
            results[futs[fut]] = fut.result()
    vehicles: list[dict] = []
    for rows in results:
        vehicles += rows or []

    # Loud zero-vehicle alarm: a chain that silently returns [] (WAF change,
    # plugin upgrade, layout change) must be visible in the scan log, not
    # discovered by users days later (see U-Pull-R, 2026-10-13..17).
    got_sources = {v.get("_source") for v in vehicles}
    for src, label in INDEPENDENT_EXPECTED_SOURCES.items():
        if src not in got_sources:
            print(f"  WARNING: independent chain {label!r} returned 0 vehicles — "
                  f"adapter broken or site blocking? Investigate before it goes stale.",
                  file=sys.stderr)
    return vehicles


def _vpic_mismatch_msg(v: dict, vin_dec: dict | None) -> str | None:
    """Cross-check the VIN's factory decode against the yard listing.

    The yard listing is what a visitor sees on the lot sign, so we never
    silently override it — but when the VIN clearly disagrees, the VIN wins
    for matching and the discrepancy is flagged in the data. Conservative on
    purpose: only year (exact int compare) and make (no substring relation
    either way) are checked; model strings vary too much across feeds to
    compare without false alarms."""
    if not vin_dec:
        return None
    msgs = []
    try:
        vin_year = int(vin_dec.get("modelYear") or 0)
    except (TypeError, ValueError):
        vin_year = 0
    listed_year = v.get("year") or 0
    if vin_year and listed_year and vin_year != listed_year:
        msgs.append(f"VIN decodes as {vin_year} (listed {listed_year})")
    vin_make = (vin_dec.get("make") or "").strip().lower()
    listed_make = (v.get("make") or "").strip().lower()
    if vin_make and listed_make and vin_make not in listed_make and listed_make not in vin_make:
        # NHTSA reports some sub-brands under the parent make (e.g. every Scion
        # VIN decodes as make "Toyota"). Same company, correctly-labeled lot
        # sign — not a mismatch.
        _BRAND_FAMILIES = [
            {"scion", "toyota"}, {"datsun", "nissan"}, {"geo", "chevrolet"},
            {"ram", "dodge"}, {"genesis", "hyundai"}, {"plymouth", "chrysler"},
            {"eagle", "chrysler"}, {"saturn", "chevrolet"},
        ]
        same_family = any(vin_make in fam and listed_make in fam for fam in _BRAND_FAMILIES)
        if not same_family:
            msgs.append(f"VIN decodes as {(vin_dec.get('make') or '').title()} (listed {v.get('make')})")
    return "; ".join(msgs) or None


# ---------------------------------------------------------------------------
# Model-name normalization. Yard feeds spell the same model many ways
# ("F150"/"F-150", "4 Runner"/"4Runner", "EDGE"/"Edge", "Es300"/"ES 300").
# Distinct spellings split the UI's model dropdown into duplicate entries and
# can miss UNOBTANIUM_DB keyword matches outright ("toyota 4 runner" never
# contains "4runner"). Canonical spelling is applied once at scan time.
# Table generated from a collision audit of the live inventory (2026-09-12),
# keyed by squashed lowercase alphanumerics, hand-corrected to brand styling.
# ---------------------------------------------------------------------------
_MODEL_CANON = {
    "1series": "1 Series", "3series": "3 Series", "5series": "5 Series",
    "6series": "6 Series", "7series": "7 Series",
    "200sx": "200SX", "280zx": "280ZX", "300zx": "300ZX", "3000gt": "3000GT",
    "4runner": "4Runner", "aura": "Aura", "aveo": "Aveo",
    "b3000": "B3000", "b4000": "B4000", "baja": "Baja", "broncoii": "Bronco II",
    "chevyvan": "Chevy Van", "clclass": "CL-Class", "clkclass": "CLK-Class",
    "clsclass": "CLS-Class", "glclass": "GL-Class", "glkclass": "GLK-Class",
    "slclass": "SL-Class",
    "crv": "CR-V", "ct200h": "CT 200h", "cts": "CTS", "cube": "Cube",
    "cx7": "CX-7", "cx9": "CX-9", "dart": "Dart", "dts": "DTS",
    "echo": "Echo", "edge": "Edge", "eightyeight": "Eighty-Eight",
    "elantragt": "Elantra GT", "eos": "Eos", "escaladeext": "Escalade EXT",
    "fit": "Fit", "fjcruiser": "FJ Cruiser", "flex": "Flex", "fox": "Fox",
    "fx35": "FX35", "golf": "Golf", "golfiii": "Golf III", "gs450h": "GS 450h",
    "hhr": "HHR", "hs250h": "HS 250h", "ion": "ION", "jettaiii": "Jetta III",
    "juke": "Juke", "leaf": "Leaf", "lebaron": "LeBaron", "lseries": "L-Series",
    "ltdcrownvictoria": "LTD Crown Victoria", "luminaapv": "Lumina APV",
    "luv": "LUV", "marklt": "Mark LT", "markvi": "Mark VI",
    "markvii": "Mark VII", "markviii": "Mark VIII", "mazdaspeed3": "Mazdaspeed3",
    "mdx": "MDX", "mkx": "MKX", "mkz": "MKZ", "mkzhybrid": "MKZ Hybrid",
    "montanasv6": "Montana SV6", "mpv": "MPV", "mx5miata": "MX-5 Miata",
    "neon": "Neon", "ninetyeight": "Ninety-Eight", "nova": "Nova",
    "nv2500": "NV2500", "ptcruiser": "PT Cruiser", "pulsarnx": "Pulsar NX",
    "ramcharger": "Ramcharger", "rav4": "RAV4", "reno": "Reno",
    "rio": "Rio", "rio5": "Rio5", "rx400h": "RX 400h",
    "s10": "S-10", "s10blazer": "S-10 Blazer", "s15": "S-15",
    "s15jimmy": "S-15 Jimmy",
    "sierra1500hd": "Sierra 1500HD", "sierra2500hd": "Sierra 2500HD",
    "sierra3500hd": "Sierra 3500HD", "silverado2500hd": "Silverado 2500HD",
    "silverado2500hdclassic": "Silverado 2500HD Classic",
    "silverado3500hd": "Silverado 3500HD",
    "sl2": "SL2", "soul": "Soul", "sportvan": "Sportvan", "srx": "SRX",
    "sseries": "S-Series", "stype": "S-Type", "swift": "Swift",
    "sx4crossover": "SX4 Crossover", "t100": "T100",
    "tc": "tC", "xa": "xA", "xb": "xB", "xd": "xD",
    "tl": "TL", "towncar": "Town Car", "trax": "Trax", "trooperii": "Trooper II",
    "tsx": "TSX", "tt": "TT", "van": "Van", "vibe": "Vibe", "volt": "Volt",
    "vue": "VUE", "xg300": "XG300", "xg350": "XG350",
    "xj12": "XJ12", "xjseries": "XJ-Series",
    "xkseries": "XK-Series", "xl7": "XL-7", "xtype": "X-Type",
    "yukonxl": "Yukon XL",
}

# --- 2026-10 model-name merge (owner-reported: BMW filter showed '328' next
# to '328i', '330I' vs '330i', a 919-car '3 Series' blob; every make audited).
#
# _MODEL_CANON_BY_MAKE: evidence-driven per-make canon table, generated from a
# collision audit of the full live inventory (2026-10-22, 2,388 distinct
# (make, model) pairs), hand-corrected to each marque's real styling. Keys are
# squashed lowercase alphanumerics of the model (same keying as _MODEL_CANON),
# outer keys are squashed canonical make names. Consulted BEFORE the global
# table so make-specific meanings win ('ls' is Lincoln 'LS').
#
# Merge policy (mirrors the 2026-10 make merge): merge only provable spelling/
# case/suffix variants of the SAME car — per-chain body suffixes ("S10
# Pickup"), Chrysler-family platform codes ("Charger Lc", "Sebring Jr"),
# redundant trim junk ("Aura Xe"), word-order flips ("Silverado Classic
# 1500"). Genuinely distinct trims stay separate: 328i ≠ 328is ≠ 328ci ≠
# 328xi ≠ 323iC, F-250 ≠ F-250 Super Duty, Malibu ≠ Malibu Limited (a real
# fleet continuation model), Armada ≠ Pathfinder Armada (official early name),
# A4 ≠ A4 Quattro. When unsure, keep separate.
_MODEL_CANON_BY_MAKE: dict[str, dict[str, str]] = {
    "acura": {"cl": "CL", "rl": "RL", "rdx": "RDX"},
    "audi": {"ttquattro": "TT Quattro"},
    "bmw": {
        # 525iA/530iA are 525i/530i automatics (feed + NHTSA use the trans
        # marker); not a distinct model, unlike is/ci/xi body/drive variants.
        "525ia": "525i", "530ia": "530i",
        "activehybrid3": "ActiveHybrid 3", "activehybrid5": "ActiveHybrid 5",
        "i3": "i3", "428igrancoupe": "428i Gran Coupe",
        "alpinab7xdrive": "Alpina B7 xDrive",
        "alpinab7lxdrive": "Alpina B7L xDrive",
    },
    "buick": {
        "lesabre": "LeSabre", "lacrosse": "LaCrosse", "encoregx": "Encore GX",
        "rendezvoussrv": "Rendezvous",  # SRV = chain body code, not a trim
    },
    "cadillac": {
        "deville": "DeVille", "coupedeville": "Coupe DeVille",
        "eldorado": "Eldorado",  # catches 'El Dorado'
        "sts": "STS", "xts": "XTS", "ctsv": "CTS-V", "elr": "ELR",
        "escaladeesv": "Escalade ESV",
    },
    "chevrolet": {
        "s10pickup": "S-10", "s10pu": "S-10", "c10": "C10",
        "c10pickup": "C10", "belair": "Bel Air", "vega": "Vega",
        "trailblazerext": "Trailblazer EXT",
        "blazers10jimmys15": "Blazer S10/Jimmy S15",
        "s10s15sonoma": "S10/S15/Sonoma",
        "silverado1500hd": "Silverado 1500HD",
        "silveradohd2500": "Silverado 2500HD",
        "silveradoclassic1500": "Silverado 1500 Classic",   # word-order flip
        "silveradoclassic": "Silverado Classic",
        "astrovan": "Astro", "chevyvanclassic": "Chevy Van",
        "luminacar": "Lumina", "luminavan": "Lumina APV",
        "luminaminivan": "Lumina APV", "ventureapv": "Venture",
        "sparkev": "Spark EV", "boltev": "Bolt EV",
        "cityexpressls": "City Express", "geoprizm": "Prizm",
        "ck1500series": "C/K 1500", "ck2500series": "C/K 2500",
        "ck3500series": "C/K 3500", "ck10series": "C/K 10",
        "ck20series": "C/K 20", "ck30series": "C/K 30",
        "rv20series": "R/V 20", "gseriesvan": "G-Series",
        "c15c1500pickup": "C1500", "c3500hd": "C3500HD",
        "c20truck": "C20", "c30pickup": "C30",
    },
    "chrysler": {
        # 'TOWN &amp; COUNTRY' unescapes to 'Town & Country' whose squashed
        # key is 'towncountry'; 'Town And Country' squashes to the long key.
        "towncountry": "Town & Country", "townandcountry": "Town & Country",
        "townandcountryrs": "Town & Country", "townandcountryrt": "Town & Country",
        # Trailing Lx/Js/Jr/... are Chrysler internal platform codes some
        # chains append; the base nameplate is the model. '300 Lh' deliberately
        # NOT merged ('300' didn't exist in the LH era — likely a mislabeled
        # 300M; ambiguous, keep).
        "300lx": "300", "300clx": "300C", "300m": "300M",
        "200js": "200", "200uf": "200", "200lx": "200",
        "sebringjr": "Sebring", "sebringjs": "Sebring",
        "pacificacs": "Pacifica", "ptcruiserpt": "PT Cruiser",
        "aspenhg": "Aspen", "concordelh": "Concorde",
        "crossfirezh": "Crossfire", "voyagerrs": "Voyager",
        "lhslh": "LHS", "lhs": "LHS",
        "tcbymaserati": "TC By Maserati", "tcmaserati": "TC By Maserati",
    },
    "dodge": {
        "ram": "Ram",            # display casing for unresolved 'RAM' rows
        "ram50": "Ram 50",
        "chargerlc": "Charger", "chargerlx": "Charger",
        "challengerla": "Challenger", "challengerlc": "Challenger",
        "avengerjs": "Avenger", "dakotand": "Dakota", "dakotaan": "Dakota",
        "caliberpm": "Caliber", "journeyjc": "Journey",
        "durangohb": "Durango", "durangodn": "Durango",
        "neonpl": "Neon", "dartpf": "Dart",
        "stratusjr": "Stratus", "stratusja": "Stratus",
        "magnumlx": "Magnum", "nitroka": "Nitro", "intrepidlh": "Intrepid",
        "grandcaravanrs": "Grand Caravan", "grandcaravanrt": "Grand Caravan",
        "caravanrs": "Caravan",
        "caravangrandcaravanrs": "Caravan/Grand Caravan",
        "neonsrt4": "Neon SRT-4",
        "d150pickup": "D150", "d100pickup": "D100", "pud250": "D250",
        "w100pickup": "W100", "w150pickup": "W150", "w200pickup": "W200",
        "w250pickup": "W250", "w350pickup": "W350",
        "ram1500van": "Ram Van 1500", "ram2500van": "Ram Van 2500",
        "ram3500van": "Ram Van 3500",
    },
    "ford": {
        "f250sd": "F-250 Super Duty", "f350sd": "F-350 Super Duty",
        "f450sd": "F-450 Super Duty",
        "escapexlt": "Escape", "escapexls": "Escape",
        "escapelimited": "Escape",       # trim, not a continuation model
        "ecosportse": "Ecosport", "ecosportses": "Ecosport",
        "expeditionel": "Expedition EL", "expeditionmax": "Expedition MAX",
        "focussvt": "Focus SVT", "escortzx2": "Escort ZX2",
        "cmax": "C-Max", "cmaxhybrid": "C-Max Hybrid",
        "cmaxenergi": "C-Max Energi",
        "transit150": "Transit-150", "transit250": "Transit-250",
        "transit350": "Transit-350", "transit350hd": "Transit-350 HD",
        "f100truck": "F-100", "f100pickup": "F-100",
    },
    "gmc": {
        "sierra1500pickup": "Sierra 1500", "sierra2500pickup": "Sierra 2500",
        "sierrack1500": "Sierra 1500", "sierrack2500": "Sierra 2500",
        "sierrack3500": "Sierra 3500",
        "savana1500van": "Savana 1500", "savana2500van": "Savana 2500",
        "savana3500van": "Savana 3500",
        "jimmys15": "S-15 Jimmy", "s15pickup": "S-15",
        "s15utility": "S-15 Jimmy", "jimmyutility": "Jimmy",
        "safarigmc": "Safari", "c3500hd": "C3500HD",
        "ck1500series": "C/K 1500", "ck2500series": "C/K 2500",
        "c15c1500pickup": "C1500",
        "blazers10jimmys15": "Blazer S10/Jimmy S15",
        "s10s15sonoma": "S10/S15/Sonoma",
        "yukonxl1500": "Yukon XL 1500", "yukonxl2500": "Yukon XL 2500",
    },
    "honda": {"civiccrx": "CRX", "cbr600": "CBR600"},
    "hyundai": {"kona": "Kona", "santafexl": "Santa Fe XL"},
    "infiniti": {
        "qx41999": "QX4", "m35h": "M35h", "qx60hybrid": "QX60 Hybrid",
        "fxseries": "FX Series",
    },
    "isuzu": {"isuzupuppickup": "Pup", "trooperii": "Trooper II"},
    "jaguar": {
        "xf": "XF", "xj": "XJ", "xj6": "XJ6", "xjs": "XJS",
        "xjsedan": "XJ", "xk8": "XK8",
    },
    "jeep": {
        "libertykj": "Liberty", "libertykk": "Liberty",
        "grandcherokeewk": "Grand Cherokee", "grandcherokeewj": "Grand Cherokee",
        "patriotmk": "Patriot", "compassmk": "Compass",
        "commanderxh": "Commander", "commanderxk": "Commander",
        "cherokeekl": "Cherokee", "cherokeexj": "Cherokee",
        "wranglerjk": "Wrangler", "cj7": "CJ7", "cj5": "CJ5",
        "pucomanche": "Comanche", "j10pickup": "J10",
    },
    "kia": {
        "niro": "Niro", "soulev": "Soul EV",
        "rio5door": "Rio5", "riocinco": "Rio5", "forte5door": "Forte5",
    },
    "landrover": {
        "rangesport": "Range Rover Sport",
        "evoque": "Range Rover Evoque",
        "discoveryii": "Discovery Series II",
        "discoveryseriesii": "Discovery Series II",
        "lr2": "LR2", "lr3": "LR3", "lr4": "LR4",
    },
    "lexus": {"ls600hl": "LS 600h L", "scseries": "SC Series"},
    "lincoln": {"ls": "LS", "mks": "MKS", "mkt": "MKT", "mark": "Mark"},
    "mazda": {
        # Bare numbers under make Mazda are unambiguous ('3' is a Mazda3).
        "3": "Mazda3", "6": "Mazda6", "5": "Mazda5", "2": "Mazda2",
        "b2000": "B2000", "b2200": "B2200", "b2300": "B2300",
        "b2500": "B2500", "b2600": "B2600",
        "rx8": "RX-8", "rx7": "RX-7", "mx6": "MX-6", "mx3": "MX-3",
        "cx3": "CX-3", "cx5": "CX-5", "cx30": "CX-30", "cx50": "CX-50",
        "miata": "MX-5 Miata", "mx5": "MX-5 Miata",
        "mazdaspeed6": "Mazdaspeed6",
        "tributelx": "Tribute", "tributedx": "Tribute", "tributees": "Tribute",
    },
    "mercedesbenz": {
        "aclass": "A-Class", "bclass": "B-Class", "cclass": "C-Class",
        "eclass": "E-Class", "sclass": "S-Class", "rclass": "R-Class",
        "mclass": "M-Class", "slkclass": "SLK-Class",
        "mlclass": "M-Class", "claclass": "CLA-Class", "glaclass": "GLA-Class",
        "glcclass": "GLC-Class", "gleclass": "GLE-Class",
        "clk": "CLK", "slk": "SLK", "cls": "CLS", "sl": "SL", "gl": "GL",
        "cla": "CLA", "gla": "GLA", "glc": "GLC", "gls": "GLS", "slc": "SLC",
        "smartsmart": "Smart",
    },
    "mini": {
        "minicooper": "Cooper",
        "cooperclubman": "Clubman", "coopercountryman": "Countryman",
        "cooperpaceman": "Paceman", "cooperconvertible": "Convertible",
        "cooperhardtop": "Hardtop",
    },
    "mitsubishi": {
        "raidernm": "Raider", "expo": "Expo", "expolrv": "Expo LRV",
        "imiev": "i-MiEV",
    },
    "nissan": {
        "nv200": "NV200", "nv1500": "NV1500", "nv3500": "NV3500",
        "nv2500hd": "NV2500 HD", "240sx": "240SX", "350z": "350Z",
        "370z": "370Z", "pathfinder19995": "Pathfinder",
    },
    "oldsmobile": {
        "ciera": "Cutlass Ciera", "culassciera": "Cutlass Ciera",  # feed typo
        "eightyeight88": "Eighty-Eight", "ninetyeight98": "Ninety-Eight",
        "eightyeightroyale": "Eighty-Eight",
        "deltaeightyeightroyale": "Delta 88",
        "intriguegx": "Intrigue", "intriguegls": "Intrigue",
        "silhouetteapv": "Silhouette",
    },
    "pontiac": {
        "grandam": "Grand Am", "grandamse": "Grand Am", "grandamse1": "Grand Am",
        "grandamgt": "Grand Am", "grandamgt1": "Grand Am",
        "grandprixgt": "Grand Prix", "grandprixgtp": "Grand Prix",
        "grandprixgt2": "Grand Prix", "grandprixse": "Grand Prix",
        "grandprixse1": "Grand Prix",
        "bonnevillese": "Bonneville", "bonnevillegxp": "Bonneville",
        "sunfirese": "Sunfire", "azteksrv": "Aztek",
        "g3wave": "G3", "gto": "GTO",
    },
    "ram": {
        "1500pickup": "1500", "2500pickup": "2500", "3500pickup": "3500",
        "promaster": "ProMaster", "promastercity": "ProMaster City",
        "promaster1500": "ProMaster 1500", "promaster2500": "ProMaster 2500",
        "promaster3500": "ProMaster 3500",
        "promaster1500van": "ProMaster 1500", "promaster2500van": "ProMaster 2500",
        "promaster3500van": "ProMaster 3500",
        "cv": "C/V",
    },
    "plymouth": {"fury": "Fury"},
    "fiat": {"500l": "500L", "500x": "500X"},
    "merkur": {"xr4ti": "XR4Ti"},
    "saab": {"92x": "9-2X", "97x": "9-7X", "93x": "9-3X"},
    "saturn": {
        "auraxe": "Aura", "auraxr": "Aura", "astraxe": "Astra",
        "vuegreenlinehybrid": "VUE Green Line",
        "auragreenlinehybrid": "Aura Green Line",
        "l300sedan": "L300", "lw300": "LW300", "lw200": "LW200",
        "sl1": "SL1",
    },
    "scion": {"iq": "iQ", "ia": "iA", "im": "iM"},
    "subaru": {"xvcrosstrek": "XV Crosstrek"},
    "suzuki": {
        "sx4sedan": "SX4 Sport",   # the SX4 Sport IS the sedan body
        "sx4sport": "SX4 Sport", "grandvitaraxl7": "XL-7",
    },
    "toyota": {
        "solara": "Camry Solara", "corollamatrix": "Matrix",
        "pickup": "Pickup",              # catches 'Pick-Up' / 'Pick-Up Std'
        "pickupstd": "Pickup", "pickupdlx": "Pickup",
        "sciontc": "Scion tC", "scionxa": "Scion xA", "scionxb": "Scion xB",
        "scionxd": "Scion xD", "scionia": "Scion iA", "scioniq": "Scion iQ",
        "yarisia": "Yaris iA", "corollaim": "Corolla iM",
        "celicast": "Celica ST", "celicagt": "Celica GT",
        "mr2spyder": "MR2 Spyder", "vanwagon": "Van",
    },
    "volkswagen": {
        "cc": "CC", "golfgti": "GTI",
        "gli": "Jetta GLI", "jettagli": "Jetta GLI",
        "taos": "Taos", "bus": "Bus",
        "cabrioletconvertible": "Cabriolet",
    },
    "volvo": {
        "v70xc": "V70 XC",
        "240series": "240", "240series240": "240",
        "740series": "740", "760series": "760",
        "850series": "850", "850series850": "850",
        "940series": "940", "940series940": "940", "960series": "960",
    },
}

# Leading make-name junk some chains prepend to the model ('BMW 328i',
# 'Mercedes C-Class', 'Volvo 60 Series', 'Mini Mini Cooper'). Stripped only
# when the prefix names the row's OWN make — 'Dodge Durango' under make
# Chrysler and 'Chevrolet Sonic' under Buick keep their (sibling-make) prefix
# rather than silently changing meaning. Extra prefixes cover short forms and
# parent brands of the same marque.
_MODEL_STRIP_EXTRA = {
    "mercedesbenz": ("mercedes",),
    "ram": ("dodge",),       # 'Dodge 1500 Pickup' under make Ram IS the Ram
    "scion": ("toyota",),    # Scion is Toyota; 'Toyota Xb' under Scion = xB
}

# Pattern rules are MAKE-SCOPED: "E350" is a Ford van (E-350) but a Mercedes
# sedan (E350), and "Es300" is Lexus-styled "ES 300" while "Ml350" is
# Mercedes-styled "ML350". A make-blind rule broke Mercedes matches.
# BMW: numeric model + suffix in BMW's own casing (328I -> 328i, 740Il ->
# 740iL, 750LI -> 750Li), with optional GT / xDrive tails ('328I Xdrive' ->
# '328i xDrive'). 'li'/'il' before 'i' so the alternation matches longest.
#   'ia' is the automatic-transmission marker (540iA = 540i automatic), not a
#   distinct model — it folds into plain 'i'.
_BMW_SUFFIX_CASE = {"li": "Li", "il": "iL", "ia": "i"}  # rest lowercases
_BMW_MODEL_RE = re.compile(
    r"^(\d{3})\s*(li|il|ia|is|ci|xi|ix|si|ti|es|i|d|e)(?:\s+(gt))?(?:\s+(xdrive))?$",
    re.IGNORECASE,
)
_FE_SERIES_RE = re.compile(r"^([FE])\s*-?\s*(\d{2,3})$", re.IGNORECASE)
# Ford truck/van chain suffixes on the squashed key: 'F150 Pickup', 'Ford
# F250Sd Pickup' (after prefix strip), 'E350 Super Duty Van', 'E-150
# Econoline Club Wagon'. SD/Super Duty is a REAL distinct truck and is kept
# in the display name; the body words (Pickup/Truck/Van/Econoline/Wagon) are
# per-chain noise — every F-150 is a pickup.
_FORD_F_KEY_RE = re.compile(r"^f(\d{3})(sd|superduty)?(?:pickup|truck)?$")
_FORD_E_KEY_RE = re.compile(
    r"^e(\d{3})(sd|superduty)?(?:van|econoline|wagon|econolinewagon|"
    r"clubwagon|econolineclubwagon)?$")
_TWO_LETTER_NUM_RE = re.compile(r"^([A-Za-z]{2})\s*-?\s*(\d{3})\s*(h|t|c)?$",
                                re.IGNORECASE)
_MB_ALNUM_RE = re.compile(r"^([A-Za-z]{1,3})\s*-?\s*(\d{2,3})$")
# Classic Mercedes digits-then-letters designations ('300Sd' -> 300SD,
# '450Sl' -> 450SL, '560Sec' -> 560SEC) and AMG tails ('Ml55 Amg' -> ML55 AMG).
_MB_NUM_SUFFIX_RE = re.compile(
    r"^(\d{3})\s*(sel|sec|slc|se|sd|sl|ce|td|te|e|d|s)$", re.IGNORECASE)
_MB_AMG_RE = re.compile(r"^([A-Za-z]{1,3})\s*(\d{2,3})\s+amg$", re.IGNORECASE)
# Volvo / Infiniti letter-prefix models are all-caps (Xc90 -> XC90, Qx56 ->
# QX56, Fx35 -> FX35, G35x stays G35X per the inventory's dominant form).
_LETTERS_NUM_UPPER_RE = re.compile(r"^([A-Za-z]{1,2})\s*-?\s*(\d{1,3})(x?)$",
                                   re.IGNORECASE)
# Chevy/GMC chain suffixes on the squashed key.
_SILVERADO_KEY_RE = re.compile(r"^silverado(\d{4})(hd)?(?:pickup)?$")
_EXPRESS_KEY_RE = re.compile(r"^express(\d{4})(?:van|cargovan)?$")


def _squash_model_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _strip_make_prefix(m: str, make_key: str) -> str:
    """Drop leading word(s) that just repeat the row's own make. Loops so
    'Mini Mini Cooper' -> 'Cooper'; never strips the whole string."""
    prefixes = (make_key,) + _MODEL_STRIP_EXTRA.get(make_key, ())
    while True:
        words = m.split()
        if len(words) < 2:
            return m
        stripped = False
        for k in (2, 1):  # longest match first ('Land Rover Range Rover')
            if len(words) > k and _squash_model_key(" ".join(words[:k])) in prefixes:
                m = " ".join(words[k:])
                stripped = True
                break
        if not stripped:
            return m


def normalize_model(model: str, make: str = "") -> str:
    """Canonical display spelling for a feed-supplied model name. Idempotent.

    Order: HTML-entity unescape ('TOWN &amp; COUNTRY'), whitespace/trailing-
    punctuation cleanup ('Grand Caravan.'), own-make prefix strip ('BMW 328i'),
    per-make canon table, global canon table, make-scoped pattern rules."""
    m = html.unescape(model or "")
    m = re.sub(r"\s+", " ", m.strip().lstrip("&/ ")).strip().rstrip(".,")
    if not m:
        return m
    make_key = _squash_model_key(make)
    m = _strip_make_prefix(m, make_key)
    key = _squash_model_key(m)
    per_make = _MODEL_CANON_BY_MAKE.get(make_key)
    if per_make and key in per_make:
        return per_make[key]
    if key in _MODEL_CANON:
        return _MODEL_CANON[key]
    mk = (make or "").lower()
    if "ford" in mk:
        r = _FORD_F_KEY_RE.match(key)    # F250Sd Pickup -> F-250 Super Duty
        if r:
            return f"F-{r.group(1)}" + (" Super Duty" if r.group(2) else "")
        r = _FORD_E_KEY_RE.match(key)    # E-350 Econoline Club Wagon -> E-350
        if r:
            return f"E-{r.group(1)}" + (" Super Duty" if r.group(2) else "")
        r = _FE_SERIES_RE.match(m)       # F150 / E 350 -> F-150 / E-350
        if r:
            return f"{r.group(1).upper()}-{r.group(2)}"
    elif "bmw" in mk:
        r = _BMW_MODEL_RE.match(m)       # 328I Xdrive -> 328i xDrive
        if r:
            suf = r.group(2).lower()
            out = f"{r.group(1)}{_BMW_SUFFIX_CASE.get(suf, suf)}"
            if r.group(3):
                out += " GT"
            if r.group(4):
                out += " xDrive"
            return out
    elif "lexus" in mk:
        r = _TWO_LETTER_NUM_RE.match(m)  # Es300 / Rx450H -> ES 300 / RX 450h
        if r:
            out = f"{r.group(1).upper()} {r.group(2)}"
            if r.group(3):
                # h/t stay lowercase (RX 450h, IS 200t); C is upper (IS 250C).
                suf = r.group(3)
                out += suf.upper() if suf.lower() == "c" else suf.lower()
            return out
    elif "mercedes" in mk:
        r = _MB_NUM_SUFFIX_RE.match(m)   # 300Sd / 560Sec -> 300SD / 560SEC
        if r:
            return f"{r.group(1)}{r.group(2).upper()}"
        r = _MB_AMG_RE.match(m)          # Ml55 Amg -> ML55 AMG
        if r:
            return f"{r.group(1).upper()}{r.group(2)} AMG"
        r = _MB_ALNUM_RE.match(m)        # Ml350 / e320 -> ML350 / E320
        if r:
            return f"{r.group(1).upper()}{r.group(2)}"
    elif "volvo" in mk or "infiniti" in mk:
        r = _LETTERS_NUM_UPPER_RE.match(m)  # Xc90 / Qx56 -> XC90 / QX56
        if r:
            return f"{r.group(1).upper()}{r.group(2)}{r.group(3).upper()}"
    elif "chevrolet" in mk:
        r = _SILVERADO_KEY_RE.match(key)  # Silverado 1500 Pickup -> Silverado 1500
        if r:
            return f"Silverado {r.group(1)}" + ("HD" if r.group(2) else "")
        r = _EXPRESS_KEY_RE.match(key)    # Express 2500 Van -> Express 2500
        if r:
            return f"Express {r.group(1)}"
    return m


# ---------------------------------------------------------------------------
# Generic-blob resolution via the VIN decode cache (same idea as the
# 'General Motors' make blob in normalize_make, but the evidence is NHTSA's
# decoded model instead of the WMI). Chains file whole families under one
# string — BMW '3 Series' (919 cars at audit time), Ford 'E-Series' /
# 'Econoline', GMC 'Sierra', Dodge 'Ram Pickup' — and the audit showed the
# decode cache resolves 85-95%+ of them to the concrete model.
#
# Policy: resolve ONLY rows whose (already-normalized) model is a registered
# blob key below, ONLY when the decode is confident (decoded make agrees,
# decoded model is concrete). Ambiguous rows keep the blob — never guess.
# Mercedes '*-Class' blobs are deliberately NOT registered: NHTSA catalogs
# Mercedes at class granularity, so the decode can't go more specific.
_MODEL_BLOBS: dict[str, set[str]] = {
    "bmw": {"1series", "2series", "3series", "4series", "5series", "6series",
            "7series", "7seriesalpinab7"},
    "ford": {"eseries", "fseries", "econoline", "econolinewagon", "clubwagon"},
    "mazda": {"bseries"},
    "saturn": {"sseries", "lseries", "lseriessedan", "lserieswagon"},
    "volvo": {"30series", "40series", "50series", "60series", "70series",
              "80series", "120series", "xc"},
    "infiniti": {"fxseries"},
    "jaguar": {"xjseries", "xfseries", "xkseries"},
    "hyundai": {"xgseries"},
    "chevrolet": {"silverado", "suburban", "express", "gmt400",
                  "ck1500", "ck2500", "ck3500", "ck10", "ck20", "ck30",
                  "ckpickup", "gseries", "1500pickup", "2500pickup",
                  "3500pickup", "1500", "2500"},
    "gmc": {"sierra", "suburban", "gmt400", "jimmyorenvoy", "ck1500",
            "ck2500", "ckpickup", "1500pickup", "2500pickup", "3500pickup",
            "1500", "2500", "1500van", "2500van"},
    "dodge": {"ram", "rampickup", "ramtruck", "dseries", "wseries",
              "1500pickup", "2500pickup", "1500", "1500van", "2500van",
              "3500van", "150van", "250van",
              "caravangrandcaravan"},
    "lexus": {"gs300400", "sc300400", "scseries"},
}
# Bare BMW three-digit strings ('328' could be i/is/ci/xi) also resolve by
# VIN; 'Unknown' resolves for every make.
_BMW_BARE_NUM_RE = re.compile(r"^\d{3}$")

# GM truck decodes name the family in `model` and the size in `series`
# ('Silverado' + '1500 (1/2 Ton)' / '1/2 Ton Nominal'). Dodge Ram ditto
# ('Ram' + 'DR (1500)').
_TONNAGE_NUM_RE = re.compile(r"\b([123]500)\b")
_TONNAGE_FRAC_RE = re.compile(r"\b(1/2|3/4|1)\s*ton", re.IGNORECASE)
_TON_TO_SERIES = {"1/2": "1500", "3/4": "2500", "1": "3500"}


def _series_tonnage(series: str) -> str | None:
    m = _TONNAGE_NUM_RE.search(series or "")
    if m:
        return m.group(1)
    m = _TONNAGE_FRAC_RE.search(series or "")
    if m:
        return _TON_TO_SERIES[m.group(1)]
    return None


def _decode_make_agrees(make: str, dec_make: str) -> bool:
    a, b = _make_key(make), _make_key(dec_make)
    return bool(a and b) and (a in b or b in a)


def resolve_model_blob(model: str, make: str, vin_dec: dict | None) -> str:
    """Concrete model for a registered generic-blob row, from its VIN decode.
    Returns the (already canonical) model unchanged when the row isn't a blob
    or the decode isn't confident."""
    key = _squash_model_key(model)
    make_key = _make_key(make)
    is_blob = (key in _MODEL_BLOBS.get(make_key, ()) or key == "unknown"
               or (make_key == "bmw" and _BMW_BARE_NUM_RE.match(key)))
    if not is_blob or not vin_dec:
        return model
    dec_model = (vin_dec.get("model") or "").strip()
    dec_series = (vin_dec.get("series") or "").strip()
    if not dec_model or not _decode_make_agrees(make, vin_dec.get("make") or ""):
        return model
    dm_key = _squash_model_key(dec_model)
    # GM/Dodge truck families: NHTSA model is itself the family name; the
    # tonnage lives in `series`. GMT-400 / 'C/K Pickup' refine to C/K via
    # driveType (position-coded C=2WD, K=4WD).
    if dm_key in ("silverado", "sierra", "suburban", "express", "ram"):
        t = _series_tonnage(dec_series)
        if t:
            name = {"ram": "Ram"}.get(dm_key, dec_model.title())
            return normalize_model(f"{name} {t}", make)
        return model
    if dm_key in ("gmt400", "ckpickup"):
        t = _series_tonnage(dec_series)
        if not t:
            return model
        drive = (vin_dec.get("driveType") or "").lower()
        if "4wd" in drive or "4x4" in drive:
            return f"K{t}"
        if "rwd" in drive or "2wd" in drive:
            return f"C{t}"
        return f"C/K {t}"
    # Mazda B-Series / Dodge D-Series: concrete designation in `series`.
    if dm_key in ("bseries", "dseries"):
        r = re.match(r"^([BD]\d{3,4})\b", dec_series.upper())
        return normalize_model(r.group(1), make) if r else model
    # Lexus 'GS 300/400' / 'SC 300/400': decode model is bare 'GS'/'SC'; the
    # platform code in `series` names the engine (JZS160=GS 300, UZS160=
    # GS 400; JZZ3x=SC 300, UZZ3x=SC 400).
    if dm_key in ("gs", "sc"):
        plat = dec_series.upper()
        for pfx, out in (("JZS160", "GS 300"), ("UZS160", "GS 400"),
                         ("JZZ", "SC 300"), ("UZZ", "SC 400")):
            if plat.startswith(pfx):
                return out
        return model
    # NHTSA sometimes answers with a multi-model string ('325/325e') or the
    # same blob the feed used ('E-Series' stays series-less) — not confident.
    if "/" in dec_model or dm_key in ("unknown", "") or dm_key == key:
        return model
    return normalize_model(dec_model, make)


# ---------------------------------------------------------------------------
# Make-name normalization. 27 chains spell makes their own way, and the raw
# strings shipped straight into the UI's make dropdown: "MINI (756)" next to
# "MINI Cooper (52)", "Alfa Romeo" next to "Alfa-Romeo", "Vw" next to
# "Volkswagen" (owner-reported 2026-10-21). Canonicalized once here, at enrich
# time, so every adapter benefits — same pattern as _sanitize_date_added.
#
# Alias table policy: EVIDENCE-DRIVEN and conservative. Keys are squashed
# lowercase alphanumerics (same keying as _MODEL_CANON), values are canonical
# display names. Only marques that are provably the SAME company belong here —
# merging wrong is worse than a duplicate dropdown entry. Deliberately NOT
# merged: Datsun/Nissan, Geo/Chevrolet, GMC/Chevrolet, Genesis/Hyundai,
# Scion/Toyota, Ram/Dodge (distinct marques users search by); Miles (a real
# 1-row 2009 Miles ZX40ST — Miles Electric Vehicles was a genuine US LSV
# maker); Mitsubishi Fuso (a real FE84D cabover — Fuso is Daimler's truck
# marque, not Mitsubishi Motors); "Sprinter (Dodge Or Freightliner)" (the
# feed itself can't tell; no VIN to break the tie).
_MAKE_ALIASES = {
    "minicooper": "MINI",            # Pull-N-Save files MINIs under "Mini Cooper"
    "alfaromeo": "Alfa Romeo",       # catches the hyphenated "Alfa-Romeo" spelling
    "fiatlancia": "Fiat",            # Pull-N-Save's combined "Fiat-Lancia" bucket
                                     # (audit 2026-10: all 24 rows are Fiat 500s /
                                     # 124 Spiders — zero actual Lancias)
    "mercedes": "Mercedes-Benz",     # Wrench-A-Part / Ace spell it short
    "mercedesbenz": "Mercedes-Benz",
    "vw": "Volkswagen",              # Pull-A-Part's "Vw" (830 rows)
    "volkswagon": "Volkswagen",      # common feed misspelling
    "chevy": "Chevrolet",
    "chev": "Chevrolet",
    "rover": "Land Rover",           # audit 2026-10: all 28 "Rover" rows carry
                                     # SAL* VINs / Land Rover models (Range Rover
                                     # Sport, LR3, Freelander...) — the British
                                     # Rover marque never appears in these feeds
    "landrover": "Land Rover",
    "rangerover": "Land Rover",      # Range Rover is a Land Rover model line
    "infinity": "Infiniti",          # misspelling — Infinity is not a marque
}

# "General Motors" (3,046 rows: Pull-N-Save + Nevada Pic-A-Part label every GM
# car with the corporation, not the division). Resolve to the real marque only
# when the evidence is unambiguous; rows that stay ambiguous keep "General
# Motors" rather than guessing.
#
# Evidence order:
#   1. VIN WMI — GM's own division coding: positions 1-3 of a [1-3|6]G? VIN
#      name the division in the 3rd character. Audit of the 3,007 VIN-bearing
#      rows cross-tabbed perfectly against models (Acadia/Yukon under GMC,
#      G6/Grand Prix under Pontiac, Alero under Oldsmobile, ...).
#   2. Model's first word is itself a division name ("Chevrolet 20 Pickup",
#      "Gmc Terrain", "Oldsmobile Bravada", "Hummer H3", "Saturn Vue").
#   3. A division-exclusive model name (Equinox -> Chevrolet, Vibe -> Pontiac,
#      Rendezvous -> Buick...), year-gated where a nameplate crossed brands
#      (Metro/Prizm/Tracker were Geo through 1997, Chevrolet after; Suburban
#      was both Chevy AND GMC through 1999 so only 2000+ resolves).
_GM_WMI_DIVISION = {  # 3rd VIN char when chars 1-2 match [1-3|6]G (US/CA/MX/AU builds)
    "1": "Chevrolet", "2": "Pontiac", "3": "Oldsmobile", "4": "Buick",
    "6": "Cadillac", "8": "Saturn",
    "B": "Chevrolet", "C": "Chevrolet", "N": "Chevrolet",   # trucks/SUVs/incomplete
    "D": "GMC", "K": "GMC", "T": "GMC",
    "M": "Pontiac", "Y": "Cadillac",
}
_GM_WMI_FULL = {  # whole-WMI entries outside the division scheme
    "KL1": "Chevrolet", "KL7": "Chevrolet", "KL8": "Chevrolet",  # GM Korea (Aveo/Spark)
    "KL4": "Buick",                                              # GM Korea (Encore)
    "W04": "Buick", "W06": "Cadillac",                           # Opel-built (Regal/Catera)
    "5GA": "Buick", "5GZ": "Saturn",                             # Lansing Delta (Enclave/Outlook)
    "5GR": "Hummer", "5GT": "Hummer",                            # H2 / H3
    "5Y2": "Pontiac", "2CK": "Pontiac",                          # NUMMI Vibe / CAMI Torrent
    "2CT": "GMC",                                                # CAMI Terrain
    "3N6": "Chevrolet",                                          # City Express (Nissan-built)
}
_GM_DIVISION_NAMES = {
    "chevrolet": "Chevrolet", "pontiac": "Pontiac", "oldsmobile": "Oldsmobile",
    "buick": "Buick", "cadillac": "Cadillac", "saturn": "Saturn", "gmc": "GMC",
    "hummer": "Hummer", "geo": "Geo", "olds": "Oldsmobile", "chevy": "Chevrolet",
}
_GM_MODEL_DIVISION = {  # division-exclusive nameplates only (squashed keys)
    # Chevrolet
    "equinox": "Chevrolet", "cobalt": "Chevrolet", "cruze": "Chevrolet",
    "sonic": "Chevrolet", "impala": "Chevrolet", "malibu": "Chevrolet",
    "tahoe": "Chevrolet", "traverse": "Chevrolet", "camaro": "Chevrolet",
    "corvette": "Chevrolet", "volt": "Chevrolet", "montecarlo": "Chevrolet",
    "cavalier": "Chevrolet", "venture": "Chevrolet", "uplander": "Chevrolet",
    "captivasport": "Chevrolet", "cityexpress": "Chevrolet", "astro": "Chevrolet",
    "avalanche": "Chevrolet", "aveo": "Chevrolet", "hhr": "Chevrolet",
    "caprice": "Chevrolet", "corsica": "Chevrolet", "celebrity": "Chevrolet",
    "lumina": "Chevrolet", "luminaapv": "Chevrolet", "spark": "Chevrolet",
    "trailblazer": "Chevrolet", "trailblazerext": "Chevrolet",
    "express1500van": "Chevrolet", "express2500van": "Chevrolet",
    "express3500van": "Chevrolet",
    # Pontiac
    "g5": "Pontiac", "g6": "Pontiac", "g8": "Pontiac", "grandprix": "Pontiac",
    "grandam": "Pontiac", "bonneville": "Pontiac", "sunfire": "Pontiac",
    "sunbird": "Pontiac", "aztek": "Pontiac", "vibe": "Pontiac",
    "montana": "Pontiac", "montanasv6": "Pontiac", "torrent": "Pontiac",
    "firebird": "Pontiac", "solstice": "Pontiac", "gto": "Pontiac",
    "fiero": "Pontiac", "transam": "Pontiac",
    # Buick
    "rendezvous": "Buick", "lesabre": "Buick", "lacrosse": "Buick",
    "century": "Buick", "enclave": "Buick", "regal": "Buick",
    "lucerne": "Buick", "verano": "Buick", "parkavenue": "Buick",
    "rainier": "Buick", "terraza": "Buick", "encore": "Buick",
    "roadmaster": "Buick", "riviera": "Buick", "skylark": "Buick",
    # Oldsmobile
    "alero": "Oldsmobile", "intrigue": "Oldsmobile", "aurora": "Oldsmobile",
    "achieva": "Oldsmobile", "toronado": "Oldsmobile", "bravada": "Oldsmobile",
    "silhouette": "Oldsmobile", "eightyeight": "Oldsmobile",
    "ninetyeight": "Oldsmobile", "cutlass": "Oldsmobile",
    "cutlasssupreme": "Oldsmobile", "cutlassciera": "Oldsmobile",
    # Cadillac
    "cts": "Cadillac", "ctsv": "Cadillac", "srx": "Cadillac",
    "deville": "Cadillac", "dts": "Cadillac", "sts": "Cadillac",
    "ats": "Cadillac", "xts": "Cadillac", "escalade": "Cadillac",
    "escaladeext": "Cadillac", "escaladeesv": "Cadillac",
    "eldorado": "Cadillac", "seville": "Cadillac", "fleetwood": "Cadillac",
    "catera": "Cadillac", "allante": "Cadillac",
    # Saturn
    "vue": "Saturn", "ion": "Saturn", "aura": "Saturn", "outlook": "Saturn",
    "sky": "Saturn", "relay": "Saturn", "astra": "Saturn", "l300": "Saturn",
    "sl1": "Saturn", "sl2": "Saturn", "sc1": "Saturn", "sc2": "Saturn",
    # GMC
    "acadia": "GMC", "envoy": "GMC", "envoyxl": "GMC", "terrain": "GMC",
    "savana": "GMC", "sonoma": "GMC", "jimmy": "GMC", "canyon": "GMC",
    "yukon": "GMC", "yukonxl": "GMC", "yukonxl1500": "GMC", "yukonxl2500": "GMC",
    # Hummer / Geo-exclusive
    "h1": "Hummer", "h2": "Hummer", "h3": "Hummer", "h3t": "Hummer",
    "storm": "Geo",
}
# Nameplates that crossed brands on a known year boundary.
_GM_MODEL_YEAR_GATED = {
    # Geo through 1997, Chevrolet from the 1998 rebrand on.
    "metro": lambda y: "Geo" if y <= 1997 else "Chevrolet",
    "prizm": lambda y: "Geo" if y <= 1997 else "Chevrolet",
    "tracker": lambda y: "Geo" if y <= 1997 else "Chevrolet",
    # GMC sold Suburbans too until the 2000 Yukon XL rename — only 2000+ is
    # unambiguously Chevrolet. (Pre-2000 rows resolve via VIN when present.)
    "suburban": lambda y: "Chevrolet" if y >= 2000 else None,
    "suburban1500": lambda y: "Chevrolet" if y >= 2000 else None,
    "suburban2500": lambda y: "Chevrolet" if y >= 2000 else None,
}

_MAKE_SQUASH_RE = re.compile(r"[^a-z0-9]")


def _make_key(s: str) -> str:
    return _MAKE_SQUASH_RE.sub("", (s or "").lower())


def _resolve_general_motors(model: str, vin: str, year: int) -> str | None:
    """Real GM division for a 'General Motors' row, or None when ambiguous."""
    vin = (vin or "").strip().upper()
    if len(vin) >= 3:
        w = vin[:3]
        if w in _GM_WMI_FULL:
            return _GM_WMI_FULL[w]
        if w[0] in "1236" and w[1] == "G":
            div = _GM_WMI_DIVISION.get(w[2])
            if div:
                return div
    words = (model or "").strip().split()
    if words:
        div = _GM_DIVISION_NAMES.get(words[0].lower())
        if div:
            return div
    mkey = _make_key(model)
    if mkey in _GM_MODEL_DIVISION:
        return _GM_MODEL_DIVISION[mkey]
    gate = _GM_MODEL_YEAR_GATED.get(mkey)
    if gate:
        try:
            y = int(year or 0)
        except (TypeError, ValueError):
            y = 0
        if y:
            return gate(y)
    return None


def normalize_make(make: str, model: str = "", vin: str = "", year: int = 0) -> str:
    """Canonical display name for a feed-supplied make. Idempotent.

    Casing first (_canon_make: FORD -> Ford, mini -> MINI), then the alias
    table, then corporate-blob resolution for 'General Motors'/'GM' rows via
    VIN WMI / model evidence (ambiguous rows keep 'General Motors')."""
    s = _canon_make(make)
    key = _make_key(s)
    if key in ("generalmotors", "gm"):
        return _resolve_general_motors(model, vin, year) or "General Motors"
    return _MAKE_ALIASES.get(key, s)


_DATE_ADDED_MAX_AGE_DAYS = 15 * 365  # ~15 years; nothing sits on a U-pull lot that long


def _sanitize_date_added(date_s: str, today_utc=None) -> str:
    """Clamp a vehicle's dateAdded to plausible values; '' = unknown date.

    The app's convention for a missing set-out date is the empty string
    (renders 'Set-out date unknown', never 'fresh'/NEW). Yard feeds ship
    placeholder/epoch garbage — Fenix's 01/01/70 rows (-> 2070 via naive
    2-digit-year expansion), Pull-N-Save's 0000-00-00 — so anything that
    isn't a real calendar date within [today-15y, today+1d] becomes ''.
    today+1 is legitimate: East Coast yards date in UTC, which can be a
    day ahead of the scanner's clock."""
    s = str(date_s or "").strip()[:10]
    if not s:
        return ""
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return ""
    today = today_utc or datetime.now(timezone.utc).date()
    if d > today + timedelta(days=1):
        return ""
    if d < today - timedelta(days=_DATE_ADDED_MAX_AGE_DAYS):
        return ""
    return s


def enrich_vehicles(
    vehicles: list[dict],
    *,
    decode_vins: bool = False,
    decode_vins_profit_top: int = 0,
    decode_vins_incremental: bool = False,
) -> list[dict]:
    """Add unobtanium match data. Optionally decode VINs via NHTSA VPIC (all unique VINs, or top-N-by-profit only)."""
    # Canonical make, then model spelling, before anything else — matching,
    # display, and the UI's make/model dropdowns all key off these fields.
    # Make goes first so normalize_model's make-scoped rules see the
    # canonical name ('Mercedes-Benz', not 'Mercedes').
    for v in vehicles:
        v["make"] = normalize_make(
            v.get("make") or "", model=v.get("model") or "",
            vin=v.get("vin") or "", year=v.get("year") or 0,
        )
        v["model"] = normalize_model(v.get("model") or "", v.get("make") or "")
        # Global date sanity clamp: every adapter's dateAdded funnels through
        # here before matching, output_json, the history DB, and alerts.
        v["dateAdded"] = _sanitize_date_added(v.get("dateAdded", ""))
    allowed_vins: set[str] | None = None

    def _apply_match(v: dict, vin_dec: dict | None) -> None:
        # Generic-blob rows ('3 Series', 'E-Series', 'Sierra', 'Ram Pickup')
        # resolve to the concrete model here, where the VIN decode is in hand
        # — before matching, so UNOBTANIUM_DB keyword matches see the real
        # model too. Non-blob rows and unconfident decodes pass through.
        v["model"] = resolve_model_blob(
            v.get("model") or "", v.get("make") or "", vin_dec)
        mismatch = _vpic_mismatch_msg(v, vin_dec)
        if mismatch:
            v["_vpic_mismatch"] = mismatch
        match_year = v.get("year", 0)
        if vin_dec:
            # Trust the VIN over the lot sign for the model year used in
            # matching (year gates which parts apply); display keeps the
            # listing year plus the mismatch flag.
            try:
                vy = int(vin_dec.get("modelYear") or 0)
            except (TypeError, ValueError):
                vy = 0
            if vy:
                match_year = vy
        v["_matches"] = match_vehicle(
            match_year, v.get("make", ""), v.get("model", ""),
            vin_decode=vin_dec,
        )
        if v["_matches"]:
            v["_max_value"] = max(m["max_value"] for m in v["_matches"])
            v["_top_parts"] = v["_matches"][0]["top_parts"]
            v["_display"] = v["_matches"][0]["display"]
        else:
            v["_max_value"] = 0
            v["_top_parts"] = []
            v["_display"] = f"{v.get('make', '')} {v.get('model', '')}"

    if decode_vins_incremental:
        # Incremental pipeline: every previously-seen VIN comes from the
        # persistent SQLite cache with zero API calls; only never-seen VINs
        # are decoded, newest arrivals first, capped per run so the initial
        # backlog drains across scheduled scans without blowing up CI time.
        try:
            import db as _db
        except ImportError:
            from scraper import db as _db  # pragma: no cover
        _db.import_vin_decodes_gz(DATA_DIR / "vin_decodes.json.gz")
        cached = _db.load_vin_decodes()
        _VPIC_CACHE.update(cached)

        vin_newest: dict[str, str] = {}
        for v in vehicles:
            vn = _normalize_vin(v.get("vin", ""))
            if vn:
                d = str(v.get("dateAdded", "") or "")
                if d > vin_newest.get(vn, ""):
                    vin_newest[vn] = d
        uncached = [vn for vn in vin_newest if vn not in cached]
        uncached.sort(key=lambda vn: vin_newest[vn], reverse=True)
        cap = max(0, int(os.environ.get("VPIC_MAX_PER_RUN", "5000")))
        todo = uncached[:cap]
        print(
            f"  NHTSA VPIC incremental: {len(vin_newest)} unique VINs in scan, "
            f"{len(cached)} cached, {len(uncached)} new; decoding {len(todo)} this run "
            f"(cap {cap}, newest first, batches of {VPIC_BATCH_SIZE})...",
            file=sys.stderr,
        )
        if todo:
            _decode_vpic_batch(todo)
            fresh = {vn: _VPIC_CACHE[vn] for vn in todo if _VPIC_CACHE.get(vn) is not None}
            failed = len(todo) - len(fresh)
            added = _db.store_vin_decodes(fresh, _iso_utc_z())
            print(
                f"  VPIC incremental: {added} decodes cached this run"
                + (f", {failed} failed (will retry next run)" if failed else ""),
                file=sys.stderr,
            )
            # Disaster-insurance export to git (only when grown enough — see db.py).
            if _db.export_vin_decodes_gz(DATA_DIR / "vin_decodes.json.gz"):
                print("  VPIC incremental: refreshed docs/data/vin_decodes.json.gz backup", file=sys.stderr)
        remaining = max(0, len(uncached) - len(todo))
        if remaining:
            print(f"  VPIC incremental: {remaining} VINs still queued for future runs", file=sys.stderr)
        for v in vehicles:
            vn = _normalize_vin(v.get("vin", ""))
            # Cache-only lookup: never trigger a network call here, so vehicles
            # beyond this run's cap simply match without VIN data until a
            # later run decodes them.
            vin_dec = _VPIC_CACHE.get(vn) if vn else None
            v["_vpic"] = vin_dec
            _apply_match(v, vin_dec)
    elif decode_vins_profit_top > 0:
        for v in vehicles:
            v["_vpic"] = None
            _apply_match(v, None)
        top_rows: list[dict] = []
        for v in sorted(vehicles, key=_vehicle_carry_profit, reverse=True):
            if len(top_rows) >= decode_vins_profit_top:
                break
            if _normalize_vin(v.get("vin", "")):
                top_rows.append(v)
        allowed_vins = {_normalize_vin(v["vin"]) for v in top_rows}
        if allowed_vins:
            print(
                f"  NHTSA VPIC (profit-top {decode_vins_profit_top}): decoding "
                f"{len(allowed_vins)} unique VIN(s) from highest carry-profit rows "
                f"({_VPIC_WORKERS} workers)...",
                file=sys.stderr,
            )
            for v in top_rows:
                p = _vehicle_carry_profit(v)
                print(
                    f"    ${p:,.0f}  {v.get('year')} {v.get('make')} {v.get('model')}  {v.get('vin', '')}",
                    file=sys.stderr,
                )
            ulist = sorted(allowed_vins)
            decs = _decode_vpic_unique_parallel(ulist)
            usable = ambiguous = empty = 0
            for d in decs:
                if not d:
                    empty += 1
                elif d.get("trimQuality") == "usable":
                    usable += 1
                elif d.get("trimQuality") == "ambiguous":
                    ambiguous += 1
                else:
                    empty += 1
            print(
                f"  VPIC trim: usable={usable} ambiguous_list={ambiguous} empty_or_fail={empty}",
                file=sys.stderr,
            )
        for v in vehicles:
            vin_dec = None
            vn = _normalize_vin(v.get("vin", ""))
            if vn and allowed_vins is not None and vn in allowed_vins:
                vin_dec = fetch_vpic_decode(vn)
            v["_vpic"] = vin_dec
            _apply_match(v, vin_dec)
    elif decode_vins:
        unique_vins: set[str] = set()
        for v in vehicles:
            vn = _normalize_vin(v.get("vin", ""))
            if vn:
                unique_vins.add(vn)
        if unique_vins:
            ulist = sorted(unique_vins)
            print(
                f"  NHTSA VPIC: decoding {len(ulist)} unique VIN(s) "
                f"({_VPIC_WORKERS} workers; set VPIC_WORKERS / VPIC_DELAY_SEC to tune)...",
                file=sys.stderr,
            )
            decs = _decode_vpic_unique_parallel(ulist)
            usable = ambiguous = empty = 0
            for d in decs:
                if not d:
                    empty += 1
                elif d.get("trimQuality") == "usable":
                    usable += 1
                elif d.get("trimQuality") == "ambiguous":
                    ambiguous += 1
                else:
                    empty += 1
            print(
                f"  VPIC trim: usable={usable} ambiguous_list={ambiguous} empty_or_fail={empty}",
                file=sys.stderr,
            )
        for v in vehicles:
            vin_dec = None
            vn = _normalize_vin(v.get("vin", ""))
            if vn:
                vin_dec = fetch_vpic_decode(vn)
            v["_vpic"] = vin_dec
            _apply_match(v, vin_dec)
    else:
        for v in vehicles:
            v["_vpic"] = None
            _apply_match(v, None)

    if decode_vins or decode_vins_profit_top or decode_vins_incremental:
        n_decode_well = sum(
            1 for v in vehicles
            if isinstance(v.get("_vpic"), dict) and v["_vpic"].get("trimQuality") == "usable"
        )
        print(
            f"  VPIC decode-well (trim-specific, per vehicle row): {n_decode_well}",
            file=sys.stderr,
        )
    return vehicles


def vehicle_hash(v: dict) -> str:
    key = f"{v.get('vin', '')}{v.get('id', '')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def load_seen() -> dict:
    CACHE_DIR.mkdir(exist_ok=True)
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text())
    return {}


def save_seen(seen: dict):
    CACHE_DIR.mkdir(exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=2))


# Fixed coordinates for Utah-chain yards (PnP provides lat/lng in its own feed).
# Matched by location-name prefix so "(Premium)" variants resolve too.
YARD_COORDS = {
    "Tear-A-Part - Salt Lake City": (40.7608, -111.8910),
    "Tear-A-Part - Ogden": (41.2230, -111.9738),
    "Utah Pic-A-Part - Ogden": (41.2230, -111.9738),
    "Utah Pic-A-Part - Orem": (40.2969, -111.6946),
}


def _vehicle_coords(v: dict) -> tuple[float | None, float | None]:
    lat, lng = v.get("_lat"), v.get("_lng")
    try:
        if lat is not None and lng is not None:
            return float(lat), float(lng)
    except (TypeError, ValueError):
        pass
    loc = v.get("_location") or ""
    for prefix, (la, ln) in YARD_COORDS.items():
        if loc.startswith(prefix):
            return la, ln
    return None, None


def output_json(vehicles: list[dict], only_matches: bool = True):
    output = []
    for v in vehicles:
        if only_matches and not v.get("_matches"):
            continue
        _lat, _lng = _vehicle_coords(v)
        entry = {
            "id": v.get("id"),
            "vin": v.get("vin", ""),
            "year": v.get("year"),
            # Already canonical after enrich_vehicles; normalize_make here is
            # an idempotent belt-and-braces for any path that skips enrich.
            "make": normalize_make(v.get("make", ""), model=v.get("model", ""),
                                   vin=v.get("vin", ""), year=v.get("year") or 0),
            "model": v.get("model", ""),
            "row": v.get("row", ""),
            "dateAdded": v.get("dateAdded", ""),
            "location": v.get("_location", ""),
            "city": v.get("_city", ""),
            "state": v.get("_state", ""),
            "utpapPremium": bool(v.get("_utpap_premium")),
            "lat": _lat,
            "lng": _lng,
            "hasMatch": bool(v.get("_matches")),
            "maxValue": v.get("_max_value", 0),
            "displayName": v.get("_display", ""),
            "topParts": [
                {
                    "name": p["name"], "rarity": p["rarity"],
                    "low": p["low"], "high": p["high"], "cost": p["cost"],
                    "sell_at": p.get("sell_at", ""),
                    "sell_speed": p.get("sell_speed", ""),
                    "sell_notes": p.get("sell_notes", ""),
                    **({"fits": p["fits"]} if p.get("fits") else {}),
                    **({"trim_status": p["trim_status"]} if p.get("trim_status") else {}),
                    **({"verify": p["verify"]} if p.get("verify") else {}),
                    **({"sharedWith": p["sharedWith"]} if p.get("sharedWith") else {}),
                }
                for p in v.get("_top_parts", [])
            ],
        }
        entry["photo"] = v.get("_photo", "")
        entry["color"] = v.get("_color", "")
        entry["engine"] = v.get("_engine", "")
        entry["trans"] = v.get("_trans", "")
        # Transmission provenance, same vocabulary as parts' trim_status:
        # "listing" = the yard's own feed/table said so, "vin" = the VIN
        # decode said so. Shipped so the UI can say which one it's quoting.
        entry["transSrc"] = "listing" if entry["trans"] else ""
        vp = v.get("_vpic")
        if isinstance(vp, dict) and vp:
            # Chain feeds rarely carry specs; the VIN decode fills them in.
            if not entry["engine"]:
                entry["engine"] = vp.get("engine", "")
            if not entry["trans"]:
                entry["trans"] = vp.get("transmission", "")
                if entry["trans"]:
                    entry["transSrc"] = "vin"
            entry["vpicTrim"] = vp.get("trim", "")
            entry["vpicTrimQuality"] = vp.get("trimQuality", "")
            # True when VPIC returned a specific trim string we trust for trim-gated parts (not OEM "all trims" blobs).
            entry["vpicDecodeWell"] = vp.get("trimQuality") == "usable"
            if vp.get("series"):
                entry["vpicSeries"] = vp["series"]
            if vp.get("driveType"):
                entry["vpicDriveType"] = vp["driveType"]
        if v.get("_vpic_mismatch"):
            entry["vpicMismatch"] = v["_vpic_mismatch"]
        output.append(entry)
    return output


def _iso_utc_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


LIFESPAN_MIN_N = 30  # departures needed before a yard/chain average is trusted


def _yard_lifespan_lookup() -> dict[str, tuple[int, str]]:
    """{location: (avg_days, basis)} for the crush-risk signal, resolved with a
    minimum-sample guard: a yard's own average needs >= LIFESPAN_MIN_N departed
    vehicles; otherwise fall back to its chain's average, then the global one.
    The basis ("yard" / "chain" / "all") ships to the UI so the copy can say
    which average it's quoting. Empty dict when the history DB is missing or
    has no usable departures yet — the UI simply shows nothing."""
    try:
        try:
            import db as _db
        except ImportError:
            from scraper import db as _db  # pragma: no cover
        stats = _db.lifespan_stats()
    except Exception as e:
        print(f"  [lifespan] history DB unavailable ({e}) — skipping crush-risk data", file=sys.stderr)
        return {}
    g_avg, g_n = stats["global"]
    out: dict[str, tuple[int, str]] = {}
    # Resolve for every yard the DB knows; the payload builder only reads the
    # ones present in the current scan.
    known_locs = set(stats["yards"]) | set()
    def resolve(loc: str) -> tuple[int, str] | None:
        y = stats["yards"].get(loc)
        if y and y[1] >= LIFESPAN_MIN_N:
            return round(y[0]), "yard"
        chain = loc.split(" - ")[0].strip()
        c = stats["chains"].get(chain)
        if c and c[1] >= LIFESPAN_MIN_N:
            return round(c[0]), "chain"
        if g_n >= LIFESPAN_MIN_N:
            return round(g_avg), "all"
        return None
    for loc in known_locs:
        r = resolve(loc)
        if r:
            out[loc] = r
    n_yard = sum(1 for v in out.values() if v[1] == "yard")
    print(
        f"  [lifespan] global avg {round(g_avg, 1)}d over {g_n} departures; "
        f"{n_yard} yard(s) have their own average (n>={LIFESPAN_MIN_N})",
        file=sys.stderr,
    )
    out["__global__"] = (round(g_avg), "all") if g_n >= LIFESPAN_MIN_N else None
    out["__chains__"] = {k: (round(a), "chain") for k, (a, n) in stats["chains"].items() if n >= LIFESPAN_MIN_N}
    return out


def compact_inventory_v2(entries: list[dict]) -> dict:
    """Schema v2: dedupe yards + part lists into lookup tables and store vehicles
    as flat arrays. Identical part lists repeat across every vehicle of the same
    model (~13 MB of the v1 file), and yard name/city/state/coords repeat per
    vehicle, so v2 is roughly 5x smaller before gzip."""
    lifespans = _yard_lifespan_lookup()
    ls_global = lifespans.pop("__global__", None)
    ls_chains = lifespans.pop("__chains__", {})

    def yard_lifespan(loc: str) -> tuple[int, str] | None:
        if loc in lifespans:
            return lifespans[loc]
        chain = loc.split(" - ")[0].strip()
        if chain in ls_chains:
            return ls_chains[chain]
        return ls_global

    yards: list[list] = []
    extras: dict[str, list] = {}
    yard_idx: dict[tuple, int] = {}
    part_sets: list[list[dict]] = []
    part_set_idx: dict[str, int] = {}
    rows: list[list] = []
    vpic: dict[str, list] = {}

    for e in entries:
        ykey = (e.get("location", ""), e.get("city", ""), e.get("state", ""),
                e.get("lat"), e.get("lng"))
        yi = yard_idx.get(ykey)
        if yi is None:
            yi = len(yards)
            yard_idx[ykey] = yi
            ls = yard_lifespan(ykey[0]) if ykey[0] else None
            # Columns 5/6: avg lot lifespan (days) + basis ("yard"/"chain"/"all")
            # for the crush-risk signal; null when there's no usable history.
            yards.append([ykey[0], ykey[1], ykey[2], ykey[3], ykey[4],
                          ls[0] if ls else None, ls[1] if ls else None])

        parts = e.get("topParts") or []
        pi = -1
        if parts:
            pkey = json.dumps(parts, sort_keys=True)
            pi = part_set_idx.get(pkey, -1)
            if pi < 0:
                pi = len(part_sets)
                part_set_idx[pkey] = pi
                part_sets.append(parts)

        # Photo/color/engine/trans(+src) ride in a separate lazy shard keyed
        # by vehicle id — the main payload stays byte-identical for cars
        # without enrichment. transSrc is non-empty exactly when trans is,
        # so the trailing-empty trim below never strands it.
        ex = [e.get("photo", ""), e.get("color", ""), e.get("engine", ""),
              e.get("trans", ""), e.get("transSrc", "")]
        while ex and not ex[-1]:
            ex.pop()
        if ex:
            extras[str(e.get("id"))] = ex

        row_i = len(rows)
        rows.append([
            e.get("id"),
            e.get("vin", ""),
            e.get("year"),
            e.get("make", ""),
            e.get("model", ""),
            e.get("row", ""),
            str(e.get("dateAdded", ""))[:10],
            yi,
            pi,
            e.get("maxValue", 0),
            1 if e.get("utpapPremium") else 0,
        ])
        # Only rows with UI-relevant decode data get a side-table entry; empty
        # decodes (no trim/series/drive and no mismatch) would bloat the file
        # now that every cached VIN carries a decode.
        if (e.get("vpicTrim") or e.get("vpicSeries") or e.get("vpicDriveType")
                or e.get("vpicMismatch") or e.get("vpicTrimQuality") == "ambiguous"):
            vpic[str(row_i)] = [
                e.get("vpicTrim", ""),
                e.get("vpicTrimQuality", ""),
                e.get("vpicSeries", ""),
                e.get("vpicDriveType", ""),
                e.get("vpicMismatch", ""),
            ]

    return {
        "schemaVersion": 2,
        "scrapedAt": _iso_utc_z(),
        "pricesLastReviewed": PRICES_LAST_REVIEWED,
        "fields": ["id", "vin", "year", "make", "model", "row", "dateAdded",
                   "yard", "partSet", "maxValue", "premium"],
        "yardFields": ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"],
        "yards": yards,
        "partSets": part_sets,
        "vpic": vpic,
        "vehicles": rows,
        "_extras": extras,
    }


def build_inventory_json_payload(vehicles: list[dict], only_matches: bool) -> dict:
    """Wrapper written to inventory_live.json: metadata + vehicle rows."""
    return compact_inventory_v2(output_json(vehicles, only_matches=only_matches))


# --- Stale-keep: never publish a vanished yard -------------------------------
# 2026-10-21 incident: one scan hit transient source failures (Pull-N-Save's
# makes API down, Budget Winter Garden serving an unparseable page) and the
# published inventory silently dropped 9 yards / 13k vehicles — including a
# yard the owner was actively pitching. A yard that fetched fine 3 hours
# earlier must not vanish from the app because of one bad fetch: carry the
# previously published rows forward (loudly) until the source recovers or the
# carry cap is hit.
STALE_KEEP_FLOOR = 0.40      # carry forward when a yard returns <40% of its previous count
STALE_KEEP_MIN_PREV = 25     # ignore tiny yards (legit fluctuation, not failure signal)
STALE_KEEP_MAX_SCANS = 30    # stop carrying after ~30 consecutive frozen scans (~5 days @4h)


def merge_carryforward_yards(new_payload: dict, prev_payload: dict,
                             yard_names: list[str],
                             new_extras: dict | None = None,
                             prev_extras: dict | None = None) -> dict[str, int]:
    """Replace/insert the given yards in new_payload with their rows from
    prev_payload (the last published inventory). Mutates new_payload (and
    new_extras when given) in place; returns {yard_name: carried_row_count}.

    Handles the compact v2 format's cross-references: yard + partSet indices
    are remapped, vpic entries (keyed by ROW index) are reindexed when
    existing rows are removed, and extras (keyed by vehicle id) follow their
    vehicles."""
    f = new_payload["fields"]
    if f != prev_payload["fields"]:
        raise ValueError("field layout changed between payloads — cannot carry forward")
    i_id, i_yard, i_pset = f.index("id"), f.index("yard"), f.index("partSet")
    targets = set(yard_names)
    new_names = [y[0] for y in new_payload["yards"]]
    prev_names = [y[0] for y in prev_payload["yards"]]

    # 1) Drop any rows the fresh scan DID produce for the target yards (the
    #    <40% collapse case), reindexing vpic keys around the removals.
    target_idx_new = {i for i, n in enumerate(new_names) if n in targets}
    kept_rows: list[list] = []
    row_map: dict[int, int] = {}
    removed_ids: set[str] = set()
    for old_i, row in enumerate(new_payload["vehicles"]):
        if row[i_yard] in target_idx_new:
            removed_ids.add(str(row[i_id]))
            continue
        row_map[old_i] = len(kept_rows)
        kept_rows.append(row)
    new_payload["vehicles"] = kept_rows
    new_payload["vpic"] = {str(row_map[int(k)]): v
                           for k, v in (new_payload.get("vpic") or {}).items()
                           if int(k) in row_map}
    if new_extras is not None:
        for rid in removed_ids:
            new_extras.pop(rid, None)

    # 2) Append the previous payload's rows for each target yard.
    pset_idx = {json.dumps(p, sort_keys=True): i
                for i, p in enumerate(new_payload["partSets"])}
    name_to_new_yard = {n: i for i, n in enumerate(new_names)}
    prev_vpic = prev_payload.get("vpic") or {}
    carried: dict[str, int] = {}
    for yname in yard_names:
        if yname not in prev_names:
            continue
        prev_yi = prev_names.index(yname)
        if yname in name_to_new_yard:
            new_yi = name_to_new_yard[yname]
            new_payload["yards"][new_yi] = prev_payload["yards"][prev_yi]
        else:
            new_yi = len(new_payload["yards"])
            new_payload["yards"].append(prev_payload["yards"][prev_yi])
            name_to_new_yard[yname] = new_yi
        n = 0
        for prev_i, row in enumerate(prev_payload["vehicles"]):
            if row[i_yard] != prev_yi:
                continue
            new_row = list(row)
            new_row[i_yard] = new_yi
            pi = row[i_pset]
            if pi is not None and pi >= 0:
                pkey = json.dumps(prev_payload["partSets"][pi], sort_keys=True)
                npi = pset_idx.get(pkey)
                if npi is None:
                    npi = len(new_payload["partSets"])
                    pset_idx[pkey] = npi
                    new_payload["partSets"].append(prev_payload["partSets"][pi])
                new_row[i_pset] = npi
            new_ri = len(new_payload["vehicles"])
            new_payload["vehicles"].append(new_row)
            pv = prev_vpic.get(str(prev_i))
            if pv is not None:
                new_payload["vpic"][str(new_ri)] = pv
            if new_extras is not None and prev_extras:
                pe = prev_extras.get(str(new_row[i_id]))
                if pe is not None:
                    new_extras[str(new_row[i_id])] = pe
            n += 1
        carried[yname] = n
    return carried


def apply_stale_keep(payload: dict, extras: dict) -> None:
    """Compare the fresh payload against the last published LIVE_FILE and carry
    forward any yard that vanished or collapsed below STALE_KEEP_FLOOR of its
    previous count. Mutates payload/extras in place. Loud by design."""
    try:
        prev = json.loads(LIVE_FILE.read_text())
    except Exception:
        return
    try:
        prev_extras = json.loads(EXTRAS_FILE.read_text()).get("extras", {})
    except Exception:
        prev_extras = {}
    try:
        health = json.loads(YARD_HEALTH_FILE.read_text()).get("yards", {})
    except Exception:
        health = {}

    i_yard = payload["fields"].index("yard")
    def _counts(p):
        names = [y[0] for y in p["yards"]]
        c: dict[str, int] = {}
        for row in p["vehicles"]:
            n = names[row[i_yard]]
            c[n] = c.get(n, 0) + 1
        return c
    prev_counts, new_counts = _counts(prev), _counts(payload)

    to_carry: list[str] = []
    for name, pc in sorted(prev_counts.items()):
        if pc < STALE_KEEP_MIN_PREV:
            continue
        nc = new_counts.get(name, 0)
        if nc >= STALE_KEEP_FLOOR * pc:
            continue
        frozen = int((health.get(name) or {}).get("unchangedScans", 0))
        if frozen >= STALE_KEEP_MAX_SCANS:
            print(f"  ⚠️  STALE-KEEP GIVING UP: {name} — frozen for {frozen} scans "
                  f"(cap {STALE_KEEP_MAX_SCANS}); publishing the fetched count ({nc}) as-is",
                  file=sys.stderr)
            continue
        to_carry.append(name)

    if not to_carry:
        return
    carried = merge_carryforward_yards(payload, prev, to_carry,
                                       new_extras=extras, prev_extras=prev_extras)
    for name in to_carry:
        print(f"  ⚠️  STALE-KEEP: {name} fetched {new_counts.get(name, 0)} vehicles "
              f"(previously {prev_counts[name]}) — carrying forward {carried.get(name, 0)} "
              f"previously published rows; fix the adapter/source", file=sys.stderr)
    print(f"  ⚠️  stale-keep carried {len(to_carry)} yard(s); "
          f"see docs/data/yard_health.json", file=sys.stderr)


YARD_HEALTH_FILE = DATA_DIR / "yard_health.json"
# A yard whose vehicle set is byte-identical for this many CONSECUTIVE scans
# (~1 day at the 4h cadence) while its source keeps serving 200s is almost
# always upstream index lag or a silently-broken adapter, not a quiet yard:
# the PnP SLC national-index freeze of 2026-10-19..21 served an identical
# 964-car set for 6 straight scans and hid a watched 4Runner for two days.
YARD_STALE_SCANS = 6
# Drop vanished yards from the health file after this many scans missing
# (closed/renamed yards shouldn't haunt the report forever).
YARD_MISSING_DROP = 30


def _update_yard_health(payload: dict) -> None:
    """Per-yard change tracking -> docs/data/yard_health.json (committed by the
    scan workflow along with the rest of docs/data/). Compares each yard's
    vehicle-set fingerprint against the previous scan's and shouts in the scan
    log when a yard has been frozen for YARD_STALE_SCANS+ scans or has
    disappeared from the scrape entirely."""
    prev: dict = {}
    try:
        prev = json.loads(YARD_HEALTH_FILE.read_text()).get("yards", {})
    except Exception:
        pass

    names = [y[0] for y in payload["yards"]]
    per_yard: dict[str, list[str]] = {n: [] for n in names}
    for row in payload["vehicles"]:
        # id + dateAdded: catches adds, removals AND date corrections.
        per_yard[names[row[7]]].append(f"{row[0]}|{row[6]}")

    now = payload["scrapedAt"]
    yards_out: dict[str, dict] = {}
    stale: list[tuple[int, str, int]] = []
    for n in names:
        fp = hashlib.sha1("\n".join(sorted(per_yard[n])).encode()).hexdigest()[:16]
        p = prev.get(n) or {}
        if p.get("fingerprint") == fp:
            unchanged = int(p.get("unchangedScans", 0)) + 1
            last_changed = p.get("lastChangedAt") or now
        else:
            unchanged = 0
            last_changed = now
        yards_out[n] = {"count": len(per_yard[n]), "fingerprint": fp,
                        "unchangedScans": unchanged, "lastChangedAt": last_changed}
        if unchanged >= YARD_STALE_SCANS:
            stale.append((unchanged, n, len(per_yard[n])))

    missing: list[tuple[int, str]] = []
    for n, p in prev.items():
        if n in yards_out:
            continue
        miss = int(p.get("missingScans", 0)) + 1
        if miss > YARD_MISSING_DROP:
            continue
        yards_out[n] = {**{k: p[k] for k in ("count", "fingerprint", "lastChangedAt") if k in p},
                        "unchangedScans": int(p.get("unchangedScans", 0)),
                        "missingScans": miss}
        missing.append((miss, n))

    YARD_HEALTH_FILE.write_text(json.dumps(
        {"schemaVersion": 1, "scrapedAt": now, "staleAfterScans": YARD_STALE_SCANS,
         "yards": yards_out}, separators=(",", ":"), sort_keys=True))

    for unchanged, n, ct in sorted(stale, reverse=True):
        print(f"  ⚠️  STALE YARD: {n} — identical {ct}-vehicle set for "
              f"{unchanged + 1} consecutive scans (since {yards_out[n]['lastChangedAt']}); "
              f"source may be serving a lagging index", file=sys.stderr)
    for miss, n in sorted(missing, reverse=True):
        print(f"  ⚠️  MISSING YARD: {n} — absent from the last {miss} scan(s); "
              f"adapter may be silently failing", file=sys.stderr)
    if stale or missing:
        print(f"  ⚠️  yard health: {len(stale)} stale, {len(missing)} missing — "
              f"see docs/data/yard_health.json", file=sys.stderr)


def print_rich(vehicles: list[dict], show_all: bool = False):
    console = Console()
    console.print()
    console.print(Panel.fit(
        "[bold yellow]YardScout[/] — Live Inventory Scan\n"
        "[dim]Pick-n-Pull + Pick Your Part + Pull-A-Part + Utah chains | No engines, no trans — carryable parts only[/]",
        border_style="yellow",
    ))

    hits = [v for v in vehicles if v.get("_matches")]
    hits.sort(key=lambda v: v.get("_max_value", 0), reverse=True)

    console.print(f"\n[bold]Scanned:[/] {len(vehicles)} vehicles | "
                  f"[bold green]{len(hits)} unobtanium matches[/] | "
                  f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    if hits:
        table = Table(box=box.ROUNDED, show_lines=True, title="Unobtanium Matches", title_style="bold green")
        table.add_column("Year", width=5)
        table.add_column("Vehicle", style="bold white", width=22)
        table.add_column("Location", style="cyan", width=18)
        table.add_column("Row", width=4, justify="center")
        table.add_column("Added", width=10)
        table.add_column("Top Parts", width=34)
        table.add_column("Max$", justify="right", style="bold green", width=7)

        for v in hits[:40]:
            parts_str = "\n".join(
                f"  [{p['rarity']}] {p['name']}: ${p['low']}–${p['high']}"
                for p in v.get("_top_parts", [])[:3]
            )
            date_str = ""
            da = v.get("dateAdded", "")
            if da:
                date_str = da[:10]
            table.add_row(
                str(v.get("year", "?")),
                f"{v.get('make', '')} {v.get('model', '')}",
                v.get("_location", "").replace("Pick-n-Pull - ", "PnP "),
                str(v.get("row", "")),
                date_str,
                parts_str,
                f"${v.get('_max_value', 0):,}",
            )
        console.print(table)

    if show_all:
        console.print(f"\n[bold]All {len(vehicles)} vehicles:[/]")
        no_match = [v for v in vehicles if not v.get("_matches")]
        for v in sorted(no_match, key=lambda x: (x.get("make", ""), x.get("model", ""), x.get("year", 0))):
            console.print(f"  [dim]{v.get('year', '?')} {v.get('make', '')} {v.get('model', '')} "
                          f"@ {v.get('_location', '').replace('Pick-n-Pull - ', 'PnP ')} row {v.get('row', '?')}[/]")


def print_plain(vehicles: list[dict]):
    hits = [v for v in vehicles if v.get("_matches")]
    hits.sort(key=lambda v: v.get("_max_value", 0), reverse=True)
    print(f"\n{'='*60}")
    print(f"  YARDSCOUT — Live Scan")
    print(f"  {len(vehicles)} vehicles | {len(hits)} matches")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    for v in hits:
        print(f"  ** {v['year']} {v['make']} {v['model']} **")
        print(f"     {v.get('_location', '')} | Row {v.get('row', '?')} | Added {v.get('dateAdded', '')[:10]}")
        for p in v.get("_top_parts", [])[:3]:
            print(f"       [{p['rarity']}] {p['name']}: ${p['low']}–${p['high']} (yard ~${p['cost']})")
        print()


# Toyota motor hunt — yards don't list engine codes; use model + year bands, then verify in person.
ENGINE_HUNT_RULES: list[tuple[str, str, str, int, int]] = [
    ("22RE-era Pickup", "Toyota", "Pickup", 1984, 1995),
    ("22RE-era 4Runner", "Toyota", "4Runner", 1984, 1995),
    ("3RZ-era Tacoma", "Toyota", "Tacoma", 1995, 2004),
    ("3RZ-era 4Runner", "Toyota", "4Runner", 1996, 2002),
    ("3RZ-era T100", "Toyota", "T100", 1995, 2000),
]


def print_engine_hunt_report(vehicles: list[dict]) -> None:
    """Stderr summary of Toyota rows that could match 22RE / 3RZ (always confirm in yard)."""
    print("\n  --- Toyota motor hunt (22RE / 3RZ candidates — verify engine before pulling) ---", file=sys.stderr)
    for label, make, model_sub, ylo, yhi in ENGINE_HUNT_RULES:
        hits = []
        mk = make.lower()
        msub = model_sub.lower()
        for v in vehicles:
            if mk not in (v.get("make") or "").lower():
                continue
            if msub not in (v.get("model") or "").lower():
                continue
            y = int(v.get("year") or 0)
            if y < ylo or y > yhi:
                continue
            hits.append(v)
        print(f"  {label}: {len(hits)} in yard", file=sys.stderr)
        for v in sorted(hits, key=lambda x: (-(x.get("year") or 0), (x.get("model") or "")))[:15]:
            loc = (v.get("_location") or "")[:52]
            vin = (v.get("vin") or "").strip()
            print(f"    {v.get('year')} {v.get('make')} {v.get('model')}  VIN {vin}  @ {loc}", file=sys.stderr)
        if len(hits) > 15:
            print(f"    … +{len(hits) - 15} more", file=sys.stderr)
    print("  --- end motor hunt ---\n", file=sys.stderr)


WATCHLIST_FILE = SCRIPT_DIR / "watchlist.json"
# In GitHub Actions, persist alert dedupe in-repo so emails don't repeat every run.
WATCH_ALERTED_FILE = (
    SCRIPT_DIR / "watch_alerted.json"
    if os.environ.get("GITHUB_ACTIONS") == "true"
    else CACHE_DIR / "watch_alerted.json"
)


def load_watchlist() -> list[dict]:
    """Load the watchlist from watchlist.json (synced from the web UI or hand-edited)."""
    if WATCHLIST_FILE.exists():
        try:
            return json.loads(WATCHLIST_FILE.read_text())
        except Exception:
            pass
    return []


def _load_watch_alerted() -> dict:
    CACHE_DIR.mkdir(exist_ok=True)
    if WATCH_ALERTED_FILE.exists():
        try:
            return json.loads(WATCH_ALERTED_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_watch_alerted(alerted: dict):
    CACHE_DIR.mkdir(exist_ok=True)
    WATCH_ALERTED_FILE.write_text(json.dumps(alerted, indent=2))


def _macos_notify(title: str, message: str, sound: str = "Glass"):
    """Send a macOS notification via osascript."""
    import subprocess
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, capture_output=True)
    except Exception:
        pass


def _smtp_configured() -> bool:
    return bool(
        os.environ.get("SMTP_USER")
        and os.environ.get("SMTP_PASS")
        and os.environ.get("ALERT_EMAIL")
    )


def _ntfy_configured() -> bool:
    return bool(os.environ.get("NTFY_TOPIC"))


def send_push_alert(title: str, message: str, priority: str = "default") -> bool:
    """Phone push via ntfy.sh — free, no account. Set NTFY_TOPIC env var to a
    hard-to-guess topic name (e.g. yardscout-bv-8k2j) and subscribe to
    the same topic in the ntfy iOS/Android app. Works from laptop or CI."""
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return False
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority, "Tags": "car,wrench"},
            timeout=10,
        )
        return True
    except Exception:
        return False


def send_email_alert(subject: str, body: str) -> bool:
    """Send email via Gmail SMTP. Requires SMTP_USER, SMTP_PASS, ALERT_EMAIL env vars."""
    if not _smtp_configured():
        return False
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    to_addr = os.environ["ALERT_EMAIL"]
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"  Email alert failed: {e}", file=sys.stderr)
        return False


def _format_vehicle_email_body(v: dict) -> str:
    lines = [
        f"{v.get('year')} {v.get('make', '')} {v.get('model', '')}",
        f"Location: {v.get('_location', '')}",
    ]
    if v.get("row"):
        lines.append(f"Row: {v.get('row')}")
    da = v.get("dateAdded") or ""
    if da:
        lines.append(f"Added: {da[:10]}")
    parts = v.get("_top_parts") or []
    if parts:
        lines.append("")
        lines.append("Unobtanium parts:")
        for p in parts[:12]:
            low, high = p.get("low"), p.get("high")
            cost = p.get("cost", "?")
            lines.append(f"  - {p.get('name', '')}: ${low}–${high} (yard ~${cost})")
            if p.get("sell_at"):
                lines.append(f"    → Sell on: {p['sell_at']}")
        haul = sum(p.get("high", 0) for p in parts)
        lines.append("")
        lines.append(f"Total resale ceiling (all parts): ~${haul:,}")
    return "\n".join(lines)


def check_watchlist_alerts(vehicles: list[dict]):
    """Check vehicles against the watchlist. Collects all new hits first, then
    notifies: macOS banners (capped), phone push via ntfy (capped), and ONE
    digest email per run — a national scan can produce dozens of first-time
    hits and per-vehicle emails would be spam.

    Watchlist entries support an optional "states" list (e.g. ["UT", "NV"])
    to scope alerts geographically on national scans."""
    watchlist = load_watchlist()
    if not watchlist:
        return

    alerted = _load_watch_alerted()
    hits: list[dict] = []

    for entry in watchlist:
        # Vehicles are already make+model-normalized by enrich_vehicles; run
        # the watch entry through the same aliasing so a watch saved as "Vw",
        # "MINI Cooper", or "Mazda 3" still hits post-merge inventory.
        make_low = normalize_make(entry.get("make") or "").lower()
        model_low = normalize_model(
            entry.get("model") or "", entry.get("make") or "").lower()
        yr_min = entry.get("yrMin")
        yr_max = entry.get("yrMax")
        match_only = entry.get("matchOnly", False)
        states = {s.upper() for s in (entry.get("states") or [])}

        for v in vehicles:
            if make_low and make_low not in (v.get("make") or "").lower():
                continue
            if model_low and model_low not in (v.get("model") or "").lower():
                continue
            year = v.get("year", 0)
            if yr_min and year < yr_min:
                continue
            if yr_max and year > yr_max:
                continue
            if match_only and not v.get("_matches"):
                continue
            if states and (v.get("_state") or "").upper() not in states:
                continue

            key = f"{v.get('id', '')}:{v.get('vin', '')}:{year}:{v.get('make', '')}:{v.get('model', '')}"
            if key in alerted:
                continue

            alerted[key] = datetime.now().isoformat()
            hits.append(v)

    if not hits:
        return

    def _vname(v):
        return f"{v.get('year')} {v.get('make', '')} {v.get('model', '')}"

    def _vloc(v):
        return (v.get("_location") or "").replace("Pick-n-Pull - ", "PnP ")

    for v in hits:
        has_parts = " — has unobtanium!" if v.get("_matches") else ""
        print(f"  🔔 ALERT: {_vname(v)} at {_vloc(v)}{has_parts}", file=sys.stderr)

    # macOS banners: first few only
    for v in hits[:5]:
        has_parts = " — has unobtanium!" if v.get("_matches") else ""
        _macos_notify("YardScout", f"{_vname(v)} at {_vloc(v)}{has_parts}")
    if len(hits) > 5:
        _macos_notify("YardScout", f"...and {len(hits) - 5} more watchlist hits")

    # Phone push: individual up to 12, otherwise one summary
    if _ntfy_configured():
        if len(hits) <= 12:
            for v in hits:
                state = v.get("_state") or ""
                send_push_alert(
                    f"{_vname(v)} hit the yard",
                    f"{_vloc(v)} ({state})" + (f" — Row {v.get('row')}" if v.get("row") else "")
                    + (f"\nParts value up to ${v.get('_max_value'):,}" if v.get("_max_value") else ""),
                    priority="high" if v.get("_matches") else "default",
                )
        else:
            top = "\n".join(f"• {_vname(v)} — {_vloc(v)}" for v in hits[:10])
            send_push_alert(
                f"{len(hits)} watchlist vehicles hit yards",
                top + f"\n...and {len(hits) - 10} more",
                priority="high",
            )
        print(f"  📱 Push sent via ntfy ({min(len(hits), 12) if len(hits) <= 12 else 1} notification(s))", file=sys.stderr)

    # Email: single digest
    if _smtp_configured():
        bodies = [_format_vehicle_email_body(v) for v in hits]
        digest = f"{len(hits)} new watchlist hit(s):\n\n" + "\n\n---\n\n".join(bodies)
        subj = (f"YardScout alert: {_vname(hits[0])} at {_vloc(hits[0])}"
                if len(hits) == 1 else f"YardScout alert: {len(hits)} new watchlist hits")
        if send_email_alert(subj, digest):
            print(f"  📧 Digest email sent ({len(hits)} vehicles)", file=sys.stderr)

    _save_watch_alerted(alerted)
    print(f"  🔔 {len(hits)} new watchlist alert(s)", file=sys.stderr)


def _record_scan_to_db(vehicles: list[dict], scraped_at: str) -> None:
    """Record full scan history into inventory_history.db (SQLite).
    History always stores ALL vehicles regardless of --all, so departures are accurate."""
    try:
        from db import record_scan, summary
        entries = output_json(vehicles, only_matches=False)
        stats = record_scan(entries, scraped_at)
        print(
            f"  DB: +{stats['new_arrivals']} new arrivals, "
            f"{stats['departures']} departed (crushed/pulled). {summary()}",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"  DB: history recording failed ({exc}) — JSON output unaffected", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="YardScout — live self-service junkyard scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true", help="Include non-matching vehicles in output")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=21600)
    parser.add_argument("--list-parts", action="store_true")
    parser.add_argument("--make", type=str)
    parser.add_argument("--save", action="store_true", help="Save JSON to inventory_live.json for the web UI")
    parser.add_argument(
        "--refresh-utpap-pricing",
        action="store_true",
        help="Fetch utpap.com pricelist (1064Carpricelist.php) and write utpap_pricing.json, then exit",
    )
    parser.add_argument(
        "--refresh-chain-pricing",
        action="store_true",
        help="Fetch chain price lists (Pick-n-Pull, LKQ Pick Your Part, Pull-A-Part) and write picknpull_pricing.json / pyp_pricing.json / pap_pricing.json, then exit",
    )
    parser.add_argument(
        "--decode-vins",
        action="store_true",
        help="NHTSA VPIC decode per VIN for trim-aware matching (parallel; tune VPIC_WORKERS / VPIC_DELAY_SEC)",
    )
    parser.add_argument(
        "--decode-vins-incremental",
        action="store_true",
        help="Trim-aware matching using the persistent VIN decode cache (inventory_history.db): "
             "cached VINs cost zero API calls; only never-seen VINs are decoded, newest arrivals "
             "first, capped per run by VPIC_MAX_PER_RUN (default 5000)",
    )
    parser.add_argument(
        "--decode-vins-profit-top",
        type=int,
        default=0,
        metavar="N",
        help="Decode VPIC only for VINs in the top N vehicle rows by carry-out profit (after matching; skips full-fleet decode)",
    )
    parser.add_argument(
        "--national",
        action="store_true",
        help="Scan every supported chain nationwide: Pick-n-Pull US+Canada, LKQ Pick Your Part (~60 yards), Pull-A-Part (~36 yards incl. former U-Pull-&-Pay). Without this flag, only the SLC-radius chains are scanned.",
    )
    parser.add_argument(
        "--independents",
        action="store_true",
        help="Also scan onboarded independent yards (Wrench-A-Part TX, U-Pull-R Parts MN/OH, Fenix U-Pull NY/GA, Harry's U-Pull-It PA, Indy-U-Pull-It IN, U-Pull-It IA/NE, Rupert's U-Pull-It VA, Pull-N-Save UT/AZ/CA, Parts Galore MI, Ace Pick-A-Part FL, Sturtevant Auto WI, iPull-uPull CA, St. Cloud U Pull MN, Nevada Pic-A-Part NV, VinPlus platform KY/TN/NC/TX/AR/LA/IL/VA/FL/GA (Bessler's, Bluegrass, Raceway, RTP Maiden, Pickers, Pipes, Joliet U-Pull-It, San Antonio Pick-N-Pull, 195 Used Auto Parts, Pick Ur Part, Chesterfield Auto Parts, Go Pull-It), Pick-A-Part VA, U-Pick-It AZ, Barry's U Pull It AL, Prestige Pull-Your-Part TX, Budget U-Pull-It FL — see scraper/independent_yards_registry.json). Opt-in so the scheduled scan enables them deliberately; JUNKYARD_INDEPENDENTS=1 works too.",
    )
    args = parser.parse_args()

    if args.refresh_utpap_pricing:
        path = refresh_utpap_pricing_file()
        n = len(json.loads(path.read_text()))
        print(f"Wrote {n} price rows to {path}", file=sys.stderr)
        return

    if args.refresh_chain_pricing:
        # Each chain refreshes independently: one chain's website being down
        # (e.g. Pull-A-Part serving its 500 page, which killed the 2026-09-16
        # 03:10 UTC scan) must not abort the others or fail the workflow —
        # yesterday's cached prices are strictly better than no scan at all.
        failures = []
        fns = (refresh_pnp_pricing_file, refresh_pyp_pricing_file,
               refresh_pap_pricing_file, refresh_wap_pricing_file,
               refresh_upullr_pricing_file, refresh_fenix_pricing_file,
               refresh_harrys_pricing_file, refresh_indy_pricing_file,
               refresh_upullitne_pricing_file, refresh_ruperts_pricing_file,
               refresh_pns_pricing_file, refresh_partsgalore_pricing_file,
               refresh_chesterfield_pricing_file, refresh_ace_pricing_file,
               refresh_sturtevant_pricing_file, refresh_nvpap_pricing_file,
               refresh_barrys_pricing_file, refresh_budget_pricing_file,
               refresh_p195_pricing_file, refresh_pnpsa_pricing_file)
        for fn in fns:
            try:
                fn()
            except Exception as e:  # noqa: BLE001 — upstream sites, anything goes
                failures.append(f"{fn.__name__}: {e}")
                print(f"WARNING: {fn.__name__} failed ({e}) — keeping previous price file", file=sys.stderr)
        if failures:
            print(f"{len(failures)} of {len(fns)} chain price refreshes failed; previous files kept.", file=sys.stderr)
        return

    if args.list_parts:
        seen = set()
        entries = []
        for kw, info in sorted(UNOBTANIUM_DB.items(), key=lambda x: _max_entry_calibrated_high(x[1]), reverse=True):
            if info["display"] in seen:
                continue
            if args.make and args.make.lower() not in info["make"].lower():
                continue
            seen.add(info["display"])
            entries.append(info)

        if HAS_RICH:
            console = Console()
            table = Table(
                title="Tracked Unobtanium — resale bands (JUNKYARD_RAW_PRICES=1 for raw DB)",
                box=box.ROUNDED, show_lines=True,
            )
            table.add_column("Vehicle", style="bold")
            table.add_column("Make", style="cyan")
            table.add_column("Years")
            table.add_column("Top Parts")
            table.add_column("Max", justify="right", style="bold green")
            for info in entries:
                ymid = (info["year_range"][0] + info["year_range"][1]) // 2
                lines = []
                for p in info["top_parts"][:4]:
                    lo, hi = _resale_sold_calibrate(p["low"], p["high"], p["name"], ymid)
                    lines.append(f"  {p['name']}: ${lo}–${hi}")
                ps = "\n".join(lines)
                mx = _max_entry_calibrated_high(info)
                table.add_row(info["display"], info["make"],
                              f"{info['year_range'][0]}–{info['year_range'][1]}", ps, f"${mx:,}")
            console.print(table)
        else:
            for info in entries:
                ymid = (info["year_range"][0] + info["year_range"][1]) // 2
                mx = _max_entry_calibrated_high(info)
                print(f"\n{info['display']} [{info['make']}] ({info['year_range'][0]}–{info['year_range'][1]})")
                for p in info["top_parts"][:4]:
                    lo, hi = _resale_sold_calibrate(p["low"], p["high"], p["name"], ymid)
                    print(f"  - {p['name']}: ${lo}–${hi} ({p['rarity']})")
                print(f"  Max: ${mx:,}")
        return

    decode_vins_profit_top = max(0, int(args.decode_vins_profit_top or 0))
    decode_vins_incremental = bool(args.decode_vins_incremental) or (
        os.environ.get("JUNKYARD_DECODE_INCREMENTAL", "").strip().lower() in ("1", "true", "yes")
    )
    decode_vins = (
        (bool(args.decode_vins) or os.environ.get("JUNKYARD_DECODE_VINS", "").strip().lower() in (
            "1", "true", "yes",
        ))
        and decode_vins_profit_top == 0
        and not decode_vins_incremental
    )

    scan_independents = bool(args.independents) or (
        os.environ.get("JUNKYARD_INDEPENDENTS", "").strip().lower() in ("1", "true", "yes")
    )

    def do_scan():
        # The independents (~22 adapters, all on hosts distinct from the big
        # chains) are the slowest fetch by far, so they start FIRST in a
        # background thread and the chain scans run on top of them: total
        # fetch wall-clock = max(chains, independents) instead of the sum.
        # Output order is unchanged — independents are still appended last.
        indep_fut = None
        indep_pool = None
        if scan_independents:
            print("Scanning independent yards (Wrench-A-Part, U-Pull-R, Fenix, Harry's, Indy, U-Pull-It IA/NE, Rupert's, Pull-N-Save, Parts Galore, Ace, Sturtevant, iPull-uPull, St. Cloud, Nevada Pic-A-Part, VinPlus x20 incl. Chesterfield + Go Pull-It, Pick-A-Part VA, U-Pick-It AZ, Barry's, Prestige, Budget) in the background, overlapped with the chain scans...", file=sys.stderr)
            indep_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="indep-main")
            indep_fut = indep_pool.submit(fetch_independent_inventory)

        scope = "NATIONAL (all US+Canada yards)" if args.national else "SLC"
        print(f"Scanning Pick-n-Pull {scope}...", file=sys.stderr)
        pnp_vehicles = fetch_pnp_inventory(national=args.national)
        print(f"  Found {len(pnp_vehicles)} vehicles from Pick-n-Pull", file=sys.stderr)

        print("Scanning Tear-A-Part (SLC + Ogden)...", file=sys.stderr)
        tap_vehicles = fetch_tearapart_inventory()
        print(f"  Found {len(tap_vehicles)} vehicles from Tear-A-Part", file=sys.stderr)

        print("Scanning Utah Pic-A-Part (Ogden + Orem)...", file=sys.stderr)
        utpap_vehicles = fetch_utpap_inventory()

        pyp_vehicles: list[dict] = []
        pap_vehicles: list[dict] = []
        if args.national:
            # National-only chains: no yards near SLC, so skip on local scans.
            print("Scanning LKQ Pick Your Part (pyp.com, ~60 yards)...", file=sys.stderr)
            pyp_vehicles = fetch_pyp_inventory()
            print("Scanning Pull-A-Part (incl. former U-Pull-&-Pay yards)...", file=sys.stderr)
            pap_vehicles = fetch_pap_inventory()

        indep_vehicles: list[dict] = []
        if indep_fut is not None:
            indep_vehicles = indep_fut.result()
            indep_pool.shutdown()

        all_vehicles = (pnp_vehicles + tap_vehicles + utpap_vehicles
                        + pyp_vehicles + pap_vehicles + indep_vehicles)
        all_vehicles = enrich_vehicles(
            all_vehicles,
            decode_vins=decode_vins,
            decode_vins_profit_top=decode_vins_profit_top,
            decode_vins_incremental=decode_vins_incremental,
        )
        print(f"  Total: {len(all_vehicles)} vehicles combined", file=sys.stderr)
        return all_vehicles

    if args.watch:
        print(f"Watching every {args.interval // 3600}h... (Ctrl+C to stop)\n")
        while True:
            vehicles = do_scan()
            if args.json or args.save:
                payload = build_inventory_json_payload(vehicles, only_matches=not args.all)
                extras = payload.pop("_extras", {})
                if args.save:
                    apply_stale_keep(payload, extras)
                    LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
                    EXTRAS_FILE.write_text(json.dumps(
                        {"version": 1, "scrapedAt": payload["scrapedAt"],
                         "extraFields": ["photo", "color", "engine", "trans", "transSrc"],
                         "extras": extras}, separators=(",", ":")))
                    print(f"Saved {len(payload['vehicles'])} vehicles to {LIVE_FILE} (scrapedAt {payload['scrapedAt']})")
                    print(f"Saved {len(extras)} enrichment entries to {EXTRAS_FILE}")
                    write_interchange_payload()
                    _update_yard_health(payload)
                    _record_scan_to_db(vehicles, payload["scrapedAt"])
                if args.json:
                    print(json.dumps(payload, separators=(",", ":")))
            elif HAS_RICH:
                print_rich(vehicles, show_all=args.all)
            else:
                print_plain(vehicles)

            seen = load_seen()
            new_ct = 0
            for v in vehicles:
                if v.get("_matches"):
                    h = vehicle_hash(v)
                    if h not in seen:
                        seen[h] = {"first_seen": datetime.now().isoformat(),
                                   "vehicle": f"{v['year']} {v['make']} {v['model']}"}
                        new_ct += 1
            save_seen(seen)
            if new_ct:
                print(f"\n*** {new_ct} NEW unobtanium find(s)! ***")

            print_engine_hunt_report(vehicles)
            check_watchlist_alerts(vehicles)
            time.sleep(args.interval)
    else:
        vehicles = do_scan()
        print_engine_hunt_report(vehicles)
        if args.json or args.save:
            payload = build_inventory_json_payload(vehicles, only_matches=not args.all)
            extras = payload.pop("_extras", {})
            if args.save:
                apply_stale_keep(payload, extras)
                LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
                EXTRAS_FILE.write_text(json.dumps(
                    {"version": 1, "scrapedAt": payload["scrapedAt"],
                     "extraFields": ["photo", "color", "engine", "trans", "transSrc"],
                     "extras": extras}, separators=(",", ":")))
                if not args.json:
                    print(f"Saved {len(payload['vehicles'])} vehicles to {LIVE_FILE} (scrapedAt {payload['scrapedAt']})", file=sys.stderr)
                    print(f"Saved {len(extras)} enrichment entries to {EXTRAS_FILE}", file=sys.stderr)
                write_interchange_payload()
                _update_yard_health(payload)
                _record_scan_to_db(vehicles, payload["scrapedAt"])
            if args.json:
                print(json.dumps(payload, separators=(",", ":")))
        elif HAS_RICH:
            print_rich(vehicles, show_all=args.all)
        else:
            print_plain(vehicles)

        check_watchlist_alerts(vehicles)


if __name__ == "__main__":
    main()
