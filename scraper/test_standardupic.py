#!/usr/bin/env python3
"""Standard Auto Wreckers UPIC Yard (Scarborough / Toronto ON): the reader
loads the yard's page, takes the published sheet that page names, and reads
that. Sheet parsing, ids, VINs, dates, fail-closed cases, name and pin.
Fixtures: scraper/fixtures/standardupic/ (real markup and rows, 2026-11-17).
Run:  python3 scraper/test_standardupic.py   (offline: every request is
served from the fixtures and any other address fails the test)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "standardupic"
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


class FakeResponse:
    def __init__(self, text, status=200):
        self.text, self.status_code, self.content = text, status, text.encode("utf-8")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise js.requests.HTTPError(f"HTTP {self.status_code}")


PAGE = (FIX / "upic-inventory.html").read_text(encoding="utf-8")
CSV = (FIX / "upic-inventory.csv").read_text(encoding="utf-8")
SHEET = js._standardupic_sheet_url(PAGE)
state = {"page": PAGE, "csv": CSV}
calls, sleeps = [], []


def fake_get(url, headers=None, timeout=None, **kw):
    calls.append((url, dict(headers or {})))
    if url == js.STANDARDUPIC_PAGE:
        return FakeResponse(state["page"])
    if url == SHEET:
        return FakeResponse(state["csv"])
    raise AssertionError(f"unexpected request to {url}")


def refuse(*a, **k):
    raise AssertionError(f"unexpected request {a[:1]}")


def big(n):
    """The fixture's header plus n synthetic-numbered copies of its first row
    (only to get past the minimum-row guard; parsing is checked on real rows)."""
    head, first = CSV.splitlines()[0], CSV.splitlines()[1]
    return "\r\n".join([head] + [first.replace("UISUB06371", f"UISUB{90000 + i}") for i in range(n)]) + "\r\n"


real = (js.requests.get, js.requests.post, js._indep_cache_raw, js.time.sleep)
js.requests.get, js.requests.post = fake_get, refuse
js._indep_cache_raw = lambda *a, **k: None
js.time.sleep = lambda s=0, *a: sleeps.append(s)
try:
    check("the page names a sheet the yard published on Google's own host",
          SHEET.startswith("https://docs.google.com/spreadsheets/d/e/") and "output=csv" in SHEET, SHEET)

    # Parsing, on the real rows.
    rows, problem = js._standardupic_parse_csv(CSV)
    check("fixture parses without a problem", problem == "", problem)
    check("12 fixture rows -> 12 cars", len(rows) == 12, len(rows))
    first = rows[0]
    check("first row: id from the stock number", first["id"] == "standardupic-uisub06371", first["id"])
    check("first row: 2006 Subaru Forester, row as the yard writes it",
          (first["year"], first["make"], first["model"], first["row"])
          == (2006, "Subaru", "Forester", "UPIC EAST 12"), first)
    check("Date Created MM/DD/YYYY -> ISO", first["dateAdded"] == "2026-09-03", first["dateAdded"])
    check("17-character VIN kept", first["vin"] == "JF1SG65646H750148", first["vin"])
    novin = [r for r in rows if not r["vin"]]
    check("a row with no VIN keeps an empty VIN (never invented)", len(novin) >= 2, len(novin))
    check("unique ids; every car carries the yard",
          len({r["id"] for r in rows}) == 12
          and all(r["_location"] == "Standard Auto Wreckers UPIC - Toronto" and r["_state"] == "ON"
                  and r["_city"] == "Scarborough" and r["_source"] == "standardupic" for r in rows))
    check("no photo and no colour invented (the sheet has neither filled in)",
          all("_photo" not in r and "_color" not in r for r in rows))
    _, prob = js._standardupic_parse_csv(CSV.replace("Stock #", "Thing"))
    check("a sheet without the Stock # column is reported, not guessed", "lacks" in prob, prob)
    reordered = "Year,Stock #,Model,Make,Date Created\r\n2006,UISUB06371,FORESTER,SUBARU,09/03/2026\r\n"
    r2, _ = js._standardupic_parse_csv(reordered)
    check("header-driven: reordered columns still parse",
          r2 and (r2[0]["year"], r2[0]["make"], r2[0]["model"]) == (2006, "Subaru", "Forester"), r2[:1])
    r3, _ = js._standardupic_parse_csv("Stock #,Year,Make,Model,VIN / Part Type\r\nX1,2001,TOYOTA,WISH,BUMPER\r\n")
    check("a part type in the VIN column is not taken for a VIN", r3 and r3[0]["vin"] == "", r3[:1])

    # The whole reader: two requests, in order, under the scanner's own name.
    state["csv"] = big(60)
    calls.clear()
    out = js.fetch_standardupic_inventory()
    check("two requests: the yard's page, then the sheet that page names",
          [c[0] for c in calls] == [js.STANDARDUPIC_PAGE, SHEET], [c[0] for c in calls])
    uas = {c[1].get("User-Agent") for c in calls}
    check("both requests send the scanner's own name",
          uas == {js.YARDSCOUT_UA} and js.YARDSCOUT_UA.startswith("YardScout/"), uas)
    check("at least 1 s between the two requests", sleeps and min(sleeps) >= 1.0, sleeps)
    check("60 rows -> 60 cars", len(out) == 60, len(out))

    # Fail closed.
    state["csv"] = CSV
    check("a sheet with too few rows publishes nothing (no partial lot)",
          js.fetch_standardupic_inventory() == [])
    state["csv"] = big(60)
    state["page"] = PAGE.replace("docs.google.com/spreadsheets", "example.com/spreadsheets")
    calls.clear()
    check("a page naming a sheet on another host -> no cars",
          js.fetch_standardupic_inventory() == [])
    check("and nothing but the yard's page was requested", [c[0] for c in calls] == [js.STANDARDUPIC_PAGE],
          [c[0] for c in calls])
    state["page"] = "<html><body>Loading inventory…</body></html>"
    check("a page naming no sheet -> no cars (no remembered address is used)",
          js.fetch_standardupic_inventory() == [])
    state["page"] = PAGE

    y = js.STANDARDUPIC_YARD
    check("pin is the map match for 1216 Sewells Rd, Scarborough ON",
          abs(y["lat"] - 43.8436) < 0.002 and abs(y["lng"] + 79.2084) < 0.002 and y["state"] == "ON", y)
    check("registered next to the other independent readers",
          any(fn is js.fetch_standardupic_inventory for _l, fn in js.INDEPENDENT_FETCHERS))
    check("zero-vehicle alarm knows the source", "standardupic" in js.INDEPENDENT_EXPECTED_SOURCES)
finally:
    js.requests.get, js.requests.post, js._indep_cache_raw, js.time.sleep = real

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
