"""GSP North America (gspnorthamerica.com, Shopify): CV axles (application tables).

Owner 2026-11-09 (relayed by the hub, ops/hub.md): "Yes, use GSP". Likely-only,
strict refusals, drive and transmission never inferred (SOURCES.md, Source
scout 2). Challenge rule: fetch.gsp_challenged (site-scoped).

Navigation (no search URLs; everything robots-allowed GET):
    /sitemap.xml                       sitemap index
    /sitemap_products_N.xml?from=&to=  product sitemaps; <image:title> carries
                                       the product title, used to pick the
                                       category and to order by make
    /products/<handle>                 product page

Product page blocks parsed (server-rendered HTML):
    <title>                                 title, verbatim (engines in "(...)")
    <p class="product__text ..."><strong>Part Number:</strong> PN</p>
    <table class="product-applications__table">
        Year Range | Make | Model | Submodel | Position, one per printed row
    Specifications <table class="theme-table ..."> th/td pairs

Facts only: no description text, images or prices are stored.
"""
from __future__ import annotations

import html as htmllib
import re
import xml.etree.ElementTree as ET

try:
    from . import common
except ImportError:  # run as a script from this directory
    import common  # type: ignore

SITE = "gspnorthamerica.com"
STATUS = "ok"
BASE = f"https://{SITE}"
# Category = title pattern on the sitemap <image:title> AND on the page title.
# strut is added only after a sampled page confirms GSP's ride-control titles.
CATEGORIES = {
    "cv-axle": {"root": "/sitemap.xml", "title_re": re.compile(r"\bCV Axle Assembly\b", re.I)},
}
get = common.get  # tests swap this for a cache-only reader

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
       "image": "http://www.google.com/schemas/sitemap-image/1.1"}
_MAKE_SCORES = None


def _make_scores() -> dict:
    """norm(make) -> cars on our lots (worklist), for ordering products."""
    global _MAKE_SCORES
    if _MAKE_SCORES is None:
        try:
            from run import build_scores  # type: ignore
        except ImportError:
            from .run import build_scores  # type: ignore
        try:
            _MAKE_SCORES = dict(build_scores()[0])
        except (OSError, ValueError, KeyError):
            _MAKE_SCORES = {}
    return _MAKE_SCORES


def title_score(title: str) -> float:
    """Highest lot count among the makes named in a product title."""
    ms = _make_scores()
    words = re.findall(r"[A-Za-z][A-Za-z-]+(?: [A-Z][a-z]+)?", title)
    best = 0.0
    for w in words:
        for cand in (w, w.split(" ")[0]):
            best = max(best, ms.get(common.norm(cand), 0.0))
    return best


def parse_listing(url: str, body: str, category: str = "cv-axle") -> dict:
    out = {"children": [], "products": [], "next": None}
    root = ET.fromstring(body)
    tag = root.tag.split("}")[-1]
    if tag == "sitemapindex":
        for loc in root.findall("sm:sitemap/sm:loc", _NS):
            u = (loc.text or "").strip()
            if u.startswith(BASE + "/sitemap_products_"):
                out["children"].append(u)
        return out
    if tag != "urlset":
        raise ValueError(f"not a sitemap: {url}")
    rx = CATEGORIES[category]["title_re"]
    picked = []
    for i, node in enumerate(root.findall("sm:url", _NS)):
        loc = (node.findtext("sm:loc", "", _NS) or "").strip()
        if not loc.startswith(BASE + "/products/"):
            continue
        titles = [t.text or "" for t in node.findall("image:image/image:title", _NS)]
        if not any(rx.search(t) for t in titles):
            continue
        picked.append((-title_score(titles[0]), i, loc))
    out["products"] = [loc for _, _, loc in sorted(picked)]
    return out


def listing(url: str, category: str = "cv-axle") -> dict:
    d = get(url)
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_listing(url, d["html"], category)


# -------------------------------------------------------------- product ---
def _text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
_PN = re.compile(r'<p\s+class="product__text[^"]*"[^>]*>\s*<strong>Part Number:</strong>\s*([^<]+?)\s*</p>', re.S)
_APPS = re.compile(r'<table class="product-applications__table">(.*?)</table>', re.S)
_SPECS = re.compile(r'Specifications\s*</h2>\s*<table class="theme-table[^"]*"[^>]*>(.*?)</table>', re.S)
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_CELL = re.compile(r"<t([hd])[^>]*>(.*?)</t\1>", re.S)
_YEARS = re.compile(r"^(19[5-9]\d|20[0-4]\d)\s*-\s*(19[5-9]\d|20[0-4]\d)$")
APP_HEADER = ["Year Range", "Make", "Model", "Submodel", "Position"]


def parse_product(url: str, page: str, retrieved: str, category: str) -> dict:
    flags = []
    tm = _TITLE.search(page)
    title = _text(tm.group(1)) if tm else ""
    title = re.sub(r"\s*[–-]\s*GSP North America$", "", title).strip()
    pm = _PN.search(page)
    pn = _text(pm.group(1)) if pm else ""
    if not pn:
        flags.append("no_part_number")
    if not CATEGORIES[category]["title_re"].search(title):
        flags.append("title_not_category")
    # engines: the parenthesised list in the title, verbatim tokens
    em = re.search(r"\(([^()]*)\)", title)
    title_engines = [e.strip() for e in em.group(1).split(",") if e.strip()] if em else []
    pos_m = re.search(r"\s-\s([A-Za-z ]+)$", title)
    title_position = pos_m.group(1).strip() if pos_m else ""

    apps, raw_rows = [], []
    am = _APPS.search(page)
    if not am:
        flags.append("no_application_table")
    else:
        rows = _ROW.findall(am.group(1))
        header = [_text(c) for _, c in _CELL.findall(rows[0])] if rows else []
        if header != APP_HEADER:
            flags.append("application_header_changed")
        else:
            for r in rows[1:]:
                cells = [_text(c) for _, c in _CELL.findall(r)]
                raw_rows.append(cells)
                if len(cells) != 5:
                    flags.append("application_row_shape")
                    continue
                ym = _YEARS.match(cells[0])
                if not ym:
                    flags.append("application_years_unparsed")
                    continue
                lo, hi = int(ym.group(1)), int(ym.group(2))
                if hi < lo:
                    flags.append("application_years_reversed")
                    continue
                apps.append({"years": [lo, hi], "make": cells[1], "model": cells[2],
                             "submodel": "" if cells[3] == "-" else cells[3],
                             "position": "" if cells[4] == "-" else cells[4],
                             "engine": "", "type": "", "notes": "", "raw": " | ".join(cells)})
    keys = [(tuple(a["years"]), a["make"], a["model"], a["submodel"], a["position"]) for a in apps]
    duplicate_rows = len(keys) - len(set(keys))
    if duplicate_rows:
        flags.append("duplicate_rows")
    if any(not a["position"] for a in apps):
        flags.append("position_missing")

    specs = {}
    sm = _SPECS.search(page)
    if sm:
        for r in _ROW.findall(sm.group(1)):
            cells = _CELL.findall(r)
            if len(cells) == 2 and cells[0][0] == "h" and cells[1][0] == "d":
                specs[_text(cells[0][1])] = _text(cells[1][1])

    makes = sorted({a["make"] for a in apps})
    return {
        "site": SITE, "category": category, "aftermarket_pn": pn, "aftermarket_brand": "GSP",
        "title": title, "title_engines": title_engines, "title_position": title_position,
        "oe_numbers": [], "oe_scope": "none", "replaces": [],
        "specs": specs, "applications": apps, "application_spans": spans(apps),
        "application_rows_printed": len(raw_rows), "duplicate_rows": duplicate_rows,
        "multi_make": len(makes) > 1, "flags": sorted(set(flags)),
        "product_url": url, "retrieved": retrieved,
    }


def spans(apps: list[dict]) -> list[dict]:
    """Derived view: contiguous rows merged per (make, model, submodel, position).
    Never evidence; `applications` (one per printed row) is the evidence."""
    keyed = [{**a, "type": a["submodel"] + "\x1f" + a["position"]} for a in apps]
    out = []
    for sp in common.merge_spans(keyed):
        sub, pos = sp.pop("type").split("\x1f")
        out.append({**sp, "submodel": sub, "position": pos})
    return out


def product(url: str, category: str) -> dict:
    d = get(url)
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_product(url, d["html"], d.get("retrieved", ""), category)
