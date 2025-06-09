import pytest
from dedupeflow.comparators.date import (
    date_similarity,
)

@pytest.mark.parametrize("a, b, expected", [
    ("2021-01-01", "2021-01-01", 1.0),
    ("2021-01-01", "2021-01-02", 0.0),
])
def test_date_similarity(a, b, expected):
    assert date_similarity(a, b) == expected    