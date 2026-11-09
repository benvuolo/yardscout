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


def complete_conf(wl_site: dict | None) -> dict | None:
    """R3 completion config of a site's worklist entry, or None:
    {"file": "<path under scraper/oem_fitment>", "version": N}. The file is
    a completion worklist ({"rows": [{site?, make, model, year, cats}]},
    e.g. curate.py's _report/<ns>.own_page_completion.json); rows naming
    another site are skipped."""
    c = (wl_site or {}).get("complete")
    if not c:
        return None
    if not isinstance(c, dict) or not isinstance(c.get("file"), str):
        raise ValueError(f"worklist complete must be {{file, version}}, got {c!r}")
    v = c.get("version", 1)
    if not isinstance(v, int) or v < 1:
        raise ValueError(f"complete version must be an int >= 1, got {v!r}")
    return {"file": c["file"], "version": v}


def complete_name(site: str, wl_site: dict | None) -> str | None:
    """Finish marker of the site's R3 completion pass (raw/<site>.cN.done), or
    None when the entry has no completion config. Raising the version (a new
    worklist file) re-opens the pass; progress C| keys skip rows already read."""
    c = complete_conf(wl_site)
    return None if c is None else f"{site}.c{c['version']}.done"


def mode(site: str, wl_site: dict | None, on_branch) -> str | None:
    """What the next run does for a site, given on_branch(name) -> bool for
    raw/<name> on oem-raw: "crawl" (worklist not finished), "complete"
    (finished, completion configured and not finished) or None (nothing)."""
    if on_branch(f"{site}.blocked") or on_branch(f"{site}.paused"):
        return None
    if not on_branch(done_name(site, wl_site)):
        return "crawl"
    cn = complete_name(site, wl_site)
    if cn and not on_branch(cn):
        return "complete"
    return None
