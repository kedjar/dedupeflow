"""Matching and blocking strategies."""

from dedupeflow.strategies.matching import (
    ExactMatchStrategy,
    FuzzyMatchStrategy,
    ThresholdStrategy,
)

__all__ = [
    "ExactMatchStrategy",
    "FuzzyMatchStrategy",
    "ThresholdStrategy",
]
