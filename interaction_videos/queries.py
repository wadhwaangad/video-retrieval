from __future__ import annotations

from .config import Format


def expand(format_: Format) -> list[tuple[str, str]]:
    """Return exact-phrase Stage-1 searches from the sole format bank.

    Each query term encodes interaction evidence (for example, ``with client``
    or ``call with prospect``). Quoting it prevents broad topical matches such
    as an advice lecture or a video about how to conduct a sales call.
    """
    return [(term, f'"{term}"') for term in format_.query_terms]
