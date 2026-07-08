"""
Parses LLM responses for the flight dataset into {attr: normalized_value}.

  - Times  → "HH:MM" (24h)
  - Gates  → uppercase, stripped
  - N/A or empty → omitted
"""

import re
from data.loader import FLIGHT_ATTRS
from .prompt_builder import FLIGHT_LABEL_TO_ATTR

_DATE_ATTRS = {
    "Scheduled departure", "Actual departure",
    "Scheduled arrival",  "Actual arrival",
}
_GATE_ATTRS = {"Departure gate", "Arrival gate"}


_TIME_RE = re.compile(r'\b(\d{1,2}):(\d{2})\s*([aApP]\.?[mM]\.?)?', re.IGNORECASE)
_CONCLUSION_RE = re.compile(
    r"(?:\bis\b|\bare\b|\bagree[sd]?\b|\bwins?\b|:)\s*\"?([^\".\n]+)\"?\.?\s*$",
    re.IGNORECASE,
)


def parse_time(value: str) -> str | None:
    """Converts a time string to HH:MM (24h)."""
    if not value:
        return None
    value = value.strip()
    if value.upper() == "N/A":
        return None

    match = _TIME_RE.search(value)
    if not match:
        return None

    hour   = int(match.group(1))
    minute = int(match.group(2))
    ampm   = match.group(3)

    if ampm:
        ampm_clean = ampm.replace(".", "").upper()
        if ampm_clean == "PM" and hour != 12:
            hour += 12
        elif ampm_clean == "AM" and hour == 12:
            hour = 0

    return f"{hour:02d}:{minute:02d}"


def _normalize_datetime(value: str) -> str | None:
    return parse_time(value)


def _normalize_gate(value: str) -> str | None:
    value = value.strip().upper()
    if not value or value == "N/A":
        return None
    return value


def _extract_label_value(raw: str, label: str) -> str:
    esc = re.escape(label)

    # strict same-line match
    m = re.search(rf"^{esc}\s*:\s*(.+)$", raw, re.IGNORECASE | re.MULTILINE)
    if m:
        value = m.group(1).strip()
        return "" if value.upper() == "N/A" else value

    # relaxed fallback: label optionally wrapped in markdown emphasis (e.g. "**Label:**")
    m = re.search(rf"\**{esc}\**\s*:?", raw, re.IGNORECASE)
    if not m:
        return ""
    start = m.end()
    next_header = re.search(r"\n\s*\**[A-Z][a-z]+ [a-z]+\**\s*:", raw[start:])
    block = raw[start:start + next_header.start()] if next_header else raw[start:]

    arrow = None
    for arrow in re.finditer(r"(?:→|->)\s*(.+)", block):
        pass  
    if arrow:
        return arrow.group(1).strip()

    # split into clauses, dropping trailing ones with no real content
    clauses = [c.strip() for c in re.split(r"[.\n]", block) if c.strip()]
    while clauses and not re.search(r"[A-Za-z0-9]", clauses[-1]):
        clauses.pop()
    last_clause = clauses[-1] if clauses else ""

    cm = _CONCLUSION_RE.search(last_clause)
    if not cm:
        return ""
    return cm.group(1).strip().lstrip(":").strip()


def parse_flight_di_response(raw: str) -> dict:
    result = {}
    for label, attr in FLIGHT_LABEL_TO_ATTR.items():
        value = _extract_label_value(raw, label)
        if not value:
            continue
        normalized = _normalize_datetime(value) if attr in _DATE_ATTRS else _normalize_gate(value)
        if normalized:
            result[attr] = normalized
    return result


def parse_flight_cw_response(raw: str, attr: str) -> str | None:
    value = raw.strip()
    if attr in _DATE_ATTRS:
        return _normalize_datetime(value)
    return _normalize_gate(value)


def parse_flight_response(raw: str) -> dict:
    result = {}
    for attr in FLIGHT_ATTRS:
        value = _extract_label_value(raw, attr)
        if not value:
            continue
        normalized = _normalize_datetime(value) if attr in _DATE_ATTRS else _normalize_gate(value)
        if normalized:
            result[attr] = normalized
    return result
