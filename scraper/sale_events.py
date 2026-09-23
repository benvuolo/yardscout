"""Sale-day scraper — publishes docs/data/sale_events.json.

Where each chain publishes sales (researched 2026-09-22):

- Pick-n-Pull:  structured JSON.
    /api/event/banner/?language=en   -> chain-wide promo banner (title + start/end)
    /api/event/alllocations          -> event-location ids ("CA - Fairfield")
    /api/event/location/{id}         -> per-location events (empty between sales)
- LKQ Pick Your Part:  no API. Sale dates render into each yard's
    pyp.com/deals/{city-slug}-{code}/ page ONLY while a sale is scheduled
    (pages are pure boilerplate otherwise). We fetch each yard's deals page
    and parse "N% off" / "half price" copy paired with a date. Anything
    percent-y we can't confidently date goes into `unparsed` for review —
    never guessed into a badge.
- Pull-A-Part:  offers live behind the VIP-club login; nothing public to
    scrape. Sales for PAP (or anything seen on Facebook etc.) can be entered
    by hand in scraper/sale_events_manual.json and flow through this same
    pipeline with source="manual".

Output shape (docs/data/sale_events.json):
    {"updatedAt": iso, "events": [
        {"chain": "Pick-n-Pull", "yard": "Pick-n-Pull - Fairfield" | null,
         "title": "50% Off Labor Day Sale", "start": "2026-09-05",
         "end": "2026-09-07", "pct": 50, "source": "picknpull-api"}
    ], "unparsed": [ ... ]}
`yard` null means chain-wide (applies to every yard of that chain).
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "docs" / "data"
OUT_FILE = DATA_DIR / "sale_events.json"
MANUAL_FILE = Path(__file__).resolve().parent / "sale_events_manual.json"

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      "Accept": "application/json"}
PNP_BASE = "https://www.picknpull.com"
PYP_BASE = "https://www.pyp.com"

# Keep events visible this long after they end (the UI greys them out same-day).
KEEP_PAST_DAYS = 2
# Ignore events further out than this — far-future junk is usually a typo.
MAX_FUTURE_DAYS = 120

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}
_MONTH_RE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
# "May 24-26", "May 24 – 26", "Nov 27th - Dec 1st", "December 31 - January 2"
DATE_RANGE_RE = re.compile(
    rf"({_MONTH_RE})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?"
    rf"(?:\s*[-–—]\s*(?:({_MONTH_RE})\.?\s+)?(\d{{1,2}})(?:st|nd|rd|th)?)?",
    re.IGNORECASE)
PCT_RE = re.compile(r"(\d{1,2})\s*%\s*off|half[\s-]?price", re.IGNORECASE)


def _infer_year(month: int, day: int, today: date) -> date:
    """Nearest occurrence of month/day that isn't deep in the past."""
    for yr in (today.year, today.year + 1):
        try:
            d = date(yr, month, day)
        except ValueError:
            continue
        if d >= today - timedelta(days=KEEP_PAST_DAYS + 30):
            return d
    return date(today.year + 1, month, min(day, 28))


def parse_sale_text(text: str, today: date | None = None) -> dict | None:
    """Extract {pct, start, end} from promo copy; None unless BOTH a
    discount token and a parseable date are present (no-guessing rule)."""
    today = today or date.today()
    pm = PCT_RE.search(text)
    dm = DATE_RANGE_RE.search(text)
    if not pm or not dm:
        return None
    pct = int(pm.group(1)) if pm.group(1) else 50   # "half price"
    m1 = MONTHS[dm.group(1).lower()[:3]]
    d1 = int(dm.group(2))
    start = _infer_year(m1, d1, today)
    if dm.group(4):
        m2 = MONTHS[dm.group(3).lower()[:3]] if dm.group(3) else m1
        end = _infer_year(m2, int(dm.group(4)), today)
        if end < start:           # "Dec 31 - Jan 2" rolling the year
            end = end.replace(year=start.year + 1)
    else:
        end = start
    if (start - today).days > MAX_FUTURE_DAYS:
        return None
    return {"pct": pct, "start": start.isoformat(), "end": end.isoformat()}


# ---------------------------------------------------------------- Pick-n-Pull

def fetch_pnp_events() -> tuple[list[dict], list[dict]]:
    events, unparsed = [], []
    # Chain-wide banner (id 0 / null title = nothing running)
    try:
        b = requests.get(f"{PNP_BASE}/api/event/banner/?language=en",
                         headers=UA, timeout=30).json()
        if b and b.get("title"):
            start = str(b.get("promoBannerStartDate", ""))[:10]
            end = str(b.get("promoBannerEndDate", ""))[:10]
            if start > "0001-01-01":
                pm = PCT_RE.search(b["title"])
                events.append({
                    "chain": "Pick-n-Pull", "yard": None, "title": b["title"],
                    "start": start, "end": end,
                    "pct": int(pm.group(1)) if pm and pm.group(1) else (50 if pm else None),
                    "source": "picknpull-banner",
                })
    except Exception as e:  # noqa: BLE001 — one chain must not kill the file
        print(f"  [sale-events] PnP banner failed: {e}", file=sys.stderr)

    # Per-location events
    try:
        locs = requests.get(f"{PNP_BASE}/api/event/alllocations",
                            headers=UA, timeout=30).json()
    except Exception as e:  # noqa: BLE001
        print(f"  [sale-events] PnP locations failed: {e}", file=sys.stderr)
        return events, unparsed

    def one(loc):
        r = requests.get(f"{PNP_BASE}/api/event/location/{loc['id']}",
                         headers=UA, timeout=30)
        return loc, (r.json() if r.status_code == 200 else [])

    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in as_completed(ex.submit(one, l) for l in locs):
            try:
                loc, evs = fut.result()
            except Exception:  # noqa: BLE001
                continue
            # "CA - Fairfield" -> yard name used in inventory: "Pick-n-Pull - Fairfield"
            yard = f"Pick-n-Pull - {loc['listText']}"
            for ev in evs or []:
                title = str(ev.get("title") or ev.get("name") or "Sale event")
                start = str(ev.get("startDate") or ev.get("eventDate") or "")[:10]
                end = str(ev.get("endDate") or start)[:10]
                if not start or start <= "0001-01-01":
                    unparsed.append({"chain": "Pick-n-Pull", "yard": yard,
                                     "raw": json.dumps(ev)[:300]})
                    continue
                pm = PCT_RE.search(title)
                events.append({
                    "chain": "Pick-n-Pull", "yard": yard, "title": title,
                    "start": start, "end": end,
                    "pct": int(pm.group(1)) if pm and pm.group(1) else (50 if pm else None),
                    "source": "picknpull-api",
                })
    return events, unparsed


# --------------------------------------------------------- LKQ Pick Your Part

def _pyp_slug(name: str) -> str:
    city = name.split(" - ", 1)[-1]
    city = unicodedata.normalize("NFKD", city).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def _pyp_locations() -> list[dict]:
    """[{code, name}] from the _locationList blob embedded in pyp.com pages."""
    r = requests.get(f"{PYP_BASE}/deals/", headers={**UA, "Accept": "text/html"},
                     timeout=30)
    m = re.search(r"_locationList\s*=\s*(\[.*?\]);", r.text, re.DOTALL)
    if not m:
        raise RuntimeError("pyp.com _locationList blob not found")
    return [{"code": l["LocationCode"], "name": l["Name"]}
            for l in json.loads(m.group(1))]


def fetch_pyp_events() -> tuple[list[dict], list[dict]]:
    events, unparsed = [], []
    try:
        locs = _pyp_locations()
    except Exception as e:  # noqa: BLE001
        print(f"  [sale-events] PYP location list failed: {e}", file=sys.stderr)
        return events, unparsed

    def one(loc):
        url = f"{PYP_BASE}/deals/{_pyp_slug(loc['name'])}-{loc['code']}/"
        r = requests.get(url, headers={**UA, "Accept": "text/html"}, timeout=30)
        if r.status_code != 200:
            return loc, None
        m = re.search(r"Start_Module_499(.*?)End_Module_499", r.text, re.DOTALL)
        seg = m.group(1) if m else r.text
        return loc, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg))

    with ThreadPoolExecutor(max_workers=6) as ex:
        for fut in as_completed(ex.submit(one, l) for l in locs):
            try:
                loc, text = fut.result()
            except Exception:  # noqa: BLE001
                continue
            if not text:
                continue
            parsed = parse_sale_text(text)
            if parsed:
                events.append({
                    "chain": "Pick Your Part", "yard": loc["name"],
                    "title": f"{parsed['pct']}% off sale",
                    "start": parsed["start"], "end": parsed["end"],
                    "pct": parsed["pct"], "source": "pyp-deals-page",
                })
            elif PCT_RE.search(text):
                # discount copy we couldn't date — surface it, never badge it
                i = PCT_RE.search(text).start()
                unparsed.append({"chain": "Pick Your Part", "yard": loc["name"],
                                 "raw": text[max(0, i - 80):i + 160]})
    return events, unparsed


# ------------------------------------------------------------ manual entries

def load_manual_events() -> list[dict]:
    if not MANUAL_FILE.exists():
        return []
    try:
        raw = json.loads(MANUAL_FILE.read_text())
    except Exception as e:  # noqa: BLE001
        print(f"  [sale-events] manual file unreadable: {e}", file=sys.stderr)
        return []
    out = []
    for ev in raw.get("events", []):
        if not ev.get("start") or not ev.get("chain"):
            continue
        out.append({"chain": ev["chain"], "yard": ev.get("yard"),
                    "title": ev.get("title", "Sale"), "start": ev["start"],
                    "end": ev.get("end", ev["start"]), "pct": ev.get("pct"),
                    "source": "manual"})
    return out


# -------------------------------------------------------------------- output

def build_sale_events() -> dict:
    today = date.today()
    cutoff = (today - timedelta(days=KEEP_PAST_DAYS)).isoformat()
    events, unparsed = [], []
    for fetch in (fetch_pnp_events, fetch_pyp_events):
        try:
            ev, un = fetch()
            events += ev
            unparsed += un
        except Exception as e:  # noqa: BLE001
            print(f"  [sale-events] {fetch.__name__} failed: {e}", file=sys.stderr)
    events += load_manual_events()
    # De-dupe (chain, yard, start) — manual entries lose to scraped ones.
    seen, kept = set(), []
    for ev in events:
        key = (ev["chain"], ev["yard"], ev["start"])
        if key in seen or ev["end"] < cutoff:
            continue
        seen.add(key)
        kept.append(ev)
    kept.sort(key=lambda e: (e["start"], e["chain"], e["yard"] or ""))
    return {"updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "events": kept, "unparsed": unparsed[:40]}


def main() -> int:
    out = build_sale_events()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, indent=1))
    print(f"[sale-events] {len(out['events'])} events, "
          f"{len(out['unparsed'])} unparsed -> {OUT_FILE.relative_to(REPO_ROOT)}")
    if out["unparsed"]:
        print("[sale-events] UNPARSED (review; add to sale_events_manual.json "
              "or improve parser):", file=sys.stderr)
        for u in out["unparsed"][:10]:
            print(f"  - {u['chain']} / {u.get('yard')}: {u['raw'][:140]}",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
