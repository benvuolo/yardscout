#!/usr/bin/env python3
"""
Junkyard Hunter — Self-Service Junkyard Inventory Scraper
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
import concurrent.futures
import hashlib
import json
import os
import re
import smtplib
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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

PNP_API = "https://www.picknpull.com/api"
SLC_ZIP = "84101"
SEARCH_RADIUS = 100
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
PRICES_LAST_REVIEWED = "2026-09-02"
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
    "4runner": {
        "display": "Toyota 4Runner",
        "make": "Toyota",
        "year_range": (1990, 2024),
        "top_parts": [
            {"name": "Rear E-Locker Actuator Motor", "rarity": "Legendary", "low": 250, "high": 500, "cost": 15},
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
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 200, "high": 400, "cost": 30, "yr_min": 2007},
            {"name": "Tailgate (w/ camera)", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2014},
            {"name": "JBL Speakers + Amp", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20, "yr_max": 2013},
        ],
    },
    "sequoia": {
        "display": "Toyota Sequoia",
        "make": "Toyota",
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "3rd Row Seat (complete)", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
            {"name": "Rear Air Suspension Bags", "rarity": "Epic", "low": 150, "high": 350, "cost": 20, "yr_min": 2008},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2008},
        ],
    },
    "highlander": {
        "display": "Toyota Highlander",
        "make": "Toyota",
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 400, "cost": 35},
            {"name": "Power Liftgate Motor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2008},
        ],
    },
    "camry": {
        "display": "Toyota Camry",
        "make": "Toyota",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 40, "yr_min": 2018},
            {"name": "BSM Side Mirror (heated, power fold)", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 15, "yr_min": 2012},
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
            {"name": "Rear Entertainment Screen", "rarity": "Rare", "low": 75, "high": 200, "cost": 15, "yr_min": 2007},
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
            {"name": "Rear Diff Locker Actuator", "rarity": "Epic", "low": 150, "high": 300, "cost": 15},
        ],
    },
    "land cruiser": {
        "display": "Toyota Land Cruiser",
        "make": "Toyota",
        "year_range": (1990, 2024),
        "top_parts": [
            {"name": "AHC Height Control Pump", "rarity": "Legendary", "low": 400, "high": 900, "cost": 40, "yr_min": 1998},
            {"name": "Factory Locker Actuators", "rarity": "Legendary", "low": 300, "high": 700, "cost": 25},
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
            {"name": "OEM Running Boards", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 15},
        ],
    },
    # --- SUBARU ---
    "outback": {
        "display": "Subaru Outback",
        "make": "Subaru",
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "Eyesight Camera Module", "rarity": "Epic", "low": 200, "high": 500, "cost": 25, "yr_min": 2013},
            {"name": "Wilderness Grille/Cladding", "rarity": "Epic", "low": 150, "high": 350, "cost": 25, "trim": ["Wilderness"]},
            {"name": "Roof Rails + Crossbars", "rarity": "Uncommon", "low": 100, "high": 250, "cost": 20},
        ],
    },
    "forester": {
        "display": "Subaru Forester",
        "make": "Subaru",
        "year_range": (1998, 2024),
        "top_parts": [
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
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30, "yr_min": 2015, "trim": ["Limited", "Sport", "GT"]},
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
            {"name": "Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2005},
        ],
    },
    "wrangler": {
        "display": "Jeep Wrangler",
        "make": "Jeep",
        "year_range": (1987, 2024),
        "top_parts": [
            {"name": "Hardtop (full, clean)", "rarity": "Legendary", "low": 400, "high": 1500, "cost": 60},
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
            {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 300, "high": 700, "cost": 40, "yr_min": 2015},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2015},
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 550, "cost": 40, "yr_min": 2004},
            {"name": "Raptor Grille", "rarity": "Legendary", "low": 200, "high": 500, "cost": 25, "trim": ["Raptor"]},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 20, "yr_max": 2014},
        ],
    },
    "f150": {
        "display": "Ford F-150",
        "make": "Ford",
        "year_range": (1997, 2024),
        "top_parts": [
            {"name": "Power-Fold Tow Mirrors", "rarity": "Epic", "low": 250, "high": 550, "cost": 40, "yr_min": 2004},
        ],
    },
    "explorer": {
        "display": "Ford Explorer",
        "make": "Ford",
        "year_range": (1991, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_min": 2002},
            {"name": "Rear Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 15, "yr_min": 2006},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 45, "high": 130, "cost": 22, "yr_max": 2005},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_min": 2006, "yr_max": 2010},
        ],
    },
    "mustang": {
        "display": "Ford Mustang",
        "make": "Ford",
        "year_range": (2005, 2024),
        "top_parts": [
            {"name": "Recaro Seats (PP/GT350)", "rarity": "Epic", "low": 500, "high": 1200, "cost": 75, "trim": ["GT350", "GT500", "Shelby", "Mach 1"]},
            {"name": "GT Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["GT"]},
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 200, "high": 450, "cost": 40, "yr_min": 2015},
        ],
    },
    # --- CHEVY ---
    "silverado": {
        "display": "Chevy Silverado",
        "make": "Chevrolet",
        "year_range": (1999, 2024),
        "top_parts": [
            {"name": "Power Retractable Running Boards", "rarity": "Epic", "low": 250, "high": 600, "cost": 35, "yr_min": 2014},
            {"name": "OEM LED Headlights", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "yr_min": 2019},
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 200, "high": 450, "cost": 30, "yr_min": 2007},
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
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        ],
    },
    "suburban": {
        "display": "Chevy Suburban",
        "make": "Chevrolet",
        "year_range": (1992, 2024),
        "top_parts": [
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 35},
        ],
    },
    "camaro": {
        "display": "Chevy Camaro",
        "make": "Chevrolet",
        "year_range": (2010, 2024),
        "top_parts": [
            {"name": "SS Brembo Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 50, "trim": ["SS", "ZL1", "Z28", "1LE"]},
            {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 60, "trim": ["SS", "ZL1", "1LE"]},
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
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 250, "high": 500, "cost": 35, "yr_min": 2009},
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
            {"name": "ST3/RS HID Headlights (pair)", "rarity": "Epic", "low": 250, "high": 500, "cost": 45, "trim": ["ST", "RS"]},
            {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 71, "trim": ["ST", "RS"]},
            {"name": "ST/RS Intercooler", "rarity": "Rare", "low": 60, "high": 160, "cost": 95, "trim": ["ST", "RS"]},
            {"name": "ST/RS Steering Wheel", "rarity": "Rare", "low": 100, "high": 225, "cost": 37, "trim": ["ST", "RS"]},
            {"name": "RS Brake Calipers (set)", "rarity": "Epic", "low": 300, "high": 600, "cost": 28, "trim": ["RS"]},
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
            {"name": "N/Sport Front Bumper Assembly", "rarity": "Epic", "low": 200, "high": 450, "cost": 73, "trim": ["N", "Sport", "N Line"]},
            {"name": "N Line Steering Wheel", "rarity": "Rare", "low": 100, "high": 225, "cost": 37, "trim": ["N", "N Line"]},
            {"name": "Sport/N Rear Spoiler", "rarity": "Uncommon", "low": 50, "high": 125, "cost": 40, "trim": ["N", "Sport", "N Line"]},
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
            {"name": "Rear Entertainment Screen + DVD", "rarity": "Rare", "low": 75, "high": 200, "cost": 60, "yr_min": 2008},
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
            {"name": "Panoramic Sunroof Glass", "rarity": "Rare", "low": 150, "high": 350, "cost": 44, "yr_min": 2011},
            {"name": "Bose/Infinity Amp + Speakers", "rarity": "Uncommon", "low": 75, "high": 175, "cost": 44},
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
        "year_range": (2000, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 250, "high": 500, "cost": 45, "yr_min": 2016},
            {"name": "Bose Subwoofer + Amp", "rarity": "Rare", "low": 100, "high": 250, "cost": 35},
            {"name": "Panoramic Sunroof Motor", "rarity": "Rare", "low": 100, "high": 220, "cost": 22, "yr_min": 2009},
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
            {"name": "Power-Fold Tow Mirrors (pair)", "rarity": "Epic", "low": 200, "high": 450, "cost": 35, "yr_min": 2007},
            {"name": "SYNC 3 / Large Touchscreen", "rarity": "Rare", "low": 250, "high": 500, "cost": 50, "yr_min": 2015},
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
        ],
    },
    "durango": {
        "display": "Dodge Durango",
        "make": "Dodge",
        "year_range": (1998, 2024),
        "top_parts": [
            {"name": "Uconnect 8.4\" Touchscreen", "rarity": "Rare", "low": 250, "high": 500, "cost": 50, "yr_min": 2014},
            {"name": "3rd Row Seat", "rarity": "Rare", "low": 200, "high": 450, "cost": 40},
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
            {"name": "Rear Entertainment Screen + DVD", "rarity": "Rare", "low": 75, "high": 200, "cost": 60, "yr_min": 2008},
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
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 28},
            {"name": "Touchscreen / UVO Head Unit", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2014},
            {"name": "Panoramic Sunroof Assembly", "rarity": "Rare", "low": 200, "high": 450, "cost": 44, "yr_min": 2014, "trim": ["Exclaim", "GT-Line"]},
        ],
    },
    "optima": {
        "display": "Kia Optima",
        "make": "Kia",
        "year_range": (2001, 2020),
        "top_parts": [
            {"name": "OEM LED Headlights", "rarity": "Rare", "low": 220, "high": 480, "cost": 42, "yr_min": 2016},
            {"name": "Infinity Audio + Amp", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 30},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 55, "high": 150, "cost": 25, "yr_max": 2015},
        ],
    },
    "ranger": {
        "display": "Ford Ranger",
        "make": "Ford",
        "year_range": (1993, 2024),
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
            {"name": "Headlights (clear, OEM)", "rarity": "Uncommon", "low": 90, "high": 240, "cost": 35},
            {"name": "Touchscreen / MIB Unit", "rarity": "Uncommon", "low": 150, "high": 350, "cost": 50, "yr_min": 2012},
        ],
    },
    "chrysler 200": {
        "display": "Chrysler 200",
        "make": "Chrysler",
        "year_range": (2011, 2017),
        "top_parts": [
            {"name": "Uconnect Touchscreen", "rarity": "Uncommon", "low": 120, "high": 280, "cost": 45, "yr_min": 2012},
            {"name": "Headlights (clear, non-hazed)", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 28},
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
            {"name": "OEM Soft Top (clean)", "rarity": "Epic", "low": 200, "high": 500, "cost": 40},
            {"name": "OEM Hardtop (ND)", "rarity": "Legendary", "low": 800, "high": 1800, "cost": 100, "yr_min": 2016},
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
            {"name": "Bang & Olufsen / Premium Audio", "rarity": "Rare", "low": 180, "high": 450, "cost": 38, "trim": ["S3", "Prestige", "Premium Plus"]},
            {"name": "Quattro / Haldex Differential (rear)", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2006},
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
            {"name": "Bang & Olufsen / B&O Sound System", "rarity": "Rare", "low": 200, "high": 520, "cost": 40, "trim": ["Prestige", "Premium Plus"]},
            {"name": "Instrument Cluster (virtual cockpit)", "rarity": "Epic", "low": 350, "high": 850, "cost": 45, "yr_min": 2017},
        ],
    },
    "audi s4": {
        "display": "Audi S4",
        "make": "Audi",
        "year_range": (2004, 2024),
        "top_parts": [
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 500, "high": 1150, "cost": 65, "yr_min": 2010},
            {"name": "Sport Differential / Quattro Controller", "rarity": "Epic", "low": 400, "high": 950, "cost": 45, "yr_min": 2010},
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
            {"name": "Sport Differential / Drive Controller", "rarity": "Epic", "low": 380, "high": 900, "cost": 42, "yr_min": 2012},
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
            {"name": "Air Suspension Compressor", "rarity": "Legendary", "low": 380, "high": 950, "cost": 44, "yr_min": 2013},
            {"name": "B&O Advanced Audio", "rarity": "Epic", "low": 450, "high": 1050, "cost": 48, "trim": ["Prestige"]},
        ],
    },
    "audi s7": {
        "display": "Audi S7",
        "make": "Audi",
        "year_range": (2012, 2024),
        "top_parts": [
            {"name": "OEM LED / Matrix Headlights (pair)", "rarity": "Epic", "low": 650, "high": 1450, "cost": 72, "yr_min": 2012},
            {"name": "MMI / Dual Touchscreens", "rarity": "Epic", "low": 400, "high": 950, "cost": 50, "yr_min": 2012},
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
            {"name": "B&O Advanced Sound", "rarity": "Epic", "low": 650, "high": 1500, "cost": 52, "yr_min": 2013},
        ],
    },
    "audi a5": {
        "display": "Audi A5 / S5",
        "make": "Audi",
        "year_range": (2008, 2024),
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 450, "high": 1000, "cost": 60, "yr_min": 2008},
            {"name": "MMI / Virtual Cockpit", "rarity": "Epic", "low": 280, "high": 700, "cost": 46, "yr_min": 2013},
            {"name": "B&O Premium Audio", "rarity": "Rare", "low": 220, "high": 560, "cost": 40, "trim": ["Prestige", "Premium Plus"]},
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
            {"name": "Air Suspension Compressor / Valve Block", "rarity": "Legendary", "low": 300, "high": 850, "cost": 40, "yr_min": 2012},
            {"name": "Bang & Olufsen 3D / Advanced Sound", "rarity": "Epic", "low": 400, "high": 1000, "cost": 48, "trim": ["Prestige"]},
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
            {"name": "Air Suspension Module", "rarity": "Legendary", "low": 350, "high": 900, "cost": 42, "yr_min": 2012},
            {"name": "B&O Advanced Sound", "rarity": "Epic", "low": 450, "high": 1100, "cost": 50, "trim": ["Prestige"]},
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
            {"name": "Air Suspension Compressor / Struts", "rarity": "Legendary", "low": 400, "high": 1100, "cost": 45, "yr_min": 2004},
            {"name": "Bang & Olufsen Advanced Sound", "rarity": "Epic", "low": 600, "high": 1500, "cost": 55, "trim": ["L", "Prestige"]},
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
            {"name": "Panoramic Sunroof Motor", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2015},
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
            {"name": "Bang & Olufsen / B&O Audio", "rarity": "Rare", "low": 220, "high": 560, "cost": 38, "trim": ["Premium Plus", "Prestige"]},
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
            {"name": "Sport Differential / Adaptive Damper Module", "rarity": "Epic", "low": 450, "high": 1000, "cost": 52, "yr_min": 2014},
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
            {"name": "Air Suspension Compressor", "rarity": "Legendary", "low": 350, "high": 950, "cost": 42, "yr_min": 2011},
            {"name": "Third Row / Power Seat Motors", "rarity": "Rare", "low": 200, "high": 550, "cost": 32, "yr_min": 2015},
            {"name": "B&O 3D Sound", "rarity": "Epic", "low": 500, "high": 1200, "cost": 50, "trim": ["Prestige"]},
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
            {"name": "B&O Advanced 3D Audio", "rarity": "Epic", "low": 600, "high": 1400, "cost": 55, "trim": ["Prestige"]},
            {"name": "Air Suspension + Roll Stabilization Module", "rarity": "Legendary", "low": 500, "high": 1300, "cost": 48, "yr_min": 2019},
        ],
    },
    "audi rs q8": {
        "display": "Audi RS Q8",
        "make": "Audi",
        "year_range": (2020, 2024),
        "top_parts": [
            {"name": "OEM Laser / Matrix Headlights (pair)", "rarity": "Legendary", "low": 1200, "high": 2800, "cost": 95, "yr_min": 2020},
            {"name": "Carbon Ceramic Brakes (set)", "rarity": "Legendary", "low": 5000, "high": 12000, "cost": 450, "yr_min": 2020},
            {"name": "RS Sport Seats (pair)", "rarity": "Legendary", "low": 2200, "high": 5000, "cost": 200, "yr_min": 2020},
        ],
    },
    # Yards often list without space: RSQ8
    "rsq8": {
        "display": "Audi RS Q8",
        "make": "Audi",
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
            {"name": "B&O Advanced Audio", "rarity": "Epic", "low": 650, "high": 1450, "cost": 54, "yr_min": 2020},
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
        "top_parts": [
            # E36/E46 (pre-iDrive): still common in yards; no yr_min so 1999–2005 matches get parts
            {"name": "OEM Headlight Assembly (pair, halogen/xenon)", "rarity": "Rare", "low": 120, "high": 350, "cost": 30, "yr_max": 2005},
            {"name": "Instrument Cluster (M3 / sport clusters worth more)", "rarity": "Rare", "low": 100, "high": 400, "cost": 20, "yr_max": 2006},
            {"name": "iDrive / Navigation Head Unit", "rarity": "Epic", "low": 200, "high": 550, "cost": 50, "yr_min": 2006},
            {"name": "OEM LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 900, "cost": 65, "yr_min": 2012},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 150, "high": 400, "cost": 35, "yr_min": 2006},
            {"name": "Sport Seats (pair)", "rarity": "Rare", "low": 300, "high": 700, "cost": 55, "trim": ["M Sport", "335i", "340i"]},
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
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 120, "high": 320, "cost": 30, "yr_min": 2013},
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
            {"name": "Panoramic Sunroof Motor + Tracks", "rarity": "Rare", "low": 150, "high": 400, "cost": 28, "yr_min": 2011},
            {"name": "iDrive / CIC / NBT Navigation Unit", "rarity": "Epic", "low": 220, "high": 580, "cost": 45, "yr_min": 2007},
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 140, "high": 380, "cost": 32, "yr_min": 2007},
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
        "year_range": (2001, 2024),
        "top_parts": [
            {"name": "Headlight assemblies (pair, E70 xenon/halogen)", "rarity": "Rare", "low": 140, "high": 420, "cost": 45, "yr_min": 2007, "yr_max": 2013},
            {"name": "Headlight assemblies (pair, F15 LED adaptive)", "rarity": "Epic", "low": 260, "high": 680, "cost": 58, "yr_min": 2014, "yr_max": 2018},
            {"name": "Headlight assemblies (pair, G05+ LED / laser)", "rarity": "Epic", "low": 420, "high": 1100, "cost": 65, "yr_min": 2019},
            {"name": "Air Suspension Compressor / Valve Block", "rarity": "Legendary", "low": 250, "high": 700, "cost": 35, "yr_min": 2007},
            {"name": "iDrive / Navigation (CIC/NBT)", "rarity": "Epic", "low": 220, "high": 600, "cost": 45, "yr_min": 2007},
            {"name": "Third Row / Power Seat Motors (if equipped)", "rarity": "Rare", "low": 150, "high": 450, "cost": 30, "yr_min": 2014},
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
            {"name": "Bowers & Wilkins / Premium Audio", "rarity": "Epic", "low": 400, "high": 1000, "cost": 50, "trim": ["Bowers"]},
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
            {"name": "Harman Kardon Amp + Speakers", "rarity": "Rare", "low": 120, "high": 320, "cost": 28, "yr_min": 2012},
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
        "top_parts": [
            {"name": "OEM Xenon / LED Headlights (pair)", "rarity": "Epic", "low": 400, "high": 950, "cost": 58, "yr_min": 2004},
            {"name": "iDrive / CIC / NBT Head Unit", "rarity": "Epic", "low": 220, "high": 600, "cost": 45, "yr_min": 2004},
            {"name": "Harman Kardon / Logic7 System", "rarity": "Rare", "low": 150, "high": 420, "cost": 35, "yr_min": 2004},
            {"name": "Comfort Seats / Multi-Contour (pair)", "rarity": "Rare", "low": 350, "high": 900, "cost": 55, "trim": ["M Sport", "535", "540", "550"]},
            {"name": "Instrument Cluster (HUD clusters worth more)", "rarity": "Rare", "low": 180, "high": 500, "cost": 28, "yr_min": 2004},
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
            {"name": "Bowers & Wilkins / Premium Audio", "rarity": "Epic", "low": 400, "high": 1100, "cost": 48, "trim": ["Bowers"]},
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
            {"name": "Retractable Hardtop Motor / Hydraulics", "rarity": "Legendary", "low": 500, "high": 1400, "cost": 60, "yr_min": 2006},
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
            {"name": "GTI/R Recaro Seats (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 75, "trim": ["GTI", "R", "Clubsport"]},
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
            {"name": "GTI Recaro Seats (pair)", "rarity": "Epic", "low": 500, "high": 1100, "cost": 75},
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
        ],
    },
    "ats": {
        "display": "Cadillac ATS / ATS-V",
        "make": "Cadillac",
        "year_range": (2013, 2019),
        "top_parts": [
            {"name": "Cue Touchscreen / Cluster", "rarity": "Epic", "low": 200, "high": 500, "cost": 45},
            {"name": "Bose / Premium Audio Amp", "rarity": "Rare", "low": 120, "high": 280, "cost": 30},
            {"name": "ATS-V Recaro Seats (pair)", "rarity": "Epic", "low": 800, "high": 1800, "cost": 100, "trim": ["V"]},
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
            {"name": "Sunroof Assembly (complete)", "rarity": "Rare", "low": 80, "high": 200, "cost": 20},
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
            {"name": "Middle Captain Chairs (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
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
            {"name": "Brembo Calipers (set, sport pkg)", "rarity": "Legendary", "low": 300, "high": 700, "cost": 55},
            {"name": "6MT Shifter + Pedal Assembly", "rarity": "Epic", "low": 100, "high": 250, "cost": 15},
            {"name": "Coupe Seats (pair)", "rarity": "Rare", "low": 150, "high": 400, "cost": 40},
            {"name": "OEM HID Headlights", "rarity": "Rare", "low": 150, "high": 350, "cost": 25},
            {"name": "Viscous LSD Rear Diff", "rarity": "Epic", "low": 150, "high": 400, "cost": 50},
        ],
    },
    "g37": {
        "display": "Infiniti G37",
        "make": "Infiniti",
        "year_range": (2008, 2015),
        "top_parts": [
            {"name": "Sport Pkg Brembo/Akebono Calipers (set)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55},
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
            {"name": "Rear LSD Differential", "rarity": "Epic", "low": 150, "high": 350, "cost": 50},
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
            {"name": "AWD Rear Diff + Driveshaft (GSX)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 60, "yr_max": 1999},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 100, "high": 300, "cost": 40},
            {"name": "Sunroof / Spoiler", "rarity": "Rare", "low": 60, "high": 175, "cost": 15},
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
            {"name": "Recaro Seats (pair)", "rarity": "Epic", "low": 300, "high": 700, "cost": 50, "trim": ["Ralliart", "Evolution", "GTS"]},
            {"name": "OEM Spoiler", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 15},
        ],
    },
    "montero": {
        "display": "Mitsubishi Montero / Montero Sport",
        "make": "Mitsubishi",
        "year_range": (1989, 2006),
        "top_parts": [
            {"name": "Rear Diff Locker Components (Gen2/2.5)", "rarity": "Legendary", "low": 200, "high": 500, "cost": 30, "yr_max": 2000},
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
            {"name": "Rear Diff (Torsen LSD — Miata swap favorite)", "rarity": "Epic", "low": 200, "high": 450, "cost": 50},
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
            {"name": "Tow Mirrors (pair)", "rarity": "Rare", "low": 60, "high": 150, "cost": 15},
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
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 200, "high": 450, "cost": 30, "yr_min": 2014},
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
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 200, "high": 450, "cost": 30, "yr_min": 2008},
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
            {"name": "Power Fold Tow Mirrors (pair)", "rarity": "Rare", "low": 200, "high": 450, "cost": 30, "yr_min": 2008},
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
            {"name": "Tow Mirrors (pair)", "rarity": "Rare", "low": 150, "high": 350, "cost": 30, "yr_min": 2010},
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
            {"name": "WS6 Hood / Spoiler", "rarity": "Epic", "low": 150, "high": 450, "cost": 30, "trim": ["WS6", "Trans Am"]},
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
            {"name": "Hardtop / Doors", "rarity": "Epic", "low": 150, "high": 450, "cost": 30},
        ],
    },
    "sidekick": {
        "display": "Suzuki Sidekick / Geo Tracker",
        "make": "Suzuki",
        "year_range": (1989, 1998),
        "top_parts": [
            {"name": "Transfer Case + 4x4 Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 40},
            {"name": "Hardtop / Soft Top Frame", "rarity": "Rare", "low": 80, "high": 250, "cost": 25},
        ],
    },
    "tracker": {
        "display": "Geo/Chevy Tracker (Sidekick twin)",
        "make": "Geo",
        "year_range": (1989, 2004),
        "top_parts": [
            {"name": "Transfer Case + 4x4 Parts", "rarity": "Epic", "low": 100, "high": 300, "cost": 40},
            {"name": "Hardtop / Soft Top Frame", "rarity": "Rare", "low": 80, "high": 250, "cost": 25},
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
            {"name": "4x4 Transfer Case / Diff Parts", "rarity": "Rare", "low": 80, "high": 250, "cost": 40},
            {"name": "Rear Gate + Glass", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 20},
        ],
    },
    "passport": {
        "display": "Honda Passport (Rodeo twin)",
        "make": "Honda",
        "year_range": (1994, 2002),
        "top_parts": [
            {"name": "4x4 Transfer Case / Diff Parts", "rarity": "Rare", "low": 80, "high": 250, "cost": 40},
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
            {"name": "Panoramic Sunroof Parts", "rarity": "Rare", "low": 80, "high": 225, "cost": 20},
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
            {"name": "Air Suspension Compressor", "rarity": "Rare", "low": 100, "high": 250, "cost": 20},
            {"name": "Rear Locking Diff (if equipped)", "rarity": "Epic", "low": 150, "high": 400, "cost": 50},
        ],
    },
    "range rover": {
        "display": "Range Rover",
        "make": "Land Rover",
        "year_range": (1995, 2020),
        "top_parts": [
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
            {"name": "Panoramic Roof Glass", "rarity": "Rare", "low": 100, "high": 250, "cost": 25},
            {"name": "TRD Parts (springs, exhaust bits)", "rarity": "Rare", "low": 80, "high": 225, "cost": 20},
        ],
    },
    "scion xb": {
        "display": "Scion xB (gen1 cult)",
        "make": "Scion",
        "year_range": (2004, 2015),
        "top_parts": [
            {"name": "Gen1 Bumpers / Body Panels (straight)", "rarity": "Rare", "low": 80, "high": 250, "cost": 25, "yr_max": 2006},
            {"name": "Gen1 Interior Trim / Cluster", "rarity": "Rare", "low": 60, "high": 175, "cost": 10, "yr_max": 2006},
        ],
    },
    "genesis coupe": {
        "display": "Hyundai Genesis Coupe",
        "make": "Hyundai",
        "year_range": (2010, 2016),
        "top_parts": [
            {"name": "Brembo Calipers (set, Track/R-Spec)", "rarity": "Epic", "low": 250, "high": 600, "cost": 55, "trim": ["Track", "R-Spec", "Ultimate"]},
            {"name": "Turbo + 2.0T Parts", "rarity": "Epic", "low": 150, "high": 400, "cost": 30},
            {"name": "OEM Seats (pair)", "rarity": "Rare", "low": 120, "high": 300, "cost": 40},
            {"name": "Rear LSD Diff (if equipped)", "rarity": "Epic", "low": 150, "high": 400, "cost": 50},
        ],
    },
    "tiburon": {
        "display": "Hyundai Tiburon",
        "make": "Hyundai",
        "year_range": (1997, 2008),
        "top_parts": [
            {"name": "GT V6 6MT Parts (shifter, pedals)", "rarity": "Rare", "low": 80, "high": 225, "cost": 15, "trim": ["GT"]},
            {"name": "OEM Seats (pair)", "rarity": "Uncommon", "low": 80, "high": 200, "cost": 40},
        ],
    },
    "veloster": {
        "display": "Hyundai Veloster",
        "make": "Hyundai",
        "year_range": (2012, 2022),
        "top_parts": [
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
            {"name": "Tow Mirrors (pair)", "rarity": "Uncommon", "low": 60, "high": 150, "cost": 20},
            {"name": "Bench Seats (rear rows)", "rarity": "Uncommon", "low": 50, "high": 150, "cost": 25},
            {"name": "7.3L Powerstroke Parts (verify engine)", "rarity": "Epic", "low": 200, "high": 600, "cost": 50, "yr_max": 2003},
        ],
    },
}

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
            if entry["kw"] == "mark levinson" and vehicle_make:
                if vehicle_make.strip().lower() == "lexus":
                    notes = "Lexus audio buyers pay well on eBay"
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
    return {
        "trim": trim,
        "series": (row.get("Series") or "").strip(),
        "driveType": (row.get("DriveType") or "").strip(),
        "trimQuality": _vpic_trim_quality(trim),
        "bodyClass": (row.get("BodyClass") or "").strip(),
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


def match_vehicle(year: int, make: str, model: str, vin_decode: dict | None = None) -> list[dict]:
    """Match a vehicle against the unobtanium database, filtering parts by
    year range and trim requirements.  Attaches sell-channel info to each part.

    Trim-gated parts carry a "trim_status" honesty flag:
      - "listing":     the yard's own listing title names the trim
      - "vin":         a usable (single-trim) vPIC decode confirms the trim
      - "unconfirmed": trim unknown/ambiguous — part listed as "if equipped"
    When a USABLE decode names a different trim (and series doesn't match
    either), the part is excluded — that's the only case where we're confident
    the car doesn't have it. Ambiguous/empty decodes never gate parts."""
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
    for keyword, info in UNOBTANIUM_DB.items():
        if keyword in model_lower or keyword in f"{make_lower} {model_lower}":
            low, high = info["year_range"]
            if low <= year <= high:
                filtered_parts = []
                for p in info["top_parts"]:
                    if "yr_min" in p and year < p["yr_min"]:
                        continue
                    if "yr_max" in p and year > p["yr_max"]:
                        continue
                    trim_status = None
                    if "trim" in p:
                        trims = [t.lower() for t in p["trim"]]
                        if any(t in model_lower for t in trims):
                            trim_status = "listing"
                        elif vin_tokens and any(t in vin_tokens for t in trims):
                            trim_status = "vin"
                        elif vin_usable:
                            # Decode is specific and names a different trim:
                            # confident the car doesn't have this part.
                            continue
                        else:
                            trim_status = "unconfirmed"
                    cl, ch = _resale_sold_calibrate(p["low"], p["high"], p["name"], year)
                    enriched = {**p, "low": cl, "high": ch, **_lookup_sell_info(p["name"], make)}
                    if trim_status:
                        enriched["trim_status"] = trim_status
                    filtered_parts.append(enriched)
                if filtered_parts:
                    max_val = max(p["high"] for p in filtered_parts)
                    matches.append({**info, "top_parts": filtered_parts, "max_value": max_val})
    return matches


def fetch_pnp_inventory(make_ids: list[int] | None = None, *, national: bool = False) -> list[dict]:
    """Fetch live inventory from Pick-n-Pull API.

    national=True uses distance=0, which the PnP API treats as unlimited —
    one request per make returns every yard in the US + Canada network."""
    if make_ids is None:
        makes_resp = requests.get(f"{PNP_API}/vehicle/makes", headers=HEADERS, timeout=15)
        all_makes = makes_resp.json()
        make_ids = [m["id"] for m in all_makes]

    distance = 0 if national else SEARCH_RADIUS
    all_vehicles = []
    for mid in make_ids:
        try:
            r = requests.get(
                f"{PNP_API}/vehicle/search",
                params={"makeId": mid, "distance": distance, "zip": SLC_ZIP},
                headers=HEADERS,
                timeout=60 if national else 15,
            )
            for loc_data in r.json():
                loc = loc_data.get("location") or {}
                # The API occasionally returns a location stub with null
                # name/city/state — skip those groups rather than emitting a
                # phantom "None" yard; the vehicles come back on the next scan.
                if not loc.get("name"):
                    continue
                for v in loc_data.get("vehicles", []):
                    v["_location"] = loc.get("name")
                    v["_city"] = loc.get("city") or ""
                    v["_state"] = loc.get("state") or ""
                    v["_lat"] = loc.get("mapLatitude")
                    v["_lng"] = loc.get("mapLongitude")
                    all_vehicles.append(v)
        except Exception:
            continue

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
            for det in row.select(".pypvi_detailItem"):
                txt = det.get_text(" ", strip=True)
                if txt.upper().startswith("VIN"):
                    vin = txt[3:].strip()
                    break
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


def enrich_vehicles(
    vehicles: list[dict],
    *,
    decode_vins: bool = False,
    decode_vins_profit_top: int = 0,
    decode_vins_incremental: bool = False,
) -> list[dict]:
    """Add unobtanium match data. Optionally decode VINs via NHTSA VPIC (all unique VINs, or top-N-by-profit only)."""
    allowed_vins: set[str] | None = None

    def _apply_match(v: dict, vin_dec: dict | None) -> None:
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
            "make": _canon_make(v.get("make", "")),
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
                    **({"trim_status": p["trim_status"]} if p.get("trim_status") else {}),
                }
                for p in v.get("_top_parts", [])
            ],
        }
        vp = v.get("_vpic")
        if isinstance(vp, dict) and vp:
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
    }


def build_inventory_json_payload(vehicles: list[dict], only_matches: bool) -> dict:
    """Wrapper written to inventory_live.json: metadata + vehicle rows."""
    return compact_inventory_v2(output_json(vehicles, only_matches=only_matches))


def print_rich(vehicles: list[dict], show_all: bool = False):
    console = Console()
    console.print()
    console.print(Panel.fit(
        "[bold yellow]Junkyard Hunter[/] — Live Inventory Scan\n"
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
    print(f"  JUNKYARD HUNTER — Live Scan")
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
    hard-to-guess topic name (e.g. junkyard-hunter-bv-8k2j) and subscribe to
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
        make_low = (entry.get("make") or "").lower()
        model_low = (entry.get("model") or "").lower()
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
        _macos_notify("Junkyard Hunter", f"{_vname(v)} at {_vloc(v)}{has_parts}")
    if len(hits) > 5:
        _macos_notify("Junkyard Hunter", f"...and {len(hits) - 5} more watchlist hits")

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
        subj = (f"Junkyard Alert: {_vname(hits[0])} at {_vloc(hits[0])}"
                if len(hits) == 1 else f"Junkyard Alert: {len(hits)} new watchlist hits")
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
    parser = argparse.ArgumentParser(description="Junkyard Hunter — live self-service junkyard scan")
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
    args = parser.parse_args()

    if args.refresh_utpap_pricing:
        path = refresh_utpap_pricing_file()
        n = len(json.loads(path.read_text()))
        print(f"Wrote {n} price rows to {path}", file=sys.stderr)
        return

    if args.refresh_chain_pricing:
        refresh_pnp_pricing_file()
        refresh_pyp_pricing_file()
        refresh_pap_pricing_file()
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

    def do_scan():
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

        all_vehicles = pnp_vehicles + tap_vehicles + utpap_vehicles + pyp_vehicles + pap_vehicles
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
                if args.save:
                    LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
                    print(f"Saved {len(payload['vehicles'])} vehicles to {LIVE_FILE} (scrapedAt {payload['scrapedAt']})")
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
            if args.save:
                LIVE_FILE.write_text(json.dumps(payload, separators=(",", ":")))
                if not args.json:
                    print(f"Saved {len(payload['vehicles'])} vehicles to {LIVE_FILE} (scrapedAt {payload['scrapedAt']})", file=sys.stderr)
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
