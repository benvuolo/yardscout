#!/usr/bin/env python3
"""Yard list freshness (scraper/yard_freshness.py and its wiring).
Run:  python3 scraper/test_yard_freshness.py   (offline, temp files only)

Covers: business-day counting (weekends, Thanksgiving), the stale / frozen
thresholds, "a car added or removed" as the only change, unread scans
(carried, missing) neither changing nor confirming a list, seeding from the
existing yard_health fingerprint, the flush rule after a long freeze, the
yard-row columns (old readers unaffected), yard_health.json agreeing with
the published columns, and held arrivals leaving alerts and "new this week"."""
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yard_freshness as yf  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


def T(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)


def Z(s):
    return s + ":00Z"


# ---------- business days ----------
# Fri 11-13 02:00 -> Tue 11-17 02:00: Friday's and Monday's 14-22 UTC blocks.
check("bd: Fri night -> Tue night = 2", yf.full_business_days(T("2026-11-13T02:00"), T("2026-11-17T02:00")) == 2)
check("bd: a plain weekend (Fri 23:00 -> Mon 13:00) = 0",
      yf.full_business_days(T("2026-11-13T23:00"), T("2026-11-16T13:00")) == 0)
check("bd: a block only partly inside does not count",
      yf.full_business_days(T("2026-11-16T15:00"), T("2026-11-17T21:00")) == 0)
check("bd: Thanksgiving 2026 is Nov 26", yf.is_yard_holiday(datetime(2026, 11, 26).date())
      and yf.is_yard_holiday(datetime(2026, 11, 27).date()) and not yf.is_yard_holiday(datetime(2026, 11, 25).date()))
check("bd: Thanksgiving 2027 is Nov 25", yf.is_yard_holiday(datetime(2027, 11, 25).date())
      and not yf.is_yard_holiday(datetime(2027, 11, 18).date()))
check("bd: Christmas / New Year", all(yf.is_yard_holiday(datetime(*d).date())
                                      for d in ((2026, 12, 24), (2026, 12, 25), (2026, 12, 31), (2027, 1, 1))))
check("bd: Thanksgiving week Wed night -> Mon night = 1 (Thu, Fri, weekend skipped)",
      yf.full_business_days(T("2026-11-25T23:00"), T("2026-11-30T23:00")) == 1)
check("bd: empty / reversed window = 0", yf.full_business_days(T("2026-11-17T00:00"), T("2026-11-16T00:00")) == 0)

# ---------- thresholds ----------
check("thresholds as measured (3 and 10 full business days)",
      yf.STALE_BUSINESS_DAYS == 3 and yf.FROZEN_BUSINESS_DAYS == 10)
ch = "2026-11-13T02:00:00Z"   # Friday early UTC: Friday's block counts
check("state: 2 bd -> fresh", yf.list_state(ch, "2026-11-17T02:00:00Z") == "")
check("state: 3 bd -> stale (Fri, Mon, Tue blocks)", yf.list_state(ch, "2026-11-17T23:00:00Z") == "stale")
check("state: 9 bd -> stale", yf.list_state(ch, "2026-11-25T23:00:00Z") == "stale")
# Fri 13, Mon 16..Fri 20 (6), Mon 23, Tue 24, Wed 25 = 9; Thu 26 / Fri 27
# holiday; Mon 30 = 10.
check("state: holidays do not count toward frozen", yf.list_state(ch, "2026-11-27T23:00:00Z") == "stale")
check("state: 10 bd -> frozen", yf.list_state(ch, "2026-11-30T23:00:00Z") == "frozen")
check("state: unknown change time -> fresh (never claims staleness)", yf.list_state(None, "2026-11-30T23:00:00Z") == "")

# ---------- one scan's freshness ----------
NOW = "2026-11-18T13:47:46Z"
ids = [f"c{i}" for i in range(100)]
fp = yf.id_fingerprint(ids)
check("fingerprint ignores order and duplicates", fp == yf.id_fingerprint(list(reversed(ids)) + ["c1"]))

out = yf.update_list_freshness({}, None, {"New Yard": ids}, set(), NOW)
check("a yard seen for the first time: changed and read now",
      out["New Yard"]["listChangedAt"] == NOW and out["New Yard"]["listReadAt"] == NOW
      and out["New Yard"]["listState"] == "" and "listFlushAt" not in out["New Yard"])

prev = {"Y": {"listFingerprint": fp, "listChangedAt": "2026-11-06T11:46:31Z", "listReadAt": "2026-11-18T08:41:39Z",
              "fingerprint": "whatever", "lastChangedAt": "2026-11-17T23:47:19Z"}}
out = yf.update_list_freshness(prev, "2026-11-18T08:41:39Z", {"Y": ids}, set(), NOW,
                               date_fps={"Y": "dates-edited"})
check("same cars, dates edited: NOT a change (only adds/removals count)",
      out["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z" and out["Y"]["listReadAt"] == NOW, str(out["Y"]))
check("…and a list unchanged since Nov 6 is stale on Nov 18", out["Y"]["listState"] == "stale")
out = yf.update_list_freshness(prev, "2026-11-18T08:41:39Z", {"Y": ids + ["new1"]}, set(), NOW)
check("one car added: changed now", out["Y"]["listChangedAt"] == NOW and out["Y"]["listState"] == "")
out = yf.update_list_freshness(prev, "2026-11-18T08:41:39Z", {"Y": ids[1:]}, set(), NOW)
check("one car removed: changed now", out["Y"]["listChangedAt"] == NOW)

# not read: carried this scan
out = yf.update_list_freshness(prev, "2026-11-18T08:41:39Z", {"Y": ids[:10]}, {"Y"}, NOW)
check("carried (not read): no change recorded, last read kept, fingerprint of the last READ copy kept",
      out["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z" and out["Y"]["listReadAt"] == "2026-11-18T08:41:39Z"
      and out["Y"]["listFingerprint"] == fp, str(out["Y"]))
after = {"Y": {**prev["Y"], **{k: out["Y"][k] for k in ("listFingerprint", "listChangedAt", "listReadAt")},
               "carried": True}}
out2 = yf.update_list_freshness(after, NOW, {"Y": ids}, set(), "2026-11-18T17:40:00Z")
check("read again after a carried scan: compared with the last READ copy (unchanged)",
      out2["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z" and out2["Y"]["listReadAt"] == "2026-11-18T17:40:00Z")
# missing yard returns (its entry kept the list fields)
miss = {"Y": {**prev["Y"], "missingScans": 3}}
out = yf.update_list_freshness(miss, NOW, {"Y": ids}, set(), "2026-11-18T17:40:00Z")
check("missing yard back with the same cars: unchanged since its last change",
      out["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z")

# seeding: no listFingerprint yet (first scan with this code)
seed = {"Y": {"fingerprint": "abc", "lastChangedAt": "2026-11-06T11:46:31Z", "unchangedScans": 40}}
out = yf.update_list_freshness(seed, "2026-11-18T08:41:39Z", {"Y": ids}, set(), NOW, date_fps={"Y": "abc"})
check("seed: id|date fingerprint unchanged -> changed at its lastChangedAt",
      out["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z" and out["Y"]["listFingerprint"] == fp)
out = yf.update_list_freshness(seed, "2026-11-18T08:41:39Z", {"Y": ids}, set(), NOW, date_fps={"Y": "xyz"})
check("seed: id|date fingerprint changed -> changed now (never older than known)", out["Y"]["listChangedAt"] == NOW)
out = yf.update_list_freshness(seed, "2026-11-18T08:41:39Z", {"Y": ids}, {"Y"}, NOW, date_fps={"Y": "abc"})
check("seed while carried: last change from yard_health, nothing confirmed",
      out["Y"]["listChangedAt"] == "2026-11-06T11:46:31Z" and out["Y"]["listFingerprint"] == "")

# ---------- flush ----------
frozen_prev = {"F": {"listFingerprint": fp, "listChangedAt": "2026-10-22T02:14:15Z",
                     "listReadAt": "2026-11-18T08:41:39Z"}}
before = set(ids)
big = ids[50:] + [f"n{i}" for i in range(60)]           # 50 removed, 60 added
out = yf.update_list_freshness(frozen_prev, "2026-11-18T08:41:39Z", {"F": big}, set(), NOW,
                               prev_ids=lambda n: before)
check("flush: frozen since Oct 22, then 55% of the list at once -> listFlushAt = now",
      out["F"].get("listFlushAt") == NOW and out["F"]["listChangedAt"] == NOW
      and out["F"]["flush"]["added"] == 60 and out["F"]["flush"]["removed"] == 50, str(out["F"]))
small = ids[5:] + [f"n{i}" for i in range(5)]
out = yf.update_list_freshness(frozen_prev, "2026-11-18T08:41:39Z", {"F": small}, set(), NOW,
                               prev_ids=lambda n: before)
check("frozen list back with a 5% change: not a flush (its new cars are new)",
      "listFlushAt" not in out["F"] and out["F"]["flush"]["share"] == 0.05)
fresh_prev = {"F": {**frozen_prev["F"], "listChangedAt": "2026-11-16T02:00:00Z"}}
out = yf.update_list_freshness(fresh_prev, "2026-11-18T08:41:39Z", {"F": big}, set(), NOW,
                               prev_ids=lambda n: before, seen_before=lambda n, s: set(s))
check("a 55% change on a list that was NOT frozen: not the flush rule (and all 60 ids came back: not a jump)",
      "flush" not in out["F"] and "listFlushAt" not in out["F"] and out["F"]["jump"]["returning"] == 60)
unread_prev = {"F": {**frozen_prev["F"], "listChangedAt": "2026-11-05T02:00:00Z",
                     "listReadAt": "2026-11-10T02:00:00Z"}}
out = yf.update_list_freshness(unread_prev, "2026-11-18T08:41:39Z", {"F": big}, set(), NOW,
                               prev_ids=lambda n: before, seen_before=lambda n, s: set(s))
check("frozen only if the unread days are counted: not a flush (unread is not unchanged)",
      "flush" not in out["F"] and "listFlushAt" not in out["F"])
check("the flush share is the lifespan writer's (one rule)", yf.FLUSH_SHARE == 0.4)
kept = {"F": {"listFingerprint": yf.id_fingerprint(big), "listChangedAt": NOW, "listReadAt": NOW, "listFlushAt": NOW}}
later = (datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=7, hours=23)).strftime("%Y-%m-%dT%H:%M:%SZ")
out = yf.update_list_freshness(kept, NOW, {"F": big}, set(), later)
check("flush mark kept for 7d23h", out["F"].get("listFlushAt") == NOW)
later = (datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
out = yf.update_list_freshness(kept, NOW, {"F": big}, set(), later)
check("flush mark dropped after 8 days", "listFlushAt" not in out["F"])

check("flush car: listed on/before the flush day", yf.flush_car("2026-11-17", NOW) and yf.flush_car("2026-11-18", NOW))
check("not a flush car: listed after the flush day / no flush / no date",
      not yf.flush_car("2026-11-19", NOW) and not yf.flush_car("2026-11-17", None) and not yf.flush_car("", NOW))
check("arrival held: frozen yard or flush car only",
      yf.arrival_held("frozen", None, "2026-11-18") and yf.arrival_held("", NOW, "2026-11-17")
      and not yf.arrival_held("stale", None, "2026-11-18") and not yf.arrival_held("", None, "2026-11-18"))

# ---------- yard rows ----------
BASE_YF = ["location", "city", "state", "lat", "lng", "avgLifespanDays", "lifespanBasis"]
payload = {"scrapedAt": NOW, "yardFields": list(BASE_YF),
           "yards": [["A", "a", "TX", 1.0, 2.0, 60, "yard"],
                     ["B", "b", "TX", 1.0, 2.0, None, None, "2026-01-01T00:00:00Z", "stale", None, None],  # carried row
                     ["C", "c", "TX", 1.0, 2.0, 50, "chain"]]}
info = {"A": {"listChangedAt": NOW, "listReadAt": NOW, "listState": ""},
        "B": {"listChangedAt": "2026-10-22T02:14:15Z", "listReadAt": "2026-11-17T23:47:19Z", "listState": "frozen"},
        "C": {"listChangedAt": NOW, "listReadAt": NOW, "listState": "", "listFlushAt": NOW}}
yf.annotate_yard_rows(payload, info)
check("yardFields: base columns untouched, list columns appended at the end",
      payload["yardFields"] == BASE_YF + yf.YARD_LIST_FIELDS, str(payload["yardFields"]))
check("old readers: positions 0..6 unchanged (app expandV2Row reads y[0..6])",
      [r[:7] for r in payload["yards"]] == [["A", "a", "TX", 1.0, 2.0, 60, "yard"],
                                            ["B", "b", "TX", 1.0, 2.0, None, None],
                                            ["C", "c", "TX", 1.0, 2.0, 50, "chain"]])
check("every row has exactly yardFields' width (a carried row's old columns replaced)",
      all(len(r) == len(payload["yardFields"]) for r in payload["yards"]))
check("columns: listReadAt null when read this scan, set when not read",
      payload["yards"][0][7:] == [NOW, "", None, None]
      and payload["yards"][1][7:] == ["2026-10-22T02:14:15Z", "frozen", "2026-11-17T23:47:19Z", None]
      and payload["yards"][2][7:] == [NOW, "", None, NOW], str(payload["yards"]))
yf.annotate_yard_rows(payload, info)
check("annotating twice is idempotent", payload["yardFields"] == BASE_YF + yf.YARD_LIST_FIELDS
      and all(len(r) == 11 for r in payload["yards"]))
cols = yf.yard_list_columns(payload)
check("columns read back by name", cols[1] == ("2026-10-22T02:14:15Z", "frozen", "2026-11-17T23:47:19Z", None))
check("payload without the columns -> {}", yf.yard_list_columns({"yardFields": BASE_YF, "yards": [["A"]]}) == {})

# ---------- the scan's wiring ----------
import junkyard_scraper as js  # noqa: E402
import push_inventory  # noqa: E402
import inventory_shards  # noqa: E402

check("one flush rule: yard_freshness.FLUSH_SHARE == LIFESPAN_FLUSH_SHARE",
      yf.FLUSH_SHARE == js.LIFESPAN_FLUSH_SHARE)

today = datetime.now(timezone.utc)
scan_now = today.strftime("%Y-%m-%dT%H:%M:%SZ")
d_recent = (today - timedelta(days=1)).strftime("%Y-%m-%d")
d_old = (today - timedelta(days=40)).strftime("%Y-%m-%d")
long_ago = (today - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
FIELDS = ["id", "vin", "year", "make", "model", "row", "dateAdded", "yard", "partSet", "maxValue", "premium"]


def car(i, yard, d):
    return [f"{yard}-{i}", "", 2010, "Honda", "Civic", "1", d, yard, -1, 0, 0]


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    js.DATA_DIR = td
    js.LIVE_FILE = td / "inventory_live.json"
    js.YARD_HEALTH_FILE = td / "yard_health.json"
    js._CARRIED_YARDS.clear()
    # Yard 0 "Live - A": changes every scan. Yard 1 "Frozen - B": same 40
    # cars since 30 days ago (one dated yesterday by the yard). Yard 2
    # "Flush - C": frozen 30 days, then 30 of 40 cars replaced this scan.
    yards = [["Live - A", "A", "TX", 30.0, -97.0, 60, "yard"],
             ["Frozen - B", "B", "TX", 30.1, -97.1, 60, "yard"],
             ["Flush - C", "C", "TX", 30.2, -97.2, 60, "yard"]]
    prev_rows = ([car(i, 0, d_old) for i in range(40)] + [car(i, 1, d_old) for i in range(39)]
                 + [car(39, 1, d_recent)] + [car(i, 2, d_old) for i in range(40)])
    js.LIVE_FILE.write_text(json.dumps({"schemaVersion": 2, "scrapedAt": long_ago, "fields": FIELDS,
                                        "yardFields": BASE_YF, "yards": yards, "vehicles": prev_rows}))

    def ids_of(rows, y):
        return [r[0] for r in rows if r[7] == y]
    prev_health = {"scrapedAt": (today - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ"), "yards": {
        "Live - A": {"listFingerprint": yf.id_fingerprint(ids_of(prev_rows, 0)), "listChangedAt": long_ago,
                     "listReadAt": long_ago, "fingerprint": "x", "lastChangedAt": long_ago},
        "Frozen - B": {"listFingerprint": yf.id_fingerprint(ids_of(prev_rows, 1)), "listChangedAt": long_ago,
                       "listReadAt": (today - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "fingerprint": "x", "lastChangedAt": long_ago, "unchangedScans": 150},
        "Flush - C": {"listFingerprint": yf.id_fingerprint(ids_of(prev_rows, 2)), "listChangedAt": long_ago,
                      "listReadAt": (today - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "fingerprint": "x", "lastChangedAt": long_ago, "unchangedScans": 150},
        "Gone - D": {"count": 5, "fingerprint": "g", "lastChangedAt": long_ago, "listFingerprint": "gf",
                     "listChangedAt": long_ago, "listReadAt": long_ago, "unchangedScans": 2},
    }}
    js.YARD_HEALTH_FILE.write_text(json.dumps(prev_health))
    new_rows = ([car(i, 0, d_old) for i in range(1, 40)] + [car(99, 0, d_recent)]
                + [car(i, 1, d_old) for i in range(39)] + [car(39, 1, d_recent)]
                + [car(i, 2, d_old) for i in range(10)] + [car(100 + i, 2, d_recent) for i in range(30)])
    payload = {"schemaVersion": 2, "scrapedAt": scan_now, "fields": FIELDS, "yardFields": list(BASE_YF),
               "yards": [list(y) for y in yards], "vehicles": new_rows, "partSets": [], "vpic": {}}
    js._apply_yard_list_freshness(payload)
    cols = yf.yard_list_columns(payload)
    check("scan: live yard changed now", cols[0][0] == scan_now and cols[0][1] == "", str(cols[0]))
    check("scan: unchanged 30-day list is frozen", cols[1][0] == long_ago and cols[1][1] == "frozen", str(cols[1]))
    check("scan: frozen list replaced 75% at once -> flush now, fresh state",
          cols[2][0] == scan_now and cols[2][1] == "" and cols[2][3] == scan_now, str(cols[2]))
    js._update_yard_health(payload)
    h = json.loads(js.YARD_HEALTH_FILE.read_text())["yards"]
    check("yard_health.json carries the same list fields as the published rows",
          all(h[n]["listChangedAt"] == cols[i][0] for i, n in enumerate(["Live - A", "Frozen - B", "Flush - C"]))
          and h["Flush - C"].get("listFlushAt") == scan_now and "listReadAt" not in h["Frozen - B"])
    # Next scan: the yard is carried (not read). Its last read comes back
    # from the previous file's scrapedAt, as if listReadAt had been stored.
    nxt = (today + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    hf = json.loads(js.YARD_HEALTH_FILE.read_text())
    again = yf.update_list_freshness(hf["yards"], hf["scrapedAt"], {"Frozen - B": ids_of(new_rows, 1)},
                                     {"Frozen - B"}, nxt)
    check("listReadAt left out when it is the scan time: read back exactly on the next (unread) scan",
          again["Frozen - B"]["listReadAt"] == scan_now and again["Frozen - B"]["listChangedAt"] == long_ago,
          str(again["Frozen - B"]))
    # Next scan: "Live - A" goes missing. Its entry keeps the last read time
    # (this scan), so if it comes back changed the flush check knows when.
    p_missing = {**payload, "scrapedAt": nxt, "yards": [list(y) for y in payload["yards"] if y[0] != "Live - A"],
                 "vehicles": []}
    js._LIST_FRESHNESS.clear()
    js._update_yard_health(p_missing)
    hm = json.loads(js.YARD_HEALTH_FILE.read_text())["yards"]["Live - A"]
    check("a yard that goes missing keeps its last read time (the scan before)",
          hm.get("missingScans") == 1 and hm.get("listReadAt") == scan_now and hm.get("listChangedAt") == scan_now, str(hm))
    js.YARD_HEALTH_FILE.write_text(json.dumps(hf))
    check("yard_health.json: listState (what the site marks) for the ops email, only when set",
          h["Frozen - B"].get("listState") == "frozen" and "listState" not in h["Live - A"])
    check("yard_health.json: a missing yard keeps its list fields as last read",
          h["Gone - D"]["listChangedAt"] == long_ago and h["Gone - D"]["listFingerprint"] == "gf"
          and h["Gone - D"]["missingScans"] == 1)
    check("yard_health.json: the ops email's own fields are untouched",
          all(k in h["Frozen - B"] for k in ("count", "fingerprint", "unchangedScans", "lastChangedAt")))

    # alerts: push_inventory.build_arrivals
    arr = push_inventory.build_arrivals(payload)
    by = {}
    for a in arr:
        by[a["location"]] = by.get(a["location"], 0) + 1
    check("alerts: the live yard's new car alerts", by.get("Live - A") == 1, str(by))
    check("alerts: a frozen yard's recently dated car does not", "Frozen - B" not in by, str(by))
    check("alerts: none of the 30 cars that came in with the flush", "Flush - C" not in by, str(by))
    # "new this week" files the site pages read
    js._write_landed_json(payload)
    landed = json.loads((td / "landed.json").read_text())
    week = {y[0]: y[4] for y in landed["yards"]}
    check("landed.json: set out this week counts only real arrivals",
          week == {"Live - A": 1, "Frozen - B": 0, "Flush - C": 0}, str(week))
    check("landed.json: per-make recent list leaves held cars out",
          landed["makes"]["Honda"]["recentCount"] == 1, str(landed["makes"]["Honda"]["recentCount"]))
    js._write_junkyards_json(payload)
    jy = json.loads((td / "junkyards.json").read_text())
    check("junkyards.json: setOutLast7Days the same", [y[6] for y in jy["yards"]] == [1, 0, 0], str(jy["yards"]))
    # A car the flushed yard lists AFTER the flush day is new as usual.
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    payload["vehicles"].append(car(500, 2, tomorrow))
    arr = push_inventory.build_arrivals(payload)
    check("alerts: a car listed after the flush day alerts again",
          sum(1 for a in arr if a["location"] == "Flush - C") == 1)
    payload["vehicles"].pop()
    # The manifest carries the columns verbatim (the app reads them by name).
    info = inventory_shards.write_inventory_shards(payload, {}, td)
    man = json.loads((td / "inv" / "manifest.json").read_text())
    check("manifest: yardFields + rows carry the list columns",
          man["yardFields"] == BASE_YF + yf.YARD_LIST_FIELDS and man["yards"][1][8] == "frozen"
          and man["yards"][2][10] == scan_now)
    # The API directory is built from the same rows (push_inventory.build_shards).
    directory, _ = push_inventory.build_shards(payload)
    check("API directory (/v1/yards, read by the site worker) carries them too",
          directory["yardFields"] == man["yardFields"] and directory["yards"][1][7] == long_ago)

    # Never fatal: a broken history file leaves the payload as it was.
    js.YARD_HEALTH_FILE.write_text("{not json")
    p2 = {"schemaVersion": 2, "scrapedAt": scan_now, "fields": FIELDS, "yardFields": list(BASE_YF),
          "yards": [list(y) for y in yards], "vehicles": new_rows}
    js._apply_yard_list_freshness(p2)
    c2 = yf.yard_list_columns(p2)
    check("no history file: every yard 'changed now' (never a false stale mark)",
          all(c[0] == scan_now and c[1] == "" for c in c2.values()), str(c2))
    bad = {"schemaVersion": 2, "scrapedAt": scan_now, "fields": ["id"], "yardFields": list(BASE_YF),
           "yards": [list(y) for y in yards], "vehicles": [["x"]]}
    js._apply_yard_list_freshness(bad)
    check("a payload the step cannot read ships without the columns", bad["yardFields"] == BASE_YF)

print()
if fails:
    print(f"{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("ALL PASS")
