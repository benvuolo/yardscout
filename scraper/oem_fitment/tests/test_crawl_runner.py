#!/usr/bin/env python3
"""crawl.py runner: transient network failures leave the seed open and are
retried on the next run; Refused stops the site; finished runs mark .done.
Offline: a fake site module, a temp ROOT. Run: python3 scraper/oem_fitment/tests/test_crawl_runner.py"""
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import crawl  # noqa: E402
from fetch import NetworkError, Refused  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


state = {"product_calls": 0, "fail_first": True, "refuse": False}
fake = types.ModuleType("sites.fakesite")
fake.SITE = "www.fakesite.com"


def categories_for(make, model, year, cats):
    if state["refuse"]:
        raise Refused("www.fakesite.com refused or challenged (HTTP 403); domain stopped for this program")
    return {"alternator": ["https://www.fakesite.com/list/alt"]} if "alternator" in cats else {}


def parts_on_page(url, cat):
    return [{"pn": "111", "name": "ALTERNATOR", "product_url": "https://www.fakesite.com/p/111"},
            {"pn": "222", "name": "ALTERNATOR REMAN", "product_url": "https://www.fakesite.com/p/222"}]


def product(url):
    state["product_calls"] += 1
    if state["fail_first"] and url.endswith("222"):
        state["fail_first"] = False
        raise NetworkError("network error after 3 tries: ProxyError")
    return {"pn": url.rsplit("/", 1)[1], "description": "x", "position": None, "replaces": [],
            "fitment": [{"years": [2007, 2011], "make": "Toyota", "model": "Camry", "trims": [], "engines": [], "raw": "r"}],
            "evidence_lines": ["2007-2011 Toyota Camry"], "retrieved": "t"}


fake.categories_for, fake.parts_on_page, fake.product = categories_for, parts_on_page, product
sys.modules["sites.fakesite"] = fake

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "worklist.json").write_text(json.dumps({"sites": {"www.fakesite.com": {"segments": [
        {"make": "Toyota", "model": "Camry", "segment": [2007, 2011], "seed_year": 2009, "cars": 100}]}}}))
    crawl.ROOT = root
    crawl.TIERS = {"A": ["alternator"], "B": []}

    def run(*extra):
        sys.argv = ["crawl.py", "--site", "www.fakesite.com", *extra]
        try:
            crawl.main()
            return 0
        except SystemExit as e:
            return e.code

    rc = run("--tier", "A")
    recs = [json.loads(x) for x in (root / "raw" / "www.fakesite.com.jsonl").read_text().splitlines()]
    prog = json.loads((root / "raw" / "www.fakesite.com.progress.json").read_text())
    check("first run finishes (exit 0)", rc == 0, str(rc))
    check("one product saved, the failed one not", [r["pn"] for r in recs] == ["111"], str([r["pn"] for r in recs]))
    check("seed left open after a network failure", not any(k.startswith("A|") for k in prog["done"]), str(prog["done"]))
    rc = run("--tier", "A")
    recs = [json.loads(x) for x in (root / "raw" / "www.fakesite.com.jsonl").read_text().splitlines()]
    prog = json.loads((root / "raw" / "www.fakesite.com.progress.json").read_text())
    check("rerun fetches only the missing product", [r["pn"] for r in recs] == ["111", "222"], str([r["pn"] for r in recs]))
    check("seed done after a clean rerun", "A|Toyota|Camry|2009" in prog["done"], str(prog["done"]))
    check("no .blocked for a network error", not (root / "raw" / "www.fakesite.com.blocked").exists())
    rc = run()  # tier all: A done, B empty -> finished
    check("full pass marks .done", (root / "raw" / "www.fakesite.com.done").exists(), str(rc))
    (root / "raw" / "www.fakesite.com.done").unlink()
    (root / "raw" / "www.fakesite.com.progress.json").unlink()
    state["refuse"] = True
    rc = run("--tier", "A")
    check("Refused stops the site with exit 3 and writes .blocked", rc == 3 and (root / "raw" / "www.fakesite.com.blocked").exists(), str(rc))
    rc = run("--tier", "A")
    check("blocked site refuses to start", rc == 3, str(rc))

check("same_model: spacing", crawl.same_model("Mazda 3", "Mazda3", "Mazda"))
check("same_model: series suffix", crawl.same_model("Silverado", "Silverado 1500", "Chevrolet"))
check("same_model: hybrid under base", crawl.same_model("Camry", "Camry Hybrid", "Toyota"))
check("same_model: different models", not crawl.same_model("Corolla", "Camry", "Toyota"))
check("same_model: too-short prefix refused", not crawl.same_model("RX", "RX-8", "Mazda") or crawl.same_model("RX-8", "RX-8", "Mazda"))

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
