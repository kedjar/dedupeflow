"""DedupeFlow: A modern Python library for data deduplication and record linkage.

This package provides efficient algorithms and tools for:
- String similarity comparison
- Numeric value matching
- Date/time comparison
- Record deduplication
- Entity resolution
"""

from importlib.metadata import version

from dedupeflow.comparators import DateComparator, NumericComparator, StringComparator
from dedupeflow.core.engine import DedupeEngine
from dedupeflow.core.matching import MatchingEngine
from dedupeflow.models import DedupeConfig, DedupeResults, FieldConfig, MatchResult
from dedupeflow.strategies import (
    ExactMatchStrategy,
    FuzzyMatchStrategy,
    ThresholdStrategy,
)
from dedupeflow.types import SimilarityScore

# from dedupeflow.core import (
#     DedupeEngine,
#     MatchingEngine,
# )


__version__ = version("dedupeflow")

__all__ = [
    # Core classes
    "DedupeEngine",
    "MatchingEngine",
    "MatchResult",
    "DedupeResults",
    "SimilarityScore",
    # Configuration
    "DedupeConfig",
    "FieldConfig",
    # Comparators
    "StringComparator",
    "NumericComparator",
    "DateComparator",
    # Strategies
    "ExactMatchStrategy",
    "FuzzyMatchStrategy",
    "ThresholdStrategy",
    # Version
    "__version__",
]
