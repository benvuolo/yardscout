"""www.infinitipartsdeal.com: Infiniti on the PartsGiant ".html" template.
Infiniti part names are Nissan's, so SUBCATS and PARTS come from
nissanpartsdeal.py.

Year catalogs split by body: g35 "coupe" 2003-2007 and "sedan" 2007-2008
only (no G35 sedan catalog for 2003-2006 on this site, 2026-11-05), g37
"coupe"/"sedan"/"convertible". Feed names that are not site models map to
the site models that carry them (G35X/G37X/G37 Sedan/G Sedan: the sedan
catalogs; FX: fx35 + fx45; M: m35 + m45).
"""
from sites import _partsgiant as T
from sites._partsgiant import M
from sites import nissanpartsdeal as N

SITE = "www.infinitipartsdeal.com"

MODELS = {
    ("Infiniti", "G35"): M("g35", pref=r"^sedan$"),
    ("Infiniti", "G35X"): M("g35", inc=r"^sedan$"),
    ("Infiniti", "G37"): M("g37", inc=r"^(sedan|coupe)$", pref=r"^sedan$"),
    ("Infiniti", "G37 Sedan"): M("g37", inc=r"^sedan$"),
    ("Infiniti", "G37X"): M("g37", inc=r"^sedan$"),
    ("Infiniti", "G Sedan"): M("g37", inc=r"^sedan$"),
    ("Infiniti", "FX"): M(["fx35", "fx45"]),
    ("Infiniti", "M"): M(["m35", "m45"]),
}

CFG = T.Config(site=SITE, models=MODELS, subcats=N.SUBCATS, subcat_excl=N.SUBCAT_EXCL, parts=N.PARTS,
               option_column_is_trims=False)
categories_for, parts_on_page, product = T.bind(CFG)
