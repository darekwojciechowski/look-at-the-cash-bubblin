"""Domain model: the ``Expense`` dataclass, the ``CATEGORY``/``IMPORTANCE``
enumerations, the ``_classify_expense`` keyword classifier, and the
``get_data`` CSV loader that reconstructs ``Expense`` objects from a
processed transactions file.
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


# Each rule groups the ``category.py`` constant names that map to the same
# ``(CATEGORY, IMPORTANCE)`` display pair. Order is significant: the first
# matching rule wins. By referencing constant names rather than inlined
# keyword sets, a new vendor added to ``category.py`` is automatically picked
# up by classification, and the bridge to ``CATEGORY_DISPLAY`` stays in sync.
_CATEGORY_RULES_BY_NAME: list[tuple[CATEGORY, IMPORTANCE, tuple[str, ...]]] = [
    (CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL, ("APARTMENT", "BILLS", "RENOVATION")),
    (CATEGORY.FOOD, IMPORTANCE.ESSENTIAL, ("FOOD", "GREENFOOD")),
    (CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE, ("CAR", "LEASING", "FUEL", "REPAIRS")),
    (CATEGORY.TRANSPORTATION, IMPORTANCE.HAVE_TO_HAVE, ("TRANSPORTATION",)),
    (CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE, ("GROCERIES", "COFFEE", "CATERING")),
    (CATEGORY.ANIMALS, IMPORTANCE.HAVE_TO_HAVE, ("ANIMALS",)),
    (CATEGORY.SELF_DEVELOPMENT, IMPORTANCE.NICE_TO_HAVE, ("SELF_DEVELOPMENT", "BOOKS")),
    (CATEGORY.CLOTHES, IMPORTANCE.NICE_TO_HAVE, ("CLOTHES", "JEWELRY")),
    (CATEGORY.ENTERTAINMENT, IMPORTANCE.NICE_TO_HAVE, ("ENTERTAINMENT", "SUBSCRIPTIONS", "PCGAMES")),
    (CATEGORY.SHOPPING, IMPORTANCE.NICE_TO_HAVE, ("SHOPPING", "ELECTRONIC")),
    (CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE, ("INVESTMENTS",)),
    (CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE, ("PHARMACY", "COSMETICS", "INSURANCE", "SPORT", "BIKE", "SELF_CARE")),
    (CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE, ("TRAVEL",)),
    (CATEGORY.SELF_DESTRUCTION, IMPORTANCE.SHOULDNT_HAVE, ("ALCOHOL", "FASTFOOD")),
    (CATEGORY.KIDS, IMPORTANCE.HAVE_TO_HAVE, ("KIDS",)),
]


def _keywords_for(names: tuple[str, ...]) -> frozenset[str]:
    """Union the ``category.py`` keyword sets named in *names*."""
    return frozenset().union(*(getattr(category, n) for n in names))


# Resolved keyword frozensets used by the substring classifier. Derived once
# from ``_CATEGORY_RULES_BY_NAME`` so the two views can never drift.
_CATEGORY_RULES: list[tuple[CATEGORY, IMPORTANCE, frozenset[str]]] = [
    (cat_enum, imp_enum, _keywords_for(names)) for cat_enum, imp_enum, names in _CATEGORY_RULES_BY_NAME
]


def _classify_expense(text: str) -> tuple[CATEGORY, IMPORTANCE]:
    """Return the ``(CATEGORY, IMPORTANCE)`` pair for *text*.

    Substring-matches the (lowercased) text against ``_CATEGORY_RULES`` in
    declaration order; the first matching rule wins. Unmatched text falls
    back to ``(CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW)``.
    """
    lowered = text.lower()
    for rule_category, rule_importance, keywords in _CATEGORY_RULES:
        if any(kw in lowered for kw in keywords):
            return rule_category, rule_importance
    return CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW


def _build_category_display() -> dict[str, tuple[CATEGORY, IMPORTANCE]]:
    """Map every ``mappings()`` output label to its display ``(CATEGORY, IMPORTANCE)``.

    Built directly from ``_CATEGORY_RULES_BY_NAME`` so each ``category.py``
    constant name resolves to a deterministic display pair, independent of
    whether its keyword set happens to contain the lowercased label as a
    substring. Labels not covered by any rule (``REMOVE_ENTRY``, ``MISC``,
    ``DEFAULT_CATEGORY``) fall through to the MISC/NEEDS_REVIEW pair.
    """
    display: dict[str, tuple[CATEGORY, IMPORTANCE]] = dict.fromkeys(
        set(category.all_category) | {DEFAULT_CATEGORY},
        (CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW),
    )
    for cat_enum, imp_enum, names in _CATEGORY_RULES_BY_NAME:
        for name in names:
            display[name] = (cat_enum, imp_enum)
    return display


# The single authoritative bridge between the pipeline's classification output
# (the string labels ``mappings()`` returns) and the display CATEGORY/IMPORTANCE.
# Domain = every value ``mappings()`` can produce: the names in
# ``category.all_category`` plus the ``DEFAULT_CATEGORY`` fallback.
CATEGORY_DISPLAY: dict[str, tuple[CATEGORY, IMPORTANCE]] = _build_category_display()


@dataclass
class Expense:
    """Single classified transaction read from ``data/processed_transactions.csv``.

    On construction, ``category`` and ``importance`` are computed from
    ``item`` by keyword matching via ``_classify_expense``.
    """

    month: int | str
    year: int | str
    item: str
    amount: int | str
    category: CATEGORY = field(init=False, repr=True)
    importance: IMPORTANCE = field(init=False, repr=True)

    def __post_init__(self) -> None:
        """Normalize numeric fields to ``str`` and derive category/importance.

        Callers (CSV rows, test fixtures) pass ``month``/``year``/``amount`` as
        either ``int`` or ``str``; they are coerced to ``str`` here so every
        ``Expense`` instance has homogeneous string fields.

        ``category``/``importance`` are derived from ``item``. If ``item`` is
        already a known category label (e.g. ``"FOOD"`` written by the
        pipeline's CSV export), the display pair is looked up directly via
        ``CATEGORY_DISPLAY``; otherwise the substring-based
        ``_classify_expense`` fallback runs against free-text descriptions.
        """
        self.month = str(self.month)
        self.year = str(self.year)
        self.amount = str(self.amount)
        label = self.item.strip().upper()
        if label in CATEGORY_DISPLAY:
            self.category, self.importance = CATEGORY_DISPLAY[label]
        else:
            self.category, self.importance = _classify_expense(self.item)


def get_data(path: Path = Path("data/processed_transactions.csv")) -> list[Expense]:
    """Read a processed transactions CSV and return a list of Expense objects.

    Reads the CSV by header name, so column order in the file is irrelevant.
    Required headers: ``month``, ``year``, ``category``, ``amount``. The
    ``category`` column populates ``Expense.item`` — it is the keyword the
    classifier uses to derive ``CATEGORY`` and ``IMPORTANCE``.

    Args:
        path: Path to the CSV file. Defaults to
            ``data/processed_transactions.csv``.

    Returns:
        List of ``Expense`` objects, one per row in the CSV.
    """
    expenses: list[Expense] = []
    with open(path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            expenses.append(
                Expense(
                    month=row["month"],
                    year=row["year"],
                    item=row["category"],
                    amount=row["amount"],
                )
            )
    return expenses
