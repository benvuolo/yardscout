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
ok(on == ["www.fordpartsgiant.com", "www.jeeppartsdeal.com", "www.lexuspartsnow.com"], f"wheels sites {on}")
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

print("OK" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
