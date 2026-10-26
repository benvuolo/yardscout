#!/usr/bin/env python3
"""Ario multi-tenant adapter tests — standalone, no network.

Covers the pure pieces of fetch_ario_inventory: org-table indexing (slug /
org_id resolution), the org-record pin extraction, the inventorysearch row
parser (ids, VIN gate, epoch-ms dates, make/model fallback from name_text,
added_since filter), the Ryan's id scheme staying byte-identical, and the
chain -> expected-sources registration. Run:

    python3 scraper/test_ario_adapter.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import junkyard_scraper as js  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    tag = "ok  " if cond else "FAIL"
    print(f"{tag} {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


APP = "1700000000000x1"
ORGS = [
    {"_id": "org-ryans", "_source": {"id_text": "ryans-pick-a-part-detroit",
                                     "name_text": "Ryan's Pick-a-Part",
                                     "owner_user": f"{APP}__LOOKUP__user1",
                                     "address_geographic_address": {
                                         "address": "9309 Hubbell Ave, Detroit",
                                         "lat": 42.36261, "lng": -83.18853}}},
    # Foss orgs carry only the newer `Slug` field, no id_text.
    {"_id": "org-foss-ws", "_source": {"Slug": "Foss-Winston-Salem",
                                       "name_text": "Foss U-Pull-It Winston-Salem"}},
    # Paul's Lake Station: the two slug fields disagree — both must resolve.
    {"_id": "org-pauls-ls", "_source": {"id_text": "pauls-auto-yard", "Slug": "pauls-lake-station",
                                        "name_text": "Paul's - Lake Station"}},
    {"_id": "org-slugless", "_source": {"name_text": "Slugless Yard",
                                        "address_geographic_address": {
                                            "address": "x", "lat": 0, "lng": 0}}},
]

# --- org index / resolution ----------------------------------------------
by_slug, by_id = js._ario_org_index(ORGS)
check("slug index is case-insensitive", "foss-winston-salem" in by_slug)
check("resolve by slug (any case)",
      js._ario_resolve_org({"slug": "FOSS-winston-salem"}, by_slug, by_id) is ORGS[1])
check("resolve by either slug field when they disagree",
      js._ario_resolve_org({"slug": "pauls-auto-yard"}, by_slug, by_id) is ORGS[2]
      and js._ario_resolve_org({"slug": "pauls-lake-station"}, by_slug, by_id) is ORGS[2])
check("resolve by org_id for slugless orgs",
      js._ario_resolve_org({"org_id": "org-slugless"}, by_slug, by_id) is ORGS[3])
check("unknown slug resolves to None",
      js._ario_resolve_org({"slug": "nope"}, by_slug, by_id) is None)
check("ref prefix comes off a reference field",
      js._ario_ref_prefix(ORGS[0]) == f"{APP}__LOOKUP__")
check("ref prefix empty when the record has none", js._ario_ref_prefix(ORGS[1]) == "")

# --- pins ----------------------------------------------------------------
check("org pin extracted + rounded", js._ario_org_pin(ORGS[0]) == (42.3626, -83.1885))
check("org without geocode -> None", js._ario_org_pin(ORGS[1]) is None)
check("0,0 geocode is rejected", js._ario_org_pin(ORGS[3]) is None)

# --- row parser ----------------------------------------------------------
MAKES = {"mk-toyota": "TOYOTA", "mk-chevrolet": "CHEVROLET"}
MODELS = {"md-4runner": "4RUNNER"}
YARD = {"slug": "x", "code": "ws", "name": "Foss U-Pull-It - Winston-Salem",
        "city": "Winston-Salem", "state": "NC", "lat": 36.1, "lng": -80.2}
ROWS = [
    {"vehicle_year_number": 2003, "stock_number_text": "STK01234",
     "vin_text": "jtebu14r530012345", "row_text": "12", "exterior_color_text": "DARK GREEN",
     "added_date_date": 1761436800000,  # 2025-10-26T00:00Z
     "vehicle_make_custom_vehicle_make": f"{APP}__LOOKUP__mk-toyota",
     "vehicle_model_custom_vehicle_model": f"{APP}__LOOKUP__md-4runner"},
    # make/model refs missing -> fall back to name_text
    {"vehicle_year_number": "2008", "stock_number_text": "STK01235",
     "name_text": "2008 CHEVROLET SILVERADO 1500", "vin_text": "short",
     "added_date_date": 1761436800000},
    # duplicate stock -> -2 suffix
    {"vehicle_year_number": 2003, "stock_number_text": "STK01234",
     "vehicle_make_custom_vehicle_make": f"{APP}__LOOKUP__mk-toyota",
     "vehicle_model_custom_vehicle_model": f"{APP}__LOOKUP__md-4runner"},
    # no year -> dropped
    {"stock_number_text": "STK09999", "name_text": "TOYOTA CAMRY"},
    # no stock -> inventory_id fallback
    {"vehicle_year_number": 1999, "inventory_id_text": "INV77",
     "vehicle_make_custom_vehicle_make": f"{APP}__LOOKUP__mk-toyota",
     "vehicle_model_custom_vehicle_model": f"{APP}__LOOKUP__md-4runner"},
]
out = js._ario_rows_to_vehicles(ROWS, yard=YARD, source="foss", id_prefix="foss-ws-",
                                make_map=MAKES, model_map=MODELS, pin=(36.0999, -80.2001))
ids = [v["id"] for v in out]
check("chain-coded ids + dupe suffix + inventory_id fallback",
      ids == ["foss-ws-stk01234", "foss-ws-stk01235", "foss-ws-stk01234-2", "foss-ws-inv77"], str(ids))
v0 = out[0]
check("17-char VIN upper-cased", v0["vin"] == "JTEBU14R530012345")
check("epoch-ms added date -> ISO day", v0["dateAdded"] == "2025-10-26", v0["dateAdded"])
check("make/model title-cased via label helper",
      (v0["make"], v0["model"]) == ("Toyota", "4Runner"), f"{v0['make']} {v0['model']}")
check("color title-cased", v0.get("_color") == "Dark Green")
check("org pin preferred over config fallback", (v0["_lat"], v0["_lng"]) == (36.0999, -80.2001))
check("source/location carried", (v0["_source"], v0["_location"]) == ("foss", YARD["name"]))
v1 = out[1]
check("name_text fallback splits make/model",
      (v1["make"], v1["model"]) == ("Chevrolet", "Silverado 1500"), f"{v1['make']} {v1['model']}")
check("non-17 VIN blanked", v1["vin"] == "")
check("row-less row keeps empty row", v1["row"] == "")

noconf = js._ario_rows_to_vehicles(ROWS[:1], yard=YARD, source="foss", id_prefix="foss-ws-",
                                   make_map=MAKES, model_map=MODELS, pin=None)
check("config pin used when org has none", (noconf[0]["_lat"], noconf[0]["_lng"]) == (36.1, -80.2))

old_yard = {**YARD, "added_since": "2026-01-01"}
filtered = js._ario_rows_to_vehicles(ROWS, yard=old_yard, source="foss", id_prefix="foss-ws-",
                                     make_map=MAKES, model_map=MODELS)
check("added_since drops dated rows older than the cutoff; undated rows stay",
      [v["id"] for v in filtered] == ["foss-ws-stk01234-2", "foss-ws-inv77"],
      str([v["id"] for v in filtered]))

# --- Ryan's keeps its historical id scheme --------------------------------
ry = js.ARIO_CHAINS["ryans"]
check("Ryan's id_prefix unchanged", ry.get("id_prefix") == "ryans-")
ry_out = js._ario_rows_to_vehicles(ROWS[:1], yard=ry["yards"][0], source="ryans",
                                   id_prefix=ry["id_prefix"], make_map=MAKES, model_map=MODELS)
check("Ryan's ids are ryans-{stock}", ry_out[0]["id"] == "ryans-stk01234", ry_out[0]["id"])
check("Ryan's fallback pin is the Hubbell Ave geocode",
      (ry["yards"][0]["lat"], ry["yards"][0]["lng"]) == (42.3626, -83.1885))

# --- config shape / alarm registration ------------------------------------
for src, chain in js.ARIO_CHAINS.items():
    check(f"chain {src}: label + yards list", bool(chain.get("label")) and isinstance(chain.get("yards"), list))
    for y in chain["yards"]:
        check(f"{y.get('name')}: slug or org_id, pin, city/state",
              bool(y.get("slug") or y.get("org_id")) and all(k in y for k in ("name", "city", "state", "lat", "lng")))
        check(f"{y.get('name')}: code is a safe id token",
              bool(y.get("code")) and y["code"] == y["code"].lower() and y["code"].isalnum())
codes = [f"{src}-{y['code']}" for src, c in js.ARIO_CHAINS.items() for y in c["yards"]]
check("yard codes unique within the Ario table", len(codes) == len(set(codes)))
check("ryans registered for the zero-vehicle alarm",
      js.INDEPENDENT_EXPECTED_SOURCES.get("ryans") == ry["label"])
check("chains with no yards are NOT registered",
      all(src in js.INDEPENDENT_EXPECTED_SOURCES or not c["yards"]
          for src, c in js.ARIO_CHAINS.items())
      and all(src not in js.INDEPENDENT_EXPECTED_SOURCES
              for src, c in js.ARIO_CHAINS.items() if not c["yards"]))
check("fetcher wired", any(fn is js.fetch_ario_inventory for _l, fn in js.INDEPENDENT_FETCHERS))

# --- live (Supabase) feed: paging, truncation, VIN cache, backfill cap --------
class FakeSession:
    pass


def make_fake_post(pages: dict, details: dict, fail_at: int | None = None, calls: list | None = None):
    """pages: {offset: (items, meta)}; details: {inventory_id: vin}."""
    def fake(session, fn, body):
        if calls is not None:
            calls.append((fn, body))
        if fn == "search-inventory":
            off = body["item_rank_offset"]
            if fail_at is not None and off == fail_at:
                return None
            items, meta = pages[off]
            return {"items": items, "total": meta["total_matching"], "yards_meta": [meta]}
        if fn == "get-inventory-item":
            vin = details.get(body["inventory_id"])
            return {"item": {"vin": vin}} if vin else {"item": {}}
        raise AssertionError(fn)
    return fake


def item(i, stock=None, date="2026-10-20"):
    return {"id": str(1000 + i), "year": "2010", "make": "FORD", "model": "FUSION", "row": "7",
            "stock": stock or f"STK{i:05d}", "date_placed": date, "color": "RED", "yard": "foss-wilson"}


PAGES = {
    0: ([item(i) for i in range(3)], {"yard": "foss-wilson", "returned": 3, "total_matching": 5, "truncated": True, "next_offset": 3}),
    3: ([item(i) for i in range(3, 5)], {"yard": "foss-wilson", "returned": 2, "total_matching": 5, "truncated": False, "next_offset": 5}),
}
_orig_post = js._ario_live_post
calls: list = []
js._ario_live_post = make_fake_post(PAGES, {"1001": "1FAHP3F29CL123456"}, calls=calls)
try:
    trunc: list = []
    items = js._ario_live_yard_items(FakeSession(), "foss-wilson", truncated=trunc)
    check("live paging follows next_offset to completion", [i["id"] for i in items] == [str(1000 + i) for i in range(5)] and not trunc, str(trunc))
    check("live paging asks for ARIO_LIVE_PAGE rows", calls[0][1]["per_yard_limit"] == js.ARIO_LIVE_PAGE and calls[0][1]["yard_list"] == ["foss-wilson"])

    yard = {"slug": "foss-wilson", "code": "wilson", "name": "Foss U-Pull-It - Wilson", "city": "Wilson", "state": "NC", "lat": 35.7, "lng": -77.9}
    vs = js._ario_live_items_to_vehicles(items, yard=yard, source="foss", id_prefix="foss-wilson-", vin_map={"foss-wilson-stk00000": "1FAHP3F20CL000000"})
    check("live rows map to the same id scheme as the legacy feed", vs[0]["id"] == "foss-wilson-stk00000", vs[0]["id"])
    check("VIN comes from the cache when present", vs[0]["vin"] == "1FAHP3F20CL000000" and vs[1]["vin"] == "")
    check("date_placed -> dateAdded, color title-cased", vs[0]["dateAdded"] == "2026-10-20" and vs[0]["_color"] == "Red")
    got = js._ario_vin_backfill(FakeSession(), vs, cap=1)
    check("backfill fetches VIN-less cars up to the cap (newest first) and fills the row",
          got == {"foss-wilson-stk00001": "1FAHP3F29CL123456"} and vs[1]["vin"] == "1FAHP3F29CL123456", str(got))
    check("backfill skipped the rest under the cap", vs[2]["vin"] == "" and sum(1 for f, _ in calls if f == "get-inventory-item") == 1)

    ghost = js._ario_live_items_to_vehicles(
        [item(7, date="2017-11-12"), item(8, date="2026-10-01"), {**item(9), "date_placed": ""}],
        yard=yard, source="foss", id_prefix="foss-wilson-", vin_map={})
    check("live rows older than ARIO_LIVE_MAX_AGE_DAYS are dropped; undated rows kept",
          [v["id"] for v in ghost] == ["foss-wilson-stk00008", "foss-wilson-stk00009"], str([v["id"] for v in ghost]))
    since = js._ario_live_items_to_vehicles([item(7, date="2026-03-01"), item(8, date="2026-10-01")],
                                            yard={**yard, "added_since": "2026-05-01"}, source="foss", id_prefix="foss-wilson-", vin_map={})
    check("live rows honour added_since", [v["id"] for v in since] == ["foss-wilson-stk00008"])

    js._ario_live_post = make_fake_post(PAGES, {}, fail_at=3)
    trunc = []
    items = js._ario_live_yard_items(FakeSession(), "foss-wilson", truncated=trunc)
    check("a failed page reports truncation instead of a short lot", len(items) == 3 and trunc and "failed" in trunc[0], str(trunc))
finally:
    js._ario_live_post = _orig_post

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("all ok")
