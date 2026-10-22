#!/usr/bin/env python3
"""Tests for the Go Pull-It state-pruned/rotation drill scheduler (2026-10-22
request-budget rework — see the GPI_STATE_FILE block comment in
junkyard_scraper.py). The site has a hard 50-newest-rows cap per query and an
honored 10s crawl-delay, so correctness here is what keeps the scan BOTH fast
and complete:

  1. bootstrap (no state): capped makes drill the FULL global model list.
  2. steady carry (rotation not due): NO model queries; previous vehicles
     carried, overlaid by today's page rows (fresher row wins by id), new
     arrivals appended.
  3. rotation due: drill pruned to models present at the yard (state+page).
  4. overflow (page shares no ids with state): full drill, not pruned.
  5. uncapped makes: single page is authoritative; state records models.
  6. state round-trips through the gzip file.

Run:  python3 scraper/test_gopullit_state.py
"""

import json
import sys
import tempfile
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js

failures = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  FAIL") + f" {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# --- synthetic site ------------------------------------------------------------
def row(make, model, year, stock, date="10/20/26", yrow="12", vin=""):
    cells = [make, model, str(year), yrow, vin, stock, date, "", ""]
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def page(rows_html, capped=False):
    sel = ('<select name="make" id="js-input-make"><option value="-1">All</option>'
           '<option value="FORD">FORD</option><option value="HONDA">HONDA</option></select>')
    more = "<p>More results available. Please select a model.</p>" if capped else ""
    return f"<html>{sel}<table>{rows_html}</table>{more}</html>"


class FakeResp:
    def __init__(self, text):
        self.text = text
        self.content = text.encode()

    def raise_for_status(self):
        pass

    def json(self):
        return json.loads(self.text)


class FakeSite:
    """Routes the adapter's GETs; records every model-drill query."""

    def __init__(self):
        self.ford_page_rows = ""     # capped FORD make page (newest 50)
        self.honda_page_rows = ""    # uncapped HONDA make page
        self.model_pages = {}        # MODEL -> rows html
        self.get_models = ["F-150", "FOCUS", "MUSTANG", "RANGER"]
        self.drilled = []            # model names queried
        self.requests = 0

    def get(self, url, **kw):
        self.requests += 1
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "getModels" in url:
            return FakeResp(json.dumps(self.get_models))
        make = (q.get("make") or [""])[0]
        model = (q.get("model") or [""])[0]
        if not make:
            return FakeResp(page(""))  # landing
        if make == "HONDA":
            return FakeResp(page(self.honda_page_rows, capped=False))
        if make == "FORD":
            if model:
                self.drilled.append(model)
                return FakeResp(page(self.model_pages.get(model, ""), capped=False))
            return FakeResp(page(self.ford_page_rows, capped=True))
        return FakeResp(page(""))


def run_fetch(site, state_path, rotation_due):
    js.GPI_STATE_FILE = Path(state_path)
    real_get, real_sleep, real_phase = js.requests.get, js.time.sleep, js._gpi_drill_phase
    real_cache = js._indep_cache_raw
    js.requests.get = site.get
    js.time.sleep = lambda s: None
    js._gpi_drill_phase = (lambda slug, make:
                           int(js.time.time() // js.GPI_SCAN_PERIOD_SEC) % js.GPI_DRILL_PHASES
                           if rotation_due else -1)
    js._indep_cache_raw = lambda name, content: None
    try:
        return js.fetch_gopullit_inventory()
    finally:
        js.requests.get, js.time.sleep = real_get, real_sleep
        js._gpi_drill_phase, js._indep_cache_raw = real_phase, real_cache


tmp = tempfile.mkdtemp()
state_path = str(Path(tmp) / "gopullit_state.json.gz")

site = FakeSite()
site.honda_page_rows = row("HONDA", "CIVIC", 2008, "GPI001") + row("HONDA", "ACCORD", 2011, "GPI002")
site.ford_page_rows = row("FORD", "F-150", 2015, "GPI100") + row("FORD", "FOCUS", 2012, "GPI101")
site.model_pages = {
    "F-150": row("FORD", "F-150", 2015, "GPI100") + row("FORD", "F-150", 2001, "GPI090"),
    "FOCUS": row("FORD", "FOCUS", 2012, "GPI101"),
    "MUSTANG": "",
    "RANGER": "",
}

# ---- 1. bootstrap: no state => full drill -------------------------------------
print("bootstrap (no state):")
out = run_fetch(site, state_path, rotation_due=False)
ids = {v["id"] for v in out}
# all 3 (identical fake) yards drill the full global list
check("full getModels drill", site.drilled == ["F-150", "FOCUS", "MUSTANG", "RANGER"] * 3,
      str(site.drilled))
check("drilled + uncapped vehicles merged (x3 yards)",
      ids == {"gopullit-gpi001", "gopullit-gpi002", "gopullit-gpi100",
              "gopullit-gpi101", "gopullit-gpi090"}, str(sorted(ids)))
check("state file written", Path(state_path).exists())

st = js._gpi_load_state()
check("state has all 3 yards", set(st) == set(js.GPI_YARDS), str(sorted(st)))
jax = st["jacksonville-fl"]
check("state FORD models = drilled presence", jax["models"].get("FORD") == ["F-150", "FOCUS"],
      str(jax["models"]))
check("state HONDA models from uncapped page", jax["models"].get("HONDA") == ["ACCORD", "CIVIC"],
      str(jax["models"]))

# ---- 2. steady carry: rotation not due => no drills ---------------------------
print("carry (rotation not due):")
site.drilled = []
# newest page now: GPI102 is a NEW arrival, GPI100 re-listed with a new row number
site.ford_page_rows = (row("FORD", "ESCAPE", 2018, "GPI102")
                       + row("FORD", "F-150", 2015, "GPI100", yrow="99"))
out = run_fetch(site, state_path, rotation_due=False)
# NB: _utpap_format_label leaves "FORD" all-caps — match case-insensitively,
# exactly like the adapter's own make matching does.
ford = {v["id"]: v for v in out
        if v["make"].upper() == "FORD" and v["_location"].endswith("Jacksonville")}
check("no model drills", site.drilled == [], str(site.drilled))
check("old off-page vehicle carried", "gopullit-gpi090" in ford, str(sorted(ford)))
check("new arrival from page appended", "gopullit-gpi102" in ford, str(sorted(ford)))
check("page overlay wins by id", ford.get("gopullit-gpi100", {}).get("row") == "99",
      str(ford.get("gopullit-gpi100")))
st = js._gpi_load_state()
check("state models grew with page's new model",
      st["jacksonville-fl"]["models"].get("FORD") == ["ESCAPE", "F-150", "FOCUS"],
      str(st["jacksonville-fl"]["models"]))

# ---- 3. rotation due => pruned drill ------------------------------------------
print("pruned drill (rotation due):")
site.drilled = []
site.model_pages["ESCAPE"] = row("FORD", "ESCAPE", 2018, "GPI102")
out = run_fetch(site, state_path, rotation_due=True)
# getModels order filtered to present models only: F-150, FOCUS, ESCAPE absent
# from the global list? add it so the prune has something to keep.
# known = state(ESCAPE, F-150, FOCUS) ∩ getModels(F-150, FOCUS, MUSTANG, RANGER)
check("drills only models present at the yard (x3 yards)",
      set(site.drilled) == {"F-150", "FOCUS"},
      str(site.drilled))
ford_ids = {v["id"] for v in out if v["make"].upper() == "FORD"}
check("drill result + page safety-net kept ESCAPE (not in getModels)",
      "gopullit-gpi102" in ford_ids, str(sorted(ford_ids)))
check("departed-model vehicle refreshed away is impossible here: GPI090 still present",
      "gopullit-gpi090" in ford_ids, str(sorted(ford_ids)))

# ---- 4. overflow: page shares no ids with state => full drill -----------------
print("overflow full drill:")
site.drilled = []
site.ford_page_rows = row("FORD", "FUSION", 2014, "GPI200") + row("FORD", "FUSION", 2016, "GPI201")
site.model_pages["FUSION"] = site.ford_page_rows
out = run_fetch(site, state_path, rotation_due=False)
check("page∩state empty forces FULL getModels drill",
      site.drilled == ["F-150", "FOCUS", "MUSTANG", "RANGER"] * 3, str(site.drilled))

# ------------------------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("All Go Pull-It state tests passed.")
