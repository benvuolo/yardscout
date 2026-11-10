"""Position, slot and packaging resolution (CURATION_SPEC.md §5.8). Pure.

Sources: the product page's `position`, each list `Location`, PartsGiant
"Location:" info, tokens in `name` / `aux_desc`, POSITION note clauses, and
the list URL slug for the door axis only. `other_names` is never a source
(§1: 35 of 166 Toyota mirror records name the wrong side there).

All sources must agree on every axis. A disagreement, or L and R in one
source without a both-sides pattern, is `position_conflict`; a required axis
with no value is `position_missing`. Either way the record goes into every
slot it could occupy and blocks them all, so ambiguity only removes claims.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import policy  # noqa: E402

SIDE_L = re.compile(r"\b(driver|drivers|driver's|left|lh|l/h|lt)\b", re.I)
SIDE_R = re.compile(r"\b(passenger|passengers|passenger's|right|rh|r/h|rt)\b", re.I)
SIDE_B = re.compile(r"left\s*(or|and|/|&)\s*right|\blh\s*/\s*rh\b|both\s+sides|either\s+side", re.I)
DOOR_F = re.compile(r"\b(front|fr|frt)\b", re.I)
DOOR_R = re.compile(r"\b(rear|rr)\b", re.I)
DOOR_S = re.compile(r"\bslid(e|ing)\b", re.I)
MOUNT_BODY = re.compile(r"\bon\s+(body|side\s+panel|quarter\s+panel)\b", re.I)
MOUNT_LID = re.compile(r"\bon\s+(trunk\s+lid|deck\s*lid|back\s+door|lift\s*gate|tail\s*gate)\b", re.I)

# wiper-motor end axis (tier C, 2026-11-10). F = windshield, R = rear window,
# liftgate, back door or tailgate. A rear word wins over "windshield": Honda
# and Acura print "Motor, RR. Windshield Wiper" for the rear-glass motor.
# An explicit front word together with a rear word is a conflict.
END_FX = re.compile(r"\b(front|fr|frt)\b", re.I)
END_W = re.compile(r"\b(windshield|windscreen|w/shield)\b", re.I)
END_R = re.compile(r"\b(rear|rr|liftgate|lift\s+gate|tailgate|tail\s+gate|back\s*door|back\s+(window|glass)"
                   r"|rear\s+window|quarter\s+window)\b", re.I)
MIRROR_CATS = {"side-mirrors", "tow-mirrors"}
LAMP_CATS = {"headlights", "tail-lights"}


@dataclass(frozen=True)
class Resolution:
    slots: tuple            # every slot the record may occupy
    reason: str | None      # None, "position_conflict", "position_missing", "unexpected_position"
    side: str | None = None
    door: str | None = None
    mount: str | None = None


def _strip_for(cat: str, text: str) -> str:
    t = text or ""
    if cat in MIRROR_CATS:
        # "Rear Outer Passenger Side" is the passenger mirror (§5.8)
        t = re.sub(r"\b(rear|outer|outside|rr)\b", " ", t, flags=re.I)
    if cat in LAMP_CATS:
        # Jeep prints "Front Driver Side" on headlamps (§5.8)
        t = re.sub(r"\bfront\b", " ", t, flags=re.I)
    return t


def side_of(text: str, cat: str = "") -> str | None:
    """'L', 'R', 'B' (one number for both sides), 'X' (both named without a
    both-sides pattern) or None."""
    t = _strip_for(cat, text)
    if SIDE_B.search(t):
        return "B"
    l, r = bool(SIDE_L.search(t)), bool(SIDE_R.search(t))
    if l and r:
        return "X"
    return "L" if l else "R" if r else None


def door_of_text(text: str) -> str | None:
    f, r, s = bool(DOOR_F.search(text or "")), bool(DOOR_R.search(text or "")), bool(DOOR_S.search(text or ""))
    n = f + r + s
    if n > 1:
        return "X"
    return "F" if f else "R" if r else "S" if s else None


def door_of_slug(url: str) -> str | None:
    """The list URL's sub slug, door axis only (§5.8): front-door-body /
    front-door -> F, rear-door-body / rear-door -> R, sliding-door-body -> S;
    door-body / door give no value. PartsGiant slugs use "_"."""
    seg = (url or "").rstrip("/").rsplit("/", 1)[-1].lower().replace(".html", "").replace("_", "-")
    if re.search(r"(^|-)slid(e|ing)-door", seg):
        return "S"
    if re.search(r"(^|-)front-door", seg):
        return "F"
    if re.search(r"(^|-)rear-door", seg):
        return "R"
    return None


def end_of_text(text: str) -> str | None:
    """wiper-motor end: 'F', 'R', 'X' (both an explicit front and a rear
    word) or None."""
    t = text or ""
    fx, w, r = bool(END_FX.search(t)), bool(END_W.search(t)), bool(END_R.search(t))
    if r and fx:
        return "X"
    if r:
        return "R"
    return "F" if (fx or w) else None


def end_of_slug(url: str) -> str | None:
    """wiper-motor end from the list URL's last segment ("rear_window_wiper",
    "windshield_wiper_rear"); used only when no other source states an end
    (resolve). Rear only: a windshield page can carry the rear motor
    (oem-raw@796a77b: fordpartsgiant windshield_front_wiper and
    windshield_wiper_motor_washer list "Rear" motors, hyundaipartsdeal
    windshield_wiper lists "Motor Assy-Rear Wiper"), while no rear page
    listed a front motor. "wipers" / "wiper-washer-components" give none."""
    seg = (url or "").rstrip("/").rsplit("/", 1)[-1].lower().replace(".html", "").replace("_", " ").replace("-", " ")
    return "R" if end_of_text(seg) == "R" else None


def mount_of(text: str) -> str | None:
    b, l = bool(MOUNT_BODY.search(text or "")), bool(MOUNT_LID.search(text or ""))
    if b and l:
        return "X"
    return "body" if b else "lid" if l else None


def _agree(vals: list[str | None]) -> tuple[str | None, bool]:
    """(value, conflict)."""
    got = {v for v in vals if v is not None}
    if "X" in got:
        return None, True
    if len(got) > 1:
        return None, True
    return (got.pop() if got else None), False


def resolve(cat: str, sources: list[tuple[str, str]]) -> Resolution:
    """sources: [(kind, text)], kind in {"position", "location", "name",
    "note", "slug"}. "slug" feeds the door axis only."""
    pol = policy.cat_policy(cat)
    axes = pol["axes"]
    sides = [side_of(t, cat) for k, t in sources if k != "slug" and t]
    doors = []
    if "door" in axes or cat == "window-switch":
        doors = [door_of_text(t) for k, t in sources if k != "slug" and t]
        doors += [door_of_slug(t) for k, t in sources if k == "slug" and t]
    mounts = [mount_of(t) for k, t in sources if k in ("note", "position", "location") and t] \
        if cat == "tail-lights" else []
    side, s_conf = _agree(sides)
    door, d_conf = _agree(doors)
    mount, m_conf = _agree(mounts)
    all_slots = tuple(pol["slots"])
    if "end" in axes:
        return _resolve_end(cat, sources, side, s_conf)
    if not axes:
        if s_conf or side in ("L", "R", "B"):
            return Resolution(all_slots[:1], "unexpected_position", side, None)
        return Resolution(all_slots[:1], None)
    if s_conf or d_conf or m_conf:
        return Resolution(_slots(cat, None, None), "position_conflict", side, door, mount)
    if cat == "window-switch":
        # the driver master switch: slot DM is decided by window_switch_slot()
        return Resolution(("DM",), None if side else "position_missing", side, door, mount)
    if side is None or ("door" in axes and door is None):
        return Resolution(_slots(cat, side, door), "position_missing", side, door, mount)
    return Resolution(_slots(cat, side, door), None, side, door, mount)


def _resolve_end(cat: str, sources, side, s_conf) -> Resolution:
    """wiper-motor: end from position / location / name / note text; the list
    slug only when none of those states one. Rear motors carry no side; a
    front motor with a side is one of a twin pair (FL / FR). Ambiguity
    blocks every slot the record could occupy."""
    all_slots = tuple(policy.cat_policy(cat)["slots"])
    ends = [end_of_text(t) for k, t in sources if k != "slug" and t]
    end, e_conf = _agree(ends)
    if end is None and not e_conf:
        end, e_conf = _agree([end_of_slug(t) for k, t in sources if k == "slug" and t])
    if s_conf or e_conf or side == "B" or (end == "R" and side is not None):
        return Resolution(all_slots, "position_conflict", side, end)
    if end is None:
        return Resolution(all_slots, "position_missing", side, None)
    if end == "R":
        return Resolution(("R",), None, None, "R")
    return Resolution(({"L": "FL", "R": "FR"}.get(side, "F"),), None, side, "F")


def _slots(cat: str, side: str | None, door: str | None) -> tuple:
    pol = policy.cat_policy(cat)
    sides = ["L", "R"] if side in (None, "B") else [side]
    if "door" in pol["axes"]:
        doors = ["F", "R", "S"] if door is None else [door]
        return tuple(d + s for d in doors for s in sides if d + s in pol["slots"])
    if cat == "window-switch":
        return ("DM",)
    return tuple(s for s in sides if s in pol["slots"])


def window_switch_slot(name: str, aux: str, side: str | None, door: str | None) -> tuple[str | None, str | None]:
    """(slot, reason) for a window-switch record (§5.8): Toyota-style
    "Master Switch" rows map to DM unless they resolve to the passenger side;
    other rows (Mopar "Switch - Window And Door Lock") map to DM only when
    the position resolves to the driver (L) front door. A passenger switch is
    out of the category ("out_of_category"); no side is position_missing."""
    text = f"{name or ''} | {aux or ''}"
    if re.search(r"\bmaster\b", text, re.I):
        if side == "R":
            return None, "out_of_category"
        return "DM", None
    if side == "R" or door in ("R", "S"):
        return None, "out_of_category"
    if side == "L" and door == "F":
        return "DM", None
    return "DM", "position_missing"


# ------------------------------------------------------------- packaging
def _head(s: str) -> str:
    return re.split(r"[,;(]", s or "", maxsplit=1)[0]


def packaging(cat: str, ns: str, pn: str, names: list[str], notes: list[str] = ()) -> str:
    """window-regulator: motor | assy | reg | reg? | door-module (§5.8 and hub
    decision P1); climate-control: switch-module (hub decision T1) | assy;
    every other category: "". Rules run on the OEM name fields (never
    other_names, never description)."""
    names = [n for n in names if n]
    if cat == "climate-control":
        base = re.sub(r"[^0-9A-Z]", "", (pn or "").upper())[:5]
        if ns == "toyota" and base in policy.TOYOTA_CLIMATE_SWITCH_BASES:
            return "switch-module"
        if any(re.search(r"control\s+sub-?\s*ass(y|embly)", n, re.I) for n in names):
            return "switch-module"
        return "assy"
    if cat == "wiper-motor":
        return wiper_packaging(names, notes)
    if cat != "window-regulator":
        return ""
    text = " | ".join(names)
    if policy.DOOR_MODULE_RE.search(text):
        return "door-module"
    has_reg = bool(re.search(r"regulator", text, re.I))
    motor_head = any(re.match(r"\s*(motor|power\s+window\s+motor)\b", n, re.I)
                     or re.search(r"power\s+window\s+motor", n, re.I) for n in names)
    reg_in_head = any(re.search(r"regulator", _head(n), re.I) for n in names)
    if motor_head and not reg_in_head:
        return "motor"
    if has_reg and re.search(r"(w/|with)\s*motor", text, re.I) and not re.search(r"(w/o|without|less)\s*motor", text, re.I):
        return "assy"
    if has_reg and re.search(r"sub-?\s*ass(y|embly)|(w/o|without|less)\s*motor", text, re.I):
        return "reg"
    return "reg?"


def regulator_slot_ok(members: list[tuple[str, str]], chains: dict[str, int]) -> str | None:
    """members: [(class key, packaging)] of one door slot; chains: class key
    -> chain id. Returns None when the slot is exactly one allowed
    configuration (P1: one chain of assy; P2: one chain of reg + one chain of
    motor; hub P1: one chain of door-module), else the blocking reason."""
    if not members:
        return "empty_slot"
    if any(p == "reg?" for _, p in members):
        return "packaging_unstated"
    by_pack: dict[str, set] = {}
    for k, p in members:
        by_pack.setdefault(p, set()).add(chains.get(k, k))
    if any(len(v) > 1 for v in by_pack.values()):
        return "packaging_split"
    packs = set(by_pack)
    if packs in ({"assy"}, {"reg", "motor"}, {"door-module"}):
        return None
    if packs == {"reg"} or packs == {"motor"}:
        return "packaging_incomplete"
    return "packaging_split"


# ------------------------------------------------- wiper-motor packaging
# (tier C, 2026-11-10; ops/interchange.md §10 wiper handover). Members of one
# slot must share one packaging; groups never mix them.
WIPER_LINKAGE_ONLY = re.compile(r"^\s*(linkage|link|pivot)\b", re.I)
WIPER_MODULE = re.compile(r"\bmodule\b|system,?\s*complete|motor\s*(&|and)\s*link\b", re.I)
WIPER_DRIVE = re.compile(r"^\s*drive\b|motor\s+(and|&|w/|with)\s+linkage|linkage\s+(and|&)\s+motor", re.I)
WIPER_KIT = re.compile(r"\b(kit|package|pkg)\b", re.I)
WIPER_ECB = re.compile(r"except\s+circuit\s+board", re.I)
# Ford "Smart" wiper motor w/ integral wiper control module (hub 2026-11-10):
# its own packaging, never matched with a plain motor. Ford states it only in
# the list remark, so this one rule also reads the row notes.
WIPER_CTL = re.compile(r"\bsmart\b[^|]*\bmotor|integral\s+(wiper\s+)?control|w/\s*(wiper\s+)?control\s+module", re.I)


def wiper_packaging(names: list[str], notes: list[str] = ()) -> str:
    """linkage (not a motor: out of the category) | module | drive (motor +
    linkage: Nissan/Infiniti "Drive Assy", Ford "Motor And Linkage Assy") |
    kit (Jeep "MOTOR KIT"/"MOTOR PACKAGE") | motor-ecb (GM "EXCEPT CIRCUIT
    BOARD") | motor-ctl (Ford "Smart" motor with integral control module,
    from names or row notes) | motor. Other rules run on the OEM name fields
    only."""
    names = [n for n in names if n]
    text = " | ".join(names)
    if WIPER_CTL.search(" | ".join([text] + [n for n in notes if n])):
        return "motor-ctl"
    if names and all(WIPER_LINKAGE_ONLY.match(n) and not re.search(r"\bmotor\b", n, re.I) for n in names):
        return "linkage"
    if WIPER_MODULE.search(text):
        return "module"
    if WIPER_DRIVE.search(text):
        return "drive"
    if WIPER_KIT.search(text):
        return "kit"
    if WIPER_ECB.search(text):
        return "motor-ecb"
    return "motor"
