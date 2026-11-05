"""TYC Americas (www.tycamericas.com): NOT REACHABLE through fetch.py.

Checked 2026-11-05 (robots: Crawl-delay 10, disallows /*search?, /*search=,
/*refiners=, /*sorting=; no bot check):
  * The site is Dynamics 365 Commerce. Category pages exist
    (/all/lighting/head-lamps/5637149891.c, /all/mirror/5637149874.c,
    /all/electrical/window-regulator/5637149883.c, /all/cooling/radiator/
    5637149879.c, /all/hvac/condenser/5637149887.c, ...) but render
    "Loading..." server-side: the product list (data action
    FullProductSearchResult, Top 30) is fetched client-side from the
    Commerce retail server on another domain.
  * No product (.p) URL appears in any server-rendered page or sitemap
    (/_msdyn365/sitemap/MA7t5q lists content pages only; /sitemap.xml 404).
  * Download Center has only an order-upload form and a returns form; no
    application catalog.
  * "Search By Vehicle" / product search are search URLs (robots disallows
    /*search?).
So nothing is enumerable with GET requests to the allowed domain.
"""
SITE = "www.tycamericas.com"
STATUS = ("unreachable: D365 Commerce storefront renders product lists client-side from "
          "the retail-server API on another domain; no product URLs server-side; search disallowed")
CATEGORY_PAGES = {
    "headlights": "/all/lighting/head-lamps/5637149891.c",
    "tail-lights": "/all/lighting/tail-lamps/5637149893.c",
    "side-mirrors": "/all/mirror/5637149874.c",
    "window-regulator": "/all/electrical/window-regulator/5637149883.c",
    "radiator": "/all/cooling/radiator/5637149879.c",
    "condenser": "/all/hvac/condenser/5637149887.c",
}
CATEGORIES: dict = {}
