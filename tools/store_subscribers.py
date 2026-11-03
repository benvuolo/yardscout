#!/usr/bin/env python3
"""Active paid subscriptions per store, for the daily ops email.

Writes one JSON object to stdout (the workflow stores it in KV
ops:store-subs, which backend/src/ops_monitor.js reads):

  {"at": "...Z",
   "apple":  {"active": 4, "trial": 0, "asOf": "2026-11-02"} | {"error": "..."},
   "google": {"active": 1, "asOf": "2026-11-02", "file": "..."} | {"error": "..."}}

Apple: App Store Connect Sales and Trends, SUBSCRIPTION/SUMMARY (the newest
       published day; Apple publishes a day behind). Counts paid
       subscriptions only: comps, TestFlight and sandbox purchases never
       appear in it.
       Env: ASC_KEY_ID, ASC_ISSUER_ID, ASC_P8 (a Sales-role key), ASC_VENDOR.
Google: Play Console's monthly subscriptions report, which Google writes to
       the developer account's Cloud Storage bucket
       (financial-stats/subscriptions/subscriptions_<package>_<YYYYMM>_*.csv).
       The service account needs Play Console permission "View financial
       data"; the bucket name is on Play Console → Download reports →
       Financial → "Copy Cloud Storage URI".
       Env: PLAY_SA_JSON (service-account JSON), PLAY_REPORTS_BUCKET
       ("pubsite_prod_rev_…" or the gs:// URI), PLAY_PACKAGE.

Either store failing leaves an "error" for that store only. Nothing secret
is printed.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import os
import re
import sys
import time


# ---------------------------------------------------------------- Google parsing
def decode_report(raw: bytes) -> str:
    """Play reports are UTF-16 (with BOM) or UTF-8; handle both."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if len(raw) > 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        return raw.decode("utf-16-le")
    return raw.decode("utf-8-sig")


def _col(fields: list[str], *want: str, avoid: tuple[str, ...] = ()) -> str | None:
    for f in fields:
        low = f.strip().lower()
        if all(w in low for w in want) and not any(a in low for a in avoid):
            return f
    return None


def active_from_report(text: str) -> tuple[int, str]:
    """(active subscriptions on the newest date, that date) from one report."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty report")
    fields = list(rows[0].keys())
    date_col = _col(fields, "date")
    act_col = _col(fields, "active", avoid=("cancel", "new"))
    if not date_col or not act_col:
        raise ValueError(f"unexpected columns: {fields[:8]}")
    newest = max(r[date_col].strip() for r in rows if r.get(date_col))
    total = 0
    for r in rows:
        if r.get(date_col, "").strip() == newest:
            try:
                total += int(float(r.get(act_col) or 0))
            except ValueError:
                pass
    return total, newest


def pick_report(names: list[str], package: str) -> str | None:
    """Newest month's subscriptions report for this package."""
    cands = [n for n in names if package in n and re.search(r"_(\d{6})", n) and n.lower().endswith(".csv")]
    if not cands:
        return None
    return max(cands, key=lambda n: re.search(r"_(\d{6})", n).group(1))


def bucket_name(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^gs://", "", raw)
    return raw.split("/", 1)[0]


# ---------------------------------------------------------------- Google fetch
def google_count(sa_json: str, bucket_raw: str, package: str) -> dict:
    import jwt  # pyjwt
    import requests
    raw = sa_json.strip()
    sa, _ = json.JSONDecoder().raw_decode(raw[raw.find("{"):])
    now = int(time.time())
    assertion = jwt.encode({"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/devstorage.read_only",
                            "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600},
                           sa["private_key"], algorithm="RS256")
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30,
                      data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
    if r.status_code != 200:
        return {"error": f"Google sign-in failed (HTTP {r.status_code})"}
    H = {"Authorization": f"Bearer {r.json()['access_token']}"}
    bucket = bucket_name(bucket_raw)
    names: list[str] = []
    page = None
    while True:
        params = {"prefix": "financial-stats/subscriptions/", "fields": "items(name),nextPageToken"}
        if page:
            params["pageToken"] = page
        r = requests.get(f"https://storage.googleapis.com/storage/v1/b/{bucket}/o", headers=H, params=params, timeout=30)
        if r.status_code in (401, 403):
            return {"error": "the service account can't read Play reports: in Play Console → Users and permissions, "
                             "give it \"View financial data\""}
        if r.status_code != 200:
            return {"error": f"listing reports failed (HTTP {r.status_code})"}
        j = r.json()
        names += [i["name"] for i in j.get("items", [])]
        page = j.get("nextPageToken")
        if not page:
            break
    name = pick_report(names, package)
    if not name:
        return {"error": "no subscriptions report in the bucket yet"}
    from urllib.parse import quote
    r = requests.get(f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{quote(name, safe='')}",
                     headers=H, params={"alt": "media"}, timeout=60)
    if r.status_code != 200:
        return {"error": f"downloading {name.rsplit('/', 1)[-1]} failed (HTTP {r.status_code})"}
    body = r.content
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    try:
        active, as_of = active_from_report(decode_report(body))
    except ValueError as e:
        return {"error": f"couldn't read {name.rsplit('/', 1)[-1]}: {e}"}
    return {"active": active, "asOf": as_of, "file": name.rsplit("/", 1)[-1]}


# ---------------------------------------------------------------- Apple
def apple_count(key_id: str, issuer: str, p8: str, vendor: str, today: dt.date | None = None) -> dict:
    import jwt
    import requests
    key = p8.strip().replace("\\n", "\n")
    tok = jwt.encode({"iss": issuer, "iat": int(time.time()), "exp": int(time.time()) + 900, "aud": "appstoreconnect-v1"},
                     key, algorithm="ES256", headers={"kid": key_id, "typ": "JWT"})
    H = {"Authorization": f"Bearer {tok}", "Accept": "application/a-gzip"}
    today = today or dt.date.today()
    for i in range(1, 6):
        day = (today - dt.timedelta(days=i)).isoformat()
        r = requests.get("https://api.appstoreconnect.apple.com/v1/salesReports", headers=H, timeout=60, params={
            "filter[frequency]": "DAILY", "filter[reportType]": "SUBSCRIPTION", "filter[reportSubType]": "SUMMARY",
            "filter[vendorNumber]": vendor, "filter[reportDate]": day, "filter[version]": "1_4"})
        if r.status_code == 404:
            continue
        if r.status_code == 403:
            return {"error": "the App Store key can't read Sales and Trends (needs the Sales role)"}
        if r.status_code != 200:
            return {"error": f"App Store report HTTP {r.status_code}"}
        rows = list(csv.DictReader(io.StringIO(gzip.decompress(r.content).decode()), delimiter="\t"))
        act = sum(int(x.get("Active Standard Price Subscriptions") or 0) for x in rows)
        trial = sum(int(x.get("Active Free Trial Introductory Offer Subscriptions") or 0) for x in rows)
        return {"active": act, "trial": trial, "asOf": day}
    return {"active": 0, "trial": 0, "asOf": (today - dt.timedelta(days=1)).isoformat(),
            "note": "no subscription report in 5 days (none active)"}


def main() -> int:
    out: dict = {"at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    e = os.environ
    if e.get("ASC_VENDOR") and e.get("ASC_P8") and e.get("ASC_KEY_ID") and e.get("ASC_ISSUER_ID"):
        try:
            out["apple"] = apple_count(e["ASC_KEY_ID"], e["ASC_ISSUER_ID"], e["ASC_P8"], e["ASC_VENDOR"])
        except Exception as ex:  # never sink the other store
            out["apple"] = {"error": f"{type(ex).__name__}"}
    else:
        out["apple"] = {"error": "not set up (App Store Sales key / vendor number missing)"}
    if e.get("PLAY_SA_JSON") and e.get("PLAY_REPORTS_BUCKET"):
        try:
            out["google"] = google_count(e["PLAY_SA_JSON"], e["PLAY_REPORTS_BUCKET"], e.get("PLAY_PACKAGE", "io.yardscout.app"))
        except Exception as ex:
            out["google"] = {"error": f"{type(ex).__name__}"}
    else:
        out["google"] = {"error": "not set up: add the PLAY_REPORTS_BUCKET repository variable "
                                  "(Play Console → Download reports → Financial → Copy Cloud Storage URI)"}
    json.dump(out, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
