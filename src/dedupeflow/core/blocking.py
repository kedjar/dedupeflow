"""Blocking strategies for efficient record pair generation."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Iterator, List, Set, Tuple, Union

import pandas as pd

from dedupeflow.types import FieldName, RecordId


class BlockingStrategy(ABC):
    """Abstract base class for blocking strategies."""

    @abstractmethod
    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate record pairs for comparison.

        Args:
            data: DataFrame containing records
            blocking_keys: List of field names to use for blocking
            id_column: Column name containing record IDs

        Yields:
            Tuples of record IDs to compare
        """
        pass


class StandardBlockingStrategy(BlockingStrategy):
    """Standard blocking strategy using exact key matching."""

    def __init__(self, max_block_size: int = 10000):
        """Initialize the blocking strategy.

        Args:
            max_block_size: Maximum number of records in a single block
        """
        self.max_block_size = max_block_size

    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate pairs using standard blocking."""
        # Create blocking key for each record
        blocks: Dict[str, List[RecordId]] = defaultdict(list)

        for _, row in data.iterrows():
            block_key = self._create_block_key(row, blocking_keys)
            if block_key:  # Only add if blocking key is not empty
                blocks[block_key].append(RecordId(row[id_column]))

        # Generate pairs within each block
        for block_key, record_ids in blocks.items():
            if len(record_ids) > self.max_block_size:
                # Skip overly large blocks to avoid performance issues
                continue

            # Generate all pairs within this block
            for i in range(len(record_ids)):
                for j in range(i + 1, len(record_ids)):
                    yield record_ids[i], record_ids[j]

    def _create_block_key(self, row: pd.Series, blocking_keys: List[FieldName]) -> str:
        """Create a blocking key from the specified fields."""
        key_parts = []

        for field_name in blocking_keys:
            if field_name in row and pd.notna(row[field_name]):
                # Normalize the value
                value = str(row[field_name]).strip().lower()
                key_parts.append(value)
            else:
                # Missing values get empty string
                key_parts.append("")

        return "|".join(key_parts)


class SoundexBlockingStrategy(BlockingStrategy):
    """Blocking strategy using Soundex algorithm for phonetic matching."""

    def __init__(self, max_block_size: int = 10000):
        """Initialize the Soundex blocking strategy.

        Args:
            max_block_size: Maximum number of records in a single block
        """
        self.max_block_size = max_block_size

    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate pairs using Soundex blocking."""
        try:
            import jellyfish
        except ImportError:
            raise ImportError("jellyfish package required for SoundexBlockingStrategy")

        blocks: Dict[str, List[RecordId]] = defaultdict(list)

        for _, row in data.iterrows():
            block_key = self._create_soundex_key(row, blocking_keys, jellyfish)
            if block_key:
                blocks[block_key].append(RecordId(row[id_column]))

        # Generate pairs within each block
        for block_key, record_ids in blocks.items():
            if len(record_ids) > self.max_block_size:
                continue

            for i in range(len(record_ids)):
                for j in range(i + 1, len(record_ids)):
                    yield record_ids[i], record_ids[j]

    def _create_soundex_key(
        self, row: pd.Series, blocking_keys: List[FieldName], jellyfish_module
    ) -> str:
        """Create a Soundex-based blocking key."""
        key_parts = []

        for field_name in blocking_keys:
            if field_name in row and pd.notna(row[field_name]):
                value = str(row[field_name]).strip()
                if value:
                    soundex_code = jellyfish_module.soundex(value)
                    key_parts.append(soundex_code)
                else:
                    key_parts.append("")
            else:
                key_parts.append("")

        return "|".join(key_parts)


class NGramBlockingStrategy(BlockingStrategy):
    """Blocking strategy using n-gram tokens for fuzzy matching."""

    def __init__(self, n: int = 2, max_block_size: int = 10000, min_tokens: int = 1):
        """Initialize the n-gram blocking strategy.

        Args:
            n: Size of n-grams to generate
            max_block_size: Maximum number of records in a single block
            min_tokens: Minimum number of tokens required for blocking
        """
        self.n = n
        self.max_block_size = max_block_size
        self.min_tokens = min_tokens

    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate pairs using n-gram blocking."""
        # Map from n-gram to list of record IDs
        ngram_to_records: Dict[str, Set[RecordId]] = defaultdict(set)

        for _, row in data.iterrows():
            record_id = RecordId(row[id_column])
            ngrams = self._extract_ngrams(row, blocking_keys)

            if len(ngrams) >= self.min_tokens:
                for ngram in ngrams:
                    ngram_to_records[ngram].add(record_id)

        # Generate pairs from records that share n-grams
        seen_pairs: Set[Tuple[RecordId, RecordId]] = set()

        for ngram, record_ids in ngram_to_records.items():
            if len(record_ids) > self.max_block_size:
                continue

            record_list = list(record_ids)
            for i in range(len(record_list)):
                for j in range(i + 1, len(record_list)):
                    pair = (record_list[i], record_list[j])
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        yield pair

    def _extract_ngrams(
        self, row: pd.Series, blocking_keys: List[FieldName]
    ) -> Set[str]:
        """Extract n-grams from the blocking key fields."""
        ngrams = set()

        for field_name in blocking_keys:
            if field_name in row and pd.notna(row[field_name]):
                value = str(row[field_name]).strip().lower()
                if len(value) >= self.n:
                    # Generate character n-grams
                    for i in range(len(value) - self.n + 1):
                        ngram = value[i : i + self.n]
                        ngrams.add(ngram)

        return ngrams


class CanopyBlockingStrategy(BlockingStrategy):
    """Canopy clustering-based blocking strategy for large datasets."""

    def __init__(
        self,
        loose_threshold: float = 0.6,
        tight_threshold: float = 0.8,
        max_canopy_size: int = 1000,
    ):
        """Initialize the canopy blocking strategy.

        Args:
            loose_threshold: Threshold for including records in canopy
            tight_threshold: Threshold for removing records from consideration
            max_canopy_size: Maximum size of a single canopy
        """
        self.loose_threshold = loose_threshold
        self.tight_threshold = tight_threshold
        self.max_canopy_size = max_canopy_size

    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate pairs using canopy clustering."""
        # Create canopies
        canopies = self._create_canopies(data, blocking_keys, id_column)

        # Generate pairs within each canopy
        for canopy in canopies:
            if len(canopy) > self.max_canopy_size:
                continue

            for i in range(len(canopy)):
                for j in range(i + 1, len(canopy)):
                    yield canopy[i], canopy[j]

    def _create_canopies(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str
    ) -> List[List[RecordId]]:
        """Create canopies using the canopy clustering algorithm."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated similarity calculations
        canopies = []
        remaining_records = data.copy()

        while len(remaining_records) > 0:
            # Pick a random center
            center_idx = remaining_records.index[0]
            center_record = remaining_records.loc[center_idx]

            # Create new canopy
            canopy = [RecordId(center_record[id_column])]
            records_to_remove = [center_idx]

            # Find records similar to center
            for idx, row in remaining_records.iterrows():
                if idx == center_idx:
                    continue

                similarity = self._calculate_similarity(
                    center_record, row, blocking_keys
                )

                if similarity >= self.loose_threshold:
                    canopy.append(RecordId(row[id_column]))

                    if similarity >= self.tight_threshold:
                        records_to_remove.append(idx)

            canopies.append(canopy)
            remaining_records = remaining_records.drop(records_to_remove)

        return canopies

    def _calculate_similarity(
        self, record1: pd.Series, record2: pd.Series, blocking_keys: List[FieldName]
    ) -> float:
        """Calculate simple similarity between two records."""
        similarities = []

        for field_name in blocking_keys:
            if field_name in record1 and field_name in record2:
                val1 = str(record1[field_name]).lower().strip()
                val2 = str(record2[field_name]).lower().strip()

                if val1 == val2:
                    similarities.append(1.0)
                elif val1 and val2:
                    # Simple Jaccard similarity using character bigrams
                    bigrams1 = set(val1[i : i + 2] for i in range(len(val1) - 1))
                    bigrams2 = set(val2[i : i + 2] for i in range(len(val2) - 1))

                    if bigrams1 or bigrams2:
                        jaccard = len(bigrams1 & bigrams2) / len(bigrams1 | bigrams2)
                        similarities.append(jaccard)
                    else:
                        similarities.append(0.0)
                else:
                    similarities.append(0.0)

        return sum(similarities) / len(similarities) if similarities else 0.0


class HashBlockingStrategy(BlockingStrategy):
    """Hash-based blocking strategy with configurable hash functions."""

    def __init__(self, hash_functions: List[str] = None, max_block_size: int = 10000):
        """Initialize the hash blocking strategy.

        Args:
            hash_functions: List of hash function names to use
            max_block_size: Maximum number of records in a single block
        """
        self.hash_functions = hash_functions or ["first_3_chars", "last_3_chars"]
        self.max_block_size = max_block_size

    def generate_pairs(
        self, data: pd.DataFrame, blocking_keys: List[FieldName], id_column: str = "id"
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate pairs using hash-based blocking."""
        # Create blocks for each hash function
        all_blocks: Dict[str, Set[RecordId]] = defaultdict(set)

        for _, row in data.iterrows():
            record_id = RecordId(row[id_column])

            for hash_func_name in self.hash_functions:
                hash_key = self._apply_hash_function(row, blocking_keys, hash_func_name)
                if hash_key:
                    block_key = f"{hash_func_name}:{hash_key}"
                    all_blocks[block_key].add(record_id)

        # Generate pairs within each block
        seen_pairs: Set[Tuple[RecordId, RecordId]] = set()

        for block_key, record_ids in all_blocks.items():
            if len(record_ids) > self.max_block_size:
                continue

            record_list = list(record_ids)
            for i in range(len(record_list)):
                for j in range(i + 1, len(record_list)):
                    pair = (record_list[i], record_list[j])
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        yield pair

    def _apply_hash_function(
        self, row: pd.Series, blocking_keys: List[FieldName], hash_func_name: str
    ) -> str:
        """Apply a hash function to the blocking keys."""
        # Combine all blocking key values
        combined_value = ""
        for field_name in blocking_keys:
            if field_name in row and pd.notna(row[field_name]):
                combined_value += str(row[field_name]).strip().lower()

        if not combined_value:
            return ""

        # Apply the specified hash function
        if hash_func_name == "first_3_chars":
            return combined_value[:3]
        elif hash_func_name == "last_3_chars":
            return combined_value[-3:]
        elif hash_func_name == "md5_prefix":
            return hashlib.md5(combined_value.encode()).hexdigest()[:8]
        elif hash_func_name == "length_bucket":
            return f"len_{len(combined_value) // 5 * 5}"  # Group by length buckets of 5
        else:
            # Default to first 3 characters
            return combined_value[:3]
