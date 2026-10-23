"""Production verification for the Live-tab sort options (jh-v65).

Checks, at 390px and 360px:
  1. the Order by select renders with the new options,
  2. each sort visibly reorders the grid,
  3. newest-arrivals ordering matches the data (rendered sequence ==
     independent stable re-sort of the same filtered scope),
  4. unknowns sort last (no fake dates/years).

Run: ~/projects/sigma-mcp/.venv/bin/python tools/_sort_verify_prod.py
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PROD = "https://yardscout.io"
OUT = Path(__file__).parent / "_sort_verify_shots"
OUT.mkdir(exist_ok=True)

EXPECTED_OPTIONS = ["date-desc", "dist-asc", "year-desc", "year-asc", "date-asc",
                    "smart-profit", "gold-first", "fastest-sell", "leaving-soonest"]

ZIP = "46203"  # Indianapolis — Indy Pull-A-Part area, dense coverage
COORDS = {"lat": 39.7368, "lng": -86.1263}


def wait_for_deploy(timeout_s=600):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                f"{PROD}/sw.js?nocache={int(time.time())}",
                headers={"User-Agent": "Mozilla/5.0"})  # host 403s python's default UA
            body = urllib.request.urlopen(req).read().decode()
            if "jh-v65" in body:
                print("deploy live: sw.js has jh-v65")
                return
            cur = body.split("CACHE = '")[1].split("'")[0] if "CACHE = '" in body else "?"
            print(f"  waiting for deploy (prod still {cur})...")
        except Exception as e:
            print(f"  fetch error: {e}")
        time.sleep(20)
    sys.exit("deploy never showed jh-v65")


EXTRACT = """
() => {
  const keyToV = new Map(liveInventory.map(v => [(v.vin || String(v.id)), v]));
  return [...document.querySelectorAll('#live-grid .car-card')].map(c => {
    const k = (c.querySelector('.heart-btn') || {dataset:{}}).dataset.vkey || null;
    const v = keyToV.get(k);
    const nameEl = c.querySelector('.car-name');
    const metaEl = c.querySelector('.car-meta');
    return {
      key: k,
      name: nameEl ? nameEl.textContent.trim() : '',
      ts: v ? yardDateMs(v.dateAdded) : -1,
      hasDate: v ? !!parseYardDate(v.dateAdded) : false,
      year: v ? (v.year || 0) : -1,
      dist: v ? vehicleDistanceMi(v) : null,
      metaHasUnknown: metaEl ? metaEl.textContent.includes('Set-out date unknown') : false,
    };
  });
}
"""

# Independent recompute of the newest-arrivals order for the current scope:
# same filter (within effective radius), stable sort by yardDateMs desc —
# mirrors app.js's decorate-sort with the tsOf tie (equal keys stay stable).
EXPECTED_NEWEST = """
() => {
  const r = effectiveRadiusMi();
  const scoped = liveInventory.filter(v => {
    const d = vehicleDistanceMi(v);
    return d != null && (!r || d <= r);
  });
  const dec = scoped.map(v => [yardDateMs(v.dateAdded), (v.vin || String(v.id))]);
  dec.sort((x, y) => y[0] - x[0]);
  return dec.map(d => ({ ts: d[0], key: d[1] }));
}
"""


def monotonic(vals, descending, label):
    for i in range(1, len(vals)):
        a, b = vals[i - 1], vals[i]
        ok = a >= b if descending else a <= b
        if not ok:
            return f"FAIL {label}: position {i}: {a} then {b}"
    return None


def run_viewport(browser, width, height):
    tag = f"{width}px"
    print(f"\n=== viewport {width}x{height} ===")
    ctx = browser.new_context(viewport={"width": width, "height": height},
                              device_scale_factor=2)
    ctx.add_init_script(f"""
      try {{
        localStorage.setItem('jh_zip', '{ZIP}');
        localStorage.setItem('jh_zip_coords', JSON.stringify({{'{ZIP}': {json.dumps(COORDS)}}}));
        localStorage.setItem('jh_filters_open', '1');
        localStorage.setItem('jh_honesty_ack', '1');
      }} catch (e) {{}}
    """)
    page = ctx.new_page()
    page.goto(PROD + "/?sortqa=" + str(int(time.time())), wait_until="domcontentloaded")
    page.wait_for_function(
        "document.querySelectorAll('#live-grid .car-card').length > 10", timeout=120000)

    failures = []

    # 1. control renders with the right options
    opts = page.eval_on_selector_all("#live-sort option", "os => os.map(o => o.value)")
    print(f"  select options: {opts}")
    if opts != EXPECTED_OPTIONS:
        failures.append(f"FAIL options mismatch: {opts}")
    default_val = page.eval_on_selector("#live-sort", "s => s.value")
    print(f"  default sort: {default_val}")
    if default_val != "date-desc":
        failures.append(f"FAIL default sort is {default_val}, expected date-desc")

    # screenshot: drawer open, Order by group in view
    page.eval_on_selector("#live-sort", "el => el.scrollIntoView({block:'center'})")
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / f"control_{tag}.png"))
    print(f"  shot: control_{tag}.png")

    first_keys = {}
    for sort_val, check in [
        ("date-desc", None),
        ("dist-asc", None),
        ("year-desc", None),
        ("year-asc", None),
        ("date-asc", None),
    ]:
        page.select_option("#live-sort", sort_val)
        page.wait_for_timeout(700)
        cards = page.evaluate(EXTRACT)
        if len(cards) < 10:
            failures.append(f"FAIL {sort_val}: only {len(cards)} cards rendered")
            continue
        first_keys[sort_val] = [c["key"] for c in cards[:5]]

        if sort_val == "date-desc":
            known = [c["ts"] for c in cards if c["hasDate"]]
            err = monotonic(known, True, "date-desc ts")
            if err: failures.append(err)
            # unknown-date cards (if any rendered) must all be at the end
            flags = [c["hasDate"] for c in cards]
            if any(f and not g for g, f in zip(flags, flags[1:])):
                failures.append("FAIL date-desc: unknown-date card before a dated one")
            # ordering matches the data, independently recomputed
            expected = page.evaluate(EXPECTED_NEWEST)
            n = len(cards)
            exp_ts = [e["ts"] for e in expected[:n]]
            got_ts = [c["ts"] for c in cards]
            if exp_ts != got_ts:
                i = next(i for i in range(n) if exp_ts[i] != got_ts[i])
                failures.append(f"FAIL newest-arrivals vs data at pos {i}: "
                                f"rendered ts {got_ts[i]}, expected {exp_ts[i]}")
            else:
                print(f"  date-desc: rendered {n} cards match independent re-sort exactly")
        elif sort_val == "dist-asc":
            dists = [c["dist"] for c in cards]
            known = [d for d in dists if d is not None]
            err = monotonic(known, False, "dist-asc")
            if err: failures.append(err)
            if any(d1 is None and d2 is not None for d1, d2 in zip(dists, dists[1:])):
                failures.append("FAIL dist-asc: no-distance card before a distanced one")
            print(f"  dist-asc: {known[0]:.1f} mi ... {known[-1]:.1f} mi over {len(cards)} cards")
        elif sort_val in ("year-desc", "year-asc"):
            known = [c["year"] for c in cards if c["year"] > 0]
            err = monotonic(known, sort_val == "year-desc", sort_val)
            if err: failures.append(err)
            flags = [c["year"] > 0 for c in cards]
            if any(f and not g for g, f in zip(flags, flags[1:])):
                failures.append(f"FAIL {sort_val}: unknown-year card before a dated one")
            print(f"  {sort_val}: years {known[0]} ... {known[-1]}")
        elif sort_val == "date-asc":
            known = [c["ts"] for c in cards if c["hasDate"]]
            err = monotonic(known, False, "date-asc ts")
            if err: failures.append(err)
            # the old bug: unknown dates floated to the TOP of this sort
            if cards and not cards[0]["hasDate"]:
                failures.append("FAIL date-asc: unknown-date car first (unknowns must sort last)")
            print(f"  date-asc: oldest first, unknowns not at top")

        # per-sort grid screenshot (scroll to top of grid)
        page.evaluate("document.getElementById('live-grid').scrollIntoView({block:'start'})")
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT / f"grid_{sort_val}_{tag}.png"))

    # 2. "visibly reorders": top-of-list differs across sorts
    orders = {k: tuple(v) for k, v in first_keys.items()}
    distinct = len(set(orders.values()))
    print(f"  distinct top-5 orderings across 5 sorts: {distinct}")
    if distinct < 4:  # allow a coincidental overlap of two
        failures.append(f"FAIL: sorts don't visibly reorder (only {distinct} distinct orders): {orders}")

    ctx.close()
    return failures


def main():
    wait_for_deploy()
    all_failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w, h in [(390, 844), (360, 800)]:
            all_failures += [f"[{w}px] {f}" for f in run_viewport(browser, w, h)]
        browser.close()
    print("\n==== RESULT ====")
    if all_failures:
        for f in all_failures:
            print(f)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
