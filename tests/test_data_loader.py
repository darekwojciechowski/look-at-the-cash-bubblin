import pytest
from data_processing.data_loader import Expense, CATEGORY, IMPORTANCE


@pytest.mark.parametrize(
    "month, year, item, price, expected_category, expected_importance",
    [
        (1, 2023, "apartment rent", 1200, CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL),
        (2, 2023, "weekly groceries", 150,
         CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE),
        (3, 2023, "fuel for car", 100, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
        (5, 2023, "investment deposit", 500,
         CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE),
        (7, 2023, "travel to Paris", 800, CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE),
        (8, 2023, "pharmacy purchase", 50, CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE),
        (9, 2023, "unknown expense", 100, CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW),
    ],
)
def test_expense_category_and_importance(
    month, year, item, price, expected_category, expected_importance
):
    """
    Tests the Expense class to ensure:
    - The correct category is assigned based on the item description.
    - The correct importance level is determined for the expense.
    """
    expense = Expense(month, year, item, price)
    assert expense.category == expected_category
    assert expense.importance == expected_importance


def test_expense_repr():
    """
    Tests the __repr__ method of the Expense class to ensure:
    - The string representation of the Expense object matches the expected format.
    """
    expense = Expense(1, 2023, "apartment rent", 1200)
    expected_repr = "1,2023,apartment rent,🏯 Apartment,1200,Essential"
    assert repr(expense) == expected_repr
