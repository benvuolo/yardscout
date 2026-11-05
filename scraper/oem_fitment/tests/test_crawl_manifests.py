#!/usr/bin/env python3
"""crawl.py end to end on fixture pages (no network, temp ROOT): the R1 list
manifest, R2 year manifest, R3 completion mode, R4 chain records, R6
recrawl_of, size-capped file parts, torn-tail healing, and that manifests add
no request. Pages: tests/_synthetic_pages.py (2030 Camry on toyotapartsnow,
2030 Malibu on gmpartsgiant) through the real site modules.
Run: python3 scraper/oem_fitment/tests/test_crawl_manifests.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _crawler_fixtures as F  # noqa: E402
import _synthetic_pages as S  # noqa: E402

import crawl  # noqa: E402

fails: list[str] = []
n = 0


def check(name: str, ok, detail="") -> None:
    global n
    n += 1
    if not ok:
        fails.append(name)
        print(f"FAIL  {name} — {detail}")


TY, GM = "www.toyotapartsnow.com", "www.gmpartsgiant.com"
L = f"{S.T}/parts-list/{S.TSTEM}"
P = f"{S.T}/oem/toyota"
WORKLIST = {"sites": {
    TY: {"segments": [{"make": "Toyota", "model": "Camry", "segment": [2030, 2030], "seed_year": 2030, "cars": 1}]},
    GM: {"segments": [{"make": "Chevrolet", "model": "Malibu", "segment": [2030, 2030], "seed_year": 2030, "cars": 1}]},
    "www.wrapsite.com": {"segments": [{"make": "Toyota", "model": "Camry", "segment": [2030, 2030], "seed_year": 2030}]},
    "www.mbpartsgiant.com": {"segments": [{"make": "Mercedes-Benz", "model": "C-Class", "segment": [2030, 2030],
                                           "seed_year": 2030}]},
    "www.volvopartsgiant.com": {"segments": [{"make": "Volvo", "model": "XC90", "segment": [2030, 2030], "seed_year": 2030}]},
}}


def fresh_pages() -> F.Pages:
    pages = F.Pages(S.toyota_pages(), S.gm_pages(), S.volvo_pages(), S.mb_pages())
    # one more headlights page on the 2030 year page, answering 404 (list-fail)
    y = f"{S.T}/catalog/{S.TSTEM}-parts"
    pages.pages[y]["html"] = pages.pages[y]["html"].replace(
        "<script>", f'<a href="/parts-list/{S.TSTEM}/headlights-lighting/headlamp-components">x</a><script>', 1)
    pages.pages[f"{L}/headlights-lighting/headlamp-components"] = F.page("<html>gone</html>", status=404)
    F.install(pages)
    return pages


def run(root: Path, *argv: str) -> int:
    crawl.ROOT = root
    sys.argv = ["crawl.py", *argv]
    try:
        crawl.main()
        return 0
    except SystemExit as e:
        return int(e.code or 0)


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


crawl.TIERS = {"A": ["alternator", "starter", "side-mirrors", "headlights"], "B": []}

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    rc = run(root, "--site", TY, "--tier", "A")
    raw = root / "raw"
    recs = jl(raw / f"{TY}.jsonl")
    lists = jl(raw / f"{TY}.lists.jsonl")
    years = jl(raw / f"{TY}.years.jsonl")
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    check("toyota run exits 0", rc == 0, rc)
    listed = [r["pn"] for r in recs if "via" not in r]
    chained = {r["pn"]: r for r in recs if "via" in r}
    check("records: listed parts", listed == ["27060-90010", "27060-90005", "28100-90010-84", "28100-90020-84",
                                              "28100-90010", "87910-90010", "87940-90010", "81110-90010"], listed)
    check("R4 chain records", sorted(chained) == ["27060-89990", "28100-90030"], sorted(chained))
    c1, c2 = chained.get("27060-89990", {}), chained.get("28100-90030", {})
    check("R4 via a list-row link", c1.get("via") == "replaces:27060-90010" and c1.get("via_link") == "list_row"
          and c1.get("via_depth") == 1 and c1.get("via_root") == "27060-90010" and c1.get("name") is None
          and c1.get("product_url") == f"{P}~alternator-kit~27060-89990" and c1.get("category") == "alternator", c1)
    check("R4 via a product-page link", c2.get("via") == "replaces:28100-90010-84" and c2.get("via_link") == "product_page"
          and c2.get("category") == "starter" and c2.get("fitment"), c2)
    check("R4 no list fields on chain records", not any(k.startswith("list_") and k != "list_url" for k in c2), sorted(c2))
    check("R4 unlinked successor counted, not fetched", prog["chain_unlinked"] == 1 and prog["chain_records"] == 2,
          (prog["chain_unlinked"], prog["chain_records"]))
    check("R4 never a constructed URL", not any("28100-90040" in u for u in pages.gets()))
    check("R6 no recrawl_of on a first crawl", not any("recrawl_of" in r for r in recs))

    # R1
    check("R1 one line per list page read (incl. the 404)", [ln["list_url"].rsplit("/", 1)[1] for ln in lists]
          == ["alternator", "starter", "outside-mirrors", "headlamp-components", "headlamps"],
          [ln["list_url"] for ln in lists])
    by_url = {ln["list_url"]: ln for ln in lists}
    a = by_url[f"{L}/charging-starting/alternator"]
    check("R1 line fields", a["kind"] == "list" and a["site"] == TY and a["tier"] == "A" and a["cat"] == "alternator"
          and a["seed"] == {"make": "Toyota", "model": "Camry", "year": 2030} and a["segment"] == [2030, 2030]
          and a["status"] == 200, {k: v for k, v in a.items() if k != "rows"})
    check("R1 every row", len(a["rows"]) == 9)
    st = {r["pn"]: (r["matched"], r["excluded_by"], r["product"]) for r in a["rows"]}
    check("R1 product status per matched row", st["27060-90010"] == (True, None, "ok") and st["27060-90005"] == (True, None, "ok")
          and st["27060-90010-84"] == (False, "reman_dropped", None) and st["27060-89990"] == (False, "rule:kit", None), st)
    fail404 = by_url[f"{L}/headlights-lighting/headlamp-components"]
    check("R1 list-fail line kept with status and error", fail404["status"] == 404 and fail404["rows"] == []
          and "list-fail" in fail404["error"], fail404)
    check("R1 read flag: true on clean pages, false on the 404", fail404.get("read") is False
          and all(ln.get("read") is True for ln in lists if ln is not fail404), [(ln["list_url"], ln.get("read")) for ln in lists])
    check("list-fail page named in progress", [(x["year"], x["cat"], x["list_url"]) for x in prog.get("list_fail", [])]
          == [(2030, "headlights", f"{L}/headlights-lighting/headlamp-components")], prog.get("list_fail"))
    check("every listed record's chain was queued and worked", prog.get("chain_pending") == [] and len(prog.get("chain_followed", [])) == 8)

    # R2
    check("R2 one year line", len(years) == 1)
    y = years[0] if years else {}
    check("R2 year line", y.get("kind") == "year" and y.get("nav") == "ok" and y.get("status") == 200
          and y.get("tier") == "A" and y.get("cats") == crawl.TIERS["A"] and len(y.get("subs", [])) == 6, y)
    check("R2 pages read, per category", y.get("pages", {}).get("headlights") == [
        f"{L}/headlights-lighting/headlamp-components", f"{L}/headlights-lighting/headlamps"]
        and y["pages"]["alternator"] == [f"{L}/charging-starting/alternator"], y.get("pages"))

    # no extra requests: every page fetched exactly once, manifests only re-read the cache
    gets = pages.gets()
    want = {f"{S.T}/catalog/{S.TSTEM}-parts", f"{L}/charging-starting/alternator", f"{L}/charging-starting/starter",
            f"{L}/body-hardware/outside-mirrors", f"{L}/headlights-lighting/headlamp-components",
            f"{L}/headlights-lighting/headlamps"} | {r["product_url"] for r in recs}
    check("no extra requests", set(gets) == want and len(gets) == len(set(gets)),
          (sorted(set(gets) ^ want), len(gets), len(set(gets))))

    # resume: nothing left to do, nothing written, no request
    before = (len(recs), len(lists), len(years), len(gets))
    rc = run(root, "--site", TY, "--tier", "A")
    after = (len(jl(raw / f"{TY}.jsonl")), len(jl(raw / f"{TY}.lists.jsonl")), len(jl(raw / f"{TY}.years.jsonl")),
             len(pages.gets()))
    check("resume: no new lines, no requests", rc == 0 and after == before, (before, after))

    # R6: progress reset -> every record written again names the line it re-crawls
    (raw / f"{TY}.progress.json").unlink()
    rc = run(root, "--site", TY, "--tier", "A")
    recs2 = jl(raw / f"{TY}.jsonl")
    new = recs2[len(recs):]
    first_line = {(r["category"], r["pn"]): i + 1 for i, r in enumerate(recs)}
    check("R6 the re-crawl writes every record again", len(new) == len(recs), (len(new), len(recs)))
    check("R6 recrawl_of = line of the earlier record", all(r.get("recrawl_of") == str(first_line[(r["category"], r["pn"])])
                                                           for r in new), [(r["pn"], r.get("recrawl_of")) for r in new])
    check("R1/R2 written again on the re-crawl", len(jl(raw / f"{TY}.lists.jsonl")) == 2 * len(lists)
          and len(jl(raw / f"{TY}.years.jsonl")) == 2)

    # torn tail: a killed writer's half line is cut before the next append
    with open(raw / f"{TY}.jsonl", "a") as fh:
        fh.write('{"site": "www.toyotapartsnow.com", "category": "alt')
    (raw / f"{TY}.progress.json").unlink()
    rc = run(root, "--site", TY, "--tier", "A")
    lines = (raw / f"{TY}.jsonl").read_text().splitlines()
    check("torn last line healed", all(ln.startswith("{") and ln.endswith("}") for ln in lines)
          and len(lines) == 3 * len(recs), len(lines))
    check("heal is logged", "healed torn last line" in (raw / f"{TY}.log").read_text())

    # PartsGiant (gmpartsgiant): two variant catalogs, R5b, chain via product page
    crawl.TIERS = {"A": ["alternator", "headlights"], "B": []}
    rc = run(root, "--site", GM, "--tier", "A")
    grecs = jl(raw / f"{GM}.jsonl")
    glists = jl(raw / f"{GM}.lists.jsonl")
    gyears = jl(raw / f"{GM}.years.jsonl")
    check("GM run exits 0", rc == 0, rc)
    check("GM records", [(r["pn"], r.get("via")) for r in grecs] == [
        ("19000001", None), ("19000003", None), ("19000002", None), ("19000000", "replaces:19000002"), ("95291999", None)],
        [(r["pn"], r.get("via")) for r in grecs])
    check("GM records carry reman", [r.get("reman") for r in grecs if "via" not in r] == [False, True, False, False])
    check("GM year lines per catalog with their pages", [(x["variant"], sorted(x["pages"])) for x in gyears] == [
        ("", ["alternator", "headlights"]), ("new_model", ["alternator"])], [(x["variant"], x["pages"]) for x in gyears])
    check("GM year lines list every offered variant", gyears[0]["variants"][:3] == ["new_model", "", "eco"]
          and gyears[0]["variants_read"] == ["", "new_model"])
    check("GM list lines", [(x["variant"], x["cat"], len(x["rows"])) for x in glists] == [
        ("", "alternator", 5), ("new_model", "alternator", 2), ("", "headlights", 2)],
        [(x["variant"], x["cat"], len(x["rows"])) for x in glists])
    nm = {r["pn"]: r for r in glists[1]["rows"]}
    check("GM reman_dropped beside a new number", nm["19000004"]["excluded_by"] == "reman_dropped"
          and nm["19000002"]["product"] == "ok")

    # a site module that adds / drops rows after the template (Honda-style wrapper)
    from sites import toyotapartsnow as T  # noqa: E402
    wrap = types.ModuleType("sites.wrapsite")
    wrap.SITE = "www.wrapsite.com"
    wrap.categories_for = lambda make, model, year, cats: {"alternator": [f"{L}/charging-starting/alternator"]} \
        if "alternator" in cats else {}

    def wrapped_parts(url, cat):
        out = [p for p in T.parts_on_page(url, cat) if p["pn"] != "27060-90005"]
        return out + [{"pn": "27060-89990", "name": "Alternator Kit", "product_url": f"{P}~alternator-kit~27060-89990"}]
    wrap.parts_on_page = wrapped_parts
    wrap.product = T.product
    wrap.year_manifest = T.year_manifest
    wrap.list_manifest = T.list_manifest
    sys.modules["sites.wrapsite"] = wrap
    crawl.TIERS = {"A": ["alternator"], "B": []}
    rc = run(root, "--site", "www.wrapsite.com", "--tier", "A")
    wl = jl(raw / "www.wrapsite.com.lists.jsonl")
    wr = {r["pn"]: r for r in wl[0]["rows"]} if wl else {}
    check("module-added row is matched in the manifest", wr.get("27060-89990", {}).get("matched") is True
          and wr["27060-89990"].get("matched_by") == "site_module" and wr["27060-89990"].get("excluded_by") is None, wr.get("27060-89990"))
    check("module-dropped row is not matched", wr.get("27060-90005", {}).get("matched") is False
          and wr["27060-90005"].get("excluded_by") == "site_module", wr.get("27060-90005"))

# size-capped parts: one logical file, global line numbers, R6 pointers across parts
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    fresh_pages()
    crawl.TIERS = {"A": ["alternator", "starter", "side-mirrors", "headlights"], "B": []}
    old_cap = crawl.PART_BYTES
    crawl.PART_BYTES = 6000
    run(root, "--site", TY, "--tier", "A")
    (root / "raw" / f"{TY}.progress.json").unlink()
    run(root, "--site", TY, "--tier", "A")
    crawl.PART_BYTES = old_cap
    raw = root / "raw"
    rparts = sorted(raw.glob(f"{TY}.*jsonl"))
    rec_parts = [raw / f"{TY}.jsonl"] + sorted(raw.glob(f"{TY}.[0-9]*.jsonl"), key=lambda p: int(p.name.split(".")[-2]))
    list_parts = [raw / f"{TY}.lists.jsonl"] + sorted(raw.glob(f"{TY}.lists.[0-9]*.jsonl"),
                                                       key=lambda p: int(p.name.split(".")[-2]))
    check("records split into parts", len(rec_parts) >= 3, [p.name for p in rparts])
    check("lists split into parts", len(list_parts) >= 3, [p.name for p in list_parts])
    check("no part over the cap unless one line is", all(p.stat().st_size <= 6000 or len(p.read_text().splitlines()) == 1
                                                          for p in rec_parts + list_parts))
    logical = [json.loads(x) for p in rec_parts for x in p.read_text().splitlines()]
    rf = crawl.RawFile(raw, TY)
    check("RawFile reads the parts in order", [r for _, r in rf.rows()] == logical and rf.lines == len(logical))
    half = len(logical) // 2
    check("R6 pointers are global line numbers", all(logical[int(r["recrawl_of"]) - 1]["pn"] == r["pn"]
                                                     for r in logical[half:]) and all("recrawl_of" in r for r in logical[half:]))

# R4 chain hop with a network failure: queued in progress, fetched at the next start
with tempfile.TemporaryDirectory() as td:
    from fetch import NetworkError  # noqa: E402
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    crawl.TIERS = {"A": ["starter"], "B": []}
    flaky = {f"{P}~starter~28100-90030": 1}
    real_get = pages.get

    def flaky_get(url):
        if flaky.get(url):
            flaky[url] -= 1
            pages.calls.append(("get", url))
            raise NetworkError("network error after 3 tries: ProxyError")
        return real_get(url)
    from sites import _simplepart  # noqa: E402
    _simplepart.get = flaky_get
    run(root, "--site", TY, "--tier", "A")
    raw = root / "raw"
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    pns = [r["pn"] for r in jl(raw / f"{TY}.jsonl")]
    check("chain hop failure queued, seed still done", len(prog["chain_retry"]) == 1 and "28100-90030" not in pns
          and "A|Toyota|Camry|2030" in prog["done"], (prog["chain_retry"], pns))
    run(root, "--site", TY, "--tier", "A")
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    recs = jl(raw / f"{TY}.jsonl")
    c = [r for r in recs if r["pn"] == "28100-90030"]
    check("chain hop retried at the next start", prog["chain_retry"] == [] and len(c) == 1
          and c[0]["via"] == "replaces:28100-90010-84" and c[0]["via_depth"] == 1 and c[0]["via_link"] == "product_page",
          (prog["chain_retry"], c[:1]))
    check("retried hop continues the chain", "chain-unlinked starter 1 numbers named by 28100-90030, no catalog link: 28100-90040" in (raw / f"{TY}.log").read_text())


def flaky(pages: F.Pages, counts: dict) -> None:
    """Make _simplepart.get raise NetworkError for the next counts[url] fetches of url."""
    from sites import _simplepart  # noqa: E402
    real_get = pages.get

    def get(url):
        if counts.get(url):
            counts[url] -= 1
            pages.calls.append(("get", url))
            raise NetworkError("network error after 3 tries: ReadTimeout")
        return real_get(url)
    _simplepart.get = get


# .done is not written while a chain hop is owed: the hop is retried at the end
# of the run, then at the next start, and given up after CHAIN_TRIES attempts
for fails_, want in ((2, "recovers"), (99, "given up")):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "worklist.json").write_text(json.dumps(WORKLIST))
        pages = fresh_pages()
        crawl.TIERS = {"A": ["starter"], "B": []}
        hop = f"{P}~starter~28100-90030"
        flaky(pages, {hop: fails_})
        raw = root / "raw"
        rc1 = run(root, "--site", TY)  # the workflow's invocation: tier all, no --max-segments
        prog = json.loads((raw / f"{TY}.progress.json").read_text())
        check(f"[{want}] hop owed after the worklist: exit 10, no .done", rc1 == 10 and not (raw / f"{TY}.done").exists()
              and [(h["pn"], h.get("tries")) for h in prog["chain_retry"]] == [("28100-90030", 2)], (rc1, prog["chain_retry"]))
        rc2 = run(root, "--site", TY)
        prog = json.loads((raw / f"{TY}.progress.json").read_text())
        got = [r for r in jl(raw / f"{TY}.jsonl") if r["pn"] == "28100-90030"]
        check(f"[{want}] next slice: .done once nothing is owed", rc2 == 0 and (raw / f"{TY}.done").exists()
              and prog["chain_retry"] == [] and prog.get("chain_pending") == [], (rc2, prog["chain_retry"]))
        if want == "recovers":
            check("[recovers] the hop is recorded", len(got) == 1 and got[0]["via"] == "replaces:28100-90010-84", got)
        else:
            check("[given up] counted and logged, never recorded", not got and prog.get("chain_given_up") == 1
                  and "chain-given-up starter 28100-90030 after 3 network failures" in (raw / f"{TY}.log").read_text()
                  and pages.gets().count(hop) == 3, (prog.get("chain_given_up"), pages.gets().count(hop)))

# A network streak mid-chain: the root stays queued (chain_pending), so the next
# slice tries every target, including the ones never reached before the exit
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    olds = [f"27060-8{i}000" for i in range(1, 7)]
    pages.pages[f"{P}~alternator~27060-90010"] = S.sp_product("27060-90010", "Alternator", replaces=", ".join(olds))
    altp = pages.pages[f"{L}/charging-starting/alternator"]
    from sites._simplepart import store as sp_store  # noqa: E402
    st_ = sp_store(altp["html"])
    st_["partList"]["gpgOnlyPartList"][0] += [S._sp_row(pn, "Alternator Kit", None) for pn in olds]
    altp["html"] = F.store_html(st_)
    for pn in olds:
        pages.pages[f"{P}~alternator-kit~{pn}"] = S.sp_product(pn, "Alternator", replaced_by="27060-90010")
    flaky(pages, {f"{P}~alternator-kit~{pn}": 1 for pn in olds[:5]})
    crawl.TIERS = {"A": ["alternator"], "B": []}
    raw = root / "raw"
    rc1 = run(root, "--site", TY, "--tier", "A")
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    check("streak mid-chain: exit 11, root still queued, 6th target untried",
          rc1 == 11 and [e["rec"]["pn"] for e in prog.get("chain_pending", [])][:1] == ["27060-90010"]
          and f"{P}~alternator-kit~27060-86000" not in pages.gets(), (rc1, prog.get("chain_pending", [])[:1]))
    rc2 = run(root, "--site", TY, "--tier", "A")
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    chained_ = sorted(r["pn"] for r in jl(raw / f"{TY}.jsonl") if "via" in r and r["pn"] in olds)
    check("next slice: every target recorded, nothing owed, seed done", rc2 == 0 and chained_ == olds
          and prog.get("chain_pending") == [] and prog["chain_retry"] == [] and "A|Toyota|Camry|2030" in prog["done"],
          (rc2, chained_, prog.get("chain_pending"), prog["chain_retry"]))

# --complete follows the chains of records written before R4 existed
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    crawl.TIERS = {"A": ["alternator", "starter"], "B": []}
    raw = root / "raw"
    old_depth, crawl.CHAIN_DEPTH = crawl.CHAIN_DEPTH, 0  # stands in for main's crawl.py (no R4)
    run(root, "--site", TY, "--tier", "A")
    crawl.CHAIN_DEPTH = old_depth
    pp = raw / f"{TY}.progress.json"
    prog = json.loads(pp.read_text())
    for k in ("chain_followed", "chain_seen", "chain_pending", "chain_retry"):
        prog.pop(k, None)
    pp.write_text(json.dumps(prog))
    (raw / f"{TY}.lists.jsonl").unlink()  # main wrote no manifests
    check("pre-R4 stand-in wrote no chain records", not any("via" in r for r in jl(raw / f"{TY}.jsonl")))
    wl = root / "c.json"
    wl.write_text(json.dumps([{"make": "Toyota", "model": "Camry", "year": 2030, "cats": ["alternator", "starter"]}]))
    rc = run(root, "--site", TY, "--complete", str(wl))
    recs = jl(raw / f"{TY}.jsonl")
    prog = json.loads(pp.read_text())
    ch = {r["pn"]: r for r in recs if "via" in r}
    check("--complete: chains of 'seen' rows followed", rc == 0 and sorted(ch) == ["27060-89990", "28100-90030"]
          and prog["chain_records"] == 2, (rc, sorted(ch)))
    check("--complete: chain records take the root record's seed and list_url",
          ch.get("27060-89990", {}).get("list_url") == f"{L}/charging-starting/alternator"
          and ch.get("28100-90030", {}).get("via") == "replaces:28100-90010-84")
    check("--complete: listed records not written again", sum(1 for r in recs if "via" not in r) == 5)

# F1: a number first reached as a chain member, listed later on another seed,
# gets its own listed record (own seed, list_url, list fields), pointing at
# the chain record through recrawl_of
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    wlx = {"sites": {TY: {"segments": [
        {"make": "Toyota", "model": "Camry", "segment": [2030, 2030], "seed_year": 2030},
        {"make": "Toyota", "model": "Camry", "segment": [2031, 2031], "seed_year": 2031}]}}}
    (root / "worklist.json").write_text(json.dumps(wlx))
    pages = fresh_pages()
    L31 = f"{S.T}/parts-list/2031-toyota-camry"
    pages.pages[f"{S.T}/catalog/2031-toyota-camry-parts"] = F.page(F.store_html(
        {}, '<a href="/parts-list/2031-toyota-camry/charging-starting/alternator">x</a>', title="2031 Toyota Camry Parts"))
    pages.pages[f"{L31}/charging-starting/alternator"] = S.sp_list([
        S._sp_row("27060-89990", "Alternator", "Alternator Assembly, With Regulator", url="/oem/toyota~alternator-kit~27060-89990",
                  notes="3.5L; Reman Core", location="Front")])
    crawl.TIERS = {"A": ["alternator"], "B": []}
    raw = root / "raw"
    rc = run(root, "--site", TY, "--tier", "A")
    recs = jl(raw / f"{TY}.jsonl")
    lines_ = jl(raw / f"{TY}.lists.jsonl")
    r89 = [(i + 1, r) for i, r in enumerate(recs) if r["pn"] == "27060-89990"]
    check("chain record first, listed record second", rc == 0 and [("via" in r) for _, r in r89] == [True, False],
          [(i, r.get("via"), r["seed"]["year"]) for i, r in r89])
    if len(r89) == 2:
        (cl, crec_), (_, lrec) = r89
        check("listed record has its own seed, list_url and list fields",
              lrec["seed"]["year"] == 2031 and lrec["list_url"] == f"{L31}/charging-starting/alternator"
              and lrec["name"] == "Alternator" and lrec["list_section"] == "diagram"
              and lrec["list_notes"] == ["3.5L; Reman Core"] and lrec["list_location"] == ["Front"]
              and lrec["reman"] is True and lrec["recrawl_of"] == str(cl), lrec)
        check("chain record unchanged (root's seed)", crec_["seed"]["year"] == 2030 and crec_["name"] is None)
    l31 = [ln for ln in lines_ if ln["seed"]["year"] == 2031]
    check("2031 list line: product ok, not seen", [(r["pn"], r["product"]) for r in l31[0]["rows"]] == [("27060-89990", "ok")]
          if l31 else False, l31)
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    check("counted and logged", prog.get("chain_then_listed") == 1
          and "listed after chain alternator 27060-89990" in (raw / f"{TY}.log").read_text())
    check("its product page is read again for the listed record (a fetch.py cache hit within one job)",
          pages.gets().count(f"{P}~alternator-kit~27060-89990") == 2)

# F3: a list page that answers 200 but does not parse, and a product-rule fetch
# that fails on a 200 list page: read false, rows not relabelled site_module
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    pages.pages[f"{L}/charging-starting/starter"] = F.page("<html><body>Please try again later</body></html>")
    crawl.TIERS = {"A": ["alternator", "starter"], "B": []}
    raw = root / "raw"
    rc = run(root, "--site", TY, "--tier", "A")
    ls = {ln["cat"]: ln for ln in jl(raw / f"{TY}.lists.jsonl")}
    s_ = ls.get("starter", {})
    check("200 error page: line kept, status 200, read false", rc == 0 and s_.get("status") == 200 and s_.get("read") is False
          and s_.get("rows") == [] and "list-fail: NavError" in s_.get("error", ""), s_)
    check("200 error page: alternator line still read", ls.get("alternator", {}).get("read") is True)
    VOS = "www.volvopartsgiant.com"
    pages.pages[f"{S.V}/genuine/volvo~door-shell~31335410"] = F.page("<html>gone</html>", status=404)
    crawl.TIERS = {"A": [], "B": ["door-front"]}
    rc = run(root, "--site", VOS, "--tier", "B")
    vl = jl(raw / f"{VOS}.lists.jsonl")
    vr = {r["pn"]: (r["matched"], r["excluded_by"], r["product"]) for r in vl[0]["rows"]} if vl else {}
    check("product-rule fetch failed: read false, template verdicts kept, no site_module",
          rc == 0 and vl[0]["status"] == 200 and vl[0].get("read") is False and "list-fail" in vl[0]["error"]
          and vr == {"31335409": (True, None, "not_attempted"), "31335410": (False, "product_rule_unchecked", None),
                     "31335411": (False, "rule:slug_miss", None), "31335412": (False, "include_miss", None)}, (vl[:1], vr))
    check("no record from a failed page", not (raw / f"{VOS}.jsonl").exists() or jl(raw / f"{VOS}.jsonl") == [])

# main's SimplePart "giant" modules (Mercedes badges, Volvo slug-checked) write full manifests
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    MBS, VOS = "www.mbpartsgiant.com", "www.volvopartsgiant.com"
    ML = f"{S.M}/parts-list/2030-mercedes_benz"
    crawl.TIERS = {"A": ["alternator"], "B": []}
    rc = run(root, "--site", MBS, "--tier", "A")
    raw = root / "raw"
    log = (raw / f"{MBS}.log").read_text()
    my, ml_ = jl(raw / f"{MBS}.years.jsonl"), jl(raw / f"{MBS}.lists.jsonl")
    check("MB crawl exits 0, no missing-manifest warning", rc == 0 and "has no year_manifest" not in log, (rc, log[-300:]))
    check("MB year lines: one per badge read, pages placed", [(x["variant"], x["status"], x["pages"], x.get("error"))
                                                              for x in my] == [
        ("c300", 200, {"alternator": [f"{ML}-c300/charging-starting/alternator"]}, None),
        ("c63_amg", 200, {"alternator": [f"{ML}-c63_amg/charging-starting/alternator"]}, None)]
        and "pages_unplaced" not in my[0], my)
    check("MB list lines carry rows", [(x["variant"], len(x["rows"]), x.get("error"), x.get("read")) for x in ml_]
          == [("c300", 2, None, True), ("c63_amg", 1, None, True)], [(x.get("variant"), x.get("error")) for x in ml_])
    check("MB the shared number is fetched once, listed on both badges",
          [r["pn"] for r in jl(raw / f"{MBS}.jsonl")] == ["272-154-00-02"]
          and [[(r["pn"], r["product"]) for r in x["rows"] if r["matched"]] for x in ml_]
          == [[("272-154-00-02", "ok")], [("272-154-00-02", "seen")]], [x["rows"] for x in ml_])
    crawl.TIERS = {"A": [], "B": ["door-front", "door-rear"]}
    rc = run(root, "--site", VOS, "--tier", "B")
    vl = jl(raw / f"{VOS}.lists.jsonl")
    check("Volvo product-rule categories: list lines with rows, no manifest error",
          rc == 0 and [(x["cat"], len(x["rows"]), x.get("error")) for x in vl] == [("door-front", 4, None), ("door-rear", 4, None)],
          [(x["cat"], len(x["rows"]), x.get("error")) for x in vl])
    check("Volvo slug miss in the crawl manifest", {r["pn"]: r["excluded_by"] for r in vl[0]["rows"]}["31335411"] == "rule:slug_miss")
    check("Volvo door records", [(r["category"], r["pn"]) for r in jl(raw / f"{VOS}.jsonl")]
          == [("door-front", "31335409"), ("door-rear", "31335410")])

# R3 completion mode
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps(WORKLIST))
    pages = fresh_pages()
    wl = root / "toyota.completion.json"
    wl.write_text(json.dumps({"rows": [{"make": "Toyota", "model": "Camry", "year": 2030, "cats": ["alternator", "starter"]},
                                       {"make": "Toyota", "model": "Camry", "year": 2031, "cats": ["alternator"]}]}))
    rc = run(root, "--site", TY, "--complete", str(wl))
    raw = root / "raw"
    recs = jl(raw / f"{TY}.jsonl")
    prog = json.loads((raw / f"{TY}.progress.json").read_text())
    ylines = jl(raw / f"{TY}.years.jsonl")
    check("R3 completion run exits 0", rc == 0, rc)
    check("R3 records for the asked categories only", {r["category"] for r in recs} == {"alternator", "starter"})
    check("R3 progress keys per row and category", {"C|Toyota|Camry|2030|alternator", "C|Toyota|Camry|2030|starter",
                                                     "C|Toyota|Camry|2031|alternator"} <= set(prog["done"]), prog["done"])
    check("R3 lines marked tier C", all(x["tier"] == "C" for x in jl(raw / f"{TY}.lists.jsonl") + ylines))
    check("R3 nav-fail year line", [(x["seed"]["year"], x["nav"]) for x in ylines] == [(2030, "ok"), (2031, "fail")]
          and ylines[1]["error"] == "not_fetched" and ylines[1].get("nav_error"), ylines[1:])
    g1 = len(pages.gets())
    rc = run(root, "--site", TY, "--complete", str(wl))
    check("R3 rerun: nothing left, no request", rc == 0 and len(pages.gets()) == g1 and len(jl(raw / f"{TY}.jsonl")) == len(recs))
    check("R3 never marks .done", not (raw / f"{TY}.done").exists())

# helpers
check("url_names_pn shapes", crawl.url_names_pn("/oem/toyota~starter~28100-90030", "28100-90030")
      and crawl.url_names_pn("/parts/ford-alternator-assy_f7pz-10346-karm.html", "F7PZ-10346-KARM")
      and crawl.url_names_pn("/parts/gm-generator-asm-13597227.html", "13597227")
      and not crawl.url_names_pn("/parts/gm-generator-asm-113597227.html", "13597227")
      and not crawl.url_names_pn("/oem/toyota~starter~28100-90031", "28100-90030"))
check("chain_targets", crawl.chain_targets({"pn": "A1", "replaces": ["B2", "A1"], "replaced_by": "C3; (MultiSupersession)",
                                             "list_info": ["Replaced By: D4", "Location: Left"]})
      == [("replaces", "B2"), ("replaced_by", "C3"), ("replaced_by", "D4")])

print(f"\n{'OK' if not fails else 'FAILED'}: {n - len(fails)}/{n} checks" + (f"; failing: {fails}" if fails else ""))
sys.exit(1 if fails else 0)
