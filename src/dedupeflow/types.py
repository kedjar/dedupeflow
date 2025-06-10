"""Type definitions for DedupeFlow."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, NewType, Optional, Tuple, Union

# Core types
SimilarityScore = NewType("SimilarityScore", float)
RecordId = NewType("RecordId", Union[str, int])
FieldName = NewType("FieldName", str)

# Data types
StringValue = Optional[str]
NumericValue = Optional[Union[int, float]]
DateValue = Optional[Union[str, date, datetime]]
AnyValue = Any

# Record types
Record = Dict[FieldName, AnyValue]
RecordPair = Tuple[Record, Record]
MatchPair = Tuple[RecordId, RecordId]

# Configuration types
ComparatorConfig = Dict[str, Any]
StrategyConfig = Dict[str, Any]
EngineConfig = Dict[str, Any]

# Result types
FieldScores = Dict[FieldName, SimilarityScore]
DedupeResults = List[Any]  # Will be properly typed when models module is imported
