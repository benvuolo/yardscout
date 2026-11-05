"""The one reader for crawl.py's size-capped raw files (README "Raw files").

crawl.py continues a .jsonl file that reaches PART_BYTES in <name>.2.jsonl,
<name>.3.jsonl ...: one logical file, read in that order, with line numbers
(R6 recrawl_of, proof pointers) counted across the parts. Every consumer
(crawl.py, ci_audit.py, audit.py, curation adapters) reads through this module
so no part is missed.

    part_paths(raw_dir, "www.toyotapartsnow.com")          records parts
    part_paths(raw_dir, "www.toyotapartsnow.com.lists")    R1 list manifest parts
    logical_paths(Path("raw/www.toyotapartsnow.com.jsonl")) the parts of that file
    rows(paths)  -> (global line number, object or None for an unreadable line)

Read-only and dependency-free: it never heals or rewrites a file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

KINDS = ("", ".lists", ".years")  # records, R1 list manifests, R2 year manifests
_PART = re.compile(r"^(?P<base>.+)\.(?P<n>[2-9]|[1-9]\d+)\.jsonl$")


def part_path(raw_dir: Path, base: str, i: int) -> Path:
    """Part i (1-based) of raw/<base>.jsonl."""
    return Path(raw_dir) / (f"{base}.jsonl" if i == 1 else f"{base}.{i}.jsonl")


def part_count(raw_dir: Path, base: str) -> int:
    """Number of parts: 1, then every consecutive part that exists."""
    n = 1
    while part_path(raw_dir, base, n + 1).exists():
        n += 1
    return n


def part_paths(raw_dir: Path, base: str) -> list[Path]:
    """Existing parts of raw/<base>.jsonl, in reading order."""
    return [p for p in (part_path(raw_dir, base, i) for i in range(1, part_count(raw_dir, base) + 1)) if p.exists()]


def base_of(path: Path) -> str | None:
    """"www.x.com" for raw/www.x.com.jsonl or raw/www.x.com.3.jsonl; None if not .jsonl."""
    name = Path(path).name
    m = _PART.match(name)
    if m:
        return m.group("base")
    return name[: -len(".jsonl")] if name.endswith(".jsonl") else None


def is_continuation(path: Path) -> bool:
    return bool(_PART.match(Path(path).name))


def logical_paths(path: Path) -> list[Path]:
    """Every part of the logical file that `path` (any part) belongs to."""
    path = Path(path)
    base = base_of(path)
    return part_paths(path.parent, base) if base else [path]


def kind_of(path: Path) -> str:
    """"records", "lists" or "years" for a raw part path."""
    base = base_of(path) or ""
    return "lists" if base.endswith(".lists") else "years" if base.endswith(".years") else "records"


def rows(paths: list[Path]):
    """(1-based line number across all parts, parsed object or None)."""
    n = 0
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                n += 1
                try:
                    yield n, json.loads(ln)
                except ValueError:
                    yield n, None


def site_rows(raw_dir: Path, site: str, kind: str = ""):
    """rows() of raw/<site><kind>.jsonl and all its parts (kind: "", ".lists", ".years")."""
    return rows(part_paths(raw_dir, f"{site}{kind}"))
