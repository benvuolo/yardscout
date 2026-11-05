#!/usr/bin/env python3
"""Deterministic OEM-fitment crawl for one site, driven by worklist.json.

    python3 scraper/oem_fitment/crawl.py --site www.toyotapartsnow.com [--tier A|B|all] [--max-segments N]

A site module (scraper/oem_fitment/sites/<module>.py, see README.md) supplies
navigation and parsing; this runner supplies order, resume, coverage seeding
and the raw evidence log. All network access goes through fetch.get (robots,
rate limits, circuit breaker, cache). Output, append-only and resumable:

    raw/<site>.jsonl         one record per (segment, category, part number)
    raw/<site>.progress.json counters + done keys
    raw/<site>.log           human-readable progress
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fetch import Refused  # noqa: E402

TIERS = {
    "A": ["alternator", "starter", "ac-compressor", "headlights", "tail-lights",
          "side-mirrors", "window-regulator", "window-switch", "climate-control",
          "fuel-pump-module", "throttle-body", "power-steering-pump"],
    "B": ["gauge-cluster", "ignition-coils", "radiator", "door-front", "door-rear",
          "hood", "fender", "bumper-front", "bumper-rear", "grille", "trunk-lid",
          "tailgate", "liftgate"],
}
MAX_SEEDS = 3


def module_for(site: str):
    name = re.sub(r"[^a-z0-9]", "_", site.replace("www.", "").split(".")[0])
    return importlib.import_module(f"sites.{name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--tier", default="all")
    ap.add_argument("--max-segments", type=int, default=0)
    a = ap.parse_args()
    site = a.site
    mod = module_for(site)
    wl = json.loads((ROOT / "worklist.json").read_text())["sites"][site]["segments"]
    if a.max_segments:
        wl = wl[: a.max_segments]
    tiers = ["A", "B"] if a.tier == "all" else [a.tier]
    raw = ROOT / "raw" / f"{site}.jsonl"
    prog_p = ROOT / "raw" / f"{site}.progress.json"
    logp = ROOT / "raw" / f"{site}.log"
    prog = json.loads(prog_p.read_text()) if prog_p.exists() else {"done": [], "records": 0, "errors": 0, "products_seen": []}
    done = set(prog["done"])
    seen_pn = set(prog["products_seen"])

    def log(msg: str) -> None:
        with open(logp, "a") as fh:
            fh.write(time.strftime("%H:%M:%S ") + msg + "\n")

    def save() -> None:
        prog["done"] = sorted(done)
        prog["products_seen"] = sorted(seen_pn)
        prog_p.write_text(json.dumps(prog))

    log(f"start site={site} segments={len(wl)} tiers={tiers}")
    try:
        for tier in tiers:
            cats = TIERS[tier]
            for seg in wl:
                make, model = seg["make"], seg["model"]
                lot_years = set(range(seg["segment"][0], seg["segment"][1] + 1))
                covered: set[int] = set()
                seeds = [seg["seed_year"]]
                tried: list[int] = []
                while seeds and len(tried) < MAX_SEEDS:
                    year = seeds.pop(0)
                    tried.append(year)
                    key = f"{tier}|{make}|{model}|{year}"
                    if key in done:
                        continue
                    try:
                        urls = mod.categories_for(make, model, year, cats)
                    except Refused:
                        raise
                    except Exception as e:  # navigation miss: log and move on
                        prog["errors"] += 1
                        log(f"nav-fail {make} {model} {year}: {type(e).__name__}: {e}")
                        done.add(key)
                        continue
                    for cat in cats:
                        for list_url in urls.get(cat, []):
                            try:
                                parts = mod.parts_on_page(list_url, cat)
                            except Refused:
                                raise
                            except Exception as e:
                                prog["errors"] += 1
                                log(f"list-fail {list_url}: {type(e).__name__}: {e}")
                                continue
                            for p in parts:
                                pkey = f"{cat}|{p['pn']}"
                                if pkey in seen_pn:
                                    continue
                                try:
                                    prod = mod.product(p["product_url"])
                                except Refused:
                                    raise
                                except Exception as e:
                                    prog["errors"] += 1
                                    log(f"product-fail {p['product_url']}: {type(e).__name__}: {e}")
                                    continue
                                seen_pn.add(pkey)
                                rec = {"site": site, "category": cat, "seed": {"make": make, "model": model, "year": year},
                                       "segment": seg["segment"], "list_url": list_url, **p, **prod}
                                with open(raw, "a") as fh:
                                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                                prog["records"] += 1
                                for f in prod.get("fitment", []):
                                    if str(f.get("model", "")).lower().replace(" ", "") == model.lower().replace(" ", ""):
                                        lo, hi = f["years"]
                                        covered.update(range(lo, hi + 1))
                    done.add(key)
                    save()
                    missing = sorted((lot_years - covered) - set(tried))
                    if missing and not seeds:
                        seeds.append(missing[len(missing) // 2])
                log(f"seg done tier={tier} {make} {model} {seg['segment']} seeds={tried} records={prog['records']} errors={prog['errors']}")
    except Refused as e:
        log(f"STOPPED: {e}")
        save()
        sys.exit(3)
    except Exception:
        log("CRASH: " + traceback.format_exc())
        save()
        raise
    save()
    log(f"finished records={prog['records']} errors={prog['errors']}")


if __name__ == "__main__":
    main()
