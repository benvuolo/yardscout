"""
Junkyard Hunter — inventory history database (SQLite).

Keeps every vehicle ever seen, when it arrived (first_seen), when we last saw
it (last_seen), and when it disappeared from the yard feed (departed_at —
usually means crushed). inventory_live.json stays the "current snapshot" for
the web UI; this DB is the permanent history that a future API/app reads.

SQLite = a single file (inventory_history.db) next to this script. No server.
Migrating to Postgres later just means swapping the connection layer.
"""

import json
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_FILE = SCRIPT_DIR / "inventory_history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles (
    key             TEXT PRIMARY KEY,   -- source:vehicle_id
    source          TEXT NOT NULL,      -- pnp | tap | utpap | unknown
    vehicle_id      TEXT NOT NULL,
    vin             TEXT,
    year            INTEGER,
    make            TEXT,
    model           TEXT,
    row             TEXT,
    location        TEXT,
    city            TEXT,
    state           TEXT,
    premium         INTEGER DEFAULT 0,
    date_added      TEXT,               -- yard-reported arrival date
    has_match       INTEGER DEFAULT 0,
    max_value       INTEGER DEFAULT 0,
    display_name    TEXT,
    top_parts_json  TEXT,
    vpic_trim       TEXT,
    vpic_quality    TEXT,
    first_seen      TEXT NOT NULL,      -- first scan that saw this vehicle
    last_seen       TEXT NOT NULL,      -- most recent scan that saw it
    departed_at     TEXT                -- scan time when it vanished (crushed/pulled)
);

CREATE INDEX IF NOT EXISTS idx_vehicles_make_model ON vehicles (make, model);
CREATE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles (vin);
CREATE INDEX IF NOT EXISTS idx_vehicles_departed ON vehicles (departed_at);

CREATE TABLE IF NOT EXISTS scans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at  TEXT NOT NULL,
    total       INTEGER,
    matches     INTEGER,
    new_arrivals INTEGER,
    departures  INTEGER
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(_SCHEMA)
    return conn


def _source_of(entry: dict) -> str:
    vid = str(entry.get("id") or "")
    loc = entry.get("location") or ""
    if vid.startswith("utpap-"):
        return "utpap"
    if "tear-a-part" in loc.lower():
        return "tap"
    if "pick-n-pull" in loc.lower():
        return "pnp"
    return "unknown"


def record_scan(entries: list[dict], scraped_at: str) -> dict:
    """Upsert one full scan (output_json-format entries, ALL vehicles not just
    matches). Marks vehicles missing from this scan as departed.
    Returns counts for logging."""
    conn = _connect()
    cur = conn.cursor()

    new_arrivals = 0
    seen_keys = set()

    for e in entries:
        source = _source_of(e)
        key = f"{source}:{e.get('id')}"
        seen_keys.add(key)

        row = cur.execute("SELECT first_seen, departed_at FROM vehicles WHERE key = ?", (key,)).fetchone()
        top_parts = json.dumps(e.get("topParts") or [])

        if row is None:
            new_arrivals += 1
            cur.execute(
                """INSERT INTO vehicles
                   (key, source, vehicle_id, vin, year, make, model, row, location,
                    city, state, premium, date_added, has_match, max_value,
                    display_name, top_parts_json, vpic_trim, vpic_quality,
                    first_seen, last_seen, departed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
                (key, source, str(e.get("id")), e.get("vin", ""), e.get("year"),
                 e.get("make", ""), e.get("model", ""), str(e.get("row", "")),
                 e.get("location", ""), e.get("city", ""), e.get("state", ""),
                 1 if e.get("utpapPremium") else 0, e.get("dateAdded", ""),
                 1 if e.get("hasMatch") else 0, e.get("maxValue", 0),
                 e.get("displayName", ""), top_parts,
                 e.get("vpicTrim", ""), e.get("vpicTrimQuality", ""),
                 scraped_at, scraped_at),
            )
        else:
            # Vehicle re-seen: refresh mutable fields; clear departed_at if it
            # reappeared (feed glitches happen).
            cur.execute(
                """UPDATE vehicles SET
                     row = ?, location = ?, has_match = ?, max_value = ?,
                     display_name = ?, top_parts_json = ?,
                     vpic_trim = CASE WHEN ? != '' THEN ? ELSE vpic_trim END,
                     vpic_quality = CASE WHEN ? != '' THEN ? ELSE vpic_quality END,
                     last_seen = ?, departed_at = NULL
                   WHERE key = ?""",
                (str(e.get("row", "")), e.get("location", ""),
                 1 if e.get("hasMatch") else 0, e.get("maxValue", 0),
                 e.get("displayName", ""), top_parts,
                 e.get("vpicTrim", ""), e.get("vpicTrim", ""),
                 e.get("vpicTrimQuality", ""), e.get("vpicTrimQuality", ""),
                 scraped_at, key),
            )

    # Anything we've seen before, not in this scan, and not already departed → departed now.
    # Scoped to yards present in THIS scan, so a Utah-only scan never marks
    # national inventory as departed (and vice versa).
    seen_locations = {e.get("location") for e in entries}
    cur.execute("SELECT key, location FROM vehicles WHERE departed_at IS NULL")
    missing = [k for (k, loc) in cur.fetchall() if k not in seen_keys and loc in seen_locations]
    for k in missing:
        cur.execute("UPDATE vehicles SET departed_at = ? WHERE key = ?", (scraped_at, k))

    matches = sum(1 for e in entries if e.get("hasMatch"))
    cur.execute(
        "INSERT INTO scans (scraped_at, total, matches, new_arrivals, departures) VALUES (?,?,?,?,?)",
        (scraped_at, len(entries), matches, new_arrivals, len(missing)),
    )

    conn.commit()
    conn.close()
    return {"total": len(entries), "new_arrivals": new_arrivals, "departures": len(missing)}


def summary() -> str:
    """Quick human-readable DB status."""
    conn = _connect()
    cur = conn.cursor()
    n_all = cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    n_active = cur.execute("SELECT COUNT(*) FROM vehicles WHERE departed_at IS NULL").fetchone()[0]
    n_scans = cur.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
    last = cur.execute("SELECT scraped_at FROM scans ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return (f"{n_all} vehicles tracked ({n_active} currently in yard, "
            f"{n_all - n_active} departed) across {n_scans} scan(s); "
            f"last scan {last[0] if last else 'never'}")
