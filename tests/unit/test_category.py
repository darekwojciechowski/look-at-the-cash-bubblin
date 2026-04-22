"""
Tests for data_processing.category module.
Validates category keywords to prevent false matches.
"""

import re
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


@pytest.mark.unit
class TestCategoryRealisticEdgeCases:
    """Edge-case tests that guard against real bank data and data-entry mistakes."""

    def _all_keywords(self) -> list[tuple[str, str]]:
        """Return [(category_name, keyword), ...] for every non-special set."""
        result = []
        for attr_name in dir(category):
            if attr_name.startswith("_") or attr_name == "all_category" or not attr_name.isupper():
                continue
            attr_value = getattr(category, attr_name)
            if isinstance(attr_value, set):
                for kw in attr_value:
                    result.append((attr_name, kw))
        return result

    def test_all_keywords_are_lowercase(self):
        """Every keyword must be stored in lowercase.

        Given: all keyword sets from the category module
        When:  each keyword is compared with its lowercase form
        Then:  no keyword contains uppercase characters

        mappings() lowercases the input string but never lowercases keywords,
        so a typo like "Biedronka" silently never matches anything.
        """
        # Arrange
        all_kws = self._all_keywords()

        # Act
        non_lowercase = [(cat, kw) for cat, kw in all_kws if kw != kw.lower()]

        # Assert
        assert not non_lowercase, f"Keywords containing uppercase characters: {non_lowercase}"

    def test_remove_entry_is_first_in_all_category(self):
        """REMOVE_ENTRY must be the first entry in all_category.

        Given: the all_category priority list
        When:  its first element is checked
        Then:  it equals "REMOVE_ENTRY"

        Refund rows must be dropped before any other category matches;
        inserting a new category before REMOVE_ENTRY would let refunds
        be mis-classified instead of dropped.
        """
        # Arrange / Act / Assert
        assert category.all_category[0] == "REMOVE_ENTRY"

    def test_misc_is_last_in_all_category(self):
        """MISC must be the last entry in all_category.

        Given: the all_category priority list
        When:  its last element is checked
        Then:  it equals "MISC"

        MISC is the catch-all fallback; placing it before any other
        category would shadow every subsequent category entirely.
        """
        # Arrange / Act / Assert
        assert category.all_category[-1] == "MISC"

    def test_no_keyword_is_digits_only(self):
        """No keyword may consist entirely of digits.

        Given: all keyword sets from the category module
        When:  each keyword is tested with str.isdigit()
        Then:  no keyword is digits-only

        A digit-only keyword (e.g. "123", "2024") would substring-match
        payment IDs, dates, and reference numbers on nearly every bank row.
        """
        # Arrange
        all_kws = self._all_keywords()

        # Act
        digit_only = [(cat, kw) for cat, kw in all_kws if kw.isdigit()]

        # Assert
        assert not digit_only, f"Digit-only keywords found: {digit_only}"

    def test_multi_word_keywords_have_single_space(self):
        """Multi-word keywords must use exactly one space between words.

        Given: all keyword sets from the category module
        When:  each keyword is searched for two or more consecutive whitespace characters
        Then:  no keyword contains such a sequence

        A double-space typo in "fast  food" would silently never match the
        real transaction description "fast food".
        """
        # Arrange
        all_kws = self._all_keywords()

        # Act
        double_space = [(cat, repr(kw)) for cat, kw in all_kws if re.search(r"\s{2,}", kw)]

        # Assert
        assert not double_space, f"Keywords with consecutive whitespace: {double_space}"

    def test_no_banking_metadata_terms_in_categories(self):
        """Common Polish bank metadata terms must not appear as standalone keywords.

        Given: all keyword sets from the category module
        When:  they are intersected with a set of known banking noise terms
        Then:  the intersection is empty

        Words like "przelew", "blik", or "bankomat" prefix nearly every
        bank export row; if one lands in a category set, that category
        would match the majority of all transactions.
        """
        # Arrange
        BANKING_NOISE = {"przelew", "platnosc", "blik", "bankomat", "wyplata", "saldo", "prowizja", "opłata"}
        all_kws = {kw for _, kw in self._all_keywords()}

        # Act
        collision = all_kws & BANKING_NOISE

        # Assert
        assert not collision, f"Banking metadata terms found in category keywords: {collision}"

    def test_remove_entry_covers_polish_and_english_refund_terms(self):
        """REMOVE_ENTRY must contain both Polish and English refund terms.

        Given: the REMOVE_ENTRY keyword set
        When:  it is checked for "zwrot" (Polish) and "refund" (English)
        Then:  both terms are present

        Polish banks export in Polish, but some fintech cards use English;
        dropping either term would let one entire language's refunds pass
        through to spending categories.
        """
        # Arrange / Act / Assert
        assert "zwrot" in category.REMOVE_ENTRY, "'zwrot' missing from REMOVE_ENTRY"
        assert "refund" in category.REMOVE_ENTRY, "'refund' missing from REMOVE_ENTRY"
