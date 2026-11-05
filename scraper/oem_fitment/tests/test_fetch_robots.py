#!/usr/bin/env python3
"""fetch.py robots reading: every "User-agent: *" group counts, * and $
wildcards work, longest match wins. Offline. Run: python3 scraper/oem_fitment/tests/test_fetch_robots.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fetch import rfc9309_allows  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


DB = """User-agent: *
Allow: /

User-agent: Googlebot
Disallow: /private/

User-agent: *
Disallow: /search.php
Disallow: /*?_bc_fsnf=1*
Disallow: /cart.php
"""
check("second * group applies: /search.php refused", not rfc9309_allows(DB, "https://x.com/search.php?q=alt"))
check("wildcard query rule: facet URL refused", not rfc9309_allows(DB, "https://x.com/alternators/?_bc_fsnf=1&brand=2"))
check("product page allowed", rfc9309_allows(DB, "https://x.com/products/400-14103.html"))
check("other bot's group ignored", rfc9309_allows(DB, "https://x.com/private/a"))
SP = """User-Agent: *
Allow: /online/contact/us
Disallow: /online/
Disallow: /Page_Product/
"""
check("SimplePart /online/ refused", not rfc9309_allows(SP, "https://x.com/online/login"))
check("longer Allow beats shorter Disallow", rfc9309_allows(SP, "https://x.com/online/contact/us"))
check("/oem/ product allowed", rfc9309_allows(SP, "https://x.com/oem/toyota~x~52159-0r160"))
END = "User-agent: *\nDisallow: /*.pdf$\n"
check("$ anchors the end", not rfc9309_allows(END, "https://x.com/a/b.pdf") and rfc9309_allows(END, "https://x.com/a/b.pdf?x=1"))
check("empty robots allows", rfc9309_allows("", "https://x.com/anything"))
print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURES"))
sys.exit(1 if fails else 0)
