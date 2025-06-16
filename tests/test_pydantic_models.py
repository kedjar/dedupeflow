"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from dedupeflow.models import (
    ComparatorType,
    DedupeConfig,
    DedupeResults,
    FieldConfig,
    MatchResult,
    StringMethod,
)
from dedupeflow.types import FieldName, RecordId, SimilarityScore


class TestFieldConfig:
    """Test FieldConfig model."""

    def test_valid_field_config(self):
        """Test creating valid field configuration."""
        config = FieldConfig(
            name=FieldName("test_field"),
            comparator=ComparatorType.STRING,
            weight=0.5,
            method="levenshtein",
            threshold=0.8,
            required=True,
        )

        assert config.name == FieldName("test_field")
        assert config.comparator == ComparatorType.STRING
        assert config.weight == 0.5
        assert config.method == "levenshtein"
        assert config.threshold == 0.8
        assert config.required is True

    def test_default_values(self):
        """Test default values for field configuration."""
        config = FieldConfig(
            name=FieldName("test_field"), comparator=ComparatorType.STRING
        )

        assert config.weight == 1.0
        assert config.method is None
        assert config.threshold is None
        assert config.required is True

    def test_invalid_weight(self):
        """Test validation of weight field."""
        # Weight too high
        with pytest.raises(ValidationError):
            FieldConfig(
                name=FieldName("test_field"),
                comparator=ComparatorType.STRING,
                weight=1.5,
            )

        # Weight negative
        with pytest.raises(ValidationError):
            FieldConfig(
                name=FieldName("test_field"),
                comparator=ComparatorType.STRING,
                weight=-0.1,
            )

    def test_invalid_threshold(self):
        """Test validation of threshold field."""
        # Threshold too high
        with pytest.raises(ValidationError):
            FieldConfig(
                name=FieldName("test_field"),
                comparator=ComparatorType.STRING,
                threshold=1.5,
            )

        # Threshold negative
        with pytest.raises(ValidationError):
            FieldConfig(
                name=FieldName("test_field"),
                comparator=ComparatorType.STRING,
                threshold=-0.1,
            )


class TestDedupeConfig:
    """Test DedupeConfig model."""

    def test_valid_config(self):
        """Test creating valid deduplication configuration."""
        fields = [
            FieldConfig(
                name=FieldName("name"), comparator=ComparatorType.STRING, weight=0.5
            ),
            FieldConfig(
                name=FieldName("email"), comparator=ComparatorType.STRING, weight=0.5
            ),
        ]

        config = DedupeConfig(
            fields=fields,
            global_threshold=0.8,
            require_all_fields=False,
            enable_blocking=True,
            blocking_keys=[FieldName("name")],
        )

        assert len(config.fields) == 2
        assert config.global_threshold == 0.8
        assert config.require_all_fields is False
        assert config.enable_blocking is True
        assert config.blocking_keys == [FieldName("name")]

    def test_empty_fields_validation(self):
        """Test validation when fields list is empty."""
        with pytest.raises(
            ValidationError, match="At least one field configuration is required"
        ):
            DedupeConfig(fields=[])

    def test_zero_weight_validation(self):
        """Test validation when all weights sum to zero."""
        fields = [
            FieldConfig(
                name=FieldName("name"), comparator=ComparatorType.STRING, weight=0.0
            ),
            FieldConfig(
                name=FieldName("email"), comparator=ComparatorType.STRING, weight=0.0
            ),
        ]

        with pytest.raises(
            ValidationError, match="Total field weights must be positive"
        ):
            DedupeConfig(fields=fields)

    def test_negative_weights_validation(self):
        """Test validation with negative total weights."""
        fields = [
            FieldConfig(
                name=FieldName("name"), comparator=ComparatorType.STRING, weight=-0.5
            ),
            FieldConfig(
                name=FieldName("email"), comparator=ComparatorType.STRING, weight=-0.3
            ),
        ]

        with pytest.raises(
            ValidationError, match="Total field weights must be positive"
        ):
            DedupeConfig(fields=fields)

    def test_invalid_global_threshold(self):
        """Test validation of global threshold."""
        fields = [
            FieldConfig(name=FieldName("name"), comparator=ComparatorType.STRING),
        ]

        # Threshold too high
        with pytest.raises(ValidationError):
            DedupeConfig(fields=fields, global_threshold=1.5)

        # Threshold negative
        with pytest.raises(ValidationError):
            DedupeConfig(fields=fields, global_threshold=-0.1)


class TestMatchResult:
    """Test MatchResult model."""

    def test_valid_match_result(self):
        """Test creating valid match result."""
        result = MatchResult(
            record1_id=RecordId(1),
            record2_id=RecordId(2),
            overall_score=SimilarityScore(0.85),
            field_scores={
                FieldName("name"): SimilarityScore(0.9),
                FieldName("email"): SimilarityScore(0.8),
            },
            is_match=True,
            confidence=0.87,
        )

        assert result.record1_id == 1
        assert result.record2_id == 2
        assert result.overall_score == 0.85
        assert len(result.field_scores) == 2
        assert result.is_match is True
        assert result.confidence == 0.87
        assert isinstance(result.timestamp, datetime)

    def test_invalid_confidence(self):
        """Test validation of confidence field."""
        # Confidence too high
        with pytest.raises(ValidationError):
            MatchResult(
                record1_id=RecordId(1),
                record2_id=RecordId(2),
                overall_score=SimilarityScore(0.85),
                field_scores={},
                is_match=True,
                confidence=1.5,
            )

        # Confidence negative
        with pytest.raises(ValidationError):
            MatchResult(
                record1_id=RecordId(1),
                record2_id=RecordId(2),
                overall_score=SimilarityScore(0.85),
                field_scores={},
                is_match=True,
                confidence=-0.1,
            )

    def test_json_serialization(self):
        """Test JSON serialization of match result."""
        result = MatchResult(
            record1_id=RecordId(1),
            record2_id=RecordId(2),
            overall_score=SimilarityScore(0.85),
            field_scores={},
            is_match=True,
            confidence=0.87,
        )

        json_data = result.dict()
        assert "timestamp" in json_data

        # Should be able to recreate from dict
        recreated = MatchResult(**json_data)
        assert recreated.record1_id == result.record1_id


class TestDedupeResults:
    """Test DedupeResults model."""

    def test_valid_results(self):
        """Test creating valid deduplication results."""
        matches = [
            MatchResult(
                record1_id=RecordId(1),
                record2_id=RecordId(2),
                overall_score=SimilarityScore(0.85),
                field_scores={},
                is_match=True,
                confidence=0.87,
            )
        ]

        config = DedupeConfig(
            fields=[
                FieldConfig(name=FieldName("name"), comparator=ComparatorType.STRING),
            ]
        )

        results = DedupeResults(
            matches=matches,
            total_comparisons=10,
            total_matches=1,
            execution_time_seconds=1.5,
            config_used=config,
        )

        assert len(results.matches) == 1
        assert results.total_comparisons == 10
        assert results.total_matches == 1
        assert results.execution_time_seconds == 1.5
        assert results.config_used == config

    def test_mismatched_counts_validation(self):
        """Test validation when match count doesn't match list length."""
        matches = [
            MatchResult(
                record1_id=RecordId(1),
                record2_id=RecordId(2),
                overall_score=SimilarityScore(0.85),
                field_scores={},
                is_match=True,
                confidence=0.87,
            )
        ]

        config = DedupeConfig(
            fields=[
                FieldConfig(name=FieldName("name"), comparator=ComparatorType.STRING),
            ]
        )

        with pytest.raises(
            ValidationError, match="total_matches must equal length of matches list"
        ):
            DedupeResults(
                matches=matches,
                total_comparisons=10,
                total_matches=2,  # Doesn't match length of matches list
                execution_time_seconds=1.5,
                config_used=config,
            )

    def test_negative_values_validation(self):
        """Test validation of negative values."""
        config = DedupeConfig(
            fields=[
                FieldConfig(name=FieldName("name"), comparator=ComparatorType.STRING),
            ]
        )

        # Negative comparisons
        with pytest.raises(ValidationError):
            DedupeResults(
                matches=[],
                total_comparisons=-1,
                total_matches=0,
                execution_time_seconds=1.5,
                config_used=config,
            )

        # Negative execution time
        with pytest.raises(ValidationError):
            DedupeResults(
                matches=[],
                total_comparisons=0,
                total_matches=0,
                execution_time_seconds=-1.0,
                config_used=config,
            )


class TestEnums:
    """Test enum definitions."""

    def test_comparator_type_enum(self):
        """Test ComparatorType enum."""
        assert ComparatorType.STRING == "string"
        assert ComparatorType.NUMERIC == "numeric"
        assert ComparatorType.DATE == "date"
        assert ComparatorType.EXACT == "exact"

    def test_string_method_enum(self):
        """Test StringMethod enum."""
        assert StringMethod.LEVENSHTEIN == "levenshtein"
        assert StringMethod.JARO_WINKLER == "jaro_winkler"
        assert StringMethod.COSINE == "cosine"
        assert StringMethod.JACCARD == "jaccard"
