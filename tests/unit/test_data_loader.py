"""Tests for data_processing.data_loader module.
Covers Expense categorization, importance assignment, and CSV representation.
"""

import pytest

from data_processing.category import all_category
from data_processing.data_loader import CATEGORY, IMPORTANCE, Expense


@pytest.mark.unit
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
        """Verify Expense assigns the correct category and importance level for each input.

        Given: parametrized month, year, item, and price values
        When:  Expense is instantiated with those values
        Then:  category and importance match the expected values
        """
        expense = Expense(month, year, item, price)
        assert expense.category == expected_category
        assert expense.importance == expected_importance


@pytest.mark.unit
class TestExpenseRepresentation:
    """Test suite for Expense string representation."""

    def test_expense_to_csv_row_basic(self):
        """Test to_csv_row method produces correct CSV-formatted output.

        Given: an Expense for apartment rent at 1200
        When:  to_csv_row() is called
        Then:  the result equals the expected comma-separated string
        """
        # Arrange
        expense = Expense(1, 2023, "apartment rent", 1200)
        expected = "1,2023,apartment rent,🏯 Apartment,1200,Essential"

        # Act + Assert
        assert expense.to_csv_row() == expected

    @pytest.mark.parametrize(
        "month,year,item,price,expected_csv",
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
    def test_expense_to_csv_row_multiple_categories(self, month, year, item, price, expected_csv):
        """Test to_csv_row output for different expense categories.

        Given: parametrized expense fields covering multiple categories
        When:  to_csv_row() is called
        Then:  the output matches the expected CSV string for each category
        """
        expense = Expense(month, year, item, price)
        assert expense.to_csv_row() == expected_csv

    def test_expense_to_csv_row_includes_emoji(self):
        """Verify that to_csv_row includes category emoji.

        Given: an Expense categorised as APARTMENT
        When:  to_csv_row() is called
        Then:  the result contains the apartment emoji '🏯'
        """
        # Arrange
        expense = Expense(1, 2023, "apartment rent", 1200)

        # Act + Assert
        assert "🏯" in expense.to_csv_row()

    def test_expense_to_csv_row_csv_format(self):
        """Verify to_csv_row produces valid CSV format with comma separation.

        Given: an Expense for a generic test item
        When:  to_csv_row() is called and the result is split on commas
        Then:  there are at least five parts and the first two are month and year
        """
        # Arrange
        expense = Expense(1, 2023, "test item", 100)

        # Act
        parts = expense.to_csv_row().split(",")

        # Assert
        assert len(parts) >= 5
        assert parts[0] == "1"
        assert parts[1] == "2023"

    def test_expense_repr_is_developer_readable(self):
        """Verify __repr__ returns dataclass representation, not CSV format.

        Given: an Expense for apartment rent
        When:  repr() is called on the instance
        Then:  the string contains 'Expense(' and a 'month=' field label
        """
        # Arrange
        expense = Expense(1, 2023, "apartment rent", 1200)

        # Act
        repr_string = repr(expense)

        # Assert
        assert "Expense(" in repr_string
        assert "month=" in repr_string


@pytest.mark.unit
class TestExpenseAttributes:
    """Test suite for Expense object attributes."""

    def test_expense_initialization(self):
        """Test Expense object is initialized with correct attributes.

        Given: month=1, year=2023, item='test item', price=100
        When:  Expense is instantiated with those values
        Then:  each attribute equals the supplied value
        """
        # Arrange + Act
        expense = Expense(1, 2023, "test item", 100)

        # Assert
        assert expense.month == 1
        assert expense.year == 2023
        assert expense.item == "test item"
        assert expense.price == 100

    def test_expense_has_category_attribute(self):
        """Verify Expense object has category attribute.

        Given: an Expense for apartment rent
        When:  the instance is inspected for a category attribute
        Then:  category exists and is not None
        """
        # Arrange
        expense = Expense(1, 2023, "apartment rent", 1200)

        # Assert
        assert hasattr(expense, "category")
        assert expense.category is not None

    def test_expense_has_importance_attribute(self):
        """Verify Expense object has importance attribute.

        Given: an Expense for apartment rent
        When:  the instance is inspected for an importance attribute
        Then:  importance exists and is not None
        """
        # Arrange
        expense = Expense(1, 2023, "apartment rent", 1200)

        # Assert
        assert hasattr(expense, "importance")
        assert expense.importance is not None

    def test_expense_equality(self):
        """Equal field values produce equal Expense instances (dataclass __eq__).

        Given: two Expense instances with identical field values
        When:  they are compared with ==
        Then:  the instances are considered equal
        """
        # Arrange
        a = Expense(1, 2023, "apartment rent", 1200)
        b = Expense(1, 2023, "apartment rent", 1200)

        # Assert
        assert a == b

    def test_expense_inequality(self):
        """Different field values produce unequal Expense instances.

        Given: two Expense instances differing only in month
        When:  they are compared with !=
        Then:  the instances are not equal
        """
        # Arrange
        a = Expense(1, 2023, "apartment rent", 1200)
        b = Expense(2, 2023, "apartment rent", 1200)

        # Assert
        assert a != b


@pytest.mark.unit
class TestExpenseEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_expense_with_zero_price(self):
        """Test Expense with zero price.

        Given: price is zero
        When:  Expense is instantiated
        Then:  price is stored as zero and category/importance are assigned
        """
        # Arrange + Act
        expense = Expense(1, 2023, "free item", 0)

        # Assert
        assert expense.price == 0
        assert expense.category is not None
        assert expense.importance is not None

    def test_expense_with_negative_price(self):
        """Test Expense with negative price (refund scenario).

        Given: price is -100 representing a refund
        When:  Expense is instantiated
        Then:  price is stored as-is and a category is assigned
        """
        # Arrange + Act
        expense = Expense(1, 2023, "refund", -100)

        # Assert
        assert expense.price == -100
        assert expense.category is not None

    def test_expense_with_empty_item_description(self):
        """Test Expense with empty item description.

        Given: item description is an empty string
        When:  Expense is instantiated
        Then:  item is empty, category defaults to MISC, and importance to NEEDS_REVIEW
        """
        # Arrange + Act
        expense = Expense(1, 2023, "", 100)

        # Assert
        assert expense.item == ""
        # Empty item should default to MISC category
        assert expense.category == CATEGORY.MISC
        assert expense.importance == IMPORTANCE.NEEDS_REVIEW

    def test_expense_with_very_long_item_description(self):
        """Test Expense with very long item description.

        Given: item description is 1000 characters long
        When:  Expense is instantiated
        Then:  the full description is stored without truncation
        """
        # Arrange
        long_description = "a" * 1000

        # Act
        expense = Expense(1, 2023, long_description, 100)

        # Assert
        assert expense.item == long_description
        assert len(expense.item) == 1000

    def test_expense_with_special_characters_in_item(self):
        """Test Expense with special characters in item description.

        Given: item contains commas, ampersands, and parentheses
        When:  Expense is instantiated
        Then:  description is stored verbatim and category resolves to APARTMENT
        """
        # Arrange
        special_item = "apartment, rent & utilities (2023)"

        # Act
        expense = Expense(1, 2023, special_item, 1200)

        # Assert
        assert expense.item == special_item
        # Should still categorize correctly despite special characters
        assert expense.category == CATEGORY.APARTMENT


@pytest.mark.unit
class TestCategoryAndImportanceEnums:
    """Test suite for CATEGORY and IMPORTANCE enum values."""

    def test_category_enum_values_exist(self):
        """Verify all expected CATEGORY enum values exist.

        Given: the CATEGORY enum is imported
        When:  each expected member name is checked with hasattr
        Then:  all seven category members are present
        """
        assert hasattr(CATEGORY, "APARTMENT")
        assert hasattr(CATEGORY, "EATING_OUT")
        assert hasattr(CATEGORY, "CAR")
        assert hasattr(CATEGORY, "INVESTMENTS")
        assert hasattr(CATEGORY, "TRAVEL")
        assert hasattr(CATEGORY, "CARE")
        assert hasattr(CATEGORY, "MISC")

    def test_importance_enum_values_exist(self):
        """Verify all expected IMPORTANCE enum values exist.

        Given: the IMPORTANCE enum is imported
        When:  each expected member name is checked with hasattr
        Then:  all four importance members are present
        """
        assert hasattr(IMPORTANCE, "ESSENTIAL")
        assert hasattr(IMPORTANCE, "HAVE_TO_HAVE")
        assert hasattr(IMPORTANCE, "NICE_TO_HAVE")
        assert hasattr(IMPORTANCE, "NEEDS_REVIEW")


@pytest.mark.unit
class TestAllCategoriesCoverage:
    """Test suite to verify all categories from category.py are handled in _determine_category_and_importance."""

    def test_all_categories_from_category_py_are_covered(self):
        """Verify no category from category.py falls back to MISC in _determine_category_and_importance.

        Given: all non-MISC/REMOVE_ENTRY category names from category.py
        When:  an Expense is created using each category name as its item
        Then:  none of them resolve to MISC (confirming full handler coverage)
        """
        # Arrange
        categories_to_test = [cat.lower() for cat in all_category if cat not in ("MISC", "REMOVE_ENTRY")]
        uncovered_categories = []

        # Act
        for category_name in categories_to_test:
            expense = Expense(1, 2023, category_name, 100)
            if expense.category == CATEGORY.MISC:
                uncovered_categories.append(category_name)

        # Assert
        assert len(uncovered_categories) == 0, (
            f"The following categories from category.py are not covered "
            f"in _determine_category_and_importance: {uncovered_categories}"
        )

    @pytest.mark.parametrize(
        "category_name", [cat.lower() for cat in all_category if cat not in ("MISC", "REMOVE_ENTRY")]
    )
    def test_individual_category_is_covered(self, category_name):
        """Verify each individual category from category.py has a handler and doesn't fall back to MISC.

        Given: a single category name from category.py (parametrized)
        When:  an Expense is instantiated using that name as the item
        Then:  the resulting category is not MISC
        """
        expense = Expense(1, 2023, category_name, 100)

        # The expense should not be categorized as MISC (except for MISC itself)
        assert expense.category != CATEGORY.MISC, (
            f"Category '{category_name}' is not handled in _determine_category_and_importance and falls back to MISC"
        )
