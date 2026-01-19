"""Transaction categorization using keyword matching."""

from data_processing import category

DEFAULT_CATEGORY = "MISC"


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
    categories = {cat_name: getattr(category, cat_name) for cat_name in category.all_category}

    for cat_name, keywords in categories.items():
        if any(keyword in data.lower() for keyword in keywords):
            return cat_name

    return DEFAULT_CATEGORY
