import pytest
from dedupeflow.comparators.numeric import (
    numeric_similarity,
)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (1.0, 1.0, 1.0),
        (1.0, 2.0, 0.0),
    ],
)
def test_numeric_similarity(a, b, expected):
    assert numeric_similarity(a, b) == expected
