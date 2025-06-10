"""Tests for date comparators."""

from datetime import date, datetime

import pytest

from dedupeflow.comparators.date import DateComparator, date_similarity
from dedupeflow.types import SimilarityScore


class TestDateComparator:
    """Test the DateComparator class."""

    def test_init_valid_methods(self):
        """Test initialization with valid methods."""
        valid_methods = ["exact", "tolerance", "year_only", "month_year"]

        for method in valid_methods:
            comparator = DateComparator(method=method)
            assert comparator.method == method

    def test_init_invalid_method(self):
        """Test initialization with invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid method"):
            DateComparator(method="invalid_method")

    def test_exact_method(self):
        """Test exact date comparison."""
        comparator = DateComparator(method="exact")

        # Same dates
        assert comparator.compare("2023-01-01", "2023-01-01") == SimilarityScore(1.0)
        assert comparator.compare(
            date(2023, 1, 1), date(2023, 1, 1)
        ) == SimilarityScore(1.0)

        # Different dates
        assert comparator.compare("2023-01-01", "2023-01-02") == SimilarityScore(0.0)
        assert comparator.compare(
            date(2023, 1, 1), date(2023, 1, 2)
        ) == SimilarityScore(0.0)

    def test_tolerance_method(self):
        """Test date comparison with tolerance."""
        comparator = DateComparator(method="tolerance", tolerance_days=1)

        # Within tolerance
        assert comparator.compare("2023-01-01", "2023-01-01") == SimilarityScore(1.0)
        assert comparator.compare("2023-01-01", "2023-01-02") == SimilarityScore(1.0)

        # Outside tolerance
        assert comparator.compare("2023-01-01", "2023-01-03") == SimilarityScore(0.0)

        # Test with larger tolerance
        comparator_7days = DateComparator(method="tolerance", tolerance_days=7)
        assert comparator_7days.compare("2023-01-01", "2023-01-07") == SimilarityScore(
            1.0
        )
        assert comparator_7days.compare("2023-01-01", "2023-01-08") == SimilarityScore(
            1.0
        )
        assert comparator_7days.compare("2023-01-01", "2023-01-09") == SimilarityScore(
            0.0
        )

    def test_year_only_method(self):
        """Test year-only comparison."""
        comparator = DateComparator(method="year_only")

        # Same year
        assert comparator.compare("2023-01-01", "2023-12-31") == SimilarityScore(1.0)
        assert comparator.compare("2023-06-15", "2023-02-28") == SimilarityScore(1.0)

        # Different years
        assert comparator.compare("2023-01-01", "2024-01-01") == SimilarityScore(0.0)
        assert comparator.compare("2022-12-31", "2023-01-01") == SimilarityScore(0.0)

    def test_month_year_method(self):
        """Test month and year comparison."""
        comparator = DateComparator(method="month_year")

        # Same month and year
        assert comparator.compare("2023-01-01", "2023-01-31") == SimilarityScore(1.0)
        assert comparator.compare("2023-06-15", "2023-06-01") == SimilarityScore(1.0)

        # Different month, same year
        assert comparator.compare("2023-01-01", "2023-02-01") == SimilarityScore(0.0)

        # Same month, different year
        assert comparator.compare("2023-01-01", "2024-01-01") == SimilarityScore(0.0)

    def test_date_parsing(self):
        """Test parsing of various date formats."""
        comparator = DateComparator(method="exact")

        # Standard formats should work
        assert comparator.compare("2023-01-01", "01/01/2023") == SimilarityScore(1.0)
        assert comparator.compare("2023-01-01", "01-01-2023") == SimilarityScore(1.0)
        assert comparator.compare("2023-01-01", "20230101") == SimilarityScore(1.0)

        # Named month formats
        assert comparator.compare("2023-01-01", "Jan 1, 2023") == SimilarityScore(1.0)
        assert comparator.compare("2023-01-01", "January 1, 2023") == SimilarityScore(
            1.0
        )

    def test_mixed_types(self):
        """Test comparison of mixed date types."""
        comparator = DateComparator(method="exact")

        # String vs date object
        assert comparator.compare("2023-01-01", date(2023, 1, 1)) == SimilarityScore(
            1.0
        )

        # String vs datetime object
        assert comparator.compare(
            "2023-01-01", datetime(2023, 1, 1, 12, 0, 0)
        ) == SimilarityScore(1.0)

        # Date vs datetime object
        assert comparator.compare(
            date(2023, 1, 1), datetime(2023, 1, 1, 12, 0, 0)
        ) == SimilarityScore(1.0)

    def test_none_handling(self):
        """Test handling of None values."""
        comparator = DateComparator(method="exact")

        assert comparator.compare(None, None) == SimilarityScore(1.0)
        assert comparator.compare("2023-01-01", None) == SimilarityScore(0.0)
        assert comparator.compare(None, "2023-01-01") == SimilarityScore(0.0)

    def test_invalid_date_handling(self):
        """Test handling of invalid date strings."""
        comparator = DateComparator(method="exact")

        # Invalid date strings should return 0.0
        assert comparator.compare("not-a-date", "2023-01-01") == SimilarityScore(0.0)
        assert comparator.compare("2023-01-01", "invalid-date") == SimilarityScore(0.0)
        assert comparator.compare("not-a-date", "also-invalid") == SimilarityScore(0.0)

        # Empty strings
        assert comparator.compare("", "2023-01-01") == SimilarityScore(0.0)
        assert comparator.compare("2023-01-01", "") == SimilarityScore(0.0)
        assert comparator.compare("", "") == SimilarityScore(0.0)

    def test_custom_format_strings(self):
        """Test custom format strings."""
        custom_formats = ["%d-%m-%Y", "%Y%m%d"]
        comparator = DateComparator(method="exact", format_strings=custom_formats)

        # Should parse custom formats
        assert comparator.compare("01-01-2023", "20230101") == SimilarityScore(1.0)

    def test_callable_interface(self):
        """Test that comparator can be called as a function."""
        comparator = DateComparator(method="exact")

        # Test callable interface
        score = comparator("2023-01-01", "2023-01-01")
        assert score == SimilarityScore(1.0)


class TestBackwardCompatibilityFunctions:
    """Test backward compatibility functions."""

    def test_date_similarity_function(self):
        """Test standalone date similarity function."""
        assert date_similarity("2023-01-01", "2023-01-01") == 1.0
        assert date_similarity("2023-01-01", "2023-01-02") == 0.0
        assert date_similarity(None, None) == 1.0
        assert date_similarity("2023-01-01", None) == 0.0


@pytest.mark.parametrize("method", ["exact", "tolerance", "year_only", "month_year"])
def test_all_methods_return_valid_scores(method, sample_date_pairs):
    """Test that all methods return valid similarity scores."""
    if method == "tolerance":
        comparator = DateComparator(method=method, tolerance_days=7)
    else:
        comparator = DateComparator(method=method)

    for d1, d2 in sample_date_pairs:
        score = comparator.compare(d1, d2)
        assert isinstance(score, SimilarityScore)
        assert 0.0 <= float(score) <= 1.0


def test_edge_cases():
    """Test edge cases for date comparison."""
    comparator = DateComparator(method="exact")

    # Leap year dates
    score = comparator.compare("2020-02-29", "2020-02-29")
    assert float(score) == 1.0

    # Different century dates
    score = comparator.compare("1999-12-31", "2000-01-01")
    assert float(score) == 0.0

    # Very old dates
    score = comparator.compare("1900-01-01", "1900-01-01")
    assert float(score) == 1.0


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("2023-01-01", "2023-01-01", 1.0),
        ("2023-01-01", "2023-01-02", 0.0),
        ("01/01/2023", "2023-01-01", 1.0),
        ("Jan 1, 2023", "January 1, 2023", 1.0),
        (None, None, 1.0),
        ("2023-01-01", None, 0.0),
    ],
)
def test_date_similarity_parametrized(a, b, expected):
    """Parametrized test for date similarity function."""
    assert date_similarity(a, b) == expected
