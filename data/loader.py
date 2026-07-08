"""
Loads raw claim files and groups them by their natural key.

Book   → {isbn_10: {attr: [(seller, value), ...]}}
Movie  → {(title, year): {attr: [(source, value), ...]}}
Flight → {flight_id: {attr: [(source, value), ...]}}
"""

from collections import defaultdict

FLIGHT_ATTRS = [
    "Scheduled departure",
    "Actual departure",
    "Departure gate",
    "Scheduled arrival",
    "Actual arrival",
    "Arrival gate",
]

BOOK_ATTRS  = ["Author", "Publish date", "Category"]
MOVIE_ATTRS = ["Director", "Genre"]


def load_book_claims(path: str) -> dict:
    # Loads book claims.
    # Returns {isbn_10: {attr: [(seller, value), ...]}}
    result = defaultdict(lambda: defaultdict(list))

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 8:
                continue
            isbn_10, author, seller, publish_date, category = parts[0], parts[2], parts[3], parts[5], parts[7]
            if author and author.lower() not in ("none", ""):
                result[isbn_10]["Author"].append((seller, author))
            if publish_date and publish_date.lower() not in ("none", "", "nan"):
                result[isbn_10]["Publish date"].append((seller, publish_date))
            if category and category.lower() not in ("none", ""):
                result[isbn_10]["Category"].append((seller, category))

    return {isbn: dict(attrs) for isbn, attrs in result.items()}


def load_movie_claims(path: str) -> dict:
    # Loads movie claims.
    # Returns {(title, year): {attr: [(source, value), ...]}}
    result = defaultdict(lambda: defaultdict(list))

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            title, genre, source, year, director = parts[0], parts[1], parts[2], parts[3], parts[4]
            key = (title, year)
            if director and director.lower() not in ("none", ""):
                result[key]["Director"].append((source, director))
            if genre and genre.lower() not in ("none", ""):
                result[key]["Genre"].append((source, genre))

    return {key: dict(attrs) for key, attrs in result.items()}


def load_flight_claims(path: str) -> dict:
    # Loads flight claims. 
    # Returns {flight_id: {attr: [(source, value), ...]}}
    result = defaultdict(lambda: defaultdict(list))

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            source    = parts[0]
            flight_id = parts[1]
            for j, attr in enumerate(FLIGHT_ATTRS):
                col = j + 2
                value = parts[col].strip() if col < len(parts) else ""
                if value:
                    result[flight_id][attr].append((source, value))

    return {fid: dict(attrs) for fid, attrs in result.items()}
