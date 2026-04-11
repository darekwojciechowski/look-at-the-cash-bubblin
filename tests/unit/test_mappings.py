"""Tests for data_processing.mappings module.
Covers keyword-to-category mapping, case-insensitive matching, and category set integrity.
"""

import pytest

from data_processing.category import (
    CLOTHES,
    COFFEE,
    ENTERTAINMENT,
    FOOD,
    TRANSPORTATION,
    all_category,
)
from data_processing.mappings import mappings


@pytest.mark.unit
class TestMappingsFunction:
    """Test suite for the mappings function."""

    @pytest.mark.parametrize(
        "test_data,expected_category",
        [
            # REMOVE_ENTRY category tests
            ("zwrot za zamowienie", "REMOVE_ENTRY"),
            ("refund for order 12345", "REMOVE_ENTRY"),
            ("ZWROT platnosci", "REMOVE_ENTRY"),
            ("partial refund processed", "REMOVE_ENTRY"),
            # FOOD category tests
            ("I bought groceries at biedronka", "FOOD"),
            ("Shopping at lidl supermarket", "FOOD"),
            ("Visit to auchan for weekly shopping", "FOOD"),
            ("DINO market purchase", "FOOD"),
            # GREENFOOD category tests
            ("greenfood organic store", "GREENFOOD"),
            ("yerbamatestore premium tea", "GREENFOOD"),
            ("matcha green tea powder", "GREENFOOD"),
            # TRANSPORTATION category tests
            ("koleo train ticket booking", "TRANSPORTATION"),
            ("pkp railway transport", "TRANSPORTATION"),
            ("mpk city bus ticket", "TRANSPORTATION"),
            ("uber ride downtown", "TRANSPORTATION"),
            ("parking fee at shopping mall", "TRANSPORTATION"),
            # CAR category tests
            ("bmw service appointment", "CAR"),
            ("bmw parts replacement", "CAR"),
            ("toyota maintenance check", "CAR"),
            ("mercedes repair work", "CAR"),
            # FUEL category tests
            ("orlen gas station fill-up", "FUEL"),
            ("shell premium fuel", "FUEL"),
            ("lotos diesel purchase", "FUEL"),
            # COFFEE category tests
            ("starbucks morning coffee", "COFFEE"),
            ("local cafe visit", "COFFEE"),
            ("coffee shop meeting", "COFFEE"),
            # FASTFOOD category tests
            ("mcdonalds quick lunch", "FASTFOOD"),
            ("kfc chicken bucket", "FASTFOOD"),
            ("subway sandwich", "FASTFOOD"),
            ("kebab dinner", "FASTFOOD"),
            # GROCERIES category tests
            ("restaurant dinner with friends", "GROCERIES"),
            ("sushi restaurant takeout", "GROCERIES"),
            ("pizza delivery order", "GROCERIES"),
            # ALCOHOL category tests
            ("whisky bottle purchase", "ALCOHOL"),
            ("guinness beer pack", "ALCOHOL"),
            ("aperol cocktail ingredients", "ALCOHOL"),
            # APARTMENT category tests
            ("apartment monthly rent", "APARTMENT"),
            # BILLS category tests
            ("internet monthly payment", "BILLS"),
            ("pge electricity bill", "BILLS"),
            # RENOVATION category tests
            ("ikea furniture shopping", "RENOVATION"),
            ("leroy merlin tools", "RENOVATION"),
            ("castorama materials", "RENOVATION"),
            # CLOTHES category tests
            ("reserved new jacket", "CLOTHES"),
            ("adidas running shoes", "CLOTHES"),
            ("zara summer collection", "CLOTHES"),
            ("nike sportswear", "CLOTHES"),
            # ENTERTAINMENT category tests
            ("cinema movie tickets", "ENTERTAINMENT"),
            # Fixed: using 'teatr' which is in the category
            ("teatr performance", "ENTERTAINMENT"),
            ("muzeum visit fee", "ENTERTAINMENT"),
            # SUBSCRIPTIONS category tests
            ("netflix monthly subscription", "SUBSCRIPTIONS"),
            ("spotify premium account", "SUBSCRIPTIONS"),
            ("youtube premium membership", "SUBSCRIPTIONS"),
            # INVESTMENTS category tests
            ("xtb trading platform", "INVESTMENTS"),
            ("tfi investment fund", "INVESTMENTS"),
            ("bossa brokerage fee", "INVESTMENTS"),
            # ELECTRONIC category tests
            ("apple store purchase", "ELECTRONIC"),
            ("morele computer parts", "ELECTRONIC"),
            ("xkom gaming setup", "ELECTRONIC"),
            # SHOPPING category tests
            ("allegro online shopping", "SHOPPING"),
            # Fixed: removed 'prime' to avoid SUBSCRIPTIONS match
            ("amazon online shopping", "SHOPPING"),
            ("empik book store", "SHOPPING"),
        ],
    )
    def test_category_mapping_positive_cases(self, test_data, expected_category):
        """Test successful category mapping for various transaction descriptions.

        Given: a transaction description containing a known category keyword
        When:  mappings() is called with that description
        Then:  the returned category string matches the expected category
        """
        result = mappings(test_data)
        assert result == expected_category

    @pytest.mark.parametrize(
        "transaction",
        [
            "completely unknown transaction",
            "random description without keywords",
            "mystery payment xyz123",
            "unknown vendor purchase",
            "",
            "   ",
        ],
    )
    def test_unknown_transaction_returns_misc(self, transaction: str) -> None:
        """Test that unknown transactions return Misc category.

        Given: a transaction description with no recognisable keywords
        When:  mappings() is called
        Then:  the result is 'MISC'
        """
        assert mappings(transaction) == "MISC"

    @pytest.mark.parametrize(
        "transaction,expected",
        [
            ("BIEDRONKA SHOPPING", "FOOD"),
            ("Starbucks Coffee", "COFFEE"),
            ("mcdonalds Lunch", "FASTFOOD"),
            ("NETFLIX Subscription", "SUBSCRIPTIONS"),
            ("orlen FUEL station", "FUEL"),
        ],
    )
    def test_case_insensitive_matching(self, transaction: str, expected: str) -> None:
        """Test that keyword matching is case-insensitive.

        Given: a transaction description with mixed-case keyword
        When:  mappings() is called
        Then:  the category is returned regardless of letter case
        """
        assert mappings(transaction) == expected

    @pytest.mark.parametrize(
        "transaction,expected",
        [
            ("visit to biedronka store", "FOOD"),
            ("my netflix account renewal", "SUBSCRIPTIONS"),
            ("bought fuel at orlen station", "FUEL"),
            ("coffee meeting at starbucks", "COFFEE"),
        ],
    )
    def test_partial_keyword_matching(self, transaction: str, expected: str) -> None:
        """Test that partial keyword matching works correctly.

        Given: a transaction description where the keyword appears as a substring
        When:  mappings() is called
        Then:  the matching category is returned
        """
        assert mappings(transaction) == expected

    def test_category_precedence(self):
        """Test that first matching category takes precedence.

        Given: a transaction that contains keywords from two categories (FOOD and GROCERIES)
        When:  mappings() is called
        Then:  FOOD is returned because it is checked before GROCERIES
        """
        # Arrange
        mixed_transaction = "biedronka restaurant"  # Could be FOOD or GROCERIES

        # Act
        result = mappings(mixed_transaction)

        # Assert
        assert result == "FOOD"  # FOOD should win due to precedence

    @pytest.mark.parametrize(
        "transaction,expected",
        [
            ("biedronka and lidl shopping trip", "FOOD"),
            ("starbucks and cafe visit", "COFFEE"),
            ("netflix and spotify subscriptions", "SUBSCRIPTIONS"),
        ],
    )
    def test_multiple_keywords_same_category(self, transaction: str, expected: str) -> None:
        """Test transactions with multiple keywords from the same category.

        Given: a transaction description containing several keywords from one category
        When:  mappings() is called
        Then:  that category is returned
        """
        assert mappings(transaction) == expected

    @pytest.mark.parametrize(
        "transaction,expected",
        [
            ("biedronka - weekly shopping", "FOOD"),
            ("starbucks: morning coffee", "COFFEE"),
            ("netflix (monthly subscription)", "SUBSCRIPTIONS"),
            ("orlen/shell fuel station", "FUEL"),
        ],
    )
    def test_special_characters_in_transaction_data(self, transaction: str, expected: str) -> None:
        """Test handling of special characters in transaction descriptions.

        Given: a transaction description containing punctuation around a keyword
        When:  mappings() is called
        Then:  the category is correctly identified despite the punctuation
        """
        assert mappings(transaction) == expected

    @pytest.mark.parametrize(
        "category_set,category_name",
        [
            (FOOD, "FOOD"),
            (TRANSPORTATION, "TRANSPORTATION"),
            (COFFEE, "COFFEE"),
            (CLOTHES, "CLOTHES"),
            (ENTERTAINMENT, "ENTERTAINMENT"),
        ],
    )
    def test_all_keywords_in_category_set(self, category_set, category_name):
        """Test that all keywords in each category set are properly mapped.

        Given: the first five keywords of a category set
        When:  mappings() is called for each keyword embedded in a transaction string
        Then:  the returned category matches the expected category name
        """
        for keyword in list(category_set)[:5]:  # Test first 5 keywords from each set
            result = mappings(f"transaction with {keyword}")
            assert result == category_name

    def test_empty_category_sets_handling(self):
        """Test behavior when category sets might be empty (edge case).

        Given: a transaction with no matching keyword
        When:  mappings() is called
        Then:  the function returns 'MISC' without raising an error
        """
        result = mappings("unknown transaction")
        assert result == "MISC"

    def test_numeric_transaction_descriptions(self):
        """Test handling of numeric transaction descriptions.

        Given: transaction descriptions that consist only of numbers
        When:  mappings() is called for each
        Then:  all return 'MISC' since numbers match no category keyword
        """
        # Arrange
        numeric_transactions = [
            "12345",
            "transaction 123 unknown",
            "payment id 456789",
        ]

        # Act + Assert
        for transaction in numeric_transactions:
            result = mappings(transaction)
            assert result == "MISC"

    def test_unicode_characters(self):
        """Test handling of unicode characters in transaction descriptions.

        Given: transaction descriptions containing accented or Polish characters
        When:  mappings() is called for each
        Then:  the correct category is returned for each description
        """
        # Arrange
        unicode_tests = [
            ("café starbucks", "COFFEE"),  # café with accent
            ("restauracja pizza", "GROCERIES"),  # Polish characters
            ("biedronka żywność", "FOOD"),  # Polish characters
        ]

        # Act + Assert
        for transaction, expected in unicode_tests:
            result = mappings(transaction)
            assert result == expected


@pytest.mark.unit
class TestCategorySetIntegrity:
    """Test suite to verify category set definitions are complete."""

    def test_all_category_sets_defined(self):
        """Test that all category sets used in mappings are properly defined.

        Given: every category name listed in all_category
        When:  the corresponding attribute is retrieved from the category module
        Then:  each attribute is a non-None set object
        """
        import data_processing.category as category_module

        # Arrange
        category_sets = [getattr(category_module, cat_name) for cat_name in all_category]

        # Assert
        for category_set in category_sets:
            assert category_set is not None
            assert isinstance(category_set, set)
            # Most categories should have at least one keyword
            # (allowing empty sets for fallback categories like MISC)

    def test_no_duplicate_keywords_across_categories(self):
        """Test that keywords are not duplicated across different categories.

        Given: all keyword sets from the category module
        When:  every keyword is collected into a shared pool
        Then:  any duplicates are reported as a warning (informational test)
        """
        import data_processing.category as category_module

        # Arrange
        all_keywords = set()
        duplicates = set()

        # Dynamically build category list from all_category
        category_sets = [(cat_name, getattr(category_module, cat_name)) for cat_name in all_category]

        # Act
        for _category_name, category_set in category_sets:
            for keyword in category_set:
                if keyword in all_keywords:
                    duplicates.add(keyword)
                all_keywords.add(keyword)

        # Report duplicates if any (might be intentional for some keywords)
        if duplicates:
            print(f"Warning: Duplicate keywords found: {duplicates}")

        # This test is informational - duplicates might be intentional
        # depending on business logic requirements

    def test_each_keyword_appears_in_only_one_category(self):
        """
        Test that each keyword appears in only one category to avoid ambiguous transaction categorization.

        Given: all keyword sets from the category module
        When:  every keyword is mapped to its owning category
        Then:  no keyword belongs to more than one category

        This test ensures that no keyword exists in multiple categories, which could lead to
        unpredictable categorization results depending on the order of category checks.
        """
        import data_processing.category as category_module

        # Arrange
        keyword_to_category = {}
        duplicate_keywords = {}

        all_categories = [(cat_name, getattr(category_module, cat_name)) for cat_name in all_category]

        # Act
        for category_name, category_set in all_categories:
            for keyword in category_set:
                if keyword in keyword_to_category:
                    if keyword not in duplicate_keywords:
                        duplicate_keywords[keyword] = [keyword_to_category[keyword]]
                    duplicate_keywords[keyword].append(category_name)
                else:
                    keyword_to_category[keyword] = category_name

        # Assert
        if duplicate_keywords:
            error_message = "\n\nDuplicate keywords found across categories:\n"
            for keyword, categories in duplicate_keywords.items():
                error_message += f"  - '{keyword}' appears in: {', '.join(categories)}\n"
            error_message += "\nEach keyword must appear in only one category to avoid ambiguous categorization."

            pytest.fail(error_message)

        assert len(keyword_to_category) > 0, "No keywords found in any category"

    def test_all_category_list_completeness(self):
        """Test that all_category list contains all category names defined in the module.

        Given: all uppercase set-typed attributes in the category module
        When:  they are compared against the all_category list
        Then:  the two sets are identical with no missing or extra entries
        """
        import data_processing.category as category_module

        # Arrange
        defined_category_variables = [
            name
            for name in dir(category_module)
            if name.isupper()
            and name != "ALL_CATEGORY"
            and not name.startswith("_")
            and isinstance(getattr(category_module, name), set)
        ]

        # Act
        missing_categories = [cat for cat in defined_category_variables if cat not in all_category]
        extra_categories = [cat for cat in all_category if cat not in defined_category_variables]

        # Assert
        assert not missing_categories, f"Categories missing from all_category list: {missing_categories}"
        assert not extra_categories, f"Extra categories in all_category list not defined as sets: {extra_categories}"
        assert len(all_category) == len(defined_category_variables), (
            f"Expected {len(defined_category_variables)} categories but found {len(all_category)}"
        )

    def test_mappings_categories_match_all_category(self):
        """Test that categories dict in mappings() matches all_category dynamically.

        Given: every category in all_category with at least one keyword
        When:  mappings() is called with the first keyword of each category
        Then:  the returned value is a valid category name from all_category

        This test works by calling mappings() with a dummy value, which triggers
        the dictionary comprehension to build the categories dict. We then verify
        that all categories from all_category are accessible in the function scope.
        """
        # Arrange
        from data_processing import category
        from data_processing.mappings import mappings

        # Act + Assert
        for cat_name in all_category:
            cat_set = getattr(category, cat_name)
            assert isinstance(cat_set, set), f"{cat_name} should be a set"

            # MISC is intentionally empty (default category), skip keyword check for it
            if cat_name == "MISC":
                continue

            assert len(cat_set) > 0, f"{cat_name} should not be empty"

            first_keyword = list(cat_set)[0]
            result = mappings(first_keyword)
            assert result in all_category, f"mappings() returned invalid category: {result}"
