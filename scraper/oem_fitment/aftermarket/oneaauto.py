"""1A Auto (www.1aauto.com): retailer catalog, house brands (TRQ, Dependable Direct, ...).

Owner 2026-11-09 (relayed by the hub, ops/hub.md): "Yes, use 1A Auto anyway"
(accepts the personal/non-commercial licence risk). Facts only: unit ->
vehicles, notes in our own wording downstream. Label "1A Auto" + unit number.
No page text, images or descriptions are published. robots: Crawl-Delay 1
(fetch.py's 8 s per-site gap is larger and is what applies).

Navigation (server-rendered GET; /search, sort=, pageSize= are robots-disallowed
and never built):
    /<cat-slug>/c/<cid>                          category: make links
    /<make>-<cat-slug>/ma-c/<mid>-<cid>           make: model links
    /<make>-<model>-<cat-slug>/mo-c/<moid>-<cid>  model: product cards, ?page=N
    /<slug>/i/<sku>                               product page

Product page blocks parsed:
    <script id="sc" type="application/ld+json">   sku, mpn, brand
    <h1 id="product-name">                         title
    <table class="fitTable ...">                   Year | Make | Model | Description rows
    <table id="interchange-codes-table">           Brand Label | Part Number rows
Multi-piece sets and kits are skipped (they repeat single units).
"""
from __future__ import annotations

import html as htmllib
import json
import re
import urllib.parse

try:
    from . import common
except ImportError:  # run as a script from this directory
    import common  # type: ignore

SITE = "www.1aauto.com"
STATUS = "ok"
BASE = f"https://{SITE}"
CATEGORIES = {
    "strut": {"root": "/shocks-and-struts/c/64", "slug": "shocks-and-struts",
              "unit_re": re.compile(r"strut-(?:and-spring-)?assembly|complete-strut")},
    "knuckle": {"root": "/steering-knuckles-and-spindles/c/381", "slug": "steering-knuckles-and-spindles",
                "unit_re": re.compile(r"knuckle|spindle")},
    "cv-axle": {"root": "/axles-and-axleshafts/c/84", "slug": "axles-and-axleshafts",
                "unit_re": re.compile(r"cv-axle|axle-shaft")},
    "door-handle-ext": {"root": "/exterior-door-handles/c/15", "slug": "exterior-door-handles",
                        "unit_re": re.compile(r"exterior-door-handle|outside-door-handle")},
    "door-lock-actuator": {"root": "/power-door-lock-actuator/c/21", "slug": "power-door-lock-actuator",
                           "unit_re": re.compile(r"lock-actuator")},
    "wiper-motor": {"root": "/windshield-wiper-motors/c/24", "slug": "windshield-wiper-motors",
                    "unit_re": re.compile(r"wiper-motor")},
    "blower-motor": {"root": "/blower-motor/c/112", "slug": "blower-motor",
                     "unit_re": re.compile(r"blower-motor(?!-resistor)")},
    "maf-sensor": {"root": "/air-flow-meter/c/77", "slug": "air-flow-meter",
                   "unit_re": re.compile(r"mass-air-flow|air-flow-(?:meter|sensor)|maf")},
    "throttle-body": {"root": "/throttle-body-assembly/c/229", "slug": "throttle-body-assembly",
                      "unit_re": re.compile(r"throttle-body")},
    "fuel-pump-module": {"root": "/fuel-pump/c/65", "slug": "fuel-pump",
                         "unit_re": re.compile(r"fuel-pump(?:-and-sending|-module|-assembly)")},
    "power-steering-pump": {"root": "/power-steering-pump/c/212", "slug": "power-steering-pump",
                            "unit_re": re.compile(r"power-steering-pump(?!-reservoir)")},
    "radiator": {"root": "/radiator/c/34", "slug": "radiator",
                 "unit_re": re.compile(r"(?<![a-z])radiator(?!-(?:fan|hose|cap|support|overflow|tank|mount))")},
}
SET_RE = re.compile(r"(?:^|-)(?:\d+-piece|set|kit|pair)(?:-|$)")
get = common.get  # tests swap this for a cache-only reader
_SCORES = None


def _scores():
    global _SCORES
    if _SCORES is None:
        try:
            from run import build_scores  # type: ignore
        except ImportError:
            from .run import build_scores  # type: ignore
        try:
            _SCORES = build_scores()
        except (OSError, ValueError, KeyError):
            _SCORES = ({}, {})
    return _SCORES


def _slug_parts(url: str):
    p = urllib.parse.urlsplit(url).path
    m = re.fullmatch(r"/([a-z0-9-]+)/(ma-c|mo-c|c)/[0-9-]+", p)
    if not m:
        return None, None
    slug, kind = m.group(1), m.group(2)
    for c in CATEGORIES.values():
        if slug.endswith("-" + c["slug"]):
            return kind, slug[: -len(c["slug"]) - 1]
    return kind, ""


def score(url: str, *_ignored) -> float:
    """Lot-weighted: make pages by cars of that make, model pages by cars of
    that make+model (split of the slug that matches the worklist)."""
    make_s, model_s = _scores()
    kind, stem = _slug_parts(url)
    if kind == "c" or kind is None:
        return 1e9 if kind == "c" else 0.0
    toks = stem.split("-")
    if kind == "ma-c":
        return 1e6 + make_s.get(common.norm(stem), 0.0)
    best = 0.0
    for i in range(1, len(toks)):
        mk, mo = common.norm("".join(toks[:i])), common.norm("".join(toks[i:]))
        best = max(best, model_s.get((mk, mo), 0.0))
    return best


def parse_listing(url: str, body: str, category: str) -> dict:
    out = {"children": [], "products": [], "next": None}
    kind, _ = _slug_parts(url)
    cid = CATEGORIES[category]["root"].rsplit("/", 1)[1]
    if kind == "c":
        out["children"] = sorted({BASE + h for h in re.findall(rf'href="(/[a-z0-9-]+/ma-c/\d+-{cid})"', body)})
        return out
    if kind == "ma-c":
        out["children"] = sorted({BASE + h for h in re.findall(rf'href="(/[a-z0-9-]+/mo-c/\d+-{cid})"', body)})
        return out
    if kind != "mo-c":
        raise ValueError(f"not a listing url: {url}")
    rx = CATEGORIES[category]["unit_re"]
    seen = set()
    for h in re.findall(r'href="(/[a-z0-9-]+/i/[a-z0-9]+)"', body):
        slug = h.split("/")[1]
        if h in seen or SET_RE.search(slug) or not rx.search(slug):
            continue
        seen.add(h)
        out["products"].append(BASE + h)
    nm = re.search(r'<link href="(https://www\.1aauto\.com/[^"?]+/mo-c/[0-9-]+\?page=\d+)" rel="next"', body)
    if nm:
        out["next"] = htmllib.unescape(nm.group(1))
    return out


def category_of(url: str) -> str:
    """Our category from the 1A category id at the end of a listing path."""
    m = re.search(r"/(?:c|ma-c|mo-c)/(?:\d+-)?(\d+)$", urllib.parse.urlsplit(url).path)
    for name, c in CATEGORIES.items():
        if m and c["root"].rsplit("/", 1)[1] == m.group(1):
            return name
    raise ValueError(f"no category for {url}")


def listing(url: str, category: str | None = None) -> dict:
    category = category or category_of(url)
    d = get(url)
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_listing(url, d["html"], category)


# -------------------------------------------------------------- product ---
def _text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


_LD = re.compile(r'<script id="sc" type="application/ld\+json">(.*?)</script>', re.S)
_H1 = re.compile(r'<h1 id="product-name">(.*?)</h1>', re.S)
_FIT = re.compile(r'<table class="fitTable[^"]*">(.*?)</table>', re.S)
_FITROW = re.compile(r'<tr class="sortable_row[^"]*"[^>]*>(.*?)</tr>', re.S)
_FITCELL = re.compile(r'<td class="(tYear|tMake|tModel|tDesc)">(.*?)(?=<td class=|</tr>|$)', re.S)
_IC = re.compile(r'<table id="interchange-codes-table"[^>]*>(.*?)</table>', re.S)
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_YEARS = re.compile(r"^(19[5-9]\d|20[0-4]\d)(?:\s*-\s*(19[5-9]\d|20[0-4]\d))?$")


def parse_product(url: str, page: str, retrieved: str, category: str) -> dict:
    flags = []
    sku = mpn = brand = ""
    lm = _LD.search(page)
    if lm:
        try:
            ld = json.loads(lm.group(1))
            sku, mpn = str(ld.get("sku", "")), str(ld.get("mpn", ""))
            b = ld.get("brand") or {}
            brand = str(b.get("name", "")) if isinstance(b, dict) else str(b)
        except ValueError:
            flags.append("structured_data_unparsed")
    else:
        flags.append("no_structured_data")
    if not sku:
        flags.append("no_sku")
    hm = _H1.search(page)
    title = _text(hm.group(1)) if hm else ""

    apps = []
    fm = _FIT.search(page)
    if not fm:
        flags.append("no_fitment_table")
    else:
        for r in _FITROW.findall(fm.group(1)):
            cells = {k: _text(v.replace("</td>", "")) for k, v in _FITCELL.findall(r)}
            if set(cells) != {"tYear", "tMake", "tModel", "tDesc"}:
                flags.append("fitment_row_shape")
                continue
            ym = _YEARS.match(cells["tYear"])
            if not ym:
                flags.append("fitment_years_unparsed")
                continue
            lo, hi = int(ym.group(1)), int(ym.group(2) or ym.group(1))
            if hi < lo:
                flags.append("fitment_years_reversed")
                continue
            apps.append({"years": [lo, hi], "make": cells["tMake"], "model": cells["tModel"],
                         "type": "", "engine": "", "description": cells["tDesc"], "notes": "",
                         "raw": " | ".join(cells[k] for k in ("tYear", "tMake", "tModel", "tDesc"))})
    if fm and not apps:
        flags.append("fitment_table_empty")
    keys = [(tuple(a["years"]), a["make"], a["model"], a["description"]) for a in apps]
    duplicate_rows = len(keys) - len(set(keys))
    if duplicate_rows:
        flags.append("duplicate_rows")

    interchange = []
    im = _IC.search(page)
    if im:
        for r in _ROW.findall(im.group(1)):
            tds = [_text(c) for c in _TD.findall(r)]
            if len(tds) == 2 and tds[0] and tds[1]:
                interchange.append({"brand": tds[0], "pn": tds[1]})
    slug = urllib.parse.urlsplit(url).path.split("/")[1] if "/i/" in url else ""
    if slug and not CATEGORIES[category]["unit_re"].search(slug):
        flags.append("slug_not_category")
    makes = sorted({a["make"] for a in apps})
    return {
        "site": SITE, "category": category, "aftermarket_brand": "1A Auto",
        "aftermarket_pn": sku, "house_brand": brand, "house_brand_pn": mpn, "title": title,
        "oe_numbers": [], "oe_scope": "none",
        "interchange_numbers": interchange, "replaces": [],
        "applications": apps, "application_spans": spans(apps),
        "duplicate_rows": duplicate_rows, "multi_make": len(makes) > 1,
        "flags": sorted(set(flags)), "product_url": url, "retrieved": retrieved,
    }


def spans(apps: list[dict]) -> list[dict]:
    """Derived view: contiguous rows merged per (make, model, description).
    Never evidence; `applications` (one per printed row) is the evidence."""
    out = []
    for sp in common.merge_spans([{**a, "type": a["description"]} for a in apps]):
        out.append({**sp, "description": sp.pop("type")})
    return out


def product(url: str, category: str) -> dict:
    d = get(url)
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_product(url, d["html"], d.get("retrieved", ""), category)
