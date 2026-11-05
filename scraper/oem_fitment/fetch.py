#!/usr/bin/env python3
"""Polite, rule-enforcing fetcher for OEM-fitment research (CLAUDE.md rule 2).

Every request to a parts catalog in this program goes through here. It:
  * refuses any domain not in ALLOWED (no other sites, ever);
  * checks robots.txt (cached) for the requested path and refuses disallowed
    paths, plus honeypot-looking URLs;
  * waits PER_DOMAIN_GAP seconds between requests to one domain and
    GLOBAL_GAP between any two requests, across all processes (file locks);
  * stops a domain for good (circuit breaker file) on a bot check, 403, 429
    or 503: no retries, no workarounds;
  * caches every response on disk, so nothing is fetched twice and
    verification re-reads the cache instead of the site.

CLI:  python3 scraper/oem_fitment/fetch.py URL [--text] [--max-lines N]
      prints JSON {url, status, cached, retrieved, cache_path, text?}
Lib:  from fetch import get, text_lines
"""
from __future__ import annotations

import fcntl
import gzip
import hashlib
import html as htmllib
import json
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = "YardScout-research/1.0 (+https://yardscout.io; OEM fitment lookup, 1 req/4s)"
ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".state"
CACHE = ROOT / "cache"
PER_DOMAIN_GAP = 4.0
GLOBAL_GAP = 0.5
TIMEOUT = 40

ALLOWED = {
    "www.toyotapartsnow.com", "www.lexuspartsnow.com", "www.hondapartsnow.com",
    "www.acurapartswarehouse.com", "www.nissanpartsdeal.com",
    "www.infinitipartsdeal.com", "www.subarupartsdeal.com",
    "www.kiapartsnow.com", "www.hyundaipartsdeal.com",
    "www.jeeppartsdeal.com", "www.moparpartsgiant.com",
    "www.fordpartsgiant.com", "www.gmpartsgiant.com",
    "en.wikipedia.org",
    # aftermarket application catalogs (robots allow, no bot check, 2026-11-05)
    "www.densoautoparts.com", "www.dbelectrical.com", "www.tycamericas.com",
}
# robots.txt Crawl-delay or a gentler pace where a site asks for it
DOMAIN_GAP = {"www.tycamericas.com": 10.0, "www.subarupartsdeal.com": 5.0}
CHALLENGE_RE = re.compile(r"Attention Required!|cf-chl|challenge-platform|Just a moment\.\.\.|captcha", re.I)


class Refused(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _locked_wait(name: str, gap: float) -> None:
    """Block until `gap` seconds have passed since the last request stamped
    under `name`, then stamp now. Works across processes."""
    STATE.mkdir(parents=True, exist_ok=True)
    p = STATE / f"{name}.lock"
    with open(p, "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        raw = fh.read().strip()
        last = float(raw) if raw else 0.0
        wait = last + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        fh.seek(0)
        fh.truncate()
        fh.write(str(time.time()))
        fh.flush()
        fcntl.flock(fh, fcntl.LOCK_UN)


def _breaker(domain: str) -> Path:
    return STATE / f"blocked_{domain}.txt"


_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def _robots_ok(url: str) -> bool:
    u = urllib.parse.urlsplit(url)
    rp = _robots.get(u.netloc)
    if rp is None:
        cp = CACHE / u.netloc / "robots.txt"
        if cp.exists():
            body = cp.read_text(errors="ignore")
        else:
            _locked_wait("global", GLOBAL_GAP)
            _locked_wait(u.netloc, PER_DOMAIN_GAP)
            r = requests.get(f"{u.scheme}://{u.netloc}/robots.txt", headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code >= 400 and r.status_code not in (404, 410):
                raise Refused(f"robots.txt HTTP {r.status_code} for {u.netloc}: treating site as closed")
            body = r.text if r.status_code == 200 else ""
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(body)
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(body.splitlines())
        _robots[u.netloc] = rp
    return rp.can_fetch(UA, url) and rp.can_fetch("*", url)


def _robots_delay(netloc: str) -> float:
    rp = _robots.get(netloc)
    try:
        d = rp.crawl_delay("*") if rp else None
    except Exception:
        d = None
    return float(d) if d else 0.0


def cache_path(url: str) -> Path:
    u = urllib.parse.urlsplit(url)
    h = hashlib.sha1(url.encode()).hexdigest()
    return CACHE / u.netloc / f"{h}.json.gz"


def get(url: str) -> dict:
    """Return {url, status, cached, retrieved, cache_path, html}. Raises Refused."""
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or u.netloc not in ALLOWED:
        raise Refused(f"domain not allowed: {u.netloc}")
    if "honeypot" in url.lower():
        raise Refused("honeypot URL")
    cp = cache_path(url)
    if cp.exists():
        d = json.loads(gzip.decompress(cp.read_bytes()))
        d["cached"] = True
        d["cache_path"] = str(cp)
        return d
    if _breaker(u.netloc).exists():
        raise Refused(f"{u.netloc} stopped earlier: {_breaker(u.netloc).read_text().strip()}")
    if not _robots_ok(url):
        raise Refused(f"robots.txt disallows {u.path}")
    _locked_wait("global", GLOBAL_GAP)
    _locked_wait(u.netloc, max(PER_DOMAIN_GAP, DOMAIN_GAP.get(u.netloc, 0.0), _robots_delay(u.netloc)))
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        raise Refused(f"network error: {type(e).__name__}") from e
    body = r.text
    if r.status_code in (403, 429, 503) or CHALLENGE_RE.search(body[:20000]):
        STATE.mkdir(parents=True, exist_ok=True)
        _breaker(u.netloc).write_text(f"{_now()} HTTP {r.status_code} on {url}")
        raise Refused(f"{u.netloc} refused or challenged (HTTP {r.status_code}); domain stopped for this program")
    d = {"url": url, "final_url": r.url, "status": r.status_code, "retrieved": _now(), "html": body}
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(gzip.compress(json.dumps(d).encode()))
    d["cached"] = False
    d["cache_path"] = str(cp)
    return d


def text_lines(html: str) -> list[str]:
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", html, flags=re.S | re.I)
    t = htmllib.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [ln.strip() for ln in t.splitlines() if ln.strip()]


def links(html: str, pattern: str) -> list[str]:
    return sorted(set(re.findall(r'href="(' + pattern + r')"', html)))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--max-lines", type=int, default=400)
    a = ap.parse_args()
    try:
        d = get(a.url)
    except Refused as e:
        print(json.dumps({"url": a.url, "refused": str(e)}))
        sys.exit(2)
    out = {k: d[k] for k in ("url", "final_url", "status", "cached", "retrieved", "cache_path") if k in d}
    if a.text:
        out["text"] = text_lines(d["html"])[: a.max_lines]
    print(json.dumps(out, ensure_ascii=False))
