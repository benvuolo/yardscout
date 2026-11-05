"""Synthetic catalog pages for the crawler-requirement tests (CURATION_SPEC.md
§3.2), in the two templates' real page formats, under model-years no real
catalog has (2030), so they never collide with the real fixture pages.

  toyota_pages(): www.toyotapartsnow.com 2030 Camry (SimplePart)
    alternator page   R5b/R5c: a new diagram number next to its -84 reman
                      (reman dropped), a superseded "other" number, a kit row
                      that is a chain target, url_pn_mismatch, no-url rows
    starter page      R5b: only remans plus a superseded "other" number, so
                      the remans stay; chain: 28100-90010-84 replaces
                      28100-90030, linked only from its product page
    mirror page       R5a: "Mirror Assy, Outer Rear View, W/Turn Signal Lamp"
    headlamp page     R5a: "Unit Assy, Headlamp, W/Auto Leveling"
  gm_pages(): www.gmpartsgiant.com 2030 Malibu (PartsGiant)
    model page offers "", new_model, eco, limited/classic carryover, hybrid
    plain generator page: a superseded number and a REMANUFACTURED one (kept,
    R5b), a bolt, gpgOnly and Standard Parts rows
    new_model generator page: a new number and a reman one (reman dropped)
  ford_split_pages(): www.fordpartsgiant.com 2030 Ranger, split into three
    engine catalogs (first and last are read)
"""
from __future__ import annotations

import html as htmllib

from _crawler_fixtures import page, store_html

T = "https://www.toyotapartsnow.com"
G = "https://www.gmpartsgiant.com"
F = "https://www.fordpartsgiant.com"
TSTEM = "2030-toyota-camry"


def _sp_row(pn, main, aux=None, url=True, replace="", notes=None, location=None, extra=None):
    e = []
    if notes:
        e.append({"name": "Part Notes", "desc": notes})
    if location:
        e.append({"name": "Location", "desc": location})
    e += extra or []
    if url is True:
        url = f"/oem/toyota~{main.lower().replace(' ', '-')}~{pn.lower()}"
    return {"partNumber": pn, "mainDesc": main, "auxiliaryDesc": aux, "allExtraInfoList": e,
            "replace": replace, "url": url or None}


def sp_list(diagram: list, other: list | None = None) -> dict:
    return page(store_html({"partList": {"partList": [diagram], "gpgOnlyPartList": [other or []]}}))


def sp_product(pn, desc, replaces="", replaced_by="", position=None, rows=None, links=()) -> dict:
    """A SimplePart product page whose rendered text matches its store."""
    rows = rows or [["2030 Toyota Camry", "LE, SE", "4 Cyl 2.5 L GAS"]]
    base = [{"name": "Position", "desc": position}] if position else []
    info = {"partNumber": pn, "mainDesc": desc, "partDescription": desc, "replaces": replaces,
            "replacedBy": replaced_by, "lr": position or "", "baseInfoList": base}
    st = {"partNumber": {"partInfo": info,
                         "fitVehicleTitleList": [{"text": "Year Make Model"}, {"text": "Trim"}, {"text": "Engine"}],
                         "fitVehicleList": rows}}
    lines = []
    if position:
        lines += ["Position", position]
    if replaces:
        lines += ["Replaces", replaces]
    if replaced_by:
        lines += ["Replaced By", replaced_by]
    lines += ["Vehicle Fitment", "Year Make Model", "Trim", "Engine"] + [c for r in rows for c in r] + ["Warning:"]
    body = "".join(f"<div>{htmllib.escape(x, quote=False)}</div>" for x in lines)
    body += "".join(f'<a href="{h}">related</a>' for h in links)
    return page(store_html(st, body))


def toyota_pages() -> dict:
    y = f"{T}/catalog/{TSTEM}-parts"
    subs = ["charging-starting/alternator", "charging-starting/starter", "body-hardware/outside-mirrors",
            "headlights-lighting/headlamps", "engine/oil-pan"]
    year = page(store_html({"vehicleOption": {"optionList": [], "optionNavList": []}},
                           "".join(f'<a href="/parts-list/{TSTEM}/{s}">x</a>' for s in subs),
                           title="2030 Toyota Camry Parts - ToyotaPartsNow.com"))
    L = f"{T}/parts-list/{TSTEM}"
    alt = sp_list([
        _sp_row("27060-90010", "Alternator", "Alternator Assembly, With Regulator", notes="2.5L"),
        _sp_row("27060-90010-84", "Alternator", "Alternator Assembly", notes="2.5L"),
        _sp_row("27415-90010", "Pulley", "Pulley, Alternator"),
        _sp_row("12511-90010", "Alternator", "Alternator Bracket"),
        _sp_row("90119-90010", "Bolt", "Bolt, W/Washer"),
        _sp_row("27060-90020", "Alternator", "Alternator Assembly", url="/oem/toyota~alternator~27060-99999"),
        _sp_row("27060-90030", "Alternator", "Alternator Assembly", url=None),
    ], [
        _sp_row("27060-90005", "Alternator Assy", None, replace="27060-90010",
                extra=[{"name": "Production Date", "desc": "01/2030-06/2030"}, {"name": "Replaced By", "desc": "27060-90010"}]),
        _sp_row("27060-89990", "Alternator Kit", None),
    ])
    starter = sp_list([
        _sp_row("28100-90010-84", "Starter", "Starter Assembly", notes="1.4 KW"),
        _sp_row("28100-90020-84", "Starter", "Reman Starter Assembly", notes="1.7 KW"),
    ], [
        _sp_row("28100-90010", "Starter Assy", None, replace="28100-90010-84"),
    ])
    mirrors = sp_list([
        _sp_row("87910-90010", "Mirror Assembly", "Mirror Assy, Outer Rear View, W/Turn Signal Lamp",
                notes="US Built, With Heated;Japan Built, With Heated", location="Passenger Side"),
        _sp_row("87940-90010", "Mirror Assembly", "Mirror Assy, Outer Rear View", notes="Japan Built, Without Heated",
                location="Driver Side"),
        _sp_row("87961-90010", "Mirror Glass", "Mirror, Outer Rear View W/Heater"),
    ])
    lamps = sp_list([
        _sp_row("81110-90010", "Headlamp Assembly", "Unit Assy, Headlamp, W/Auto Leveling", location="Driver Side"),
        _sp_row("81145-90010", "Headlamp Cover", "Cover, Headlamp"),
    ])
    P = f"{T}/oem/toyota"
    return {
        y: year,
        f"{L}/charging-starting/alternator": alt,
        f"{L}/charging-starting/starter": starter,
        f"{L}/body-hardware/outside-mirrors": mirrors,
        f"{L}/headlights-lighting/headlamps": lamps,
        f"{P}~alternator~27060-90010": sp_product("27060-90010", "Alternator", replaces="27060-89990"),
        f"{P}~alternator~27060-90010-84": sp_product("27060-90010-84", "Reman Alternator"),
        f"{P}~alternator-assy~27060-90005": sp_product("27060-90005", "Alternator", replaced_by="27060-90010"),
        f"{P}~alternator-kit~27060-89990": sp_product("27060-89990", "Alternator Kit", replaced_by="27060-90010"),
        f"{P}~starter~28100-90010-84": sp_product("28100-90010-84", "Reman Starter", replaces="28100-90010, 28100-90030",
                                                  links=["/oem/toyota~starter~28100-90030",
                                                         "/oem/toyota~bolt~90119-90099"]),
        f"{P}~starter~28100-90020-84": sp_product("28100-90020-84", "Reman Starter"),
        f"{P}~starter-assy~28100-90010": sp_product("28100-90010", "Starter", replaced_by="28100-90010-84"),
        f"{P}~starter~28100-90030": sp_product("28100-90030", "Starter", replaces="28100-90040",
                                               replaced_by="28100-90010-84"),
        f"{P}~mirror-assembly~87910-90010": sp_product("87910-90010", "Mirror Assembly", position="Rear Outer Passenger Side"),
        f"{P}~mirror-assembly~87940-90010": sp_product("87940-90010", "Mirror Assembly", position="Rear Outer Driver Side"),
        f"{P}~headlamp-assembly~81110-90010": sp_product("81110-90010", "Headlamp Assembly", position="Driver Side"),
    }


def _pg_row(pn, main, group, remark="", info=(), replace="", url=True):
    if url is True:
        url = f"/parts/gm-{main.lower().split(',')[0].replace(' ', '-')}-{pn}.html"
    return {"partNumber": pn, "mainDesc": main, "pncDesc": group, "mainDescAlter": remark or None,
            "allExtraInfoList": [{"name": n, "desc": d} for n, d in info], "replace": replace, "url": url or None}


def pg_list(diagram: list, gpg: list | None = None, standard: list | None = None) -> dict:
    pl = {"partList": [diagram], "expandPartList": [standard or []]}
    if gpg is not None:
        pl["gpgOnlyPartList"] = [gpg]
    return page(store_html({"partList": pl}))


def pg_product(pn, desc, replaces="", replaced_by="", lr="", rows=None, links=()) -> dict:
    rows = rows or [["2030 Chevrolet Malibu", "4 Cyl 2.5L", "LS, LT"]]
    info = {"partNumber": pn, "partDescription": desc, "mainDesc": desc, "lr": lr,
            "replacedBy": replaced_by, "replaces": replaces}
    st = {"partNumber": {"partInfo": info,
                         "fitVehicleTitleList": [{"text": "Year Make Model"}, {"text": "Engine"},
                                                 {"text": "Important vehicle option details"}],
                         "fitVehicleList": rows}}
    table = '<table class="fit-vehicle-list-table">' + "".join(
        "<tr>" + "".join(f"<td>{htmllib.escape(c, quote=False)}</td>" for c in r) + "</tr>" for r in rows) + "</table>"
    table += "".join(f'<a href="{h}">related</a>' for h in links)
    return page(store_html(st, table))


def gm_pages() -> dict:
    variants = ["new_model", "", "eco", "limited_carryover_model", "classic_carryover_model", "hybrid"]
    model = page(store_html({}, "".join(
        f'<a href="/2030-chevrolet-malibu{"-" + v if v else ""}-parts.html">x</a>' for v in variants)
        + '<a href="/2029-chevrolet-malibu-parts.html">x</a>', title="Chevrolet Malibu Parts"))
    sec = "starter_generator_ignition_electrical_lamps"
    plain = page(store_html({}, f'<a href="/parts-list/2030-chevrolet-malibu/{sec}/generator_mounting.html">x</a>'
                                f'<a href="/parts-list/2030-chevrolet-malibu/{sec}/lamps_front.html">x</a>',
                            title="2030 Chevrolet Malibu Parts - GMPartsGiant.com"))
    new = page(store_html({}, f'<a href="/parts-list/2030-chevrolet-malibu-new_model/{sec}/generator_mounting.html">x</a>',
                          title="2030 Chevrolet Malibu New Model Parts - GMPartsGiant.com"))
    gen = pg_list([
        _pg_row("19000001", "GENERATOR", "GENERATOR, Engine Electrical", "(INCLUDES 3-5)",
                [("Fitting Vehicle Options", "LS(69)(LUV)"), ("Replaced By", "19000002")], replace="19000002"),
        _pg_row("19000003", "GENERATOR", "GENERATOR, Engine Electrical", "REMANUFACTURED(INCLUDES 3-5)",
                [("Fitting Vehicle Options", "LS(69)(LUV)")]),
        _pg_row("11589999", "BOLT, Generator", "BOLT, Generator", "BOLT,GENERATOR(M8X1.25)"),
    ], gpg=[_pg_row("19000009", "GENERATOR", "GENERATOR, Engine Electrical", "CATALOG ONLY")],
        standard=[_pg_row("11589280", "BOLT", "Standard Parts", "HEX FLANGED HEAD")])
    gen_new = pg_list([
        _pg_row("19000002", "GENERATOR", "GENERATOR, Engine Electrical", "(INCLUDES 3-5)",
                [("Fitting Vehicle Options", "LT(69)(LWE)")]),
        _pg_row("19000004", "GENERATOR", "GENERATOR, Engine Electrical", "REMANUFACTURED(INCLUDES 3-5)",
                [("Fitting Vehicle Options", "LT(69)(LWE)")]),
    ])
    lamps = pg_list([
        _pg_row("95291999", "HEADLAMP", "HEADLAMP, Capsule/Headlamp/Fog Lamp", "(INCLUDES 4,5)",
                [("Location", "Driver Side")]),
        _pg_row("13503418", "BULB, Capsule/Headlamp/Fog Lamp", "BULB, Capsule/Headlamp/Fog Lamp", "BULB,HEADLAMP(PART OF 1)"),
    ])
    PP = f"{G}/parts"
    return {
        f"{G}/chevrolet-malibu-parts.html": model,
        f"{G}/2030-chevrolet-malibu-parts.html": plain,
        f"{G}/2030-chevrolet-malibu-new_model-parts.html": new,
        f"{G}/parts-list/2030-chevrolet-malibu/{sec}/generator_mounting.html": gen,
        f"{G}/parts-list/2030-chevrolet-malibu/{sec}/lamps_front.html": lamps,
        f"{G}/parts-list/2030-chevrolet-malibu-new_model/{sec}/generator_mounting.html": gen_new,
        f"{PP}/gm-generator-19000001.html": pg_product("19000001", "Alternator", replaced_by="19000002"),
        f"{PP}/gm-generator-19000003.html": pg_product("19000003", "Alternator, Remanufactured"),
        f"{PP}/gm-generator-19000002.html": pg_product("19000002", "Alternator", replaces="19000001, 19000000",
                                                       links=["/parts/gm-generator-asm-19000000.html"]),
        f"{PP}/gm-generator-asm-19000000.html": pg_product("19000000", "Alternator", replaced_by="19000002"),
        f"{PP}/gm-headlamp-95291999.html": pg_product("95291999", "Headlamp", lr="Driver Side"),
    }


def ford_split_pages() -> dict:
    trims = ["4_cyl_2_3l-5mt", "6_cyl_3_0l-4at", "6_cyl_4_0l-5at"]
    model = page(store_html({}, '<a href="/2030-ford-ranger-parts.html">x</a>', title="Ford Ranger Parts"))
    cat = page(store_html({}, "".join(f'<a href="/2030-ford-ranger--{t}-parts.html">x</a>' for t in trims),
                          title="2030 Ford Ranger Parts - FordPartsGiant.com"))
    out = {f"{F}/ford-ranger-parts.html": model, f"{F}/2030-ford-ranger-parts.html": cat}
    for t in (trims[0], trims[-1]):
        out[f"{F}/2030-ford-ranger--{t}-parts.html"] = page(store_html(
            {}, f'<a href="/parts-list/2030-ford-ranger--{t}/electrical/alternator_and_mountings.html">x</a>'
                f'<a href="/parts-list/2030-ford-ranger--{t}/electrical/starter_motor.html">x</a>',
            title=f"2030 Ford Ranger {t} Parts"))
    return out
