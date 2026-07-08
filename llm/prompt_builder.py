"""
Prompt builder taxonomy:

    <DD|DI>-<RW|CW>-<ST|MT>-<0shot|1shot>

  DD/DI : Domain-Dependent (real attribute names) vs Domain-Independent ("Attribute N")
  RW/CW : Row-Wise   — one prompt resolves every attribute of the entity at once
          Column-Wise — one prompt resolves a single attribute at a time
  ST/MT : Single-Truth — prompt assumes one correct value per attribute
          Multi-Truth  — prompt allows several correct values (semicolon-separated)

Set config.PROMPT_DOMAIN to one of:
  dd_rw_st, dd_rw_mt, dd_cw_st, dd_cw_mt,
  di_rw_st, di_rw_mt, di_cw_st, di_cw_mt
and config.PROMPT_SHOT to 0 or 1.

Use build_book_prompt_rw / build_movie_prompt_rw / build_flight_prompt_rw for RW mode (all attributes resolved in one prompt). 
Use build_book_prompt_cw / build_movie_prompt_cw / build_flight_prompt_cw for CW mode (one prompt per attribute).
"""

import config
from data.loader import FLIGHT_ATTRS, BOOK_ATTRS, MOVIE_ATTRS

_VALID_DOMAINS = {
    "dd_rw_st", "dd_rw_mt", "dd_cw_st", "dd_cw_mt",
    "di_rw_st", "di_rw_mt", "di_cw_st", "di_cw_mt",
}

# attribute -> generic "Attribute N" label
_FLIGHT_LABELS = {attr: f"Attribute {i+1}" for i, attr in enumerate(FLIGHT_ATTRS)}
FLIGHT_LABEL_TO_ATTR = {v: k for k, v in _FLIGHT_LABELS.items()}

_BOOK_LABELS  = {attr: f"Attribute {i+1}" for i, attr in enumerate(BOOK_ATTRS)}
_MOVIE_LABELS = {attr: f"Attribute {i+1}" for i, attr in enumerate(MOVIE_ATTRS)}

# CW phrasing for the two attributes with prior, slide-verified wording ("authors" /
# "directors"); new attributes fall back to their raw name (e.g. "Publish date").
_BOOK_CW_WORD  = {"Author": "authors"}
_MOVIE_CW_WORD = {"Director": "directors"}


def _shot() -> int:
    return getattr(config, "PROMPT_SHOT", 0)


def _mode():
    domain = getattr(config, "PROMPT_DOMAIN", "dd_cw_mt")
    if domain not in _VALID_DOMAINS:
        raise ValueError(f"Unknown PROMPT_DOMAIN: {domain} (expected one of {sorted(_VALID_DOMAINS)})")
    dd_or_di, layout, truth = domain.split("_")
    return dd_or_di, layout, truth  # ("dd"|"di", "rw"|"cw", "st"|"mt")


# ─────────────────────────────────────────────────────────────────────────────
# 1-shot examples
# ─────────────────────────────────────────────────────────────────────────────

_BOOK_RW_EXAMPLE = """\
[EXAMPLE]
Book: 012345678X
Multiple sources report the following data:

Author:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

Publish date:
  - source_A: "1984"
  - source_B: "1983"

Category:
  - source_A: "book_detail_fiction_horror_books"
  - source_B: "book_detail_fiction_fantasy_science_fiction"

What is the correct value for each attribute?
Reply ONLY in this exact format (use N/A if unknown):
Author: Stephen King; Peter Straub
Publish date: 1984
Category: book_detail_fiction_horror_books
[/EXAMPLE]

"""

_MOVIE_RW_EXAMPLE = """\
[EXAMPLE]
Movie: "The Godfather" (1972)
Multiple sources report the following data:

Director:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

Genre:
  - source_A: "crime"
  - source_B: "drama"

What is the correct value for each attribute?
Reply ONLY in this exact format (use N/A if unknown):
Director: Francis Ford Coppola
Genre: crime
[/EXAMPLE]

"""

_FLIGHT_DD_RW_EXAMPLE = """\
[EXAMPLE]
Flight: AA-1234-JFK-LAX
Multiple sources report the following data:

Scheduled departure:
  - aa: "12/01/2011 08:00 AM"
  - flightaware: "2011-12-01 08:00AM EST"

Actual departure:
  - aa: "12/01/2011 08:15 AM"
  - flightaware: "2011-12-01 08:15AM EST"

Departure gate:
  - aa: "B12"
  - flightaware: " B12 "

Scheduled arrival:
  - aa: "12/01/2011 11:30 AM"
  - flightaware: "2011-12-01 11:30AM EST"

Actual arrival:
  - aa: "12/01/2011 11:45 AM"
  - flightaware: "2011-12-01 11:45AM EST"

Arrival gate:
  - aa: "C5"
  - flightaware: " C5 "

Scheduled departure: 12/01/2011 08:00 AM
Actual departure: 12/01/2011 08:15 AM
Departure gate: B12
Scheduled arrival: 12/01/2011 11:30 AM
Actual arrival: 12/01/2011 11:45 AM
Arrival gate: C5
[/EXAMPLE]

"""

_BOOK_DI_RW_EXAMPLE = """\
[EXAMPLE]
Entity: 012345678X
Multiple sources report the following data:

Attribute 1:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

Attribute 2:
  - source_A: "1984"
  - source_B: "1983"

Attribute 3:
  - source_A: "book_detail_fiction_horror_books"
  - source_B: "book_detail_fiction_fantasy_science_fiction"

What is the correct value for each attribute?
Reply ONLY in this exact format (use N/A if unknown):
Attribute 1: Stephen King; Peter Straub
Attribute 2: 1984
Attribute 3: book_detail_fiction_horror_books
[/EXAMPLE]

"""

_MOVIE_DI_RW_EXAMPLE = """\
[EXAMPLE]
Entity: The Godfather (1972)
Multiple sources report the following data:

Attribute 1:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

Attribute 2:
  - source_A: "crime"
  - source_B: "drama"

What is the correct value for each attribute?
Reply ONLY in this exact format (use N/A if unknown):
Attribute 1: Francis Ford Coppola
Attribute 2: crime
[/EXAMPLE]

"""
_FLIGHT_DI_RW_EXAMPLE = """\
[EXAMPLE]
Entity: AA-1234-JFK-LAX
Multiple sources report the following data:

Attribute 1:
  - source_A: "12/01/2011 08:00 AM"
  - source_B: "2011-12-01 08:00AM EST"

Attribute 2:
  - source_A: "12/01/2011 08:15 AM"
  - source_B: "2011-12-01 08:15AM EST"

Attribute 3:
  - source_A: "B12"
  - source_B: " B12 "

Attribute 4:
  - source_A: "12/01/2011 11:30 AM"
  - source_B: "2011-12-01 11:30AM EST"

Attribute 5:
  - source_A: "12/01/2011 11:45 AM"
  - source_B: "2011-12-01 11:45AM EST"

Attribute 6:
  - source_A: "C5"
  - source_B: " C5 "

Attribute 1: 12/01/2011 08:00 AM
Attribute 2: 12/01/2011 08:15 AM
Attribute 3: B12
Attribute 4: 12/01/2011 11:30 AM
Attribute 5: 12/01/2011 11:45 AM
Attribute 6: C5
[/EXAMPLE]

"""

_BOOK_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Book: 012345678X
Multiple sources report the following authors:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

What is the correct value for authors?
Reply ONLY with the value for the authors attribute.

Answer: Stephen King; Peter Straub
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Book: 012345678X
Multiple sources report the following authors:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

What is the correct value for authors?
If there are multiple authors, separate them with a semicolon (;)
Reply ONLY with the value for the authors attribute.

Answer: Stephen King; Peter Straub
[/EXAMPLE]

""",
}

_MOVIE_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Movie: "The Godfather" (1972)
Multiple sources report the following directors:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

What is the correct value for directors?
Reply ONLY with the value for the directors attribute.

Answer: Francis Ford Coppola
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Movie: "The Godfather" (1972)
Multiple sources report the following directors:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

What is the correct value for directors?
If there are multiple directors, separate them with a semicolon (;)
Reply ONLY with the value for the directors attribute.

Answer: Francis Ford Coppola
[/EXAMPLE]

""",
}
_FLIGHT_DD_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Flight ID: AA-1234-JFK-LAX
Multiple sources report the following Departure gate:
  - aa: "B12"
  - flightaware: " B12 "

What is the correct value for Departure gate?
Reply ONLY with the value for the Departure gate attribute.

Answer: B12
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Flight ID: AA-1234-JFK-LAX
Multiple sources report the following Departure gate:
  - aa: "B12"
  - flightaware: " B12 "

What is the correct value for Departure gate?
If there are multiple Departure gate, separate them with a semicolon (;)
Reply ONLY with the value for the Departure gate attribute.

Answer: B12
[/EXAMPLE]

""",
}

_BOOK_DI_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Entity: 012345678X
Multiple sources report the following values for the same attribute:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

What is the correct value for this attribute?
Reply with ONLY the value for the attribute, nothing else.

Answer: Stephen King; Peter Straub
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Entity: 012345678X
Multiple sources report the following values for the same attribute:
  - source_A: "STEPHEN KING; PETER STRAUB"
  - source_B: "King, Stephen"

What is the correct value for this attribute?
If there are multiple values, separate them with a semicolon (;)
Reply with ONLY the value for the attribute, nothing else.

Answer: Stephen King; Peter Straub
[/EXAMPLE]

""",
}

_MOVIE_DI_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Entity: The Godfather (1972)
Multiple sources report the following values for the same attribute:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

What is the correct value for this attribute?
Reply with ONLY the value for the attribute, nothing else.

Answer: Francis Ford Coppola
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Entity: The Godfather (1972)
Multiple sources report the following values for the same attribute:
  - source_A: "FRANCIS FORD COPPOLA"
  - source_B: "Coppola, Francis Ford"

What is the correct value for this attribute?
If there are multiple values, separate them with a semicolon (;)
Reply with ONLY the value for the attribute, nothing else.

Answer: Francis Ford Coppola
[/EXAMPLE]

""",
}

_FLIGHT_DI_CW_EXAMPLE = {
    "st": """\
[EXAMPLE]
Entity: AA-1234-JFK-LAX
Multiple sources report the following values for the same attribute:
  - aa: "B12"
  - flightaware: " B12 "

What is the correct value for this attribute?
Reply with ONLY the value for the attribute, nothing else.

Answer: B12
[/EXAMPLE]

""",
    "mt": """\
[EXAMPLE]
Entity: AA-1234-JFK-LAX
Multiple sources report the following values for the same attribute:
  - aa: "B12"
  - flightaware: " B12 "

What is the correct value for this attribute?
If there are multiple values, separate them with a semicolon (;)
Reply with ONLY the value for the attribute, nothing else.

Answer: B12
[/EXAMPLE]

""",
}

# ─────────────────────────────────────────────────────────────────────────────
# Every prompt is assembled from up to 4 blocks: 
#   - [EXAMPLE] (1-shot only), 
#   - BODY (entity + source data), 
#   - QUESTION, 
#   - FORMAT. 
# Blocks are separate functions
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Generic RW (Row-Wise) builder — one prompt, every attribute of the entity
# ─────────────────────────────────────────────────────────────────────────────

def _rw_body_dd(entity_line: str, attrs: dict) -> list:
    """DD body: real attribute names used directly as labels."""
    lines = [entity_line, "Multiple sources report the following data:", ""]
    for attr, sources in attrs.items():
        lines.append(f"{attr}:")
        for source, value in sources:
            lines.append(f'  - {source}: "{value}"')
        if not sources:
            lines.append("  (no data)")
        lines.append("")
    return lines


def _rw_body_di(entity_line: str, attrs: dict, labels: dict) -> list:
    """DI body: generic 'Attribute N' labels supplied by the caller."""
    lines = [entity_line, "Multiple sources report the following data:", ""]
    for attr, sources in attrs.items():
        lines.append(f"{labels[attr]}:")
        for source, value in sources:
            lines.append(f'  - {source}: "{value}"')
        if not sources:
            lines.append("  (no data)")
        lines.append("")
    return lines


def _rw_question() -> list:
    return ["What is the correct value for each attribute?"]


def _mt_note(subject: str, truth: str) -> list:
    if truth != "mt":
        return []
    return [f"If there are multiple {subject}, separate them with a semicolon (;)"]


def _rw_format_dd(attrs: dict, truth: str, multi_attr_label: str | None) -> list:
    """DD format: names the specific multi-valued attribute (e.g. 'authors'), if any."""
    subject = multi_attr_label if multi_attr_label else "values for any attribute"
    lines = _mt_note(subject, truth)
    lines.append("Reply ONLY in this exact format (use N/A if unknown):")
    for attr in attrs:
        lines.append(f"{attr}: <value>")
    return lines


def _rw_format_di(attrs: dict, labels: dict, truth: str) -> list:
    """DI format: always the generic subject — no attribute is ever named."""
    lines = _mt_note("values for any attribute", truth)
    lines.append("Reply ONLY in this exact format (use N/A if unknown):")
    for attr in attrs:
        lines.append(f"{labels[attr]}: <value>")
    return lines


def _rw_prompt_dd(entity_line: str, attrs: dict, truth: str,
                   multi_attr_label: str | None, example: str) -> str:
    blocks = []
    if _shot() == 1:
        blocks.append(example)
    blocks.append("\n".join(_rw_body_dd(entity_line, attrs)))
    blocks.append("\n".join(_rw_question()))
    blocks.append("\n".join(_rw_format_dd(attrs, truth, multi_attr_label)))
    return "\n".join(blocks)


def _rw_prompt_di(entity_line: str, attrs: dict, labels: dict, truth: str, example: str) -> str:
    blocks = []
    if _shot() == 1:
        blocks.append(example)
    blocks.append("\n".join(_rw_body_di(entity_line, attrs, labels)))
    blocks.append("\n".join(_rw_question()))
    blocks.append("\n".join(_rw_format_di(attrs, labels, truth)))
    return "\n".join(blocks)


# ─────────────────────────────────────────────────────────────────────────────
# Generic CW (Column-Wise) builder — one prompt, a single attribute
# ─────────────────────────────────────────────────────────────────────────────

def _cw_dd_body(entity_line: str, attr_word: str, sources: list) -> list:
    lines = [entity_line, f"Multiple sources report the following {attr_word}:"]
    for source, value in sources:
        lines.append(f'  - {source}: "{value}"')
    lines.append("")
    return lines


def _cw_dd_question(attr_word: str) -> list:
    return [f"What is the correct value for {attr_word}?"]


def _cw_dd_format(attr_word: str, truth: str) -> list:
    lines = _mt_note(attr_word, truth)
    lines.append(f"Reply ONLY with the value for the {attr_word} attribute.")
    return lines


def _cw_prompt_dd(entity_line: str, attr_word: str, sources: list, truth: str, example: str) -> str:
    blocks = []
    if _shot() == 1:
        blocks.append(example)
    blocks.append("\n".join(_cw_dd_body(entity_line, attr_word, sources)))
    blocks.append("\n".join(_cw_dd_question(attr_word)))
    blocks.append("\n".join(_cw_dd_format(attr_word, truth)))
    return "\n".join(blocks)


def _cw_di_body(entity_line: str, sources: list) -> list:
    lines = [entity_line, "Multiple sources report the following values for the same attribute:"]
    for source, value in sources:
        lines.append(f'  - {source}: "{value}"')
    lines.append("")
    return lines


def _cw_di_question() -> list:
    return ["What is the correct value for this attribute?"]


def _cw_di_format(truth: str) -> list:
    if truth == "mt":
        return [
            "If there are multiple values, separate them with a semicolon (;)",
            "Reply with ONLY the value for the attribute, nothing else.",
        ]
    return ["Reply with ONLY the value for the attribute, nothing else."]


def _cw_prompt_di(entity_line: str, sources: list, truth: str, example: str) -> str:
    blocks = []
    if _shot() == 1:
        blocks.append(example)
    blocks.append("\n".join(_cw_di_body(entity_line, sources)))
    blocks.append("\n".join(_cw_di_question()))
    blocks.append("\n".join(_cw_di_format(truth)))
    return "\n".join(blocks)


# ─────────────────────────────────────────────────────────────────────────────
# Book
# ─────────────────────────────────────────────────────────────────────────────

def build_book_prompt_rw(isbn: str, claims_by_attr: dict) -> str:
    """RW — resolves all BOOK_ATTRS (Author, Publish date, Category) in one prompt."""
    dd_or_di, layout, truth = _mode()
    if layout != "rw":
        raise ValueError("build_book_prompt_rw is RW-only; use build_book_prompt_cw for CW")
    attrs = {attr: claims_by_attr.get(attr, []) for attr in BOOK_ATTRS}
    if dd_or_di == "dd":
        return _rw_prompt_dd(f"Book: {isbn}", attrs, truth, "authors", _BOOK_RW_EXAMPLE)
    return _rw_prompt_di(f"Entity: {isbn}", attrs, _BOOK_LABELS, truth, _BOOK_DI_RW_EXAMPLE)


def build_book_prompt_cw(isbn: str, attr: str, sources: list) -> str:
    """CW — resolves a single BOOK_ATTRS attribute for one book."""
    dd_or_di, layout, truth = _mode()
    if layout != "cw":
        raise ValueError("build_book_prompt_cw is CW-only; use build_book_prompt_rw for RW")
    if dd_or_di == "dd":
        attr_word = _BOOK_CW_WORD.get(attr, attr)
        return _cw_prompt_dd(f"Book: {isbn}", attr_word, sources, truth, _BOOK_CW_EXAMPLE[truth])
    return _cw_prompt_di(f"Entity: {isbn}", sources, truth, _BOOK_DI_CW_EXAMPLE[truth])


# ─────────────────────────────────────────────────────────────────────────────
# Movie
# ─────────────────────────────────────────────────────────────────────────────

def build_movie_prompt_rw(title: str, year: str, claims_by_attr: dict) -> str:
    """RW — resolves all MOVIE_ATTRS (Director, Genre) in one prompt."""
    dd_or_di, layout, truth = _mode()
    if layout != "rw":
        raise ValueError("build_movie_prompt_rw is RW-only; use build_movie_prompt_cw for CW")
    attrs = {attr: claims_by_attr.get(attr, []) for attr in MOVIE_ATTRS}
    if dd_or_di == "dd":
        return _rw_prompt_dd(f'Movie: "{title}" ({year})', attrs, truth, "directors", _MOVIE_RW_EXAMPLE)
    entity_id = f"{title} ({year})"
    return _rw_prompt_di(f"Entity: {entity_id}", attrs, _MOVIE_LABELS, truth, _MOVIE_DI_RW_EXAMPLE)


def build_movie_prompt_cw(title: str, year: str, attr: str, sources: list) -> str:
    """CW — resolves a single MOVIE_ATTRS attribute for one movie."""
    dd_or_di, layout, truth = _mode()
    if layout != "cw":
        raise ValueError("build_movie_prompt_cw is CW-only; use build_movie_prompt_rw for RW")
    if dd_or_di == "dd":
        attr_word = _MOVIE_CW_WORD.get(attr, attr)
        return _cw_prompt_dd(f'Movie: "{title}" ({year})', attr_word, sources, truth, _MOVIE_CW_EXAMPLE[truth])
    entity_id = f"{title} ({year})"
    return _cw_prompt_di(f"Entity: {entity_id}", sources, truth, _MOVIE_DI_CW_EXAMPLE[truth])


# ─────────────────────────────────────────────────────────────────────────────
# Flight
# ─────────────────────────────────────────────────────────────────────────────

def build_flight_prompt_rw(flight_id: str, claims_by_attr: dict) -> str:
    """RW — resolves all FLIGHT_ATTRS for one flight in a single prompt."""
    dd_or_di, layout, truth = _mode()
    if layout != "rw":
        raise ValueError("build_flight_prompt_rw is RW-only; use build_flight_prompt_cw for CW")
    attrs = {attr: claims_by_attr.get(attr, []) for attr in FLIGHT_ATTRS}
    if dd_or_di == "dd":
        return _rw_prompt_dd(f"Flight ID: {flight_id}", attrs, truth, None, _FLIGHT_DD_RW_EXAMPLE)
    return _rw_prompt_di(f"Entity: {flight_id}", attrs, _FLIGHT_LABELS, truth, _FLIGHT_DI_RW_EXAMPLE)


def build_flight_prompt_cw(flight_id: str, attr: str, sources: list) -> str:
    """CW — resolves a single FLIGHT_ATTRS attribute for one flight."""
    dd_or_di, layout, truth = _mode()
    if layout != "cw":
        raise ValueError("build_flight_prompt_cw is CW-only; use build_flight_prompt_rw for RW")
    if dd_or_di == "dd":
        return _cw_prompt_dd(f"Flight ID: {flight_id}", attr, sources, truth, _FLIGHT_DD_CW_EXAMPLE[truth])
    return _cw_prompt_di(f"Entity: {flight_id}", sources, truth, _FLIGHT_DI_CW_EXAMPLE[truth])
