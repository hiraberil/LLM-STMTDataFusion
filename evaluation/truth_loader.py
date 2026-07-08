"""
Loads ground truth files for each dataset.

Book   → {isbn_10: set of normalized authors}
Movie  → {(title, year): set of normalized directors}
Flight → {flight_id: {attr: value}}
"""

from data.normalizer import normalize, normalize_set
from data.loader import FLIGHT_ATTRS


def load_book_truth(path: str) -> dict:
    # Loads book ground truth. 
    # Returns {isbn_10: set of normalized authors}.
    truth = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            isbn_10, authors_raw = parts[0], parts[1]
            normalized = normalize_set(authors_raw.split(";"))
            if normalized:
                truth[isbn_10] = normalized
    return truth


def load_movie_truth(path: str) -> dict:
    # Loads movie ground truth. 
    # Returns {(title, year): set of normalized directors}.
    truth = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            title, year, directors_raw = parts[0], parts[1], parts[2]
            key = (title, year)
            normalized = normalize_set(directors_raw.split(";"))
            if normalized:
                truth[key] = normalized
    return truth


def load_flight_truth(path: str) -> dict:
    # Loads flight ground truth. 
    # Returns {flight_id: {attr: value}}.
    truth = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            flight_id = parts[0]
            attrs = {}
            for j, attr in enumerate(FLIGHT_ATTRS):
                col = j + 1
                value = parts[col].strip() if col < len(parts) else ""
                if value:
                    attrs[attr] = value
            if attrs:
                truth[flight_id] = attrs
    return truth
