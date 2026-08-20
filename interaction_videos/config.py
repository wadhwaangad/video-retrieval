from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Format:
    slug: str
    description: str
    query_terms: list[str]


def load_formats(path: str | Path) -> list[Format]:
    """Read the deliberately small YAML subset used by the v1 format bank."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    formats: list[Format] = []
    current: dict | None = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = re.match(r"^  ([a-z_]+):\s*$", raw)
        if match:
            if current:
                formats.append(Format(**current))
            current = {"slug": match.group(1), "description": "", "query_terms": []}
            continue
        if not current:
            continue
        desc = re.match(r'^    description:\s*"(.*)"\s*$', raw)
        if desc:
            current["description"] = desc.group(1)
            continue
        inline = re.match(r"^    query_terms:\s*\[(.*)\]\s*$", raw)
        if inline:
            current["query_terms"] = re.findall(r'"([^"]+)"', inline.group(1))
            continue
        item = re.match(r'^      -\s+"?(.*?)"?\s*$', raw)
        if item:
            current["query_terms"].append(item.group(1))
    if current:
        formats.append(Format(**current))
    if not formats:
        raise ValueError(f"No formats found in {path}")
    return formats
