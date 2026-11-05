"""Test helper for the crawler-requirement tests (CURATION_SPEC.md §3.2):
serves fixture pages to both templates instead of fetch.get, so no test
touches the network or the local cache.

    pages = Pages(real_pages(), {...synthetic url: page...})
    install(pages)          # _simplepart.get/cached and _partsgiant.get/cached

`get(url)` returns a copy of the page (KeyError-like Missing when absent, the
way a fetch would fail); `cached(url)` returns the page or None, never raising,
like the templates' cache-only re-read. Every call is logged in `calls` so a
test can assert that manifests make no extra requests.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIX = Path(__file__).resolve().parent / "fixtures" / "crawler"

TIER_A = ["alternator", "starter", "ac-compressor", "headlights", "tail-lights", "side-mirrors",
          "window-regulator", "window-switch", "climate-control", "fuel-pump-module", "throttle-body",
          "power-steering-pump"]
TIER_B = ["gauge-cluster", "ignition-coils", "radiator", "door-front", "door-rear", "hood", "fender",
          "bumper-front", "bumper-rear", "grille", "trunk-lid", "tailgate", "liftgate"]
ALL_CATS = TIER_A + TIER_B


class Missing(Exception):
    """The page is not in the fixture set (a real fetch would have gone out)."""


class Pages:
    def __init__(self, *page_sets: dict):
        self.pages: dict[str, dict] = {}
        for s in page_sets:
            self.pages.update(s)
        self.calls: list[tuple[str, str]] = []

    def _page(self, url: str) -> dict:
        d = copy.deepcopy(self.pages[url])
        d.pop("kind", None)
        d.setdefault("url", url)
        d.setdefault("final_url", url)
        d.setdefault("retrieved", "2026-11-05T00:00:00Z")
        d["cached"] = True
        return d

    def get(self, url: str) -> dict:
        self.calls.append(("get", url))
        if url not in self.pages:
            raise Missing(url)
        return self._page(url)

    def cached(self, url: str):
        self.calls.append(("cached", url))
        return self._page(url) if url in self.pages else None

    def gets(self) -> list[str]:
        return [u for k, u in self.calls if k == "get"]


def real_pages() -> dict:
    return json.loads((FIX / "real_pages.json").read_text())


def page(html: str, status: int = 200, final_url: str | None = None, retrieved: str = "2026-11-05T00:00:00Z") -> dict:
    d = {"status": status, "html": html, "retrieved": retrieved}
    if final_url:
        d["final_url"] = final_url
    return d


def store_html(store: dict, body: str = "", title: str = "") -> str:
    s = json.dumps(store, ensure_ascii=False).replace("</", "<\\/")
    return (f"<html><head><title>{title}</title></head><body>{body}"
            f"<script>window.__INITIAL_STORE__ = {s}</script></body></html>")


def install(pages: Pages) -> None:
    from sites import _partsgiant, _simplepart
    for mod in (_simplepart, _partsgiant):
        mod.get = pages.get
        if hasattr(mod, "cached"):
            mod.cached = pages.cached


def record_outputs() -> dict:
    """Everything the three contract functions return for the real fixture
    pages, in a fixed order (PartsGiant product() reads list positions that
    parts_on_page saved, so lists run before products)."""
    from sites import fordpartsgiant, gmpartsgiant, toyotapartsnow
    mods = {"www.toyotapartsnow.com": toyotapartsnow, "www.gmpartsgiant.com": gmpartsgiant,
            "www.fordpartsgiant.com": fordpartsgiant}
    real = real_pages()
    out: dict = {"nav": {}, "lists": {}, "products": {}}
    out["nav"]["Toyota Camry 2009"] = toyotapartsnow.categories_for("Toyota", "Camry", 2009, ALL_CATS)
    out["nav"]["Chevrolet Cruze 2014"] = gmpartsgiant.categories_for("Chevrolet", "Cruze", 2014, ALL_CATS)
    out["nav"]["Ford F-150 2004"] = fordpartsgiant.categories_for("Ford", "F-150", 2004, ALL_CATS)
    for url in sorted(u for u, p in real.items() if p["kind"] == "list"):
        mod = mods[url.split("/")[2]]
        rules = mod._T.rules if hasattr(mod, "_T") else mod.CFG.parts
        for cat in ALL_CATS:
            if cat in rules:
                out["lists"][f"{cat} {url}"] = mod.parts_on_page(url, cat)
    for url in sorted(u for u, p in real.items() if p["kind"].startswith("product")):
        out["products"][url] = mods[url.split("/")[2]].product(url)
    return out
