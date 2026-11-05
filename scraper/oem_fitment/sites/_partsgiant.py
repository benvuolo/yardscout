"""Shared code for the PartsGiant ".html" dealer-catalog template.

Sites on this template (fetch.py ALLOWED): gmpartsgiant, fordpartsgiant,
moparpartsgiant, nissanpartsdeal, infinitipartsdeal, hondapartsnow,
acurapartswarehouse, hyundaipartsdeal, kiapartsnow, subarupartsdeal,
lexuspartsnow. All network access goes through fetch.get (cache, robots,
rate limits, circuit breaker); a fetch.Refused is never caught here.

Catalog layout (learned through fetch.py, 2026-11-05)
----------------------------------------------------
  /<make>-<model>-parts.html                 model page: links to year catalogs
  /<year>-<make>-<model>[-<variant>]-parts.html
        year catalog. <variant> appears when one model-year has several
        catalogs (gm: new_model / classic_carryover_model; ford: gas / hybrid;
        nissan: coupe / sedan). Some makes (Honda family) add a per-trim level:
        /<year>-<make>-<model>--<trim>-parts.html (double dash); Ford does the
        same per engine + transmission for some years
        (/2001-ford-f_150--8_cyl_5_4l-5mt-parts.html).
  /parts-list/<year>-<make>-<model>[-<variant>]/<section>/<subcategory>.html
        parts list for one subcategory (one or more diagrams)
  /parts/<brand>-<name>-<pn>.html            product page

Slugs are the printed name lower-cased with every run of non-alphanumerics
turned into "_" ("F-150" -> "f_150", "Town & Country" -> "town_country").

Pages are server-rendered and also carry the same data as JSON in
`window.__INITIAL_STORE__` (same page, same response). The parsers read that
store because the visible fitment table is cut at 10 rows behind a "View More"
toggle while the store holds the whole list. As a guard, product() checks that
the rows rendered in the HTML table are exactly the first rows of the store
list and raises if they are not, so a template change cannot silently produce
different evidence.

Site modules stay thin:

    from sites import _partsgiant as T
    SITE = "www.gmpartsgiant.com"
    CFG = T.Config(site=SITE, models={...}, subcats={...}, parts={...})
    categories_for, parts_on_page, product = T.bind(CFG)

Config fields
-------------
models       {(feed make, feed model): M(...) or [M(years=...), ...]}: the
             site's model slug(s) and the year-catalog variant rules (see M).
             Missing entries use slug(make), slug(model), every variant except
             DEFAULT_VARIANT_EXCLUDE (hybrid/electric), plain catalog first.
             At most MAX_CATALOGS catalogs per model-year are crawled.
subcats      {category id: regex} searched (case-insensitive) in the
             <subcategory> slug of each parts-list link on the year catalog
             (the section slug is not used: GM sections such as
             "starter_generator_ignition_electrical_lamps" name everything).
subcat_excl  {category id: regex} parts-list links to drop.
parts        {category id: (include, exclude_head[, exclude_full])}.
             include and exclude_full are searched in the row's printed text
             "<pncDesc> | <mainDesc> | <remark> | <info; info>"; exclude_head
             only in "<pncDesc> | <mainDesc> | <remark up to its first '('>",
             so catalog notes such as "(W/O FUEL LEVEL SENSOR)" do not knock
             out an assembly. A part is kept when include matches and neither
             exclude does. COMMON_EXCLUDE (bulbs, bolts, clips, brackets,
             gaskets, seals, wiring, labels, trim, ...) always applies to
             "<pncDesc> | <mainDesc>" (or to head_fn(row) when the site
             sets head_fn). A rule may instead be a function
             rule(row, text) -> bool (row: pn, group, main, remark, info),
             e.g. Ford matches on the base number inside its part number.

What a record holds (product())
-------------------------------
pn; description (the page's "Part Description"); position: the side the
parts list printed for this pn ("Location: Driver Side", Ford/GM/Nissan; Mopar
prints a bare "Left"/"Right"), else the product page's "lr" field ("Passenger
Side"), else None. When list and product page name opposite sides, position
is None and flags says so (the Mopar product page for 1AN401BGAD says "Driver
Side"/"Door Mirror Left" while the catalog row says "Right") (sides written inside the description, "Headlamp
Assy-LH", stay in description only); replaces (list); replaced_by (the page's "Replaced By", raw or None);
fitment rows; evidence_lines; flags; retrieved.

fitment row: years [lo, hi] as printed ("2010-2015" or "2012"; a cell that
lists several spans, "2002, 1999-2000 Chevrolet Silverado", becomes one row
per span with the same raw), make = first
word after the years, model = the rest of that cell, engines from the Engine
column, options = the "Important vehicle option details" cell split on ", "
(GM: trim + body names; Ford: transmissions and drive; Mopar: trims; Nissan:
engine codes), trims = the "Trim" part of a "Trim & Engine" cell
("Base, S|4 Cyl 2.5L": trims before "|", engines after; a cell with no "|"
is engines when every item reads as an engine, "6 Cyl 3.5L", else trims) or,
when the site sets
option_column_is_trims, the options. raw = the row's cells joined by " | "
exactly as printed (a "|" with no spaces is the site's own, inside a cell).

evidence_lines: "Part Number", "Part Description", "Position" (lr), "Parts
list <url>: <position>" when the position came from the list page, "Replaced
By", "Replaces", "Notes", then the fitment header and every fitment row (raw),
in page order, capped at 120 lines (flags notes a truncation).

parts_on_page adds list-level evidence for the seed vehicle: list_group
(pncDesc), list_remark (the remark printed after the name) and list_info
(e.g. "Fitting Vehicle Options: Z(LY7)", "Replaced By: 12745819",
"Location: Driver Side").
"""
from __future__ import annotations

import html as htmllib
import json
import re
import urllib.parse
from dataclasses import dataclass, field

from fetch import get

MAX_CATALOGS = 2       # catalogs (variants or trims) per model-year
# Parts-list pages that never hold a puller's assembly (any category).
SUBCAT_COMMON_EXCLUDE = re.compile(r"wiring|harness|labels?$|paint|decal|emblem|stripe", re.I)
EVIDENCE_CAP = 120

# Never a puller's assembly (README "Exclude from every category").
COMMON_EXCLUDE = re.compile(
    r"\b(BULBS?|SOCKETS?|GASKETS?|BOLTS?|SCREWS?|NUTS?|STUDS?|WASHERS?|CLIPS?|"
    r"BRACKETS?|BRKTS?|BRACES?|RETAINERS?|SEALS?|WEATHERSTRIPS?|O-RINGS?|"
    r"HARNESS(ES)?|WIRING|WIRES?|PIGTAILS?|CONNECTORS?|TERMINALS?|LABELS?|DECALS?|"
    r"EMBLEMS?|NAMEPLATES?|PLUGS?|GROMMETS?|SPACERS?|SHIMS?|PULLEYS?|BELTS?|"
    r"FUSES?|INSULATORS?|SHIELDS?|DEFLECTORS?|TAPES?|ADHESIVES?|KNOBS?|BEZELS?|"
    r"HOSES?|PIPES?|LINES?|TUBES?|FITTINGS?|RESERVOIRS?|CAPS?|FILTERS?|"
    r"MOULDINGS?|MOLDINGS?|TRIM|GARNISH|SPRINGS?|PINS?|CABLES?|RIVETS?|"
    r"KEYS?|ANTENNAS?|PADS?|STRIPS?|BUMPERS? STOPS?|LOCATORS?|"
    r"REFLECTORS?|MOUNTS?|MOUNTINGS?|HANGERS?|STRAPS?|SUPPORTS?)\b",
    re.I)


@dataclass
class M:
    """How one feed model maps onto the site. slugs: the site's model slug(s)
    (several when the site splits one feed model over model pages, e.g.
    C/K 1500 -> c1500 + k1500). inc / exc / pref: regexes on the year-catalog
    variant ("" for the plain catalog, e.g. "1500_4wd", "new_model", "coupe").
    years: (lo, hi) model years this mapping applies to (None = all)."""
    slugs: object = None
    inc: str | None = None
    exc: str | None = None
    pref: str | None = None
    make: str | None = None
    years: tuple | None = None


# Variants that are a different vehicle unless the feed model names them.
DEFAULT_VARIANT_EXCLUDE = r"hybrid|electric|plug_in|(^|_)ev($|_)"


@dataclass
class Config:
    site: str
    subcats: dict
    parts: dict
    # {(feed make, feed model): M or [M, ...] (by years)}; missing -> M()
    models: dict = field(default_factory=dict)
    subcat_excl: dict = field(default_factory=dict)
    # True when the site prints trim names in the "Important vehicle option
    # details" column (GM, Mopar); False when it prints drivetrain options there
    # (Ford). Either way the column is kept verbatim in fitment[].options.
    option_column_is_trims: bool = False
    # optional: row -> the text exclude_head is tested on (default
    # "<pncDesc> | <mainDesc> | <remark up to its first '('>")
    head_fn: object = None
    # optional extra pattern (searched like REMAN_RE) for a make's own word
    # for remanufactured units, e.g. BMW "Exch. alternator" / "Exchange ..."
    reman_re: object = None
    # header regex of the column kept as fitment[].options (BMW prints its
    # body/engine variants under "Submodel")
    option_col: str = r"option|detail"
    # optional (Honda family): (make, model, year, [trim slugs in page order])
    # -> the trim slugs to read when a year catalog is split per trim
    # ("4dr_lx-ka_5at"). Default: first and last in page order.
    trim_pick: object = None
    # optional: header regex of the column kept as fitment[].trims when it is
    # not "Trim" (Honda family: "Body & Trim").
    trim_col: str | None = None
    # optional: row -> True for a remanufactured row the site marks its own way
    # (Honda "(RMD)", "Core Id", pn suffix "RM"); OR-ed with REMAN_RE.
    reman_fn: object = None


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def absolute(site: str, href: str) -> str:
    return urllib.parse.urljoin(f"https://{site}/", href)


def store(html: str) -> dict:
    """The page's window.__INITIAL_STORE__ object. It is a JS literal that is
    JSON except for bare `undefined`, which becomes null."""
    i = html.find("window.__INITIAL_STORE__")
    if i < 0:
        raise ValueError("no __INITIAL_STORE__ on page")
    i = html.find("=", i) + 1
    e = html.find("</script>", i)
    s = html[i:e].strip().rstrip(";")
    s = re.sub(r"(?<=[:,\[])undefined(?=[,}\]])", "null", s)
    return json.loads(s)


def _page(url: str) -> dict:
    d = get(url)
    if d.get("status") != 200:
        raise ValueError(f"HTTP {d.get('status')} for {url}")
    return d


# ---------------------------------------------------------------- navigation

def _mapping(cfg: Config, make: str, model: str, year: int) -> M:
    spec = cfg.models.get((make, model))
    if spec is None:
        return M()
    if isinstance(spec, M):
        spec = [spec]
    for m in spec:
        if m.years is None or m.years[0] <= year <= m.years[1]:
            return m
    raise ValueError(f"no site mapping for {make} {model} {year}")


def year_catalogs(cfg: Config, make: str, model: str, year: int) -> list[tuple[str, str]]:
    """[(variant, absolute year-catalog url)] for this feed vehicle-year after
    the variant rules, at most MAX_CATALOGS. Order: variants matching `pref`,
    then the plain catalog, then the rest in page order."""
    m = _mapping(cfg, make, model, year)
    mk = m.make or slug(make)
    slugs = m.slugs if isinstance(m.slugs, list) else [m.slugs or slug(model)]
    cats: list[tuple[str, str]] = []
    pages_ok = 0
    for md in slugs:
        d = get(absolute(cfg.site, f"/{mk}-{md}-parts.html"))
        if d.get("status") != 200:
            continue
        pages_ok += 1
        pat = re.compile(r'href="(/%d-%s-%s(?:-([a-z0-9_]+))?-parts\.html)"' % (year, re.escape(mk), re.escape(md)))
        for mm in pat.finditer(d["html"]):
            c = (mm.group(2) or "", absolute(cfg.site, mm.group(1)))
            if c not in cats:
                cats.append(c)
    if not pages_ok:
        raise ValueError(f"no model page for {make} {model} ({mk}-{slugs})")
    if not cats:
        raise ValueError(f"no {year} catalog for {make} {model} ({mk}-{slugs})")
    if m.inc:
        cats = [c for c in cats if re.search(m.inc, c[0], re.I)]
    else:
        if not re.search(r"hybrid|electric|\bev\b", model, re.I):
            cats = [c for c in cats if not re.search(DEFAULT_VARIANT_EXCLUDE, c[0], re.I)]
    if m.exc:
        cats = [c for c in cats if not re.search(m.exc, c[0], re.I)]
    if not cats:
        raise ValueError(f"every {year} catalog excluded for {make} {model}")
    def rank(c):
        if m.pref and re.search(m.pref, c[0], re.I):
            return 0
        return 1 if c[0] == "" else 2
    cats = sorted(cats, key=rank)  # stable: page order within a rank
    return cats[:MAX_CATALOGS]


def parts_list_links(cfg: Config, catalog_url: str, ctx: tuple | None = None) -> list[str]:
    """Parts-list URLs on a year catalog. When the catalog is split into
    option catalogs (no parts-list links, only /<year>-...--<option>-parts.html
    links: per trim on Honda-family sites, per engine/transmission on Ford,
    e.g. /2001-ford-f_150--6_cyl_4_2l-4at_4r100-parts.html), the first and
    last option catalogs in page order are used (on trim lists: base and
    best-equipped; on Ford engine lists: smallest and largest engine)."""
    html = _page(catalog_url)["html"]
    base = urllib.parse.urlsplit(catalog_url).path[: -len("-parts.html")].lstrip("/")
    L = sorted(set(re.findall(r'href="(/parts-list/%s/[a-z0-9_]+/[a-z0-9_]+\.html)"' % re.escape(base), html)))
    if L:
        return [absolute(cfg.site, u) for u in L]
    trims = []
    for u in re.findall(r'href="(/%s--[a-z0-9_-]+-parts\.html)"' % re.escape(base), html):
        if u not in trims:
            trims.append(u)
    if not trims:
        raise ValueError(f"no parts-list or trim links on {catalog_url}")
    pick = [trims[0]] + ([trims[-1]] if len(trims) > 1 else [])
    if cfg.trim_pick and ctx:
        pre = "/%s--" % base
        slugs = cfg.trim_pick(*ctx, [u[len(pre):-len("-parts.html")] for u in trims])
        pick = [f"{pre}{t}-parts.html" for t in slugs]
        if not pick:
            raise ValueError(f"trim_pick chose no trim on {catalog_url}")
    out: list[str] = []
    for t in pick:
        out += parts_list_links(cfg, absolute(cfg.site, t), ctx)
    return out


def categories_for(cfg: Config, make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
    links: list[str] = []
    for _variant, url in year_catalogs(cfg, make, model, year):
        links += [u for u in parts_list_links(cfg, url, (make, model, year)) if u not in links]
    out: dict[str, list[str]] = {}
    for cat in cats:
        rx = cfg.subcats.get(cat)
        if not rx:
            continue
        ex = cfg.subcat_excl.get(cat)
        sel = []
        for u in links:
            tail = urllib.parse.urlsplit(u).path.split("/")[-1][: -len(".html")]
            if SUBCAT_COMMON_EXCLUDE.search(tail):
                continue
            if re.search(rx, tail, re.I) and not (ex and re.search(ex, tail, re.I)):
                sel.append(u)
        if sel:
            out[cat] = sel
    return out


# ---------------------------------------------------------------- list page

def _clean(t) -> str:
    t = re.sub(r"<br\s*/?>", " / ", str(t or ""), flags=re.I)
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", t))).strip()


def _info(x: dict) -> str:
    name, desc = _clean(x.get("name")), _clean(x.get("desc"))
    return f"{name}: {desc}" if name else desc


def list_parts(html: str) -> list[dict]:
    """Every main part row on a parts-list page (the 'Standard Parts'
    hardware block, expandPartList, is not read)."""
    pl = store(html)["partList"]
    rows = []
    for group in pl.get("partList") or []:
        for p in group:
            rows.append({
                "pn": p.get("partNumber") or "",
                "main": _clean(p.get("mainDesc")),
                "group": _clean(p.get("pncDesc")),
                "remark": _clean(p.get("mainDescAlter")),
                "info": [_info(x) for x in (p.get("allExtraInfoList") or [])],
                "url": p.get("url") or "",
            })
    return rows


REMAN_RE = re.compile(r"\b(REMANUFACTURED|REMAN|REFURBISHED|RECONDITIONED|REBUILT)\b|Core Return", re.I)
LOCATION_RE = re.compile(r"^Location:", re.I)

# pn -> position text printed on the list page (filled by parts_on_page and
# read by product(), which crawl.py calls right after for the same pn).
_LIST_POSITION: dict[str, tuple[str, str]] = {}


def _side(text: str) -> str | None:
    """L / R for a printed side, None when the text names no side."""
    if re.search(r"\b(Left|LH|Driver)\b", text, re.I) and not re.search(r"\b(Right|RH|Passenger)\b", text, re.I):
        return "L"
    if re.search(r"\b(Right|RH|Passenger)\b", text, re.I) and not re.search(r"\b(Left|LH|Driver)\b", text, re.I):
        return "R"
    return None


def _list_position(info: list[str]) -> str | None:
    for x in info:
        if LOCATION_RE.match(x):
            return x
    for x in info:  # nameless entry such as "Right [GTS], [JP5]" (Mopar)
        if ":" not in x.split(" ")[0]:
            m = re.match(r"^(?:Left|Right|LH|RH|Front|Rear)\b(?:[ -](?:Bank|Side|Hand|Front|Rear|Upper|Lower|Inner|Outer)\b)*", x, re.I)
            if m:
                return m.group(0)  # verbatim: "Right", "RIGHT BANK"
    return None


def parts_on_page(cfg: Config, list_url: str, cat: str) -> list[dict]:
    """Parts on the page for `cat`. Matching text is
    "<group> | <name> | <remark> | <info; info>"; COMMON_EXCLUDE looks at
    group and name only. Remanufactured/refurbished rows are dropped when the
    page also has a new part for this category, kept otherwise."""
    rule = cfg.parts[cat]
    html = _page(list_url)["html"]
    kept = []
    for r in list_parts(html):
        if not r["pn"] or not r["url"]:
            continue
        info = "; ".join(r["info"])
        text = f"{r['group']} | {r['main']} | {r['remark']} | {info}"
        if callable(rule):
            if not rule(r, text):
                continue
        else:
            inc, exc_head, exc_full = (tuple(rule) + (None, None))[:3]
            head = cfg.head_fn(r) if cfg.head_fn else f"{r['group']} | {r['main']} | {r['remark'].split('(')[0]}"
            if not re.search(inc, text, re.I):
                continue
            if exc_head and re.search(exc_head, head, re.I):
                continue
            if exc_full and re.search(exc_full, text, re.I):
                continue
        if COMMON_EXCLUDE.search(cfg.head_fn(r) if cfg.head_fn else f"{r['group']} | {r['main']}"):
            continue
        kept.append((r, bool(REMAN_RE.search(text)) or bool(cfg.reman_re and re.search(cfg.reman_re, text, re.I))
                     or bool(cfg.reman_fn and cfg.reman_fn(r))))
    if any(not reman for _, reman in kept):
        kept = [k for k in kept if not k[1]]
    out, seen = [], set()
    for r, _ in kept:
        if r["pn"] in seen:
            continue
        seen.add(r["pn"])
        pos = _list_position(r["info"])
        if pos:
            _LIST_POSITION[r["pn"]] = (pos, list_url)
        name = r["main"] + (f", {r['remark']}" if r["remark"] else "")
        out.append({"pn": r["pn"], "name": name, "product_url": absolute(cfg.site, r["url"]),
                    "list_group": r["group"], "list_remark": r["remark"], "list_info": r["info"]})
    return out


# ---------------------------------------------------------------- product

# "2010-2015 Buick Allure", "2012 Chevrolet Malibu", and non-contiguous year
# lists such as "2002, 1999-2000 Chevrolet Silverado".
YEARS_RE = re.compile(r"^((?:\d{4}(?:\s*-\s*\d{4})?)(?:\s*,\s*\d{4}(?:\s*-\s*\d{4})?)*)\s+(\S+)\s+(.+)$")
ENGINE_RE = re.compile(r"^(\d+ Cyl\b|\d\.\dL\b|Electric\b|Rotary\b)", re.I)
SPAN_RE = re.compile(r"(\d{4})(?:\s*-\s*(\d{4}))?")


def _split(cell: str) -> list[str]:
    cell = (cell or "").strip()
    return [x.strip() for x in cell.split(", ") if x.strip()] if cell else []


def _html_rows(html: str) -> list[list[str]]:
    i = html.find('class="fit-vehicle-list-table"')
    if i < 0:
        return []
    e = html.find("</table>", i)
    body = html[i:e]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if tds:
            rows.append([htmllib.unescape(re.sub(r"<[^>]+>", "", t)).strip() for t in tds])
    return rows


def _find(o, key):
    """First value stored under `key` anywhere in a JSON tree."""
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = _find(v, key)
            if r is not None:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find(v, key)
            if r is not None:
                return r
    return None


def product(cfg: Config, product_url: str) -> dict:
    d = _page(product_url)
    html = d["html"]
    st = store(html)
    pnode = st.get("partNumber") or {}
    info = pnode.get("partInfo") or _find(pnode, "partInfo")
    if not info or not info.get("partNumber"):
        raise ValueError("no partInfo in store")
    titles = [t.get("text", "").strip() for t in (_find(pnode, "fitVehicleTitleList") or [])]
    rows = _find(pnode, "fitVehicleList") or []
    rows = [[(c or "").strip() for c in r] for r in rows]
    shown = _html_rows(html)
    if shown and rows[: len(shown)] != shown:
        raise ValueError("rendered fitment table differs from page store")
    if not rows and shown:
        rows = shown

    def col(name_rx):
        for k, t in enumerate(titles):
            if re.search(name_rx, t, re.I):
                return k
        return None
    c_ymm = col(r"year") if titles else 0
    c_te = col(r"trim\s*&\s*engine")
    c_eng = None if c_te is not None else col(r"engine")
    c_trim = None if c_te is not None else col(cfg.trim_col or r"^trim")
    c_opt = col(cfg.option_col)
    if c_ymm is None:
        raise ValueError(f"unexpected fitment header {titles}")

    fitment = []
    for r in rows:
        m = YEARS_RE.match(r[c_ymm])
        if not m:
            raise ValueError(f"unparsed fitment cell {r[c_ymm]!r}")
        spans = [(int(a), int(b or a)) for a, b in SPAN_RE.findall(m.group(1))]
        cell = lambda c: r[c] if c is not None and c < len(r) else ""
        options = _split(cell(c_opt))
        if c_te is not None:  # "Base, S|4 Cyl 2.5L" (Nissan family)
            te = cell(c_te)
            if "|" in te:
                t, _, e = te.partition("|")
                trims, engines = _split(t), _split(e)
            elif te and all(ENGINE_RE.match(x) for x in _split(te)):
                trims, engines = [], _split(te)  # "6 Cyl 3.5L": engine only
            else:
                trims, engines = _split(te), []
        else:
            trims, engines = _split(cell(c_trim)), _split(cell(c_eng))
            if not trims and cfg.option_column_is_trims:
                trims = options
        for lo, hi in spans:  # one row per printed span; raw is the whole row
            fitment.append({
                "years": [lo, hi], "make": m.group(2), "model": m.group(3).strip(),
                "trims": trims, "engines": engines, "options": options,
                "raw": " | ".join(r),
            })

    desc = (info.get("partDescription") or "").strip() or " ; ".join(
        x for x in [(info.get("mainDesc") or "").strip(), (info.get("subDesc") or "").strip()] if x)
    lr = (info.get("lr") or "").strip()
    pn = info.get("partNumber")
    listed = _LIST_POSITION.get(pn)
    # Only a side the site states as a position counts; words inside the
    # description ("O/S REAR VIEW") are not a position. The parts-list row is
    # the catalog's own line for this pn, so it wins over the product page's
    # "lr"; when the two name opposite sides the record gets no position and a
    # flag (seen on Mopar: list "Right", product page "Driver Side").
    flags = []
    position = (listed[0] if listed else None) or lr or None
    if listed and lr and _side(listed[0]) and _side(lr) and _side(listed[0]) != _side(lr):
        flags.append(f"position conflict: parts list says {listed[0]!r}, product page says {lr!r}")
        position = None
    replaced_by = (info.get("replacedBy") or "").strip() or None
    replaces = [x.strip() for x in re.split(r"[,;]", info.get("replaces") or "") if x.strip()]
    notes = [(info.get(k) or "").strip() for k in ("notes", "comment", "applyTo", "extraInfo") if isinstance(info.get(k), str)]
    notes = [n for n in notes if n]

    ev = [f"Part Number: {info.get('partNumber')}", f"Part Description: {desc}"]
    if lr:
        ev.append(f"Position: {lr}")
    if listed:
        ev.append(f"Parts list {listed[1]}: {listed[0]}")
    if replaced_by:
        ev.append(f"Replaced By: {replaced_by}")
    if info.get("replaces"):
        ev.append(f"Replaces: {info.get('replaces').strip()}")
    ev += [f"Notes: {n}" for n in notes]
    if titles:
        ev.append(" | ".join(titles))
    ev += [" | ".join(r) for r in rows]
    if len(ev) > EVIDENCE_CAP:
        flags.append(f"evidence truncated at {EVIDENCE_CAP} lines ({len(fitment)} fitment rows)")
    if not fitment:
        flags.append("no fitment rows on page")
    return {
        "pn": info.get("partNumber"),
        "description": desc,
        "position": position,
        "replaces": replaces,
        "replaced_by": replaced_by,
        "fitment": fitment,
        "evidence_lines": ev[:EVIDENCE_CAP],
        "flags": flags,
        "retrieved": d.get("retrieved"),
    }


def bind(cfg: Config):
    """The three contract functions for a site module."""
    return (lambda make, model, year, cats: categories_for(cfg, make, model, year, cats),
            lambda list_url, cat: parts_on_page(cfg, list_url, cat),
            lambda product_url: product(cfg, product_url))
