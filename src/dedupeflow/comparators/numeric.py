"""Numeric comparator functions for record linkage."""

from typing import Optional, Union


def numeric_similarity(
    a: Optional[Union[int, float]], 
    b: Optional[Union[int, float]], 
    tolerance: float = 0.0
) -> float:
    """
    Calculate the similarity between two numeric values.
    
    Returns 1.0 for identical values or values within the specified tolerance,
    and 0.0 otherwise. For more sophisticated numeric comparison, consider
    using relative or scaled distance metrics.
    
    Args:
        a: First numeric value to compare.
        b: Second numeric value to compare.
        tolerance: Absolute tolerance for considering values equal (default: 0.0).
    
    Returns:
        float: Similarity score of either 0.0 or 1.0.
    
    Examples:
        >>> numeric_similarity(100, 100)
        1.0
        >>> numeric_similarity(100.0, 100.1, tolerance=0.1)
        1.0
        >>> numeric_similarity(100, 200)
        0.0
        >>> numeric_similarity(None, None)
        1.0
        >>> numeric_similarity(100, None)
        0.0
        >>> numeric_similarity(99.95, 100.05, tolerance=0.1)
        1.0
    """
    # Handle None values
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    
    # Convert to float for comparison
    try:
        a_float = float(a)
        b_float = float(b)
    except (ValueError, TypeError):
        return 0.0
    
    # Check if values are within tolerance
    if abs(a_float - b_float) <= tolerance:
        return 1.0
    
    return 0.0