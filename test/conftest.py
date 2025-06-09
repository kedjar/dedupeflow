"""Shared pytest fixtures for record linkage tests."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_string_pairs():
    """Return sample string pairs for testing comparators."""
    return [
        ("John Smith", "Jon Smith"),
        ("NYC", "New York City"),
        ("California", "Calfornia"),
        ("123 Main St", "123 Main Street"),
        ("O'Reilly", "OReilly"),
    ]


@pytest.fixture
def sample_numeric_pairs():
    """Return sample numeric pairs for testing."""
    return [
        (10, 10),
        (10, 11),
        (100, 110),
        (1000, 900),
        (42.5, 42.55),
    ]


@pytest.fixture
def sample_date_pairs():
    """Return sample date pairs for testing."""
    return [
        ("2023-01-01", "2023-01-01"),
        ("2023-01-01", "2023-01-02"),
        ("2023-01-01", "2023-02-01"),
        ("Jan 1, 2023", "January 1, 2023"),
        ("01/01/2023", "2023-01-01"),
    ]


@pytest.fixture
def sample_records():
    """Return a sample DataFrame for integration testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["John Smith", "Jane Doe", "Robert Johnson", "Maria Garcia", "David Lee"],
        "address": ["123 Main St", "456 Oak Ave", "789 Pine Rd", "101 Maple Dr", "202 Cedar Ln"],
        "birth_date": ["1980-05-15", "1992-11-30", "1975-03-22", "1988-07-10", "1995-09-05"],
        "income": [50000, 65000, 48000, 72000, 55000],
    })