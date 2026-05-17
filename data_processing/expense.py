"""Domain model: the ``Expense`` dataclass, the ``CATEGORY``/``IMPORTANCE``
enumerations, the ``ExpenseClassifier``, and the ``get_data`` CSV loader that
reconstructs ``Expense`` objects from a processed transactions file.
"""

import csv
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from data_processing import category
from data_processing.mappings import DEFAULT_CATEGORY


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


class ExpenseClassifier:
    """Stateless keyword classifier: maps free-text to ``(CATEGORY, IMPORTANCE)``.

    Wraps ``_CATEGORY_RULES``. The first rule with a keyword substring-matching
    the (lowercased) text wins; unmatched text falls back to
    ``CATEGORY.MISC`` / ``IMPORTANCE.NEEDS_REVIEW``.
    """

    def classify(self, text: str) -> tuple[CATEGORY, IMPORTANCE]:
        """Return the ``(CATEGORY, IMPORTANCE)`` pair for *text*.

        Args:
            text: Free-text transaction description or category label.

        Returns:
            Two-tuple of ``(CATEGORY, IMPORTANCE)``; the MISC/NEEDS_REVIEW
            fallback when no rule matches.
        """
        lowered = text.lower()
        for rule_category, rule_importance, keywords in _CATEGORY_RULES:
            if any(kw in lowered for kw in keywords):
                return rule_category, rule_importance
        return CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW


# Built once at import — the classifier is stateless, so a single shared
# instance serves every Expense construction and the CATEGORY_DISPLAY map.
_DEFAULT_CLASSIFIER = ExpenseClassifier()


# The single authoritative bridge between the pipeline's classification output
# (the string labels mappings() returns) and the display CATEGORY/IMPORTANCE.
# Domain = every value mappings() can produce: the names in category.all_category
# plus the DEFAULT_CATEGORY fallback. Precomputing it makes the contract explicit
# and mypy-checked instead of relying on label/keyword coincidence at export time.
CATEGORY_DISPLAY: dict[str, tuple[CATEGORY, IMPORTANCE]] = {
    name: _DEFAULT_CLASSIFIER.classify(name) for name in sorted(set(category.all_category) | {DEFAULT_CATEGORY})
}


@dataclass
class Expense:
    """Single classified transaction read from ``data/processed_transactions.csv``.

    On construction, ``category`` and ``importance`` are computed from
    ``item`` by keyword matching via ``_DEFAULT_CLASSIFIER``.
    """

    month: int | str
    year: int | str
    item: str
    price: int | str
    category: CATEGORY = field(init=False, repr=True)
    importance: IMPORTANCE = field(init=False, repr=True)

    def __post_init__(self) -> None:
        """Normalize numeric fields to ``str`` and derive category/importance.

        Callers (CSV rows, test fixtures) pass ``month``/``year``/``price`` as
        either ``int`` or ``str``; they are coerced to ``str`` here so every
        ``Expense`` instance has homogeneous string fields.
        """
        self.month = str(self.month)
        self.year = str(self.year)
        self.price = str(self.price)
        self.category, self.importance = _DEFAULT_CLASSIFIER.classify(self.item)


def get_data(path: Path = Path("data/processed_transactions.csv")) -> list[Expense]:
    """Read a processed transactions CSV and return a list of Expense objects.

    Columns must be in the order ``month, year, category, price``.

    Args:
        path: Path to the CSV file. Defaults to
            ``data/processed_transactions.csv``.

    Returns:
        List of ``Expense`` objects, one per row in the CSV.
    """
    expenses: list[Expense] = []
    with open(path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        next(reader)  # Skip the header row
        for row in reader:
            expenses.append(Expense(row[0], row[1], row[2], row[3]))
    return expenses
