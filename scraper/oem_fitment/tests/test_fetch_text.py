#!/usr/bin/env python3
"""fetch.py --text never clips a page silently (2026-11-09: the old 400-line
default hid list rows at the bottom of long pages, e.g. Lexus, from
verifiers). Offline: no request is made."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fetch  # noqa: E402

FAILS = 0


def check(name, ok):
    global FAILS
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        FAILS += 1


html = "<html><body>" + "".join(f"<div>row {i}</div>" for i in range(1, 6001)) + "</body></html>"
full = fetch.text_lines(html)
check("6000-line page parses to 6000 text lines", len(full) == 6000)

d = fetch.text_output(html)
check("default limit is at least 5000", fetch.TEXT_MAX_LINES >= 5000)
check("past the default: marker line names where it was cut and the total",
      d["text"][-1] == "[TRUNCATED at 5000 of 6000 lines]" and len(d["text"]) == 5001)
check("past the default: text_truncated true, text_lines_total 6000",
      d["text_truncated"] is True and d["text_lines_total"] == 6000)
check("kept lines are the first 5000, in order", d["text"][:5000] == full[:5000])

d2 = fetch.text_output(html, 400)
check("an explicit small limit marks the cut too (400 of 6000)",
      d2["text"][-1] == "[TRUNCATED at 400 of 6000 lines]" and d2["text_truncated"] is True)

small = "<p>a</p><p>b</p><p>c</p>"
d3 = fetch.text_output(small)
check("a short page is whole: no marker, text_truncated false",
      d3["text"] == ["a", "b", "c"] and d3["text_truncated"] is False and d3["text_lines_total"] == 3)
d4 = fetch.text_output(small, 3)
check("a page exactly at the limit is not marked", d4["text"] == ["a", "b", "c"] and d4["text_truncated"] is False)

src = (HERE.parent / "fetch.py").read_text()
check("the CLI uses text_output and the 5000 default (no bare slice)",
      "out.update(text_output(" in src and "default=TEXT_MAX_LINES" in src and "[: a.max_lines]" not in src)

print(f"\n{'OK' if not FAILS else 'FAILED'} test_fetch_text ({FAILS} failures)")
sys.exit(1 if FAILS else 0)
