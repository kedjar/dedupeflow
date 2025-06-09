"""Date comparator functions for record linkage."""

from __future__ import annotations
from typing import Optional, Union
from datetime import datetime, date


def date_similarity(
    a: Optional[Union[str, datetime, date]], 
    b: Optional[Union[str, datetime, date]],
    format_strings: Optional[list[str]] = None
) -> float:
    """
    Calculate the similarity between two date values.
    
    Compares dates by parsing string representations or using datetime objects
    directly. Returns 1.0 for identical dates and 0.0 otherwise.
    
    Args:
        a: First date to compare (string, datetime, or date object).
        b: Second date to compare (string, datetime, or date object).
        format_strings: List of date format strings to try when parsing. 
        Defaults to common formats if None.
    
    Returns:
        float: Similarity score of either 0.0 or 1.0.
    
    Examples:
        >>> date_similarity("2023-01-15", "2023-01-15")
        1.0
        >>> date_similarity("01/15/2023", "2023-01-15")
        1.0
        >>> date_similarity("2023-01-15", "2023-01-16")
        0.0
        >>> date_similarity(None, None)
        1.0
        >>> date_similarity("2023-01-15", None)
        0.0
        >>> from datetime import date
        >>> date_similarity(date(2023, 1, 15), "2023-01-15")
        1.0
    """
    # Handle None values
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    
    # Default format strings to try
    if format_strings is None:
        format_strings = [
            "%Y-%m-%d",        # 2023-01-15
            "%m/%d/%Y",        # 01/15/2023
            "%d/%m/%Y",        # 15/01/2023
            "%Y/%m/%d",        # 2023/01/15
            "%m-%d-%Y",        # 01-15-2023
            "%d-%m-%Y",        # 15-01-2023
            "%Y%m%d",          # 20230115
            "%m/%d/%y",        # 01/15/23
            "%d/%m/%y",        # 15/01/23
            "%b %d, %Y",       # Jan 15, 2023
            "%B %d, %Y",       # January 15, 2023
            "%d %b %Y",        # 15 Jan 2023
            "%d %B %Y",        # 15 January 2023
        ]
    
    def parse_date(value: Union[str, datetime, date]) -> Optional[date]:
        """Parse a date value into a date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        
        if not isinstance(value, str):
            return None
        
        # Clean the string
        value = value.strip()
        if not value:
            return None
        
        # Try each format string
        for fmt in format_strings:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.date()
            except ValueError:
                continue
        
        return None
    
    # Parse both dates
    date_a = parse_date(a)
    date_b = parse_date(b)
    
    # If either couldn't be parsed, return 0.0
    if date_a is None or date_b is None:
        return 0.0
    
    # Compare the dates
    return 1.0 if date_a == date_b else 0.0