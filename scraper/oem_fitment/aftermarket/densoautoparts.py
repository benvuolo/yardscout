"""DENSO Auto Parts (www.densoautoparts.com): NOT REACHABLE through fetch.py.

Checked 2026-11-05 (robots allows `*` everywhere; no bot check):
  * /catalogs/ says "PDF versions of our catalogs for the U.S. and Canada are
    no longer available" and points to Find My Part.
  * Find My Part (denso-part-finder-plugin 1.4.4) loads every list by
    POST https://www.densoautoparts.com/wp-admin/admin-ajax.php with a
    WordPress nonce (actions dpf_opticat_years/makes/models/engines/trims/
    part_types/parts). /part-finder-part-details/ and
    /part-finder-search-results/ are empty shells filled by those calls.
  * No product or application page is server-rendered; the sitemaps
    (page/post/events) list no part pages.
fetch.get is GET-only and the brief forbids any other client, so this site
yields nothing here. Using the AJAX endpoint would need a POST path in
fetch.py and a hub/owner decision (it is a search endpoint behind a nonce).
"""
SITE = "www.densoautoparts.com"
STATUS = ("unreachable: catalog is POST-only admin-ajax with a nonce (no GET product or "
          "application pages; PDF catalogs withdrawn)")
CATEGORIES: dict = {}
