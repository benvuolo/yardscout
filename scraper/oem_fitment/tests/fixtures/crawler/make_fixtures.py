#!/usr/bin/env python3
"""Rebuild real_pages.json from the local fetch.py cache (scraper/oem_fitment/cache,
gitignored). Developer tool: the committed real_pages.json is what tests read,
and CI never runs this.

    python3 scraper/oem_fitment/tests/fixtures/crawler/make_fixtures.py

Every page here was fetched through fetch.py (toyotapartsnow 2026-11-05 by
the crawler-requirements session, 10 requests 10 s apart; GM and Ford pages by
the PartsGiant builder session). Pages are trimmed to what the parsers read,
so the fixture stays small:
  * list pages: the store's partList / gpgOnlyPartList / expandPartList rows,
    each row cut to the keys the templates read;
  * year, model and catalog pages: <title>, every catalog link (hrefs ending
    in -parts.html or -parts, and /parts-list/ links) and the store's
    vehicleOption block;
  * product pages: the store's partInfo and fitment lists, the rendered
    fitment table (PartsGiant) and, for SimplePart, the page's text lines from
    the first label the parser reads through the end of the fitment block,
    one line per <div>, so fetch.text_lines() returns the same lines.
The trimmed page parses to the same records as the full page; test_crawler_
manifests.py checks that against the cache when the cache is present.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import fetch  # noqa: E402

T = "https://www.toyotapartsnow.com"
G = "https://www.gmpartsgiant.com"
F = "https://www.fordpartsgiant.com"
PAGES = {
    "year": [f"{T}/catalog/2009-toyota-camry-parts",
             f"{G}/chevrolet-cruze-parts.html", f"{G}/2014-chevrolet-cruze-parts.html",
             f"{G}/chevrolet-silverado-parts.html", f"{G}/2004-chevrolet-silverado-1500_2wd-parts.html",
             f"{F}/ford-f_150-parts.html", f"{F}/2001-ford-f_150-parts.html",
             f"{F}/2001-ford-f_150--8_cyl_5_4l-4at_4r100-parts.html",
             f"{F}/2004-ford-f_150-f_150_heritage_old_style-parts.html",
             f"{F}/2004-ford-f_150-f_150_new_style-parts.html"],
    "list": [f"{T}/parts-list/2009-toyota-camry/charging-starting/alternator",
             f"{T}/parts-list/2007-toyota-camry/charging-starting/alternator",
             f"{T}/parts-list/1999-toyota-camry/charging-starting/starter",
             f"{T}/parts-list/2009-toyota-camry/body-hardware/outside-mirrors",
             f"{G}/parts-list/2014-chevrolet-cruze/starter_generator_ignition_electrical_lamps/generator_mounting.html",
             f"{G}/parts-list/2014-chevrolet-cruze/starter_generator_ignition_electrical_lamps/starter_motor_and_mounting.html",
             f"{G}/parts-list/2014-chevrolet-cruze/starter_generator_ignition_electrical_lamps/lamps_front.html",
             f"{G}/parts-list/2014-chevrolet-cruze/starter_generator_ignition_electrical_lamps/lamps_rear.html",
             f"{G}/parts-list/2014-chevrolet-cruze/body_mounting_air_conditioning_audio_entertainment/a_c_compressor_assembly.html",
             f"{F}/parts-list/2001-ford-f_150--8_cyl_5_4l-4at_4r100/alternator_battery_distributor_starter/alternator.html",
             f"{F}/parts-list/2004-ford-f_150-f_150_new_style/electrical/alternator_and_mountings.html"],
    "product_sp": [f"{T}/oem/toyota~mirror-assembly-outer-r~87910-06925",
                   f"{T}/oem/toyota~reman-alternator~27060-0h111-84",
                   f"{T}/oem/toyota~motor-assy-power-window-regulator-front-lh~85720-ae010",
                   f"{T}/oem/toyota~passenger-side-mirror-assembly-outside-rear-view~87910-33660-c0"],
    "product_pg": [f"{G}/parts/gm-generator-asm-13597227.html", f"{G}/parts/gm-headlamp-95291963.html",
                   f"{G}/parts/gm-lamp-95389371.html", f"{G}/parts/gm-lamp-asm-rr-body-structure-stop-94540776.html",
                   f"{F}/parts/ford-alternator-assy_f7pz-10346-karm.html"],
}
ROW_KEYS = ("partNumber", "mainDesc", "auxiliaryDesc", "pncDesc", "mainDescAlter", "allExtraInfoList", "replace", "url")


def _store(html: str) -> dict:
    from sites import _simplepart
    return _simplepart.store(html)


def _script(obj: dict) -> str:
    return "<script>window.__INITIAL_STORE__ = " + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def _title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    return f"<title>{m.group(1)}</title>" if m else ""


def trim_list(html: str) -> str:
    pl = _store(html).get("partList") or {}
    out = {}
    for sec in ("partList", "gpgOnlyPartList", "expandPartList"):
        if sec in pl:
            out[sec] = [[{k: r.get(k) for k in ROW_KEYS if k in r} for r in (g or [])] for g in (pl[sec] or [])]
    return f"<html><head>{_title(html)}</head><body>{_script({'partList': out})}</body></html>"


def trim_year(html: str) -> str:
    hrefs = []
    for h in re.findall(r'href="([^"]+)"', html):
        if (h.startswith("/parts-list/") or h.endswith("-parts.html") or re.match(r"^/\d{4}-[^/]+-parts$", h)
                or h.startswith("/catalog/")) and h not in hrefs:
            hrefs.append(h)
    st = {}
    try:
        st = {"vehicleOption": _store(html).get("vehicleOption")}
    except Exception:
        pass
    links = "".join(f'<a href="{h}">x</a>' for h in hrefs)
    return f"<html><head>{_title(html)}</head><body>{links}{_script(st)}</body></html>"


def trim_product_sp(html: str) -> str:
    st = _store(html).get("partNumber") or {}
    keep = {"partNumber": {k: st.get(k) for k in ("partInfo", "fitVehicleTitleList", "fitVehicleList")}}
    lines = fetch.text_lines(html)
    top = lines.index("Vehicle Fitment") if "Vehicle Fitment" in lines else len(lines)
    starts = [lines.index(lb) for lb in ("Position", "Replaces", "Replaced By") if lb in lines[:top]] + [top]
    a = min(starts)
    b = len(lines)
    for i in range(top, len(lines)):
        if lines[i] in ("Warning:", "Customer Questions & Expert Answers", "View More") and i > top:
            b = i + 1
            break
    body = "".join(f"<div>{htmllib.escape(ln, quote=False)}</div>" for ln in lines[a:b])
    return f"<html><head></head><body>{body}{_script(keep)}</body></html>"


def trim_product_pg(html: str) -> str:
    st = _store(html).get("partNumber") or {}
    keep = {"partNumber": {k: st.get(k) for k in ("partInfo", "fitVehicleTitleList", "fitVehicleList")}}
    i = html.find('class="fit-vehicle-list-table"')
    table = ""
    if i >= 0:
        s = html.rfind("<table", 0, i)
        e = html.find("</table>", i)
        table = html[s:e + len("</table>")]
    return f"<html><head></head><body>{table}{_script(keep)}</body></html>"


def main() -> None:
    trim = {"year": trim_year, "list": trim_list, "product_sp": trim_product_sp, "product_pg": trim_product_pg}
    out = {}
    for kind, urls in PAGES.items():
        for u in urls:
            if not fetch.cache_path(u).exists():
                sys.exit(f"not in the local cache: {u}")
            d = fetch.get(u)
            out[u] = {"kind": kind, "status": d["status"], "final_url": d.get("final_url") or u,
                      "retrieved": d.get("retrieved"), "html": trim[kind](d["html"])}
    p = HERE / "real_pages.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=0, sort_keys=True) + "\n")
    print(f"wrote {p} ({p.stat().st_size} bytes, {len(out)} pages)")


if __name__ == "__main__":
    main()
