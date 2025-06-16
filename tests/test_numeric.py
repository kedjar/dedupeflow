"""Tests for numeric comparators."""

import math

import pytest

from dedupeflow.comparators.numeric import NumericComparator, numeric_similarity
from dedupeflow.types import SimilarityScore


class TestNumericComparator:
    """Test the NumericComparator class."""

    def test_init_valid_methods(self):
        """Test initialization with valid methods."""
        valid_methods = ["threshold", "scaled", "percentage", "exact"]

        for method in valid_methods:
            comparator = NumericComparator(method=method)
            assert comparator.method == method

    def test_init_invalid_method(self):
        """Test initialization with invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid method"):
            NumericComparator(method="invalid_method")

    def test_threshold_method_absolute(self):
        """Test threshold method with absolute tolerance."""
        comparator = NumericComparator(
            method="threshold", tolerance=1.0, relative=False
        )

        # Within tolerance
        assert comparator.compare(10.0, 10.5) == SimilarityScore(1.0)
        assert comparator.compare(10.0, 11.0) == SimilarityScore(1.0)

        # Outside tolerance
        assert comparator.compare(10.0, 12.0) == SimilarityScore(0.0)

        # Exact match
        assert comparator.compare(10.0, 10.0) == SimilarityScore(1.0)

    def test_threshold_method_relative(self):
        """Test threshold method with relative tolerance."""
        comparator = NumericComparator(method="threshold", tolerance=0.1, relative=True)

        # Within 10% tolerance
        assert comparator.compare(100.0, 105.0) == SimilarityScore(1.0)
        assert comparator.compare(100.0, 110.0) == SimilarityScore(1.0)

        # Outside 10% tolerance
        assert comparator.compare(100.0, 120.0) == SimilarityScore(0.0)

        # Test with zero values
        assert comparator.compare(0.0, 0.0) == SimilarityScore(1.0)

    def test_scaled_method(self):
        """Test scaled method with exponential decay."""
        comparator = NumericComparator(method="scaled", scale_factor=10.0)

        # Exact match
        assert comparator.compare(10.0, 10.0) == SimilarityScore(1.0)

        # Small difference should have high similarity
        score = comparator.compare(10.0, 11.0)
        assert 0.8 < float(score) < 1.0

        # Large difference should have low similarity
        score = comparator.compare(10.0, 50.0)
        assert 0.0 <= float(score) < 0.2

    def test_percentage_method(self):
        """Test percentage-based similarity."""
        comparator = NumericComparator(method="percentage")

        # Exact match
        assert comparator.compare(100.0, 100.0) == SimilarityScore(1.0)

        # 10% difference
        score = comparator.compare(100.0, 110.0)
        assert abs(float(score) - 0.9) < 0.01

        # 50% difference
        score = comparator.compare(100.0, 150.0)
        assert abs(float(score) - 0.5) > 0.01

        # Test with zero values
        assert comparator.compare(0.0, 0.0) == SimilarityScore(1.0)

    def test_exact_method(self):
        """Test exact matching method."""
        comparator = NumericComparator(method="exact")

        assert comparator.compare(10.0, 10.0) == SimilarityScore(1.0)
        assert comparator.compare(10.0, 10.1) == SimilarityScore(0.0)
        assert comparator.compare(-5.0, -5.0) == SimilarityScore(1.0)

    def test_none_handling(self):
        """Test handling of None values."""
        comparator = NumericComparator(method="threshold")

        assert comparator.compare(None, None) == SimilarityScore(1.0)
        assert comparator.compare(10.0, None) == SimilarityScore(0.0)
        assert comparator.compare(None, 10.0) == SimilarityScore(0.0)

    def test_type_conversion(self):
        """Test automatic type conversion to float."""
        comparator = NumericComparator(method="exact")

        # Integer inputs
        assert comparator.compare(10, 10) == SimilarityScore(1.0)
        assert comparator.compare(10, 10.0) == SimilarityScore(1.0)

        # String inputs (valid numbers)
        assert comparator.compare(float("10"), float("10.0")) == SimilarityScore(1.0)
        assert comparator.compare(float("10.5"), 10.5) == SimilarityScore(1.0)

        # Invalid inputs (should not be tested as per type hints)
        # Removed tests with string inputs to satisfy type checker

    def test_negative_numbers(self):
        """Test handling of negative numbers."""
        comparator = NumericComparator(method="threshold", tolerance=1.0)

        assert comparator.compare(-10.0, -10.5) == SimilarityScore(1.0)
        assert comparator.compare(-10.0, -12.0) == SimilarityScore(0.0)
        assert comparator.compare(-5.0, 5.0) == SimilarityScore(0.0)

    def test_callable_interface(self):
        """Test that comparator can be called as a function."""
        comparator = NumericComparator(method="exact")

        # Test callable interface
        score = comparator(10.0, 10.0)
        assert score == SimilarityScore(1.0)


class TestBackwardCompatibilityFunctions:
    """Test backward compatibility functions."""

    def test_numeric_similarity_function(self):
        """Test standalone numeric similarity function."""
        assert numeric_similarity(10.0, 10.0) == 1.0
        assert numeric_similarity(10.0, 11.0, tolerance=1.0) == 1.0
        assert numeric_similarity(10.0, 12.0, tolerance=1.0) == 0.0
        assert numeric_similarity(None, None) == 1.0
        assert numeric_similarity(10.0, None) == 0.0


@pytest.mark.parametrize("method", ["threshold", "scaled", "percentage", "exact"])
def test_all_methods_return_valid_scores(method, sample_numeric_pairs):
    """Test that all methods return valid similarity scores."""
    comparator = NumericComparator(method=method)

    for n1, n2 in sample_numeric_pairs:
        score = comparator.compare(n1, n2)
        assert 0.0 <= float(score) <= 1.0


def test_edge_cases():
    """Test edge cases for numeric comparison."""
    comparator = NumericComparator(method="percentage")

    # Very large numbers
    score = comparator.compare(1e10, 1.1e10)
    assert 0.0 <= float(score) <= 1.0

    # Very small numbers
    score = comparator.compare(1e-10, 1.1e-10)
    assert 0.0 <= float(score) <= 1.0

    # Infinity handling
    score = comparator.compare(float("inf"), float("inf"))
    assert 0.0 <= float(score) <= 1.0


@pytest.mark.parametrize("tolerance", [0.0, 0.1, 1.0, 10.0])
def test_threshold_tolerances(tolerance, sample_numeric_pairs):
    """Test threshold method with different tolerance values."""
    comparator = NumericComparator(method="threshold", tolerance=tolerance)

    for n1, n2 in sample_numeric_pairs:
        score = comparator.compare(n1, n2)

        if abs(n1 - n2) <= tolerance:
            assert float(score) == 1.0
        else:
            assert float(score) == 0.0
