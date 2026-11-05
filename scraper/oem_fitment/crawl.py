#!/usr/bin/env python3
"""Deterministic OEM-fitment crawl for one site, driven by worklist.json.

    python3 scraper/oem_fitment/crawl.py --site www.toyotapartsnow.com [--tier A|B|all] [--max-segments N]
    python3 scraper/oem_fitment/crawl.py --site S --complete groups/_report/<ns>.completion.json [--minutes 28]

A site module (scraper/oem_fitment/sites/<module>.py, see README.md) supplies
navigation and parsing; this runner supplies order, resume, coverage seeding
and the raw evidence log. All network access goes through fetch.get (robots,
rate limits, circuit breaker, cache). Output, append-only and resumable
(README.md "Raw files" has the line formats):

    raw/<site>.jsonl         one record per (category, part number); chain
                             records (R4) carry "via"; a record for a
                             (category, pn) already in the file carries
                             "recrawl_of" (R6)
    raw/<site>.lists.jsonl   R1: one line per list page read, every row
    raw/<site>.years.jsonl   R2: one line per year-catalog page read
    raw/<site>.progress.json counters + done keys
    raw/<site>.log           human-readable progress

The manifests re-read the cached fetch: they never add a request. A .jsonl
file that reaches PART_BYTES continues in <name>.2.jsonl, .3.jsonl ... (one
logical file; line numbers count across the parts in order), so no file
outgrows GitHub's limits on the oem-raw branch.
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
import rawparts  # noqa: E402
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
CHAIN_DEPTH = 4            # R4: replaces / replaced_by hops from a listed record
CHAIN_TRIES = 3            # R4: network attempts per hop before it is given up (chain_given_up)
CHAIN_FIELDS = ("pn", "product_url", "replaces", "replaced_by", "list_replaced_by", "list_info")
PART_BYTES = 40_000_000    # GitHub warns at 50 MB and refuses 100 MB files


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


def norm_pn(pn) -> str:
    return re.sub(r"[^a-z0-9]", "", str(pn or "").lower())


def url_names_pn(url: str, pn: str) -> bool:
    """The product URL's last path segment ends with this part number: after
    the last "~" (/oem/toyota~slug~27060-0h111-84, /genuine/honda~slug~pn.html),
    after the last "_" (/parts/ford-alternator-assy_f7pz-10346-karm.html) or as
    the last "-"-separated piece (/parts/gm-generator-asm-13597227.html)."""
    seg = (url or "").split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    seg = seg[: -len(".html")] if seg.endswith(".html") else seg
    want = norm_pn(pn)
    if not want or not seg:
        return False
    if norm_pn(seg.rsplit("~", 1)[-1]) == want or norm_pn(seg.rsplit("_", 1)[-1]) == want:
        return True
    p = str(pn).strip().lower()
    return seg.lower().endswith("-" + p)


PN_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\- ]{1,40}$")


def chain_targets(rec: dict) -> list[tuple[str, str]]:
    """[(field, pn)] the record names as predecessors ("replaces") or
    successors ("replaced_by": the product page's Replaced By, SimplePart's
    list_replaced_by, PartsGiant's "Replaced By:" list info). Markers that are
    not part numbers ("(MultiSupersession)") are skipped."""
    out: list[tuple[str, str]] = []

    def add(field: str, value) -> None:
        vals = value if isinstance(value, list) else re.split(r"[,;]", str(value or ""))
        for v in vals:
            v = str(v or "").strip()
            if v and PN_TOKEN.match(v) and re.search(r"\d", v):
                out.append((field, v))
    add("replaces", rec.get("replaces") or [])
    add("replaced_by", rec.get("replaced_by") or [])
    add("replaced_by", rec.get("list_replaced_by") or "")
    for x in rec.get("list_info") or []:
        if str(x).lower().startswith("replaced by:"):
            add("replaced_by", str(x).split(":", 1)[1])
    seen, uniq = {norm_pn(rec.get("pn"))}, []
    for f, v in out:
        if norm_pn(v) not in seen:
            seen.add(norm_pn(v))
            uniq.append((f, v))
    return uniq


class RawFile:
    """An append-only JSONL file in size-capped parts with global 1-based line
    numbers: part 1 is raw/<base>.jsonl, part n is raw/<base>.<n>.jsonl. The
    part layout and the reader are rawparts.py's, which every consumer uses."""

    def __init__(self, raw_dir: Path, base: str, log=None):
        self.dir, self.base = raw_dir, base
        self.n = rawparts.part_count(raw_dir, base)
        self._heal(log)
        self.lines = sum(self._count(self.path(i)) for i in range(1, self.n + 1))

    def path(self, i: int) -> Path:
        return rawparts.part_path(self.dir, self.base, i)

    def paths(self) -> list[Path]:
        return [self.path(i) for i in range(1, self.n + 1) if self.path(i).exists()]

    @staticmethod
    def _count(p: Path) -> int:
        if not p.exists():
            return 0
        with open(p, "rb") as fh:
            return sum(1 for _ in fh)

    def _heal(self, log) -> None:
        """A killed writer can leave a torn last line; it would be glued to the
        next record. Cut it (its seed was not saved as done, so it is redone)."""
        p = self.path(self.n)
        if not p.exists() or p.stat().st_size == 0:
            return
        data = p.read_bytes()
        if data.endswith(b"\n"):
            return
        keep = data.rfind(b"\n") + 1
        with open(p, "r+b") as fh:
            fh.truncate(keep)
        if log:
            log(f"healed torn last line of {p.name} ({len(data) - keep} bytes cut)")

    def append(self, obj: dict) -> int:
        line = (json.dumps(obj, ensure_ascii=False) + "\n").encode()
        p = self.path(self.n)
        if p.exists() and p.stat().st_size > 0 and p.stat().st_size + len(line) > PART_BYTES:
            self.n += 1
            p = self.path(self.n)
        with open(p, "ab") as fh:
            fh.write(line)
        self.lines += 1
        return self.lines

    def rows(self):
        """(line number, object or None for an unreadable line), all parts in order."""
        return rawparts.rows(self.paths())


def _load_completion(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = ROOT / path
    data = json.loads(p.read_text())
    rows = data.get("rows", data.get("worklist")) if isinstance(data, dict) else data
    out = []
    for r in rows or []:
        out.append({"make": r["make"], "model": r["model"], "year": int(r["year"]), "cats": list(r["cats"])})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--tier", default="all")
    ap.add_argument("--max-segments", type=int, default=0)
    ap.add_argument("--minutes", type=float, default=0, help="stop cleanly after this long (checkpointed runs)")
    ap.add_argument("--complete", metavar="WORKLIST",
                    help="R3 completion mode: [{make, model, year, cats}] rows (feed names), in order")
    a = ap.parse_args()
    deadline = time.time() + a.minutes * 60 if a.minutes else None
    site = a.site
    mod = module_for(site)
    tiers = ["A", "B"] if a.tier == "all" else [a.tier]
    raw_dir = ROOT / "raw"
    raw_dir.mkdir(exist_ok=True)
    if (raw_dir / f"{site}.blocked").exists():
        print(f"{site} is blocked: {(raw_dir / f'{site}.blocked').read_text().strip()}")
        sys.exit(3)
    prog_p = raw_dir / f"{site}.progress.json"
    logp = raw_dir / f"{site}.log"
    prog = json.loads(prog_p.read_text()) if prog_p.exists() else {"done": [], "records": 0, "errors": 0, "products_seen": []}
    for k in ("chain_records", "chain_unlinked", "chain_failed", "chain_given_up", "chain_then_listed",
              "list_lines", "year_lines", "recrawls"):
        prog.setdefault(k, 0)
    prog.setdefault("chain_retry", [])     # R4 hops that hit a network error, retried at the next start
    prog.setdefault("chain_pending", [])   # R4 records whose chain targets are still to be tried
    prog.setdefault("chain_followed", [])  # "cat|normpn" of listed records queued for R4
    prog.setdefault("chain_seen", [])      # "cat|pn" recorded only as chain records (not products_seen)
    prog.setdefault("list_fail", [])       # list pages that did not parse (read: false), for --complete
    done = set(prog["done"])
    seen_pn = set(prog["products_seen"])   # listed records written ("cat|pn" as listed)
    chain_seen = set(prog["chain_seen"])
    chain_followed = set(prog["chain_followed"])
    chain_norm = {(k.split("|", 1)[0], norm_pn(k.split("|", 1)[1])) for k in chain_seen if "|" in k}
    unlinked_seen: set[tuple[str, str]] = set()  # chain_unlinked counts each number once per run
    seen_norm = {(k.split("|", 1)[0], norm_pn(k.split("|", 1)[1])) for k in seen_pn | chain_seen if "|" in k}

    def log(msg: str) -> None:
        with open(logp, "a") as fh:
            fh.write(time.strftime("%H:%M:%S ") + msg + "\n")

    records = RawFile(raw_dir, site, log)
    lists = RawFile(raw_dir, f"{site}.lists", log)
    years = RawFile(raw_dir, f"{site}.years", log)
    # R6: (category, pn) -> line of its newest record
    last_line: dict[tuple[str, str], int] = {}
    # R4: (category, pn) -> the newest LISTED record's chain fields, so a list
    # row whose record was written earlier (products_seen, possibly before
    # chains were followed at all) can still have its chain followed
    listed_rec: dict[tuple[str, str], dict] = {}
    for n, r in records.rows():
        if r and r.get("category") and r.get("pn"):
            last_line[(r["category"], norm_pn(r["pn"]))] = n
            if "via" not in r:
                listed_rec[(r["category"], norm_pn(r["pn"]))] = {
                    "seed": r.get("seed"), "segment": r.get("segment"), "list_url": r.get("list_url"),
                    "rec": {k: r[k] for k in CHAIN_FIELDS if r.get(k)}}
    # R4: part number -> product URL, from every list row the catalog printed
    url_index: dict[str, str] = {}
    failed_urls: set[str] = set()  # product pages that failed to parse in this run

    def index_rows(rows: list[dict], base: str) -> None:
        for row in rows or []:
            pn, u = row.get("pn"), row.get("url")
            if pn and u and url_names_pn(u, pn):
                url_index.setdefault(norm_pn(pn), u if u.startswith("http") else base + u)
    site_base = f"https://{site}"
    for _, r in lists.rows():
        if r:
            index_rows(r.get("rows"), site_base)
    year_fn = getattr(mod, "year_manifest", None)
    list_fn = getattr(mod, "list_manifest", None)
    links_fn = getattr(mod, "chain_links", None)
    if not (year_fn and list_fn):
        log(f"WARNING {mod.__name__} has no year_manifest/list_manifest: manifests are written without rows")

    def save() -> None:
        prog["done"] = sorted(done)
        prog["products_seen"] = sorted(seen_pn)
        prog["chain_seen"] = sorted(chain_seen)
        prog["chain_followed"] = sorted(chain_followed)
        prog_p.write_text(json.dumps(prog))

    def write_record(rec: dict) -> int:
        key = (rec.get("category"), norm_pn(rec.get("pn")))
        if key in last_line:
            rec["recrawl_of"] = str(last_line[key])
            prog["recrawls"] += 1
        n = records.append(rec)
        last_line[key] = n
        prog["records"] += 1
        return n

    mode = "complete" if a.complete else "worklist"
    log(f"start site={site} mode={mode} tiers={tiers} records={records.lines} list_lines={lists.lines} "
        f"year_lines={years.lines} url_index={len(url_index)}")
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

    def write_years(tier: str, seed: dict, segment, cats: list[str], urls: dict | None, nav_error: str | None) -> None:
        lines = []
        if year_fn:
            try:
                lines = year_fn(seed["make"], seed["model"], seed["year"])
            except Exception as e:  # a manifest bug must not stop the crawl; say so in the line
                lines = [{"error": f"year_manifest failed: {type(e).__name__}: {e}"}]
        if not lines:
            lines = [{"error": "site module has no year_manifest"}]
        placed: set[str] = set()
        for ln in lines:
            pages = {}
            for cat, us in (urls or {}).items():
                mine = [u for u in us if ln.get("catalog") and f"/parts-list/{ln['catalog']}/" in u]
                if mine:
                    pages[cat] = mine
                    placed.update(mine)
            ln["pages"] = pages
        stray = {c: [u for u in us if u not in placed] for c, us in (urls or {}).items()}
        stray = {c: us for c, us in stray.items() if us}
        if stray:
            lines[0]["pages_unplaced"] = stray
        for ln in lines:
            out = {"kind": "year", "site": site, "tier": tier, "seed": seed, "segment": segment, "cats": cats,
                   "nav": "fail" if nav_error else "ok", **ln}
            if nav_error:
                out["nav_error"] = nav_error
            years.append(out)
            prog["year_lines"] += 1

    def list_line(tier, seed, segment, cat, list_url, parts, pstat, error=None) -> None:
        """One R1 line. `error` is set when parts_on_page raised (list-fail):
        the rows are then the template's own re-read, not relabelled (nothing
        came back from the module to relabel them by), and the line is
        `read: false`. A line counts as read only when status is 200 and it
        has no error and no rows_missing."""
        man = None
        if list_fn:
            try:
                man = list_fn(list_url, cat)
            except Exception as e:
                man = {"list_url": list_url, "rows": [], "error": f"list_manifest failed: {type(e).__name__}: {e}"}
        if man is None:
            man = {"list_url": list_url, "rows": [], "error": "site module has no list_manifest"}
        rows = man.get("rows") or []
        kept = {p["pn"] for p in parts or []}
        tmpl = {r["pn"] for r in rows if r.get("matched")}
        for r in rows:
            # what parts_on_page returned is the truth for `matched`: a module
            # wrapper can add rows (Honda's bare "Switch Assy.") or drop them
            if error is None and r.get("pn") in kept and r["pn"] not in tmpl and r.get("excluded_by") != "section_not_read":
                r["matched"], r["excluded_by"], r["matched_by"] = True, None, "site_module"
            elif error is None and r.get("matched") and r.get("pn") not in kept:
                r["matched"], r["excluded_by"] = False, "site_module"
            r["product"] = pstat.get(r.get("pn"), "not_attempted") if r.get("matched") else None
        missing = sorted(kept - {r.get("pn") for r in rows})
        out = {"kind": "list", "site": site, "tier": tier, "seed": seed, "segment": segment, "cat": cat, **man}
        if missing and not man.get("error"):
            out["rows_missing"] = missing  # matched parts with no manifest row: should never happen
            log(f"WARNING manifest rows missing for {missing} on {list_url}")
        if error:
            out["error"] = error if not man.get("error") else f"{error}; {man['error']}"
        out["read"] = out.get("status") == 200 and not out.get("error") and not out.get("rows_missing")
        lists.append(out)
        prog["list_lines"] += 1
        index_rows(rows, site_base)

    def fetch_chain(hop: dict) -> dict | None:
        """One R4 hop: fetch, write the chain record, return it. None on a
        failure: a network failure waits in progress chain_retry (up to
        CHAIN_TRIES attempts, then chain_given_up); a page that does not parse
        is counted in chain_failed."""
        url = hop["url"]
        try:
            prod = mod.product(url)
            net["streak"] = 0
        except Refused:
            raise
        except NetworkError as e:
            tries = int(hop.get("tries", 0)) + 1
            same = (hop["cat"], norm_pn(hop["pn"]))
            prog["chain_retry"] = [h for h in prog["chain_retry"] if (h["cat"], norm_pn(h["pn"])) != same]
            if tries >= CHAIN_TRIES:
                prog["chain_given_up"] += 1
                log(f"chain-given-up {hop['cat']} {hop['pn']} after {tries} network failures: {url}")
            else:
                prog["chain_retry"].append({**hop, "tries": tries})
            net_fail(f"chain product {url}", e)
            return None
        except Exception as e:
            prog["errors"] += 1
            prog["chain_failed"] += 1
            failed_urls.add(url)
            log(f"chain-product-fail {url}: {type(e).__name__}: {e}")
            return None
        cat, tpn = hop["cat"], hop["pn"]
        crec = {"site": site, "category": cat, "seed": hop["seed"], "segment": hop["segment"],
                "list_url": hop["list_url"], "pn": tpn, "name": None, "product_url": url, **prod,
                "via": f"{hop['field']}:{hop['via_pn']}", "via_depth": hop["depth"], "via_root": hop["root"],
                "via_link": hop["how"]}
        # chain-reached, not listed: a list page that matches it later still
        # writes its own listed record (chain_seen is not products_seen)
        chain_seen.update({f"{cat}|{tpn}", f"{cat}|{crec['pn']}"})
        chain_norm.update({(cat, norm_pn(tpn)), (cat, norm_pn(crec["pn"]))})
        seen_norm.update({(cat, norm_pn(tpn)), (cat, norm_pn(crec["pn"]))})
        write_record(crec)
        prog["chain_records"] += 1
        return crec

    def queue_chain(rec: dict, cat: str, seed: dict, segment, list_url: str, depth: int, root_pn) -> None:
        """Persist a record whose chain targets are still to be tried (progress
        chain_pending). It leaves the queue only after every target was tried,
        so a slice that stops mid-chain resumes it at the next start."""
        if depth >= CHAIN_DEPTH:
            return
        prog["chain_pending"].append({"cat": cat, "seed": seed, "segment": segment, "list_url": list_url,
                                      "depth": depth, "root": root_pn,
                                      "rec": {k: rec[k] for k in CHAIN_FIELDS if rec.get(k)}})

    def queue_root(rec: dict, cat: str, seed: dict, segment, list_url: str) -> None:
        """R4 for a listed record, once per (category, pn) (progress chain_followed)."""
        k = f"{cat}|{norm_pn(rec.get('pn'))}"
        if k in chain_followed:
            return
        chain_followed.add(k)
        queue_chain(rec, cat, seed, segment, list_url, 0, rec.get("pn"))

    def chain_step(e: dict) -> None:
        """Try every predecessor / successor the queued record names: fetch the
        ones the catalog links (a list row read in this crawl or a link on the
        record's own product page; URLs are never built), queue what was
        fetched one level deeper."""
        rec, cat = e["rec"], e["cat"]
        unlinked: list[str] = []
        for field, tpn in chain_targets(rec):
            k = norm_pn(tpn)
            if (cat, k) in seen_norm:
                continue  # already recorded (as listed or chain record)
            how, url = None, None
            if links_fn and rec.get("product_url"):
                try:
                    url = (links_fn(rec["product_url"], [tpn]) or {}).get(tpn)
                except Exception as x:
                    log(f"chain_links failed on {rec['product_url']}: {type(x).__name__}: {x}")
                how = "product_page" if url else None
            if not url and k in url_index:
                url, how = url_index[k], "list_row"
            if not url or not url_names_pn(url, tpn):
                if (cat, k) not in unlinked_seen:
                    unlinked_seen.add((cat, k))
                    prog["chain_unlinked"] += 1
                unlinked.append(tpn)
                continue
            if url in failed_urls:
                prog["chain_failed"] += 1  # its product page already failed in this run
                continue
            tries = max([int(h.get("tries", 0)) for h in prog["chain_retry"]
                         if h["cat"] == cat and norm_pn(h["pn"]) == k] or [0])  # attempts so far
            crec = fetch_chain({"cat": cat, "seed": e["seed"], "segment": e["segment"], "list_url": e["list_url"],
                                "field": field, "pn": tpn, "url": url, "how": how, "via_pn": rec.get("pn"),
                                "depth": e["depth"] + 1, "root": e["root"], "tries": tries})
            if crec:
                queue_chain(crec, cat, e["seed"], e["segment"], e["list_url"], e["depth"] + 1, e["root"])
        if unlinked:
            log(f"chain-unlinked {cat} {len(unlinked)} numbers named by {rec.get('pn')}, no catalog link: "
                + ", ".join(unlinked))

    def drain_chains(budget: bool = False) -> bool:
        """Work the chain_pending queue to the end. With budget, stop at the
        time budget (False: work is left). An exit mid-entry (network streak,
        Refused) leaves that entry at the head: it is tried again next time."""
        q = prog["chain_pending"]
        while q:
            if budget and deadline and time.time() > deadline:
                return False
            chain_step(q[0])
            q.pop(0)
        return True

    def retry_chains(budget: bool = True) -> bool:
        """Chain hops that hit a network error earlier (progress chain_retry).
        False when the time budget left some untried."""
        pending, prog["chain_retry"] = prog["chain_retry"], []
        for i, h in enumerate(pending):
            if (h["cat"], norm_pn(h["pn"])) in seen_norm:
                continue
            if budget and deadline and time.time() > deadline:
                prog["chain_retry"] += pending[i:]
                return False
            try:
                crec = fetch_chain(h)
                if crec:
                    queue_chain(crec, h["cat"], h["seed"], h["segment"], h["list_url"], h["depth"], h["root"])
                    drain_chains()
            except (SystemExit, Refused):
                prog["chain_retry"] += pending[i + 1:]  # still owed
                save()
                raise
            save()
        return True

    def chains_owed() -> int:
        return len(prog["chain_pending"]) + len(prog["chain_retry"])

    def visit(tier: str, make: str, model: str, year: int, cats: list[str], segment, covered: set | None) -> tuple[bool, bool]:
        """Navigate one vehicle-year, read its list pages, record new parts.
        Returns (navigated, network_failure)."""
        seed = {"make": make, "model": model, "year": year}
        try:
            urls = mod.categories_for(make, model, year, cats)
            net["streak"] = 0
        except Refused:
            raise
        except NetworkError as e:
            net_fail(f"nav {make} {model} {year}", e)
            return False, True  # not marked done: the next slice retries it
        except Exception as e:  # navigation miss: log and move on
            prog["errors"] += 1
            log(f"nav-fail {make} {model} {year}: {type(e).__name__}: {e}")
            write_years(tier, seed, segment, cats, None, f"{type(e).__name__}: {e}")
            return False, False
        write_years(tier, seed, segment, cats, urls, None)
        seed_net_fail = False
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
                    continue  # no manifest line: the seed is retried
                except Exception as e:
                    # The seed is still marked done: fetch.py cached this
                    # response, so a retry in this job would re-read the same
                    # page. The line says read: false (never counts for C2),
                    # and progress list_fail names the page for a completion
                    # row (--complete) in a later run.
                    prog["errors"] += 1
                    log(f"list-fail {list_url}: {type(e).__name__}: {e}")
                    list_line(tier, seed, segment, cat, list_url, [], {}, f"list-fail: {type(e).__name__}: {e}")
                    prog["list_fail"].append({"tier": tier, **seed, "cat": cat, "list_url": list_url,
                                              "error": f"{type(e).__name__}: {e}"[:300]})
                    continue
                pstat: dict[str, str] = {}
                written: list[dict] = []
                try:
                    for p in parts:
                        pkey = f"{cat}|{p['pn']}"
                        if pkey in seen_pn:
                            pstat.setdefault(p["pn"], "seen")
                            continue
                        # a number recorded only as a chain record gets its listed
                        # record now (own seed, list_url and list fields); R6 then
                        # points it at the chain record's line (recrawl_of)
                        chain_first = (cat, norm_pn(p["pn"])) in chain_norm
                        try:
                            prod = mod.product(p["product_url"])
                            net["streak"] = 0
                        except Refused:
                            raise
                        except NetworkError as e:
                            seed_net_fail = True
                            pstat[p["pn"]] = "fail"
                            net_fail(f"product {p['product_url']}", e)
                            continue
                        except Exception as e:
                            prog["errors"] += 1
                            pstat[p["pn"]] = "fail"
                            failed_urls.add(p["product_url"])
                            log(f"product-fail {p['product_url']}: {type(e).__name__}: {e}")
                            continue
                        seen_pn.add(pkey)
                        seen_norm.add((cat, norm_pn(p["pn"])))
                        rec = {"site": site, "category": cat, "seed": seed,
                               "segment": segment, "list_url": list_url, **p, **prod}
                        seen_norm.add((cat, norm_pn(rec["pn"])))
                        n_line = write_record(rec)
                        if chain_first:
                            prog["chain_then_listed"] += 1
                            log(f"listed after chain {cat} {p['pn']}: line {n_line} (recrawl_of {rec.get('recrawl_of')})")
                        pstat[p["pn"]] = "ok"
                        written.append(rec)
                        if covered is not None:
                            for f in prod.get("fitment", []):
                                if same_model(str(f.get("model", "")), model, make):
                                    lo, hi = f["years"]
                                    covered.update(range(lo, hi + 1))
                finally:
                    # R1: one line per list page read, written whether or not its
                    # numbers were seen before (R7), also when the run stops here
                    list_line(tier, seed, segment, cat, list_url, parts, pstat)
                # R4 after the page, so a listed number is recorded with its list
                # row first. Every root is queued (persisted) before any hop is
                # fetched, so a slice that stops here resumes the chains.
                for rec in written:
                    queue_root(rec, cat, seed, segment, list_url)
                for p in parts:  # recorded earlier, chain never followed (e.g. before R4 existed)
                    old_rec = listed_rec.get((cat, norm_pn(p["pn"]))) if pstat.get(p["pn"]) == "seen" else None
                    if old_rec:
                        queue_root(old_rec["rec"], cat, old_rec["seed"], old_rec["segment"], old_rec["list_url"])
                drain_chains()
        return True, seed_net_fail

    finish = False
    try:
        if chains_owed():
            log(f"chain work left by an earlier slice: {len(prog['chain_pending'])} queued records, "
                f"{len(prog['chain_retry'])} hops to retry")
            if not drain_chains(budget=True) or not retry_chains():
                save()
                log(f"time budget reached during chain work records={prog['records']}")
                sys.exit(10)
            save()
        if a.complete:
            rows = _load_completion(a.complete)
            log(f"completion worklist {a.complete}: {len(rows)} rows")
            for r in rows:
                todo = [c for c in r["cats"] if f"C|{r['make']}|{r['model']}|{r['year']}|{c}" not in done]
                if not todo:
                    continue
                if deadline and time.time() > deadline:
                    save()
                    log(f"time budget reached records={prog['records']}")
                    sys.exit(10)
                navigated, failed = visit("C", r["make"], r["model"], r["year"], todo, None, None)
                if not failed:
                    done.update(f"C|{r['make']}|{r['model']}|{r['year']}|{c}" for c in todo)
                else:
                    log(f"completion row {r['make']} {r['model']} {r['year']} had network failures; left open")
                save()
            save()
            log(f"completion finished records={prog['records']} errors={prog['errors']}")
            return
        wl = json.loads((ROOT / "worklist.json").read_text())["sites"][site]["segments"]
        if a.max_segments:
            wl = wl[: a.max_segments]
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
                    navigated, failed = visit(tier, make, model, year, cats, seg["segment"], covered)
                    if not navigated:
                        if not failed:
                            done.add(key)  # navigation miss (no catalog for this year): done
                        continue  # a network failure in navigation is retried next slice
                    if failed:
                        log(f"seed {key} had network failures; left open for retry")
                    else:
                        done.add(key)
                    save()
                    missing = sorted((lot_years - covered) - set(tried))
                    if missing and not seeds:
                        seeds.append(missing[len(missing) // 2])
                log(f"seg done tier={tier} {make} {model} {seg['segment']} seeds={tried} records={prog['records']} errors={prog['errors']}")
        if not a.max_segments and a.tier == "all":
            # .done stops every later run, so chain hops still owed are tried
            # now; if any remain (network), the next slice tries again
            if chains_owed():
                drain_chains(budget=True)
                retry_chains()
            if chains_owed():
                save()
                log(f"worklist finished but {len(prog['chain_pending'])} queued records and "
                    f"{len(prog['chain_retry'])} chain hops are still owed; .done not written (exit 10)")
                sys.exit(10)
            finish = True
    except Refused as e:
        log(f"STOPPED: {e}")
        save()
        if "stopped" in str(e) or "refused or challenged" in str(e) or "robots.txt HTTP" in str(e):
            (raw_dir / f"{site}.blocked").write_text(str(e))
        sys.exit(3)
    except Exception:
        log("CRASH: " + traceback.format_exc())
        save()
        raise
    save()
    if finish:
        (raw_dir / f"{site}.done").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log(f"finished records={prog['records']} errors={prog['errors']} chain_records={prog['chain_records']} "
        f"chain_unlinked={prog['chain_unlinked']} chain_failed={prog['chain_failed']} "
        f"chain_given_up={prog['chain_given_up']}")


if __name__ == "__main__":
    main()
