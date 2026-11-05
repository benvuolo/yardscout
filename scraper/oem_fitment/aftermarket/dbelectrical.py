"""DB Electrical (www.dbelectrical.com): Lester-numbered alternators and starters.

Navigation (BigCommerce category tree, no search, robots-checked):
    /alternators/automotive/            make index
    /alternators/automotive/<make>/     model index
    /alternators/automotive/<make>/<model>/[?page=N]   product cards
    /products/<slug>.html               product page

Product page blocks parsed (all server-rendered HTML):
    span[data-product-sku]       -> aftermarket_pn (their item number, e.g. 400-14103)
    #product-specs table         -> specs {Unit Type, Voltage, Amperage, ..., Fits}
    #applications-list table     -> applications, one per printed row
                                    (MAKE | TYPE | MODEL | YEAR | ENGINE)
    #replaces-list table         -> replaces [{brand, numbers}] verbatim

The replaces table is PRODUCT-level: it does not say which OE number goes
with which application row (oe_scope = "product").
"""
from __future__ import annotations

import html as htmllib
import re

try:
    from . import common
except ImportError:  # run as a script from this directory
    import common  # type: ignore

SITE = "www.dbelectrical.com"
STATUS = "ok"
BASE = f"https://{SITE}"
CATEGORIES = {
    "alternator": {"root": "/alternators/automotive/", "unit_type": "Alternator"},
    "starter": {"root": "/starters/automotive/", "unit_type": "Starter"},
}
get = common.get  # tests swap this for a cache-only reader


def _cell_text(c: str) -> str:
    """Cell text as printed: tags dropped, entities decoded, each line stripped,
    <br> kept as a newline, internal spacing untouched ("V8  DIESEL" stays)."""
    c = re.sub(r"<br\s*/?>", "\n", c, flags=re.I)
    c = htmllib.unescape(re.sub(r"<[^>]+>", "\n", c))
    return "\n".join(ln.strip() for ln in c.splitlines() if ln.strip())


def _cells(row_html: str) -> list[str]:
    return [_cell_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.S | re.I)]


def _block(html: str, div_id: str) -> str | None:
    m = re.search(r'<div id="%s">(.*?)</table>' % re.escape(div_id), html, re.S)
    return m.group(1) if m else None


def _rows(block: str) -> list[list[str]]:
    return [_cells(r) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S | re.I)]


# ---------------------------------------------------------------- listing ---

def parse_listing(url: str, html: str) -> dict:
    """Product cards, child category pages one level below `url`, next page."""
    path = re.sub(r"\?.*$", "", url[len(BASE):])
    products = []
    for m in re.finditer(r'<h3 class="card-title">\s*<a[^>]*href="(https://www\.dbelectrical\.com/products/[^"?#]+\.html)"', html):
        if m.group(1) not in products:
            products.append(m.group(1))
    children = []
    child_re = re.compile(r'href="https://www\.dbelectrical\.com(%s[A-Za-z0-9][A-Za-z0-9\-]*/)"' % re.escape(path))
    for c in child_re.findall(html):
        u = BASE + c
        if u not in children:
            children.append(u)
    nxt = None
    m = re.search(r'<a class="pagination-link" href="([^"]+)"[^>]*aria-label="Next Page"', html)
    if m:
        nxt = htmllib.unescape(m.group(1))
        if not re.fullmatch(re.escape(BASE + path) + r"\?page=\d+", nxt):
            nxt = None  # only the plain ?page=N pattern; never facet/filter URLs
    return {"products": products, "children": children, "next": nxt}


def listing(url: str) -> dict:
    return parse_listing(url, get(url)["html"])


# ---------------------------------------------------------------- product ---

def parse_product(url: str, html: str, retrieved: str, category: str) -> dict:
    flags: list[str] = []
    ev: list[str] = []
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    title = _cell_text(m.group(1)).replace("\n", " ") if m else ""
    ev.append(title)
    m = re.search(r"<span data-product-sku[^>]*>([^<]+)</span>", html)
    pn = m.group(1).strip() if m else ""
    ev.append(f"Item #: {pn}")
    m2 = re.search(r"<strong>Item Number:\s*([^<]+)</strong>", html)
    if not pn:
        flags.append("no_sku")
    if m2 and m2.group(1).strip() != pn:
        flags.append(f"item_number_differs:{m2.group(1).strip()}")

    specs: dict[str, str] = {}
    blk = _block(html, "product-specs")
    if blk:
        for r in _rows(blk):
            if len(r) == 2:
                specs[r[0]] = r[1]
                ev.append(f"{r[0]} | " + r[1].replace("\n", " / "))
    else:
        flags.append("no_specs_table")
    want = common_unit = None
    if category in CATEGORIES:
        want = CATEGORIES[category]["unit_type"]
        common_unit = specs.get("Unit Type", "")
        if want.lower() not in common_unit.lower().split():  # "Automotive Starter" ok; "Generator" flagged
            flags.append(f"unit_type_not_{want.lower()}:{common_unit or 'missing'}")

    apps = []
    blk = _block(html, "applications-list")
    if blk is None:
        flags.append("no_applications_table")
    else:
        rows = _rows(blk)
        header = [h.upper() for h in rows[0]] if rows else []
        if header[:5] != ["MAKE", "TYPE", "MODEL", "YEAR", "ENGINE"]:
            flags.append(f"applications_header:{'|'.join(header)}")
        ev.append(" | ".join(rows[0]) if rows else "")
        idx = {h: i for i, h in enumerate(header)}
        for r in rows[1:]:
            raw = " | ".join(r)
            ev.append(raw)
            try:
                ytxt = r[idx["YEAR"]]
                ym = re.fullmatch(r"(\d{4})(?:\s*-\s*(\d{4}))?", ytxt)
                if not ym:
                    raise ValueError(ytxt)
                lo = int(ym.group(1))
                hi = int(ym.group(2) or lo)
                apps.append({"years": [lo, hi], "make": r[idx["MAKE"]], "type": r[idx["TYPE"]],
                             "model": r[idx["MODEL"]], "engine": r[idx["ENGINE"]],
                             "notes": "", "raw": raw})
            except (KeyError, IndexError, ValueError):
                flags.append(f"unparsed_application_row:{raw}")
        if not apps:
            flags.append("no_application_rows")

    replaces = []
    blk = _block(html, "replaces-list")
    if blk is None:
        flags.append("no_replaces_table")
    else:
        ev.append("Replaces These Part Numbers")
        for r in _rows(blk):
            if len(r) != 2:
                flags.append(f"unparsed_replaces_row:{' | '.join(r)}")
                continue
            ev.append(f"{r[0]} | {r[1]}")
            nums = [n.strip() for n in r[1].split(",") if n.strip()]
            replaces.append({"brand": r[0], "numbers": nums})
    cls = common.classify_replaces(replaces)
    if not cls["oe_numbers"]:
        flags.append("no_carmaker_oe_numbers")
    lester = [x["pn"] for x in cls["interchange_numbers"] if x["brand"].upper() == "LESTER"]
    makes = sorted({a["make"].strip().lower() for a in apps})
    return {
        "site": SITE, "category": category, "aftermarket_pn": pn, "aftermarket_brand": "DB Electrical",
        "title": title, "lester": lester,
        "oe_numbers": cls["oe_numbers"], "oe_scope": "product",
        "oe_service_numbers": cls["oe_service_numbers"],
        "oe_supplier_numbers": cls["oe_supplier_numbers"],
        "interchange_numbers": cls["interchange_numbers"],
        "other_numbers": cls["other_numbers"], "ambiguous_numbers": cls["ambiguous_numbers"],
        "replaces": replaces, "specs": specs, "fits_text": specs.get("Fits", ""),
        "applications": apps, "application_spans": common.merge_spans(apps),
        "multi_make": len(makes) > 1,
        "evidence_lines": ev, "flags": flags,
        "product_url": url, "retrieved": retrieved,
    }


def product(url: str, category: str) -> dict:
    d = get(url)
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_product(url, d["html"], d["retrieved"], category)
