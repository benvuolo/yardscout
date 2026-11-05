"""Test helper: make the PartsGiant template (sites/_partsgiant.py) read the
fetch.py cache only. A cache miss raises CacheMiss instead of touching the
network; have() lets a test skip its page checks on a machine without the
cache (scraper/oem_fitment/cache is gitignored)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import fetch  # noqa: E402
from sites import _partsgiant  # noqa: E402


class CacheMiss(Exception):
    pass


def cache_only_get(url: str) -> dict:
    if not fetch.cache_path(url).exists():
        raise CacheMiss(url)
    return fetch.get(url)


def install() -> None:
    _partsgiant.get = cache_only_get


def have(urls: list[str]) -> bool:
    missing = [u for u in urls if not fetch.cache_path(u).exists()]
    for u in missing:
        print(f"SKIP (not in local cache): {u}")
    return not missing
