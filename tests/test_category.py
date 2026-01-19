"""
Tests for data_processing.category module.
Validates category keywords to prevent false matches.
"""

from collections import defaultdict

import pytest

from data_processing import category


class TestCategoryKeywordUniqueness:
    """Test suite for validating category keyword uniqueness and preventing false matches."""

    def test_short_strings_not_substring_of_other_keywords(self):
        """
        Test that short strings (1-4 characters) are not substrings of other keywords.

        This prevents false positive matches where a short keyword (e.g., "car")
        might match within a longer word (e.g., "carrefour").

        Validates all category sets to ensure short keywords don't appear
        as substrings in any other keywords across the entire category module.
        """
        # Dynamically get all category sets from the module
        category_sets = []
        for attr_name in dir(category):
            # Skip private attributes, all_category list, and non-uppercase attributes
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            # Only include set objects (category keyword sets)
            if isinstance(attr_value, set):
                category_sets.append((attr_name, attr_value))

        # Collect all keywords from all categories
        all_keywords = []
        for category_name, category_set in category_sets:
            for keyword in category_set:
                all_keywords.append((category_name, keyword.lower()))

        # Find short keywords (1-4 characters)
        short_keywords = [(cat, kw) for cat, kw in all_keywords if 1 <= len(kw) <= 4]

        # Check each short keyword against all other keywords
        problematic_matches = []

        for short_cat, short_kw in short_keywords:
            for other_cat, other_kw in all_keywords:
                # Skip comparing keyword with itself
                if short_kw == other_kw:
                    continue

                # Check if short keyword is a substring of another keyword
                if short_kw in other_kw:
                    problematic_matches.append(
                        {
                            "short_keyword": short_kw,
                            "short_category": short_cat,
                            "found_in": other_kw,
                            "found_in_category": other_cat,
                        }
                    )

        # If there are problematic matches, create a detailed error message
        if problematic_matches:
            error_message = "\n\nFound short keywords (1-4 chars) that appear as substrings in other keywords:\n"
            for match in problematic_matches:
                error_message += (
                    f"  - '{match['short_keyword']}' (from {match['short_category']}) "
                    f"found in '{match['found_in']}' (from {match['found_in_category']})\n"
                )
            error_message += "\nThese short keywords may cause false positive matches during categorization."

            pytest.fail(error_message)

    def test_no_duplicate_keywords_across_categories(self):
        """
        Test that no keyword appears in multiple categories.

        This is critical for transaction categorization - each keyword should
        uniquely identify a single category.
        """
        # Dynamically get all category sets from the module
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Create a mapping of keywords to their categories
        keyword_map = defaultdict(list)
        for category_name, keywords in categories.items():
            for keyword in keywords:
                keyword_map[keyword.lower()].append(category_name)

        # Find all keywords that appear in more than one category
        duplicates = {keyword: cats for keyword, cats in keyword_map.items() if len(cats) > 1}

        # Build detailed error message if duplicates found
        if duplicates:
            error_lines = [
                f"\n❌ Found {len(duplicates)} duplicate keyword(s) across different categories:",
                "",
            ]

            for keyword, cats in sorted(duplicates.items()):
                error_lines.append(f"  • '{keyword}' appears in: {', '.join(cats)}")

            error_message = "\n".join(error_lines)
            pytest.fail(error_message)

    def test_all_categories_have_keywords(self):
        """
        Test that all categories (except MISC) contain at least one keyword.

        Empty categories would never match any transactions.
        MISC is intentionally empty as it serves as a fallback category.
        """
        # Dynamically get all category sets from the module
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # MISC is intentionally empty as fallback category
        empty_categories = [name for name, keywords in categories.items() if len(keywords) == 0 and name != "MISC"]

        assert not empty_categories, f"Found empty categories: {', '.join(empty_categories)}"

    def test_no_empty_string_keywords(self):
        """
        Test that no category contains empty string keywords.

        Empty strings would cause false matches.
        """
        # Dynamically get all category sets from the module
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        categories_with_empty = []

        for category_name, keywords in categories.items():
            if "" in keywords or any(not keyword.strip() for keyword in keywords):
                categories_with_empty.append(category_name)

        assert not categories_with_empty, (
            f"Categories with empty/whitespace-only keywords: {', '.join(categories_with_empty)}"
        )

    def test_category_count(self):
        """
        Test that we have a reasonable number of categories.

        This is a sanity check to ensure the category module was loaded correctly.
        """
        # Dynamically get all category sets from the module
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Based on the current file, we should have a reasonable number of categories
        expected_min_categories = 30  # Minimum expected
        expected_max_categories = 50  # Maximum reasonable

        actual_count = len(categories)

        assert expected_min_categories <= actual_count <= expected_max_categories, (
            f"Expected between {expected_min_categories} and {expected_max_categories} "
            f"categories, but found {actual_count}"
        )

    def test_keywords_are_valid_characters(self):
        """
        Test that keywords don't contain unexpected characters.

        This is a basic sanity check for data quality.
        """
        import string

        allowed_chars = set(string.ascii_letters + string.digits + " '.,-_()&łąćęńóśźżŁĄĆĘŃÓŚŹŻ/ñóéíá:;öü")

        # Dynamically get all category sets from the module
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        invalid_keywords = []

        for category_name, keywords in categories.items():
            for keyword in keywords:
                if not all(char in allowed_chars for char in keyword):
                    invalid_keywords.append((category_name, keyword))

        # This is a warning test - we allow some special characters
        if invalid_keywords:
            print(f"\n⚠️  Warning: Found {len(invalid_keywords)} keywords with special characters")
            for cat, kw in invalid_keywords[:5]:  # Show first 5
                print(f"    {cat}: '{kw}'")

    def test_specific_sensitive_keywords(self):
        """
        Test for specific keywords that are known to potentially cause issues.

        This test checks common words that might accidentally appear in multiple categories.
        """
        # Common words that should probably only appear once
        sensitive_keywords = [
            "bike",
            "sport",
            "restaurant",
            "pizza",
            "hotel",
            "food",
            "car",
            "travel",
            "kawa",
            "coffee",
        ]

        keyword_locations = defaultdict(list)

        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)

            if isinstance(attr_value, set):
                for keyword in attr_value:
                    keyword_locations[keyword.lower()].append(attr_name)

        # Check our sensitive keywords
        duplicated_sensitive = {
            kw: cats for kw in sensitive_keywords for cats in [keyword_locations.get(kw.lower(), [])] if len(cats) > 1
        }

        if duplicated_sensitive:
            error_lines = ["\n⚠️  Sensitive keywords found in multiple categories:", ""]
            for kw, cats in duplicated_sensitive.items():
                error_lines.append(f"  • '{kw}' in: {', '.join(cats)}")

            pytest.fail("\n".join(error_lines))

    def test_all_categories_exist_in_all_category_list(self):
        """
        Test that all category sets defined in the module are listed in all_category.

        This ensures consistency between category definitions and the category list.
        """
        # Get all category sets from the module
        defined_categories = set()
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue

            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                defined_categories.add(attr_name)

        # Get categories from all_category list
        listed_categories = set(category.all_category)

        # Find categories that are defined but not listed
        not_listed = defined_categories - listed_categories

        # Find categories that are listed but not defined
        not_defined = listed_categories - defined_categories

        error_messages = []

        if not_listed:
            error_messages.append(
                f"\n❌ Categories defined in code but missing from all_category list: {', '.join(sorted(not_listed))}"
            )

        if not_defined:
            error_messages.append(
                f"\n❌ Categories in all_category list but not defined in code: {', '.join(sorted(not_defined))}"
            )

        if error_messages:
            pytest.fail("".join(error_messages))
