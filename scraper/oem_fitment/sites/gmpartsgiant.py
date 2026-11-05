"""www.gmpartsgiant.com: GM catalog (Chevrolet, GMC, Buick, Cadillac, Pontiac,
Saturn, Oldsmobile, Hummer) on the PartsGiant ".html" template.

GM naming on list pages: group "NOUN, Description" (e.g. "GENERATOR, Engine
Electrical"), name = NOUN, remark = the catalog note ("FRONT SIDE DOOR
WINDOW(INCLUDES 5,8)(W/MOTOR)"), info carries "Location: Driver Side" and
"Fitting Vehicle Options: <RPO codes>". The rules below anchor on the noun.
Product pages print trims + body in "Important vehicle option details".
"""
from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.gmpartsgiant.com"

# Year-catalog variants seen on the site (2026-11-05): silverado/sierra
# "1500_2wd", "1500_4wd", "2500_hd_4wd", "1500_classic_2wd" (2007),
# "1500_new_style_4wd" (2007), "1500_hybrid_2wd"; suburban "1500_4wd" and
# pre-2000 "c1500"/"k1500"; yukon "2wd", "xl_1500_4wd", "denali_awd";
# malibu/cruze/impala "new_model", "carryover_model", "limited_carryover_model".
P1500 = r"^1500(_new_style|_new_model)?_(2wd|4wd)$"
MODELS = {
    ("Chevrolet", "Silverado 1500"): M("silverado", inc=P1500),
    ("Chevrolet", "Silverado"): M("silverado", inc=P1500),
    ("Chevrolet", "Silverado 1500 Classic"): M("silverado", inc=r"^1500_classic_(2wd|4wd)$"),
    ("Chevrolet", "Silverado 2500"): M("silverado", inc=r"^2500(_hd)?(_new_style)?_(2wd|4wd)$", pref=r"^2500_(2wd|4wd)$"),
    ("Chevrolet", "Silverado 2500HD"): M("silverado", inc=r"^2500_hd(_new_style)?_(2wd|4wd)$"),
    ("Chevrolet", "Silverado 3500"): M("silverado", inc=r"^3500(_hd)?(_new_style)?_(2wd|4wd)$"),
    ("Chevrolet", "Suburban"): M("suburban", inc=r"^1500_(2wd|4wd)$|^[ckrv]1500$|^[ckrv]10$"),
    ("Chevrolet", "Suburban 1500"): M("suburban", inc=r"^1500_(2wd|4wd)$|^[ckrv]1500$|^[ckrv]10$"),
    ("Chevrolet", "Suburban 2500"): M("suburban", inc=r"^2500_(2wd|4wd)$|^[ckrv]2500$|^[ckrv]20$"),
    ("Chevrolet", "C1500 Suburban"): M("suburban", inc=r"^[cr]1500$|^[cr]10$"),
    ("Chevrolet", "Express"): M("express", inc=r"^(1500|2500)(_2wd|_awd|_4wd)?$", pref=r"^1500"),
    ("Chevrolet", "Express 1500"): M("express", inc=r"^1500(_2wd|_awd|_4wd)?$"),
    ("Chevrolet", "Express 2500"): M("express", inc=r"^2500(_2wd|_4wd)?$"),
    ("Chevrolet", "Express 3500"): M("express", inc=r"^3500$"),
    ("Chevrolet", "S-10"): M("s10", inc=r"^(2wd|4wd|pickup_2wd|pickup_4wd)?$"),
    ("Chevrolet", "S10/S15/Sonoma"): M("s10", inc=r"^(2wd|4wd|pickup_2wd|pickup_4wd)?$"),
    ("Chevrolet", "S-10 Blazer"): [M("s10", inc=r"^blazer_(2wd|4wd)$", years=(1983, 1994)),
                                   M("blazer", inc=r"^(2wd|4wd)$", years=(1995, 2005))],
    ("Chevrolet", "Blazer S10"): [M("s10", inc=r"^blazer_(2wd|4wd)$", years=(1983, 1994)),
                                  M("blazer", inc=r"^(2wd|4wd)$", years=(1995, 2005))],
    ("Chevrolet", "Blazer S10/Jimmy S15"): [M("s10", inc=r"^blazer_(2wd|4wd)$", years=(1983, 1994)),
                                            M("blazer", inc=r"^(2wd|4wd)$", years=(1995, 2005))],
    ("Chevrolet", "Avalanche"): M("avalanche", inc=r"^(1500_)?(2wd|4wd)$"),
    ("Chevrolet", "Avalanche 1500"): M("avalanche", inc=r"^(1500_)?(2wd|4wd)$"),
    ("Chevrolet", "Trailblazer"): M("trailblazer", inc=r"^(2wd|4wd|awd|2wd_exc_ss|4wd_exc_ss)?$"),
    ("Chevrolet", "Trailblazer EXT"): M("trailblazer", inc=r"^ext_(2wd|4wd)$"),
    ("Chevrolet", "Cruze"): M("cruze", exc=r"carryover"),
    ("Chevrolet", "Cruze Limited"): M("cruze", inc=r"^carryover_model$"),
    ("Chevrolet", "Impala"): M("impala", exc=r"limited"),
    ("Chevrolet", "Impala Limited"): M("impala", inc=r"^limited_carryover_model$"),
    ("Chevrolet", "Malibu"): M("malibu", exc=r"limited|classic"),
    ("Chevrolet", "Malibu Limited"): M("malibu", inc=r"^limited_carryover_model$"),
    ("Chevrolet", "Malibu Maxx"): M("malibu", inc=r"^(new_model)?$"),
    ("Chevrolet", "Classic"): M("malibu", inc=r"^classic_carryover_model$|^$"),
    ("Chevrolet", "C/K 1500"): M(["c1500", "k1500"]),
    ("Chevrolet", "Gmt-400"): M(["c1500", "k1500"]),
    ("Chevrolet", "C/K 2500"): M(["c2500", "k2500"]),
    ("Chevrolet", "C/K 3500"): M(["c3500", "k3500"]),
    ("Chevrolet", "Aveo5"): M("aveo", inc=r"^(hatchback)?$", pref=r"hatchback"),
    ("Chevrolet", "G-Series"): M(["g10", "g20"]),
    ("Chevrolet", "Caprice Classic"): M("caprice"),
    ("GMC", "Sierra"): M("sierra", inc=P1500),
    ("GMC", "Sierra 1500"): M("sierra", inc=P1500),
    ("GMC", "Sierra 2500"): M("sierra", inc=r"^2500(_hd)?(_new_style)?_(2wd|4wd)$", pref=r"^2500_(2wd|4wd)$"),
    ("GMC", "Sierra 2500HD"): M("sierra", inc=r"^2500_hd(_new_style)?_(2wd|4wd)$"),
    ("GMC", "Sierra 3500"): M("sierra", inc=r"^3500(_hd)?(_new_style)?_(2wd|4wd)$"),
    ("GMC", "Yukon"): M("yukon", inc=r"^(2wd|4wd)?$"),
    ("GMC", "Yukon Denali"): M("yukon", inc=r"^denali_(2wd|4wd|awd)$"),
    ("GMC", "Yukon XL"): M("yukon", inc=r"^xl(_1500)?_(2wd|4wd)$"),
    ("GMC", "Yukon XL 1500"): M("yukon", inc=r"^xl(_1500)?_(2wd|4wd)$"),
    ("GMC", "Envoy"): M("envoy", inc=r"^(2wd|4wd|2wd_exc_denali|4wd_exc_denali)$"),
    ("GMC", "Envoy Xl"): M("envoy", inc=r"^xl_(2wd|4wd)$"),
    ("GMC", "Savana"): M("savana", inc=r"^(1500|2500)(_2wd|_awd)?$", pref=r"^1500"),
    ("GMC", "Savana 1500"): M("savana", inc=r"^1500(_2wd|_awd)?$"),
    ("GMC", "Savana 2500"): M("savana", inc=r"^2500(_2wd|_awd)?$"),
    ("GMC", "Suburban 1500"): M("suburban", pref=r"1500"),
    ("Cadillac", "Escalade"): M("escalade", inc=r"^(2wd|4wd|awd)?$"),
    ("Cadillac", "Escalade ESV"): M("escalade", inc=r"^esv_(2wd|4wd|awd)$"),
    ("Cadillac", "Escalade EXT"): M("escalade", inc=r"^ext_(2wd|awd)$"),
    ("Pontiac", "Montana"): M("montana", inc=r"^(base)?$"),
    ("Pontiac", "Montana SV6"): M("montana", inc=r"^sv6_(2wd|awd)$"),
    ("Saturn", "S-Series"): M(["sl1", "sl2"]),
    ("Saturn", "L-Series"): M(["l200", "l300"]),
    ("Oldsmobile", "Cutlass"): M("cutlass", inc=r"^(base_model)?$"),
    ("Oldsmobile", "Cutlass Ciera"): M("cutlass", inc=r"^ciera$"),
    ("Oldsmobile", "Cutlass Supreme"): M("cutlass", inc=r"^supreme"),
    ("Oldsmobile", "Eighty-Eight"): M("88"),
    ("Oldsmobile", "Ninety-Eight"): M("98"),
}

# Parts-list subcategory slugs that hold each category.
SUBCATS = {
    "alternator": r"generator|alternator",
    "starter": r"starter",
    "ac-compressor": r"compressor",
    "headlights": r"lamps?_front|headlamp|front_lamp",
    "tail-lights": r"lamps?_rear|tail_?lamp|rear_lamp",
    "side-mirrors": r"mirror",
    "window-regulator": r"door_hardware|window|regulator",
    "window-switch": r"trim_front_door|door_trim_side_front|door_hardware_front|door_hardware_side_front|front_door|window_switch|switch",
    "climate-control": r"instrument_panel_electrical|instrument_panel_related_parts_electrical|heater.*control|a_c.*control|control.*(heater|a_c)|hvac",
    "fuel-pump-module": r"fuel_tank|fuel_supply|fuel_pump|fuel_sender",
    "throttle-body": r"throttle|fuel_injection|air_intake",
    "power-steering-pump": r"steering_pump|power_steering|steering_gear_pump",
    # ^instrument_panel$: 2012 Equinox cluster page; (^|_)gage, not "gage" (it matched lugGAGE_carrier)
    "gauge-cluster": r"instrument_panel_electrical|instrument_panel_related_parts_electrical|instrument_cluster|cluster|(^|_)gage|gauge|^instrument_panel$",
    "ignition-coils": r"ignition|coil|spark|cylinder_head_related",  # 2012 Equinox coils: engine_assembly_cylinder_head_related_parts
    "radiator": r"radiator",
    "door-front": r"door_hardware_front|door_hardware_side_front|body_side_frame_doors|front_door|door_front|doors",  # 2000 Silverado: door_hardware_side_front
    "door-rear": r"door_hardware_rear|door_hardware_side_rear|body_side_frame_doors|rear_door|door_rear|doors",
    "hood": r"^hood",
    "fender": r"fender",
    "bumper-front": r"bumper_front|front_bumper|fascia_front|front_fascia",
    "bumper-rear": r"bumper_rear|rear_bumper|fascia_rear|rear_fascia",
    "grille": r"grille",
    "trunk-lid": r"rear_compartment|deck_lid|trunk",
    "tailgate": r"tailgate|end_gate|pickup_box|box_",
    "liftgate": r"lift_?gate|end_gate|rear_door_hardware|body_rear_end",
}
SUBCAT_EXCL = {
    "window-regulator": r"trim|weatherstrip|glass_only|moldings",
    "window-switch": r"steering|ignition|instrument_panel_lamp",
    "door-front": r"trim|weatherstrip",
    "door-rear": r"trim|weatherstrip",
}

# (include, exclude_head, exclude_full); see _partsgiant.Config.parts.
# GM marks sub-components "(PART OF n)" (a bulb, glass or motor inside the
# assembly); assemblies are never "PART OF". exclude_full uses that.
N = r"^(?:{})\b"  # anchor on the GM noun that starts the group
SUB = r"\(PART OF\b"
PARTS = {
    "alternator": (N.format("GENERATOR|ALTERNATOR"), r"PULLEY|BEARING|REGULATOR|BRUSH|RECTIFIER|FAN|COVER", SUB),
    "starter": (N.format("STARTER|MOTOR,\\s*STARTER|MOTOR ASM,\\s*STARTER"), r"SOLENOID|DRIVE|SHIELD|BRUSH|ARMATURE|PINION|HOUSING", SUB),
    "ac-compressor": (N.format("COMPRESSOR(?: KIT| ASM)?") + r"[^|]*\|.*\bA/?C\b", r"CLUTCH|PULLEY|VALVE|SWITCH|COIL|AIR COMPRESSOR|LEVEL", SUB),
    "headlights": (r"^HEADLAMP\b|^(LAMP|LAMP ASM|LAMP KIT|HEADLAMP ASM)[^|]*\|[^|]*\|\s*(LAMP,\s*)?HEADLAMP",
                   r"FOG|BULB|CAPSULE|HOUSING|LENS|ACTUATOR|LEVEL|BALLAST|MODULE|IGNITOR|ADJUSTER|CONTROL|DOOR|BEZEL|COVER|SWITCH|SENSOR", SUB),
    "tail-lights": (r"^LAMP\b[^|]*\|[^|]*\|\s*(LAMP( ASM)?,\s*)?TAIL\b|^LAMP\b.*\bTAIL LAMP\b",
                    r"HIGH MOUNT|HI-MOUNT|LICENSE|MARKER|BACK ?UP|SOCKET|BULB|LENS|CONTROL|MODULE|PLATE|COMPARTMENT", SUB),
    "side-mirrors": (r"^MIRROR\b[^|]*\|[^|]*\|\s*(MIRROR( ASM)?,\s*)?OUTSIDE",
                     r"GLASS|REFLECTOR|\|\s*(MIRROR( ASM)?,\s*)?INSIDE|COVER|CAP|HOUSING|MOTOR|ACTUATOR|SWITCH|LAMP|HEATER|INNER|TRIM", SUB + r"|REFLECTOR GLASS"),
    "window-regulator": (r"^(REGULATOR|MOTOR|MOTOR KIT|REGULATOR KIT|REGULATOR ASM|MOTOR ASM)\b[^|]*\|[^|]*\|[^|]*\bWINDOW\b",
                         r"VENT|BACK WINDOW|REAR WINDOW|SUNROOF|WIPER|SLIDING|DEFOG|SWITCH|HANDLE|CRANK"),
    "window-switch": (r"^SWITCH\b[^|]*\|[^|]*\|[^|]*\bWINDOW\b",
                      r"\|\s*(SWITCH,\s*)?REAR SIDE DOOR|SUNROOF|DEFOG|VENT|WIPER|MIRROR",
                      r"Location: Passenger"),
    "climate-control": (r"^(CONTROL|CONTROL ASM|CONTROL KIT)\b[^|]*\|[^|]*\|[^|]*\b(HEATER|A/C|HVAC|CLIMATE|AIR CONDITIONING)\b",
                        r"ACTUATOR|CABLE|VALVE|KNOB|BEZEL|SENSOR|PROGRAMMER|VACUUM|SEAT", SUB),
    "fuel-pump-module": (r"^(MODULE|MODULE KIT|MODULE ASM|PUMP|PUMP KIT|PUMP ASM|SENDER|SENDER ASM)\b[^|]*\|.*\bFUEL\b",
                         r"SENSOR|CONTROL|RELAY|STRAINER|INJECTION|FLOW|DRIVER|VAPOR|EVAP|PURGE|LEAK|PRIMER|SHIELD|VACUUM|DIESEL|FILTER", SUB),
    "throttle-body": (r"^(BODY|BODY ASM|THROTTLE BODY|THROTTLE BODY ASM)\b[^|]*\|.*\bTHROTTLE\b",
                      r"SENSOR|CABLE|HEATER|SPACER|INLET|LEVER|COVER", SUB),
    "power-steering-pump": (r"^(PUMP|PUMP ASM|PUMP KIT)\b[^|]*\|.*(P/S|POWER STEERING|STEERING PUMP|STRG)",
                            r"PULLEY|RESERVOIR|CAP|VACUUM|COOLANT|WATER|FUEL|BRAKE|SEAL", SUB),
    "gauge-cluster": (N.format("CLUSTER|CLUSTER ASM|CLUSTER KIT"), r"LENS|BEZEL|TRIM|BULB|MASK|PLATE|HOOD", SUB),
    "ignition-coils": (N.format("COIL|COIL ASM|COIL KIT|MODULE KIT,\\s*IGNITION COIL") + r".*IGNITION", r"BOOT|SPRING|SHIELD|CONDENSER|PICKUP", SUB),
    "radiator": (N.format("RADIATOR|RADIATOR ASM|RADIATOR KIT"),
                 r"CAP|SUPPORT|BAFFLE|DRAIN|AIR|SHROUD|TANK|GRILLE|DEFLECTOR|SIGHT|BRACE|CUSHION|INSULATOR", SUB),
    "door-front": (r"^DOOR\b[^|]*\|[^|]*\|\s*(DOOR( ASM)?,\s*)?FRONT", r"FUEL|FILLER|GLOVE|COMPARTMENT|ACCESS|STORAGE|ASHTRAY", SUB),
    "door-rear": (r"^DOOR\b[^|]*\|[^|]*\|\s*(DOOR( ASM)?,\s*)?REAR (SIDE|ACCESS)", r"FUEL|FILLER|GLOVE|COMPARTMENT|STORAGE|ASHTRAY|CARGO|PICKUP BOX", SUB),
    "hood": (N.format("HOOD|HOOD ASM|PANEL,\\s*HOOD"),
             r"HINGE|LATCH|CABLE|STRUT|ROD|LOCK|RELEASE|ORNAMENT|SCOOP|PROP|LIFT|HANDLE|LIGHT|LAMP|WASHER|VENT|LOUVER|BLANKET", SUB),
    "fender": (N.format("FENDER|FENDER ASM|PANEL,\\s*FENDER"),
               r"LINER|FLARE|EXTENSION|FILLER|SPLASH|WHEELHOUSE|SKIRT|VENT|RAIL|APRON", SUB),
    "bumper-front": (r"^(FASCIA|BUMPER|COVER|FASCIA ASM|BUMPER ASM)\b[^|]*\|.*\bFRONT\b",
                     r"ABSORBER|BAR\b|REINFORCEMENT|IMPACT|GUIDE|ENERGY|STEP|EXTENSION|INSERT|END\b|SENSOR|CLOSEOUT|HOOK|TOW|LICENSE|AIR DAM|VALANCE|FILLER|GUARD|SIGHT", SUB),
    "bumper-rear": (r"^(FASCIA|BUMPER|COVER|FASCIA ASM|BUMPER ASM)\b[^|]*\|.*\bREAR\b",
                    r"ABSORBER|BAR\b|REINFORCEMENT|IMPACT|GUIDE|ENERGY|STEP PAD|EXTENSION|INSERT|END\b|SENSOR|CLOSEOUT|HOOK|TOW|LICENSE|AIR DAM|VALANCE|FILLER|GUARD|SIGHT|HITCH", SUB),
    "grille": (N.format("GRILLE|GRILLE ASM"),
               r"BAFFLE|SPEAKER|DEFROSTER|COWL|VENT|RADIO|OUTLET|INSERT|SCREEN|AIR INLET", SUB),
    "trunk-lid": (r"^LID\b[^|]*\|.*REAR COMPARTMENT", r"LAMP|HINGE|LOCK|SPOILER|RELEASE|PANEL|LINER|TORSION|STRUT|LATCH|TRIM", SUB),
    "tailgate": (r"^(GATE|TAILGATE|GATE ASM)\b[^|]*\|.*\b(END GATE|ENDGATE|TAIL ?GATE|PICKUP BOX)\b",
                 r"HANDLE|LATCH|CABLE|LOCK|HINGE|STRUT|LIFT ASSIST|PROTECTOR|LINER|STOP|SUPPORT|TRUNNION|ROD|CAP|TRIM|LAMP", SUB),
    "liftgate": (r"^(GATE|LIFTGATE|GATE ASM)\b[^|]*\|.*\bLIFT ?GATE\b|^(GATE|GATE ASM)\b[^|]*\|[^|]*\|\s*(GATE,\s*)?LIFT",
                 r"STRUT|HINGE|LATCH|LOCK|MOTOR|WINDOW|GLASS|SWITCH|HANDLE|ACTUATOR|LAMP|WIPER|APPLIQUE|SPOILER|CYLINDER|RELEASE|TRIM|PANEL", SUB),
}

def head(r: dict) -> str:
    """GM's group text after the noun is the illustration group
    ("HEADLAMP, Capsule/Headlamp/Fog Lamp"), not the part, so exclude_head
    sees only "<NOUN> | <remark up to its first '('>"."""
    return f"{r['group'].split(',')[0].strip()} | {r['remark'].split('(')[0]}"


CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=True, head_fn=head)
categories_for, parts_on_page, product = T.bind(CFG)
