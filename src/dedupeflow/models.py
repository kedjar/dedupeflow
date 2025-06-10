"""Pydantic models for configuration and results."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from dedupeflow.types import FieldName, RecordId, SimilarityScore


class ComparatorType(str, Enum):
    """Available comparator types."""

    STRING = "string"
    NUMERIC = "numeric"
    DATE = "date"
    EXACT = "exact"


class StringMethod(str, Enum):
    """String comparison methods."""

    LEVENSHTEIN = "levenshtein"
    JARO_WINKLER = "jaro_winkler"
    COSINE = "cosine"
    JACCARD = "jaccard"


class FieldConfig(BaseModel):
    """Configuration for a single field comparison."""

    name: FieldName
    comparator: ComparatorType
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    method: Optional[str] = None
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tolerance: Optional[float] = Field(default=None, ge=0.0)
    required: bool = True

    class Config:
        use_enum_values = True


class DedupeConfig(BaseModel):
    """Main configuration for deduplication engine."""

    fields: List[FieldConfig]
    global_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    require_all_fields: bool = False
    enable_blocking: bool = True
    blocking_keys: Optional[List[FieldName]] = None

    @validator("fields")
    def fields_not_empty(cls, v):
        if not v:
            raise ValueError("At least one field configuration is required")
        return v

    @validator("fields")
    def weights_sum_positive(cls, v):
        total_weight = sum(field.weight for field in v)
        if total_weight <= 0:
            raise ValueError("Total field weights must be positive")
        return v


class MatchResult(BaseModel):
    """Result of a single record comparison."""

    record1_id: RecordId
    record2_id: RecordId
    overall_score: SimilarityScore
    field_scores: Dict[FieldName, SimilarityScore]
    is_match: bool
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DedupeResults(BaseModel):
    """Results from a deduplication run."""

    matches: List[MatchResult]
    total_comparisons: int = Field(ge=0)
    total_matches: int = Field(ge=0)
    execution_time_seconds: float = Field(ge=0.0)
    config_used: DedupeConfig

    @validator("total_matches")
    def matches_count_valid(cls, v, values):
        if "matches" in values and v != len(values["matches"]):
            raise ValueError("total_matches must equal length of matches list")
        return v
