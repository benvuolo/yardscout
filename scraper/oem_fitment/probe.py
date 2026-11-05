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
        out["pages"].append({"path": p, "robots_allows": True, "status": x.status_code,
                             "bytes": len(x.text), "challenge": bool(CHALLENGE_RE.search(x.text[:20000])),
                             "title": title.group(1).strip() if title else ""})
    except requests.RequestException as e:
        out["pages"].append({"path": p, "error": type(e).__name__})
out["usable"] = (out["robots_status"] in (200, 404) and all(
    pg.get("status") == 200 and not pg.get("challenge") for pg in out["pages"] if pg.get("robots_allows")))
print(json.dumps(out, indent=1))
