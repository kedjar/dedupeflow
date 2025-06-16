"""Enhanced string comparators with multiple algorithms."""

from __future__ import annotations

import re
from typing import Optional, Set, cast

import jellyfish
import Levenshtein
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dedupeflow.protocols import BaseComparator
from dedupeflow.types import SimilarityScore, StringValue


class StringComparator(BaseComparator):
    """Advanced string comparator with multiple algorithms."""

    def __init__(
        self,
        method: str = "levenshtein",
        case_sensitive: bool = True,
        normalize_whitespace: bool = True,
        remove_punctuation: bool = False,
    ):
        """Initialize the string comparator.

        Args:
            method: Comparison method to use
            case_sensitive: Whether to consider case differences
            normalize_whitespace: Whether to normalize whitespace
            remove_punctuation: Whether to remove punctuation
        """
        self.method = method.lower()
        self.case_sensitive = case_sensitive
        self.normalize_whitespace = normalize_whitespace
        self.remove_punctuation = remove_punctuation

        # Validate method
        valid_methods = {
            "levenshtein",
            "jaro_winkler",
            "cosine",
            "jaccard",
            "exact",
            "soundex",
            "metaphone",
        }
        if self.method not in valid_methods:
            raise ValueError(
                f"Invalid method: {method}. Must be one of {valid_methods}"
            )

    def compare(self, a: StringValue, b: StringValue, **kwargs) -> SimilarityScore:
        """Compare two strings using the configured method."""
        # Handle None values
        if a is None and b is None:
            return SimilarityScore(1.0)
        if a is None or b is None:
            return SimilarityScore(0.0)

        # Preprocess strings
        str_a = self._preprocess(str(a))
        str_b = self._preprocess(str(b))

        # Quick exact match check
        if str_a == str_b:
            return SimilarityScore(1.0)

        # Empty string handling
        if not str_a or not str_b:
            return SimilarityScore(0.0)

        # Apply the selected method
        method_map = {
            "levenshtein": self._levenshtein_similarity,
            "jaro_winkler": self._jaro_winkler_similarity,
            "cosine": self._cosine_similarity,
            "jaccard": self._jaccard_similarity,
            "exact": self._exact_similarity,
            "soundex": self._soundex_similarity,
            "metaphone": self._metaphone_similarity,
        }

        return method_map[self.method](str_a, str_b)

    def _preprocess(self, text: str) -> str:
        """Preprocess text according to configuration."""
        if not self.case_sensitive:
            text = text.lower()

        if self.normalize_whitespace:
            text = re.sub(r"\s+", " ", text.strip())

        if self.remove_punctuation:
            text = re.sub(r"[^\w\s]", "", text)

        return text

    def _levenshtein_similarity(self, a: str, b: str) -> SimilarityScore:
        """Calculate Levenshtein similarity."""
        distance = Levenshtein.distance(a, b)
        max_len = max(len(a), len(b))
        return SimilarityScore(1.0 - (distance / max_len))

    def _jaro_winkler_similarity(self, a: str, b: str) -> SimilarityScore:
        """Calculate Jaro-Winkler similarity."""
        return SimilarityScore(jellyfish.jaro_winkler_similarity(a, b))

    def _cosine_similarity(self, a: str, b: str) -> SimilarityScore:
        """Calculate cosine similarity using TF-IDF vectors."""
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 3))
        try:
            tfidf_matrix = vectorizer.fit_transform([a, b])
            tfidf_matrix = cast(csr_matrix, tfidf_matrix)  # Explicit cast
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return SimilarityScore(float(similarity))
        except ValueError:
            # Handle edge cases where vectorization fails
            return SimilarityScore(0.0)

    def _jaccard_similarity(self, a: str, b: str) -> SimilarityScore:
        """Calculate Jaccard similarity using character bigrams."""

        def get_bigrams(text: str) -> Set[str]:
            return set(text[i : i + 2] for i in range(len(text) - 1))

        bigrams_a = get_bigrams(a)
        bigrams_b = get_bigrams(b)

        if not bigrams_a and not bigrams_b:
            return SimilarityScore(1.0)

        intersection = len(bigrams_a & bigrams_b)
        union = len(bigrams_a | bigrams_b)

        return SimilarityScore(intersection / union if union > 0 else 0.0)

    def _exact_similarity(self, a: str, b: str) -> SimilarityScore:
        """Exact string match."""
        return SimilarityScore(1.0 if a == b else 0.0)

    def _soundex_similarity(self, a: str, b: str) -> SimilarityScore:
        """Soundex-based similarity."""
        soundex_a = jellyfish.soundex(a)
        soundex_b = jellyfish.soundex(b)
        return SimilarityScore(1.0 if soundex_a == soundex_b else 0.0)

    def _metaphone_similarity(self, a: str, b: str) -> SimilarityScore:
        """Metaphone-based similarity."""
        metaphone_a = jellyfish.metaphone(a)
        metaphone_b = jellyfish.metaphone(b)
        return SimilarityScore(1.0 if metaphone_a == metaphone_b else 0.0)


# Convenience functions for backward compatibility
def levenshtein_similarity(s1: StringValue, s2: StringValue) -> float:
    """Calculate Levenshtein similarity (backward compatibility)."""
    comparator = StringComparator(method="levenshtein")
    return float(comparator.compare(s1, s2))


def jaro_winkler_similarity(s1: StringValue, s2: StringValue) -> float:
    """Calculate Jaro-Winkler similarity (backward compatibility)."""
    comparator = StringComparator(method="jaro_winkler")
    return float(comparator.compare(s1, s2))
