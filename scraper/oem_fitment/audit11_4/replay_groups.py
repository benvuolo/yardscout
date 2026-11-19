"""replay_groups.py OUT.json GROUPS_FILE [GROUPS_FILE...]: the payload rows
(junkyard_scraper._oem_entries: gated apps in the 6-element shape) of each
curated groups/<ns>.json, held categories left out as the payload builder
does (_oem_held), written as [{id, ns, cat, apps, pn, tier}] for
lot_replay.mjs (round3-1119). Read-only; no fetch."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scraper"))
import junkyard_scraper as js  # noqa: E402


def payload_rows(paths):
    out = []
    for p in paths:
        doc = json.loads(Path(p).read_text())
        ns = doc["ns"]
        groups, _vg = js._oem_entries(ns, doc)
        out += [{k: g[k] for k in ("id", "ns", "cat", "apps", "pn", "tier", "note")}
                for g in groups if not js._oem_held(g["cat"], ns)]
    return out


if __name__ == "__main__":
    rows = payload_rows(sys.argv[2:])
    Path(sys.argv[1]).write_text(json.dumps(rows))
    print(f"replay_groups: {len(rows)} payload groups from {len(sys.argv) - 2} files")
