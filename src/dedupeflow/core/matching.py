"""Matching engine for record comparison and scoring."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from dedupeflow.models import FieldConfig, MatchResult
    from dedupeflow.protocols import BaseMatchStrategy, Comparator

from dedupeflow.comparators import DateComparator, NumericComparator, StringComparator
from dedupeflow.strategies import ThresholdStrategy
from dedupeflow.types import FieldName, FieldScores, Record, RecordId, SimilarityScore

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Engine for comparing records and determining matches."""

    def __init__(
        self,
        field_configs: List[FieldConfig],
        match_strategy: Optional[BaseMatchStrategy] = None,
        global_threshold: float = 0.8,
        require_all_fields: bool = False,
    ):
        """Initialize the matching engine.

        Args:
            field_configs: List of field configurations for comparison
            match_strategy: Strategy for determining if records match
            global_threshold: Default threshold for matching
            require_all_fields: Whether all fields must be present for matching
        """
        self.field_configs = field_configs
        self.global_threshold = global_threshold
        self.require_all_fields = require_all_fields
        self.comparators = {}
        self._setup_comparators()
        self.match_strategy = match_strategy or ThresholdStrategy(
            threshold=global_threshold
        )

        # Initialize comparators for each field
        self.comparators: Dict[FieldName, Comparator] = {}
        self._setup_comparators()

    def get_statistics(self, results: list) -> dict:
        """Compute statistics from a list of MatchResult objects."""
        if not results:
            return {
                "total_comparisons": 0,
                "total_matches": 0,
                "match_rate": 0.0,
                "avg_score": 0.0,
            }
        total = len(results)
        matches = sum(1 for r in results if getattr(r, "is_match", False))
        avg_score = (
            sum(float(getattr(r, "overall_score", 0.0)) for r in results) / total
        )
        stats = {
            "total_comparisons": total,
            "total_matches": matches,
            "match_rate": matches / total if total else 0.0,
            "avg_score": avg_score,
        }
        # Add per-field average scores if available
        if hasattr(results[0], "field_scores"):
            for field in results[0].field_scores:
                field_avg = (
                    sum(float(r.field_scores.get(field, 0.0)) for r in results) / total
                )
                stats[f"{field}_avg_score"] = field_avg
        return stats

    def update_match_strategy(self, new_strategy):
        """Update the matching strategy."""
        self.match_strategy = new_strategy
        logger.debug(f"Updated match strategy to {new_strategy}")

    def get_field_weights(self):
        """Return a dictionary of field names to their weights."""
        return {str(fc.name): fc.weight for fc in self.field_configs}

    def _setup_comparators(self) -> None:
        """Set up comparators based on field configurations."""
        for field_config in self.field_configs:
            comparator = self._create_comparator(field_config)
            self.comparators[field_config.name] = comparator
            logger.debug(
                f"Created {field_config.comparator} comparator for field '{field_config.name}'"
            )

    def _create_comparator(self, field_config: FieldConfig) -> Comparator:
        """Create a comparator for a field configuration."""
        from dedupeflow.models import ComparatorType

        comparator_type = field_config.comparator
        method = field_config.method or "default"

        if comparator_type == ComparatorType.STRING:
            return StringComparator(
                method=method if method != "default" else "levenshtein",
                case_sensitive=False,
                normalize_whitespace=True,
            )
        elif comparator_type == ComparatorType.NUMERIC:
            return NumericComparator(
                method=method if method != "default" else "threshold",
                tolerance=field_config.tolerance or 0.0,
            )
        elif comparator_type == ComparatorType.DATE:
            return DateComparator(method=method if method != "default" else "exact")
        elif comparator_type == ComparatorType.EXACT:
            return StringComparator(method="exact")
        else:
            raise ValueError(f"Unknown comparator type: {comparator_type}")

    def compare_records(
        self,
        id1: str,
        record1: Record,
        id2: str,
        record2: Record,
    ) -> MatchResult:
        """Compare two records and return a detailed match result."""
        from dedupeflow.models import MatchResult

        field_scores: FieldScores = {}
        total_weight = 0.0
        weighted_score = 0.0
        missing_required_fields = []

        # Compare each configured field
        for field_config in self.field_configs:
            field_name = field_config.name

            # Check if field exists in both records
            field1_exists = field_name in record1 and record1[field_name] is not None
            field2_exists = field_name in record2 and record2[field_name] is not None

            if not field1_exists or not field2_exists:
                if field_config.required:
                    missing_required_fields.append(field_name)
                    field_scores[field_name] = SimilarityScore(0.0)

                    # If we require all fields and this is missing, short-circuit
                    if self.require_all_fields:
                        logger.debug(
                            f"Missing required field '{field_name}', skipping comparison"
                        )
                        break
                else:
                    # Optional field missing - assign neutral score
                    field_scores[field_name] = SimilarityScore(0.5)
                    weighted_score += 0.5 * field_config.weight
                    total_weight += field_config.weight
                continue

            # Get the comparator and compare values
            comparator = self.comparators[field_name]

            try:
                score = comparator.compare(record1[field_name], record2[field_name])
                field_scores[field_name] = score

                # Apply field-specific threshold if configured
                if field_config.threshold is not None:
                    if float(score) < field_config.threshold:
                        score = SimilarityScore(0.0)

                weighted_score += float(score) * field_config.weight
                total_weight += field_config.weight

                logger.debug(
                    f"Field '{field_name}': {record1[field_name]} vs {record2[field_name]} = {score:.3f}"
                )

            except Exception as e:
                logger.warning(f"Error comparing field '{field_name}': {e}")
                field_scores[field_name] = SimilarityScore(0.0)
                total_weight += field_config.weight

        # Calculate overall score
        if total_weight > 0:
            overall_score = SimilarityScore(weighted_score / total_weight)
        else:
            overall_score = SimilarityScore(0.0)

        # Determine if it's a match using the strategy
        is_match = self.match_strategy.is_match(overall_score)

        # Calculate confidence based on field coverage and score consistency
        confidence = self._calculate_confidence(
            field_scores, overall_score, missing_required_fields
        )

        logger.debug(
            f"Records {id1} vs {id2}: overall_score={overall_score:.3f}, "
            f"is_match={is_match}, confidence={confidence:.3f}"
        )

        return MatchResult(
            record1_id=id1,
            record2_id=id2,
            overall_score=overall_score,
            field_scores=field_scores,
            is_match=is_match,
            confidence=confidence,
        )

    def _calculate_confidence(
        self,
        field_scores: FieldScores,
        overall_score: SimilarityScore,
        missing_required_fields: List[FieldName],
    ) -> float:
        """Calculate confidence score for the match result."""
        if not field_scores:
            return 0.0

        # Base confidence is the overall score
        confidence = float(overall_score)

        # Reduce confidence for missing required fields
        if missing_required_fields:
            penalty = len(missing_required_fields) / len(self.field_configs)
            confidence *= 1.0 - penalty

        # Reduce confidence if scores are inconsistent (high variance)
        scores = [float(score) for score in field_scores.values()]
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            consistency_factor = max(0.5, 1.0 - variance)
            confidence *= consistency_factor

        # Boost confidence for very high scores
        if float(overall_score) > 0.9:
            confidence = min(1.0, confidence * 1.1)

        return max(0.0, min(1.0, confidence))

    def batch_compare(
        self, record_pairs: List[Tuple[str, Record, str, Record]]
    ) -> List[MatchResult]:
        """Compare multiple record pairs in batch."""
        from dedupeflow.models import MatchResult

        results = []

        for id1, record1, id2, record2 in record_pairs:
            try:
                result = self.compare_records(id1, record1, id2, record2)
                results.append(result)
            except Exception as e:
                logger.error(f"Error comparing records {id1} vs {id2}: {e}")
                # Create a failed match result
                results.append(
                    MatchResult(
                        record1_id=id1,
                        record2_id=id2,
                        overall_score=SimilarityScore(0.0),
                        field_scores={},
                        is_match=False,
                        confidence=0.0,
                    )
                )

        return results
