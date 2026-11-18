"""When each yard's own published list last CHANGED, and what that means for
the cars we show from it (data-quality workstream, 2026-11-18).

Some yards keep serving the same list for days or weeks (2026-11-17: Budget
U-Pull-It - Bartow served the same 879 cars from Nov 6 to Nov 18; Wrench-A-
Part - Holland has served one 1,113-car list since Oct 22). The scan already
noticed ("STALE YARD" in the log, yard_health.json) but nothing reached a
visitor, who could drive to a car from a list nobody had updated in weeks.

Per yard, per scan:
  listChangedAt  the scan at which a car was last ADDED to or REMOVED from
                 the yard's list (the set of car ids). A date-only edit is
                 not a change. A scan that could not read the yard (fetch
                 failed and the last copy was re-served, or the yard was
                 missing) is NOT READ: it neither changes nor confirms the
                 list, and the next read is compared with the last READ copy.
  listReadAt     the last scan that actually read the yard's list.
  listState      "" | "stale" | "frozen", from full business days since
                 listChangedAt (thresholds below, measured on the scan
                 history; ops/data.md 2026-11-18).
  listFlushAt    the scan at which a list that had been frozen suddenly
                 changed by LIFESPAN_FLUSH_SHARE (40%) or more of its cars at
                 once: the same "one scan carries 40%" rule the lifespan
                 writer uses to call a yard's departures a feed flush
                 (db.yard_departure_reliability). Cars that came in with the
                 flush are not new arrivals: no alerts, not counted in "new
                 this week" (kept FLUSH_HOLD_DAYS).

Published as four extra columns at the END of every yard row in
inventory_live.json, inv/manifest.json and the API's yard directory (named
in yardFields), so every reader that indexes yard rows by position or by
name keeps working; old app builds simply never read them.

Standard library only (push_inventory.py imports it too).
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

# A weekday counts as a business day for a yard when its whole 14:00-22:00
# UTC block (9 am-5 pm ET, 6 am-2 pm PT: when yards set cars out and crush)
# lies inside the window: the ops email's fullBusinessDaysBetween
# (backend/src/ops_monitor.js), plus the days most self-service yards close.
BIZ_START_H, BIZ_END_H = 14, 22

# "May be out of date": no car added or removed for this many full business
# days. On the 2026-10-25 .. 11-18 history (160 scans, 301 yards, 6,791
# closed gaps between list changes), daily-updating yards went 3+ business
# days without a change in 27 of 6,561 gaps (0.41%), and all 27 look like
# feed lags (whole chains at once, or one yard skipping a week); 2 business
# days happened 173 times (2.6%) and would flag ordinary lulls.
STALE_BUSINESS_DAYS = 3
# "Frozen": cars are held back from Newest arrivals and alerts (still listed
# on the yard's own page, marked). Two working weeks: in the same history
# only 2 closed gaps ever reached it (0.03%), while the slowest regular
# updater (Budget Bartow, a list about every 12 calendar days) peaks at 8.
FROZEN_BUSINESS_DAYS = 10
# How long cars that arrived with a flush stay out of "new": past the 7-day
# "new this week" window and the 3-day alert window.
FLUSH_HOLD_DAYS = 8
# The lifespan writer's feed-flush share (junkyard_scraper.LIFESPAN_FLUSH_SHARE),
# repeated here so this module needs no import of the scraper; a test checks
# the two agree.
FLUSH_SHARE = 0.4
# List jump (2026-11-18 follow-up): one scan adds cars under ids the yard
# has never listed, at least JUMP_SHARE of the list and JUMP_MIN_CARS cars.
# Marked like a flush (listFlushAt, listFlushWhy "jump"): the cars it
# brought are not new arrivals. Measured in ops/data.md.
JUMP_SHARE = 0.3
JUMP_MIN_CARS = 50

YARD_LIST_FIELDS = ["listChangedAt", "listState", "listReadAt", "listFlushAt"]


def _p(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_yard_holiday(d: date) -> bool:
    """Days most self-service yards are closed: Thanksgiving and the Friday
    after, Dec 24, Dec 25, Dec 31, Jan 1."""
    if d.month == 11 and d.weekday() in (3, 4):
        first_thu = 1 + (3 - date(d.year, 11, 1).weekday()) % 7
        tg = first_thu + 21
        return d.day == tg or (d.weekday() == 4 and d.day == tg + 1)
    return (d.month, d.day) in ((12, 24), (12, 25), (12, 31), (1, 1))


def full_business_days(a: datetime, b: datetime) -> int:
    """Weekdays (holidays excluded) whose 14:00-22:00 UTC block lies wholly
    inside [a, b]."""
    if not (b > a):
        return 0
    n = 0
    d = datetime(a.year, a.month, a.day, tzinfo=timezone.utc)
    while d <= b:
        if d.weekday() < 5 and not is_yard_holiday(d.date()) \
                and d + timedelta(hours=BIZ_START_H) >= a and d + timedelta(hours=BIZ_END_H) <= b:
            n += 1
        d += timedelta(days=1)
    return n


def list_state(changed_at: str | None, now: str) -> str:
    """"" (fresh, or unknown), "stale" or "frozen" for a list last changed at
    changed_at, as of now. Unread time counts: what we show is as old as the
    last change we saw."""
    a, b = _p(changed_at), _p(now)
    if a is None or b is None:
        return ""
    k = full_business_days(a, b)
    return "frozen" if k >= FROZEN_BUSINESS_DAYS else "stale" if k >= STALE_BUSINESS_DAYS else ""


def id_fingerprint(ids) -> str:
    """The list as a set of car ids (order and dates ignored)."""
    return hashlib.sha1("\n".join(sorted({str(i) for i in ids})).encode()).hexdigest()[:16]


def update_list_freshness(prev: dict, prev_scraped_at: str | None, current: dict[str, list],
                          carried: set[str], now: str, date_fps: dict[str, str] | None = None,
                          prev_ids=None, flush_share: float = FLUSH_SHARE,
                          seen_before=None) -> dict[str, dict]:
    """One scan's list freshness for every yard in `current` ({name: [car
    id, ...]}, the published payload, carried yards included).

    prev: yard_health.json "yards" from the previous scan. prev_scraped_at:
    its scrapedAt. carried: yards whose rows this scan re-served (not read).
    date_fps: {name: the id|dateAdded fingerprint yard_health keeps}, used
    only to seed a yard that has no listFingerprint yet (first scan after
    this code ships): unchanged id|date fingerprint => the list has not
    changed since its lastChangedAt; anything else => changed now (the
    conservative side: it never claims a list is older than it is).
    prev_ids(name) -> set of the last read car ids, or None; called for a
    yard whose list changed (flush and jump checks).
    seen_before(name, ids) -> the subset of ids this yard listed at any time
    before (the history DB); called only for a jump candidate. Without it
    every added id counts as never listed (the cautious side: hold).

    Returns {name: {"listFingerprint", "listChangedAt", "listReadAt",
    "listState", optional "listFlushAt" + "listFlushWhy" ("flush" | "jump"),
    optional "flush": {...}, optional "jump": {...}}}."""
    out: dict[str, dict] = {}
    t_now = _p(now)
    for name, ids in current.items():
        p = prev.get(name) or {}
        fp = id_fingerprint(ids)
        read = name not in carried
        p_fp = p.get("listFingerprint")
        p_changed = p.get("listChangedAt")
        # Last read before this scan: recorded, or (first scan after this
        # code) the previous scan unless that one re-served the yard too.
        p_read = p.get("listReadAt") or (
            prev_scraped_at if p and not p.get("carried") and not p.get("missingScans") else None) \
            or p.get("lastChangedAt")
        flush_at = p.get("listFlushAt")
        why = p.get("listFlushWhy") or "flush"
        info: dict = {}
        if not read:
            info = {"listFingerprint": p_fp or "", "listChangedAt": p_changed or p.get("lastChangedAt") or now,
                    "listReadAt": p_read or now}
        elif not p:
            info = {"listFingerprint": fp, "listChangedAt": now, "listReadAt": now}
        elif not p_fp:
            same = bool(date_fps) and p.get("fingerprint") and date_fps.get(name) == p.get("fingerprint")
            info = {"listFingerprint": fp, "listChangedAt": (p.get("lastChangedAt") if same else None) or now,
                    "listReadAt": now}
        elif fp == p_fp:
            info = {"listFingerprint": fp, "listChangedAt": p_changed or now, "listReadAt": now}
        else:
            info = {"listFingerprint": fp, "listChangedAt": now, "listReadAt": now}
            before = prev_ids(name) if prev_ids else None
            cur = {str(i) for i in ids} if before else None
            # Was it frozen as of the last time we READ it? Unread scans are
            # not frozen time (we cannot know the list did not change then).
            a, b = _p(p_changed), _p(p_read)
            if before and a is not None and b is not None and full_business_days(a, b) >= FROZEN_BUSINESS_DAYS:
                added, removed = len(cur - before), len(before - cur)
                share = max(added / max(len(cur), 1), removed / max(len(before), 1))
                info["flush"] = {"added": added, "removed": removed, "share": round(share, 3),
                                 "frozenSince": p_changed}
                if share >= flush_share:
                    flush_at, why = now, "flush"
            # List jump (any list, frozen or not): this one scan added cars
            # under ids the yard has NEVER listed, for a large share of the
            # list: a re-key, a coverage change, a source swap. Ids that come
            # back (a flip between two lists, a partial read recovering) are
            # not counted: they keep their own set-out dates and the alert
            # dedupe already knows them (ops/data.md, 2026-11-18 list jumps).
            if before and flush_at != now:
                added_ids = cur - before
                if len(added_ids) >= max(JUMP_MIN_CARS, JUMP_SHARE * len(cur)):
                    back = seen_before(name, added_ids) if seen_before else set()
                    never = len(added_ids) - len(back)
                    info["jump"] = {"added": len(added_ids), "returning": len(back), "neverListed": never,
                                    "share": round(never / max(len(cur), 1), 3)}
                    if never >= JUMP_MIN_CARS and never >= JUMP_SHARE * len(cur):
                        flush_at, why = now, "jump"
        f = _p(flush_at)
        if f is not None and t_now is not None and t_now - f < timedelta(days=FLUSH_HOLD_DAYS):
            info["listFlushAt"] = flush_at
            info["listFlushWhy"] = why if flush_at == now else (p.get("listFlushWhy") or "flush")
        info["listState"] = list_state(info["listChangedAt"], now)
        out[name] = info
    return out


def annotate_yard_rows(payload: dict, info: dict[str, dict]) -> None:
    """Append YARD_LIST_FIELDS to payload["yardFields"] and every yard row
    (replacing them if a row already carries them, e.g. a carried-forward
    yard from the previous publish). listReadAt is null when this scan read
    the yard; listFlushAt is null with no flush in the last FLUSH_HOLD_DAYS."""
    yf = list(payload.get("yardFields") or [])
    base = len(yf)
    for k in YARD_LIST_FIELDS:
        if k in yf:
            base = min(base, yf.index(k))
    yf = yf[:base] + YARD_LIST_FIELDS
    now = payload.get("scrapedAt")
    rows = []
    for y in payload.get("yards") or []:
        r = list(y[:base]) + [None] * max(0, base - len(y))
        i = info.get(y[0]) if y else None
        if i:
            r += [i.get("listChangedAt"), i.get("listState") or "",
                  None if i.get("listReadAt") == now else i.get("listReadAt"), i.get("listFlushAt")]
        else:
            r += [None, "", None, None]
        rows.append(r)
    payload["yardFields"] = yf
    payload["yards"] = rows


def yard_list_columns(payload: dict) -> dict[int, tuple]:
    """{yard index: (listChangedAt, listState, listReadAt, listFlushAt)} read
    by column name; {} when the payload predates the columns."""
    yf = payload.get("yardFields") or []
    if "listState" not in yf:
        return {}
    ix = [yf.index(k) if k in yf else -1 for k in YARD_LIST_FIELDS]
    out = {}
    for n, y in enumerate(payload.get("yards") or []):
        out[n] = tuple(y[i] if 0 <= i < len(y) else None for i in ix)
    return out


def flush_car(date_added: str | None, flush_at: str | None) -> bool:
    """A car that came in with its yard's flush: listed on or before the
    flush scan's day (UTC). A car the yard lists later is new as usual."""
    if not flush_at:
        return False
    d = str(date_added or "")[:10]
    return bool(d) and d <= str(flush_at)[:10]


def arrival_held(state: str | None, flush_at: str | None, date_added: str | None) -> bool:
    """True when a car must not be treated as a new arrival (alerts, "new
    this week", Newest arrivals): its yard's list is frozen, or the car came
    in with a flush."""
    return state == "frozen" or flush_car(date_added, flush_at)
