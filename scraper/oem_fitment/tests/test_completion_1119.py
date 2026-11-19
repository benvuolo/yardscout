#!/usr/bin/env python3
"""Round 9 F (2026-11-19, owner "crawl"): the own-page completion pass 2.

Offline. Checks the completion files and worklist entries only; the crawler's
fetch rules, pacing, allowlist, robots handling and stop conditions are not
touched by this pass (fetch.py, crawl.py, markers.py, platform_crawl.py and
sites/ are unchanged).
  1. every "complete" entry naming a *_1119.json file: the file exists, its
     version is 2, crawl._load_completion reads at least one row for the site,
     and every row of the file belongs to a site whose entry names the file;
  2. no row for a site that is .blocked / .paused on oem-raw (markers below,
     as listed at oem-raw@57e8b5b99de0), and markers.mode says "complete"
     for every re-opened site (finish marker raw/<site>.c2.done);
  3. the site module navigates each row to the catalog the census pages sit
     in (model slug and variant rule; SimplePart stem), and each census page's
     slug passes the module's own category rule for that row's category;
  4. the variant pages 1119i found unread (Rogue 2017 t32j / t32d, Sentra
     b14x) stay unreachable: the nissanpartsdeal variant rules keep only
     t32u / b14u, so those vehicle-years stay held (no new fetch path).
"""
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import crawl  # noqa: E402
import markers  # noqa: E402
from sites import _partsgiant as PG  # noqa: E402

FAILS = 0


def check(name, ok, got=None):
    global FAILS
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
    if not ok:
        FAILS += 1


# raw/ markers on oem-raw@57e8b5b99de0 for the sites below
ON_RAW = {
    "www.infinitipartsdeal.com": {"done", "v2.done", "c1.done"},
    "www.nissanpartsdeal.com": {"done", "v2.done", "c1.done"},
    "www.jeeppartsdeal.com": {"done", "v2.done", "v3.done", "v5.done", "v6.done", "c1.done"},
    "www.lexuspartsnow.com": {"done", "v2.done", "v3.done", "v4.done", "c1.done"},
    "www.toyotapartsnow.com": {"done", "v2.done", "v3.done", "c1.done"},
    "www.vwpartsgiant.com": {"done", "v3.done", "v4.done", "c1.done"},
    "www.gmpartsgiant.com": {"blocked"},
    "www.fordpartsgiant.com": {"done", "v2.done", "blocked"},
    "www.subarupartsdeal.com": {"done", "blocked"},
    "www.moparpartsgiant.com": {"blocked"},
}
BLOCKED = {s for s, m in ON_RAW.items() if "blocked" in m or "paused" in m}
MODS = {"www.infinitipartsdeal.com": "infinitipartsdeal", "www.nissanpartsdeal.com": "nissanpartsdeal",
        "www.jeeppartsdeal.com": "jeeppartsdeal", "www.lexuspartsnow.com": "lexuspartsnow",
        "www.toyotapartsnow.com": "toyotapartsnow", "www.vwpartsgiant.com": "vwpartsgiant"}

wl = json.loads((ROOT / "worklist.json").read_text())["sites"]
entries = {s: e["complete"] for s, e in wl.items() if str((e.get("complete") or {}).get("file", "")).endswith("_1119.json")}
check("1. six sites re-opened for completion pass 2",
      sorted(entries) == sorted(MODS), sorted(entries))
files = {}
for site, c in entries.items():
    p = ROOT / c["file"]
    check(f"1. {site}: {c['file']} exists, version 2", p.exists() and c["version"] == 2, c)
    rows = crawl._load_completion(c["file"], site)
    check(f"1. {site}: crawl reads {len(rows)} rows of its own", len(rows) >= 1, len(rows))
    files.setdefault(c["file"], set()).add(site)
for f, sites in files.items():
    doc = json.loads((ROOT / f).read_text())
    orphans = [r for r in doc["rows"] if r.get("site") not in sites]
    check(f"1. {f}: every row names a site whose entry reads the file", not orphans and doc["rows"], orphans[:2])
    check(f"2. {f}: no row for a blocked or paused site", not [r for r in doc["rows"] if r["site"] in BLOCKED])
for site in entries:
    have = {f"{site}.{m}" for m in ON_RAW[site]}
    mode = markers.mode(site, wl[site], lambda n: n in have)
    check(f"2. {site}: markers.mode -> complete, finish marker {site}.c2.done",
          mode == "complete" and markers.complete_name(site, wl[site]) == f"{site}.c2.done", mode)
for site in BLOCKED & set(wl):
    have = {f"{site}.{m}" for m in ON_RAW[site]}
    check(f"2. {site}: blocked, nothing runs", markers.mode(site, wl[site], lambda n: n in have) is None)

# 3. navigation reaches the census pages (no network: slugs and rules only)
n_pages = 0
for f, sites in files.items():
    for r in json.loads((ROOT / f).read_text())["rows"]:
        mod = importlib.import_module(f"sites.{MODS[r['site']]}")
        for cat in r["cats"]:
            for u in r["census_pages"][cat]:
                n_pages += 1
                path = u.split("/parts-list/", 1)[1]
                stem, sub = path.split("/", 1)
                if hasattr(mod, "CFG"):
                    m, mk, slugs = PG._model_slugs(mod.CFG, r["make"], r["model"], r["year"])
                    pre = [f"{r['year']}-{mk}-{md}" for md in slugs]
                    var = next((stem[len(p) + 1:] if stem != p else "" for p in pre
                                if stem == p or stem.startswith(p + "-")), None)
                    nav_ok = var is not None and bool(PG._select_variants(m, r["model"], [(var, u)]))
                    tail = sub[: -len(".html")].split("/")[-1]
                    rx, ex = mod.CFG.subcats.get(cat), (mod.CFG.subcat_excl or {}).get(cat)
                    cat_ok = bool(rx and re.search(rx, tail, re.I) and not (ex and re.search(ex, tail, re.I))
                                  and not PG.SUBCAT_COMMON_EXCLUDE.search(tail))
                else:
                    nav_ok = mod._T.stem(r["make"], r["model"], r["year"]) == stem
                    rx = mod._T.cat_pages.get(cat)
                    cat_ok = bool(rx is not None and rx.search(sub))
                check(f"3. {r['make']} {r['model']} {r['year']} {cat}: {path} reached", nav_ok and cat_ok,
                      (nav_ok, cat_ok))
check("3. census pages checked", n_pages >= 40, n_pages)

# 4. the variant pages the crawler does not read as it stands
N = importlib.import_module("sites.nissanpartsdeal")
u = "https://www.nissanpartsdeal.com/x"
rog = [v for v, _u in PG._select_variants(N.MODELS[("Nissan", "Rogue")], "Rogue",
                                           [("hybrid", u), ("t32j", u), ("t32d", u), ("t32u", u)])]
sen = [v for v, _u in PG._select_variants(N.MODELS[("Nissan", "Sentra")], "Sentra", [("b14u", u), ("b14x", u)])]
check("4. Rogue 2017: only t32u is read (t32j / t32d stay held)", rog == ["t32u"], rog)
check("4. Sentra 1995-96: only b14u is read (b14x stays held)", sen == ["b14u"], sen)
rows_n = [r for r in json.loads((ROOT / "completion/nissan.own_page_1119.json").read_text())["rows"]]
check("4. no completion row claims those variant pages",
      not [r for r in rows_n if (r["model"], r["year"]) in {("Rogue", 2017), ("Sentra", 1995), ("Sentra", 1996)}])

print(f"\n{'FAILED' if FAILS else 'passed'}: {FAILS} failure(s)")
sys.exit(1 if FAILS else 0)
