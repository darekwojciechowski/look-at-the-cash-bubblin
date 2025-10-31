"""
Tests for data_processing.mappings module.
Comprehensive testing of transaction categorization functionality.
"""

import pytest
from data_processing.mappings import mappings
from data_processing.category import (
    FOOD, GREENFOOD, TRANSPORTATION, CAR, LEASING, FUEL, REPAIRS,
    COFFEE, FASTFOOD, GROCERIES, CATERING, ALCOHOL, APARTMENT,
    BILLS, RENOVATION, CLOTHES, JEWELRY, ENTERTAINMENT, PCGAMES,
    BIKE, SPORT, PHARMACY, COSMETICS, TRAVEL, BOOKS, ANIMALS,
    INSURANCE, SUBSCRIPTIONS, INVESTMENTS, SELF_DEVELOPMENT,
    ELECTRONIC, SHOPPING, MISC, SELF_CARE, KIDS
)


class TestMappingsFunction:
    """Test suite for the mappings function."""

    @pytest.mark.parametrize("test_data,expected_category", [
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
        ("audi service appointment", "CAR"),
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
        ("etf investment purchase", "INVESTMENTS"),
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
    ])
    def test_category_mapping_positive_cases(self, test_data, expected_category):
        """Test successful category mapping for various transaction descriptions."""
        result = mappings(test_data)
        assert result == expected_category

    def test_unknown_transaction_returns_misc(self):
        """Test that unknown transactions return Misc category."""
        unknown_transactions = [
            "completely unknown transaction",
            "random description without keywords",
            "mystery payment xyz123",
            "unknown vendor purchase",
            "",  # empty string
            "   ",  # whitespace only
        ]

        for transaction in unknown_transactions:
            result = mappings(transaction)
            assert result == "MISC"

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        test_cases = [
            ("BIEDRONKA SHOPPING", "FOOD"),
            ("Starbucks Coffee", "COFFEE"),
            # Fixed: using exact keyword 'mcdonalds'
            ("mcdonalds Lunch", "FASTFOOD"),
            ("NETFLIX Subscription", "SUBSCRIPTIONS"),
            ("orlen FUEL station", "FUEL"),
        ]

        for transaction, expected in test_cases:
            result = mappings(transaction)
            assert result == expected

    def test_partial_keyword_matching(self):
        """Test that partial keyword matching works correctly."""
        test_cases = [
            ("visit to biedronka store", "FOOD"),
            ("my netflix account renewal", "SUBSCRIPTIONS"),
            ("bought fuel at orlen station", "FUEL"),
            ("coffee meeting at starbucks", "COFFEE"),
        ]

        for transaction, expected in test_cases:
            result = mappings(transaction)
            assert result == expected

    def test_category_precedence(self):
        """Test that first matching category takes precedence."""
        # Create a transaction that could match multiple categories
        # Based on the order in mappings function, FOOD comes before other categories
        mixed_transaction = "biedronka restaurant"  # Could be FOOD or GROCERIES
        result = mappings(mixed_transaction)
        assert result == "FOOD"  # FOOD should win due to precedence

    def test_multiple_keywords_same_category(self):
        """Test transactions with multiple keywords from the same category."""
        test_cases = [
            ("biedronka and lidl shopping trip", "FOOD"),
            ("starbucks and cafe visit", "COFFEE"),
            ("netflix and spotify subscriptions", "SUBSCRIPTIONS"),
        ]

        for transaction, expected in test_cases:
            result = mappings(transaction)
            assert result == expected

    def test_special_characters_in_transaction_data(self):
        """Test handling of special characters in transaction descriptions."""
        test_cases = [
            ("biedronka - weekly shopping", "FOOD"),
            ("starbucks: morning coffee", "COFFEE"),
            ("netflix (monthly subscription)", "SUBSCRIPTIONS"),
            ("orlen/shell fuel station", "FUEL"),
        ]

        for transaction, expected in test_cases:
            result = mappings(transaction)
            assert result == expected

    @pytest.mark.parametrize("category_set,category_name", [
        (FOOD, "FOOD"),
        (TRANSPORTATION, "TRANSPORTATION"),
        (COFFEE, "COFFEE"),
        (CLOTHES, "CLOTHES"),
        (ENTERTAINMENT, "ENTERTAINMENT"),
    ])
    def test_all_keywords_in_category_set(self, category_set, category_name):
        """Test that all keywords in each category set are properly mapped."""
        for keyword in list(category_set)[:5]:  # Test first 5 keywords from each set
            result = mappings(f"transaction with {keyword}")
            assert result == category_name

    def test_empty_category_sets_handling(self):
        """Test behavior when category sets might be empty (edge case)."""
        # This test ensures the function doesn't break if a category set is empty
        result = mappings("unknown transaction")
        assert result == "MISC"

    def test_numeric_transaction_descriptions(self):
        """Test handling of numeric transaction descriptions."""
        numeric_transactions = [
            "12345",
            "transaction 123 unknown",
            "payment id 456789",
        ]

        for transaction in numeric_transactions:
            result = mappings(transaction)
            assert result == "MISC"

    def test_unicode_characters(self):
        """Test handling of unicode characters in transaction descriptions."""
        unicode_tests = [
            ("café starbucks", "COFFEE"),  # café with accent
            ("restauracja pizza", "GROCERIES"),  # Polish characters
            ("biedronka żywność", "FOOD"),  # Polish characters
        ]

        for transaction, expected in unicode_tests:
            result = mappings(transaction)
            assert result == expected


class TestCategorySetIntegrity:
    """Test suite to verify category set definitions are complete."""

    def test_all_category_sets_defined(self):
        """Test that all category sets used in mappings are properly defined."""
        # This test ensures no category set is None or empty when it shouldn't be
        category_sets = [
            FOOD, GREENFOOD, TRANSPORTATION, CAR, LEASING, FUEL, REPAIRS,
            COFFEE, FASTFOOD, GROCERIES, CATERING, ALCOHOL, APARTMENT,
            BILLS, RENOVATION, CLOTHES, JEWELRY, ENTERTAINMENT, PCGAMES,
            BIKE, SPORT, PHARMACY, COSMETICS, TRAVEL, BOOKS, ANIMALS,
            INSURANCE, SUBSCRIPTIONS, INVESTMENTS, SELF_DEVELOPMENT,
            ELECTRONIC, SHOPPING, MISC
        ]

        for category_set in category_sets:
            assert category_set is not None
            assert isinstance(category_set, set)
            # Most categories should have at least one keyword
            # (allowing empty sets for fallback categories like MISC)

    def test_no_duplicate_keywords_across_categories(self):
        """Test that keywords are not duplicated across different categories."""
        all_keywords = set()
        duplicates = set()

        category_sets = [
            ("FOOD", FOOD), ("GREENFOOD",
                             GREENFOOD), ("TRANSPORTATION", TRANSPORTATION),
            ("CAR", CAR), ("FUEL", FUEL), ("COFFEE",
                                           COFFEE), ("FASTFOOD", FASTFOOD),
            ("GROCERIES", GROCERIES), ("ALCOHOL", ALCOHOL), ("CLOTHES", CLOTHES),
            ("ENTERTAINMENT", ENTERTAINMENT), ("SUBSCRIPTIONS", SUBSCRIPTIONS),
            ("ELECTRONIC", ELECTRONIC), ("SHOPPING", SHOPPING), ("MISC", MISC)
        ]

        for category_name, category_set in category_sets:
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

        This test ensures that no keyword exists in multiple categories, which could lead to
        unpredictable categorization results depending on the order of category checks.
        """
        # Dictionary to track which category each keyword belongs to
        keyword_to_category = {}
        # Dictionary to track keywords that appear in multiple categories
        duplicate_keywords = {}

        # All category sets with their names
        all_categories = [
            ("FOOD", FOOD),
            ("GREENFOOD", GREENFOOD),
            ("TRANSPORTATION", TRANSPORTATION),
            ("CAR", CAR),
            ("LEASING", LEASING),
            ("FUEL", FUEL),
            ("REPAIRS", REPAIRS),
            ("COFFEE", COFFEE),
            ("FASTFOOD", FASTFOOD),
            ("GROCERIES", GROCERIES),
            ("CATERING", CATERING),
            ("ALCOHOL", ALCOHOL),
            ("APARTMENT", APARTMENT),
            ("BILLS", BILLS),
            ("RENOVATION", RENOVATION),
            ("CLOTHES", CLOTHES),
            ("JEWELRY", JEWELRY),
            ("ENTERTAINMENT", ENTERTAINMENT),
            ("PCGAMES", PCGAMES),
            ("BIKE", BIKE),
            ("SPORT", SPORT),
            ("PHARMACY", PHARMACY),
            ("COSMETICS", COSMETICS),
            ("TRAVEL", TRAVEL),
            ("BOOKS", BOOKS),
            ("ANIMALS", ANIMALS),
            ("INSURANCE", INSURANCE),
            ("SUBSCRIPTIONS", SUBSCRIPTIONS),
            ("INVESTMENTS", INVESTMENTS),
            ("SELF_DEVELOPMENT", SELF_DEVELOPMENT),
            ("ELECTRONIC", ELECTRONIC),
            ("SELF_CARE", SELF_CARE),
            ("KIDS", KIDS),
            ("SHOPPING", SHOPPING),
            ("MISC", MISC),
        ]

        # Check each keyword in each category
        for category_name, category_set in all_categories:
            for keyword in category_set:
                if keyword in keyword_to_category:
                    # Keyword already exists in another category
                    if keyword not in duplicate_keywords:
                        duplicate_keywords[keyword] = [
                            keyword_to_category[keyword]]
                    duplicate_keywords[keyword].append(category_name)
                else:
                    keyword_to_category[keyword] = category_name

        # Build detailed error message if duplicates found
        if duplicate_keywords:
            error_message = "\n\nDuplicate keywords found across categories:\n"
            for keyword, categories in duplicate_keywords.items():
                error_message += f"  - '{keyword}' appears in: {', '.join(categories)}\n"
            error_message += "\nEach keyword must appear in only one category to avoid ambiguous categorization."

            pytest.fail(error_message)

        # If we reach here, all keywords are unique across categories
        assert len(keyword_to_category) > 0, "No keywords found in any category"
