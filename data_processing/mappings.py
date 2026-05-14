"""Transaction categorization using keyword matching.

Exports ``mappings()`` (expense categorization) and
``lookup_income_category()`` (income categorization), plus the
``DEFAULT_CATEGORY`` and ``DEFAULT_INCOME_CATEGORY`` fallback strings.
"""

from data_processing import category

# Fallback value returned by mappings() when no keyword in _CATEGORY_MAP matches.
DEFAULT_CATEGORY = "MISC"

# Fallback value returned by lookup_income_category() when no income keyword matches.
DEFAULT_INCOME_CATEGORY = "INCOME_MISC"

# Built once at import time — avoids rebuilding on every mappings() call.
_CATEGORY_MAP: dict[str, set[str]] = {cat_name: getattr(category, cat_name) for cat_name in category.all_category}

# Income lookup map. Distinct from expense _CATEGORY_MAP so the two tracks
# never cross-contaminate (e.g. an expense row never resolves to "SALARY").
# Maps the public return label to its keyword frozenset in category.py.
_INCOME_MAP: dict[str, frozenset[str]] = {
    "SALARY": category.INCOME_SALARY,
    "SIDE_HUSTLE": category.INCOME_SIDE_HUSTLE,
    "EXTRA_INCOME": category.INCOME_EXTRA,
}


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


def lookup_income_category(description: str) -> str:
    """Categorize an income transaction description by keyword match.

    Args:
        description: Income transaction description text.

    Returns:
        One of ``"SALARY"``, ``"SIDE_HUSTLE"``, ``"EXTRA_INCOME"`` when a
        keyword matches, or ``"INCOME_MISC"`` as the fallback for manual review.
    """
    lowered = description.lower()
    for label, keywords in _INCOME_MAP.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return DEFAULT_INCOME_CATEGORY
