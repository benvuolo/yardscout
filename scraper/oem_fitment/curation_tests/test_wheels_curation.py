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

print("OK" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
