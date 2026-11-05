"""www.hondapartsnow.com: Honda on the PartsGiant ".html" template.

Rules, page map and trim choice are shared with acurapartswarehouse.py in
sites/_honda_names.py (both print American Honda's part names).

Site facts (fetch.py, 2026-11-05): model page /honda-<slug>-parts.html, year
page /<year>-honda-<slug>-parts.html lists per-trim catalogs
/<year>-honda-<slug>--<body>_<trim>-<ka|kl>_<trans>-parts.html. Product pages
are /genuine/honda~<name>~<pn>.html; their fitment table is
"Year Make Model | Body & Trim | Emission & Transmission" (one row per year;
no engine column, no Position line). "Civic Hybrid" has no model page of its
own: it is the Civic catalog's "4dr_mx_hybrid..." trims, and its fitment rows
print model "Civic".
"""
from sites import _partsgiant as T
from sites import _honda_names as H
from sites._partsgiant import M

SITE = "www.hondapartsnow.com"

MODELS = {
    ("Honda", "CR-V"): M("cr_v"),
    ("Honda", "Civic Hybrid"): M("civic"),
    ("Honda", "Accord Hybrid"): M("accord"),
}

CFG = H.make_config(T, SITE, MODELS)
categories_for, parts_on_page, product = H.bind(T, CFG)
