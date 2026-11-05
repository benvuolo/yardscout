"""The one validator for groups/<ns>.json (CURATION_SPEC.md §8).

structural(doc, ctx) -> [problem]   V1-V8, V10 (curate.py before writing,
                                     tests strictly, the payload loader to
                                     drop a namespace)
expire(doc, now)                     build-time evidence expiry (120 days)
old_keys_problems(before, after)     V9 (old keys may only lose claims)
size_trim(payload, budget)           V11
full(doc, recompute, committed)      V12-V15 (with raw)

This file imports nothing from the crawler or the network: the payload
builder loads it with importlib.util.spec_from_file_location. policy.py is
loaded the same way (it is pure data).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_policy():
    spec = importlib.util.spec_from_file_location("_oem_policy", _HERE / "policy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


policy = _load_policy()

NOTE_VERIFIED_RE = re.compile(r"^[A-Za-z/ ]+ catalog: same numbers on every trim and engine for these years \(.+\)$")
NOTE_LIKELY_RE = re.compile(r"^[A-Za-z/ ]+ catalog lists #\S+ for both — .+; verify the number on the part$")


def _canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sig_id(sig) -> str:
    return hashlib.sha1(_canon(sig).encode()).hexdigest()[:10]


def _ts(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def context_from(js, mm=None, status_table=None, policy_sha=None) -> dict:
    """ctx from junkyard_scraper (or any object with the same names)."""
    targets = None
    if mm is not None:
        targets = {(t.ns, t.make, t.model) for ts in mm.by_cat.values() for t in ts}
    return {"categories": getattr(js, "INTERCHANGE_PART_CATEGORIES", {}),
            "engine_families": getattr(js, "ENGINE_FAMILIES", {}),
            "normalize_make": getattr(js, "normalize_make", None),
            "normalize_model": getattr(js, "normalize_model", None),
            "squash": getattr(js, "_squash_model", None),
            "app_matches": getattr(js, "_app_matches", None),
            "targets": targets, "status_table": status_table, "policy_sha256": policy_sha}


def expire(doc: dict, now: datetime, days: int | None = None) -> tuple[dict, list]:
    """Drop groups whose oldest evidence is more than `days` (default 120)
    older than `now`. Fails closed: a group without a timestamp is dropped."""
    days = policy.EVIDENCE_MAX_AGE_DAYS if days is None else days
    dropped = []
    out = dict(doc)
    for key in ("groups", "vg"):
        keep = []
        for g in doc.get(key) or []:
            stamps = [_ts((y.get("closure") or {}).get("oldest_retrieved")) for y in g.get("years") or []]
            if not stamps or any(s is None or now - s > timedelta(days=days) for s in stamps):
                dropped.append(g.get("id"))
            else:
                keep.append(g)
        out[key] = keep
    return out, dropped


def _app_ok(app, ns_makes, year_cap, targets, ns) -> str | None:
    if not isinstance(app, list) or len(app) != 4:
        return f"app is not [make, model, lo, hi]: {app!r}"
    mk, md, lo, hi = app
    if not isinstance(mk, str) or not isinstance(md, str) or not isinstance(lo, int) or not isinstance(hi, int):
        return f"app types: {app!r}"
    if "*" in mk or "*" in md:
        return f"app with '*': {app!r}"
    if mk not in ns_makes:
        return f"app make outside namespace: {app!r}"
    if not (1950 <= lo <= hi <= year_cap):
        return f"app years: {app!r}"
    if targets is not None and (ns, mk, md) not in targets:
        return f"app target not in the validated model map: {app!r}"
    return None


def _note_ok(note: str, tier: str, pns: list) -> str | None:
    if not isinstance(note, str) or not note:
        return "empty note"
    if len(note) > policy.NOTE_MAX_LEN:
        return f"note longer than {policy.NOTE_MAX_LEN}"
    if not policy.NOTE_CHARSET.match(note):
        return f"note charset: {note!r}"
    if policy.NOTE_BANNED.search(note):
        return f"banned word in note: {note!r}"
    rx = NOTE_VERIFIED_RE if tier == "verified" else NOTE_LIKELY_RE
    if not rx.match(note):
        return f"note does not match the {tier} template: {note!r}"
    if tier == "verified" and not any(p in note for p in pns):
        return "verified note names no part number"
    return None


def structural(doc: dict, ctx: dict) -> list:
    """Every problem found (empty = valid)."""
    P = []
    if not isinstance(doc, dict):
        return ["V1 not an object"]
    if doc.get("schema") != policy.SCHEMA:
        P.append(f"V1 schema {doc.get('schema')!r}")
    ns = doc.get("ns")
    if ns not in policy.NAMESPACES:
        return P + [f"V1 unknown namespace {ns!r}"]
    makes = set(policy.NAMESPACES[ns]["makes"])
    as_of = _ts(doc.get("as_of"))
    if as_of is None:
        P.append("V4 as_of missing")
    year_cap = (as_of.year if as_of else datetime.now(timezone.utc).year) + 1
    cats = ctx.get("categories") or {}
    fams = ctx.get("engine_families") or {}
    targets = ctx.get("targets")
    classes = doc.get("classes") or {}
    for key in ("groups", "vg", "likely", "classes", "cells", "raw"):
        if key not in doc:
            P.append(f"V1 missing key {key}")
    if not isinstance(doc.get("groups", []), list) or not isinstance(doc.get("vg", []), list) \
            or not isinstance(doc.get("likely", []), list):
        return P + ["V1 groups/vg/likely must be lists"]
    # V8 policy hash
    if ctx.get("policy_sha256") and doc.get("policy_sha256") != ctx["policy_sha256"]:
        P.append("V8 policy_sha256 does not match the tree")
    # classes (V6, V10)
    for k, c in classes.items():
        if not k.startswith(ns + ":"):
            P.append(f"V6 class {k} outside namespace {ns}")
        for n in c.get("names") or []:
            if policy.RULE4_RE.search(n or ""):
                P.append(f"V10 rule-4 name in class {k}: {n!r}")
    seen_verified = {}
    feed_models_by_class: dict = {}
    for kind_key in ("groups", "vg", "likely"):
        for g in doc.get(kind_key) or []:
            gid = g.get("id", "?")
            tier = g.get("tier")
            # V1 tier and kind routing
            if kind_key == "likely":
                if tier != "likely":
                    P.append(f"V1 {gid}: tier {tier!r} in likely")
            elif tier != "verified":
                P.append(f"V1 {gid}: tier {tier!r}")
            cat = g.get("cat")
            ckind = (cats.get(cat) or {}).get("kind")
            if cat in policy.PHASE3_CATS or ckind == "oem" or (cats.get(cat) or {}).get("clientMin", 0) >= 3:
                P.append(f"V10 {gid}: Phase 3 / oem-kind category {cat!r}")
            elif ckind in ("combo", "exact"):
                P.append(f"V10 {gid}: OEM group for {ckind} category {cat!r}")
            elif kind_key in ("groups", "likely") and ckind != "body":
                P.append(f"V1 {gid}: {kind_key} needs a body category, {cat!r} is {ckind!r}")
            elif kind_key == "vg":
                if ckind != "engine":
                    P.append(f"V1 {gid}: vg needs an engine category, {cat!r} is {ckind!r}")
                fam = fams.get(g.get("family"))
                if fam is None:
                    P.append(f"V1 {gid}: unknown family {g.get('family')!r}")
                elif cat not in fam.get("parts", {}) and cat != "ignition-coils":
                    P.append(f"V1 {gid}: family {g.get('family')} has no part {cat!r}")
            apps = g.get("spans") if kind_key == "vg" else g.get("apps")
            if not apps:
                P.append(f"V2 {gid}: no apps")
                apps = []
            for app in apps:
                why = _app_ok(app, makes, year_cap, targets, ns)
                if why:
                    P.append(f"V2 {gid}: {why}")
            if apps != sorted(apps):
                P.append(f"V8 {gid}: apps not sorted")
            pns = g.get("pn") or []
            if not pns or pns != sorted(pns):
                P.append(f"V8 {gid}: pn missing or unsorted")
            why = _note_ok(g.get("note"), tier if tier in ("verified", "likely") else "verified", pns)
            if why:
                P.append(f"V5 {gid}: {why}")
            # V6 universal cap, per class across groups
            gkeys = set()
            if kind_key != "likely":
                sig = g.get("sig") or []
                if not sig:
                    P.append(f"V4 {gid}: no signature")
                if g.get("id", "").rsplit(":", 1)[-1] != _sig_id(sig):
                    P.append(f"V8 {gid}: id does not recompute from sig")
                slots_of = {}
                for slot, packs in sig:
                    for _pack, keys in packs:
                        if keys != sorted(keys):
                            P.append(f"V8 {gid}: keys unsorted")
                        for k in keys:
                            if not k.startswith(ns + ":"):
                                P.append(f"V6 {gid}: key {k} outside namespace")
                            if k in slots_of and slots_of[k] != slot:
                                P.append(f"V6 {gid}: class {k} in two slots")
                            slots_of[k] = slot
                            gkeys.add(k)
                            if k not in classes:
                                P.append(f"V6 {gid}: class {k} not in classes")
            for k in gkeys:
                feed_models_by_class.setdefault(k, set()).update((a[0], a[1]) for a in apps if len(a) == 4)
            if kind_key == "likely":
                feed = {(a[0], a[1]) for a in apps if len(a) == 4}
                if len(feed) > policy.UNIVERSAL_CAP:
                    P.append(f"V6 {gid}: {len(feed)} feed models (cap {policy.UNIVERSAL_CAP})")
                continue
            # V4 proof
            years = g.get("years") or []
            vy = [tuple(y.get("t") or ()) for y in years]
            app_years = {(a[0], a[1], y) for a in apps if len(a) == 4 for y in range(a[2], a[3] + 1)}
            if len(app_years) < policy.MIN_GROUP_VEHICLE_YEARS:
                P.append(f"V4 {gid}: fewer than {policy.MIN_GROUP_VEHICLE_YEARS} vehicle-years")
            if set(vy) != app_years:
                P.append(f"V4 {gid}: proof years do not equal app years")
            for y in years:
                cl = y.get("closure") or {}
                if not cl.get("year") or not cl.get("lists"):
                    P.append(f"V4 {gid}: {y.get('t')} missing closure pointers")
                if (y.get("universe") or {}).get("trims_src") in (None, "unattested"):
                    P.append(f"V4 {gid}: {y.get('t')} universe not attested")
                t = _ts(cl.get("oldest_retrieved"))
                if t is None or (as_of and as_of - t > timedelta(days=policy.EVIDENCE_MAX_AGE_DAYS)):
                    P.append(f"V4 {gid}: {y.get('t')} evidence stale or undated")
            # V3 partition
            part_key = (cat,) if kind_key == "groups" else (g.get("family"), cat)
            for T in app_years:
                kk = part_key + T
                if kk in seen_verified and seen_verified[kk] != gid:
                    P.append(f"V3 {gid}: {T} also in {seen_verified[kk]}")
                seen_verified[kk] = gid
            # V7 gates: every contributing (site, cat) confirmed, audit matches
            sites = set()
            for k in gkeys:
                for ev in (classes.get(k) or {}).get("evidence") or []:
                    sites.add(ev.split(":", 1)[0])
            for y in years:
                for ptr in (y.get("closure") or {}).get("lists") or []:
                    sites.add(ptr.split(":", 1)[0])
            if not sites:
                P.append(f"V7 {gid}: no contributing site")
            for s in sorted(sites):
                rec = policy.category_status(s, cat, ctx.get("status_table"))
                if rec is None:
                    P.append(f"V7 {gid}: ({s}, {cat}) not confirmed")
                elif rec.get("policy_sha256") != doc.get("policy_sha256") or \
                        rec.get("raw_commit") != (doc.get("raw") or {}).get("commit"):
                    P.append(f"V7 {gid}: audit record for ({s}, {cat}) does not match policy/raw")
    for k, ms in feed_models_by_class.items():
        if len(ms) > policy.UNIVERSAL_CAP:
            P.append(f"V6 class {k}: {len(ms)} feed models")
    return P


# --------------------------------------------------------------- payload
OLD_KEYS = ("categories", "platformGroups", "engineFamilies")


def old_keys_problems(before: dict, after: dict) -> list:
    """V9: with and without groups/, the old keys may differ only by
    demotions (platform tier verified -> likely, removed vg groups, an added
    ambig string, a note extended by the OEM caveat)."""
    P = []
    if _canon(before.get("categories")) != _canon(after.get("categories")):
        P.append("V9 categories changed")
    bg = {g["id"]: g for g in before.get("platformGroups") or []}
    ag = {g["id"]: g for g in after.get("platformGroups") or []}
    if set(bg) != set(ag):
        P.append(f"V9 platformGroups ids changed: +{sorted(set(ag) - set(bg))[:3]} -{sorted(set(bg) - set(ag))[:3]}")
    for gid, a in ag.items():
        b = bg.get(gid)
        if b is None:
            continue
        for k in set(a) | set(b):
            if k in ("tier", "note"):
                continue
            if _canon(a.get(k)) != _canon(b.get(k)):
                P.append(f"V9 platformGroups {gid}: {k} changed")
        if a.get("tier") != b.get("tier") and not (b.get("tier") == "verified" and a.get("tier") == "likely"):
            P.append(f"V9 platformGroups {gid}: tier {b.get('tier')} -> {a.get('tier')}")
        if a.get("note") != b.get("note") and not (a.get("note") or "").startswith(b.get("note") or ""):
            P.append(f"V9 platformGroups {gid}: note rewritten")
    bf = {f["id"]: f for f in before.get("engineFamilies") or []}
    af = {f["id"]: f for f in after.get("engineFamilies") or []}
    if set(bf) != set(af):
        P.append("V9 engineFamilies ids changed")
    for fid, a in af.items():
        b = bf.get(fid)
        if b is None:
            continue
        for k in set(a) | set(b):
            if k == "parts":
                continue
            if k == "apps":
                for x, y in zip(b.get("apps") or [], a.get("apps") or []):
                    if x[:5] != y[:5] or (x[5] and x[5] != y[5]):
                        P.append(f"V9 engineFamilies {fid}: app changed beyond an added ambig")
                if len(b.get("apps") or []) != len(a.get("apps") or []):
                    P.append(f"V9 engineFamilies {fid}: apps added/removed")
                continue
            if _canon(a.get(k)) != _canon(b.get(k)):
                P.append(f"V9 engineFamilies {fid}: {k} changed")
        for cat in set(a.get("parts") or {}) | set(b.get("parts") or {}):
            pa, pb = (a.get("parts") or {}).get(cat), (b.get("parts") or {}).get(cat)
            if pa is None or pb is None:
                P.append(f"V9 engineFamilies {fid}: part {cat} added/removed")
                continue
            for k in set(pa) | set(pb):
                if k == "vg":
                    va = [_canon(x) for x in pa.get("vg") or []]
                    vb = [_canon(x) for x in pb.get("vg") or []]
                    if any(x not in vb for x in va):
                        P.append(f"V9 engineFamilies {fid}/{cat}: vg group added or changed")
                elif _canon(pa.get(k)) != _canon(pb.get(k)):
                    P.append(f"V9 engineFamilies {fid}/{cat}: {k} changed")
    return P


def size_trim(payload: dict, budget: int | None = None) -> list:
    """V11: keep interchange.json within budget. Likely groups go first,
    lowest value (cars x (cars - 1)) first, then Verified groups. Returns the
    dropped ids (the payload is edited in place)."""
    budget = policy.PAYLOAD_BYTE_BUDGET if budget is None else budget
    dropped = []

    def size():
        return len(json.dumps(payload, separators=(",", ":")))
    if size() <= budget:
        return dropped
    groups = payload.get("oemGroups") or []
    for tier in ("likely", "verified"):
        order = sorted([g for g in groups if g.get("tier") == tier],
                       key=lambda g: ((g.get("cars") or 0) * max((g.get("cars") or 0) - 1, 0), g["id"]))
        for g in order:
            if size() <= budget:
                return dropped
            groups.remove(g)
            dropped.append(g["id"])
    if size() > budget:
        for fam, cats in list((payload.get("oemVg") or {}).items()):
            payload["oemVg"].pop(fam)
            dropped.append(f"oemVg:{fam}")
            if size() <= budget:
                break
    return dropped


def full(doc: dict, recompute, committed: dict | None = None, accept_churn: str | None = None,
         report: dict | None = None, oracle_pairs=None) -> list:
    """V12 reproducible (recompute() returns the doc from the pinned raw),
    V13 oracle soundness (shipped pairs subset of oracle_pairs), V14 churn,
    V15 reports present."""
    P = []
    again = recompute()
    if _canon(again) != _canon(doc):
        P.append("V12 recomputing from the pinned raw gives a different file")
    shipped = set()
    for g in doc.get("groups") or []:
        ys = [tuple(y["t"]) for y in g.get("years") or []]
        shipped |= {(g["cat"], a, b) for a in ys for b in ys if a != b}
    if oracle_pairs is not None and not shipped <= set(oracle_pairs):
        P.append(f"V13 {len(shipped - set(oracle_pairs))} shipped pairs the oracle rejects")
    if committed is not None:
        old = set()
        for g in committed.get("groups") or []:
            ys = [tuple(y["t"]) for y in g.get("years") or []]
            old |= {(g["cat"], a, b) for a in ys for b in ys if a != b}
        new_groups = {g["id"] for g in doc.get("groups") or []} - {g["id"] for g in committed.get("groups") or []}
        grow = (len(shipped) - len(old)) / max(len(old), 1)
        if (grow > policy.CHURN_MAX_PAIR_GROWTH or len(new_groups) > policy.CHURN_MAX_NEW_GROUPS) and not accept_churn:
            P.append(f"V14 churn: pairs {len(old)} -> {len(shipped)}, {len(new_groups)} new groups; "
                     "needs --accept-churn <audit-file>")
    if report is not None:
        for k in ("refusals", "contradictions", "funnel_cars"):
            if k not in report:
                P.append(f"V15 report lacks {k}")
    return P
