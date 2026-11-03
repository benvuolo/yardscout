#!/usr/bin/env python3
"""Bevell's Pull It Yourself adapter: page parser, date handling, ids.
Run:  python3 scraper/test_bevells.py   (offline)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


PAGE = """<html><body><div class="wpv-view-output"><table width="100%"><thead><tr>
<th><a href="#">Year<span></span></a></th><th><a>Make</a></th><th><a>Model</a></th><th><a>Row</a></th><th><a>Arrival Date</a></th>
</tr></thead><tbody class="wpv-loop js-wpv-loop">
<tr><td>1998</td><td>CHEVROLET</td><td>S10/S15/SONOMA</td><td>R44-03</td><td>October 30, 2026</td></tr>
<tr><td>2006</td><td>CHEVROLET</td><td>COLORADO</td><td>R44-05</td><td>October 30, 2026</td></tr>
<tr><td>2010</td><td>CHRYSLER</td><td>TOWN &amp; COUNTRY</td><td>R52-07</td><td>September 2, 2026</td></tr>
<tr><td>2013</td><td>FORD</td><td>FOCUS</td><td>R09-17</td><td></td></tr>
<tr><td>n/a</td><td>FORD</td><td>FOCUS</td><td>R09-18</td><td>October 1, 2026</td></tr>
</tbody></table></div></body></html>"""

rows, problem = js._bevells_parse_page(PAGE)
check("parses without a problem", problem == "", problem)
check("four usable rows (the n/a year is skipped)", len(rows) == 4, str(len(rows)))
check("first row", rows[0] == {"year": 1998, "make": "CHEVROLET", "model": "S10/S15/SONOMA", "row": "R44-03", "date": "2026-10-30"}, str(rows[0]))
check("entity in model decoded", rows[2]["model"] == "TOWN & COUNTRY", rows[2]["model"])
check("'September 2, 2026' -> 2026-09-02", rows[2]["date"] == "2026-09-02", rows[2]["date"])
check("blank arrival date -> '' (never invented)", rows[3]["date"] == "")

reordered = PAGE.replace("<th><a href=\"#\">Year<span></span></a></th><th><a>Make</a></th>", "<th><a>Make</a></th><th><a href=\"#\">Year<span></span></a></th>") \
                .replace("<td>1998</td><td>CHEVROLET</td>", "<td>CHEVROLET</td><td>1998</td>")
rows2, _ = js._bevells_parse_page(reordered)
check("header-driven: swapped Year/Make columns still parse", rows2 and rows2[0]["year"] == 1998 and rows2[0]["make"] == "CHEVROLET", str(rows2[:1]))
_, prob = js._bevells_parse_page(PAGE.replace("Model", "Thing"))
check("missing Model header is reported, not guessed", "lack Year/Make/Model" in prob, prob)
_, prob = js._bevells_parse_page("<html>no table</html>")
check("no table is reported", prob == "inventory table not found", prob)

# id stability: same slot + car + date -> same id; new car in the slot -> new id
import hashlib
basis = "|".join(("R44-03", "1998", "CHEVROLET", "S10/S15/SONOMA", "2026-10-30")).lower()
check("id basis is slot|year|make|model|date", hashlib.sha1(basis.encode()).hexdigest()[:12] != hashlib.sha1(basis.replace("1998", "1999").encode()).hexdigest()[:12])
check("registered in INDEPENDENT_FETCHERS", any(n == "Bevell's" for n, _ in js.INDEPENDENT_FETCHERS))
check("yard pin set", js.BEVELLS_YARD["lat"] and js.BEVELLS_YARD["lng"] and js.BEVELLS_YARD["state"] == "NC")

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
