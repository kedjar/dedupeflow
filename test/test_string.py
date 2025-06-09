"""Tests for string comparators."""

import pytest
from dedupeflow.comparators.string import (
    levenshtein_similarity,
    jaro_winkler_similarity,
)


def test_levenshtein_similarity(sample_string_pairs):
    """Test Levenshtein similarity function."""
    results = [levenshtein_similarity(s1, s2) for s1, s2 in sample_string_pairs]
    
    # All similarities should be between 0 and 1
    assert all(0 <= sim <= 1 for sim in results)
    
    # Exact matches should have similarity 1.0
    assert levenshtein_similarity("exact", "exact") == 1.0
    
    # Completely different strings should have low similarity
    assert levenshtein_similarity("completely", "different") < 0.3
    
    # Small edits should have high similarity
    assert levenshtein_similarity("testing", "testng") > 0.8


def test_jaro_winkler_similarity(sample_string_pairs):
    """Test Jaro-Winkler similarity function."""
    results = [jaro_winkler_similarity(s1, s2) for s1, s2 in sample_string_pairs]
    
    # All similarities should be between 0 and 1
    assert all(0 <= sim <= 1 for sim in results)
    
    # Exact matches should have similarity 1.0
    assert jaro_winkler_similarity("exact", "exact") == 1.0
    
    # Test with empty strings
    assert jaro_winkler_similarity("", "") == 1.0
    assert jaro_winkler_similarity("test", "") == 0.0


def test_string_comparator_handles_none_values():
    """Test that comparators handle None values gracefully."""
    assert levenshtein_similarity(None, "test") == 0.0
    assert levenshtein_similarity("test", None) == 0.0
    assert levenshtein_similarity(None, None) == 1.0
    
    assert jaro_winkler_similarity(None, "test") == 0.0
    assert jaro_winkler_similarity("test", None) == 0.0
    assert jaro_winkler_similarity(None, None) == 1.0