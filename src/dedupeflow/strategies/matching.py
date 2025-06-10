"""Matching strategies for determining if records match."""

from __future__ import annotations

from dedupeflow.protocols import BaseMatchStrategy
from dedupeflow.types import SimilarityScore


class ThresholdStrategy(BaseMatchStrategy):
    """Simple threshold-based matching strategy."""

    def __init__(self, threshold: float = 0.8):
        """Initialize with a similarity threshold.

        Args:
            threshold: Minimum similarity score for a match (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.threshold = threshold

    def is_match(self, score: SimilarityScore, **kwargs) -> bool:
        """Determine if score meets the threshold."""
        return float(score) >= self.threshold


class ExactMatchStrategy(BaseMatchStrategy):
    """Strategy requiring perfect similarity scores."""

    def is_match(self, score: SimilarityScore, **kwargs) -> bool:
        """Require exact match (score = 1.0)."""
        return float(score) == 1.0


class FuzzyMatchStrategy(BaseMatchStrategy):
    """Multi-tier fuzzy matching strategy."""

    def __init__(
        self,
        high_threshold: float = 0.9,
        medium_threshold: float = 0.7,
        low_threshold: float = 0.5,
    ):
        """Initialize with multiple thresholds.

        Args:
            high_threshold: Threshold for high-confidence matches
            medium_threshold: Threshold for medium-confidence matches
            low_threshold: Minimum threshold for any match
        """
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold

    def is_match(
        self, score: SimilarityScore, confidence_level: str = "medium", **kwargs
    ) -> bool:
        """Determine match based on confidence level."""
        score_val = float(score)

        thresholds = {
            "high": self.high_threshold,
            "medium": self.medium_threshold,
            "low": self.low_threshold,
        }

        threshold = thresholds.get(confidence_level, self.medium_threshold)
        return score_val >= threshold
