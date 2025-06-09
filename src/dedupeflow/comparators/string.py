# src/record_linkage/comparators/string.py
"""String comparator functions for record linkage."""

from typing import Optional, Union
import jellyfish
import Levenshtein


def levenshtein_similarity(s1: Optional[str], s2: Optional[str]) -> float:
    """
    Calculate the normalized Levenshtein similarity between two strings.
    
    The similarity is 1.0 for identical strings and approaches 0.0 as
    strings become more different.
    
    Args:
        s1: First string to compare.
        s2: Second string to compare.
    
    Returns:
        float: Similarity score between 0.0 and 1.0.
    
    Examples:
        >>> levenshtein_similarity("John", "Jon")
        0.75
        >>> levenshtein_similarity("completely", "different")
        0.18181818181818182
    """
    # Handle None values
    if s1 is None and s2 is None:
        return 1.0
    if s1 is None or s2 is None:
        return 0.0
    
    # Convert to strings if needed
    s1 = str(s1)
    s2 = str(s2)
    
    # Quick check for exact match
    if s1 == s2:
        return 1.0
    
    # Empty string handling
    if not s1 or not s2:
        return 0.0
    
    # Calculate Levenshtein distance
    distance = Levenshtein.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    
    # Normalize to [0, 1] range
    similarity = 1.0 - (distance / max_len)
    return similarity


def jaro_winkler_similarity(s1: Optional[str], s2: Optional[str]) -> float:
    """
    Calculate the Jaro-Winkler similarity between two strings.
    
    This similarity metric is particularly effective for short strings
    like personal names.
    
    Args:
        s1: First string to compare.
        s2: Second string to compare.
    
    Returns:
        float: Similarity score between 0.0 and 1.0.
    
    Examples:
        >>> jaro_winkler_similarity("Martha", "Marhta")
        0.9611111111111111
        >>> jaro_winkler_similarity("CRATE", "TRACE")
        0.7333333333333334
    """
    # Handle None values
    if s1 is None and s2 is None:
        return 1.0
    if s1 is None or s2 is None:
        return 0.0
    
    # Convert to strings if needed
    s1 = str(s1)
    s2 = str(s2)
    
    # Quick check for exact match
    if s1 == s2:
        return 1.0
    
    # Empty string handling
    if not s1 or not s2:
        return 0.0
    
    # Calculate Jaro-Winkler similarity
    return jellyfish.jaro_winkler_similarity(s1, s2)