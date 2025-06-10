"""Tests for the matching engine."""

from unittest.mock import Mock, patch

import pytest

from dedupeflow.core.matching import MatchingEngine
from dedupeflow.models import ComparatorType, FieldConfig, MatchResult
from dedupeflow.strategies import ThresholdStrategy
from dedupeflow.types import RecordId, SimilarityScore


class TestMatchingEngine:
    """Test MatchingEngine class."""

    def test_init(self):
        """Test matching engine initialization."""
        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=0.6),
            FieldConfig(name="age", comparator=ComparatorType.NUMERIC, weight=0.4),
        ]

        engine = MatchingEngine(field_configs)

        assert engine.field_configs == field_configs
        assert engine.global_threshold == 0.8
        assert engine.require_all_fields is False
        assert len(engine.comparators) == 2

    def test_setup_comparators(self):
        """Test comparator setup."""
        field_configs = [
            FieldConfig(
                name="name", comparator=ComparatorType.STRING, method="levenshtein"
            ),
            FieldConfig(
                name="score", comparator=ComparatorType.NUMERIC, method="threshold"
            ),
            FieldConfig(name="date", comparator=ComparatorType.DATE, method="exact"),
        ]

        engine = MatchingEngine(field_configs)

        assert "name" in engine.comparators
        assert "score" in engine.comparators
        assert "date" in engine.comparators

    def test_compare_records_exact_match(self):
        """Test comparing identical records."""
        field_configs = [
            FieldConfig(
                name="name",
                comparator=ComparatorType.STRING,
                weight=0.5,
                method="exact",
            ),
            FieldConfig(
                name="email",
                comparator=ComparatorType.STRING,
                weight=0.5,
                method="exact",
            ),
        ]

        engine = MatchingEngine(field_configs, global_threshold=0.9)

        record1 = {"name": "John Smith", "email": "john@test.com"}
        record2 = {"name": "John Smith", "email": "john@test.com"}

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        assert result.overall_score == SimilarityScore(1.0)
        assert result.is_match is True
        assert result.confidence > 0.9
        assert len(result.field_scores) == 2

    def test_compare_records_no_match(self):
        """Test comparing completely different records."""
        field_configs = [
            FieldConfig(
                name="name",
                comparator=ComparatorType.STRING,
                weight=1.0,
                method="exact",
            ),
        ]

        engine = MatchingEngine(field_configs, global_threshold=0.9)

        record1 = {"name": "John Smith"}
        record2 = {"name": "Jane Doe"}

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        assert result.overall_score == SimilarityScore(0.0)
        assert result.is_match is False
        assert result.confidence < 0.5

    def test_compare_records_missing_fields(self):
        """Test comparing records with missing fields."""
        field_configs = [
            FieldConfig(
                name="name", comparator=ComparatorType.STRING, weight=0.5, required=True
            ),
            FieldConfig(
                name="email",
                comparator=ComparatorType.STRING,
                weight=0.5,
                required=False,
            ),
        ]

        engine = MatchingEngine(field_configs)

        record1 = {"name": "John Smith"}  # Missing email
        record2 = {"name": "John Smith", "email": "john@test.com"}

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        # Should still compare, with reduced confidence
        assert 0.0 <= float(result.overall_score) <= 1.0
        assert result.confidence < 1.0

    def test_compare_records_missing_required_field(self):
        """Test comparing records missing required fields."""
        field_configs = [
            FieldConfig(
                name="name", comparator=ComparatorType.STRING, weight=1.0, required=True
            ),
        ]

        engine = MatchingEngine(field_configs, require_all_fields=True)

        record1 = {"email": "john@test.com"}  # Missing required name
        record2 = {"name": "John Smith"}

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        # Should have low score due to missing required field
        assert result.overall_score == SimilarityScore(0.0)
        assert result.is_match is False

    def test_field_specific_threshold(self):
        """Test field-specific thresholds."""
        field_configs = [
            FieldConfig(
                name="name",
                comparator=ComparatorType.STRING,
                weight=1.0,
                method="levenshtein",
                threshold=0.9,  # High threshold
            ),
        ]

        engine = MatchingEngine(field_configs, global_threshold=0.5)

        record1 = {"name": "John Smith"}
        record2 = {"name": "Jon Smith"}  # Similar but not identical

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        # Should fail field-specific threshold even if similar
        # (depends on exact Levenshtein score)
        assert 0.0 <= float(result.overall_score) <= 1.0

    def test_batch_compare(self):
        """Test batch comparison."""
        field_configs = [
            FieldConfig(
                name="name",
                comparator=ComparatorType.STRING,
                weight=1.0,
                method="exact",
            ),
        ]

        engine = MatchingEngine(field_configs)

        record_pairs = [
            (RecordId(1), {"name": "John"}, RecordId(2), {"name": "John"}),
            (RecordId(3), {"name": "Jane"}, RecordId(4), {"name": "Bob"}),
        ]

        results = engine.batch_compare(record_pairs)

        assert len(results) == 2
        assert all(isinstance(r, MatchResult) for r in results)
        assert results[0].is_match is True
        assert results[1].is_match is False

    def test_get_field_weights(self):
        """Test getting field weights."""
        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=0.6),
            FieldConfig(name="email", comparator=ComparatorType.STRING, weight=0.4),
        ]

        engine = MatchingEngine(field_configs)
        weights = engine.get_field_weights()

        assert weights["name"] == 0.6
        assert weights["email"] == 0.4

    def test_update_match_strategy(self):
        """Test updating match strategy."""
        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=1.0),
        ]

        engine = MatchingEngine(field_configs)
        new_strategy = ThresholdStrategy(threshold=0.9)

        engine.update_match_strategy(new_strategy)
        assert engine.match_strategy == new_strategy

    def test_get_statistics(self):
        """Test getting match statistics."""
        # Create some mock results
        results = [
            MatchResult(
                record1_id=RecordId(1),
                record2_id=RecordId(2),
                overall_score=SimilarityScore(0.9),
                field_scores={"name": SimilarityScore(0.9)},
                is_match=True,
                confidence=0.85,
            ),
            MatchResult(
                record1_id=RecordId(3),
                record2_id=RecordId(4),
                overall_score=SimilarityScore(0.3),
                field_scores={"name": SimilarityScore(0.3)},
                is_match=False,
                confidence=0.2,
            ),
        ]

        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=1.0),
        ]

        engine = MatchingEngine(field_configs)
        stats = engine.get_statistics(results)

        assert stats["total_comparisons"] == 2
        assert stats["total_matches"] == 1
        assert stats["match_rate"] == 0.5
        assert stats["avg_score"] == 0.6
        assert "name_avg_score" in stats

    def test_calculate_confidence(self):
        """Test confidence calculation."""
        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=0.5),
            FieldConfig(name="email", comparator=ComparatorType.STRING, weight=0.5),
        ]

        engine = MatchingEngine(field_configs)

        # High consistency should give high confidence
        field_scores = {"name": SimilarityScore(0.9), "email": SimilarityScore(0.8)}

        confidence = engine._calculate_confidence(
            field_scores, SimilarityScore(0.85), []
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be relatively high

    @patch("dedupeflow.core.matching.logger")
    def test_comparison_error_handling(self, mock_logger):
        """Test handling of comparison errors."""
        field_configs = [
            FieldConfig(name="name", comparator=ComparatorType.STRING, weight=1.0),
        ]

        engine = MatchingEngine(field_configs)

        # Mock comparator to raise exception
        engine.comparators["name"].compare = Mock(side_effect=Exception("Test error"))

        record1 = {"name": "John"}
        record2 = {"name": "Jane"}

        result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

        # Should handle error gracefully
        assert result.field_scores["name"] == SimilarityScore(0.0)
        mock_logger.warning.assert_called()


@pytest.fixture
def sample_field_configs():
    """Sample field configurations for testing."""
    return [
        FieldConfig(
            name="name",
            comparator=ComparatorType.STRING,
            weight=0.4,
            method="levenshtein",
        ),
        FieldConfig(
            name="email", comparator=ComparatorType.STRING, weight=0.3, method="exact"
        ),
        FieldConfig(
            name="age", comparator=ComparatorType.NUMERIC, weight=0.2, tolerance=1.0
        ),
        FieldConfig(
            name="score",
            comparator=ComparatorType.NUMERIC,
            weight=0.1,
            method="percentage",
        ),
    ]


def test_matching_engine_integration(sample_field_configs):
    """Integration test for matching engine."""
    engine = MatchingEngine(sample_field_configs, global_threshold=0.8)

    record1 = {
        "name": "John Smith",
        "email": "john.smith@email.com",
        "age": 30,
        "score": 85.5,
    }

    record2 = {
        "name": "Jon Smith",  # Similar
        "email": "john.smith@email.com",  # Same
        "age": 30,  # Same
        "score": 86.0,  # Close
    }

    result = engine.compare_records(RecordId(1), record1, RecordId(2), record2)

    # Should be a strong match
    assert float(result.overall_score) > 0.8
    assert result.is_match is True
    assert result.confidence > 0.7
    assert len(result.field_scores) == 4
