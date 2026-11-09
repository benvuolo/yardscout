#!/usr/bin/env python3
"""Part-driven runner for aftermarket application catalogs (separate from crawl.py).

    python3 scraper/oem_fitment/aftermarket/run.py --site www.dbelectrical.com
        [--category alternator|starter|all] [--max-products N] [--minutes M]

Walks a site module's catalog tree (category -> make -> model -> paginated
product cards), most valuable pages first, and writes one record per
product page. Every request goes through fetch.get (via common.get, which
adds an RFC 9309 robots check). Append-only and resumable:

    aftermarket/raw/<site>.jsonl          one record per (category, product page)
    aftermarket/raw/<site>.progress.json  pending queue, done pages, seen products
    aftermarket/raw/<site>.log
    aftermarket/raw/<site>.done | .blocked

Exit codes: 0 finished (or cap reached), 10 time budget reached, 11 network
errors in a row (page left queued; run again later), 3 site stopped/blocked
(permanent: no retries, no workaround), 4 module unreachable.

Priority: make index pages first; then model pages scored by cars on our
lots (worklist.json, all sites) + engine-family applications
(junkyard_scraper.ENGINE_FAMILIES) + a boost for makes no dealer catalog
reaches (VW, Mazda, Mitsubishi, BMW, Mercedes, Volvo, ...). Unscored pages
still run, last.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402
from common import Refused, norm  # noqa: E402

NetworkError = getattr(common.fetch, "NetworkError", None) or type("NetworkErrorUnused", (Exception,), {})
NET_STREAK_STOP = 3

RAW = HERE / "raw"
NO_DEALER_CATALOG = {"volkswagen", "mazda", "mitsubishi", "bmw", "mercedesbenz", "volvo",
                     "audi", "mini", "saab", "landrover", "jaguar", "porsche", "fiat", "suzuki",
                     "isuzu", "smart"}
MAKE_PAGE_SCORE = 10**9


SITE_MODULES = {"ecat.spectrapremium.com": "spectrapremium", "www.1aauto.com": "oneaauto"}


def module_for(site: str):
    if site in SITE_MODULES:
        return importlib.import_module(SITE_MODULES[site])
    return importlib.import_module(re.sub(r"[^a-z0-9]", "_", site.replace("www.", "").split(".")[0]))


def build_scores() -> tuple[dict[str, float], dict[tuple[str, str], float]]:
    make_s: dict[str, float] = defaultdict(float)
    model_s: dict[tuple[str, str], float] = defaultdict(float)
    wl = json.loads((HERE.parent / "worklist.json").read_text())["sites"]
    for site in wl.values():
        for seg in site["segments"]:
            mk, mo = norm(seg["make"]), norm(seg["model"])
            make_s[mk] += seg["cars"]
            model_s[(mk, mo)] += seg["cars"]
    try:
        sys.path.insert(0, str(HERE.parents[1]))
        import junkyard_scraper as js  # noqa: E402
        for fam in js.ENGINE_FAMILIES.values():
            for app in fam["apps"]:
                for mk in str(app[0]).split("|"):
                    model_s[(norm(mk), norm(app[1]))] += 50
                    make_s[norm(mk)] += 50
    except Exception as e:  # scoring is an ordering aid only
        print(f"note: ENGINE_FAMILIES not loaded ({type(e).__name__}); worklist scores only")
    for mk in NO_DEALER_CATALOG:
        make_s[mk] += 500
    return make_s, model_s


def score_for(url: str, root: str, make_s, model_s) -> float:
    rest = url.split(root, 1)[1].split("?")[0].strip("/").split("/") if root in url else []
    if len(rest) == 1 and rest[0]:
        if "?page=" in url:
            # a make page's own product pagination repeats what its model pages
            # list; run it after every scored model page, to catch unfiled products
            return 1 + make_s.get(norm(rest[0]), 0) / 1e6
        return MAKE_PAGE_SCORE + make_s.get(norm(rest[0]), 0)
    if len(rest) >= 2:
        mk, mo = norm(rest[0]), norm(rest[1])
        boost = 500 if mk in NO_DEALER_CATALOG else 0
        return model_s.get((mk, mo), 0) + boost + make_s.get(mk, 0) / 1e6
    return MAKE_PAGE_SCORE * 10  # the category root itself


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--category", default="all")
    ap.add_argument("--max-products", type=int, default=0, help="stop after this many new records (trials)")
    ap.add_argument("--minutes", type=float, default=0, help="stop cleanly after this long (checkpointed runs)")
    a = ap.parse_args()
    deadline = time.time() + a.minutes * 60 if a.minutes else None
    site = a.site
    mod = module_for(site)
    RAW.mkdir(exist_ok=True)
    if mod.STATUS != "ok":
        print(f"{site}: {mod.STATUS}")
        sys.exit(4)
    if (RAW / f"{site}.blocked").exists():
        print(f"{site} is blocked: {(RAW / f'{site}.blocked').read_text().strip()}")
        sys.exit(3)
    cats = list(mod.CATEGORIES) if a.category == "all" else [a.category]
    raw = RAW / f"{site}.jsonl"
    logp = RAW / f"{site}.log"
    prog_p = RAW / f"{site}.progress.json"
    prog = json.loads(prog_p.read_text()) if prog_p.exists() else {}
    prog.setdefault("records", 0)
    prog.setdefault("errors", 0)
    prog.setdefault("requests_new", 0)
    prog.setdefault("cats", {})
    seen = set(prog.get("seen_products", []))
    make_s, model_s = build_scores()
    new_records = 0
    net_streak = 0

    def log(msg: str) -> None:
        with open(logp, "a") as fh:
            fh.write(time.strftime("%Y-%m-%dT%H:%M:%SZ ", time.gmtime()) + msg + "\n")

    def save() -> None:
        prog["seen_products"] = sorted(seen)
        prog_p.write_text(json.dumps(prog))

    def counted_get(fn, *args):
        before = common.fetch.cache_path(args[0]).exists()
        out = fn(*args)
        if not before:
            prog["requests_new"] += 1
        return out

    log(f"start site={site} cats={cats} max_products={a.max_products} minutes={a.minutes}")
    try:
        for cat in cats:
            root = mod.CATEGORIES[cat]["root"]
            st = prog["cats"].setdefault(cat, {"pending": [[0, mod.BASE + root]], "done_lists": [], "finished": False})
            if st["finished"]:
                continue
            done_lists = set(st["done_lists"])
            while st["pending"]:
                if deadline and time.time() > deadline:
                    save()
                    log(f"time budget reached records={prog['records']}")
                    sys.exit(10)
                if a.max_products and new_records >= a.max_products:
                    save()
                    log(f"product cap reached records={prog['records']}")
                    return
                st["pending"].sort(key=lambda x: -x[0])
                sc, url = st["pending"].pop(0)
                if url in done_lists:
                    continue
                try:
                    li = counted_get(mod.listing, url)
                except Refused:
                    st["pending"].insert(0, [sc, url])
                    raise
                except NetworkError as e:
                    st["pending"].insert(0, [sc, url])
                    net_streak += 1
                    log(f"network {url}: {e} streak={net_streak}")
                    if net_streak >= NET_STREAK_STOP:
                        save()
                        log("pausing: network error streak")
                        sys.exit(11)
                    continue
                except Exception as e:
                    prog["errors"] += 1
                    log(f"list-fail {url}: {type(e).__name__}: {e}")
                    done_lists.add(url)
                    continue
                net_streak = 0
                page_incomplete = False
                queued = {u for _, u in st["pending"]}
                score = getattr(mod, "score", None) or (lambda u, *_: score_for(u, root, make_s, model_s))
                for c in li["children"]:
                    if c not in done_lists and c not in queued:
                        st["pending"].append([score(c), c])
                if li["next"] and li["next"] not in done_lists and li["next"] not in queued:
                    nsc = score(li["next"]) if sc >= MAKE_PAGE_SCORE else sc
                    st["pending"].append([nsc, li["next"]])
                for pu in li["products"]:
                    key = f"{cat}|{pu}"
                    if key in seen:
                        continue
                    if a.max_products and new_records >= a.max_products:
                        break
                    if deadline and time.time() > deadline:
                        break
                    try:
                        rec = counted_get(mod.product, pu, cat)
                    except Refused:
                        raise
                    except NetworkError as e:
                        net_streak += 1
                        page_incomplete = True
                        log(f"network {pu}: {e} streak={net_streak}")
                        if net_streak >= NET_STREAK_STOP:
                            break
                        continue
                    except Exception as e:
                        prog["errors"] += 1
                        log(f"product-fail {pu}: {type(e).__name__}: {e}")
                        continue
                    rec["found_on"] = url
                    seen.add(key)
                    with open(raw, "a") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    prog["records"] += 1
                    new_records += 1
                    net_streak = 0
                else:
                    if not page_incomplete:
                        done_lists.add(url)  # only when every card on the page was handled
                st["done_lists"] = sorted(done_lists)
                if url not in done_lists:
                    st["pending"].insert(0, [sc, url])  # resume this page next time
                save()
                if net_streak >= NET_STREAK_STOP:
                    log("pausing: network error streak")
                    sys.exit(11)
                log(f"list {cat} {url} products={len(li['products'])} children={len(li['children'])} "
                    f"next={'y' if li['next'] else 'n'} records={prog['records']} new_requests={prog['requests_new']}")
            st["finished"] = True
            save()
            log(f"category done {cat} records={prog['records']}")
    except Refused as e:
        log(f"STOPPED: {e}")
        save()
        msg = str(e)
        if "stopped" in msg or "refused or challenged" in msg or "robots.txt HTTP" in msg:
            (RAW / f"{site}.blocked").write_text(msg)
        sys.exit(3)
    except SystemExit:
        raise
    except Exception:
        log("CRASH: " + traceback.format_exc())
        save()
        raise
    save()
    if all(prog["cats"].get(c, {}).get("finished") for c in mod.CATEGORIES):
        (RAW / f"{site}.done").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log(f"finished records={prog['records']} errors={prog['errors']}")


if __name__ == "__main__":
    main()
