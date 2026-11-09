"""www.nissanpartsdeal.com: Nissan on the PartsGiant ".html" template. The
Infiniti module (infinitipartsdeal.py) reuses SUBCATS and PARTS from here:
both catalogs print Nissan's own part names.

Nissan list rows: group = name = "<Part> Assy-<Where>, <LH|RH>" ("Headlamp
Assy-LH", "Regulator Assy-Rear Door Window, LH", "Switch Assy-Power Window,
Main"); info holds "Location: Driver side", "Production Date", "Fitting Vehicle
Options: 4S. QR25DE". Service numbers that start with a letter (H4300-...,
F3100-...) are Nissan's own service part numbers and are kept. "Value
Advantage Replacement Part" rows (B-prefixed, Nissan's non-genuine line) are
excluded. Product pages print "Trim & Engine" ("Base, S|4 Cyl 2.5L") and
engine codes in the option column.

Year catalogs split by body or market code: altima 2007-2018 "sedan"/"coupe"
(+ "hybrid"), versa 2007-2019 "sedan"/"hatchback", rogue 2014-2019
"t32u"/"t32d"/"t32j"/"select", sentra 1995-1999 "b14u"/"b14x", titan 2020+
"regular"/"xd".
"""
from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.nissanpartsdeal.com"

MODELS = {
    ("Nissan", "Altima"): M("altima", pref=r"^sedan$"),
    ("Nissan", "Versa"): M("versa", pref=r"^sedan$"),
    ("Nissan", "Rogue"): M("rogue", inc=r"^(t32u)?$"),
    ("Nissan", "Rogue Select"): M("rogue", inc=r"^select$|^$"),
    ("Nissan", "Sentra"): M("sentra", inc=r"^(b14u)?$"),
    ("Nissan", "Titan"): M("titan", inc=r"^(regular)?$"),
    ("Nissan", "Pickup"): M("hardbody_pickup_d21"),
}

SUBCATS = {
    "alternator": r"^alternator$",
    "starter": r"starter",
    "ac-compressor": r"^compressor$",
    "headlights": r"^headlamp",
    "tail-lights": r"rear_combination_lamp|tail_?lamp",
    "side-mirrors": r"rear_view_mirror|door_mirror|outside_mirror",
    "window-regulator": r"door_window_regulator|window_regulator|back_door_window",
    "window-switch": r"^switch$",
    "climate-control": r"^control_unit$|heater_control|air_conditioner_control|^controller",
    "fuel-pump-module": r"fuel_tank|fuel_pump",
    "throttle-body": r"throttle_chamber|throttle",
    "power-steering-pump": r"power_steering_pump",
    "gauge-cluster": r"instrument_meter|meter_gauge",
    "ignition-coils": r"ignition_system",
    "radiator": r"radiator",
    "door-front": r"front_door_panel",
    "door-rear": r"rear_door_panel|slide_door_panel",
    "hood": r"hood_panel",
    "fender": r"front_fender",
    "bumper-front": r"front_bumper",
    "bumper-rear": r"rear_bumper",
    "grille": r"grille|front_bumper",
    "trunk-lid": r"trunk_lid",
    "tailgate": r"rear_body|tail_?gate|rear_gate",
    "liftgate": r"back_door_panel|back_door$",
    # tier C (2026-11-09; 2012 Altima sedan: body_electrical/windshield_wiper,
    # axle_suspension/front_axle, front_suspension, rear_suspension)
    "wiper-motor": r"wiper",
    "knuckle": r"^(front|rear)_axle$",
    "strut": r"^(front|rear)_suspension$|shock_absorber",
}
SUBCAT_EXCL = {"radiator": r"hose", "wiper-motor": r"washer|headlamp"}

VA = r"Value Advantage"
PARTS = {
    # tier C. "Drive Assy-Windshield Wiper" is motor + linkage: its product
    # page says "Motor & Drive" (28800-ZX01A). "Strut Kit-Front Suspension,
    # LH" and "Shock Absorber Kit-Rear" are the dampers (E-prefixed service
    # numbers, kept). Rear axle housings are not knuckles and are not taken.
    "wiper-motor": (r"^(Motor|Drive)(?: Assy)?-[^|]*Wiper", r"Headlamp|Washer|Arm|Blade|Link|Pivot|Cover|Bracket|Refill", VA),
    "knuckle": (r"^Knuckle Spindle|^Spindle-Knuckle|^Knuckle(?: Assy)?-(?!Arm)", r"Nut|Bolt|Arm|Bush|Cover|Seal|Plate|Shield|Bearing", VA),
    "strut": (r"^Strut(?: Assy| Kit)?-|^Shock Absorber(?: Assy| Kit)?-|^Absorber (?:Assy|Kit)-Shock",
              r"Mount|Bearing|Insulator|Bush|Bracket|Cap|Seat|Bound|Bumper|Boot|Cover|Tube|Spring|Distance|Stopper|Nut|Bolt|Washer", VA),
    "alternator": (r"^(Generator|Alternator)\b", r"Pulley|Bracket|Fan|Regulator|Brush|Bearing|Cover", VA),
    "starter": (r"^Motor Assy-Starter|^Starter Motor|^Starter\b", r"Switch|Solenoid|Pinion|Gear", VA),
    "ac-compressor": (r"^Compressor(?: Assy)?-(Cooler|Air Con|A/C)|^Compressor Assy-Cooler", r"Clutch|Pulley|Coil|Valve|Switch", VA),
    "headlights": (r"^Headlamp(?: Assy)?\b|^Head Lamp Assy", r"Socket|Bulb|Housing|Lens|Bezel|Level|Actuator|Cover|Bracket|Ballast|Ignitor|Washer|Finisher|Garnish|Unit-Control", VA),
    "tail-lights": (r"^(Combination Lamp Assy-Rear|Lamp Assy-Rear Combination|Lamp Assy-Tail|Tail Lamp Assy|Lamp Assy-Rear\b)",
                    r"Socket|Bulb|Lens|Gasket|Packing|Finisher|Bracket|License|Licence|High Mount", VA),
    "side-mirrors": (r"^(Door Mirror Assy|Mirror Assy-Outside|Mirror Assy-Door|Mirror-Door)", r"Glass|Lens|Cover|Cap|Motor|Inside|Garnish|Finisher|Gasket", VA),
    "window-regulator": (r"^(Regulator Assy-[^|]*Window|Regulator-[^|]*Window|Motor Assy-Regulator|Regulator Assy-Door)",
                         r"Glass|Vent|Back Window|Sunroof|Handle", VA),
    "window-switch": (r"^Switch Assy-Power Window[^|]*Main|^Switch Assy-Power Window\b(?![^|]*(Assist|Rear|Sub))", r"Assist|Rear|Sub|Finisher", VA),
    "climate-control": (r"^(Controller Assy-Air Con|Control Assy-Air Con|Control Assy-Heater|Control Assy-A/C|Controller Assy-A/C|Control Unit-Air Con|Controller Assy-Heater|Panel Assy-Air Conditioner Control)",
                        r"Cable|Knob|Lens|Finisher|Rear|Bezel|Amplifier|Sensor", VA),
    "fuel-pump-module": (r"^(Fuel Pump Assy|Pump Assy-Fuel|In Tank Fuel Pump|Fuel Pump\b|Pump Complete-Fuel|Fuel Pump & Gauge|Pump & Gauge Assy-Fuel)",
                         r"Bracket|Strainer|Filter|Control|Module-Fuel Pump Control|Relay|Gasket|Packing|Seal|Hose|Injection", VA),
    "throttle-body": (r"^(Chamber Assy-Throttle|Throttle Body|Body Assy-Throttle|Throttle Chamber)", r"Gasket|Sensor|Spacer|Cable|Bracket", VA),
    "power-steering-pump": (r"^Pump Assy-Power Steering|^Power Steering Pump|^Pump Assy-Power Steering, Electric", r"Pulley|Reservoir|Tank|Bracket|Connector|Hose|Seal|Gasket", VA),
    # Meter Assy-Analog: 2003-07 Infiniti G35 cluster (24820-AC700; product page pdName
    # "Instrument Cluster"). Not Meter Assy-Temperature (the separate compass gauge).
    "gauge-cluster": (r"^(Combination Meter Assy|Meter Assy-Combination|Speedometer Assy|Instrument Assy-Combination|Meter Assy-Instrument|Meter Assy-Analog)",
                      r"Lens|Finisher|Housing|Cover|Bulb|Socket|Printed|Window", VA),
    "ignition-coils": (r"^(Coil Assy-Ignition|Ignition Coil Assy|Coil-Ignition)", r"Boot|Bracket", VA),
    "radiator": (r"^Radiator Assy|^Radiator\b(?!-)", r"Cap|Support|Mount|Hose|Shroud|Drain|Seal|Baffle|Tank|Bracket|Insulator", VA),
    "door-front": (r"^Door(?: Assy)?-Front\b", r"Panel|Sash|Moulding|Tape|Finisher|Trim|Lock|Handle|Hinge|Seal", VA),
    "door-rear": (r"^Door(?: Assy)?-(Rear|Slide)\b", r"Panel|Sash|Moulding|Tape|Finisher|Trim|Lock|Handle|Hinge|Seal|Rail|Roller", VA),
    "hood": (r"^Hood(?: Assy)?\b(?!-)|^Hood Assy\b", r"Bumper|Rod|Hinge|Lock|Seal|Insulator|Stay|Release|Cable|Ledge|Garnish|Finisher|Moulding", VA),
    "fender": (r"^Fender(?: Assy)?-Front\b", r"Protector|Stay|Liner|Seal|Moulding|Finisher|Mud|Flare|Cover", VA),
    "bumper-front": (r"^Fascia(?: Kit| Assy)?-Front Bumper|^Bumper Assy-Front\b|^Fascia-Front\b", r"Finisher|Moulding|Stay|Absorber|Armature|Bracket|Lower|Cover-|Grille|Retainer", VA),
    "bumper-rear": (r"^Fascia(?: Kit| Assy)?-Rear Bumper|^Bumper Assy-Rear\b|^Fascia-Rear\b", r"Finisher|Moulding|Stay|Absorber|Reinforce|Bracket|Lower|Cover-|Step|Retainer", VA),
    "grille": (r"^Grille(?: Assy)?-(Front|Radiator)", r"Emblem|Bracket|Moulding|Finisher|Seal|Bumper|Fog|Lower", VA),
    "trunk-lid": (r"^Lid(?: Assy)?-Trunk|^Trunk Lid Assy", r"Torsion|Bumper|Finisher|Handle|Holder|Lock|Striker|Pin|Hinge|Seal", VA),
    "tailgate": (r"^(Gate|Gate Assy|Tail Gate)(?: Assy)?-(Rear|Tail)|^Tailgate Assy|^Gate-Rear", r"Handle|Lock|Hinge|Cable|Seal|Protector|Finisher|Stay|Damper|Striker|Rod", VA),
    "liftgate": (r"^(Door Assy-Back|Door-Back|Back Door Assy)\b", r"Glass|Lock|Handle|Stay|Seal|Finisher|Hinge|Spoiler|Garnish|Weatherstrip|Moulding|Switch|Striker|Window", VA),
}

CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=False)
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
