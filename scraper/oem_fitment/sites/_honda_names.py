"""Honda/Acura catalog rules shared by hondapartsnow.py and acurapartswarehouse.py.

Both sites print American Honda's own part names ("Headlight Assy., R.",
"Regulator Assy., R. FR. Door Power", "Switch Assy., Power Window Master").
Learned through fetch.py on 2026-11-05 from the seed-year trim catalogs of
every worklist segment (two trims each); see ops/interchange.md.

  * diagram (subcategory) slugs often carry an engine or supplier suffix:
    alternator_denso_l4, radiator_toyo, mirror_fixed, p_s_pump_bracket.
  * names may start with "[Freight Parts] " (shipping class, not part of the
    OEM name). Rules match on the name with that prefix removed; the record
    keeps the name exactly as printed.
  * reman: "(RMD)" in the name, an "RM" part-number suffix, or "Core Id".
  * side and position are printed in the name: "R." / "L." (right/left),
    "FR." / "RR." (front/rear). Honda product pages have no Position line.
  * trims: catalogs are per body/trim + emission/transmission
    ("4dr_exl_v6_navi-ka_5at"; Acura "4dr_base-ka5at"). KA = 49-state,
    KL = California. We read at most two per year: the base and the
    best-equipped trim of one body style (TRIM selection below).
"""
from __future__ import annotations

import re

FREIGHT = re.compile(r"^\s*\[freight parts\]\s*", re.I)
REMAN = re.compile(r"\(RMD\)|\bcore id\b|\breman", re.I)
REMAN_PN = re.compile(r"RM$", re.I)
BARE_SWITCH = re.compile(r"^switch\s+assy\.?\s*(\*[^*]+\*.*)?$", re.I)
INCLUDES = re.compile(r"\((?:includes?|incl\.?|with|w/)[^)]*\)", re.I)


def oem_name(name: str) -> str:
    return FREIGHT.sub("", name or "").strip()


def matches(cat: str, name: str) -> bool:
    """Include/exclude test on the OEM name. Exclusion words match at a word
    start ("ring" must not hit "Steering")."""
    inc, exc = RULES[cat]
    n = oem_name(name)
    # "(INCLUDES CLUTCH & COIL)" / "(INCLUDES REF #1,2,3)" say what the
    # assembly contains; they are not part of what it is.
    bare = INCLUDES.sub(" ", n)
    return bool(re.search(inc, n, re.I)) and not re.search(r"\b(?:" + exc + ")", bare, re.I)


def is_reman(pn: str, name: str) -> bool:
    return bool(REMAN.search(name or "") or REMAN_PN.search(pn or ""))


# our category -> regex over the diagram (subcategory) slug of the trim
# catalog's parts-list links (the template drops the section slug)
CAT_PAGES = {
    "alternator": r"^alternator(?!_belt)(_|$)",   # old catalogs draw the unit on alternator_bracket
    "starter": r"^starter_motor",
    "ac-compressor": r"^a_c_(air_conditioner_)?compressor",
    "headlights": r"^headlight",
    "tail-lights": r"^taillight",
    "side-mirrors": r"^mirrors?(_|$)",
    "window-regulator": r"^((front|rear|slide)_)?door_(glass|windows?)(_door)?(_regulator)?$",
    "window-switch": r"^((front_)?door_lining|switch)$",
    "climate-control": r"^(heater_control(?!_rear|_lever)|auto_air_conditioner_control(?!_rear)|center_module[a-z_]*air_conditioner)",
    "fuel-pump-module": r"^(fuel_tank|fuel_pump[a-z_]*)$",
    "throttle-body": r"^throttle_body",
    "power-steering-pump": r"^p_s_pump(_|$)",   # pre-2003 catalogs draw the pump on p_s_pump_bracket
    "gauge-cluster": r"^(combination_)?meter(_|$)",
    "ignition-coils": r"^(ignition_coil|plug_hole_coil|plug_top_coil)",
    "radiator": r"^radiator(?!_hose)(_|$)",
    "door-front": r"^(front_door_panels?|door_panels?)$",
    "door-rear": r"^(rear_door_panels?|slide_door_panels?)$",
    "hood": r"^(engine_)?hood$",
    "fender": r"^(front_)?fenders?$",
    "bumper-front": r"^(bumpers?|front_bumper)$",
    "bumper-rear": r"^(bumpers?|rear_bumper)$",
    "grille": r"^(front_)?grille$",
    "trunk-lid": r"^trunk_lid$",
    "tailgate": r"^(lower_)?tailgate$",
    "liftgate": r"^tailgate$",
}
# Honda calls both a pickup bed gate and an SUV/van/hatch rear hatch "Tailgate".
# Our categories split them: pickups -> tailgate, everything else -> liftgate.
PICKUPS = {"Ridgeline"}

SIDE = r"(?:[rl]\.\s*)?"
# (include, exclude) over oem_name(); explicit per category, case-insensitive.
RULES = {
    "alternator": (r"^alternator(\s+assy\.?|\s*\(|,\s*core id|$)",
                   r"belt|bracket|pulley|brush|bearing|frame|cover|rotor|stator|holder|regulator|rectifier|terminal|insulator|bush|stay|fan|nut|tensioner"),
    "starter": (r"^starter(\s+motor)?(\s+assy\.?|\s*\(|,\s*core id|$)",
                r"gear|yoke|armature|holder|brush|bracket|cover|plunger|switch|solenoid|lever|clutch|bush|stay|rubber|bolt|cable|relay"),
    "ac-compressor": (r"^compressor(\s+assy\.?|\s*\(|,|$)|^compressor,\s*core id",
                      r"clutch|valve|switch|sensor|hose|pipe|stator|pulley|plate|ring|stay|bracket|coil|relay|oil|bolt|cover|gasket|seal|thermo|kit"),
    "headlights": (rf"^headlight\s+(assy\.|unit)|^(light|lamp)\s+assy\.?,\s*{SIDE}head|^headlight,\s*{SIDE}",
                   r"bracket|bulb|socket|ballast|inverter|igniter|cord|cover|bezel|lens|level|actuator|garnish|cap|module|unit,\s*(hid|control)|washer|cleaner|nut|screw|harness|seal|gasket|ecu|control unit|light unit,|holder"),
    "tail-lights": (rf"^lamp\s+unit,\s*[rl]\.\s*(tail)?\s*$|^taillight\s+assy\.|^(light|lamp)\s+(assy\.?|unit),\s*{SIDE}(tail|rr\.?\s*combination)|^taillight,\s*{SIDE}|^light assy\.,\s*{SIDE}rr\.?\s*combination",
                    r"bulb|socket|gasket|seal|base|cord|cover|lens\b|reflector|license|garnish|bracket|nut|screw|holder|cushion|harness|inner|trunk lid|lid light|back[- ]?up"),
    "side-mirrors": (rf"^mirror\s+assy\.?,\s*{SIDE}(\(|door|side|$|\w)",
                     r"rearview|room|inside|vanity|glass|cover|cap|housing|actuator|bracket|garnish|base|motor|switch|skull|harness|visor|day/night|interior"),
    "window-regulator": (r"^regulator(\s+assy\.?)?,\s*[rl]\.?\s+(fr|rr)\.?\s*$|^regulator(\s+assy\.?)?,.*\bdoor\b|^regulator(\s+assy\.?)?,.*window|^motor(\s+assy\.?)?,.*power window|^motor(\s+assy\.?)?,.*window regulator|^window regulator",
                         r"switch|handle|channel|run|glass|sash|cable(?!.*regulator)|knob|cover|bracket|bolt|seal|weatherstrip|holder|guide|stopper|garnish|tape|clip|cushion"),
    "window-switch": (r"^switch\s+assy\.?,\s*power\s+window\s+master|^switch\s+assy\.?,\s*.*\bmaster\b.*power\s+window|^power\s+window\s+master\s+switch",
                      r"panel|base|bezel|cover|knob|lamp|bulb|garnish|passenger|sub\b"),
    "climate-control": (r"^control\s+(assy|unit|sub-assy)\.?,\s*(heater|auto\s+air\s*con(ditioner)?|air\s*con(ditioner)?|a/?c|automatic\s+air)|^switch\s+assy\.?,\s*(heater|auto\s+air\s*con(ditioner)?|air\s*con(ditioner)?)\s+control|^heater\s+control\s+assy|^control\s+assy\.?,\s*(climate|hvac)",
                        r"rear|panel|knob|cable|lever|lamp|bulb|sensor|motor|servo|button|bezel|garnish|harness|bracket|base|blower|unit,\s*blower|display|cover|wire|switch,\s*sub"),
    "fuel-pump-module": (r"^module\s+(set|assy)\.?,\s*fuel\s+pump|^pump\s+(set|assy|unit)\.?,\s*fuel(?!\s+(pump\s+)?(cover|filter))|^fuel\s+pump(\s+(assy|module|set))?\b|^pump,\s*fuel",
                         r"filter|regulator|gauge|sender|meter|strainer|nut|gasket|seal|ring|relay|resistor|cover|harness|cushion|holder|band|cap|tube|hose|clip|stay|bracket|kit,\s*(filter|seal)|insulator"),
    "throttle-body": (r"^throttle\s+body\b|^body\s+assy\.?,\s*throttle|^body,\s*throttle",
                      r"gasket|seal|sensor|case|cover|cable|bracket|stay|hose|spacer|o-ring|bolt|heater|insulator|cap"),
    "power-steering-pump": (r"^pump\s+(assy|sub-assy|set)\.?,\s*(power\s+steering|p\.?\s*s\.?)\b|^pump,\s*(power\s+steering|p\.?\s*s\.?)\b|^power\s+steering\s+pump(\s+assy)?\b",
                            r"seal|belt|shaft|pulley|bracket|reservoir|tank|hose|pipe|joint|ring|bolt|kit|cover|valve|switch|bearing|stay|o-ring|gasket|tensioner"),
    "gauge-cluster": (r"^meter\s+assy\.?,\s*combination|^combination\s+meter\s+assy|^meter\s+assy\.?\s*(\(|$)",
                      r"lens|glass|case|visor|panel|circuit|bulb|socket|gasket|screw|garnish|hood|cover|plate|grommet|bracket|harness|sub\b"),
    "ignition-coils": (r"^coil(\s+assy\.?)?,\s*(plug\s+hole|ignition|plug\s+top)|^ignition\s+coil(\s+assy)?\b",
                       r"cap|cord|boot|plug,\s*spark|spark\s+plug|bracket|cover|bolt|igniter|resistor|stay|wire"),
    "radiator": (r"^radiator(\s+assy\.?)?(\s*\(|\s*,\s*\(|$)|^radiator\s+sub-assy",
                 r"cap|hose|petcock|drain|tank|reserve|shroud|fan|motor|cushion|bracket|stay|label|seal|ring|sensor|switch|pipe|mount|support|grille|duct|cover|insulator|bolt|clip"),
    "door-front": (rf"^panel,\s*{SIDE}(fr\.?\s+)?door\b|^door\s+assy\.?,\s*{SIDE}(fr\.?\s+)?|^door,\s*{SIDE}(fr\.?\s+)?$",
                   r"skin|lining|hinge|trim|weatherstrip|seal|checker|garnish|molding|sash|stiffener|reinforce|beam|rr\.|rear|slide|bolt|bracket|switch|tailgate|lid"),
    "door-rear": (rf"^panel,\s*{SIDE}(rr\.?|slide)\s+door\b|^door\s+assy\.?,\s*{SIDE}(rr\.?|slide)\s|^panel,\s*{SIDE}slide\s+door",
                  r"skin|lining|hinge|trim|weatherstrip|seal|checker|garnish|molding|sash|stiffener|reinforce|beam|bolt|bracket|switch|roller|rail|motor|cable|actuator|lock|stopper"),
    "hood": (r"^hood,\s*engine|^hood\s+assy\b|^hood(\s*\(|$)",
             r"hinge|lock|latch|wire|cable|lever|insulator|seal|rubber|stay|support|stopper|cushion|emblem|molding|spoiler|scoop|duct|cover|garnish|nozzle|striker|bracket|grommet|opener"),
    "fender": (rf"^panel\s+set,\s*{SIDE}fr\.?\s+fender\b|^fender,\s*{SIDE}(fr\.?)?(\s*\(|\s*$|\s+fr)|^fender\s+assy\.?,\s*{SIDE}(fr\.?)?(\s*\(dot\)|\s*$)|^fender,\s*{SIDE}$",
               r"inner|liner|garnish|molding|flare|mud|splash|guard|lining|shield|protector|seal|cover|bracket|stay|brace|extension|emblem|cushion|insulator|clip"),
    "bumper-front": (r"^(face|cover),\s*fr\.?\s+bumper(?!\s+(lower|side|lip|corner|spoiler|garnish|molding))|^bumper\s+(face|cover)\s+assy\.?,\s*fr|^bumper,\s*fr\.?(\s*\(|$)|^face,\s*front\s+bumper",
                     r"beam|spoiler|lip|absorber|garnish|molding|grille|bracket|spacer|stay|reinforce|support|cap|guard|step|skid|plate|license|lower\s+cover|side|corner|retainer|extension|hole\s+cover"),
    "bumper-rear": (r"^(face|cover),\s*rr\.?\s+bumper(?!\s+(lower|side|lip|corner|spoiler|garnish|molding))|^bumper\s+(face|cover)\s+assy\.?,\s*rr|^bumper,\s*rr\.?(\s*\(|$)|^face,\s*rear\s+bumper",
                    r"beam|spoiler|lip|absorber|garnish|molding|bracket|spacer|stay|reinforce|support|cap|guard|step|skid|plate|license|lower\s+cover|side|corner|retainer|extension|hole\s+cover|protector|diffuser"),
    "grille": (r"^grille\s+assy\.?,\s*(fr|front|radiator)|^grille,\s*(fr\.?|front|radiator)(\s*\(|\s*\*|$|\s)|^grille\s+assy\.?(\s*\(|\s*\*|$)|^grille,\s*fr\.?\s+bumper\s*$",
               r"emblem|molding|base|cover|mesh|screen|bracket|garnish|lower|upper\s+molding|clip|seal|insert|shutter|lamp|camera|sensor|chrome\s+molding|plate|absorber"),
    "trunk-lid": (r"^lid,\s*trunk|^trunk\s+lid(\s+assy)?\s*(\(|$)|^lid\s+assy\.?,\s*trunk",
                  r"weatherstrip|garnish|lock|hinge|spoiler|lining|cylinder|damper|spring|cable|opener|striker|seal|molding|emblem|light|lamp|switch|handle|stay|cushion|bolt"),
    "tailgate": (r"^tailgate(\s+assy\.?)?(\s*\(|,\s*lower|\s*$)|^(gate|panel),\s*(lower\s+)?tail(gate)?\b|^tailgate,\s*(lower|upper)\b",
                 r"lock|latch|damper|hinge|motor|glass|lining|handle|garnish|spoiler|stay|weatherstrip|seal|switch|cylinder|emblem|molding|light|lamp|cable|striker|actuator|wiper|cushion|stopper|rod|unit|module|trim|cover|bracket|bolt|harness|opener|protector"),
    "liftgate": (r"^tailgate(\s+assy\.?)?(\s*\(|\s*$)|^(gate|panel),\s*tail(gate)?\b|^door\s+assy\.?,\s*tail",
                 r"lock|latch|damper|hinge|motor|glass|lining|handle|garnish|spoiler|stay|weatherstrip|seal|switch|cylinder|emblem|molding|light|lamp|cable|striker|actuator|wiper|cushion|stopper|rod|unit|module|trim|cover|bracket|bolt|harness|opener|protector|lower"),
}

# ---------------------------------------------------------------- trims

# "best-equipped" rank by trim words; base = lowest, best = highest.
_TIER = [
    (r"\b(elite|advance|adv|tourin|tour|touring|type s|type r|a spec|tech|platinum|black edition|sh awd)\b", 5),
    (r"\b(ex l|exl|ex lv6|leather|rtl|prem|premium|sport|si|gs r|ls|exlsul|res)\b", 3),
    (r"\b(ex|exv6|rts|se|special|special edition|spec ed|lx s|hx|sport)\b", 2),
]
_BONUS = [(r"\bv ?6\b|lv6|exv6|lxv6|3 5", 2), (r"\b4wd\b|\bawd\b", 1), (r"\bnavi?\b|navigation", 1),
          (r"\b(res|entertainment)\b", 1)]
# variants we never pick: CNG, regional (Alaska/Hawaii), plant/transmission
# sub-builds and California-only emission packages.
_SKIP = re.compile(r"\b(gx|alaska|hawaii|hcm|jpn|trans|pzev|sul|ul|exlsul|exsul|lxsul)\b|_sul|_ul\b")
_HYBRID = re.compile(r"hybrid", re.I)


def split_trim(slug: str) -> tuple[str, str, str]:
    """'4dr_exl_v6_navi-ka_5at' -> ('4dr', 'exl v6 navi', 'ka_5at');
    Acura '4dr_base-ka5at' -> ('4dr', 'base', 'ka5at')."""
    left, _, em = slug.partition("-")
    body, _, trim = left.partition("_")
    return body, trim.replace("_", " ").strip(), em


def _rank(slug: str) -> int:
    t = " " + split_trim(slug)[1] + " "
    s = 0
    for rx, v in _TIER:
        if re.search(rx, t):
            s = v
            break
    for rx, v in _BONUS:
        if re.search(rx, t):
            s += v
    return s


def pick_trims(slugs: list[str], want_hybrid: bool | None = None) -> list[str]:
    """At most two trims for one model-year: base and best-equipped, both of
    one body style (4dr when the year has one, else the body with the most trims), 49-state (KA)
    and automatic when available. want_hybrid True keeps only hybrid trims,
    False drops them, None leaves them."""
    s = sorted(set(slugs))
    if want_hybrid is True:
        s = [x for x in s if _HYBRID.search(x)]
    elif want_hybrid is False:
        s = [x for x in s if not _HYBRID.search(x)] or s
    s = [x for x in s if not _SKIP.search(split_trim(x)[1].replace("-", " "))] or s
    s = [x for x in s if split_trim(x)[2].lower().startswith("ka")] or s
    s = [x for x in s if not re.search(r"mt$", split_trim(x)[2], re.I)] or s
    if not s:
        return []
    bodies: dict[str, int] = {}
    for x in s:
        bodies[split_trim(x)[0]] = bodies.get(split_trim(x)[0], 0) + 1
    body = "4dr" if "4dr" in bodies else max(bodies, key=lambda b: (bodies[b], b))
    s = [x for x in s if split_trim(x)[0] == body]
    r = sorted(s, key=lambda x: (_rank(x), len(x), x))
    return [r[0], r[-1]] if len(r) > 1 and r[0] != r[-1] else r[:1]


# ---------------------------------------------------------------- template glue

def head(row: dict) -> str:
    """Text the template's COMMON_EXCLUDE is tested on: the OEM name without
    the freight prefix, "(INCLUDES ...)" notes, and the coil type words
    "Plug Hole" / "Plug Top" (Honda's name for coil-on-plug ignition coils,
    "Coil, Plug Hole"; the word "Plug" is not a spark plug there)."""
    n = INCLUDES.sub(" ", oem_name(row.get("main", "")))
    return re.sub(r"\bplug\s+(hole|top)\b", " ", n, flags=re.I)


def rule(cat: str):
    return lambda row, _text: matches(cat, row.get("main", ""))


def make_config(T, site: str, models: dict):
    return T.Config(
        site=site, models=models, subcats=CAT_PAGES, parts={c: rule(c) for c in RULES},
        head_fn=head, trim_col=r"body\s*&\s*trim", option_col=r"emission\s*&\s*transmission",
        reman_fn=lambda r: is_reman(r.get("pn", ""), r.get("main", "")),
        trim_pick=lambda make, model, year, slugs: pick_trims(slugs, want_hybrid=bool(_HYBRID.search(model))),
    )


def bind(T, cfg):
    cats_for, parts_on_page_t, product = T.bind(cfg)

    def parts_on_page(list_url: str, cat: str) -> list[dict]:
        out = parts_on_page_t(list_url, cat)
        if cat == "window-switch" and re.search(r"/(front_)?door_lining\.html$", list_url):
            # 2003-2007 Accord prints its driver window switch as a bare
            # "Switch Assy." (35754-SDA-306; product page: "Window Switch",
            # Driver Side, replaces 35750-SDA-A12). Kept from the front door
            # lining diagram only, and flagged for curation.
            have = {p["pn"] for p in out}
            for r in T.list_parts(T.get(list_url)["html"]):
                if r["pn"] and r["url"] and r["pn"] not in have and BARE_SWITCH.match(oem_name(r["main"])):
                    have.add(r["pn"])
                    out.append({"pn": r["pn"], "name": r["main"], "product_url": T.absolute(cfg.site, r["url"]),
                                "list_group": r["group"], "list_remark": r["remark"], "list_info": r["info"],
                                "list_flags": ["bare name 'Switch Assy.' on the front door lining diagram: "
                                               "check the product page says a driver window switch"]})
        return out

    def categories_for(make: str, model: str, year: int, cats: list[str]) -> dict[str, list[str]]:
        # one "Tailgate" diagram; pickups file it as tailgate, the rest as liftgate
        drop = "liftgate" if model in PICKUPS else "tailgate"
        return cats_for(make, model, year, [c for c in cats if c != drop])
    def product_checked(product_url: str) -> dict:
        rec = product(product_url)
        try:
            main = (T.store(T.get(product_url)["html"]).get("partNumber") or {}).get("partInfo", {}).get("mainDesc") or ""
        except Exception:  # the page was just read by product(); a cache hit
            main = ""
        f = side_flag(main, rec.get("position"))
        if f:
            rec["flags"] = rec.get("flags", []) + [f]
        return rec
    return categories_for, parts_on_page, product_checked


def side_flag(name: str, position: str | None) -> str | None:
    """Honda product pages sometimes print a Position naming both sides
    ("Driver Side Passenger Side" on left mirror 76250-S84-A31ZJ) or the other
    side. The position stays as printed; the record gets a flag."""
    if not position:
        return None
    drv, pas = bool(re.search(r"\bdriver\b", position, re.I)), bool(re.search(r"\bpassenger\b", position, re.I))
    if drv and pas:
        return f"position names both sides: {position!r}"
    m = re.search(r"(?:,|^)\s*(?:[a-z ]+,\s*)?\b([RL])\.(?:\s|$|,)", name or "")
    side = m.group(1).upper() if m else None
    if side is None:  # product-page names spell it out: "Mirror Assembly, Driver Side Door"
        if re.search(r"\b(driver|left)\b", name or "", re.I) and not re.search(r"\b(passenger|right)\b", name or "", re.I):
            side = "L"
        elif re.search(r"\b(passenger|right)\b", name or "", re.I) and not re.search(r"\b(driver|left)\b", name or "", re.I):
            side = "R"
    if side == "L" and pas or side == "R" and drv:
        return f"position {position!r} contradicts name {name!r}"
    return None
