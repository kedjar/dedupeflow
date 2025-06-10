"""Main deduplication engine."""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterator, List, Optional, Tuple

import pandas as pd

from dedupeflow.comparators import DateComparator, NumericComparator, StringComparator
from dedupeflow.core.blocking import BlockingStrategy, StandardBlockingStrategy
from dedupeflow.core.matching import MatchingEngine
from dedupeflow.models import DedupeConfig, DedupeResults, FieldConfig, MatchResult
from dedupeflow.protocols import Comparator
from dedupeflow.strategies import ThresholdStrategy
from dedupeflow.types import FieldName, FieldScores, Record, RecordId, SimilarityScore

logger = logging.getLogger(__name__)


class DedupeEngine:
    """Main deduplication engine with configurable strategies."""

    def __init__(
        self,
        config: DedupeConfig,
        blocking_strategy: Optional[BlockingStrategy] = None,
    ):
        """Initialize the deduplication engine.

        Args:
            config: Deduplication configuration
            blocking_strategy: Optional custom blocking strategy
        """
        self.config = config
        self.blocking_strategy = blocking_strategy or StandardBlockingStrategy()

        # Initialize the matching engine
        self.matching_engine = MatchingEngine(
            field_configs=config.fields,
            global_threshold=config.global_threshold,
            require_all_fields=config.require_all_fields,
        )

    def deduplicate(
        self,
        data: pd.DataFrame,
        id_column: str = "id",
        progress_callback: Optional[callable] = None,
    ) -> DedupeResults:
        """Perform deduplication on a DataFrame."""
        start_time = time.time()
        matches: List[MatchResult] = []
        total_comparisons = 0

        logger.info(f"Starting deduplication of {len(data)} records")

        # Generate record pairs using blocking
        pairs = list(self._generate_pairs(data, id_column))

        for i, (id1, id2) in enumerate(pairs):
            record1 = data[data[id_column] == id1].iloc[0].to_dict()
            record2 = data[data[id_column] == id2].iloc[0].to_dict()

            # Compare the record pair using the matching engine
            match_result = self.matching_engine.compare_records(
                RecordId(id1), record1, RecordId(id2), record2
            )

            if match_result.is_match:
                matches.append(match_result)

            total_comparisons += 1

            # Progress callback
            if progress_callback and i % 1000 == 0:
                progress_callback(i + 1, len(pairs))

        execution_time = time.time() - start_time

        logger.info(
            f"Deduplication completed: {len(matches)} matches found "
            f"in {total_comparisons} comparisons ({execution_time:.2f}s)"
        )

        return DedupeResults(
            matches=matches,
            total_comparisons=total_comparisons,
            total_matches=len(matches),
            execution_time_seconds=execution_time,
            config_used=self.config,
        )

    def _generate_pairs(
        self, data: pd.DataFrame, id_column: str
    ) -> Iterator[Tuple[RecordId, RecordId]]:
        """Generate record pairs for comparison."""
        if self.config.enable_blocking and self.config.blocking_keys:
            return self.blocking_strategy.generate_pairs(
                data, self.config.blocking_keys, id_column
            )
        else:
            # Full cartesian product for small datasets
            records = data[id_column].tolist()
            for i in range(len(records)):
                for j in range(i + 1, len(records)):
                    yield RecordId(records[i]), RecordId(records[j])
