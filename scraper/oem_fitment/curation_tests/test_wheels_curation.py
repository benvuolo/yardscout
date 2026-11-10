"""Wheels curation (ops/interchange.md "Wheels"): a compact / mini / temporary
spare is never offered as a road wheel; a full-size spare that is the same
number as the road wheels is. Strings are real oem-raw text (2026-11-09,
oem-raw@4a733550)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import curate  # noqa: E402,F401  (imports policy the way the curator does)
import policy  # noqa: E402

fails = []


def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


RX = policy.WHEEL_COMPACT_SPARE_RE
for t in ["[TBK] Compact Spare",                                   # Mopar 4721567AB, 2010 Grand Caravan
          '17" Mini Steel Spare Wheel, With 22" Wheels',          # Ford 7T4Z-1007-B
          '17" X 4.5 Mini Steel Spare Wheel, With 16" Wheels',
          "Spare Wheel - Mini Steel, With 16\" Wheels",
          "Wheel - Temporary Use Spare", "T125/70D16", "T-Type spare"]:
    ok(bool(RX.search(t)), f"compact spare: {t!r}")
for t in ["With Full Size Spare, 16 Inch",                        # Mopar 5105078AB, road wheel elsewhere
          "Wheel, Disc (For Spare)",                              # Lexus full-size matching spare
          '16", WDJ With Full Spare', "Spare Wheel, 16x6.5", "[WKB] Matching Spare Wheel",
          "Wheel, Alloy", '17", Code WFU', "Wheel Assy - Spare"]:
    ok(not RX.search(t), f"not a compact spare: {t!r}")

# notes that list the CAR's options are not read on these sites
for s in ["www.hyundaipartsdeal.com", "www.kiapartsnow.com", "www.lexuspartsnow.com", "www.toyotapartsnow.com"]:
    ok(s in policy.WHEEL_NOTES_ARE_OPTIONS, f"{s}: notes are car options for the spare check")
ok("www.fordpartsgiant.com" not in policy.WHEEL_NOTES_ARE_OPTIONS
   and "www.jeeppartsdeal.com" not in policy.WHEEL_NOTES_ARE_OPTIONS,
   "Ford / Mopar notes name the part (read)")
ok(bool(RX.search("TEMPORARY - STEEL WHEEL & TIRE (MINI)"))
   and bool(RX.search("&SPARE TIRE-REINFORCED TEMPORARY(T165/90D18)")),
   "option-list notes WOULD match: that is why those sites' notes are skipped")

# the refusal is wired into Curation.verify for the wheels category
src = (ROOT / "curate.py").read_text()
ok(re.search(r'wheel_compact_spare', src) is not None and "WHEEL_NOTES_ARE_OPTIONS" in src,
   "curate.verify refuses wheel_compact_spare and honours WHEEL_NOTES_ARE_OPTIONS")

# group-level basis (§11.4 round 1, 2026-11-09): stated diameter must agree, no spare
# note, no other numbered model; Toyota/Lexus wheels stay within one exact model
D = policy.WHEEL_DIAMETER_RE
ok({m.group(1) for m in D.finditer("17x6.5")} == {"17"} and {m.group(1) for m in D.finditer("16 Inch")} == {"16"}
   and {m.group(1) for m in D.finditer('16", WDJ')} == {"16"} and {m.group(1) for m in D.finditer("Steel Wheels, 16x6.5\"")} == {"16"},
   "diameter read from '17x6.5', '16 Inch', '16\"'")
ok(not D.search("Code WFU") and not D.search("2500, 3500"), "no diameter in a bare sales code or model list")
ok(set(policy.MODEL_NUMBER_RE.findall("3500, WD4, WF1")) - set(policy.MODEL_NUMBER_RE.findall("Ram 2500")) == {"3500"},
   "'3500' on a Ram 2500 page names another model (52121267AC)")
ok(bool(policy.WHEEL_SPARE_NOTE_RE.search("Spare Wheel ... With Full Size Spare, 17 Inch")), "spare note seen (5105032AA)")
ok("toyota" in policy.WHEEL_SAME_MODEL_ONLY_NS, "Toyota/Lexus wheels groups stay within one exact model (chassis codes)")
ok(all(x in src for x in ["wheel_size_unstated", "wheel_size_conflict", "wheel_model_other", "wheel_spare_note",
                          "wheel_cross_model_chassis"]), "curate.wheel_group_refusal codes wired")

W = policy.WHEEL_WIDTH_RE
ok({float(m.group(1)) for m in W.finditer("Part Notes: 15x6 WJW")} == {6.0}
   and {float(m.group(1)) for m in W.finditer("2009-15, 20x8, Code WP2")} == {8.0}
   and {float(m.group(1)) for m in W.finditer("16 X 6.5 - [WNG]")} == {6.5} and not W.search("16 Inch"),
   "width read from '15x6', '20x8', '16 X 6.5'; none from '16 Inch' (round 2: 1SZ98PAKAA, 1DP88SZ0AB)")
ok("wheel_width_conflict" in src and "wheel_spare_description" in src, "width conflict and spare description wired")

ok(policy.WHEELS_AUDITED_NS == frozenset({"mopar", "mb", "vag"}) and "wheels_not_audited" in src,
   "wheels publish only in audited namespaces (mopar, mb, vag; 2026-11-09)")

# MB / VW census (2026-11-09)
B = policy.WHEEL_BODY_RE
ok({m.group(1).lower() for m in B.finditer("Wagon, 5 Spoke, With Grooved Spokes, 17X7")} == {"wagon"}
   and {m.group(1).lower() for m in B.finditer('17", 5 Double Spokes, Type 1;Coupe')} == {"coupe"},
   "body words read: Jetta 'Wagon' vs Beetle 'Coupe' (1J0-601-025-AB-Z31)")
SP = policy.WHEEL_SPOKE_RE
ok({m.group(1) for m in SP.finditer('17", 10 Spoke')} == {"10"} and {m.group(1) for m in SP.finditer('17", 8 Spoke, Porto')} == {"8"}
   and {m.group(1) for m in SP.finditer("5 Double Spokes")} == {"5"}, "spoke counts read (5K0-601-025-AN-8Z8)")
AX = policy.WHEEL_AXLE_RE
ok(bool(AX.search("Front, Type #11, 7.5X17")) and bool(AX.search("Rear")) and not AX.search("Frontier")
   and not AX.search("Steel Wheels, 16x6.5"), "axle-limited notes seen; 'Frontier' is not")
ok(all(x in src for x in ["wheel_axle_limited", "wheel_body_conflict", "wheel_design_conflict"]), "MB/VW rules wired")

# Hyundai / Kia census (2026-11-10)
BO = policy.WHEEL_BODY_OPTION_RE
ok({m.group(1) for m in BO.finditer("Fitting Vehicle Options: [Coupe - 2Door 5P] 2.0L")} == {"Coupe - 2Door 5P"}
   and {m.group(1) for m in BO.finditer("[Sedan - 4Door 5P], [Sedan - 5Door 5P]")} == {"Sedan - 4Door 5P", "Sedan - 5Door 5P"},
   "body option codes read (529091M550, 529101M650)")
PD = policy.WHEEL_PRODUCTION_RE
m = PD.search("Production Date: 02/2009-08/2010")
ok(m is not None and (m.group(1), m.group(2)) == ("2009", "2010") and PD.search("Production Date: 06/2009").group(2) is None,
   "production dates read (529101M250, 529101M450)")
ok("wheel_body_option" in src and "wheel_production_date" in src, "Hyundai/Kia rules wired")

print("OK" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
