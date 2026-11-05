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
from fetch import NetworkError, Refused  # noqa: E402

TIERS = {
    "A": ["alternator", "starter", "ac-compressor", "headlights", "tail-lights",
          "side-mirrors", "window-regulator", "window-switch", "climate-control",
          "fuel-pump-module", "throttle-body", "power-steering-pump"],
    "B": ["gauge-cluster", "ignition-coils", "radiator", "door-front", "door-rear",
          "hood", "fender", "bumper-front", "bumper-rear", "grille", "trunk-lid",
          "tailgate", "liftgate"],
}
MAX_SEEDS = 3


def _squash(s: str, make: str = "") -> str:
    t = re.sub(r"[^a-z0-9]", "", s.lower())
    m = re.sub(r"[^a-z0-9]", "", make.lower())
    return t[len(m):] if m and t.startswith(m) and len(t) > len(m) else t


def same_model(printed: str, feed: str, make: str = "") -> bool:
    """Coverage bookkeeping only (which seed years still need a visit): does
    the catalog's printed model name stand for our feed's model? Tolerant on
    spacing, punctuation, a leading make, and a series suffix on either side
    ("Mazda 3"/"Mazda3", "Silverado"/"Silverado 1500", "Camry"/"Camry
    Hybrid"). A false match only means fewer extra seed years; it never
    changes a record."""
    a, b = _squash(printed, make), _squash(feed, make)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 3 and long_.startswith(short)


def module_for(site: str):
    name = re.sub(r"[^a-z0-9]", "_", site.replace("www.", "").split(".")[0])
    return importlib.import_module(f"sites.{name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--tier", default="all")
    ap.add_argument("--max-segments", type=int, default=0)
    ap.add_argument("--minutes", type=float, default=0, help="stop cleanly after this long (checkpointed runs)")
    a = ap.parse_args()
    deadline = time.time() + a.minutes * 60 if a.minutes else None
    site = a.site
    mod = module_for(site)
    wl = json.loads((ROOT / "worklist.json").read_text())["sites"][site]["segments"]
    if a.max_segments:
        wl = wl[: a.max_segments]
    tiers = ["A", "B"] if a.tier == "all" else [a.tier]
    (ROOT / "raw").mkdir(exist_ok=True)
    raw = ROOT / "raw" / f"{site}.jsonl"
    if (ROOT / "raw" / f"{site}.blocked").exists():
        print(f"{site} is blocked: {(ROOT / 'raw' / f'{site}.blocked').read_text().strip()}")
        sys.exit(3)
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
    net = {"streak": 0}

    def net_fail(where: str, e: Exception) -> None:
        """Transient failure: log, count, and pause the slice on a streak."""
        prog["errors"] += 1
        net["streak"] += 1
        log(f"net-fail {where}: {e}")
        if net["streak"] >= 5:
            save()
            log("5 network failures in a row; pausing this slice (exit 11)")
            sys.exit(11)
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
                    if deadline and time.time() > deadline:
                        save()
                        log(f"time budget reached records={prog['records']}")
                        sys.exit(10)
                    year = seeds.pop(0)
                    tried.append(year)
                    key = f"{tier}|{make}|{model}|{year}"
                    if key in done:
                        continue
                    seed_net_fail = False
                    try:
                        urls = mod.categories_for(make, model, year, cats)
                        net["streak"] = 0
                    except Refused:
                        raise
                    except NetworkError as e:
                        net_fail(f"nav {make} {model} {year}", e)
                        continue  # not marked done: the next slice retries it
                    except Exception as e:  # navigation miss: log and move on
                        prog["errors"] += 1
                        log(f"nav-fail {make} {model} {year}: {type(e).__name__}: {e}")
                        done.add(key)
                        continue
                    for cat in cats:
                        for list_url in urls.get(cat, []):
                            try:
                                parts = mod.parts_on_page(list_url, cat)
                                net["streak"] = 0
                            except Refused:
                                raise
                            except NetworkError as e:
                                seed_net_fail = True
                                net_fail(f"list {list_url}", e)
                                continue
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
                                    net["streak"] = 0
                                except Refused:
                                    raise
                                except NetworkError as e:
                                    seed_net_fail = True
                                    net_fail(f"product {p['product_url']}", e)
                                    continue
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
                                    if same_model(str(f.get("model", "")), model, make):
                                        lo, hi = f["years"]
                                        covered.update(range(lo, hi + 1))
                    if seed_net_fail:
                        log(f"seed {key} had network failures; left open for retry")
                    else:
                        done.add(key)
                    save()
                    missing = sorted((lot_years - covered) - set(tried))
                    if missing and not seeds:
                        seeds.append(missing[len(missing) // 2])
                log(f"seg done tier={tier} {make} {model} {seg['segment']} seeds={tried} records={prog['records']} errors={prog['errors']}")
    except Refused as e:
        log(f"STOPPED: {e}")
        save()
        if "stopped" in str(e) or "refused or challenged" in str(e) or "robots.txt HTTP" in str(e):
            (ROOT / "raw" / f"{site}.blocked").write_text(str(e))
        sys.exit(3)
    except Exception:
        log("CRASH: " + traceback.format_exc())
        save()
        raise
    save()
    if not a.max_segments and a.tier == "all":
        (ROOT / "raw" / f"{site}.done").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log(f"finished records={prog['records']} errors={prog['errors']}")


if __name__ == "__main__":
    main()
