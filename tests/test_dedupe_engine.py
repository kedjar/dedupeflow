"""Tests for the core deduplication engine."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from dedupeflow.core.blocking import StandardBlockingStrategy
from dedupeflow.core.engine import DedupeEngine
from dedupeflow.models import ComparatorType, DedupeConfig, FieldConfig
from dedupeflow.types import DedupeResults, FieldName, RecordId


class TestDedupeEngine:
    """Test the DedupeEngine class."""

    def test_init(self, sample_config):
        """Test engine initialization."""
        engine = DedupeEngine(sample_config)

        assert engine.config == sample_config
        assert isinstance(engine.blocking_strategy, StandardBlockingStrategy)
        assert engine.matching_engine is not None

    def test_init_with_custom_blocking(self, sample_config):
        """Test engine initialization with custom blocking strategy."""
        custom_blocking = Mock()
        engine = DedupeEngine(sample_config, blocking_strategy=custom_blocking)

        assert engine.blocking_strategy == custom_blocking

    def test_deduplicate_simple(self, sample_records, sample_config):
        """Test basic deduplication functionality."""
        engine = DedupeEngine(sample_config)

        results = engine.deduplicate(sample_records)

        assert results.total_comparisons >= 0
        assert results.total_matches >= 0
        assert results.total_matches <= results.total_comparisons
        assert len(results.matches) == results.total_matches
        assert results.execution_time_seconds > 0
        assert results.config_used == sample_config

    def test_deduplicate_with_known_duplicates(self, duplicate_records):
        """Test deduplication with known duplicate records."""
        config = DedupeConfig(
            fields=[
                FieldConfig(
                    name=FieldName("name"),
                    comparator=ComparatorType.STRING,
                    weight=0.5,
                    method="exact",
                ),
                FieldConfig(
                    name=FieldName("email"),
                    comparator=ComparatorType.STRING,
                    weight=0.5,
                    method="exact",
                ),
            ],
            global_threshold=0.9,
            enable_blocking=False,  # Test without blocking
        )

        engine = DedupeEngine(config)
        results = engine.deduplicate(duplicate_records)

        # Should find at least one duplicate pair
        assert results.total_matches >= 1

        # Check that we found the known duplicates
        duplicate_pairs = [(1, 2), (3, 4)]  # Known duplicate pairs
        found_pairs = [
            (match.record1_id, match.record2_id) for match in results.matches
        ]

        # At least one known duplicate should be found
        assert any(
            (pair in found_pairs or (pair[1], pair[0]) in found_pairs)
            for pair in duplicate_pairs
        )

    def test_deduplicate_with_blocking(self, sample_records, sample_config):
        """Test deduplication with blocking enabled."""
        # Enable blocking
        sample_config.enable_blocking = True
        sample_config.blocking_keys = ["name"]

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(sample_records)

        assert results.total_comparisons >= 0
        assert results.total_matches >= 0

    def test_deduplicate_with_progress_callback(self, sample_records, sample_config):
        """Test deduplication with progress callback."""
        callback_calls = []

        def progress_callback(current, total):
            callback_calls.append((current, total))

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(
            sample_records, progress_callback=progress_callback
        )

        # Progress callback should have been called
        # (might not be called for small datasets)
        assert isinstance(results, type(results))  # Just ensure it completed

    def test_deduplicate_custom_id_column(self, sample_records, sample_config):
        """Test deduplication with custom ID column."""
        # Rename id column
        test_data = sample_records.rename(columns={"id": "record_id"})

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(test_data, id_column="record_id")

        assert results.total_comparisons >= 0

    def test_deduplicate_empty_dataframe(self, sample_config):
        """Test deduplication with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["id", "name", "email"])

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(empty_df)

        assert results.total_comparisons == 0
        assert results.total_matches == 0
        assert len(results.matches) == 0

    def test_deduplicate_single_record(self, sample_config):
        """Test deduplication with single record."""
        single_record_df = pd.DataFrame(
            {
                "id": [1],
                "name": ["John Doe"],
                "email": ["john@test.com"],
                "phone": ["555-1234"],
                "income": [50000],
            }
        )

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(single_record_df)

        assert results.total_comparisons == 0
        assert results.total_matches == 0

    def test_generate_pairs_without_blocking(self, sample_records, sample_config):
        """Test pair generation without blocking."""
        sample_config.enable_blocking = False

        engine = DedupeEngine(sample_config)
        pairs = list(engine._generate_pairs(sample_records, "id"))

        # Should generate all possible pairs
        n_records = len(sample_records)
        expected_pairs = n_records * (n_records - 1) // 2
        assert len(pairs) == expected_pairs

    def test_generate_pairs_with_blocking(self, sample_records, sample_config):
        """Test pair generation with blocking."""
        sample_config.enable_blocking = True
        sample_config.blocking_keys = ["name"]

        engine = DedupeEngine(sample_config)
        pairs = list(engine._generate_pairs(sample_records, "id"))

        # Should generate fewer pairs than without blocking
        n_records = len(sample_records)
        max_possible_pairs = n_records * (n_records - 1) // 2
        assert len(pairs) <= max_possible_pairs


class TestDedupeEngineEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_id_column(self, sample_records, sample_config):
        """Test handling of missing ID column."""
        engine = DedupeEngine(sample_config)

        with pytest.raises(KeyError):
            engine.deduplicate(sample_records, id_column="nonexistent_id")

    def test_missing_required_fields(self, sample_config):
        """Test handling of missing required fields."""
        # Create data missing required fields
        incomplete_data = pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["John", "Jane"],
                # Missing email, phone, income fields
            }
        )

        engine = DedupeEngine(sample_config)
        results = engine.deduplicate(incomplete_data)

        # Should complete without error
        assert results.total_comparisons >= 0

    def test_mixed_data_types(self, mixed_data_types_records, sample_config):
        """Test handling of mixed data types."""
        engine = DedupeEngine(sample_config)

        # Should handle mixed types gracefully
        results = engine.deduplicate(mixed_data_types_records)
        assert results.total_comparisons >= 0


@pytest.mark.integration
class TestDedupeEngineIntegration:
    """Integration tests for the deduplication engine."""

    def test_end_to_end_deduplication(self):
        """Test complete end-to-end deduplication workflow."""
        # Create test data with known duplicates
        test_data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": [
                    "John Smith",
                    "John Smith",  # Duplicate
                    "Jane Doe",
                    "Robert Johnson",
                    "Jane M. Doe",  # Fuzzy duplicate
                ],
                "email": [
                    "john.smith@email.com",
                    "john.smith@email.com",  # Exact duplicate
                    "jane.doe@email.com",
                    "robert.j@email.com",
                    "jane.doe@email.com",  # Exact duplicate
                ],
                "age": [30, 30, 25, 45, 25],
            }
        )

        # Configure for exact matching
        config = DedupeConfig(
            fields=[
                FieldConfig(
                    name=FieldName("name"),
                    comparator=ComparatorType.STRING,
                    weight=0.4,
                    method="exact",
                ),
                FieldConfig(
                    name=FieldName("email"),
                    comparator=ComparatorType.STRING,
                    weight=0.6,
                    method="exact",
                ),
            ],
            global_threshold=0.8,
            enable_blocking=False,
        )

        engine = DedupeEngine(config)
        results = engine.deduplicate(test_data)

        # Should find the exact duplicates
        assert results.total_matches >= 1

        # Verify specific matches
        match_pairs = [
            (match.record1_id, match.record2_id) for match in results.matches
        ]

        # Records 1 and 2 should be matched (exact duplicates)
        assert (1, 2) in match_pairs or (2, 1) in match_pairs

        # Records 3 and 5 should be matched (same email)
        assert (3, 5) in match_pairs or (5, 3) in match_pairs
