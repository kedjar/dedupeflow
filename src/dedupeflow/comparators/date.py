def date_similarity(a: str, b: str) -> float:
    """Compute the similarity between two date strings."""
    if a == b:
        return 1.0
    return 0.0