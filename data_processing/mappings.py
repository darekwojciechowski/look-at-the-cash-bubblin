"""Transaction categorization using keyword matching.

Exports ``mappings()`` (expense categorization) and
``lookup_income_category()`` (income categorization), plus the
``DEFAULT_CATEGORY`` and ``DEFAULT_INCOME_CATEGORY`` fallback strings.
"""

from collections.abc import Iterable, Mapping

from data_processing import category
from data_processing.category import EXPENSE_CATEGORIES as _CATEGORY_MAP

# Fallback value returned by mappings() when no keyword in _CATEGORY_MAP matches.
DEFAULT_CATEGORY = "MISC"

# Fallback value returned by lookup_income_category() when no income keyword matches.
DEFAULT_INCOME_CATEGORY = "INCOME_MISC"

# Income lookup map. Distinct from expense _CATEGORY_MAP so the two tracks
# never cross-contaminate (e.g. an expense row never resolves to "SALARY").
# Maps the public return label to its keyword frozenset in category.py.
_INCOME_MAP: dict[str, frozenset[str]] = {
    "SALARY": category.INCOME_SALARY,
    "SIDE_HUSTLE": category.INCOME_SIDE_HUSTLE,
    "EXTRA_INCOME": category.INCOME_EXTRA,
}


def _match_category(text: str, table: Mapping[str, Iterable[str]], default: str) -> str:
    """Return the first label in *table* whose keywords substring-match *text*.

    Args:
        text: Transaction description to classify (matched case-insensitively).
        table: Ordered label-to-keywords mapping; the first matching label wins.
        default: Fallback label returned when no keyword matches.

    Returns:
        The matching label, or *default* when nothing matches.
    """
    lowered = text.lower()
    for label, keywords in table.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return default


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
    return _match_category(data, _CATEGORY_MAP, DEFAULT_CATEGORY)


def lookup_income_category(description: str) -> str:
    """Categorize an income transaction description by keyword match.

    Args:
        description: Income transaction description text.

    Returns:
        One of ``"SALARY"``, ``"SIDE_HUSTLE"``, ``"EXTRA_INCOME"`` when a
        keyword matches, or ``"INCOME_MISC"`` as the fallback for manual review.
    """
    return _match_category(description, _INCOME_MAP, DEFAULT_INCOME_CATEGORY)
