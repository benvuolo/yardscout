"""Shared helpers for the aftermarket application-table track.

All network access goes through ../fetch.py (allowlist, robots, spacing,
cache, circuit breaker). This module adds one extra guard on top of it:
`robots_allows()` re-reads the cached robots.txt with RFC 9309 semantics
(every `User-agent: *` group merged, `*` and `$` wildcards, longest match
wins). Python's urllib.robotparser, which fetch.py uses, keeps only the
FIRST `*` group and ignores wildcards, so on dbelectrical.com it would allow
/search.php (the first `*` group there is "Allow: /"). We never build such
URLs, and this guard makes sure of it.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fetch  # noqa: E402
from fetch import Refused  # noqa: E402,F401

# ---------------------------------------------------------------- robots ---


@lru_cache(maxsize=None)
def _rules(netloc: str) -> list[tuple[str, bool]]:
    """(pattern, allow) for every rule in every group naming `*` or our UA token."""
    cp = fetch.CACHE / netloc / "robots.txt"
    if not cp.exists():
        # fetch.get of any page on the site caches robots.txt first
        fetch.get(f"https://{netloc}/")
    body = cp.read_text(errors="ignore")
    ours = "yardscout-research"
    rules: list[tuple[str, bool]] = []
    agents: list[str] = []
    in_rules = False
    for line in body.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = (s.strip() for s in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(v.lower())
        elif k in ("allow", "disallow"):
            in_rules = True
            if v and any(a in ("*", ours) for a in agents):
                rules.append((v, k == "allow"))
        else:
            in_rules = in_rules or bool(agents)
    return rules


def _match_len(pattern: str, path: str) -> int:
    rx = "^" + re.escape(pattern).replace(r"\*", ".*")
    if rx.endswith(r"\$"):
        rx = rx[:-2] + "$"
    return len(pattern) if re.match(rx, path) else -1


def robots_allows(url: str) -> bool:
    u = urllib.parse.urlsplit(url)
    path = u.path + ("?" + u.query if u.query else "")
    best, allow = -1, True
    for pat, is_allow in _rules(u.netloc):
        n = _match_len(pat, path)
        if n > best or (n == best and is_allow):
            best, allow = n, is_allow
    return allow


def get(url: str) -> dict:
    """fetch.get behind the RFC 9309 guard."""
    if not robots_allows(url):
        raise Refused(f"robots.txt (RFC 9309 reading) disallows {url}")
    return fetch.get(url)


# ------------------------------------------------- part-number brand roles ---

# Brands in "replaces" tables whose numbers are the carmaker's own part numbers.
CARMAKER_BRANDS = {
    "ACURA", "ALFA ROMEO", "AMC", "AUDI", "BMW", "BUICK", "CADILLAC", "CHEVROLET",
    "CHRYSLER", "DAEWOO", "DAIHATSU", "DODGE", "EAGLE", "FIAT", "FORD", "GEO",
    "GM", "GENERAL MOTORS", "GMC", "HONDA", "HUMMER", "HYUNDAI", "INFINITI",
    "INTERNATIONAL", "ISUZU", "JAGUAR", "JEEP", "KIA", "LAND ROVER", "LEXUS",
    "LINCOLN", "MAZDA", "MERCEDES", "MERCEDES BENZ", "MERCEDES-BENZ", "MERCURY",
    "MINI", "MOPAR", "NISSAN", "OLDSMOBILE", "OPEL", "PEUGEOT", "PLYMOUTH",
    "PONTIAC", "PORSCHE", "RAM", "RENAULT", "SAAB", "SATURN", "SCION", "SMART",
    "SUBARU", "SUZUKI", "TOYOTA", "VOLKSWAGEN", "VW", "VOLVO",
}
# Carmaker service brands: numbers are the carmaker's service-part numbers,
# not its engineering part numbers. Kept apart; never merged into oe_numbers.
SERVICE_BRANDS = {"MOTORCRAFT", "ACDELCO", "AC DELCO", "AC-DELCO"}
# Original-equipment suppliers (their numbers identify the supplier's unit).
OE_SUPPLIER_BRANDS = {
    "DENSO", "NIPPONDENSO", "NIPPON DENSO", "BOSCH", "VALEO", "HITACHI",
    "MITSUBA", "VISTEON", "DELCO", "DELCO REMY", "DELCO-REMY", "MANDO",
    "MAGNETI MARELLI", "MARELLI", "MITSUBISHI ELECTRIC", "KOKUSAN DENKI",
}
# Lester (the industry interchange number), USA Industries (Lester-numbered) and
# DENSO First Time Fit (Denso's reman 210-/280- numbers, which the existing
# Denso-based verified groups cite).
INTERCHANGE_BRANDS = {"LESTER", "USA INDUSTRIES", "DENSO FIRST TIME FIT"}

# "MITSUBISHI" in these tables can be Mitsubishi Electric (the OE alternator /
# starter maker: A3TG0491, M1T70384, A002TG0491) or Mitsubishi Motors (MD..., MN...,
# 1800A...). Split only on these documented number shapes; anything else stays
# ambiguous and out of oe_numbers.
MELCO_RE = re.compile(r"^[AM]0*\d{1,3}T[A-Z]{0,2}\d", re.I)
MMC_RE = re.compile(r"^(?:M[DNRQ]\d{5,}|1[78]\d\dA\d{3,})", re.I)


def classify_replaces(replaces: list[dict]) -> dict:
    """replaces: [{"brand": "FORD", "numbers": [...]}] (verbatim) ->
    oe_numbers, oe_service_numbers, oe_supplier_numbers, interchange_numbers,
    other_numbers, ambiguous_numbers (each a list of {"brand", "pn"})."""
    out = {k: [] for k in ("oe_numbers", "oe_service_numbers", "oe_supplier_numbers",
                           "interchange_numbers", "other_numbers", "ambiguous_numbers")}
    for row in replaces:
        b = row["brand"].strip().upper()
        for pn in row["numbers"]:
            item = {"brand": row["brand"], "pn": pn}
            if b == "MITSUBISHI":
                if MELCO_RE.match(pn):
                    out["oe_supplier_numbers"].append({**item, "role_basis": "Mitsubishi Electric number shape"})
                elif MMC_RE.match(pn):
                    out["oe_numbers"].append({**item, "role_basis": "Mitsubishi Motors number shape"})
                else:
                    out["ambiguous_numbers"].append(item)
            elif b in CARMAKER_BRANDS:
                out["oe_numbers"].append(item)
            elif b in SERVICE_BRANDS:
                out["oe_service_numbers"].append(item)
            elif b in OE_SUPPLIER_BRANDS:
                out["oe_supplier_numbers"].append(item)
            elif b in INTERCHANGE_BRANDS:
                out["interchange_numbers"].append(item)
            else:
                out["other_numbers"].append(item)
    return out


def merge_spans(apps: list[dict]) -> list[dict]:
    """Derived convenience view: contiguous single-year rows with the same
    verbatim (make, type, model, engine) merged into one span. Never used as
    evidence; `applications` (one per printed row) is the evidence."""
    groups: dict[tuple, list[int]] = {}
    for a in apps:
        key = (a["make"], a.get("type", ""), a["model"], a["engine"])
        groups.setdefault(key, []).extend(range(a["years"][0], a["years"][1] + 1))
    out = []
    for (mk, ty, mo, en), ys in groups.items():
        ys = sorted(set(ys))
        lo = prev = ys[0]
        for y in ys[1:] + [None]:
            if y is not None and y == prev + 1:
                prev = y
                continue
            out.append({"years": [lo, prev], "make": mk, "type": ty, "model": mo, "engine": en})
            if y is not None:
                lo = prev = y
    return out


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())
