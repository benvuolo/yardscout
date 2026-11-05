#!/usr/bin/env python3
"""Print (or write) the record-level output of the three contract functions on
the real fixture pages, for a given code tree. Used once to capture the
pre-change baseline (golden_records_v0.json) from the commit before the
crawler-requirement changes:

    git archive <sha> scraper/oem_fitment | tar -x -C /tmp/old
    python3 scraper/oem_fitment/tests/fixtures/crawler/snapshot.py --tree /tmp/old/scraper/oem_fitment \
        --out scraper/oem_fitment/tests/fixtures/crawler/golden_records_v0.json

Without --tree it snapshots the current tree. Offline: pages come from
real_pages.json through tests/_crawler_fixtures.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", help="an oem_fitment directory (default: this checkout)")
    ap.add_argument("--out")
    a = ap.parse_args()
    tree = Path(a.tree).resolve() if a.tree else TESTS.parent
    with tempfile.TemporaryDirectory() as td:
        # the helper and fixture travel with the snapshot so an old tree can run them
        shutil.copy(TESTS / "_crawler_fixtures.py", Path(td) / "_crawler_fixtures.py")
        (Path(td) / "fixtures" / "crawler").mkdir(parents=True)
        shutil.copy(HERE / "real_pages.json", Path(td) / "fixtures" / "crawler" / "real_pages.json")
        sys.path[:0] = [td, str(tree)]
        import _crawler_fixtures as F  # noqa: E402
        F.ROOT = tree
        pages = F.Pages(F.real_pages())
        F.install(pages)
        out = F.record_outputs()
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).write_text(text)
        print(f"wrote {a.out}: {len(out['nav'])} navigations, {len(out['lists'])} list calls, {len(out['products'])} products")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
