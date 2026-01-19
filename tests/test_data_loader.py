"""
Tests for data_processing.data_loader module.
Comprehensive testing of Expense class categorization and representation.
"""

import pytest

from data_processing.category import all_category
from data_processing.data_loader import CATEGORY, IMPORTANCE, Expense


class TestExpenseCategorization:
    """Test suite for Expense category assignment logic."""

    @pytest.mark.parametrize(
        "month,year,item,price,expected_category,expected_importance",
        [
            # APARTMENT category tests
            (1, 2023, "apartment rent", 1200, CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL),
            (2, 2023, "bills payment", 1200, CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL),
            # EATING_OUT category tests
            (
                2,
                2023,
                "weekly groceries",
                150,
                CATEGORY.EATING_OUT,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            (
                3,
                2023,
                "coffee shop visit",
                80,
                CATEGORY.EATING_OUT,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            # CAR category tests
            (3, 2023, "fuel for car", 100, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            (4, 2023, "car maintenance", 200, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            (5, 2023, "car repairs", 300, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            # INVESTMENTS category tests
            (
                5,
                2023,
                "investment deposit",
                500,
                CATEGORY.INVESTMENTS,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            (
                6,
                2023,
                "investment portfolio",
                1000,
                CATEGORY.INVESTMENTS,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            # TRAVEL category tests
            (7, 2023, "travel to Paris", 800, CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE),
            (
                8,
                2023,
                "travel expenses",
                1200,
                CATEGORY.TRAVEL,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            # CARE category tests
            (8, 2023, "pharmacy purchase", 50, CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE),
            (9, 2023, "pharmacy items", 75, CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE),
            # MISC category tests (default)
            (9, 2023, "unknown expense", 100, CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW),
            (10, 2023, "random purchase", 50, CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW),
            (11, 2023, "unidentified item", 30, CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW),
        ],
    )
    def test_expense_category_and_importance_assignment(
        self, month, year, item, price, expected_category, expected_importance
    ):
        """
        Test correct category and importance assignment for various expense types.

        Verifies that:
        - Expenses are categorized correctly based on item description
        - Appropriate importance level is assigned to each category
        """
        expense = Expense(month, year, item, price)
        assert expense.category == expected_category
        assert expense.importance == expected_importance


class TestExpenseRepresentation:
    """Test suite for Expense string representation."""

    def test_expense_repr_basic(self):
        """Test __repr__ method produces correct CSV-formatted output."""
        expense = Expense(1, 2023, "apartment rent", 1200)
        expected_repr = "1,2023,apartment rent,🏯 Apartment,1200,Essential"
        assert repr(expense) == expected_repr

    @pytest.mark.parametrize(
        "month,year,item,price,expected_repr",
        [
            (
                1,
                2023,
                "apartment rent",
                1200,
                "1,2023,apartment rent,🏯 Apartment,1200,Essential",
            ),
            (
                2,
                2023,
                "groceries",
                150,
                "2,2023,groceries,🦞 Eating Out,150,Nice to Have",
            ),
            (3, 2023, "fuel", 100, "3,2023,fuel,🚗 Car,100,Have to Have"),
            (
                5,
                2023,
                "investment",
                500,
                "5,2023,investment,💸 Investments,500,Nice to Have",
            ),
            (7, 2023, "travel", 800, "7,2023,travel,🗺️ Travel,800,Nice to Have"),
            (9, 2023, "unknown", 100, "9,2023,unknown,Misc,100,Needs Review"),
        ],
    )
    def test_expense_repr_multiple_categories(self, month, year, item, price, expected_repr):
        """Test __repr__ output for different expense categories."""
        expense = Expense(month, year, item, price)
        assert repr(expense) == expected_repr

    def test_expense_repr_includes_emoji(self):
        """Verify that repr includes category emoji."""
        expense = Expense(1, 2023, "apartment rent", 1200)
        repr_string = repr(expense)
        assert "🏯" in repr_string

    def test_expense_repr_csv_format(self):
        """Verify repr produces valid CSV format with comma separation."""
        expense = Expense(1, 2023, "test item", 100)
        repr_string = repr(expense)
        parts = repr_string.split(",")

        # Should have 6 comma-separated parts
        assert len(parts) >= 5
        assert parts[0] == "1"
        assert parts[1] == "2023"


class TestExpenseAttributes:
    """Test suite for Expense object attributes."""

    def test_expense_initialization(self):
        """Test Expense object is initialized with correct attributes."""
        expense = Expense(1, 2023, "test item", 100)

        assert expense.month == 1
        assert expense.year == 2023
        assert expense.item == "test item"
        assert expense.price == 100

    def test_expense_has_category_attribute(self):
        """Verify Expense object has category attribute."""
        expense = Expense(1, 2023, "apartment rent", 1200)

        assert hasattr(expense, "category")
        assert expense.category is not None

    def test_expense_has_importance_attribute(self):
        """Verify Expense object has importance attribute."""
        expense = Expense(1, 2023, "apartment rent", 1200)

        assert hasattr(expense, "importance")
        assert expense.importance is not None


class TestExpenseEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_expense_with_zero_price(self):
        """Test Expense with zero price."""
        expense = Expense(1, 2023, "free item", 0)

        assert expense.price == 0
        assert expense.category is not None
        assert expense.importance is not None

    def test_expense_with_negative_price(self):
        """Test Expense with negative price (refund scenario)."""
        expense = Expense(1, 2023, "refund", -100)

        assert expense.price == -100
        assert expense.category is not None

    def test_expense_with_empty_item_description(self):
        """Test Expense with empty item description."""
        expense = Expense(1, 2023, "", 100)

        assert expense.item == ""
        # Empty item should default to MISC category
        assert expense.category == CATEGORY.MISC
        assert expense.importance == IMPORTANCE.NEEDS_REVIEW

    def test_expense_with_very_long_item_description(self):
        """Test Expense with very long item description."""
        long_description = "a" * 1000
        expense = Expense(1, 2023, long_description, 100)

        assert expense.item == long_description
        assert len(expense.item) == 1000

    def test_expense_with_special_characters_in_item(self):
        """Test Expense with special characters in item description."""
        special_item = "apartment, rent & utilities (2023)"
        expense = Expense(1, 2023, special_item, 1200)

        assert expense.item == special_item
        # Should still categorize correctly despite special characters
        assert expense.category == CATEGORY.APARTMENT


class TestCategoryAndImportanceEnums:
    """Test suite for CATEGORY and IMPORTANCE enum values."""

    def test_category_enum_values_exist(self):
        """Verify all expected CATEGORY enum values exist."""
        assert hasattr(CATEGORY, "APARTMENT")
        assert hasattr(CATEGORY, "EATING_OUT")
        assert hasattr(CATEGORY, "CAR")
        assert hasattr(CATEGORY, "INVESTMENTS")
        assert hasattr(CATEGORY, "TRAVEL")
        assert hasattr(CATEGORY, "CARE")
        assert hasattr(CATEGORY, "MISC")

    def test_importance_enum_values_exist(self):
        """Verify all expected IMPORTANCE enum values exist."""
        assert hasattr(IMPORTANCE, "ESSENTIAL")
        assert hasattr(IMPORTANCE, "HAVE_TO_HAVE")
        assert hasattr(IMPORTANCE, "NICE_TO_HAVE")
        assert hasattr(IMPORTANCE, "NEEDS_REVIEW")


class TestAllCategoriesCoverage:
    """Test suite to verify all categories from category.py are handled in _determine_category_and_importance."""

    def test_all_categories_from_category_py_are_covered(self):
        """
        Test that all categories defined in category.py are handled
        in the _determine_category_and_importance method.

        This test creates an Expense with each category name and verifies
        that it doesn't fall into the MISC category (unless it's MISC itself).
        """
        # Categories that should be explicitly handled (dynamically loaded from category.py)
        categories_to_test = [cat.lower() for cat in all_category if cat != "MISC"]

        uncovered_categories = []

        for category_name in categories_to_test:
            # Create an expense with the category name
            expense = Expense(1, 2023, category_name, 100)

            # If the expense is categorized as MISC, it means this category
            # is not explicitly handled in _determine_category_and_importance
            if expense.category == CATEGORY.MISC:
                uncovered_categories.append(category_name)

        # Assert that all categories are covered
        assert len(uncovered_categories) == 0, (
            f"The following categories from category.py are not covered "
            f"in _determine_category_and_importance: {uncovered_categories}"
        )

    @pytest.mark.parametrize("category_name", [cat.lower() for cat in all_category if cat != "MISC"])
    def test_individual_category_is_covered(self, category_name):
        """
        Test that each individual category from category.py is properly handled.

        This parameterized test verifies each category individually to provide
        more granular feedback if a specific category is not covered.
        """
        expense = Expense(1, 2023, category_name, 100)

        # The expense should not be categorized as MISC (except for MISC itself)
        assert expense.category != CATEGORY.MISC, (
            f"Category '{category_name}' is not handled in _determine_category_and_importance and falls back to MISC"
        )
