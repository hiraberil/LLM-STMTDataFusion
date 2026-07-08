"""
Parses LLM responses for book and movie into a set of normalized values.
"""

import re

from data.normalizer import normalize


def parse_response(raw: str) -> set:
    # Splits on ";", normalizes each part, and discards empty results.
    parts = raw.split(";")
    result = set()
    for part in parts:
        normalized = normalize(part)
        if normalized:
            result.add(normalized)
    return result


def parse_rw_value(raw: str, label: str) -> str:
    # Pulls one attribute's value out of a "label: <value>" line (prompt_builder.py's
    # RW format, e.g. "Author: ..." or "Attribute 1: ..."). Missing/N-A -> "".
    pattern = re.compile(rf"^{re.escape(label)}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(raw)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if value.upper() == "N/A" else value
