"""Curation policy for the OEM fitment layer (CURATION_SPEC.md §4, §5).

Every entry carries a basis comment. This module is pure data plus a few
helpers: no network, no imports of crawler code. curate.py, validate.py and
the tests read it; its sha256 (with notes.py, positions.py and
model_map.json) is pinned into every generated groups/<ns>.json
(`policy_sha256`), so any edit here invalidates committed groups until they
are re-curated.

Changing a value here can only be done by reviewed commit. Values that would
let a claim through (an audits.json record, ENGINE_CELLS_RELIABLE True, a
SIBLING_IGNORE entry) need the audit record named in their basis.
"""
from __future__ import annotations

import re
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent

CURATE_VERSION = "1.0"
SCHEMA = 1

# --------------------------------------------------------------- thresholds
# §0 conflict #8: evidence older than this (days before --as-of) is stale;
# re-applied at payload-build time against "now".
EVIDENCE_MAX_AGE_DAYS = 120
# §0 conflict #9: a class listing more feed models than this is a suspected
# catalog aggregate, never a one-part fit (E6, V6).
UNIVERSAL_CAP = 12
# §0 conflict #11: more than this share of evidence re-check failures in a
# (site, cat) makes the whole (site, cat) unconfirmed (systemic).
SYSTEMIC_FAIL_RATE = 0.02
# §0 conflict #7 / §5.7: a fitment-derived trim universe is attested only with
# at least this many distinct verified records from at least this many
# categories covering the catalog vehicle-year.
TRIMU_MIN_RECORDS = 5
TRIMU_MIN_CATS = 3
# §5.10 C5 / R4: supersession depth followed for chain completeness.
CHAIN_DEPTH = 4
# §5.15: a Verified group spans at least this many feed vehicle-years.
MIN_GROUP_VEHICLE_YEARS = 2
# §5.16 own-page rule (2026-11-06, hub accuracy audit): a vehicle-year joins
# a Likely body group only when its OWN catalog page lists the number
# (Curation.own_page: a matched R1 manifest row, or for a site without
# manifests a record seeded on that page). A product page's fitment table
# alone is not enough: dealer catalogs print platform rollups there
# (fordpartsgiant AH6Z-8200-ACP, an MKZ grille, lists Fusion/MKZ/Milan
# 2010-12 with the identical whole-platform engine and transmission union,
# incl. the 2.5L and manual the MKZ never had). Measured on oem-raw@42683f9:
# where the app's own list page was crawled it did not list the number for
# 3-19% of exterior app-years per namespace (mopar 136/733, ford 91/811,
# hmg 8/71, gm 42/563, subaru 54/856, toyota 34/1193), and 80-95% of
# app-years had no own-page evidence at all. Engine categories never form
# Likely groups (body only), so they keep their own rules.
LIKELY_REQUIRES_OWN_PAGE = True
# §5.16 exterior hold (owner decision 2026-11-06, ops/hub.md): in exterior
# styling categories a Likely group whose apps span more than one BASE model
# is held (refusal held_exterior_cross_model, listed in
# groups/_report/held_exterior.json for an owner checklist). Badge twins and
# sister models usually differ in front/rear styling (Fusion/MKZ/Milan,
# Legacy/Outback, DeVille/Seville), and a list page can print a platform
# diagram. Base model = make + first word of the model after a leading
# "Grand"/"Super" (Camry/Camry Hybrid and RX 350/RX 450h stay together).
# Only removes claims.
EXTERIOR_HOLD_CATS = frozenset({"bumper-front", "bumper-rear", "grille", "headlights", "tail-lights", "fender",
                                "hood", "door-front", "door-rear", "liftgate", "tailgate", "trunk-lid"})


# Per-namespace option holds (hub decision 2026-11-09, make breadth §11.4
# Subaru resample): categories where an option we cannot see per row (heated
# vs non-heated mirror; US vs non-US configurations the catalog does not
# mark) splits the part. A cross-model Likely group in one of these is held
# like an exterior group (held_option_cross_model), listed in
# held_exterior.json for the owner checklist. Only removes claims.
OPTION_HOLD_CATS: dict = {"subaru": frozenset({"side-mirrors"})}


def held_cross_model_cat(ns: str, cat: str) -> str | None:
    """Refusal code when a cross-model Likely group in (ns, cat) is held."""
    if cat in EXTERIOR_HOLD_CATS:
        return "held_exterior_cross_model"
    if cat in OPTION_HOLD_CATS.get(ns, ()):
        return "held_option_cross_model"
    return None


# Namespaces withheld from shipping (2026-11-09, ops/interchange.md): their
# held groups are never released by the allowlist.
WITHHELD_NS = frozenset({"subaru"})
# §5.16 release allowlist: exact (ns, cat, pn, apps) entries let a held group
# through the exterior hold; OEM_RELEASE_ALLOWLIST (tests only) points at
# another file with the same layout.
RELEASE_ALLOWLIST_PATH = _Path(__import__("os").environ.get("OEM_RELEASE_ALLOWLIST")
                               or (_HERE / "release_allowlist.json"))


def release_allowlist(path=None) -> set:
    """{(ns, cat, (pn, ...), ((make, model, lo, hi), ...))} of released held groups."""
    import json
    p = _Path(path) if path else RELEASE_ALLOWLIST_PATH
    if not p.exists():
        return set()
    out = set()
    for g in json.loads(p.read_text()).get("groups") or []:
        if g.get("ns") in WITHHELD_NS:
            continue
        out.add((g["ns"], g["cat"], tuple(sorted(g["pn"])), tuple(tuple(a) for a in g["apps"])))
    return out


def base_model(make: str, model: str) -> tuple:
    words = (model or "").split()
    if len(words) > 1 and words[0].lower() in ("grand", "super"):
        words = words[1:]
    return ((make or "").lower(), words[0].lower() if words else "")
# §8 V11: interchange.json budget (raw bytes).
PAYLOAD_BYTE_BUDGET = 1_300_000
# §8 V14: churn gate against the committed file.
CHURN_MAX_PAIR_GROWTH = 0.30
CHURN_MAX_NEW_GROUPS = 200
# §8 V5: OEM note length cap and charset (no <, >, &, ").
NOTE_MAX_LEN = 160
NOTE_CHARSET = re.compile(r"^[A-Za-z0-9 #.,;:()/'+–—-]*$")
NOTE_BANNED = re.compile(r"fits all|guaranteed|always|100%", re.I)

# --------------------------------------------------------------- namespaces
# §4: by numbering system, not make. Each site belongs to exactly one
# namespace. A crawled site not listed here is reported as
# `site_without_namespace` and makes no claim. The aftermarket track
# (dbelectrical) is never a namespace (§12).
# 2026-11-05 (interchange session): vag, bmw, mb, mazda, mitsubishi, volvo
# added under the same rules as the others: no audits.json record, no R1/R2
# manifests on oem-raw for them yet and ENGINE_CELLS_RELIABLE unset, so every
# group they yield is Likely until those exist (§5.12, §8 V7).
# - vag: Volkswagen and Audi share one numbering system (alternator
#   06B-903-016-AB is listed on both catalogs on oem-raw), so one namespace
#   with both sites, as toyota/lexus and honda/acura.
# - bmw: BMW only. MINI shares BMW numbering, but bmwpartsdeal is not a MINI
#   catalog (sites/bmwpartsdeal.py, SOURCES.md) and its 1,746 records print
#   no MINI fitment row, so MINI is not a namespace make (no source).
# - mb: the feed's make string is "Mercedes-Benz"; the note brand is "Mercedes"
#   (validate.NOTE_LIKELY_RE allows letters, "/" and spaces only).
NAMESPACES: dict[str, dict] = {
    "toyota": {"makes": ["Toyota", "Scion", "Lexus"], "brand": "Toyota",
               "sites": ["www.toyotapartsnow.com", "www.lexuspartsnow.com"]},
    "mopar": {"makes": ["Jeep", "Dodge", "Chrysler", "Ram", "Plymouth", "Eagle", "Fiat"],
              "brand": "Mopar", "sites": ["www.jeeppartsdeal.com", "www.moparpartsgiant.com"]},
    "gm": {"makes": ["Chevrolet", "GMC", "Buick", "Cadillac", "Pontiac", "Oldsmobile",
                     "Saturn", "Hummer", "Geo"],
           "brand": "GM", "sites": ["www.gmpartsgiant.com"]},
    "ford": {"makes": ["Ford", "Lincoln", "Mercury"], "brand": "Ford",
             "sites": ["www.fordpartsgiant.com"]},
    "nissan": {"makes": ["Nissan", "Infiniti"], "brand": "Nissan",
               "sites": ["www.nissanpartsdeal.com", "www.infinitipartsdeal.com"]},
    "honda": {"makes": ["Honda", "Acura"], "brand": "Honda",
              "sites": ["www.hondapartsnow.com", "www.acurapartswarehouse.com"]},
    "hmg": {"makes": ["Hyundai", "Kia", "Genesis"], "brand": "Hyundai/Kia",
            "sites": ["www.hyundaipartsdeal.com", "www.kiapartsnow.com"]},
    "subaru": {"makes": ["Subaru"], "brand": "Subaru", "sites": ["www.subarupartsdeal.com"]},
    "vag": {"makes": ["Volkswagen", "Audi"], "brand": "VW/Audi",
            "sites": ["www.vwpartsgiant.com", "www.audipartsgiant.com"]},
    "bmw": {"makes": ["BMW"], "brand": "BMW", "sites": ["www.bmwpartsdeal.com"]},
    "mb": {"makes": ["Mercedes-Benz"], "brand": "Mercedes", "sites": ["www.mbpartsgiant.com"]},
    "mazda": {"makes": ["Mazda"], "brand": "Mazda", "sites": ["www.mazdapartsnow.com"]},
    "mitsubishi": {"makes": ["Mitsubishi"], "brand": "Mitsubishi", "sites": ["www.mitsubishipartsgiant.com"]},
    "volvo": {"makes": ["Volvo"], "brand": "Volvo", "sites": ["www.volvopartsgiant.com"]},
}

SITE_NS: dict[str, str] = {s: ns for ns, d in NAMESPACES.items() for s in d["sites"]}
AFTERMARKET_SITES = {"www.dbelectrical.com", "www.densoautoparts.com", "www.tycamericas.com"}

# Template per site. SimplePart records carry list_section/list_notes;
# PartsGiant records carry list_group/list_remark/list_info (§3.1).
SIMPLEPART_SITES = {"www.toyotapartsnow.com", "www.jeeppartsdeal.com", "www.vwpartsgiant.com",
                    "www.mazdapartsnow.com", "www.mbpartsgiant.com",
                    "www.mitsubishipartsgiant.com"}

# §5.2 options column: True where the site's Config sets
# option_column_is_trims=True (copied from sites/<x>.py; test_policy checks
# the module source still says so). Even then a namespace audit must confirm
# before such trims count as coverage (§5.2), so curate.py treats these rows
# as trim layout only when ENGINE_CELLS_RELIABLE is also set for the site.
OPTION_COLUMN_IS_TRIMS = {
    "www.gmpartsgiant.com": True,       # sites/gmpartsgiant.py CFG
    "www.moparpartsgiant.com": True,    # sites/moparpartsgiant.py CFG
    "www.subarupartsdeal.com": True,    # sites/subarupartsdeal.py CFG
}

# §4 / §5.5: engine cells are used for universes and coverage only where set.
# basis: PartsGiant engine/trim cells are per-row aggregates and sometimes
# wrong (ops/interchange.md "PartsGiant: what a curator must know": Infiniti
# 16119-8J103 FX45 printed "6 Cyl 3.5L") -> False until an audit flips it.
# SimplePart trim-layout rows print one engine list per row from the store
# and the AUDIT.md re-check found 0 E on toyotapartsnow (757) and
# jeeppartsdeal (748); option-layout rows are never used for engines (§1).
ENGINE_CELLS_RELIABLE: dict[str, bool] = {
    "www.toyotapartsnow.com": True,
    "www.jeeppartsdeal.com": True,
}

# §5.12: every (site, category) starts unconfirmed; it flips only with an
# audit record {status: "confirmed", date, auditor_session, sample_n,
# errors: 0, policy_sha256, raw_commit} written by a session that did not
# write curate.py (§11). The records live in audits.json, NOT in this file:
# policy_sha256 hashes this file, so an audit table kept here would change
# the very hash its records must match, and no doc curated after a record
# was written could ever pass V7 (review finding, 2026-11-05). audits.json is
# not hashed; each record names the policy_sha256 and raw commit it audited,
# so a policy edit still invalidates every record (V7) until re-audited.
# No audit has run yet (2026-11-05), so the table is empty on purpose.
# OEM_AUDITS_PATH (tests only) points at another file with the same layout,
# so a test can record an audit in a real store without touching this one.
AUDITS_PATH = _Path(__import__("os").environ.get("OEM_AUDITS_PATH") or (_HERE / "audits.json"))


def load_category_status(path=None) -> dict[str, dict[str, dict]]:
    """{site: {cat: audit record}} from audits.json (missing file: {})."""
    import json
    p = _Path(path) if path else AUDITS_PATH
    if not p.exists():
        return {}
    doc = json.loads(p.read_text())
    tbl = doc.get("category_status") or {}
    if not isinstance(tbl, dict):
        raise ValueError(f"{p}: category_status is not an object")
    return tbl


CATEGORY_STATUS: dict[str, dict[str, dict]] = load_category_status()


# §4.1 policy_sha256: the curation policy a groups file was curated under.
# audits.json is deliberately not an input (see CATEGORY_STATUS above).
POLICY_INPUTS = ("policy.py", "notes.py", "positions.py", "model_map.json", "release_allowlist.json")


def tree_sha256(model_map_path=None) -> str:
    """sha256 over policy.py + notes.py + positions.py + model_map.json (the
    model map may be another file, as curate.py --model-map allows)."""
    import hashlib
    h = hashlib.sha256()
    for name in POLICY_INPUTS:
        p = _Path(model_map_path) if (name == "model_map.json" and model_map_path) else _HERE / name
        h.update(p.read_bytes())
    return h.hexdigest()


def category_status(site: str, cat: str, status_table: dict | None = None) -> dict | None:
    """The audit record for (site, cat) if confirmed, else None."""
    tbl = CATEGORY_STATUS if status_table is None else status_table
    rec = (tbl.get(site) or {}).get(cat)
    if rec and rec.get("status") == "confirmed" and rec.get("errors") == 0 \
            and int(rec.get("sample_n") or 0) > 0:
        return rec
    return None


# ---------------------------------------------------------------- categories
# Slots (§5.8) and the slots a vehicle-year must list for a closed category
# (REQUIRED_SLOT_SETS: any one set must be fully present). Requiring both
# sides only removes claims: a page that lists one mirror says nothing about
# the other side.
SIDE_CATS = {"side-mirrors", "tow-mirrors", "headlights", "fender", "door-front", "door-rear",
             "tail-lights"}
CATEGORY_POLICY: dict[str, dict] = {
    **{c: {"slots": ["L", "R"], "axes": ["side"], "required": [["L", "R"]]} for c in SIDE_CATS},
    "window-regulator": {"slots": ["FL", "FR", "RL", "RR", "SL", "SR"], "axes": ["side", "door"],
                         # every door the car has must be present: front pair,
                         # plus the rear or sliding pair when either shows up
                         "required": [["FL", "FR"], ["FL", "FR", "RL", "RR"],
                                      ["FL", "FR", "SL", "SR"]]},
    "window-switch": {"slots": ["DM"], "axes": ["side"], "required": [["DM"]]},
    "climate-control": {"slots": ["C", "CSW"], "axes": [], "required": [["C"], ["CSW"], ["C", "CSW"]]},
}
DEFAULT_CATEGORY_POLICY = {"slots": ["C"], "axes": [], "required": [["C"]]}
# §5.14: colour collapse is off in Phase 1 for every category.
COLOR_COLLAPSE: dict[str, bool] = {}

ENGINE_CATS = {"alternator", "starter", "ignition-coils"}
# §7.6 oem_split: the conditional classes that say the catalog's numbers
# differ by configuration inside a closed cell (a note naming a plant, trim,
# option, engine, emissions, production date, body, package or colour; a
# fitment row listing only some trims or engines; a qualifier phrase in the
# name). Everything else a cell can be conditional on is an evidence gap
# (notes_not_own_page, fitted_not_listed, listed_not_fitted, option_layout,
# trim/engine universes unattested or unparsed, engine cells unaudited, a
# blank trim cell, an UNKNOWN note clause) and never contradicts a hand
# group (review, 2026-11-05: those gaps removed 55 of 468 hand vg groups).
SPLIT_CONDITIONS = frozenset({"plant", "trim", "option", "engine", "emissions", "production", "fuel", "trans",
                              "body", "package", "colour", "model_other", "qualifier"})
# §7.7: Phase 3 categories (kind "oem", clientMin 3). No groups in Phase 1.
PHASE3_CATS = {"ac-compressor", "fuel-pump-module", "throttle-body", "power-steering-pump",
               "radiator"}


def cat_policy(cat: str) -> dict:
    return CATEGORY_POLICY.get(cat, DEFAULT_CATEGORY_POLICY)


# §5.10 C2: a year-page sub whose slug matches NOUN[c] but is not one of the
# site's CAT_PAGES/SUBCATS for c must have been read (unread_sibling_page),
# unless SIBLING_IGNORE exempts it with a basis. Patterns run on the
# "<group>/<sub>" slug (SimplePart) or the <sub> slug (PartsGiant).
NOUN: dict[str, str] = {
    "alternator": r"alternator|generator",
    "starter": r"starter",
    "ac-compressor": r"compressor",
    "headlights": r"head-?_?lamp|headlight",
    "tail-lights": r"tail-?_?lamp|combination-?_?lamp|rear-?_?lamp",
    "side-mirrors": r"mirror",
    "tow-mirrors": r"mirror",
    "window-regulator": r"regulator|door-body|door_body|window",
    "window-switch": r"switch",
    "climate-control": r"control|heater",
    "fuel-pump-module": r"fuel",
    "throttle-body": r"throttle",
    "power-steering-pump": r"steering|p-s-pump",
    "gauge-cluster": r"gauge|meter|cluster|instrument",
    "ignition-coils": r"ignition|coil",
    "radiator": r"radiator",
    "door-front": r"door",
    "door-rear": r"door",
    "hood": r"hood",
    "fender": r"fender",
    "bumper-front": r"bumper|fascia",
    "bumper-rear": r"bumper|fascia",
    "grille": r"grille",
    "trunk-lid": r"trunk|deck-?_?lid",
    "tailgate": r"tail-?_?gate|rear-?_?gate",
    "liftgate": r"lift-?_?gate|back-door",
}
# {site: {cat: {sub_slug: basis}}}. Empty: no page has been exempted yet.
SIBLING_IGNORE: dict[str, dict[str, dict[str, str]]] = {}

# §5.6: objects that describe the assembly's contents, not the car; a
# qualifier phrase naming one of these does not condition the row.
CONTENT_TOKENS: dict[str, list[str]] = {
    "alternator": ["regulator", "pulley"],
    "ac-compressor": ["pulley", "clutch", "magnet"],
    "fuel-pump-module": ["filter", "pump", "gage", "gauge", "sender"],
    "radiator": ["cap"],
    "headlights": ["bulb", "socket"],
    "tail-lights": ["bulb", "socket"],
    "side-mirrors": ["glass"],
}

# §5.6 qualifier phrases in names / aux_desc / other_names (they only remove
# claims). The phrase runs to the next "," or ";" (R5a).
QUALIFIER_RE = re.compile(
    r"(?:^|[\s,;(])(w/o|w/|with(?:out)?|less|exc(?:ept)?|excl(?:uding)?|for\s+(?:models|vehicles)\s+with|"
    r"if\s+equipped)\s*([^,;)]*)", re.I)

# §5.3 guards.
KIT_RE = re.compile(r"\b(kit|set|pair)\b", re.I)
RHD_RE = re.compile(r"\bRHD\b|right[\s-]+hand[\s-]+drive", re.I)
# CLAUDE.md rule 4: a class name matching this is a lint error.
RULE4_RE = re.compile(r"engine\s+assembly|long\s+block|transmission|transaxle|catalytic|converter", re.I)
TOW_RE = re.compile(r"\btow(ing)?\b|\btrailer\b", re.I)

# §5.4 withhold-only reman syntax.
REMAN_NAME_RE = re.compile(r"\breman", re.I)
REMAN_PN_RE = re.compile(r"^R\d")


def is_reman_pn(ns: str, pn: str) -> bool:
    # basis: Toyota -84 remans arrive with reman:false (§1: 28100-20020-84,
    # 27060-20040-84, 28100-74270-84); the catalog's own replace pairs name
    # them (27060-28320 -> 27060-28321-84). Mopar/others: R + digit (R5233006).
    if REMAN_PN_RE.match(pn or ""):
        return True
    if ns == "toyota" and re.search(r"-84$", pn or ""):
        return True
    return False


def pn_key(ns: str, pn: str) -> str:
    """§5.4: ns + ':' + the pn upper-cased with every non-alphanumeric dropped.
    No suffix is ever interpreted (colour, revision and reman suffixes stay)."""
    return ns + ":" + re.sub(r"[^A-Z0-9]", "", (pn or "").upper())


# AUDIT.md "Exclude at curation": records already crawled that a later rule
# fix drops, by (site, category, pn).
EXCLUDE_AT_CURATION: dict[tuple[str, str, str], str] = {
    ("www.moparpartsgiant.com", "headlights", "LBK13001"):
        "light bulb kit ('Light Bulb Kit (Assorted Bulbs and Fuses)'), not a headlamp (AUDIT.md)",
    ("www.jeeppartsdeal.com", "headlights", "5143152AA"):
        "headlamp boot / bulb cap ('Boot, Front'), not a headlamp (AUDIT.md)",
}

# Hub decisions (ops/interchange.md "Hub decisions (curation policy)").
# T1: Toyota climate-control sub-assemblies are their own packaging/slot.
TOYOTA_CLIMATE_SWITCH_BASES = ("55901", "55902", "55903")
# P1: Hyundai/Kia door-module panels carry the regulator: packaging
# "door-module", matching only other door-module packages.
DOOR_MODULE_RE = re.compile(r"door\s*(dr\s*)?module|module\s+panel|panel\s+assy-?\s*(front|rear|fr|rr)?\s*(door|dr)\s*module", re.I)

# §5.18 Phase 2 atoms (computed in reports, never shipped in Phase 1).
# basis: VIN position 1 world manufacturer region (ISO 3779); the plant atom
# ships only after owner question Q2 and its audit. The spec table maps L to
# KR; ISO 3779 assigns L to China (Korean WMIs start with K: KM Hyundai,
# KN Kia, KL GM Korea), so L is CN here and never satisfies plant=KR.
PLANT_FROM_VIN0 = {"1": "US", "4": "US", "5": "US", "2": "CA", "3": "MX", "J": "JP",
                   "K": "KR", "L": "CN"}
PLANT_NOTE = {"us": "US", "usa": "US", "u.s.": "US", "japan": "JP", "canada": "CA",
              "mexico": "MX", "korea": "KR"}
