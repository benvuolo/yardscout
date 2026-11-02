#!/usr/bin/env python3
"""Live eBay asking prices for every part in the unobtanium DB.

What it does
  For each (vehicle entry, part) in junkyard_scraper.UNOBTANIUM_DB, asks the
  eBay Browse API for USED, fixed-price, US listings of that part, fitment-
  matched to the car (eBay's compatibility filter: Year/Make/Model), and keeps
  the middle half of the asking prices (25th–75th percentile) plus the count.
  The scan reads the result (docs/data/ebay_prices.json) and ships those bands
  on each car's parts instead of the hand-tuned anchors — see
  junkyard_scraper._ebay_band / match_vehicle. Parts with too few listings,
  or a stale/absent entry, keep the anchors; the app labels each case.

Why asking prices, not sold
  eBay's sold-price API (Marketplace Insights) is limited-release and needs a
  separate approval. Browse is open to any developer account. The app says
  "On eBay now" and never claims these are sale prices.

Accuracy guards
  - compatibility_filter restricts to listings whose fitment includes this
    exact year/make/model; when eBay rejects the filter for a model name the
    query is retried as plain keywords and flagged ("fit": false).
  - p25–p75 drops the junk at both ends (wrong-part $9 brackets, $2,000 NOS).
  - Fewer than MIN_N listings is "not enough data": the anchors stay.
  - The scan also ignores an eBay band that lands wildly off the curated
    anchor (likely a keyword collision) — see _ebay_band.

Setup (one time, by the owner)
  developer.ebay.com → "Create an application" (Production keyset) →
  repository secrets EBAY_CLIENT_ID + EBAY_CLIENT_SECRET. Browse needs only
  the application token (client-credentials grant), no user sign-in. Default
  allowance is 5,000 calls/day; one refresh of the whole DB is ~3,800 calls.

Run
  python scraper/ebay_prices.py --max-calls 2000      # refresh stalest first
  python scraper/ebay_prices.py --dry-run             # list queries, no calls
Env: EBAY_CLIENT_ID, EBAY_CLIENT_SECRET. Nothing secret is ever printed.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - the scan workflow installs it
    requests = None

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/v2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
MARKETPLACE = "EBAY_US"
CATEGORY_PARTS = "6028"  # eBay Motors > Parts & Accessories
DEFAULT_PATH = SCRIPT_DIR.parent / "docs" / "data" / "ebay_prices.json"
MIN_N = 5            # listings needed before a band counts
MAX_AGE_DAYS = 14    # refresh order: missing, then older than this
LIMIT = 100          # listings per query (Browse max 200; 100 is plenty)
PAUSE_SEC = 0.25     # polite spacing between calls


# ---------------------------------------------------------------- queries
_PAREN_RE = re.compile(r"\([^)]*\)")
_SPLIT_RE = re.compile(r"\s+[—–-]{1,2}\s+|:\s+")
_DROP_WORDS = {
    "oem", "complete", "set", "pair", "full", "factory", "genuine", "assembly",
    "w/", "with", "and", "the", "swap", "gold", "kit", "non-hazed", "clear",
    "unit", "units", "parts", "components", "accessories",
}


def clean_part_query(name: str) -> str:
    """Turn a DB part label into eBay keywords.

    "Headlights (clear, non-hazed)"            -> "Headlights"
    "5-speed manual + pedal box + shifter (…)" -> "5-speed manual pedal box shifter"
    "2JZ-GE accessories / harness (SC300)"     -> "2JZ-GE harness"
    """
    s = _PAREN_RE.sub(" ", name)
    s = _SPLIT_RE.split(s)[0]           # text before " — note" / "Label: detail"
    s = s.replace("/", " ").replace("+", " ").replace("&", " ")
    words = [w for w in re.split(r"\s+", s.strip()) if w]
    words = [w for w in words if w.lower().strip(",.") not in _DROP_WORDS]
    out = " ".join(words).strip(" ,.")
    return re.sub(r"\s{2,}", " ", out)


_NICKNAMES = {"chevy", "mercedes"}            # brand words that never name a model
_MAKE_NICKNAMES = {"ram": ("dodge",)}           # "Dodge Ram Truck" under make Ram


def entry_model(info: dict) -> str:
    """The model words of an entry's display name, as eBay fitment knows them.

    "Toyota 4Runner (3rd gen)" -> "4Runner";  "Audi A4 / Allroad" -> "A4";
    "Chevrolet Chevy Suburban" -> "Suburban";  "Ram / Dodge Ram Truck" -> "Ram Truck".
    """
    disp = re.sub(r"\s*\((?:[^)]*)\)\s*$", "", str(info.get("display") or ""))
    make = str(info.get("make") or "").strip().lower()
    nick = _NICKNAMES | set(_MAKE_NICKNAMES.get(make, ()))
    for alt in disp.split("/"):
        words = alt.strip(" -–—").split()
        if words and make and words[0].lower().strip(",") == make:
            words.pop(0)                       # the make itself, only as the first word
        while words and words[0].lower().strip(",") in nick:
            words.pop(0)                       # "Chevy", "Dodge" brand words
        if words:
            return " ".join(words)
    return disp.strip()


def part_window(info: dict, p: dict) -> tuple[int, int]:
    """Model years this DB row covers: the entry's range narrowed by the part's gates."""
    lo, hi = info.get("year_range", (0, 0))
    plo = max(lo, int(p.get("yr_min", lo) or lo))
    phi = min(hi, int(p.get("yr_max", hi) or hi))
    return (plo, phi) if phi >= plo else (lo, hi)


def part_key(entry_key: str, part_name: str, window: tuple[int, int]) -> str:
    """One entry can list the same part twice with different year windows
    (headlights 2014–2021 vs 2022+), so the window is part of the key."""
    return f"{entry_key}|{part_name.strip().lower()}|{window[0]}-{window[1]}"


def canonical_keys(db: dict) -> dict[int, str]:
    """id(entry) -> the first dict key it is stored under (alias keys share an object)."""
    out: dict[int, str] = {}
    for k, info in db.items():
        out.setdefault(id(info), k)
    return out


def build_queries(db: dict) -> list[dict]:
    """One query per (entry, part): key, keywords, fitment year/make/model, anchors."""
    canon = canonical_keys(db)
    seen: set[int] = set()
    out: list[dict] = []
    for k, info in db.items():
        if id(info) in seen:
            continue
        seen.add(id(info))
        ekey = canon[id(info)]
        make = str(info.get("make") or "").strip()
        model = entry_model(info)
        for p in info.get("top_parts", []):
            plo, phi = part_window(info, p)
            year = (plo + phi) // 2
            kw = clean_part_query(p["name"])
            if not kw or kw.lower().startswith("anything"):
                continue  # "Anything — Datsun parts all sell" is a note, not a part
            words = f"{make} {model} {kw}".split()
            words = [w for i, w in enumerate(words) if i == 0 or w.lower() != words[i - 1].lower()]  # "Ram Ram Truck"
            out.append({
                "key": part_key(ekey, p["name"], (plo, phi)),
                "q": " ".join(words),
                "year": year, "make": make, "model": model,
                "anchor_low": int(p.get("low", 0) or 0), "anchor_high": int(p.get("high", 0) or 0),
            })
    return out


# ---------------------------------------------------------------- stats
def percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * pct
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def band(prices: list[float]) -> dict | None:
    """Middle half of the asking prices; None when there aren't enough."""
    vals = sorted(float(v) for v in prices if v and v > 0)
    if len(vals) < MIN_N:
        return None
    return {
        "low": int(round(percentile(vals, 0.25))),
        "mid": int(round(percentile(vals, 0.50))),
        "high": int(round(percentile(vals, 0.75))),
        "n": len(vals),
    }


# ---------------------------------------------------------------- eBay
class EbayClient:
    """Thin Browse API client: application token + one search call."""

    def __init__(self, client_id: str, client_secret: str, session=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session or requests.Session()
        self._token = ""
        self._token_exp = 0.0

    def token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        r = self.session.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            timeout=30,
        )
        if r.status_code != 200:
            raise RuntimeError(f"eBay token request failed: HTTP {r.status_code}")
        j = r.json()
        self._token = j["access_token"]
        self._token_exp = time.time() + float(j.get("expires_in", 7200))
        return self._token

    def search_prices(self, q: dict) -> tuple[list[float], bool]:
        """Asking prices (USD) for a query; second value: fitment filter applied."""
        base = {
            "q": q["q"],
            "category_ids": CATEGORY_PARTS,
            "limit": str(LIMIT),
            "filter": "conditions:{USED},buyingOptions:{FIXED_PRICE},priceCurrency:USD,itemLocationCountry:US",
        }
        compat = f"Year:{q['year']};Make:{q['make']};Model:{q['model']}" if q.get("year") and q.get("make") and q.get("model") else ""
        for use_fit in ((True, False) if compat else (False,)):
            params = dict(base)
            if use_fit:
                params["compatibility_filter"] = compat
            r = self.session.get(
                SEARCH_URL, params=params,
                headers={"Authorization": f"Bearer {self.token()}", "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE},
                timeout=30,
            )
            if r.status_code == 400 and use_fit:
                continue  # eBay didn't accept the fitment filter for this model: plain keywords
            if r.status_code in (401, 403, 429) or r.status_code >= 500:
                raise RuntimeError(f"eBay search failed: HTTP {r.status_code}")
            if r.status_code != 200:
                return [], use_fit
            items = r.json().get("itemSummaries", []) or []
            prices = []
            for it in items:
                pr = (it.get("price") or {})
                if pr.get("currency", "USD") != "USD":
                    continue
                try:
                    prices.append(float(pr.get("value")))
                except (TypeError, ValueError):
                    continue
            return prices, use_fit
        return [], False


# ---------------------------------------------------------------- refresh
def load(path: Path) -> dict:
    try:
        d = json.loads(Path(path).read_text())
        if isinstance(d, dict) and isinstance(d.get("parts"), dict):
            return d
    except (OSError, ValueError):
        pass
    return {"asOf": "", "marketplace": MARKETPLACE, "parts": {}}


def refresh_order(queries: list[dict], parts: dict, now: datetime) -> list[dict]:
    """Missing entries first, then the stalest; entries fresher than MAX_AGE_DAYS last."""
    def age_days(key: str) -> float:
        at = (parts.get(key) or {}).get("at")
        if not at:
            return 1e9
        try:
            return (now - datetime.fromisoformat(at.replace("Z", "+00:00"))).total_seconds() / 86400
        except ValueError:
            return 1e9
    return sorted(queries, key=lambda q: -age_days(q["key"]))


def refresh(client, queries: list[dict], path: Path, max_calls: int, now: datetime | None = None,
            pause: float = PAUSE_SEC) -> dict:
    now = now or datetime.now(timezone.utc)
    data = load(path)
    parts = data["parts"]
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    done = thin = 0
    stopped = ""
    for q in refresh_order(queries, parts, now)[:max_calls]:
        try:
            prices, fit = client.search_prices(q)
        except RuntimeError as e:
            stopped = str(e)
            break
        b = band(prices)
        rec = {"q": q["q"], "at": stamp, "fit": bool(fit), "n": len([p for p in prices if p and p > 0])}
        if b:
            rec.update(b)
        else:
            thin += 1
        parts[q["key"]] = rec
        done += 1
        if pause:
            time.sleep(pause)
    data["asOf"] = stamp
    data["parts"] = dict(sorted(parts.items()))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=0, sort_keys=True, ensure_ascii=False) + "\n")
    priced = sum(1 for v in parts.values() if v.get("n", 0) >= MIN_N and "low" in v)
    print(f"ebay prices: {done} queried this run ({thin} with <{MIN_N} listings); "
          f"{priced}/{len(queries)} parts have a live band; file {path}")
    if stopped:
        print(f"::warning::stopped early: {stopped}")
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max-calls", type=int, default=2000)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--dry-run", action="store_true", help="print the query plan, call nothing")
    args = ap.parse_args(argv)

    import junkyard_scraper as js  # noqa: WPS433 - the DB lives there
    queries = build_queries(js.UNOBTANIUM_DB)
    if args.dry_run:
        parts = load(Path(args.path))["parts"]
        order = refresh_order(queries, parts, datetime.now(timezone.utc))
        print(f"{len(queries)} queries; first {min(10, len(order))} in refresh order:")
        for q in order[:10]:
            print(f"  {q['key']}  ->  {q['q']}  [{q['year']} {q['make']} {q['model']}]")
        return 0
    cid, sec = os.environ.get("EBAY_CLIENT_ID", "").strip(), os.environ.get("EBAY_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        print("::error::EBAY_CLIENT_ID / EBAY_CLIENT_SECRET not set")
        return 2
    if requests is None:
        print("::error::python 'requests' is required")
        return 2
    refresh(EbayClient(cid, sec), queries, Path(args.path), args.max_calls)
    return 0


if __name__ == "__main__":
    sys.exit(main())
