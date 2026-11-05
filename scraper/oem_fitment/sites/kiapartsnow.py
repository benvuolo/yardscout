"""www.kiapartsnow.com: Kia on the PartsGiant ".html" template, same layout
and Hyundai-group part names as hyundaipartsdeal.py, whose SUBCATS, PARTS,
ENGINE_RX and reman_fn are reused (see that module's notes).

Kia differences (learned through fetch.py, 2026-11-05)
  * Part numbers print without the hyphen: "373002G600" is Hyundai's
    "37300-2G600". Records keep the site's form; curation must compare
    numbers with "-" removed when matching Kia/Hyundai platform twins
    (Optima/Sonata, Sportage/Tucson, Forte/Elantra, Sorento/Santa Fe).
  * Supersessions can point to a reman number ("Replaced By: 373002G500RU").
    Recorded as printed.
  * Year variants: optima 2011-2015 korean_made / us_georgia_made (both were
    sold in the US; both crawled), 2006 produced_before/after_sep_2006, 2008
    new/old_body_style; sorento 2006 has three (old_body_style is the
    first-generation car and is preferred); spectra 2001-2006 sedan /
    hatchback (sedan preferred); sportage/sorento 2021+ gas / hybrid (hybrid
    excluded by the template default).
  * Rio5 and Forte5 have no catalog of their own: the rio and forte
    catalogs cover every body (body style is in the fitment option column).
    crawl.py's coverage check compares model names, so those segments use
    up to MAX_SEEDS seeds.
  * "Trim & Engine" cells read "2.0L - Theta 2" (engines).
"""
from sites import _partsgiant as T
from sites._partsgiant import M
from sites.hyundaipartsdeal import ENGINE_RX, PARTS, SUBCAT_EXCL, SUBCATS, reman_fn

SITE = "www.kiapartsnow.com"

MODELS = {
    ("Kia", "Rio5"): M("rio"),
    ("Kia", "Forte5"): M("forte"),
    ("Kia", "Sorento"): M("sorento", pref=r"^old_body_style$"),
    ("Kia", "Spectra"): M("spectra", pref=r"^sedan"),
}

CFG = T.Config(site=SITE, models=MODELS, subcats=SUBCATS, subcat_excl=SUBCAT_EXCL, parts=PARTS,
               option_column_is_trims=False, engine_rx=ENGINE_RX, reman_fn=reman_fn)
categories_for, parts_on_page, product = T.bind(CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
