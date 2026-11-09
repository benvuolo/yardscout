"""www.hyundaipartsdeal.com: Hyundai on the PartsGiant ".html" template. The
Kia module (kiapartsnow.py) reuses SUBCATS and PARTS from here: Hyundai and
Kia catalogs print the same Hyundai-group part names and part codes (PNC:
37300 alternator, 36100 starter, 97701 A/C compressor, 92101/92102
headlamps, ...).

Layout (learned through fetch.py, 2026-11-05)
  year catalog  /<year>-hyundai-<model>[-<variant>]-parts.html; variants are
                body styles or markets (sonata 2005 new_body_style_korean /
                new_body_style_us / old_body_style; 2007-2010
                new_body_style / old_body_style)
  parts list    /parts-list/<year>-hyundai-<model>/<section>/<subcat>.html,
                one list per subcategory holding every diagram of that
                subcategory for the whole catalog model (a 2011 Sonata list
                carries 14MY rows too)
  product       /genuine/hyundai-<name>~<pn>.html

List rows: group = name = "<Part> Assy-<Where>, <LH|RH>" ("Lamp Assy-Head,
LH", "Motor Assy-Front Power Wdw, LH", "Switch Assy-Power Window Main");
info holds "Location: Driver Side", "Fit Note: ...", "Production Date:
12/2009-05/2014", "Fitting Vehicle Options: 2.4L Theta 2.. DOHC - GDI",
"Replaced By: ...". Product pages print "Position", "Replaces" /
"Replaced By", and a fitment table "Year Make Model | Trim & Engine |
Important vehicle option details" whose middle cell is an engine
description ("DOHC - TCI/GDI"), read as engines via engine_rx; the option
column is body style ("Sedan - 4Door 5P").

Category notes for curators
  * Reman units carry no "reman" on the list row, only a part-number suffix
    (97701-3V110-RM); the product page names them ("Reman Compressor").
    reman_fn (REMAN_PN) drops them when a new number is on the same page.
  * Window regulator on door-module cars (2011+ Sonata) is sold as "Panel
    Assy-Front Door Module, LH" (regulator carrier); kept under
    window-regulator with its name as printed. Motors are separate rows.
  * "Sender Assy-Fuel Pump" (94460) is the level sender; not kept. The
    in-tank assembly is "Fuel Pump & Sender Module Assy" / "Complete-Fuel
    Pump" / "Pump Assy-Fuel" (31110).
  * SUV/hatch rear doors are "Tail Gate" in this catalog: kept as liftgate.
  * Fitment year spans can be wider than US model years (YF Sonata parts
    print "2009-2014 Hyundai Sonata"). Recorded as printed.
"""
import re

from sites import _partsgiant as T
from sites._partsgiant import M

SITE = "www.hyundaipartsdeal.com"

MODELS = {
    # 2005 has a Korean-market catalog besides the US ones
    ("Hyundai", "Sonata"): M("sonata", exc=r"korean"),
    ("Hyundai", "Elantra"): M("elantra", exc=r"korean"),
    ("Hyundai", "Accent"): M("accent", exc=r"korean"),
}

SUBCATS = {
    "alternator": r"^alternator$",
    "starter": r"^starter(_motor)?$",
    "ac-compressor": r"compressor|air_condition|a_c_system|aircon",
    "headlights": r"^head_?lamp",
    "tail-lights": r"^rear_combination_lamp|^tail_?lamp|^rear_lamp",
    "side-mirrors": r"mirror_outside|^rear_view_mirror|outside_mirror|door_mirror",
    "window-regulator": r"window_regulator",
    "window-switch": r"^front_door_trim|^trim_front_door|^switch$|power_window",
    "climate-control": r"heater_control|heater_system_control|a_c_control|climate_control",
    "fuel-pump-module": r"^fuel_system$|^fuel_tank$|fuel_pump",
    "throttle-body": r"throttle_body|^intake_manifold$",
    "power-steering-pump": r"power_steering_(oil_)?pump",
    "gauge-cluster": r"instrument_cluster",
    "ignition-coils": r"spark_plug|ignition",
    "radiator": r"^engine_cooling_system$|^radiator(?!_hose)",
    "door-front": r"^(panel_front_door|front_door_panel)$",
    "door-rear": r"^(panel_rear_door|rear_door_panel)$",
    "hood": r"^fender_hood_panel$|^hood_panel$",
    "fender": r"^fender_hood_panel$|^fender_panel$",
    "bumper-front": r"^(front_bumper|bumper_front)$",
    "bumper-rear": r"^(rear_bumper|bumper_rear)$",
    "grille": r"radiator_grille|^grille|^(front_bumper|bumper_front)$",
    "trunk-lid": r"trunk_lid_back_panel|back_panel_trunk_lid|^trunk_lid$",
    "liftgate": r"^tail_gate$|^back_door$",
    # tier C (§8): subs from the R2 years manifests (Hyundai and Kia)
    "wiper-motor": r"^windshield_wiper(_rear)?$|^rear_wiper_washer$|wiper_motor",
    "knuckle": r"^front_axle$|^rear_axle$|knuckle|carrier",
    "strut": r"spring_strut|strut_front|strut_rear|shock_absorber",
}
SUBCAT_EXCL = {
    "ac-compressor": r"duct|blower|evaporator|heater_unit",
    "climate-control": r"blower|evaporator|heater_unit",
    "radiator": r"hose|reservoir",
}

PNL = r"Trim|Moulding|Molding|Garnish|Hinge|Latch|Lock|Handle|Weather|W/Strip|Insulator|Pad|Seal|Stay|Lifter|Cable|Release"
PARTS = {
    "alternator": (r"^(Alternator|Generator) Assy|^Reman Alternator",
                   r"Regulator|Rotor|Stator|Frame|Pulley|Rectifier|Bracket|Cover|Brush|Bearing"),
    "starter": (r"^Starter Assy|^Motor Assy-Starter|^Reman Starter",
                r"Switch|Bracket|Armature|Yoke|Lever|Clutch|Gear|Brush|Holder|Stopper|Kit|Shaft|Packing"),
    "ac-compressor": (r"^Compressor Assy\b|^Compressor Assy-A/?C|^Reman Compressor",
                      r"Clutch|Pulley|Disc|Hub|Coil|Valve|Switch|Bracket|Seal|Sensor|Wiring|Mtg"),
    "headlights": (r"^(Lamp Assy-Head|Head Lamp Assy|Headlamp Assy|Lamp Assembly-Head)",
                   r"Bulb|Socket|Lens|Housing|Bezel|Cover|Cap|Actuator|Level|Ballast|Module|Unit-|Extension|Garnish|Holder|Washer"),
    "tail-lights": (r"^(Lamp Assy-(Rear|RR) Comb|Lamp Assy-Tail|Tail Lamp Assy|Lamp Assy-Rear Lamp)",
                    r"Bulb|Socket|Holder|Lens|Pad|Garnish|High Mount|License|Licence|Reflex|Reflector|Fog"),
    "side-mirrors": (r"^Mirror Assy-(Outside|O/S|Door)",
                     r"Glass|Holder|Cover|Cap|Actuator|Lamp|Inside|Scalp|Garnish"),
    "window-regulator": (r"^Regulator Assy-[^|]*(Door|Window|Wdw)|^Motor Assy-[^|]*(Power\s*W(in)?do?w|P/\s*W(in)?do?w|Pwr\s*Wdw|Power Reg|Window|Regulator)|^Panel Assy-[^|]*(Door|DR) Module|^Module Panel & Reg Assy-",
                         r"Generator|Fuel|Voltage|Handle|Glass|Switch|Seat|Mirror|Trunk|Tail|Sunroof|Antenna|Wiper"),
    "window-switch": (r"^Switch Assy-[^|]*(Power Window Main|P/W(in)?do?w Main|Pwr Wdw Main|Window Main)",
                      r"Assist|Sub\b|Rear|RR\b|Bezel|Cover|Pass"),
    "climate-control": (r"^(Control Assy-(Heater|A/C|Air Con|Aircon|Dual|Heater & A/C|Heater Control)|Heater Control Assy|Control Unit-(Heater|A/C)|Panel Assy-(Heater|A/C|Aircon) Control)",
                        r"Cable|Knob|Bezel|Cover|Rear|RR\b|Sensor|Lamp|Bulb|Actuator|Blower"),
    "fuel-pump-module": (r"^(Fuel Pump & Sender Module|Complete-Fuel Pump|Pump Assy-Fuel|Fuel Pump Assy|Fuel Pump Module|Module Assy-Fuel Pump|Fuel Pump & Sender)",
                         r"Filter|Cover|Packing|Ring|Plate|Bracket|Strainer|Regulator|Relay|High Pressure|Hose|Tube|Gasket|Control|Driver|Sender Assy"),
    "throttle-body": (r"^(Body Assy-Throttle|Throttle Body Assy|Throttle Body\b)",
                      r"Gasket|Sensor|Bracket|Cable|Spacer|Heater"),
    "power-steering-pump": (r"^Pump Assy-(Power Steering|P/S|Power Strg|Steering)|^Power Steering Pump",
                            r"Reservoir|Pulley|Bracket|Hose|Seal|Kit|Cap|Tank"),
    "gauge-cluster": (r"^Cluster Assy-Instrument|^Instrument Cluster Assy|^Cluster Assy\b",
                      r"Glass|Lens|Window|Housing|Case|Cover|Bulb|Socket|Plate|Board|Printed|Mask|Facia"),
    "ignition-coils": (r"^Coil Assy-Ignition|^Ignition Coil Assy|^Coil-Ignition",
                       r"Boot|Bracket|Cover"),
    "radiator": (r"^Radiator Assy|^Radiator$",
                 r"Cap|Hose|Grille|Support|Mount|Bracket|Seal|Insulator|Shroud|Fan|Drain|Plug|Reservoir|Tank|Baffle|Guide|Guard|Deflector|Cover"),
    "door-front": (r"^Panel Assy-(Front|FR) Door\b|^Door Assy-Front\b",
                   PNL + r"|Outer|Skin|Module|Belt|Frame|Glass|Speaker|Beam"),
    "door-rear": (r"^Panel Assy-(Rear|RR) Door\b|^Door Assy-Rear\b",
                  PNL + r"|Outer|Skin|Module|Belt|Frame|Glass|Speaker|Beam"),
    "hood": (r"^Panel Assy-Hood|^Hood Assy|^Panel-Hood\b",
             PNL + r"|Bumper|Grille|Rod|Scoop"),
    "fender": (r"^Panel Assy-Fender|^Fender Assy|^Panel-Fender\b",
               r"Liner|Guard|Apron|Insulator|Moulding|Garnish|Flare|Extension|Seal|Bracket|Inner|Protector|Cover"),
    "bumper-front": (r"^Cover(?: Assy)?-(Front|FR) Bumper|^Bumper Assy-Front|^Front Bumper Cover",
                     r"Absorber|Beam|Rail|Reinforce|Bracket|Lip|Moulding|Garnish|Guard|Skid|Grille|Fog|Retainer|Tow|Hook|Cap\b|Spoiler|Extension|Lower|Under|Insert|Plate|Stay|Pad|Side"),
    "bumper-rear": (r"^Cover(?: Assy)?-(Rear|RR) Bumper|^Bumper Assy-Rear|^Rear Bumper Cover",
                    r"Absorber|Beam|Rail|Reinforce|Bracket|Lip|Moulding|Garnish|Guard|Skid|Retainer|Tow|Hook|Cap\b|Spoiler|Extension|Lower|Under|Insert|Plate|Stay|Pad|Side|Step|Reflector"),
    "grille": (r"^Grille Assy-Radiator|^Radiator Grille Assy|^Grille-Radiator|^Grille Assy-Front\b",
               r"Emblem|Moulding|Garnish|Bracket|Lower|Fog|Insert|Cover|Bumper|Mesh|Plate|Cap\b|Seal|Guard"),
    "trunk-lid": (r"^Panel Assy-Trunk Lid|^Trunk Lid Assy|^Lid Assy-Trunk|^Panel-Trunk Lid",
                  PNL + r"|Torsion|Bar\b|Spoiler|Lamp|Cylinder|Actuator|Cover|Bumper|Striker"),
    "liftgate": (r"^Panel Assy-Tail ?Gate|^Tail ?Gate Assy|^Panel Assy-Back Door|^Door Assy-Tail ?Gate",
                 PNL + r"|Glass|Spoiler|Lamp|Cylinder|Actuator|Cover|Bumper|Striker|Wiper|Motor|Switch|Strut|Lifter"),
    # tier C, Kia trial rows (Hyundai shares the EPC names): "Motor Assy-Windshield
    # Wiper" / "Motor Assy-Rear Wiper" (not "Motor & Link Assy", motor plus
    # linkage); "Knuckle-Front Axle, LH", "Carrier Assy-Rear Axle, LH"; "Strut
    # Assy-Fr, LH", "Shock Absorber Assy-Front, LH" / "-Rear". "Damper
    # Assy-Dynamic" is not a strut; "Strut, LH" on the rear axle page is a brake part.
    "wiper-motor": (r"^Motor Assy-(Windshield|Front|Rear|Back|Tail ?Gate|Liftgate)?\s*Wiper",
                    r"Link|Washer|Pump|Arm|Blade|Cover|Cap|Pivot|Crank|Relay|Switch"),
    "knuckle": (r"^Knuckle(?: Assy)?-(Front|Fr|Steering)|^Carrier Assy-(Rear|Rr) Axle|^Knuckle-Rear|^Carrier-Rear Axle",
                r"Hub|Bearing|Bolt|Nut|Cover|Seal|Shield|Bush|Arm|Sensor|Ring"),
    "strut": (r"^Strut Assy-|^Shock Absorber Assy-|^Strut & Spring Assy|^Shock Absorber & Spring",
              r"Mount|Insulator|Bearing|Spring Pad|Pad|Seat|Bumper|Stopper|Cap|Cover|Dust|Kit|Bracket|Nut|Bolt|Dynamic|Bar|Rod"),
}

# Older catalogs spell "Assembly" where newer ones print "Assy".
PARTS = {k: (v[0].replace("Assy", "Ass(?:y|embly)"),) + tuple(v[1:]) for k, v in PARTS.items()}

# "Trim & Engine" cells are engine descriptions: "DOHC - TCI/GDI", "SOHC - MPI".
ENGINE_RX = r"^(DOHC|SOHC|OHC|OHV|\d\.\d\s*L|V6|V8|LPI|LPG|CRDI|Diesel|Hybrid|Gasoline|Electric|MPI|GDI|TCI)\b"
REMAN_PN = r"(?:-RM|(?<=\d)RU|(?<=\d)RM)$"


def reman_fn(row: dict) -> bool:
    return bool(re.search(REMAN_PN, row["pn"], re.I))

CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=False, engine_rx=ENGINE_RX, reman_fn=reman_fn)
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
