"""www.moparpartsgiant.com: Dodge, Ram, Chrysler (and Jeep) on the PartsGiant
".html" template. Plymouth is not in this catalog (/plymouth-parts.html is a
404, 2026-11-05), so Plymouth feed models fail navigation by design.

Mopar list rows: group = "NOUN Description" ("GENERATOR Engine", "LAMP
Headlamp Park And Turn", "MIRROR Outside, Rearview, Electric, Heated"); the
side is a bare "Left"/"Right" at the start of the info text; product pages
carry the side in "lr" ("Passenger Side") and print trims in the option
column. Remanufactured ("R" prefix, "Remanufactured", "New Part For Core
Return") rows are dropped when a new number is on the same page.
"""
from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.moparpartsgiant.com"

# 1981-1993 Ram pickups are the site's d150/w150 (d250/w250) pages;
# dodge-ram_1500 covers 1994-2010 (1998-2001 also "quad_club_cab"/"regular_cab");
# ram-1500 covers 2011+ (2019-2020 "new_style"/"classic").
RAM1500 = [M(["d150", "w150"], years=(1981, 1993)), M("ram_1500", years=(1994, 2010)), M("1500", make="ram", inc=r"^(new_style)?$", years=(2011, 2030))]
RAM2500 = [M(["d250", "w250"], years=(1981, 1993)), M("ram_2500", years=(1994, 2010)), M("2500", make="ram", years=(2011, 2030))]
MODELS = {
    ("Dodge", "Ram 1500"): RAM1500,
    ("Dodge", "Ram"): RAM1500,
    ("Dodge", "Ram Pickup"): RAM1500,
    ("Dodge", "1500 Pickup"): RAM1500,
    ("Dodge", "Ram 2500"): RAM2500,
    ("Ram", "1500"): M("1500", inc=r"^(new_style)?$"),
    ("Dodge", "D1500"): M("d150"),
    ("Dodge", "Ram Van 1500"): M("ram_van"),
    ("Dodge", "Caravan/Grand Caravan"): M("grand_caravan"),
    ("Chrysler", "300C"): M("300"),
    ("Chrysler", "Town & Country"): M("town_country"),
}

SUBCATS = {
    "alternator": r"generator|alternator",
    "starter": r"starter",
    "ac-compressor": r"a_c_compressor$|compressor",
    "headlights": r"lamps_front|headlamp",
    "tail-lights": r"lamps_rear|tail_?lamp",
    "side-mirrors": r"mirror_exterior|mirrors?_outside|exterior_mirror",
    "window-regulator": r"regulator|window",
    "window-switch": r"switches_doors|switches_door|^switches$|switches_body",
    "climate-control": r"a_c_heater_controls|heater_controls|switches_heating_a_c|climate_control",
    "fuel-pump-module": r"fuel_pump|fuel_tank|fuel_module",
    "throttle-body": r"throttle",
    "power-steering-pump": r"power_steering_pump|steering_pump",
    "gauge-cluster": r"cluster",
    "ignition-coils": r"ignition|spark_plugs\w*_coils?$",  # 2002 Ram, 2006 300: spark_plugs_cables_coils
    "radiator": r"radiator",
    "door-front": r"front_door_shell|door_front_shell|front_door$|door_shell",  # door_front_shell_hinges (2002 Ram, 2006 300)
    "door-rear": r"rear_door_shell|door_rear_shell|sliding_door_shell|rear_door$|door_shell",
    "hood": r"^hood",
    "fender": r"fender$|front_fender",
    "bumper-front": r"fascia_front|bumper_front|front_bumper",
    "bumper-rear": r"fascia_rear|bumper_rear|rear_bumper",
    "grille": r"grille",
    "trunk-lid": r"deck_?lid|trunk",
    "tailgate": r"tailgate",
    "liftgate": r"^liftgate$|liftgate_shell|liftgate_related|^decklid_liftgate",  # 300/Magnum decklid_liftgate_panel
}
SUBCAT_EXCL = {
    "window-regulator": r"sliding_door_regulator|weatherstrip|trim|wiring|switch|defrost|wiper",
    "side-mirrors": r"lamps_outside_mirror",
    # no fender page exclude: the 2015 200 fender is on front_fenders_shields;
    # the part rule and COMMON_EXCLUDE drop the shield rows
    "liftgate": r"weatherstrip|wiring|trim|panels",
    "trunk-lid": r"weatherstrip|wiring|trim",
}

N = r"^(?:{})\b"
PARTS = {
    "alternator": (N.format("GENERATOR|ALTERNATOR"), r"PULLEY|BRACKET|BELT|DECOUPLER|REGULATOR"),
    "starter": (N.format("STARTER"), r"SOLENOID|SHIELD|DRIVE"),
    "ac-compressor": (N.format("COMPRESSOR") + r"[^|]*(A/C|Air Conditioning)", r"CLUTCH|PULLEY|COIL|VALVE|SWITCH"),
    # full-text exclude: bulb kits filed under the lamp's own group (LBK13001 "LAMP Headlamp
    # Park And Turn", info "Light Bulb Kit (Assorted Bulbs and Fuses)")
    "headlights": (N.format("LAMP|HEADLAMP") + r"[^|]*\bHead", r"Fog|Bulb|Level|Housing|Bezel|Boot|Ballast|Module|Shield|Socket|Lens|Washer|Adjuster|Switch", r"Bulb Kit|Assorted Bulbs"),
    "tail-lights": (N.format("LAMP") + r"[^|]*\bTail", r"Bulb|Socket|License|Center High|CHMSL|Mounted Stop|Back ?Up|Lens|Gasket", r"Bulb Kit|Assorted Bulbs"),
    "side-mirrors": (N.format("MIRROR") + r"[^|]*\bOutside", r"Glass|Cap|Cover|Bezel|Motor|Lamp|Gasket|Switch|Flag|Applique"),
    "window-regulator": (N.format("REGULATOR|MOTOR") + r"[^|]*\bWindow", r"Vent|Quarter|Back|Sliding Door(?! Window)|Wiper|Liftgate|Switch"),
    "window-switch": (N.format("SWITCH") + r"[^|]*\bWindow", r"Rear|Vent|Quarter|Lock|Liftgate|Wiper|Defrost", r"^[^|]*\|[^|]*\|[^|]*\|\s*Right\b|Passenger"),
    "climate-control": (N.format("CONTROL|SWITCH|MODULE") + r"[^|]*(A/C and Heater|A/C And Heater|Heater and A/C|Heater And A/C|Air Conditioning|Climate|HVAC|Heater Control|A/C Heater)",
                        r"Actuator|Sensor|Blower|Resistor|Cable|Knob|Bezel|Seat|Rear Defrost|Door|Vacuum"),
    "fuel-pump-module": (N.format("MODULE|PUMP|PACKAGE") + r"[^|]*\bFuel", r"Pressure|Sensor|Control|Injection|Leak|Vapor|Relay|Filter|Strainer|Diesel|Lift|Transfer|Water"),
    "throttle-body": (N.format("THROTTLE BODY|BODY") + r"[^|]*Throttle|^THROTTLE BODY", r"Sensor|Gasket|Spacer|Cable|Bracket|Adapter"),
    "power-steering-pump": (N.format("PUMP") + r"[^|]*Power Steering", r"Pulley|Reservoir|Hose|Cap|Bracket|Seal|Cooler"),
    "gauge-cluster": (N.format("CLUSTER"), r"Lens|Bezel|Mask|Bulb|Trim"),
    "ignition-coils": (N.format("COIL|IGNITION COIL") + r"[^|]*Ignition|^IGNITION COIL|^COIL Ignition", r"Boot|Bracket|Cable|Wire|Shield"),
    "radiator": (N.format("RADIATOR"), r"Cap|Support|Seal|Shield|Drain|Bracket|Isolator|Hose|Baffle|Bushing|Insulator|Grommet|Closure"),
    "door-front": (N.format("DOOR") + r"[^|]*\bFront", r"Fuel|Filler|Glove|Bin|Storage|Handle|Trim|Ajar|Lock|Hinge|Check|Speaker"),
    "door-rear": (N.format("DOOR") + r"[^|]*\b(Rear|Sliding)", r"Fuel|Filler|Glove|Bin|Storage|Handle|Trim|Ajar|Lock|Hinge|Check|Speaker|Track"),
    # Kit: accessory "HOOD KIT Vehicle" 82211065AD (mopar_accessories_component_parts/hood)
    "hood": (N.format("HOOD"), r"Kit|Hinge|Latch|Seal|Silencer|Insulator|Prop|Release|Scoop|Lock|Striker|Cable|Strut|Rod|Bumper|Ornament|Vent|Louver|Deflector"),
    "fender": (N.format("FENDER"), r"Liner|Flare|Shield|Extension|Molding|Brace|Support|Seal|Filler|Vent"),
    "bumper-front": (N.format("FASCIA|BUMPER") + r"[^|]*\bFront", r"Reinforcement|Absorber|Support|Guide|Retainer|Extension|Bezel|Closeout|Applique|Bracket|Isolator|Step|Pad|Shield|Insert|Tow|Valance|Air Dam|Splitter|Lower"),
    "bumper-rear": (N.format("FASCIA|BUMPER") + r"[^|]*\bRear", r"Reinforcement|Absorber|Support|Guide|Retainer|Extension|Bezel|Closeout|Applique|Bracket|Isolator|Step|Pad|Shield|Insert|Tow|Valance|Hitch|Lower"),
    "grille": (N.format("GRILLE"), r"Kit|Fog|Bezel|Speaker|Molding|Emblem|Bracket|Reinforcement|Insert|Screen|Defroster|Cowl|Liftgate"),
    # Opening: "PANEL Deck Lid Opening" 5065744AD is rear body sheet metal, not the lid
    "trunk-lid": (N.format("DECKLID|DECK LID|LID") + r"|^PANEL[^|]*Deck ?Lid", r"Opening|Hinge|Latch|Seal|Lock|Strut|Torsion|Spoiler|Release|Trim|Switch|Cylinder|Light|Lamp|Molding|Applique|Emblem"),
    "tailgate": (N.format("TAILGATE"), r"Hinge|Latch|Handle|Cable|Lock|Strut|Damper|Seal|Cap|Protector|Rod|Cylinder|Switch|Release|Trim|Applique|Spoiler|Bezel|Camera|Molding"),
    "liftgate": (N.format("LIFTGATE"), r"Hinge|Latch|Handle|Lock|Strut|Prop|Seal|Motor|Switch|Glass|Wiper|Spoiler|Release|Trim|Cylinder|Light|Lamp|Applique|Molding|Actuator|Module|Bumper|Striker|Bezel|Camera|Weatherstrip"),
}

CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=True)
categories_for, parts_on_page, product = T.bind(CFG)
