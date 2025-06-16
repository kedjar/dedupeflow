"""Shared test fixtures and utilities for DedupeFlow tests."""

import logging
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytest
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

from dedupeflow.models import ComparatorType, DedupeConfig, FieldConfig
from dedupeflow.types import FieldName, SimilarityScore

# Install rich traceback handler for better error formatting
install(show_locals=True)

# Global console instance for rich output
console = Console()


def setup_rich_logging(
    level: str = "INFO", show_time: bool = True, show_path: bool = False
):
    """Set up rich logging for tests.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        show_time: Whether to show timestamps
        show_path: Whether to show file paths
    """
    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )

    # Set up formatting
    rich_handler.setFormatter(
        logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]",
        )
    )

    # Configure root logger
    root_logger.addHandler(rich_handler)
    root_logger.setLevel(getattr(logging, level.upper()))

    return root_logger


def get_test_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for tests with rich formatting.

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        logging.Logger: Configured logger instance
    """
    if name is None:
        # Get the calling module's name
        import inspect

        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            name = frame.f_back.f_globals.get("__name__", "test")
        else:
            name = "test"

    logger = logging.getLogger(name)

    # Ensure the logger uses our rich handler
    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        # If no rich handler exists, set up logging
        if not logging.getLogger().handlers:
            setup_rich_logging()

    return logger


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Automatically set up rich logging for all tests."""
    logger = setup_rich_logging(level="DEBUG", show_time=True, show_path=False)
    logger.info("[bold green]🚀 Test session started with rich logging[/bold green]")
    yield logger
    logger.info("[bold blue]✅ Test session completed[/bold blue]")


@pytest.fixture
def test_logger():
    """Provide a test logger for individual tests."""
    return get_test_logger()


@pytest.fixture
def rich_console():
    """Provide the rich console for tests that need direct access."""
    return console


def log_test_data(
    data: Any, title: str = "Test Data", logger: Optional[logging.Logger] = None
):
    """Log test data in a formatted way using rich.

    Args:
        data: Data to log
        title: Title for the log entry
        logger: Logger instance (if None, creates new one)
    """
    if logger is None:
        logger = get_test_logger()

    logger.info(f"[bold cyan]{title}[/bold cyan]")

    if isinstance(data, (dict, list, tuple)):
        from rich.pretty import Pretty

        console.print(Pretty(data))
    elif isinstance(data, pd.DataFrame):
        logger.info(f"DataFrame shape: {data.shape}")
        console.print(data.to_string())
    else:
        logger.info(f"Value: {data} (type: {type(data).__name__})")


def log_comparison_result(
    val1: Any,
    val2: Any,
    result: Any,
    expected: Any = None,
    test_name: str = "Comparison",
    logger: Optional[logging.Logger] = None,
):
    """Log comparison results in a formatted way.

    Args:
        val1: First comparison value
        val2: Second comparison value
        result: Actual result
        expected: Expected result (optional)
        test_name: Name of the test
        logger: Logger instance
    """
    if logger is None:
        logger = get_test_logger()

    logger.info(f"[bold yellow]{test_name}[/bold yellow]")
    logger.info(f"  Value 1: [green]{val1}[/green] ({type(val1).__name__})")
    logger.info(f"  Value 2: [green]{val2}[/green] ({type(val2).__name__})")
    logger.info(f"  Result:  [blue]{result}[/blue]")

    if expected is not None:
        status = "[green]✅ PASS[/green]" if result == expected else "[red]❌ FAIL[/red]"
        logger.info(f"  Expected: [blue]{expected}[/blue] {status}")


def create_record(**kwargs) -> Dict[FieldName, Any]:
    """Helper function to create properly typed records for testing.

    Args:
        **kwargs: Field names and values as keyword arguments

    Returns:
        Dict[FieldName, Any]: A properly typed record dictionary

    Example:
        >>> record = create_record(name="John Smith", email="john@test.com")
        >>> assert record[FieldName("name")] == "John Smith"
    """
    return {FieldName(k): v for k, v in kwargs.items()}


@pytest.fixture
def sample_record_pair():
    """Sample record pair for testing."""
    record1 = create_record(
        name="John Smith", email="john.smith@email.com", age=30, score=85.5
    )

    record2 = create_record(
        name="Jon Smith",  # Similar
        email="john.smith@email.com",  # Same
        age=30,  # Same
        score=86.0,  # Close
    )

    return record1, record2


@pytest.fixture
def sample_field_configs():
    """Sample field configurations for testing."""
    from dedupeflow.models import ComparatorType, FieldConfig

    return [
        FieldConfig(
            name=FieldName("name"),
            comparator=ComparatorType.STRING,
            weight=0.4,
            method="levenshtein",
        ),
        FieldConfig(
            name=FieldName("email"),
            comparator=ComparatorType.STRING,
            weight=0.3,
            method="exact",
        ),
        FieldConfig(
            name=FieldName("age"),
            comparator=ComparatorType.NUMERIC,
            weight=0.2,
            tolerance=1.0,
        ),
        FieldConfig(
            name=FieldName("score"),
            comparator=ComparatorType.NUMERIC,
            weight=0.1,
            method="percentage",
        ),
    ]


@pytest.fixture
def sample_matching_engine(sample_field_configs):
    """Pre-configured matching engine for testing."""
    from dedupeflow.core.matching import MatchingEngine

    return MatchingEngine(sample_field_configs, global_threshold=0.8)


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
                name=FieldName("name"),
                comparator=ComparatorType.STRING,
                weight=0.4,
                method="levenshtein",
                required=True,
            ),
            FieldConfig(
                name=FieldName("email"),
                comparator=ComparatorType.STRING,
                weight=0.3,
                method="exact",
                required=True,
            ),
            FieldConfig(
                name=FieldName("phone"),
                comparator=ComparatorType.STRING,
                weight=0.2,
                method="exact",
                required=False,
            ),
            FieldConfig(
                name=FieldName("income"),
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
        blocking_keys=[FieldName("name")],
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
