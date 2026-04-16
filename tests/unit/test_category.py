"""
Tests for data_processing.category module.
Validates category keywords to prevent false matches.
"""

from collections import defaultdict

import pytest

from data_processing import category


@pytest.mark.unit
class TestCategoryKeywordUniqueness:
    """Test suite for validating category keyword uniqueness and preventing false matches."""

    def test_short_strings_not_substring_of_other_keywords(self):
        """Short keywords (1-4 chars) must not appear as substrings of other keywords.

        Given: all keyword sets from the category module
        When:  every short keyword (1-4 chars) is checked against all other keywords
        Then:  no short keyword appears as a substring inside another keyword

        This prevents false positive matches where a short keyword (e.g., "car")
        might match within a longer word (e.g., "carrefour").
        """
        # Arrange
        category_sets = []
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                category_sets.append((attr_name, attr_value))

        all_keywords = []
        for category_name, category_set in category_sets:
            for keyword in category_set:
                all_keywords.append((category_name, keyword.lower()))

        short_keywords = [(cat, kw) for cat, kw in all_keywords if 1 <= len(kw) <= 4]

        # Act
        problematic_matches = []
        for short_cat, short_kw in short_keywords:
            for other_cat, other_kw in all_keywords:
                if short_kw == other_kw:
                    continue
                if short_kw in other_kw:
                    problematic_matches.append({
                        "short_keyword": short_kw,
                        "short_category": short_cat,
                        "found_in": other_kw,
                        "found_in_category": other_cat,
                    })

        # Assert
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
        """No keyword may appear in multiple categories.

        Given: all keyword sets from the category module
        When:  every keyword is mapped to its owning categories
        Then:  no keyword belongs to more than one category

        Each keyword must uniquely identify a single category to avoid
        ambiguous transaction categorization.
        """
        # Arrange
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Act
        keyword_map = defaultdict(list)
        for category_name, keywords in categories.items():
            for keyword in keywords:
                keyword_map[keyword.lower()].append(category_name)

        duplicates = {keyword: cats for keyword, cats in keyword_map.items() if len(cats) > 1}

        # Assert
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
        """All categories (except MISC) must contain at least one keyword.

        Given: all category sets from the category module
        When:  each set's length is checked
        Then:  no set is empty (MISC is the only permitted exception as a fallback category)

        Empty categories would never match any transactions.
        MISC is intentionally empty as it serves as a fallback category.
        """
        # Arrange
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Act
        # MISC is intentionally empty as fallback category
        empty_categories = [name for name, keywords in categories.items() if len(keywords) == 0 and name != "MISC"]

        # Assert
        assert not empty_categories, f"Found empty categories: {', '.join(empty_categories)}"

    def test_no_empty_string_keywords(self):
        """No category may contain empty or whitespace-only keywords.

        Given: all keyword sets from the category module
        When:  each keyword is checked for emptiness or whitespace-only content
        Then:  no category contains such a keyword

        Empty strings would cause false matches on every transaction.
        """
        # Arrange
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Act
        categories_with_empty = []
        for category_name, keywords in categories.items():
            if "" in keywords or any(not keyword.strip() for keyword in keywords):
                categories_with_empty.append(category_name)

        # Assert
        assert not categories_with_empty, (
            f"Categories with empty/whitespace-only keywords: {', '.join(categories_with_empty)}"
        )

    def test_category_count(self):
        """Category count must fall within the expected 30–50 range.

        Given: all uppercase set-typed attributes in the category module
        When:  their count is checked
        Then:  the count falls between 30 and 50 (sanity check for correct module loading)
        """
        # Arrange
        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Act
        actual_count = len(categories)

        # Assert
        expected_min_categories = 30  # Minimum expected
        expected_max_categories = 50  # Maximum reasonable

        assert expected_min_categories <= actual_count <= expected_max_categories, (
            f"Expected between {expected_min_categories} and {expected_max_categories} "
            f"categories, but found {actual_count}"
        )

    def test_keywords_are_valid_characters(self):
        """Keywords should not contain unexpected characters (informational warning).

        Given: all keyword sets from the category module
        When:  every character in every keyword is checked against the allowed set
        Then:  any violations are printed as a warning (no assertion failure)
        """
        import string

        # Arrange
        allowed_chars = set(string.ascii_letters + string.digits + " '.,-_()&łąćęńóśźżŁĄĆĘŃÓŚŹŻ/ñóéíá:;öü")

        categories = {}
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                categories[attr_name] = attr_value

        # Act
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
        """Sensitive keywords known to overlap (e.g. 'car', 'food') must belong to exactly one category.

        Given: a predefined list of sensitive keywords that could appear in multiple categories
        When:  each keyword is looked up across all category sets
        Then:  none of them belongs to more than one category
        """
        # Arrange
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

        # Act
        duplicated_sensitive = {
            kw: cats for kw in sensitive_keywords for cats in [keyword_locations.get(kw.lower(), [])] if len(cats) > 1
        }

        # Assert
        if duplicated_sensitive:
            error_lines = ["\n⚠️  Sensitive keywords found in multiple categories:", ""]
            for kw, cats in duplicated_sensitive.items():
                error_lines.append(f"  • '{kw}' in: {', '.join(cats)}")

            pytest.fail("\n".join(error_lines))

    def test_all_categories_exist_in_all_category_list(self):
        """All category sets in the module must be listed in all_category and vice versa.

        Given: all uppercase set-typed attributes in the category module
        When:  they are compared against all_category
        Then:  both sets are identical with no missing or extra entries
        """
        # Arrange
        defined_categories = set()
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                defined_categories.add(attr_name)

        listed_categories = set(category.all_category)

        # Act
        not_listed = defined_categories - listed_categories
        not_defined = listed_categories - defined_categories

        # Assert
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
