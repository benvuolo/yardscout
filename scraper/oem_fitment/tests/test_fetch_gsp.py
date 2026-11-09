#!/usr/bin/env python3
"""fetch.py: gspnorthamerica.com detector rule (a)-(e) (SOURCES.md, Source scout 2). Offline.
Run: python3 scraper/oem_fitment/tests/test_fetch_gsp.py

1. Every other host: challenged() equals the old rule on every input,
   including the real GSP pages.
2. gspnorthamerica.com: real pages (untouched product page retrieved
   2026-11-09; the real sitemap index) pass; every variant below stops.
"""
import gzip
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fetch  # noqa: E402

fails = []


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(name)


PROD = gzip.decompress((HERE / "fixtures/gsp_full_product_ncv36167xd.html.gz").read_bytes()).decode()
IDX = (HERE.parent / "aftermarket/tests/fixtures/gsp_sitemap_index.xml").read_text()
URLSET = (HERE.parent / "aftermarket/tests/fixtures/gsp_sitemap_products_2_head.xml").read_text()
G, PP = fetch.GSP, "/products/ncv36167xd"


def old_rule(status, body):
    return status in (403, 429, 503) or bool(fetch.CHALLENGE_RE.search(body[:20000]))


# 1. other hosts unchanged
bodies = [PROD, IDX, URLSET, "<html>ok</html>", "<title>Just a moment...</title>", "x" * 19990 + "captcha",
          "x" * 20001 + "captcha", "<div class=cf-chl></div>", "unusual traffic", '<script id="captcha-bootstrap"></script>']
same = True
n = 0
for host in ("www.dbelectrical.com", "www.toyotapartsnow.com", "www.1aauto.com", "www.gspnorthamerica.com",
             "gspnorthamerica.com.evil.example", "shop.gspnorthamerica.com"):
    for st in (200, 301, 403, 404, 429, 500, 503):
        for b in bodies:
            for path in (PP, "/", "/sitemap.xml"):
                n += 1
                if fetch.challenged(host, path, st, b) != old_rule(st, b):
                    same = False
                    print("  differs:", host, st, path, b[:40])
check(f"other hosts: challenged() == old rule on {n} inputs (incl. real GSP pages)", same)
check("real GSP page on another host keeps the old rule", fetch.challenged("www.1aauto.com", PP, 200, PROD) == old_rule(200, PROD))
check("gspnorthamerica.com is allowlisted", G in fetch.ALLOWED)
check("Spectra rule untouched (still its own function)", fetch.challenged(fetch.SPECTRA, PP, 200, PROD))

# 2. GSP: real pages pass
check("real product page passes", not fetch.challenged(G, PP, 200, PROD))
check("real product page has 'captcha' in its first 20 KB or later only inside scripts",
      fetch.CHALLENGE_RE.search(fetch._SCRIPT_EL.sub(" ", PROD)) is None)
check("real sitemap index passes", not fetch.challenged(G, "/sitemap.xml", 200, IDX))
check("real product sitemap passes", not fetch.challenged(G, "/sitemap_products_2.xml", 200, URLSET))
check("site root '/' (robots warm-up) passes on a GSP-titled page", not fetch.challenged(G, "/", 200, PROD))

B = "</body>"
variants = {
    "visible g-recaptcha div": PROD.replace(B, '<div class="g-recaptcha" data-sitekey="x"></div>' + B),
    "visible h-captcha div": PROD.replace(B, '<div class="h-captcha" data-sitekey="x"></div>' + B),
    "visible turnstile div": PROD.replace(B, '<div class="cf-turnstile" data-sitekey="x"></div>' + B),
    "visible 'verify you are human'": PROD.replace(B, "<p>Please verify you are human</p>" + B),
    "'verify you are human' inside a script": PROD.replace(B, "<script>var m='Verify you are human';</script>" + B),
    "visible 'unusual traffic'": PROD.replace(B, "<p>We detected unusual traffic</p>" + B),
    "visible 'captcha' text": PROD.replace(B, "<p>Complete the captcha to continue</p>" + B),
    "Shopify /challenge page link": PROD.replace(B, '<form action="/challenge" method="post"></form>' + B),
    "Shopify /checkpoint page": PROD.replace(B, '<a href="/checkpoint">continue</a>' + B),
    "cf-chl marker in a script": PROD.replace(B, "<script>window._cf_chl_opt={}; var x='cf-chl';</script>" + B),
    "challenge-platform script": PROD.replace(B, '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate"></script>' + B),
    "'Just a moment...' title anywhere": PROD.replace(B, "<script>document.title='Just a moment...'</script>" + B),
    "'Attention Required!' text": PROD.replace(B, "<h1>Attention Required! | Cloudflare</h1>" + B),
    "second captcha-bootstrap script": PROD.replace(B, '<script id="captcha-bootstrap"></script>' + B),
    "no captcha-bootstrap script": PROD.replace('<script id="captcha-bootstrap">', '<script id="x-bootstrap">'),
    "missing part-number line": PROD.replace("<strong>Part Number:</strong>", "<strong>PN</strong>"),
    "title not GSP North America": PROD.replace("GSP North America</title>", "Shop</title>", 1)
    if "GSP North America</title>" in PROD else PROD.replace("\n</title>", " x</title>", 1),
    "interstitial page": "<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>",
    "Shopify challenge page": '<html><head><title>GSP North America</title></head><body><form action="/challenge"><div class="h-captcha"></div></form></body></html>',
    "empty body": "",
}
for name, body in variants.items():
    check(f"stops: {name}", fetch.challenged(G, PP, 200, body))
check("stops: unknown path", fetch.challenged(G, "/collections/all", 200, PROD))
check("stops: search path", fetch.challenged(G, "/search", 200, PROD))
check("stops: product .json variant", fetch.challenged(G, PP + ".json", 200, '{"product":{}}'))
check("stops: sitemap that is HTML", fetch.challenged(G, "/sitemap.xml", 200, PROD))
check("stops: sitemap with a captcha word", fetch.challenged(G, "/sitemap.xml", 200, IDX.replace("</sitemapindex>", "<!-- captcha --></sitemapindex>")))
check("stops: sitemap of another kind", fetch.challenged(G, "/sitemap.xml", 200, "<rss></rss>"))
for st in (403, 429, 503, 500, 404, 301):
    check(f"stops: HTTP {st} with a real page body", fetch.challenged(G, PP, st, PROD))

print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
