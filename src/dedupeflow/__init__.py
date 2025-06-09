"""Record linkage package for efficient entity resolution."""

__version__ = "0.1.0"

from .comparators.string import levenshtein_similarity, jaro_winkler_similarity
from .comparators.numeric import numeric_similarity
from .comparators.date import date_similarity

__all__ = [
    "levenshtein_similarity",
    "jaro_winkler_similarity", 
    "numeric_similarity",
    "date_similarity",
]