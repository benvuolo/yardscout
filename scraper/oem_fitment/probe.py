#!/usr/bin/env python3
"""Check whether a NEW catalog domain may be used, without crawling it.

    python3 scraper/oem_fitment/probe.py www.example.com [/sample/path ...]

Fetches only robots.txt and the home page (plus any sample paths given, max 3),
5 s apart, with the program's honest user agent. Reports robots rules for "*",
crawl-delay, HTTP codes, and whether any response is a bot check. A domain is
usable only if robots allows the catalog paths AND no response is a challenge
AND no 403/429/503 appears. This tool never adds a domain to fetch.ALLOWED;
the hub does that after reading the report and the site's terms.
"""
import json
import re
import sys
import time
import urllib.robotparser

import requests

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from fetch import UA, CHALLENGE_RE  # noqa: E402

FIT_RE = re.compile(r"vehicle fitment|this part fits|fits the following|fits these|compatible vehicles|"
                    r"vehicle compatibility|fitment details|check fitment|year make model", re.I)
YMM_RE = re.compile(r"\b(?:19[5-9]\d|20[0-3]\d)(?:\s*-\s*(?:19[5-9]\d|20[0-3]\d))?\s+[A-Z][A-Za-z-]+\s+[A-Z0-9][A-Za-z0-9-]+")
TERMS_RE = re.compile(r"[^.]{0,140}\b(?:automated|robots?\b|scrap(?:e|er|ers|ing)|crawl|spider|data[- ]mining|harvest)"
                      r"[^.]{0,140}", re.I)


def signals(html: str, txt: str) -> dict:
    """Read-only markers from the one response already fetched: template,
    fitment list present in server HTML, and anti-automation clauses (terms)."""
    tpl = []
    if "__INITIAL_STORE__" in html:
        tpl.append("simplepart_store")
    if re.search(r"revolutionparts|rp-cdn|revparts", html, re.I):
        tpl.append("revolutionparts")
    if re.search(r"partsgiant|partsdeal|partsnow", html, re.I) and re.search(r"\.html", html):
        tpl.append("partsgiant_html")
    return {"template_markers": tpl,
            "fitment_markers": sorted({m.group(0).lower() for m in FIT_RE.finditer(txt)})[:8],
            "ymm_rows_in_text": len(YMM_RE.findall(txt)),
            "ymm_samples": [m.group(0) for m in YMM_RE.finditer(txt)][:6],
            "linked_catalog_domains": sorted(set(re.findall(
                r"(?:www\.)?[a-z0-9-]+(?:partsgiant|partsdeal|partsnow|partswarehouse|partsonline)\.com", html, re.I)))[:40],
            "sample_links": sorted(set(re.findall(r'href="(/[^"#?]{3,140}\.html)"', html)))[:25],
            "fit_context": [txt[m.start():m.start() + 400] for m in FIT_RE.finditer(txt)
                            if m.group(0).lower() != "year make model"][:2],
            "terms_hits": [m.group(0).strip()[:280] for m in TERMS_RE.finditer(txt)][:6],
            # terms text some templates keep only in the embedded store (JSON, unescaped here)
            "terms_hits_raw": [m.group(0).strip()[:280] for m in TERMS_RE.finditer(
                html.encode().decode("unicode_escape", "ignore") if "__INITIAL_STORE__" in html else "")
                if not re.search(r"robots|crawl|spider", m.group(0), re.I) or "terms" in html.lower()][:8]}


dom = sys.argv[1]
paths = sys.argv[2:5]
out = {"domain": dom}
r = requests.get(f"https://{dom}/robots.txt", headers={"User-Agent": UA}, timeout=30)
out["robots_status"] = r.status_code
body = r.text if r.status_code == 200 else ""
rp = urllib.robotparser.RobotFileParser()
rp.parse(body.splitlines())
out["crawl_delay"] = rp.crawl_delay("*")
out["robots_star_disallow"] = [ln.split(":", 1)[1].strip() for ln in body.splitlines()
                               if ln.lower().startswith("disallow")][:30]
out["pages"] = []
for p in ["/"] + paths:
    time.sleep(5)
    url = f"https://{dom}{p}"
    allowed = rp.can_fetch("*", url) and rp.can_fetch(UA, url)
    if not allowed:
        out["pages"].append({"path": p, "robots_allows": False})
        continue
    try:
        x = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        title = re.search(r"<title>([^<]{0,120})", x.text)
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", x.text)))
        out["pages"].append({"path": p, "robots_allows": True, "status": x.status_code,
                             "bytes": len(x.text), "challenge": bool(CHALLENGE_RE.search(x.text[:20000])),
                             "title": title.group(1).strip() if title else "",
                             "final_url": x.url, "signals": signals(x.text, txt)})
    except requests.RequestException as e:
        out["pages"].append({"path": p, "error": type(e).__name__})
out["usable"] = (out["robots_status"] in (200, 404) and all(
    pg.get("status") == 200 and not pg.get("challenge") for pg in out["pages"] if pg.get("robots_allows")))
print(json.dumps(out, indent=1))
