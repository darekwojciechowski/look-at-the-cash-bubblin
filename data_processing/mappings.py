"""Transaction categorization using keyword matching.

Exports ``mappings()`` (the main categorization function) and
``DEFAULT_CATEGORY`` (the fallback string returned when no keyword matches).
"""

from data_processing import category

# Fallback value returned by mappings() when no keyword in _CATEGORY_MAP matches.
DEFAULT_CATEGORY = "MISC"

# Built once at import time — avoids rebuilding on every mappings() call.
_CATEGORY_MAP: dict[str, set[str]] = {cat_name: getattr(category, cat_name) for cat_name in category.all_category}


def mappings(data: str) -> str:
    """
    Categorize transaction data by matching keywords.

    Args:
        data: Transaction description text.

    Returns:
        Category name (e.g., "FOOD", "COFFEE") or "MISC" if no match.

    Examples:
        >>> mappings("biedronka groceries")
        'FOOD'
        >>> mappings("starbucks coffee")
        'COFFEE'
        >>> mappings("unknown transaction")
        'MISC'
    """
    for cat_name, keywords in _CATEGORY_MAP.items():
        if any(keyword in data.lower() for keyword in keywords):
            return cat_name

    return DEFAULT_CATEGORY
