"""Tier W (wheels) include/exclude rules, pure checks (ops/interchange.md
"Wheels"). Road-wheel assemblies are kept; caps, nuts, locks, sensors and
spare / temporary wheels are not. Names are typical catalog spellings, not
crawled rows: the first crawl's list manifests are the real check."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import crawl  # noqa: E402
from sites import fordpartsgiant as F, jeeppartsdeal as J, lexuspartsnow as L  # noqa: E402

fails = []


def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


ok(crawl.TIERS.get("W") == ["wheels"], "crawl tier W = [wheels]")
wl = json.loads((ROOT / "worklist.json").read_text())["sites"]
on = sorted(s for s, e in wl.items() if e.get("wheels"))
ok(on == ["www.fordpartsgiant.com", "www.gmpartsgiant.com", "www.hyundaipartsdeal.com", "www.jeeppartsdeal.com",
          "www.lexuspartsnow.com", "www.mbpartsgiant.com", "www.vwpartsgiant.com"], f"wheels sites {on}")
ok(not any(wl[s].get("wheels") for s in wl if "kia" in s), "Kia not on tier W (reuses Hyundai rules; not asked yet)")
ok(not any(wl[s].get("wheels") for s in wl if re.search(r"honda|acura|nissan|infiniti|mopar|subaru", s)),
   "no wheels tier on Honda/Acura/Nissan/Infiniti (other session), Mopar (blocked), Subaru (withheld)")

inc, exc = J.RULES["wheels"]
jk = lambda n: bool(re.search(inc, n, re.I)) and not re.search(rf"\b(?:{exc})", n, re.I)
for n in ["Wheel - Aluminum", "Wheel, Steel", "Wheel", "Wheel - Chrome"]:
    ok(jk(n), f"jeep keeps {n!r}")
for n in ["Wheel - Spare", "Wheel - Temporary Use Spare", "Cap - Wheel Center", "Nut - Wheel Lug",
          "Wheel Lock Kit", "Sensor - Tire Pressure", "Weight - Wheel Balance", "Wheel Cover"]:
    ok(not jk(n), f"jeep drops {n!r}")

linc, lexc = L.RULES["wheels"]
lk = lambda n: bool(linc.search(n)) and not lexc.search(n)
for n in ["WHEEL, DISC", "Wheel, Disc", "Disc Wheel"]:
    ok(lk(n), f"lexus keeps {n!r}")
for n in ["ORNAMENT SUB-ASSY, WHEEL HUB", "CAP SUB-ASSY, WHEEL HUB", "NUT, HUB", "WHEEL, DISC (SPARE)"]:
    ok(not lk(n), f"lexus drops {n!r}")

fr = F.PARTS["wheels"]
row = lambda pn, main, remark="": {"pn": pn, "group": "WHEELS", "main": main, "remark": remark}
ok(fr.why(row("BL3Z-1007-A", "Wheel Assy"), "") is None, "ford keeps 1007 wheel")
ok(fr.why(row("BL3Z-1007-B", "Wheel Assy", "Spare"), "") is not None, "ford drops a 1007 spare")
ok(fr.why(row("BL3Z-1130-A", "Cover - Wheel"), "") == "include_miss", "ford drops a 1130 wheel cover")
ok(bool(re.search(F.SUBCATS["wheels"], "wheels")) and not re.search(F.SUBCATS["wheels"], "steering_wheel"),
   "ford wheels subcat matches 'wheels', not steering_wheel")

# ---- GM, VW, MB, Hyundai: rows exactly as printed on real wheels list pages
# (fetch.py, 2026-11-09: 2016 Trax .../wheels, 2008 Passat and 2008 C350
# suspension/wheels, 2005 XG350 chassis/wheel_cap), plus spellings the
# exclusions must catch.
from sites import _partsgiant as PG, gmpartsgiant as G, hyundaipartsdeal as H  # noqa: E402
from sites import vwpartsgiant as V, mbpartsgiant as MB  # noqa: E402


def pg_keep(cfg, cat, group, main=None, remark="", info=()):
    r = {"pn": "1", "url": "https://x/1", "group": group, "main": main or group, "remark": remark, "info": list(info)}
    return PG._verdict(cfg, cfg.parts[cat], r)[0] is None


ok(pg_keep(G.CFG, "wheels", "WHEEL, Rear or Spare",
           remark="WHEEL (PKG),(11.7876 KG)(INSTALL 0.30)(REQS ALUMINUM WHEEL TAG 14002325)(18X7)"),
   "gm keeps the real Trax 'WHEEL, Rear or Spare' 18X7 road wheel")
ok(pg_keep(G.CFG, "wheels", "WHEEL, Front", remark="ALUMINUM (17X7.5)"), "gm keeps 'WHEEL, Front' aluminum")
for g, rem in [("WHEEL, Spare", "WHEEL (16X4)"), ("WHEEL, Rear or Spare", "SPARE (16X4)(COMPACT)"),
               ("WHEEL, Front", "WHEEL (T125/70R16)(TEMPORARY)"), ("CAP, Wheel Hub", "CAP"),
               ("NUT, Wheel", "NUT"), ("COVER, Wheel", "COVER"), ("WHEEL COVER, Front", ""),
               ("WHEEL, Steering", "STEERING WHEEL"), ("SENSOR, Tire Pressure", ""), ("WEIGHT, Wheel Balance", ""),
               ("WHEEL, Rear", "WHEEL (PART OF 5)")]:
    ok(not pg_keep(G.CFG, "wheels", g, remark=rem), f"gm drops {g!r} / {rem!r}")
ok(bool(re.search(G.SUBCATS["wheels"], "wheels")) and bool(re.search(G.SUBCATS["wheels"], "wheels_wheel_covers"))
   and not any(re.search(G.SUBCATS["wheels"], x) for x in ["spare_wheel", "wheel_covers", "tire_pressure_sensor",
                                                            "spare_wheel_carrier", "drive_shaft_front_wheel"]),
   "gm wheels subcats: wheels pages only")

for n in ["Wheel Assy-Aluminium", "Wheel Assy-Steel"]:
    ok(pg_keep(H.CFG, "wheels", n), f"hyundai keeps {n!r}")
for n in ["Wheel Assy-Temporary", "Cap Assy-Aluminium Wheel Hub", "Cap Assy-Wheel Hub", "Nut-Hub",
          "Clamp-Spare Tire", "Pad-Spare Tire", "Wheel Assy-Steel(Spare)", "Sensor Assy-Tpms"]:
    ok(not pg_keep(H.CFG, "wheels", n), f"hyundai drops {n!r}")
ok(not pg_keep(H.CFG, "wheels", "Wheel Assy-Steel", info=["Fit Note: Spare"]), "hyundai drops a steel wheel noted as spare")
ok(re.search(H.SUBCATS["wheels"], "wheel_cap") and not re.search(H.SUBCATS["wheels"], "wheel_kit_alloy"),
   "hyundai wheels subcat chassis/wheel_cap only")

for mod, nm in [(V, "vw"), (MB, "mb")]:
    inc = re.compile(mod.RULES["wheels"][0], re.I)
    for n in ["Wheel, Alloy", "Wheel Alloy", "Wheel"]:
        ok(bool(inc.search(n)), f"{nm} keeps {n!r}")
    for n in ["Spare Wheel", "Wheel, Spare", "Wheel Bolt", "Wheel Bolt Cap", "Wheel Lock Kit", "Center Cap",
              "Valve Stem", "Wheel Cover", "Hub Cap", "Steering Wheel"]:
        ok(not inc.search(n), f"{nm} drops {n!r}")
    ok(bool(re.search(mod.CAT_PAGES["wheels"], "suspension/wheels"))
       and not re.search(mod.CAT_PAGES["wheels"], "suspension/wheel-covers-trim")
       and not re.search(mod.CAT_PAGES["wheels"], "suspension/wheels-trim"), f"{nm} wheels page suspension/wheels only")

print("OK" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
