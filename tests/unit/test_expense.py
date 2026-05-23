"""Tests for data_processing.expense module.
Covers Expense categorization, importance assignment, the _classify_expense
function, the CATEGORY_DISPLAY bridge, and CSV representation.
"""

import pytest

from data_processing import category
from data_processing.category import all_category
from data_processing.expense import CATEGORY, CATEGORY_DISPLAY, IMPORTANCE, Expense, _classify_expense
from data_processing.mappings import DEFAULT_CATEGORY, mappings


@pytest.mark.unit
class TestExpenseCategorization:
    """Test suite for Expense category assignment logic."""

    @pytest.mark.parametrize(
        "month,year,item,amount,expected_category,expected_importance",
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
            (4, 2023, "bmw maintenance", 200, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            (5, 2023, "car repairs", 300, CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            # INVESTMENTS category tests
            (
                5,
                2023,
                "investments deposit",
                500,
                CATEGORY.INVESTMENTS,
                IMPORTANCE.NICE_TO_HAVE,
            ),
            (
                6,
                2023,
                "xtb portfolio",
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
        self, month, year, item, amount, expected_category, expected_importance
    ):
        """Verify Expense assigns the correct category and importance level for each input.

        Given: parametrized month, year, item, and amount values
        When:  Expense is instantiated with those values
        Then:  category and importance match the expected values
        """
        expense = Expense(month, year, item, amount)
        assert expense.category == expected_category
        assert expense.importance == expected_importance


@pytest.mark.unit
class TestExpenseRepresentation:
    """Test suite for Expense string representation."""

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
        """Test Expense normalizes numeric fields to str on construction.

        Given: month=1, year=2023, item='test item', amount=100 (ints)
        When:  Expense is instantiated with those values
        Then:  month/year/amount are coerced to str; item is stored verbatim
        """
        # Arrange + Act
        expense = Expense(1, 2023, "test item", 100)

        # Assert
        assert expense.month == "1"
        assert expense.year == "2023"
        assert expense.item == "test item"
        assert expense.amount == "100"

    def test_expense_int_fields_normalized_to_str(self):
        """Verify int month/year/amount are coerced to str and repr reflects it.

        Given: Expense(1, 2023, "rent", 1200) with int numeric fields
        When:  the instance is constructed and repr() is taken
        Then:  month is "1" and the repr renders the string-typed values
        """
        expense = Expense(1, 2023, "rent", 1200)

        assert expense.month == "1"
        assert expense.year == "2023"
        assert expense.amount == "1200"
        assert "month='1'" in repr(expense)
        assert "amount='1200'" in repr(expense)

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

    def test_expense_with_zero_amount(self):
        """Test Expense with zero amount.

        Given: amount is zero
        When:  Expense is instantiated
        Then:  amount is normalized to "0" and category/importance are assigned
        """
        # Arrange + Act
        expense = Expense(1, 2023, "free item", 0)

        # Assert
        assert expense.amount == "0"
        assert expense.category is not None
        assert expense.importance is not None

    def test_expense_with_negative_amount(self):
        """Test Expense with negative amount (refund scenario).

        Given: amount is -100 representing a refund
        When:  Expense is instantiated
        Then:  amount is normalized to "-100" and a category is assigned
        """
        # Arrange + Act
        expense = Expense(1, 2023, "refund", -100)

        # Assert
        assert expense.amount == "-100"
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


@pytest.mark.unit
class TestClassifyExpense:
    """Test suite for the stateless _classify_expense function."""

    @pytest.mark.parametrize(
        "text,expected_category,expected_importance",
        [
            # One keyword hit per rule in _CATEGORY_RULES (order matters).
            ("apartment", CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL),
            ("food", CATEGORY.FOOD, IMPORTANCE.ESSENTIAL),
            ("fuel", CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE),
            ("transportation", CATEGORY.TRANSPORTATION, IMPORTANCE.HAVE_TO_HAVE),
            ("groceries", CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE),
            ("animals", CATEGORY.ANIMALS, IMPORTANCE.HAVE_TO_HAVE),
            ("self_development", CATEGORY.SELF_DEVELOPMENT, IMPORTANCE.NICE_TO_HAVE),
            ("clothes", CATEGORY.CLOTHES, IMPORTANCE.NICE_TO_HAVE),
            ("entertainment", CATEGORY.ENTERTAINMENT, IMPORTANCE.NICE_TO_HAVE),
            ("shopping", CATEGORY.SHOPPING, IMPORTANCE.NICE_TO_HAVE),
            ("investments", CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE),
            ("pharmacy", CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE),
            ("travel", CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE),
            ("alcohol", CATEGORY.SELF_DESTRUCTION, IMPORTANCE.SHOULDNT_HAVE),
            ("kids", CATEGORY.KIDS, IMPORTANCE.HAVE_TO_HAVE),
        ],
    )
    def test_classify_one_keyword_per_rule(self, text, expected_category, expected_importance):
        """Verify _classify_expense returns the correct pair for one keyword per rule.

        Given: a keyword that matches exactly one rule in _CATEGORY_RULES
        When:  _classify_expense() is called with that keyword
        Then:  the returned (category, importance) pair matches the rule
        """
        category, importance = _classify_expense(text)

        assert category == expected_category
        assert importance == expected_importance

    def test_classify_unmatched_falls_back_to_misc(self):
        """Verify _classify_expense falls back to MISC / NEEDS_REVIEW for unmatched text.

        Given: text containing no rule keyword
        When:  _classify_expense() is called
        Then:  the result is (CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW)
        """
        category, importance = _classify_expense("totally unknown vendor xyz")

        assert category == CATEGORY.MISC
        assert importance == IMPORTANCE.NEEDS_REVIEW

    def test_classify_is_case_insensitive(self):
        """Verify _classify_expense lowercases input before matching.

        Given: an uppercase keyword
        When:  _classify_expense() is called
        Then:  the keyword still matches its rule
        """
        result_category, _ = _classify_expense("APARTMENT RENT")

        assert result_category == CATEGORY.APARTMENT


@pytest.mark.unit
class TestCategoryDisplayMap:
    """Guards the explicit bridge between mappings() output and display categories."""

    def test_domain_equals_mappings_codomain(self):
        """Verify CATEGORY_DISPLAY's domain exactly equals the mappings() codomain.

        Given: the CATEGORY_DISPLAY map and category.all_category
        When:  the key set is compared to all_category plus the default fallback
        Then:  they are exactly equal, so a future category.py rename fails loudly
        """
        assert set(CATEGORY_DISPLAY) == set(category.all_category) | {DEFAULT_CATEGORY}

    def test_every_mappings_output_is_a_map_key(self):
        """Verify every label mappings() can return is a CATEGORY_DISPLAY key.

        Given: each category name's first keyword and an unknown string
        When:  mappings() classifies each one
        Then:  every returned label is present in CATEGORY_DISPLAY
        """
        produced = {mappings("totally unknown vendor xyz")}
        for cat_name in category.all_category:
            cat_set = getattr(category, cat_name)
            if cat_set:
                produced.add(mappings(next(iter(cat_set))))

        assert produced <= set(CATEGORY_DISPLAY)

    def test_unmapped_labels_default_to_misc(self):
        """Verify labels not absorbed by any rule resolve to MISC / NEEDS_REVIEW.

        Given: ``REMOVE_ENTRY``, ``MISC``, and ``DEFAULT_CATEGORY`` — none of
            which appears in ``_CATEGORY_RULES_BY_NAME``
        When:  their CATEGORY_DISPLAY entries are inspected
        Then:  each maps to ``(CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW)``
        """
        misc_pair = (CATEGORY.MISC, IMPORTANCE.NEEDS_REVIEW)

        assert CATEGORY_DISPLAY["REMOVE_ENTRY"] == misc_pair
        assert CATEGORY_DISPLAY["MISC"] == misc_pair
        assert CATEGORY_DISPLAY[DEFAULT_CATEGORY] == misc_pair
