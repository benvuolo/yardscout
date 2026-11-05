"""Finish-marker names on the oem-raw branch (no imports: the workflow's plan
step loads this without the crawler's dependencies).

A site's worklist entry may carry "version": N. Version 1 (or none) finishes
with raw/<site>.done, as every site did before. When seeds are added to a
site that already finished, its entry's version is raised instead of
deleting the old marker: the old .done stays on oem-raw as evidence of the
earlier pass, the next scheduled run sees no raw/<site>.vN.done and crawls
again, and progress.json's done keys skip every seed already crawled.
"""
from __future__ import annotations


def version(wl_site: dict | None) -> int:
    v = (wl_site or {}).get("version", 1)
    if not isinstance(v, int) or v < 1:
        raise ValueError(f"worklist version must be an int >= 1, got {v!r}")
    return v


def done_name(site: str, wl_site: dict | None) -> str:
    v = version(wl_site)
    return f"{site}.done" if v == 1 else f"{site}.v{v}.done"
