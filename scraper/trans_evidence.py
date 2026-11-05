"""Transmission evidence: which sources say what about one car's gearbox.

Loads scraper/manual_detect/trans_rules.json (compiled from the verified
manual-detection worklists by scraper/manual_detect/compile_trans_rules.py)
and answers, per car:

  infer(...)   -> the rule claims about the car (VIN code, manual-only
                  trim, EPA sole offering), without looking at vPIC's
                  TransmissionStyle or the yard listing
  resolve(...) -> (trans text, transSrc) for the extras shard, after
                  precedence and conflict handling

Precedence (highest first): the vPIC decode's own transmission > the yard
listing > a VIN-code rule > a manual-only trim > the EPA sole offering.
Conflict: if any two sources that have an opinion disagree (manual vs not
manual), nothing is recorded (trans "" and transSrc ""). Only MANUAL rule
claims are ever published; automatic rule claims (and conflict_only rules)
only withhold a disagreeing value. A car is never called manual because
manuals were common: every published rule claim rests on evidence that the
gearbox is certain for that VIN / trim / engine (CLAUDE.md rules 3 and 8).

transSrc vocabulary (docs/app.js names each in plain words):
  "vin"      vPIC decode of this VIN
  "listing"  the yard's own listing
  "vin_code" the maker's VIN coding (Part 565 filing) marks this car manual
  "trim"     manual was the only transmission offered for this trim
  "engine"   manual was the only transmission offered with this engine
  "model"    manual was the only transmission offered for this model-year
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent / "manual_detect" / "trans_rules.json"

MANUAL, NOT_MANUAL = "manual", "not_manual"
CANADA = {"AB", "BC", "MB", "NB", "NL", "NS", "ON", "PE", "QC", "SK", "YT", "NT", "NU"}
INFERRED_SRCS = ("vin_code", "trim", "engine", "model")

_TRANSLIT = {**{str(i): i for i in range(10)},
             "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
             "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
             "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"   # 1980..2009, then repeats


def check_digit_ok(vin: str) -> bool:
    """49 CFR 565.15(c) check digit. A VIN that fails it may be mistyped,
    so no rule claim is made from it."""
    if len(vin) != 17 or any(ch not in _TRANSLIT for ch in vin):
        return False
    r = sum(_TRANSLIT[ch] * w for ch, w in zip(vin, _WEIGHTS)) % 11
    return vin[8] == ("X" if r == 10 else str(r))


def vin_year(vin: str, hint: int | None) -> int | None:
    """Model year from VIN character 10; the hint (listing or decode year)
    only picks the 30-year cycle and must be within 2 years."""
    i = _YEAR_CODES.find(vin[9]) if len(vin) == 17 else -1
    if i < 0:
        return None
    cands = [1980 + i] + ([2010 + i] if i < 21 else [])
    if not hint:
        return cands[0] if len(cands) == 1 else None
    best = min(cands, key=lambda y: abs(y - hint))
    return best if abs(best - hint) <= 2 else None


def trans_class(text: str) -> str | None:
    """manual / not_manual / None (blank or speeds only). Same manual test as
    the app's isConfirmedManual (/manual/i and not /automated/i)."""
    s = (text or "").strip()
    if not s:
        return None
    if re.search(r"manual", s, re.I) and not re.search(r"automated", s, re.I):
        return MANUAL
    if re.search(r"automatic|automated|continuously variable|\bcvt\b|dual.clutch|\bdct\b|\bamt\b|\bauto\b",
                 s, re.I):
        return NOT_MANUAL
    return None


def _int(y) -> int | None:
    try:
        return int(str(y)[:4])
    except (TypeError, ValueError):
        return None


_ENG = re.compile(r"^(?:(\d+(?:\.\d+)?)L)?\s*(?:(\d+)-cyl)?")


def _drive_key(d: str) -> str:
    d = (d or "").lower()
    if not d or "," in d or d.startswith("2wd/4wd"):
        return ""
    for k in ("fwd", "rwd", "awd", "4wd", "4x2"):
        if d.startswith(k):
            return k
    return ""


class Rules:
    def __init__(self, doc: dict):
        self.doc = doc
        self.by_wmi: dict[str, list[dict]] = {}
        for c in doc.get("vin_rules", []):
            c = dict(c)
            c["_re"] = re.compile(c["re"])
            c["_and"] = re.compile(c["and_re"]) if c.get("and_re") else None
            c["_not"] = re.compile(c["not_re"]) if c.get("not_re") else None
            c["_years"] = set(c["years"])
            for w in c["wmi"]:
                self.by_wmi.setdefault(w, []).append(c)
        self.documented = set(doc.get("honda_documented", []))
        self.trims = []
        for t in doc.get("trim_rules", []):
            t = dict(t)
            t["_idents"] = [self._compile_ident(i) for i in t["idents"]]
            self.trims.append(t)
        self._trim_by_year: dict[int, list] = {}
        self._trim_other: list = []
        for ti, t in enumerate(self.trims):
            for idn in t["_idents"]:
                if idn["type"] in ("feed_model", "vin_regex"):
                    self._trim_other.append((ti, idn))
                else:
                    for y in range(idn["years"][0], idn["years"][1] + 1):
                        self._trim_by_year.setdefault(y, []).append((ti, idn))
        self.epa = []
        for e in doc.get("epa_rules", []):
            e = dict(e)
            e["_ids"] = {tuple(x) for x in e["identities"]}
            e["_years"] = set(e["years"])
            self.epa.append(e)

    # --- the three rule tracks ---------------------------------------------
    def vin_claims(self, vin: str, listing_year, dec: dict | None, state: str) -> list[dict]:
        if len(vin) != 17 or not check_digit_ok(vin):
            return []
        cands = self.by_wmi.get(vin[:3])
        if not cands:
            return []
        ly, dy = _int(listing_year), _int((dec or {}).get("modelYear"))
        yr = {"decode": vin_year(vin, dy or ly), "listing": vin_year(vin, ly or dy)}
        out = []
        for c in cands:
            if c["us_only"] and state in CANADA:
                continue
            y = yr[c["hint"]]
            if y is None or y not in c["_years"]:
                continue
            if not c["_re"].match(vin) or (c["_and"] and not c["_and"].match(vin)):
                continue
            if c["_not"] and c["_not"].match(vin):
                continue
            if c["need_documented"] and not ((dec or {}).get("model") or f"{y}:{vin[3:7]}" in self.documented):
                continue
            out.append({"src": "vin_code", "claim": c["claim"], "rule": c["id"],
                        "conflict_only": c["conflict_only"], "label": c["label"]})
        return out

    def trim_claims(self, vin: str, listing_year, make: str, model: str,
                    dec: dict | None, state: str) -> list[dict]:
        ly = _int(listing_year)
        dy = _int((dec or {}).get("modelYear"))
        # the yard's year and the VIN's must not be far apart (a 1997 listing
        # on a VIN that decodes 1992 is not certain for that car)
        if ly and dy and abs(ly - dy) > 1:
            return []
        hit: set[int] = set()
        # only identifiers that can match this car's years (vPIC ones by the
        # decoded year; feed-model and VIN-pattern ones are few and always tried)
        for ti, idn in self._trim_by_year.get(dy, []) + self._trim_other:
            if ti in hit:
                continue
            if self.trims[ti]["us_only"] and state in CANADA:
                continue
            if self._ident(idn, vin, ly, dy, make, model, dec):
                hit.add(ti)
        return [{"src": "trim", "claim": self.trims[ti]["claim"], "rule": self.trims[ti]["id"],
                 "conflict_only": False, "label": self.trims[ti]["label"]} for ti in sorted(hit)]

    @staticmethod
    def _compile_ident(idn: dict) -> dict:
        c = dict(idn)
        for k in ("make", "model", "trim", "engine", "drive"):     # full-match, any case
            if idn.get(k):
                c["_" + k] = re.compile(idn[k], re.I)
        for k in ("regex", "vin"):                                   # VIN prefix match
            if idn.get(k):
                c["_" + k] = re.compile(idn[k])
        return c

    @staticmethod
    def _ident(idn: dict, vin: str, ly, dy, make: str, model: str, dec: dict | None) -> bool:
        def fm(k, s):
            return idn["_" + k].fullmatch((s or "").strip()) is not None
        y0, y1 = idn["years"]
        t = idn["type"]
        if t == "feed_model":
            return ly is not None and y0 <= ly <= y1 and fm("make", make) and fm("model", model)
        if t == "vin_regex":
            if not vin or not idn["_regex"].match(vin) or not check_digit_ok(vin):
                return False
            y = vin_year(vin, ly)
            return y is not None and y0 <= y <= y1
        if not dec or dy is None or not (y0 <= dy <= y1):
            return False
        mc = idn.setdefault("_make_ok", {})          # few distinct makes: memoize
        mk = dec.get("make") or ""
        if mk not in mc:
            mc[mk] = fm("make", mk)
        if not mc[mk] or not fm("model", dec.get("model")):
            return False
        if t == "vpic_model":
            return True
        if t == "vpic_engine":
            return fm("engine", dec.get("engine"))
        if not fm("trim", dec.get("trim" if t == "vpic_trim" else "series")):
            return False
        if idn.get("engine") and not fm("engine", dec.get("engine")):
            return False
        if idn.get("drive") and not fm("drive", dec.get("driveType")):
            return False
        if idn.get("vin") and not idn["_vin"].match(vin or ""):
            return False
        return True

    def epa_claims(self, vin: str, listing_year, make: str, model: str, dec: dict | None) -> list[dict]:
        if not dec or len(vin) != 17 or not check_digit_ok(vin):
            return []
        ly, dy = _int(listing_year), _int(dec.get("modelYear"))
        if not dy or ly != dy:
            return []
        ident = (make or "", model or "", (dec.get("make") or "").upper(), dec.get("model") or "")
        m = _ENG.match((dec.get("engine") or "").strip())
        d = float(m.group(1)) if m and m.group(1) else None
        cyl = int(m.group(2)) if m and m.group(2) else None
        dk = _drive_key(dec.get("driveType"))
        out = []
        for e in self.epa:
            if dy not in e["_years"] or ident not in e["_ids"]:
                continue
            if e["level"] == "engine":
                if d is None or e["displ"] is None or abs(d - float(e["displ"])) >= 0.051:
                    continue
                if e["cyl"] is not None and cyl is not None and cyl != e["cyl"]:
                    continue
            if e["drive"] in ("4wd", "awd") and dk not in ("4wd", "awd"):
                continue
            if e["drive"] in ("2wd", "4x2", "fwd", "rwd") and dk not in ("fwd", "rwd", "4x2"):
                continue
            out.append({"src": "model" if e["level"] == "model_year" else "engine", "claim": e["claim"],
                        "rule": e["id"], "conflict_only": False, "label": e["label"]})
        return out

    def infer(self, *, vin: str, listing_year, make: str, model: str, dec: dict | None,
              state: str = "") -> list[dict]:
        """Every rule claim about one car (VIN code, trim, EPA), in precedence order."""
        vin = (vin or "").strip().upper()
        state = (state or "").strip().upper()
        return (self.vin_claims(vin, listing_year, dec, state)
                + self.trim_claims(vin, listing_year, make, model, dec, state)
                + self.epa_claims(vin, listing_year, make, model, dec))


@lru_cache(maxsize=1)
def load_rules(path: str | None = None) -> Rules:
    p = Path(path) if path else RULES_FILE
    try:
        doc = json.loads(p.read_text())
    except (OSError, ValueError):
        doc = {}
    return Rules(doc)


def _claim_class(claim: str) -> str:
    return MANUAL if claim == "manual" else NOT_MANUAL


def resolve(vpic_trans: str, listing_trans: str, claims: list[dict]) -> tuple[str, str, dict]:
    """-> (trans, transSrc, info). info["conflict"] names the disagreeing
    sources when nothing was recorded because of a disagreement."""
    vpic_trans = (vpic_trans or "").strip()
    listing_trans = (listing_trans or "").strip()
    opinions: list[tuple[str, str]] = []           # (source, class), precedence order
    vc, lc = trans_class(vpic_trans), trans_class(listing_trans)
    if vc:
        opinions.append(("vin", vc))
    if lc:
        opinions.append(("listing", lc))
    for c in claims:
        opinions.append((c["src"], _claim_class(c["claim"])))
    classes = {cl for _s, cl in opinions}
    if len(classes) > 1:
        return "", "", {"conflict": sorted({f"{s}:{cl}" for s, cl in opinions}),
                        "rules": sorted({c["rule"] for c in claims})}
    if vc:
        return vpic_trans, "vin", {}
    if lc:
        return listing_trans, "listing", {}
    for c in claims:                                # first publishable claim, precedence order
        if c["claim"] == "manual" and not c["conflict_only"]:
            return "Manual", c["src"], {"rule": c["rule"]}
    # nobody has a class: keep the old text (speeds-only vPIC, listing) as before
    if vpic_trans:
        return vpic_trans, "vin", {}
    if listing_trans:
        return listing_trans, "listing", {}
    return "", "", {}
