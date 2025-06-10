"""Protocol definitions for DedupeFlow components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from dedupeflow.types import SimilarityScore


@runtime_checkable
class Comparator(Protocol):
    """Protocol for similarity comparators."""

    def compare(self, a: Any, b: Any, **kwargs: Any) -> SimilarityScore:
        """Compare two values and return a similarity score."""
        ...


@runtime_checkable
class MatchStrategy(Protocol):
    """Protocol for matching strategies."""

    def is_match(self, score: SimilarityScore, **kwargs: Any) -> bool:
        """Determine if a similarity score constitutes a match."""
        ...


class BaseComparator(ABC):
    """Abstract base class for all comparators."""

    @abstractmethod
    def compare(self, a: Any, b: Any, **kwargs: Any) -> SimilarityScore:
        """Compare two values and return a similarity score.

        Args:
            a: First value to compare
            b: Second value to compare
            **kwargs: Additional comparison parameters

        Returns:
            SimilarityScore between 0.0 and 1.0
        """
        pass

    def __call__(self, a: Any, b: Any, **kwargs: Any) -> SimilarityScore:
        """Allow comparator to be called as a function."""
        return self.compare(a, b, **kwargs)


class BaseMatchStrategy(ABC):
    """Abstract base class for matching strategies."""

    @abstractmethod
    def is_match(self, score: SimilarityScore, **kwargs: Any) -> bool:
        """Determine if a similarity score constitutes a match.

        Args:
            score: Similarity score to evaluate
            **kwargs: Additional strategy parameters

        Returns:
            True if the score constitutes a match, False otherwise
        """
        pass
