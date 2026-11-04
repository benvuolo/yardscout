#!/usr/bin/env python3
"""OKC Pull-A-Part adapter (pullapartokc.com): form parsing, result table,
ids, no invented dates, partial-lot guard, registration.
Run:  python3 scraper/test_okcpap.py   (offline)"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" — {detail}"))
    if not ok:
        fails.append(name)


HOME = """<form method="post" action="./" id="logbg">
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPabc" />
<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="90059987" />
<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="/wEdA&amp;x" />
<select name="ddlMake" id="ddlMake"><option value="SELECT MAKE">SELECT MAKE</option><option value="FORD">FORD</option>
<option value="HONDA">HONDA</option><option value="LAND ROVER">LAND ROVER</option></select>
<select name="ddlModel" id="ddlModel"><option value="SELECT MODEL">SELECT MODEL</option><option value="200">200</option>
<option value="ACCORD">ACCORD</option></select></form>"""

RESULT = """<table><tr><td>Yard Hours</td></tr></table>
<table cellspacing="0" rules="all" border="1" id="GridView1">
<tr><th scope="col">Year</th><th scope="col">Make</th><th scope="col">Model</th><th scope="col">Row</th></tr>
<tr><td>2004</td><td>HONDA</td><td>ACCORD</td><td>300</td></tr>
<tr><td>2003</td><td>HONDA</td><td>ACCORD</td><td>301</td></tr>
<tr><td>2003</td><td>HONDA</td><td>ACCORD</td><td>301</td></tr>
<tr><td>n/a</td><td>HONDA</td><td>CIVIC</td><td>302</td></tr>
<tr><td>2006</td><td>HONDA</td><td>CR-V</td><td>304</td></tr>
</table>"""

hidden, makes, any_model = js._okcpap_form(HOME)
check("form: hidden fields kept (entities decoded)", hidden.get("__VIEWSTATE") == "/wEPabc"
      and hidden.get("__EVENTVALIDATION") == "/wEdA&x" and "__VIEWSTATEGENERATOR" in hidden, str(hidden))
check("form: makes without the SELECT placeholder", makes == ["FORD", "HONDA", "LAND ROVER"], str(makes))
check("form: a real model value for the make-wide search", any_model == "200", any_model)

rows, problem = js._okcpap_parse(RESULT)
check("result: the Year/Make/Model table is found, not the hours table", problem == "" and len(rows) == 4, f"{problem} {rows}")
check("result: first row", rows[0] == {"year": 2004, "make": "HONDA", "model": "ACCORD", "row": "300"}, str(rows[0]))
check("result: non-numeric year skipped", all(r["model"] != "CIVIC" for r in rows))
_, prob = js._okcpap_parse("<table><tr><td>Yard Hours</td></tr></table>")
check("result: no inventory table is reported", prob == "no Year/Make/Model table", prob)
swapped = RESULT.replace('<th scope="col">Year</th><th scope="col">Make</th>', '<th scope="col">Make</th><th scope="col">Year</th>') \
                .replace("<td>2004</td><td>HONDA</td>", "<td>HONDA</td><td>2004</td>")
rows2, _ = js._okcpap_parse(swapped)
check("result: header-driven (swapped columns)", rows2[0]["year"] == 2004 and rows2[0]["make"] == "HONDA", str(rows2[:1]))

vs = js._okcpap_vehicles(rows, hashlib)
check("ids: unique, prefixed, identical cars in one row get distinct ids",
      len({v["id"] for v in vs}) == 4 and all(v["id"].startswith("okcpap-") for v in vs), str([v["id"] for v in vs]))
vs_again = js._okcpap_vehicles(rows, hashlib)
check("ids: stable across scans", [v["id"] for v in vs] == [v["id"] for v in vs_again])
check("dates: none on the site, none invented; no VIN", all(v["dateAdded"] == "" and v["vin"] == "" for v in vs))
check("yard fields: name, pin, source", all(v["_location"] == "OKC Pull-A-Part - Oklahoma City" and v["_state"] == "OK"
                                           and v["_lat"] and v["_lng"] and v["_source"] == "okcpap" for v in vs))
check("display name does not start with 'Pull-A-Part' (app.js keys the national chain on that prefix)",
      not js.OKCPAP_YARD["name"].lower().startswith("pull-a-part"))


# fetch: partial-lot guard and make cross-check, with a fake session
class Resp:
    def __init__(self, text, status=200):
        self.text, self.status_code = text, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, per_make):
        self.per_make, self.posts = per_make, []

    def get(self, url, headers=None, timeout=None):
        self.ua = headers.get("User-Agent")
        return Resp(HOME)

    def post(self, url, data=None, headers=None, timeout=None):
        self.posts.append((data["ddlMake"], data["ddlModel"], data["__VIEWSTATE"]))
        return self.per_make.get(data["ddlMake"], Resp("<table><tr><td>none</td></tr></table>"))


ford = Resp(RESULT.replace("HONDA", "FORD"))
real_session, real_sleep = js.requests.Session, js.time.sleep
js.time.sleep = lambda s: None
try:
    fs = FakeSession({"HONDA": Resp(RESULT), "FORD": ford})
    js.requests.Session = lambda: fs
    got = js.fetch_okcpap_inventory()
    check("fetch: one POST per make, any-model value, VIEWSTATE reused, honest UA",
          [p[0] for p in fs.posts] == ["FORD", "HONDA", "LAND ROVER"] and {p[1] for p in fs.posts} == {"200"}
          and {p[2] for p in fs.posts} == {"/wEPabc"} and fs.ua == js.YARDSCOUT_HEADERS["User-Agent"], str(fs.posts))
    check("fetch: both makes' cars returned, empty make is fine", len(got) == 8, str(len(got)))
    fs2 = FakeSession({"HONDA": Resp("err", 500), "FORD": ford})
    js.requests.Session = lambda: fs2
    check("fetch: a failed make skips the whole yard (no partial lot)", js.fetch_okcpap_inventory() == [])
    fs3 = FakeSession({"FORD": Resp(RESULT)})  # FORD request answered with HONDA rows
    js.requests.Session = lambda: fs3
    check("fetch: results for another make -> skip (form semantics changed)", js.fetch_okcpap_inventory() == [])
finally:
    js.requests.Session, js.time.sleep = real_session, real_sleep

check("registered in INDEPENDENT_FETCHERS", any(n == "OKC Pull-A-Part" for n, _ in js.INDEPENDENT_FETCHERS))
check("expected source (zero-vehicle alarm)", "okcpap" in js.INDEPENDENT_EXPECTED_SOURCES)
check("yard pin set", js.OKCPAP_YARD["lat"] == 35.4535 and js.OKCPAP_YARD["lng"] == -97.5115)

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
