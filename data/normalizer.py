# Text normalization utilities for book and movie claim values.

import re
import unicodedata


_SPECIAL = {'ø': 'o', 'ð': 'd', 'æ': 'ae', 'þ': 'th', 'ł': 'l', 'ß': 'ss'}

_TITLES = re.compile(
    r'\b(sir|dame|dr|prof|professor|general|gen|colonel|col|captain|capt|'
    r'mr|mrs|ms|miss|rev|lord|lady|baron|count)\b\.?',
    re.IGNORECASE
)


# Normalizes a string: NFKD decomposition, lowercase, special char mapping, title removal, punctuation to spaces.
def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = ''.join(_SPECIAL.get(c, c) for c in text)
    text = _TITLES.sub('', text)
    text = text.replace(".", " ").replace("-", " ").replace(",", " ")
    text = text.lower().strip()
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def normalize_set(values) -> set:
    # Normalizes all values in a collection, discarding empty results.
    return {normalize(v) for v in values if v and v.strip() and normalize(v)}
