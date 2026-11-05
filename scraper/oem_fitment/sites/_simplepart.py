"""Shared navigator/parser for the SimplePart dealer-catalog template
(www.toyotapartsnow.com, www.jeeppartsdeal.com).

Template facts (learned through fetch.py, 2026-11-05):
  * model page   /<make>-<model>-parts            (links /catalog/<year>-<make>-<model>-parts)
  * year page    /catalog/<year>-<make>-<model>-parts
                 links /parts-list/<year>-<make>-<model>/<group>/<subcategory>
  * list page    /parts-list/...  server-rendered; the same data sits in
                 window.__INITIAL_STORE__ -> partList.partList (diagram parts,
                 groups of rows) and partList.gpgOnlyPartList (catalog rows not
                 on a diagram, often superseded numbers). Rows: partNumber,
                 mainDesc, auxiliaryDesc, allExtraInfoList (Part Notes,
                 Location, ...), replace, url (/oem/<make>~<slug>~<pn>).
  * product page /oem/<make>~<slug>~<pn>; __INITIAL_STORE__.partNumber holds
                 partInfo (partNumber, mainDesc, lr/Position, replaces,
                 replacedBy) and the "Vehicle Fitment" table:
                 fitVehicleTitleList (column headers, e.g. "Year Make Model",
                 "Trim", "Engine" or "Year Make Model", "Engine",
                 "Important vehicle option details") and fitVehicleList (rows of
                 cells, cell 0 like "2007-2017 Jeep Compass").
  * pages carry a /login/honeypot.html link: we never follow links blindly;
    only /catalog/, /parts-list/ and /oem/ URLs built from the patterns above.

The structured fields come from the JSON store; evidence_lines come from the
rendered page text (fetch.text_lines) and every JSON fitment cell is checked
against that text. Any disagreement is recorded in `flags`, never smoothed over.

Manifests (CURATION_SPEC.md §3.2 R1/R2), read back from the cached fetch with
cached(), never a new request:
  * list_manifest(list_url, cat): every row of partList ("diagram") and
    gpgOnlyPartList ("other") with the template's verdict for `cat`
    (matched / excluded_by), the row's notes verbatim as `extra`, its
    `replace` and URL;
  * year_manifest(make, model, year): the year page's status, final URL,
    title and every "<group>/<sub>" parts-list slug;
  * chain_links(product_url, pns): product-page links to those part numbers
    (R4; replaced numbers are usually not linked, so this is often empty).
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch  # noqa: E402
from fetch import get, text_lines  # noqa: E402

from ._qualifier import QUALIFIER, strip_qualifiers  # noqa: E402,F401  (QUALIFIER re-exported)

EVIDENCE_CAP = 120
TWO_WORD_MAKES = ("Alfa Romeo", "Land Rover", "Aston Martin", "Rolls Royce", "Rolls-Royce")

# README "exclude from every category": applied to both printed names.
GLOBAL_EXCLUDE = re.compile(
    r"\b(bulbs?|sockets?|gaskets?|bolts?|screws?|nuts?|clips?|brackets?|seals?|wires?|wiring|harness|"
    r"labels?|decals?|grommets?|retainers?|washers?|o-rings?|rivets?|studs?|pins?|spacers?|"
    r"plugs?|clamps?|fasteners?|tapes?|stickers?)\b", re.I)
# "with X" / "w/X" / "less X" / "l/X" qualifier phrases describe what an
# assembly includes; the whole phrase (to the next "," or ";") is removed
# before the exclusion checks ("Compressor Assy, With Pulley",
# "Mirror Assy, Outer Rear View, W/Turn Signal Lamp"): sites/_qualifier.py.
REMAN = re.compile(r"\breman", re.I)


def cached(url: str) -> dict | None:
    """The cached response for url, or None. Never a network request: the
    manifests re-read pages that navigation and parts_on_page just fetched."""
    if not fetch.cache_path(url).exists():
        return None
    return get(url)


def norm_pn(pn: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (pn or "").lower())


def _title(html: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.S | re.I)
    return _clean(m.group(1)) if m else None


class NavError(Exception):
    pass


# ---------------------------------------------------------------- page data

def _strip_undefined(js: str) -> str:
    """The store is a JS literal: JSON plus bare `undefined`. Replace
    `undefined` tokens that sit outside strings with null."""
    out, i, n, in_str = [], 0, len(js), False
    while i < n:
        c = js[i]
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(js[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if js.startswith("undefined", i) and not (js[i - 1].isalnum() if i else False):
            out.append("null")
            i += 9
            continue
        out.append(c)
        i += 1
    return "".join(out)


def store(html: str) -> dict:
    m = re.search(r"window\.__INITIAL_STORE__\s*=\s*(\{.*?)\s*</script>", html, re.S)
    if not m:
        raise NavError("no __INITIAL_STORE__ on page")
    raw = m.group(1).strip().rstrip(";")
    return json.loads(_strip_undefined(raw))


def _clean(s) -> str:
    if s is None:
        return ""
    s = htmllib.unescape(re.sub(r"<[^>]+>", " ", str(s)))
    return re.sub(r"\s+", " ", s).strip()


def split_list(s: str) -> list[str]:
    """Split a printed comma list, keeping commas inside parentheses
    ("Base (4WD, FWD), Latitude (4WD, FWD)" -> 2 items)."""
    s = _clean(s)
    if not s:
        return []
    out, depth, cur = [], 0, []
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur).strip())
    return [x for x in out if x]


def _extra(row: dict, name: str) -> str:
    vals = [_clean(e.get("desc")) for e in (row.get("allExtraInfoList") or []) if e.get("name") == name]
    return "; ".join(v for v in vals if v)


def _list_stem(list_url: str) -> str | None:
    """"<year>-<make>-<model>" from /parts-list/<stem>/<group>/<sub>."""
    parts = urllib.parse.urlsplit(list_url).path.split("/")
    return parts[2] if len(parts) > 2 and parts[1] == "parts-list" else None


# ---------------------------------------------------------------- the template

class SimplePart:
    def __init__(self, site: str, url_make: dict[str, str], model_slugs: dict[tuple[str, str], str],
                 cat_pages: dict[str, str], rules: dict[str, tuple[str, str]], oem_name_field: str,
                 year_path: str = "/catalog/{year}-{make}-{model}-parts",
                 product_prefixes: tuple[str, ...] = ("/oem/",),
                 category_notes: dict[str, str] | None = None,
                 product_rules: dict[str, str] | None = None,
                 slug_checks: bool = False,
                 reman_pn: str | None = None):
        """
        site:           domain
        url_make:       feed make -> make token in catalog URLs ("Scion" -> "scion")
        model_slugs:    (feed make, feed model) -> catalog model slug; others slugify
        cat_pages:      our category -> regex on "<group>/<subcategory>" slugs of the year page
        rules:          our category -> (include regex, exclude regex) on the part's printed names
        oem_name_field: "aux" when auxiliaryDesc holds the OEM name (Toyota), "main" when mainDesc does (Mopar)
        year_path:      year-page path; parts-list stem is always "<year>-<make>-<model>"
                        (toyotapartsnow/jeeppartsdeal: /catalog/...; vwpartsgiant & co: /<year>-...-parts)
        product_prefixes: product path prefixes ("/oem/" or "/genuine/")
        category_notes: our category -> caveat copied onto every part record of
                        that category (`category_note`), for curators
        product_rules:  our category -> regex the product page must match, on
                        "<description> | <other_names> | Position: <position>",
                        for facts the list page does not print (front vs rear
                        door, driver vs passenger switch). The matched text is
                        kept in `product_check`.
        slug_checks:    also apply the exclusions and the reman test to the product URL's
                        name slug (/genuine/<make>~<name-slug>~<pn>), for stores whose list
                        names are loose (mitsubishipartsgiant lists bolt 7812A133 as
                        "Dehydrator", slug bolt-a-c-condenser; reman M1810A001D as "Starter",
                        slug remanufactured-starter). Subclasses may also check `slug` in
                        excluded_by() (match() is excluded_by() is None).
        reman_pn:       regex on the part number for the make's own reman numbering, OR-ed
                        with the name test (Toyota "-84": 27060-28320 -> 27060-28321-84)
        """
        self.site = site
        self.base = f"https://{site}"
        self.url_make = url_make
        self.model_slugs = model_slugs
        self.cat_pages = {k: re.compile(v) for k, v in cat_pages.items()}
        self.rules = {k: (re.compile(a, re.I), re.compile(b, re.I) if b else None) for k, (a, b) in rules.items()}
        self.oem_name_field = oem_name_field
        self.year_path = year_path
        self.product_prefixes = tuple(product_prefixes)
        self.category_notes = dict(category_notes or {})
        self.product_rules = {k: re.compile(v, re.I) for k, v in (product_rules or {}).items()}
        self.slug_checks = slug_checks
        self.reman_pn = re.compile(reman_pn, re.I) if reman_pn else None

    # ---- navigation
    def slug(self, make: str, model: str, year: int | None = None) -> str:
        """model_slugs values: a slug; a list of (first_year, last_year, slug)
        when the catalog splits a feed model by year; or None when the feed
        model does not name one catalog model (navigation then fails)."""
        if (make, model) in self.model_slugs:
            s = self.model_slugs[(make, model)]
            if s is None:
                raise NavError(f"{make} {model}: no single catalog model for this feed name")
            if isinstance(s, list):
                for lo, hi, sl in s:
                    if year is not None and lo <= year <= hi:
                        return sl
                raise NavError(f"{make} {model} {year}: no catalog model for this year")
            return s
        return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")

    def stem(self, make: str, model: str, year: int) -> str:
        return f"{year}-{self.url_make.get(make, make.lower())}-{self.slug(make, model, year)}"

    def year_url(self, make: str, model: str, year: int) -> str:
        mk = self.url_make.get(make, make.lower())
        return self.base + self.year_path.format(year=year, make=mk, model=self.slug(make, model, year))

    def categories_for(self, make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
        return self.categories_for_slug(make, self.slug(make, model, year), year, cats)

    def categories_for_slug(self, make: str, slug: str, year: int, cats: list[str]) -> dict[str, list[str]]:
        mk = self.url_make.get(make, make.lower())
        url = self.base + self.year_path.format(year=year, make=mk, model=slug)
        d = get(url)
        if d.get("status") != 200:
            raise NavError(f"HTTP {d.get('status')} for {url}")
        if urllib.parse.urlsplit(d.get("final_url") or url).path != urllib.parse.urlsplit(url).path:
            raise NavError(f"{url} redirected to {d.get('final_url')}")
        stem = f"{year}-{mk}-{slug}"
        subs = sorted(set(re.findall(r'href="/parts-list/' + re.escape(stem) + r'/([a-z0-9-]+/[a-z0-9-]+)"', d["html"])))
        if not subs:
            raise NavError(f"no parts-list links on {url}")
        out: dict[str, list[str]] = {}
        for cat in cats:
            rx = self.cat_pages.get(cat)
            if rx is None:
                continue
            urls = [f"{self.base}/parts-list/{stem}/{s}" for s in subs if rx.search(s)]
            if urls:
                out[cat] = urls
        return out

    def year_manifest(self, make: str, model: str, year: int) -> list[dict]:
        """R2: what the year page offers, re-read from the cache. One line;
        SimplePart has one catalog per model-year (variant "")."""
        line: dict = {"variant": "", "trim": None, "year_url": None, "catalog": None, "status": None,
                      "final_url": None, "redirected": None, "title": None, "subs": [],
                      "variants": [""], "variants_read": [""], "retrieved": None}
        try:
            slug = self.slug(make, model, year)
        except NavError as e:
            line["error"] = str(e)
            return [line]
        mk = self.url_make.get(make, make.lower())
        url = self.base + self.year_path.format(year=year, make=mk, model=slug)
        stem = f"{year}-{mk}-{slug}"
        line.update(year_url=url, catalog=stem)
        d = cached(url)
        if d is None:
            line["error"] = "not_fetched"
            return [line]
        final = d.get("final_url") or url
        line.update(status=d.get("status"), final_url=final, retrieved=d.get("retrieved"),
                    redirected=urllib.parse.urlsplit(final).path != urllib.parse.urlsplit(url).path,
                    title=_title(d.get("html", "")))
        line["subs"] = sorted(set(re.findall(r'href="/parts-list/' + re.escape(stem) + r'/([a-z0-9-]+/[a-z0-9-]+)"',
                                             d.get("html", ""))))
        try:
            vo = store(d.get("html", "")).get("vehicleOption") or {}
        except (NavError, ValueError):
            vo = {}
        if vo.get("optionList") or vo.get("optionNavList"):
            line["vehicle_options"] = vo  # verbatim: multi-trim years ask the shopper to pick options
        if line["status"] != 200:
            line["error"] = f"HTTP {line['status']}"
        elif line["redirected"]:
            line["error"] = "redirected"
        elif not line["subs"]:
            line["error"] = "no parts-list links"
        return [line]

    # ---- list pages
    def oem_name(self, main: str, aux: str) -> str:
        if self.oem_name_field == "aux" and aux:
            return aux
        return main or aux

    def excluded_by(self, cat: str, main: str, aux: str, slug: str = "") -> str | None:
        """None when the row belongs to `cat`, else why not (manifest
        `excluded_by`): "include_miss", "global:<word>" (README exclusions)
        or "rule:<word>" (the category's exclusions). Exclusions read the
        names with qualifier phrases removed (R5a)."""
        inc, exc = self.rules[cat]
        name = self.oem_name(main, aux)
        if not inc.search(name):
            return "include_miss"
        for s in (main, aux, slug.replace("-", " ") if self.slug_checks else ""):
            t = strip_qualifiers(s)
            m = GLOBAL_EXCLUDE.search(t)
            if m:
                return f"global:{m.group(0).lower()}"
            m = exc.search(t) if exc else None
            if m:
                return f"rule:{m.group(0).lower()}"
        return None

    def match(self, cat: str, main: str, aux: str, slug: str = "") -> bool:
        return self.excluded_by(cat, main, aux, slug) is None

    def is_reman(self, pn: str, main: str, aux: str, notes: str, name_slug: str) -> bool:
        """One list row says remanufactured: its names or notes say "reman",
        the number is R-prefixed (Mopar), or the site's reman_pn matches."""
        return (bool(REMAN.search(" ".join([main, aux, notes, name_slug if self.slug_checks else ""])))
                or bool(re.match(r"^R\d", pn)) or bool(self.reman_pn and self.reman_pn.search(pn)))

    def _scan(self, d: dict, cat: str, product_fn) -> tuple[list[dict], list[dict]]:
        """(parts, manifest rows) for one fetched list page. parts is what
        parts_on_page returns; rows is every partList / gpgOnlyPartList row with
        the verdict for `cat`. product_fn(url) -> product dict or None (None:
        the page is not available, the product rule is left unchecked)."""
        pl = store(d["html"]).get("partList") or {}
        src = [(r, "diagram") for g in (pl.get("partList") or []) for r in (g or [])]
        src += [(r, "other") for g in (pl.get("gpgOnlyPartList") or []) for r in (g or [])]
        found: dict[str, dict] = {}
        rows: list[dict] = []
        new_number: set[str] = set()  # pns with a non-reman diagram row and no replace value (R5b)
        for r, section in src:
            pn = _clean(r.get("partNumber"))
            url = r.get("url") or ""
            main, aux = _clean(r.get("mainDesc")), _clean(r.get("auxiliaryDesc"))
            replace = _clean(r.get("replace"))
            row = {"pn": pn or None, "section": section, "main": main, "aux": aux or None,
                   "extra": [{"name": _clean(e.get("name")), "desc": _clean(e.get("desc"))}
                             for e in (r.get("allExtraInfoList") or [])],
                   "replace": replace or None, "url": url or None,
                   "reman": False, "matched": False, "excluded_by": None}
            rows.append(row)
            if not pn:
                row["excluded_by"] = "no_pn"
                continue
            name_slug = url.split("~")[1] if url.count("~") >= 2 else ""
            notes = _extra(r, "Part Notes")
            row_reman = self.is_reman(pn, main, aux, notes, name_slug)
            row["reman"] = row_reman
            if not url.startswith(self.product_prefixes):
                row["excluded_by"] = "no_product_url"
                continue
            # the URL must name the same part number (honest link, not a redirect/ad)
            if url.rsplit("~", 1)[-1].replace("-", "").lower() != pn.replace("-", "").lower():
                row["excluded_by"] = "url_pn_mismatch"
                continue
            if not self.match(cat, main, aux, name_slug):
                row["excluded_by"] = self.excluded_by(cat, main, aux, name_slug) or "rule:site"
                continue
            row["matched"] = True
            if section == "diagram" and not replace and not row_reman:
                new_number.add(pn)
            rec = found.get(pn)
            if rec is None:
                rec = found[pn] = {
                    "pn": pn, "name": main, "aux_desc": aux or None,
                    "product_url": self.base + url,
                    "list_section": section,
                    "list_notes": [], "list_location": [],
                    "list_replaced_by": replace or None,
                    "reman": True,  # AND over this number's rows, below
                }
            # a number is reman only if every row listing it says so (VW prints
            # one X-number on a "New" row and on a "Remanufactured" row)
            rec["reman"] = rec["reman"] and row_reman
            if notes and notes not in rec["list_notes"]:
                rec["list_notes"].append(notes)
            loc = _extra(r, "Location")
            if loc and loc not in rec["list_location"]:
                rec["list_location"].append(loc)

        def unmatch(pns: set[str], why: str) -> None:
            for row in rows:
                if row["matched"] and row["pn"] in pns:
                    row["matched"], row["excluded_by"] = False, why

        parts = list(found.values())
        if cat in self.product_rules:
            kept = []
            for p in parts:
                pr = product_fn(p["product_url"])
                if pr is None:
                    unmatch({p["pn"]}, "product_rule_unchecked")
                    continue
                text = f"{pr['description']} | {pr['other_names'] or ''} | Position: {pr['position'] or ''}"
                m = self.product_rules[cat].search(text)
                if m:
                    p["product_check"] = f"{m.group(0)!r} in {text!r}"
                    kept.append(p)
                else:
                    unmatch({p["pn"]}, "product_rule")
            parts = kept
        if cat in self.category_notes:
            for p in parts:
                p["category_note"] = self.category_notes[cat]
        # README: drop remanufactured numbers when a new number for the same
        # category is on the page; keep reman when it is the only listing.
        # R5b: only a non-reman "diagram" row without a replace value is a new
        # number. A superseded or catalog-only number ("other" section,
        # 27060-28320 -> 27060-28321-84) is not, so remans stay next to it.
        if any(p["pn"] in new_number for p in parts) and any(p["reman"] for p in parts):
            unmatch({p["pn"] for p in parts if p["reman"]}, "reman_dropped")
            parts = [p for p in parts if not p["reman"]]
        return parts, rows

    def parts_on_page(self, list_url: str, cat: str) -> list[dict]:
        if cat not in self.rules:
            return []
        d = get(list_url)
        if d.get("status") != 200:
            raise NavError(f"HTTP {d.get('status')} for {list_url}")
        return self._scan(d, cat, self.product)[0]

    def list_manifest(self, list_url: str, cat: str) -> dict:
        """R1: every row of the list page with the verdict for `cat`, re-read
        from the cache (no request). `product` per row is filled by crawl.py."""
        out: dict = {"list_url": list_url, "catalog": _list_stem(list_url), "variant": "", "status": None,
                     "final_url": None, "retrieved": None, "rows": []}
        if cat not in self.rules:
            out["error"] = "no rules for this category"
            return out
        d = cached(list_url)
        if d is None:
            out["error"] = "not_fetched"
            return out
        out.update(status=d.get("status"), final_url=d.get("final_url") or list_url, retrieved=d.get("retrieved"))
        if d.get("status") != 200:
            out["error"] = f"HTTP {d.get('status')}"
            return out

        def cached_product(url: str):
            try:
                return self.product(url, _get=cached)
            except NavError:
                return None
        try:
            out["rows"] = self._scan(d, cat, cached_product)[1]
        except NavError as e:
            out["error"] = str(e)
        return out

    def chain_links(self, product_url: str, pns: list[str]) -> dict[str, str]:
        """R4: {pn: product URL} for the numbers in `pns` that the product page
        itself links (/oem/... or /genuine/... hrefs whose last "~" part is the
        number). Read from the cache; never a constructed slug."""
        d = cached(product_url)
        if not d:
            return {}
        want = {norm_pn(p): p for p in pns if norm_pn(p)}
        out: dict[str, str] = {}
        for href in re.findall(r'href="([^"#?]+)"', d.get("html", "")):
            if not href.startswith(self.product_prefixes) or href.count("~") < 2:
                continue
            k = norm_pn(href.rsplit("~", 1)[-1])
            if k in want and want[k] not in out:
                out[want[k]] = self.base + href
        return out

    # ---- product pages
    @staticmethod
    def parse_ymm(cell: str) -> dict | None:
        """"2019-2025 Toyota RAV4" -> years [2019, 2025]. The catalog also prints
        several spans in one cell ("2011-2016, 2007-2008 Scion tC",
        "2014, 2010-2011, 2008 Jeep Compass"): `spans` keeps them all, in
        printed order; `years` is the first span."""
        m = re.match(r"^(\d{4}(?:\s*-\s*\d{4})?(?:\s*,\s*\d{4}(?:\s*-\s*\d{4})?)*)\s+(\D.*)$", cell)
        if not m:
            return None
        spans = []
        for part in m.group(1).split(","):
            ys = [int(y) for y in re.findall(r"\d{4}", part)]
            spans.append([ys[0], ys[-1]])
        rest = m.group(2).strip()
        make = next((mk for mk in TWO_WORD_MAKES if rest.startswith(mk + " ")), None) or rest.split(" ", 1)[0]
        model = rest[len(make):].strip()
        return {"years": spans[0], "spans": spans, "make": make, "model": model}

    def product(self, product_url: str, _get=None) -> dict:
        d = (_get or get)(product_url)
        if d is None:
            raise NavError(f"not in cache: {product_url}")
        if d.get("status") != 200:
            raise NavError(f"HTTP {d.get('status')} for {product_url}")
        st = store(d["html"]).get("partNumber") or {}
        info = st.get("partInfo") or {}
        pn = _clean(info.get("partNumber"))
        if not pn:
            raise NavError(f"no part number on {product_url}")
        flags: list[str] = []
        url_pn = product_url.rsplit("~", 1)[-1]
        if url_pn.replace("-", "").lower() != pn.replace("-", "").lower():
            flags.append(f"pn_differs_from_url:{url_pn}")

        base_info = {_clean(b.get("name")): _clean(b.get("desc")) for b in (info.get("baseInfoList") or [])}
        position = base_info.get("Position") or _clean(info.get("lr")) or None
        replaces = split_list(info.get("replaces") or base_info.get("Replaces") or "")
        replaced_by = split_list(info.get("replacedBy") or base_info.get("Replaced By") or "")

        headers = [_clean(t.get("text")) for t in (st.get("fitVehicleTitleList") or [])]
        fitment = []
        for row in st.get("fitVehicleList") or []:
            cells = [_clean(c) for c in row]
            col = dict(zip(headers, cells))
            ymm = self.parse_ymm(col.get("Year Make Model", cells[0] if cells else ""))
            raw = " | ".join(cells)
            if not ymm:
                flags.append(f"unparsed_fitment_row:{raw}")
                continue
            spans = ymm.pop("spans")
            base = {**ymm,
                    "trims": split_list(col.get("Trim", "")),
                    "engines": split_list(col.get("Engine", "")),
                    "raw": raw}
            other = {h: v for h, v in col.items() if h not in ("Year Make Model", "Trim", "Engine")}
            if other:
                base["other_columns"] = other  # e.g. "Important vehicle option details"
            # one entry per printed year span (contract: years = [lo, hi]); all
            # entries of a multi-span cell share `raw` and carry `year_spans`
            for sp in spans:
                f = {**base, "years": sp}
                if len(spans) > 1:
                    f["year_spans"] = spans
                fitment.append(f)
        if not fitment:
            flags.append("no_fitment_rows")
        unknown = [h for h in headers if h not in ("Year Make Model", "Trim", "Engine", "Important vehicle option details")]
        if unknown:
            flags.append(f"unknown_fitment_columns:{unknown}")

        lines = text_lines(d["html"])
        evidence: list[str] = []
        top = lines.index("Vehicle Fitment") if "Vehicle Fitment" in lines else len(lines)
        for label in ("Position", "Replaces", "Replaced By"):
            if label in lines[:top]:
                i = lines.index(label)
                evidence += lines[i:i + 2]
        block: list[str] = []
        view_more = False
        if top < len(lines):
            for ln in lines[top:]:
                if ln in ("Warning:", "Customer Questions & Expert Answers") and block:
                    break
                if ln == "View More":
                    view_more = True
                    break
                block.append(ln)
        # The rendered table must equal the store's rows, cell for cell. Long
        # tables render the first rows then "View More"; the rest of the rows
        # are in the same page's embedded data and are appended to the
        # evidence from there (marked by `fitment_rows_rendered`).
        rows_cells = [[_clean(c) for c in row if _clean(c)] for row in (st.get("fitVehicleList") or [])]
        head = ["Vehicle Fitment"] + headers
        # compare with whitespace runs collapsed (HTML renders "2020-2022,  2012"
        # as one space); evidence_lines keep the page text as extracted
        body = [re.sub(r"\s+", " ", ln) for ln in block[len(head):]]
        flat, rendered = [], 0
        for rc in rows_cells:
            if body[len(flat):len(flat) + len(rc)] != rc:
                break
            flat += rc
            rendered += 1
        if block[:len(head)] != head or len(flat) != len(body) or (rendered < len(rows_cells) and not view_more):
            flags.append("fitment_text_differs_from_store")
        evidence += block
        if rendered < len(rows_cells) and view_more and "fitment_text_differs_from_store" not in flags:
            evidence.append("View More")
            evidence += [c for rc in rows_cells[rendered:] for c in rc]
        fitment_rendered = rendered
        if len(evidence) > EVIDENCE_CAP:
            flags.append(f"evidence_truncated:{len(evidence)}")
            evidence = evidence[:EVIDENCE_CAP]

        out = {
            "pn": pn,
            "description": _clean(info.get("mainDesc")),
            "other_names": _clean(info.get("partDescription") or info.get("subDesc")) or None,
            "position": position,
            "replaces": replaces,
            "replaced_by": replaced_by,
            "fitment": fitment,
            "evidence_lines": evidence,
            "fitment_rows_rendered": fitment_rendered,
            "fitment_rows_total": len(rows_cells),
            "retrieved": d.get("retrieved"),
        }
        if flags:
            out["flags"] = flags
        return out
