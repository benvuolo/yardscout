#!/usr/bin/env python3
"""fetch.py challenge detection. Offline.
Run: python3 scraper/oem_fitment/tests/test_fetch_challenge.py

1. Every site except ecat.spectrapremium.com: challenged() equals the old
   rule (403/429/503 or CHALLENGE_RE in the first 20 KB) on every input.
2. ecat.spectrapremium.com: rule (a)-(e) (SOURCES.md). Real pages
   (untouched, retrieved 2026-11-09) pass; every variant below stops.
"""
import gzip
import re
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


VEH = gzip.decompress((HERE / "fixtures/spectra_full_vehicle_23745.html.gz").read_bytes()).decode()
PART = gzip.decompress((HERE / "fixtures/spectra_full_part_CU13221.html.gz").read_bytes()).decode()
VP, PP = "/en/vehicles/23745/parts", "/en/parts/CU13221"
SP = fetch.SPECTRA


def old_rule(status, body):
    return status in (403, 429, 503) or bool(fetch.CHALLENGE_RE.search(body[:20000]))


# 1. other sites: unchanged
bodies = ["<html>ok</html>", VEH, PART, "<title>Just a moment...</title>", "x" * 20001 + "captcha",
          "x" * 19990 + "captcha", '{"a": 1}', "<div class=cf-chl></div>", "Attention Required! | Cloudflare",
          "unusual traffic"]
same = True
for host in ("www.dbelectrical.com", "www.toyotapartsnow.com", "www.tycamericas.com", "spectrapremium.com",
             "www.spectrapremium.com"):
    for st in (200, 301, 403, 404, 429, 500, 503):
        for b in bodies:
            if fetch.challenged(host, VP, st, b) != old_rule(st, b):
                same = False
                print("  differs:", host, st, b[:40])
check("other sites: challenged() == old rule on 350 inputs", same)
check("real Spectra page on another host still stops (scope is the exact netloc)",
      fetch.challenged("www.dbelectrical.com", VP, 200, VEH))
check("ecat.spectrapremium.com is allowlisted", SP in fetch.ALLOWED)

# 2. Spectra: real pages pass
check("real vehicle page passes", not fetch.challenged(SP, VP, 200, VEH))
check("real part page passes", not fetch.challenged(SP, PP, 200, PART))
check("JSON endpoint passes", not fetch.challenged(SP, "/en/vehicules/get-models.json", 200, '{"Civic": "Civic"}'))

W = fetch._SP_WIDGET.search(VEH).group(0)
form = fetch._SP_VINFORM.search(VEH)
variants = {
    "second widget": VEH.replace("</body>", W + "</body>"),
    "visible widget": VEH.replace('data-size="invisible"', 'data-size="normal"'),
    "widget without data-size": VEH.replace(' data-size="invisible"', ""),
    "widget outside vin-search-form": VEH.replace(W, "").replace("</body>", W + "</body>"),
    "missing catalog body (no motorization block)": VEH.replace("parts__motorization", "x"),
    "missing parts counter": VEH.replace("Showing parts", "x"),
    "unusual traffic text": VEH.replace("</body>", "<p>We have detected unusual traffic</p></body>"),
    "verify you are human": VEH.replace("</body>", "<p>Please verify you are human</p></body>"),
    "challenge-platform marker": VEH.replace("</body>", '<script src="/cdn-cgi/challenge-platform/x"></script></body>'),
    "other captcha text": VEH.replace("</body>", "<p>captcha</p></body>"),
    "hcaptcha widget": VEH.replace("</body>", '<div class="h-captcha"></div></body>'),
    "second api.js include": VEH.replace("</head>", '<script src="https://www.google.com/recaptcha/api.js?hl=en" async="async" defer="defer"></script></head>'),
    "interstitial page": '<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>',
    "empty body": "",
}
for name, body in variants.items():
    check(f"stops: {name}", fetch.challenged(SP, VP, 200, body))
check("stops: part page without application table", fetch.challenged(SP, PP, 200, PART.replace("part__table-applications", "x")))
check("stops: JSON endpoint returning HTML", fetch.challenged(SP, "/en/vehicules/get-models.json", 200, VEH))
check("stops: unknown path", fetch.challenged(SP, "/en/vehicules/get-vehicle", 200, VEH))
for st in (403, 429, 503, 500, 404, 301):
    check(f"stops: HTTP {st} with a real page body", fetch.challenged(SP, VP, st, VEH))

print(f"{'FAILED ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
