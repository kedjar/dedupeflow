"""Tests for matching strategies."""

import pytest

from dedupeflow.strategies import (
    ExactMatchStrategy,
    FuzzyMatchStrategy,
    ThresholdStrategy,
)
from dedupeflow.types import SimilarityScore


class TestThresholdStrategy:
    """Test ThresholdStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = ThresholdStrategy(threshold=0.8)
        assert strategy.threshold == 0.8

    def test_is_match_above_threshold(self):
        """Test matching above threshold."""
        strategy = ThresholdStrategy(threshold=0.8)
        assert strategy.is_match(SimilarityScore(0.9)) is True
        assert strategy.is_match(SimilarityScore(0.8)) is True

    def test_is_match_below_threshold(self):
        """Test matching below threshold."""
        strategy = ThresholdStrategy(threshold=0.8)
        assert strategy.is_match(SimilarityScore(0.7)) is False
        assert strategy.is_match(SimilarityScore(0.0)) is False


class TestExactMatchStrategy:
    """Test ExactMatchStrategy class."""

    def test_is_match_exact(self):
        """Test exact matching."""
        strategy = ExactMatchStrategy()
        assert strategy.is_match(SimilarityScore(1.0)) is True
        assert strategy.is_match(SimilarityScore(0.99)) is False
        assert strategy.is_match(SimilarityScore(0.0)) is False


class TestFuzzyMatchStrategy:
    """Test FuzzyMatchStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = FuzzyMatchStrategy(
            high_threshold=0.9, medium_threshold=0.7, low_threshold=0.5
        )
        assert strategy.low_threshold == 0.5
        assert strategy.medium_threshold == 0.7
        assert strategy.high_threshold == 0.9

    def test_is_match_in_range(self):
        """Test matching within fuzzy range."""
        strategy = FuzzyMatchStrategy(
            low_threshold=0.5, medium_threshold=0.7, high_threshold=0.9
        )

        assert strategy.is_match(SimilarityScore(0.7)) is True
        assert strategy.is_match(SimilarityScore(0.8)) is True
        assert strategy.is_match(SimilarityScore(0.6)) is False
        assert strategy.is_match(SimilarityScore(0.9)) is True

    def test_is_match_outside_range(self):
        """Test matching outside fuzzy range."""
        strategy = FuzzyMatchStrategy(
            low_threshold=0.5, medium_threshold=0.7, high_threshold=0.9
        )

        assert strategy.is_match(SimilarityScore(0.5)) is False
        assert strategy.is_match(SimilarityScore(0.95)) is True
        assert strategy.is_match(SimilarityScore(1.0)) is True
