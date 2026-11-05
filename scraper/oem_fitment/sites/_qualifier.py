"""Qualifier phrases in printed part names (CURATION_SPEC.md §3.2 R5a).

Catalog names say what an assembly includes or leaves out with a qualifier:
"Mirror Assy, Outer Rear View, W/Turn Signal Lamp", "Headlamp Unit Assy,
W/Auto Leveling", "Tube Assy, Fuel Suction W/Pump & Gage", "Radiator Assy,
L/Cap", "Compressor Assy, With Pulley". The words inside the phrase name
contents, not the part, so they must not trigger the exclusion checks.

The phrase runs from the qualifier word to the next "," or ";" (or the end of
the name). The old rule removed only the first word after the qualifier, so
"W/Turn Signal Lamp" left "Signal Lamp" and the mirror was dropped by the
"lamp" exclusion; "W/O Socket & Bulb" left "& Bulb".

Only the exclusion checks see the stripped text. Include rules still run on
the full printed name, so stripping can never make a row match a category
it did not already name.
"""
from __future__ import annotations

import re

# "w/o", "w/", "l/" (Toyota "less") must start a word; "with", "without",
# "less", "incl", "includes", "including" must be whole words ("Wireless" and
# "Lessor" are not qualifiers).
QUALIFIER = re.compile(r"(?:\b(?:w/o|w/|l/)|\b(?:with(?:out)?|less|incl(?:udes|uding)?)\b)[^,;]*", re.I)


def strip_qualifiers(s: str | None) -> str:
    """The name with every qualifier phrase replaced by one space."""
    return QUALIFIER.sub(" ", s or "")
