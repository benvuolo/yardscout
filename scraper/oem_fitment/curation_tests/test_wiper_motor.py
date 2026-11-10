#!/usr/bin/env python3
"""Tier C wiper-motor rules (ops/interchange.md §10 wiper handover): the end
axis (F windshield / R rear), twin-motor sides, packaging and the slot sets."""
from _util import check, done
import policy
import positions as P

W = "wiper-motor"
for text, want in [("Motor Assy-Windshield Wiper", "F"), ("Motor, FR. Wiper", "F"), ("Front Motor", "F"),
                   ("Motor Assy-Rear Wiper", "R"), ("Motor, RR. Windshield Wiper", "R"),
                   ("Motor Assy., RR. Windshield Wiper", "R"), ("MOTOR Liftgate Wiper", "R"),
                   ("Motor Assy-Back Door Wiper", "R"), ("Drive Assy-Rear Window Wiper", "R"),
                   ("Wiper Motor", None), ("Motor", None), ("Front and Rear", "X")]:
    check(f"end {text!r} -> {want}", P.end_of_text(text) == want, str(P.end_of_text(text)))
for url, want in [("https://x/parts-list/2011-hyundai-tucson/electrical/windshield_wiper_rear.html", "R"),
                  ("https://x/parts-list/2005-honda-accord/front_windshield_wiper.html", None),
                  ("https://x/ford/windshield_wiper.html", None),
                  ("https://x/ford/rear_liftgate_wiper_washer.html", "R"),
                  ("https://x/oem-parts/a/b/front-motor", None),
                  ("https://x/oem-parts/a/b/rear-motor", "R"),
                  ("https://x/v/2012-vw-jetta/electrical/wipers", None),
                  ("https://x/v/2012-vw-jetta/body-hardware/wiper-washer-components", None)]:
    check(f"end slug {url.rsplit('/', 1)[-1]} -> {want}", P.end_of_slug(url) == want, str(P.end_of_slug(url)))

r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper")])
check("windshield motor -> F", r.slots == ("F",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper, LH"), ("location", "Driver Side")])
check("twin motor LH -> FL", r.slots == ("FL",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("position", "Passenger Side"), ("slug", "https://x/front-motor")])
check("front slug is no evidence (windshield pages carry rear motors) -> position_missing",
      r.reason == "position_missing", str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("slug", "https://x/rear_window_wiper.html")])
check("rear slug fallback -> R", r.slots == ("R",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Motor, RR. Windshield Wiper"), ("position", "Rear")])
check("Honda rear-glass motor -> R", r.slots == ("R",) and r.reason is None, str(r))
r = P.resolve(W, [("name", "Wiper Motor"), ("slug", "https://x/wipers")])
check("no end anywhere -> position_missing, blocks every slot",
      r.reason == "position_missing" and set(r.slots) == {"F", "FL", "FR", "R"}, str(r))
r = P.resolve(W, [("name", "Motor Assy - Wiper"), ("position", "Rear"), ("slug", "https://x/windshield_front_wiper.html")])
check("slug only a fallback: position Rear on a front page -> R", r.slots == ("R",), str(r))
r = P.resolve(W, [("name", "Motor Assy-Rear Wiper"), ("note", "Front wiper")])
check("rear name + front note -> position_conflict", r.reason == "position_conflict", str(r))
r = P.resolve(W, [("name", "Motor Assy-Rear Wiper"), ("location", "Driver Side")])
check("rear motor with a side -> position_conflict", r.reason == "position_conflict", str(r))
r = P.resolve(W, [("name", "Motor Assy-Windshield Wiper"), ("location", "Left or Right")])
check("one number both sides -> position_conflict", r.reason == "position_conflict", str(r))

for names, want in [(["Motor Assy-Windshield Wiper"], "motor"), (["Drive Assy-Windshield Wiper"], "drive"),
                    (["Motor And Linkage Assy"], "drive"), (["MOTOR KIT Windshield Wiper"], "kit"),
                    (["MOTOR PACKAGE Front Wiper"], "kit"), (["Linkage Assy - Wiper"], "linkage"),
                    (["MOTOR, WIPER (EXCEPT CIRCUIT BOARD)"], "motor-ecb"),
                    (["MODULE ASM, WSW (W/ TRANSMISSION)"], "module"), (["Motor & Link Assy-Wiper"], "module")]:
    check(f"wiper packaging {names[0]!r} -> {want}", P.packaging(W, "x", "x", names) == want,
          P.packaging(W, "x", "x", names))

req = [set(x) for x in policy.cat_policy(W)["required"]]
check("F alone closes", {"F"} in req)
check("F + R closes", {"F", "R"} in req)
check("twin pair closes", {"FL", "FR"} in req and {"FL", "FR", "R"} in req)
check("a lone sided front motor closes nothing", {"FL"} not in req and {"FL", "R"} not in req)
check("rear alone closes nothing", {"R"} not in req)
check("F with a twin half is not a configuration", not any({"F", "FL"} <= s for s in req))
check("NOUN wiper-motor", policy.NOUN.get(W) == r"wiper")
done("test_wiper_motor")
