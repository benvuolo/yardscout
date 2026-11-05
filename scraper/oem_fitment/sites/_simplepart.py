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
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fetch import get, text_lines  # noqa: E402

EVIDENCE_CAP = 120
TWO_WORD_MAKES = ("Alfa Romeo", "Land Rover", "Aston Martin", "Rolls Royce", "Rolls-Royce")

# README "exclude from every category": applied to both printed names.
GLOBAL_EXCLUDE = re.compile(
    r"\b(bulbs?|sockets?|gaskets?|bolts?|screws?|nuts?|clips?|brackets?|seals?|wires?|wiring|harness|"
    r"labels?|decals?|grommets?|retainers?|washers?|o-rings?|rivets?|studs?|pins?|spacers?|"
    r"plugs?|clamps?|fasteners?|tapes?|stickers?)\b", re.I)
# "with X" / "w/X" / "less X" / "l/X" qualifiers describe what an assembly
# includes; strip them before exclusion checks ("Compressor Assy, With Pulley").
QUALIFIER = re.compile(r"\b(?:w/o|w/|l/|with(?:out)?|less|incl(?:udes|uding)?)\s*[a-z0-9]+", re.I)
REMAN = re.compile(r"\breman", re.I)


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


# ---------------------------------------------------------------- the template

class SimplePart:
    def __init__(self, site: str, url_make: dict[str, str], model_slugs: dict[tuple[str, str], str],
                 cat_pages: dict[str, str], rules: dict[str, tuple[str, str]], oem_name_field: str):
        """
        site:           domain
        url_make:       feed make -> make token in catalog URLs ("Scion" -> "scion")
        model_slugs:    (feed make, feed model) -> catalog model slug; others slugify
        cat_pages:      our category -> regex on "<group>/<subcategory>" slugs of the year page
        rules:          our category -> (include regex, exclude regex) on the part's printed names
        oem_name_field: "aux" when auxiliaryDesc holds the OEM name (Toyota), "main" when mainDesc does (Mopar)
        """
        self.site = site
        self.base = f"https://{site}"
        self.url_make = url_make
        self.model_slugs = model_slugs
        self.cat_pages = {k: re.compile(v) for k, v in cat_pages.items()}
        self.rules = {k: (re.compile(a, re.I), re.compile(b, re.I) if b else None) for k, (a, b) in rules.items()}
        self.oem_name_field = oem_name_field

    # ---- navigation
    def slug(self, make: str, model: str) -> str:
        s = self.model_slugs.get((make, model))
        return s or re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")

    def year_url(self, make: str, model: str, year: int) -> str:
        mk = self.url_make.get(make, make.lower())
        return f"{self.base}/catalog/{year}-{mk}-{self.slug(make, model)}-parts"

    def categories_for(self, make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
        url = self.year_url(make, model, year)
        d = get(url)
        if d.get("status") != 200:
            raise NavError(f"HTTP {d.get('status')} for {url}")
        if urllib.parse.urlsplit(d.get("final_url") or url).path != urllib.parse.urlsplit(url).path:
            raise NavError(f"{url} redirected to {d.get('final_url')}")
        stem = urllib.parse.urlsplit(url).path[len("/catalog/"):-len("-parts")]
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

    # ---- list pages
    def oem_name(self, main: str, aux: str) -> str:
        if self.oem_name_field == "aux" and aux:
            return aux
        return main or aux

    def match(self, cat: str, main: str, aux: str) -> bool:
        inc, exc = self.rules[cat]
        name = self.oem_name(main, aux)
        if not inc.search(name):
            return False
        for s in (main, aux):
            t = QUALIFIER.sub(" ", s or "")
            if GLOBAL_EXCLUDE.search(t) or (exc and exc.search(t)):
                return False
        return True

    def parts_on_page(self, list_url: str, cat: str) -> list[dict]:
        if cat not in self.rules:
            return []
        d = get(list_url)
        if d.get("status") != 200:
            raise NavError(f"HTTP {d.get('status')} for {list_url}")
        pl = store(d["html"]).get("partList") or {}
        rows = [(r, "diagram") for g in (pl.get("partList") or []) for r in (g or [])]
        rows += [(r, "other") for g in (pl.get("gpgOnlyPartList") or []) for r in (g or [])]
        found: dict[str, dict] = {}
        for r, section in rows:
            pn = _clean(r.get("partNumber"))
            url = r.get("url") or ""
            if not pn or not url.startswith("/oem/"):
                continue
            # the URL must name the same part number (honest link, not a redirect/ad)
            if url.rsplit("~", 1)[-1].replace("-", "").lower() != pn.replace("-", "").lower():
                continue
            main, aux = _clean(r.get("mainDesc")), _clean(r.get("auxiliaryDesc"))
            if not self.match(cat, main, aux):
                continue
            notes = _extra(r, "Part Notes")
            rec = found.get(pn)
            if rec is None:
                rec = found[pn] = {
                    "pn": pn, "name": main, "aux_desc": aux or None,
                    "product_url": self.base + url,
                    "list_section": section,
                    "list_notes": [], "list_location": [],
                    "list_replaced_by": _clean(r.get("replace")) or None,
                    "reman": bool(REMAN.search(" ".join([main, aux, notes]))) or bool(re.match(r"^R\d", pn)),
                }
            if notes and notes not in rec["list_notes"]:
                rec["list_notes"].append(notes)
            loc = _extra(r, "Location")
            if loc and loc not in rec["list_location"]:
                rec["list_location"].append(loc)
        parts = list(found.values())
        # README: drop remanufactured numbers when a new number for the same
        # category is on the page; keep reman when it is the only listing.
        if any(p["reman"] for p in parts) and any(not p["reman"] for p in parts):
            parts = [p for p in parts if not p["reman"]]
        return parts

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

    def product(self, product_url: str) -> dict:
        d = get(product_url)
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
        body = block[len(head):]
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
