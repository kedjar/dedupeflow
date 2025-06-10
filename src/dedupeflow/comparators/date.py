"""Date comparator functions for record linkage."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

from dedupeflow.protocols import BaseComparator
from dedupeflow.types import DateValue, SimilarityScore


class DateComparator(BaseComparator):
    """Advanced date comparator with multiple methods."""

    def __init__(
        self,
        method: str = "exact",
        format_strings: Optional[list[str]] = None,
        tolerance_days: int = 0,
    ):
        """Initialize the date comparator.

        Args:
            method: Comparison method ("exact", "tolerance", "year_only", "month_year")
            format_strings: List of date format strings to try when parsing
            tolerance_days: Number of days tolerance for "tolerance" method
        """
        self.method = method.lower()
        self.format_strings = format_strings
        self.tolerance_days = tolerance_days

        valid_methods = {"exact", "tolerance", "year_only", "month_year"}
        if self.method not in valid_methods:
            raise ValueError(
                f"Invalid method: {method}. Must be one of {valid_methods}"
            )

    def compare(self, a: DateValue, b: DateValue, **kwargs) -> SimilarityScore:
        """Compare two date values."""
        # Handle None values
        if a is None and b is None:
            return SimilarityScore(1.0)
        if a is None or b is None:
            return SimilarityScore(0.0)

        # Parse both dates
        date_a = self._parse_date(a)
        date_b = self._parse_date(b)

        # If either couldn't be parsed, return 0.0
        if date_a is None or date_b is None:
            return SimilarityScore(0.0)

        # Apply the selected method
        method_map = {
            "exact": self._exact_comparison,
            "tolerance": self._tolerance_comparison,
            "year_only": self._year_only_comparison,
            "month_year": self._month_year_comparison,
        }

        return method_map[self.method](date_a, date_b)

    def _parse_date(self, value: Union[str, datetime, date]) -> Optional[date]:
        """Parse a date value into a date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()

        if not isinstance(value, str):
            return None

        # Clean the string
        value = value.strip()
        if not value:
            return None

        # Default format strings to try
        format_strings = self.format_strings or [
            "%Y-%m-%d",  # 2023-01-15
            "%m/%d/%Y",  # 01/15/2023
            "%d/%m/%Y",  # 15/01/2023
            "%Y/%m/%d",  # 2023/01/15
            "%m-%d-%Y",  # 01-15-2023
            "%d-%m-%Y",  # 15-01-2023
            "%Y%m%d",  # 20230115
            "%m/%d/%y",  # 01/15/23
            "%d/%m/%y",  # 15/01/23
            "%b %d, %Y",  # Jan 15, 2023
            "%B %d, %Y",  # January 15, 2023
            "%d %b %Y",  # 15 Jan 2023
            "%d %B %Y",  # 15 January 2023
        ]

        # Try each format string
        for fmt in format_strings:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.date()
            except ValueError:
                continue

        return None

    def _exact_comparison(self, date_a: date, date_b: date) -> SimilarityScore:
        """Exact date comparison."""
        return SimilarityScore(1.0 if date_a == date_b else 0.0)

    def _tolerance_comparison(self, date_a: date, date_b: date) -> SimilarityScore:
        """Date comparison with tolerance in days."""
        diff_days = abs((date_a - date_b).days)
        return SimilarityScore(1.0 if diff_days <= self.tolerance_days else 0.0)

    def _year_only_comparison(self, date_a: date, date_b: date) -> SimilarityScore:
        """Compare only the year component."""
        return SimilarityScore(1.0 if date_a.year == date_b.year else 0.0)

    def _month_year_comparison(self, date_a: date, date_b: date) -> SimilarityScore:
        """Compare year and month components."""
        same_year = date_a.year == date_b.year
        same_month = date_a.month == date_b.month
        return SimilarityScore(1.0 if same_year and same_month else 0.0)


def date_similarity(
    a: Optional[Union[str, datetime, date]],
    b: Optional[Union[str, datetime, date]],
    format_strings: Optional[list[str]] = None,
) -> float:
    """
    Calculate the similarity between two date values.

    Compares dates by parsing string representations or using datetime objects
    directly. Returns 1.0 for identical dates and 0.0 otherwise.

    Args:
        a: First date to compare (string, datetime, or date object).
        b: Second date to compare (string, datetime, or date object).
        format_strings: List of date format strings to try when parsing.
                       Defaults to common formats if None.

    Returns:
        Similarity score of either 0.0 or 1.0.

    Examples:
        >>> date_similarity("2023-01-15", "2023-01-15")
        1.0
        >>> date_similarity("01/15/2023", "2023-01-15")
        1.0
        >>> date_similarity("2023-01-15", "2023-01-16")
        0.0
        >>> date_similarity(None, None)
        1.0
        >>> date_similarity("2023-01-15", None)
        0.0
        >>> from datetime import date
        >>> date_similarity(date(2023, 1, 15), "2023-01-15")
        1.0
    """
    comparator = DateComparator(format_strings=format_strings)
    return float(comparator.compare(a, b))
