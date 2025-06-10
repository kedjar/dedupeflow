"""Comparator implementations for different data types."""

from dedupeflow.comparators.date import DateComparator
from dedupeflow.comparators.numeric import NumericComparator
from dedupeflow.comparators.string import StringComparator

__all__ = [
    "StringComparator",
    "NumericComparator",
    "DateComparator",
]
