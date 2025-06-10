"""Tests for string comparators."""

import pytest

from dedupeflow.comparators.string import (
    StringComparator,
    jaro_winkler_similarity,
    levenshtein_similarity,
)
from dedupeflow.types import SimilarityScore


class TestStringComparator:
    """Test the StringComparator class."""

    def test_init_valid_methods(self):
        """Test initialization with valid methods."""
        valid_methods = [
            "levenshtein",
            "jaro_winkler",
            "cosine",
            "jaccard",
            "exact",
            "soundex",
            "metaphone",
        ]

        for method in valid_methods:
            comparator = StringComparator(method=method)
            assert comparator.method == method

    def test_init_invalid_method(self):
        """Test initialization with invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid method"):
            StringComparator(method="invalid_method")

    def test_levenshtein_method(self, sample_string_pairs):
        """Test Levenshtein similarity method."""
        comparator = StringComparator(method="levenshtein")

        # Test exact matches
        assert comparator.compare("test", "test") == SimilarityScore(1.0)
        assert comparator.compare("", "") == SimilarityScore(1.0)

        # Test None handling
        assert comparator.compare(None, None) == SimilarityScore(1.0)
        assert comparator.compare("test", None) == SimilarityScore(0.0)
        assert comparator.compare(None, "test") == SimilarityScore(0.0)

        # Test empty strings
        assert comparator.compare("", "test") == SimilarityScore(0.0)
        assert comparator.compare("test", "") == SimilarityScore(0.0)

        # Test sample pairs
        for s1, s2 in sample_string_pairs:
            if s1 and s2:  # Skip empty string pairs
                score = comparator.compare(s1, s2)
                assert 0.0 <= float(score) <= 1.0

    def test_jaro_winkler_method(self):
        """Test Jaro-Winkler similarity method."""
        comparator = StringComparator(method="jaro_winkler")

        # Test exact matches
        assert comparator.compare("test", "test") == SimilarityScore(1.0)

        # Test similar strings
        score = comparator.compare("John", "Jon")
        assert float(score) > 0.8

        # Test different strings
        score = comparator.compare("apple", "orange")
        assert float(score) < 0.5

    def test_exact_method(self):
        """Test exact matching method."""
        comparator = StringComparator(method="exact")

        assert comparator.compare("test", "test") == SimilarityScore(1.0)
        assert comparator.compare("test", "Test") == SimilarityScore(
            0.0
        )  # Case sensitive by default
        assert comparator.compare("test", "testing") == SimilarityScore(0.0)

    def test_case_sensitivity(self):
        """Test case sensitivity options."""
        case_sensitive = StringComparator(method="exact", case_sensitive=True)
        case_insensitive = StringComparator(method="exact", case_sensitive=False)

        assert case_sensitive.compare("Test", "test") == SimilarityScore(0.0)
        assert case_insensitive.compare("Test", "test") == SimilarityScore(1.0)

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        normalizing = StringComparator(method="exact", normalize_whitespace=True)
        non_normalizing = StringComparator(method="exact", normalize_whitespace=False)

        assert normalizing.compare("test  string", "test string") == SimilarityScore(
            1.0
        )
        assert non_normalizing.compare(
            "test  string", "test string"
        ) == SimilarityScore(0.0)

    def test_punctuation_removal(self):
        """Test punctuation removal."""
        removing = StringComparator(method="exact", remove_punctuation=True)
        non_removing = StringComparator(method="exact", remove_punctuation=False)

        assert removing.compare("test!", "test") == SimilarityScore(1.0)
        assert non_removing.compare("test!", "test") == SimilarityScore(0.0)

    def test_cosine_similarity(self):
        """Test cosine similarity method."""
        comparator = StringComparator(method="cosine")

        # Test similar strings
        score = comparator.compare("testing", "test")
        assert 0.0 <= float(score) <= 1.0

        # Test exact match
        assert comparator.compare("test", "test") == SimilarityScore(1.0)

    def test_jaccard_similarity(self):
        """Test Jaccard similarity method."""
        comparator = StringComparator(method="jaccard")

        # Test exact match
        assert comparator.compare("test", "test") == SimilarityScore(1.0)

        # Test similarity
        score = comparator.compare("testing", "test")
        assert 0.0 <= float(score) <= 1.0

    def test_soundex_similarity(self):
        """Test Soundex similarity method."""
        comparator = StringComparator(method="soundex")

        # Test phonetically similar names
        score = comparator.compare("Smith", "Smyth")
        assert float(score) == 1.0  # Should be phonetically identical

        # Test different names
        score = comparator.compare("Smith", "Johnson")
        assert float(score) == 0.0

    def test_metaphone_similarity(self):
        """Test Metaphone similarity method."""
        comparator = StringComparator(method="metaphone")

        # Test phonetically similar words
        score = comparator.compare("night", "knight")
        assert float(score) == 1.0  # Should be phonetically identical

    def test_callable_interface(self):
        """Test that comparator can be called as a function."""
        comparator = StringComparator(method="exact")

        # Test callable interface
        score = comparator("test", "test")
        assert score == SimilarityScore(1.0)


class TestBackwardCompatibilityFunctions:
    """Test backward compatibility functions."""

    def test_levenshtein_similarity_function(self):
        """Test standalone Levenshtein similarity function."""
        assert levenshtein_similarity("test", "test") == 1.0
        assert levenshtein_similarity("test", "testing") > 0.7
        assert levenshtein_similarity(None, None) == 1.0
        assert levenshtein_similarity("test", None) == 0.0

    def test_jaro_winkler_similarity_function(self):
        """Test standalone Jaro-Winkler similarity function."""
        assert jaro_winkler_similarity("test", "test") == 1.0
        assert jaro_winkler_similarity("John", "Jon") > 0.8
        assert jaro_winkler_similarity(None, None) == 1.0
        assert jaro_winkler_similarity("test", None) == 0.0


@pytest.mark.parametrize("method", ["levenshtein", "jaro_winkler", "cosine", "jaccard"])
def test_all_methods_return_valid_scores(method, sample_string_pairs):
    """Test that all methods return valid similarity scores."""
    comparator = StringComparator(method=method)

    for s1, s2 in sample_string_pairs:
        score = comparator.compare(s1, s2)
        assert isinstance(score, SimilarityScore)
        assert 0.0 <= float(score) <= 1.0


def test_edge_cases():
    """Test edge cases for string comparison."""
    comparator = StringComparator(method="levenshtein")

    # Very long strings
    long_str1 = "a" * 1000
    long_str2 = "a" * 999 + "b"
    score = comparator.compare(long_str1, long_str2)
    assert 0.0 <= float(score) <= 1.0

    # Unicode strings
    score = comparator.compare("café", "cafe")
    assert 0.0 <= float(score) <= 1.0

    # Numbers as strings
    score = comparator.compare("123", "124")
    assert 0.0 <= float(score) <= 1.0
