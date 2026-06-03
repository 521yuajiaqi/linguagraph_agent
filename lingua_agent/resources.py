from __future__ import annotations

from lingua_agent.config import load_terminology


def find_terminology_hits(pair: str, domain: str, source_text: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for row in load_terminology(pair, domain):
        source_term = (row.get("source_term") or "").strip()
        if source_term and source_term in source_text:
            hits.append(row)
    return hits
