"""Shared pytest fixtures for DedupeFlow tests."""

from datetime import date, datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
import pytest

from dedupeflow.models import ComparatorType, DedupeConfig, FieldConfig
from dedupeflow.types import SimilarityScore


@pytest.fixture
def sample_string_pairs() -> List[Tuple[str, str]]:
    """Return sample string pairs for testing comparators."""
    return [
        ("John Smith", "Jon Smith"),
        ("NYC", "New York City"),
        ("California", "Calfornia"),
        ("123 Main St", "123 Main Street"),
        ("O'Reilly", "OReilly"),
        ("", ""),
        ("Test", ""),
        ("", "Test"),
    ]


@pytest.fixture
def sample_numeric_pairs() -> List[Tuple[float, float]]:
    """Return sample numeric pairs for testing."""
    return [
        (10.0, 10.0),
        (10.0, 11.0),
        (100.0, 110.0),
        (1000.0, 900.0),
        (42.5, 42.55),
        (0.0, 0.0),
        (-10.5, -10.5),
        (1.0, 2.0),
    ]


@pytest.fixture
def sample_date_pairs() -> List[Tuple[str, str]]:
    """Return sample date pairs for testing."""
    return [
        ("2023-01-01", "2023-01-01"),
        ("2023-01-01", "2023-01-02"),
        ("2023-01-01", "2023-02-01"),
        ("Jan 1, 2023", "January 1, 2023"),
        ("01/01/2023", "2023-01-01"),
        ("2023-12-25", "2023-12-25"),
        ("15/03/2023", "2023-03-15"),  # Different formats
    ]


@pytest.fixture
def sample_records() -> pd.DataFrame:
    """Return a sample DataFrame for integration testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6],
            "name": [
                "John Smith",
                "Jon Smith",  # Similar to #1
                "Jane Doe",
                "Robert Johnson",
                "Maria Garcia",
                "David Lee",
            ],
            "email": [
                "john.smith@email.com",
                "j.smith@email.com",  # Similar to #1
                "jane.doe@email.com",
                "robert.johnson@email.com",
                "maria.garcia@email.com",
                "david.lee@email.com",
            ],
            "phone": [
                "(555) 123-4567",
                "555-123-4567",  # Similar to #1
                "(555) 987-6543",
                "(555) 555-1234",
                "(555) 444-5678",
                "(555) 777-8899",
            ],
            "address": [
                "123 Main St",
                "123 Main Street",  # Similar to #1
                "456 Oak Ave",
                "789 Pine Rd",
                "101 Maple Dr",
                "202 Cedar Ln",
            ],
            "birth_date": [
                "1980-05-15",
                "1980-05-15",  # Same as #1
                "1992-11-30",
                "1975-03-22",
                "1988-07-10",
                "1995-09-05",
            ],
            "income": [50000, 51000, 65000, 48000, 72000, 55000],
        }
    )


@pytest.fixture
def sample_config() -> DedupeConfig:
    """Return a sample deduplication configuration."""
    return DedupeConfig(
        fields=[
            FieldConfig(
                name="name",
                comparator=ComparatorType.STRING,
                weight=0.4,
                method="levenshtein",
                required=True,
            ),
            FieldConfig(
                name="email",
                comparator=ComparatorType.STRING,
                weight=0.3,
                method="exact",
                required=True,
            ),
            FieldConfig(
                name="phone",
                comparator=ComparatorType.STRING,
                weight=0.2,
                method="exact",
                required=False,
            ),
            FieldConfig(
                name="income",
                comparator=ComparatorType.NUMERIC,
                weight=0.1,
                method="threshold",
                tolerance=1000.0,
                required=False,
            ),
        ],
        global_threshold=0.8,
        require_all_fields=False,
        enable_blocking=True,
        blocking_keys=["name"],
    )


@pytest.fixture
def duplicate_records() -> pd.DataFrame:
    """Return DataFrame with known duplicates for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["John Smith", "John Smith", "Jane Doe", "Jane M. Doe"],
            "email": [
                "john@test.com",
                "john@test.com",
                "jane@test.com",
                "jane@test.com",
            ],
            "age": [30, 30, 25, 25],
        }
    )


@pytest.fixture
def mixed_data_types_records() -> pd.DataFrame:
    """Return DataFrame with mixed data types for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "score": [85.5, 90.0, 88.2, 92.1],
            "birth_date": [
                date(1990, 1, 15),
                "1985-06-22",
                datetime(1992, 12, 3),
                "03/14/1988",
            ],
            "is_active": [True, False, True, True],
            "notes": ["Good student", None, "Excellent", ""],
        }
    )
