"""Tests for blocking strategies."""

from unittest.mock import Mock

import pandas as pd
import pytest

from dedupeflow.core.blocking import (
    CanopyBlockingStrategy,
    HashBlockingStrategy,
    NGramBlockingStrategy,
    SoundexBlockingStrategy,
    StandardBlockingStrategy,
)
from dedupeflow.types import FieldName, RecordId


class TestStandardBlockingStrategy:
    """Test StandardBlockingStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = StandardBlockingStrategy(max_block_size=5000)
        assert strategy.max_block_size == 5000

    def test_generate_pairs_simple(self):
        """Test basic pair generation."""
        data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "name": ["John", "John", "Jane", "Bob"],
                "city": ["NYC", "NYC", "LA", "NYC"],
            }
        )

        strategy = StandardBlockingStrategy()
        pairs = list(
            strategy.generate_pairs(data, [FieldName("name")], FieldName("id"))
        )

        # Should generate pairs for records with same name
        expected_pairs = [(RecordId(1), RecordId(2))]
        assert len(pairs) >= 1
        assert (RecordId(1), RecordId(2)) in pairs or (
            RecordId(2),
            RecordId(1),
        ) in pairs

    def test_create_block_key(self):
        """Test block key creation."""
        strategy = StandardBlockingStrategy()

        row = pd.Series({"name": "John Smith", "city": "New York"})
        key = strategy._create_block_key(row, [FieldName("name"), FieldName("city")])
        assert key == "john smith|new york"

        # Test with missing values
        row_missing = pd.Series({"name": "John Smith", "city": None})
        key_missing = strategy._create_block_key(
            row_missing, [FieldName("name"), FieldName("city")]
        )
        assert key_missing == "john smith|"


class TestSoundexBlockingStrategy:
    """Test SoundexBlockingStrategy class."""

    @pytest.mark.skipif(True, reason="Requires jellyfish package")
    def test_generate_pairs_soundex(self):
        """Test Soundex-based pair generation."""
        data = pd.DataFrame({"id": [1, 2, 3], "name": ["Smith", "Smyth", "Johnson"]})

        strategy = SoundexBlockingStrategy()
        pairs = list(
            strategy.generate_pairs(data, [FieldName("name")], FieldName("id"))
        )

        # Smith and Smyth should be in same block (same Soundex)
        pair_ids = [(int(p[0]), int(p[1])) for p in pairs]
        assert (1, 2) in pair_ids or (2, 1) in pair_ids


class TestNGramBlockingStrategy:
    """Test NGramBlockingStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = NGramBlockingStrategy(n=3, min_tokens=2)
        assert strategy.n == 3
        assert strategy.min_tokens == 2

    def test_extract_ngrams(self):
        """Test n-gram extraction."""
        strategy = NGramBlockingStrategy(n=2)

        row = pd.Series({"name": "test"})
        ngrams = strategy._extract_ngrams(row, [FieldName("name")])

        expected_ngrams = {"te", "es", "st"}
        assert ngrams == expected_ngrams

    def test_generate_pairs_ngram(self):
        """Test n-gram based pair generation."""
        data = pd.DataFrame({"id": [1, 2, 3], "name": ["testing", "test", "example"]})

        strategy = NGramBlockingStrategy(n=2, min_tokens=1)
        pairs = list(
            strategy.generate_pairs(data, [FieldName("name")], FieldName("id"))
        )

        # testing and test should share n-grams
        pair_ids = [(int(p[0]), int(p[1])) for p in pairs]
        assert len(pairs) >= 1


class TestCanopyBlockingStrategy:
    """Test CanopyBlockingStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = CanopyBlockingStrategy(
            loose_threshold=0.6, tight_threshold=0.8, max_canopy_size=500
        )
        assert strategy.loose_threshold == 0.6
        assert strategy.tight_threshold == 0.8
        assert strategy.max_canopy_size == 500

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        strategy = CanopyBlockingStrategy()

        record1 = pd.Series({"name": "John Smith"})
        record2 = pd.Series({"name": "John Smith"})
        record3 = pd.Series({"name": "Jane Doe"})

        # Same records should have high similarity
        sim1 = strategy._calculate_similarity(record1, record2, [FieldName("name")])
        assert sim1 == 1.0

        # Different records should have lower similarity
        sim2 = strategy._calculate_similarity(record1, record3, [FieldName("name")])
        assert sim2 < 1.0


class TestHashBlockingStrategy:
    """Test HashBlockingStrategy class."""

    def test_init(self):
        """Test strategy initialization."""
        strategy = HashBlockingStrategy(
            hash_functions=["first_3_chars", "last_3_chars"], max_block_size=1000
        )
        assert strategy.hash_functions == ["first_3_chars", "last_3_chars"]
        assert strategy.max_block_size == 1000

    def test_apply_hash_function(self):
        """Test hash function application."""
        strategy = HashBlockingStrategy()

        row = pd.Series({"name": "testing"})

        # Test different hash functions
        result1 = strategy._apply_hash_function(
            row, [FieldName("name")], "first_3_chars"
        )
        assert result1 == "tes"

        result2 = strategy._apply_hash_function(
            row, [FieldName("name")], "last_3_chars"
        )
        assert result2 == "ing"

        result3 = strategy._apply_hash_function(
            row, [FieldName("name")], "length_bucket"
        )
        assert result3 == "len_5"  # "testing" has 7 chars, bucket is 5

    def test_generate_pairs_hash(self):
        """Test hash-based pair generation."""
        data = pd.DataFrame({"id": [1, 2, 3], "name": ["test", "testing", "example"]})

        strategy = HashBlockingStrategy(hash_functions=["first_3_chars"])
        pairs = list(
            strategy.generate_pairs(data, [FieldName("name")], FieldName("id"))
        )

        # test and testing should be in same block (both start with "tes")
        pair_ids = [(int(p[0]), int(p[1])) for p in pairs]
        assert (1, 2) in pair_ids or (2, 1) in pair_ids


@pytest.fixture
def sample_blocking_data():
    """Sample data for blocking tests."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": [
                "John Smith",
                "John Smith",
                "Jane Doe",
                "Bob Johnson",
                "Jane M. Doe",
            ],
            "city": ["NYC", "NYC", "LA", "NYC", "LA"],
            "age": [30, 30, 25, 45, 26],
        }
    )


@pytest.mark.parametrize(
    "strategy_class",
    [
        StandardBlockingStrategy,
        NGramBlockingStrategy,
        HashBlockingStrategy,
    ],
)
def test_all_blocking_strategies_return_valid_pairs(
    strategy_class, sample_blocking_data
):
    """Test that all blocking strategies return valid pairs."""
    strategy = strategy_class()
    pairs = list(strategy.generate_pairs(sample_blocking_data, ["name"], "id"))

    # All pairs should be valid record ID tuples
    for pair in pairs:
        assert len(pair) == 2
        assert isinstance(pair[0], RecordId)
        assert isinstance(pair[1], RecordId)
        assert pair[0] != pair[1]  # No self-pairs
