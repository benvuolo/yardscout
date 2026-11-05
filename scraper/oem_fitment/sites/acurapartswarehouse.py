"""www.acurapartswarehouse.com: Acura on the PartsGiant ".html" template.

Rules, page map and trim choice are shared with hondapartsnow.py in
sites/_honda_names.py (both print American Honda's part names).

Site facts (fetch.py, 2026-11-05): same layout as hondapartsnow; trim slugs
have no "_" between emission code and transmission ("4dr_base-ka5at",
"5dr_tech_entertainment-ka5at"). RL also lists Alaska/Hawaii trims, which the
trim picker skips.
"""
from sites import _partsgiant as T
from sites import _honda_names as H

SITE = "www.acurapartswarehouse.com"

MODELS: dict = {}

CFG = H.make_config(T, SITE, MODELS)
categories_for, parts_on_page, product = H.bind(T, CFG)
# R1/R2/R4 manifests (README "Site module contract"), re-read from the cache
year_manifest, list_manifest, chain_links = T.bind_manifests(CFG)
