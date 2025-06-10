"""Core deduplication engine and utilities."""

from dedupeflow.core.blocking import (
    BlockingStrategy,
    CanopyBlockingStrategy,
    HashBlockingStrategy,
    NGramBlockingStrategy,
    SoundexBlockingStrategy,
    StandardBlockingStrategy,
)
from dedupeflow.core.engine import DedupeEngine
from dedupeflow.core.matching import MatchingEngine

__all__ = [
    "DedupeEngine",
    "MatchingEngine",
    "BlockingStrategy",
    "StandardBlockingStrategy",
    "SoundexBlockingStrategy",
    "NGramBlockingStrategy",
    "CanopyBlockingStrategy",
    "HashBlockingStrategy",
]
