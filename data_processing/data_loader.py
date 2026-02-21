"""Domain model: Expense dataclass plus CATEGORY and IMPORTANCE enumerations."""

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


class Expense:
    """Single classified transaction read from ``data/processed_transactions.csv``.

    On construction, ``_determine_category_and_importance`` maps the item
    string to a ``CATEGORY`` and ``IMPORTANCE`` value via keyword matching.
    """

    def __init__(self, month: str, year: str, item: str, price: str) -> None:
        """Initialize an Expense and resolve its category and importance.

        Args:
            month: Month number as a string (for example, ``"3"`` for March).
            year: Four-digit year as a string (for example, ``"2025"``).
            item: Category label from the processed CSV (for example, ``"FOOD"``),
                used for keyword-based classification.
            price: Transaction amount as a string (unsigned, without leading dash).
        """
        self.month = month
        self.year = year
        self.item = item
        self.price = price
        self.category, self.importance = self._determine_category_and_importance()

    def _determine_category_and_importance(self) -> tuple[CATEGORY, IMPORTANCE]:
        """Map ``self.item`` to a ``CATEGORY`` / ``IMPORTANCE`` pair by keyword.

        Checks lowercase substrings in priority order. Returns
        ``CATEGORY.MISC`` / ``IMPORTANCE.NEEDS_REVIEW`` when no keyword matches.

        Returns:
            Two-tuple of ``(CATEGORY, IMPORTANCE)``.
        """
        item = self.item.lower()
        if "apartment" in item or "bills" in item or "renovation" in item:
            return CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL
        if "food" in item or "greenfood" in item:
            return CATEGORY.FOOD, IMPORTANCE.ESSENTIAL
        if "fuel" in item or "repairs" in item or "car" in item or "leasing" in item:
            return CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE
        if "transportation" in item:
            return CATEGORY.TRANSPORTATION, IMPORTANCE.HAVE_TO_HAVE
        if "groceries" in item or "coffee" in item or "catering" in item:
            return CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE
        if "animals" in item:
            return CATEGORY.ANIMALS, IMPORTANCE.HAVE_TO_HAVE
        if "self_development" in item or "book" in item:
            return CATEGORY.SELF_DEVELOPMENT, IMPORTANCE.NICE_TO_HAVE
        if "clothes" in item or "jewelry" in item:
            return CATEGORY.CLOTHES, IMPORTANCE.NICE_TO_HAVE
        if "entertainment" in item or "subscriptions" in item or "pcgames" in item:
            return CATEGORY.ENTERTAINMENT, IMPORTANCE.NICE_TO_HAVE
        if "shopping" in item or "electronic" in item:
            return CATEGORY.SHOPPING, IMPORTANCE.NICE_TO_HAVE
        if "investment" in item:
            return CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE
        if "pharmacy" in item or "cosmetics" in item or "insurance" in item or "sport" in item or "bike" in item:
            return CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE
        if "travel" in item:
            return CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE
        if "alcohol" in item or "fastfood" in item:
            return CATEGORY.SELF_DESTRUCTION, IMPORTANCE.SHOULDNT_HAVE
        if "kids" in item:
            return CATEGORY.KIDS, IMPORTANCE.HAVE_TO_HAVE
        return CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW

    def __repr__(self) -> str:
        """Return a comma-separated string suitable for CSV output.

        Format: ``month,year,item,category_value,price,importance_value``.
        """
        return f"{self.month},{self.year},{self.item},{self.category.value},{self.price},{self.importance.value}"
