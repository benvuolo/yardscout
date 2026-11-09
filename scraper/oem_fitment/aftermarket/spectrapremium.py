"""Spectra Premium e-catalog (ecat.spectrapremium.com): radiators, condensers,
A/C compressors, evaporators, heaters, fuel tanks, fuel modules, filler necks,
ignition coils, sensors, oil pans.

Probe 2026-11-09 (ops/interchange.md "Aftermarket breadth"; SOURCES.md):
robots `User-Agent: * / Disallow:` (everything allowed); no challenge on any
page we use (Google reCAPTCHA sits only on the VIN search, which we never
call); corporate Legal Notice has a copyright / no-reproduction clause and no
anti-automation clause. All pages are plain GET HTML or GET JSON.

Why the crawl is VEHICLE-driven, not part-driven: a part page
(/en/parts/<pn>) prints every application row (year, submodel, engine code)
but NOT the application note. The note ("Body Type: Coupe", "USA Built",
"with Manual Trans") is printed only on the vehicle page, per part card
(div.tuile-produit__commentaire-applicatif). The tightening rule refuses rows
whose note the puller cannot see, so we must read the note, so we read
vehicle pages.

Navigation (all GET; JSON endpoints are what the site's own form calls):
    /en/vehicules/get-models.json?year=Y&make=M        {"Civic": "Civic", ...}
    /en/vehicules/get-submodels.json?year=&make=&model=
        [{"vehiculeIds": "23745", "submodel": "LX", "engtype": "L4", "liter": "1.8"}]
        a comma in vehiculeIds means several engines:
    /en/vehicules/get-motorizations.json?vehiculeIds=a,b
        [{"vehicule_id": .., "fuel", "fueldel", "asp", "engvin", "engdesg"}]
    /en/vehicles/<id>/parts?limit=50[&page=N]           one vehicle, every part

Record = one vehicle page: the vehicle (meta description "Y / Make / Model /
Submodel"), its motorization block, and every part card verbatim
(part number, line, application note, specs).
"""
from __future__ import annotations

import html as htmllib
import json
import re
import time
import urllib.parse

try:
    from . import common
except ImportError:  # run as a script from this directory
    import common  # type: ignore

SITE = "ecat.spectrapremium.com"
STATUS = "ok"
BASE = f"https://{SITE}"
# One crawl "category": every vehicle page carries every product line. The
# root is the catalog home (one fetch); its children come from the worklist.
CATEGORIES = {"vehicle": {"root": "/en"}}
MIN_YEAR = 1995
get = common.get  # tests swap this for a cache-only reader

_Q = urllib.parse.quote


def models_url(year: int, make: str) -> str:
    return f"{BASE}/en/vehicules/get-models.json?year={year}&make={_Q(make)}"


def submodels_url(year: int, make: str, model: str) -> str:
    return f"{BASE}/en/vehicules/get-submodels.json?year={year}&make={_Q(make)}&model={_Q(model)}"


def motorizations_url(ids: str) -> str:
    return f"{BASE}/en/vehicules/get-motorizations.json?vehiculeIds={_Q(ids, safe=',')}"


def vehicle_url(vid: str) -> str:
    return f"{BASE}/en/vehicles/{vid}/parts?limit=50"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


# ------------------------------------------------------------- worklist ---
def worklist_targets() -> dict:
    """{(year, make): {model_norm: (score, is_seed)}} from worklist.json:
    every segment year >= MIN_YEAR; the seed year scores highest so a time
    budget covers one year per generation first."""
    from pathlib import Path
    wl = json.loads((Path(__file__).resolve().parents[1] / "worklist.json").read_text())["sites"]
    out: dict = {}
    for site in wl.values():
        for seg in site["segments"]:
            y0, y1 = seg["segment"]
            seed = seg.get("seed_year") or y1
            for y in range(max(y0, MIN_YEAR), y1 + 1):
                sc = seg["cars"] * (1.0 if y == seed else 0.5 / (1 + abs(y - seed)))
                d = out.setdefault((y, seg["make"]), {})
                k = _norm(seg["model"])
                d[k] = max(d.get(k, 0), sc)
    return out


_TARGETS = None


def targets() -> dict:
    global _TARGETS
    if _TARGETS is None:
        _TARGETS = worklist_targets()
    return _TARGETS


def _qs(url: str) -> dict:
    return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items()}


def score(url: str, *_ignored) -> float:
    """Crawl order (run.py calls this when a module defines it)."""
    q = _qs(url)
    if "/get-models.json" in url:
        t = targets().get((int(q["year"]), q["make"]), {})
        return 1e9 + sum(t.values())
    if "/get-submodels.json" in url or "/get-motorizations.json" in url:
        return float(q.get("_score", 0)) or 1.0
    return 1e12


def model_matches(site_model: str, wanted: dict) -> float:
    """Score of the worklist model this catalog model name stands for, 0 if
    none. Exact normalized name only (no fuzzy guess): 'CR-V' == 'crv'."""
    return wanted.get(_norm(site_model), 0.0)


# -------------------------------------------------------------- listing ---
def parse_listing(url: str, body: str) -> dict:
    out = {"children": [], "products": [], "next": None}
    if url.rstrip("/") == BASE + "/en":
        for (y, mk), d in targets().items():
            out["children"].append(models_url(y, mk))
        return out
    q = _qs(url)
    data = json.loads(body) if body.strip() else []
    if "/get-models.json" in url:
        wanted = targets().get((int(q["year"]), q["make"]), {})
        for m in (data or {}):
            sc = model_matches(m, wanted)
            if sc:
                out["children"].append(submodels_url(int(q["year"]), q["make"], m) + f"&_score={sc:.3f}")
        return out
    if "/get-submodels.json" in url:
        for row in data or []:
            ids = str(row.get("vehiculeIds", ""))
            if "," in ids:
                out["children"].append(motorizations_url(ids) + f"&_score={q.get('_score', '1')}")
            elif ids:
                out["products"].append(vehicle_url(ids))
        return out
    if "/get-motorizations.json" in url:
        for row in data or []:
            if row.get("vehicule_id"):
                out["products"].append(vehicle_url(str(row["vehicule_id"])))
        return out
    raise ValueError(f"not a listing url: {url}")


def fetch_url(url: str) -> str:
    """Strip our private `_score` hint before the request."""
    p = urllib.parse.urlsplit(url)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if k != "_score"]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q, safe=",", quote_via=urllib.parse.quote), ""))


def listing(url: str) -> dict:
    d = get(fetch_url(url))
    if d.get("status") != 200:
        raise RuntimeError(f"HTTP {d.get('status')}")
    return parse_listing(url, d["html"])


# -------------------------------------------------------------- vehicle ---
def _text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


_CARD = re.compile(r'<article class="tuile-produit">(.*?)</article>', re.S)


def parse_vehicle_page(url: str, html: str) -> dict:
    m = re.search(r'<meta name="description" content="[^"]*?for &quot;(.*?)&quot;', html)
    if not m:
        raise ValueError("no vehicle description")
    desc = htmllib.unescape(m.group(1))
    parts = [p.strip() for p in desc.split(" / ")]
    if len(parts) != 4 or not re.fullmatch(r"(19|20)\d\d", parts[0]):
        raise ValueError(f"unexpected vehicle description {desc!r}")
    motor = {}
    for t, v in re.findall(r'<dt class="parts__motorization__term">(.*?)</dt>\s*'
                           r'<dd class="parts__motorization__description">(.*?)</dd>', html, re.S):
        motor[_text(t)] = _text(v)
    cards = []
    for c in _CARD.findall(html):
        pn = re.search(r'class="tuile-produit__code-produit"><a href="/en/parts/([^"]+)"[^>]*>(.*?)</a>', c, re.S)
        if not pn:
            raise ValueError("card without part number")
        note = re.search(r'<div class="tuile-produit__commentaire-applicatif">(.*?)</div>', c, re.S)
        line = re.search(r'<div class="tuile-produit__canada-ligne">(.*?)</div>', c, re.S)
        specs = {_text(k): _text(v) for k, v in re.findall(
            r'<dt class="tuile-produit__nom-spec">(.*?)</dt>\s*<dd class="tuile-produit__valeur-spec">(.*?)</dd>', c, re.S)}
        cards.append({"pn": _text(pn.group(2)), "href_pn": urllib.parse.unquote(pn.group(1)),
                      "line": _text(line.group(1)) if line else "",
                      "note": _text(note.group(1)) if note else "", "specs": specs})
    cnt = re.search(r"Showing parts (\d+) to (\d+) out of (\d+)", html)
    nxt = re.search(r'<a[^>]*rel="next"[^>]*href="([^"]+)"', html) or \
        re.search(r'<a[^>]*href="([^"]+)"[^>]*rel="next"', html)
    flags = []
    if any(c["pn"] != c["href_pn"] for c in cards):
        flags.append("pn_differs_from_link")
    return {"year": int(parts[0]), "make": parts[1], "model": parts[2], "submodel": parts[3],
            "motorization": motor, "cards": cards,
            "count": [int(x) for x in cnt.groups()] if cnt else None,
            "next": urllib.parse.urljoin(BASE, htmllib.unescape(nxt.group(1))) if nxt else None,
            "flags": flags}


def product(url: str, category: str) -> dict:
    """One vehicle (all result pages merged) -> one record."""
    vid = re.search(r"/vehicles/(\d+)/parts", url).group(1)
    pages, u, rec = 0, url, None
    while u and pages < 10:
        d = get(u)
        if d.get("status") != 200:
            raise RuntimeError(f"HTTP {d.get('status')}")
        p = parse_vehicle_page(u, d["html"])
        if rec is None:
            rec = {k: p[k] for k in ("year", "make", "model", "submodel", "motorization")}
            rec.update(cards=[], flags=list(p["flags"]), retrieved=d.get("retrieved"))
        rec["cards"].extend(p["cards"])
        rec["flags"] += [f for f in p["flags"] if f not in rec["flags"]]
        total = p["count"][2] if p["count"] else None
        u = p["next"]
        pages += 1
    if total is not None and total != len(rec["cards"]):
        rec["flags"].append(f"card_count_mismatch:{len(rec['cards'])}/{total}")
    rec.update(site=SITE, category=category, vehicle_id=vid, product_url=url,
               retrieved=rec.get("retrieved") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return rec
