from __future__ import annotations

from .config import Format


def expand(format_: Format) -> list[tuple[str, str]]:
    """Return focused Stage-1 searches from the format's own terms only.

    The suffixes are shared retrieval syntax, not a second taxonomy or
    per-format configuration bank. They favor videos that expose a complete,
    observable interaction instead of short topical explainers.
    """
    queries: list[tuple[str, str]] = []
    for term in format_.query_terms:
        queries.extend((
            (term, f'"{term}"'),
            (term, f'"{term}" "full session"'),
            (term, f'"{term}" "real session"'),
        ))
    return queries
