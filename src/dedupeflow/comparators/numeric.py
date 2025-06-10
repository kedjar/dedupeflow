"""Enhanced numeric comparators with multiple strategies."""

from __future__ import annotations

import math
from typing import Optional, Union

from dedupeflow.protocols import BaseComparator
from dedupeflow.types import NumericValue, SimilarityScore


class NumericComparator(BaseComparator):
    """Advanced numeric comparator with multiple similarity methods."""

    def __init__(
        self,
        method: str = "threshold",
        tolerance: float = 0.0,
        relative: bool = False,
        scale_factor: Optional[float] = None,
    ):
        """Initialize the numeric comparator.

        Args:
            method: Comparison method ("threshold", "scaled", "percentage")
            tolerance: Absolute or relative tolerance for matching
            relative: Whether tolerance is relative (percentage) or absolute
            scale_factor: Factor for scaling differences (for scaled method)
        """
        self.method = method.lower()
        self.tolerance = tolerance
        self.relative = relative
        self.scale_factor = scale_factor

        valid_methods = {"threshold", "scaled", "percentage", "exact"}
        if self.method not in valid_methods:
            raise ValueError(
                f"Invalid method: {method}. Must be one of {valid_methods}"
            )

    def compare(self, a: NumericValue, b: NumericValue, **kwargs) -> SimilarityScore:
        """Compare two numeric values."""
        # Handle None values
        if a is None and b is None:
            return SimilarityScore(1.0)
        if a is None or b is None:
            return SimilarityScore(0.0)

        # Convert to float
        try:
            val_a = float(a)
            val_b = float(b)
        except (ValueError, TypeError):
            return SimilarityScore(0.0)

        # Apply the selected method
        method_map = {
            "threshold": self._threshold_similarity,
            "scaled": self._scaled_similarity,
            "percentage": self._percentage_similarity,
            "exact": self._exact_similarity,
        }

        return method_map[self.method](val_a, val_b)

    def _threshold_similarity(self, a: float, b: float) -> SimilarityScore:
        """Threshold-based similarity."""
        if self.relative:
            # Relative tolerance (percentage)
            max_val = max(abs(a), abs(b))
            if max_val == 0:
                return SimilarityScore(1.0)
            threshold = max_val * self.tolerance
        else:
            # Absolute tolerance
            threshold = self.tolerance

        return SimilarityScore(1.0 if abs(a - b) <= threshold else 0.0)

    def _scaled_similarity(self, a: float, b: float) -> SimilarityScore:
        """Scaled similarity using exponential decay."""
        difference = abs(a - b)
        if difference == 0:
            return SimilarityScore(1.0)

        scale = self.scale_factor or max(abs(a), abs(b), 1.0)
        normalized_diff = difference / scale

        # Exponential decay: e^(-x)
        similarity = math.exp(-normalized_diff)
        return SimilarityScore(min(1.0, max(0.0, similarity)))

    def _percentage_similarity(self, a: float, b: float) -> SimilarityScore:
        """Percentage-based similarity."""
        if a == 0 and b == 0:
            return SimilarityScore(1.0)

        max_val = max(abs(a), abs(b))
        if max_val == 0:
            return SimilarityScore(1.0)

        percentage_diff = abs(a - b) / max_val
        similarity = max(0.0, 1.0 - percentage_diff)
        return SimilarityScore(similarity)

    def _exact_similarity(self, a: float, b: float) -> SimilarityScore:
        """Exact numeric match."""
        return SimilarityScore(1.0 if a == b else 0.0)


# Backward compatibility function
def numeric_similarity(
    a: NumericValue, b: NumericValue, tolerance: float = 0.0
) -> float:
    """Calculate numeric similarity (backward compatibility)."""
    comparator = NumericComparator(method="threshold", tolerance=tolerance)
    return float(comparator.compare(a, b))
