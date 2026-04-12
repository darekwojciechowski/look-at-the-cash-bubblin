"""Domain model: Expense dataclass plus CATEGORY and IMPORTANCE enumerations."""

from dataclasses import dataclass, field
from enum import Enum


class CATEGORY(Enum):
    """Display categories used when rendering expenses in reports or spreadsheets."""

    TRANSPORTATION = "🚊 Transportation"
    CAR = "🚗 Car"
    EATING_OUT = "🦞 Eating Out"
    FOOD = "🥦 Food"
    CLOTHES = "👘 Clothes"
    TRAVEL = "🗺️ Travel"
    SHOPPING = "🛒 Shopping"
    APARTMENT = "🏯 Apartment"
    SELF_DEVELOPMENT = "🚀 Self Development"
    ANIMALS = "🐺 Animals"
    ENTERTAINMENT = "🎥 Entertainment"
    INVESTMENTS = "💸 Investments"
    CARE = "🛀🏾 Care"
    SELF_DESTRUCTION = "☠ Self Destruction"
    KIDS = "🧸 Kids"
    MISC = "Misc"


class IMPORTANCE(Enum):
    """Priority scale for classifying whether an expense was necessary."""

    SHOULDNT_HAVE = "Shouldn't Have"
    NICE_TO_HAVE = "Nice to Have"
    HAVE_TO_HAVE = "Have to Have"
    ESSENTIAL = "Essential"
    NEEDS_REVIEW = "Needs Review"


# Each rule groups all keywords that map to the same (CATEGORY, IMPORTANCE) pair.
# Order is significant: the first matching rule wins.
_CATEGORY_RULES: list[tuple[CATEGORY, IMPORTANCE, frozenset[str]]] = [
    (CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL, frozenset({"apartment", "bills", "renovation"})),
    (CATEGORY.FOOD, IMPORTANCE.ESSENTIAL, frozenset({"food", "greenfood"})),
    (CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE, frozenset({"fuel", "repairs", "car", "leasing"})),
    (CATEGORY.TRANSPORTATION, IMPORTANCE.HAVE_TO_HAVE, frozenset({"transportation"})),
    (CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE, frozenset({"groceries", "coffee", "catering"})),
    (CATEGORY.ANIMALS, IMPORTANCE.HAVE_TO_HAVE, frozenset({"animals"})),
    (CATEGORY.SELF_DEVELOPMENT, IMPORTANCE.NICE_TO_HAVE, frozenset({"self_development", "book"})),
    (CATEGORY.CLOTHES, IMPORTANCE.NICE_TO_HAVE, frozenset({"clothes", "jewelry"})),
    (CATEGORY.ENTERTAINMENT, IMPORTANCE.NICE_TO_HAVE, frozenset({"entertainment", "subscriptions", "pcgames"})),
    (CATEGORY.SHOPPING, IMPORTANCE.NICE_TO_HAVE, frozenset({"shopping", "electronic"})),
    (CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE, frozenset({"investment"})),
    (CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE, frozenset({"pharmacy", "cosmetics", "insurance", "sport", "bike"})),
    (CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE, frozenset({"travel"})),
    (CATEGORY.SELF_DESTRUCTION, IMPORTANCE.SHOULDNT_HAVE, frozenset({"alcohol", "fastfood"})),
    (CATEGORY.KIDS, IMPORTANCE.HAVE_TO_HAVE, frozenset({"kids"})),
]


@dataclass
class Expense:
    """Single classified transaction read from ``data/processed_transactions.csv``.

    On construction, ``category`` and ``importance`` are computed from
    ``item`` by keyword matching against ``_CATEGORY_RULES``.
    """

    month: str
    year: str
    item: str
    price: str
    category: CATEGORY = field(init=False, repr=True)
    importance: IMPORTANCE = field(init=False, repr=True)

    def __post_init__(self) -> None:
        """Set ``category`` and ``importance`` based on ``item`` after construction."""
        self.category, self.importance = self._determine_category_and_importance()

    def _determine_category_and_importance(self) -> tuple[CATEGORY, IMPORTANCE]:
        """Return the ``CATEGORY`` and ``IMPORTANCE`` for ``self.item``.

        Falls back to ``CATEGORY.MISC`` / ``IMPORTANCE.NEEDS_REVIEW`` when no
        rule matches.

        Returns:
            Two-tuple of ``(CATEGORY, IMPORTANCE)``.
        """
        item = self.item.lower()
        for category, importance, keywords in _CATEGORY_RULES:
            if any(kw in item for kw in keywords):
                return category, importance
        return CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW

    def to_csv_row(self) -> str:
        """Return a comma-separated string suitable for CSV output.

        Format: ``month,year,item,category_value,price,importance_value``.
        """
        return f"{self.month},{self.year},{self.item},{self.category.value},{self.price},{self.importance.value}"
